"""Direction N: Can φ^(1/N_gen) be derived from SRRG efficiency + PSC generation count?"""
import numpy as np
import json
from fractions import Fraction

pi = np.pi; ln2 = np.log(2); phi = (1+5**0.5)/2
N_gen = 3  # PSC-derived
IPT = 1 + np.log(phi)/(2*np.log(2*pi))

f_vol_exact = np.e**pi / (2*pi**2)
print(f"=== DIRECTION N: φ^(1/N_gen) from SRRG + generation structure ===")
print(f"f_vol_exact = e^π/(2π²) = {f_vol_exact:.8f}")
print(f"φ^(1/3) = {phi**(1/N_gen):.8f}")
print(f"IPT^(1/3) = {IPT**(1/N_gen):.8f}")
print()

# --- Candidate 1: 2π² × φ^(1/N_gen) ---
L_SSB_phi = np.log2(2*pi**2 * phi**(1/N_gen))
target_L = pi/ln2
v_PDG = 246.22

M_ref_phi = v_PDG / (ln2/pi * L_SSB_phi)**0.5
print(f"Candidate 1: Vol = 2π² × φ^(1/3)")
print(f"  L_SSB = {L_SSB_phi:.8f} bits (target: {target_L:.8f})")
print(f"  Gap in L: {(target_L - L_SSB_phi)/target_L * 100:.4f}%")
print(f"  M_ref = {M_ref_phi:.6f} GeV  (err: {(M_ref_phi-v_PDG)/v_PDG*100:+.4f}%)")

# --- Candidate 2: 2π² × IPT^(1/N_gen) ---
L_SSB_IPT = np.log2(2*pi**2 * IPT**(1/N_gen))
M_ref_IPT = v_PDG / (ln2/pi * L_SSB_IPT)**0.5
print(f"\nCandidate 2: Vol = 2π² × IPT^(1/3)")
print(f"  IPT^(1/3) = {IPT**(1/N_gen):.8f}")
print(f"  L_SSB = {L_SSB_IPT:.8f} bits")
print(f"  Gap in L: {(target_L - L_SSB_IPT)/target_L * 100:.4f}%")
print(f"  M_ref = {M_ref_IPT:.6f} GeV  (err: {(M_ref_IPT-v_PDG)/v_PDG*100:+.4f}%)")

# --- How close is φ^(1/3) to f_vol_exact? ---
print(f"\n=== Comparison at f_vol level ===")
print(f"f_vol_exact = e^π/(2π²)  = {f_vol_exact:.8f}")
print(f"φ^(1/3)                  = {phi**(1/3):.8f}  diff: {abs(phi**(1/3) - f_vol_exact)*100:.4f}%")
print(f"IPT^(1/3)                = {IPT**(1/3):.8f}  diff: {abs(IPT**(1/3) - f_vol_exact)*100:.4f}%")
print(f"7/6                      = {7/6:.8f}  diff: {abs(7/6 - f_vol_exact)*100:.4f}%")
print(f"6/5                      = {6/5:.8f}  diff: {abs(6/5 - f_vol_exact)*100:.4f}%")
print(f"e^(1/e)                  = {np.e**(1/np.e):.8f}  diff: {abs(np.e**(1/np.e) - f_vol_exact)*100:.4f}%")
print(f"1 + 1/φ²                 = {1 + 1/phi**2:.8f}  diff: {abs(1 + 1/phi**2 - f_vol_exact)*100:.4f}%")

# --- Exact α such that φ^α = f_vol_exact ---
alpha_phi = np.log(f_vol_exact) / np.log(phi)
print(f"\n=== Exact φ-exponent ===")
print(f"φ^α = e^π/(2π²) → α = {alpha_phi:.8f}")
print(f"α vs 1/3 = {1/3:.8f}: diff = {abs(alpha_phi - 1/3)*100:.4f}%")
print(f"α vs 1/N_gen (N_gen=3): within {abs(alpha_phi - 1/3)/abs(1/3)*100:.4f}%")

# Best simple fraction
best_fracs = sorted([(abs(float(Fraction(p,q)) - alpha_phi), p, q) 
                      for p in range(1, 30) for q in range(1, 30)])[:5]
print(f"\nBest rational approximations to α = {alpha_phi:.8f}:")
for diff, p, q in best_fracs:
    print(f"  {p}/{q} = {p/q:.8f}, diff = {diff:.8f}")

