# Security & Limitations

## Onofficiële API

Deze integratie gebruikt de **onofficiële Albert Heijn Appie mobile API**. Dit betekent:

- Geen garantie op stabiliteit of beschikbaarheid
- Albert Heijn kan de API op elk moment wijzigen of blokkeren
- Geen officiële support van Albert Heijn
- Gebruik kan in strijd zijn met AH terms of service

**Gebruik op eigen risico.**

## Credential handling

| Regel | Implementatie |
|-------|---------------|
| Geen tokens in logs | ✅ Alle token logging is uitgesloten |
| Geen tokens in diagnostics | ✅ Redacted via `async_redact_data` |
| Geen hardcoded tokens | ✅ Tokens alleen in config entry |
| Geen tokens in YAML | ✅ Config entry storage only |
| Automatische refresh | ✅ 5 min vóór expiry |

## Wat de integratie NIET doet (MVP)

- ❌ Geen bestellingen plaatsen
- ❌ Geen checkout automatiseren
- ❌ Geen betalingen verwerken
- ❌ Geen remote AH lijst synchroniseren
- ❌ Geen bezorgslots reserveren

## Experimentele features

De optie `experimental_cart_enabled` is standaard **uit**. Als deze in de toekomst cart-endpoints activeert:

- Vereist expliciete user confirmation per actie
- Nooit automatische checkout
- Duidelijke waarschuwing in UI

## Rate limiting & API belasting

- Minimum 500ms tussen API requests
- Exponential backoff bij 429/5xx
- Standaard receipt polling: 1x per uur
- Geen agressieve polling in automatiseringen

## Data opslag

| Data | Locatie |
|------|---------|
| Tokens | Home Assistant config entry (encrypted) |
| Shopping list | Home Assistant storage (`.storage/ah_shopping_list_*`) |
| Receipt cache | Coordinator memory (niet persistent) |

## Privacy

- Receipt data blijft lokaal in Home Assistant
- Geen data wordt gedeeld met derden
- API calls gaan direct naar `api.ah.nl`

## Aanbevelingen

1. Gebruik een dedicated AH account niet voor kritieke automatiseringen
2. Monitor logs na AH app updates (API kan wijzigen)
3. Deel geen diagnostics publiekelijk zonder te controleren op gevoelige data
4. Houd de integratie up-to-date via HACS

## Responsible disclosure

Als je een security issue vindt in deze integratie, open een GitHub issue of neem contact op met de maintainer. Deel geen live tokens in issues.

## Limitations

| Beperking | Impact |
|-----------|--------|
| OAuth via handmatige code | Geen native redirect in HA |
| Anonymous mode | Geen bonnen, beperkte API toegang |
| Lokale lijst only | Niet gesynchroniseerd met AH app |
| Geen product images in HA | Alleen via event data |
| API response variatie | Parsing kan falen bij API wijzigingen |
