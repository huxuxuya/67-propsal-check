#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from env_utils import gonka_rpc_url


ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "upstream" / "gonka-kimi-restitution"
OUT = ROOT / "data" / "cpoc_epoch_snapshots"

EPOCHS = range(265, 277)


def load_json(path):
    with path.open() as f:
        return json.load(f)


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def epoch_group(epoch):
    if epoch == 265:
        path = UPSTREAM / "e265" / "epoch265_group_data_healthy.json"
    else:
        path = UPSTREAM / f"e{epoch}" / f"epoch{epoch}_group_data.json"
    payload = load_json(path)
    if isinstance(payload, list):
        payload = payload[0] if payload else {}
    return payload.get("epoch_group_data") or payload


def snapshot_heights(epoch):
    if epoch == 265:
        return {"start": 4_103_170, "cpoc": 4_105_360}
    group = epoch_group(epoch)
    return {
        "start": int(group.get("poc_start_block_height") or 0),
        "cpoc": int(group.get("effective_block_height") or 0),
    }


def inferenced_binary():
    return os.environ.get("INFERENCED_BINARY") or shutil.which("inferenced") or "inferenced"


def fetch_epoch_group(epoch, height):
    cmd = [
        inferenced_binary(),
        "query",
        "inference",
        "show-epoch-group-data",
        str(epoch),
        "--node",
        gonka_rpc_url("http://204.12.168.157:26657"),
        "--height",
        str(height),
        "-o",
        "json",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f"command failed: {' '.join(cmd)}")
    return json.loads(result.stdout)


def main():
    manifest = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "source": {
            "rpcNode": "GONKA_RPC_URL" if os.environ.get("GONKA_RPC_URL") else gonka_rpc_url("http://204.12.168.157:26657"),
            "binary": inferenced_binary(),
        },
        "epochs": [],
    }
    for epoch in EPOCHS:
        heights = snapshot_heights(epoch)
        row = {"epoch": epoch, "snapshots": {}}
        for phase, height in heights.items():
            if not height:
                row["snapshots"][phase] = {"height": height, "file": "", "error": "missing_height"}
                continue
            try:
                payload = fetch_epoch_group(epoch, height)
                rel = f"e{epoch}/{phase}.json"
                write_json(OUT / rel, {"height": height, "json": payload, "error": ""})
                row["snapshots"][phase] = {"height": height, "file": rel, "error": ""}
            except Exception as exc:
                row["snapshots"][phase] = {"height": height, "file": "", "error": str(exc)}
        manifest["epochs"].append(row)
    write_json(OUT / "manifest.json", manifest)
    print(f"Wrote {OUT / 'manifest.json'}")


if __name__ == "__main__":
    main()
