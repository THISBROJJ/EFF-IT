---
owner: DevSecOps
status: Draft
---

# git-pr

Create a GitHub pull request following Exelixis conventions — imperative title, structured body, base main.

## Overview

Verifies prerequisites (not on main, clean tree, branch pushed), then guides the user through
collecting a title, summary bullets, and a test plan checklist before calling `gh pr create`.
Enforces Exelixis PR conventions: imperative title ≤70 chars, no AI attribution trailers,
draft flag for WIP work.

## Use Cases

- Opening a PR without remembering `gh pr create` flags
- Ensuring every PR has a structured summary and test plan
- Creating draft PRs for work in progress
- Getting next-step commands (reviewers, CI checks, merge) after the PR opens

## How to Use

```
/git-pr
/git-pr "Add OAuth2 PKCE flow"
/git-pr draft
```

Empty invocation enters guided mode and infers the title from recent commits.
Pass a title string to skip the inference step. Pass `draft` to open as a draft PR.

## Output

PR URL from `gh pr create`, followed by next-step commands for requesting reviewers,
checking CI, and merging.

## Additional Notes

- Requires the `gh` CLI to be authenticated.
- Refuses to open a PR from `main` — use `/git-branch` first.
- No AI attribution footers are added to the PR body (Exelixis convention).
- Part of the `git-expert` agent's operation router.
