---
marp: true
theme: default
paginate: true
---

# EFF-IT
### A Claude Code harness for vibe-driven software delivery

> "You know what? EFF-IT. Let the agents handle it."

<!--
SPEAKER NOTES — Slide 1 (Title, ~45 sec)

Open by saying the name out loud, then the tagline. Pause for the laugh.

Set expectations in two sentences:
"This is a presentation about a scaffold I built on top of Claude Code. It takes
the 'vibe coding' experience — describe what you want, let the AI build it —
and wraps it with the structure you'd normally have to remember to add
yourself: specs, audits, security review, checkpoints, the works."

Don't dive into architecture yet. The next slide explains why this exists at all.
Resist the urge to list features here — you have ten slides for that.
-->

---

## What is "vibe coding"?

- You describe **intent** in plain language
- The agent reads the repo, writes code, runs tests, opens the PR
- You stay in the driver's seat — but you're not typing every line

**The promise:** ship features at the speed of thought.
**The reality (without guardrails):** drift, half-done work, broken tests, leaked secrets.

<!--
SPEAKER NOTES — Slide 2 (Framing, ~60 sec)

Make sure the room agrees on what "vibe coding" means before you critique it.
The term is fresh enough that half the audience will have heard it and half
won't. Define it cleanly: you describe intent, the agent executes. That's it.

The pivot in this slide is the last line — "the reality without guardrails."
Land that beat hard. This is the problem statement for the whole talk. If the
audience nods here, the rest of the deck writes itself.

Concrete examples to drop if energy is low:
  - "I've watched Claude edit a failing test to make it pass."
  - "I've watched it commit a .env file with a real API key."
  - "I've watched it forget what it was building three messages in."
Pick one. Don't list all three.

Transition: "So I built something to fix that."
-->

---

## The problem with raw vibe coding

| What happens | Why it's painful |
|---|---|
| Agent forgets context mid-feature | Start over, lose state |
| Tests get "adjusted" to pass | False green builds |
| Scope creeps silently | Reviewer surprise |
| Secrets land in commits | Rotate, redeploy, apologize |
| No record of *why* anything happened | Can't debug the agent itself |

Raw Claude Code is a **power tool**. EFF-IT is the **jig** that makes it safe.

<!--
SPEAKER NOTES — Slide 3 (Problem deep-dive, ~75 sec)

Walk the table top-to-bottom. One sentence per row, no more:

  1. "Sessions die. Without a checkpoint, you start from scratch."
  2. "Agents are great at making tests pass — including by editing the test."
  3. "Ask for a bug fix, get a 40-file refactor."
  4. "Secrets in commits aren't theoretical. It's happened to me twice."
  5. "When the agent does something weird, you want a transcript. Raw Claude Code doesn't keep one by default."

Land the closing line — the power-tool / jig metaphor — slowly. This is the
mental model for the whole rest of the deck. The harness is not a replacement
for Claude Code; it's the fixture that holds the work piece steady while the
tool does its job.

If anyone asks "why not just be more careful?" — that's the *exact* question
the next slide answers.
-->

---

## What EFF-IT is

A **drop-in scaffold** for any repo:

- `.claude/commands/` — slash-command workflows (`/run`, `/fast-lane`, `/resume`)
- `.claude/agents/` — 12 single-purpose subagents
- `.claude/hooks/` — lifecycle scripts (logging, secrets scan, test immutability)
- `sessions/<run_id>/` — self-contained per-run artifacts + checkpoint
- `security/profiles/` — app-type threat models loaded per run

**Stack:** Bash + Markdown + GitHub Actions. **No runtime.** It targets whatever
stack your project already uses.

<!--
SPEAKER NOTES — Slide 4 (What it is, ~60 sec)

Now you can finally show the goods. Five bullets, each pointing at a directory
in the repo. Don't read every bullet — point at the slide and call out the
three that matter most:

  - "Commands are how *you* talk to it — slash commands you type."
  - "Agents are how *it* talks to itself — each one does one thing."
  - "Hooks are the safety rails that fire whether the agent remembers to or not."

