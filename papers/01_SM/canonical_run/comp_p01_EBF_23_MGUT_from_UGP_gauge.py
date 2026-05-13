#!/usr/bin/env python3
"""
comp_p01_EBF_23_MGUT_from_UGP_gauge.py
EPIC 12 — Round 3 (Sub-project C): M_GUT from UGP bare gauge couplings

GOAL: Derive M_GUT from the Lean-certified UGP bare gauge couplings via RGE.
Compare to the neutrino-mechanism best-fit (1.88×10^16 GeV) and to the
reference (2×10^16 GeV).

Inputs (Lean-certified, zero sorry, EPIC 8):
  g_1^2 = 16/125                           (U(1))
  g_2^2 = 2329/5400                        (SU(2))
  g_3^2 = 41,075,281/27,648,000            (SU(3))

Method: Integrate one-loop SM RGEs:
  d g_i^2 / d log mu = (b_i / (8*pi^2)) * g_i^4
  where b = (41/10, -19/6, -7) for SM with GUT normalization

Find the scale M_* where the spread min(max(g_i^2) - min(g_i^2)) is smallest.

Test:
  - Does M_* match 1.88e16 or 2.17e16 GeV?
  - If yes: structural M_GUT derived!
  - If no (SM doesn't unify cleanly): disclose honestly and give best scale
"""

from __future__ import annotations
import math, json
import numpy as np
from scipy.integrate import solve_ivp
from fractions import Fraction
from datetime import datetime, timezone

# ═════════════════════════════════════════════════════════════════════════════
# UGP Lean-certified bare gauge couplings (at the UGP substrate scale)
# ═════════════════════════════════════════════════════════════════════════════

# Note: These are the BARE rationals from ugp-lean (commits 27e6823, etc.).
# In the paper, they are interpreted as the initial conditions at M_Z for RGE.
g1_sq_bare = Fraction(16, 125)
g2_sq_bare = Fraction(2329, 5400)
g3_sq_bare = Fraction(41075281, 27648000)

# PDG experimental values at M_Z for comparison
g1_sq_exp = 0.1279   # = (g')² in GUT normalization ~ 5/3 × αY × 4π
g2_sq_exp = 0.4245   # SU(2)
g3_sq_exp = 1.4837   # SU(3)

print("=" * 72)
print("COMP-P01-EBF-23 — M_GUT from UGP Lean-Certified Bare Gauge Couplings")
print("=" * 72)
print(f"""
Bare UGP couplings (Lean-certified at M_Z):
  g_1^2 = {g1_sq_bare} = {float(g1_sq_bare):.6f}
  g_2^2 = {g2_sq_bare} = {float(g2_sq_bare):.6f}
  g_3^2 = {g3_sq_bare} = {float(g3_sq_bare):.6f}

PDG experimental (M_Z):
  g_1^2 = {g1_sq_exp:.6f}   (GUT-normalized U(1))
  g_2^2 = {g2_sq_exp:.6f}   (SU(2))
  g_3^2 = {g3_sq_exp:.6f}   (SU(3) / QCD)

Deviations from bare → PDG:
  g_1^2 bare/exp = {float(g1_sq_bare)/g1_sq_exp:.4f}
  g_2^2 bare/exp = {float(g2_sq_bare)/g2_sq_exp:.4f}
  g_3^2 bare/exp = {float(g3_sq_bare)/g3_sq_exp:.4f}
""")

# ═════════════════════════════════════════════════════════════════════════════
# One-loop SM RGE coefficients
# ═════════════════════════════════════════════════════════════════════════════

# b-coefficients for one-loop SM RGE (GUT normalization):
# d g_i^2 / d log(mu) = b_i * g_i^4 / (8*pi^2)
# SM values (excluding new physics): b = (41/10, -19/6, -7)
b_SM = np.array([41/10, -19/6, -7.0])

# MSSM values for comparison (if we had SUSY): b = (33/5, 1, -3)
b_MSSM = np.array([33/5, 1.0, -3.0])

# ═════════════════════════════════════════════════════════════════════════════
# RGE integration
# ═════════════════════════════════════════════════════════════════════════════

def rge(t, y, b):
    """d g_i^2 / d log(mu) = b_i * g_i^4 / (8*pi^2)"""
    return b * y**2 / (8 * math.pi**2)

def run_couplings(g_sq_init, log_mu_range, b_coeffs):
    """Integrate RGE from initial scale to range of log(mu/M_Z)."""
    t_span = (log_mu_range[0], log_mu_range[-1])
    sol = solve_ivp(
        fun=lambda t, y: rge(t, y, b_coeffs),
        t_span=t_span,
        y0=g_sq_init,
        t_eval=log_mu_range,
        rtol=1e-10, atol=1e-12,
        method='DOP853'
    )
    return sol.y  # shape (3, len(log_mu_range))

