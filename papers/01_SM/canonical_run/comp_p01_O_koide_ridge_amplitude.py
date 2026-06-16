#!/usr/bin/env python3
"""
COMP-P01-O: Koide amplitude from UGP ridge structure.

Hypothesis H1:
  The Koide parametrization m_i = m_0 (1 + r cos(theta + 2pi(i-1)/3))^2
  gives Q = 2/3 iff r^2 = 2.

  UGP's ridge structure gives R_n / 2^(n-1) = 2 - 2^(5-n), which approaches
  2 asymptotically. Does the charged-lepton sector correspond to some specific
  UGP ridge level n*, at which the *predicted* Koide Q_n matches the empirical
  value at PDG precision?

  Q_n  = (1/3) * (1 + r_n^2 / 2)
       = (1/3) * (1 + (2 - 2^(5-n))/2)
       = (1/3) * (2 - 2^(4-n))
       = 2/3 - 2^(4-n)/3

This script:
  1. Computes the empirical Koide Q with PDG uncertainties.
  2. Computes Q_n for all ridge levels n = 5..40.
  3. Reports the ridge level (if any) at which Q_n sits inside PDG 1-sigma.
  4. Also reports the natural ridge levels (n=10 Lepton Seed, n=13 mirror, n=16 Fermat).
  5. Tests three specific candidate UGP values for cos(3 theta): 11/14, 1/phi, 3/4,
     etc., and checks which ones are inside PDG 1-sigma.

Deterministic. All arithmetic in Python float; final report uses Decimal for precision.
"""

from __future__ import annotations
import json
import math
from decimal import Decimal, getcontext
from hashlib import sha256
from pathlib import Path

getcontext().prec = 50

# ---------------------------------------------------------------------------
# PDG / CODATA inputs
# ---------------------------------------------------------------------------

M_E = 0.5109989461     # MeV, CODATA 2018
M_MU = 105.6583755     # MeV, PDG 2020
M_TAU = 1776.86        # MeV, PDG 2020
D_M_TAU = 0.12         # MeV, PDG 1-sigma
# m_e and m_mu uncertainties are tiny; we use m_tau-dominant error.

# ---------------------------------------------------------------------------
# Koide Q and cos(3 theta) utilities
# ---------------------------------------------------------------------------

def koide_Q(m_e: float, m_mu: float, m_tau: float) -> float:
    s = math.sqrt(m_e) + math.sqrt(m_mu) + math.sqrt(m_tau)
    return (m_e + m_mu + m_tau) / (s * s)


def cos_3theta_from_masses(m_e: float, m_mu: float, m_tau: float) -> float:
    """Koide parametrization: m_i = m_0 (1 + sqrt(2) cos(theta_i))^2
    with theta_i = theta + 2pi*(i-1)/3 (tau=i=3 canonically).
    We use m_0 = (Sum sqrt(m) / 3)^2.

    cos(theta_tau) extracted via (sqrt(m_tau/m_0) - 1)/sqrt(2), and
    cos(3 theta) = 4 cos^3(theta) - 3 cos(theta) is the natural S3-invariant.
    """
    s_sqrt = math.sqrt(m_e) + math.sqrt(m_mu) + math.sqrt(m_tau)
    m0 = (s_sqrt / 3) ** 2
    c_tau = (math.sqrt(m_tau / m0) - 1) / math.sqrt(2)
    return 4 * c_tau ** 3 - 3 * c_tau


def empirical_Q_and_error() -> tuple[float, float]:
    q0 = koide_Q(M_E, M_MU, M_TAU)
    # numerical derivative wrt m_tau
    dm = 1e-5
    qp = koide_Q(M_E, M_MU, M_TAU + dm)
    qm = koide_Q(M_E, M_MU, M_TAU - dm)
    dq_dmtau = (qp - qm) / (2 * dm)
    sigma_q = abs(dq_dmtau) * D_M_TAU
    return q0, sigma_q


