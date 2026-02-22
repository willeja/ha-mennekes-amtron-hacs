"""Support for Mennekes Amtron switches."""
from __future__ import annotations

import logging

from pymodbus.exceptions import ModbusException

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, REG_HEMS_CURRENT_LIMIT, MIN_CURRENT

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Mennekes Amtron switches."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    client = hass.data[DOMAIN][config_entry.entry_id]["client"]
    slave_id = hass.data[DOMAIN][config_entry.entry_id]["slave_id"]
    
    switches = [
        MennekesChargeSwitch(coordinator, config_entry, client, slave_id),
    ]
    
    async_add_entities(switches)


class MennekesChargeSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a Mennekes Amtron charge control switch."""

    def __init__(self, coordinator, config_entry, client, slave_id):
        """Initialize the switch."""
        super().__init__(coordinator)
        self._client = client
        self._slave_id = slave_id
        self._attr_name = "Mennekes Charge Control"
        self._attr_unique_id = f"{config_entry.entry_id}_charge_control"
        self._attr_icon = "mdi:power-plug"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": "Mennekes Amtron",
            "manufacturer": "Mennekes",
            "model": "Amtron 4Business 710",
        }

    @property
    def is_on(self):
        """Return true if charging is enabled."""
        if self.coordinator.data is None:
            return None
        # Charging is enabled if HEMS current limit is >= 6A
        current_limit = self.coordinator.data.get("hems_current_limit", 0)
        return current_limit >= MIN_CURRENT

    async def async_turn_on(self, **kwargs):
        """Enable charging by setting HEMS current limit to 16A (default)."""
        try:
            # Set to 16A as a reasonable default
            result = await self.hass.async_add_executor_job(
                lambda: self._client.write_register(address=REG_HEMS_CURRENT_LIMIT, value=16)
            )
            
            if result.isError():
                _LOGGER.error("Failed to enable charging: %s", result)
                return
            
            await self.coordinator.async_request_refresh()
            
        except ModbusException as err:
            _LOGGER.error("Error enabling charging: %s", err)

    async def async_turn_off(self, **kwargs):
        """Disable charging by setting HEMS current limit to 0A."""
        try:
            result = await self.hass.async_add_executor_job(
                lambda: self._client.write_register(address=REG_HEMS_CURRENT_LIMIT, value=0)
            )
            
            if result.isError():
                _LOGGER.error("Failed to disable charging: %s", result)
                return
            
            await self.coordinator.async_request_refresh()
            
        except ModbusException as err:
            _LOGGER.error("Error disabling charging: %s", err)
