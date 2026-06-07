# Proposal 67 Public Name Enrichment

This report normalizes public naming sources for proposal #67 addresses. It uses saved snapshots only: GNS `.gnk` contract state, validator metadata, participant inference URLs, and previously built evidence claims. A public name is an attribution lead unless `evidence_boundary` is `public_owner_proof`.

## Summary

- Proposal addresses reviewed: 63
- Proposal addresses with any public name/metadata signal: 62
- Proposal addresses with public owner proof: 6
- Proposal addresses with GNS names: 1 (1 reverse)
- Saved GNS snapshot: 5184 names across 200 addresses
- Public name/source groups in proposal set: 124; multi-address groups: 3

## Proposal Addresses With Public Names

### ancapex | Mine from $1, no losses from node failures

- Address: `gonka10mmdjau4dnj8krs7sh7t7635ttnmq9u3vqgz09`
- Roles: recipient, voter; compensation: 66487.744752 GONKA; voting power: 28865; vote: no_with_veto
- Best public name: ancapex | Mine from $1, no losses from node failures
- Evidence boundary: public_owner_proof
- GNS: none; reverse: none
- Validator: ancapex | Mine from $1, no losses from node failures | https://ancapex.ai | identity B22258DF68546529 | contact none
- Inference URL: http://89.149.242.149:8000
- Next actions: review recipient-voter conflict

Public sources:
- validator_moniker (high, proof): ancapex | Mine from $1, no losses from node failures
- validator_website (medium, signal): https://ancapex.ai
- validator_identity (high, proof): B22258DF68546529
- participant_inference_url (medium, signal): http://89.149.242.149:8000

### Arturs Plisko · Hyperfusion

- Address: `gonka1ym3np7guxart483yfdxnlztuazx22cjt0e4a2p`
- Roles: voter; compensation: 0 GONKA; voting power: 5395; vote: no_with_veto
- Best public name: Hyperfusion
- Evidence boundary: public_owner_proof
- GNS: none; reverse: none
- Validator: Hyperfusion | https://hyperfusion.io/gonka | identity 7B07CCF42FA50009 | contact none
- Inference URL: http://46.4.101.189:8000
- Next actions: archive as public proof

Public sources:
- validator_moniker (high, proof): Hyperfusion
- validator_website (medium, signal): https://hyperfusion.io/gonka
- validator_identity (high, proof): 7B07CCF42FA50009
- participant_inference_url (medium, signal): http://46.4.101.189:8000

### gonka-3

- Address: `gonka1kx9mca3xm8u8ypzfuhmxey66u0ufxhs7nm6wc5`
- Roles: recipient; compensation: 3018.840187 GONKA; voting power: 0; vote: did_not_vote
- Best public name: gonka-3
- Evidence boundary: public_owner_proof
- GNS: none; reverse: none
- Validator: gonka-3 | https://gonka.ai | identity 673C81B66A67ED67 | contact none
- Inference URL: https://node3.gonka.ai
- Next actions: archive as public proof

Public sources:
- validator_moniker (high, proof): gonka-3
- validator_website (medium, signal): https://gonka.ai
- validator_identity (high, proof): 673C81B66A67ED67
- participant_inference_url (medium, signal): https://node3.gonka.ai

### Formula x AI

- Address: `gonka12pcu9mcrpa4w4sjd9y3dsksnvu495ss6f9r4ra`
- Roles: recipient; compensation: 1166.439756 GONKA; voting power: 0; vote: did_not_vote
- Best public name: Formula x AI
- Evidence boundary: public_owner_proof
- GNS: none; reverse: none
- Validator: Formula x AI | https://formulaxpool.com | identity none | contact none
- Inference URL: http://162.55.232.115:8000
- Next actions: archive as public proof

Public sources:
- validator_moniker (high, proof): Formula x AI
- validator_website (medium, signal): https://formulaxpool.com
- participant_inference_url (medium, signal): http://162.55.232.115:8000

### gonka-1

- Address: `gonka1y2a9p56kv044327uycmqdexl7zs82fs5ryv5le`
- Roles: recipient; compensation: 1025.259358 GONKA; voting power: 0; vote: did_not_vote
- Best public name: gonka-1
- Evidence boundary: public_owner_proof
- GNS: none; reverse: none
- Validator: gonka-1 | https://gonka.ai | identity 673C81B66A67ED67 | contact none
- Inference URL: http://node1.gonka.ai:8000
- Next actions: archive as public proof

Public sources:
- validator_moniker (high, proof): gonka-1
- validator_website (medium, signal): https://gonka.ai
- validator_identity (high, proof): 673C81B66A67ED67
- participant_inference_url (medium, signal): http://node1.gonka.ai:8000

### asd.gnk

- Address: `gonka1q9f3wphjnf633fevej30y4aw3nnw87hl0r7qe4`
- Roles: voter; compensation: 0 GONKA; voting power: 0; vote: no_with_veto
- Best public name: asd.gnk
- Evidence boundary: public_owner_proof
- GNS: asd.gnk, its.gnk, may.gnk, qwe.gnk, she.gnk, sosnov.gnk, was.gnk, wat.gnk; reverse: sosnov.gnk
- Validator: none | no website | identity none | contact none
- Inference URL: none
- Next actions: archive as public proof

Public sources:
- gns_name (high, proof): asd.gnk
- gns_name (high, proof): its.gnk
- gns_name (high, proof): may.gnk
- gns_name (high, proof): qwe.gnk
- gns_name (high, proof): she.gnk
- gns_name (high, proof): was.gnk
- gns_name (high, proof): wat.gnk
- gns_name (high, proof): sosnov.gnk

### Votkon · http://89.169.97.113:8000

- Address: `gonka1q5xt54wncgzk7dxv9x64uln68455g83wu9tugg`
- Roles: recipient, voter; compensation: 73073.708453 GONKA; voting power: 92840; vote: yes
- Best public name: gonkavaloper1q5xt54wncgzk7dxv9x64uln68455g83wq96ml9
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: gonkavaloper1q5xt54wncgzk7dxv9x64uln68455g83wq96ml9 | no website | identity none | contact none
- Inference URL: http://89.169.97.113:8000
- Next actions: review recipient-voter conflict | corroborate voter owner | corroborate beneficiary owner

Public sources:
- validator_moniker (high, signal): gonkavaloper1q5xt54wncgzk7dxv9x64uln68455g83wq96ml9
- participant_inference_url (medium, signal): http://89.169.97.113:8000

### http://54.38.118.143:8000

- Address: `gonka1gvrrhjmy4w4mayvs2s5l23edj8ertcmtd2v4zr`
- Roles: recipient, voter; compensation: 52290.195676 GONKA; voting power: 86433; vote: yes
- Best public name: gonkavaloper1gvrrhjmy4w4mayvs2s5l23edj8ertcmt32aj4w
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: gonkavaloper1gvrrhjmy4w4mayvs2s5l23edj8ertcmt32aj4w | no website | identity none | contact none
- Inference URL: http://54.38.118.143:8000
- Next actions: review recipient-voter conflict | corroborate voter owner | corroborate beneficiary owner

Public sources:
- validator_moniker (high, signal): gonkavaloper1gvrrhjmy4w4mayvs2s5l23edj8ertcmt32aj4w
- participant_inference_url (medium, signal): http://54.38.118.143:8000

### http://178.105.174.27:8000

