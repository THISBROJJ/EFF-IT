---
name: git-pr
description: Create a GitHub pull request following Exelixis conventions — imperative title ≤70 chars, structured body, base main, draft flag for WIP. Wraps gh pr create.
argument-hint: "[title | 'draft' for a draft PR | empty for guided mode]"
allowed-tools: [Bash, Glob, Grep, Read]
---

# Git PR — Pull Request Creation

Creates a well-formed GitHub PR against `main` using `gh pr create`.
Enforces Exelixis PR conventions and collects any missing information
before opening.

## Scope

Input: `$ARGUMENTS` — an optional title string, the word `draft`, or empty
(guided mode: gathers title and context from the current branch).

Out of scope: code review, approvals, merging the PR.

---

## § 1 — Verify prerequisites

```bash
git branch --show-current
git status --short
git log HEAD..origin/main --oneline
```

Checks:
- **Not on main:** refuse if the current branch is `main`.
  "You're on `main`. Create a feature branch first (`/git-branch`)."
- **Clean working tree:** warn if uncommitted changes exist.
  "You have uncommitted changes — they won't be in this PR unless you commit first."
- **Branch is pushed:** run `git ls-remote --heads origin <branch>`. If empty,
  tell the user: "Branch hasn't been pushed yet — push it first or I can do it now (SSH required)."

---

## § 2 — Gather PR metadata

### Title

If `$ARGUMENTS` contains a non-`draft` string: use it as the title candidate.
If empty: infer from the current branch name and recent commits:

```bash
git log --oneline $(git merge-base HEAD origin/main)..HEAD
```

Propose a title and ask the user to confirm or edit.

**Title rules:**
- Imperative mood, present tense (e.g., "Add user auth endpoint").
- ≤70 characters.
- No trailing period.
- No `[WIP]` prefix — use the draft flag instead.

### Draft flag

Set `--draft` if:
- `$ARGUMENTS` contains `draft`, or
- the user answers "yes" when asked "Is this a work-in-progress PR?"

### Summary

Ask the user: "What's the one-sentence summary of this change?"
If the branch name and commits make the purpose obvious, propose a summary
bullet and ask for confirmation.

### Test plan

Inspect changed files:
```bash
git diff --name-only $(git merge-base HEAD origin/main)..HEAD
```

Propose relevant test steps based on what changed (e.g., unit tests, manual
smoke test, migration check). Ask the user to add/remove steps.

### Secrets / auth / payments

Ask: "Does this PR touch any secrets, authentication, or payment flows?"
Record the answer verbatim.

---

## § 3 — Create the PR

Compose the body and run `gh pr create` via HEREDOC:

```bash
gh pr create \
  --title "<title>" \
  --base main \
  [--draft] \
  --body "$(cat <<'EOF'
## Summary
- <bullet 1>
- <bullet 2>

## Test plan
- [ ] <test step 1>
- [ ] <test step 2>

## Does this touch secrets, auth, or payments?
<yes/no — explanation if yes>
EOF
)"
```

Do NOT add:
- `🤖 Generated with Claude Code` footer
- `Co-Authored-By:` trailer
- Any AI attribution

---

## § 4 — Post-creation

Print the PR URL returned by `gh pr create`.

Then print:
```
Next steps:
  - Request reviewers: gh pr edit <number> --add-reviewer <github-handle>
  - Check CI:          gh pr checks <number>
  - Merge when approved: gh pr merge <number> --squash --delete-branch
```

---

## § 5 — Common scenarios

### Updating an existing PR

To add commits to an open PR: commit normally and push the branch.
The PR updates automatically — no `gh` command needed.

To change the PR title or body:
```bash
gh pr edit <number> --title "<new title>"
gh pr edit <number> --body "<new body>"
```

### Converting draft → ready for review

```bash
gh pr ready <number>
```

### Closing without merging

```bash
gh pr close <number>
```

---

## Hard Rules

- Always target `--base main`. Never target another feature branch as the base
  unless the user explicitly requests it and explains why.
- Never push `--force` inside this skill.
- Never fabricate test steps — ask if unclear.
- No AI attribution in the PR body.
