#!/usr/bin/env python3
import base64
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from env_utils import gonka_api_source_label, gonka_api_url


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

NODE = gonka_api_url()
GNS_CONTRACT = "gonka1rd582xazhyxde68g099ed0zpjzq0j0shnhkegg06s8009h7lnxjqvyf0qf"
STATE_PATH = f"/chain-api/cosmwasm/wasm/v1/contract/{GNS_CONTRACT}/state"


def fetch_json(url):
    with urllib.request.urlopen(url, timeout=45) as response:
        return json.loads(response.read().decode())


def decode_key(raw_key):
    if all(char in "0123456789abcdefABCDEF" for char in raw_key) and len(raw_key) % 2 == 0:
        data = bytes.fromhex(raw_key)
    else:
        data = base64.b64decode(raw_key)
    if len(data) < 2:
        return {"namespace": "", "name": "", "rawBytesHex": data.hex()}
    namespace_len = data[0] << 8 | data[1]
    namespace = data[2 : 2 + namespace_len].decode(errors="replace")
    rest = data[2 + namespace_len :]
    name = rest.decode(errors="replace")
    return {"namespace": namespace, "name": name, "restHex": rest.hex(), "rawBytesHex": data.hex()}


def decode_length_prefixed_text(data):
    if len(data) < 2:
        return "", b""
    length = data[0] << 8 | data[1]
    value = data[2 : 2 + length].decode(errors="replace")
    rest = data[2 + length :]
    return value, rest


def decode_value(raw_value):
    decoded = base64.b64decode(raw_value).decode()
    return json.loads(decoded)


def main():
    DATA.mkdir(exist_ok=True)
    pages = []
    names = []
    reverse = {}
    records = {}
    namespace_counts = {}
    next_key = None

    while True:
        params = {"pagination.limit": "100"}
        if next_key:
            params["pagination.key"] = next_key
        url = f"{NODE}{STATE_PATH}?{urllib.parse.urlencode(params)}"
        page = fetch_json(url)
        pages.append({"url": f"{gonka_api_source_label()}{STATE_PATH}?{urllib.parse.urlencode(params)}", "response": page})

        for model in page.get("models", []):
            key = decode_key(model["key"])
            namespace_counts[key["namespace"]] = namespace_counts.get(key["namespace"], 0) + 1
            try:
                value = decode_value(model["value"])
            except Exception as exc:
                value = {"decode_error": str(exc), "raw_value": model["value"]}
            if key["namespace"] == "names":
                names.append(
                    {
                        "name": key["name"],
                        "fullName": f"{key['name']}.gnk",
                        "address": value.get("address") if isinstance(value, dict) else None,
                        "owner": value.get("owner") if isinstance(value, dict) else None,
                        "expiresAt": value.get("expires_at") if isinstance(value, dict) else None,
                        "salePrice": value.get("sale_price") if isinstance(value, dict) else None,
                        "rawKey": model["key"],
                        "rawValue": model["value"],
                        "decoded": value,
                    }
                )
            elif key["namespace"] == "reverse":
                reverse[key["name"]] = {
                    "address": key["name"],
                    "name": value,
                    "fullName": f"{value}.gnk" if isinstance(value, str) else "",
                    "rawKey": model["key"],
                    "rawValue": model["value"],
                }
            elif key["namespace"] == "records":
                rest = bytes.fromhex(key["restHex"])
                name, record_key_bytes = decode_length_prefixed_text(rest)
                record_key = record_key_bytes.decode(errors="replace")
                records.setdefault(name, {})[record_key] = {
                    "name": name,
                    "fullName": f"{name}.gnk",
                    "key": record_key,
                    "value": value,
                    "rawKey": model["key"],
                    "rawValue": model["value"],
                }

        next_key = (page.get("pagination") or {}).get("next_key")
        if not next_key:
            break

    by_address = {}
    deduped_names = {}
    for item in names:
        deduped_names[item["fullName"]] = item
    for item in sorted(deduped_names.values(), key=lambda row: (row.get("address") or "", len(row["name"]), row["name"])):
        address = item.get("address")
        if not address:
            continue
        by_address.setdefault(address, []).append(
            {
                "name": item["name"],
                "fullName": item["fullName"],
                "owner": item.get("owner"),
                "expiresAt": item.get("expiresAt"),
                "salePrice": item.get("salePrice"),
                "reverse": reverse.get(address, {}).get("name") == item["name"],
                "records": records.get(item["name"], {}),
            }
        )

    raw_snapshot = {
        "source": {
            "node": gonka_api_source_label(),
            "contract": GNS_CONTRACT,
            "path": STATE_PATH,
            "fetchedAt": datetime.now(timezone.utc).isoformat(),
        },
        "namespaceCounts": namespace_counts,
        "pages": pages,
    }
    normalized = {
        "source": raw_snapshot["source"],
        "names": sorted(deduped_names.values(), key=lambda row: row["fullName"]),
        "reverse": reverse,
        "records": records,
        "byAddress": by_address,
    }

    (DATA / "gns_names_raw.json").write_text(json.dumps(raw_snapshot, indent=2, sort_keys=True) + "\n")
    (DATA / "gns_names_by_address.json").write_text(json.dumps(normalized, indent=2, sort_keys=True) + "\n")
    print(f"Wrote {DATA / 'gns_names_raw.json'}")
    print(f"Wrote {DATA / 'gns_names_by_address.json'}")
    print(f"Decoded {len(deduped_names)} unique names for {len(by_address)} addresses")


if __name__ == "__main__":
    main()
