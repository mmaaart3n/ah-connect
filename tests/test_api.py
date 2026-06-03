"""Tests for AH API client."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.ah_shopping.api import AhApiClient
from custom_components.ah_shopping.exceptions import AhAuthError, AhRateLimitError


@pytest.fixture
def mock_auth():
    auth = MagicMock()
    auth.get_access_token = AsyncMock(return_value="test-token")
    auth.is_anonymous = False
    return auth


@pytest.fixture
def api_client(mock_auth):
    hass = MagicMock()
    entry = MagicMock()
    entry.options = {}
    entry.data = {}
    return AhApiClient(hass, mock_auth, entry)


class TestExtractProductList:
    """Test product list extraction from various response shapes."""

    def test_flat_list(self, api_client):
        data = [{"webshopId": 1, "title": "A"}]
        result = api_client._extract_product_list(data)
        assert len(result) == 1

    def test_products_key(self, api_client):
        data = {"products": [{"webshopId": 1, "title": "A"}]}
        result = api_client._extract_product_list(data)
        assert len(result) == 1

    def test_nested_search_result(self, api_client):
        data = {"searchResult": {"products": [{"webshopId": 1, "title": "A"}]}}
        result = api_client._extract_product_list(data)
        assert len(result) == 1

    def test_empty(self, api_client):
        assert api_client._extract_product_list({}) == []
        assert api_client._extract_product_list("invalid") == []


class TestExtractReceiptList:
    """Test receipt list extraction."""

    def test_receipts_key(self, api_client):
        data = {"receipts": [{"transactionId": "abc"}]}
        result = api_client._extract_receipt_list(data)
        assert len(result) == 1


class TestGetReceiptsAnonymous:
    """Test that receipts require auth."""

    async def test_anonymous_raises(self, api_client, mock_auth):
        mock_auth.is_anonymous = True
        with pytest.raises(AhAuthError):
            await api_client.get_receipts()
