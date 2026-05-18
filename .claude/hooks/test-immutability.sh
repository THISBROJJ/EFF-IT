#!/usr/bin/env bash
# PreToolUse hook for Edit|Write — blocks direct modification of test files.
# Reads Claude Code's hook payload (JSON) on stdin; expects .tool_input.file_path.
# Exit 2 + JSON decision block = blocked; exit 0 = allowed.
#
# Protected patterns (after path normalisation to forward slashes):
#   - any path segment named: test, tests, __tests__, spec, specs, evaluation
#   - filenames matching: *.test.<ext>, *.spec.<ext>, test_*, *_test.<ext>

set -u

# shellcheck source=./test-file-patterns.sh
# shellcheck disable=SC1091
source "$(dirname "$0")/test-file-patterns.sh"

INPUT=$(cat)
FILE=$(printf '%s' "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null)

if [ -z "$FILE" ]; then
  exit 0
fi

# Normalise Windows backslashes to forward slashes for consistent matching
FILE_NORM=$(printf '%s' "$FILE" | tr '\\' '/')

is_test_file() {
  local f="$1"
  # Directory segment match: /tests/, /test/, /__tests__/, /spec/, /specs/, /evaluation/
  if printf '%s' "$f" | grep -qE "$TEST_DIR_PATTERN"; then
    return 0
  fi
  # File name patterns: foo.test.ts, foo.spec.js, test_foo.py, foo_test.go
  if printf '%s' "$f" | grep -qE "$TEST_FILE_PATTERN"; then
    return 0
  fi
  return 1
}

# docs/ is never a test directory regardless of segment names (e.g. docs/specs/)
if printf '%s' "$FILE_NORM" | grep -qE '/docs/'; then
  exit 0
fi

if is_test_file "$FILE_NORM"; then
  # Creating a new test file is allowed (TDD requires it).
  # Overwriting or editing an existing test file is blocked.
  if [ -f "$FILE" ] || [ -f "$FILE_NORM" ]; then
    MSG="Test file '${FILE}' is immutable. Per CLAUDE.md §4, existing test files cannot be"
    MSG="${MSG} modified. To update a test: write a new file, or move the original to"
    MSG="${MSG} tests/deprecated/ with a '# DEPRECATED <date>: <reason>' header."
    printf '{"decision":"block","reason":"%s"}' "$MSG"
    exit 2
  fi
fi

exit 0
