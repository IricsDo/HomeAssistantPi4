# YOLO26n v2 evaluation and deployment decision

## Decision

`best.pt` remains the locked v2 reference checkpoint, but it is **not approved
for final NCNN export at 416 px**. The 416 px validation result loses too much
person recall and requires an impractically low smoke confidence to retain the
smoke recall target. Test was not reopened while making this decision.

The next model cycle should start from v2 `best.pt`, train against the same
class-scoped dataset at the intended edge resolution, and remain a new run so
v2 stays reproducible.

## Calibration policy

- Smoke: highest confidence that reaches validation recall 0.90.
- Fire: highest confidence that reaches validation recall 0.90.
- Person: confidence with maximum validation F1 because person is an auxiliary
  occupancy signal and does not create a hazard alert by itself.
- Thresholds are resolution-specific. A 640 px threshold must not be copied to
  a 416 px runtime.

## Resolution comparison

| Input | Class | Threshold | Precision | Recall | F1 |
|---:|---|---:|---:|---:|---:|
| 640 | smoke | 0.249249 | 0.875 | 0.903 | 0.889 |
| 640 | fire | 0.439439 | 0.927 | 0.900 | 0.913 |
| 640 | person | 0.270270 | 0.733 | 0.601 | 0.660 |
| 416 | smoke | 0.033033 | 0.581 | 0.916 | 0.711 |
| 416 | fire | 0.131131 | 0.801 | 0.907 | 0.851 |
| 416 | person | 0.291291 | 0.788 | 0.480 | 0.597 |

The 640 rows use the scope-aware error analyzer at IoU 0.50. Minor differences
from the interpolated curve reports are expected. At 416, aggregate
mAP50/mAP50-95 falls from `0.846/0.565` to `0.796/0.507`.

## Error analysis

At 640 px:

- Smoke negative-image false-alarm rate is 0.81%; 58 of 83 misses are below
  the selected confidence.
- Fire negative-image false-alarm rate is 1.14%; 91 of 126 misses are below
  confidence.
- Person negative-image false-alarm rate is 12.31%. Small-person recall is
  0.354 versus 0.856 for large people. Of 2,131 misses, 1,531 are below
  confidence and 569 are localization/no-overlap errors.

At 416 px:

- Smoke negative-image false-alarm rate rises to 5.25%, with 568 false-positive
  boxes at the recall-oriented threshold.
- Fire negative-image false-alarm rate is 1.79%; small-fire recall is 0.848.
- Person negative-image false-alarm rate is 9.79%. Small-person recall drops to
  0.181 and 2,772 person boxes are missed.

Visual galleries confirm that person misses are dominated by small or crowded
people. Frequent person false positives include animals, statues, dolls and
human-shaped objects. Hazard galleries include genuine small/dark misses and
annotation/localization disagreements where predicted and reference regions
partition the same plume or flame differently.

## Limitations

The hazard sources include outdoor, staged and synthetic images. COCO person is
also mixed-domain. These reports are source-scoped diagnostics, not a verified
pure-indoor holdout. Raspberry Pi latency, memory and camera behavior remain
unknown until hardware is available.

## Artifact location

All machine-readable reports and galleries remain outside Git at:

`E:\HomeAssistantPi4\reports\indoor-yolo26n-v2-evaluation`
