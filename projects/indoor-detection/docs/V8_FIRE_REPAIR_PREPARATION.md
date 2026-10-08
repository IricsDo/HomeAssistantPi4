# V8 fire repair: preparation and handover

Owner: OpenAI Codex. Updated 2026-10-09.
Status: **READY_FOR_REVIEW; data PASS_WITH_LIMITATIONS; resource PASS**.
The user authorized the 185-image audit, derivative, gates and bounded preparation.
**Stop before training.** No optimizer step, epoch, new run or holdout prediction.
V7 remains NO_RELEASE; this preparation does not establish better model quality.

## Frozen evidence

- Report: `E:/HomeAssistantPi4/reports/indoor-fire-train-repair-audit-v1`.
- Dataset: `E:/HomeAssistantPi4/processed/indoor-partial-joint-v5-fire-repaired`.
- Frozen253-file `artifact-manifest.json` SHA256:
  `a55301eff85190d3cf9a164747a3ff0e340333b0bdab6ca15ab9b217142f1eb9`.
- `dataset.yaml` SHA256:
  `fd2cbd3dc90d36ed83fedd9451dd270957acf74a091f8db7495aa614c71fac77`.
- Scope SHA256:
  `844e903c8a54db928caa65e66acd736d696a432ab2e7984c5606d9e9c9158910`.
- Review SHA256:
  `c8277d9e83d7722f8e9027337a44cdb140f2385fb807e791fe8365733ad4138b`.
- Derivative `current-bindings.json` SHA256:
  `7a89e9a63726ac66c2928db9aa8e3724776963d2f838a4b62cb15878760cae70`.
- Frozen E: config `frozen-train-config.yaml` SHA256:
  `d2b780459be2538ade69f470280c3e699c8196b91ff5ced0374c42841d8506a7`.
  Its frozen bytes are authoritative across Git autocrlf checkouts.

Do not rerun report-generation recipes in this frozen directory. Any fresh probe
or reproduction writes to a new directory. Original v4 images, labels, manifests,
v7 evidence and external holdout remain unchanged.

## Audit decisions

Reused the frozen160 IDs plus25 nonoverlapping EXIF additions:185 unique train
images. Viewed all original overview pages before label overlays, with no added
model predictions. Inspected native originals and proposed overlays for all12
manual repairs; inspected native correct-versus-current-coordinate crops for all27
EXIF cases. Per-image decisions, original hashes and evidence paths are recorded.
Some source pixels already contain translucent highlights, watermarks or composites;
these remain source pixels. Earlier error diagnosis means this is not a study with
a reviewer unaware of the model's errors, nor an annotation-error prevalence estimate.

| Action | Images | Treatment |
|---|---:|---|
| Keep |112| Existing labels/scopes retained |
| Replace fire |12| Six missing-fire cases and six incomplete extent/component cases |
| Orient raw EXIF8 |27| Lossless oriented PNG; transform all class corners; remove residual EXIF |
| Unknown fire |34| Preserve images and known smoke; remove56 uncertain fire rows from this derivative |

Changes: FS10 manual repairs/14 unknown scopes; home2 manual repairs/20 unknown
scopes/27 EXIF repairs. There are73 derivative image/label pairs. Manual repair
adds a net11 fire boxes; masking removes56, so fire count5549 →5504. Original rows
remain in source files and before/after receipts. No model box was adopted as GT.

Policy: manually repaired boxes enclose visible flame regions; spatially separate
regions have separate envelopes, and a dense connected fire front may use one
envelope. Existing source grouping is retained where visually defensible. This
does not standardize every source annotation. Uncertain ember/spark/flame identity,
occlusion, saturation or incomplete grouping becomes unknown fire supervision.
It does not certify the image as fire-negative. No size/confidence/blur cutoff
removes an image or genuine small flame.

Smoke rows/scopes are retained; this task is not an exhaustive smoke reannotation.
Person remains outside these hazard-source scopes. All previous person rehearsal
and all dataset members remain present. Unknown-fire images participate through
the existing class-masked loss with smoke known and fire/person unknown.

## Data gates and benchmark integrity

`data-gate.json`: PASS_WITH_LIMITATIONS; `readiness.json`: READY_FOR_REVIEW.
The generic scoped auditor intentionally leaves its standalone visual field
PENDING and training_allowed=false. Final review and conversion evidence are in
the separate data-gate receipt; no generic audit result was rewritten to PASS.

- Full scoped audit:24,100 images;15,502 train/4,301 val/4,297 test; zero corrupt,
  missing/invalid/out-of-scope labels, path overlap or exact-file duplicate groups.
- Original48,465 image/label/scope and frozen diagnosis/validation bindings verified.
  Original split memberships also match the frozen v4 binding records.
