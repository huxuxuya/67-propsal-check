#!/usr/bin/env python3
import html
import json
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HISTORY = ROOT / "history"
DATA = ROOT / "data"
OUT = DATA / "telegram_evidence.json"

ADDRESS_RE = re.compile(r"gonka1[0-9a-z]{38}|gonkavaloper1[0-9a-z]{38}")
URL_RE = re.compile(r"https?://[^\s\"'<>]+")
USERNAME_RE = re.compile(r"(?<![A-Za-z0-9_])@[A-Za-z0-9_]{4,32}")
SELF_CLAIM_RE = re.compile(
    r"\b(моя|моей|мой|наша|нашей|наш|своей|свою)\s+"
    r"(нода|ноде|ноду|node|узел|адрес|баланс)|"
    r"\bу\s+нас\s+на\s+gonka1|"
    r"\bмы\s+(хостим|послали|делегировали|заделегировали)|"
    r"\bтестирую\s+новую\s+конфигурацию|"
    r"\bэто\s+кстати\s+моя\s+первая\s+нода",
    re.IGNORECASE,
)
OPERATOR_RE = re.compile(
    r"(set-poc-delegation[\s\S]{0,260}(можно\s+вот\s+сюда|можете\s+делегировать|будет\s+запускать|буду\s+давать|работает|топ\s+1\s+сегмент)|"
    r"(нашу|нашей)\s+[\s\S]{0,80}(ноду|node)|"
    r"\bмы\s+хостим\b|"
    r"\bбудет\s+запускать\b|"
    r"\bбуду\s+давать\s+обн|"
    r"\bтоп\s+1\s+сегмент\s+по\s+весу)",
    re.IGNORECASE,
)
DELEGATION_TARGET_RE = re.compile(
    r"set-poc-delegation|\b(делегировать|заделегировать|делегировали|делегации|делегацию)\b",
    re.IGNORECASE,
)
OWNER_INQUIRY_RE = re.compile(
    r"\b(чья|чей|чье|чья\s+нода|владелец|владельцев|owner|оунер|кто-то\s+знает)\b",
    re.IGNORECASE,
)
TRACKER_RE = re.compile(r"tracker\.gonka|gonkascan\.com|gonka\.gg/(participants|address|wallets)", re.IGNORECASE)


class TelegramExportParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.messages = []
        self.current = None
        self.stack = []
        self.in_from = False
        self.in_text = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = set((attrs.get("class") or "").split())
        self.stack.append((tag, classes))
        if tag == "div" and "message" in classes and "service" not in classes:
            self.current = {
                "messageId": (attrs.get("id") or "").replace("message", ""),
                "author": "",
                "date": "",
                "text": "",
            }
        if not self.current:
            return
        if tag == "div" and "from_name" in classes:
            self.in_from = True
        if tag == "div" and "text" in classes:
            self.in_text = True
        if tag == "div" and "date" in classes:
            self.current["date"] = attrs.get("title", "")

    def handle_endtag(self, tag):
        if self.current and tag == "div":
            if self.in_from and self.stack and "from_name" in self.stack[-1][1]:
                self.in_from = False
            if self.in_text and self.stack and "text" in self.stack[-1][1]:
                self.in_text = False
            if self.stack and "message" in self.stack[-1][1]:
                self.current["author"] = " ".join(self.current["author"].split())
                self.current["text"] = " ".join(self.current["text"].split())
                self.messages.append(self.current)
                self.current = None
        if self.stack:
            self.stack.pop()

    def handle_data(self, data):
        if not self.current:
            return
        if self.in_from:
            self.current["author"] += data
        elif self.in_text:
            self.current["text"] += data


def parse_file(path):
    parser = TelegramExportParser()
    parser.feed(path.read_text(errors="replace"))
    last_author = ""
    for message in parser.messages:
        author = message.get("author", "")
        if author:
            last_author = author
            message["authorSource"] = "explicit"
        elif last_author:
            message["author"] = last_author
            message["authorSource"] = "inherited_previous_message"
        else:
            message["authorSource"] = "missing"
    return parser.messages


def excerpt(text, max_len=420):
    text = html.unescape(" ".join((text or "").split()))
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "..."


def chat_name(path):
    return path.parent.name


