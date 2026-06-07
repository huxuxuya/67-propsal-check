#!/usr/bin/env python3
"""
Epoch 266 Full Restitution Calculator

All data is fetched live from the archive node. The poc_commits/ JSON files in this
repo are reference artifacts only and are not read by this script.

The external attack on Kimi vLLM nodes that began in e265 escalated in e266, crashing
most operators' inference nodes and causing mass nonce exclusion. Two compensation
components:

Part 1 — Nonce compensation (compensation_266_nonces.csv)
  Participants whose Kimi nonces were not counted due to the attack-induced exclusion.
  Weight is reconstructed from on-chain commits; fair share vs actual rewards determines
  the compensation.

Part 2 — Delegation compensation (compensation_266_delegation.csv)
  Participants who delegated Kimi to an excluded operator. The exclusion forced them into
  ModeNone (15% penalty) instead of ModeDelegate (5% transfer) — a net 10% extra loss.

Combined: compensation_266_combined.csv + compensation_266.json
"""

import json
import math
import subprocess
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "../../gonka-segment-report/.env"))

ARCHIVE_NODE = os.getenv("ARCHIVE_NODE_URL", "http://204.12.168.157:26657")
BINARY       = os.getenv("INFERENCED_BINARY", "/Users/fixtwin/gonka/gonka/inferenced")

EPOCH         = 266
POC_START     = 4105361
EPOCH_END     = 4120751   # POC_START + 15391 - 1
SNAPSHOT_HEIGHT = POC_START - 500  # deploy_window = 500 blocks

KIMI_MODEL = "moonshotai/Kimi-K2.6"
QWEN_MODEL = "Qwen/Qwen3-235B-A22B-Instruct-2507-FP8"

# Weight scale factors (from chain params at height 4105361)
MODEL_FACTORS = {
    KIMI_MODEL: 1.2620856201975851,
    QWEN_MODEL: 0.3593,
}

# Delegation params (from chain params at height 4105361)
NO_PARTICIPATION_PENALTY = 0.15  # ModeNone: target didn't participate
DELEGATION_SHARE         = 0.05  # ModeDelegate: target participated
NET_EXTRA_PENALTY        = NO_PARTICIPATION_PENALTY - DELEGATION_SHARE  # 0.10

# Tokenomics
INITIAL_EPOCH_REWARD = 323_000_000_000_000  # ngonka
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
    """Fetch all PoC v2 store commits for epoch 266 at EPOCH_END height."""
    print(f"  Fetching PoC commits at height {EPOCH_END}...")
    d = run_cli(["query", "inference", "all-poc-v2-store-commits", str(POC_START)], height=EPOCH_END)
    if not d or "commits" not in d:
        raise RuntimeError("Failed to fetch PoC commits")
    result = {}
    for c in d["commits"]:
        addr  = c["participant_address"]
        model = c["model_id"]
        result.setdefault(addr, {})
        result[addr][model] = result[addr].get(model, 0) + int(c["count"])
    print(f"  -> {sum(len(v) for v in result.values())} commit entries for {len(result)} addresses")
    # Save reference copy
    with open(os.path.join(HERE, "epoch266_commits.json"), "w") as f:
        json.dump(d, f, indent=2)
    return result


def fetch_group_data():
    """Fetch epoch group data (actual on-chain weights) at EPOCH_END height."""
    print(f"  Fetching epoch group data at height {EPOCH_END}...")
    d = run_cli(["query", "inference", "show-epoch-group-data", str(EPOCH)], height=EPOCH_END)
    if not d:
        raise RuntimeError("Failed to fetch epoch group data")
    weights = {x["member_address"]: int(x.get("weight", 0))
               for x in d["epoch_group_data"]["validation_weights"]}
    print(f"  -> {len(weights)} members in epoch group")
    with open(os.path.join(HERE, "epoch266_group_data.json"), "w") as f:
        json.dump(d, f, indent=2)
    return weights


def fetch_performance(addresses):
    """Fetch rewarded_coins for each address in epoch 266."""
    print(f"  Fetching performance summaries for {len(addresses)} addresses...")
    result = {}
    for addr in sorted(addresses):
        d = run_cli(["query", "inference", "show-epoch-performance-summary-by-participant",
                     str(EPOCH), addr])
        if d:
            s = d.get("epochPerformanceSummary", {})
            result[addr] = int(s.get("rewarded_coins", 0))
        else:
            result[addr] = 0
    with open(os.path.join(HERE, "epoch266_performance.json"), "w") as f:
        json.dump([{"participant_id": k, "rewarded_coins": str(v)} for k, v in result.items()], f, indent=2)
    print(f"  -> done")
    return result


