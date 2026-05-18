#!/usr/bin/env bash
# PostToolUse hook for Write on sessions/{run_id}/PROGRESS_TRACKER.md
# Stages all changes and commits with a message derived from the last log heading.
# Fires only when a session progress tracker is written (filtered by settings.json
# and guarded again here for robustness).

set -u

file_path=$(jq -r '.tool_input.file_path // empty')

# Guard: only act on session progress tracker files (handles both / and \ path separators)
if ! echo "$file_path" | grep -qE '[/\\]sessions[/\\][^/\\]+[/\\]PROGRESS_TRACKER\.md$'; then
  exit 0
fi

# Skip if nothing to commit
if [ -z "$(git status --porcelain 2>/dev/null)" ]; then
  exit 0
fi

# Extract the last ## heading from the progress tracker for the commit message
last_heading=$(grep -E '^## ' "$file_path" 2>/dev/null | tail -1 | sed 's/^## //')
[ -z "$last_heading" ] && last_heading="update session log"

# Strip agent-type prefix (e.g. "[coder] [T1] [iteration 2]"), lowercase
description=$(echo "$last_heading" | sed 's/^\[.*\] //' | tr '[:upper:]' '[:lower:]')
commit_msg="chore: ${description}"

if git add "$file_path" && git commit -m "$commit_msg" 2>/dev/null; then
  commit_hash=$(git rev-parse --short HEAD 2>/dev/null)
  printf 'Auto-committed: %s (%s)' "$commit_msg" "$commit_hash" | jq -Rrs '{"systemMessage": .}'
fi
