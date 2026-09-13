#!/usr/bin/env python3
"""
triality_pairing_alternative_test.py

Tests all three distinct cyclic permutations of (e, mu, tau) in the Koide ladder
reconstruction, computing the torsor-invariant Koide angle for each.

The Koide ladder parametrization is:
    sqrt(m_k) = A * (1 + sqrt(2) * |z| * cos(delta - 2*pi*k/3))   k=0,1,2

For each assignment of lepton masses to positions k=0,1,2, we solve for
(A, |z|, delta) and compute:
    - raw angle delta (in radians)
    - torsor-invariant angle: min over n of |delta - n * 2*pi/3|
    - residual from UGP's koideThetaUGP = 2/9

Permutations tested:
  P0 (original): k=0<->e, k=1<->mu, k=2<->tau   [gen1<->V per rigidity theorem]
  P1 (gen3<->V): k=0<->tau, k=1<->e,  k=2<->mu  [gen3<->V alternative]
  P2             k=0<->mu,  k=1<->tau, k=2<->e

The torsor-invariant angle |delta mod 2pi/3| is by construction invariant under
cyclic relabeling k -> k+1, so all three permutations give the same angle.
This means the Koide angle 2/9 does NOT discriminate between gen1<->V and gen3<->V
at the numerical level. Discriminating the two requires additional physical input:
the field-theoretic role of the lightest generation (which sits in V by the rigidity
argument of positive_triality_theorems.py), or the kink quantum numbers.

Results written to: ../data/triality_pairing_alternative_test_results.json
"""

import json
import math
import os
import signal
import sys
import time

import numpy as np
from scipy.optimize import minimize

# ─── Wall-clock timeout ───────────────────────────────────────────────────────
TIMEOUT_SECONDS = 120

def _timeout_handler(signum, frame):
    print(f"\nTIMEOUT: wall-clock limit {TIMEOUT_SECONDS}s reached.")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

# ─── PDG masses (MeV) ─────────────────────────────────────────────────────────
# PDG 2024: electron, muon, tau charged lepton masses
M_E   = 0.51099895    # MeV
M_MU  = 105.6583755   # MeV
M_TAU = 1776.86       # MeV

# UGP's koideThetaUGP = 2/9 (radians)
KOIDE_THETA_UGP = 2.0 / 9.0

# Three cyclic permutations of (e, mu, tau) masses
PERMUTATIONS = [
    ("P0_original_gen1V",    [M_E,   M_MU,  M_TAU], "k=0<->e, k=1<->mu, k=2<->tau"),
    ("P1_gen3V_alternative", [M_TAU, M_E,   M_MU],  "k=0<->tau, k=1<->e, k=2<->mu"),
    ("P2_mu_first",          [M_MU,  M_TAU, M_E],   "k=0<->mu, k=1<->tau, k=2<->e"),
]

def koide_model(k_vals, A, z_mod, delta):
    """
    Koide parametrization: sqrt(m_k) = A*(1 + sqrt(2)*|z|*cos(delta - 2*pi*k/3)).
    Returns sqrt(m_k) for k=0,1,2.
    """
    return A * (1.0 + math.sqrt(2) * z_mod * np.cos(delta - 2.0 * np.pi * np.array(k_vals) / 3.0))

