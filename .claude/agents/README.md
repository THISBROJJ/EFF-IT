# `.claude/agents/`

Subagent definitions. Claude Code discovers them recursively, so each agent lives in its own folder.

## Layout

```
.claude/agents/
  <agent-name>/
    <agent-name>.md       — the agent prompt (YAML frontmatter + system prompt)
    criteria.json         — evaluation criteria, scored by agent-evaluator after each run
    scenarios/            — novel inputs / edge cases recorded by the agent itself
      <brief-slug>.md     — one file per scenario
```

The agent's `name:` frontmatter field is what identifies it to Claude Code, not the filename or folder name — keep all three matching to avoid confusion.

## Adding a subagent

1. Create `.claude/agents/<name>/<name>.md`:

   ```markdown
   ---
   name: <kebab-case-name>
   description: <one line — when this agent should be invoked>
   tools: [Read, Grep, Glob, Bash]   # optional; subset of parent tools
   model: sonnet                      # optional; sonnet|opus|haiku
   ---

   # Agent prompt

   System prompt. Describe role, scope, hard rules, and output shape.
   ```

2. Add `.claude/agents/<name>/criteria.json` in the same commit (mandatory per CLAUDE.md §14 for any agent that participates in a pipeline run). Use an existing agent's `criteria.json` as a template.

3. `scenarios/` is created on demand — the agent writes its own scenario files when it encounters something noteworthy.

## Convention notes

- Keep agent prompts under 200 lines (CLAUDE.md §6).
- Each agent does **one** thing — if the description needs "and", split it.
- Agents that mutate the repo need an explicit scope statement in the prompt; read-only research agents are the safer default.

## Pipeline roster

| Agent | Role |
|---|---|
| `orchestrator` | Decomposes a spec into a task plan |
| `concern-resolver` | Scans the spec for security trigger keywords, merges in app-type profiles |
| `architect` | Drafts/updates architecture docs; read-only during plan review |
| `spec-drafter` | Writes the session SPEC.md from interrogation output |
| `coder` | Implements a single task from the plan |
| `unit-test-writer` | Generates failing tests targeting ≥90% coverage (TDD red phase) |
| `test-runner` | Runs the test suite; reports pass/fail/blocked |
| `karen` | Audits completed work against the original spec (PASS/PARTIAL/FAIL) |
| `security-reviewer` | Reviews changed code for security findings |
| `git-expert` | Branching, committing, pushing, PR creation |
| `session-keeper` | Owns `sessions/<run_id>/PROGRESS_TRACKER.md` exclusively — appends one entry per agent completion |
| `agent-evaluator` | Scores each agent's trace against its `criteria.json`, emits per-agent verdict JSON |
