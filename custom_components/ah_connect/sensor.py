"""Sensors for AH Connect."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

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
)
from .coordinator import AhConnectCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: AhConnectCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    entities: list[SensorEntity] = []
    opts = entry.options

    if opts.get(OPT_ENABLE_RECEIPTS_SENSOR) and not entry.data.get("anonymous"):
        entities.extend(
            [
                AhReceiptTotalSensor(coordinator, entry),
                AhReceiptDateSensor(coordinator, entry),
            ]
        )

    if opts.get(OPT_ENABLE_REMOTE_SHOPPING_LIST) and not entry.data.get("anonymous"):
        entities.append(AhShoppingListCountSensor(coordinator, entry))

    if opts.get(OPT_ENABLE_BONUS_SENSOR):
        entities.append(AhBonusCountSensor(coordinator, entry))

    if opts.get(OPT_EXPERIMENTAL_ORDER_ENABLED) and not entry.data.get("anonymous"):
        entities.extend(
            [
                AhOrderTotalSensor(coordinator, entry),
                AhOrderItemCountSensor(coordinator, entry),
            ]
        )

    async_add_entities(entities)


class AhConnectSensor(CoordinatorEntity, SensorEntity):
    """Base AH Connect sensor."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self, coordinator: AhConnectCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "Albert Heijn",
            "model": "AH Connect",
        }


class AhReceiptTotalSensor(AhConnectSensor):
    _attr_name = "Last receipt total"
    _attr_unique_id_suffix = "last_receipt_total"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_{self._attr_unique_id_suffix}"

    @property
    def native_value(self) -> str | None:
        receipt = self.coordinator.data.get(COORD_LAST_RECEIPT)
        if not receipt:
            return None
        return str(receipt.get("total_amount", ""))


class AhReceiptDateSensor(AhConnectSensor):
    _attr_name = "Last receipt date"
    _attr_unique_id_suffix = "last_receipt_date"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_{self._attr_unique_id_suffix}"

    @property
    def native_value(self) -> str | None:
        receipt = self.coordinator.data.get(COORD_LAST_RECEIPT)
        if not receipt:
            return None
        return receipt.get("date")


class AhShoppingListCountSensor(AhConnectSensor):
    _attr_name = "Remote shopping list count"
    _attr_unique_id_suffix = "remote_shopping_list_count"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_{self._attr_unique_id_suffix}"

    @property
    def native_value(self) -> int | None:
        return self.coordinator.data.get(COORD_SHOPPING_LIST_COUNT)


class AhBonusCountSensor(AhConnectSensor):
    _attr_name = "Bonus product count"
    _attr_unique_id_suffix = "bonus_product_count"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_{self._attr_unique_id_suffix}"

    @property
    def native_value(self) -> int | None:
        return self.coordinator.data.get(COORD_BONUS_COUNT)


class AhOrderTotalSensor(AhConnectSensor):
    _attr_name = "Order total"
    _attr_unique_id_suffix = "order_total"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_{self._attr_unique_id_suffix}"

    @property
    def native_value(self) -> str | None:
        summary = self.coordinator.data.get(COORD_ORDER_SUMMARY)
        if not summary:
            return None
        return str(summary.get("total_price", ""))


class AhOrderItemCountSensor(AhConnectSensor):
    _attr_name = "Order item count"
    _attr_unique_id_suffix = "order_item_count"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_{self._attr_unique_id_suffix}"

    @property
    def native_value(self) -> int | None:
        summary = self.coordinator.data.get(COORD_ORDER_SUMMARY)
        if not summary:
            return None
        return summary.get("total_items")
