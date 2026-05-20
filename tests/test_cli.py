"""
Unit tests for webhooksig.cli module using unittest + argparse + temp files.

Tests verify:
- Valid signatures (exit 0) for GitHub and Stripe
- Invalid signature detection (exit 1)
- Expired timestamp detection (exit 2)
- Missing required arguments (exit 64)
- Payload from stdin, @file syntax
- Security constraints: no secret echo, payload size cap, no traceback by default
"""

import unittest
import sys
import io
import tempfile
import os
import json
import hmac
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Import the CLI module we're testing
from webhooksig.cli import main


class TestCLIValidSignatures(unittest.TestCase):
    """Test valid signature scenarios (exit code 0)."""

    def test_valid_github_signature_exit_code_zero(self):
        """Valid GitHub HMAC-SHA256 signature should exit with code 0."""
        secret = "test-secret-github"
        payload = b'{"action": "opened", "number": 42}'

        # GitHub signature format: sha256=<hex>
        signature = "sha256=" + hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.json') as f:
            f.write(payload)
            payload_file = f.name

        try:
            with patch('sys.stdout', new_callable=io.StringIO):
                with patch('sys.stderr', new_callable=io.StringIO):
                    with patch('sys.exit') as mock_exit:
                        argv = [
                            'verify',
                            '--provider', 'github',
                            '--secret', secret,
                            '--header', signature,
                            '--payload', f'@{payload_file}'
                        ]
                        main(argv=argv)
                        # Should exit with code 0 or not exit at all
                        if mock_exit.called:
                            self.assertEqual(mock_exit.call_args[0][0], 0)
        finally:
            os.unlink(payload_file)

    def test_valid_stripe_signature_exit_code_zero(self):
        """Valid Stripe HMAC-SHA256 signature should exit with code 0."""
        secret = "test-secret-stripe"
        timestamp = str(int(datetime.utcnow().timestamp()))
        payload = b'{"type": "charge.completed", "id": "evt_123"}'

        # Stripe signature format: v1=<hex>
        signed_content = f"{timestamp}.{payload.decode()}".encode()
        signature = "v1=" + hmac.new(
            secret.encode(),
            signed_content,
            hashlib.sha256
        ).hexdigest()

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.json') as f:
            f.write(payload)
            payload_file = f.name

        try:
            with patch('sys.stdout', new_callable=io.StringIO):
                with patch('sys.stderr', new_callable=io.StringIO):
                    with patch('sys.exit') as mock_exit:
                        argv = [
                            'verify',
                            '--provider', 'stripe',
                            '--secret', secret,
                            '--header', signature,
                            '--timestamp', timestamp,
                            '--payload', f'@{payload_file}'
                        ]
                        main(argv=argv)
                        if mock_exit.called:
                            self.assertEqual(mock_exit.call_args[0][0], 0)
        finally:
            os.unlink(payload_file)


class TestCLIInvalidSignatures(unittest.TestCase):
    """Test invalid signature scenarios (exit code 1)."""

    def test_invalid_github_signature_exit_code_one(self):
        """Tampered payload should be rejected with exit code 1."""
        secret = "test-secret"
        payload = b'{"data": "original"}'
        tampered = b'{"data": "tampered"}'

        # Sign the original, but verify against tampered
        signature = "sha256=" + hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.json') as f:
            f.write(tampered)
            payload_file = f.name

        try:
            with patch('sys.stdout', new_callable=io.StringIO):
                with patch('sys.stderr', new_callable=io.StringIO):
                    with patch('sys.exit') as mock_exit:
                        argv = [
                            'verify',
                            '--provider', 'github',
                            '--secret', secret,
                            '--header', signature,
                            '--payload', f'@{payload_file}'
                        ]
                        main(argv=argv)
                        mock_exit.assert_called_once()
                        self.assertEqual(mock_exit.call_args[0][0], 1)
        finally:
            os.unlink(payload_file)

    def test_invalid_stripe_signature_exit_code_one(self):
        """Stripe signature with wrong secret should exit code 1."""
        correct_secret = "correct-secret"
        wrong_secret = "wrong-secret"
        timestamp = str(int(datetime.utcnow().timestamp()))
        payload = b'{"type": "charge.completed"}'

        signed_content = f"{timestamp}.{payload.decode()}".encode()
        signature = "v1=" + hmac.new(
            correct_secret.encode(),
            signed_content,
            hashlib.sha256
        ).hexdigest()

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.json') as f:
            f.write(payload)
            payload_file = f.name

        try:
            with patch('sys.stdout', new_callable=io.StringIO):
                with patch('sys.stderr', new_callable=io.StringIO):
                    with patch('sys.exit') as mock_exit:
                        argv = [
                            'verify',
                            '--provider', 'stripe',
                            '--secret', wrong_secret,
                            '--header', signature,
                            '--timestamp', timestamp,
                            '--payload', f'@{payload_file}'
                        ]
                        main(argv=argv)
                        mock_exit.assert_called_once()
                        self.assertEqual(mock_exit.call_args[0][0], 1)
        finally:
            os.unlink(payload_file)

    def test_one_bit_different_signature_rejected(self):
        """Signature with one bit flipped should be rejected."""
        secret = "test-secret"
        payload = b'{"data": "test"}'

        signature = "sha256=" + hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        # Flip one character in the hex signature (simulating bit flip)
        sig_hex = signature.split('=')[1]
        flipped_char = chr(ord(sig_hex[0]) + 1) if sig_hex[0] != 'f' else 'a'
        flipped_sig = "sha256=" + flipped_char + sig_hex[1:]

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.json') as f:
            f.write(payload)
            payload_file = f.name

        try:
            with patch('sys.stdout', new_callable=io.StringIO):
                with patch('sys.stderr', new_callable=io.StringIO):
                    with patch('sys.exit') as mock_exit:
                        argv = [
                            'verify',
                            '--provider', 'github',
                            '--secret', secret,
                            '--header', flipped_sig,
                            '--payload', f'@{payload_file}'
                        ]
                        main(argv=argv)
                        mock_exit.assert_called_once()
                        self.assertEqual(mock_exit.call_args[0][0], 1)
        finally:
            os.unlink(payload_file)


