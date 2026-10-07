# THUD++ and smart-factory public paired pilots

Owner: OpenAI Codex. Updated2026-10-08. Overall IN_PROGRESS; bounded pilots complete.
No source admitted, no model predictions, no v7 launch. Existing targets/gates unchanged.

## THUD++

Original public Zenodo18459791 RGB-D.zip20,037,654,766bytes, CC BY4.0;
2026 release, associated2024 research; original capture dates not yet established.
HTTP206/Content-Range/ZIP CRC enforced. Inventory107,642members via16,240,984bytes.
Real store contains **two captures**, Capture_1(360labels), Capture_2(449labels),
809total paired RGB/LabelMe JSON. Synthetic Gym/Office excluded. Do not count809
independent events or assume two captures mean independent physical scenes.

Seed48 six image/JSON pairs fixed before retrieval,12members11,113,350raw bytes,
25,809,993network bytes. All decode960x540 and label dimensions match. Two valid
People rectangle boxes across six frames. All6 visually reviewed: real convenience
store, checkout/aisle view, blur; no room or actual mounted-camera equivalence claim.
Embedded JSON PNG pixel-identical to corresponding separately acquired RGB for6/6.
Labels for other classes do not establish smoke/fire completeness.

Full809-label census is a separate ongoing job, with image extraction from source
imageData. Its first script mistakenly used flat stems for two captures and overwrote
same-named downloaded candidate files. Existing training data was unaffected. Original
flat candidates preserved; recovery verifies label ZIP CRC and creates capture-qualified
paths. Initial/first resume requests failed short range; bounded three-attempt range
reader now reads all chunks and verifies response length/CRC. No partial acquisition
is an admission gate PASS. Census metadata/group correction recorded separately on E:.

Full creator collection uses identity/contact access; no forms submitted. Public demo
is the candidate, not a claim of full-source coverage.

## Smart-factory2024

Original [Sensors paper](https://doi.org/10.3390/s24154786) links public Google Drive
folder1xnZX_fZ6_QU-J1zDmI-AMm07kvAmIuvN. Visible listing only first50paired files per
inside/outside domain; not full inventory. Seed48 frozen indices17,28,41per domain,
six images/six VOC XML acquired. Public virus-scan download confirmation followed;
no account, contact or terms submission. All decode, geometry/dimensions valid:
15fire/8smoke boxes. Six overlays reviewed blinded to model output.

**NOT_ADMITTED main holdout**: inside17 depicts molten metal/sparks with ambiguous
fire-hazard semantics, visible person unlabelled; capture dates and original session
ancestry unknown. Other pilot scenes include factory blaze/news views. Release2024
does not establish recent original image age. No automatic expansion or missing-class
negative scope. A valid VOC box does not resolve these content/provenance limitations.

Refreshed all33,849corpus image hashes against registry; six THUD and six factory
pilot images have0exact/0dHash<=5candidates. Limited probe only; not exhaustive
crop/mirror/event proof. Historical test remains closed.

## FURG house-family fallback

A separate bounded old-source exception was frozen after recent access/domain
failures. Six original pinned house clips49,028,587bytes, provisional one related
family. Decode899frames/clip versus900XML, dimensions match, no missing XML for
actual frames;29.97actual fps/XML29, one extra XML tail ignored per clip. Annotation
timestamps2014, not recent capture metadata. All180previews reviewed: **scale-model
houses outdoors**, related house2/3 and house4/5 settings. NOT_ADMITTED real indoor
acceptance holdout. No corpus overlap pass claimed after domain rejection; no further
house-family acquisition. Earlier rejected case2_house remains rejected for reuse.

## Evidence and continuation

Frozen pilot report: E:/HomeAssistantPi4/reports/indoor-thud-factory-access-v1,
manifest65bindings SHA903b434b87b5cec6ce1e2e4e5714b8cc9fe5eaeb05365e873e8092d42a8771b4.
Frozen FURG report: E:/HomeAssistantPi4/reports/indoor-furg-house-family-v1,
manifest378bindings SHAac1f3086a2a6a41a02d74b5fec694b30a435cbe32e314d39b5571fa3035d23a5.
Raw paired pilots and videos under E:/HomeAssistantPi4/raw/holdout-candidates.

Ongoing separate reports: indoor-thud-store-census-v1; indoor-boreal-box-mirror-v1.
Boreal label mirror pinned6ffe9c72bcfac836255c0f4faa0efd5201dd1e62: all4,954labels
match original Fairdata SHA256 and byte sizes. Four prior pilot image names matched
original labels; three original image SHA match, one resized copy excluded from byte
parity. A frozen seed48 original-checksum-required400positive image acquisition
(100per each2022location/event) is underway. No mask-to-box conversion or admission.

Next finish recoverable downloads, audit complete group-qualified paths/geometry,
corpus and internal overlap, then blinded annotation/completeness and scope decisions.
Four Boreal events and one/two THUD captures do not meet30-group intake target.
Any feasibility revision must be explicit and frozen before predictions; no silent
quality-gate change or readiness claim. Complete holdout/protocol and final resource
readiness before v7 can train. One detector; E: artifacts/C:venv; .env untouched.

Primary sources: [THUD original record](https://zenodo.org/records/18459791),
[creator](https://github.com/jackyzengl/THUD-plus-plus),
[FURG pinned source](https://github.com/steffensbola/furg-fire-dataset/tree/6aff09d7baa27425f31d1df685284c26cbffe7af),
[Boreal original metadata](https://etsin.fairdata.fi/dataset/1dce1023-493a-4d63-a906-f2a44f831898).
