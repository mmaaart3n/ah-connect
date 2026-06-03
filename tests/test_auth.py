"""Tests for auth manager."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from custom_components.ah_connect.auth import AhAuthManager
from custom_components.ah_connect.const import (
    CONF_ACCESS_TOKEN,
    CONF_ANONYMOUS,
    CONF_EXPIRES_AT,
    CONF_REFRESH_TOKEN,
)


def _entry(data: dict):
    entry = MagicMock()
    entry.data = data
    return entry


def test_is_anonymous():
    auth = AhAuthManager(MagicMock(), _entry({CONF_ANONYMOUS: True}))
    assert auth.is_anonymous is True


def test_is_authenticated():
    auth = AhAuthManager(
        MagicMock(), _entry({CONF_ANONYMOUS: False, CONF_ACCESS_TOKEN: "x"})
    )
    assert auth.is_anonymous is False


def test_expiry_detection():
    expired = (datetime.now(tz=UTC) - timedelta(hours=1)).isoformat()
    auth = AhAuthManager(
        MagicMock(),
        _entry(
            {
                CONF_ANONYMOUS: False,
                CONF_ACCESS_TOKEN: "x",
                CONF_REFRESH_TOKEN: "r",
                CONF_EXPIRES_AT: expired,
            }
        ),
    )
    assert auth._is_expired() is True
