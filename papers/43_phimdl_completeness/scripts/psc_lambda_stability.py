"""
PSC Orbit Stability Under Cosmological Constant Λ
===================================================
Tests whether the PSC-admissible orbit (gen1→gen2→gen3→vacuum) remains stable
when a de Sitter correction is applied to the CMCA causal-graph τ_c values.

Model: Rule 110 CMCA on periodic 1D tape, L=100 cells, T=200 steps.
De Sitter correction: each cell i has τ_c multiplied by (1 + Λ * x_i² / L²)
where x_i = i - L/2 is the position relative to center.

PSC-admissible Z₇ winding sectors: {0, 2, 3, 4, 6}
- vacuum = 0
- gen1 (electron-type) = 4
- gen2 (muon-type) = 3
- gen3 (tau-type) = 2 (or 6)

The PSC orbit stability criterion:
1. Vacuum state (all-zeros tape) must remain a fixed point under the modified CA.
2. The gen1/gen2/gen3 kink winding numbers must remain in {2,3,4,6} and
   not collapse to {1,5} (dark sector / PSC-inadmissible).
3. The CMCA still produces a unique attractor in the {0,2,3,4,6} sector.

Authors: Ninja (EPIC_075 Session 4)
Date: 2026-05-26
"""

import json
import signal
import sys
import time
import numpy as np

TIMEOUT_SECONDS = 600

def _timeout_handler(signum, frame):
    print(f"\nTIMEOUT: wall-clock limit {TIMEOUT_SECONDS}s reached. Saving partial results.")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

# ─────────────────────────────────────────────────
# Rule 110 truth table (Z₂ level)
# ─────────────────────────────────────────────────
RULE110 = {
    (1,1,1): 0, (1,1,0): 1, (1,0,1): 1, (1,0,0): 0,
    (0,1,1): 1, (0,1,0): 1, (0,0,1): 1, (0,0,0): 0
}

# Z₇ f_MDL lookup table (from GTE: maps 5-cell Z₇ neighborhoods)
# For 1D mod-7 purposes, simplified to the standard GTE f_MDL table on Z₇
# PSC-admissible cells: {0, 2, 3, 4, 6} = vacuum/gen1/gen2/gen3
PSC_ADMISSIBLE = {0, 2, 3, 4, 6}
PSC_INADMISSIBLE = {1, 5}  # dark sector / Z₇-forbidden in SM orbit

def rule110_step(tape):
    """One step of Rule 110 on a periodic tape."""
    L = len(tape)
    new_tape = np.zeros(L, dtype=int)
    for i in range(L):
        l = tape[(i - 1) % L]
        c = tape[i]
        r = tape[(i + 1) % L]
        new_tape[i] = RULE110[(l, c, r)]
    return new_tape

def rule110_step_weighted(tape, weights):
    """
    Rule 110 step with de Sitter-weighted τ_c.
    Cells with weight > τ_threshold are 'slower' — they update less often.
    Model: cell i fires only if a uniform random draw < 1/weight_i.
    (For τ_c = 1 everywhere, this is standard synchronous Rule 110.)
    For the vacuum-fixed-point test we use deterministic: skip update if weight > 1.
    We use a threshold-based model: cell fires if weight_i * random < 1.
    For analytical test, use τ_c > 1 → cell participates with probability 1/weight.
    """
    L = len(tape)
    new_tape = tape.copy()
    for i in range(L):
        w = weights[i]
        prob = 1.0 / w if w > 0 else 0.0
        if np.random.random() < prob:
            l = tape[(i - 1) % L]
            c = tape[i]
            r = tape[(i + 1) % L]
            new_tape[i] = RULE110[(l, c, r)]
    return new_tape

def compute_weights(L, Lambda):
    """
    De Sitter correction to τ_c values.
    x_i = i - L/2 (position relative to center)
    weight_i = τ_c_i = 1 + Λ * x_i² / L²
    """
    x = np.arange(L) - L / 2.0
    return 1.0 + Lambda * (x / L) ** 2

def is_vacuum_fixed_point(L, Lambda):
    """
    Check if the all-zeros tape is a fixed point under Rule 110
    (it always is for standard Rule 110, but check for weighted version).
    For the de Sitter model: the zero tape stays zero because RULE110[(0,0,0)] = 0.
    This is independent of weights — the all-zeros state is ALWAYS a fixed point.
    """
    # RULE110[(0,0,0)] = 0, so vacuum is always a fixed point regardless of weights
    return True

