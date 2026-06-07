# Proposal 67 Interest Clusters

Clusters combine compensation, exact archive-derived governance voting power, vote direction, and public evidence boundaries. `public_owner_proof` clusters are stronger; `infrastructure_or_public_signal` and `shared_public_label_only` clusters are investigation leads and must not be treated as ownership proof by themselves.

## #1 http://89.169.97.113:8000

- Cluster: label:http://89.169.97.113:8000 (label; shared_public_label_only)
- Addresses: gonka1q5xt54wncgzk7dxv9x64uln68455g83wu9tugg
- Roles: epoch_commit_participant, operator, recipient, voter
- Compensation: 73073.708453 GONKA across 1 recipients
- Exact governance voting power: 92840 across 1 voters
- Vote power split: yes=92840.0
- Recipient-voter overlap: 1
- Interest score: 46.531
- Caveats: No strict public owner proof. | Cluster may be based on infrastructure/public signals, not ownership. | At least one address both received compensation and voted.

Top evidence:
- gonka1q5xt54wncgzk7dxv9x64uln68455g83wu9tugg compensation_output (high, signal): 73073.708453 GONKA
- gonka1q5xt54wncgzk7dxv9x64uln68455g83wu9tugg matched_validator_moniker (high, signal): gonkavaloper1q5xt54wncgzk7dxv9x64uln68455g83wq96ml9
- gonka1q5xt54wncgzk7dxv9x64uln68455g83wu9tugg matched_validator_moniker (high, signal): gonkavaloper1q5xt54wncgzk7dxv9x64uln68455g83wq96ml9
- gonka1q5xt54wncgzk7dxv9x64uln68455g83wu9tugg proposal_vote (high, signal): yes
- gonka1q5xt54wncgzk7dxv9x64uln68455g83wu9tugg telegram_operator_statement (high, signal): Успевайте заделегировать Кими до след эпохи чтобы не потерять 15% ! Если ищите кому делегировать, то можно вот сюда:./inferenced tx inference set-poc-delegation moonshotai/Kimi-K2.6 gonka1q5xt54wncgzk7dxv9x64uln68455g83wu9tugg \ --from <your-account-key> \ --node http://node2.gonka.ai:8000/chain-rpc/ \ --chain-id gonka-mainnet \ --keyring-backend file \ --gas auto \ --gas-adjustment 1.3 \ -yЭто топ 1 сегмент по весу...

## #2 http://54.38.118.143:8000

- Cluster: label:http://54.38.118.143:8000 (label; shared_public_label_only)
- Addresses: gonka1gvrrhjmy4w4mayvs2s5l23edj8ertcmtd2v4zr
- Roles: epoch_commit_participant, recipient, voter
- Compensation: 52290.195676 GONKA across 1 recipients
- Exact governance voting power: 86433 across 1 voters
- Vote power split: yes=86433.0
- Recipient-voter overlap: 1
- Interest score: 40.42
- Caveats: No strict public owner proof. | Cluster may be based on infrastructure/public signals, not ownership. | At least one address both received compensation and voted.

Top evidence:
- gonka1gvrrhjmy4w4mayvs2s5l23edj8ertcmtd2v4zr compensation_output (high, signal): 52290.195676 GONKA
- gonka1gvrrhjmy4w4mayvs2s5l23edj8ertcmtd2v4zr matched_validator_moniker (high, signal): gonkavaloper1gvrrhjmy4w4mayvs2s5l23edj8ertcmt32aj4w
- gonka1gvrrhjmy4w4mayvs2s5l23edj8ertcmtd2v4zr matched_validator_moniker (high, signal): gonkavaloper1gvrrhjmy4w4mayvs2s5l23edj8ertcmt32aj4w
- gonka1gvrrhjmy4w4mayvs2s5l23edj8ertcmtd2v4zr proposal_vote (high, signal): yes
- gonka1gvrrhjmy4w4mayvs2s5l23edj8ertcmtd2v4zr epoch_commit_participant (medium, signal): e268 Qwen/Qwen3-235B-A22B-Instruct-2507-FP8 count=8512

## #3 http://135.181.56.61:8000

- Cluster: label:http://135.181.56.61:8000 (label; shared_public_label_only)
- Addresses: gonka1qa90tgczc0k5dvk4l5nvlf5y6phgm6mg22sfjv
- Roles: epoch_commit_participant, recipient
- Compensation: 158541.879456 GONKA across 1 recipients
- Exact governance voting power: 0 across 0 voters
- Vote power split: none
- Recipient-voter overlap: 0
- Interest score: 39.635
- Caveats: No strict public owner proof. | Cluster may be based on infrastructure/public signals, not ownership.

Top evidence:
- gonka1qa90tgczc0k5dvk4l5nvlf5y6phgm6mg22sfjv compensation_output (high, signal): 158541.879456 GONKA
- gonka1qa90tgczc0k5dvk4l5nvlf5y6phgm6mg22sfjv matched_validator_moniker (high, signal): gonkavaloper1qa90tgczc0k5dvk4l5nvlf5y6phgm6mgk2pw9p
- gonka1qa90tgczc0k5dvk4l5nvlf5y6phgm6mg22sfjv matched_validator_moniker (high, signal): gonkavaloper1qa90tgczc0k5dvk4l5nvlf5y6phgm6mgk2pw9p
- gonka1qa90tgczc0k5dvk4l5nvlf5y6phgm6mg22sfjv epoch_commit_participant (medium, signal): e266 moonshotai/Kimi-K2.6 count=55552
- gonka1qa90tgczc0k5dvk4l5nvlf5y6phgm6mg22sfjv epoch_commit_participant (medium, signal): e267 moonshotai/Kimi-K2.6 count=56352

## #4 ancapex | Mine from $1, no losses from node failures

- Cluster: label:ancapex | Mine from $1, no losses from node failures (label; public_owner_proof)
- Addresses: gonka10mmdjau4dnj8krs7sh7t7635ttnmq9u3vqgz09
- Roles: epoch_commit_participant, recipient, voter
- Compensation: 66487.744752 GONKA across 1 recipients
- Exact governance voting power: 28865 across 1 voters
- Vote power split: no_with_veto=28865.0
- Recipient-voter overlap: 1
- Interest score: 35.746
- Caveats: At least one address both received compensation and voted.

