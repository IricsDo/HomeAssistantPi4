# Smoke baseline snapshot before unified migration

Snapshot code commit: `f52379b` (`feat:expand-smoke-dataset-and-analysis-pipeline`).

## Artifact

- Path: `E:\HomeAssistantPi4\models\checkpoints\smoke_yolo26n_combined_v2.pt`
- Bytes: `5,365,829`
- SHA-256: `1104F90EE0723E0877A4797C71CD88EBC7B43A5841396D153010F59781EA3D04`
- Best epoch: 56 of 60
- Frozen confidence threshold: `0.43043043043043044`

## Combined validation

- Precision: 0.93959
- Recall: 0.89277
- mAP50: 0.94678
- mAP50-95: 0.64999
- At frozen threshold: precision 0.92681, recall 0.90034

## Locked test results at the frozen threshold

| Source | Precision | Recall | mAP50 | mAP50-95 |
|---|---:|---:|---:|---:|
| Home-Fire | 0.90909 | 0.86357 | 0.89439 | 0.55217 |
| Indoor Fire & Smoke | 0.99642 | 0.99634 | 0.99496 | 0.86369 |

## Validation error analysis

- TP 767, FP 61, FN 91
- Precision 0.92633, recall 0.89394, F1 0.90985
- False alarms on negative images: 11/980 (1.12%)
- Misses: 59 below confidence, 28 localization/no-overlap, 4 without candidate
- Medium-smoke recall: 0.822
- Blurred slice: precision 0.855, recall 0.826
- Dark slice recall: 0.865

This checkpoint remains the smoke regression baseline. A unified model is not
accepted if smoke recall drops by more than 0.03 on the same locked slice unless
there is a documented safety/latency trade-off.
