# auth_authz

## Metadata
- **Severity:** critical

## Trigger Keywords
- auth
- authentication
- authorization
- login
- permission
- role
- access control
- privilege
- session

## Architect Checklist
- [ ] Separate authentication (who you are) from authorization (what you may do) as distinct layers; design authz checks at the resource level, not only at the route or login boundary
- [ ] Apply the principle of least privilege: define the minimum permission set for each role and default new resources to private/restricted, requiring explicit grants to open access
- [ ] Design the full session lifecycle: creation, idle timeout, absolute timeout, and explicit invalidation on logout and password change; document the session store and token rotation strategy

## Review Checklist
- [ ] Verify that every protected resource performs an authorization check for the requesting identity, not just an authentication check — confirm ownership or role is validated before data is returned or mutated
- [ ] Check for IDOR vulnerabilities: ensure object IDs in requests (URL params, request body) are validated against the authenticated user's permitted scope, not accessed directly from the data store
- [ ] Confirm privilege escalation paths are blocked — verify that role elevation, admin actions, and cross-tenant data access each require explicit authz checks that cannot be bypassed by parameter manipulation
- [ ] Verify session tokens are fully invalidated server-side on logout and that previously issued tokens cannot be replayed after invalidation
