"""Pytest configuration for AH Shopping tests."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

# Add project root so custom_components can be imported
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock Home Assistant modules (not installed in unit test environment)
_HA_MODULES = [
    "homeassistant",
    "homeassistant.config_entries",
    "homeassistant.core",
    "homeassistant.data_entry_flow",
    "homeassistant.helpers",
    "homeassistant.helpers.aiohttp_client",
    "homeassistant.helpers.config_validation",
    "homeassistant.helpers.entity",
    "homeassistant.helpers.entity_platform",
    "homeassistant.helpers.storage",
    "homeassistant.helpers.update_coordinator",
    "homeassistant.helpers.entity_registry",
    "homeassistant.components",
    "homeassistant.components.sensor",
    "homeassistant.components.diagnostics",
    "homeassistant.helpers.aiohttp_client",
]

for _mod in _HA_MODULES:
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()

# Minimal config_entries base for config_flow
sys.modules["homeassistant"].config_entries = sys.modules["homeassistant.config_entries"]
sys.modules["homeassistant.config_entries"].ConfigFlow = type(
    "ConfigFlow", (), {"VERSION": 1, "domain": "ah_shopping"}
)
sys.modules["homeassistant.config_entries"].OptionsFlow = type("OptionsFlow", (), {})