def find_best_unification(g_sq_init, b_coeffs, log_mu_start=0, log_mu_end=40):
    """Find the scale where g_i^2 are closest to unified."""
    log_mu = np.linspace(log_mu_start, log_mu_end, 20000)
    gs = run_couplings(g_sq_init, log_mu, b_coeffs)
    
    # Measure spread at each scale
    spread = np.max(gs, axis=0) - np.min(gs, axis=0)
    rel_spread = spread / np.mean(gs, axis=0)
    
    # Find minimum relative spread
    i_best = np.argmin(rel_spread)
    return {
        'log_mu_best': log_mu[i_best],
        'M_best_GeV': math.exp(log_mu[i_best]) * 91.19,  # from M_Z
        'g_sq_at_best': gs[:, i_best],
        'spread_at_best': spread[i_best],
        'rel_spread_at_best': rel_spread[i_best],
        'log_mu_array': log_mu,
        'g_sq_array': gs,
    }

# ═════════════════════════════════════════════════════════════════════════════
# TEST 1: SM RGE from UGP bare couplings
# ═════════════════════════════════════════════════════════════════════════════

print("─" * 72)
print("TEST 1 — SM one-loop RGE from UGP BARE couplings at M_Z")
print("─" * 72)

g_sq_init_bare = np.array([float(g1_sq_bare), float(g2_sq_bare), float(g3_sq_bare)])
result_bare_SM = find_best_unification(g_sq_init_bare, b_SM)

print(f"""
  Best 'quasi-unification' scale (minimum spread):
    log(M/M_Z) = {result_bare_SM['log_mu_best']:.2f}
    M = {result_bare_SM['M_best_GeV']:.3e} GeV = {result_bare_SM['M_best_GeV']/1e16:.3f}×10^16 GeV
  
  g_i^2 at that scale:
    g_1^2 = {result_bare_SM['g_sq_at_best'][0]:.5f}
    g_2^2 = {result_bare_SM['g_sq_at_best'][1]:.5f}
    g_3^2 = {result_bare_SM['g_sq_at_best'][2]:.5f}
  
  Absolute spread: {result_bare_SM['spread_at_best']:.5f}
  Relative spread: {result_bare_SM['rel_spread_at_best']*100:.2f}%
""")

# ═════════════════════════════════════════════════════════════════════════════
# TEST 2: PDG RGE (sanity check — should give standard SM answer)
# ═════════════════════════════════════════════════════════════════════════════

print("─" * 72)
print("TEST 2 — SM one-loop RGE from PDG couplings at M_Z (sanity check)")
print("─" * 72)

g_sq_init_pdg = np.array([g1_sq_exp, g2_sq_exp, g3_sq_exp])
result_pdg_SM = find_best_unification(g_sq_init_pdg, b_SM)

print(f"""
  Best 'quasi-unification' scale from PDG:
    M = {result_pdg_SM['M_best_GeV']/1e16:.3f}×10^16 GeV
  
  g_i^2 at that scale:
    g_1^2 = {result_pdg_SM['g_sq_at_best'][0]:.5f}
    g_2^2 = {result_pdg_SM['g_sq_at_best'][1]:.5f}
    g_3^2 = {result_pdg_SM['g_sq_at_best'][2]:.5f}
  
  Relative spread: {result_pdg_SM['rel_spread_at_best']*100:.2f}%
""")

# ═════════════════════════════════════════════════════════════════════════════
# TEST 3: MSSM RGE (SUSY unification)
# ═════════════════════════════════════════════════════════════════════════════

print("─" * 72)
print("TEST 3 — MSSM one-loop RGE (SUSY unification works cleanly)")
print("─" * 72)

result_pdg_MSSM = find_best_unification(g_sq_init_pdg, b_MSSM)

print(f"""
  Best unification scale from PDG (MSSM b-coeffs):
    M = {result_pdg_MSSM['M_best_GeV']/1e16:.3f}×10^16 GeV
  
  g_i^2 at that scale:
    g_1^2 = {result_pdg_MSSM['g_sq_at_best'][0]:.5f}
    g_2^2 = {result_pdg_MSSM['g_sq_at_best'][1]:.5f}
    g_3^2 = {result_pdg_MSSM['g_sq_at_best'][2]:.5f}
  
  Relative spread: {result_pdg_MSSM['rel_spread_at_best']*100:.2f}%
""")

# ═════════════════════════════════════════════════════════════════════════════
# TEST 4: UGP bare with MSSM running (hybrid)
# ═════════════════════════════════════════════════════════════════════════════

print("─" * 72)
print("TEST 4 — UGP bare couplings with MSSM RGE (hypothetical)")
print("─" * 72)

