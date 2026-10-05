# P1b small-person labelled pilot

Updated 2026-10-06 by OpenAI Codex. **IN_PROGRESS**: CrowdHuman pilot review and
duplicate screening complete; expansion deferred. Next unused-COCO pilot frozen.
No model run, conversion or joint-dataset mutation. V5 remains NO RELEASE.

## Selection and evidence

Revalidated the original 15,000 train ODGT records using the existing whole-image
body-ignore/invalid-body exclusion. Excluded **all 560 attempted IDs** from the
previous 60 pilot and 500 expansion, including their rejected images. Retained
valid-head and head intersection/min(area) <0.5 filters. This conservative filter
can remove valid occluded people; it does not establish annotation correctness.

Remaining population: **1,834 images / 20,311 person boxes**, 13,416 marked occluded.
ODGT has no image dimensions. Raw pixel area and vbox area divided by the visible
annotation envelope are descriptive selection proxies, never actual image size.
The envelope is the rectangle spanning all raw vboxes; no clipping is possible
before decoding. Single-person images may have small actual boxes despite a
large envelope ratio. No inferred image bounds are used as ground truth.

Proxy strata: high = >=3 boxes with envelope area ratio <1% and share >=30%;
some = >=1 such box, excluding high; none = zero. Population: **37/248/1,549**.
Before any image download, froze 60 IDs using sorted original train IDs and one
`random.Random(45)`, sampling high/some/none sequentially with quotas **30/20/10**.
All 60 require visual review, including original-resolution tiny/ambiguous cases.
This is a diagnostic enriched pilot, not a representative source sample.

Acquired only these original training JPEG members from the existing pinned HF
revision `d97203da87e348ea69f7a7633a57c21a956120a6` using bounded HTTP ranges and
the existing downloader with eight workers. Exit 0; all 60 paired images decode,
receipt hashes match, and visible geometry has **zero flags**. 43 raw vboxes
extend outside image bounds; normal clipping alone is not an annotation error.

Actual size audit clips each vbox to decoded image dimensions. Small <1%, medium
1%-5%, large >=5% image area (not the proportion of padded 512x512 canvas).

| Selection stratum | Images | Small boxes | Medium | Large | Total |
|---|---:|---:|---:|---:|---:|
| high | 30 | 548 | 367 | 85 | 1,000 |
| some | 20 | 63 | 173 | 110 | 346 |
| none | 10 | 4 | 19 | 61 | 84 |
| total | 60 | **615** | 559 | 256 | **1,430** |

Small share **43.01%**, compared with 12.07% in the previous accepted pilot plus
expansion. These are existing source labels, not yet visually accepted labels;
coverage is not evidence that model quality improves. Source density is higher,
and small/occluded cases require special completeness checks. Scope remains
person-only; unannotated smoke/fire must remain unknown under class masking.
Original noncommercial provenance policy and mixed-domain caveats remain.

## Frozen stop rules and immediate next steps

1. Verify `artifact-manifest.json` and inspect all 60 paired galleries plus crops.
   Record ACCEPT/EXCLUDE and reasons separately; preserve original annotations.
   Any new systematic box/completeness issue stops conversion pending assessment.
2. Compare with the **current 24,046-image joint v3**, including its 548 accepted
   CrowdHuman images. Build a current registry; the old 23,498/23,547 registries
   alone are insufficient. Run exact/near screens and adjudicate candidates.
   Keep crop/mirror/same-session limits explicit; never mine holdout errors.
3. Recompute actual sizes after visual/duplicate exclusions. **No expansion if
   accepted small-box share <30%**. This is an intake coverage stop rule, not a
   new or reduced person quality gate. If it passes, freeze a separate bounded
   expansion and review protocol before downloading. Do not automatically train.
4. Any new derivative must preserve all hazard rehearsal, scopes, and frozen
   validation/test membership; repeat full joint gates before declaring one run.

All 60 galleries are generated but **none reviewed in this milestone**. Exact and
near overlap are **not yet checked for this pilot**. No processed derivative or
training readiness file exists. Test/export remain closed and all jobs finished.

## Artifacts and reproduction