- Address: `gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv`
- Roles: recipient, voter; compensation: 11262.520198 GONKA; voting power: 57838; vote: yes
- Best public name: http://178.105.174.27:8000
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: none | no website | identity none | contact none
- Inference URL: http://178.105.174.27:8000
- Next actions: review recipient-voter conflict | corroborate voter owner | corroborate beneficiary owner

Public sources:
- participant_inference_url (medium, signal): http://178.105.174.27:8000

### http://148.113.47.235:8000

- Address: `gonka1tja3g2da45efhe2p83gk3whtussmgmtsdlgprt`
- Roles: recipient, voter; compensation: 1805.142498 GONKA; voting power: 31217; vote: yes
- Best public name: gonkavaloper1tja3g2da45efhe2p83gk3whtussmgmts3lex5x
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: gonkavaloper1tja3g2da45efhe2p83gk3whtussmgmts3lex5x | no website | identity none | contact none
- Inference URL: http://148.113.47.235:8000
- Next actions: review recipient-voter conflict | corroborate voter owner | corroborate beneficiary owner

Public sources:
- validator_moniker (high, signal): gonkavaloper1tja3g2da45efhe2p83gk3whtussmgmts3lex5x
- participant_inference_url (medium, signal): http://148.113.47.235:8000

### http://network002.kaitaku.ai:8000

- Address: `gonka1d694r00czmq75txghwjcuk07lxvc8d4ekgsha0`
- Roles: voter; compensation: 0 GONKA; voting power: 31063; vote: no_with_veto
- Best public name: gonkavaloper1d694r00czmq75txghwjcuk07lxvc8d4e2gps2z
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: gonkavaloper1d694r00czmq75txghwjcuk07lxvc8d4e2gps2z | no website | identity none | contact none
- Inference URL: http://network002.kaitaku.ai:8000
- Next actions: corroborate voter owner

Public sources:
- validator_moniker (high, signal): gonkavaloper1d694r00czmq75txghwjcuk07lxvc8d4e2gps2z
- participant_inference_url (medium, signal): http://network002.kaitaku.ai:8000

### http://network000.kaitaku.ai:8000

- Address: `gonka168rtjfkszuhcggg4dfyse4yh7xn9zwfglnkns2`
- Roles: recipient, voter; compensation: 11021.18308 GONKA; voting power: 25278; vote: no_with_veto
- Best public name: gonkavaloper168rtjfkszuhcggg4dfyse4yh7xn9zwfgrn8588
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: gonkavaloper168rtjfkszuhcggg4dfyse4yh7xn9zwfgrn8588 | no website | identity none | contact none
- Inference URL: http://network000.kaitaku.ai:8000
- Next actions: review recipient-voter conflict | corroborate voter owner | corroborate beneficiary owner

Public sources:
- validator_moniker (high, signal): gonkavaloper168rtjfkszuhcggg4dfyse4yh7xn9zwfgrn8588
- participant_inference_url (medium, signal): http://network000.kaitaku.ai:8000

### http://94.237.52.191:8000

- Address: `gonka1nmn039cgpkhmkzekpkfz3nkv9tcjckpn46jyrj`
- Roles: voter; compensation: 0 GONKA; voting power: 20647; vote: yes
- Best public name: gonkavaloper1nmn039cgpkhmkzekpkfz3nkv9tcjckpnf6rr5l
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: gonkavaloper1nmn039cgpkhmkzekpkfz3nkv9tcjckpnf6rr5l | no website | identity none | contact none
- Inference URL: http://94.237.52.191:8000
- Next actions: corroborate voter owner

Public sources:
- validator_moniker (high, signal): gonkavaloper1nmn039cgpkhmkzekpkfz3nkv9tcjckpnf6rr5l
- participant_inference_url (medium, signal): http://94.237.52.191:8000

### http://148.113.47.71:8000

- Address: `gonka1hwvel7n3zuk6wruefuzc356l9myske9stckwnz`
- Roles: recipient, voter; compensation: 1575.513417 GONKA; voting power: 19974; vote: yes
- Best public name: gonkavaloper1hwvel7n3zuk6wruefuzc356l9myske9shc8fy0
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: gonkavaloper1hwvel7n3zuk6wruefuzc356l9myske9shc8fy0 | no website | identity none | contact none
- Inference URL: http://148.113.47.71:8000
- Next actions: review recipient-voter conflict | corroborate voter owner | corroborate beneficiary owner

Public sources:
- validator_moniker (high, signal): gonkavaloper1hwvel7n3zuk6wruefuzc356l9myske9shc8fy0
- participant_inference_url (medium, signal): http://148.113.47.71:8000

### http://65.108.198.21:8000

- Address: `gonka1zktn8j65wlys8a8e38hqhf4y3x6m4x04zskkrx`
- Roles: recipient, voter; compensation: 2392.222959 GONKA; voting power: 4565; vote: no_with_veto
- Best public name: gonkavaloper1zktn8j65wlys8a8e38hqhf4y3x6m4x047s835t
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: gonkavaloper1zktn8j65wlys8a8e38hqhf4y3x6m4x047s835t | no website | identity none | contact none
- Inference URL: http://65.108.198.21:8000
- Next actions: review recipient-voter conflict | corroborate voter owner | corroborate beneficiary owner

Public sources:
- validator_moniker (high, signal): gonkavaloper1zktn8j65wlys8a8e38hqhf4y3x6m4x047s835t
- participant_inference_url (medium, signal): http://65.108.198.21:8000

### http://84.32.59.212:8000

- Address: `gonka1qwfrtz9c7kcrfkrrlne2pkcye74mj6ce33xdkl`
- Roles: voter; compensation: 0 GONKA; voting power: 556; vote: no_with_veto
- Best public name: gonkavaloper1qwfrtz9c7kcrfkrrlne2pkcye74mj6ced3h2pj
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: gonkavaloper1qwfrtz9c7kcrfkrrlne2pkcye74mj6ced3h2pj | no website | identity none | contact none
- Inference URL: http://84.32.59.212:8000
- Next actions: corroborate voter owner

Public sources:
- validator_moniker (high, signal): gonkavaloper1qwfrtz9c7kcrfkrrlne2pkcye74mj6ced3h2pj
- participant_inference_url (medium, signal): http://84.32.59.212:8000

### http://84.32.185.226:8000

- Address: `gonka1m58jds005cttwq2vt0p7yk6vy2aqg254cqqppf`
- Roles: voter; compensation: 0 GONKA; voting power: 490; vote: no_with_veto
- Best public name: gonkavaloper1m58jds005cttwq2vt0p7yk6vy2aqg254yq3xky
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: gonkavaloper1m58jds005cttwq2vt0p7yk6vy2aqg254yq3xky | no website | identity none | contact none
- Inference URL: http://84.32.185.226:8000
- Next actions: corroborate voter owner

Public sources:
- validator_moniker (high, signal): gonkavaloper1m58jds005cttwq2vt0p7yk6vy2aqg254yq3xky
- participant_inference_url (medium, signal): http://84.32.185.226:8000

### http://69.48.159.137:8000/

- Address: `gonka1gyk0aahvr3qeju4zx0nplfreej6cy4jjk8svc5`
- Roles: recipient, voter; compensation: 30.990429 GONKA; voting power: 278; vote: no_with_veto
- Best public name: gonkavaloper1gyk0aahvr3qeju4zx0nplfreej6cy4jj28pt0e
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: gonkavaloper1gyk0aahvr3qeju4zx0nplfreej6cy4jj28pt0e | no website | identity none | contact none
- Inference URL: http://69.48.159.137:8000/
- Next actions: review recipient-voter conflict | corroborate voter owner | corroborate beneficiary owner

