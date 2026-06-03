# Troubleshooting

## HACS does not show the integration

- Repository URL: `https://github.com/mmaaart3n/ah-connect`
- Category: Integration
- Clear HACS cache and reload

## Invalid config JSON

- Ensure full file from `~/.config/appie/config.json` after `appie login`
- Must contain `access_token` and `refresh_token` (snake_case in appie-go)

## 401 / token expired

- Re-run `appie login` and re-import config, or wait for automatic refresh (authenticated mode)

## Service: authenticated required

- Use authenticated setup, not anonymous mode

## Experimental feature disabled

- Enable **Experimental order** in integration options

## Debug logging

- Enable **Debug API logging** in options (does not log token values)