Top evidence:
- gonka10mmdjau4dnj8krs7sh7t7635ttnmq9u3vqgz09 matched_validator_identity (high, proof): B22258DF68546529
- gonka10mmdjau4dnj8krs7sh7t7635ttnmq9u3vqgz09 matched_validator_identity (high, proof): B22258DF68546529
- gonka10mmdjau4dnj8krs7sh7t7635ttnmq9u3vqgz09 matched_validator_moniker (high, proof): ancapex | Mine from $1, no losses from node failures
- gonka10mmdjau4dnj8krs7sh7t7635ttnmq9u3vqgz09 matched_validator_moniker (high, proof): ancapex | Mine from $1, no losses from node failures
- gonka10mmdjau4dnj8krs7sh7t7635ttnmq9u3vqgz09 validator_key_match (high, proof): 1MsHbnXp09bUZK/WEJVpwTOiZgKN+P5R7zuXXQUnYDM=

## #5 http://178.105.174.27:8000

- Cluster: label:http://178.105.174.27:8000 (label; shared_public_label_only)
- Addresses: gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv
- Roles: epoch_commit_participant, recipient, voter
- Compensation: 11262.520198 GONKA across 1 recipients
- Exact governance voting power: 57838 across 1 voters
- Vote power split: yes=57838.0
- Recipient-voter overlap: 1
- Interest score: 26.078
- Caveats: No strict public owner proof. | Cluster may be based on infrastructure/public signals, not ownership. | At least one address both received compensation and voted.

Top evidence:
- gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv compensation_output (high, signal): 11262.520198 GONKA
- gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv proposal_vote (high, signal): yes
- gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv epoch_commit_participant (medium, signal): e268 moonshotai/Kimi-K2.6 count=14528
- gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv epoch_commit_participant (medium, signal): e269 moonshotai/Kimi-K2.6 count=7296
- gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv epoch_commit_participant (medium, signal): e270 moonshotai/Kimi-K2.6 count=14880

## #6 http://54.37.131.156:8000

- Cluster: label:http://54.37.131.156:8000 (label; shared_public_label_only)
- Addresses: gonka17pw6099q758qwzewtrqmqpf5c2lrhr97fwqexu
- Roles: epoch_commit_participant, recipient
- Compensation: 101147.807219 GONKA across 1 recipients
- Exact governance voting power: 0 across 0 voters
- Vote power split: none
- Recipient-voter overlap: 0
- Interest score: 25.287
- Caveats: No strict public owner proof. | Cluster may be based on infrastructure/public signals, not ownership.

Top evidence:
- gonka17pw6099q758qwzewtrqmqpf5c2lrhr97fwqexu compensation_output (high, signal): 101147.807219 GONKA
- gonka17pw6099q758qwzewtrqmqpf5c2lrhr97fwqexu epoch_commit_participant (medium, signal): e265 Qwen/Qwen3-235B-A22B-Instruct-2507-FP8 count=56288
- gonka17pw6099q758qwzewtrqmqpf5c2lrhr97fwqexu epoch_commit_participant (medium, signal): e265 moonshotai/Kimi-K2.6 count=144224
- gonka17pw6099q758qwzewtrqmqpf5c2lrhr97fwqexu epoch_commit_participant (medium, signal): e266 Qwen/Qwen3-235B-A22B-Instruct-2507-FP8 count=59296
- gonka17pw6099q758qwzewtrqmqpf5c2lrhr97fwqexu epoch_commit_participant (medium, signal): e266 moonshotai/Kimi-K2.6 count=153408

## #7 http://65.21.232.177:8000

- Cluster: label:http://65.21.232.177:8000 (label; shared_public_label_only)
- Addresses: gonka1uhqpup9fev3zahlx6n326lp0krznc6usjtx6lu
- Roles: epoch_commit_participant, recipient
- Compensation: 96601.320933 GONKA across 1 recipients
- Exact governance voting power: 0 across 0 voters
- Vote power split: none
- Recipient-voter overlap: 0
- Interest score: 24.15
- Caveats: No strict public owner proof. | Cluster may be based on infrastructure/public signals, not ownership.

Top evidence:
- gonka1uhqpup9fev3zahlx6n326lp0krznc6usjtx6lu compensation_output (high, signal): 96601.320933 GONKA
- gonka1uhqpup9fev3zahlx6n326lp0krznc6usjtx6lu matched_validator_moniker (high, signal): gonkavaloper1uhqpup9fev3zahlx6n326lp0krznc6uswthag3
- gonka1uhqpup9fev3zahlx6n326lp0krznc6usjtx6lu matched_validator_moniker (high, signal): gonkavaloper1uhqpup9fev3zahlx6n326lp0krznc6uswthag3
- gonka1uhqpup9fev3zahlx6n326lp0krznc6usjtx6lu epoch_commit_participant (medium, signal): e270 moonshotai/Kimi-K2.6 count=68352
- gonka1uhqpup9fev3zahlx6n326lp0krznc6usjtx6lu epoch_commit_participant (medium, signal): e271 moonshotai/Kimi-K2.6 count=59712

## #8 http://network000.kaitaku.ai:8000

- Cluster: label:http://network000.kaitaku.ai:8000 (label; shared_public_label_only)
- Addresses: gonka168rtjfkszuhcggg4dfyse4yh7xn9zwfglnkns2
- Roles: epoch_commit_participant, recipient, voter
- Compensation: 11021.18308 GONKA across 1 recipients
- Exact governance voting power: 25278 across 1 voters
- Vote power split: no_with_veto=25278.0
- Recipient-voter overlap: 1
- Interest score: 21.366
- Caveats: No strict public owner proof. | Cluster may be based on infrastructure/public signals, not ownership. | At least one address both received compensation and voted.

Top evidence:
- gonka168rtjfkszuhcggg4dfyse4yh7xn9zwfglnkns2 compensation_output (high, signal): 11021.18308 GONKA
- gonka168rtjfkszuhcggg4dfyse4yh7xn9zwfglnkns2 matched_validator_moniker (high, signal): gonkavaloper168rtjfkszuhcggg4dfyse4yh7xn9zwfgrn8588
- gonka168rtjfkszuhcggg4dfyse4yh7xn9zwfglnkns2 matched_validator_moniker (high, signal): gonkavaloper168rtjfkszuhcggg4dfyse4yh7xn9zwfgrn8588
- gonka168rtjfkszuhcggg4dfyse4yh7xn9zwfglnkns2 proposal_vote (high, signal): no_with_veto
- gonka168rtjfkszuhcggg4dfyse4yh7xn9zwfglnkns2 epoch_commit_participant (medium, signal): e265 moonshotai/Kimi-K2.6 count=10528

