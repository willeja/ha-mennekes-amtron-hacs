"""Support for Mennekes Amtron sensors."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, OCPP_STATUS_MAP, VEHICLE_STATE_MAP


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Mennekes Amtron sensors."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    
    sensors = [
        # Status sensors
        MennekesSensor(coordinator, config_entry, "ocpp_status", "Charging Status", None, None, "mdi:ev-station"),
        MennekesSensor(coordinator, config_entry, "vehicle_state", "Vehicle State", None, None, "mdi:car-electric"),
        MennekesSensor(coordinator, config_entry, "relay_state", "Relay State", None, None, "mdi:electric-switch"),
        MennekesSensor(coordinator, config_entry, "assigned_phases", "Assigned Phases", None, None, "mdi:sine-wave"),
        MennekesSensor(coordinator, config_entry, "phase_switch_mode", "Phase Switch Mode", None, None, "mdi:arrow-split-vertical"),
        MennekesSensor(coordinator, config_entry, "hems_comm_status", "HEMS Status", None, None, "mdi:lan-check"),

        # Power and energy
        MennekesSensor(coordinator, config_entry, "power", "Power", UnitOfPower.WATT, SensorDeviceClass.POWER, "mdi:flash", SensorStateClass.MEASUREMENT),
        MennekesSensor(coordinator, config_entry, "power_l1", "Power L1", UnitOfPower.WATT, SensorDeviceClass.POWER, "mdi:flash", SensorStateClass.MEASUREMENT),
        MennekesSensor(coordinator, config_entry, "power_l2", "Power L2", UnitOfPower.WATT, SensorDeviceClass.POWER, "mdi:flash", SensorStateClass.MEASUREMENT),
        MennekesSensor(coordinator, config_entry, "power_l3", "Power L3", UnitOfPower.WATT, SensorDeviceClass.POWER, "mdi:flash", SensorStateClass.MEASUREMENT),
        MennekesSensor(coordinator, config_entry, "total_power", "Total Power", UnitOfPower.WATT, SensorDeviceClass.POWER, "mdi:flash", SensorStateClass.MEASUREMENT),
        MennekesSensor(coordinator, config_entry, "total_energy", "Total Energy", UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, "mdi:counter", SensorStateClass.TOTAL_INCREASING),
        MennekesSensor(coordinator, config_entry, "session_energy", "Session Energy", UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, "mdi:lightning-bolt", SensorStateClass.TOTAL_INCREASING),

        # Current
        MennekesSensor(coordinator, config_entry, "current_l1", "Current L1", UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, "mdi:current-ac", SensorStateClass.MEASUREMENT),
        MennekesSensor(coordinator, config_entry, "current_l2", "Current L2", UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, "mdi:current-ac", SensorStateClass.MEASUREMENT),
        MennekesSensor(coordinator, config_entry, "current_l3", "Current L3", UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, "mdi:current-ac", SensorStateClass.MEASUREMENT),
        MennekesSensor(coordinator, config_entry, "signaled_current", "Signaled Current", UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, "mdi:current-ac", SensorStateClass.MEASUREMENT),

        # Voltage
        MennekesSensor(coordinator, config_entry, "voltage_l1", "Voltage L1", UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, "mdi:sine-wave", SensorStateClass.MEASUREMENT),
        MennekesSensor(coordinator, config_entry, "voltage_l2", "Voltage L2", UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, "mdi:sine-wave", SensorStateClass.MEASUREMENT),
        MennekesSensor(coordinator, config_entry, "voltage_l3", "Voltage L3", UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, "mdi:sine-wave", SensorStateClass.MEASUREMENT),

        # Session info
        MennekesSensor(coordinator, config_entry, "charging_duration", "Charging Duration", UnitOfTime.SECONDS, SensorDeviceClass.DURATION, "mdi:timer", SensorStateClass.MEASUREMENT),
    ]
    
    async_add_entities(sensors)


class MennekesSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Mennekes Amtron sensor."""

    def __init__(self, coordinator, config_entry, sensor_type, name, unit, device_class, icon, state_class=None):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._attr_name = f"Mennekes {name}"
        self._attr_unique_id = f"{config_entry.entry_id}_{sensor_type}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_icon = icon
        self._attr_state_class = state_class
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": "Mennekes Amtron",
            "manufacturer": "Mennekes",
            "model": "Amtron 4Business 710",
        }

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
        
        value = self.coordinator.data.get(self._sensor_type)
        
        # Map status values to readable text
        if self._sensor_type == "ocpp_status" and value is not None:
            return OCPP_STATUS_MAP.get(value, f"Unknown ({value})")
        
        if self._sensor_type == "vehicle_state" and value is not None:
            return VEHICLE_STATE_MAP.get(value, f"Unknown ({value})")
        
        if self._sensor_type == "relay_state" and value is not None:
            return "On" if value == 1 else "Off"
        
        if self._sensor_type == "hems_comm_status" and value is not None:
            return "OK" if value == 0 else "Timeout"
        
        if self._sensor_type == "assigned_phases" and value is not None:
            phases_map = {0: "None", 1: "One phase", 2: "Three phases"}
            return phases_map.get(value, f"Unknown ({value})")

        if self._sensor_type == "phase_switch_mode" and value is not None:
            mode_map = {0: "1 fase", 1: "3 fasen", 2: "Dynamisch", 3: "Vast (bij aansluiting)"}
            return mode_map.get(value, f"Unknown ({value})")

        return value
