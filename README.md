# Proposal 67 Check

Investigation workspace for Gonka proposal #67, "Kimi Restitution (epochs 265-276)".

## Artifacts

- `upstream/gonka-kimi-restitution/` - cloned source restitution repository.
- `docs/` - GitHub Pages static forensic dashboard.
- `docs/data/dashboard.json` - deterministic dashboard data built from saved local snapshots.
- `docs/data/dashboard.js` - same saved data as a browser-loadable static snapshot for opening `docs/index.html` directly.
- `data/gns_names_raw.json` - raw on-chain GNS CosmWasm contract state snapshot.
- `data/gns_names_by_address.json` - decoded `.gnk` names, reverse names, records, and names grouped by address.
- `data/public_identity_signals.json` - raw DNS/RDAP/TLS/HTTP public signal snapshot for proposal #67 addresses and related URLs.
- `reports/proposal_67_analysis.md` - current summary: recipients, final voters, and why 30k became 946k.
- `reports/proposal_67_recipients.csv` - all non-zero compensation recipients with public participant metadata.
- `reports/proposal_67_final_votes.csv` - final per-address vote after last-vote-wins consolidation.
- `data/` - raw on-chain and participant JSON snapshots used by the report and dashboard.

## Rebuild

```bash
python3 scripts/fetch_proposal_67_data.py
python3 scripts/fetch_gns_names.py
python3 scripts/fetch_public_identity_signals.py
python3 scripts/analyze_proposal_67.py
python3 scripts/build_dashboard_data.py
```

The fetch steps use public Gonka node APIs and may need network access. Run them only when intentionally refreshing raw snapshots. All analysis and dashboard builds after that use saved local data from `data/` and `upstream/`; they do not query nodes.

## Dashboard

Open `docs/index.html` directly in a browser, or serve the repository with a simple static server:

```bash
python3 -m http.server 8080
```

Then open `http://localhost:8080/docs/`.

For GitHub Pages, configure the repository to serve from the `/docs` folder. The dashboard is static vanilla HTML/CSS/JS with Apache ECharts loaded from CDN and committed dashboard data under `docs/data/`.

Raw investigation outputs remain under `reports/`. Raw public identity snapshots remain under `data/`. Dashboard-specific static data remains under `docs/data/`.

The dashboard distinguishes strict public attribution from signal-only grouping:

- Strict evidence includes public self-declared validator/GNS identity and direct validator-key matches.
- Signal clusters may include shared inference host, DNS/IP/RDAP/TLS clues, and are shown as infrastructure signals rather than owner attribution.
