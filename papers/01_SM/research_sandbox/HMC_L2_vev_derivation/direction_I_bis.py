"""Direction I-bis: Does the 3-generation structure correct S³ to give exact PSC closure?"""
import numpy as np
from fractions import Fraction
import json

pi = np.pi; ln2 = np.log(2); phi = (1+5**0.5)/2
v_PDG = 246.22

N_gen = 3
g2_sq = float(Fraction(2329, 5400))

# Tree-level S³ volume
Vol_S3 = 2*pi**2
L_S3 = np.log2(Vol_S3)
target_L = pi/ln2

print(f"L_S3 = log₂(2π²) = {L_S3:.6f} bits")
print(f"Target: π/ln2 = {target_L:.6f} bits")
print(f"Gap: {(target_L - L_S3)/target_L*100:.4f}%")

# Generation correction candidates:
corrections = {
    "1 + 1/(2 N_gen) = 7/6": 1 + 1/(2*N_gen),
    "1 + 1/N_gen = 4/3": 1 + 1/N_gen,
    "N_gen/(N_gen-1) = 3/2": N_gen/(N_gen-1),
    "(N_gen+1)/N_gen = 4/3": (N_gen+1)/N_gen,
    "phi^(1/N_gen) = phi^(1/3)": phi**(1/N_gen),
    "2^(1/N_gen) = 2^(1/3)": 2**(1/N_gen),
    "exp(1/(2*N_gen)) = exp(1/6)": np.exp(1/(2*N_gen)),
    "1 + g₂²/(4π) = 1 + loop": 1 + g2_sq/(4*pi),
}

print(f"\nCorrection candidates:")
for name, corr in corrections.items():
    L_corrected = np.log2(Vol_S3 * corr)
    M_ref = v_PDG / (ln2/pi * L_corrected)**0.5 if ln2/pi*L_corrected > 0 else None
    if M_ref:
        err = (M_ref - v_PDG)/v_PDG * 100
        gap_from_target = (target_L - L_corrected)/target_L * 100
        print(f"  {name}: corr={corr:.6f}, L={L_corrected:.4f} bits (gap {gap_from_target:+.3f}%), M_ref={M_ref:.4f} GeV ({err:+.4f}%)")

# What EXACT VOLUME correction closes the gap?
# We need log₂(Vol_S3 × f_vol) = target_L
# → f_vol = 2^(target_L) / Vol_S3 = e^π / (2π²)
f_vol_exact = np.exp(pi) / (2*pi**2)
print(f"\nExact VOLUME correction needed: f_vol = e^π/(2π²) = {f_vol_exact:.8f}")
print(f"  (Note: log₂ L-ratio = target_L/L_S3 = {target_L/L_S3:.6f} — this is NOT f_vol)")
print(f"7/6 = {7/6:.8f}  (diff from f_vol: {(7/6 - f_vol_exact)/f_vol_exact*100:+.4f}%)")
print(f"e^(1/6) = {np.exp(1/6):.8f}  (diff: {(np.exp(1/6) - f_vol_exact)/f_vol_exact*100:+.4f}%)")
print(f"φ^(1/3) = {phi**(1/3):.8f}  (diff: {(phi**(1/3) - f_vol_exact)/f_vol_exact*100:+.4f}%)")
print(f"1+1/2π = {1 + 1/(2*pi):.8f}  (diff: {(1+1/(2*pi) - f_vol_exact)/f_vol_exact*100:+.4f}%)")
print(f"1 + ln(φ)/π = {1 + np.log(phi)/pi:.8f}  (diff: {(1+np.log(phi)/pi - f_vol_exact)/f_vol_exact*100:+.4f}%)")
print(f"1 + g₂²/(4) = {1 + g2_sq/4:.8f}  (diff: {(1+g2_sq/4 - f_vol_exact)/f_vol_exact*100:+.4f}%)")

# Also verify: e^π = Vol_corrected
print(f"\ne^π = {np.exp(pi):.8f}  (this is the corrected Goldstone manifold volume needed)")
print(f"log₂(e^π) = π/ln2 = {np.log2(np.exp(pi)):.8f}  ✓")

