# Web App Security Profile

## Threat Model
Web applications face the OWASP Top 10 in full: Cross-Site Scripting (XSS) where attacker-controlled input is rendered as executable HTML/JS, Cross-Site Request Forgery (CSRF) tricking authenticated users into unintended state-changing requests, SQL injection via unparameterized database queries, Insecure Direct Object Reference (IDOR) where authorization is checked at the route level but not the object level, broken authentication (weak session management, missing MFA), and security misconfiguration (verbose error pages, default credentials, missing security headers).

## Architect Checklist
- [ ] CSRF tokens required on all state-changing forms (POST, PUT, PATCH, DELETE); SameSite cookie attribute set to Strict or Lax as a defense-in-depth layer
- [ ] Content Security Policy (CSP) header defined and enforced; default-src restricted, unsafe-inline and unsafe-eval prohibited unless explicitly justified
- [ ] Output encoding strategy documented per context (HTML, JS, CSS, URL); use framework-provided encoding rather than manual escaping
- [ ] Auth middleware applied to all protected routes by default (deny by default, explicit allow for public routes)
- [ ] Session tokens use cryptographically secure generation, have appropriate expiry, and are invalidated on logout

## Review Checklist
- [ ] CSP header present in responses and covers all relevant directives; validate with CSP evaluator
- [ ] CSRF protection confirmed on all POST/PUT/DELETE endpoints; verify token validation is server-side
- [ ] No reflected XSS vectors — user-controlled values not rendered unescaped in HTML responses
- [ ] IDOR checked: authorization validates the requesting user owns or has permission for the specific object, not just that they are authenticated
- [ ] Error responses return generic messages; stack traces and DB schema details not exposed to clients
