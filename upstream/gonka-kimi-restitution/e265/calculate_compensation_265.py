#!/usr/bin/env python3
"""
Epoch 265 Restitution Calculator — CPoC degradation at block 4103171

Issue:
  An unknown external actor conducted a targeted attack using malicious requests
  designed to crash vLLM instances running the Kimi model. The attack first hit in
  e265: CPoC confirmation weights for Kimi participants collapsed abnormally at block
  4103171. Binary search on the archive node confirmed:
    - Last healthy state : block 4103170  (confirmation_weights intact)
    - First corrupted    : block 4103171  (confirmation_weights collapsed)

  Compensation uses confirmation_weight values at height 4103170 — the last
  block before the degradation — as the authoritative measure of each
  participant's actual confirmed work.

Eligibility:
  All participants who had Kimi commits and a confirmation_weight at the healthy
  height are eligible, including those who received zero rewards as a direct
  result of the CPoC collapse. This differs from epochs 267+ where zero-reward
  participants are excluded (there, zero rewards indicates the participant failed
  the epoch for their own reasons, not due to the bug).

Compensation methodology:
  correct_reward = confirmation_weight_i (at 4103170) / total_confirmation_weight (at 4103170) × epoch_reward
  compensation   = max(0, correct_reward - actual_rewards_received)

All data is fetched live from the archive node. Reference JSON files are written
to this directory as a side effect.
"""

import json
import math
import subprocess
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "../../gonka-segment-report/.env"))

ARCHIVE_NODE = os.getenv("ARCHIVE_NODE_URL", "http://204.12.168.157:26657")
BINARY       = os.getenv("INFERENCED_BINARY", "/Users/fixtwin/gonka/gonka/inferenced")

EPOCH          = 265
POC_START      = 4089970
EPOCH_END      = 4105360
CPOC_CUTOFF      = 4103170   # last healthy block before CPoC degradation
SNAPSHOT_HEIGHT  = POC_START - 500  # delegation snapshot

KIMI_MODEL   = "moonshotai/Kimi-K2.6"
CW_DROP_THRESHOLD = 0.05  # exclude noise — only compensate >5% CW drop

INITIAL_EPOCH_REWARD = 323_000_000_000_000
DECAY_RATE           = -475e-6
GENESIS_EPOCH        = 1
epoch_theoretical_reward = INITIAL_EPOCH_REWARD * math.exp(DECAY_RATE * (EPOCH - GENESIS_EPOCH))

HERE = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------
# Chain fetchers
# ---------------------------------------------------------------------------

