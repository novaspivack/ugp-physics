#!/usr/bin/env python3
"""
Rank 073-LOR1: Phi_MDL KG dispersion -> exact Lorentz invariance (continuum track).

Verifies numerically that the Klein-Gordon dispersion relation omega^2 = k^2 + m^2
(c = 1) yields a Lorentz-invariant Minkowski interval ds^2 = dt^2 - dx^2 - dy^2 - dz^2
under boosts along x, and records the AFCA lattice correction epsilon_0(M=7) for the
CA track bridge (Rank 073-LOR4).

No long-running loops; wall-clock cap 120 s.
"""

import json
import math
import signal
import sys
import time

TIMEOUT_SECONDS = 120


def _timeout_handler(_signum, _frame):
    print(f"\nTIMEOUT: wall-clock limit {TIMEOUT_SECONDS}s reached.")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

t0 = time.time()

# --- Constants (exact rationals where possible) ---
M_AFCA = 7
EPS0_M7 = math.pi ** 2 / (3 * M_AFCA ** 2)  # pi^2/147
EPS0_M7_ALT = 9 / 140  # N_gen^2 / (2*70) from P36 identity (numerical check only)
M_KINK_GEV = 0.29010  # GeV, from GTE (Rank 79-MASSES); used as m in natural units c=1
HBAR_C = 1.0  # natural units


def lorentz_boost_x(dt, dx, v):
    """Boost (dt, dx) along x with velocity v (|v| < 1)."""
    gamma = 1.0 / math.sqrt(1.0 - v * v)
    dt_p = gamma * (dt - v * dx)
    dx_p = gamma * (dx - v * dt)
    return dt_p, dx_p


def minkowski_interval_sq(dt, dx, dy=0.0, dz=0.0):
    return dt * dt - dx * dx - dy * dy - dz * dz


def kg_dispersion(k, m):
    """omega >= 0 branch."""
    return math.sqrt(k * k + m * m)


# --- Test 1: interval invariance under random boosts ---
rng_seed = 20260525
import random

random.seed(rng_seed)
m = M_KINK_GEV
n_trials = 500
max_interval_error = 0.0
for _ in range(n_trials):
    k = random.uniform(0.0, 5.0 * m)
    omega = kg_dispersion(k, m)
    dt, dx = omega, k  # plane wave 4-vector (omega, k, 0, 0)
    v = random.uniform(-0.95, 0.95)
    dt_p, dx_p = lorentz_boost_x(dt, dx, v)
    ds2 = minkowski_interval_sq(dt, dx)
    ds2_p = minkowski_interval_sq(dt_p, dx_p)
    err = abs(ds2 - ds2_p)
    max_interval_error = max(max_interval_error, err)

interval_invariance_pass = max_interval_error < 1e-10

# --- Test 2: dispersion covariant form omega^2 - k^2 = m^2 ---
max_dispersion_error = 0.0
for _ in range(n_trials):
    k = random.uniform(0.0, 10.0 * m)
    omega = kg_dispersion(k, m)
    residual = omega * omega - k * k - m * m
    max_dispersion_error = max(max_dispersion_error, abs(residual))

dispersion_pass = max_dispersion_error < 1e-12

# --- Test 3: group velocity v_g = k/omega < 1 ---
k_test = 0.5 * m
omega_test = kg_dispersion(k_test, m)
v_group = k_test / omega_test
v_group_pass = v_group < 1.0 - 1e-15

# --- Test 4: BPS kink gamma factor (P36 reference) ---
# T(v) = T0 * gamma, 0.026% error at v = 0.532 — record reference value only
v_bps = 0.532
gamma_bps = 1.0 / math.sqrt(1.0 - v_bps * v_bps)
T_ratio = gamma_bps  # T/T0

# --- Test 5: epsilon_0(7) lattice correction (CA track) ---
eps0_pct = 100.0 * EPS0_M7
eps0_alt_pct = 100.0 * EPS0_M7_ALT
eps0_alt_match_pct = 100.0 * abs(EPS0_M7 - EPS0_M7_ALT) / EPS0_M7

results = {
    "rank_id": "073-LOR1",
    "dispersion_relation": "omega^2 = k^2 + m^2",
    "m_kink_GeV_natural_units": m,
    "n_boost_trials": n_trials,
    "max_minkowski_interval_error": max_interval_error,
    "interval_invariance_pass": interval_invariance_pass,
    "max_dispersion_residual": max_dispersion_error,
    "dispersion_identity_pass": dispersion_pass,
    "group_velocity_at_k_half_m": v_group,
    "group_velocity_subluminal_pass": v_group_pass,
    "epsilon_0_M7": EPS0_M7,
    "epsilon_0_M7_percent": eps0_pct,
    "epsilon_0_M7_rational_form": "pi^2/(3*49) = pi^2/147",
    "epsilon_0_alt_9_over_140": EPS0_M7_ALT,
    "epsilon_0_alt_vs_pi2_147_percent_diff": eps0_alt_match_pct,
    "bps_gamma_at_v_0_532": gamma_bps,
    "wall_clock_seconds": time.time() - t0,
    "status": "PASS" if (interval_invariance_pass and dispersion_pass and v_group_pass) else "FAIL",
}

out_path = "epic073_lor1_kg_dispersion_lorentz_results.json"
with open(out_path, "w") as f:
    json.dump(results, f, indent=2)

signal.alarm(0)

print("=" * 70)
print("RANK 073-LOR1: Phi_MDL KG dispersion -> Lorentz invariance")
print("=" * 70)
print(f"  Dispersion: omega^2 = k^2 + m^2,  m = {m:.5f} (natural units)")
print(f"  Minkowski interval invariance ({n_trials} boosts): max |Δds^2| = {max_interval_error:.3e}  "
      f"{'PASS' if interval_invariance_pass else 'FAIL'}")
print(f"  Dispersion identity residual: max = {max_dispersion_error:.3e}  "
      f"{'PASS' if dispersion_pass else 'FAIL'}")
print(f"  Group velocity k/omega at k=m/2: {v_group:.6f}  {'PASS' if v_group_pass else 'FAIL'}")
print(f"  epsilon_0(7) = pi^2/147 = {EPS0_M7:.8f}  ({eps0_pct:.4f}%)")
print(f"  9/140 alternative: {EPS0_M7_ALT:.8f}  (rel diff {eps0_alt_match_pct:.4f}%)")
print(f"  Results: {out_path}")
print(f"  STATUS: {results['status']}")
