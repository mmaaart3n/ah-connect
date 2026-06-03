# AH API Discovery

Documentatie van bekende en ontdekte Albert Heijn Appie API endpoints.

> **Waarschuwing:** Dit is een onofficiële API. Endpoints kunnen zonder waarschuwing wijzigen. Gebruik defensief en verwacht breaking changes.

## Base URL

```
https://api.ah.nl
```

## Standaard headers

```
User-Agent: Appie/8.22.3
Content-Type: application/json
Authorization: Bearer {access_token}
```

---

## Geïmplementeerd in MVP

### Authentication

| Method | Endpoint | Body | Status |
|--------|----------|------|--------|
| POST | `/mobile-auth/v1/auth/token/anonymous` | `{"clientId":"appie"}` | ✅ Implemented |
| POST | `/mobile-auth/v1/auth/token` | `{"clientId":"appie","code":"..."}` | ✅ Implemented |
| POST | `/mobile-auth/v1/auth/token/refresh` | `{"clientId":"appie","refreshToken":"..."}` | ✅ Implemented |

### Products

| Method | Endpoint | Params | Status |
|--------|----------|--------|--------|
| GET | `/mobile-services/product/search/v2` | `query`, `sortOn=RELEVANCE`, `size` | ✅ Implemented |

### Receipts

| Method | Endpoint | Status |
|--------|----------|--------|
| GET | `/mobile-services/v1/receipts` | ✅ Implemented |
| GET | `/mobile-services/v2/receipts/{transactionId}` | ✅ Implemented |

---

## Ontdekt maar NIET geïmplementeerd

> ⚠️ Onderstaande endpoints zijn **niet gevalideerd** in productie. Implementeer pas na grondig testen en achter feature flags.

### Shopping list (remote AH lijst)

| Method | Endpoint | Notities |
|--------|----------|----------|
| GET | `/mobile-services/v1/shoppinglists` | TODO: response schema documenteren |
| POST | `/mobile-services/v1/shoppinglists` | TODO: lijst aanmaken |
| PUT | `/mobile-services/v1/shoppinglists/{id}/items` | TODO: items toevoegen |

**Status:** Fase 2 – niet in MVP

### Cart / Basket

| Method | Endpoint | Notities |
|--------|----------|----------|
| GET | `/mobile-services/v1/cart` | TODO: mandje ophalen |
| POST | `/mobile-services/v1/cart/items` | TODO: product toevoegen |
| DELETE | `/mobile-services/v1/cart/items/{id}` | TODO: product verwijderen |

**Status:** Fase 2 – achter `experimental_cart_enabled` feature flag

> **NOOIT** automatisch checkout uitvoeren zonder expliciete user confirmation service.

### Delivery slots

| Method | Endpoint | Notities |
|--------|----------|----------|
| GET | `/mobile-services/v1/delivery/slots` | TODO: beschikbare slots |
| POST | `/mobile-services/v1/delivery/slots/reserve` | TODO: slot reserveren |

**Status:** Fase 3

### Checkout / Orders

| Method | Endpoint | Notities |
|--------|----------|----------|
| POST | `/mobile-services/v1/checkout` | TODO: checkout starten |
| GET | `/mobile-services/v1/orders` | TODO: order status |
| GET | `/mobile-services/v1/orders/{id}` | TODO: order detail |

**Status:** Fase 3+ – **niet plannen voor MVP**

### Product detail

| Method | Endpoint | Notities |
|--------|----------|----------|
| GET | `/mobile-services/product/detail/v1/{webshopId}` | TODO: volledig product detail |

**Status:** Fase 2

---

## Rate limiting

De integratie hanteert een minimum van **500ms tussen requests** en exponential backoff bij HTTP 429/5xx.

AH-side rate limits zijn onbekend. Wees spaarzaam met polling en zoekopdrachten.

---

## Response parsing

API responses variëren in structuur. De client probeert meerdere keys:

**Products:** `products`, `items`, `results`, `data`, `searchResult.products`

**Receipts:** `receipts`, `items`, `data`, `results`

Meld inconsistenties via GitHub issues.

---

## Bijdragen

Heb je een endpoint ontdekt? Voeg toe aan dit document met:

- HTTP method + URL
- Request body/params
- Response voorbeeld (zonder tokens!)
- Testdatum + Appie versie
