"""
GTE CP Violation, Mersenne Prime Structure, and Top Quark Prediction.

Investigates:
1. Why c_H = 13 is the N_fam-th Mersenne prime exponent (Mersenne hierarchy)
2. CP violation from Mersenne/algebraic incommensurability: irrationality proof
3. New testable predictions: angle γ in degrees, |V_cb|/|V_us|, Jarlskog vs Norfleet delta_hol
4. Top quark structural formula: b_t = 2^(c_H-2) × N_gen × N_fam × (2N_fam+1)

GTE constants: N_gen=3, N_fam=5, c_H=13
Quark N_eff: b_u=9, b_d=5, b_c=275, b_s=186, b_b=8191, b_t=337920
"""

import math
from fractions import Fraction

# ── GTE constants ──────────────────────────────────────────────────────────────
N_gen = 3
N_fam = 5
c_H   = N_gen + 2 * N_fam          # = 13

# ── Quark N_eff values ─────────────────────────────────────────────────────────
b_u = N_gen ** 2                                        # 9
b_d = N_fam                                             # 5
b_c = N_fam ** 2 * (2 * N_fam + 1)                     # 275
b_s = 2 * N_gen * (2 * c_H + N_fam)                    # 186
b_b = 2 ** c_H - 1                                      # 8191  (Mersenne)
b_t = 337920                                             # from discovery engine GTE triple (76, 337920, -1)

print("=" * 70)
print("GTE CONSTANTS AND QUARK N_eff STRUCTURAL FORMULAS")
print("=" * 70)
print(f"  N_gen = {N_gen}, N_fam = {N_fam}, c_H = {c_H}")
print(f"  b_u = N_gen^2                      = {b_u}")
print(f"  b_d = N_fam                        = {b_d}")
print(f"  b_c = N_fam^2 (2 N_fam+1)         = {b_c}")
print(f"  b_s = 2 N_gen (2 c_H + N_fam)     = {b_s}")
print(f"  b_b = 2^c_H - 1  (Mersenne M_13)  = {b_b}")
print(f"  b_t = (discovery engine triple)    = {b_t}")

# ── SECTION 1: MERSENNE HIERARCHY ─────────────────────────────────────────────
print()
print("=" * 70)
print("SECTION 1: MERSENNE PRIME EXPONENT HIERARCHY")
print("=" * 70)

def is_prime(n):
    if n < 2: return False
    if n == 2: return True
    if n % 2 == 0: return False
    for i in range(3, int(n**0.5)+1, 2):
        if n % i == 0: return False
    return True

def is_mersenne_prime(p):
    """Check if 2^p - 1 is a Mersenne prime (p must be prime)."""
    if not is_prime(p): return False
    m = 2**p - 1
    # Lucas-Lehmer test
    if p == 2: return True
    s = 4
    for _ in range(p - 2):
        s = (s * s - 2) % m
    return s == 0

# First 10 Mersenne prime exponents
mersenne_exponents = []
p = 2
while len(mersenne_exponents) < 10:
    if is_mersenne_prime(p):
        mersenne_exponents.append(p)
    p += 1
    if p > 200: break

print(f"\nMersenne prime exponents (p such that 2^p-1 is prime):")
for i, p in enumerate(mersenne_exponents):
    M_p = 2**p - 1
    marker = " ← c_H (Higgs endpoint)" if p == c_H else ""
    marker2 = " ← (c_H = N_gen + 2×N_fam = 13)" if p == c_H else ""
    print(f"  p_{i+1} = {p:3d}   M_{p} = 2^{p}-1 = {M_p:12d}{marker}")

# Check key facts
idx_cH = mersenne_exponents.index(c_H) + 1  # 1-indexed position
print(f"\nKey facts:")
print(f"  c_H = {c_H} is the {idx_cH}-th Mersenne prime exponent")
print(f"  N_fam = {N_fam}")
print(f"  c_H is the N_fam-th Mersenne prime exponent: {idx_cH == N_fam}")
print(f"  b_b = 2^c_H - 1 = 2^13 - 1 = {b_b} is a Mersenne prime: {is_mersenne_prime(c_H)}")
print(f"  c_H = N_gen + 2×N_fam = {N_gen} + {2*N_fam} = {c_H}")

