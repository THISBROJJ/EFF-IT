---
name: git-commit
description: Stage changes and write a well-formed Conventional Commit message — no AI footers, specific file staging, ≤72-char subjects. Examples to invoke this skill if/when: a new feature or function was just implemented; a bug fix or refactor is complete; wrapping up a discrete chunk of work before switching context; "commit this"; "git commit".
argument-hint: "[files to stage | 'all' | empty for interactive]"
allowed-tools: [Bash, Glob, Grep, Read]
---

# Git Commit

Stages changes and produces a correctly-formed commit. Enforces Conventional
Commits format throughout.

## Scope

Input: `$ARGUMENTS` — a space-separated list of files to stage, the word `all`
(stage everything changed), or empty (interactive guidance).

Out of scope: pushing, branch creation, or PR creation.

---

## § 0 — Detect shell environment

Before running any commands, identify the active shell:

**bash / zsh / sh** — probe with:
```bash
echo $SHELL
```

**PowerShell** — if the above returns nothing or errors, probe with:
```powershell
$PSVersionTable.PSVersion
```

**cmd** — if neither works, assume cmd.

Record the result. Use it in § 4 to pick the correct commit syntax. If the
shell is cmd, warn the user that multi-line commit messages require bash or
PowerShell — offer to open one.

---

## § 1 — Inspect the working tree

Run in sequence:

```bash
git status --short
git diff --stat HEAD
```

Print the output verbatim. If both return empty: "Nothing to commit — working
tree is clean." and stop.

---

## § 2 — Determine what to stage

- If `$ARGUMENTS` contains explicit file paths: stage only those files.
- If `$ARGUMENTS` is `all`: stage everything (`git add -A`) **only if** every
  changed file clearly belongs to the same concern. If mixed concerns exist,
  print the file list and ask the user to pick.
- If `$ARGUMENTS` is empty: show the changed files and ask the user which to
  include. Do not proceed without a confirmed file list.

Stage using: `git add <file1> <file2> ...`

**Sensitive file guard** — before confirming the staged set, scan for files that
should never be committed. Reject staging and warn if any of the following appear:

- `.env`, `.env.*`, `*.env`
- Files named `credentials`, `secrets`, `token`, `key`, `password` (any extension)
- `*.pem`, `*.p12`, `*.pfx`, `*.key`, `id_rsa`, `id_ed25519`
- Any file the repo's `.gitignore` explicitly lists

If found: "Sensitive file detected: `<file>` — remove it from the staged set before
committing. If this is intentional, confirm explicitly."

Confirm staged content: `git diff --staged --stat`

---

## § 3 — Build the commit message

### Subject line (required)

Format: `type(scope): short description`

- **type** (required): one of `feat`, `fix`, `docs`, `chore`, `refactor`,
  `test`, `ci`, `perf`.
- **scope** (optional but preferred): the module, component, or area affected —
  e.g., `auth`, `dashboard`, `ci`, `api`.
- **description**: imperative mood, present tense, ≤72 chars total including
  type and scope. No trailing period. No sentence case (lowercase after colon).

Good: `feat(auth): add OAuth2 PKCE flow`
Good: `fix(dashboard): prevent null pointer on empty dataset`
Bad: `Updated auth` — missing type, past tense
Bad: `feat: Added new feature for the dashboard page to handle empty states` — too long

### Body (optional)

Add a blank line after the subject, then a paragraph explaining the WHY if
the subject alone isn't self-explanatory. Omit if the subject is clear.

Never explain WHAT the code does (the diff shows that). Only explain WHY.

### Trailers (forbidden)

Do NOT add:
- `Co-Authored-By: Claude ...`
- `🤖 Generated with ...`
- Any AI attribution footer

Confirm the message with the user before committing if the intent was ambiguous.

---

## § 4 — Commit

Use the syntax matching the shell detected in § 0:

**bash / zsh:**
```bash
git commit -m "$(cat <<'EOF'
type(scope): description

Optional body paragraph here.
EOF
)"
```

**PowerShell:**
```powershell
git commit -m @'
type(scope): description

Optional body paragraph here.
'@
```

**cmd** — not supported for multi-line messages. Switch to bash or PowerShell,
or use a single-line message if the body is not needed:
```cmd
git commit -m "type(scope): description"
```

---

## § 5 — Verify

```bash
git log -1 --format="%H %s"
```

Print the result. Confirm the full SHA and subject are correct.

---

## § 6 — Rejection criteria

Stop and report the problem (do not commit) if any of the following are true:

| Problem | What to say |
|---|---|
| No type prefix | "Subject must start with a type (feat/fix/docs/…)." |
| Subject >72 chars | "Subject is N chars — shorten to ≤72." |
| `git add -A` used with unrelated files | "These files are unrelated to the commit — stage specific files only." |
| Nothing staged after Step 2 | "Nothing staged. Aborting." |

---

## Output Format

- § 1 output: raw `git status` and `git diff --stat` — no reformatting.
- § 3 output: the proposed commit message in a fenced code block, clearly labeled.
- § 5 output: `git log -1 --format="%H %s"` result on a single line.
- If rejected: one sentence stating the problem and what to fix.
