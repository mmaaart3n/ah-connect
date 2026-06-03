"""Config flow for AH Connect."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .appie_config import parse_appie_config
from .const import (
    AUTH_METHOD_ANONYMOUS,
    AUTH_METHOD_APPIE_CONFIG,
    AUTH_METHOD_AUTHORIZATION_CODE,
    CONF_ACCESS_TOKEN,
    CONF_ANONYMOUS,
    CONF_APPIE_CONFIG_JSON,
    CONF_AUTH_METHOD,
    CONF_AUTHORIZATION_CODE,
    CONF_CLIENT_ID,
    CONF_EXPIRES_AT,
    CONF_MEMBER_ID,
    CONF_REFRESH_TOKEN,
    DEFAULT_CLIENT_ID,
    DOMAIN,
    FLOW_MODE_ADVANCED_AUTHORIZATION_CODE,
    FLOW_MODE_ANONYMOUS,
    FLOW_MODE_AUTHENTICATED_APPIE_CONFIG,
    NAME,
    OPT_DEBUG_LOGGING,
    OPT_ENABLE_BONUS_SENSOR,
    OPT_ENABLE_RECEIPTS_SENSOR,
    OPT_ENABLE_REMOTE_SHOPPING_LIST,
    OPT_EXPERIMENTAL_CHECKOUT_ENABLED,
    OPT_EXPERIMENTAL_ORDER_ENABLED,
    OPT_MAX_SEARCH_RESULTS,
    OPT_SCAN_INTERVAL,
)
from .exceptions import AhConfigError

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required("mode"): vol.In(
            [
                FLOW_MODE_ANONYMOUS,
                FLOW_MODE_AUTHENTICATED_APPIE_CONFIG,
                FLOW_MODE_ADVANCED_AUTHORIZATION_CODE,
            ]
        )
    }
)

STEP_APPIE_CONFIG_SCHEMA = vol.Schema(
    {vol.Required(CONF_APPIE_CONFIG_JSON): str}
)

STEP_AUTH_CODE_SCHEMA = vol.Schema(
    {vol.Required(CONF_AUTHORIZATION_CODE): str}
)

OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Optional(OPT_SCAN_INTERVAL, default=300): vol.All(
            vol.Coerce(int), vol.Range(min=60, max=3600)
        ),
        vol.Optional(OPT_MAX_SEARCH_RESULTS, default=10): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=50)
        ),
        vol.Optional(OPT_ENABLE_RECEIPTS_SENSOR, default=True): bool,
        vol.Optional(OPT_ENABLE_REMOTE_SHOPPING_LIST, default=True): bool,
        vol.Optional(OPT_ENABLE_BONUS_SENSOR, default=False): bool,
        vol.Optional(OPT_EXPERIMENTAL_ORDER_ENABLED, default=False): bool,
        vol.Optional(OPT_EXPERIMENTAL_CHECKOUT_ENABLED, default=False): bool,
        vol.Optional(OPT_DEBUG_LOGGING, default=False): bool,
    }
)


class AhConnectConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle AH Connect config flow."""

    VERSION = 1

    def __init__(self) -> None:
        self._mode: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=STEP_USER_SCHEMA,
            )

        self._mode = user_input["mode"]
        if self._mode == FLOW_MODE_ANONYMOUS:
            return await self._async_create_anonymous_entry()
        if self._mode == FLOW_MODE_AUTHENTICATED_APPIE_CONFIG:
            return await self.async_step_appie_config()
        return await self.async_step_authorization_code()

    async def _async_create_anonymous_entry(self) -> FlowResult:
        await self.async_set_unique_id("anonymous")
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=f"{NAME} (anoniem)",
            data={
                CONF_ANONYMOUS: True,
                CONF_AUTH_METHOD: AUTH_METHOD_ANONYMOUS,
                CONF_CLIENT_ID: DEFAULT_CLIENT_ID,
                CONF_ACCESS_TOKEN: "",
                CONF_REFRESH_TOKEN: "",
                CONF_EXPIRES_AT: "",
            },
            options=_default_options(),
        )

    async def async_step_appie_config(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is None:
            return self.async_show_form(
                step_id="appie_config",
                data_schema=STEP_APPIE_CONFIG_SCHEMA,
            )

        raw = user_input[CONF_APPIE_CONFIG_JSON].strip()
        try:
            parsed = parse_appie_config(raw)
        except AhConfigError as err:
            return self.async_show_form(
                step_id="appie_config",
                data_schema=STEP_APPIE_CONFIG_SCHEMA,
                errors={CONF_APPIE_CONFIG_JSON: str(err)},
            )

        await self.async_set_unique_id(parsed["access_token"][:16])
        self._abort_if_unique_id_configured()

        data = {
            CONF_ANONYMOUS: False,
            CONF_AUTH_METHOD: AUTH_METHOD_APPIE_CONFIG,
            CONF_CLIENT_ID: parsed["client_id"],
            CONF_ACCESS_TOKEN: parsed["access_token"],
            CONF_REFRESH_TOKEN: parsed["refresh_token"],
            CONF_EXPIRES_AT: parsed["expires_at"],
        }
        if parsed.get("member_id"):
            data[CONF_MEMBER_ID] = parsed["member_id"]

        return self.async_create_entry(
            title=NAME,
            data=data,
            options=_default_options(),
        )

    async def async_step_authorization_code(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is None:
            return self.async_show_form(
                step_id="authorization_code",
                data_schema=STEP_AUTH_CODE_SCHEMA,
            )

        from .auth import AhAuthManager

        code = user_input[CONF_AUTHORIZATION_CODE].strip()
        try:
            tokens = await AhAuthManager.exchange_authorization_code(
                self.hass, DEFAULT_CLIENT_ID, code
            )
        except Exception:
            _LOGGER.exception("Authorization code exchange failed")
            return self.async_show_form(
                step_id="authorization_code",
                data_schema=STEP_AUTH_CODE_SCHEMA,
                errors={"base": "invalid_auth"},
            )

        access = tokens.get(CONF_ACCESS_TOKEN) or ""
        await self.async_set_unique_id(access[:16])
        self._abort_if_unique_id_configured()

        entry_data = {
            CONF_ANONYMOUS: False,
            CONF_AUTH_METHOD: AUTH_METHOD_AUTHORIZATION_CODE,
            CONF_CLIENT_ID: tokens.get(CONF_CLIENT_ID, DEFAULT_CLIENT_ID),
            CONF_ACCESS_TOKEN: access,
            CONF_REFRESH_TOKEN: tokens.get(CONF_REFRESH_TOKEN, ""),
            CONF_EXPIRES_AT: tokens.get(CONF_EXPIRES_AT, ""),
        }
        if tokens.get(CONF_MEMBER_ID):
            entry_data[CONF_MEMBER_ID] = tokens[CONF_MEMBER_ID]

        return self.async_create_entry(
            title=NAME,
            data=entry_data,
            options=_default_options(),
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> AhConnectOptionsFlow:
        return AhConnectOptionsFlow(config_entry)


class AhConnectOptionsFlow(config_entries.OptionsFlow):
    """Options flow for AH Connect."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                OPTIONS_SCHEMA, self.config_entry.options
            ),
        )


def _default_options() -> dict[str, Any]:
    return {
        OPT_SCAN_INTERVAL: 300,
        OPT_MAX_SEARCH_RESULTS: 10,
        OPT_ENABLE_RECEIPTS_SENSOR: True,
        OPT_ENABLE_REMOTE_SHOPPING_LIST: True,
        OPT_ENABLE_BONUS_SENSOR: False,
        OPT_EXPERIMENTAL_ORDER_ENABLED: False,
        OPT_EXPERIMENTAL_CHECKOUT_ENABLED: False,
        OPT_DEBUG_LOGGING: False,
    }
