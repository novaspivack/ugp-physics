#!/usr/bin/env python3
"""
generate_be_curve.py
Generate the nuclear binding energy curve figure (be_curve_final.png).

Reads periodic_table_data.csv from the same directory and plots
binding energy per nucleon (MeV/A) vs. mass number A, colored by
stability class.

Usage:
    cd papers/03_nuclear
    python3 generate_be_curve.py

Output:
    be_curve_final.png (same directory)

Requirements: numpy, pandas, matplotlib
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_CSV = os.path.join(SCRIPT_DIR, "periodic_table_data.csv")
OUTPUT_PNG = os.path.join(SCRIPT_DIR, "be_curve_final.png")

# Import NUBASE2020 empirical stability data
sys.path.insert(0, SCRIPT_DIR)
from nubase_stability_lookup import NUBASE_STABILITY as _NUBASE_STABILITY  # noqa: E402

# Map NUBASE categories → CSV Stability_Class keys (for Z=1-118)
_NUBASE_TO_CLASS = {
    "stable":      "Green",
    "primordial":  "Orange",
    "long_lived":  "Blue",
    "radioactive": "Red",
}

# Stability class → plot color and display label
STABILITY_COLORS = {
    "Green":  ("green",          "Stable"),
    "Blue":   ("cornflowerblue", "Long-lived (no stable isotopes)"),
    "Orange": ("darkorange",     "Primordial (effectively stable)"),
    "Red":    ("crimson",        "Radioactive"),
}

# Experimental BE/A reference values (MeV/A), from AME2020
EXPERIMENTAL_REFS = {
    2:   1.11,   # H-2
    4:   7.07,   # He-4
    12:  7.68,   # C-12
    16:  7.98,   # O-16
    56:  8.79,   # Fe-56
    208: 7.87,   # Pb-208
    238: 7.57,   # U-238
}

# Key nuclei to annotate (mass number → label)
KEY_NUCLEI_LABELS = {
    2:   "H-2",
    4:   "He-4",
    12:  "C-12",
    16:  "O-16",
    56:  "Fe-56",
    208: "Pb-208",
    238: "U-238",
}

# Per-nucleus text offset (points) for annotation arrows
ANNOTATION_OFFSETS = {
    2:   (20, 12),
    4:   (20, 10),
    12:  (25, -18),
    16:  (28, 10),
    56:  (15, 14),
    208: (18, 10),
    238: (22, 14),
}


def _apply_nubase_override(df: pd.DataFrame) -> pd.DataFrame:
    """Override Stability_Class for Z=1-118 using NUBASE2020 empirical data.

    The CSV's Stability_Class was produced by the GTE model (BE/A threshold) and
    incorrectly classifies elements like Tc (Z=43) and Pm (Z=61) as Green (stable).
    This function replaces those values with the correct empirical categories.
    For Z>118 the GTE prediction is retained.
    """
    if "Z" not in df.columns:
        return df
    df = df.copy()
    mask = df["Z"].between(1, 118)
    df.loc[mask, "Stability_Class"] = df.loc[mask, "Z"].map(
        lambda z: _NUBASE_TO_CLASS.get(_NUBASE_STABILITY.get(int(z), ""), "Red")
    )
    return df


def load_data(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    required = {"Mass_Number", "Binding_Energy_Per_Nucleon", "Stability_Class", "Symbol"}
    missing = required - set(df.columns)
    if missing:
        raise RuntimeError(f"CSV is missing required columns: {missing}")
    df = df.dropna(subset=["Mass_Number", "Binding_Energy_Per_Nucleon"])
    df["Mass_Number"] = df["Mass_Number"].astype(int)
    df = _apply_nubase_override(df)
    return df


def plot_be_curve(df: pd.DataFrame, output_path: str) -> None:
    fig, ax = plt.subplots(figsize=(13, 8))

    # --- scatter by stability class ---
    for cls, (color, label) in STABILITY_COLORS.items():
        subset = df[df["Stability_Class"] == cls]
        if subset.empty:
            continue
        ax.scatter(
            subset["Mass_Number"],
            subset["Binding_Energy_Per_Nucleon"],
            c=color, s=22, alpha=0.75, zorder=5,
            label=f"{label} ({len(subset)} nuclei)",
        )

    # --- smooth envelope line (sorted by A) ---
    sorted_df = df.sort_values("Mass_Number")
    ax.plot(
        sorted_df["Mass_Number"],
        sorted_df["Binding_Energy_Per_Nucleon"],
        color="steelblue", linewidth=0.9, alpha=0.4, zorder=3,
    )

    # --- experimental reference crosses ---
    exp_A = list(EXPERIMENTAL_REFS.keys())
    exp_be = list(EXPERIMENTAL_REFS.values())
    ax.scatter(
        exp_A, exp_be, c="red", s=60, marker="x", linewidths=1.8,
        label="Experimental (AME2020)", zorder=8,
    )

    # --- annotate key nuclei ---
    a_index = df.set_index("Mass_Number")["Binding_Energy_Per_Nucleon"].to_dict()
    for A, label in KEY_NUCLEI_LABELS.items():
        if A not in a_index:
            continue
        be = a_index[A]
        dx, dy = ANNOTATION_OFFSETS.get(A, (15, 10))
        ax.annotate(
            label, (A, be),
            xytext=(dx, dy), textcoords="offset points",
            fontsize=9, zorder=10,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow", alpha=0.85, edgecolor="gray"),
            arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0.05", color="gray"),
        )

    # --- formatting ---
    ax.set_xlabel("Mass Number (A)", fontsize=13)
    ax.set_ylabel("Binding Energy per Nucleon (MeV)", fontsize=13)
    ax.set_title(
        "Nuclear Binding Energy Curve: GTE Model Predictions vs Experimental Data",
        fontsize=14, fontweight="bold",
    )
    ax.set_xlim(0, df["Mass_Number"].max() + 15)
    ax.set_ylim(0, df["Binding_Energy_Per_Nucleon"].max() + 0.8)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=11, loc="lower right")

    model_info = (
        "GTE Renormalization Law\n"
        f"Nuclei: Z=1–{df['Z'].max() if 'Z' in df.columns else '?'}\n"
        f"Dataset: {len(df)} nuclei"
    )
    ax.text(
        0.98, 0.97, model_info,
        transform=ax.transAxes, fontsize=9,
        verticalalignment="top", horizontalalignment="right",
        bbox=dict(boxstyle="round", facecolor="lightblue", alpha=0.8),
    )

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_path}")


def main():
    print(f"Reading data from: {DATA_CSV}")
    df = load_data(DATA_CSV)
    print(f"Loaded {len(df)} nuclei. Mass number range: {df['Mass_Number'].min()}–{df['Mass_Number'].max()}")
    print(f"Stability classes: {df['Stability_Class'].value_counts().to_dict()}")
    plot_be_curve(df, OUTPUT_PNG)


if __name__ == "__main__":
    main()
