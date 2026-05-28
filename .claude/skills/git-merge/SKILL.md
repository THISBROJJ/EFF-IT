---
name: git-merge
description: Resolve merge and rebase conflicts step by step — reads conflicted files, explains ours vs. theirs, applies user-chosen resolutions, and continues the operation.
argument-hint: "[file to resolve | empty for all conflicted files]"
allowed-tools: [Bash, Read, Grep, Write]
---

# Git Merge — Conflict Resolution

Walks through merge or rebase conflicts one file at a time. Explains each
conflict in plain language, applies the user's chosen resolution, and advances
the merge or rebase to completion.

## Scope

Input: `$ARGUMENTS` — a specific file to resolve, or empty to resolve all
conflicted files in sequence.

Out of scope: deciding merge strategy, choosing which branch to merge, or
performing the merge itself (those are PR territory).

---

## § 1 — Detect operation type and conflict state

```bash
git status --short
```

Identify:
- Files marked `UU` (both modified), `AA` (added by both), `DD` (deleted by both) — these are conflicted.
- Whether a `rebase` or `merge` is in progress:
  ```bash
  test -d .git/rebase-merge && echo "rebase" || test -f .git/MERGE_HEAD && echo "merge" || echo "none"
  ```

If `none` and no conflicted files: "No conflicts detected." Stop.

Print:
```
Operation : rebase | merge
Conflicted: <count> files
Files     : <list>
```

---

## § 2 — Explain the conflict context (once)

Tell the user which side is which:
- In a **rebase**: "ours" = `origin/main` (what you're rebasing onto), "theirs" = your branch commits.
- In a **merge**: "ours" = the branch you're currently on, "theirs" = the branch being merged in.

---

## § 3 — Resolve each conflicted file

For each conflicted file (or the one in `$ARGUMENTS`):

### 3a — Read and display the conflict

Read the file and find each conflict block:
```
<<<<<<< HEAD (or ours label)
[ours content]
=======
[theirs content]
>>>>>>> <sha or branch> (or theirs label)
```

Print the conflict block with line numbers. Describe in plain language what
each side does — not just the raw code. Example:
> "Ours: sets the timeout to 30s. Theirs: sets the timeout to 60s."

### 3b — Ask for the user's decision

Offer clear choices:
```
Options:
  [1] Keep ours   — <brief description>
  [2] Keep theirs — <brief description>
  [3] Keep both   — I'll show you the merged version to approve
  [4] Custom      — paste what you want this section to look like
  [A] Abort the entire merge/rebase
```

Wait for the user's answer. Do not assume or default.

### 3c — Apply the resolution

Remove ALL conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`) and all lines
belonging to the rejected side. Leave only the chosen content.

If the user chose `[3] Keep both`: interleave the two sides in a logical order,
show the result, and ask for approval before writing.

If the user chose `[4] Custom`: display what they provided, confirm it replaces
the block, then write it.

Show the resolved section in a fenced code block before writing to disk.

### 3d — Stage the file

```bash
git add <file>
```

Print: "Resolved and staged: `<file>`."

Repeat § 3 for each remaining conflicted file.

---

## § 4 — Continue or finalize

After all conflicts are resolved and staged:

**Rebase:**
```bash
git rebase --continue
```
If more conflict rounds occur (multi-commit rebase), loop back to § 1.

**Merge:**
```bash
git commit
```
If no commit message was pre-set: draft one in the form
`chore: merge <source-branch> into <target-branch>` and show it for approval.

---

## § 5 — Abort protocol

If the user chooses `[A]` at any point:

```bash
git rebase --abort   # if rebase in progress
git merge --abort    # if merge in progress
```

Confirm with `git status --short`. Print:
"Operation aborted. Working tree is back to its pre-conflict state."

---

## § 6 — Verify clean state

```bash
git status --short
git log -3 --oneline
```

If `git status` shows no conflicts: "All conflicts resolved. Operation complete."

---

## Hard Rules

- Never auto-choose a side without asking — always present both sides and wait.
- Never delete conflict markers without writing the resolution to the file.
- Never continue (`git rebase --continue`) while any `<<<<<<<` markers remain.
- Never suggest force-resetting as a shortcut — always resolve or abort cleanly.
