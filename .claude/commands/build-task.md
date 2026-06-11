---
name: build-task
description: Build half of the SDLC — read the repo-root PLAN.md produced by /draft-design-docs, pick one task, implement it through the test/fix loop, audit (karen) and security-review it, and open one atomic PR. Re-invoke for the next task. Requires a design produced by /draft-design-docs.
argument-hint: "[task id to build, or empty to choose]"
allowed-tools: [Agent, Bash, Read, Write, Glob, Grep]
---

# Build Task — SDLC Build Half

Reads the durable master `PLAN.md` at the repo root, builds **one task** end-to-end into an
atomic, independently-mergeable PR, and flips that task's `status` to `DONE`. Run it once per
task; re-invoke for the next. Progress for the whole design is tracked in the one root
`PLAN.md` — that is the single source of truth for what is and isn't done.

The design docs (`SPEC.md`, `CONCERN.md`, `ARCHITECTURE.md`, `PLAN.md`) come from `/draft-design-docs`.
This command does not produce them.

---

## Pre-flight

```bash
git status --short
git branch --show-current
```

Must be on `main` with a clean tree. If not, stop and tell the user.

Read the repo-root `PLAN.md`. If it is **absent**, stop:
"No design found. Run `/draft-design-docs` first, then merge its PR so `PLAN.md` is on `main`."

---

## Step 1 — Select a task

Parse `PLAN.md`. Build the set of **buildable** tasks: `status` is not `DONE` **and** every
id in `depends_on` belongs to a task whose `status` is `DONE`.

- If `$ARGUMENTS` names a task id: verify it is buildable. If its dependencies are not all
  `DONE`, stop and list the blocking task ids — do not build against missing code.
- If `$ARGUMENTS` is empty: list the buildable tasks (id, description, scope) and ask the
  user which to start. Also list any pending-but-blocked tasks so the user sees why they
  are unavailable.

If every task is already `DONE`, report that the design is complete (see Step 7) and stop.

Let `TASK` be the chosen task and `task-slug` a kebab-case slug from its description.

---

## Session setup

Generate `run_id` (`YYYYMMDD-HHmm`, UTC). Create the session directory, register the active
run, and detect the test command:
- `package.json` with a `"test"` script → `npm test`
- `pytest.ini` / `pyproject.toml` → `pytest -v`
- `Makefile` with a `test` target → `make test`
- `go.mod` → `go test ./...`
- else ask: "What command runs your tests? (blank to auto-detect later)"

```bash
mkdir -p sessions/<run_id>
echo "<run_id>" > .current_run
```

Write `sessions/<run_id>/checkpoint.json`:
```json
{
  "run_id": "<run_id>",
  "slug": "<task-slug>",
  "phase": "build",
  "started_at": "<ISO8601>",
  "stage": "task-select",
  "task_id": "<TASK id>",
  "spec_path": "SPEC.md",
  "plan_path": "sessions/<run_id>/PLAN.md",
  "branch": null,
  "iteration": 0,
  "max_iterations": 5,
  "test_command": null
}
```

Write the **per-task working plan** `sessions/<run_id>/PLAN.md` — a single-task slice of the
master plan containing `TASK` (its id, description, agent, scope, depends_on) plus the
acceptance criteria it covers. The implementation-loop mutates this working slice freely
(punch lists, remediation); the master root `PLAN.md` is never churned by the loop.

Initialize `sessions/<run_id>/PROGRESS_TRACKER.md`:
```
# Progress — <task-slug>
Started: <YYYY-MM-DD HH:MM>
Task: <TASK id> from PLAN.md
Spec: SPEC.md
```

---

## Step 2 — Create the task branch

Spawn the `git-expert` agent: create branch `feat/<task-slug>` from `main` and check it out.
Update checkpoint: `"stage": "implement", "branch": "feat/<task-slug>"`.

---

## Step 3 — Implementation loop

Invoke the `implementation-loop` command:
- Input: `PLAN_PATH` = `sessions/<run_id>/PLAN.md` (the working slice), `SPEC_PATH` = `SPEC.md`, `run_id`, `max_iterations=5`

