---
name: architect
description: Explore the codebase and surface deepening opportunities — refactors that turn shallow agents, skills, and hooks into deep, well-seamed modules. Use when the user wants to improve architecture, consolidate tightly-coupled modules, or make the codebase more testable and AI-navigable. May write ADRs to docs/adr/ and update ARCHITECTURE.md as side effects of the grilling loop; the architect agent (spawned for plan-review) is strictly read-only. Examples to invoke this skill if/when: improve architecture; review architecture; surface refactoring opportunities; the codebase feels messy; consolidate modules.
argument-hint: [path or topic to focus on]
allowed-tools: [Agent, Read, Glob, Grep, Write]
---

# Architect

Surface architectural friction and propose **deepening opportunities** — refactors that turn
shallow modules into deep ones. Informed by the domain context in `ARCHITECTURE.md` and
decisions recorded in `docs/adr/`.

See `LANGUAGE.md` for the shared vocabulary all suggestions must use exactly.
See `DEEPENING.md` for dependency categorization and testing strategy.

---

## Process

### 1. Explore

Read `ARCHITECTURE.md`, `CLAUDE.md`, and any files in `docs/adr/` first. These record
decisions you must NOT re-litigate — only surface a contradicting candidate when the friction
is real enough to warrant reopening the ADR. Mark it clearly ("contradicts ADR-XXXX — but
worth reopening because…").

Then use the Agent tool with `subagent_type=Explore` to walk the codebase. If `$ARGUMENTS`
names a path or topic, focus there. Otherwise, walk the full repo:

- `.claude/agents/` — agent definitions
- `.claude/skills/` — skill definitions
- `scripts/` — hook scripts and utilities (hooks are wired via `.claude/settings.json`)
- `tests/` — test harness

Explore organically. Note where you experience friction:

- Where are modules **shallow** — interface nearly as complex as the implementation?
- Where do agents or skills **leak concerns** across seams (doing more than one job)?
- Where is **locality** broken — a bug or change requiring edits in N separate places?
- What is currently hard to test through its existing interface?
- Apply the **deletion test** to anything suspect: would deleting it concentrate complexity
  (it earns its keep) or just move it (it's a pass-through)?

### 2. Present candidates

Present a numbered list of deepening opportunities. For each:

- **Files** — which agents/skills/hooks are involved
- **Problem** — the friction, described in `LANGUAGE.md` vocabulary (depth, seam, locality)
- **Solution** — plain English, what would change
- **Benefits** — leverage for callers, locality for maintainers, testability improvement
- **Dependency category** — see `DEEPENING.md` (pure, local-substitutable, owned external,
  true external)

**Use `ARCHITECTURE.md` vocabulary for domain concepts. Use `LANGUAGE.md` for structural
concepts.** If `ARCHITECTURE.md` names a concept, use that name — not a paraphrase.

Do NOT propose concrete interfaces yet. End with:
_"Which of these would you like to explore?"_

### 3. Grilling loop

When the user picks a candidate, walk the design tree interactively:

- What constraints must the deepened module satisfy?
- What dependencies does it take, and what category are they (see `DEEPENING.md`)?
- What sits behind the seam?
- What tests would survive a refactor to the deepened interface?

For exploring alternative interfaces, spawn 2–3 sub-agents in parallel with the Agent tool,
each given a different design constraint:

- Agent 1: "Minimize the interface — 1–3 entry points max. Maximize leverage per entry point."
- Agent 2: "Maximize flexibility — support many use cases and extension."
- Agent 3: "Optimize for the most common caller — make the default case trivial."

Compare designs by depth, locality, and seam placement. Give a recommendation.

### 4. Side effects during grilling

As decisions crystallize, make these side effects immediately:

- **New concept not in `ARCHITECTURE.md`?** Suggest adding it (offer to write it).
- **User rejects a candidate with a load-bearing reason?** Offer to record an ADR in
  `docs/adr/`. Create the directory if it doesn't exist. Only offer when the reason is
  structural and durable — skip "not worth it right now" and self-evident reasons. The ADR
  exists so future architect reviews don't re-suggest the same thing.
- **Decision contradicts `CLAUDE.md` rules?** Flag it; don't silently override.
