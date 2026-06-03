"""Tests for AH auth manager."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.ah_shopping.auth import AhAuthManager
from custom_components.ah_shopping.const import CONF_ACCESS_TOKEN, CONF_ANONYMOUS, CONF_EXPIRES_AT
from custom_components.ah_shopping.exceptions import AhAuthError


@pytest.fixture
def anonymous_entry():
    entry = MagicMock()
    entry.data = {CONF_ANONYMOUS: True}
    entry.entry_id = "test"
    return entry


@pytest.fixture
def authenticated_entry():
    expires = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    entry = MagicMock()
    entry.data = {
        CONF_ANONYMOUS: False,
        CONF_ACCESS_TOKEN: "valid-token",
        "refresh_token": "refresh-token",
        CONF_EXPIRES_AT: expires,
    }
    entry.entry_id = "test"
    return entry


class TestAhAuthManager:
    """Test auth manager properties and token logic."""

    def test_is_anonymous(self, anonymous_entry):
        auth = AhAuthManager(MagicMock(), anonymous_entry)
        assert auth.is_anonymous is True
        assert auth.is_authenticated is False

    def test_is_authenticated(self, authenticated_entry):
        auth = AhAuthManager(MagicMock(), authenticated_entry)
        assert auth.is_anonymous is False
        assert auth.is_authenticated is True

    def test_token_needs_refresh_expired(self, authenticated_entry):
        authenticated_entry.data[CONF_EXPIRES_AT] = (
            datetime.now(timezone.utc) - timedelta(hours=1)
        ).isoformat()
        auth = AhAuthManager(MagicMock(), authenticated_entry)
        assert auth._token_needs_refresh() is True

    def test_token_needs_refresh_valid(self, authenticated_entry):
        auth = AhAuthManager(MagicMock(), authenticated_entry)
        assert auth._token_needs_refresh() is False

    async def test_get_access_token_authenticated(self, authenticated_entry):
        auth = AhAuthManager(MagicMock(), authenticated_entry)
        token = await auth.get_access_token()
        assert token == "valid-token"

    async def test_get_access_token_not_authenticated_raises(self):
        entry = MagicMock()
        entry.data = {CONF_ANONYMOUS: False}
        entry.entry_id = "test"
        auth = AhAuthManager(MagicMock(), entry)
        with pytest.raises(AhAuthError):
            await auth.get_access_token()

    def test_parse_token_response(self, authenticated_entry):
        auth = AhAuthManager(MagicMock(), authenticated_entry)
        result = auth._parse_token_response(
            {"access_token": "new-token", "refresh_token": "new-refresh", "expires_in": 3600}
        )
        assert result[CONF_ACCESS_TOKEN] == "new-token"
        assert result["refresh_token"] == "new-refresh"
        assert CONF_EXPIRES_AT in result

    def test_parse_token_response_missing_token(self, authenticated_entry):
        auth = AhAuthManager(MagicMock(), authenticated_entry)
        with pytest.raises(AhAuthError):
            auth._parse_token_response({})
