---
name: implementation-loop
description: Manages the code → test → fix cycle until all tests pass or max iterations is reached. Receives a task plan and spec path; spawns coders, runs tests, and repeats.
argument-hint: "[PLAN_PATH SPEC_PATH]"
allowed-tools: [Agent, Read, Write, Glob, Grep, Bash]
---

# Implementation Loop

Manages the code → test → fix cycle until all tests pass or max iterations is
reached. Receives a task plan and spec path; spawns coders, runs tests, repeats.

---

## Inputs

- `PLAN_PATH`: path to the per-task working plan (e.g., `sessions/<run_id>/PLAN.md`). `/fast-lane` writes this working slice containing the single task it selected from the master `PLAN.md`; the loop may mutate it freely (punch lists, remediation) without touching the durable master plan at the repo root.
- `SPEC_PATH`: path to the spec (the repo-root `SPEC.md`)
- `run_id`: the session run identifier (e.g., `20260515-1430`); used to locate all session artifacts
- `max_iterations`: max cycles before escalating (default: 5)
- `punch_list` (optional): additional tasks from karen or security-reviewer

`run_id` is passed by the caller (`/fast-lane`). All ephemeral session artifacts live at `sessions/<run_id>/`.

---

## Cycle protocol

### Iteration N of max_iterations

**1. Load the plan**

Read `PLAN_PATH`. Identify all tasks where `status != DONE`.
If `punch_list` is provided, append each item as a new task in group `PL` with `agent: coder`.

**1.5. Write failing tests (TDD red phase) — iteration 1 only**

On the first iteration, before spawning any coder:
- For each pending task, check whether a corresponding test file already exists.
- For tasks without test coverage, spawn `unit-test-writer` agents in parallel (one per task, mirroring the parallel group structure).
- Pass each `unit-test-writer`: `task_description`, `scope`, and `spec_path`.
- Wait for all `unit-test-writer` agents to complete.
- Verify test files now exist. If a unit-test-writer could not produce tests (e.g., scope is infrastructure-only), note it and continue — do not block.
- **REQUIRED — record before proceeding:** For each `unit-test-writer` agent that ran, spawn `session-keeper` in parallel (one call per agent) with: `run_id`, `agent_name="unit-test-writer"`, `task_id`, `iteration=1`, `status` (`DONE` or `BLOCKED`), `summary`, `karen_verdict="n/a"`, `karen_findings=""`, `scope`. Wait for all session-keeper calls to complete before proceeding to step 2.

Skip this step on iterations 2+ (tests already exist from iteration 1; coders are now fixing failures, not starting from scratch).

**2. Spawn parallel groups**

For each parallel group (process all parallel groups before sequential):
- Spawn all assigned agents simultaneously (one Agent call per task in the same message)
- Wait for all to complete

After all agents in the group complete:

**Karen** — For each **coder** task, spawn Karen simultaneously (one Agent call per coder task). Pass the task description as the original ask and the task's `scope` as the change set. Wait for all Karen verdicts. PASS → continue; PARTIAL or FAIL → append findings to `sessions/<run_id>/PROBLEMS.md`, mark task `NEEDS_RETRY`.

**REQUIRED — record before proceeding to next group:** For **every** agent in this group (coder and non-coder alike), spawn `session-keeper` in parallel (one call per agent) with: `run_id`, `agent_name`, `task_id`, `iteration`, `status` (`DONE` or `BLOCKED`), `summary`, `karen_verdict` (Karen's verdict for coder tasks; `"n/a"` for all other agent types), `karen_findings`, `scope`. Wait for **all** session-keeper calls to complete. Do not start the next group until this step finishes.

Pass each agent: `task_description`, `scope`, `spec_path`, and any `context`
from prior iterations (test-runner failure output for the relevant component).
Coders must not modify test files — the tests written in step 1.5 are the acceptance target.

**3. Spawn sequential groups**

For each sequential group, in order:
- Spawn one agent at a time. Pass the result of the prior task as `context` to the next.
- **Karen** (coder tasks only): after the agent completes, spawn Karen with the task description and scope. Wait for verdict. PASS → continue; PARTIAL or FAIL → append findings to `sessions/<run_id>/PROBLEMS.md`, mark task `NEEDS_RETRY`.
- **REQUIRED — record before proceeding to next task:** Spawn `session-keeper` with: `run_id`, `agent_name`, `task_id`, `iteration`, `status` (`DONE` or `BLOCKED`), `summary`, `karen_verdict` (Karen's verdict for coder tasks; `"n/a"` for all other agent types), `karen_findings`, `scope`. Wait for session-keeper to complete. Do not start the next task until this step finishes.

**4. Run tests**

Spawn the `test-runner` agent with `PLAN_PATH`. Wait for it to complete.

**REQUIRED — record before acting on result:** Spawn `session-keeper` with: `run_id`, `agent_name="test-runner"`, `task_id="test-runner"`, `iteration`, `status="DONE"`, `summary` (e.g. "PASS — 42 tests" or "FAIL — 3 tests failing"), `karen_verdict="n/a"`, `karen_findings=""`, `scope="all"`. Wait for session-keeper to complete before reading the test result below.

| Test result | Action |
|---|---|
| BLOCKED (immutability violation) | Surface the violation to the user; pause and wait for resolution |
| UNKNOWN (no test command) | Surface to the user; pause and wait |
| PASS | Proceed to Step 4.5 — Security check |
| FAIL | Identify failing components; update their task `context` with failure output; go to Iteration N+1 |

**4.5. Security check** (runs only when Step 4 result is PASS)

Invoke the `/security-review` skill. Capture its output as `SKILL_SECURITY_OUTPUT`.

Spawn the `security-reviewer` agent with `run_id` and `skill_findings: SKILL_SECURITY_OUTPUT`.

**REQUIRED — record before acting on result:** Spawn `session-keeper` with: `run_id`, `agent_name="security-reviewer"`, `task_id="security-check"`, `iteration`, `status="DONE"`, `summary` (e.g. "PASS" or "FINDINGS — N items"), `karen_verdict="n/a"`, `karen_findings=""`, `scope="all"`. Wait for session-keeper to complete before reading the result below.

| Security verdict | Action |
|---|---|
| PASS | Exit loop with STATUS: PASS |
| FINDINGS | Append remediation tasks to `sessions/<run_id>/PLAN.md`; agent writes findings to `sessions/<run_id>/PROBLEMS.md`; go to Iteration N+1 (or escalate if max_iterations reached — include security findings in escalation report) |

**5. Max iterations check**

If N == max_iterations and tests are still failing:
- Do NOT continue looping
- Report:
  - Which tests are still failing
  - Which tasks were BLOCKED (coder could not complete without out-of-scope access)
  - What the coder attempted in the last iteration
- Ask the user how to proceed (extend iterations, adjust scope, or abandon)

---

## After the loop exits with STATUS: PASS

Return to the caller with:
- Final status: PASS
- One-line summary per completed task
- List of any tasks that remained BLOCKED throughout all iterations

---

## Escalation format (max iterations reached without PASS)

```
# Implementation Loop — Escalation

**Status: ESCALATED after <N> iterations**

## Still-failing tests
- <test name> — <file:line> — <failure message>

## Blocked tasks
- <task id>: <what the coder needs that is out of scope>

## Last iteration summary
- <task id>: <what was attempted>

## Recommended next step
<One concrete suggestion: expand scope, fix a dependency, or ask user>
```
