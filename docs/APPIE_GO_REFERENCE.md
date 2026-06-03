# appie-go Reference

## Purpose

The Go library [appie-go](https://github.com/gwillem/appie-go) ([pkg.go.dev](https://pkg.go.dev/github.com/gwillem/appie-go)) is used as a **technical reference only** for this Home Assistant integration.

- **License:** appie-go is AGPLv3. We do **not** copy Go source code.
- **Runtime:** AH Shopping is Python and has **no** Go dependency.
- **Approach:** Endpoints, request shapes, GraphQL queries, and flows are reimplemented in Python (`api.py`, `auth.py`, `models.py`).

## Capabilities mapped to Python

### Anonymous / public

| appie-go | Python (`AhApiClient`) | Status |
|----------|------------------------|--------|
| `GetAnonymousToken` | `get_anonymous_token()` | ✅ |
| `SearchProducts` | `search_products()` | ✅ |
| `SearchProductsFiltered` | `search_products_filtered()` | ✅ |
| `GetProduct` | `get_product()` | ✅ |
| `GetProductFull` | `get_product_full()` | ⚠️ Partial (no nutrition GraphQL yet) |
| `GetProductsByIDs` | `get_products_by_ids()` | ✅ |
| `GetBonusProducts` | `get_bonus_products()` | ✅ |

### Authenticated

| appie-go | Python | Status |
|----------|--------|--------|
| `Login` / OAuth | Config flow + `AhAuthManager` | ✅ Manual OAuth code |
| `Logout` | — | ❌ Not exposed in HA |
| `GetMember` | `get_member()` | ✅ GraphQL |
| `GetReceipts` | `get_receipts()` | ✅ GraphQL (+ REST fallback) |
| `GetReceipt` | `get_receipt()` | ✅ GraphQL (+ REST fallback) |
| `GetShoppingLists` | `get_shopping_lists()` | ✅ |
| `GetShoppingListItems` | `get_shopping_list_items()` | ✅ GraphQL |
| `AddProductToShoppingList` | `add_product_to_shopping_list()` | ✅ |
| `AddFreeTextToShoppingList` | `add_free_text_to_shopping_list()` | ✅ |
| `ClearShoppingList` | `clear_shopping_list()` | ⚠️ Partial (see TODO in code) |
| `CheckShoppingListItem` | `check_shopping_list_item()` | ✅ |
| `GetOrder` | `get_order()` | ✅ Experimental flag |
| `GetOrderDetails` | `get_order_details()` | ✅ Experimental flag |
| `GetOrderSummary` | `get_order_summary()` | ✅ Experimental flag |
| `AddToOrder` | `add_to_order()` | ✅ Experimental flag |
| `RemoveFromOrder` | `remove_from_order()` | ✅ Experimental flag |
| `UpdateOrderItem` | `update_order_item()` | ✅ Experimental flag |
| `ShoppingListToOrder` | — | ❌ Not exposed (safety) |
| `GetFulfillments` | `get_fulfillments()` | ✅ Experimental flag |
| `SearchStores` | `search_stores()` | ❌ `AhNotImplementedError` |

## HTTP headers (appie-go)

```
User-Agent: Appie/9.28 (...)
x-client-name: appie-ios
x-client-version: 9.28
x-application: AHWEBSHOP
Authorization: Bearer <token>
```

OAuth client ID: `appie-ios` (legacy `appie` documented in AUTHENTICATION.md).

## Order / checkout safety

- **No** `place_order`, `confirm_order`, `checkout`, or payment services.
- Order read/write requires `experimental_order_enabled` in integration options.
- `experimental_checkout_enabled` is reserved and **not functional**.

## Links

- https://github.com/gwillem/appie-go
- https://pkg.go.dev/github.com/gwillem/appie-go
