"""DataUpdateCoordinator for AH Shopping."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AhApiClient
from .auth import AhAuthManager
from .const import (
    CONF_ENABLE_RECEIPTS,
    CONF_SCAN_INTERVAL,
    DEFAULT_ENABLE_RECEIPTS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .exceptions import AhAuthError, AhError
from .models import AhReceipt

_LOGGER = logging.getLogger(__name__)


class AhDataCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for receipt data and periodic updates."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        api: AhApiClient,
        auth: AhAuthManager,
    ) -> None:
        """Initialize the coordinator."""
        scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        self.api = api
        self.auth = auth
        self.entry = entry

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch receipt data."""
        enable_receipts = self.entry.options.get(
            CONF_ENABLE_RECEIPTS, DEFAULT_ENABLE_RECEIPTS
        )

        if self.auth.is_anonymous or not enable_receipts:
            return {"last_receipt": None, "receipts": []}

        try:
            receipts = await self.api.get_receipts()
            last_receipt: AhReceipt | None = receipts[0] if receipts else None
            return {
                "last_receipt": last_receipt,
                "receipts": receipts,
            }
        except AhAuthError as err:
            raise UpdateFailed(f"Authentication error: {err}") from err
        except AhError as err:
            raise UpdateFailed(f"AH API error: {err}") from err
