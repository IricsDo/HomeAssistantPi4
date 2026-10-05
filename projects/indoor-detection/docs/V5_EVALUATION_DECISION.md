# V5 bounded experiment and validation decision

Owner: OpenAI Codex. Status: **READY_FOR_REVIEW**, run date 2026-10-05.
The user requested continuation after the preparation stop. Pre-run readiness
and CUDA/GPU checks passed. No deployment approval is implied by starting training.

## Frozen intervention

- Run: `E:/HomeAssistantPi4/runs/indoor-detection/indoor_partial_joint_yolo26n_v5_crowdhuman_512`.
- Reports: `E:/HomeAssistantPi4/reports/indoor-yolo26n-v5-evaluation`.
- Config: `configs/train_indoor_v5_512.yaml`; initialize from frozen v2 best.pt,
  joint v3, 512 px, at most 12 epochs, patience 5, seed 42, AdamW lr0 0.00015.
- New data: 548 images / 5,810 existing person boxes. Retain every original image,
  scope and hazard rehearsal example. Holdout membership unchanged. Uniform
  sampling, class-masked loss/validator, all mixing augmentations disabled.
- Data gate PASS_WITH_LIMITATIONS. Mixed-domain/staged data, annotation
  completeness, 470 unsampled expansion images and near-duplicate limits remain.
  Full preparation hashes and provenance: [V5 preparation](V5_TRAINING_PREPARATION.md).

## Evaluation protocol declared before results

1. Use the run's best.pt selected by inline validation fitness; record the best
   epoch, training termination, resolved batch, duration and checkpoint hashes.
2. Standalone class-scoped validation at 512, GPU 0, batch 20, workers 0. Preserve
   validator's rectangular-padding protocol; report separately from square
   deployment diagnostics. Smoke/fire choose highest interpolated confidence
   with validation recall >=0.90. Person chooses maximum validation F1.
3. At those thresholds run explicit class-scoped error matching on validation:
   512 square (`rect=False`), one unscored warmup image, batch 16, candidate
   confidence 0.001, max_det 100, matching IoU 0.50. Include all three classes,
   small-person recall, false alarms on annotated-negative images and brightness/
   blur buckets. Report source slices as provenance proxies, not indoor domains.
4. Report calibration and explicit matching separately. Person requires both
   F1>=0.65 and recall>=0.60; smoke/fire recall>=0.90. A failure in the authoritative
   square matching closes release, even if another protocol has a favorable metric.
5. Keep test closed during selection. Historical v2 test use is acknowledged;
   this holdout must not be described as never previously used. Only a candidate
   passing validation may be locked before final test. Smoke test regression
   requires a genuinely comparable baseline slice/protocol, not mixed metrics.
6. No automatic series of retries or gate reductions. If the bounded run fails,
   record failure and the next intervention supported by evidence. NCNN export
   remains closed until quality approval; Pi/camera validation requires hardware.

## Results

**NO RELEASE: person still fails at 512 px.** Training and validation evaluation
completed, both exit code 0. No new test evaluation or NCNN export. All jobs ended.

Training completed 12 total epochs (2 original +10 resumed). Patience 5 triggered
at epoch 12, coinciding with the configured cap; resumed console reports ten epochs
in 0.364 hours. Best checkpoint is epoch 7, inline mAP50/mAP50-95
0.82890/0.54678. Standalone scoped validation (batch 20) gives
0.82896490/0.54633065. Inline validation used batch 36; rectangular padding and
batch differences are recorded, not mixed with square matching below.

Best SHA-256: `caa86c04beb2d38d92f9a84d3b3fdc833d056aa5587ec2a5f3407c8d4bcd9fc7`.
Last SHA-256: `8468d30624ed2e18fb5ede304770af48942201ac601af1de3e4f64d84237eccd`.
Each stripped checkpoint is 5,351,557 bytes with canonical names.

CSV time resets on resume. Initial completed segment: 640.927 s; resumed segment:
1,310.270 s; sum 1,951.197 s (32.52 minutes), excluding discarded partial epoch,
restart and initial setup overhead. Do not call the resumed CSV time the whole run.
Full original/resume console logs and training-result.json retain actual evidence.
No training/evaluation traceback or NMS timeout warning found.

### Calibration (interpolated validation curves)

| Class | Selection | Confidence | Precision | Recall | F1 | Gate |
|---|---|---:|---:|---:|---:|---|
| smoke | target recall 0.90 | 0.122122 | 0.8121 | 0.9009 | 0.8542 | PASS |
| fire | target recall 0.90 | 0.357357 | 0.8994 | 0.9002 | 0.8998 | PASS |
| person | maximum F1 | 0.325325 | 0.7379 | 0.5636 | 0.6391 | FAIL |

Standalone per-class mAP50/mAP50-95: smoke 0.92179/0.62350,
fire 0.92718/0.61634, person 0.63792/0.39915. Class confusion plots are under
validation-runs. Validator's reported P/R at its common operating point are not
the class-specific thresholds in the table.

### Authoritative square explicit matching

| Class | Precision | Recall | F1 | TP / FP / FN | Negative images with alarms | Gate |
|---|---:|---:|---:|---|---|---|
| smoke | 0.7686 | 0.9172 | 0.8363 | 787 / 237 / 71 | 24/990 (2.42%) | PASS |
| fire | 0.8995 | 0.9073 | 0.9034 | 1,145 / 128 / 117 | 8/616 (1.30%) | PASS |
| person | 0.7307 | 0.5717 | 0.6415 | 3,050 / 1,124 / 2,285 | 136/1,154 (11.79%) | FAIL |

