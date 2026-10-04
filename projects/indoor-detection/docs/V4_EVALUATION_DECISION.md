# YOLO26n v4 evaluation and deployment decision

## Decision

The 512 px fine-tune completed, but person remains below the required validation
F1 >= 0.65 and recall >= 0.60. Keep NCNN export closed. V4 is an experimental
checkpoint; its small aggregate improvement does not establish deployment readiness.
Test was not reopened for epoch or threshold selection.

## Training and checkpoint

The run completed 12 epochs in 0.854 hours. Epoch 11 recorded the highest
validation mAP50-95 (0.54568). Separate class-scoped evaluation with batch 20
reloaded best.pt and obtained mAP50/mAP50-95 0.82649/0.54660. Small differences
from inline evaluation with batch 40 are recorded rather than treated as new training.

Run: `E:\HomeAssistantPi4\runs\indoor-detection\indoor_partial_joint_yolo26n_v4_512`

Best checkpoint SHA-256:
`bee9971938d8a213b294751fa39d6af7cf41b63e0e214bcff9ba94a4de708a22`

Last checkpoint SHA-256:
`89aac2d9f8a0f1d3b26e3c2fa9ccc1084d49a3516d3b3b312e441a1382486601`

## Calibration at 512 px

These rows use interpolated validation curves. Error-analysis metrics use
explicit matching at IoU 0.50 and are reported separately below.

| Class | Selection | Threshold | Precision | Recall | F1 | Recall/quality gate |
|---|---|---:|---:|---:|---:|---|
| smoke | recall >= 0.90 | 0.176176 | 0.8513 | 0.9009 | 0.8754 | PASS |
| fire | recall >= 0.90 | 0.392392 | 0.9176 | 0.9000 | 0.9087 | PASS |
| person | maximum F1 | 0.297297 | 0.7305 | 0.5625 | 0.6356 | FAIL |

## Person error analysis

At the selected threshold, explicit matching gives precision 0.7190, recall
0.5593 and F1 0.6292: 2,984 true positives, 1,166 false positives and 2,351
false negatives. Negative-image false alarms affect 169/1,154 images (14.64%).

Recall is 0.8467 for large people, 0.6502 for medium people and 0.2907 for
people occupying less than 1% of the image. Misses include 1,515 below-confidence
boxes, 806 localization/no-overlap errors, 29 assignment errors and one absent
candidate. Contact sheets still show distant/crowded people and false alarms
on animals, statues, dolls and household objects. These galleries are selected
error examples, not a representative estimate of indoor performance.

## Hazard error analysis

Smoke explicit matching gives P/R/F1 0.8340/0.9138/0.8721, with 784 true
positives, 156 false positives and 74 misses. Negative-image false alarms are
12/990 (1.21%). Blurred-smoke recall is 75/86 (0.8721); blur remains eligible.

Fire explicit matching gives P/R/F1 0.9159/0.9065/0.9112, with 1,144 true
positives, 105 false positives and 118 misses. Negative-image false alarms are
8/616 (1.30%).

The authoritative error reports use `rect=False` (square 512 inputs) and an
unscored warmup image. Older reports retain the previous automatic rectangular
padding policy. A batch-1 diagnostic changed fire recall to 0.8946 under that
old policy; batch composition can change padding, so those reports must not
be mixed with the square reports. Cold-start NMS time-limit warnings occurred
in the old fire diagnostics; the new warmup precedes all scored images.

## V2 control at 512 px

V2 calibration gives smoke threshold 0.166166 (P/R 0.8437/0.9000), fire
threshold 0.305305 (0.9029/0.9002) and person threshold 0.283283
(P/R/F1 0.7594/0.5410/0.6318). Person explicit square matching gives
0.7644/0.5432/0.6351, with 2,898 true positives, 893 false positives and 2,437
misses. Negative-image false alarms are 11.61%; small-person recall is 0.2530.
V2 was not audited again for hazards because the person gate already fails.

| Square matching at 512 | Person F1 | Person recall | Small-person recall | Negative-image false alarms |
|---|---:|---:|---:|---:|
| V2 control | 0.6351 | 0.5432 | 0.2530 | 11.61% |
| V4 | 0.6292 | 0.5593 | 0.2907 | 14.64% |

Neither checkpoint passes. V4 improves small-person recall but loses precision;
the control does not support claiming that restarting from v2 alone fixes the
512 px gate. Move to training-only error mining before another fine-tune.

Control reports: `E:\HomeAssistantPi4\reports\indoor-yolo26n-v2-512-control`.

## Training-only mining

V4 was run on all 7,000 training images with person annotation scope. This is
mining on data already seen in training, not an independent quality estimate.
It finds 7,624 missed person boxes, including 6,454 small boxes, and predictions
on 41/1,000 annotated-negative images. Training small-person recall is 0.4049.
Gallery review confirms distant/crowded people and object/animal/sign false alarms.
Possible annotation ambiguities require full-resolution review before any
negative candidate is accepted.

Artifacts: `E:\HomeAssistantPi4\reports\indoor-person-train-mining-v1`.
`review-queue.json` contains 64 images ranked by small missed-box count and all
41 negative images with predictions. Every row is REVIEW_REQUIRED with a null
decision. No source label, dataset index or training configuration was changed.
Validation/test images are excluded by selecting the train split before mining.

## Next steps

1. Review the 105 queued training examples at full resolution. Review small
   or crowded missed people and high-confidence false alarms on negative images.
   Use validation only for evaluation; do not add its error examples to training.
2. Build a reviewed training intervention with explicit annotation scope and
   provenance. Retain source images/labels, freeze validation/test, and repeat
   structural, annotation and cross-split duplicate gates before training.
3. Lock a checkpoint and thresholds only after all validation gates pass, then
   export NCNN and check output parity. Pi latency and camera validation require
   the physical hardware.

The audited dataset remains unchanged and mixed-domain. Reports must not be
presented as a verified pure-indoor benchmark.

## Artifacts

Calibration JSON, error reports and galleries:
`E:\HomeAssistantPi4\reports\indoor-yolo26n-v4-evaluation`