## #9 http://148.113.47.235:8000

- Cluster: label:http://148.113.47.235:8000 (label; shared_public_label_only)
- Addresses: gonka1tja3g2da45efhe2p83gk3whtussmgmtsdlgprt
- Roles: delegator, epoch_commit_participant, recipient, voter
- Compensation: 1805.142498 GONKA across 1 recipients
- Exact governance voting power: 31217 across 1 voters
- Vote power split: yes=31217.0
- Recipient-voter overlap: 1
- Interest score: 19.911
- Caveats: No strict public owner proof. | Cluster may be based on infrastructure/public signals, not ownership. | At least one address both received compensation and voted.

Top evidence:
- gonka1tja3g2da45efhe2p83gk3whtussmgmtsdlgprt compensation_output (high, signal): 1805.142498 GONKA
- gonka1tja3g2da45efhe2p83gk3whtussmgmtsdlgprt matched_validator_moniker (high, signal): gonkavaloper1tja3g2da45efhe2p83gk3whtussmgmts3lex5x
- gonka1tja3g2da45efhe2p83gk3whtussmgmtsdlgprt matched_validator_moniker (high, signal): gonkavaloper1tja3g2da45efhe2p83gk3whtussmgmts3lex5x
- gonka1tja3g2da45efhe2p83gk3whtussmgmtsdlgprt proposal_vote (high, signal): yes
- gonka1tja3g2da45efhe2p83gk3whtussmgmtsdlgprt epoch_commit_participant (medium, signal): e265 Qwen/Qwen3-235B-A22B-Instruct-2507-FP8 count=60352

## #10 http://57.128.30.101:8000

- Cluster: label:http://57.128.30.101:8000 (label; shared_public_label_only)
- Addresses: gonka1wthc28t25pg63hzvl07rl8e8r6km6hesl6jhsz
- Roles: epoch_commit_participant, recipient
- Compensation: 79247.555227 GONKA across 1 recipients
- Exact governance voting power: 0 across 0 voters
- Vote power split: none
- Recipient-voter overlap: 0
- Interest score: 19.812
- Caveats: No strict public owner proof. | Cluster may be based on infrastructure/public signals, not ownership.

Top evidence:
- gonka1wthc28t25pg63hzvl07rl8e8r6km6hesl6jhsz compensation_output (high, signal): 79247.555227 GONKA
- gonka1wthc28t25pg63hzvl07rl8e8r6km6hesl6jhsz epoch_commit_participant (medium, signal): e265 Qwen/Qwen3-235B-A22B-Instruct-2507-FP8 count=4544
- gonka1wthc28t25pg63hzvl07rl8e8r6km6hesl6jhsz epoch_commit_participant (medium, signal): e266 Qwen/Qwen3-235B-A22B-Instruct-2507-FP8 count=4480
- gonka1wthc28t25pg63hzvl07rl8e8r6km6hesl6jhsz epoch_commit_participant (medium, signal): e266 moonshotai/Kimi-K2.6 count=85632
- gonka1wthc28t25pg63hzvl07rl8e8r6km6hesl6jhsz epoch_commit_participant (medium, signal): e267 Qwen/Qwen3-235B-A22B-Instruct-2507-FP8 count=4096

## #11 http://148.113.47.71:8000

- Cluster: label:http://148.113.47.71:8000 (label; shared_public_label_only)
- Addresses: gonka1hwvel7n3zuk6wruefuzc356l9myske9stckwnz
- Roles: delegator, epoch_commit_participant, recipient, voter
- Compensation: 1575.513417 GONKA across 1 recipients
- Exact governance voting power: 19974 across 1 voters
- Vote power split: yes=19974.0
- Recipient-voter overlap: 1
- Interest score: 18.247
- Caveats: No strict public owner proof. | Cluster may be based on infrastructure/public signals, not ownership. | At least one address both received compensation and voted.

Top evidence:
- gonka1hwvel7n3zuk6wruefuzc356l9myske9stckwnz compensation_output (high, signal): 1575.513417 GONKA
- gonka1hwvel7n3zuk6wruefuzc356l9myske9stckwnz matched_validator_moniker (high, signal): gonkavaloper1hwvel7n3zuk6wruefuzc356l9myske9shc8fy0
- gonka1hwvel7n3zuk6wruefuzc356l9myske9stckwnz matched_validator_moniker (high, signal): gonkavaloper1hwvel7n3zuk6wruefuzc356l9myske9shc8fy0
- gonka1hwvel7n3zuk6wruefuzc356l9myske9stckwnz proposal_vote (high, signal): yes
- gonka1hwvel7n3zuk6wruefuzc356l9myske9stckwnz epoch_commit_participant (medium, signal): e265 Qwen/Qwen3-235B-A22B-Instruct-2507-FP8 count=51552

## #12 http://88.99.213.222:8000

- Cluster: label:http://88.99.213.222:8000 (label; shared_public_label_only)
- Addresses: gonka1wt8sr9jxzpec65j7zkxsgh6edk3m6r8nlf5za4
- Roles: epoch_commit_participant, recipient, voter
- Compensation: 10934.181496 GONKA across 1 recipients
- Exact governance voting power: 0 across 1 voters
- Vote power split: no_with_veto=0.0
- Recipient-voter overlap: 1
- Interest score: 17.734
- Caveats: No strict public owner proof. | Cluster may be based on infrastructure/public signals, not ownership. | Voter addresses in this cluster had zero archive governance voting power. | At least one address both received compensation and voted.

Top evidence:
- gonka1wt8sr9jxzpec65j7zkxsgh6edk3m6r8nlf5za4 compensation_output (high, signal): 10934.181496 GONKA
- gonka1wt8sr9jxzpec65j7zkxsgh6edk3m6r8nlf5za4 proposal_vote (high, signal): no_with_veto
- gonka1wt8sr9jxzpec65j7zkxsgh6edk3m6r8nlf5za4 epoch_commit_participant (medium, signal): e265 moonshotai/Kimi-K2.6 count=12832
- gonka1wt8sr9jxzpec65j7zkxsgh6edk3m6r8nlf5za4 epoch_commit_participant (medium, signal): e268 Qwen/Qwen3-235B-A22B-Instruct-2507-FP8 count=39328
- gonka1wt8sr9jxzpec65j7zkxsgh6edk3m6r8nlf5za4 epoch_commit_participant (medium, signal): e270 moonshotai/Kimi-K2.6 count=13536

