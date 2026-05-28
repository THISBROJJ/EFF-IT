# Coverage Commands Reference

Exact CLI invocations per framework. All commands assume you are in the
project root. Pipe output to `scripts/parse-coverage.py` for normalization.

---

## JavaScript / TypeScript — Jest

```bash
# Text summary (human-readable, parseable by parse-coverage.py)
npx jest --coverage --coverageReporters=text

# Scope to a specific file
npx jest --coverage --coverageReporters=text -- src/auth/token.test.ts

# Exclude generated files
npx jest --coverage --coverageReporters=text --coveragePathIgnorePatterns='["dist/","generated/"]'

# Output JSON summary for programmatic use
npx jest --coverage --coverageReporters=json-summary
# Result written to coverage/coverage-summary.json
```

## JavaScript / TypeScript — Vitest

```bash
npx vitest run --coverage --reporter=text

# Scope to a file pattern
npx vitest run --coverage --reporter=text src/auth/token.test.ts
```

## Python — pytest-cov

```bash
# Line + branch coverage, show missing lines
python -m pytest --cov=. --cov-report=term-missing --cov-branch

# Scope to a specific module
python -m pytest --cov=src/auth --cov-report=term-missing --cov-branch tests/test_token.py

# Exclude files
python -m pytest --cov=. --cov-report=term-missing --omit="**/migrations/*,**/generated/*"

# Enforce a threshold inline (fails the run if below)
python -m pytest --cov=. --cov-fail-under=90
```

**Install:** `pip install pytest-cov`

## Go

```bash
# All packages, write profile
go test ./... -coverprofile=coverage.out -covermode=atomic

# Parse profile — per-function breakdown
go tool cover -func=coverage.out

# HTML report (open in browser)
go tool cover -html=coverage.out

# Scope to one package
go test ./internal/auth/... -coverprofile=coverage.out
```

## Rust — cargo-tarpaulin

```bash
# Text output (parseable by parse-coverage.py)
cargo tarpaulin --out Stdout --skip-clean

# Scope to specific tests
cargo tarpaulin --out Stdout --test unit_tests

# Exclude integration tests
cargo tarpaulin --out Stdout --exclude-files "tests/*"
```

**Install:** `cargo install cargo-tarpaulin`

## Java / Kotlin — Maven + JaCoCo

```bash
# Run tests and generate report
mvn test jacoco:report

# Report written to: target/site/jacoco/index.html
# XML report: target/site/jacoco/jacoco.xml

# Enforce threshold (fails build if below — configure in pom.xml)
mvn verify
```

**pom.xml threshold config:**
```xml
<plugin>
  <groupId>org.jacoco</groupId>
  <artifactId>jacoco-maven-plugin</artifactId>
  <configuration>
    <rules>
      <rule>
        <limits>
          <limit><counter>LINE</counter><minimum>0.90</minimum></limit>
          <limit><counter>BRANCH</counter><minimum>0.90</minimum></limit>
          <limit><counter>METHOD</counter><minimum>0.90</minimum></limit>
        </limits>
      </rule>
    </rules>
  </configuration>
</plugin>
```

## Java / Kotlin — Gradle + JaCoCo

```bash
./gradlew test jacocoTestReport
# Report: build/reports/jacoco/test/html/index.html

./gradlew test jacocoTestCoverageVerification
```

**build.gradle threshold config:**
```groovy
jacocoTestCoverageVerification {
  violationRules {
    rule {
      limit { minimum = 0.90 }
    }
  }
}
```

---

## Common Exclusion Patterns

| Pattern | Purpose |
|---------|---------|
| `**/migrations/*` | Django / Alembic DB migrations |
| `**/generated/*` | Protobuf / OpenAPI generated code |
| `**/vendor/*` | Vendored dependencies |
| `**/__init__.py` | Python package markers |
| `**/fixtures/*` | Test fixtures |
| `**/conftest.py` | pytest configuration |
