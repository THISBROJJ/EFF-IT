---
owner: DevSecOps
status: Draft
---

# unit-test-writer

Generates unit tests for new or changed code following TDD principles and enforces 90% coverage across lines, functions, and branches.

## Overview

This skill scans your codebase for coverage gaps, ranks untested functions by
priority, and writes test cases to bring each target to ≥90% line, branch, and
function coverage. It works with JavaScript/TypeScript (Jest/Vitest), Python
(pytest), Go, Rust, and Java/Kotlin projects, detecting the toolchain
automatically from project files.

## Use Cases

- Writing tests for a new function or feature before or after implementation
- Auditing an existing codebase for coverage gaps and filling them in bulk
- Enforcing a 90% coverage floor as part of a PR review or CI readiness check
- Targeting a specific file, class, or function for test hardening

## How to Use

```
/unit-test-writer [path | function-name | feature-description]
```

**Scan the whole codebase for gaps:**
```
/unit-test-writer
```

**Target a specific file:**
```
/unit-test-writer src/auth/token.ts
```

**Target a specific function:**
```
/unit-test-writer generateToken
```

**Target by feature description:**
```
/unit-test-writer "password reset flow"
```

## Output

1. A ranked list of coverage gaps (file, function, current %)
2. Confirmation prompt before writing any tests
3. Per-function confirmation as each test file is written
4. A final coverage table showing line/branch/function % for each file touched
5. A plain-language summary of files created and modified

## Additional Notes

- Requires the project's test runner and coverage tool to be installed
  (e.g. `jest`, `pytest-cov`, `go test`)
- Never deletes existing tests — only appends or creates
- If a target cannot reach 90% (e.g. dead code or platform branches),
  the skill flags it as a known gap rather than silently skipping it
- Coverage floor is 90% across all three dimensions: lines, functions, branches
- Related skills: `pr-decomposition` (split large test PRs)
