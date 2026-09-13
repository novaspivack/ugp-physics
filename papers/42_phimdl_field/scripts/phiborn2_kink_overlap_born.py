#!/usr/bin/env python3
"""
Kink wavefunction -> Born probability from Phi_MDL field overlap.

Computes position-space overlap integrals between shifted Z7-KG kink profiles and
an MDL superposition field configuration:

  phi_k(x) = phi_0(x - x_k)   (k-th kink, vacuum k-1 -> vacuum k)
  phi_MDL(x) = sum_k c_k phi_k(x)

Born weights from overlap:
  P(k) = |integral phi_k*(x) phi_MDL(x) dx|^2 / sum_j |integral phi_j*(x) phi_MDL(x) dx|^2

Tests:
  1. Gram matrix orthogonality of shifted kinks under L2(phi) and L2(dphi/dx)
  2. Overlap Born weights vs Fock sector P(k) = |c_k|^2
  3. Normalization sum_k P(k) = 1
  4. Consistency with 074-PHIBORN1: sector integral of P(x) = |d phi_MDL/dx|^2 / norm

Prerequisite: 074-PHIBORN1 established P(x) = |d phi/dx|^2 / integral|d phi/dx|^2 for single kink.

Wall-clock cap: 300 s.
"""

from __future__ import annotations

import json
import math
import random
import signal
import sys
import time
from pathlib import Path

TIMEOUT_SECONDS = 300


def _timeout_handler(_signum, _frame):
    print(f"\nTIMEOUT: wall-clock limit {TIMEOUT_SECONDS}s reached.")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

t0 = time.time()

N7 = 7
M_TAU_MEV = 1776.86
M_TAU_GEV = M_TAU_MEV / 1000.0
M_KINK_BPS_GEV = (8.0 / 49.0) * M_TAU_GEV
TWO_PI_OVER_7 = 2.0 * math.pi / N7


def kink_profile(x: float, m: float) -> float:
    """Static Z7-KG kink: phi(x) = (4/7) arctan(exp(m x))."""
    arg = max(-500.0, min(500.0, m * x))
    return (4.0 / N7) * math.atan(math.exp(arg))


def kink_derivative(x: float, m: float) -> float:
    """d phi / dx for the BPS kink profile."""
    arg = max(-500.0, min(500.0, m * x))
    em = math.exp(arg)
    return (4.0 * m / N7) / (em + 1.0 / em)


def integrate_midpoint(fn, x_min: float, x_max: float, n_pts: int) -> float:
    dx = (x_max - x_min) / n_pts
    total = 0.0
    for i in range(n_pts):
        x = x_min + (i + 0.5) * dx
        total += fn(x) * dx
    return total


def shifted_profile(x: float, m: float, x_k: float) -> float:
    return kink_profile(x - x_k, m)


def shifted_derivative(x: float, m: float, x_k: float) -> float:
    return kink_derivative(x - x_k, m)


def gram_matrix(
    positions: list[float],
    m: float,
    use_derivative: bool,
    x_min: float,
    x_max: float,
    n_pts: int,
) -> tuple[list[list[float]], list[float]]:
    """Compute G_jk = integral phi_j phi_k and norms ||phi_j||."""
    n = len(positions)
    raw = [[0.0] * n for _ in range(n)]
    for j in range(n):
        for k in range(j, n):
            if use_derivative:
                fn = lambda x, jj=j, kk=k: shifted_derivative(x, m, positions[jj]) * shifted_derivative(
                    x, m, positions[kk]
                )
            else:
                fn = lambda x, jj=j, kk=k: shifted_profile(x, m, positions[jj]) * shifted_profile(
                    x, m, positions[kk]
                )
            val = integrate_midpoint(fn, x_min, x_max, n_pts)
            raw[j][k] = val
            raw[k][j] = val
    norms = [math.sqrt(raw[j][j]) for j in range(n)]
    return raw, norms


def normalized_gram(raw: list[list[float]], norms: list[float], norm_floor: float = 1e-30) -> list[list[float]]:
    n = len(norms)
    out = [[0.0] * n for _ in range(n)]
    for j in range(n):
        for k in range(n):
            denom = norms[j] * norms[k]
            if denom > norm_floor:
                out[j][k] = raw[j][k] / denom
    return out


