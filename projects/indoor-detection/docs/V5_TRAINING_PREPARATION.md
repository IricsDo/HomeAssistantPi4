# V5 preparation — stop before training

> Historical preparation snapshot. The user subsequently requested continuation;
> v5 training/evaluation are now complete. Current decision and next task:
> [V5 evaluation](V5_EVALUATION_DECISION.md). Do not relaunch the completed run.

Owner: **OpenAI Codex**. Status: **READY_FOR_REVIEW** (2026-10-05).
The user explicitly requested continuation through preparation, then a stop.
**No v5 training has started; do not start it without a subsequent user request.**

## Intervention and data gate

New scoped index: `E:/HomeAssistantPi4/processed/indoor-partial-joint-v3/dataset.yaml`.
Reports: `E:/HomeAssistantPi4/reports/indoor-partial-joint-v3-audit`.
Data gate: `data-gate.json`, `PASS_WITH_LIMITATIONS`, `training_allowed=true`
for a bounded class-masked experiment. This is not model/deployment approval.

| Split | Images | Smoke boxes | Fire boxes | Person boxes |
|---|---:|---:|---:|---:|
| train | 15,448 | 4,124 | 5,549 | 29,421 |
| validation | 4,301 | 858 | 1,262 | 5,335 |
| test | 4,297 | 968 | 1,146 | 5,442 |

- Preserve all v2 images, labels and scopes; append **548 person training images /
  5,810 boxes**: 49 individually accepted pilot images +499 expansion images.
- Expansion's fixed 30-image sample: 29 ACCEPT / 1 EXCLUDE (gallery 292 athletics
  photomontage). Domains: 19 outdoor /10 indoor /1 composite, sample counts only.
  Five original-resolution head/context crops resolve ambiguous cases 60, 194, 264,
  278, 353. Case 278 is a child held by a man, not a repeated person assignment.
- No new systematic box/completeness problem found in this sample. The remaining
  **470 images were automatically screened, not individually visually certified**.
  Graphic content or label omissions can remain; no whole-source certification.
- Existing source annotations only, vbox clipped then normalized as YOLO class2.
  All 548 image/label hashes and 5,810 normalized boxes reverified against source
  coordinates (tolerance 5.1e-9). Six converted overlays actually inspected:
  15,149,194,278,353,360. Originals/source labels remain unchanged.
- All 24,046 joint images/labels audited: zero structure errors, exact duplicates,
  cross-split groups, annotation conflicts or scope conflicts. Expansion near
  screen against corpus+pilot: 22 candidates reviewed, all unrelated scenes.
  dHash is not exhaustive for crops, mirrors, edits or same-session images.
- Train scope: 7,900 hazard images +7,548 person images. All hazard rehearsal
  retained; unknown classes remain masked. No error-mined sampling/reweighting.
  Earlier 42/56 box review and optional sampling are preserved, not prerequisites
  for this new-data intervention.
- Holdout index files are byte-identical to v2; all original path/scopes preserved.
  Base visual gate is inherited with mixed indoor/outdoor/staged/synthetic limits.
  No new test predictions, metrics, threshold or epoch selection.
- Original CrowdHuman noncommercial terms/provenance remain applicable. No image
  redistribution or claim of camera/Pi validation. Camera mounting is undetermined.

## Frozen experiment preparation

Config: `configs/train_indoor_v5_512.yaml`.
Readiness snapshot: `E:/HomeAssistantPi4/reports/indoor-partial-joint-v3-audit/train-readiness.json`.

- Initialize from v2 `best.pt`: explicit person F1 at 512 is 0.6351 versus v4's
  0.6292; v4 recall is higher. V2 avoids additional v3/v4 continuation history,
  but restarting alone is not expected or claimed to fix the gate. The intervention
  is additional labelled person data. This is not a pure single-variable ablation.
- 512 px, maximum 12 epochs, patience 5, AdamW, LR 0.00015, seed 42, deterministic.
  Scale 0.15, translate 0.05; mosaic/mixup/cutmix/copy_paste remain 0. No custom sampler.
