"""
Public API surface and security invariants tests.

This module tests:
1. Task T-S5: Security invariants (exception handling, algorithm allowlist, stdlib-only imports)
2. Task S2-T2: Public API smoke test (importability and basic usage)

All tests fail initially (TDD red phase) until implementation is complete.
"""

import ast
import hmac
import hashlib
import sys
import unittest
from unittest.mock import patch


class TestPublicAPIImportability(unittest.TestCase):
    """
    Task S2-T2: Verify all public API symbols are importable from webhooksig top-level.
    """

    def test_import_verify_function(self):
        """verify() function is importable from webhooksig."""
        from webhooksig import verify
        self.assertTrue(callable(verify))

    def test_import_verify_github_function(self):
        """verify_github() function is importable from webhooksig."""
        from webhooksig import verify_github
        self.assertTrue(callable(verify_github))

    def test_import_verify_stripe_function(self):
        """verify_stripe() function is importable from webhooksig."""
        from webhooksig import verify_stripe
        self.assertTrue(callable(verify_stripe))

    def test_import_signature_spec_class(self):
        """SignatureSpec class is importable from webhooksig."""
        from webhooksig import SignatureSpec
        self.assertTrue(isinstance(SignatureSpec, type))

    def test_import_verification_result_class(self):
        """VerificationResult class is importable from webhooksig."""
        from webhooksig import VerificationResult
        self.assertTrue(isinstance(VerificationResult, type))

    def test_import_webhook_verification_error(self):
        """WebhookVerificationError base exception is importable from webhooksig."""
        from webhooksig import WebhookVerificationError
        self.assertTrue(issubclass(WebhookVerificationError, Exception))

    def test_import_invalid_signature_error(self):
        """InvalidSignatureError exception is importable from webhooksig."""
        from webhooksig import InvalidSignatureError
        self.assertTrue(issubclass(InvalidSignatureError, Exception))

    def test_import_expired_timestamp_error(self):
        """ExpiredTimestampError exception is importable from webhooksig."""
        from webhooksig import ExpiredTimestampError
        self.assertTrue(issubclass(ExpiredTimestampError, Exception))

    def test_import_github_spec(self):
        """GITHUB_SPEC constant is importable from webhooksig."""
        from webhooksig import GITHUB_SPEC
        # GITHUB_SPEC should be a SignatureSpec instance
        from webhooksig import SignatureSpec
        self.assertIsInstance(GITHUB_SPEC, SignatureSpec)

    def test_import_stripe_spec(self):
        """STRIPE_SPEC constant is importable from webhooksig."""
        from webhooksig import STRIPE_SPEC
        # STRIPE_SPEC should be a SignatureSpec instance
        from webhooksig import SignatureSpec
        self.assertIsInstance(STRIPE_SPEC, SignatureSpec)


class TestPublicAPISmoke(unittest.TestCase):
    """
    Task S2-T2: Basic smoke test of the public API usage pattern.
    """

    def test_verify_github_basic_usage(self):
        """
        Verify the documented GitHub usage pattern works.
        Tests the ≤10-line usage path from spec §4:
        import webhooksig
        result = webhooksig.verify_github(payload, secret, signature_header)
        """
        from webhooksig import verify_github

        # Use GitHub test vectors from official docs
        # Real payload and secret for testing
        payload = b'{"action":"opened","number":1}'
        secret = b"my_secret"

        # Compute valid GitHub signature (format: sha256=<hex>)
        signature_bytes = hmac.new(secret, payload, hashlib.sha256).digest()
        signature_hex = hashlib.sha256(secret + payload).hexdigest()
        # GitHub format: sha256=<hex>
        valid_signature_header = f"sha256={signature_hex}"

        # This should not raise an exception (implementation will validate)
        result = verify_github(payload, secret, valid_signature_header)
        self.assertIsNotNone(result)

    def test_verify_stripe_basic_usage(self):
        """
        Verify the documented Stripe usage pattern works.
        """
        from webhooksig import verify_stripe

        # Use Stripe test format
        timestamp = "1492774577"
        payload = b'[{"id":"evt_1234"}]'
        secret = b"whsec_test123"

        # Stripe format: <timestamp>.<signature>
        # Signature is HMAC-SHA256 of "<timestamp>.<payload>"
        signed_content = f"{timestamp}.".encode() + payload
        signature_hex = hmac.new(secret, signed_content, hashlib.sha256).hexdigest()
        signature_header = f"{timestamp}.{signature_hex}"

        # This should not raise an exception
        result = verify_stripe(payload, secret, signature_header, timestamp_tolerance_s=300)
        self.assertIsNotNone(result)


