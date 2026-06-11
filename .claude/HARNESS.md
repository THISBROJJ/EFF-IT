# Harness Architecture

This document describes the **harness itself** — the reusable scaffold of hooks, agents, and
commands that wraps any software project with an AI-assisted development workflow. It lives at
`.claude/HARNESS.md` so that the repo-root `ARCHITECTURE.md` is free to hold the *project's*
architecture (produced by `/design`). The harness lives in `.claude/` and `sessions/`.

The **project's** durable design docs live at the repo root — `SPEC.md`, `CONCERN.md`,
`ARCHITECTURE.md`, and `PLAN.md` — written by `/design` and consumed by `/fast-lane`. Project
source goes in `src/`, `tests/`. The permanent cross-cycle feature log is `docs/SPEC.md`.

---

## Layer map

```
.claude/
  hooks/              — shell scripts wired to Claude Code lifecycle events
  agents/             — subagent definitions (markdown + YAML frontmatter)
  commands/           — slash-command workflows invoked interactively
  skills/             — reusable capability bundles (model-triggered or user-typed)
security/
  profiles/           — app-type threat model profiles (loaded by concern-resolver)
  concerns/           — trigger-based concern definitions (scanned per-run)
sessions/
  {run_id}/   — self-contained per-run artifacts (checkpoint, spec, plan, logs)
tests/
  fixtures/   — pre-baked sessions for testing individual pipeline stages
```

---

## Hooks

Hooks are shell scripts that Claude Code executes at lifecycle events (PreToolUse, PostToolUse).
They never block user flow unless intentional.

| Hook | Event | What it does |
|---|---|---|
| `log_tool_call.sh` | PostToolUse (all tools) | Appends one JSONL record per tool call to `sessions/tool-calls-YYYY-MM-DD.jsonl`. Captures Bash commands, file paths, Agent spawns, command invocations, web queries. |
| `session-autocommit.sh` | PostToolUse (Write on `sessions/*/PROGRESS_TRACKER.md`) | Stages all changes and auto-commits with a message derived from the last `##` heading in the progress tracker. |
| `secrets-postwrite.sh` | PostToolUse (Write \| Edit) | Scans the written file for secrets. Surfaces findings in transcript; never blocks. |
| `git-commit-scope.sh` | PreToolUse (Bash `git commit*`) | Injects a `systemMessage` showing `git diff --stat` and `git status` before the commit runs, enforcing diff-before-commit discipline. |
| `test-immutability.sh` | PreToolUse (Edit \| Write) | Blocks modification of existing test files. New test files are allowed (TDD). Protected patterns are defined in `test-file-patterns.sh`. |
| `test-file-patterns.sh` | (sourced library) | Single source of truth for test-path patterns. Shared by `test-immutability.sh` and agent prompts. |

---

## Agents

Agents are subagent definitions that Claude Code spawns via the `Agent` tool. Each is a single
markdown file with YAML frontmatter specifying `name`, `description`, optional `tools`, and
optional `model`. Live in `.claude/agents/` — Claude Code discovers them automatically.

| Agent | Role |
|---|---|
| `orchestrator` | Reads root `SPEC.md`/`CONCERN.md`/`ARCHITECTURE.md`; writes the master task plan (root `PLAN.md`); folds security checklist into tasks |
| `concern-resolver` | Scans root `SPEC.md` for security trigger keywords; writes root `CONCERN.md` |
| `coder` | Implements a single task from the plan |
| `karen` | Audits completed work against the original spec (PASS / PARTIAL / FAIL) |
| `architect` | Drafts the project's root `ARCHITECTURE.md` (before the plan) and appends an as-built section at build finalization; read-only during plan review |
| `spec-drafter` | Writes the root `SPEC.md` from interrogation output |
| `git-expert` | Handles branching, committing, pushing, and PR creation |
| `security-reviewer` | Reviews changed code for security findings |
| `session-keeper` | Writes and updates the session progress tracker |
| `agent-evaluator` | Evaluates agent output quality against expected behavior |
| `test-runner` | Runs the test suite and reports pass/fail/blocked |
| `unit-test-writer` | Generates unit tests targeting ≥90% coverage |
| `spec-keeper` | Appends a dated entry to the cross-cycle log `docs/SPEC.md` at build finalization (idempotent) |

---

## Commands

Commands are slash-command workflows invoked interactively by the user. They orchestrate agents
and tools in a defined sequence. Live in `.claude/commands/` as flat `.md` files.

### Pipeline entry points

| Command | Trigger | What it does |
|---|---|---|
| `design` | `/design [idea]` | Design half: interrogate → spec → concern → architect → orchestrate. Writes the four root design docs and opens a design PR. Stops. |
| `fast-lane` | `/fast-lane [task id]` | Build half: read root `PLAN.md`, pick one task → implement → audit → security → atomic PR; flips the task to `DONE`. Re-invoke per task. |
| `resume` | `/resume [run_id]` | Resume an interrupted design or build run from its checkpoint (`phase` selects the stage machine) |

