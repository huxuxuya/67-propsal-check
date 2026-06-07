# Delegation Impact Analysis — Epoch 266

## Background

An external attack on Kimi vLLM nodes (which began in e265) escalated in epoch 266,
crashing most operators' inference nodes and causing 9 participants to be completely
excluded from the epoch group — they submitted Kimi nonces on-chain but their weight
was never registered. The confirmed attack vectors were malicious chat completions
requests combining `stop_token_ids` with `min_tokens` (triggers a vLLM CUDA assert,
`EngineDeadError`, ~5 min recovery) and `prompt_logprobs` on long prompts (GPU OOM).
Both were patched at the devshard gateway on May 16 2026 (PRs #1170, #1171), after
e266 had already run. As a result, anyone who had delegated their Kimi consensus weight
to one of those excluded operators was also harmed indirectly via the delegation penalty
mechanism.

---

## How PoC Delegation Works

Participants who don't run an MLNode directly can delegate their consensus weight
to an operator (a direct epoch member) for a given model. The delegation is frozen into
a **snapshot** at block `poc_start - deploy_window` (deploy_window = 500 blocks).

For each model, the chain resolves each non-direct participant into one of four modes:

| Mode | Condition | Effect |
|------|-----------|--------|
| `DIRECT` | Participant is a member of the epoch group | No penalty, earns rewards directly |
| `DELEGATE` | Delegation points at an operator who entered the epoch | `delegation_share` (5%) transferred to operator |
| `NONE` | No delegation set, or delegation points at a non-participating operator | `no_participation_penalty` (15%) deducted |
| `REFUSE` | Explicit refusal | `refusal_penalty` (10%) deducted |

Penalties accumulate additively across all eligible models and are capped at 100%.
They are applied to the participant's consensus weight before rewards are distributed.

Kimi (`moonshotai/Kimi-K2.6`) has `penalty_start_epoch = 251`, so penalties apply
from epoch 251 onward. Epoch 266 > 251, so the Kimi penalty was active.

**Source:** `inference-chain/x/inference/module/delegation_weight_adjustment.go`,
`delegation_weight_calculator.go`

---

## What Happened in Epoch 266

Because the attack prevented 9 operators from entering the epoch, any
participant whose Kimi delegation pointed at one of those operators was forced into
**`ModeNone`** instead of `ModeDelegate`.

This caused an **extra 10% weight penalty** per affected participant:

```
Expected (ModeDelegate):  -5%  weight transferred to operator
Actual   (ModeNone):      -15% weight deducted as penalty
Extra loss:               -10% of original consensus weight
```

The 9 excluded operators and the delegators who pointed to them:

| Excluded Operator | Kimi Nonces Submitted | Delegators Affected |
|-------------------|-----------------------|---------------------|
| `gonka1q5xt54wncgzk7dxv9x64uln68455g83wu9tugg` | 89,984 | 9 |
| `gonka1qa90tgczc0k5dvk4l5nvlf5y6phgm6mg22sfjv` | 55,552 | 0 |
| `gonka1jrgm47v5eg876udmzg6j6glqcsd5x0vk6crpax` | 25,664 | 0 |
| `gonka1c6fwzedfsmpu4jnjekv4cn7mvr7x7fuqd6uqt9` | 12,384 | 0 |
| `gonka1xwkesaxvdadh9wt9yyladu0r260s7whklcktds` | 12,896 | 0 |
| `gonka18xeqnspxpg2vncufnjne485rkaagwvz7whyn0d` | 6,080  | 0 |
| `gonka125n6kr5gvdup0lndfkps7t6rd6592panhrg3np` | 6,048  | 0 |
| `gonka1yal0ysgzc860zt3y8cds8656tnueusgymftvkw` | 5,664  | 0 |
| `gonka1wkgawwdzj623ss8eywayzdj6qcgr2llygactje` | 6,496  | 0 |

Only `gonka1q5xt54...` had active Kimi delegations pointing at it at snapshot height
4104861 (epoch 266 start − 500 blocks).

---

## Affected Delegators

All 9 delegators pointed their Kimi delegation at `gonka1q5xt54wncgzk7dxv9x64uln68455g83wu9tugg`.

| Delegator | Post-penalty weight | Reconstructed original | Extra weight lost | Compensation (GONKA) |
|-----------|--------------------|-----------------------|-------------------|---------------------|
| `gonka1tja3g2da45efhe2p83gk3whtussmgmtsdlgprt` | 18,057 | 21,243.5 | 2,124.3 | 1,805.14 |
| `gonka1hwvel7n3zuk6wruefuzc356l9myske9stckwnz`  | 15,760 | 18,541.2 | 1,854.1 | 1,575.51 |
| `gonka12pcu9mcrpa4w4sjd9y3dsksnvu495ss6f9r4ra`  | 11,668 | 13,727.1 | 1,372.7 | 1,166.44 |
| `gonka1tlvg4kjx7ljd5thgd5fkgh39q6lu8cmxupktgg`  |  1,763 |  2,074.1 |   207.4 |   176.25 |
| `gonka1fvly5jrewyjmjfgwah3khy9rttq4cqajcesv9p`  |  1,139 |  1,340.0 |   134.0 |   113.86 |
| `gonka1cuwejs77gectp3n32wg8q27hlsa4m3hqspf4ww`  |  1,084 |  1,275.3 |   127.5 |   108.37 |
| `gonka1tmk2tzdneht6smu34pkmqdvu7p34qavvmwtwq2`  |  1,006 |  1,183.5 |   118.3 |   100.57 |
| `gonka1gyk0aahvr3qeju4zx0nplfreej6cy4jjk8svc5`  |    310 |    364.7 |    36.5 |    30.99 |
| `gonka14ef2pxjge75gflqftn7m2wy0xv59gq9uc7qnct`  |    156 |    183.5 |    18.4 |    15.60 |

**Total delegation compensation: 5,092.73 GONKA**

---

## Compensation Methodology

1. Recover each delegator's original weight before penalty:
   `original = chain_weight / (1 - 0.15)`

2. Calculate the extra weight lost vs what should have happened:
   `extra_loss = original * (0.15 - 0.05) = original * 0.10`

3. Convert weight loss to reward loss using the epoch reward pool:
   `compensation = extra_loss / total_epoch_weight * epoch_theoretical_reward`

Chain params used:
- `no_participation_penalty` = 0.15 (actual, ModeNone)
- `delegation_share` = 0.05 (expected, ModeDelegate)
- `epoch_theoretical_reward` = 284,797.19 GONKA
- `total_epoch_weight` = 335,159 (post-adjustment, as used by the chain)

**Script:** `calculate_delegation_compensation_266.py`
**Output:** `delegation_compensation_266.csv`, `delegation_compensation_266.json`

---

## Data Sources

- Delegation snapshot queried at height **4104861** (`poc_start 4105361 − deploy_window 500`)
  via: `inferenced query inference poc-delegation <address> --height 4104861`
- Epoch 266 group data (actual chain weights): `epoch266_group_data.json`
- Epoch 266 performance summaries (actual rewards): `epoch266_performance.json`
- Kimi delegation state also cross-checked via REST:
  `https://node3.gonka.ai/chain-api/productscience/inference/inference/poc_delegation/<address>`
