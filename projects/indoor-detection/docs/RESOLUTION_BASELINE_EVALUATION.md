# Resolution and pretrained-person comparison

Owner: OpenAI Codex. Stage 1 status: **COMPLETED** on 2026-10-06.
Remaining stages: **IN_PROGRESS**. User approved this plan on 2026-10-06.
This supersedes immediate60-epoch preparation; training is conditional on evidence.
No dataset/label/scope/gate change,training,test inference or NCNN export.

## Four stages

1. Evaluate v6 at640/768 and original pretrained YOLO26n person at512/640/768.
   Revalidate v6-512 with aligned square calibration. Six configurations,zero training runs.
2. Define operational person coverage using ROI,distance and projected sizes.
   Camera geometry remains unknown; do not select a minimum merely to pass gates.
   Keep full-corpus metrics alongside exploratory size reports.
3. Choose one justified intervention:resolution/fine-tune schedule,ROI or a
   separately assessed person model. Do not chain retries/source expansions.
4. After quality approval and hardware availability,measure Pi pipeline latency,
   RAM/FPS,camera coverage and lock final resolution/thresholds/artifact.

## Frozen stage1 protocol

- Data:joint v4 dataset.yaml; unchanged4,301 validation images. Person scope
  includes2,501 COCO images,5,335 boxes and1,154 annotated-negative images.
- Checkpoint v6 best SHA
  `103b45ab6a61f2431b462ee2bc4402f6ddaa7b982e872afd50515e3c6ef28729`.
- Original pretrained model:E:/HomeAssistantPi4/models/pretrained/yolo26n.pt,
  SHA `9b09cc8bf347f0fc8a5f7657480587f25db09b34bf33b0652110fb03a8ad4fef`.
- Class-scoped square calibration,batch20/workers0,GPU0,rect=False in
  both validator dataset construction and model.val.
  Person max interpolated F1;smoke/fire highest confidence with recall>=.90.
  One validation pass provides all three class curves per v6 resolution.
- Authoritative matching:square input,rect=False,batch16,IoU.50,
  candidate confidence.001,maxdet100,one unscored warmup.
  All models/resolutions follow same person image membership and matching.
  Thresholds calibrated separately with the same square geometry as matching.
- Pretrained model stays80-class;postprocessing/NMS retains original outputs,
  then evaluation-only projection person0->canonical2 drops other classes.
  Labels/class scopes stay unchanged. Other pretrained classes can occupy the
  output cap; this measures original model behavior,not a pruned one-class head.
  Hazard predictions/quality from baseline are not evaluated or claimed.
- Gates unchanged:personF1>=.65 AND recall>=.60;smoke/fire recall>=.90.
  No person minimum-size filtering. Tiny objects still count in full metrics.

## Size and resource reports

Height bands:[0,16),[16,32),[32,64),[64,128),[128,infinity) projected pixels.
Also both sides<=12 and short side<=12. Include native input and fixed512
projection for every configuration; fixed groups preserve comparable membership
across resolutions. Pre-rounding letterbox estimates,not physical distances.
Recall per bucket is diagnostic;precision cannot be assigned from target counts
alone. No label deletion or ignore policy introduced.

Per-configuration sampled Windows process RSS and CUDA allocated/reserved peak
cover calibration/error/plot/benchmark work,not deployment-only service memory.
Batch1 benchmark uses the same frozen validation image,5warmups/30 measured
iterations,conf.001,maxdet100,square input,synchronized GPU,including image loading
and pre/postprocessing. No camera capture or Pi claim.

## Evidence and continuation

Root:E:/HomeAssistantPi4/reports/indoor-resolution-baseline-square-v2.
Frozen protocol SHA
`eb3598294a551029ab05ea84e794e08545b9883799f524691828325668412cb2`.
Contains protocol.json,comparison-workflow.py,execution-status.json,stdout/stderr
and separate per-configuration directories. Actual PythonPID19396,launcher13700
at launch20:57 Vietnam time. Use receipt/process/log together for live state.
Do not launch again into existing outputs or overwrite partial/old results.
Workflow stops on exception withFAILED receipt;no automatic retry.

All six finished at 21:29:40 Vietnam time, exit 0; PID19396 is no longer running.
Integrity checks PASS: implementation hashes, 21 preparation bindings, identical
person image membership/ground truth and fixed512 bucket counts; no traceback or
NMS timeout in workflow logs. `integrity-and-comparison.json`, `comparison.png`
and `artifact-manifest.json` are finalized. Manifest binds 81 artifacts, SHA
`568dbfa770fa96d4bb56bfbc8c01ac62418d4f3ecc6d6630301d15c6765996f3`.
Run `finalize-comparison.py` from repository root (bindings are relative paths).
Do not rerun into finalized outputs. One attempted invocation from project cwd
failed on a relative binding path before writing final artifacts; root invocation
passed. This did not rerun inference or change the frozen protocol.

