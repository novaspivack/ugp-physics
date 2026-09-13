#!/usr/bin/env python3
"""
generate_physics_validation.py
Generate the nuclear physics validation figure (physics_validation.png).

Reads periodic_table_data.csv from the same directory and produces a
four-panel summary:
  1. Q-value distribution by predicted decay mode
  2. Predicted decay mode distribution
  3. Half-life vs Q-value relationship
  4. Stability classification distribution

Usage:
    cd papers/03_nuclear
    python3 generate_physics_validation.py

Output:
    physics_validation.png (same directory)

Requirements: numpy, pandas, matplotlib
"""

import os
import re
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_CSV = os.path.join(SCRIPT_DIR, "periodic_table_data.csv")
OUTPUT_PNG = os.path.join(SCRIPT_DIR, "physics_validation.png")

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

# Unit-to-seconds conversion factors
UNIT_SECONDS = {
    "seconds": 1.0,
    "second":  1.0,
    "minutes": 60.0,
    "minute":  60.0,
    "hours":   3_600.0,
    "hour":    3_600.0,
    "days":    86_400.0,
    "day":     86_400.0,
    "years":   365.25 * 86_400.0,
    "year":    365.25 * 86_400.0,
}

STABLE_HALF_LIFE_S = 1e30    # sentinel for "stable" nuclei in log plots
STABLE_LOG_HALF_LIFE = 30.0  # log10 of sentinel value


def parse_half_life_s(raw):
    """Convert a half-life string (e.g. '2.52e+00 seconds', 'stable') to seconds."""
    if raw is None or (isinstance(raw, float) and np.isnan(raw)):
        return None
    s = str(raw).strip().lower()
    if s == "stable":
        return STABLE_HALF_LIFE_S
    # Match pattern like "2.52e+00 seconds" or "9.90e+00 years"
    m = re.match(r"([0-9eE+\-.]+)\s+(\w+)", s)
    if m:
        value = float(m.group(1))
        unit = m.group(2).rstrip("s") + "s"  # normalize pluralisation
        # try exact key first, then singular
        factor = UNIT_SECONDS.get(m.group(2), UNIT_SECONDS.get(unit))
        if factor is not None:
            return value * factor
    # Plain numeric
    try:
        return float(s)
    except ValueError:
        return None


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
    required = {"Predicted_Decay_Mode", "Predicted_Q_Value_MeV",
                "Predicted_Half_Life_s", "Stability_Class"}
    missing = required - set(df.columns)
    if missing:
        raise RuntimeError(f"CSV is missing required columns: {missing}")
    df["Half_Life_s_numeric"] = df["Predicted_Half_Life_s"].apply(parse_half_life_s)
    df["Log10_Half_Life"] = df["Half_Life_s_numeric"].apply(
        lambda x: np.log10(max(x, 1e-30)) if x is not None else np.nan
    )
    df = _apply_nubase_override(df)
    return df


def panel_q_distribution(ax: plt.Axes, df: pd.DataFrame) -> None:
    """Q-value histogram by decay mode (excluding stable which have Q=0)."""
    colors = {"alpha": "tomato", "beta": "cornflowerblue", "gamma": "mediumseagreen"}
    default_color = "gray"
    plotted_any = False
    for mode, grp in df.groupby("Predicted_Decay_Mode"):
        if mode == "stable":
            continue
        q_vals = grp["Predicted_Q_Value_MeV"].dropna()
        q_vals = q_vals[q_vals > 0]
        if q_vals.empty:
            continue
        color = colors.get(mode, default_color)
        ax.hist(q_vals, bins=15, alpha=0.72,
                label=f"{mode.capitalize()} decay (n={len(q_vals)})",
                color=color)
        plotted_any = True
    if not plotted_any:
        ax.text(0.5, 0.5, "No Q-value data", transform=ax.transAxes,
                ha="center", va="center")
    ax.set_xlabel("Q-value (MeV)", fontsize=11)
    ax.set_ylabel("Frequency", fontsize=11)
    ax.set_title("Q-value Distribution by Decay Mode", fontsize=13)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)


