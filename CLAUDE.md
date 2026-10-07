# Claude Code Project Instructions

Latest sourcing/readiness milestone (2026-10-08): [HOLDOUT_READINESS_SOURCING_V2.md](projects/indoor-detection/docs/HOLDOUT_READINESS_SOURCING_V2.md).
MultiNatSmoke8 image/mask pairs and AGHRI12 images/22boxes audited;
FURG case2_house rejected for confirmed v32 scene reuse. No holdout admission.
User authorizes continuous preparation until v7 is ready; stop before training.


This file contains Claude Code-specific instructions.

The repository-wide collaboration rules are defined in `AGENTS.md`.
`AGENTS.md` is the source of truth for shared coding, Git, validation,
ownership, and handover rules.

## 1. Required Startup Procedure

At the beginning of every session:

1. Read `AGENTS.md`.
2. Read `CHANGES.log`.
3. Run `git status`.
4. Inspect recent relevant commits.
5. Identify the active task and current owner.
6. Inspect the relevant files before editing.
7. Read `projects/indoor-detection/PROJECT_PLAN.md` and continue the first
   unfinished applicable checklist item; update the plan after milestones.

Do not begin implementation until the current task and ownership are clear.

## 1.1 Current authorized execution (2026-10-06)

- Owner OpenAI Codex; P1b preparation complete; v6 training COMPLETED (12 epochs); validation completed, person FAIL; no running job.
- User explicitly authorized continuation on 2026-10-06; v6 started at 12:13:11 UTC.
  Finished12:51:51 UTC,exit0; no training job. Best inline epoch10.
  Training PID34596 is historical; do not relaunch.
- Joint v4 now24,100 images:15,502 train/4,301 val/4,297 test. Reviewed-only54
  added (COCO24/CrowdHuman30),553 boxes including316 small. Full automated audit,
  conversion parity and inherited/new visual data gate PASS_WITH_LIMITATIONS.
- All base rehearsal/scopes retained, holdout indexes byte-identical. No automatic
  source expansion; original source/review evidence remains immutable.
- Config configs/train_indoor_v6_512.yaml: v2 init,512px/max12 epochs,AdamW,
  LR0.00015,seed42,batch18/workers2,all mixing augmentations0. Fixed resources
  follow v5 recovery; no guarantee of person improvement from this modest subset.