Public sources:
- validator_moniker (high, signal): gonkavaloper1gyk0aahvr3qeju4zx0nplfreej6cy4jj28pt0e
- participant_inference_url (medium, signal): http://69.48.159.137:8000/

### http://135.181.56.61:8000

- Address: `gonka1qa90tgczc0k5dvk4l5nvlf5y6phgm6mg22sfjv`
- Roles: recipient; compensation: 158541.879456 GONKA; voting power: 0; vote: did_not_vote
- Best public name: gonkavaloper1qa90tgczc0k5dvk4l5nvlf5y6phgm6mgk2pw9p
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: gonkavaloper1qa90tgczc0k5dvk4l5nvlf5y6phgm6mgk2pw9p | no website | identity none | contact none
- Inference URL: http://135.181.56.61:8000
- Next actions: corroborate beneficiary owner

Public sources:
- validator_moniker (high, signal): gonkavaloper1qa90tgczc0k5dvk4l5nvlf5y6phgm6mgk2pw9p
- participant_inference_url (medium, signal): http://135.181.56.61:8000

### http://54.37.131.156:8000

- Address: `gonka17pw6099q758qwzewtrqmqpf5c2lrhr97fwqexu`
- Roles: recipient; compensation: 101147.807219 GONKA; voting power: 0; vote: did_not_vote
- Best public name: http://54.37.131.156:8000
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: none | no website | identity none | contact none
- Inference URL: http://54.37.131.156:8000
- Next actions: corroborate beneficiary owner

Public sources:
- participant_inference_url (medium, signal): http://54.37.131.156:8000

### http://65.21.232.177:8000

- Address: `gonka1uhqpup9fev3zahlx6n326lp0krznc6usjtx6lu`
- Roles: recipient; compensation: 96601.320933 GONKA; voting power: 0; vote: did_not_vote
- Best public name: gonkavaloper1uhqpup9fev3zahlx6n326lp0krznc6uswthag3
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: gonkavaloper1uhqpup9fev3zahlx6n326lp0krznc6uswthag3 | no website | identity none | contact none
- Inference URL: http://65.21.232.177:8000
- Next actions: corroborate beneficiary owner

Public sources:
- validator_moniker (high, signal): gonkavaloper1uhqpup9fev3zahlx6n326lp0krznc6uswthag3
- participant_inference_url (medium, signal): http://65.21.232.177:8000

### http://57.128.30.101:8000

- Address: `gonka1wthc28t25pg63hzvl07rl8e8r6km6hesl6jhsz`
- Roles: recipient; compensation: 79247.555227 GONKA; voting power: 0; vote: did_not_vote
- Best public name: http://57.128.30.101:8000
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: none | no website | identity none | contact none
- Inference URL: http://57.128.30.101:8000
- Next actions: corroborate beneficiary owner

Public sources:
- participant_inference_url (medium, signal): http://57.128.30.101:8000

### http://178.104.95.5:8000

- Address: `gonka1j7x6dv42xehe9e5au4ku3wvzwtqlegfjhlvzj6`
- Roles: recipient; compensation: 39809.676543 GONKA; voting power: 0; vote: did_not_vote
- Best public name: gonkavaloper1j7x6dv42xehe9e5au4ku3wvzwtqlegfjtla99h
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: gonkavaloper1j7x6dv42xehe9e5au4ku3wvzwtqlegfjtla99h | no website | identity none | contact none
- Inference URL: http://178.104.95.5:8000
- Next actions: corroborate beneficiary owner

Public sources:
- validator_moniker (high, signal): gonkavaloper1j7x6dv42xehe9e5au4ku3wvzwtqlegfjtla99h
- participant_inference_url (medium, signal): http://178.104.95.5:8000

### http://95.217.121.189:8000

- Address: `gonka1jrgm47v5eg876udmzg6j6glqcsd5x0vk6crpax`
- Roles: recipient; compensation: 33750.579636 GONKA; voting power: 0; vote: did_not_vote
- Best public name: gonkavaloper1jrgm47v5eg876udmzg6j6glqcsd5x0vkxcjx2t
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: gonkavaloper1jrgm47v5eg876udmzg6j6glqcsd5x0vkxcjx2t | no website | identity none | contact none
- Inference URL: http://95.217.121.189:8000
- Next actions: corroborate beneficiary owner

Public sources:
- validator_moniker (high, signal): gonkavaloper1jrgm47v5eg876udmzg6j6glqcsd5x0vkxcjx2t
- participant_inference_url (medium, signal): http://95.217.121.189:8000

### http://178.105.170.135:8000

- Address: `gonka10079cnl3nuh2k82mhkm04dj0slhtw9kmjewwau`
- Roles: recipient; compensation: 20610.390028 GONKA; voting power: 0; vote: did_not_vote
- Best public name: gonkavaloper10079cnl3nuh2k82mhkm04dj0slhtw9kmwelf23
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: gonkavaloper10079cnl3nuh2k82mhkm04dj0slhtw9kmwelf23 | no website | identity none | contact none
- Inference URL: http://178.105.170.135:8000
- Next actions: corroborate beneficiary owner

Public sources:
- validator_moniker (high, signal): gonkavaloper10079cnl3nuh2k82mhkm04dj0slhtw9kmwelf23
- participant_inference_url (medium, signal): http://178.105.170.135:8000

### A? · http://136.243.110.227:8000

- Address: `gonka15munkmx6x7k6rqqeexjet4556p7at39ks9qgr5`
- Roles: recipient; compensation: 18234.887511 GONKA; voting power: 0; vote: did_not_vote
- Best public name: http://136.243.110.227:8000
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: none | no website | identity none | contact none
- Inference URL: http://136.243.110.227:8000
- Next actions: corroborate beneficiary owner

Public sources:
- participant_inference_url (medium, signal): http://136.243.110.227:8000

### http://94.130.152.246:8000

- Address: `gonka1yal0ysgzc860zt3y8cds8656tnueusgymftvkw`
- Roles: recipient; compensation: 17630.158097 GONKA; voting power: 0; vote: did_not_vote
- Best public name: gonkavaloper1yal0ysgzc860zt3y8cds8656tnueusgy8f6tpr
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: gonkavaloper1yal0ysgzc860zt3y8cds8656tnueusgy8f6tpr | no website | identity none | contact none
- Inference URL: http://94.130.152.246:8000
- Next actions: corroborate beneficiary owner

Public sources:
- validator_moniker (high, signal): gonkavaloper1yal0ysgzc860zt3y8cds8656tnueusgy8f6tpr
- participant_inference_url (medium, signal): http://94.130.152.246:8000

### http://195.201.192.170:8000

- Address: `gonka1830lqug50lse998x2lakk4pj5ypfumz5pasz0y`
- Roles: recipient; compensation: 13958.367773 GONKA; voting power: 0; vote: did_not_vote
- Best public name: gonkavaloper1830lqug50lse998x2lakk4pj5ypfumz5aap9cf
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: gonkavaloper1830lqug50lse998x2lakk4pj5ypfumz5aap9cf | no website | identity none | contact none
- Inference URL: http://195.201.192.170:8000
- Next actions: corroborate beneficiary owner

Public sources:
- validator_moniker (high, signal): gonkavaloper1830lqug50lse998x2lakk4pj5ypfumz5aap9cf
- participant_inference_url (medium, signal): http://195.201.192.170:8000

