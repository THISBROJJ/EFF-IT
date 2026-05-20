"""Stripe webhook signature verification adapter."""

import hmac
import time

from webhooksig.types import (
    ExpiredTimestampError,
    InvalidSignatureError,
    SignatureSpec,
    VerificationResult,
)

SCHEME_VERSION = "stripe-v1"

STRIPE_SPEC = SignatureSpec(
    algorithm="sha256",
    header_name="Stripe-Signature",
    encoding="hex",
    timestamp_tolerance_s=300,
)

_MAX_HEADER_BYTES = 4096
_MAX_V1_ELEMENTS = 16


def verify_stripe(
    payload: bytes,
    secret: str,
    signature_header: str,
    *,
    now: int | None = None,
) -> VerificationResult:
    """Verify a Stripe webhook HMAC-SHA256 signature.

    Args:
        payload: The raw request body bytes.
        secret: The webhook endpoint secret configured in Stripe.
        signature_header: Value of the Stripe-Signature header.
        now: Optional current Unix timestamp; defaults to int(time.time()).

    Returns:
        VerificationResult with valid=True and provider="stripe".

    Raises:
        InvalidSignatureError: If the header is malformed, too large, or signature mismatch.
        ExpiredTimestampError: If the timestamp is outside the tolerance window.
    """
    if len(signature_header.encode("utf-8")) > _MAX_HEADER_BYTES:
        raise InvalidSignatureError(provider="stripe", reason_code="header_too_large")

    timestamp_str: str | None = None
    v1_sigs: list[str] = []

    for part in signature_header.split(","):
        if not part:
            continue
        if "=" not in part:
            raise InvalidSignatureError(provider="stripe", reason_code="missing_timestamp")
        key, _, value = part.partition("=")
        if key == "t":
            timestamp_str = value
        elif key == "v1":
            if value:
                v1_sigs.append(value)

    if timestamp_str is None:
        raise InvalidSignatureError(provider="stripe", reason_code="missing_timestamp")

    if not v1_sigs:
        raise InvalidSignatureError(provider="stripe", reason_code="missing_signature")

    if len(v1_sigs) > _MAX_V1_ELEMENTS:
        raise InvalidSignatureError(provider="stripe", reason_code="too_many_signatures")

    try:
        timestamp = int(timestamp_str)
    except ValueError:
        raise InvalidSignatureError(provider="stripe", reason_code="missing_timestamp")

    current = now if now is not None else int(time.time())
    # Reject future timestamps unconditionally; reject past timestamps outside tolerance.
    if timestamp > current or (current - timestamp) > STRIPE_SPEC.timestamp_tolerance_s:
        raise ExpiredTimestampError(provider="stripe", reason_code="timestamp_expired")

    signed_payload = timestamp_str.encode() + b"." + payload
    expected_hex = hmac.new(
        secret.encode(),
        signed_payload,
        "sha256",
    ).hexdigest()

    # Compare all candidates timing-safely using string comparison (case-sensitive).
    # Do NOT short-circuit on match — iterate all candidates.
    matched = False
    for candidate in v1_sigs:
        if hmac.compare_digest(expected_hex, candidate):
            matched = True

    if not matched:
        raise InvalidSignatureError(provider="stripe", reason_code="invalid_signature")

    return VerificationResult(valid=True, provider="stripe", timestamp=timestamp)
