# RAG Security Profile

## Threat Model
Retrieval-Augmented Generation systems introduce an indirect prompt injection surface: malicious content embedded in retrieved documents can manipulate the LLM's behavior without the user issuing the injection directly. Additional threats include PII persisted in vector embeddings (making it hard to delete), index poisoning where an attacker inserts adversarial documents to steer retrieval, query manipulation that extracts documents beyond the user's access scope, and retrieval context leakage where system-level or other users' documents surface in responses.

## Architect Checklist
- [ ] Establish a trust boundary between retrieved document content and the system prompt — retrieved text must be treated as untrusted user-tier input, not system-tier instructions
- [ ] PII scrubbed or redacted from documents before embedding; scrubbing pipeline reviewed before indexing new data sources
- [ ] Vector index access controls enforce per-user or per-role document visibility; embeddings namespaced or filtered by authorization scope
- [ ] Rate limiting and query logging on retrieval endpoints to detect enumeration or extraction attempts
- [ ] Index ingestion pipeline authenticated and audited — only authorized sources can write to the index

## Review Checklist
- [ ] Retrieved document text is wrapped or delimited so the LLM prompt architecture prevents it from overriding system instructions
- [ ] PII not persisted in vector store; confirm scrubbing pipeline runs before embed calls
- [ ] Similarity search results filtered by the requesting user's authorization scope before inclusion in prompt context
- [ ] Retrieval query and results logged for audit; anomalous query patterns (broad or repeated extraction) alertable
- [ ] Index write path requires authentication; unauthenticated or untrusted sources cannot poison the index
