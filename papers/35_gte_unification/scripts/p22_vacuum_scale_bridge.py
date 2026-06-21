"""
169-P2B: P22 vacuum scale bridge — absolute M_Z prediction from GTE first principles.

Identifies the CA/Schwinger energy anchor E_0 and tests multiple routes from GTE
structure to absolute electroweak boson masses in GeV.

"P22" in the EPIC_073 context refers to the P22-consistent CA dynamics / Schwinger
identity chain (P33 deeper consequences, P31 Weinberg angle), NOT papers/22_ugp_dynamics
(which covers UGP atomic moves and vertex dynamics).

Primary vacuum scale (Rank 167-SWI / P31 Remark rem:schwinger_sm_identity):
  E_0 = v_H × sqrt(π/8)
with v_H = v_PSC = 246.16 GeV from P27 SRRG (grade [A−], one open axiom).

Physical chain (primary):
  v_PSC (P27) → E_0 → M_W (Schwinger + Δr) → M_Z = M_W / cos θ_W

Alternative routes tested:
  - Kink mass M_kink = 290.10 MeV (073-LOR2 / P39 SCC) via orbit ratios
  - Planck scale × GTE orbit denominators
  - SM tree-level from v_PSC without Schwinger CA unit

GTE constants (CatAL unless noted): N_gen=3, N_fam=5, c_H=13, λ=9/40,
sin²θ_W tree=3/13, two-term=384729/1664000, v_CA=2/3.

PDG 2024: M_Z=91.1876 GeV, M_W=80.3692 GeV, sin²θ_W=0.23129.
(Note: M_W=80.377 GeV and sin²θ_W=0.2312 are PDG 2022 values.)
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

# ── GTE arithmetic (CatAL) ────────────────────────────────────────────────────
N_GEN = 3
N_FAM = 5
C_H = 13
B_H = 3
V_CA = Fraction(2, 3)
LAMBDA = Fraction(N_GEN ** 2, (2 ** N_GEN) * N_FAM)  # 9/40

SIN2_TREE = Fraction(N_GEN, C_H)  # 3/13
SIN2_CORR = LAMBDA ** N_GEN / (2 * C_H)  # 729/1664000
SIN2_TWO_TERM = SIN2_TREE + SIN2_CORR  # 384729/1664000

COS2_TREE = 1 - SIN2_TREE  # 10/13
MWMZ_TREE = math.sqrt(float(COS2_TREE))  # sqrt(10/13)

# GTE fine-structure (CatA cascade; PDG α used only for comparison row)
ALPHA_GTE = 1 / 137.0
ALPHA_PDG = 1 / 137.036

# P27 SRRG structural VEV (grade [A−]; not PDG input)
V_PSC = 246.16  # GeV

# PDG 2024 reference values
M_Z_PDG = 91.1876
M_W_PDG = 80.3692   # PDG 2024 (was 80.377 = PDG 2022)
SIN2_W_PDG = 0.23129  # PDG 2024 (was 0.2312 = PDG 2022)
SIN2_ERR = 0.00004   # PDG 2024 uncertainty
V_H_PDG = 246.21965

# 073-LOR2 / P39 SCC kink mass (CatAL)
M_KINK_MEV = 290.10
M_KINK_GEV = M_KINK_MEV / 1000.0

# Planck mass (external cosmological constant of nature, not GTE-derived)
M_PLANCK_GEV = 1.220910e19

# GTE b-ladder (P01)
B_ELECTRON = 73
B_TAU = 275


def rel_err_pct(pred: float, ref: float) -> float:
    return 100.0 * (pred - ref) / ref


def route_primary_schwinger_p22(
    v_h: float,
    alpha: float,
    sin2: float,
    delta_r: float | None = None,
) -> dict[str, float]:
    """
    Primary P22/Schwinger bridge (P31, P33, P35).

    E_0 = v_H sqrt(π/8)
    M_W = E_0 × g_W × sqrt(2/π) / sqrt(1 − Δr)   [SM–Schwinger identity]
        = v_H × (g_W/2) / sqrt(1 − Δr)           [tree SM when Δr=0]
    M_Z = M_W / cos θ_W = M_W × sqrt(c_H / (c_H − N_gen))
    """
    sin2_f = float(sin2) if isinstance(sin2, Fraction) else sin2
    cos2 = 1.0 - sin2_f
    cos_w = math.sqrt(cos2)

    e0 = v_h * math.sqrt(math.pi / 8.0)
    g_w = math.sqrt(4.0 * math.pi * alpha / sin2_f)

    if delta_r is None:
        delta_r = sin2_f / math.pi  # CatAD candidate from P33

    mw_tree = v_h * g_w / 2.0
    mw_corr = mw_tree / math.sqrt(1.0 - delta_r)
    mz_tree = mw_tree / cos_w
    mz_corr = mw_corr / cos_w

    # CA-unit cross-check
    mw_ca_schwinger = math.sqrt(N_GEN * (g_w ** 2) * float(V_CA) / math.pi)
    mw_from_e0 = e0 * g_w * math.sqrt(2.0 / math.pi) / math.sqrt(1.0 - delta_r)

    # P31 alternate M_W,CA parameterization
    mw_ca_p31 = math.sqrt(4.0 * math.pi * alpha * C_H / N_GEN) / 2.0
    mw_from_e0_p31 = e0 * mw_ca_p31 / math.sqrt(1.0 - delta_r)

    return {
        "E_0_GeV": e0,
        "delta_r": delta_r,
        "M_W_tree_GeV": mw_tree,
        "M_W_corr_GeV": mw_corr,
        "M_Z_tree_GeV": mz_tree,
        "M_Z_corr_GeV": mz_corr,
        "M_W_CA_schwinger": mw_ca_schwinger,
        "M_W_from_E0_schwinger": mw_from_e0,
        "M_W_CA_P31": mw_ca_p31,
        "M_W_from_E0_P31": mw_from_e0_p31,
        "g_W": g_w,
    }


def route_kink_cascade() -> dict[str, float]:
    """Test whether M_kink × orbit ratio reaches EW scale (expected negative)."""
    ratio_tau_e = B_TAU / B_ELECTRON  # 275/73
    mw_mz_from_kink = M_KINK_GEV * ratio_tau_e
    # Orbit step count N_gen=3 as multiplier
    mz_kink_x_ngen = M_KINK_GEV * ratio_tau_e * N_GEN
    # Z7 well depth: c_H = 13
    mz_kink_x_ch = M_KINK_GEV * C_H
    # Full naive chain M_kink → EW via b-ladder^N_gen
    mz_kink_power = M_KINK_GEV * (ratio_tau_e ** N_GEN)
    return {
        "M_kink_GeV": M_KINK_GEV,
        "b_tau_over_b_e": ratio_tau_e,
        "M_kink_x_ratio_GeV": mw_mz_from_kink,
        "M_kink_x_ratio_x_Ngen_GeV": mz_kink_x_ngen,
        "M_kink_x_cH_GeV": mz_kink_x_ch,
        "M_kink_x_ratio^Ngen_GeV": mz_kink_power,
    }


def route_planck_ratio() -> dict[str, float]:
    """Test Planck × GTE orbit denominator ratios (expected negative)."""
    # Common GTE orbit denominators
    candidates = {
        "M_Pl / (2^N_gen × c_H × N_fam × |Z7|)": M_PLANCK_GEV / (8 * C_H * N_FAM * 7),
        "M_Pl / (2^16 − 1)": M_PLANCK_GEV / 65535,
        "M_Pl / (N_gen × c_H × 10^14)": M_PLANCK_GEV / (N_GEN * C_H * 1e14),
        "M_Pl × α × N_gen / c_H": M_PLANCK_GEV * ALPHA_GTE * N_GEN / C_H,
    }
    return candidates


def main() -> None:
    print("=" * 72)
    print("169-P2B: P22 Vacuum Scale Bridge — Absolute M_Z Prediction")
    print("=" * 72)

    print("\n--- P22 identification ---")
    print("  P22 (EPIC context): CA P22-consistent dynamics / Schwinger identity")
    print("  Primary papers: P33 (Schwinger mechanism), P31 (E_0 = v_H sqrt(π/8)),")
    print("                  P27 (v_PSC = 246.16 GeV), P35 (predictions table)")
    print("  NOT papers/22_ugp_dynamics (UGP atomic moves / vertex table)")

    print("\n--- Vacuum scale E_0 ---")
    e0_psc = V_PSC * math.sqrt(math.pi / 8.0)
    e0_pdg = V_H_PDG * math.sqrt(math.pi / 8.0)
    print(f"  E_0 = v_H × sqrt(π/8)")
    print(f"  v_PSC = {V_PSC} GeV (P27 SRRG, grade [A−])")
    print(f"  E_0(v_PSC) = {e0_psc:.6f} GeV")
    print(f"  E_0(v_PDG) = {e0_pdg:.6f} GeV  [comparison only]")

    # ── Route A: Primary Schwinger-P22 with v_PSC ───────────────────────────
    print("\n--- Route A: Primary P22/Schwinger (v_PSC, α_GTE=1/137) ---")
    r_a_tree = route_primary_schwinger_p22(V_PSC, ALPHA_GTE, SIN2_TREE, delta_r=0.0)
    r_a_corr = route_primary_schwinger_p22(V_PSC, ALPHA_GTE, SIN2_TREE)
    r_a_two = route_primary_schwinger_p22(V_PSC, ALPHA_GTE, SIN2_TWO_TERM)

    print(f"  sin²θ_W tree = {float(SIN2_TREE):.10f}")
    print(f"  Δr = sin²θ_W/π = {r_a_corr['delta_r']:.10f}")
    print(f"  M_W tree (Δr=0):     {r_a_tree['M_W_tree_GeV']:.4f} GeV  "
          f"({rel_err_pct(r_a_tree['M_W_tree_GeV'], M_W_PDG):+.3f}% vs PDG)")
    print(f"  M_W corrected:       {r_a_corr['M_W_corr_GeV']:.4f} GeV  "
          f"({rel_err_pct(r_a_corr['M_W_corr_GeV'], M_W_PDG):+.3f}% vs PDG)")
    print(f"  M_Z tree (Δr=0):     {r_a_tree['M_Z_tree_GeV']:.4f} GeV  "
          f"({rel_err_pct(r_a_tree['M_Z_tree_GeV'], M_Z_PDG):+.3f}% vs PDG)")
    print(f"  M_Z corrected:       {r_a_corr['M_Z_corr_GeV']:.4f} GeV  "
          f"({rel_err_pct(r_a_corr['M_Z_corr_GeV'], M_Z_PDG):+.3f}% vs PDG)")
    print(f"  M_Z (two-term sin²): {r_a_two['M_Z_corr_GeV']:.4f} GeV  "
          f"({rel_err_pct(r_a_two['M_Z_corr_GeV'], M_Z_PDG):+.3f}% vs PDG)")

    # ── Route B: Alternate Δr = (N_fam−1)/(N_fam × c_W) ─────────────────────
    c_w = 11  # EW boson staircase bottom (CatAL)
    delta_r_alt = (N_FAM - 1) / (N_FAM * c_w)
    r_b = route_primary_schwinger_p22(V_PSC, ALPHA_GTE, SIN2_TREE, delta_r=delta_r_alt)
    print("\n--- Route B: Alternate Δr = (N_fam−1)/(N_fam×c_W) = 4/55 ---")
    print(f"  M_W = {r_b['M_W_corr_GeV']:.4f} GeV  "
          f"({rel_err_pct(r_b['M_W_corr_GeV'], M_W_PDG):+.3f}% vs PDG)")
    print(f"  M_Z = {r_b['M_Z_corr_GeV']:.4f} GeV  "
          f"({rel_err_pct(r_b['M_Z_corr_GeV'], M_Z_PDG):+.3f}% vs PDG)")

    # ── Route C: Kink mass cascade (negative control) ─────────────────────────
    print("\n--- Route C: M_kink cascade (073-LOR2, negative control) ---")
    r_c = route_kink_cascade()
    for key, val in r_c.items():
        if key.startswith("M_") and val > 0.1:
            print(f"  {key}: {val:.4f} GeV  ({rel_err_pct(val, M_Z_PDG):+.1f}% vs M_Z)")

    # ── Route D: Planck ratios (negative control) ───────────────────────────
    print("\n--- Route D: Planck × GTE ratios (negative control) ---")
    for desc, val in route_planck_ratio().items():
        print(f"  {desc}: {val:.4e} GeV  ({rel_err_pct(val, M_Z_PDG):+.1f}% vs M_Z)")

    # ── M_Z = E_0 × f(sin²θ_W, N_gen, c_H) closed form ─────────────────────
    print("\n--- Closed form M_Z = E_0 × f(sin²θ_W, N_gen, c_H) ---")
    sin2_f = float(SIN2_TREE)
    cos2_f = 1.0 - sin2_f
    g_w = math.sqrt(4.0 * math.pi * ALPHA_GTE / sin2_f)
    delta_r = sin2_f / math.pi
    # M_Z = v_H × (g_W/2) × sqrt(c_H/(c_H−N_gen)) / sqrt(1−Δr)
    f_mz = (g_w / 2.0) * math.sqrt(C_H / (C_H - N_GEN)) / math.sqrt(1.0 - delta_r)
    mz_closed = e0_psc * f_mz / math.sqrt(math.pi / 8.0) * math.sqrt(math.pi / 8.0)
    # Simplify: M_Z = v_H × f_mz since E_0/v_H = sqrt(π/8) cancels in ratio form
    mz_from_v = V_PSC * f_mz
    print(f"  f = (g_W/2) × sqrt(c_H/(c_H−N_gen)) / sqrt(1−Δr)")
    print(f"  M_Z^pred = v_PSC × f = {mz_from_v:.4f} GeV")
    print(f"  PDG M_Z = {M_Z_PDG} GeV  →  error {rel_err_pct(mz_from_v, M_Z_PDG):+.3f}%")

    # ── Assumption audit ────────────────────────────────────────────────────
    print("\n--- Assumption / uncertainty audit ---")
    assumptions = [
        ("v_H = v_PSC = 246.16 GeV", "P27 SRRG [A−]; 1 open axiom psc_ew_entropy_maximization"),
        ("E_0 = v_H sqrt(π/8)", "CatAD; SM–Schwinger algebraic identity (P31)"),
        ("N_gen × v_CA = 2", "CatAL (orbit depth × glider speed)"),
        ("sin²θ_W = 3/13 tree", "CatAL (GUTStructure)"),
        ("Δr = sin²θ_W/π", "CatAD; pending first-principles CA loop derivation"),
        ("α = 1/137 (GTE cascade)", "CatA; 0.026% below PDG α"),
        ("M_kink → M_Z direct", "FAILS — wrong scale by ~10× (Route C negative)"),
        ("Planck ratio → M_Z", "FAILS — no GTE mechanism (Route D negative)"),
    ]
    for item, status in assumptions:
        print(f"  • {item}: {status}")

    # ── Cat level assessment ────────────────────────────────────────────────
    # Canonical: Schwinger–SM identity (P31 Remark rem:schwinger_sm_identity)
    # M_W = E_0 × g_W × sqrt(2/π) / sqrt(1−Δr)  ≡  v_H × (g_W/2) / sqrt(1−Δr)
    mw_canonical = r_a_corr["M_W_from_E0_schwinger"]
    mz_canonical = r_a_corr["M_Z_corr_GeV"]
    print("\n--- Canonical route: E_0 × g_W × sqrt(2/π) / sqrt(1−Δr) ---")
    print(f"  M_W^pred = {mw_canonical:.4f} GeV  "
          f"({rel_err_pct(mw_canonical, M_W_PDG):+.3f}% vs PDG; P35 ref 80.456 GeV)")
    print(f"  M_Z^pred = {mz_canonical:.4f} GeV  "
          f"({rel_err_pct(mz_canonical, M_Z_PDG):+.3f}% vs PDG)")

    print("\n--- Cat level assessment (169-P2B) ---")
    print("  Structural chain (168-EWD + E_0 identity): CatAD")
    print(f"  M_Z absolute prediction: CatAD — {rel_err_pct(mz_canonical, M_Z_PDG):+.3f}% vs PDG")
    print(f"  M_W absolute prediction: CatAD — {rel_err_pct(mw_canonical, M_W_PDG):+.3f}% vs PDG")
    print("  Unconditional CatAL blocked on: Δr first-principles derivation (CatD)")
    print("  158-EWS: APPROACHABLE — M_W/M_Z ratio CatAL; absolute scale CatAD")

    results = {
        "rank": "169-P2B",
        "p22_identification": "CA Schwinger identity chain (P33/P31), not papers/22",
        "vacuum_scale": {
            "formula": "E_0 = v_H * sqrt(pi/8)",
            "v_PSC_GeV": V_PSC,
            "E_0_GeV": e0_psc,
        },
        "primary_route_schwinger_gW": {
            "M_W_tree_GeV": r_a_tree["M_W_tree_GeV"],
            "M_W_corr_GeV": r_a_corr["M_W_corr_GeV"],
            "M_Z_tree_GeV": r_a_tree["M_Z_tree_GeV"],
            "M_Z_corr_GeV": r_a_corr["M_Z_corr_GeV"],
            "M_Z_two_term_sin2_GeV": r_a_two["M_Z_corr_GeV"],
            "M_W_corr_rel_err_pct": rel_err_pct(r_a_corr["M_W_corr_GeV"], M_W_PDG),
            "M_Z_corr_rel_err_pct": rel_err_pct(r_a_corr["M_Z_corr_GeV"], M_Z_PDG),
        },
        "canonical_prediction": {
            "M_W_GeV": mw_canonical,
            "M_Z_GeV": mz_canonical,
            "M_W_rel_err_pct": rel_err_pct(mw_canonical, M_W_PDG),
            "M_Z_rel_err_pct": rel_err_pct(mz_canonical, M_Z_PDG),
            "formula_M_W": "E_0 * g_W * sqrt(2/pi) / sqrt(1 - delta_r)",
            "formula_M_Z": "M_W / cos(theta_W) = M_W * sqrt(c_H/(c_H - N_gen))",
        },
        "alternate_delta_r_route": {
            "delta_r": delta_r_alt,
            "M_W_GeV": r_b["M_W_corr_GeV"],
            "M_Z_GeV": r_b["M_Z_corr_GeV"],
            "M_Z_rel_err_pct": rel_err_pct(r_b["M_Z_corr_GeV"], M_Z_PDG),
        },
        "negative_controls": {
            "kink_cascade": r_c,
            "planck_ratios": route_planck_ratio(),
        },
        "closed_form": {
            "M_Z_pred_GeV": mz_from_v,
            "M_Z_PDG_GeV": M_Z_PDG,
            "rel_err_pct": rel_err_pct(mz_from_v, M_Z_PDG),
        },
        "cat_level": "CatAD",
        "158_EWS_status": "APPROACHABLE",
        "blocking_items": [
            "Delta_r first-principles CA loop derivation (CatD)",
            "psc_ew_entropy_maximization axiom for full CatAL on v_PSC",
        ],
    }

    out_path = Path(__file__).resolve().parent / "p22_vacuum_scale_bridge_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved: {out_path}")
    signal.alarm(0)
    print("\n169-P2B vacuum scale bridge COMPLETE.")


if __name__ == "__main__":
    main()