Update checkpoint: `"stage": "audit"`.

---

## Step 4 — Completion audit

Spawn the `karen` agent with `SPEC.md` as the original ask, scoped to `TASK`.

| Karen verdict | Action |
|---|---|
| PASS | Continue to Step 4.5 |
| PARTIAL or FAIL | Append punch list to `sessions/<run_id>/PLAN.md`; return to Step 3 |

Update checkpoint: `"stage": "security"`.

---

## Step 4.5 — Post-karen evaluation

After karen returns PASS:
- Invoke `/evaluate-run <run_id>`
- Append the one-line summary from EVALUATION.md to `sessions/<run_id>/PROGRESS_TRACKER.md`:
  ```
  ## [evaluate-run] [post-karen] [iteration <N>]
  **Output:** <N passed> / <M total> agents scored | overall: PASS/PARTIAL/FAIL
  ```

---

## Step 5 — Security review

Invoke the `/security-review` skill. Capture its output as `SKILL_SECURITY_OUTPUT`.

Spawn the `security-reviewer` agent, passing `SKILL_SECURITY_OUTPUT` as `skill_findings`.

| Result | Action |
|---|---|
| PASS | Continue to Step 6 |
| FINDINGS | Append remediation tasks to `sessions/<run_id>/PLAN.md`; agent writes findings to `sessions/<run_id>/PROBLEMS.md`; return to Step 3 |

Update checkpoint: `"stage": "git"`.

---

## Step 6 — Mark done, finalize if last, open PR

1. **Flip task status in the master plan.** In the repo-root `PLAN.md`, set `TASK`'s
   `status: DONE`. Leave `pr:` empty for now (filled after the PR is opened).

2. **Finalize if this was the last task (idempotent).** If every task in the root `PLAN.md`
   is now `DONE` **and** the plan's top-level `finalized` is not already `true`:
   - Spawn the `architect` agent (Trigger B): inputs `spec_path` = `SPEC.md`, `slug`. It
     appends an as-built section to the repo-root `ARCHITECTURE.md`.
   - Spawn the `spec-keeper` agent: inputs `spec_path` = `SPEC.md`, `slug`, `run_id`. It
     appends the shipped spec to `docs/SPEC.md` (no-ops if the date+slug entry already exists).
   - Set `finalized: true` in the root `PLAN.md`.
   If not the last task, or already finalized, skip this sub-step.

3. **Open the PR.** Spawn the `git-expert` agent:
   - Commit the task's code plus the root `PLAN.md` status change (and, on finalization, the
     updated `ARCHITECTURE.md` and `docs/SPEC.md`) — conventional commit, no AI trailers
   - Push the branch and open a PR against `main`
   - Record the PR URL back into `TASK`'s `pr:` field in the root `PLAN.md` and amend/commit
     that change

Update checkpoint: `"stage": "done"`. Clear the active run marker:

```bash
rm -f .current_run
```

---

## Step 7 — Done

Tell the user the task's PR is open at `<url>`, and how many tasks remain `TODO` in
`PLAN.md`. If tasks remain, prompt: "Merge this PR, then run `/build-task` for the next task."
If the design was finalized, say so — `ARCHITECTURE.md` has its as-built section and the
shipped spec is logged in `docs/SPEC.md`.

---

## Artifacts

| Artifact | Path | Lifetime |
|---|---|---|
| Spec / concern / architecture | `SPEC.md` · `CONCERN.md` · `ARCHITECTURE.md` (repo root) | durable (from `/draft-design-docs`) |
| Master task plan | `PLAN.md` (repo root) | durable; status flipped per task |
| Per-task working plan | `sessions/<run_id>/PLAN.md` | ephemeral |
| Progress tracker / problems / evaluation | `sessions/<run_id>/{PROGRESS_TRACKER,PROBLEMS,EVALUATION}.md` | ephemeral |
| Checkpoint | `sessions/<run_id>/checkpoint.json` | ephemeral |
| Feature branch / PR | `feat/<task-slug>` → PR to `main` | per task |
