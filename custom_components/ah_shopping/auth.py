"""Authentication handling for the AH Shopping integration."""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    APPLICATION_HEADER,
    AUTH_ANONYMOUS_TOKEN,
    AUTH_REFRESH,
    AUTH_TOKEN,
    CLIENT_ID,
    CLIENT_VERSION,
    CONF_ACCESS_TOKEN,
    CONF_ANONYMOUS,
    CONF_CLIENT_ID,
    CONF_EXPIRES_AT,
    CONF_REFRESH_TOKEN,
    DEFAULT_TIMEOUT,
    MIN_REQUEST_INTERVAL,
    TOKEN_REFRESH_BUFFER,
    USER_AGENT,
)
from .exceptions import AhAuthError, AhRateLimitError, AhUnavailableError

_LOGGER = logging.getLogger(__name__)


class AhAuthManager:
    """Manages AH API tokens with automatic refresh."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        *,
        on_token_update: Any | None = None,
    ) -> None:
        """Initialize the auth manager."""
        self._hass = hass
        self._entry = entry
        self._session = async_get_clientsession(hass)
        self._on_token_update = on_token_update
        self._lock = asyncio.Lock()
        self._last_request: float = 0.0

    @property
    def is_anonymous(self) -> bool:
        """Return True if running in anonymous mode."""
        return bool(self._entry.data.get(CONF_ANONYMOUS))

    @property
    def is_authenticated(self) -> bool:
        """Return True if user is authenticated (not anonymous)."""
        return not self.is_anonymous and bool(self._entry.data.get(CONF_ACCESS_TOKEN))

    @property
    def client_id(self) -> str:
        """OAuth client ID used for this entry."""
        return str(self._entry.data.get(CONF_CLIENT_ID) or CLIENT_ID)

    async def _throttle(self) -> None:
        """Enforce minimum interval between auth requests."""
        elapsed = time.monotonic() - self._last_request
        if elapsed < MIN_REQUEST_INTERVAL:
            await asyncio.sleep(MIN_REQUEST_INTERVAL - elapsed)
        self._last_request = time.monotonic()

    def _headers(self) -> dict[str, str]:
        """Return default request headers."""
        return {
            "User-Agent": USER_AGENT,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "x-application": APPLICATION_HEADER,
            "x-client-name": self.client_id,
            "x-client-version": CLIENT_VERSION,
        }

    async def _request(
        self,
        method: str,
        url: str,
        *,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an authenticated HTTP request."""
        await self._throttle()
        timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT)
        try:
            async with self._session.request(
                method,
                url,
                json=json_body,
                headers=self._headers(),
                timeout=timeout,
            ) as response:
                if response.status == 429:
                    raise AhRateLimitError("Rate limit exceeded during auth request")
                if response.status >= 500:
                    raise AhUnavailableError(
                        f"AH auth service unavailable (HTTP {response.status})"
                    )
                data = await response.json(content_type=None)
                if response.status >= 400:
                    raise AhAuthError(
                        f"Authentication failed (HTTP {response.status})"
                    )
                if not isinstance(data, dict):
                    raise AhAuthError("Unexpected auth response format")
                return data
        except aiohttp.ClientError as err:
            raise AhUnavailableError(f"Network error during auth: {err}") from err

    async def get_access_token(self) -> str:
        """Return a valid access token, refreshing if needed."""
        async with self._lock:
            if self.is_anonymous:
                token_data = await self._fetch_anonymous_token()
                return str(token_data["access_token"])

            if not self.is_authenticated:
                raise AhAuthError("Not authenticated. Complete OAuth login first.")

            if self._token_needs_refresh():
                await self._refresh_token()

            token = self._entry.data.get(CONF_ACCESS_TOKEN)
            if not token:
                raise AhAuthError("No access token available")
            return str(token)

    def _token_needs_refresh(self) -> bool:
        """Check if the access token should be refreshed."""
        expires_at = self._entry.data.get(CONF_EXPIRES_AT)
        if not expires_at:
            return True
        try:
            expiry = datetime.fromisoformat(str(expires_at))
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)
            return datetime.now(timezone.utc) >= (expiry - TOKEN_REFRESH_BUFFER)
        except (ValueError, TypeError):
            return True

    async def _fetch_anonymous_token(self) -> dict[str, Any]:
        """Fetch a new anonymous access token."""
        _LOGGER.debug("Fetching anonymous AH token")
        data = await self._request(
            "POST",
            AUTH_ANONYMOUS_TOKEN,
            json_body={"clientId": self.client_id},
        )
        if "access_token" not in data:
            raise AhAuthError("Anonymous token response missing access_token")
        return data

    async def exchange_auth_code(self, code: str) -> dict[str, Any]:
        """Exchange an OAuth authorization code for tokens."""
        _LOGGER.debug("Exchanging OAuth authorization code")
        data = await self._request(
            "POST",
            AUTH_TOKEN,
            json_body={"clientId": self.client_id, "code": code.strip()},
        )
        return self._parse_token_response(data)

    async def _refresh_token(self) -> None:
        """Refresh the access token using the stored refresh token."""
        refresh_token = self._entry.data.get(CONF_REFRESH_TOKEN)
        if not refresh_token:
            raise AhAuthError(
                "No refresh token available. Re-authenticate via config flow."
            )

        _LOGGER.debug("Refreshing AH access token")
        data = await self._request(
            "POST",
            AUTH_REFRESH,
            json_body={"clientId": self.client_id, "refreshToken": refresh_token},
        )
        token_data = self._parse_token_response(data)
        await self._persist_tokens(token_data)

    def _parse_token_response(self, data: dict[str, Any]) -> dict[str, Any]:
        """Parse and validate a token response."""
        access_token = data.get("access_token") or data.get("accessToken")
        if not access_token:
            raise AhAuthError("Token response missing access_token")

        refresh_token = data.get("refresh_token") or data.get("refreshToken")
        expires_in = data.get("expires_in") or data.get("expiresIn") or 3600

        expires_at = datetime.now(timezone.utc).timestamp() + int(expires_in)
        expires_at_iso = datetime.fromtimestamp(
            expires_at, tz=timezone.utc
        ).isoformat()

        return {
            CONF_ACCESS_TOKEN: access_token,
            CONF_REFRESH_TOKEN: refresh_token or self._entry.data.get(CONF_REFRESH_TOKEN),
            CONF_EXPIRES_AT: expires_at_iso,
        }

    async def _persist_tokens(self, token_data: dict[str, Any]) -> None:
        """Persist updated tokens to the config entry."""
        new_data = {**self._entry.data, **token_data}
        self._hass.config_entries.async_update_entry(self._entry, data=new_data)
        if self._on_token_update:
            await self._on_token_update(token_data)

    async def setup_authenticated(self, code: str) -> dict[str, Any]:
        """Complete OAuth setup and persist tokens."""
        token_data = await self.exchange_auth_code(code)
        token_data[CONF_ANONYMOUS] = False
        token_data[CONF_CLIENT_ID] = self.client_id
        return token_data
