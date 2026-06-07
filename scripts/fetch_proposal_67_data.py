#!/usr/bin/env python3
import json
import urllib.request
from pathlib import Path

from env_utils import gonka_rpc_url


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
UPSTREAM = ROOT / "upstream" / "gonka-kimi-restitution"
NODE = gonka_rpc_url()


def fetch_json(url):
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.loads(response.read().decode())


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def addresses_for_case():
    addresses = set()
    with (UPSTREAM / "aggregate_compensation.csv").open() as f:
        header = f.readline().strip().split(",")
        address_idx = header.index("address")
        total_idx = header.index("total_gonka")
        for line in f:
            cols = line.strip().split(",")
            if cols and float(cols[total_idx]) > 0:
                addresses.add(cols[address_idx])

    txs = fetch_json(
        f"{NODE}/chain-rpc/tx_search?query=%22proposal_vote.proposal_id%3D%2767%27%22&prove=false&page=1&per_page=100&order_by=%22asc%22"
    )["result"]["txs"]
    for tx in txs:
        for event in tx["tx_result"]["events"]:
            if event.get("type") != "proposal_vote":
                continue
            for attr in event.get("attributes", []):
                if attr.get("key") == "voter":
                    addresses.add(attr["value"])
    return sorted(addresses)


def main():
    DATA.mkdir(exist_ok=True)
    write_json(DATA / "proposal_67.json", fetch_json(f"{NODE}/chain-api/cosmos/gov/v1/proposals/67"))
    write_json(
        DATA / "proposal_67_tx_search.json",
        fetch_json(f"{NODE}/chain-rpc/tx_search?query=%22proposal_vote.proposal_id%3D%2767%27%22&prove=false&page=1&per_page=100&order_by=%22asc%22"),
    )
    write_json(
        DATA / "validators.json",
        fetch_json(f"{NODE}/chain-api/cosmos/staking/v1beta1/validators?pagination.limit=2000"),
    )

    participants = {}
    for address in addresses_for_case():
        try:
            participants[address] = fetch_json(
                f"{NODE}/chain-api/productscience/inference/inference/participant/{address}"
            ).get("participant")
        except Exception as exc:
            participants[address] = {"error": str(exc)}
    write_json(DATA / "participants_by_address.json", participants)


if __name__ == "__main__":
    main()
