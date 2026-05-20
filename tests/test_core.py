"""Unit tests for webhooksig.core.verify() function.

Tests the webhook signature verifier core module with comprehensive coverage
of happy paths, error cases, edge cases, and security concerns.

Coverage targets:
- Happy path: valid signature, correct secret, within timestamp window
- Tampered payload: altered payload with original signature
- One-bit-off signature: verify timing-safe comparison catches subtle changes
- Wrong secret: signature computed with different secret
- Expired timestamp: timestamp outside tolerance window
- Missing timestamp: when tolerance_s is set but timestamp is None
- Algorithm confusion: attempt to use wrong algorithm
"""

import hmac
import hashlib
import time
import unittest
from unittest.mock import patch

from webhooksig.core import verify
from webhooksig.types import (
    SignatureSpec,
    VerificationResult,
    InvalidSignatureError,
    ExpiredTimestampError,
)


class TestVerifyHappyPath(unittest.TestCase):
    """Test cases for the happy path — valid signature, correct secret, valid timestamp."""

    def setUp(self):
        """Set up common test fixtures."""
        self.payload = b"test webhook payload"
        self.secret = "test-secret-key"
        self.spec = SignatureSpec(
            algorithm="sha256",
            header_name="X-Webhook-Signature",
            encoding="hex",
            timestamp_tolerance_s=300,
        )

    def test_verify_valid_signature_with_hex_encoding(self):
        """Happy path: valid signature in hex encoding is accepted."""
        # Compute correct signature
        signature = hmac.new(
            self.secret.encode(),
            self.payload,
            hashlib.sha256,
        ).hexdigest()

        result = verify(
            payload=self.payload,
            secret=self.secret,
            signature=signature,
            spec=self.spec,
        )

        self.assertIsInstance(result, VerificationResult)
        self.assertTrue(result.valid)
        self.assertEqual(result.provider, "webhooksig")

    def test_verify_valid_signature_without_timestamp(self):
        """Happy path: verification succeeds when timestamp is not provided and tolerance is 0."""
        spec = SignatureSpec(
            algorithm="sha256",
            header_name="X-Webhook-Signature",
            encoding="hex",
            timestamp_tolerance_s=0,
        )
        signature = hmac.new(
            self.secret.encode(),
            self.payload,
            hashlib.sha256,
        ).hexdigest()

        result = verify(
            payload=self.payload,
            secret=self.secret,
            signature=signature,
            spec=spec,
            timestamp=None,
        )

        self.assertTrue(result.valid)
        self.assertIsNone(result.timestamp)

    def test_verify_valid_signature_with_current_timestamp(self):
        """Happy path: valid signature with current timestamp is accepted."""
        current_time = int(time.time())
        spec = SignatureSpec(
            algorithm="sha256",
            header_name="X-Webhook-Signature",
            encoding="hex",
            timestamp_tolerance_s=300,
        )
        signature = hmac.new(
            self.secret.encode(),
            self.payload,
            hashlib.sha256,
        ).hexdigest()

        result = verify(
            payload=self.payload,
            secret=self.secret,
            signature=signature,
            spec=spec,
            timestamp=current_time,
            now=current_time,
        )

        self.assertTrue(result.valid)
        self.assertEqual(result.timestamp, current_time)

    def test_verify_valid_signature_within_tolerance_window(self):
        """Happy path: timestamp within tolerance window is accepted."""
        now = 1000000
        timestamp = now - 100  # 100 seconds in the past
        spec = SignatureSpec(
            algorithm="sha256",
            header_name="X-Webhook-Signature",
            encoding="hex",
            timestamp_tolerance_s=300,
        )
        signature = hmac.new(
            self.secret.encode(),
            self.payload,
            hashlib.sha256,
        ).hexdigest()

        result = verify(
            payload=self.payload,
            secret=self.secret,
            signature=signature,
            spec=spec,
            timestamp=timestamp,
            now=now,
        )

        self.assertTrue(result.valid)

    def test_verify_signature_at_tolerance_boundary(self):
        """Happy path: timestamp exactly at tolerance boundary is accepted."""
        now = 1000000
        timestamp = now - 300  # Exactly 300 seconds in the past
        spec = SignatureSpec(
            algorithm="sha256",
            header_name="X-Webhook-Signature",
            encoding="hex",
            timestamp_tolerance_s=300,
        )
        signature = hmac.new(
            self.secret.encode(),
            self.payload,
            hashlib.sha256,
        ).hexdigest()

        result = verify(
            payload=self.payload,
            secret=self.secret,
            signature=signature,
            spec=spec,
            timestamp=timestamp,
            now=now,
        )

        self.assertTrue(result.valid)


