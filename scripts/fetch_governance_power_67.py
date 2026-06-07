#!/usr/bin/env python3
import base64
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from env_utils import gonka_api_source_label, gonka_api_url, gonka_rpc_source_label, gonka_rpc_url


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = DATA / "governance_power_67"
RPC_NODE = gonka_rpc_url()
API_NODE = gonka_api_url()
PROPOSAL_ID = 67
VOTING_END_TIME = "2026-06-05T22:09:02.699803591Z"
BOUNDARY_HEIGHTS = [4_433_308, 4_433_309]
OPTION_LABELS = {1: "yes", 2: "abstain", 3: "no", 4: "no_with_veto"}


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


def as_text(value):
    try:
        return value.decode()
    except UnicodeDecodeError:
        return ""


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


def proposal_request_hex():
    return "0x0843"


def abci_query(path, height, data_hex=""):
    params = {"path": f'"{path}"', "height": str(height)}
    if data_hex:
        params["data"] = data_hex
    query = urllib.parse.urlencode(params)
    return rpc_get(f"/abci_query?{query}", 60)


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


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    raw_dir = OUT / "raw"
    raw_dir.mkdir(exist_ok=True)

    proposal = read_json(DATA / "proposal_67.json")["proposal"]
    tx_votes = read_json(DATA / "proposal_67_tx_search.json")["result"]["txs"]

    blocks = {}
    for height in BOUNDARY_HEIGHTS:
        wrapper = rpc_get(f"/block?height={height}", 60)
        blocks[height] = wrapper
        write_json(raw_dir / f"block_{height}.json", wrapper)

    archive = {}
    for height in BOUNDARY_HEIGHTS:
        archive[height] = {
            "proposal": abci_query("/cosmos.gov.v1.Query/Proposal", height, proposal_request_hex()),
            "votes": abci_query("/cosmos.gov.v1.Query/Votes", height, proposal_request_hex()),
            "tally": abci_query("/cosmos.gov.v1.Query/TallyResult", height, proposal_request_hex()),
            "validators": abci_query("/cosmos.staking.v1beta1.Query/Validators", height),
        }
        for key, wrapper in archive[height].items():
            write_json(raw_dir / f"abci_{height}_{key}.json", wrapper)

    rest_probes = {}
    for height in BOUNDARY_HEIGHTS:
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

    end_before = block_summary(blocks[4_433_308])
    end_after = block_summary(blocks[4_433_309])
    decoded_votes = decode_votes(response_value(archive[4_433_308]["votes"]))
    decoded_votes_after_end = decode_votes(response_value(archive[4_433_309]["votes"]))
    decoded_tally = decode_tally_result(response_value(archive[4_433_308]["tally"]))
    decoded_tally_after_end = decode_tally_result(response_value(archive[4_433_309]["tally"]))
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

    per_voter_power = [
        {
            "voter": voter,
            "votingPower": None,
            "votingPowerSource": "unknown",
            "reason": "Archive gov Votes stores vote options, not per-voter power. Aggregate TallyResult is exact; historical REST gov/staking probes failed; chain-specific voting-power calculator/API is still required.",
        }
        for voter in sorted(voter_set)
    ]

    summary = {
        "proposalId": PROPOSAL_ID,
        "votingEndTime": VOTING_END_TIME,
        "lastBlockBeforeVotingEnd": end_before,
        "firstBlockAfterVotingEnd": end_after,
        "archiveSource": gonka_rpc_source_label(),
        "apiSource": gonka_api_source_label(),
        "archiveGovProposalCode": response_code(archive[4_433_308]["proposal"]),
        "archiveGovVotesCode": response_code(archive[4_433_308]["votes"]),
        "archiveGovTallyCode": response_code(archive[4_433_308]["tally"]),
        "archiveStakingValidatorsCode": response_code(archive[4_433_308]["validators"]),
        "decodedGovVotesCount": len(decoded_votes),
        "decodedGovVotesBeforeEndCount": len(decoded_votes),
        "decodedGovVotesAfterEndCount": len(decoded_votes_after_end),
        "txSearchUniqueVotersCount": len(tx_voter_set),
        "govVotesMatchTxSearchVoters": voter_set == tx_voter_set,
        "decodedTally": decoded_tally,
        "decodedTallyAfterEnd": decoded_tally_after_end,
        "finalTally": final_tally,
        "decodedTallyMatchesFinalTally": decoded_tally == final_tally,
        "decodedTallyAfterEndMatchesFinalTally": decoded_tally_after_end == final_tally,
        "historicalRestAvailable": False,
        "perVoterPowerStatus": "unknown",
        "perVoterPowerReason": "Exact aggregate tally and gov vote set are available from archive abci_query. Exact per-voter governance power is not exposed in gov Votes/TallyResult and was not derived from inference epoch weights.",
        "restProbeStatuses": {key: {"status": value.get("status"), "error": value.get("error")} for key, value in rest_probes.items()},
        "dashboardProbeStatus": {"status": dashboard_probe.get("status"), "error": dashboard_probe.get("error")},
        "generatedAt": datetime.now(timezone.utc).isoformat(),
    }

    write_json(
        OUT / "governance_power_67.json",
        {
            "summary": summary,
            "archiveGovVotes": decoded_votes,
            "perVoterPower": per_voter_power,
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
        f"- Voting end time: {VOTING_END_TIME}",
        f"- Last block before voting end: {end_before['height']} at {end_before['time']}",
        f"- First block after voting end: {end_after['height']} at {end_after['time']}",
        f"- Archive gov votes decoded: {len(decoded_votes)}",
        f"- Archive gov votes decoded after first post-end block: {len(decoded_votes_after_end)}",
        f"- Tx search unique voters: {len(tx_voter_set)}",
        f"- Archive gov voters match tx_search voters: {voter_set == tx_voter_set}",
        f"- Archive aggregate tally: {decoded_tally}",
        f"- Archive aggregate tally after first post-end block: {decoded_tally_after_end}",
        f"- Final proposal tally: {final_tally}",
        f"- Archive tally matches final proposal tally: {decoded_tally == final_tally}",
        f"- Per-voter governance power status: {summary['perVoterPowerStatus']}",
        "",
        "Per-voter governance power is not inferred from inference epoch weights. Archive gov Votes stores voter options, not exact per-voter power. At the first post-end block, gov Votes is empty while TallyResult remains final, so the investigation uses the last pre-end gov Votes snapshot plus the final aggregate TallyResult. Historical REST gov/staking probes failed for the boundary heights, and the standard staking validator response does not by itself provide Gonka's chain-specific governance power calculation.",
        "",
        "Raw evidence is saved under `data/governance_power_67/raw/` with the archive RPC source redacted as `GONKA_RPC_URL`.",
    ]
    (reports / "governance_power_67.md").write_text("\n".join(report_lines) + "\n")
    print(f"Wrote {OUT / 'governance_power_67.json'}")
    print(f"Votes: {len(decoded_votes)}; tally matches: {summary['decodedTallyMatchesFinalTally']}; per-voter power: {summary['perVoterPowerStatus']}")


if __name__ == "__main__":
    main()