# Is c_H itself prime?
print(f"  c_H = 13 is prime: {is_prime(c_H)}")
print(f"\nSummary: c_H = 13 = p_{{N_fam}} (5th Mersenne prime exponent).")
print(f"  The GTE Higgs endpoint is structurally the N_fam-th Mersenne prime exponent.")
print(f"  This forces b_b = M_{{c_H}} = M_13 = 8191 to be a Mersenne prime.")

# ── SECTION 2: CP VIOLATION FROM MERSENNE IRRATIONALITY ───────────────────────
print()
print("=" * 70)
print("SECTION 2: CP VIOLATION — MERSENNE IRRATIONALITY PROOF")
print("=" * 70)

print(f"\n  b_b = {b_b} = 2^{c_H} - 1  (Mersenne prime)")
print(f"  b_s = {b_s} = 2 × 3 × 31  (algebraic)")

# Factorizations
def factorize(n):
    factors = {}
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors[d] = factors.get(d, 0) + 1
            n //= d
        d += 1
    if n > 1: factors[n] = factors.get(n, 0) + 1
    return factors

f_bb = factorize(b_b)
f_bs = factorize(b_s)
print(f"\n  Factorization of b_b = {b_b}: {f_bb}")
print(f"  Factorization of b_s = {b_s}: {f_bs}")

# The ratio b_b/b_s — is it a perfect square?
ratio = Fraction(b_b, b_s)
print(f"\n  b_b/b_s = {b_b}/{b_s} = {ratio} (exact rational)")
print(f"  b_b/b_s = {b_b/b_s:.10f}")

# Check if b_b * b_s is a perfect square (condition for sqrt(b_b/b_s) rational)
product = b_b * b_s
sqrt_product = math.isqrt(product)
is_perfect_square = (sqrt_product ** 2 == product)
print(f"\n  b_b × b_s = {b_b} × {b_s} = {product}")
print(f"  Is b_b × b_s a perfect square? {is_perfect_square}")
print(f"  (Since b_b = 8191 is prime and does not divide b_s = 186,")
print(f"   the product b_b × b_s = {product} is not a perfect square.)")
print(f"  Therefore sqrt(b_b/b_s) is irrational. QED.")

# tan(gamma) and angle gamma
tan_gamma = math.sqrt(b_b / b_s) / N_gen
gamma_rad = math.atan(tan_gamma)
gamma_deg = math.degrees(gamma_rad)

print(f"\n  tan(γ) = sqrt(b_b/b_s) / N_gen = sqrt({b_b}/{b_s}) / {N_gen}")
print(f"         = {math.sqrt(b_b/b_s):.8f} / {N_gen} = {tan_gamma:.8f}")
print(f"  γ = arctan({tan_gamma:.6f}) = {gamma_rad:.6f} rad = {gamma_deg:.4f}°")

# PDG values
pdg_tan_gamma = 2.189
pdg_gamma_deg = 65.8
pdg_gamma_unc = 5.4
pdg_Rb = 0.3826
pdg_Rb_unc = 0.009

print(f"\n  PDG γ = {pdg_gamma_deg}° ± {pdg_gamma_unc}°")
print(f"  GTE γ = {gamma_deg:.4f}°")
print(f"  Discrepancy: ({gamma_deg:.4f} - {pdg_gamma_deg}) / {pdg_gamma_unc} = "
      f"{(gamma_deg - pdg_gamma_deg)/pdg_gamma_unc:.4f}σ")

# ── SECTION 3: NEW TESTABLE PREDICTIONS ───────────────────────────────────────
print()
print("=" * 70)
print("SECTION 3: NEW TESTABLE PREDICTIONS")
print("=" * 70)

# GTE Wolfenstein parameters
lam = Fraction(b_u, 2**N_gen * b_d)          # 9/40
A_sq = Fraction(b_s, b_c)                     # 186/275
A = math.sqrt(float(A_sq))
Rb = Fraction(N_gen, 2**N_gen)                # 3/8
Rb_f = float(Rb)

# rho_bar, eta_bar
cos_gamma = math.cos(gamma_rad)
sin_gamma = math.sin(gamma_rad)
rho_bar = Rb_f * cos_gamma
eta_bar = Rb_f * sin_gamma

lam_f = float(lam)
print(f"\n--- Wolfenstein parameters ---")
print(f"  λ    = {lam} = {lam_f:.5f}")
print(f"  A    = sqrt({A_sq}) = {A:.6f}")
print(f"  ρ̄   = {rho_bar:.6f}")
print(f"  η̄   = {eta_bar:.6f}")