def panel_decay_mode_distribution(ax: plt.Axes, df: pd.DataFrame) -> None:
    """Bar chart of predicted decay mode counts (log scale)."""
    counts = df["Predicted_Decay_Mode"].value_counts()
    modes = counts.index.tolist()
    vals = counts.values.tolist()
    bar_colors = [
        {"alpha": "tomato", "beta": "cornflowerblue", "stable": "mediumseagreen"}.get(m, "lightgray")
        for m in modes
    ]
    bars = ax.bar(range(len(modes)), vals, color=bar_colors, alpha=0.8, edgecolor="white")
    ax.set_yscale("log")
    ax.set_xticks(range(len(modes)))
    ax.set_xticklabels([m.capitalize() for m in modes], rotation=30, ha="right")
    ax.set_xlabel("Predicted Decay Mode", fontsize=11)
    ax.set_ylabel("Number of Nuclei (log scale)", fontsize=11)
    ax.set_title("Predicted Decay Mode Distribution", fontsize=13)
    ax.grid(True, alpha=0.3, axis="y")
    for bar, count in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() * 1.25, str(count),
                ha="center", va="bottom", fontsize=10)


def panel_halflife_vs_qvalue(ax: plt.Axes, df: pd.DataFrame) -> None:
    """Scatter: log₁₀(half-life) vs Q-value, colored by decay mode."""
    color_map = {"alpha": "tomato", "beta": "cornflowerblue",
                 "gamma": "mediumseagreen", "stable": "steelblue"}
    for mode, grp in df.groupby("Predicted_Decay_Mode"):
        sub = grp.dropna(subset=["Log10_Half_Life", "Predicted_Q_Value_MeV"])
        if sub.empty:
            continue
        # Cap log half-life at STABLE_LOG_HALF_LIFE so stable sentinels plot at the top
        log_hl = sub["Log10_Half_Life"].clip(upper=STABLE_LOG_HALF_LIFE)
        marker = "^" if mode == "stable" else "o"
        ax.scatter(sub["Predicted_Q_Value_MeV"], log_hl,
                   c=color_map.get(mode, "gray"),
                   alpha=0.65, s=35, marker=marker,
                   label=mode.capitalize(), zorder=5)

    ax.set_xlabel("Q-value (MeV)", fontsize=11)
    ax.set_ylabel("log₁₀(Half-life / s)", fontsize=11)
    ax.set_title("Half-life vs Q-value Relationship", fontsize=13)
    # Mark the stable sentinel
    ax.axhline(STABLE_LOG_HALF_LIFE, color="steelblue", linestyle="--",
               linewidth=0.8, alpha=0.5, label=f"Stable sentinel (10^{STABLE_LOG_HALF_LIFE:.0f} s)")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)


def panel_stability_distribution(ax: plt.Axes, df: pd.DataFrame) -> None:
    """Pie chart of stability classification counts."""
    counts = df["Stability_Class"].value_counts()
    color_map = {
        "Green":  "mediumseagreen",
        "Blue":   "cornflowerblue",
        "Orange": "darkorange",
        "Red":    "crimson",
    }
    label_map = {
        "Green":  "Stable",
        "Blue":   "Long-lived",
        "Orange": "Primordial",
        "Red":    "Radioactive",
    }
    labels = []
    sizes = []
    colors = []
    for cls, cnt in counts.items():
        labels.append(f"{label_map.get(cls, cls)} ({cnt})")
        sizes.append(cnt)
        colors.append(color_map.get(cls, "lightgray"))

    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, colors=colors,
        autopct="%1.1f%%", startangle=90,
        textprops={"fontsize": 10},
    )
    for at in autotexts:
        at.set_fontsize(9)
    ax.set_title("Stability Classification Distribution", fontsize=13)

    total = len(df)
    stable_n = counts.get("Green", 0)
    pct = stable_n / total * 100 if total > 0 else 0
    ax.text(
        0.02, 0.98,
        f"Total: {total} nuclei\nStable (Green): {stable_n} ({pct:.1f}%)",
        transform=ax.transAxes, fontsize=9,
        verticalalignment="top",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
    )


def main():
    print(f"Reading data from: {DATA_CSV}")
    df = load_data(DATA_CSV)
    print(f"Loaded {len(df)} nuclei.")
    print(f"Decay modes: {df['Predicted_Decay_Mode'].value_counts().to_dict()}")
    print(f"Stability classes: {df['Stability_Class'].value_counts().to_dict()}")

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

    panel_q_distribution(ax1, df)
    panel_decay_mode_distribution(ax2, df)
    panel_halflife_vs_qvalue(ax3, df)
    panel_stability_distribution(ax4, df)

    fig.suptitle(
        "Nuclear Physics Validation: GTE Periodic-Table Predictions",
        fontsize=15, fontweight="bold", y=1.01,
    )
    plt.tight_layout()
    plt.savefig(OUTPUT_PNG, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {OUTPUT_PNG}")


if __name__ == "__main__":
    main()
