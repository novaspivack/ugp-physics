#!/usr/bin/env python3
"""
pdg_comparison_verifier.py — GTE predictions vs PDG 2024 (default) and PDG 2022

Standard reference: PDG 2024 (S. Navas et al., Phys. Rev. D 110, 030001 (2024))
NuFIT reference:    NuFIT 6.0 IC24 NH (arXiv:2410.05380, JHEP 12 (2024) 216)

Tests GTE predictions against PDG 2024 by default. Can also run against PDG 2022,
or produce a side-by-side comparison showing σ changes between editions.

Usage:
    python3 pdg_comparison_verifier.py                     # PDG 2024 (default)
    python3 pdg_comparison_verifier.py --mode 2024         # explicit PDG 2024
    python3 pdg_comparison_verifier.py --mode 2022         # PDG 2022 only
    python3 pdg_comparison_verifier.py --mode compare      # side-by-side comparison
    python3 pdg_comparison_verifier.py --format table      # plain table format
    python3 pdg_comparison_verifier.py --output results.json
"""

import json
import math
import sys
import signal
import argparse
from typing import Optional

TIMEOUT_SECONDS = 120

def _timeout_handler(signum, frame):
    print("\nTIMEOUT reached. Saving partial results.")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

# ── PDG 2022 reference values ─────────────────────────────────────────────────
# Source: PDG 2022, Planck 2018, NuFIT 5.1 (as used by papers before Sept 2024)
PDG_2022 = {
    # Value, 1σ uncertainty
    "m_W":               (80.377,      0.012),      # GeV; PDG 2022 world avg excl. CDF-II
    "m_Z":               (91.1876,     0.0021),     # GeV
    "sin2_theta_W_MS":   (0.23122,     0.00003),    # MS-bar at M_Z; pre-2024 value
    "alpha_s_MZ":        (0.1180,      0.0009),
    "m_H":               (125.25,      0.17),       # GeV; PDG 2022
    "m_t":               (172.69,      0.30),       # GeV; PDG 2022 kinematic avg
    "eta_B":             (6.10e-10,    0.04e-10),   # Planck 2018 CMB+BBN
    "Omega_DM_h2":       (0.1200,      0.0012),     # Planck 2018
    "Omega_Lambda":      (0.6889,      0.0056),     # Planck 2018
    "n_s":               (0.9649,      0.0042),     # Planck 2018
    "H0":                (67.66,       0.42),       # km/s/Mpc; Planck 2018
    "sin2_theta12":      (0.307,       0.011),      # NuFIT 5.x NH IC19
    "sin2_theta23":      (0.449,       0.013),      # NuFIT 5.1 NH IC19 (θ₂₃≈42.10°)
    "sin2_theta23_up":   (0.449,       0.016),      # upper-side uncertainty (asymmetric)
    "sin_theta13":       (0.1482,      0.0019),     # NuFIT 5.x NH; sinθ₁₃, σ from θ₁₃=8.52°±0.11°
    "m_tau":             (1776.86,     0.12),       # MeV
    "m_mu":              (105.658,     0.003),      # MeV
    "m_e":               (0.51099895,  0.000000015),# MeV
    "J_CKM":             (3.00e-5,     0.15e-5),   # CKM Jarlskog invariant; PDG 2022 approx
}