def fit_koide(masses_ordered):
    """
    Fit the Koide parametrization to the ordered masses m_0, m_1, m_2.
    Returns dict with: A, z_mod, delta, raw_angle, torsor_invariant_angle,
                        koide_Q, residual_from_2_9.
    """
    sqrt_m = np.sqrt(masses_ordered)
    A = np.mean(sqrt_m)
    omega = np.exp(2j * np.pi / 3.0)
    v = sqrt_m / A - 1.0
    z_complex = (2.0/3.0) * sum(v[k] * (omega**k) for k in range(3))

    def residual(params):
        A_, z_, delta_ = params
        if A_ <= 0 or z_ < 0 or z_ > 2:
            return 1e10
        pred = koide_model([0, 1, 2], A_, z_, delta_)
        return np.sum((pred - sqrt_m)**2)

    z_guess = np.abs(z_complex) * math.sqrt(2)
    delta_guess = np.angle(z_complex)

    best_result = None
    best_val = 1e30

    for delta0 in np.linspace(-np.pi, np.pi, 12):
        x0 = [A, max(z_guess, 0.01), delta0]
        try:
            res = minimize(residual, x0, method='Nelder-Mead',
                           options={'xatol': 1e-12, 'fatol': 1e-15, 'maxiter': 100000})
            if res.fun < best_val:
                best_val = res.fun
                best_result = res
        except Exception:
            continue

    A_fit, z_fit, delta_fit = best_result.x
    if z_fit < 0:
        z_fit = -z_fit
        delta_fit = delta_fit + np.pi
    delta_fit = (delta_fit + np.pi) % (2 * np.pi) - np.pi

    step = 2.0 * np.pi / 3.0
    residues = [delta_fit - n * step for n in range(-5, 6)]
    torsor_invariant = min(abs(r) for r in residues)

    koide_Q = np.sum(masses_ordered) / np.sum(sqrt_m)**2
    pred = koide_model([0, 1, 2], A_fit, z_fit, delta_fit)
    max_err = np.max(np.abs(pred - sqrt_m))

    return {
        "A": float(A_fit),
        "z_mod": float(z_fit),
        "delta_raw_rad": float(delta_fit),
        "torsor_invariant_angle_rad": float(torsor_invariant),
        "koide_theta_UGP": float(KOIDE_THETA_UGP),
        "residual_from_2_9": float(abs(torsor_invariant - KOIDE_THETA_UGP)),
        "koide_Q": float(koide_Q),
        "koide_Q_ideal": 2.0/3.0,
        "koide_Q_deviation": float(abs(koide_Q - 2.0/3.0)),
        "fit_max_error_sqrt_mass": float(max_err),
        "fit_residual": float(best_val),
    }

# ─── Main ─────────────────────────────────────────────────────────────────────
print("=" * 60)
print("triality_pairing_alternative_test.py — Koide triality labeling test")
print(f"PDG masses: e={M_E} MeV, mu={M_MU} MeV, tau={M_TAU} MeV")
print(f"koideThetaUGP = 2/9 = {KOIDE_THETA_UGP:.9f} rad")
print("=" * 60)

results = {}
all_torsor_angles = []

for perm_name, masses, description in PERMUTATIONS:
    print(f"\n[{perm_name}]")
    print(f"  Ordering: {description}")
    print(f"  Masses at k=(0,1,2): {masses}")

    r = fit_koide(masses)
    results[perm_name] = {
        "description": description,
        "masses_k0_k1_k2_MeV": masses,
        **r
    }
    all_torsor_angles.append(r["torsor_invariant_angle_rad"])

    print(f"  delta_raw         = {r['delta_raw_rad']:.9f} rad")
    print(f"  torsor_invariant  = {r['torsor_invariant_angle_rad']:.9f} rad")
    print(f"  2/9               = {KOIDE_THETA_UGP:.9f} rad")
    print(f"  |angle - 2/9|     = {r['residual_from_2_9']:.3e}")
    print(f"  Koide Q           = {r['koide_Q']:.7f}  (ideal 2/3 = {2/3:.7f})")
    print(f"  Fit quality (max |sqrt(m) error|) = {r['fit_max_error_sqrt_mass']:.3e}")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
for perm_name, masses, description in PERMUTATIONS:
    r = results[perm_name]
    print(f"  {perm_name[:12]}: torsor_angle = {r['torsor_invariant_angle_rad']:.9f}, "
          f"|angle-2/9| = {r['residual_from_2_9']:.3e}")