Person requires F1>=0.65 **and** recall>=0.60; both fail. No candidate lock or
test selection. Smoke's blurred slice remains eligible: 72/86 recalled (0.8372),
versus v4's 75/86. Smoke negative-image alarms rose from v4's 12/990 to 24/990;
passing overall recall does not establish equivalent hazard quality. The separate
same-test-slice smoke regression gate is **unverified**, because test remains closed.

Person recall by box size: large >=5% area 1,442/1,663 (0.8671), medium 1–5%
958/1,415 (0.6770), small <1% 650/2,257 (0.2880). Small boxes account for
1,607/2,285 misses (70.3%). Miss taxonomy: 1,488 below confidence, 770
localization/no-overlap, 27 duplicate/assignment. These diagnostic buckets do
not prove annotation correctness or determine a new threshold from test.

| Validation square 512 control | Person F1 | Recall | Small-person recall | Negative alarms |
|---|---:|---:|---:|---:|
| v2 | 0.6351 | 0.5432 | 0.2530 | 11.61% |
| v4 | 0.6292 | 0.5593 | 0.2907 | 14.64% |
| v5 | 0.6415 | 0.5717 | 0.2880 | 11.79% |

Control reports verified as validation, square 512, one warmup, IoU 0.50,
candidate confidence 0.001/max_det 100. Each threshold was calibrated independently.
V5 improves overall person F1/recall relative to these controls but tiny-person
recall does not improve over v4. Initialization/history and resume differ;
this is not a clean ablation or evidence of a causal data-source effect.

Source provenance slices (not indoor-domain certification): smoke recall
0.9502 on indoor-fs-v2 /0.9044 on indoor-home-fire-v2; fire 0.8963/0.9107.
Person holdout is COCO only (2,501 images). No independent CrowdHuman holdout
or physical Camera Module 3 Wide benchmark was introduced.

Two person contact sheets were viewed (misses and negative alarms), plus original
resolution overlays 001_000000388846 and 018_000000078823. Examples include
tiny distant beach/crowd people and false alarms on a dog, toys, animals and
statues. These are selected errors, not representative domain estimates or
authorization to alter labels. No source annotation or split was changed.

### Next intervention supported by this result

Training-label size census, no model predictions: base COCO has 10,846/23,611
small boxes (45.94%). Added pilot+expansion has **701/5,810** small boxes (12.07%):
82 pilot +619 expansion. Total small training boxes increased only 6.46%, while
all person boxes increased 24.61%. This describes coverage; it does not prove
why the model failed. Current bounded uniform intake did not resolve the gate.

Return to P1 with a labelled, size-stratified intervention. First audit remaining
source annotations for small visible-body coverage and freeze a bounded selection
with box-size/image-density strata and a visual stop condition before downloading.
Do not collect validation/test error images into train. Retain hazard rehearsal,
scope masking, holdout fingerprints and duplicate/annotation gates. Existing
head/body semantics and missing/ignored objects still require intake review.
Predeclare one next experiment and initialization/retention rationale after its
data gate; do not automatically run a series of retries or reduce quality gates.
Optional historical sampling remains unimplemented and is not a prerequisite.

### Reproducibility and reports

`evaluation-workflow.py` on E calls the existing evaluate/analyze_errors APIs
sequentially with the declared settings; SHA-256
`2fadd587b293fcf8f027b63152947a9bb76b6a75f119ed4999fae527fb92007b`.
It ran once after training. Do not rerun into the same nonempty report directory.
Copy/adapt output paths to a new derivative for a reproducibility run.

Artifacts: training-result.json, resume-receipt.json, three *-calibration.json,
three *-square-error-analysis directories, evaluation-summary.json,
person-control-comparison.json, train-person-size-distribution.json and console
logs. Summary binds checkpoint/configured protocol and calibration/error hashes.
Per-image rows, source slices, condition buckets, confusion plots and galleries
remain on E. No weights, image data or secrets are committed.

| Final receipt | SHA-256 |
|---|---|
| artifact-manifest.json (27 bound files) | ba4baa6cb90da56fc4464c19dd40ba160dbe5276b7667cc2f2ad637ae38854c4 |
| evaluation-summary.json | 67a837823dc5737d789165c22160f8b779c00c64731d6ca4b517fb7c85a236fd |
| training-result.json | 99093e5b6a8a3e2e7077c64589b4a3fa9eacce598c5e2aa51f684bbbb8638b50 |
| train-person-size-distribution.json | d6a3e4a9e20abbbf96c198f4eabbc4c3627957c166fbfb9b0318a5b80a1792f9 |

Final tests: 153/153 PASS; Ruff PASS. Data YAML, all indexes and class-scope
manifest hashes rechecked unchanged after training/evaluation. Artifact lock is
a receipt, not proof of real-world camera performance or complete annotation.

## Resource recovery during training

Initial AutoBatch resolved to 18. After two completed epochs, Windows free RAM
fell to 0.76 GB; the eight train/eight validation loader workers contributed
substantial process memory. Epoch 2 checkpoint was CPU-loaded and verified to
contain optimizer state, epoch index 1, batch 18 and total epochs 12. Only the
verified v5 process tree was stopped; a partial epoch 3 was discarded. Free RAM
then increased to 17.27 GB. No other Python job was stopped.

Preserved `resume-epoch2.pt`, original console log and a separate resume receipt/
config/log in the v5 report directory. Resume continues the same run at epoch 3,
workers 2, resolved batch 18, with optimizer and epoch/LR schedule retained.
Original repository config and frozen preparation evidence are unchanged.
Standard resume and changed loader RNG are not bit-identical to uninterrupted
training. Receipt: `resume-receipt.json`; resolved config:
`train-resume-workers2.yaml`; current log: `training-resume-console.log`.

Resume checkpoint SHA-256:
`25fffce3374a929047f08c343696de0168cb505fba53a831ef07b3edde2abc6c`.
