#!/usr/bin/env python3
"""
EPIC_075 Rank 075-TMUNU: Complete stress-energy tensor for the Phi_MDL Z7 sine-Gordon field.

Computes all 10 independent components of T_{mu nu} for:
  L = 1/2 (d_mu Phi)^2 - V(Phi)   [+--- metric signature]
  V(Phi) = m^2 (1 - cos(7 Phi)) / 49

Tasks:
  1. Full analytic components derived symbolically and verified numerically
  2. Static kink T_{mu nu}: T_{00}, T_{0i}=0, T_{11}=0 (BPS), T_{22}=T_{33}=-V
  3. Moving kink T_{0i} (momentum density) at velocity v
  4. On-shell conservation: partial_mu T^{mu nu} = 0 verified numerically along kink worldline
  5. Integrated kink mass int T_{00} dx = M_kink = 290.10 MeV
  6. Trace T = T^mu_mu and relation to kink mass

Wall-clock cap: 300 s.
"""

from __future__ import annotations

import json
import math
import signal
import sys
import time

TIMEOUT_SECONDS = 300


def _timeout_handler(_signum, _frame):
    print(f"\nTIMEOUT: wall-clock limit {TIMEOUT_SECONDS}s reached.")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

t0 = time.time()

# --------------------------------------------------------------------------
# Constants and metric (+--- signature: g_{00}=+1, g_{11}=g_{22}=g_{33}=-1)
# --------------------------------------------------------------------------
# Sign convention: L = +1/2 (d_mu Phi)^2 - V(Phi)
# where (d_mu Phi)^2 = g^{mu nu} d_mu Phi d_nu Phi = (d_t Phi)^2 - |grad Phi|^2
# T_{mu nu} = d_mu Phi d_nu Phi - g_{mu nu} L
# T_{00} = (d_t Phi)^2 - g_{00} * (1/2 * ((d_t)^2 - |grad|^2) - V)
#         = (d_t Phi)^2 - (1/2 (d_t)^2 - 1/2 |grad|^2 - V)
#         = 1/2 (d_t Phi)^2 + 1/2 |grad Phi|^2 + V   [energy density, always >= 0]

# Note on metric sign conventions:
# We use (+,-,-,-) with g_{mu nu} = diag(+1,-1,-1,-1)
# L = +1/2 (d Phi)^2 - V = +1/2 ((d_t Phi)^2 - |grad Phi|^2) - V
# T_{mu nu} = d_mu Phi d_nu Phi - g_{mu nu} L

G_DIAG = (1.0, -1.0, -1.0, -1.0)   # (+,-,-,-) signature

N7 = 7
M_TAU_GEV = 1.77686       # SCC m_phi = m_tau (GeV), Rank 79-MASSES CatA
M_KINK_BPS = (8.0 / 49.0) * M_TAU_GEV   # = 290.10 MeV (GeV units)
M_KINK_MEV_TARGET = 290.10


def potential(phi: float, m: float) -> float:
    """V = m^2 (1 - cos(7 phi)) / 49."""
    return (m * m / (N7 * N7)) * (1.0 - math.cos(N7 * phi))


def dpotential(phi: float, m: float) -> float:
    """dV/d phi = m^2 sin(7 phi) / 7."""
    return (m * m / N7) * math.sin(N7 * phi)


def lagrangian_flat(dphi: tuple[float, ...], phi: float, m: float) -> float:
    """L = +1/2 sum_mu g^{mu nu} d_mu d_nu - V. g^{mu nu} = g_{mu nu} = diag(+1,-1,-1,-1)."""
    # (d_mu Phi)^2 with (+,-,-,-): sum g^{mu nu} d_mu d_nu = d_0^2 - d_1^2 - d_2^2 - d_3^2
    kinetic = 0.5 * (dphi[0]**2 - dphi[1]**2 - dphi[2]**2 - dphi[3]**2)
    return kinetic - potential(phi, m)


