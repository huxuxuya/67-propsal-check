#!/usr/bin/env python3
import argparse
import base64
import json
import re
import urllib.request
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_DOWN
from pathlib import Path

from env_utils import gonka_api_source_label, gonka_api_url, gonka_rpc_source_label, gonka_rpc_url
from fetch_cpoc_epoch_snapshots import (
    abci_query,
    decode_epoch_group_response,
    load_json,
    load_upstream_epoch_group,
    parse_fields,
    proto_bytes,
    proto_varint,
    as_text,
)


ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "upstream" / "gonka-kimi-restitution"
DATA = ROOT / "data"
OUT = DATA / "model_cap_factors"
DEFAULT_EPOCHS = list(range(264, 282))
DEFAULT_API_NODE = "http://node1.gonka.ai:8000"
DEFAULT_RPC_NODE = "http://node1.gonka.ai:26657"
QWEN_MODEL = "Qwen/Qwen3-235B-A22B-Instruct-2507-FP8"
KIMI_MODEL = "moonshotai/Kimi-K2.6"
MINIMAX_MODEL = "MiniMaxAI/MiniMax-M2.7"


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def epoch_end_height_from_script(epoch):
    path = UPSTREAM / f"e{epoch}" / f"calculate_compensation_{epoch}.py"
    if not path.exists():
        return 0
    match = re.search(r"^EPOCH_END\s*=\s*([0-9_]+)", path.read_text(), re.MULTILINE)
    return int(match.group(1).replace("_", "")) if match else 0


def load_epoch_group(epoch, rpc_node=""):
    local = load_upstream_epoch_group(epoch, "healthy" if epoch == 265 else "")
    if local:
        return local
    if not rpc_node:
        return {}
    try:
        return fetch_epoch_group_from_rpc(rpc_node, epoch, 0).get("epoch_group_data", {})
    except Exception:
        return {}


def epoch_end_height(epoch, rpc_node):
    scripted = epoch_end_height_from_script(epoch)
    if scripted:
        return scripted
    group = load_epoch_group(epoch, rpc_node)
    next_group = load_epoch_group(epoch + 1, rpc_node)
    if next_group.get("poc_start_block_height"):
        return int(next_group["poc_start_block_height"]) - 1
    return int(group.get("last_block_height") or group.get("effective_block_height") or group.get("poc_start_block_height") or 0)


def epoch_start_height(epoch, rpc_node):
    group = load_epoch_group(epoch, rpc_node)
    return int(group.get("effective_block_height") or group.get("poc_start_block_height") or 0)


def decimal_value(value, default=Decimal(0)):
    if value is None:
        return default
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    if isinstance(value, str):
        try:
            return Decimal(value)
        except InvalidOperation:
            return default
    if isinstance(value, dict):
        raw = value.get("value")
        exponent = value.get("exponent", 0)
        try:
            return Decimal(str(raw)) * (Decimal(10) ** int(exponent))
        except (InvalidOperation, TypeError, ValueError):
            return default
    return default


def decimal_float(value):
    return float(value.quantize(Decimal("0.000001")))


def signed64(value):
    return value - (1 << 64) if value >= (1 << 63) else value


def decode_proto_decimal(value):
    raw = 0
    exponent = 0
    for field_no, wire_type, inner_value in parse_fields(value):
        if field_no == 1 and wire_type == 0:
            raw = signed64(inner_value)
        elif field_no == 2 and wire_type == 0:
            exponent = signed64(inner_value)
    return Decimal(raw) * (Decimal(10) ** exponent)


def epoch_group_data_request_hex(epoch, model_id=""):
    payload = proto_varint(1, int(epoch))
    if model_id:
        payload += proto_bytes(2, model_id.encode())
    return "0x" + payload.hex()


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


def decode_poc_model_config(value):
    row = {}
    for field_no, wire_type, inner_value in parse_fields(value):
        if field_no == 1 and wire_type == 2:
            row["model_id"] = as_text(inner_value)
        elif field_no == 4 and wire_type == 2:
            row["weight_scale_factor"] = decode_proto_decimal(inner_value)
    return row


def decode_poc_params(value):
    rows = []
    for field_no, wire_type, inner_value in parse_fields(value):
        if field_no == 14 and wire_type == 2:
            rows.append(decode_poc_model_config(inner_value))
    return rows


