"""AH API client for AH Connect (functionally aligned with appie-go)."""

from __future__ import annotations

import asyncio
import logging
from datetime import date
from typing import Any
from urllib.parse import urlencode

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .auth import AhAuthManager
from .const import DEFAULT_BASE_URL, OPT_DEBUG_LOGGING
from .exceptions import AhApiError, AhAuthenticatedModeRequired, AhNotImplementedError
from .models import (
    AhFulfillment,
    AhKoopje,
    AhMember,
    AhOrder,
    AhOrderSummary,
    AhProduct,
    AhReceipt,
    AhShoppingList,
    AhShoppingListItem,
    AhStore,
)

_LOGGER = logging.getLogger(__name__)

# GraphQL queries (from appie-go reference)
_FETCH_POS_RECEIPTS = """query FetchPosReceipts($offset: Int!, $limit: Int!) {
  posReceiptsPage(pagination: {offset: $offset, limit: $limit}) {
    posReceipts { id dateTime totalAmount { amount } }
  }
}"""

_FETCH_POS_RECEIPT_DETAILS = """query FetchReceipt($id: String!) {
  posReceiptDetails(id: $id) {
    id
    products { id quantity name price { amount } amount { amount } }
    discounts { name amount { amount } }
    payments { method amount { amount } }
  }
}"""

_FETCH_MEMBER = """query FetchMember {
  member {
    id emailAddress gender dateOfBirth phoneNumber
    name { first last }
    address { street houseNumber postalCode city countryCode }
    cards { bonus gall }
    customerProfileAudiences
  }
}"""

_FAVORITE_LIST_V2 = """query FavoriteListV2($ids: [String!]!) {
  favoriteListV2(ids: $ids) {
    id description totalSize
    items { id productId quantity }
  }
}"""

_FETCH_PRODUCT_NUTRITION = """query FetchProduct($productId: Int!) {
  product(id: $productId) {
    id
    tradeItem {
      nutritions { nutrients { type name value } }
    }
  }
}"""

_STORES_SEARCH = """query StoresSearch($filter: StoresFilterInput) {
  storesSearch(filter: $filter, limit: 5) {
    result { id name storeType address { street postalCode city } }
  }
}"""

_BARGAIN_ITEMS = """query BargainItems($storeId: String!) {
  bargainItems(storeId: $storeId) {
    product { id title brand salesUnitSize }
    categoryTitle
    markdown { markdownPercentage }
    stock
    bargainPrice { priceWas priceNow }
  }
}"""

_REOPEN_ORDER = """mutation OrderReopen($id: Int!) {
  orderReopen(id: $id) { status errorMessage }
}"""

_REVERT_ORDER = """mutation OrderRevert($id: Int!) {
  orderRevert(id: $id) { status errorMessage }
}"""

_FULFILLMENTS = """query OrderFulfillments {
  orderFulfillments(status: OPEN) {
    result {
      orderId statusDescription shoppingType transactionCompleted modifiable
      totalPrice { totalPrice { amount } }
      delivery { status slot { date dateDisplay timeDisplay } }
    }
  }
}"""


