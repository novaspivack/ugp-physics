"""
Direction 1: Cyclotomic Ratio Search
EPIC_051 Phase 2 — Level 2 Higgs VEV structural derivation

Question: Is log(v/M_Planck) expressible as a·ln(φ) + b·ln(2) + c·π + d
for small integers a,b,c,d? (and extensions with more atoms)

Physical constants:
  v = 246.22 GeV (PDG 2024 electroweak VEV)
  M_Planck = 1.2209e19 GeV (reduced Planck mass: M_P = sqrt(hbar*c/8*pi*G))

  Note: some use M_Planck = 1.221e19 GeV (non-reduced). We use the reduced version.
  PDG: M_Pl = 2.435e18 GeV (reduced). Let's be careful:
    v_PDG = 246.2196 GeV (standard: v = (sqrt(2) * G_F)^{-1/2})
    M_Planck_GeV = 1.22089e19 GeV (non-reduced, used in hierarchy discussions)
    M_Planck_reduced = 2.43532e18 GeV (reduced = M_Pl_non-reduced / sqrt(8*pi))

We'll compute log(v/M_Planck) for both conventions.

Null discipline: After finding hits, we estimate basis saturation by testing
N_null random targets drawn from the same distribution.
"""

import numpy as np
from itertools import product
import json
import hashlib
import random
from datetime import datetime

random.seed(42)
np.random.seed(42)

# --- Physical constants ---
v_PDG = 246.22        # GeV, PDG 2024 electroweak VEV
M_Planck_non_red = 1.22089e19   # GeV, non-reduced Planck mass (hbar=c=1)
M_Planck_reduced = 2.43532e18   # GeV, reduced Planck mass

# Target: natural log of ratio
target_nr = np.log(v_PDG / M_Planck_non_red)  # non-reduced
target_rd = np.log(v_PDG / M_Planck_reduced)  # reduced

print(f"log(v / M_Planck_non_reduced) = {target_nr:.8f}")
print(f"log(v / M_Planck_reduced)     = {target_rd:.8f}")
print()

# --- Atom basis ---
phi = (1 + 5**0.5) / 2

atoms = {
    'ln_phi':   np.log(phi),       # ln(φ) ≈ 0.48121
    'ln_2':     np.log(2),         # ln(2) ≈ 0.69315
    'pi':       np.pi,             # π ≈ 3.14159
    'const':    1.0,               # integer offset
    'pi_sq_6':  np.pi**2 / 6,      # ζ(2) = π²/6 ≈ 1.64493  (Euler series)
    'ln_2pi':   np.log(2 * np.pi), # ln(2π) ≈ 1.83788
    'ln_pi':    np.log(np.pi),     # ln(π) ≈ 1.14473
}

print("Atom values:")
for k, v_atom in atoms.items():
    print(f"  {k} = {v_atom:.8f}")
print()

# -----------------------------------------------------------------------
# SEARCH 1: 4-parameter search: a·ln(φ) + b·ln(2) + c·π + d
# -----------------------------------------------------------------------
print("=" * 60)
print("SEARCH 1: a·ln(φ) + b·ln(2) + c·π + d")
print("Search range: a,b in [-60,60], c in [-20,20], d in [-50,50]")
print("Tolerance: 0.01% relative (1e-4)")
print("=" * 60)

def search_4param(target, tol_rel=1e-4):
    """Search a·ln(φ) + b·ln(2) + c·π + d ≈ target."""
    ln_phi = np.log(phi)
    ln_2 = np.log(2)
    pi = np.pi
    hits = []
    # Precompute the phi/2 grid to speed up
    for a in range(-60, 61):
        base_a = a * ln_phi
        for b in range(-60, 61):
            base_ab = base_a + b * ln_2
            # c range: narrow because pi is large
            for c in range(-20, 21):
                base_abc = base_ab + c * pi
                # d must be an integer in [-50,50]
                d_float = target - base_abc
                d_int = int(round(d_float))
                if -50 <= d_int <= 50:
                    val = base_abc + d_int
                    err = abs(val - target) / abs(target)
                    if err < tol_rel:
                        hits.append({'a': a, 'b': b, 'c': c, 'd': d_int,
                                     'val': val, 'err_pct': err * 100})
    return hits