- Use the existing ClassScopedDetectionTrainer and authoritative scoped validator.
- Target run: `E:/HomeAssistantPi4/runs/indoor-detection/indoor_partial_joint_yolo26n_v5_crowdhuman_512`.
  `exist_ok=false`; run directory does not exist. No runs/checkpoints overwritten.
- GPU availability confirmed: RTX 5070 Laptop GPU, 8,518,041,600 bytes;
  torch 2.14.0+cu130 / Ultralytics 8.4.163. Checkpoint loads on CPU with canonical
  smoke=0/fire=1/person=2 names. No train method or inference called during preparation.

Read-only preparation verification (safe to run now):

```powershell
.venv/Scripts/python.exe -m indoor_detection.crowdhuman_intake `
  --readiness E:/HomeAssistantPi4/reports/indoor-partial-joint-v3-audit/train-readiness.json
```

It verifies config/checkpoint/data gate/evidence hashes, safe augmentation options
and unused run path. It always reports `training_started=false` and does not
authorize execution. A changed file must be investigated; do not rewrite hashes
just to bypass the check. It is a preparation snapshot, not continuous monitoring
of every underlying image/label. Reaudit changed data before a future run.

After the user asks to resume training, recheck Git, readiness and GPU. Only then:

```powershell
.venv/Scripts/python.exe -m indoor_detection.train --config configs/train_indoor_v5_512.yaml
```

After that bounded run, calibrate/scoped-evaluate on validation at 512, including
hazards, tiny-person recall and false alarms. Person requires F1>=0.65 and
recall>=0.60; smoke/fire recall>=0.90. No gate reductions. Keep test closed during
selection; disclose historical v2 test use. No NCNN release until quality approval.

## Artifact locks

| Artifact | SHA-256 |
|---|---|
| expansion review-final-v1.json | 55bc4c297386c29201f7a101a9331cc9cdcf16c13734d2eec0ded49d85574d7e |
| expansion derivative manifest.json | 5723769c40c35860d921be3ca79667419465dd87812c7a3a4c14b6812f8ce50c |
| joint dataset.yaml | d989c53dd84cfa9e73d92efbc2b55e5fe98729b35eefa6f6ad0e880b854abf42 |
| joint class_scope_manifest.json | 4b5e1b01f6ff2bd9cf3e23b7ca7e3c7a893f9fde487be74dbd06ffb796f035e1 |
| joint manifest.json | 9ddaecbd19084e94e80a7ec0aa62e5078116c1b45b16dfdb71e38b96291d81a8 |
| index-audit.json | 0609a849fe6f25850d0f6cc3842e814c574e15f709a011765610bdcf42384b6b |
| conversion-consistency.json | c06c2a45d521245cfb0abfbdef00886c0687e8f78732718abc2a45710645b43e |
| data-gate.json | 2ae00e2ee438390d50584af91b7ad5ebcc63c662955504c6e353fb2b51a3edbd |
| train-readiness.json | a0c3ec57f04dbc4efe17938a550979729f8abf8bbd0a1498a828434fb612f4b2 |
| v2 initialization checkpoint | 59dbfedb2f1fb79e1a9ad3ce584a1d1b85ae30b93bf5ca6d0f238f5cf20596b3 |
| v5 config current file bytes | 1ac35d97c782f03a79c4e3fa47d2397bbd48f9fb67f80bc8014e2c1e159851ae |

Index hashes: train `9a3292536fffb49f72729dc8ff11a23767f6abae7d88f810177d6ec9a0b2b3df`;
val `bd6edaeb329efa5cb86d4e904f4a90b49072118fbfe388bc652bbbdd1de8f182`;
test `4d37f4aeb2dfb212adda2aeff60748935a283a03f6074d55cca10376367f8180`.
Config byte hash can differ after a Git line-ending conversion; review the actual
diff/content and refresh a separate readiness snapshot if needed, without changing
the original evidence. No large artifacts or secrets committed.