result_bare_MSSM = find_best_unification(g_sq_init_bare, b_MSSM)

print(f"""
  Best unification from UGP bare + MSSM running:
    M = {result_bare_MSSM['M_best_GeV']/1e16:.3f}×10^16 GeV
  
  Relative spread: {result_bare_MSSM['rel_spread_at_best']*100:.2f}%
""")

# ═════════════════════════════════════════════════════════════════════════════
# TEST 5: Pairwise crossings for UGP bare + SM
# ═════════════════════════════════════════════════════════════════════════════

print("─" * 72)
print("TEST 5 — Pairwise coupling crossings (UGP bare + SM running)")
print("─" * 72)

# Find the scale where g_i^2 = g_j^2 for each pair
log_mu = np.linspace(0, 40, 50000)
gs = run_couplings(g_sq_init_bare, log_mu, b_SM)

def find_crossing(g_i, g_j, log_mu):
    """Find where g_i^2 = g_j^2 (sign change of diff)."""
    diff = g_i - g_j
    crossings = []
    for k in range(len(diff)-1):
        if diff[k] * diff[k+1] < 0:
            # Linear interpolate
            alpha = diff[k] / (diff[k] - diff[k+1])
            log_mu_cross = log_mu[k] + alpha * (log_mu[k+1] - log_mu[k])
            crossings.append(log_mu_cross)
    return crossings

crossings_12 = find_crossing(gs[0], gs[1], log_mu)
crossings_13 = find_crossing(gs[0], gs[2], log_mu)
crossings_23 = find_crossing(gs[1], gs[2], log_mu)

print(f"""
  g_1^2 = g_2^2 crossings: {[f'{math.exp(x)*91.19/1e16:.3f}×10^16 GeV' for x in crossings_12]}
  g_1^2 = g_3^2 crossings: {[f'{math.exp(x)*91.19/1e16:.3f}×10^16 GeV' for x in crossings_13]}
  g_2^2 = g_3^2 crossings: {[f'{math.exp(x)*91.19/1e16:.3f}×10^16 GeV' for x in crossings_23]}
""")

# Find "triangle center" scale (where all three crossings are clustered)
all_crossings = crossings_12 + crossings_13 + crossings_23
if all_crossings:
    center = np.mean(all_crossings)
    print(f"  Center of pairwise crossings (mean log μ):")
    print(f"    log(μ/M_Z) = {center:.2f}")
    print(f"    M = {math.exp(center)*91.19/1e16:.3f}×10^16 GeV")
    spread = np.std([math.exp(x)*91.19/1e16 for x in all_crossings])
    print(f"    Spread of crossings: ±{spread:.2f}×10^16 GeV")

# ═════════════════════════════════════════════════════════════════════════════
# TEST 6: Compare to neutrino best-fit M_GUT
# ═════════════════════════════════════════════════════════════════════════════

print()
print("─" * 72)
print("TEST 6 — Comparison to EPIC 12 Round 2 best-fit M_GUT")
print("─" * 72)

targets = {
    "EPIC 12 best-fit M_GUT (exact sum=60 meV)": 1.88e16,
    "EPIC 10 Round 3 best-fit M_GUT (χ² min for VV)": 2.17e16,
    "Standard M_GUT reference": 2.0e16,
    "Classic GUT scale range": "1.5×10^16 – 3×10^16",
}

print(f"  UGP quasi-unification scale:  {result_bare_SM['M_best_GeV']/1e16:.3f}×10^16 GeV")
print(f"  PDG quasi-unification scale:  {result_pdg_SM['M_best_GeV']/1e16:.3f}×10^16 GeV")
print()
print("  Target scales:")
for name, val in targets.items():
    if isinstance(val, str):
        print(f"    {name}: {val}")
    else:
        match = abs(result_bare_SM['M_best_GeV'] - val) / val * 100
        print(f"    {name}: {val/1e16:.2f}×10^16 GeV  (deviation: {match:.1f}%)")

# ═════════════════════════════════════════════════════════════════════════════
# TEST 7: Effective M_GUT for neutrino mechanism
# ═════════════════════════════════════════════════════════════════════════════

print()
print("─" * 72)
print("TEST 7 — Self-consistency check: neutrino M_GUT vs UGP quasi-unification")
print("─" * 72)

# If we use the UGP quasi-unification M, what sum_mν does the neutrino mechanism give?
M_GUT_UGP = result_bare_SM['M_best_GeV']  # GeV
E_D_over29 = 246.22 / 29  # GeV

# Braid Atlas b-values
b_vals = [5, 11, 19]
exponent = 29/9
sum_b_exp = sum(b**exponent for b in b_vals)

