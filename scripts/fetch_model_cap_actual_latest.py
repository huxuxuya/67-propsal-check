#!/usr/bin/env python3
import json
import math
import urllib.request
from pathlib import Path

from fetch_model_cap_factors import build_rows, gonka_rpc_source_label, gonka_rpc_url, load_epoch_group

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "model-cap-actual-latest" / "data"
OUT_JSON = OUT_DIR / "model_cap_actual.json"
OUT_JS = OUT_DIR / "model_cap_actual.js"

FALLBACK_EPOCH = 281
MAX_EPOCH_SCAN = 1024


def rpc_request_json(url):
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            return json.load(response)
    except Exception as exc:
        raise RuntimeError(f"RPC request failed for {url}: {exc}") from exc


def load_latest_block_height(rpc_node):
    status = rpc_request_json(f"{rpc_node.rstrip('/')}/status")
    raw_height = (status.get("result", {}).get("sync_info", {}) or {}).get("latest_block_height")
    if raw_height is None:
        raise RuntimeError("rpc status response missing sync_info.latest_block_height")
    return int(raw_height), status


def discover_seed_epoch(cached_max=FALLBACK_EPOCH):
    cached_path = ROOT / "data" / "model_cap_factors" / "model_cap_factors.json"
    if not cached_path.exists():
        return cached_max
    try:
        payload = json.loads(cached_path.read_text())
        raw_epochs = payload.get("raw", {}).get("epochs", {})
        numeric = [int(epoch) for epoch in raw_epochs.keys() if str(epoch).isdigit()]
        if numeric:
            return max(numeric)
    except Exception:
        pass
    return cached_max


def read_epoch_start_height(rpc_node, epoch):
    group = load_epoch_group(epoch, rpc_node, prefer_rpc=True)
    return int(group.get("effective_block_height") or group.get("poc_start_block_height") or 0)


def discover_latest_completed_epoch(rpc_node, seed_epoch, latest_height):
    current = int(seed_epoch)
    # Bring seed down if chain is currently before it.
    for _ in range(MAX_EPOCH_SCAN):
        start_height = read_epoch_start_height(rpc_node, current)
        if start_height and start_height <= latest_height:
            break
        if current == 0:
            break
        current -= 1
    else:
        raise RuntimeError("Unable to align seed epoch to current chain height")

    for _ in range(MAX_EPOCH_SCAN):
        next_group = load_epoch_group(current + 1, rpc_node, prefer_rpc=True)
        if not next_group:
            break
        next_start_height = int(
            next_group.get("poc_start_block_height")
            or next_group.get("effective_block_height")
            or next_group.get("last_block_height")
            or 0
        )
        if not next_start_height or next_start_height > latest_height:
            break
        current += 1

    return current


def build_forecast_rows(payload, latest):
    rows = payload.get("rows") or []
    latest_rows = [row for row in rows if int(row.get("epoch") or 0) == int(latest)]
    if not latest_rows:
        return [], {}
    basis = int(latest_rows[0].get("rootTotalWeight") or 0)
    cap_factor = float(latest_rows[0].get("capFactor") or 0.75)
    cap_limit = math.floor(basis * cap_factor) if basis else 0
    next_epoch = int(latest) + 1
    forecast_rows = []
    for row in latest_rows:
        forecast = dict(row)
        requested = int(row.get("rawConsensusWeight") or 0)
        cap_applies = bool(row.get("capApplies") is not False and not row.get("initialModel"))
        counted = min(requested, cap_limit) if cap_applies and cap_limit else requested
        forecast.update(
            {
                "epoch": next_epoch,
                "isForecast": True,
                "forecastBasis": "latest_requested_weight_repeats",
                "previousEpochRootTotalWeight": basis,
                "rootTotalWeight": None,
                "capWeight": cap_limit if cap_applies else None,
                "capLimitFromPreviousEpoch": cap_limit if cap_applies else None,
                "countedWeight": counted,
                "cappedConsensusWeight": counted,
                "clippedWeight": max(0, requested - counted) if cap_applies else 0,
                "capHeadroom": max(0, cap_limit - requested) if cap_applies and cap_limit else None,
                "capUtilization": (requested / cap_limit) if cap_applies and cap_limit else None,
                "pressureRatio": (requested / cap_limit) if cap_applies and cap_limit else None,
                "status": "forecast_capped" if cap_applies and cap_limit and requested > cap_limit else ("forecast_under_cap" if cap_applies else "initial_exempt"),
            }
        )
        forecast_rows.append(forecast)
    return forecast_rows, {
        "nextEpoch": next_epoch,
        "nextCapBasis": basis,
        "nextCapLimit": cap_limit,
        "forecastBasis": "latest_requested_weight_repeats",
    }


def main():
    rpc_source = gonka_rpc_source_label("fallback_public_rpc")
    if rpc_source != "GONKA_RPC_URL":
        raise SystemExit("GONKA_RPC_URL is required to run this report")

    rpc_node = gonka_rpc_url()
    try:
        latest_height, status = load_latest_block_height(rpc_node)
    except RuntimeError as exc:
        raise SystemExit(f"{exc} (ensure GONKA_RPC_URL is reachable from this environment)")
    seed = discover_seed_epoch()
    latest = discover_latest_completed_epoch(rpc_node, seed, latest_height)
    epochs = list(range(max(0, latest - 2), latest + 1))

    payload = build_rows(epochs, rpc_node, "", use_cache=False, prefer_rpc=True, height_overrides={latest: latest_height})
    payload = payload.copy()
    forecast_rows, next_epoch_preview = build_forecast_rows(payload, latest)
    payload["forecastRows"] = forecast_rows
    payload["summary"] = {
        "generatedBy": "scripts/fetch_model_cap_actual_latest.py",
        "mode": "actual",
        "latestEpoch": latest,
        "latestCompletedEpoch": latest,
        "latestBlockHeight": latest_height,
        "latestSnapshotHeight": latest_height,
        "latestEpochIsOpen": True,
        "epochWindow": epochs,
        "windowLabel": f"e{epochs[0]}-e{epochs[-1]}",
        "nextEpochPreview": next_epoch_preview,
        "fallbackUsed": False,
        "fallbackEpochs": [],
        "rowCount": len(payload.get("rows", [])),
        "sourceChain": "GONKA_RPC_URL (archive)",
        "statusHeight": int((status.get("result", {}).get("sync_info", {}).get("latest_block_height") or 0)),
        "statusCatchingUp": bool(
            (status.get("result", {}).get("sync_info", {}) or {}).get("catching_up") in (True, "true", "True", 1, "1")
        ),
    }
    payload["windowSource"] = "3 latest completed epochs (actual)"

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n")
    OUT_JS.write_text(f"window.modelCapActualData = {json.dumps(payload)};\n")
    print(
        json.dumps(
            {
                "latest": latest,
                "latestBlockHeight": latest_height,
                "epochs": epochs,
                "rows": len(payload.get("rows", [])),
                "out": str(OUT_JSON),
            }
        )
    )


if __name__ == "__main__":
    main()
