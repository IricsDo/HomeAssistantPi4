# AI Agent Collaboration Protocol

This repository is maintained by multiple AI coding agents, including Claude Code, OpenAI Codex, Cody, and other explicitly authorized agents.

The purpose of this document is to maintain project consistency, prevent agents from overwriting each other's work, and provide reliable handovers between agents.

---

## 1. Project Context

- **Repository purpose:** Multi-project workspace for Raspberry Pi 4 home-assistant
  experiments.
- **Active project:** `projects/indoor-detection` -- unified indoor object detector
  for `smoke`, `fire`, and `person`.
- **Archived project:** `projects/ai-voice-assistant` -- preserved prototype; do not
  mix its dependencies or code into the active detector.
- **Framework / Language:** Python 3.12-3.14, Ultralytics YOLO26n, OpenCV, PyTorch.
- **Runtime targets:** Windows 11 development/training; Raspberry Pi 4 4 GB NCNN
  inference target.
- **State / Storage:** No database. Large datasets, runs, checkpoints, and reports
  live under `E:\HomeAssistantPi4` and must not be committed.
- **Package Manager:** Python `venv` + `pip`; package metadata is in
  `projects/indoor-detection/pyproject.toml`.
- **Install Command:** `python -m pip install -e ".[dev]"` from
  `projects/indoor-detection`.
- **Build Command:** No application build is required during dataset preparation;
  NCNN export is performed later with `indoor-export`.
- **Test Command:** `python -m pytest` from `projects/indoor-detection`.
- **Lint Command:** `python -m ruff check .` from `projects/indoor-detection`.
- **Typecheck Command:** Not configured.

### Latest preparation state (2026-10-08)

- V7 preparation READY_FOR_REVIEW for one bounded experiment; read
  `projects/indoor-detection/docs/V7_EXPERIMENTAL_PREPARATION.md` and latest CHANGES.
- Experimental external set1,403images frozen outside unchanged joint-v4.
  Intake targets explicitly amended before predictions; original30 independent
  groups/300fire target NOT_MET. Preserve quality gates and deployment closure.
- 768/batch8 in-memory resource probe PASS; no optimizer step or training launch.
  User requested stop at train-ready preparation. Do not launch without a later request.
- Preserve frozen E: reports/manifests and source bytes; do not regenerate them in place.

### Current delivery constraints

- Keep one detector and one inference pass for all three target classes.
- Do not split fire, smoke, and person back into separate projects unless the user
  explicitly changes the architecture decision.
- Prioritize Raspberry Pi 4 memory and latency; training may use the Windows laptop
  GPU, but deployment assumptions must remain Pi-compatible.
- Smoke detections must not be rejected solely because an image is blurred.
- Camera integration and real Pi benchmarking remain out of scope until the user
  provides the hardware.
- Target camera is Raspberry Pi Camera Module 3 Wide (IMX708, ~12 MP, autofocus).
  Planned mounting height is approximately 4 m or higher (user, 2026-10-06);
  exact height, tilt, distance, ROI and accessible hardware remain unconfirmed. Outdoor person
  data is eligible after assessment; follow projects/indoor-detection/docs/PERSON_DATA_STRATEGY.md.
- User-confirmed person coverage prioritizes the room and doorway; very distant
  people outside the window are not required. No numeric minimum box size or ROI
  is selected yet. Preserve full validation metrics, labels and existing gates.
- Never print or commit `projects/.env`; it contains the Roboflow API key and is
  already covered by `.gitignore`.
- Prioritize datasets, reference code, documentation and frameworks released or
  substantively updated within the rolling last five years (user, 2026-10-07).
  Check original release/data age separately from mirror upload/access dates;
  a new paper or packaging does not make old data new. Older sources require a
  documented reason that they remain useful and no suitable recent alternative
  was found. This preference does not authorize unrelated dependency upgrades or
  invalidate existing audited datasets/checkpoints. Reassess FURG before intake;
  its 2015-2017 material is a legacy fallback, not the default pilot.

Agents MUST use the existing project stack and conventions. Do not introduce alternative frameworks, package managers, or architectural patterns without explicit authorization.

---

## 2. Universal Coding Standards

### Type Safety

- Use strict TypeScript when TypeScript is used.
- Avoid `any`.
- Prefer explicit interfaces/types where appropriate.
- Do not suppress type errors without documenting why.

### Architecture

- Follow the existing folder structure.
- Reuse existing utilities, components, services, and abstractions.
- Do not create redundant utility or component folders.
- Do not reorganize unrelated code while implementing a task.
- Preserve established architectural conventions.

### Error Handling

- Handle expected errors explicitly.
- Do not silently swallow errors.
- Preserve useful error information for debugging.
- Use the project's existing error-handling conventions.

### Code Quality

- Keep changes focused and task-oriented.
- Avoid unrelated refactoring.
- Prefer simple, maintainable solutions.
- Match existing naming and formatting conventions.
- Do not optimize prematurely.

---

## 3. Agent Identity

Every agent MUST identify itself in handover records as one of:

- Claude Code
- OpenAI Codex
- Cody
- Other explicitly authorized agent

Handover records MUST include the agent identity.

---

## 4. Task Ownership

Only one agent should actively own a task at a time.

Before modifying code, an agent MUST determine:

- Current task
- Current owner
- Task status
- Active files
- Relevant previous work

An agent MUST NOT modify files actively owned by another agent unless:

1. The task has been explicitly handed over, or
2. The user explicitly authorizes the change.

### Task Status

Use one of:

- `PLANNED`
- `IN_PROGRESS`
- `BLOCKED`
- `READY_FOR_REVIEW`
- `COMPLETED`
- `HANDED_OVER`

---