class TestVerifyTamperedPayload(unittest.TestCase):
    """Test cases for tampered payload detection."""

    def setUp(self):
        """Set up common test fixtures."""
        self.payload = b"test webhook payload"
        self.secret = "test-secret-key"
        self.spec = SignatureSpec(
            algorithm="sha256",
            header_name="X-Webhook-Signature",
            encoding="hex",
            timestamp_tolerance_s=300,
        )

    def test_verify_tampered_payload_rejected(self):
        """Tampered payload: altered payload fails signature verification."""
        # Compute signature for original payload
        signature = hmac.new(
            self.secret.encode(),
            self.payload,
            hashlib.sha256,
        ).hexdigest()

        # Attempt to verify with different payload
        tampered_payload = b"tampered webhook payload"

        with self.assertRaises(InvalidSignatureError):
            verify(
                payload=tampered_payload,
                secret=self.secret,
                signature=signature,
                spec=self.spec,
            )

    def test_verify_payload_with_single_byte_change_rejected(self):
        """Tampered payload: single byte change is detected."""
        signature = hmac.new(
            self.secret.encode(),
            self.payload,
            hashlib.sha256,
        ).hexdigest()

        # Change one byte in the payload
        tampered_payload = bytearray(self.payload)
        tampered_payload[0] ^= 0x01  # Flip one bit
        tampered_payload = bytes(tampered_payload)

        with self.assertRaises(InvalidSignatureError):
            verify(
                payload=tampered_payload,
                secret=self.secret,
                signature=signature,
                spec=self.spec,
            )

    def test_verify_empty_payload_with_non_empty_signature(self):
        """Tampered payload: empty payload with signature for non-empty payload fails."""
        signature = hmac.new(
            self.secret.encode(),
            self.payload,
            hashlib.sha256,
        ).hexdigest()

        with self.assertRaises(InvalidSignatureError):
            verify(
                payload=b"",
                secret=self.secret,
                signature=signature,
                spec=self.spec,
            )


class TestVerifyOneBitOffSignature(unittest.TestCase):
    """Test cases for one-bit-off signature detection (critical spec risk #1).

    The timing-safe comparison must catch even single-bit differences in the
    signature, preventing any exploitation of timing attacks.
    """

    def setUp(self):
        """Set up common test fixtures."""
        self.payload = b"test webhook payload"
        self.secret = "test-secret-key"
        self.spec = SignatureSpec(
            algorithm="sha256",
            header_name="X-Webhook-Signature",
            encoding="hex",
            timestamp_tolerance_s=300,
        )

    def test_verify_one_bit_off_signature_hex_rejected(self):
        """One-bit-off signature: single hex digit change is rejected."""
        # Compute correct signature
        correct_signature = hmac.new(
            self.secret.encode(),
            self.payload,
            hashlib.sha256,
        ).hexdigest()

        # Flip one character in hex (change 'a' to 'b', or '0' to '1')
        sig_list = list(correct_signature)
        if sig_list[0] == 'a':
            sig_list[0] = 'b'
        else:
            sig_list[0] = 'a'
        tampered_signature = ''.join(sig_list)

        with self.assertRaises(InvalidSignatureError):
            verify(
                payload=self.payload,
                secret=self.secret,
                signature=tampered_signature,
                spec=self.spec,
            )

    def test_verify_truncated_signature_rejected(self):
        """One-bit-off signature: truncated signature is rejected."""
        correct_signature = hmac.new(
            self.secret.encode(),
            self.payload,
            hashlib.sha256,
        ).hexdigest()

        # Remove last character
        truncated_signature = correct_signature[:-1]

        with self.assertRaises(InvalidSignatureError):
            verify(
                payload=self.payload,
                secret=self.secret,
                signature=truncated_signature,
                spec=self.spec,
            )

    def test_verify_signature_with_extra_character_rejected(self):
        """One-bit-off signature: signature with extra character is rejected."""
        correct_signature = hmac.new(
            self.secret.encode(),
            self.payload,
            hashlib.sha256,
        ).hexdigest()

        # Add extra character
        padded_signature = correct_signature + "00"

        with self.assertRaises(InvalidSignatureError):
            verify(
                payload=self.payload,
                secret=self.secret,
                signature=padded_signature,
                spec=self.spec,
            )


