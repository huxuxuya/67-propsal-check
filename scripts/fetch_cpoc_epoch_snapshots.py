#!/usr/bin/env python3
import argparse
import base64
import json
import os
import shutil
import subprocess
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from env_utils import gonka_api_url, gonka_rpc_url, load_dotenv


ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "upstream" / "gonka-kimi-restitution"
DATA = ROOT / "data"
OUT = DATA / "cpoc_epoch_snapshots"
DEFAULT_EPOCHS = list(range(265, 277))
DEFAULT_MODELS = [
    "moonshotai/Kimi-K2.6",
    "Qwen/Qwen3-235B-A22B-Instruct-2507-FP8",
]


def load_json(path):
    with path.open() as f:
        return json.load(f)


def default_api_node(rpc):
    load_dotenv()
    if os.environ.get("GONKA_API_URL"):
        return gonka_api_url()
    parsed = urllib.parse.urlparse(rpc)
    if parsed.hostname:
        return f"{parsed.scheme or 'http'}://{parsed.hostname}:8000"
    return gonka_api_url()


def inferenced_binary(required=False):
    configured = os.environ.get("INFERENCED_BINARY")
    if configured:
        return configured
    found = shutil.which("inferenced")
    if found:
        return found
    if required:
        raise SystemExit("inferenced binary not found; set INFERENCED_BINARY=/path/to/inferenced")
    return None


def load_upstream_epoch_group(epoch, snapshot=""):
    if epoch == 265 and snapshot:
        path = UPSTREAM / "e265" / f"epoch265_group_data_{snapshot}.json"
    else:
        path = UPSTREAM / f"e{epoch}" / f"epoch{epoch}_group_data.json"
    if not path.exists():
        return {}
    payload = load_json(path)
    if isinstance(payload, list):
        payload = payload[0] if payload else {}
    return payload.get("epoch_group_data") or payload


def epoch_bounds(epoch):
    current = load_upstream_epoch_group(epoch, "healthy" if epoch == 265 else "")
    next_group = load_upstream_epoch_group(epoch + 1)
    start = int(current.get("poc_start_block_height") or current.get("effective_block_height") or 0)
    if next_group.get("poc_start_block_height"):
        end = int(next_group["poc_start_block_height"]) - 1
    else:
        end = int(current.get("effective_block_height") or start)
    if not start or end < start:
        raise SystemExit(f"Cannot determine block range for epoch {epoch}")
    return start, end


def epoch_start_snapshot_height(epoch):
    group = load_upstream_epoch_group(epoch, "healthy" if epoch == 265 else "")
    return int(group.get("effective_block_height") or group.get("poc_start_block_height") or 0)


def epoch_group_id(epoch):
    group = load_upstream_epoch_group(epoch, "healthy" if epoch == 265 else "")
    group_id = group.get("epoch_group_id")
    if not group_id:
        raise SystemExit(f"Cannot determine epoch_group_id for epoch {epoch}")
    return str(group_id)


def configured_heights():
    path = DATA / "cpoc_checkpoint_heights.json"
    if not path.exists():
        return {}
    payload = load_json(path)
    raw_epochs = payload.get("epochs", payload)
    return {int(epoch): sorted({int(height) for height in heights}) for epoch, heights in raw_epochs.items()}


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
            raise ValueError(f"Unsupported protobuf wire type {wire_type}")
        yield field_no, wire_type, value


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


def proto_varint(field_no, value):
    return proto_key(field_no, 0) + encode_varint(value)


def proto_bytes(field_no, value):
    return proto_key(field_no, 2) + encode_varint(len(value)) + value


def as_text(value):
    try:
        return value.decode()
    except UnicodeDecodeError:
        return ""


def model_slug(model_id):
    return (
        model_id.replace("/", "__")
        .replace(":", "_")
        .replace(" ", "_")
    )


