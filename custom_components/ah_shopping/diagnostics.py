"""Diagnostics support for the AH Shopping integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_ACCESS_TOKEN,
    CONF_AUTH_CODE,
    CONF_EXPIRES_AT,
    CONF_REFRESH_TOKEN,
    DOMAIN,
)

REDACT_KEYS = {
    CONF_ACCESS_TOKEN,
    CONF_REFRESH_TOKEN,
    CONF_EXPIRES_AT,
    CONF_AUTH_CODE,
    "access_token",
    "refresh_token",
    "authorization",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})

    diag: dict[str, Any] = {
        "entry_id": entry.entry_id,
        "anonymous": entry.data.get("anonymous", False),
        "options": dict(entry.options),
        "has_access_token": bool(entry.data.get(CONF_ACCESS_TOKEN)),
        "has_refresh_token": bool(entry.data.get(CONF_REFRESH_TOKEN)),
        "expires_at": entry.data.get(CONF_EXPIRES_AT, "N/A"),
    }

    storage = data.get("storage")
    if storage:
        diag["shopping_list_count"] = storage.count

    coordinator = data.get("coordinator")
    if coordinator and coordinator.data:
        last = coordinator.data.get("last_receipt")
        if last:
            diag["last_receipt"] = {
                "transaction_id": last.transaction_id,
                "total": last.total,
                "date": last.date.isoformat() if last.date else None,
                "store_name": last.store_name,
            }

    return async_redact_data(diag, REDACT_KEYS)
