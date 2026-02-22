"""Config flow for Mennekes Amtron integration."""
from __future__ import annotations

import logging
from typing import Any

from pymodbus.client import ModbusTcpClient
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_SLAVE_ID,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SLAVE_ID,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


def validate_connection(
    host: str, port: int, slave_id: int
) -> dict[str, str] | None:
    """Test if we can communicate with the charger."""
    try:
        client = ModbusTcpClient(host=host, port=port, timeout=5)
        if not client.connect():
            return {"base": "cannot_connect"}
        
        # Simple validation - just check if we can connect
        # Don't validate registers during config as pymodbus syntax is inconsistent
        client.close()
        return None
        
    except Exception:  # pylint: disable=broad-except
        _LOGGER.exception("Unexpected exception during connection test")
        return {"base": "unknown"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Mennekes Amtron."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate the input
            errors = await self.hass.async_add_executor_job(
                validate_connection,
                user_input[CONF_HOST],
                user_input[CONF_PORT],
                user_input[CONF_SLAVE_ID],
            )

            if not errors:
                # Create a unique ID based on host
                await self.async_set_unique_id(user_input[CONF_HOST])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"{DEFAULT_NAME} ({user_input[CONF_HOST]})",
                    data=user_input,
                )

        # Show the form
        data_schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
                vol.Optional(CONF_SLAVE_ID, default=DEFAULT_SLAVE_ID): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=247)
                ),
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): vol.All(vol.Coerce(int), vol.Range(min=5, max=60)),
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )
