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
- Chain-like archive staking/delegation tally decimal: {'yes': '319920.586500000000000000', 'abstain': '744.717000000000000000', 'no': '150.098000000000000000', 'no_with_veto': '84623.598500000000000000'}
- Chain-like archive staking/delegation tally truncated: {'yes': 319920, 'abstain': 744, 'no': 150, 'no_with_veto': 84623}
- Chain-like truncated tally matches final proposal tally: True
- Archive bonded validators with non-zero power: 39
- Voters with non-zero archive voting power: 14
- Per-voter governance power status: exact_chain_like

Per-voter governance power is not inferred from inference epoch weights. The calculation follows the Gonka SDK gov tally path: collect all bonded validators with non-zero bonded tokens, apply each voter delegation as direct voter power, deduct voted delegator shares from validator self-votes, then add remaining validator voting power. Decimal weighted results are truncated by Cosmos SDK TallyResult serialization; the truncated result matches the final on-chain tally.

Raw evidence is saved under `data/governance_power_67/raw/` with the archive RPC source redacted as `GONKA_RPC_URL`.
