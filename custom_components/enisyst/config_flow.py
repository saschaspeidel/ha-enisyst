"""Config flow for enisyst Wallbox integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import EnisystApiClient, EnisystAuthError, EnisystApiError
from .const import CONF_STATION_ID, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.EMAIL)
        ),
        vol.Required(CONF_PASSWORD): selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
        ),
        vol.Required(CONF_STATION_ID): selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
        ),
    }
)


class EnisystConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the initial setup config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            username = user_input[CONF_USERNAME].strip()
            password = user_input[CONF_PASSWORD]
            station_id = user_input[CONF_STATION_ID].strip().upper()

            # Check for duplicate entries
            await self.async_set_unique_id(f"{username}_{station_id}")
            self._abort_if_unique_id_configured()

            # Validate credentials by attempting login + one API call
            session = async_create_clientsession(self.hass)
            client = EnisystApiClient(username, password, station_id, session)
            try:
                await client.async_login()
                chargepoints = await client.async_get_chargepoints()
                if not chargepoints:
                    errors["base"] = "no_chargepoints"
            except EnisystAuthError:
                errors["base"] = "invalid_auth"
            except EnisystApiError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error during config flow")
                errors["base"] = "unknown"

            if not errors:
                return self.async_create_entry(
                    title=f"enisyst {station_id}",
                    data={
                        CONF_USERNAME: username,
                        CONF_PASSWORD: password,
                        CONF_STATION_ID: station_id,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