### Utility commands

| Command | Trigger | What it does |
|---|---|---|
| `implementation-loop` | (invoked by fast-lane) | Spawns coders, runs tests, cycles until all tests pass or max iterations reached |
| `idea-interrogator` | `/idea-interrogator` | Socratic interview loop until the problem is fully specified |
| `evaluate-run` | `/evaluate-run [run_id]` | Scores a completed pipeline run by running `agent-evaluator` against each agent trace |

---

## Skills

Skills are reusable capability bundles. Unlike commands, they can be invoked two ways:
the model auto-matches a skill's description against the user's request, **or** the user
types `/<skill-name>` to invoke explicitly. Live in `.claude/skills/<name>/SKILL.md` with
optional supporting files (`references/`, `scripts/`, `tests/`).

| Skill | Trigger | What it does |
|---|---|---|
| `spec-drafter` | `/spec-drafter` or model-matched | Drafts PRD, technical spec, design doc, or Tessl spec from conversation context |
| `architect` | `/architect` or model-matched | Surfaces refactor opportunities; may write ADRs and update `ARCHITECTURE.md` |
| `unit-test-writer` | `/unit-test-writer` or model-matched | Generates unit tests targeting ≥90% coverage |
| `git-branch` | `/git-branch` or model-matched | Creates and names branches following trunk-based conventions |
| `git-commit` | `/git-commit` or model-matched | Stages and commits with a well-formed Conventional Commit message |
| `git-merge` | `/git-merge` or model-matched | Resolves merge/rebase conflicts interactively |
| `git-pr` | `/git-pr` or model-matched | Creates a GitHub PR with structured body |
| `pr-decomposition` | `/pr-decomposition` or model-matched | Splits a large diff into atomic, independently-mergeable PRs |
| `completion-auditor` | `/completion-auditor` or model-matched | Audits a "done" claim against the original request |
| `claude-skills-installer` | model-matched | Installs/uninstalls/lists skills from the catalog |
| `claude-skills-catalog-manager` | model-matched | Manages the skills catalog (contribute, promote, deprecate) |

---

## Pipeline flow

```
/design <idea>   (design half — produces the durable root docs, opens a PR, then stops)
  │
  ├─ session setup        →  sessions/<run_id>/checkpoint.json (phase: design)
  ├─ idea-interrogator    (interactive)
  ├─ spec-drafter agent   →  SPEC.md          (repo root)
  ├─ concern-resolver     →  CONCERN.md       (repo root)
  ├─ architect (Trigger A) →  ARCHITECTURE.md (repo root)   ← runs BEFORE the plan
  ├─ orchestrator agent   →  PLAN.md          (repo root; master tasklist, status per task)
  └─ git-expert agent     →  docs/design-<slug> branch → design PR  →  user merges

/fast-lane [task]   (build half — one task per invocation, repeat until PLAN.md is drained)
  │
  ├─ read root PLAN.md, pick a buildable task (deps DONE), session setup (phase: build)
  ├─ git-expert agent     →  feat/<task-slug> branch
  ├─ implementation-loop (up to 5 iterations, over the per-task working slice)
  │     └─ unit-test-writer → coder → test-runner → [karen PARTIAL/FAIL → repeat]
  ├─ karen agent          →  PASS or punch list  →  sessions/<run_id>/PROBLEMS.md
  ├─ /evaluate-run        →  (on karen PASS)     →  sessions/<run_id>/EVALUATION.md
  ├─ security-reviewer    →  PASS or remediation →  sessions/<run_id>/PROBLEMS.md
  ├─ flip task → DONE in root PLAN.md
  ├─ if last task: architect (Trigger B) → ARCHITECTURE.md as-built; spec-keeper → docs/SPEC.md
  └─ git-expert agent     →  commit → push → atomic PR

/resume <run_id>
  └─ reads sessions/<run_id>/checkpoint.json → re-enters the owning pipeline at last stage
```

---

## Artifact locations

Durable, committed **project** docs live at the repo root; ephemeral per-run telemetry lives
under `sessions/`. The split is deliberate: design is durable, build telemetry is disposable.

