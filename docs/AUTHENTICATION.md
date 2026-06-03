# Authenticatie

AH Shopping ondersteunt twee authenticatiemodi via de onofficiële Appie mobile API.

## Anonymous mode

Geschikt voor product zoeken zonder AH-account.

**Endpoint:**

```
POST https://api.ah.nl/mobile-auth/v1/auth/token/anonymous
Content-Type: application/json

{"clientId": "appie"}
```

**Response:** `access_token`, `expires_in`

Het anonieme token wordt bij elke API-call opnieuw opgehaald (niet opgeslagen in config entry).

## Authenticated mode (OAuth)

Vereist voor bon-sensoren en toekomstige functies (remote lijst, mandje).

### Stap 1: Authorize URL openen

Open deze URL in een **desktop browser** (Chrome, Firefox, Safari):

```
https://login.ah.nl/login?client_id=appie-ios&response_type=code&redirect_uri=appie://login-exit
```

> Legacy URL (oudere gist): `client_id=appie` op `/secure/oauth/authorize` – werkt mogelijk nog, maar de integratie gebruikt standaard **appie-ios** (referentie: [appie-go](https://github.com/gwillem/appie-go)).

Log in met je Albert Heijn / Mijn AH account (inclusief MFA/2FA indien gevraagd).

> **User-Agent (optioneel):** De [Appie API gist](https://gist.github.com/jabbink/8bfa44bdfc535d696b340c46d228fdd1) adviseert `User-Agent: Appie/8.22.3` voor API-calls. Voor de **browser-login** is dat meestal niet nodig. Alleen bij problemen: gebruik een User-Agent-switcher extensie en zet tijdelijk `Appie/8.22.3` voor `login.ah.nl`.

### Stap 2: Authorization code kopiëren

Na succesvolle login word je doorgestuurd. In de console of op het scherm zie je vaak:

```
Failed to launch 'appie://login-exit?code=XXXXXXXX' because the scheme does not have a registered handler.
```

**Dat is geen fout — dat betekent dat de login gelukt is.** Je computer heeft geen Appie-app om `appie://` te openen; de code staat in die URL.

Kopieer alleen het deel **na** `code=`:

```
4154ab6d-a4e9-4868-a866-94af727d9d79
```

De code is **kort geldig** (enkele minuten). Plak hem direct in Home Assistant.

> **Tip:** Staat de code niet in de adresbalk? Open F12 → **Console** of **Network** en zoek naar `appie://login-exit?code=`.

### Stap 3: Code invoeren in config flow

Plak de code in het veld **Autorisatiecode** in Home Assistant.

**Endpoint (achter de schermen):**

```
POST https://api.ah.nl/mobile-auth/v1/auth/token
Content-Type: application/json

{"clientId": "appie", "code": "YOUR_CODE"}
```

**Response:** `access_token`, `refresh_token`, `expires_in`

### Token opslag

Tokens worden opgeslagen in de config entry:

| Veld | Beschrijving |
|------|-------------|
| `access_token` | Bearer token voor API calls |
| `refresh_token` | Token voor vernieuwing |
| `expires_at` | ISO timestamp van verloop |

Tokens worden **nooit** gelogd, getoond in diagnostics of opgeslagen in YAML.

## Automatische token refresh

De integratie vernieuwt het access token automatisch **5 minuten vóór verloop**.

**Endpoint:**

```
POST https://api.ah.nl/mobile-auth/v1/auth/token/refresh
Content-Type: application/json

{"clientId": "appie", "refreshToken": "REFRESH_TOKEN"}
```

Als refresh faalt (bijv. refresh token verlopen), moet je opnieuw inloggen via de config flow.

## Opnieuw authenticeren

1. Verwijder de bestaande config entry.
2. Voeg AH Shopping opnieuw toe.
3. Kies **Authenticated** en volg de OAuth stappen.

> Toekomstige versies kunnen een re-auth flow toevoegen zonder entry te verwijderen.

## HTTP Headers

Alle requests gebruiken:

```
User-Agent: Appie/8.22.3
Content-Type: application/json
Authorization: Bearer ACCESS_TOKEN
```

## Veiligheid

- Deel nooit je authorization code of tokens.
- Gebruik geen hardcoded tokens in automatiseringen of scripts.
- Tokens staan alleen in de encrypted config entry storage van Home Assistant.
