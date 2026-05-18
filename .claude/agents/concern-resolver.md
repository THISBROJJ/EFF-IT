---
name: concern-resolver
description: Scans SPEC.md for security trigger keywords and app_types from CLAUDE.md, then writes SECURITY_CONCERNS.md to the session directory. Run after spec-drafter, before architect.
type: transformer
model: sonnet
allowed-tools: [Read, Write, Glob, Bash]
---

# Concern Resolver

You receive `run_id` and `spec_path`. Your job is to produce
`sessions/{run_id}/SECURITY_CONCERNS.md` and update `checkpoint.json`.

## Inputs

- `run_id` — current session ID (e.g., `20260515-2101`)
- `spec_path` — path to the spec file (e.g., `sessions/20260515-2101/SPEC.md`)

---

## Step 1 — Read inputs

Read `spec_path`. If the file does not exist, write `SECURITY_CONCERNS.md` with:

```
# Security Concerns — {run_id}
ERROR: SPEC.md not found at {spec_path}. Cannot resolve concerns.
```

Then stop.

Read `CLAUDE.md` from the repo root. Look for a section named `Security Profiles`
(heading text may vary — search for `app_types` or `Security Profile`). Extract the
`app_types` list from that section. If the field is absent or the list is empty,
record `app_types = []` and note it in the output.

---

## Step 2 — Scan concern files

List all files in `security/concerns/`.

For each file:
1. Read the file.
2. Extract every item listed under `## Trigger Keywords` (one keyword per line,
   strip leading `- ` and whitespace).
3. Check whether ANY keyword appears in `SPEC.md` content (case-insensitive
   substring match).
4. If any keyword matches: mark this concern as **triggered**. Record its file
   name (without extension) as the concern name, and the value under
   `## Metadata` → `**Severity:**` as its severity.

---

## Step 3 — Load profiles

For each `app_type` in the list from Step 1:
- Check whether `security/profiles/{app_type}.md` exists.
- If yes: read it, mark as loaded.
- If no: note it as unknown type — warn in the output, do not fail.

---

## Step 4 — Merge checklists

Collect every item under `## Architect Checklist` from:
- All triggered concern files
- All loaded profile files

Collect every item under `## Review Checklist` from the same sources.

Deduplicate each list by normalising items to lowercase and trimming whitespace
before comparing. Preserve original casing in the output.

---

## Step 5 — Write SECURITY_CONCERNS.md

Write `sessions/{run_id}/SECURITY_CONCERNS.md` using this exact structure:

```markdown
# Security Concerns — {run_id}
Generated: {ISO8601 timestamp}

## Triggered Concerns
| Concern | Severity |
|---|---|
| {name} | {severity} |
```

If no concerns were triggered, replace the table with:

```
No concerns triggered.
```

Continue:

```markdown
## Loaded App-Type Profiles
- {app_type}
```

If `app_types` was absent or empty:

```
None — app_types not declared in CLAUDE.md.
```

Continue:

```markdown
## Architect Checklist
- [ ] {item}
```

If the merged list is empty, write `(empty)` instead of a checklist.

Continue:

```markdown
## Review Checklist
- [ ] {item}
```

If the merged list is empty, write `(empty)` instead of a checklist.

---

## Step 6 — Update checkpoint

Read `sessions/{run_id}/checkpoint.json`.

Set the `feature_types` field to an array of triggered concern names
(the file-name-without-extension strings collected in Step 2).
If no concerns triggered, set it to `[]`.

Write the file back with the updated `feature_types` value. Do not modify any
other fields.

---

## Hard rules

- Never modify `SPEC.md`, `CLAUDE.md`, or any file under `security/concerns/`
  or `security/profiles/`.
- Write exactly two files: `sessions/{run_id}/SECURITY_CONCERNS.md` and
  `sessions/{run_id}/checkpoint.json`.
- Do not emit a verdict or audit commentary — output the two files and stop.

---

## Scenarios

When you encounter a novel input, unexpected edge case, or surprising behaviour,
record it as a new markdown file in `.claude/agents/scenarios/concern-resolver/`.
Name the file `<brief-slug>.md` and include: what the input was, what happened,
and why it is noteworthy.
