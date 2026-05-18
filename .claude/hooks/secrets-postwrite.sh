#!/usr/bin/env bash
# PostToolUse hook for Write|Edit — scans the touched file for secrets.
# Reads Claude Code's hook payload (JSON) on stdin; expects
# .tool_input.file_path to be the path that was written or edited.
# Always exits 0 — findings are surfaced in the transcript, never block.

set -u

f=$(jq -r '.tool_input.file_path // empty')
if [ -n "$f" ] && [ -f "$f" ]; then
  bash scripts/secrets-scanner.sh "$f" 2>/dev/null || true
fi

exit 0
