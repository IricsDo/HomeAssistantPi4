# CrowdHuman preliminary assessment

Date: 2026-10-05. Reviewer: OpenAI Codex.
Decision: **ADVANCE_TO_LABELLED_PILOT**, **training_allowed=false**.

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
Selection uses annotations only, not image appearance or detector scores. Images
are still awaiting acquisition and label review; do not confuse these IDs with
the ten HF convenience preview rows.
