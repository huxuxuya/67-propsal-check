# Proposal 67 Governance Power Evidence

This report separates on-chain governance evidence from inference epoch timing.

- Voting end time: 2026-06-05T22:09:02.699803591Z
- Last block before voting end: 4433308 at 2026-06-05T22:08:57.716062379Z
- First block after voting end: 4433309 at 2026-06-05T22:09:03.332831118Z
- Archive gov votes decoded: 24
- Archive gov votes decoded after first post-end block: 0
- Tx search unique voters: 24
- Archive gov voters match tx_search voters: True
- Archive aggregate tally: {'yes': 319920, 'abstain': 744, 'no': 150, 'no_with_veto': 84623}
- Archive aggregate tally after first post-end block: {'yes': 319920, 'abstain': 744, 'no': 150, 'no_with_veto': 84623}
- Final proposal tally: {'yes': 319920, 'abstain': 744, 'no': 150, 'no_with_veto': 84623}
- Archive tally matches final proposal tally: True
- Per-voter governance power status: unknown

Per-voter governance power is not inferred from inference epoch weights. Archive gov Votes stores voter options, not exact per-voter power. At the first post-end block, gov Votes is empty while TallyResult remains final, so the investigation uses the last pre-end gov Votes snapshot plus the final aggregate TallyResult. Historical REST gov/staking probes failed for the boundary heights, and the standard staking validator response does not by itself provide Gonka's chain-specific governance power calculation.

Raw evidence is saved under `data/governance_power_67/raw/` with the archive RPC source redacted as `GONKA_RPC_URL`.
