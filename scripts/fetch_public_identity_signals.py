#!/usr/bin/env python3
import csv
import json
import socket
import ssl
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
UPSTREAM = ROOT / "upstream" / "gonka-kimi-restitution"
OUT = DATA / "public_identity_signals.json"

HTTP_TIMEOUT = 4
DNS_TIMEOUT = 4
MAX_WORKERS = 16


def load_json(path):
    with path.open() as f:
        return json.load(f)


def account_from_valoper(operator_address):
    if not operator_address.startswith("gonkavaloper"):
        return ""
    return "gonka" + operator_address[len("gonkavaloper") :]


def extract_attr(events, event_type, key):
    for event in events:
        if event.get("type") != event_type:
            continue
        for attr in event.get("attributes", []):
            if attr.get("key") == key:
                return attr.get("value")
    return None


def relevant_addresses():
    addresses = set()
    with (UPSTREAM / "aggregate_compensation.csv").open(newline="") as f:
        for row in csv.DictReader(f):
            if float(row["total_gonka"]) > 0:
                addresses.add(row["address"])

    txs = load_json(DATA / "proposal_67_tx_search.json")["result"]["txs"]
    for tx in txs:
        voter = extract_attr(tx["tx_result"]["events"], "proposal_vote", "voter")
        if voter:
            addresses.add(voter)
    return addresses


def normalize_url(value):
    value = (value or "").strip()
    if not value:
        return ""
    if value.startswith("https:/") and not value.startswith("https://"):
        value = "https://" + value[len("https:/") :].lstrip("/")
    if value.startswith("http:/") and not value.startswith("http://"):
        value = "http://" + value[len("http:/") :].lstrip("/")
    if "://" not in value:
        value = "https://" + value
    return value


def hostname_for_url(url):
    try:
        return urllib.parse.urlparse(url).hostname or ""
    except Exception:
        return ""


def collect_targets(addresses):
    participants = load_json(DATA / "participants_by_address.json")
    validators = load_json(DATA / "validators.json").get("validators", [])
    gns = load_json(DATA / "gns_names_by_address.json") if (DATA / "gns_names_by_address.json").exists() else {}

    consensus_metadata = {}
    for validator in validators:
        key = validator.get("consensus_pubkey", {}).get("key", "")
        desc = validator.get("description", {})
        if key:
            consensus_metadata[key] = {
                "operatorAddress": validator.get("operator_address", ""),
                "accountAddress": account_from_valoper(validator.get("operator_address", "")),
                "moniker": desc.get("moniker", ""),
                "website": desc.get("website", ""),
                "identity": desc.get("identity", ""),
                "securityContact": desc.get("security_contact", ""),
                "details": desc.get("details", ""),
            }

    targets = {"urls": {}, "domains": {}, "ips": {}}

    def add_url(url, source_type, address, source_value):
        normalized = normalize_url(url)
        host = hostname_for_url(normalized)
        if not normalized or not host:
            return
        targets["urls"].setdefault(normalized, {"url": normalized, "host": host, "sources": []})
        targets["urls"][normalized]["sources"].append(
            {"address": address, "sourceType": source_type, "sourceValue": source_value}
        )
        add_domain_or_ip(host, source_type, address, source_value)

    def add_domain_or_ip(host, source_type, address, source_value):
        try:
            socket.inet_pton(socket.AF_INET, host)
            targets["ips"].setdefault(host, {"ip": host, "sources": []})
            targets["ips"][host]["sources"].append(
                {"address": address, "sourceType": source_type, "sourceValue": source_value}
            )
            return
        except OSError:
            pass
        targets["domains"].setdefault(host, {"domain": host, "sources": []})
        targets["domains"][host]["sources"].append(
            {"address": address, "sourceType": source_type, "sourceValue": source_value}
        )

    for address in sorted(addresses):
        participant = participants.get(address) or {}
        if isinstance(participant, dict):
            add_url(participant.get("inference_url", ""), "participant_inference_url", address, participant.get("inference_url", ""))
            matched = consensus_metadata.get(participant.get("validator_key", ""))
            if matched:
                add_url(matched.get("website", ""), "matched_validator_website", address, matched.get("website", ""))

        for item in (gns.get("byAddress", {}) or {}).get(address, []):
            for record in (item.get("records") or {}).values():
                if record.get("key") == "website":
                    add_url(record.get("value", ""), "gns_record_website", address, f"{item['fullName']}:{record.get('value', '')}")

    return targets


