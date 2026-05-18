# Fixture: evaluate-run-karen-trace

## Contents

A minimal PROGRESS_TRACKER.md containing one complete karen audit entry for a
hypothetical `audit-1` task, in the format session-keeper produces.

## What `/evaluate-run` should produce

Running `/evaluate-run` against this fixture directory should produce an
EVALUATION.md containing:
- One karen row (from `[karen] [audit-1] [iteration 1]`)
- Score: 1.0 (all criteria met, no findings)
- Verdict: PASS

## How to run

```
/evaluate-run --run-dir tests/fixtures/evaluate-run-karen-trace
```

The command reads PROGRESS_TRACKER.md, parses each `[agent]` entry, scores
each against the agent's `criteria.json`, and writes EVALUATION.md to the
same directory.