def tmunu(dphi: tuple[float, ...], phi: float, m: float) -> list[list[float]]:
    """
    T_{mu nu} = d_mu Phi d_nu Phi - g_{mu nu} L
    where g_{mu nu} = diag(+1,-1,-1,-1).
    """
    L = lagrangian_flat(dphi, phi, m)
    T = [[0.0] * 4 for _ in range(4)]
    for mu in range(4):
        for nu in range(4):
            T[mu][nu] = dphi[mu] * dphi[nu]
            if mu == nu:
                T[mu][nu] -= G_DIAG[mu] * L
    return T


def tmunu_trace(T: list[list[float]]) -> float:
    """T = g^{mu nu} T_{mu nu} = sum_mu g_{mu mu}^{-1} T_{mu mu} = sum_mu g^{mu mu} T_{mu mu}."""
    return sum(G_DIAG[mu] * T[mu][mu] for mu in range(4))


# --------------------------------------------------------------------------
# Kink profile (static, 1+1D)
# --------------------------------------------------------------------------

def kink_profile(x: float, m: float) -> float:
    """Phi(x) = (4/7) arctan(exp(m x)); BPS kink connecting 0 -> 2pi/7."""
    arg = max(-500.0, min(500.0, m * x))
    return (4.0 / N7) * math.atan(math.exp(arg))


def kink_dPhi_dx(x: float, m: float) -> float:
    """d Phi / dx = (4m/7) * 1/(exp(mx) + exp(-mx)) = (2m/7) sech(mx)."""
    arg = max(-500.0, min(500.0, m * x))
    em = math.exp(arg)
    return (4.0 * m / N7) / (em + 1.0 / em)


def kink_dPhi_dt(x: float, m: float) -> float:
    """Static kink: d Phi / dt = 0."""
    return 0.0


# --------------------------------------------------------------------------
# Moving kink (Lorentz-boosted BPS kink at velocity v along x)
# --------------------------------------------------------------------------

def moving_kink(x: float, t: float, v: float, m: float) -> tuple[float, float, float]:
    """
    Returns (phi, dphi_dt, dphi_dx) for a kink boosted to velocity v along x.
    Lorentz-contracted profile: xi = gamma*(x - v*t).
    """
    gamma = 1.0 / math.sqrt(1.0 - v * v)
    xi = gamma * (x - v * t)
    phi = kink_profile(xi, m)
    dphi_dxi = kink_dPhi_dx(xi, m)
    dphi_dx = gamma * dphi_dxi
    dphi_dt = -gamma * v * dphi_dxi
    return phi, dphi_dt, dphi_dx


# --------------------------------------------------------------------------
# Task 1: Static kink T_{mu nu} at x=0 (peak of energy density)
# --------------------------------------------------------------------------

def compute_static_kink_tmunu(m: float) -> dict:
    """Full T_{mu nu} for static kink at x=0 (kink center)."""
    x = 0.0
    phi = kink_profile(x, m)
    d1 = kink_dPhi_dx(x, m)

    # d_phi = (d_t, d_x, d_y, d_z) Phi
    dphi = (0.0, d1, 0.0, 0.0)

    T = tmunu(dphi, phi, m)
    trace = tmunu_trace(T)
    L = lagrangian_flat(dphi, phi, m)
    V = potential(phi, m)
    kin = 0.5 * d1 * d1

    # BPS check: for BPS kink, d_x Phi = sqrt(2V) and T_{11} = 0
    bps_lhs = d1
    bps_rhs = math.sqrt(2.0 * V) if V > 0 else 0.0
    bps_residual = abs(bps_lhs - bps_rhs) / (bps_rhs + 1e-30)

    # T_{11} should vanish on-shell for BPS
    T11_expected = kin - V  # = 1/2 (dPhi/dx)^2 - V = V - V = 0 on BPS

    return {
        "x": x,
        "phi": phi,
        "dphi_dx": d1,
        "V": V,
        "L": L,
        "kinetic_density": kin,
        "T00": T[0][0],   # energy density = kin + V
        "T01": T[0][1],   # momentum density (= 0 static)
        "T02": T[0][2],
        "T03": T[0][3],
        "T11": T[1][1],   # longitudinal pressure (= 0 BPS)
        "T22": T[2][2],   # transverse pressure (= -V - kinetic via g_{22}=-1 term)
        "T33": T[3][3],
        "trace": trace,
        "T00_analytic_check": kin + V,
        "T11_analytic_check": kin - V,  # BPS -> 0
        "T22_analytic_check": -(kin + V),  # = -T00 [using BPS kin=V: T22=-(kin+V)]
        "bps_residual": bps_residual,
        "note_T00": "T00 = kinetic + V = energy density (always >= 0)",
        "note_T11": "T11 = kinetic - V = 0 on BPS (pressure-free)",
        "note_T22": "T22 = T33 = -(kinetic + V) = -T00 on BPS (transverse tension)",
    }


