# V6-768 locked final test and smoke regression

Owner: OpenAI Codex. Status: IN_PROGRESS. User requested continuation on2026-10-06.
This opens one fixed test evaluation after validation gates passed. No training,
test threshold selection, retry series or export is authorized by this workflow.

## Readiness and frozen inputs

Preparation: `E:/HomeAssistantPi4/reports/indoor-v6-768-test-preparation-v1`.
Protocol SHA `2a866525bb99459e2d42e23608b9335ad02ee65047605c2d81ec8e341a168cfa`.
Test output: `E:/HomeAssistantPi4/reports/indoor-v6-768-final-test-v1`.
Stdout/stderr are in the preparation root (`test.stdout.log`, `test.stderr.log`).
Hidden launcherPID6792; actual Python PID/times appear in test execution-status.json.
Do not relaunch into existing output. Confirm receipt/log/process for live state.

- Frozen v6 best SHA `103b45ab6a61f2431b462ee2bc4402f6ddaa7b982e872afd50515e3c6ef28729`.
- 768 square, rect=False, candidate confidence .001, maxdet100, IoU .50.
  Authoritative matching batch16/GPU0/one unscored warmup; no minimum size/ROI.
- Thresholds unchanged from validation: smoke .1860014796257019,
  fire .42607951164245605, person .34934934934934936.
- All4,297 test images retained. Scope: smoke/fire1,798 images each,
  smoke968/fire1,146 targets; person2,499 images/5,442 targets.
- Baseline smoke checkpoint SHA
  `1104f90ee0723e0877a4797c71cd88ebc7b43a5841396d153010f59781ea3d04`,
  historical validation threshold .43043043043043044 retained. Original model
  names `{0: item}` from single_cls training; original smoke-only dataset names
  smoke0 and snapshot hash bind its smoke semantics. No model/label mutation.

Readiness PASS: all current smoke test image hashes and normalized smoke GT
multisets match original baseline test. Baseline originally had1,800 images;
two negatives absent from current frozen joint test are disclosed in readiness:
`test_1240.jpg`, `test_696.jpg` (old home-fire source). Regression uses the full
current1,798 images for both models, not different historical aggregate scores.
No exact image-hash overlap with baseline train7,883 or val1,790 images. This is
an exact-hash audit, not new near-duplicate/session or pretrained-overlap proof.
Both models use current canonical GT/scopes and the same preprocessing/matcher.
Different historical resolutions/thresholds are not silently called equivalent.
The baseline is explicitly remeasured at768 with its frozen historical threshold.

The prior v2 test results were inspected. This test is not an untouched holdout;
do not use it to select another threshold, epoch, source subset or augmentation.
If failure motivates redesign, close this candidate and plan independent evidence.

## Predeclared decision

Conservative test floors: smoke/fire recall>=.90, personF1>=.65 AND recall>=.60.
Existing person acceptance specifies validation; these additional test floors are
declared before results as this candidate's release decision, not retroactive
changes to validation gates. Smoke recall delta vs baseline must be>=-.03 on
aggregate and each current source (home-fire and indoor-fs); aggregate alone
must not hide a source regression. No rounding misses to PASS.

Compute scoped square AP using batch20/workers0,conf.001,maxdet100 with the existing
square validator. Do not call threshold calibration on test. Validator default
P/R summaries/curves are diagnostics; fixed-threshold explicit matching decides
the gates. Report per-class/source, tiny/negative/image-condition diagnostics and
smoke baseline counts. Candidate and baseline smoke image/GT identity must match.
Reverify frozen file bindings after scoring. Stop on technical failure; no retry.
Failed quality records NO_RELEASE, not a threshold adjustment on this test.

Pi performance, target indoor coverage at planned height~4m+, camera geometry,
backend parity and final deployment resolution remain unverified even if test passes.
