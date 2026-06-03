# appie-go reference

AH Connect is functionally inspired by [appie-go](https://github.com/gwillem/appie-go) — the **only** technical/API reference for this project.

- [GitHub](https://github.com/gwillem/appie-go)
- [pkg.go.dev](https://pkg.go.dev/github.com/gwillem/appie-go)

appie-go is a Go client library and CLI for the Albert Heijn mobile API. AH Connect is a **Python-native** Home Assistant integration. appie-go is **not** a runtime dependency. No Go source is copied (appie-go is AGPLv3).

## Capabilities (appie-go)

### Anonymous

- GetAnonymousToken
- SearchProducts / SearchProductsFiltered
- GetProduct / GetProductFull
- GetProductsByIDs
- GetBonusProducts

### Authenticated

- Login (CLI) / token refresh
- GetMember
- GetReceipts / GetReceipt
- GetShoppingLists / GetShoppingListItems
- AddProductToShoppingList / AddFreeTextToShoppingList / AddToShoppingList
- ClearShoppingList / CheckShoppingListItem
- GetOrder / GetOrderDetails / GetOrderSummary
- AddToOrder / RemoveFromOrder / UpdateOrderItem
- ReopenOrder / RevertOrder
- GetFulfillments
- SearchStores / GetBargains (koopjes)

### CLI

- `appie login`
- `appie search`
- `appie receipt`
- `appie order`
- `appie list`
- `appie koopjes`

## Not in AH Connect

**Checkout / place order / payment** are intentionally not implemented in this Home Assistant integration.