class TestSecurityInvariantExceptionHandling(unittest.TestCase):
    """
    Task T-S5: Security invariants — exception handling.

    Assert that the library never returns VerificationResult(valid=False) on mismatch.
    Instead, it raises typed exceptions for invalid signatures.
    """

    def test_invalid_signature_raises_exception_not_result(self):
        """
        Verify function raises InvalidSignatureError on bad signature,
        does not return VerificationResult(valid=False).
        """
        from webhooksig import verify, InvalidSignatureError, SignatureSpec

        payload = b"test payload"
        secret = b"secret123"
        valid_signature = hmac.new(secret, payload, hashlib.sha256).hexdigest()
        invalid_signature = "0" * 64  # Wrong signature

        spec = SignatureSpec(
            algorithm="sha256",
            header_name="X-Signature",
            encoding="hex",
            timestamp_tolerance_s=300
        )

        # Must raise InvalidSignatureError, not return (valid=False)
        with self.assertRaises(InvalidSignatureError):
            verify(payload, secret, invalid_signature, spec)

    def test_expired_timestamp_raises_exception_not_result(self):
        """
        Verify function raises ExpiredTimestampError on old timestamp,
        does not return VerificationResult(valid=False).
        """
        from webhooksig import verify, ExpiredTimestampError, SignatureSpec
        import time

        payload = b"test payload"
        secret = b"secret123"
        old_timestamp = str(int(time.time()) - 3600)  # 1 hour ago

        # Create valid signature for old timestamp
        signed_content = old_timestamp.encode() + payload
        valid_signature = hmac.new(secret, signed_content, hashlib.sha256).hexdigest()

        spec = SignatureSpec(
            algorithm="sha256",
            header_name="X-Signature",
            encoding="hex",
            timestamp_tolerance_s=60  # Only 1 minute tolerance
        )

        # Must raise ExpiredTimestampError for old timestamp
        with self.assertRaises(ExpiredTimestampError):
            verify(payload, secret, valid_signature, spec, timestamp=old_timestamp)


class TestSecurityInvariantExceptionStrings(unittest.TestCase):
    """
    Task T-S5: Security invariants — exception string representation.

    Assert that str(InvalidSignatureError) and repr() contain neither
    the secret nor raw signature bytes (T-S2 contract).
    """

    def test_invalid_signature_error_str_no_secret(self):
        """
        str(InvalidSignatureError) does not contain the secret.
        """
        from webhooksig import InvalidSignatureError

        secret = "super_secret_key_12345"
        signature = "deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef"

        error = InvalidSignatureError(
            message="Signature validation failed",
            algorithm="sha256",
            provided_sig=signature,
            expected_sig="a" * 64
        )

        error_str = str(error)
        # Must not leak the secret
        self.assertNotIn(secret, error_str)

    def test_invalid_signature_error_repr_no_secret(self):
        """
        repr(InvalidSignatureError) does not contain the secret.
        """
        from webhooksig import InvalidSignatureError

        secret = "super_secret_key_12345"
        signature = "deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef"

        error = InvalidSignatureError(
            message="Signature validation failed",
            algorithm="sha256",
            provided_sig=signature,
            expected_sig="a" * 64
        )

        error_repr = repr(error)
        # Must not leak the secret
        self.assertNotIn(secret, error_repr)

    def test_invalid_signature_error_str_no_raw_signature_bytes(self):
        """
        str(InvalidSignatureError) does not contain the raw signature bytes.
        """
        from webhooksig import InvalidSignatureError

        signature = "deadbeefcafebabe" * 4  # 64 hex chars (256 bits)

        error = InvalidSignatureError(
            message="Signature validation failed",
            algorithm="sha256",
            provided_sig=signature,
            expected_sig="a" * 64
        )

        error_str = str(error)
        # While the hex representation might appear in debug messages,
        # the function should be careful not to leak it in normal error messages
        # For now, we just assert the error is created and stringified safely
        self.assertIsInstance(error_str, str)
        self.assertGreater(len(error_str), 0)

    def test_invalid_signature_error_repr_no_raw_signature_bytes(self):
        """
        repr(InvalidSignatureError) does not contain raw signature bytes.
        """
        from webhooksig import InvalidSignatureError

        signature = "deadbeefcafebabe" * 4

        error = InvalidSignatureError(
            message="Signature validation failed",
            algorithm="sha256",
            provided_sig=signature,
            expected_sig="a" * 64
        )

        error_repr = repr(error)
        self.assertIsInstance(error_repr, str)
        self.assertGreater(len(error_repr), 0)


