"""The Mennekes Amtron integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    CONF_SLAVE_ID,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.SWITCH, Platform.NUMBER]


def _to_int32(high: int, low: int) -> int:
    """Combine two 16-bit registers into a signed 32-bit integer."""
    value = (high << 16) | low
    return value if value < 2147483648 else value - 4294967296


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Mennekes Amtron from a config entry."""

    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    client = ModbusTcpClient(host=host, port=port, timeout=10)

    async def _read(address: int, count: int = 1):
        """Read holding registers; returns list of values or None on error."""
        result = await hass.async_add_executor_job(
            lambda: client.read_holding_registers(address=address, count=count)
        )
        if result.isError():
            _LOGGER.warning("Read error at address %d (count=%d): %s", address, count, result)
            return None
        return result.registers

    async def async_update_data():
        """Fetch data from the charger."""
        try:
            if not client.connected:
                _LOGGER.debug("Connecting to %s:%s", host, port)
                connected = await hass.async_add_executor_job(client.connect)
                if not connected:
                    raise UpdateFailed("Could not connect to charger")
                _LOGGER.info("Connected to %s:%s", host, port)

            data = {}

            # --- Status registers (individual reads — gaps in register map) ---
            r = await _read(104)  # OCPP Status
            if r is None:
                raise UpdateFailed("Cannot read OCPP status (register 104)")
            data["ocpp_status"] = r[0]

            r = await _read(122)  # Vehicle State
            if r is not None:
                data["vehicle_state"] = r[0]

            r = await _read(124)  # Charge Point Availability
            if r is not None:
                data["charge_point_availability"] = r[0]

            r = await _read(140)  # Relay State
            if r is not None:
                data["relay_state"] = r[0]

            # --- Meter block: 206-227 (22 registers, fully contiguous) ---
            # 206-211: Power L1/L2/L3 [W]       3x int32
            # 212-217: Current L1/L2/L3 [mA]    3x int32
            # 218-219: Total Energy [Wh]         1x int32
            # 220-221: Total Power [W]           1x int32
            # 222-227: Voltage L1/L2/L3 [V]     3x int32
            r = await _read(206, count=22)
            if r is not None:
                data["power_l1"] = _to_int32(r[0], r[1])
                data["power_l2"] = _to_int32(r[2], r[3])
                data["power_l3"] = _to_int32(r[4], r[5])
                data["power"] = data["power_l1"] + data["power_l2"] + data["power_l3"]
                data["current_l1"] = _to_int32(r[6], r[7]) / 1000.0    # mA → A
                data["current_l2"] = _to_int32(r[8], r[9]) / 1000.0
                data["current_l3"] = _to_int32(r[10], r[11]) / 1000.0
                data["total_energy"] = _to_int32(r[12], r[13]) / 1000.0  # Wh → kWh
                data["total_power"] = _to_int32(r[14], r[15])            # W
                data["voltage_l1"] = _to_int32(r[16], r[17])             # V (not mV!)
                data["voltage_l2"] = _to_int32(r[18], r[19])
                data["voltage_l3"] = _to_int32(r[20], r[21])

            # --- Signaled current to EV (706) ---
            r = await _read(706)
            if r is not None:
                data["signaled_current"] = r[0]

            # --- Session energy (716-717) and charging duration (718-719) ---
            r = await _read(716, count=4)
            if r is not None:
                data["session_energy"] = _to_int32(r[0], r[1]) / 1000.0  # Wh → kWh
                data["charging_duration"] = _to_int32(r[2], r[3])        # seconds

            # --- HEMS: current limit (2000), power limit (2002) ---
            r = await _read(2000, count=3)  # 2000, 2001, 2002
            if r is not None:
                data["hems_current_limit"] = r[0]   # 2000 in A
                data["hems_power_limit"] = r[2]     # 2002 in W

            # --- HEMS comm status (2011) ---
            r = await _read(2011)
            if r is not None:
                data["hems_comm_status"] = r[0]

            # --- Phase mode (2020) and assigned phases (2023) ---
            # Register 2020 is read-only (FC03 only) per device documentation.
            # Phase switch mode can only be configured via the charger web interface.
            r = await _read(2020, count=4)  # 2020..2023
            if r is not None:
                data["phase_switch_mode"] = r[0]  # 2020
                data["assigned_phases"] = r[3]    # 2023

            # --- Authorization status (2030) ---
            r = await _read(2030)
            if r is not None:
                data["authorization_status"] = r[0]

            # Defaults for registers that failed to read
            data.setdefault("vehicle_state", 0)
            data.setdefault("charge_point_availability", 0)
            data.setdefault("relay_state", 0)
            data.setdefault("power", 0)
            data.setdefault("power_l1", 0)
            data.setdefault("power_l2", 0)
            data.setdefault("power_l3", 0)
            data.setdefault("current_l1", 0)
            data.setdefault("current_l2", 0)
            data.setdefault("current_l3", 0)
            data.setdefault("voltage_l1", 0)
            data.setdefault("voltage_l2", 0)
            data.setdefault("voltage_l3", 0)
            data.setdefault("total_energy", 0)
            data.setdefault("total_power", 0)
            data.setdefault("session_energy", 0)
            data.setdefault("signaled_current", 0)
            data.setdefault("charging_duration", 0)
            data.setdefault("hems_current_limit", 0)
            data.setdefault("hems_power_limit", 0)
            data.setdefault("hems_comm_status", 0)
            data.setdefault("phase_switch_mode", 0)
            data.setdefault("assigned_phases", 0)
            data.setdefault("authorization_status", 0)

            return data

        except ModbusException as err:
            raise UpdateFailed(f"Modbus error: {err}") from err
        except UpdateFailed:
            raise
        except Exception as err:
            _LOGGER.error("Unexpected error: %s", err, exc_info=True)
            raise UpdateFailed(f"Error: {err}") from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{DOMAIN}_{host}",
        update_method=async_update_data,
        update_interval=timedelta(seconds=scan_interval),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "client": client,
        "slave_id": entry.data[CONF_SLAVE_ID],
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        data = hass.data[DOMAIN].pop(entry.entry_id)
        await hass.async_add_executor_job(data["client"].close)

    return unload_ok
