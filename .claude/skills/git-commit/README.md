---
owner: DevSecOps
status: Draft
---

# git-commit

Stage changes and write a well-formed Conventional Commit message following Exelixis conventions.

## Overview

Inspects the working tree, guides file staging, and constructs a `type(scope): description`
commit message that complies with Conventional Commits and Exelixis house rules. Explicitly
forbids AI attribution trailers (`Co-Authored-By: Claude`, `🤖 Generated with…`) and enforces
the ≤72-character subject limit.

## Use Cases

- Committing work without memorizing Conventional Commits format
- Ensuring only related files are grouped in one commit
- Preventing AI footers from appearing in git history

## How to Use

```
/git-commit
/git-commit src/auth.py tests/test_auth.py
/git-commit all
```

Empty invocation enters interactive mode and asks which files to stage.
Pass specific files to stage only those. Pass `all` to stage everything (with a mixed-concern check).

## Output

Prints the staged diff, proposes a commit message in a fenced block, waits for confirmation,
then commits and prints `git log -1 --oneline`.

## Additional Notes

- Never adds AI attribution trailers — Exelixis convention forbids them.
- Rejects commits with subject lines longer than 72 characters.
- Does not push. Chain with `/git-pr` to open a pull request.
- Part of the `git-expert` agent's operation router.