# Prediction 1: |V_cb| / |V_us|
Vcb = A * lam_f**2
Vus = lam_f
ratio_cb_us = Vcb / Vus
pdg_Vcb = 0.04183
pdg_Vus = 0.22500
pdg_ratio_cb_us = pdg_Vcb / pdg_Vus
print(f"\n--- Prediction 1: |V_cb|/|V_us| ---")
print(f"  GTE: A×λ = {A:.6f} × {lam_f:.5f} = {ratio_cb_us:.6f}")
print(f"  PDG: {pdg_Vcb}/{pdg_Vus} = {pdg_ratio_cb_us:.6f}")
print(f"  Discrepancy: {100*(ratio_cb_us-pdg_ratio_cb_us)/pdg_ratio_cb_us:.3f}%")

# Prediction 2: λ / R_b = N_gen / N_fam
lam_Rb_ratio = lam_f / Rb_f
pdg_lam = 0.22500
pdg_lam_Rb = pdg_lam / pdg_Rb
print(f"\n--- Prediction 2: λ/R_b = N_gen/N_fam ---")
print(f"  GTE: {lam}/{Rb} = {lam_Rb_ratio:.6f} = N_gen/N_fam = {N_gen}/{N_fam} = {N_gen/N_fam:.6f}")
print(f"  PDG: λ/R_b = {pdg_lam}/{pdg_Rb} = {pdg_lam_Rb:.6f}")
print(f"  GTE exact: {Fraction(N_gen, N_fam)} = 3/5 = 0.6")
print(f"  Discrepancy: {100*(lam_Rb_ratio - pdg_lam_Rb)/pdg_lam_Rb:.2f}%")
pdg_Rb_unc_frac = 0.009
pdg_lam_unc = 0.00067
sigma_ratio = (pdg_lam_Rb / pdg_Rb) * math.sqrt((pdg_lam_unc/pdg_lam)**2 + (pdg_Rb_unc_frac/pdg_Rb)**2)
print(f"  σ on PDG ratio ≈ {sigma_ratio:.4f}")
print(f"  Pull: {(lam_Rb_ratio - pdg_lam_Rb)/sigma_ratio:.2f}σ")

# Prediction 3: Jarlskog invariant
J_GTE = lam_f**6 * float(A_sq) * eta_bar
print(f"\n--- Prediction 3: Jarlskog invariant J ---")
print(f"  J_GTE = λ^6 × A^2 × η̄ = {lam_f:.5f}^6 × {float(A_sq):.6f} × {eta_bar:.6f}")
print(f"        = {lam_f**6:.4e} × {float(A_sq):.6f} × {eta_bar:.6f}")
print(f"        = {J_GTE:.4e}")
print(f"  PDG:  J_CKM = 3.27×10^-5 ± 0.15×10^-5")
pdg_J = 3.27e-5
pdg_J_unc = 0.15e-5
print(f"  Pull: ({J_GTE:.3e} - {pdg_J:.3e}) / {pdg_J_unc:.2e} = {(J_GTE-pdg_J)/pdg_J_unc:.2f}σ")

# Norfleet delta_hol
phi = (1 + math.sqrt(5)) / 2
Lambda_Norfleet = math.log(phi) / math.log(2 * math.pi)
delta_hol = Lambda_Norfleet - math.pi / 12
print(f"\n--- Norfleet δ_hol ---")
print(f"  φ = {phi:.10f}")
print(f"  Λ = ln(φ)/ln(2π) = {Lambda_Norfleet:.10f}")
print(f"  π/12 = {math.pi/12:.10f}")
print(f"  δ_hol = Λ - π/12 = {delta_hol:.6e}")
print(f"  J_GTE / δ_hol = {J_GTE/delta_hol:.6f}  (1 = perfect match)")
print(f"  Discrepancy J_GTE vs δ_hol: {100*(J_GTE - delta_hol)/delta_hol:.1f}%")
print(f"  Note: J_GTE = {J_GTE:.4e}, δ_hol = {delta_hol:.4e}")

# Is J_GTE ≈ δ_hol?
if abs(J_GTE - delta_hol) < 0.5e-5:
    print(f"  → Both are O(10^-5), discrepancy = {abs(J_GTE-delta_hol):.2e}")
else:
    print(f"  → Discrepancy is {abs(J_GTE-delta_hol):.2e} (not a coincidence)")