The last paragraph is important: this isn't a framework that owns your stack.
It's pure Bash and Markdown. It doesn't care if your project is Python, Go,
Rust, or TypeScript. That portability is the reason it's worth adopting.

If someone asks "is this open source / can I copy it?" — yes, that's exactly
the point. The README has the copy-paste steps. (Slide 11 covers adoption.)
-->

---

## Three entry points for three vibes

| Command | When to use it |
|---|---|
| `/run [idea]` | New feature, vague brief — full pipeline, idea → PR |
| `/fast-lane [desc]` | You know exactly what to build — skip the spec phase |
| `/resume <run_id>` | Session crashed — pick up at the last checkpoint |

Every entry point lands in the same pipeline. `/resume` exists because long
runs *will* get interrupted, and starting over is the worst feeling in vibe
coding.

<!--
SPEAKER NOTES — Slide 5 (Entry points, ~50 sec)

Three commands, three moods. Walk the row:

  - "/run is the front door. Pitch me an idea — even a bad one — and it'll
     interrogate it into a spec before writing a line of code."
  - "/fast-lane is for when you don't want the Socratic dialogue. You've
     thought about it, you know what you want, just go."
  - "/resume is the unsung hero. Long agent runs die. Network blips, context
     fills up, you close the laptop. /resume reads checkpoint.json and drops
     you back in at the exact stage where things stopped."

The last paragraph is the emotional beat — anyone who's done serious agent
work has lost a run at minute 45 and felt that specific kind of despair.

Transition: "What actually happens inside /run? Next slide."
-->

---

## The pipeline (the whole show)

```
/run
  ├─ idea-interrogator    → Socratic Q&A until spec is concrete
  ├─ spec-drafter         → SPEC.md
  ├─ git-expert           → feat/<slug> branch
  ├─ orchestrator         → PLAN.md (task decomposition)
  ├─ concern-resolver     → SECURITY_CONCERNS.md
  ├─ architect            → ARCHITECTURE.md
  ├─ implementation-loop  → unit-test-writer → coder → test-runner ↻ (≤5x)
  ├─ karen                → PASS / PARTIAL / FAIL audit vs SPEC
  ├─ evaluate-run         → per-agent quality scores
  ├─ security-reviewer    → remediation list
  └─ git-expert           → commit → push → PR
```

<!--
SPEAKER NOTES — Slide 6 (Pipeline, ~90 sec — biggest beat in the deck)

This is the slide everything else hangs off. Don't rush.

Walk it once at a high level:
"Idea on the left, PR on the right. Everything in between is automated, but
every stage produces a named artifact you can read and audit."

Then walk it again calling out the four moments that matter:

  1. interrogator → spec-drafter: "This is where vague becomes specific.
     You can't build the wrong thing if you couldn't articulate it."
  2. orchestrator → architect: "Plan before code. The agent decomposes the
     work and proposes architecture *before* touching files."
  3. implementation-loop: "Five iterations max. Tests drive the loop. If
     they don't pass, the loop runs again with the failure as context."
  4. karen + security-reviewer: "Two independent audits at the end. karen
     checks 'did we build what was asked.' security checks 'did we ship
     anything dangerous.' Either can block the PR."

Inevitable question: "Who's Karen?" — yes, she's named for the meme. She
audits ruthlessly and returns PASS, PARTIAL, or FAIL. The joke writes itself.

Optional aside if you have time: every arrow in this diagram corresponds to
a markdown file in .claude/agents/. The whole pipeline is data — no
hardcoded orchestration logic. That's why it's portable.
-->

---

## 12 agents, one job each

| Agent | Role |
|---|---|
| `orchestrator` | Decompose spec into tasks |
| `coder` | Implement one task |
| `karen` | Audit work against spec |
| `architect` | Draft / update architecture docs |
| `spec-drafter` | Turn interrogation into SPEC.md |
| `concern-resolver` | Surface security concerns from triggers |
| `security-reviewer` | Final security pass on the diff |
| `git-expert` | Branch, commit, push, PR |
| `test-runner` | Run suite, report pass/fail/blocked |
| `unit-test-writer` | Generate tests to ≥90% coverage |
| `session-keeper` | Maintain PROGRESS_TRACKER.md |
| `agent-evaluator` | Score agents against criteria.json |

