---
name: spec-drafter
description: Drafts a PRD, technical spec, design doc, or spec-driven-development feature spec (GitHub Spec Kit / Tessl) from prior conversation context. Picks the template based on the artifact type and fills it from what's already been discussed, asking only the targeted questions needed to fill remaining gaps.
argument-hint: "[prd|tech-spec|design-doc|speckit|tessl] [optional title]"
allowed-tools: [Read, Write, Edit, Glob, Grep]
---

# Spec Drafter

Produces a written artifact from context that's already in the
conversation — typically a prior interrogation or design discussion.
Picks the template, fills what's known, asks targeted questions only
for the gaps that matter for that artifact type.

## Inputs

- **Doc type**: one of the five below. If the user didn't specify, ask
  once — the templates differ materially in shape and audience.
- **Title**: optional; infer from context if absent.
- **Source**: prior conversation by default. If the conversation is thin,
  ask the user to paste notes or invoke `idea-interrogator` first.

## Templates

Each template lives in its own reference file. Read the relevant one
**before** drafting — the file contains the structure, the filling rules,
and notes on which sections are typically weakest.

| Doc type | Reference file | Use for |
|---|---|---|
| `prd` | `references/prd.md` | Product/feature scope, success metrics, rollout. Narrative form. |
| `tech-spec` | `references/technical-spec.md` | Engineering implementation, API surface, data model, rollout |
| `design-doc` | `references/design-doc.md` | Cross-team architecture, hard-to-reverse decisions (Google-style) |
| `speckit` | `references/speckit-spec.md` | Spec-driven dev with prioritized user stories, FR-### IDs, Given-When-Then, separate `plan.md`. Tech-stack-agnostic by design. |
| `tessl` | `references/tessl-spec.md` | Repo-resident `.spec.md` with `targets` and inline `[@test]` links. Implementation-coupled, single logical unit. |

**Picking between them** when the user is ambiguous:

- Stakeholder-facing, product-shaped → `prd`
- Engineering-facing, implementation-shaped → `tech-spec`
- Architectural, cross-team, alternatives-heavy → `design-doc`
- Team practices spec-driven-development with separate spec/plan/tasks → `speckit`
- Spec needs to live in the repo with mechanical test traceability → `tessl`

## Rules

1. **Read the reference file first.** Each template ships with filling
   rules that are easy to skip. Don't.

2. **Fill from context first, ask second.** Pull every field you can from
   the prior conversation before asking the user anything. Only ask about
   fields the conversation didn't cover.

3. **Read the codebase when relevant.** For technical specs and design
   docs especially, read existing schemas, modules, and configs rather
   than asking the user to describe them.

4. **One artifact per invocation.** Don't try to produce all three from
   one pass. If the user wants both a PRD and a tech spec, run twice.

5. **Mark gaps explicitly.** Use `[GAP: <what's missing>]` inline rather
   than inventing plausible content. Real gaps are more useful than
   plausible-looking placeholders.

6. **Confirm the path before writing.** Suggest a default based on doc type
   and always confirm before invoking Write:
   - `prd` → `docs/prd/<slug>.md`
   - `tech-spec` → `docs/spec/<slug>.md`
   - `design-doc` → `docs/design/<slug>.md`
   - `speckit` → `specs/<###-feature-name>/spec.md`
   - `tessl` → `specs/<feature>.spec.md` (next to the code it targets)

## Output

1. State which template you're using and why (one line)
2. Targeted questions for the gaps you can't fill from context (if any)
3. The filled markdown artifact with explicit `[GAP: …]` markers where
   information is genuinely missing
4. An offer to write it to disk at the suggested path