## #13 http://57.131.17.61:8000

- Cluster: label:http://57.131.17.61:8000 (label; shared_public_label_only)
- Addresses: gonka1scskt6wpnjnumsah6kjphmdu87vjgvcxmn4rxv
- Roles: epoch_commit_participant, recipient, voter
- Compensation: 5645.801437 GONKA across 1 recipients
- Exact governance voting power: 0 across 1 voters
- Vote power split: yes=0.0
- Recipient-voter overlap: 1
- Interest score: 16.411
- Caveats: No strict public owner proof. | Cluster may be based on infrastructure/public signals, not ownership. | Voter addresses in this cluster had zero archive governance voting power. | At least one address both received compensation and voted.

Top evidence:
- gonka1scskt6wpnjnumsah6kjphmdu87vjgvcxmn4rxv compensation_output (high, signal): 5645.801437 GONKA
- gonka1scskt6wpnjnumsah6kjphmdu87vjgvcxmn4rxv matched_validator_moniker (high, signal): gonkavaloper1scskt6wpnjnumsah6kjphmdu87vjgvcx8nyy3p
- gonka1scskt6wpnjnumsah6kjphmdu87vjgvcxmn4rxv matched_validator_moniker (high, signal): gonkavaloper1scskt6wpnjnumsah6kjphmdu87vjgvcx8nyy3p
- gonka1scskt6wpnjnumsah6kjphmdu87vjgvcxmn4rxv proposal_vote (high, signal): yes
- gonka1scskt6wpnjnumsah6kjphmdu87vjgvcxmn4rxv epoch_commit_participant (medium, signal): e275 Qwen/Qwen3-235B-A22B-Instruct-2507-FP8 count=8320

## #14 http://65.108.198.21:8000

- Cluster: label:http://65.108.198.21:8000 (label; shared_public_label_only)
- Addresses: gonka1zktn8j65wlys8a8e38hqhf4y3x6m4x04zskkrx
- Roles: epoch_commit_participant, recipient, voter
- Compensation: 2392.222959 GONKA across 1 recipients
- Exact governance voting power: 4565 across 1 voters
- Vote power split: no_with_veto=4565.0
- Recipient-voter overlap: 1
- Interest score: 16.25
- Caveats: No strict public owner proof. | Cluster may be based on infrastructure/public signals, not ownership. | At least one address both received compensation and voted.

Top evidence:
- gonka1zktn8j65wlys8a8e38hqhf4y3x6m4x04zskkrx compensation_output (high, signal): 2392.222959 GONKA
- gonka1zktn8j65wlys8a8e38hqhf4y3x6m4x04zskkrx matched_validator_moniker (high, signal): gonkavaloper1zktn8j65wlys8a8e38hqhf4y3x6m4x047s835t
- gonka1zktn8j65wlys8a8e38hqhf4y3x6m4x04zskkrx matched_validator_moniker (high, signal): gonkavaloper1zktn8j65wlys8a8e38hqhf4y3x6m4x047s835t
- gonka1zktn8j65wlys8a8e38hqhf4y3x6m4x04zskkrx proposal_vote (high, signal): no_with_veto
- gonka1zktn8j65wlys8a8e38hqhf4y3x6m4x04zskkrx epoch_commit_participant (medium, signal): e265 Qwen/Qwen3-235B-A22B-Instruct-2507-FP8 count=41056

## #15 http://69.48.159.137:8000/

- Cluster: label:http://69.48.159.137:8000/ (label; shared_public_label_only)
- Addresses: gonka1gyk0aahvr3qeju4zx0nplfreej6cy4jjk8svc5
- Roles: delegator, epoch_commit_participant, recipient, voter
- Compensation: 30.990429 GONKA across 1 recipients
- Exact governance voting power: 278 across 1 voters
- Vote power split: no_with_veto=278.0
- Recipient-voter overlap: 1
- Interest score: 15.047
- Caveats: No strict public owner proof. | Cluster may be based on infrastructure/public signals, not ownership. | At least one address both received compensation and voted.

Top evidence:
- gonka1gyk0aahvr3qeju4zx0nplfreej6cy4jjk8svc5 compensation_output (high, signal): 30.990429 GONKA
- gonka1gyk0aahvr3qeju4zx0nplfreej6cy4jjk8svc5 matched_validator_moniker (high, signal): gonkavaloper1gyk0aahvr3qeju4zx0nplfreej6cy4jj28pt0e
- gonka1gyk0aahvr3qeju4zx0nplfreej6cy4jjk8svc5 matched_validator_moniker (high, signal): gonkavaloper1gyk0aahvr3qeju4zx0nplfreej6cy4jj28pt0e
- gonka1gyk0aahvr3qeju4zx0nplfreej6cy4jjk8svc5 proposal_vote (high, signal): no_with_veto
- gonka1gyk0aahvr3qeju4zx0nplfreej6cy4jjk8svc5 epoch_commit_participant (medium, signal): e267 Qwen/Qwen3-235B-A22B-Instruct-2507-FP8 count=1152

## #16 http://20.163.111.183:8000

- Cluster: label:http://20.163.111.183:8000 (label; shared_public_label_only)
- Addresses: gonka1fvly5jrewyjmjfgwah3khy9rttq4cqajcesv9p
- Roles: delegator, epoch_commit_participant, recipient, voter
- Compensation: 113.864834 GONKA across 1 recipients
- Exact governance voting power: 0 across 1 voters
- Vote power split: no_with_veto=0.0
- Recipient-voter overlap: 1
- Interest score: 15.028
- Caveats: No strict public owner proof. | Cluster may be based on infrastructure/public signals, not ownership. | Voter addresses in this cluster had zero archive governance voting power. | At least one address both received compensation and voted.