def mdl_field(x: float, m: float, positions: list[float], coeffs: list[complex]) -> float:
    """Real scalar MDL configuration: Re(sum_k c_k phi_k)."""
    return sum(c.real * shifted_profile(x, m, positions[k]) for k, c in enumerate(coeffs))


def mdl_derivative(x: float, m: float, positions: list[float], coeffs: list[complex]) -> float:
    """d/dx of real scalar MDL configuration."""
    return sum(c.real * shifted_derivative(x, m, positions[k]) for k, c in enumerate(coeffs))


def overlap_integrals(
    positions: list[float],
    m: float,
    coeffs: list[complex],
    use_derivative: bool,
    x_min: float,
    x_max: float,
    n_pts: int,
) -> list[complex]:
    """a_k = integral phi_k*(x) phi_MDL(x) dx."""
    n = len(positions)
    overlaps = []
    for k in range(n):
        if use_derivative:

            def integrand(x, kk=k):
                return shifted_derivative(x, m, positions[kk]) * mdl_derivative(x, m, positions, coeffs)

        else:

            def integrand(x, kk=k):
                return shifted_profile(x, m, positions[kk]) * mdl_field(x, m, positions, coeffs)

        overlaps.append(integrate_midpoint(integrand, x_min, x_max, n_pts))
    return overlaps


def born_weights_from_overlaps(overlaps: list[complex]) -> list[float]:
    sq = [abs(a) ** 2 for a in overlaps]
    total = sum(sq)
    if total <= 0:
        return [0.0] * len(overlaps)
    return [s / total for s in sq]


def random_normalized_coeffs(seed: int, n: int, real_only: bool = True) -> list[complex]:
    rng = random.Random(seed)
    if real_only:
        c = [complex(rng.gauss(0, 1), 0.0) for _ in range(n)]
    else:
        c = [complex(rng.gauss(0, 1), rng.gauss(0, 1)) for _ in range(n)]
    norm = math.sqrt(sum(abs(z) ** 2 for z in c))
    return [z / norm for z in c]


def sector_integral_grad_density(
    positions: list[float],
    m: float,
    coeffs: list[complex],
    x_min: float,
    x_max: float,
    n_pts: int,
) -> tuple[list[float], float]:
    """P(x) = |d phi_MDL/dx|^2 / integral; return sector integrals over windows around x_k."""
    dx = (x_max - x_min) / n_pts
    grad_sq = []
    xs = []
    for i in range(n_pts):
        x = x_min + (i + 0.5) * dx
        xs.append(x)
        g = mdl_derivative(x, m, positions, coeffs)
        grad_sq.append(g * g)
    norm = sum(grad_sq) * dx
    if norm <= 0:
        return [0.0] * len(positions), 0.0
    p_x = [g / norm for g in grad_sq]
    window_half = 5.0 / m
    sector_probs = []
    for x_k in positions:
        lo, hi = x_k - window_half, x_k + window_half
        s = 0.0
        for i in range(n_pts):
            x = xs[i]
            if lo <= x <= hi:
                s += p_x[i] * dx
        sector_probs.append(s)
    total_norm = sum(p_x) * dx
    return sector_probs, total_norm


def winding_sector_integral(
    positions: list[float],
    m: float,
    coeffs: list[complex],
    x_min: float,
    x_max: float,
    n_pts: int,
) -> list[float]:
    """Integrate P(x) over field-winding bins: phi in [2pi k/7, 2pi (k+1)/7)."""
    dx = (x_max - x_min) / n_pts
    grad_sq = []
    xs = []
    for i in range(n_pts):
        x = x_min + (i + 0.5) * dx
        xs.append(x)
        g = mdl_derivative(x, m, positions, coeffs)
        grad_sq.append(g * g)
    norm = sum(grad_sq) * dx
    if norm <= 0:
        return [0.0] * N7
    p_x = [g / norm for g in grad_sq]
    sector_probs = [0.0] * N7
    for i in range(n_pts):
        phi_val = mdl_field(xs[i], m, positions, coeffs)
        # Map phi to Z7 sector index (0..6)
        sector = int(phi_val / TWO_PI_OVER_7) % N7
        if sector < 0:
            sector = (sector + N7) % N7
        sector_probs[sector] += p_x[i] * dx
    return sector_probs


