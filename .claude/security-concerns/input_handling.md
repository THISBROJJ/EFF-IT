# input_handling

## Metadata
- **Severity:** medium

## Trigger Keywords
- user input
- form
- query
- request body
- params
- search
- upload
- sanitize
- validate

## Architect Checklist
- [ ] Design a single input validation layer (schema validation at the boundary, before any business logic) using a typed schema library; document which fields are required, their types, and allowed value ranges
- [ ] Plan output encoding strategy for each rendering context (HTML, JSON, URL, shell) — identify where user-supplied data surfaces in responses
- [ ] Require parameterized queries or ORM-level abstractions for all database access; prohibit string concatenation for SQL, shell commands, or template rendering with user data
- [ ] Define file upload constraints (allowed MIME types, max size, filename sanitization) as part of the input contract, not as a bolt-on

## Review Checklist
- [ ] Verify no raw user-controlled input is interpolated into SQL queries, shell commands, `eval()` calls, or server-side templates without parameterization or strict escaping
- [ ] Confirm output is encoded for the correct context (HTML-escaped in HTML, JSON-serialized in JSON responses) before being written to any response
- [ ] Check that file upload handlers validate MIME type and extension server-side and enforce size limits at the framework or middleware level
- [ ] Ensure validation errors return generic messages without reflecting the raw invalid input back to the caller in a way that could be exploited for reflected injection
