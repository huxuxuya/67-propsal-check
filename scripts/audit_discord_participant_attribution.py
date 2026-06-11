#!/usr/bin/env python3
import csv
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from audit_chat_participant_attribution import (
    AMBIGUOUS_NODE_SET_RE,
    DATA,
    DOCS_DATA,
    FORMULA_RE,
    LEVEL_PRIORITY,
    OPERATOR_OWNERSHIP_RE,
    OWNER_INQUIRY_RE,
    POOL_ROSTER_RE,
    REPORTS,
    ROOT,
    SELF_CLAIM_RE,
    account_from_valoper,
    best_candidate,
    clean_text,
    excerpt,
    load_json,
    relevant_metadata,
)


DISCORD_EVIDENCE = DATA / "discord_evidence.json"
OUT_JSON = DATA / "investigations" / "discord_participant_attribution.json"

DELEGATION_RE = re.compile(r"set-poc-delegation|\b(delegat|delegate|delegated|делегировать|делегаци)\w*", re.IGNORECASE)
HOST_RE = re.compile(r"\b(host|hosting|validator|operator|node|нода|валидатор|оператор|хост)\b", re.IGNORECASE)
DISCORD_SELF_CLAIM_RE = re.compile(
    r"\b(my|our|one)\s+(node|validator|wallet|address)\s+(is|are|:)|"
    r"\bi\s+have\s+.{0,80}(node|validator|wallet|address|unclaimed rewards)|"
    r"\bмоя|мой|наш|наша\b.{0,80}\b(нода|адрес|кошелек|валидатор)\b",
    re.IGNORECASE,
)


def load_discord_messages():
    payload = load_json(DISCORD_EVIDENCE, {"messages": []})
    return payload.get("messages") or []


def classify_candidate(message, context_kind, candidate_label):
    text = message.get("text", "")
    if context_kind != "same_message" and AMBIGUOUS_NODE_SET_RE.search(text):
        return "weak_context", "discord_ambiguous_node_set", "low"
    if SELF_CLAIM_RE.search(text) or DISCORD_SELF_CLAIM_RE.search(text):
        return "strong_local_operator_signal", "discord_self_claim", "high"
    if OPERATOR_OWNERSHIP_RE.search(text):
        return "strong_local_operator_signal", "discord_operator_statement", "high"
    if HOST_RE.search(text):
        return "weak_context", "discord_operator_context", "medium"
    if DELEGATION_RE.search(text):
        return "weak_context", "discord_delegation_target", "medium"
    if FORMULA_RE.search(text) and ("your node" in text.lower() or "ваш" in text.lower()):
        return "medium_operator_context", "discord_operator_context", "medium"
    if POOL_ROSTER_RE.search(text) and candidate_label:
        return "medium_operator_context", "discord_pool_roster", "medium"
    if OWNER_INQUIRY_RE.search(text):
        return "weak_context", "discord_owner_inquiry", "low"
    return "weak_context", "discord_context_only", "medium"


def candidate_label_for(message):
    text = message.get("text", "")
    if FORMULA_RE.search(text):
        return "Formula X"
    match = POOL_ROSTER_RE.search(text)
    if match:
        return clean_text(match.group(0))
    if SELF_CLAIM_RE.search(text) or DISCORD_SELF_CLAIM_RE.search(text) or OPERATOR_OWNERSHIP_RE.search(text):
        return message.get("author") or message.get("authorUsername") or ""
    return ""


def add_candidate(candidates, address, message, context_kind):
    label = candidate_label_for(message)
    level, source_type, confidence = classify_candidate(message, context_kind, label)
    row = {
        "address": address,
        "bestChatCandidateLabel": label,
        "evidenceLevel": level,
        "sourceType": source_type,
        "confidence": confidence,
        "isAttributionProof": False,
        "platform": "discord",
        "chat": message.get("chat", ""),
        "channelId": message.get("channelId", ""),
        "messageId": message.get("messageId", ""),
        "messageTime": message.get("date", ""),
        "author": message.get("author", ""),
        "authorUsername": message.get("authorUsername", ""),
        "authorUserId": message.get("authorUserId", ""),
        "authorSource": message.get("authorSource", ""),
        "contextKind": context_kind,
        "replyToMessageId": message.get("replyToMessageId", ""),
        "sourceFile": message.get("sourceFile", ""),
        "sourceUrl": message.get("sourceUrl", ""),
        "excerpt": excerpt(message.get("text", "")),
        "replyText": excerpt(message.get("replyText", ""), 260),
        "urls": message.get("urls", []),
        "ips": message.get("ips", []),
        "caveat": "Local Discord chat signal; not public owner proof without independent corroboration.",
    }
    candidates[address].append(row)


