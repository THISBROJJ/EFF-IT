# open_endpoint

## Metadata
- **Severity:** high

## Trigger Keywords
- endpoint
- route
- API
- handler
- controller
- public API
- unauthenticated

## Architect Checklist
- [ ] Document which endpoints require authentication and which are intentionally public; make this explicit in the route definition or a companion auth-requirements table
- [ ] Design a rate-limiting strategy (per-IP, per-user, or per-key) and specify limits before implementation begins
- [ ] Define the error response contract — specify what information is safe to surface (status codes, opaque IDs) and what must be suppressed (stack traces, internal paths, database errors)
- [ ] Identify any endpoints that cross trust boundaries (public internet vs. internal network) and plan network-layer controls accordingly

## Review Checklist
- [ ] Verify that auth middleware is applied to every non-public route and that no route accidentally bypasses the middleware chain
- [ ] Confirm no route is reachable without passing the auth layer (check wildcard routes, prefix mismatches, and framework-specific bypass patterns)
- [ ] Verify error responses do not leak internal details — stack traces, file paths, query strings, or service names must not appear in production error bodies
- [ ] Check that rate-limit headers and enforcement are present on all public-facing endpoints
