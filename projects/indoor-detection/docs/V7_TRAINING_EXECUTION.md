# V7 bounded training execution

Owner: OpenAI Codex. Status: IN_PROGRESS (RUNNING). Updated2026-10-08.
User requested continuation after the train-ready milestone; this authorizes
one unchanged bounded v7 launch. Preparation reports stay frozen.

## Start and current scope

Started **2026-10-08 21:35:35 Asia/Saigon** (14:35:35UTC).
Report root: `E:/HomeAssistantPi4/reports/indoor-v7-execution-v1`.
Run: `E:/HomeAssistantPi4/runs/indoor-detection/indoor_partial_joint_yolo26n_v7_aligned_768`.
Supervisor launcher36456 / supervisor runtime23120.
Training launcher22964 / actual Python training runtime28328 observed21:37.
Process IDs are snapshots, not a guarantee a process is still alive. Check receipt,
process identity and newest log together. Never relaunch into this run.

- One YOLO26n, smoke0/fire1/person2; init frozen v6 best, unchanged joint-v4.
- 768px/batch8/workers2, max12epochs/patience5, AdamW LR.00015/lrf.05, seed42.
- Existing class-scoped trainer/loss/validator; mixing augmentations all0.
- Effective `args.yaml` matches every explicit config setting; device0 normalized
  from integer0 to string0 by Ultralytics. Initial raw-equality observer rejected
  this serialization type only; normalized check PASS. No training error/retry/change.
- AMP check PASS, first training batches finite, approximately1.86GB shown in log.
  These are startup observations; no completed epoch or quality result yet.
- Training process runs offline with external logging flags disabled in memory;
  no persistent Ultralytics settings change, package installation or secret access.
- No old-test/new-holdout predictions, export or deployment. Original independent
  coverage/deployment limitations remain in V7_EXPERIMENTAL_PREPARATION.md.

## Read-only launch checks

New verifier reads existing frozen manifests without rewriting any earlier report.
51,324 bindings verified, including24,100 current joint images/labels and scopes;
prior holdout/readiness manifests and implementation/config/checkpoint unchanged.
GPU free7,353,663,488B / total8,518,041,600B; RAM available17,260,605,440B;
E: free526,096,125,952B at21:34:48. New run was absent immediately before launch.

Config SHA `5cccddd70d70aef20f5adf2a5e53eee1b8ac1cf45e616fed475e8b93da0c7466`.
V6 best SHA `103b45ab6a61f2431b462ee2bc4402f6ddaa7b982e872afd50515e3c6ef28729`.
Evaluation protocol SHA `b4de1b89b106b0a389972c9b52883afa659e3ba4fa4377797ca9626bc85e5293`.
Unrelated untracked `src/indoor_detection/source_box_review.py` unchanged,
SHA `2672f80a9b1fd3fd3fed9b41f8e82967f089d30f9bced9f91f725aadfeae1df6`.

## Durable monitoring

- `preflight.json`: immutable launch readiness receipt.
- `effective-args-check.json`: explicit config/runtime process observer.
- `execution-status.json`: supervisor-updated STARTING/RUNNING/COMPLETED/FAILED receipt.
- `training.stdout.log`, `training.stderr.log`: child training output.
- `supervisor.stdout.log`, `supervisor.stderr.log`: supervisor output/errors.
- `supervise_training.py`: single launch only, no retry; waits for child exit and
  records exit code, CSV epoch count, checkpoint hashes and unchanged v6 checksum.
- `training_entry.py`: calls existing project CLI with exact frozen config.

Supervisor is a hidden Windows background process; returning from chat does not
finish training. Do not modify the running scripts or frozen receipts. If the
laptop/process exits, inspect evidence first: no automatic resume/retry.
On error/OOM stop and retain logs; do not lower batch/resolution or reopen old runs.
No training-completion or metric claim may be made from startup observations.

Read-only checks from repository root:

```powershell
Get-Content E:/HomeAssistantPi4/reports/indoor-v7-execution-v1/execution-status.json
Get-Content E:/HomeAssistantPi4/reports/indoor-v7-execution-v1/training.stdout.log -Tail 10
Get-Content E:/HomeAssistantPi4/reports/indoor-v7-execution-v1/training.stderr.log -Tail 10
```

## Next steps after exit

1. Verify exit/status/epoch count and checkpoint hashes; inspect actual results/logs.
   Early stop before12 is allowed by patience5; completion does not imply gate PASS.
2. Perform exact square768 validation-only calibration and aggregate/source gates
   under the frozen evaluation protocol. Fire R>=.90 aggregate AND each source,
   smoke R>=.90, person F1>=.65/R>=.60 plus unchanged .01 guardrails vs v6.
3. Any failure: NO_RELEASE, holdout stays closed, no automatic trial series.
4. Only validation acceptance permits candidate/threshold/preprocessing lock before
   one external-holdout opening; no holdout selection/tuning. Experimental PASS
   does not remove representative independent and Pi/camera blockers.

## Validation for launch milestone

Tests192/192 PASS29.07s; Ruff PASS; pip check PASS. Build not applicable;
typecheck not configured. No repository implementation/dependency/config changed.
Launch/status documentation is committed separately; preserve untracked prior work.
