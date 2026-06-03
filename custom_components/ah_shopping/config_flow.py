"""Config flow for the AH Shopping integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .auth import AhAuthManager
from .const import (
    CONF_ANONYMOUS,
    CONF_ENABLE_RECEIPTS,
    CONF_EXPERIMENTAL_CART,
    CONF_MAX_SEARCH_RESULTS,
    CONF_SCAN_INTERVAL,
    DEFAULT_ENABLE_RECEIPTS,
    DEFAULT_EXPERIMENTAL_CART,
    DEFAULT_MAX_SEARCH_RESULTS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    OAUTH_AUTHORIZE_URL,
)
from .exceptions import AhAuthError, AhError

class AhConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for AH Shopping."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize config flow."""
        self._auth_mode: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step – choose auth mode."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._auth_mode = user_input["auth_mode"]
            if self._auth_mode == "anonymous":
                return await self._create_anonymous_entry()
            return await self.async_step_oauth()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("auth_mode"): vol.In(
                        {
                            "anonymous": "Anonymous (product search only)",
                            "authenticated": "Authenticated (receipts + search)",
                        }
                    )
                }
            ),
        )

    async def _create_anonymous_entry(self) -> FlowResult:
        """Create an anonymous config entry."""
        await self.async_set_unique_id("ah_shopping_anonymous")
        self._abort_if_unique_id_configured()

        # Verify anonymous token works
        try:
            entry_data = {CONF_ANONYMOUS: True}
            # Temporary entry-like object for auth test
            temp_entry = type(
                "TempEntry",
                (),
                {"data": entry_data, "entry_id": "temp"},
            )()
            auth = AhAuthManager(self.hass, temp_entry)  # type: ignore[arg-type]
            await auth.get_access_token()
        except AhError as err:
            return self.async_abort(reason="cannot_connect")

        return self.async_create_entry(
            title="AH Shopping (Anonymous)",
            data={CONF_ANONYMOUS: True},
        )

    async def async_step_oauth(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle OAuth code input."""
        errors: dict[str, str] = {}

        if user_input is not None:
            code = user_input.get("auth_code", "").strip()
            if not code:
                errors["base"] = "invalid_auth_code"
            else:
                try:
                    temp_entry = type(
                        "TempEntry",
                        (),
                        {"data": {CONF_ANONYMOUS: False}, "entry_id": "temp"},
                    )()
                    auth = AhAuthManager(self.hass, temp_entry)  # type: ignore[arg-type]
                    token_data = await auth.setup_authenticated(code)

                    await self.async_set_unique_id("ah_shopping_authenticated")
                    self._abort_if_unique_id_configured()

                    return self.async_create_entry(
                        title="AH Shopping",
                        data={
                            CONF_ANONYMOUS: False,
                            **token_data,
                        },
                    )
                except AhAuthError:
                    errors["base"] = "invalid_auth_code"
                except AhError:
                    errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="oauth",
            data_schema=vol.Schema(
                {vol.Required("auth_code"): str}
            ),
            description_placeholders={
                "oauth_url": OAUTH_AUTHORIZE_URL,
            },
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> AhOptionsFlow:
        """Return the options flow handler."""
        return AhOptionsFlow(config_entry)


class AhOptionsFlow(config_entries.OptionsFlow):
    """Handle options for AH Shopping."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage integration options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=options.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=300, max=86400)),
                    vol.Optional(
                        CONF_MAX_SEARCH_RESULTS,
                        default=options.get(
                            CONF_MAX_SEARCH_RESULTS, DEFAULT_MAX_SEARCH_RESULTS
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=50)),
                    vol.Optional(
                        CONF_ENABLE_RECEIPTS,
                        default=options.get(
                            CONF_ENABLE_RECEIPTS, DEFAULT_ENABLE_RECEIPTS
                        ),
                    ): bool,
                    vol.Optional(
                        CONF_EXPERIMENTAL_CART,
                        default=options.get(
                            CONF_EXPERIMENTAL_CART, DEFAULT_EXPERIMENTAL_CART
                        ),
                    ): bool,
                }
            ),
        )
