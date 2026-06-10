# gonka1007 ownership investigation

- Address: `gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv`
- Valoper: `gonkavaloper1007dchuqgdnute4qam70kmn56j2vfw388h4yhp`
- Inference URL: `http://178.105.174.27:8000`
- Validator key: `tpe7BLcggZjebLowWzBPv7N9525XYz419oXnLSmXQsU=`
- Epoch commit public key: `03a654c9be1fa2ae64cefc00d611b88e41faa00d907d5f0f1ca85682b7db2661ab`
- Generated: `2026-06-10T20:33:19.482318+00:00`

## Conclusion

- No strict human owner proof was found in the local dashboard data, Telegram/history exports, public-name enrichment, or shared-key/shared-host clusters.
- The strongest proven facts are operational/on-chain: this address received compensation, voted `yes`, and had zero voting power at the voting start snapshot but `57838` by the voting end snapshot.
- The voting power source is a self-delegation to its own valoper; this connects the voter account and validator operator but does not identify a person.
- The infrastructure points to Hetzner (`AS24940`, `HETZNER-DC`, `CLOUD-NBG1`, Germany); this is provider-level attribution only.

## Proven On-Chain / Snapshot Facts

- Compensation: `11262.520198` GONKA, component `cap_e267_e276`.
- Compensation epochs: `{'e265': 0.0, 'e266': 0.0, 'e267': 0.0, 'e268': 2384.499296, 'e269': 1089.182117, 'e270': 3289.208043, 'e271': 1132.160499, 'e272': 0.0, 'e273': 3367.470243, 'e274': 0.0, 'e275': 0.0, 'e276': 0.0}`.
- Vote: `yes` at height `4414864`, tx `2163756502FF44AF25F1F41C5E1791ACC4236C8DC1ECBB0A825FDC4228BBBBBC`.
- Voting power window: start `0`, end `57838`, status `power_at_end_only`.
- Voting epoch weights: `{'e285': 0, 'e286': 37261, 'e287': 57838}`.
- End delegation: `[{'balanceAmount': '57838', 'balanceDenom': 'ngonka', 'delegatorAddress': 'gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv', 'shares': '57838000000000000000000', 'validatorAddress': 'gonkavaloper1007dchuqgdnute4qam70kmn56j2vfw388h4yhp'}]`.
- Validator at voting end: `{'accountAddress': 'gonka1007dchuqgdnute4qam70kmn56j2vfw388h4yhp', 'delegatorShares': '57838000000000000000000', 'moniker': 'gonkavaloper1007dchuqgdnute4qam70kmn56j2vfw388h4yhp', 'operatorAddress': 'gonkavaloper1007dchuqgdnute4qam70kmn56j2vfw388h4yhp', 'status': 3, 'tokens': '57838'}`.

## Public Infrastructure

- Participant status: `INACTIVE`; join height `4132613`; last inference time `1779140555741`.
- Worker public key: `<empty>`.
- RIPE summary: `{'inetnum': '178.105.160.0/20', 'netname': 'CLOUD-NBG1', 'country': 'DE', 'org': 'ORG-HOA1-RIPE', 'mnt-by': 'HOS-GUN', 'created': '2026-05-11T12:10:27Z', 'last-modified': '2026-05-11T12:10:27Z', 'route': '178.104.0.0/15', 'descr': 'HETZNER-DC', 'origin': '24940'}`.

## Local Cluster Checks

- Same inference IP: `['gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv']`.
- Same validator key: `['gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv']`.
- Same epoch commit public key: `['gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv']`.

## Reward / Compensation Context

| Epoch | Claimed | Rewarded GONKA | Earned GONKA | Inferences | Missed |
|---:|:---:|---:|---:|---:|---:|
| 268 | True | 4332.010079 | 0.032687 | 1055 | 30 |
| 269 | True | 2385.568365 | 0.003032 | 590 | 21 |
| 270 | True | 6552.663433 | 0.084709 | 1750 | 39 |
| 271 | True | 4968.728344 | 0.126862 | 6721 | 114 |
| 273 | True | 5548.226164 | 0.0 | 0 | 0 |

## Epoch Commit Public Key Matches

