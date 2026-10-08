# Fire diagnosis after v7 and next intervention design

Owner: OpenAI Codex. Updated2026-10-08.
Status: **COMPLETED diagnosis; PLANNED intervention, not train-ready**.
User requested train/validation error analysis and intervention design.
V7 remains NO_RELEASE; this task authorizes diagnosis/design, not another run.

Evidence root: `E:/HomeAssistantPi4/reports/indoor-v7-fire-diagnosis-v1`.
Frozen104-file manifest SHA:
`41849078dd6d257671853094be12038636c30bb891cba8b2277c8d145e0532f1`.
Previous v7 validation evidence and all original images/labels stay unchanged.

## What was measured

- Reused frozen v7 validation candidates, no new validation prediction call.
- One successful train extraction:7,900 fire-scoped images,768 square/batch8,
  conf floor.001/max_det100/IoU.5/unscored warmup. Started23:06:14, finished
  23:08:52 Asia/Saigon, exit0. This was inference, not training.
- Two previously declared diagnostic thresholds:.2048617601 (source gate) and
  .4659980536 (aggregate-only). Neither is a new deployment candidate.
- Reviewed66 error/control entries covering57 unique images:31 train/26 val.
  Two ranked plus two seeded random examples per error stratum, two train matched
  controls/source. Error-enriched selection is not an annotation-error prevalence
  estimate. Uncertainty and per-image hashes are retained in `visual-review.json`.
- Verified15,801 train image/label/scope bindings against frozen joint-v4 evidence.
  Prior untracked source_box_review.py hash unchanged. No test/holdout predictions.

## Quantitative findings

### Confidence/source gap is present on training data

| Threshold | Split/source | TP / FP / FN | Precision | Recall |
|---|---|---:|---:|---:|
| .466 | train FS | 2164 / 130 / 407 | .943330 | .841696 |
| .466 | train home | 2857 / 60 / 121 | .979431 | .959369 |
| .466 | val FS | 255 / 26 / 44 | .907473 | .852843 |
| .466 | val home | 881 / 56 / 82 | .940235 | .914849 |
| .205 | train FS | 2372 / 544 / 199 | .813443 | .922598 |
| .205 | train home | 2900 / 265 / 78 | .916272 | .973808 |
| .205 | val FS | 270 / 55 / 29 | .830769 | .903010 |
| .205 | val home | 905 / 148 / 58 | .859449 | .939772 |

At the higher threshold FS training misses370 boxes with an IoU-qualified
candidate below confidence,36 with inadequate overlap and1 with no candidate.
At the lower threshold those counts are162/36/1. Home lower-threshold train
misses19/58/1. This supports investigating supervision/confidence and geometry;
it does not prove a specific cause or establish that more epochs cannot help.

Lowering the shared validation threshold gains39 TP while adding121 FP.
191/203 low-threshold FP boxes occur on positive images;12 on images annotated
fire-negative. The latter are *annotation-based negatives*, not all visually
verified true negatives.

| Low-threshold validation unmatched prediction geometry | FS | home | Total |
|---|---:|---:|---:|
| IoU>=.5 with some GT, extra assignment/duplicate | 3 | 39 | 42 |
| >=80% inside GT, IoU<.5 | 19 | 39 | 58 |
| Partial overlap, IoU .1–<.5 | 25 | 46 | 71 |
| Positive image, best IoU<.1 | 5 | 15 | 20 |
| Annotated negative image | 3 | 9 | 12 |

171/203 FP boxes overlap GT or duplicate an assignment. These are geometric
categories, not171 proven label errors. A smaller flame prediction can be wrong,
or the reference extent can be inconsistent; original pixels decide that.

### Direct visual evidence

- `train-005` and `train-006`: visible roof/ground flames, but label files contain
  only class0(smoke). `val-006` shows the same completeness problem on burning
  wood. These are counterexamples to assuming every scoped fire-negative is true.
- `val-002`/`val-012`: one GT encloses two flame regions, separate predictions
  receive inadequate IoU. `train-014`: several component boxes along a plume.
  `val-003` uses a broad fireplace/log extent; its prediction is flame-focused.
  These support a granularity/extent audit, not wholesale automatic relabeling.
- Real model mistakes also remain: bright windows, red/white extinguisher features,
  clothing/equipment, candle stems included in flame boxes, and tiny candle misses.
  Uncertain ember/low-light examples are not approved hard negatives.
- Repeated room-fire families appear in train and val galleries. Family correlation
  must be recorded before weighting examples; no frame-independent or newly proven
  train/val leakage claim is made from visual resemblance alone.

## EXIF coordinate problem