Raw: `E:/HomeAssistantPi4/raw/CrowdHuman-small-person-pilot-v1`.
Reports: `E:/HomeAssistantPi4/reports/crowdhuman-small-person-pilot-v1`.
`gallery/bundle.json` lists all 60 review paths in acquisition order.
`measure-pilot.py` reproduces the decoded size audit/gallery to fresh output;
its original invocation refuses existing audit outputs. Never overwrite evidence.

| Artifact | SHA-256 |
|---|---|
| coverage.json | 940ff807e303ac3e4a3aad0d5d00a5917212a14085b6d6d1d413dcba7e18ba4b |
| plan-60.json | f382301b5e1cff26363b799a2c90cd48ddd36a44533fae0c922cfbabae5838e0 |
| actual-size-coverage.json | 99672b0dc74824315e3a2ed99c25224661fbc91c483fe51efadfcd98b7aa11ff |
| acquisition.json | 510836b224dd30be44fc8841a08333998f27749a4905ac5821b4fae0862611af |
| artifact-manifest.json (8 primary files) | ba4fa8ca190cae51af88cdf33203ed85c062b022d4d955838cc2b56afb98fbe1 |

From project C: venv, annotation-only assessment command (use a fresh output):

```powershell
.venv/Scripts/python.exe -m indoor_detection.crowdhuman_coverage `
  --annotations E:/HomeAssistantPi4/raw/CrowdHuman-assessment/annotation_train.odgt `
  --previous-plan E:/HomeAssistantPi4/reports/crowdhuman-assessment-v1/labelled-pilot-plan.json `
  --previous-plan E:/HomeAssistantPi4/reports/crowdhuman-pilot-box-review-v1/expansion-plan-500-v1.json `
  --output E:/HomeAssistantPi4/reports/NEW-coverage.json
```

`freeze_plan(report_path, {'high':30, 'some':20, 'none':10}, seed=45)` produces
the acquisition-compatible plan. This acquisition is completed; do not repeat it.
Tests **158/158 (7.75s)**, Ruff PASS; no new dependency. Venv stays on C:, all
image/report artifacts on E:. Unrelated untracked source_box_review.py preserved.

## Review decision and next pilot (2026-10-06)

The acquisition-state paragraphs above are historical. **All 60 paired galleries
and 21 original-resolution diagnostic crops were actually inspected**. Final
ledger `review-final-v1.json`: **30 ACCEPT / 30 EXCLUDE**. ACCEPT means eligible
for a later derivative, not certification of exhaustive labels or a joint gate.
All source images and annotations remain unchanged; no conversion was performed.

Accepted gallery numbers: 01,02,03,04,07,08,09,11,13,14,16,19,20,24,26,27,28,29,
31,33,39,41,44,51,54,55,56,57,59,60. Accepted labels: **397 boxes**, including
**189 small / 107 medium / 101 large**, small share **47.61%** (coverage gate PASS).
Accepted high/some/none strata have 172/13/4 small boxes respectively.

Original crops resolved several apparent duplicates as distinct occluded people
(04,11,27,28,41,51,59). Do not call these annotation errors. Record34's crop
confirms an unsupported target on the wall/window left of the first visible
woman, separate from her box2. Other exclusions include unresolved crowded/partial
assignments or completeness, mirror/background ambiguity (18/40), promotional
rendering (48), decorative border (58), and embedded border/box convention (52).
Conservative exclusions do **not** mean every excluded annotation is proven wrong.
No new systematic error rate or whole-source defect is established by this sample.

**Defer CrowdHuman expansion and conversion**: coverage passes, but unresolved
dense-target assignments make automatic enlargement inappropriate. This decision
does not invalidate the previous v3 gate or imply that all existing source labels
are bad. Retain the 30 accepted examples and ledger for a later scoped intervention.
Model quality gate remains FAIL; no new model predictions, test or export.

Current joint registry `joint-v3-registry.json` freshly hashes **24,046 images**,
including all548 previous accepted CrowdHuman derivatives. Exact raw SHA screen:
zero internal/corpus overlaps. All60 x24,046 dHash<=5 pairs screened, zero internal
or corpus candidates. No adjudication queue needed. Registry files were rehashed
by the near audit; train/val/test index hashes unchanged. Crop/mirror/edit/session
overlap remains a limitation, so screening is not an exhaustive leakage proof.

