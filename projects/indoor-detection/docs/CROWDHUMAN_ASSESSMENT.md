# CrowdHuman preliminary assessment

Date: 2026-10-05. Reviewer: OpenAI Codex.
Current decision: **ADVANCE_TO_BOUNDED_FILTERED_INTAKE**, **training_allowed=false**.
The 60-image review is complete; 49 images are converted. A separate 500-image
expansion is frozen, not yet acquired or approved. Historical milestones follow.

## Policy and access

Official schema distinguishes visible body (`vbox`), inferred full body (`fbox`)
and head (`hbox`). A `mask` tag represents an ignore region; `extra.ignore`
applies to the person/body, while `head_attr.ignore` applies to head. These are
not interchangeable. Optional ignore attributes may be absent.
[Official schema and terms](https://www.crowdhuman.org/download.html).

Our trainer masks unknown classes per image, not spatial ignore regions within
the person class. Dropping ignore boxes while retaining the rest of an image
would turn ambiguous/unlabelled regions into background. For a first pilot,
exclude the whole image if any body-ignore region is present. Do not interpret
head-ignore alone as body-ignore, and do not train all three box types as person.

The official page restricts image use to non-commercial research/education and
prohibits distributing images. Record these terms separately from the HF card's
CC-BY-NC-4.0 tag; do not assume the tag replaces the original image terms.
Images remain outside Git. This project milestone does not approve commercial
deployment or redistribution.

Official Google Drive links failed to fetch through the web tool. The accessible
HF repository is `sshao0516/CrowdHuman`, revision
`d97203da87e348ea69f7a7633a57c21a956120a6`.
Its profile identifies Shuai Shao and links GitHub `sshao0516`; the author's
website links CrowdHuman at `sshao0516.github.io`. This supports provenance but
does not independently certify bytes against an original publisher checksum.
[HF repository](https://huggingface.co/datasets/sshao0516/CrowdHuman),
[profile](https://huggingface.co/sshao0516), [author](https://www.sshao.com/).

## Local annotation audit

Source: `E:\HomeAssistantPi4\raw\CrowdHuman-assessment\annotation_train.odgt`
(80,017,502 bytes), SHA-256:
`6bf241a79f19e30cf52681eab3392368bd5a534164be9272e7a808cb284d9f77`.
Only train annotations were downloaded/read; no candidate val/test acquired.

| Measurement | Count |
|---|---:|
| Train images | 15,000 |
| Non-ignored person boxes | 339,565 |
| Body-ignored boxes, including masks | 99,227 |
| Images containing body-ignore regions | 12,125 |
| Provisionally eligible images without body ignore/invalid body geometry | 2,875 |
| Invalid non-ignored visible/full body geometry | 0 |
| Person boxes whose visible/full coordinates differ | 261,612 |
| Non-ignored person boxes with occlusion flag | 243,879 |

These are annotation counts, not quality metrics. Eligibility is only a schema
prefilter: image bounds, duplicate checks, visible-person completeness, label
convention compatibility and domain coverage are still unchecked. In particular,
no claim is made that the 2,875 images pass the data gate.

Audit code: `src/indoor_detection/crowdhuman_assessment.py`. Reproduce with a new
output filename (the CLI preserves existing reports):

```powershell
.venv\Scripts\python.exe -m indoor_detection.crowdhuman_assessment `
  --annotations E:\HomeAssistantPi4\raw\CrowdHuman-assessment\annotation_train.odgt `
  --output E:\HomeAssistantPi4\reports\crowdhuman-assessment-v2\annotation-audit.json
```

V1 report: `E:\HomeAssistantPi4\reports\crowdhuman-assessment-v1\annotation-audit.json`.
SHA-256 `187ff20e47d994ba3b21004b98d5c065a1ad54dcce154af9aa27e23cc73ef19a`.

## Domain preview and its limits

Downloaded and reviewed deterministic HF train preview rows
0,11,22,33,44,55,66,77,88,99 from its first 100 rows, with no model-based filtering.
Original files, hashes and per-row notes are under
`E:\HomeAssistantPi4\reports\crowdhuman-assessment-v1`:
`preview/`, `preview-hashes.json`, `hf-train-preview.json`, `preview-decision.json`.

Nine previews clearly depict indoor gatherings/venues; one is a sports-team
composite. Several contain seated/occluded people, backs/profiles, artificial
light and small background people. One venue image appears rendered/staged;
authenticity is unresolved. This convenience preview is not a random corpus
sample and cannot establish a dataset-wide indoor fraction or camera match.

HF preview labels are null and original filenames/ODGT IDs are not exposed.
No preview-to-annotation pairing, clean-subset membership or box completeness
was established. Domain preview does not substitute for labelled pilot review.

## Selection and next step

Advance CrowdHuman to a labelled pilot because it has explicit person/occlusion
metadata, inspectable ignore semantics and a provisional 2,875-image subset.
Compared with the Leo Ueno reference, fewer class aliases need interpretation;
its ignore and visible/amodal box differences still require work. No model metric
was used to select this candidate; no assertion is made that it is better data.

Next: acquire original training image members, select a seeded bounded pilot from
eligible ODGT IDs, and overlay visible/full boxes side by side. Verify image
bounds/completeness and choose one convention compatible with existing person
labels. Then perform overlap/duplicate checks against current data and frozen
holdout. Defer conversion if semantics or completeness cannot be reconciled;
compare the reference/backup sources instead. Keep smoke/fire rehearsal and all
quality gates. No new model training, full image archive download, joint corpus
creation or original label edit has occurred in this milestone.

Pilot selection is now frozen: 60 IDs sampled by Python `random.Random(42)` from
the sorted 2,875 provisional eligible IDs. Plan:
`E:\HomeAssistantPi4\reports\crowdhuman-assessment-v1\labelled-pilot-plan.json`,
SHA-256 `00b47f33466af5c0df1167f3982627c794eb8f091cf43ca5c63f3c15c88b95cc`.
Selection used annotations only, not image appearance or detector scores. At
freeze time images awaited acquisition/review; do not confuse these IDs with
the ten HF convenience preview rows.

## Original-image acquisition tooling

`indoor_detection.crowdhuman_pilot` acquires only exact selected training ZIP
members using bounded HTTP Range requests. Each response must be HTTP 206 with
the requested byte interval and stable archive size; reads are capped at 8 MiB.
ZIP member CRC and per-image SHA-256 are checked/recorded. This does not verify a
whole-archive SHA-256 or independently authenticate the original publisher.
No signed redirect URLs are persisted. No new dependencies are needed.

```powershell
.venv\Scripts\python.exe -m indoor_detection.crowdhuman_pilot `
  --plan E:/HomeAssistantPi4/reports/crowdhuman-assessment-v1/labelled-pilot-plan.json `
  --annotations E:/HomeAssistantPi4/raw/CrowdHuman-assessment/annotation_train.odgt `
  --output E:/HomeAssistantPi4/raw/CrowdHuman-pilot-v1 `
  --review-output E:/HomeAssistantPi4/reports/crowdhuman-pilot-box-review-v1
```

The CLI requires a fresh output directory and validates the frozen annotation
hash and pilot IDs before creating it. On interruption, keep the partial output
and receipts; this version does not resume automatically. Use a fresh directory
for a retry. It never extracts arbitrary ZIP paths or modifies source labels.
The gallery displays visible boxes on the left and full-body boxes on the right,
numbered consistently. Boxes are clipped for display only; bounds excursions
and empty intersections are counted separately in `bundle.json`. Amodal boxes
outside the frame are not automatically annotation errors. Neither acquisition
nor gallery generation opens the training gate.

Review policy: examine the frozen 60-image sample and flagged geometry, rather
than manually inspect the entire source. Conversion/class-ID remapping uses
existing labels; there is no requirement to redraw all boxes or label the two
unknown hazard classes in these person-only images. Class scopes remain required.

### Acquisition milestone result (2026-10-05)

- All 60 frozen original IDs acquired and paired with 621 person annotations.
  Images total 33,599,374 bytes; HTTP ranges transferred 34,593,123 bytes across
  the three pinned train ZIPs. No full archive, candidate val/test or model run.
- Original images/receipts: `E:/HomeAssistantPi4/raw/CrowdHuman-pilot-v1`.
- Gallery/reports: `E:/HomeAssistantPi4/reports/crowdhuman-pilot-box-review-v1`.
  Left vbox/right fbox. All 60 images decode and all boxes have valid geometry;
  51 vboxes and 187 fboxes extend outside the image, zero empty intersections.
  These excursions need interpretation, not automatic deletion of amodal labels.
- Exact raw-file SHA-256 check: zero pilot internal duplicates and zero overlap
  with all 23,498 current train/val/test images. Corpus registry:
  `E:/HomeAssistantPi4/reports/crowdhuman-pilot-corpus-hashes-v1.json`.
  Split path fingerprints match the earlier frozen review manifest. Near
  duplicates (including recompressed/cropped versions) are not yet audited.
- Three gallery pairs inspected: outdoor market crowd, outdoor public street,
  indoor seated gathering. Pairing appears correct; visible/full differences
  are evident around occlusion. Notes in `review-progress-03.json` are provisional,
  not completeness/convention approval. Continue 04–60, revisit 01–03 for final
  decisions and inspect tiny/ambiguous cases at original resolution.
- Tests: 132 passed; lint PASS. No new dependencies or changes to original labels,
  source indexes or old unfinished source-box review. Training gate remains closed.

| Artifact | SHA-256 |
|---|---|
| acquisition.json | cac744a7ab4992a0e3739770b3c85d5d40d4d2d56a038a35884c18ce03ea6a4f |
| pilot-annotations.json | 872c4e1fd55fca207d2aeb0eb32664ecaaf510a8400802e74cfe239bc08f566e |
| bundle.json | 212cb3c13c8587ac14b6898d8deac9dc01a6297a067215bbcce7590d073876ae |
| exact-overlap.json | af4dc10d96e6e750d8a0dbc93ee884047ca31320681a3fc4fa87a7c06c4a1a2e |
| corpus hash registry | 88454fa205d927a292af02cf59f7a72ab5dd9bca5fe2634f24bcd0d042c81b99 |
| review-progress-03.json | 38d5ad498d4095607634b503a17f15a6a18586c3ffb1467660493e16de41aa43 |

## Pilot review and conversion milestone (2026-10-05)

All 60 paired galleries were inspected, with original-resolution context/head
crops for small or suspicious cases. Decisions in `review-final-v1.json`:
**49 ACCEPT / 11 EXCLUDE**. The sample contains 34 outdoor, 21 indoor, three
graphic/composite and two uncertain venue images; these counts describe this
seeded pilot, not the whole source or the ten earlier convenience previews.

Excluded gallery numbers: 05 (ambiguous background figure), 15 (ambiguous tiny
overlapping heads), 20/35/51 (graphic compositions), 31/42/47/53/58 (repeated or
inconsistent person assignments supported by original crops/coordinates), and
43 (ambiguous rear-head assignments). No source labels were edited. Number 48's
suspected duplication was resolved as two distinct people behind one another.
Blur alone was not an exclusion rule. Review does not prove exhaustive labels
for every distant person.

Choose **vbox clipped to image bounds**, rather than amodal fbox, for this intake.
The paired review shows fbox extending into hidden legs/background; comparison
with five existing COCO labelled examples, including a bus passenger/head and a
bench sitter, supports matching observed body extent. This is a project intake
decision from inspected examples, not a universal claim about every COCO box.
Head boxes remain diagnostic metadata, never a second person target.

Converted derivative: `E:/HomeAssistantPi4/processed/crowdhuman-reviewed-pilot-v1`:
49 unchanged original images, 507 YOLO boxes with class ID 2, scope `person` in
`manifest.json`. All output labels parse and copied-image hashes match receipts.
This directory has no training configuration; compose a new scoped joint index
with hazard rehearsal and pass its gates before training.

Near-duplicate screen revalidated every corpus file SHA-256, reused the project's
64-bit dHash (9x8 grayscale BILINEAR) and compared all 60 x 23,498 pairs at Hamming
distance <= 5, plus pilot pairs. One train candidate, zero holdout/internal
candidates. Pilot 27 is a posed campus staff group; its matched corpus image is a
rotated close campfire scene. Visual adjudication: unrelated scenes, false positive.
Reports: `near-overlap-v1.json`, `near-adjudication-v1.json`. This screen does not
guarantee detection of crops, mirrors, heavily edited or same-session images.

### Frozen next intake

Automatic approval of all 2,875 provisional images is deferred because the pilot
exposes annotation anomalies. The next bounded intake excludes all 60 pilot IDs
and whole images with invalid hbox or any head-pair intersection/min(area) >= 0.5.
This conservative heuristic may exclude valid close/occluded people; it is not
proof of duplicate annotation and does not repair labels. Among 2,815 remaining
prefilter candidates, 481 are excluded for overlap, zero for invalid heads,
leaving **2,334**. Freeze 500 IDs using `random.Random(43).sample` from sorted IDs.
Freeze 30 visual spot-check IDs with seed 44 before acquisition/model inference.

Plan: `expansion-plan-500-v1.json` in the pilot report directory. Stop joint
conversion if spot-checks reveal a new systematic box/completeness problem.
Review those 30 plus flagged cases; do not require manual inspection of all 500.
Acquisition, duplicate screening/adjudication and the joint data gate remain
required. The reviewed 49 can be retained separately; no images are added to the
current train/val/test indexes yet, and no model training/export occurred.

```powershell
.venv\Scripts\python.exe -m indoor_detection.crowdhuman_pilot `
  --plan E:/HomeAssistantPi4/reports/crowdhuman-pilot-box-review-v1/expansion-plan-500-v1.json `
  --annotations E:/HomeAssistantPi4/raw/CrowdHuman-assessment/annotation_train.odgt `
  --output E:/HomeAssistantPi4/raw/CrowdHuman-expansion-500-v1
```

Programmatic utilities: `audit_near_overlap(acquisition, corpus_registry, NEW_report)`,
`convert_reviewed_pilot(acquisition, review, NEW_output)` and
`freeze_expansion_plan(annotations, annotation_audit, pilot_review, NEW_plan)`.
Fresh output protects existing artifacts. Tests 134/134 and Ruff PASS; no new packages.

| New artifact | SHA-256 |
|---|---|
| review-final-v1.json | 62da8e22f017db5517f5a8bc500c4a4860973230467d6f062c10cacc197bba3a |
| near-overlap-v1.json | ecc1dc9c37a2450a2f764bcf2bba1559ead1710636b434932dd5f294e0fcf04b |
| near-adjudication-v1.json | 7c9efde3dc7603e0d29b1ce9d449ffd5516585ed293095b56f37eff4a1c04a13 |
| converted manifest.json | 652235b771029afeaa2d09903691609fd0944a839eefe402e166ab94ccadddf1 |
| expansion-plan-500-v1.json | 40c186386b12ba58b0d846640ad0be2124d6ddb3daa82703246dfd3f42dec48a |
