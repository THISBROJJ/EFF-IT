# GitHub Webhook Signature Adapter - Test Plan

## Overview
This document describes the 38 unit tests written for `src/webhooksig/providers/github.py` to achieve ≥90% coverage.

All tests use stdlib `unittest` only (no pytest). Tests compute HMAC-SHA256 signatures inline using `hmac` + `hashlib` for self-contained verification.

## Test Categories and Coverage

### 1. Scheme Metadata Tests (6 tests)
Tests that verify GitHub adapter constants and specification are correctly defined.

- `test_scheme_version_constant` — SCHEME_VERSION = "github-sha256-v1"
- `test_github_spec_exists` — GITHUB_SPEC is defined
- `test_github_spec_algorithm_is_sha256` — Algorithm field is "sha256"
- `test_github_spec_header_name` — Header is "X-Hub-Signature-256"
- `test_github_spec_encoding_is_hex` — Encoding is "hex"
- `test_github_spec_timestamp_tolerance_300s` — Tolerance is 300 seconds

**Coverage:** Module constants, spec initialization

---

### 2. Happy Path Tests (6 tests)
Tests that verify valid signatures are correctly accepted.

- `test_verify_github_valid_signature_with_sha256_prefix` — Valid sig with sha256= prefix
- `test_verify_github_valid_signature_returns_correct_provider_name` — provider="github"
- `test_verify_github_valid_signature_with_timestamp` — Valid sig with past timestamp
- `test_verify_github_valid_signature_without_timestamp_parameter` — timestamp=None is OK
- `test_verify_github_returns_verification_result_type` — Returns VerificationResult
- `test_verify_github_result_timestamp_preserved` — Timestamp in result matches input

**Coverage:**
- Happy path: valid payload + valid secret + valid signature
- Return type: VerificationResult
- Timestamp handling: both provided and None cases
- Result fields: valid=True, provider="github", timestamp

---

### 3. Invalid Signature Tests (8 tests)
Tests that verify invalid signatures are correctly rejected.

- `test_verify_github_missing_sha256_prefix_raises` — No prefix → InvalidSignatureError
- `test_verify_github_wrong_prefix_raises` — Wrong prefix (sha1=) → InvalidSignatureError
- `test_verify_github_wrong_secret_raises` — Different secret → InvalidSignatureError
- `test_verify_github_tampered_payload_raises` — Modified payload → InvalidSignatureError
- `test_verify_github_one_bit_changed_in_signature_raises` — Single char change → InvalidSignatureError
- `test_verify_github_empty_signature_raises` — Empty string → InvalidSignatureError
- `test_verify_github_malformed_signature_raises` — Invalid hex → InvalidSignatureError
- `test_verify_github_truncated_signature_raises` — Too short hex → InvalidSignatureError

**Coverage:**
- Error paths: prefix validation, secret comparison, payload validation
- Constant-time comparison (timing-safe) — single bit changes detected
- Malformed input handling: empty, truncated, non-hex
- Exception: InvalidSignatureError raised correctly

---

### 4. Replay Protection Tests (5 tests)
Tests that verify timestamp-based replay protection.

- `test_verify_github_timestamp_within_tolerance` — 200s old is OK
- `test_verify_github_timestamp_at_tolerance_boundary` — Exactly 300s old is OK
- `test_verify_github_timestamp_outside_tolerance_raises` — 400s old → ExpiredTimestampError
- `test_verify_github_timestamp_slightly_outside_tolerance_raises` — 301s old → ExpiredTimestampError
- `test_verify_github_future_timestamp_raises` — Future timestamp → ExpiredTimestampError

**Coverage:**
- Timestamp validation: within window, at boundary, outside
- Replay protection: 300s default tolerance enforced
- Exception: ExpiredTimestampError raised correctly
- Edge case: future timestamps rejected

---

### 5. Edge Cases Tests (6 tests)
Tests for boundary conditions and unusual inputs.

- `test_verify_github_empty_payload` — Zero-byte payload
- `test_verify_github_large_payload` — 10KB payload
- `test_verify_github_unicode_secret` — Secret with UTF-8 and emoji
- `test_verify_github_binary_payload` — Non-UTF-8 binary data
- `test_verify_github_signature_with_mixed_case_hex` — Uppercase hex characters
- `test_verify_github_empty_secret` — Zero-length secret