def resolve_domain(domain):
    result = {"domain": domain, "addresses": [], "reverse": {}, "error": ""}
    old_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(DNS_TIMEOUT)
    try:
        infos = socket.getaddrinfo(domain, None, proto=socket.IPPROTO_TCP)
        ips = sorted({item[4][0] for item in infos})
        result["addresses"] = ips
        for ip in ips:
            try:
                result["reverse"][ip] = socket.gethostbyaddr(ip)[0]
            except Exception as exc:
                result["reverse"][ip] = {"error": str(exc)}
    except Exception as exc:
        result["error"] = str(exc)
    finally:
        socket.setdefaulttimeout(old_timeout)
    return result


def rdap_lookup(kind, value):
    url = f"https://rdap.org/{kind}/{urllib.parse.quote(value)}"
    try:
        with urllib.request.urlopen(url, timeout=HTTP_TIMEOUT) as response:
            body = response.read(250000).decode(errors="replace")
            return {"url": url, "status": response.status, "json": json.loads(body), "error": ""}
    except Exception as exc:
        return {"url": url, "status": None, "json": None, "error": str(exc)}


def tls_lookup(host, port=443):
    context = ssl.create_default_context()
    try:
        with socket.create_connection((host, port), timeout=HTTP_TIMEOUT) as sock:
            with context.wrap_socket(sock, server_hostname=host) as tls:
                cert = tls.getpeercert()
                return {
                    "host": host,
                    "port": port,
                    "subject": cert.get("subject", []),
                    "issuer": cert.get("issuer", []),
                    "notBefore": cert.get("notBefore", ""),
                    "notAfter": cert.get("notAfter", ""),
                    "subjectAltName": cert.get("subjectAltName", []),
                    "version": cert.get("version"),
                    "serialNumber": cert.get("serialNumber", ""),
                    "error": "",
                }
    except Exception as exc:
        return {"host": host, "port": port, "error": str(exc)}


def http_probe(url):
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "proposal-67-forensic-snapshot/1.0"})
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT) as response:
            body = response.read(65536).decode(errors="replace")
            title = ""
            lower = body.lower()
            start = lower.find("<title")
            if start != -1:
                start = lower.find(">", start)
                end = lower.find("</title>", start)
                if start != -1 and end != -1:
                    title = body[start + 1 : end].strip()[:300]
            headers = {k: v for k, v in response.headers.items()}
            return {"url": url, "status": response.status, "finalUrl": response.url, "headers": headers, "title": title, "error": ""}
    except Exception as exc:
        return {"url": url, "status": None, "finalUrl": "", "headers": {}, "title": "", "error": str(exc)}


def parallel_lookup(values, fn):
    results = {}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(fn, value): value for value in values}
        for future in as_completed(futures):
            value = futures[future]
            try:
                results[value] = future.result()
            except Exception as exc:
                results[value] = {"error": str(exc)}
    return results


def main():
    DATA.mkdir(exist_ok=True)
    addresses = relevant_addresses()
    targets = collect_targets(addresses)

    domains = set(targets["domains"])
    ips = set(targets["ips"])
    urls = set(targets["urls"])

    dns = {}
    rdap_domains = {}
    rdap_ips = {}
    tls = {}
    http = {}

    dns = parallel_lookup(sorted(domains), resolve_domain)
    for domain_result in dns.values():
        ips.update(ip for ip in domain_result.get("addresses", []) if ":" not in ip)

    rdap_domains = parallel_lookup(sorted(domains), lambda domain: rdap_lookup("domain", domain))
    rdap_ips = parallel_lookup(sorted(ips), lambda ip: rdap_lookup("ip", ip))
    tls = parallel_lookup(sorted(domains), tls_lookup)
    http = parallel_lookup(sorted(urls), http_probe)

    snapshot = {
        "source": {
            "fetchedAt": datetime.now(timezone.utc).isoformat(),
            "scope": "Proposal #67 recipients and final voters only",
        },
        "targets": targets,
        "dns": dns,
        "rdapDomains": rdap_domains,
        "rdapIps": rdap_ips,
        "tls": tls,
        "http": http,
    }
    OUT.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n")
    print(f"Wrote {OUT}")
    print(f"Targets: {len(urls)} urls, {len(domains)} domains, {len(ips)} ips")


if __name__ == "__main__":
    main()
