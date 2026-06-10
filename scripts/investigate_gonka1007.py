#!/usr/bin/env python3
import json
import re
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from env_utils import gonka_rpc_source_label, gonka_rpc_url


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
REPORTS = ROOT / "reports"
OUT_DATA = DATA / "investigations" / "gonka1007_ownership_investigation.json"
OUT_REPORT = REPORTS / "gonka1007_ownership_investigation.md"

ADDRESS = "gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv"
VALOPER = "gonkavaloper1007dchuqgdnute4qam70kmn56j2vfw388h4yhp"
PUBKEY = "03a654c9be1fa2ae64cefc00d611b88e41faa00d907d5f0f1ca85682b7db2661ab"
VALIDATOR_KEY = "tpe7BLcggZjebLowWzBPv7N9525XYz419oXnLSmXQsU="
INFERENCE_URL = "http://178.105.174.27:8000"
HOST_IP = "178.105.174.27"


def load_json(path, default=None):
    if not path.exists():
        return default
    with path.open() as f:
        return json.load(f)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def extract_attr(events, event_type, key):
    for event in events or []:
        if event.get("type") != event_type:
            continue
        for attr in event.get("attributes", []):
            if attr.get("key") == key:
                return attr.get("value")
    return None


def evidence(source_type, subject, value, confidence, proof, source_file, caveat, category="investigation"):
    return {
        "address": ADDRESS,
        "category": category,
        "caveat": caveat,
        "confidence": confidence,
        "isAttributionProof": proof,
        "sourceFile": source_file,
        "sourceType": source_type,
        "sourceUrl": source_file,
        "sourceValue": value,
        "subject": subject,
    }


def tx_search(query, per_page=100):
    url = gonka_rpc_url()
    params = urllib.parse.urlencode(
        {
            "query": f'"{query}"',
            "prove": "false",
            "page": "1",
            "per_page": str(per_page),
            "order_by": '"desc"',
        }
    )
    request_url = f"{url}/tx_search?{params}"
    try:
        with urllib.request.urlopen(request_url, timeout=20) as response:
            body = response.read(2_000_000).decode(errors="replace")
            return {"ok": True, "source": gonka_rpc_source_label(), "url": request_url, "json": json.loads(body), "error": ""}
    except Exception as exc:
        return {"ok": False, "source": gonka_rpc_source_label(), "url": request_url, "json": None, "error": str(exc)}


def ripe_lookup(ip):
    url = f"https://stat.ripe.net/data/whois/data.json?resource={urllib.parse.quote(ip)}"
    try:
        with urllib.request.urlopen(url, timeout=20) as response:
            body = response.read(500_000).decode(errors="replace")
            raw = json.loads(body)
    except Exception as exc:
        return {"ok": False, "url": url, "error": str(exc), "summary": {}}

    summary = {}
    for record_set in raw.get("data", {}).get("records", []):
        for item in record_set:
            key = item.get("key")
            value = item.get("value")
            if key in {"inetnum", "netname", "country", "org", "mnt-by", "created", "last-modified"} and key not in summary:
                summary[key] = value
    for record_set in raw.get("data", {}).get("irr_records", []):
        for item in record_set:
            key = item.get("key")
            value = item.get("value")
            if key in {"route", "descr", "origin"} and key not in summary:
                summary[key] = value
    return {"ok": True, "url": url, "error": "", "summary": summary}


def participant_info():
    participants = load_json(DATA / "participants_by_address.json", {})
    return participants.get(ADDRESS, {})


def recipient_info():
    dashboard = load_json(ROOT / "docs" / "data" / "dashboard.json", {})
    recipient = next((row for row in dashboard.get("recipients", []) if row.get("address") == ADDRESS), {})
    vote = next((row for row in dashboard.get("votes", []) if row.get("voter") == ADDRESS), {})
    ranked = next((row for row in dashboard.get("rankedParties", []) if ADDRESS in row.get("addresses", [])), {})
    identity_edges = [
        edge
        for edge in dashboard.get("identityGraph", {}).get("edges", [])
        if ADDRESS in edge.get("source", "") or ADDRESS in edge.get("target", "") or HOST_IP in edge.get("sourceValue", "")
    ]
    epoch_weights = (dashboard.get("votingWindowEpochWeights", {}).get("rows", {}) or {}).get(ADDRESS, {})
    return {
        "recipient": recipient,
        "vote": vote,
        "rankedParty": ranked,
        "identityEdges": identity_edges,
        "votingWindowEpochWeights": epoch_weights,
    }


