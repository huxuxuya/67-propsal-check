#!/usr/bin/env python3
import json
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from env_utils import gonka_rpc_source_label, gonka_rpc_url


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = DATA / "voting_end_epochs"
NODE = gonka_rpc_url()
DEFAULT_NODE = "http://node1.gonka.ai:8000"
EPOCHS = range(285, 291)


def fetch_json(path, timeout=12, attempts=3, node=NODE, source_label=None):
    source_label = source_label or gonka_rpc_source_label()
    url = f"{node}{path}"
    source_url = f"{source_label}{path}"
    last_error = ""
    last_status = None
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(url, timeout=timeout) as response:
                return {
                    "url": source_url,
                    "status": response.status,
                    "json": json.loads(response.read().decode()),
                    "error": "",
                    "attempts": attempt,
                    "fetchedAt": datetime.now(timezone.utc).isoformat(),
                }
        except Exception as exc:
            last_status = exc.code if isinstance(exc, urllib.error.HTTPError) else None
            last_error = type(exc).__name__
            time.sleep(1)
    return {
        "url": source_url,
        "status": last_status,
        "json": None,
        "error": last_error,
        "attempts": attempts,
        "fetchedAt": datetime.now(timezone.utc).isoformat(),
    }


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def fetch_epoch_rows(node=NODE, source_label=None):
    jobs = []
    for epoch in EPOCHS:
        jobs.append((epoch, "epoch_group_data", f"/chain-api/productscience/inference/inference/epoch_group_data/{epoch}"))

    epoch_rows = {epoch: {"epoch": epoch, "files": {}} for epoch in EPOCHS}
    results = {}
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(fetch_json, path, 12, 3, node, source_label): (epoch, key) for epoch, key, path in jobs}
        for future in as_completed(futures):
            epoch, key = futures[future]
            result = future.result()
            rel = f"e{epoch}/{key}.json"
            results[(epoch, key)] = (rel, result)
            epoch_rows[epoch]["files"][key] = rel
    return epoch_rows, results


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {
        "source": {
            "node": gonka_rpc_source_label(),
            "generatedAt": datetime.now(timezone.utc).isoformat(),
        "scope": "Proposal #67 voting-end epoch window e285-e290",
        },
        "epochs": [],
        "fallbackUsed": False,
    }

    epoch_rows, results = fetch_epoch_rows()
    if all((result.get("json") is None for _, result in results.values())) and NODE != DEFAULT_NODE:
        manifest["fallbackUsed"] = True
        epoch_rows, results = fetch_epoch_rows(DEFAULT_NODE, "fallback_public_node")

    manifest["epochs"] = [epoch_rows[epoch] for epoch in EPOCHS]
    for rel, result in results.values():
        write_json(OUT / rel, result)

    write_json(OUT / "manifest.json", manifest)
    print(f"Wrote {OUT / 'manifest.json'}")


if __name__ == "__main__":
    main()
