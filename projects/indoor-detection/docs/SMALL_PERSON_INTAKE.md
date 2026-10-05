# P1b small-person labelled pilot

Updated 2026-10-06 by OpenAI Codex. **IN_PROGRESS**: annotation coverage audit,
frozen selection and acquisition complete; semantic and duplicate gates pending.
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
