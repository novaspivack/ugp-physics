#!/usr/bin/env python3
"""
Rank 073-LOR2: Phi_MDL KG stress-energy tensor Lorentz covariance.

Verifies numerically that the Noether stress-energy tensor
  T^{mu nu} = partial^mu Phi partial^nu Phi - eta^{mu nu} L
for L = -1/2 eta^{mu nu} partial_mu Phi partial_nu Phi - V(Phi),
V(Phi) = m^2 (1 - cos(7 Phi)) / 49,
transforms as a rank-2 contravariant Lorentz tensor under boosts.

Also integrates T_{00} (covariant) for the static Z7 kink and compares to
M_kink = (8/49) m_tau = 290.10 MeV (BPS / SCC chain).

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

# --- Metric and constants (eta = diag(-1, +1, +1, +1), c = hbar = 1) ---
ETA = (-1.0, 1.0, 1.0, 1.0)
N7 = 7
M_TAU_GEV = 1.77686  # SCC bare mass m_phi = m_tau (GeV)
M_KINK_BPS_GEV = (8.0 / 49.0) * M_TAU_GEV  # 0.290101224... GeV
M_KINK_TARGET_MEV = 290.10


def eta_contract(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    return sum(ETA[i] * a[i] * b[i] for i in range(4))


def raise_index(covector: tuple[float, ...]) -> tuple[float, ...]:
    return tuple(ETA[i] * covector[i] for i in range(4))


def lower_index(vector: tuple[float, ...]) -> tuple[float, ...]:
    return tuple(ETA[i] * vector[i] for i in range(4))


def potential(phi: float, m: float) -> float:
    return (m * m / (N7 * N7)) * (1.0 - math.cos(N7 * phi))


def dpotential_dphi(phi: float, m: float) -> float:
    return (m * m / N7) * math.sin(N7 * phi)


def lagrangian(d_phi: tuple[float, ...], phi: float, m: float) -> float:
    kinetic = -0.5 * eta_contract(d_phi, d_phi)
    return kinetic - potential(phi, m)


def stress_energy_contravariant(
    d_phi: tuple[float, ...], phi: float, m: float
) -> list[list[float]]:
    """T^{mu nu} = partial^mu Phi partial^nu Phi - eta^{mu nu} L."""
    d_up = raise_index(d_phi)
    L = lagrangian(d_phi, phi, m)
    T = [[0.0] * 4 for _ in range(4)]
    for mu in range(4):
        for nu in range(4):
            T[mu][nu] = d_up[mu] * d_up[nu]
            if mu == nu:
                T[mu][nu] -= ETA[mu] * L
    return T


def stress_energy_covariant_wald(d_phi: tuple[float, ...], phi: float, m: float) -> list[list[float]]:
    """Covariant T_{mu nu} = d_mu Phi d_nu Phi + eta_{mu nu} L (GR source convention)."""
    L = lagrangian(d_phi, phi, m)
    T = [[0.0] * 4 for _ in range(4)]
    for mu in range(4):
        for nu in range(4):
            T[mu][nu] = d_phi[mu] * d_phi[nu]
            if mu == nu:
                T[mu][nu] += ETA[mu] * L
    return T


def lorentz_boost_x_matrix(v: float) -> list[list[float]]:
    """Active boost along +x: x'^mu = Lambda^mu_nu x^nu."""
    gamma = 1.0 / math.sqrt(1.0 - v * v)
    return [
        [gamma, -gamma * v, 0.0, 0.0],
        [-gamma * v, gamma, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]


def mat_vec(L: list[list[float]], x: tuple[float, ...]) -> tuple[float, ...]:
    out = [0.0] * 4
    for mu in range(4):
        out[mu] = sum(L[mu][nu] * x[nu] for nu in range(4))
    return tuple(out)


def mat_mat(A: list[list[float]], B: list[list[float]]) -> list[list[float]]:
    n = len(A)
    return [
        [sum(A[i][k] * B[k][j] for k in range(n)) for j in range(n)]
        for i in range(n)
    ]


def transform_contravariant(T: list[list[float]], Lambda: list[list[float]]) -> list[list[float]]:
    """T'^{alpha beta} = sum_{mu,nu} Lambda^alpha_mu Lambda^beta_nu T^{mu nu}."""
    out = [[0.0] * 4 for _ in range(4)]
    for alpha in range(4):
        for beta in range(4):
            s = 0.0
            for mu in range(4):
                for nu in range(4):
                    s += Lambda[alpha][mu] * T[mu][nu] * Lambda[beta][nu]
            out[alpha][beta] = s
    return out


def transform_covector(d_phi: tuple[float, ...], Lambda: list[list[float]]) -> tuple[float, ...]:
    """Covariant d_mu Phi -> d'_alpha = (Lambda^{-1})^mu_alpha d_mu; for Lorentz boost Lambda^{-1}=Lambda."""
    out = [0.0] * 4
    for alpha in range(4):
        out[alpha] = sum(Lambda[mu][alpha] * d_phi[mu] for mu in range(4))
    return tuple(out)


def transform_contravariant_vector(v: tuple[float, ...], Lambda: list[list[float]]) -> tuple[float, ...]:
    """Contravariant v^alpha -> v'^alpha = Lambda^alpha_mu v^mu."""
    out = [0.0] * 4
    for alpha in range(4):
        out[alpha] = sum(Lambda[alpha][mu] * v[mu] for mu in range(4))
    return tuple(out)


def stress_energy_from_contravariant_derivs(
    d_up: tuple[float, ...], phi: float, m: float
) -> list[list[float]]:
    L = lagrangian(lower_index(d_up), phi, m)
    T = [[0.0] * 4 for _ in range(4)]
    for mu in range(4):
        for nu in range(4):
            T[mu][nu] = d_up[mu] * d_up[nu]
            if mu == nu:
                T[mu][nu] -= ETA[mu] * L
    return T


def random_field_config(rng) -> tuple[tuple[float, ...], float]:
    """Smooth test configuration: plane wave + Gaussian envelope."""
    t, x, y, z = (rng.uniform(-1, 1) for _ in range(4))
    k = rng.uniform(0.3, 2.0)
    sigma = 0.5
    envelope = math.exp(-(x * x + y * y + z * z) / (2 * sigma * sigma))
    phi = 0.15 * envelope * math.cos(k * x - 0.8 * t)
    d0 = 0.15 * envelope * (
        -0.8 * math.sin(k * x - 0.8 * t) - (x / (sigma * sigma)) * math.cos(k * x - 0.8 * t)
    )
    d1 = 0.15 * envelope * (
        -k * math.sin(k * x - 0.8 * t) - (x / (sigma * sigma)) * math.cos(k * x - 0.8 * t)
    )
    d2 = 0.15 * envelope * (-(y / (sigma * sigma)) * math.cos(k * x - 0.8 * t))
    d3 = 0.15 * envelope * (-(z / (sigma * sigma)) * math.cos(k * x - 0.8 * t))
    return (d0, d1, d2, d3), phi


def kink_profile(x: float, m: float) -> float:
    """Static sine-Gordon kink: Phi(x) = (4/7) arctan(exp(m x))."""
    arg = max(-500.0, min(500.0, m * x))
    return (4.0 / N7) * math.atan(math.exp(arg))


def kink_derivative_x(x: float, m: float) -> float:
    """d Phi / dx for Phi = (4/7) arctan(exp(m x))."""
    arg = max(-500.0, min(500.0, m * x))
    em = math.exp(arg)
    return (4.0 * m / N7) / (em + 1.0 / em)


def integrate_kink_mass(m: float, x_max: float, n_pts: int) -> dict[str, float]:
    """Integrate energy densities for static kink along x (y,z trivial)."""
    dx = (2.0 * x_max) / n_pts
    sum_T00_cov = 0.0
    sum_hamiltonian = 0.0
    sum_T00_contrav = 0.0
    for i in range(n_pts):
        x = -x_max + (i + 0.5) * dx
        phi = kink_profile(x, m)
        d1 = kink_derivative_x(x, m)
        d_phi = (0.0, d1, 0.0, 0.0)
        T_up = stress_energy_contravariant(d_phi, phi, m)
        T_lo = stress_energy_covariant_wald(d_phi, phi, m)
        kin = 0.5 * d1 * d1
        V = potential(phi, m)
        sum_T00_cov += T_lo[0][0] * dx
        sum_hamiltonian += (kin + V) * dx
        sum_T00_contrav += T_up[0][0] * dx
    return {
        "T00_covariant_GeV": sum_T00_cov,
        "hamiltonian_density_GeV": sum_hamiltonian,
        "T00_contravariant_GeV": sum_T00_contrav,
    }


# --- Test 1: Lorentz covariance of T^{mu nu} under random boosts ---
import random

random.seed(20260525)
m = M_TAU_GEV
n_trials = 400
max_tensor_error = 0.0
max_scalar_L_error = 0.0

for _ in range(n_trials):
    d_phi, phi = random_field_config(random)
    d_up = raise_index(d_phi)
    T = stress_energy_from_contravariant_derivs(d_up, phi, m)
    L = lagrangian(d_phi, phi, m)
    v = random.uniform(-0.92, 0.92)
    Lambda = lorentz_boost_x_matrix(v)

    d_up_p = transform_contravariant_vector(d_up, Lambda)
    T_direct = stress_energy_from_contravariant_derivs(d_up_p, phi, m)

    # Tensor law: T' = Lambda T Lambda^T
    T_transformed = transform_contravariant(T, Lambda)

    for alpha in range(4):
        for beta in range(4):
            err = abs(T_direct[alpha][beta] - T_transformed[alpha][beta])
            max_tensor_error = max(max_tensor_error, err)

    # Lagrangian scalar invariance
    L_p = lagrangian(lower_index(d_up_p), phi, m)
    max_scalar_L_error = max(max_scalar_L_error, abs(L - L_p))

tensor_pass = max_tensor_error < 1e-10
L_scalar_pass = max_scalar_L_error < 1e-10

# --- Test 2: explicit T^{00}, T^{ij} for static kink at origin ---
phi0 = kink_profile(0.0, m)
d1_0 = kink_derivative_x(0.0, m)
d_phi_static = (0.0, d1_0, 0.0, 0.0)
T_static = stress_energy_contravariant(d_phi_static, phi0, m)
T00_contrav = T_static[0][0]
T11 = T_static[1][1]
T22 = T_static[2][2]
T33 = T_static[3][3]
T_lo_static = stress_energy_covariant_wald(d_phi_static, phi0, m)
T00_cov = T_lo_static[0][0]

# --- Test 3: integrated kink mass ---
mass_int = integrate_kink_mass(m, x_max=25.0 / m, n_pts=400000)
M_ham = mass_int["hamiltonian_density_GeV"]
M_cov = mass_int["T00_covariant_GeV"]
rel_err_bps = abs(M_ham - M_KINK_BPS_GEV) / M_KINK_BPS_GEV
rel_err_target = abs(M_ham * 1000.0 - M_KINK_TARGET_MEV) / M_KINK_TARGET_MEV
kink_mass_pass = rel_err_bps < 0.001  # 0.1% numerical integration tolerance

# --- Test 4: BPS closed form sanity ---
bps_analytic = 8.0 * m / 49.0

results = {
    "rank_id": "073-LOR2",
    "lagrangian": "L = -1/2 eta^{mu nu} d_mu Phi d_nu Phi - V(Phi)",
    "potential": "V(Phi) = m^2 (1 - cos(7 Phi)) / 49",
    "stress_energy_contravariant": "T^{mu nu} = d^mu Phi d^nu Phi - eta^{mu nu} L",
    "stress_energy_covariant_note": "T_{mu nu} = eta_{mu alpha} eta_{nu beta} T^{alpha beta}; T_{00} sources GR",
    "m_phi_GeV": m,
    "M_kink_BPS_GeV": M_KINK_BPS_GEV,
    "M_kink_target_MeV": M_KINK_TARGET_MEV,
    "n_lorentz_trials": n_trials,
    "max_T_tensor_transform_error": max_tensor_error,
    "tensor_covariance_pass": tensor_pass,
    "max_L_scalar_error": max_scalar_L_error,
    "L_scalar_invariance_pass": L_scalar_pass,
    "static_kink_T00_contravariant": T00_contrav,
    "static_kink_T00_covariant": T00_cov,
    "static_kink_T11": T11,
    "static_kink_T22": T22,
    "static_kink_T33": T33,
    "kink_integration": {
        **mass_int,
        "M_hamiltonian_MeV": M_ham * 1000.0,
        "M_T00_covariant_MeV": M_cov * 1000.0,
        "M_BPS_analytic_GeV": bps_analytic,
        "M_BPS_analytic_MeV": bps_analytic * 1000.0,
        "rel_error_vs_BPS": rel_err_bps,
        "rel_error_vs_290p10_MeV": rel_err_target,
        "T00_covariant_equals_hamiltonian_density_static": abs(
            T00_cov - (0.5 * d1_0 * d1_0 + potential(phi0, m))
        )
        < 1e-12,
        "T00_contravariant_equals_neg_hamiltonian_static": abs(
            T00_contrav + (0.5 * d1_0 * d1_0 + potential(phi0, m))
        )
        < 1e-12,
    },
    "kink_mass_integration_pass": kink_mass_pass,
    "analytical_covariance": "confirmed — L Lorentz scalar implies T^{mu nu} rank-2 tensor",
    "wall_clock_seconds": time.time() - t0,
    "status": "PASS"
    if (tensor_pass and L_scalar_pass and kink_mass_pass)
    else "FAIL",
}

out_path = "tmunu_lorentz_covariance_results.json"
with open(out_path, "w") as f:
    json.dump(results, f, indent=2)

signal.alarm(0)

print("=" * 70)
print("RANK 073-LOR2: Phi_MDL T^{mu nu} Lorentz covariance")
print("=" * 70)
print(f"  Tensor transform error (max): {max_tensor_error:.3e}  {'PASS' if tensor_pass else 'FAIL'}")
print(f"  L scalar invariance (max):    {max_scalar_L_error:.3e}  {'PASS' if L_scalar_pass else 'FAIL'}")
print(f"  Static kink T^00 (contrav):   {T00_contrav:.6e} GeV^4")
print(f"  Static kink T_00 (covariant): {T00_cov:.6e} GeV^4")
print(f"  Integrated M (Hamiltonian):   {M_ham * 1000:.4f} MeV  (target {M_KINK_TARGET_MEV} MeV)")
print(f"  BPS analytic:                 {bps_analytic * 1000:.4f} MeV")
print(f"  Rel error vs 290.10 MeV:      {100 * rel_err_target:.4f}%")
print(f"  Results: {out_path}")
print(f"  STATUS: {results['status']}")
