"""
Direction 4: GTE Generating Function Constants → EW Scale
EPIC_051 Phase 2 — Level 2 Higgs VEV structural derivation

The GTE canonical triple at generation 1: (a₁, b₁, c₁) = (1, 73, 823)
  b₁ = 73: fundamental GTE period parameter
  c₁ = 823: GTE "closure" value at generation 1

Question: Is there a natural algebraic transformation T(a₁,b₁,c₁) → v ≈ 246.22 GeV?

Physical note: The GTE constants are dimensionless integers. To interpret them
in GeV we need either:
  (a) A reference mass that turns the expression into an absolute energy
  (b) A ratio v/m_ref where m_ref is a UGP-predicted mass

We therefore search BOTH:
  1. Expressions E(73, 823, φ, π, e) ≈ 246.22 (treating as if in GeV — numerological)
  2. Ratios v / m_ref where m_ref ∈ UGP-predicted masses

For case 2, UGP-predicted reference masses:
  m_W = 80.379 GeV (PDG, used as anchor)
  m_W_2loop = 80.364 GeV (UGP prediction)
  m_t_PDG = 172.76 GeV
  m_Z = 91.1876 GeV
  m_p = 0.9383 GeV
  m_e = 0.511e-3 GeV
"""

import numpy as np
from itertools import product
import json
import hashlib
from datetime import datetime

# -------------------------
# Constants
# -------------------------
phi = (1 + 5**0.5) / 2
pi = np.pi
e = np.e

# GTE canonical values
b1 = 73.0   # GTE fundamental period
c1 = 823.0  # GTE closure value
a1 = 1.0    # GTE base

# Target
v_PDG = 246.22  # GeV

# UGP reference masses for ratio search
ref_masses = {
    'm_W_PDG': 80.379,       # GeV
    'm_W_2loop': 80.364,     # GeV (UGP P01 prediction)
    'm_Z': 91.1876,          # GeV
    'm_t_PDG': 172.76,       # GeV
    'm_H_PDG': 125.20,       # GeV
    'm_p': 0.9383,           # GeV (proton)
    'm_pi': 0.1350,          # GeV (pion)
    'm_e_keV': 0.511e-3,     # GeV (electron)
}

print("=" * 60)
print("DIRECTION 4: GTE Constants → EW Scale")
print("=" * 60)
print(f"\nGTE canonical triple: (a₁, b₁, c₁) = ({a1:.0f}, {b1:.0f}, {c1:.0f})")
print(f"Target: v_PDG = {v_PDG} GeV")

# -------------------------
# SEARCH 1: Simple expressions in {b₁, c₁, φ, π, e, √2, ...}
# -------------------------
print("\n" + "-" * 40)
print("SEARCH 1: Simple arithmetic/transcendental expressions ≈ 246.22")
print("-" * 40)

# Atoms: b1=73, c1=823, phi, pi, e, ln(2), ln(phi), sqrt(2), sqrt(3), sqrt(5)
atoms_named = {
    'b1': b1,
    'c1': c1,
    'phi': phi,
    'pi': pi,
    'e': e,
    'ln2': np.log(2),
    'lnphi': np.log(phi),
    'sqrt2': np.sqrt(2),
    'sqrt3': np.sqrt(3),
    'sqrt5': np.sqrt(5),
    'sqrt73': np.sqrt(73),
    'sqrt823': np.sqrt(823),
    'sqrt(73*823)': np.sqrt(73*823),
}

print("\nAtom values:")
for k, v_atom in atoms_named.items():
    print(f"  {k} = {v_atom:.6f}")

print(f"\nKey check: sqrt(b₁ × c₁) = sqrt({b1*c1}) = {np.sqrt(b1*c1):.4f}")
print(f"  vs v_PDG = {v_PDG:.4f}")
print(f"  deviation = {abs(np.sqrt(b1*c1) - v_PDG)/v_PDG*100:.4f}%")
sigma_v = 246.22 * 2.5e-7  # ~60 keV
print(f"  sigma tension: {abs(np.sqrt(b1*c1) - v_PDG)/sigma_v:.0f}σ (from PDG precision)")

# --- Depth-1 expressions: a × atom₁ ---
print("\n[Depth-1: a × atom for integer a ∈ [1,20]]")
depth1_hits = []
for atom_name, atom_val in atoms_named.items():
    for coef in range(1, 50):
        val = coef * atom_val
        dev = abs(val - v_PDG) / v_PDG * 100
        if dev < 2.0:  # within 2%
            depth1_hits.append({'expr': f'{coef}×{atom_name}', 'val': val, 'dev_pct': dev})

