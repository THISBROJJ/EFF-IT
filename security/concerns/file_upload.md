# file_upload

## Metadata
- **Severity:** high

## Trigger Keywords
- upload
- file upload
- multipart
- attachment
- blob
- storage
- S3
- file type

## Architect Checklist
- [ ] Define the allowed file type allowlist (MIME types and extensions), maximum file size, and maximum number of concurrent uploads per user before implementation begins
- [ ] Plan storage path isolation: uploaded files must be stored outside the web root (or in a private bucket with no public ACL) with server-generated keys, never caller-supplied filenames
- [ ] Evaluate whether virus/malware scanning is required given the file types accepted and the sensitivity of downstream consumers; document the decision and any compensating controls if scanning is deferred

## Review Checklist
- [ ] Confirm MIME type is validated server-side using magic bytes or a server-side library, not solely from the `Content-Type` header or file extension supplied by the client
- [ ] Verify file extension is checked against the allowlist after sanitizing the filename (strip path components, null bytes, and unicode tricks before the check)
- [ ] Confirm uploaded files are stored at a server-generated path (e.g., UUID-keyed) outside the web root or in a private bucket — no caller-controlled path or filename reaches the storage layer
- [ ] Check that file size limits are enforced at the server/middleware level before the full payload is buffered, not only after the upload completes
