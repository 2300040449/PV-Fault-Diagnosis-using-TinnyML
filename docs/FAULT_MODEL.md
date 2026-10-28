# Fault Modeling & Injection Specifications

## Overview
The digital twin accurately models four electrical/environmental operating states selected via the hardware push button (`GPIO 13`).

---

### Fault Mode 0: NORMAL
- **Description**: Pristine PV operating state under current ambient conditions.
- **Current**: $I = I_{normal}(G)$
- **Voltage**: $V = V_{normal}(T_{pv})$
- **Temperature**: $T_{pv} = T_a + (G/1000) \times 3.0^\circ\text{C}$
- **LED Indicator**: `LOW` (OFF)
- **Label**: `NORMAL`

---

### Fault Mode 1: PARTIAL SHADING
- **Description**: Non-uniform cloud cover, soiling, or localized building shadows blocking part of the array.
- **Physical Effect**: Available photocurrent drops sharply; bypass diodes conduct, causing a slight voltage drop.
- **Current**: $I = I_{normal} \times 0.45$
- **Voltage**: $V = V_{normal} \times 0.95$
- **Temperature**: $T_{pv} = T_a$
- **Power**: Substantially reduced ($P \approx 42\% \text{ of nominal}$)
- **LED Indicator**: `HIGH` (ON)
- **Label**: `PARTIAL SHADE`

---

### Fault Mode 2: OPEN CIRCUIT
- **Description**: Physical wire disconnect, blown DC fuse, or faulty connector.
- **Physical Effect**: Output circuit impedance becomes infinite; no current can flow.
- **Current**: $I = 0.00\text{ A}$
- **Voltage**: Sits at open-circuit potential $V_{oc} = 21.6 \times [1 + \beta_V(T_a - 25)]$
- **Power**: $P = 0.00\text{ W}$
- **LED Indicator**: `HIGH` (ON)
- **Label**: `OPEN CIRCUIT`

---

### Fault Mode 3: OVER TEMPERATURE
- **Description**: Thermal runaway, poor module ventilation, junction box overheating, or heat-sink blockage.
- **Physical Effect**: Module temperature exceeds safe thresholds ($> 60^\circ\text{C}$); bandgap narrowing causes severe voltage degradation.
- **Temperature**: $T_{pv} = T_a + 35.0^\circ\text{C}$ (reaches $60^\circ\text{C} - 77^\circ\text{C}$)
- **Voltage**: Degrades severely: $V = 18.0 \times [1 + \beta_V(T_{pv} - 25)]$ ($\approx 12 - 14\text{ V}$)
- **Current**: $I = I_{normal} \times 0.95$ (mild reduction from carrier recombination)
- **Power**: Degrades by $25\% - 35\%$
- **LED Indicator**: `HIGH` (ON)
- **Label**: `OVER TEMP`
