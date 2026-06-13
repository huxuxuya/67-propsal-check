# Archive Node Access Rules

Use the archive RPC from `.env` for every historical chain query.

- Read archive RPC from `GONKA_RPC_URL`; this repo's `.env` may contain a host without a scheme or port, and `scripts/env_utils.py` normalizes it to `http://<host>:26657`.
- Do not use `node1.gonka.ai` for archive, historical height, ABCI, governance-power, CPoC, epoch-group, or model-cap data.
- If `GONKA_RPC_URL` is missing, stop and report the missing environment variable instead of falling back to `node1.gonka.ai`.
- `GONKA_API_URL` is only for REST/API snapshots when a script explicitly needs a REST endpoint. It is not a replacement for archive CometBFT RPC.
- Do not commit `.env` or print the concrete archive host in reports. Committed data should identify the source as `GONKA_RPC_URL`.

Before running a fetch, verify the source:

```bash
python3 -c 'import sys; sys.path.insert(0, "scripts"); from env_utils import gonka_rpc_source_label, gonka_rpc_url; print(gonka_rpc_source_label(), gonka_rpc_url())'
```

Expected source label is `GONKA_RPC_URL`. If it is not, do not run the fetch.

For model cap data, use:

```bash
python3 scripts/fetch_model_cap_factors.py
python3 scripts/build_dashboard_data.py
```