class TestVerifyWrongSecret(unittest.TestCase):
    """Test cases for wrong secret detection."""

    def setUp(self):
        """Set up common test fixtures."""
        self.payload = b"test webhook payload"
        self.secret = "test-secret-key"
        self.wrong_secret = "wrong-secret-key"
        self.spec = SignatureSpec(
            algorithm="sha256",
            header_name="X-Webhook-Signature",
            encoding="hex",
            timestamp_tolerance_s=300,
        )

    def test_verify_wrong_secret_rejected(self):
        """Wrong secret: signature computed with different secret is rejected."""
        # Compute signature with correct secret
        signature = hmac.new(
            self.secret.encode(),
            self.payload,
            hashlib.sha256,
        ).hexdigest()

        # Attempt to verify with wrong secret
        with self.assertRaises(InvalidSignatureError):
            verify(
                payload=self.payload,
                secret=self.wrong_secret,
                signature=signature,
                spec=self.spec,
            )

    def test_verify_empty_secret_rejected(self):
        """Wrong secret: empty secret produces different signature."""
        # Compute signature with correct secret
        signature = hmac.new(
            self.secret.encode(),
            self.payload,
            hashlib.sha256,
        ).hexdigest()

        # Attempt to verify with empty secret
        with self.assertRaises(InvalidSignatureError):
            verify(
                payload=self.payload,
                secret="",
                signature=signature,
                spec=self.spec,
            )

    def test_verify_case_sensitive_secret(self):
        """Wrong secret: secret comparison is case-sensitive."""
        signature = hmac.new(
            self.secret.encode(),
            self.payload,
            hashlib.sha256,
        ).hexdigest()

        # Try with uppercase version
        with self.assertRaises(InvalidSignatureError):
            verify(
                payload=self.payload,
                secret=self.secret.upper(),
                signature=signature,
                spec=self.spec,
            )


class TestVerifyExpiredTimestamp(unittest.TestCase):
    """Test cases for expired timestamp detection."""

    def setUp(self):
        """Set up common test fixtures."""
        self.payload = b"test webhook payload"
        self.secret = "test-secret-key"
        self.spec = SignatureSpec(
            algorithm="sha256",
            header_name="X-Webhook-Signature",
            encoding="hex",
            timestamp_tolerance_s=300,
        )

    def test_verify_expired_timestamp_rejected(self):
        """Expired timestamp: timestamp beyond tolerance window is rejected."""
        now = 1000000
        timestamp = now - 301  # 301 seconds in the past (beyond 300s tolerance)

        signature = hmac.new(
            self.secret.encode(),
            self.payload,
            hashlib.sha256,
        ).hexdigest()

        with self.assertRaises(ExpiredTimestampError):
            verify(
                payload=self.payload,
                secret=self.secret,
                signature=signature,
                spec=self.spec,
                timestamp=timestamp,
                now=now,
            )

    def test_verify_far_future_timestamp_rejected(self):
        """Expired timestamp: timestamp far in the future is rejected."""
        now = 1000000
        timestamp = now + 1000  # 1000 seconds in the future

        signature = hmac.new(
            self.secret.encode(),
            self.payload,
            hashlib.sha256,
        ).hexdigest()

        with self.assertRaises(ExpiredTimestampError):
            verify(
                payload=self.payload,
                secret=self.secret,
                signature=signature,
                spec=self.spec,
                timestamp=timestamp,
                now=now,
            )

    def test_verify_timestamp_just_beyond_boundary(self):
        """Expired timestamp: timestamp one second beyond boundary is rejected."""
        now = 1000000
        timestamp = now - 301  # One second beyond tolerance

        signature = hmac.new(
            self.secret.encode(),
            self.payload,
            hashlib.sha256,
        ).hexdigest()

        with self.assertRaises(ExpiredTimestampError):
            verify(
                payload=self.payload,
                secret=self.secret,
                signature=signature,
                spec=self.spec,
                timestamp=timestamp,
                now=now,
            )

    def test_verify_zero_tolerance_with_old_timestamp_rejected(self):
        """Expired timestamp: with zero tolerance, any past timestamp is rejected."""
        now = 1000000
        timestamp = now - 1  # Even 1 second in the past

        spec = SignatureSpec(
            algorithm="sha256",
            header_name="X-Webhook-Signature",
            encoding="hex",
            timestamp_tolerance_s=0,
        )

        signature = hmac.new(
            self.secret.encode(),
            self.payload,
            hashlib.sha256,
        ).hexdigest()

        with self.assertRaises(ExpiredTimestampError):
            verify(
                payload=self.payload,
                secret=self.secret,
                signature=signature,
                spec=spec,
                timestamp=timestamp,
                now=now,
            )


