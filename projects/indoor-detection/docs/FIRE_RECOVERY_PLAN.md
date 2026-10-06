# Fire diagnosis and bounded recovery proposal

Owner: OpenAI Codex. Diagnosis COMPLETED; v7 proposal PLANNED, not launched.
Updated 2026-10-06. V6 final test remains NO_RELEASE; never tune/reopen that test.

## Evidence from training and validation only

Report: `E:/HomeAssistantPi4/reports/indoor-v6-fire-diagnosis-v1`.
No GPU inference or test access in diagnosis. Reused immutable fire validation
predictions; inspected train annotations/image dimensions without modifying data.
Source-specific thresholds below are diagnostics, not a deployment policy.

| Source | Train images | Fire GT | GT area <1% | Validation fire GT | Current val recall |
|---|---:|---:|---:|---:|---:|
| indoor-fs-v2 | 4,000 | 2,571 | 326 (12.68%) | 299 | .839465 |
| indoor-home-fire-v2 | 3,900 | 2,978 | 1,443 (48.46%) | 963 | .919003 |

At the current shared fire threshold .4260795, aggregate validation recall .900158
passes while indoor-fs fails. Home-fire contributes 76.31% of validation fire GT.
Source-specific threshold required for 90% recall differs (.226140 FS, .517446
home-fire). These differences indicate an operating-point/domain problem; they
do not identify its cause or justify different runtime thresholds by source.

Only 7/299 FS validation fire boxes have area<1%; its low recall cannot be explained
solely by tiny objects. Train has 170 projected short-side <= 12 boxes overall, val 55,
all retained. GT pair IoU >= .50: 1 train, 0 val; >=90% containment: 8 train, 2 val.
Geometric overlap is rare, so pervasive overlapping GT is not established as the
main failure mechanism. This does not prove annotation completeness/correctness.

FS validation recall: normal-brightness .8245 (188 GT), dark .8649 (111 GT);
sharp .8000 (160 GT), soft .8922 (102 GT), blurred .8649 (37 GT). Counts are descriptive
and correlated, not causal evidence that sharpness/lighting caused misses. No
blur filtering is introduced; source names remain mixed-domain provenance proxies.

| Diagnostic aggregate val recall target | Threshold | Precision | Negative-image alarm rate |
|---|---:|---:|---:|
| .90 | .4260795 | .886115 | 2.11% |
| .92 | .2935935 | .841419 | 3.41% |
| .95 | .0372991 | .565299 | 13.31% |

The .92/.95 probes breach the previous intervention's 1 percentage point precision
and negative-alarm guardrails. No new threshold/candidate was selected. Lowering
confidence alone is not supported as an acceptable recovery under those limits.

## One bounded proposal

Prepare one continuation fine-tune **at 768**, initialized from frozen v6 best,
using unchanged joint-v4 images/labels/scopes and existing class-masked trainer.
Keep source sampling, loss, optimizer/LR and augmentation policy unchanged.
Do not add a second model, relabel test, expand sources automatically or launch 60
epochs. The hypothesis is that training at the evaluated resolution can improve
confidence/localization while preserving smoke/person; this is unproven. Continued
training and resolution change are not a causal ablation of each other.

Draft `configs/train_indoor_v7_768_proposal.yaml`: max 12 epochs/patience 5,
AdamW/LR .00015, seed 42, workers 2, batch 8 (memory precaution at 768), mixing 0.
Batch 8 is provisional; validate GPU memory/resources before the single launch.
New run must not exist. No training permission is represented by this draft config.
Readiness must verify data gates, checkpoint SHA, environment, scope masking and
resources; preserve all earlier runs. No automatic failure retry.

Before launch, establish independent holdout intake per
[INDEPENDENT_HOLDOUT_PLAN.md](INDEPENDENT_HOLDOUT_PLAN.md). The closed v6 test is
development history, not the acceptance set for v7. Existing val remains calibration.

Predeclare v7 validation decision before results: one global threshold per class;
fire recall>=.90 on aggregate **and each source**, smoke R >= .90, person F1 >= .65/R >= .60.
Apply the existing intervention precision/negative-alarm guardrails relative to
frozen v6 validation points for smoke/fire (drop/increase<=.01). Report person
negative alarms and require no increase>.01 vs frozen v6. These are conservative
experiment criteria, not silent changes to historical acceptance. No source-aware
runtime thresholds. Select checkpoint only using training/validation; retain
inline scoped best.pt selection, then assess exact square calibration externally.
If no acceptable point/source gate exists, stop NO_RELEASE; no next retry series.
If accepted, lock checkpoint/thresholds before opening the new holdout once.

## Immediate continuation checklist

- [x] Train/validation diagnosis and diagnostic trade-offs; data/test unchanged.
- [x] Draft one bounded config and stop conditions; no training launch.
- [x] Define independent holdout admission and use policy.
- [ ] Assess concrete labeled source candidates and freeze scene/video groups;
  prepare holdout metadata/annotation/overlap audit before any prediction on it.
- [ ] Pass holdout/data/resource readiness and record one launch authorization.
- [ ] Run proposed v7 only after those prerequisites; do not launch directly from YAML.

Camera remains planned at~4m or higher; actual tilt/distance/ROI and Pi performance
await hardware. No numeric person cutoff, class deletion or dataset mutation.
