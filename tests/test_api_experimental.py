"""Tests for experimental and auth-gated API methods."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.ah_shopping.api import AhApiClient
from custom_components.ah_shopping.const import CONF_EXPERIMENTAL_ORDER
from custom_components.ah_shopping.exceptions import AhAuthError, AhExperimentalFeatureDisabled, AhNotImplementedError


@pytest.fixture
def api_client():
    hass = MagicMock()
    auth = MagicMock()
    auth.is_anonymous = False
    auth.get_access_token = AsyncMock(return_value="token")
    auth.client_id = "appie-ios"
    entry = MagicMock()
    entry.options = {CONF_EXPERIMENTAL_ORDER: False}
    entry.data = {}
    return AhApiClient(hass, auth, entry)


class TestExperimentalGating:
    async def test_get_order_disabled(self, api_client):
        with pytest.raises(AhExperimentalFeatureDisabled):
            await api_client.get_order()

    async def test_get_receipts_anonymous(self):
        hass = MagicMock()
        auth = MagicMock()
        auth.is_anonymous = True
        entry = MagicMock()
        entry.options = {}
        client = AhApiClient(hass, auth, entry)
        with pytest.raises(AhAuthError):
            await client.get_receipts()

    async def test_search_stores_not_implemented(self, api_client):
        with pytest.raises(AhNotImplementedError):
            await api_client.search_stores("3521GZ")
