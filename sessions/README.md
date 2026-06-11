# sessions/

Each pipeline run (`/design`, `/fast-lane`, `/resume`) creates a self-contained directory here
for **ephemeral telemetry**. The durable design docs (`SPEC.md`, `CONCERN.md`,
`ARCHITECTURE.md`, `PLAN.md`) live at the repo root, not here.

```
sessions/
  {run_id}/                    ← e.g. 20260515-1430
    checkpoint.json            ← current pipeline stage + phase; used by /resume
    session_log.jsonl          ← every tool call during this run (JSONL)
    PLAN.md                    ← per-task working slice (build phase; loop may mutate freely)
    PROGRESS_TRACKER.md        ← per-agent I/O log
    PROBLEMS.md                ← karen and security-reviewer findings
    EVALUATION.md              ← evaluate-run scores
    traces/                    ← extracted agent traces + verdicts
  tool-calls-YYYY-MM-DD.jsonl  ← fallback log when no run is active
```

`run_id` format: `YYYYMMDD-HHmm` (UTC). Use `/resume <run_id>` to continue an interrupted run.

---

## Git tracking modes

**Local only (default for template development)**
Add to `.git/info/exclude` — stays off git, never affects collaborators:
```
sessions/*.jsonl
sessions/*/
.current_run
```

**Collaborative**
Leave `.git/info/exclude` alone. The `session-autocommit` hook will commit
`PROGRESS_TRACKER.md` writes automatically, giving teammates a live audit trail.

The template ships with neither a `.gitignore` entry nor a default exclude — each
user opts in to the mode that fits their workflow.