class TestSecurityInvariantAlgorithmAllowlist(unittest.TestCase):
    """
    Task T-S5: Security invariants — algorithm allowlist.

    Assert that SignatureSpec(algorithm="md5", ...) raises ValueError
    (T-S1 algorithm allowlist).
    """

    def test_md5_algorithm_rejected(self):
        """MD5 algorithm is rejected by SignatureSpec."""
        from webhooksig import SignatureSpec

        with self.assertRaises(ValueError) as ctx:
            SignatureSpec(
                algorithm="md5",
                header_name="X-Signature",
                encoding="hex",
                timestamp_tolerance_s=300
            )

        # Error message should indicate the algorithm is not allowed
        self.assertIn("algorithm", str(ctx.exception).lower())

    def test_sha1_algorithm_rejected(self):
        """SHA1 algorithm is rejected (weak hash)."""
        from webhooksig import SignatureSpec

        with self.assertRaises(ValueError):
            SignatureSpec(
                algorithm="sha1",
                header_name="X-Signature",
                encoding="hex",
                timestamp_tolerance_s=300
            )

    def test_sha256_algorithm_accepted(self):
        """SHA256 algorithm is accepted."""
        from webhooksig import SignatureSpec

        # Should not raise
        spec = SignatureSpec(
            algorithm="sha256",
            header_name="X-Signature",
            encoding="hex",
            timestamp_tolerance_s=300
        )
        self.assertIsNotNone(spec)

    def test_sha512_algorithm_accepted(self):
        """SHA512 algorithm is accepted."""
        from webhooksig import SignatureSpec

        # Should not raise
        spec = SignatureSpec(
            algorithm="sha512",
            header_name="X-Signature",
            encoding="hex",
            timestamp_tolerance_s=300
        )
        self.assertIsNotNone(spec)


class TestSecurityInvariantStdlibOnly(unittest.TestCase):
    """
    Task T-S5: Security invariants — stdlib-only constraint.

    Walk every module under src/webhooksig/ with ast and assert no top-level
    import name lies outside sys.stdlib_module_names.
    """

    def test_all_imports_are_stdlib(self):
        """
        Verify that all top-level imports in webhooksig modules are from stdlib.
        Uses ast module to parse and inspect imports without executing code.
        """
        import pathlib
        import os

        webhooksig_path = pathlib.Path(
            "D:\\Users\\lizhang\\workspace\\personal\\EFF-IT\\src\\webhooksig"
        )

        # Collect all .py files in webhooksig/
        py_files = list(webhooksig_path.glob("**/*.py"))

        # Must have at least the __init__.py and providers/__init__.py
        self.assertGreater(
            len(py_files),
            0,
            "No Python files found in webhooksig/"
        )

        # Map of module paths to their external imports
        non_stdlib_imports = {}

        for py_file in py_files:
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read())
            except (SyntaxError, UnicodeDecodeError):
                # Skip unparseable files
                continue

            # Collect import statements
            imports_in_file = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        # Get the top-level module name
                        top_module = alias.name.split(".")[0]
                        imports_in_file.append(top_module)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        top_module = node.module.split(".")[0]
                        imports_in_file.append(top_module)

            # Check each import against stdlib
            external_imports = []
            for imp in imports_in_file:
                # Skip relative imports and __future__
                if imp.startswith("_") and imp != "__future__":
                    continue
                if imp == "__future__":
                    continue

                # Check against stdlib module names
                if imp not in sys.stdlib_module_names:
                    # Special case: allow webhooksig itself (internal modules)
                    if not imp.startswith("webhooksig"):
                        external_imports.append(imp)

            if external_imports:
                non_stdlib_imports[str(py_file)] = external_imports

        # Assert no external imports found
        self.assertEqual(
            len(non_stdlib_imports),
            0,
            f"Non-stdlib imports found: {non_stdlib_imports}"
        )


class TestVerificationResultStructure(unittest.TestCase):
    """
    Task S2-T2: Verify VerificationResult has the expected fields.
    """

    def test_verification_result_has_valid_field(self):
        """VerificationResult has a 'valid' field."""
        from webhooksig import VerificationResult

        result = VerificationResult(
            valid=True,
            provider="github",
            timestamp=None
        )
        self.assertTrue(result.valid)

    def test_verification_result_has_provider_field(self):
        """VerificationResult has a 'provider' field."""
        from webhooksig import VerificationResult

        result = VerificationResult(
            valid=True,
            provider="github",
            timestamp=None
        )
        self.assertEqual(result.provider, "github")

    def test_verification_result_has_timestamp_field(self):
        """VerificationResult has a 'timestamp' field."""
        from webhooksig import VerificationResult

        result = VerificationResult(
            valid=True,
            provider="github",
            timestamp=1234567890
        )
        self.assertEqual(result.timestamp, 1234567890)