### http://35.89.168.230:8000

- Address: `gonka1ujnc662v6g69jm6fgxnr79a2m7ehzeut059239`
- Roles: recipient; compensation: 12612.234866 GONKA; voting power: 0; vote: did_not_vote
- Best public name: gonkavaloper1ujnc662v6g69jm6fgxnr79a2m7ehzeutn55dxg
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: gonkavaloper1ujnc662v6g69jm6fgxnr79a2m7ehzeutn55dxg | no website | identity none | contact none
- Inference URL: http://35.89.168.230:8000
- Next actions: corroborate beneficiary owner

Public sources:
- validator_moniker (high, signal): gonkavaloper1ujnc662v6g69jm6fgxnr79a2m7ehzeutn55dxg
- participant_inference_url (medium, signal): http://35.89.168.230:8000

### http://178.105.172.102:8000

- Address: `gonka1007g0ut3u4wjkay9hegqfev4pj90qgexwskmcw`
- Roles: recipient; compensation: 11688.555563 GONKA; voting power: 0; vote: did_not_vote
- Best public name: gonkavaloper1007g0ut3u4wjkay9hegqfev4pj90qgexjs8u0r
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: gonkavaloper1007g0ut3u4wjkay9hegqfev4pj90qgexjs8u0r | no website | identity none | contact none
- Inference URL: http://178.105.172.102:8000
- Next actions: corroborate beneficiary owner

Public sources:
- validator_moniker (high, signal): gonkavaloper1007g0ut3u4wjkay9hegqfev4pj90qgexjs8u0r
- participant_inference_url (medium, signal): http://178.105.172.102:8000

### http://204.12.168.89:8000

- Address: `gonka1c6fwzedfsmpu4jnjekv4cn7mvr7x7fuqd6uqt9`
- Roles: recipient; compensation: 11366.419254 GONKA; voting power: 0; vote: did_not_vote
- Best public name: gonkavaloper1c6fwzedfsmpu4jnjekv4cn7mvr7x7fuq36d8ug
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: gonkavaloper1c6fwzedfsmpu4jnjekv4cn7mvr7x7fuq36d8ug | no website | identity none | contact none
- Inference URL: http://204.12.168.89:8000
- Next actions: corroborate beneficiary owner

Public sources:
- validator_moniker (high, signal): gonkavaloper1c6fwzedfsmpu4jnjekv4cn7mvr7x7fuq36d8ug
- participant_inference_url (medium, signal): http://204.12.168.89:8000

### http://88.99.213.222:8000

- Address: `gonka1wt8sr9jxzpec65j7zkxsgh6edk3m6r8nlf5za4`
- Roles: recipient, voter; compensation: 10934.181496 GONKA; voting power: 0; vote: no_with_veto
- Best public name: http://88.99.213.222:8000
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: none | no website | identity none | contact none
- Inference URL: http://88.99.213.222:8000
- Next actions: review recipient-voter conflict | corroborate voter owner | corroborate beneficiary owner

Public sources:
- participant_inference_url (medium, signal): http://88.99.213.222:8000

### http://95.217.35.48:8000

- Address: `gonka1wkgawwdzj623ss8eywayzdj6qcgr2llygactje`
- Roles: recipient; compensation: 10456.612261 GONKA; voting power: 0; vote: did_not_vote
- Best public name: http://95.217.35.48:8000
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: none | no website | identity none | contact none
- Inference URL: http://95.217.35.48:8000
- Next actions: corroborate beneficiary owner

Public sources:
- participant_inference_url (medium, signal): http://95.217.35.48:8000

### http://94.130.143.155:8000

- Address: `gonka1xwkesaxvdadh9wt9yyladu0r260s7whklcktds`
- Roles: recipient; compensation: 9768.694504 GONKA; voting power: 0; vote: did_not_vote
- Best public name: gonkavaloper1xwkesaxvdadh9wt9yyladu0r260s7whkrc8v6a
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: gonkavaloper1xwkesaxvdadh9wt9yyladu0r260s7whkrc8v6a | no website | identity none | contact none
- Inference URL: http://94.130.143.155:8000
- Next actions: corroborate beneficiary owner

Public sources:
- validator_moniker (high, signal): gonkavaloper1xwkesaxvdadh9wt9yyladu0r260s7whkrc8v6a
- participant_inference_url (medium, signal): http://94.130.143.155:8000

### http://88.198.4.29:8000

- Address: `gonka125n6kr5gvdup0lndfkps7t6rd6592panhrg3np`
- Roles: recipient; compensation: 9423.072516 GONKA; voting power: 0; vote: did_not_vote
- Best public name: gonkavaloper125n6kr5gvdup0lndfkps7t6rd6592pantrekyv
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: gonkavaloper125n6kr5gvdup0lndfkps7t6rd6592pantrekyv | no website | identity none | contact none
- Inference URL: http://88.198.4.29:8000
- Next actions: corroborate beneficiary owner

Public sources:
- validator_moniker (high, signal): gonkavaloper125n6kr5gvdup0lndfkps7t6rd6592pantrekyv
- participant_inference_url (medium, signal): http://88.198.4.29:8000

### http://136.243.111.105:8000

- Address: `gonka19cjm4c5mt3j3qdr8vhytmm4hef3pnkvkm0x7m2`
- Roles: recipient; compensation: 8441.669468 GONKA; voting power: 0; vote: did_not_vote
- Best public name: http://136.243.111.105:8000
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: none | no website | identity none | contact none
- Inference URL: http://136.243.111.105:8000
- Next actions: corroborate beneficiary owner

Public sources:
- participant_inference_url (medium, signal): http://136.243.111.105:8000

### http://195.201.83.167:8000

- Address: `gonka18xeqnspxpg2vncufnjne485rkaagwvz7whyn0d`
- Roles: recipient; compensation: 6820.652574 GONKA; voting power: 0; vote: did_not_vote
- Best public name: gonkavaloper18xeqnspxpg2vncufnjne485rkaagwvz7jh45cq
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: gonkavaloper18xeqnspxpg2vncufnjne485rkaagwvz7jh45cq | no website | identity none | contact none
- Inference URL: http://195.201.83.167:8000
- Next actions: corroborate beneficiary owner

Public sources:
- validator_moniker (high, signal): gonkavaloper18xeqnspxpg2vncufnjne485rkaagwvz7jh45cq
- participant_inference_url (medium, signal): http://195.201.83.167:8000

### http://138.201.121.253:8000

- Address: `gonka1mmlyd5xxu5l68yx8wzclrkxkxvm88mhq5tp5s0`
- Roles: recipient; compensation: 6618.057561 GONKA; voting power: 0; vote: did_not_vote
- Best public name: http://138.201.121.253:8000
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: none | no website | identity none | contact none
- Inference URL: http://138.201.121.253:8000
- Next actions: corroborate beneficiary owner

Public sources:
- participant_inference_url (medium, signal): http://138.201.121.253:8000

### http://57.131.17.61:8000

- Address: `gonka1scskt6wpnjnumsah6kjphmdu87vjgvcxmn4rxv`
- Roles: recipient, voter; compensation: 5645.801437 GONKA; voting power: 0; vote: yes
- Best public name: gonkavaloper1scskt6wpnjnumsah6kjphmdu87vjgvcx8nyy3p
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: gonkavaloper1scskt6wpnjnumsah6kjphmdu87vjgvcx8nyy3p | no website | identity none | contact none
- Inference URL: http://57.131.17.61:8000
- Next actions: review recipient-voter conflict | corroborate voter owner | corroborate beneficiary owner