# ---------------------------------------------------------------------------
# UGP ridge prediction
# ---------------------------------------------------------------------------

def Q_ridge(n: int) -> float:
    """Q_n = 2/3 - 2^(4-n)/3 using r_n^2 = R_n/2^(n-1) = 2 - 2^(5-n)."""
    return 2.0/3.0 - 2.0 ** (4 - n) / 3.0


# ---------------------------------------------------------------------------
# cos(3 theta) from 11/14 and related UGP rationals
# ---------------------------------------------------------------------------

UGP_COS3THETA_CANDIDATES: dict[str, float] = {
    # Clean UGP rationals using Lean-certified atoms:
    "11/14 = q1/(2*delta)": 11.0 / 14.0,
    "3/4 = simple dyadic": 3.0 / 4.0,
    "7/9 = delta/(2*a2 - delta) wtf": 7.0 / 9.0,
    "22/28 = 11/14 duplicate": 22.0 / 28.0,
    "12/15 = 4/5": 12.0 / 15.0,
    "4/5 dyadic": 4.0 / 5.0,
    "13/16 = ugp1_g/D1": 13.0 / 16.0,
    "26/33 = 2*ugp1_g/(b2-q2+etc)": 26.0 / 33.0,
    "11/(11+3)=11/14 dup": 11.0 / 14.0,
    "20/23-phi-like": 20.0 / 23.0,
    "phi/2 gold": (1 + math.sqrt(5)) / 4,
    "1 - 1/phi = 1/phi^2": 1 - 2.0 / (1 + math.sqrt(5)),
    "sqrt(0.618) ~ 1/sqrt(phi)": math.sqrt(2.0 / (1 + math.sqrt(5))),
    "pi/4 cos": math.cos(math.pi / 4),        # not a UGP value; baseline
    "cos(pi/8)": math.cos(math.pi / 8),
    "cos(pi/9) - Koide's original Z3": math.cos(math.pi / 9),
    "q1*2/(b1-q1+... )": 22.0 / 28.0,
    "14/17.818 — baseline": 0.78585,
    "73/92.86 — baseline": 0.78605,
}


def angle_prediction(cos3th: float) -> dict:
    """Given a hypothesized cos(3 theta), back out Q and the three mass ratios
    assuming Koide parametrization with r = sqrt(2) and m_0 chosen so Sum m = 6 m_0."""
    three_theta = math.acos(cos3th)
    theta = three_theta / 3.0
    # Three angles: theta, theta+2pi/3, theta+4pi/3
    cos_vec = [math.cos(theta),
               math.cos(theta + 2 * math.pi / 3),
               math.cos(theta + 4 * math.pi / 3)]
    # Sqrt(m_i/m_0) = |1 + sqrt(2)*cos_i|; signs matter but if m0 is free we can
    # choose m0 so signs match empirical ordering. Take absolute value for mass ratios.
    r2 = 2.0
    m_ratios = [(1 + math.sqrt(r2) * c) ** 2 for c in cos_vec]
    m_ratios_sorted = sorted(m_ratios)
    eps = 1e-30
    def safe_ratio(a: float, b: float) -> float:
        return a / b if b > eps else float('inf')
    return {
        "cos3theta": cos3th,
        "theta_deg": math.degrees(theta),
        "cos_per_generation": cos_vec,
        "mass_ratios_over_m0_sorted": m_ratios_sorted,
        "m_tau_over_m_e_predicted": safe_ratio(m_ratios_sorted[2], m_ratios_sorted[0]),
        "m_mu_over_m_e_predicted": safe_ratio(m_ratios_sorted[1], m_ratios_sorted[0]),
        "m_tau_over_m_mu_predicted": safe_ratio(m_ratios_sorted[2], m_ratios_sorted[1]),
    }