def run_cli(args, height=None):
    cmd = [BINARY] + args + ["--node", ARCHIVE_NODE, "-o", "json"]
    if height:
        cmd += ["--height", str(height)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return None


def fetch_commits():
    print(f"  Fetching PoC commits at height {EPOCH_END}...")
    d = run_cli(["query", "inference", "all-poc-v2-store-commits", str(POC_START)], height=EPOCH_END)
    if not d or "commits" not in d:
        raise RuntimeError("Failed to fetch PoC commits")
    with open(os.path.join(HERE, f"epoch{EPOCH}_commits.json"), "w") as f:
        json.dump(d, f, indent=2)
    kimi_addrs = set()
    for c in d["commits"]:
        if c["model_id"] == KIMI_MODEL:
            kimi_addrs.add(c["participant_address"])
    print(f"  -> {len(kimi_addrs)} addresses with Kimi commits")
    return kimi_addrs


def fetch_group_data(height, label):
    print(f"  Fetching epoch group data at {label} height {height}...")
    d = run_cli(["query", "inference", "show-epoch-group-data", str(EPOCH)], height=height)
    if not d:
        raise RuntimeError(f"Failed to fetch epoch group data at height {height}")
    fname = f"epoch{EPOCH}_group_data_{'healthy' if height == CPOC_CUTOFF else 'end'}.json"
    with open(os.path.join(HERE, fname), "w") as f:
        json.dump(d, f, indent=2)
    vw = d["epoch_group_data"]["validation_weights"]
    print(f"  -> {len(vw)} members")
    return vw


def fetch_delegations(addresses):
    print(f"  Fetching delegations at snapshot height {SNAPSHOT_HEIGHT} for {len(addresses)} addresses...")
    result = {}
    for addr in sorted(addresses):
        d = run_cli(["query", "inference", "poc-delegation", addr], height=SNAPSHOT_HEIGHT)
        result[addr] = {x["model_id"]: x["delegate_to"] for x in d.get("delegations", [])} if d else {}
    with open(os.path.join(HERE, f"epoch{EPOCH}_delegations.json"), "w") as f:
        json.dump(result, f, indent=2)
    print("  -> done")
    return result


def fetch_performance(addresses):
    print(f"  Fetching performance summaries for {len(addresses)} addresses...")
    result = {}
    for addr in sorted(addresses):
        d = run_cli(["query", "inference", "show-epoch-performance-summary-by-participant",
                     str(EPOCH), addr])
        result[addr] = int(d.get("epochPerformanceSummary", {}).get("rewarded_coins", 0)) if d else 0
    with open(os.path.join(HERE, f"epoch{EPOCH}_performance.json"), "w") as f:
        json.dump([{"participant_id": k, "rewarded_coins": str(v)} for k, v in result.items()], f, indent=2)
    print("  -> done")
    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(f"=== Epoch {EPOCH} Restitution Calculator (CPoC degradation at block {CPOC_CUTOFF+1}) ===\n")
    print("Fetching data from chain...")

    kimi_addrs  = fetch_commits()
    vw_healthy  = fetch_group_data(CPOC_CUTOFF, "healthy")
    vw_end      = fetch_group_data(EPOCH_END, "epoch end")
    addresses   = [x["member_address"] for x in vw_healthy]
    performance = fetch_performance(addresses)
    fetch_delegations(addresses)
    print()

    healthy_map = {x["member_address"]: x for x in vw_healthy}
    end_map     = {x["member_address"]: x for x in vw_end}

    # Total weight is stable throughout the epoch — verified constant from
    # block 4095000 through epoch end. Use epoch-end as canonical.
    total_weight = sum(int(x.get("weight", 0)) for x in vw_end)

    print(f"Epoch {EPOCH} theoretical reward pool : {epoch_theoretical_reward / 1e9:,.4f} GONKA")
    print(f"Total epoch weight                    : {total_weight:,}")
    print()

    excluded = []
    results  = []

    for addr in kimi_addrs:
        x_h = healthy_map.get(addr)
        if not x_h or "confirmation_weight" not in x_h:
            excluded.append((addr, "no confirmation_weight at healthy height"))
            continue
        cw_healthy = int(x_h["confirmation_weight"])
        if cw_healthy == 0:
            excluded.append((addr, "confirmation_weight = 0"))
            continue

        # Check CW drop vs epoch end — only compensate >5% drop
        x_end  = end_map.get(addr, {})
        cw_end = int(x_end["confirmation_weight"]) if "confirmation_weight" in x_end else 0
        drop   = (cw_healthy - cw_end) / cw_healthy
        if drop <= CW_DROP_THRESHOLD:
            excluded.append((addr, f"CW drop {drop:.1%} below threshold — not attributable to bug"))
            continue

        # Fair reward = participant's weight / total epoch weight * epoch reward
        # Weight is unaffected by the CPoC bug — it's set at epoch start.
        # The bug reduced confirmation_weight which caused the chain to underpay.
        weight       = int(x_end.get("weight", 0))
        actual       = performance.get(addr, 0)
        correct      = weight / total_weight * epoch_theoretical_reward
        compensation = max(0.0, correct - actual)

        if compensation > 0:
            results.append({
                "address":               addr,
                "weight":                weight,
                "cw_healthy":            cw_healthy,
                "cw_end":                cw_end,
                "cw_drop_pct":           round(drop * 100, 2),
                "correct_reward_ngonka": int(correct),
                "correct_reward_gonka":  correct / 1e9,
                "actual_rewards_ngonka": actual,
                "actual_rewards_gonka":  actual / 1e9,
                "compensation_ngonka":   int(compensation),
                "compensation_gonka":    compensation / 1e9,
            })

    results.sort(key=lambda x: x["compensation_ngonka"], reverse=True)
    total_comp = sum(r["compensation_ngonka"] for r in results)

    if excluded:
        print("Kimi participants excluded:")
        for addr, reason in excluded:
            print(f"  {addr}  ({reason})")
        print()

    print(f"{'='*112}")
    print(f"COMPENSATION SUMMARY — Epoch {EPOCH} (CPoC degradation)")
    print(f"{'='*112}")
    print(f"{'Address':<50} {'weight':>8} {'cw@healthy':>10} {'cw@end':>8} {'drop':>6} {'correct':>14} {'actual':>14} {'owed':>14}")
    print(f"{'-'*124}")
    for r in results:
        print(f"{r['address']:<50} "
              f"{r['weight']:>8,} "
              f"{r['cw_healthy']:>10,} "
              f"{r['cw_end']:>8,} "
              f"{r['cw_drop_pct']:>5.1f}% "
              f"{r['correct_reward_gonka']:>14,.4f} "
              f"{r['actual_rewards_gonka']:>14,.4f} "
              f"{r['compensation_gonka']:>14,.4f}")
    print(f"{'-'*112}")
    print(f"  Affected participants : {len(results)}")
    print(f"  Total compensation   : {total_comp / 1e9:,.4f} GONKA\n")

    def out(name):
        return os.path.join(HERE, name)

    with open(out(f"compensation_{EPOCH}.csv"), "w") as f:
        f.write("address,cw_healthy,cw_end,cw_drop_pct,"
                "correct_reward_ngonka,correct_reward_gonka,"
                "actual_rewards_ngonka,actual_rewards_gonka,"
                "compensation_ngonka,compensation_gonka\n")
        for r in results:
            f.write(f"{r['address']},{r['cw_healthy']},{r['cw_end']},{r['cw_drop_pct']},"
                    f"{r['correct_reward_ngonka']},{r['correct_reward_gonka']:.4f},"
                    f"{r['actual_rewards_ngonka']},{r['actual_rewards_gonka']:.4f},"
                    f"{r['compensation_ngonka']},{r['compensation_gonka']:.4f}\n")

    print(f"Saved to e{EPOCH}/compensation_{EPOCH}.csv")

    with open(out(f"compensation_{EPOCH}.json"), "w") as f:
        json.dump({
            "epoch":                           EPOCH,
            "cpoc_cutoff_height":              CPOC_CUTOFF,
            "epoch_theoretical_reward_ngonka": int(epoch_theoretical_reward),
            "epoch_theoretical_reward_gonka":  epoch_theoretical_reward / 1e9,
            "total_epoch_weight":              total_weight,
            "affected_participants":           len(results),
            "total_compensation_ngonka":       total_comp,
            "total_compensation_gonka":        total_comp / 1e9,
            "compensation":                    results,
        }, f, indent=2)
    print(f"Saved to e{EPOCH}/compensation_{EPOCH}.json")


if __name__ == "__main__":
    main()