Public sources:
- validator_moniker (high, signal): gonkavaloper1scskt6wpnjnumsah6kjphmdu87vjgvcx8nyy3p
- participant_inference_url (medium, signal): http://57.131.17.61:8000

### https://gonka.top

- Address: `gonka1wvv656pt2d8x2khcvytqeessck5uzjnxzsa8f6`
- Roles: recipient; compensation: 5511.598439 GONKA; voting power: 0; vote: did_not_vote
- Best public name: gonkavaloper1wvv656pt2d8x2khcvytqeessck5uzjnx7svq7h
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: gonkavaloper1wvv656pt2d8x2khcvytqeessck5uzjnx7svq7h | https://gonka.top | identity none | contact none
- Inference URL: http://109.206.182.166:8000
- Next actions: corroborate beneficiary owner

Public sources:
- validator_moniker (high, signal): gonkavaloper1wvv656pt2d8x2khcvytqeessck5uzjnx7svq7h
- validator_website (medium, signal): https://gonka.top
- participant_inference_url (medium, signal): http://109.206.182.166:8000

### http://95.217.122.154:8000

- Address: `gonka1f0u3y2wneer8zhz3ypw4x54h38cpa0qsy8ts3e`
- Roles: recipient; compensation: 4673.802242 GONKA; voting power: 0; vote: did_not_vote
- Best public name: http://95.217.122.154:8000
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: none | no website | identity none | contact none
- Inference URL: http://95.217.122.154:8000
- Next actions: corroborate beneficiary owner

Public sources:
- participant_inference_url (medium, signal): http://95.217.122.154:8000

### http://109.206.182.132:8000

- Address: `gonka14ljarev2nlzu4ej50vx7ylj2rvg4n20fnq2ysc`
- Roles: recipient; compensation: 4444.392151 GONKA; voting power: 0; vote: did_not_vote
- Best public name: gonkavaloper14ljarev2nlzu4ej50vx7ylj2rvg4n20f0qmr84
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: gonkavaloper14ljarev2nlzu4ej50vx7ylj2rvg4n20f0qmr84 | no website | identity none | contact none
- Inference URL: http://109.206.182.132:8000
- Next actions: corroborate beneficiary owner

Public sources:
- validator_moniker (high, signal): gonkavaloper14ljarev2nlzu4ej50vx7ylj2rvg4n20f0qmr84
- participant_inference_url (medium, signal): http://109.206.182.132:8000

### http://159.69.112.72:8000

- Address: `gonka1l8jd2nz92mnem0xwgwkltcw2952cnlphs5arsa`
- Roles: recipient; compensation: 4167.200641 GONKA; voting power: 0; vote: did_not_vote
- Best public name: http://159.69.112.72:8000
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: none | no website | identity none | contact none
- Inference URL: http://159.69.112.72:8000
- Next actions: corroborate beneficiary owner

Public sources:
- participant_inference_url (medium, signal): http://159.69.112.72:8000

### http://178.105.166.7:8000

- Address: `gonka1007n977a7uda3pd9m6hftw8xcql0tc20m96myu`
- Roles: recipient; compensation: 3396.492512 GONKA; voting power: 0; vote: did_not_vote
- Best public name: gonkavaloper1007n977a7uda3pd9m6hftw8xcql0tc2089tun3
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: gonkavaloper1007n977a7uda3pd9m6hftw8xcql0tc2089tun3 | no website | identity none | contact none
- Inference URL: http://178.105.166.7:8000
- Next actions: corroborate beneficiary owner

Public sources:
- validator_moniker (high, signal): gonkavaloper1007n977a7uda3pd9m6hftw8xcql0tc2089tun3
- participant_inference_url (medium, signal): http://178.105.166.7:8000

### http://95.217.47.126:8000

- Address: `gonka1tl5m3vuqsx333v7095ymwjdc4vdk2wd9r5hqws`
- Roles: recipient; compensation: 2731.396085 GONKA; voting power: 0; vote: did_not_vote
- Best public name: gonkavaloper1tl5m3vuqsx333v7095ymwjdc4vdk2wd9l5x8ea
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: gonkavaloper1tl5m3vuqsx333v7095ymwjdc4vdk2wd9l5x8ea | no website | identity none | contact none
- Inference URL: http://95.217.47.126:8000
- Next actions: corroborate beneficiary owner

Public sources:
- validator_moniker (high, signal): gonkavaloper1tl5m3vuqsx333v7095ymwjdc4vdk2wd9l5x8ea
- participant_inference_url (medium, signal): http://95.217.47.126:8000

### http://94.130.64.22:8000

- Address: `gonka14g78ez2zy08k8sssue483zmfpgd4qut8zcwlqc`
- Roles: recipient; compensation: 2602.055674 GONKA; voting power: 0; vote: did_not_vote
- Best public name: gonkavaloper14g78ez2zy08k8sssue483zmfpgd4qut87clch4
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: gonkavaloper14g78ez2zy08k8sssue483zmfpgd4qut87clch4 | no website | identity none | contact none
- Inference URL: http://94.130.64.22:8000
- Next actions: corroborate beneficiary owner

Public sources:
- validator_moniker (high, signal): gonkavaloper14g78ez2zy08k8sssue483zmfpgd4qut87clch4
- participant_inference_url (medium, signal): http://94.130.64.22:8000

### http://gnk.antifreeze.dev:8000

- Address: `gonka1tlvg4kjx7ljd5thgd5fkgh39q6lu8cmxupktgg`
- Roles: recipient; compensation: 2293.694675 GONKA; voting power: 0; vote: did_not_vote
- Best public name: gonkavaloper1tlvg4kjx7ljd5thgd5fkgh39q6lu8cmxqp8vl9
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: gonkavaloper1tlvg4kjx7ljd5thgd5fkgh39q6lu8cmxqp8vl9 | no website | identity none | contact none
- Inference URL: http://gnk.antifreeze.dev:8000
- Next actions: corroborate beneficiary owner

Public sources:
- validator_moniker (high, signal): gonkavaloper1tlvg4kjx7ljd5thgd5fkgh39q6lu8cmxqp8vl9
- participant_inference_url (medium, signal): http://gnk.antifreeze.dev:8000

### http://125.93.200.207:8000

- Address: `gonka15p7s7w2hx0y8095lddd4ummm2y0kwpwljk00aq`
- Roles: recipient; compensation: 2034.501081 GONKA; voting power: 0; vote: did_not_vote
- Best public name: http://125.93.200.207:8000
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: none | no website | identity none | contact none
- Inference URL: http://125.93.200.207:8000
- Next actions: corroborate beneficiary owner

Public sources:
- participant_inference_url (medium, signal): http://125.93.200.207:8000

### http://198.244.228.95:8000

- Address: `gonka1ce02jjduga8jvwj8jx39mxn0jr345vgkx7lk2n`
- Roles: recipient; compensation: 1753.409171 GONKA; voting power: 0; vote: did_not_vote
- Best public name: http://198.244.228.95:8000
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: none | no website | identity none | contact none
- Inference URL: http://198.244.228.95:8000
- Next actions: corroborate beneficiary owner

Public sources:
- participant_inference_url (medium, signal): http://198.244.228.95:8000

### http://178.105.165.144:8000

