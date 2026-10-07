# Detectium provenance decision and next source intake

Owner: OpenAI Codex. Updated: 2026-10-07.
Metadata follow-up COMPLETED; independent holdout intake IN_PROGRESS.
This supersedes the pending class-definition step in DETECTIUM_IOT_PILOT.md.
Preserve that frozen pilot document and receipts; no images/labels converted.

## Resolved source classes

The original public Kaggle version6 file
`real_images/real_images/real_fire/data.yaml` reports `nc: 2` and
`names: ['fire', 'flame']`: source0=fire, source1=flame.
Its relative train/val/test paths do not describe the observed flat images/labels
layout; do not use this YAML directly as a training configuration.

The [paper](https://arxiv.org/html/2511.02495v1), section3.1 and appendixB.2,
defines the task as fire-region bounding boxes; its IoT table describes controlled
demos. Together with the twelve reviewed pilot overlays, this supports a proposed
alias of both source classes to canonical fire=1. Keep source IDs in the receipt;
no conversion or dataset admission performed. This is not evidence of smoke/person
annotation completeness or known-negative scope for those classes.

## Bounded provenance follow-up

- Six definition-path probes: actual nested data.yaml succeeded, other five404.
- Thirty more public listing pages, added to prior listing:17,620 unique entries,
  still partial. Of318 IoT metadata filenames,67 images and0 labels listed so far.
  Prior pilot retrieved twelve labels directly; listing absence is not missing GT.
  No additional image pairs or full >100GB archive acquired.
- Caption taxonomy counts:151 lighter,33 candle,3 matches,131 indoor_fire.
  These are metadata tags, not independently reviewed box or event counts.
- Filename prefix `msg5430551134` spans155 images; `video5994592357331242812`
  spans96. Remaining67 prefixes are singleton identifiers. These are family
  hypotheses only; they do not certify251 adjacent frames,67 separate events,
  original capture dates or the number of independent sessions.
- Public creator repository/paper reviewed; original session/capture evidence
  still absent. Publication2025 remains distinct from original data age.

**Decision: defer Detectium as the main acceptance holdout.** Preserve the12-pair
controlled-fire pilot as a diagnostic candidate only. Do not keep acquiring this
source to reach nominal box counts while independence/domain coverage is unresolved.
No holdout admitted, no predictions, no training; v6 NO_RELEASE and v7 PLANNED.

Evidence: `E:/HomeAssistantPi4/reports/indoor-detectium-provenance-v1` includes
bounded protocol, original YAML, public metadata pages, inventory, paper snapshots,
source retrieval/error receipts and decision. Older pilot/source receipts immutable.

## Next source actions

1. Prioritize [FASDD creator](https://github.com/openrsgis/FASDD) ground-camera/CV
   subset for smoke/fire metadata/access and source ancestry assessment. Creator
   links [original dataset DOI](https://doi.org/10.57760/sciencedb.j00104.00103).
   It is a recent2024 DOI/2025 journal collection, not proof of recent original
   footage. Inspect ground-camera filenames, labels and original scene IDs before
   a bounded paired pilot; remote-sensing/UAV data cannot stand in for room coverage.
   DOI could not be opened by the web tool this session; next verify creator-linked
   repository/file access. Do not download the full collection or adopt its training stack.
2. [SCOUT creator toolkit](https://github.com/cvlab-epfl/scout_toolkit) confirms
   outdoor multi-camera person boxes in COCO/individual/MOT formats and sequence
   IDs. Assess exact annotation semantics, capture dates and grouped reservation.
   Both official site/download urllib probes timed out and web returned no text;
   no dataset/terms retrieved, no access denial inferred. Retry bounded metadata
   access, then a small sequence-labelled pilot if available. It supplements person
   public-area coverage; it does not prove indoor/doorway deployment quality.
3. Keep existing holdout targets and per-image/class scopes. Resolve source
   overlap, grouping, completeness and domain coverage before freezing a protocol.
   If targets prove infeasible, revise with evidence before any model predictions.
   No source is admitted by this follow-up; no holdout score or Pi benchmark claimed.

Reference snapshots: SCOUT toolkit commit1acd79513bfcf16aecef1150283af58c8273542e;
FASDD creator commit1419f20b2627d0a3e992cab1a468caffe34f3f36. No provider code run,
packages installed or credentials used. FASDD Unicode console display failed after
successful saved retrieval; ASCII-safe display succeeded, original bytes preserved.