## 5. Git Collaboration Rules

Before starting work:

- Run `git status`.
- Inspect recent relevant commits.
- Read the latest `CHANGES.log` entries.
- Check whether another agent has active/uncommitted work.

Rules:

- Never use `git reset --hard` without explicit authorization.
- Never force-push without explicit authorization.
- Never rewrite another agent's commits.
- Never delete or overwrite another agent's uncommitted work.
- Keep commits atomic and task-focused.
- Do not mix unrelated changes into the same task commit.
- Do not commit known broken code.
- Use clear conventional commit messages where appropriate.

Examples:

- `feat: add authentication middleware`
- `fix: resolve session hydration error`
- `test: add authentication coverage`
- `refactor: simplify validation service`

---

## 6. Dependency Rules

- Use only the repository's configured package manager.
- Never switch package managers.
- Do not add dependencies unless necessary.
- Do not upgrade unrelated dependencies.
- Update the lockfile whenever dependencies change.
- Explain why a new dependency is required in the handover notes when relevant.

---

## 7. Protected Data and Files

Never expose, commit, or intentionally modify secrets.

Examples:

- `.env`
- `.env.*` containing secrets
- API keys
- private credentials
- production secrets
- authentication tokens
- private certificates

Never print secret values in logs, commits, or `CHANGES.log`.

Do not modify deployment or infrastructure configuration destructively without explicit authorization.

---

## 8. Database Safety

When a database is present:

- Never perform destructive production operations without explicit authorization.
- Never delete production data.
- Never modify an already-applied migration.
- Create a new migration instead.
- Test migrations against a safe development/test database first.
- Document significant schema changes in the handover.

---

## 9. Validation Requirements

Before marking a task completed or handing it over, run the relevant validation commands:

- Build
- Tests
- Typecheck
- Lint

Record the actual result.

Example:

```text
Build: PASS
Tests: PASS (128/128)
Typecheck: PASS
Lint: PASS
```

If something fails, record:

- Command
- Failure
- Relevant file(s)
- Whether the failure is pre-existing or introduced by the current task

Never claim a task is complete when required validation is failing unless the failure is explicitly documented as an accepted blocker.

---

## 10. Handover Protocol

When handing work to another agent:

1. Inspect the current implementation.
2. Run relevant tests/build/typecheck/lint.
3. Inspect `git status`.
4. Record the current branch.
5. Record the latest commit.
6. Record uncommitted changes.
7. Update `CHANGES.log`.
8. Clearly identify unfinished work.
9. Clearly identify blockers.
10. List active files.
11. Provide actionable next steps for the next agent.

A handover must allow the next agent to continue without reconstructing the entire previous session.

---

## 11. CHANGES.log Format

Append a new entry. Never silently rewrite previous handovers.

```markdown
## [YYYY-MM-DD HH:MM] - Handover from [Agent Name]

- **Current Task:** [Task name]
- **Status:** [IN_PROGRESS / BLOCKED / READY_FOR_REVIEW / COMPLETED / HANDED_OVER]

- **Completed in this session:**
  - [Completed item]
  - [Completed item]

- **Unfinished / Next Steps (CRITICAL):**
  - [ ] [Immediate next step]
  - [ ] [Subsequent step]

- **Known Blocks / Issues:**
  - [Issue or "None"]

- **Validation:**
  - Build: [PASS/FAIL/NOT RUN]
  - Tests: [PASS/FAIL/NOT RUN]
  - Typecheck: [PASS/FAIL/NOT RUN]
  - Lint: [PASS/FAIL/NOT RUN]

- **Git State:**
  - Branch: [branch]
  - Last Commit: [commit hash]
  - Working Tree: [CLEAN/DIRTY]

- **Uncommitted Changes:**
  - [file]
  - [file]

- **Active Files:**
  - [file]
  - [file]

- **Notes for Next Agent:**
  - [Important implementation detail]
  - [Important constraint]
```

---

## 12. Conflict Resolution

If an agent detects conflicting work:

1. Stop modifying the conflicting files.
2. Inspect `git status`.
3. Inspect recent commits.
4. Read the latest relevant `CHANGES.log` entry.
5. Determine task ownership.
6. Do not silently overwrite another agent's changes.
7. Ask the user for clarification if ownership cannot be determined.

When resolving a merge conflict, preserve the intent of both changes where possible and validate the resulting code.

---

## 13. Session Start Protocol

At the beginning of every session:

1. Read `AGENTS.md`.
2. Read `CHANGES.log`.
3. Run `git status`.
4. Inspect recent relevant commits.
5. Identify the current active task.
6. Confirm task ownership.
7. Inspect the relevant files before editing.
8. Read `projects/indoor-detection/PROJECT_PLAN.md` for the delivery checklist;
   update its status after significant milestones with evidence in `CHANGES.log`.

If a task has been explicitly handed over to the current agent, continue it without unnecessary user confirmation.

If ownership, scope, expected behavior, or requirements are ambiguous, ask the user before making consequential changes.

---

## 14. Definition of Done

A task is considered complete only when:

- Implementation is complete.
- Relevant tests are added or updated.
- Relevant tests pass.
- Typecheck passes when applicable.
- Build passes when applicable.
- Lint passes when applicable.
- No unrelated files were unnecessarily modified.
- Git state is understood.
- `CHANGES.log` is updated when a handover or significant state transition occurs.
- Any known limitation is documented.

---

## 15. General Rule

When uncertain:

1. Preserve existing behavior.
2. Do not overwrite another agent's work.
3. Prefer the smallest safe change.
4. Ask before making destructive or ambiguous changes.
5. Document important decisions in `CHANGES.log`.

Continuity, correctness, and traceability are more important than speed.