- Address: `gonka10070xwkwv00sulsa7gdfwkgh8w069stkjjf39x`
- Roles: recipient; compensation: 1017.602508 GONKA; voting power: 0; vote: did_not_vote
- Best public name: gonkavaloper10070xwkwv00sulsa7gdfwkgh8w069stkwjckjt
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: gonkavaloper10070xwkwv00sulsa7gdfwkgh8w069stkwjckjt | no website | identity none | contact none
- Inference URL: http://178.105.165.144:8000
- Next actions: corroborate beneficiary owner

Public sources:
- validator_moniker (high, signal): gonkavaloper10070xwkwv00sulsa7gdfwkgh8w069stkwjckjt
- participant_inference_url (medium, signal): http://178.105.165.144:8000

### http://178.105.169.55:8000

- Address: `gonka10075dz43h94zhqu5hwdj3nyjay6v8mzwvpxr0s`
- Roles: recipient; compensation: 1017.602508 GONKA; voting power: 0; vote: did_not_vote
- Best public name: gonkavaloper10075dz43h94zhqu5hwdj3nyjay6v8mzwsphyca
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: gonkavaloper10075dz43h94zhqu5hwdj3nyjay6v8mzwsphyca | no website | identity none | contact none
- Inference URL: http://178.105.169.55:8000
- Next actions: corroborate beneficiary owner

Public sources:
- validator_moniker (high, signal): gonkavaloper10075dz43h94zhqu5hwdj3nyjay6v8mzwsphyca
- participant_inference_url (medium, signal): http://178.105.169.55:8000

### http://178.105.175.114:8000

- Address: `gonka1007lnkyhdh7aq0vjdcdwcerkdh4yy85rymjdg6`
- Roles: recipient; compensation: 1007.974842 GONKA; voting power: 0; vote: did_not_vote
- Best public name: gonkavaloper1007lnkyhdh7aq0vjdcdwcerkdh4yy85rcmr2lh
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: gonkavaloper1007lnkyhdh7aq0vjdcdwcerkdh4yy85rcmr2lh | no website | identity none | contact none
- Inference URL: http://178.105.175.114:8000
- Next actions: corroborate beneficiary owner

Public sources:
- validator_moniker (high, signal): gonkavaloper1007lnkyhdh7aq0vjdcdwcerkdh4yy85rcmr2lh
- participant_inference_url (medium, signal): http://178.105.175.114:8000

### http://185.70.186.176:8000

- Address: `gonka13a4v8gxxjav5t4xq5y9cv9d8rfnvkjfw5adqz3`
- Roles: recipient; compensation: 521.637815 GONKA; voting power: 0; vote: did_not_vote
- Best public name: gonkavaloper13a4v8gxxjav5t4xq5y9cv9d8rfnvkjfwgau84u
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: gonkavaloper13a4v8gxxjav5t4xq5y9cv9d8rfnvkjfwgau84u | no website | identity none | contact none
- Inference URL: http://185.70.186.176:8000
- Next actions: corroborate beneficiary owner

Public sources:
- validator_moniker (high, signal): gonkavaloper13a4v8gxxjav5t4xq5y9cv9d8rfnvkjfwgau84u
- participant_inference_url (medium, signal): http://185.70.186.176:8000

### http://202.78.161.246:8000

- Address: `gonka1myu058axjs62mc3e7na9krwvqpfl9z3gtcw9es`
- Roles: recipient; compensation: 279.015575 GONKA; voting power: 0; vote: did_not_vote
- Best public name: http://202.78.161.246:8000
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: none | no website | identity none | contact none
- Inference URL: http://202.78.161.246:8000
- Next actions: corroborate beneficiary owner

Public sources:
- participant_inference_url (medium, signal): http://202.78.161.246:8000

### http://202.78.161.100:8000

- Address: `gonka14ef2pxjge75gflqftn7m2wy0xv59gq9uc7qnct`
- Roles: recipient; compensation: 276.414091 GONKA; voting power: 0; vote: did_not_vote
- Best public name: gonkavaloper14ef2pxjge75gflqftn7m2wy0xv59gq9uy7350x
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: gonkavaloper14ef2pxjge75gflqftn7m2wy0xv59gq9uy7350x | no website | identity none | contact none
- Inference URL: http://202.78.161.100:8000
- Next actions: corroborate beneficiary owner

Public sources:
- validator_moniker (high, signal): gonkavaloper14ef2pxjge75gflqftn7m2wy0xv59gq9uy7350x
- participant_inference_url (medium, signal): http://202.78.161.100:8000

### http://20.163.111.183:8000

- Address: `gonka1fvly5jrewyjmjfgwah3khy9rttq4cqajcesv9p`
- Roles: recipient, voter; compensation: 113.864834 GONKA; voting power: 0; vote: no_with_veto
- Best public name: gonkavaloper1fvly5jrewyjmjfgwah3khy9rttq4cqajyeptjv
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: gonkavaloper1fvly5jrewyjmjfgwah3khy9rttq4cqajyeptjv | no website | identity none | contact none
- Inference URL: http://20.163.111.183:8000
- Next actions: review recipient-voter conflict | corroborate voter owner | corroborate beneficiary owner

Public sources:
- validator_moniker (high, signal): gonkavaloper1fvly5jrewyjmjfgwah3khy9rttq4cqajyeptjv
- participant_inference_url (medium, signal): http://20.163.111.183:8000

### http://20.171.77.105:8000

- Address: `gonka1cuwejs77gectp3n32wg8q27hlsa4m3hqspf4ww`
- Roles: recipient, voter; compensation: 108.366532 GONKA; voting power: 0; vote: no_with_veto
- Best public name: gonkavaloper1cuwejs77gectp3n32wg8q27hlsa4m3hqvpcjer
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: gonkavaloper1cuwejs77gectp3n32wg8q27hlsa4m3hqvpcjer | no website | identity none | contact none
- Inference URL: http://20.171.77.105:8000
- Next actions: review recipient-voter conflict | corroborate voter owner | corroborate beneficiary owner

Public sources:
- validator_moniker (high, signal): gonkavaloper1cuwejs77gectp3n32wg8q27hlsa4m3hqvpcjer
- participant_inference_url (medium, signal): http://20.171.77.105:8000

### http://64.236.203.236:8000

- Address: `gonka1tmk2tzdneht6smu34pkmqdvu7p34qavvmwtwq2`
- Roles: recipient; compensation: 100.56894 GONKA; voting power: 0; vote: did_not_vote
- Best public name: http://64.236.203.236:8000
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: none | no website | identity none | contact none
- Inference URL: http://64.236.203.236:8000
- Next actions: corroborate beneficiary owner

Public sources:
- participant_inference_url (medium, signal): http://64.236.203.236:8000

### http://20.88.58.210:8000

- Address: `gonka1naxyjmun6kl23htjdujwd6c5z5avgwapsrmfk3`
- Roles: voter; compensation: 0 GONKA; voting power: 0; vote: no_with_veto
- Best public name: gonkavaloper1naxyjmun6kl23htjdujwd6c5z5avgwapvr2wpu
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: gonkavaloper1naxyjmun6kl23htjdujwd6c5z5avgwapvr2wpu | no website | identity none | contact none
- Inference URL: http://20.88.58.210:8000
- Next actions: corroborate voter owner

Public sources:
- validator_moniker (high, signal): gonkavaloper1naxyjmun6kl23htjdujwd6c5z5avgwapvr2wpu
- participant_inference_url (medium, signal): http://20.88.58.210:8000

### http://78.46.89.87:8000