# --------------------------------------------------------------------------
# Task 2: Moving kink T_{mu nu} at x=0, t=0 for several velocities
# --------------------------------------------------------------------------

def compute_moving_kink_tmunu(v: float, m: float) -> dict:
    """T_{mu nu} for kink moving at velocity v at (x=0, t=0)."""
    phi, d0, d1 = moving_kink(0.0, 0.0, v, m)
    dphi = (d0, d1, 0.0, 0.0)
    T = tmunu(dphi, phi, m)
    gamma = 1.0 / math.sqrt(1.0 - v * v)

    # For a boosted BPS kink, the expected results:
    # T_{00} = gamma^2 * M_kink_density (Lorentz-transformed energy)
    # T_{01} = gamma^2 * v * M_kink_density (momentum flux)
    # T_{11} = gamma^2 * v^2 * M_kink_density (longitudinal stress)

    return {
        "v": v,
        "gamma": gamma,
        "phi_at_origin": phi,
        "T00": T[0][0],
        "T01": T[0][1],
        "T11": T[1][1],
        "T22": T[2][2],
        "T33": T[3][3],
        "trace": tmunu_trace(T),
        "note": f"Moving kink at v={v}: T_01 = momentum density (should be gamma^2 * v * epsilon_0)",
    }


# --------------------------------------------------------------------------
# Task 3: On-shell conservation partial_mu T^{mu nu} = 0
# Verify numerically along kink worldline using finite differences
# --------------------------------------------------------------------------

def conservation_check(m: float, v: float, x0: float, t0_val: float, dx: float, dt: float) -> dict:
    """
    Compute partial_mu T^{mu nu}(x,t) numerically using finite differences.
    For on-shell field (satisfies equation of motion), this should = 0.

    T^{mu nu} = g^{mu alpha} g^{nu beta} T_{alpha beta}
    For (+,-,-,-): T^{00} = T_{00}, T^{01} = -T_{01}, T^{11} = -T_{11}, T^{22} = -T_{22}

    partial_mu T^{mu nu} = partial_t T^{0 nu} + partial_x T^{1 nu} + ...
    """

    def get_tmunu_at(x: float, t: float) -> list[list[float]]:
        phi, d0, d1 = moving_kink(x, t, v, m)
        dphi = (d0, d1, 0.0, 0.0)
        T_lo = tmunu(dphi, phi, m)
        # Raise both indices: T^{mu nu} = g^{mu alpha} g^{nu beta} T_{alpha beta}
        T_up = [[G_DIAG[mu] * G_DIAG[nu] * T_lo[mu][nu] for nu in range(4)] for mu in range(4)]
        return T_up

    # Central difference: partial_mu T^{mu nu}(x0, t0) for nu=0,1
    T_tp = get_tmunu_at(x0, t0_val + dt)
    T_tm = get_tmunu_at(x0, t0_val - dt)
    T_xp = get_tmunu_at(x0 + dx, t0_val)
    T_xm = get_tmunu_at(x0 - dx, t0_val)

    results = {}
    for nu in range(4):
        div_t = (T_tp[0][nu] - T_tm[0][nu]) / (2.0 * dt)
        div_x = (T_xp[1][nu] - T_xm[1][nu]) / (2.0 * dx)
        # y,z terms vanish (no y,z dependence)
        divergence = div_t + div_x
        results[f"div_nu{nu}"] = divergence

    return results


