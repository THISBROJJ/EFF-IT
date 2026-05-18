# GitHub Spec Kit — Feature Specification

Adapted from [github/spec-kit](https://github.com/github/spec-kit) — a
toolkit for spec-driven development where specifications become executable
inputs to a `specify → plan → tasks → implement` workflow.

This template is **technology-agnostic by design**: tech-stack decisions
belong in the companion `plan.md`, not here. Specs answer *what* and *why*;
plans answer *how*.

## When to use

- The team practices spec-driven development with separate spec / plan / tasks
  artifacts (or wants to)
- Requirements need stable IDs (FR-001, SC-001) for traceability into tests
  and tasks
- User stories must be independently testable so each one is its own MVP
  slice
- Stakeholders need an explicit "Review & Acceptance" gate before any code
  is written

## Distinguishing features vs. a generic PRD

- **Prioritized, independently testable user stories** (P1/P2/P3), each
  shippable on its own
- **Given-When-Then acceptance scenarios** per story
- **Stable requirement IDs** (`FR-001`, `SC-001`) for traceability
- **`[NEEDS CLARIFICATION: …]` markers** in-line where the spec is
  ambiguous — these are first-class, not footnotes
- **Measurable success criteria are mandatory**, not aspirational
- **Pairs with `plan.md`** for tech context (language, dependencies,
  storage, testing, performance goals, constraints, scale)

## Template

```markdown
# Feature Specification: <FEATURE NAME>

**Feature Branch**: `<###-feature-name>`
**Created**: <DATE>
**Status**: Draft
**Input**: User description: "<original request>"

## User Scenarios & Testing *(mandatory)*

<!--
Each user story must be INDEPENDENTLY TESTABLE — implementing just one
should still deliver a viable MVP. Assign P1 (most critical), P2, P3, …
-->

### User Story 1 — <Brief Title> (Priority: P1)

<plain-language description of the user journey>

**Why this priority**: <…>

**Independent Test**: <how this can be tested standalone — e.g.,
"verifiable by [action] which delivers [value]">

**Acceptance Scenarios**:

1. **Given** <initial state>, **When** <action>, **Then** <expected outcome>
2. **Given** …, **When** …, **Then** …

---

### User Story 2 — <Brief Title> (Priority: P2)

<…>

---

### Edge Cases

- What happens when <boundary condition>?
- How does the system handle <error scenario>?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST <specific capability>
- **FR-002**: Users MUST be able to <key interaction>
- **FR-003**: System MUST <data requirement>

*Marking unclear requirements:*

- **FR-004**: System MUST authenticate users via [NEEDS CLARIFICATION:
  auth method not specified — email/password, SSO, OAuth?]

### Key Entities *(include if feature involves data)*

- **<Entity 1>**: <what it represents, key attributes — no implementation>
- **<Entity 2>**: <relationships to other entities>

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: <measurable metric — e.g., "Users complete account creation
  in under 2 minutes">
- **SC-002**: <measurable metric — e.g., "System handles 1000 concurrent
  users without degradation">
- **SC-003**: <user satisfaction metric>
- **SC-004**: <business metric — e.g., "Reduce support tickets for X by 50%">

## Assumptions

- <assumption about target users>
- <assumption about scope boundaries — e.g., "mobile out of scope for v1">
- <assumption about data/environment>
- <dependency on existing system or service>
```

## Companion artifact: plan.md

If the team is doing full Spec Kit, the spec is followed by an
implementation plan with these sections:

- **Technical Context** — language/version, primary dependencies, storage,
  testing framework, target platform, project type, performance goals,
  constraints, scale/scope. Each may be marked `NEEDS CLARIFICATION`.
- **Constitution Check** — gating check against project principles before
  research begins, re-checked after design.
- **Project Structure** — concrete directory layout (single project / web /
  mobile-+-API).
- **Complexity Tracking** — table justifying any constitution violations.

If the user wants both, run `spec-drafter` once for the feature spec and
again for the plan.

## Filling rules

- **Never embed tech-stack decisions in the spec.** "Use Postgres" belongs
  in plan.md, not FR-NNN. If the user offers a tech detail during
  drafting, push it to the plan or assumptions section.
- **Stable IDs are non-negotiable.** Don't renumber FR-### or SC-### when
  inserting; append. Tests and tasks reference these IDs.
- **Use `[NEEDS CLARIFICATION: <question>]` liberally.** It's better to
  ship a spec with five clarification markers than one with five plausible
  guesses.
- **Independent testability is the bar for "user story".** If two stories
  can't ship separately, they're one story.
- **Success criteria must be measurable from outside the system.** Reject
  "the system is fast"; demand "p95 latency < 200ms at 1000 RPS".
```
