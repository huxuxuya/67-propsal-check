#!/usr/bin/env python3
import csv
import json
import re
from collections import Counter, defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "upstream" / "gonka-kimi-restitution"
DATA = ROOT / "data"
DOCS_DATA = ROOT / "docs" / "data"

N_GONKA = Decimal(1_000_000_000)
VISIBLE_DAMAGE_E265 = Decimal("30592.10")
EXPECTED_TOTAL = Decimal("946509.93")
ROUND_TOLERANCE = Decimal("0.01")
EPOCHS = list(range(265, 277))

OPTION_NAMES = {
    1: "yes",
    2: "abstain",
    3: "no",
    4: "no_with_veto",
}


def load_json(path):
    with path.open() as f:
        return json.load(f)


def as_decimal(value):
    return Decimal(str(value))


def quantize(value, places="0.000001"):
    return value.quantize(Decimal(places), rounding=ROUND_HALF_UP)


def as_float(value):
    return float(quantize(value))


def read_aggregate_compensation():
    rows = []
    with (UPSTREAM / "aggregate_compensation.csv").open(newline="") as f:
        for row in csv.DictReader(f):
            total = as_decimal(row["total_gonka"])
            if total <= 0:
                continue
            per_epoch = {f"e{epoch}": as_decimal(row[f"e{epoch}"]) for epoch in EPOCHS}
            attack = per_epoch["e265"] + per_epoch["e266"]
            cap = sum(per_epoch[f"e{epoch}"] for epoch in range(267, 277))
            rows.append(
                {
                    "address": row["address"],
                    "total": total,
                    "attack": attack,
                    "cap": cap,
                    "per_epoch": per_epoch,
                }
            )
    rows.sort(key=lambda item: (-item["total"], item["address"]))
    return rows


def build_epoch_summary(recipients_raw, total):
    epochs = []
    for epoch in EPOCHS:
        key = f"e{epoch}"
        rows = [
            {"address": row["address"], "amount": row["per_epoch"][key]}
            for row in recipients_raw
            if row["per_epoch"][key] > 0
        ]
        rows.sort(key=lambda row: (-row["amount"], row["address"]))
        epoch_total = sum((row["amount"] for row in rows), Decimal(0))
        component = "attack_e265_e266" if epoch <= 266 else "cap_e267_e276"
        epochs.append(
            {
                "epoch": epoch,
                "key": key,
                "componentSource": component,
                "totalGonka": as_float(epoch_total),
                "recipientsCount": len(rows),
                "shareOfTotal": as_float(epoch_total / total) if total else 0,
                "topRecipient": rows[0]["address"] if rows else "",
                "topRecipientGonka": as_float(rows[0]["amount"]) if rows else 0,
            }
        )
    return epochs


def read_proposal():
    proposal = load_json(DATA / "proposal_67.json")["proposal"]
    outputs = {}
    for output in proposal["messages"][0]["outputs"]:
        amount = as_decimal(output["amount"][0]["amount"]) / N_GONKA
        outputs[output["recipient"]] = amount
    return proposal, outputs


def extract_attr(events, event_type, key):
    for event in events:
        if event.get("type") != event_type:
            continue
        for attr in event.get("attributes", []):
            if attr.get("key") == key:
                return attr.get("value")
    return None


def saved_block_time(height):
    if not height:
        return ""
    for path in [
        DATA / "proposal_67_vote_blocks" / "blocks" / f"block_{height}.json",
        DATA / "voting_end_epochs" / "blocks" / f"block_{height}.json",
    ]:
        if not path.exists():
            continue
        try:
            return load_json(path)["json"]["result"]["block"]["header"]["time"]
        except Exception:
            continue
    return ""


def read_votes():
    raw = load_json(DATA / "proposal_67_tx_search.json")
    all_votes = []
    latest = {}
    for tx in raw["result"]["txs"]:
        voter = extract_attr(tx["tx_result"]["events"], "proposal_vote", "voter")
        option_raw = extract_attr(tx["tx_result"]["events"], "proposal_vote", "option")
        if not voter or not option_raw:
            continue
        options = []
        for item in json.loads(option_raw):
            options.append(
                {
                    "option": OPTION_NAMES[int(item["option"])],
                    "weight": as_float(as_decimal(item["weight"])),
                }
            )
        row = {
            "voter": voter,
            "height": int(tx["height"]),
            "index": int(tx["index"]),
            "txHash": tx["hash"],
            "options": options,
        }
        row["blockTime"] = saved_block_time(row["height"])
        all_votes.append(row)
        if voter not in latest or (row["height"], row["index"]) >= (
            latest[voter]["height"],
            latest[voter]["index"],
        ):
            latest[voter] = row
    return all_votes, sorted(latest.values(), key=lambda row: (row["height"], row["index"], row["voter"]))


def account_from_valoper(operator_address):
    if not operator_address.startswith("gonkavaloper"):
        return ""
    return "gonka" + operator_address[len("gonkavaloper") :]


def read_public_metadata():
    account_labels = {}
    consensus_labels = {}
    consensus_metadata = {}
    evidence = defaultdict(list)
    validators = load_json(DATA / "validators.json").get("validators", [])

    for validator in validators:
        account = account_from_valoper(validator.get("operator_address", ""))
        if not account:
            continue
        desc = validator.get("description", {})
        moniker = (desc.get("moniker") or "").strip()
        website = (desc.get("website") or "").strip()
        identity = (desc.get("identity") or "").strip()
        security_contact = (desc.get("security_contact") or "").strip()
        details = (desc.get("details") or "").strip()
        consensus_key = validator.get("consensus_pubkey", {}).get("key", "")
        label = moniker if moniker and moniker != validator.get("operator_address") else website

        if consensus_key:
            consensus_metadata[consensus_key] = {
                "operatorAddress": validator.get("operator_address", ""),
                "accountAddress": account,
                "moniker": moniker,
                "website": website,
                "identity": identity,
                "securityContact": security_contact,
                "details": details,
                "label": label,
            }

        if moniker and moniker != validator.get("operator_address"):
            account_labels[account] = moniker
            consensus_labels[consensus_key] = moniker
            evidence[account].append(
                {
                    "address": account,
                    "resolvedName": moniker,
                    "sourceType": "validator_moniker",
                    "sourceValue": moniker,
                    "confidence": "high",
                }
            )
        if website:
            evidence[account].append(
                {
                    "address": account,
                    "resolvedName": website,
                    "sourceType": "validator_website",
                    "sourceValue": website,
                    "confidence": "medium",
                }
            )
            if account not in account_labels:
                account_labels[account] = website
                consensus_labels[consensus_key] = website
        if identity:
            evidence[account].append(
                {
                    "address": account,
                    "resolvedName": moniker or website or identity,
                    "sourceType": "validator_identity",
                    "sourceValue": identity,
                    "confidence": "high",
                }
            )
        if security_contact:
            evidence[account].append(
                {
                    "address": account,
                    "resolvedName": moniker or website or security_contact,
                    "sourceType": "validator_security_contact",
                    "sourceValue": security_contact,
                    "confidence": "high",
                }
            )
        if details:
            evidence[account].append(
                {
                    "address": account,
                    "resolvedName": moniker or website or "Validator details",
                    "sourceType": "validator_details",
                    "sourceValue": details,
                    "confidence": "medium",
                }
            )

    participants = load_json(DATA / "participants_by_address.json")
    for address, participant in participants.items():
        if not isinstance(participant, dict) or participant.get("error"):
            continue
        inference_url = (participant.get("inference_url") or "").strip()
        if inference_url:
            evidence[address].append(
                {
                    "address": address,
                    "resolvedName": inference_url,
                    "sourceType": "participant_inference_url",
                    "sourceValue": inference_url,
                    "confidence": "medium",
                }
            )
        validator_key = participant.get("validator_key") or ""
        matched_validator = consensus_metadata.get(validator_key)
        if matched_validator and matched_validator.get("label"):
            evidence[address].append(
                {
                    "address": address,
                    "resolvedName": matched_validator["label"],
                    "sourceType": "validator_key_match",
                    "sourceValue": validator_key,
                    "confidence": "high",
                }
            )
        if matched_validator:
            for source_type, field, confidence in [
                ("matched_validator_moniker", "moniker", "high"),
                ("matched_validator_website", "website", "medium"),
                ("matched_validator_identity", "identity", "high"),
                ("matched_validator_security_contact", "securityContact", "high"),
                ("matched_validator_details", "details", "medium"),
            ]:
                value = matched_validator.get(field)
                if not value:
                    continue
                evidence[address].append(
                    {
                        "address": address,
                        "resolvedName": matched_validator.get("label") or value,
                        "sourceType": source_type,
                        "sourceValue": value,
                        "confidence": confidence,
                    }
                )

    gns_by_address = read_gns_names_by_address()
    for address, names in gns_by_address.items():
        for item in names:
            evidence[address].append(
                {
                    "address": address,
                    "resolvedName": item["fullName"],
                    "sourceType": "gns_name",
                    "sourceValue": f"{item['fullName']} -> {address}",
                    "confidence": "high",
                }
            )

    return participants, account_labels, consensus_labels, consensus_metadata, gns_by_address, evidence


def read_gns_names_by_address():
    path = DATA / "gns_names_by_address.json"
    if not path.exists():
        return {}
    return load_json(path).get("byAddress", {})


def preferred_gns_name(gns_by_address, address):
    names = gns_by_address.get(address) or []
    if not names:
        return ""
    return sorted((item["fullName"] for item in names), key=lambda name: (len(name), name))[0]


def public_label(address, participant, account_labels, consensus_labels, gns_by_address):
    if address in account_labels and not looks_like_generic_node_label(account_labels[address]):
        return account_labels[address]
    if isinstance(participant, dict):
        validator_key = participant.get("validator_key") or ""
        if validator_key in consensus_labels and not looks_like_generic_node_label(consensus_labels[validator_key]):
            return consensus_labels[validator_key]
    gns_name = preferred_gns_name(gns_by_address, address)
    if gns_name:
        return gns_name
    return address


def display_label(address, public_name):
    if not public_name or public_name == address or public_name == "Unknown public owner":
        return address
    return f"{public_name} · {address}"


def short_actor_label(address, display):
    display = display or address
    suffix = f" · {address}"
    if display.endswith(suffix):
        return display[: -len(suffix)]
    return display if display and display != address else address


def canonical_actor_for_address(address, row, claims):
    display = row.get("label") or address
    public_name = row.get("publicLabel") or ""
    operator_signal = row.get("operatorSignalLabel") or ""
    operator_signal_display = row.get("operatorSignalDisplayLabel") or operator_signal
    proof_claims = [claim for claim in claims if claim.get("isAttributionProof")]
    high_claims = [claim for claim in claims if claim.get("confidence") == "high"]
    infrastructure_claims = [
        claim
        for claim in claims
        if claim.get("category") == "infrastructure_signal"
        or claim.get("sourceType") in {"participant_inference_url", "same_inference_host", "same_ip_prefix", "same_asn", "same_tls_cert"}
    ]

    if operator_signal:
        short_label = operator_signal_display
        label_source = row.get("operatorSignal", {}).get("sourceType", "telegram_operator_signal")
    else:
        short_label = short_actor_label(address, display)
        if public_name and public_name != address:
            label_source = row.get("identityType") or "public_metadata"
        else:
            label_source = "address"

    if proof_claims:
        boundary = "public_owner_proof"
    elif infrastructure_claims and not high_claims and not (public_name and public_name != address):
        boundary = "infrastructure_signal"
    elif high_claims or public_name and public_name != address:
        boundary = "public_identity_signal"
    else:
        boundary = "unknown"

    return {
        "address": address,
        "displayLabel": display,
        "shortLabel": short_label,
        "publicName": public_name if public_name != address else "",
        "labelSource": label_source,
        "identityBoundary": boundary,
        "claimCount": len(claims),
        "proofCount": len(proof_claims),
        "highConfidenceClaimCount": len(high_claims),
    }


def apply_canonical_actor_fields(rows, address_key, canonical_by_address):
    for row in rows:
        address = row.get(address_key, "")
        actor = canonical_by_address.get(address)
        if not actor:
            continue
        row["actorDisplayLabel"] = actor["displayLabel"]
        row["actorShortLabel"] = actor["shortLabel"]
        row["publicName"] = actor["publicName"]
        row["labelSource"] = actor["labelSource"]
        row["identityBoundary"] = actor["identityBoundary"]
        row["label"] = actor["displayLabel"]


def primary_identity_type(evidence_rows):
    if not evidence_rows:
        return "unknown"
    source_priority = {
        "validator_key_match": 0,
        "matched_validator_moniker": 1,
        "validator_moniker": 2,
        "gns_name": 3,
        "matched_validator_website": 4,
        "validator_website": 5,
        "participant_inference_url": 6,
    }
    preferred = sorted(
        evidence_rows,
        key=lambda row: (
            {"high": 0, "medium": 1, "low": 2}.get(row["confidence"], 3),
            source_priority.get(row["sourceType"], 20),
        ),
    )[0]
    return preferred["sourceType"]


def public_node_info(participant, consensus_metadata):
    if not isinstance(participant, dict):
        return {}
    validator_key = participant.get("validator_key") or ""
    return {
        "inferenceUrl": participant.get("inference_url", ""),
        "status": participant.get("status", "UNKNOWN"),
        "epochsCompleted": participant.get("epochs_completed"),
        "joinHeight": participant.get("join_height"),
        "lastInferenceTime": participant.get("last_inference_time"),
        "validatorKey": validator_key,
        "workerPublicKey": participant.get("worker_public_key", ""),
        "matchedValidator": consensus_metadata.get(validator_key, {}),
    }


def read_public_identity_signals():
    path = DATA / "public_identity_signals.json"
    if not path.exists():
        return {}
    return load_json(path)


def load_optional_json(path, default):
    if not path.exists():
        return default
    return load_json(path)


def read_onchain_graph_snapshot():
    return load_optional_json(DATA / "onchain_graph" / "proposal_67_local_graph.json", {})


def read_public_osint_sources():
    return load_optional_json(DATA / "osint" / "public_osint_sources.json", {})


def read_telegram_evidence():
    return load_optional_json(DATA / "telegram_evidence.json", {"messages": [], "summary": {}})


def read_voting_end_epochs():
    return load_optional_json(DATA / "voting_end_epochs" / "manifest.json", {"epochs": [], "blocks": []})


def read_governance_power_evidence():
    return load_optional_json(DATA / "governance_power_67" / "governance_power_67.json", {"summary": {}, "archiveGovVotes": [], "perVoterPower": []})


def build_voting_power_window(votes, governance_power_evidence):
    by_voter = {row["voter"]: row for row in governance_power_evidence.get("windowVoterPower", [])}
    summary = governance_power_evidence.get("summary", {})
    rows = []
    for vote in votes:
        window = by_voter.get(vote["voter"], {})
        start_power = window.get("startVotingPower")
        end_power = window.get("endVotingPower")
        if start_power is None:
            start_power = vote.get("votingPower") if vote.get("votingPower") is not None else 0
        if end_power is None:
            end_power = vote.get("votingPower") if vote.get("votingPower") is not None else 0
        rows.append(
            {
                "voter": vote["voter"],
                "address": vote["voter"],
                "label": vote["label"],
                "publicLabel": vote.get("publicLabel", ""),
                "operatorSignalLabel": vote.get("operatorSignalLabel", ""),
                "operatorSignalDisplayLabel": vote.get("operatorSignalDisplayLabel", ""),
                "primaryOption": vote["primaryOption"],
                "height": vote["height"],
                "txHash": vote["txHash"],
                "isRecipient": vote["isRecipient"],
                "startVotingPower": round(start_power or 0, 6),
                "endVotingPower": round(end_power or 0, 6),
                "startVotingPowerSource": window.get("startVotingPowerSource", "unknown"),
                "endVotingPowerSource": window.get("endVotingPowerSource", vote.get("votingPowerSource", "unknown")),
                "windowPowerStatus": window.get("windowPowerStatus", "not_in_window_snapshot" if not window else "unchanged"),
                "startDelegationCount": len(window.get("startDelegations") or []),
                "endDelegationCount": len(window.get("endDelegations") or []),
            }
        )
    rows.sort(key=lambda row: (row["windowPowerStatus"] == "unchanged", -abs(row["endVotingPower"] - row["startVotingPower"]), -row["endVotingPower"], row["label"]))
    return {
        "summary": {
            "votingStartTime": summary.get("votingStartTime", ""),
            "votingEndTime": summary.get("votingEndTime", ""),
            "lastBlockBeforeVotingStart": summary.get("lastBlockBeforeVotingStart", {}),
            "firstBlockAfterVotingStart": summary.get("firstBlockAfterVotingStart", {}),
            "lastBlockBeforeVotingEnd": summary.get("lastBlockBeforeVotingEnd", {}),
            "firstBlockAfterVotingEnd": summary.get("firstBlockAfterVotingEnd", {}),
            "decodedGovVotesBeforeStartCount": summary.get("decodedGovVotesBeforeStartCount", 0),
            "decodedGovVotesAfterStartCount": summary.get("decodedGovVotesAfterStartCount", 0),
            "decodedGovVotesBeforeEndCount": summary.get("decodedGovVotesBeforeEndCount", 0),
            "votersWithStartVotingPowerCount": summary.get("votersWithStartVotingPowerCount", 0),
            "votersWithEndVotingPowerCount": summary.get("votersWithEndVotingPowerCount", 0),
            "votersZeroAtStartAndEndCount": summary.get("votersZeroAtStartAndEndCount", 0),
            "votersPowerAtStartOnlyCount": summary.get("votersPowerAtStartOnlyCount", 0),
            "votersPowerAtEndOnlyCount": summary.get("votersPowerAtEndOnlyCount", 0),
            "startChainLikeTallyTruncatedForFinalVoters": summary.get("startChainLikeTallyTruncatedForFinalVoters", {}),
            "chainLikeTallyTruncated": summary.get("chainLikeTallyTruncated", {}),
            "chainLikeTallyMatchesFinalTally": summary.get("chainLikeTallyMatchesFinalTally", False),
        },
        "rows": rows,
    }


def source_url_for_file(source_file):
    if source_file.startswith("http"):
        return source_file
    if source_file.startswith("upstream/gonka-kimi-restitution/"):
        rel = source_file.removeprefix("upstream/gonka-kimi-restitution/")
        return f"https://github.com/votkon/gonka-kimi-restitution/blob/main/{rel}"
    if source_file.startswith("data/osint/"):
        return source_file
    if source_file.startswith("data/") or source_file.startswith("docs/") or source_file.startswith("reports/"):
        return source_file
    return source_file


def normalize_claim_value(value):
    if value is None:
        return ""
    return str(value).strip()


def evidence_category(source_type):
    if source_type in {"proposal_proposer", "proposal_message_sender", "proposal_vote", "proposal_output"}:
        return "governance"
    if source_type in {"compensation_output", "upstream_delegation", "epoch_commit_participant"}:
        return "financial_or_epoch_activity"
    if "github" in source_type or "social" in source_type or source_type.startswith("gonka_names"):
        return "public_social"
    if source_type in {"same_ip_prefix", "same_asn", "same_tls_cert", "dns_resolves_to"}:
        return "infrastructure_signal"
    if "host" in source_type or "url" in source_type or "website" in source_type:
        return "public_infrastructure"
    return "public_identity"


