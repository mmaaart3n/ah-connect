"""AH API client for the AH Shopping integration (appie-go reference)."""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import date
from typing import Any

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .auth import AhAuthManager
from .const import (
    API_BASE,
    APPLICATION_HEADER,
    BONUS_METADATA,
    BONUS_SECTION,
    CLIENT_VERSION,
    CONF_EXPERIMENTAL_ORDER,
    DEFAULT_TIMEOUT,
    GQL_FAVORITE_LIST_V2,
    GQL_FETCH_MEMBER,
    GQL_FETCH_POS_RECEIPTS,
    GQL_FETCH_RECEIPT,
    GQL_ORDER_FULFILLMENTS,
    GRAPHQL_PATH,
    MIN_REQUEST_INTERVAL,
    ORDER_ACTIVE_SUMMARY,
    ORDER_DETAILS,
    ORDER_ITEMS,
    PRODUCT_DETAIL,
    PRODUCT_SEARCH,
    PRODUCT_SEARCH_BY_IDS,
    RECEIPT_DETAIL_LEGACY,
    RECEIPTS_LEGACY,
    SHOPPING_LIST_ITEM_CHECK,
    SHOPPING_LIST_ITEMS_V2,
    SHOPPING_LISTS_V3,
    USER_AGENT,
)
from .exceptions import (
    AhApiError,
    AhAuthError,
    AhExperimentalFeatureDisabled,
    AhNotImplementedError,
    AhRateLimitError,
    AhUnavailableError,
)
from .models import (
    AhFulfillment,
    AhMember,
    AhOrder,
    AhOrderItem,
    AhOrderSummary,
    AhProduct,
    AhReceipt,
    AhShoppingList,
    AhShoppingListItem,
)

_LOGGER = logging.getLogger(__name__)


