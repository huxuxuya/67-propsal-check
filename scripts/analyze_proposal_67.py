#!/usr/bin/env python3
import csv
import json
from collections import defaultdict
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "upstream" / "gonka-kimi-restitution"
DATA = ROOT / "data"
REPORTS = ROOT / "reports"

OPTION_NAMES = {
    1: "yes",
    2: "abstain",
    3: "no",
    4: "no_with_veto",
}


def load_json(path):
    with path.open() as f:
        return json.load(f)


def read_recipients():
    rows = []
    with (UPSTREAM / "aggregate_compensation.csv").open() as f:
        for row in csv.DictReader(f):
            total = Decimal(row["total_gonka"])
            if total <= 0:
                continue
            epochs = [k for k, v in row.items() if k.startswith("e") and Decimal(v) > 0]
            rows.append({
                "address": row["address"],
                "total_gonka": total,
                "epochs": ",".join(epochs),
                "attack_e265_e266": Decimal(row["e265"]) + Decimal(row["e266"]),
                "cap_e267_e276": sum(Decimal(row[f"e{e}"]) for e in range(267, 277)),
            })
    rows.sort(key=lambda r: r["total_gonka"], reverse=True)
    return rows


def read_proposal_outputs():
    proposal = load_json(DATA / "proposal_67.json")["proposal"]
    outputs = proposal["messages"][0]["outputs"]
    return {
        o["recipient"]: Decimal(o["amount"][0]["amount"]) / Decimal(1_000_000_000)
        for o in outputs
    }


def extract_attr(events, event_type, key):
    for event in events:
        if event.get("type") != event_type:
            continue
        for attr in event.get("attributes", []):
            if attr.get("key") == key:
                return attr.get("value")
    return None


def read_votes():
    raw = load_json(DATA / "proposal_67_tx_search.json")
    txs = raw["result"]["txs"]
    all_rows = []
    latest = {}

    for tx in txs:
        events = tx["tx_result"]["events"]
        voter = extract_attr(events, "proposal_vote", "voter")
        option_raw = extract_attr(events, "proposal_vote", "option")
        if not voter or not option_raw:
            continue
        options = json.loads(option_raw)
        weighted = []
        for item in options:
            option = OPTION_NAMES[int(item["option"])]
            weight = Decimal(item["weight"])
            weighted.append((option, weight))
        height = int(tx["height"])
        index = int(tx["index"])
        row = {
            "voter": voter,
            "height": height,
            "index": index,
            "hash": tx["hash"],
            "weighted_options": weighted,
        }
        all_rows.append(row)
        if voter not in latest or (height, index) >= (latest[voter]["height"], latest[voter]["index"]):
            latest[voter] = row

    final_rows = sorted(latest.values(), key=lambda r: (r["height"], r["index"], r["voter"]))
    return all_rows, final_rows


def read_validator_labels():
    path = DATA / "validators.json"
    if not path.exists():
        return {}, {}
    validators = load_json(path).get("validators", [])
    labels = {}
    consensus_labels = {}
    for val in validators:
        op = val.get("operator_address", "")
        if not op.startswith("gonkavaloper"):
            continue
        account = "gonka" + op[len("gonkavaloper"):]
        desc = val.get("description", {})
        moniker = desc.get("moniker") or ""
        website = desc.get("website") or ""
        if moniker and moniker != op:
            labels[account] = moniker
            consensus_labels[val.get("consensus_pubkey", {}).get("key", "")] = moniker
        elif website:
            labels[account] = website
            consensus_labels[val.get("consensus_pubkey", {}).get("key", "")] = website
    return labels, consensus_labels


def read_participant_details():
    path = DATA / "participants_by_address.json"
    if not path.exists():
        return {}
    return load_json(path)


def public_label(address, account_labels, consensus_labels, participant_details):
    if address in account_labels:
        return account_labels[address]
    p = participant_details.get(address) or {}
    validator_key = p.get("validator_key") or ""
    if validator_key in consensus_labels:
        return consensus_labels[validator_key]
    return p.get("inference_url") or ""


def write_csv(path, fieldnames, rows):
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def fmt_gonka(value):
    return f"{value:,.2f}"


