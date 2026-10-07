# V7 experimental preparation and holdout freeze

Owner: OpenAI Codex. Updated 2026-10-08.
Status: READY_FOR_REVIEW for one bounded experimental v7 run, with limitations.
**No v7 training, optimizer step or new holdout prediction has been run.**

## Explicit protocol amendment before predictions

The original intake targets were 30 independent groups, 300 fire, 300 smoke,
500 person boxes and 200 verified negative images per class. Accessible labeled
sources repeatedly contained known training scenes, incomplete annotations or
unverifiable access/ancestry. Their outcomes are preserved in earlier reports.
The intake plan expressly permits revision before predictions.

For **one bounded experimental v7 run**, freeze revised intake targets:
7 conservatively reserved source/event families across 4 sources, at least
90 fire, 300 smoke, 500 person boxes and 200 verified negatives per class.
Seven reserved families are **not seven proven statistically independent samples**.
These targets apply to experimental preparation only. The original 30-group /
300-fire target is NOT_MET; representative independent acceptance and deployment
remain incomplete. Even passing this experimental holdout cannot authorize release.
No numerical recall/F1 or precision/negative-alarm guardrail has been lowered.
No image was selected by model predictions, box size, blur or model success.

This amendment is recorded in `reports/indoor-v7-holdout-freeze-v1/protocol.json`
on E: before holdout predictions and training. Whole sources remain reserved,
including unselected adjacent frames. No new source enters joint-v4 training.

## Frozen external evaluation data

Root: `E:/HomeAssistantPi4/processed/indoor-v7-experimental-holdout-v1`.
Reports: `E:/HomeAssistantPi4/reports/indoor-v7-holdout-freeze-v1`.

| Source | Images | Scored boxes | Known annotation scope | Reserved family |
|---|---:|---:|---|---|
| THUD real store | 808 | 379 person | smoke/fire negative; person known on 733 images | one store family |
| Boreal 2022 burns | 398 | 398 smoke | smoke only | four original burn events |
| AGHRI 2024 greenhouse | 100 | 188 person | person only | one greenhouse family |
| RGBT-3M night/yard | 97 | 97 fire | fire only | entire RGBT source |
| Total | 1,403 | 398 smoke / 97 fire / 567 person | per-image scope manifest | seven reserved families |

Verified negative images: smoke808, fire808, person461. Unknown classes never
count as negatives. THUD store/public interior is an indoor proxy; greenhouse and
outdoor UAV views are supplemental stress evidence. Room/doorway camera at 4m+
has not been validated. No numeric minimum person size or ROI is introduced.

### Annotation decisions

- Reviewed all809 THUD images. Keep source People boxes where completeness was
  verified;75 images have unknown person scope. Identical images737/738 have two
  slightly different source box coordinates: retain earliest737 and drop738 in
  the derivative, preserve both originals. No synthetic data included.
- Boreal400 original-image hashes and all4,954 mirrored label hashes agree with
  original Fairdata checksums. Reviewed400; images353/356 each contain11 nested/
  component boxes including whole plume. Exclude those two from smoke scope
  before predictions; do not merge boxes or mark them negative.
- AGHRI100 images from four original2024 dates/scenarios reviewed. Source numeric
  classes are person identities per creator exporter. Explicitly clip29 images'
  source-boundary boxes to the image rectangle; retain original xywh and provenance.
  All188 boxes survive. Four sequences in one greenhouse are one conservative family.
- RGBT public archive SHA `f54784cb705b7b87d5baa64cac0156e5459155129da5dafc44bf7da86e05a442`.
  The11,220 RGB labels reproduce published class totals exactly; that is not an
  original per-file hash proof. Reviewed8 pilot +400 seed48 fire-positive images,
  and enlarged crops0-99. Forest videos2-5 have uncertain RGB-visible burning
  sites; road videos8/9 frequently label trays without identifiable RGB flames.
  Quarantine these whole video subsets for scored fire evidence. Yard52/62/76
  have uncertain burning state and are excluded, not relabeled negative.
  Keep97 night/yard originals with the **source burning-core/tray box convention**;
  boxes do not necessarily enclose every transient flame tip. Report this convention
  and localization limitation; no claim of full flame-envelope annotations.
  RGBT person offsets and nested smoke boxes prevent automatic other-class scopes.

### Provenance/access limitations

[THUD creator](https://github.com/jackyzengl/THUD-plus-plus) links its public
[Zenodo release](https://zenodo.org/records/18459791);2024 research/2026 release,
capture dates unknown, CC BY4.0. Boreal originals are2022 prescribed burns;
mirror packaging dates do not change original age.
[AGHRI creator](https://github.com/LCAS/AGHRI-dataset-tools) and original Figshare
32982638 establish2024 captures/2026 release, CC BY4.0.
[RGBT original paper](https://doi.org/10.3390/rs17152593) is2025; capture dates remain
unknown. Public HF AwayXu/RGBT-3M revision
`1a3cbf46a39a33595f88473cb4f841d015ac2a23` was accessible without an account,
but its README says private/pending source and license review. Public access is
not license clearance. Preserve that unresolved status; use locally for this
experiment only, do not redistribute or treat it as deployment approval.
Unknown capture dates/pretrained exposure are unresolved evidence gaps, not
proven independence or recent acquisition. Whole-source reservation and known-
corpus checks reduce leakage; they do not remove every provenance gap.

### Overlap/structure/conversion evidence

Refreshed33,849 known-corpus image hashes. THUD/Boreal/AGHRI: zero exact matches,
five dHash candidates manually adjudicated FALSE_MATCH. RGBT400: zero exact,
165 candidates ALL manually inspected and FALSE_MATCH. No confirmed reuse.
Full derivative: zero exact duplicates, zero cross-source dHash<=5 candidates.
Within-family adjacent frames remain correlated and reserved together; source
families/crop/mirror ancestry and pretrained exposure are not exhaustively proved.
FURG real car/barbecue/NASA pilots all show confirmed old-corpus scene reuse:
reject each entire event; do not salvage unmatched remainders.

Holdout scoped audit:1,403/1,403 valid, zero missing labels/scope violations/
conflicting duplicates. Independent conversion verifier checks original THUD,
Boreal and RGBT label bytes plus4 AGHRI original annotation hashes/100rows.
Pixel round-trip error <=7.12e-8 pixels (tolerance1e-6), images byte-identical.
Frozen3,107-binding manifest SHA:
`af9065e0abbccabac301d48f0244c8d4ca528928c93ae170b772286af329ff37`.
Do not rerun acquisition/freeze generators into these existing report directories.

## Unchanged training and bounded resource probe

Draft remains `configs/train_indoor_v7_768_proposal.yaml`, SHA
`5cccddd70d70aef20f5adf2a5e53eee1b8ac1cf45e616fed475e8b93da0c7466`.
V6 best SHA `103b45ab6a61f2431b462ee2bc4402f6ddaa7b982e872afd50515e3c6ef28729`.
Joint-v4 remains24,100 images (15,502train/4,301val/4,297historical test).
Fresh audit: all24,100 valid, no missing scopes/labels/exact duplicate conflicts.
Old test was checked for integrity only, no inference or model-selection access.

One proposed768 continuation: max12epochs/patience5, batch8/workers2, seed42,
AdamW lr0=.00015/lrf=.05, warmup.5, existing class masking/sampling, mixing0.
No training dataset expansion or dependency change.

Readiness reports: `E:/HomeAssistantPi4/reports/indoor-v7-readiness-final-v1`.
Two finite forward/backward passes on an in-memory checkpoint copy at768/batch8,
including mixed hazard +dense person342GT and allocated AdamW-like moment buffers:
peak allocated1,846,358,016B / reserved2,021,654,528B; RTX5070Laptop8GB.
No optimizer step, trainer/epoch, checkpoint save, new run or holdout prediction.
First probe report serialization failed because YOLO26 E2E loss_items is a dict;
failed recipe/error retained, serialization fixed, finite probes completed.
This estimates memory feasibility, not worker/augmentation peaks, long-run stability
or Pi performance. Actual training must stop on any error/OOM; no automatic retries.

## Evaluation policy frozen before v7 results

See readiness `evaluation-protocol.json`. Existing validation alone selects the
scoped best checkpoint/global thresholds. Square768 (`rect=False`), candidate
conf=.001/maxdet100, matching IoU=.50 and one unscored warmup.
Fire R>=.90 aggregate AND each existing validation source; smoke R>=.90;
person F1>=.65/R>=.60. Hazard precision drop and negative-alarm increase <=.01,
person negative-alarm increase <=.01 versus frozen v6 on the same validation.
If validation fails: NO_RELEASE, keep holdout closed, no retry series.

Only after validation acceptance, lock checkpoint hash/thresholds/preprocessing
before one new holdout opening. Require same recall/F1 gates and report every
positive source/event; smoke regression drop<=.03 and negative-alarm increase
<=.01 vs frozen v6 on this SAME scoped holdout. Recall is undefined on negative-
only sources. Uncertainty must respect correlated families; no frame-iid confidence
interval or representative indoor-generalization claim. No holdout tuning.
Even PASS leaves deployment closed pending representative independent/hardware
proof. If FAIL close candidate, preserve results; further redesign needs new evidence.

## Final readiness evidence

Final read-only receipt at03:17 local:33,849 prior corpus images,3,107 frozen
holdout/report bindings,24,100 current joint image/label hashes and scope coverage
verified. Checkpoint/config/split hashes unchanged; new v7 run absent. RAM available
18,161,176,576B; E: free526,096,146,432B. Python3.14.7 local C: venv;
torch2.14.0+cu130, Ultralytics8.4.163; no packages installed on E:.
Readiness manifest SHA:
`bb04c647d955999f653a6efc8ba19571d084a9a5c37bf2a2ddc51f09bc847086`.
This receipt establishes bounded experimental preparation, not full independent
acceptance. Do not rerun report generators into frozen directories. Verify existing
bindings without rewriting receipts before a later launch.

## Stop boundary / next authorized action

Tests192/192 PASS (6.50s), Ruff PASS, pip check PASS, git diff --check PASS.
Build not applicable; typecheck not configured. Documentation-only repository changes;
all large data/report artifacts remain E:. Preparation milestone is committed/pushed.
Stop before training. The next action is a separately authorized single v7 launch,
after read-only verification of frozen bindings, current GPU/RAM/disk and absent
run `indoor_partial_joint_yolo26n_v7_aligned_768`. Do not resume/relaunch v6 or
rewrite this frozen evidence. A train-ready experiment is not a deployable model.

A later authorized launch command, NOT executed in this preparation session:

```powershell
# From projects/indoor-detection, only after frozen integrity/resource recheck
.venv/Scripts/python.exe -m indoor_detection.train --config configs/train_indoor_v7_768_proposal.yaml
```

Preserve the unrelated untracked `src/indoor_detection/source_box_review.py`.
