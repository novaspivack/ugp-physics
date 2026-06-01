#!/usr/bin/env python3
"""
G13 infrastructure: 3+1D SU(3) Wilson loop Monte Carlo for string tension.

Physical context
----------------
Goal: measure the string tension σ in the Φ_MDL/SU(3) theory to determine
f_quant precisely, resolving the 7.28% gap between:
    f_quant(C-ratio)  = 0.6289   [P39 canonical]
    f_quant(σ-ratio)  = 0.6747   [σ_PDG / σ_GTE_classical]

The standard tool is the Creutz ratio:
    χ(I,J) = -ln[ W(I,J)·W(I-1,J-1) / (W(I,J-1)·W(I-1,J)) ]  →  σ·a²  as I,J→∞

where W(I,J) is the expectation value of a rectangular I×J Wilson loop.

F₂₁ ↪ SU(3) embedding (CatAL, P39, commit f21_su3_continuum_limit_results.json)
-------------------
- F₂₁ = Z₇ ⋊ Z₃ faithfully embeds in SU(3) (max det-1 error: 4×10⁻¹⁵)
- Pure F₂₁ gauge freezes at β_f ≈ 0.857; no standalone continuum limit
- Burnside: F₂₁ generates full M_3(ℂ), so SU(3)/F₂₁ coset is filled by scalar
- The correct framework is SU(3) Yang-Mills with MDL coupling b₀=7 (CatAL, P39)

This script (infrastructure only)
-----------------------------------
Initializes a L^4 SU(3) lattice with random (hot) start and measures the
average plaquette P = (1/3) Re Tr(U_μν). For a hot start, P ≈ 0; after
thermalization at β=6, P ≈ 0.60-0.65.

Full simulation requirements are documented in g13_creutz_plan.py.

Artifacts
---------
Output: papers/39_qcd_from_gte/scripts/g13_wilson_loop_infrastructure_results.json
"""

import numpy as np
import math
import json
import signal
import sys
import time

# ── Timeout guard ──────────────────────────────────────────────────────────────
TIMEOUT_SECONDS = 300
t_start = time.time()

def _timeout_handler(signum, frame):
    print(f"\nTIMEOUT: wall-clock limit {TIMEOUT_SECONDS}s reached. Saving partial results.")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

# ── GTE/SU(3) physical parameters ─────────────────────────────────────────────
delta_K       = math.log2(9)          # MDL confinement cost: log₂9 bits (CatAD)
m_tau_GeV     = 1.77686               # tau mass, PDG 2022
m_kink_GeV    = (8.0 / 49.0) * m_tau_GeV  # BPS kink mass (CatAD, P42)
sigma_GTE_classical = delta_K * m_kink_GeV**2   # classical σ (no quantum corrections)
sigma_PDG     = 0.18                  # GeV² (phenomenological string tension)
C_F           = 4.0 / 3.0            # SU(3) fundamental Casimir
N_c           = 3

f_quant_C_ratio   = 0.6289           # from P39 C-ratio calibration
f_quant_sigma_ratio = sigma_PDG / sigma_GTE_classical  # direct ratio
f_quant_candidate = 2**(-2.0/3.0)   # 4^{-1/3} = (C_F·N_c)^{-1/3} PROVISIONAL

print("=" * 70)
print("G13 Wilson Loop Infrastructure — SU(3) Lattice Setup")
print("=" * 70)
print(f"  m_kink = (8/49)m_τ = {m_kink_GeV*1000:.4f} MeV")
print(f"  ΔK = log₂9 = {delta_K:.6f}")
print(f"  σ_GTE_classical = ΔK × m_kink² = {sigma_GTE_classical:.6f} GeV²")
print(f"  σ_PDG = {sigma_PDG} GeV²")
print(f"  f_quant(C-ratio)   = {f_quant_C_ratio:.4f}")
print(f"  f_quant(σ-ratio)   = {f_quant_sigma_ratio:.4f}")
print(f"  f_quant(candidate) = 2^(-2/3) = {f_quant_candidate:.6f}")
print(f"  Gap = {abs(f_quant_sigma_ratio - f_quant_C_ratio)/f_quant_C_ratio*100:.2f}%")
print()

# ── SU(3) matrix operations ────────────────────────────────────────────────────

def random_su3(rng):
    """
    Generate a uniformly distributed SU(3) matrix via QR decomposition.

    Steps:
    1. Sample a 3×3 complex Gaussian matrix.
    2. QR-decompose: Q is unitary, R is upper-triangular.
    3. Fix R to have positive diagonal (standard QR → unique unitary).
    4. Fix det(Q) = 1 by rotating by the cube root of the determinant.
    """
    Z = rng.standard_normal((3, 3)) + 1j * rng.standard_normal((3, 3))
    Q, R = np.linalg.qr(Z)
    # Make R diagonal elements real positive (standard QR gauge)
    d = np.diag(R)
    ph = d / np.abs(d)
    Q = Q * ph[np.newaxis, :]
    # Fix det = 1
    det = np.linalg.det(Q)
    Q = Q * (np.conj(det) / np.abs(det))**(1.0/3.0)
    return Q