def max_off_diagonal(gram: list[list[float]]) -> float:
    n = len(gram)
    mx = 0.0
    for j in range(n):
        for k in range(n):
            if j != k:
                mx = max(mx, abs(gram[j][k]))
    return mx


def analytic_two_kink_dphi_overlap(delta_x: float, m: float) -> float:
    """Exact integral of (dphi/dx)(x)(dphi/dx)(x-delta) for Z7 kink; sech kernel."""
    # dphi/dx = (2m/7) sech(mx); integral sech(mx) sech(m(x-delta)) dx = (2/m) sech(m delta/2)
    coeff = (2.0 * m / N7) ** 2
    return coeff * (2.0 / m) * (1.0 / math.cosh(0.5 * m * delta_x))


def compare_vectors(a: list[float], b: list[float]) -> dict:
    n = len(a)
    l1 = sum(abs(a[i] - b[i]) for i in range(n))
    l2 = math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(n)))
    max_res = max(abs(a[i] - b[i]) for i in range(n))
    return {"l1_diff": l1, "l2_diff": l2, "max_residual": max_res}


m = M_TAU_GEV
n_pts = 300_000

# Kink positions: centered on x-axis so all seven modes fit in one integration window
separation = 20.0 / m
positions = [(k - (N7 - 1) / 2.0) * separation for k in range(N7)]
margin = 15.0 / m
x_min = positions[0] - margin
x_max = positions[-1] + margin

# Tight separation: cores overlap; still centered
positions_tight = [(k - (N7 - 1) / 2.0) * (3.0 / m) for k in range(N7)]

coeffs = random_normalized_coeffs(seed=20260525, n=N7, real_only=True)
P_fock = [abs(c) ** 2 for c in coeffs]

# --- Full-line phi^2 integral (PHIBORN1 divergence check) ---
phi_sq_wide = integrate_midpoint(lambda x: kink_profile(x, m) ** 2, -100.0 / m, 100.0 / m, 200_000)
phi_sq_core = integrate_midpoint(lambda x: kink_profile(x, m) ** 2, -10.0 / m, 10.0 / m, 200_000)

# --- Gram matrices: L2(phi) windowed vs L2(dphi/dx) ---
gram_phi, norms_phi = gram_matrix(positions, m, use_derivative=False, x_min=x_min, x_max=x_max, n_pts=n_pts)
gram_phi_norm = normalized_gram(gram_phi, norms_phi)
off_diag_phi = max_off_diagonal(gram_phi_norm)

gram_dphi, norms_dphi = gram_matrix(positions, m, use_derivative=True, x_min=x_min, x_max=x_max, n_pts=n_pts)
gram_dphi_norm = normalized_gram(gram_dphi, norms_dphi)
off_diag_dphi = max_off_diagonal(gram_dphi_norm)

# Single-kink gradient norm (PHIBORN1 cross-check)
single_grad_norm_sq = gram_dphi[0][0]
single_grad_norm_analytic = 8.0 * m / 49.0

# --- Overlap Born weights (well-separated) ---
overlap_phi = overlap_integrals(positions, m, coeffs, use_derivative=False, x_min=x_min, x_max=x_max, n_pts=n_pts)
P_overlap_phi = born_weights_from_overlaps(overlap_phi)
cmp_phi = compare_vectors(P_overlap_phi, P_fock)

overlap_dphi = overlap_integrals(positions, m, coeffs, use_derivative=True, x_min=x_min, x_max=x_max, n_pts=n_pts)
P_overlap_dphi = born_weights_from_overlaps(overlap_dphi)
cmp_dphi = compare_vectors(P_overlap_dphi, P_fock)

# --- Tight separation case ---
overlap_phi_tight = overlap_integrals(
    positions_tight, m, coeffs, use_derivative=False, x_min=x_min, x_max=x_max, n_pts=n_pts
)
P_overlap_phi_tight = born_weights_from_overlaps(overlap_phi_tight)
cmp_phi_tight = compare_vectors(P_overlap_phi_tight, P_fock)

overlap_dphi_tight = overlap_integrals(
    positions_tight, m, coeffs, use_derivative=True, x_min=x_min, x_max=x_max, n_pts=n_pts
)
P_overlap_dphi_tight = born_weights_from_overlaps(overlap_dphi_tight)
cmp_dphi_tight = compare_vectors(P_overlap_dphi_tight, P_fock)

