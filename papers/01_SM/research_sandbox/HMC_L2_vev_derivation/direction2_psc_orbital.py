"""
Direction 2: PSC Orbital Counting at EW Scale
EPIC_051 Phase 2 — Level 2 Higgs VEV structural derivation

Hypothesis: The EW phase transition corresponds to a PSC orbit structure
(D_EW, ℓ_EW) such that:
  v = (exp(−log₂(D/ℓ) · ln2) · M_Planck⁴)^(1/4) = M_Planck · (D/ℓ)^(-1/4)

The PSC cosmological constant derivation uses:
  D₁ = 2⁴ × 5³ = 2000 (orbital degrees of freedom × 5³)
  wait: D₁ = D_1 was originally stated as 2000 = 2^4 * 5^3... no, actually:
  From the paper: D₁ = 24 × 5³? Let me use: L_model = log₂(2000/3) = log₂(D₁/orbit_length)
  with D₁ = 2000, orbit_length = 3.

For EW scale: we seek integers D, ℓ from UGP-motivated families:
  D ∈ {2^n · 3^m · 5^p : 0 ≤ n,m,p ≤ 6}
  ℓ ∈ {1, 2, ..., 20}

Physical constants:
  v_PDG = 246.22 GeV
  M_Planck = 1.22089e19 GeV (non-reduced)

This script computes v(D,ℓ) = M_Planck · (D/ℓ)^(-1/4) for all pairs
and checks which (if any) land near 246.22 GeV.

We also check the formula analytically: what D/ℓ would be required?
"""

import numpy as np
import json
import hashlib
from datetime import datetime
from itertools import product

# --- Physical constants ---
v_PDG = 246.22       # GeV
M_Planck = 1.22089e19  # GeV (non-reduced)

# --- Analytical calculation ---
# v = M_Planck · (D/ℓ)^(-1/4)
# D/ℓ = (M_Planck / v)^4
ratio = M_Planck / v_PDG
D_over_l_required = ratio**4

print("=" * 60)
print("DIRECTION 2: PSC Orbital Counting for EW Scale")
print("=" * 60)
print(f"\nPhysical setup:")
print(f"  v_PDG = {v_PDG} GeV")
print(f"  M_Planck = {M_Planck:.6e} GeV")
print(f"  M_Planck / v_PDG = {ratio:.6e}")
print(f"\nRequired D/ℓ = (M_Planck/v)^4 = {D_over_l_required:.6e}")
print(f"  That is ≈ 10^{np.log10(D_over_l_required):.1f}")
print(f"  In bits: log₂(D/ℓ) = 4 · log₂(M_Planck/v) = {4*np.log2(ratio):.2f} bits")

# --- What range of v does the search cover? ---
print("\n" + "-" * 40)
print("Range of v accessible from UGP-motivated D, ℓ:")

# D ∈ {2^n·3^m·5^p: 0≤n,m,p≤6}, ℓ ∈ {1,...,20}
D_values = set()
for n, m, p in product(range(7), range(7), range(7)):
    D_values.add(2**n * 3**m * 5**p)
D_values = sorted(D_values)
ell_values = list(range(1, 21))

print(f"  D values: {len(D_values)} smooth numbers (2^n·3^m·5^p, max={max(D_values)})")
print(f"  ℓ values: {ell_values}")

# D/ℓ range
min_ratio = min(D_values) / max(ell_values)  # = 1/20 = 0.05
max_ratio = max(D_values) / 1  # = 2^6·3^6·5^6 = 729000000

print(f"\n  min(D/ℓ) = {min_ratio:.4f}")
print(f"  max(D/ℓ) = {max_ratio:.3e}")

v_max = M_Planck * (min_ratio)**(-0.25)  # D/ℓ small → v large
v_min = M_Planck * (max_ratio)**(-0.25)  # D/ℓ large → v small

print(f"\n  v range accessible:")
print(f"    max v = M_Planck · ({min_ratio})^(-1/4) = {v_max:.6e} GeV")
print(f"    min v = M_Planck · ({max_ratio:.3e})^(-1/4) = {v_min:.6e} GeV")
print(f"  Target v = {v_PDG} GeV")
print(f"\n  GAP: target v is {v_PDG:.2f} GeV but accessible range is")
print(f"       [{v_min:.3e}, {v_max:.3e}] GeV")
print(f"       Target is {(v_min/v_PDG):.2e}x BELOW the minimum accessible v!")

# --- Full scan (will confirm analytical result) ---
print("\n" + "-" * 40)
print("Full scan for best (D,ℓ) match:")

best_hits = []
for D in D_values:
    for ell in ell_values:
        v_pred = M_Planck * (D / ell) ** (-0.25)
        dev_pct = abs(v_pred - v_PDG) / v_PDG * 100
        if dev_pct < 1000:  # capture anything < 10x off
            best_hits.append({
                'D': D, 'ell': ell, 'D_over_ell': D/ell,
                'v_pred': v_pred, 'dev_pct': dev_pct
            })

