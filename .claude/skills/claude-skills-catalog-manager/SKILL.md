---
name: claude-skills-catalog-manager
description: >
  Manages the Claude Skills Catalog for this repository. Use this skill to
  install one or more skills (globally or for a project), contribute and
  scaffold a new skill with guided setup, promote a skill status from Draft
  to Beta to Active or Deprecated, or list and search available skills.
  Triggers on: "install [skill]", "create a new skill", "help me contribute
  a skill", "promote [skill] to active", "mark [skill] as deprecated",
  "what skills are available", "list skills".
argument-hint: [install <skill> | contribute | promote <skill> to <status> | list]
allowed-tools: [Bash, Read, Write, Edit, Glob, Grep]
---

# Claude Skills Catalog Manager

Natural-language interface to the Claude Skills Catalog. Routes to one of
four workflows — install, contribute, promote, list — based on user intent.

## Routing

Identify the user's intent from their message:

- **install** — "install", "get me [skill]", "add [skill] to my [project/global]"
- **contribute** — "create", "contribute", "new skill", "scaffold", "add a skill"
- **promote** — "promote", "mark as", "update status", "move to active/beta/deprecated"
- **list** — "list", "show", "what skills", "search", "available"

If intent is ambiguous, ask: "Are you trying to install a skill, create a new
one, update a skill's status, or browse what's available?"

## Finding the Catalog Root

Run `git rev-parse --show-toplevel` from the current working directory.
Verify the result contains a `skills/` subdirectory — if so, that is the
catalog root. If not, tell the user: "I need to be run from inside the
Claude Skills Catalog repository. Please navigate there first."

## §1 — Install Workflow

### §1.1 — Parse the request

From the user's message extract:
- **Skill names** — one or more, comma- or "and"-separated
- **Scope**:
  - `global` if message contains "globally", "for me", or "user-level"
  - `local` if message contains "project", "local", "this repo", or "working directory"
  - If ambiguous, ask: "Should I install this globally (all projects) or just
    for this project?"

### §1.2 — Validate skill names

Read `<catalog-root>/metadata.json`. For each skill name:
- Found → proceed
- Not found → reply: "I couldn't find a skill called '[name]'. Here are the
  available skills:" then list names and statuses from metadata.json. Stop.

Draft skills are valid to install by direct name.

### §1.3 — Confirm and install

Say: "I'll install [skill-names] [scope]. Shall I proceed?"

Wait for confirmation. Then run:

```bash
# global (default)
bash <catalog-root>/scripts/install.sh <skill-name> [<skill-name> ...]

# local (installs into .claude/skills/ inside the current working directory)
bash <catalog-root>/scripts/install.sh <skill-name> [<skill-name> ...] --scope local
```

Report results in plain language. Never show raw script error output.

## §2 — Contribute Workflow

### §2.1 — Read conventions

Read `<catalog-root>/CONTRIBUTING.md` and `<catalog-root>/README.md` before
asking the user anything. Note naming rules (kebab-case, unique), branch
prefixes (`feature/`, `fix/`, etc.), and status definitions.

### §2.2 — Guided interview

Ask one question at a time, waiting for each answer:

1. "What should this skill be called? Use kebab-case (e.g. `pdf-extractor`)."
   - Validate: no spaces, no uppercase. Check `skills/` for name uniqueness.
   - If taken, say so and ask again.

2. "In one sentence, what does it do and when should Claude use it? (No colons
   or markdown — this becomes the trigger description.)"

3. "Which team or person owns this skill?"

4. "Does this skill accept arguments? If yes, describe them briefly. If no, say no."

5. "Which Claude tools does this skill need? (Read, Write, Edit, Bash, Glob,
   Grep, WebSearch, WebFetch — or say 'all' for no restriction.)"

6. Show summary and ask for confirmation:
   ```
   Name        : <name>
   Description : <description>
   Owner       : <owner>
   Status      : Draft
   Arg hint    : <value or none>
   Tools       : <list or unrestricted>
   ```
   "Shall I create the files?"

### §2.3 — Scaffold

1. Create `skills/<name>/SKILL.md` from `template/SKILL.md`, filling in
   the frontmatter fields collected above.
2. Create `skills/<name>/README.md` from `template/README.md`, setting
   `owner: <owner>` and `status: Draft`.

Do NOT run `update_metadata.py` or `update_readme.py` — CI handles this on merge.

### §2.4 — Git handoff

Ask: "Files are ready. Would you like me to handle the git workflow (create a
branch and stage the files), or will you do that yourself?"

If Claude handles it:
- `git checkout -b feature/<name>`
- `git add skills/<name>/`
- Report: "Branch `feature/<name>` created, files staged. Write the instructions
  in `skills/<name>/SKILL.md`, then commit and open a PR targeting `main`."

If user handles it:
- Report: "Files created at `skills/<name>/`. When ready: `git checkout -b
  feature/<name>`, commit, and open a PR targeting `main`."

## §3 — Promote Workflow

### §3.1 — Parse and validate

Extract the skill name and target status from the user's message.
Valid target statuses: `Active`, `Beta`, `Deprecated`.

Read `skills/<name>/README.md` to get the current status.
Valid transitions: `Draft → Beta`, `Beta → Active`, `any → Deprecated`.
If a step is skipped (e.g. `Draft → Active`), warn and ask to confirm override.

If the skill doesn't exist, say so and stop.

### §3.2 — Confirm and update

Say: "I'll update [skill] from [current] → [target]. Confirm?"

Wait for confirmation. Then edit `skills/<name>/README.md` — change
`status: <current>` to `status: <target>`.

Do NOT run `update_metadata.py` or `update_readme.py` — CI handles this on merge.

Ask: "Status updated. Would you like me to handle the git workflow (branch and
stage) or will you do that yourself?"

If Claude handles it:
- `git checkout -b fix/<name>-status`
- `git add skills/<name>/README.md`
- Report: "Branch `fix/<name>-status` created, file staged. Commit and open a
  PR targeting `main`."

If user handles it: report what was changed and where.

## §4 — List / Search Workflow

Read `<catalog-root>/metadata.json`. Format output as a table:

| Skill | Status | Description |
|-------|--------|-------------|

If the user included a search term, filter rows where name or description
contains the term (case-insensitive).

If no matches, say "No skills matched '[term]'."

End with: "To install a skill, say 'install [skill-name] globally' or
'install [skill-name] for this project'."

## Output Format

- Confirmations: plain sentences, no bullet lists
- Errors: plain language only — never show raw script output
- File paths: relative to the catalog root (e.g. `skills/pr-decomposition/SKILL.md`)
- Shell commands shown to the user: fenced code blocks
