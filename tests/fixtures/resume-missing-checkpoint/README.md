# Fixture: resume-missing-checkpoint

Simulates an abandoned or corrupted run.

## Setup

- `.current_run` points to run `20260101-1111`
- No `sessions/` directory exists — the session was never created

## Expected behavior

`/resume-run` must refuse with:

> "No checkpoint found for that run_id. Check `sessions/` for available runs."

The command must not attempt to reconstruct the session or continue the pipeline.
