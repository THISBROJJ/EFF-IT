---
owner: DevSecOps
status: Draft
---

# architect

Explore the codebase and surface deepening opportunities — refactors that turn shallow agents,
skills, and hooks into deep, well-seamed modules.

## Overview

The architect skill walks the repository, identifies structural friction (shallow modules,
broken locality, leaking seams), and presents numbered deepening opportunities for the user
to explore interactively. When the user picks a candidate, it runs a "grilling loop" that
examines design alternatives in parallel before recommending a direction. As decisions
crystallize, it offers to record ADRs and update `ARCHITECTURE.md`.

## Use Cases

- Surface refactoring opportunities before starting a new feature
- Identify tightly-coupled modules that make testing difficult
- Get an independent architectural second opinion on a proposed design
- Generate ADRs for structural decisions that should not be revisited

## How to Use

```
/architect
/architect src/agents/
/architect "why is the auth module so hard to test?"
```

With no argument, the skill walks the full repo. Pass a path or topic to focus the analysis.

## Output

A numbered list of deepening opportunities, each with: files involved, problem description,
proposed solution, benefits, and dependency category. Ends with a prompt to pick a candidate
for deeper exploration.

## Additional Notes

- The `architect` agent (spawned by `orchestrator` for plan review) is strictly read-only and
  does not run the grilling loop — it only returns APPROVE or REVISE verdicts.
- Requires `ARCHITECTURE.md` and optionally `docs/adr/` to be present for full context.
