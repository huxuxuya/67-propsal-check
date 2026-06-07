# ComputeGroupCap Weight Analysis — Epochs 265–276

## The Issue

The ComputeGroupCap mechanism limits any single model subgroup to
`cap_factor (0.75) × N-1 total network weight`. When the Kimi subgroup's
`confirmation_weight` exceeds this cap, the chain scales down every Kimi
participant's effective weight proportionally — causing systematic underpayment
relative to their actual confirmed work.

The cap was first breached in e265 and remained triggered through e276. The issue
was resolved by the v0.2.13 upgrade (block 4,267,300, mid-e276) which introduced a
lower WeightScaleFactor for Kimi (0.78), reducing its effective confirmation weight
below the 75% threshold. e277 is the first clean epoch.

---

## Kimi Weight vs Network — Full History

| Epoch | Kimi val_w | Kimi conf_w | Total val_w | Kimi val% | Kimi conf% | Participants | Nodes |
|-------|-----------|------------|------------|----------|-----------|-------------|-------|
| e265  | 377,276   | 640,858    | 904,177    | 41.7%    | **70.9%** | 20          | 44    |
| e266  | 59,933    | 115,164    | 335,159    | 17.9%    | 34.4%     | 8           | 9     |
| e267  | 658,820   | 915,743    | 541,415    | 121.7%   | **169.1%**| 27          | 81    |
| e268  | 449,753   | 595,505    | 698,639    | 64.4%    | **85.2%** | 20          | 52    |
| e269  | 450,982   | 594,890    | 679,397    | 66.4%    | **87.6%** | 30          | 56    |
| e270  | 521,085   | 681,025    | 717,467    | 72.6%    | **94.9%** | 23          | 70    |
| e271  | 488,471   | 640,601    | 796,030    | 61.4%    | **80.5%** | 23          | 65    |
| e272  | 508,968   | 658,739    | 823,183    | 61.8%    | **80.0%** | 23          | 65    |
| e273  | 631,147   | 815,951    | 758,715    | 83.2%    | **107.5%**| 30          | 81    |
| e274  | 524,596   | 678,323    | 766,804    | 68.4%    | **88.5%** | 24          | 73    |
| e275  | 589,904   | 763,391    | 736,925    | 80.0%    | **103.6%**| 24          | 80    |
| e276  | 629,257   | 812,469    | 798,029    | 78.9%    | **101.8%**| 23          | 83    |
| e277+ | —         | —          | —          | —        | <75%      | —           | —     |

**Bold** = cap breached (>75% of total network weight).

---

## Compensation Paid Per Epoch

| Epoch | Issue type | Affected | Compensation (GONKA) | % of epoch reward |
|-------|-----------|---------|---------------------|-------------------|
| e265  | CPoC bug (separate) | 3 | 30,592 | 10.7% |
| e266  | Nonce bug (separate) | 18 operators + 9 delegators | 188,698 | 66.3% |
| e267  | ComputeGroupCap | 25 | 246,472 | 86.6% |
| e268  | ComputeGroupCap | 11 | 42,635 | 15.0% |
| e269  | ComputeGroupCap | 19 | 47,505 | 16.7% |
| e270  | ComputeGroupCap | 19 | 76,870 | 27.0% |
| e271  | ComputeGroupCap | 17 | 28,422 | 10.0% |
| e272  | ComputeGroupCap | 11 | 16,988 | 6.0% |
| e273  | ComputeGroupCap | 20 | 86,243 | 30.4% |
| e274  | ComputeGroupCap | 9  | 41,818 | 14.7% |
| e275  | ComputeGroupCap | 18 | 89,985 | 31.7% |
| e276  | ComputeGroupCap | 11 | 50,281 | 17.7% |

**Total ComputeGroupCap restitution (e267–e276): 727,219.35 GONKA**

Note: e265 and e266 compensated different bugs. The ComputeGroupCap issue
begins at e267 — the first epoch where Kimi's weight structurally dominated
the network.

---

## Root Cause: What Started the Breakdown

### Phase 1 — Kimi introduction (e251–e252)

Kimi-K2.6 was added to the network in epoch 251 with `penalty_start_epoch=251`.
Initial adoption was tiny: 5 participants, 6 nodes, conf_weight at 4.9% of total.
The network total weight was ~700–860k, dominated by Qwen operators.

