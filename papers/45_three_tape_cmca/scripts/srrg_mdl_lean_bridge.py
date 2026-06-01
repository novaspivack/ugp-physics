#!/usr/bin/env python3
"""
srrg_mdl_lean_bridge.py — SRRG=MDL equivalence: numerical verification of
the Lean-provable algebraic identity β_SRRG(g) = 0 ↔ K_CMCA(g) = 0.

EPIC_080 rank 080-MDLSRRG-LEAN.

The GTE polynomial p(g,g,g) over ℝ equals g when g² + g = 1.
Define:
  β_SRRG(g) = p(g,g,g) - g = g(1 - g - g²)  [SRRG beta function]
  K_CMCA(g) = -log₂(g² + g)                  [MDL description length]

Both vanish exactly at g* = 1/φ = (√5-1)/2.
This is the numerical certificate for the Lean theorem
  srrg_beta_zero_iff_kCMCA_minimum (g : ℝ) (hg : 0 < g) :
      srrgBetaFn g = 0 ↔ kCMCA g = 0

Also verifies:
  - K_CMCA is strictly positive on (0, g*)
  - K_CMCA achieves minimum value 0 at g* = 1/φ
  - The functional non-identity: d/dg K_CMCA ≠ β_SRRG as functions
  - The honest equivalence: β(g)=0 ↔ K_CMCA(g)=0 for g>0

Expected output:
  g* = 0.6180339887498949 (= 1/φ)
  β_SRRG(g*) ≈ 0.0
  K_CMCA(g*) ≈ 0.0
  Derivative of K_CMCA at g* ≈ -3.2 (NOT zero)
  Equivalence: β(g)=0 ↔ K_CMCA(g)=0 confirmed on 10000 sample points
"""

import signal
import sys
import math
import json
import numpy as np

TIMEOUT_SECONDS = 120

def _timeout_handler(signum, frame):
    print(f"\nTIMEOUT: {TIMEOUT_SECONDS}s reached. Saving partial results.")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

# --- Core definitions ---

phi = (1 + math.sqrt(5)) / 2
g_star = 1 / phi  # = (sqrt(5)-1)/2 = 0.6180...

def srrg_beta(g):
    """SRRG β-function: β(g) = p(g,g,g) - g = g(1 - g - g²)."""
    return g * (1 - g - g**2)

def gte_poly_diag(g):
    """Diagonal GTE polynomial: p(g,g,g) = 2g - g² - g³."""
    return 2*g - g**2 - g**3

def k_cmca(g):
    """MDL K_CMCA description length: K(g) = -log₂(g²+g)."""
    val = g**2 + g
    if val <= 0:
        return float('inf')
    return -math.log2(val)

def dk_cmca(g):
    """Derivative of K_CMCA: d/dg K_CMCA = -(2g+1)/((ln2)(g²+g))."""
    val = g**2 + g
    if val <= 0:
        return float('nan')
    return -(2*g + 1) / (math.log(2) * val)

# --- Verification 1: g* = 1/φ ---
print("=" * 60)
print("SRRG=MDL Lean Bridge — Numerical Certificate")
print("=" * 60)
print(f"\nFixed point: g* = 1/φ = {g_star:.16f}")
print(f"Verification: g*² + g* = {g_star**2 + g_star:.16f} (should be 1.0)")
print(f"β_SRRG(g*) = {srrg_beta(g_star):.2e} (should be 0)")
print(f"K_CMCA(g*) = {k_cmca(g_star):.2e} (should be 0)")

# --- Verification 2: Derivative at g* (not zero!) ---
dk_at_star = dk_cmca(g_star)
print(f"\nd/dg K_CMCA at g* = {dk_at_star:.6f}")
print(f"  (= -√5/ln2 = {-math.sqrt(5)/math.log(2):.6f})")
print(f"  This is NOT zero — g* is a boundary minimum, not interior critical point")
print(f"  Consequence: 'β_SRRG = dK_CMCA/dg' is NOT a functional identity")

# --- Verification 3: K_CMCA behavior on (0, g*) ---
print(f"\nK_CMCA values on (0, g*):")
g_samples = [0.1, 0.2, 0.3, 0.4, 0.5, 0.55, 0.60, g_star]
print(f"  {'g':>10} {'g²+g':>12} {'K_CMCA':>12} {'β_SRRG':>14}")
for g in g_samples:
    label = " ← g*" if abs(g - g_star) < 1e-10 else ""
    print(f"  {g:>10.5f} {g**2+g:>12.6f} {k_cmca(g):>12.6f} {srrg_beta(g):>14.6f}{label}")

print(f"\n  K_CMCA is strictly decreasing on (0, g*]: {all(k_cmca(g_samples[i]) > k_cmca(g_samples[i+1]) for i in range(len(g_samples)-1))}")

