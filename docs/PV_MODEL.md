# Photovoltaic (PV) Mathematical Model

## Standard Test Condition (STC) Baseline
The mathematical digital twin calculates PV operating parameters relative to reference STC conditions:
- Reference Solar Irradiance: $G_{ref} = 1000\text{ W/m}^2$
- Reference Temperature: $T_{ref} = 25^\circ\text{C}$
- Reference Maximum Power Point Voltage: $V_{mp,ref} = 18.0\text{ V}$
- Reference Maximum Power Point Current: $I_{mp,ref} = 2.7\text{ A}$
- Open-Circuit Reference Voltage: $V_{oc,ref} = 21.6\text{ V}$
- Voltage Temperature Coefficient: $\beta_V = -0.004\text{ /}^\circ\text{C}$

## Governing Equations

### 1. PV Cell Temperature Estimation
Under solar illumination, solar absorption heats the PV module above ambient temperature:
$$T_{pv} = T_a + \left(\frac{G}{G_{ref}}\right) \times 3.0^\circ\text{C}$$

### 2. Output Current ($I$)
The generated photocurrent scales directly with available solar irradiance:
$$I(G) = I_{mp,ref} \times \left(\frac{G}{G_{ref}}\right)$$

### 3. Terminal Voltage ($V$)
The terminal voltage exhibits a characteristic negative temperature dependency:
$$V(T_{pv}, G) = V_{mp,ref} \times \left[1 + \beta_V \times (T_{pv} - T_{ref})\right]$$

For low irradiance conditions ($G < 40\text{ W/m}^2$), voltage scales down smoothly:
$$V(G) = V \times \left(\frac{G}{40.0}\right) \quad \text{for } G < 40\text{ W/m}^2$$

### 4. Electrical Output Power ($P$)
$$P = V \times I$$
