"""Data update coordinator for AH Connect."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import AhConnectApiClient
from .const import (
    COORD_BONUS_COUNT,
    COORD_LAST_RECEIPT,
    COORD_ORDER_SUMMARY,
    COORD_SHOPPING_LIST_COUNT,
    DOMAIN,
    OPT_ENABLE_BONUS_SENSOR,
    OPT_ENABLE_RECEIPTS_SENSOR,
    OPT_ENABLE_REMOTE_SHOPPING_LIST,
    OPT_EXPERIMENTAL_ORDER_ENABLED,
    OPT_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class AhConnectCoordinator(DataUpdateCoordinator):
    """Coordinator for polling AH data."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        api: AhConnectApiClient,
    ) -> None:
        interval = entry.options.get(OPT_SCAN_INTERVAL, 300)
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=interval),
        )
        self.entry = entry
        self.api = api

    async def _async_update_data(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            COORD_LAST_RECEIPT: None,
            COORD_SHOPPING_LIST_COUNT: 0,
            COORD_BONUS_COUNT: 0,
            COORD_ORDER_SUMMARY: None,
        }
        opts = self.entry.options

        if opts.get(OPT_ENABLE_RECEIPTS_SENSOR) and not self.api.auth.is_anonymous:
            try:
                receipts = await self.api.get_receipts()
                if receipts:
                    data[COORD_LAST_RECEIPT] = receipts[0].to_dict()
            except Exception as err:
                _LOGGER.warning("Failed to fetch receipts: %s", err)

        if opts.get(OPT_ENABLE_REMOTE_SHOPPING_LIST) and not self.api.auth.is_anonymous:
            try:
                lists = await self.api.get_shopping_lists()
                if lists:
                    data[COORD_SHOPPING_LIST_COUNT] = lists[0].item_count
            except Exception as err:
                _LOGGER.warning("Failed to fetch shopping lists: %s", err)

        if opts.get(OPT_ENABLE_BONUS_SENSOR):
            try:
                bonus = await self.api.get_bonus_products()
                data[COORD_BONUS_COUNT] = len(bonus)
            except Exception as err:
                _LOGGER.warning("Failed to fetch bonus products: %s", err)

        if opts.get(OPT_EXPERIMENTAL_ORDER_ENABLED) and not self.api.auth.is_anonymous:
            try:
                summary = await self.api.get_order_summary()
                data[COORD_ORDER_SUMMARY] = summary.to_dict()
            except Exception as err:
                _LOGGER.warning("Failed to fetch order summary: %s", err)

        return data
