# V6-768 empirical hazard calibration

Owner: OpenAI Codex. Status: COMPLETED. User approved execution on 2026-10-06.

## Frozen protocol and stop conditions

Root: `E:/HomeAssistantPi4/reports/indoor-v6-768-exact-hazard-calibration-v2`.
Protocol SHA `e9d4ddb897a57f8d7ca59f49fa0bad3594b86327fb81d1b60c11f2aceeed1943`.
This is the diagnosed implementation correction below; v1 outputs stay immutable.
V2 started21:48:34, actualPID3068/launcher24340; completed21:53:42, exit0.
No job remains. Root contains finalized summary, integrity and validation candidate.
Do not relaunch into existing output. Receipt/log/process together describe state.

- Same frozen v6 best, joint-v4 validation membership/labels/scopes, 768 square,
  batch16, GPU0, candidate confidence .001, maxdet100, IoU .50, one unscored warmup.
- Freeze implementation/checkpoint/data/reference hashes; verify all81 comparison
  artifact bindings and21 preparation bindings before and after execution.
- Extract all candidate predictions for each hazard once. Build exact recall curve
  with the existing confidence-descending greedy matcher; equal scores stay grouped,
  inclusive confidence >= threshold. Choose highest observed score meeting .90.
  Independently rematch the point and confirm with another inference pass.
- Fresh candidates must reproduce original v6-768 operating TP/FP/FN and negative
  alarms exactly. Image/ground-truth identity must equal original reports. Drift
  causes failure rather than a retry or replacement of historical results.
- Person checkpoint/threshold .34934934934934936 and report remain unchanged;
  no label removal, minimum size or ROI. No new training, test inference or export.
- Conservative intervention guardrails declared before results: precision drop
  <=.01 and negative-image alarm-rate increase <=.01 versus original hazard
  thresholds. These govern this calibration intervention; they are not additional
  release gates or evidence of acceptable real-camera alert frequency. Stop on
  violation/unattainable recall; report the trade-off, no automatic retry.

This empirical curve replaces interpolation only for this explicitly declared
hazard operating-point decision. Historical interpolated calibration results stay
unchanged and are not silently reported as passing. Validation selection remains
development evidence; test/regression checks and Pi deployment gates are separate.

## Implementation and validation

`src/indoor_detection/threshold_calibration.py` reuses `match_detections`;
`scripts/calibrate_exact_hazards.py` owns immutable receipts and confirmation.
The curve exploits confidence order: lower-score boxes cannot alter higher-score
assignments with fixed candidates/NMS. It is not a sweep of changing prediction
calls. Unit tests compare every point against independent matching, including
ties, overlapping boxes, negatives, invalid/ineligible inputs and unreachable recall.

Camera plan: approximately 4 m or higher, room/doorway priority. Actual tilt,
distance, ROI and minimum projected person size await deployment. Check elevated
views, occlusion and frame edges with real images before any coverage filtering.

## Diagnosed implementation correction

V1 protocol SHA `e4e5d0b41ddf09ad8f75b0e06a0d489a4caac2a98492044d463501972a0b1e81`.
Started21:44:51, actualPID5588/launcher39596; FAILED21:46:39 after smoke extraction.
The new calibration input check incorrectly required positive area for predictions.
Five smoke candidates clipped at image boundaries have zero width, confidence
.00102–.00226; all ground-truth boxes have positive area. Existing matcher assigns
these predictions IoU0 and counts them as FP. The correction preserves them asFP;
regression confirms this. No dataset or matcher semantics changed.

V2 binds the preserved smoke candidate JSON SHA
`fda4a8ba09136b5678a65f0e3c55e8599830aae8bb425afa9cf443114f73346a`,
reuses that extraction and confirms with new inference; fire extraction is new.
Original protocol/FAILED receipt also bound. This is a diagnosed code correction,
not an automatic model retry. V1 root is preserved; no refreshed historical hashes.

## Confirmed results and next decision

| Class | Locked validation threshold | Precision | Recall | F1 | Decision |
|---|---:|---:|---:|---:|---|
| smoke | .1860014796257019 | .785569 | .900932 | .839305 | PASS |
| fire | .42607951164245605 | .886115 | .900158 | .893082 | PASS |
| person (unchanged) | .34934934934934936 | .685756 | .621743 | .652182 | PASS |

Smoke: TP773/FP211/FN85, versus772/211/86 at the original square threshold.
Fire: TP1136/FP146/FN126, versus1133/142/129. Smoke precision increases .000218;
fire decreases .002512 (0.2512 percentage points), within the frozen .01 limit.
Negative-image alarm counts unchanged: smoke31/990 (3.13%), fire13/616 (2.11%).
Both intervention guardrails PASS. Person negative alarm rate remains13.34% on
the COCO scope; hazard calibration does not repair it or prove indoor performance.

Independent inference reproduced selected-point TP/FP/FN and negative alarms
exactly; fresh candidates reproduced original operating counts. Image membership/
ground truth identical; all frozen bindings,81 comparison and21 preparation
bindings verified; no workflow traceback/NMS timeout. Integrity PASS.
Manifest includes96 artifacts (including JPEG galleries and external reused smoke
candidate JSON), SHA `26dd7725f3d394951cc9c227d1fa779b7f72e060b1c0de462d5b209000b9674c`.
`validation-candidate.json` SHA
`87330384727fd673031a383b9cdad38848bb126e06962989659bb9fb5252e4bb`.

**Validation class gates PASS; release remains unapproved.** This is a validation
candidate at768, not a final Pi resolution. Prepare the final test protocol with
these thresholds/checkpoint/preprocessing fixed; establish the same smoke test
slice and baseline protocol before evaluating the <=.03 regression requirement.
Document prior v2 test use. No threshold/epoch selection on test, new training,
test inference or export in this milestone. Do not rerun completed calibration.
The very narrow margins above .90 and person F1 above .65 are measured point
estimates, not confidence bounds or guarantees on new camera scenes.

Tests181/181 PASS9.94s; RuffPASS. Full command from project:
`.venv/Scripts/python.exe -m pytest -p no:cacheprovider --basetemp C:/Users/Public/Documents/indoor-threshold-20261006e`.
Build not applicable; typecheck not configured. No dependencies changed.
