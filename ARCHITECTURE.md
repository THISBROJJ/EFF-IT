# Harness Architecture

This repo is a Claude Code harness — a reusable scaffold of hooks, agents, and commands that
wraps any software project with an AI-assisted development workflow. The harness lives entirely
in `.claude/` and `sessions/`; your actual project source goes in `src/`, `tests/`, and `docs/`.

---

## Layer map

```
.claude/
  hooks/              — shell scripts wired to Claude Code lifecycle events
  agents/             — subagent definitions (markdown + YAML frontmatter)
  commands/           — slash-command workflows invoked interactively
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
| `orchestrator` | Decomposes a spec into a task plan (`sessions/<run_id>/PLAN.md`) |
| `concern-resolver` | Scans SPEC.md for security trigger keywords; writes `SECURITY_CONCERNS.md` to session dir |
| `coder` | Implements a single task from the plan |
| `karen` | Audits completed work against the original spec (PASS / PARTIAL / FAIL) |
| `architect` | Drafts or updates architecture docs; read-only during plan review |
| `spec-drafter` | Writes specs from interrogation output |
| `git-expert` | Handles branching, committing, pushing, and PR creation |
| `security-reviewer` | Reviews changed code for security findings |
| `session-keeper` | Writes and updates the session progress tracker |
| `agent-evaluator` | Evaluates agent output quality against expected behavior |
| `test-runner` | Runs the test suite and reports pass/fail/blocked |
| `unit-test-writer` | Generates unit tests targeting ≥90% coverage |

---

## Commands

Commands are slash-command workflows invoked interactively by the user. They orchestrate agents
and tools in a defined sequence. Live in `.claude/commands/` as flat `.md` files.

### Pipeline entry points

| Command | Trigger | What it does |
|---|---|---|
| `run` | `/run [idea]` | Full lifecycle: interrogate → spec → branch → orchestrate → implement → audit → security → PR |
| `fast-lane` | `/fast-lane [description]` | Skip interrogation/spec; go straight to branch → orchestrate → implement → audit → security → PR |
| `resume` | `/resume [run_id]` | Resume an interrupted run from its checkpoint |

### Utility commands

| Command | Trigger | What it does |
|---|---|---|
| `implementation-loop` | (invoked by run/fast-lane) | Spawns coders, runs tests, cycles until all tests pass or max iterations reached |
| `idea-interrogator` | `/idea-interrogator` | Socratic interview loop until the problem is fully specified |
| `spec-drafter` | `/spec-drafter` | Drafts PRD, technical spec, design doc, or Tessl spec from conversation context |
| `architect` | `/architect` | Surfaces refactor opportunities; may write ADRs and update `ARCHITECTURE.md` |
| `completion-auditor` | `/completion-auditor` | Audits a claimed-done task; produces PASS / PARTIAL / FAIL with evidence |
| `git-branch` | `/git-branch` | Creates and names branches following trunk-based conventions |
| `git-commit` | `/git-commit` | Stages and commits with a well-formed Conventional Commit message |
| `git-merge` | `/git-merge` | Resolves merge/rebase conflicts interactively |
| `git-pr` | `/git-pr` | Creates a GitHub PR with structured body |
| `unit-test-writer` | `/unit-test-writer` | Generates unit tests targeting ≥90% coverage |
| `pr-decomposition` | `/pr-decomposition` | Splits a large diff into atomic, independently-mergeable PRs |

---

## Pipeline flow

```
/run  (or /fast-lane to skip steps 1–2)
  │
  ├─ session setup        →  sessions/<run_id>/  +  checkpoint.json
  ├─ idea-interrogator    (interactive; skipped by fast-lane)
  ├─ spec-drafter agent   →  sessions/<run_id>/SPEC.md
  ├─ git-expert agent     →  feat/<slug> branch
  ├─ orchestrator agent   →  sessions/<run_id>/PLAN.md
  ├─ concern-resolver agent →  sessions/<run_id>/SECURITY_CONCERNS.md
  ├─ architect agent      →  sessions/<run_id>/ARCHITECTURE.md
  │
  ├─ implementation-loop (up to 5 iterations)
  │     └─ unit-test-writer → coder → test-runner → [karen PARTIAL/FAIL → repeat]
  │
  ├─ karen agent          →  PASS or punch list  →  sessions/<run_id>/PROBLEMS.md
  ├─ security-reviewer    →  PASS or remediation →  sessions/<run_id>/PROBLEMS.md
  └─ git-expert agent     →  commit → push → PR

/resume <run_id>
  └─ reads sessions/<run_id>/checkpoint.json → re-enters pipeline at last stage
```

---

## Session structure

Each run creates a self-contained directory under `sessions/`:

```
sessions/
  {run_id}/             ← e.g. 20260515-1430
    checkpoint.json     ← current pipeline stage + metadata
    SPEC.md             ← feature specification
    PLAN.md             ← task plan (orchestrator output)
    ARCHITECTURE.md     ← proposed architecture for this feature
    PROGRESS_TRACKER.md ← per-agent I/O log (auto-committed by hook)
    PROBLEMS.md         ← karen and security findings
    SECURITY_CONCERNS.md  ← triggered concerns + merged security checklists
    session_log.json    ← (future) structured event log
```

`checkpoint.json` schema:
```json
{
  "run_id": "20260515-1430",
  "slug": "user-auth-flow",
  "started_at": "2026-05-15T14:30:00Z",
  "stage": "implement",
  "spec_path": "sessions/20260515-1430/SPEC.md",
  "plan_path": "sessions/20260515-1430/PLAN.md",
  "branch": "feat/user-auth-flow",
  "iteration": 2,
  "max_iterations": 5,
  "feature_types": ["open_endpoint", "jwt"]
}
```

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

Every tool call is appended to `sessions/tool-calls-YYYY-MM-DD.jsonl` (via `log_tool_call.sh`).
Session progress logs live in `sessions/<run_id>/PROGRESS_TRACKER.md` and are auto-committed
on write. This gives a durable, queryable audit trail of what agents did and why.

---

## Conventions

- Agent prompts stay under 200 lines.
- Each agent does one thing — if the description needs "and", split it.
- Existing test files are immutable; create new ones instead of editing.
- Commit messages follow Conventional Commits; no AI footers.
- Branches follow `type/kebab-name` off `main` (trunk-based).