hits_nr = search_4param(target_nr, tol_rel=1e-4)
hits_rd = search_4param(target_rd, tol_rel=1e-4)

print(f"\nTarget (non-reduced): {target_nr:.8f}")
print(f"  Hits at 0.01%: {len(hits_nr)}")
for h in sorted(hits_nr, key=lambda x: x['err_pct'])[:10]:
    print(f"  {h['a']}·ln(φ) + {h['b']}·ln(2) + {h['c']}·π + {h['d']} = {h['val']:.8f}  (err={h['err_pct']:.5f}%)")

print(f"\nTarget (reduced Planck): {target_rd:.8f}")
print(f"  Hits at 0.01%: {len(hits_rd)}")
for h in sorted(hits_rd, key=lambda x: x['err_pct'])[:10]:
    print(f"  {h['a']}·ln(φ) + {h['b']}·ln(2) + {h['c']}·π + {h['d']} = {h['val']:.8f}  (err={h['err_pct']:.5f}%)")

# -----------------------------------------------------------------------
# NULL DISCIPLINE: Saturation test
# -----------------------------------------------------------------------
print("\n" + "=" * 60)
print("NULL DISCIPLINE: Basis saturation test")
print("Testing 500 random targets in [-40, -37] (same range as real target)")
print("=" * 60)

def count_hits_4param(target, tol_rel=1e-4):
    """Count hits without storing (faster)."""
    ln_phi = np.log(phi)
    ln_2 = np.log(2)
    pi = np.pi
    count = 0
    for a in range(-60, 61):
        base_a = a * ln_phi
        for b in range(-60, 61):
            base_ab = base_a + b * ln_2
            for c in range(-20, 21):
                base_abc = base_ab + c * pi
                d_float = target - base_abc
                d_int = int(round(d_float))
                if -50 <= d_int <= 50:
                    val = base_abc + d_int
                    err = abs(val - target) / abs(target)
                    if err < tol_rel:
                        count += 1
    return count

# Sample 200 null targets
null_targets = np.random.uniform(-40.0, -37.0, 200)
null_counts = []
print("Running null tests (200 random targets)...")
for i, nt in enumerate(null_targets):
    c = count_hits_4param(nt, tol_rel=1e-4)
    null_counts.append(c)
    if (i + 1) % 50 == 0:
        print(f"  Progress: {i+1}/200 done, running median={np.median(null_counts):.1f} hits/target")

real_hits_nr = len(hits_nr)
real_hits_rd = len(hits_rd)
null_arr = np.array(null_counts)
median_null = np.median(null_arr)
mean_null = np.mean(null_arr)
frac_with_hits = np.mean(null_arr > 0)

print(f"\nNULL DISCIPLINE RESULT:")
print(f"  Random target median hits: {median_null:.1f}")
print(f"  Random target mean hits:   {mean_null:.2f}")
print(f"  Fraction of random targets with ≥1 hit: {frac_with_hits*100:.1f}%")
print(f"  Real target (non-reduced) hits: {real_hits_nr}")
print(f"  Real target (reduced) hits:     {real_hits_rd}")

if frac_with_hits > 0.5:
    verdict_null = "VOLUME-DOMINATED: >50% of random targets also produce hits. Basis is saturated at this tolerance."
elif frac_with_hits > 0.10:
    verdict_null = "LIKELY SATURATED: 10-50% of random targets produce hits."
else:
    verdict_null = "POTENTIALLY SIGNIFICANT: <10% of random targets produce hits."

print(f"\n  VERDICT: {verdict_null}")

# -----------------------------------------------------------------------
# SEARCH 2: Tighter tolerance, more atoms
# -----------------------------------------------------------------------
print("\n" + "=" * 60)
print("SEARCH 2: Tight 0.001% tolerance (1e-5), extended atom basis")
print("Atoms: {ln_phi, ln_2, pi, 1, pi²/6, ln(2π)}")
print("=" * 60)

