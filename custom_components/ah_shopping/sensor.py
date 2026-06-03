"""Sensor platform for the AH Shopping integration."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AhDataCoordinator
from .storage import ShoppingListStorage


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AH Shopping sensors."""
    coordinator: AhDataCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    storage: ShoppingListStorage = hass.data[DOMAIN][entry.entry_id]["storage"]
    auth = hass.data[DOMAIN][entry.entry_id]["auth"]

    entities: list[SensorEntity] = [
        AhShoppingListCountSensor(entry, storage),
    ]

    if not auth.is_anonymous:
        entities.extend(
            [
                AhLastReceiptTotalSensor(entry, coordinator),
                AhLastReceiptDateSensor(entry, coordinator),
            ]
        )

    async_add_entities(entities)


class AhShoppingListCountSensor(SensorEntity):
    """Sensor showing the number of items on the local shopping list."""

    _attr_has_entity_name = True
    _attr_name = "Shopping list count"
    _attr_icon = "mdi:cart"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "items"

    def __init__(self, entry: ConfigEntry, storage: ShoppingListStorage) -> None:
        """Initialize the sensor."""
        self._storage = storage
        self._attr_unique_id = f"{entry.entry_id}_list_count"
        self._attr_device_info = _device_info(entry)

    @property
    def native_value(self) -> int:
        """Return the item count."""
        return self._storage.count

    async def async_added_to_hass(self) -> None:
        """Register for list update events."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.hass.bus.async_listen(
                f"{DOMAIN}_list_updated",
                self._handle_list_updated,
            )
        )

    def _handle_list_updated(self, event: Any) -> None:
        """Handle shopping list update event."""
        self.async_write_ha_state()


class AhLastReceiptTotalSensor(CoordinatorEntity[AhDataCoordinator], SensorEntity):
    """Sensor showing the total of the last receipt."""

    _attr_has_entity_name = True
    _attr_name = "Last receipt total"
    _attr_icon = "mdi:receipt"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(
        self, entry: ConfigEntry, coordinator: AhDataCoordinator
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_last_receipt_total"
        self._attr_device_info = _device_info(entry)

    @property
    def native_value(self) -> float | None:
        """Return the last receipt total."""
        last = self.coordinator.data.get("last_receipt") if self.coordinator.data else None
        return last.total if last else None

    @property
    def native_unit_of_measurement(self) -> str:
        """Return currency unit."""
        return "EUR"


class AhLastReceiptDateSensor(CoordinatorEntity[AhDataCoordinator], SensorEntity):
    """Sensor showing the date of the last receipt."""

    _attr_has_entity_name = True
    _attr_name = "Last receipt date"
    _attr_icon = "mdi:calendar"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(
        self, entry: ConfigEntry, coordinator: AhDataCoordinator
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_last_receipt_date"
        self._attr_device_info = _device_info(entry)

    @property
    def native_value(self) -> datetime | None:
        """Return the last receipt date."""
        last = self.coordinator.data.get("last_receipt") if self.coordinator.data else None
        return last.date if last else None


def _device_info(entry: ConfigEntry) -> dict[str, Any]:
    """Return device info for sensors."""
    return {
        "identifiers": {(DOMAIN, entry.entry_id)},
        "name": "AH Shopping",
        "manufacturer": "Albert Heijn",
        "model": "Appie API",
    }
