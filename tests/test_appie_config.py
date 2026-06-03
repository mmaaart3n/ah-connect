"""Tests for appie-go config parser."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from custom_components.ah_connect.appie_config import (
    ERROR_INVALID_JSON,
    ERROR_MISSING_ACCESS_TOKEN,
    ERROR_MISSING_REFRESH_TOKEN,
    parse_appie_config,
)
from custom_components.ah_connect.const import DEFAULT_CLIENT_ID
from custom_components.ah_connect.exceptions import AhConfigError


def test_valid_appie_go_format():
    raw = json.dumps(
        {
            "access_token": "at_123",
            "refresh_token": "rt_456",
            "expires_at": "2026-06-01T12:00:00+00:00",
            "member_id": "42",
        }
    )
    result = parse_appie_config(raw)
    assert result["access_token"] == "at_123"
    assert result["refresh_token"] == "rt_456"
    assert result["client_id"] == DEFAULT_CLIENT_ID
    assert result["anonymous"] is False


def test_snake_case_top_level():
    raw = json.dumps(
        {
            "access_token": "a",
            "refresh_token": "r",
            "client_id": "appie-ios",
        }
    )
    result = parse_appie_config(raw)
    assert result["client_id"] == "appie-ios"


def test_camel_case():
    raw = json.dumps(
        {
            "accessToken": "a",
            "refreshToken": "r",
            "clientId": "appie-ios",
            "expiresAt": "2026-01-01T00:00:00Z",
        }
    )
    result = parse_appie_config(raw)
    assert result["access_token"] == "a"
    assert result["refresh_token"] == "r"


def test_nested_token_object():
    raw = json.dumps(
        {
            "token": {
                "access_token": "nested_at",
                "refresh_token": "nested_rt",
            }
        }
    )
    result = parse_appie_config(raw)
    assert result["access_token"] == "nested_at"


def test_nested_auth_object():
    raw = json.dumps(
        {
            "auth": {
                "accessToken": "auth_at",
                "refreshToken": "auth_rt",
            }
        }
    )
    result = parse_appie_config(raw)
    assert result["access_token"] == "auth_at"


def test_invalid_json():
    with pytest.raises(AhConfigError) as exc:
        parse_appie_config("{not json")
    assert str(exc.value) == ERROR_INVALID_JSON


def test_missing_access_token():
    with pytest.raises(AhConfigError) as exc:
        parse_appie_config('{"refresh_token": "r"}')
    assert str(exc.value) == ERROR_MISSING_ACCESS_TOKEN


def test_missing_refresh_token():
    with pytest.raises(AhConfigError) as exc:
        parse_appie_config('{"access_token": "a"}')
    assert str(exc.value) == ERROR_MISSING_REFRESH_TOKEN


def test_missing_expiry_gets_default():
    raw = json.dumps({"access_token": "a", "refresh_token": "r"})
    result = parse_appie_config(raw)
    assert result["expires_at"]
    expires = datetime.fromisoformat(result["expires_at"])
    assert expires.tzinfo is not None
