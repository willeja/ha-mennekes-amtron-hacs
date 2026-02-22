# Mennekes Amtron – Home Assistant Integratie

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

Home Assistant integratie voor **Mennekes Amtron 4Business** laadpalen via Modbus TCP.
Getest op: Amtron 4Business 710 22 C2 · Firmware 1.5.21 · Protocol 1.5

---

## Functies

### Sensors
| Sensor | Eenheid | Omschrijving |
|---|---|---|
| Charging Status | tekst | OCPP status (Available, Charging, …) |
| Vehicle State | tekst | IEC 61851 CP-status (A/B/C/D/E) |
| Relay State | tekst | Laadrelais aan/uit |
| Assigned Phases | tekst | Actieve fasen (None / 1 fase / 3 fasen) |
| Phase Switch Mode | tekst | Geconfigureerde fase-modus (alleen lezen) |
| HEMS Status | tekst | Communicatiestatus (OK / Timeout) |
| Power L1 / L2 / L3 | W | Vermogen per fase |
| Total Power | W | Totaalvermogen van de meter |
| Current L1 / L2 / L3 | A | Stroom per fase |
| Signaled Current | A | Laadstroom gesignaleerd naar EV |
| Voltage L1 / L2 / L3 | V | Spanning per fase |
| Total Energy | kWh | Totale energie (oplopend) |
| Session Energy | kWh | Energie huidige laadsessie |
| Charging Duration | s | Duur huidige laadsessie |

### Controls
| Entity | Omschrijving |
|---|---|
| Switch – Charge Control | Laden pauzeren / hervatten (0A of 16A) |
| Number – Current Limit | Stroomlimiet: 0 (pauze) of 6–32 A |
| Number – Power Limit | Vermogenslimiet: 0 (pauze) of 1380–22080 W |

> **Power Limit** is de aanbevolen control voor dynamisch fase-schakelen.

---

## Vereisten

### Laadpaal instellen (eenmalig)

1. Open het webinterface: `http://[IP-LAADPAAL]`
2. Ga naar **Instellingen → Netwerk → Extern energiemanagement**
3. Zet **"Interface naar energiebeheersysteem"** op **"Modbus TCP – Lezen en schrijven"**
4. Sla op en herstart de laadpaal

> Voor fase-schakelen: zet ook **Phase Switch Mode** op **"Dynamisch"**.

---

## Installatie

### Via HACS (aanbevolen)

1. Ga in HA naar **HACS → Integraties → ⋮ → Aangepaste repositories**
2. Voeg de GitHub URL van dit project toe (categorie: **Integratie**)
3. Zoek naar **Mennekes Amtron** en klik **Downloaden**
4. Herstart Home Assistant

### Handmatig

1. Kopieer de map `mennekes_modbus` naar `/config/custom_components/`
2. Herstart Home Assistant

---

## Home Assistant configureren

1. Ga naar **Instellingen → Apparaten & Services → + Integratie toevoegen**
2. Zoek naar **Mennekes Amtron**
3. Vul in:
   - **IP-adres**: IP van je laadpaal (bijv. `10.0.3.128`)
   - **Poort**: `502`
   - **Slave ID**: `1`
   - **Scan interval**: `10` seconden
4. Klik **Verzenden**

---

## Dynamisch fase-schakelen op basis van beschikbaar vermogen

Wanneer de laadpaal in **Dynamisch** fase-modus staat, bepaalt de **Power Limit** het laadgedrag:

| Power Limit | Gedrag |
|---|---|
| 0 W | Pauze laden |
| 1380 – 7360 W | Laden op **1 fase** |
| ≥ 4140 W | Laadpaal mag naar **3 fasen** schakelen |

> Waarden van 1–1379 W worden automatisch naar 0 W (pauze) gezet.

### Automatie: laden op zonne-overschot (met hysteresis)

```yaml
alias: Laden op zonne-overschot met fase-schakelen
trigger:
  - platform: time_pattern
    minutes: "/1"
action:
  - variables:
      overschot: "{{ states('sensor.solar_overschot') | float(0) }}"
      huidig: "{{ states('number.mennekes_power_limit') | float(0) }}"
      nieuw: >
        {% if overschot < 1380 %}
          0
        {% elif huidig < 4140 and overschot > 4500 %}
          {{ [overschot | int, 22080] | min }}
        {% elif huidig >= 4140 and overschot < 3800 %}
          {{ [overschot | int, 3680] | min }}
        {% else %}
          {{ [overschot | int, 22080] | min }}
        {% endif %}
  - service: number.set_value
    target:
      entity_id: number.mennekes_power_limit
    data:
      value: "{{ nieuw }}"
```

---

## Probleemoplossing

### Verbindingsfout / geen data

- Controleer of **HEMS Modbus TCP (lezen en schrijven)** ingeschakeld is
- Controleer of poort 502 bereikbaar is
- Bekijk de logs: **Instellingen → Systeem → Logboek** → filter op `mennekes_modbus`

### HEMS Status toont "Timeout" (fout 1073 op laadpaal)

Communicatie was te lang onderbroken – laadpaal activeerde Safe Current. Verdwijnt vanzelf na de volgende schrijfactie.

### Debug logging

```yaml
logger:
  default: warning
  logs:
    custom_components.mennekes_modbus: debug
```

---

## Technische details

**Protocol**: Modbus TCP · Holding Registers (FC03 lezen, FC06 schrijven)
**Register documentatie**: `http://[IP-LAADPAAL]/datapointlist.html`

| Adres | Omschrijving |
|---|---|
| 104 | OCPP Status |
| 122 | Vehicle State |
| 140 | Relay State |
| 206–227 | Meter: vermogen, stroom, energie, spanning |
| 706 | Gesignaleerde stroom [A] |
| 716–719 | Sessie-energie [Wh] + laadduur [s] |
| 2000 | HEMS stroomlimiet [A] R/W |
| 2002 | HEMS vermogenslimiet [W] R/W |
| 2011 | HEMS communicatiestatus |
| 2020 | Fase-schakel modus (alleen lezen) |
| 2023 | Toegewezen fasen |

---

## Licentie

MIT License

## Credits

- Mennekes Amtron 4Business Modbus TCP specificatie versie 1.5
- [pymodbus](https://github.com/pymodbus-dev/pymodbus)
- [Home Assistant](https://www.home-assistant.io/) community