def make_claim(address, subject, source_type, source_value, source_file, confidence="medium", proof=False, caveat=""):
    return {
        "address": address,
        "subject": subject or address,
        "category": evidence_category(source_type),
        "sourceType": source_type,
        "sourceValue": normalize_claim_value(source_value),
        "sourceFile": source_file,
        "sourceUrl": source_url_for_file(source_file),
        "confidence": confidence,
        "isAttributionProof": bool(proof),
        "caveat": caveat,
    }


def edge_policy(source_type):
    strict = {
        "validator_key_match",
        "matched_validator_moniker",
        "matched_validator_identity",
        "matched_validator_security_contact",
        "validator_moniker",
        "validator_identity",
        "validator_security_contact",
        "gns_name",
        "gns_reverse",
    }
    medium = {
        "participant_inference_url",
        "matched_validator_website",
        "validator_website",
        "matched_validator_details",
        "validator_details",
        "gns_record_website",
        "gns_record_telegram",
        "gns_record_twitter",
        "gns_record_email",
        "gns_record_description",
        "same_validator_website",
        "same_security_contact",
        "same_validator_identity",
        "same_inference_host",
        "same_gns_contact",
    }
    if source_type in strict:
        return "high", True
    if source_type in medium:
        return "medium", False
    return "low", False


def entity_id(entity_type, value):
    return f"{entity_type}:{value}"


def looks_like_generic_node_label(value):
    value = (value or "").strip().lower()
    if not value:
        return True
    if value.startswith(("http://", "https://", "http:/", "https:/", "gonkavaloper", "gonka1")):
        return True
    if re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}(:\d+)?/?", value):
        return True
    return False


def public_owner_proof(source_type, source_value, resolved_name=""):
    value = resolved_name or source_value
    if source_type in {"matched_validator_identity", "validator_identity", "matched_validator_security_contact", "validator_security_contact", "gns_name", "gns_reverse"}:
        return True
    if source_type in {"matched_validator_moniker", "validator_moniker"}:
        return not looks_like_generic_node_label(value)
    if source_type == "validator_key_match":
        return not looks_like_generic_node_label(resolved_name)
    return False


def add_entity(entities, entity_type, value, label=None, metadata=None):
    if not value:
        return ""
    eid = entity_id(entity_type, value)
    entities[eid] = {
        "id": eid,
        "type": entity_type,
        "value": value,
        "label": label or value,
        "metadata": metadata or {},
    }
    return eid


def add_edge(edges, source, target, source_type, source_value, source_file, confidence=None, proof=None):
    if not source or not target or source == target:
        return
    default_confidence, default_proof = edge_policy(source_type)
    default_proof = default_proof and public_owner_proof(source_type, source_value)
    edges.append(
        {
            "source": source,
            "target": target,
            "sourceType": source_type,
            "sourceValue": source_value,
            "sourceFile": source_file,
            "confidence": confidence or default_confidence,
            "isAttributionProof": default_proof if proof is None else proof,
        }
    )


def host_from_url(url):
    try:
        from urllib.parse import urlparse

        return urlparse(url).hostname or ""
    except Exception:
        return ""


def ip_prefix(ip):
    parts = ip.split(".")
    if len(parts) == 4:
        return ".".join(parts[:3]) + ".0/24"
    return ""


def rdap_org(rdap):
    data = (rdap or {}).get("json") or {}
    for key in ["name", "handle"]:
        if data.get(key):
            return str(data[key])
    return ""


def component(addresses, adjacency):
    seen = set()
    components = []
    for address in sorted(addresses):
        if address in seen:
            continue
        stack = [address]
        seen.add(address)
        group = []
        while stack:
            current = stack.pop()
            group.append(current)
            for nxt in sorted(adjacency.get(current, set())):
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        if len(group) > 1:
            components.append(sorted(group))
    return components


def graph_address_components(addresses, edges, edge_filter):
    address_nodes = {entity_id("address", address) for address in addresses}
    adjacency = defaultdict(set)
    nodes = set(address_nodes)
    for edge in edges:
        if not edge_filter(edge):
            continue
        source = edge["source"]
        target = edge["target"]
        nodes.add(source)
        nodes.add(target)
        adjacency[source].add(target)
        adjacency[target].add(source)

    seen = set()
    groups = []
    for node in sorted(nodes):
        if node in seen:
            continue
        stack = [node]
        seen.add(node)
        group_nodes = []
        while stack:
            current = stack.pop()
            group_nodes.append(current)
            for nxt in sorted(adjacency.get(current, set())):
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        group_addresses = sorted(item.replace("address:", "") for item in group_nodes if item in address_nodes)
        if len(group_addresses) > 1:
            groups.append(group_addresses)
    return groups


def cluster_label(rows, graph_edges, addresses, cluster_kind):
    address_set = set(addresses)
    if cluster_kind == "strict":
        strict_edges = [
            edge for edge in graph_edges
            if edge["confidence"] == "high"
            and edge["isAttributionProof"]
            and (edge["source"].replace("address:", "") in address_set or edge["target"].replace("address:", "") in address_set)
        ]
        if strict_edges:
            return strict_edges[0]["sourceValue"]
    signal_edges = [
        edge for edge in graph_edges
        if edge["confidence"] in {"medium", "low"}
        and (edge["source"].replace("address:", "") in address_set or edge["target"].replace("address:", "") in address_set)
    ]
    if signal_edges:
        return f"Shared signal: {signal_edges[0]['sourceValue']}"
    for row in rows:
        info = row.get("publicNodeInfo", {})
        host = host_from_url(info.get("inferenceUrl", ""))
        if host:
            return f"Shared signal: {host}"
    return "Possible infrastructure group"


def summarize_clusters(groups, rows_by_address, graph_edges, cluster_kind):
    clusters = []
    for index, addresses in enumerate(groups, start=1):
        rows = [rows_by_address[address] for address in addresses if address in rows_by_address]
        recipient_count = sum(1 for row in rows if row.get("kind") == "recipient")
        voter_count = sum(1 for row in rows if row.get("hasVote"))
        total = sum(row.get("totalGonka", 0) for row in rows)
        vote_counts = Counter(row.get("voteOption") or row.get("primaryOption") or "did_not_vote" for row in rows)
        relevant_edges = [
            edge for edge in graph_edges
            if edge["source"].replace("address:", "") in addresses or edge["target"].replace("address:", "") in addresses
        ]
        if cluster_kind == "strict":
            relevant_edges = [
                edge for edge in relevant_edges
                if edge["confidence"] == "high" and edge["isAttributionProof"]
            ]
        weakest = "high"
        if any(edge["confidence"] == "low" for edge in relevant_edges):
            weakest = "low"
        elif any(edge["confidence"] == "medium" for edge in relevant_edges):
            weakest = "medium"
        clusters.append(
            {
                "id": f"{cluster_kind}-{index}",
                "kind": cluster_kind,
                "label": cluster_label(rows, relevant_edges, addresses, cluster_kind),
                "addresses": addresses,
                "recipientCount": recipient_count,
                "voterCount": voter_count,
                "totalCompensationGonka": round(total, 6),
                "voteCounts": dict(vote_counts),
                "weakestEvidence": weakest,
                "evidenceCount": len(relevant_edges),
            }
        )
    clusters.sort(key=lambda row: (-row["totalCompensationGonka"], -len(row["addresses"]), row["id"]))
    return clusters


def build_identity_graph(recipients, votes, identity_evidence, gns_by_address):
    signals = read_public_identity_signals()
    entities = {}
    edges = []
    rows_by_address = {}

    for row in recipients:
        rows_by_address[row["address"]] = {**row, "kind": "recipient", "hasVote": row.get("voteOption") != "did_not_vote"}
    for vote in votes:
        rows_by_address.setdefault(vote["voter"], {**vote, "kind": "voter", "hasVote": True})
        rows_by_address[vote["voter"]]["hasVote"] = True
        rows_by_address[vote["voter"]]["primaryOption"] = vote["primaryOption"]

    relevant_addresses = set(rows_by_address)
    for address in relevant_addresses:
        add_entity(entities, "address", address)

    for item in identity_evidence:
        address = item["address"]
        if address not in relevant_addresses:
            continue
        source_type = item["sourceType"]
        value = item["sourceValue"]
        if source_type.startswith("gns_record_"):
            entity_type = "contact"
        elif "website" in source_type:
            entity_type = "website"
        elif "identity" in source_type:
            entity_type = "validator_identity"
        elif "security_contact" in source_type:
            entity_type = "contact"
        elif source_type == "gns_name":
            entity_type = "gns_name"
        elif "inference_url" in source_type:
            entity_type = "inference_endpoint"
        else:
            entity_type = "public_label"
        target = add_entity(entities, entity_type, value)
        add_edge(edges, entity_id("address", address), target, source_type, value, "docs/data/dashboard.json", item.get("confidence"))

    for address, names in gns_by_address.items():
        if address not in relevant_addresses:
            continue
        for name in names:
            if name.get("reverse"):
                target = add_entity(entities, "gns_name", name["fullName"])
                add_edge(edges, entity_id("address", address), target, "gns_reverse", name["fullName"], "data/gns_names_by_address.json", "high", True)
            for record_key, record in (name.get("records") or {}).items():
                source_type = f"gns_record_{record_key}"
                target = add_entity(entities, "contact" if record_key != "website" else "website", str(record.get("value", "")))
                add_edge(edges, entity_id("address", address), target, source_type, f"{name['fullName']}:{record_key}={record.get('value', '')}", "data/gns_names_by_address.json")

    for url, target in (signals.get("targets", {}).get("urls", {}) or {}).items():
        host = target.get("host", "")
        for source in target.get("sources", []):
            address = source.get("address")
            if address not in relevant_addresses:
                continue
            url_entity = add_entity(entities, "url", url)
            host_entity = add_entity(entities, "host", host)
            source_type = source.get("sourceType", "public_url")
            add_edge(edges, entity_id("address", address), url_entity, source_type, source.get("sourceValue", url), "data/public_identity_signals.json")
            add_edge(edges, entity_id("address", address), host_entity, "same_inference_host" if source_type == "participant_inference_url" else "same_website", host, "data/public_identity_signals.json", "medium", False)

    for domain, dns in (signals.get("dns") or {}).items():
        domain_entity = add_entity(entities, "domain", domain)
        for ip in dns.get("addresses", []):
            ip_entity = add_entity(entities, "ip", ip)
            add_edge(edges, domain_entity, ip_entity, "dns_resolves_to", f"{domain}->{ip}", "data/public_identity_signals.json", "low", False)
            prefix = ip_prefix(ip)
            if prefix:
                prefix_entity = add_entity(entities, "ip_prefix", prefix)
                add_edge(edges, ip_entity, prefix_entity, "same_ip_prefix", prefix, "data/public_identity_signals.json", "low", False)

    for ip, rdap in (signals.get("rdapIps") or {}).items():
        org = rdap_org(rdap)
        if org:
            add_edge(edges, add_entity(entities, "ip", ip), add_entity(entities, "asn_or_rdap_org", org), "same_asn", org, "data/public_identity_signals.json", "low", False)

    for domain, tls in (signals.get("tls") or {}).items():
        serial = tls.get("serialNumber")
        if serial:
            add_edge(edges, add_entity(entities, "domain", domain), add_entity(entities, "tls_cert", serial), "same_tls_cert", serial, "data/public_identity_signals.json", "low", False)

    strict_groups = graph_address_components(
        relevant_addresses,
        edges,
        lambda edge: edge.get("confidence") == "high" and edge.get("isAttributionProof"),
    )
    signal_groups = graph_address_components(
        relevant_addresses,
        edges,
        lambda edge: edge.get("confidence") in {"high", "medium", "low"},
    )

    return {
        "entities": sorted(entities.values(), key=lambda row: row["id"]),
        "edges": sorted(edges, key=lambda row: (row["source"], row["target"], row["sourceType"], row["sourceValue"])),
        "strictClusters": summarize_clusters(strict_groups, rows_by_address, edges, "strict"),
        "signalClusters": summarize_clusters(signal_groups, rows_by_address, edges, "signal"),
    }


def address_from_edge_node(value):
    return value.replace("address:", "") if value.startswith("address:") else ""


def collect_address_labels(recipients, votes, participants, account_labels, consensus_labels, gns_by_address):
    labels = {}
    identity_types = {}
    for row in recipients:
        labels[row["address"]] = row["label"]
        identity_types[row["address"]] = row["identityType"]
    for row in votes:
        labels[row["voter"]] = row["label"]
        identity_types[row["voter"]] = row["identityType"]
    for address, participant in participants.items():
        public_name = public_label(address, participant, account_labels, consensus_labels, gns_by_address)
        labels.setdefault(address, display_label(address, public_name))
    return labels, identity_types


def build_evidence_claims(proposal, recipients, votes, identity_evidence, identity_graph, onchain_graph, osint_sources, telegram_evidence=None, epoch_anomalies=None):
    claims = []
    recipient_by_address = {row["address"]: row for row in recipients}
    vote_by_address = {row["voter"]: row for row in votes}

    for row in recipients:
        claims.append(
            make_claim(
                row["address"],
                row["label"],
                "compensation_output",
                f"{row['totalGonka']} GONKA",
                "data/proposal_67.json",
                "high",
                False,
                "On-chain proposal output proves beneficiary address and amount, not human owner.",
            )
        )
    for row in votes:
        claims.append(
            make_claim(
                row["voter"],
                row["label"],
                "proposal_vote",
                row["primaryOption"],
                "data/proposal_67_tx_search.json",
                "high",
                False,
                "Vote proves governance action by address, not human owner.",
            )
        )

    proposer = proposal.get("proposer", "")
    message_sender = proposal.get("messages", [{}])[0].get("sender", "")
    if proposer:
        claims.append(
            make_claim(
                proposer,
                proposer,
                "proposal_proposer",
                proposal.get("id", "67"),
                "data/proposal_67.json",
                "high",
                False,
                "Proposal proposer is a governance actor and should be reviewed as an interested party.",
            )
        )
    if message_sender:
        claims.append(
            make_claim(
                message_sender,
                message_sender,
                "proposal_message_sender",
                proposal.get("messages", [{}])[0].get("@type", ""),
                "data/proposal_67.json",
                "high",
                False,
                "Message sender is the address authorizing the proposal message, not necessarily the final human owner.",
            )
        )

    for item in identity_evidence:
        claims.append(
            make_claim(
                item["address"],
                item.get("resolvedName") or item["address"],
                item["sourceType"],
                item["sourceValue"],
                "docs/data/dashboard.json",
                item.get("confidence", "medium"),
                public_owner_proof(item["sourceType"], item["sourceValue"], item.get("resolvedName", "")),
                "Public self-declared metadata when proof=true; otherwise a public label/signal.",
            )
        )

    relevant_addresses = {row["address"] for row in recipients} | {row["voter"] for row in votes}
    relevant_addresses |= {proposer, message_sender} - {""}
    for edge in identity_graph.get("edges", []):
        address = address_from_edge_node(edge["source"]) or address_from_edge_node(edge["target"])
        if not address or address not in relevant_addresses:
            continue
        claims.append(
            make_claim(
                address,
                edge["target"] if edge["source"].startswith("address:") else edge["source"],
                edge["sourceType"],
                edge["sourceValue"],
                edge["sourceFile"],
                edge.get("confidence", "medium"),
                edge.get("isAttributionProof", False) and public_owner_proof(edge["sourceType"], edge["sourceValue"]),
                "Graph edge; infrastructure/provider edges are signals only.",
            )
        )

    for row in (onchain_graph.get("delegations") or []):
        if row["delegator"] in relevant_addresses or row["operator"] in relevant_addresses:
            claims.append(
                make_claim(
                    row["delegator"],
                    row["operator"],
                    "upstream_delegation",
                    f"{row['delegator']} -> {row['operator']}",
                    row.get("sourceFile", "upstream/gonka-kimi-restitution/e266/epoch266_kimi_delegators.json"),
                    "medium",
                    False,
                    "Delegation links economic/operational relationship, not common ownership.",
                )
            )
    for row in (onchain_graph.get("epochCommits") or []):
        participant = row.get("participant", "")
        if participant not in relevant_addresses:
            continue
        claims.append(
            make_claim(
                participant,
                row.get("hexPubKey") or participant,
                "epoch_commit_participant",
                f"e{row.get('epoch')} {row.get('modelId')} count={row.get('count')}",
                row.get("sourceFile", "upstream/gonka-kimi-restitution"),
                "medium",
                False,
                "Epoch commit activity links an address to model participation and public key usage.",
            )
        )

    github = (osint_sources.get("github") or {})
    for source_name, response in github.items():
        payload = response.get("json")
        if not payload:
            continue
        rows = payload if isinstance(payload, list) else [payload]
        for item in rows:
            if not isinstance(item, dict):
                continue
            login = (item.get("author") or {}).get("login") or item.get("login") or (item.get("owner") or {}).get("login")
            html_url = (item.get("author") or {}).get("html_url") or item.get("html_url") or ""
            if not login and not html_url:
                continue
            claims.append(
                make_claim(
                    "",
                    login or html_url,
                    f"github_{source_name}",
                    html_url or login,
                    response.get("url", "https://github.com/votkon/gonka-kimi-restitution"),
                    "medium",
                    False,
                    "GitHub actor is connected to the public restitution repository, not directly to an on-chain address unless another edge links them.",
                )
            )

    for link in osint_sources.get("publicSocialCandidates") or []:
        claims.append(
            make_claim(
                "",
                link,
                "public_social_candidate",
                link,
                "data/osint/public_osint_sources.json",
                "low",
                False,
                "Public social/profile URL candidate requires manual review or a stronger linking edge.",
            )
        )

    for message in (telegram_evidence or {}).get("messages") or []:
        for address in message.get("addresses") or [""]:
            excerpt_value = message.get("excerpt", "")
            author_value = message.get("author") or message.get("chat", "")
            claims.append(
                make_claim(
                    address,
                    author_value,
                    message.get("sourceType", "telegram_export_excerpt"),
                    excerpt_value,
                    message.get("sourceFile", "history"),
                    message.get("confidence", "medium"),
                    False,
                    message.get("caveat", "Telegram excerpt requires corroboration."),
                )
            )

    for row in epoch_anomalies or []:
        claims.append(
            make_claim(
                row["address"],
                row["label"],
                "voting_end_epoch_anomaly",
                f"e287={row['e287Weight']} prev={row['prevMaxWeight']} next={row['nextMaxWeight']} vote={row['voteOption']}@{row['voteHeight']}",
                "data/voting_end_epochs/manifest.json",
                "medium",
                False,
                row["caveat"],
            )
        )

    deduped = {}
    for claim in claims:
        key = (
            claim["address"],
            claim["subject"],
            claim["sourceType"],
            claim["sourceValue"],
            claim["sourceFile"],
        )
        deduped[key] = claim
    return sorted(deduped.values(), key=lambda row: (row["address"], row["category"], row["sourceType"], row["sourceValue"]))