- Read-only readiness verification PASS before the single authorized launch.
  Execution status/logs: E:/HomeAssistantPi4/reports/indoor-partial-joint-v4-audit/
  v6-execution-status.json and v6-training.stdout.log / v6-training.stderr.log.
  Do not relaunch, resume, overwrite or retry automatically.
  Evaluation report root E:/HomeAssistantPi4/reports/indoor-yolo26n-v6-evaluation.
  Follow docs/V6_EVALUATION_DECISION.md; person F1/recall0.6375/0.5618 FAIL,
  smoke/fire recall0.9138/0.9049 PASS. Test/export stay closed.
  Resolution/pretrained baseline stage1 COMPLETED, six configs, exit0 at21:29:40 local.
  Root E:/HomeAssistantPi4/reports/indoor-resolution-baseline-square-v2; no running job.
  Six square configurations: v6/pretrained at512/640/768; historical512 separate.
  Read docs/RESOLUTION_BASELINE_EVALUATION.md and finalized integrity/manifest.
  V6-768 personF1/R .652182/.621743 PASS; smoke/fireR .899767/.897781 FAIL.
  Pretrained person exceeds v6 at all resolutions; this is diagnostic, not a causal proof.
  Exact square smoke/fire calibration at768 COMPLETED, checkpoint/person threshold
  fixed; root E:/HomeAssistantPi4/reports/indoor-v6-768-exact-hazard-calibration-v2.
  V1 failed on a new overly strict check of zero-width clipped predictions; corrected
  to retain them asFP consistent with matcher. Reuse frozen smoke extraction, no
  dataset change or automatic model retry. Preserve reports; do not relaunch.
  Follow docs/V6_EXACT_HAZARD_CALIBRATION.md and execution receipt/logs.
  No job remains; final thresholds smoke.1860014796257019/fire.42607951164245605.
  Smoke/fireR .900932/.900158 PASS; person unchanged PASS. Validation gates PASS,
  not release. Candidate/manifest frozen onE; prepare final test/same-slice smoke
  regression protocol next. No test inference/export/new training in this milestone.
  Latest task: fixed v6-768 final test COMPLETED22:21:58 local,exit0; no job remains.
  Read docs/V6_FINAL_TEST.md. Preparation/readiness PASS; test root onE:
  reports/indoor-v6-768-final-test-v1; logs in indoor-v6-768-test-preparation-v1.
  ProtocolSHA2a866525bb99459e2d42e23608b9335ad02ee65047605c2d81ec8e341a168cfa.
  SmokeR .905992 PASS,personF1/R .675073/.634509 PASS;fireR .849913 FAIL.
  Same-slice smoke recall regression PASS aggregate and both sources, but smoke
  precision/negative alarms worse than baseline. Final decision NO_RELEASE.
  Do not relaunch or tune thresholds on this test. Export/new training remain closed.
  Fire train/validation diagnosis COMPLETED; read docs/FIRE_RECOVERY_PLAN.md.
  Fire val recall FS .839465 vs home .919003; threshold reduction breaches prior
  precision/negative-alarm guardrails. V7 aligned768 max12 epochs is PLANNED only.
  Source assessment v1 is historical. User 2026-10-07 prioritizes rolling last-five-
  year sources (datasets/code/docs/frameworks); see AGENTS and
  docs/RECENT_HOLDOUT_SOURCE_REVIEW.md. FURG2015-2017 pilot deprioritized, no videos
  downloaded. Preserve original v1 decision/doc/hash receipts; do not rewrite them.
  Zenodo2025 archive pilot COMPLETED but NOT_ADMITTED: shared IFireSmoke scenes
  confirmed despite zero byte/pixel hashes; Detectium2025 original IoT metadata
  assessed (318 entries, no box fields). Public Kaggle version6 paired access
  confirmed;12 original pairs acquired/audited. Read docs/DETECTIUM_IOT_PILOT.md:
  zero exact/near corpus candidates across33,849 images, one internal related
  scene pair. NOT_ADMITTED: source IDs0/1 both enclose flames, semantics/session
  dates/completeness unresolved; lighter demos and repeated industrial context.
  Follow-up COMPLETED: original YAML names0fire/1flame; proposed aliases to
  canonical fire=1, no conversion. Original sessions/dates remain unknown; defer
  Detectium as main acceptance holdout, keep controlled diagnostic candidate.
  Read docs/DETECTIUM_PROVENANCE_DECISION.md. Next: FASDD ground-camera/CV
  metadata/access/ancestry and SCOUT assessment now COMPLETED. Read
  docs/HOLDOUT_ACCESS_PILOTS.md: FASDD12 paired VOC/YOLO pilot, geometry/parity
  PASS,2 confirmed reused rawv32 scenes; NOT_ADMITTED. SCOUT still timeout.
  Boreal full subsetA metadata inventory complete (four2022 events), but download
  service disabled/legacy500; no images acquired. Next bounded alternate access
  or recent original labelled source assessment; do not repeat completed FASDD pilot.
  User authorizes automatic planned continuation without repeated continue prompts;
  keep all admission/readiness/training constraints. Do not repeat completed Detectium public-access pilot.
  No holdout admitted, no train/inference/download job.
  V7 requires independent holdout/data/resource readiness; old test remains closed.
  User scope: room/doorway; distant people outside window not required. No numeric
  minimum or ROI selected; labels/full metrics/gates unchanged. Planned height~4m
  or higher; exact tilt/distance await deployment. Max60 training deferred.
  Read docs/V6_TRAINING_PREPARATION.md and latest CHANGES.
- Existing v5 person quality FAIL; NCNN/test gates stay closed. Hardware unavailable.

### Previous milestone history (2026-10-06)


- Active project: `projects/indoor-detection`.
- Goal: one YOLO26n detector for indoor `smoke`, `fire`, and `person`, exported
  to NCNN for Raspberry Pi 4 4 GB.
