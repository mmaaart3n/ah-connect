# Troubleshooting

## Config flow

### "Could not connect to the AH API"

- Controleer internetverbinding van je Home Assistant instance.
- AH API kan tijdelijk offline zijn — probeer later opnieuw.
- Controleer of je geen firewall/proxy de requests blokkeert.

### "Invalid or expired authorization code"

- OAuth codes zijn **kort geldig** (meestal enkele minuten). Kopieer en plak direct.
- Zorg dat je de volledige code kopieert zonder extra spaties.
- Start opnieuw: open de authorize URL opnieuw en log opnieuw in.

### Redirect opent niet / geen code zichtbaar

- Gebruik een **desktop browser** in plaats van mobiel.
- Open developer tools (F12) → Network tab → volg redirects.
- De code staat in `appie://login-exit?code=XXXX`.

### Console: `Failed to launch 'appie://login-exit?code=...'`

**Dit is normaal en betekent meestal succes.** De browser kan het `appie://`-protocol niet openen zonder de Appie-app.

1. Kopieer de UUID uit de foutmelding (alles na `code=`).
2. Plak direct in Home Assistant → AH Shopping config flow → **Autorisatiecode**.
3. Wacht niet te lang — codes verlopen snel.

Voorbeeld uit console:

```
appie://login-exit?code=4154ab6d-a4e9-4868-a866-94af727d9d79
```

→ plak: `4154ab6d-a4e9-4868-a866-94af727d9d79`

### Console: `POST .../login/api/login/mfa 400 (Bad Request)`

Dit komt van de **AH login-pagina** (`login.ah.nl`), niet van de Home Assistant-integratie.

Mogelijke oorzaken:

- Verkeerde of verlopen MFA/2FA-code
- Sessie verlopen — begin opnieuw via de OAuth authorize URL
- Adblocker/privacy-extensie die cookies blokkeert
- Inloggen in meerdere tabs tegelijk

**Als je daarna wél `appie://login-exit?code=...` ziet, negeer de MFA 400** en gebruik die code in Home Assistant.

Probeer anders: incognito venster, andere browser, of tijdelijk extensies uitzetten voor `login.ah.nl`.

## Services

### search_products geeft geen resultaten

- Controleer spelling van de zoekterm.
- Probeer een algemenere term ("melk" i.p.v. specifiek merk).
- Bekijk Home Assistant logs: **Instellingen → Systeem → Logboeken**.
- Filter op `ah_shopping`.

### search_products faalt met auth error (authenticated mode)

- Token is mogelijk verlopen en refresh mislukt.
- Verwijder en voeg integratie opnieuw toe met nieuwe OAuth code.

## Sensoren

### Bon-sensoren tonen "unavailable"

- Alleen beschikbaar in **authenticated mode**.
- Controleer optie "Enable receipt sensors" in integratie-instellingen.
- Roep `ah_shopping.refresh_receipts` aan om handmatig te vernieuwen.

### sensor.ah_shopping_list_count update niet

- Sensor luistert naar `ah_shopping_list_updated` events.
- Controleer of services correct worden aangeroepen.
- Herstart de integratie via **Instellingen → Apparaten & services → AH Shopping → Herladen**.

## Logs inschakelen

Voeg toe aan `configuration.yaml`:

```yaml
logger:
  logs:
    custom_components.ah_shopping: debug
```

> Tokens worden nooit gelogd, ook niet op debug niveau.

## Diagnostics

Download diagnostics via **Instellingen → Apparaten & services → AH Shopping → Diagnostics**.

Bevat:
- Auth mode (anonymous/authenticated)
- Token aanwezigheid (niet de waarden)
- Shopping list count
- Laatste bon samenvatting

## Rate limiting

Bij veel opeenvolgende zoekopdrachten kan de API rate limiting toepassen.

- Wacht enkele minuten.
- Vermijd het pollen van search_products in automatiseringen.
- Standaard throttle: 500ms tussen requests.

## HACS / Installatie

### Integratie verschijnt niet

- Herstart Home Assistant na installatie.
- Controleer dat `custom_components/ah_shopping/manifest.json` bestaat.
- Controleer logs op import errors.

### HACS validatie faalt

- Zorg dat `hacs.json` in de repository root staat.
- Controleer GitHub Actions workflow resultaten.

## Veelgestelde vragen

**Kan ik bestellen via Home Assistant?**
Nee, niet in MVP. Zie [ROADMAP.md](ROADMAP.md).

**Werkt dit met AH Premium / bezorging?**
MVP ondersteunt alleen zoeken, lokale lijst en bonnen. Bezorging is gepland voor latere fases.

**Is dit officieel van Albert Heijn?**
Nee. Onofficiële integratie op eigen risico.