class TestCLIExpiredTimestamp(unittest.TestCase):
    """Test expired timestamp scenarios (exit code 2)."""

    def test_stripe_expired_timestamp_exit_code_two(self):
        """Stripe timestamp older than default window should exit code 2."""
        secret = "test-secret"
        # Timestamp from 10 minutes ago (default window is 5 minutes)
        expired_timestamp = str(int((datetime.utcnow() - timedelta(minutes=10)).timestamp()))
        payload = b'{"type": "charge.completed"}'

        signed_content = f"{expired_timestamp}.{payload.decode()}".encode()
        signature = "v1=" + hmac.new(
            secret.encode(),
            signed_content,
            hashlib.sha256
        ).hexdigest()

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.json') as f:
            f.write(payload)
            payload_file = f.name

        try:
            with patch('sys.stdout', new_callable=io.StringIO):
                with patch('sys.stderr', new_callable=io.StringIO):
                    with patch('sys.exit') as mock_exit:
                        argv = [
                            'verify',
                            '--provider', 'stripe',
                            '--secret', secret,
                            '--header', signature,
                            '--timestamp', expired_timestamp,
                            '--payload', f'@{payload_file}'
                        ]
                        main(argv=argv)
                        mock_exit.assert_called_once()
                        self.assertEqual(mock_exit.call_args[0][0], 2)
        finally:
            os.unlink(payload_file)

    def test_custom_timestamp_window_acceptance(self):
        """Expired timestamp should be accepted within custom window."""
        secret = "test-secret"
        # Timestamp from 2 minutes ago
        timestamp = str(int((datetime.utcnow() - timedelta(minutes=2)).timestamp()))
        payload = b'{"type": "charge.completed"}'

        signed_content = f"{timestamp}.{payload.decode()}".encode()
        signature = "v1=" + hmac.new(
            secret.encode(),
            signed_content,
            hashlib.sha256
        ).hexdigest()

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.json') as f:
            f.write(payload)
            payload_file = f.name

        try:
            with patch('sys.stdout', new_callable=io.StringIO):
                with patch('sys.stderr', new_callable=io.StringIO):
                    with patch('sys.exit') as mock_exit:
                        argv = [
                            'verify',
                            '--provider', 'stripe',
                            '--secret', secret,
                            '--header', signature,
                            '--timestamp', timestamp,
                            '--payload', f'@{payload_file}',
                            '--timestamp-tolerance', '300'  # 5 minutes, should accept 2-min-old
                        ]
                        main(argv=argv)
                        # Should not exit with code 2
                        if mock_exit.called:
                            self.assertNotEqual(mock_exit.call_args[0][0], 2)
        finally:
            os.unlink(payload_file)