- Address: `gonka1kvmerzu64094dt9t62ea0cp75larh39ulzldum`
- Roles: voter; compensation: 0 GONKA; voting power: 0; vote: no_with_veto
- Best public name: gonkavaloper1kvmerzu64094dt9t62ea0cp75larh39urzw2tk
- Evidence boundary: public_name_or_metadata_signal
- GNS: none; reverse: none
- Validator: gonkavaloper1kvmerzu64094dt9t62ea0cp75larh39urzw2tk | no website | identity none | contact none
- Inference URL: http://78.46.89.87:8000
- Next actions: corroborate voter owner

Public sources:
- validator_moniker (high, signal): gonkavaloper1kvmerzu64094dt9t62ea0cp75larh39urzw2tk
- participant_inference_url (medium, signal): http://78.46.89.87:8000

## Shared Public Name/Metadata Groups

### participant_inference_url: http://178.105.170.135:8000

- Boundary: medium signal; addresses: 2
- Compensation: 20610.390028 GONKA; voting power: 0
- Vote power: none
- Addresses: gonka10079cnl3nuh2k82mhkm04dj0slhtw9kmjewwau gonka16r08lhm50zwjddmslfw2344z67r70vqul0dus6
- Source file: data/participants_by_address.json

### validator_identity: 673C81B66A67ED67

- Boundary: high proof; addresses: 2
- Compensation: 4044.099545 GONKA; voting power: 0
- Vote power: none
- Addresses: gonka1kx9mca3xm8u8ypzfuhmxey66u0ufxhs7nm6wc5 gonka1y2a9p56kv044327uycmqdexl7zs82fs5ryv5le
- Source file: data/validators.json

### validator_website: https://gonka.ai

- Boundary: medium signal; addresses: 2
- Compensation: 4044.099545 GONKA; voting power: 0
- Vote power: none
- Addresses: gonka1kx9mca3xm8u8ypzfuhmxey66u0ufxhs7nm6wc5 gonka1y2a9p56kv044327uycmqdexl7zs82fs5ryv5le
- Source file: data/validators.json

### participant_inference_url: http://135.181.56.61:8000

- Boundary: medium signal; addresses: 1
- Compensation: 158541.879456 GONKA; voting power: 0
- Vote power: none
- Addresses: gonka1qa90tgczc0k5dvk4l5nvlf5y6phgm6mg22sfjv
- Source file: data/participants_by_address.json

### validator_moniker: gonkavaloper1qa90tgczc0k5dvk4l5nvlf5y6phgm6mgk2pw9p

- Boundary: high signal; addresses: 1
- Compensation: 158541.879456 GONKA; voting power: 0
- Vote power: none
- Addresses: gonka1qa90tgczc0k5dvk4l5nvlf5y6phgm6mg22sfjv
- Source file: data/validators.json

### participant_inference_url: http://54.37.131.156:8000

- Boundary: medium signal; addresses: 1
- Compensation: 101147.807219 GONKA; voting power: 0
- Vote power: none
- Addresses: gonka17pw6099q758qwzewtrqmqpf5c2lrhr97fwqexu
- Source file: data/participants_by_address.json

### participant_inference_url: http://65.21.232.177:8000

- Boundary: medium signal; addresses: 1
- Compensation: 96601.320933 GONKA; voting power: 0
- Vote power: none
- Addresses: gonka1uhqpup9fev3zahlx6n326lp0krznc6usjtx6lu
- Source file: data/participants_by_address.json

### validator_moniker: gonkavaloper1uhqpup9fev3zahlx6n326lp0krznc6uswthag3

- Boundary: high signal; addresses: 1
- Compensation: 96601.320933 GONKA; voting power: 0
- Vote power: none
- Addresses: gonka1uhqpup9fev3zahlx6n326lp0krznc6usjtx6lu
- Source file: data/validators.json

### participant_inference_url: http://57.128.30.101:8000

- Boundary: medium signal; addresses: 1
- Compensation: 79247.555227 GONKA; voting power: 0
- Vote power: none
- Addresses: gonka1wthc28t25pg63hzvl07rl8e8r6km6hesl6jhsz
- Source file: data/participants_by_address.json

### participant_inference_url: http://89.169.97.113:8000

- Boundary: medium signal; addresses: 1
- Compensation: 73073.708453 GONKA; voting power: 92840
- Vote power: yes=92840.0
- Addresses: gonka1q5xt54wncgzk7dxv9x64uln68455g83wu9tugg
- Source file: data/participants_by_address.json

### validator_moniker: gonkavaloper1q5xt54wncgzk7dxv9x64uln68455g83wq96ml9

- Boundary: high signal; addresses: 1
- Compensation: 73073.708453 GONKA; voting power: 92840
- Vote power: yes=92840.0
- Addresses: gonka1q5xt54wncgzk7dxv9x64uln68455g83wu9tugg
- Source file: data/validators.json

### participant_inference_url: http://89.149.242.149:8000

- Boundary: medium signal; addresses: 1
- Compensation: 66487.744752 GONKA; voting power: 28865
- Vote power: no_with_veto=28865.0
- Addresses: gonka10mmdjau4dnj8krs7sh7t7635ttnmq9u3vqgz09
- Source file: data/participants_by_address.json

### validator_identity: B22258DF68546529

- Boundary: high proof; addresses: 1
- Compensation: 66487.744752 GONKA; voting power: 28865
- Vote power: no_with_veto=28865.0
- Addresses: gonka10mmdjau4dnj8krs7sh7t7635ttnmq9u3vqgz09
- Source file: data/validators.json

### validator_moniker: ancapex | Mine from $1, no losses from node failures

- Boundary: high proof; addresses: 1
- Compensation: 66487.744752 GONKA; voting power: 28865
- Vote power: no_with_veto=28865.0
- Addresses: gonka10mmdjau4dnj8krs7sh7t7635ttnmq9u3vqgz09
- Source file: data/validators.json

### validator_website: https://ancapex.ai

- Boundary: medium signal; addresses: 1
- Compensation: 66487.744752 GONKA; voting power: 28865
- Vote power: no_with_veto=28865.0
- Addresses: gonka10mmdjau4dnj8krs7sh7t7635ttnmq9u3vqgz09
- Source file: data/validators.json

### participant_inference_url: http://54.38.118.143:8000

- Boundary: medium signal; addresses: 1
- Compensation: 52290.195676 GONKA; voting power: 86433
- Vote power: yes=86433.0
- Addresses: gonka1gvrrhjmy4w4mayvs2s5l23edj8ertcmtd2v4zr
- Source file: data/participants_by_address.json

### validator_moniker: gonkavaloper1gvrrhjmy4w4mayvs2s5l23edj8ertcmt32aj4w

- Boundary: high signal; addresses: 1
- Compensation: 52290.195676 GONKA; voting power: 86433
- Vote power: yes=86433.0
- Addresses: gonka1gvrrhjmy4w4mayvs2s5l23edj8ertcmtd2v4zr
- Source file: data/validators.json

### participant_inference_url: http://178.104.95.5:8000

- Boundary: medium signal; addresses: 1
- Compensation: 39809.676543 GONKA; voting power: 0
- Vote power: none
- Addresses: gonka1j7x6dv42xehe9e5au4ku3wvzwtqlegfjhlvzj6
- Source file: data/participants_by_address.json

### validator_moniker: gonkavaloper1j7x6dv42xehe9e5au4ku3wvzwtqlegfjtla99h

