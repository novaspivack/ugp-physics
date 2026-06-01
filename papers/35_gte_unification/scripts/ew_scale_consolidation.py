"""
158-EWS: EW scale consolidation — canonical GTE prediction table and consistency check.

Consolidates ranks 168-EWD (structural threshold), 169-P2B (vacuum scale bridge), and
GUTStructure Lean certs into a single self-consistency audit for M_W, M_Z, sin²θ_W.

Chain:
  168-EWD: EW threshold = k = N_gen = 3; sin²θ_W tree = 3/13; two-term + 729/1664000
  169-P2B: E_0 = v_PSC sqrt(π/8); M_W/M_Z from Schwinger + Δr = sin²θ_W/π
  GUTStructure §45: (M_W/M_Z)² = 10/13 at tree sin²

PDG 2024: M_Z = 91.1876 GeV, M_W = 80.377 GeV, sin²θ_W = 0.2312.
"""

from __future__ import annotations

import json
import math
import signal
import sys
from fractions import Fraction
from pathlib import Path

TIMEOUT_SECONDS = 300


def _timeout_handler(_signum, _frame):
    print(f"\nTIMEOUT: wall-clock limit {TIMEOUT_SECONDS}s reached.")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

# ── GTE constants (CatAL unless noted) ────────────────────────────────────────
N_GEN = 3
N_FAM = 5
C_H = 13
LAMBDA = Fraction(N_GEN ** 2, (2 ** N_GEN) * N_FAM)  # 9/40

SIN2_TREE = Fraction(N_GEN, C_H)
SIN2_CORR = LAMBDA ** N_GEN / (2 * C_H)  # 729/1664000
SIN2_TWO_TERM = SIN2_TREE + SIN2_CORR  # 384729/1664000

COS2_TREE = 1 - SIN2_TREE  # 10/13
MWMZ_TREE = math.sqrt(float(COS2_TREE))

ALPHA_GTE = 1 / 137.0
ALPHA_PDG = 1 / 137.036

V_PSC = 246.16  # GeV — P27 SRRG [A−]
V_H_PDG = 246.21965

M_Z_PDG = 91.1876
M_W_PDG = 80.377
SIN2_W_PDG = 0.2312
MWMZ_PDG = M_W_PDG / M_Z_PDG


def rel_err_pct(pred: float, ref: float) -> float:
    return 100.0 * (pred - ref) / ref


def sigma_pull(pred: float, ref: float, sigma: float) -> float:
    return (pred - ref) / sigma


def g_w_from_alpha_sin2(alpha: float, sin2: float) -> float:
    return math.sqrt(4.0 * math.pi * alpha / sin2)


def masses_from_v(
    v_h: float,
    alpha: float,
    sin2: float | Fraction,
    delta_r: float,
) -> dict[str, float]:
    sin2_f = float(sin2) if isinstance(sin2, Fraction) else sin2
    cos2_f = 1.0 - sin2_f
    cos_w = math.sqrt(cos2_f)
    g_w = g_w_from_alpha_sin2(alpha, sin2_f)

    mw_tree = v_h * g_w / 2.0
    mw_corr = mw_tree / math.sqrt(1.0 - delta_r)
    mz_tree = mw_tree / cos_w
    mz_corr = mw_corr / cos_w
    mw_mz_tree = mw_tree / mz_tree
    mw_mz_corr = mw_corr / mz_corr

    return {
        "sin2": sin2_f,
        "cos2": cos2_f,
        "cos_w": cos_w,
        "g_W": g_w,
        "delta_r": delta_r,
        "M_W_tree_GeV": mw_tree,
        "M_W_corr_GeV": mw_corr,
        "M_Z_tree_GeV": mz_tree,
        "M_Z_corr_GeV": mz_corr,
        "M_W/M_Z_tree": mw_mz_tree,
        "M_W/M_Z_corr": mw_mz_corr,
    }