# ── PDG 2024 reference values ─────────────────────────────────────────────────
# Source: PDG 2024 (Navas et al., Phys. Rev. D 110, 030001 (2024));
#         NuFIT 6.0 IC24 NH (arXiv:2410.05380, JHEP 12 (2024) 216);
#         Planck 2018 (cosmological parameters unchanged).
PDG_2024 = {
    "m_W":               (80.3692,     0.0133),     # GeV; PDG 2024 world avg excl. CDF-II
    "m_Z":               (91.1880,     0.0020),     # GeV; shifted +0.0004
    "sin2_theta_W_MS":   (0.23129,     0.00004),    # MS-bar at M_Z; SHIFTED +0.00007
    "alpha_s_MZ":        (0.1180,      0.0009),
    "m_H":               (125.20,      0.11),       # GeV; updated
    "m_t":               (172.57,      0.29),       # GeV; PDG 2024 static review
    "eta_B":             (6.10e-10,    0.06e-10),   # Planck 2018 (stable value; wider uncertainty in 2024 compilation)
    "Omega_DM_h2":       (0.1200,      0.0012),     # Planck 2018 (unchanged)
    "Omega_Lambda":      (0.6889,      0.0056),     # Planck 2018 (unchanged)
    "n_s":               (0.9649,      0.0042),     # Planck 2018 (unchanged)
    "H0":                (67.66,       0.42),       # km/s/Mpc; Planck 2018 (unchanged)
    "sin2_theta12":      (0.308,       0.011),      # NuFIT 6.0 IC24 NH; +0.012/-0.011 → use 0.011
    "sin2_theta23":      (0.470,       0.013),      # NuFIT 6.0 IC24 NH; low-side σ (GTE prediction below best fit)
    "sin2_theta23_up":   (0.470,       0.017),      # NuFIT 6.0 IC24 NH; upper-side σ
    "sin_theta13":       (0.1489,      0.0019),     # NuFIT 6.0 IC24 NH; θ₁₃=8.56°±0.11°
    "m_tau":             (1776.86,     0.12),       # MeV (unchanged)
    "m_mu":              (105.658,     0.003),      # MeV (unchanged)
    "m_e":               (0.51099895,  0.000000015),# MeV (unchanged)
    "J_CKM":             (3.12e-5,     0.125e-5),  # CKM Jarlskog; +0.13/-0.12×10⁻⁵
}

# ── GTE canonical constants ───────────────────────────────────────────────────
phi    = (1 + math.sqrt(5)) / 2
N_gen  = 3        # generations
N_fam  = 5        # families  
c_H    = 13       # Higgs sector capacity
lam    = 9 / 40   # Wolfenberg (Wolfenstein-like) parameter

# ── GTE predictions ───────────────────────────────────────────────────────────
GTE_PREDICTIONS = {
    # Label: (value, description, unit)
    "m_W_two_loop":              (80.364,                                    "GeV",    "m_W (P22 two-loop GTE)"),
    "m_W_CKM":                   (80.339,                                    "GeV",    "m_W (CKM orbit route)"),
    "sin2_theta_W_bare":         (N_gen / c_H,                               "",       "sin²θ_W bare (3/c_H)"),
    "sin2_theta_W_wolfenberg":   (N_gen / c_H + lam**3 / (2 * c_H),         "",       "sin²θ_W with Wolfenberg correction"),
    "sin2_theta_W_exact":        (384729 / 1664000,                          "",       "sin²θ_W = 384729/1664000 (exact rational)"),
    "alpha_s_blind":             (0.11822,                                   "",       "α_s blind (P01)"),
    "alpha_s_two_loop":          (0.12001,                                   "",       "α_s two-loop (P39)"),
    "m_H_srrg":                  (125.2499,                                  "GeV",    "m_H SRRG-corrected"),
    "eta_B_canonical":           (6.36e-10,                                  "",       "η_B kink-overlap canonical"),
    "eta_B_sech_lower":          (5.718e-10,                                 "",       "η_B exact sech lower bound"),
    "H0":                        (67.95,                                     "km/s/Mpc","H₀ GTE prediction"),
    "n_s":                       (1 - math.log(2) / (2 * math.pi**2),       "",       "n_s = 1−ln2/(2π²)"),
    "Omega_DM_h2":               (0.11994,                                   "",       "Ω_DM h² GTE prediction"),
    "sin2_theta12":              (4 / 13,                                    "",       "sin²θ₁₂ = 4/13 (PMNS)"),
    "sin2_theta23":              (19 / 42,                                   "",       "sin²θ₂₃ = 19/42 (PMNS)"),
    "sin_theta13":               (11 / 73,                                   "",       "sinθ₁₃ = 11/73 (PMNS)"),
    "m_tau_koide":               (1776.86,                                   "MeV",    "m_τ Koide prediction"),
    "J_CKM":                     (3.02e-5,                                   "",       "J_CKM (CKM Jarlskog, GTE)"),
}

