# Frontend Security Profile

## Threat Model
Frontend applications face XSS via DOM manipulation where attacker-controlled data is written to the DOM using unsafe sinks (innerHTML, document.write, eval), sensitive credential or token data stored in localStorage or sessionStorage where it is accessible to any JS on the page including XSS payloads, third-party script supply chain attacks where a compromised CDN or npm package injects malicious code, and clickjacking where the application is embedded in an attacker-controlled iframe to steal user interaction.

## Architect Checklist
- [ ] Content Security Policy defined with script-src, object-src, and base-uri restricted; unsafe-inline and unsafe-eval avoided
- [ ] Authentication tokens stored in httpOnly, Secure, SameSite cookies rather than localStorage or sessionStorage
- [ ] Subresource Integrity (SRI) hashes required for all scripts and stylesheets loaded from CDN or third-party origins
- [ ] Trusted Types or equivalent framework-level protection enabled to prevent DOM XSS via unsafe sinks
- [ ] X-Frame-Options or frame-ancestors CSP directive set to prevent clickjacking

## Review Checklist
- [ ] No eval(), Function(), or innerHTML assignments with user-controlled or externally sourced data
- [ ] Authentication tokens and session identifiers not stored in localStorage or sessionStorage; confirm storage mechanism uses httpOnly cookies
- [ ] X-Frame-Options header set to DENY or SAMEORIGIN, or frame-ancestors CSP directive configured
- [ ] Third-party scripts loaded from CDN include SRI integrity attribute with a pinned hash
- [ ] All dynamic DOM writes use safe APIs (textContent, createElement) or framework escaping; grep for innerHTML and dangerouslySetInnerHTML usages and verify each one