### Phase 2 — Explosive node count growth (e253–e258)

Between e252 and e253 something decisive happened: Kimi conf_weight jumped from
5.7% to **51.0%** in a single epoch. The participant count went from 3 to 9 and
nodes from 3 to 10, but that alone doesn't explain the conf_weight explosion.
The key factor was that early Kimi operators had accumulated very high
`confirmation_weight` through CPoC rounds (e.g. `gonka17gpuntq09` had conf=110k
on a val_weight of only 1,023 — a 107x multiplier). When those operators re-entered
after absence, their stored CW dominated the subgroup instantly.

From e253 onward the growth was relentless:

| Epoch | Kimi nodes | Kimi conf% |
|-------|-----------|-----------|
| e252  | 3         | 5.7%      |
| e253  | 10        | 51.0%     |
| e254  | 34        | 60.0%     |
| e255  | 47        | 65.1%     |
| e256  | 49        | 70.3%     |
| e257  | 48        | 70.9%     |
| e258  | 52        | 72.7%     |

Each epoch ~5–10 new nodes joined. Kimi's original WSF was much higher than
Qwen's (0.3593), meaning each Kimi nonce contributed far more raw weight, and
CPoC accumulation compounded that advantage rapidly.

### Phase 3 — Cap first breached (e262–e264)

By e260 Kimi was at 73.2% of total — brushing the 75% cap. e262 was the first
clear breach at **76.8%**, with 21 participants and 57 nodes. e263 followed at
75.6%, e264 at 74.0% (just under). At this point the Qwen network was still
large (~1.0–1.1M total weight) which kept Kimi from going further.

### Phase 4 — External attack begins, cap triggers hard (e265)

An unknown external actor conducted a targeted attack using malicious requests designed
to crash vLLM instances running the Kimi model. The attack payload has since been
confirmed from production fleet logs (2026-05-14 17:41–18:05 UTC, epoch 264): a chat
completions request combining `stop_token_ids` containing out-of-bounds values with
`min_tokens >= 1` triggers a CUDA assert in vLLM's sampler (`apply_top_k_only`
performs a `gather` against an out-of-bounds index), killing the engine with
`EngineDeadError` — 5 min recovery per node. 16 crashes across 12 of 14 mlnodes were
observed from a single repeated payload signature. A second crash vector was also
exploited: `prompt_logprobs` on long prompts causes a vocab-sized `all_gather` OOM
(8 crashes/day on one mlnode, ~40 min downtime/day). A proxy nginx geo-module bug
(geo variables not expanded per-request) meant IP-based rate-limiting was also
non-functional during this period — all IPs shared one rate-limit bucket.

The attack first hit in e265: CPoC confirmation weights for Kimi participants collapsed
abnormally at block 4,103,171, reducing 3 operators' rewards significantly (30,592
GONKA compensation). Total network weight also dropped from 1.01M to **904k** as Qwen
operators churned out around the same time, tipping Kimi conf_weight to 70.9% and
triggering the cap.

Gateway patches were merged May 16–18: PR #1170 strips `min_tokens` when
`stop_token_ids` is present (the confirmed attack vector); PR #1171 strips
`prompt_logprobs`; PR #1180 adds CVE-class defenses (JSON schema recursion,
Jinja injection via `chat_template_kwargs`, body depth pre-scan); PR #1183
fixes the proxy geo-module bug restoring per-IP rate-limiting.

### Phase 5 — Attack escalates, network collapse and weight inversion (e266→e267)

