#!/usr/bin/env python3
import csv
import html
import json
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parents[1]
HISTORY = ROOT / "history"
DATA = ROOT / "data"
DOCS_DATA = ROOT / "docs" / "data"
REPORTS = ROOT / "reports"
OUT_JSON = DATA / "investigations" / "chat_participant_attribution.json"

ADDRESS_RE = re.compile(r"\b(?:gonka1|gonkavaloper1)[0-9a-z]{38}\b")
USERNAME_RE = re.compile(r"(?<![A-Za-z0-9_])@[A-Za-z0-9_]{4,32}")
URL_RE = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)
IP_RE = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}(?::\d{2,5})?\b")

SELF_CLAIM_RE = re.compile(
    r"\b(моя|моей|мой|наша|нашей|наш|своей|свою)\s+(нода|ноде|ноду|node|узел|адрес|баланс)|"
    r"\bу\s+нас\s+на\s+gonka1|"
    r"\bмы\s+(хостим|послали|держим|подняли|запустили)|"
    r"\bэто\s+(кстати\s+)?моя\s+.*нода|"
    r"\bот\s+моего\s+адреса\b",
    re.IGNORECASE,
)
OPERATOR_RE = re.compile(
    r"set-poc-delegation|"
    r"\b(делегировать|заделегировать|делегировали|делегации|делегацию)\b|"
    r"\b(нашу|нашей)\s+.{0,80}(ноду|node)\b|"
    r"\b(будет|буду|можете|можно)\s+.{0,120}(запускать|делегировать|сюда|обн)|"
    r"\bтоп\s+1\s+сегмент\s+по\s+весу\b",
    re.IGNORECASE,
)
DELEGATION_RE = re.compile(
    r"set-poc-delegation|\b(делегировать|заделегировать|делегировали|делегации|делегацию)\b",
    re.IGNORECASE,
)
OPERATOR_OWNERSHIP_RE = re.compile(
    r"\b(нашу|нашей)\s+.{0,80}(ноду|node)\b|"
    r"\bмы\s+(хостим|держим|подняли|запустили)\b|"
    r"\b(он|она|мы|я)\s+.{0,120}(будет\s+запускать|буду\s+давать\s+обн|работает)|"
    r"\bтоп\s+1\s+сегмент\s+по\s+весу\b",
    re.IGNORECASE,
)
OWNER_INQUIRY_RE = re.compile(
    r"\b(чья|чей|чье|владелец|владельцев|owner|оунер|кто-то\s+знает|кто\s+знает)\b",
    re.IGNORECASE,
)
POOL_ROSTER_RE = re.compile(r"\b(formula\s*x|formulax|formulaxpool|ancapex|hyperfusion|gonka\s*top)\b", re.IGNORECASE)
FORMULA_RE = re.compile(r"\bformula\s*x\b|formulax|formulaxpool", re.IGNORECASE)
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


def clean_text(value):
    return html.unescape(re.sub(r"\s+", " ", value or "")).strip()