def fetch_delegations(addresses):
    """Fetch Kimi delegation targets for all addresses at SNAPSHOT_HEIGHT."""
    print(f"  Fetching delegations at snapshot height {SNAPSHOT_HEIGHT} for {len(addresses)} addresses...")
    result = {}
    for addr in sorted(addresses):
        d = run_cli(["query", "inference", "poc-delegation", addr], height=SNAPSHOT_HEIGHT)
        if d:
            result[addr] = {x["model_id"]: x["delegate_to"] for x in d.get("delegations", [])}
        else:
            result[addr] = {}
    print(f"  -> done")
    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(f"=== Epoch {EPOCH} Full Restitution Calculator ===\n")
    print("Fetching data from chain...")

    commits       = fetch_commits()
    group_weights = fetch_group_data()
    all_addresses = set(commits.keys()) | set(group_weights.keys())
    performance   = fetch_performance(all_addresses)
    delegations   = fetch_delegations(all_addresses)

    total_epoch_weight = sum(group_weights.values())
    print()

    # --- Identify excluded operators ---
    # Submitted Kimi nonces but never entered the epoch group
    excluded_operators = {
        addr for addr, models in commits.items()
        if KIMI_MODEL in models and addr not in group_weights
    }
    print(f"Excluded Kimi operators (commits present, not in epoch group): {len(excluded_operators)}")
    for a in sorted(excluded_operators):
        print(f"  {a}  kimi_nonces={commits[a].get(KIMI_MODEL, 0):,}")
    print()

    # -----------------------------------------------------------------------
    # Part 1: Nonce compensation
    # -----------------------------------------------------------------------
    print("--- Part 1: Nonce compensation ---")
    reconstructed = {}
    for addr, models in commits.items():
        w = 0.0
        for model_id, nonces in models.items():
            factor = MODEL_FACTORS.get(model_id)
            if factor is None:
                print(f"  WARNING: unknown model {model_id} for {addr}, skipping")
                continue
            w += nonces * factor
        reconstructed[addr] = w

    total_reconstructed_weight = sum(reconstructed.values())

    nonce_results = []
    for addr, rec_weight in reconstructed.items():
        actual = performance.get(addr, 0)
        # Unlike e267–e276 (ComputeGroupCap), zero-reward participants are NOT excluded
        # here. In e266 the attack was still active and unpatched (gateway patches landed
        # May 16–18, after e266 ran). An operator with zero rewards was excluded from the
        # epoch precisely because the attack crashed their vLLM node — zero rewards is
        # evidence of victimisation, not failure. Excluding them would make compensation
        # circular: attacked → got zero → excluded from compensation.
        fair_share   = rec_weight / total_reconstructed_weight * epoch_theoretical_reward
        compensation = max(0.0, fair_share - actual)
        if compensation > 0:
            nonce_results.append({
                "address":               addr,
                "reconstructed_weight":  rec_weight,
                "fair_share_ngonka":     int(fair_share),
                "fair_share_gonka":      fair_share / 1e9,
                "actual_rewards_ngonka": actual,
                "actual_rewards_gonka":  actual / 1e9,
                "compensation_ngonka":   int(compensation),
                "compensation_gonka":    compensation / 1e9,
            })

    nonce_results.sort(key=lambda x: x["compensation_ngonka"], reverse=True)
    total_nonce_comp = sum(r["compensation_ngonka"] for r in nonce_results)
    print(f"  Reconstructed total weight : {total_reconstructed_weight:,.2f}")
    print(f"  Affected participants      : {len(nonce_results)}")
    print(f"  Total compensation        : {total_nonce_comp / 1e9:,.4f} GONKA\n")

    # -----------------------------------------------------------------------
    # Part 2: Delegation compensation
    # -----------------------------------------------------------------------
    print("--- Part 2: Delegation compensation ---")

    kimi_delegators = []
    for addr, deleg_map in delegations.items():
        if addr in excluded_operators:
            continue
        kimi_target = deleg_map.get(KIMI_MODEL)
        if kimi_target and kimi_target in excluded_operators:
            kimi_delegators.append({"delegator": addr, "operator": kimi_target})

    print(f"  Delegators pointing Kimi at an excluded operator: {len(kimi_delegators)}")
    for d in kimi_delegators:
        print(f"    {d['delegator']}  ->  {d['operator']}")
    print()

    deleg_results = []
    for item in kimi_delegators:
        addr        = item["delegator"]
        chain_w     = group_weights.get(addr, 0)
        actual      = performance.get(addr, 0)
        original_w  = chain_w / (1 - NO_PARTICIPATION_PENALTY) if chain_w > 0 else 0.0
        extra_w     = original_w * NET_EXTRA_PENALTY
        compensation = extra_w / total_epoch_weight * epoch_theoretical_reward if total_epoch_weight > 0 else 0.0
        deleg_results.append({
            "address":                       addr,
            "excluded_operator":             item["operator"],
            "chain_weight_post_penalty":     chain_w,
            "reconstructed_original_weight": round(original_w, 2),
            "extra_weight_lost":             round(extra_w, 2),
            "actual_rewards_ngonka":         actual,
            "actual_rewards_gonka":          actual / 1e9,
            "compensation_ngonka":           int(compensation),
            "compensation_gonka":            compensation / 1e9,
        })

    deleg_results.sort(key=lambda x: x["compensation_ngonka"], reverse=True)
    total_deleg_comp = sum(r["compensation_ngonka"] for r in deleg_results)
    print(f"  Total delegation compensation : {total_deleg_comp / 1e9:,.4f} GONKA\n")

    # -----------------------------------------------------------------------
    # Print summaries
    # -----------------------------------------------------------------------
    print(f"{'='*100}")
    print(f"PART 1 — Nonce Compensation (Epoch {EPOCH})")
    print(f"{'='*100}")
    print(f"{'Address':<50} {'Rec.Weight':>12} {'Fair Share':>14} {'Actual':>14} {'Compensation':>14}")
    print(f"{'-'*100}")
    for r in nonce_results:
        print(f"{r['address']:<50} {r['reconstructed_weight']:>12,.1f} "
              f"{r['fair_share_gonka']:>14,.4f} {r['actual_rewards_gonka']:>14,.4f} "
              f"{r['compensation_gonka']:>14,.4f}")
    print(f"{'-'*100}")
    print(f"  Total: {total_nonce_comp / 1e9:,.4f} GONKA\n")

    print(f"{'='*110}")
    print(f"PART 2 — Delegation Compensation (Epoch {EPOCH})")
    print(f"{'='*110}")
    print(f"{'Address':<50} {'Orig weight':>12} {'Extra loss':>12} {'Actual':>14} {'Compensation':>14}")
    print(f"{'-'*110}")
    for r in deleg_results:
        print(f"{r['address']:<50} {r['reconstructed_original_weight']:>12,.1f} "
              f"{r['extra_weight_lost']:>12,.1f} {r['actual_rewards_gonka']:>14,.4f} "
              f"{r['compensation_gonka']:>14,.4f}")
    print(f"{'-'*110}")
    print(f"  Total: {total_deleg_comp / 1e9:,.4f} GONKA\n")

    grand_total = total_nonce_comp + total_deleg_comp
    print(f"{'='*50}")
    print(f"  GRAND TOTAL EPOCH {EPOCH} : {grand_total / 1e9:,.4f} GONKA")
    print(f"{'='*50}\n")

    # -----------------------------------------------------------------------
    # Save outputs
    # -----------------------------------------------------------------------
    def out(filename):
        return os.path.join(HERE, filename)

    with open(out("compensation_266_nonces.csv"), "w") as f:
        f.write("address,reconstructed_weight,fair_share_ngonka,fair_share_gonka,"
                "actual_rewards_ngonka,actual_rewards_gonka,compensation_ngonka,compensation_gonka\n")
        for r in nonce_results:
            f.write(f"{r['address']},{r['reconstructed_weight']:.2f},"
                    f"{r['fair_share_ngonka']},{r['fair_share_gonka']:.4f},"
                    f"{r['actual_rewards_ngonka']},{r['actual_rewards_gonka']:.4f},"
                    f"{r['compensation_ngonka']},{r['compensation_gonka']:.4f}\n")
    print(f"Saved to e266/compensation_266_nonces.csv")

    with open(out("compensation_266_delegation.csv"), "w") as f:
        f.write("address,excluded_operator,chain_weight_post_penalty,reconstructed_original_weight,"
                "extra_weight_lost,actual_rewards_ngonka,actual_rewards_gonka,"
                "compensation_ngonka,compensation_gonka\n")
        for r in deleg_results:
            f.write(f"{r['address']},{r['excluded_operator']},"
                    f"{r['chain_weight_post_penalty']},{r['reconstructed_original_weight']:.2f},"
                    f"{r['extra_weight_lost']:.2f},{r['actual_rewards_ngonka']},{r['actual_rewards_gonka']:.4f},"
                    f"{r['compensation_ngonka']},{r['compensation_gonka']:.4f}\n")
    print(f"Saved to e266/compensation_266_delegation.csv")

    # Combined
    combined = {}
    for r in nonce_results:
        combined[r["address"]] = {
            "address":                        r["address"],
            "nonce_compensation_ngonka":      r["compensation_ngonka"],
            "nonce_compensation_gonka":       r["compensation_gonka"],
            "delegation_compensation_ngonka": 0,
            "delegation_compensation_gonka":  0.0,
        }
    for r in deleg_results:
        addr = r["address"]
        if addr not in combined:
            combined[addr] = {
                "address":                        addr,
                "nonce_compensation_ngonka":      0,
                "nonce_compensation_gonka":       0.0,
                "delegation_compensation_ngonka": 0,
                "delegation_compensation_gonka":  0.0,
            }
        combined[addr]["delegation_compensation_ngonka"] = r["compensation_ngonka"]
        combined[addr]["delegation_compensation_gonka"]  = r["compensation_gonka"]

    combined_list = list(combined.values())
    for row in combined_list:
        row["total_compensation_ngonka"] = row["nonce_compensation_ngonka"] + row["delegation_compensation_ngonka"]
        row["total_compensation_gonka"]  = row["nonce_compensation_gonka"]  + row["delegation_compensation_gonka"]
    combined_list.sort(key=lambda x: x["total_compensation_ngonka"], reverse=True)

    with open(out("compensation_266_combined.csv"), "w") as f:
        f.write("address,nonce_compensation_ngonka,nonce_compensation_gonka,"
                "delegation_compensation_ngonka,delegation_compensation_gonka,"
                "total_compensation_ngonka,total_compensation_gonka\n")
        for row in combined_list:
            f.write(f"{row['address']},"
                    f"{row['nonce_compensation_ngonka']},{row['nonce_compensation_gonka']:.4f},"
                    f"{row['delegation_compensation_ngonka']},{row['delegation_compensation_gonka']:.4f},"
                    f"{row['total_compensation_ngonka']},{row['total_compensation_gonka']:.4f}\n")
    print(f"Saved to e266/compensation_266_combined.csv")

    with open(out("compensation_266.json"), "w") as f:
        json.dump({
            "epoch": EPOCH,
            "epoch_theoretical_reward_ngonka": int(epoch_theoretical_reward),
            "epoch_theoretical_reward_gonka":  epoch_theoretical_reward / 1e9,
            "total_reconstructed_weight":      total_reconstructed_weight,
            "total_epoch_weight_on_chain":     total_epoch_weight,
            "model_weight_factors":            MODEL_FACTORS,
            "delegation_params": {
                "no_participation_penalty": NO_PARTICIPATION_PENALTY,
                "delegation_share":         DELEGATION_SHARE,
                "net_extra_penalty":        NET_EXTRA_PENALTY,
                "snapshot_height":          SNAPSHOT_HEIGHT,
            },
            "excluded_operators": sorted(excluded_operators),
            "nonce_compensation": {
                "affected_participants": len(nonce_results),
                "total_ngonka":          total_nonce_comp,
                "total_gonka":           total_nonce_comp / 1e9,
                "entries":               nonce_results,
            },
            "delegation_compensation": {
                "affected_delegators": len(deleg_results),
                "total_ngonka":        total_deleg_comp,
                "total_gonka":         total_deleg_comp / 1e9,
                "entries":             deleg_results,
            },
            "grand_total_ngonka": int(grand_total),
            "grand_total_gonka":  grand_total / 1e9,
        }, f, indent=2)
    print(f"Saved to e266/compensation_266.json")


if __name__ == "__main__":
    main()
