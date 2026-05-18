---
name: resume
description: Resume a pipeline run that was interrupted. Reads sessions/{run_id}/checkpoint.json and continues from the recorded stage.
argument-hint: "[run_id]"
allowed-tools: [Agent, Bash, Read, Write, Glob, Grep]
---

# Resume

Picks up an interrupted `/run` or `/fast-lane` pipeline from wherever it stopped.
Reads `checkpoint.json`, restores context, and re-enters the pipeline at the
last incomplete stage.

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
- `run_id`, `slug`, `stage`, `spec_path`, `plan_path`, `branch`, `iteration`, `max_iterations`

Verify the referenced files exist:
```bash
test -f sessions/<run_id>/SPEC.md  && echo "SPEC ok"  || echo "SPEC missing"
test -f sessions/<run_id>/PLAN.md  && echo "PLAN ok"  || echo "PLAN missing"
```

If critical files are missing, report which ones and stop. Do not attempt to reconstruct them.

Register the active run:

```bash
echo "<run_id>" > .current_run
```

Switch to the feature branch if not already on it:
```bash
git branch --show-current
git checkout <branch>   # if not already on it
```

---

## Step 3 — Re-enter the pipeline at `stage`

| `stage` value | Resume action |
|---|---|
| `interrogate` | Cannot resume — no checkpoint data yet. Start fresh with `/run`. |
| `spec` | Re-run spec-drafter with context from IDEA_SUMMARY if available |
| `branch` | Create branch and continue to orchestrate |
| `orchestrate` | Spawn orchestrator → write PLAN.md, continue to concern |
| `concern` | Spawn concern-resolver with `run_id` and `spec_path`; update `feature_types` in checkpoint; continue to architect |
| `architect` | Spawn architect (Trigger A), initialize PROGRESS_TRACKER.md, continue to implement |
| `implement` | Invoke implementation-loop with current `iteration` as starting point |
| `audit` | Spawn karen with SPEC.md |
| `security` | Spawn security-reviewer |
| `git` | Spawn git-expert for commit/push/PR |
| `done` | "This run is already complete. Nothing to resume." |

For `implement`: pass `iteration` from the checkpoint so the loop doesn't restart from 0.

---

## Step 4 — Continue normally

From the resumed stage, follow the same logic as `/run` steps through to completion.
Update `checkpoint.json` at each stage transition exactly as `/run` does.

---

## Hard rules

- Never re-run a stage that is already past. If `stage` is `audit`, don't re-run implement.
- Never overwrite SPEC.md or PLAN.md when resuming — they are the source of truth.
- If the branch no longer exists, stop and ask the user before creating a new one.
