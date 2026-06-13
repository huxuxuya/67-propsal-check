# Compensation Package Breakdown

This note splits the `votkon/gonka-kimi-restitution` package into validation-sized
components. The goal is to validate each compensation mechanism separately instead of
mixing payout formulas with diagnostic reconstruction charts.

Source repository snapshot: `upstream/gonka-kimi-restitution`.

Total package amount from `aggregate_compensation.csv`: **946,509.925002 GONKA**.

## Component Summary

| Component | Epochs | Mechanism | Paid (GONKA) | Validation focus |
|---|---:|---|---:|---|
| e265 CPoC degradation | 265 | Kimi operators entered, then confirmation weight degraded during CPoC | 30,592.104862 | healthy/end confirmation weights, participant weight, actual rewards |
| e266 nonce exclusion | 266 | Kimi/Qwen nonce commits reconstruct weight that was absent or undercounted in epoch group | 183,605.741812 | commit counts, model factors, reconstructed weight, actual rewards |
| e266 delegation penalty | 266 | Kimi delegators were forced into `ModeNone` instead of `ModeDelegate` because target operator was excluded | 5,092.727157 | delegation snapshot, excluded operator, extra 10% lost weight |
| e267-e276 ComputeGroupCap underpayment | 267-276 | Kimi confirmation work exceeded capped counted weight after e266 total_weight collapse | 722,219.351171 | confirmation weight, root total_weight denominator, actual rewards |

## Component 1: e265 CPoC Degradation

Epoch 265 is direct attack damage inside an epoch. Kimi operators entered the epoch
group, but confirmation weight dropped abnormally during CPoC.

Formula:

```text
compensation = max(0, weight / total_epoch_weight * epoch_reward - actual_rewards)
```

Control values:

| Metric | Value |
|---|---:|
| Affected participants | 3 |
| Denominator `total_epoch_weight` | 904,177 |
| Epoch reward | 284,932.503736 GONKA |
| Total compensation | 30,592.104862 GONKA |

Validate this component by checking:

| Check | Source |
|---|---|
| affected addresses and payout rows | `e265/compensation_265.csv`, `e265/compensation_265.json` |
| healthy vs end confirmation weights | `e265/epoch265_group_data_healthy.json`, `e265/epoch265_group_data_end.json` |
| actual received rewards | `e265/epoch265_performance.json` |

Do not validate this component by comparing it to e266 nonce reconstruction or e267
GroupCap formulas. It uses its own e265 total epoch weight and actual rewards.

## Component 2: e266 Nonce Exclusion

Epoch 266 is the main nonce reconstruction component. The attack escalated and many
Kimi operators either did not enter the epoch group or had model contribution
undercounted. The package reconstructs each address from on-chain nonce commits and
model weight factors.

Formula:

```text
compensation = max(0, reconstructed_weight / total_reconstructed_weight * epoch_reward - actual_rewards)
```

Control values:

| Metric | Value |
|---|---:|
| Affected nonce participants | 18 |
| Total reconstructed weight | 1,079,697.957709 |
| On-chain epoch total weight | 335,159 |
| Epoch reward | 284,797.192935 GONKA |
| Nonce compensation | 183,605.741812 GONKA |

Model commit reconstruction:

| Model | Raw commit count | Weight factor | Reconstructed weight |
|---|---:|---:|---:|
| Kimi | 609,820 | 1.2620856201975851 | 769,645.052909 |
| Qwen | 862,936 | 0.3593 | 310,052.904800 |
| Total | | | 1,079,697.957709 |

Validate this component by checking:

| Check | Source |
|---|---|
| per-address nonce reconstructed weights | `e266/compensation_266_nonces.csv` |
| raw nonce commits by address/model | `e266/epoch266_commits.json` |
| model factors and denominator | `e266/compensation_266.json` |
| actual rewards subtracted from fair share | `e266/epoch266_performance.json` |

Important distinction:

- The compensation denominator is `total_reconstructed_weight = 1,079,697.957709`.
- Dashboard cap simulations may show smaller Kimi-only counted values after cap, such as
  `678,132`. Those are diagnostics, not the payout denominator.

## Component 3: e266 Delegation Penalty

This is separate from nonce compensation. It pays Kimi delegators whose delegation target
was an excluded Kimi operator. Those delegators were resolved as `ModeNone` instead of
`ModeDelegate`.

Formula:

```text
original_weight = chain_weight_post_penalty / (1 - no_participation_penalty)
extra_weight_lost = original_weight * (no_participation_penalty - delegation_share)
compensation = extra_weight_lost / total_epoch_weight_on_chain * epoch_reward
```

Control values:

| Metric | Value |
|---|---:|
| Affected delegators | 9 |
| `no_participation_penalty` | 0.15 |
| `delegation_share` | 0.05 |
| Net extra penalty | 0.10 |
| Denominator `total_epoch_weight_on_chain` | 335,159 |
| Delegation compensation | 5,092.727157 GONKA |

Validate this component by checking:

| Check | Source |
|---|---|
| affected delegators and excluded operator | `e266/compensation_266_delegation.csv` |
| delegation mechanics and snapshot explanation | `e266/DELEGATION.md` |
| penalty params and denominator | `e266/compensation_266.json` |

Do not merge this weight basis with e266 nonce weight. The nonce component uses
`total_reconstructed_weight`; delegation uses the on-chain e266 total weight.

## Component 4: e267-e276 ComputeGroupCap Underpayment

Epochs 267-276 are cap-underpayment epochs. The e266 collapse lowered the N-1
`total_weight` used by `ComputeGroupCap`; when Kimi returned, the cap limited counted
Kimi weight while Kimi operators still had higher confirmation work.

Formula:

```text
compensation = max(0, confirmation_weight / root_total_weight * epoch_reward - actual_rewards)
```

Eligibility rule for validation:

- include only rows with `compensation_ngonka > 0`;
- participants with zero compensation or zero rewards are not counted as affected payout rows.

Per-epoch control values:

| Epoch | Paid rows | Root total weight | Sum validation weight | Sum confirmation weight | Compensation (GONKA) |
|---:|---:|---:|---:|---:|---:|
| 267 | 24 | 541,415 | 264,238 | 705,309 | 246,471.823957 |
| 268 | 10 | 698,639 | 269,308 | 325,099 | 42,634.684509 |
| 269 | 18 | 679,397 | 352,027 | 420,931 | 47,504.581759 |
| 270 | 18 | 717,467 | 453,798 | 631,698 | 76,870.083553 |
| 271 | 16 | 796,030 | 485,868 | 498,135 | 28,422.154069 |
| 272 | 10 | 823,183 | 351,107 | 331,644 | 16,988.149548 |
| 273 | 19 | 758,715 | 438,964 | 641,992 | 86,243.303557 |
| 274 | 8 | 766,804 | 372,034 | 469,277 | 41,818.441791 |
| 275 | 17 | 736,925 | 452,628 | 663,502 | 89,984.775198 |
| 276 | 11 | 798,029 | 360,013 | 432,120 | 50,281.353229 |

Validate this component by checking:

| Check | Source |
|---|---|
| per-address validation/confirmation weights | `e267/compensation_267.json` through `e276/compensation_276.json` |
| root denominator used in formula | `root_total_weight` in each epoch JSON |
| actual rewards subtracted from correct reward | `epoch<N>_performance.json` in each epoch folder |
| positive payout row count | rows where `compensation_ngonka > 0` |

Important distinction:

- `confirmation_weight` is the compensation basis.
- `validation_weight` is the weight already counted by the capped chain state.
- `root_total_weight` is the denominator used by the package.
- Graph deltas such as "no-attack simulated counted weight" are not payout formulas.

## Diagnostic Reconstructions Are Not Payout Components

The dashboard and investigation files may show reconstruction metrics that are useful
for explaining damage but should not be validated as direct compensation components.

| Diagnostic metric | What it explains | Why it differs from payout basis |
|---|---|---|
| No-attack cap simulation | What Kimi/Qwen counted weight might have been if e266 did not collapse the cap basis | Applies cap carry-forward assumptions; not a per-address payout formula |
| Full CPoC scan | Extra degradation or missing entrants found from saved CPoC snapshots | Diagnostic coverage can include non-compensated rows or use reconstructed what-if weights |
| e266 missing entrants from e265 start weight | Operators that were present in previous Kimi start snapshot but absent from e266 start snapshot | Useful for damage scale, but nonce package payout is based on e266 nonce commits |
| e267 no-attack `+489k` counted delta | Difference between actual counted Kimi and simulated no-attack counted Kimi | e267 payout uses `confirmation_weight / root_total_weight`, not this graph delta |

Validation should start from the four payout components above. Diagnostics can then be
used to explain why the component exists, not to recompute the amount unless a separate
methodology is being proposed.

## Validation Order

1. Reconcile aggregate total from `aggregate_compensation.csv`: **946,509.925002 GONKA**.
2. Validate e265 CPoC degradation independently.
3. Validate e266 nonce exclusion independently.
4. Validate e266 delegation penalty independently.
5. Validate e267-e276 GroupCap underpayment epoch by epoch.
6. Only after payout components match, compare diagnostic reconstructions to explain
   cause and scale.