class TestVerifyMissingTimestamp(unittest.TestCase):
    """Test cases for missing timestamp when tolerance is set."""

    def setUp(self):
        """Set up common test fixtures."""
        self.payload = b"test webhook payload"
        self.secret = "test-secret-key"
        self.spec = SignatureSpec(
            algorithm="sha256",
            header_name="X-Webhook-Signature",
            encoding="hex",
            timestamp_tolerance_s=300,
        )

    def test_verify_missing_timestamp_with_nonzero_tolerance_rejected(self):
        """Missing timestamp: None timestamp when tolerance > 0 is rejected."""
        signature = hmac.new(
            self.secret.encode(),
            self.payload,
            hashlib.sha256,
        ).hexdigest()

        with self.assertRaises(ExpiredTimestampError):
            verify(
                payload=self.payload,
                secret=self.secret,
                signature=signature,
                spec=self.spec,
                timestamp=None,  # Missing
                now=int(time.time()),
            )

    def test_verify_missing_timestamp_allowed_with_zero_tolerance(self):
        """Missing timestamp: None timestamp is allowed when tolerance is 0."""
        spec = SignatureSpec(
            algorithm="sha256",
            header_name="X-Webhook-Signature",
            encoding="hex",
            timestamp_tolerance_s=0,
        )

        signature = hmac.new(
            self.secret.encode(),
            self.payload,
            hashlib.sha256,
        ).hexdigest()

        result = verify(
            payload=self.payload,
            secret=self.secret,
            signature=signature,
            spec=spec,
            timestamp=None,
        )

        self.assertTrue(result.valid)
        self.assertIsNone(result.timestamp)


class TestVerifyAlgorithmConfusion(unittest.TestCase):
    """Test cases for algorithm confusion attacks."""

    def setUp(self):
        """Set up common test fixtures."""
        self.payload = b"test webhook payload"
        self.secret = "test-secret-key"

    def test_verify_rejects_unsupported_algorithm(self):
        """Algorithm confusion: unsupported algorithm raises ValueError."""
        spec = SignatureSpec(
            algorithm="sha512",  # Not supported, only sha256 allowed
            header_name="X-Webhook-Signature",
            encoding="hex",
            timestamp_tolerance_s=300,
        )

        signature = "dummy_signature"

        with self.assertRaises(ValueError):
            verify(
                payload=self.payload,
                secret=self.secret,
                signature=signature,
                spec=spec,
            )

    def test_verify_rejects_md5_algorithm(self):
        """Algorithm confusion: MD5 (insecure) is rejected."""
        spec = SignatureSpec(
            algorithm="md5",  # Insecure, must reject
            header_name="X-Webhook-Signature",
            encoding="hex",
            timestamp_tolerance_s=300,
        )

        signature = "dummy_signature"

        with self.assertRaises(ValueError):
            verify(
                payload=self.payload,
                secret=self.secret,
                signature=signature,
                spec=spec,
            )

    def test_verify_rejects_unknown_algorithm(self):
        """Algorithm confusion: unknown algorithm raises ValueError."""
        spec = SignatureSpec(
            algorithm="unknown_algo",
            header_name="X-Webhook-Signature",
            encoding="hex",
            timestamp_tolerance_s=300,
        )

        signature = "dummy_signature"

        with self.assertRaises(ValueError):
            verify(
                payload=self.payload,
                secret=self.secret,
                signature=signature,
                spec=spec,
            )


class TestVerifySignatureEncoding(unittest.TestCase):
    """Test cases for different signature encoding formats."""

    def setUp(self):
        """Set up common test fixtures."""
        self.payload = b"test webhook payload"
        self.secret = "test-secret-key"

    def test_verify_rejects_unknown_encoding(self):
        """Unsupported encoding: unknown encoding format raises ValueError."""
        spec = SignatureSpec(
            algorithm="sha256",
            header_name="X-Webhook-Signature",
            encoding="unknown_encoding",
            timestamp_tolerance_s=300,
        )

        signature = "dummy_signature"

        with self.assertRaises(ValueError):
            verify(
                payload=self.payload,
                secret=self.secret,
                signature=signature,
                spec=spec,
            )


