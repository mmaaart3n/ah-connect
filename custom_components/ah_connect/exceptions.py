"""Exceptions for AH Connect."""

from __future__ import annotations


class AhConnectError(Exception):
    """Base exception for AH Connect."""


class AhApiError(AhConnectError):
    """API request failed."""

    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


class AhAuthError(AhConnectError):
    """Authentication failed."""


class AhConfigError(AhConnectError):
    """Configuration is invalid."""


class AhRateLimitError(AhApiError):
    """Rate limit exceeded."""


class AhUnavailableError(AhApiError):
    """Service unavailable."""


class AhNotImplementedError(AhConnectError):
    """Feature not yet implemented (pending appie-go parity)."""


class AhExperimentalFeatureDisabled(AhConnectError):
    """Experimental feature is disabled in options."""


class AhAuthenticatedModeRequired(AhConnectError):
    """Authenticated mode is required for this operation."""
