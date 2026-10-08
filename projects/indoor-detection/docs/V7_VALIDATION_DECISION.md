# V7 square validation and decision

Owner: OpenAI Codex. Updated2026-10-08.
Status: COMPLETED evaluation; **NO_RELEASE**. No background job remains.
Training completed12/12 epochs, exit0 at22:33:27 Asia/Saigon. Evaluation uses
inline scoped `best.pt`; no alternate epoch selection or further training.

Report root: `E:/HomeAssistantPi4/reports/indoor-v7-validation-v1`.
Frozen readiness protocol:
`E:/HomeAssistantPi4/reports/indoor-v7-readiness-final-v1/evaluation-protocol.json`,
SHA `b4de1b89b106b0a389972c9b52883afa659e3ba4fa4377797ca9626bc85e5293`.
Selected checkpoint SHA
`148964125fea8ec42a9620ee0366727d9e814b71e3d9e67490618ad534576158`.

## Evaluation contract

- Existing joint-v4 validation only; class scopes remain authoritative.
- Exact square768, `rect=False`, batch8, candidate confidence.001, max_det100,
  greedy matching IoU.5; one unscored warmup before each extraction.
- Reuse existing square class-scoped validator, error analysis, empirical recall
  calibration, explicit matcher and projected size diagnostics.
- Fire: highest global observed threshold satisfying aggregate and each positive
  validation source recall>=.90. Smoke: highest global threshold reaching.90.
  Per-source curves determine the one global fire threshold; no runtime source
  threshold or holdout-based choice.
- Person: maximum interpolated validation F1, then authoritative explicit matching
  at that threshold. Both F1>=.65 and recall>=.60 remain required.
- Hazard precision drop<=.01 and verified negative-image alarm increase<=.01
  relative to frozen v6 points; person alarm increase<=.01.
- Fresh fixed-threshold v6 extraction uses identical batch8/square preprocessing
  and image/GT membership. Historical reference used batch16; report any numerical
  differences and retain the frozen-reference guardrails as well.
- All boxes retained, including tiny persons and blurred smoke. Source-directory
  names are provenance proxies; these results do not establish pure indoor or Pi
  performance. No old-test or external-holdout inference is performed here.

51,501 frozen bindings verified before inference. Source data, training config,
v6 checkpoint, previous reports and unrelated untracked source_box_review.py stay
unchanged. E: stores all reports/weights/data; the Python venv remains on C:.

## Authoritative results

Finished22:55:29 Asia/Saigon, exit0. No evaluation errors or automatic retry.
Independent finalization retains both fresh identical-batch and historical frozen
guardrails. Final decision is in `final-decision.json`; `summary.json` is the
original workflow result. Raw reports and frozen references are preserved.

| Class | Global threshold | TP / FP / FN | Precision | Recall | F1 | Gate |
|---|---:|---:|---:|---:|---:|---|
| smoke | .2655713260 | 773 / 132 / 85 | .854144 | .900932 | .876914 | PASS |
| fire | .2048617601 | 1175 / 203 / 87 | .852685 | .931062 | .890152 | FAIL precision guardrail |
| person | .3423423423 | 3218 / 1076 / 2117 | .749418 | .603187 | .668398 | PASS |

Person interpolated F1/recall.668189/.602528 also PASS. These are validation
results after calibration, not independent-holdout or deployment acceptance.
Smoke source recall: FS222/241=.921162; home551/617=.893031. Frozen validation
protocol requires smoke aggregate recall; each-source hazard recall remains a
separate requirement of any future external-holdout acceptance. No gate changed.

| Class | Verified negative alarms / images | Rate | Change vs frozen v6 |
|---|---:|---:|---:|
| smoke | 16 / 990 | 1.6162% | -1.5152 percentage points |
| fire | 10 / 616 | 1.6234% | -.4870 percentage points |
| person | 118 / 1154 | 10.2253% | -3.1196 percentage points |

Smoke precision improves6.8575points. Person precision/F1 improve, while recall
falls from frozen v6.621743 to.603187; the pass margin is small. Do not interpret
F1 improvement as improved recall at all sizes.

### Fire global-threshold constraint

At an aggregate-only recall threshold.4659981, fire P/R=.932677/.900158. That
point does not meet each-source recall and cannot be selected for acceptance.
The limiting source requires threshold<=.2048618:

| Fire source | TP / FP / FN | Precision | Recall |
|---|---:|---:|---:|
| indoor-fs-v2 | 270 / 55 / 29 | .830769 | .903010 |
| indoor-home-fire-v2 | 905 / 148 / 58 | .859449 | .939772 |

At the selected global threshold precision falls3.3430percentage points vs frozen
v6.886115; allowed drop is1point (minimum acceptable precision.876115).
All observed confidence points at or below the source-recall cap were inspected
from the existing candidate curve: their highest aggregate precision is.852685,
still below.876115. Higher thresholds fail the limiting source recall. This
rules out a confidence-only solution for this checkpoint, candidate extraction
and fixed matching protocol; it is not a claim about all possible models.
No alternative candidate was selected and no additional predictions were run.

Fresh batch8 v6 versus frozen batch16 reference precision differences are
smoke+.000799, fire-.000089, person+.000284; negative rates are identical.
The decision is unchanged under both comparisons; no numerical tolerance added.

### Person size diagnostics

No size filtering. Fixed512 projected height strata are disjoint:
<16px47/512 recalled (9.18%);16–<32px271/827 (32.77%);
32–<64px620/1126 (55.06%);64–<128px832/1167 (71.29%);
>=128px1448/1703 (85.03%). Both sides<=12px17/303 (5.61%).
At native768 both sides<=12px2/113 (1.77%). Sizes are continuous letterbox
projections before rounding, not actual camera-distance measurements. The
current room/doorway scope does not authorize removing tiny labels.

## Decision and next work

**NO_RELEASE**. External1403-image holdout remains unopened; old test stays
closed. No NCNN export, deployment, new training or automatic retry.

Next design work must use training/validation evidence: distinguish limiting
source fire misses from extra detections on the other source, inspect annotation
conventions and source/domain coverage, then propose one bounded intervention
with data/resource gates and unchanged acceptance criteria before another run.
Longer training is not established as a remedy by these results. Preserve the
experimental holdout for a future validation-accepted candidate; do not use it
to choose new data, thresholds, ROI, object-size limits or epochs.
Original30-independent-group/300fire coverage and Pi/camera evidence remain
incomplete even if a future experimental holdout passes.

Frozen160-file artifact manifest SHA:
`ae5b0cd66f7531ed2bb84bf4d5d73b8e5bf7a0ec13d0f54765b627ea83344587`.
Validation policy SHA:
`d336812aa4fb11a193f6ae1dc8c8d15ed322e9bc6d7f2b5383b5f04b95effc69`.

## Validation commands

Tests:192/192 PASS8.03s using `.venv/Scripts/python.exe -m pytest
-p no:cacheprovider --basetemp C:/Users/Public/Documents/indoor-v7-validation-20261008`.
Ruff `check . --no-cache`:PASS. `pip check`:PASS. Build not applicable;
typecheck not configured. No implementation/dependency/config changes.