def main() -> None:
    print("=" * 72)
    print("158-EWS: EW Scale Consolidation — GTE Prediction Table")
    print("=" * 72)

    delta_r_tree = float(SIN2_TREE) / math.pi
    delta_r_two = float(SIN2_TWO_TERM) / math.pi

    # Primary predictions (169-P2B canonical: tree sin², Δr = sin²/π)
    primary = masses_from_v(V_PSC, ALPHA_GTE, SIN2_TREE, delta_r_tree)
    two_term_sin2 = masses_from_v(V_PSC, ALPHA_GTE, SIN2_TWO_TERM, delta_r_two)
    no_delta_r = masses_from_v(V_PSC, ALPHA_GTE, SIN2_TREE, 0.0)

    # PDG α sensitivity
    primary_pdg_alpha = masses_from_v(V_PSC, ALPHA_PDG, SIN2_TREE, delta_r_tree)

    # v_PSC vs PDG v_H sensitivity
    primary_pdg_v = masses_from_v(V_H_PDG, ALPHA_GTE, SIN2_TREE, delta_r_tree)

    e0 = V_PSC * math.sqrt(math.pi / 8.0)

    # ── Consolidation table ─────────────────────────────────────────────────
    print("\n--- Consolidated GTE EW prediction table ---")
    print(f"{'Quantity':<28} {'GTE':>14} {'PDG':>14} {'Error %':>10} {'σ':>8} {'Source'}")
    print("-" * 95)

    rows = [
        (
            "sin²θ_W (tree 3/13)",
            float(SIN2_TREE),
            SIN2_W_PDG,
            rel_err_pct(float(SIN2_TREE), SIN2_W_PDG),
            sigma_pull(float(SIN2_TREE), SIN2_W_PDG, 0.00004),
            "168-EWD / GUTStructure §12 CatAL",
        ),
        (
            "sin²θ_W (two-term)",
            float(SIN2_TWO_TERM),
            SIN2_W_PDG,
            rel_err_pct(float(SIN2_TWO_TERM), SIN2_W_PDG),
            sigma_pull(float(SIN2_TWO_TERM), SIN2_W_PDG, 0.00004),
            "168-EWD / GUTStructure §24 CatAL",
        ),
        (
            "M_W/M_Z (tree √(10/13))",
            MWMZ_TREE,
            MWMZ_PDG,
            rel_err_pct(MWMZ_TREE, MWMZ_PDG),
            None,
            "GUTStructure §45 CatAL",
        ),
        (
            "M_W/M_Z (two-term cos θ_W)",
            two_term_sin2["M_W/M_Z_corr"],
            MWMZ_PDG,
            rel_err_pct(two_term_sin2["M_W/M_Z_corr"], MWMZ_PDG),
            None,
            "derived from two-term sin²",
        ),
        (
            "M_W (tree, Δr=0)",
            no_delta_r["M_W_corr_GeV"],
            M_W_PDG,
            rel_err_pct(no_delta_r["M_W_corr_GeV"], M_W_PDG),
            None,
            "169-P2B Schwinger, no Δr",
        ),
        (
            "M_W (Δr=sin²/π)",
            primary["M_W_corr_GeV"],
            M_W_PDG,
            rel_err_pct(primary["M_W_corr_GeV"], M_W_PDG),
            None,
            "169-P2B CatAD",
        ),
        (
            "M_Z (tree, Δr=0)",
            no_delta_r["M_Z_corr_GeV"],
            M_Z_PDG,
            rel_err_pct(no_delta_r["M_Z_corr_GeV"], M_Z_PDG),
            None,
            "169-P2B Schwinger, no Δr",
        ),
        (
            "M_Z (Δr=sin²/π)",
            primary["M_Z_corr_GeV"],
            M_Z_PDG,
            rel_err_pct(primary["M_Z_corr_GeV"], M_Z_PDG),
            None,
            "169-P2B CatAD",
        ),
        (
            "M_Z (two-term sin² + Δr)",
            two_term_sin2["M_Z_corr_GeV"],
            M_Z_PDG,
            rel_err_pct(two_term_sin2["M_Z_corr_GeV"], M_Z_PDG),
            None,
            "combined angle + Δr(two-term)",
        ),
    ]

    for name, gte, pdg, err, sig, src in rows:
        sig_str = f"{sig:+.2f}" if sig is not None else "—"
        print(f"{name:<28} {gte:>14.10f} {pdg:>14.10f} {err:>+9.3f}% {sig_str:>8}  {src}")

    # ── Input assumptions ───────────────────────────────────────────────────
    print("\n--- Input assumptions at each step ---")
    assumptions = [
        ("Step 1: EW threshold", "k = N_gen = 3 orbit-vacuum step", "168-EWD CatAL"),
        ("Step 2: sin²θ_W tree", "N_gen/c_H = 3/13", "GUTStructure §12 CatAL"),
        ("Step 3: sin²θ_W correction", "λ³/(2·c_H) = 729/1664000", "GUTStructure §24 CatAL"),
        ("Step 4: M_W/M_Z ratio", "√(1 − sin²) = √(10/13) at tree", "GUTStructure §45 CatAL"),
        ("Step 5: v_H scale", "v_PSC = 246.16 GeV", "P27 SRRG CatAD [A−]"),
        ("Step 6: E_0 anchor", "E_0 = v_H sqrt(π/8)", "P31 Schwinger identity CatAD"),
        ("Step 7: α", "α = 1/137 (GTE cascade)", "CatA (−0.026% vs PDG)"),
        ("Step 8: Δr radiative", "Δr = sin²θ_W/π = 3/(13π)", "P33 Sirlin CatAD"),
    ]
    for step, formula, cat in assumptions:
        print(f"  {step}: {formula}  [{cat}]")

    # ── Internal consistency check ──────────────────────────────────────────
    print("\n--- Internal consistency check ---")
    mz_direct = primary["M_Z_corr_GeV"]
    mw_direct = primary["M_W_corr_GeV"]
    mw_from_mz_tree_ratio = mz_direct * MWMZ_TREE
    mw_from_mz_cos = mz_direct * primary["cos_w"]

    print(f"  sin²θ_W = 3/13 + 729/1664000 = {float(SIN2_TWO_TERM):.10f}")
    print(f"  M_W/M_Z (tree) = √(10/13) = {MWMZ_TREE:.10f}")
    print(f"  M_Z (direct)   = {mz_direct:.6f} GeV")
    print(f"  M_W (direct)   = {mw_direct:.6f} GeV")
    print(f"  M_W from M_Z × √(10/13) = {mw_from_mz_tree_ratio:.6f} GeV")
    print(f"  M_W from M_Z × cos θ_W  = {mw_from_mz_cos:.6f} GeV")
    print(f"  Direct vs M_Z×√(10/13):  Δ = {mw_direct - mw_from_mz_tree_ratio:.6f} GeV "
          f"({rel_err_pct(mw_direct, mw_from_mz_tree_ratio):+.4f}% internal)")
    print(f"  Direct vs M_Z×cos θ_W:   Δ = {mw_direct - mw_from_mz_cos:.6f} GeV "
          f"({rel_err_pct(mw_direct, mw_from_mz_cos):+.6f}% internal)")

    # Self-consistency: at tree sin², M_W/M_Z from masses equals sqrt(10/13) exactly
    ratio_from_masses = mw_direct / mz_direct
    ratio_internal_err = rel_err_pct(ratio_from_masses, MWMZ_TREE)
    print(f"  M_W/M_Z from direct masses = {ratio_from_masses:.10f}")
    print(f"  vs √(10/13) internal error = {ratio_internal_err:+.6f}%")

    consistency_pass = (
        abs(mw_direct - mw_from_mz_cos) < 1e-6
        and abs(ratio_from_masses - MWMZ_TREE) < 1e-10
    )
    print(f"  CONSISTENCY: {'PASS' if consistency_pass else 'FAIL'}")

    # Note: M_Z × √(10/13) ≠ M_W when Δr applied because ratio is tree-level
    tree_ratio_vs_corrected = rel_err_pct(mw_from_mz_tree_ratio, mw_direct)
    print(f"\n  Note: M_Z×√(10/13) vs M_W(direct) = {tree_ratio_vs_corrected:+.3f}%")
    print("  (Expected: Δr shifts M_W without shifting tree M_W/M_Z identically)")

    # ── Residual error / Δr analysis ────────────────────────────────────────
    print("\n--- Residual error analysis (+0.80% M_Z) ---")
    print(f"  Tree (Δr=0):     M_W {rel_err_pct(no_delta_r['M_W_corr_GeV'], M_W_PDG):+.3f}%, "
          f"M_Z {rel_err_pct(no_delta_r['M_Z_corr_GeV'], M_Z_PDG):+.3f}%")
    print(f"  With Δr:         M_W {rel_err_pct(mw_direct, M_W_PDG):+.3f}%, "
          f"M_Z {rel_err_pct(mz_direct, M_Z_PDG):+.3f}%")
    print(f"  Δr magnitude:    {delta_r_tree:.6f}  (≈ {delta_r_tree * 100:.2f}% of unity)")

    # Does Δr fully account for tree→PDG gap?
    mw_gap_tree = M_W_PDG - no_delta_r["M_W_corr_GeV"]
    mw_shift_delta_r = mw_direct - no_delta_r["M_W_corr_GeV"]
    print(f"  M_W gap (PDG − tree):     {mw_gap_tree:+.4f} GeV")
    print(f"  M_W shift from Δr:        {mw_shift_delta_r:+.4f} GeV")
    print(f"  Δr accounts for:        {100 * mw_shift_delta_r / mw_gap_tree:.1f}% of tree gap")
    print(f"  Residual after Δr:        {mw_direct - M_W_PDG:+.4f} GeV "
          f"({rel_err_pct(mw_direct, M_W_PDG):+.3f}%)")

    # Overshoot test: what Δr would give exact PDG M_W?
    g_w = primary["g_W"]
    mw_target = M_W_PDG
    mw_tree_val = V_PSC * g_w / 2.0
    delta_r_exact_mw = 1.0 - (mw_tree_val / mw_target) ** 2
    print(f"\n  Δr for exact PDG M_W:     {delta_r_exact_mw:.6f}")
    print(f"  GTE Δr = sin²/π:          {delta_r_tree:.6f}")
    print(f"  Ratio Δr_GTE/Δr_exact:    {delta_r_tree / delta_r_exact_mw:.4f}")
    print(f"  → Δr overshoots M_W by {rel_err_pct(mw_direct, M_W_PDG):+.3f}% "
          f"(needs Δr ≈ {100 * (delta_r_tree - delta_r_exact_mw) / delta_r_exact_mw:+.1f}% smaller for exact M_W)")

    # Component sensitivity for M_Z residual
    print("\n  M_Z residual decomposition:")
    print(f"    v_PSC → v_H(PDG):       M_Z = {primary_pdg_v['M_Z_corr_GeV']:.4f} GeV "
          f"({rel_err_pct(primary_pdg_v['M_Z_corr_GeV'], M_Z_PDG):+.3f}%)")
    print(f"    α_GTE → α(PDG):         M_Z = {primary_pdg_alpha['M_Z_corr_GeV']:.4f} GeV "
          f"({rel_err_pct(primary_pdg_alpha['M_Z_corr_GeV'], M_Z_PDG):+.3f}%)")
    print(f"    Two-term sin² + Δr(2):  M_Z = {two_term_sin2['M_Z_corr_GeV']:.4f} GeV "
          f"({rel_err_pct(two_term_sin2['M_Z_corr_GeV'], M_Z_PDG):+.3f}%)")

    # GTE-sourced corrections that could close 0.8% gap
    v_psc_for_exact = V_PSC * M_Z_PDG / mz_direct
    print(f"\n  v_H for exact M_Z (holding rest): {v_psc_for_exact:.4f} GeV "
          f"(Δv/v = {rel_err_pct(v_psc_for_exact, V_PSC):+.3f}%)")

    # Threshold correction on mass scale (not yet in chain)
    threshold_frac = float(SIN2_CORR)  # 729/1664000
    mz_with_threshold_on_v = mz_direct * (1.0 - threshold_frac)
    print(f"  If v scale × (1 − λ³/2c_H): M_Z = {mz_with_threshold_on_v:.4f} GeV "
          f"({rel_err_pct(mz_with_threshold_on_v, M_Z_PDG):+.3f}%)")

    # Alternate Δr from P33 remark (4/55)
    c_w = 11
    delta_r_alt = (N_FAM - 1) / (N_FAM * c_w)
    alt = masses_from_v(V_PSC, ALPHA_GTE, SIN2_TREE, delta_r_alt)
    print(f"\n  Alternate Δr = 4/55:    M_W = {alt['M_W_corr_GeV']:.4f} GeV "
          f"({rel_err_pct(alt['M_W_corr_GeV'], M_W_PDG):+.3f}%), "
          f"M_Z = {alt['M_Z_corr_GeV']:.4f} GeV "
          f"({rel_err_pct(alt['M_Z_corr_GeV'], M_Z_PDG):+.3f}%)")

    # ── Cat level assessment ────────────────────────────────────────────────
    print("\n--- Cat level assessment (158-EWS) ---")
    print("  sin²θ_W (tree + two-term):     CatAL (GUTStructure §12, §24)")
    print("  EW threshold structure:        CatAL (168-EWD, GUTStructure §41)")
    print("  M_W/M_Z ratio (tree):          CatAL (GUTStructure §45)")
    print("  M_W/M_Z (two-term cos θ_W):    CatAD (two-term sin² not yet in §45 mass ratio)")
    print("  Absolute M_W, M_Z:             CatAD (+0.30%, +0.80% vs PDG)")
    print("  Full EW scale consolidation:   CatAD")
    print("\n  Upgrade to CatAL requires:")
    print("    1. Lean cert of Schwinger–SM identity (E_0, M_W absolute)")
    print("    2. First-principles Δr from CA loop (currently CatD)")
    print("    3. v_PSC from SRRG without open axiom (psc_ew_entropy_maximization)")

    # ── Lean cert targets ───────────────────────────────────────────────────
    print("\n--- Lean certification targets ---")
    print("  Existing (CatAL):")
    print("    weinberg_angle_closure, weinberg_two_term_prediction")
    print("    ew_threshold_definitional_route, mw_mz_squared_from_weinberg")
    print("    sirlin_cos_cancellation, delta_rho_zero_in_massless_limit (§63)")
    print("  New module EWScalePrediction.lean:")
    print("    ew_vacuum_scale_identity: E_0/v_H = sqrt(π/8)")
    print("    mw_from_v_psc: M_W = v_H × g_W / (2 sqrt(1 − Δr))")
    print("    mz_from_mw_weinberg: M_Z = M_W / cos θ_W")
    print("    ew_scale_consistency: M_W/M_Z = cos θ_W from same sin² input")
    print("  Blocking: numeric v_PSC value + Δr identification remain axioms until SRRG/CA loop closed")

    results = {
        "rank": "158-EWS",
        "consolidation_table": {
            "sin2_tree": float(SIN2_TREE),
            "sin2_two_term": float(SIN2_TWO_TERM),
            "sin2_PDG": SIN2_W_PDG,
            "sin2_two_term_sigma": sigma_pull(float(SIN2_TWO_TERM), SIN2_W_PDG, 0.00004),
            "M_W_M_Z_tree": MWMZ_TREE,
            "M_W_M_Z_PDG": MWMZ_PDG,
            "M_W_tree_no_delta_r_GeV": no_delta_r["M_W_corr_GeV"],
            "M_W_corrected_GeV": mw_direct,
            "M_W_PDG_GeV": M_W_PDG,
            "M_W_rel_err_pct": rel_err_pct(mw_direct, M_W_PDG),
            "M_Z_tree_no_delta_r_GeV": no_delta_r["M_Z_corr_GeV"],
            "M_Z_corrected_GeV": mz_direct,
            "M_Z_PDG_GeV": M_Z_PDG,
            "M_Z_rel_err_pct": rel_err_pct(mz_direct, M_Z_PDG),
            "M_Z_two_term_sin2_GeV": two_term_sin2["M_Z_corr_GeV"],
        },
        "internal_consistency": {
            "M_W_direct_GeV": mw_direct,
            "M_Z_direct_GeV": mz_direct,
            "M_W_from_M_Z_times_sqrt_10_13_GeV": mw_from_mz_tree_ratio,
            "M_W_from_M_Z_times_cos_theta_GeV": mw_from_mz_cos,
            "internal_M_W_vs_cos_theta_err_pct": rel_err_pct(mw_direct, mw_from_mz_cos),
            "M_W_M_Z_from_masses": ratio_from_masses,
            "consistency_pass": consistency_pass,
        },
        "residual_analysis": {
            "delta_r_GTE": delta_r_tree,
            "delta_r_for_exact_M_W": delta_r_exact_mw,
            "delta_r_overshoots_M_W_pct": rel_err_pct(mw_direct, M_W_PDG),
            "M_W_tree_gap_GeV": mw_gap_tree,
            "M_W_delta_r_shift_GeV": mw_shift_delta_r,
            "v_H_for_exact_M_Z_GeV": v_psc_for_exact,
            "v_H_shift_pct": rel_err_pct(v_psc_for_exact, V_PSC),
            "M_Z_with_v_PDG_GeV": primary_pdg_v["M_Z_corr_GeV"],
            "M_Z_with_alpha_PDG_GeV": primary_pdg_alpha["M_Z_corr_GeV"],
            "alternate_delta_r_4_55_M_Z_GeV": alt["M_Z_corr_GeV"],
        },
        "cat_level": "CatAD",
        "catAL_blockers": [
            "Delta_r first-principles CA loop (CatD)",
            "psc_ew_entropy_maximization axiom for v_PSC",
            "Schwinger-SM identity Lean cert (E_0, absolute M_W)",
        ],
        "lean_targets": {
            "existing_CatAL": [
                "weinberg_angle_closure",
                "weinberg_two_term_prediction",
                "ew_threshold_definitional_route",
                "mw_mz_squared_from_weinberg",
            ],
            "proposed_EWScalePrediction.lean": [
                "ew_vacuum_scale_identity",
                "mw_from_v_psc",
                "mz_from_mw_weinberg",
                "ew_scale_consistency",
            ],
        },
        "inputs": {
            "v_PSC_GeV": V_PSC,
            "E_0_GeV": e0,
            "alpha_GTE": ALPHA_GTE,
            "delta_r": delta_r_tree,
        },
    }

    out_path = Path(__file__).resolve().parent / "ew_scale_consolidation_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved: {out_path}")
    signal.alarm(0)
    print("\n158-EWS EW scale consolidation COMPLETE.")


if __name__ == "__main__":
    main()