def apply_investigation_labels(recipients, votes, evidence_claims):
    label_source_types = {"telegram_operator_statement", "telegram_self_or_team_claim"}
    operator_labels = {}
    priority = {"high": 0, "medium": 1}
    for claim in evidence_claims:
        if claim.get("sourceType") not in label_source_types:
            continue
        confidence = claim.get("confidence", "")
        if confidence not in priority:
            continue
        address = claim.get("address") or ""
        subject = claim.get("subject") or ""
        if not address or not subject:
            continue
        label = {
            "label": subject,
            "sourceType": claim.get("sourceType", ""),
            "confidence": confidence,
            "sourceUrl": claim.get("sourceUrl", ""),
            "caveat": claim.get("caveat", ""),
        }
        current = operator_labels.get(address)
        if not current or priority[confidence] < priority.get(current.get("confidence", ""), 9):
            operator_labels[address] = label

    def apply(row, address_key):
        address = row.get(address_key, "")
        signal = operator_labels.get(address)
        if not signal:
            return
        public_label_value = row.get("publicLabel") or address
        signal_label = signal["label"] if signal["confidence"] == "high" else f"{signal['label']}?"
        row["publicLabel"] = public_label_value
        row["operatorSignalLabel"] = signal["label"]
        row["operatorSignalDisplayLabel"] = signal_label
        row["operatorSignal"] = signal
        label_parts = [signal_label]
        if public_label_value and public_label_value not in {address, signal["label"]}:
            label_parts.append(public_label_value)
        label_parts.append(address)
        row["label"] = " · ".join(label_parts)

    for row in recipients:
        apply(row, "address")
    for row in votes:
        apply(row, "voter")


def build_actors(proposal, recipients, votes, identity_graph, onchain_graph, labels, identity_types):
    actors = {}

    def ensure(address, label=None):
        if address not in actors:
            actors[address] = {
                "id": f"address:{address}" if address else "",
                "address": address,
                "label": label or labels.get(address) or address or "Unknown public owner",
                "roles": set(),
                "totalCompensationGonka": 0,
                "votingPower": 0,
                "voteOption": "did_not_vote",
                "identityType": identity_types.get(address, "unknown"),
                "actorDisplayLabel": label or labels.get(address) or address or "Unknown public owner",
                "actorShortLabel": short_actor_label(address, label or labels.get(address) or address or "Unknown public owner"),
                "publicName": "",
                "labelSource": "address",
                "identityBoundary": "unknown",
                "strictClusterId": "",
                "signalClusterId": "",
            }
        return actors[address]

    for row in recipients:
        actor = ensure(row["address"], row["label"])
        actor["roles"].add("recipient")
        actor["totalCompensationGonka"] += row["totalGonka"]
        actor["voteOption"] = row["voteOption"]
        actor["identityType"] = row["identityType"]
        actor["actorDisplayLabel"] = row.get("actorDisplayLabel", actor["label"])
        actor["actorShortLabel"] = row.get("actorShortLabel", short_actor_label(row["address"], actor["actorDisplayLabel"]))
        actor["publicName"] = row.get("publicName", "")
        actor["labelSource"] = row.get("labelSource", "")
        actor["identityBoundary"] = row.get("identityBoundary", "")
        actor["strictClusterId"] = row.get("strictClusterId", "")
        actor["signalClusterId"] = row.get("signalClusterId", "")

    for row in votes:
        actor = ensure(row["voter"], row["label"])
        actor["roles"].add("voter")
        actor["voteOption"] = row["primaryOption"]
        actor["votingPower"] = row.get("votingPower") or 0
        actor["identityType"] = row["identityType"]
        actor["actorDisplayLabel"] = row.get("actorDisplayLabel", actor["label"])
        actor["actorShortLabel"] = row.get("actorShortLabel", short_actor_label(row["voter"], actor["actorDisplayLabel"]))
        actor["publicName"] = row.get("publicName", "")
        actor["labelSource"] = row.get("labelSource", "")
        actor["identityBoundary"] = row.get("identityBoundary", "")
        actor["strictClusterId"] = row.get("strictClusterId", "")
        actor["signalClusterId"] = row.get("signalClusterId", "")

    proposer = proposal.get("proposer", "")
    sender = proposal.get("messages", [{}])[0].get("sender", "")
    if proposer:
        ensure(proposer).get("roles").add("proposer")
    if sender:
        ensure(sender).get("roles").add("message_sender")

    for row in (onchain_graph.get("delegations") or []):
        if row.get("delegator"):
            ensure(row["delegator"]).get("roles").add("delegator")
        if row.get("operator"):
            ensure(row["operator"]).get("roles").add("operator")
    for row in (onchain_graph.get("epochCommits") or []):
        if row.get("participant"):
            ensure(row["participant"]).get("roles").add("epoch_commit_participant")

    for cluster in identity_graph.get("strictClusters", []):
        for address in cluster.get("addresses", []):
            if address in actors:
                actors[address]["strictClusterId"] = cluster["id"]
    for cluster in identity_graph.get("signalClusters", []):
        for address in cluster.get("addresses", []):
            if address in actors:
                actors[address]["signalClusterId"] = cluster["id"]

    return sorted(
        [
            {
                **actor,
                "roles": sorted(actor["roles"]),
                "totalCompensationGonka": round(actor["totalCompensationGonka"], 6),
                "votingPower": round(actor["votingPower"], 6),
            }
            for actor in actors.values()
            if actor["address"]
        ],
        key=lambda row: (-row["totalCompensationGonka"], row["address"]),
    )


def build_ranked_parties(actors, claims, identity_graph):
    claims_by_address = defaultdict(list)
    for claim in claims:
        if claim["address"]:
            claims_by_address[claim["address"]].append(claim)

    grouped = {}
    for actor in actors:
        cluster = actor.get("strictClusterId") or actor.get("signalClusterId") or actor["address"]
        grouped.setdefault(
            cluster,
            {
                "id": cluster,
                "label": actor["label"],
                "actorDisplayLabel": actor.get("actorDisplayLabel", actor["label"]),
                "actorShortLabel": actor.get("actorShortLabel", actor["label"]),
                "identityBoundary": actor.get("identityBoundary", ""),
                "labelSource": actor.get("labelSource", ""),
                "addresses": [],
                "roles": set(),
                "totalCompensationGonka": 0,
                "voteCounts": Counter(),
                "identityTypes": set(),
                "claims": [],
            },
        )
        row = grouped[cluster]
        row["addresses"].append(actor["address"])
        row["roles"].update(actor["roles"])
        row["totalCompensationGonka"] += actor["totalCompensationGonka"]
        row["voteCounts"][actor.get("voteOption", "did_not_vote")] += 1
        row["identityTypes"].add(actor.get("identityType", "unknown"))
        row["claims"].extend(claims_by_address.get(actor["address"], []))

    ranked = []
    for row in grouped.values():
        proof_claims = [claim for claim in row["claims"] if claim["isAttributionProof"]]
        high_claims = [claim for claim in row["claims"] if claim["confidence"] == "high"]
        medium_claims = [claim for claim in row["claims"] if claim["confidence"] == "medium"]
        signal_claims = [claim for claim in row["claims"] if not claim["isAttributionProof"]]
        identity_score = 25 if proof_claims else (14 if high_claims else (7 if medium_claims else 0))
        benefit_score = min(35, row["totalCompensationGonka"] / 5000)
        governance_score = 0
        if "proposer" in row["roles"]:
            governance_score += 18
        if "message_sender" in row["roles"]:
            governance_score += 18
        if "voter" in row["roles"]:
            governance_score += 8
        if "recipient" in row["roles"] and "voter" in row["roles"]:
            governance_score += 8
        governance_score = min(25, governance_score)
        telegram_claims = [claim for claim in row["claims"] if claim["sourceType"].startswith("telegram_")]
        telegram_score = min(
            12,
            sum(
                4 if claim["sourceType"] in {"telegram_operator_statement", "telegram_self_or_team_claim"} else 2
                for claim in telegram_claims
            ),
        )
        operational_timing_score = min(18, sum(1 for claim in row["claims"] if claim["sourceType"] == "voting_end_epoch_anomaly") * 8)
        inference_vote_overlap_score = 6 if any("vote=" in claim["sourceValue"] and "@None" not in claim["sourceValue"] for claim in row["claims"] if claim["sourceType"] == "voting_end_epoch_anomaly") else 0
        proposal_role_score = 10 if {"proposer", "message_sender"} & row["roles"] else 0
        coordination_score = min(15, max(0, len(row["addresses"]) - 1) * 5 + len(signal_claims) * 0.15)
        overall = round(identity_score + benefit_score + governance_score + coordination_score + telegram_score + proposal_role_score, 3)
        top_claims = sorted(
            row["claims"],
            key=lambda claim: (
                {"high": 0, "medium": 1, "low": 2}.get(claim["confidence"], 3),
                not claim["isAttributionProof"],
                claim["sourceType"],
            ),
        )[:5]
        caveats = []
        if not proof_claims:
            caveats.append("No strict public owner proof.")
        if any(claim["category"] == "infrastructure_signal" for claim in row["claims"]):
            caveats.append("Contains infrastructure/provider signals; do not treat as ownership proof.")
        if "recipient" in row["roles"] and "voter" in row["roles"]:
            caveats.append("Address both received compensation and voted.")
        if operational_timing_score or inference_vote_overlap_score:
            caveats.append("e287 inference timing is an operational signal, not governance voting power.")
        ranked.append(
            {
                "id": row["id"],
                "label": row["label"],
                "actorDisplayLabel": row.get("actorDisplayLabel", row["label"]),
                "actorShortLabel": row.get("actorShortLabel", row["label"]),
                "identityBoundary": row.get("identityBoundary", ""),
                "labelSource": row.get("labelSource", ""),
                "addresses": sorted(row["addresses"]),
                "roles": sorted(row["roles"]),
                "identityTypes": sorted(row["identityTypes"]),
                "totalCompensationGonka": round(row["totalCompensationGonka"], 6),
                "voteCounts": dict(row["voteCounts"]),
                "scoreComponents": {
                    "identityConfidence": round(identity_score, 3),
                    "benefit": round(benefit_score, 3),
                    "governance": round(governance_score, 3),
                    "coordination": round(coordination_score, 3),
                    "telegramAttribution": round(telegram_score, 3),
                    "epochAnomaly": round(operational_timing_score, 3),
                    "operationalTiming": round(operational_timing_score, 3),
                    "voteTiming": round(inference_vote_overlap_score, 3),
                    "inferenceVoteOverlap": round(inference_vote_overlap_score, 3),
                    "proposalRole": round(proposal_role_score, 3),
                },
                "overallPriority": overall,
                "operationalPriority": round(overall + operational_timing_score + inference_vote_overlap_score, 3),
                "confidence": "high" if proof_claims else ("medium" if high_claims or medium_claims else "low"),
                "topEvidence": top_claims,
                "caveats": caveats,
            }
        )

    ranked.sort(key=lambda row: (-row["overallPriority"], -row["totalCompensationGonka"], row["label"]))
    for index, row in enumerate(ranked, start=1):
        row["rank"] = index
    return ranked


def build_interest_clusters(actors, evidence_claims, identity_graph):
    claims_by_address = defaultdict(list)
    for claim in evidence_claims:
        if claim.get("address"):
            claims_by_address[claim["address"]].append(claim)

    strict_ids = {cluster["id"] for cluster in identity_graph.get("strictClusters", [])}
    signal_ids = {cluster["id"] for cluster in identity_graph.get("signalClusters", [])}
    grouped = {}
    for actor in actors:
        if actor.get("strictClusterId"):
            group_id = actor["strictClusterId"]
            kind = "strict_identity"
        elif actor.get("signalClusterId"):
            group_id = actor["signalClusterId"]
            kind = "signal_cluster"
        else:
            continue

        grouped.setdefault(
            group_id,
            {
                "id": group_id,
                "kind": kind,
                "label": actor["label"],
                "actorDisplayLabel": actor.get("actorDisplayLabel", actor["label"]),
                "actorShortLabel": actor.get("actorShortLabel", actor["label"]),
                "identityBoundary": actor.get("identityBoundary", ""),
                "labelSource": actor.get("labelSource", ""),
                "addresses": [],
                "roles": set(),
                "identityTypes": set(),
                "voteAddressCounts": Counter(),
                "votePowerByOption": defaultdict(float),
                "totalCompensationGonka": 0,
                "totalVotingPower": 0,
                "recipientCount": 0,
                "voterCount": 0,
                "recipientVoterCount": 0,
                "claims": [],
            },
        )
        row = grouped[group_id]
        row["addresses"].append(actor["address"])
        row["roles"].update(actor.get("roles", []))
        row["identityTypes"].add(actor.get("identityType", "unknown"))
        row["totalCompensationGonka"] += actor.get("totalCompensationGonka") or 0
        row["totalVotingPower"] += actor.get("votingPower") or 0
        if "recipient" in actor.get("roles", []):
            row["recipientCount"] += 1
        if "voter" in actor.get("roles", []):
            row["voterCount"] += 1
            option = actor.get("voteOption", "did_not_vote")
            row["voteAddressCounts"][option] += 1
            row["votePowerByOption"][option] += actor.get("votingPower") or 0
        if "recipient" in actor.get("roles", []) and "voter" in actor.get("roles", []):
            row["recipientVoterCount"] += 1
        row["claims"].extend(claims_by_address.get(actor["address"], []))

    clusters = []
    for row in grouped.values():
        proof_claims = [claim for claim in row["claims"] if claim.get("isAttributionProof")]
        high_claims = [claim for claim in row["claims"] if claim.get("confidence") == "high"]
        signal_claims = [claim for claim in row["claims"] if not claim.get("isAttributionProof")]
        if proof_claims or row["kind"] == "strict_identity" or row["id"] in strict_ids:
            evidence_boundary = "public_owner_proof"
        elif row["kind"] == "signal_cluster" or row["id"] in signal_ids:
            evidence_boundary = "infrastructure_or_public_signal"
        else:
            evidence_boundary = "shared_public_label_only"

        interest_score = (
            min(45, row["totalCompensationGonka"] / 4000)
            + min(35, row["totalVotingPower"] / 7000)
            + (15 if row["recipientVoterCount"] else 0)
            + min(10, max(0, len(row["addresses"]) - 1) * 2)
        )
        top_claims = sorted(
            row["claims"],
            key=lambda claim: (
                {"high": 0, "medium": 1, "low": 2}.get(claim.get("confidence"), 3),
                not claim.get("isAttributionProof"),
                claim.get("sourceType", ""),
            ),
        )[:6]
        caveats = []
        if not proof_claims:
            caveats.append("No strict public owner proof.")
        if signal_claims and evidence_boundary != "public_owner_proof":
            caveats.append("Cluster may be based on infrastructure/public signals, not ownership.")
        if row["totalVotingPower"] == 0 and row["voterCount"]:
            caveats.append("Voter addresses in this cluster had zero archive governance voting power.")
        if row["recipientVoterCount"]:
            caveats.append("At least one address both received compensation and voted.")

        clusters.append(
            {
                "id": row["id"],
                "kind": row["kind"],
                "label": row["label"],
                "actorDisplayLabel": row.get("actorDisplayLabel", row["label"]),
                "actorShortLabel": row.get("actorShortLabel", row["label"]),
                "identityBoundary": row.get("identityBoundary", evidence_boundary),
                "labelSource": row.get("labelSource", ""),
                "addresses": sorted(set(row["addresses"])),
                "roles": sorted(row["roles"]),
                "identityTypes": sorted(row["identityTypes"]),
                "recipientCount": row["recipientCount"],
                "voterCount": row["voterCount"],
                "recipientVoterCount": row["recipientVoterCount"],
                "totalCompensationGonka": round(row["totalCompensationGonka"], 6),
                "totalVotingPower": round(row["totalVotingPower"], 6),
                "voteAddressCounts": dict(row["voteAddressCounts"]),
                "votePowerByOption": {key: round(value, 6) for key, value in sorted(row["votePowerByOption"].items())},
                "evidenceBoundary": evidence_boundary,
                "proofCount": len(proof_claims),
                "highConfidenceClaimCount": len(high_claims),
                "signalClaimCount": len(signal_claims),
                "interestScore": round(interest_score, 3),
                "topEvidence": top_claims,
                "caveats": caveats,
            }
        )

    clusters.sort(key=lambda row: (-row["interestScore"], -row["totalVotingPower"], -row["totalCompensationGonka"], row["label"]))
    for index, row in enumerate(clusters, start=1):
        row["rank"] = index
    return clusters


def build_benefit_power_matrix(recipients, votes, interest_clusters, evidence_claims):
    recipient_by_address = {row["address"]: row for row in recipients}
    vote_by_address = {row["voter"]: row for row in votes}
    claims_by_address = defaultdict(list)
    for claim in evidence_claims:
        if claim.get("address"):
            claims_by_address[claim["address"]].append(claim)

    cluster_by_address = {}
    for cluster in interest_clusters:
        for address in cluster.get("addresses", []):
            cluster_by_address[address] = cluster

    addresses = sorted(set(recipient_by_address) | set(vote_by_address))
    rows = []
    for address in addresses:
        recipient = recipient_by_address.get(address, {})
        vote = vote_by_address.get(address, {})
        cluster = cluster_by_address.get(address, {})
        claims = claims_by_address.get(address, [])
        proof_claims = [claim for claim in claims if claim.get("isAttributionProof")]
        high_claims = [claim for claim in claims if claim.get("confidence") == "high"]
        total_comp = recipient.get("totalGonka") or 0
        voting_power = vote.get("votingPower") or 0
        is_recipient = bool(recipient)
        is_voter = bool(vote)
        overlap = is_recipient and is_voter
        evidence_boundary = cluster.get("evidenceBoundary") or ("public_owner_proof" if proof_claims else ("public_signal" if high_claims else "unknown_or_weak_signal"))
        triage_score = (
            min(40, total_comp / 4000)
            + min(40, voting_power / 7000)
            + (15 if overlap else 0)
            + (8 if evidence_boundary == "public_owner_proof" else 0)
        )
        next_actions = []
        if overlap:
            next_actions.append("review conflict narrative")
        if voting_power and not proof_claims:
            next_actions.append("prioritize owner attribution")
        if total_comp and not proof_claims:
            next_actions.append("enrich beneficiary identity")
        if cluster.get("kind") == "signal_cluster":
            next_actions.append("corroborate infrastructure cluster")
        if not next_actions:
            next_actions.append("monitor")

        rows.append(
            {
                "address": address,
                "label": recipient.get("label") or vote.get("label") or "Unknown public owner",
                "actorDisplayLabel": recipient.get("actorDisplayLabel") or vote.get("actorDisplayLabel") or recipient.get("label") or vote.get("label") or "Unknown public owner",
                "actorShortLabel": recipient.get("actorShortLabel") or vote.get("actorShortLabel") or recipient.get("label") or vote.get("label") or address,
                "identityBoundary": recipient.get("identityBoundary") or vote.get("identityBoundary") or evidence_boundary,
                "labelSource": recipient.get("labelSource") or vote.get("labelSource") or "",
                "publicLabel": recipient.get("publicLabel") or vote.get("publicLabel") or "",
                "operatorSignalLabel": recipient.get("operatorSignalLabel") or vote.get("operatorSignalLabel") or "",
                "operatorSignalDisplayLabel": recipient.get("operatorSignalDisplayLabel") or vote.get("operatorSignalDisplayLabel") or "",
                "isRecipient": is_recipient,
                "isVoter": is_voter,
                "recipientVoterOverlap": overlap,
                "totalCompensationGonka": round(total_comp, 6),
                "votingPower": round(voting_power, 6),
                "voteOption": vote.get("primaryOption", "did_not_vote"),
                "clusterId": cluster.get("id", ""),
                "clusterKind": cluster.get("kind", ""),
                "evidenceBoundary": evidence_boundary,
                "proofCount": len(proof_claims),
                "highConfidenceClaimCount": len(high_claims),
                "triageScore": round(triage_score, 3),
                "nextActions": next_actions,
                "topEvidence": sorted(
                    claims,
                    key=lambda claim: (
                        {"high": 0, "medium": 1, "low": 2}.get(claim.get("confidence"), 3),
                        not claim.get("isAttributionProof"),
                        claim.get("sourceType", ""),
                    ),
                )[:5],
            }
        )

    rows.sort(key=lambda row: (-row["triageScore"], -row["votingPower"], -row["totalCompensationGonka"], row["label"]))
    for index, row in enumerate(rows, start=1):
        row["rank"] = index
    return rows


