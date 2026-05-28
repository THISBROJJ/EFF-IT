---
owner: DevSecOps
status: Draft
---

# spec-drafter

Drafts a PRD, technical spec, design doc, or spec-driven-development
feature spec from existing conversation context — picking the right
template, filling what's known, and asking targeted questions only for
the remaining gaps.

## Overview

Most "write me a spec" requests follow a discovery conversation that
already contains 80% of the answers. This skill harvests that context
first and only interrupts the user with the questions it genuinely can't
answer from what's already been said (or from reading the codebase).
Produces one of five artifacts:

- **PRD** — product/feature scope, success metrics, rollout
- **Technical spec** — engineering design, data model, API surface, testing
- **Design doc** — Google-style context / goals / alternatives / risks
- **Spec Kit feature spec** — GitHub `spec-kit` style: prioritized user
  stories, FR-### IDs, Given-When-Then scenarios, tech-agnostic
- **Tessl `.spec.md`** — repo-resident executable spec with `targets`
  and inline `[@test]` links for mechanical traceability

## Use Cases

- Turning a prior `idea-interrogator` session into a PRD
- Writing a tech spec for a feature whose design has been discussed
- Producing a design doc for stakeholder review of a non-trivial change
- Capturing a verbal design decision in a durable, reviewable form

## How to Use

```
/spec-drafter [prd|tech-spec|design-doc|speckit|tessl] [optional title]
```

Examples:

```
/spec-drafter prd
/spec-drafter tech-spec "experiment-tracking dashboard"
/spec-drafter design-doc
/spec-drafter speckit "shopping cart checkout"
/spec-drafter tessl "auth module"
```

If you skip the type, the skill will ask once — the templates differ
enough that picking matters.

## Output

1. One-line statement of which template is being used and why
2. Targeted questions for any genuine gaps the conversation didn't cover
3. The filled markdown artifact with `[GAP: …]` markers where information
   is missing
4. An offer to write the file (default paths: `docs/prd/<slug>.md`,
   `docs/spec/<slug>.md`, `docs/design/<slug>.md`)

## Additional Notes

- Designed to follow `idea-interrogator`, but works standalone if the
  user pastes notes or has had a substantive design discussion already
- Reads the codebase for tech specs and design docs (data models, APIs,
  existing modules) rather than asking the user to retype things
- Marks gaps explicitly instead of inventing plausible content — a doc
  full of `[GAP: …]` tags is more useful than one full of best guesses
- One artifact per invocation; run again for additional doc types