### Concrete next intake: unused original COCO train annotations

Annotation-only census from existing `raw/COCO2017/annotations/instances_train2017.json`:
64,115 train images have person annotations. Excluded 6,000 filenames already in
current corpus, 4,756 person-crowd images, and one invalid clipped-geometry image;
remaining **53,358 images**. No original validation/test annotations were mined.
Filename exclusion is only preliminary and does not replace image duplicate gates.

Rule for enriched candidates: >=3 small boxes, >=50% small share, <=40 people;
valid clipped person geometry and no person `iscrowd`. **8,093 candidates**, 60,213
boxes including49,192 small. None of these candidate original images is downloaded.
Unlike ODGT proxies, sizes use original COCO image width/height metadata, still
requiring decode verification. Existing COCO convention matches the base source;
this is not a claim of indoor-domain adequacy or guaranteed metric improvement.

Frozen `coco-pilot-plan-60-v1.json`: seed46, sorted train ID pools, sample30 with
3-6 people, then30 with7-15 people (populations3,633/4,460). **60 images / 415 boxes,
342 small (82.41%) according to metadata**. All60 require visual review. Same
accepted small-share>=30% stop rule; any systematic annotation/completeness issue
or unresolved duplicate conflict blocks expansion/conversion. No download yet.

Next agent: inspect `src/indoor_detection/coco_person_dataset.py` before extending
or reusing acquisition; preserve its original train IDs/annotations and this frozen
plan. Acquire exactly these60 to a fresh E directory, decode/hash/geometry/size
check, render all60, screen against current joint v3 and review. Do not rerun the
old uniform COCO builder to replace existing source indexes. Keep partial-label
scope person, hazard rehearsal and all current holdout membership unchanged.

| New artifact under the same report root | SHA-256 |
|---|---|
| review-final-v1.json | 4cd72f6cbc612a8b5a67f1df909f4da104c80ea96d7036662257037ddcc05c2d |
| coco-pilot-plan-60-v1.json | c1afa602c049015ae9172b28469e8e4f51984d0459b5d03ca9f02cb69f0c169a |
| review-artifact-manifest.json (30 files) | 33897720b03346992c65ead3f8d77e54ed6f28e7f54bf8b6f58cb94ba8c9dd0a |

