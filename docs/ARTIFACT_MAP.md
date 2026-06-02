# EFF-IT Artifact Map

Companion to `docs/SDLC_FLOWCHART.md`. Focuses on **what is written, by whom, and who reads it** — rather than process flow.

**↺** marks artifacts that participate in feedback loops: a downstream agent writes back to them, and an upstream agent re-reads them in a later iteration.

> Render in any Mermaid-aware viewer (GitHub, VS Code + Mermaid Preview, mermaid.live).

---

## Diagram 1 — Full Artifact Data Flow

```mermaid
flowchart TD
    classDef artifact fill:#1B5E20,stroke:#145214,color:#fff
    classDef loop     fill:#E65100,stroke:#BF360C,color:#fff
    classDef agent    fill:#6A1B9A,stroke:#4A148C,color:#fff
    classDef cmd      fill:#1565C0,stroke:#0D47A1,color:#fff
    classDef hook     fill:#B71C1C,stroke:#7F0000,color:#fff
    classDef obs      fill:#37474F,stroke:#263238,color:#fff

    %% ── Session Init ──────────────────────────────────────────────────────────
    SESSION["session setup\n/run · /fast-lane"]:::cmd

    SESSION -->|"creates"| CURR_RUN{{".current_run"}}:::artifact
    SESSION -->|"initial write"| CHK[("checkpoint.json ↺\nstage · slug · branch\nfeature_types · iteration")]:::loop

    %% ── Spec Phase ────────────────────────────────────────────────────────────
    SPEC_D["spec-drafter"]:::agent
    SPEC_D --> SPEC[("SPEC.md\nsource of truth\nfor all downstream agents")]:::artifact

    %% ── Orchestrate ───────────────────────────────────────────────────────────
    SPEC --> ORCH["orchestrator"]:::agent
    PROB[("PROBLEMS.md ↺\nkaren punch lists\nsecurity findings")]:::loop -.->|"fold blockers on re-run"| ORCH
    ORCH --> PLAN[("PLAN.md ↺\ntask decomposition\nstatus per task")]:::loop

    subgraph ARCH_REVIEW ["Architect Plan Review (inside orchestrator)"]
        direction LR
        ARCH_PR["architect · Plan Review\n(read-only)"]:::agent
        ARCH_PR_V{"APPROVE\nor REVISE?"}
    end
    PLAN --> ARCH_PR
    ARCH_PR --> ARCH_PR_V
    ARCH_PR_V -->|"REVISE — violations\n(max 2 rounds)"| ORCH
    ARCH_PR_V -->|"APPROVE"| PLAN_FINAL(["PLAN.md finalised"])

    %% ── Security Concerns ─────────────────────────────────────────────────────
    SPEC --> CONCERN["concern-resolver"]:::agent
    CONCERN --> SCON[("SECURITY_CONCERNS.md\ntriggered concerns\nmerged checklists")]:::artifact
    CONCERN -->|"feature_types written back"| CHK

    %% ── Architecture Draft ────────────────────────────────────────────────────
    SPEC --> ARCH_A["architect · Trigger A\nArchitecture Draft"]:::agent
    PLAN_FINAL --> ARCH_A
    ARCH_A --> SARCH[("ARCHITECTURE.md · session\nproposed design\nfor this feature")]:::artifact
    SARCH -.->|"aligns task scopes"| ORCH

    %% ── Implementation Loop ───────────────────────────────────────────────────
    PLAN_FINAL --> IMPL["implementation-loop"]:::cmd
    SPEC --> IMPL
    PROB -.->|"retry context"| IMPL

    IMPL --> UTW["unit-test-writer"]:::agent
    IMPL --> CODER["coder"]:::agent
    IMPL --> TR["test-runner"]:::agent

    UTW  --> TEST_FILES[("tests/ — new test files\nimmutable once written")]:::artifact
    CODER --> SRC[("src/ changes")]:::artifact
    SRC  --> TR

    %% session-keeper records every agent completion
    UTW   -->|"completion"| SK["session-keeper\n(Haiku)"]:::agent
    CODER -->|"completion"| SK
    TR    -->|"completion"| SK
    SK --> PROG[("PROGRESS_TRACKER.md\nper-agent I/O log\nauto-committed on write")]:::artifact

    %% ── Completion Audit ──────────────────────────────────────────────────────
    SPEC --> KAREN["karen · completion auditor\n(Opus)"]:::agent
    KAREN -->|"PARTIAL / FAIL — punch list"| PLAN
    KAREN -->|"findings"| PROB
    KAREN -->|"full audit report"| AUD[("audits/task-slug.md")]:::obs

    %% ── Security Review ───────────────────────────────────────────────────────
    SCON --> SECRV["security-reviewer"]:::agent
    SECRV -->|"FINDINGS — remediation tasks"| PLAN
    SECRV -->|"findings"| PROB

    %% ── Evaluate Run ──────────────────────────────────────────────────────────
    PROG --> EVAL_C["evaluate-run"]:::cmd
    EVAL_C --> TMD[("traces/agent.md\nextracted trace blocks · temp")]:::obs
    TMD --> EVAL_A["agent-evaluator\n(Opus)"]:::agent
    EVAL_A --> TJSON[("traces/agent.json\nper-agent scored verdict")]:::obs
    TJSON -->|"per-agent score"| EVAL_C
    EVAL_C --> EVAL[("EVALUATION.md\naggregated scores\noverall verdict")]:::obs

    %% ── Architecture Trigger B ────────────────────────────────────────────────
    KAREN -->|"PASS → update root docs"| ARCH_B["architect · Trigger B\nUpdate root ARCHITECTURE.md"]:::agent
    ARCH_B --> RARCH[("ARCHITECTURE.md · root\npermanent design record")]:::artifact

    %% ── Git Wrap-up ───────────────────────────────────────────────────────────
    GIT["git-expert"]:::agent
    GIT --> PR[("GitHub PR → main")]:::artifact
    SESSION -->|"cleared on done"| CURR_RUN

    %% ── Hooks (always active) ─────────────────────────────────────────────────
    LOG_H["log_tool_call.sh · hook\nPostToolUse — all tools"]:::hook
    CURR_RUN -.->|"routes log destination"| LOG_H
    LOG_H --> SLOG[("session_log.json\nor tool-calls-YYYY-MM-DD.jsonl\none JSONL per tool call")]:::obs

    AC["session-autocommit.sh · hook\nPostToolUse — Write on PROGRESS_TRACKER.md"]:::hook
    PROG -.->|"triggers auto-commit"| AC

    %% ── Resume ────────────────────────────────────────────────────────────────
    CHK -.->|"stage field → re-entry point"| RESUME["/resume"]:::cmd
```