## Stage 1 results and decision

Authoritative explicit square matching, all 5,335 person boxes retained:

| Model | Input | Person precision | Recall | F1 | Person gate | Negative images with alarms |
|---|---:|---:|---:|---:|---|---:|
| v6 | 512 | .746482 | .556888 | .637896 | FAIL | 12.39% |
| v6 | 640 | .722133 | .591378 | .650247 | FAIL recall | 11.87% |
| v6 | 768 | .685756 | .621743 | .652182 | PASS | 13.34% |
| pretrained | 512 | .796166 | .614995 | .693951 | PASS | 2.95% |
| pretrained | 640 | .813386 | .656045 | .726292 | PASS | 2.69% |
| pretrained | 768 | .802617 | .678351 | .735270 | PASS | 2.95% |

| v6 input | Smoke recall | Fire recall | All three gates |
|---:|---:|---:|---|
| 512 | .899767 FAIL | .900158 PASS | FAIL |
| 640 | .900932 PASS | .899366 FAIL | FAIL |
| 768 | .899767 FAIL | .897781 FAIL | FAIL |

768 improves v6 person recall by 6.49 percentage points versus 512; it passes
person without ignoring small objects. At fixed512 geometry, height <16 recall
rises from 3.52% to 14.06%; height 16–32 from 18.98% to 38.21%. These objects
remain difficult. Recall for height >=128 decreases from 85.97% to 82.68% at
the separately selected thresholds: increased resolution is not uniformly better.
Pretrained person exceeds v6 overall and has fewer alarms at every input.
This supports investigating transfer/head retention, not concluding YOLO fails
or immediately replacing the architecture. No causal attribution is established.

Inspected diagnostic contact sheets: v6-768 negative alarms include animals,
furniture and other objects; pretrained-640 misses include tiny/dense people.
These selected examples do not estimate error prevalence; counts above do.

Windows GPU batch1 mean milliseconds: v6 512/640/768 = 14.85/18.84/17.79;
pretrained = 14.48/12.80/17.24. Single-image short measurements are noisy and
not monotonic; do not choose Pi resolution from them. Whole-configuration peak
RSS spans about 1.91–2.22 GiB; CUDA reserved peak about .60–1.34 GiB. Neither
is deployment service memory or proof that Pi targets pass.

**Next chosen intervention:** refine smoke/fire threshold calibration for v6-768
against the exact square matcher before considering new training. At current
thresholds smoke needs one additional TP (773/858) and fire three (1136/1262)
to reach .90. Interpolated calibration target attainment did not guarantee these
explicit counts. Freeze a separate protocol/output, keep person threshold and
checkpoint fixed, choose the highest threshold meeting empirical recall >=.90,
report precision/negative alarms and preserve this comparison. If no acceptable
operating point exists, stop and document the trade-off. Do not lower gates,
silently replace prior reports or open test/export. 60-epoch training remains
deferred; no deployment resolution or release candidate is locked.

## Confirmed person coverage

User confirmed: prioritize the room and doorway; very distant people outside
the window are not required. Camera mounting, maximum distance, numeric minimum
size and ROI remain unknown/unlocked. Preserve full validation results and labels.
This scope alone does not justify a 12px cutoff: small/occluded people inside
the room or doorway can matter. Measure actual camera coverage before filtering.

## Limitations

Pretrained COCO validation familiarity/overlap was not independently audited.
This baseline is diagnostic,not an independent generalization claim or proof
that fine-tuning caused a difference. Mixed-domain hazards,COCO-onlyperson
holdout,historicv2test use and unverified smoke same-test regression persist.
Pi hardware and mounting geometry unavailable; operational min size uncommitted.
Architecture remains one unified detector pending a separate supported decision.

## Protocol correction (before square comparison results)

The first launched workflow inherited rectangular calibration despite the new
plan requiring square consistency. Stopped only its verifiedownedPID18728;
process absence verified. Oldroot E:/HomeAssistantPi4/reports/
indoor-resolution-baseline-v1 remains untouched,with protocol-correction.json.
V6-640 completed there;v6-768 was interrupted during person matching. Those
results are supplementary diagnostics only,not the aligned comparison.
Original execution receipt stayedIN_PROGRESS after forcedstop;the correction
receipt recordsterminal decision. No automatic failure retry or source changes.

The square successor revalidates512 instead of mixing historical rectangular
thresholds into comparison. Default historical validator remains rectangular;
new explicit square subclass changes datasetgeometry as well as model.val flag.
Unit regression confirms defaultrect=True and square=False. Tests168PASS7.79s,
RuffPASS before launch. Current code hashes bound in squareprotocol.

Timestamp correction:initial launch was13:39UTC=20:39Vietnam,not21:39 stated
in the prior launch handover. That historical entry is preserved.
