# Deepening

How to deepen a cluster of shallow modules safely. Assumes vocabulary from `LANGUAGE.md`.

## Dependency categories

When assessing a candidate for deepening, classify its dependencies. The category determines
how the deepened module is tested across its seam.

| Category | Description | Test strategy |
|---|---|---|
| **Pure** | No I/O, no side effects — pure transformations | Test through the deepened interface directly |
| **Local-substitutable** | Has a test stand-in (in-memory store, stub hook) | Run the stand-in in the test suite; seam stays internal |
| **Owned external** | Another agent/skill/hook you control | Define a port; test with an in-memory adapter |
| **True external** | Third-party (GitHub API, Anthropic API, OS calls) | Inject as a port; test with a mock adapter |

## Seam discipline

- **One adapter = hypothetical seam. Two adapters = real seam.** Don't introduce a port
  unless both a production adapter and a test adapter are justified.
- **Internal seams vs external seams.** A deep module can have internal seams (private to
  its implementation, used by its own tests) as well as the external seam at its interface.
  Don't expose internal seams through the public interface just because tests use them.

## Testing strategy: replace, don't layer

- Old tests on shallow modules become waste once tests at the deepened module's interface
  exist — deprecate them to `tests/deprecated/`.
- Write new tests at the deepened module's interface. The **interface is the test surface**.
- Tests assert on observable outcomes through the interface, not internal state.
- Tests must survive internal refactors. If a test has to change when the implementation
  changes, it is testing past the interface.

## Recognising shallow modules in this repo

Common shallow patterns in Claude Code infrastructure:

- **Pass-through agent**: agent reads a file, does no analysis, re-emits the contents.
  Apply deletion test — if the caller could read the file directly with no loss, it's shallow.
- **One-liner hook wrapper**: hook script that calls one external command without adding
  invariants, error translation, or output shaping. Consider merging into the caller.
- **Duplicate skill**: two skills that cover ≥80% of the same use case with different names.
  Merge into one deep skill with an optional argument.
- **Split orchestration**: pipeline stage split into two agents where neither alone has a
  complete interface (caller must always use both together). Merge them.