# --------------------------------------------------------------------------
# Task 4: Integrate T_{00} for static and moving kinks
# --------------------------------------------------------------------------

def integrate_energy(m: float, v: float, x_max_over_m: float = 25.0, n_pts: int = 200000) -> dict:
    """Integrate T_{00} for kink at velocity v."""
    x_max = x_max_over_m / m
    dx = 2.0 * x_max / n_pts
    gamma = 1.0 / math.sqrt(1.0 - v * v) if v != 0.0 else 1.0

    sum_T00 = 0.0
    sum_T01 = 0.0
    sum_T11 = 0.0
    sum_trace = 0.0

    for i in range(n_pts):
        x = -x_max + (i + 0.5) * dx
        if v == 0.0:
            phi = kink_profile(x, m)
            d1 = kink_dPhi_dx(x, m)
            dphi = (0.0, d1, 0.0, 0.0)
        else:
            phi, d0, d1 = moving_kink(x, 0.0, v, m)
            dphi = (d0, d1, 0.0, 0.0)

        T = tmunu(dphi, phi, m)
        sum_T00 += T[0][0] * dx
        sum_T01 += T[0][1] * dx
        sum_T11 += T[1][1] * dx
        sum_trace += tmunu_trace(T) * dx

    return {
        "v": v,
        "gamma": gamma,
        "int_T00_GeV": sum_T00,
        "int_T01_GeV": sum_T01,
        "int_T11_GeV": sum_T11,
        "int_trace_GeV": sum_trace,
        "int_T00_MeV": sum_T00 * 1000.0,
        "M_BPS_GeV": M_KINK_BPS,
        "gamma_M_BPS_GeV": gamma * M_KINK_BPS,
        "rel_err_vs_gammaM": abs(sum_T00 - gamma * M_KINK_BPS) / (gamma * M_KINK_BPS),
    }


# --------------------------------------------------------------------------
# Task 5: BPS condition verification across the kink profile
# --------------------------------------------------------------------------

def bps_profile_check(m: float, n_pts: int = 1000) -> dict:
    """Verify BPS condition d_x Phi = sqrt(2V) across the kink profile."""
    x_max = 15.0 / m
    max_bps_residual = 0.0
    max_T11 = 0.0
    max_T00_T22_relation = 0.0

    for i in range(n_pts):
        x = -x_max + (2.0 * x_max * (i + 0.5)) / n_pts
        phi = kink_profile(x, m)
        d1 = kink_dPhi_dx(x, m)
        V = potential(phi, m)
        dphi = (0.0, d1, 0.0, 0.0)
        T = tmunu(dphi, phi, m)

        bps_res = abs(d1 - math.sqrt(2.0 * V)) / (math.sqrt(2.0 * V) + 1e-40)
        max_bps_residual = max(max_bps_residual, bps_res)
        max_T11 = max(max_T11, abs(T[1][1]))

        # T22 + T00 should = 0 on BPS (T22 = -(kin+V) = -T00 when kin=V)
        t22_t00_sum = abs(T[2][2] + T[0][0])
        max_T00_T22_relation = max(max_T00_T22_relation, t22_t00_sum)

    return {
        "n_pts": n_pts,
        "max_bps_residual_dxPhi_vs_sqrt2V": max_bps_residual,
        "max_T11_over_profile": max_T11,
        "bps_T11_zero_pass": max_T11 < 1e-6 * M_KINK_BPS,
        "max_T00_plus_T22_over_profile": max_T00_T22_relation,
        "T00_equals_neg_T22_pass": max_T00_T22_relation < 1e-10,
    }


# --------------------------------------------------------------------------
# Task 6: On-shell conservation check at multiple points and velocities
# --------------------------------------------------------------------------

