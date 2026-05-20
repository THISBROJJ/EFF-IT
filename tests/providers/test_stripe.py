"""
Unit tests for Stripe webhook signature verification adapter.

Tests cover the Stripe v1 signature scheme:
  - Header format: t=<unix_ts>,v1=<hex_sig>[,v1=<hex_sig>...]
  - Signed payload: f"{timestamp}.{payload.decode()}"
  - HMAC-SHA256 with hex-encoded result

Tests validate:
  1. Valid signatures with correct timestamp and secret
  2. Multiple v1 elements (rolling secret scenario)
  3. Expired timestamps (default 5-min window)
  4. Malformed headers (missing t, missing v1, no elements)
  5. Tampered payloads
  6. Replay attempts (old timestamp outside window)
  7. One-bit-off signature detection (timing-safe comparison)
  8. Resource bounds enforcement (header length, v1 element count)

Coverage target: ≥90% on src/webhooksig/providers/stripe.py
"""

import unittest
import hmac
import hashlib
import time
from webhooksig.providers.stripe import (
    verify_stripe,
    STRIPE_SPEC,
    SCHEME_VERSION,
)
from webhooksig.types import (
    InvalidSignatureError,
    ExpiredTimestampError,
    VerificationResult,
)


class TestStripeSchemeMetadata(unittest.TestCase):
    """Test module-level metadata and constants."""

    def test_scheme_version_defined(self):
        """SCHEME_VERSION should be 'stripe-v1'."""
        self.assertEqual(SCHEME_VERSION, "stripe-v1")

    def test_stripe_spec_defined(self):
        """STRIPE_SPEC should be a SignatureSpec instance."""
        self.assertIsNotNone(STRIPE_SPEC)
        self.assertEqual(STRIPE_SPEC.algorithm, "sha256")
        self.assertEqual(STRIPE_SPEC.header_name, "Stripe-Signature")
        self.assertEqual(STRIPE_SPEC.timestamp_tolerance_s, 300)  # 5 minutes default

    def test_stripe_spec_encoding_hex(self):
        """STRIPE_SPEC encoding should be 'hex'."""
        self.assertEqual(STRIPE_SPEC.encoding, "hex")


class TestStripeValidSignature(unittest.TestCase):
    """Test happy path: valid signatures with correct timestamp and secret."""

    def setUp(self):
        """Set up test fixtures."""
        self.secret = "whsec_test1234567890abcdefghij"
        self.payload = b'{"id":"evt_test","object":"event"}'
        self.now = int(time.time())
        self.timestamp = self.now - 10  # 10 seconds ago (within 5-min window)

    def _make_signature(self, timestamp: int, payload: bytes, secret: str) -> str:
        """Compute Stripe v1 HMAC-SHA256 signature."""
        signed_payload = f"{timestamp}.{payload.decode()}".encode()
        sig = hmac.new(
            secret.encode(),
            signed_payload,
            hashlib.sha256,
        ).hexdigest()
        return sig

    def test_valid_signature_header(self):
        """Valid t=...,v1=... header should verify successfully."""
        sig = self._make_signature(self.timestamp, self.payload, self.secret)
        header = f"t={self.timestamp},v1={sig}"

        result = verify_stripe(
            self.payload,
            self.secret,
            header,
            now=self.now,
        )

        self.assertIsInstance(result, VerificationResult)
        self.assertTrue(result.valid)
        self.assertEqual(result.provider, "stripe")
        self.assertEqual(result.timestamp, self.timestamp)

    def test_valid_signature_with_multiple_v1_elements(self):
        """Multiple v1 elements (rolling secret) — should accept if any matches."""
        # Generate three signatures: one old (doesn't match), current, one future
        sig_old = self._make_signature(self.timestamp, self.payload, "old_secret")
        sig_current = self._make_signature(self.timestamp, self.payload, self.secret)
        sig_future = self._make_signature(self.timestamp, self.payload, "future_secret")

        # Order: old, current, future (Stripe may rotate keys)
        header = f"t={self.timestamp},v1={sig_old},v1={sig_current},v1={sig_future}"

        result = verify_stripe(
            self.payload,
            self.secret,
            header,
            now=self.now,
        )

        self.assertTrue(result.valid)
        self.assertEqual(result.timestamp, self.timestamp)

    def test_valid_signature_multiple_v1_elements_current_last(self):
        """Multiple v1 elements with current signature at the end."""
        sig_old = self._make_signature(self.timestamp, self.payload, "old_secret")
        sig_current = self._make_signature(self.timestamp, self.payload, self.secret)

        header = f"t={self.timestamp},v1={sig_old},v1={sig_current}"

        result = verify_stripe(
            self.payload,
            self.secret,
            header,
            now=self.now,
        )

        self.assertTrue(result.valid)

    def test_valid_signature_single_v1_element(self):
        """Single v1 element (no rotation) should verify."""
        sig = self._make_signature(self.timestamp, self.payload, self.secret)
        header = f"t={self.timestamp},v1={sig}"

        result = verify_stripe(
            self.payload,
            self.secret,
            header,
            now=self.now,
        )

        self.assertTrue(result.valid)


