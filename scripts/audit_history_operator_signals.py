#!/usr/bin/env python3
import csv
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HISTORY = ROOT / "history"
DATA = ROOT / "data"
DOCS_DATA = ROOT / "docs" / "data"
REPORTS = ROOT / "reports"
OUT_JSON = DATA / "investigations" / "history_operator_signal_audit.json"

ADDRESS_RE = re.compile(r"\bgonka1[0-9a-z]{38}\b")
VALOPER_RE = re.compile(r"\bgonkavaloper1[0-9a-z]{38}\b")
FORMULA_RE = re.compile(r"\bformula\s*x\b|formulax|formulaxpool", re.IGNORECASE)
RAZUM_RE = re.compile(r"Razum_Dmitriy|Разум|Razum|Dmitriy\s+Razum", re.IGNORECASE)
MESSAGE_SPLIT_RE = re.compile(r'(?=<div class="message[^"]*"[^>]*id="message\d+")')


def load_json(path, default):
    if not path.exists():
        return default
    with path.open() as f:
        return json.load(f)


def account_from_valoper(value):
    if value.startswith("gonkavaloper"):
        return "gonka" + value[len("gonkavaloper") :]
    return value


def tag_text(block, class_name):
    match = re.search(rf'<div class="{re.escape(class_name)}"[^>]*>(.*?)</div>', block, re.DOTALL)
    if not match:
        return ""
    return clean_html(match.group(1))


def clean_html(value):
    value = re.sub(r"<br\s*/?>", "\n", value, flags=re.IGNORECASE)
    value = re.sub(r"<[^>]+>", "", value)
    value = html.unescape(value)
    value = re.sub(r"[ \t\r\f\v]+", " ", value)
    value = re.sub(r"\n\s+", "\n", value)
    return value.strip()


def message_time(block):
    match = re.search(r'<div class="pull_right date details" title="([^"]+)"', block)
    return html.unescape(match.group(1)).strip() if match else ""


def message_id(block):
    match = re.search(r'id="(message\d+)"', block)
    return match.group(1) if match else ""


def relevant_addresses():
    dashboard = load_json(DOCS_DATA / "dashboard.json", {})
    addresses = set()
    for key in ["recipients", "votes", "actors"]:
        for row in dashboard.get(key, []) or []:
            address = row.get("address") or row.get("voter")
            if address:
                addresses.add(address)
    for cluster_key in ["strictClusters", "signalClusters"]:
        for row in (dashboard.get("identityGraph", {}) or {}).get(cluster_key, []) or []:
            addresses.update(row.get("addresses") or [])
    return addresses


def address_metadata():
    dashboard = load_json(DOCS_DATA / "dashboard.json", {})
    participants = load_json(DATA / "participants_by_address.json", {})
    validators = load_json(DATA / "validators.json", {"validators": []}).get("validators", [])
    metadata = {}

    def ensure(address):
        metadata.setdefault(
            address,
            {
                "address": address,
                "currentLabel": address,
                "roles": set(),
                "totalCompensationGonka": 0,
                "votingPower": 0,
                "inferenceUrl": "",
                "validatorKey": "",
                "matchedValidator": "",
            },
        )
        return metadata[address]

    for row in dashboard.get("recipients", []) or []:
        item = ensure(row["address"])
        item["roles"].add("recipient")
        item["currentLabel"] = row.get("label") or item["currentLabel"]
        item["totalCompensationGonka"] = row.get("totalGonka") or 0
        item["inferenceUrl"] = row.get("inferenceUrl") or item["inferenceUrl"]
        item["validatorKey"] = (row.get("publicNodeInfo") or {}).get("validatorKey", item["validatorKey"])
        item["matchedValidator"] = ((row.get("publicNodeInfo") or {}).get("matchedValidator") or {}).get("operatorAddress", "")
    for row in dashboard.get("votes", []) or []:
        item = ensure(row["voter"])
        item["roles"].add("voter")
        item["currentLabel"] = row.get("label") or item["currentLabel"]
        item["votingPower"] = row.get("votingPower") or 0
    for address, participant in participants.items():
        if not isinstance(participant, dict) or participant.get("error"):
            continue
        item = ensure(address)
        item["inferenceUrl"] = participant.get("inference_url") or item["inferenceUrl"]
        item["validatorKey"] = participant.get("validator_key") or item["validatorKey"]
    for validator in validators:
        account = account_from_valoper(validator.get("operator_address", ""))
        if not account:
            continue
        item = ensure(account)
        desc = validator.get("description", {})
        if desc.get("moniker"):
            item["currentLabel"] = desc["moniker"]
        item["matchedValidator"] = validator.get("operator_address", "")
    return metadata


def message_blocks(path):
    text = path.read_text(errors="replace")
    chunks = MESSAGE_SPLIT_RE.split(text)
    for chunk in chunks:
        if 'class="message' not in chunk:
            continue
        end = chunk.find('<div class="message', 1)
        block = chunk[:end] if end != -1 else chunk
        if "from_name" in block or 'class="text"' in block:
            yield block


