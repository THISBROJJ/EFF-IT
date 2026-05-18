# prompt_injection

## Metadata
- **Severity:** critical

## Trigger Keywords
- prompt
- system prompt
- LLM
- language model
- AI
- chat
- message
- context injection
- user message

## Architect Checklist
- [ ] Define explicit trust boundaries: diagram which content comes from the system (trusted) vs. the user (untrusted) and document how each is handled before any prompt assembly code is written
- [ ] Require typed prompt templates (e.g., structured message arrays with `role` fields) rather than string concatenation; no user-supplied string should be interpolated directly into the system prompt slot
- [ ] Design output trust boundaries — specify which model outputs are treated as data (displayed, stored) vs. instructions (executed), and plan how to prevent the model from issuing system-level commands via its output
- [ ] Evaluate whether untrusted user content should be wrapped in a clearly delimited section with explicit instructions to the model to treat it as data, not instructions

## Review Checklist
- [ ] Verify that user-controlled strings are never concatenated directly into the system prompt; confirm they appear only in user-role message slots within a structured message array
- [ ] Confirm the system prompt cannot be overridden, appended to, or replaced by user input at runtime — check all code paths that assemble the final prompt
- [ ] Verify that model output is treated as untrusted data before being passed to downstream systems (shell, database, template engine, tool calls) — no raw LLM output executed without sanitization or schema validation
- [ ] Check that indirect injection vectors (file contents, web pages, tool results, database values) fed into the context are treated with the same level of distrust as direct user input