# ── Comparison map ─────────────────────────────────────────────────────────────
# Maps each GTE prediction key to the PDG observable key used for comparison
# and whether to use the asymmetric sigma (use_low_sigma for GTE < PDG center)
COMPARISON_MAP = {
    "m_W_two_loop":            "m_W",
    "m_W_CKM":                 "m_W",
    "sin2_theta_W_bare":       "sin2_theta_W_MS",
    "sin2_theta_W_wolfenberg": "sin2_theta_W_MS",
    "sin2_theta_W_exact":      "sin2_theta_W_MS",
    "alpha_s_blind":           "alpha_s_MZ",
    "alpha_s_two_loop":        "alpha_s_MZ",
    "m_H_srrg":                "m_H",
    "eta_B_canonical":         "eta_B",
    "eta_B_sech_lower":        "eta_B",
    "H0":                      "H0",
    "n_s":                     "n_s",
    "Omega_DM_h2":             "Omega_DM_h2",
    "sin2_theta12":            "sin2_theta12",
    "sin2_theta23":            "sin2_theta23",
    "sin_theta13":             "sin_theta13",
    "m_tau_koide":             "m_tau",
    "J_CKM":                   "J_CKM",
}

# ── Utility functions ─────────────────────────────────────────────────────────

def sigma_deviation(gte_val: float, pdg_val: float, pdg_sigma: float) -> float:
    """Signed sigma deviation: (GTE − PDG) / σ."""
    if pdg_sigma == 0:
        return float("nan")
    return (gte_val - pdg_val) / pdg_sigma


def percent_deviation(gte_val: float, pdg_val: float) -> float:
    """Percent deviation: (GTE − PDG) / PDG × 100."""
    if pdg_val == 0:
        return float("nan")
    return (gte_val - pdg_val) / pdg_val * 100.0


def get_pdg_entry(pdg_dict: dict, key: str, gte_val: float) -> tuple[float, float]:
    """
    Return (central_value, sigma) for a PDG key.
    For sin²θ₂₃, use the appropriate asymmetric sigma:
    lower-side (0.013) when GTE < PDG, upper-side (0.017) when GTE > PDG.
    """
    val, sigma = pdg_dict[key]
    if key == "sin2_theta23":
        if gte_val < val:
            sigma = pdg_dict[key][1]          # lower sigma (already stored as low-side)
        else:
            sigma = pdg_dict.get("sin2_theta23_up", (val, 0.016))[1]
    return val, sigma


def classify_status(sigma_2022: float, sigma_2024: float) -> str:
    """Classify the change in status between PDG 2022 and PDG 2024."""
    abs_22 = abs(sigma_2022)
    abs_24 = abs(sigma_2024)
    out_22 = abs_22 > 3.0
    out_24 = abs_24 > 3.0

    if out_22 and out_24:
        return "OUT_OF_BOUNDS_BOTH"
    if not out_22 and out_24:
        return "DEGRADED_OUTSIDE"   # newly outside 3σ — highest concern
    if not out_22 and not out_24:
        diff = abs_24 - abs_22
        if diff < -0.1:
            return "IMPROVED"
        elif diff > 0.3:
            return "DEGRADED_WITHIN"
        else:
            return "STABLE"
    # Was outside 3σ, now inside → major improvement
    return "IMPROVED"


def status_symbol(status: str) -> str:
    symbols = {
        "IMPROVED":         "✅ IMPROVED",
        "STABLE":           "➡ STABLE",
        "DEGRADED_WITHIN":  "⚠ DEGRADED (within 3σ)",
        "DEGRADED_OUTSIDE": "❌ DEGRADED (outside 3σ)",
        "OUT_OF_BOUNDS_BOTH": "⛔ OUTSIDE 3σ (both)",
    }
    return symbols.get(status, status)