def parse_dt(value):
    if not value:
        return None
    for fmt in ("%d.%m.%Y %H:%M:%S UTC%z", "%d.%m.%Y %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def excerpt(value, max_len=700):
    value = clean_text(value)
    if len(value) <= max_len:
        return value
    return value[: max_len - 1].rstrip() + "..."


def source_url(source_file, message_id):
    if not source_file or not message_id:
        return source_file
    return f"{source_file}#{message_id}"


class TelegramHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.messages = []
        self.current = None
        self.stack = []
        self.in_from = False
        self.in_text = False
        self.in_reply = False
        self.in_forwarded = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = set((attrs.get("class") or "").split())
        self.stack.append((tag, classes))
        if tag == "div" and "message" in classes and "service" not in classes:
            self.current = {
                "messageId": attrs.get("id", ""),
                "author": "",
                "authorSource": "explicit",
                "date": "",
                "text": "",
                "replyText": "",
                "replyToMessageId": "",
                "forwardedFrom": "",
                "hrefs": [],
                "media": [],
            }
        if not self.current:
            return
        if tag == "div" and "from_name" in classes:
            self.in_from = True
        if tag == "div" and "text" in classes:
            self.in_text = True
        if tag == "div" and "reply_to" in classes:
            self.in_reply = True
        if tag == "div" and "forwarded" in classes:
            self.in_forwarded = True
        if tag == "div" and "date" in classes:
            self.current["date"] = attrs.get("title", "")
        if tag == "a":
            href = attrs.get("href", "")
            if href:
                self.current["hrefs"].append(href)
                reply_match = re.search(r"go_to_message(\d+)", href)
                if self.in_reply and reply_match:
                    self.current["replyToMessageId"] = f"message{reply_match.group(1)}"
        if tag in {"a", "img"}:
            media_href = attrs.get("href") or attrs.get("src") or ""
            if media_href and ("photo" in media_href or "video" in media_href):
                self.current["media"].append(media_href)

    def handle_endtag(self, tag):
        if self.current and tag == "div":
            classes = self.stack[-1][1] if self.stack else set()
            if "from_name" in classes:
                self.in_from = False
            if "text" in classes:
                self.in_text = False
            if "reply_to" in classes:
                self.in_reply = False
            if "forwarded" in classes:
                self.in_forwarded = False
            if "message" in classes:
                for key in ["author", "text", "replyText", "forwardedFrom"]:
                    self.current[key] = clean_text(self.current.get(key, ""))
                self.current["hrefs"] = sorted(set(self.current["hrefs"]))
                self.current["media"] = sorted(set(self.current["media"]))
                self.messages.append(self.current)
                self.current = None
                self.in_from = False
                self.in_text = False
                self.in_reply = False
                self.in_forwarded = False
        if self.stack:
            self.stack.pop()

    def handle_data(self, data):
        if not self.current:
            return
        if self.in_from:
            self.current["author"] += data
        elif self.in_text:
            self.current["text"] += data
        elif self.in_reply:
            self.current["replyText"] += data
        elif self.in_forwarded:
            self.current["forwardedFrom"] += data


def strip_html(value):
    value = re.sub(r"<br\s*/?>", "\n", value or "", flags=re.IGNORECASE)
    value = re.sub(r"<[^>]+>", "", value)
    value = html.unescape(value)
    value = re.sub(r"[ \t\r\f\v]+", " ", value)
    value = re.sub(r"\n\s+", "\n", value)
    return value.strip()


def div_text(block, class_name):
    match = re.search(rf'<div class="{re.escape(class_name)}"[^>]*>(.*?)</div>', block, re.DOTALL)
    return strip_html(match.group(1)) if match else ""


def parse_block(block, path):
    message_match = re.search(r'id="(message\d+)"', block)
    date_match = re.search(r'<div class="pull_right date details" title="([^"]+)"', block)
    reply_match = re.search(r"go_to_message(\d+)", block)
    hrefs = re.findall(r'href="([^"]+)"', block)
    media = [href for href in hrefs if "photo" in href or "video" in href]
    return {
        "messageId": message_match.group(1) if message_match else "",
        "author": div_text(block, "from_name"),
        "authorSource": "explicit",
        "date": html.unescape(date_match.group(1)).strip() if date_match else "",
        "text": div_text(block, "text"),
        "replyText": div_text(block, "reply_to details"),
        "replyToMessageId": f"message{reply_match.group(1)}" if reply_match else "",
        "forwardedFrom": div_text(block, "forwarded body"),
        "hrefs": sorted(set(hrefs)),
        "media": sorted(set(media)),
        "chat": path.parent.name,
        "sourceFile": str(path.relative_to(ROOT)),
    }


def parse_file(path):
    text = path.read_text(errors="replace")
    messages = []
    for chunk in MESSAGE_SPLIT_RE.split(text):
        if 'class="message' not in chunk:
            continue
        end = chunk.find('<div class="message', 1)
        block = chunk[:end] if end != -1 else chunk
        if "from_name" not in block and 'class="text"' not in block:
            continue
        messages.append(parse_block(block, path))
    last_author = ""
    for message in messages:
        if message["author"]:
            last_author = message["author"]
            message["authorSource"] = "explicit"
        elif last_author:
            message["author"] = last_author
            message["authorSource"] = "inherited_previous_message"
        else:
            message["authorSource"] = "missing"
    return messages


def relevant_metadata():
    dashboard = load_json(DOCS_DATA / "dashboard.json", {})
    participants = load_json(DATA / "participants_by_address.json", {})
    validators = load_json(DATA / "validators.json", {"validators": []}).get("validators", [])
    rows = {}

    def ensure(address):
        rows.setdefault(
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
                "publicProof": False,
            },
        )
        return rows[address]

    for row in dashboard.get("recipients", []) or []:
        item = ensure(row["address"])
        item["roles"].add("recipient")
        item["currentLabel"] = row.get("label") or item["currentLabel"]
        item["totalCompensationGonka"] = row.get("totalGonka") or 0
        item["inferenceUrl"] = row.get("inferenceUrl") or item["inferenceUrl"]
        item["validatorKey"] = (row.get("publicNodeInfo") or {}).get("validatorKey", item["validatorKey"])
        item["matchedValidator"] = ((row.get("publicNodeInfo") or {}).get("matchedValidator") or {}).get("operatorAddress", "")
        item["publicProof"] = item["publicProof"] or row.get("identityBoundary") == "public_owner_proof"
    for row in dashboard.get("votes", []) or []:
        item = ensure(row["voter"])
        item["roles"].add("voter")
        item["currentLabel"] = row.get("label") or item["currentLabel"]
        item["votingPower"] = row.get("votingPower") or 0
        item["publicProof"] = item["publicProof"] or row.get("identityBoundary") == "public_owner_proof"
    for address, participant in participants.items():
        if address not in rows or not isinstance(participant, dict) or participant.get("error"):
            continue
        rows[address]["inferenceUrl"] = participant.get("inference_url") or rows[address]["inferenceUrl"]
        rows[address]["validatorKey"] = participant.get("validator_key") or rows[address]["validatorKey"]
    for validator in validators:
        account = account_from_valoper(validator.get("operator_address", ""))
        if account in rows:
            rows[account]["matchedValidator"] = validator.get("operator_address", "")
    for item in rows.values():
        item["roles"] = " ".join(sorted(item["roles"]))
    return rows


