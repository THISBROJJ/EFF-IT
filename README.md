# EFF-IT
> "You know what? EFF-IT. Let the agents handle it." — me, TAT

A Claude Code harness that wraps any software project with a full AI-assisted development workflow — from raw idea to merged PR.

---

## What it does

Drop this scaffold into any repo and get:

- **`/run`** — full pipeline: interrogate idea → spec → branch → orchestrate → implement → audit → security review → PR
- **`/fast-lane`** — skip the spec phase, go straight to implementation
- **`/resume`** — pick up an interrupted run from its last checkpoint

Every run is self-contained under `sessions/{run_id}/` with a `checkpoint.json` tracking pipeline stage, artifacts (SPEC, PLAN, ARCHITECTURE), a per-run tool call log, and a problems log from audits.

---

## Structure

```
.claude/
  commands/   — slash-command workflows (/run, /fast-lane, /resume, git-*, etc.)
  agents/     — subagents spawned by commands (orchestrator, coder, karen, etc.)
  hooks/      — lifecycle hooks (logging, secrets scanning, test immutability)
sessions/     — per-run artifacts and tool call logs
tests/
  fixtures/   — pre-baked inputs for testing pipeline stages
scripts/
  secrets-scanner.sh
```

---

## Hooks (always-on)

Wired via `.claude/settings.json` — fire automatically, no opt-in required:

| Hook | When | What |
|---|---|---|
| `log_tool_call.sh` | Every tool use | Writes to `sessions/{run_id}/session_log.json` (or daily flat file outside a run) |
| `secrets-postwrite.sh` | Every Write/Edit | Scans the file for leaked credentials |
| `test-immutability.sh` | Every Edit/Write | Blocks modification of existing test files |
| `git-commit-scope.sh` | `git commit` | Injects diff stat before the commit runs |
| `session-autocommit.sh` | Session log writes | Auto-commits progress tracker (collaborative mode) |

---

## Session tracking modes

**Local only** — add to `.git/info/exclude` (your machine only, not shared):
```
sessions/*.jsonl
sessions/*/
.current_run
```

**Collaborative** — leave exclude alone. The `session-autocommit` hook commits `PROGRESS_TRACKER.md` automatically, giving teammates a live audit trail.

The template ships neutral — no `.gitignore` entry for sessions, no default exclude.

---

## Using it

1. Copy `.claude/`, `sessions/`, `tests/`, `scripts/`, `.github/`, and `.gitignore` into your target repo
2. Fill in `CLAUDE.md` (project name, stack, test command)
3. Run `/run` and describe what you want to build
