"""
Null-discipline test for the EW VEV PSC formula.

Our formula: v_PSC = v_PDG / sqrt((ln2/pi) * log2(2*pi**2 * phi**(1/N_gen)))
= 246.16 GeV (−0.024% from v_PDG)

Test: among all structural formulas of similar complexity over the UGP atom basis,
how many achieve <0.024% accuracy? If saturation << 1%, the match is structural.
"""

import numpy as np
from itertools import product
import json

phi = (1+5**0.5)/2; pi = np.pi; ln2 = np.log(2)
v_PDG = 246.22  # GeV
N_gen = 3

# Our formula precision
our_L_EW = np.log2(2*pi**2 * phi**(1/N_gen))
our_v = v_PDG / (ln2/pi * our_L_EW)**0.5
our_error = abs(our_v - v_PDG)/v_PDG
print(f"Our formula: L_EW = {our_L_EW:.8f} bits")
print(f"Our v_PSC = {our_v:.6f} GeV ({our_error*100:+.4f}% from v_PDG)")

# The PSC formula maps L_EW → v via: v = v_PDG / sqrt((ln2/pi) * L_EW)
# So we need to find how many L_EW values land within our_error of L_EW* = pi/ln2

# L_EW* = pi/ln2 (exact self-referential closure target)
L_target = pi/ln2
tolerance = our_error  # 0.000240 = 0.024%

# The formula structure: L_EW = log2(Vol × phi^(something))
# where Vol is a geometric volume and phi^something is the SRRG correction

# ATOM BASIS for the formula (UGP-structural atoms):
atoms = {
    'phi': phi, '1/phi': 1/phi, 'phi^2': phi**2,
    'pi': pi, '2pi': 2*pi, 'pi^2': pi**2, '2pi^2': 2*pi**2,
    'e': np.e, 'e^pi': np.e**pi, 'sqrt_e': np.e**0.5,
    'ln2': ln2, 'ln_phi': np.log(phi), 'ln_pi': np.log(pi),
    '2': 2.0, '3': 3.0, '4': 4.0, '6': 6.0, '8': 8.0, '12': 12.0,
    'N_gen': float(N_gen), '1/N_gen': 1.0/N_gen,
    'IPT': 1 + np.log(phi)/(2*np.log(2*pi)),
    'sqrt2': 2**0.5, 'sqrt3': 3**0.5,
}

# Generate candidate formulas of the form: log2(A * phi^(B))
# where A is a product of atom powers and B is a rational
# LEVEL 1: log2(A) where A is a single atom or simple product

# First: what fraction of random L_EW values in the "physically reasonable range" 
# [L_target × 0.9, L_target × 1.1] land within our tolerance?
n_random = 1_000_000
L_random = np.random.uniform(L_target * 0.9, L_target * 1.1, n_random)
# Map to v: v = v_PDG / sqrt((ln2/pi) * L)
v_random = v_PDG / (ln2/pi * L_random)**0.5
hits_random = np.sum(np.abs(v_random - v_PDG)/v_PDG < tolerance)
saturation_random = hits_random / n_random
print(f"\nRandom L_EW saturation (uniform [0.9, 1.1] × L_target): {saturation_random*100:.2f}%")

# LEVEL 2: Enumerate actual structural formulas
# Form: L_EW = log2(A × phi^α) where:
# A ∈ {2π², 4π, 2π, π², π, 4, 2, 8, 12, 2π³}
# α ∈ {1/N_gen, 1/6, 2/N_gen, 1/N_gen², 1/4, 1/2, N_gen/4, ...}

volume_atoms = [
    ('2pi^2', 2*pi**2),
    ('4pi', 4*pi),
    ('2pi', 2*pi),
    ('pi^2', pi**2),
    ('pi', pi),
    ('4', 4.0),
    ('8', 8.0),
    ('12', 12.0),
    ('2pi^3', 2*pi**3),
    ('6pi', 6*pi),
    ('3pi', 3*pi),
    ('pi^3', pi**3),
    ('e^pi', np.e**pi),
    ('2e^pi', 2*np.e**pi),
    ('pi*phi', pi*phi),
    ('2pi*phi', 2*pi*phi),
    ('pi^2*phi', pi**2*phi),
    ('phi^2*pi', phi**2*pi),
]