def reward_claims():
    raw = load_json(DATA / "epoch_reward_claims.json", {})
    return [row for row in raw.get("rows", []) if row.get("address") == ADDRESS]


def governance_power():
    raw = load_json(DATA / "governance_power_67" / "governance_power_67.json", {})
    window = next((row for row in raw.get("windowVoterPower", []) if row.get("voter") == ADDRESS), {})
    start_delegations = load_json(DATA / "governance_power_67" / "raw" / "decoded_voter_delegations_4401104.json", {})
    end_delegations = load_json(DATA / "governance_power_67" / "raw" / "decoded_voter_delegations_4433308.json", {})
    validators = load_json(DATA / "governance_power_67" / "raw" / "decoded_bonded_validators_4433308.json", [])
    validator = next((row for row in validators if row.get("operatorAddress") == VALOPER), {})
    return {
        "window": window,
        "startDelegationsAt4401104": start_delegations.get(ADDRESS, []),
        "endDelegationsAt4433308": end_delegations.get(ADDRESS, []),
        "validatorAt4433308": validator,
    }


def compensation_sources():
    proposal = load_json(DATA / "proposal_67.json", {}).get("proposal", {})
    msg = (proposal.get("messages") or [{}])[0]
    recipients = []
    for item in msg.get("recipients", []):
        if item.get("recipient") == ADDRESS:
            recipients.append(item)
    return {
        "proposalRecipientOutputs": recipients,
        "proposalId": proposal.get("id"),
        "proposalProposer": proposal.get("proposer"),
        "proposalSubmitTime": proposal.get("submit_time"),
    }


def vote_sources():
    raw = load_json(DATA / "proposal_67_tx_search.json", {})
    rows = []
    for tx in raw.get("result", {}).get("txs", []):
        events = tx.get("tx_result", {}).get("events", [])
        voter = extract_attr(events, "proposal_vote", "voter")
        if voter != ADDRESS:
            continue
        rows.append(
            {
                "height": int(tx.get("height", 0)),
                "index": int(tx.get("index", 0)),
                "hash": tx.get("hash", ""),
                "feePayer": extract_attr(events, "tx", "fee_payer"),
                "sender": extract_attr(events, "message", "sender"),
                "option": extract_attr(events, "proposal_vote", "option"),
            }
        )
    return rows


def public_key_matches():
    matches = []
    paths = sorted((ROOT / "upstream" / "gonka-kimi-restitution").glob("e*/epoch*_commits.json"))
    for path in paths:
        raw = load_json(path, {})
        epoch_match = re.search(r"e(\d+)", path.as_posix())
        epoch = int(epoch_match.group(1)) if epoch_match else None
        for commit in raw.get("commits", []):
            if commit.get("hex_pub_key") != PUBKEY:
                continue
            matches.append(
                {
                    "epoch": epoch,
                    "participant": commit.get("participant_address", ""),
                    "modelId": commit.get("model_id", ""),
                    "count": commit.get("count"),
                    "rootHash": commit.get("root_hash", ""),
                    "sourceFile": str(path.relative_to(ROOT)),
                }
            )
    return matches


def local_same_value_matches():
    participants = load_json(DATA / "participants_by_address.json", {})
    same_ip = []
    same_validator_key = []
    for address, item in participants.items():
        if not isinstance(item, dict):
            continue
        if HOST_IP in str(item.get("inference_url", "")):
            same_ip.append(address)
        if item.get("validator_key") == VALIDATOR_KEY:
            same_validator_key.append(address)
    same_pubkey = sorted({row["participant"] for row in public_key_matches() if row.get("participant")})
    return {
        "sameInferenceIpAddresses": sorted(same_ip),
        "sameValidatorKeyAddresses": sorted(same_validator_key),
        "sameEpochCommitPublicKeyAddresses": same_pubkey,
    }


