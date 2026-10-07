# Independent holdout intake protocol (before source selection)

Owner: OpenAI Codex. Original intake proposal below retained. Latest experimental
amendment/freeze: [V7_EXPERIMENTAL_PREPARATION.md](V7_EXPERIMENTAL_PREPARATION.md).
Experimental preparation complete; full independent coverage NOT_MET. No predictions.
The old v2/v6 test is closed for selection. Randomly repartitioning existing
train/validation/old-test images does not produce an independent holdout.

## Admission and freeze

- Assess labeled public sources with original scene/video/sequence IDs and usable
  fire/smoke/person box semantics. Camera data can supplement later; hardware is
  not currently available. Prioritize labels; retain provenance/license or unknown
  license status, without waiting for an ideal all-three-class source.
- Partial labels remain eligible with explicit per-image/class annotation scopes;
  an absent class is not an annotated negative unless completeness is established.
  Face/head alone is not automatically a full-person label. Keep canonical mapping.
- Reserve new sources or entire scene/video groups outside every existing training,
  calibration and inspected-test corpus. No adjacent frames/groups split across
  development/holdout. Check augmentation ancestry and original IDs when available.
- Before predictions, inventory labels/groups and freeze selection seed 48 plus
  deterministic group membership. Assign all frames from a group together. Prefer
  whole-source reservation where IDs/families are uncertain. Record any missing
  provenance/independence evidence as a blocker, not an assumed PASS.
- Planning targets: >=30 independent groups across >= 2 sources;  >= 300 fire boxes,
   >= 300 smoke boxes, >= 500 person boxes; >=200 verified negative images per assessed
  class. Include room/doorway person context, indoor/staged/public-area attributes
  recorded separately, small/occluded targets and confusing backgrounds. These
  are intake targets, not confidence guarantees. If infeasible, revise and freeze
  the protocol **before** model predictions; do not select by model successes.
- Check exact/near image overlap against all existing corpora and source families,
  adjudicate candidates; document crop/mirror/session limitations. Review annotations
  blinded to detector outputs. Keep source box convention and explicit completeness
  decisions; no using model errors to choose which holdout images count.
- Freeze image/label/group/scope hashes and data gate on E:. No large Git artifacts.
  Publish metadata decision and limitations before any v7 training/holdout inference.

## Use policy

Existing validation may calibrate/select the redesigned candidate. New holdout
cannot choose epoch, confidence, ROI, minimum size, source subset or augmentation.
Lock model/thresholds/preprocessing first, then one holdout evaluation and same-slice
smoke baseline regression where smoke annotation and baseline provenance are
comparable. Predeclare gates/negative diagnostics and uncertainty reporting before
opening holdout. Report source/domain metrics; mixed-source performance is not
proof of the real camera domain or Pi throughput.

If holdout fails, close candidate and preserve results. Further redesign requires
new independent evidence; do not repeatedly reuse this holdout to reach PASS.
Already inspected old test can remain a historical regression report, never be
renamed as new independent test. A publicly available source does not guarantee
absence from pretrained model data; record known/unknown exposure separately.

Current sourcing priority (user2026-10-07): recent sources from the rolling last
five years; see RECENT_HOLDOUT_SOURCE_REVIEW.md and AGENTS.md. Original FURG
selection is historical/deprioritized; its reports and source assessment remain
immutable. Zenodo2025 archive pilot completed but NOT_ADMITTED (shared scenes);
Detectium2025 IoT public image/label access and12-pair pilot are complete
(see DETECTIUM_IOT_PILOT.md); NOT_ADMITTED. Original YAML resolves0fire/1flame;
session evidence absent, defer as main holdout. Follow DETECTIUM_PROVENANCE_DECISION.md:
next FASDD CV/SCOUT metadata/access and recent smoke/person coverage. Keep acquisition date/ancestry checks separate from
recent publication date. No model predictions or new training authorized by intake.

Current access/pilot result: HOLDOUT_ACCESS_PILOTS.md. FASDD12-pair pilot has
confirmed oldv32 reuse, NOT_ADMITTED; SCOUT timeout; Boreal original2022 event
metadata complete but download disabled/legacy500. No holdout gate closed.

Latest bounded access milestone: HOLDOUT_READINESS_SOURCING_V2.md.
MultiNatSmoke/AGHRI paired pilots obtained; FURG case2_house confirmed reused,
NOT_ADMITTED. Holdout targets unchanged/unmet. Continuous preparation authorized
until v7 readiness; no training launch. Next original THUD++/smart-factory access.

Latest paired pilots: HOLDOUT_THUD_FACTORY_PILOTS.md. THUD809-label census
and original-checksum Boreal400-image acquisition ongoing; neither admitted.
Factory pilot and old FURG model-house family not admitted main holdout.

## Experimental amendment and freeze2026-10-08 (before predictions)

See V7_EXPERIMENTAL_PREPARATION.md for source decisions and evidence. The original
30-independent-group/300fire target was infeasible with verified accessible sources;
it remains incomplete full acceptance work. For one bounded experiment only,
freeze7conservatively reserved families/4sources,90fire/300smoke/500person boxes,
200verified negatives/class. Actual1403images:97fire/398smoke/567person boxes,
negatives808fire/808smoke/461person.7reserved families are not7proven independent
samples. Unknown original capture dates/license/exposure remain unresolved evidence
gaps; do not infer independence or deployment approval. Whole sources reserved.
Recall/F1/guardrails unchanged. Model selection remains existing validation only;
new experimental holdout opened once after candidate lock. Even PASS cannot release.
Freeze3107bindings at E:/HomeAssistantPi4/reports/indoor-v7-holdout-freeze-v1;
SHAaf9065e0abbccabac301d48f0244c8d4ca528928c93ae170b772286af329ff37.
