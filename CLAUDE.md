# Claude Code Project Instructions

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

## 1.1 Current Project Snapshot (2026-10-05)

- Active project: `projects/indoor-detection`.
- Goal: one YOLO26n detector for indoor `smoke`, `fire`, and `person`, exported
  to NCNN for Raspberry Pi 4 4 GB.
- Current branch: `main`.
- Last completed training: v4 512 px, 12 epochs, with best checkpoint at epoch 11.
- Current owner: OpenAI Codex; status is `IN_PROGRESS`. If the user asks Claude
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
  and exact file-overlap PASS against the current 23,498-image corpus. Visual
  notes cover 3/60 provisionally; convention/completeness and near duplicates
  remain pending. See docs/CROWDHUMAN_ASSESSMENT.md for review next steps.

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
