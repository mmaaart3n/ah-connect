"""Exception classes for the AH Shopping integration."""

from __future__ import annotations


class AhError(Exception):
    """Base exception for AH Shopping."""


class AhApiError(AhError):
    """Raised when the AH API returns an unexpected or error response."""


class AhAuthError(AhError):
    """Raised when authentication or token refresh fails."""


class AhRateLimitError(AhApiError):
    """Raised when rate limiting is detected or enforced locally."""


class AhUnavailableError(AhApiError):
    """Raised when the AH API is temporarily unavailable."""


class AhNotImplementedError(AhApiError):
    """Raised when an API method is not yet implemented."""


class AhExperimentalFeatureDisabled(AhError):
    """Raised when an experimental feature is disabled in options."""
