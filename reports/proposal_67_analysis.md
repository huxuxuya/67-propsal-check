# Proposal 67 Kimi Restitution Analysis

Source data: upstream `gonka-kimi-restitution`, on-chain proposal #67, and Tendermint tx index for `proposal_vote.proposal_id='67'`.

## Executive summary

- Proposal #67 passed. Final tally: yes 319,920; no 150; abstain 744; no_with_veto 84,623.
- Compensation outputs: 52 non-zero recipients, total 946,509.93 GONKA.
- e265-e266 external attack component: 219,290.57 GONKA.
- e267-e276 ComputeGroupCap component: 727,219.35 GONKA.
- Multiplier from the original e265-only visible damage of 30,592.10 GONKA to final proposal: 30.94x.
- Final vote txs: 27 txs, 24 unique voters after last-vote-wins consolidation.
- Compensation recipients who also voted: 13.

## Why 30k became 946k

The 30,592.10 GONKA figure is only epoch 265 CPoC degradation for 3 operators. The proposal also includes epoch 266 nonce exclusion and delegation loss, then ten more epochs where the previous epoch's collapsed Kimi weight made ComputeGroupCap underpay otherwise healthy Kimi operators.

| Component | GONKA | Share |
|---|---:|---:|
| e265-e266 external attack and nonce/delegation loss | 219,290.57 | 23.2% |
| e267-e276 ComputeGroupCap underpayment | 727,219.35 | 76.8% |
| Total | 946,509.93 | 100.0% |

## Top recipients

| Address | Label | Total GONKA | Attack e265-e266 | Cap e267-e276 |
|---|---|---:|---:|---:|
| `gonka1qa90tgczc0k5dvk4l5nvlf5y6phgm6mg22sfjv` | http://135.181.56.61:8000 | 158,541.88 | 18,493.62 | 140,048.26 |
| `gonka17pw6099q758qwzewtrqmqpf5c2lrhr97fwqexu` | http://54.37.131.156:8000 | 101,147.81 | 47,784.37 | 53,363.44 |
| `gonka1uhqpup9fev3zahlx6n326lp0krznc6usjtx6lu` | http://65.21.232.177:8000 | 96,601.32 | 0.00 | 96,601.32 |
| `gonka1wthc28t25pg63hzvl07rl8e8r6km6hesl6jhsz` | http://57.128.30.101:8000 | 79,247.56 | 26,783.90 | 52,463.66 |
| `gonka1q5xt54wncgzk7dxv9x64uln68455g83wu9tugg` | http://89.169.97.113:8000 | 73,073.71 | 29,956.26 | 43,117.45 |
| `gonka10mmdjau4dnj8krs7sh7t7635ttnmq9u3vqgz09` | ancapex \| Mine from $1, no losses from node failures | 66,487.74 | 11,068.29 | 55,419.45 |
| `gonka1gvrrhjmy4w4mayvs2s5l23edj8ertcmtd2v4zr` | http://54.38.118.143:8000 | 52,290.20 | 0.00 | 52,290.20 |
| `gonka1j7x6dv42xehe9e5au4ku3wvzwtqlegfjhlvzj6` | http://178.104.95.5:8000 | 39,809.68 | 39,809.68 | 0.00 |
| `gonka1jrgm47v5eg876udmzg6j6glqcsd5x0vk6crpax` | http://95.217.121.189:8000 | 33,750.58 | 8,543.71 | 25,206.87 |
| `gonka10079cnl3nuh2k82mhkm04dj0slhtw9kmjewwau` | http://178.105.170.135:8000 | 20,610.39 | 0.00 | 20,610.39 |
| `gonka15munkmx6x7k6rqqeexjet4556p7at39ks9qgr5` | http://136.243.110.227:8000 | 18,234.89 | 0.00 | 18,234.89 |
| `gonka1yal0ysgzc860zt3y8cds8656tnueusgymftvkw` | http://94.130.152.246:8000 | 17,630.16 | 1,885.58 | 15,744.58 |

## Final voters