```
<repo root>/
  SPEC.md            ← current design spec        (spec-drafter; overwritten next /design)
  CONCERN.md         ← triggered security concerns (concern-resolver)
  ARCHITECTURE.md    ← project architecture        (architect; as-built appended at finalize)
  PLAN.md            ← master tasklist, status+pr per task, finalized flag (orchestrator + fast-lane)
docs/
  SPEC.md            ← permanent cross-cycle feature log (spec-keeper, append-only)
sessions/
  {run_id}/          ← ephemeral; gitignored        e.g. 20260515-1430
    checkpoint.json     ← current stage + metadata
    PLAN.md             ← per-task working slice (build phase only; loop may mutate freely)
    PROGRESS_TRACKER.md ← per-agent I/O log (auto-committed by hook)
    PROBLEMS.md         ← karen and security findings
    EVALUATION.md       ← evaluate-run scores
    traces/             ← extracted agent traces + verdicts
    session_log.json    ← structured tool-call log for this run
```

`checkpoint.json` schema (a design run and a build run differ by `phase`):
```json
{
  "run_id": "20260515-1430",
  "slug": "user-auth-flow",
  "phase": "build",
  "started_at": "2026-05-15T14:30:00Z",
  "stage": "implement",
  "task_id": "P1-T1",
  "spec_path": "SPEC.md",
  "plan_path": "sessions/20260515-1430/PLAN.md",
  "branch": "feat/user-auth-flow",
  "iteration": 2,
  "max_iterations": 5,
  "test_command": null,
  "feature_types": ["open_endpoint", "jwt"]
}
```
- `"phase"` — `design` or `build`; selects the stage machine `/resume` re-enters.
- Design stages: `interrogate → spec → concern → architect → orchestrate → publish → plan-ready`.
- Build stages: `task-select → branch → implement → audit → security → git → done`.
- `"task_id"` — build phase only; the master-plan task being built. Absent in design.
- `"test_command"` — test runner command string, or `null` to auto-detect (build phase).

## Cross-agent contracts

- **Acceptance-criterion IDs.** ACs are `AC-NN` (zero-padded, two digits: `AC-01`, … `AC-12`).
  spec-drafter mints them in `SPEC.md`; orchestrator references them in `PLAN.md`
  (`acceptance_criteria[].id` / `covered_by`); karen reuses the same IDs when a spec is
  passed. IDs are stable — never renumber an existing AC; append new ones.
- **Plan task status.** Every `PLAN.md` task carries `status: TODO|DONE` and a `pr:` URL
  field. The orchestrator writes them `TODO`/empty; `/fast-lane` owns their lifecycle and is
  the only writer that flips them.

## Design/build invariant

One `/design` cycle fills the four root docs; `/fast-lane` then drains `PLAN.md` task by task.
A later `/design` **overwrites** the root docs — the clean-tree preflight does not protect a
committed `PLAN.md`. Therefore: **finish or shelve the current design before starting a new
one.** `docs/SPEC.md` is the only memory that survives across cycles, which is why
`spec-keeper` logs there at finalization.

---

## Test fixtures

`tests/fixtures/{scenario}/` holds pre-baked session inputs for testing individual pipeline
stages without running the full pipeline:

```
tests/
  fixtures/
    {scenario}/
      SPEC.md   ← pre-written spec for stage-level tests
      PLAN.md   ← pre-written plan for implementation-loop tests
```

---

## Observability

`log_tool_call.sh` appends one JSONL record per tool call using dual-path routing:

- **Per-run log** — when `.current_run` is active, writes to `sessions/<run_id>/session_log.json` (scoped to the active pipeline run)
- **Daily flat log** — when no run is active, writes to `sessions/tool-calls-YYYY-MM-DD.jsonl` (ad-hoc work outside a pipeline run)

Both paths are complementary: the per-run log captures structured events for a specific run, while the daily log captures everything else. Session progress also lives in `sessions/<run_id>/PROGRESS_TRACKER.md` and is auto-committed on write. Together these give a durable, queryable audit trail of what agents did and why.

---

## Conventions

- Agent prompts stay under 200 lines.
- Each agent does one thing — if the description needs "and", split it.
- Existing test files are immutable; create new ones instead of editing.
- Commit messages follow Conventional Commits; no AI footers.
- Branches follow `type/kebab-name` off `main` (trunk-based).

---

## Change log

### 2026-06-10 — decouple-design-build

**What changed.** Split the monolithic `/run` into two commands and promoted design artifacts
to durable, repo-root project docs:

1. **`/run` deleted; `/design` added.** `/design` owns the front half — interrogate → spec →
   concern → architect → orchestrate — and writes the four durable docs to the repo root
   (`SPEC.md`, `CONCERN.md`, `ARCHITECTURE.md`, `PLAN.md`), then opens a `docs/design-<slug>`
   PR and stops. This removes the duplicated `orchestrate → git` build sequence that `run.md`
   and `fast-lane.md` both carried (CLAUDE.md §13).
2. **`/fast-lane` is now the build half.** It reads the master root `PLAN.md`, builds one
   buildable task (dependencies `DONE`) per invocation through implement → karen → security →
   atomic PR, and flips that task's `status`/`pr` in the master plan. Re-invoke per task.
