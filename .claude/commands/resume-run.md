---
name: resume-run
description: Resume a pipeline run that was interrupted. Reads sessions/{run_id}/checkpoint.json and continues from the recorded stage.
argument-hint: "[run_id]"
allowed-tools: [Agent, Bash, Read, Write, Glob, Grep]
---

# Resume Run

Picks up an interrupted `/draft-design-docs` or `/build-task` pipeline from wherever it stopped.
Reads `checkpoint.json`, restores context, and re-enters the pipeline at the
last incomplete stage. The checkpoint's `phase` field (`design` or `build`) selects which
stage machine applies.

---

## Step 0 — Staleness guard (pre-flight)

If `.current_run` exists, read it to get the `run_id`, then validate before proceeding:

```bash
if [ -f .current_run ]; then
  run_id=$(cat .current_run)

  # Check 1: session directory and checkpoint must exist
  if [ ! -f "sessions/${run_id}/checkpoint.json" ]; then
    echo "Error: session ${run_id} not found. Remove .current_run manually if this run is abandoned."
    exit 1
  fi

  # Check 2: run must not already be complete (build terminal=done, design terminal=plan-ready)
  stage=$(jq -r '.stage' "sessions/${run_id}/checkpoint.json")
  if [ "$stage" = "done" ] || [ "$stage" = "plan-ready" ]; then
    echo "Error: run ${run_id} is already complete (stage: ${stage}). Start a new design with /draft-design-docs or build the next task with /build-task. To examine the run, read sessions/${run_id}/."
    exit 1
  fi
fi
```

If `.current_run` is absent, skip this step and proceed to Step 1.

---

## Step 1 — Locate the checkpoint

If `$ARGUMENTS` is a `run_id` (e.g. `20260515-1430`):
- Read `sessions/<run_id>/checkpoint.json`

If `$ARGUMENTS` is empty:
- List all session directories with their checkpoint stage:
  ```bash
  for f in sessions/*/checkpoint.json; do
    echo "$f: $(jq -r '.stage + " | " + .slug + " | started: " + .started_at' "$f")"
  done
  ```
- Ask the user which `run_id` to resume.

If no checkpoint is found: "No checkpoint found for that run_id. Check `sessions/` for available runs."

---

## Step 2 — Restore context

Read the checkpoint and extract:
- `run_id`, `phase`, `slug`, `stage`, `task_id`, `spec_path`, `plan_path`, `branch`, `iteration`, `max_iterations`

Verify the artifacts expected for the current `phase`/`stage` exist (design docs live at the
repo root; build telemetry under `sessions/<run_id>/`). For example, once past `spec` the
repo-root `SPEC.md` should exist; for a build run past `branch` the per-task working plan
`sessions/<run_id>/PLAN.md` should exist.

If critical files are missing, report which ones and stop. Do not attempt to reconstruct them.

Register the active run:

```bash
echo "<run_id>" > .current_run
```

For a `build`-phase run, switch to the feature branch if not already on it:
```bash
git branch --show-current
git checkout <branch>   # if not already on it
```
A `design`-phase run stays on `main` until its `publish` stage.

---

## Step 3 — Re-enter the pipeline at `stage`

### `phase: design` (re-enters `/draft-design-docs`)

| `stage` value | Resume action |
|---|---|
| `interrogate` | Cannot resume — no artifacts yet. Start fresh with `/draft-design-docs`. |
| `spec` | Re-run spec-drafter with context from IDEA_SUMMARY if available → repo-root `SPEC.md` |
| `concern` | Spawn concern-resolver (`run_id`, `spec_path`=`SPEC.md`) → `CONCERN.md`; update `feature_types`; continue to architect |
| `architect` | Spawn architect Trigger A (`SPEC.md` + `CONCERN.md`) → repo-root `ARCHITECTURE.md`; continue to orchestrate |
| `orchestrate` | Spawn orchestrator (reads `SPEC.md`, `CONCERN.md`, `ARCHITECTURE.md`) → repo-root `PLAN.md`; continue to publish |
| `publish` | Spawn git-expert: `docs/design-<slug>` branch, commit the four docs, open PR; continue to plan-ready |
| `plan-ready` | Design complete. Merge the design PR, then run `/build-task`. |

### `phase: build` (re-enters `/build-task`)

| `stage` value | Resume action |
|---|---|
| `task-select` | Re-read root `PLAN.md`; reselect the task (use `task_id` if set), continue to branch |
| `branch` | Create `feat/<task-slug>`, write the per-task working plan, continue to implement |
| `implement` | Invoke implementation-loop with current `iteration` as starting point |
| `audit` | Spawn karen with `SPEC.md`; on PASS invoke `/evaluate-run <run_id>` and append its summary to PROGRESS_TRACKER.md, continue to security |
| `security` | Spawn security-reviewer |
| `git` | Flip the task's `status`/`pr` in root `PLAN.md`, promote unresolved `PROBLEMS.md` residue to root `BACKLOG.md` (idempotent — dedup means re-entry adds no duplicate rows), finalize if it was the last task (architect Trigger B + spec-keeper, guarded by `finalized`), then git-expert commit/push/PR |
| `done` | "This run is already complete. Nothing to resume." |

For `implement`: pass `iteration` from the checkpoint so the loop doesn't restart from 0. If
the loop returns `ESCALATED`, follow `/build-task` Step 3's escalation branch (promote residue
→ `BACKLOG.md`, set the task `BLOCKED`, open a triage PR) rather than continuing to `audit`.

---

## Step 4 — Continue normally

From the resumed stage, follow the same logic as the owning command (`/draft-design-docs` for a design
run, `/build-task` for a build run) through to completion. Update `checkpoint.json` at each
stage transition exactly as the originating pipeline does.

---

## Hard rules

- Never re-run a stage that is already past. If `stage` is `audit`, don't re-run implement.
- Never overwrite the repo-root design docs (`SPEC.md`, `CONCERN.md`, `ARCHITECTURE.md`, `PLAN.md`) or the durable `BACKLOG.md` when resuming — they are the source of truth. Promotion only *appends* to `BACKLOG.md`, and is idempotent (dedup on `source+area+problem`), so re-entering the `git` stage never duplicates rows.
- If the branch no longer exists, stop and ask the user before creating a new one.
