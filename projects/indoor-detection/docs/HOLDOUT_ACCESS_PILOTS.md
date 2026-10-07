# Holdout access pilots: FASDD, SCOUT and Boreal

Owner: OpenAI Codex. Evidence completed across 2026-10-07/08 (Asia/Saigon).
Access/pilot assessment COMPLETED; independent holdout intake IN_PROGRESS.
User authorizes automatic continuation of planned work without repeated continue
prompts. Continue applicable work and record milestones; retain data/readiness gates.
No training, model predictions, dataset conversion, checkpoint or threshold change.

## FASDD original CV pilot

[Creator dataset DOI](https://doi.org/10.57760/sciencedb.j00104.00103) resolves to
ScienceDB dataset ce9c9400b44148e1b0a749f5c3eb0bda. Public metadata: created
2022-07-18, issued2022-08-02, updated2025-09-09, versionV9, CC BY-SA4.0.
V9 total82,125,550,221bytes/six archive files; original CV ZIP12,326,081,298bytes.
Recent release/update does not establish recent original footage.

Public read-only file-tree/search/preview APIs identified the original archive.
Some endpoints failed (numeric version rejected, details access error, root empty);
correct V9 file-tree path and public search succeeded. No access control bypass,
FTP credential creation, account, signatures or contact. No provider code executed.
Browser UI unavailable (no enabled browser surfaces); used public HTTP metadata.

Archive preview141,645,083bytes SHA
4c4e8e03e7df68211f67eaf5e462a9b7efbf0fd45c00e3857061e6d509fcee61.
Contains285,949 files;95,314 images, paired VOC/YOLO and COCO/TDML formats.
Metadata preview initially exceeded10MB/60MB caps; completed under a separately
frozen150MB metadata cap. No full12.3GB payload downloaded. Public range requests
strictly verified206/Content-Range; ZipFile checked original member CRCs.

Seed48 frozen before image retrieval:three sorted-population samples per four
filename categories (bothFireAndSmoke,fire,neitherFireNorSmoke,smoke).
Twelve images plus twelve VOC and twelve YOLO originals:36 files805,002bytes.
ZIP metadata/member transfer41,077,872bytes, excluding preview/site metadata.
All12 decode;23 boxes (16fire/7smoke), source0fire/1smoke confirmed by VOC pairing.
YOLO/VOC count/coordinate parity and XML/image dimensions PASS; zero flagged geometry.
Original paths/IDs retained. No normalized dataset or class scope files created.

All12 overlays reviewed, plus full-resolution smoke10. Building/field/forest fire,
night/demo footage, an indoor controlled flame with a person, smoke plumes and
confusing lantern/car/sky backgrounds. Person labels absent; no person negatives
inferred. Three empty labels are source-declared hazard negatives with no obvious
hazard in pilot review; no whole-source negative/completeness approval.
Smoke10 has a visible narrow plume, physical smoke/steam identity uncertain;
overlay date2017-03-20 is observed old-content evidence, not a verified capture date.

Refreshed all33,849 corpus image SHA256 against existing frozen fingerprints and
verified joint-v4 split index locks before overlap matching. Exact0; dHash64
BILINEAR distance<=5 gives2 corpus candidates,0 internal pairs. Both visually
confirmed shared scenes with rawv32 (pilot0 burning building;pilot2 field fire and
firefighters/watermark). Different aspect ratio/resolution/overlays explain absent
byte hashes. No current joint train/val/test candidates found in this limited probe.

**FASDD NOT_ADMITTED** as independent holdout: confirmed old-corpus scene reuse,
original group/capture ancestry unavailable in numbered filenames/XML and limited
room coverage. Do not assert the other ten images or remaining95,302 independent.
Preserve pilot as diagnostic candidate; no automatic source expansion for main holdout.

Originals: E:/HomeAssistantPi4/raw/holdout-candidates/fasdd-cv-pilot-v1.
Reports/recipes: E:/HomeAssistantPi4/reports/indoor-fasdd-scout-access-v1.

## SCOUT and person fallback

Official site/download HTTP/HTTPS probes still time out. Metadata/toolkit support
outdoor person boxes with sequence IDs, but no original image/label data acquired.
Do not mistake precomputed detector outputs from UMPN for ground-truth annotations.
No complete annotation/independence/domain gate; defer repeated immediate retries.

[JRDB official dataset](https://jrdb.erc.monash.edu/dataset/) fallback checked:
recent pose/social annotations reuse2019 underlying footage; official downloads
require login/account. It is not new original footage merely because labelled2022.
No account created, terms accepted, contact sent or credentials used. Not acquired.

## Boreal original-event metadata

[Creator record](https://research.aalto.fi/en/datasets/boreal-forest-fire-uav-collected-wildfire-detection-and-smoke-seg/)
links DOI10.23729/fd-72c6cf74-b8eb-3687-860d-bf93a1ab94c9,
Fairdata1dce1023-493a-4d63-a906-f2a44f831898. Open/CC BY4.0. DataCite records
four2022 collection days (05-24,06-28,07-06,08-15), issued2025-02-28.
Metax public metadata/file directories inventory succeeds; subsetA9,909 files,
13,069,558,883bytes. Whole dataset125,086,946,035bytes, not downloaded.

SubsetA originals: Evo931,Heinola906,Karkkila1096,Ruokolahti1765 image/label pairs,
plus256 empty-image/empty-label pairs and image_counts.txt. All folder listings
complete; counts/metadata pairing are not content decode/annotation PASS.
Four locations/events, all drone views/adjacent frames must stay together;
4,954 images are not4,954 independent scenes. No room or person/fire scope inferred.

V3 download authorize responds405 `Download is not enabled`; legacy Etsin route
responds500. Earlier wrong-body400/trailing-slash404 are retained as probe history.
No images or actual label bytes downloaded, no download share credentials stored.
Creator web fetch403 but source supports browser search; this is not dataset refusal.
Public metadata/recipes: E:/HomeAssistantPi4/reports/indoor-boreal-access-v1.
**Boreal NOT_ADMITTED: paired access unresolved**, outdoor smoke stress candidate only.

## Automatic continuation checklist

1. Preserve all frozen source decisions/receipts. FASDD pilot acquisition/review is
   complete; do not repeat it or curate a claimed independent remainder from hashes.
2. For Boreal, check creator-published alternate endpoint/service change with bounded
   requests before a frozen event-level paired pilot. For SCOUT, retry only after
   an access change/usable original mirror. Do not repeatedly poll failed endpoints.
3. Continue recent original labelled room/doorway/person and smoke/fire source
   assessment. Contact/account/terms-dependent candidates stay unacquired unless
   separately authorized. Existing label priority and partial-class policy retained.
4. Current admission targets unmet (>=30 groups/>=2sources,300fire/300smoke/
   500person boxes,200verified negatives/class). If infeasible, prepare a concrete
   evidence-based protocol revision before predictions; do not silently lower gates.
5. Freeze admitted sources/groups/scopes/hashes and readiness before v7 launch.
   V6 NO_RELEASE/v7 PLANNED/export closed, no running acquisition/audit/train job.