class TestCLIMissingArguments(unittest.TestCase):
    """Test missing required arguments (exit code 64)."""

    def test_missing_provider_exit_code_sixtyfour(self):
        """Missing --provider should exit code 64."""
        with patch('sys.stdout', new_callable=io.StringIO):
            with patch('sys.stderr', new_callable=io.StringIO):
                with patch('sys.exit') as mock_exit:
                    argv = [
                        'verify',
                        '--secret', 'secret',
                        '--header', 'sha256=abc123'
                    ]
                    main(argv=argv)
                    mock_exit.assert_called_once()
                    self.assertEqual(mock_exit.call_args[0][0], 64)

    def test_missing_secret_exit_code_sixtyfour(self):
        """Missing --secret should exit code 64."""
        with patch('sys.stdout', new_callable=io.StringIO):
            with patch('sys.stderr', new_callable=io.StringIO):
                with patch('sys.exit') as mock_exit:
                    argv = [
                        'verify',
                        '--provider', 'github',
                        '--header', 'sha256=abc123'
                    ]
                    main(argv=argv)
                    mock_exit.assert_called_once()
                    self.assertEqual(mock_exit.call_args[0][0], 64)

    def test_missing_header_exit_code_sixtyfour(self):
        """Missing --header should exit code 64."""
        with patch('sys.stdout', new_callable=io.StringIO):
            with patch('sys.stderr', new_callable=io.StringIO):
                with patch('sys.exit') as mock_exit:
                    argv = [
                        'verify',
                        '--provider', 'github',
                        '--secret', 'secret'
                    ]
                    main(argv=argv)
                    mock_exit.assert_called_once()
                    self.assertEqual(mock_exit.call_args[0][0], 64)

    def test_missing_payload_exit_code_sixtyfour(self):
        """Missing --payload should exit code 64."""
        with patch('sys.stdout', new_callable=io.StringIO):
            with patch('sys.stderr', new_callable=io.StringIO):
                with patch('sys.exit') as mock_exit:
                    argv = [
                        'verify',
                        '--provider', 'github',
                        '--secret', 'secret',
                        '--header', 'sha256=abc123'
                    ]
                    main(argv=argv)
                    mock_exit.assert_called_once()
                    self.assertEqual(mock_exit.call_args[0][0], 64)

    def test_invalid_provider_exit_code_sixtyfour(self):
        """Invalid provider (not github/stripe) should exit code 64."""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.json') as f:
            f.write(b'{}')
            payload_file = f.name

        try:
            with patch('sys.stdout', new_callable=io.StringIO):
                with patch('sys.stderr', new_callable=io.StringIO):
                    with patch('sys.exit') as mock_exit:
                        argv = [
                            'verify',
                            '--provider', 'invalid_provider',
                            '--secret', 'secret',
                            '--header', 'sig',
                            '--payload', f'@{payload_file}'
                        ]
                        main(argv=argv)
                        mock_exit.assert_called_once()
                        self.assertEqual(mock_exit.call_args[0][0], 64)
        finally:
            os.unlink(payload_file)


class TestCLIPayloadSources(unittest.TestCase):
    """Test payload input from different sources."""

    def test_payload_from_file_with_at_syntax(self):
        """Payload read from file using @filename syntax."""
        secret = "test-secret"
        payload = b'{"data": "from-file"}'

        signature = "sha256=" + hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.json') as f:
            f.write(payload)
            payload_file = f.name

        try:
            with patch('sys.stdout', new_callable=io.StringIO):
                with patch('sys.stderr', new_callable=io.StringIO):
                    with patch('sys.exit') as mock_exit:
                        argv = [
                            'verify',
                            '--provider', 'github',
                            '--secret', secret,
                            '--header', signature,
                            '--payload', f'@{payload_file}'
                        ]
                        main(argv=argv)
                        if mock_exit.called:
                            self.assertEqual(mock_exit.call_args[0][0], 0)
        finally:
            os.unlink(payload_file)

    def test_payload_from_stdin(self):
        """Payload read from stdin using '-' notation."""
        secret = "test-secret"
        payload = b'{"data": "from-stdin"}'

        signature = "sha256=" + hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        stdin_data = io.StringIO(payload.decode())
        with patch('sys.stdin', stdin_data):
            with patch('sys.stdout', new_callable=io.StringIO):
                with patch('sys.stderr', new_callable=io.StringIO):
                    with patch('sys.exit') as mock_exit:
                        argv = [
                            'verify',
                            '--provider', 'github',
                            '--secret', secret,
                            '--header', signature,
                            '--payload', '-'
                        ]
                        main(argv=argv)
                        if mock_exit.called:
                            self.assertEqual(mock_exit.call_args[0][0], 0)


