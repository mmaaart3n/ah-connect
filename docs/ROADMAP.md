# Roadmap

## MVP (v0.1.0) ✅

- [x] HACS-compatible custom integration
- [x] Config flow (anonymous + OAuth)
- [x] Token refresh
- [x] Product search service
- [x] Local shopping list (storage)
- [x] Receipt sensors (authenticated)
- [x] Options flow
- [x] Diagnostics (redacted)
- [x] NL/EN translations
- [x] Throttling & retry/backoff

## Fase 2 – Remote sync & enrichment

- [ ] **Remote AH shopping list sync**
  - GET/POST `/mobile-services/v1/shoppinglists`
  - Two-way sync met conflict resolution
  - Opt-in via options

- [ ] **Product detail endpoint**
  - Volledige product info (allergenen, voedingswaarden)
  - Sensor/attribute voor favoriete producten

- [ ] **Re-auth flow**
  - OAuth opnieuw doen zonder entry te verwijderen

- [ ] **Improved OAuth UX**
  - Onderzoek OAuth2 helper / external auth flow
  - Mogelijk via HA OAuth2 delegation

- [ ] **Search result caching**
  - Korte TTL cache om API calls te beperken

- [ ] **Multiple config entries**
  - Ondersteuning voor meerdere AH accounts

## Fase 3 – Cart & delivery (experimenteel)

> ⚠️ Alleen achter feature flag `experimental_cart_enabled`. Nooit automatische checkout.

- [ ] **Cart/basket read**
  - GET `/mobile-services/v1/cart`
  - Sensor: aantal items in mandje

- [ ] **Cart item management**
  - POST/DELETE cart items
  - Service met expliciete confirmation

- [ ] **Delivery slots**
  - Beschikbare slots ophalen
  - Sensor voor volgende beschikbare slot

- [ ] **User confirmation service**
  - `ah_shopping.confirm_action` voor gevaarlijke operaties

## Fase 4 – Orders (toekomst, onzeker)

> **Niet gepland zolang endpoints niet veilig en reproduceerbaar zijn vastgesteld.**

- [ ] Checkout flow onderzoek
- [ ] Order status tracking
- [ ] Order history sensors
- [ ] Delivery tracking notifications

## Fase 5 – Smart home integratie

- [ ] Blueprint: "Voeg toe aan lijst via voice assistant"
- [ ] Blueprint: "Bon ontvangen → update budget sensor"
- [ ] Integratie met `shopping_list` entity
- [ ] Dashboard card (custom Lovelace)
- [ ] AI suggesties op basis van koopgeschiedenis

## Known TODOs (technisch)

```
TODO(fase2): Remote shopping list API – endpoints valideren
TODO(fase2): Product detail parser
TODO(fase2): Re-auth config subflow
TODO(fase3): Cart endpoints – ACHTER feature flag
TODO(fase3): Delivery slot endpoints
TODO(fase3): confirm_action service voor destructive ops
TODO(fase4): Checkout – NIET implementeren zonder expliciete user approval
TODO(fase5): Lovelace card
```

## Bijdragen

Suggesties en PRs welkom! Begin met endpoints documenteren in [AH_API_DISCOVERY.md](AH_API_DISCOVERY.md) voordat je implementeert.