| Epoch | Participant | Model | Count |
|---:|---|---|---:|
| 268 | `gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv` | `moonshotai/Kimi-K2.6` | 14528 |
| 269 | `gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv` | `moonshotai/Kimi-K2.6` | 7296 |
| 270 | `gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv` | `moonshotai/Kimi-K2.6` | 14880 |
| 271 | `gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv` | `moonshotai/Kimi-K2.6` | 22336 |
| 272 | `gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv` | `moonshotai/Kimi-K2.6` | 14912 |
| 273 | `gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv` | `moonshotai/Kimi-K2.6` | 15360 |

## Tx Trace Queries

| Query | Status | Count | Sample |
|---|---|---:|---|
| `sender` | `ok` | 40 | `4506025:7C35D0D0792DFF1AE26F64CFD7B6EA43C1836FDF3BBA834934CFBB885DB6919A, 4494309:D0E353F636A4014C1FD816AD27F4CF41ECC8428AAB9091866F433B8149C71659, 4473865:0DCC1FDD6EBEDF0C59EDC27898182B7088EB897649AE10C3FF69E3A2605A1544, 4457908:898895411DC461B339683F5F24BD3B65CF9D4DF4FECF088CA28711F28B438B67, 4457906:366E8EA98115C5BA0750F431259F3A15BE778F9D5FDEEBD7DBA4BF3B170161AB` |
| `transferRecipient` | `ok` | 51 | `4428980:C4A422D627AAA96C0FECDEE2348155FBC2E5E43084C9F2EB9911F2D2026DB9CD, 4410258:DA5E9CFFFEDA347B0C52F40EA7DBC629B2E175E21D9C6541671B5ADCDDC873BF, 4410218:D6A832F9D1196569F5B8423F9DBE28A112468AF742E4D008F63FABDD88731880, 4406683:0B0DBF30B7A825975985993BAE444D2A85AC4C66ABEF3146E9DBF7871C3BCB93, 4390297:22E7D86121A1222661C1DD7EB2847B7778F6CB0345DB089E60C95E5CA6D5F130` |
| `transferSender` | `ok` | 17 | `4506025:7C35D0D0792DFF1AE26F64CFD7B6EA43C1836FDF3BBA834934CFBB885DB6919A, 4494309:D0E353F636A4014C1FD816AD27F4CF41ECC8428AAB9091866F433B8149C71659, 4473865:0DCC1FDD6EBEDF0C59EDC27898182B7088EB897649AE10C3FF69E3A2605A1544, 4413519:3631B519F4F5767B3CB8B73EF6F4194294F0FCE93FA97FD306D0FFD437D4B6E4, 4398551:F9FC5EC2D05C0380E51F1A973FBE507B337290D5D7139C04739A2E3EA57B532C` |
| `delegateDelegator` | `ok` | 0 | `` |
| `createValidator` | `ok` | 0 | `` |

## Transfer Counterparties

| Counterparty | Incoming GONKA | Outgoing GONKA | Net GONKA | In txs | Out txs | Latest height |
|---|---:|---:|---:|---:|---:|---:|
| `gonka1rhmr93td57nwqxv08we74va095hfdh3wha7vyd` | 0.0 | 7130.0 | -7130.0 | 0 | 16 | 4506025 |
| `gonka1jftn8khawsmfn7shgzfjn27myu5d4zd6ns09y8` | 0.643265889 | 0.0 | 0.643265889 | 49 | 0 | 4428980 |
| `gonka1jrfmcl6ztdhtejv88j6fnmk0ex9ygj60dh46ak` | 0.1 | 0.0 | 0.1 | 1 | 0 | 4378165 |
| `gonka125vkkhk5tcj59jeq4fz9mt2zew6tcfuu42czm6` | 0.0 | 0.1 | -0.1 | 0 | 1 | 4130013 |
| `gonka1j7x6dv42xehe9e5au4ku3wvzwtqlegfjhlvzj6` | 0.1 | 0.0 | 0.1 | 1 | 0 | 4129921 |

### Counterparty Local Context

| Counterparty | Participant | Recipient | Voter | History signal |
|---|:---:|:---:|:---:|---|
| `gonka1rhmr93td57nwqxv08we74va095hfdh3wha7vyd` | False | False | False | - |
| `gonka1jftn8khawsmfn7shgzfjn27myu5d4zd6ns09y8` | False | False | False | history/Gonka Devs/messages5.html:37051 |
| `gonka1jrfmcl6ztdhtejv88j6fnmk0ex9ygj60dh46ak` | False | False | False | - |
| `gonka125vkkhk5tcj59jeq4fz9mt2zew6tcfuu42czm6` | False | False | False | - |
| `gonka1j7x6dv42xehe9e5au4ku3wvzwtqlegfjhlvzj6` | True | True | False | history/Gonka Devs/messages16.html:10637 |

