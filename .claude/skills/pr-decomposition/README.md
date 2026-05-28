---
owner: DevSecOps
status: Beta
---

# pr-decomposition

Decomposes a multi-part task or staged diff into atomic independently-mergeable pull requests with filled PR templates.

## Overview

Large changesets that mix features, bug fixes, refactors, and config updates cause painful reviews, merge conflicts, and accidental regressions. This skill takes either a plain-language task description or your current working-tree diff and splits it into atomic PRs — one concern each — then generates filled PR templates ready to paste. It pauses after the plan so you can redirect before any templates are written.

## Use Cases

- You are about to start a large task and want a decomposition plan before writing any code.
- Your working-tree changes have grown to cover multiple concerns and you need to split them cleanly.
- You want confirmation that a proposed change is truly one PR or whether it should be two.
- You need PR templates filled out for a set of changes for a team review.

## How to Use

```
/pr-decomposition [task description | diff]
```

**Plan from a task description:**
```
/pr-decomposition add OAuth login, refactor the user model, and update the CI pipeline
```

**Plan from current working-tree diff:**
```
/pr-decomposition
/pr-decomposition diff
```

The skill outputs a numbered PR plan and pauses for your confirmation. You can redirect at that point ("merge PR 1 and PR 2", "split PR 3", etc.) before the templates are generated.

## Output

1. **Concern labeling** — every changed file or task component is assigned one concern.
2. **PR plan** — numbered list with description, files, required tests, base branch, and inter-PR dependencies.
3. **Confirmation pause** — waits for approval or redirection.
4. **PR templates** — one filled `What changed / Why / How to test / Secrets?` block per PR.

## Additional Notes

- The skill never writes code, modifies files, or creates commits — it is a planning tool only.
- If the entire changeset is already atomic, the skill says so and outputs one template.
- Test steps that cannot be inferred are marked `TBD` rather than fabricated.
