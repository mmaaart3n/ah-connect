# AH Shopping – Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![Validate](https://github.com/mmaaart3n/ah-connect/actions/workflows/validate.yml/badge.svg)](https://github.com/mmaaart3n/ah-connect/actions/workflows/validate.yml)

Home Assistant custom integration voor **Albert Heijn**, gebouwd op de onofficiële Appie mobiele API. Technische referentie: [appie-go](https://github.com/gwillem/appie-go) (Python-port, geen Go-runtime).

> **Waarschuwing:** Dit is een **onofficiële, ongedocumenteerde API**. Albert Heijn kan endpoints op elk moment wijzigen of blokkeren. Gebruik op eigen risico. **Geen checkout of bestellingen** in de MVP.

## Functies (MVP)

| Functie | Anonymous | Authenticated |
|---------|-----------|---------------|
| Producten zoeken | ✅ | ✅ |
| Lokale boodschappenlijst | ✅ | ✅ |
| Bon-sensoren | ❌ | ✅ |
| Automatische token refresh | — | ✅ |
| Export naar HA todo | ✅ | ✅ |

## Installatie

### Via HACS (aanbevolen)

1. Open **HACS → Integrations** (drie puntjes → **Custom repositories**).
2. Voeg toe:
   - **Repository URL:** `https://github.com/mmaaart3n/ah-connect`
   - **Category:** Integration
3. Zoek **AH Shopping** en installeer.
4. **Herstart Home Assistant.**
5. Ga naar **Instellingen → Apparaten & services → Integratie toevoegen** en zoek op **AH Shopping**.

Zie [docs/INSTALLATION.md](docs/INSTALLATION.md) voor gedetailleerde instructies.

### Handmatig

1. Download of clone [https://github.com/mmaaart3n/ah-connect](https://github.com/mmaaart3n/ah-connect)
2. Kopieer `custom_components/ah_shopping/` naar je Home Assistant `config/custom_components/` map
3. Herstart Home Assistant
4. Voeg de integratie toe via de UI

## Configuratie

Alle configuratie verloopt via de **Home Assistant UI** (geen YAML vereist):

1. **Config flow** – kies Anonymous of Authenticated (OAuth-code)
2. **Options flow** – scan interval, max zoekresultaten, bon-sensoren aan/uit

Zie [docs/AUTHENTICATION.md](docs/AUTHENTICATION.md) voor OAuth-instructies.

## Snel starten

### Anonymous mode (alleen zoeken)

1. Kies **Anonymous** tijdens setup.
2. Roep de zoek-service aan:

```yaml
service: ah_shopping.search_products
data:
  query: melk
  limit: 5
```

### Authenticated mode (bonnen + zoeken)

1. Kies **Authenticated** tijdens setup.
2. Open de OAuth URL (zie [docs/AUTHENTICATION.md](docs/AUTHENTICATION.md)).
3. Plak de autorisatiecode in de config flow.

## Services

| Service | Beschrijving |
|---------|-------------|
| `ah_shopping.search_products` | Zoek producten op AH |
| `ah_shopping.add_to_list` | Voeg product toe aan lokale lijst |
| `ah_shopping.remove_from_list` | Verwijder product van lijst |
| `ah_shopping.clear_list` | Maak lijst leeg |
| `ah_shopping.get_list` | Haal lijst op (via event) |
| `ah_shopping.refresh_receipts` | Vernieuw bondata (authenticated) |
| `ah_shopping.export_list_to_todo` | Exporteer lijst naar HA todo |

Zie [docs/SERVICES.md](docs/SERVICES.md) voor alle details.

## Sensoren

| Entiteit | Beschrijving |
|----------|-------------|
| `sensor.ah_shopping_list_count` | Aantal items op lokale lijst |
| `sensor.ah_last_receipt_total` | Totaalbedrag laatste bon (authenticated) |
| `sensor.ah_last_receipt_date` | Datum laatste bon (authenticated) |

## Voorbeeldautomatiseringen

Zie [examples/automations.yaml](examples/automations.yaml).

## Security & beperkingen

- Tokens worden nooit gelogd of getoond in diagnostics
- Geen checkout of order placement
- Rate limiting en retry/backoff ingebouwd
- Onofficiële API – geen garantie op stabiliteit

Zie [docs/SECURITY_AND_LIMITATIONS.md](docs/SECURITY_AND_LIMITATIONS.md).

## Troubleshooting

Zie [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).

## Documentatie

- [Installatie](docs/INSTALLATION.md)
- [Authenticatie](docs/AUTHENTICATION.md)
- [Services](docs/SERVICES.md)
- [API Discovery](docs/AH_API_DISCOVERY.md)
- [GitHub repository setup](docs/GITHUB_REPOSITORY_SETUP.md)
- [appie-go referentie](docs/APPIE_GO_REFERENCE.md)
- [Roadmap](docs/ROADMAP.md)

## Issues & support

Problemen of vragen? Open een issue:

**https://github.com/mmaaart3n/ah-connect/issues**

## Ontwikkeling

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install pytest pytest-asyncio aiohttp voluptuous
PYTHONPATH=. pytest tests/ -v
```

## Disclaimer

Deze integratie gebruikt een **onofficiële, ongedocumenteerde API**. Albert Heijn kan toegang op elk moment wijzigen of blokkeren. Gebruik op eigen risico. Er worden **geen bestellingen geplaatst** in de MVP.

## Licentie

MIT