**Rule:** if an agent's description needs the word "and," split it.

<!--
SPEAKER NOTES — Slide 7 (Agent roster, ~60 sec)

Don't read the table. Let the audience scan it.

What to say while they scan:
"Twelve agents. Every one of them is under 200 lines of prompt. Every one
has a single responsibility. If you've ever written a CLAUDE.md that's
two thousand lines long trying to teach one giant agent every skill — this
is the alternative. Small, composable, replaceable."

Then land the rule at the bottom hard:
"If you can't describe what an agent does without using the word 'and,'
you have two agents pretending to be one. Split them."

Call out karen and agent-evaluator specifically as the meta-agents — they
review the work of other agents. That's how the system catches itself
when individual agents go off the rails.

If asked which agent was hardest to write: orchestrator. Task decomposition
is the place where vagueness becomes expensive.
-->

---

## Always-on safety rails (hooks)

| Hook | Fires on | What it guarantees |
|---|---|---|
| `log_tool_call.sh` | Every tool call | JSONL audit trail of every action |
| `secrets-postwrite.sh` | Write / Edit | Scans for leaked credentials |
| `test-immutability.sh` | Edit / Write | **Blocks** edits to existing tests |
| `git-commit-scope.sh` | `git commit` | Injects `git diff --stat` first |
| `session-autocommit.sh` | Tracker writes | Auto-commits progress (team mode) |

These fire **whether the agent remembers them or not.** That's the whole point.

<!--
SPEAKER NOTES — Slide 8 (Hooks, ~75 sec)

This is the slide where security and SRE people lean in. Sell it hard.

For each hook, one sentence:

  - log_tool_call.sh: "Every Bash command, every file edit, every web
    fetch — appended as JSONL. When the agent does something weird, you
    have a transcript."
  - secrets-postwrite.sh: "The moment a file is written, it's scanned.
    If a credential lands, you know before you push."
  - test-immutability.sh: "This is the one I'm proudest of. Agents are
    *very* good at making failing tests pass by editing the test. This
    hook blocks the edit at the tool-call level. New tests are fine.
    Existing tests are immutable."
  - git-commit-scope.sh: "Diff before commit. Every time. The agent sees
    what it's about to commit and can bail if the scope is wrong."
  - session-autocommit.sh: "Optional team mode — the agent's progress
    tracker auto-commits, so reviewers can watch the run live."

The closer is the key sentence: "These fire whether the agent remembers
them or not." Hooks live in .claude/settings.json — they're harness-level
guarantees, not agent-level intentions. The agent literally cannot bypass
them; the runtime executes them.
-->

---

## Quality gates that block bad PRs

**`karen`** — audits the final diff against `SPEC.md`
PASS → continue. PARTIAL / FAIL → punch list to `PROBLEMS.md`, loop again.

**`security-reviewer`** — merges app-type threat models with code findings
Loads checklists from `security/profiles/` based on declared `app_types`
(`web_app`, `api`, `rag`, `ai_agent`, `database`, `frontend`, …).

**`evaluate-run`** — scores each agent against its `criteria.json`
Writes per-agent verdicts to `sessions/<run_id>/traces/<agent>.json`.

No PR opens until all three are satisfied.

<!--
SPEAKER NOTES — Slide 9 (Quality gates, ~60 sec)

This is the "trust" slide. You're answering the question: "How do I know
the agent didn't ship garbage?"

Three gates, three answers:

  - karen: "Did we build what the spec asked for? Not 'does it run' —
    'does it match.' She compares the diff to SPEC.md and returns a
    verdict. If she says PARTIAL or FAIL, the implementation loop runs
    again with her punch list as context."
  - security-reviewer: "Did we ship anything dangerous? She's loaded with
    threat models specific to the app type. If you declared this is a
    web_app and an api, she'll check for OWASP top 10 plus API-specific
    risks. The checklists merge — no manual selection."
  - evaluate-run: "Did each agent actually do its job well? This is the
    meta-gate — agent-evaluator scores every agent's output against its
    own criteria. It's how the harness detects when an individual agent
    is regressing."

