#!/usr/bin/env python3
import argparse
import json
import os
import shutil
import subprocess
import urllib.parse
import urllib.request
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


def inferenced_binary(required=False):
    configured = os.environ.get("INFERENCED_BINARY")
    if configured:
        return configured
    found = shutil.which("inferenced")
    if found:
        return found
    if required:
        raise SystemExit("inferenced binary not found; set INFERENCED_BINARY=/path/to/inferenced")
    return None


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


def epoch_group_id(epoch):
    group = load_upstream_epoch_group(epoch, "healthy" if epoch == 265 else "")
    group_id = group.get("epoch_group_id")
    if not group_id:
        raise SystemExit(f"Cannot determine epoch_group_id for epoch {epoch}")
    return str(group_id)


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


def rpc_get_json(rpc, path, params):
    url = f"{rpc.rstrip('/')}/{path.lstrip('/')}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.load(response)


def block_search(rpc, query, page=1, per_page=100):
    return rpc_get_json(
        rpc,
        "block_search",
        {
            "query": json.dumps(query),
            "page": str(page),
            "per_page": str(per_page),
        },
    )


def discover_event_heights(rpc, epoch, start, end):
    group_id = epoch_group_id(epoch)
    query = (
        f"cosmos.group.v1.EventUpdateGroup.group_id='\"{group_id}\"' "
        f"AND block.height >= {start} AND block.height <= {end}"
    )
    heights = []
    page = 1
    total_count = None
    while total_count is None or len(heights) < total_count:
        payload = block_search(rpc, query, page=page, per_page=100)
        if payload.get("error"):
            raise RuntimeError(payload["error"])
        result = payload.get("result") or {}
        total_count = int(result.get("total_count") or 0)
        blocks = result.get("blocks") or []
        if not blocks:
            break
        for block in blocks:
            header = ((block.get("block") or {}).get("header") or {})
            height = int(header.get("height") or 0)
            if height:
                heights.append(
                    {
                        "height": height,
                        "time": header.get("time") or "",
                    }
                )
        page += 1
    unique = {row["height"]: row for row in heights}
    return [unique[height] for height in sorted(unique)]


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
    parser.add_argument("--height-source", choices=["events", "scan", "configured"], default="events")
    parser.add_argument("--scan-step", type=int, default=100)
    parser.add_argument("--node", default=gonka_rpc_url())
    parser.add_argument("--require-snapshots", action="store_true")
    args = parser.parse_args()

    if args.scan_step < 1:
        raise SystemExit("--scan-step must be >= 1")

    binary = inferenced_binary(required=args.require_snapshots or args.height_source == "scan")
    configured = configured_heights()
    manifest = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "source": {
            "rpcNode": args.node,
            "binary": binary,
            "heightSource": args.height_source,
            "scanStep": args.scan_step,
            "configuredHeights": bool(configured),
            "snapshotsFetched": bool(binary),
        },
        "epochs": [],
    }

    for epoch in args.epochs:
        start, end = epoch_bounds(epoch)
        event_rows = []
        if args.height_source == "configured":
            heights = configured.get(epoch, [])
            if not heights:
                raise SystemExit(f"No configured CPoC heights for epoch {epoch}")
            event_rows = [{"height": height, "time": ""} for height in heights]
        elif args.height_source == "events":
            event_rows = discover_event_heights(args.node, epoch, start, end)
            heights = [row["height"] for row in event_rows]
        else:
            heights = discover_heights(binary, args.node, epoch, start, end, args.scan_step)
            event_rows = [{"height": height, "time": ""} for height in heights[1:]]

        epoch_dir = OUT / f"e{epoch}"
        cache = {}
        entries = [{"index": 0, "height": start, "kind": "start"}]
        if binary:
            path = write_snapshot(epoch_dir, f"start_{start}.json", fetch_at_height(binary, args.node, epoch, start, cache))
            entries[0]["file"] = str(path.relative_to(OUT))
        for index, row in enumerate(event_rows, start=1):
            height = row["height"]
            entry = {
                "index": index,
                "height": height,
                "blockTime": row.get("time") or "",
                "kind": "cpoc",
            }
            if binary:
                payload = fetch_at_height(binary, args.node, epoch, height, cache)
                path = write_snapshot(epoch_dir, f"cpoc_{index:02d}_{height}.json", payload)
                entry["file"] = str(path.relative_to(OUT))
            entries.append(entry)

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
