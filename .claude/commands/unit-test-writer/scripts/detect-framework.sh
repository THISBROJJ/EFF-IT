#!/usr/bin/env bash
# Detects the primary language and test toolchain from project files.
# Prints shell-assignment lines: LANGUAGE, RUNNER, COVERAGE_CMD.
# Exit 0: framework detected. Exit 1: unknown.
#
# Usage: bash detect-framework.sh [project-root]

set -uo pipefail

ROOT="${1:-.}"

# JavaScript / TypeScript
if [ -f "$ROOT/package.json" ]; then
  if grep -q '"vitest"' "$ROOT/package.json" 2>/dev/null; then
    RUNNER="vitest"
    COVERAGE_CMD="npx vitest run --coverage --reporter=text"
  else
    RUNNER="jest"
    COVERAGE_CMD="npx jest --coverage --coverageReporters=text --coverageReporters=json-summary"
  fi
  if [ -f "$ROOT/tsconfig.json" ] || find "$ROOT/src" -maxdepth 3 -name "*.ts" 2>/dev/null | grep -q .; then
    LANG="typescript"
  else
    LANG="javascript"
  fi
  echo "LANGUAGE=$LANG"
  echo "RUNNER=$RUNNER"
  echo "COVERAGE_CMD=$COVERAGE_CMD"
  exit 0
fi

# Python
for f in pyproject.toml setup.cfg pytest.ini setup.py tox.ini; do
  if [ -f "$ROOT/$f" ]; then
    echo "LANGUAGE=python"
    echo "RUNNER=pytest"
    echo "COVERAGE_CMD=python -m pytest --cov=. --cov-report=term-missing --cov-branch"
    exit 0
  fi
done

# Go
if [ -f "$ROOT/go.mod" ]; then
  echo "LANGUAGE=go"
  echo "RUNNER=go test"
  echo "COVERAGE_CMD=go test ./... -coverprofile=coverage.out -covermode=atomic && go tool cover -func=coverage.out"
  exit 0
fi

# Rust
if [ -f "$ROOT/Cargo.toml" ]; then
  echo "LANGUAGE=rust"
  echo "RUNNER=cargo test"
  echo "COVERAGE_CMD=cargo tarpaulin --out Stdout --skip-clean"
  exit 0
fi

# Java / Kotlin — Maven
if [ -f "$ROOT/pom.xml" ]; then
  echo "LANGUAGE=java"
  echo "RUNNER=mvn test"
  echo "COVERAGE_CMD=mvn test jacoco:report"
  exit 0
fi

# Java / Kotlin — Gradle
if [ -f "$ROOT/build.gradle" ] || [ -f "$ROOT/build.gradle.kts" ]; then
  echo "LANGUAGE=java"
  echo "RUNNER=gradle test"
  echo "COVERAGE_CMD=./gradlew test jacocoTestReport"
  exit 0
fi

echo "LANGUAGE=unknown"
echo "RUNNER=unknown"
echo "COVERAGE_CMD=unknown"
exit 1
