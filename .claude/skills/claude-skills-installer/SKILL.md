---
name: claude-skills-installer
description: >
  Installs, uninstalls, and lists Claude skills from the catalog without
  needing a local copy of the repository. Works from any directory. Use
  this skill to install one or more skills globally or for a project,
  remove skills you no longer need, or browse what is available. Triggers
  on: "install [skill]", "get me [skill]", "install all skills",
  "uninstall [skill]", "remove [skill]", "what skills are available",
  "list skills", "search for [skill]".
argument-hint: "[install <skill> | install --all | uninstall <skill> | list [all] | search [all] <term>]"
allowed-tools: [Bash, Read]
---

# Claude Skills Installer

Installs and uninstalls Claude skills from the catalog using the bundled
`install.py` script in remote mode — no local clone of the catalog repo
required. Works from any working directory.

## Prerequisites

Before any workflow, verify the `gh` CLI is available and authenticated:

```bash
gh auth status
```

If `gh` is not installed, tell the user in plain language:
> "This skill requires the GitHub CLI (`gh`). Install it from
> https://cli.github.com/, then run `gh auth login` to authenticate."

If `gh` is installed but not authenticated, tell the user:
> "You need to authenticate with GitHub first. Run `gh auth login` in your
> terminal and follow the prompts, then try again."

Stop if either check fails.

## Finding the Scripts

The skill's scripts directory lives at one of:
```
$HOME/.claude/skills/claude-skills-installer/scripts/
$(pwd)/.claude/skills/claude-skills-installer/scripts/
```

Check the global path first; fall back to the local path. If neither
directory exists, tell the user to reinstall the skill.

Assign the directory to `SCRIPTS_DIR`, then set:
```bash
INSTALL_SCRIPT="$SCRIPTS_DIR/install.py"
```

## Self-Update

Before routing, silently update the installer itself so all subsequent
commands run the latest `install.py`:

```bash
python3 "$INSTALL_SCRIPT" claude-skills-installer >/dev/null 2>&1
```

If the command exits non-zero, warn the user in plain language:
> "Could not update the skill installer — proceeding with the installed
> version. Check your network connection or GitHub CLI authentication."

Then continue. Never block the user's request because of a failed self-update.

## Routing

Identify the user's intent:

- **install** — "install", "get me [skill]", "add [skill]", "install all",
  "reinstall", "uninstall and install", "uninstall and reinstall"
- **uninstall** — "uninstall" or "remove" with no install intent
- **list/search** — "list", "show", "what skills", "search", "available"

**Important:** "reinstall" and any combination of uninstall + install always
route to **install only** — never run uninstall first. The install script
overwrites existing files, and uninstalling `claude-skills-installer` itself
deletes the script needed to reinstall it.

If ambiguous, ask: "Are you trying to install a skill, remove one, or
browse what's available?"

## §1 — Install Workflow

### §1.1 — Parse the request

Extract:
- **Skill names** — one or more, comma- or "and"-separated; or `--all`
- **Scope** — `global` (default) or `local`:
  - `global` if message contains "globally", "for me", "user-level"
  - `local` if message contains "project", "local", "this repo", "working directory"
  - If ambiguous, ask: "Should I install globally (all projects) or just
    for this project?"

### §1.2 — Validate (named installs only, skip for --all)

If unsure whether the skill name is correct, show available options first:
```bash
python3 "$INSTALL_SCRIPT" --list
```

For each named skill: if not found in the output, show the list to the
user and stop. Draft skills are valid to install by direct name.

### §1.3 — Confirm and install

Say: "I'll install [skill-names or 'all Active/Beta skills'] [scope]. Proceed?"

Wait for confirmation. Then run:

```bash
# named, global (default)
python3 "$INSTALL_SCRIPT" <skill-name> [<skill-name> ...]

# named, local
python3 "$INSTALL_SCRIPT" --scope local <skill-name> [<skill-name> ...]

# all, global
python3 "$INSTALL_SCRIPT" --all

# all, local
python3 "$INSTALL_SCRIPT" --all --scope local
```

Report results in plain language. Never show raw script error output.

## §2 — Uninstall Workflow

### §2.1 — Parse the request

Extract the skill name and scope (global or local, same logic as §1.1).

### §2.2 — Confirm and uninstall

Say: "I'll remove [skill] from your [global/project] skills. This deletes
the local copy — the skill stays in the catalog. Proceed?"

Wait for confirmation. Then run:

```bash
# global
python3 "$INSTALL_SCRIPT" --uninstall <skill-name>

# local
python3 "$INSTALL_SCRIPT" --scope local --uninstall <skill-name>
```

Report result in plain language.

## §3 — List / Search Workflow

### §3.1 — List

No search term present. Run:

```bash
python3 "$INSTALL_SCRIPT" --list
```

Display the output as a table: name, status, description.

### §3.2 — Search

A search term is present. Run:

```bash
python3 "$INSTALL_SCRIPT" --search <term>
```

Display the matching results as a table: name, status, description.

---

End with: "To install a skill, say 'install [skill-name] globally' or
'install [skill-name] for this project'."

## Output Format

- Confirmations: plain sentences, no bullet lists
- Errors: plain language only — never show raw script output
- Shell commands shown to the user: fenced code blocks