def run_conservation_checks(m: float) -> dict:
    """Run on-shell conservation partial_mu T^{mu nu} = 0 at several kink positions."""
    results = []
    dx = 1e-5 / m
    dt = 1e-5 / m
    test_cases = [
        (0.0, 0.0, 0.0),      # static kink at center
        (0.5 / m, 0.0, 0.0),  # static kink off-center
        (0.0, 0.0, 0.3),      # moving kink at center (v=0.3)
        (0.0, 0.0, 0.7),      # moving kink at center (v=0.7)
        (1.0 / m, 0.1 / m, 0.5),  # moving kink off-center, off-zero-time
    ]

    max_div_any = 0.0
    for (x, t_val, v) in test_cases:
        divs = conservation_check(m, v, x, t_val, dx, dt)
        max_div_here = max(abs(divs[f"div_nu{nu}"]) for nu in range(4))
        max_div_any = max(max_div_any, max_div_here)
        results.append({
            "x": x * m,
            "t": t_val * m,
            "v": v,
            "divergences": divs,
            "max_abs_divergence": max_div_here,
        })

    return {
        "test_cases": results,
        "max_divergence_over_all_cases": max_div_any,
        "conservation_pass": max_div_any < 1e-4 * m**3,
        "tolerance": 1e-4 * m**3,
        "note": "Units: GeV^4; kink scale m ~ 1.77 GeV",
    }


# --------------------------------------------------------------------------
# Main computation
# --------------------------------------------------------------------------

print("=" * 72)
print("EPIC_075 Rank 075-TMUNU: Phi_MDL Complete Stress-Energy Tensor")
print("=" * 72)

m = M_TAU_GEV

# Task 1: Static kink
print("\n[Task 1] Static kink T_{mu nu} at x=0 (kink center)")
static = compute_static_kink_tmunu(m)
print(f"  T_00 = {static['T00']:.6e} GeV^2  (energy density)")
print(f"  T_01 = {static['T01']:.6e}         (momentum density, expected 0)")
print(f"  T_11 = {static['T11']:.6e} GeV^2  (longitudinal pressure, expected ~0 BPS)")
print(f"  T_22 = {static['T22']:.6e} GeV^2  (transverse pressure)")
print(f"  T_33 = {static['T33']:.6e} GeV^2  (same as T_22 by symmetry)")
print(f"  Trace T = {static['trace']:.6e} GeV^2")
print(f"  BPS residual |d_xPhi - sqrt(2V)|/sqrt(2V) = {static['bps_residual']:.3e}")

# Task 2: Moving kink at several velocities
print("\n[Task 2] Moving kink T_{mu nu} at (x=0, t=0)")
moving_results = []
for v in [0.0, 0.3, 0.5, 0.7, 0.9]:
    r = compute_moving_kink_tmunu(v, m)
    moving_results.append(r)
    print(f"  v={v:.1f}: T_00={r['T00']:.4e}  T_01={r['T01']:.4e}  T_11={r['T11']:.4e}  T_22={r['T22']:.4e}  gamma={r['gamma']:.4f}")

# Task 3: BPS profile check
print("\n[Task 3] BPS condition over full profile")
bps_check = bps_profile_check(m)
print(f"  Max BPS residual (d_xPhi vs sqrt(2V)): {bps_check['max_bps_residual_dxPhi_vs_sqrt2V']:.3e}")
print(f"  Max |T_11| over profile: {bps_check['max_T11_over_profile']:.3e} GeV^2")
print(f"  BPS T_11=0 PASS: {bps_check['bps_T11_zero_pass']}")
print(f"  Max |T_00 + T_22| over profile: {bps_check['max_T00_plus_T22_over_profile']:.3e}")
print(f"  T_00 = -T_22 PASS: {bps_check['T00_equals_neg_T22_pass']}")

# Task 4: Integrated energies
print("\n[Task 4] Integrated T_{00} (kink rest mass = 290.10 MeV)")
int_results = {}
for v in [0.0, 0.5, 0.866]:
    r = integrate_energy(m, v)
    int_results[str(v)] = r
    print(f"  v={v:.3f} (gamma={r['gamma']:.4f}): int T_00 = {r['int_T00_MeV']:.4f} MeV  (expected {r['gamma_M_BPS_GeV']*1000:.4f} MeV)  err={r['rel_err_vs_gammaM']:.2e}")