def run_query(binary, rpc, epoch, height):
    cmd = [
        binary,
        "query",
        "inference",
        "show-epoch-group-data",
        str(epoch),
        "--node",
        rpc,
        "--height",
        str(height),
        "-o",
        "json",
    ]
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def epoch_group_data_request_hex(epoch, model_id=""):
    payload = proto_varint(1, int(epoch))
    if model_id:
        payload += proto_bytes(2, model_id.encode())
    return "0x" + payload.hex()


def http_get_json(node, path, params=None, headers=None):
    query = f"?{urllib.parse.urlencode(params or {})}" if params else ""
    url = f"{node.rstrip('/')}/{path.lstrip('/')}{query}"
    request = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def block_search(rpc, query, page=1, per_page=100):
    return http_get_json(
        rpc,
        "block_search",
        {
            "query": json.dumps(query),
            "page": str(page),
            "per_page": str(per_page),
        },
    )


def abci_query(rpc, path, height, data_hex=""):
    params = {"path": f'"{path}"', "height": str(height)}
    if data_hex:
        params["data"] = data_hex
    return http_get_json(rpc, "abci_query", params)


def decode_decimal(value):
    row = {}
    for field_no, wire_type, inner_value in parse_fields(value):
        if field_no == 1 and wire_type == 2:
            row["value"] = as_text(inner_value)
    return row


def decode_ml_node_info(value):
    row = {}
    for field_no, wire_type, inner_value in parse_fields(value):
        if field_no == 1 and wire_type == 2:
            row["node_id"] = as_text(inner_value)
        elif field_no == 2 and wire_type == 0:
            row["throughput"] = str(inner_value)
        elif field_no == 3 and wire_type == 0:
            row["poc_weight"] = str(inner_value)
        elif field_no == 4 and wire_type == 0:
            row.setdefault("timeslot_allocation", []).append(bool(inner_value))
    return row


def decode_confirmation_weight_scale(value):
    row = {}
    for field_no, wire_type, inner_value in parse_fields(value):
        if field_no == 1 and wire_type == 2:
            row["model_id"] = as_text(inner_value)
        elif field_no == 2 and wire_type == 2:
            row["weight_scale_factor"] = decode_decimal(inner_value)
    return row


def decode_validation_weight(value):
    row = {"ml_nodes": []}
    for field_no, wire_type, inner_value in parse_fields(value):
        if field_no == 1 and wire_type == 2:
            row["member_address"] = as_text(inner_value)
        elif field_no == 2 and wire_type == 0:
            row["weight"] = str(inner_value)
        elif field_no == 3 and wire_type == 0:
            row["reputation"] = int(inner_value)
        elif field_no == 4 and wire_type == 2:
            row["ml_nodes"].append(decode_ml_node_info(inner_value))
        elif field_no == 5 and wire_type == 0:
            row["confirmation_weight"] = str(inner_value)
        elif field_no == 6 and wire_type == 0:
            row["voting_power"] = str(inner_value)
    return row


def decode_epoch_group_data(value):
    row = {"member_seed_signatures": [], "validation_weights": [], "sub_group_models": [], "confirmation_weight_scales": []}
    for field_no, wire_type, inner_value in parse_fields(value):
        if field_no == 1 and wire_type == 0:
            row["poc_start_block_height"] = str(inner_value)
        elif field_no == 2 and wire_type == 0:
            row["epoch_group_id"] = str(inner_value)
        elif field_no == 3 and wire_type == 2:
            row["epoch_policy"] = as_text(inner_value)
        elif field_no == 4 and wire_type == 0:
            row["effective_block_height"] = str(inner_value)
        elif field_no == 5 and wire_type == 0:
            row["last_block_height"] = str(inner_value)
        elif field_no == 8 and wire_type == 2:
            row["validation_weights"].append(decode_validation_weight(inner_value))
        elif field_no == 9 and wire_type == 0:
            row["unit_of_compute_price"] = str(inner_value)
        elif field_no == 10 and wire_type == 0:
            row["number_of_requests"] = str(inner_value)
        elif field_no == 11 and wire_type == 0:
            row["previous_epoch_requests"] = str(inner_value)
        elif field_no == 13 and wire_type == 0:
            row["total_weight"] = str(inner_value)
        elif field_no == 14 and wire_type == 2:
            row["model_id"] = as_text(inner_value)
        elif field_no == 15 and wire_type == 2:
            row["sub_group_models"].append(as_text(inner_value))
        elif field_no == 16 and wire_type == 0:
            row["epoch_index"] = str(inner_value)
        elif field_no == 18 and wire_type == 0:
            row["total_throughput"] = str(inner_value)
        elif field_no == 19 and wire_type == 2:
            row["confirmation_weight_scales"].append(decode_confirmation_weight_scale(inner_value))
    return row


