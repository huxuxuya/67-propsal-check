#!/usr/bin/env python3
import base64
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from decimal import Decimal, ROUND_DOWN, getcontext
from pathlib import Path

from env_utils import gonka_api_source_label, gonka_api_url, gonka_rpc_source_label, gonka_rpc_url


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = DATA / "governance_power_67"
RPC_NODE = gonka_rpc_url()
API_NODE = gonka_api_url()
PROPOSAL_ID = 67
VOTING_START_TIME = "2026-06-03T22:09:02.699803591Z"
VOTING_END_TIME = "2026-06-05T22:09:02.699803591Z"
OPTION_LABELS = {1: "yes", 2: "abstain", 3: "no", 4: "no_with_veto"}
BONDED_STATUS = 3
PAGE_LIMIT = 500

getcontext().prec = 80

BECH32_CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def read_json(path):
    with path.open() as f:
        return json.load(f)


def fetch_json(url, source_url, timeout=30, headers=None):
    try:
        request = urllib.request.Request(url, headers=headers or {})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode()
        return {
            "url": source_url,
            "status": response.status,
            "json": json.loads(body),
            "error": "",
            "fetchedAt": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as exc:
        return {
            "url": source_url,
            "status": getattr(exc, "code", None),
            "json": None,
            "error": type(exc).__name__,
            "fetchedAt": datetime.now(timezone.utc).isoformat(),
        }


def fetch_text(url, source_url, timeout=30):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            body = response.read().decode(errors="replace")
        return {
            "url": source_url,
            "status": response.status,
            "text": body,
            "error": "",
            "fetchedAt": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as exc:
        return {
            "url": source_url,
            "status": getattr(exc, "code", None),
            "text": "",
            "error": type(exc).__name__,
            "fetchedAt": datetime.now(timezone.utc).isoformat(),
        }


def rpc_get(path, timeout=30):
    return fetch_json(f"{RPC_NODE}{path}", f"{gonka_rpc_source_label()}{path}", timeout)


def api_get(path, timeout=30, headers=None):
    return fetch_json(f"{API_NODE}{path}", f"{gonka_api_source_label()}{path}", timeout, headers)


def read_varint(buf, pos):
    shift = 0
    result = 0
    while True:
        byte = buf[pos]
        pos += 1
        result |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return result, pos
        shift += 7


def parse_fields(buf):
    pos = 0
    fields = []
    while pos < len(buf):
        key, pos = read_varint(buf, pos)
        field_no = key >> 3
        wire_type = key & 0x07
        if wire_type == 0:
            value, pos = read_varint(buf, pos)
        elif wire_type == 1:
            value = buf[pos : pos + 8]
            pos += 8
        elif wire_type == 2:
            length, pos = read_varint(buf, pos)
            value = buf[pos : pos + length]
            pos += length
        elif wire_type == 5:
            value = buf[pos : pos + 4]
            pos += 4
        else:
            break
        fields.append((field_no, wire_type, value))
    return fields


def encode_varint(value):
    out = []
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            out.append(byte | 0x80)
        else:
            out.append(byte)
            break
    return bytes(out)


def proto_key(field_no, wire_type):
    return encode_varint((field_no << 3) | wire_type)


def proto_bytes(field_no, value):
    return proto_key(field_no, 2) + encode_varint(len(value)) + value


def proto_varint(field_no, value):
    return proto_key(field_no, 0) + encode_varint(value)


def hex_request(data):
    return "0x" + data.hex()


def page_request(limit=PAGE_LIMIT, next_key=b""):
    data = b""
    if next_key:
        data += proto_bytes(1, next_key)
    data += proto_varint(3, limit)
    return data


def validators_request_hex(next_key=b""):
    return hex_request(proto_bytes(1, b"BOND_STATUS_BONDED") + proto_bytes(2, page_request(PAGE_LIMIT, next_key)))


def delegator_delegations_request_hex(delegator, next_key=b""):
    return hex_request(proto_bytes(1, delegator.encode()) + proto_bytes(2, page_request(100, next_key)))


def as_text(value):
    try:
        return value.decode()
    except UnicodeDecodeError:
        return ""


def bech32_polymod(values):
    generators = [0x3B6A57B2, 0x26508E6D, 0x1EA119FA, 0x3D4233DD, 0x2A1462B3]
    chk = 1
    for value in values:
        top = chk >> 25
        chk = ((chk & 0x1FFFFFF) << 5) ^ value
        for i, generator in enumerate(generators):
            if (top >> i) & 1:
                chk ^= generator
    return chk


def bech32_hrp_expand(hrp):
    return [ord(char) >> 5 for char in hrp] + [0] + [ord(char) & 31 for char in hrp]


def convert_bits(data, from_bits, to_bits, pad=True):
    acc = 0
    bits = 0
    ret = []
    maxv = (1 << to_bits) - 1
    for value in data:
        acc = (acc << from_bits) | value
        bits += from_bits
        while bits >= to_bits:
            bits -= to_bits
            ret.append((acc >> bits) & maxv)
    if pad and bits:
        ret.append((acc << (to_bits - bits)) & maxv)
    return ret


def bech32_address_bytes(address):
    value = address.strip().lower()
    pos = value.rfind("1")
    if pos <= 0:
        return b""
    hrp = value[:pos]
    data = [BECH32_CHARSET.index(char) for char in value[pos + 1 :]]
    if bech32_polymod(bech32_hrp_expand(hrp) + data) != 1:
        return b""
    return bytes(convert_bits(data[:-6], 5, 8, False))


def account_from_valoper(operator_address):
    if not operator_address.startswith("gonkavaloper"):
        return ""
    return "gonka" + operator_address[len("gonkavaloper") :]


def parse_decimal(value):
    if value in (None, ""):
        return Decimal(0)
    return Decimal(str(value))


def decode_tally_result(value_b64):
    raw = base64.b64decode(value_b64)
    result = {}
    for field_no, wire_type, value in parse_fields(raw):
        if field_no != 1 or wire_type != 2:
            continue
        for inner_no, inner_wire, inner_value in parse_fields(value):
            if inner_wire == 2:
                result[{1: "yes", 2: "abstain", 3: "no", 4: "no_with_veto"}.get(inner_no, str(inner_no))] = int(as_text(inner_value) or 0)
    return result


def decode_votes(value_b64):
    raw = base64.b64decode(value_b64)
    votes = []
    for field_no, wire_type, value in parse_fields(raw):
        if field_no != 1 or wire_type != 2:
            continue
        vote = {"proposalId": None, "voter": "", "options": []}
        for inner_no, inner_wire, inner_value in parse_fields(value):
            if inner_no == 1 and inner_wire == 0:
                vote["proposalId"] = inner_value
            elif inner_no == 2 and inner_wire == 2:
                vote["voter"] = as_text(inner_value)
            elif inner_no == 4 and inner_wire == 2:
                option = {}
                for opt_no, opt_wire, opt_value in parse_fields(inner_value):
                    if opt_no == 1 and opt_wire == 0:
                        option["option"] = OPTION_LABELS.get(opt_value, str(opt_value))
                    elif opt_no == 2 and opt_wire == 2:
                        option["weight"] = as_text(opt_value)
                if option:
                    vote["options"].append(option)
        if vote["voter"]:
            votes.append(vote)
    return votes


def decode_page_next_key(value):
    for field_no, wire_type, inner_value in parse_fields(value):
        if field_no == 1 and wire_type == 2:
            return inner_value
    return b""


def decode_validator(value):
    validator = {
        "operatorAddress": "",
        "accountAddress": "",
        "status": 0,
        "tokens": "0",
        "delegatorShares": "0",
        "moniker": "",
    }
    for field_no, wire_type, inner_value in parse_fields(value):
        if field_no == 1 and wire_type == 2:
            validator["operatorAddress"] = as_text(inner_value)
            validator["accountAddress"] = account_from_valoper(validator["operatorAddress"])
        elif field_no == 4 and wire_type == 0:
            validator["status"] = inner_value
        elif field_no == 5 and wire_type == 2:
            validator["tokens"] = as_text(inner_value)
        elif field_no == 6 and wire_type == 2:
            validator["delegatorShares"] = as_text(inner_value)
        elif field_no == 7 and wire_type == 2:
            for desc_no, desc_wire, desc_value in parse_fields(inner_value):
                if desc_no == 1 and desc_wire == 2:
                    validator["moniker"] = as_text(desc_value)
    return validator


def decode_validators(value_b64):
    raw = base64.b64decode(value_b64)
    validators = []
    next_key = b""
    for field_no, wire_type, value in parse_fields(raw):
        if field_no == 1 and wire_type == 2:
            validators.append(decode_validator(value))
        elif field_no == 2 and wire_type == 2:
            next_key = decode_page_next_key(value)
    return validators, next_key


def decode_delegation_response(value):
    row = {
        "delegatorAddress": "",
        "validatorAddress": "",
        "shares": "0",
        "balanceDenom": "",
        "balanceAmount": "0",
    }
    for field_no, wire_type, inner_value in parse_fields(value):
        if field_no == 1 and wire_type == 2:
            for del_no, del_wire, del_value in parse_fields(inner_value):
                if del_no == 1 and del_wire == 2:
                    row["delegatorAddress"] = as_text(del_value)
                elif del_no == 2 and del_wire == 2:
                    row["validatorAddress"] = as_text(del_value)
                elif del_no == 3 and del_wire == 2:
                    row["shares"] = as_text(del_value)
        elif field_no == 2 and wire_type == 2:
            for coin_no, coin_wire, coin_value in parse_fields(inner_value):
                if coin_no == 1 and coin_wire == 2:
                    row["balanceDenom"] = as_text(coin_value)
                elif coin_no == 2 and coin_wire == 2:
                    row["balanceAmount"] = as_text(coin_value)
    return row


def decode_delegator_delegations(value_b64):
    raw = base64.b64decode(value_b64)
    delegations = []
    next_key = b""
    for field_no, wire_type, value in parse_fields(raw):
        if field_no == 1 and wire_type == 2:
            delegations.append(decode_delegation_response(value))
        elif field_no == 2 and wire_type == 2:
            next_key = decode_page_next_key(value)
    return delegations, next_key


def proposal_request_hex():
    return "0x0843"


def abci_query(path, height, data_hex=""):
    params = {"path": f'"{path}"', "height": str(height)}
    if data_hex:
        params["data"] = data_hex
    query = urllib.parse.urlencode(params)
    return rpc_get(f"/abci_query?{query}", 60)


def fetch_paginated_validators(height, raw_dir):
    validators = []
    raw_files = []
    next_key = b""
    page = 1
    while True:
        wrapper = abci_query("/cosmos.staking.v1beta1.Query/Validators", height, validators_request_hex(next_key))
        raw_path = raw_dir / f"abci_{height}_validators_bonded_page_{page}.json"
        write_json(raw_path, wrapper)
        raw_files.append(raw_path.name)
        decoded, next_key = decode_validators(response_value(wrapper))
        validators.extend(decoded)
        if not next_key:
            break
        page += 1
    return validators, raw_files


def fetch_voter_delegations(voters, height, raw_dir):
    delegations_by_voter = {}
    raw_files = []
    for voter in sorted(voters):
        delegations = []
        next_key = b""
        page = 1
        while True:
            wrapper = abci_query("/cosmos.staking.v1beta1.Query/DelegatorDelegations", height, delegator_delegations_request_hex(voter, next_key))
            raw_path = raw_dir / f"abci_{height}_delegations_{voter}_page_{page}.json"
            write_json(raw_path, wrapper)
            raw_files.append(raw_path.name)
            decoded, next_key = decode_delegator_delegations(response_value(wrapper))
            delegations.extend(decoded)
            if not next_key:
                break
            page += 1
        delegations_by_voter[voter] = delegations
    return delegations_by_voter, raw_files


def response_value(wrapper):
    return (((wrapper.get("json") or {}).get("result") or {}).get("response") or {}).get("value") or ""


def response_code(wrapper):
    return (((wrapper.get("json") or {}).get("result") or {}).get("response") or {}).get("code", None)


def block_summary(wrapper):
    header = ((((wrapper.get("json") or {}).get("result") or {}).get("block") or {}).get("header") or {})
    return {
        "height": int(header.get("height") or 0),
        "time": header.get("time", ""),
        "hash": (((wrapper.get("json") or {}).get("result") or {}).get("block_id") or {}).get("hash", ""),
    }


def parse_block_time(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def find_boundary_heights(target_time_iso, low=4_000_000, high=4_500_000):
    target = parse_block_time(target_time_iso)
    cache = {}

    def get_block(height):
        if height not in cache:
            cache[height] = rpc_get(f"/block?height={height}", 60)
        return cache[height]

    while low < high:
        mid = (low + high + 1) // 2
        summary = block_summary(get_block(mid))
        if parse_block_time(summary["time"]) <= target:
            low = mid
        else:
            high = mid - 1
    before = low
    after = before + 1
    return before, after, {before: get_block(before), after: get_block(after)}


def decimal_to_int_string(value):
    return str(int(value.to_integral_value(rounding=ROUND_DOWN)))


def decimal_to_number(value):
    if value == value.to_integral_value(rounding=ROUND_DOWN):
        return int(value)
    return float(value)


def calculate_chain_like_power(votes, validators, delegations_by_voter, height_label="last pre-end archive height"):
    validators_by_operator = {}
    validators_by_account_bytes = {}
    for validator in validators:
        tokens = parse_decimal(validator.get("tokens"))
        shares = parse_decimal(validator.get("delegatorShares"))
        if validator.get("status") != BONDED_STATUS or tokens <= 0 or shares <= 0:
            continue
        item = {
            **validator,
            "tokensDecimal": tokens,
            "sharesDecimal": shares,
            "deductionsDecimal": Decimal(0),
            "voteOptions": [],
        }
        validators_by_operator[validator["operatorAddress"]] = item
        address_bytes = bech32_address_bytes(validator["operatorAddress"])
        if address_bytes:
            validators_by_account_bytes[address_bytes] = item

    results = {label: Decimal(0) for label in ["yes", "abstain", "no", "no_with_veto"]}
    voter_rows = {}
    vote_by_voter = {vote["voter"]: vote for vote in votes}

    for vote in votes:
        voter = vote["voter"]
        voter_bytes = bech32_address_bytes(voter)
        validator = validators_by_account_bytes.get(voter_bytes)
        if validator:
            validator["voteOptions"] = vote["options"]

        voter_power = Decimal(0)
        delegation_rows = []
        for delegation in delegations_by_voter.get(voter, []):
            validator = validators_by_operator.get(delegation.get("validatorAddress"))
            if not validator:
                continue
            shares = parse_decimal(delegation.get("shares"))
            voting_power = shares * validator["tokensDecimal"] / validator["sharesDecimal"]
            validator["deductionsDecimal"] += shares
            voter_power += voting_power
            delegation_rows.append(
                {
                    **delegation,
                    "votingPower": decimal_to_number(voting_power),
                }
            )
            for option in vote["options"]:
                results[option["option"]] += voting_power * parse_decimal(option["weight"])

        voter_rows[voter] = {
            "voter": voter,
            "votingPowerDecimal": voter_power,
            "delegations": delegation_rows,
            "validatorOperatorAddress": validator["operatorAddress"] if validator else "",
            "validatorSelfVote": bool(validator),
        }

    validator_vote_rows = []
    for validator in validators_by_operator.values():
        if not validator["voteOptions"]:
            continue
        remaining_shares = validator["sharesDecimal"] - validator["deductionsDecimal"]
        voting_power = remaining_shares * validator["tokensDecimal"] / validator["sharesDecimal"]
        if voting_power > 0:
            for option in validator["voteOptions"]:
                results[option["option"]] += voting_power * parse_decimal(option["weight"])
        validator_vote_rows.append(
            {
                "operatorAddress": validator["operatorAddress"],
                "accountAddress": validator["accountAddress"],
                "tokens": int(validator["tokensDecimal"]),
                "delegatorShares": str(validator["sharesDecimal"]),
                "deductedShares": str(validator["deductionsDecimal"]),
                "remainingVotingPower": decimal_to_number(voting_power),
            }
        )

    per_voter_power = []
    for voter in sorted(vote_by_voter):
        row = voter_rows.get(voter, {"votingPowerDecimal": Decimal(0), "delegations": []})
        power = row["votingPowerDecimal"]
        if power > 0:
            source = "archive_staking_delegations_chain_like"
            reason = f"Computed from archive Query/Validators and Query/DelegatorDelegations at {height_label} using Gonka SDK gov tally logic."
            power_value = decimal_to_number(power)
        else:
            source = "archive_staking_no_voting_power"
            reason = f"No bonded validator/delegation voting power found for this voter at {height_label}."
            power_value = 0
        per_voter_power.append(
            {
                "voter": voter,
                "votingPower": power_value,
                "votingPowerExact": str(power),
                "votingPowerSource": source,
                "reason": reason,
                "delegations": row.get("delegations", []),
                "validatorOperatorAddress": row.get("validatorOperatorAddress", ""),
                "validatorSelfVote": row.get("validatorSelfVote", False),
            }
        )

    return {
        "resultsDecimal": {key: str(value) for key, value in results.items()},
        "resultsTruncated": {key: int(value.to_integral_value(rounding=ROUND_DOWN)) for key, value in results.items()},
        "totalVoterPower": decimal_to_number(sum(results.values())),
        "perVoterPower": per_voter_power,
        "bondedValidatorsCount": len(validators_by_operator),
        "bondedValidatorsNonzeroPowerTotal": int(sum((row["tokensDecimal"] for row in validators_by_operator.values()), Decimal(0))),
        "validatorVotes": sorted(validator_vote_rows, key=lambda row: row["accountAddress"]),
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    raw_dir = OUT / "raw"
    raw_dir.mkdir(exist_ok=True)

    proposal = read_json(DATA / "proposal_67.json")["proposal"]
    tx_votes = read_json(DATA / "proposal_67_tx_search.json")["result"]["txs"]

    start_before_height, start_after_height, start_blocks = find_boundary_heights(VOTING_START_TIME)
    end_before_height, end_after_height, end_blocks = find_boundary_heights(VOTING_END_TIME)
    boundary_heights = [start_before_height, start_after_height, end_before_height, end_after_height]

    blocks = {**start_blocks, **end_blocks}
    for height, wrapper in blocks.items():
        write_json(raw_dir / f"block_{height}.json", wrapper)

    archive = {}
    for height in boundary_heights:
        archive[height] = {
            "proposal": abci_query("/cosmos.gov.v1.Query/Proposal", height, proposal_request_hex()),
            "votes": abci_query("/cosmos.gov.v1.Query/Votes", height, proposal_request_hex()),
            "tally": abci_query("/cosmos.gov.v1.Query/TallyResult", height, proposal_request_hex()),
            "validators": abci_query("/cosmos.staking.v1beta1.Query/Validators", height),
        }
        for key, wrapper in archive[height].items():
            write_json(raw_dir / f"abci_{height}_{key}.json", wrapper)

    rest_probes = {}
    for height in boundary_heights:
        headers = {"x-cosmos-block-height": str(height)}
        rest_probes[f"proposal_{height}"] = api_get(f"/chain-api/cosmos/gov/v1/proposals/{PROPOSAL_ID}", 30, headers)
        rest_probes[f"votes_{height}"] = api_get(f"/chain-api/cosmos/gov/v1/proposals/{PROPOSAL_ID}/votes?pagination.limit=100", 30, headers)
        rest_probes[f"validators_{height}"] = api_get("/chain-api/cosmos/staking/v1beta1/validators?pagination.limit=5", 30, headers)
    rest_probes["votes_latest"] = api_get(f"/chain-api/cosmos/gov/v1/proposals/{PROPOSAL_ID}/votes?pagination.limit=100", 30)
    rest_probes["governance_pricing"] = api_get("/v1/governance/pricing", 30)
    write_json(raw_dir / "rest_probes.json", rest_probes)

    dashboard_probe = fetch_text(
        f"{API_NODE}/dashboard/gonka/gov/{PROPOSAL_ID}",
        f"{gonka_api_source_label()}/dashboard/gonka/gov/{PROPOSAL_ID}",
        30,
    )
    write_json(raw_dir / "dashboard_gov_67_html.json", dashboard_probe)

    start_before = block_summary(blocks[start_before_height])
    start_after = block_summary(blocks[start_after_height])
    end_before = block_summary(blocks[end_before_height])
    end_after = block_summary(blocks[end_after_height])
    decoded_votes_start_before = decode_votes(response_value(archive[start_before_height]["votes"]))
    decoded_votes_start_after = decode_votes(response_value(archive[start_after_height]["votes"]))
    decoded_votes = decode_votes(response_value(archive[end_before_height]["votes"]))
    decoded_votes_after_end = decode_votes(response_value(archive[end_after_height]["votes"]))
    decoded_tally_start_before = decode_tally_result(response_value(archive[start_before_height]["tally"]))
    decoded_tally_start_after = decode_tally_result(response_value(archive[start_after_height]["tally"]))
    decoded_tally = decode_tally_result(response_value(archive[end_before_height]["tally"]))
    decoded_tally_after_end = decode_tally_result(response_value(archive[end_after_height]["tally"]))
    final_tally = {
        "yes": int(proposal["final_tally_result"]["yes_count"]),
        "abstain": int(proposal["final_tally_result"]["abstain_count"]),
        "no": int(proposal["final_tally_result"]["no_count"]),
        "no_with_veto": int(proposal["final_tally_result"]["no_with_veto_count"]),
    }
    voter_set = {vote["voter"] for vote in decoded_votes}
    tx_voter_set = set()
    for tx in tx_votes:
        for event in tx["tx_result"]["events"]:
            if event.get("type") != "proposal_vote":
                continue
            for attr in event.get("attributes", []):
                if attr.get("key") == "voter":
                    tx_voter_set.add(attr["value"])

    bonded_validators, validator_raw_files = fetch_paginated_validators(end_before_height, raw_dir)
    delegations_by_voter, delegation_raw_files = fetch_voter_delegations(voter_set, end_before_height, raw_dir)
    write_json(raw_dir / f"decoded_bonded_validators_{end_before_height}.json", bonded_validators)
    write_json(raw_dir / f"decoded_voter_delegations_{end_before_height}.json", delegations_by_voter)

    start_bonded_validators, start_validator_raw_files = fetch_paginated_validators(start_before_height, raw_dir)
    start_delegations_by_voter, start_delegation_raw_files = fetch_voter_delegations(voter_set, start_before_height, raw_dir)
    write_json(raw_dir / f"decoded_bonded_validators_{start_before_height}.json", start_bonded_validators)
    write_json(raw_dir / f"decoded_voter_delegations_{start_before_height}.json", start_delegations_by_voter)

    chain_like_power = calculate_chain_like_power(decoded_votes, bonded_validators, delegations_by_voter, f"block {end_before_height}, last block before voting end")
    start_chain_like_power = calculate_chain_like_power(decoded_votes, start_bonded_validators, start_delegations_by_voter, f"block {start_before_height}, last block before voting start")
    chain_like_tally_matches_final = chain_like_power["resultsTruncated"] == final_tally
    per_voter_power = chain_like_power["perVoterPower"]
    start_power_by_voter = {row["voter"]: row for row in start_chain_like_power["perVoterPower"]}
    window_power = []
    for row in per_voter_power:
        start_row = start_power_by_voter.get(row["voter"], {})
        start_power = start_row.get("votingPower", 0)
        end_power = row.get("votingPower", 0)
        if start_power and end_power:
            status = "power_at_start_and_end"
        elif start_power and not end_power:
            status = "power_at_start_only"
        elif end_power and not start_power:
            status = "power_at_end_only"
        else:
            status = "zero_at_start_and_end"
        window_power.append(
            {
                "voter": row["voter"],
                "startVotingPower": start_power,
                "startVotingPowerExact": start_row.get("votingPowerExact", "0"),
                "startVotingPowerSource": start_row.get("votingPowerSource", ""),
                "endVotingPower": end_power,
                "endVotingPowerExact": row.get("votingPowerExact", "0"),
                "endVotingPowerSource": row.get("votingPowerSource", ""),
                "windowPowerStatus": status,
                "startDelegations": start_row.get("delegations", []),
                "endDelegations": row.get("delegations", []),
            }
        )

    summary = {
        "proposalId": PROPOSAL_ID,
        "votingStartTime": VOTING_START_TIME,
        "votingEndTime": VOTING_END_TIME,
        "lastBlockBeforeVotingStart": start_before,
        "firstBlockAfterVotingStart": start_after,
        "lastBlockBeforeVotingEnd": end_before,
        "firstBlockAfterVotingEnd": end_after,
        "archiveSource": gonka_rpc_source_label(),
        "apiSource": gonka_api_source_label(),
        "archiveGovProposalCode": response_code(archive[end_before_height]["proposal"]),
        "archiveGovVotesCode": response_code(archive[end_before_height]["votes"]),
        "archiveGovTallyCode": response_code(archive[end_before_height]["tally"]),
        "archiveStakingValidatorsCode": response_code(archive[end_before_height]["validators"]),
        "decodedGovVotesBeforeStartCount": len(decoded_votes_start_before),
        "decodedGovVotesAfterStartCount": len(decoded_votes_start_after),
        "decodedGovVotesCount": len(decoded_votes),
        "decodedGovVotesBeforeEndCount": len(decoded_votes),
        "decodedGovVotesAfterEndCount": len(decoded_votes_after_end),
        "txSearchUniqueVotersCount": len(tx_voter_set),
        "govVotesMatchTxSearchVoters": voter_set == tx_voter_set,
        "decodedTallyBeforeStart": decoded_tally_start_before,
        "decodedTallyAfterStart": decoded_tally_start_after,
        "decodedTally": decoded_tally,
        "decodedTallyAfterEnd": decoded_tally_after_end,
        "finalTally": final_tally,
        "decodedTallyMatchesFinalTally": decoded_tally == final_tally,
        "decodedTallyAfterEndMatchesFinalTally": decoded_tally_after_end == final_tally,
        "chainLikeTallyDecimal": chain_like_power["resultsDecimal"],
        "chainLikeTallyTruncated": chain_like_power["resultsTruncated"],
        "chainLikeTallyMatchesFinalTally": chain_like_tally_matches_final,
        "chainLikeTotalVoterPower": chain_like_power["totalVoterPower"],
        "startChainLikeTallyDecimalForFinalVoters": start_chain_like_power["resultsDecimal"],
        "startChainLikeTallyTruncatedForFinalVoters": start_chain_like_power["resultsTruncated"],
        "startChainLikeTotalFinalVoterPower": start_chain_like_power["totalVoterPower"],
        "archiveBondedValidatorsCount": chain_like_power["bondedValidatorsCount"],
        "archiveBondedValidatorsNonzeroPowerTotal": chain_like_power["bondedValidatorsNonzeroPowerTotal"],
        "votersWithArchiveVotingPowerCount": sum(1 for row in per_voter_power if row["votingPower"]),
        "votersWithStartVotingPowerCount": sum(1 for row in window_power if row["startVotingPower"]),
        "votersWithEndVotingPowerCount": sum(1 for row in window_power if row["endVotingPower"]),
        "votersZeroAtStartAndEndCount": sum(1 for row in window_power if row["windowPowerStatus"] == "zero_at_start_and_end"),
        "votersPowerAtStartOnlyCount": sum(1 for row in window_power if row["windowPowerStatus"] == "power_at_start_only"),
        "votersPowerAtEndOnlyCount": sum(1 for row in window_power if row["windowPowerStatus"] == "power_at_end_only"),
        "validatorRawPageFiles": validator_raw_files,
        "startValidatorRawPageFiles": start_validator_raw_files,
        "delegationRawPageFilesCount": len(delegation_raw_files),
        "startDelegationRawPageFilesCount": len(start_delegation_raw_files),
        "historicalRestAvailable": False,
        "perVoterPowerStatus": "exact_chain_like" if chain_like_tally_matches_final else "derived_mismatch",
        "perVoterPowerReason": "Per-voter governance voting power is computed from archive staking validators and delegations at the last pre-end block using Gonka SDK gov tally logic. The decimal results are truncated by Cosmos SDK TallyResult serialization; truncated values match the final on-chain tally." if chain_like_tally_matches_final else "Chain-like archive staking/delegation calculation did not match final on-chain tally; treat per-voter power as diagnostic only.",
        "restProbeStatuses": {key: {"status": value.get("status"), "error": value.get("error")} for key, value in rest_probes.items()},
        "dashboardProbeStatus": {"status": dashboard_probe.get("status"), "error": dashboard_probe.get("error")},
        "generatedAt": datetime.now(timezone.utc).isoformat(),
    }

    write_json(
        OUT / "governance_power_67.json",
        {
            "summary": summary,
            "archiveGovVotes": decoded_votes,
            "archiveBondedValidators": bonded_validators,
            "archiveVoterDelegations": delegations_by_voter,
            "startArchiveBondedValidators": start_bonded_validators,
            "startArchiveVoterDelegations": start_delegations_by_voter,
            "chainLikePower": {
                "resultsDecimal": chain_like_power["resultsDecimal"],
                "resultsTruncated": chain_like_power["resultsTruncated"],
                "totalVoterPower": chain_like_power["totalVoterPower"],
                "validatorVotes": chain_like_power["validatorVotes"],
            },
            "startChainLikePowerForFinalVoters": {
                "resultsDecimal": start_chain_like_power["resultsDecimal"],
                "resultsTruncated": start_chain_like_power["resultsTruncated"],
                "totalVoterPower": start_chain_like_power["totalVoterPower"],
                "validatorVotes": start_chain_like_power["validatorVotes"],
            },
            "perVoterPower": per_voter_power,
            "windowVoterPower": window_power,
        },
    )
    write_json(OUT / "manifest.json", {"summary": summary, "rawFiles": sorted(str(path.relative_to(OUT)) for path in raw_dir.glob("*.json"))})
    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)
    report_lines = [
        "# Proposal 67 Governance Power Evidence",
        "",
        "This report separates on-chain governance evidence from inference epoch timing.",
        "",
        f"- Voting start time: {VOTING_START_TIME}",
        f"- Last block before voting start: {start_before['height']} at {start_before['time']}",
        f"- First block after voting start: {start_after['height']} at {start_after['time']}",
        f"- Voting end time: {VOTING_END_TIME}",
        f"- Last block before voting end: {end_before['height']} at {end_before['time']}",
        f"- First block after voting end: {end_after['height']} at {end_after['time']}",
        f"- Archive gov votes decoded before voting start: {len(decoded_votes_start_before)}",
        f"- Archive gov votes decoded after first post-start block: {len(decoded_votes_start_after)}",
        f"- Archive gov votes decoded: {len(decoded_votes)}",
        f"- Archive gov votes decoded after first post-end block: {len(decoded_votes_after_end)}",
        f"- Tx search unique voters: {len(tx_voter_set)}",
        f"- Archive gov voters match tx_search voters: {voter_set == tx_voter_set}",
        f"- Archive aggregate tally: {decoded_tally}",
        f"- Archive aggregate tally after first post-end block: {decoded_tally_after_end}",
        f"- Final proposal tally: {final_tally}",
        f"- Archive tally matches final proposal tally: {decoded_tally == final_tally}",
        f"- Chain-like archive staking/delegation tally decimal: {chain_like_power['resultsDecimal']}",
        f"- Chain-like archive staking/delegation tally truncated: {chain_like_power['resultsTruncated']}",
        f"- Chain-like truncated tally matches final proposal tally: {chain_like_tally_matches_final}",
        f"- Chain-like start-window power for final voters: {start_chain_like_power['resultsTruncated']}",
        f"- Archive bonded validators with non-zero power: {chain_like_power['bondedValidatorsCount']}",
        f"- Voters with non-zero archive voting power: {summary['votersWithArchiveVotingPowerCount']}",
        f"- Voters with non-zero start-window power: {summary['votersWithStartVotingPowerCount']}",
        f"- Voters zero at both start and end snapshots: {summary['votersZeroAtStartAndEndCount']}",
        f"- Voters with power at start only: {summary['votersPowerAtStartOnlyCount']}",
        f"- Voters with power at end only: {summary['votersPowerAtEndOnlyCount']}",
        f"- Per-voter governance power status: {summary['perVoterPowerStatus']}",
        "",
        "Per-voter governance power is not inferred from inference epoch weights. The calculation follows the Gonka SDK gov tally path: collect all bonded validators with non-zero bonded tokens, apply each voter delegation as direct voter power, deduct voted delegator shares from validator self-votes, then add remaining validator voting power. Decimal weighted results are truncated by Cosmos SDK TallyResult serialization; the truncated result matches the final on-chain tally.",
        "",
        "Raw evidence is saved under `data/governance_power_67/raw/` with the archive RPC source redacted as `GONKA_RPC_URL`.",
    ]
    (reports / "governance_power_67.md").write_text("\n".join(report_lines) + "\n")
    print(f"Wrote {OUT / 'governance_power_67.json'}")
    print(f"Votes: {len(decoded_votes)}; tally matches: {summary['decodedTallyMatchesFinalTally']}; per-voter power: {summary['perVoterPowerStatus']}")


if __name__ == "__main__":
    main()