def decode_delegation_params(value):
    row = {}
    for field_no, wire_type, inner_value in parse_fields(value):
        if field_no == 7 and wire_type == 2:
            row["cap_factor"] = decode_proto_decimal(inner_value)
        elif field_no == 8 and wire_type == 2:
            row["initial_model_id"] = as_text(inner_value)
    return row


def decode_params_response(value_b64):
    payload = {"models": [], "delegation": {}}
    raw = base64.b64decode(value_b64)
    for field_no, wire_type, value in parse_fields(raw):
        if field_no != 1 or wire_type != 2:
            continue
        for params_field, params_wire, params_value in parse_fields(value):
            if params_field == 3 and params_wire == 2:
                payload["models"] = decode_poc_params(params_value)
            elif params_field == 16 and params_wire == 2:
                payload["delegation"] = decode_delegation_params(params_value)
    return payload


def fetch_params_from_rpc(rpc, height):
    payload = abci_query(rpc, "/inference.inference.Query/Params", height, "")
    response = ((payload.get("result") or {}).get("response") or {})
    if response.get("code") not in (None, 0):
        raise RuntimeError(response.get("log") or f"ABCI code {response.get('code')}")
    value = response.get("value")
    if not value:
        raise RuntimeError(response.get("log") or "Empty ABCI response")
    decoded = decode_params_response(value)
    delegation = decoded.get("delegation") or {}
    return {
        "capFactor": decimal_value(delegation.get("cap_factor"), Decimal("0.75")),
        "initialModelId": delegation.get("initial_model_id") or "",
        "weightScaleFactors": {
            row["model_id"]: decimal_value(row.get("weight_scale_factor"), Decimal(1))
            for row in decoded.get("models", [])
            if row.get("model_id")
        },
        "paramsSource": "archive_rpc_params",
        "paramsError": "",
        "rawDecoded": {
            "delegation": {
                "cap_factor": str(delegation.get("cap_factor", "")),
                "initial_model_id": delegation.get("initial_model_id") or "",
            },
            "models": [
                {
                    "model_id": row.get("model_id", ""),
                    "weight_scale_factor": str(row.get("weight_scale_factor", "")),
                }
                for row in decoded.get("models", [])
            ],
        },
    }


def params_signature(params):
    return json.dumps(
        {
            "capFactor": str(params.get("capFactor", "")),
            "initialModelId": params.get("initialModelId", ""),
            "weightScaleFactors": {key: str(value) for key, value in sorted((params.get("weightScaleFactors") or {}).items())},
        },
        sort_keys=True,
    )


def params_snapshot(epoch, height, position, params):
    return {
        "epoch": epoch,
        "height": height,
        "position": position,
        "capFactor": decimal_float(params["capFactor"]),
        "initialModelId": params.get("initialModelId", ""),
        "initialModelLabel": model_label(params.get("initialModelId", "")),
        "paramsSource": params.get("paramsSource", ""),
        "models": [
            {
                "modelId": model_id,
                "modelLabel": model_label(model_id),
                "weightScaleFactor": decimal_float(value),
            }
            for model_id, value in sorted((params.get("weightScaleFactors") or {}).items(), key=lambda item: model_label(item[0]))
        ],
    }


def find_params_change_height(rpc, start_height, end_height, start_signature, end_signature):
    if not start_height or not end_height or start_height >= end_height or start_signature == end_signature:
        return None
    left = start_height + 1
    right = end_height
    found = None
    while left <= right:
        mid = (left + right) // 2
        mid_signature = params_signature(fetch_params_from_rpc(rpc, mid))
        if mid_signature == end_signature:
            found = mid
            right = mid - 1
        else:
            left = mid + 1
    return found


def fetch_json(node, path, height=None, timeout=30):
    url = f"{node.rstrip('/')}/{path.lstrip('/')}"
    headers = {"x-cosmos-block-height": str(height)} if height else {}
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def fetch_params(api_node, height):
    return fetch_json(api_node, "/chain-api/productscience/inference/inference/params", height=height)