The attack continued into e266 before the gateway patches landed (PRs #1170/#1171 merged
May 16, after e265 had already begun). With the devshard gateway still unpatched and
IP-based rate-limiting non-functional (proxy geo-module bug, fixed PR #1183 May 18),
the attacker succeeded in taking down most Kimi operators' inference nodes entirely.
Kimi presence collapsed from ~52 nodes to 9, and total network weight crashed from ~1M
to **335k**. This caused mass nonce exclusion and delegation penalties (188,698 GONKA
compensation).

The collapse destroyed the **N-1 reference weight** used by the cap formula for e267.

When Kimi operators came back online in e267 — now with 27 participants and
**81 nodes**, many carrying large accumulated CW — the subgroup's conf_weight was
915k against a cap reference of only 335k × 0.75 = 251k. Kimi's weight was
**3.6× above the cap**, causing the 169.1% conf% figure and 246,472 GONKA in
compensation — the worst single epoch of the entire incident.

The attack across e265–e266, by destroying the N-1 reference weight, directly amplified
the severity of the e267 inversion. Without it, the cap formula would have used
a ~1M reference and the breach would have been far smaller or not triggered at all.

### Phase 6 — Persistent breach despite partial recovery (e268–e275)

After e267 the network restabilised somewhat — total weight recovered to 700–820k
as Qwen operators returned. But Kimi's node count never dropped below 52 again
(compared to ~50 pre-e266), and the CW accumulation advantage meant conf_weight
stayed at 80–105% of total. The cap remained triggered every epoch.

### Resolution — v0.2.13 WSF reduction (e277)

v0.2.13 (block 4,267,300) reduced Kimi's WeightScaleFactor from its original high
value to **0.78**. This directly reduced the confirmation_weight each Kimi nonce
contributes to the CPoC aggregation, bringing Kimi's conf_weight share from
~100% down to **51.3%** in e277 — well below the 75% cap.

---

## How the Weight Became Unbalanced

### e265 — first breach, near miss

Kimi conf_weight reached 70.9% of total network — just below the 75% cap
in absolute terms but enough to trigger the cap mechanism for the largest
participants. Only 3 operators were affected. The network total weight was
still high (~904k) because many Qwen operators were active.

### e266 — collapse and reset

A nonce bug (separate issue) caused most Kimi operators to be excluded.
Only 8 Kimi participants remained, with minimal weight (17.9% val share).
Total network weight dropped sharply to 335k as the Kimi exodus removed
most of the weight. This epoch is anomalous — the cap was not the issue here.

### e267 — severe breach, weight inversion

With Kimi operators returning after the e266 nonce fix, Kimi val_weight
jumped to 658k — **121.7% of total network weight of 541k**. This is a
weight inversion: the Kimi subgroup alone outweighed the entire reported
network total. Kimi conf_weight hit 169.1% of total. The cap triggered hard,
causing 246,472 GONKA in compensation — the largest single-epoch payout.

The inversion occurred because the N-1 total weight used by the cap formula
referenced e266's collapsed network (335k) while e267 had recovered to a much
larger Kimi cohort. This lag in the reference weight amplified the breach.

### e268 — partial recovery

Total network weight recovered to 698k as more Qwen participants joined.
Kimi conf_weight fell to 85.2% of total — still above cap but improving.
Compensation dropped to 42,635 GONKA.

### e269–e272 — stabilisation attempt

Total network weight grew toward 700–820k as Qwen operators joined.
Kimi's conf_weight share oscillated between 80–95%, consistently above the
75% cap but no longer in inversion territory. Compensation settled into the
30–48k GONKA range per epoch.

The e272 dip (ratio 0.882, only 11 affected) coincided with several Kimi
operators being excluded mid-epoch (CPoC failures, statistical invalidations),
temporarily reducing Kimi's effective weight.

### e273 — second spike

Kimi node count jumped from 65 to 81 (30 participants). Kimi conf_weight
reached 107.5% of total — a second inversion. Total network weight had dipped
back to 758k as some Qwen operators churned out. Compensation spiked to 86,243 GONKA.

### e274–e275 — worsening trend

Despite Kimi node count returning to ~73–80, Kimi conf_weight remained above
100% of total network weight in e275 (103.6%). The ratio hit its highest value
yet at 1.284x. The trend shows Kimi's per-node confirmation weight was growing
faster than Qwen network capacity was being added.

### e276 — final affected epoch

v0.2.13 activated at block 4,267,300 (mid-epoch 276). Kimi conf_weight was at
101.8% of total (ratio 1.060) — cap still breached. Compensation is calculated
using group data queried at the true epoch end (block 4,279,520), matching what
the chain used for reward distribution. After the upgrade Kimi WSF dropped to
0.78, bringing the ratio below 0.75 for all subsequent epochs.

### e277 — resolved

Kimi conf_weight dropped to 51.3% of total network weight — well below the
75% cap. The issue is closed.

---

## conf/val Ratio Trend (e267–e276)

```
e267  1.749x  |###################################
e268  0.854x  |#################
e269  0.997x  |###################
e270  1.226x  |########################
e271  0.948x  |##################
e272  0.882x  |#################
e273  1.177x  |#######################
e274  0.967x  |###################
e275  1.284x  |#########################
e276  1.060x  |#####################  (pre-upgrade only)
e277  0.512x  |##########  RESOLVED
              0                        1.75x
```

- **Mean (e267–e276)**: 1.069x
- **Peak**: e267 at 1.749x (weight inversion)
- **Resolution**: e277 at 0.512x after v0.2.13 lowered Kimi WSF to 0.78

---

## Why Kimi conf_weight Persistently Exceeds val_weight

1. **CPoC accumulation**: Kimi nodes earn `confirmation_weight` through each
   successful CPoC round on top of their base weight. High-capacity nodes with
   many ML nodes accumulate CW much faster than smaller Qwen operators.

2. **Per-node inference volume**: Kimi handles significantly more inference
   requests per epoch due to higher capacity, directly feeding more CPoC
   validations and faster CW growth.

3. **Node count growth outpacing Qwen**: e273 and e275 saw Kimi at 80–81 nodes
   while Qwen participation was flat or declining. Each new Kimi node adds
   directly to the cap-exceeding numerator.

4. **N-1 weight lag**: the cap formula uses the previous epoch's total weight
   as its reference. When Kimi grows quickly between epochs (as in e267), the
   denominator lags behind the actual network state, amplifying the breach.

---

## Final Compensation Summary (e267–e276)

| Epoch | Affected | Compensation (GONKA) | Notes |
|-------|---------|---------------------|-------|
| e267  | 25      | 246,471.82          | weight inversion, worst epoch |
| e268  | 11      | 42,634.68           | |
| e269  | 19      | 47,504.58           | |
| e270  | 19      | 76,870.08           | |
| e271  | 17      | 28,422.15           | |
| e272  | 11      | 16,988.15           | |
| e273  | 20      | 86,243.30           | second inversion |
| e274  | 9       | 41,818.44           | |
| e275  | 18      | 89,984.78           | |
| e276  | 11      | 50,281.35           | queried at true epoch end (block 4,279,520) |
| **TOTAL** | | **727,219.35 GONKA** | |

Issue resolved in e277 following v0.2.13 upgrade (block 4,267,300).
No further compensation required.

---

## Conclusion: GRC Case Eligibility

**This case should not be treated as a GRC restitution case.**

The ComputeGroupCap breach and the resulting underpayments across e267–e276 were
a consequence of two compounding factors, neither of which is a protocol bug:

1. **Kimi's original WSF was too high** relative to the network's capacity to
   absorb it. This is a parameter calibration issue, not a code defect. The fix
   (lowering WSF to 0.78 in v0.2.13) was a deliberate protocol parameter
   adjustment, not a bug patch.

2. **The severity of the e265–e267 damage was caused by an external attack.** An
   unknown actor deliberately targeted Kimi operators with malicious vLLM requests
   starting in e265, escalating in e266 to crash most inference nodes and collapse
   network weight to 335k. This destroyed the N-1 reference weight and directly
   caused the worst epoch (e267) of the entire incident. The attack is external to
   the protocol — the chain behaved correctly given the state it observed. The
   specific crash vectors (confirmed from production logs) were: (a) `stop_token_ids`
   + `min_tokens` causing a vLLM CUDA assert (`EngineDeadError`, ~5 min recovery),
   and (b) `prompt_logprobs` on long prompts causing GPU OOM via vocab-sized
   `all_gather`. Both were patched at the devshard gateway (PRs #1170, #1171, May 16)
   along with broader CVE-class hardening (PR #1180, May 18) and a proxy rate-limiting
   bug fix (PR #1183, May 18) that had left all IPs sharing a single rate-limit bucket
   during the attack window.

The calculated shortfall (727,219.35 GONKA across e267–e276) represents the
difference between what operators should have received under correct parameters
and what the chain actually paid. No compensation has been distributed yet.

Regardless of whether these amounts are eventually paid out, this incident should
not be opened as a GRC case. GRC restitution addresses losses caused by
protocol-level bugs. This incident was caused by parameter miscalibration and an
external attack — both outside the GRC mandate. Opening a GRC case here would set
a precedent for compensating externally-induced network disruptions and parameter
tuning decisions.
