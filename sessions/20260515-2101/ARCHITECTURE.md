# Context-Aware Security Concern System — Architecture

## Overview

This feature inserts a `concern-resolver` stage into the F-IT pipeline between spec and architect, and enriches both the architect and security-reviewer stages with context-aware, app-type-scoped security guidance.

---

## Components and Responsibilities

### 1. Security Concern Definitions (`.claude/security-concerns/`)

Seven static Markdown files (open_endpoint, jwt, transport_security, input_handling, prompt_injection, file_upload, auth_authz). Each file contains:
- `trigger_keywords`: list used for keyword scanning against SPEC.md
- `severity`: critical | high | medium
- `architect_checklist`: tasks injected into PLAN.md as interleaved steps
- `review_checklist`: items verified by the security-reviewer agent

Read-only at runtime. Encode domain knowledge independently of any specific run.

### 2. App-Type Security Profiles (`.claude/security-profiles/`)

Nine static Markdown files (database, rag, ai_agent, web_app, api, frontend, networking, search, security_tool). Each profiles the threat surface for that app type with curated architect and review checklist items.

Loaded by matching the `app_types` field declared in `CLAUDE.md`. Multiple profiles may be loaded and unioned.

### 3. `concern-resolver` Agent (`.claude/agents/concern-resolver.md`)

Runs once per session, after `spec-drafter` and before `architect`. Responsibilities:
- Reads `sessions/{run_id}/SPEC.md`
- Scans SPEC text against trigger keywords in all seven concern files (case-insensitive)
- Reads `CLAUDE.md` to extract `app_types`
- Loads matched concern files + applicable profile files
- Unions and deduplicates architect and review checklists from both layers
- Writes `sessions/{run_id}/SECURITY_CONCERNS.md`
- Updates `checkpoint.json` `feature_types` field with triggered concern names

### 4. `sessions/{run_id}/SECURITY_CONCERNS.md`

Session-scoped artifact. Canonical contract between concern-resolver and downstream agents. Written once by concern-resolver; read by architect and security-reviewer. Never modified after initial write. Contains:
- Triggered concerns list with severity
- Merged architect checklist
- Merged review checklist
- "No concerns triggered" notice if zero hits

### 5. Architect Agent Update

After PLAN.md is drafted, reads `SECURITY_CONCERNS.md` and interleaves architect checklist items as numbered tasks within PLAN.md — not in a separate section.

### 6. Security-Reviewer Agent Update

At review start, loads `SECURITY_CONCERNS.md` and relevant profile files. Emits explicit PASS/FAIL/UNVERIFIABLE verdict per review checklist item. Does not skip items silently.

### 7. `secrets-scanner.sh` Extension

Adds a pattern pass for hardcoded `http://` URLs. Exclusion list: `localhost`, `127.0.0.1`, `0.0.0.0`, `example.com`, paths containing `test` or `fixture`. Reports file + line; exits 0.

### 8. `CLAUDE.md` Schema Addition

New `app_types` field — array of strings matching profile filenames (without `.md`). Absent or empty = trigger-only detection with a warning emitted in SECURITY_CONCERNS.md.

---

## Data Flow

```
SPEC.md + CLAUDE.md
        |
        v
  concern-resolver
        |
        v
SECURITY_CONCERNS.md  ──────────────────────────────────┐
        |                                                |
        v                                                v
  architect agent                             security-reviewer agent
  (interleaves PLAN.md tasks)                 (verifies review checklist)
```

Pipeline insertion: `run.md`, `fast-lane.md`, and `resume.md` each invoke `concern-resolver` after `spec-drafter` and before `architect`.

---

## Technology Choices

- **Static Markdown** for concern/profile definitions: no parser dependency, human-editable, diff-friendly, consistent with the harness convention.
- **Agent-based keyword scanning**: concern-resolver is a Claude agent, not a regex script — tolerates paraphrased triggers and synonyms.
- **Session-scoped artifact**: `SECURITY_CONCERNS.md` follows the existing `SPEC.md`/`PLAN.md` pattern — one canonical file per run, written once, read by later stages.
- **Bash for http:// scanner**: extends the existing `secrets-scanner.sh` in-language, no new dependency.

---

## Constraints and Risks

| Risk | Mitigation |
|---|---|
| `app_types` missing from CLAUDE.md | concern-resolver emits warning; profile layer skipped gracefully |
| Profile filename mismatch | concern-resolver validates declared app_types against filesystem; unknown types logged and skipped |
| Architect checklist injection ordering | Unplaced items appended at end of PLAN.md rather than dropped |
| SECURITY_CONCERNS.md absent on resume | `resume.md` checks for file; if absent, re-runs concern-resolver before continuing |
| http:// false positives | Exclusion list covers common dev/test cases; list is extensible |
