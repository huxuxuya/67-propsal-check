#!/usr/bin/env python3
import csv
import json
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
    if address in account_labels:
        return account_labels[address]
    if isinstance(participant, dict):
        validator_key = participant.get("validator_key") or ""
        if validator_key in consensus_labels:
            return consensus_labels[validator_key]
    gns_name = preferred_gns_name(gns_by_address, address)
    if gns_name:
        return gns_name
    if isinstance(participant, dict):
        if participant.get("inference_url"):
            return participant["inference_url"]
    return "Unknown public owner"


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


def main():
    DOCS_DATA.mkdir(parents=True, exist_ok=True)
    recipients_raw = read_aggregate_compensation()
    proposal, outputs = read_proposal()
    participants, account_labels, consensus_labels, consensus_metadata, gns_by_address, evidence_by_address = read_public_metadata()
    all_votes, final_votes = read_votes()

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
        recipients.append(
            {
                "rank": rank,
                "address": row["address"],
                "label": public_label(row["address"], participant, account_labels, consensus_labels, gns_by_address),
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

    votes = []
    for vote in final_votes:
        participant = participants.get(vote["voter"]) or {}
        evidence_rows = evidence_by_address.get(vote["voter"], [])
        votes.append(
            {
                "voter": vote["voter"],
                "label": public_label(vote["voter"], participant, account_labels, consensus_labels, gns_by_address),
                "gnsNames": gns_by_address.get(vote["voter"], []),
                "publicNodeInfo": public_node_info(participant, consensus_metadata),
                "isRecipient": vote["voter"] in recipient_set,
                "finalVoteOptions": vote["options"],
                "primaryOption": max(vote["options"], key=lambda item: item["weight"])["option"],
                "txHash": vote["txHash"],
                "height": vote["height"],
                "votingPower": None,
                "votingPowerSource": "unknown",
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
        "summary": {
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
            "finalVoteAddressCounts": dict(final_vote_counts),
            "recipientVoteAddressCounts": dict(recipient_vote_counts),
            "grcOffchainVote": {"include": 2, "exclude": 6, "abstain": 1, "votersIdentified": False},
        },
        "recipients": recipients,
        "votes": votes,
        "voteTimeline": votes,
        "epochs": epoch_summary,
        "identityEvidence": identity_evidence,
        "identityGraph": identity_graph,
        "notes": [
            "Per-voter voting power is intentionally unknown because no exact public source is included in the snapshots.",
            "Voting-power charts use the final aggregate on-chain tally only.",
            "GRC off-chain voters are not identified in the upstream repository.",
            "Identity labels come from public validator metadata, validator-key matches, GNS .gnk names, or participant inference URLs.",
            "GNS .gnk names are read from the saved on-chain CosmWasm contract state snapshot.",
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