def build_public_name_enrichment(recipients, votes, identity_evidence, evidence_claims, gns_by_address):
    vote_by_address = {row["voter"]: row for row in votes}
    recipient_by_address = {row["address"]: row for row in recipients}
    claims_by_address = defaultdict(list)
    for claim in evidence_claims:
        if claim.get("address"):
            claims_by_address[claim["address"]].append(claim)

    evidence_by_address = defaultdict(list)
    for item in identity_evidence:
        evidence_by_address[item["address"]].append(item)

    addresses = sorted(set(recipient_by_address) | set(vote_by_address))
    rows = []
    for address in addresses:
        recipient = recipient_by_address.get(address, {})
        vote = vote_by_address.get(address, {})
        node_info = recipient.get("publicNodeInfo") or vote.get("publicNodeInfo") or {}
        matched_validator = node_info.get("matchedValidator") or {}
        gns_names = gns_by_address.get(address) or []
        reverse_names = sorted(item["fullName"] for item in gns_names if item.get("reverse"))
        all_gns_names = sorted(item["fullName"] for item in gns_names)
        public_name_sources = []

        for name in gns_names:
            public_name_sources.append(
                {
                    "sourceType": "gns_name",
                    "value": name["fullName"],
                    "confidence": "high",
                    "isAttributionProof": True,
                    "sourceFile": "data/gns_names_by_address.json",
                }
            )
            for record_key, record in (name.get("records") or {}).items():
                public_name_sources.append(
                    {
                        "sourceType": f"gns_record_{record_key}",
                        "value": str(record.get("value", "")),
                        "confidence": "medium",
                        "isAttributionProof": False,
                        "sourceFile": "data/gns_names_by_address.json",
                    }
                )

        for field, source_type, confidence, proof in [
            ("moniker", "validator_moniker", "high", True),
            ("website", "validator_website", "medium", False),
            ("identity", "validator_identity", "high", True),
            ("securityContact", "validator_security_contact", "high", True),
            ("details", "validator_details", "medium", False),
        ]:
            value = matched_validator.get(field)
            if value:
                public_name_sources.append(
                    {
                        "sourceType": source_type,
                        "value": value,
                        "confidence": confidence,
                        "isAttributionProof": proof and public_owner_proof(source_type, value, matched_validator.get("label", "")),
                        "sourceFile": "data/validators.json",
                    }
                )

        if node_info.get("inferenceUrl"):
            public_name_sources.append(
                {
                    "sourceType": "participant_inference_url",
                    "value": node_info["inferenceUrl"],
                    "confidence": "medium",
                    "isAttributionProof": False,
                    "sourceFile": "data/participants_by_address.json",
                }
            )

        proof_claims = [claim for claim in claims_by_address.get(address, []) if claim.get("isAttributionProof")]
        high_claims = [claim for claim in claims_by_address.get(address, []) if claim.get("confidence") == "high"]
        if proof_claims or any(source["isAttributionProof"] for source in public_name_sources):
            evidence_boundary = "public_owner_proof"
        elif public_name_sources or high_claims:
            evidence_boundary = "public_name_or_metadata_signal"
        else:
            evidence_boundary = "unknown_public_owner"

        best_public_name = ""
        for source_type in ["gns_name", "validator_moniker", "validator_identity", "validator_security_contact", "validator_website", "participant_inference_url"]:
            best_public_name = next((source["value"] for source in public_name_sources if source["sourceType"] == source_type), "")
            if best_public_name:
                break

        next_actions = []
        if evidence_boundary == "unknown_public_owner":
            next_actions.append("find public name source")
        if vote and recipient:
            next_actions.append("review recipient-voter conflict")
        if vote and not proof_claims:
            next_actions.append("corroborate voter owner")
        if recipient and not proof_claims:
            next_actions.append("corroborate beneficiary owner")
        if not reverse_names and all_gns_names:
            next_actions.append("check non-reverse GNS names")
        if not next_actions:
            next_actions.append("archive as public proof")

        rows.append(
            {
                "address": address,
                "label": recipient.get("label") or vote.get("label") or "Unknown public owner",
                "actorDisplayLabel": recipient.get("actorDisplayLabel") or vote.get("actorDisplayLabel") or recipient.get("label") or vote.get("label") or "Unknown public owner",
                "actorShortLabel": recipient.get("actorShortLabel") or vote.get("actorShortLabel") or recipient.get("label") or vote.get("label") or address,
                "identityBoundary": recipient.get("identityBoundary") or vote.get("identityBoundary") or evidence_boundary,
                "labelSource": recipient.get("labelSource") or vote.get("labelSource") or "",
                "bestPublicName": best_public_name,
                "roles": sorted([role for role, present in {"recipient": bool(recipient), "voter": bool(vote)}.items() if present]),
                "totalCompensationGonka": round(recipient.get("totalGonka") or 0, 6),
                "votingPower": round(vote.get("votingPower") or 0, 6),
                "voteOption": vote.get("primaryOption", "did_not_vote"),
                "gnsNames": all_gns_names,
                "reverseGnsNames": reverse_names,
                "validatorOperatorAddress": matched_validator.get("operatorAddress", ""),
                "validatorMoniker": matched_validator.get("moniker", ""),
                "validatorWebsite": matched_validator.get("website", ""),
                "validatorIdentity": matched_validator.get("identity", ""),
                "validatorSecurityContact": matched_validator.get("securityContact", ""),
                "validatorDetails": matched_validator.get("details", ""),
                "inferenceUrl": node_info.get("inferenceUrl", ""),
                "evidenceBoundary": evidence_boundary,
                "publicNameSources": public_name_sources,
                "evidenceClaims": sorted(
                    claims_by_address.get(address, []),
                    key=lambda claim: (
                        {"high": 0, "medium": 1, "low": 2}.get(claim.get("confidence"), 3),
                        not claim.get("isAttributionProof"),
                        claim.get("sourceType", ""),
                    ),
                )[:8],
                "nextActions": next_actions,
            }
        )

    rows.sort(
        key=lambda row: (
            row["evidenceBoundary"] != "public_owner_proof",
            row["evidenceBoundary"] == "unknown_public_owner",
            -row["votingPower"],
            -row["totalCompensationGonka"],
            row["label"],
        )
    )

    groups = {}
    for row in rows:
        for source in row["publicNameSources"]:
            value = source["value"]
            if not value:
                continue
            key = (source["sourceType"], value)
            groups.setdefault(
                key,
                {
                    "sourceType": source["sourceType"],
                    "value": value,
                    "confidence": source["confidence"],
                    "isAttributionProof": source["isAttributionProof"],
                    "sourceFile": source["sourceFile"],
                    "addresses": [],
                    "totalCompensationGonka": 0,
                    "totalVotingPower": 0,
                    "votePowerByOption": defaultdict(float),
                },
            )
            group = groups[key]
            group["addresses"].append(row["address"])
            group["totalCompensationGonka"] += row["totalCompensationGonka"]
            group["totalVotingPower"] += row["votingPower"]
            if row["votingPower"]:
                group["votePowerByOption"][row["voteOption"]] += row["votingPower"]

    grouped_sources = []
    for group in groups.values():
        grouped_sources.append(
            {
                **group,
                "addresses": sorted(set(group["addresses"])),
                "totalCompensationGonka": round(group["totalCompensationGonka"], 6),
                "totalVotingPower": round(group["totalVotingPower"], 6),
                "votePowerByOption": {key: round(value, 6) for key, value in sorted(group["votePowerByOption"].items())},
            }
        )
    grouped_sources.sort(key=lambda row: (-len(row["addresses"]), -row["totalCompensationGonka"], -row["totalVotingPower"], row["sourceType"], row["value"]))

    summary = {
        "proposalAddressCount": len(rows),
        "proposalAddressesWithAnyPublicName": sum(1 for row in rows if row["publicNameSources"]),
        "proposalAddressesWithPublicOwnerProof": sum(1 for row in rows if row["evidenceBoundary"] == "public_owner_proof"),
        "proposalAddressesWithGns": sum(1 for row in rows if row["gnsNames"]),
        "proposalAddressesWithReverseGns": sum(1 for row in rows if row["reverseGnsNames"]),
        "gnsSnapshotAddressCount": len(gns_by_address),
        "gnsSnapshotNameCount": sum(len(names) for names in gns_by_address.values()),
        "publicNameGroupCount": len(grouped_sources),
        "publicNameGroupsWithMultipleProposalAddresses": sum(1 for row in grouped_sources if len(row["addresses"]) > 1),
    }

    return {"summary": summary, "rows": rows, "groups": grouped_sources}


def load_epoch_group_snapshot(epoch):
    path = DATA / "voting_end_epochs" / f"e{epoch}" / "epoch_group_data.json"
    if not path.exists():
        return {}
    wrapper = load_json(path)
    payload = wrapper.get("json") or {}
    return payload.get("epoch_group_data") or payload


def epoch_weights(epoch):
    group = load_epoch_group_snapshot(epoch)
    rows = {}
    for item in group.get("validation_weights") or []:
        address = item.get("member_address")
        if not address:
            continue
        rows[address] = {
            "weight": int(item.get("weight") or item.get("voting_power") or 0),
            "raw": item,
        }
    return rows


def block_time(height):
    path = DATA / "voting_end_epochs" / "blocks" / f"block_{height}.json"
    if not path.exists():
        return ""
    wrapper = load_json(path)
    block = ((wrapper.get("json") or {}).get("result") or {}).get("block") or {}
    return ((block.get("header") or {}).get("time")) or ""


def build_epoch_anomalies(votes, recipients, labels_by_address):
    epochs = [285, 286, 287, 288, 289, 290]
    weights = {epoch: epoch_weights(epoch) for epoch in epochs}
    groups = {epoch: load_epoch_group_snapshot(epoch) for epoch in epochs}
    vote_by_address = {vote["voter"]: vote for vote in votes}
    recipient_set = {row["address"] for row in recipients}
    relevant = set().union(*(set(rows) for rows in weights.values() if rows))
    relevant |= set(vote_by_address)
    anomalies = []
    e287_start = int(groups.get(287, {}).get("effective_block_height") or 0)
    e288_start = int(groups.get(288, {}).get("effective_block_height") or 0)
    e287_start_time = block_time(e287_start)
    e288_start_time = block_time(e288_start)
    for address in sorted(relevant):
        row_weights = {f"e{epoch}": weights.get(epoch, {}).get(address, {}).get("weight", 0) for epoch in epochs}
        e287_weight = row_weights.get("e287", 0)
        if not e287_weight:
            continue
        prev_max = max(row_weights.get("e285", 0), row_weights.get("e286", 0))
        next_max = max(row_weights.get("e288", 0), row_weights.get("e289", 0), row_weights.get("e290", 0))
        entered_e287 = prev_max == 0
        exited_after_e287 = next_max == 0
        vote = vote_by_address.get(address)
        vote_height = vote.get("height") if vote else None
        governance_voting_power = vote.get("votingPower") if vote else 0
        governance_voting_power = governance_voting_power or 0
        voted_during_e287 = bool(vote_height and e287_start and (not e288_start or e287_start <= vote_height < e288_start))
        weight_delta = e287_weight - prev_max
        anomaly_score = 0
        anomaly_score += min(35, e287_weight / 3500)
        anomaly_score += 25 if entered_e287 else 0
        anomaly_score += 25 if exited_after_e287 else 0
        anomaly_score += 20 if voted_during_e287 else 0
        anomaly_score += 10 if vote and vote.get("primaryOption") == "no_with_veto" else 0
        anomaly_score += 8 if address in recipient_set else 0
        if e287_weight >= 20_000 or entered_e287 or exited_after_e287 or voted_during_e287:
            anomalies.append(
                {
                    "address": address,
                    "label": labels_by_address.get(address, "Unknown public owner"),
                    "weights": row_weights,
                    "e287Weight": e287_weight,
                    "prevMaxWeight": prev_max,
                    "nextMaxWeight": next_max,
                    "weightDeltaIntoE287": weight_delta,
                    "enteredE287": entered_e287,
                    "exitedAfterE287": exited_after_e287,
                    "votedDuringE287": voted_during_e287,
                    "voteHeight": vote_height,
                    "voteBlockTime": block_time(vote_height) if vote_height else "",
                    "voteOption": vote.get("primaryOption") if vote else "did_not_vote",
                    "governanceVotingPower": governance_voting_power,
                    "governanceVotingPowerSource": vote.get("votingPowerSource", "") if vote else "",
                    "hasGovernanceVotingPower": governance_voting_power > 0,
                    "e287StartHeight": e287_start,
                    "e287StartTime": e287_start_time,
                    "e288StartHeight": e288_start,
                    "e288StartTime": e288_start_time,
                    "isRecipient": address in recipient_set,
                    "anomalyScore": round(anomaly_score, 3),
                    "status": "operational_enter_vote_exit_signal" if entered_e287 and exited_after_e287 and voted_during_e287 else ("partial_operational_timing_signal" if voted_during_e287 or entered_e287 or exited_after_e287 else "context"),
                    "caveat": "Inference epoch weight/timing is operational evidence only. It is not governance voting power and does not prove whether a vote was counted.",
                }
            )
    anomalies.sort(key=lambda row: (-row["anomalyScore"], -row["e287Weight"], row["address"]))
    return anomalies


def build_epoch_entry_exit_clusters(epoch_anomalies, recipients, votes, identity_graph, evidence_claims):
    recipient_by_address = {row["address"]: row for row in recipients}
    vote_by_address = {row["voter"]: row for row in votes}
    strict_by_address = {
        address: cluster["id"]
        for cluster in identity_graph.get("strictClusters", [])
        for address in cluster.get("addresses", [])
    }
    signal_by_address = {
        address: cluster["id"]
        for cluster in identity_graph.get("signalClusters", [])
        for address in cluster.get("addresses", [])
    }
    claims_by_address = defaultdict(list)
    for claim in evidence_claims:
        if claim.get("address"):
            claims_by_address[claim["address"]].append(claim)

    groups = {}
    for row in epoch_anomalies:
        address = row["address"]
        group_id = strict_by_address.get(address) or signal_by_address.get(address)
        if not group_id:
            continue
        kind = "strict_identity" if strict_by_address.get(address) else "signal_cluster"
        group = groups.setdefault(
            group_id,
            {
                "id": group_id,
                "kind": kind,
                "label": row["label"],
                "addresses": set(),
                "addressRows": [],
                "totalE287Weight": 0,
                "maxE287Weight": 0,
                "enteredCount": 0,
                "exitedCount": 0,
                "votedDuringCount": 0,
                "recipientCount": 0,
                "totalCompensationGonka": 0.0,
                "voteCounts": Counter(),
                "votePowerByOption": defaultdict(float),
                "totalGovernanceVotingPower": 0,
                "confirmedEnterVoteExitWithPowerCount": 0,
                "topEvidence": [],
                "topEvidenceKeys": set(),
                "caveats": set(),
            },
        )
        payout = recipient_by_address.get(address, {}).get("totalGonka", 0) or 0
        vote = vote_by_address.get(address) or {}
        group["addresses"].add(address)
        group["totalE287Weight"] += row["e287Weight"]
        group["maxE287Weight"] = max(group["maxE287Weight"], row["e287Weight"])
        group["enteredCount"] += int(row["enteredE287"])
        group["exitedCount"] += int(row["exitedAfterE287"])
        group["votedDuringCount"] += int(row["votedDuringE287"])
        group["recipientCount"] += int(row["isRecipient"])
        group["totalCompensationGonka"] += payout
        group["voteCounts"][row["voteOption"]] += 1
        group["totalGovernanceVotingPower"] += row.get("governanceVotingPower") or 0
        if row.get("voteOption") != "did_not_vote":
            group["votePowerByOption"][row["voteOption"]] += row.get("governanceVotingPower") or 0
        if row["enteredE287"] and row["exitedAfterE287"] and row["votedDuringE287"] and row.get("governanceVotingPower"):
            group["confirmedEnterVoteExitWithPowerCount"] += 1
        if row["status"] != "operational_enter_vote_exit_signal":
            group["caveats"].add("Some addresses are timing/context leads, not full enter-vote-exit operational cases.")
        if kind != "strict_identity":
            group["caveats"].add("Cluster is not strict public owner proof.")
        group["caveats"].add("Inference epoch weight is not governance voting power; vote inclusion must be checked through governance tally/staking data.")
        address_claims = sorted(
            claims_by_address.get(address, []),
            key=lambda claim: (
                {"high": 0, "medium": 1, "low": 2}.get(claim.get("confidence"), 3),
                not claim.get("isAttributionProof"),
                claim.get("sourceType", ""),
            ),
        )
        for claim in address_claims[:3]:
            evidence_key = (address, claim["sourceType"], claim["sourceValue"], claim["confidence"], claim["isAttributionProof"])
            if evidence_key in group["topEvidenceKeys"]:
                continue
            group["topEvidenceKeys"].add(evidence_key)
            group["topEvidence"].append(
                {
                    "address": address,
                    "sourceType": claim["sourceType"],
                    "sourceValue": claim["sourceValue"],
                    "confidence": claim["confidence"],
                    "isAttributionProof": claim["isAttributionProof"],
                }
            )
        group["addressRows"].append(
            {
                "address": address,
                "label": row["label"],
                "e287Weight": row["e287Weight"],
                "prevMaxWeight": row["prevMaxWeight"],
                "nextMaxWeight": row["nextMaxWeight"],
                "enteredE287": row["enteredE287"],
                "exitedAfterE287": row["exitedAfterE287"],
                "votedDuringE287": row["votedDuringE287"],
                "voteOption": row["voteOption"],
                "voteHeight": row["voteHeight"],
                "voteBlockTime": row["voteBlockTime"],
                "governanceVotingPower": row.get("governanceVotingPower", 0),
                "governanceVotingPowerSource": row.get("governanceVotingPowerSource", ""),
                "hasGovernanceVotingPower": row.get("hasGovernanceVotingPower", False),
                "isRecipient": row["isRecipient"],
                "totalCompensationGonka": round(payout, 6),
                "strictClusterId": strict_by_address.get(address, ""),
                "signalClusterId": signal_by_address.get(address, ""),
                "inferenceUrl": recipient_by_address.get(address, {}).get("inferenceUrl", ""),
                "txHash": vote.get("txHash", ""),
                "anomalyScore": row["anomalyScore"],
                "status": row["status"],
            }
        )

    clusters = []
    for group in groups.values():
        rows = sorted(group["addressRows"], key=lambda item: (-item["anomalyScore"], -item["e287Weight"], item["address"]))
        confirmed = [row for row in rows if row["enteredE287"] and row["exitedAfterE287"] and row["votedDuringE287"]]
        clusters.append(
            {
                "id": group["id"],
                "kind": group["kind"],
                "label": group["label"],
                "addresses": sorted(group["addresses"]),
                "addressRows": rows,
                "addressesCount": len(group["addresses"]),
                "totalE287Weight": group["totalE287Weight"],
                "maxE287Weight": group["maxE287Weight"],
                "enteredCount": group["enteredCount"],
                "exitedCount": group["exitedCount"],
                "votedDuringCount": group["votedDuringCount"],
                "confirmedEnterVoteExitCount": len(confirmed),
                "confirmedEnterVoteExitWithPowerCount": group["confirmedEnterVoteExitWithPowerCount"],
                "recipientCount": group["recipientCount"],
                "totalCompensationGonka": round(group["totalCompensationGonka"], 6),
                "totalGovernanceVotingPower": round(group["totalGovernanceVotingPower"], 6),
                "votePowerByOption": {key: round(value, 6) for key, value in sorted(group["votePowerByOption"].items())},
                "voteCounts": dict(group["voteCounts"]),
                "topEvidence": group["topEvidence"][:8],
                "caveats": sorted(group["caveats"]) or ["Operational timing cluster; not governance voting power and owner attribution still requires public proof."],
                "priorityScore": round(
                    min(45, group["totalE287Weight"] / 3000)
                    + group["enteredCount"] * 8
                    + group["exitedCount"] * 8
                    + group["votedDuringCount"] * 10
                    + len(confirmed) * 12
                    + min(20, group["totalGovernanceVotingPower"] / 7000)
                    + min(20, group["totalCompensationGonka"] / 8000),
                    3,
                ),
            }
        )
    clusters.sort(key=lambda row: (-row["priorityScore"], -row["totalE287Weight"], row["label"]))
    for index, row in enumerate(clusters, start=1):
        row["rank"] = index
    return clusters


