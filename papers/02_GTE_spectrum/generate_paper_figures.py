"""
generate_paper_figures.py
=========================
Generates the two canonical mass-vs-n_value figures for the GTE Particle Spectrum paper
from the v4 canonical candidates.csv.

Figure 1: gte_spectrum_full.png
    Full 1M-candidate landscape, log-log, color-coded by tier.
    NO particle name labels (they are illegible at this scale).
    SM-matched particles shown as larger black × markers.

Figure 2: gte_spectrum_sm_zoom.png
    Zoomed view restricted to the SM fermion mass range (0.3–200,000 MeV).
    Full color-coded landscape in this window + labeled SM particles (name + symbol).
    Uses the same color scheme as Figure 1.

Run (from ugp-physics clone):
    python3 papers/02_GTE_spectrum/generate_paper_figures.py

Uses the frozen ``discovery_engine/candidates.csv`` at the repository root.

Outputs (written next to this script):
    gte_spectrum_full.png
    gte_spectrum_sm_zoom.png
"""

import os
import sys
import pathlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = pathlib.Path(__file__).parent
_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
# Frozen spectrum build — same CSV as discovery_engine/ in this repository
CANDIDATES_CSV = _REPO_ROOT / "discovery_engine" / "candidates.csv"

OUT_FULL  = SCRIPT_DIR / "gte_spectrum_full.png"
OUT_ZOOM  = SCRIPT_DIR / "gte_spectrum_sm_zoom.png"

# ---------------------------------------------------------------------------
# Color scheme (matches ClassificationThresholds in engine)
# ---------------------------------------------------------------------------
COLOR_MAP = {
    "Green":  "#2ca02c",
    "Blue":   "#1f77b4",
    "Purple": "#9467bd",
    "Orange": "#ff7f0e",
    "Red":    "#d62728",
    "Gray":   "#7f7f7f",
    "Teal":   "#17becf",
    "Brown":  "#8c564b",
}
COLOR_ALPHA = {
    "Green": 0.85, "Blue": 0.65, "Purple": 0.55,
    "Orange": 0.45, "Red": 0.35, "Gray": 0.3,
    "Teal": 0.5, "Brown": 0.4,
}
COLOR_SIZE = {
    "Green": 18, "Blue": 8, "Purple": 5,
    "Orange": 3, "Red": 2, "Gray": 2,
    "Teal": 4, "Brown": 3,
}