Top evidence:
- gonka1fvly5jrewyjmjfgwah3khy9rttq4cqajcesv9p compensation_output (high, signal): 113.864834 GONKA
- gonka1fvly5jrewyjmjfgwah3khy9rttq4cqajcesv9p matched_validator_moniker (high, signal): gonkavaloper1fvly5jrewyjmjfgwah3khy9rttq4cqajyeptjv
- gonka1fvly5jrewyjmjfgwah3khy9rttq4cqajcesv9p matched_validator_moniker (high, signal): gonkavaloper1fvly5jrewyjmjfgwah3khy9rttq4cqajyeptjv
- gonka1fvly5jrewyjmjfgwah3khy9rttq4cqajcesv9p proposal_vote (high, signal): no_with_veto
- gonka1fvly5jrewyjmjfgwah3khy9rttq4cqajcesv9p epoch_commit_participant (medium, signal): e265 Qwen/Qwen3-235B-A22B-Instruct-2507-FP8 count=4000

## #17 http://20.171.77.105:8000

- Cluster: label:http://20.171.77.105:8000 (label; shared_public_label_only)
- Addresses: gonka1cuwejs77gectp3n32wg8q27hlsa4m3hqspf4ww
- Roles: delegator, epoch_commit_participant, recipient, voter
- Compensation: 108.366532 GONKA across 1 recipients
- Exact governance voting power: 0 across 1 voters
- Vote power split: no_with_veto=0.0
- Recipient-voter overlap: 1
- Interest score: 15.027
- Caveats: No strict public owner proof. | Cluster may be based on infrastructure/public signals, not ownership. | Voter addresses in this cluster had zero archive governance voting power. | At least one address both received compensation and voted.

Top evidence:
- gonka1cuwejs77gectp3n32wg8q27hlsa4m3hqspf4ww compensation_output (high, signal): 108.366532 GONKA
- gonka1cuwejs77gectp3n32wg8q27hlsa4m3hqspf4ww matched_validator_moniker (high, signal): gonkavaloper1cuwejs77gectp3n32wg8q27hlsa4m3hqvpcjer
- gonka1cuwejs77gectp3n32wg8q27hlsa4m3hqspf4ww matched_validator_moniker (high, signal): gonkavaloper1cuwejs77gectp3n32wg8q27hlsa4m3hqvpcjer
- gonka1cuwejs77gectp3n32wg8q27hlsa4m3hqspf4ww proposal_vote (high, signal): no_with_veto
- gonka1cuwejs77gectp3n32wg8q27hlsa4m3hqspf4ww epoch_commit_participant (medium, signal): e265 Qwen/Qwen3-235B-A22B-Instruct-2507-FP8 count=3872

## #18 http://178.105.170.135:8000

- Cluster: signal-1 (signal_cluster; infrastructure_or_public_signal)
- Addresses: gonka10079cnl3nuh2k82mhkm04dj0slhtw9kmjewwau gonka16r08lhm50zwjddmslfw2344z67r70vqul0dus6 gonka1wvv656pt2d8x2khcvytqeessck5uzjnxzsa8f6
- Roles: epoch_commit_participant, recipient, voter
- Compensation: 26121.988467 GONKA across 2 recipients
- Exact governance voting power: 0 across 1 voters
- Vote power split: no_with_veto=0.0
- Recipient-voter overlap: 0
- Interest score: 10.53
- Caveats: No strict public owner proof. | Cluster may be based on infrastructure/public signals, not ownership. | Voter addresses in this cluster had zero archive governance voting power.

Top evidence:
- gonka10079cnl3nuh2k82mhkm04dj0slhtw9kmjewwau compensation_output (high, signal): 20610.390028 GONKA
- gonka1wvv656pt2d8x2khcvytqeessck5uzjnxzsa8f6 compensation_output (high, signal): 5511.598439 GONKA
- gonka10079cnl3nuh2k82mhkm04dj0slhtw9kmjewwau matched_validator_moniker (high, signal): gonkavaloper10079cnl3nuh2k82mhkm04dj0slhtw9kmwelf23
- gonka10079cnl3nuh2k82mhkm04dj0slhtw9kmjewwau matched_validator_moniker (high, signal): gonkavaloper10079cnl3nuh2k82mhkm04dj0slhtw9kmwelf23
- gonka1wvv656pt2d8x2khcvytqeessck5uzjnxzsa8f6 matched_validator_moniker (high, signal): gonkavaloper1wvv656pt2d8x2khcvytqeessck5uzjnx7svq7h

## #19 Unknown public owner

- Cluster: label:Unknown public owner (label; shared_public_label_only)
- Addresses: gonka1007py6y2qfn2vaqrthqhtchkwx64hgzc6w544w gonka10d07y265gmmuvt4z0w9aw880jnsr700j2h5m33 gonka14hyyn555u6dqdr4zqmllr429cnt8kdqx80jws5 gonka14tqh62mangwzrma2lgg2dm375rcjzn2ydy8ttm gonka16xa2sdc8qe2289nzr4e6vmdyzlke8g8fn8e75s gonka17gpuntq09zsaqtmpe544gc32tk4424dwv5t34f gonka187tn9y92ur6tu0zf69u94hwl0q77m47y0k36hv gonka18x5f3q6g0r3n7rgslwq66d2hd6tp5mgxwxnmc3 gonka19f9hkpmjaldncsfly4j63sy932y8hughn4l3d8 gonka19ghzvgfr065s3fr5awuvs3nhy9fq4n7wrr9kel gonka1amlmhjym02shahjv8ldmupg4cx0qc66q6f85rj gonka1d7p03cu2y2yt3vytq9wlfm6tlz0lfhlgv9h82p gonka1dkl4mah5erqggvhqkpc8j3qs5tyuetgdy552cp gonka1duuaqdx06sx8v2dzggltwwmqyuw8lvjkjq7xll gonka1famtxh54kad6ylwtm60j6d7h6unpc08d4vdqnk gonka1fc9tzt83dgrqswlgay4668cuqjrk7zsqks2vm2 gonka1mgdgcll2f4m0cjekqyueheeu7y8adz0hddfnh2 gonka1nku7u6d5mz80h35ty8ydeh0k5xydesvt9w0vjr gonka1nvcwl2c7jxj2h47c56y8dmcmf0tynt5dplzngy gonka1p2lhgng7tcqju7emk989s5fpdr7k2c3ek6h26m gonka1qnj39ysxpzknvrr5dw9rdl7cx5q7dpkwerryrs gonka1qu9mna5xlvlnw9455ygtjq92wuzkzm237w8l08 gonka1rcpc45n6zch9qlkn4m3cwngekad89xu8mcr09v gonka1u4zxypjgcr8khlzefwjr0vwdaj2uzruw2cehj3 gonka1uf5cg7ef0ns6877nl27y0s6rt06cdmn40k5a88 gonka1v5cl6pudnagau7exyu3a9h74clw9zm7l5psp0r gonka1w29nvdy6caqtrw30whz9h6ghl0xszwh3egndah gonka1x7zh2277spp7jfqjhv0g5mnezg290xdr4kpfnk gonka1zsvl7ujlc8z3a35v2q6e3nml7ftyk23v76jqgl
- Roles: epoch_commit_participant, message_sender, proposer, voter
- Compensation: 0 GONKA across 0 recipients
- Exact governance voting power: 0 across 1 voters
- Vote power split: yes=0.0
- Recipient-voter overlap: 0
- Interest score: 10.0
- Caveats: No strict public owner proof. | Cluster may be based on infrastructure/public signals, not ownership. | Voter addresses in this cluster had zero archive governance voting power.