depth1_hits.sort(key=lambda x: x['dev_pct'])
print(f"  Hits within 2%:")
for h in depth1_hits[:10]:
    print(f"    {h['expr']} = {h['val']:.4f}  (dev={h['dev_pct']:.4f}%)")

# --- Depth-2 expressions: a × atom₁ + b × atom₂ ---
print("\n[Depth-2: a × atom₁ + b × atom₂ for integers a,b ∈ [-20,20]]")
key_atoms = [(k, v_atom) for k, v_atom in atoms_named.items() 
             if k in ('b1','c1','phi','pi','e','sqrt(73*823)')]
depth2_hits = []
for (n1, v1), (n2, v2) in product(key_atoms, key_atoms):
    if n1 >= n2:  # avoid duplicates
        continue
    for a in range(-20, 21):
        for b in range(-20, 21):
            if a == 0 and b == 0:
                continue
            val = a * v1 + b * v2
            dev = abs(val - v_PDG) / v_PDG * 100
            if dev < 0.5:  # within 0.5%
                depth2_hits.append({
                    'expr': f'{a}×{n1} + {b}×{n2}',
                    'val': val, 'dev_pct': dev
                })

depth2_hits.sort(key=lambda x: x['dev_pct'])
print(f"  Hits within 0.5%:")
for h in depth2_hits[:15]:
    print(f"    {h['expr']} = {h['val']:.4f}  (dev={h['dev_pct']:.4f}%)")

# --- Depth-2 ratios: atom₁ / atom₂ and atom₁ * atom₂ ---
print("\n[Products and ratios of pairs]")
all_atoms = list(atoms_named.items())
ratio_hits = []
for (n1, v1), (n2, v2) in product(all_atoms, all_atoms):
    if v2 == 0:
        continue
    # v1 * v2
    val_prod = v1 * v2
    dev_prod = abs(val_prod - v_PDG) / v_PDG * 100
    if dev_prod < 2.0:
        ratio_hits.append({'expr': f'{n1}×{n2}', 'val': val_prod, 'dev_pct': dev_prod})
    # v1 / v2
    val_ratio = v1 / v2
    dev_ratio = abs(val_ratio - v_PDG) / v_PDG * 100
    if dev_ratio < 2.0:
        ratio_hits.append({'expr': f'{n1}/{n2}', 'val': val_ratio, 'dev_pct': dev_ratio})
    # v1^2 / v2
    val_sq = v1**2 / v2
    dev_sq = abs(val_sq - v_PDG) / v_PDG * 100
    if dev_sq < 2.0:
        ratio_hits.append({'expr': f'{n1}²/{n2}', 'val': val_sq, 'dev_pct': dev_sq})

ratio_hits.sort(key=lambda x: x['dev_pct'])
print("  Hits within 2%:")
for h in ratio_hits[:15]:
    print(f"    {h['expr']} = {h['val']:.4f}  (dev={h['dev_pct']:.4f}%)")

# -------------------------
# SEARCH 2: v/m_ref ratios
# -------------------------
print("\n" + "-" * 40)
print("SEARCH 2: v/m_ref as GTE expression")
print("-" * 40)
print("Checking if v/m_ref has a simple GTE structural form")
print()

for ref_name, ref_val in ref_masses.items():
    ratio_v_mref = v_PDG / ref_val
    print(f"  v / {ref_name} = {v_PDG}/{ref_val} = {ratio_v_mref:.6f}")
    # Check against simple GTE expressions
    candidates = {
        'b1/pi':          b1/pi,
        'b1/e':           b1/e,
        'b1/phi^2':       b1/phi**2,
        'sqrt(b1)':       np.sqrt(b1),
        'c1/b1':          c1/b1,
        'sqrt(c1/b1)':    np.sqrt(c1/b1),
        'c1/(b1*pi)':     c1/(b1*pi),
        'pi+1/phi':       pi + 1/phi,
        '2+phi':          2+phi,
        '3+phi':          3+phi,
        'pi+phi':         pi+phi,
        '2*phi':          2*phi,
        'sqrt(b1*phi)':   np.sqrt(b1*phi),
        'b1^{1/3}':       b1**(1/3),
        'e*phi':          e*phi,
        'pi*phi/ln2':     pi*phi/np.log(2),
    }
    hits = []
    for cname, cval in candidates.items():
        dev = abs(cval - ratio_v_mref) / ratio_v_mref * 100
        if dev < 1.0:
            hits.append(f"    {cname} = {cval:.5f} (dev={dev:.4f}%)")
    if hits:
        for h in hits:
            print(h)
    else:
        best_cand = min(candidates.items(), key=lambda x: abs(x[1]-ratio_v_mref)/ratio_v_mref)
        print(f"    (no hit within 1%; best: {best_cand[0]} = {best_cand[1]:.4f}, "
              f"dev={abs(best_cand[1]-ratio_v_mref)/ratio_v_mref*100:.2f}%)")

