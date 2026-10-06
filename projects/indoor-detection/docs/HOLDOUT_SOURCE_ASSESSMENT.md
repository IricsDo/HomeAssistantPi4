# Independent holdout source assessment

Owner: OpenAI Codex. Updated: 2026-10-06.
Status: COMPLETED for source assessment; acquisition/admission IN_PROGRESS.
No holdout is approved. V7 remains PLANNED; no detector predictions or training.

## Decision

Advance **FURG Fire Dataset** to a bounded video/label pilot for the fire slice.
It has original video boundaries and existing rectangle annotations, so it is
more practical to assess than another mixed collection with unknown frame IDs.
This selection is based on metadata, not model scores. Reserve the source for
evaluation; do not add its frames to v7 training or validation.

Smoke and person sources below are backups for assessment, not admitted slices.
The shortlist does not yet cover the intended room/doorway domain sufficiently.
Outdoor sources can provide supplemental stress tests, but cannot substitute for
indoor smoke or real camera evaluation. Missing license detail alone does not
reject a research candidate; missing labels/independence evidence still need work.

## Candidates and evidence

| Source | Labels/group information | Decision and remaining work |
|---|---|---|
| [FURG](https://github.com/steffensbola/furg-fire-dataset) | Fire rectangles in OpenCV XML; 23 MP4/XML pairs verified in original repository tree. CC0 file. | **First pilot**. Decode/pair frames, review annotation completeness and box convention, infer event families conservatively, screen all old corpora. Smoke/person remain unknown. |
| [Boreal Forest Fire](https://research.aalto.fi/en/datasets/boreal-forest-fire-uav-collected-wildfire-detection-and-smoke-seg/) | Creator reports manually boxed smoke in subset A, four prescribed-burn events, 4K UAV footage, CC-BY-4.0. | Smoke backup with identifiable events. Use A, not binary-video subset B or SAM masks in C. Outdoor aerial domain, four events only; does not establish indoor smoke/negative coverage. Inspect file manifest/download cost before intake. |
| [AI For Mankind / HPWREN](https://github.com/aiformankind/wildfire-smoke-dataset) | Creator reports VOC smoke boxes, v2 2,192 images, camera/event references; CC-BY-NC-SA-4.0. | Alternative smoke stress slice. Verify actual filenames/event IDs and negatives; clouds collection is separate, not automatically fully annotated negative data. Distant outdoor smoke differs from indoor plumes. |
| [WILDTRACK](https://www.epfl.ch/labs/cvlab/data/data-wildtrack/) | Creator reports full GT on 400 synchronized frames at 2 fps, seven cameras, JSON; public area at ETH Zurich. | Person backup. All synchronized views/event must stay together; seven cameras are not seven independent scenes. Audit projected/full-body box convention, visibility/invalid sentinels and rights metadata. Outdoor dense crowds; no claim of indoor or 200 negative images. |
| [D-Fire](https://github.com/gaia-solutions-on-demand/DFireDataset) | Creator reports YOLO fire/smoke boxes and 9,838 no-hazard images; CC0 collection notice disclaims copyright over underlying images. | Reserve backup only. Repository README does not provide per-image scene ancestry. Prior local download problem is historical, not reverified here. Whole-source reservation plus exact/near and scene audit required; abundant negatives are not proven independent. |
| [Zenodo Indoor Fire Smoke](https://zenodo.org/records/15826133) | Record claims 5,000 labeled indoor images; 200.5 MB ZIP, API license CC-BY-4.0. | **Defer as independent source** until ancestry/overlap checked. Similar size/name to existing IFireSmoke is a warning, not proof of identity. Existing archive is 92,266,502 bytes vs this package ~200.5 MB; different packaging does not prove new scenes. No group IDs documented in record. |
| [EPFL-RLC](https://www.epfl.ch/labs/cvlab/data/data-rlc/) | Indoor three-camera footage, but creator explicitly says frames are not fully annotated; annotations are multi-view position examples. | Defer for direct person detection holdout. Unannotated people would distort recall/FP; indoor appearance does not fix incomplete detection GT. |
| [UniData](https://github.com/UniData-pro/fire-and-smoke-dataset) | Provider advertises 85 boxed videos; public material is a limited preview and full dataset is paid. | Defer full source; no purchase/contact authorized or performed. Preview cannot establish promised group/count coverage. |
| [ONFIRE 2025](https://mivia.unisa.it/onfire2025/index.html) | Organizer uses ignition-index video labels rather than standard boxes; includes reused public sources. | Defer for current box metric. Useful later for temporal alerts, not a ready box holdout. |

Existing Home-fire, IFireSmoke, COCO/CrowdHuman pilots and Roboflow v32 are
development/previously inspected sources, not new independent evidence. A new
version, unsampled adjacent frames or random repartitioning does not resolve this.
The [Home-fire source URL list](https://github.com/PengBo0/Home-fire-dataset/blob/main/dataPath/dataPath.md)
was retrieved; literal `furg`, `steffens`, `dfire`, `hpwren`, `wildtrack` were absent.
This weak text check does **not** exclude common YouTube clips or renamed content.
Pretrained exposure is unknown for all candidates; do not assert absence from COCO
or other pretraining merely because a source is not in our local training index.

## FURG metadata audit actually performed

Pinned repository revision: `6aff09d7baa27425f31d1df685284c26cbffe7af`.
All 23 original XML files retrieved and parsed without running source code:

- 28,049 annotated frame entries, 17,936 fire rectangles, 13,636 empty annotation
  frames; 17 videos have boxes and 6 have none.
- Zero duplicate frame IDs within each XML; zero nonpositive/out-of-bounds boxes
  against the XML's declared dimensions. All 23 match a video path ignoring case.
- Original case differs in `Car2.xml` / `car2.mp4` and `Car3.xml` / `car3.mp4`;
  explicit mapping is required, not platform-dependent basename assumptions.
- Boxes are `(x, y, width, height)` with top-left origin; inspect frame numbering,
  actual resolution, frame count and alignment after video decoding before conversion.
- The tree reports 619,080,679 bytes across all MP4 files. No MP4 downloaded yet.
  XML counts are correlated adjacent frames, not independent examples/events.
  `house1`–`house6`, `case2_*`, `Car*` and related clips need event-family review;
  clip filename alone is not proof that each clip is an independent scene.

No image decode, visual annotation gate, duplicate image gate, camera-domain gate
or holdout admission PASS is claimed. Empty fire annotations are candidate fire
negatives pending review; they do not imply smoke/person absence or completeness.

Evidence under `E:/HomeAssistantPi4/reports/indoor-independent-holdout-source-assessment-v1`:
`retrieval.json`, pinned `furg-tree.json`, original XMLs, licenses/READMEs,
`home-source-urls.md`, `zenodo-record.json`, `all-annotation-retrieval.json`,
`furg-annotation-inventory.json` and `artifact-manifest.json`.
Public metadata/labels only; no credentials or dataset images committed.
Initial display step hit a Windows cp1252 decoding error after successful retrieval;
rerun explicitly with UTF-8 succeeded. Original retrieval receipt preserved.

## Concrete next pilot

1. Bind this decision and pinned video URLs/hashes before retrieval. Acquire one
   positive clip (`case2_house.mp4`) and one no-box clip
   (`non_fire_patrolbot_onboard.mp4`) on E:, using the matching pinned XMLs.
   These are format/completeness probes, not a score-based acceptance sample.
2. Decode video/verify dimensions/frame-index alignment. Use deterministic 1-second
   temporal spacing for audit previews; document actual timestamp/decoded frame index
   rather than assuming XML fps is accurate. Review with GT only, no predictions.
3. Inspect nearby frames for label completeness and source/event families. Check
   exact/near matches against all existing raw/processed/inspected data, including
   Roboflow v32 excluded from training; adjudicate matches and scene-level reuse.
4. If pilot is usable, inventory/reserve the full FURG source and group families
   before selecting holdout frames with seed 48. Never place adjacent/cross-view
   frames into development. Stop/defer any unresolved overlap/completeness group.
5. Assess smoke/person metadata next, prioritizing indoor-compatible evidence;
   record gaps explicitly. The planning targets of 30 groups/300 fire/300 smoke/
   500 person/200 negatives per class are **not met yet**. Do not manufacture group
   independence by counting frames/cameras or silently downgrade coverage targets.
6. Freeze admitted membership/scopes/hashes and evaluation protocol before any
   v7 training or holdout inference; follow INDEPENDENT_HOLDOUT_PLAN.md.

This milestone selects an acquisition pilot, not a model or release. The old v6
test remains closed, v7 readiness unmet, and NCNN export closed.