- Boundary: high signal; addresses: 1
- Compensation: 39809.676543 GONKA; voting power: 0
- Vote power: none
- Addresses: gonka1j7x6dv42xehe9e5au4ku3wvzwtqlegfjhlvzj6
- Source file: data/validators.json

### participant_inference_url: http://95.217.121.189:8000

- Boundary: medium signal; addresses: 1
- Compensation: 33750.579636 GONKA; voting power: 0
- Vote power: none
- Addresses: gonka1jrgm47v5eg876udmzg6j6glqcsd5x0vk6crpax
- Source file: data/participants_by_address.json

### validator_moniker: gonkavaloper1jrgm47v5eg876udmzg6j6glqcsd5x0vkxcjx2t

- Boundary: high signal; addresses: 1
- Compensation: 33750.579636 GONKA; voting power: 0
- Vote power: none
- Addresses: gonka1jrgm47v5eg876udmzg6j6glqcsd5x0vk6crpax
- Source file: data/validators.json

### validator_moniker: gonkavaloper10079cnl3nuh2k82mhkm04dj0slhtw9kmwelf23

- Boundary: high signal; addresses: 1
- Compensation: 20610.390028 GONKA; voting power: 0
- Vote power: none
- Addresses: gonka10079cnl3nuh2k82mhkm04dj0slhtw9kmjewwau
- Source file: data/validators.json

### participant_inference_url: http://136.243.110.227:8000

- Boundary: medium signal; addresses: 1
- Compensation: 18234.887511 GONKA; voting power: 0
- Vote power: none
- Addresses: gonka15munkmx6x7k6rqqeexjet4556p7at39ks9qgr5
- Source file: data/participants_by_address.json

### participant_inference_url: http://94.130.152.246:8000

- Boundary: medium signal; addresses: 1
- Compensation: 17630.158097 GONKA; voting power: 0
- Vote power: none
- Addresses: gonka1yal0ysgzc860zt3y8cds8656tnueusgymftvkw
- Source file: data/participants_by_address.json

### validator_moniker: gonkavaloper1yal0ysgzc860zt3y8cds8656tnueusgy8f6tpr

- Boundary: high signal; addresses: 1
- Compensation: 17630.158097 GONKA; voting power: 0
- Vote power: none
- Addresses: gonka1yal0ysgzc860zt3y8cds8656tnueusgymftvkw
- Source file: data/validators.json

### participant_inference_url: http://195.201.192.170:8000

- Boundary: medium signal; addresses: 1
- Compensation: 13958.367773 GONKA; voting power: 0
- Vote power: none
- Addresses: gonka1830lqug50lse998x2lakk4pj5ypfumz5pasz0y
- Source file: data/participants_by_address.json

### validator_moniker: gonkavaloper1830lqug50lse998x2lakk4pj5ypfumz5aap9cf

- Boundary: high signal; addresses: 1
- Compensation: 13958.367773 GONKA; voting power: 0
- Vote power: none
- Addresses: gonka1830lqug50lse998x2lakk4pj5ypfumz5pasz0y
- Source file: data/validators.json

### participant_inference_url: http://35.89.168.230:8000

- Boundary: medium signal; addresses: 1
- Compensation: 12612.234866 GONKA; voting power: 0
- Vote power: none
- Addresses: gonka1ujnc662v6g69jm6fgxnr79a2m7ehzeut059239
- Source file: data/participants_by_address.json

### validator_moniker: gonkavaloper1ujnc662v6g69jm6fgxnr79a2m7ehzeutn55dxg

- Boundary: high signal; addresses: 1
- Compensation: 12612.234866 GONKA; voting power: 0
- Vote power: none
- Addresses: gonka1ujnc662v6g69jm6fgxnr79a2m7ehzeut059239
- Source file: data/validators.json

### participant_inference_url: http://178.105.172.102:8000

- Boundary: medium signal; addresses: 1
- Compensation: 11688.555563 GONKA; voting power: 0
- Vote power: none
- Addresses: gonka1007g0ut3u4wjkay9hegqfev4pj90qgexwskmcw
- Source file: data/participants_by_address.json

### validator_moniker: gonkavaloper1007g0ut3u4wjkay9hegqfev4pj90qgexjs8u0r

- Boundary: high signal; addresses: 1
- Compensation: 11688.555563 GONKA; voting power: 0
- Vote power: none
- Addresses: gonka1007g0ut3u4wjkay9hegqfev4pj90qgexwskmcw
- Source file: data/validators.json

### participant_inference_url: http://204.12.168.89:8000

- Boundary: medium signal; addresses: 1
- Compensation: 11366.419254 GONKA; voting power: 0
- Vote power: none
- Addresses: gonka1c6fwzedfsmpu4jnjekv4cn7mvr7x7fuqd6uqt9
- Source file: data/participants_by_address.json

### validator_moniker: gonkavaloper1c6fwzedfsmpu4jnjekv4cn7mvr7x7fuq36d8ug

- Boundary: high signal; addresses: 1
- Compensation: 11366.419254 GONKA; voting power: 0
- Vote power: none
- Addresses: gonka1c6fwzedfsmpu4jnjekv4cn7mvr7x7fuqd6uqt9
- Source file: data/validators.json

### participant_inference_url: http://178.105.174.27:8000

- Boundary: medium signal; addresses: 1
- Compensation: 11262.520198 GONKA; voting power: 57838
- Vote power: yes=57838.0
- Addresses: gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv
- Source file: data/participants_by_address.json

### participant_inference_url: http://network000.kaitaku.ai:8000

- Boundary: medium signal; addresses: 1
- Compensation: 11021.18308 GONKA; voting power: 25278
- Vote power: no_with_veto=25278.0
- Addresses: gonka168rtjfkszuhcggg4dfyse4yh7xn9zwfglnkns2
- Source file: data/participants_by_address.json

### validator_moniker: gonkavaloper168rtjfkszuhcggg4dfyse4yh7xn9zwfgrn8588

- Boundary: high signal; addresses: 1
- Compensation: 11021.18308 GONKA; voting power: 25278
- Vote power: no_with_veto=25278.0
- Addresses: gonka168rtjfkszuhcggg4dfyse4yh7xn9zwfglnkns2
- Source file: data/validators.json

### participant_inference_url: http://88.99.213.222:8000

- Boundary: medium signal; addresses: 1
- Compensation: 10934.181496 GONKA; voting power: 0
- Vote power: none
- Addresses: gonka1wt8sr9jxzpec65j7zkxsgh6edk3m6r8nlf5za4
- Source file: data/participants_by_address.json

### participant_inference_url: http://95.217.35.48:8000

- Boundary: medium signal; addresses: 1
- Compensation: 10456.612261 GONKA; voting power: 0
- Vote power: none
- Addresses: gonka1wkgawwdzj623ss8eywayzdj6qcgr2llygactje
- Source file: data/participants_by_address.json

### participant_inference_url: http://94.130.143.155:8000

- Boundary: medium signal; addresses: 1
- Compensation: 9768.694504 GONKA; voting power: 0
- Vote power: none
- Addresses: gonka1xwkesaxvdadh9wt9yyladu0r260s7whklcktds
- Source file: data/participants_by_address.json

### validator_moniker: gonkavaloper1xwkesaxvdadh9wt9yyladu0r260s7whkrc8v6a

- Boundary: high signal; addresses: 1
- Compensation: 9768.694504 GONKA; voting power: 0
- Vote power: none
- Addresses: gonka1xwkesaxvdadh9wt9yyladu0r260s7whklcktds
- Source file: data/validators.json

## Still Missing Public Names
