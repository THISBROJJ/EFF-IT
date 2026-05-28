---
owner: DevSecOps
status: Draft
---

# claude-skills-installer

Install and uninstall Claude skills from any directory — no local clone of
the catalog repository required. Requires the `gh` CLI authenticated with
GitHub.

## Overview

This skill is the lightweight, globally-installable companion to
`claude-skills-catalog-manager`. Where the catalog manager is scoped to
contributors working inside the repo, this skill is for anyone who just
wants to add or remove skills from their Claude environment using natural
language. It runs `install.sh` in remote mode via the bundled
`scripts/install.sh`.

## Use Cases

- "Install pr-decomposition for me globally"
- "Install secrets-check into my project"
- "Install all skills"
- "Uninstall pr-decomposition"
- "Remove secrets-check from my project"
- "What skills are available?"
- "Search for PDF skills"

## How to Use

```
/claude-skills-installer [intent]
```

Speak naturally — the skill auto-detects whether you want to install,
uninstall, or browse.

**Install a skill globally:**
```
install pr-decomposition for me
```

**Install into the current project only:**
```
install secrets-check into my project
```

**Install all Active/Beta skills:**
```
install all skills globally
```

**Uninstall a skill:**
```
uninstall pr-decomposition
```

**Browse available skills:**
```
what skills are available?
```

## Output

- Install/uninstall: confirms scope, runs `install.sh` in remote mode,
  reports result in plain language
- List/search: table of Active/Beta skills from the catalog with name,
  status, and description

## Additional Notes

- Requires `gh` CLI installed and authenticated (`gh auth login`)
- Only Active and Beta skills appear in list/search; Draft skills can be
  installed by naming them explicitly
- `--scope global` installs to `~/.claude/skills/` (default)
- `--scope local` installs to `.claude/skills/` in the current directory
- This skill does not scaffold new skills or manage skill status — use
  `claude-skills-catalog-manager` for those workflows