best_hits.sort(key=lambda x: x['dev_pct'])
print(f"\nTop 10 closest (D,ℓ) pairs:")
print(f"{'D':>15} {'ℓ':>4} {'D/ℓ':>15} {'v_pred (GeV)':>16} {'dev%':>10}")
for h in best_hits[:10]:
    print(f"{h['D']:>15} {h['ell']:>4} {h['D_over_ell']:>15.2e} {h['v_pred']:>16.4e} {h['dev_pct']:>10.2f}%")

if best_hits:
    best = best_hits[0]
    sigma_best = abs(best['v_pred'] - v_PDG) / 0.001  # assume 1 MeV uncertainty? No.
    # Actually use PDG precision ~0.05 MeV for v? v = (sqrt(2)G_F)^{-1/2}, delta_v/v ≈ delta_G_F/2G_F
    # G_F PDG uncertainty: G_F = 1.1663788(6)×10^{-5} GeV^{-2}, so δG_F/G_F = 5×10^{-7}
    # δv/v = δG_F/(2G_F) ≈ 2.5×10^{-7}, so σ_v ≈ 246.22 × 2.5e-7 ≈ 6×10^{-5} GeV = 60 keV
    sigma_v = 246.22 * 2.5e-7  # GeV
    sigma_best = abs(best['v_pred'] - v_PDG) / sigma_v
    print(f"\nBest hit: D={best['D']}, ℓ={best['ell']}, v_pred={best['v_pred']:.4e} GeV")
    print(f"  Deviation from PDG: {best['dev_pct']:.2f}%")
    print(f"  In sigma (using σ_v ≈ {sigma_v*1e6:.1f} keV): {sigma_best:.0f}σ")

# --- Alternative PSC formula: Cosmological analogy ---
print("\n" + "=" * 60)
print("ALTERNATIVE: PSC analogy with cosmological constant formula")
print("=" * 60)
print("""
The cosmological constant PSC formula is:
  Λ_vac = (ln2/π) × L_model × H₀²/c²  (dimensionally carries H₀²)
This is NOT exp(−L × ln2) × M_Planck⁴ in general.

For an EW analogy, the PSC formula for v would need to be of the form:
  v⁴ = exp(−L_EW · ln2) · M_Planck⁴
  → L_EW = 4·log₂(M_Planck/v) ≈ 4 × 55.46 ≈ 221.86 bits
  → D_EW/ℓ_EW = 2^221.86 ≈ 10^{66.8}  [astronomically large]

OR if we use the Λ-style formula:
  v = (ln2/π) × L_model_EW × some_reference_scale²/v
This doesn't make dimensional sense without a reference scale.

CONCLUSION: Neither formulation of the PSC orbital counting formula
can produce v ≈ 246 GeV from UGP-smooth integers D and small ℓ.
The required D/ℓ ≈ 10^{66.8} is far beyond any UGP-motivated integer.
""")

# --- What would actually work? (analytical) ---
print("What L_model value would yield v via the exponential formula?")
L_EW = 4 * np.log2(M_Planck / v_PDG)
print(f"  L_EW = 4·log₂(M_Planck/v) = {L_EW:.4f} bits")
print(f"  Compare: L_model_cosmo = log₂(2000/3) = {np.log2(2000/3):.4f} bits")
print(f"  Ratio L_EW/L_cosmo = {L_EW/np.log2(2000/3):.2f}")
print(f"\n  No UGP-structured D,ℓ pair gives log₂(D/ℓ) ≈ {L_EW:.1f} bits.")
print(f"  The maximal accessible is log₂({max_ratio:.2e}) ≈ {np.log2(max_ratio):.1f} bits.")
print(f"  Gap: {L_EW - np.log2(max_ratio):.1f} bits short.")

# --- Save results ---
results = {
    'direction': 2,
    'description': 'PSC orbital counting: v = M_Planck*(D/ℓ)^(-1/4) from UGP smooth integers',
    'required_D_over_ell': D_over_l_required,
    'required_L_EW_bits': float(L_EW),
    'L_model_cosmo_bits': float(np.log2(2000/3)),
    'max_D_over_ell_in_search': max_ratio,
    'max_accessible_bits': float(np.log2(max_ratio)),
    'v_min_accessible_GeV': float(v_min),
    'v_max_accessible_GeV': float(v_max),
    'best_hit': best_hits[0] if best_hits else None,
    'grade': 'NEGATIVE',
    'reason': (f'Required D/ℓ ≈ 10^{np.log10(D_over_l_required):.0f} is '
               f'{D_over_l_required/max_ratio:.2e}x larger than max UGP-motivated D/ℓ. '
               f'L_EW ≈ {L_EW:.1f} bits vs L_cosmo ≈ {np.log2(2000/3):.2f} bits. '
               'No PSC orbital formula can bridge this gap.'),
    'timestamp': datetime.utcnow().isoformat(),
}

output_path = 'papers/01_SM/research_sandbox/HMC_L2_vev_derivation/direction2_results.json'
with open(output_path, 'w') as f:
    json.dump(results, f, indent=2)
print(f"\nResults saved to {output_path}")
sha = hashlib.sha256(json.dumps(results, sort_keys=True).encode()).hexdigest()
print(f"SHA-256: {sha}")
