"""
Rank 8-PSB: Particle Size Bounds from Planck Scale
EPIC_072 — GTE Ontological Unification

Computes information-theoretic and physical bounds on the size of each
SM particle in units of Planck lengths (= CA cells at the Planck scale).

Three bound types:
1. Information-theoretic: min cells to encode Z₇^5 ring state
2. Compton wavelength: λ_C = ℏ/mc in Planck units
3. Causal volume: c × τ (lifetime) in Planck units (upper bound for unstable)
"""

import numpy as np

# Physical constants in SI
hbar = 1.0546e-34   # J·s
c = 2.998e8         # m/s
G = 6.674e-11       # m^3/(kg·s^2)

# Planck units
l_P = np.sqrt(hbar * G / c**3)  # Planck length ≈ 1.616e-35 m
t_P = l_P / c                    # Planck time ≈ 5.39e-44 s
m_P = np.sqrt(hbar * c / G)      # Planck mass ≈ 2.176e-8 kg

print("=" * 70)
print("Rank 8-PSB: Particle Size Bounds (in Planck lengths = CA cells)")
print("EPIC_072 — GTE Ontological Unification")
print("=" * 70)
print(f"Planck length: {l_P:.4e} m")
print()

# ─────────────────────────────────────────────────────────────
# 1. Information-Theoretic Lower Bound
# ─────────────────────────────────────────────────────────────
print("─" * 50)
print("1. INFORMATION-THEORETIC LOWER BOUND")
print("─" * 50)
bits_z7_ring = 5 * np.log2(7)
print(f"   Z₇^5 ring: 5 × log₂(7) = {bits_z7_ring:.2f} bits")
print(f"   Minimum cells to encode: ⌈{bits_z7_ring:.2f}⌉ = {int(np.ceil(bits_z7_ring))} cells")
print(f"   Practical meta-glider minimum (thermal stability): ~O(100-1000) cells")
print()

# ─────────────────────────────────────────────────────────────
# 2. Compton Wavelength Lower Bound
# ─────────────────────────────────────────────────────────────
print("─" * 50)
print("2. COMPTON WAVELENGTH (quantum size in Planck units)")
print("─" * 50)
print(f"   λ_C = ℏ/(mc) = m_P/m × Planck lengths")
print()

particles = [
    # (name, mass_kg, lifetime_s, is_stable)
    ("Electron", 9.109e-31, float('inf'), True),
    ("Muon (gen₂)", 1.884e-28, 2.197e-6, False),
    ("Tau (gen₃)", 3.167e-27, 2.903e-13, False),
    ("Up quark", 3.7e-30, float('inf'), True),   # confined
    ("Down quark", 8.5e-30, float('inf'), True),  # confined
    ("Strange quark", 1.7e-28, float('inf'), True), # confined
    ("Charm quark", 2.26e-27, float('inf'), True),
    ("Bottom quark", 7.65e-27, float('inf'), True),
    ("Top quark", 3.09e-25, 5e-25, False),
    ("Proton", 1.673e-27, float('inf'), True),
    ("W boson", 1.432e-25, 3.16e-25, False),
    ("Z boson", 1.626e-25, 2.64e-25, False),
    ("Higgs boson", 2.228e-25, 1.56e-22, False),
]

print(f"   {'Particle':<20} {'Mass (kg)':<15} {'λ_C (cells)':<18} {'τ×c/ℓ_P (cells)':<20} {'Notes'}")
print(f"   {'-'*20} {'-'*15} {'-'*18} {'-'*20} {'-'*20}")

results = []
for name, mass, lifetime, stable in particles:
    lambda_C = hbar / (mass * c)  # meters
    lambda_C_cells = lambda_C / l_P

    if stable or lifetime == float('inf'):
        causal_cells = float('inf')
        causal_str = "∞ (stable)"
    else:
        causal_dist = c * lifetime  # meters
        causal_cells = causal_dist / l_P
        causal_str = f"{causal_cells:.2e}"

    # Effective size: min(Compton, causal) but never below info-theoretic
    if lifetime == float('inf'):
        effective = lambda_C_cells
        note = "stable"
    else:
        effective = min(lambda_C_cells, causal_cells)
        if causal_cells < lambda_C_cells:
            note = "lifetime-limited"
        else:
            note = "Compton-limited"

    print(f"   {name:<20} {mass:<15.3e} {lambda_C_cells:<18.3e} {causal_str:<20} {note}")
    results.append((name, lambda_C_cells, causal_cells, note))

print()
print("─" * 50)
print("3. SUMMARY TABLE")
print("─" * 50)
print(f"\n   {'Particle':<20} {'Min size (cells)':<20} {'Max size (cells)':<20}")
print(f"   {'-'*20} {'-'*20} {'-'*20}")
for name, lambda_C, causal, note in results:
    min_size = max(int(np.ceil(bits_z7_ring)), 100)  # practical minimum
    max_size = min(lambda_C, causal) if causal != float('inf') else lambda_C
    print(f"   {name:<20} {min_size:<20} {max_size:<20.3e}")

print()
print("─" * 50)
print("4. KEY FINDINGS")
print("─" * 50)
print(f"""
   Information-theoretic minimum: {int(np.ceil(bits_z7_ring))} cells (encoding Z₇^5 ring)
   Practical minimum (thermal stability): ~100-1000 cells

   Electron Compton radius: {hbar/(9.109e-31*c)/l_P:.3e} cells ≈ 2.4×10²² cells
   Top quark (lifetime-limited): {min(hbar/(3.09e-25*c), c*5e-25)/l_P:.3e} cells

   CONCLUSION:
   - For stable particles (gen₁): size range = [100-1000 cells, 10²²-10²³ cells]
   - For unstable particles: further constrained by c×τ/ℓ_P
   - The CA 'beable' (glider) is likely O(100-10⁴) cells; wavefunction is much larger
   - The 5-cell Z-ring is the algebraic description, NOT the spatial size
""")