- Validation/test indexes are byte-identical; their images, labels, scopes and
  distributions are unchanged. Training lineage order is preserved, including54
  previously appended person examples.
- EXIF27/27 decoded-pixel parity PASS; raw/oriented corner round-trip error at most
  `4.40e-10` pixels. Newly encoded EXIF PNGs have no exact decoded-pixel collision
  against8,598 validation/test images. This is not a new near-duplicate/family-
  independence claim; previous family-correlation limitations remain.
- Train smoke4124/person29974 boxes unchanged; fire5504. Known fire scope7866
  images, smoke-only34, person-only7602. Val/test fire1262/1146 unchanged.
- Legacy validation's completeness/EXIF concerns are retained as benchmark
  limitations. Correcting it requires a separately authorized benchmark version
  and paired baseline evaluation; never change it to help a candidate pass.

## One bounded future candidate

Proposal: `configs/train_indoor_v8_fire_repair_proposal.yaml`.
Initialize from frozen v7 best checkpoint SHA256:
`148964125fea8ec42a9620ee0366727d9e814b71e3d9e67490618ad534576158`.
Run name: `indoor_partial_joint_yolo26n_v8_fire_repaired_768` (does not exist).

Retain768/batch8/workers2, maximum12 epochs/patience5, AdamW LR0.00015/lrf0.05,
warmup0.5, seed42/deterministic, scale0.15/translate0.05, all image-mixing0,
uniform sampling and the existing class-masked trainer. No new dependencies.
Continuing optimization is a confound: a future gain cannot prove label repair
alone caused the gain. This small error-enriched repair may not recover fire gates.

Fresh in-memory resource probe: two forward/backward passes with frozen v7 weights,
repaired FS fire, oriented home fire, unknown-fire home image and five dense person
images;299 GT boxes. Loss/gradients finite; allocated AdamW-like moments; no optimizer
step or trainer. Peak allocated1,846,307,328 bytes, reserved2,021,654,528 bytes;
approximately5.28 GB GPU free afterward. Checkpoint hash unchanged, run absent.
This does not measure worker/augmentation peaks, epoch stability or Pi performance.

Future validation protocol and gates remain unchanged: exact square768, rect=false,
IoU0.5 greedy matching, candidate floor0.001/max_det100, unscored warmup. Calibrate
on unchanged validation only. Smoke recall>=0.90; fire recall>=0.90 separately for
FS and home; person F1>=0.65/recall>=0.60. Preserve frozen v6 precision and negative-
alarm guardrails (maximum absolute deterioration0.01) and full metrics/size slices.
No newly excluded small people or relabeled validation examples. Holdout opens once
only after acceptance and candidate lock. Old final test remains closed.

## Corrections and validation

- Gallery `_draw_example` now applies EXIF transpose, matching OpenCV's prediction
  frame. Regression tests cover orientations1/3/6/8 and OpenCV pixels. No historical
  metrics or frozen galleries were recomputed.
- Initial gallery assembly used a Windows backslash path in a slash replacement;
  failed before intake creation, then corrected to as_posix. No source changes.
- Initial verification compared remapped sorted helper lists, then raw indexes
  exposed an actual builder order defect: appended person entries were reordered.
  Fixed builder to preserve original index order, added a regression test, corrected
  only the unfrozen derivative train index with before/after receipt. Resolved audit
  membership and resource-probe members were identical; no inference/training retry.
  Failures and prior index bytes retained in the frozen report.
- Initial lint caught our scratch recipes and one test line/import; corrected and
  moved only our scratch recipes to E. Prior untracked source file untouched.
- Final tests:210/210 PASS6.15s; Ruff PASS; pip check PASS. Build not applicable;
  typecheck not configured.

## Next agent

1. Read current AGENTS/CLAUDE/README/CHANGES/PROJECT_PLAN and this document;
   inspect Git and preserve unrelated untracked source_box_review.py SHA256
   `2672f80a9b1fd3fd3fed9b41f8e82967f089d30f9bced9f91f725aadfeae1df6`.
2. Stop at this train-ready milestone until a later explicit launch request.
3. When authorized, verify253 frozen artifact hashes, all current dataset bindings,
   v7 checkpoint hash, frozen config and run absence. Recheck C: venv, GPU/free disk
   and fresh resources in a new E: report directory. Never overwrite old probe reports.
4. Launch exactly one v8 using the frozen E: config and existing indoor-train CLI.
   Record start/status/logs; stop on error/OOM, no automatic retry series.
5. Evaluate/calibrate unchanged validation and apply all gates. On failure record
   NO_RELEASE and keep holdout/export closed; do not tune on old test.

Large data/reports remain on E, venv on C. Never read, print or commit projects/.env.
