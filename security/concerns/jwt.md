# jwt

## Metadata
- **Severity:** high

## Trigger Keywords
- JWT
- token
- bearer
- JSON Web Token
- claims
- refresh token

## Architect Checklist
- [ ] Select and document the signing algorithm (RS256 or ES256 preferred; HS256 only with a secret ≥256-bit random value); explicitly forbid `none` in the validation config
- [ ] Define token expiry strategy: access token TTL, refresh token TTL, and whether short-lived access tokens with refresh rotation are required
- [ ] Design a revocation approach (token blocklist, short TTLs with forced re-auth, or opaque reference tokens) before any token issuance code is written
- [ ] Specify which claims are authoritative for authz decisions and require validation before use (e.g., `sub`, `scope`, `roles`, `exp`, `iss`, `aud`)

## Review Checklist
- [ ] Verify that the token validation library rejects `alg: none` and that the allowed algorithm list is an explicit allowlist, not a passthrough
- [ ] Confirm the `exp` claim is validated on every token decode path, including refresh flows
- [ ] Check that signing secrets and private keys are loaded from environment variables or a secrets manager — no hardcoded values in source or config files
- [ ] Ensure scope and role claims are validated against the required permission before the protected action executes, not just at login time
