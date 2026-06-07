#!/usr/bin/env python3
"""
Epoch 269 Restitution Calculator — ComputeGroupCap underpayment

Issue:
  Same as epochs 267–268: all Kimi participants entered the epoch, but the Kimi model
  group's total weight exceeded the ComputeGroupCap (cap_factor × N-1 total network
  weight). The chain applied a uniform scale factor to every Kimi participant's
  ValidationWeight.Weight, causing systematic underpayment to every Kimi contributor.

  No delegation compensation is needed: all Kimi operators entered the epoch group,
  so no delegators were forced into ModeNone.

Cap parameters (from chain params at height 4228489):
  cap_factor             = 0.75
  N-1 total weight       = epoch 273 total ValidationWeight (fetched from chain)
  Kimi group cap         = cap_factor × N-1_total_weight
  Scale factor applied   = Kimi_group_cap / Kimi_raw_weight

Eligibility:
  Only healthy participants are compensated — those who confirmed work AND received
  actual rewards. Participants who failed the epoch (no confirmation_weight, or
  confirmation_weight present but rewards = 0) are excluded.

Compensation methodology:
  Use confirmation_weight as the authoritative measure of each participant's actual
  confirmed work. The correct reward each participant should have received is:

    correct_reward = confirmation_weight_i / EpochGroupData.total_weight * epoch_reward

  Compensation = max(0, correct_reward - actual_rewards_received)

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

EPOCH     = 276
POC_START = 4264130
EPOCH_END = 4279520  # true epoch end (poc_start + 15391 - 1)

KIMI_MODEL = "moonshotai/Kimi-K2.6"

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


def fetch_group_data():
    print(f"  Fetching epoch group data at height {EPOCH_END}...")
    d = run_cli(["query", "inference", "show-epoch-group-data", str(EPOCH)], height=EPOCH_END)
    if not d:
        raise RuntimeError("Failed to fetch epoch group data")
    with open(os.path.join(HERE, f"epoch{EPOCH}_group_data.json"), "w") as f:
        json.dump(d, f, indent=2)
    vw = d["epoch_group_data"]["validation_weights"]
    root_total_weight = int(d["epoch_group_data"].get("total_weight") or 0)
    print(f"  -> {len(vw)} members, root total_weight={root_total_weight:,}")
    return vw, root_total_weight


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
    print(f"=== Epoch {EPOCH} Restitution Calculator (ComputeGroupCap) ===\n")
    print("Fetching data from chain...")

    kimi_addrs  = fetch_commits()
    vw, root_total_weight = fetch_group_data()
    addresses   = [x["member_address"] for x in vw]
    performance = fetch_performance(addresses)
    print()

    kimi_vw      = [x for x in vw if x["member_address"] in kimi_addrs]
    total_conf_w = sum(int(x.get("confirmation_weight", 0)) for x in vw if "confirmation_weight" in x)
    total_weight = sum(int(x.get("weight", 0)) for x in vw)
    # root_total_weight: parent EpochGroupData.total_weight — the denominator the chain
    # used for reward distribution. Matches GRC e247 audit precedent (issue2_audit.py).

    non_kimi = [x["member_address"] for x in vw if x["member_address"] not in kimi_addrs]
    if non_kimi:
        print(f"Non-Kimi participants excluded from compensation pool: {len(non_kimi)}")
        print()

    excluded = [x["member_address"] for x in kimi_vw
                if "confirmation_weight" not in x or performance.get(x["member_address"], 0) == 0]
    if excluded:
        print(f"Participants excluded from compensation (dropped or received no rewards):")
        for a in excluded:
            entry = next(x for x in kimi_vw if x["member_address"] == a)
            cw_str = "no conf_w" if "confirmation_weight" not in entry else "conf_w present but rewards=0"
            print(f"  {a}  ({cw_str})")
        print()

    print(f"Epoch {EPOCH} theoretical reward pool  : {epoch_theoretical_reward / 1e9:,.4f} GONKA")
    print(f"Kimi participants in epoch group       : {len(kimi_vw)}")
    print(f"Total ValidationWeight.weight          : {total_weight:,}")
    print(f"Total confirmation_weight (all)        : {total_conf_w:,}")
    print(f"Root total_weight (reward denominator) : {root_total_weight:,}")
    if total_weight > 0:
        print(f"Ratio (conf/weight)                    : {total_conf_w/total_weight:.2f}x")
    print()

    results = []
    for x in kimi_vw:
        addr   = x["member_address"]
        cw     = int(x.get("confirmation_weight", 0)) if "confirmation_weight" in x else 0
        w      = int(x.get("weight", 0))
        actual = performance.get(addr, 0)

        if cw == 0 or root_total_weight == 0 or actual == 0:
            continue

        correct      = cw / root_total_weight * epoch_theoretical_reward
        compensation = max(0.0, correct - actual)

        if compensation > 0:
            results.append({
                "address":               addr,
                "validation_weight":     w,
                "confirmation_weight":   cw,
                "correct_reward_ngonka": int(correct),
                "correct_reward_gonka":  correct / 1e9,
                "actual_rewards_ngonka": actual,
                "actual_rewards_gonka":  actual / 1e9,
                "compensation_ngonka":   int(compensation),
                "compensation_gonka":    compensation / 1e9,
            })

    results.sort(key=lambda x: x["compensation_ngonka"], reverse=True)
    total_comp = sum(r["compensation_ngonka"] for r in results)

    print(f"{'='*112}")
    print(f"COMPENSATION SUMMARY — Epoch {EPOCH} (ComputeGroupCap underpayment)")
    print(f"{'='*112}")
    print(f"{'Address':<50} {'weight':>8} {'conf_w':>8} {'correct':>14} {'actual':>14} {'owed':>14}")
    print(f"{'-'*112}")
    for r in results:
        print(f"{r['address']:<50} "
              f"{r['validation_weight']:>8,} "
              f"{r['confirmation_weight']:>8,} "
              f"{r['correct_reward_gonka']:>14,.4f} "
              f"{r['actual_rewards_gonka']:>14,.4f} "
              f"{r['compensation_gonka']:>14,.4f}")
    print(f"{'-'*112}")
    print(f"  Affected participants : {len(results)}")
    print(f"  Total compensation   : {total_comp / 1e9:,.4f} GONKA\n")

    def out(name):
        return os.path.join(HERE, name)

    with open(out(f"compensation_{EPOCH}.csv"), "w") as f:
        f.write("address,validation_weight,confirmation_weight,"
                "correct_reward_ngonka,correct_reward_gonka,"
                "actual_rewards_ngonka,actual_rewards_gonka,"
                "compensation_ngonka,compensation_gonka\n")
        for r in results:
            f.write(f"{r['address']},{r['validation_weight']},{r['confirmation_weight']},"
                    f"{r['correct_reward_ngonka']},{r['correct_reward_gonka']:.4f},"
                    f"{r['actual_rewards_ngonka']},{r['actual_rewards_gonka']:.4f},"
                    f"{r['compensation_ngonka']},{r['compensation_gonka']:.4f}\n")
    print(f"Saved to e{EPOCH}/compensation_{EPOCH}.csv")

    with open(out(f"compensation_{EPOCH}.json"), "w") as f:
        json.dump({
            "epoch":                           EPOCH,
            "epoch_theoretical_reward_ngonka": int(epoch_theoretical_reward),
            "epoch_theoretical_reward_gonka":  epoch_theoretical_reward / 1e9,
            "total_validation_weight":         total_weight,
            "total_confirmation_weight":       total_conf_w,
            "root_total_weight":               root_total_weight,
            "denominator_mode":                "root_total_weight",
            "affected_participants":           len(results),
            "total_compensation_ngonka":       total_comp,
            "total_compensation_gonka":        total_comp / 1e9,
            "compensation":                    results,
        }, f, indent=2)
    print(f"Saved to e{EPOCH}/compensation_{EPOCH}.json")


if __name__ == "__main__":
    main()
