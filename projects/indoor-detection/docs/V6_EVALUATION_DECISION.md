# V6 reviewed-small-person validation decision

Owner: OpenAI Codex. Status: **READY_FOR_REVIEW** (training/evaluation completed; NO RELEASE).
Training completed on2026-10-06,12 total epochs,exit0; no training job remains.
Test selection and NCNN export remain closed pending quality gates.

## Frozen experiment and checkpoint

- Joint v4:24,100 images,15,502 train/4,301 validation/4,297 test.
- Reviewed-only addition54 images/553 boxes (316 small),same holdout/rehearsal.
- Config `configs/train_indoor_v6_512.yaml`:v2 initialization,512px,max12,
  patience5,AdamW,LR0.00015,seed42,batch18/workers2,uniform rows,mixing0.
- Run `E:/HomeAssistantPi4/runs/indoor-detection/indoor_partial_joint_yolo26n_v6_reviewed_small_512`.
- Reports `E:/HomeAssistantPi4/reports/indoor-yolo26n-v6-evaluation`.
- Started19:13:11,finished19:51:51 Vietnam time (38m40s wall time).
  CSV training duration2255.33s excludes setup/final validation overhead.
- Best selected by inline fitness at epoch10 (mAP50-95=0.54526).
  Best SHA `103b45ab6a61f2431b462ee2bc4402f6ddaa7b982e872afd50515e3c6ef28729`.
  Last SHA `b402f97023770b05272a3a3d61edee688f8d9876d146084790681d0e606f76db`.
- All21 preparation-manifest bindings rechecked PASS; dataset/config/index/scope
  hashes unchanged. This is not a fresh hash of every source image/label.

## Protocol declared before standalone results

Reuse v5 protocol: standalone class-scoped validation512,GPU0,batch20,workers0,
rectangular padding. Smoke/fire choose highest interpolated confidence meeting
validation recall0.90; person maximizes validation F1. Report curves separately.
At those thresholds, explicit class-scoped validation matching uses square512,
rect=False,one unscored warmup,batch16,candidate confidence0.001,max_det100,IoU0.50.
Person requires F1>=0.65 AND recall>=0.60; smoke/fire recall>=0.90.
Square matching is authoritative; do not pick favorable metrics across protocols.
No test inference during selection; disclose historic v2 test use. No automatic
retries,source expansion,gate reduction or schedule extension.

## Epoch-budget evidence

Twelve epochs is the frozen experiment budget,not a proven optimum. Training
loss declines while aggregate validation mAP50-95 last5 spans0.54382–0.54526;
late epochs do not show a strong monotonic gain. These aggregate curves do not
establish convergence or a person-specific optimum. A100/200-epoch schedule is
a possible separate hypothesis,not a guaranteed fix or permission to change this
completed run. Figure and per-epoch data:training-curves.png and
training-curve-analysis.json on E.

## Limitations

Mixed indoor/outdoor/staged/synthetic corpus; source slices are provenance proxies.
Person holdout remains COCO only; no independent CrowdHuman or physical camera
benchmark. Reviewed54 do not remove base limitations,including470 previously
auto-screened CrowdHuman expansion images. Fixed v6 resources differ from early
v5; comparisons cannot isolate a causal effect of the54 additions. Historic v2
test use and unverified smoke same-test regression gate persist. Pi hardware
validation unavailable. See [V6 preparation](V6_TRAINING_PREPARATION.md).

## Results: NO RELEASE

Both training and validation workflow completed without traceback/NMS timeout.
No job remains. No test evaluation or NCNN export.

### Calibration (rectangular validator, interpolated class curves)

| Class | Confidence | Precision | Recall | F1 | Gate |
|---|---:|---:|---:|---:|---|
| smoke | 0.148148 | 0.8311 | 0.9005 | 0.8644 | PASS |
| fire | 0.347347 | 0.9008 | 0.9002 | 0.9005 | PASS |
| person | 0.327327 | 0.7424 | 0.5554 | 0.6354 | FAIL |

Person maximizes F1; smoke/fire target recall0.90. Per-class mAP50/mAP50-95:
smoke0.92280/0.62161,fire0.92833/0.61891,person0.63413/0.39677.
Confusion plots and confidence/PR curves persist under validation-runs.