Top evidence:
- gonka10d07y265gmmuvt4z0w9aw880jnsr700j2h5m33 proposal_message_sender (high, signal): /inference.streamvesting.MsgBatchTransferWithVesting
- gonka1nvcwl2c7jxj2h47c56y8dmcmf0tynt5dplzngy proposal_proposer (high, signal): 67
- gonka1mgdgcll2f4m0cjekqyueheeu7y8adz0hddfnh2 proposal_vote (high, signal): yes
- gonka10d07y265gmmuvt4z0w9aw880jnsr700j2h5m33 telegram_export_excerpt (medium, signal): из вот этого кармана gonka10d07y265gmmuvt4z0w9aw880jnsr700j2h5m33
- gonka17gpuntq09zsaqtmpe544gc32tk4424dwv5t34f telegram_export_excerpt (medium, signal): 17:51 In reply to this message И закорешиться с gonka17gpuntq09zsaqtmpe544gc32tk4424dwv5t34f )))

## #20 http://178.104.95.5:8000

- Cluster: label:http://178.104.95.5:8000 (label; shared_public_label_only)
- Addresses: gonka1j7x6dv42xehe9e5au4ku3wvzwtqlegfjhlvzj6
- Roles: epoch_commit_participant, recipient
- Compensation: 39809.676543 GONKA across 1 recipients
- Exact governance voting power: 0 across 0 voters
- Vote power split: none
- Recipient-voter overlap: 0
- Interest score: 9.952
- Caveats: No strict public owner proof. | Cluster may be based on infrastructure/public signals, not ownership.

Top evidence:
- gonka1j7x6dv42xehe9e5au4ku3wvzwtqlegfjhlvzj6 compensation_output (high, signal): 39809.676543 GONKA
- gonka1j7x6dv42xehe9e5au4ku3wvzwtqlegfjhlvzj6 matched_validator_moniker (high, signal): gonkavaloper1j7x6dv42xehe9e5au4ku3wvzwtqlegfjtla99h
- gonka1j7x6dv42xehe9e5au4ku3wvzwtqlegfjhlvzj6 matched_validator_moniker (high, signal): gonkavaloper1j7x6dv42xehe9e5au4ku3wvzwtqlegfjtla99h
- gonka1j7x6dv42xehe9e5au4ku3wvzwtqlegfjhlvzj6 epoch_commit_participant (medium, signal): e265 Qwen/Qwen3-235B-A22B-Instruct-2507-FP8 count=1024
- gonka1j7x6dv42xehe9e5au4ku3wvzwtqlegfjhlvzj6 epoch_commit_participant (medium, signal): e265 moonshotai/Kimi-K2.6 count=57984

## #21 http://95.217.121.189:8000

- Cluster: label:http://95.217.121.189:8000 (label; shared_public_label_only)
- Addresses: gonka1jrgm47v5eg876udmzg6j6glqcsd5x0vk6crpax
- Roles: epoch_commit_participant, recipient
- Compensation: 33750.579636 GONKA across 1 recipients
- Exact governance voting power: 0 across 0 voters
- Vote power split: none
- Recipient-voter overlap: 0
- Interest score: 8.438
- Caveats: No strict public owner proof. | Cluster may be based on infrastructure/public signals, not ownership.

Top evidence:
- gonka1jrgm47v5eg876udmzg6j6glqcsd5x0vk6crpax compensation_output (high, signal): 33750.579636 GONKA
- gonka1jrgm47v5eg876udmzg6j6glqcsd5x0vk6crpax matched_validator_moniker (high, signal): gonkavaloper1jrgm47v5eg876udmzg6j6glqcsd5x0vkxcjx2t
- gonka1jrgm47v5eg876udmzg6j6glqcsd5x0vk6crpax matched_validator_moniker (high, signal): gonkavaloper1jrgm47v5eg876udmzg6j6glqcsd5x0vkxcjx2t
- gonka1jrgm47v5eg876udmzg6j6glqcsd5x0vk6crpax epoch_commit_participant (medium, signal): e266 moonshotai/Kimi-K2.6 count=25664
- gonka1jrgm47v5eg876udmzg6j6glqcsd5x0vk6crpax epoch_commit_participant (medium, signal): e267 moonshotai/Kimi-K2.6 count=38336

## #22 http://136.243.110.227:8000

- Cluster: label:http://136.243.110.227:8000 (label; shared_public_label_only)
- Addresses: gonka15munkmx6x7k6rqqeexjet4556p7at39ks9qgr5
- Roles: epoch_commit_participant, recipient
- Compensation: 18234.887511 GONKA across 1 recipients
- Exact governance voting power: 0 across 0 voters
- Vote power split: none
- Recipient-voter overlap: 0
- Interest score: 4.559
- Caveats: No strict public owner proof. | Cluster may be based on infrastructure/public signals, not ownership.

Top evidence:
- gonka15munkmx6x7k6rqqeexjet4556p7at39ks9qgr5 compensation_output (high, signal): 18234.887511 GONKA
- gonka15munkmx6x7k6rqqeexjet4556p7at39ks9qgr5 epoch_commit_participant (medium, signal): e265 moonshotai/Kimi-K2.6 count=11168
- gonka15munkmx6x7k6rqqeexjet4556p7at39ks9qgr5 epoch_commit_participant (medium, signal): e266 moonshotai/Kimi-K2.6 count=12896
- gonka15munkmx6x7k6rqqeexjet4556p7at39ks9qgr5 epoch_commit_participant (medium, signal): e267 moonshotai/Kimi-K2.6 count=19040
- gonka15munkmx6x7k6rqqeexjet4556p7at39ks9qgr5 epoch_commit_participant (medium, signal): e268 moonshotai/Kimi-K2.6 count=13568

