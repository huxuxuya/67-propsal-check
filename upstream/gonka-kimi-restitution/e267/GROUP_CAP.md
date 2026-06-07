# ComputeGroupCap — Mechanics and Impact on Epochs 267+

## What is ComputeGroupCap?

Gonka's delegation system supports multiple model groups. To prevent any single
non-initial model from dominating the network's total consensus weight, the chain
applies a **group weight cap** to every non-initial model group (Kimi is non-initial;
Qwen is the initial model and is always uncapped).

**Formula** (`delegation_weight_calculator.go:276-292`):
```
cap = cap_factor × total_network_weight_from_epoch_N-1
```

At epoch 267:
- `cap_factor` = 0.75 (from chain params)
- epoch 266 total network weight (N-1) = 335,159
- **Kimi group cap = 0.75 × 335,159 = 251,369**

The Kimi group's raw reconstructed weight from nonce commits in epoch 267 was
**899,487**, which exceeds the cap by 648,118 units. The chain applied a uniform
scale factor of `251,369 / 899,487 = 0.2795` to every Kimi participant's weight,
cutting it to roughly **28%** of the true earned weight.

---

## Where the Cap Is Applied

The cap operates on `ActiveParticipant.Weight` — the consensus weight used for the
validator set and stored in `ValidationWeights.Weight` in `EpochGroupData`.

**Key distinction:**

| Field | What it holds | Affected by cap? |
|-------|---------------|-----------------|
| `ValidationWeights.Weight` | Capped consensus weight | **Yes** — stored post-cap |
| `ValidationWeights.ConfirmationWeight` | Result of Confirmation PoC (CPoC) evaluation | Recorded independently from raw MLNode work |

The cap is applied during `onEndOfPoCValidationStage()` in `module.go`, before
CPoC runs. CPoC then confirms work against the (already capped) weight base.

---

## Why ConfirmationWeight > Weight in Epoch 267

Looking at the epoch 267 group data, many participants show
`confirmation_weight / weight` ratios of ~358% — i.e. their confirmed work is
3.5× their capped weight. This is the direct signature of the cap:

- The participant actually performed and confirmed, say, 10,000 units of Kimi work
- The chain stored `weight = 2,795` (capped at 27.95%)
- CPoC measured their actual output and recorded `confirmation_weight = 10,000`
- The chain's reward formula then rescales: `effective = confirmation_weight × weight / raw_total`
  which partially recovers the true value, but is still bounded by `weight`

The rescaling formula in `bitcoin_rewards.go:617-630`:
```go
effectiveWeight = confirmation_weight × weight / raw_total
// then capped at fullWeight (= weight)
```

So even with correct `confirmation_weight`, the reward is bounded above by `weight`
(the capped value). Participants could never earn more than their capped weight allowed,
regardless of how much work they confirmed.

---

## Compensation Methodology for Epochs 267+

The correct compensation approach is to reconstruct what each participant's reward
**would have been** without the cap, then subtract what they actually received.

### Reward formula used by the chain

```
reward_i = (effective_weight_i / total_full_weight) × epoch_theoretical_reward
```

where:
- `effective_weight_i` = `min(confirmation_weight_i × weight_i / raw_total_i, weight_i)`  ← capped
- `total_full_weight` = sum of all `weight_i` (capped denominator)

### Correct (uncapped) formula

Replace the cap with the full confirmed work:

```
correct_reward_i = (confirmation_weight_i / total_uncapped_confirmation_weight) × epoch_theoretical_reward
```

where `total_uncapped_confirmation_weight` = sum of all `confirmation_weight_i` across
all participants.

This uses `confirmation_weight` as both numerator and denominator — it reflects actual
confirmed PoC work, is computed independently by CPoC, and is not subject to the group cap.

**Compensation = correct_reward_i − actual_rewards_i** (floored at 0)

### Why confirmation_weight is the right basis

1. It is what the chain's CPoC mechanism independently verified as real work done.
2. It is already stored on-chain in `EpochGroupData.ValidationWeights.ConfirmationWeight`.
3. The chain itself uses it as the reward numerator — the only distortion is that it
   then rescales it back through the capped `weight`, artificially bounding the result.
4. Using `confirmation_weight / EpochGroupData.total_weight` matches the actual chain
   settlement denominator, producing the correct counterfactual reward.

---

## Epoch 267 Numbers

| Quantity | Value |
|----------|-------|
| Epoch 266 total weight (N-1 baseline) | 335,159 |
| cap_factor | 0.75 |
| Kimi group cap | 251,369 |
| Kimi raw weight from commits | 899,487 |
| Scale factor applied | 0.2795 (×28%) |
| Participants with Kimi commits | 27 |
| Total epoch members | 51 |

Most participants' `confirmation_weight / weight` ratios are ~358%, confirming the
~3.58× underpayment factor for Kimi contributors.

---

## Source References

| Topic | File | Lines |
|-------|------|-------|
| ComputeGroupCap formula | `x/inference/module/delegation_weight_calculator.go` | 276–292 |
| Cap applied in pipeline | `x/inference/module/delegation_weight_calculator.go` | 340–360 |
| confirmation_weight proto | `proto/inference/inference/epoch_group_data.proto` | 48–49 |
| Reward uses confirmation_weight | `x/inference/keeper/bitcoin_rewards.go` | 615–630 |
| Denominator uses full weight | `x/inference/keeper/bitcoin_rewards.go` | 597–603, 663–666 |
