"""
Synthetic Dataset Generator
Implements the exact deterministic mathematical PV digital twin used on the ESP32-S3
to generate balanced multi-condition datasets for offline TinyML model training and evaluation.
"""

import os
import numpy as np
import pandas as pd

OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "pv_dataset.csv")

# Reference physical model parameters (STC: 1000 W/m2, 25 deg C)
Gref = 1000.0
Tref = 25.0
Vmp_ref = 18.0
Imp_ref = 2.7
Voc_ref = 21.6
beta_V = -0.004
SHADING_FACTOR = 0.45
TEMP_RISE_OVER_TEMP = 35.0

FAULT_CLASSES = ["NORMAL", "PARTIAL SHADE", "OPEN CIRCUIT", "OVER TEMP"]

def calculate_pv_sample(G, Ta, H, fault_mode, timestamp_ms, noise_std=0.01):
    # Base solar cell heating under normal irradiance
    solar_heating = (G / Gref) * 3.0
    Tpv = Ta + solar_heating

    # Base electrical calculations
    I_base = Imp_ref * (G / Gref)
    V_base = Vmp_ref * (1.0 + beta_V * (Tpv - Tref))
    if G < 40.0:
        V_base *= (G / 40.0)

    if fault_mode == "NORMAL":
        I = I_base
        V = V_base
        P = V * I

    elif fault_mode == "PARTIAL SHADE":
        I = I_base * SHADING_FACTOR
        V = V_base * 0.95
        Tpv = Ta
        P = V * I

    elif fault_mode == "OPEN CIRCUIT":
        I = 0.0
        V = Voc_ref * (1.0 + beta_V * (Ta - Tref))
        if G < 40.0:
            V *= (G / 40.0)
        Tpv = Ta
        P = 0.0

    elif fault_mode == "OVER TEMP":
        Tpv = Ta + TEMP_RISE_OVER_TEMP
        V = Vmp_ref * (1.0 + beta_V * (Tpv - Tref))
        if G < 40.0:
            V *= (G / 40.0)
        I = Imp_ref * (G / Gref) * 0.95
        P = V * I

    # Add realistic sensor micro-fluctuations (bounded Gaussian noise)
    if noise_std > 0:
        V = max(0.0, V * (1.0 + np.random.normal(0, noise_std)))
        if fault_mode != "OPEN CIRCUIT":
            I = max(0.0, I * (1.0 + np.random.normal(0, noise_std)))
        P = V * I

    return {
        "timestamp_ms": timestamp_ms,
        "irradiance_wm2": round(float(G), 1),
        "humidity_percent": round(float(H), 1),
        "ambient_temp_c": round(float(Ta), 1),
        "pv_temp_c": round(float(Tpv), 1),
        "voltage_v": round(float(V), 2),
        "current_a": round(float(I), 2),
        "power_w": round(float(P), 2),
        "fault_mode": fault_mode
    }

def generate_dataset(num_samples_per_class=250, output_path=OUTPUT_FILE, seed=42):
    np.random.seed(seed)
    records = []
    current_time = 1000

    print(f"Generating synthetic dataset with {num_samples_per_class * len(FAULT_CLASSES)} total samples...")

    for fault in FAULT_CLASSES:
        for _ in range(num_samples_per_class):
            # Vary irradiance realistically between 150 and 1000 W/m2
            G = np.random.uniform(150.0, 1000.0)
            # Vary ambient temperature realistically between 18.0 and 42.0 deg C
            Ta = np.random.uniform(18.0, 42.0)
            # Vary humidity between 30.0% and 85.0%
            H = np.random.uniform(30.0, 85.0)

            sample = calculate_pv_sample(G, Ta, H, fault, current_time)
            records.append(sample)
            current_time += 1000

    df = pd.DataFrame(records)
    df.to_csv(output_path, index=False)
    print(f"Dataset successfully saved to: {output_path}")
    print(f"Summary by class:\n{df['fault_mode'].value_counts()}")
    return df

if __name__ == "__main__":
    generate_dataset()
