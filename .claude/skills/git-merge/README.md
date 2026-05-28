---
owner: DevSecOps
status: Draft
---

# git-merge

Resolve merge and rebase conflicts step by step with guided, interactive conflict resolution.

## Overview

Detects active merge or rebase conflicts, explains each conflict block in plain language
(not just raw code), presents four resolution choices (ours / theirs / both / custom), applies
the chosen resolution, stages the file, and then continues or finalizes the operation. Supports
multi-round rebases automatically.

## Use Cases

- Resolving conflicts without manually editing conflict markers
- Understanding what each conflicting side actually does before choosing
- Safely aborting a merge or rebase mid-way through
- Handling multi-commit rebases that produce multiple conflict rounds

## How to Use

```
/git-merge
/git-merge src/config.py
```

Empty invocation resolves all conflicted files in sequence.
Pass a specific file to target only that conflict.

## Output

For each conflict block: a description of both sides, a numbered menu of resolution choices,
confirmation of the applied resolution, and a `git add` confirmation. Ends with
`git rebase --continue` or `git commit` and a clean-state verification.

## Additional Notes

- Never auto-chooses a resolution — always waits for explicit user input.
- Explains "ours" vs "theirs" differently for merge vs. rebase — easy to confuse otherwise.
- Part of the `git-expert` agent's operation router.