# SM particle display names and PDG masses (MeV) for the zoom plot
SM_LABELS = {
    # Charged leptons
    "electron":        ("e⁻",        0.511),
    "muon":            ("μ",         105.66),
    "tau":             ("τ",        1776.86),
    # Quarks
    "up":              ("u",            2.16),
    "down":            ("d",            4.67),
    "strange":         ("s",           93.0),
    "charm":           ("c",         1270.0),
    "bottom":          ("b",         4180.0),
    "top":             ("t",       172760.0),
    # Baryons
    "proton":          ("p",          938.3),
    "neutron":         ("n",          939.6),
    "lambda":          ("Λ",         1115.7),
    "sigma_plus":      ("Σ⁺",        1189.4),
    "sigma_zero":      ("Σ⁰",        1192.6),
    "sigma_minus":     ("Σ⁻",        1197.4),
    "xi_zero":         ("Ξ⁰",        1314.9),
    "xi_minus":        ("Ξ⁻",        1321.7),
    "omega_minus":     ("Ω⁻",        1672.5),
    # Bosons
    "W_boson":         ("W",        80369.2),  # PDG 2024 (was 80379.0 ≈ PDG 2022)
    "Z_boson":         ("Z",        91188.0),
    "Higgs_boson":     ("H",       125090.0),
}

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
def load_candidates(path):
    if not path.exists():
        sys.exit(f"ERROR: candidates.csv not found at:\n  {path}\n"
                 "Run the discovery step first (see PROVENANCE.md).")
    print(f"Loading {path} ...")
    df = pd.read_csv(path, low_memory=False)
    print(f"  Loaded {len(df):,} rows.")

    # Ensure numeric columns
    for col in ("n_value", "mass_mev_calibrated", "confidence"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Use calibrated mass; fall back to raw
    if "mass_mev_calibrated" in df.columns:
        df["_mass"] = df["mass_mev_calibrated"]
    elif "mass_mev" in df.columns:
        df["_mass"] = pd.to_numeric(df["mass_mev"], errors="coerce")
    else:
        sys.exit("ERROR: no mass column found.")

    # Drop non-positive masses / n_values
    df = df[df["_mass"] > 0].copy()
    df = df[df["n_value"] > 0].copy()

    # SM-matched flag — all known SM particles (neutrinos excluded: mass=NaN)
    df["_is_sm"] = (
        df["canonical_match"].notna()
        & df["canonical_match"].astype(str).str.strip().isin(list(SM_LABELS.keys()))
    )

    print(f"  SM-matched rows: {df['_is_sm'].sum()}")
    return df


# ---------------------------------------------------------------------------
# Legend handles helper
# ---------------------------------------------------------------------------
def tier_legend_handles(tiers):
    handles = []
    labels_desc = {
        "Green":  "Green — best experimental targets (top 2%)",
        "Blue":   "Blue — high priority (top 2–6%)",
        "Purple": "Purple — medium priority (top 6–14%)",
        "Orange": "Orange — low priority (top 14–30%)",
        "Red":    "Red — very low priority (bottom 70%)",
    }
    for tier in tiers:
        if tier in labels_desc:
            handles.append(Line2D(
                [0], [0], marker='o', color='w',
                markerfacecolor=COLOR_MAP[tier],
                markersize=8 if tier == "Green" else 6,
                label=labels_desc[tier],
                alpha=COLOR_ALPHA.get(tier, 0.7),
            ))
    handles.append(Line2D(
        [0], [0], marker='x', color='black',
        markersize=9, markeredgewidth=2,
        label="SM particle (canonical match)",
        linestyle='None',
    ))
    return handles


# ---------------------------------------------------------------------------
# Figure 1: Full landscape (no labels)
# ---------------------------------------------------------------------------
def plot_full(df, out_path):
    print("Generating Figure 1: full landscape …")
    fig, ax = plt.subplots(figsize=(12, 7))

    tiers = ["Red", "Orange", "Purple", "Blue", "Green"]
    for tier in tiers:
        sub = df[df["classification_color"] == tier]
        if sub.empty:
            continue
        ax.scatter(
            sub["n_value"], sub["_mass"],
            c=COLOR_MAP[tier],
            s=COLOR_SIZE[tier],
            alpha=COLOR_ALPHA[tier],
            linewidths=0,
            rasterized=True,
            zorder=2 if tier == "Green" else 1,
        )

    # SM particles — large black ×, no text labels
    sm = df[df["_is_sm"]]
    if not sm.empty:
        ax.scatter(
            sm["n_value"], sm["_mass"],
            c="black", marker="x", s=60,
            linewidths=1.8, zorder=5,
        )

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("n-value  (information complexity)", fontsize=13)
    ax.set_ylabel("Calibrated mass  (MeV)", fontsize=13)
    ax.set_title(
        f"GTE Particle Spectrum at n = 10  —  1,000,035 candidates",
        fontsize=14, fontweight="bold",
    )
    ax.grid(True, which="both", linestyle=":", linewidth=0.4, alpha=0.5)

    legend = ax.legend(
        handles=tier_legend_handles(tiers),
        loc="lower right",
        fontsize=9,
        framealpha=0.9,
        title="Viability tier",
        title_fontsize=9,
    )

    fig.tight_layout()
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved → {out_path}")


# ---------------------------------------------------------------------------
# Figure 2: Zoomed SM range with labels
# ---------------------------------------------------------------------------
def plot_sm_zoom(df, out_path):
    print("Generating Figure 2: SM-range zoom with labels …")

    # Restrict to SM fermion mass window (a bit wider than top quark)
    MASS_LO = 0.3      # MeV  (below electron)
    MASS_HI = 2.0e5    # MeV  (~200 GeV, covers top + W/Z/H)
    N_LO    = 1
    N_HI    = 3e6      # wide enough to include sigma/xi/omega (n up to ~1.8M)

    window = df[(df["_mass"] >= MASS_LO) & (df["_mass"] <= MASS_HI)
                & (df["n_value"] >= N_LO) & (df["n_value"] <= N_HI)].copy()
    print(f"  Candidates in zoom window: {len(window):,}")

    fig, ax = plt.subplots(figsize=(15, 9))

    tiers = ["Red", "Orange", "Purple", "Blue", "Green"]
    for tier in tiers:
        sub = window[window["classification_color"] == tier]
        if sub.empty:
            continue
        ax.scatter(
            sub["n_value"], sub["_mass"],
            c=COLOR_MAP[tier],
            s=COLOR_SIZE[tier] * 1.5,
            alpha=COLOR_ALPHA[tier],
            linewidths=0,
            rasterized=True,
            zorder=2 if tier == "Green" else 1,
        )

    # SM particles — colored × then label
    sm_window = window[window["_is_sm"]].copy()

    # Build best-representative row per canonical name
    best = {}
    for _, row in sm_window.iterrows():
        name = str(row["canonical_match"]).strip()
        if name not in best:
            best[name] = row
        else:
            # prefer row whose mass is closest to PDG reference
            pdg_mass = SM_LABELS.get(name, (name, None))[1]
            if pdg_mass is not None:
                if abs(row["_mass"] - pdg_mass) < abs(best[name]["_mass"] - pdg_mass):
                    best[name] = row

    # Plot SM markers
    for name, row in best.items():
        ax.scatter(
            row["n_value"], row["_mass"],
            c="black", marker="x", s=120,
            linewidths=2.2, zorder=6,
        )

    # Annotate SM particles with symbol + name.
    # Two annotation modes:
    #   "factor"  — xytext = (n*dx, m*dy)  good for isolated particles
    #   "points"  — xytext in offset points from the data point (for dense clusters)
    #
    # Format: (mode, dx, dy, ha, va)
    label_offsets = {
        # Leptons — well separated, use factor mode
        "electron":    ("points",  +65,     0,  "left",  "center"),
        "muon":        ("points",  -65,     0,  "right", "center"),
        "tau":         ("points",    0,   +55,  "center", "bottom"),
        # Quarks
        "up":          ("factor",  3.0,   2.1,  "left",  "bottom"),
        "down":        ("factor",  3.0,   1.55, "left",  "bottom"),
        "strange":     ("points",  +18,   -30,  "left",   "top"),
        "charm":       ("points",  +65,   +45,  "left",  "bottom"),
        "bottom":      ("points",    0,   +55,  "center", "bottom"),
        "top":         ("points",  +65,     0,  "left",  "center"),
        # Baryons — carefully routed so NO callout lines cross each other.
        #
        # Cluster 1 (low n: proton~11K, neutron~11K, lambda~38K):
        #   These sit left of the hinge band. Fan labels downward-left.
        #   proton > neutron > lambda ordered top-to-bottom in label space.
        "proton":      ("points",  -80,   -40,  "right", "top"),
        "neutron":     ("points",  -40,   +18,  "right", "bottom"),
        "lambda":      ("points",    0,   -55,  "center", "top"),
        #
        # Cluster 2 (sigma ~640K) and Cluster 3 (xi ~880K, omega ~1.8M):
        # sigma_zero: goes DOWN-RIGHT into the open space below the hinge band
        "sigma_zero":  ("points",    0,   +55,  "center", "bottom"),
        # sigma_plus and sigma_minus: staircase UP-LEFT, clear of sigma_zero
        "sigma_plus":  ("points",   +3,  -125,  "left",   "top"),
        "sigma_minus": ("points",  -85,   +85,  "right", "bottom"),
        # xi: continue staircase UP-LEFT above sigma
        "xi_zero":     ("points",  -30,  +120,  "right", "bottom"),
        "xi_minus":    ("points",  +11,  +116,  "left",  "bottom"),
        # omega_minus: slightly right of straight down (5° tilt)
        "omega_minus": ("points",   +5,   -55,  "left",   "top"),
        # Bosons — at n=3, push labels rightward into the plot interior
        "W_boson":     ("factor",  15.0,  0.58, "left",  "top"),
        "Z_boson":     ("factor",  15.0,  1.00, "left",  "center"),
        "Higgs_boson": ("factor",  15.0,  1.60, "left",  "bottom"),
    }

    # Human-readable display names for labels
    display_names = {
        "electron": "electron", "muon": "muon", "tau": "tau",
        "up": "up", "down": "down", "strange": "strange",
        "charm": "charm", "bottom": "bottom", "top": "top",
        "proton": "proton", "neutron": "neutron",
        "lambda": "lambda", "sigma_plus": "sigma+", "sigma_zero": "sigma0",
        "sigma_minus": "sigma−", "xi_zero": "xi0", "xi_minus": "xi−",
        "omega_minus": "omega−",
        "W_boson": "W boson", "Z_boson": "Z boson", "Higgs_boson": "Higgs",
    }

    for name, row in best.items():
        if name not in SM_LABELS:
            continue
        symbol, _ = SM_LABELS[name]
        disp = display_names.get(name, name)
        n  = float(row["n_value"])
        m  = float(row["_mass"])
        spec = label_offsets.get(name, ("factor", 3.0, 1.2, "left", "bottom"))
        mode, dx, dy, ha, va = spec

        if mode == "factor":
            xt, yt = n * dx, m * dy
            textcoords = "data"
        else:
            xt, yt = dx, dy
            textcoords = "offset points"

        ax.annotate(
            f"{symbol}  {disp}",
            xy=(n, m),
            xytext=(xt, yt),
            xycoords="data",
            textcoords=textcoords,
            fontsize=9, fontweight="bold", color="black",
            ha=ha, va=va,
            arrowprops=dict(
                arrowstyle="->",
                color="black",
                lw=1.2,
                alpha=0.75,
                connectionstyle="arc3,rad=0.0",
            ),
            zorder=7,
            clip_on=False,
        )

    # ---------------------------------------------------------------------------
    # Novel GTE predictions — high-confidence Green non-SM candidates
    # Three distinct predictions highlighted with ★ markers + teal callouts
    # ---------------------------------------------------------------------------
    PRED_COLOR    = "#1a6fcc"   # blue  — genuinely novel predictions (P1,P2,P3,P6–P11)
    VARIANT_COLOR = "#d67b00"   # amber — trajectory-path variants (P4, P5): same SM triple, distinct path

    def variant_star(ax, n, m, label, xoff, yoff, ha, va):
        """Hollow-style star for trajectory-path variants (not novel predictions)."""
        ax.scatter(n, m, marker="*", s=220, c="none", edgecolors=VARIANT_COLOR,
                   linewidths=1.8, zorder=12)
        ax.annotate(
            label,
            xy=(n, m),
            xytext=(xoff, yoff), textcoords="offset points",
            fontsize=8.5, fontweight="bold", color=VARIANT_COLOR,
            ha=ha, va=va,
            arrowprops=dict(arrowstyle="->", color=VARIANT_COLOR, lw=1.3, alpha=0.9),
            zorder=13, clip_on=False,
        )

    # Pull Green non-SM candidates in window
    novel = df[
        (df["classification_color"] == "Green") &
        (~df["_is_sm"]) &
        (df["_mass"] >= MASS_LO) & (df["_mass"] <= MASS_HI) &
        (df["n_value"] >= N_LO) & (df["n_value"] <= N_HI)
    ].copy()

    def pred_star(ax, n, m, label, xoff, yoff, ha, va):
        ax.scatter(n, m, marker="*", s=260, c=PRED_COLOR, zorder=12, linewidths=0)
        ax.annotate(
            label,
            xy=(n, m),
            xytext=(xoff, yoff), textcoords="offset points",
            fontsize=8.5, fontweight="bold", color=PRED_COLOR,
            ha=ha, va=va,
            arrowprops=dict(arrowstyle="->", color=PRED_COLOR, lw=1.3, alpha=0.9),
            zorder=13, clip_on=False,
        )

    # --- Prediction 1: highest-confidence candidate (~3 MeV, n=4935) ---
    # Label goes DOWN from the star
    p1 = novel.loc[novel["confidence"].idxmax()]
    pred_star(ax, p1["n_value"], p1["_mass"],
              f"★ GTE-P1\n{p1['_mass']:.2f} MeV",
              0, -55, "center", "top")

    # --- Prediction 2: 107–137 MeV cluster (n=4702, mass=107 MeV) ---
    # Angle callout down-right to avoid overlapping the green band
    p2_band = novel[(novel["_mass"] >= 105) & (novel["_mass"] <= 140)]
    if not p2_band.empty:
        p2 = p2_band.loc[p2_band["confidence"].idxmax()]
        pred_star(ax, p2["n_value"], p2["_mass"],
                  f"★ GTE-P2\n{p2['_mass']:.0f} MeV",
                  +55, -45, "left", "top")

    # --- Prediction 3: nucleon-adjacent band (~800 MeV) ---
    p3_band = novel[(novel["_mass"] >= 790) & (novel["_mass"] <= 820)]
    if not p3_band.empty:
        p3 = p3_band.loc[p3_band["confidence"].idxmax()]
        pred_star(ax, p3["n_value"], p3["_mass"],
                  f"★ GTE-P3\n~800 MeV band",
                  0, -55, "center", "top")

    # --- Path variant P4: n=42, mass=137 MeV — muon triple, distinct path ---
    p4_band = novel[(novel["n_value"] == 42)]
    if not p4_band.empty:
        p4 = p4_band.iloc[0]
        variant_star(ax, p4["n_value"], p4["_mass"],
                     f"GTE-P4\n{p4['_mass']:.0f} MeV\n(path variant)",
                     0, +55, "center", "bottom")

    # --- Path variant P5: n=73, mass=21 MeV — electron triple, distinct path ---
    p5_band = novel[(novel["n_value"] == 73)]
    if not p5_band.empty:
        p5 = p5_band.iloc[0]
        variant_star(ax, p5["n_value"], p5["_mass"],
                     f"GTE-P5\n{p5['_mass']:.1f} MeV\n(path variant)",
                     -65, 0, "right", "center")

    # --- Prediction 6: ~31 MeV (n=6333) — isolated, below GTE-P2 ---
    p6_band = novel[(novel["n_value"] == 6333)]
    if not p6_band.empty:
        p6 = p6_band.iloc[0]
        pred_star(ax, p6["n_value"], p6["_mass"],
                  f"★ GTE-P6\n{p6['_mass']:.0f} MeV",
                  -65, 0, "right", "center")

    # --- Prediction 7: ~212 MeV (n=5383) — same angle as GTE-P2 (down-right) ---
    p7_band = novel[(novel["n_value"] == 5383)]
    if not p7_band.empty:
        p7 = p7_band.iloc[0]
        pred_star(ax, p7["n_value"], p7["_mass"],
                  f"★ GTE-P7\n{p7['_mass']:.0f} MeV",
                  +55, -45, "left", "top")

    # --- Prediction 8: ~298 MeV cluster (n=5867) — same angle, slightly less steep ---
    p8_band = novel[(novel["n_value"] == 5867)]
    if not p8_band.empty:
        p8 = p8_band.iloc[0]
        pred_star(ax, p8["n_value"], p8["_mass"],
                  f"★ GTE-P8\n~{p8['_mass']:.0f} MeV cluster",
                  +55, -30, "left", "top")

    # --- Prediction 9: n=275, mass=561 MeV — below charm (same n-value as charm!) ---
    p9_band = novel[(novel["n_value"] == 275)]
    if not p9_band.empty:
        p9 = p9_band.iloc[0]
        pred_star(ax, p9["n_value"], p9["_mass"],
                  f"★ GTE-P9\n{p9['_mass']:.0f} MeV",
                  0, -28, "center", "top")

    # --- Prediction 10: charm-adjacent band ~1100–1350 MeV (n~495K) ---
    # Aligns with Paper 01 theoretical charm prediction (1271 MeV)
    p10_band = novel[(novel["_mass"].between(1100, 1350))]
    if not p10_band.empty:
        p10 = p10_band.nlargest(1, "confidence").iloc[0]
        pred_star(ax, p10["n_value"], p10["_mass"],
                  f"★ GTE-P10\n~{p10['_mass']:.0f} MeV\n(cf. c-th)",
                  -4, -81, "center", "top")

    # --- Prediction 11: tau-adjacent band ~1600–1900 MeV (n~1.6M) ---
    # Aligns with Paper 01 theoretical tau prediction (1771 MeV)
    p11_band = novel[(novel["_mass"].between(1600, 1900)) & (novel["n_value"] <= N_HI)]
    if not p11_band.empty:
        p11 = p11_band.nlargest(1, "confidence").iloc[0]
        pred_star(ax, p11["n_value"], p11["_mass"],
                  f"★ GTE-P11\n~{p11['_mass']:.0f} MeV\n(cf. τ-th)",
                  0, -98, "center", "top")

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(N_LO * 0.8, N_HI * 2.0)
    ax.set_ylim(MASS_LO * 0.5, MASS_HI * 1.5)
    ax.set_xlabel("n-value  (information complexity)", fontsize=13)
    ax.set_ylabel("Calibrated mass  (MeV)", fontsize=13)
    ax.set_title(
        "GTE Particle Spectrum — SM mass range (0.3 MeV – 200 GeV)\n"
        "× confirmed SM particles   ★ novel GTE predictions   ☆ trajectory-path variants",
        fontsize=13, fontweight="bold",
    )
    ax.grid(True, which="both", linestyle=":", linewidth=0.4, alpha=0.5)

    # Secondary x-axis tick labels in GeV for readability
    ax2 = ax.secondary_yaxis("right",
                              functions=(lambda m: m / 1000, lambda g: g * 1000))
    ax2.set_ylabel("Calibrated mass  (GeV)", fontsize=11)

    legend_handles = tier_legend_handles(tiers)
    legend_handles.append(Line2D(
        [0], [0], marker="*", color="w", markerfacecolor="#1a6fcc",
        markersize=11, label="★ GTE novel prediction (high confidence)",
        linestyle="None",
    ))
    legend_handles.append(Line2D(
        [0], [0], marker="*", color="w", markerfacecolor="none",
        markeredgecolor="#d67b00", markeredgewidth=1.8,
        markersize=11, label="☆ Trajectory-path variant (SM triple, distinct path)",
        linestyle="None",
    ))
    ax.legend(
        handles=legend_handles,
        loc="lower right",
        fontsize=9,
        framealpha=0.92,
        title="Viability tier",
        title_fontsize=9,
    )

    fig.tight_layout()
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved → {out_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    df = load_candidates(CANDIDATES_CSV)
    plot_full(df, OUT_FULL)
    plot_sm_zoom(df, OUT_ZOOM)
    print("\nDone. Both figures written to:")
    print(f"  {OUT_FULL}")
    print(f"  {OUT_ZOOM}")
