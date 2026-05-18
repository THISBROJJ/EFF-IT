# Database Security Profile

## Threat Model
Databases are the primary target for data exfiltration. Attack surface includes SQL injection through unsanitized input, schema and error message exposure revealing table structure, privilege escalation via over-permissioned DB users, data at rest readable without encryption (especially PII), connection string secrets leaked in code or logs, unsafe migration scripts that cannot be rolled back, and backup files stored without access controls or encryption.

## Architect Checklist
- [ ] All queries use parameterized statements or prepared statements — no string concatenation of user input into SQL
- [ ] Database user accounts follow least-privilege: each service connects as a user scoped to only the tables and operations it needs
- [ ] PII and sensitive columns (SSN, payment data, health data) encrypted at rest using column-level or tablespace encryption
- [ ] Every migration includes a tested rollback script; forward-only migrations require explicit sign-off
- [ ] Backup storage encrypted and access-controlled; backup restoration tested in a non-production environment

## Review Checklist
- [ ] No raw SQL concatenation — grep for string interpolation into SQL queries
- [ ] Connection strings and credentials not hardcoded in source; loaded from environment or secrets manager
- [ ] DB user permissions verified to be scoped to minimum required (no superuser, no DDL rights for app user)
- [ ] Sensitive columns identified and confirmed encrypted; query results do not expose raw PII in logs or API responses
- [ ] Migration rollback scripts present and reviewed alongside forward migration