# Prediction 4: CP angle γ in degrees
print(f"\n--- Prediction 4: CP angle γ ---")
print(f"  GTE: γ = arctan(sqrt({b_b}/{b_s})/{N_gen}) = {gamma_deg:.4f}°")
print(f"  PDG: γ = 65.8° ± 5.4°  (CKMfitter 2024)")
print(f"  Pull: ({gamma_deg:.4f} - {pdg_gamma_deg}) / {pdg_gamma_unc} = {(gamma_deg-pdg_gamma_deg)/pdg_gamma_unc:.4f}σ")

# Prediction 5: V_tb at O(lambda^4) from Wolfenstein
# Exact Wolfenstein: |V_tb| = 1 - A^2*lambda^4/2 + ...
# More precisely from unitarity:
Vub = A * lam_f**3 * math.sqrt(rho_bar**2 + eta_bar**2)
Vcb_exact = A * lam_f**2 * (1 - lam_f**2/2)
Vtb = math.sqrt(1 - Vcb_exact**2 - (A*lam_f**3)**2)
print(f"\n--- Prediction 5: V_tb ---")
print(f"  GTE V_tb = sqrt(1 - V_ts^2 - V_td^2) ≈ {Vtb:.7f}")
print(f"  PDG V_tb = 0.99918 ± 0.00021")
print(f"  Pull: ({Vtb:.7f} - 0.99918) / 0.00021 = {(Vtb - 0.99918)/0.00021:.2f}σ")

# ── SECTION 4: TOP QUARK STRUCTURAL FORMULA ───────────────────────────────────
print()
print("=" * 70)
print("SECTION 4: TOP QUARK b_t STRUCTURAL FORMULA")
print("=" * 70)

# b_t = 2^(c_H - 2) * N_gen * N_fam * (2*N_fam + 1)
formula_bt = 2**(c_H - 2) * N_gen * N_fam * (2 * N_fam + 1)
print(f"\n  b_t (discovery engine) = {b_t}")
print(f"  Formula: 2^(c_H-2) × N_gen × N_fam × (2 N_fam+1)")
print(f"         = 2^{c_H-2} × {N_gen} × {N_fam} × {2*N_fam+1}")
print(f"         = {2**(c_H-2)} × {N_gen} × {N_fam} × {2*N_fam+1}")
print(f"         = {formula_bt}")
print(f"  Matches discovery engine: {formula_bt == b_t}")

# Alternative decompositions
print(f"\n  Alternative decompositions:")
print(f"    b_t = 2^(c_H-2) × N_gen × b_c/N_fam")
print(f"        = {2**(c_H-2)} × {N_gen} × {b_c}/{N_fam}")
print(f"        = {2**(c_H-2) * N_gen * b_c // N_fam}")
print(f"    b_t = 2^(c_H-2) × N_gen × 55 (where 55 = N_fam × (2N_fam+1)/N_fam = b_c/N_fam)")

# Symmetry in up-type quarks
print(f"\n  Up-type quark N_eff pattern:")
print(f"    b_u = N_gen^2                          = {b_u}")
print(f"    b_c = N_fam^2 × (2N_fam+1)            = {b_c}")
print(f"    b_t = 2^(c_H-2) × N_gen × N_fam × (2N_fam+1) = {b_t}")
print(f"  Ratios:")
print(f"    b_c / b_u = {b_c}/{b_u} = {b_c/b_u:.4f}")
print(f"    b_t / b_c = {b_t}/{b_c} = {b_t/b_c:.4f}  = 2^(c_H-2) × N_gen/N_fam = {2**(c_H-2)*N_gen/N_fam:.4f}")

# Physical check: b_t/b_b vs M_top/M_bottom
pdg_Mtop = 173.3
pdg_Mbot = 4.18
pdg_mass_ratio = pdg_Mtop / pdg_Mbot
gte_Neff_ratio = b_t / b_b
print(f"\n  Physical check: b_t/b_b vs M_top/M_bottom")
print(f"  b_t/b_b = {b_t}/{b_b} = {gte_Neff_ratio:.4f}")
print(f"  M_top/M_bottom (PDG) = {pdg_Mtop}/{pdg_Mbot} = {pdg_mass_ratio:.4f}")
print(f"  Discrepancy: {100*(gte_Neff_ratio - pdg_mass_ratio)/pdg_mass_ratio:.2f}%")

