---
owner: DevSecOps
status: Draft
---

# git-branch

Create, name, and switch branches following Exelixis trunk-based conventions.

## Overview

Derives a correctly-formatted branch name from a plain-language description (or validates an
explicit name), confirms with the user, then creates the branch from the latest `origin/main`.
Enforces the `type/kebab-name` format required by Exelixis conventions throughout.

## Use Cases

- Starting new work without memorizing branch naming rules
- Validating a branch name before creating it
- Ensuring all branches start from the latest remote main

## How to Use

```
/git-branch add user authentication endpoint
/git-branch fix null pointer on empty dataset
/git-branch feat/user-auth-endpoint
```

Pass a plain-language description and the skill infers the type prefix and kebab slug.
Pass an explicit branch name to validate it first.

## Output

Prints the proposed branch name, waits for confirmation, then reports:
`Branch <name> created from origin/main at <sha>.`

## Additional Notes

- Always calls `git fetch origin main` before branching — never creates from a stale local main.
- Does not commit, push, or create PRs. Chain with `/git-commit` and `/git-pr` for a full workflow.
- Part of the `git-expert` agent's operation router.