# Does it factor as (N_gen+something)?
print(f"\nlog(f_vol_exact) = {np.log(f_vol_exact):.8f} nats")
print(f"log(7/6) = {np.log(7/6):.8f} nats")
print(f"log(f_vol_exact)/log(7/6) = {np.log(f_vol_exact)/np.log(7/6):.6f}")
alpha = np.log(f_vol_exact)/np.log(7/6)
print(f"  → f_vol_exact = (7/6)^{alpha:.4f}")
alpha_phi = np.log(f_vol_exact)/np.log(phi)
print(f"  → f_vol_exact = φ^{alpha_phi:.4f}  (close to φ^(1/3)?)")
print(f"  → φ^(1/3) diff: {(phi**(1/3) - f_vol_exact)/f_vol_exact*100:+.4f}%")

# Null-discipline test: how many random VOLUME corrections f ∈ [1.1, 1.25] land within 0.5% of f_vol_exact?
np.random.seed(42)
n = 100000
f_rand = np.random.uniform(1.1, 1.25, n)
sat_0p5 = np.sum(np.abs(f_rand - f_vol_exact)/f_vol_exact < 0.005)/n
sat_0p05 = np.sum(np.abs(f_rand - f_vol_exact)/f_vol_exact < 0.0005)/n
print(f"\nNull saturation (±0.5% of f_vol_exact): {sat_0p5*100:.2f}%")
print(f"Null saturation (±0.05% of f_vol_exact): {sat_0p05*100:.2f}%")

# Rank all candidates by proximity to f_vol_exact (the correct VOLUME correction)
candidates_ranked = {
    "7/6 = 1 + 1/(2 N_gen)": 7/6,
    "φ^(1/3) = phi^(1/N_gen)": phi**(1/3),
    "e^(1/6)": np.exp(1/6),
    "1 + 1/(2π)": 1 + 1/(2*pi),
    "1 + ln(φ)/π": 1 + np.log(phi)/pi,
    "1 + g₂²/(4π)": 1 + g2_sq/(4*pi),
    "2^(1/3)": 2**(1/3),
    "4/3": 4/3,
}
print(f"\nRanking by proximity to f_vol_exact = e^π/(2π²) = {f_vol_exact:.6f}:")
ranked = sorted(candidates_ranked.items(), key=lambda x: abs(x[1]-f_vol_exact))
for name, val in ranked:
    diff_pct = (val - f_vol_exact)/f_vol_exact * 100
    L_c = np.log2(Vol_S3 * val)
    M_c = v_PDG / (ln2/pi * L_c)**0.5
    print(f"  {name}: {val:.6f}  ({diff_pct:+.4f}%),  L={L_c:.4f} bits,  M_ref={M_c:.4f} GeV ({(M_c-v_PDG)/v_PDG*100:+.4f}%)")

best_name, best_val = ranked[0]
json.dump({
    "f_vol_exact": f_vol_exact,
    "f_vol_exact_formula": "e^π / (2π²)",
    "corrected_volume": float(np.exp(pi)),
    "corrected_volume_formula": "e^π",
    "gap_pct_S3": float((target_L-L_S3)/target_L*100),
    "best_approx": best_name,
    "best_approx_value": float(best_val),
    "best_approx_diff_pct": float((best_val - f_vol_exact)/f_vol_exact*100),
    "phi_1over3": float(phi**(1/3)),
    "phi_1over3_diff_pct": float((phi**(1/3) - f_vol_exact)/f_vol_exact*100),
    "7_over_6": float(7/6),
    "7_over_6_diff_pct": float((7/6 - f_vol_exact)/f_vol_exact*100),
    "phi_exponent_for_exact": float(np.log(f_vol_exact)/np.log(phi)),
    "null_sat_pct_0p5": float(sat_0p5*100),
    "null_sat_pct_0p05": float(sat_0p05*100),
    "ranking": [{"name": n, "value": float(v), "diff_pct": float((v-f_vol_exact)/f_vol_exact*100)} for n,v in ranked],
    "verdict": "φ^(1/3) = φ^(1/N_gen) is the best structural approximant at +0.14%; 7/6 is second at -0.47%. Both have N_gen=3 interpretation. The golden ratio connection (φ appears in IPT/SRRG) makes φ^(1/3) the most theoretically motivated candidate."
}, open("direction_I_bis.json","w"), indent=2)
print("\nSaved direction_I_bis.json")