def addresses_from_url(url):
    found = set(account_from_valoper(item) for item in ADDRESS_RE.findall(url or ""))
    try:
        query = parse_qs(urlparse(url).query)
    except Exception:
        return found
    for key in ["participant", "address", "wallet", "validator"]:
        for value in query.get(key, []):
            found.update(account_from_valoper(item) for item in ADDRESS_RE.findall(value))
    return found


def message_features(message):
    text = message.get("text", "")
    hrefs = message.get("hrefs") or []
    all_text = " ".join([text, message.get("replyText", ""), " ".join(hrefs)])
    addresses = set(account_from_valoper(item) for item in ADDRESS_RE.findall(all_text))
    for href in hrefs:
        addresses.update(addresses_from_url(href))
    return {
        "addresses": addresses,
        "urls": sorted(set(URL_RE.findall(all_text)) | {href for href in hrefs if href.startswith(("http://", "https://"))}),
        "usernames": sorted(set(USERNAME_RE.findall(all_text))),
        "ips": sorted(set(IP_RE.findall(all_text))),
        "selfClaim": bool(SELF_CLAIM_RE.search(text)),
        "operator": bool(OPERATOR_RE.search(text)),
        "ownerInquiry": bool(OWNER_INQUIRY_RE.search(text)),
        "poolRoster": bool(POOL_ROSTER_RE.search(text)),
        "formula": bool(FORMULA_RE.search(text)),
    }