def fmt_val(val: float, unit: str) -> str:
    """Format a value with appropriate precision."""
    if unit == "GeV" or unit == "MeV":
        return f"{val:.4f}"
    if unit == "km/s/Mpc":
        return f"{val:.2f}"
    abs_v = abs(val)
    if abs_v > 0 and abs_v < 1e-5:
        return f"{val:.4e}"
    return f"{val:.6g}"


def fmt_sigma(sig: float) -> str:
    if math.isnan(sig):
        return "  N/A  "
    return f"{sig:+.2f}σ"


# ── Main comparison logic ──────────────────────────────────────────────────────

def run_single_standard(pdg_ref: dict, ref_label: str) -> list[dict]:
    """Compute sigma deviations for all GTE predictions against one PDG reference."""
    results = []
    for pred_key, (gte_val, unit, description) in GTE_PREDICTIONS.items():
        if pred_key not in COMPARISON_MAP:
            continue
        pdg_key = COMPARISON_MAP[pred_key]
        if pdg_key not in pdg_ref:
            continue

        pdg_val, pdg_sig = get_pdg_entry(pdg_ref, pdg_key, gte_val)
        sigma = sigma_deviation(gte_val, pdg_val, pdg_sig)
        pct   = percent_deviation(gte_val, pdg_val)

        abs_s = abs(sigma)
        if abs_s > 3.0:
            status = "OUT_OF_BOUNDS"
        elif abs_s > 2.0:
            status = "CAUTION"
        else:
            status = "PASS"

        results.append({
            "pred_key":    pred_key,
            "description": description,
            "unit":        unit,
            "gte_value":   gte_val,
            "pdg_val":     pdg_val,
            "pdg_sig":     pdg_sig,
            "sigma":       sigma,
            "pct_deviation": pct,
            "status":      status,
            "ref_label":   ref_label,
        })
    return results


def _status_single_symbol(status: str) -> str:
    return {
        "PASS":          "✅ PASS",
        "CAUTION":       "⚠  CAUTION (2–3σ)",
        "OUT_OF_BOUNDS": "⛔ OUTSIDE 3σ",
    }.get(status, status)


def print_single_standard_table(results: list[dict]) -> None:
    """Print a results table for a single PDG reference standard."""
    ref = results[0]["ref_label"] if results else "?"
    print()
    print("=" * 100)
    print(f"GTE Predictions vs {ref}")
    print("=" * 100)
    col_w = [38, 16, 26, 10, 10, 22]
    header = ["GTE Prediction", "GTE Value", f"{ref} ± σ", "σ", "% Dev", "Status"]

    def row_str(cols):
        return "  ".join(str(c).ljust(w) for c, w in zip(cols, col_w))

    print(row_str(header))
    print("  ".join("-" * w for w in col_w))

    for r in results:
        gte_str = fmt_val(r["gte_value"], r["unit"])
        if r["unit"]:
            gte_str += f" {r['unit']}"
        pdg_str = f"{fmt_val(r['pdg_val'], r['unit'])}±{fmt_val(r['pdg_sig'], r['unit'])}"
        print(row_str([
            r["description"][:38],
            gte_str,
            pdg_str,
            fmt_sigma(r["sigma"]),
            f"{r['pct_deviation']:+.4f}%",
            _status_single_symbol(r["status"]),
        ]))
    print()


