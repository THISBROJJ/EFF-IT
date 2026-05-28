---
owner: DevSecOps
status: Draft
---

# completion-auditor

Audits a task that's just been claimed "done" against the user's original ask, catching shortcut fixes, silently-skipped requirements, and tests altered to pass instead of code fixed.

## Overview

AI agents (and tired humans) tend to optimize for the fastest path to a green
build, not for actually solving the problem the way the user described it.
Common failure modes: catching the symptom instead of the cause, weakening
the test until it passes, deleting the failing test, silencing a lint rule,
adding the requested feature but renaming six unrelated functions on the way
through, or quietly skipping half the requirements.

This skill is the QA-Karen pass that runs *after* the "done" claim. It
reconstructs the original ask verbatim, derives explicit acceptance
criteria, inspects the diff against each criterion, scans for anti-patterns,
and produces a PASS / PARTIAL / FAIL verdict with a punch list of what
still needs to happen.

It does not fix anything. It only audits.

## Use Cases

- A coding agent says "done" and you want a second pair of eyes before you
  hit merge
- A PR claims to fix issue #1234 — verify it actually does what the issue asked
- A handoff from one contributor to another, where the receiver wants
  evidence the work matches the ticket
- A retrospective sanity check on a feature that shipped but feels
  suspiciously cheap
- Catching test-tampering (assertions deleted, cases skipped, snapshots
  regenerated) introduced under deadline pressure

## How to Use

```
/completion-auditor [original-request | issue-link | path-to-spec]
```

Pass the original ask as the argument — a one-liner, a path to a spec file,
or a link to an issue. If you omit the argument, the skill will quote back
the earliest task description it can find in the conversation and ask you
to confirm or replace it.

**Example — paste the original request:**
```
/completion-auditor "Add a /healthz endpoint that returns 200 with the build SHA. Must work without auth."
```

**Example — point to a spec file:**
```
/completion-auditor docs/specs/healthz.md
```

**Example — let the skill pick up the ask from the transcript:**
```
/completion-auditor
```

The skill walks through 7 sections: capture the ask, derive criteria,
inventory the diff, map criteria to evidence, scan for shortcut anti-patterns,
deliver a verdict, and write a punch list. You confirm the criteria checklist
before the audit starts, so the skill audits against *your* definition of
done, not its own paraphrase.

## Output

1. The original ask, quoted verbatim, with a confirmation prompt
2. A numbered acceptance-criteria checklist that you sign off on before
   the audit runs
3. A change inventory: branch, base, commit count, files changed, test
   and config files touched
4. A per-criterion table marking each as **PASS**, **PARTIAL**, **FAIL**,
   or **GAP**, each with `file:line` evidence (or "not found in diff")
5. A findings list covering anti-patterns the criteria checklist won't
   catch: weakened tests, swallowed errors, disabled lint rules, lowered
   coverage thresholds, surface-only fixes, scope drift
6. An overall verdict (**PASS** / **PARTIAL** / **FAIL**) at the top of
   the report
7. A punch list of items required before the task can be re-claimed as done
8. An "out of scope but noticed" section for non-blocking observations

The full report is rendered in markdown and can optionally be written to
`docs/audits/<slug>.md`.

## Additional Notes

- Hostile-by-design: the "done" claim is treated as a hypothesis until
  evidence proves it. Do not invoke this skill expecting validation
- The skill **never edits code**. It only audits. If the punch list needs
  fixing, run a fix task afterwards, and use `pr-decomposition` if the
  fixes span multiple concerns
- Best paired with `unit-test-writer` (when the audit reveals weak or
  missing tests) and `pr-decomposition` (when the fix list is long)
- Requires a git repository for the diff inventory; falls back to
  uncommitted changes only if no merge-base is available
- Recommended on Opus — the criteria-to-evidence mapping and the
  anti-pattern scan benefit from deeper reasoning. Runs on Sonnet/Haiku
  but findings will be shallower