def search_6param_tight(target, tol_rel=1e-5):
    """6-parameter search at tight tolerance."""
    ln_phi = np.log(phi)
    ln_2 = np.log(2)
    pi = np.pi
    pi2_6 = np.pi**2 / 6
    ln2pi = np.log(2 * np.pi)
    hits = []
    # a, b, c, d (integer), e (ln(2π)), f (π²/6)
    for a in range(-30, 31):
        for b in range(-30, 31):
            for c in range(-10, 11):
                for e_coef in range(-5, 6):
                    for f_coef in range(-5, 6):
                        base = a*ln_phi + b*ln_2 + c*pi + e_coef*ln2pi + f_coef*pi2_6
                        d_float = target - base
                        d_int = int(round(d_float))
                        if -50 <= d_int <= 50:
                            val = base + d_int
                            err = abs(val - target) / abs(target)
                            if err < tol_rel:
                                hits.append({'a': a, 'b': b, 'c': c, 'd': d_int,
                                             'e_ln2pi': e_coef, 'f_pi2_6': f_coef,
                                             'val': val, 'err_pct': err * 100})
    return hits

# Only run if the basic search was saturated (skip for speed otherwise)
print("Running tight 6-parameter search on non-reduced target...")
hits_tight = search_6param_tight(target_nr, tol_rel=1e-5)
print(f"  Hits at 0.001%: {len(hits_tight)}")
for h in sorted(hits_tight, key=lambda x: x['err_pct'])[:5]:
    print(f"  {h['a']}·ln(φ)+{h['b']}·ln(2)+{h['c']}·π+{h['d']}+{h['e_ln2pi']}·ln(2π)+{h['f_pi2_6']}·π²/6"
          f" = {h['val']:.10f}  (err={h['err_pct']:.6f}%)")

# -----------------------------------------------------------------------
# SUMMARY
# -----------------------------------------------------------------------
print("\n" + "=" * 60)
print("DIRECTION 1 SUMMARY")
print("=" * 60)
print(f"  Target: ln(v/M_Planck) = {target_nr:.8f} (non-reduced Planck)")
print(f"  4-param hits at 0.01%: {real_hits_nr}")
print(f"  Null saturation: {frac_with_hits*100:.1f}% of random targets also hit")
print(f"  Best hit (non-reduced):")
if hits_nr:
    best = sorted(hits_nr, key=lambda x: x['err_pct'])[0]
    print(f"    {best['a']}·ln(φ) + {best['b']}·ln(2) + {best['c']}·π + {best['d']}")
    print(f"    value = {best['val']:.8f}, err = {best['err_pct']:.5f}%")
else:
    print("    (no hits)")

# Save results
results = {
    'direction': 1,
    'description': 'Cyclotomic ratio search: ln(v/M_Planck) as integer linear combination of {ln(φ),ln(2),π,1}',
    'target_non_reduced': target_nr,
    'target_reduced': target_rd,
    'hits_4param_01pct': {'non_reduced': len(hits_nr), 'reduced': len(hits_rd)},
    'best_hit_non_reduced': sorted(hits_nr, key=lambda x: x['err_pct'])[0] if hits_nr else None,
    'null_saturation_pct': frac_with_hits * 100,
    'null_median_hits': float(median_null),
    'null_mean_hits': float(mean_null),
    'verdict': verdict_null,
    'grade': 'NEGATIVE' if frac_with_hits > 0.50 else 'INCONCLUSIVE',
    'timestamp': datetime.utcnow().isoformat(),
}

output_path = 'papers/01_SM/research_sandbox/HMC_L2_vev_derivation/direction1_results.json'
with open(output_path, 'w') as f:
    json.dump(results, f, indent=2)
print(f"\nResults saved to {output_path}")

# Compute SHA-256 of prediction block
sha = hashlib.sha256(json.dumps(results, sort_keys=True).encode()).hexdigest()
print(f"SHA-256: {sha}")