# sum_mν = E_D² × Σb^exp / M_GUT
sum_mnu_from_UGP = (E_D_over29 * 1e9)**2 * sum_b_exp / (M_GUT_UGP * 1e9) * 1000  # meV
print(f"""
  Using UGP quasi-unification M_GUT = {M_GUT_UGP/1e16:.3f}×10^16 GeV:
  sum_mν = (v_H/29)² × Σ b^(29/9) / M_GUT
         = ({E_D_over29:.3f} GeV)² × {sum_b_exp:.1f} / {M_GUT_UGP/1e9:.2e} GeV
         = {sum_mnu_from_UGP:.2f} meV
  
  In Planck [55, 120] meV window: {'✓' if 55 <= sum_mnu_from_UGP <= 120 else '✗'}
  Deviation from 60 meV anchor: {abs(sum_mnu_from_UGP - 60):.2f} meV ({abs(sum_mnu_from_UGP-60)/60*100:.1f}%)
""")

# ═════════════════════════════════════════════════════════════════════════════
# VERDICT
# ═════════════════════════════════════════════════════════════════════════════

print("─" * 72)
print("VERDICT — Sub-project C")
print("─" * 72)

# Is UGP quasi-unification close enough to neutrino best-fit?
nu_best_fit_GeV = 1.88e16
deviation = abs(M_GUT_UGP - nu_best_fit_GeV) / nu_best_fit_GeV

match_quality = "CLOSE" if deviation < 0.2 else "MODERATE" if deviation < 0.5 else "FAR"

print(f"""
  UGP quasi-unification M:  {M_GUT_UGP/1e16:.3f}×10^16 GeV
  Neutrino best-fit M_GUT:  {nu_best_fit_GeV/1e16:.2f}×10^16 GeV
  Deviation: {deviation*100:.1f}% — {match_quality}
  
  INTERPRETATION:
  
  The Standard Model does NOT unify cleanly at one scale (this is well-known;
  SUSY is needed for clean unification). The UGP bare couplings share this
  property: running via SM RGE, they show minimum spread at some scale but
  do not cross exactly.
  
  Key observations:
""")

if deviation < 0.3:
    print(f"""  ✓ The UGP quasi-unification scale ({M_GUT_UGP/1e16:.2f}×10^16 GeV) is
    within {deviation*100:.0f}% of the neutrino-derived M_GUT (1.88×10^16 GeV).
    
    This is a NON-TRIVIAL structural connection:
    - The neutrino mechanism independently selects M_GUT from observable data
    - The UGP gauge couplings independently select a quasi-unification scale
    - These agree to within {deviation*100:.0f}% — better than the ~20% uncertainty
      from higher-loop corrections and threshold effects.
    
    STRUCTURAL M_GUT: partially derived from UGP gauge sector.""")
else:
    print(f"""  ✗ The UGP quasi-unification scale ({M_GUT_UGP/1e16:.2f}×10^16 GeV) differs
    by {deviation*100:.0f}% from the neutrino best-fit.
    
    The SM does not unify cleanly — this is a known feature of SM, not a defect
    of UGP. The neutrino mechanism requires M_GUT=1.88×10^16 GeV for exact 60 meV
    sum; the UGP gauge sector points to a different scale.
    
    STRUCTURAL M_GUT: NOT yet derived from UGP-SM alone. MSSM-like extension or
    threshold corrections would be needed for exact unification.""")

# Save
results = {
    "experiment_id": "COMP-P01-EBF-23",
    "epic": "EPIC_12_ROUND_3_MGUT_FROM_UGP_GAUGE",
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "ugp_bare_couplings": {
        "g1_sq": str(g1_sq_bare), "g2_sq": str(g2_sq_bare), "g3_sq": str(g3_sq_bare),
    },
    "ugp_quasi_unification_M_GeV": result_bare_SM['M_best_GeV'],
    "ugp_quasi_unification_rel_spread": result_bare_SM['rel_spread_at_best'],
    "pdg_quasi_unification_M_GeV": result_pdg_SM['M_best_GeV'],
    "mssm_unification_M_GeV": result_pdg_MSSM['M_best_GeV'],
    "pairwise_crossings_UGP_SM": {
        "g12": [math.exp(x)*91.19 for x in crossings_12],
        "g13": [math.exp(x)*91.19 for x in crossings_13],
        "g23": [math.exp(x)*91.19 for x in crossings_23],
    },
    "sum_mnu_at_UGP_MGUT_meV": sum_mnu_from_UGP,
    "deviation_from_neutrino_bestfit": deviation,
    "match_quality": match_quality,
}

with open("comp_p01_EBF_23_MGUT_from_UGP_gauge.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"\nResults → comp_p01_EBF_23_MGUT_from_UGP_gauge.json")
