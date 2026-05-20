"""
Webhook signature verification CLI.

Verifies incoming webhook signatures against a shared secret.
Supports GitHub and Stripe HMAC-SHA256 signatures.

Usage:
    webhooksig verify --provider {github,stripe} --secret <s> --header <sig> \
        [--timestamp <ts>] [--payload @file|-] [--max-payload-bytes <n>] [--debug]

Exit codes:
    0: Valid signature
    1: InvalidSignatureError
    2: ExpiredTimestampError
    64: Usage error (missing args, invalid payload, etc.)
"""

import argparse
import sys
import traceback

from webhooksig.providers.github import verify_github
from webhooksig.providers.stripe import verify_stripe
from webhooksig.types import ExpiredTimestampError, InvalidSignatureError, WebhookVerificationError

_DEFAULT_MAX_PAYLOAD_BYTES = 8 * 1024 * 1024  # 8 MiB
_CHUNK_SIZE = 65536  # 64 KiB read chunks


def _build_parser() -> argparse.ArgumentParser:
    # exit_on_error=False makes argparse raise ArgumentError instead of calling
    # error()/sys.exit(), giving us a single, clean place to handle parse failures.
    parser = argparse.ArgumentParser(
        prog="webhooksig",
        description="Verify HMAC-SHA256 webhook signatures.",
        exit_on_error=False,
    )
    subparsers = parser.add_subparsers(dest="subcommand")

    verify_parser = subparsers.add_parser(
        "verify",
        help="Verify a webhook signature.",
        exit_on_error=False,
    )
    verify_parser.add_argument(
        "--provider",
        required=True,
        choices=["github", "stripe"],
        help="Webhook provider.",
    )
    verify_parser.add_argument(
        "--secret",
        required=True,
        metavar="SECRET",
        help="Shared webhook secret.",
    )
    verify_parser.add_argument(
        "--header",
        required=True,
        help="Full raw signature header value.",
    )
    verify_parser.add_argument(
        "--timestamp",
        type=int,
        default=None,
        help="Optional Unix epoch timestamp. For GitHub: passed to verify_github. "
             "For Stripe: prepended to header as 't=<ts>,' when header lacks it.",
    )
    verify_parser.add_argument(
        "--payload",
        required=True,
        help="Payload source: @<file> for a file, '-' for stdin.",
    )
    verify_parser.add_argument(
        "--max-payload-bytes",
        type=int,
        default=_DEFAULT_MAX_PAYLOAD_BYTES,
        dest="max_payload_bytes",
        help="Maximum payload size in bytes (default: 8 MiB).",
    )
    verify_parser.add_argument(
        "--timestamp-tolerance",
        type=int,
        default=None,
        dest="timestamp_tolerance",
        help="Timestamp tolerance in seconds (informational).",
    )
    verify_parser.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="Print tracebacks on unexpected errors.",
    )

    return parser


def _load_payload(source: str, max_bytes: int) -> bytes:
    """Read payload bytes from a file path or stdin, enforcing the size limit.

    Args:
        source: '@path' for a file, '-' for stdin.
        max_bytes: Maximum bytes allowed.

    Returns:
        Raw payload bytes.

    Raises:
        FileNotFoundError: If the @file path does not exist.
        ValueError: If the payload exceeds max_bytes.
    """
    chunks: list[bytes] = []
    total = 0

    if source.startswith("@"):
        path = source[1:]
        with open(path, "rb") as fh:
            while True:
                chunk = fh.read(_CHUNK_SIZE)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    raise ValueError("payload exceeds max size")
                chunks.append(chunk)
    else:
        # stdin — may be patched to StringIO in tests (no .buffer attribute)
        if hasattr(sys.stdin, "buffer"):
            raw = sys.stdin.buffer
            while True:
                chunk = raw.read(_CHUNK_SIZE)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    raise ValueError("payload exceeds max size")
                chunks.append(chunk)
        else:
            data = sys.stdin.read().encode()
            if len(data) > max_bytes:
                raise ValueError("payload exceeds max size")
            return data

    return b"".join(chunks)


def main(argv=None) -> None:
    """Main CLI entry point.

    Args:
        argv: Optional list of command-line arguments (for testing).
              If not provided, sys.argv[1:] is used.

    Exit codes:
        0: Valid signature
        1: InvalidSignatureError
        2: ExpiredTimestampError
        64: Usage error
    """
    if argv is None:
        argv = sys.argv[1:]

    parser = _build_parser()

    try:
        args = parser.parse_args(argv)
    except (argparse.ArgumentError, argparse.ArgumentTypeError, SystemExit):
        # Never include the exception message — it may contain argument values.
        print("usage error", file=sys.stderr)
        sys.exit(64)
        return

    if args.subcommand is None:
        print("usage error: subcommand required", file=sys.stderr)
        sys.exit(64)
        return

    debug: bool = args.debug

    # Load payload with size cap.
    try:
        payload = _load_payload(args.payload, args.max_payload_bytes)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(64)
        return
    except FileNotFoundError:
        print("payload file not found", file=sys.stderr)
        sys.exit(64)
        return
    except OSError:
        if debug:
            traceback.print_exc(file=sys.stderr)
        else:
            print("payload read error", file=sys.stderr)
        sys.exit(64)
        return

    # Build the effective Stripe signature header.
    # Tests supply only "v1=<hex>" and pass --timestamp separately.
    # Prepend "t=<ts>," so verify_stripe can extract the timestamp field.
    header = args.header
    if args.provider == "stripe" and args.timestamp is not None:
        if not header.startswith("t="):
            header = f"t={args.timestamp},{header}"

    # Dispatch to the appropriate provider verifier.
    try:
        if args.provider == "github":
            result = verify_github(
                payload,
                args.secret,
                args.header,
                timestamp=args.timestamp,
            )
        else:
            result = verify_stripe(
                payload,
                args.secret,
                header,
            )
    except ExpiredTimestampError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)
        return
    except InvalidSignatureError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
        return
    except WebhookVerificationError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
        return
    except Exception:
        if debug:
            traceback.print_exc(file=sys.stderr)
        else:
            print("unexpected error", file=sys.stderr)
        sys.exit(64)
        return

    print(f"valid provider={result.provider} timestamp={result.timestamp}")
    sys.exit(0)
