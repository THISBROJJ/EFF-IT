"""GitHub webhook signature verification adapter."""

from webhooksig import core
from webhooksig.types import InvalidSignatureError, SignatureSpec, VerificationResult

SCHEME_VERSION = "github-sha256-v1"

GITHUB_SPEC = SignatureSpec(
    algorithm="sha256",
    header_name="X-Hub-Signature-256",
    encoding="hex",
    timestamp_tolerance_s=300,
)

_PREFIX = "sha256="
_MAX_HEADER_BYTES = 4096


def verify_github(
    payload: bytes,
    secret: str,
    signature_header: str,
    *,
    timestamp: int | None = None,
) -> VerificationResult:
    """Verify a GitHub webhook HMAC-SHA256 signature.

    Args:
        payload: The raw request body bytes.
        secret: The shared secret configured in GitHub.
        signature_header: Value of the X-Hub-Signature-256 header.
        timestamp: Optional webhook delivery timestamp (seconds since epoch).

    Returns:
        VerificationResult with valid=True and provider="github".

    Raises:
        InvalidSignatureError: If the header is malformed or signature does not match.
        ExpiredTimestampError: If the timestamp is outside the tolerance window.
    """
    if len(signature_header.encode("utf-8")) > _MAX_HEADER_BYTES:
        raise InvalidSignatureError(provider="github", reason_code="header_too_large")

    if not signature_header.startswith(_PREFIX):
        raise InvalidSignatureError(provider="github", reason_code="missing_prefix")

    sig_hex = signature_header[len(_PREFIX):]

    try:
        core.verify(payload, secret, sig_hex, GITHUB_SPEC, timestamp=timestamp)
    except InvalidSignatureError as exc:
        if exc.provider != "github":
            raise InvalidSignatureError(
                provider="github",
                reason_code=exc.reason_code,
                cause=exc,
            ) from exc
        raise

    return VerificationResult(valid=True, provider="github", timestamp=timestamp)
