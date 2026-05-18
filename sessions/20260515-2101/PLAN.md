# PLAN.md — context-aware-security-concern-system

## Phase 1 — Foundation: Security Concern Data Files

**T1** — Create `.claude/security-concerns/open_endpoint.md` with trigger keywords, severity (high), architect checklist, and review checklist
- File: `.claude/security-concerns/open_endpoint.md`
- Dep: none

**T2** — Create `.claude/security-concerns/jwt.md` with trigger keywords, severity (high), architect checklist, and review checklist
- File: `.claude/security-concerns/jwt.md`
- Dep: none

**T3** — Create `.claude/security-concerns/transport_security.md` with trigger keywords, severity (high), architect checklist, and review checklist
- File: `.claude/security-concerns/transport_security.md`
- Dep: none

**T4** — Create `.claude/security-concerns/input_handling.md` with trigger keywords, severity (medium), architect checklist, and review checklist
- File: `.claude/security-concerns/input_handling.md`
- Dep: none

**T5** — Create `.claude/security-concerns/prompt_injection.md` with trigger keywords, severity (critical), architect checklist, and review checklist
- File: `.claude/security-concerns/prompt_injection.md`
- Dep: none

**T6** — Create `.claude/security-concerns/file_upload.md` with trigger keywords, severity (high), architect checklist, and review checklist
- File: `.claude/security-concerns/file_upload.md`
- Dep: none

**T7** — Create `.claude/security-concerns/auth_authz.md` with trigger keywords, severity (critical), architect checklist, and review checklist
- File: `.claude/security-concerns/auth_authz.md`
- Dep: none

---

## Phase 2 — Foundation: Security Profile Data Files

**T8** — Create three security profiles: `database.md`, `rag.md`, `ai_agent.md` — each with threat model paragraph, architect checklist, and review checklist
- Files: `.claude/security-profiles/database.md`, `.claude/security-profiles/rag.md`, `.claude/security-profiles/ai_agent.md`
- Dep: none

**T9** — Create three security profiles: `web_app.md`, `api.md`, `frontend.md` — same structure
- Files: `.claude/security-profiles/web_app.md`, `.claude/security-profiles/api.md`, `.claude/security-profiles/frontend.md`
- Dep: none

**T10** — Create three security profiles: `networking.md`, `search.md`, `security_tool.md` — same structure
- Files: `.claude/security-profiles/networking.md`, `.claude/security-profiles/search.md`, `.claude/security-profiles/security_tool.md`
- Dep: none

---

## Phase 3 — Core Agent: concern-resolver

**T11** — Create `.claude/agents/concern-resolver.md` — agent that reads SPEC.md and CLAUDE.md, scans trigger keywords, loads matching profiles, writes `sessions/{run_id}/SECURITY_CONCERNS.md`, updates `checkpoint.json` `feature_types` field; ≤200 lines
- File: `.claude/agents/concern-resolver.md`
- Dep: T1–T10 (references those directories)

---

## Phase 4 — Secrets Scanner Extension

**T12** — Add `http://` URL pattern to `scripts/secrets-scanner.sh` — grep pattern excludes `localhost`, `127.0.0.1`, `0.0.0.0`, `example.com`, and paths containing `test`/`fixture`; hook exits 0, surfaces findings in transcript
- File: `scripts/secrets-scanner.sh`
- Dep: none

---

## Phase 5 — Pipeline Command Updates

**T13** — Update `.claude/commands/run.md` — insert `concern` stage block between the `spec` block (Step 2) and the `architect` block (Step 4.5); spawn `concern-resolver` agent, pass `run_id` and `spec_path`; update checkpoint to `stage: concern` before call and `stage: architect` after; include `"feature_types": []` in initial checkpoint template
- File: `.claude/commands/run.md`
- Dep: T11

**T14** — Update `.claude/commands/fast-lane.md` — insert same `concern` stage block; include `"feature_types": []` in initial checkpoint template
- File: `.claude/commands/fast-lane.md`
- Dep: T11

**T15** — Update `.claude/commands/resume.md` — add `concern` row to the stage dispatch table (between `branch` and `orchestrate`); resume action: spawn concern-resolver, continue to orchestrate
- File: `.claude/commands/resume.md`
- Dep: T11

---

## Phase 6 — Agent Behaviour Updates

**T16** — Update `.claude/agents/architect.md` — add conditional block: if `sessions/{run_id}/SECURITY_CONCERNS.md` exists, read it and inject each architect checklist item as a numbered task interleaved in PLAN.md (not a separate section); keep total prompt ≤200 lines
- File: `.claude/agents/architect.md`
- Dep: T11

**T17** — Update `.claude/agents/security-reviewer.md` — add Step 0: if `SECURITY_CONCERNS.md` exists, read it and load referenced profile files; expand report template to include a checklist section where each review item is explicitly verified or marked "unverifiable — [reason]"; keep total prompt ≤200 lines
- File: `.claude/agents/security-reviewer.md`
- Dep: T11

---

## Phase 7 — Documentation and Schema

**T18** — Update `CLAUDE.md` — add "Security Profiles" section documenting the `app_types` field: accepted values, usage by concern-resolver, behavior when absent or empty
- File: `CLAUDE.md`
- Dep: T8–T10, T11

**T19** — Update `ARCHITECTURE.md` — add `concern` stage to pipeline flow; add new directories to layer map; add `SECURITY_CONCERNS.md` to session structure; add `feature_types` to checkpoint schema
- File: `ARCHITECTURE.md`
- Dep: T11, T13, T14

---

## Phase 8 — Validation Fixtures

**T20** — Create `tests/fixtures/concern-resolver-keyword-hit/SPEC.md` — minimal spec with trigger keywords from ≥3 concern files
- File: `tests/fixtures/concern-resolver-keyword-hit/SPEC.md`
- Dep: T1–T7

**T21** — Create `tests/fixtures/concern-resolver-no-hit/SPEC.md` — minimal spec with no trigger keywords (zero-concern path)
- File: `tests/fixtures/concern-resolver-no-hit/SPEC.md`
- Dep: T1–T7

**T22** — Create `tests/fixtures/concern-resolver-keyword-hit/CLAUDE.md` — minimal CLAUDE.md with `app_types: ["api", "web_app"]`
- File: `tests/fixtures/concern-resolver-keyword-hit/CLAUDE.md`
- Dep: T8–T10
