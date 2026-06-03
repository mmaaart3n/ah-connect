"""Parse appie-go CLI config JSON for Home Assistant setup."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any

from .const import DEFAULT_CLIENT_ID
from .exceptions import AhConfigError

# Error keys for config flow translations
ERROR_INVALID_JSON = "invalid_json"
ERROR_MISSING_ACCESS_TOKEN = "missing_access_token"
ERROR_MISSING_REFRESH_TOKEN = "missing_refresh_token"
ERROR_INVALID_APPIE_CONFIG = "invalid_appie_config"


def _get_nested(data: dict[str, Any], *keys: str) -> Any:
    """Walk nested dicts trying multiple key variants."""
    current: Any = data
    for key_group in keys:
        if not isinstance(current, dict):
            return None
        found = None
        if isinstance(key_group, str):
            key_group = (key_group,)
        for k in key_group:
            if k in current:
                found = current[k]
                break
        if found is None:
            return None
        current = found
    return current


def _pick_str(data: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        val = data.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return None


def _parse_expires_at(raw: Any) -> str | None:
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return datetime.fromtimestamp(raw, tz=UTC).isoformat()
    if isinstance(raw, str):
        raw = raw.strip()
        if not raw:
            return None
        try:
            if raw.isdigit():
                return datetime.fromtimestamp(int(raw), tz=UTC).isoformat()
            # ISO format from appie-go config
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=UTC)
            return parsed.isoformat()
        except ValueError:
            return None
    return None


def parse_appie_config(raw_json: str) -> dict[str, Any]:
    """Parse appie-go config.json content into normalized token data.

    Supports appie-go native format (snake_case top-level) and fallbacks
    for camelCase and nested token/auth objects.
    """
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise AhConfigError(ERROR_INVALID_JSON) from exc

    if not isinstance(data, dict):
        raise AhConfigError(ERROR_INVALID_APPIE_CONFIG)

    token_obj = data.get("token") or data.get("Token") or {}
    auth_obj = data.get("auth") or data.get("Auth") or {}

    sources: list[dict[str, Any]] = [data]
    if isinstance(token_obj, dict):
        sources.append(token_obj)
    if isinstance(auth_obj, dict):
        sources.append(auth_obj)

    access_token: str | None = None
    refresh_token: str | None = None
    expires_at: str | None = None
    client_id: str | None = None
    member_id: str | None = None

    for src in sources:
        if access_token is None:
            access_token = _pick_str(src, "access_token", "accessToken")
        if refresh_token is None:
            refresh_token = _pick_str(src, "refresh_token", "refreshToken")
        if client_id is None:
            client_id = _pick_str(src, "client_id", "clientId")
        if member_id is None:
            mid = src.get("member_id") or src.get("memberId") or src.get("memberID")
            if mid is not None:
                member_id = str(mid)
        if expires_at is None:
            expires_at = _parse_expires_at(
                src.get("expires_at")
                or src.get("expiresAt")
                or src.get("expiry")
                or src.get("expires_in")
            )

    if not access_token:
        raise AhConfigError(ERROR_MISSING_ACCESS_TOKEN)
    if not refresh_token:
        raise AhConfigError(ERROR_MISSING_REFRESH_TOKEN)

    if not expires_at:
        expires_at = (datetime.now(tz=UTC) + timedelta(seconds=300)).isoformat()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_at": expires_at,
        "client_id": client_id or DEFAULT_CLIENT_ID,
        "member_id": member_id,
        "anonymous": False,
    }