def build_audit():
    metadata = relevant_metadata()
    relevant = set(metadata)
    messages = load_discord_messages()
    by_message_id = {message.get("messageId"): message for message in messages if message.get("messageId")}
    candidates = defaultdict(list)
    for message in messages:
        direct_addresses = {account_from_valoper(addr) for addr in message.get("addresses", [])} & relevant
        for address in direct_addresses:
            add_candidate(candidates, address, message, "same_message")
        reply_id = message.get("replyToMessageId")
        if reply_id and (SELF_CLAIM_RE.search(message.get("text", "")) or HOST_RE.search(message.get("text", ""))):
            parent = by_message_id.get(reply_id)
            if parent:
                parent_addresses = {account_from_valoper(addr) for addr in parent.get("addresses", [])} & relevant
                for address in parent_addresses:
                    add_candidate(candidates, address, message, "reply_parent")

    rows = []
    for address, meta in sorted(metadata.items()):
        best = best_candidate(candidates[address])
        evidence_level = best.get("evidenceLevel", "no_chat_signal")
        if meta.get("publicProof"):
            evidence_level = "public_owner_proof"
        rows.append(
            {
                **meta,
                "evidenceLevel": evidence_level,
                "bestChatCandidateLabel": best.get("bestChatCandidateLabel", ""),
                "sourceType": best.get("sourceType", "no_chat_signal"),
                "confidence": best.get("confidence", ""),
                "isAttributionProof": False,
                "platform": "discord",
                "chat": best.get("chat", ""),
                "channelId": best.get("channelId", ""),
                "messageId": best.get("messageId", ""),
                "messageTime": best.get("messageTime", ""),
                "author": best.get("author", ""),
                "authorUsername": best.get("authorUsername", ""),
                "authorUserId": best.get("authorUserId", ""),
                "authorSource": best.get("authorSource", ""),
                "contextKind": best.get("contextKind", ""),
                "replyToMessageId": best.get("replyToMessageId", ""),
                "sourceFile": best.get("sourceFile", ""),
                "sourceUrl": best.get("sourceUrl", ""),
                "excerpt": best.get("excerpt", ""),
                "replyText": best.get("replyText", ""),
                "urls": best.get("urls", []),
                "ips": best.get("ips", []),
                "caveat": best.get("caveat", "No relevant local Discord signal found."),
                "allCandidateCount": len(candidates[address]),
            }
        )
    return rows


def write_outputs(rows):
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(exist_ok=True)
    summary = {
        "rows": len(rows),
        "addresses": len({row["address"] for row in rows}),
        "publicOwnerProofRows": sum(1 for row in rows if row["evidenceLevel"] == "public_owner_proof"),
        "strongLocalOperatorRows": sum(1 for row in rows if row["evidenceLevel"] == "strong_local_operator_signal"),
        "mediumOperatorContextRows": sum(1 for row in rows if row["evidenceLevel"] == "medium_operator_context"),
        "weakContextRows": sum(1 for row in rows if row["evidenceLevel"] == "weak_context"),
        "noChatSignalRows": sum(1 for row in rows if row["evidenceLevel"] == "no_chat_signal"),
    }
    payload = {
        "metadata": {
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "source": "history/export-gonka-full/*.html",
            "description": "Structured local Discord attribution audit for proposal participants. Chat-only rows are not public owner proof.",
        },
        "summary": summary,
        "rows": rows,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n")

    fields = [
        "address",
        "currentLabel",
        "roles",
        "evidenceLevel",
        "bestChatCandidateLabel",
        "sourceType",
        "confidence",
        "chat",
        "messageId",
        "messageTime",
        "author",
        "authorUsername",
        "authorUserId",
        "contextKind",
        "sourceUrl",
        "allCandidateCount",
        "excerpt",
        "caveat",
    ]
    with (REPORTS / "discord_participant_attribution.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})
    with (REPORTS / "discord_participant_attribution.md").open("w") as f:
        f.write("# Discord Participant Attribution Audit\n\n")
        f.write("Local Discord logs are forensic context. A chat-only signal can identify an operator candidate, but it is not public owner proof without independent corroboration.\n\n")
        for key, value in summary.items():
            f.write(f"- {key}: {value}\n")
        f.write("\n")
        for row in rows:
            if row["evidenceLevel"] in {"no_chat_signal", "weak_context"} and row["allCandidateCount"] == 0:
                continue
            f.write(f"## {row['evidenceLevel']}: `{row['address']}`\n\n")
            f.write(f"- Current label: {row['currentLabel']}\n")
            f.write(f"- Discord candidate: {row['bestChatCandidateLabel'] or 'none'}; source: {row['sourceType']} ({row['confidence'] or 'none'})\n")
            if row["sourceFile"]:
                f.write(f"- Source: `{row['sourceFile']}` {row['messageId']} {row['messageTime']} by {row['author'] or row['authorUsername'] or 'unknown'}\n")
            if row["excerpt"]:
                f.write(f"- Excerpt: {row['excerpt']}\n")
            f.write(f"- Caveat: {row['caveat']}\n\n")


def main():
    rows = build_audit()
    write_outputs(rows)
    print(json.dumps({"rows": len(rows), "levels": {level: sum(1 for row in rows if row["evidenceLevel"] == level) for level in LEVEL_PRIORITY}}, sort_keys=True))


if __name__ == "__main__":
    main()