class TestStripeExpiredTimestamp(unittest.TestCase):
    """Test timestamp expiration: default 5-minute window."""

    def setUp(self):
        """Set up test fixtures."""
        self.secret = "whsec_test1234567890abcdefghij"
        self.payload = b'{"id":"evt_test","object":"event"}'
        self.now = int(time.time())

    def _make_signature(self, timestamp: int, payload: bytes, secret: str) -> str:
        """Compute Stripe v1 HMAC-SHA256 signature."""
        signed_payload = f"{timestamp}.{payload.decode()}".encode()
        sig = hmac.new(
            secret.encode(),
            signed_payload,
            hashlib.sha256,
        ).hexdigest()
        return sig

    def test_timestamp_at_boundary_just_valid(self):
        """Timestamp exactly at tolerance boundary (5 min) should be valid."""
        # 5 minutes = 300 seconds
        timestamp = self.now - 300
        sig = self._make_signature(timestamp, self.payload, self.secret)
        header = f"t={timestamp},v1={sig}"

        result = verify_stripe(
            self.payload,
            self.secret,
            header,
            now=self.now,
        )

        self.assertTrue(result.valid)

    def test_timestamp_just_outside_tolerance(self):
        """Timestamp just outside tolerance (301s) should be rejected."""
        # 5 minutes + 1 second
        timestamp = self.now - 301
        sig = self._make_signature(timestamp, self.payload, self.secret)
        header = f"t={timestamp},v1={sig}"

        with self.assertRaises(ExpiredTimestampError) as ctx:
            verify_stripe(
                self.payload,
                self.secret,
                header,
                now=self.now,
            )

        self.assertEqual(ctx.exception.provider, "stripe")

    def test_timestamp_far_in_past(self):
        """Timestamp far in the past (1 hour) should be rejected."""
        timestamp = self.now - 3600
        sig = self._make_signature(timestamp, self.payload, self.secret)
        header = f"t={timestamp},v1={sig}"

        with self.assertRaises(ExpiredTimestampError):
            verify_stripe(
                self.payload,
                self.secret,
                header,
                now=self.now,
            )

    def test_timestamp_in_future(self):
        """Timestamp in the future should be rejected."""
        timestamp = self.now + 100
        sig = self._make_signature(timestamp, self.payload, self.secret)
        header = f"t={timestamp},v1={sig}"

        with self.assertRaises(ExpiredTimestampError):
            verify_stripe(
                self.payload,
                self.secret,
                header,
                now=self.now,
            )

    def test_replay_attempt_old_timestamp(self):
        """Replay attempt with old timestamp should be rejected."""
        # Original event timestamp
        original_timestamp = self.now - 400  # 6 min 40 sec ago

        # Attacker tries to replay with now = original_timestamp + 10 seconds
        # This is still 6+ minutes in the past relative to current time
        attacker_now = original_timestamp + 10

        sig = self._make_signature(original_timestamp, self.payload, self.secret)
        header = f"t={original_timestamp},v1={sig}"

        with self.assertRaises(ExpiredTimestampError):
            verify_stripe(
                self.payload,
                self.secret,
                header,
                now=self.now,
            )