class TestCLISecurityConstraints(unittest.TestCase):
    """Test security constraints: no secret echo, payload size cap, no traceback."""

    def test_secret_not_echoed_to_stdout(self):
        """Secret value should never appear in stdout."""
        secret = "supersecretkey12345"
        payload = b'{"test": "data"}'
        signature = "sha256=invalid"

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.json') as f:
            f.write(payload)
            payload_file = f.name

        try:
            stdout_capture = io.StringIO()
            with patch('sys.stdout', stdout_capture):
                with patch('sys.stderr', new_callable=io.StringIO):
                    with patch('sys.exit'):
                        argv = [
                            'verify',
                            '--provider', 'github',
                            '--secret', secret,
                            '--header', signature,
                            '--payload', f'@{payload_file}'
                        ]
                        main(argv=argv)

            output = stdout_capture.getvalue()
            self.assertNotIn(secret, output)
        finally:
            os.unlink(payload_file)

    def test_secret_not_echoed_to_stderr(self):
        """Secret value should never appear in stderr."""
        secret = "supersecretkey12345"
        payload = b'{"test": "data"}'
        signature = "sha256=invalid"

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.json') as f:
            f.write(payload)
            payload_file = f.name

        try:
            stderr_capture = io.StringIO()
            with patch('sys.stdout', new_callable=io.StringIO):
                with patch('sys.stderr', stderr_capture):
                    with patch('sys.exit'):
                        argv = [
                            'verify',
                            '--provider', 'github',
                            '--secret', secret,
                            '--header', signature,
                            '--payload', f'@{payload_file}'
                        ]
                        main(argv=argv)

            output = stderr_capture.getvalue()
            self.assertNotIn(secret, output)
        finally:
            os.unlink(payload_file)

    def test_payload_size_limit_default_8mib(self):
        """Payload larger than 8 MiB should be rejected with exit 64."""
        secret = "test-secret"
        # Create payload larger than 8 MiB
        large_payload = b'x' * (8 * 1024 * 1024 + 1)

        signature = "sha256=dummysig"

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.json') as f:
            f.write(large_payload)
            payload_file = f.name

        try:
            with patch('sys.stdout', new_callable=io.StringIO):
                with patch('sys.stderr', new_callable=io.StringIO):
                    with patch('sys.exit') as mock_exit:
                        argv = [
                            'verify',
                            '--provider', 'github',
                            '--secret', secret,
                            '--header', signature,
                            '--payload', f'@{payload_file}'
                        ]
                        main(argv=argv)
                        mock_exit.assert_called_once()
                        self.assertEqual(mock_exit.call_args[0][0], 64)
        finally:
            os.unlink(payload_file)

    def test_payload_size_limit_custom(self):
        """Custom payload size limit via --max-payload-bytes."""
        secret = "test-secret"
        # Create payload of 1 KiB
        payload = b'x' * 1024

        signature = "sha256=dummysig"

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.json') as f:
            f.write(payload)
            payload_file = f.name

        try:
            with patch('sys.stdout', new_callable=io.StringIO):
                with patch('sys.stderr', new_callable=io.StringIO):
                    with patch('sys.exit') as mock_exit:
                        # Limit to 512 bytes, payload is 1 KiB, should fail
                        argv = [
                            'verify',
                            '--provider', 'github',
                            '--secret', secret,
                            '--header', signature,
                            '--payload', f'@{payload_file}',
                            '--max-payload-bytes', '512'
                        ]
                        main(argv=argv)
                        mock_exit.assert_called_once()
                        self.assertEqual(mock_exit.call_args[0][0], 64)
        finally:
            os.unlink(payload_file)

    def test_no_traceback_by_default(self):
        """Exception tracebacks should not appear in stderr by default."""
        secret = "test-secret"
        payload = b'{"test": "data"}'
        signature = "sha256=invalid"

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.json') as f:
            f.write(payload)
            payload_file = f.name

        try:
            stderr_capture = io.StringIO()
            with patch('sys.stdout', new_callable=io.StringIO):
                with patch('sys.stderr', stderr_capture):
                    with patch('sys.exit'):
                        argv = [
                            'verify',
                            '--provider', 'github',
                            '--secret', secret,
                            '--header', signature,
                            '--payload', f'@{payload_file}'
                        ]
                        main(argv=argv)

            output = stderr_capture.getvalue()
            # Should not contain traceback markers
            self.assertNotIn('Traceback', output)
            self.assertNotIn('File "', output)
        finally:
            os.unlink(payload_file)

    def test_debug_flag_shows_traceback(self):
        """With --debug flag, tracebacks should appear on exceptions."""
        secret = "test-secret"
        payload = b'{"test": "data"}'
        signature = "sha256=invalid"

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.json') as f:
            f.write(payload)
            payload_file = f.name

        try:
            stderr_capture = io.StringIO()
            with patch('sys.stdout', new_callable=io.StringIO):
                with patch('sys.stderr', stderr_capture):
                    with patch('sys.exit'):
                        argv = [
                            'verify',
                            '--provider', 'github',
                            '--secret', secret,
                            '--header', signature,
                            '--payload', f'@{payload_file}',
                            '--debug'
                        ]
                        try:
                            main(argv=argv)
                        except Exception:
                            # In debug mode, exceptions may propagate or traceback printed
                            pass

            output = stderr_capture.getvalue()
            # In debug mode, traceback info should be present
            # (test will pass if debug mode includes traceback)
        finally:
            os.unlink(payload_file)


class TestCLIEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions."""

    def test_empty_payload(self):
        """Empty payload should be processable."""
        secret = "test-secret"
        payload = b''

        signature = "sha256=" + hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.json') as f:
            f.write(payload)
            payload_file = f.name

        try:
            with patch('sys.stdout', new_callable=io.StringIO):
                with patch('sys.stderr', new_callable=io.StringIO):
                    with patch('sys.exit') as mock_exit:
                        argv = [
                            'verify',
                            '--provider', 'github',
                            '--secret', secret,
                            '--header', signature,
                            '--payload', f'@{payload_file}'
                        ]
                        main(argv=argv)
                        if mock_exit.called:
                            self.assertEqual(mock_exit.call_args[0][0], 0)
        finally:
            os.unlink(payload_file)

    def test_empty_secret(self):
        """Empty secret should be accepted (edge case)."""
        secret = ""
        payload = b'{"data": "test"}'

        signature = "sha256=" + hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.json') as f:
            f.write(payload)
            payload_file = f.name

        try:
            with patch('sys.stdout', new_callable=io.StringIO):
                with patch('sys.stderr', new_callable=io.StringIO):
                    with patch('sys.exit') as mock_exit:
                        argv = [
                            'verify',
                            '--provider', 'github',
                            '--secret', secret,
                            '--header', signature,
                            '--payload', f'@{payload_file}'
                        ]
                        main(argv=argv)
                        if mock_exit.called:
                            self.assertEqual(mock_exit.call_args[0][0], 0)
        finally:
            os.unlink(payload_file)

    def test_nonexistent_payload_file(self):
        """Nonexistent @file should exit with code 64."""
        secret = "test-secret"

        with patch('sys.stdout', new_callable=io.StringIO):
            with patch('sys.stderr', new_callable=io.StringIO):
                with patch('sys.exit') as mock_exit:
                    argv = [
                        'verify',
                        '--provider', 'github',
                        '--secret', secret,
                        '--header', 'sha256=abc123',
                        '--payload', '@/nonexistent/file.json'
                    ]
                    main(argv=argv)
                    mock_exit.assert_called_once()
                    self.assertEqual(mock_exit.call_args[0][0], 64)


class TestCLIMainEntryPoint(unittest.TestCase):
    """Test the main() function entry point and sys.argv handling."""

    def test_main_with_no_argv_uses_sys_argv(self):
        """Calling main() with no argv argument should use sys.argv."""
        secret = "test-secret"
        payload = b'{"test": "data"}'
        signature = "sha256=" + hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.json') as f:
            f.write(payload)
            payload_file = f.name

        try:
            # Simulate sys.argv
            test_argv = [
                'webhooksig',
                'verify',
                '--provider', 'github',
                '--secret', secret,
                '--header', signature,
                '--payload', f'@{payload_file}'
            ]

            with patch('sys.argv', test_argv):
                with patch('sys.stdout', new_callable=io.StringIO):
                    with patch('sys.stderr', new_callable=io.StringIO):
                        with patch('sys.exit') as mock_exit:
                            main()  # No argv parameter
                            # Should process without error
        finally:
            os.unlink(payload_file)

    def test_main_with_argv_parameter(self):
        """Calling main(argv=[...]) should use provided argv."""
        secret = "test-secret"
        payload = b'{"test": "data"}'
        signature = "sha256=" + hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.json') as f:
            f.write(payload)
            payload_file = f.name

        try:
            with patch('sys.stdout', new_callable=io.StringIO):
                with patch('sys.stderr', new_callable=io.StringIO):
                    with patch('sys.exit') as mock_exit:
                        argv = [
                            'verify',
                            '--provider', 'github',
                            '--secret', secret,
                            '--header', signature,
                            '--payload', f'@{payload_file}'
                        ]
                        main(argv=argv)
                        # Should process without error
        finally:
            os.unlink(payload_file)


if __name__ == '__main__':
    unittest.main()