# -------------------------
# NULL DISCIPLINE for Depth-1/2
# -------------------------
print("\n" + "-" * 40)
print("NULL DISCIPLINE for depth-2 additive search")
print("-" * 40)
print("Testing 200 random targets in [230, 260] (near v)")

import random
random.seed(123)
np.random.seed(123)

def count_depth2_hits(target, tol_pct=0.5):
    count = 0
    for (n1, v1), (n2, v2) in product(key_atoms, key_atoms):
        if n1 >= n2:
            continue
        for a in range(-20, 21):
            for b in range(-20, 21):
                if a == 0 and b == 0:
                    continue
                val = a * v1 + b * v2
                dev = abs(val - target) / target * 100
                if dev < tol_pct:
                    count += 1
    return count

null_targets = np.random.uniform(230, 260, 200)
null_counts = []
print("Running 200 null tests...")
for i, nt in enumerate(null_targets):
    null_counts.append(count_depth2_hits(nt, tol_pct=0.5))
    if (i + 1) % 50 == 0:
        print(f"  Progress: {i+1}/200, running median={np.median(null_counts):.1f}")

real_depth2_count = len(depth2_hits)
null_arr = np.array(null_counts)
frac_with_hits = np.mean(null_arr > 0)

print(f"\nNULL DISCIPLINE RESULT (depth-2, 0.5% tolerance):")
print(f"  Real target (v=246.22) depth-2 hits: {real_depth2_count}")
print(f"  Random target median hits: {np.median(null_arr):.1f}")
print(f"  Random target mean hits: {np.mean(null_arr):.2f}")
print(f"  Fraction of random targets with ≥1 hit: {frac_with_hits*100:.1f}%")

if frac_with_hits > 0.5:
    null_verdict = "VOLUME-DOMINATED (>50% saturation at 0.5%)"
elif frac_with_hits > 0.10:
    null_verdict = "LIKELY SATURATED (10-50% saturation)"
else:
    null_verdict = "POTENTIALLY SIGNIFICANT (<10% saturation)"

print(f"  Verdict: {null_verdict}")

# -------------------------
# SEARCH 3: GTE recurrence and deeper structure
# -------------------------
print("\n" + "-" * 40)
print("SEARCH 3: GTE recurrence T(a,b,c) and multi-generation values")
print("-" * 40)
print("""
The GTE recurrence: if the T operator advances (a,b,c), what are
the multi-generation values? Gen 0: (1,1,1)?, Gen 1: (1,73,823)?

From P01 context: b₁ = 73 is the UGP fundamental 'b' parameter.
The GTE sequence b-values grow. Let's check if any b_n or c_n is near 246.

From context in SPEC docs: the b-sequence includes 73, and the c-sequence
includes 823. These are related: 823 = 73×11 + 20? Let's verify:
  73 × 11 = 803, 823 - 803 = 20. Not clean.
  823 = 73 × 11.274... not a clean multiple.
  
Check: Is 246 = 2 × 73 + 100? = 146+100. No.
Is 246 = 3 × 73 + 27? = 219+27. No.
Is 246 = 823/3 - 28? = 274 - 28 = 246! Let's check: 823/3 = 274.33, 274.33-28.33=246. Only if we use 823/3 = 274.33 and 274.33-28.33=246.00. But 28.33 = 85/3. So 823/3 - 85/3 = 738/3 = 246. 738 = 2×369 = 2×3×123 = 6×123. Not structurally motivated.

What about: b₁ × φ + c₁/φ^k?
  73×φ = 73×1.618 = 118.1 (no)
  73×φ² = 73×2.618 = 191.1 (no)
  73×φ³ = 73×4.236 = 309.2 (no)
  73×(φ²+1/φ) = 73×(2.618+0.618) = 73×3.236 = 236.2 (close: 4.1% off)
  73×(φ²+φ) = 73×4.236 = 309 (no)
  73×(2+1/φ) = 73×(2+0.618) = 73×2.618 = 191.1 (same as φ²)
  73×(π+0.05) = 73×3.19 = 232.9 (5.4% off)
  73×(π+0.18) = 73×3.32 = 242.4 (1.5% off)
""")