### Recent Direct Flows

| Height | Direction | Counterparty | Amount GONKA | Tx |
|---:|---|---|---:|---|
| 4506025 | `out` | `gonka1rhmr93td57nwqxv08we74va095hfdh3wha7vyd` | 657.0 | `7C35D0D0792DFF1AE26F64CFD7B6EA43C1836FDF3BBA834934CFBB885DB6919A` |
| 4494309 | `out` | `gonka1rhmr93td57nwqxv08we74va095hfdh3wha7vyd` | 1314.0 | `D0E353F636A4014C1FD816AD27F4CF41ECC8428AAB9091866F433B8149C71659` |
| 4473865 | `out` | `gonka1rhmr93td57nwqxv08we74va095hfdh3wha7vyd` | 1839.0 | `0DCC1FDD6EBEDF0C59EDC27898182B7088EB897649AE10C3FF69E3A2605A1544` |
| 4428980 | `in` | `gonka1jftn8khawsmfn7shgzfjn27myu5d4zd6ns09y8` | 6.25e-07 | `C4A422D627AAA96C0FECDEE2348155FBC2E5E43084C9F2EB9911F2D2026DB9CD` |
| 4413519 | `out` | `gonka1rhmr93td57nwqxv08we74va095hfdh3wha7vyd` | 484.0 | `3631B519F4F5767B3CB8B73EF6F4194294F0FCE93FA97FD306D0FFD437D4B6E4` |
| 4410258 | `in` | `gonka1jftn8khawsmfn7shgzfjn27myu5d4zd6ns09y8` | 0.00155727 | `DA5E9CFFFEDA347B0C52F40EA7DBC629B2E175E21D9C6541671B5ADCDDC873BF` |
| 4410218 | `in` | `gonka1jftn8khawsmfn7shgzfjn27myu5d4zd6ns09y8` | 0.00772669 | `D6A832F9D1196569F5B8423F9DBE28A112468AF742E4D008F63FABDD88731880` |
| 4406683 | `in` | `gonka1jftn8khawsmfn7shgzfjn27myu5d4zd6ns09y8` | 6.25e-07 | `0B0DBF30B7A825975985993BAE444D2A85AC4C66ABEF3146E9DBF7871C3BCB93` |
| 4398551 | `out` | `gonka1rhmr93td57nwqxv08we74va095hfdh3wha7vyd` | 449.0 | `F9FC5EC2D05C0380E51F1A973FBE507B337290D5D7139C04739A2E3EA57B532C` |
| 4390297 | `in` | `gonka1jftn8khawsmfn7shgzfjn27myu5d4zd6ns09y8` | 0.022964507 | `22E7D86121A1222661C1DD7EB2847B7778F6CB0345DB089E60C95E5CA6D5F130` |
| 4383031 | `out` | `gonka1rhmr93td57nwqxv08we74va095hfdh3wha7vyd` | 377.0 | `BC16E3D42CE914631FC022BC20C7AFDD656E4C5F2F4E4C8E6D25153EB17C2624` |
| 4378165 | `in` | `gonka1jrfmcl6ztdhtejv88j6fnmk0ex9ygj60dh46ak` | 0.1 | `AEAFD0F41099A1FEA35ACE0C1E6E7785E8938D66399025CA319BB1FB76AC92FF` |
| 4374526 | `in` | `gonka1jftn8khawsmfn7shgzfjn27myu5d4zd6ns09y8` | 0.007964795 | `7AB6342F766EB3294D2F39353D4FFCACF40DAD499B8B1A3464C747174CFFA95A` |
| 4367377 | `out` | `gonka1rhmr93td57nwqxv08we74va095hfdh3wha7vyd` | 342.0 | `37BE0816C3C840C448805F7B7C3544E0FF1A93700E865DA1DA19DFBDE2785FCC` |
| 4360328 | `out` | `gonka1rhmr93td57nwqxv08we74va095hfdh3wha7vyd` | 292.0 | `AFEF0B89212A5613FAFCEF1CAAA9C102F69AB9AC062EB12326D3ED6B89E8A723` |
| 4358929 | `in` | `gonka1jftn8khawsmfn7shgzfjn27myu5d4zd6ns09y8` | 0.014758543 | `3BC8DFE83CB696E8EE1C37072ED2DADF44F07036255E174AB140E5E376F46EFC` |
| 4358882 | `in` | `gonka1jftn8khawsmfn7shgzfjn27myu5d4zd6ns09y8` | 0.025286415 | `CCDBDF7C4231AF0969A20F3190A0189AD4AA7E101DE8CBF780D664E4A31408EF` |
| 4358872 | `in` | `gonka1jftn8khawsmfn7shgzfjn27myu5d4zd6ns09y8` | 0.023979567 | `86066A78AE35F584CA70D36B4F9C7D3269C8648F34602FA62AEE4D3220525A20` |
| 4358867 | `in` | `gonka1jftn8khawsmfn7shgzfjn27myu5d4zd6ns09y8` | 0.079847505 | `D8109280E58CF8526DF45D87ABDCC660A44B892B9FB2859A884EEB6CB2E0C6D1` |
| 4358856 | `in` | `gonka1jftn8khawsmfn7shgzfjn27myu5d4zd6ns09y8` | 0.025680232 | `B163D516216D49C1D160EB8D17E8C42D545C2358F25BBA0D76867E0602E7A885` |