Fire-scoped metadata census finds EXIF orientation8 in27 train and3 val images,
all home source; FS has none. PIL raw raster is720x1280 while cv2/EXIF-oriented
decoding is1280x720. Existing gallery `_draw_example` opens PIL without applying
EXIF, while `_image_stats` and inference use OpenCV-oriented coordinates.
Thus untransposed EXIF galleries cannot adjudicate geometry reliably.

For `train_522.jpg`, raw-normalized GT rotated with EXIF covers the actual flame;
current normalized GT applied directly to the oriented dimensions lands on an
empty doorway. `exif-train-522-comparison.jpg` and JSON show the two coordinates.
This is a confirmed coordinate mismatch for this example. The other29 flagged
images still require native-coordinate review before any blanket transformation.
Their metadata count does not mean30 individually confirmed annotation defects.

Historical metrics still describe the unchanged dataset/evaluation. No result
was recomputed after dropping or repairing labels. This small home-source subset
does not explain the FS confidence gap by itself.

## Proposed intervention: audited training data repair

Choose a **data-quality intervention first**, with current model, resolution,
loss, uniform sampling and optimizer conventions retained. The intended change
is verified training image-coordinate/annotation/scope repair in a new derivative.
Its expected benefit is a hypothesis, not a guaranteed gate recovery.

### Frozen audit intake (ready for the next task)

`train-fire-audit-160.json`, seed81,160 unique train images:

- All34 annotated-negative alarm images:11 FS/23 home.
- 32 positive images with extra boxes per source (64).
- 15 below-confidence positive images per source (30).
- 16 random annotated-negative controls per source (32).

Add all27 EXIF-flagged training images;2 already occur in the pilot, so the union
is **185 unique training images**. All IDs/image/label hashes are fixed. The3 val
EXIF cases are diagnostic evidence only; they never enter this training intake.
Pilot audit status is PENDING, `training_allowed=false`;66 diagnostic entries
above do not constitute final repair approval for the185-image intake.

### Execution checklist before another model run

1. Review185 original images/labels with consistent EXIF rendering. Hide model
   overlays during ground-truth judgement, then compare errors. Record each
   class's completeness, connected-vs-separated flame grouping and box extent.
   Prioritize ready-made annotations; only confirmed repairs need new boxes.
2. Define and record source annotation conventions before conversion. Confirm
   missing fire, label geometry, true confuser or uncertainty. Predictions never
   become GT automatically; no confidence/size cutoff deletes genuine fire.
3. For verified raw-coordinate EXIF cases, create oriented pixel derivatives and
   transform **all class boxes** through the same corner mapping. Preserve source
   bytes/labels, class IDs and scope. Round-trip/parity and native-overlay checks
   are mandatory; strip residual EXIF only in the new derivative.
4. Correct confirmed training-only fire defects with before/after receipts.
   Where fire completeness cannot be resolved, use the existing unknown-class
   scope mechanism under its audit rules. Keep known smoke/person supervision.
   Only visually confirmed negatives remain eligible as fire-negative examples.
5. Build a new joint derivative on E:. Preserve full validation/test memberships
   and labels, all person/hazard rehearsal, unique indexes and frozen holdout.
   Audit geometry, class scopes, duplicate conflicts and per-source distributions.
   No extra weighting or source expansion in the first data-repair candidate.
6. Fix/test gallery orientation consistency as a separate small implementation
   change before using galleries for approval. It must not silently alter metrics.
7. Freeze data-gate/resource/config/checkpoint receipts. Proposed future run is
   one new768/batch8 bounded continuation from frozen v7 best, max12/patience5,
   existing AdamW/LR/class masking/mixing0; no YAML or run created in this task.
   Continued optimization is a confound; improvement would not prove a causal
   isolated effect of label repair. Launch requires a later explicit authorization.
8. Apply the same validation gates, source-recall and precision/alarm guardrails
   against frozen v6. Lock only after acceptance, then open experimental holdout
   once. Stop on error/OOM/gate failure; no automatic retry series.

### Benchmark integrity

Legacy validation has documented label/completeness/EXIF concerns. Keep it intact
as a continuity benchmark; uncertain reference labels limit interpretation.
Any future validation correction requires an explicit new benchmark version,
published change receipts, and paired v6/v7 evaluation under one protocol before
using it for selection. Never remove difficult cases or tune labels to predictions.
This design does not authorize changing validation or reopening old test/holdout.
External1403-image coverage and actual Pi/camera limitations remain unchanged.

## Validation and reporting issues

Tests192/192 PASS6.39s; Ruff PASS; pip check PASS. Build not applicable,
typecheck not configured. Repository implementation/dependencies unchanged.
Initial reporting assembly used an incorrect label path; `diagnose_v2.py` reuses
the existing helper and writes separate output. An early train-report read preceded
extraction completion; reporting completed after successful extraction. Both issues
are retained; no model-inference retry or source rewrite occurred.
