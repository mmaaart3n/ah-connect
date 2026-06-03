"""Diagnostics for AH Connect with secret redaction."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

REDACT_LIST = [
    "token",
    "access_token",
    "accessToken",
    "refresh_token",
    "refreshToken",
    "id_token",
    "idToken",
    "authorization",
    "Authorization",
    "appie_config_json",
    "bearer",
    "Bearer",
    "password",
    "secret",
    "member_id",
]


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return redacted diagnostics for a config entry."""
    data = {
        "entry_id": entry.entry_id,
        "title": entry.title,
        "domain": entry.domain,
        "source": entry.source,
        "unique_id": entry.unique_id,
        "options": dict(entry.options),
        "data_keys": list(entry.data.keys()),
        "anonymous": entry.data.get("anonymous"),
        "auth_method": entry.data.get("auth_method"),
    }
    return async_redact_data(data, REDACT_LIST)