def decode_epoch_group_response(value_b64):
    raw = base64.b64decode(value_b64)
    for field_no, wire_type, value in parse_fields(raw):
        if field_no == 1 and wire_type == 2:
            return {"epoch_group_data": decode_epoch_group_data(value)}
    return {"epoch_group_data": {}}


def fetch_epoch_group_from_rpc(rpc, epoch, height, model_id=""):
    payload = abci_query(
        rpc,
        "/inference.inference.Query/EpochGroupData",
        height,
        epoch_group_data_request_hex(epoch, model_id),
    )
    response = ((payload.get("result") or {}).get("response") or {})
    if response.get("code") not in (None, 0):
        raise RuntimeError(response.get("log") or f"ABCI code {response.get('code')}")
    value = response.get("value")
    if not value:
        raise RuntimeError(response.get("log") or "Empty ABCI response")
    return decode_epoch_group_response(value)


def fetch_epoch_group_from_api(api_node, epoch, height):
    return http_get_json(
        api_node,
        f"/chain-api/productscience/inference/inference/epoch_group_data/{epoch}",
        headers={"x-cosmos-block-height": str(height)},
    )


def discover_event_heights(rpc, epoch, start, end):
    group_id = epoch_group_id(epoch)
    query = (
        f"cosmos.group.v1.EventUpdateGroup.group_id='\"{group_id}\"' "
        f"AND block.height >= {start} AND block.height <= {end}"
    )
    heights = []
    page = 1
    total_count = None
    while total_count is None or len(heights) < total_count:
        payload = block_search(rpc, query, page=page, per_page=100)
        if payload.get("error"):
            raise RuntimeError(payload["error"])
        result = payload.get("result") or {}
        total_count = int(result.get("total_count") or 0)
        blocks = result.get("blocks") or []
        if not blocks:
            break
        for block in blocks:
            header = ((block.get("block") or {}).get("header") or {})
            height = int(header.get("height") or 0)
            if height:
                heights.append(
                    {
                        "height": height,
                        "time": header.get("time") or "",
                    }
                )
        page += 1
    unique = {row["height"]: row for row in heights}
    return [unique[height] for height in sorted(unique)]


def unwrap_epoch_group(payload):
    wrapper = payload.get("json") if isinstance(payload, dict) else None
    if isinstance(wrapper, dict):
        payload = wrapper
    return payload.get("epoch_group_data") or payload


def weight_signature(payload):
    group = unwrap_epoch_group(payload)
    rows = []
    for item in group.get("validation_weights") or []:
        rows.append(
            (
                item.get("member_address") or "",
                int(item.get("weight") or item.get("voting_power") or 0),
                int(item.get("confirmation_weight") or 0),
            )
        )
    return tuple(sorted(rows))


def first_changed_height(binary, rpc, epoch, low_height, low_sig, high_height, high_sig, cache):
    if low_sig == high_sig:
        return high_height, high_sig
    low = low_height
    high = high_height
    found_sig = high_sig
    while high - low > 1:
        mid = (low + high) // 2
        payload = fetch_at_height(binary, rpc, epoch, mid, cache)
        sig = weight_signature(payload)
        if sig == low_sig:
            low = mid
        else:
            high = mid
            found_sig = sig
    return high, found_sig