def build_attack_narrative(proposal, votes, epochs, epoch_anomalies):
    voting_start = proposal.get("voting_start_time", "")
    voting_end = proposal.get("voting_end_time", "")
    e287_time = block_time(4_428_972)
    return {
        "title": "Proposal #67 Kimi restitution attack investigation",
        "phases": [
            {
                "id": "damage",
                "label": "Visible e265 damage",
                "timeOrHeight": "e265",
                "summary": "Initial visible attack/damage component was materially smaller than the final restitution proposal.",
                "confidence": "high",
            },
            {
                "id": "restitution_construction",
                "label": "Restitution construction",
                "timeOrHeight": proposal.get("metadata", ""),
                "summary": "Upstream restitution repository computed compensation for epochs e265-e276.",
                "confidence": "high",
            },
            {
                "id": "proposal_submission",
                "label": "Proposal submission",
                "timeOrHeight": proposal.get("submit_time", ""),
                "summary": f"Proposal submitted by {proposal.get('proposer', '')}; message sender {proposal.get('messages', [{}])[0].get('sender', '')}.",
                "confidence": "high",
            },
            {
                "id": "voting",
                "label": "Voting window",
                "timeOrHeight": f"{voting_start} to {voting_end}",
                "summary": f"{len(votes)} final on-chain voters after last-vote-wins consolidation.",
                "confidence": "high",
            },
            {
                "id": "voting_end_epoch_anomaly",
                "label": "Voting-end inference timing",
                "timeOrHeight": f"e287 effective 4428972 {e287_time}".strip(),
                "summary": f"{len(epoch_anomalies)} e287 inference weight/timing leads detected. These are not governance voting power and do not prove vote inclusion.",
                "confidence": "medium" if epoch_anomalies else "low",
            },
            {
                "id": "post_vote_outcome",
                "label": "Proposal outcome",
                "timeOrHeight": proposal.get("status", ""),
                "summary": "Final aggregate tally passed. Per-voter governance voting power remains unknown unless exact historical gov/staking data is added.",
                "confidence": "high",
            },
        ],
    }


def build_hypotheses(ranked_parties, epoch_anomalies, telegram_evidence, proposal):
    telegram_rows = telegram_evidence.get("messages") or []
    e287_vote_anomalies = [row for row in epoch_anomalies if row["votedDuringE287"]]
    entered_and_exited = [row for row in epoch_anomalies if row["enteredE287"] and row["exitedAfterE287"]]
    e287_vote_with_power = [row for row in epoch_anomalies if row["votedDuringE287"] and row.get("governanceVotingPower")]
    full_enter_vote_exit_with_power = [
        row
        for row in epoch_anomalies
        if row["enteredE287"] and row["votedDuringE287"] and row["exitedAfterE287"] and row.get("governanceVotingPower")
    ]
    recipient_voters = [row for row in ranked_parties if "recipient" in row["roles"] and "voter" in row["roles"]]
    return [
        {
            "id": "large_weight_node_entered_voting_end_epoch",
            "title": "Large-weight node around voting-end epoch",
            "status": "partially_supported" if e287_vote_anomalies else "needs_more_data",
            "summary": f"{len(e287_vote_anomalies)} voting addresses overlap with e287 inference timing; {len(e287_vote_with_power)} of them have non-zero exact governance power. {len(entered_and_exited)} entered and exited strictly in the compared inference window, but {len(full_enter_vote_exit_with_power)} rows satisfy enter+vote+exit with non-zero governance power.",
            "evidenceRefs": [row["address"] for row in epoch_anomalies[:10]],
            "nextCheck": "Review reports/voting_window_power_reconciliation.md, then widen the compared epoch window if the suspected temporary validator entered before e287 or exited after e290.",
        },
        {
            "id": "recipient_voters_conflict",
            "title": "Recipients also voted",
            "status": "confirmed" if recipient_voters else "refuted",
            "summary": f"{len(recipient_voters)} ranked parties include both recipient and voter roles.",
            "evidenceRefs": [row["id"] for row in recipient_voters[:10]],
            "nextCheck": "Review vote option and public owner proof for each recipient-voter party.",
        },
        {
            "id": "proposal_sender_interest",
            "title": "Proposal proposer/message sender interest",
            "status": "confirmed",
            "summary": f"Proposer {proposal.get('proposer', '')}; message sender {proposal.get('messages', [{}])[0].get('sender', '')}.",
            "evidenceRefs": [proposal.get("proposer", ""), proposal.get("messages", [{}])[0].get("sender", "")],
            "nextCheck": "Trace archive-node transaction graph and public identity labels for both addresses.",
        },
        {
            "id": "telegram_identity_link",
            "title": "Telegram identity links",
            "status": "partially_supported" if telegram_rows else "needs_more_data",
            "summary": f"{len(telegram_rows)} Telegram excerpts contain addresses, URLs, or usernames.",
            "evidenceRefs": [f"{row['chat']}#{row['messageId']}" for row in telegram_rows[:10]],
            "nextCheck": "Corroborate Telegram excerpts with public on-chain/GNS/GitHub/validator evidence before treating as owner proof.",
        },
    ]


def load_upstream_epoch_group(epoch, snapshot=""):
    if epoch == 265 and snapshot:
        path = UPSTREAM / "e265" / f"epoch265_group_data_{snapshot}.json"
    else:
        path = UPSTREAM / f"e{epoch}" / f"epoch{epoch}_group_data.json"
    if not path.exists():
        return {}
    payload = load_json(path)
    if isinstance(payload, list):
        payload = payload[0] if payload else {}
    return payload.get("epoch_group_data") or payload


def upstream_epoch_weights(epoch, snapshot=""):
    group = load_upstream_epoch_group(epoch, snapshot)
    weights = {}
    for item in group.get("validation_weights") or []:
        address = item.get("member_address")
        if address:
            weights[address] = int(item.get("weight") or item.get("voting_power") or 0)
    return weights


def load_cpoc_epoch_group(epoch, phase):
    path = DATA / "cpoc_epoch_snapshots" / f"e{epoch}" / f"{phase}.json"
    if path.exists():
        wrapper = load_json(path)
        payload = wrapper.get("json") or {}
        return payload.get("epoch_group_data") or payload
    if epoch == 265:
        return load_upstream_epoch_group(epoch, "healthy" if phase == "start" else "end")
    return load_upstream_epoch_group(epoch)


def load_cpoc_manifest():
    path = DATA / "cpoc_epoch_snapshots" / "manifest.json"
    if not path.exists():
        return {}
    return load_json(path)


def cpoc_manifest_epochs():
    manifest = load_cpoc_manifest()
    return {int(row["epoch"]): row for row in manifest.get("epochs", []) if row.get("epoch") is not None}


def load_cpoc_snapshot_file(relative_file):
    path = DATA / "cpoc_epoch_snapshots" / relative_file
    wrapper = load_json(path)
    payload = wrapper.get("json") or wrapper
    return payload.get("epoch_group_data") or payload


def cpoc_columns_for_epoch(epoch, manifest_epochs):
    columns = [{"key": f"e{epoch}_weight", "label": f"e{epoch} W", "epoch": epoch, "phase": "start", "type": "weight"}]
    manifest_epoch = manifest_epochs.get(epoch, {})
    checkpoints = manifest_epoch.get("checkpoints") or []
    cpoc_checkpoints = [row for row in checkpoints if row.get("kind") != "start"]
    if not cpoc_checkpoints:
        columns.append(
            {
                "key": f"e{epoch}_cpoc",
                "label": "CPoC",
                "epoch": epoch,
                "phase": "cpoc",
                "type": "cpoc",
                "checkpointIndex": 1,
                "fallback": True,
            }
        )
        return columns
    for checkpoint in cpoc_checkpoints:
        index = int(checkpoint.get("index") or 0)
        columns.append(
            {
                "key": f"e{epoch}_c{index}",
                "label": f"C{index}",
                "epoch": epoch,
                "phase": f"cpoc_{index}",
                "type": "cpoc",
                "checkpointIndex": index,
                "height": checkpoint.get("height"),
                "blockTime": checkpoint.get("blockTime") or "",
                "file": checkpoint.get("file"),
                "snapshotStatus": checkpoint.get("snapshotStatus") or ("fetched" if checkpoint.get("file") else "missing"),
                "fallback": not bool(checkpoint.get("file")),
            }
        )
    return columns


def cpoc_epoch_weights_from_group(group):
    weights = {}
    for item in group.get("validation_weights") or []:
        address = item.get("member_address")
        if not address:
            continue
        weights[address] = {
            "weight": int(item.get("weight") or item.get("voting_power") or 0),
            "confirmationWeight": int(item.get("confirmation_weight") or 0),
        }
    return weights


def weights_for_timeline_column(column, manifest_epochs):
    epoch = column["epoch"]
    if column.get("file"):
        return cpoc_epoch_weights_from_group(load_cpoc_snapshot_file(column["file"]))
    if column["type"] == "weight":
        manifest_epoch = manifest_epochs.get(epoch, {})
        start = next((row for row in manifest_epoch.get("checkpoints", []) if row.get("kind") == "start"), None)
        if start and start.get("file"):
            return cpoc_epoch_weights_from_group(load_cpoc_snapshot_file(start["file"]))
        return cpoc_epoch_weights_from_group(load_cpoc_epoch_group(epoch, "start"))
    if column.get("fallback"):
        return {}
    return cpoc_epoch_weights_from_group(load_cpoc_epoch_group(epoch, "cpoc"))


def model_bucket(model_id):
    value = (model_id or "").lower()
    if "qwen" in value:
        return "qwen"
    if "kimi" in value or "moonshot" in value:
        return "kimi"
    return "other"


def upstream_epoch_model_activity(epoch):
    path = UPSTREAM / f"e{epoch}" / f"epoch{epoch}_commits.json"
    if not path.exists():
        return {}
    payload = load_json(path)
    commits = payload.get("commits") if isinstance(payload, dict) else payload
    activity = defaultdict(lambda: {"qwenCount": 0, "kimiCount": 0, "otherCount": 0, "totalCommitCount": 0})
    for item in commits or []:
        address = item.get("participant_address") or item.get("participant")
        if not address:
            continue
        count = int(item.get("count") or 0)
        bucket = model_bucket(item.get("model_id"))
        key = {"qwen": "qwenCount", "kimi": "kimiCount"}.get(bucket, "otherCount")
        activity[address][key] += count
        activity[address]["totalCommitCount"] += count
    return activity


def build_participant_epoch_timeline(recipients, votes):
    manifest_epochs = cpoc_manifest_epochs()
    columns = []
    for epoch in EPOCHS:
        columns.extend(cpoc_columns_for_epoch(epoch, manifest_epochs))
    weights_by_column = {column["key"]: weights_for_timeline_column(column, manifest_epochs) for column in columns}
    weight_column_by_epoch = {column["epoch"]: column for column in columns if column["type"] == "weight"}
    activity_by_epoch = {epoch: upstream_epoch_model_activity(epoch) for epoch in EPOCHS}
    vote_by_address = {vote["voter"]: vote for vote in votes}
    recipient_by_address = {recipient["address"]: recipient for recipient in recipients}
    observed_addresses = set(recipient_by_address)
    for weights in weights_by_column.values():
        observed_addresses.update(weights)
    for activity in activity_by_epoch.values():
        observed_addresses.update(activity)
    rows = []
    max_weight = 0
    max_reward = 0
    reward_without_weight_count = 0
    reward_without_confirmation_count = 0
    def sort_key(address):
        recipient = recipient_by_address.get(address, {})
        has_compensation = 1 if recipient.get("totalGonka", 0) > 0 else 0
        max_observed_weight = max((weights.get(address, {}).get("weight", 0) for weights in weights_by_column.values()), default=0)
        total_commits = sum((activity.get(address, {}).get("totalCommitCount", 0) for activity in activity_by_epoch.values()), 0)
        return (-has_compensation, -recipient.get("totalGonka", 0), -max_observed_weight, -total_commits, address)

    for address in sorted(observed_addresses, key=sort_key):
        recipient = recipient_by_address.get(address)
        recipient_per_epoch = recipient.get("perEpoch", {}) if recipient else {}
        vote = vote_by_address.get(address, {})
        seen_active = False
        previous_weight = 0
        previous_cpoc_confirmation_by_epoch = {}
        first_failed_cpoc = None
        cells = []
        for index, column in enumerate(columns):
            epoch = column["epoch"]
            start_column = weight_column_by_epoch[epoch]
            start_row = weights_by_column[start_column["key"]].get(address, {})
            current_row = weights_by_column[column["key"]].get(address, {})
            weight = current_row.get("weight", 0)
            start_weight = start_row.get("weight", 0)
            confirmation_weight = current_row.get("confirmationWeight", 0)
            previous_cpoc_confirmation = previous_cpoc_confirmation_by_epoch.get(epoch)
            cpoc_delta_confirmation = (
                confirmation_weight - previous_cpoc_confirmation
                if column["type"] == "cpoc" and previous_cpoc_confirmation is not None and not column.get("fallback")
                else None
            )
            reward = recipient_per_epoch.get(f"e{epoch}", 0)
            activity = activity_by_epoch.get(epoch, {}).get(address, {})
            reward_without_weight = bool(reward and reward > 0 and start_weight <= 0)
            reward_without_confirmation = bool(
                reward and reward > 0 and column["type"] == "cpoc" and not column.get("fallback") and start_weight > 0 and confirmation_weight <= 0
            )
            if column["type"] == "cpoc":
                ratio = (confirmation_weight / start_weight) if start_weight and not column.get("fallback") else 0
                if column.get("fallback"):
                    state = "snapshot_missing"
                elif start_weight <= 0:
                    state = "no_epoch_weight"
                elif confirmation_weight <= 0:
                    state = "cpoc_failed"
                elif ratio < 0.5:
                    state = "cpoc_degraded"
                else:
                    state = "confirmed"
            else:
                if weight > 0:
                    state = "returned" if seen_active and previous_weight == 0 else "active"
                    seen_active = True
                elif previous_weight > 0:
                    state = "dropped"
                elif seen_active:
                    state = "missing_after_active"
                else:
                    state = "no_weight"
            if column["type"] == "cpoc" and not column.get("fallback"):
                previous_cpoc_confirmation_by_epoch[epoch] = confirmation_weight
                if first_failed_cpoc is None and start_weight > 0 and confirmation_weight <= 0:
                    first_failed_cpoc = {"epoch": epoch, "checkpointIndex": column.get("checkpointIndex"), "height": column.get("height")}
            max_weight = max(max_weight, weight)
            max_reward = max(max_reward, reward or 0)
            reward_without_weight_count += 1 if reward_without_weight and column["type"] == "weight" else 0
            reward_without_confirmation_count += 1 if reward_without_confirmation else 0
            cells.append(
                {
                    "x": index,
                    "columnKey": column["key"],
                    "columnType": column["type"],
                    "epoch": epoch,
                    "snapshot": column["phase"],
                    "checkpointIndex": column.get("checkpointIndex"),
                    "height": column.get("height"),
                    "blockTime": column.get("blockTime") or "",
                    "fallback": bool(column.get("fallback")),
                    "snapshotStatus": column.get("snapshotStatus") or "",
                    "state": state,
                    "weight": weight,
                    "startWeight": start_weight,
                    "confirmationWeight": confirmation_weight,
                    "cpocDeltaConfirmation": cpoc_delta_confirmation,
                    "confirmationRatio": round((confirmation_weight / start_weight) if start_weight else 0, 6),
                    "confirmed": state == "confirmed",
                    "rewardGonka": round(reward or 0, 6),
                    "rewardWithoutWeight": reward_without_weight,
                    "rewardWithoutConfirmation": reward_without_confirmation,
                    "qwenCount": activity.get("qwenCount", 0) if column["type"] == "weight" else 0,
                    "kimiCount": activity.get("kimiCount", 0) if column["type"] == "weight" else 0,
                    "otherCount": activity.get("otherCount", 0) if column["type"] == "weight" else 0,
                    "totalCommitCount": activity.get("totalCommitCount", 0) if column["type"] == "weight" else 0,
                }
            )
            if column["type"] == "weight":
                previous_weight = weight
        rows.append(
            {
                "address": address,
                "actorDisplayLabel": recipient.get("actorDisplayLabel", recipient.get("label", address)) if recipient else address,
                "actorShortLabel": recipient.get("actorShortLabel", recipient.get("label", address)) if recipient else address,
                "rank": recipient.get("rank") if recipient else None,
                "totalCompensationGonka": recipient.get("totalGonka", 0) if recipient else 0,
                "compensationStatus": "compensated" if recipient else "not_compensated",
                "voteOption": recipient.get("voteOption", "did_not_vote") if recipient else (vote.get("primaryOption") or "did_not_vote"),
                "governanceVotingPower": vote.get("votingPower") or 0,
                "firstFailedCpocIndex": first_failed_cpoc.get("checkpointIndex") if first_failed_cpoc else None,
                "firstFailedCpocHeight": first_failed_cpoc.get("height") if first_failed_cpoc else None,
                "firstFailedCpocEpoch": first_failed_cpoc.get("epoch") if first_failed_cpoc else None,
                "cells": cells,
            }
        )
    return {
        "columns": columns,
        "rows": rows,
        "summary": {
            "maxWeight": max_weight,
            "maxRewardGonka": round(max_reward, 6),
            "cpocCheckpointCount": sum(1 for column in columns if column["type"] == "cpoc"),
            "rewardWithoutWeightCount": reward_without_weight_count,
            "rewardWithoutConfirmationCount": reward_without_confirmation_count,
        },
    }


