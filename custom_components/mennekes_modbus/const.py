"""Constants for the Mennekes Amtron integration."""
from typing import Final

DOMAIN: Final = "mennekes_modbus"
DEFAULT_NAME = "Mennekes Amtron"
DEFAULT_PORT = 502
DEFAULT_SLAVE_ID = 1
DEFAULT_SCAN_INTERVAL = 10

# Configuration keys
CONF_SLAVE_ID = "slave_id"

# Modbus register addresses from AMTRON 4Business documentation
# All registers are Holding Registers (FC03)

# Device Information
REG_FIRMWARE_VERSION = 100        # 2 registers - ASCII version
REG_OCPP_STATUS = 104             # OCPP status enum
REG_PROTOCOL_VERSION = 120        # 2 registers - ASCII version
REG_VEHICLE_STATE = 122           # A/B/C/D/E state
REG_CHARGE_POINT_AVAILABILITY = 124  # 0=Unavailable, 1=Available
REG_RELAY_STATE = 140             # On=1, Off=0
REG_DEVICE_ID = 141               # "AM"
REG_CHARGE_POINT_MODEL = 142      # 10 registers - ASCII model name
REG_PLUG_LOCK_STATUS = 152        # Lock status
REG_DEVICE_NAME = 2158            # 16 registers - ASCII device name

# Meter readings
REG_METER_ENERGY = 200            # 6 registers - L1/L2/L3 energy in Wh
REG_METER_POWER = 206             # 6 registers - L1/L2/L3 power in W
REG_METER_CURRENT = 212           # 6 registers - L1/L2/L3 current in mA
REG_METER_TOTAL_ENERGY = 218      # 2 registers - Total energy in Wh
REG_METER_VOLTAGE = 222           # 6 registers - L1/L2/L3 voltage in mV

# HEMS / Energy Management Control
REG_SAFE_CURRENT = 131            # Fallback current when HEMS timeout
REG_COMMUNICATION_TIMEOUT = 132   # Timeout in seconds
REG_OPERATOR_CURRENT_LIMIT = 134  # Calculated minimum current

# Charging Information  
REG_SIGNALED_CURRENT_TO_EV = 706  # Current signaled to EV
REG_MIN_CHARGING_CURRENT = 712    # Minimum charging current
REG_MAX_CHARGING_CURRENT = 715    # Maximum charging current
REG_CHARGED_ENERGY = 716          # 2 registers - Energy in current session (Wh)
REG_CHARGING_DURATION = 718       # 2 registers - Duration in seconds

# HEMS Control Registers (Read/Write)
REG_HEMS_CURRENT_LIMIT = 2000     # Main control register - 0A or 6-32A
REG_HEMS_CURRENT_LIMIT_TENTH = 2001  # Same but in 0.1A steps
REG_HEMS_POWER_LIMIT = 2002       # Power limit in W

# HEMS Status
REG_MODBUS_HEMS_CONFIG = 2010     # 0=Not active, 1=Read-only, 2=Read/Write
REG_HEMS_COMM_STATUS = 2011       # 0=OK, 1=Timeout (error 1073!)
REG_HEMS_POWER_LIMIT_MIN = 2012   # Minimum power in W
REG_HEMS_POWER_LIMIT_MAX = 2013   # Maximum power in W

# Phase management
REG_PHASE_SWITCH_MODE = 2020      # 0=1phase, 1=3phase, 2=dynamic, 3=fixed
REG_PHASE_SWITCH_PAUSE = 2021     # Delay after phase switch in seconds
REG_PHASE_SWITCH_STATUS = 2022    # 0=not running, 1=running
REG_ASSIGNED_PHASES = 2023        # 0=None, 1=One, 2=Three

# Authorization
REG_AUTHORIZATION_STATUS = 2030   # 0=Autostart, 1=Authorized, 2=Not authorized

# OCPP Status values
OCPP_STATUS_UNDEFINED = 0
OCPP_STATUS_AVAILABLE = 1
OCPP_STATUS_PREPARING = 2
OCPP_STATUS_CHARGING = 3
OCPP_STATUS_SUSPENDED_EVSE = 4
OCPP_STATUS_SUSPENDED_EV = 5
OCPP_STATUS_FINISHING = 6
OCPP_STATUS_RESERVED = 7
OCPP_STATUS_UNAVAILABLE = 8
OCPP_STATUS_FAULTED = 9

OCPP_STATUS_MAP = {
    OCPP_STATUS_UNDEFINED: "Undefined",
    OCPP_STATUS_AVAILABLE: "Available",
    OCPP_STATUS_PREPARING: "Preparing",
    OCPP_STATUS_CHARGING: "Charging",
    OCPP_STATUS_SUSPENDED_EVSE: "Suspended (Charger)",
    OCPP_STATUS_SUSPENDED_EV: "Suspended (Vehicle)",
    OCPP_STATUS_FINISHING: "Finishing",
    OCPP_STATUS_RESERVED: "Reserved",
    OCPP_STATUS_UNAVAILABLE: "Unavailable",
    OCPP_STATUS_FAULTED: "Faulted",
}

# Vehicle State values (IEC 61851-1 CP states)
VEHICLE_STATE_A = 1  # No EV connected
VEHICLE_STATE_B = 2  # EV connected but not charging
VEHICLE_STATE_C = 3  # EV charging
VEHICLE_STATE_D = 4  # Ventilation required
VEHICLE_STATE_E = 5  # Error

VEHICLE_STATE_MAP = {
    VEHICLE_STATE_A: "Not Connected",
    VEHICLE_STATE_B: "Connected",
    VEHICLE_STATE_C: "Charging",
    VEHICLE_STATE_D: "Ventilation Required",
    VEHICLE_STATE_E: "Error",
}

# Current limits (Ampere)
MIN_CURRENT = 6
MAX_CURRENT = 32
