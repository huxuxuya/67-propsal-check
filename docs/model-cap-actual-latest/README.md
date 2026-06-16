# Model Cap Actual (Latest 3 Epochs)

This folder contains a standalone, data-isolated view of **actual chain model-cap outputs** for the latest 3 available epochs, plus a clearly marked next-epoch preview.

Scope:
- epoch window is computed dynamically from `GONKA_RPC_URL`
- only regular on-chain model-cap rows are included (no no-attack scenarios)
- the next-epoch preview is derived from the latest root total and assumes latest requested model weight repeats
- source values are read from archive RPC only

## Included files

- `data/model_cap_actual.json` — full payload injected into the page.
- `data/model_cap_actual.js` — the same payload as a global `window.modelCapActualData` object.
- `assets/app.js` — UI + charts.
- `assets/styles.css` — page styles.
- `index.html` — static page.

## Data columns (per model/epoch row)

- `subgroupRawWeight` — on-chain subgroup raw weight.
- `weightScaleFactor` — model coefficient from `delegation.poc_params`.
- `rawConsensusWeight` — subgroupRawWeight × weightScaleFactor.
- `capWeight` — 75% chain cap threshold for previous epoch root total (if cap is enabled).
- `countedWeight` — counted weight after cap.
- `clippedWeight` — amount above cap.
- `pressureRatio` — rawConsensusWeight / capWeight (if cap is enabled).
- `capHeadroom` — capWeight - rawConsensusWeight if uncapped.
- `previousEpochRootTotalWeight` — chain denominator used for cap basis.
- `capUtilization` — the same as `pressureRatio` but explicitly tied to cap capability.

## Forecast rows

`forecastRows` are not on-chain facts. They answer one narrow question:

```text
If the latest requested model weight repeats in the next epoch,
what cap would apply from the latest root total?
```

Formula:

```text
nextCapLimit = floor(latestRootTotalWeight * capFactor)
forecastCounted = min(latestRequestedWeight, nextCapLimit)
forecastClipped = max(0, latestRequestedWeight - forecastCounted)
```

## What changed vs previous dashboard view

- This is an independent page with its own data file.
- It does not depend on the shared dashboard’s bundled `data/dashboard.js` cache.
- It is intended for direct model-cap validation: denominator, scale factors, requested weight, cap limit, counted weight, clipped weight, and next-epoch preview.

## Rebuild

From repository root:

```bash
python3 scripts/fetch_model_cap_actual_latest.py
```

The script verifies source by reading:

```bash
python3 -c 'import sys; sys.path.insert(0, "scripts"); from env_utils import gonka_rpc_source_label, gonka_rpc_url; print(gonka_rpc_source_label(), gonka_rpc_url())'
```

`latestEpoch` is discovered from archive RPC; payload is the latest available three-epoch window. The latest epoch is read at the current archive RPC height so it can be a current snapshot, not necessarily a completed epoch.

## Source provenance

- `source.rpcNode`: `GONKA_RPC_URL`
- `source.paramsSource`: `archive_rpc_params`
- `summary.sourceChain`: `GONKA_RPC_URL (archive)`
- `summary.latestBlockHeight`: latest block height from RPC status
- `summary.nextEpochPreview`: derived next-epoch cap basis and cap limit
- `summary.mode`: `actual`