class TestStripeMalformedHeader(unittest.TestCase):
    """Test malformed headers: missing t, missing v1, empty elements."""

    def setUp(self):
        """Set up test fixtures."""
        self.secret = "whsec_test1234567890abcdefghij"
        self.payload = b'{"id":"evt_test","object":"event"}'
        self.now = int(time.time())
        self.timestamp = self.now - 10

    def _make_signature(self, timestamp: int, payload: bytes, secret: str) -> str:
        """Compute Stripe v1 HMAC-SHA256 signature."""
        signed_payload = f"{timestamp}.{payload.decode()}".encode()
        sig = hmac.new(
            secret.encode(),
            signed_payload,
            hashlib.sha256,
        ).hexdigest()
        return sig

    def test_header_missing_t_element(self):
        """Header with no t= element should raise InvalidSignatureError."""
        sig = self._make_signature(self.timestamp, self.payload, self.secret)
        header = f"v1={sig}"

        with self.assertRaises(InvalidSignatureError) as ctx:
            verify_stripe(
                self.payload,
                self.secret,
                header,
                now=self.now,
            )

        self.assertEqual(ctx.exception.provider, "stripe")

    def test_header_missing_v1_element(self):
        """Header with no v1= element should raise InvalidSignatureError."""
        header = f"t={self.timestamp}"

        with self.assertRaises(InvalidSignatureError) as ctx:
            verify_stripe(
                self.payload,
                self.secret,
                header,
                now=self.now,
            )

        self.assertEqual(ctx.exception.provider, "stripe")

    def test_header_empty_string(self):
        """Empty header string should raise InvalidSignatureError."""
        with self.assertRaises(InvalidSignatureError):
            verify_stripe(
                self.payload,
                self.secret,
                "",
                now=self.now,
            )

    def test_header_malformed_t_value(self):
        """Header with non-numeric t value should raise InvalidSignatureError."""
        sig = self._make_signature(self.timestamp, self.payload, self.secret)
        header = f"t=not_a_number,v1={sig}"

        with self.assertRaises(InvalidSignatureError):
            verify_stripe(
                self.payload,
                self.secret,
                header,
                now=self.now,
            )

    def test_header_empty_v1_value(self):
        """Header with empty v1= value should raise InvalidSignatureError."""
        header = f"t={self.timestamp},v1="

        with self.assertRaises(InvalidSignatureError):
            verify_stripe(
                self.payload,
                self.secret,
                header,
                now=self.now,
            )

    def test_header_extra_whitespace(self):
        """Header with unexpected whitespace should raise InvalidSignatureError."""
        sig = self._make_signature(self.timestamp, self.payload, self.secret)
        # Space after comma
        header = f"t={self.timestamp}, v1={sig}"

        with self.assertRaises(InvalidSignatureError):
            verify_stripe(
                self.payload,
                self.secret,
                header,
                now=self.now,
            )

    def test_header_unexpected_elements(self):
        """Header with unexpected key=value pairs should still validate t and v1."""
        # Some Stripe features might add new elements; we should ignore unknown ones
        sig = self._make_signature(self.timestamp, self.payload, self.secret)
        header = f"t={self.timestamp},v1={sig},foo=bar"

        result = verify_stripe(
            self.payload,
            self.secret,
            header,
            now=self.now,
        )

        self.assertTrue(result.valid)