def normalize_params(payload):
    params = payload.get("params") or payload
    delegation = params.get("delegation_params") or params.get("delegationParams") or {}
    poc = params.get("poc_params") or params.get("pocParams") or {}
    models = poc.get("models") or []
    coeffs = {}
    for item in models:
        model_id = item.get("model_id") or item.get("modelId") or item.get("id") or ""
        if not model_id:
            continue
        coeffs[model_id] = decimal_value(item.get("weight_scale_factor") or item.get("weightScaleFactor"), Decimal(1))
    return {
        "capFactor": decimal_value(delegation.get("cap_factor") or delegation.get("capFactor"), Decimal("0.75")),
        "initialModelId": delegation.get("initial_model_id") or delegation.get("initialModelId") or "",
        "weightScaleFactors": coeffs,
        "paramsSource": "archive_rest_params",
        "paramsError": "",
    }


def fallback_params(epoch, message=""):
    coeffs = {
        QWEN_MODEL: Decimal(1),
        KIMI_MODEL: Decimal("0.78") if epoch >= 276 else Decimal(1),
        MINIMAX_MODEL: Decimal("0.3024"),
    }
    return {
        "capFactor": Decimal("0.75"),
        "initialModelId": QWEN_MODEL,
        "weightScaleFactors": coeffs,
        "paramsSource": "known_investigation_constants",
        "paramsError": message,
    }


def normalize_cached_params(payload):
    if not payload:
        return {}
    return {
        "capFactor": decimal_value(payload.get("capFactor"), Decimal("0.75")),
        "initialModelId": payload.get("initialModelId") or "",
        "weightScaleFactors": {
            model_id: decimal_value(value, Decimal(1))
            for model_id, value in (payload.get("weightScaleFactors") or {}).items()
        },
        "paramsSource": payload.get("paramsSource") or "cached_normalized_params",
        "paramsError": payload.get("paramsError") or "",
    }


def model_label(model_id):
    value = (model_id or "").lower()
    if "kimi" in value or "moonshot" in value:
        return "Kimi"
    if "qwen" in value:
        return "Qwen"
    if "minimax" in value:
        return "MiniMax"
    return model_id.split("/")[-1] if model_id else "Unknown"


def subgroup_raw_weight(group):
    rows = group.get("validation_weights") or []
    if rows:
        return sum(int(row.get("weight") or 0) for row in rows)
    return int(group.get("total_weight") or 0)


def subgroup_node_count(group):
    return sum(len(row.get("ml_nodes") or []) for row in group.get("validation_weights") or [])


def load_existing_cache():
    path = OUT / "model_cap_factors.json"
    if not path.exists():
        return {}
    return load_json(path)


