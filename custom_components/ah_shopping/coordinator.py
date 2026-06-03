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
    CONF_ENABLE_BONUS_SENSOR,
    CONF_ENABLE_RECEIPTS,
    CONF_ENABLE_REMOTE_SHOPPING_LIST,
    CONF_EXPERIMENTAL_ORDER,
    CONF_SCAN_INTERVAL,
    DEFAULT_ENABLE_BONUS_SENSOR,
    DEFAULT_ENABLE_RECEIPTS,
    DEFAULT_ENABLE_REMOTE_SHOPPING_LIST,
    DEFAULT_EXPERIMENTAL_ORDER,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .exceptions import AhAuthError, AhError, AhExperimentalFeatureDisabled

_LOGGER = logging.getLogger(__name__)


class AhDataCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for receipts, remote list, orders, and bonus data."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        api: AhApiClient,
        auth: AhAuthManager,
    ) -> None:
        """Initialize coordinator."""
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
        """Fetch coordinator data."""
        data: dict[str, Any] = {
            "last_receipt": None,
            "receipts": [],
            "remote_list_count": None,
            "order_total": None,
            "order_item_count": None,
            "bonus_product_count": None,
        }

        if self.auth.is_anonymous:
            return data

        if self.entry.options.get(CONF_ENABLE_RECEIPTS, DEFAULT_ENABLE_RECEIPTS):
            try:
                receipts = await self.api.get_receipts()
                data["receipts"] = receipts
                data["last_receipt"] = receipts[0] if receipts else None
            except AhAuthError as err:
                raise UpdateFailed(f"Authentication error: {err}") from err
            except AhError as err:
                raise UpdateFailed(f"Receipt fetch failed: {err}") from err

        if self.entry.options.get(
            CONF_ENABLE_REMOTE_SHOPPING_LIST, DEFAULT_ENABLE_REMOTE_SHOPPING_LIST
        ):
            try:
                lists = await self.api.get_shopping_lists()
                if lists:
                    items = await self.api.get_shopping_list_items(lists[0].list_id)
                    data["remote_list_count"] = len(items)
            except AhError as err:
                _LOGGER.debug("Remote shopping list update failed: %s", err)

        if self.entry.options.get(CONF_EXPERIMENTAL_ORDER, DEFAULT_EXPERIMENTAL_ORDER):
            try:
                order = await self.api.get_order()
                data["order_total"] = order.total_price
                data["order_item_count"] = order.item_count
            except (AhExperimentalFeatureDisabled, AhError) as err:
                _LOGGER.debug("Order update skipped: %s", err)

        if self.entry.options.get(CONF_ENABLE_BONUS_SENSOR, DEFAULT_ENABLE_BONUS_SENSOR):
            try:
                bonus = await self.api.get_bonus_products()
                data["bonus_product_count"] = len(bonus)
            except AhError as err:
                _LOGGER.debug("Bonus products update failed: %s", err)

        return data