class TestStripeTamperedPayload(unittest.TestCase):
    """Test tampered payloads: bit flip, modified content, wrong encoding."""

    def setUp(self):
        """Set up test fixtures."""
        self.secret = "whsec_test1234567890abcdefghij"
        self.payload = b'{"id":"evt_test","object":"event"}'
        self.now = int(time.time())
        self.timestamp = self.now - 10

    def _make_signature(self, timestamp: int, payload: bytes, secret: str) -> str:
        """Compute Stripe v1 HMAC-SHA256 signature."""
        signed_payload = f"{timestamp}.{payload.decode()}".encode()
        sig = hmac.new(
            secret.encode(),
            signed_payload,
            hashlib.sha256,
        ).hexdigest()
        return sig

    def test_payload_bit_flip(self):
        """Payload with a single bit flipped should be rejected (timing-safe)."""
        sig = self._make_signature(self.timestamp, self.payload, self.secret)
        header = f"t={self.timestamp},v1={sig}"

        # Flip one bit in the payload
        tampered = bytearray(self.payload)
        tampered[0] ^= 1  # Flip first bit of first byte

        with self.assertRaises(InvalidSignatureError):
            verify_stripe(
                bytes(tampered),
                self.secret,
                header,
                now=self.now,
            )

    def test_payload_modified_json_field(self):
        """Modified JSON field should be rejected."""
        sig = self._make_signature(self.timestamp, self.payload, self.secret)
        header = f"t={self.timestamp},v1={sig}"

        # Change evt_test to evt_bogus
        tampered = self.payload.replace(b"evt_test", b"evt_bogus")

        with self.assertRaises(InvalidSignatureError):
            verify_stripe(
                tampered,
                self.secret,
                header,
                now=self.now,
            )

    def test_payload_extra_byte(self):
        """Payload with extra byte appended should be rejected."""
        sig = self._make_signature(self.timestamp, self.payload, self.secret)
        header = f"t={self.timestamp},v1={sig}"

        tampered = self.payload + b"X"

        with self.assertRaises(InvalidSignatureError):
            verify_stripe(
                tampered,
                self.secret,
                header,
                now=self.now,
            )

    def test_payload_missing_byte(self):
        """Payload with missing byte should be rejected."""
        sig = self._make_signature(self.timestamp, self.payload, self.secret)
        header = f"t={self.timestamp},v1={sig}"

        tampered = self.payload[:-1]

        with self.assertRaises(InvalidSignatureError):
            verify_stripe(
                tampered,
                self.secret,
                header,
                now=self.now,
            )

    def test_wrong_secret(self):
        """Using wrong secret should be rejected."""
        sig = self._make_signature(self.timestamp, self.payload, self.secret)
        header = f"t={self.timestamp},v1={sig}"

        with self.assertRaises(InvalidSignatureError):
            verify_stripe(
                self.payload,
                "wrong_secret_xyz",
                header,
                now=self.now,
            )


class TestStripeSignatureEncoding(unittest.TestCase):
    """Test hex signature encoding and validation."""

    def setUp(self):
        """Set up test fixtures."""
        self.secret = "whsec_test1234567890abcdefghij"
        self.payload = b'{"id":"evt_test","object":"event"}'
        self.now = int(time.time())
        self.timestamp = self.now - 10

    def _make_signature(self, timestamp: int, payload: bytes, secret: str) -> str:
        """Compute Stripe v1 HMAC-SHA256 signature."""
        signed_payload = f"{timestamp}.{payload.decode()}".encode()
        sig = hmac.new(
            secret.encode(),
            signed_payload,
            hashlib.sha256,
        ).hexdigest()
        return sig

    def test_hex_signature_lowercase(self):
        """Hex signature in lowercase should validate correctly."""
        sig = self._make_signature(self.timestamp, self.payload, self.secret)
        self.assertTrue(sig.islower() or sig.isdigit(), "Signature should be lowercase hex")
        header = f"t={self.timestamp},v1={sig}"

        result = verify_stripe(
            self.payload,
            self.secret,
            header,
            now=self.now,
        )

        self.assertTrue(result.valid)

    def test_hex_signature_uppercase(self):
        """Hex signature in uppercase should be rejected (case-sensitive)."""
        sig = self._make_signature(self.timestamp, self.payload, self.secret)
        sig_upper = sig.upper()
        header = f"t={self.timestamp},v1={sig_upper}"

        with self.assertRaises(InvalidSignatureError):
            verify_stripe(
                self.payload,
                self.secret,
                header,
                now=self.now,
            )

    def test_hex_signature_invalid_character(self):
        """Hex signature with invalid character should be rejected."""
        sig = self._make_signature(self.timestamp, self.payload, self.secret)
        # Replace a hex digit with 'G' (not valid hex)
        sig_invalid = sig[:-1] + "G"
        header = f"t={self.timestamp},v1={sig_invalid}"

        with self.assertRaises(InvalidSignatureError):
            verify_stripe(
                self.payload,
                self.secret,
                header,
                now=self.now,
            )

    def test_hex_signature_wrong_length(self):
        """Hex signature with wrong length should be rejected."""
        sig = self._make_signature(self.timestamp, self.payload, self.secret)
        # Remove last character
        sig_short = sig[:-1]
        header = f"t={self.timestamp},v1={sig_short}"

        with self.assertRaises(InvalidSignatureError):
            verify_stripe(
                self.payload,
                self.secret,
                header,
                now=self.now,
            )