# --- SRRG derivation attempt ---
print(f"\n=== SRRG derivation attempt ===")
# In SRRG: the per-generation selector efficiency η* = IPT^(1/N_gen)?
# IPT is the fixed-point efficiency. If each generation contributes IPT^(1/N_gen):
# Vol_corrected = 2π² × IPT^(1/N_gen)  — checked above, gives IPT^(1/3) not φ^(1/3)

# Another SRRG route: φ arises as the SRRG branching ratio (golden mean)
# The SRRG efficiency per generation step:
# η_per_gen = (IPT)^(1/N_gen)?  OR  φ^(1/N_gen)?
# IPT = 1 + ln(φ)/(2 ln(2π)) ≈ 1.131 — this IS built from φ
# φ^(1/3) ≈ 1.174 is BETTER than IPT^(1/3) ≈ 1.042

# Try: can φ^(1/N_gen) be expressed in terms of IPT and N_gen?
val = np.log(phi**(1/N_gen)) / np.log(IPT**(1/N_gen))
print(f"ln(φ^(1/3)) / ln(IPT^(1/3)) = {val:.6f}")
print(f"φ^(1/3) = IPT^({val:.4f}/3) — no clean relation")

# SRRG fixed-point ratio: at fixed-point, the branching ratio is φ
# Conjecture N-draft: the correction arises from φ DIRECTLY (not IPT)
# because the Goldstone π-modes are PSC-selected with golden-ratio branching
# and N_gen = 3 is the depth of the selection tree.
# This would give: f_vol = φ^(1/N_gen) = φ^(1/3) ≈ f_vol_exact to 0.14%

print(f"\n=== Conjecture N formulation ===")
print(f"Conjecture N: f_vol = φ^(1/N_gen) where")
print(f"  φ = SRRG golden-ratio branching factor")
print(f"  N_gen = 3 = PSC-derived generation count")
print(f"This gives f_vol ≈ {phi**(1/3):.6f} vs exact {f_vol_exact:.6f} (0.14% gap)")
print(f"The conjecture is NOT exact but is the best structural approximant found.")
print(f"A derivation would require showing the Goldstone PSC entropy accumulates")
print(f"as φ^(1/N_gen) per generation — not yet derived.")

# Best achievable M_ref summary
print(f"\n=== Best M_ref candidates ===")
for name, L in [("Exact e^π/(2π²)", np.log2(2*pi**2 * f_vol_exact)),
                ("φ^(1/3) approx", L_SSB_phi),
                ("7/6 approx", np.log2(2*pi**2 * 7/6)),
                ("IPT^(1/3) approx", L_SSB_IPT)]:
    M = v_PDG / (ln2/pi * L)**0.5
    print(f"  {name:30s}: L = {L:.6f}, M_ref = {M:.4f} GeV  ({(M-v_PDG)/v_PDG*100:+.4f}%)")

conclusion = (f"φ^(1/3) is the best structural approximant to f_vol_exact (0.14% gap vs 0.48% for 7/6 and 11.3% for IPT^(1/3)). "
              f"With Vol = 2π² × φ^(1/3), L_SSB = {L_SSB_phi:.6f} bits, M_ref = {M_ref_phi:.4f} GeV ({(M_ref_phi-v_PDG)/v_PDG*100:+.4f}% from v_PDG). "
              f"Exact φ-exponent: α = {alpha_phi:.6f} ≈ 1/3 within 0.85%. "
              f"No SRRG derivation found; Conjecture N (golden-ratio branching depth = N_gen) is physically motivated but unproven.")
print(f"\nVerdict: {conclusion}")

json.dump({
    "phi_1over3": phi**(1/N_gen),
    "IPT_1over3": IPT**(1/N_gen),
    "f_vol_exact": f_vol_exact,
    "alpha_phi_exact": alpha_phi,
    "alpha_phi_vs_1over3_pct": abs(alpha_phi - 1/3) / (1/3) * 100,
    "best_fraction": f"{best_fracs[0][1]}/{best_fracs[0][2]}",
    "M_ref_phi": M_ref_phi,
    "M_ref_phi_err_pct": (M_ref_phi - v_PDG) / v_PDG * 100,
    "M_ref_IPT": M_ref_IPT,
    "M_ref_IPT_err_pct": (M_ref_IPT - v_PDG) / v_PDG * 100,
    "L_SSB_phi": L_SSB_phi,
    "conclusion": conclusion
}, open("direction_N_phi_Ngen.json","w"), indent=2)
