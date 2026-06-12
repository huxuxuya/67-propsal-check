# Model Cap Factor Timeline

This report shows model-level ComputeGroupCap pressure by epoch. The main chart metric is applied scale: `min(1, cap_weight / raw_consensus_weight)`. A lower value means the model subgroup was compressed harder by cap.

## Summary

- Rows: 24
- Capped rows: 9
- Missing subgroup rows: 0
- Models: Kimi, Qwen
- Epochs: 265, 266, 267, 268, 269, 270, 271, 272, 273, 274, 275, 276
- Params sources: archive_rpc_params
- Source: RPC GONKA_RPC_URL; API fallback_public_api; generated 2026-06-12T07:35:17.619054+00:00

## Rows

- e265 Kimi `moonshotai/Kimi-K2.6`: status=cap_reference_missing scale=n/a pressure=n/a raw=476,154 cap=exempt coeff=1.262086 participants=20 nodes=44 params=archive_rpc_params
- e265 Qwen `Qwen/Qwen3-235B-A22B-Instruct-2507-FP8`: status=initial_exempt scale=1.0000 pressure=0.0000 raw=441,184 cap=exempt coeff=0.3593 participants=41 nodes=188 params=archive_rpc_params
- e266 Kimi `moonshotai/Kimi-K2.6`: status=under_cap scale=1.0000 pressure=0.1115 raw=75,640 cap=678,132 coeff=1.262086 participants=8 nodes=9 params=archive_rpc_params
- e266 Qwen `Qwen/Qwen3-235B-A22B-Instruct-2507-FP8`: status=initial_exempt scale=1.0000 pressure=0.0000 raw=318,374 cap=exempt coeff=0.3593 participants=40 nodes=141 params=archive_rpc_params
- e267 Kimi `moonshotai/Kimi-K2.6`: status=capped scale=0.3023 pressure=3.3078 raw=831,487 cap=251,369 coeff=1.262086 participants=27 nodes=81 params=archive_rpc_params
- e267 Qwen `Qwen/Qwen3-235B-A22B-Instruct-2507-FP8`: status=initial_exempt scale=1.0000 pressure=0.0000 raw=301,029 cap=exempt coeff=0.3593 participants=34 nodes=134 params=archive_rpc_params
- e268 Kimi `moonshotai/Kimi-K2.6`: status=capped scale=0.7154 pressure=1.3979 raw=567,626 cap=406,061 coeff=1.262086 participants=20 nodes=52 params=archive_rpc_params
- e268 Qwen `Qwen/Qwen3-235B-A22B-Instruct-2507-FP8`: status=initial_exempt scale=1.0000 pressure=0.0000 raw=322,358 cap=exempt coeff=0.3593 participants=43 nodes=129 params=archive_rpc_params
- e269 Kimi `moonshotai/Kimi-K2.6`: status=capped scale=0.9206 pressure=1.0863 raw=569,177 cap=523,979 coeff=1.262086 participants=30 nodes=56 params=archive_rpc_params
- e269 Qwen `Qwen/Qwen3-235B-A22B-Instruct-2507-FP8`: status=initial_exempt scale=1.0000 pressure=0.0000 raw=277,904 cap=exempt coeff=0.3593 participants=36 nodes=111 params=archive_rpc_params
- e270 Kimi `moonshotai/Kimi-K2.6`: status=capped scale=0.7748 pressure=1.2907 raw=657,653 cap=509,547 coeff=1.262086 participants=23 nodes=70 params=archive_rpc_params
- e270 Qwen `Qwen/Qwen3-235B-A22B-Instruct-2507-FP8`: status=initial_exempt scale=1.0000 pressure=0.0000 raw=269,439 cap=exempt coeff=0.3593 participants=32 nodes=109 params=archive_rpc_params
- e271 Kimi `moonshotai/Kimi-K2.6`: status=capped scale=0.8728 pressure=1.1457 raw=616,492 cap=538,100 coeff=1.262086 participants=23 nodes=65 params=archive_rpc_params
- e271 Qwen `Qwen/Qwen3-235B-A22B-Instruct-2507-FP8`: status=initial_exempt scale=1.0000 pressure=0.0000 raw=277,805 cap=exempt coeff=0.3593 participants=34 nodes=111 params=archive_rpc_params
- e272 Kimi `moonshotai/Kimi-K2.6`: status=capped scale=0.9294 pressure=1.0759 raw=642,361 cap=597,022 coeff=1.262086 participants=23 nodes=65 params=archive_rpc_params
- e272 Qwen `Qwen/Qwen3-235B-A22B-Instruct-2507-FP8`: status=initial_exempt scale=1.0000 pressure=0.0000 raw=267,305 cap=exempt coeff=0.3593 participants=35 nodes=109 params=archive_rpc_params
- e273 Kimi `moonshotai/Kimi-K2.6`: status=capped scale=0.7751 pressure=1.2902 raw=796,561 cap=617,387 coeff=1.262086 participants=30 nodes=81 params=archive_rpc_params
- e273 Qwen `Qwen/Qwen3-235B-A22B-Instruct-2507-FP8`: status=initial_exempt scale=1.0000 pressure=0.0000 raw=249,205 cap=exempt coeff=0.3593 participants=39 nodes=108 params=archive_rpc_params
- e274 Kimi `moonshotai/Kimi-K2.6`: status=capped scale=0.8595 pressure=1.1635 raw=662,085 cap=569,036 coeff=1.262086 participants=24 nodes=73 params=archive_rpc_params
- e274 Qwen `Qwen/Qwen3-235B-A22B-Instruct-2507-FP8`: status=initial_exempt scale=1.0000 pressure=0.0000 raw=259,801 cap=exempt coeff=0.3593 participants=38 nodes=110 params=archive_rpc_params
- e275 Kimi `moonshotai/Kimi-K2.6`: status=capped scale=0.7725 pressure=1.2946 raw=744,509 cap=575,103 coeff=1.262086 participants=24 nodes=80 params=archive_rpc_params
- e275 Qwen `Qwen/Qwen3-235B-A22B-Instruct-2507-FP8`: status=initial_exempt scale=1.0000 pressure=0.0000 raw=256,442 cap=exempt coeff=0.3593 participants=39 nodes=112 params=archive_rpc_params
- e276 Kimi `moonshotai/Kimi-K2.6`: status=under_cap scale=1.0000 pressure=0.8881 raw=490,820 cap=552,693 coeff=0.78 participants=23 nodes=83 params=archive_rpc_params
- e276 Qwen `Qwen/Qwen3-235B-A22B-Instruct-2507-FP8`: status=initial_exempt scale=1.0000 pressure=0.0000 raw=264,384 cap=exempt coeff=0.3593 participants=39 nodes=126 params=archive_rpc_params
