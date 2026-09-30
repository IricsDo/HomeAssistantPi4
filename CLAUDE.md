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

Do not begin implementation until the current task and ownership are clear.

## 1.1 Current Project Snapshot (2026-09-30)

- Active project: `projects/indoor-detection`.
- Goal: one YOLO26n detector for indoor `smoke`, `fire`, and `person`, exported
  to NCNN for Raspberry Pi 4 4 GB.
- Current branch: `main`.
- Last committed checkpoint: `b07a200 feat: add fully labeled joint dataset intake`.
- Current owner: OpenAI Codex; status is `IN_PROGRESS`. If the user asks Claude
  Code to continue, that request is the explicit handover authorization.
- Tests at this snapshot: PASS, 65/65.
- Ruff at this snapshot: PASS.
- The immediate task is dataset intake and audit, not model training yet.

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

1. Inspect the uncommitted downloader before keeping or revising it:
   `projects/indoor-detection/scripts/download_roboflow_dataset.py`.
2. Use the complete raw extraction at
   `E:\HomeAssistantPi4\raw\fire-smoke-human-v32-clean`.
3. Fix or copy its `data.yaml` so split paths resolve inside that directory;
   the exported file currently says `../train/images`, `../valid/images`, and
   `../test/images`.
4. Run `indoor-prepare-joint` into
   `E:\HomeAssistantPi4\processed\indoor-joint-v1` with source URL, version v32,
   and license `CC BY 4.0` recorded in the manifest.
5. Audit structure, exact/cross-split duplicates, class distribution, negatives,
   and stratified annotation samples before running `configs/train_joint_v1.yaml`.

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