## History / Report Hits

- `history/Gonka Devs/messages16.html:24095` - Некоторые адреса не получили reward_coins за 272 только work_coins:<br><br>gonka1wt8sr9jxzpec65j7zkxsgh6edk3m6r8nlf5za4<br>gonka10079cnl3nuh2k82mhkm04dj0slhtw9kmjewwau<br>gonka1007g0ut3u4wjkay9hegqfev4pj90qgexwskmcw<br>gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv<br>gonka15munkmx6x7k6rqqeexjet4556p7at39ks9qgr5<br>gonka1ce02jjduga8jvwj8jx39mxn0jr345vgkx7lk2n<br><br>Возможно это не полный список.<br>Видимых причин этого не нашел.<br><br>UPD: оказывает miss rate высокий
- `reports/attribution_audit.md:224` - ### #15 gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv
- `reports/attribution_audit.md:226` - - Addresses: gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv
- `reports/benefit_power_matrix.csv:6` - 5,gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv,gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv,True,True,True,11262.520198,57838,yes,,,public_signal,0,2,26.078,review conflict narrative | prioritize owner attribution | enrich beneficiary identity,compensation_output:11262.520198 GONKA:high | proposal_vote:yes:high | epoch_commit_participant:e268 moonshotai/Kimi-K2.6 count=14528:medium | epoch_commit_participant:e269 moonshotai/Kimi-K2.6 count=7296:medium | epoch_commit_participant:e270 moonshotai/K
- `reports/benefit_power_matrix.md:75` - ### #5 gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv
- `reports/benefit_power_matrix.md:77` - - Address: `gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv`
- `reports/evidence_claims.csv:1688` - gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv,gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv,financial_or_epoch_activity,compensation_output,11262.520198 GONKA,high,False,data/proposal_67.json,data/proposal_67.json,"On-chain proposal output proves beneficiary address and amount, not human owner."
- `reports/evidence_claims.csv:1689` - gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv,03a654c9be1fa2ae64cefc00d611b88e41faa00d907d5f0f1ca85682b7db2661ab,financial_or_epoch_activity,epoch_commit_participant,e268 moonshotai/Kimi-K2.6 count=14528,medium,False,upstream/gonka-kimi-restitution/e268/epoch268_commits.json,https://github.com/votkon/gonka-kimi-restitution/blob/main/e268/epoch268_commits.json,Epoch commit activity links an address to model participation and public key usage.
- `reports/evidence_claims.csv:1690` - gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv,03a654c9be1fa2ae64cefc00d611b88e41faa00d907d5f0f1ca85682b7db2661ab,financial_or_epoch_activity,epoch_commit_participant,e269 moonshotai/Kimi-K2.6 count=7296,medium,False,upstream/gonka-kimi-restitution/e269/epoch269_commits.json,https://github.com/votkon/gonka-kimi-restitution/blob/main/e269/epoch269_commits.json,Epoch commit activity links an address to model participation and public key usage.
- `reports/evidence_claims.csv:1691` - gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv,03a654c9be1fa2ae64cefc00d611b88e41faa00d907d5f0f1ca85682b7db2661ab,financial_or_epoch_activity,epoch_commit_participant,e270 moonshotai/Kimi-K2.6 count=14880,medium,False,upstream/gonka-kimi-restitution/e270/epoch270_commits.json,https://github.com/votkon/gonka-kimi-restitution/blob/main/e270/epoch270_commits.json,Epoch commit activity links an address to model participation and public key usage.
- `reports/evidence_claims.csv:1692` - gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv,03a654c9be1fa2ae64cefc00d611b88e41faa00d907d5f0f1ca85682b7db2661ab,financial_or_epoch_activity,epoch_commit_participant,e271 moonshotai/Kimi-K2.6 count=22336,medium,False,upstream/gonka-kimi-restitution/e271/epoch271_commits.json,https://github.com/votkon/gonka-kimi-restitution/blob/main/e271/epoch271_commits.json,Epoch commit activity links an address to model participation and public key usage.
- `reports/evidence_claims.csv:1693` - gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv,03a654c9be1fa2ae64cefc00d611b88e41faa00d907d5f0f1ca85682b7db2661ab,financial_or_epoch_activity,epoch_commit_participant,e272 moonshotai/Kimi-K2.6 count=14912,medium,False,upstream/gonka-kimi-restitution/e272/epoch272_commits.json,https://github.com/votkon/gonka-kimi-restitution/blob/main/e272/epoch272_commits.json,Epoch commit activity links an address to model participation and public key usage.
- `reports/evidence_claims.csv:1694` - gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv,03a654c9be1fa2ae64cefc00d611b88e41faa00d907d5f0f1ca85682b7db2661ab,financial_or_epoch_activity,epoch_commit_participant,e273 moonshotai/Kimi-K2.6 count=15360,medium,False,upstream/gonka-kimi-restitution/e273/epoch273_commits.json,https://github.com/votkon/gonka-kimi-restitution/blob/main/e273/epoch273_commits.json,Epoch commit activity links an address to model participation and public key usage.
- `reports/evidence_claims.csv:1695` - gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv,gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv,governance,proposal_vote,yes,high,False,data/proposal_67_tx_search.json,data/proposal_67_tx_search.json,"Vote proves governance action by address, not human owner."
- `reports/evidence_claims.csv:1696` - gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv,gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv,public_identity,voting_end_epoch_anomaly,e287=57838 prev=37261 next=0 vote=yes@4414864,medium,False,data/voting_end_epochs/manifest.json,data/voting_end_epochs/manifest.json,Inference epoch weight/timing is operational evidence only. It is not governance voting power and does not prove whether a vote was counted.
- `reports/evidence_claims.csv:1697` - gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv,http://178.105.174.27:8000,public_infrastructure,participant_inference_url,http://178.105.174.27:8000,medium,False,docs/data/dashboard.json,docs/data/dashboard.json,Public self-declared metadata when proof=true; otherwise a public label/signal.
- `reports/evidence_claims.csv:1698` - gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv,inference_endpoint:http://178.105.174.27:8000,public_infrastructure,participant_inference_url,http://178.105.174.27:8000,medium,False,docs/data/dashboard.json,docs/data/dashboard.json,Graph edge; infrastructure/provider edges are signals only.
- `reports/evidence_claims.csv:1699` - gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv,url:http://178.105.174.27:8000,public_infrastructure,participant_inference_url,http://178.105.174.27:8000,medium,False,data/public_identity_signals.json,data/public_identity_signals.json,Graph edge; infrastructure/provider edges are signals only.
- `reports/evidence_claims.csv:1700` - gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv,host:178.105.174.27,public_infrastructure,same_inference_host,178.105.174.27,medium,False,data/public_identity_signals.json,data/public_identity_signals.json,Graph edge; infrastructure/provider edges are signals only.
- `reports/proposal_67_analysis.md:58` - | `gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv` | http://178.105.174.27:8000 | true | yes:1.000000000000000000 | 4414864 |
- `reports/proposal_67_final_votes.csv:14` - gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv,http://178.105.174.27:8000,true,yes:1.000000000000000000,4414864,2163756502FF44AF25F1F41C5E1791ACC4236C8DC1ECBB0A825FDC4228BBBBBC
- `reports/proposal_67_recipients.csv:18` - gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv,http://178.105.174.27:8000,http://178.105.174.27:8000,INACTIVE,0,11262.520198,0.000000,11262.520198,"e268,e269,e270,e271,e273",11262.520198,true
- `reports/public_name_enrichment.csv:10` - gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv,gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv,http://178.105.174.27:8000,recipient voter,11262.520198,57838,yes,public_name_or_metadata_signal,,,,,,,,http://178.105.174.27:8000,participant_inference_url:http://178.105.174.27:8000:medium,review recipient-voter conflict | corroborate voter owner | corroborate beneficiary owner
- `reports/public_name_enrichment.md:151` - ### gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv
- `reports/public_name_enrichment.md:153` - - Address: `gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv`
- `reports/public_name_enrichment.md:155` - - Best public name: http://178.105.174.27:8000
- `reports/public_name_enrichment.md:159` - - Inference URL: http://178.105.174.27:8000
- `reports/public_name_enrichment.md:163` - - participant_inference_url (medium, signal): http://178.105.174.27:8000
- `reports/public_name_enrichment.md:1185` - ### participant_inference_url: http://178.105.174.27:8000
- `reports/public_name_enrichment.md:1190` - - Addresses: gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv
- `reports/public_name_groups.csv:35` - participant_inference_url,http://178.105.174.27:8000,medium,False,gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv,1,11262.520198,57838,yes:57838.0,data/participants_by_address.json
- `reports/ranked_parties.csv:16` - 15,gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv,gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv,epoch_commit_participant recipient voter,11262.520198,34.203,medium,14,2.253,16,1.95,0,8,6,0,"No strict public owner proof. | Address both received compensation and voted. | e287 inference timing is an operational signal, not governance voting power."
- `reports/voting_power_window_comparison.csv:2` - gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv,gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv,yes,4414864,True,0,57838,power_at_end_only,archive_staking_no_voting_power,archive_staking_delegations_chain_like,0,1,2163756502FF44AF25F1F41C5E1791ACC4236C8DC1ECBB0A825FDC4228BBBBBC
- `reports/voting_power_window_comparison.md:16` - - gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv `gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv`: vote=yes tx_height=4414864 start_power=0 end_power=57838 status=power_at_end_only
- `reports/voting_window_power_reconciliation.csv:4` - ,single-address timing lead,,gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv,gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv,False,False,True,False,57838,37261,0,yes,4414864,57838,archive_staking_delegations_chain_like,True,0,partial_operational_timing_signal

