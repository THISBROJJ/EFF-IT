# Feature Spec: User Login Endpoint

## Summary

Add a login route to the existing REST API that authenticates a user with email and password, validates request body params, and returns a signed JWT token on success.

## Background

The application currently has no authentication. This feature adds a `/auth/login` public API endpoint so that clients can obtain a bearer token for subsequent requests.

## Acceptance criteria

1. `POST /auth/login` handler accepts a JSON request body with `email` and `password` fields.
2. The controller validates user input — both fields are required and must not be empty.
3. On valid credentials the response includes a JWT (JSON Web Token) containing `sub`, `role`, and `exp` claims.
4. The token expires in 1 hour; a refresh token with a 7-day TTL is set in an HttpOnly cookie.
5. The endpoint returns HTTP 401 for invalid credentials and HTTP 422 for malformed params.
6. Access control: only unauthenticated requests may hit this route; authenticated users receive HTTP 400.

## Out of scope

- OAuth / social login
- Multi-factor authentication
- Role or permission changes at login time
