# EFF-IT
> "You know what? EFF-IT. Let the agents handle it." 

A Claude Code harness that wraps any software project with a full AI-assisted development workflow — from raw idea to merged PR.

---

## What it does

Drop this scaffold into any repo and get:

- **`/design`** — design half: interrogate idea → spec → concern → architect → orchestrate. Writes the durable repo-root design docs (`SPEC.md`, `CONCERN.md`, `ARCHITECTURE.md`, `PLAN.md`) and opens a design PR.
- **`/fast-lane`** — build half: read the master `PLAN.md`, build one task → implement → audit → security review → atomic PR; flips that task to `DONE`. Re-invoke per task.
- **`/resume`** — pick up an interrupted design or build run from its last checkpoint

The project's durable design docs live at the repo root; the master `PLAN.md` is the single source of truth for what's built. Ephemeral per-run telemetry (`checkpoint.json`, progress tracker, problems log, evaluation, traces) is self-contained under `sessions/{run_id}/`. The harness's own design is documented in [`.claude/HARNESS.md`](./.claude/HARNESS.md).

---

## Structure

```
.
├── .claude/
│   ├── commands/   — slash-command workflows (/design, /fast-lane, /resume, git-*, etc.)
│   ├── agents/     — subagents spawned by commands (orchestrator, coder, karen, etc.)
│   └── hooks/      — lifecycle hooks (logging, secrets scanning, test immutability)
├── security/
│   ├── profiles/   — app-type threat model profiles (loaded by concern-resolver)
│   └── concerns/   — trigger-based concern definitions (scanned per-run)
├── sessions/       — per-run artifacts and tool call logs
├── tests/
│   └── fixtures/   — pre-baked inputs for testing pipeline stages
└── scripts/
    └── secrets-scanner.sh
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
2. Fill in `CLAUDE.md` (project name, stack, test command). The repo-root `ARCHITECTURE.md` is the project's (written by `/design`); the harness's own design is `.claude/HARNESS.md`.
3. Run `/design` and describe what you want to build; merge the design PR, then `/fast-lane` to build each task
