---
name: git-branch
description: Create, name, and switch branches following trunk-based conventions — always branches from main, enforces type/kebab-name format.
argument-hint: "[intent description | branch-name to validate]"
allowed-tools: [Bash]
---

# Git Branch

Creates or validates a branch following Exelixis trunk-based development rules.
If given a plain-language intent (e.g., "add login page"), derives a correct
branch name and creates it. If given an explicit name, validates it first.

## Scope

Input: `$ARGUMENTS` — either a plain-language description of the work, or an
explicit branch name to validate and create.

Out of scope: committing, pushing, or creating PRs.

---

## § 1 — Derive or validate the branch name

### If `$ARGUMENTS` is a plain-language description

Infer the branch type from the intent:

| Intent signals | Branch type |
|---|---|
| new feature, add X, build X | `feat/` |
| bug, broken, fix, patch | `fix/` |
| docs, readme, comment, docstring | `docs/` |
| config, deps, cleanup, chore | `chore/` |
| hotfix, urgent, prod issue | `hotfix/` |
| refactor, restructure, move | `refactor/` |
| test, spec, coverage | `test/` |

Construct name: `type/2-4-word-kebab-summary`

- Lowercase only. Hyphens only (no underscores, slashes beyond the prefix).
- 2–4 words after the slash.
- Drop articles (a, an, the), prepositions, and filler words.

Good: `feat/user-auth-endpoint`, `fix/null-ptr-on-empty-list`
Bad: `feature/AddUserLoginPage` — wrong case and format
Bad: `fix/issue` — too vague
Bad: `johns-branch` — no type prefix, personal name

### If `$ARGUMENTS` looks like a branch name already

Validate against the rules above. If it violates any rule, propose a corrected
name and ask for confirmation before proceeding.

Print the proposed name and ask: "Create branch `<name>`? (yes/no)"

Wait for confirmation.

---

## § 2 — Ensure main is up to date

```bash
git fetch origin main
git log HEAD..origin/main --oneline
```

If commits are listed, note that the new branch will be based on the latest
remote `main`.

---

## § 3 — Create the branch

```bash
git checkout -b <branch-name> origin/main
```

Do NOT branch from:
- The current feature branch (unless user explicitly requests it with a reason)
- A local `main` that hasn't been fetched — always use `origin/main`
- Any branch named `develop`, `staging`, or `release` unless the repo has
  documented a different trunk and the user confirms

---

## § 4 — Confirm

```bash
git branch --show-current
git log -1 --oneline
```

Print: "Branch `<name>` created from `origin/main` at `<sha>`."

---

## Hard Rules

- Never create a branch from another feature branch without explicit user approval.
- Never use uppercase, underscores, or spaces in a branch name.
- Never allow a branch named `main`, `master`, `develop`, `HEAD`.
- Always use the `type/` prefix.