def classify_message(text, addresses, urls, usernames, author, author_source):
    context_tags = []
    if SELF_CLAIM_RE.search(text):
        context_tags.append("self_or_team_claim")
    if OPERATOR_RE.search(text):
        context_tags.append("operator_or_delegation")
    if DELEGATION_TARGET_RE.search(text):
        context_tags.append("delegation_context")
    if OWNER_INQUIRY_RE.search(text):
        context_tags.append("owner_inquiry")
    if TRACKER_RE.search(text) or any("tracker.gonka" in url or "gonkascan.com" in url or "gonka.gg" in url for url in urls):
        context_tags.append("tracker_or_explorer_link")
    if usernames:
        context_tags.append("telegram_username")

    if addresses and author and "self_or_team_claim" in context_tags:
        inherited_author = author_source != "explicit"
        return {
            "sourceType": "telegram_self_or_team_claim",
            "confidence": "medium" if inherited_author else "high",
            "signalStrength": "strong_context" if inherited_author else "strong",
            "contextTags": context_tags,
            "caveat": "Telegram author was inherited from the previous export message; self/team ownership language is a strong lead but needs manual verification." if inherited_author else "Telegram author used self/team ownership language around this address; strong local-export attribution signal, but not public owner proof without a linkable public source.",
        }
    if addresses and "owner_inquiry" in context_tags:
        return {
            "sourceType": "telegram_owner_inquiry",
            "confidence": "low",
            "signalStrength": "context",
            "contextTags": context_tags,
            "caveat": "Telegram message asks about ownership; this is investigation context, not attribution.",
        }
    if addresses and author and "operator_or_delegation" in context_tags:
        return {
            "sourceType": "telegram_operator_statement",
            "confidence": "high",
            "signalStrength": "strong",
            "contextTags": context_tags,
            "caveat": "Telegram author posted operator/delegation language around this address; strong local-export operator signal, but not public owner proof without a linkable public source.",
        }
    if addresses and "delegation_context" in context_tags:
        return {
            "sourceType": "telegram_delegation_context",
            "confidence": "medium",
            "signalStrength": "context",
            "contextTags": context_tags,
            "caveat": "Telegram message discusses delegation for this address; this is operational context, not owner attribution by itself.",
        }
    if addresses:
        return {
            "sourceType": "telegram_address_context",
            "confidence": "medium",
            "signalStrength": "context",
            "contextTags": context_tags,
            "caveat": "Telegram export mentions this address; treat as context unless corroborated by self-claim, operator language, or public evidence.",
        }
    return {
        "sourceType": "telegram_export_excerpt",
        "confidence": "low",
        "signalStrength": "weak",
        "contextTags": context_tags,
        "caveat": "Telegram export excerpt requires corroboration.",
    }


def main():
    DATA.mkdir(exist_ok=True)
    rows = []
    summary = {"files": 0, "messages": 0, "messagesWithMatches": 0}
    for path in sorted(HISTORY.glob("Gonka */messages*.html")):
        summary["files"] += 1
        for message in parse_file(path):
            summary["messages"] += 1
            text = message.get("text", "")
            addresses = sorted(set(ADDRESS_RE.findall(text)))
            urls = sorted(set(URL_RE.findall(text)))
            usernames = sorted(set(USERNAME_RE.findall(text)))
            if not addresses and not urls and not usernames:
                continue
            classification = classify_message(text, addresses, urls, usernames, message.get("author", ""), message.get("authorSource", "missing"))
            summary["messagesWithMatches"] += 1
            rows.append(
                {
                    "chat": chat_name(path),
                    "messageId": message.get("messageId", ""),
                    "date": message.get("date", ""),
                    "author": message.get("author", ""),
                    "authorSource": message.get("authorSource", "missing"),
                    "excerpt": excerpt(text),
                    "addresses": addresses,
                    "urls": urls,
                    "usernames": usernames,
                    "sourceFile": str(path.relative_to(ROOT)),
                    "sourceType": classification["sourceType"],
                    "confidence": classification["confidence"],
                    "signalStrength": classification["signalStrength"],
                    "contextTags": classification["contextTags"],
                    "isAttributionProof": False,
                    "caveat": classification["caveat"],
                }
            )

    snapshot = {
        "source": {
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "scope": "Curated excerpts from local Telegram HTML exports; full exports remain ignored in history/",
        },
        "summary": summary,
        "messages": rows,
    }
    OUT.write_text(json.dumps(snapshot, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    print(f"Wrote {OUT}")
    print(f"Messages with matches: {len(rows)}")


if __name__ == "__main__":
    main()