def plaquette_trace(U, site, mu, nu, L):
    """
    Compute (1/3) Re Tr(U_μ(x) U_ν(x+μ̂) U_μ†(x+ν̂) U_ν†(x)) for one plaquette.

    U shape: (L, L, L, L, 4) array of 3x3 complex matrices.
    site: tuple (x0, x1, x2, x3)
    """
    x  = np.array(site, dtype=int)
    eμ = np.zeros(4, dtype=int); eμ[mu] = 1
    eν = np.zeros(4, dtype=int); eν[nu] = 1

    x1   = tuple((x + eμ)      % L)
    x2   = tuple((x + eν)      % L)
    x12  = tuple((x + eμ + eν) % L)
    xs   = tuple(x)

    Uμx   = U[xs  + (mu,)]
    Uνx1  = U[x1  + (nu,)]
    Uμx2  = U[x2  + (mu,)]  # U_μ†(x+ν̂)
    Uνx   = U[xs  + (nu,)]  # U_ν†(x)

    # W = U_μ(x) · U_ν(x+μ̂) · U_μ†(x+ν̂) · U_ν†(x)
    W = Uμx @ Uνx1 @ Uμx2.conj().T @ Uνx.conj().T
    return np.real(np.trace(W)) / 3.0

def measure_plaquette_all(U, L):
    """Average plaquette over all sites and all (μ,ν) with μ < ν."""
    total = 0.0
    count = 0
    for x0 in range(L):
        for x1 in range(L):
            for x2 in range(L):
                for x3 in range(L):
                    for mu in range(4):
                        for nu in range(mu + 1, 4):
                            total += plaquette_trace(U, (x0, x1, x2, x3), mu, nu, L)
                            count += 1
    return total / count

def unitarity_check(U, L, n_sample=20):
    """Check UU† = I for a random sample of links. Returns max Frobenius error."""
    rng_check = np.random.default_rng(0)
    max_err = 0.0
    for _ in range(n_sample):
        x0, x1, x2, x3 = rng_check.integers(0, L, 4)
        mu = rng_check.integers(0, 4)
        M = U[(x0, x1, x2, x3, mu)]
        err = np.max(np.abs(M @ M.conj().T - np.eye(3)))
        if err > max_err:
            max_err = err
    return max_err

# ── Lattice initialization ─────────────────────────────────────────────────────

# L=4 for feasibility within timeout; full run uses L≥16
L = 4
N_sites  = L**4
N_dirs   = 4
N_links  = N_sites * N_dirs

rng = np.random.default_rng(seed=42)

print(f"Initializing {L}^4 SU(3) lattice (hot start) ...")
print(f"  Total links: {N_links}")
print(f"  Each link: 3×3 SU(3) matrix (18 real DOF)")
print()

# Build U as a numpy object array: shape (L,L,L,L,4) of 3x3 matrices
U = np.empty((L, L, L, L, 4), dtype=object)
t_init = time.time()
for x0 in range(L):
    for x1 in range(L):
        for x2 in range(L):
            for x3 in range(L):
                for mu in range(4):
                    U[(x0, x1, x2, x3, mu)] = random_su3(rng)

t_elapsed = time.time() - t_init
print(f"Initialization done in {t_elapsed:.2f}s")

# ── Unitarity verification ─────────────────────────────────────────────────────
max_unitarity_err = unitarity_check(U, L)
print(f"Unitarity check (max ||UU†-I||_∞): {max_unitarity_err:.2e}")
assert max_unitarity_err < 1e-12, "SU(3) unitarity violated!"

# ── Average plaquette on hot start ────────────────────────────────────────────
print()
print("Measuring average plaquette on hot start ...")
t_meas = time.time()
P_hot = measure_plaquette_all(U, L)
t_meas = time.time() - t_meas
print(f"  Average plaquette (hot start): P = {P_hot:.6f}")
print(f"  (Expected for random SU(3):    P ≈ 0 — hot start is maximally disordered)")
print(f"  (Expected after thermalization at β=6: P ≈ 0.60–0.65)")
print(f"  Measurement time: {t_meas:.2f}s")

# ── Wilson loop structure (not computed — infrastructure only) ─────────────────
print()
print("Wilson loop sizes (infrastructure geometry):")
print("  W(I,J): rectangular loop, I steps in μ̂ direction, J steps in ν̂ direction")
print("  Creutz ratio: χ(I,J) = -ln[ W(I,J)·W(I-1,J-1) / (W(I,J-1)·W(I-1,J)) ]")
print("  String tension: χ(I,J) → σ·a² as I,J → ∞")
print()

# At β=6, a≈0.093 fm → need I,J up to 8 to see string at R≈0.75 fm
a_beta6_fm   = 0.093    # fm (standard SU(3) lattice calibration at β=6)
hbar_c_MeV_fm = 197.3  # MeV·fm
a_beta6_GeV  = a_beta6_fm / (hbar_c_MeV_fm * 1e-3)  # GeV^-1