def classify_candidate(message, context_kind, candidate_label):
    text = message.get("text", "")
    if SELF_CLAIM_RE.search(text):
        return "strong_local_operator_signal", "telegram_self_claim", "high"
    if OPERATOR_OWNERSHIP_RE.search(text):
        return "strong_local_operator_signal", "telegram_operator_statement", "high"
    if context_kind == "reply_parent" and (SELF_CLAIM_RE.search(text) or OPERATOR_OWNERSHIP_RE.search(text)):
        return "strong_local_operator_signal", "telegram_operator_answer", "high"
    if DELEGATION_RE.search(text):
        return "weak_context", "telegram_delegation_target", "medium"
    if FORMULA_RE.search(text) and ("ваша нода" in text.lower() or "ваш" in text.lower()):
        return "medium_operator_context", "telegram_operator_context", "medium"
    if POOL_ROSTER_RE.search(text) and candidate_label:
        return "medium_operator_context", "telegram_pool_roster", "medium"
    if OWNER_INQUIRY_RE.search(text):
        return "weak_context", "telegram_owner_inquiry", "low"
    if context_kind != "same_message":
        return "weak_context", f"telegram_{context_kind}_context", "low"
    return "weak_context", "telegram_context_only", "medium"


def candidate_label_for(message, features):
    text = message.get("text", "")
    text_without_urls = URL_RE.sub(" ", text)
    if features.get("formula"):
        return "Formula X"
    match = POOL_ROSTER_RE.search(text_without_urls)
    if match:
        return clean_text(match.group(0))
    if features.get("selfClaim") or features.get("operator"):
        return message.get("author", "")
    return ""


def add_candidate(candidates, address, message, features, context_kind):
    label = candidate_label_for(message, features)
    level, source_type, confidence = classify_candidate(message, context_kind, label)
    row = {
        "address": address,
        "bestChatCandidateLabel": label,
        "evidenceLevel": level,
        "sourceType": source_type,
        "confidence": confidence,
        "isAttributionProof": False,
        "chat": message.get("chat", ""),
        "messageId": message.get("messageId", ""),
        "messageTime": message.get("date", ""),
        "author": message.get("author", ""),
        "authorSource": message.get("authorSource", ""),
        "contextKind": context_kind,
        "replyToMessageId": message.get("replyToMessageId", ""),
        "sourceFile": message.get("sourceFile", ""),
        "sourceUrl": source_url(message.get("sourceFile", ""), message.get("messageId", "")),
        "excerpt": excerpt(message.get("text", "")),
        "replyText": excerpt(message.get("replyText", ""), 260),
        "urls": features.get("urls", []),
        "usernames": features.get("usernames", []),
        "ips": features.get("ips", []),
        "caveat": "Local Telegram chat signal; not public owner proof without independent corroboration.",
    }
    candidates[address].append(row)


LEVEL_PRIORITY = {
    "public_owner_proof": 0,
    "strong_local_operator_signal": 1,
    "medium_operator_context": 2,
    "weak_context": 3,
    "no_chat_signal": 4,
}


def best_candidate(rows):
    if not rows:
        return {}
    return sorted(
        rows,
        key=lambda row: (
            LEVEL_PRIORITY.get(row["evidenceLevel"], 9),
            {"high": 0, "medium": 1, "low": 2}.get(row["confidence"], 3),
            row["sourceFile"],
            row["messageId"],
        ),
    )[0]


