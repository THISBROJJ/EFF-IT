# Fixture: resume-stale-current-run

Simulates a completed pipeline run.

## Setup

- `.current_run` points to run `20260101-0000`
- `sessions/20260101-0000/checkpoint.json` has `"stage": "done"`

## Expected behavior

`/resume` must refuse with:

> "This run is already complete. Nothing to resume."

The command must not re-enter any pipeline stage when `stage` is `done`.