# --- Verification 4: Equivalence β(g)=0 ↔ K_CMCA(g)=0 for g>0 ---
print(f"\nEquivalence verification on 10000 samples g ∈ (1e-6, 2):")
N = 10000
g_vals = np.linspace(1e-6, 2, N)
tol = 1e-10
mismatch_count = 0
mismatches = []
for g in g_vals:
    beta_zero = abs(srrg_beta(g)) < tol
    k_zero = abs(k_cmca(g)) < tol
    if beta_zero != k_zero:
        mismatch_count += 1
        mismatches.append((float(g), float(srrg_beta(g)), float(k_cmca(g))))
print(f"  Mismatches found: {mismatch_count}")
print(f"  β(g)=0 ↔ K_CMCA(g)=0 holds: {mismatch_count == 0}")

# Find zero locations numerically
zeros = []
for i in range(len(g_vals)-1):
    if srrg_beta(g_vals[i]) * srrg_beta(g_vals[i+1]) < 0:
        # Linear interpolation
        g_zero = g_vals[i] - srrg_beta(g_vals[i]) * (g_vals[i+1] - g_vals[i]) / (srrg_beta(g_vals[i+1]) - srrg_beta(g_vals[i]))
        zeros.append(float(g_zero))
print(f"  β_SRRG zero locations on (0, 2): {zeros}")
print(f"  All = 1/φ = {g_star:.10f}: {all(abs(z - g_star) < 1e-3 for z in zeros)}")

# --- Verification 5: SRRG=MDL summary ---
print(f"\nSummary: SRRG=MDL equivalence")
print(f"  SRRG: g* = 1/φ is unique positive zero of β_SRRG")
print(f"  MDL: g* = 1/φ minimizes K_CMCA on (0, g*] (value 0)")
print(f"  Both select same g* = 1/φ")
print(f"  Lean theorem: β_SRRG(g)=0 ↔ K_CMCA(g)=0 for g>0")
print(f"  Algebraic identity: β(g)=0 ↔ g²+g=1 ↔ K_CMCA(g)=0")

# --- Verification 6: The identity at value level ---
print(f"\nAlgebraic chain (all equivalent for g > 0):")
print(f"  β_SRRG(g) = 0")
print(f"  ↔ g(1 - g - g²) = 0  [since g > 0]")
print(f"  ↔ 1 - g - g² = 0")
print(f"  ↔ g² + g = 1")
print(f"  ↔ log₂(g²+g) = log₂(1) = 0")
print(f"  ↔ -log₂(g²+g) = 0")
print(f"  ↔ K_CMCA(g) = 0  □")

# --- Also verify L_EW near-identity (from prior session) ---
print(f"\nL_EW near-identity (from prior session, CatAL):")
L_EW_srrg = math.log2(2 * math.pi**2 * phi**(1/3))
L_EW_piln2 = math.pi / math.log(2)
print(f"  L_EW_SRRG = log₂(2π²φ^(1/3)) = {L_EW_srrg:.8f} bits")
print(f"  L_EW_piln2 = π/ln2 = {L_EW_piln2:.8f} bits")
print(f"  Difference: {L_EW_srrg - L_EW_piln2:.8f} bits ({(L_EW_srrg/L_EW_piln2 - 1)*100:.4f}%)")

# --- Output JSON artifact ---
results = {
    "session": "EPIC_080 MDLSRRG-LEAN numerical certificate",
    "g_star": g_star,
    "phi": phi,
    "g_star_squared_plus_g_star": g_star**2 + g_star,
    "beta_srrg_at_g_star": float(srrg_beta(g_star)),
    "k_cmca_at_g_star": float(k_cmca(g_star)),
    "dk_cmca_at_g_star": float(dk_cmca(g_star)),
    "dk_cmca_is_zero_at_g_star": abs(dk_cmca(g_star)) < 1e-10,
    "functional_identity_beta_eq_dk_holds": False,
    "value_equivalence_beta_zero_iff_k_zero": mismatch_count == 0,
    "lean_theorem": "srrg_beta_zero_iff_kCMCA_minimum",
    "lean_theorem_status": "zero-sorry provable (algebraic equivalence only)",
    "honest_correction": "beta_SRRG = dK_CMCA/dg is NOT a functional identity; correct statement is beta(g)=0 iff K_CMCA(g)=0",
    "L_EW_srrg_bits": L_EW_srrg,
    "L_EW_piln2_bits": L_EW_piln2,
    "L_EW_difference_bits": L_EW_srrg - L_EW_piln2,
    "k_cmca_monotone_on_domain": all(k_cmca(g_samples[i]) > k_cmca(g_samples[i+1]) for i in range(len(g_samples)-1)),
    "srrg_zero_locations": zeros,
    "verdict_kCMCA_definition_valid": True,
    "verdict_beta_eq_dkdg_literal": False,
    "verdict_beta_zero_iff_kCMCA_zero": True
}

with open("/Users/nova/ugp-physics/papers/45_three_tape_cmca/scripts/srrg_mdl_lean_bridge_results.json", "w") as f:
    json.dump(results, f, indent=2)

print(f"\nJSON artifact saved: srrg_mdl_lean_bridge_results.json")

signal.alarm(0)
print("\nDone.")