def md_cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def main():
    REPORTS.mkdir(exist_ok=True)
    recipients = read_recipients()
    proposal_outputs = read_proposal_outputs()
    account_labels, consensus_labels = read_validator_labels()
    participant_details = read_participant_details()
    all_votes, final_votes = read_votes()
    recipient_set = {r["address"] for r in recipients}

    total = sum(r["total_gonka"] for r in recipients)
    attack_total = sum(r["attack_e265_e266"] for r in recipients)
    cap_total = sum(r["cap_e267_e276"] for r in recipients)

    recipient_rows = []
    for r in recipients:
        onchain = proposal_outputs.get(r["address"], Decimal(0))
        p = participant_details.get(r["address"]) or {}
        recipient_rows.append({
            "address": r["address"],
            "label": public_label(r["address"], account_labels, consensus_labels, participant_details),
            "inference_url": p.get("inference_url", ""),
            "status": p.get("status", ""),
            "epochs_completed": p.get("epochs_completed", ""),
            "total_gonka": f"{r['total_gonka']:.6f}",
            "attack_e265_e266_gonka": f"{r['attack_e265_e266']:.6f}",
            "cap_e267_e276_gonka": f"{r['cap_e267_e276']:.6f}",
            "epochs": r["epochs"],
            "onchain_output_gonka": f"{onchain:.6f}",
            "matches_onchain_output": str(abs(onchain - r["total_gonka"]) < Decimal("0.00001")).lower(),
        })

    vote_rows = []
    vote_summary = defaultdict(Decimal)
    recipient_voters = []
    for v in final_votes:
        option_text = ";".join(f"{name}:{weight}" for name, weight in v["weighted_options"])
        for name, weight in v["weighted_options"]:
            vote_summary[name] += weight
        is_recipient = v["voter"] in recipient_set
        if is_recipient:
            recipient_voters.append(v["voter"])
        vote_rows.append({
            "voter": v["voter"],
            "label": public_label(v["voter"], account_labels, consensus_labels, participant_details),
            "is_compensation_recipient": str(is_recipient).lower(),
            "final_vote": option_text,
            "height": v["height"],
            "tx_hash": v["hash"],
        })

    write_csv(
        REPORTS / "proposal_67_recipients.csv",
        ["address", "label", "inference_url", "status", "epochs_completed", "total_gonka", "attack_e265_e266_gonka", "cap_e267_e276_gonka", "epochs", "onchain_output_gonka", "matches_onchain_output"],
        recipient_rows,
    )
    write_csv(
        REPORTS / "proposal_67_final_votes.csv",
        ["voter", "label", "is_compensation_recipient", "final_vote", "height", "tx_hash"],
        vote_rows,
    )

    top = recipients[:12]
    md = []
    md.append("# Proposal 67 Kimi Restitution Analysis")
    md.append("")
    md.append("Source data: upstream `gonka-kimi-restitution`, on-chain proposal #67, and Tendermint tx index for `proposal_vote.proposal_id='67'`.")
    md.append("")
    md.append("## Executive summary")
    md.append("")
    md.append(f"- Proposal #67 passed. Final tally: yes 319,920; no 150; abstain 744; no_with_veto 84,623.")
    md.append(f"- Compensation outputs: {len(recipients)} non-zero recipients, total {fmt_gonka(total)} GONKA.")
    md.append(f"- e265-e266 external attack component: {fmt_gonka(attack_total)} GONKA.")
    md.append(f"- e267-e276 ComputeGroupCap component: {fmt_gonka(cap_total)} GONKA.")
    md.append(f"- Multiplier from the original e265-only visible damage of 30,592.10 GONKA to final proposal: {total / Decimal('30592.10'):.2f}x.")
    md.append(f"- Final vote txs: {len(all_votes)} txs, {len(final_votes)} unique voters after last-vote-wins consolidation.")
    md.append(f"- Compensation recipients who also voted: {len(set(recipient_voters))}.")
    md.append("")
    md.append("## Why 30k became 946k")
    md.append("")
    md.append("The 30,592.10 GONKA figure is only epoch 265 CPoC degradation for 3 operators. The proposal also includes epoch 266 nonce exclusion and delegation loss, then ten more epochs where the previous epoch's collapsed Kimi weight made ComputeGroupCap underpay otherwise healthy Kimi operators.")
    md.append("")
    md.append("| Component | GONKA | Share |")
    md.append("|---|---:|---:|")
    md.append(f"| e265-e266 external attack and nonce/delegation loss | {fmt_gonka(attack_total)} | {attack_total / total * 100:.1f}% |")
    md.append(f"| e267-e276 ComputeGroupCap underpayment | {fmt_gonka(cap_total)} | {cap_total / total * 100:.1f}% |")
    md.append(f"| Total | {fmt_gonka(total)} | 100.0% |")
    md.append("")
    md.append("## Top recipients")
    md.append("")
    md.append("| Address | Label | Total GONKA | Attack e265-e266 | Cap e267-e276 |")
    md.append("|---|---|---:|---:|---:|")
    for r in top:
        label = md_cell(public_label(r["address"], account_labels, consensus_labels, participant_details))
        md.append(f"| `{r['address']}` | {label} | {fmt_gonka(r['total_gonka'])} | {fmt_gonka(r['attack_e265_e266'])} | {fmt_gonka(r['cap_e267_e276'])} |")
    md.append("")
    md.append("## Final voters")
    md.append("")
    md.append("| Voter | Label | Recipient? | Final vote | Height |")
    md.append("|---|---|---:|---|---:|")
    for row in vote_rows:
        md.append(f"| `{row['voter']}` | {md_cell(row['label'])} | {row['is_compensation_recipient']} | {md_cell(row['final_vote'])} | {row['height']} |")
    md.append("")
    md.append("## Notes")
    md.append("")
    md.append("- Labels are public validator descriptions matched by validator key, falling back to public participant inference URLs. Empty label means no reliable public label was found in this pass.")
    md.append("- The final on-chain tally is voting-power weighted; the voter table is address-level and includes weighted vote options where a voter split their vote.")
    md.append("- The GRC off-chain vote in the upstream README is separate: 2 include, 6 exclude, 1 abstain. The repository does not identify those committee voters.")
    (REPORTS / "proposal_67_analysis.md").write_text("\n".join(md) + "\n")


if __name__ == "__main__":
    main()
