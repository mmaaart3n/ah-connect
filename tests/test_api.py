"""Tests for API client constants and guards."""

from unittest.mock import MagicMock

import pytest

from custom_components.ah_connect.api import AhConnectApiClient
from custom_components.ah_connect.auth import AhAuthManager
from custom_components.ah_connect.const import (
    DEFAULT_CLIENT_ID,
    PATH_AUTH_ANONYMOUS,
    PATH_AUTH_REFRESH,
    PATH_AUTH_TOKEN,
)
from custom_components.ah_connect.exceptions import AhAuthenticatedModeRequired


def test_appie_go_auth_paths():
    assert PATH_AUTH_ANONYMOUS == "/mobile-auth/v1/auth/token/anonymous"
    assert PATH_AUTH_TOKEN == "/mobile-auth/v1/auth/token"
    assert PATH_AUTH_REFRESH == "/mobile-auth/v1/auth/token/refresh"


def test_default_client_id():
    assert DEFAULT_CLIENT_ID == "appie-ios"


def test_authenticated_required():
    entry = MagicMock()
    entry.data = {"anonymous": True}
    auth = AhAuthManager(MagicMock(), entry)
    api = AhConnectApiClient(MagicMock(), auth, {})
    with pytest.raises(AhAuthenticatedModeRequired):
        api._require_authenticated()