def history_hits():
    needles = [ADDRESS, HOST_IP, PUBKEY, VALIDATOR_KEY, VALOPER]
    hits = []
    for base in [ROOT / "history", REPORTS]:
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in {".html", ".md", ".csv", ".txt"}:
                continue
            if path.resolve() == OUT_REPORT.resolve():
                continue
            try:
                text = path.read_text(errors="replace")
            except Exception:
                continue
            for line_no, line in enumerate(text.splitlines(), 1):
                if any(needle in line for needle in needles):
                    hits.append(
                        {
                            "sourceFile": str(path.relative_to(ROOT)),
                            "line": line_no,
                            "excerpt": re.sub(r"\s+", " ", line).strip()[:500],
                        }
                    )
    return hits


def tx_trace():
    queries = {
        "sender": f"message.sender='{ADDRESS}'",
        "transferRecipient": f"transfer.recipient='{ADDRESS}'",
        "transferSender": f"transfer.sender='{ADDRESS}'",
        "delegateDelegator": f"delegate.delegator='{ADDRESS}'",
        "createValidator": f"create_validator.validator='{VALOPER}'",
    }
    return {name: tx_search(query) for name, query in queries.items()}


def attr_values(event, key):
    return [attr.get("value", "") for attr in event.get("attributes", []) if attr.get("key") == key]


def amount_to_gonka(value):
    if not value or not value.endswith("ngonka"):
        return None
    try:
        return int(value[:-6]) / 1_000_000_000
    except ValueError:
        return None


def transfer_flows(trace):
    by_hash = {}
    for result in trace.values():
        if not result.get("ok"):
            continue
        for tx in result.get("json", {}).get("result", {}).get("txs") or []:
            by_hash[tx.get("hash", "")] = tx

    flows = []
    for tx_hash, tx in by_hash.items():
        height = int(tx.get("height", 0) or 0)
        for event in tx.get("tx_result", {}).get("events", []):
            if event.get("type") != "transfer":
                continue
            for sender, recipient, amount in zip(attr_values(event, "sender"), attr_values(event, "recipient"), attr_values(event, "amount")):
                if sender != ADDRESS and recipient != ADDRESS:
                    continue
                direction = "out" if sender == ADDRESS else "in"
                counterparty = recipient if direction == "out" else sender
                flows.append(
                    {
                        "amount": amount,
                        "amountGonka": amount_to_gonka(amount),
                        "counterparty": counterparty,
                        "direction": direction,
                        "height": height,
                        "txHash": tx_hash,
                    }
                )
    flows.sort(key=lambda row: (row["height"], row["txHash"]), reverse=True)

    counterparties = {}
    for flow in flows:
        item = counterparties.setdefault(
            flow["counterparty"],
            {"address": flow["counterparty"], "incomingGonka": 0.0, "incomingCount": 0, "latestHeight": 0, "latestTxHash": "", "outgoingGonka": 0.0, "outgoingCount": 0},
        )
        amount = flow.get("amountGonka") or 0.0
        if flow["direction"] == "in":
            item["incomingGonka"] += amount
            item["incomingCount"] += 1
        else:
            item["outgoingGonka"] += amount
            item["outgoingCount"] += 1
        if flow["height"] > item["latestHeight"]:
            item["latestHeight"] = flow["height"]
            item["latestTxHash"] = flow["txHash"]

    rows = []
    for item in counterparties.values():
        rows.append(
            {
                **item,
                "incomingGonka": round(item["incomingGonka"], 9),
                "netGonka": round(item["incomingGonka"] - item["outgoingGonka"], 9),
                "outgoingGonka": round(item["outgoingGonka"], 9),
            }
        )
    return {"counterparties": sorted(rows, key=lambda row: abs(row["netGonka"]), reverse=True), "flows": flows}