def build_dashboard_chart_data(proposal, recipients, votes, epochs, epoch_anomalies, summary, attack_narrative):
    recipient_by_address = {row["address"]: row for row in recipients}
    vote_options = ["yes", "no", "abstain", "no_with_veto"]
    vote_by_address = {vote["voter"]: vote for vote in votes}
    vote_matrix_groups = defaultdict(lambda: {"addresses": [], "totalCompensationGonka": 0, "votingPower": 0})
    for address in sorted(set(recipient_by_address) | set(vote_by_address)):
        recipient = recipient_by_address.get(address)
        vote = vote_by_address.get(address)
        recipient_status = "recipient" if recipient else "non_recipient"
        vote_option = vote["primaryOption"] if vote else "did_not_vote"
        group = vote_matrix_groups[(recipient_status, vote_option)]
        group["addresses"].append(address)
        group["totalCompensationGonka"] += recipient.get("totalGonka", 0) if recipient else 0
        group["votingPower"] += vote.get("votingPower") or 0 if vote else 0

    vote_matrix = []
    for recipient_status in ["recipient", "non_recipient"]:
        for option in [*vote_options, "did_not_vote"]:
            group = vote_matrix_groups[(recipient_status, option)]
            vote_matrix.append(
                {
                    "recipientStatus": recipient_status,
                    "voteOption": option,
                    "addressCount": len(group["addresses"]),
                    "totalCompensationGonka": round(group["totalCompensationGonka"], 6),
                    "votingPower": round(group["votingPower"], 6),
                    "addresses": group["addresses"],
                }
            )

    compensation_components = []
    for row in recipients:
        vote = next((vote for vote in votes if vote["voter"] == row["address"]), {})
        compensation_components.append(
            {
                "address": row["address"],
                "actorDisplayLabel": row.get("actorDisplayLabel", row["label"]),
                "actorShortLabel": row.get("actorShortLabel", row["label"]),
                "identityBoundary": row.get("identityBoundary", ""),
                "rank": row["rank"],
                "attackE265E266Gonka": row["attackE265E266Gonka"],
                "capE267E276Gonka": row["capE267E276Gonka"],
                "totalGonka": row["totalGonka"],
                "voteOption": row.get("voteOption", "did_not_vote"),
                "votingPower": vote.get("votingPower") or 0,
                "recipientVoterOverlap": bool(vote),
            }
        )

    timing_leads = []
    for row in epoch_anomalies:
        recipient = recipient_by_address.get(row["address"], {})
        timing_leads.append(
            {
                "address": row["address"],
                "actorDisplayLabel": row.get("actorDisplayLabel") or row["label"],
                "actorShortLabel": row.get("actorShortLabel") or short_actor_label(row["address"], row["label"]),
                "identityBoundary": row.get("identityBoundary", recipient.get("identityBoundary", "")),
                "anomalyScore": row["anomalyScore"],
                "prevMaxWeight": row["prevMaxWeight"],
                "e287Weight": row["e287Weight"],
                "nextMaxWeight": row["nextMaxWeight"],
                "enteredE287": row["enteredE287"],
                "votedDuringE287": row["votedDuringE287"],
                "exitedAfterE287": row["exitedAfterE287"],
                "voteOption": row["voteOption"],
                "voteHeight": row["voteHeight"],
                "voteBlockTime": row["voteBlockTime"],
                "governanceVotingPower": row.get("governanceVotingPower", 0),
                "isRecipient": row["isRecipient"],
                "totalCompensationGonka": recipient.get("totalGonka", 0),
                "status": row["status"],
                "caveat": row.get("caveat", ""),
            }
        )

    event_timeline = []
    for phase in attack_narrative.get("phases", []):
        event_timeline.append({**phase, "time": ""})
    event_times = {
        "proposal_submission": proposal.get("submit_time", ""),
        "voting": proposal.get("voting_start_time", ""),
        "post_vote_outcome": proposal.get("voting_end_time", ""),
        "voting_end_epoch_anomaly": block_time(4_428_972),
    }
    if votes:
        event_times["first_vote"] = min((vote.get("blockTime") or "" for vote in votes if vote.get("blockTime")), default="")
        event_times["last_vote"] = max((vote.get("blockTime") or "" for vote in votes if vote.get("blockTime")), default="")
        event_timeline.extend(
            [
                {
                    "id": "first_vote",
                    "label": "First final vote",
                    "timeOrHeight": event_times["first_vote"],
                    "time": event_times["first_vote"],
                    "summary": "Earliest final voter transaction in the saved last-vote-wins set.",
                    "confidence": "high",
                },
                {
                    "id": "last_vote",
                    "label": "Last final vote",
                    "timeOrHeight": event_times["last_vote"],
                    "time": event_times["last_vote"],
                    "summary": "Latest final voter transaction in the saved last-vote-wins set.",
                    "confidence": "high",
                },
            ]
        )
    for event in event_timeline:
        event["time"] = event.get("time") or event_times.get(event["id"], "")

    tally_by_option = []
    vote_counts = Counter(vote["primaryOption"] for vote in votes)
    recipient_power = defaultdict(float)
    for vote in votes:
        if vote["isRecipient"]:
            recipient_power[vote["primaryOption"]] += vote.get("votingPower") or 0
    for option in vote_options:
        power = summary["finalTally"].get(option, 0)
        tally_by_option.append(
            {
                "voteOption": option,
                "votingPower": power,
                "addressCount": vote_counts.get(option, 0),
                "recipientVotingPower": round(recipient_power.get(option, 0), 6),
            }
        )

    return {
        "voteMatrixPower": vote_matrix,
        "compensationComponents": compensation_components,
        "participantEpochTimeline": build_participant_epoch_timeline(recipients, votes),
        "timingLeads": sorted(timing_leads, key=lambda row: (-row["anomalyScore"], -row["e287Weight"], row["address"])),
        "eventTimeline": event_timeline,
        "tallyByOption": tally_by_option,
        "epochTotals": epochs,
    }


def build_telegram_attribution_audit(recipients, votes, evidence_claims):
    recipient_by_address = {row["address"]: row for row in recipients}
    vote_by_address = {row["voter"]: row for row in votes}
    relevant_addresses = sorted(set(recipient_by_address) | set(vote_by_address))
    telegram_claims = [
        claim
        for claim in evidence_claims
        if claim.get("address") in relevant_addresses and claim.get("sourceType", "").startswith("telegram_")
    ]
    priority = {
        "telegram_self_or_team_claim": 0,
        "telegram_operator_statement": 1,
        "telegram_owner_inquiry": 2,
        "telegram_address_context": 3,
        "telegram_export_excerpt": 4,
    }
    rows = []
    for claim in sorted(
        telegram_claims,
        key=lambda row: (
            row["address"],
            priority.get(row.get("sourceType", ""), 9),
            {"high": 0, "medium": 1, "low": 2}.get(row.get("confidence", ""), 3),
            row.get("sourceValue", ""),
        ),
    ):
        address = claim["address"]
        recipient = recipient_by_address.get(address, {})
        vote = vote_by_address.get(address, {})
        roles = []
        if recipient:
            roles.append("recipient")
        if vote:
            roles.append("voter")
        rows.append(
            {
                "address": address,
                "label": recipient.get("label") or vote.get("label") or "Unknown public owner",
                "publicLabel": recipient.get("publicLabel") or vote.get("publicLabel") or recipient.get("label") or vote.get("label") or "",
                "roles": roles,
                "totalCompensationGonka": round(recipient.get("totalGonka") or 0, 6),
                "voteOption": vote.get("primaryOption") or recipient.get("voteOption") or "did_not_vote",
                "votingPower": round(vote.get("votingPower") or 0, 6),
                "sourceType": claim.get("sourceType", ""),
                "subject": claim.get("subject", ""),
                "confidence": claim.get("confidence", ""),
                "isAttributionProof": claim.get("isAttributionProof", False),
                "sourceUrl": claim.get("sourceUrl", ""),
                "sourceValue": claim.get("sourceValue", ""),
                "caveat": claim.get("caveat", ""),
            }
        )
    return rows


def write_telegram_attribution_report(rows):
    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)
    with (reports / "telegram_attribution_audit.csv").open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "address",
                "label",
                "publicLabel",
                "roles",
                "totalCompensationGonka",
                "voteOption",
                "votingPower",
                "sourceType",
                "subject",
                "confidence",
                "isAttributionProof",
                "sourceUrl",
                "sourceValue",
                "caveat",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({**row, "roles": " ".join(row["roles"])})

    self_or_operator = [row for row in rows if row["sourceType"] in {"telegram_self_or_team_claim", "telegram_operator_statement"}]
    high_confidence = [row for row in self_or_operator if row["confidence"] == "high"]
    medium_leads = [row for row in self_or_operator if row["confidence"] == "medium"]
    with (reports / "telegram_attribution_audit.md").open("w") as f:
        f.write("# Telegram Attribution Audit\n\n")
        f.write("Local Telegram exports are used as investigation context only. Explicit high-confidence self/operator statements can label dashboard rows. Medium leads are shown with a question mark and remain non-public signals unless corroborated by linkable public evidence.\n\n")
        f.write(f"- Proposal/voter Telegram evidence rows: {len(rows)}\n")
        f.write(f"- Self/operator rows: {len(self_or_operator)}\n")
        f.write(f"- High-confidence self/operator rows: {len(high_confidence)}\n")
        f.write(f"- Medium self/operator leads: {len(medium_leads)}\n\n")
        for row in rows:
            f.write(f"## {row['label']}\n\n")
            f.write(f"- Address: `{row['address']}`\n")
            f.write(f"- Roles: {', '.join(row['roles']) or 'context only'}; vote: {row['voteOption']}; voting power: {row['votingPower']}; compensation: {row['totalCompensationGonka']} GONKA\n")
            f.write(f"- Telegram signal: {row['sourceType']} ({row['confidence']}, {'proof' if row['isAttributionProof'] else 'signal'}) by {row['subject']}\n")
            f.write(f"- Source: {row['sourceUrl']}\n")
            f.write(f"- Excerpt: {row['sourceValue']}\n")
            f.write(f"- Caveat: {row['caveat']}\n\n")


def write_voting_power_window_report(voting_power_window):
    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)
    rows = voting_power_window.get("rows") or []
    summary = voting_power_window.get("summary") or {}
    with (reports / "voting_power_window_comparison.csv").open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "voter",
                "label",
                "primaryOption",
                "height",
                "isRecipient",
                "startVotingPower",
                "endVotingPower",
                "windowPowerStatus",
                "startVotingPowerSource",
                "endVotingPowerSource",
                "startDelegationCount",
                "endDelegationCount",
                "txHash",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in writer.fieldnames})

    zero_both = [row for row in rows if row["windowPowerStatus"] == "zero_at_start_and_end"]
    start_only = [row for row in rows if row["windowPowerStatus"] == "power_at_start_only"]
    end_only = [row for row in rows if row["windowPowerStatus"] == "power_at_end_only"]
    with (reports / "voting_power_window_comparison.md").open("w") as f:
        f.write("# Voting Power Window Comparison\n\n")
        f.write("This report reconciles final proposal #67 voters against archive staking/delegation snapshots at the governance voting start and voting end boundaries. It does not use inference epoch weights as governance voting power.\n\n")
        f.write(f"- Voting start: {summary.get('votingStartTime', '')}; last block before/start boundary: {summary.get('lastBlockBeforeVotingStart', {}).get('height', '')}\n")
        f.write(f"- Voting end: {summary.get('votingEndTime', '')}; last block before/end boundary: {summary.get('lastBlockBeforeVotingEnd', {}).get('height', '')}\n")
        f.write(f"- On-chain vote records before start: {summary.get('decodedGovVotesBeforeStartCount', 0)}; before end: {summary.get('decodedGovVotesBeforeEndCount', 0)}\n")
        f.write(f"- Voters with non-zero power at start/end: {summary.get('votersWithStartVotingPowerCount', 0)} / {summary.get('votersWithEndVotingPowerCount', 0)}\n")
        f.write(f"- Zero at both boundaries: {len(zero_both)}; power at start only: {len(start_only)}; power at end only: {len(end_only)}\n")
        f.write(f"- End-window chain-like tally matches final tally: {summary.get('chainLikeTallyMatchesFinalTally', False)}\n\n")
        f.write("## Non-stable Voting Power Rows\n\n")
        for row in start_only + end_only + zero_both:
            f.write(f"- {row['label']} `{row['voter']}`: vote={row['primaryOption']} tx_height={row['height']} start_power={row['startVotingPower']} end_power={row['endVotingPower']} status={row['windowPowerStatus']}\n")