def fetch_at_height(binary, rpc, epoch, height, cache):
    key = (epoch, height)
    if key not in cache:
        cache[key] = run_query(binary, rpc, epoch, height)
    return cache[key]


def fetch_snapshot(snapshot_source, binary, rpc, api_node, epoch, height, cache, model_id=""):
    key = (snapshot_source, epoch, height, model_id)
    if key in cache:
        return cache[key]
    if model_id and snapshot_source != "rpc":
        payload = fetch_epoch_group_from_rpc(rpc, epoch, height, model_id)
    elif snapshot_source == "inferenced":
        payload = run_query(binary, rpc, epoch, height)
    elif snapshot_source == "api":
        payload = fetch_epoch_group_from_api(api_node, epoch, height)
    elif snapshot_source == "rpc":
        payload = fetch_epoch_group_from_rpc(rpc, epoch, height, model_id)
    else:
        raise ValueError(f"Unsupported snapshot source: {snapshot_source}")
    group = unwrap_epoch_group(payload)
    if not group.get("validation_weights"):
        raise RuntimeError(f"No validation_weights for epoch {epoch} at height {height}")
    cache[key] = payload
    return payload


def discover_heights(binary, rpc, epoch, start, end, scan_step):
    heights = sorted(set([start, end, *range(start, end + 1, scan_step)]))
    cache = {}
    checkpoints = [start]
    previous_height = start
    previous_payload = fetch_at_height(binary, rpc, epoch, start, cache)
    previous_sig = weight_signature(previous_payload)

    for height in heights[1:]:
        payload = fetch_at_height(binary, rpc, epoch, height, cache)
        sig = weight_signature(payload)
        if sig != previous_sig:
            changed_height, changed_sig = first_changed_height(
                binary, rpc, epoch, previous_height, previous_sig, height, sig, cache
            )
            checkpoints.append(changed_height)
            previous_height = changed_height
            previous_sig = changed_sig
        else:
            previous_height = height
    return sorted(set(checkpoints))


def write_snapshot(epoch_dir, filename, payload):
    epoch_dir.mkdir(parents=True, exist_ok=True)
    path = epoch_dir / filename
    with path.open("w") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")
    return path