# --- PHIBORN1 consistency: P(x) sector integrals ---
sector_window_probs, p_x_norm = sector_integral_grad_density(
    positions, m, coeffs, x_min, x_max, n_pts
)
cmp_sector_window = compare_vectors(sector_window_probs, P_fock)

sector_winding_probs = winding_sector_integral(positions, m, coeffs, x_min, x_max, n_pts)
cmp_sector_winding = compare_vectors(sector_winding_probs, P_fock)

# --- Normalization checks ---
sum_P_phi = sum(P_overlap_phi)
sum_P_dphi = sum(P_overlap_dphi)
sum_P_fock = sum(P_fock)

# --- Orthogonality thresholds ---
ORTH_EPS = 0.01
phi_orthogonal = off_diag_phi < ORTH_EPS
dphi_orthogonal = off_diag_dphi < ORTH_EPS

# Analytic cross-check: two-kink dphi overlap at separation
analytic_dphi_cross = analytic_two_kink_dphi_overlap(separation, m)
numeric_dphi_cross = gram_dphi[0][1] if N7 > 1 else 0.0
analytic_dphi_cross_norm = analytic_dphi_cross / single_grad_norm_sq if single_grad_norm_sq > 0 else 0.0
numeric_dphi_cross_norm = gram_dphi_norm[0][1] if N7 > 1 else 0.0

# --- Pass/fail logic ---
Fock_match_eps = 0.15
phi_fock_match = cmp_phi["max_residual"] < Fock_match_eps
dphi_fock_match = cmp_dphi["max_residual"] < Fock_match_eps

norm_pass_phi = abs(sum_P_phi - 1.0) < 1e-10
norm_pass_dphi = abs(sum_P_dphi - 1.0) < 1e-10

# Decision: positive if gradient overlap matches Fock AND kinks nearly orthogonal in dphi metric
positive_result = dphi_orthogonal and dphi_fock_match and norm_pass_dphi
negative_result = not positive_result

if positive_result:
    cat_level = "CatAD"
    next_rank = "074-PHIBORN3"
    status = "PASS"
elif dphi_fock_match and not dphi_orthogonal:
    cat_level = "CatA"
    next_rank = "074-PHIBORN2b"
    status = "PARTIAL — overlap Born works but kinks not orthogonal in L2(dphi); field-theoretic inner product needed"
else:
    cat_level = "CatA"
    next_rank = "074-PHIBORN2b"
    status = "PARTIAL/NEGATIVE — naïve L2(phi) overlap fails; gradient overlap or field-theoretic measure required"

