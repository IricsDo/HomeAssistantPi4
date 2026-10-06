# DetectiumFire IoT access and paired-data pilot

Owner: OpenAI Codex. Updated: 2026-10-07.
Public access/paired-data pilot COMPLETED; holdout admission remains IN_PROGRESS.
No training, model predictions, joint conversion or holdout acceptance.
This is the continuation of RECENT_HOLDOUT_SOURCE_REVIEW.md; preserve its frozen receipt.

## Verified access and provenance

- [Creator GitHub](https://github.com/ZixuanLiu4869/DetectiumFire) points to Kaggle.
  Anonymous Kaggle search/view/file APIs resolve the published opaque link to
  [yimengfuyao/detectiumfire](https://www.kaggle.com/datasets/yimengfuyao/detectiumfire).
  Metadata reports public version6, updated2025-10-22. Original capture dates unknown.
- Version6 view reports102,868,503,861 bytes, while search reports102,564,334,853.
  These are different API metadata snapshots/representations; no full archive was
  downloaded. Avoid a >100GB download when individual image/label access works.
- Real paired files are under `real_images/real_images/real_fire/images/` and
  `labels/`; the shorter GitHub illustration is not the actual Kaggle export path.
  Initial shorter-path probes returned404, not evidence that the source was private.
- Metadata listing is partial:58 paginated follow-ups plus first page returned
  11,800 entries before reaching real_images. Page size1000 was capped at200.
  This is not a complete source-file census or proof all318 IoT pairs are present.
- Creator metadata remains revision `ef4a092c2109c086435ba117a342efe1bce70c66`.
  IoT318 entries have only image/source/fire_prompt/fire_type, all unique filenames
  and pre-`.rf.` stems. No session IDs or capture dates; unique filenames are not
  unique scenes. Captions do not establish smoke/person annotation completeness.
- Kaggle names CC-BY-NC-ND-4.0, while the [paper's IoT table](https://arxiv.org/html/2511.02495v1)
  names CC-BY-NC-SA-4.0. Record this unresolved discrepancy; do not claim confirmed
  redistribution/model-release rights or discard the candidate merely for missing
  metadata. No external contact, signed agreement or purchase performed.

## Frozen pilot and actual audit

Before paired retrieval, froze seed48 selection: six sorted-population samples
from `iot_device_detectium` and six from `iot_device_dubai`. Retrieval version6;
per-file cap5MB and total cap60MB. Actual24 files total543,043 bytes. Public HTTP
only; no `.env`, private key, Kaggle account or provider code execution.

Original pairs: `E:/HomeAssistantPi4/raw/holdout-candidates/detectium-iot-pilot-v1`.
Reports: `E:/HomeAssistantPi4/reports/indoor-detectium-iot-access-v1`.
Original labels/images preserved; no normalized dataset written.

- All12 image/label pairs retrieved; all12 images decode. Twelve boxes, no
  nonfinite/nonpositive/out-of-bounds geometry in normalized coordinates.
- Source IDs are **1 for all six Detectium boxes and 0 for all six Dubai boxes**.
  Both cohorts visually enclose flames. Do not assume0=fire/1=smoke from other
  datasets: source taxonomy/alias policy is unresolved. No automatic remapping.
- Reviewed all12 GT overlays: Detectium shows small hand-held lighter demos,
  often with visible people; Dubai shows multiple frames in a shared industrial
  setting. These are controlled/staged contexts, not confirmed home-fire coverage.
- Repeated room/camera/event contexts are visible. Twelve frames and two origin
  tags do not imply12 or two independent event groups. No group count certified.
- Gallery supports a provisional fire-box format/semantics check; no estimate of
  source-wide completeness/label quality or smoke/person negatives. Do not replace
  missing person labels with caption-derived pseudo labels or known-negative scope.

## Independence checks and admission

Screen exact file hashes and the existing64-bit BILINEAR dHash at distance<=5
against current joint-v4 train/val/test and previously inspected raw Roboflowv32.
The registry binds current index hashes and image bytes. Also screen internal
pilot pairs. Registry:33,849 images (24,100 joint-v4 plus9,749 rawv32).
Exact overlap:0 corpus matches/0 internal duplicates. Near overlap:0 corpus
candidates/1 internal pair (IDs0 and3, distance4). Visual review confirms the
same room and lighter-demo context with changed hand/flame position, not identical
pixels; keep together as related scene content, without claiming a session ID.
Dubai frames also share industrial context despite exceeding the hash threshold.
Results are in `pilot-exact-overlap.json`, `pilot-near-overlap.json` and
`pilot-visual-review.json`. Current index hashes remained unchanged.

Coverage is limited to those indexed images; unsampled raw COCO/CrowdHuman,
external web/pretrained corpora, crop/mirror/session ancestry are not exhaustively
covered. Zero hash matches would not prove event independence. Old test image
membership may be screened for leakage, but no predictions/score-based selection.

**Holdout NOT_ADMITTED** until original capture/event grouping, source class-ID
semantics, annotation completeness and adequate target-domain coverage are resolved.
No permission to train follows from successful public access or valid geometry.
V6 stays NO_RELEASE, v7 PLANNED, NCNN export closed. No numeric person cutoff.

## Immediate continuation

1. Check source class definitions/release metadata and source/frame naming to
   resolve0/1 flame labels; do not map a class by numeric ID or caption alone.
2. Inspect the remaining318 IoT metadata candidates for original session evidence
   and original pair availability with bounded public requests. Do not automatically
   download all or claim group counts. Reserve any eventual accepted source solely
   for evaluation, outside v7 train/validation.
3. Choose an admitted group inventory only after blinded label/domain and overlap
   review. If session independence cannot be established, defer this source as the
   main acceptance holdout and retain it as a limited controlled diagnostic slice.
4. Continue recent smoke/person sourcing and retain the30-group/box/negative intake
   targets. Few lighter demos cannot close all three class/domain gates. Freeze
   accepted groups/scopes/hashes/protocol before v7 readiness or model predictions.
