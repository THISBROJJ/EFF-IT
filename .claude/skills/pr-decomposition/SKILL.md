---
name: pr-decomposition
description: Decomposes a multi-part task or staged diff into atomic independently-mergeable pull requests with filled PR templates.
argument-hint: [task description | diff]
allowed-tools: [Bash, Glob, Grep, Read]
---

# PR Decomposition

Given a multi-part task description or the current staged/uncommitted diff, split the work into atomic, independently-mergeable pull requests. Each PR must touch exactly one concern. Output a numbered PR plan, pause for confirmation, then generate a filled template for each PR.

## Scope

Input: `$ARGUMENTS`

- If `$ARGUMENTS` is empty or the literal word `diff`: analyze the current working tree using `git diff HEAD` and `git status --short`.
- Otherwise: treat `$ARGUMENTS` as a plain-language task description and decompose it without reading the diff.

Out of scope: generating code, modifying files, or creating commits.

## Instructions

### §1 — Collect the changeset

If operating in diff mode (empty or `diff` argument):

```bash
git diff HEAD
git status --short
```

If both return no output, report: "No uncommitted changes found. Pass a task description as an argument instead." and stop.

If operating in task-description mode: skip §1 and proceed to §2 using `$ARGUMENTS` as the sole input.

### §2 — Identify concerns

A **concern** is exactly one of: new feature, bug fix, refactor, test addition, configuration change, documentation update, dependency change, CI/build change.

For each changed file (diff mode) or each named component (task-description mode), assign exactly one concern label. Apply these rules:

- A refactor and a feature are **never** the same concern.
- A bug fix and new functionality are **never** the same concern.
- Tests that cover only one feature belong to that feature's PR; tests that cover multiple features are their own concern.
- Changes to `.github/`, CI scripts, or build configuration are always a separate concern.
- Changes to multiple independent features in the same file are separate concerns.

List every file or task component with its assigned concern label before proceeding.

### §3 — Group into atomic PRs

Merge files/components that share the same concern into one PR. For each PR assign:

- A short imperative description (≤72 characters)
- The list of files it touches
- The tests it requires (happy path, edge cases, and a regression test if it is a bug fix)
- A base branch (usually `main`)
- Any dependency on another PR in this list

A PR is atomic if it can be merged and deployed independently without breaking the application. If a PR depends on another, note it explicitly as `Depends on PR N`.

### §4 — Output the PR plan

Print the plan in this exact format:

```
PR 1: <description>
  Files  : <comma-separated list>
  Tests  : <what must be tested>
  Base   : <base branch>

PR 2: <description>
  Files  : <comma-separated list>
  Tests  : <what must be tested>
  Base   : <base branch>
  Depends: PR 1
```

After the plan, print exactly: "Review the plan above. Confirm or redirect before I generate the PR templates."

Stop and wait for user confirmation before proceeding to §5.

### §5 — Generate PR templates

For each PR in the confirmed plan, output a filled template block:

```
---
## PR N — <description>

## What changed
<one or two sentences>

## Why it changed
<one or two sentences — the business or technical motivation>

## How to test it
- [ ] <step 1>
- [ ] <step 2>

## Does this touch any secrets, auth, or payments?
<yes / no — if yes, explain>
---
```

Do not fabricate test steps. If tests cannot be determined from the available information, write `TBD — describe the expected behavior and I will generate the test steps.`

## Output Format

- §4 plan: plain text, indented with two spaces, one blank line between PRs.
- §5 templates: one fenced Markdown block per PR, separated by a horizontal rule.
- If the entire changeset is already atomic (single concern), say so explicitly and output one template only.
- Never reproduce raw `git diff` output in the final report.
