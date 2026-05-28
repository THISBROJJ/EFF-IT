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
| `secrets-check` | `/secrets-check` or model-matched | Scans the repo for hard-coded secrets |
| `claude-skills-installer` | model-matched | Installs/uninstalls/lists skills from the catalog |
| `claude-skills-catalog-manager` | model-matched | Manages the skills catalog (contribute, promote, deprecate) |

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
  ├─ /evaluate-run        →  (on karen PASS)     →  sessions/<run_id>/EVALUATION.md
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
    session_log.json    ← structured tool-call log for this run
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
  "test_command": null,
  "feature_types": ["open_endpoint", "jwt"]
}
```
_`"test_command"` — test runner command string, or `null` to auto-detect._

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
