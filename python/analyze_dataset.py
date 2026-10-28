"""
Dataset Analysis and Visual Validation Script
Loads data/pv_dataset.csv, calculates key statistical metrics per fault class,
generates comparison tables, and saves high-resolution publication-quality plots.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "pv_dataset.csv")
PLOTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results", "plots")
TABLES_DIR = os.path.join(os.path.dirname(__file__), "..", "results", "tables")

def run_analysis():
    if not os.path.exists(DATA_FILE):
        print(f"Error: {DATA_FILE} not found. Run generate_dataset.py first.")
        return

    df = pd.read_csv(DATA_FILE)
    print(f"Loaded dataset: {df.shape[0]} rows, {df.shape[1]} columns.")
    print(f"Columns: {list(df.columns)}")

    os.makedirs(PLOTS_DIR, exist_ok=True)
    os.makedirs(TABLES_DIR, exist_ok=True)

    # 1. Summary Statistics Table
    summary_stats = df.groupby("fault_mode")[["voltage_v", "current_a", "power_w", "pv_temp_c"]].agg(
        ["mean", "std", "min", "max"]
    )
    summary_csv = os.path.join(TABLES_DIR, "fault_class_summary.csv")
    summary_stats.to_csv(summary_csv)
    print(f"Saved class summary statistics to {summary_csv}")

    # Generate Markdown Table for documentation
    summary_md = os.path.join(TABLES_DIR, "fault_class_summary.md")
    with open(summary_md, "w", encoding="utf-8") as f:
        f.write("# PV Fault Class Statistical Summary\n\n")
        f.write(summary_stats.to_markdown())
    print(f"Saved markdown summary table to {summary_md}")

    # 2. Figure 1: I-V and P-V Characteristic Scatter Plots
    plt.figure(figsize=(14, 6))

    # Subplot 1: Voltage vs Current
    plt.subplot(1, 2, 1)
    for fault, color in [("NORMAL", "#2ecc71"), ("PARTIAL SHADE", "#f39c12"),
                         ("OPEN CIRCUIT", "#e74c3c"), ("OVER TEMP", "#9b59b6")]:
        subset = df[df["fault_mode"] == fault]
        plt.scatter(subset["voltage_v"], subset["current_a"], label=fault, alpha=0.6, edgecolors="none", s=30)
    plt.title("PV Operating Point Distribution (I-V Domain)", fontsize=13, fontweight="bold")
    plt.xlabel("Voltage (V)", fontsize=11)
    plt.ylabel("Current (A)", fontsize=11)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(frameon=True)

    # Subplot 2: Voltage vs Power
    plt.subplot(1, 2, 2)
    for fault, color in [("NORMAL", "#2ecc71"), ("PARTIAL SHADE", "#f39c12"),
                         ("OPEN CIRCUIT", "#e74c3c"), ("OVER TEMP", "#9b59b6")]:
        subset = df[df["fault_mode"] == fault]
        plt.scatter(subset["voltage_v"], subset["power_w"], label=fault, alpha=0.6, edgecolors="none", s=30)
    plt.title("PV Power Curve Comparison (P-V Domain)", fontsize=13, fontweight="bold")
    plt.xlabel("Voltage (V)", fontsize=11)
    plt.ylabel("Power (W)", fontsize=11)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(frameon=True)

    plt.tight_layout()
    fig1_path = os.path.join(PLOTS_DIR, "iv_pv_curves.png")
    plt.savefig(fig1_path, dpi=300)
    plt.close()
    print(f"Saved: {fig1_path}")

    # 3. Figure 2: Boxplots of Key Features Across Fault Classes
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    metrics = [
        ("voltage_v", "Terminal Voltage (V)", axes[0, 0]),
        ("current_a", "Array Current (A)", axes[0, 1]),
        ("power_w", "Output Power (W)", axes[1, 0]),
        ("pv_temp_c", "PV Cell Temperature (°C)", axes[1, 1])
    ]

    for col, label, ax in metrics:
        df.boxplot(column=col, by="fault_mode", ax=ax, grid=False, patch_artist=True)
        ax.set_title(label, fontsize=12, fontweight="bold")
        ax.set_xlabel("Fault Mode", fontsize=10)
        ax.set_ylabel(label, fontsize=10)
        ax.tick_params(axis="x", rotation=15)

    fig.suptitle("Feature Separability Across PV Operating Conditions", fontsize=14, fontweight="bold")
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    fig2_path = os.path.join(PLOTS_DIR, "fault_distributions.png")
    plt.savefig(fig2_path, dpi=300)
    plt.close()
    print(f"Saved: {fig2_path}")

    print("\n[SUCCESS] Dataset analysis and visualization complete.")

if __name__ == "__main__":
    run_analysis()
