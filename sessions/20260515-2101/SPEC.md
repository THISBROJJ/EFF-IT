# context-aware-security-concern-system

## Problem Statement

The F-IT harness runs a security-reviewer agent at the end of the pipeline, but it operates without knowledge of what kind of application is being built or which security concerns are relevant to the feature under development. As a result, reviews are generic, architect plans omit security tasks, and critical concerns (prompt injection, open endpoints, JWT misuse) go undetected until after implementation.

## Goals

- Surface security concerns before the architect writes a plan, giving developers security-aware task lists.
- Produce a deterministic, file-backed concern record (`SECURITY_CONCERNS.md`) that both the architect and security-reviewer agents consume.
- Cover two detection axes: application type (declared in CLAUDE.md) and feature content (SPEC.md keyword scanning).
- Extend the secrets scanner to flag hardcoded `http://` URLs.

## Non-Goals

- No runtime security enforcement or blocking behavior.
- No concern categories beyond the seven listed (open_endpoint, jwt, transport_security, input_handling, prompt_injection, file_upload, auth_authz).
- No application types beyond the nine listed (database, rag, ai_agent, web_app, api, frontend, networking, search, security_tool).
- No changes to the host project's code or dependencies.
- No UI, dashboard, or external reporting.

---

## Functional Requirements

1. `.claude/security-profiles/` contains exactly nine Markdown files (one per app type). Each file includes a threat model paragraph, an architect checklist, and a review checklist.
2. `.claude/security-concerns/` contains exactly seven Markdown files (one per concern category). Each file includes: trigger keywords list, architect checklist items, review checklist items, and a severity field (critical / high / medium).
3. CLAUDE.md accepts an `app_types` field (array of strings). Each string must match a filename in `.claude/security-profiles/` (without `.md`). If absent or empty, concern-resolver skips profile loading and uses trigger-only detection.
4. The `concern-resolver` agent reads SPEC.md from `sessions/{run_id}/`, scans it for trigger keywords from every file in `.claude/security-concerns/`, and activates any concern whose keyword appears at least once (case-insensitive).
5. The `concern-resolver` agent loads all profiles named in `app_types`; if `app_types` is absent, no profiles are loaded.
6. The `concern-resolver` agent writes `sessions/{run_id}/SECURITY_CONCERNS.md` containing: (a) list of triggered concern names with severity, (b) merged architect checklist (union of triggered concerns + loaded profiles, deduped), (c) merged review checklist (same union logic).
7. `SECURITY_CONCERNS.md` is written even when zero concerns are triggered; in that case it contains an explicit "No concerns triggered" notice and empty checklists.
8. `/run` and `/fast-lane` execute the `concern` stage after `spec` and before `architect`.
9. `checkpoint.json` includes a `feature_types` field (array of strings) populated by concern-resolver with the names of all triggered concerns.
10. `/resume` displays a `concern` row in its stage table, showing status from `checkpoint.json`.
11. The architect agent reads `SECURITY_CONCERNS.md` when present and injects each architect checklist item as a numbered task in PLAN.md, interleaved with feature tasks (not in a separate section).
12. The security-reviewer agent reads `SECURITY_CONCERNS.md` and loads relevant profile files. For each review checklist item, it either verifies or explicitly marks the item "unverifiable — [reason]". It does not skip items silently.
13. `scripts/secrets-scanner.sh` flags any hardcoded `http://` URL that does not match localhost, 127.0.0.1, 0.0.0.0, example.com, or a test fixture path. The finding is surfaced in the transcript; the hook exits 0.
14. The `http://` scanner in `secrets-scanner.sh` runs on every Write and Edit (existing PostToolUse hook behavior) without requiring additional hook registration.

---

## Technical Design

### New files

- `.claude/security-profiles/{app_type}.md` (×9): static Markdown, loaded by concern-resolver and security-reviewer.
- `.claude/security-concerns/{concern}.md` (×7): static Markdown, loaded by concern-resolver.
- `.claude/agents/concern-resolver.md`: agent prompt (≤200 lines). Reads SPEC.md, scans keywords, unions profiles, writes SECURITY_CONCERNS.md, updates checkpoint.json `feature_types`.

### Modified files

- `.claude/commands/run.md`: insert `concern` stage call between `spec` and `architect` blocks.
- `.claude/commands/fast-lane.md`: same insertion.
- `.claude/commands/resume.md`: add `concern` row to stage table.
- `.claude/agents/architect.md`: add conditional block — if `SECURITY_CONCERNS.md` exists in session dir, read it and inline architect checklist items into PLAN.md task list.
- `.claude/agents/security-reviewer.md`: add block to load `SECURITY_CONCERNS.md` and profile files; require explicit verification or "unverifiable" annotation per item.
- `scripts/secrets-scanner.sh`: add `http://` URL pattern check with exclusion list.
- `CLAUDE.md`: document `app_types` field under a new "Security Profiles" section.
- `ARCHITECTURE.md`: add `concern` stage to pipeline flow diagram; document new directories.

### Concern-resolver agent flow

```
read SPEC.md
read CLAUDE.md → extract app_types[]
for each file in .claude/security-concerns/:
    if any trigger keyword in SPEC.md (case-insensitive): add to triggered[]
for each type in app_types[]:
    load .claude/security-profiles/{type}.md → add to profiles[]
merge architect checklists (triggered + profiles), dedup lines
merge review checklists (triggered + profiles), dedup lines
write sessions/{run_id}/SECURITY_CONCERNS.md
update sessions/{run_id}/checkpoint.json .feature_types = triggered[].names
```

### Checkpoint schema addition

```json
{
  "feature_types": ["open_endpoint", "jwt"]
}
```

---

## Affected Files

**New**
- `.claude/agents/concern-resolver.md`
- `.claude/security-profiles/database.md`
- `.claude/security-profiles/rag.md`
- `.claude/security-profiles/ai_agent.md`
- `.claude/security-profiles/web_app.md`
- `.claude/security-profiles/api.md`
- `.claude/security-profiles/frontend.md`
- `.claude/security-profiles/networking.md`
- `.claude/security-profiles/search.md`
- `.claude/security-profiles/security_tool.md`
- `.claude/security-concerns/open_endpoint.md`
- `.claude/security-concerns/jwt.md`
- `.claude/security-concerns/transport_security.md`
- `.claude/security-concerns/input_handling.md`
- `.claude/security-concerns/prompt_injection.md`
- `.claude/security-concerns/file_upload.md`
- `.claude/security-concerns/auth_authz.md`

**Modified**
- `.claude/commands/run.md`
- `.claude/commands/fast-lane.md`
- `.claude/commands/resume.md`
- `.claude/agents/architect.md`
- `.claude/agents/security-reviewer.md`
- `scripts/secrets-scanner.sh`
- `CLAUDE.md`
- `ARCHITECTURE.md`

---

## Open Questions

1. Should concern-resolver fail the pipeline (exit non-zero) if `app_types` contains a value with no matching profile file, or should it warn and continue?
2. For keyword scanning, should multi-word trigger phrases require exact phrase match or token-level OR matching?
3. Should the `feature_types` checkpoint field be populated with triggered-concern names only, or also include loaded app-type profile names?