def write_attribution_reports(ranked_parties, evidence_claims, epoch_entry_exit_clusters=None, interest_clusters=None, benefit_power_matrix=None, public_name_enrichment=None, epoch_anomalies=None):
    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)

    with (reports / "ranked_parties.csv").open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "rank",
                "label",
                "addresses",
                "roles",
                "total_gonka",
                "overall_priority",
                "confidence",
                "identity_score",
                "benefit_score",
                "governance_score",
                "coordination_score",
                "telegram_score",
                "operational_timing_score",
                "inference_vote_overlap_score",
                "proposal_role_score",
                "caveats",
            ],
        )
        writer.writeheader()
        for row in ranked_parties:
            scores = row["scoreComponents"]
            writer.writerow(
                {
                    "rank": row["rank"],
                    "label": row["label"],
                    "addresses": " ".join(row["addresses"]),
                    "roles": " ".join(row["roles"]),
                    "total_gonka": row["totalCompensationGonka"],
                    "overall_priority": row["overallPriority"],
                    "confidence": row["confidence"],
                    "identity_score": scores["identityConfidence"],
                    "benefit_score": scores["benefit"],
                    "governance_score": scores["governance"],
                    "coordination_score": scores["coordination"],
                    "telegram_score": scores.get("telegramAttribution", 0),
                    "operational_timing_score": scores.get("operationalTiming", scores.get("epochAnomaly", 0)),
                    "inference_vote_overlap_score": scores.get("inferenceVoteOverlap", scores.get("voteTiming", 0)),
                    "proposal_role_score": scores.get("proposalRole", 0),
                    "caveats": " | ".join(row["caveats"]),
                }
            )

    with (reports / "evidence_claims.csv").open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "address",
                "subject",
                "category",
                "source_type",
                "source_value",
                "confidence",
                "is_attribution_proof",
                "source_file",
                "source_url",
                "caveat",
            ],
        )
        writer.writeheader()
        for row in evidence_claims:
            writer.writerow(
                {
                    "address": row["address"],
                    "subject": row["subject"],
                    "category": row["category"],
                    "source_type": row["sourceType"],
                    "source_value": row["sourceValue"],
                    "confidence": row["confidence"],
                    "is_attribution_proof": row["isAttributionProof"],
                    "source_file": row["sourceFile"],
                    "source_url": row["sourceUrl"],
                    "caveat": row["caveat"],
                }
            )

    if public_name_enrichment is not None:
        with (reports / "public_name_enrichment.csv").open("w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "address",
                    "label",
                    "best_public_name",
                    "roles",
                    "total_compensation_gonka",
                    "voting_power",
                    "vote_option",
                    "evidence_boundary",
                    "gns_names",
                    "reverse_gns_names",
                    "validator_operator_address",
                    "validator_moniker",
                    "validator_website",
                    "validator_identity",
                    "validator_security_contact",
                    "inference_url",
                    "public_name_sources",
                    "next_actions",
                ],
            )
            writer.writeheader()
            for row in public_name_enrichment["rows"]:
                writer.writerow(
                    {
                        "address": row["address"],
                        "label": row["label"],
                        "best_public_name": row["bestPublicName"],
                        "roles": " ".join(row["roles"]),
                        "total_compensation_gonka": row["totalCompensationGonka"],
                        "voting_power": row["votingPower"],
                        "vote_option": row["voteOption"],
                        "evidence_boundary": row["evidenceBoundary"],
                        "gns_names": " ".join(row["gnsNames"]),
                        "reverse_gns_names": " ".join(row["reverseGnsNames"]),
                        "validator_operator_address": row["validatorOperatorAddress"],
                        "validator_moniker": row["validatorMoniker"],
                        "validator_website": row["validatorWebsite"],
                        "validator_identity": row["validatorIdentity"],
                        "validator_security_contact": row["validatorSecurityContact"],
                        "inference_url": row["inferenceUrl"],
                        "public_name_sources": " | ".join(f"{item['sourceType']}:{item['value']}:{item['confidence']}" for item in row["publicNameSources"]),
                        "next_actions": " | ".join(row["nextActions"]),
                    }
                )

        with (reports / "public_name_groups.csv").open("w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "source_type",
                    "value",
                    "confidence",
                    "is_attribution_proof",
                    "addresses",
                    "address_count",
                    "total_compensation_gonka",
                    "total_voting_power",
                    "vote_power_by_option",
                    "source_file",
                ],
            )
            writer.writeheader()
            for row in public_name_enrichment["groups"]:
                writer.writerow(
                    {
                        "source_type": row["sourceType"],
                        "value": row["value"],
                        "confidence": row["confidence"],
                        "is_attribution_proof": row["isAttributionProof"],
                        "addresses": " ".join(row["addresses"]),
                        "address_count": len(row["addresses"]),
                        "total_compensation_gonka": row["totalCompensationGonka"],
                        "total_voting_power": row["totalVotingPower"],
                        "vote_power_by_option": " ".join(f"{option}:{power}" for option, power in row["votePowerByOption"].items()),
                        "source_file": row["sourceFile"],
                    }
                )

        summary = public_name_enrichment["summary"]
        lines = [
            "# Proposal 67 Public Name Enrichment",
            "",
            "This report normalizes public naming sources for proposal #67 addresses. It uses saved snapshots only: GNS `.gnk` contract state, validator metadata, participant inference URLs, and previously built evidence claims. A public name is an attribution lead unless `evidence_boundary` is `public_owner_proof`.",
            "",
            "## Summary",
            "",
            f"- Proposal addresses reviewed: {summary['proposalAddressCount']}",
            f"- Proposal addresses with any public name/metadata signal: {summary['proposalAddressesWithAnyPublicName']}",
            f"- Proposal addresses with public owner proof: {summary['proposalAddressesWithPublicOwnerProof']}",
            f"- Proposal addresses with GNS names: {summary['proposalAddressesWithGns']} ({summary['proposalAddressesWithReverseGns']} reverse)",
            f"- Saved GNS snapshot: {summary['gnsSnapshotNameCount']} names across {summary['gnsSnapshotAddressCount']} addresses",
            f"- Public name/source groups in proposal set: {summary['publicNameGroupCount']}; multi-address groups: {summary['publicNameGroupsWithMultipleProposalAddresses']}",
            "",
            "## Proposal Addresses With Public Names",
            "",
        ]
        named_rows = [row for row in public_name_enrichment["rows"] if row["publicNameSources"]]
        for row in named_rows[:60]:
            lines.extend(
                [
                    f"### {row['label']}",
                    "",
                    f"- Address: `{row['address']}`",
                    f"- Roles: {', '.join(row['roles'])}; compensation: {row['totalCompensationGonka']} GONKA; voting power: {row['votingPower']}; vote: {row['voteOption']}",
                    f"- Best public name: {row['bestPublicName'] or 'none'}",
                    f"- Evidence boundary: {row['evidenceBoundary']}",
                    f"- GNS: {', '.join(row['gnsNames']) or 'none'}; reverse: {', '.join(row['reverseGnsNames']) or 'none'}",
                    f"- Validator: {row['validatorMoniker'] or 'none'} | {row['validatorWebsite'] or 'no website'} | identity {row['validatorIdentity'] or 'none'} | contact {row['validatorSecurityContact'] or 'none'}",
                    f"- Inference URL: {row['inferenceUrl'] or 'none'}",
                    f"- Next actions: {' | '.join(row['nextActions'])}",
                    "",
                ]
            )
            lines.append("Public sources:")
            for source in row["publicNameSources"][:8]:
                proof = "proof" if source["isAttributionProof"] else "signal"
                lines.append(f"- {source['sourceType']} ({source['confidence']}, {proof}): {source['value']}")
            lines.append("")

        lines.extend(["## Shared Public Name/Metadata Groups", ""])
        for row in public_name_enrichment["groups"][:40]:
            proof = "proof" if row["isAttributionProof"] else "signal"
            lines.extend(
                [
                    f"### {row['sourceType']}: {row['value']}",
                    "",
                    f"- Boundary: {row['confidence']} {proof}; addresses: {len(row['addresses'])}",
                    f"- Compensation: {row['totalCompensationGonka']} GONKA; voting power: {row['totalVotingPower']}",
                    f"- Vote power: {', '.join(f'{option}={power}' for option, power in row['votePowerByOption'].items()) or 'none'}",
                    f"- Addresses: {' '.join(row['addresses'])}",
                    f"- Source file: {row['sourceFile']}",
                    "",
                ]
            )

        unknown_rows = [row for row in public_name_enrichment["rows"] if row["evidenceBoundary"] == "unknown_public_owner"]
        lines.extend(["## Still Missing Public Names", ""])
        for row in sorted(unknown_rows, key=lambda item: (-item["votingPower"], -item["totalCompensationGonka"], item["address"]))[:40]:
            lines.append(f"- `{row['address']}` {row['label']} | roles={','.join(row['roles'])} | comp={row['totalCompensationGonka']} | power={row['votingPower']} | actions={' | '.join(row['nextActions'])}")

        (reports / "public_name_enrichment.md").write_text("\n".join(lines).rstrip() + "\n")

    if benefit_power_matrix is not None:
        with (reports / "benefit_power_matrix.csv").open("w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "rank",
                    "address",
                    "label",
                    "is_recipient",
                    "is_voter",
                    "recipient_voter_overlap",
                    "total_compensation_gonka",
                    "voting_power",
                    "vote_option",
                    "cluster_id",
                    "cluster_kind",
                    "evidence_boundary",
                    "proof_count",
                    "high_confidence_claim_count",
                    "triage_score",
                    "next_actions",
                    "top_evidence",
                ],
            )
            writer.writeheader()
            for row in benefit_power_matrix:
                writer.writerow(
                    {
                        "rank": row["rank"],
                        "address": row["address"],
                        "label": row["label"],
                        "is_recipient": row["isRecipient"],
                        "is_voter": row["isVoter"],
                        "recipient_voter_overlap": row["recipientVoterOverlap"],
                        "total_compensation_gonka": row["totalCompensationGonka"],
                        "voting_power": row["votingPower"],
                        "vote_option": row["voteOption"],
                        "cluster_id": row["clusterId"],
                        "cluster_kind": row["clusterKind"],
                        "evidence_boundary": row["evidenceBoundary"],
                        "proof_count": row["proofCount"],
                        "high_confidence_claim_count": row["highConfidenceClaimCount"],
                        "triage_score": row["triageScore"],
                        "next_actions": " | ".join(row["nextActions"]),
                        "top_evidence": " | ".join(f"{item['sourceType']}:{item['sourceValue']}:{item['confidence']}" for item in row["topEvidence"]),
                    }
                )

        lines = [
            "# Proposal 67 Benefit + Governance Power Matrix",
            "",
            "This report ranks addresses by combined compensation benefit, exact archive-derived governance voting power, recipient-voter overlap, and public evidence boundary. It is a triage queue: `public_owner_proof` is stronger attribution; URL/IP-only labels remain investigation leads.",
            "",
            "## Highest Priority Rows",
            "",
        ]
        for row in benefit_power_matrix[:35]:
            lines.extend(
                [
                    f"### #{row['rank']} {row['label']}",
                    "",
                    f"- Address: `{row['address']}`",
                    f"- Compensation: {row['totalCompensationGonka']} GONKA; governance power: {row['votingPower']}; vote: {row['voteOption']}",
                    f"- Recipient: {row['isRecipient']}; voter: {row['isVoter']}; overlap: {row['recipientVoterOverlap']}",
                    f"- Cluster: {row['clusterId'] or 'none'} ({row['clusterKind'] or 'none'})",
                    f"- Evidence boundary: {row['evidenceBoundary']} (proof {row['proofCount']}, high-confidence claims {row['highConfidenceClaimCount']})",
                    f"- Triage score: {row['triageScore']}",
                    f"- Next actions: {' | '.join(row['nextActions'])}",
                    "",
                ]
            )
            if row["topEvidence"]:
                lines.append("Top evidence:")
                for item in row["topEvidence"]:
                    proof = "proof" if item["isAttributionProof"] else "signal"
                    lines.append(f"- {item['sourceType']} ({item['confidence']}, {proof}): {item['sourceValue']}")
                lines.append("")
        (reports / "benefit_power_matrix.md").write_text("\n".join(lines).rstrip() + "\n")

    if interest_clusters is not None:
        with (reports / "interest_clusters.csv").open("w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "rank",
                    "cluster_id",
                    "kind",
                    "label",
                    "addresses",
                    "roles",
                    "recipient_count",
                    "voter_count",
                    "recipient_voter_count",
                    "total_compensation_gonka",
                    "total_voting_power",
                    "vote_power_by_option",
                    "vote_address_counts",
                    "evidence_boundary",
                    "interest_score",
                    "top_evidence",
                    "caveats",
                ],
            )
            writer.writeheader()
            for row in interest_clusters:
                writer.writerow(
                    {
                        "rank": row["rank"],
                        "cluster_id": row["id"],
                        "kind": row["kind"],
                        "label": row["label"],
                        "addresses": " ".join(row["addresses"]),
                        "roles": " ".join(row["roles"]),
                        "recipient_count": row["recipientCount"],
                        "voter_count": row["voterCount"],
                        "recipient_voter_count": row["recipientVoterCount"],
                        "total_compensation_gonka": row["totalCompensationGonka"],
                        "total_voting_power": row["totalVotingPower"],
                        "vote_power_by_option": " ".join(f"{option}:{power}" for option, power in row["votePowerByOption"].items()),
                        "vote_address_counts": " ".join(f"{option}:{count}" for option, count in row["voteAddressCounts"].items()),
                        "evidence_boundary": row["evidenceBoundary"],
                        "interest_score": row["interestScore"],
                        "top_evidence": " | ".join(f"{item['sourceType']}:{item['sourceValue']}:{item['confidence']}" for item in row["topEvidence"]),
                        "caveats": " | ".join(row["caveats"]),
                    }
                )

        lines = [
            "# Proposal 67 Interest Clusters",
            "",
            "Clusters combine compensation, exact archive-derived governance voting power, vote direction, and public evidence boundaries. `public_owner_proof` clusters are stronger; `infrastructure_or_public_signal` and `shared_public_label_only` clusters are investigation leads and must not be treated as ownership proof by themselves.",
            "",
        ]
        for row in interest_clusters[:30]:
            lines.extend(
                [
                    f"## #{row['rank']} {row['label']}",
                    "",
                    f"- Cluster: {row['id']} ({row['kind']}; {row['evidenceBoundary']})",
                    f"- Addresses: {' '.join(row['addresses'])}",
                    f"- Roles: {', '.join(row['roles']) or 'none'}",
                    f"- Compensation: {row['totalCompensationGonka']} GONKA across {row['recipientCount']} recipients",
                    f"- Exact governance voting power: {row['totalVotingPower']} across {row['voterCount']} voters",
                    f"- Vote power split: {', '.join(f'{option}={power}' for option, power in row['votePowerByOption'].items()) or 'none'}",
                    f"- Recipient-voter overlap: {row['recipientVoterCount']}",
                    f"- Interest score: {row['interestScore']}",
                    f"- Caveats: {' | '.join(row['caveats']) if row['caveats'] else 'none'}",
                    "",
                ]
            )
            if row["topEvidence"]:
                lines.append("Top evidence:")
                for item in row["topEvidence"][:5]:
                    proof = "proof" if item["isAttributionProof"] else "signal"
                    lines.append(f"- {item['address']} {item['sourceType']} ({item['confidence']}, {proof}): {item['sourceValue']}")
                lines.append("")
        (reports / "interest_clusters.md").write_text("\n".join(lines).rstrip() + "\n")

    if epoch_entry_exit_clusters is not None:
        with (reports / "epoch_entry_exit_clusters.csv").open("w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "rank",
                    "cluster_id",
                    "kind",
                    "label",
                    "addresses",
                    "total_e287_weight",
                    "max_e287_weight",
                    "entered_count",
                    "voted_during_count",
                    "exited_count",
                    "confirmed_enter_vote_exit_count",
                    "confirmed_enter_vote_exit_with_power_count",
                    "recipient_count",
                    "total_compensation_gonka",
                    "total_governance_voting_power",
                    "vote_power_by_option",
                    "vote_counts",
                    "top_evidence",
                    "caveats",
                ],
            )
            writer.writeheader()
            for row in epoch_entry_exit_clusters:
                writer.writerow(
                    {
                        "rank": row["rank"],
                        "cluster_id": row["id"],
                        "kind": row["kind"],
                        "label": row["label"],
                        "addresses": " ".join(row["addresses"]),
                        "total_e287_weight": row["totalE287Weight"],
                        "max_e287_weight": row["maxE287Weight"],
                        "entered_count": row["enteredCount"],
                        "voted_during_count": row["votedDuringCount"],
                        "exited_count": row["exitedCount"],
                        "confirmed_enter_vote_exit_count": row["confirmedEnterVoteExitCount"],
                        "confirmed_enter_vote_exit_with_power_count": row["confirmedEnterVoteExitWithPowerCount"],
                        "recipient_count": row["recipientCount"],
                        "total_compensation_gonka": row["totalCompensationGonka"],
                        "total_governance_voting_power": row["totalGovernanceVotingPower"],
                        "vote_power_by_option": " ".join(f"{option}:{power}" for option, power in row["votePowerByOption"].items()),
                        "vote_counts": " ".join(f"{option}:{count}" for option, count in row["voteCounts"].items()),
                        "top_evidence": " | ".join(f"{item['sourceType']}:{item['sourceValue']}:{item['confidence']}" for item in row["topEvidence"]),
                        "caveats": " | ".join(row["caveats"]),
                    }
                )

        lines = [
            "# Proposal 67 e287 Inference Timing Clusters",
            "",
            "This report groups voting-end inference epoch timing signals only when multiple addresses share strict public identity or signal-cluster evidence. Single-address timing cases remain timing leads, not clusters. Inference epoch weight is not governance voting power; a cluster is an investigation lead, not owner attribution unless the evidence is explicitly marked as public proof.",
            "",
        ]
        for row in epoch_entry_exit_clusters[:25]:
            lines.extend(
                [
                    f"## #{row['rank']} {row['label']}",
                    "",
                    f"- Cluster: {row['id']} ({row['kind']})",
                    f"- Addresses: {' '.join(row['addresses'])}",
                    f"- e287 inference weight: total {row['totalE287Weight']}, max {row['maxE287Weight']}",
                    f"- Inference enter / governance vote tx during e287 / inference exit counts: {row['enteredCount']} / {row['votedDuringCount']} / {row['exitedCount']}",
                    f"- Full operational enter-vote-exit signals: {row['confirmedEnterVoteExitCount']}",
                    f"- Full operational enter-vote-exit signals with non-zero governance power: {row['confirmedEnterVoteExitWithPowerCount']}",
                    f"- Exact governance voting power in cluster: {row['totalGovernanceVotingPower']} ({', '.join(f'{option}={power}' for option, power in row['votePowerByOption'].items()) or 'none'})",
                    f"- Recipients: {row['recipientCount']}; compensation: {row['totalCompensationGonka']} GONKA",
                    f"- Votes: {', '.join(f'{option}={count}' for option, count in row['voteCounts'].items()) or 'none'}",
                    f"- Caveats: {' | '.join(row['caveats'])}",
                    "",
                ]
            )
            if row["topEvidence"]:
                lines.append("Top evidence:")
                for item in row["topEvidence"][:5]:
                    proof = "proof" if item["isAttributionProof"] else "signal"
                    lines.append(f"- {item['address']} {item['sourceType']} ({item['confidence']}, {proof}): {item['sourceValue']}")
                lines.append("")
        (reports / "epoch_entry_exit_clusters.md").write_text("\n".join(lines).rstrip() + "\n")

        cluster_by_address = {}
        for cluster in epoch_entry_exit_clusters:
            for address in cluster.get("addresses", []):
                cluster_by_address[address] = cluster
        reconciliation_rows = []
        for row in epoch_anomalies or []:
            cluster = cluster_by_address.get(row["address"], {})
            reconciliation_rows.append(
                {
                    "rank": cluster.get("rank", ""),
                    "cluster_id": cluster.get("id", "single-address timing lead"),
                    "cluster_label": cluster.get("label", ""),
                    "address": row["address"],
                    "label": row["label"],
                    "entered_e287": row["enteredE287"],
                    "voted_during_e287": row["votedDuringE287"],
                    "exited_after_e287": row["exitedAfterE287"],
                    "full_enter_vote_exit": row["enteredE287"] and row["votedDuringE287"] and row["exitedAfterE287"],
                    "e287_weight": row["e287Weight"],
                    "prev_max_weight": row["prevMaxWeight"],
                    "next_max_weight": row["nextMaxWeight"],
                    "vote_option": row["voteOption"],
                    "vote_height": row["voteHeight"],
                    "governance_voting_power": row.get("governanceVotingPower", 0),
                    "governance_voting_power_source": row.get("governanceVotingPowerSource", ""),
                    "is_recipient": row["isRecipient"],
                    "total_compensation_gonka": row.get("totalCompensationGonka", 0),
                    "status": row["status"],
                }
            )
        reconciliation_rows.sort(
            key=lambda row: (
                not row["full_enter_vote_exit"],
                -float(row["governance_voting_power"] or 0),
                -int(row["e287_weight"] or 0),
                row["address"],
            )
        )
        with (reports / "voting_window_power_reconciliation.csv").open("w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "rank",
                    "cluster_id",
                    "cluster_label",
                    "address",
                    "label",
                    "entered_e287",
                    "voted_during_e287",
                    "exited_after_e287",
                    "full_enter_vote_exit",
                    "e287_weight",
                    "prev_max_weight",
                    "next_max_weight",
                    "vote_option",
                    "vote_height",
                    "governance_voting_power",
                    "governance_voting_power_source",
                    "is_recipient",
                    "total_compensation_gonka",
                    "status",
                ],
            )
            writer.writeheader()
            writer.writerows(reconciliation_rows)

        full_with_power = [row for row in reconciliation_rows if row["full_enter_vote_exit"] and row["governance_voting_power"]]
        timing_voted_with_power = [row for row in reconciliation_rows if row["voted_during_e287"] and row["governance_voting_power"]]
        timing_voted_zero_power = [row for row in reconciliation_rows if row["voted_during_e287"] and not row["governance_voting_power"]]
        lines = [
            "# Proposal 67 Voting-Window Power Reconciliation",
            "",
            "This report reconciles e287 inference timing signals with exact archive-derived governance voting power. Inference epoch weight is operational timing evidence only; counted governance influence is the archive staking/delegation voting power.",
            "",
            f"- e287 timing rows: {len(reconciliation_rows)}",
            f"- Voted during e287 with non-zero governance power: {len(timing_voted_with_power)}",
            f"- Voted during e287 with zero governance power: {len(timing_voted_zero_power)}",
            f"- Full enter-vote-exit rows with non-zero governance power: {len(full_with_power)}",
            "",
        ]
        if full_with_power:
            lines.append("## Full Enter-Vote-Exit With Power")
            lines.append("")
            for row in full_with_power[:25]:
                lines.extend(
                    [
                        f"### {row['label']}",
                        "",
                        f"- Address: {row['address']}",
                        f"- Cluster: {row['cluster_id']} ({row['cluster_label']})",
                        f"- e287 inference weight: {row['e287_weight']} (prev max {row['prev_max_weight']}, next max {row['next_max_weight']})",
                        f"- Vote: {row['vote_option']} at height {row['vote_height']}",
                        f"- Exact governance voting power: {row['governance_voting_power']} ({row['governance_voting_power_source']})",
                        f"- Recipient: {row['is_recipient']}; compensation: {row['total_compensation_gonka']} GONKA",
                        "",
                    ]
                )
        else:
            lines.extend(
                [
                    "## Full Enter-Vote-Exit With Power",
                    "",
                    "No row currently satisfies all three operational conditions (entered e287, voted during e287, exited after e287) while also having non-zero archive governance voting power.",
                    "",
                ]
            )
        lines.append("## Voted During e287 With Power")
        lines.append("")
        for row in timing_voted_with_power[:30]:
            lines.append(
                f"- {row['label']} `{row['address']}`: vote={row['vote_option']} power={row['governance_voting_power']} e287_weight={row['e287_weight']} entered={row['entered_e287']} exited={row['exited_after_e287']}"
            )
        if not timing_voted_with_power:
            lines.append("- none")
        lines.append("")
        (reports / "voting_window_power_reconciliation.md").write_text("\n".join(lines).rstrip() + "\n")

    lines = [
        "# Proposal 67 Attribution Audit",
        "",
        "This report ranks interested parties from committed public snapshots. It is not a legal accusation; weak infrastructure signals are explicitly separated from owner attribution proof.",
        "",
        "## Top Ranked Parties",
        "",
    ]
    for row in ranked_parties[:20]:
        scores = row["scoreComponents"]
        lines.extend(
            [
                f"### #{row['rank']} {row['label']}",
                "",
                f"- Addresses: {' '.join(row['addresses'])}",
                f"- Roles: {', '.join(row['roles'])}",
                f"- Total compensation: {row['totalCompensationGonka']} GONKA",
                f"- Overall priority: {row['overallPriority']} (identity {scores['identityConfidence']}, benefit {scores['benefit']}, governance {scores['governance']}, coordination {scores['coordination']}, telegram {scores.get('telegramAttribution', 0)}, proposal {scores.get('proposalRole', 0)}); operational priority {row.get('operationalPriority', row['overallPriority'])} (inference timing {scores.get('operationalTiming', scores.get('epochAnomaly', 0))}, inference/vote overlap {scores.get('inferenceVoteOverlap', scores.get('voteTiming', 0))})",
                f"- Confidence: {row['confidence']}",
                f"- Caveats: {' | '.join(row['caveats']) if row['caveats'] else 'none'}",
                "",
            ]
        )
        if row["topEvidence"]:
            lines.append("Top evidence:")
            for claim in row["topEvidence"]:
                proof = "proof" if claim["isAttributionProof"] else "signal"
                lines.append(f"- {claim['sourceType']} ({claim['confidence']}, {proof}): {claim['sourceValue']}")
            lines.append("")

    (reports / "attribution_audit.md").write_text("\n".join(lines).rstrip() + "\n")