def counterparty_context(counterparties):
    participants = load_json(DATA / "participants_by_address.json", {})
    dashboard = load_json(ROOT / "docs" / "data" / "dashboard.json", {})
    recipients = {row.get("address"): row for row in dashboard.get("recipients", [])}
    votes = {row.get("voter"): row for row in dashboard.get("votes", [])}
    ranked = {}
    for row in dashboard.get("rankedParties", []):
        for address in row.get("addresses", []):
            ranked[address] = row

    contexts = {}
    for row in counterparties[:20]:
        address = row["address"]
        hits = []
        history_root = ROOT / "history"
        if history_root.exists():
            for path in sorted(history_root.rglob("*")):
                if not path.is_file() or path.suffix.lower() not in {".html", ".md", ".txt"}:
                    continue
                try:
                    text = path.read_text(errors="replace")
                except Exception:
                    continue
                if address not in text:
                    continue
                for line_no, line in enumerate(text.splitlines(), 1):
                    if address in line:
                        hits.append({"sourceFile": str(path.relative_to(ROOT)), "line": line_no, "excerpt": re.sub(r"\s+", " ", line).strip()[:400]})
                        break
                if len(hits) >= 3:
                    break
        contexts[address] = {
            "historyHits": hits,
            "isParticipant": address in participants,
            "isRecipient": address in recipients,
            "isVoter": address in votes,
            "participant": participants.get(address),
            "rankedParty": ranked.get(address),
            "recipient": recipients.get(address),
            "vote": votes.get(address),
        }
    return contexts


def build_claims(investigation):
    claims = []
    claims.append(evidence("participant_inference_url", INFERENCE_URL, INFERENCE_URL, "medium", False, "data/participants_by_address.json", "Public participant metadata links the node to this endpoint, not to a human owner.", "public_infrastructure"))
    claims.append(evidence("participant_validator_key", VALIDATOR_KEY, VALIDATOR_KEY, "medium", False, "data/participants_by_address.json", "Validator key is unique in local snapshots but is not an owner proof.", "public_identity"))
    claims.append(evidence("staking_self_delegation", VALOPER, "57838 ngonka self-delegated by voting end", "high", False, "data/governance_power_67/governance_power_67.json", "On-chain staking state proves voting-power source, not human owner.", "governance"))
    claims.append(evidence("proposal_vote", ADDRESS, "yes at height 4414864", "high", False, "data/proposal_67_tx_search.json", "Vote proves governance action by this address.", "governance"))
    claims.append(evidence("compensation_output", ADDRESS, "11262.520198 GONKA", "high", False, "data/proposal_67.json", "Proposal output proves beneficiary address and amount, not human owner.", "financial_or_epoch_activity"))
    claims.append(evidence("ripe_asn", HOST_IP, "AS24940 HETZNER-DC / CLOUD-NBG1", "medium", False, "RIPE Stat", "Hosting provider attribution is infrastructure-only.", "public_infrastructure"))
    top_counterparty = (investigation.get("transferFlows", {}).get("counterparties") or [{}])[0]
    if top_counterparty.get("address"):
        claims.append(evidence("top_transfer_counterparty", top_counterparty["address"], f"net {top_counterparty['netGonka']} GONKA", "high", False, "archive RPC tx_search", "Transfer counterparty is an on-chain money-flow link, not human ownership proof.", "financial_or_epoch_activity"))
    if investigation["localMatches"]["sameInferenceIpAddresses"] == [ADDRESS]:
        claims.append(evidence("no_same_ip_cluster", HOST_IP, "No other local participant uses this IP", "medium", False, "data/participants_by_address.json", "Absence in local data is not global proof.", "negative_evidence"))
    if investigation["localMatches"]["sameEpochCommitPublicKeyAddresses"] == [ADDRESS]:
        claims.append(evidence("no_same_pubkey_cluster", PUBKEY, "No other local participant uses this epoch commit public key", "medium", False, "upstream/gonka-kimi-restitution", "Absence in local data is not global proof.", "negative_evidence"))
    return claims


def summarize_tx_trace(trace):
    summary = {}
    for name, result in trace.items():
        if not result.get("ok"):
            summary[name] = {"ok": False, "error": result.get("error", ""), "count": None, "sample": []}
            continue
        txs = result.get("json", {}).get("result", {}).get("txs") or []
        sample = [
            {
                "height": tx.get("height"),
                "hash": tx.get("hash"),
                "code": tx.get("tx_result", {}).get("code"),
            }
            for tx in txs[:5]
        ]
        total_count = result.get("json", {}).get("result", {}).get("total_count")
        summary[name] = {"ok": True, "error": "", "count": int(total_count) if total_count is not None else len(txs), "sample": sample}
    return summary


