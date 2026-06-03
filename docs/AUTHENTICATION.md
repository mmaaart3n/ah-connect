# Authentication

## Primary: appie-go CLI config import

1. Install CLI: `go install github.com/gwillem/appie-go/cmd/appie@latest`
2. Login: `appie login`
3. Config path: `~/.config/appie/config.json` (or `$XDG_CONFIG_HOME/appie/config.json`)
4. In Home Assistant: add AH Connect → **Authenticated via appie-go config** → paste JSON

The integration stores normalized tokens in the config entry and refreshes access tokens automatically.

## Anonymous mode

No login. Used for product search, bonus and koopjes. An anonymous token is fetched on startup.

## Advanced fallback: authorization code

Only when CLI import is not possible. Use the appie-go compatible OAuth flow (`appie login` URL pattern). Paste the authorization code in Home Assistant.

This path is for debugging; **not recommended** for daily use.

## Security

- Never share `config.json`, tokens, diagnostics exports or logs with credentials
- Revoke access by removing the HA config entry and logging out in the AH app if needed
