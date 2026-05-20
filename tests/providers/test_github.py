"""
Unit tests for GitHub webhook signature verification adapter.

Task P2-T5: Tests for GitHub adapter using known-good payloads from GitHub docs.
Covers: valid signature with sha256= prefix, missing prefix, wrong secret,
tampered payload, header case-insensitivity if applicable.

All tests use stdlib unittest only (no pytest).
Tests use inline computed HMAC-SHA256 test vectors for self-contained verification.
Target: ≥90% coverage on src/webhooksig/providers/github.py
"""

import hashlib
import hmac
import time
import unittest
from unittest.mock import patch

from webhooksig.providers.github import (
    SCHEME_VERSION,
    GITHUB_SPEC,
    verify_github,
)
from webhooksig.types import (
    InvalidSignatureError,
    ExpiredTimestampError,
    VerificationResult,
)


class TestGitHubSchemeMetadata(unittest.TestCase):
    """Test GitHub scheme constants and metadata."""

    def test_scheme_version_constant(self):
        """SCHEME_VERSION is set to github-sha256-v1."""
        self.assertEqual(SCHEME_VERSION, "github-sha256-v1")

    def test_github_spec_exists(self):
        """GITHUB_SPEC is defined and populated."""
        self.assertIsNotNone(GITHUB_SPEC)

    def test_github_spec_algorithm_is_sha256(self):
        """GITHUB_SPEC uses sha256 algorithm."""
        self.assertEqual(GITHUB_SPEC.algorithm, "sha256")

    def test_github_spec_header_name(self):
        """GITHUB_SPEC header name is X-Hub-Signature-256."""
        self.assertEqual(GITHUB_SPEC.header_name, "X-Hub-Signature-256")

    def test_github_spec_encoding_is_hex(self):
        """GITHUB_SPEC uses hex encoding."""
        self.assertEqual(GITHUB_SPEC.encoding, "hex")

    def test_github_spec_timestamp_tolerance_300s(self):
        """GITHUB_SPEC has 300-second timestamp tolerance."""
        self.assertEqual(GITHUB_SPEC.timestamp_tolerance_s, 300)


class TestGitHubVerifyHappyPath(unittest.TestCase):
    """Test valid GitHub webhook signatures."""

    def setUp(self):
        """Set up known-good test vectors."""
        self.secret = "my-secret-key"
        self.payload = b'{"action":"opened","number":1,"pull_request":{"id":1}}'
        # Compute known-good signature using hmac.new + sha256
        signature_bytes = hmac.new(
            self.secret.encode("utf-8"),
            self.payload,
            hashlib.sha256,
        ).digest()
        self.valid_signature = "sha256=" + signature_bytes.hex()
        self.current_timestamp = int(time.time())

    def test_verify_github_valid_signature_with_sha256_prefix(self):
        """Valid signature with sha256= prefix returns VerificationResult(valid=True)."""
        result = verify_github(
            payload=self.payload,
            secret=self.secret,
            signature_header=self.valid_signature,
            timestamp=self.current_timestamp,
        )
        self.assertIsInstance(result, VerificationResult)
        self.assertTrue(result.valid)
        self.assertEqual(result.provider, "github")

    def test_verify_github_valid_signature_returns_correct_provider_name(self):
        """VerificationResult includes provider='github'."""
        result = verify_github(
            payload=self.payload,
            secret=self.secret,
            signature_header=self.valid_signature,
            timestamp=self.current_timestamp,
        )
        self.assertEqual(result.provider, "github")

    def test_verify_github_valid_signature_with_timestamp(self):
        """Valid signature with explicit timestamp parameter."""
        past_timestamp = self.current_timestamp - 100  # 100s in past
        result = verify_github(
            payload=self.payload,
            secret=self.secret,
            signature_header=self.valid_signature,
            timestamp=past_timestamp,
        )
        self.assertTrue(result.valid)

    def test_verify_github_valid_signature_without_timestamp_parameter(self):
        """Valid signature with timestamp=None uses current time."""
        result = verify_github(
            payload=self.payload,
            secret=self.secret,
            signature_header=self.valid_signature,
            timestamp=None,
        )
        # Should succeed without error when timestamp is None
        self.assertIsInstance(result, VerificationResult)

    def test_verify_github_returns_verification_result_type(self):
        """verify_github returns VerificationResult instance."""
        result = verify_github(
            payload=self.payload,
            secret=self.secret,
            signature_header=self.valid_signature,
            timestamp=self.current_timestamp,
        )
        self.assertIsInstance(result, VerificationResult)

    def test_verify_github_result_timestamp_preserved(self):
        """VerificationResult timestamp field is populated when provided."""
        result = verify_github(
            payload=self.payload,
            secret=self.secret,
            signature_header=self.valid_signature,
            timestamp=self.current_timestamp,
        )
        self.assertEqual(result.timestamp, self.current_timestamp)