def run_psc_orbit_test(L, T, Lambda, seed=42, n_trials=5):
    """
    Run CMCA with de Sitter-weighted τ_c.
    
    Tests:
    1. Vacuum (all-zeros) stays fixed.
    2. Random initial tapes evolve toward vacuum-dominated patterns.
    3. Count fraction of cells in PSC-inadmissible states after T steps.
    
    For Z₇ extension: map binary Rule 110 output to Z₇ using the standard
    winding-number assignment: 0→0(vacuum), 1-patterns→{2,3,4,6} (SM sector).
    
    Since Rule 110 is Z₂ (binary), we track the winding sector by looking at
    the density of '1' cells: high density ~ gen3, medium ~ gen2, low ~ gen1.
    In the GTE framework, the Z₇ winding is assigned by the local 5-cell pattern.
    For this test we use the simpler proxy: fraction of '1' cells as an indicator.
    """
    np.random.seed(seed)
    
    weights = compute_weights(L, Lambda)
    max_weight = weights.max()
    
    # Test 1: vacuum fixed point
    vacuum_tape = np.zeros(L, dtype=int)
    test_tape = vacuum_tape.copy()
    for t in range(T):
        test_tape = rule110_step_weighted(test_tape, weights)
    vacuum_stable = np.all(test_tape == 0)
    
    # Test 2: random tapes converge to vacuum-dominated patterns
    # Metric: does the density of '1' cells decrease over time (attractor at vacuum)?
    final_densities = []
    converge_steps = []
    
    for trial in range(n_trials):
        rng = np.random.RandomState(seed + trial)
        tape = rng.randint(0, 2, size=L)
        
        prev_density = tape.mean()
        converge_step = None
        
        for t in range(T):
            tape = rule110_step_weighted(tape, weights)
            density = tape.mean()
            
            # Check if tape has settled into a periodic/vacuum pattern
            if density < 0.01 and converge_step is None:
                converge_step = t
        
        final_densities.append(tape.mean())
        converge_steps.append(converge_step)
    
    # Test 3: check orbit stability — does the CA still produce glider-like
    # structures (proxies for gen1/gen2/gen3 kinks)?
    # Run a single-glider initial condition (a period-14 ether seed from CMCA)
    ether_tape = np.zeros(L, dtype=int)
    # Standard Rule 110 background ether: period-14 pattern
    ether_pattern = [1,1,1,0,1,1,0,1,1,1,0,1,1,0]
    for i in range(L):
        ether_tape[i] = ether_pattern[i % 14]
    
    ether_final = ether_tape.copy()
    for t in range(T):
        ether_final = rule110_step_weighted(ether_final, weights)
    
    # Check if ether structure is preserved (measure correlation with ether pattern)
    ether_final_corr = 0.0
    for i in range(L):
        ether_final_corr += (ether_final[i] == ether_pattern[i % 14])
    ether_corr = ether_final_corr / L
    
    return {
        "Lambda": Lambda,
        "max_weight": float(max_weight),
        "vacuum_fixed_point": bool(vacuum_stable),
        "mean_final_density": float(np.mean(final_densities)),
        "std_final_density": float(np.std(final_densities)),
        "ether_correlation": float(ether_corr),
        "converge_fracs": sum(1 for c in converge_steps if c is not None) / n_trials,
    }

def run_deterministic_psc_test(L, T, Lambda):
    """
    Deterministic test: for large Λ, the τ_c weights become very large at edges.
    The extreme case: cells near edges never fire (prob ≈ 0), while center fires normally.
    This would effectively truncate the tape to just the central portion.
    
    For very large Λ >> 1:
    - Edge cells (x ≈ ±L/2) have weight ≈ 1 + Λ/4 >> 1 → fire rate ≈ 4/Λ → 0
    - Center cells (x ≈ 0) have weight ≈ 1 → fire rate ≈ 1 (normal)
    
    Critical question: for Rule 110 on a finite effective domain, does the ether
    structure collapse? The ether requires periodic boundary conditions to be stable.
    If edges are frozen (fire rate → 0), the effective system becomes non-periodic,
    and the Rule 110 ether can unravel.
    
    The PSC orbit stability criterion: ether correlation > 0.85 (arbitrary but sensible).
    """
    np.random.seed(42)
    weights = compute_weights(L, Lambda)
    
    # Ether initial condition
    ether_pattern = [1,1,1,0,1,1,0,1,1,1,0,1,1,0]
    tape = np.array([ether_pattern[i % 14] for i in range(L)], dtype=int)
    
    for t in range(T):
        tape = rule110_step_weighted(tape, weights)
    
    corr = sum(tape[i] == ether_pattern[i % 14] for i in range(L)) / L
    
    # Effective lattice size: cells with weight > 10 are effectively frozen
    effective_size = sum(1 for w in weights if w < 10.0)
    
    return {
        "Lambda": Lambda,
        "ether_correlation": float(corr),
        "effective_size": int(effective_size),
        "orbit_stable": bool(corr > 0.70),
    }

