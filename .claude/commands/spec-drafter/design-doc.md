# Design Doc Template (Google-style)

Use for architectural designs that span teams or have long-lived consequences.
Modeled on the widely-cited Google design doc format. Distinct from a tech
spec in emphasis: design docs argue for a *shape*, tech specs nail down an
*implementation*.

## When to use

- A design will affect multiple services or teams
- The decision is hard to reverse later (data model, protocol, contract)
- Stakeholders outside the building team need to weigh in

## Template

```markdown
# Design Doc — <title>

## Status
<draft | in review | accepted | superseded by [link]>

## Authors & reviewers
- Author: <…>
- Reviewers: <…>

## 1. Context
<what's the situation today, why is a design needed now>

## 2. Goals
- <…>

## 3. Non-goals
- <explicit list>

## 4. Overview
<one-paragraph elevator pitch of the proposed design>

## 5. Detailed design
<the meat — components, interactions, data flows, sequencing>

## 6. Alternatives considered
### Alternative A: <name>
- What it is: <…>
- Why rejected: <…>

### Alternative B: <name>
- What it is: <…>
- Why rejected: <…>

## 7. Cross-cutting concerns
- Security: <…>
- Privacy: <…>
- Compliance: <…>
- Cost: <…>
- Operations: <on-call burden, runbook implications>

## 8. Risks
- <risk> — <likelihood, impact, mitigation>

## 9. Open questions
- <…>
```

## Filling rules

- The **alternatives considered** section is the heart of the doc. A design
  doc with one alternative is a proposal; with three or more it's a design.
- **Non-goals** (§3) prevents scope creep in review. Push for at least three.
- **Cross-cutting concerns** (§7) is where most designs are weakest — security,
  privacy, and ops are afterthoughts. Read the codebase for existing patterns
  rather than asking the user to invent them.
- Mark genuine unknowns with `[GAP: <what's missing>]`.

## Pairs with

- **ADR** for narrower single-decision records that don't justify a full
  design doc
- **Tech spec** as the implementation layer once a design doc is accepted