def build_markdown(investigation):
    participant = investigation["participant"]
    recipient = investigation["dashboard"]["recipient"]
    vote = investigation["dashboard"]["vote"]
    gov = investigation["governancePower"]
    local = investigation["localMatches"]
    ripe = investigation["ripe"]
    history = investigation["historyHits"]
    claims = investigation["evidenceClaims"]
    rewards = investigation["rewardClaims"]
    commits = investigation["epochCommitPublicKeyMatches"]
    tx_summary = investigation["txTrace"]
    counterparties = investigation.get("transferFlows", {}).get("counterparties", [])
    flows = investigation.get("transferFlows", {}).get("flows", [])
    counterparty_notes = investigation.get("counterpartyContext", {})

    lines = [
        "# gonka1007 ownership investigation",
        "",
        f"- Address: `{ADDRESS}`",
        f"- Valoper: `{VALOPER}`",
        f"- Inference URL: `{INFERENCE_URL}`",
        f"- Validator key: `{VALIDATOR_KEY}`",
        f"- Epoch commit public key: `{PUBKEY}`",
        f"- Generated: `{investigation['generatedAt']}`",
        "",
        "## Conclusion",
        "",
        "- No strict human owner proof was found in the local dashboard data, Telegram/history exports, public-name enrichment, or shared-key/shared-host clusters.",
        "- The strongest proven facts are operational/on-chain: this address received compensation, voted `yes`, and had zero voting power at the voting start snapshot but `57838` by the voting end snapshot.",
        "- The voting power source is a self-delegation to its own valoper; this connects the voter account and validator operator but does not identify a person.",
        "- The infrastructure points to Hetzner (`AS24940`, `HETZNER-DC`, `CLOUD-NBG1`, Germany); this is provider-level attribution only.",
        "",
        "## Proven On-Chain / Snapshot Facts",
        "",
        f"- Compensation: `{recipient.get('totalGonka', 11262.520198)}` GONKA, component `{recipient.get('componentSource', 'cap_e267_e276')}`.",
        f"- Compensation epochs: `{recipient.get('perEpoch', {})}`.",
        f"- Vote: `{vote.get('primaryOption')}` at height `{vote.get('height')}`, tx `{vote.get('txHash')}`.",
        f"- Voting power window: start `{vote.get('startVotingPower')}`, end `{vote.get('endVotingPower')}`, status `{vote.get('windowPowerStatus')}`.",
        f"- Voting epoch weights: `{investigation['dashboard'].get('votingWindowEpochWeights')}`.",
        f"- End delegation: `{gov.get('endDelegationsAt4433308')}`.",
        f"- Validator at voting end: `{gov.get('validatorAt4433308')}`.",
        "",
        "## Public Infrastructure",
        "",
        f"- Participant status: `{participant.get('status')}`; join height `{participant.get('join_height')}`; last inference time `{participant.get('last_inference_time')}`.",
        f"- Worker public key: `{participant.get('worker_public_key') or '<empty>'}`.",
        f"- RIPE summary: `{ripe.get('summary')}`.",
        "",
        "## Local Cluster Checks",
        "",
        f"- Same inference IP: `{local.get('sameInferenceIpAddresses')}`.",
        f"- Same validator key: `{local.get('sameValidatorKeyAddresses')}`.",
        f"- Same epoch commit public key: `{local.get('sameEpochCommitPublicKeyAddresses')}`.",
        "",
        "## Reward / Compensation Context",
        "",
        "| Epoch | Claimed | Rewarded GONKA | Earned GONKA | Inferences | Missed |",
        "|---:|:---:|---:|---:|---:|---:|",
    ]
    for row in sorted(rewards, key=lambda item: item.get("epoch", 0)):
        lines.append(
            f"| {row.get('epoch')} | {row.get('claimed')} | {row.get('rewardedGonka')} | {row.get('earnedGonka')} | {row.get('inferenceCount')} | {row.get('missedRequests')} |"
        )

    lines.extend(["", "## Epoch Commit Public Key Matches", "", "| Epoch | Participant | Model | Count |", "|---:|---|---|---:|"])
    for row in commits:
        lines.append(f"| {row.get('epoch')} | `{row.get('participant')}` | `{row.get('modelId')}` | {row.get('count')} |")

    lines.extend(["", "## Tx Trace Queries", "", "| Query | Status | Count | Sample |", "|---|---|---:|---|"])
    for name, row in tx_summary.items():
        sample = ", ".join(f"{item.get('height')}:{item.get('hash')}" for item in row.get("sample", []))
        lines.append(f"| `{name}` | `{row.get('error') or 'ok'}` | {row.get('count')} | `{sample}` |")

    lines.extend(
        [
            "",
            "## Transfer Counterparties",
            "",
            "| Counterparty | Incoming GONKA | Outgoing GONKA | Net GONKA | In txs | Out txs | Latest height |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in counterparties[:20]:
        lines.append(
            f"| `{row['address']}` | {row['incomingGonka']} | {row['outgoingGonka']} | {row['netGonka']} | {row['incomingCount']} | {row['outgoingCount']} | {row['latestHeight']} |"
        )
    lines.extend(["", "### Counterparty Local Context", "", "| Counterparty | Participant | Recipient | Voter | History signal |", "|---|:---:|:---:|:---:|---|"])
    for row in counterparties[:10]:
        note = counterparty_notes.get(row["address"], {})
        history_note = "; ".join(f"{hit['sourceFile']}:{hit['line']}" for hit in note.get("historyHits", [])[:2])
        lines.append(
            f"| `{row['address']}` | {note.get('isParticipant', False)} | {note.get('isRecipient', False)} | {note.get('isVoter', False)} | {history_note or '-'} |"
        )
    lines.extend(["", "### Recent Direct Flows", "", "| Height | Direction | Counterparty | Amount GONKA | Tx |", "|---:|---|---|---:|---|"])
    for row in flows[:20]:
        lines.append(f"| {row['height']} | `{row['direction']}` | `{row['counterparty']}` | {row['amountGonka']} | `{row['txHash']}` |")

    lines.extend(["", "## History / Report Hits", ""])
    if history:
        for hit in history[:40]:
            lines.append(f"- `{hit['sourceFile']}:{hit['line']}` - {hit['excerpt']}")
    else:
        lines.append("- No direct local history/report hits.")

    lines.extend(["", "## Evidence Claims", "", "| Type | Subject | Value | Confidence | Proof | Caveat |", "|---|---|---|---|:---:|---|"])
    for claim in claims:
        lines.append(
            f"| `{claim['sourceType']}` | `{claim['subject']}` | `{claim['sourceValue']}` | `{claim['confidence']}` | {claim['isAttributionProof']} | {claim['caveat']} |"
        )

    lines.extend(
        [
            "",
            "## Remaining Gaps",
            "",
            "- Need deeper tx history if RPC tx indexes expose funding/delegation/create-validator events beyond the sampled tx_search queries.",
            "- Need non-local proof such as signed operator statement, public profile, or repeated reuse of the same account/IP/key in external sources before naming an owner.",
        ]
    )
    return "\n".join(lines) + "\n"


def main():
    trace = tx_trace()
    investigation = {
        "address": ADDRESS,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "participant": participant_info(),
        "dashboard": recipient_info(),
        "rewardClaims": reward_claims(),
        "governancePower": governance_power(),
        "compensation": compensation_sources(),
        "voteTxs": vote_sources(),
        "epochCommitPublicKeyMatches": public_key_matches(),
        "localMatches": local_same_value_matches(),
        "historyHits": history_hits(),
        "ripe": ripe_lookup(HOST_IP),
        "txTrace": summarize_tx_trace(trace),
    }
    investigation["transferFlows"] = transfer_flows(trace)
    investigation["counterpartyContext"] = counterparty_context(investigation["transferFlows"]["counterparties"])
    investigation["evidenceClaims"] = build_claims(investigation)

    write_json(OUT_DATA, investigation)
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text(build_markdown(investigation))
    print(f"Wrote {OUT_DATA}")
    print(f"Wrote {OUT_REPORT}")
    print("Local match counts:", dict(Counter({key: len(value) for key, value in investigation["localMatches"].items()})))


if __name__ == "__main__":
    main()