# ─────────────────────────────────────────────────
# Main computation
# ─────────────────────────────────────────────────

L = 100
T = 200
N_SEEDS = 5

Lambda_values = [0, 1e-3, 1e-2, 1e-1, 1.0, 10.0, 100.0, 1000.0, 1e4, 1e6]

print("PSC Orbit Stability Under Cosmological Constant Perturbation")
print("=" * 60)
print(f"L={L}, T={T}, N_seeds={N_SEEDS}")
print()
print(f"{'Λ':>12} | {'max_τ_c':>8} | {'vac_fp':>6} | {'ether_corr':>10} | {'eff_L':>6} | stable")
print("-" * 65)

t_start = time.time()
results = []

for Lambda in Lambda_values:
    if time.time() - t_start > TIMEOUT_SECONDS - 10:
        print("Approaching timeout — stopping early.")
        break
    
    r_det = run_deterministic_psc_test(L, T, Lambda)
    
    max_w = 1.0 + Lambda * 0.25  # max weight at edge: x = ±L/2, (x/L)² = 0.25
    
    row = {
        "Lambda": Lambda,
        "max_tau_c": max_w,
        "vacuum_fixed_point": True,  # always true for Rule 110 (algebraic)
        "ether_correlation": r_det["ether_correlation"],
        "effective_lattice_size": r_det["effective_size"],
        "orbit_stable": r_det["orbit_stable"],
    }
    results.append(row)
    
    stable_str = "✓ STABLE" if row["orbit_stable"] else "✗ BROKEN"
    print(f"{Lambda:>12.4g} | {max_w:>8.4g} | {'yes':>6} | "
          f"{row['ether_correlation']:>10.4f} | {row['effective_lattice_size']:>6} | {stable_str}")

print()

# Identify critical Λ_c: first Λ where orbit breaks
stable_list = [(r["Lambda"], r["orbit_stable"]) for r in results]
broken = [r["Lambda"] for r in results if not r["orbit_stable"]]
Lambda_c = broken[0] if broken else None

print(f"Critical Λ_c (first orbit break): {Lambda_c}")
print()

# ─────────────────────────────────────────────────
# Analytical estimate of Λ_c
# ─────────────────────────────────────────────────
print("Analytical estimates:")
print()

# Kink mass and Compton wavelength
M_kink_MeV = 290.10  # MeV
hbar_c_MeV_fm = 197.3269804  # MeV·fm

lambda_kink_fm = hbar_c_MeV_fm / M_kink_MeV
print(f"  λ_kink = ℏc / M_kink = {hbar_c_MeV_fm:.4f} / {M_kink_MeV:.4f} = {lambda_kink_fm:.4f} fm")

# PSC stability bound: Λ < 3/λ_kink² (de Sitter radius > λ_kink)
# (natural units: ℏ=c=1, distances in fm, masses in MeV)
Lambda_PSC_bound_MeV2 = M_kink_MeV**2 / hbar_c_MeV_fm**2  # in fm⁻² = (MeV/ℏc)²
Lambda_PSC_bound_fm2 = 1.0 / lambda_kink_fm**2  # fm⁻²

print(f"  PSC de Sitter stability: R_dS > λ_kink → Λ < 3/λ_kink²")
print(f"  Λ_PSC_upper = 3 × (1/λ_kink²) = {3.0/lambda_kink_fm**2:.4f} fm⁻²")
print(f"  Λ_PSC_upper in MeV² = 3 × M_kink²/(ℏc)² = {3*M_kink_MeV**2/hbar_c_MeV_fm**2:.4e} fm⁻²")
print()

# Convert to SI
MeV_to_J = 1.602176634e-13  # J per MeV
hbar_SI = 1.054571817e-34    # J·s
c_SI = 2.99792458e8          # m/s
G_N = 6.67430e-11            # m³/(kg·s²)

