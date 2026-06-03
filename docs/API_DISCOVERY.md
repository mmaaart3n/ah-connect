# API discovery (appie-go parity)

Base URL: `https://api.ah.nl`  
Client: `appie-ios`  
User-Agent: `Appie/9.28` (per appie-go)

## Implemented (aligned with appie-go)

| Method | Endpoint / transport |
|--------|----------------------|
| Anonymous token | `POST /mobile-auth/v1/auth/token/anonymous` |
| Token / refresh | `POST /mobile-auth/v1/auth/token`, `/refresh` |
| Search | `GET /mobile-services/product/search/v2` |
| Product detail | `GET /mobile-services/product/detail/v4/fir/{id}` |
| Products by IDs | `GET /mobile-services/product/search/v2/products` |
| Bonus | `/mobile-services/bonuspage/v3/metadata`, `/v2/section` |
| Receipts | GraphQL `posReceiptsPage`, `posReceiptDetails` |
| Member | GraphQL `FetchMember` |
| Shopping lists | `/mobile-services/lists/v3`, GraphQL favorites |
| Orders | `/mobile-services/order/v1/...` |
| Stores / koopjes | GraphQL `storesSearch`, `bargainItems` |

## Pending / partial

- GetBonusGroupProducts (group segment resolution)
- Full nutritional enrichment edge cases
- Native HA OAuth callback (roadmap)

## Not implemented

- Checkout, place order, payment, finalize order
