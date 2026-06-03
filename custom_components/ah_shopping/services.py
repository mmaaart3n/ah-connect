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
    EVENT_RESULT,
)
from .coordinator import AhDataCoordinator
from .exceptions import AhAuthError, AhError, AhExperimentalFeatureDisabled
from .storage import ShoppingListStorage

_LOGGER = logging.getLogger(__name__)

# Backward-compatible local list service names
SERVICE_SEARCH_PRODUCTS = "search_products"
SERVICE_GET_PRODUCT = "get_product"
SERVICE_GET_BONUS_PRODUCTS = "get_bonus_products"
SERVICE_ADD_TO_LIST = "add_to_list"
SERVICE_REMOVE_FROM_LIST = "remove_from_list"
SERVICE_CLEAR_LIST = "clear_list"
SERVICE_GET_LIST = "get_list"
SERVICE_ADD_TO_LOCAL_LIST = "add_to_local_list"
SERVICE_REMOVE_FROM_LOCAL_LIST = "remove_from_local_list"
SERVICE_CLEAR_LOCAL_LIST = "clear_local_list"
SERVICE_EXPORT_LIST_TO_TODO = "export_list_to_todo"
SERVICE_EXPORT_LOCAL_LIST_TO_TODO = "export_local_list_to_todo"
SERVICE_REFRESH_RECEIPTS = "refresh_receipts"
SERVICE_GET_RECEIPT = "get_receipt"
SERVICE_GET_SHOPPING_LISTS = "get_shopping_lists"
SERVICE_GET_SHOPPING_LIST_ITEMS = "get_shopping_list_items"
SERVICE_ADD_PRODUCT_TO_SHOPPING_LIST = "add_product_to_shopping_list"
SERVICE_ADD_FREE_TEXT_TO_SHOPPING_LIST = "add_free_text_to_shopping_list"
SERVICE_CLEAR_SHOPPING_LIST = "clear_shopping_list"
SERVICE_CHECK_SHOPPING_LIST_ITEM = "check_shopping_list_item"
SERVICE_GET_ORDER = "get_order"
SERVICE_GET_ORDER_SUMMARY = "get_order_summary"
SERVICE_ADD_TO_ORDER = "add_to_order"
SERVICE_REMOVE_FROM_ORDER = "remove_from_order"
SERVICE_UPDATE_ORDER_ITEM = "update_order_item"


def _fire_result(hass: HomeAssistant, action: str, data: dict[str, Any]) -> None:
    hass.bus.async_fire(EVENT_RESULT, {"action": action, **data})


def _get_entry_id(hass: HomeAssistant) -> str | None:
    entries = hass.config_entries.async_entries(DOMAIN)
    return entries[0].entry_id if entries else None