| Voter | Label | Recipient? | Final vote | Height |
|---|---|---:|---|---:|
| `gonka1gvrrhjmy4w4mayvs2s5l23edj8ertcmtd2v4zr` | http://54.38.118.143:8000 | true | yes:1.000000000000000000 | 4401130 |
| `gonka1scskt6wpnjnumsah6kjphmdu87vjgvcxmn4rxv` | http://57.131.17.61:8000 | true | yes:1.000000000000000000 | 4401160 |
| `gonka1gyk0aahvr3qeju4zx0nplfreej6cy4jjk8svc5` | http://69.48.159.137:8000/ | true | no_with_veto:1.000000000000000000 | 4401505 |
| `gonka1ym3np7guxart483yfdxnlztuazx22cjt0e4a2p` | Hyperfusion | false | no_with_veto:1.000000000000000000 | 4404760 |
| `gonka1tja3g2da45efhe2p83gk3whtussmgmtsdlgprt` | http://148.113.47.235:8000 | true | yes:1.000000000000000000 | 4406961 |
| `gonka1hwvel7n3zuk6wruefuzc356l9myske9stckwnz` | http://148.113.47.71:8000 | true | yes:1.000000000000000000 | 4406963 |
| `gonka1q5xt54wncgzk7dxv9x64uln68455g83wu9tugg` | http://89.169.97.113:8000 | true | yes:1.000000000000000000 | 4406965 |
| `gonka168rtjfkszuhcggg4dfyse4yh7xn9zwfglnkns2` | http://network000.kaitaku.ai:8000 | true | no_with_veto:1.000000000000000000 | 4412026 |
| `gonka1d694r00czmq75txghwjcuk07lxvc8d4ekgsha0` | http://network002.kaitaku.ai:8000 | false | no_with_veto:1.000000000000000000 | 4412030 |
| `gonka1zktn8j65wlys8a8e38hqhf4y3x6m4x04zskkrx` | http://65.108.198.21:8000 | true | no_with_veto:1.000000000000000000 | 4413730 |
| `gonka16r08lhm50zwjddmslfw2344z67r70vqul0dus6` | https:/gonka.top | false | no_with_veto:1.000000000000000000 | 4413853 |
| `gonka1wt8sr9jxzpec65j7zkxsgh6edk3m6r8nlf5za4` | http://88.99.213.222:8000 | true | no_with_veto:1.000000000000000000 | 4413855 |
| `gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv` | http://178.105.174.27:8000 | true | yes:1.000000000000000000 | 4414864 |
| `gonka1mgdgcll2f4m0cjekqyueheeu7y8adz0hddfnh2` |  | false | yes:1.000000000000000000 | 4416171 |
| `gonka1qwfrtz9c7kcrfkrrlne2pkcye74mj6ce33xdkl` | http://84.32.59.212:8000 | false | no_with_veto:1.000000000000000000 | 4422937 |
| `gonka1m58jds005cttwq2vt0p7yk6vy2aqg254cqqppf` | http://84.32.185.226:8000 | false | no_with_veto:1.000000000000000000 | 4422941 |
| `gonka1q9f3wphjnf633fevej30y4aw3nnw87hl0r7qe4` |  | false | no_with_veto:1.000000000000000000 | 4426014 |
| `gonka1vjz8csqsr0ph0lv0yylc4auypnzrld7y6l2feu` | http://95.216.112.248:8000 | false | no_with_veto:1.000000000000000000 | 4426629 |
| `gonka1kvmerzu64094dt9t62ea0cp75larh39ulzldum` | http://78.46.89.87:8000 | false | no_with_veto:1.000000000000000000 | 4429647 |
| `gonka10mmdjau4dnj8krs7sh7t7635ttnmq9u3vqgz09` | ancapex \| Mine from $1, no losses from node failures | true | yes:0.380100000000000000;no:0.005200000000000000;abstain:0.025800000000000000;no_with_veto:0.588900000000000000 | 4430015 |
| `gonka1fvly5jrewyjmjfgwah3khy9rttq4cqajcesv9p` | http://20.163.111.183:8000 | true | no_with_veto:1.000000000000000000 | 4430200 |
| `gonka1cuwejs77gectp3n32wg8q27hlsa4m3hqspf4ww` | http://20.171.77.105:8000 | true | no_with_veto:1.000000000000000000 | 4430201 |
| `gonka1naxyjmun6kl23htjdujwd6c5z5avgwapsrmfk3` | http://20.88.58.210:8000 | false | no_with_veto:1.000000000000000000 | 4430202 |
| `gonka1nmn039cgpkhmkzekpkfz3nkv9tcjckpn46jyrj` | http://94.237.52.191:8000 | false | yes:1.000000000000000000 | 4430417 |

## Notes

- Labels are public validator descriptions matched by validator key, falling back to public participant inference URLs. Empty label means no reliable public label was found in this pass.
- The final on-chain tally is voting-power weighted; the voter table is address-level and includes weighted vote options where a voter split their vote.
- The GRC off-chain vote in the upstream README is separate: 2 include, 6 exclude, 1 abstain. The repository does not identify those committee voters.
