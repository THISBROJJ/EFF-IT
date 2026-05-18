---
name: run
description: Full AI-assisted development lifecycle from idea to merged PR — interrogates the idea, drafts a spec, branches, orchestrates, implements, audits, security-reviews, and opens a PR. All artifacts land in sessions/{run_id}/.
argument-hint: "[idea or feature description]"
allowed-tools: [Agent, Bash, Read, Write, Glob, Grep]
---

# Run — Full SDLC Pipeline

## Pre-flight

Confirm the repo is on `main` with a clean working tree (`git status --short`, `git branch --show-current`). If not clean or not on main, ask the user to commit/stash and sync first.

---

## Session setup

Generate a `run_id` using the format `YYYYMMDD-HHmm` (UTC). Example: `20260515-1430`.

Create the session directory, register the active run, and write the initial checkpoint:

```bash
mkdir -p sessions/<run_id>
echo "<run_id>" > .current_run
```

Detect or prompt for the test command:
- Check for `package.json` with a `"test"` script → `npm test`
- Check for `pytest.ini` or `pyproject.toml` → `pytest -v`
- Check for `Makefile` with a `test` target → `make test`
- Check for `go.mod` → `go test ./...`
- If none found, ask the user: "What command runs your tests? (leave blank to auto-detect later)"

Write the detected/provided value (or null) as `test_command` in the initial checkpoint.json.

Write `sessions/<run_id>/checkpoint.json`:
```json
{
  "run_id": "<run_id>",
  "slug": null,
  "started_at": "<ISO8601>",
  "stage": "interrogate",
  "spec_path": null,
  "plan_path": null,
  "branch": null,
  "iteration": 0,
  "max_iterations": 5,
  "feature_types": [],
  "test_command": null
}
```

All subsequent artifact writes and checkpoint updates use `sessions/<run_id>/`.

---

## Step 1 — Interrogate the idea

Invoke the `idea-interrogator` command interactively. Run until the user signals
the problem is well-specified ("done", "that's enough", "ship it", or similar).

Capture the refined problem statement as `IDEA_SUMMARY`.

Update checkpoint: `"stage": "spec"`.

---

## Step 2 — Draft the spec

Spawn the `spec-drafter` agent:
- Input: `IDEA_SUMMARY` + any constraints confirmed during interrogation
- Output: `sessions/<run_id>/SPEC.md`

Derive `slug` (kebab-case) from the spec title. Update checkpoint: `slug`, `stage: branch`, `spec_path`.

---

## Step 3 — Create the feature branch

Spawn the `git-expert` agent:
- Task: create branch `feat/<slug>` from `main` and check it out

Confirm branch is active. Update checkpoint: `stage: orchestrate`, `branch: feat/<slug>`.

---

## Step 4 — Orchestrate

Spawn the `orchestrator` agent:
- Input: `sessions/<run_id>/SPEC.md`, `slug`, `run_id`
- Output: `sessions/<run_id>/PLAN.md`

Update checkpoint: `stage: concern`, `plan_path`.

---

## Step 4.1 — Resolve security concerns

Update checkpoint: `"stage": "concern"`.

Spawn the `concern-resolver` agent:
- Input: `run_id`, `spec_path` (`sessions/<run_id>/SPEC.md`)
- Output: `sessions/<run_id>/SECURITY_CONCERNS.md`; updates `feature_types` in checkpoint

Update checkpoint: `"stage": "architect"`.

---

## Step 4.5 — Architecture draft

Spawn the `architect` agent in Architecture Draft mode (Trigger A):
- Input: `sessions/<run_id>/SPEC.md`, `sessions/<run_id>/PLAN.md`, `slug`
- Output: `sessions/<run_id>/ARCHITECTURE.md`

Initialize the session progress log `sessions/<run_id>/PROGRESS_TRACKER.md`:
```
# Progress — <slug>
Started: <YYYY-MM-DD HH:MM>
Spec: sessions/<run_id>/SPEC.md
Plan: sessions/<run_id>/PLAN.md
```

Update checkpoint: `"stage": "implement"`.

---

## Step 5 — Implementation loop

Invoke the `implementation-loop` command:
- Input: `sessions/<run_id>/PLAN.md`, `sessions/<run_id>/SPEC.md`, `run_id`, `max_iterations=5`

The command spawns coders, runs tests, and cycles until all tests pass or iterations
are exhausted. It returns either PASS or an escalation report.

Update checkpoint: `"stage": "audit"`.

---

## Step 6 — Completion audit

Spawn the `karen` agent:
- Input: `sessions/<run_id>/SPEC.md` as the original ask

| Karen verdict | Action |
|---|---|
| PASS | Spawn `architect` agent (Trigger B) to update root `ARCHITECTURE.md`; continue to Step 7 |
| PARTIAL or FAIL | Append Karen's punch list to `sessions/<run_id>/PLAN.md`; return to Step 5 |

Update checkpoint: `"stage": "security"`.

---

## Step 6.5 — Post-karen evaluation

After karen returns PASS, before architect Trigger B:
- Invoke `/evaluate-run <run_id>`
- Append the one-line summary from EVALUATION.md to `sessions/<run_id>/PROGRESS_TRACKER.md`:
  ```
  ## [evaluate-run] [post-karen] [iteration <N>]
  **Output:** <N passed> / <M total> agents scored | overall: PASS/PARTIAL/FAIL
  ```

---

## Step 7 — Security review

Spawn the `security-reviewer` agent.

| Result | Action |
|---|---|
| PASS | Continue to Step 8 |
| FINDINGS | Append remediation tasks to `sessions/<run_id>/PLAN.md`; return to Step 5 |

Update checkpoint: `"stage": "git"`.

---

## Step 8 — Git wrap-up

Spawn the `git-expert` agent:
- Commit all remaining staged changes (conventional commit, no AI trailers)
- Push branch via SSH
- Open PR against `main`

Update checkpoint: `"stage": "done"`. Clear the active run marker:

```bash
rm -f .current_run
```

---

All artifacts land in `sessions/<run_id>/`. See `ARCHITECTURE.md` — Session structure for the full list.
