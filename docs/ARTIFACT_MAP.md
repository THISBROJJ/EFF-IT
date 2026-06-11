# EFF-IT Artifact Map

Companion to `docs/SDLC_FLOWCHART.md`. Focuses on **what is written, by whom, and who reads it** — rather than process flow.

**↺** marks artifacts that participate in feedback loops: a downstream agent writes back to them, and an upstream agent re-reads them in a later iteration.

> Render in any Mermaid-aware viewer (GitHub, VS Code + Mermaid Preview, mermaid.live).

The harness splits into two commands: **`/draft-design-docs`** writes the four durable repo-root docs (`SPEC.md`, `CONCERN.md`, `ARCHITECTURE.md`, `PLAN.md`) and opens a design PR, then stops; **`/build-task`** runs once per task, building it from the master root `PLAN.md` through a session-scoped working slice.

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

    subgraph DESIGN ["/draft-design-docs — design half (writes durable root docs, opens PR, stops)"]
        direction TB

        %% ── Design Session Init ───────────────────────────────────────────────
        DSESSION["session setup\n/draft-design-docs"]:::cmd
        DSESSION -->|"creates"| CURR_RUN{{".current_run"}}:::artifact
        DSESSION -->|"initial write\nphase=design"| DCHK[("checkpoint.json ↺\nphase · stage · slug\nfeature_types")]:::loop

        %% ── Spec Phase ────────────────────────────────────────────────────────
        III["idea-interrogator"]:::agent
        III --> SPEC_D["spec-drafter"]:::agent
        SPEC_D --> SPEC[("SPEC.md · ROOT\nsource of truth\nfor all downstream agents")]:::artifact

        %% ── Security Concerns ─────────────────────────────────────────────────
        SPEC --> CONCERN["concern-resolver"]:::agent
        CONCERN --> SCON[("CONCERN.md · ROOT\ntriggered concerns\nmerged checklists")]:::artifact
        CONCERN -->|"feature_types written back"| DCHK

        %% ── Architecture Draft (now BEFORE orchestrator) ──────────────────────
        SPEC --> ARCH_A["architect · Trigger A\nArchitecture Draft (no plan)"]:::agent
        SCON --> ARCH_A
        ARCH_A --> RARCH[("ARCHITECTURE.md · ROOT\nproposed design\nfor this feature")]:::artifact

        %% ── Orchestrate (reads SPEC + CONCERN + ARCHITECTURE) ─────────────────
        SPEC --> ORCH["orchestrator"]:::agent
        SCON -->|"folds Architect Checklist\ninto security tasks"| ORCH
        RARCH -->|"aligns task scopes"| ORCH
        ORCH --> MPLAN[("PLAN.md · ROOT\nmaster tasklist\nstatus · pr · finalized")]:::artifact

        subgraph ARCH_REVIEW ["Architect Plan Review (inside orchestrator)"]
            direction LR
            ARCH_PR["architect · Plan Review\n(read-only)"]:::agent
            ARCH_PR_V{"APPROVE\nor REVISE?"}
        end
        MPLAN --> ARCH_PR
        ARCH_PR --> ARCH_PR_V
        ARCH_PR_V -->|"REVISE — violations\n(max 2 rounds)"| ORCH
        ARCH_PR_V -->|"APPROVE"| PLAN_FINAL(["PLAN.md finalized: true"])

        %% ── Design PR ─────────────────────────────────────────────────────────
        PLAN_FINAL --> DGIT["git-expert"]:::agent
        DGIT --> DPR[("GitHub PR: docs/design-{slug}\nfour root docs → main")]:::artifact
        DSESSION -->|"cleared at plan-ready"| CURR_RUN
    end

    subgraph BUILD ["/build-task — build half (one buildable task per run)"]
        direction TB

        %% ── Task Pick + Build Session Init ────────────────────────────────────
        MPLAN -->|"pick task: status≠DONE\nAND depends_on all DONE"| BSESSION["session setup\n/build-task"]:::cmd
        BSESSION -->|"creates"| CURR_RUN
        BSESSION -->|"initial write\nphase=build"| BCHK[("checkpoint.json ↺\nphase · stage")]:::loop
        BSESSION --> BGIT["git-expert\nfeat/{task-slug}"]:::agent
        BSESSION -->|"working slice\nfrom picked master task"| SPLAN[("PLAN.md · SESSION ↺\nper-task working slice")]:::loop

        %% ── Implementation Loop ───────────────────────────────────────────────
        SPLAN --> IMPL["implementation-loop"]:::cmd
        SPEC --> IMPL

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

        %% ── Completion Audit ──────────────────────────────────────────────────
        SPEC --> KAREN["karen · completion auditor\n(Opus)"]:::agent
        KAREN -->|"PARTIAL / FAIL — punch list"| SPLAN
        KAREN -->|"findings"| PROB[("PROBLEMS.md ↺\nkaren punch lists\nsecurity findings")]:::loop
        KAREN -->|"full audit report"| AUD[("audits/task-slug.md")]:::obs
        PROB -.->|"retry context"| IMPL

        %% ── Evaluate Run ──────────────────────────────────────────────────────
        PROG --> EVAL_C["evaluate-run"]:::cmd
        EVAL_C --> TMD[("traces/agent.md\nextracted trace blocks · temp")]:::obs
        TMD --> EVAL_A["agent-evaluator\n(Opus)"]:::agent
        EVAL_A --> TJSON[("traces/agent.json\nper-agent scored verdict")]:::obs
        TJSON -->|"per-agent score"| EVAL_C
        EVAL_C --> EVAL[("EVALUATION.md\naggregated scores\noverall verdict")]:::obs

        %% ── Security Review ───────────────────────────────────────────────────
        SCON -->|"review checklist"| SECRV["security-reviewer"]:::agent
        SECRV -->|"FINDINGS — remediation tasks"| SPLAN
        SECRV -->|"findings"| PROB

        %% ── Flip master task status ───────────────────────────────────────────
        KAREN -->|"PASS"| FLIP["/build-task\nflip status: DONE + pr:"]:::cmd
        SECRV -->|"clean"| FLIP
        FLIP -->|"one write per task"| MPLAN

        %% ── Finalization (last task DONE, guarded by finalized) ───────────────
        FLIP -->|"last task DONE\n(guarded by finalized)"| ARCH_B["architect · Trigger B\nappend as-built"]:::agent
        ARCH_B --> RARCH
        FLIP -->|"last task DONE"| SKEEP["spec-keeper"]:::agent
        SKEEP --> DOCSPEC[("docs/SPEC.md\ncross-cycle feature log\nappend-only · idempotent")]:::artifact

        %% ── Atomic PR per task ────────────────────────────────────────────────
        FLIP --> BPR["git-expert"]:::agent
        BPR --> PR[("GitHub PR → main\natomic, per task")]:::artifact
        BSESSION -->|"cleared at done"| CURR_RUN
    end

    %% ── Hooks (always active) ─────────────────────────────────────────────────
    LOG_H["log_tool_call.sh · hook\nPostToolUse — all tools"]:::hook
    CURR_RUN -.->|"routes log destination"| LOG_H
    LOG_H --> SLOG[("session_log.json\nor tool-calls-YYYY-MM-DD.jsonl\none JSONL per tool call")]:::obs

    AC["session-autocommit.sh · hook\nPostToolUse — Write on PROGRESS_TRACKER.md"]:::hook
    PROG -.->|"triggers auto-commit"| AC

    %% ── Resume ────────────────────────────────────────────────────────────────
    DCHK -.->|"phase + stage → re-entry point"| RESUME["/resume-run"]:::cmd
    BCHK -.->|"phase + stage → re-entry point"| RESUME
