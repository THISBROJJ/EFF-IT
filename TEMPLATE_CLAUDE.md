# CLAUDE.md

> Template for projects adopting this Claude Code harness. Replace every `<…>` placeholder with values for your project, then delete this blockquote.

## 1. Project overview

**Name:** `<project name>`
**Purpose:** `<one-sentence description of what this project does>`
**Stack:** `<languages, frameworks, runtimes>`
**Primary entry point:** `<path to main entry — e.g. src/index.ts, cmd/server/main.go>`

---

## 2. Before committing

`git-commit-scope.sh` automatically injects `git diff --stat` before any `git commit` command — verify the scope looks right before proceeding.

Run the project's test suite before committing: `<test command — e.g. npm test, pytest, go test ./...>`.

---

## 3. Build & run

`<install command — e.g. npm install, pip install -r requirements.txt>`
`<build command, if any>`
`<run command — e.g. npm run dev, python -m app>`

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

## 6. Agent, command, and skill constraints

Three surfaces, three roles. Each capability lives in exactly one.

| Surface | Invoked by | Lives in | Use for |
|---|---|---|---|
| Command | User typing `/<name>` | `.claude/commands/` | Workflow orchestrators that manage other agents or pause for user input (e.g. `/run`, `/fast-lane`, `/resume`, `/evaluate-run`, `/idea-interrogator`, `/implementation-loop`) |
| Skill | User typing `/<name>` **or** model auto-match against the description | `.claude/skills/<name>/` | Reusable bounded capabilities with a clear input/output (e.g. `spec-drafter`, `architect`, `git-*`, `unit-test-writer`, `pr-decomposition`) |
| Agent | Spawned programmatically via the `Agent` tool by a command/skill | `.claude/agents/<name>/` | Pipeline workers that do one job and return a structured result |

**Surface-choice rule:** workflow orchestrators → commands; reusable capabilities → skills.
Deciding test: does it manage other agents or pause for user input? Command. Single bounded
capability with a clear input/output? Skill. If a capability needs both auto-invocation and
a user-typed entrypoint, make it a skill — skills are already user-invocable as `/<name>`.

**Other constraints:**

- Agent prompts stay under 200 lines.
- Each agent does one thing — if the description needs "and", split it.
- Never duplicate a capability across surfaces. If you find an existing skill/command/agent
  that covers ≥80% of what you need, extend it; don't create a parallel implementation.

---

## 7. Branching & commits

- Branches: `type/kebab-name` off `main` (trunk-based, no long-lived branches).
- Commits: Conventional Commits format (`feat:`, `fix:`, `chore:`, etc.). No AI-generated trailers.
- PRs: imperative title ≤70 chars, base `main`.

Use `/git-branch`, `/git-commit`, `/git-pr` for these tasks.

---

## 8. Session artifacts

Pipeline runs write all artifacts to `sessions/<run_id>/` (e.g. `sessions/YYYYMMDD-HHMM/`). These are local-only — excluded via `.git/info/exclude`, never committed.

`checkpoint.json` in each session directory tracks the current pipeline stage. Use `/resume <run_id>` to continue an interrupted run.

---

## 9. Architecture reference

See [`ARCHITECTURE.md`](./ARCHITECTURE.md) for the full project architecture and harness design: hooks, agents, commands topology, session structure, and pipeline flow.

---

## 10. Security profiles

Declare `app_types` to load app-type-specific threat models into every pipeline run:

```yaml
app_types:
  - <app_type>
  - <app_type>
```

Accepted values (must match a filename in `security/profiles/` without `.md`):
`database`, `rag`, `ai_agent`, `web_app`, `api`, `frontend`, `networking`, `search`, `security_tool`

**How it works:** The `concern-resolver` agent (runs between orchestrate and architect) loads each listed profile and unions its checklists with any trigger-keyword matches from SPEC.md. The merged result is written to `sessions/<run_id>/SECURITY_CONCERNS.md`.

**If absent or empty:** concern-resolver still runs keyword-only detection from SPEC.md, but app-type profile checklists are skipped. A warning is emitted in SECURITY_CONCERNS.md.