def main():
    parser = argparse.ArgumentParser(
        description="Fetch archive-node epoch group snapshots for every observed CPoC checkpoint."
    )
    parser.add_argument("--epochs", nargs="+", type=int, default=DEFAULT_EPOCHS)
    parser.add_argument("--height-source", choices=["events", "scan", "configured"], default="events")
    parser.add_argument("--snapshot-source", choices=["auto", "rpc", "api", "inferenced", "none"], default="auto")
    parser.add_argument("--scan-step", type=int, default=100)
    parser.add_argument("--node", default=gonka_rpc_url())
    parser.add_argument("--api-node", default=None)
    parser.add_argument("--require-snapshots", action="store_true")
    parser.add_argument("--include-model-snapshots", action="store_true")
    parser.add_argument("--models", nargs="+", default=DEFAULT_MODELS)
    args = parser.parse_args()

    if args.scan_step < 1:
        raise SystemExit("--scan-step must be >= 1")

    api_node = args.api_node or default_api_node(args.node)
    binary = inferenced_binary(required=(args.snapshot_source == "inferenced") or args.height_source == "scan")
    snapshot_source = args.snapshot_source
    if snapshot_source == "auto":
        snapshot_source = "inferenced" if binary else "rpc"
    if snapshot_source == "inferenced" and not binary:
        raise SystemExit("inferenced binary not found; set INFERENCED_BINARY=/path/to/inferenced")
    configured = configured_heights()
    manifest = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "source": {
            "rpcNode": args.node,
            "apiNode": api_node,
            "binary": binary,
            "heightSource": args.height_source,
            "snapshotSource": snapshot_source,
            "scanStep": args.scan_step,
            "configuredHeights": bool(configured),
            "snapshotsFetched": snapshot_source != "none",
        },
        "epochs": [],
    }

    for epoch in args.epochs:
        start, end = epoch_bounds(epoch)
        start_snapshot_height = epoch_start_snapshot_height(epoch)
        event_rows = []
        if args.height_source == "configured":
            heights = configured.get(epoch, [])
            if not heights:
                raise SystemExit(f"No configured CPoC heights for epoch {epoch}")
            event_rows = [{"height": height, "time": ""} for height in heights]
        elif args.height_source == "events":
            event_rows = discover_event_heights(args.node, epoch, start, end)
            heights = [row["height"] for row in event_rows]
        else:
            heights = discover_heights(binary, args.node, epoch, start, end, args.scan_step)
            event_rows = [{"height": height, "time": ""} for height in heights[1:]]

        epoch_dir = OUT / f"e{epoch}"
        cache = {}
        entries = [{"index": 0, "height": start_snapshot_height, "pocStartHeight": start, "kind": "start", "snapshotStatus": "missing"}]
        if snapshot_source != "none":
            payload = fetch_snapshot(snapshot_source, binary, args.node, api_node, epoch, start_snapshot_height, cache)
            path = write_snapshot(epoch_dir, f"start_{start_snapshot_height}.json", payload)
            entries[0]["file"] = str(path.relative_to(OUT))
            entries[0]["snapshotStatus"] = "fetched"
            if args.include_model_snapshots:
                entries[0]["modelFiles"] = {}
                for model_id in args.models:
                    payload = fetch_snapshot("rpc", binary, args.node, api_node, epoch, start_snapshot_height, cache, model_id)
                    path = write_snapshot(epoch_dir / "models" / model_slug(model_id), f"start_{start_snapshot_height}.json", payload)
                    entries[0]["modelFiles"][model_id] = str(path.relative_to(OUT))
        elif args.require_snapshots:
            raise SystemExit(f"Snapshot required but snapshot source is none for epoch {epoch} start")
        for index, row in enumerate(event_rows, start=1):
            height = row["height"]
            entry = {
                "index": index,
                "height": height,
                "blockTime": row.get("time") or "",
                "kind": "cpoc",
                "snapshotStatus": "missing",
            }
            if snapshot_source != "none":
                try:
                    payload = fetch_snapshot(snapshot_source, binary, args.node, api_node, epoch, height, cache)
                    path = write_snapshot(epoch_dir, f"cpoc_{index:02d}_{height}.json", payload)
                    entry["file"] = str(path.relative_to(OUT))
                    entry["snapshotStatus"] = "fetched"
                    if args.include_model_snapshots:
                        entry["modelFiles"] = {}
                        for model_id in args.models:
                            payload = fetch_snapshot("rpc", binary, args.node, api_node, epoch, height, cache, model_id)
                            path = write_snapshot(epoch_dir / "models" / model_slug(model_id), f"cpoc_{index:02d}_{height}.json", payload)
                            entry["modelFiles"][model_id] = str(path.relative_to(OUT))
                except Exception as exc:
                    entry["snapshotStatus"] = "error"
                    entry["snapshotError"] = type(exc).__name__
                    if args.require_snapshots:
                        raise
            elif args.require_snapshots:
                raise SystemExit(f"Snapshot required but snapshot source is none for epoch {epoch} CPoC {height}")
            entries.append(entry)

        manifest["epochs"].append(
            {
                "epoch": epoch,
                "startHeight": start,
                "startSnapshotHeight": start_snapshot_height,
                "endHeight": end,
                "checkpoints": entries,
            }
        )

    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "manifest.json").open("w") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
        f.write("\n")


if __name__ == "__main__":
    main()