def main():
    DOCS_DATA.mkdir(parents=True, exist_ok=True)
    recipients_raw = read_aggregate_compensation()
    proposal, outputs = read_proposal()
    participants, account_labels, consensus_labels, consensus_metadata, gns_by_address, evidence_by_address = read_public_metadata()
    all_votes, final_votes = read_votes()
    onchain_graph = read_onchain_graph_snapshot()
    osint_sources = read_public_osint_sources()
    telegram_evidence = read_telegram_evidence()
    voting_end_epochs = read_voting_end_epochs()
    governance_power_evidence = read_governance_power_evidence()

    recipient_set = {row["address"] for row in recipients_raw}
    output_total = sum(outputs.values(), Decimal(0))
    aggregate_total = sum(row["total"] for row in recipients_raw)
    attack_total = sum(row["attack"] for row in recipients_raw)
    cap_total = sum(row["cap"] for row in recipients_raw)
    epoch_summary = build_epoch_summary(recipients_raw, aggregate_total)

    missing_outputs = sorted(recipient_set - set(outputs))
    extra_outputs = sorted(set(outputs) - recipient_set)
    mismatched_outputs = []
    for row in recipients_raw:
        delta = abs(outputs.get(row["address"], Decimal(0)) - row["total"])
        if delta > Decimal("0.00001"):
            mismatched_outputs.append({"address": row["address"], "delta": as_float(delta)})

    if missing_outputs or extra_outputs or mismatched_outputs:
        raise SystemExit(
            "Proposal outputs do not match aggregate compensation: "
            f"missing={missing_outputs}, extra={extra_outputs}, mismatched={mismatched_outputs[:5]}"
        )
    if abs(quantize(aggregate_total, "0.01") - EXPECTED_TOTAL) > ROUND_TOLERANCE:
        raise SystemExit(f"Unexpected compensation total: {aggregate_total}")

    final_tally = proposal["final_tally_result"]
    final_vote_counts = Counter()
    recipient_vote_counts = Counter()
    for vote in final_votes:
        primary = max(vote["options"], key=lambda item: item["weight"])["option"]
        final_vote_counts[primary] += 1
        if vote["voter"] in recipient_set:
            recipient_vote_counts[primary] += 1

    votes_by_address = {vote["voter"]: vote for vote in final_votes}
    recipients = []
    for rank, row in enumerate(recipients_raw, start=1):
        participant = participants.get(row["address"]) or {}
        evidence_rows = evidence_by_address.get(row["address"], [])
        per_epoch = {epoch_key: as_float(value) for epoch_key, value in row["per_epoch"].items()}
        active = participant.get("status") == "ACTIVE" if isinstance(participant, dict) else False
        public_name = public_label(row["address"], participant, account_labels, consensus_labels, gns_by_address)
        recipients.append(
            {
                "rank": rank,
                "address": row["address"],
                "label": display_label(row["address"], public_name),
                "publicLabel": public_name,
                "gnsNames": gns_by_address.get(row["address"], []),
                "publicNodeInfo": public_node_info(participant, consensus_metadata),
                "inferenceUrl": participant.get("inference_url", "") if isinstance(participant, dict) else "",
                "status": participant.get("status", "UNKNOWN") if isinstance(participant, dict) else "UNKNOWN",
                "activeNode": active,
                "epochsCompleted": participant.get("epochs_completed") if isinstance(participant, dict) else None,
                "totalGonka": as_float(row["total"]),
                "attackE265E266Gonka": as_float(row["attack"]),
                "capE267E276Gonka": as_float(row["cap"]),
                "perEpoch": per_epoch,
                "onchainOutputGonka": as_float(outputs[row["address"]]),
                "componentSource": "mixed" if row["attack"] and row["cap"] else ("attack_e265_e266" if row["attack"] else "cap_e267_e276"),
                "voteOption": max(votes_by_address[row["address"]]["options"], key=lambda item: item["weight"])["option"]
                if row["address"] in votes_by_address
                else "did_not_vote",
                "identityType": primary_identity_type(evidence_rows),
            }
        )

    governance_power_by_voter = {row["voter"]: row for row in governance_power_evidence.get("perVoterPower", [])}
    governance_power_window_by_voter = {row["voter"]: row for row in governance_power_evidence.get("windowVoterPower", [])}
    governance_power_summary = governance_power_evidence.get("summary", {})
    votes = []
    for vote in final_votes:
        participant = participants.get(vote["voter"]) or {}
        evidence_rows = evidence_by_address.get(vote["voter"], [])
        governance_power = governance_power_by_voter.get(vote["voter"], {})
        governance_window = governance_power_window_by_voter.get(vote["voter"], {})
        public_name = public_label(vote["voter"], participant, account_labels, consensus_labels, gns_by_address)
        votes.append(
            {
                "voter": vote["voter"],
                "label": display_label(vote["voter"], public_name),
                "publicLabel": public_name,
                "gnsNames": gns_by_address.get(vote["voter"], []),
                "publicNodeInfo": public_node_info(participant, consensus_metadata),
                "isRecipient": vote["voter"] in recipient_set,
                "finalVoteOptions": vote["options"],
                "primaryOption": max(vote["options"], key=lambda item: item["weight"])["option"],
                "txHash": vote["txHash"],
                "height": vote["height"],
                "blockTime": vote.get("blockTime", ""),
                "votingPower": governance_power.get("votingPower"),
                "votingPowerSource": governance_power.get("votingPowerSource", "unknown"),
                "votingPowerReason": governance_power.get("reason", governance_power_summary.get("perVoterPowerReason", "")),
                "startVotingPower": governance_window.get("startVotingPower"),
                "endVotingPower": governance_window.get("endVotingPower", governance_power.get("votingPower")),
                "windowPowerStatus": governance_window.get("windowPowerStatus", ""),
                "identityType": primary_identity_type(evidence_rows),
            }
        )

    relevant_addresses = recipient_set | {vote["voter"] for vote in final_votes}
    identity_evidence = sorted(
        [item for address, rows in evidence_by_address.items() if address in relevant_addresses for item in rows],
        key=lambda row: (row["address"], row["sourceType"], row["sourceValue"]),
    )
    identity_graph = build_identity_graph(recipients, votes, identity_evidence, gns_by_address)
    strict_cluster_by_address = {
        address: cluster["id"]
        for cluster in identity_graph["strictClusters"]
        for address in cluster["addresses"]
    }
    signal_cluster_by_address = {
        address: cluster["id"]
        for cluster in identity_graph["signalClusters"]
        for address in cluster["addresses"]
    }
    for row in recipients:
        row["strictClusterId"] = strict_cluster_by_address.get(row["address"], "")
        row["signalClusterId"] = signal_cluster_by_address.get(row["address"], "")
    for row in votes:
        row["strictClusterId"] = strict_cluster_by_address.get(row["voter"], "")
        row["signalClusterId"] = signal_cluster_by_address.get(row["voter"], "")

    labels_by_address, identity_types_by_address = collect_address_labels(
        recipients,
        votes,
        participants,
        account_labels,
        consensus_labels,
        gns_by_address,
    )
    epoch_anomalies = build_epoch_anomalies(votes, recipients, labels_by_address)
    evidence_claims = build_evidence_claims(proposal, recipients, votes, identity_evidence, identity_graph, onchain_graph, osint_sources, telegram_evidence, epoch_anomalies)
    apply_investigation_labels(recipients, votes, evidence_claims)
    labels_by_address, identity_types_by_address = collect_address_labels(
        recipients,
        votes,
        participants,
        account_labels,
        consensus_labels,
        gns_by_address,
    )
    actors = build_actors(proposal, recipients, votes, identity_graph, onchain_graph, labels_by_address, identity_types_by_address)
    epoch_anomalies = build_epoch_anomalies(votes, recipients, labels_by_address)
    evidence_claims = build_evidence_claims(proposal, recipients, votes, identity_evidence, identity_graph, onchain_graph, osint_sources, telegram_evidence, epoch_anomalies)
    epoch_anomalies = build_epoch_anomalies(votes, recipients, labels_by_address)
    evidence_claims = build_evidence_claims(proposal, recipients, votes, identity_evidence, identity_graph, onchain_graph, osint_sources, telegram_evidence, epoch_anomalies)
    claims_by_address = defaultdict(list)
    for claim in evidence_claims:
        if claim.get("address"):
            claims_by_address[claim["address"]].append(claim)
    row_by_address = {row["address"]: row for row in actors}
    for row in recipients:
        row_by_address[row["address"]] = {**row_by_address.get(row["address"], {}), **row}
    for row in votes:
        row_by_address[row["voter"]] = {**row_by_address.get(row["voter"], {}), **row, "address": row["voter"]}
    canonical_actors = [
        canonical_actor_for_address(address, row, claims_by_address.get(address, []))
        for address, row in sorted(row_by_address.items())
    ]
    canonical_by_address = {row["address"]: row for row in canonical_actors}
    apply_canonical_actor_fields(recipients, "address", canonical_by_address)
    apply_canonical_actor_fields(votes, "voter", canonical_by_address)
    apply_canonical_actor_fields(actors, "address", canonical_by_address)
    epoch_entry_exit_clusters = build_epoch_entry_exit_clusters(epoch_anomalies, recipients, votes, identity_graph, evidence_claims)
    ranked_parties = build_ranked_parties(actors, evidence_claims, identity_graph)
    interest_clusters = build_interest_clusters(actors, evidence_claims, identity_graph)
    benefit_power_matrix = build_benefit_power_matrix(recipients, votes, interest_clusters, evidence_claims)
    voting_power_window = build_voting_power_window(votes, governance_power_evidence)
    public_name_enrichment = build_public_name_enrichment(recipients, votes, identity_evidence, evidence_claims, gns_by_address)
    telegram_attribution_audit = build_telegram_attribution_audit(recipients, votes, evidence_claims)
    attack_narrative = build_attack_narrative(proposal, votes, epoch_summary, epoch_anomalies)
    hypotheses = build_hypotheses(ranked_parties, epoch_anomalies, telegram_evidence, proposal)
    (DATA / "public_name_enrichment.json").write_text(json.dumps(public_name_enrichment, indent=2, sort_keys=True) + "\n")
    write_attribution_reports(ranked_parties, evidence_claims, epoch_entry_exit_clusters, interest_clusters, benefit_power_matrix, public_name_enrichment, epoch_anomalies)
    write_telegram_attribution_report(telegram_attribution_audit)
    write_voting_power_window_report(voting_power_window)

    dashboard_summary = {
        "totalCompensationGonka": as_float(aggregate_total),
        "proposalOutputTotalGonka": as_float(output_total),
        "recipientsCount": len(recipients),
        "finalTally": {
            "yes": int(final_tally["yes_count"]),
            "no": int(final_tally["no_count"]),
            "abstain": int(final_tally["abstain_count"]),
            "no_with_veto": int(final_tally["no_with_veto_count"]),
        },
        "attackE265E266Gonka": as_float(attack_total),
        "capE267E276Gonka": as_float(cap_total),
        "epochCount": len(epoch_summary),
        "visibleDamageE265Gonka": as_float(VISIBLE_DAMAGE_E265),
        "visibleDamageToFinalMultiplier": as_float(aggregate_total / VISIBLE_DAMAGE_E265),
        "voteTransactionsCount": len(all_votes),
        "uniqueVotersCount": len(final_votes),
        "recipientVotersCount": sum(1 for vote in final_votes if vote["voter"] in recipient_set),
        "nonRecipientVotersCount": sum(1 for vote in final_votes if vote["voter"] not in recipient_set),
        "recipientsWithGnsNamesCount": sum(1 for row in recipients if row["gnsNames"]),
        "votersWithGnsNamesCount": sum(1 for row in votes if row["gnsNames"]),
        "addressesWithGnsNamesInSnapshot": len(gns_by_address),
        "identityGraphEntitiesCount": len(identity_graph["entities"]),
        "identityGraphEdgesCount": len(identity_graph["edges"]),
        "strictClustersCount": len(identity_graph["strictClusters"]),
        "signalClustersCount": len(identity_graph["signalClusters"]),
        "actorsCount": len(actors),
        "evidenceClaimsCount": len(evidence_claims),
        "rankedPartiesCount": len(ranked_parties),
        "interestClustersCount": len(interest_clusters),
        "canonicalActorsCount": len(canonical_actors),
        "interestClustersWithVotingPowerCount": sum(1 for row in interest_clusters if row["totalVotingPower"] > 0),
        "interestClustersWithCompensationAndVotingPowerCount": sum(1 for row in interest_clusters if row["totalVotingPower"] > 0 and row["totalCompensationGonka"] > 0),
        "benefitPowerMatrixCount": len(benefit_power_matrix),
        "benefitPowerOverlapCount": sum(1 for row in benefit_power_matrix if row["recipientVoterOverlap"]),
        "benefitPowerPublicProofOverlapCount": sum(1 for row in benefit_power_matrix if row["recipientVoterOverlap"] and row["evidenceBoundary"] == "public_owner_proof"),
        "publicNameEnrichmentAddressCount": public_name_enrichment["summary"]["proposalAddressCount"],
        "publicNameEnrichmentSignalCount": public_name_enrichment["summary"]["proposalAddressesWithAnyPublicName"],
        "publicNameEnrichmentOwnerProofCount": public_name_enrichment["summary"]["proposalAddressesWithPublicOwnerProof"],
        "publicNameEnrichmentGnsCount": public_name_enrichment["summary"]["proposalAddressesWithGns"],
        "publicNameEnrichmentGroupCount": public_name_enrichment["summary"]["publicNameGroupCount"],
        "publicNameEnrichmentMultiAddressGroupCount": public_name_enrichment["summary"]["publicNameGroupsWithMultipleProposalAddresses"],
        "publicSocialCandidateCount": len(osint_sources.get("publicSocialCandidates") or []),
        "telegramEvidenceCount": len(telegram_evidence.get("messages") or []),
        "epochAnomaliesCount": len(epoch_anomalies),
        "epochEntryExitClusterCount": len(epoch_entry_exit_clusters),
        "votingEndEpochSnapshotCount": len(voting_end_epochs.get("epochs") or []),
        "governanceArchiveVotesCount": governance_power_summary.get("decodedGovVotesCount", 0),
        "governanceArchiveTallyMatchesFinal": governance_power_summary.get("decodedTallyMatchesFinalTally", False),
        "governancePerVoterPowerStatus": governance_power_summary.get("perVoterPowerStatus", "unknown"),
        "votingStartLastBlockBefore": governance_power_summary.get("lastBlockBeforeVotingStart", {}),
        "votingStartFirstBlockAfter": governance_power_summary.get("firstBlockAfterVotingStart", {}),
        "votingEndLastBlockBefore": governance_power_summary.get("lastBlockBeforeVotingEnd", {}),
        "votingEndFirstBlockAfter": governance_power_summary.get("firstBlockAfterVotingEnd", {}),
        "votersWithStartVotingPowerCount": governance_power_summary.get("votersWithStartVotingPowerCount", 0),
        "votersWithEndVotingPowerCount": governance_power_summary.get("votersWithEndVotingPowerCount", 0),
        "votersZeroAtStartAndEndCount": governance_power_summary.get("votersZeroAtStartAndEndCount", 0),
        "votersPowerAtStartOnlyCount": governance_power_summary.get("votersPowerAtStartOnlyCount", 0),
        "votersPowerAtEndOnlyCount": governance_power_summary.get("votersPowerAtEndOnlyCount", 0),
        "finalVoteAddressCounts": dict(final_vote_counts),
        "recipientVoteAddressCounts": dict(recipient_vote_counts),
        "grcOffchainVote": {"include": 2, "exclude": 6, "abstain": 1, "votersIdentified": False},
    }
    chart_data = build_dashboard_chart_data(proposal, recipients, votes, epoch_summary, epoch_anomalies, dashboard_summary, attack_narrative)

    dashboard = {
        "metadata": {
            "generatedFrom": "committed snapshots",
            "sourceRepository": "https://github.com/votkon/gonka-kimi-restitution",
            "proposalMetadata": proposal.get("metadata", ""),
            "gnsContract": "gonka1rd582xazhyxde68g099ed0zpjzq0j0shnhkegg06s8009h7lnxjqvyf0qf",
            "proposalId": proposal["id"],
            "title": proposal["title"],
            "status": proposal["status"],
            "votingStartTime": proposal["voting_start_time"],
            "votingEndTime": proposal["voting_end_time"],
        },
        "summary": dashboard_summary,
        "chartData": chart_data,
        "recipients": recipients,
        "votes": votes,
        "voteTimeline": votes,
        "epochs": epoch_summary,
        "identityEvidence": identity_evidence,
        "identityGraph": identity_graph,
        "canonicalActors": canonical_actors,
        "actors": actors,
        "evidenceClaims": evidence_claims,
        "rankedParties": ranked_parties,
        "interestClusters": interest_clusters,
        "benefitPowerMatrix": benefit_power_matrix,
        "votingPowerWindow": voting_power_window,
        "publicNameEnrichment": public_name_enrichment,
        "telegramAttributionAudit": telegram_attribution_audit,
        "telegramEvidence": telegram_evidence.get("messages") or [],
        "epochAnomalies": epoch_anomalies,
        "epochEntryExitClusters": epoch_entry_exit_clusters,
        "governancePowerEvidence": governance_power_evidence,
        "methodology": {
            "governanceVoteRule": "A vote is evidenced by an on-chain governance vote transaction for proposal #67. A prior vote remains part of the saved vote set unless superseded by a later vote from the same voter under last-vote-wins consolidation.",
            "governanceVotingPowerRule": "Per-voter governance voting power is not inferred from inference epochs. It is computed from archive staking Query/Validators and Query/DelegatorDelegations at the last pre-end block using Gonka SDK gov tally logic; the truncated decimal result must match the final on-chain TallyResult.",
            "governanceVotingWindowRule": "Zero-power voters are still real on-chain governance voters. The dashboard compares archive staking/delegation power at the voting-start boundary and the voting-end boundary; the final tally is governed by the end-window chain-like power, while the start-window view is a reconciliation check.",
            "inferenceEpochRule": "e287 validation_weights are inference/epoch participation weights. They are operational timing signals only and are not used as governance voting power.",
            "recipientConflictRule": "Recipient-voter conflict is based on address overlap between compensation outputs and final on-chain governance voters; it does not imply the compensation amount affected vote weight.",
            "identityRule": "Public attribution requires public validator/GNS/metadata/source evidence. Infrastructure, Telegram, and inference timing remain signals unless independently corroborated.",
        },
        "hypotheses": hypotheses,
        "attackNarrative": attack_narrative,
        "notes": [
            "Per-voter voting power is computed from archive staking validators and delegations at the last pre-end block; the truncated chain-like result matches the final aggregate on-chain tally.",
            "Voting-power charts use archive-derived per-voter power where available and final aggregate on-chain tally for the proposal-level result.",
            "Inference epoch weights are not governance voting power and are not used for tally or per-voter power claims.",
            "A governance vote transaction can be included even if the same address is not active in a later inference epoch; vote inclusion must be checked through governance data, not inference participation.",
            "GRC off-chain voters are not identified in the upstream repository.",
            "Identity labels come from public validator metadata, validator-key matches, GNS .gnk names, or participant inference URLs.",
            "GNS .gnk names are read from the saved on-chain CosmWasm contract state snapshot.",
            "Public-social OSINT is limited to linkable public sources such as Gonka names, GitHub, public websites, GNS records, and public profile URLs.",
            "Ranked parties are prioritized interested-party leads, not legal accusations.",
            "Telegram evidence contains short excerpts from local exports selected by address/URL/username matches; full exports remain ignored under history/.",
            "Voting-end epoch anomalies are operational timing signals and not ownership proof by themselves.",
            "Node ownership clues include public validator moniker, website, identity, security contact, details, and participant inference URL when present.",
            "Strict clusters use only high-confidence public attribution evidence; signal clusters may include infrastructure clues such as shared host, IP, RDAP organization, or TLS certificate.",
        ],
    }

    json_payload = json.dumps(dashboard, indent=2, sort_keys=True)
    (DOCS_DATA / "dashboard.json").write_text(json_payload + "\n")
    (DOCS_DATA / "dashboard.js").write_text("window.DASHBOARD_DATA = " + json_payload + ";\n")
    print(f"Wrote {DOCS_DATA / 'dashboard.json'}")
    print(f"Recipients: {len(recipients)}; voters: {len(votes)}; total: {aggregate_total:.6f} GONKA")


if __name__ == "__main__":
    main()