## #23 http://network002.kaitaku.ai:8000

- Cluster: label:http://network002.kaitaku.ai:8000 (label; shared_public_label_only)
- Addresses: gonka1d694r00czmq75txghwjcuk07lxvc8d4ekgsha0
- Roles: epoch_commit_participant, voter
- Compensation: 0 GONKA across 0 recipients
- Exact governance voting power: 31063 across 1 voters
- Vote power split: no_with_veto=31063.0
- Recipient-voter overlap: 0
- Interest score: 4.438
- Caveats: No strict public owner proof. | Cluster may be based on infrastructure/public signals, not ownership.

Top evidence:
- gonka1d694r00czmq75txghwjcuk07lxvc8d4ekgsha0 matched_validator_moniker (high, signal): gonkavaloper1d694r00czmq75txghwjcuk07lxvc8d4e2gps2z
- gonka1d694r00czmq75txghwjcuk07lxvc8d4ekgsha0 matched_validator_moniker (high, signal): gonkavaloper1d694r00czmq75txghwjcuk07lxvc8d4e2gps2z
- gonka1d694r00czmq75txghwjcuk07lxvc8d4ekgsha0 proposal_vote (high, signal): no_with_veto
- gonka1d694r00czmq75txghwjcuk07lxvc8d4ekgsha0 epoch_commit_participant (medium, signal): e266 Qwen/Qwen3-235B-A22B-Instruct-2507-FP8 count=1424
- gonka1d694r00czmq75txghwjcuk07lxvc8d4ekgsha0 epoch_commit_participant (medium, signal): e267 Qwen/Qwen3-235B-A22B-Instruct-2507-FP8 count=1424

## #24 http://94.130.152.246:8000

- Cluster: label:http://94.130.152.246:8000 (label; shared_public_label_only)
- Addresses: gonka1yal0ysgzc860zt3y8cds8656tnueusgymftvkw
- Roles: epoch_commit_participant, recipient
- Compensation: 17630.158097 GONKA across 1 recipients
- Exact governance voting power: 0 across 0 voters
- Vote power split: none
- Recipient-voter overlap: 0
- Interest score: 4.408
- Caveats: No strict public owner proof. | Cluster may be based on infrastructure/public signals, not ownership.

Top evidence:
- gonka1yal0ysgzc860zt3y8cds8656tnueusgymftvkw compensation_output (high, signal): 17630.158097 GONKA
- gonka1yal0ysgzc860zt3y8cds8656tnueusgymftvkw matched_validator_moniker (high, signal): gonkavaloper1yal0ysgzc860zt3y8cds8656tnueusgy8f6tpr
- gonka1yal0ysgzc860zt3y8cds8656tnueusgymftvkw matched_validator_moniker (high, signal): gonkavaloper1yal0ysgzc860zt3y8cds8656tnueusgy8f6tpr
- gonka1yal0ysgzc860zt3y8cds8656tnueusgymftvkw epoch_commit_participant (medium, signal): e266 moonshotai/Kimi-K2.6 count=5664
- gonka1yal0ysgzc860zt3y8cds8656tnueusgymftvkw epoch_commit_participant (medium, signal): e267 moonshotai/Kimi-K2.6 count=30176

## #25 http://195.201.192.170:8000

- Cluster: label:http://195.201.192.170:8000 (label; shared_public_label_only)
- Addresses: gonka1830lqug50lse998x2lakk4pj5ypfumz5pasz0y
- Roles: epoch_commit_participant, recipient
- Compensation: 13958.367773 GONKA across 1 recipients
- Exact governance voting power: 0 across 0 voters
- Vote power split: none
- Recipient-voter overlap: 0
- Interest score: 3.49
- Caveats: No strict public owner proof. | Cluster may be based on infrastructure/public signals, not ownership.

Top evidence:
- gonka1830lqug50lse998x2lakk4pj5ypfumz5pasz0y compensation_output (high, signal): 13958.367773 GONKA
- gonka1830lqug50lse998x2lakk4pj5ypfumz5pasz0y matched_validator_moniker (high, signal): gonkavaloper1830lqug50lse998x2lakk4pj5ypfumz5aap9cf
- gonka1830lqug50lse998x2lakk4pj5ypfumz5pasz0y matched_validator_moniker (high, signal): gonkavaloper1830lqug50lse998x2lakk4pj5ypfumz5aap9cf
- gonka1830lqug50lse998x2lakk4pj5ypfumz5pasz0y epoch_commit_participant (medium, signal): e265 moonshotai/Kimi-K2.6 count=12480
- gonka1830lqug50lse998x2lakk4pj5ypfumz5pasz0y epoch_commit_participant (medium, signal): e267 moonshotai/Kimi-K2.6 count=12640

## #26 http://35.89.168.230:8000

- Cluster: label:http://35.89.168.230:8000 (label; shared_public_label_only)
- Addresses: gonka1ujnc662v6g69jm6fgxnr79a2m7ehzeut059239
- Roles: epoch_commit_participant, recipient
- Compensation: 12612.234866 GONKA across 1 recipients
- Exact governance voting power: 0 across 0 voters
- Vote power split: none
- Recipient-voter overlap: 0
- Interest score: 3.153
- Caveats: No strict public owner proof. | Cluster may be based on infrastructure/public signals, not ownership.

Top evidence:
- gonka1ujnc662v6g69jm6fgxnr79a2m7ehzeut059239 compensation_output (high, signal): 12612.234866 GONKA
- gonka1ujnc662v6g69jm6fgxnr79a2m7ehzeut059239 matched_validator_moniker (high, signal): gonkavaloper1ujnc662v6g69jm6fgxnr79a2m7ehzeutn55dxg
- gonka1ujnc662v6g69jm6fgxnr79a2m7ehzeut059239 matched_validator_moniker (high, signal): gonkavaloper1ujnc662v6g69jm6fgxnr79a2m7ehzeutn55dxg
- gonka1ujnc662v6g69jm6fgxnr79a2m7ehzeut059239 epoch_commit_participant (medium, signal): e265 Qwen/Qwen3-235B-A22B-Instruct-2507-FP8 count=7296
- gonka1ujnc662v6g69jm6fgxnr79a2m7ehzeut059239 epoch_commit_participant (medium, signal): e265 moonshotai/Kimi-K2.6 count=6784

