# Recent-source review for the independent holdout

Owner: OpenAI Codex. Updated: 2026-10-07. Holdout admission IN_PROGRESS.
This decision supersedes the FURG acquisition priority in the 2026-10-06
HOLDOUT_SOURCE_ASSESSMENT.md. Preserve that historical document and E: receipt.

## Recency policy

User requests priority for sources released/substantively updated within the last
five years. At this review the exact rolling window is 2021-10-07 to 2026-10-07.
Record release/publication, original acquisition/collection and code maintenance
dates separately. A recent mirror, access date or paper using an old corpus does
not establish recent data. Unknown dates remain unknown; no automatic PASS.

Apply to datasets, reference code, documentation and frameworks. Use current
official documentation matching installed versions; do not upgrade dependencies
or change architecture solely for recency. Older sources are possible exceptions
only with a documented continuing value and lack of a suitable recent alternative.
Existing trained corpus/checkpoints are retained; this is a sourcing preference,
not an instruction to delete earlier work or relax annotation/independence gates.

## Revised priorities

| Source / date evidence | Suitability and action |
|---|---|
| [Zenodo Indoor Fire Smoke v1](https://zenodo.org/records/15826133), record publication 2025; acquisition age unknown | **Pilot audited; NOT_ADMITTED**. 200,547,120 bytes/checksum verified. Existing IFireSmoke scenes confirmed in visual pairs; a 2025 record is not evidence of new original footage. No independent remainder established. |
| [DetectiumFire](https://arxiv.org/abs/2511.02495), 2025 release/paper | **Prioritize original IoT image subset for metadata/access assessment** over recycled FIRE/FireNET data and web collections. Local pinned metadata has 318 IoT entries; captions are not bbox labels. Acquire original image+box pairs only after confirming access, group IDs, dates and rights. Fire-only assessment; smoke/person labels unknown. |
| [FASDD](https://github.com/openrsgis/FASDD), dataset link from creator; 2024 DOI/2025 journal citation | Fire/smoke boxed collection; original item ages/group ancestry unresolved. Backup, not immediate full download or proof of independent scenes. Do not copy its conda/MMDetection/Swin stack into this project. |
| [Boreal Forest Fire](https://www.nature.com/articles/s41597-025-05634-0), release/paper 2025, burns collected 2022 | Recent original smoke backup, subset A boxes; only four events and outdoor UAV domain. Supplemental smoke stress data, not indoor acceptance coverage. |
| [MmodalFire](https://www.nature.com/articles/s41597-026-06810-6), 2026 | Recent controlled indoor data, but published labeling is binary fire/non-fire. Defer direct boxed holdout: no ready fire/smoke bbox GT established. Useful potential temporal reference later. |
| [MMPTRACK](https://openaccess.thecvf.com/content/WACV2023/html/Han_MMPTRACK_Large-Scale_Densely_Annotated_Multi-Camera_Multiple_People_Tracking_Benchmark_WACV_2023_paper.html), WACV2023; original workshop2021 | Indoor full-body person candidate. Original release day/collection date unresolved; [creator download page](https://iccv2021-mmp.github.io/subpage/dataset.html) requires signed terms and emailed request. Defer acquisition; no signature/contact authorized or performed. A 2023 paper does not reset original data age. |
| [SCOUT people tracking](https://scout.epfl.ch/), first release2025; [creator toolkit](https://github.com/cvlab-epfl/scout_toolkit) | Recent outdoor person backup; original capture dates/completeness of exact release need verification. Keep all views from a session together; few sequences cannot satisfy many independent groups. Do not confuse with unrelated SCOUT camouflage/driving projects. |
| FURG2015–2017 / WILDTRACK2018 / HPWREN2020 material | Legacy fallbacks, **deprioritized**. No FURG video pilot launch while recent alternatives are being assessed. Prior XML audit remains useful format/provenance history, not current selected intake. |

No full recent source is admitted. Recency cannot solve duplicated scenes, partial
labels, missing IDs or source-domain mismatch. No test/model predictions are used
to choose candidates or images.

## Detectium metadata audit performed

Creator repository [DetectiumFire](https://github.com/ZixuanLiu4869/DetectiumFire),
pinned revision `ef4a092c2109c086435ba117a342efe1bce70c66`.
Downloaded only `image/fire_prompts.json`; 7,549 entries:

- Original IoT provenance tags: `iot_device_detectium`187 + `iot_device_dubai`131
  =318. These tags indicate provenance categories, not 318 independent scenes.
- Older named corpora: FIRE433, Forest-fire373, FireNET485; do not prefer these
  merely because they were republished with 2025 captions.
- Remaining web entries: 5,940. Shared internet clips/augmentation families need
  audit against old corpus; original-source category alone does not prove independence.
- No bbox/boxes field in this caption metadata. Frame/session IDs, capture dates,
  image content, annotation geometry/completeness and overlap have not been checked.

Do not use generated descriptions as ground truth for smoke/person absence.
Prefer real original IoT pairs if usable; exclude synthetic preference data from
claims of real indoor holdout coverage. No provider code/API calls were executed.

Evidence root: `E:/HomeAssistantPi4/reports/indoor-holdout-recency-review-v1`.
Contains retrieval hashes, original metadata, `detectium-metadata-audit.json`,
Zenodo record and bounded acquisition protocol. Large artifacts stay on E:.

## Zenodo pilot results (no detector predictions)

Archive SHA `f5e4b452bc0e74508366b4ce3f62d7479d1a790a7438a1f0ebee145a216d7b6a`;
MD5 matches published `086fbc3b874139276097f4057bc45a3c`. Original archive stored
at `E:/HomeAssistantPi4/raw/holdout-candidates/zenodo-15826133-v1` without extraction.
API transfer initially appeared stalled and its wrapper was interrupted; the child
transfer later completed with a valid receipt. A direct curl fallback timed out at
its low-speed bound with zero payload. No download process remains.

Ignore `__MACOSX` resource forks when inventorying: 5,000 images/5,000 paired labels,
not the misleading 10,000 JPEG-named members. All 5,000 decode successfully. Label
field counts valid; class0 has3,592 boxes, class1 has3,343. Export data.yaml only
names numeric classes and points to Roboflow `object-detection-7qn6l/indoor-fire-smoke/1`.
A seed48 class probe of12 images supports 0=fire/1=smoke, not whole annotation PASS.

Against the existing 5,000 IFireSmoke raw images: zero exact file or decoded-pixel
hash overlap and zero shared basenames, but dHash<=3 yields945 pairs involving455
new images. Eight deterministic lowest-distance pairs visually reviewed all show
shared scenes/content, including reframed/aspect-changed images. The other937 pairs
are not adjudicated; do not label all945 as duplicates. Zero exact matches did not
prove independent scenes. No all-old-corpus or full annotation/geometry audit claimed.

**Decision: NOT_ADMITTED** as independent holdout. Reused scenes are confirmed,
original scene IDs/ages unavailable, and independent remainder is not established.
Do not automatically split out the other4,545 images and assert independence.
No data enters training/validation, no checkpoint/threshold/gate changes.

## Continuation

1. Zenodo pilot completed; defer this source as independent holdout. Preserve the
   original archive/reports. Do not acquire more versions or curate the remaining
   images into a claimed independent set without scene ancestry evidence.
2. Confirm Detectium original IoT image/box access and family metadata using public
   sources; do not contact anyone, sign terms or use private credentials automatically.
3. Audit overlap and label completeness for any usable pilot, then resolve smoke/
   person/indoor coverage. Keep the existing holdout planning targets visible.
4. Freeze admitted groups/scopes/hash/evaluation protocol before v7 readiness,
   training or holdout inference. V6 NO_RELEASE remains; export closed.