## Evidence Claims

| Type | Subject | Value | Confidence | Proof | Caveat |
|---|---|---|---|:---:|---|
| `participant_inference_url` | `http://178.105.174.27:8000` | `http://178.105.174.27:8000` | `medium` | False | Public participant metadata links the node to this endpoint, not to a human owner. |
| `participant_validator_key` | `tpe7BLcggZjebLowWzBPv7N9525XYz419oXnLSmXQsU=` | `tpe7BLcggZjebLowWzBPv7N9525XYz419oXnLSmXQsU=` | `medium` | False | Validator key is unique in local snapshots but is not an owner proof. |
| `staking_self_delegation` | `gonkavaloper1007dchuqgdnute4qam70kmn56j2vfw388h4yhp` | `57838 ngonka self-delegated by voting end` | `high` | False | On-chain staking state proves voting-power source, not human owner. |
| `proposal_vote` | `gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv` | `yes at height 4414864` | `high` | False | Vote proves governance action by this address. |
| `compensation_output` | `gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv` | `11262.520198 GONKA` | `high` | False | Proposal output proves beneficiary address and amount, not human owner. |
| `ripe_asn` | `178.105.174.27` | `AS24940 HETZNER-DC / CLOUD-NBG1` | `medium` | False | Hosting provider attribution is infrastructure-only. |
| `top_transfer_counterparty` | `gonka1rhmr93td57nwqxv08we74va095hfdh3wha7vyd` | `net -7130.0 GONKA` | `high` | False | Transfer counterparty is an on-chain money-flow link, not human ownership proof. |
| `no_same_ip_cluster` | `178.105.174.27` | `No other local participant uses this IP` | `medium` | False | Absence in local data is not global proof. |
| `no_same_pubkey_cluster` | `03a654c9be1fa2ae64cefc00d611b88e41faa00d907d5f0f1ca85682b7db2661ab` | `No other local participant uses this epoch commit public key` | `medium` | False | Absence in local data is not global proof. |

## Remaining Gaps

- Need deeper tx history if RPC tx indexes expose funding/delegation/create-validator events beyond the sampled tx_search queries.
- Need non-local proof such as signed operator statement, public profile, or repeated reuse of the same account/IP/key in external sources before naming an owner.
