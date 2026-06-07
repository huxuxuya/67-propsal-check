# PoC Commits — Epochs 266–269

Raw nonce commit data fetched from the archive node for the restitution case covering epochs 266–269.
Epoch 270 had not started at time of collection (current epoch was 269).

## Files

| File | Epoch | Commits |
|------|-------|---------|
| epoch266_commits.json | 266 | 44 |
| epoch267_commits.json | 267 | 49 |
| epoch268_commits.json | 268 | 47 |
| epoch269_commits.json | 269 | 48 |

## Commands Used

Block heights follow the formula:
- `poc_start = 4105361 + (epoch - 266) * 15391`
- `epoch_end  = poc_start + 15391 - 1`

**Epochs 266–268** (completed — query at epoch end height to read state before pruning):
```
inferenced query inference all-poc-v2-store-commits <poc_start> \
  --node <ARCHIVE_NODE> \
  --height <epoch_end> \
  -o json
```

| Epoch | poc_start | epoch_end (--height) |
|-------|-----------|----------------------|
| 266   | 4105361   | 4120751              |
| 267   | 4120752   | 4136142              |
| 268   | 4136143   | 4151533              |

**Epoch 269** (current — no `--height` pin needed):
```
inferenced query inference all-poc-v2-store-commits 4151534 \
  --node <ARCHIVE_NODE> \
  -o json
```

> **Note:** The archive node IP is stored in `.env` as `ARCHIVE_NODE_URL` and must not be committed.