class AhConnectApiClient:
    """Async client for Albert Heijn mobile API."""

    def __init__(
        self,
        hass: HomeAssistant,
        auth: AhAuthManager,
        entry_options: dict[str, Any] | None = None,
    ) -> None:
        self.hass = hass
        self.auth = auth
        self.options = entry_options or {}
        self._session = async_get_clientsession(hass)
        self._lock = asyncio.Lock()

    def _debug(self, msg: str, *args: Any) -> None:
        if self.options.get(OPT_DEBUG_LOGGING):
            _LOGGER.debug(msg, *args)

    def _require_authenticated(self) -> None:
        if self.auth.is_anonymous:
            raise AhAuthenticatedModeRequired(
                "This operation requires authenticated mode"
            )

    async def _request(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, Any] | None = None,
        params: dict[str, str] | None = None,
    ) -> Any:
        headers = await self.auth.async_get_headers()
        url = f"{DEFAULT_BASE_URL}{path}"
        if params:
            url = f"{url}?{urlencode(params)}"

        async with self._lock:
            self._debug("%s %s", method, path)
            async with self._session.request(
                method, url, json=body, headers=headers
            ) as resp:
                text = await resp.text()
                if resp.status == 429:
                    raise AhApiError("Rate limited", status=429)
                if resp.status >= 500:
                    raise AhApiError(f"Server error {resp.status}", status=resp.status)
                if resp.status >= 400:
                    raise AhApiError(
                        f"API error {resp.status}: {text[:300]}", status=resp.status
                    )
                if not text:
                    return None
                return await resp.json(content_type=None)

    async def _graphql(
        self, query: str, variables: dict[str, Any] | None = None
    ) -> Any:
        payload = {"query": query, "variables": variables or {}}
        resp = await self._request("POST", "/graphql", body=payload)
        if not isinstance(resp, dict):
            raise AhApiError("Invalid GraphQL response")
        errors = resp.get("errors") or []
        if errors:
            msg = errors[0].get("message", "GraphQL error")
            raise AhApiError(msg)
        return resp.get("data")

    def _product_from_response(self, p: dict[str, Any]) -> AhProduct:
        return AhProduct.from_product_response(p)

    # --- Anonymous / product methods ---

    async def search_products(self, query: str, limit: int = 10) -> list[AhProduct]:
        return await self.search_products_filtered(query=query, limit=limit)

    async def search_products_filtered(
        self,
        query: str,
        limit: int = 10,
        bonus_only: bool = False,
    ) -> list[AhProduct]:
        if limit <= 0:
            limit = 30
        products: list[AhProduct] = []
        page = 0
        page_size = limit * 5 if bonus_only else limit

        while len(products) < limit:
            params = {
                "query": query,
                "page": str(page),
                "size": str(page_size),
                "sortOn": "RELEVANCE",
            }
            data = await self._request(
                "GET", "/mobile-services/product/search/v2", params=params
            )
            if not isinstance(data, dict):
                break
            for p in data.get("products") or []:
                prod = self._product_from_response(p)
                if bonus_only and not prod.is_bonus:
                    continue
                products.append(prod)
                if len(products) >= limit:
                    break
            page_info = data.get("page") or {}
            total = page_info.get("totalElements", 0)
            if (page + 1) * page_size >= total:
                break
            page += 1

        return products[:limit]

    async def get_product(self, product_id: int) -> AhProduct:
        data = await self._request(
            "GET", f"/mobile-services/product/detail/v4/fir/{product_id}"
        )
        if not isinstance(data, dict):
            raise AhApiError("Invalid product response")
        card = data.get("productCard") or data
        return self._product_from_response(card)

    async def get_product_full(self, product_id: int) -> AhProduct:
        product = await self.get_product(product_id)
        gql = await self._graphql(
            _FETCH_PRODUCT_NUTRITION, {"productId": product_id}
        )
        if gql and isinstance(gql.get("product"), dict):
            trade = gql["product"].get("tradeItem") or {}
            # Nutrition stored in model extension via to_dict if needed
            _ = trade
        return product

    async def get_products_by_ids(self, product_ids: list[int]) -> list[AhProduct]:
        if not product_ids:
            return []
        params: dict[str, str] = {"sortOn": "INPUT_PRODUCT_IDS"}
        for pid in product_ids:
            params.setdefault("ids", "")
            # urlencode handles multiple ids via list in urlencode with doseq
        params_list = [("ids", str(pid)) for pid in product_ids] + [
            ("sortOn", "INPUT_PRODUCT_IDS")
        ]
        headers = await self.auth.async_get_headers()
        url = f"{DEFAULT_BASE_URL}/mobile-services/product/search/v2/products?{urlencode(params_list)}"
        async with self._session.get(url, headers=headers) as resp:
            if resp.status >= 400:
                raise AhApiError(f"get products by ids failed: {resp.status}")
            data = await resp.json(content_type=None)
        if not isinstance(data, list):
            return []
        return [self._product_from_response(p) for p in data]

    async def get_bonus_products(self) -> list[AhProduct]:
        meta = await self._request("GET", "/mobile-services/bonuspage/v3/metadata")
        categories: list[str] = []
        if isinstance(meta, dict):
            for period in meta.get("periods") or []:
                for tab in period.get("tabs") or []:
                    for m in tab.get("urlMetadataList") or []:
                        if m.get("bonusType") == "NATIONAL":
                            categories.append(m.get("description", ""))

        seen: set[str] = set()
        products: list[AhProduct] = []
        today = date.today().isoformat()

        for category in categories:
            if not category:
                continue
            params = {
                "application": "AHWEBSHOP",
                "date": today,
                "promotionType": "NATIONAL",
                "category": category,
            }
            section = await self._request(
                "GET", "/mobile-services/bonuspage/v2/section", params=params
            )
            if not isinstance(section, dict):
                continue
            for item in section.get("bonusGroupOrProducts") or []:
                if item.get("product"):
                    prod = self._product_from_response(item["product"])
                elif item.get("bonusGroup"):
                    bg = item["bonusGroup"]
                    prod = AhProduct(
                        title=bg.get("segmentDescription", ""),
                        is_bonus=True,
                        bonus_mechanism=bg.get("discountDescription", ""),
                    )
                else:
                    continue
                key = f"{prod.id}:{prod.title}"
                if key not in seen:
                    seen.add(key)
                    products.append(prod)

        return products

    async def get_koopjes(self, postal_code: str) -> list[AhKoopje]:
        stores = await self.search_stores(postal_code=postal_code)
        if not stores:
            return []
        store_id = stores[0].id
        data = await self._graphql(_BARGAIN_ITEMS, {"storeId": str(store_id)})
        items = (data or {}).get("bargainItems") or []
        return [AhKoopje.from_api(i) for i in items]

    # --- Authenticated ---

    async def get_member(self) -> AhMember:
        self._require_authenticated()
        data = await self._graphql(_FETCH_MEMBER)
        member = (data or {}).get("member") or {}
        return AhMember.from_api(member)

    async def get_receipts(self) -> list[AhReceipt]:
        self._require_authenticated()
        data = await self._graphql(_FETCH_POS_RECEIPTS, {"offset": 0, "limit": 100})
        receipts = []
        for r in (data or {}).get("posReceiptsPage", {}).get("posReceipts") or []:
            receipts.append(
                AhReceipt(
                    transaction_id=str(r.get("id", "")),
                    date=str(r.get("dateTime", "")),
                    total_amount=float(
                        (r.get("totalAmount") or {}).get("amount", 0)
                    ),
                )
            )
        return receipts

    async def get_receipt(self, transaction_id: str) -> AhReceipt:
        self._require_authenticated()
        data = await self._graphql(
            _FETCH_POS_RECEIPT_DETAILS, {"id": transaction_id}
        )
        details = (data or {}).get("posReceiptDetails") or {}
        from .models import AhReceiptItem

        receipt = AhReceipt(
            transaction_id=str(details.get("id", transaction_id)),
            items=[
                AhReceiptItem.from_api(p)
                for p in details.get("products") or []
            ],
        )
        return receipt

    async def get_shopping_lists(
        self, product_id: int | None = None
    ) -> list[AhShoppingList]:
        self._require_authenticated()
        pid = product_id if product_id and product_id > 0 else 1
        data = await self._request(
            "GET", f"/mobile-services/lists/v3/lists?productId={pid}"
        )
        if not isinstance(data, list):
            return []
        return [AhShoppingList.from_api(r) for r in data]

    async def get_shopping_list_items(self, list_id: str) -> list[AhShoppingListItem]:
        self._require_authenticated()
        data = await self._graphql(
            _FAVORITE_LIST_V2, {"ids": [list_id.upper()]}
        )
        lists = (data or {}).get("favoriteListV2") or []
        if not lists:
            return []
        return [
            AhShoppingListItem.from_api(i)
            for i in lists[0].get("items") or []
        ]

    async def add_product_to_shopping_list(
        self, product_id: int, quantity: int = 1
    ) -> None:
        await self.add_to_shopping_list(
            list_id="",
            product_id=product_id,
            quantity=quantity,
        )

    async def add_free_text_to_shopping_list(
        self, name: str, quantity: int = 1
    ) -> None:
        await self.add_to_shopping_list(list_id="", name=name, quantity=quantity)

    async def add_to_shopping_list(
        self,
        list_id: str,
        product_id: int | None = None,
        name: str | None = None,
        quantity: int = 1,
    ) -> None:
        self._require_authenticated()
        qty = max(quantity, 1)
        item: dict[str, Any] = {
            "quantity": qty,
            "strikeThrough": False,
            "type": "SHOPPABLE",
            "originCode": "PRD",
        }
        if product_id:
            item["productId"] = product_id
            item["description"] = name or ""
            item["searchTerm"] = name or ""
        else:
            item["description"] = name or ""
        await self._request(
            "PATCH",
            "/mobile-services/shoppinglist/v2/items",
            body={"items": [item]},
        )

    async def clear_shopping_list(self, list_id: str) -> None:
        self._require_authenticated()
        items = await self.get_shopping_list_items(list_id)
        product_ids = [i.product_id for i in items if i.product_id > 0]
        if not product_ids:
            return
        await self._remove_from_favorite_list(list_id, product_ids)

    async def _remove_from_favorite_list(
        self, list_id: str, product_ids: list[int]
    ) -> None:
        items = await self.get_shopping_list_items(list_id)
        want = set(product_ids)
        item_ids = [i.id for i in items if i.product_id in want and i.id]
        if not item_ids:
            return
        mutation = """mutation DeleteProductsFromFavoriteList($favoriteListId: String!, $itemIds: [String!]!) {
  favoriteListProductsDeleteV2(id: $favoriteListId, itemIds: $itemIds) {
    status errorMessage
  }
}"""
        data = await self._graphql(
            mutation,
            {"favoriteListId": list_id.upper(), "itemIds": item_ids},
        )
        result = (data or {}).get("favoriteListProductsDeleteV2") or {}
        if result.get("status") != "SUCCESS":
            raise AhApiError(result.get("errorMessage", "Delete failed"))

    async def check_shopping_list_item(
        self, list_id: str, item_id: str, checked: bool
    ) -> None:
        self._require_authenticated()
        await self._request(
            "PATCH",
            f"/mobile-services/lists/v3/lists/items/{item_id}",
            body={"checked": checked},
        )

    # --- Orders (experimental) ---

    async def get_order(self) -> AhOrder:
        self._require_authenticated()
        data = await self._request(
            "GET",
            "/mobile-services/order/v1/summaries/active?sortBy=DEFAULT",
        )
        if not isinstance(data, dict):
            raise AhApiError("Invalid order response")
        order = AhOrder.from_summary(data)
        self.auth.set_order_context(order.id)
        return order

    async def get_order_details(self, order_id: int) -> AhOrder:
        self._require_authenticated()
        data = await self._request(
            "GET",
            f"/mobile-services/order/v1/{order_id}/details-grouped-by-taxonomy",
        )
        if not isinstance(data, dict):
            raise AhApiError("Invalid order details")
        items: list = []
        for group in data.get("groupedProductsInTaxonomy") or []:
            for op in group.get("orderedProducts") or []:
                from .models import AhOrderItem

                items.append(AhOrderItem.from_api(op))
        return AhOrder(
            id=str(data.get("orderId", order_id)),
            state=str(data.get("orderState", "")),
            items=items,
            total_count=len(items),
        )

    async def get_order_summary(self) -> AhOrderSummary:
        self._require_authenticated()
        data = await self._request(
            "GET",
            "/mobile-services/order/v1/summaries/active?sortBy=DEFAULT",
        )
        if not isinstance(data, dict):
            raise AhApiError("Invalid order summary")
        tp = data.get("totalPrice") or {}
        items = data.get("orderedProducts") or []
        return AhOrderSummary(
            total_items=len(items),
            total_price=float(tp.get("priceTotalPayable", 0)),
            total_discount=float(tp.get("priceDiscount", 0)),
        )

    async def add_to_order(self, product_id: int, quantity: int = 1) -> None:
        await self._update_order_items({product_id: quantity})

    async def remove_from_order(self, product_id: int) -> None:
        await self._update_order_items({product_id: 0})

    async def update_order_item(self, product_id: int, quantity: int) -> None:
        await self._update_order_items({product_id: quantity})

    async def _update_order_items(self, merged: dict[int, int]) -> None:
        self._require_authenticated()
        req_items = [
            {
                "productId": pid,
                "quantity": qty,
                "originCode": "PRD",
                "description": "",
                "strikethrough": False,
            }
            for pid, qty in merged.items()
        ]
        await self._request(
            "PUT",
            "/mobile-services/order/v1/items?sortBy=DEFAULT",
            body={"items": req_items},
        )

    async def reopen_order(self, order_id: int) -> None:
        self._require_authenticated()
        data = await self._graphql(_REOPEN_ORDER, {"id": order_id})
        result = (data or {}).get("orderReopen") or {}
        if result.get("status") != "SUCCESS":
            raise AhApiError(result.get("errorMessage", "Reopen failed"))

    async def revert_order(self, order_id: int) -> None:
        self._require_authenticated()
        data = await self._graphql(_REVERT_ORDER, {"id": order_id})
        result = (data or {}).get("orderRevert") or {}
        if result.get("status") != "SUCCESS":
            raise AhApiError(result.get("errorMessage", "Revert failed"))
        self.auth.set_order_context("", "")

    async def get_fulfillments(self) -> list[AhFulfillment]:
        self._require_authenticated()
        data = await self._graphql(_FULFILLMENTS)
        results = (data or {}).get("orderFulfillments", {}).get("result") or []
        return [AhFulfillment.from_api(r) for r in results]

    async def search_stores(
        self,
        query: str | None = None,
        postal_code: str | None = None,
    ) -> list[AhStore]:
        filt: dict[str, Any] = {}
        if postal_code:
            filt["postalCode"] = postal_code
        if query:
            filt["query"] = query
        data = await self._graphql(_STORES_SEARCH, {"filter": filt})
        results = (data or {}).get("storesSearch", {}).get("result") or []
        return [AhStore.from_api(r) for r in results]
