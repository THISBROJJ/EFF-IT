# Problems — context-aware-security-concern-system

## Security review findings (LOW — optional)

**L1** — `log_tool_call.sh:19` — `.current_run` content used in file path without format validation. Mitigated by restricted write surface. Fix: add `^[0-9]{8}-[0-9]{4}$` guard.

**L2** — `scripts/secrets-scanner.sh:153-159` — EXCLUDE list covers `.claude/`, so `http://` URLs inside agent/hook/command files are not scanned by the new advisory pass. Fix: remove `.claude` from EXCLUDE for the http-only pass or add a dedicated pass.

**L3** — `security-reviewer.md:25` — `app_type` from SECURITY_CONCERNS.md used to construct profile path without allow-list validation. Mitigated by trusted concern-resolver provenance. Document the constraint.
