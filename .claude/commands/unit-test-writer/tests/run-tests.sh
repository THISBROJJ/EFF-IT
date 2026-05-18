#!/usr/bin/env bash
# Smoke-tests the unit-test-writer helper scripts against the bundled fixtures.
# Exit 0: all checks passed. Exit 1: one or more failed.
#
# Usage: bash tests/run-tests.sh

set -uo pipefail

SKILL_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPTS="$SKILL_ROOT/scripts"
FIXTURES="$SKILL_ROOT/tests/fixtures"
PASS=0
FAIL=0

check() {
  local label="$1" result="$2" expected="$3"
  if [ "$result" = "$expected" ]; then
    echo "PASS  $label"
    PASS=$((PASS + 1))
  else
    echo "FAIL  $label"
    echo "      expected: $expected"
    echo "      got:      $result"
    FAIL=$((FAIL + 1))
  fi
}

# ── detect-framework.sh ──────────────────────────────────────────────────────

LANG_PY=$(bash "$SCRIPTS/detect-framework.sh" "$FIXTURES/python" | grep LANGUAGE | cut -d= -f2)
check "detect python" "$LANG_PY" "python"

RUNNER_PY=$(bash "$SCRIPTS/detect-framework.sh" "$FIXTURES/python" | grep RUNNER | cut -d= -f2)
check "detect python runner" "$RUNNER_PY" "pytest"

LANG_JS=$(bash "$SCRIPTS/detect-framework.sh" "$FIXTURES/javascript" | grep LANGUAGE | cut -d= -f2)
check "detect javascript" "$LANG_JS" "javascript"

RUNNER_JS=$(bash "$SCRIPTS/detect-framework.sh" "$FIXTURES/javascript" | grep RUNNER | cut -d= -f2)
check "detect javascript runner" "$RUNNER_JS" "jest"

LANG_GO=$(bash "$SCRIPTS/detect-framework.sh" "$FIXTURES/go" | grep LANGUAGE | cut -d= -f2)
check "detect go" "$LANG_GO" "go"

# detect-framework should exit 1 on an empty directory
EMPTY_DIR=$(mktemp -d)
bash "$SCRIPTS/detect-framework.sh" "$EMPTY_DIR" > /dev/null 2>&1 && UNKNOWN_EXIT=0 || UNKNOWN_EXIT=$?
rmdir "$EMPTY_DIR"
check "unknown project exits 1" "$UNKNOWN_EXIT" "1"

# ── check-threshold.sh ───────────────────────────────────────────────────────

# All files above threshold → exit 0
PASS_INPUT=$'FILE\tLINE_PCT\tBRANCH_PCT\tFUNC_PCT\nsrc/a.py\t95.0\t91.0\t100.0\n'
printf '%s' "$PASS_INPUT" | bash "$SCRIPTS/check-threshold.sh" 90 > /dev/null 2>&1 && THRESH_PASS=0 || THRESH_PASS=$?
check "threshold pass exits 0" "$THRESH_PASS" "0"

# One file below threshold → exit 1
FAIL_INPUT=$'FILE\tLINE_PCT\tBRANCH_PCT\tFUNC_PCT\nsrc/b.py\t80.0\t75.0\t100.0\n'
printf '%s' "$FAIL_INPUT" | bash "$SCRIPTS/check-threshold.sh" 90 > /dev/null 2>&1 && THRESH_FAIL=0 || THRESH_FAIL=$?
check "threshold fail exits 1" "$THRESH_FAIL" "1"

# ── parse-coverage.py ────────────────────────────────────────────────────────

PYTEST_SAMPLE="Name                 Stmts   Miss  Cover   Missing
--------------------------------------------------
src/calculator.py       20      2    90%   12, 25
TOTAL                   20      2    90%"

PARSED=$(echo "$PYTEST_SAMPLE" | python3 "$SCRIPTS/parse-coverage.py" --format pytest | tail -1 | cut -f1)
check "parse pytest file name" "$PARSED" "src/calculator.py"

# ── summary ──────────────────────────────────────────────────────────────────

echo ""
echo "Results: ${PASS} passed, ${FAIL} failed"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