def _get_ctx(hass: HomeAssistant) -> dict[str, Any] | None:
    entry_id = _get_entry_id(hass)
    if not entry_id:
        return None
    return hass.data.get(DOMAIN, {}).get(entry_id)


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Register all AH Shopping services."""

    async def _api(call: ServiceCall) -> AhApiClient | None:
        ctx = _get_ctx(hass)
        return ctx["api"] if ctx else None

    async def handle_search_products(call: ServiceCall) -> None:
        ctx = _get_ctx(hass)
        if not ctx:
            return
        api: AhApiClient = ctx["api"]
        entry = ctx["entry"]
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
            _fire_result(hass, SERVICE_SEARCH_PRODUCTS, {"products": product_dicts})
        except AhError as err:
            _LOGGER.error("search_products failed: %s", err)
            _fire_result(hass, SERVICE_SEARCH_PRODUCTS, {"error": str(err)})

    async def handle_get_product(call: ServiceCall) -> None:
        api = await _api(call)
        if not api:
            return
        try:
            product = await api.get_product(call.data["webshop_id"])
            _fire_result(hass, SERVICE_GET_PRODUCT, {"product": product.to_dict()})
        except AhError as err:
            _fire_result(hass, SERVICE_GET_PRODUCT, {"error": str(err)})

    async def handle_get_bonus_products(call: ServiceCall) -> None:
        api = await _api(call)
        if not api:
            return
        try:
            products = await api.get_bonus_products()
            _fire_result(
                hass,
                SERVICE_GET_BONUS_PRODUCTS,
                {"products": [p.to_dict() for p in products], "count": len(products)},
            )
        except AhError as err:
            _fire_result(hass, SERVICE_GET_BONUS_PRODUCTS, {"error": str(err)})

    async def _handle_add_local(call: ServiceCall) -> None:
        ctx = _get_ctx(hass)
        if not ctx:
            return
        storage: ShoppingListStorage = ctx["storage"]
        await storage.add_item(
            webshop_id=call.data["webshop_id"],
            title=call.data.get("title", "Unknown"),
            quantity=call.data.get("quantity", 1),
        )
        hass.bus.async_fire(f"{DOMAIN}_list_updated")

    async def _handle_remove_local(call: ServiceCall) -> None:
        ctx = _get_ctx(hass)
        if not ctx:
            return
        storage: ShoppingListStorage = ctx["storage"]
        await storage.remove_item(call.data["webshop_id"])
        hass.bus.async_fire(f"{DOMAIN}_list_updated")

    async def _handle_clear_local(call: ServiceCall) -> None:
        ctx = _get_ctx(hass)
        if not ctx:
            return
        storage: ShoppingListStorage = ctx["storage"]
        await storage.clear()
        hass.bus.async_fire(f"{DOMAIN}_list_updated")

    async def handle_get_list(call: ServiceCall) -> None:
        ctx = _get_ctx(hass)
        if not ctx:
            return
        items = ctx["storage"].get_list()
        _fire_result(hass, SERVICE_GET_LIST, {"items": items, "count": len(items)})

    async def handle_export_todo(call: ServiceCall) -> None:
        ctx = _get_ctx(hass)
        if not ctx:
            return
        items = ctx["storage"].items
        todo_entity_id = call.data.get("todo_entity_id") or _find_todo_entity(hass)
        if not todo_entity_id:
            _LOGGER.error("No todo entity found")
            return
        for item in items:
            await hass.services.async_call(
                "todo",
                "add_item",
                {"entity_id": todo_entity_id, "item": f"{item.title} (x{item.quantity})"},
                blocking=False,
            )

    async def handle_refresh_receipts(call: ServiceCall) -> None:
        ctx = _get_ctx(hass)
        if not ctx:
            return
        if ctx["auth"].is_anonymous:
            _fire_result(hass, SERVICE_REFRESH_RECEIPTS, {"error": "Requires authenticated mode"})
            return
        coordinator: AhDataCoordinator = ctx["coordinator"]
        await coordinator.async_request_refresh()

    async def handle_get_receipt(call: ServiceCall) -> None:
        api = await _api(call)
        if not api:
            return
        try:
            receipt = await api.get_receipt(call.data["transaction_id"])
            _fire_result(
                hass,
                SERVICE_GET_RECEIPT,
                {
                    "transaction_id": receipt.transaction_id,
                    "total": receipt.total,
                    "items": [
                        {
                            "description": i.description,
                            "quantity": i.quantity,
                            "amount": i.amount,
                        }
                        for i in receipt.items
                    ],
                },
            )
        except AhError as err:
            _fire_result(hass, SERVICE_GET_RECEIPT, {"error": str(err)})

    async def handle_get_shopping_lists(call: ServiceCall) -> None:
        api = await _api(call)
        if not api:
            return
        try:
            lists = await api.get_shopping_lists()
            _fire_result(
                hass,
                SERVICE_GET_SHOPPING_LISTS,
                {
                    "lists": [
                        {"list_id": lst.list_id, "name": lst.name, "item_count": lst.item_count}
                        for lst in lists
                    ]
                },
            )
        except AhAuthError as err:
            _fire_result(hass, SERVICE_GET_SHOPPING_LISTS, {"error": str(err)})
        except AhError as err:
            _fire_result(hass, SERVICE_GET_SHOPPING_LISTS, {"error": str(err)})

    async def handle_get_shopping_list_items(call: ServiceCall) -> None:
        api = await _api(call)
        if not api:
            return
        try:
            list_id = call.data.get("list_id")
            if not list_id:
                lists = await api.get_shopping_lists()
                list_id = lists[0].list_id if lists else None
            if not list_id:
                _fire_result(hass, SERVICE_GET_SHOPPING_LIST_ITEMS, {"items": []})
                return
            items = await api.get_shopping_list_items(list_id)
            _fire_result(
                hass,
                SERVICE_GET_SHOPPING_LIST_ITEMS,
                {
                    "items": [
                        {
                            "item_id": i.item_id,
                            "product_id": i.product_id,
                            "quantity": i.quantity,
                        }
                        for i in items
                    ]
                },
            )
        except AhError as err:
            _fire_result(hass, SERVICE_GET_SHOPPING_LIST_ITEMS, {"error": str(err)})

    async def handle_add_product_shopping_list(call: ServiceCall) -> None:
        api = await _api(call)
        if not api:
            return
        try:
            await api.add_product_to_shopping_list(
                call.data["webshop_id"], call.data.get("quantity", 1)
            )
            _fire_result(hass, SERVICE_ADD_PRODUCT_TO_SHOPPING_LIST, {"success": True})
        except AhError as err:
            _fire_result(hass, SERVICE_ADD_PRODUCT_TO_SHOPPING_LIST, {"error": str(err)})

    async def handle_add_free_text_shopping_list(call: ServiceCall) -> None:
        api = await _api(call)
        if not api:
            return
        try:
            await api.add_free_text_to_shopping_list(
                call.data["name"], call.data.get("quantity", 1)
            )
            _fire_result(hass, SERVICE_ADD_FREE_TEXT_TO_SHOPPING_LIST, {"success": True})
        except AhError as err:
            _fire_result(hass, SERVICE_ADD_FREE_TEXT_TO_SHOPPING_LIST, {"error": str(err)})

    async def handle_clear_shopping_list(call: ServiceCall) -> None:
        api = await _api(call)
        if not api:
            return
        try:
            await api.clear_shopping_list()
            _fire_result(hass, SERVICE_CLEAR_SHOPPING_LIST, {"success": True})
        except AhError as err:
            _fire_result(hass, SERVICE_CLEAR_SHOPPING_LIST, {"error": str(err)})

    async def handle_check_shopping_list_item(call: ServiceCall) -> None:
        api = await _api(call)
        if not api:
            return
        try:
            await api.check_shopping_list_item(
                call.data["item_id"], call.data.get("checked", True)
            )
            _fire_result(hass, SERVICE_CHECK_SHOPPING_LIST_ITEM, {"success": True})
        except AhError as err:
            _fire_result(hass, SERVICE_CHECK_SHOPPING_LIST_ITEM, {"error": str(err)})

    async def handle_get_order(call: ServiceCall) -> None:
        api = await _api(call)
        if not api:
            return
        try:
            order = await api.get_order()
            _fire_result(
                hass,
                SERVICE_GET_ORDER,
                {
                    "order_id": order.order_id,
                    "state": order.state,
                    "total_price": order.total_price,
                    "item_count": order.item_count,
                },
            )
        except (AhExperimentalFeatureDisabled, AhAuthError, AhError) as err:
            _fire_result(hass, SERVICE_GET_ORDER, {"error": str(err)})

    async def handle_get_order_summary(call: ServiceCall) -> None:
        api = await _api(call)
        if not api:
            return
        try:
            summary = await api.get_order_summary()
            _fire_result(
                hass,
                SERVICE_GET_ORDER_SUMMARY,
                {
                    "total_items": summary.total_items,
                    "total_price": summary.total_price,
                    "total_discount": summary.total_discount,
                },
            )
        except (AhExperimentalFeatureDisabled, AhAuthError, AhError) as err:
            _fire_result(hass, SERVICE_GET_ORDER_SUMMARY, {"error": str(err)})

    async def handle_add_to_order(call: ServiceCall) -> None:
        api = await _api(call)
        if not api:
            return
        try:
            await api.add_to_order(call.data["webshop_id"], call.data.get("quantity", 1))
            _fire_result(hass, SERVICE_ADD_TO_ORDER, {"success": True})
        except (AhExperimentalFeatureDisabled, AhError) as err:
            _fire_result(hass, SERVICE_ADD_TO_ORDER, {"error": str(err)})

    async def handle_remove_from_order(call: ServiceCall) -> None:
        api = await _api(call)
        if not api:
            return
        try:
            await api.remove_from_order(call.data["webshop_id"])
            _fire_result(hass, SERVICE_REMOVE_FROM_ORDER, {"success": True})
        except (AhExperimentalFeatureDisabled, AhError) as err:
            _fire_result(hass, SERVICE_REMOVE_FROM_ORDER, {"error": str(err)})

    async def handle_update_order_item(call: ServiceCall) -> None:
        api = await _api(call)
        if not api:
            return
        try:
            await api.update_order_item(
                call.data["webshop_id"], call.data.get("quantity", 1)
            )
            _fire_result(hass, SERVICE_UPDATE_ORDER_ITEM, {"success": True})
        except (AhExperimentalFeatureDisabled, AhError) as err:
            _fire_result(hass, SERVICE_UPDATE_ORDER_ITEM, {"error": str(err)})

    schemas = {
        SERVICE_SEARCH_PRODUCTS: vol.Schema(
            {
                vol.Required("query"): cv.string,
                vol.Optional("limit", default=10): vol.All(cv.positive_int, vol.Range(max=50)),
            }
        ),
        SERVICE_GET_PRODUCT: vol.Schema({vol.Required("webshop_id"): cv.positive_int}),
        SERVICE_GET_BONUS_PRODUCTS: vol.Schema({}),
        SERVICE_ADD_TO_LIST: vol.Schema(
            {
                vol.Required("webshop_id"): cv.positive_int,
                vol.Optional("title", default="Unknown"): cv.string,
                vol.Optional("quantity", default=1): cv.positive_int,
            }
        ),
        SERVICE_REMOVE_FROM_LIST: vol.Schema({vol.Required("webshop_id"): cv.positive_int}),
        SERVICE_CLEAR_LIST: vol.Schema({}),
        SERVICE_GET_LIST: vol.Schema({}),
        SERVICE_ADD_TO_LOCAL_LIST: vol.Schema(
            {
                vol.Required("webshop_id"): cv.positive_int,
                vol.Optional("title", default="Unknown"): cv.string,
                vol.Optional("quantity", default=1): cv.positive_int,
            }
        ),
        SERVICE_REMOVE_FROM_LOCAL_LIST: vol.Schema({vol.Required("webshop_id"): cv.positive_int}),
        SERVICE_CLEAR_LOCAL_LIST: vol.Schema({}),
        SERVICE_EXPORT_LIST_TO_TODO: vol.Schema({vol.Optional("todo_entity_id"): cv.string}),
        SERVICE_EXPORT_LOCAL_LIST_TO_TODO: vol.Schema({vol.Optional("todo_entity_id"): cv.string}),
        SERVICE_REFRESH_RECEIPTS: vol.Schema({}),
        SERVICE_GET_RECEIPT: vol.Schema({vol.Required("transaction_id"): cv.string}),
        SERVICE_GET_SHOPPING_LISTS: vol.Schema({}),
        SERVICE_GET_SHOPPING_LIST_ITEMS: vol.Schema({vol.Optional("list_id"): cv.string}),
        SERVICE_ADD_PRODUCT_TO_SHOPPING_LIST: vol.Schema(
            {
                vol.Required("webshop_id"): cv.positive_int,
                vol.Optional("quantity", default=1): cv.positive_int,
            }
        ),
        SERVICE_ADD_FREE_TEXT_TO_SHOPPING_LIST: vol.Schema(
            {
                vol.Required("name"): cv.string,
                vol.Optional("quantity", default=1): cv.positive_int,
            }
        ),
        SERVICE_CLEAR_SHOPPING_LIST: vol.Schema({}),
        SERVICE_CHECK_SHOPPING_LIST_ITEM: vol.Schema(
            {
                vol.Required("item_id"): cv.string,
                vol.Optional("checked", default=True): cv.boolean,
            }
        ),
        SERVICE_GET_ORDER: vol.Schema({}),
        SERVICE_GET_ORDER_SUMMARY: vol.Schema({}),
        SERVICE_ADD_TO_ORDER: vol.Schema(
            {
                vol.Required("webshop_id"): cv.positive_int,
                vol.Optional("quantity", default=1): cv.positive_int,
            }
        ),
        SERVICE_REMOVE_FROM_ORDER: vol.Schema({vol.Required("webshop_id"): cv.positive_int}),
        SERVICE_UPDATE_ORDER_ITEM: vol.Schema(
            {
                vol.Required("webshop_id"): cv.positive_int,
                vol.Optional("quantity", default=1): cv.positive_int,
            }
        ),
    }

    handlers = {
        SERVICE_SEARCH_PRODUCTS: handle_search_products,
        SERVICE_GET_PRODUCT: handle_get_product,
        SERVICE_GET_BONUS_PRODUCTS: handle_get_bonus_products,
        SERVICE_ADD_TO_LIST: _handle_add_local,
        SERVICE_REMOVE_FROM_LIST: _handle_remove_local,
        SERVICE_CLEAR_LIST: _handle_clear_local,
        SERVICE_GET_LIST: handle_get_list,
        SERVICE_ADD_TO_LOCAL_LIST: _handle_add_local,
        SERVICE_REMOVE_FROM_LOCAL_LIST: _handle_remove_local,
        SERVICE_CLEAR_LOCAL_LIST: _handle_clear_local,
        SERVICE_EXPORT_LIST_TO_TODO: handle_export_todo,
        SERVICE_EXPORT_LOCAL_LIST_TO_TODO: handle_export_todo,
        SERVICE_REFRESH_RECEIPTS: handle_refresh_receipts,
        SERVICE_GET_RECEIPT: handle_get_receipt,
        SERVICE_GET_SHOPPING_LISTS: handle_get_shopping_lists,
        SERVICE_GET_SHOPPING_LIST_ITEMS: handle_get_shopping_list_items,
        SERVICE_ADD_PRODUCT_TO_SHOPPING_LIST: handle_add_product_shopping_list,
        SERVICE_ADD_FREE_TEXT_TO_SHOPPING_LIST: handle_add_free_text_shopping_list,
        SERVICE_CLEAR_SHOPPING_LIST: handle_clear_shopping_list,
        SERVICE_CHECK_SHOPPING_LIST_ITEM: handle_check_shopping_list_item,
        SERVICE_GET_ORDER: handle_get_order,
        SERVICE_GET_ORDER_SUMMARY: handle_get_order_summary,
        SERVICE_ADD_TO_ORDER: handle_add_to_order,
        SERVICE_REMOVE_FROM_ORDER: handle_remove_from_order,
        SERVICE_UPDATE_ORDER_ITEM: handle_update_order_item,
    }

    for service, handler in handlers.items():
        if not hass.services.has_service(DOMAIN, service):
            hass.services.async_register(DOMAIN, service, handler, schema=schemas[service])


def _find_todo_entity(hass: HomeAssistant) -> str | None:
    for entity in er.async_get(hass).entities.values():
        if entity.domain == "todo":
            return entity.entity_id
    return None