```

---

## Diagram 2 — Feedback Loops (zoomed in)

Three artifacts form genuine feedback loops — downstream agents write back, upstream agents re-read in the next iteration.

```mermaid
flowchart LR
    classDef loop  fill:#E65100,stroke:#BF360C,color:#fff
    classDef agent fill:#6A1B9A,stroke:#4A148C,color:#fff
    classDef cmd   fill:#1565C0,stroke:#0D47A1,color:#fff

    subgraph LOOP1 ["↺ Loop 1 — session PLAN.md (implementation retry)"]
        direction TB
        FASTLANE1["/build-task"]:::cmd
        SPLAN1[("PLAN.md · SESSION")]:::loop
        KAREN1["karen"]:::agent
        SECRV1["security-reviewer"]:::agent
        IMPL1["implementation-loop"]:::cmd

        FASTLANE1 -->|"seeds working slice from picked master task"| SPLAN1
        KAREN1    -->|"appends punch list on PARTIAL/FAIL"| SPLAN1
        SECRV1    -->|"appends remediation tasks on FINDINGS"| SPLAN1
        SPLAN1    -->|"re-read each iteration for pending items"| IMPL1
        IMPL1     -->|"triggers re-audit"| KAREN1
        IMPL1     -->|"triggers re-review on PASS"| SECRV1
    end

    subgraph LOOP2 ["↺ Loop 2 — checkpoint.json (resume handover)"]
        direction TB
        SESSION2["session setup\n/draft-design-docs · /build-task"]:::cmd
        CHK2[("checkpoint.json")]:::loop
        CONCERN2["concern-resolver"]:::agent
        STAGE2["each pipeline stage"]:::cmd
        RESUME2["/resume-run"]:::cmd

        SESSION2  -->|"initial write: phase + stage"| CHK2
        CONCERN2  -->|"writes feature_types back"| CHK2
        STAGE2    -->|"advances stage field"| CHK2
        CHK2      -->|"phase + stage determine re-entry point"| RESUME2
    end

    subgraph LOOP3 ["↺ Loop 3 — PROBLEMS.md (blocker escalation)"]
        direction TB
        KAREN3["karen"]:::agent
        SECRV3["security-reviewer"]:::agent
        PROB3[("PROBLEMS.md")]:::loop
        IMPL3["implementation-loop"]:::cmd

        KAREN3 -->|"punch list findings"| PROB3
        SECRV3 -->|"security findings"| PROB3
        PROB3  -->|"retry context for failing tasks"| IMPL3
    end
