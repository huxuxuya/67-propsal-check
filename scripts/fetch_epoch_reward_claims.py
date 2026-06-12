#!/usr/bin/env python3
import argparse
import base64
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from env_utils import gonka_rpc_source_label, gonka_rpc_url
from fetch_cpoc_epoch_snapshots import abci_query, as_text, parse_fields, proto_varint


ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "upstream" / "gonka-kimi-restitution"
DATA = ROOT / "data"
COMPENSATION_EPOCHS = list(range(265, 277))
DEFAULT_START_EPOCH = 255
DEFAULT_END_EPOCH = 276
N_GONKA = 1_000_000_000


def read_recipients():
    path = UPSTREAM / "aggregate_compensation.csv"
    rows = []
    with path.open() as f:
        header = f.readline().strip().split(",")
        address_index = header.index("address")
        epoch_indexes = {epoch: header.index(f"e{epoch}") for epoch in COMPENSATION_EPOCHS}
        for line in f:
            parts = line.strip().split(",")
            if not parts:
                continue
            per_epoch = {epoch: float(parts[index]) for epoch, index in epoch_indexes.items()}
            if sum(per_epoch.values()) <= 0:
                continue
            rows.append({"address": parts[address_index], "perEpoch": per_epoch})
    return rows


def parse_args():
    parser = argparse.ArgumentParser(description="Fetch epoch reward summaries for compensated recipients.")
    parser.add_argument("--from-epoch", type=int, default=DEFAULT_START_EPOCH)
    parser.add_argument("--to-epoch", type=int, default=DEFAULT_END_EPOCH)
    parser.add_argument("--workers", type=int, default=12)
    return parser.parse_args()


def decode_summary_row(value):
    row = {
        "epoch": 0,
        "address": "",
        "inferenceCount": 0,
        "missedRequests": 0,
        "earnedCoins": 0,
        "rewardedCoins": 0,
        "validatedInferences": 0,
        "invalidatedInferences": 0,
        "claimed": False,
    }
    for field_no, wire_type, inner_value in parse_fields(value):
        if field_no == 1 and wire_type == 0:
            row["epoch"] = int(inner_value)
        elif field_no == 2 and wire_type == 2:
            row["address"] = as_text(inner_value)
        elif field_no == 3 and wire_type == 0:
            row["inferenceCount"] = int(inner_value)
        elif field_no == 4 and wire_type == 0:
            row["missedRequests"] = int(inner_value)
        elif field_no == 5 and wire_type == 0:
            row["earnedCoins"] = int(inner_value)
        elif field_no == 6 and wire_type == 0:
            row["rewardedCoins"] = int(inner_value)
        elif field_no == 8 and wire_type == 0:
            row["validatedInferences"] = int(inner_value)
        elif field_no == 9 and wire_type == 0:
            row["invalidatedInferences"] = int(inner_value)
        elif field_no == 10 and wire_type == 0:
            row["claimed"] = bool(inner_value)
    return row


def decode_epoch_summaries_response(value_b64):
    rows = {}
    raw = base64.b64decode(value_b64)
    for field_no, wire_type, value in parse_fields(raw):
        if field_no != 1 or wire_type != 2:
            continue
        row = decode_summary_row(value)
        if row["address"]:
            rows[row["address"]] = row
    return rows


def fetch_epoch_summaries(rpc_url, epoch, retries=3):
    data_hex = "0x" + proto_varint(1, int(epoch)).hex()
    for attempt in range(retries):
        try:
            payload = abci_query(rpc_url, "/inference.inference.Query/EpochPerformanceSummary", 0, data_hex)
            response = ((payload.get("result") or {}).get("response") or {})
            if response.get("code") not in (None, 0):
                raise RuntimeError(response.get("log") or f"ABCI code {response.get('code')}")
            value = response.get("value")
            if not value:
                return {}
            return decode_epoch_summaries_response(value)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, RuntimeError):
            if attempt + 1 == retries:
                return None
            time.sleep(0.4 * (attempt + 1))
    return None


def read_existing_rows(path):
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text()).get("rows", [])
    except (OSError, json.JSONDecodeError):
        return []


def main():
    args = parse_args()
    if args.from_epoch > args.to_epoch:
        raise SystemExit("--from-epoch must be <= --to-epoch")
    rpc_url = gonka_rpc_url()
    epochs = list(range(args.from_epoch, args.to_epoch + 1))
    recipients = read_recipients()
    recipient_addresses = {recipient["address"] for recipient in recipients}
    jobs = [
        epoch
        for epoch in epochs
    ]
    rows = []
    failed = 0
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(fetch_epoch_summaries, rpc_url, epoch): epoch
            for epoch in jobs
        }
        for future in as_completed(futures):
            epoch = futures[future]
            summaries = future.result()
            if summaries is None:
                failed += 1
                continue
            for address in sorted(recipient_addresses):
                summary = summaries.get(address) or {}
                rewarded = int(summary.get("rewardedCoins") or 0)
                earned = int(summary.get("earnedCoins") or 0)
                rows.append(
                    {
                        "epoch": epoch,
                        "address": address,
                        "claimed": bool(summary.get("claimed")),
                        "rewardedCoins": rewarded,
                        "rewardedGonka": round(rewarded / N_GONKA, 6),
                        "earnedCoins": earned,
                        "earnedGonka": round(earned / N_GONKA, 6),
                        "inferenceCount": int(summary.get("inferenceCount") or 0),
                        "missedRequests": int(summary.get("missedRequests") or 0),
                        "validatedInferences": int(summary.get("validatedInferences") or 0),
                        "invalidatedInferences": int(summary.get("invalidatedInferences") or 0),
                        "fetchedFromEpochSummary": address in summaries,
                    }
                )
    if not rows:
        raise SystemExit(f"No reward summaries were fetched from {rpc_url}; keeping existing {DATA / 'epoch_reward_claims.json'} untouched")
    path = DATA / "epoch_reward_claims.json"
    by_key = {
        (int(row.get("epoch") or 0), row.get("address") or ""): row
        for row in read_existing_rows(path)
        if row.get("epoch") and row.get("address")
    }
    for row in rows:
        by_key[(row["epoch"], row["address"])] = row
    merged_rows = sorted(by_key.values(), key=lambda row: (int(row["epoch"]), row["address"]))
    rows.sort(key=lambda row: (row["epoch"], row["address"]))
    output = {
        "source": gonka_rpc_source_label(),
        "endpoint": "/inference.inference.Query/EpochPerformanceSummary",
        "epochRange": {"from": args.from_epoch, "to": args.to_epoch},
        "recipientCount": len(recipients),
        "fetchedRows": len(rows),
        "failedRequests": failed,
        "rows": merged_rows,
    }
    DATA.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(f"Wrote {path} with {len(merged_rows)} merged rows; fetched={len(rows)} failed={failed}")


if __name__ == "__main__":
    main()
