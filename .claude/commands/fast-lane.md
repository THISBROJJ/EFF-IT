---
name: fast-lane
description: Skip interrogation and spec-drafting — take a plain description, branch immediately, and implement. Use when the ask is already well-defined and you don't need a formal spec.
argument-hint: "[feature description]"
allowed-tools: [Agent, Bash, Read, Write, Glob, Grep]
---

# Fast Lane

Skip the interrogation and spec-drafting phases. Takes a plain-language description,
creates a session and branch, then goes straight to orchestration → implementation →
audit → security → PR.

Use this when:
- The ask is already clear and scoped
- You're iterating on something that was already specified
- You want to prototype quickly without a formal spec

---

## Pre-flight

```bash
git status --short
git branch --show-current
```

Must be on `main` with a clean tree. If not, stop and tell the user.

---

## Session setup

If `$ARGUMENTS` is empty, ask for a one-sentence description of the work.

Derive `slug` from the description (kebab-case, 2–4 words, type prefix optional).
Generate `run_id`: `YYYYMMDD-HHmm` (UTC).

Create session directory, register the active run, and write the initial checkpoint:

```bash
mkdir -p sessions/<run_id>
echo "<run_id>" > .current_run
```

`sessions/<run_id>/checkpoint.json`:
```json
{
  "run_id": "<run_id>",
  "slug": "<slug>",
  "started_at": "<ISO8601>",
  "stage": "branch",
  "spec_path": null,
  "plan_path": "sessions/<run_id>/PLAN.md",
  "branch": null,
  "iteration": 0,
  "max_iterations": 5,
  "feature_types": []
}
```

Write a minimal `sessions/<run_id>/SPEC.md` from the description:
```markdown
# <slug>

## Description
<$ARGUMENTS verbatim>

## Acceptance criteria
[GAP: derived from description — orchestrator will expand]
```

---

## Step 1 — Create the feature branch

Spawn the `git-expert` agent:
- Task: create branch `feat/<slug>` from `main` and check it out

Update checkpoint: `"stage": "orchestrate", "branch": "feat/<slug>"`.

---

## Step 2 — Orchestrate

Spawn the `orchestrator` agent:
- Input: `sessions/<run_id>/SPEC.md`, `slug`
- Output: `sessions/<run_id>/PLAN.md`

Update checkpoint: `"stage": "concern"`.

---

## Step 2.5 — Resolve security concerns

Update checkpoint: `"stage": "concern"`.

Spawn the `concern-resolver` agent:
- Input: `run_id`, `spec_path` (`sessions/<run_id>/SPEC.md`)
- Output: `sessions/<run_id>/SECURITY_CONCERNS.md`; updates `feature_types` in checkpoint

Update checkpoint: `"stage": "implement"`.

---

## Step 3 — Implementation loop

Invoke the `implementation-loop` command:
- Input: `sessions/<run_id>/PLAN.md`, `sessions/<run_id>/SPEC.md`, `run_id`, `max_iterations=5`

Update checkpoint: `"stage": "audit"`.

---

## Step 4 — Completion audit

Spawn the `karen` agent with `sessions/<run_id>/SPEC.md` as the original ask.

| Karen verdict | Action |
|---|---|
| PASS | Continue to Step 5 |
| PARTIAL or FAIL | Append punch list to `sessions/<run_id>/PLAN.md`; return to Step 3 |

Update checkpoint: `"stage": "security"`.

---

## Step 5 — Security review

Spawn the `security-reviewer` agent.

| Result | Action |
|---|---|
| PASS | Continue to Step 6 |
| FINDINGS | Append remediation tasks to `sessions/<run_id>/PLAN.md`; return to Step 3 |

Update checkpoint: `"stage": "git"`.

---

## Step 6 — Git wrap-up

Spawn the `git-expert` agent:
- Commit, push, open PR against `main`

Update checkpoint: `"stage": "done"`.

---

## Artifacts

| Artifact | Path |
|---|---|
| Minimal spec | `sessions/<run_id>/SPEC.md` |
| Task plan | `sessions/<run_id>/PLAN.md` |
| Security concern checklist | `sessions/<run_id>/SECURITY_CONCERNS.md` |
| Problems log | `sessions/<run_id>/PROBLEMS.md` |
| Checkpoint | `sessions/<run_id>/checkpoint.json` |
| Feature branch | `feat/<slug>` |
| PR | GitHub PR → `main` |
