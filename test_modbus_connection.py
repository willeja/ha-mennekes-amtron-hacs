#!/usr/bin/env python3
"""
Test script voor Mennekes Amtron Modbus TCP verbinding
Gebruik dit script om te testen of de verbinding met je laadpaal werkt
"""

import sys

try:
    from pymodbus.client import ModbusTcpClient
except ImportError:
    print("ERROR: pymodbus is niet geïnstalleerd")
    print("Installeer met: pip install pymodbus")
    sys.exit(1)

# Configuratie - PAS DIT AAN NAAR JOUW INSTELLINGEN
HOST = "10.0.3.128"  # IP-adres van je laadpaal
PORT = 502           # Modbus TCP poort (standaard 502)
SLAVE_ID = 1         # Probeer ook 255 als 1 niet werkt
TIMEOUT = 10         # Timeout in seconden

print(f"╔══════════════════════════════════════════════════════════╗")
print(f"║  Mennekes Amtron Modbus TCP Test                        ║")
print(f"╚══════════════════════════════════════════════════════════╝")
print()
print(f"Configuratie:")
print(f"  Host:     {HOST}")
print(f"  Port:     {PORT}")
print(f"  Slave ID: {SLAVE_ID}")
print(f"  Timeout:  {TIMEOUT}s")
print()

# Test 1: Verbinding maken
print("[1/4] Verbinding maken...")
client = ModbusTcpClient(host=HOST, port=PORT, timeout=TIMEOUT)

try:
    if not client.connect():
        print("  ❌ FOUT: Kan geen verbinding maken met de laadpaal")
        print()
        print("Mogelijke oorzaken:")
        print("  - Verkeerd IP-adres")
        print("  - Laadpaal is offline")
        print("  - Firewall blokkeert poort 502")
        print("  - Modbus TCP is niet geactiveerd op de laadpaal")
        sys.exit(1)
    
    print("  ✓ Verbinding succesvol!")
    
    # Test 2: Register lezen (status)
    print("[2/4] Register 1000 lezen (charging state)...")
    result = client.read_holding_registers(address=1000, count=1, unit=SLAVE_ID)
    
    if result.isError():
        print(f"  ❌ FOUT bij lezen register: {result}")
        print()
        print("Mogelijke oorzaken:")
        print(f"  - Verkeerde Slave ID (probeer {255 if SLAVE_ID == 1 else 1} in plaats van {SLAVE_ID})")
        print("  - Register 1000 bestaat niet op dit model")
        print("  - Modbus TCP is niet correct geconfigureerd")
        client.close()
        sys.exit(1)
    
    print(f"  ✓ Register gelezen! Waarde: {result.registers[0]}")
    
    # Test 3: Meerdere registers lezen
    print("[3/4] Meerdere registers lezen (1000-1029)...")
    result = client.read_holding_registers(address=1000, count=30, unit=SLAVE_ID)
    
    if result.isError():
        print(f"  ❌ FOUT: {result}")
        client.close()
        sys.exit(1)
    
    print(f"  ✓ {len(result.registers)} registers gelezen!")
    
    # Test 4: Data weergeven
    print("[4/4] Data interpreteren...")
    registers = result.registers
    
    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  Laadpaal Data                                           ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"  Charging State:    {registers[0]}")
    print(f"  Charge Control:    {registers[4]}")
    print(f"  Current Limit:     {registers[6] / 10.0:.1f} A")
    print(f"  Power:             {registers[8]} W")
    print(f"  Total Energy:      {registers[10] / 100.0:.2f} kWh")
    print(f"  Session Energy:    {registers[12] / 100.0:.2f} kWh")
    print(f"  Current L1:        {registers[14] / 100.0:.2f} A")
    print(f"  Current L2:        {registers[16] / 100.0:.2f} A")
    print(f"  Current L3:        {registers[18] / 100.0:.2f} A")
    print(f"  Voltage L1:        {registers[20] / 10.0:.1f} V")
    print(f"  Voltage L2:        {registers[22] / 10.0:.1f} V")
    print(f"  Voltage L3:        {registers[24] / 10.0:.1f} V")
    print(f"  Cable State:       {registers[26]}")
    print(f"  Error Code:        {registers[28]}")
    print()
    
    print("✓ ALLE TESTS SUCCESVOL!")
    print()
    print("De laadpaal werkt correct via Modbus TCP.")
    print("Je kunt nu de Home Assistant integratie gebruiken.")
    
except Exception as e:
    print(f"  ❌ ONVERWACHTE FOUT: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    client.close()
    print()
    print("Verbinding gesloten.")
