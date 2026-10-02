# YOLO26n v3 evaluation and deployment decision

## Decision

The v3 416 px fine-tune improves both hazard operating points, but it does not
meet the person quality gate at 416, 512, or 640 px. Keep v3 `best.pt` as an
experimental checkpoint and do not export it as the final NCNN artifact.

The test split was not reopened. Epoch selection, threshold calibration and the
resolution comparison use validation only.

## Training result

The run completed all 20 configured epochs. Epoch 19 had the highest recorded
validation mAP50-95 (`0.52560`). Reloading the saved `best.pt` at 416 px produced
aggregate mAP50/mAP50-95 `0.81232/0.52549`.

Checkpoint:

`E:\HomeAssistantPi4\runs\indoor-detection\indoor_partial_joint_yolo26n_v3_416\weights\best.pt`

SHA-256:

`ebeaaa7848167e658b5f6c22a3869839133aafe798937c33ddffab73d11ac1ae`

## 416 px calibrated operating points

| Class | Selection | Threshold | Precision | Recall | F1 | Gate |
|---|---|---:|---:|---:|---:|---|
| smoke | recall >= 0.90 | 0.106106 | 0.770 | 0.911 | 0.835 | PASS |
| fire | recall >= 0.90 | 0.279279 | 0.866 | 0.906 | 0.886 | PASS |
| person | maximum F1 | 0.328328 | 0.759 | 0.518 | 0.616 | FAIL |

Smoke negative-image false alarms fall from 5.25% in v2 to 2.32% in v3. Fire
negative-image false alarms are 1.30%. Smoke recall on the blurred bucket is
0.860, so blurred smoke remains eligible for detection.

Person misses remain dominated by scale: recall is 0.844 for large people,
0.620 for medium people and 0.213 for people occupying less than 1% of the
image. Of 2,573 missed person boxes, 1,649 are below confidence and 893 are
localization/no-overlap errors. Person false alarms occur on 13.00% of negative
images.

Visual review confirms that person false negatives are mainly distant or
crowded people. Frequent false positives are animals, statues, dolls and other
human-shaped objects. Hazard misses continue to include small or dark regions
and annotation/localization disagreements.

## Resolution diagnostic

| Input | Aggregate mAP50/mAP50-95 | Person threshold | Person precision | Person recall | Person F1 | Gate |
|---:|---:|---:|---:|---:|---:|---|
| 416 | 0.812/0.525 | 0.328328 | 0.755 | 0.520 | 0.616 | FAIL |
| 512 | 0.830/0.543 | 0.297297 | 0.706 | 0.575 | 0.634 | FAIL |
| 640 | 0.832/0.536 | 0.343343 | 0.723 | 0.586 | 0.647 | FAIL |

Increasing inference resolution helps person recall, but even 640 px stays
below the required validation F1 0.65 and recall 0.60. A larger export would
also increase Raspberry Pi compute cost, so resolution alone is not accepted as
the fix.

## Next model cycle

Use v3 `best.pt` as the starting point for a short 512 px fine-tune. Keep the
same audited class-scoped dataset, reduce geometric scale variation so small
people are not further downscaled during training, and keep all multi-image
augmentations disabled. Re-run the full validation calibration and error gates
before any NCNN export.

## Artifacts

Reports and galleries are stored outside Git at:

`E:\HomeAssistantPi4\reports\indoor-yolo26n-v3-evaluation`
