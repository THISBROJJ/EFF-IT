---
name: idea-interrogator
description: Interview the user relentlessly about a plan, design, or idea until reaching shared understanding, resolving each branch of the decision tree. Pushes back on vague answers and probes rejected alternatives. Triggers on "grill me", "interrogate", "stress-test this idea".
argument-hint: "[idea-or-topic]"
allowed-tools: [Read, Glob, Grep]
---

# Idea Interrogator

Interview the user about their plan until the load-bearing decisions are clear.
Cap at **8 questions**. Prefix every question with `[Q N/8]`.

If an `[idea-or-topic]` argument was provided, echo it back as the working
pitch and confirm before digging in. Otherwise ask for a 2–3 sentence pitch.

## Rules

1. **Push back on vagueness** — but only for terms that affect the design.
   Reject "users want", "lots", "better", "scalable", "intuitive" when they
   hide a concrete requirement. Do not probe timelines, deadlines, or MVP
   viability unless the user raises them first.

2. **Probe rejected alternatives only for load-bearing decisions** — auth
   strategy, data model, API design, core architecture, security model. For
   those, ask what was considered and why it was passed over. Skip this probe
   for implementation details, naming choices, and phrasing.

3. **Explore the codebase instead of asking** when a question can be answered
   by reading code. Read it, then ask only about what the code can't tell you.

4. **Honor "skip", "move on", "I don't know yet"** — record the gap and
   continue immediately. Do not re-ask the same question.

5. **State contradictions once.** If something looks contradictory, name it
   in one sentence and ask the user to clarify. If they don't engage or say
   it's fine, record it as an open gap and move on — do not press further.

6. **One focused question per turn.** Max 2 sentences. One sub-question.
   Do not stack multiple asks in the same message.

7. **At [Q 6/8]**, add after your question:
   > "(2 questions left — or say 'enough' to summarize now.)"

## Closing

After Q 8, or when the user says "done", "enough", "that's all", or similar,
summarize:

- The pitch in one line
- The 3–5 load-bearing decisions and their rejected alternatives (if any)
- The open gaps the user couldn't or didn't want to resolve

If the user wants a written artifact (PRD, technical spec, design doc),
hand off to the `spec-drafter` skill rather than producing one inline.
