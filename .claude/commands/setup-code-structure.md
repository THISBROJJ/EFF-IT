---
name: setup-code-structure
description: One-time project bootstrap — read the repo-root ARCHITECTURE.md (and PLAN.md task scopes) and scaffold the code directory structure it describes, dropping a short explainer README.md in each created folder. Idempotent. Run once after the design PR merges, before /fast-lane.
argument-hint: "(no arguments)"
allowed-tools: [Agent, Bash, Read, Write, Glob, Grep]
---

# Setup — One-Time Project Scaffold

Reads the durable repo-root `ARCHITECTURE.md` and creates the directory structure it
describes, dropping a one-paragraph explainer `README.md` in each folder it creates. Run this
**once**, after `/design`'s PR is merged (so `ARCHITECTURE.md` is on `main`) and before the
first `/fast-lane` build, to lay down the skeleton the plan's tasks will fill in.

This is a bootstrap, not a pipeline stage: it has no session, no checkpoint, and is not
resumable. It is **idempotent** — re-running it only fills in what is missing and never
overwrites an existing folder or `README.md`.

---

## Pre-flight

```bash
git status --short
git branch --show-current
```

Should be on `main` with a clean tree. If not, ask the user to commit/stash first.

Confirm the repo-root `ARCHITECTURE.md` exists. If it is **absent**, stop:
"No architecture found. Run `/design` first and merge its PR so `ARCHITECTURE.md` is on
`main`, then run `/setup-code-structure`."

---

## Step 1 — Derive the intended layout

`ARCHITECTURE.md` is prose, not a directory manifest — it may or may not spell out a folder
tree. Extract the intended layout, primary source first:

1. **`ARCHITECTURE.md`** (primary): read the components, data-flow, and layer descriptions.
   Note every directory path it names or clearly implies (e.g. "the API layer lives in
   `src/api/`", "handlers under `cmd/`").
2. **`PLAN.md`** (corroborating): if present, read each task's `scope` field. Scopes name
   concrete files and directories and are a more reliable signal than prose — use them to
   confirm and complete the set of directories inferred from `ARCHITECTURE.md`.

Build a deduplicated list of **directories to ensure**. For each, draft a one-paragraph
purpose line in plain language, derived from the component it maps to in `ARCHITECTURE.md`.

If you cannot extract a confident layout (architecture is too abstract, names no paths, and
`PLAN.md` scopes are vague), **do not invent a tree**. Tell the user what little you could
infer and ask them to confirm or supply the directory list before continuing.

---

## Step 2 — Confirm before writing (mandatory gate)

Present the proposed scaffold and wait for explicit approval. Show, for each directory:
- its path,
- whether it already **exists** (will be skipped) or is **new** (will be created),
- whether a `README.md` already exists there (left untouched) or will be added,
- the one-line purpose that will go into a new `README.md`.

Do not write anything until the user confirms. If they amend the list, re-display and
re-confirm.

---

## Step 3 — Scaffold (idempotent)

For each approved directory, in order:

- **Directory missing** → create it (`mkdir -p <dir>`), then write `<dir>/README.md`.
- **Directory exists, `README.md` missing** → write only `<dir>/README.md`.
- **Directory exists, `README.md` present** → skip entirely (never overwrite).

Each created `README.md` is a short stub:

```markdown
# <dir>

<one-paragraph purpose, derived from ARCHITECTURE.md>

See [`ARCHITECTURE.md`](<relative path to repo-root ARCHITECTURE.md>) for how this fits the
overall design.
```

Skip-if-exists also protects harness-reserved directories (`.claude/`, `docs/`, `tests/`,
`scripts/`, `sessions/`, `security/`) if the architecture happens to name them.

---

## Step 4 — Report and hand off

Print a summary: directories **created**, `README.md` files **added**, and everything
**skipped** (and why — existed already).

The scaffold is left in the working tree. Suggest the user review it and commit — either
directly or by invoking the `git-expert` agent on a `chore/scaffold` branch to open a PR. Do
not commit automatically.

Then point the user to the next step: run `/fast-lane` to build the first task from `PLAN.md`.
