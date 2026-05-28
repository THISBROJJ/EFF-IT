# Tessl `.spec.md` — Executable Specification

Adapted from [tesslio/spec-driven-development-tile](https://github.com/tesslio/spec-driven-development-tile) —
a spec format designed to live next to the code it describes, with inline
test traceability so requirements can be verified mechanically.

Where a PRD is a *narrative* and a Spec Kit spec is a *requirements
document*, a Tessl spec is closer to an **executable contract**: it points
at the files it governs, names the tests that prove each requirement, and
lives in the repo so it can drift along with the code.

## When to use

- Requirements need to live in the repo, next to the code, with
  per-requirement test traceability
- The team wants spec compliance to be reviewable in code review (specs
  are .md files in the repo, not Confluence)
- Implementation already exists or is imminent — this format is too
  low-level for early-stage discovery
- Each spec covers a single logical unit of functionality (a module, an
  API, a feature surface) — not a whole product

## Distinguishing features vs. a PRD or design doc

- **YAML frontmatter with `targets`** — explicit file paths or globs that
  the spec governs. A spec without targets is invalid.
- **Inline `[@test]` links** — every requirement points to its verifying
  test file. The spec doubles as a traceability matrix.
- **Filename ends in `.spec.md`** — the extension is part of the contract;
  tooling looks for it.
- **Lives in `specs/` directory in the repo**, not in a wiki.
- **One spec per logical unit** — don't bundle unrelated features.
- **Code blocks for API contracts inline** — function signatures sit next
  to the prose that describes them.

## Template

````markdown
---
name: <Human-readable feature name>
description: <One-line summary of what this spec covers>
targets:
  - ../src/<path-to-implementation>.py
  - ../src/<related-glob>/**/*.py
---

# <Feature Name>

## <Section: Core operations / API / Behavior>

```<language>
def <function>(arg1: Type, arg2: Type) -> ReturnType: ...
```

`[@test] ../tests/<area>/test_<area>_operations.py`

## <Section: Validation rules / Edge cases>

- <requirement statement — specific, behavior-focused>
  `[@test] ../tests/<area>/test_<requirement>.py`
- <next requirement>
  `[@test] ../tests/<area>/test_<next>.py`

## <Section: Error handling>

- <expected error condition and behavior>
  `[@test] ../tests/<area>/test_<error_case>.py`
````

## Filling rules

- **Targets are mandatory and concrete.** At least one path or glob,
  relative to the spec file. A spec with no targets isn't a Tessl spec.
- **Every requirement gets a `[@test]` link.** A requirement without one
  is either un-testable (rewrite it) or untested (file a gap). Mark
  un-tested requirements with `[GAP: no test yet]` rather than omitting.
- **Test paths are relative to the spec file**, not the repo root.
- **Be specific about behavior.** "Returns 401 on invalid password" beats
  "handles invalid passwords".
- **Don't bundle unrelated features.** If the spec covers two modules
  whose tests don't overlap, split it into two specs.
- **API contract code blocks are encouraged** — they make the spec
  scannable and catch signature drift in review.

## Pairs with

- A separate **PRD** or **design doc** for the *why* — Tessl specs only
  capture *what* and *how it's verified*. They're not a substitute for
  product context.
- A `requirement-gathering` step (in Tessl's own toolkit) before writing,
  so the spec captures confirmed requirements rather than guesses.