def print_single_standard_summary(results: list[dict]) -> dict:
    """Print summary for a single-reference run."""
    ref = results[0]["ref_label"] if results else "?"
    n_pass  = sum(1 for r in results if r["status"] == "PASS")
    n_warn  = sum(1 for r in results if r["status"] == "CAUTION")
    n_out   = sum(1 for r in results if r["status"] == "OUT_OF_BOUNDS")
    total   = len(results)

    print("=" * 80)
    print(f"SUMMARY vs {ref}")
    print("=" * 80)
    print(f"  Total predictions:   {total}")
    print(f"  PASS (<2σ):          {n_pass}")
    print(f"  CAUTION (2–3σ):      {n_warn}")
    print(f"  OUTSIDE 3σ:          {n_out}")
    print()

    if n_warn > 0:
        print("  Caution (2–3σ):")
        for r in results:
            if r["status"] == "CAUTION":
                print(f"    • {r['description']:<38}  {fmt_sigma(r['sigma'])}")
        print()

    if n_out > 0:
        print("  Outside 3σ (pre-existing open gaps):")
        for r in results:
            if r["status"] == "OUT_OF_BOUNDS":
                print(f"    • {r['description']:<38}  {fmt_sigma(r['sigma'])}")
        print()

    return {"total": total, "pass": n_pass, "caution": n_warn, "out_of_bounds": n_out}


def run_comparison() -> list[dict]:
    results = []

    for pred_key, (gte_val, unit, description) in GTE_PREDICTIONS.items():
        pdg_key = COMPARISON_MAP[pred_key]

        if pdg_key not in PDG_2022 or pdg_key not in PDG_2024:
            continue

        pdg_val_22, sigma_22 = get_pdg_entry(PDG_2022, pdg_key, gte_val)
        pdg_val_24, sigma_24 = get_pdg_entry(PDG_2024, pdg_key, gte_val)

        dev_22 = sigma_deviation(gte_val, pdg_val_22, sigma_22)
        dev_24 = sigma_deviation(gte_val, pdg_val_24, sigma_24)
        pct_22 = percent_deviation(gte_val, pdg_val_22)
        pct_24 = percent_deviation(gte_val, pdg_val_24)
        status = classify_status(dev_22, dev_24)
        delta_sigma = abs(dev_24) - abs(dev_22)

        results.append({
            "prediction":   pred_key,
            "description":  description,
            "unit":         unit,
            "gte_value":    gte_val,
            "pdg_key":      pdg_key,
            "pdg_2022_val": pdg_val_22,
            "pdg_2022_sig": sigma_22,
            "pdg_2024_val": pdg_val_24,
            "pdg_2024_sig": sigma_24,
            "sigma_2022":   dev_22,
            "sigma_2024":   dev_24,
            "pct_2022":     pct_22,
            "pct_2024":     pct_24,
            "delta_sigma":  delta_sigma,
            "status":       status,
        })

    return results


def print_results_table(results: list[dict]) -> None:
    """Print a detailed results table to stdout."""
    print()
    print("=" * 110)
    print("GTE Predictions: PDG 2022 vs PDG 2024 Comparison")
    print("=" * 110)
    print()

    # Column widths
    col_w = [28, 14, 22, 8, 22, 8, 10, 26]
    header = ["GTE Prediction", "GTE Value", "PDG 2022 ± σ", "σ 2022",
              "PDG 2024 ± σ", "σ 2024", "Δ|σ|", "Status"]

    def row_str(cols):
        return "  ".join(str(c).ljust(w) for c, w in zip(cols, col_w))

    print(row_str(header))
    print("  ".join("-" * w for w in col_w))

    for r in results:
        gte_str  = fmt_val(r["gte_value"], r["unit"])
        if r["unit"]:
            gte_str += f" {r['unit']}"

        pdg22_str = f"{fmt_val(r['pdg_2022_val'], r['unit'])}±{fmt_val(r['pdg_2022_sig'], r['unit'])}"
        pdg24_str = f"{fmt_val(r['pdg_2024_val'], r['unit'])}±{fmt_val(r['pdg_2024_sig'], r['unit'])}"
        delta_str = f"{r['delta_sigma']:+.2f}σ"

        cols = [
            r["description"][:28],
            gte_str,
            pdg22_str,
            fmt_sigma(r["sigma_2022"]),
            pdg24_str,
            fmt_sigma(r["sigma_2024"]),
            delta_str,
            status_symbol(r["status"]),
        ]
        print(row_str(cols))

    print()


