# CLAUDE.md

## 1. Project overview

**Name:** EFF-IT (Feature Implementation Toolkit)
**Purpose:** A Claude Code harness — reusable scaffold of hooks, agents, and commands that wraps any software project with an AI-assisted development workflow.
**Stack:** Bash / Markdown / GitHub Actions — no application runtime; the harness targets whatever stack the host project uses.
**Primary entry point:** `.claude/commands/run.md` (full pipeline), `.claude/commands/fast-lane.md` (skip spec), `.claude/commands/resume.md` (resume from checkpoint)

---

## 2. Before committing

`git-commit-scope.sh` automatically injects `git diff --stat` before any `git commit` command — verify the scope looks right before proceeding.

No test command yet (`src/` is empty). When the host project adds a stack, update this section with the actual test runner.

---

## 3. Build & run

This repo is a harness, not an application. There is nothing to install or run directly.

To use it as a scaffold for a new project:
1. Copy `.claude/`, `sessions/`, `tests/`, `scripts/`, and `.github/` into the target repo.
2. Update `CLAUDE.md` and `ARCHITECTURE.md` for the new project.
3. Run `/run` to start the full pipeline.

---

## 4. Test immutability

Existing test files are **immutable**. The `test-immutability.sh` hook blocks edits to files matching test-path patterns (`tests/`, `*.test.*`, `*_test.*`, etc.).

- To fix a broken test: write a new test file; deprecate the old one by moving it to `tests/deprecated/` with a `# DEPRECATED <date>: <reason>` header.
- Creating new test files (TDD) is always allowed.

---

## 5. Secrets

`secrets-postwrite.sh` runs on every Write and Edit via the PostToolUse hook. It calls `scripts/secrets-scanner.sh` against the touched file. If it fires, treat the finding as real — remove the secret and rotate it before pushing.

Never commit `.env` files. Use `.env.local` (gitignored) or a secrets manager for any credentials.

---

## 6. Agent and command constraints

- Agent prompts stay under 200 lines.
- Each agent does one thing — if the description needs "and", split it.
- Commands (`/run`, `/fast-lane`, `/resume`, etc.) are slash-commands invoked interactively by the user; agents are spawned programmatically by commands. Don't blur the two.
- Commands live in `.claude/commands/`; agents live in `.claude/agents/`.

---

## 7. Branching & commits

- Branches: `type/kebab-name` off `main` (trunk-based, no long-lived branches).
- Commits: Conventional Commits format (`feat:`, `fix:`, `chore:`, etc.). No AI-generated trailers.
- PRs: imperative title ≤70 chars, base `main`.

Use `/git-branch`, `/git-commit`, `/git-pr` for these tasks.

---

## 8. Session artifacts

Pipeline runs write all artifacts to `sessions/<run_id>/` (e.g. `sessions/20260515-1430/`). These are local-only — excluded via `.git/info/exclude`, never committed.

`checkpoint.json` in each session directory tracks the current pipeline stage. Use `/resume <run_id>` to continue an interrupted run.

---

## 9. Architecture reference

See [`ARCHITECTURE.md`](./ARCHITECTURE.md) for the full harness design: hooks, agents, commands topology, session structure, and pipeline flow.

---

## 10. Security profiles

Declare `app_types` to load app-type-specific threat models into every pipeline run:

```yaml
app_types:
  - web_app
  - api
```

Accepted values (must match a filename in `.claude/security-profiles/` without `.md`):
`database`, `rag`, `ai_agent`, `web_app`, `api`, `frontend`, `networking`, `search`, `security_tool`

**How it works:** The `concern-resolver` agent (runs between orchestrate and architect) loads each listed profile and unions its checklists with any trigger-keyword matches from SPEC.md. The merged result is written to `sessions/<run_id>/SECURITY_CONCERNS.md`.

**If absent or empty:** concern-resolver still runs keyword-only detection from SPEC.md, but app-type profile checklists are skipped. A warning is emitted in SECURITY_CONCERNS.md.