### Authoritative square512 explicit matching

| Class | Precision | Recall | F1 | TP / FP / FN | Negative alarms | Gate |
|---|---:|---:|---:|---|---|---|
| smoke | 0.8091 | 0.9138 | 0.8582 | 784 / 185 / 74 | 22/990 (2.22%) | PASS |
| fire | 0.9013 | 0.9049 | 0.9031 | 1142 / 125 / 120 | 7/616 (1.14%) | PASS |
| person | 0.7369 | 0.5618 | 0.6375 | 2997 / 1070 / 2338 | 145/1154 (12.56%) | FAIL |

Person fails both required thresholds. Small recall616/2,257=0.2729,medium
954/1,415=0.6742,large1,427/1,663=0.8581. Small boxes account for1,641/2,338
misses (70.2%). Miss reasons:1,551 below confidence,755 localization/no-overlap,
31 duplicate/assignment,1 no candidate; these are diagnostics,not label corrections.

Smoke blurred slice75/86=0.8721,versus v5 72/86; blur alone remains no rejection.
Source recalls smoke0.9295/0.9076 and fire0.8930/0.9086 for indoor-fs-v2 /
indoor-home-fire-v2. Overall hazard gate passing does not imply every source
slice passes or prove same-test smoke regression; that gate remains unverified.

| Square512 validation control | Person F1 | Recall | Small recall | Negative alarms |
|---|---:|---:|---:|---:|
| v2 | 0.6351 | 0.5432 | 0.2530 | 11.61% |
| v4 | 0.6292 | 0.5593 | 0.2907 | 14.64% |
| v5 | 0.6415 | 0.5717 | 0.2880 | 11.79% |
| v6 | 0.6375 | 0.5618 | 0.2729 | 12.56% |

Same validation membership and matching settings,independently calibrated
thresholds. V6 does not improve the target metrics over v5; fixed loader/training
history differs,so this does not prove the54 images caused a decline. No separate
CrowdHuman/camera holdout has been introduced.

Actually viewed two person contact sheets (misses,negative alarms) and original
resolution overlays001_000000388846 and007_000000505573. Examples: tiny beach
people missed,animal/figurine/statue false alarms,including dog confidence0.87.
Selected errors do not estimate domain prevalence or authorize relabeling.

## Next intervention proposal: training schedule

Prepare one max60-epoch/patience15 experiment on the same joint v4,from the same
v2 initialization,512px,batch18/workers2,AdamW LR0.00015,seed42,uniform masking
and mixing0. This tests the unresolved budget/schedule hypothesis before another
source intake. Keep all holdouts/rehearsal and gates unchanged. The longer LR
decay schedule is part of the intervention; it is not an exact resumed v6 run.

Status **PLANNED_NOT_AUTHORIZED_TO_LAUNCH**: no new config/readiness/run created.
Freeze the new schedule and resource estimate,verify existing data locks and
unused output,record explicit execution decision before launching. Do not resume
completed v6 or chain retries. More epochs may help or fail; aggregate plateau
and person failures provide no guarantee. One longer schedule can test this
hypothesis;100/200 is not required or prohibited by the framework.

## Validation and reproducibility

Tests162/162 PASS7.49s,Ruff PASS; Build not applicable,Typecheck not configured.
Existing APIs reused without implementation/dependency changes.
`evaluation-workflow.py` on E declares and executes the protocol once; outputs
refuse existing summary/calibration/error targets. Final summary adds control
comparison,visual review and next-intervention proposal after the workflow.
Do not rerun into the same directory; use a separate derivative output.

Artifacts:training-result.json,training-curve-analysis.json,training-curves.png,
post-training-integrity.json,three calibration files,three square-error directories,
person-control-comparison.json,evaluation-summary.json,stdout/stderr and
artifact-manifest.json (36 selected reports/scripts/CSV/PNG/log files).
Summary SHA `416226173e9aa60f7e2eeb6036bc4166117d249d0ef92df12fcb7e6cd4eab4ed`.
Manifest SHA `f8a2cce43625a20b7d6350276fcc2599b7ee5ef2fa5b2eccf8a3f76b7b5bc27b`.
All21 preparation bindings rechecked after evaluation:PASS. Gallery images/data
remain on E;no weights,datasets or secrets committed.
