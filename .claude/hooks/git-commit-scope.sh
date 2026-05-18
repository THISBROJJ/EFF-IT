#!/usr/bin/env bash
# PreToolUse hook for Bash(git commit*) — surfaces commit scope to Claude
# before the commit runs. Enforces CLAUDE.md §2's "git diff --stat before
# committing" rule automatically.
# Output: a single JSON object with a `systemMessage` field, written to
# stdout per Claude Code's hook protocol.

set -u

# Only fire on git commit commands
cmd=$(jq -r '.tool_input.command // empty' 2>/dev/null)
if ! echo "$cmd" | grep -q 'git commit'; then
  exit 0
fi

stat=$(git diff --stat HEAD 2>/dev/null | head -20)
status=$(git status --short 2>/dev/null | head -20)

printf 'Commit scope:\n%s\n%s' "$stat" "$status" | jq -Rrs '{"systemMessage": .}'