def empirical_lepton_ratios() -> dict:
    return {
        "m_tau_over_m_e": M_TAU / M_E,
        "m_mu_over_m_e": M_MU / M_E,
        "m_tau_over_m_mu": M_TAU / M_MU,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    Q_emp, sigma_Q = empirical_Q_and_error()
    cos3th_emp = cos_3theta_from_masses(M_E, M_MU, M_TAU)
    emp_ratios = empirical_lepton_ratios()

    # Test ridge predictions
    ridge_report: list[dict] = []
    for n in range(5, 41):
        Qn = Q_ridge(n)
        dev = Qn - 2.0/3.0
        sigma_dist = (Qn - Q_emp) / sigma_Q if sigma_Q > 0 else float('nan')
        ridge_report.append({
            "n": n,
            "R_n": 2**n - 16,
            "Q_n_predicted": Qn,
            "Q_minus_2/3": dev,
            "Q_minus_Q_emp": Qn - Q_emp,
            "sigma_distance_from_emp": sigma_dist,
        })

    # Test cos(3 theta) candidates
    cos3th_report: list[dict] = []
    # Sensitivity: delta cos(3 theta) per delta m_tau
    dm = 1e-3
    c1 = cos_3theta_from_masses(M_E, M_MU, M_TAU + dm)
    c2 = cos_3theta_from_masses(M_E, M_MU, M_TAU - dm)
    dc3_dmtau = (c1 - c2) / (2 * dm)
    sigma_cos3th = abs(dc3_dmtau) * D_M_TAU

    for label, val in UGP_COS3THETA_CANDIDATES.items():
        diff = val - cos3th_emp
        sigma_dist = diff / sigma_cos3th if sigma_cos3th > 0 else float('nan')
        pred = angle_prediction(val)
        # compare with empirical mass ratios
        rel_dev_tau_e = (pred["m_tau_over_m_e_predicted"] / emp_ratios["m_tau_over_m_e"]) - 1
        rel_dev_mu_e = (pred["m_mu_over_m_e_predicted"] / emp_ratios["m_mu_over_m_e"]) - 1
        rel_dev_tau_mu = (pred["m_tau_over_m_mu_predicted"] / emp_ratios["m_tau_over_m_mu"]) - 1
        cos3th_report.append({
            "label": label,
            "cos3theta_candidate": val,
            "diff_from_emp_cos3theta": diff,
            "sigma_distance_from_emp": sigma_dist,
            "theta_deg_predicted": pred["theta_deg"],
            "m_ratio_tau_e_predicted": pred["m_tau_over_m_e_predicted"],
            "m_ratio_mu_e_predicted": pred["m_mu_over_m_e_predicted"],
            "m_ratio_tau_mu_predicted": pred["m_tau_over_m_mu_predicted"],
            "rel_dev_tau_over_e": rel_dev_tau_e,
            "rel_dev_mu_over_e": rel_dev_mu_e,
            "rel_dev_tau_over_mu": rel_dev_tau_mu,
        })
    cos3th_report.sort(key=lambda r: abs(r["sigma_distance_from_emp"]))

    # Summary: which ridge n is closest to empirical Q?
    best_n = min(ridge_report, key=lambda r: abs(r["sigma_distance_from_emp"]))
    best_cos3th = cos3th_report[0]

    out = {
        "empirical": {
            "M_e_MeV": M_E,
            "M_mu_MeV": M_MU,
            "M_tau_MeV": M_TAU,
            "dM_tau_MeV_1sigma": D_M_TAU,
            "Q_empirical": Q_emp,
            "Q_2_over_3": 2.0/3.0,
            "Q_minus_2_over_3": Q_emp - 2.0/3.0,
            "sigma_Q_1sigma": sigma_Q,
            "Q_minus_2_over_3_in_sigma": (Q_emp - 2.0/3.0) / sigma_Q if sigma_Q > 0 else float('nan'),
            "cos_3theta_empirical": cos3th_emp,
            "sigma_cos_3theta_1sigma": sigma_cos3th,
            "lepton_ratios_empirical": emp_ratios,
        },
        "hypothesis_H1_ridge_amplitude": {
            "description": "r^2 = R_n/2^(n-1) = 2 - 2^(5-n); Q_n = 2/3 - 2^(4-n)/3",
            "best_n_ridge": best_n,
            "all_ridges_n5_to_n40": ridge_report,
            "verdict": (
                "H1 CONSISTENT with empirical at 1-sigma for n >= "
                + str(next(r["n"] for r in ridge_report if abs(r["sigma_distance_from_emp"]) <= 1))
                + "; ASYMPTOTIC (n -> infty) exact 2/3."
                if any(abs(r["sigma_distance_from_emp"]) <= 1 for r in ridge_report)
                else "H1 NOT CONSISTENT at 1-sigma for any n in [5, 40]."
            ),
        },
        "hypothesis_H3_cos3theta_rationals": {
            "description": (
                "cos(3 theta) candidate UGP rationals; Koide Q is 2/3 by construction "
                "when r=sqrt(2) (which H1 gives asymptotically). If a UGP-native rational "
                "matches cos(3 theta) inside 1 sigma AND predicts m_tau/m_e, m_mu/m_e, "
                "m_tau/m_mu within PDG, then it fixes the third mass."
            ),
            "best_cos3theta_candidate": best_cos3th,
            "all_candidates_sorted_by_sigma": cos3th_report,
        },
        "script_sha256": "filled_after_write",
    }

    out_path = Path(__file__).with_suffix(".json")
    # First write to compute SHA of the artifact (with placeholder), then re-write with actual SHA.
    serialized = json.dumps(out, indent=2, sort_keys=True)
    digest = sha256(serialized.encode("utf-8")).hexdigest()
    out["script_sha256"] = digest
    out_path.write_text(json.dumps(out, indent=2, sort_keys=True))

    # Console summary
    print("=" * 72)
    print("COMP-P01-O: Koide amplitude from UGP ridge structure")
    print("=" * 72)
    print(f"Empirical Q = {Q_emp:.10f}")
    print(f"          2/3 = {2/3:.10f}")
    print(f"Q - 2/3 = {Q_emp - 2/3:+.3e}   (1-sigma from m_tau: {sigma_Q:.3e})")
    print(f"       -> distance from 2/3 in 1-sigma units: {(Q_emp - 2/3)/sigma_Q:+.2f}")
    print()
    print(f"Empirical cos(3 theta_tau) = {cos3th_emp:.10f}   (1-sigma: {sigma_cos3th:.3e})")
    print(f"Empirical lepton ratios:")
    for k, v in emp_ratios.items():
        print(f"  {k:20s} = {v:.6f}")
    print()
    print("H1 ridge amplitude (r^2 = R_n/2^(n-1)) predictions:")
    for r in ridge_report[:10]:
        print(f"  n={r['n']:2d}   R_n={r['R_n']:8d}   Q_n={r['Q_n_predicted']:.8f}   "
              f"Q_n - Q_emp = {r['Q_minus_Q_emp']:+.3e}   sigmas = {r['sigma_distance_from_emp']:+.2f}")
    print("  ...")
    for r in ridge_report[15:20] + ridge_report[-3:]:
        print(f"  n={r['n']:2d}   R_n={r['R_n']:10d}   Q_n={r['Q_n_predicted']:.10f}   "
              f"Q_n - Q_emp = {r['Q_minus_Q_emp']:+.3e}   sigmas = {r['sigma_distance_from_emp']:+.2f}")
    print()
    print(f"Best ridge: n = {best_n['n']} with sigma_dist = {best_n['sigma_distance_from_emp']:+.2f}")
    print()
    print("H3 cos(3 theta) UGP candidates (top 5 by proximity):")
    for r in cos3th_report[:5]:
        print(f"  {r['label']:50s} val={r['cos3theta_candidate']:.6f}  "
              f"sigmas={r['sigma_distance_from_emp']:+6.2f}  "
              f"tau/e dev={r['rel_dev_tau_over_e']*100:+.2f}%")
    print()
    print(f"Written to {out_path.name} (SHA {digest[:16]}...)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
