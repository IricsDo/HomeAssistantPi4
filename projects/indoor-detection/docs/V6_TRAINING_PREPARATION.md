# V6 reviewed small-person training preparation

Owner: OpenAI Codex. Preparation completed; execution: **IN_PROGRESS**.
Preparation originally stopped before training. On 2026-10-06 the user explicitly
authorized continuation; the frozen configuration was launched once after fresh
read-only readiness and GPU checks. Historical preparation receipts remain unchanged.
V5 remains NO RELEASE: person F1/recall0.6415/0.5717 below0.65/0.60.

## Data decision and compatibility

The frozen reviewed-only54 proposal is accepted for separate derivatives:
24 COCO original train images/156 boxes and30 CrowdHuman images/397 boxes.
316/553 boxes are small (<1% image area),57.14%. This is a modest addition,
not a prediction of model gain. Automatic expansion remains closed because
metadata-only source eligibility did not reliably establish complete/physical labels.

COCO original bbox clipped uses the base COCO convention; CrowdHuman clipped
visible-body vbox uses the previous548-image convention. Preserve their provenance;
these are person targets, not a claim of identical amodal/full-body extents.
No source labels corrected or generated from model predictions. Original source
annotations/images/licenses and prior ledgers remain unchanged. CrowdHuman
noncommercial policy and per-image COCO license metadata persist; rights were
not newly verified. No source/image redistribution or camera-domain claim.

## Artifacts and gates

All large artifacts are under `E:/HomeAssistantPi4`:

- `processed/coco-reviewed-small-pilot-v1`:24 images/156 boxes.
- `processed/crowdhuman-reviewed-small-pilot-v1`:30 images/397 boxes.
- `processed/indoor-partial-joint-v4`:24,100 images,15,502/4,301/4,297 train/val/test.
- `reports/indoor-partial-joint-v4-audit`:decision,conversion,full audit,data gate,
  environment/readiness/verification and reproducible workflows.

All54 images/553 boxes pass exact source-to-YOLO conversion parity; copied image
bytes/hash unchanged. Six actual converted overlays reviewed (COCO09/16/22,
CrowdHuman01/08/29). Source visual eligibility reviews cover all new54; base visual
approval inherited only with all original limitations. Existing base includes470
individually unreviewed CrowdHuman expansion images; no claim of new full review.

Full joint audit:zero errors,zero exact duplicate groups or scope conflicts.
Train boxes:smoke4,124/fire5,549/person29,974. Validation858/1,262/5,335;
test968/1,146/5,442. Only person train increases by553. Every24,046 base row/scope
retained, original train prefix preserved, validation/test byte-identical.
Raw pilot-v3 and cross-pilot exact/near screens have zero candidates. Derivative
image hashes exactly match raw images, so those screens apply to the added rows.
Fresh registry-integrity check rehashed all24,046 base images and matched the
frozen near-screen registry. Near screen is not exhaustive for crop/mirror/edit/
same-session overlap.

Data gate **PASS_WITH_LIMITATIONS**, training_allowed=true for data only;
execution_authorized=false. Snapshot binds derivatives,labels/images,reviews,
conversion evidence,base gate,current indexes/scopes and audit. It is not continuous
monitoring of underlying base files; re-audit changed data before a future run.

## Predeclared v6 experiment (not launched)

Config: `configs/train_indoor_v6_512.yaml`.
Initialize v2 best.pt (same starting checkpoint as v5), avoiding extra v5 fine-tune
history. Keep uniform unique rows,512px,AdamW/LR0.00015,max12 epochs/patience5,
seed42,scale0.15/translate0.05. All mixing augmentations0; class masking required.
All hazard rehearsal preserved. Fixed batch18/workers2 follows stable v5 recovery
and avoids repeating initial workers8/autobatch memory pressure. V5 early epochs
had different resources, so this is not a bit-identical single-variable ablation.
No error weighting, repeated index rows, broad retries or lowered quality gates.

Target unused run:
`E:/HomeAssistantPi4/runs/indoor-detection/indoor_partial_joint_yolo26n_v6_reviewed_small_512`.
`exist_ok=false`. Canonical checkpoint loads on CPU; no inference/train method
called. RTX5070 Laptop GPU8.52GB,torch2.14.0+cu130,Ultralytics8.4.163 confirmed.