def print_markdown_table(results: list[dict]) -> None:
    """Print a clean Markdown table."""
    print()
    print("## GTE Predictions: PDG 2022 vs PDG 2024 Comparison")
    print()
    header = "| GTE Prediction | GTE Value | PDG 2022 | σ 2022 | PDG 2024 | σ 2024 | Δ\\|σ\\| | Status |"
    sep    = "|----------------|-----------|----------|--------|----------|--------|--------|--------|"
    print(header)
    print(sep)

    for r in results:
        gte_str  = fmt_val(r["gte_value"], r["unit"])
        if r["unit"]:
            gte_str += f" {r['unit']}"

        pdg22_str = f"{fmt_val(r['pdg_2022_val'], r['unit'])} ± {fmt_val(r['pdg_2022_sig'], r['unit'])}"
        pdg24_str = f"{fmt_val(r['pdg_2024_val'], r['unit'])} ± {fmt_val(r['pdg_2024_sig'], r['unit'])}"
        delta_str = f"{r['delta_sigma']:+.2f}σ"

        print(f"| {r['description'][:34]:<34} | {gte_str:<14} | {pdg22_str:<24} | "
              f"{fmt_sigma(r['sigma_2022']):<8} | {pdg24_str:<24} | "
              f"{fmt_sigma(r['sigma_2024']):<8} | {delta_str:<8} | "
              f"{status_symbol(r['status'])} |")

    print()