results = {
    "rank_id": "074-PHIBORN2",
    "title": "Kink wavefunction Born probability from Phi_MDL field overlap",
    "prerequisite": "074-PHIBORN1",
    "field": "Z7-symmetric Klein-Gordon Phi_MDL",
    "kink_profile": "phi(x) = (4/7) arctan(exp(m_phi x))",
    "m_phi_MeV": M_TAU_MEV,
    "m_phi_GeV": m,
    "M_kink_BPS_GeV": M_KINK_BPS_GEV,
    "setup": {
        "positions_well_separated": positions,
        "separation_well": separation,
        "positions_tight": positions_tight,
        "separation_tight": 3.0 / m,
        "integration_window": [x_min, x_max],
        "n_pts": n_pts,
        "coefficients_seed": 20260525,
        "P_fock_sector": P_fock,
    },
    "phi_sq_divergence_check": {
        "integral_core": phi_sq_core,
        "integral_wide": phi_sq_wide,
        "divergent_on_R": phi_sq_wide > phi_sq_core * 1.05,
    },
    "orthogonality": {
        "L2_phi_windowed_max_off_diagonal": off_diag_phi,
        "L2_phi_orthogonal": phi_orthogonal,
        "L2_dphi_max_off_diagonal": off_diag_dphi,
        "L2_dphi_orthogonal": dphi_orthogonal,
        "single_kink_grad_norm_sq_numeric": single_grad_norm_sq,
        "single_kink_grad_norm_sq_analytic_8m_49": single_grad_norm_analytic,
        "grad_norm_rel_error": abs(single_grad_norm_sq - single_grad_norm_analytic) / single_grad_norm_analytic,
        "dphi_cross_overlap_analytic": analytic_dphi_cross,
        "dphi_cross_overlap_numeric_G01": numeric_dphi_cross,
        "dphi_cross_overlap_normalized_analytic": analytic_dphi_cross_norm,
        "dphi_cross_overlap_normalized_numeric": numeric_dphi_cross_norm,
    },
    "overlap_born_well_separated": {
        "L2_phi": {
            "overlaps": [{"re": o.real, "im": o.imag} for o in overlap_phi],
            "P_k": P_overlap_phi,
            "sum_P_k": sum_P_phi,
            "normalized": norm_pass_phi,
            "vs_fock": cmp_phi,
            "matches_fock": phi_fock_match,
        },
        "L2_dphi": {
            "overlaps": [{"re": o.real, "im": o.imag} for o in overlap_dphi],
            "P_k": P_overlap_dphi,
            "sum_P_k": sum_P_dphi,
            "normalized": norm_pass_dphi,
            "vs_fock": cmp_dphi,
            "matches_fock": dphi_fock_match,
        },
    },
    "overlap_born_tight_separation": {
        "L2_phi": {"P_k": P_overlap_phi_tight, "vs_fock": cmp_phi_tight},
        "L2_dphi": {"P_k": P_overlap_dphi_tight, "vs_fock": cmp_dphi_tight},
    },
    "phiborn1_consistency": {
        "P_x_gradient_normalization": p_x_norm,
        "sector_integral_window_5_over_m": sector_window_probs,
        "sector_integral_vs_fock": cmp_sector_window,
        "sector_integral_winding_bins": sector_winding_probs,
        "sector_winding_vs_fock": cmp_sector_winding,
    },
    "interpretation": {
        "positive_result": positive_result,
        "negative_result": negative_result,
        "L2_phi_fails_reason": "integral |phi|^2 diverges on R; windowed L2(phi) overlap does not recover |c_k|^2",
        "L2_dphi_note": "gradient localized amplitude (PHIBORN1) gives finite norm = M_kink BPS per kink",
        "field_theoretic_inner_product_needed": not dphi_orthogonal or not dphi_fock_match,
    },
    "cat_level": cat_level,
    "next_rank": next_rank,
    "wall_clock_seconds": time.time() - t0,
    "status": status,
}

out_path = Path(__file__).parent / "phiborn2_kink_overlap_born_results.json"
with open(out_path, "w") as f:
    json.dump(results, f, indent=2)

signal.alarm(0)

print("=" * 72)
print("RANK 074-PHIBORN2: Kink overlap -> Born probability")
print("=" * 72)
print(f"  m_phi = {M_TAU_MEV} MeV")
print(f"  Kink separation (well): {separation:.6e} GeV^-1 = {separation * 197.327:.2f} fm")
print(f"  P_fock = {[round(p, 6) for p in P_fock]}")
print()
print("  Orthogonality (normalized Gram off-diagonal max):")
print(f"    L2(phi) windowed:  {off_diag_phi:.6f}  orthogonal={phi_orthogonal}")
print(f"    L2(dphi/dx):        {off_diag_dphi:.6f}  orthogonal={dphi_orthogonal}")
print()
print("  Born weights P(k) from overlap (well-separated):")
print(f"    L2(phi):   {[round(p, 6) for p in P_overlap_phi]}  sum={sum_P_phi:.12f}")
print(f"               vs Fock max residual: {cmp_phi['max_residual']:.6f}")
print(f"    L2(dphi):  {[round(p, 6) for p in P_overlap_dphi]}  sum={sum_P_dphi:.12f}")
print(f"               vs Fock max residual: {cmp_dphi['max_residual']:.6f}")
print()
print("  PHIBORN1 consistency (P(x)=|dphi|^2/norm sector integrals):")
print(f"    window sectors:  {[round(p, 6) for p in sector_window_probs]}")
print(f"    vs Fock max res: {cmp_sector_window['max_residual']:.6f}")
print(f"    winding sectors: {[round(p, 6) for p in sector_winding_probs]}")
print(f"    vs Fock max res: {cmp_sector_winding['max_residual']:.6f}")
print()
print(f"  Cat level: {cat_level}")
print(f"  Next rank: {next_rank}")
print(f"  Results: {out_path}")
print(f"  STATUS: {status}")
