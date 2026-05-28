# PRD Template

Use for product/feature scope: defining what to build, for whom, and how
success will be measured. Closest public reference: Lenny Rachitsky / Reforge
PRD style. Optional addition: a "time appetite" field borrowed from Shape Up
if the team wants time as an input rather than an estimate.

## When to use

- A new feature, tool, or service is being scoped for engineering kickoff
- Stakeholders need to align on problem, scope, and success metrics
- Decisions about scope and rejected alternatives need a durable home

## Template

```markdown
# PRD — <title>

## 1. One-line pitch
<the confirmed one-liner>

## 2. Problem
<problem statement, evidence, current workaround and its cost>

## 3. Users & stakeholders
- Primary user: <persona>
- Secondary: <list>
- Approvers / vetoers: <list>

## 4. Goals & success metrics
- Outcome: <one sentence, present tense, observable from the outside>
- Metric: <number, direction, deadline — e.g. "reduce X from 12min to <2min by EOQ3">
- Leading indicator (week 1): <…>
- Lagging indicator (month 3): <…>
- Kill criterion: <what outcome would cause us to shut this down in 6 months>

## 5. Scope
### Must-haves (v1)
- <cap at 5>
### Non-goals
- <things people will ask for that we will not do, and why>
### Smallest demonstrable cut
- <what could ship in 2 weeks that proves the core value>

## 6. Key decisions
| Decision | Options considered | Choice | Reason | Reversible? |
|---|---|---|---|---|
| … | … | … | … | … |

## 7. Constraints
- Time: <deadline + what's driving it>
- Budget: <people-weeks or dollars>
- Team: <who's building, what skills are missing>
- Tech / integration: <existing systems this must fit into>
- Regulatory / compliance / data residency: <…>

## 8. Risks & mitigations
1. <risk> — <mitigation>
2. …

## 9. Validation & rollout
- Pre-build validation: <prototype, user interview, fake door, spreadsheet>
- Rollout rings: <dogfood → beta → GA, with exit criteria>
- Day-1 telemetry: <metrics that prove it's working>

## 10. Open gaps
- <every "I don't know yet" answer captured during discovery>
```

## Filling rules

- The **kill criterion** field (§4) is the one most often skipped and most
  often valuable. Push the user to fill it.
- The **rejected alternatives** column in §6 is what separates a real PRD
  from a wish list. Don't let it stay empty.
- **Smallest demonstrable cut** (§5) should be ship-able, not a prototype.
- Mark genuine unknowns with `[GAP: <what's missing>]` rather than inventing
  plausible content.
