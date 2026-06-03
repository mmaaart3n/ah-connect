# AH Connect

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![Validate](https://github.com/mmaaart3n/ah-connect/actions/workflows/validate.yml/badge.svg)](https://github.com/mmaaart3n/ah-connect/actions/workflows/validate.yml)

**AH Connect** is a Home Assistant custom integration for Albert Heijn product search, shopping lists, receipts and optional experimental order/cart features.

It is a **Python-native** Home Assistant integration, functionally inspired by [appie-go](https://github.com/gwillem/appie-go). appie-go is the only technical/API reference. appie-go is not used as a runtime dependency and no Go code is copied.

> **Warning:** This integration uses the **unofficial** Albert Heijn mobile API. It may break without notice. Never share tokens, config JSON, logs or screenshots containing credentials.

## Features

- Product search (anonymous or authenticated)
- Bonus products and laatste-kans koopjes (by postal code)
- Receipts (kassabonnen) when authenticated
- Remote AH shopping lists (authenticated)
- Optional experimental order/cart services (no checkout)

## Not supported

- Checkout / place order / payment / finalize order

## Installation (HACS)

1. Add custom repository: `https://github.com/mmaaart3n/ah-connect`
2. Category: **Integration**
3. Install **AH Connect** and restart Home Assistant
4. Add integration via **Settings → Devices & services**

## Configuration

### Recommended: authenticated via appie-go CLI

On a machine with Go:

```bash
go install github.com/gwillem/appie-go/cmd/appie@latest
appie login
cat ~/.config/appie/config.json
```

In Home Assistant:

1. Add **AH Connect**
2. Choose **Authenticated via appie-go config**
3. Paste the full JSON from `~/.config/appie/config.json`

### Anonymous mode

Choose **Anonymous** for product search and bonus only (no personal data).

### Advanced fallback

**Advanced fallback: authorization code** — only if CLI import is not possible. See [docs/AUTHENTICATION.md](docs/AUTHENTICATION.md).

## Services

Results are published on the `ah_connect_result` event.

| Service | Auth | Notes |
|---------|------|-------|
| `ah_connect.search_products` | Optional | |
| `ah_connect.get_bonus_products` | Optional | |
| `ah_connect.get_koopjes` | Optional | Requires `postal_code` |
| `ah_connect.get_receipts` | Required | |
| `ah_connect.get_shopping_lists` | Required | |
| `ah_connect.get_order` | Required | Experimental option |

Full list: [docs/SERVICES.md](docs/SERVICES.md)

## Sensors

- Last receipt total/date (authenticated, option)
- Remote shopping list count (authenticated, option)
- Bonus product count (option)
- Order total/items (experimental, authenticated)

## Security

- Tokens are stored in the config entry
- Diagnostics redact secrets
- Do not share `config.json` or HA config entry exports

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install pytest pytest-asyncio aiohttp voluptuous
PYTHONPATH=. pytest tests/ -v
```

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

## Changelog

### 1.0.0

- First HACS release of rebuilt **AH Connect** (`ah_connect`)
- Replaces the pre-1.0.0 integration; do not use tag v0.2.0

### 0.1.0 (development)

- Initial clean appie-go focused build
- Domain `ah_connect`, integration name **AH Connect**
- appie-go config JSON import as primary authentication
- Anonymous and advanced authorization-code fallback modes

## License

MIT — Albert Heijn and appie-go are separate projects; appie-go is AGPLv3.