def build_audit():
    metadata = relevant_metadata()
    relevant = set(metadata)
    messages = []
    for path in sorted(HISTORY.glob("Gonka */messages*.html")):
        messages.extend(parse_file(path))

    by_message_id = {}
    by_source_file = {}
    for message in messages:
        by_message_id[(message["sourceFile"], message["messageId"])] = message
        by_source_file.setdefault(message["sourceFile"], []).append(message)
        message["features"] = message_features(message)

    candidates = {address: [] for address in relevant}
    for message in messages:
        features = message["features"]
        direct_addresses = features["addresses"] & relevant
        for address in direct_addresses:
            add_candidate(candidates, address, message, features, "same_message")

        reply_id = message.get("replyToMessageId")
        if reply_id and (features["selfClaim"] or features["operator"] or features["poolRoster"]):
            parent = by_message_id.get((message["sourceFile"], reply_id))
            if parent:
                parent_addresses = parent["features"]["addresses"] & relevant
                for address in parent_addresses:
                    add_candidate(candidates, address, message, features, "reply_parent")

    rows = []
    for address, meta in sorted(metadata.items()):
        best = best_candidate(candidates[address])
        evidence_level = best.get("evidenceLevel", "no_chat_signal")
        if meta.get("publicProof"):
            evidence_level = "public_owner_proof"
        row = {
            **meta,
            "evidenceLevel": evidence_level,
            "bestChatCandidateLabel": best.get("bestChatCandidateLabel", ""),
            "sourceType": best.get("sourceType", "no_chat_signal"),
            "confidence": best.get("confidence", ""),
            "isAttributionProof": False,
            "chat": best.get("chat", ""),
            "messageId": best.get("messageId", ""),
            "messageTime": best.get("messageTime", ""),
            "author": best.get("author", ""),
            "authorSource": best.get("authorSource", ""),
            "contextKind": best.get("contextKind", ""),
            "replyToMessageId": best.get("replyToMessageId", ""),
            "sourceFile": best.get("sourceFile", ""),
            "sourceUrl": best.get("sourceUrl", ""),
            "excerpt": best.get("excerpt", ""),
            "replyText": best.get("replyText", ""),
            "urls": best.get("urls", []),
            "usernames": best.get("usernames", []),
            "ips": best.get("ips", []),
            "caveat": best.get("caveat", "No relevant local chat signal found."),
            "allCandidateCount": len(candidates[address]),
        }
        rows.append(row)
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
            "source": "history/Gonka */messages*.html",
            "description": "Structured local Telegram attribution audit for proposal participants. Chat-only rows are not public owner proof.",
        },
        "summary": summary,
        "rows": rows,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n")

    fields = [
        "address",
        "currentLabel",
        "roles",
        "totalCompensationGonka",
        "votingPower",
        "evidenceLevel",
        "bestChatCandidateLabel",
        "sourceType",
        "confidence",
        "chat",
        "messageId",
        "messageTime",
        "author",
        "contextKind",
        "replyToMessageId",
        "sourceFile",
        "sourceUrl",
        "inferenceUrl",
        "validatorKey",
        "matchedValidator",
        "allCandidateCount",
        "excerpt",
        "caveat",
    ]
    with (REPORTS / "chat_participant_attribution.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})

    with (REPORTS / "chat_participant_attribution.md").open("w") as f:
        f.write("# Chat Participant Attribution Audit\n\n")
        f.write("Local Telegram chats are forensic context. A chat-only signal can identify an operator candidate, but it is not public owner proof without independent corroboration.\n\n")
        for key, value in summary.items():
            f.write(f"- {key}: {value}\n")
        f.write("\n")
        for row in rows:
            if row["evidenceLevel"] in {"no_chat_signal", "weak_context"} and row["allCandidateCount"] == 0:
                continue
            f.write(f"## {row['evidenceLevel']}: `{row['address']}`\n\n")
            f.write(f"- Current label: {row['currentLabel']}\n")
            f.write(f"- Chat candidate: {row['bestChatCandidateLabel'] or 'none'}; source: {row['sourceType']} ({row['confidence'] or 'none'})\n")
            f.write(f"- Roles: {row['roles'] or 'none'}; compensation: {row['totalCompensationGonka']} GONKA; voting power: {row['votingPower']}\n")
            if row["sourceFile"]:
                f.write(f"- Source: `{row['sourceFile']}` {row['messageId']} {row['messageTime']} by {row['author'] or 'unknown'}\n")
            if row["excerpt"]:
                f.write(f"- Excerpt: {row['excerpt']}\n")
            f.write(f"- Caveat: {row['caveat']}\n\n")


def main():
    rows = build_audit()
    write_outputs(rows)
    print(json.dumps({"rows": len(rows), "levels": {level: sum(1 for row in rows if row["evidenceLevel"] == level) for level in LEVEL_PRIORITY}}, sort_keys=True))


if __name__ == "__main__":
    main()