---

## Diagram 2 — Feedback Loops (zoomed in)

Three artifacts form genuine feedback loops — downstream agents write back, upstream agents re-read in the next iteration.

```mermaid
flowchart LR
    classDef loop  fill:#E65100,stroke:#BF360C,color:#fff
    classDef agent fill:#6A1B9A,stroke:#4A148C,color:#fff
    classDef cmd   fill:#1565C0,stroke:#0D47A1,color:#fff

    subgraph LOOP1 ["↺ Loop 1 — PLAN.md (implementation retry)"]
        direction TB
        ORCH1["orchestrator"]:::agent
        PLAN1[("PLAN.md")]:::loop
        KAREN1["karen"]:::agent
        SECRV1["security-reviewer"]:::agent
        IMPL1["implementation-loop"]:::cmd

        ORCH1   -->|"writes initial task decomposition"| PLAN1
        KAREN1  -->|"appends punch list on PARTIAL/FAIL"| PLAN1
        SECRV1  -->|"appends remediation tasks on FINDINGS"| PLAN1
        PLAN1   -->|"re-read each iteration for pending tasks"| IMPL1
        IMPL1   -->|"triggers re-audit"| KAREN1
        IMPL1   -->|"triggers re-review on PASS"| SECRV1
    end

    subgraph LOOP2 ["↺ Loop 2 — checkpoint.json (resume handover)"]
        direction TB
        SESSION2["session setup"]:::cmd
        CHK2[("checkpoint.json")]:::loop
        CONCERN2["concern-resolver"]:::agent
        STAGE2["each pipeline stage"]:::cmd
        RESUME2["/resume"]:::cmd

        SESSION2  -->|"initial write: stage=interrogate"| CHK2
        CONCERN2  -->|"writes feature_types back"| CHK2
        STAGE2    -->|"advances stage field"| CHK2
        CHK2      -->|"stage field determines re-entry point"| RESUME2
    end

    subgraph LOOP3 ["↺ Loop 3 — PROBLEMS.md (blocker escalation)"]
        direction TB
        KAREN3["karen"]:::agent
        SECRV3["security-reviewer"]:::agent
        PROB3[("PROBLEMS.md")]:::loop
        ORCH3["orchestrator\n(re-run)"]:::agent
        IMPL3["implementation-loop"]:::cmd

        KAREN3 -->|"punch list findings"| PROB3
        SECRV3 -->|"security findings"| PROB3
        PROB3  -->|"fold BLOCKED/CRITICAL into new tasks"| ORCH3
        PROB3  -->|"retry context for failing tasks"| IMPL3
    end
```

