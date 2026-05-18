# API Security Profile

## Threat Model
APIs are commonly targeted via broken object-level authorization (BOLA/IDOR) where an attacker substitutes another user's resource ID in a request, excessive data exposure where full database rows are returned when only a subset is needed, mass assignment where client-supplied fields are bound directly to model objects allowing unintended property overwrite, absence of rate limiting enabling credential stuffing or scraping, and improper error responses that leak stack traces, SQL error messages, or internal schema details to callers.

## Architect Checklist
- [ ] Response schema whitelisting enforced — API serializers explicitly list allowed fields; the full DB row or model object is never returned directly
- [ ] Rate limiting applied per endpoint and per caller identity (authenticated user or IP); limits tuned to legitimate usage patterns
- [ ] API versioning strategy defined so breaking security changes can be deployed without stranding clients
- [ ] Authentication required on every endpoint by default; endpoints intended to be public are explicitly annotated and reviewed
- [ ] Object-level authorization checked in every handler that accepts a resource identifier (not just route-level auth middleware)

## Review Checklist
- [ ] No mass assignment vulnerabilities — input binding uses an allowlist of writable fields, not a blocklist or direct model bind
- [ ] Error responses return a generic message and a correlation ID; no stack traces, SQL errors, or internal field names in client-visible errors
- [ ] Rate limiting confirmed present and tested for all endpoints, including auth endpoints (login, token refresh, password reset)
- [ ] All endpoints authenticated unless explicitly documented as public; public endpoints reviewed for information disclosure
- [ ] BOLA/IDOR check: every handler that uses a resource ID from the request verifies the caller is authorized for that specific resource
