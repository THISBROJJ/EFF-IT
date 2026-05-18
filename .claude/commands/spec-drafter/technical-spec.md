# Technical Spec Template

Use for engineering implementation specs: how a feature will be built, the
data model, API surface, rollout plan, and tested. Hybrid format closer to
Stripe / GitHub internal style than any single named public template.

## When to use

- A PRD or design has been agreed and engineering needs to plan implementation
- Cross-team API contracts need to be reviewed before code is written
- A migration, rewrite, or refactor needs a durable record of decisions

## Template

```markdown
# Technical Spec — <title>

## 1. Summary
<2–3 sentences: what we're building and why it matters technically>

## 2. Context & motivation
<link to PRD or issue if one exists; otherwise summarize the driver>

## 3. Goals / Non-goals
### Goals
- <…>
### Non-goals
- <explicit list of what this spec does NOT cover>

## 4. Proposed design
### Architecture
- <components, data flow, sequence of operations>
### Data model
- <entities, relationships, indexes, migrations>
### API surface
- <endpoints / functions / events, request/response contracts, error modes>
### Concurrency & consistency
- <ordering guarantees, idempotency, retry semantics>

## 5. Alternatives considered
| Option | Pros | Cons | Why rejected |
|---|---|---|---|
| … | … | … | … |

## 6. Dependencies & integrations
- Internal services: <…>
- External APIs / vendors: <…>
- Blockers if any of these change: <…>

## 7. Testing strategy
- Unit: <coverage targets, key scenarios>
- Integration: <real-DB tests, contract tests>
- Load / performance: <if relevant>
- Regression: <existing behavior we must not break>

## 8. Rollout & migration
- Feature flag plan: <…>
- Backfill plan: <…>
- Kill switch / rollback: <how we undo this if it goes wrong>
- Data migration: <if applicable>

## 9. Observability
- Metrics: <what we'll track and why>
- Logs: <key events, log levels>
- Alerts: <thresholds, paging policy>
- Dashboards: <where ops will look>

## 10. Security & privacy
- AuthZ / authN model: <…>
- PII / sensitive data handling: <…>
- Threat model summary: <STRIDE or equivalent if non-trivial>

## 11. Open questions
- <unresolved decisions that need owner + deadline>
```

## Filling rules

- Read the codebase before asking the user about existing data models, APIs,
  or modules. Use `Read`, `Glob`, `Grep`.
- The **alternatives considered** table (§5) is the most-skipped section and
  the most-cited section in post-mortems. Insist on it.
- **Kill switch / rollback** (§8) is non-negotiable for anything touching
  production. If the user can't describe one, that's the section to interrogate.
- Mark genuine unknowns with `[GAP: <what's missing>]`.
