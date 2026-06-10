#!/usr/bin/env python3
import argparse
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from env_utils import gonka_rpc_url


ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "upstream" / "gonka-kimi-restitution"
DATA = ROOT / "data"
OUT = DATA / "cpoc_epoch_snapshots"
DEFAULT_EPOCHS = list(range(265, 277))


def load_json(path):
    with path.open() as f:
        return json.load(f)


def inferenced_binary():
    configured = os.environ.get("INFERENCED_BINARY")
    if configured:
        return configured
    found = shutil.which("inferenced")
    if found:
        return found
    raise SystemExit("inferenced binary not found; set INFERENCED_BINARY=/path/to/inferenced")


def load_upstream_epoch_group(epoch, snapshot=""):
    if epoch == 265 and snapshot:
        path = UPSTREAM / "e265" / f"epoch265_group_data_{snapshot}.json"
    else:
        path = UPSTREAM / f"e{epoch}" / f"epoch{epoch}_group_data.json"
    if not path.exists():
        return {}
    payload = load_json(path)
    if isinstance(payload, list):
        payload = payload[0] if payload else {}
    return payload.get("epoch_group_data") or payload


def epoch_bounds(epoch):
    current = load_upstream_epoch_group(epoch, "healthy" if epoch == 265 else "")
    next_group = load_upstream_epoch_group(epoch + 1)
    start = int(current.get("poc_start_block_height") or current.get("effective_block_height") or 0)
    if next_group.get("poc_start_block_height"):
        end = int(next_group["poc_start_block_height"]) - 1
    else:
        end = int(current.get("effective_block_height") or start)
    if not start or end < start:
        raise SystemExit(f"Cannot determine block range for epoch {epoch}")
    return start, end


def configured_heights():
    path = DATA / "cpoc_checkpoint_heights.json"
    if not path.exists():
        return {}
    payload = load_json(path)
    raw_epochs = payload.get("epochs", payload)
    return {int(epoch): sorted({int(height) for height in heights}) for epoch, heights in raw_epochs.items()}


def run_query(binary, rpc, epoch, height):
    cmd = [
        binary,
        "query",
        "inference",
        "show-epoch-group-data",
        str(epoch),
        "--node",
        rpc,
        "--height",
        str(height),
        "-o",
        "json",
    ]
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def unwrap_epoch_group(payload):
    wrapper = payload.get("json") if isinstance(payload, dict) else None
    if isinstance(wrapper, dict):
        payload = wrapper
    return payload.get("epoch_group_data") or payload


def weight_signature(payload):
    group = unwrap_epoch_group(payload)
    rows = []
    for item in group.get("validation_weights") or []:
        rows.append(
            (
                item.get("member_address") or "",
                int(item.get("weight") or item.get("voting_power") or 0),
                int(item.get("confirmation_weight") or 0),
            )
        )
    return tuple(sorted(rows))


def first_changed_height(binary, rpc, epoch, low_height, low_sig, high_height, high_sig, cache):
    if low_sig == high_sig:
        return high_height, high_sig
    low = low_height
    high = high_height
    found_sig = high_sig
    while high - low > 1:
        mid = (low + high) // 2
        payload = fetch_at_height(binary, rpc, epoch, mid, cache)
        sig = weight_signature(payload)
        if sig == low_sig:
            low = mid
        else:
            high = mid
            found_sig = sig
    return high, found_sig


def fetch_at_height(binary, rpc, epoch, height, cache):
    key = (epoch, height)
    if key not in cache:
        cache[key] = run_query(binary, rpc, epoch, height)
    return cache[key]


def discover_heights(binary, rpc, epoch, start, end, scan_step):
    heights = sorted(set([start, end, *range(start, end + 1, scan_step)]))
    cache = {}
    checkpoints = [start]
    previous_height = start
    previous_payload = fetch_at_height(binary, rpc, epoch, start, cache)
    previous_sig = weight_signature(previous_payload)

    for height in heights[1:]:
        payload = fetch_at_height(binary, rpc, epoch, height, cache)
        sig = weight_signature(payload)
        if sig != previous_sig:
            changed_height, changed_sig = first_changed_height(
                binary, rpc, epoch, previous_height, previous_sig, height, sig, cache
            )
            checkpoints.append(changed_height)
            previous_height = changed_height
            previous_sig = changed_sig
        else:
            previous_height = height
    return sorted(set(checkpoints))


def write_snapshot(epoch_dir, filename, payload):
    epoch_dir.mkdir(parents=True, exist_ok=True)
    path = epoch_dir / filename
    with path.open("w") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")
    return path


def main():
    parser = argparse.ArgumentParser(
        description="Fetch archive-node epoch group snapshots for every observed CPoC checkpoint."
    )
    parser.add_argument("--epochs", nargs="+", type=int, default=DEFAULT_EPOCHS)
    parser.add_argument("--scan-step", type=int, default=100)
    parser.add_argument("--node", default=gonka_rpc_url())
    args = parser.parse_args()

    if args.scan_step < 1:
        raise SystemExit("--scan-step must be >= 1")

    binary = inferenced_binary()
    configured = configured_heights()
    manifest = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "source": {
            "rpcNode": args.node,
            "binary": binary,
            "scanStep": args.scan_step,
            "configuredHeights": bool(configured),
        },
        "epochs": [],
    }

    for epoch in args.epochs:
        start, end = epoch_bounds(epoch)
        if epoch in configured:
            heights = configured[epoch]
            if start not in heights:
                heights = [start, *heights]
            heights = sorted(set(heights))
        else:
            heights = discover_heights(binary, args.node, epoch, start, end, args.scan_step)

        epoch_dir = OUT / f"e{epoch}"
        cache = {}
        entries = []
        for index, height in enumerate(heights):
            payload = fetch_at_height(binary, args.node, epoch, height, cache)
            filename = f"start_{height}.json" if index == 0 else f"cpoc_{index:02d}_{height}.json"
            path = write_snapshot(epoch_dir, filename, payload)
            entries.append(
                {
                    "index": index,
                    "height": height,
                    "file": str(path.relative_to(OUT)),
                    "kind": "start" if index == 0 else "cpoc",
                }
            )

        manifest["epochs"].append(
            {
                "epoch": epoch,
                "startHeight": start,
                "endHeight": end,
                "checkpoints": entries,
            }
        )

    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "manifest.json").open("w") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
        f.write("\n")


if __name__ == "__main__":
    main()