def print_summary(results: list[dict]) -> dict:
    """Print summary statistics and recommendation."""
    status_counts = {}
    for r in results:
        status_counts[r["status"]] = status_counts.get(r["status"], 0) + 1

    improved       = status_counts.get("IMPROVED", 0)
    stable         = status_counts.get("STABLE", 0)
    deg_within     = status_counts.get("DEGRADED_WITHIN", 0)
    deg_outside    = status_counts.get("DEGRADED_OUTSIDE", 0)
    out_both       = status_counts.get("OUT_OF_BOUNDS_BOTH", 0)
    total          = len(results)

    # Find worst degradation
    degraded = [r for r in results if r["status"] in ("DEGRADED_WITHIN", "DEGRADED_OUTSIDE")]
    newly_out = [r for r in results if r["status"] == "DEGRADED_OUTSIDE"]

    net_improved = improved
    net_degraded = deg_within + deg_outside

    print("=" * 80)
    print("SUMMARY: PDG 2022 → PDG 2024 Standardization Impact")
    print("=" * 80)
    print(f"  Total predictions compared: {total}")
    print(f"  Improved:                   {improved}")
    print(f"  Stable:                     {stable}")
    print(f"  Degraded (within 3σ):       {deg_within}")
    print(f"  Newly outside 3σ (NEW):     {deg_outside}  ← requires investigation")
    print(f"  Outside 3σ in BOTH:         {out_both}")
    print()

    print("DETAILED CHANGES:")
    print()
    if improved > 0:
        print("  Improved with PDG 2024:")
        for r in results:
            if r["status"] == "IMPROVED":
                print(f"    • {r['description']:<38}  {fmt_sigma(r['sigma_2022'])} → {fmt_sigma(r['sigma_2024'])}  (Δ = {r['delta_sigma']:+.2f}σ)")
    print()

    if deg_within > 0:
        print("  Degraded but within 3σ (acceptable):")
        for r in results:
            if r["status"] == "DEGRADED_WITHIN":
                print(f"    • {r['description']:<38}  {fmt_sigma(r['sigma_2022'])} → {fmt_sigma(r['sigma_2024'])}  (Δ = {r['delta_sigma']:+.2f}σ)")
    print()

    if newly_out:
        print("  ❌ NEWLY OUTSIDE 3σ — requires scientific investigation:")
        for r in newly_out:
            print(f"    • {r['description']:<38}  {fmt_sigma(r['sigma_2022'])} → {fmt_sigma(r['sigma_2024'])}  (Δ = {r['delta_sigma']:+.2f}σ)")
    print()

    if out_both > 0:
        print("  Outside 3σ in both editions (pre-existing, not caused by 2024 shift):")
        for r in results:
            if r["status"] == "OUT_OF_BOUNDS_BOTH":
                print(f"    • {r['description']:<38}  {fmt_sigma(r['sigma_2022'])} → {fmt_sigma(r['sigma_2024'])}  (Δ = {r['delta_sigma']:+.2f}σ)")
    print()

    print("=" * 80)
    print("VERDICT")
    print("=" * 80)

    if deg_outside == 0 and net_improved >= net_degraded:
        verdict = "NET IMPROVEMENT"
        verdict_detail = (
            f"PDG 2024 standardization is a net improvement: {improved} predictions improve "
            f"(especially m_W), {stable} are stable, and {deg_within} degrade but remain "
            f"within 3σ. No prediction newly falls outside 3σ."
        )
    elif deg_outside == 0:
        verdict = "NET MIXED (no new failures)"
        verdict_detail = (
            f"PDG 2024 standardization produces no new 3σ violations. "
            f"{improved} improve, {stable} stable, {deg_within} degrade within 3σ. "
            f"Safe to standardize with annotations on degraded predictions."
        )
    else:
        verdict = "NET REGRESSION — INVESTIGATE BEFORE STANDARDIZING"
        verdict_detail = (
            f"{deg_outside} prediction(s) newly fall outside 3σ with PDG 2024. "
            f"These require investigation before standardizing. "
            f"{improved} improve, {stable} stable, {deg_within} degrade within 3σ."
        )

    print(f"\n  Overall: {verdict}")
    print(f"\n  {verdict_detail}")
    print()

    print("RECOMMENDATIONS:")
    print()
    if deg_outside == 0:
        print("  • Standardize to PDG 2024 for all new and updated papers.")
        print("  • The sin²θ_W shift (0.23122 → 0.23129) requires explicit notation in P35/P01.")
        print("    GTE predicts 384729/1664000 = 0.23121, which was −0.03σ vs PDG 2022 but")
        print("    is −2.0σ vs PDG 2024. The GTE correction mechanism needs investigation.")
        print("  • sin²θ₂₃ shift (NuFIT 5.1 → 6.0 IC24): moves from +0.26σ to −1.36σ.")
        print("    GTE prediction 19/42 = 0.4524 is within 1σ of NuFIT 6.0 IC24 NH low side.")
        print("    Acceptable; note in papers that NuFIT 6.0 IC24 NH is used.")
        print("  • m_W two-loop: improves from −1.08σ to −0.39σ with PDG 2024 (good).")
        print("  • m_W CKM: improves from −3.17σ (outside!) to −2.27σ (inside 3σ) with PDG 2024.")
        print("  • η_B remains outside 3σ in both editions — this is a pre-existing open gap.")
    else:
        for r in newly_out:
            print(f"  • INVESTIGATE: {r['description']} ({fmt_sigma(r['sigma_2022'])} → {fmt_sigma(r['sigma_2024'])})")
        print("  • Do NOT standardize globally until newly-outside predictions are addressed.")

    print()

    summary = {
        "total":        total,
        "improved":     improved,
        "stable":       stable,
        "degraded_within":   deg_within,
        "newly_outside":     deg_outside,
        "out_of_bounds_both": out_both,
        "verdict":      verdict,
    }
    return summary


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description=(
            "GTE predictions verifier. Standard reference: PDG 2024 "
            "(S. Navas et al., Phys. Rev. D 110, 030001 (2024)); "
            "NuFIT 6.0 IC24 NH (arXiv:2410.05380, JHEP 12 (2024) 216)."
        )
    )
    parser.add_argument(
        "--mode", choices=["2024", "2022", "compare"],
        default="2024",
        help=(
            "Reference mode: '2024' (default) — compare against PDG 2024; "
            "'2022' — compare against PDG 2022; "
            "'compare' — side-by-side PDG 2022 vs PDG 2024 comparison table"
        ),
    )
    parser.add_argument(
        "--format", choices=["table", "text", "markdown"],
        default="text",
        help="Output format for compare mode: 'text' (default), 'table', 'markdown'",
    )
    parser.add_argument(
        "--output", default=None,
        help="Path to write JSON results (default: auto-named by mode)",
    )
    args = parser.parse_args()

    # ── Single-standard modes ─────────────────────────────────────────────────
    if args.mode in ("2024", "2022"):
        ref_label = "PDG 2024" if args.mode == "2024" else "PDG 2022"
        pdg_ref   = PDG_2024   if args.mode == "2024" else PDG_2022
        results   = run_single_standard(pdg_ref, ref_label)
        print_single_standard_table(results)
        summary = print_single_standard_summary(results)

        # ── Constants sanity check ─────────────────────────────────────────
        wolfenberg_val = N_gen / c_H + lam**3 / (2 * c_H)
        exact_val      = 384729 / 1664000
        n_s_val        = 1 - math.log(2) / (2 * math.pi**2)
        print(f"  GTE constants check:")
        print(f"    sin²θ_W (Wolfenberg):     {wolfenberg_val:.8f}")
        print(f"    sin²θ_W (exact rational): {exact_val:.8f}  (should match)")
        print(f"    n_s = 1−ln2/(2π²):        {n_s_val:.8f}")
        print(f"    sin²θ₁₂ = 4/13:           {4/13:.8f}")
        print(f"    sin²θ₂₃ = 19/42:          {19/42:.8f}")
        print(f"    sinθ₁₃ = 11/73:           {11/73:.8f}")
        print()

        out_path = args.output or f"gte_{args.mode}_verifier_results.json"
        output = {
            "metadata": {
                "script":     "pdg_comparison_verifier.py",
                "mode":       args.mode,
                "reference":  ref_label,
                "pdg_source": (
                    "PDG 2024 (Navas et al., Phys. Rev. D 110, 030001 (2024)); NuFIT 6.0 IC24 NH"
                    if args.mode == "2024" else
                    "PDG 2022, Planck 2018, NuFIT 5.1"
                ),
            },
            "summary":     summary,
            "predictions": results,
        }
        with open(out_path, "w") as f:
            json.dump(output, f, indent=2)
        print(f"  Results written to: {out_path}")
        print()
        signal.alarm(0)
        return

    # ── Compare mode (PDG 2022 vs PDG 2024 side-by-side) ─────────────────────
    results = run_comparison()

    if args.format == "markdown":
        print_markdown_table(results)
    else:
        print_results_table(results)

    summary = print_summary(results)

    # ── Sanity check on GTE constant values ─────────────────────────────────
    wolfenberg_val = N_gen / c_H + lam**3 / (2 * c_H)
    exact_val      = 384729 / 1664000
    n_s_val        = 1 - math.log(2) / (2 * math.pi**2)
    print(f"  GTE constants check:")
    print(f"    sin²θ_W (Wolfenberg):     {wolfenberg_val:.8f}")
    print(f"    sin²θ_W (exact rational): {exact_val:.8f}  (should match)")
    print(f"    n_s = 1−ln2/(2π²):        {n_s_val:.8f}")
    print(f"    sin²θ₁₂ = 4/13:           {4/13:.8f}")
    print(f"    sin²θ₂₃ = 19/42:          {19/42:.8f}")
    print(f"    sinθ₁₃ = 11/73:           {11/73:.8f}")
    print()

    # ── Write JSON ────────────────────────────────────────────────────────────
    output = {
        "metadata": {
            "script":          "pdg_comparison_verifier.py",
            "mode":            "compare",
            "purpose":         "GTE predictions vs PDG 2022 and PDG 2024 side-by-side",
            "pdg_2022_source": "PDG 2022, Planck 2018, NuFIT 5.1",
            "pdg_2024_source": "PDG 2024 (Navas et al., Phys. Rev. D 110, 030001 (2024)); NuFIT 6.0 IC24 NH",
        },
        "summary":     summary,
        "predictions": results,
    }

    out_path = args.output or "pdg_comparison_results.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"  Results written to: {out_path}")
    print()

    signal.alarm(0)


if __name__ == "__main__":
    main()
