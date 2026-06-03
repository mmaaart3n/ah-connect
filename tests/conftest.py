"""Pytest configuration for AH Connect tests."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

_HA_MODULES = [
    "homeassistant",
    "homeassistant.config_entries",
    "homeassistant.core",
    "homeassistant.const",
    "homeassistant.data_entry_flow",
    "homeassistant.exceptions",
    "homeassistant.helpers",
    "homeassistant.helpers.aiohttp_client",
    "homeassistant.helpers.config_validation",
    "homeassistant.helpers.entity",
    "homeassistant.helpers.entity_platform",
    "homeassistant.helpers.update_coordinator",
    "homeassistant.helpers.entity_registry",
    "homeassistant.components",
    "homeassistant.components.sensor",
    "homeassistant.components.diagnostics",
]

for _mod in _HA_MODULES:
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()

sys.modules["homeassistant.config_entries"].ConfigFlow = type(
    "ConfigFlow", (), {"VERSION": 1, "domain": "ah_connect"}
)
sys.modules["homeassistant.config_entries"].OptionsFlow = type("OptionsFlow", (), {})
sys.modules["homeassistant.components.sensor"].SensorEntity = type("SensorEntity", (), {})
sys.modules["homeassistant.helpers.update_coordinator"].DataUpdateCoordinator = type(
    "DataUpdateCoordinator", (), {}
)
sys.modules["homeassistant.helpers.update_coordinator"].UpdateFailed = Exception
sys.modules["homeassistant.helpers.entity"].EntityCategory = MagicMock()
sys.modules["homeassistant.helpers.entity"].EntityCategory.DIAGNOSTIC = "diagnostic"
sys.modules["homeassistant.components.diagnostics"].async_redact_data = lambda data, keys: _redact(data, keys)


def _redact(data, keys):
    if isinstance(data, dict):
        return {
            k: "***REDACTED***"
            if any(rk.lower() in k.lower() for rk in keys)
            else _redact(v, keys)
            for k, v in data.items()
        }
    if isinstance(data, list):
        return [_redact(i, keys) for i in data]
    return data