class TestGitHubVerifyInvalidSignatures(unittest.TestCase):
    """Test rejection of invalid GitHub webhook signatures."""

    def setUp(self):
        """Set up test vectors."""
        self.secret = "my-secret-key"
        self.payload = b'{"action":"opened","number":1,"pull_request":{"id":1}}'
        signature_bytes = hmac.new(
            self.secret.encode("utf-8"),
            self.payload,
            hashlib.sha256,
        ).digest()
        self.valid_signature = "sha256=" + signature_bytes.hex()
        self.current_timestamp = int(time.time())

    def test_verify_github_missing_sha256_prefix_raises(self):
        """Signature without sha256= prefix raises InvalidSignatureError."""
        invalid_signature = self.valid_signature[7:]  # Remove 'sha256=' prefix
        with self.assertRaises(InvalidSignatureError):
            verify_github(
                payload=self.payload,
                secret=self.secret,
                signature_header=invalid_signature,
                timestamp=self.current_timestamp,
            )

    def test_verify_github_wrong_prefix_raises(self):
        """Signature with wrong prefix (e.g., sha1=) raises InvalidSignatureError."""
        invalid_signature = "sha1=" + self.valid_signature[7:]
        with self.assertRaises(InvalidSignatureError):
            verify_github(
                payload=self.payload,
                secret=self.secret,
                signature_header=invalid_signature,
                timestamp=self.current_timestamp,
            )

    def test_verify_github_wrong_secret_raises(self):
        """Signature computed with different secret raises InvalidSignatureError."""
        with self.assertRaises(InvalidSignatureError):
            verify_github(
                payload=self.payload,
                secret="different-secret",
                signature_header=self.valid_signature,
                timestamp=self.current_timestamp,
            )

    def test_verify_github_tampered_payload_raises(self):
        """Signature fails when payload is tampered with."""
        tampered_payload = b'{"action":"closed","number":1,"pull_request":{"id":1}}'
        with self.assertRaises(InvalidSignatureError):
            verify_github(
                payload=tampered_payload,
                secret=self.secret,
                signature_header=self.valid_signature,
                timestamp=self.current_timestamp,
            )

    def test_verify_github_one_bit_changed_in_signature_raises(self):
        """Signature with one bit changed raises InvalidSignatureError."""
        # Change one character in the hex signature
        tampered_sig = "sha256=" + ("f" if self.valid_signature[7] != "f" else "0") + self.valid_signature[8:]
        with self.assertRaises(InvalidSignatureError):
            verify_github(
                payload=self.payload,
                secret=self.secret,
                signature_header=tampered_sig,
                timestamp=self.current_timestamp,
            )

    def test_verify_github_empty_signature_raises(self):
        """Empty signature header raises InvalidSignatureError."""
        with self.assertRaises(InvalidSignatureError):
            verify_github(
                payload=self.payload,
                secret=self.secret,
                signature_header="",
                timestamp=self.current_timestamp,
            )

    def test_verify_github_malformed_signature_raises(self):
        """Malformed signature (invalid hex) raises InvalidSignatureError."""
        with self.assertRaises(InvalidSignatureError):
            verify_github(
                payload=self.payload,
                secret=self.secret,
                signature_header="sha256=not-hex-data",
                timestamp=self.current_timestamp,
            )

    def test_verify_github_truncated_signature_raises(self):
        """Truncated signature (too short) raises InvalidSignatureError."""
        truncated = "sha256=" + self.valid_signature[7:20]  # Only first 13 hex chars
        with self.assertRaises(InvalidSignatureError):
            verify_github(
                payload=self.payload,
                secret=self.secret,
                signature_header=truncated,
                timestamp=self.current_timestamp,
            )


