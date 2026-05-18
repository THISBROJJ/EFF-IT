---
name: evaluate-run
description: Scores a completed pipeline run by running agent-evaluator against each agent trace found in PROGRESS_TRACKER.md. Writes sessions/<run_id>/EVALUATION.md with per-agent verdicts and an overall score.
argument-hint: "<run_id>"
allowed-tools: [Agent, Read, Write, Glob, Grep, Bash]
---

# Evaluate Run

Reads recorded agent traces from a completed run's `PROGRESS_TRACKER.md`, scores
each agent against its `criteria.json`, and writes a consolidated `EVALUATION.md`.
Callable standalone or auto-invoked from `/run` after karen returns PASS.

## Inputs

`$ARGUMENTS` is the `<run_id>` string (e.g. `20260518-2227`).

## Protocol

### §1 — Validate the run exists

Check that `sessions/<run_id>/checkpoint.json` exists. If it does not:

```
Error: no checkpoint found for run <run_id>.
Expected: sessions/<run_id>/checkpoint.json
```

Print the error and stop. Do not write any artifact.

### §2 — Parse PROGRESS_TRACKER.md

Read `sessions/<run_id>/PROGRESS_TRACKER.md`.

Extract every section whose heading matches:

```
## [<agent_name>] [<task_id>] [iteration N]
```

Regex (for reference): `^## \[(?P<agent>[^\]]+)\] \[(?P<task>[^\]]+)\] \[iteration (?P<n>\d+)\]`

For each match, capture:
- `agent_name` — the first bracketed token
- `task_id` — the second bracketed token
- `iteration` — the `N` integer
- `block_content` — all lines from the heading through the line before the next `## ` heading (or end of file)

Collect these as a list of trace entries. Deduplicate by `agent_name` to get the
set of unique agents referenced. If PROGRESS_TRACKER.md is absent or empty, skip
to §5 with zero entries.

### §3 — Locate criteria files

For each unique `agent_name`, check whether `.claude/agents/<agent_name>/criteria.json`
exists.

- **With criteria:** include in the evaluation set.
- **Without criteria:** add to the skipped list; do not attempt evaluation.

If no agents have a `criteria.json`, skip §4 and write EVALUATION.md using the
"no criteria" template in §5, then exit 0.

### §4 — Evaluate each agent

For each agent in the evaluation set:

1. Write all trace blocks for this agent (concatenated, with headings preserved)
   to a temp file at `sessions/<run_id>/traces/<agent_name>.md`. Create the
   `traces/` directory if it does not exist.

2. Spawn `agent-evaluator` with the prompt:
   ```
   --trace sessions/<run_id>/traces/<agent_name>.md
   --agent <agent_name>
   ```
   The evaluator reads `.claude/agents/<agent_name>/criteria.json` internally
   and writes its JSON report to `reports/<trace_id>.json`.

3. After the spawn completes, read the JSON report written by `agent-evaluator`
   (path: `reports/<agent_name>.json` or the `trace_id`-based path the evaluator
   emits). Extract `score`, `verdict`, and the count of evaluated criteria.

Collect one result row per agent: `agent_name`, `tasks_evaluated` (count of
distinct `task_id` values for this agent), `score`, `verdict`.

### §5 — Write EVALUATION.md

Write `sessions/<run_id>/EVALUATION.md`.

**Standard template** (when at least one agent was evaluated):

```markdown
# Evaluation — <run_id>
Generated: <ISO-8601 timestamp>

## Results
| Agent | Tasks evaluated | Score | Verdict |
|---|---|---|---|
| <agent_name> | <N> | <0.00–1.00> | PASS / PARTIAL / FAIL |

## Agents skipped (no criteria.json)
- <agent_name>

## Overall
<pass_count> / <total_evaluated> agents passed
```

If no agents were skipped, omit the "Agents skipped" section.

**No-criteria template** (when zero agents have a `criteria.json`):

```markdown
# Evaluation — <run_id>
Generated: <ISO-8601 timestamp>

No criteria files found. Add `.claude/agents/<agent_name>/criteria.json` to
enable scoring.

## Agents seen in PROGRESS_TRACKER.md
- <agent_name>
```

Do not modify `PROGRESS_TRACKER.md` or any other existing session artifact.
Only files written by this command are `sessions/<run_id>/EVALUATION.md` and
temp trace files under `sessions/<run_id>/traces/`.

## Hard rules

- Never modify `PROGRESS_TRACKER.md` or `checkpoint.json`.
- If `sessions/<run_id>/EVALUATION.md` already exists, overwrite it (re-runs are
  idempotent).
- Temp trace files in `sessions/<run_id>/traces/` may be left in place; they are
  gitignored by the session artifact pattern.
- Do not block the pipeline on a FAIL verdict — this command is report-only.