## #27 gonka-3

- Cluster: strict-1 (strict_identity; public_owner_proof)
- Addresses: gonka1kx9mca3xm8u8ypzfuhmxey66u0ufxhs7nm6wc5 gonka1y2a9p56kv044327uycmqdexl7zs82fs5ryv5le
- Roles: epoch_commit_participant, recipient
- Compensation: 4044.099545 GONKA across 2 recipients
- Exact governance voting power: 0 across 0 voters
- Vote power split: none
- Recipient-voter overlap: 0
- Interest score: 3.011
- Caveats: none

Top evidence:
- gonka1kx9mca3xm8u8ypzfuhmxey66u0ufxhs7nm6wc5 matched_validator_identity (high, proof): 673C81B66A67ED67
- gonka1kx9mca3xm8u8ypzfuhmxey66u0ufxhs7nm6wc5 matched_validator_identity (high, proof): 673C81B66A67ED67
- gonka1y2a9p56kv044327uycmqdexl7zs82fs5ryv5le matched_validator_identity (high, proof): 673C81B66A67ED67
- gonka1y2a9p56kv044327uycmqdexl7zs82fs5ryv5le matched_validator_identity (high, proof): 673C81B66A67ED67
- gonka1kx9mca3xm8u8ypzfuhmxey66u0ufxhs7nm6wc5 matched_validator_moniker (high, proof): gonka-3

## #28 http://94.237.52.191:8000

- Cluster: label:http://94.237.52.191:8000 (label; shared_public_label_only)
- Addresses: gonka1nmn039cgpkhmkzekpkfz3nkv9tcjckpn46jyrj
- Roles: voter
- Compensation: 0 GONKA across 0 recipients
- Exact governance voting power: 20647 across 1 voters
- Vote power split: yes=20647.0
- Recipient-voter overlap: 0
- Interest score: 2.95
- Caveats: No strict public owner proof. | Cluster may be based on infrastructure/public signals, not ownership.

Top evidence:
- gonka1nmn039cgpkhmkzekpkfz3nkv9tcjckpn46jyrj matched_validator_moniker (high, signal): gonkavaloper1nmn039cgpkhmkzekpkfz3nkv9tcjckpnf6rr5l
- gonka1nmn039cgpkhmkzekpkfz3nkv9tcjckpn46jyrj matched_validator_moniker (high, signal): gonkavaloper1nmn039cgpkhmkzekpkfz3nkv9tcjckpnf6rr5l
- gonka1nmn039cgpkhmkzekpkfz3nkv9tcjckpn46jyrj proposal_vote (high, signal): yes
- gonka1nmn039cgpkhmkzekpkfz3nkv9tcjckpn46jyrj participant_inference_url (medium, signal): http://94.237.52.191:8000
- gonka1nmn039cgpkhmkzekpkfz3nkv9tcjckpn46jyrj participant_inference_url (medium, signal): http://94.237.52.191:8000

## #29 http://178.105.172.102:8000

- Cluster: label:http://178.105.172.102:8000 (label; shared_public_label_only)
- Addresses: gonka1007g0ut3u4wjkay9hegqfev4pj90qgexwskmcw
- Roles: epoch_commit_participant, recipient
- Compensation: 11688.555563 GONKA across 1 recipients
- Exact governance voting power: 0 across 0 voters
- Vote power split: none
- Recipient-voter overlap: 0
- Interest score: 2.922
- Caveats: No strict public owner proof. | Cluster may be based on infrastructure/public signals, not ownership.

Top evidence:
- gonka1007g0ut3u4wjkay9hegqfev4pj90qgexwskmcw compensation_output (high, signal): 11688.555563 GONKA
- gonka1007g0ut3u4wjkay9hegqfev4pj90qgexwskmcw matched_validator_moniker (high, signal): gonkavaloper1007g0ut3u4wjkay9hegqfev4pj90qgexjs8u0r
- gonka1007g0ut3u4wjkay9hegqfev4pj90qgexwskmcw matched_validator_moniker (high, signal): gonkavaloper1007g0ut3u4wjkay9hegqfev4pj90qgexjs8u0r
- gonka1007g0ut3u4wjkay9hegqfev4pj90qgexwskmcw epoch_commit_participant (medium, signal): e268 moonshotai/Kimi-K2.6 count=14464
- gonka1007g0ut3u4wjkay9hegqfev4pj90qgexwskmcw epoch_commit_participant (medium, signal): e269 moonshotai/Kimi-K2.6 count=7008

## #30 http://204.12.168.89:8000

- Cluster: label:http://204.12.168.89:8000 (label; shared_public_label_only)
- Addresses: gonka1c6fwzedfsmpu4jnjekv4cn7mvr7x7fuqd6uqt9
- Roles: epoch_commit_participant, recipient
- Compensation: 11366.419254 GONKA across 1 recipients
- Exact governance voting power: 0 across 0 voters
- Vote power split: none
- Recipient-voter overlap: 0
- Interest score: 2.842
- Caveats: No strict public owner proof. | Cluster may be based on infrastructure/public signals, not ownership.

Top evidence:
- gonka1c6fwzedfsmpu4jnjekv4cn7mvr7x7fuqd6uqt9 compensation_output (high, signal): 11366.419254 GONKA
- gonka1c6fwzedfsmpu4jnjekv4cn7mvr7x7fuqd6uqt9 matched_validator_moniker (high, signal): gonkavaloper1c6fwzedfsmpu4jnjekv4cn7mvr7x7fuq36d8ug
- gonka1c6fwzedfsmpu4jnjekv4cn7mvr7x7fuqd6uqt9 matched_validator_moniker (high, signal): gonkavaloper1c6fwzedfsmpu4jnjekv4cn7mvr7x7fuq36d8ug
- gonka1c6fwzedfsmpu4jnjekv4cn7mvr7x7fuqd6uqt9 epoch_commit_participant (medium, signal): e266 moonshotai/Kimi-K2.6 count=12384
- gonka1c6fwzedfsmpu4jnjekv4cn7mvr7x7fuqd6uqt9 epoch_commit_participant (medium, signal): e267 moonshotai/Kimi-K2.6 count=11680
