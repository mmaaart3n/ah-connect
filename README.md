# AH Shopping – Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![Validate](https://github.com/mmaaart3n/ah-connect/actions/workflows/validate.yml/badge.svg)](https://github.com/mmaaart3n/ah-connect/actions/workflows/validate.yml)

Home Assistant custom integration voor **Albert Heijn**, gebouwd op de onofficiële Appie mobiele API.

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

1. Voeg deze repository toe als [custom repository](https://hacs.xyz/docs/faq/custom_repositories/) in HACS (category: Integration).
2. Installeer **AH Shopping**.
3. Herstart Home Assistant.
4. Ga naar **Instellingen → Apparaten & services → Integratie toevoegen** en zoek op **AH Shopping**.

Zie [docs/INSTALLATION.md](docs/INSTALLATION.md) voor gedetailleerde instructies.

### Handmatig

Kopieer de map `custom_components/ah_shopping` naar je Home Assistant `custom_components` directory en herstart.

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

## Documentatie

- [Installatie](docs/INSTALLATION.md)
- [Authenticatie](docs/AUTHENTICATION.md)
- [Services](docs/SERVICES.md)
- [API Discovery](docs/AH_API_DISCOVERY.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Security & Limitations](docs/SECURITY_AND_LIMITATIONS.md)
- [Roadmap](docs/ROADMAP.md)

## Ontwikkeling

```bash
# Tests draaien
pip install pytest pytest-asyncio aiohttp voluptuous
pytest tests/ -v
```

## Disclaimer

Deze integratie gebruikt een **onofficiële, gedocumenteerde API**. Albert Heijn kan toegang op elk moment wijzigen of blokkeren. Gebruik op eigen risico. Er worden **geen bestellingen geplaatst** in de MVP.

## Licentie

MIT
