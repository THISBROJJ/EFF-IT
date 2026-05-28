---
name: unit-test-writer
description: Generates unit tests for new or changed code following TDD principles and enforces 90% coverage across lines, functions, and branches
argument-hint: "[path | function-name | feature-description]"
allowed-tools: [Bash, Glob, Grep, Read, Write, Edit]
---

# Unit Test Writer

Generates unit tests for new or changed code following TDD principles, and
scans the codebase to find and fix gaps below 90% coverage across lines,
functions, and branches.

Invoke with a file path, a function/class name, or a plain-language feature
description. Omit the argument to scan the entire codebase.

## Scope

- Source files under the current working directory (excludes `node_modules/`,
  `vendor/`, `dist/`, `build/`, `.git/`, and binary files)
- Existing test files discovered by convention (`*.test.*`, `*.spec.*`,
  `tests/`, `__tests__/`)
- Coverage reports produced by the project's own test runner

## Instructions

### §1 — Detect language and test framework

Run the bundled detection script from the project root:

```bash
SKILL_DIR="$HOME/.claude/skills/unit-test-writer"
bash "$SKILL_DIR/scripts/detect-framework.sh" .
```

The script prints `LANGUAGE=`, `RUNNER=`, and `COVERAGE_CMD=` lines.
Eval or parse these to obtain the values for §3.

See `references/coverage-commands.md` for exact CLI flags per framework.

If the script exits 1 (unknown), ask: "I couldn't detect a test framework.
Which test runner does this project use?"

### §2 — Determine target scope

If an argument was provided:

- **File path** — target that file only; find its existing test file by
  convention or note that one must be created.
- **Function or class name** — use Grep to locate all definitions and
  their existing tests.
- **Feature description** — use Grep and Glob to identify the files
  implementing that feature.

If no argument was provided, scan the full codebase (§3).

### §3 — Measure current coverage

Run the coverage command detected in §1, then normalize and check:

```bash
SKILL_DIR="$HOME/.claude/skills/unit-test-writer"

# Run the project's coverage command (from §1 COVERAGE_CMD) and pipe to
# parse-coverage.py, then check against the 90% threshold.
eval "$COVERAGE_CMD" 2>&1 | python3 "$SKILL_DIR/scripts/parse-coverage.py" | \
  tee /tmp/coverage-normalized.tsv | \
  bash "$SKILL_DIR/scripts/check-threshold.sh" 90
```

The normalized TSV columns are: `FILE  LINE_PCT  BRANCH_PCT  FUNC_PCT`.

Identify from the output:
- Files or functions below 90% on any dimension
- Files with zero coverage (no tests at all)

If the runner is not installed or the command fails, note which files
have no corresponding test file and treat them as 0% coverage.
See `references/coverage-commands.md` for install instructions.

### §4 — Prioritise gaps

Rank uncovered targets in this order:
1. Public functions / exported symbols with 0% coverage
2. Public functions / exported symbols below 90%
3. Private/internal functions below 90%

Report the ranked list before writing any tests:

```
Coverage gaps (ranked):
  1. src/auth/token.ts — generateToken() — 0%
  2. src/auth/token.ts — validateToken() — 60% (branch)
  3. src/utils/format.ts — formatDate() — 75% (line)
```

Ask: "I'll write tests for these targets to bring coverage to ≥90%.
Proceed, or adjust the list?"

Wait for confirmation.

### §5 — Write tests (TDD order)

For each target, in ranked order:

1. **Read the source** — understand inputs, outputs, edge cases, and
   error paths.
2. **Check existing tests** — read the current test file (if any) to
   avoid duplication.
3. **Write the test cases** in this order:
   - Happy path (valid input, expected output)
   - Null / empty / zero input
   - Boundary values (min, max, off-by-one)
   - At least one expected failure / error case
   - Any branch not yet covered (guard clauses, conditionals)
4. **Create or edit the test file**:
   - New file: use Write, follow the project's naming convention
     (e.g. `token.test.ts` alongside `token.ts`, or `tests/test_token.py`)
   - Existing file: use Edit, append only — never delete existing tests

After each file, briefly state what was added:
```
✓ skills/unit-test-writer — wrote 6 tests for generateToken()
    happy path, empty string, expired payload, invalid signature,
    missing claims, correct expiry
```

### §6 — Verify coverage

Re-run the coverage command from §3. Confirm each target now meets ≥90%.

If any target is still below 90%, identify the uncovered branches and
add the missing cases (repeat §5 for that target only).

Report final coverage for each file touched:

```
Coverage after:
  src/auth/token.ts      98% line  95% branch  100% function  ✓
  src/utils/format.ts    91% line  90% branch   100% function  ✓
```

### §7 — Summary

End with a plain-language summary:

```
Added N test file(s), M test case(s) across X function(s).
All targets now meet the 90% coverage floor.

Files created : <list>
Files modified: <list>
```

If any target could not reach 90% (e.g. unreachable dead code or
platform-specific branches), explain why and flag it as a known gap.

## Output Format

- §4 gap list: numbered, one entry per function, showing file, function, and current %
- §5 per-file confirmation: `✓ <file> — wrote N tests for <function>()`
- §6 coverage table: columns for file, line %, branch %, function %, pass/fail
- §7 summary: plain sentences, file lists
- Errors: plain language — never show raw test runner stack traces unless
  the user asks for them
