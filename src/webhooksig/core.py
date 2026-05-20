import hmac
import time

from webhooksig.types import (
    ExpiredTimestampError,
    InvalidSignatureError,
    SignatureSpec,
    VerificationResult,
)


def verify(
    payload: bytes,
    secret: str,
    signature: str,
    spec: SignatureSpec,
    timestamp: int | None = None,
    now: int | None = None,
) -> VerificationResult:
    if timestamp is not None and spec.timestamp_tolerance_s > 0:
        current = now if now is not None else int(time.time())
        if abs(current - timestamp) > spec.timestamp_tolerance_s:
            raise ExpiredTimestampError(provider="unknown", reason_code="timestamp_expired")

    expected = hmac.new(secret.encode(), payload, spec.algorithm).digest()

    if spec.encoding == "hex":
        try:
            provided = bytes.fromhex(signature)
        except ValueError as exc:
            raise InvalidSignatureError(provider="unknown", reason_code="invalid_signature") from exc
    else:
        raise ValueError(f"unsupported encoding: {spec.encoding!r}")

    if not hmac.compare_digest(expected, provided):
        raise InvalidSignatureError(provider="unknown", reason_code="invalid_signature")

    return VerificationResult(valid=True, provider="unknown", timestamp=timestamp)
