"""Authentication manager for AH Connect (appie-go aligned)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_ACCESS_TOKEN,
    CONF_ANONYMOUS,
    CONF_CLIENT_ID,
    CONF_EXPIRES_AT,
    CONF_MEMBER_ID,
    CONF_REFRESH_TOKEN,
    DEFAULT_BASE_URL,
    DEFAULT_CLIENT_ID,
    DEFAULT_CLIENT_VERSION,
    DEFAULT_USER_AGENT,
    PATH_AUTH_ANONYMOUS,
    PATH_AUTH_REFRESH,
    PATH_AUTH_TOKEN,
)
from .exceptions import AhAuthError

_LOGGER = logging.getLogger(__name__)


class AhAuthManager:
    """Manage OAuth tokens for AH API (inspired by appie-go)."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._session = async_get_clientsession(hass)
        self._order_id: str = ""
        self._order_hash: str = ""

    @property
    def is_anonymous(self) -> bool:
        return bool(self.entry.data.get(CONF_ANONYMOUS))

    @property
    def client_id(self) -> str:
        return self.entry.data.get(CONF_CLIENT_ID) or DEFAULT_CLIENT_ID

    def _expires_at(self) -> datetime | None:
        raw = self.entry.data.get(CONF_EXPIRES_AT)
        if not raw:
            return None
        try:
            return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        except ValueError:
            return None

    def _is_expired(self) -> bool:
        expires = self._expires_at()
        if expires is None:
            return False
        now = datetime.now(tz=UTC)
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=UTC)
        return now >= expires

    async def get_access_token(self) -> str:
        if self.is_anonymous:
            token = self.entry.data.get(CONF_ACCESS_TOKEN)
            if not token:
                await self.async_get_anonymous_token()
                token = self.entry.data.get(CONF_ACCESS_TOKEN)
            return str(token or "")

        if self._is_expired() and self.entry.data.get(CONF_REFRESH_TOKEN):
            await self.async_refresh_token()

        return str(self.entry.data.get(CONF_ACCESS_TOKEN) or "")

    async def async_get_headers(self) -> dict[str, str]:
        token = await self.get_access_token()
        headers = {
            "User-Agent": DEFAULT_USER_AGENT,
            "x-client-name": self.client_id,
            "x-client-version": DEFAULT_CLIENT_VERSION,
            "x-application": "AHWEBSHOP",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        if self._order_id:
            headers["appie-current-order-id"] = self._order_id
            if self._order_hash:
                headers["appie-current-order-hash"] = self._order_hash
        return headers

    def set_order_context(self, order_id: str, order_hash: str = "") -> None:
        self._order_id = order_id
        self._order_hash = order_hash

    async def _post_auth(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        url = f"{DEFAULT_BASE_URL}{path}"
        headers = {
            "User-Agent": DEFAULT_USER_AGENT,
            "x-client-name": self.client_id,
            "x-client-version": DEFAULT_CLIENT_VERSION,
            "x-application": "AHWEBSHOP",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        async with self._session.post(url, json=body, headers=headers) as resp:
            if resp.status >= 400:
                text = await resp.text()
                raise AhAuthError(f"Auth request failed ({resp.status}): {text[:200]}")
            return await resp.json()

    async def async_get_anonymous_token(self) -> None:
        data = await self._post_auth(
            PATH_AUTH_ANONYMOUS, {"clientId": self.client_id}
        )
        await self._store_tokens(data, anonymous=True)

    async def async_exchange_code(self, code: str) -> None:
        data = await self._post_auth(
            PATH_AUTH_TOKEN, {"clientId": self.client_id, "code": code}
        )
        await self._store_tokens(data, anonymous=False)

    @staticmethod
    async def exchange_authorization_code(
        hass: HomeAssistant, client_id: str, code: str
    ) -> dict[str, Any]:
        """Exchange authorization code and return normalized token dict."""
        session = async_get_clientsession(hass)
        url = f"{DEFAULT_BASE_URL}{PATH_AUTH_TOKEN}"
        headers = {
            "User-Agent": DEFAULT_USER_AGENT,
            "x-client-name": client_id,
            "x-client-version": DEFAULT_CLIENT_VERSION,
            "x-application": "AHWEBSHOP",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        async with session.post(
            url, json={"clientId": client_id, "code": code}, headers=headers
        ) as resp:
            if resp.status >= 400:
                raise AhAuthError(f"Token exchange failed ({resp.status})")
            data = await resp.json()

        expires_in = data.get("expires_in") or data.get("expiresIn") or 0
        expires_at = ""
        if expires_in:
            expires_at = datetime.fromtimestamp(
                datetime.now(tz=UTC).timestamp() + int(expires_in), tz=UTC
            ).isoformat()

        return {
            CONF_ACCESS_TOKEN: data.get("access_token") or data.get("accessToken"),
            CONF_REFRESH_TOKEN: data.get("refresh_token") or data.get("refreshToken"),
            CONF_EXPIRES_AT: expires_at,
            CONF_MEMBER_ID: str(data.get("member_id") or data.get("memberId") or ""),
            CONF_CLIENT_ID: client_id,
        }

    async def async_refresh_token(self) -> None:
        refresh = self.entry.data.get(CONF_REFRESH_TOKEN)
        if not refresh:
            raise AhAuthError("No refresh token available")
        data = await self._post_auth(
            PATH_AUTH_REFRESH,
            {"clientId": self.client_id, "refreshToken": refresh},
        )
        await self._store_tokens(data, anonymous=False)

    async def _store_tokens(self, data: dict[str, Any], *, anonymous: bool) -> None:
        access = data.get("access_token") or data.get("accessToken")
        refresh = data.get("refresh_token") or data.get("refreshToken")
        expires_in = data.get("expires_in") or data.get("expiresIn") or 0
        member_id = data.get("member_id") or data.get("memberId")

        expires_at = self.entry.data.get(CONF_EXPIRES_AT)
        if expires_in:
            expires_at = (
                datetime.now(tz=UTC).timestamp() + int(expires_in)
            )
            expires_at = datetime.fromtimestamp(expires_at, tz=UTC).isoformat()

        new_data = {**self.entry.data}
        if access:
            new_data[CONF_ACCESS_TOKEN] = access
        if refresh:
            new_data[CONF_REFRESH_TOKEN] = refresh
        if expires_at:
            new_data[CONF_EXPIRES_AT] = expires_at
        if member_id:
            new_data[CONF_MEMBER_ID] = str(member_id)
        new_data[CONF_ANONYMOUS] = anonymous

        self.hass.config_entries.async_update_entry(self.entry, data=new_data)
        _LOGGER.debug("Token data updated (anonymous=%s)", anonymous)
