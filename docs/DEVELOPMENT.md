# Development

## Setup

```bash
cd ah-connect
python -m venv .venv
source .venv/bin/activate
pip install pytest pytest-asyncio aiohttp voluptuous
```

## Tests

```bash
PYTHONPATH=. pytest tests/ -v
```

No live AH API calls in unit tests.

## Structure

```
custom_components/ah_connect/
  api.py          # API client (appie-go aligned)
  auth.py         # Token management
  appie_config.py # CLI config import parser
  config_flow.py
  coordinator.py
  services.py
```

## CI

GitHub Actions: pytest, HACS validation, hassfest.