def audit_messages():
    relevant = relevant_addresses()
    metadata = address_metadata()
    rows = []

    for path in sorted(HISTORY.glob("**/*.html")):
        if "/photos/" in str(path):
            continue
        try:
            blocks = list(message_blocks(path))
        except OSError:
            continue
        for block in blocks:
            text = tag_text(block, "text")
            if not text:
                continue
            addresses = set(ADDRESS_RE.findall(text))
            addresses.update(account_from_valoper(item) for item in VALOPER_RE.findall(text))
            addresses = {address for address in addresses if address in relevant}
            if not addresses:
                continue

            formula_hit = FORMULA_RE.search(text)
            razum_hit = RAZUM_RE.search(text)
            if not formula_hit and not razum_hit:
                continue

            if len(addresses) > 1:
                scoped_addresses = set()
                for line in text.splitlines():
                    if not FORMULA_RE.search(line) and not RAZUM_RE.search(line):
                        continue
                    scoped_addresses.update(ADDRESS_RE.findall(line))
                    scoped_addresses.update(account_from_valoper(item) for item in VALOPER_RE.findall(line))
                addresses = {address for address in scoped_addresses if address in relevant}
                if not addresses:
                    continue

            source_type = "telegram_operator_context"
            subject = "Formula X" if formula_hit else "Razum_Dmitriy"
            if formula_hit and razum_hit:
                subject = "Formula X / Razum_Dmitriy"
            confidence = "medium"
            caveat = "Local Telegram history links this address to an operator/pool context; this is not public owner proof."
            if formula_hit and "ваша нода" in text.lower():
                caveat = "Telegram message explicitly says the address appears to be that operator's node; still not public owner proof without corroboration."

            for address in sorted(addresses):
                item = metadata.get(address, {"currentLabel": address, "roles": set()})
                rows.append(
                    {
                        "address": address,
                        "currentLabel": item.get("currentLabel", address),
                        "operatorSignalLabel": "Formula X" if formula_hit else "Razum_Dmitriy",
                        "subject": subject,
                        "sourceType": source_type,
                        "confidence": confidence,
                        "isAttributionProof": False,
                        "sourceFile": str(path.relative_to(ROOT)),
                        "messageId": message_id(block),
                        "messageTime": message_time(block),
                        "author": tag_text(block, "from_name"),
                        "roles": " ".join(sorted(item.get("roles") or [])),
                        "totalCompensationGonka": item.get("totalCompensationGonka", 0),
                        "votingPower": item.get("votingPower", 0),
                        "inferenceUrl": item.get("inferenceUrl", ""),
                        "validatorKey": item.get("validatorKey", ""),
                        "matchedValidator": item.get("matchedValidator", ""),
                        "excerpt": text[:1200],
                        "caveat": caveat,
                    }
                )

    deduped = {}
    for row in rows:
        key = (row["address"], row["operatorSignalLabel"], row["sourceFile"], row["messageId"], row["excerpt"])
        deduped[key] = row
    return sorted(deduped.values(), key=lambda row: (row["operatorSignalLabel"], row["address"], row["sourceFile"], row["messageId"]))


def write_outputs(rows):
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(exist_ok=True)
    payload = {
        "metadata": {
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "source": "history/**/*.html",
            "description": "Operator/pool attribution leads from local Telegram history exports. These are non-proof signals unless corroborated.",
        },
        "rows": rows,
        "summary": {
            "rows": len(rows),
            "addresses": len({row["address"] for row in rows}),
            "formulaXRows": sum(1 for row in rows if row["operatorSignalLabel"] == "Formula X"),
            "formulaXAddresses": len({row["address"] for row in rows if row["operatorSignalLabel"] == "Formula X"}),
        },
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    fields = [
        "address",
        "currentLabel",
        "operatorSignalLabel",
        "subject",
        "sourceType",
        "confidence",
        "isAttributionProof",
        "sourceFile",
        "messageId",
        "messageTime",
        "author",
        "roles",
        "totalCompensationGonka",
        "votingPower",
        "inferenceUrl",
        "validatorKey",
        "matchedValidator",
        "excerpt",
        "caveat",
    ]
    with (REPORTS / "history_operator_signal_audit.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})

    with (REPORTS / "history_operator_signal_audit.md").open("w") as f:
        f.write("# History Operator Signal Audit\n\n")
        f.write("Local Telegram exports are investigation context only. These rows can label dashboard operator-signal candidates, but they are not public owner proof.\n\n")
        f.write(f"- Rows: {payload['summary']['rows']}\n")
        f.write(f"- Addresses: {payload['summary']['addresses']}\n")
        f.write(f"- Formula X rows: {payload['summary']['formulaXRows']}\n")
        f.write(f"- Formula X addresses: {payload['summary']['formulaXAddresses']}\n\n")
        for row in rows:
            f.write(f"## {row['operatorSignalLabel']} candidate: `{row['address']}`\n\n")
            f.write(f"- Current label: {row['currentLabel']}\n")
            f.write(f"- Roles: {row['roles'] or 'context only'}; compensation: {row['totalCompensationGonka']} GONKA; voting power: {row['votingPower']}\n")
            f.write(f"- Source: `{row['sourceFile']}` {row['messageId']} {row['messageTime']}\n")
            f.write(f"- Author: {row['author'] or 'unknown'}\n")
            f.write(f"- Signal: {row['sourceType']} ({row['confidence']}, signal)\n")
            f.write(f"- Excerpt: {row['excerpt']}\n")
            f.write(f"- Caveat: {row['caveat']}\n\n")


def main():
    rows = audit_messages()
    write_outputs(rows)
    print(json.dumps({"rows": len(rows), "addresses": len({row["address"] for row in rows})}, sort_keys=True))


if __name__ == "__main__":
    main()