- Current branch: `main`.
- Last completed training: v5 512 px, 12 epochs, best checkpoint epoch 7.
- Current owner: OpenAI Codex; v5 evaluation milestone is `READY_FOR_REVIEW`.
  Person explicit F1/recall 0.6415/0.5717 FAIL; smoke/fire recall 0.9172/0.9073 PASS.
  Test/export remain closed; no background job. P1b audit/selection and 60-image
  acquisition completed: 615/1,430 small boxes (43.01%), geometry PASS.
  CrowdHuman review now30 ACCEPT/30 EXCLUDE, accepted small189/397=47.61%;
  exact/near screening against24,046 joint images has zero overlaps/candidates.
  Expansion deferred due unresolved dense-label assignments; no new conversion.
  COCO pilot60 seed46 acquired/decoded,342/415 small boxes (82.41%), geometry
  PASS; all60 galleries/25 crops reviewed:24 ACCEPT/36 EXCLUDE,127/156 small
  (81.41%). Exact/near screens against24,046 corpus images have zero matches
  or candidates. Recurrent label/completeness/representation issues block automatic
  expansion. Next: assess reviewed-only54-image proposal (COCO24+CrowdHuman30),
  now frozen with cross-pilot screening zero matches/candidates; assess annotation
  policy and separate derivatives/full joint gates before any run.
  No conversion/training authorization yet; current source/joint unchanged.
  No automatic expansion/training; see docs/SMALL_PERSON_INTAKE.md.
  Do not resume/relaunch completed v5. See
  docs/V5_EVALUATION_DECISION.md and latest CHANGES for current execution state.
  If the user asks Claude
  Code to continue, that request is the explicit handover authorization.
- Tests at this snapshot: read the latest `CHANGES.log` entry for the current
  count.
- Ruff at this snapshot: PASS.
- V4 person calibration at 512 px gives F1/recall 0.6356/0.5625; explicit
  matching gives 0.6292/0.5593. V2 control at 512 gives 0.6351/0.5432 and
  also fails. The export gate remains closed. Training-only person mining is
  complete. All 105 original images have been reviewed: 56 positive and 35
  negative images accepted for sampling-plan preparation, 14 excluded from
  extra weighting. Box review has provisional notes for 42/56 images, not final
  approval. User now authorizes assessing additional person sources, including
  outdoor/public areas; prioritize this assessment before choosing an intervention.
  Sampling is optional, not a prerequisite for new-source intake. Camera target:
  Module 3 Wide IMX708; mounting geometry is undetermined and hardware access
  is unconfirmed. See `projects/indoor-detection/docs/PERSON_DATA_STRATEGY.md` and
  `docs/V4_EVALUATION_DECISION.md`.
- Head/face supplementation is a conditional user-suggested fallback; fall
  detection is a post-project extension. Neither is implemented or part of the
  current release gate; preserve the one-detector contract pending an explicit
  architecture decision supported by quality and Pi performance evidence.
- CrowdHuman assessment now advances to a labelled pilot: 15,000 train records
  audited, 2,875 pass the conservative no-body-ignore prefilter, ten HF domain
  previews reviewed. Previews lack original ODGT IDs/labels; no box data gate
  passed. Original 60-ID pilot is now acquired/paired (621 boxes), with gallery
  and exact file-overlap PASS against the current 23,498-image corpus. Review is
  complete: 49 accepted/11 excluded, vbox clipped chosen, 49 images/507 boxes
  converted on E:. Near-hash screen's only train candidate is visually unrelated;
  zero holdout candidates, with crop/mirror/session limitations. No whole-source
  approval. Frozen 500-ID expansion is acquired/paired (5,313 boxes), all images
  decode, visible geometry has no flagged issues, exact overlap is zero against
  current corpus plus accepted pilot. All 22 near-hash candidates adjudicated as
  unrelated scenes; crop/mirror/session limitations remain. All 30 annotation
  spot-checks now reviewed: 29 ACCEPT/1 graphic EXCLUDE; no new systematic box issue.
  Converted 499 expansion images/5,303 boxes; 470 were automatically screened,
  not individually visually reviewed. Joint v3: 15,448/4,301/4,297 train/val/test,
  all base images/scopes/hazard rehearsal preserved, holdout indexes byte-identical.
  Automated and visual data gate PASS_WITH_LIMITATIONS; read-only preflight PASS.
  V5 started from v2, completed 12 epochs, with workers 2/batch 18 after epoch 2
  resource recovery. Original prep snapshot remains historical, not execution state.
  See docs/CROWDHUMAN_ASSESSMENT.md for exact paths/hashes/commands.