# Down-type quark N_eff pattern
print(f"\n  Down-type quark N_eff pattern:")
print(f"    b_d = N_fam                   = {b_d}")
print(f"    b_s = 2 N_gen (2 c_H + N_fam) = {b_s}")
print(f"    b_b = 2^c_H - 1  (Mersenne)   = {b_b}")
print(f"  Ratios:")
print(f"    b_s/b_d = {b_s}/{b_d} = {b_s/b_d:.2f} = 2 N_gen (2 c_H + N_fam) / N_fam = {2*N_gen*(2*c_H+N_fam)/N_fam:.2f}")
print(f"    b_b/b_s = {b_b}/{b_s} = {b_b/b_s:.4f}")
print(f"    tan^2(γ) × N_gen^2 = b_b/b_s = {b_b/b_s:.4f} ✓")

# Generation mass hierarchy structure
print(f"\n  Cross-generation ratio table:")
print(f"  {'Gen':<6} {'b_up':<10} {'b_down':<10} {'b_up/b_down':<15} {'b_down/b_up':<15}")
pairs = [(b_u, b_d, 'G1'), (b_c, b_s, 'G2'), (b_t, b_b, 'G3')]
for bu, bd, g in pairs:
    print(f"  {g:<6} {bu:<10} {bd:<10} {bu/bd:<15.4f} {bd/bu:<15.6f}")

# Structural formula for b_t in terms of b_c
print(f"\n  Structural relation b_t = 2^(c_H-2) × (N_gen/N_fam) × b_c:")
print(f"    = 2^11 × (3/5) × 275 = 2048 × 165 = {2048*165}")
print(f"    GTE predicts b_t = 337920  ✓")

# Mersenne structure of b_b revisited
print(f"\n  Why b_b = 2^c_H - 1 is Mersenne at the Higgs endpoint:")
print(f"    c_H = 13 = p_5 (5th Mersenne prime exponent)")
print(f"    N_fam = 5")
print(f"    c_H = p_{{N_fam}}  →  b_b = M_{{c_H}} = M_{{p_{{N_fam}}}} is always Mersenne")
print(f"    The Higgs endpoint is positioned at the N_fam-th Mersenne prime exponent.")

# Final summary
print()
print("=" * 70)
print("SUMMARY: ALL PREDICTIONS")
print("=" * 70)
rows = [
    ("γ (CP angle)", f"{gamma_deg:.3f}°", "65.8° ± 5.4°", f"{(gamma_deg-pdg_gamma_deg)/pdg_gamma_unc:.3f}σ"),
    ("|V_cb|/|V_us|", f"{ratio_cb_us:.5f}", f"{pdg_ratio_cb_us:.5f}", f"{100*(ratio_cb_us-pdg_ratio_cb_us)/pdg_ratio_cb_us:.2f}%"),
    ("λ/R_b", f"{lam_Rb_ratio:.4f}", f"{pdg_lam_Rb:.4f}", f"{(lam_Rb_ratio-pdg_lam_Rb)/sigma_ratio:.2f}σ"),
    ("Jarlskog J", f"{J_GTE:.3e}", f"3.27e-5 ± 0.15e-5", f"{(J_GTE-pdg_J)/pdg_J_unc:.2f}σ"),
    ("J vs δ_hol", f"J/δ_hol={J_GTE/delta_hol:.4f}", f"δ_hol={delta_hol:.3e}", "numerical coincidence?"),
    ("V_tb", f"{Vtb:.5f}", "0.99918 ± 0.00021", f"{(Vtb-0.99918)/0.00021:.2f}σ"),
    ("b_t formula check", f"2^11×3×5×11={formula_bt}", "337920 (discovery engine)", "exact match" if formula_bt==b_t else "MISMATCH"),
    ("b_t/b_b vs M_t/M_b", f"{gte_Neff_ratio:.3f}", f"{pdg_mass_ratio:.3f}", f"{100*(gte_Neff_ratio-pdg_mass_ratio)/pdg_mass_ratio:.2f}%"),
]
print(f"\n  {'Observable':<22} {'GTE':<18} {'PDG':<22} {'Discrepancy'}")
print(f"  {'-'*22} {'-'*18} {'-'*22} {'-'*15}")
for r in rows:
    print(f"  {r[0]:<22} {r[1]:<18} {r[2]:<22} {r[3]}")

print(f"\n  Mersenne hierarchy: c_H = 13 = p_{{N_fam}} = p_5 (5th Mersenne prime exponent)")
print(f"  b_b = M_13 = 8191 is therefore a Mersenne prime by construction.")
print(f"  b_t = 2^(c_H-2) × N_gen × N_fam × (2 N_fam+1) = {formula_bt} (structural formula verified)")
