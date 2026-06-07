#!/usr/bin/env python3
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "osint"

GONKA_NAMES_URL = "https://gonka.gg/names"
GITHUB_API = "https://api.github.com/repos/votkon/gonka-kimi-restitution"


def fetch_text(url, timeout=30):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "proposal-67-public-osint-snapshot/1.0",
            "Accept": "application/json,text/html,text/plain,*/*",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return {
            "url": url,
            "status": response.status,
            "headers": dict(response.headers.items()),
            "body": response.read(2_000_000).decode(errors="replace"),
            "fetchedAt": datetime.now(timezone.utc).isoformat(),
        }


def fetch_json(url, timeout=30):
    result = fetch_text(url, timeout)
    try:
        result["json"] = json.loads(result["body"])
    except Exception as exc:
        result["json"] = None
        result["jsonError"] = str(exc)
    return result


def extract_candidate_links(text):
    links = sorted(
        set(
            re.findall(r"https?://[^\s\"'<>]+", text)
            + re.findall(r"https?://[A-Za-z0-9._~:/?#\[\]@!$&()*+,;=%-]+", text)
        )
    )
    social_hosts = ("github.com", "x.com", "twitter.com", "t.me", "telegram.me", "discord.gg", "discord.com")
    return [link.rstrip(").,;") for link in links if any(host in link.lower() for host in social_hosts)]


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    snapshot = {
        "source": {
            "fetchedAt": datetime.now(timezone.utc).isoformat(),
            "scope": "Public web/GitHub/Gonka names OSINT for proposal #67 attribution",
        },
        "gonkaNames": {},
        "github": {},
        "publicSocialCandidates": [],
        "errors": [],
    }

    try:
        gonka_names = fetch_text(GONKA_NAMES_URL)
        snapshot["gonkaNames"] = {
            "url": gonka_names["url"],
            "status": gonka_names["status"],
            "headers": gonka_names["headers"],
            "bodyPath": "data/osint/gonka_names/gonka_names.html",
            "candidateSocialLinks": extract_candidate_links(gonka_names["body"]),
        }
        (OUT / "gonka_names").mkdir(parents=True, exist_ok=True)
        (OUT / "gonka_names" / "gonka_names.html").write_text(gonka_names["body"])
    except Exception as exc:
        snapshot["errors"].append({"source": GONKA_NAMES_URL, "error": str(exc)})

    github_requests = {
        "repo": GITHUB_API,
        "commits": f"{GITHUB_API}/commits?per_page=100",
        "contributors": f"{GITHUB_API}/contributors?per_page=100",
    }
    for key, url in github_requests.items():
        try:
            snapshot["github"][key] = fetch_json(url)
        except Exception as exc:
            snapshot["errors"].append({"source": url, "error": str(exc)})

    for section in [snapshot.get("gonkaNames", {})]:
        snapshot["publicSocialCandidates"].extend(section.get("candidateSocialLinks") or [])
    for response in snapshot["github"].values():
        body = response.get("body", "")
        snapshot["publicSocialCandidates"].extend(extract_candidate_links(body))
    snapshot["publicSocialCandidates"] = sorted(set(snapshot["publicSocialCandidates"]))

    write_json(OUT / "public_osint_sources.json", snapshot)
    print(f"Wrote {OUT / 'public_osint_sources.json'}")
    print(f"Social candidates: {len(snapshot['publicSocialCandidates'])}; errors: {len(snapshot['errors'])}")


if __name__ == "__main__":
    main()