Read the newest entry in `CHANGES.log` for exact uncommitted files, dataset paths,
checksums, known issues, and next commands. Do not rely only on this snapshot.

## 2. Collaboration with Other AI Agents

This project may be modified by OpenAI Codex, Cody, or other authorized agents.

Treat their committed and uncommitted work as intentional unless there is
clear evidence otherwise.

Do not:

- overwrite another agent's uncommitted changes;
- reset another agent's work;
- rewrite another agent's commits;
- silently take ownership of an active task;
- modify protected files without authorization.

If task ownership is unclear, stop and ask the user.

## 3. Task Execution

When implementing a task:

1. Understand the existing implementation first.
2. Make the smallest coherent change that solves the task.
3. Reuse existing project patterns.
4. Avoid unrelated refactoring.
5. Add or update tests where appropriate.
6. Run relevant validation commands.
7. Update `CHANGES.log` when handing over or when a significant task state changes.

### Active detector conventions

- Preserve the canonical output classes and IDs: `smoke=0`, `fire=1`,
  `person=2`; source class `human` maps to `person`.
- Large artifacts belong under `E:\HomeAssistantPi4`, never in Git.
- Do not use partially labeled fire/smoke corpora to fine-tune the three-class
  model: unlabeled people would be learned as background.
- Treat `projects/indoor-detection/docs/JOINT_DATASET_INTAKE.md` as the current
  data gate and `docs/SMOKE_BASELINE_SNAPSHOT.md` as historical baseline context.
- Do not start training until structural audit, duplicate audit, class statistics,
  and visual annotation spot-checks pass.
- Do not expose the Roboflow key from `projects/.env` in output, logs, commits, or
  handover notes.

### Immediate continuation checklist

1. Use checkpoint
   `E:\HomeAssistantPi4\runs\indoor-detection\indoor_partial_joint_yolo26n_v2\weights\best.pt`.
2. Keep all evaluation authoritative through the class-scoped validator.
3. Preserve the completed source/domain reports and their mixed-domain caveat.
4. Preserve the completed calibration/error reports; do not reopen test for
   further selection.
5. Assess additional person sources per PERSON_DATA_STRATEGY.md; the Leo Ueno
   dataset is a reference, not a required source. Preserve partial source-box
   review and diagnose source annotations before weighting those candidates.
   Choose new-data intake, verified sampling or a justified combination, and pass
   the intervention data gate before training. Keep validation/test frozen,
   every run separate and class scopes enabled.
6. Export NCNN only after the selected edge resolution passes validation and
   its checkpoint/thresholds are locked.

## 4. Handover to Another Agent

When the user indicates that work should continue with another agent,
prepare an actionable handover.

Before handing over:

- inspect `git status`;
- run relevant tests;
- run typecheck/build/lint as applicable;
- identify completed work;
- identify unfinished work;
- identify blockers;
- record active files;
- record branch and latest commit;
- record uncommitted changes;
- append a handover entry to `CHANGES.log`.

Do not claim validation passed unless it was actually run.

## 5. Git Safety

Follow all Git rules in `AGENTS.md`.

In particular:

- never use `git reset --hard` without explicit authorization;
- never force-push without explicit authorization;
- never discard another agent's uncommitted work;
- keep commits focused and atomic;
- do not commit known broken code.

## 6. User Confirmation

Do not unnecessarily ask for confirmation when a task has already been
explicitly handed over to Claude Code.

Ask the user when:

- requirements are materially ambiguous;
- task ownership is unclear;
- a destructive action is required;
- production data/configuration may be affected;
- an architectural decision outside existing conventions is required.

## 7. Priority Order

When instructions conflict, use this order:

1. System/developer instructions and safety requirements.
2. Explicit user instructions for the current task.
3. `AGENTS.md`.
4. This `CLAUDE.md`.
5. Existing project conventions and documentation.

`CLAUDE.md` must not override `AGENTS.md` for shared repository rules.

## 8. Final Verification

Before reporting a completed task:

- verify the actual files changed;
- verify Git state;
- run the relevant validation;
- report failures honestly;
- update `CHANGES.log` when appropriate.

The goal is not merely to produce code, but to leave the repository in a
state that the next agent can safely understand and continue.
