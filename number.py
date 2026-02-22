"""Support for Mennekes Amtron number entities."""
from __future__ import annotations

import logging

from pymodbus.exceptions import ModbusException

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfElectricCurrent, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MAX_CURRENT, MIN_CURRENT, REG_HEMS_CURRENT_LIMIT, REG_HEMS_POWER_LIMIT

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Mennekes Amtron number entities."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    client = hass.data[DOMAIN][config_entry.entry_id]["client"]
    slave_id = hass.data[DOMAIN][config_entry.entry_id]["slave_id"]
    
    numbers = [
        MennekesCurrentLimit(coordinator, config_entry, client, slave_id),
        MennekesPowerLimit(coordinator, config_entry, client, slave_id),
    ]

    async_add_entities(numbers)


class MennekesCurrentLimit(CoordinatorEntity, NumberEntity):
    """Representation of a Mennekes Amtron HEMS current limit control."""

    def __init__(self, coordinator, config_entry, client, slave_id):
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._client = client
        self._slave_id = slave_id
        self._attr_name = "Mennekes Current Limit"
        self._attr_unique_id = f"{config_entry.entry_id}_current_limit"
        self._attr_icon = "mdi:current-ac"
        self._attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
        self._attr_native_min_value = 0  # 0 = pause charging
        self._attr_native_max_value = MAX_CURRENT
        self._attr_native_step = 1
        self._attr_mode = "slider"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": "Mennekes Amtron",
            "manufacturer": "Mennekes",
            "model": "Amtron 4Business 710",
        }

    @property
    def native_value(self):
        """Return the current HEMS current limit."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("hems_current_limit", 0)

    async def async_set_native_value(self, value: float) -> None:
        """Set new HEMS current limit."""
        try:
            # Convert to integer
            int_value = int(value)
            
            # Values below 6A are set to 0A (pause) according to documentation
            if 0 < int_value < MIN_CURRENT:
                int_value = 0
            
            result = await self.hass.async_add_executor_job(
                lambda: self._client.write_register(address=REG_HEMS_CURRENT_LIMIT, value=int_value)
            )
            
            if result.isError():
                _LOGGER.error("Failed to set current limit: %s", result)
                return
            
            await self.coordinator.async_request_refresh()
            
        except ModbusException as err:
            _LOGGER.error("Error setting current limit: %s", err)


class MennekesPowerLimit(CoordinatorEntity, NumberEntity):
    """HEMS Power Limit control (register 2002).

    Used for dynamic phase switching:
    - 0 W        = pause charging
    - 1380–7360W = 1-phase charging (charger picks appropriate current)
    - ≥4140 W    = charger may switch to 3 phases (requires Dynamic mode on device)
    """

    def __init__(self, coordinator, config_entry, client, slave_id):
        """Initialize the power limit entity."""
        super().__init__(coordinator)
        self._client = client
        self._slave_id = slave_id
        self._attr_name = "Mennekes Power Limit"
        self._attr_unique_id = f"{config_entry.entry_id}_power_limit"
        self._attr_icon = "mdi:lightning-bolt-circle"
        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_native_min_value = 0       # 0 = pause
        self._attr_native_max_value = 22080   # 32A × 3ph × 230V
        self._attr_native_step = 230          # ~1A per phase at 230V
        self._attr_mode = "slider"

        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": "Mennekes Amtron",
            "manufacturer": "Mennekes",
            "model": "Amtron 4Business 710",
        }

    @property
    def native_value(self):
        """Return the current HEMS power limit."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("hems_power_limit", 0)

    async def async_set_native_value(self, value: float) -> None:
        """Set new HEMS power limit."""
        try:
            int_value = int(value)
            # Per docs: values below minimum (register 2012) are set to 0W
            # We enforce: 1 to 1379 W → set to 0 (pause)
            if 0 < int_value < 1380:
                int_value = 0

            result = await self.hass.async_add_executor_job(
                lambda: self._client.write_register(address=REG_HEMS_POWER_LIMIT, value=int_value)
            )

            if result.isError():
                _LOGGER.error("Failed to set power limit: %s", result)
                return

            await self.coordinator.async_request_refresh()

        except ModbusException as err:
            _LOGGER.error("Error setting power limit: %s", err)