Other artifacts: exact-overlap.json, near-overlap.json, unused-coco-train-coverage.json,
duplicate-workflow.py, coco-coverage-workflow.py, crops/*.png. Original acquisition
manifest remains untouched. Review manifest locks all21 actually viewed crops.
Tests158/158 (7.72s), Ruff PASS. No active job or dependency/code change this milestone.


## COCO pilot acquisition and review decision (2026-10-06)

The COCO pre-acquisition paragraphs above are historical. The exact frozen60 IDs
were downloaded with the existing bounded COCO downloader, workers8, to fresh
`E:/HomeAssistantPi4/raw/COCO-small-person-pilot-v1`. Reports/gallery/crops are at
`E:/HomeAssistantPi4/reports/coco-small-person-pilot-v1`. Original image IDs,
filenames, source boxes, category metadata and per-image license IDs are retained
in `source-annotations.json`; no source relabeling or new rights verification.
Only original train annotations were read. No old uniform builder/holdout mining.

All60 decode and match source dimensions; clipped person geometry passes, with
no flagged issues. Actual decoded sizes:342 small/58 medium/15 large =415 boxes,
small82.41%, matching frozen metadata. Small means clipped box area/image area
<1%; medium<10%. Raw acquisition receipts bind image hashes and frozen plan.
All60 paired plain/box galleries and25 original-pixel diagnostic crops were
actually viewed. Authoritative `review-final-v1.json`: **24 ACCEPT/36 EXCLUDE**.
Accepted gallery numbers:01,06,08,10,11,12,14,17,19,21,22,29,30,31,33,36,39,41,
48,49,50,53,55,57. **156 accepted boxes:127 small/23 medium/6 large**, small81.41%.
ACCEPT is eligibility for a later reviewed-only derivative, not exhaustive
annotation certification or training authorization.

Confirmed localized concerns include the omitted beach pair05, unboxed woman09,
foreground head and split background assignment20, adjacent pedestrian32,
unsupported wide box37, unboxed boarding-stair people43 and train passenger47.
03's helmet extends above the source primary-person bbox; 52's tiny box10 lacks
supported physical person extent. 15 includes a printed advertisement face,
26 labels reflections,56 labels a skull/skeleton prop,16 is a printed photograph
and27 is an anaglyph. Other exclusions are conservative unresolved completeness
or tiny/partial target assignments, not proven wrong labels. 19's crop resolves
apparent overlap as distinct people. 53's crop does not support a substantial
head-omission claim. Motion blur39 is accepted; blur alone is not a rejection.

Exact hashes:zero internal/corpus matches. dHash<=5 screen:zero internal/corpus
candidates against24,046 joint v3 images, including548 prior CrowdHuman. Existing
registry membership/index locks verified; the near screen freshly rehashed all
registry images. No queue needed. Crop/mirror/edit/session overlap remains a
limitation. Frozen train/val/test indexes are byte-identical; no source/joint,
scope, predictions, model, test or export changes.

**No automatic expansion of the enriched COCO pool.** Recurrent localized label,
completeness and representation concerns defeat metadata-only eligibility. This
sample is small-box enriched, not an estimate of whole-COCO annotation quality.
It does not invalidate the existing v3 gate. Preserve accepted24 and all originals.

Next: assess a **reviewed-only proposal54 images** (COCO24 + prior CrowdHuman30)
before deciding conversion. Nominal labels553, including316 small (57.14%), before
cross-pilot duplicate/compatibility checks. Keep source-specific box conventions
explicit (original clipped COCO bbox / reviewed CrowdHuman vbox), person-only
scope and immutable provenance. This is a modest bounded intervention, not a
claim that54 images will solve person recall. First screen/adjudicate between the
two pilots; retained samples must pass the derivative and full joint gates with
all hazard rehearsal and holdouts preserved. Conversion and training remain
unauthorized by these review ledgers. Prepare a single declared experiment only
after the joint data gate, then stop for the user's training-stage boundary.

| Artifact | SHA-256 |
|---|---|
| acquisition.json (raw root) | f41126ee8302471aa1b8e1945eb58be1a92dc6130365bbb18abe56767cfd8776 |
| actual-size-coverage.json | b0409d576b936473346ffa2a5dea6e078b1a0025cfed1c47faeb62d4ec28aa09 |
| artifact-manifest.json (69 source/acquisition/audit/gallery locks) | e5eb9ab6f8378e47f5c4b63bfdb5c214b14170726efaf60d3692d1bb798380c2 |
| review-final-v1.json | e20c030b0ae2f84d3d3f76a7d337573271107b4dd51627cc1d606ee85ae7dfe6 |
| review-artifact-manifest.json (30 review/crop/workflow locks) | 291b33b0c36778dbb4d1447ccf282c5b07496a70834e559b81755b95b39795e4 |

Workflow `acquire-audit-workflow.py` refuses existing raw/report targets; it is
for reproduction to fresh paths, not a resume command. Acquisition/gallery/near
session75415 completedexit0. `crop-workflow.py`, `crop-regions.json` and
`review-workflow.py` retain decision evidence. Acquisition gallery bundle's
NOT_REVIEWED status is historical; separate final ledger is authoritative.
Tests158/158 (6.57s), Ruff result in latest CHANGES; no dependency/code change.


### Reviewed-only proposal now frozen

`reviewed-only-proposal-54-v1.json` SHA
`99f92074cdc73b9bf1885444e0a7574f62807c6c4873b9341038c88738c2d41f`
binds all54 original IDs/images/annotations/review hashes, source conventions,
person=2 scope and joint-v3 split locks. **Cross-pilot screening completed**:
all60 COCO images vs30 accepted CrowdHuman, zero exact/near candidates. This
covers accepted24 COCO; existing pilot-internal screens also have zero candidates.
`proposal-artifact-manifest.json` SHA
`f3dc6146d88e65bb98943330f38edad87a2f5ee8c5d176b630f021edf7c0d671`
locks5 proposal/registry/cross-audit/workflow files. No annotation modifications,
conversion or training. Next begins compatibility/provenance decision and separate
derivatives/full joint gate; do not repeat acquisition or completed visual review.