---

## Reference Table

| Artifact | Path | Written by | Read by | Loop? |
|---|---|---|---|---|
| `.current_run` | `.current_run` | session setup (`/run`, `/fast-lane`) | `log_tool_call.sh` (routes log destination), `karen`, `security-reviewer`, `session-keeper` | No — cleared at `stage: done` |
| `checkpoint.json` | `sessions/<run_id>/checkpoint.json` | session setup (initial); every stage transition (stage field); `concern-resolver` (feature_types) | `/resume` (re-entry point), `session-keeper` (seeds PROGRESS_TRACKER header) | **↺ Yes** — `concern-resolver` writes `feature_types` back; `/resume` reads `stage` to re-enter |
| `SPEC.md` | `sessions/<run_id>/SPEC.md` | `spec-drafter` | `orchestrator`, `concern-resolver`, `architect` (Trigger A), `implementation-loop`, `karen`, `unit-test-writer` | No — write-once, read-many |
| `PLAN.md` | `sessions/<run_id>/PLAN.md` | `orchestrator` (initial); `karen` (punch list); `security-reviewer` (remediation tasks) | `implementation-loop` (each iteration), `orchestrator` (on re-run, folds blockers) | **↺ Yes** — `karen` and `security-reviewer` append; `implementation-loop` re-reads |
| `ARCHITECTURE.md` (session) | `sessions/<run_id>/ARCHITECTURE.md` | `architect` Trigger A | `orchestrator` (aligns task scopes) | No |
| `ARCHITECTURE.md` (root) | `ARCHITECTURE.md` | `architect` Trigger B (post-karen PASS) | Permanent design record — human and future pipeline runs | No |
| `SECURITY_CONCERNS.md` | `sessions/<run_id>/SECURITY_CONCERNS.md` | `concern-resolver` | `security-reviewer` (mandatory Review Checklist) | No — but `feature_types` extracted here are written back to `checkpoint.json` |
| `PROBLEMS.md` | `sessions/<run_id>/PROBLEMS.md` | `karen` (PARTIAL/FAIL); `security-reviewer` (FINDINGS) | `orchestrator` (re-run: fold blockers), `implementation-loop` (retry context) | **↺ Yes** — multi-writer, append-only; upstream agents re-read on next cycle |
| `PROGRESS_TRACKER.md` | `sessions/<run_id>/PROGRESS_TRACKER.md` | `session-keeper` (sole writer, append-only) | `evaluate-run` (extracts agent traces), `session-autocommit.sh` (triggers auto-commit on every write) | No — but auto-commit hook fires on every write |
| `session_log.json` | `sessions/<run_id>/session_log.json` | `log_tool_call.sh` hook (PostToolUse, when `.current_run` active) | Human / external tooling only | No |
| `tool-calls-YYYY-MM-DD.jsonl` | `sessions/tool-calls-YYYY-MM-DD.jsonl` | `log_tool_call.sh` hook (PostToolUse, when no active run) | Human / external tooling only | No — daily rotation |
| `audits/task-slug.md` | `sessions/<run_id>/audits/<task-slug>.md` | `karen` (when active run context exists) | Human review only | No |
| `traces/<agent>.md` | `sessions/<run_id>/traces/<agent_name>.md` | `evaluate-run` (extracts blocks from PROGRESS_TRACKER) | `agent-evaluator` | No — temp; left in place after run |
| `traces/<agent>.json` | `sessions/<run_id>/traces/<agent_name>.json` | `agent-evaluator` | `evaluate-run` (reads score + verdict to populate EVALUATION.md) | No — but part of a tight read-write loop within `evaluate-run` |
| `EVALUATION.md` | `sessions/<run_id>/EVALUATION.md` | `evaluate-run` | `/run` (appends one-line summary to PROGRESS_TRACKER) | No — idempotent; re-runs overwrite |

---

## Legend

| Color | Meaning |
|---|---|
| Dark green | Artifact (file written to disk) |
| Orange | Artifact in a feedback loop (written by downstream; re-read upstream) |
| Purple | Agent (spawned programmatically) |
| Blue | Command (user-invoked slash command) |
| Dark red | Hook (Claude Code lifecycle event) |
| Dark grey | Observability artifact (audit trail; not read by pipeline agents) |
