#!/usr/bin/env bash
# PostToolUse hook — appends one JSONL record per tool call.
#
# If .current_run exists, writes to sessions/{run_id}/session_log.json
# (per-run log scoped to the active pipeline run).
# Otherwise falls back to sessions/tool-calls-YYYY-MM-DD.jsonl
# (global flat log for ad-hoc work outside a pipeline run).
#
# Captures: Bash commands, Read/Write/Edit file paths, Glob/Grep patterns,
# Agent spawns, command invocations, WebFetch/WebSearch queries.
# Never blocks (always exits 0).

set -uo pipefail

LOG_DIR="sessions"

if [ -f ".current_run" ]; then
  RUN_ID=$(cat .current_run)
  LOG_FILE="$LOG_DIR/$RUN_ID/session_log.json"
else
  LOG_FILE="$LOG_DIR/tool-calls-$(date -u +%Y-%m-%d).jsonl"
fi

INPUT=$(cat)

ENTRY=$(echo "$INPUT" | jq -c --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" '{
  ts: $ts,
  tool: .tool_name,
  input: (
    if   .tool_name == "Bash"      then {cmd: (.tool_input.command // null)}
    elif .tool_name == "Read"      then {file: (.tool_input.file_path // null), offset: (.tool_input.offset // null), limit: (.tool_input.limit // null)}
    elif .tool_name == "Write"     then {file: (.tool_input.file_path // null), bytes: ((.tool_input.content // "") | length)}
    elif .tool_name == "Edit"      then {file: (.tool_input.file_path // null), replace_all: (.tool_input.replace_all // false)}
    elif .tool_name == "Glob"      then {pattern: (.tool_input.pattern // null), path: (.tool_input.path // null)}
    elif .tool_name == "Grep"      then {pattern: (.tool_input.pattern // null), path: (.tool_input.path // null), glob: (.tool_input.glob // null)}
    elif .tool_name == "Agent"     then {type: (.tool_input.subagent_type // "general-purpose"), preview: ((.tool_input.prompt // "") | .[0:120])}
    elif .tool_name == "Skill"     then {skill: (.tool_input.skill // null), args: (.tool_input.args // null)}
    elif .tool_name == "WebFetch"  then {url: (.tool_input.url // null)}
    elif .tool_name == "WebSearch" then {query: (.tool_input.query // null)}
    elif .tool_name == "NotebookEdit" then {file: (.tool_input.notebook_path // null)}
    else .tool_input
    end
  )
}' 2>/dev/null)

if [ -n "$ENTRY" ]; then
  mkdir -p "$(dirname "$LOG_FILE")"
  echo "$ENTRY" >> "$LOG_FILE"
fi

exit 0