class TestVerifyEdgeCases(unittest.TestCase):
    """Test cases for edge cases and boundary conditions."""

    def setUp(self):
        """Set up common test fixtures."""
        self.spec = SignatureSpec(
            algorithm="sha256",
            header_name="X-Webhook-Signature",
            encoding="hex",
            timestamp_tolerance_s=300,
        )

    def test_verify_empty_payload(self):
        """Edge case: empty payload can be signed and verified."""
        payload = b""
        secret = "test-secret"

        signature = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()

        result = verify(
            payload=payload,
            secret=secret,
            signature=signature,
            spec=self.spec,
        )

        self.assertTrue(result.valid)

    def test_verify_large_payload(self):
        """Edge case: large payload is handled correctly."""
        payload = b"x" * 1000000  # 1MB payload
        secret = "test-secret"

        signature = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()

        result = verify(
            payload=payload,
            secret=secret,
            signature=signature,
            spec=self.spec,
        )

        self.assertTrue(result.valid)

    def test_verify_special_characters_in_secret(self):
        """Edge case: secret with special characters is handled correctly."""
        payload = b"test payload"
        secret = "!@#$%^&*()_+-=[]{}|;:,.<>?"

        signature = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()

        result = verify(
            payload=payload,
            secret=secret,
            signature=signature,
            spec=self.spec,
        )

        self.assertTrue(result.valid)

    def test_verify_unicode_secret(self):
        """Edge case: unicode characters in secret are handled."""
        payload = b"test payload"
        secret = "test-secret-你好-мир-🔑"

        signature = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256,
        ).hexdigest()

        result = verify(
            payload=payload,
            secret=secret,
            signature=signature,
            spec=self.spec,
        )

        self.assertTrue(result.valid)

    def test_verify_negative_timestamp_rejected(self):
        """Edge case: negative timestamp (before epoch) is handled."""
        payload = b"test payload"
        secret = "test-secret"
        now = 1000000
        timestamp = -1  # Before epoch

        signature = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()

        with self.assertRaises(ExpiredTimestampError):
            verify(
                payload=payload,
                secret=secret,
                signature=signature,
                spec=self.spec,
                timestamp=timestamp,
                now=now,
            )

    def test_verify_zero_timestamp(self):
        """Edge case: zero timestamp (epoch) is handled."""
        payload = b"test payload"
        secret = "test-secret"
        now = 1000000
        timestamp = 0  # Epoch

        signature = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()

        with self.assertRaises(ExpiredTimestampError):
            verify(
                payload=payload,
                secret=secret,
                signature=signature,
                spec=self.spec,
                timestamp=timestamp,
                now=now,
            )

    def test_verify_provider_name_in_result(self):
        """Edge case: result includes provider name."""
        payload = b"test payload"
        secret = "test-secret"

        signature = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()

        result = verify(
            payload=payload,
            secret=secret,
            signature=signature,
            spec=self.spec,
        )

        self.assertEqual(result.provider, "webhooksig")


class TestVerifyInputValidation(unittest.TestCase):
    """Test cases for input validation and type checking."""

    def setUp(self):
        """Set up common test fixtures."""
        self.payload = b"test payload"
        self.secret = "test-secret"
        self.spec = SignatureSpec(
            algorithm="sha256",
            header_name="X-Webhook-Signature",
            encoding="hex",
            timestamp_tolerance_s=300,
        )

    def test_verify_payload_must_be_bytes(self):
        """Input validation: payload must be bytes."""
        signature = hmac.new(
            self.secret.encode(),
            self.payload,
            hashlib.sha256,
        ).hexdigest()

        # Attempt with string payload
        with self.assertRaises((TypeError, AttributeError)):
            verify(
                payload="not bytes",  # type: ignore
                secret=self.secret,
                signature=signature,
                spec=self.spec,
            )

    def test_verify_secret_must_be_string(self):
        """Input validation: secret must be string."""
        signature = hmac.new(
            self.secret.encode(),
            self.payload,
            hashlib.sha256,
        ).hexdigest()

        # Attempt with bytes secret
        with self.assertRaises((TypeError, AttributeError)):
            verify(
                payload=self.payload,
                secret=b"not a string",  # type: ignore
                signature=signature,
                spec=self.spec,
            )

    def test_verify_signature_must_be_string(self):
        """Input validation: signature must be string."""
        # Attempt with bytes signature
        with self.assertRaises((TypeError, AttributeError)):
            verify(
                payload=self.payload,
                secret=self.secret,
                signature=b"not a string",  # type: ignore
                spec=self.spec,
            )

    def test_verify_spec_must_be_signature_spec(self):
        """Input validation: spec must be SignatureSpec instance."""
        signature = "dummy"

        # Attempt with dict instead of SignatureSpec
        with self.assertRaises((TypeError, AttributeError)):
            verify(
                payload=self.payload,
                secret=self.secret,
                signature=signature,
                spec={"algorithm": "sha256"},  # type: ignore
            )


if __name__ == "__main__":
    unittest.main()
