# Person data strategy for Camera Module 3 Wide

Updated: 2026-10-05. Owner: OpenAI Codex. Status: IN_PROGRESS.

## Decision and scope

The user authorizes evaluating additional labeled person datasets, including
outdoor/public-area sources. The Leo Ueno dataset is a reference candidate, not
a required choice. Prioritize new-source assessment before committing to a
sampling intervention. Sampling remains optional and cannot add missing scenes.
Keep one YOLO26n detector, canonical smoke=0/fire=1/person=2, class scopes,
the current frozen validation/test membership, and the existing quality gates.
No dataset in the shortlist below has been approved or downloaded in this milestone.

Outdoor person images are eligible training data. Indoor/outdoor is a context
attribute, not a different output class. Similar body appearance can transfer,
but target performance is not guaranteed: lighting, background, pose, scale,
viewpoint and occlusion may differ. Domain-shift research supports checking these
attributes; it does not quantify this project's outdoor-to-indoor performance.
[Primary research](https://arxiv.org/abs/1803.03243).

Our existing COCO person source already includes outdoor scenes. Adding images
only because they are outdoor is not sufficient; the new source must add useful
coverage or better annotations. Do not infer annotation-error prevalence from
the deliberately error-biased training review queue.

## Confirmed camera target and implications

User-specified camera: **Raspberry Pi Camera Module 3 Wide**, Sony IMX708,
approximately 12 MP, phase detection autofocus. Manufacturer specification:
4608 x 2592 sensor pixels, diagonal/horizontal/vertical field of view
120/102/67 degrees. The user has not specified NoIR or confirmed accessible
hardware for integration. Do not assume night vision or hardware availability.
[Official product brief](https://datasheets.raspberrypi.com/camera/camera-module-3-product-brief.pdf).

Engineering implications to check, not measured results:

- Broad coverage makes distant people occupy fewer input pixels relative to a
  narrower view with the same framing conditions. Inspect center and edge cases;
  measure lens distortion with real frames rather than assuming a fisheye model.
- Sensor megapixels are not detector input resolution. For an uncropped 4608 x
  2592 frame letterboxed to 512 x 512, scale is 512/4608, giving a 512 x 288 image
  region plus padding. A 90-pixel-tall source person becomes about 10 input pixels.
  This example is geometry, not a claimed minimum detectable size or selected
  capture mode. Actual video mode/crop may change field of view and pixel scale.
- Favor seated, bending, partly occluded, near-edge and distant people as well as
  standing pedestrians. Include person-negative indoor backgrounds, screens,
  posters/reflections and low-light scenes for the target-domain check.
- Autofocus/HDR do not prove detection quality or latency. Capture mode, focus
  behavior, exposure and preprocessing require later hardware validation.

The user confirms installation height/tilt and distance are not yet determined.
Day/night illumination and exact camera variant also remain unspecified.
These do not block source research; do not assume mounting geometry.
P5 remains blocked until hardware is available for actual integration/benchmarking.

## Candidate shortlist: metadata assessment only

| Candidate | Potential contribution | Risks and next decision |
|---|---|---|
| CrowdHuman, original source | Dedicated person annotation; occlusion and crowded scenes; separate head, visible-body and full-body boxes | First inspect annotation policy and representative train examples. Choose one compatible box convention; never treat all three boxes as three people. Verify ignore-region support, completeness, scale and download access. Dense crowds may differ from home occupancy. Not selected yet. |
| Leo Ueno People Detection | Aggregates sources with varied scenes/cameras, including security-camera data | Reference alternative. Inspect exact version, individual source provenance and person aliases. Head/face/group labels are not automatically whole-person boxes. Audit duplicates and augmentation ancestry. Not selected from its published metrics. |
| WiderPerson | Author paper describes diverse pedestrian scenarios beyond traffic | Backup candidate. Official landing page was inaccessible through the web tool in this session; acquisition/schema/ignore policy remain unverified. Do not replace missing primary evidence with an arbitrary mirror. |
| Additional COCO train images | Existing converter/provenance, no new label format | Useful only if unsampled training images add missing coverage. Exclude all current holdout overlaps and resolve source crowd/annotation-policy questions before treating more COCO as a remedy. |

CrowdHuman has 15,000 training images and head/visible/full-body annotations.
This is a reason to inspect it, not proof it fits our camera or improves YOLO26n.
[Original dataset](https://www.crowdhuman.org/),
[author paper](https://arxiv.org/abs/1805.00123).

The Roboflow project lists many class aliases and an RF-DETR NAS model; the
displayed metrics are not a directly comparable person-only YOLO26n benchmark.
Version 12 lists 17,401 images and three augmented outputs per training example,
so do not count every output as independent scene coverage.
[Project](https://universe.roboflow.com/leo-ueno/people-detection-o4rdr),
[version 12](https://universe.roboflow.com/leo-ueno/people-detection-o4rdr/dataset/12).

WiderPerson metadata is supported by the authors' paper; access is still pending.
[Author paper](https://arxiv.org/abs/1909.12118).

## Intake and comparison protocol

1. Read original schema and annotation instructions before conversion. Record
   source URL/version, terms/license metadata (including missing information),
   access requirements, box definitions, crowd/ignore handling and class aliases.
   Prefer usable labeled data; do not wait for perfect domain or metadata coverage.
2. Inspect a reproducible, bounded set of training images selected without model
   score filtering. Record seed/IDs and limitations. Include available pose,
   scale, lighting, occlusion and camera-view variation. Do not claim this sample
   certifies every annotation or proves real-camera generalization.
3. Reject or defer a source if person semantics cannot be reconciled, visible
   people are routinely unlabelled, or ignore regions cannot be handled safely.
   Whole-class masking does not solve missing person instances inside person scope.
   Any repaired labels belong in an explicit derivative with review provenance.
4. Download candidate artifacts only under E:\HomeAssistantPi4. Preserve source
   files and hashes. Separate augmentation families/video sequences before any
   new split; exact hashing alone does not establish near-duplicate independence.
5. Audit exact/near duplicate conflicts within the candidate and against existing
   data, especially frozen holdout. Exclude overlapping training examples and
   document methods/coverage. Do not run test predictions for candidate selection.
6. Build a new processed corpus with unique indexes, person-only class scope for
   the added source, and retained smoke/fire rehearsal. Audit structure, class/box
   distribution, annotation and provenance. Do not silently change the existing
   corpus or use published aggregate metrics as an intake gate.
7. Predeclare a bounded training comparison: source counts/selection, initialization,
   seed, optimizer, resolution, epochs, class masking, augmentation and stop
   conditions. Change one intervention at a time; sampling is not mandatory.
8. Judge improvement on the same frozen validation protocol at deployment size,
   including person F1 >= 0.65 and recall >= 0.60 and hazard gates. Report small
   persons, negative-image alarms and source slices. Extra-source validation can
   be reported separately; do not mix it into old validation and claim a fair gain.
9. Reserve a separate indoor camera evaluation protocol for P5; collect and split
   by recording session/scene before model selection. Lock thresholds/checkpoint
   before the final camera test. Existing mixed-domain validation alone cannot
   establish indoor release quality.

## Immediate continuation

- Inspect CrowdHuman annotation/access policy and train previews first; compare
  with the reference Roboflow source before selecting an acquisition.
- Preserve current source-box review: 42/56 images have provisional visual notes;
  suspected duplicate/completeness issues require comparison with original COCO
  annotations. No final box gate or weighting approval has been issued.
- Choose new-source intake, verified sampling, or a justified combination from
  evidence; freeze/audit the chosen intervention before P2. No training now.

## Conditional head/face fallback and future fall detection

User suggestion (2026-10-05): if person quality cannot be sufficiently improved,
evaluate a supplementary face/head detector; after this project, extend to fall
detection. Record these as a conditional fallback and future project respectively,
not as implementation tasks or new release requirements for P1-P6.

`person` does not mean only unobstructed full-body images are valid. Partial people
can be labelled under the source's documented person-box convention. Amodal
full-body, visible-body and head boxes are different targets; do not silently mix
them. Finding heads can support presence but cannot reconstruct reliable full-body
ground truth or substitute for the current person's box quality metric.

Head cues have supported occlusion robustness in published pedestrian models,
but this does not establish a gain for our YOLO26n/Pi pipeline.
[Primary research](https://arxiv.org/abs/1911.11985).
My engineering preference is to investigate head before face for general presence:
rear/profile views may show a head without a visible face; head/face regions have
fewer pixels than the body after resize. Neither cue is guaranteed visible.
This is detection, not face recognition or identity tracking.

Before a fallback experiment, document remaining failures after bounded person
interventions and distinguish body localisation quality from presence/event
quality. Compare (a) an additional head output in one detector and (b) a separate
head model with explicit scheduling; neither architecture is selected now. The
current one-detector/three-class contract stays active. A model triggered only
by a person detection cannot rescue cases where person detection is absent;
design any rescue schedule and benchmark its total Pi latency/RAM separately.

If implemented later, use compatible head-labelled data with explicit scopes,
head/body association and duplicate suppression. Recalibrate the resulting
presence policy and measure false alarms, including faces/heads on screens or
posters, and misses. Report person metrics unchanged alongside separate head
and fused-presence metrics; do not declare the person gate passed by relabelling
head outputs. Any gate/API/architecture revision must be explicit and reviewed.

Fall detection is an event over time, not simply a person bounding box becoming
horizontal. A future design should compare temporal body geometry/tracking and
pose-based sequences, with seated/lying/bending activities as non-fall examples.
Pose sequences are an established research approach, not a selected architecture
or a Pi performance promise.
[Primary research](https://arxiv.org/abs/2107.14633).
Future work must define event-level recall/false alarms, time to alert, occlusion,
multi-person association, camera geometry and subject/session split policies.
Head-only presence cannot supply all body-pose information. Preserve reproducible
timestamps, event schema and camera/preprocessing provenance now; collect new
video and benchmark compute during a separately scoped extension after P1-P6.