class TestStripeResourceBounds(unittest.TestCase):
    """Test resource bounds: header length, v1 element count."""

    def setUp(self):
        """Set up test fixtures."""
        self.secret = "whsec_test1234567890abcdefghij"
        self.payload = b'{"id":"evt_test","object":"event"}'
        self.now = int(time.time())
        self.timestamp = self.now - 10

    def _make_signature(self, timestamp: int, payload: bytes, secret: str) -> str:
        """Compute Stripe v1 HMAC-SHA256 signature."""
        signed_payload = f"{timestamp}.{payload.decode()}".encode()
        sig = hmac.new(
            secret.encode(),
            signed_payload,
            hashlib.sha256,
        ).hexdigest()
        return sig

    def test_header_length_at_limit(self):
        """Header at 4096-byte limit should be accepted."""
        sig = self._make_signature(self.timestamp, self.payload, self.secret)
        # Create a header close to 4096 bytes by adding many v1 elements
        header = f"t={self.timestamp},v1={sig}"

        # Add dummy v1 signatures until we approach 4096 bytes
        dummy_sig = "a" * 64  # 64 hex chars = 256-bit hash
        while len(header.encode()) < 4096 - 100:
            header += f",v1={dummy_sig}"

        # Should still accept if header is at or under limit
        # (only the current signature needs to match, others ignored)
        result = verify_stripe(
            self.payload,
            self.secret,
            header,
            now=self.now,
        )

        self.assertTrue(result.valid)

    def test_header_length_exceeds_limit(self):
        """Header exceeding 4096-byte limit should be rejected."""
        sig = self._make_signature(self.timestamp, self.payload, self.secret)
        header = f"t={self.timestamp},v1={sig}"

        # Add many dummy signatures to exceed limit
        dummy_sig = "b" * 64
        while len(header.encode()) <= 4096:
            header += f",v1={dummy_sig}"

        with self.assertRaises(InvalidSignatureError) as ctx:
            verify_stripe(
                self.payload,
                self.secret,
                header,
                now=self.now,
            )

        # Error should be about header size, not signature mismatch
        self.assertEqual(ctx.exception.provider, "stripe")

    def test_v1_element_count_at_limit(self):
        """At 16 v1 elements (limit) should be accepted."""
        sig = self._make_signature(self.timestamp, self.payload, self.secret)
        header = f"t={self.timestamp},v1={sig}"

        # Add 15 dummy signatures (plus the current one = 16 total)
        dummy_sig = "c" * 64
        for _ in range(15):
            header += f",v1={dummy_sig}"

        result = verify_stripe(
            self.payload,
            self.secret,
            header,
            now=self.now,
        )

        self.assertTrue(result.valid)

    def test_v1_element_count_exceeds_limit(self):
        """More than 16 v1 elements should be rejected."""
        sig = self._make_signature(self.timestamp, self.payload, self.secret)
        header = f"t={self.timestamp},v1={sig}"

        # Add 16 more dummy signatures (17 total)
        dummy_sig = "d" * 64
        for _ in range(16):
            header += f",v1={dummy_sig}"

        with self.assertRaises(InvalidSignatureError) as ctx:
            verify_stripe(
                self.payload,
                self.secret,
                header,
                now=self.now,
            )

        self.assertEqual(ctx.exception.provider, "stripe")


