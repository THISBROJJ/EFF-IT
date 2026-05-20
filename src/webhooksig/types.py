"""Type definitions and exceptions for webhook signature verification."""

from dataclasses import dataclass

_ALLOWED_ALGORITHMS: frozenset[str] = frozenset({"sha256"})


class WebhookVerificationError(Exception):
    def __init__(self, provider: str, reason_code: str, *, cause: Exception | None = None) -> None:
        self.provider = provider
        self.reason_code = reason_code
        super().__init__(str(self))
        if cause is not None:
            self.__cause__ = cause

    def __str__(self) -> str:
        return f"{self.provider}: {self.reason_code}"

    def __repr__(self) -> str:
        return f"{type(self).__name__}(provider={self.provider!r}, reason_code={self.reason_code!r})"


class InvalidSignatureError(WebhookVerificationError):
    pass


class ExpiredTimestampError(WebhookVerificationError):
    pass


@dataclass(frozen=True)
class SignatureSpec:
    algorithm: str
    header_name: str
    encoding: str
    timestamp_tolerance_s: int = 300

    def __post_init__(self) -> None:
        if self.algorithm not in _ALLOWED_ALGORITHMS:
            raise ValueError(
                f"algorithm {self.algorithm!r} not allowed; use one of {sorted(_ALLOWED_ALGORITHMS)}"
            )


@dataclass(frozen=True)
class VerificationResult:
    valid: bool
    provider: str
    timestamp: int | None = None
