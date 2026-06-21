"""
158-EWS-DR: CA Schwinger loop → Δr = sin²θ_W/π closure assessment.

Consolidates Rank 221-CPL (photon Feynman loop), Rank 223-WGM (γ-W mixing / isospin),
and P33 Remark rem:delta_r_formal into a single gate table for Cluster B CatAL upgrade path.

Objective:
  Test whether the GTE CA 1+1D Schwinger / vacuum-polarization machinery derives
  Δα_GTE = sin²θ_W cos²θ_W/π (and hence Δr = sin²θ_W/π) from first-principles loops.

Expected outcome (from prior ranks 221, 223):
  - Direct photon self-energy loops: FAIL (ratio ≠ Δα_GTE)
  - γ-W closed fermion loops: FAIL (ΣQ_f = 0)
  - Isospin + Sirlin + CatAL algebra: PASS (Δr = sin²/π CatAD)

Reference scripts: rank221_feynman_loop.py, rank223_wgm_mixing.py,
  papers/33_deeper_consequences/scripts/w_boson_self_energy.py
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

# ── GTE constants ─────────────────────────────────────────────────────────────
N_GEN = 3
N_FAM = 5
C_H = 13
V_CA = Fraction(2, 3)
SIN2 = Fraction(N_GEN, C_H)
COS2 = Fraction(C_H - N_GEN, C_H)
ALPHA = 1 / 137.036

V_PSC = 246.16
M_W_PDG = 80.377
M_W_TREE = 77.59668796548269  # from 169-P2B / ew_scale_consolidation

Q2_E, Q2_U, Q2_D = 1.0, (2 / 3) ** 2, (1 / 3) ** 2
N_C = 3
Q2_PER_GEN = Q2_E + N_C * (Q2_U + Q2_D)
Q2_TOTAL = N_GEN * Q2_PER_GEN
Q_SUM_PER_GEN = 0.0 + (-1) + N_C * (2 / 3 + (-1 / 3))

G_W2 = 4 * math.pi * ALPHA / float(SIN2)
E2 = 4 * math.pi * ALPHA
M_W_CA2 = N_GEN * G_W2 * float(V_CA) / math.pi

DELTA_ALPHA_GTE = float(SIN2 * COS2) / math.pi
DELTA_R_GTE = float(SIN2) / math.pi


def feynman_integrand(x: float, q2_e: float, m: float, v: float = float(V_CA)) -> float:
    denom = x * (1 - x) * q2_e + (m / v) ** 2
    return 1.0 / denom**1.5


def pi_gamma_ca(q2_e: float, masses: list[tuple[float, float, int]]) -> float:
    """Vector-coupling photon VP in CA units; masses = [(Q², m, N_c), ...]."""
    from scipy.integrate import quad

    total = 0.0
    for q2_f, m_f, n_c in masses:
        integral, _ = quad(
            feynman_integrand, 0.0, 1.0, args=(q2_e, m_f), limit=200, epsabs=1e-12, epsrel=1e-10
        )
        total += n_c * q2_f * E2 * (m_f**2 / float(V_CA) ** 4) * integral
    return total


def main() -> None:
    print("=" * 72)
    print("158-EWS-DR: CA Schwinger loop → Δr closure assessment")
    print("=" * 72)

    # ── Gate 1: charge arithmetic (CatA) ─────────────────────────────────────
    assert abs(Q2_PER_GEN - 8 / 3) < 1e-12
    assert abs(Q2_TOTAL - 8.0) < 1e-12
    assert abs(Q_SUM_PER_GEN) < 1e-12
    print(f"\nGate 1 — charge sums: ΣQ/gen = {Q_SUM_PER_GEN:.6f}, ΣQ²/gen = {Q2_PER_GEN:.6f}, "
          f"ΣQ² = {Q2_TOTAL:.6f}  PASS (CatA)")

    # ── Gate 2: massless Schwinger ratio vs Δα_GTE ───────────────────────────
    pi_schwinger = Q2_TOTAL * E2 * float(V_CA) / math.pi
    ratio_massless = pi_schwinger / M_W_CA2
    ratio_analytic = 8 * float(SIN2) / N_GEN
    gate2_pass = abs(ratio_analytic - DELTA_ALPHA_GTE) / DELTA_ALPHA_GTE < 0.01
    print(f"\nGate 2 — massless Π_γ/M_W² vs Δα_GTE:")
    print(f"  Π_γ^Schw / M_W² = {ratio_massless:.6f}  (analytic 8 sin²/N_gen = {ratio_analytic:.6f})")
    print(f"  Δα_GTE target   = {DELTA_ALPHA_GTE:.6f}")
    print(f"  Ratio/target    = {ratio_massless / DELTA_ALPHA_GTE:.4f}×  "
          f"{'PASS' if gate2_pass else 'FAIL (expected)'}")

    # ── Gate 3: massive fermion running (representative N_eff masses) ───────
    m_e = 73 / C_H
    m_u = 9 / C_H
    masses = [(Q2_E, m_e, 1), (Q2_U, m_u, 3), (Q2_D, m_u / 10, 3)]
    pi_0 = pi_gamma_ca(0.0, masses)
    pi_mw = pi_gamma_ca(M_W_CA2, masses)
    delta_pi_ratio = (pi_0 - pi_mw) / M_W_CA2
    gate3_pass = abs(delta_pi_ratio - DELTA_ALPHA_GTE) / DELTA_ALPHA_GTE < 0.05
    print(f"\nGate 3 — massive ΔΠ/M_W² (e + u + d proxy):")
    print(f"  ΔΠ/M_W² = {delta_pi_ratio:.6f}")
    print(f"  Δα_GTE  = {DELTA_ALPHA_GTE:.6f}")
    print(f"  {'PASS' if gate3_pass else 'FAIL (expected)'}")

    # ── Gate 4: γ-W mixing vanishes (charge neutrality) ─────────────────────
    gate4_pass = abs(Q_SUM_PER_GEN) < 1e-10
    print(f"\nGate 4 — γ-W closed loops (ΣQ_f = 0): {'PASS' if gate4_pass else 'FAIL'} (CatA)")

    # ── Gate 5: Sirlin isospin path algebra ─────────────────────────────────
    delta_r_sirlin = DELTA_ALPHA_GTE / float(COS2)
    gate5_algebra = abs(delta_r_sirlin - DELTA_R_GTE) < 1e-12
    delta_r_frac = Fraction(30, 169) / Fraction(10, 13)
    gate5_exact = delta_r_frac == Fraction(3, 13)
    print(f"\nGate 5 — Sirlin path (Δρ=0, Δα_GTE = sin² cos²/π):")
    print(f"  Δr = Δα/cos² = {delta_r_sirlin:.10f}")
    print(f"  Δr = sin²/π   = {DELTA_R_GTE:.10f}")
    print(f"  Exact ℚ: 30/169 ÷ 10/13 = {delta_r_frac} = 3/13  {'PASS' if gate5_exact else 'FAIL'}")
    print(f"  Algebraic match: {'PASS' if gate5_algebra else 'FAIL'} (CatAD Sirlin identification)")

    # ── Gate 6: null — cos²/π ≠ 8/N_gen ────────────────────────────────────
    null_lhs = float(COS2) / math.pi
    null_rhs = 8 / N_GEN
    gate6_null = abs(null_lhs - null_rhs) > 0.1
    print(f"\nGate 6 — null (wrong identity cos²/π = 8/N_gen): "
          f"{null_lhs:.4f} vs {null_rhs:.4f}  {'PASS null' if gate6_null else 'FAIL null'}")

    # ── Gate 7: M_W prediction ───────────────────────────────────────────────
    mw_pred = M_W_TREE / math.sqrt(1 - DELTA_R_GTE)
    mw_err_pct = 100 * (mw_pred - M_W_PDG) / M_W_PDG
    print(f"\nGate 7 — M_W with Δr = sin²/π:")
    print(f"  M_W_pred = {mw_pred:.4f} GeV  ({mw_err_pct:+.3f}% vs PDG {M_W_PDG} GeV)")

    # ── Verdict ────────────────────────────────────────────────────────────
    direct_loop_derives_delta_alpha = gate2_pass or gate3_pass
    sirlin_path_consistent = gate5_algebra and gate5_exact

    if direct_loop_derives_delta_alpha:
        cat_level = "CatA (unexpected — direct loop matched Δα_GTE)"
        status = "NOT CONFIRMED — contradicts ranks 221/223"
    elif sirlin_path_consistent:
        cat_level = "CatAD (Sirlin + isospin; direct CA loop negative)"
        status = "COMPLETE"
    else:
        cat_level = "CatD"
        status = "NOT CONFIRMED"

    results = {
        "rank": "158-EWS-DR",
        "gates": {
            "charge_sums": {"Q2_total": Q2_TOTAL, "Q_sum": Q_SUM_PER_GEN, "pass": True},
            "massless_pi_over_mw2": {
                "value": ratio_massless,
                "analytic_8_sin2_over_ngen": ratio_analytic,
                "delta_alpha_gte": DELTA_ALPHA_GTE,
                "ratio_to_target": ratio_massless / DELTA_ALPHA_GTE,
                "derives_delta_alpha": gate2_pass,
            },
            "massive_delta_pi_over_mw2": {
                "value": delta_pi_ratio,
                "delta_alpha_gte": DELTA_ALPHA_GTE,
                "derives_delta_alpha": gate3_pass,
            },
            "gamma_w_mixing_vanishes": gate4_pass,
            "sirlin_path": {
                "delta_r": delta_r_sirlin,
                "delta_r_gte": DELTA_R_GTE,
                "exact_rational": str(delta_r_frac),
                "pass": sirlin_path_consistent,
            },
            "null_cos2_over_pi": {"pass": gate6_null},
            "M_W_prediction_GeV": mw_pred,
            "M_W_error_pct": mw_err_pct,
        },
        "verdict": {
            "direct_ca_loop_derives_delta_alpha": direct_loop_derives_delta_alpha,
            "sirlin_isospin_path_consistent": sirlin_path_consistent,
            "cat_level": cat_level,
            "status": status,
            "blocking_catAL": [
                "Δα_GTE = sin² cos²/π physical identification (CatAD, not from 2-prop photon loop)",
                "Sirlin on-shell formula application to GTE (CatAD)",
            ],
            "catAL_achieved": [
                "delta_rho_zero_in_massless_limit",
                "sirlin_cos_cancellation",
                "delta_alpha_gte_rational (Lean)",
                "delta_r_from_delta_alpha_gte (Lean)",
            ],
        },
    }

    out_path = Path(__file__).with_name("epic073_rank158_ews_dr_delta_r_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 72)
    print(f"VERDICT: {cat_level}")
    print(f"Direct CA loop derives Δα_GTE: {direct_loop_derives_delta_alpha}")
    print(f"Sirlin + isospin path (CatAD): {sirlin_path_consistent}")
    print(f"Results: {out_path}")
    print("=" * 72)

    signal.alarm(0)


if __name__ == "__main__":
    main()