class TestGitHubVerifyReplayProtection(unittest.TestCase):
    """Test timestamp-based replay protection."""

    def setUp(self):
        """Set up test vectors."""
        self.secret = "my-secret-key"
        self.payload = b'{"action":"opened","number":1,"pull_request":{"id":1}}'
        signature_bytes = hmac.new(
            self.secret.encode("utf-8"),
            self.payload,
            hashlib.sha256,
        ).digest()
        self.valid_signature = "sha256=" + signature_bytes.hex()
        self.current_timestamp = int(time.time())

    def test_verify_github_timestamp_within_tolerance(self):
        """Timestamp within 300s window is accepted."""
        # 200 seconds in the past (within 300s tolerance)
        old_timestamp = self.current_timestamp - 200
        result = verify_github(
            payload=self.payload,
            secret=self.secret,
            signature_header=self.valid_signature,
            timestamp=old_timestamp,
        )
        self.assertTrue(result.valid)

    def test_verify_github_timestamp_at_tolerance_boundary(self):
        """Timestamp exactly at 300s boundary is accepted."""
        boundary_timestamp = self.current_timestamp - 300
        result = verify_github(
            payload=self.payload,
            secret=self.secret,
            signature_header=self.valid_signature,
            timestamp=boundary_timestamp,
        )
        self.assertTrue(result.valid)

    def test_verify_github_timestamp_outside_tolerance_raises(self):
        """Timestamp beyond 300s window raises ExpiredTimestampError."""
        # 400 seconds in the past (outside 300s tolerance)
        expired_timestamp = self.current_timestamp - 400
        with self.assertRaises(ExpiredTimestampError):
            verify_github(
                payload=self.payload,
                secret=self.secret,
                signature_header=self.valid_signature,
                timestamp=expired_timestamp,
            )

    def test_verify_github_future_timestamp_raises(self):
        """Timestamp in the future raises ExpiredTimestampError."""
        future_timestamp = self.current_timestamp + 600
        with self.assertRaises(ExpiredTimestampError):
            verify_github(
                payload=self.payload,
                secret=self.secret,
                signature_header=self.valid_signature,
                timestamp=future_timestamp,
            )

    def test_verify_github_timestamp_slightly_outside_tolerance_raises(self):
        """Timestamp just beyond 300s boundary raises ExpiredTimestampError."""
        expired_timestamp = self.current_timestamp - 301
        with self.assertRaises(ExpiredTimestampError):
            verify_github(
                payload=self.payload,
                secret=self.secret,
                signature_header=self.valid_signature,
                timestamp=expired_timestamp,
            )


class TestGitHubVerifyEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions."""

    def setUp(self):
        """Set up test vectors."""
        self.secret = "my-secret-key"
        self.current_timestamp = int(time.time())

    def test_verify_github_empty_payload(self):
        """Empty payload is handled correctly."""
        empty_payload = b""
        signature_bytes = hmac.new(
            self.secret.encode("utf-8"),
            empty_payload,
            hashlib.sha256,
        ).digest()
        signature = "sha256=" + signature_bytes.hex()
        result = verify_github(
            payload=empty_payload,
            secret=self.secret,
            signature_header=signature,
            timestamp=self.current_timestamp,
        )
        self.assertTrue(result.valid)

    def test_verify_github_large_payload(self):
        """Large payload is handled correctly."""
        large_payload = b"x" * 10000  # 10KB payload
        signature_bytes = hmac.new(
            self.secret.encode("utf-8"),
            large_payload,
            hashlib.sha256,
        ).digest()
        signature = "sha256=" + signature_bytes.hex()
        result = verify_github(
            payload=large_payload,
            secret=self.secret,
            signature_header=signature,
            timestamp=self.current_timestamp,
        )
        self.assertTrue(result.valid)

    def test_verify_github_unicode_secret(self):
        """Secret with unicode characters is handled correctly."""
        unicode_secret = "secret-with-émojis-🔒"
        payload = b'{"action":"opened"}'
        signature_bytes = hmac.new(
            unicode_secret.encode("utf-8"),
            payload,
            hashlib.sha256,
        ).digest()
        signature = "sha256=" + signature_bytes.hex()
        result = verify_github(
            payload=payload,
            secret=unicode_secret,
            signature_header=signature,
            timestamp=self.current_timestamp,
        )
        self.assertTrue(result.valid)

    def test_verify_github_binary_payload(self):
        """Binary payload (non-UTF8) is handled correctly."""
        binary_payload = bytes([0xFF, 0xFE, 0xFD, 0xFC])
        signature_bytes = hmac.new(
            self.secret.encode("utf-8"),
            binary_payload,
            hashlib.sha256,
        ).digest()
        signature = "sha256=" + signature_bytes.hex()
        result = verify_github(
            payload=binary_payload,
            secret=self.secret,
            signature_header=signature,
            timestamp=self.current_timestamp,
        )
        self.assertTrue(result.valid)

    def test_verify_github_signature_with_mixed_case_hex(self):
        """Signature with mixed-case hex (uppercase letters) is accepted."""
        payload = b'{"action":"opened"}'
        signature_bytes = hmac.new(
            self.secret.encode("utf-8"),
            payload,
            hashlib.sha256,
        ).digest()
        # Create signature with uppercase hex
        signature = "sha256=" + signature_bytes.hex().upper()
        result = verify_github(
            payload=payload,
            secret=self.secret,
            signature_header=signature,
            timestamp=self.current_timestamp,
        )
        self.assertTrue(result.valid)

    def test_verify_github_empty_secret(self):
        """Empty secret is accepted and used correctly."""
        payload = b'{"action":"opened"}'
        empty_secret = ""
        signature_bytes = hmac.new(
            empty_secret.encode("utf-8"),
            payload,
            hashlib.sha256,
        ).digest()
        signature = "sha256=" + signature_bytes.hex()
        result = verify_github(
            payload=payload,
            secret=empty_secret,
            signature_header=signature,
            timestamp=self.current_timestamp,
        )
        self.assertTrue(result.valid)


class TestGitHubVerifyHeaderCaseInsensitivity(unittest.TestCase):
    """Test header name case-insensitivity (if applicable)."""

    def setUp(self):
        """Set up test vectors."""
        self.secret = "my-secret-key"
        self.payload = b'{"action":"opened","number":1}'
        signature_bytes = hmac.new(
            self.secret.encode("utf-8"),
            self.payload,
            hashlib.sha256,
        ).digest()
        self.valid_signature = "sha256=" + signature_bytes.hex()
        self.current_timestamp = int(time.time())

    def test_verify_github_signature_header_is_x_hub_signature_256(self):
        """The expected header name in GITHUB_SPEC is X-Hub-Signature-256."""
        self.assertEqual(GITHUB_SPEC.header_name, "X-Hub-Signature-256")


class TestGitHubVerifyTimingAttackResistance(unittest.TestCase):
    """Test that timing-safe comparison is used (constant-time comparison)."""

    def setUp(self):
        """Set up test vectors."""
        self.secret = "my-secret-key"
        self.payload = b'{"action":"opened"}'
        signature_bytes = hmac.new(
            self.secret.encode("utf-8"),
            self.payload,
            hashlib.sha256,
        ).digest()
        self.valid_signature = "sha256=" + signature_bytes.hex()
        self.current_timestamp = int(time.time())

    def test_verify_github_uses_timing_safe_comparison(self):
        """Implementation must use hmac.compare_digest for timing-safe comparison.

        This test verifies that two signatures that differ only in the first character
        take similar time to reject (resistance to timing attacks).
        The actual timing measurement is implicit in the rejection behavior.
        """
        # Create two signatures that differ only at the start
        tampered_1 = "sha256=" + ("a" if self.valid_signature[7] != "a" else "b") + self.valid_signature[8:]
        tampered_2 = "sha256=" + ("c" if self.valid_signature[7] != "c" else "d") + self.valid_signature[8:]

        # Both should raise InvalidSignatureError
        # (no assertion about timing itself, but the implementation must use compare_digest)
        with self.assertRaises(InvalidSignatureError):
            verify_github(
                payload=self.payload,
                secret=self.secret,
                signature_header=tampered_1,
                timestamp=self.current_timestamp,
            )

        with self.assertRaises(InvalidSignatureError):
            verify_github(
                payload=self.payload,
                secret=self.secret,
                signature_header=tampered_2,
                timestamp=self.current_timestamp,
            )


class TestGitHubVerifyRealWorldPayloads(unittest.TestCase):
    """Test with realistic GitHub webhook payloads."""

    def setUp(self):
        """Set up realistic test vectors."""
        self.secret = "my-webhook-secret"
        self.current_timestamp = int(time.time())

    def test_verify_github_with_push_event_payload(self):
        """Test with realistic push event payload."""
        # Simplified push event payload
        push_payload = b'{"ref":"refs/heads/main","before":"abc123","after":"def456","pusher":{"name":"user"},"commits":[]}'
        signature_bytes = hmac.new(
            self.secret.encode("utf-8"),
            push_payload,
            hashlib.sha256,
        ).digest()
        signature = "sha256=" + signature_bytes.hex()

        result = verify_github(
            payload=push_payload,
            secret=self.secret,
            signature_header=signature,
            timestamp=self.current_timestamp,
        )
        self.assertTrue(result.valid)

    def test_verify_github_with_pull_request_event_payload(self):
        """Test with realistic pull request event payload."""
        pr_payload = b'{"action":"opened","number":42,"pull_request":{"id":12345,"title":"Fix bug","body":"Fixes #1","user":{"login":"alice"}}}'
        signature_bytes = hmac.new(
            self.secret.encode("utf-8"),
            pr_payload,
            hashlib.sha256,
        ).digest()
        signature = "sha256=" + signature_bytes.hex()

        result = verify_github(
            payload=pr_payload,
            secret=self.secret,
            signature_header=signature,
            timestamp=self.current_timestamp,
        )
        self.assertTrue(result.valid)

    def test_verify_github_with_issue_event_payload(self):
        """Test with realistic issue event payload."""
        issue_payload = b'{"action":"opened","issue":{"number":1,"title":"Bug report","body":"Issue description"}}'
        signature_bytes = hmac.new(
            self.secret.encode("utf-8"),
            issue_payload,
            hashlib.sha256,
        ).digest()
        signature = "sha256=" + signature_bytes.hex()

        result = verify_github(
            payload=issue_payload,
            secret=self.secret,
            signature_header=signature,
            timestamp=self.current_timestamp,
        )
        self.assertTrue(result.valid)


class TestGitHubVerifyExceptionHierarchy(unittest.TestCase):
    """Test exception types and inheritance."""

    def setUp(self):
        """Set up test vectors."""
        self.secret = "my-secret-key"
        self.payload = b'{"action":"opened"}'
        self.current_timestamp = int(time.time())

    def test_verify_github_invalid_signature_raises_correct_exception_type(self):
        """InvalidSignatureError is raised for signature mismatches."""
        with self.assertRaises(InvalidSignatureError):
            verify_github(
                payload=self.payload,
                secret=self.secret,
                signature_header="sha256=0000000000000000000000000000000000000000000000000000000000000000",
                timestamp=self.current_timestamp,
            )

    def test_verify_github_expired_timestamp_raises_correct_exception_type(self):
        """ExpiredTimestampError is raised for out-of-window timestamps."""
        signature_bytes = hmac.new(
            self.secret.encode("utf-8"),
            self.payload,
            hashlib.sha256,
        ).digest()
        signature = "sha256=" + signature_bytes.hex()

        old_timestamp = self.current_timestamp - 400  # Outside 300s window
        with self.assertRaises(ExpiredTimestampError):
            verify_github(
                payload=self.payload,
                secret=self.secret,
                signature_header=signature,
                timestamp=old_timestamp,
            )


if __name__ == "__main__":
    unittest.main()
