# Proposal 67 Voting-Window Power Reconciliation

This report reconciles e287 inference timing signals with exact archive-derived governance voting power. Inference epoch weight is operational timing evidence only; counted governance influence is the archive staking/delegation voting power.

- e287 timing rows: 17
- Voted during e287 with non-zero governance power: 2
- Voted during e287 with zero governance power: 4
- Full enter-vote-exit rows with non-zero governance power: 0

## Full Enter-Vote-Exit With Power

No row currently satisfies all three operational conditions (entered e287, voted during e287, exited after e287) while also having non-zero archive governance voting power.

## Voted During e287 With Power

- ancapex | Mine from $1, no losses from node failures `gonka10mmdjau4dnj8krs7sh7t7635ttnmq9u3vqgz09`: vote=no_with_veto power=28865 e287_weight=28865 entered=False exited=False
- http://94.237.52.191:8000 `gonka1nmn039cgpkhmkzekpkfz3nkv9tcjckpn46jyrj`: vote=yes power=20647 e287_weight=20647 entered=False exited=False
