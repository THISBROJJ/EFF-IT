# transport_security

## Metadata
- **Severity:** high

## Trigger Keywords
- HTTP
- HTTPS
- TLS
- SSL
- connection
- external service
- webhook
- callback URL

## Architect Checklist
- [ ] Mandate HTTPS for all external calls and webhook/callback URLs in the design; document any internal-only HTTP exceptions with explicit justification and network-isolation controls
- [ ] Specify minimum TLS version (TLS 1.2 minimum, TLS 1.3 preferred) and define the cipher suite policy for any custom server or client configuration
- [ ] Identify all outbound connections to external services and plan certificate validation — document whether system trust store, pinning, or custom CA is appropriate for each integration

## Review Checklist
- [ ] Search the codebase for hardcoded `http://` URLs (excluding `localhost`, `127.0.0.1`, and `::1`) and confirm none are used for external calls
- [ ] Verify that TLS verification is not disabled — check for flags like `verify=False`, `InsecureSkipVerify: true`, `rejectUnauthorized: false`, or equivalent in every HTTP client
- [ ] Confirm TLS version is not downgraded below 1.2 in server config, reverse proxy config, and any custom TLS dial options
- [ ] Validate that webhook and callback URLs received from external parties are validated against an allowlist before being used to make outbound requests (SSRF prevention)