Close with the line on the slide. No PR opens until all three are happy.
That's the contract.
-->

---

## Anatomy of a session

```
sessions/20260515-1430/
├── checkpoint.json        ← current pipeline stage + metadata
├── SPEC.md                ← what we're building
├── PLAN.md                ← how, broken into tasks
├── ARCHITECTURE.md        ← proposed design
├── SECURITY_CONCERNS.md   ← triggered concerns + checklists
├── PROGRESS_TRACKER.md    ← per-agent I/O log (auto-committed)
├── PROBLEMS.md            ← karen + security findings
├── traces/<agent>.json    ← per-agent evaluation verdicts
└── session_log.json       ← structured tool-call log
```

Cleanup = `rm -rf sessions/<id>`. Debugging = `ls sessions/<id>`. Resume = `/resume <id>`.

<!--
SPEAKER NOTES — Slide 10 (Session anatomy, ~50 sec)

This slide answers: "Where does all this stuff live?"

The point to land: everything for one run is in one folder. Not scattered
across docs/, reports/, .claude/state/, and the git log. One folder.

That single-root design is *why* cleanup, debugging, and resume are all
trivial one-liners. The bottom line of the slide is the payoff.

If you have time, point at PROGRESS_TRACKER.md specifically: in team mode
that file auto-commits on every write, so a reviewer can pull the branch
and watch the agent's progress as if they were pair programming.

Optional: mention the two session modes (local-only vs collaborative)
briefly. Local-only adds three lines to .git/info/exclude. Collaborative
leaves them out and lets the auto-commit hook do its thing.

Transition: "OK — how do you actually use this on your own repo?"
-->

---

## Adopting it

1. Copy `.claude/`, `sessions/`, `tests/`, `scripts/`, `.github/`, `.gitignore` into your repo
2. Fill in `CLAUDE.md` — project name, stack, test command
3. (Optional) Declare `app_types` in `CLAUDE.md` to load threat models
4. (Optional) Add `sessions/*/` to `.git/info/exclude` for local-only mode
5. `/run` and describe what you want to build

**That's it.** No runtime to install. No service to deploy. Pure scaffold.

<!--
SPEAKER NOTES — Slide 11 (Adoption, ~45 sec)

Make this feel small. The barrier to adoption is the message.

"Five steps. Two of them are optional. The other three are 'copy files,'
'fill in a markdown file,' and 'run a command.' If you've used Claude
Code at all, you can adopt this in fifteen minutes."

Specifically call out the no-runtime line. People hear "harness" and
brace for a Docker image, a server, a config file with seventeen YAML
keys. None of that. It's markdown and bash.

If anyone asks about CI: the .github/ folder ships with workflows for
the standard hooks (secrets scan, test immutability) running on PRs too,
so the guarantees extend beyond the local agent loop. Mention this only
if asked — it's not the main beat.
-->

---

## Plain Claude Code vs EFF-IT

| Concern | Plain Claude Code | EFF-IT |
|---|---|---|
| One agent or many? | One, doing everything | 12 single-purpose |
| Session crashes? | Start over | `/resume` from checkpoint |
| Did we build the right thing? | You check | `karen` checks |
| Security? | Your job | Profile-driven, every run |
| Tests "adjusted" to pass? | Possible | Blocked at hook level |
| Audit trail? | Transcript only | JSONL log + per-agent traces |
| Scope drift? | Possible | Diff-before-commit hook |
| Portable across repos? | Per-repo CLAUDE.md | Drop-in scaffold |

<!--
SPEAKER NOTES — Slide 12 (Comparison, ~75 sec)

This is the closer before the demo. Don't walk every row — let people read.

What to say while they read:
"Plain Claude Code is incredibly capable. Nothing on this slide is a knock
against it. The point is that everything in the right column is *work* —
work you'd have to do yourself, every project, every session, with raw
Claude Code. EFF-IT just bundles that work into a scaffold so you don't
have to redo it."

