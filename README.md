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
- `data/osint/public_osint_sources.json` - raw public OSINT snapshot for Gonka names, GitHub repository metadata, commits, contributors, and public social/profile candidates.
- `data/public_name_enrichment.json` - normalized public naming index for proposal #67 addresses from GNS, validator metadata, inference URLs, and evidence claims.
- `data/onchain_graph/proposal_67_local_graph.json` - deterministic local graph snapshot built from saved proposal, vote, upstream delegation, and epoch commit data.
- `data/telegram_evidence.json` - curated short excerpts parsed from ignored Telegram exports under `history/`.
- `data/voting_end_epochs/` - raw e285-e290 voting-end epoch snapshots and archive block snapshots, with public-node fallback recorded in the manifest.
- `reports/proposal_67_analysis.md` - current summary: recipients, final voters, and why 30k became 946k.
- `reports/attribution_audit.md` - ranked interested-party audit with evidence caveats.
- `reports/ranked_parties.csv` - exportable ranked actor/cluster priority list.
- `reports/evidence_claims.csv` - exportable evidence claims with source, confidence, and proof/signal boundary.
- `reports/public_name_enrichment.md` / `reports/public_name_enrichment.csv` - public name and metadata attribution queue for proposal #67 addresses.
- `reports/public_name_groups.csv` - grouped public name/source values, useful for shared operator/domain/contact review.
- `reports/proposal_67_recipients.csv` - all non-zero compensation recipients with public participant metadata.
- `reports/proposal_67_final_votes.csv` - final per-address vote after last-vote-wins consolidation.
- `data/` - raw on-chain and participant JSON snapshots used by the report and dashboard.

## Rebuild

```bash
python3 scripts/fetch_proposal_67_data.py
python3 scripts/fetch_gns_names.py
python3 scripts/fetch_public_identity_signals.py
python3 scripts/fetch_public_osint_sources.py
python3 scripts/parse_telegram_exports.py
python3 scripts/fetch_voting_end_epoch_data.py
python3 scripts/build_onchain_graph_snapshot.py
python3 scripts/analyze_proposal_67.py
python3 scripts/build_dashboard_data.py
```

The fetch steps use public Gonka node APIs and may need network access. Run them only when intentionally refreshing raw snapshots. All analysis and dashboard builds after that use saved local data from `data/` and `upstream/`; they do not query nodes.
`build_onchain_graph_snapshot.py` is local-only and derives graph evidence from already saved files.
Set `GONKA_RPC_URL` in a local `.env` file to use an archive CometBFT/Tendermint RPC node for raw endpoints such as `/block?height=...`. If no port is provided, scripts assume port `26657`. Set `GONKA_API_URL` only when you have a separate REST `/chain-api` endpoint; otherwise scripts use the public API endpoint for those snapshots. `.env` is ignored; committed snapshots redact the actual archive node URL as `GONKA_RPC_URL/...`.

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
- Ranked interested parties are prioritized forensic leads, not accusations. Scores separate public identity confidence, compensation benefit, governance activity, and coordination/infrastructure signals.
- Telegram evidence and voting-end epoch anomalies are shown as separate evidence classes. Telegram excerpts require corroboration; epoch anomalies prove timing/weight behavior, not ownership by themselves.
- Governance voting power is not inferred from inference epoch weights. Proposal votes are on-chain governance transactions; e287 validation weights are inference/epoch participation signals only. Per-voter governance power must come from exact historical gov/staking data or remain `unknown`.
