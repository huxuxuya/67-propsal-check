#!/usr/bin/env python3
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
UPSTREAM = ROOT / "upstream" / "gonka-kimi-restitution"
OUT = DATA / "onchain_graph" / "proposal_67_local_graph.json"


def load_json(path):
    with path.open() as f:
        return json.load(f)


def extract_attr(events, event_type, key):
    for event in events:
        if event.get("type") != event_type:
            continue
        for attr in event.get("attributes", []):
            if attr.get("key") == key:
                return attr.get("value")
    return None


def compensation_rows():
    rows = []
    with (UPSTREAM / "aggregate_compensation.csv").open(newline="") as f:
        for row in csv.DictReader(f):
            total = float(row["total_gonka"])
            if total <= 0:
                continue
            rows.append({"address": row["address"], "totalGonka": total})
    return rows


def proposal_actors():
    proposal = load_json(DATA / "proposal_67.json")["proposal"]
    msg = proposal["messages"][0]
    return {
        "proposalId": proposal["id"],
        "proposer": proposal.get("proposer", ""),
        "messageSender": msg.get("sender", ""),
        "metadata": proposal.get("metadata", ""),
        "submitTime": proposal.get("submit_time", ""),
    }


def vote_rows():
    txs = load_json(DATA / "proposal_67_tx_search.json")["result"]["txs"]
    rows = []
    for tx in txs:
        voter = extract_attr(tx["tx_result"]["events"], "proposal_vote", "voter")
        option = extract_attr(tx["tx_result"]["events"], "proposal_vote", "option")
        if not voter:
            continue
        rows.append(
            {
                "voter": voter,
                "height": int(tx["height"]),
                "index": int(tx["index"]),
                "txHash": tx["hash"],
                "optionRaw": option,
            }
        )
    return rows


def delegation_rows():
    path = UPSTREAM / "e266" / "epoch266_kimi_delegators.json"
    if not path.exists():
        return []
    raw = load_json(path)
    return [
        {
            "delegator": row.get("delegator", ""),
            "operator": row.get("operator", ""),
            "snapshotHeight": raw.get("snapshot_height"),
            "sourceFile": str(path.relative_to(ROOT)),
        }
        for row in raw.get("kimi_delegators", [])
        if row.get("delegator") and row.get("operator")
    ]


def epoch_commit_rows():
    rows = []
    for path in sorted(UPSTREAM.glob("e*/epoch*_commits.json")):
        epoch = "".join(ch for ch in path.parent.name if ch.isdigit())
        raw = load_json(path)
        for commit in raw.get("commits", []):
            rows.append(
                {
                    "epoch": int(epoch) if epoch else None,
                    "participant": commit.get("participant_address", ""),
                    "hexPubKey": commit.get("hex_pub_key", ""),
                    "rootHash": commit.get("root_hash", ""),
                    "modelId": commit.get("model_id", ""),
                    "count": commit.get("count", 0),
                    "sourceFile": str(path.relative_to(ROOT)),
                }
            )
    return rows


def summarize_links(snapshot):
    roles = defaultdict(set)
    actor_totals = defaultdict(float)
    for row in snapshot["compensationOutputs"]:
        roles[row["address"]].add("recipient")
        actor_totals[row["address"]] += row["totalGonka"]
    for row in snapshot["votes"]:
        roles[row["voter"]].add("voter")
    if snapshot["proposalActors"].get("proposer"):
        roles[snapshot["proposalActors"]["proposer"]].add("proposer")
    if snapshot["proposalActors"].get("messageSender"):
        roles[snapshot["proposalActors"]["messageSender"]].add("message_sender")
    for row in snapshot["delegations"]:
        roles[row["delegator"]].add("delegator")
        roles[row["operator"]].add("operator")
    for row in snapshot["epochCommits"]:
        if row["participant"]:
            roles[row["participant"]].add("epoch_commit_participant")

    return {
        "actors": [
            {
                "address": address,
                "roles": sorted(values),
                "totalGonka": round(actor_totals[address], 6),
            }
            for address, values in sorted(roles.items())
        ],
        "roleCounts": dict(Counter(role for values in roles.values() for role in values)),
    }


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    snapshot = {
        "source": {
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "mode": "local saved snapshots only",
        },
        "proposalActors": proposal_actors(),
        "compensationOutputs": compensation_rows(),
        "votes": vote_rows(),
        "delegations": delegation_rows(),
        "epochCommits": epoch_commit_rows(),
    }
    snapshot["summary"] = summarize_links(snapshot)
    OUT.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n")
    print(f"Wrote {OUT}")
    print(f"Actors: {len(snapshot['summary']['actors'])}; delegations: {len(snapshot['delegations'])}; commits: {len(snapshot['epochCommits'])}")


if __name__ == "__main__":
    main()