```

---

## Reference Table

| Artifact | Path | Written by | Read by | Loop? |
|---|---|---|---|---|
| `.current_run` | `.current_run` | session setup (`/draft-design-docs`, `/build-task`) | `log_tool_call.sh` (routes log destination), `karen`, `security-reviewer`, `session-keeper` | No — cleared at `plan-ready` (design) / `done` (build) |
| `checkpoint.json` | `sessions/<run_id>/checkpoint.json` | session setup (initial, sets `phase`); every stage transition (stage field); `concern-resolver` (feature_types) | `/resume-run` (reads `phase` + `stage` for re-entry), `session-keeper` (seeds PROGRESS_TRACKER header) | **↺ Yes** — `concern-resolver` writes `feature_types` back; `/resume-run` reads `phase` + `stage` to re-enter |
| `SPEC.md` (root) | `SPEC.md` | `spec-drafter` | `concern-resolver`, `architect` (Trigger A), `orchestrator`, `implementation-loop`, `karen`, `security-reviewer`, `unit-test-writer` | No — durable/committed; write-once, read-many |
| `CONCERN.md` (root) | `CONCERN.md` | `concern-resolver` (from root SPEC.md) | `architect` (Trigger A), `orchestrator` (folds Architect Checklist into security tasks), `security-reviewer` (Review Checklist) | No — durable/committed; but `feature_types` extracted here are written back to `checkpoint.json` |
| `ARCHITECTURE.md` (root) | `ARCHITECTURE.md` | `architect` Trigger A (Architecture Draft, before orchestrator); `architect` Trigger B (appends as-built at finalization) | `orchestrator` (aligns task scopes); permanent design record for humans and future runs | No — single durable doc; Trigger A writes, Trigger B appends |
| `PLAN.md` (master, root) | `PLAN.md` | `orchestrator` (initial master tasklist, every task `status: TODO`, empty `pr:`, `finalized: false`); `/build-task` (flips `status: DONE` + `pr:` per task; sets `finalized`) | `/build-task` (picks buildable task: status≠DONE AND all `depends_on` DONE; seeds session slice) | No — durable/committed; one status/pr flip per task, not a tight loop |
| `PLAN.md` (session) | `sessions/<run_id>/PLAN.md` | `/build-task` (seeds working slice from picked master task); `karen` (punch list on PARTIAL/FAIL); `security-reviewer` (remediation tasks on FINDINGS) | `implementation-loop` (re-reads each iteration) | **↺ Yes** — per-task working slice; `karen` and `security-reviewer` append; `implementation-loop` re-reads |
| `docs/SPEC.md` | `docs/SPEC.md` | `spec-keeper` (at finalization, append-only, idempotent) | Human / future pipeline runs (cross-cycle feature log) | No — append-only; idempotent re-appends |
| `PROBLEMS.md` | `sessions/<run_id>/PROBLEMS.md` | `karen` (PARTIAL/FAIL); `security-reviewer` (FINDINGS) | `implementation-loop` (retry context) | **↺ Yes** — session-scoped, multi-writer, append-only; `implementation-loop` re-reads on next cycle |
| `PROGRESS_TRACKER.md` | `sessions/<run_id>/PROGRESS_TRACKER.md` | `session-keeper` (sole writer, append-only) | `evaluate-run` (extracts agent traces), `session-autocommit.sh` (triggers auto-commit on every write) | No — but auto-commit hook fires on every write |
| `session_log.json` | `sessions/<run_id>/session_log.json` | `log_tool_call.sh` hook (PostToolUse, when `.current_run` active) | Human / external tooling only | No |
| `tool-calls-YYYY-MM-DD.jsonl` | `sessions/tool-calls-YYYY-MM-DD.jsonl` | `log_tool_call.sh` hook (PostToolUse, when no active run) | Human / external tooling only | No — daily rotation |
| `audits/task-slug.md` | `sessions/<run_id>/audits/<task-slug>.md` | `karen` (when active run context exists) | Human review only | No |
| `traces/<agent>.md` | `sessions/<run_id>/traces/<agent_name>.md` | `evaluate-run` (extracts blocks from PROGRESS_TRACKER) | `agent-evaluator` | No — temp; left in place after run |
| `traces/<agent>.json` | `sessions/<run_id>/traces/<agent_name>.json` | `agent-evaluator` | `evaluate-run` (reads score + verdict to populate EVALUATION.md) | No — but part of a tight read-write loop within `evaluate-run` |
| `EVALUATION.md` | `sessions/<run_id>/EVALUATION.md` | `evaluate-run` | `/build-task` (appends one-line summary to PROGRESS_TRACKER) | No — idempotent; re-runs overwrite |

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
