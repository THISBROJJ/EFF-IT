# Test File Naming Conventions

Where to place test files and what to name them, by language and framework.
The unit-test-writer skill uses these conventions when creating new test files.

---

## JavaScript / TypeScript — Jest / Vitest

Test files live **alongside** the source file in the same directory, or in a
sibling `__tests__/` directory.

| Source file | Test file (colocated) | Test file (__tests__) |
|-------------|----------------------|----------------------|
| `src/auth/token.ts` | `src/auth/token.test.ts` | `src/auth/__tests__/token.test.ts` |
| `src/utils/format.js` | `src/utils/format.test.js` | `src/utils/__tests__/format.test.js` |

**Detection:** Jest picks up `*.test.{js,ts,jsx,tsx}` and `*.spec.{js,ts,jsx,tsx}`
by default. Prefer `.test.` over `.spec.` for unit tests; reserve `.spec.` for
integration/e2e tests.

**Jest config discovery:**
```
jest.config.{js,ts,mjs}   testMatch: ["**/*.test.*"]
package.json              "jest": { "testMatch": [...] }
```

---

## Python — pytest

Test files live in a top-level `tests/` directory, mirroring the source
structure, OR alongside the source (flat layout).

| Source file | Recommended test file |
|-------------|----------------------|
| `src/auth/token.py` | `tests/auth/test_token.py` |
| `src/utils/format.py` | `tests/utils/test_format.py` |
| `calculator.py` (flat) | `tests/test_calculator.py` |

**Rules:**
- File name must start with `test_` (pytest auto-discovery)
- Test functions must start with `test_`
- Test classes must start with `Test` (no `__init__` needed)
- `tests/` directory should contain an empty `__init__.py` for src-layout projects

**pytest discovery config (`pyproject.toml`):**
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```

---

## Go

Test files live **in the same package directory** as the source file.

| Source file | Test file |
|-------------|-----------|
| `internal/auth/token.go` | `internal/auth/token_test.go` |
| `pkg/utils/format.go` | `pkg/utils/format_test.go` |

**Rules:**
- File name must end in `_test.go` — Go toolchain ignores it in non-test builds
- Package name is either `package auth` (whitebox) or `package auth_test` (blackbox)
- Use blackbox (`_test` suffix package) for public API tests; whitebox for internal logic

---

## Rust

Test modules live **inside the source file** (unit tests) or in a top-level
`tests/` directory (integration tests).

```rust
// src/calculator.rs — unit tests at the bottom of the file
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_divide_happy_path() { ... }
}
```

| Test type | Location |
|-----------|---------- |
| Unit test | Inline `#[cfg(test)] mod tests` block in the source file |
| Integration test | `tests/calculator_integration.rs` (separate crate) |

---

## Java / Kotlin — JUnit

Test files mirror the source structure under `src/test/`.

| Source file | Test file |
|-------------|-----------|
| `src/main/java/com/example/auth/TokenService.java` | `src/test/java/com/example/auth/TokenServiceTest.java` |
| `src/main/kotlin/auth/TokenService.kt` | `src/test/kotlin/auth/TokenServiceTest.kt` |

**Rules:**
- Class name is `<SourceClass>Test`
- JUnit 5: annotate with `@Test`, extend nothing
- Maven Surefire picks up `*Test.java`, `Test*.java`, `*Tests.java`, `*TestCase.java`

---

## Summary Table

| Language | Convention | Discovery pattern |
|----------|-----------|-------------------|
| JS/TS | `<name>.test.ts` alongside source | `**/*.test.{js,ts}` |
| Python | `tests/test_<name>.py` | `test_*.py` |
| Go | `<name>_test.go` in same directory | `*_test.go` |
| Rust | Inline `#[cfg(test)]` block | built-in |
| Java/Kotlin | `src/test/…/<Name>Test.java` | `*Test.java` |
