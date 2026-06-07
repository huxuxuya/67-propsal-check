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
    return parser.messages


def excerpt(text, max_len=420):
    text = html.unescape(" ".join((text or "").split()))
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "..."


def chat_name(path):
    return path.parent.name


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
            summary["messagesWithMatches"] += 1
            rows.append(
                {
                    "chat": chat_name(path),
                    "messageId": message.get("messageId", ""),
                    "date": message.get("date", ""),
                    "author": message.get("author", ""),
                    "excerpt": excerpt(text),
                    "addresses": addresses,
                    "urls": urls,
                    "usernames": usernames,
                    "sourceFile": str(path.relative_to(ROOT)),
                    "sourceType": "telegram_export_excerpt",
                    "confidence": "medium" if addresses else "low",
                    "isAttributionProof": False,
                    "caveat": "Telegram export excerpt is context evidence; it is attribution proof only if manually corroborated by public on-chain or profile data.",
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
