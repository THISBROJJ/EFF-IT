# `.claude/agents/`

Subagent definitions live here. Empty for v1 — multi-agent orchestration
is a v2+ deliverable per [docs/prd/claude-code-sandbox-template.md](../../docs/prd/claude-code-sandbox-template.md).
This directory exists in v1 to establish the convention without
committing to it.

## Adding a subagent

Each subagent is a single Markdown file with YAML frontmatter:

```markdown
---
name: <kebab-case-name>
description: <one line — when this agent should be invoked>
tools: [Read, Grep, Glob, Bash]   # optional; subset of parent tools
model: sonnet                      # optional; sonnet|opus|haiku
---

# Agent prompt

System prompt for the agent. Describe role, scope, hard rules, and the
shape of output it should return.
```

Save as `.claude/agents/<name>.md`. Claude Code picks it up automatically
on next session.

## Convention notes

- Keep agent prompts under 200 lines (architecture rule from CLAUDE.md §6).
- Each agent should do **one** thing — if the description needs "and",
  split it.
- Agents that mutate the repo (Edit, Write) need a clear scope statement
  in the system prompt; read-only research agents are safer defaults.
- Add an evaluation case under `evaluation/agents/<name>/` when you ship
  a new agent — see [evaluation/README.md](../../evaluation/README.md).
