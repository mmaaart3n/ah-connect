"""Home Assistant services for AH Connect."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import HomeAssistantError
from .api import AhConnectApiClient
from .const import DOMAIN, EVENT_RESULT, OPT_EXPERIMENTAL_ORDER_ENABLED
from .exceptions import (
    AhAuthenticatedModeRequired,
    AhExperimentalFeatureDisabled,
)

_LOGGER = logging.getLogger(__name__)

SERVICE_SEARCH_PRODUCTS = "search_products"
SERVICE_SEARCH_PRODUCTS_FILTERED = "search_products_filtered"
SERVICE_GET_PRODUCT = "get_product"
SERVICE_GET_PRODUCT_FULL = "get_product_full"
SERVICE_GET_PRODUCTS_BY_IDS = "get_products_by_ids"
SERVICE_GET_BONUS_PRODUCTS = "get_bonus_products"
SERVICE_GET_KOOPJES = "get_koopjes"
SERVICE_GET_MEMBER = "get_member"
SERVICE_GET_RECEIPTS = "get_receipts"
SERVICE_GET_RECEIPT = "get_receipt"
SERVICE_GET_SHOPPING_LISTS = "get_shopping_lists"
SERVICE_GET_SHOPPING_LIST_ITEMS = "get_shopping_list_items"
SERVICE_ADD_PRODUCT_TO_SHOPPING_LIST = "add_product_to_shopping_list"
SERVICE_ADD_FREE_TEXT_TO_SHOPPING_LIST = "add_free_text_to_shopping_list"
SERVICE_ADD_TO_SHOPPING_LIST = "add_to_shopping_list"
SERVICE_CLEAR_SHOPPING_LIST = "clear_shopping_list"
SERVICE_CHECK_SHOPPING_LIST_ITEM = "check_shopping_list_item"
SERVICE_GET_ORDER = "get_order"
SERVICE_GET_ORDER_DETAILS = "get_order_details"
SERVICE_GET_ORDER_SUMMARY = "get_order_summary"
SERVICE_ADD_TO_ORDER = "add_to_order"
SERVICE_REMOVE_FROM_ORDER = "remove_from_order"
SERVICE_UPDATE_ORDER_ITEM = "update_order_item"
SERVICE_REOPEN_ORDER = "reopen_order"
SERVICE_REVERT_ORDER = "revert_order"
SERVICE_GET_FULFILLMENTS = "get_fulfillments"
SERVICE_SEARCH_STORES = "search_stores"

ATTR_CONFIG_ENTRY = "config_entry"
ATTR_QUERY = "query"
ATTR_LIMIT = "limit"
ATTR_BONUS_ONLY = "bonus_only"
ATTR_PRODUCT_ID = "product_id"
ATTR_PRODUCT_IDS = "product_ids"
ATTR_POSTAL_CODE = "postal_code"
ATTR_TRANSACTION_ID = "transaction_id"
ATTR_LIST_ID = "list_id"
ATTR_ITEM_ID = "item_id"
ATTR_NAME = "name"
ATTR_QUANTITY = "quantity"
ATTR_CHECKED = "checked"
ATTR_ORDER_ID = "order_id"


def _get_api(hass: HomeAssistant, call: ServiceCall) -> AhConnectApiClient:
    entry_id = call.data.get(ATTR_CONFIG_ENTRY)
    domain_data = hass.data.get(DOMAIN, {})
    if entry_id and entry_id in domain_data:
        return domain_data[entry_id]["api"]
    if domain_data:
        first = next(iter(k for k in domain_data if k != "services_registered"), None)
        if first:
            return domain_data[first]["api"]
    raise HomeAssistantError("No AH Connect config entry found")


def _fire_result(hass: HomeAssistant, call: ServiceCall, result: Any) -> None:
    hass.bus.async_fire(
        EVENT_RESULT,
        {
            "service": call.service,
            "result": result,
        },
    )


def _require_experimental(api: AhConnectApiClient) -> None:
    if not api.options.get(OPT_EXPERIMENTAL_ORDER_ENABLED):
        raise HomeAssistantError(
            "Experimental order features are disabled in integration options"
        )


async def _handle_search_products(hass: HomeAssistant, call: ServiceCall) -> None:
    api = _get_api(hass, call)
    products = await api.search_products(
        call.data[ATTR_QUERY], call.data.get(ATTR_LIMIT, 10)
    )
    _fire_result(hass, call, [p.to_dict() for p in products])


async def _handle_search_filtered(hass: HomeAssistant, call: ServiceCall) -> None:
    api = _get_api(hass, call)
    products = await api.search_products_filtered(
        query=call.data[ATTR_QUERY],
        limit=call.data.get(ATTR_LIMIT, 10),
        bonus_only=call.data.get(ATTR_BONUS_ONLY, False),
    )
    _fire_result(hass, call, [p.to_dict() for p in products])


async def _handle_get_product(hass: HomeAssistant, call: ServiceCall) -> None:
    api = _get_api(hass, call)
    product = await api.get_product(call.data[ATTR_PRODUCT_ID])
    _fire_result(hass, call, product.to_dict())


async def _handle_get_product_full(hass: HomeAssistant, call: ServiceCall) -> None:
    api = _get_api(hass, call)
    product = await api.get_product_full(call.data[ATTR_PRODUCT_ID])
    _fire_result(hass, call, product.to_dict())


async def _handle_get_products_by_ids(hass: HomeAssistant, call: ServiceCall) -> None:
    api = _get_api(hass, call)
    products = await api.get_products_by_ids(call.data[ATTR_PRODUCT_IDS])
    _fire_result(hass, call, [p.to_dict() for p in products])


async def _handle_get_bonus(hass: HomeAssistant, call: ServiceCall) -> None:
    api = _get_api(hass, call)
    products = await api.get_bonus_products()
    _fire_result(hass, call, [p.to_dict() for p in products])


async def _handle_get_koopjes(hass: HomeAssistant, call: ServiceCall) -> None:
    api = _get_api(hass, call)
    postal = call.data[ATTR_POSTAL_CODE]
    koopjes = await api.get_koopjes(postal)
    _fire_result(hass, call, [k.to_dict() for k in koopjes])


async def _handle_get_member(hass: HomeAssistant, call: ServiceCall) -> None:
    api = _get_api(hass, call)
    try:
        member = await api.get_member()
    except AhAuthenticatedModeRequired as err:
        raise HomeAssistantError(str(err)) from err
    _fire_result(hass, call, member.to_dict())


async def _handle_get_receipts(hass: HomeAssistant, call: ServiceCall) -> None:
    api = _get_api(hass, call)
    try:
        receipts = await api.get_receipts()
    except AhAuthenticatedModeRequired as err:
        raise HomeAssistantError(str(err)) from err
    _fire_result(hass, call, [r.to_dict() for r in receipts])


async def _handle_get_receipt(hass: HomeAssistant, call: ServiceCall) -> None:
    api = _get_api(hass, call)
    try:
        receipt = await api.get_receipt(call.data[ATTR_TRANSACTION_ID])
    except AhAuthenticatedModeRequired as err:
        raise HomeAssistantError(str(err)) from err
    _fire_result(hass, call, receipt.to_dict())


async def _handle_get_shopping_lists(hass: HomeAssistant, call: ServiceCall) -> None:
    api = _get_api(hass, call)
    try:
        lists = await api.get_shopping_lists(call.data.get(ATTR_PRODUCT_ID))
    except AhAuthenticatedModeRequired as err:
        raise HomeAssistantError(str(err)) from err
    _fire_result(hass, call, [lst.to_dict() for lst in lists])


async def _handle_get_list_items(hass: HomeAssistant, call: ServiceCall) -> None:
    api = _get_api(hass, call)
    try:
        items = await api.get_shopping_list_items(call.data[ATTR_LIST_ID])
    except AhAuthenticatedModeRequired as err:
        raise HomeAssistantError(str(err)) from err
    _fire_result(hass, call, [i.to_dict() for i in items])


async def _handle_add_product_list(hass: HomeAssistant, call: ServiceCall) -> None:
    api = _get_api(hass, call)
    try:
        await api.add_product_to_shopping_list(
            call.data[ATTR_PRODUCT_ID], call.data.get(ATTR_QUANTITY, 1)
        )
    except AhAuthenticatedModeRequired as err:
        raise HomeAssistantError(str(err)) from err
    _fire_result(hass, call, {"success": True})


async def _handle_add_free_text(hass: HomeAssistant, call: ServiceCall) -> None:
    api = _get_api(hass, call)
    try:
        await api.add_free_text_to_shopping_list(
            call.data[ATTR_NAME], call.data.get(ATTR_QUANTITY, 1)
        )
    except AhAuthenticatedModeRequired as err:
        raise HomeAssistantError(str(err)) from err
    _fire_result(hass, call, {"success": True})


async def _handle_add_to_list(hass: HomeAssistant, call: ServiceCall) -> None:
    api = _get_api(hass, call)
    try:
        await api.add_to_shopping_list(
            list_id=call.data.get(ATTR_LIST_ID, ""),
            product_id=call.data.get(ATTR_PRODUCT_ID),
            name=call.data.get(ATTR_NAME),
            quantity=call.data.get(ATTR_QUANTITY, 1),
        )
    except AhAuthenticatedModeRequired as err:
        raise HomeAssistantError(str(err)) from err
    _fire_result(hass, call, {"success": True})


async def _handle_clear_list(hass: HomeAssistant, call: ServiceCall) -> None:
    api = _get_api(hass, call)
    try:
        await api.clear_shopping_list(call.data[ATTR_LIST_ID])
    except AhAuthenticatedModeRequired as err:
        raise HomeAssistantError(str(err)) from err
    _fire_result(hass, call, {"success": True})


async def _handle_check_item(hass: HomeAssistant, call: ServiceCall) -> None:
    api = _get_api(hass, call)
    try:
        await api.check_shopping_list_item(
            call.data[ATTR_LIST_ID],
            call.data[ATTR_ITEM_ID],
            call.data[ATTR_CHECKED],
        )
    except AhAuthenticatedModeRequired as err:
        raise HomeAssistantError(str(err)) from err
    _fire_result(hass, call, {"success": True})


async def _handle_get_order(hass: HomeAssistant, call: ServiceCall) -> None:
    api = _get_api(hass, call)
    _require_experimental(api)
    try:
        order = await api.get_order()
    except (AhAuthenticatedModeRequired, AhExperimentalFeatureDisabled) as err:
        raise HomeAssistantError(str(err)) from err
    _fire_result(hass, call, order.to_dict())


async def _handle_get_order_details(hass: HomeAssistant, call: ServiceCall) -> None:
    api = _get_api(hass, call)
    _require_experimental(api)
    try:
        order = await api.get_order_details(call.data[ATTR_ORDER_ID])
    except AhAuthenticatedModeRequired as err:
        raise HomeAssistantError(str(err)) from err
    _fire_result(hass, call, order.to_dict())


async def _handle_get_order_summary(hass: HomeAssistant, call: ServiceCall) -> None:
    api = _get_api(hass, call)
    _require_experimental(api)
    try:
        summary = await api.get_order_summary()
    except AhAuthenticatedModeRequired as err:
        raise HomeAssistantError(str(err)) from err
    _fire_result(hass, call, summary.to_dict())


async def _handle_add_to_order(hass: HomeAssistant, call: ServiceCall) -> None:
    api = _get_api(hass, call)
    _require_experimental(api)
    try:
        await api.add_to_order(
            call.data[ATTR_PRODUCT_ID], call.data.get(ATTR_QUANTITY, 1)
        )
    except AhAuthenticatedModeRequired as err:
        raise HomeAssistantError(str(err)) from err
    _fire_result(hass, call, {"success": True})


async def _handle_remove_from_order(hass: HomeAssistant, call: ServiceCall) -> None:
    api = _get_api(hass, call)
    _require_experimental(api)
    try:
        await api.remove_from_order(call.data[ATTR_PRODUCT_ID])
    except AhAuthenticatedModeRequired as err:
        raise HomeAssistantError(str(err)) from err
    _fire_result(hass, call, {"success": True})


async def _handle_update_order_item(hass: HomeAssistant, call: ServiceCall) -> None:
    api = _get_api(hass, call)
    _require_experimental(api)
    try:
        await api.update_order_item(
            call.data[ATTR_PRODUCT_ID], call.data[ATTR_QUANTITY]
        )
    except AhAuthenticatedModeRequired as err:
        raise HomeAssistantError(str(err)) from err
    _fire_result(hass, call, {"success": True})


async def _handle_reopen_order(hass: HomeAssistant, call: ServiceCall) -> None:
    api = _get_api(hass, call)
    _require_experimental(api)
    try:
        await api.reopen_order(call.data[ATTR_ORDER_ID])
    except AhAuthenticatedModeRequired as err:
        raise HomeAssistantError(str(err)) from err
    _fire_result(hass, call, {"success": True})


async def _handle_revert_order(hass: HomeAssistant, call: ServiceCall) -> None:
    api = _get_api(hass, call)
    _require_experimental(api)
    try:
        await api.revert_order(call.data[ATTR_ORDER_ID])
    except AhAuthenticatedModeRequired as err:
        raise HomeAssistantError(str(err)) from err
    _fire_result(hass, call, {"success": True})


async def _handle_get_fulfillments(hass: HomeAssistant, call: ServiceCall) -> None:
    api = _get_api(hass, call)
    _require_experimental(api)
    try:
        fulfillments = await api.get_fulfillments()
    except AhAuthenticatedModeRequired as err:
        raise HomeAssistantError(str(err)) from err
    _fire_result(hass, call, [f.to_dict() for f in fulfillments])


async def _handle_search_stores(hass: HomeAssistant, call: ServiceCall) -> None:
    api = _get_api(hass, call)
    stores = await api.search_stores(
        query=call.data.get("query"),
        postal_code=call.data.get(ATTR_POSTAL_CODE),
    )
    _fire_result(hass, call, [s.to_dict() for s in stores])


SERVICE_HANDLERS = {
    SERVICE_SEARCH_PRODUCTS: _handle_search_products,
    SERVICE_SEARCH_PRODUCTS_FILTERED: _handle_search_filtered,
    SERVICE_GET_PRODUCT: _handle_get_product,
    SERVICE_GET_PRODUCT_FULL: _handle_get_product_full,
    SERVICE_GET_PRODUCTS_BY_IDS: _handle_get_products_by_ids,
    SERVICE_GET_BONUS_PRODUCTS: _handle_get_bonus,
    SERVICE_GET_KOOPJES: _handle_get_koopjes,
    SERVICE_GET_MEMBER: _handle_get_member,
    SERVICE_GET_RECEIPTS: _handle_get_receipts,
    SERVICE_GET_RECEIPT: _handle_get_receipt,
    SERVICE_GET_SHOPPING_LISTS: _handle_get_shopping_lists,
    SERVICE_GET_SHOPPING_LIST_ITEMS: _handle_get_list_items,
    SERVICE_ADD_PRODUCT_TO_SHOPPING_LIST: _handle_add_product_list,
    SERVICE_ADD_FREE_TEXT_TO_SHOPPING_LIST: _handle_add_free_text,
    SERVICE_ADD_TO_SHOPPING_LIST: _handle_add_to_list,
    SERVICE_CLEAR_SHOPPING_LIST: _handle_clear_list,
    SERVICE_CHECK_SHOPPING_LIST_ITEM: _handle_check_item,
    SERVICE_GET_ORDER: _handle_get_order,
    SERVICE_GET_ORDER_DETAILS: _handle_get_order_details,
    SERVICE_GET_ORDER_SUMMARY: _handle_get_order_summary,
    SERVICE_ADD_TO_ORDER: _handle_add_to_order,
    SERVICE_REMOVE_FROM_ORDER: _handle_remove_from_order,
    SERVICE_UPDATE_ORDER_ITEM: _handle_update_order_item,
    SERVICE_REOPEN_ORDER: _handle_reopen_order,
    SERVICE_REVERT_ORDER: _handle_revert_order,
    SERVICE_GET_FULFILLMENTS: _handle_get_fulfillments,
    SERVICE_SEARCH_STORES: _handle_search_stores,
}


async def async_setup_services(hass: HomeAssistant) -> None:
    """Register AH Connect services."""

    @callback
    def _create_handler(name: str):
        async def handler(call: ServiceCall) -> None:
            await SERVICE_HANDLERS[name](hass, call)

        return handler

    for service_name in SERVICE_HANDLERS:
        if hass.services.has_service(DOMAIN, service_name):
            continue
        hass.services.async_register(
            DOMAIN,
            service_name,
            _create_handler(service_name),
        )


async def async_unload_services(hass: HomeAssistant) -> None:
    """Unregister services."""
    for service_name in SERVICE_HANDLERS:
        if hass.services.has_service(DOMAIN, service_name):
            hass.services.async_remove(DOMAIN, service_name)