class AhApiClient:
    """Async client for the Albert Heijn mobile API."""

    def __init__(
        self,
        hass: HomeAssistant,
        auth: AhAuthManager,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the API client."""
        self._hass = hass
        self._auth = auth
        self._entry = entry
        self._session = async_get_clientsession(hass)
        self._lock = asyncio.Lock()
        self._last_request: float = 0.0
        self._order_id: str | None = None

    @property
    def options(self) -> dict[str, Any]:
        """Return config entry options."""
        return self._entry.options

    def _require_authenticated(self) -> None:
        if self._auth.is_anonymous:
            raise AhAuthError("This action requires authenticated mode")

    def _require_experimental_order(self) -> None:
        if not self.options.get(CONF_EXPERIMENTAL_ORDER, False):
            raise AhExperimentalFeatureDisabled(
                "Order features are disabled. Enable 'experimental_order_enabled' in options."
            )

    async def _throttle(self) -> None:
        async with self._lock:
            elapsed = time.monotonic() - self._last_request
            if elapsed < MIN_REQUEST_INTERVAL:
                await asyncio.sleep(MIN_REQUEST_INTERVAL - elapsed)
            self._last_request = time.monotonic()

    def _headers(self, *, include_order: bool = False) -> dict[str, str]:
        headers = {
            "User-Agent": USER_AGENT,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "x-application": APPLICATION_HEADER,
            "x-client-name": self._auth.client_id,
            "x-client-version": CLIENT_VERSION,
        }
        if include_order and self._order_id:
            headers["appie-current-order-id"] = self._order_id
        return headers

    async def _request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        require_auth: bool = True,
        include_order: bool = False,
    ) -> Any:
        """HTTP request with retry/backoff."""
        max_retries = 3
        backoff = 1.0

        for attempt in range(max_retries):
            await self._throttle()
            headers = self._headers(include_order=include_order)
            if require_auth:
                token = await self._auth.get_access_token()
                headers["Authorization"] = f"Bearer {token}"

            timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT)
            try:
                async with self._session.request(
                    method,
                    url,
                    params=params,
                    json=json_body,
                    headers=headers,
                    timeout=timeout,
                ) as response:
                    if response.status == 429:
                        if attempt < max_retries - 1:
                            await asyncio.sleep(backoff)
                            backoff *= 2
                            continue
                        raise AhRateLimitError("Rate limit exceeded")

                    if response.status >= 500:
                        if attempt < max_retries - 1:
                            await asyncio.sleep(backoff)
                            backoff *= 2
                            continue
                        raise AhUnavailableError(
                            f"AH API unavailable (HTTP {response.status})"
                        )

                    if response.status == 401:
                        raise AhAuthError("Unauthorized – re-authenticate.")

                    if response.status >= 400:
                        raise AhApiError(f"AH API error (HTTP {response.status})")

                    if response.status == 204:
                        return None
                    return await response.json(content_type=None)

            except aiohttp.ClientError as err:
                if attempt < max_retries - 1:
                    await asyncio.sleep(backoff)
                    backoff *= 2
                    continue
                raise AhUnavailableError(
                    f"Network error: {type(err).__name__}"
                ) from err

        raise AhUnavailableError("Max retries exceeded")

    async def _graphql(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
        *,
        require_auth: bool = True,
    ) -> Any:
        """Execute GraphQL query."""
        body = {"query": query, "variables": variables or {}}
        data = await self._request(
            "POST",
            f"{API_BASE}{GRAPHQL_PATH}",
            json_body=body,
            require_auth=require_auth,
        )
        if not isinstance(data, dict):
            raise AhApiError("Unexpected GraphQL response")
        errors = data.get("errors")
        if errors and isinstance(errors, list):
            msg = errors[0].get("message", "GraphQL error") if errors else "GraphQL error"
            raise AhApiError(str(msg))
        return data.get("data")

    # --- Anonymous / public ---

    async def get_anonymous_token(self) -> dict[str, Any]:
        """Fetch anonymous token (via auth manager)."""
        token = await self._auth.get_access_token()
        return {"access_token": token}

    async def search_products(self, query: str, *, limit: int = 10) -> list[AhProduct]:
        """Search products by query."""
        return await self.search_products_filtered(query=query, limit=limit)

    async def search_products_filtered(
        self,
        query: str,
        *,
        limit: int = 10,
        bonus_only: bool = False,
    ) -> list[AhProduct]:
        """Search with optional bonus filter."""
        _LOGGER.debug("search_products query=%s limit=%d bonus=%s", query, limit, bonus_only)
        products: list[AhProduct] = []
        page = 0
        page_size = limit * 5 if bonus_only else limit

        while len(products) < limit:
            data = await self._request(
                "GET",
                PRODUCT_SEARCH,
                params={
                    "query": query,
                    "page": page,
                    "size": page_size,
                    "sortOn": "RELEVANCE",
                },
                require_auth=True,
            )
            items = self._extract_product_list(data)
            if not items:
                break
            for item in items:
                try:
                    prod = AhProduct.from_api(item)
                    if bonus_only and not prod.is_bonus:
                        continue
                    products.append(prod)
                    if len(products) >= limit:
                        break
                except (KeyError, TypeError, ValueError):
                    continue
            page += 1
            if len(items) < page_size:
                break

        return products[:limit]

    async def get_product(self, product_id: int) -> AhProduct:
        """Get product detail by webshop ID."""
        url = f"{PRODUCT_DETAIL}/{product_id}"
        data = await self._request("GET", url, require_auth=True)
        if isinstance(data, dict):
            card = data.get("productCard") or data
            if isinstance(card, dict):
                return AhProduct.from_api(card)
        raise AhApiError("Unexpected product detail response")

    async def get_product_full(self, product_id: int) -> AhProduct:
        """Product detail (nutrition via GraphQL not yet ported)."""
        return await self.get_product(product_id)

    async def get_products_by_ids(self, product_ids: list[int]) -> list[AhProduct]:
        """Fetch multiple products by ID."""
        if not product_ids:
            return []
        params: dict[str, Any] = {"sortOn": "INPUT_PRODUCT_IDS"}
        for pid in product_ids:
            params.setdefault("ids", [])
            if isinstance(params["ids"], list):
                params["ids"].append(pid)
        # aiohttp needs repeated keys – build manually
        param_list = [("sortOn", "INPUT_PRODUCT_IDS")]
        for pid in product_ids:
            param_list.append(("ids", str(pid)))

        await self._throttle()
        headers = self._headers()
        token = await self._auth.get_access_token()
        headers["Authorization"] = f"Bearer {token}"
        timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT)
        async with self._session.request(
            "GET",
            PRODUCT_SEARCH_BY_IDS,
            params=param_list,
            headers=headers,
            timeout=timeout,
        ) as response:
            if response.status >= 400:
                raise AhApiError(f"get_products_by_ids failed (HTTP {response.status})")
            data = await response.json(content_type=None)

        products: list[AhProduct] = []
        items = data if isinstance(data, list) else self._extract_product_list(data)
        for item in items:
            if isinstance(item, dict):
                try:
                    products.append(AhProduct.from_api(item))
                except (KeyError, TypeError, ValueError):
                    pass
        return products

    async def get_bonus_products(self) -> list[AhProduct]:
        """Fetch national bonus products."""
        meta = await self._request("GET", BONUS_METADATA, require_auth=True)
        categories: list[str] = []
        if isinstance(meta, dict):
            for period in meta.get("periods") or []:
                if not isinstance(period, dict):
                    continue
                for tab in period.get("tabs") or []:
                    if not isinstance(tab, dict):
                        continue
                    for url_meta in tab.get("urlMetadataList") or []:
                        if (
                            isinstance(url_meta, dict)
                            and url_meta.get("bonusType") == "NATIONAL"
                            and url_meta.get("description")
                        ):
                            categories.append(str(url_meta["description"]))

        seen: set[str] = set()
        products: list[AhProduct] = []
        today = date.today().isoformat()
        for category in categories:
            data = await self._request(
                "GET",
                BONUS_SECTION,
                params={
                    "application": APPLICATION_HEADER,
                    "date": today,
                    "promotionType": "NATIONAL",
                    "category": category,
                },
                require_auth=True,
            )
            if not isinstance(data, dict):
                continue
            for entry in data.get("bonusGroupOrProducts") or []:
                if not isinstance(entry, dict):
                    continue
                raw = entry.get("product")
                if isinstance(raw, dict):
                    prod = AhProduct.from_api(raw)
                    key = f"{prod.webshop_id}:{prod.title}"
                    if key not in seen:
                        seen.add(key)
                        products.append(prod)
        return products

    # --- Authenticated: member & receipts ---

    async def get_member(self) -> AhMember:
        """Get member profile via GraphQL."""
        self._require_authenticated()
        data = await self._graphql(GQL_FETCH_MEMBER)
        member = (data or {}).get("member") if isinstance(data, dict) else None
        if isinstance(member, dict):
            return AhMember.from_api(member)
        raise AhApiError("Member not found in response")

    async def get_receipts(self) -> list[AhReceipt]:
        """List receipts (GraphQL, appie-go style)."""
        self._require_authenticated()
        try:
            data = await self._graphql(
                GQL_FETCH_POS_RECEIPTS,
                {"offset": 0, "limit": 100},
            )
            page = (data or {}).get("posReceiptsPage") if isinstance(data, dict) else {}
            raw = page.get("posReceipts") if isinstance(page, dict) else []
            receipts: list[AhReceipt] = []
            for item in raw or []:
                if isinstance(item, dict):
                    receipts.append(
                        AhReceipt.from_api(
                            {
                                "id": item.get("id"),
                                "dateTime": item.get("dateTime"),
                                "totalAmount": item.get("totalAmount"),
                            }
                        )
                    )
            return receipts
        except AhApiError:
            _LOGGER.debug("GraphQL receipts failed, trying legacy REST")
            return await self._get_receipts_legacy()

    async def _get_receipts_legacy(self) -> list[AhReceipt]:
        data = await self._request("GET", RECEIPTS_LEGACY)
        receipts: list[AhReceipt] = []
        for item in self._extract_receipt_list(data):
            try:
                receipts.append(AhReceipt.from_api(item))
            except (KeyError, TypeError, ValueError):
                pass
        return receipts

    async def get_receipt(self, transaction_id: str) -> AhReceipt:
        """Receipt detail via GraphQL."""
        self._require_authenticated()
        try:
            data = await self._graphql(GQL_FETCH_RECEIPT, {"id": transaction_id})
            details = (data or {}).get("posReceiptDetails") if isinstance(data, dict) else None
            if isinstance(details, dict):
                return AhReceipt.from_api(
                    {
                        "id": details.get("id"),
                        "products": details.get("products"),
                    }
                )
        except AhApiError:
            _LOGGER.debug("GraphQL receipt detail failed, trying legacy")
        url = f"{RECEIPT_DETAIL_LEGACY}/{transaction_id}"
        data = await self._request("GET", url)
        if isinstance(data, dict):
            return AhReceipt.from_api(data)
        raise AhApiError("Unexpected receipt detail response")

    # --- Shopping lists ---

    async def get_shopping_lists(self, product_id: int | None = None) -> list[AhShoppingList]:
        """List remote AH favorite lists."""
        self._require_authenticated()
        pid = product_id or 1
        data = await self._request(
            "GET",
            SHOPPING_LISTS_V3,
            params={"productId": pid},
        )
        lists: list[AhShoppingList] = []
        items = data if isinstance(data, list) else []
        for item in items:
            if isinstance(item, dict):
                lists.append(AhShoppingList.from_api(item))
        return lists

    async def get_shopping_list_items(self, list_id: str) -> list[AhShoppingListItem]:
        """Items for a shopping list."""
        self._require_authenticated()
        data = await self._graphql(
            GQL_FAVORITE_LIST_V2,
            {"ids": [list_id.upper()]},
        )
        raw_lists = (data or {}).get("favoriteListV2") if isinstance(data, dict) else []
        if not raw_lists:
            return []
        first = raw_lists[0] if isinstance(raw_lists, list) else raw_lists
        items: list[AhShoppingListItem] = []
        for item in (first.get("items") if isinstance(first, dict) else []) or []:
            if isinstance(item, dict):
                items.append(AhShoppingListItem.from_api(item))
        return items

    async def add_product_to_shopping_list(
        self, product_id: int, quantity: int = 1
    ) -> None:
        """Add product to main shopping list."""
        await self._add_to_shopping_list_items(
            [{"productId": product_id, "quantity": max(quantity, 1), "type": "SHOPPABLE"}]
        )

    async def add_free_text_to_shopping_list(self, name: str, quantity: int = 1) -> None:
        """Add free-text item to main shopping list."""
        await self._add_to_shopping_list_items(
            [
                {
                    "description": name,
                    "quantity": max(quantity, 1),
                    "type": "SHOPPABLE",
                    "originCode": "PRD",
                }
            ]
        )

    async def _add_to_shopping_list_items(self, items: list[dict[str, Any]]) -> None:
        self._require_authenticated()
        v2_items = []
        for item in items:
            entry = {
                "quantity": item.get("quantity", 1),
                "strikeThrough": False,
                "type": "SHOPPABLE",
                "originCode": "PRD",
            }
            if item.get("productId"):
                entry["productId"] = item["productId"]
                entry["description"] = item.get("description", "")
            else:
                entry["description"] = item.get("description", "Item")
            v2_items.append(entry)
        await self._request(
            "PATCH",
            SHOPPING_LIST_ITEMS_V2,
            json_body={"items": v2_items},
        )

    async def clear_shopping_list(self) -> None:
        """Clear main shopping list (via favorite list remove)."""
        self._require_authenticated()
        lists = await self.get_shopping_lists()
        if not lists:
            return
        list_id = lists[0].list_id
        items = await self.get_shopping_list_items(list_id)
        product_ids = [i.product_id for i in items if i.product_id]
        if not product_ids:
            return
        # Remove via PATCH with empty or use item check – simplified: not fully ported favorite list GraphQL delete
        _LOGGER.warning(
            "clear_shopping_list: full remote clear requires favoriteListProductsDeleteV2 (TODO)"
        )

    async def check_shopping_list_item(self, item_id: str, checked: bool) -> None:
        """Mark shopping list item checked/unchecked."""
        self._require_authenticated()
        url = f"{SHOPPING_LIST_ITEM_CHECK}/{item_id}"
        await self._request("PATCH", url, json_body={"checked": checked})

    # --- Orders (experimental) ---

    async def get_order(self) -> AhOrder:
        """Active order summary."""
        self._require_authenticated()
        self._require_experimental_order()
        data = await self._request(
            "GET",
            ORDER_ACTIVE_SUMMARY,
            include_order=False,
        )
        if isinstance(data, dict):
            order = AhOrder.from_summary_api(data)
            self._order_id = order.order_id
            return order
        raise AhApiError("Unexpected order response")

    async def get_order_details(self, order_id: int) -> AhOrder:
        """Order details grouped by taxonomy."""
        self._require_authenticated()
        self._require_experimental_order()
        url = f"{ORDER_DETAILS}/{order_id}/details-grouped-by-taxonomy"
        data = await self._request("GET", url)
        if not isinstance(data, dict):
            raise AhApiError("Unexpected order details")
        items: list[AhOrderItem] = []
        for group in data.get("groupedProductsInTaxonomy") or []:
            if not isinstance(group, dict):
                continue
            for op in group.get("orderedProducts") or []:
                if isinstance(op, dict):
                    items.append(AhOrderItem.from_api(op))
        return AhOrder(
            order_id=str(data.get("orderId") or order_id),
            state=data.get("orderState"),
            items=items,
            item_count=len(items),
        )

    async def get_order_summary(self) -> AhOrderSummary:
        """Active order totals."""
        order = await self.get_order()
        return AhOrderSummary(
            total_items=order.item_count,
            total_price=order.total_price,
            total_discount=order.total_discount,
        )

    async def add_to_order(self, product_id: int, quantity: int = 1) -> None:
        """Add or update order line."""
        self._require_authenticated()
        self._require_experimental_order()
        await self._request(
            "PUT",
            ORDER_ITEMS,
            json_body={
                "items": [
                    {
                        "productId": product_id,
                        "quantity": quantity,
                        "originCode": "PRD",
                        "description": "",
                        "strikethrough": False,
                    }
                ]
            },
            include_order=True,
        )

    async def remove_from_order(self, product_id: int) -> None:
        """Remove product from order (quantity 0)."""
        await self.add_to_order(product_id, quantity=0)

    async def update_order_item(self, product_id: int, quantity: int) -> None:
        """Update order line quantity."""
        await self.add_to_order(product_id, quantity=quantity)

    async def get_fulfillments(self) -> list[AhFulfillment]:
        """Open order fulfillments."""
        self._require_authenticated()
        self._require_experimental_order()
        data = await self._graphql(GQL_ORDER_FULFILLMENTS)
        raw = (data or {}).get("orderFulfillments") if isinstance(data, dict) else {}
        results = raw.get("result") if isinstance(raw, dict) else []
        return [
            AhFulfillment.from_api(r)
            for r in results or []
            if isinstance(r, dict)
        ]

    async def search_stores(self, postal_code: str) -> list[Any]:
        """Search stores by postal code – not yet implemented."""
        raise AhNotImplementedError(
            "search_stores endpoint not yet documented. See docs/AH_API_DISCOVERY.md"
        )

    async def shopping_list_to_order(self) -> None:
        """Convert shopping list to order – experimental, not enabled in HA service layer."""
        raise AhNotImplementedError(
            "shopping_list_to_order is not exposed in Home Assistant (safety)."
        )

    def _extract_product_list(self, data: Any) -> list[dict[str, Any]]:
        if isinstance(data, list):
            return [i for i in data if isinstance(i, dict)]
        if not isinstance(data, dict):
            return []
        for key in ("products", "items", "results", "data"):
            items = data.get(key)
            if isinstance(items, list):
                return [i for i in items if isinstance(i, dict)]
        search_result = data.get("searchResult") or data.get("productSearch")
        if isinstance(search_result, dict):
            for key in ("products", "items"):
                items = search_result.get(key)
                if isinstance(items, list):
                    return [i for i in items if isinstance(i, dict)]
        return []

    def _extract_receipt_list(self, data: Any) -> list[dict[str, Any]]:
        if isinstance(data, list):
            return [i for i in data if isinstance(i, dict)]
        if not isinstance(data, dict):
            return []
        for key in ("receipts", "items", "data", "results"):
            items = data.get(key)
            if isinstance(items, list):
                return [i for i in items if isinstance(i, dict)]
        return []
