#!/usr/bin/env python3
import html
import json
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR = ROOT / "history" / "export-gonka-full"
OUT_JSON = ROOT / "data" / "discord_evidence.json"

ADDRESS_RE = re.compile(r"\b(?:gonka1|gonkavaloper1)[0-9a-z]{38}\b")
URL_RE = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)
IP_RE = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}(?::\d{2,5})?\b")
CHANNEL_RE = re.compile(r"Gonka - (.*?) \[(\d+)\]\.html$")


def account_from_valoper(value):
    if value.startswith("gonkavaloper"):
        return "gonka" + value[len("gonkavaloper") :]
    return value


def clean_text(value):
    value = html.unescape(value or "")
    value = re.sub(r"[ \t\r\f\v]+", " ", value)
    value = re.sub(r"\n\s+", "\n", value)
    return value.strip()


def excerpt(value, max_len=700):
    value = clean_text(value)
    if len(value) <= max_len:
        return value
    return value[: max_len - 1].rstrip() + "..."


def channel_from_path(path):
    match = CHANNEL_RE.search(path.name)
    if not match:
        return path.stem, ""
    return match.group(1).strip(), match.group(2)


class DiscordHTMLParser(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.path = path
        self.channel, self.channel_id = channel_from_path(path)
        self.messages = []
        self.current = None
        self.stack = []
        self.capture = []
        self.capture_target = ""
        self.capture_classes = set()
        self.last_author = {}
        self.in_content = False
        self.in_reply = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = set((attrs.get("class") or "").split())
        self.stack.append((tag, classes))
        if tag == "div" and "chatlog__message-container" in classes:
            self.current = {
                "platform": "discord",
                "chat": self.channel,
                "channelId": self.channel_id,
                "messageId": attrs.get("data-message-id", ""),
                "author": "",
                "authorUsername": "",
                "authorUserId": "",
                "authorSource": "explicit",
                "date": "",
                "text": "",
                "replyText": "",
                "replyAuthor": "",
                "replyToMessageId": "",
                "hrefs": [],
                "media": [],
                "sourceFile": str(self.path.relative_to(ROOT)),
            }
            return
        if not self.current:
            return
        if tag == "span" and "chatlog__author" in classes:
            self.current["authorUsername"] = attrs.get("title", "")
            self.current["authorUserId"] = attrs.get("data-user-id", "")
            self.capture_target = "author"
            self.capture_classes = classes
            self.capture = []
        elif tag == "span" and "chatlog__timestamp" in classes:
            self.current["date"] = attrs.get("title", "")
        elif tag == "div" and "chatlog__content" in classes:
            self.in_content = True
        elif tag == "div" and "chatlog__reply" in classes:
            self.in_reply = True
        elif tag == "div" and "chatlog__reply-author" in classes:
            self.capture_target = "replyAuthor"
            self.capture_classes = classes
            self.capture = []
        elif tag == "span" and "chatlog__reply-link" in classes:
            match = re.search(r"scrollToMessage\(event,'(\d+)'\)", attrs.get("onclick", ""))
            if match:
                self.current["replyToMessageId"] = match.group(1)
        if tag == "a":
            href = attrs.get("href", "")
            if href:
                self.current["hrefs"].append(html.unescape(href))
        if tag in {"img", "video"}:
            src = attrs.get("data-canonical-url") or attrs.get("src") or ""
            if src and "discord" in src:
                self.current["media"].append(html.unescape(src))

    def handle_endtag(self, tag):
        if self.current and self.capture_target and self.stack:
            _, classes = self.stack[-1]
            if classes == self.capture_classes:
                self.current[self.capture_target] = clean_text("".join(self.capture))
                self.capture_target = ""
                self.capture_classes = set()
                self.capture = []
        if self.current and tag == "div" and self.stack:
            _, classes = self.stack[-1]
            if "chatlog__content" in classes:
                self.in_content = False
            elif "chatlog__reply" in classes:
                self.in_reply = False
            elif "chatlog__message-container" in classes:
                for key in ["author", "text", "replyText", "replyAuthor"]:
                    self.current[key] = clean_text(self.current.get(key, ""))
                if self.current["author"]:
                    self.last_author = {
                        "author": self.current["author"],
                        "authorUsername": self.current.get("authorUsername", ""),
                        "authorUserId": self.current.get("authorUserId", ""),
                    }
                    self.current["authorSource"] = "explicit"
                elif self.last_author:
                    self.current.update(self.last_author)
                    self.current["authorSource"] = "inherited_previous_message"
                else:
                    self.current["authorSource"] = "missing"
                text_for_match = " ".join(
                    [
                        self.current.get("text", ""),
                        self.current.get("replyText", ""),
                        " ".join(self.current.get("hrefs") or []),
                    ]
                )
                self.current["addresses"] = sorted({account_from_valoper(item) for item in ADDRESS_RE.findall(text_for_match)})
                self.current["urls"] = sorted(set(URL_RE.findall(text_for_match)) | set(self.current.get("hrefs") or []))
                self.current["ips"] = sorted(set(IP_RE.findall(text_for_match)))
                self.current["excerpt"] = excerpt(self.current.get("text", ""))
                self.current["hrefs"] = sorted(set(self.current["hrefs"]))
                self.current["media"] = sorted(set(self.current["media"]))
                self.messages.append(self.current)
                self.current = None
                self.in_content = False
                self.in_reply = False
                self.capture_target = ""
        if self.stack:
            self.stack.pop()

    def handle_data(self, data):
        if not self.current:
            return
        if self.capture_target:
            self.capture.append(data)
        elif self.in_content:
            self.current["text"] += data
        elif self.in_reply:
            self.current["replyText"] += data


def parse_file(path):
    parser = DiscordHTMLParser(path)
    parser.feed(path.read_text(errors="replace"))
    parser.close()
    return parser.messages


def classify_message(message):
    text = message.get("text", "")
    lowered = text.lower()
    has_identity_terms = any(
        term in lowered
        for term in [
            "my node",
            "my address",
            "our node",
            "моя нода",
            "мой адрес",
            "наша нода",
            "validator",
            "operator",
            "delegat",
            "host",
            "formula",
            "ancapex",
            "hyperfusion",
            "votkon",
        ]
    )
    if message.get("addresses") and has_identity_terms:
        return "discord_identity_excerpt", "medium", "Discord excerpt contains an address and operator/identity wording; requires corroboration."
    if message.get("addresses"):
        return "discord_address_excerpt", "medium", "Discord excerpt contains an address; this is context, not owner proof."
    if message.get("ips") and has_identity_terms:
        return "discord_host_excerpt", "low", "Discord excerpt contains host/operator context without a direct proposal address."
    return "discord_context_excerpt", "low", "Discord excerpt is searchable context."


def main():
    messages = []
    for path in sorted(EXPORT_DIR.glob("*.html")):
        messages.extend(parse_file(path))
    matched = []
    for message in messages:
        if not (message.get("addresses") or message.get("ips")):
            continue
        source_type, confidence, caveat = classify_message(message)
        matched.append(
            {
                **message,
                "sourceType": source_type,
                "confidence": confidence,
                "caveat": caveat,
                "sourceUrl": f"{message['sourceFile']}#chatlog__message-container-{message['messageId']}",
            }
        )
    payload = {
        "source": {
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "exportDir": str(EXPORT_DIR.relative_to(ROOT)),
        },
        "summary": {
            "files": len(list(EXPORT_DIR.glob("*.html"))),
            "messages": len(messages),
            "messagesWithEvidence": len(matched),
            "messagesWithAddresses": sum(1 for item in matched if item.get("addresses")),
            "uniqueAddresses": len({addr for item in matched for addr in item.get("addresses", [])}),
        },
        "messages": matched,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    print(json.dumps(payload["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