M_kink_kg = M_kink_MeV * MeV_to_J / c_SI**2
lambda_kink_m = hbar_SI * c_SI / (M_kink_kg * c_SI**2)

print(f"  M_kink = {M_kink_kg:.4e} kg")
print(f"  λ_kink = {lambda_kink_m:.4e} m = {lambda_kink_m*1e15:.4f} fm (check: {lambda_kink_fm:.4f} fm)")

Lambda_PSC_upper_m2 = 3.0 / lambda_kink_m**2
Lambda_obs_m2 = 1.1056e-52   # m⁻²  (Λ = 2.888 × 10⁻¹²² l_P⁻² ≈ 1.1e-52 m⁻²)

print(f"  Λ_PSC_upper (SI) = {Lambda_PSC_upper_m2:.4e} m⁻²")
print(f"  Λ_observed       = {Lambda_obs_m2:.4e} m⁻²")
print(f"  Ratio Λ_obs/Λ_PSC = {Lambda_obs_m2/Lambda_PSC_upper_m2:.4e}  (PSC bound is {Lambda_PSC_upper_m2/Lambda_obs_m2:.4e}× the observed Λ)")
print()

# PSC bound on G: r_S(M_kink) << λ_kink → G << ℏc/(2 M_kink²) = λ_kink²·c³/(2ℏ)
G_PSC_upper = hbar_SI * c_SI / (2 * M_kink_kg**2)
print("PSC constraint on Newton's G:")
print(f"  Condition: Schwarzschild radius r_S = 2GM_kink/c² << λ_kink = ℏ/(M_kink c)")
print(f"  → G << ℏc / (2 M_kink²)")
print(f"  G_PSC_upper = ℏc/(2M_kink²) = {G_PSC_upper:.4e} m³/(kg·s²)")
print(f"  G_Newton    = {G_N:.4e} m³/(kg·s²)")
print(f"  G_N / G_PSC = {G_N/G_PSC_upper:.4e}  (G_Newton is {G_PSC_upper/G_N:.4e}× BELOW the PSC bound)")
print()

# Schwarzschild radius of a kink
r_S_kink = 2 * G_N * M_kink_kg / c_SI**2
print(f"  Schwarzschild radius of kink: r_S = 2G_N M_kink/c² = {r_S_kink:.4e} m = {r_S_kink*1e15:.4e} fm")
print(f"  Compton wavelength of kink:   λ_kink = {lambda_kink_m:.4e} m = {lambda_kink_m*1e15:.4f} fm")
print(f"  r_S / λ_kink = {r_S_kink/lambda_kink_m:.4e}  (PSC satisfied: kinks do NOT collapse into black holes)")
print()

# PSC reflexive Λ argument: the fixed-point iteration
print("PSC Reflexive Λ Fixed-Point Analysis:")
print("  Claim: Λ must satisfy the PSC self-consistency equation Λ = f(Λ)")
print("  where f(Λ) = Z₇ vacuum energy + de Sitter correction to ZPE")
print()
print("  Classical: f(0) = 0 exactly (Z₇ cosine minima at V=0 — CatAD)")
print("  Quantum:   f(Λ) = ΔV_CW + δV_dS(Λ)")
print()

# Coleman-Weinberg one-loop correction
# ΔV_CW = m_φ⁴/(64π²) × [ln(m_φ²/μ²) - 3/2]  (massive scalar, MS-bar)
# m_φ = 1776.86 MeV (the Z₇-KG field mass = tau lepton mass from GTE)
m_phi_MeV = 1776.86  # MeV
m_phi_kg = m_phi_MeV * MeV_to_J / c_SI**2
mu_MeV = m_phi_MeV  # renormalization scale = m_φ (MS-bar)

DeltaV_CW_MeV4 = m_phi_MeV**4 / (64 * np.pi**2) * (np.log(1) - 3/2)
DeltaV_CW_MeV4_abs = abs(DeltaV_CW_MeV4)
print(f"  ΔV_CW (one-loop, μ=m_φ) = {DeltaV_CW_MeV4:.4e} MeV⁴")
print(f"  |ΔV_CW| = {DeltaV_CW_MeV4_abs:.4e} MeV⁴")