# Systematic: find a,b,c,d such that a*b1 + b*c1 + c ≈ 246
# a,b ∈ rational[-5,5], c ∈ [-200,200]
print("\n[Systematic: a×73 + b×823 ≈ 246 for rational a,b = p/q, |p|,|q| ≤ 8]")
linear_hits = []
for p1 in range(-8, 9):
    for q1 in range(1, 9):
        for p2 in range(-8, 9):
            for q2 in range(1, 9):
                a_rat = p1 / q1
                b_rat = p2 / q2
                val = a_rat * b1 + b_rat * c1
                dev = abs(val - v_PDG) / v_PDG * 100
                if dev < 0.2 and (abs(p1)+abs(p2)) > 0:
                    linear_hits.append({
                        'expr': f'({p1}/{q1})×73 + ({p2}/{q2})×823',
                        'val': val, 'dev_pct': dev,
                        'complexity': abs(p1)+q1+abs(p2)+q2
                    })

linear_hits.sort(key=lambda x: (x['dev_pct']))
print(f"  Rational-coefficient hits within 0.2%:")
if linear_hits:
    for h in linear_hits[:10]:
        print(f"    {h['expr']} = {h['val']:.4f}  (dev={h['dev_pct']:.5f}%, complexity={h['complexity']})")
else:
    print("    No hits within 0.2%")

# -------------------------
# SUMMARY
# -------------------------
print("\n" + "=" * 60)
print("DIRECTION 4 SUMMARY")
print("=" * 60)

# Identify best promising hit
all_hits_d4 = depth1_hits + depth2_hits + ratio_hits
best_by_dev = sorted(all_hits_d4, key=lambda x: x['dev_pct']) if all_hits_d4 else []

print(f"\nKey finding: sqrt(b₁ × c₁) = sqrt(73 × 823) = sqrt(60079) ≈ {np.sqrt(73*823):.4f}")
print(f"  vs v_PDG = {v_PDG}")
print(f"  deviation = {abs(np.sqrt(73*823)-v_PDG)/v_PDG*100:.4f}%")
print(f"  But this is pure numerology: b₁, c₁ are dimensionless integers;")
print(f"  there is no physical reason why √(73×823) should equal v in GeV.")
print(f"  The expression doesn't specify units, reference scale, or mechanism.")
print()
print(f"Null discipline (depth-2): {frac_with_hits*100:.1f}% of random targets also hit")
print(f"Verdict: {null_verdict}")

results = {
    'direction': 4,
    'description': 'GTE canonical triple (1,73,823) → EW scale 246.22 GeV search',
    'notable_hit': {
        'expr': 'sqrt(73×823)',
        'val': float(np.sqrt(73*823)),
        'dev_pct': float(abs(np.sqrt(73*823)-v_PDG)/v_PDG*100),
        'assessment': 'Pure numerology: dimensionless integers, no physical units mechanism'
    },
    'depth1_hits_within_2pct': len(depth1_hits),
    'depth2_hits_within_0p5pct': real_depth2_count,
    'null_saturation_pct': float(frac_with_hits * 100),
    'null_verdict': null_verdict,
    'linear_rational_hits_0p2pct': len(linear_hits),
    'best_linear_hit': linear_hits[0] if linear_hits else None,
    'grade': 'NEGATIVE',
    'reason': (
        'No structurally motivated expression of GTE integers (73, 823) gives v = 246.22 GeV. '
        'Best numerological hit sqrt(73×823) ≈ 245.11 is 0.45% off (>>PDG precision) '
        'and lacks dimensional mechanism. Depth-2 additive search is volume-dominated '
        f'({frac_with_hits*100:.0f}% null saturation). '
        'Ratio search v/m_ref finds no GTE-structural expression for any reference mass. '
        'Missing ingredient: a dimensional anchor connecting GTE integers to GeV scale.'
    ),
    'timestamp': datetime.utcnow().isoformat(),
}

output_path = 'papers/01_SM/research_sandbox/HMC_L2_vev_derivation/direction4_results.json'
with open(output_path, 'w') as f:
    json.dump(results, f, indent=2)
print(f"\nResults saved to {output_path}")
sha = hashlib.sha256(json.dumps(results, sort_keys=True).encode()).hexdigest()
print(f"SHA-256: {sha}")
