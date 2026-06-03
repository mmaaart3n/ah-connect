"""Services for the AH Shopping integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er

from .api import AhApiClient
from .auth import AhAuthManager
from .const import (
    CONF_MAX_SEARCH_RESULTS,
    DEFAULT_MAX_SEARCH_RESULTS,
    DOMAIN,
    EVENT_PRODUCTS_FOUND,
)
from .coordinator import AhDataCoordinator
from .exceptions import AhAuthError, AhError
from .storage import ShoppingListStorage

_LOGGER = logging.getLogger(__name__)

SERVICE_SEARCH_PRODUCTS = "search_products"
SERVICE_ADD_TO_LIST = "add_to_list"
SERVICE_REMOVE_FROM_LIST = "remove_from_list"
SERVICE_CLEAR_LIST = "clear_list"
SERVICE_GET_LIST = "get_list"
SERVICE_REFRESH_RECEIPTS = "refresh_receipts"
SERVICE_EXPORT_LIST_TO_TODO = "export_list_to_todo"

SEARCH_PRODUCTS_SCHEMA = vol.Schema(
    {
        vol.Required("query"): cv.string,
        vol.Optional("limit", default=10): vol.All(
            cv.positive_int, vol.Range(max=50)
        ),
    }
)

ADD_TO_LIST_SCHEMA = vol.Schema(
    {
        vol.Required("webshop_id"): cv.positive_int,
        vol.Optional("title", default="Unknown"): cv.string,
        vol.Optional("quantity", default=1): cv.positive_int,
    }
)

REMOVE_FROM_LIST_SCHEMA = vol.Schema(
    {
        vol.Required("webshop_id"): cv.positive_int,
    }
)

EXPORT_LIST_SCHEMA = vol.Schema(
    {
        vol.Optional("todo_entity_id"): cv.string,
    }
)


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Register AH Shopping services."""

    async def handle_search_products(call: ServiceCall) -> None:
        """Search for AH products."""
        entry_id = _get_entry_id(hass)
        if not entry_id:
            _LOGGER.error("No AH Shopping config entry found")
            return

        data = hass.data[DOMAIN][entry_id]
        api: AhApiClient = data["api"]
        entry = data["entry"]
        query = call.data["query"]
        limit = call.data.get(
            "limit",
            entry.options.get(CONF_MAX_SEARCH_RESULTS, DEFAULT_MAX_SEARCH_RESULTS),
        )

        try:
            products = await api.search_products(query, limit=limit)
            product_dicts = [p.to_dict() for p in products]

            hass.bus.async_fire(
                EVENT_PRODUCTS_FOUND,
                {"query": query, "products": product_dicts, "count": len(product_dicts)},
            )

            # Build notification message
            lines = [f"Found {len(product_dicts)} products for '{query}':"]
            for p in product_dicts[:5]:
                price_str = f"€{p['price']:.2f}" if p["price"] is not None else "N/A"
                lines.append(f"• {p['title']} ({price_str})")
            if len(product_dicts) > 5:
                lines.append(f"... and {len(product_dicts) - 5} more")

            await hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "AH Shopping – Search Results",
                    "message": "\n".join(lines),
                    "notification_id": f"ah_shopping_search_{query[:20]}",
                },
            )
        except AhError as err:
            _LOGGER.error("Product search failed: %s", err)
            await hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "AH Shopping – Search Failed",
                    "message": str(err),
                    "notification_id": "ah_shopping_search_error",
                },
            )

    async def handle_add_to_list(call: ServiceCall) -> None:
        """Add a product to the local shopping list."""
        entry_id = _get_entry_id(hass)
        if not entry_id:
            return
        storage: ShoppingListStorage = hass.data[DOMAIN][entry_id]["storage"]
        await storage.add_item(
            webshop_id=call.data["webshop_id"],
            title=call.data.get("title", "Unknown"),
            quantity=call.data.get("quantity", 1),
        )
        _fire_list_updated(hass)

    async def handle_remove_from_list(call: ServiceCall) -> None:
        """Remove a product from the local shopping list."""
        entry_id = _get_entry_id(hass)
        if not entry_id:
            return
        storage: ShoppingListStorage = hass.data[DOMAIN][entry_id]["storage"]
        removed = await storage.remove_item(call.data["webshop_id"])
        if removed:
            _fire_list_updated(hass)
        else:
            _LOGGER.warning(
                "Product %s not found on shopping list",
                call.data["webshop_id"],
            )

    async def handle_clear_list(call: ServiceCall) -> None:
        """Clear the local shopping list."""
        entry_id = _get_entry_id(hass)
        if not entry_id:
            return
        storage: ShoppingListStorage = hass.data[DOMAIN][entry_id]["storage"]
        await storage.clear()
        _fire_list_updated(hass)

    async def handle_get_list(call: ServiceCall) -> None:
        """Return the current shopping list via event."""
        entry_id = _get_entry_id(hass)
        if not entry_id:
            return
        storage: ShoppingListStorage = hass.data[DOMAIN][entry_id]["storage"]
        items = storage.get_list()
        hass.bus.async_fire(
            f"{DOMAIN}_list_retrieved",
            {"items": items, "count": len(items)},
        )

    async def handle_refresh_receipts(call: ServiceCall) -> None:
        """Force refresh receipt data."""
        entry_id = _get_entry_id(hass)
        if not entry_id:
            return
        auth: AhAuthManager = hass.data[DOMAIN][entry_id]["auth"]
        if auth.is_anonymous:
            _LOGGER.error("Receipt refresh requires authenticated mode")
            return
        coordinator: AhDataCoordinator = hass.data[DOMAIN][entry_id]["coordinator"]
        await coordinator.async_request_refresh()

    async def handle_export_list_to_todo(call: ServiceCall) -> None:
        """Export shopping list items to a Home Assistant todo list."""
        entry_id = _get_entry_id(hass)
        if not entry_id:
            return
        storage: ShoppingListStorage = hass.data[DOMAIN][entry_id]["storage"]
        items = storage.items

        if not items:
            _LOGGER.info("Shopping list is empty, nothing to export")
            return

        todo_entity_id = call.data.get("todo_entity_id")
        if not todo_entity_id:
            todo_entity_id = _find_todo_entity(hass)

        if not todo_entity_id:
            _LOGGER.error(
                "No todo entity found. Provide todo_entity_id or add a todo integration."
            )
            return

        for item in items:
            summary = f"{item.title} (x{item.quantity})"
            try:
                await hass.services.async_call(
                    "todo",
                    "add_item",
                    {"entity_id": todo_entity_id, "item": summary},
                    blocking=False,
                )
            except Exception as err:
                _LOGGER.error(
                    "Failed to add item to todo %s: %s",
                    todo_entity_id,
                    type(err).__name__,
                )

        _LOGGER.info(
            "Exported %d items to todo entity %s", len(items), todo_entity_id
        )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SEARCH_PRODUCTS,
        handle_search_products,
        schema=SEARCH_PRODUCTS_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN, SERVICE_ADD_TO_LIST, handle_add_to_list, schema=ADD_TO_LIST_SCHEMA
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_REMOVE_FROM_LIST,
        handle_remove_from_list,
        schema=REMOVE_FROM_LIST_SCHEMA,
    )
    hass.services.async_register(DOMAIN, SERVICE_CLEAR_LIST, handle_clear_list)
    hass.services.async_register(DOMAIN, SERVICE_GET_LIST, handle_get_list)
    hass.services.async_register(DOMAIN, SERVICE_REFRESH_RECEIPTS, handle_refresh_receipts)
    hass.services.async_register(
        DOMAIN,
        SERVICE_EXPORT_LIST_TO_TODO,
        handle_export_list_to_todo,
        schema=EXPORT_LIST_SCHEMA,
    )


def _get_entry_id(hass: HomeAssistant) -> str | None:
    """Return the first config entry ID for this domain."""
    entries = hass.config_entries.async_entries(DOMAIN)
    return entries[0].entry_id if entries else None


def _fire_list_updated(hass: HomeAssistant) -> None:
    """Fire a shopping list updated event."""
    hass.bus.async_fire(f"{DOMAIN}_list_updated")


def _find_todo_entity(hass: HomeAssistant) -> str | None:
    """Find the first available todo entity."""
    entity_registry_instance = er.async_get(hass)
    for entity in entity_registry_instance.entities.values():
        if entity.domain == "todo":
            return entity.entity_id
    return None