Safe read-only verification from the project C:venv:

```powershell
.venv/Scripts/python.exe -m indoor_detection.crowdhuman_intake `
  --readiness E:/HomeAssistantPi4/reports/indoor-partial-joint-v4-audit/train-readiness.json
```

Preflight PASS, training_started=false,execution_authorized=false. After the user
explicitly requests training, recheck Git/readiness/GPU, then run the recorded
config once. A generic continuation must not cross the user's stop boundary.
After any future run use validation-only calibration/scoped explicit square512
matching; require person F1>=0.65 AND recall>=0.60, smoke/fire recall>=0.90.
Report small-person recall, negatives,false alarms and hazard retention. Test/NCNN
remain closed pending quality approval; disclose historic v2 test use.

## Validation and locks

Tests162/162 PASS (6.84s), Ruff PASS; Build not applicable, Typecheck not configured.
Composer accepts only reviewed clipped vbox/COCO bbox; regression tests cover
both preservation paths and reject head boxes/missing review. No dependency changes.

| Artifact | SHA-256 |
|---|---|
| derivative-decision.json | defbb0350a397a29a391dff33589466bc3c0980125a579e07760a3908897bb8c |
| conversion-consistency.json | 0270d29e64c54ca7a2fdcea0df29bd83d84e655e0a71d120b6e519c9d3952bd5 |
| index-audit.json | cc2fcd34899575bd9f0b5a73eb0f2af9284f7c024984f8ae897e5a7482a636e0 |
| data-gate.json | 7392fe22921ef72b70917f7a0a38e740d0fdc10e9d199469c2acbc467ba805f2 |
| train-readiness.json | 2cd75ed5c24cbc4a8924de5f2b408a365ee65d5ce10dd13a3687755882a3bc6a |
| dataset.yaml | 641b95aa44e238c4699c7a25732272d4c43987b14f0684ceb67dd2705617d6c1 |
| class_scope_manifest.json | 0dfb1efae7300c51d0c4bce83eb7c7d510bf6ed8503def4ba7166f9bbeea6a60 |
| train.txt | b7b1d1536a094ac22eafe59e594828ff83141a1c3f4a984205464ef63907406b |
| val.txt | bd6edaeb329efa5cb86d4e904f4a90b49072118fbfe388bc652bbbdd1de8f182 |
| test.txt | 4d37f4aeb2dfb212adda2aeff60748935a283a03f6074d55cca10376367f8180 |
| train_indoor_v6_512.yaml | 1ceeec8adbc7ae4d299d789c64b51b9af9a5e6b53e5420af6e7a2bd148317a02 |

Artifact manifest21 SHA `c8ab223b06d5ef45ff30ad4b52b6fa7e233d9b500d8cbb9f1d9caf9e6c1ceeec`
binds preparation evidence,conversion galleries,config/composer/tests.

## Authorized execution and epoch rationale (2026-10-06)

Started12:13:11 UTC /19:13 Vietnam time; Python PID34596 (launcher39912).
Run: `E:/HomeAssistantPi4/runs/indoor-detection/indoor_partial_joint_yolo26n_v6_reviewed_small_512`.
Receipt and stdout/stderr: report root above, `v6-execution-status.json`,
`v6-training.stdout.log`, `v6-training.stderr.log`. Hidden durable Python wrapper
`run-v6-authorized.py` records success/failure on exit; it does not retry. Check
receipt plus process/log/run artifacts; do not infer completion from process absence.

Max12 epochs is a bounded experiment budget, not a demonstrated optimum or a
universal YOLO limit. Initialization is the v2 checkpoint trained40 epochs; all
15,502 training images participate, not only the54 additions. V5 selected best
checkpoint at epoch7 by trainer fitness; that does not prove longer training
cannot improve person quality. Patience5 follows validation fitness, not the
product's per-class acceptance gate. 100/200 epochs are possible in a separately
declared schedule if validation evidence justifies them; do not silently extend
this frozen run. Inspect validation curves before deciding on that intervention.
After completion, calibrate/evaluate square512 validation and compare person,
small-person recall, smoke/fire and negatives. Test and NCNN remain closed.