3. **Architect reordered before orchestrate.** Trigger A now drafts `ARCHITECTURE.md` from
   `SPEC.md` + `CONCERN.md` (no `PLAN.md`), so architecture *informs* the task breakdown. The
   security-task injection moved to the orchestrator, which now reads `CONCERN.md`.
4. **Harness self-doc relocated.** Root `ARCHITECTURE.md` → `.claude/HARNESS.md`, freeing the
   root slot for the *project's* architecture.
5. **`SECURITY_CONCERNS.md` → `CONCERN.md`**, at the repo root.
6. **Finalization hooks** (architect Trigger B as-built + `spec-keeper` → `docs/SPEC.md`) fire
   once, when the last `PLAN.md` task is marked `DONE`, guarded by a `finalized` flag.

**How it fits.** Design (think) and build (do) are now separate commands with one shared
source of truth — the master root `PLAN.md`. Progress across many atomic PRs is read from one
file. `docs/SPEC.md` remains the cross-cycle history; the root docs are the current cycle and
are overwritten by the next `/design` (see Design/build invariant).

### 2026-05-18 — harness-eval-paths

**What changed.** Closed five gaps that broke the evaluation pipeline and left
per-run artifact paths inconsistent across the harness:

1. **Agent-evaluator redesigned.** `agents/agent-evaluator.md` no longer writes
   to a nonexistent `reports/` directory and no longer references a missing
   `schemas/evaluation.schema.json`. Verdict reports are now written to
   `sessions/<run_id>/traces/<agent_name>.json`, sibling to the JSONL trace
   they score. `commands/evaluate-run.md` §4 reads from the same location and
   aggregates into `sessions/<run_id>/EVALUATION.md`. The output contract is
   inlined in the agent prompt instead of a separate schema file.
2. **Seven new `criteria.json` files.** `coder`, `test-runner`,
   `unit-test-writer`, `spec-drafter`, `git-expert`, `architect`, and
   `agent-evaluator` each now have a `criteria.json` under
   `.claude/agents/<name>/`. All 11 evaluable agents are now scored end-to-end;
   previously 7 of them were silently skipped by `evaluate-run`.
3. **Agent output paths aligned with the session convention.**
   `agents/spec-drafter.md` and `agents/architect.md` previously documented
   `docs/specs/<slug>.md` and `docs/architecture/<slug>.md` as outputs even
   though every caller passed `sessions/<run_id>/SPEC.md` and
   `sessions/<run_id>/ARCHITECTURE.md`. Both agent prompts and all internal
   cross-references now use the session paths exclusively.
4. **Fast-lane gained an architect step.** `commands/fast-lane.md` now invokes
   architect Trigger A between `concern-resolver` and `implementation-loop`,
   matching `/run`. Checkpoint transitions `concern_resolve → architect →
   implement` mirror `run.md` so `/resume` needs no fast-lane-specific
   branches. Without this step, fast-lane silently skipped security-task
   injection into PLAN.md.
5. **Stale `references/` paths corrected.** `commands/spec-drafter.md` and
   `commands/unit-test-writer.md` previously pointed at `references/<file>.md`
   paths that do not exist; they now reference
   `.claude/commands/<command>/<file>.md` where the templates actually live.
6. **Observability docs reconciled.** §Observability above no longer marks
   `session_log.json` as "(future)" — `log_tool_call.sh` has implemented dual-
   path routing all along.

**How it fits.** This change set finishes wiring `evaluate-run` end-to-end:
agent traces, criteria files, and verdict reports now live in one location
(`sessions/<run_id>/traces/`) under one root (`sessions/<run_id>/`). Every
artifact a single run produces is now under that one directory, so cleanup is
`rm -rf sessions/<id>`, debugging is `ls sessions/<id>`, and there is no
parallel `docs/` or `reports/` tree to keep in sync. Fast-lane and `/run` now
follow the same agent sequence, which simplifies `/resume`.

**Deviations from the proposed session architecture
(`sessions/20260518-2347/ARCHITECTURE.md`).** None of substance. The proposed
design — co-located verdict JSON next to JSONL trace, session-folder as single
artifact root, fast-lane architect step keyed by checkpoint stage, no
`schemas/` directory — was implemented as drafted. One execution-level note
worth recording: the implementation landed across multiple follow-on commits
(`851fe35` P1 gaps, `a38043f` P2 / evaluate-run, `26c317a` S1 wiring,
`e1dfa98` karen punch-list fixes) rather than a single atomic commit, because
karen's first pass surfaced criteria-schema drift across the seven new files
(the Medium-likelihood risk the proposal flagged). That drift was resolved by
a follow-up commit that normalized the criteria shape; the final state
matches the proposed schema. No new directories were created; the "no new
directories" constraint held.
