"""Local shopping list storage for the AH Shopping integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import STORAGE_KEY, STORAGE_VERSION
from .models import ShoppingListItem

_LOGGER = logging.getLogger(__name__)


class ShoppingListStorage:
    """Persist the local AH shopping list in Home Assistant storage."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        """Initialize storage for a config entry."""
        self._store = Store[dict[str, Any]](
            hass,
            STORAGE_VERSION,
            f"{STORAGE_KEY}_{entry_id}",
        )
        self._items: list[ShoppingListItem] = []

    async def async_load(self) -> None:
        """Load the shopping list from storage."""
        data = await self._store.async_load()
        if data and isinstance(data.get("items"), list):
            self._items = [
                ShoppingListItem.from_dict(item)
                for item in data["items"]
                if isinstance(item, dict)
            ]
        else:
            self._items = []
        _LOGGER.debug("Loaded %d shopping list items", len(self._items))

    async def async_save(self) -> None:
        """Persist the shopping list to storage."""
        await self._store.async_save(
            {"items": [item.to_dict() for item in self._items]}
        )

    @property
    def items(self) -> list[ShoppingListItem]:
        """Return a copy of the current items."""
        return list(self._items)

    @property
    def count(self) -> int:
        """Return total item count (sum of quantities)."""
        return sum(item.quantity for item in self._items)

    async def add_item(
        self,
        webshop_id: int,
        title: str,
        quantity: int = 1,
    ) -> ShoppingListItem:
        """Add or increment an item on the list."""
        for item in self._items:
            if item.webshop_id == webshop_id:
                item.quantity += quantity
                if title and title != "Unknown":
                    item.title = title
                await self.async_save()
                return item

        new_item = ShoppingListItem(
            webshop_id=webshop_id,
            title=title,
            quantity=quantity,
        )
        self._items.append(new_item)
        await self.async_save()
        return new_item

    async def remove_item(self, webshop_id: int) -> bool:
        """Remove an item from the list. Returns True if found."""
        before = len(self._items)
        self._items = [i for i in self._items if i.webshop_id != webshop_id]
        if len(self._items) < before:
            await self.async_save()
            return True
        return False

    async def clear(self) -> None:
        """Clear all items from the list."""
        self._items = []
        await self.async_save()

    def get_list(self) -> list[dict[str, Any]]:
        """Return the list as serializable dicts."""
        return [item.to_dict() for item in self._items]
