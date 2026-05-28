---
owner: DevSecOps
status: Draft
---

# claude-skills-catalog-manager

Natural-language interface for managing the Claude Skills Catalog. Lets anyone
install skills, contribute new ones, update skill status, and browse what's
available — without needing to know the repo structure or CLI flags.

## Overview

This skill is the front door to the catalog for non-technical contributors.
It wraps `install.sh`, the skill scaffolding templates, and git conventions
into a guided conversational workflow. It is scoped exclusively to this
repository and assumes it is invoked from within it.

## Use Cases

- "Install secrets-check for me globally"
- "Install pr-decomposition and secrets-check into my project"
- "I want to create a new skill for generating weekly reports"
- "Promote pr-decomposition to Active"
- "Mark secrets-check as Deprecated"
- "What skills are available?"
- "Do you have anything for PDF?"

## How to Use

```
/claude-skills-catalog-manager [intent]
```

The skill auto-detects intent from your message. You do not need to use a
specific command syntax — speak naturally.

**Install a skill globally:**
```
install pr-decomposition for me
```

**Install a skill into your current project:**
```
install secrets-check into my project
```

**Scaffold a new skill (guided interview):**
```
I want to create a new skill
```

**Promote a skill's status:**
```
promote pr-decomposition to Active
```

**Browse available skills:**
```
what skills are available?
```

## Output

- Install workflow: confirms scope, runs `install.sh`, reports result in plain language
- Contribute workflow: collects metadata interactively, scaffolds `SKILL.md`
  and `README.md` from templates, optionally creates a git branch and stages files
- Promote workflow: edits `README.md` status field, optionally handles git
- List workflow: table of all skills in `metadata.json` with name, status, description

## Additional Notes

- Must be run from inside the Claude Skills Catalog repository
- Draft skills can be installed by naming them explicitly; they are excluded
  from `--all` installs and the interactive picker
- CI automatically rebuilds `metadata.json` and the README skills table on
  merge — this skill does not run those scripts manually
- Git steps (branch, stage) are offered but never forced; the user can always
  handle git themselves