alpha_atoms = [
    ('1/3', 1/3),
    ('1/6', 1/6),
    ('2/3', 2/3),
    ('1/4', 1/4),
    ('1/2', 1/2),
    ('3/4', 3/4),
    ('1', 1.0),
    ('1/9', 1/9),
    ('1/N_gen', 1/N_gen),
    ('1/(2N_gen)', 1/(2*N_gen)),
    ('2/N_gen', 2/N_gen),
    ('Λ_N', np.log(phi)/np.log(2*pi)),  # Norfleet's constant
    ('IPT/3', (1 + np.log(phi)/(2*np.log(2*pi)))/3),
    ('0', 0.0),  # no phi correction
    ('ln(phi)/pi', np.log(phi)/pi),
    ('1/pi', 1/pi),
]

# Enumerate all combinations and count hits within tolerance
n_total = len(volume_atoms) * len(alpha_atoms)
n_hits = 0
hits = []

for v_name, vol in volume_atoms:
    for a_name, alpha in alpha_atoms:
        try:
            if alpha == 0:
                L = np.log2(vol)
            else:
                L = np.log2(vol * phi**alpha)
            v_pred = v_PDG / (ln2/pi * L)**0.5 if ln2/pi*L > 0 else None
            if v_pred and abs(v_pred - v_PDG)/v_PDG < tolerance:
                n_hits += 1
                hits.append({
                    'formula': f"log₂({v_name} × φ^{a_name})",
                    'L_EW': L,
                    'v_pred': v_pred,
                    'error_pct': (v_pred - v_PDG)/v_PDG * 100,
                    'is_our_formula': (v_name == '2pi^2' and a_name == '1/3'),
                })
        except:
            pass

saturation = n_hits / n_total
print(f"\nStructural formula enumeration:")
print(f"  Total candidates: {n_total}")
print(f"  Hits within {tolerance*100:.4f}%: {n_hits}")
print(f"  Saturation: {saturation*100:.2f}%")
print(f"\nHits found:")
for h in hits:
    marker = " ← OUR FORMULA" if h.get('is_our_formula') else ""
    print(f"  {h['formula']}: L={h['L_EW']:.4f} bits, v={h['v_pred']:.4f} GeV ({h['error_pct']:+.4f}%){marker}")

# The null-discipline threshold is < 1% saturation
if saturation < 0.01:
    verdict = "STRUCTURAL (saturation < 1% — match is NOT coincidental)"
elif saturation < 0.05:
    verdict = "MARGINAL (saturation 1-5% — borderline structural)"
else:
    verdict = "COINCIDENTAL (saturation > 5% — match is volume-dominated)"
print(f"\nVERDICT: {verdict}")

# Also test at broader tolerance (1%):
n_hits_1pct = sum(1 for v_name, vol in volume_atoms for a_name, alpha in alpha_atoms
                  if alpha >= 0 and (ln2/pi*np.log2(vol*phi**alpha if alpha > 0 else vol)) > 0
                  and abs(v_PDG / (ln2/pi * np.log2(vol*phi**alpha if alpha > 0 else vol))**0.5 - v_PDG)/v_PDG < 0.01)
print(f"\nAt 1% tolerance: {n_hits_1pct}/{n_total} hits ({n_hits_1pct/n_total*100:.1f}% saturation)")

import json
json.dump({
    'our_formula_error_pct': our_error*100,
    'n_candidates': n_total,
    'n_hits_at_our_tolerance': n_hits,
    'saturation_pct': saturation*100,
    'verdict': verdict,
    'hits': hits,
}, open("null_discipline_vev_formula.json","w"), indent=2)
print("Saved null_discipline_vev_formula.json")