# Task 5: On-shell conservation
print("\n[Task 5] On-shell conservation partial_mu T^{mu nu} = 0")
cons = run_conservation_checks(m)
print(f"  Max divergence over all test cases: {cons['max_divergence_over_all_cases']:.3e} GeV^4")
print(f"  Tolerance: {cons['tolerance']:.3e} GeV^4")
print(f"  Conservation PASS: {cons['conservation_pass']}")
for case in cons['test_cases']:
    print(f"    (x={case['x']:.2f}/m, t={case['t']:.2f}/m, v={case['v']:.1f}): max_div = {case['max_abs_divergence']:.3e}")

# --------------------------------------------------------------------------
# Results summary
# --------------------------------------------------------------------------
all_pass = (
    static['T01'] < 1e-14
    and static['T11'] < 1e-6 * m**2
    and bps_check['bps_T11_zero_pass']
    and bps_check.get('T00_equals_neg_T22_pass', False)
    and abs(int_results['0.0']['rel_err_vs_gammaM']) < 0.001
    and cons['conservation_pass']
)

results = {
    "rank_id": "075-TMUNU",
    "epic": "EPIC_075",
    "date": "2026-05-26",
    "lagrangian": "L = 1/2 (d_mu Phi)^2 - V(Phi),  (+,-,-,-) signature",
    "potential": "V(Phi) = m^2 (1 - cos(7 Phi)) / 49",
    "tmunu_formula": {
        "covariant": "T_{mu nu} = d_mu Phi d_nu Phi - g_{mu nu} L",
        "T00": "T_{00} = 1/2(d_t Phi)^2 + 1/2|grad Phi|^2 + V(Phi)   [energy density >= 0]",
        "T0i": "T_{0i} = d_t Phi d_i Phi   [momentum density; = 0 for static kink]",
        "Tij": "T_{ij} = d_i Phi d_j Phi + delta_{ij}(1/2|grad Phi|^2 + 1/2(d_t Phi)^2 - V(Phi))*(-1)",
        "T11_BPS": "T_{11} = 1/2(d_x Phi)^2 - V(Phi) = 0 on BPS [pressure-free kink]",
        "T22_BPS": "T_{22} = T_{33} = -(T_{00}) on BPS [transverse tension]",
        "trace": "T = g^{mu nu} T_{mu nu} = (d_t Phi)^2 - |grad Phi|^2 - 4V(Phi)",
        "trace_static_kink": "T_static = (d_x Phi)^2 - 4V = 2V - 4V = -2V on BPS",
    },
    "static_kink": static,
    "bps_profile_check": bps_check,
    "moving_kink_samples": moving_results,
    "integrated_energies": int_results,
    "conservation_check": cons,
    "m_phi_GeV": m,
    "M_kink_BPS_MeV": M_KINK_BPS * 1000.0,
    "int_T00_MeV": int_results['0.0']['int_T00_MeV'],
    "rel_err_vs_290p10_MeV": abs(int_results['0.0']['int_T00_MeV'] - M_KINK_MEV_TARGET) / M_KINK_MEV_TARGET,
    "all_pass": all_pass,
    "status": "PASS" if all_pass else "FAIL",
    "wall_clock_seconds": time.time() - t0,
}

out_path = "phimdl_tmunu_full_results.json"
with open(out_path, "w") as f:
    json.dump(results, f, indent=2)

signal.alarm(0)

print(f"\n{'='*72}")
print(f"  INT T_00 dx = {int_results['0.0']['int_T00_MeV']:.4f} MeV  (target {M_KINK_MEV_TARGET} MeV)")
print(f"  Rel error: {results['rel_err_vs_290p10_MeV']*100:.4f}%")
print(f"  ALL TASKS PASS: {all_pass}")
print(f"  STATUS: {results['status']}")
print(f"  Results: {out_path}")
print(f"  Wall clock: {results['wall_clock_seconds']:.2f}s")