class TestStripeEdgeCases(unittest.TestCase):
    """Test edge cases: empty payload, large payload, special characters."""

    def setUp(self):
        """Set up test fixtures."""
        self.secret = "whsec_test1234567890abcdefghij"
        self.now = int(time.time())
        self.timestamp = self.now - 10

    def _make_signature(self, timestamp: int, payload: bytes, secret: str) -> str:
        """Compute Stripe v1 HMAC-SHA256 signature."""
        signed_payload = f"{timestamp}.{payload.decode()}".encode()
        sig = hmac.new(
            secret.encode(),
            signed_payload,
            hashlib.sha256,
        ).hexdigest()
        return sig

    def test_empty_payload(self):
        """Empty payload should be verifiable."""
        payload = b""
        sig = self._make_signature(self.timestamp, payload, self.secret)
        header = f"t={self.timestamp},v1={sig}"

        result = verify_stripe(
            payload,
            self.secret,
            header,
            now=self.now,
        )

        self.assertTrue(result.valid)

    def test_large_payload(self):
        """Large payload (10 KB) should be verifiable."""
        payload = b"X" * 10240
        sig = self._make_signature(self.timestamp, payload, self.secret)
        header = f"t={self.timestamp},v1={sig}"

        result = verify_stripe(
            payload,
            self.secret,
            header,
            now=self.now,
        )

        self.assertTrue(result.valid)

    def test_payload_with_special_json_characters(self):
        """Payload with special JSON characters should verify."""
        payload = b'{"msg":"hello\\"world\\n","status":"ok"}'
        sig = self._make_signature(self.timestamp, payload, self.secret)
        header = f"t={self.timestamp},v1={sig}"

        result = verify_stripe(
            payload,
            self.secret,
            header,
            now=self.now,
        )

        self.assertTrue(result.valid)

    def test_secret_with_special_characters(self):
        """Secret with special characters should work."""
        secret = "whsec_!@#$%^&*()_+[]{}|;:',.<>?/~`"
        payload = b'{"test":"data"}'
        sig = self._make_signature(self.timestamp, payload, secret)
        header = f"t={self.timestamp},v1={sig}"

        result = verify_stripe(
            payload,
            secret,
            header,
            now=self.now,
        )

        self.assertTrue(result.valid)


class TestStripeNowParameter(unittest.TestCase):
    """Test the now parameter for timestamp comparison."""

    def setUp(self):
        """Set up test fixtures."""
        self.secret = "whsec_test1234567890abcdefghij"
        self.payload = b'{"id":"evt_test","object":"event"}'

    def _make_signature(self, timestamp: int, payload: bytes, secret: str) -> str:
        """Compute Stripe v1 HMAC-SHA256 signature."""
        signed_payload = f"{timestamp}.{payload.decode()}".encode()
        sig = hmac.new(
            secret.encode(),
            signed_payload,
            hashlib.sha256,
        ).hexdigest()
        return sig

    def test_now_parameter_explicit(self):
        """Explicit now parameter should be used for timestamp validation."""
        now = 1000000
        timestamp = now - 100

        sig = self._make_signature(timestamp, self.payload, self.secret)
        header = f"t={timestamp},v1={sig}"

        result = verify_stripe(
            self.payload,
            self.secret,
            header,
            now=now,
        )

        self.assertTrue(result.valid)

    def test_now_parameter_none_uses_current_time(self):
        """When now=None, should use current time."""
        now = int(time.time())
        timestamp = now - 100

        sig = self._make_signature(timestamp, self.payload, self.secret)
        header = f"t={timestamp},v1={sig}"

        result = verify_stripe(
            self.payload,
            self.secret,
            header,
            now=None,
        )

        self.assertTrue(result.valid)

    def test_now_parameter_default(self):
        """Default now parameter should use current time."""
        now = int(time.time())
        timestamp = now - 100

        sig = self._make_signature(timestamp, self.payload, self.secret)
        header = f"t={timestamp},v1={sig}"

        # Call without now parameter
        result = verify_stripe(
            self.payload,
            self.secret,
            header,
        )

        self.assertTrue(result.valid)