def build_rows(epochs, rpc_node, api_node, use_cache=False):
    cached = load_existing_cache() if use_cache else {}
    cached_raw = ((cached.get("raw") or {}).get("epochs") or {}) if isinstance(cached, dict) else {}
    rows = []
    raw_epochs = {}
    param_snapshots = []
    errors = []
    fetched_at = datetime.now(timezone.utc).isoformat()

    for epoch in epochs:
        height = epoch_end_height(epoch, rpc_node)
        start_height = epoch_start_height(epoch, rpc_node)
        if not height:
            errors.append({"epoch": epoch, "error": "missing_epoch_end_height"})
            continue

        cache_epoch = cached_raw.get(str(epoch)) or cached_raw.get(epoch) or {}
        try:
            if cache_epoch:
                root = cache_epoch["root"]["epoch_group_data"]
                params = normalize_cached_params(cache_epoch.get("paramsNormalized")) or normalize_params(cache_epoch["params"])
                subgroups = {item["modelId"]: item["epoch_group_data"] for item in cache_epoch.get("subgroups", [])}
                start_subgroups = {item["modelId"]: item["epoch_group_data"] for item in cache_epoch.get("startSubgroups", [])}
                param_snapshots.extend(cache_epoch.get("paramSnapshots", []))
                raw_epochs[str(epoch)] = cache_epoch
            else:
                root_payload = fetch_epoch_group_from_rpc(rpc_node, epoch, height, "")
                root = root_payload.get("epoch_group_data") or {}
                start_params = None
                try:
                    if start_height:
                        start_params = fetch_params_from_rpc(rpc_node, start_height)
                    params = fetch_params_from_rpc(rpc_node, height)
                    params_payload = params.get("rawDecoded") or {}
                except Exception as exc:
                    if api_node:
                        try:
                            params_payload = fetch_params(api_node, height)
                            params = normalize_params(params_payload)
                        except Exception as rest_exc:
                            params_payload = {
                                "rpcError": {"error": type(exc).__name__, "message": str(exc)},
                                "restError": {"error": type(rest_exc).__name__, "message": str(rest_exc)},
                            }
                            params = fallback_params(epoch, f"RPC {type(exc).__name__}: {exc}; REST {type(rest_exc).__name__}: {rest_exc}")
                    else:
                        params_payload = {
                            "rpcError": {"error": type(exc).__name__, "message": str(exc)},
                            "restSkipped": "GONKA_API_URL is not set; node1 REST fallback is disabled",
                        }
                        params = fallback_params(epoch, f"RPC {type(exc).__name__}: {exc}; REST fallback disabled")
                if start_params is None:
                    start_params = params

                epoch_param_snapshots = []
                if start_height:
                    epoch_param_snapshots.append(params_snapshot(epoch, start_height, "start", start_params))
                if height != start_height:
                    epoch_param_snapshots.append(params_snapshot(epoch, height, "end", params))
                if params_signature(start_params) != params_signature(params):
                    change_height = find_params_change_height(rpc_node, start_height, height, params_signature(start_params), params_signature(params))
                    if change_height:
                        epoch_param_snapshots.append(params_snapshot(epoch, change_height, "change", fetch_params_from_rpc(rpc_node, change_height)))
                param_snapshots.extend(epoch_param_snapshots)

                subgroups = {}
                start_subgroups = {}
                for model_id in root.get("sub_group_models") or []:
                    subgroups[model_id] = (fetch_epoch_group_from_rpc(rpc_node, epoch, height, model_id).get("epoch_group_data") or {})
                    if start_height:
                        try:
                            start_subgroups[model_id] = (
                                fetch_epoch_group_from_rpc(rpc_node, epoch, start_height, model_id).get("epoch_group_data") or {}
                            )
                        except Exception as exc:
                            errors.append(
                                {
                                    "epoch": epoch,
                                    "height": start_height,
                                    "modelId": model_id,
                                    "error": type(exc).__name__,
                                    "message": f"start subgroup fetch failed: {exc}",
                                }
                            )

                raw_epochs[str(epoch)] = {
                    "height": height,
                    "startHeight": start_height,
                    "root": root_payload,
                    "params": params_payload,
                    "paramsNormalized": {
                        "capFactor": str(params["capFactor"]),
                        "initialModelId": params["initialModelId"],
                        "weightScaleFactors": {model_id: str(value) for model_id, value in params["weightScaleFactors"].items()},
                        "paramsSource": params.get("paramsSource", ""),
                        "paramsError": params.get("paramsError", ""),
                    },
                    "paramSnapshots": epoch_param_snapshots,
                    "startSubgroups": [{"modelId": model_id, "epoch_group_data": group} for model_id, group in sorted(start_subgroups.items())],
                    "subgroups": [{"modelId": model_id, "epoch_group_data": group} for model_id, group in sorted(subgroups.items())],
                }

            prev_root = load_upstream_epoch_group(epoch - 1, "end" if epoch - 1 == 265 else "")
            if not prev_root:
                prev_root = load_epoch_group(epoch - 1, rpc_node)
            previous_total = int(prev_root.get("total_weight") or 0)
            root_total = int(root.get("total_weight") or 0)
            cap_factor = params["capFactor"]
            cap_weight = int((cap_factor * Decimal(previous_total)).to_integral_value(rounding=ROUND_DOWN)) if previous_total else 0
            initial_model = params["initialModelId"]
            sole_group = len(root.get("sub_group_models") or []) == 1

            for model_id in root.get("sub_group_models") or []:
                group = subgroups.get(model_id) or {}
                if not group:
                    rows.append(
                        {
                            "epoch": epoch,
                            "height": height,
                            "modelId": model_id,
                            "modelLabel": model_label(model_id),
                            "status": "missing_subgroup",
                            "source": "archive_rpc",
                            "paramsSource": params.get("paramsSource", ""),
                            "paramsError": params.get("paramsError", ""),
                        }
                    )
                    continue
                coeff = params["weightScaleFactors"].get(model_id, Decimal(1))
                raw_weight = subgroup_raw_weight(group)
                raw_consensus = int((coeff * Decimal(raw_weight)).to_integral_value(rounding=ROUND_DOWN))
                is_initial = bool(initial_model and model_id == initial_model)
                cap_applies = not is_initial and not sole_group
                if not cap_applies:
                    applied_scale = Decimal(1)
                    pressure = Decimal(0)
                    capped_weight = raw_consensus
                    status = "initial_exempt" if is_initial else "sole_group_uncapped"
                elif not previous_total:
                    applied_scale = None
                    pressure = None
                    capped_weight = raw_consensus
                    status = "cap_reference_missing"
                elif raw_consensus > cap_weight and raw_consensus > 0:
                    applied_scale = Decimal(cap_weight) / Decimal(raw_consensus)
                    pressure = Decimal(raw_consensus) / Decimal(cap_weight) if cap_weight else Decimal(0)
                    capped_weight = cap_weight
                    status = "capped"
                else:
                    applied_scale = Decimal(1)
                    pressure = Decimal(raw_consensus) / Decimal(cap_weight) if cap_weight else Decimal(0)
                    capped_weight = raw_consensus
                    status = "under_cap"
                rows.append(
                    {
                        "epoch": epoch,
                        "height": height,
                        "modelId": model_id,
                        "modelLabel": model_label(model_id),
                        "status": status,
                        "source": "archive_rpc",
                        "paramsSource": params.get("paramsSource", ""),
                        "paramsError": params.get("paramsError", ""),
                        "capApplies": cap_applies,
                        "initialModel": is_initial,
                        "capFactor": decimal_float(cap_factor),
                        "previousEpochRootTotalWeight": previous_total,
                        "rootTotalWeight": root_total,
                        "subgroupRawWeight": raw_weight,
                        "weightScaleFactor": decimal_float(coeff),
                        "rawConsensusWeight": raw_consensus,
                        "capWeight": cap_weight if cap_applies and previous_total else None,
                        "cappedConsensusWeight": capped_weight,
                        "countedWeight": capped_weight,
                        "scaleDelta": raw_consensus - raw_weight,
                        "clippedWeight": max(0, raw_consensus - capped_weight) if cap_applies and previous_total else 0,
                        "capUtilization": decimal_float(Decimal(raw_consensus) / Decimal(cap_weight)) if cap_applies and cap_weight else None,
                        "capHeadroom": max(0, cap_weight - raw_consensus) if cap_applies and cap_weight and raw_consensus <= cap_weight else None,
                        "capLimitFromPreviousEpoch": cap_weight if previous_total else None,
                        "appliedScale": decimal_float(applied_scale) if applied_scale is not None else None,
                        "pressureRatio": decimal_float(pressure) if pressure is not None else None,
                        "participantCount": len(group.get("validation_weights") or []),
                        "nodeCount": subgroup_node_count(group),
                    }
                )
        except Exception as exc:
            errors.append({"epoch": epoch, "height": height, "error": type(exc).__name__, "message": str(exc)})

    payload = {
        "source": {
            "rpcNode": gonka_rpc_source_label("fallback_public_rpc"),
            "apiNode": gonka_api_source_label("disabled_no_GONKA_API_URL"),
            "generatedAt": fetched_at,
            "scope": f"model cap factors e{min(epochs)}-e{max(epochs)}",
        },
        "rows": sorted(rows, key=lambda row: (row.get("epoch", 0), row.get("modelLabel", ""), row.get("modelId", ""))),
        "paramSnapshots": sorted(param_snapshots, key=lambda row: (row.get("epoch", 0), row.get("height", 0), row.get("position", ""))),
        "errors": errors,
        "raw": {"epochs": raw_epochs},
    }
    return payload


def main():
    parser = argparse.ArgumentParser(description="Fetch model subgroup cap-factor inputs for proposal #67 dashboard.")
    parser.add_argument("--epochs", nargs="*", type=int, default=DEFAULT_EPOCHS)
    parser.add_argument("--use-cache", action="store_true", help="Rebuild normalized rows from existing raw cache when present.")
    args = parser.parse_args()

    rpc_source = gonka_rpc_source_label("fallback_public_rpc")
    if rpc_source != "GONKA_RPC_URL":
        raise SystemExit("GONKA_RPC_URL is required for archive model-cap fetches; refusing to use node1 fallback.")

    api_node = gonka_api_url("") if gonka_api_source_label("") == "GONKA_API_URL" else ""
    payload = build_rows(args.epochs, gonka_rpc_url(DEFAULT_RPC_NODE), api_node, args.use_cache)
    write_json(OUT / "model_cap_factors.json", payload)
    print(json.dumps({"rows": len(payload["rows"]), "errors": len(payload["errors"]), "out": str(OUT / "model_cap_factors.json")}, indent=2))


if __name__ == "__main__":
    main()
