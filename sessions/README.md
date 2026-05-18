# sessions/

Each pipeline run (`/run`, `/fast-lane`, `/resume`) creates a self-contained directory here.

```
sessions/
  {run_id}/                    ← e.g. 20260515-1430
    checkpoint.json            ← current pipeline stage; used by /resume
    session_log.json           ← every tool call during this run (JSONL)
    SPEC.md                    ← feature specification
    PLAN.md                    ← task plan (orchestrator output)
    ARCHITECTURE.md            ← proposed architecture for this feature
    PROGRESS_TRACKER.md        ← per-agent I/O log
    PROBLEMS.md                ← karen and security-reviewer findings
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
