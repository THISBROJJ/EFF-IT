---
name: sdlc-pipeline
description: Full AI-assisted development lifecycle from idea to merged PR — runs idea-interrogator, spec-drafter, orchestrator, implementation-loop, karen, security-reviewer, and git-expert in sequence.
argument-hint: "[idea or feature description]"
allowed-tools: [Agent, Bash, Read, Write, Glob, Grep]
---

# SDLC Pipeline

Full AI-assisted development lifecycle from idea to merged PR.
Trigger: user brings a new idea, feature request, or problem statement.

---

## Pre-flight

Confirm the repo is on `main` with a clean working tree:

```bash
git status --short
git branch --show-current
```

If not clean or not on main, ask the user to commit/stash and sync before proceeding.

---

## Step 1 — Interrogate the idea

Invoke the `idea-interrogator` skill interactively. Run until the user signals
the problem is well-specified ("done", "that's enough", "ship it", or similar).

Capture the refined problem statement as `IDEA_SUMMARY`.

---

## Step 2 — Draft the spec

Spawn the `spec-drafter` agent:
- Input: `IDEA_SUMMARY` + any constraints confirmed during interrogation
- Output: `sessions/<run_id>/SPEC.md` — capture path as `SPEC_PATH`

`<slug>` is kebab-case derived from the spec title chosen by spec-drafter.

---

## Step 3 — Create the feature branch

Spawn the `git-expert` agent:
- Task: create branch `feat/<slug>` from `main` and check it out

Confirm branch is active before continuing.

---

## Step 4 — Orchestrate

Spawn the `orchestrator` agent:
- Input: `SPEC_PATH`, `SLUG`
- Output: `sessions/<run_id>/PLAN.md` — capture path as `PLAN_PATH`

---

## Step 4.5 — Architecture draft

Spawn the `architect` agent in Architecture Draft mode (Trigger A):
- Input: `SPEC_PATH`, `PLAN_PATH`, `SLUG`
- Output: `sessions/<run_id>/ARCHITECTURE.md`

Initialize the session run log: create `sessions/<run_id>/run.md` with a header:
```
# Session Run — <slug>
Started: <YYYY-MM-DD HH:MM>
Spec: <SPEC_PATH>
Plan: <PLAN_PATH>
```

---

## Step 5 — Implementation loop

Invoke the `implementation-loop` skill:
- Input: `PLAN_PATH`, `SPEC_PATH`, `max_iterations=5`

The skill spawns coders, runs tests, and cycles until all tests pass or iterations
are exhausted. It returns either PASS or an escalation report.

---

## Step 6 — Completion audit

Spawn the `karen` agent:
- Input: `SPEC_PATH` as the original ask

| Karen verdict | Action |
|---|---|
| PASS | Spawn `architect` agent in Architecture Draft mode (Trigger B) to update root `ARCHITECTURE.md`; then continue to Step 7 |
| PARTIAL or FAIL | Append Karen's punch list to `PLAN_PATH`; return to Step 5 |

---

## Step 7 — Security review

Spawn the `security-reviewer` agent.

| Result | Action |
|---|---|
| PASS | Continue to Step 8 |
| FINDINGS | Append remediation tasks to `PLAN_PATH`; return to Step 5 |

---

## Step 8 — Git wrap-up

Spawn the `git-expert` agent:
- Commit all remaining staged changes (conventional commit, no AI trailers)
- Push branch via SSH
- Open PR against `main`

---

## Artifacts

| Artifact | Path |
|---|---|
| Spec | `sessions/<run_id>/SPEC.md` |
| Task plan | `sessions/<run_id>/PLAN.md` |
| Proposed architecture | `sessions/<run_id>/ARCHITECTURE.md` |
| Canonical architecture | `ARCHITECTURE.md` (root, updated) |
| Problems log | `sessions/<run_id>/PROBLEMS.md` |
| Session run log | `sessions/<run_id>/run.md` |
| Feature branch | `feat/<slug>` |
| PR | GitHub PR → `main` |