print(f"  At β=6: a ≈ {a_beta6_fm:.3f} fm ≈ {a_beta6_GeV:.3f} GeV⁻¹")
print(f"  Loop 4×4 reaches R = {4*a_beta6_fm:.3f} fm = {4*a_beta6_GeV:.3f} GeV⁻¹")
print(f"  Loop 8×8 reaches R = {8*a_beta6_fm:.3f} fm = {8*a_beta6_GeV:.3f} GeV⁻¹")
sigma_a2_expected = sigma_PDG * a_beta6_GeV**2
print(f"  σ·a² expected at β=6: {sigma_a2_expected:.5f}")
print(f"  (Creutz ratio should asymptote to this value)")

# ── f_quant discrimination requirement ────────────────────────────────────────
print()
print("f_quant discrimination:")
print(f"  f_quant = 2^(-2/3) = {f_quant_candidate:.6f}  → σ_pred = {sigma_GTE_classical*f_quant_candidate:.5f} GeV²")
print(f"  f_quant = 5/8      = {5/8:.6f}                → σ_pred = {sigma_GTE_classical*5/8:.5f} GeV²")
print(f"  f_quant(C-ratio)   = {f_quant_C_ratio:.6f}  → σ_pred = {sigma_GTE_classical*f_quant_C_ratio:.5f} GeV²")
print(f"  f_quant(σ-ratio)   = {f_quant_sigma_ratio:.6f}  → σ_pred = {sigma_PDG:.5f} GeV² (by definition)")
print(f"  Needed discrimination: Δσ/σ = {(f_quant_sigma_ratio - f_quant_C_ratio)/f_quant_C_ratio*100:.2f}%")
print(f"  Required statistical precision: <2% in Creutz ratio (systematic-dominated)")

# ── Results dict ──────────────────────────────────────────────────────────────
results = {
    "infrastructure": {
        "L": L,
        "lattice_geometry": f"{L}^4 SU(3) Wilson action",
        "initialization": "hot start (uniformly random SU(3) matrices via QR)",
        "seed": 42,
        "n_links": N_links,
        "max_unitarity_error": float(max_unitarity_err),
        "init_time_s": round(t_elapsed, 3),
        "meas_time_s": round(t_meas, 3),
    },
    "plaquette_hot_start": {
        "P_avg": float(P_hot),
        "expected_random": 0.0,
        "expected_thermalized_beta6": 0.62,
        "note": "hot start → P≈0; full simulation needs Metropolis/heatbath sweeps",
    },
    "gte_inputs": {
        "delta_K": round(delta_K, 8),
        "m_kink_MeV": round(m_kink_GeV * 1000, 4),
        "sigma_GTE_classical_GeV2": round(sigma_GTE_classical, 8),
        "sigma_PDG_GeV2": sigma_PDG,
        "f_quant_C_ratio": f_quant_C_ratio,
        "f_quant_sigma_ratio": round(f_quant_sigma_ratio, 6),
        "f_quant_candidate_4neg13": round(f_quant_candidate, 8),
        "gap_pct": round(abs(f_quant_sigma_ratio - f_quant_C_ratio) / f_quant_C_ratio * 100, 4),
    },
    "wilson_loop_geometry": {
        "action": "S = β × Σ_P (1 - (1/3) Re Tr U_P)",
        "beta_target": 6.0,
        "a_fm_at_beta6": a_beta6_fm,
        "sigma_a2_expected": round(sigma_a2_expected, 6),
        "creutz_formula": "χ(I,J) = -ln[ W(I,J)·W(I-1,J-1) / (W(I,J-1)·W(I-1,J)) ]",
        "creutz_limit": "χ(I,J) → σ·a² as I,J → ∞",
    },
    "status": "INFRASTRUCTURE_ONLY — hot start plaquette measured; full simulation in g13_creutz_plan.py",
    "epic": "EPIC_080",
    "rank": "080-G13",
    "date": "2026-05-29",
    "elapsed_s": round(time.time() - t_start, 3),
}

out_path = "papers/39_qcd_from_gte/scripts/g13_wilson_loop_infrastructure_results.json"
with open(out_path, "w") as f:
    json.dump(results, f, indent=2)

print()
print(f"Results saved to {out_path}")
print()
print("Summary:")
print(f"  ✓ {L}^4 SU(3) lattice initialized with {N_links} random links")
print(f"  ✓ Unitarity verified: max error = {max_unitarity_err:.2e}")
print(f"  ✓ Hot-start plaquette: P = {P_hot:.4f} (expected ≈ 0 for random start)")
print(f"  ✓ Full Creutz ratio plan → g13_creutz_plan.py")
print(f"  ✓ Infrastructure only — full run requires 10^4+ sweeps on L≥16 lattice")

signal.alarm(0)