# ─── Assertions ───────────────────────────────────────────────────────────────
# All permutations should give the same torsor-invariant angle (cyclic invariance)
tol_cyclic = 1e-6
for i, (pn, _, _) in enumerate(PERMUTATIONS[1:], 1):
    diff = abs(all_torsor_angles[i] - all_torsor_angles[0])
    assert diff < tol_cyclic, (
        f"FAIL: Cyclic invariance broken: "
        f"|torsor({pn}) - torsor(P0)| = {diff:.6e} > {tol_cyclic}"
    )
print(f"\n[ASSERT] Cyclic invariance: all three permutations agree to <{tol_cyclic}: PASS")

# All three should land near 2/9 (within 1e-4 rad)
tol_koide = 1e-4
for perm_name, _, _ in PERMUTATIONS:
    r = results[perm_name]
    assert r["residual_from_2_9"] < tol_koide, (
        f"FAIL: {perm_name} torsor angle = {r['torsor_invariant_angle_rad']:.9f}, "
        f"expected near 2/9={KOIDE_THETA_UGP:.9f}, "
        f"|diff| = {r['residual_from_2_9']:.3e} > {tol_koide}"
    )
print(f"[ASSERT] All three torsor angles land within {tol_koide} rad of 2/9: PASS")

# Koide Q should be close to 2/3 for original assignment
tol_Q = 1e-4
r0 = results["P0_original_gen1V"]
assert r0["koide_Q_deviation"] < tol_Q, (
    f"FAIL: Koide Q = {r0['koide_Q']:.7f}, expected ~2/3, deviation {r0['koide_Q_deviation']:.3e}"
)
print(f"[ASSERT] Koide Q ≈ 2/3 for original assignment: PASS")

# ─── Physical interpretation ──────────────────────────────────────────────────
print("\n[PHYSICAL INTERPRETATION]")
print("""The three permutations P0, P1, P2 are the three cyclic shifts of (e, mu, tau).
Since the torsor-invariant angle |delta mod 2pi/3| is by construction invariant under
cyclic relabeling k -> k+1, all three permutations give the same angle to machine
precision. This means the Koide angle 2/9 does NOT discriminate between gen1<->V
(electron at k=0) and gen3<->V (tau at k=0) at the numerical level.

The torsor-invariant angle 2/9 is an intrinsic property of the mass ratios
(m_e, m_mu, m_tau), not of the generation labeling. The Koide angle is well-defined
on the Z3-torsor regardless of which generation is placed at which slot.

Discriminating gen1<->V from gen3<->V requires additional physical input beyond
the mass ratios: specifically, the field-theoretic role (which generation is U-fixed
= electron = lightest = sits in the V slot by the rigidity argument of
positive_triality_theorems.py), or the kink quantum numbers.
""")

# ─── Save results ─────────────────────────────────────────────────────────────
output = {
    "script": "triality_pairing_alternative_test.py",
    "pdg_masses_MeV": {"e": M_E, "mu": M_MU, "tau": M_TAU},
    "koide_theta_UGP": KOIDE_THETA_UGP,
    "permutations": results,
    "conclusion": (
        "All three cyclic permutations give the same torsor-invariant Koide angle "
        f"= {all_torsor_angles[0]:.9f} rad = 2/9 + {all_torsor_angles[0] - KOIDE_THETA_UGP:.3e}. "
        "Cyclic invariance confirmed. The Koide angle does not discriminate "
        "gen1<->V from gen3<->V; the discrimination requires field-theoretic input."
    ),
    "assertions_passed": True,
}

_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../data")
os.makedirs(_data_dir, exist_ok=True)
outfile = os.path.join(_data_dir, "triality_pairing_alternative_test_results.json")
with open(outfile, "w") as f:
    json.dump(output, f, indent=2)

print(f"\n[OUTPUT] Results saved to: {outfile}")

signal.alarm(0)
print("\ntriality_pairing_alternative_test.py COMPLETE — all assertions passed.")
