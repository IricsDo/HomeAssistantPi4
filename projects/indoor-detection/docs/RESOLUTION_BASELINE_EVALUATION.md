# Resolution and pretrained-person comparison

Owner: OpenAI Codex. Status: **IN_PROGRESS**. User approved this plan on2026-10-06.
This supersedes immediate60-epoch preparation; training is conditional on evidence.
No dataset/label/scope/gate change,training,test inference or NCNN export.

## Four stages

1. Evaluate v6 at640/768 and original pretrained YOLO26n person at512/640/768.
   Reuse locked v6-512 results. Five new configurations,zero training runs.
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
- Reuse existing class-scoped rectangular calibration,batch20/workers0,GPU0.
  Person max interpolated F1;smoke/fire highest confidence with recall>=.90.
  One validation pass provides all three class curves per v6 resolution.
- Authoritative matching:square input,rect=False,batch16,IoU.50,
  candidate confidence.001,maxdet100,one unscored warmup.
  All models/resolutions follow same person image membership and matching.
  Thresholds calibrated separately; rectangular calibration reported separately.
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

Root:E:/HomeAssistantPi4/reports/indoor-resolution-baseline-v1.
Frozen protocol SHA
`6a01c93df51c32f9520b257e6250b4dffa583f84ccba122361a1b79320be887e`.
Contains protocol.json,comparison-workflow.py,execution-status.json,stdout/stderr
and separate per-configuration directories. Actual PythonPID18728,launcher29816
at launch21:39 Vietnam time. Use receipt/process/log together for live state.
Do not launch again into existing outputs or overwrite partial/old results.
Workflow stops on exception withFAILED receipt;no automatic retry.

After all five finish,check logs/bindings and compare full metrics,fixed/native
size recalls,negative alarms,hazard retention and resources. Decide next stage
with a written rationale;do not infer release from a single favorable metric.

## Limitations

Pretrained COCO validation familiarity/overlap was not independently audited.
This baseline is diagnostic,not an independent generalization claim or proof
that fine-tuning caused a difference. Mixed-domain hazards,COCO-onlyperson
holdout,historicv2test use and unverified smoke same-test regression persist.
Pi hardware and mounting geometry unavailable; operational min size uncommitted.
Architecture remains one unified detector pending a separate supported decision.