class TestStripeExceptionDetails(unittest.TestCase):
    """Test exception handling and error messages (no secret leakage)."""

    def setUp(self):
        """Set up test fixtures."""
        self.secret = "whsec_test1234567890abcdefghij"
        self.payload = b'{"id":"evt_test","object":"event"}'
        self.now = int(time.time())
        self.timestamp = self.now - 10

    def _make_signature(self, timestamp: int, payload: bytes, secret: str) -> str:
        """Compute Stripe v1 HMAC-SHA256 signature."""
        signed_payload = f"{timestamp}.{payload.decode()}".encode()
        sig = hmac.new(
            secret.encode(),
            signed_payload,
            hashlib.sha256,
        ).hexdigest()
        return sig

    def test_invalid_signature_error_has_provider(self):
        """InvalidSignatureError should include provider info."""
        sig = self._make_signature(self.timestamp, self.payload, self.secret)
        header = f"t={self.timestamp},v1={sig}"

        with self.assertRaises(InvalidSignatureError) as ctx:
            verify_stripe(
                self.payload,
                "wrong_secret",
                header,
                now=self.now,
            )

        self.assertEqual(ctx.exception.provider, "stripe")

    def test_expired_timestamp_error_has_provider(self):
        """ExpiredTimestampError should include provider info."""
        timestamp = self.now - 400
        sig = self._make_signature(timestamp, self.payload, self.secret)
        header = f"t={timestamp},v1={sig}"

        with self.assertRaises(ExpiredTimestampError) as ctx:
            verify_stripe(
                self.payload,
                self.secret,
                header,
                now=self.now,
            )

        self.assertEqual(ctx.exception.provider, "stripe")

    def test_error_str_does_not_leak_secret(self):
        """Error __str__ should not contain the secret."""
        sig = self._make_signature(self.timestamp, self.payload, self.secret)
        header = f"t={self.timestamp},v1={sig}"

        with self.assertRaises(InvalidSignatureError) as ctx:
            verify_stripe(
                self.payload,
                "wrong_secret",
                header,
                now=self.now,
            )

        error_str = str(ctx.exception)
        self.assertNotIn(self.secret, error_str)
        self.assertNotIn("wrong_secret", error_str)

    def test_error_repr_does_not_leak_secret(self):
        """Error __repr__ should not contain the secret."""
        sig = self._make_signature(self.timestamp, self.payload, self.secret)
        header = f"t={self.timestamp},v1={sig}"

        with self.assertRaises(InvalidSignatureError) as ctx:
            verify_stripe(
                self.payload,
                "wrong_secret",
                header,
                now=self.now,
            )

        error_repr = repr(ctx.exception)
        self.assertNotIn(self.secret, error_repr)
        self.assertNotIn("wrong_secret", error_repr)


class TestStripeVerificationResultDetails(unittest.TestCase):
    """Test VerificationResult structure and content."""

    def setUp(self):
        """Set up test fixtures."""
        self.secret = "whsec_test1234567890abcdefghij"
        self.payload = b'{"id":"evt_test","object":"event"}'
        self.now = int(time.time())
        self.timestamp = self.now - 10

    def _make_signature(self, timestamp: int, payload: bytes, secret: str) -> str:
        """Compute Stripe v1 HMAC-SHA256 signature."""
        signed_payload = f"{timestamp}.{payload.decode()}".encode()
        sig = hmac.new(
            secret.encode(),
            signed_payload,
            hashlib.sha256,
        ).hexdigest()
        return sig

    def test_result_has_valid_flag(self):
        """VerificationResult should have valid=True on success."""
        sig = self._make_signature(self.timestamp, self.payload, self.secret)
        header = f"t={self.timestamp},v1={sig}"

        result = verify_stripe(
            self.payload,
            self.secret,
            header,
            now=self.now,
        )

        self.assertTrue(hasattr(result, "valid"))
        self.assertTrue(result.valid)

    def test_result_has_provider(self):
        """VerificationResult should have provider='stripe'."""
        sig = self._make_signature(self.timestamp, self.payload, self.secret)
        header = f"t={self.timestamp},v1={sig}"

        result = verify_stripe(
            self.payload,
            self.secret,
            header,
            now=self.now,
        )

        self.assertTrue(hasattr(result, "provider"))
        self.assertEqual(result.provider, "stripe")

    def test_result_has_timestamp(self):
        """VerificationResult should include the parsed timestamp."""
        sig = self._make_signature(self.timestamp, self.payload, self.secret)
        header = f"t={self.timestamp},v1={sig}"

        result = verify_stripe(
            self.payload,
            self.secret,
            header,
            now=self.now,
        )

        self.assertTrue(hasattr(result, "timestamp"))
        self.assertEqual(result.timestamp, self.timestamp)


if __name__ == "__main__":
    unittest.main()
