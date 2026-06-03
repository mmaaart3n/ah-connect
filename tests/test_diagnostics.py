"""Tests for diagnostics redaction."""

from custom_components.ah_connect.diagnostics import REDACT_LIST


def test_redact_list_includes_tokens():
    assert "access_token" in REDACT_LIST
    assert "refresh_token" in REDACT_LIST
    assert "authorization" in REDACT_LIST


def test_nested_redaction_via_conftest():
    from tests.conftest import _redact

    data = {
        "options": {"scan_interval": 300},
        "nested": {"access_token": "secret", "ok": "visible"},
    }
    redacted = _redact(data, REDACT_LIST)
    assert redacted["nested"]["access_token"] == "***REDACTED***"
    assert redacted["nested"]["ok"] == "visible"