If pressed on which row matters most, pick two:
  - "Tests adjusted to pass" — because it's invisible until production.
  - "Session crashes" — because it's the single biggest productivity
     killer in long agent runs.

Transition to demo:
"Let me show you what it looks like in practice."
-->

---

## Live demo

Pick one:
- `/run "add a JWT refresh endpoint to the auth service"`
- `/fast-lane "rename UserService.findById to UserService.getById everywhere"`
- `/resume 20260520-1145`  *(if a paused run exists)*

What to watch for:
- The Q&A loop in `idea-interrogator` (it really does push back)
- `karen` returning PARTIAL the first iteration (it usually does)
- Hooks firing in the transcript margin

<!--
SPEAKER NOTES — Slide 13 (Demo, ~3–5 min depending on pipeline speed)

Pre-flight checklist before going live:
  1. Repo is on a clean branch (the harness is going to create a new one).
  2. CLAUDE.md has app_types declared, or be ready to explain why concerns
     are keyword-only.
  3. Have a fixture session ready under sessions/ in case the live run
     stalls — you can pivot to /resume on the fixture.
  4. Terminal font is large enough to read from the back of the room.

Demo choice guidance:
  - /run is the most impressive but also the longest. Pick this if you
    have 8+ minutes and a reliable network.
  - /fast-lane is the safer choice for a short slot. Skip the
    interrogation, land directly in the implementation loop.
  - /resume is the rescue option — use this if live runs are flaky or
    if your slot is under 5 minutes.

Narrate as the agent works:
  - When interrogator asks a question: "Notice it's pushing back — it
    won't draft a spec until the ambiguity is resolved."
  - When the coder starts editing: "Watch the secrets hook fire on every
    write — there's the JSONL line appearing in the log."
  - When karen returns: "There's the audit. If she says PARTIAL, we loop."

Have a fallback: if the demo dies mid-flight, switch to showing
sessions/<a-completed-run>/ in the file tree. The artifacts tell the
story even without the live run.
-->

---

## Q&A

**Likely questions, pre-baked answers:**

- *"Why not just use one big agent with a great prompt?"*
  Single agents drift on long tasks. Decomposition + audit catches drift early.

- *"What if I disagree with karen?"*
  Override and continue — karen's verdict is advisory at the harness level,
  blocking at the loop level. You're still the human.

- *"Does this lock me into Claude?"*
  The hooks and pipeline are model-agnostic. Agents are markdown — port them
  to any agent runtime that reads frontmatter.

- *"What's the failure mode I should worry about?"*
  Stale agents. If an agent hasn't been invoked in 30+ days, it's a candidate
  for removal — sprawl has a real cost.

<!--
SPEAKER NOTES — Slide 14 (Q&A, open-ended)

Read the room. If hands go up immediately, you've nailed the talk. If
silence, prime the pump with one of the pre-baked questions from the slide:
"A question I get a lot is..."

Hard questions you might get, and how to handle them:

  - "Have you measured productivity gains?" — Be honest. "No formal A/B,
    but the runs I would have abandoned without /resume are the strongest
    signal. Anecdotally, idea-to-PR for a small feature is under an hour."

  - "What about cost? 12 agents per feature must burn tokens." — Yes. The
    tradeoff is fewer failed runs and fewer round trips with humans for
    spec clarification. Net cost vs raw Claude Code is roughly comparable
    for non-trivial features; worse for trivial ones (use /fast-lane).

  - "Could the agent disable a hook?" — In principle, by editing
    .claude/settings.json. In practice, secrets-postwrite would scan the
    edit, and the agent has no instruction to do this. But: don't run
    this scaffold against a repo with sensitive secrets you haven't
    rotated. Defense in depth, not magic.

  - "Is this open source?" — [Insert your answer here based on the repo's
    actual license status.]

  - "How do I contribute?" — [Insert your answer here.]

Close with a callback to the title. "EFF-IT. Let the agents handle it.
Thanks for listening — happy to keep talking after."
-->
