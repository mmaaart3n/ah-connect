"""AH Connect – Home Assistant integration for Albert Heijn (appie-go inspired)."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .api import AhConnectApiClient
from .auth import AhAuthManager
from .const import CONF_ACCESS_TOKEN, DOMAIN
from .coordinator import AhConnectCoordinator
from .services import async_setup_services, async_unload_services

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up AH Connect from a config entry."""
    auth = AhAuthManager(hass, entry)
    if auth.is_anonymous and not entry.data.get(CONF_ACCESS_TOKEN):
        await auth.async_get_anonymous_token()

    api = AhConnectApiClient(hass, auth, entry.options)
    coordinator = AhConnectCoordinator(hass, entry, api)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "auth": auth,
        "api": api,
        "coordinator": coordinator,
    }

    await coordinator.async_config_entry_first_refresh()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    if not hass.data[DOMAIN].get("services_registered"):
        await async_setup_services(hass)
        hass.data[DOMAIN]["services_registered"] = True

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    coordinator: AhConnectCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    api: AhConnectApiClient = hass.data[DOMAIN][entry.entry_id]["api"]
    api.options = entry.options
    await coordinator.async_request_refresh()


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload AH Connect config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if not hass.data[DOMAIN] or len(hass.data[DOMAIN]) <= 1:
            await async_unload_services(hass)
            hass.data.pop(DOMAIN, None)
    return unload_ok
