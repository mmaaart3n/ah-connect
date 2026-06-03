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

```
https://login.ah.nl/secure/oauth/authorize?client_id=appie&redirect_uri=appie://login-exit&response_type=code
```

Log in met je Albert Heijn / Mijn AH account.

### Stap 2: Authorization code kopiëren

Na succesvolle login word je doorgestuurd naar een URL als:

```
appie://login-exit?code=AUTHORIZATION_CODE_HERE
```

De browser toont mogelijk een foutmelding ("kan pagina niet openen") — dat is normaal. Kopieer de `code` parameter uit de URL-balk.

> **Tip:** Op Android/iOS met de Appie app geïnstalleerd opent de redirect in de app. Gebruik in dat geval een desktop browser of kopieer de code uit de redirect-URL via developer tools.

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
