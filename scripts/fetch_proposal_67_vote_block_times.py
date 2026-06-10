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
OUT = DATA / "proposal_67_vote_blocks"
RPC_NODE = gonka_rpc_url()
DEFAULT_RPC_NODE = "http://node1.gonka.ai:26657"


def load_json(path):
    with path.open() as f:
        return json.load(f)


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def fetch_json(path, timeout=12, attempts=3, node=None, source_label=None):
    node = node or RPC_NODE
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


def vote_heights():
    raw = load_json(DATA / "proposal_67_tx_search.json")
    return sorted({int(tx["height"]) for tx in raw["result"]["txs"]})


def fetch_blocks(heights, node=RPC_NODE, source_label=None):
    source_label = source_label or gonka_rpc_source_label()
    results = {}
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {
            executor.submit(fetch_json, f"/block?height={height}", 12, 3, node, source_label): height
            for height in heights
        }
        for future in as_completed(futures):
            height = futures[future]
            results[height] = future.result()
    return results


def block_time(result):
    try:
        return result["json"]["result"]["block"]["header"]["time"]
    except Exception:
        return ""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    heights = vote_heights()
    manifest = {
        "source": {
            "rpcNode": gonka_rpc_source_label(),
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "scope": "Proposal #67 governance vote transaction block times",
        },
        "blocks": [],
        "rpcFallbackUsed": False,
    }

    results = fetch_blocks(heights)
    if all(result.get("json") is None for result in results.values()) and RPC_NODE != DEFAULT_RPC_NODE:
        manifest["rpcFallbackUsed"] = True
        manifest["source"]["rpcNode"] = "fallback_public_rpc"
        results = fetch_blocks(heights, DEFAULT_RPC_NODE, "fallback_public_rpc")

    for height in heights:
        result = results[height]
        rel = f"blocks/block_{height}.json"
        manifest["blocks"].append(
            {
                "height": height,
                "file": rel,
                "time": block_time(result),
                "status": result.get("status"),
                "error": result.get("error", ""),
            }
        )
        write_json(OUT / rel, result)

    write_json(OUT / "manifest.json", manifest)
    missing = [row["height"] for row in manifest["blocks"] if not row["time"]]
    print(f"Wrote {OUT / 'manifest.json'}")
    print(f"Blocks: {len(heights)}; missing times: {len(missing)}")
    if missing:
        raise SystemExit(f"Missing block times for heights: {missing}")


if __name__ == "__main__":
    main()