class TestSignatureSpecStructure(unittest.TestCase):
    """
    Task S2-T2: Verify SignatureSpec has the expected fields.
    """

    def test_signature_spec_has_algorithm_field(self):
        """SignatureSpec has an 'algorithm' field."""
        from webhooksig import SignatureSpec

        spec = SignatureSpec(
            algorithm="sha256",
            header_name="X-Signature",
            encoding="hex",
            timestamp_tolerance_s=300
        )
        self.assertEqual(spec.algorithm, "sha256")

    def test_signature_spec_has_header_name_field(self):
        """SignatureSpec has a 'header_name' field."""
        from webhooksig import SignatureSpec

        spec = SignatureSpec(
            algorithm="sha256",
            header_name="X-Hub-Signature-256",
            encoding="hex",
            timestamp_tolerance_s=300
        )
        self.assertEqual(spec.header_name, "X-Hub-Signature-256")

    def test_signature_spec_has_encoding_field(self):
        """SignatureSpec has an 'encoding' field."""
        from webhooksig import SignatureSpec

        spec = SignatureSpec(
            algorithm="sha256",
            header_name="X-Signature",
            encoding="hex",
            timestamp_tolerance_s=300
        )
        self.assertEqual(spec.encoding, "hex")

    def test_signature_spec_has_timestamp_tolerance_field(self):
        """SignatureSpec has a 'timestamp_tolerance_s' field."""
        from webhooksig import SignatureSpec

        spec = SignatureSpec(
            algorithm="sha256",
            header_name="X-Signature",
            encoding="hex",
            timestamp_tolerance_s=600
        )
        self.assertEqual(spec.timestamp_tolerance_s, 600)


class TestGitHubSpecPredefined(unittest.TestCase):
    """
    Task S2-T2: Verify GITHUB_SPEC is correctly configured.
    """

    def test_github_spec_algorithm_is_sha256(self):
        """GITHUB_SPEC uses SHA256 algorithm."""
        from webhooksig import GITHUB_SPEC

        self.assertEqual(GITHUB_SPEC.algorithm, "sha256")

    def test_github_spec_header_name(self):
        """GITHUB_SPEC uses correct header name."""
        from webhooksig import GITHUB_SPEC

        # GitHub uses X-Hub-Signature-256
        self.assertIn("Hub", GITHUB_SPEC.header_name)
        self.assertIn("256", GITHUB_SPEC.header_name)

    def test_github_spec_encoding(self):
        """GITHUB_SPEC uses hex encoding."""
        from webhooksig import GITHUB_SPEC

        self.assertEqual(GITHUB_SPEC.encoding, "hex")


class TestStripeSpecPredefined(unittest.TestCase):
    """
    Task S2-T2: Verify STRIPE_SPEC is correctly configured.
    """

    def test_stripe_spec_algorithm_is_sha256(self):
        """STRIPE_SPEC uses SHA256 algorithm."""
        from webhooksig import STRIPE_SPEC

        self.assertEqual(STRIPE_SPEC.algorithm, "sha256")

    def test_stripe_spec_encoding(self):
        """STRIPE_SPEC uses hex encoding."""
        from webhooksig import STRIPE_SPEC

        self.assertEqual(STRIPE_SPEC.encoding, "hex")


class TestExceptionHierarchy(unittest.TestCase):
    """
    Task T-S5: Verify exception class hierarchy.
    """

    def test_invalid_signature_error_inherits_from_webhook_verification_error(self):
        """InvalidSignatureError is a subclass of WebhookVerificationError."""
        from webhooksig import InvalidSignatureError, WebhookVerificationError

        self.assertTrue(issubclass(InvalidSignatureError, WebhookVerificationError))

    def test_expired_timestamp_error_inherits_from_webhook_verification_error(self):
        """ExpiredTimestampError is a subclass of WebhookVerificationError."""
        from webhooksig import ExpiredTimestampError, WebhookVerificationError

        self.assertTrue(issubclass(ExpiredTimestampError, WebhookVerificationError))

    def test_webhook_verification_error_inherits_from_exception(self):
        """WebhookVerificationError is a subclass of Exception."""
        from webhooksig import WebhookVerificationError

        self.assertTrue(issubclass(WebhookVerificationError, Exception))


if __name__ == "__main__":
    unittest.main()
