#!/usr/bin/env python3
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from env_utils import gonka_api_url, gonka_api_source_label


ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "upstream" / "gonka-kimi-restitution"
DATA = ROOT / "data"
EPOCHS = list(range(265, 277))
N_GONKA = 1_000_000_000


def read_recipients():
    path = UPSTREAM / "aggregate_compensation.csv"
    rows = []
    with path.open() as f:
        header = f.readline().strip().split(",")
        address_index = header.index("address")
        epoch_indexes = {epoch: header.index(f"e{epoch}") for epoch in EPOCHS}
        for line in f:
            parts = line.strip().split(",")
            if not parts:
                continue
            per_epoch = {epoch: float(parts[index]) for epoch, index in epoch_indexes.items()}
            if sum(per_epoch.values()) <= 0:
                continue
            rows.append({"address": parts[address_index], "perEpoch": per_epoch})
    return rows


def get_json(url, timeout=10):
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_summary(api_url, epoch, address, retries=3):
    path = f"/chain-api/productscience/inference/inference/epoch_performance_summary/{epoch}/{urllib.parse.quote(address)}"
    url = f"{api_url.rstrip('/')}{path}"
    for attempt in range(retries):
        try:
            return get_json(url).get("epochPerformanceSummary") or {}
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            if attempt + 1 == retries:
                return {}
            time.sleep(0.4 * (attempt + 1))
    return {}


def main():
    api_url = gonka_api_url()
    jobs = [
        (epoch, recipient["address"])
        for recipient in read_recipients()
        for epoch, compensation in recipient["perEpoch"].items()
        if compensation > 0
    ]
    rows = []
    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = {
            executor.submit(fetch_summary, api_url, epoch, address): (epoch, address)
            for epoch, address in jobs
        }
        for future in as_completed(futures):
            epoch, address = futures[future]
            summary = future.result()
            rewarded = int(summary.get("rewarded_coins") or 0)
            earned = int(summary.get("earned_coins") or 0)
            rows.append(
                {
                    "epoch": epoch,
                    "address": address,
                    "claimed": bool(summary.get("claimed")),
                    "rewardedCoins": rewarded,
                    "rewardedGonka": round(rewarded / N_GONKA, 6),
                    "earnedCoins": earned,
                    "earnedGonka": round(earned / N_GONKA, 6),
                    "inferenceCount": int(summary.get("inference_count") or 0),
                    "missedRequests": int(summary.get("missed_requests") or 0),
                    "validatedInferences": int(summary.get("validated_inferences") or 0),
                    "invalidatedInferences": int(summary.get("invalidated_inferences") or 0),
                }
            )
    rows.sort(key=lambda row: (row["epoch"], row["address"]))
    output = {
        "source": gonka_api_source_label(),
        "endpoint": "/chain-api/productscience/inference/inference/epoch_performance_summary/{epoch}/{address}",
        "rows": rows,
    }
    DATA.mkdir(parents=True, exist_ok=True)
    path = DATA / "epoch_reward_claims.json"
    path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(f"Wrote {path} with {len(rows)} compensated epoch rows")


if __name__ == "__main__":
    main()