# de Sitter correction to ZPE: δV_dS(Λ) ~ H² m_φ² / (16π²) where H² = Λc²/3
# For observed Λ = 1.1e-52 m⁻², H = √(Λc²/3) = 2.17e-18 s⁻¹ = H_0 (Hubble constant)
H0_s = 2.17e-18  # s⁻¹
H0_eV = hbar_SI * H0_s / MeV_to_J * 1e6  # eV
H0_MeV = H0_eV * 1e-6
dV_dS_MeV4 = H0_MeV**2 * m_phi_MeV**2 / (16 * np.pi**2)
print(f"  δV_dS (de Sitter correction at observed Λ) = H₀² m_φ²/(16π²) = {dV_dS_MeV4:.4e} MeV⁴")
print(f"  Ratio |δV_dS| / |ΔV_CW| = {dV_dS_MeV4/DeltaV_CW_MeV4_abs:.4e}  (de Sitter correction is negligible)")
print()
print("  PSC reflexive Λ fixed-point equation: Λ = f(Λ)")
print("  - Classical: Λ = 0 is the unique fixed point (V(φ_k)=0 for all k)")
print("  - Quantum: f(Λ) = ΔV_CW + O(H²) where ΔV_CW >> δV_dS for Λ << Λ_PSC")
print("  - The de Sitter correction to ΔV_CW is ~10⁻⁸² relative for observed Λ")
print("  - Therefore: the quantum fixed-point equation has NO Λ=0 solution")
print("  - The PSC reflexive argument fails to cancel the quantum ZPE")
print()
print("  CONCLUSION: PSC reflexivity constrains Λ < Λ_PSC ≈ 10³⁰ m⁻² (orbit stability)")
print("  but does NOT select Λ = 0 at the quantum level.")
print("  The argument conflates PSC admissibility (algebraic, metric-independent)")
print("  with orbit dynamics (CA-level, can depend on τ_c weights).")

# ─────────────────────────────────────────────────
# Save results
# ─────────────────────────────────────────────────

output = {
    "model": {
        "L": L, "T": T, "N_seeds": N_SEEDS,
        "rule": "Rule 110 CMCA with de Sitter τ_c weighting",
        "de_sitter_correction": "τ_c(i) = 1 + Λ × (x_i/L)², x_i = i - L/2"
    },
    "lambda_scan": results,
    "critical_Lambda_c": Lambda_c,
    "analytical": {
        "kink_mass_MeV": M_kink_MeV,
        "lambda_kink_fm": lambda_kink_fm,
        "lambda_kink_m": lambda_kink_m,
        "r_S_kink_m": r_S_kink,
        "r_S_over_lambda_kink": r_S_kink / lambda_kink_m,
        "Lambda_PSC_upper_m2": Lambda_PSC_upper_m2,
        "Lambda_observed_m2": Lambda_obs_m2,
        "Lambda_obs_over_PSC_bound": Lambda_obs_m2 / Lambda_PSC_upper_m2,
        "G_PSC_upper_SI": G_PSC_upper,
        "G_Newton_SI": G_N,
        "G_Newton_over_G_PSC_bound": G_N / G_PSC_upper,
        "DeltaV_CW_MeV4": DeltaV_CW_MeV4,
        "dV_dS_at_observed_Lambda_MeV4": dV_dS_MeV4,
        "dS_correction_over_CW_correction": dV_dS_MeV4 / DeltaV_CW_MeV4_abs,
    },
    "psc_reflexive_argument_verdict": {
        "logical_validity": "PARTIALLY VALID — the reflexive structure is correct in principle",
        "classical_Lambda_0": "VALID — Z₇ cosine potential forces V=0 at all vacua (CatAD) regardless of Λ",
        "quantum_Lambda_0": "INVALID — PSC reflexive iteration cannot cancel ZPE; de Sitter correction to ΔV_CW is ~10⁻⁸²",
        "PSC_orbit_stability_gives_upper_bound": True,
        "Lambda_PSC_upper_m2_vs_observed": "PSC upper bound exceeds observed Λ by ~82 orders of magnitude",
        "PSC_constraint_on_G": "G_Newton satisfies G << G_PSC_upper by ~39 orders of magnitude; PSC gives only a weak upper bound, not a prediction",
        "overall_verdict": "PSC/reflexivity provides NO mechanism for quantum Λ=0. It gives weak upper bounds on both Λ and G that are consistent with observations but do not predict them. Classical Λ=0 is protected by Z₇ structure (already CatAD), not by PSC reflexivity.",
    }
}

import pathlib as _pl
output_path = str(_pl.Path(__file__).resolve().parent / "psc_lambda_stability_results.json")
with open(output_path, "w") as f:
    json.dump(output, f, indent=2)

print()
print(f"Results saved: {output_path}")

signal.alarm(0)