**Coverage:**
- Boundary values: empty, very large
- Encoding: unicode secrets, binary payloads
- Hex parsing: case-insensitive (uppercase supported)
- Edge: empty secret is valid

---

### 6. Header Case Insensitivity Tests (1 test)
Tests for header name handling (if applicable).

- `test_verify_github_signature_header_is_x_hub_signature_256` — Constant verification

**Coverage:**
- Specification: confirms expected header name

---

### 7. Timing Attack Resistance Tests (1 test)
Tests that verify constant-time comparison is used.

- `test_verify_github_uses_timing_safe_comparison` — Both early and late char changes rejected

**Coverage:**
- Security invariant: `hmac.compare_digest` used
- Two signatures with different first chars both rejected
- Implicit verification that timing-safe comparison is in place

---

### 8. Real-World Payloads Tests (3 tests)
Tests with realistic GitHub webhook payloads.

- `test_verify_github_with_push_event_payload` — Push event JSON
- `test_verify_github_with_pull_request_event_payload` — PR event JSON
- `test_verify_github_with_issue_event_payload` — Issue event JSON

**Coverage:**
- Realistic integration: common GitHub event types
- Payload structures: multi-level JSON objects

---

### 9. Exception Hierarchy Tests (2 tests)
Tests that verify correct exception types are raised.

- `test_verify_github_invalid_signature_raises_correct_exception_type` — InvalidSignatureError
- `test_verify_github_expired_timestamp_raises_correct_exception_type` — ExpiredTimestampError

**Coverage:**
- Exception types: correct exception for each failure mode
- Exception inheritance and distinction

---

## Coverage Targets

This test suite targets ≥90% coverage on:
- **Line coverage:** All code paths exercised
- **Branch coverage:** All if/elif/else branches covered
- **Function coverage:** `verify_github()` fully tested

### Expected Coverage by Component

| Component | Coverage | Tested By |
|-----------|----------|-----------|
| Prefix parsing (sha256=) | 100% | Invalid Signature tests (2-3 tests) |
| Hex decoding | 100% | Invalid Signature tests (malformed hex) |
| HMAC-SHA256 computation | 100% | Happy Path + all signature tests |
| Timing-safe comparison | 100% | Timing Attack Resistance + Happy Path |
| Timestamp validation | 100% | Replay Protection tests (5 tests) |
| Exception raising | 100% | Invalid Signature + Replay Protection tests |
| Result construction | 100% | Happy Path tests |
| Edge case handling | 100% | Edge Cases tests (6 tests) |

---

## Test Execution

All tests use `unittest` and are compatible with both `unittest` discovery and `pytest`:

```bash
# Run all GitHub provider tests
python -m unittest tests.providers.test_github -v

# Or with pytest
python -m pytest tests/providers/test_github.py -v

# Coverage report
python -m pytest tests/providers/test_github.py --cov=src/webhooksig/providers/github --cov-report=term-missing
```

---

## Known-Good Test Vectors

All tests compute HMAC-SHA256 signatures dynamically using:
```python
signature_bytes = hmac.new(
    secret.encode("utf-8"),
    payload,
    hashlib.sha256,
).digest()
signature = "sha256=" + signature_bytes.hex()
```

This ensures tests are self-contained and don't rely on external hardcoded values. Each test verifies both the happy path and failure modes with computed signatures.

---

## Test Naming Convention

Following the naming conventions guide:
- Test file: `tests/providers/test_github.py` (mirrors `src/webhooksig/providers/github.py`)
- Test classes: `Test*` (e.g., `TestGitHubVerifyHappyPath`)
- Test methods: `test_*` (e.g., `test_verify_github_valid_signature_with_sha256_prefix`)

---

## TDD Red Phase

These tests are written in TDD red phase — they will fail until `src/webhooksig/providers/github.py` is implemented with:
- `SCHEME_VERSION` constant
- `GITHUB_SPEC: SignatureSpec` object
- `verify_github(payload, secret, signature_header, *, timestamp=None) -> VerificationResult` function

Expected implementation should:
1. Parse `sha256=` prefix from signature header (raise InvalidSignatureError if missing/wrong)
2. Decode hex signature (raise InvalidSignatureError if malformed)
3. Compute HMAC-SHA256(secret, payload)
4. Compare using `hmac.compare_digest()` (raise InvalidSignatureError if mismatch)
5. Validate timestamp is within 300s window (raise ExpiredTimestampError if outside)
6. Return `VerificationResult(valid=True, provider="github", timestamp=timestamp)`
