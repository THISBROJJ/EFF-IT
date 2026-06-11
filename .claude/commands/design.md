---
name: design
description: Design half of the SDLC — interrogate the idea, draft the spec, resolve security concerns, draft the architecture, and decompose into a task plan. Produces the durable repo-root design docs (SPEC.md, CONCERN.md, ARCHITECTURE.md, PLAN.md) and opens a design PR. Hand off to /fast-lane to build.
argument-hint: "[idea or feature description]"
allowed-tools: [Agent, Bash, Read, Write, Glob, Grep]
---

# Design — SDLC Front Half

Turns an idea into the four durable, repo-root design docs and opens a PR for them.
Stops there. Once the design PR is merged, run `/fast-lane` to build the plan one task at a
time. This is the half `/fast-lane` does NOT do.

The four design docs live at the **repo root** — they are the *project's* docs (the harness's
own architecture is `.claude/HARNESS.md`). A later `/design` cycle **overwrites** them, so
finish or shelve the current design before starting a new one (the permanent cross-cycle log
is `docs/SPEC.md`, maintained by `spec-keeper`).

---

## Pre-flight

Confirm the repo is on `main` with a clean working tree (`git status --short`,
`git branch --show-current`). If not clean or not on main, ask the user to commit/stash first.

If a repo-root `PLAN.md` already exists with tasks whose `status` is not `DONE`, warn:
"An unfinished design is in progress (`<slug>`, N pending tasks). Starting a new design will
overwrite it. Finish it with `/fast-lane`, or confirm you want to replace it." Wait for
confirmation before proceeding.

---

## Session setup

Generate a `run_id` using the format `YYYYMMDD-HHmm` (UTC). Create the session directory
(for checkpointing only — design outputs go to the repo root), register the active run, and
write the initial checkpoint:

```bash
mkdir -p sessions/<run_id>
echo "<run_id>" > .current_run
```

Write `sessions/<run_id>/checkpoint.json`:
```json
{
  "run_id": "<run_id>",
  "slug": null,
  "phase": "design",
  "started_at": "<ISO8601>",
  "stage": "interrogate",
  "spec_path": "SPEC.md",
  "concern_path": "CONCERN.md",
  "architecture_path": "ARCHITECTURE.md",
  "plan_path": "PLAN.md",
  "feature_types": []
}
```

Test-command detection is not done here — it belongs to the build half (`/fast-lane`).

---

## Step 1 — Interrogate the idea

Invoke the `idea-interrogator` command interactively. Run until the user signals the problem
is well-specified ("done", "that's enough", "ship it", or similar).

Capture the refined problem statement as `IDEA_SUMMARY`. Update checkpoint: `"stage": "spec"`.

---

## Step 2 — Draft the spec

Spawn the `spec-drafter` agent:
- Input: `IDEA_SUMMARY` + any constraints confirmed during interrogation
- Output: repo-root `SPEC.md`

Derive `slug` (kebab-case) from the spec title. Update checkpoint: `slug`, `"stage": "concern"`.

---

## Step 3 — Resolve security concerns

Spawn the `concern-resolver` agent:
- Input: `run_id`, `spec_path` (repo-root `SPEC.md`)
- Output: repo-root `CONCERN.md`; updates `feature_types` in checkpoint

Update checkpoint: `"stage": "architect"`.

---

## Step 4 — Draft the architecture

Spawn the `architect` agent in Architecture Draft mode (Trigger A):
- Input: `spec_path` (repo-root `SPEC.md`), `concern_path` (repo-root `CONCERN.md`), `slug`
- Output: repo-root `ARCHITECTURE.md`

Update checkpoint: `"stage": "orchestrate"`.

---

## Step 5 — Decompose into a plan

Spawn the `orchestrator` agent:
- Input: `run_id`, `SPEC_PATH` (repo-root `SPEC.md`), `slug` (it also reads `CONCERN.md` and `ARCHITECTURE.md`)
- Output: repo-root `PLAN.md` — the durable master tasklist, every task `status: TODO`, `finalized: false`

Update checkpoint: `"stage": "publish"`.

---

## Step 6 — Publish the design

Spawn the `git-expert` agent:
- Create branch `docs/design-<slug>` from `main`
- Commit the four design docs (`SPEC.md`, `CONCERN.md`, `ARCHITECTURE.md`, `PLAN.md`) with a
  `docs: design <slug>` message (no AI trailers)
- Push and open a PR against `main`

Update checkpoint: `"stage": "plan-ready"`. Clear the active run marker:

```bash
rm -f .current_run
```

---

## Done

Tell the user:
- The design docs are at the repo root and opened in PR `<url>`.
- Review/edit them on the PR, then **merge it** so the docs land on `main`.
- After merge, run `/fast-lane` to build the plan one task at a time.

Do not auto-continue into the build — the user reviews and merges first.
