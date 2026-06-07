#!/usr/bin/env python3
import json
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from env_utils import gonka_api_source_label, gonka_api_url, gonka_rpc_source_label, gonka_rpc_url


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = DATA / "voting_end_epochs"
API_NODE = gonka_api_url()
RPC_NODE = gonka_rpc_url()
DEFAULT_API_NODE = "http://node1.gonka.ai:8000"
DEFAULT_RPC_NODE = "http://node1.gonka.ai:26657"
EPOCHS = range(285, 291)
KEY_BLOCK_HEIGHTS = [
    4_413_581,
    4_428_572,
    4_428_972,
    4_429_647,
    4_430_015,
    4_430_200,
    4_430_201,
    4_430_202,
    4_430_417,
    4_444_363,
]


def fetch_json(path, timeout=12, attempts=3, node=None, source_label=None):
    node = node or API_NODE
    source_label = source_label or gonka_api_source_label()
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


def fetch_epoch_rows(node=API_NODE, source_label=None):
    source_label = source_label or gonka_api_source_label()
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


def fetch_block_rows(node=RPC_NODE, source_label=None):
    source_label = source_label or gonka_rpc_source_label("fallback_public_rpc")
    results = {}
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {
            executor.submit(fetch_json, f"/block?height={height}", 10, 2, node, source_label): height
            for height in KEY_BLOCK_HEIGHTS
        }
        for future in as_completed(futures):
            height = futures[future]
            result = future.result()
            rel = f"blocks/block_{height}.json"
            results[height] = (rel, result)
    return results


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {
        "source": {
            "apiNode": gonka_api_source_label(),
            "rpcNode": gonka_rpc_source_label("fallback_public_rpc"),
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "scope": "Proposal #67 voting-end epoch window e285-e290",
        },
        "epochs": [],
        "blocks": [],
        "apiFallbackUsed": False,
        "rpcFallbackUsed": False,
    }

    epoch_rows, results = fetch_epoch_rows()
    if all((result.get("json") is None for _, result in results.values())) and API_NODE != DEFAULT_API_NODE:
        manifest["apiFallbackUsed"] = True
        epoch_rows, results = fetch_epoch_rows(DEFAULT_API_NODE, "fallback_public_api")

    manifest["epochs"] = [epoch_rows[epoch] for epoch in EPOCHS]
    for rel, result in results.values():
        write_json(OUT / rel, result)

    block_results = fetch_block_rows()
    if all((result.get("json") is None for _, result in block_results.values())) and RPC_NODE != DEFAULT_RPC_NODE:
        manifest["rpcFallbackUsed"] = True
        block_results = fetch_block_rows(DEFAULT_RPC_NODE, "fallback_public_rpc")
    for height, (rel, result) in sorted(block_results.items()):
        manifest["blocks"].append({"height": height, "file": rel})
        write_json(OUT / rel, result)

    write_json(OUT / "manifest.json", manifest)
    print(f"Wrote {OUT / 'manifest.json'}")


if __name__ == "__main__":
    main()
