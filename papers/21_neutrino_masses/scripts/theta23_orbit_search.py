"""
theta23_orbit_search.py

Searches for GTE-motivated orbit ratios within 0.5σ of NuFIT 6.0 IC24 NH
sin²θ₂₃ = 0.470, and investigates NLO correction mechanisms.

Expected output: candidates with |val - 0.470| < 0.5 × 0.013 = 0.0065
"""

import signal
import sys
import json
from fractions import Fraction
from math import comb, sqrt, asin, pi, atan

TIMEOUT_SECONDS = 120

def _timeout_handler(signum, frame):
    print(f"\nTIMEOUT: wall-clock limit {TIMEOUT_SECONDS}s reached. Saving partial results.")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

# ============================================================
# GTE Constants (CatAL)
# ============================================================
N_gen = 3
N_fam = 5
b0 = 7        # Casimir: b0 = N_fam + N_gen - 1 = 7
c_H = 13

# GTE b-values from the cascade:
b_e   = 73   # electron: b_{L1}
b_mu  = 42   # muon: b_{L2}
b_tau = 275  # tau: b_{L3}

# Right-handed neutrino b-values (from Braid Atlas):
b_nuR1 = 5    # ν_e,R
b_nuR2 = 11   # ν_μ,R: b_{R2}
b_nuR3 = 19   # ν_τ,R: b_{R3}

# Orbit structure:
C73 = comb(7,3)  # 35
C72 = comb(7,2)  # 21
# ratio = 5/3

# Current GTE prediction:
gte_sin2_23 = Fraction(19, 42)
gte_val = float(gte_sin2_23)

# NuFIT 6.0 IC24 NH:
nufit_best = 0.470
nufit_sigma_up = 0.017
nufit_sigma_down = 0.013  # asymmetric; use down for lower edge
nufit_3sigma_low = 0.41   # sin²θ₂₃ > 0.41 at 3σ
nufit_3sigma_high = 0.49  # sin²θ₂₃ < 0.49 at 3σ

deviation_gte = (gte_val - nufit_best) / nufit_sigma_down
print("=" * 60)
print("GTE THETA_23 NLO INVESTIGATION")
print("=" * 60)
print(f"\n[Baseline]")
print(f"  GTE sin²θ₂₃ = 19/42 = {gte_val:.6f}")
print(f"  NuFIT 6.0 IC24 NH best-fit: {nufit_best}")
print(f"  Deviation: {deviation_gte:.3f}σ")
print(f"  3σ range: [{nufit_3sigma_low}, {nufit_3sigma_high}]")
print(f"  GTE within 3σ: {nufit_3sigma_low <= gte_val <= nufit_3sigma_high}")
print(f"  GTE above 1σ lower edge (0.457): {gte_val >= 0.457}")

print(f"\n[GTE Structural Constants]")
print(f"  N_gen = {N_gen}, N_fam = {N_fam}, b₀ = {b0} = N_fam + N_gen - 1")
print(f"  c_H = {c_H}")
print(f"  b_e = {b_e} (b_L1), b_μ = {b_mu} (b_L2), b_τ = {b_tau} (b_L3)")
print(f"  b_νR1 = {b_nuR1}, b_νR2 = {b_nuR2}, b_νR3 = {b_nuR3}")
print(f"  C(7,3) = {C73}, C(7,2) = {C72}, ratio = {Fraction(C73,C72)}")

# ============================================================
# Task 1: Orbit-Ratio Search (small p/q within 0.5σ of target)
# ============================================================
print(f"\n{'='*60}")
print("TASK 1: Small orbit ratios within 0.5σ of NuFIT IC24 NH")
print(f"  Target: {nufit_best}, tolerance: 0.5 × {nufit_sigma_down} = {0.5*nufit_sigma_down:.4f}")
print(f"  Search range: [{nufit_best - 0.5*nufit_sigma_down:.4f}, {nufit_best + 0.5*nufit_sigma_up:.4f}]")

tolerance_05 = 0.5 * nufit_sigma_down  # 0.0065
tolerance_1  = nufit_sigma_down         # 0.013

# GTE-notable denominators (from structure)
gte_notable = {b_e, b_mu, b_tau, b_nuR1, b_nuR2, b_nuR3, 
               b0, c_H, N_gen, N_fam, C73, C72, 
               b_e - b_mu, b_mu + b_nuR3, b_e + b_mu,  
               b_e*N_gen, b_mu*N_gen, b_tau - b_mu,
               2*b_nuR3, 2*b_mu, b_e - b_nuR3}

candidates_05 = []  # within 0.5σ
candidates_1  = []  # within 1σ

for den in range(1, 300):
    for num in range(1, den):
        val = num / den
        dev = (val - nufit_best)
        sigma_val = abs(dev) / (nufit_sigma_down if dev < 0 else nufit_sigma_up)
        if sigma_val < 1.0:
            f = Fraction(num, den)
            num_red, den_red = f.numerator, f.denominator
            is_gte = (num_red in gte_notable or den_red in gte_notable or
                      num_red + den_red in gte_notable or
                      abs(num_red - den_red) in gte_notable)
            entry = {
                'fraction': f'{num_red}/{den_red}',
                'value': float(f),
                'deviation_sigma': round(sigma_val, 4),
                'numerator': num_red,
                'denominator': den_red,
                'gte_notable': is_gte,
                'dev_from_gte': round(float(f) - gte_val, 6),
            }
            if sigma_val < 0.5:
                candidates_05.append(entry)
            else:
                candidates_1.append(entry)

# Sort by deviation
candidates_05.sort(key=lambda x: x['deviation_sigma'])
candidates_1.sort(key=lambda x: x['deviation_sigma'])

print(f"\nWithin 0.5σ ({len(candidates_05)} candidates):")
for c in candidates_05[:20]:
    gte_marker = " ★GTE" if c['gte_notable'] else ""
    print(f"  {c['fraction']:>8} = {c['value']:.6f}, {c['deviation_sigma']:.3f}σ, "
          f"Δ from 19/42: {c['dev_from_gte']:+.5f}{gte_marker}")

print(f"\nWithin 1σ (first 15, non-0.5σ):")
for c in candidates_1[:15]:
    gte_marker = " ★GTE" if c['gte_notable'] else ""
    print(f"  {c['fraction']:>8} = {c['value']:.6f}, {c['deviation_sigma']:.3f}σ, "
          f"Δ from 19/42: {c['dev_from_gte']:+.5f}{gte_marker}")

# ============================================================
# Task 2: NLO Correction Mechanisms
# ============================================================
print(f"\n{'='*60}")
print("TASK 2: NLO Correction Mechanisms")

# --- Mechanism A: ℤ₃ generation correction to the orbit ratio ---
gap = nufit_best - gte_val  # 0.0176 needed
fractional_gap = gap / gte_val  # ~3.9%

print(f"\nMechanism A: Direct fractional correction to 19/42")
print(f"  Gap needed: {gap:.6f}")
print(f"  Fractional correction needed: {fractional_gap:.4f} = {fractional_gap*100:.2f}%")
print(f"  (For reference: ε_Z5 in θ₁₂ NLO ~ 4λ² = 81/400 = {81/400:.4f} = 20.25%)")
print(f"  A small GTE fraction near {fractional_gap:.4f} would close the gap")

# Search for small GTE fractions near the needed correction
print(f"\n  Small GTE fractions near {fractional_gap:.4f} (for additive correction):")
for num in range(1, 50):
    for den in range(num+1, 500):
        if abs(num/den - fractional_gap) < 0.001:
            f = Fraction(num, den)
            n, d = f.numerator, f.denominator
            is_gte = (n in gte_notable or d in gte_notable or 
                      n+d in gte_notable)
            gte_marker = " ★GTE" if is_gte else ""
            print(f"    {n}/{d} = {float(f):.5f} (vs needed {fractional_gap:.5f}){gte_marker}")

# --- Mechanism B: Transit-factor correction ---
print(f"\nMechanism B: Transit-factor additive correction")
transit_23 = Fraction(b_nuR2, b_tau)  # 11/275
transit_23_sq = float(transit_23)**2
corrected_B = gte_val + transit_23_sq
dev_B = (corrected_B - nufit_best) / nufit_sigma_down
print(f"  Transit factor b_νR2/b_τ = {b_nuR2}/{b_tau} = {float(transit_23):.5f}")
print(f"  (transit)² = {transit_23_sq:.6f}")
print(f"  sin²θ₂₃ + (transit)² = {gte_val:.6f} + {transit_23_sq:.6f} = {corrected_B:.6f}")
print(f"  Deviation from NuFIT: {dev_B:.3f}σ")

t2 = Fraction(b_nuR1, b_tau)  # 5/275
corrected_B2 = gte_val + float(t2)**2
dev_B2 = (corrected_B2 - nufit_best) / nufit_sigma_down
print(f"\n  Transit factor b_νR1/b_τ = {b_nuR1}/{b_tau} = {float(t2):.5f}")
print(f"  sin²θ₂₃ + (transit)² = {corrected_B2:.6f}, deviation = {dev_B2:.3f}σ")

# --- Mechanism C: F₂₁ off-diagonal correction ---
print(f"\nMechanism C: F₂₁ off-diagonal correction O(1/21)")
corr_F21 = 1.0 / 21.0
corrected_C_mult = gte_val * (1 + corr_F21)
dev_C = (corrected_C_mult - nufit_best) / nufit_sigma_up
print(f"  O(1/21) = {corr_F21:.5f}")
print(f"  19/42 × (1 + 1/21) = {corrected_C_mult:.6f}, deviation = {dev_C:+.3f}σ (using σ_up)")
val_22_21 = gte_val * Fraction(22, 21)
dev_22_21 = (float(val_22_21) - nufit_best) / nufit_sigma_up
print(f"  19/42 × 22/21 = 19×22/(42×21) = {19*22}/{42*21} = {Fraction(19*22, 42*21)} = {float(val_22_21):.6f}")
print(f"  Deviation: {dev_22_21:+.3f}σ from NuFIT IC24 NH 0.470")
f_check = Fraction(19*22, 42*21)
print(f"  Reduced form: {f_check} = {float(f_check):.6f}")

# --- Mechanism D: Z₇ orbit phase correction ---
print(f"\nMechanism D: ℤ₇ missing-position correction")
z7_missing = 2   # positions {1,5} not occupied by SM
z7_occupied = 5  # SM occupies {0,2,3,4,6}
corr_D = Fraction(z7_missing, 7)
next_ratio = Fraction(b_nuR3, b_tau)  # 19/275
print(f"  b_νR3/b_τ = {b_nuR3}/{b_tau} = {float(next_ratio):.5f}")
avg_ratio = (gte_val + float(next_ratio)) / 2
print(f"  Average (19/42 + 19/275)/2 = {avg_ratio:.5f}, dev = {(avg_ratio - nufit_best)/nufit_sigma_down:.3f}σ")

# --- Mechanism E: Casimir correction ---
C74 = comb(7,4)  # 35
C71 = comb(7,1)  # 7
print(f"\nMechanism E: Casimir combinatorial correction")
print(f"  C(7,3) = {C73}, C(7,4) = {C74}, C(7,2) = {C72}, C(7,1) = {C71}")

# --- Mechanism F: N_eff weighted ratio ---
print(f"\nMechanism F: N_eff weighted orbit correction")
denom_F = Fraction(b_mu*N_gen - b_nuR2, N_gen)  # (42×3 - 11)/3 = 115/3
val_F = Fraction(b_nuR3, 1) / denom_F
print(f"  b_{{L2}} - b_{{R2}}/N_gen = {b_mu} - {b_nuR2}/{N_gen} = {denom_F}")
print(f"  19 / (115/3) = 57/115 = {float(Fraction(57,115)):.6f}")
dev_F = (float(val_F) - nufit_best) / nufit_sigma_down
print(f"  Value: {val_F} = {float(val_F):.6f}, deviation: {dev_F:.3f}σ")

print(f"\nMechanism G: Additive orbit index corrections")
val_20_42 = Fraction(20, 42)
dev_20 = (float(val_20_42) - nufit_best) / nufit_sigma_down
print(f"  20/42 = {val_20_42} = {float(val_20_42):.6f}, dev = {dev_20:.3f}σ")
val_19_40 = Fraction(19, 40)
dev_19_40 = (float(val_19_40) - nufit_best) / nufit_sigma_down
print(f"  19/40 = {float(val_19_40):.6f}, dev = {dev_19_40:.3f}σ")

# --- Mechanism H: Average of two GTE orbit ratios ---
print(f"\nMechanism H: Average of RH neutrino b-values with LH b-values")
val_h1 = (Fraction(b_nuR2, b_mu) + Fraction(b_nuR3, b_mu)) / 2
print(f"  (b_{{R2}}/b_{{L2}} + b_{{R3}}/b_{{L2}})/2 = ({b_nuR2}/{b_mu} + {b_nuR3}/{b_mu})/2 = {val_h1} = {float(val_h1):.6f}")
dev_h1 = (float(val_h1) - nufit_best) / nufit_sigma_down
print(f"  Deviation: {dev_h1:.3f}σ")

val_h2 = Fraction(b_nuR2 + b_nuR3, 2 * b_mu)
print(f"  (b_{{R2}} + b_{{R3}}) / (2 × b_{{L2}}) = ({b_nuR2}+{b_nuR3})/(2×{b_mu}) = {b_nuR2+b_nuR3}/{2*b_mu} = {val_h2} = {float(val_h2):.6f}")
dev_h2 = (float(val_h2) - nufit_best) / nufit_sigma_down
print(f"  Deviation: {dev_h2:.3f}σ")

denom_h3 = b_mu - b_nuR1  # 42 - 5 = 37
val_h3 = Fraction(b_nuR3, denom_h3)
print(f"  b_{{R3}} / (b_{{L2}} - b_{{R1}}) = {b_nuR3}/{denom_h3} = {val_h3} = {float(val_h3):.6f}")
dev_h3 = (float(val_h3) - nufit_best) / nufit_sigma_down
print(f"  Deviation: {dev_h3:.3f}σ")

# --- Mechanism I: Phenomenological check of the ℤ₃ NLO analog ---
print(f"\nMechanism I: ℤ₃/ℤ₅ NLO analog")
corr_I = Fraction(1, N_gen * N_fam)  # 1/15
val_I = gte_val * (1 + float(corr_I))
dev_I = (val_I - nufit_best) / nufit_sigma_down
print(f"  NLO factor: 1 + 1/(N_gen × N_fam) = 1 + 1/15 = {1 + float(corr_I):.5f}")
print(f"  19/42 × (1 + 1/15) = {val_I:.6f}, deviation = {dev_I:.3f}σ")

corr_I2 = Fraction(1, N_gen**2)  # 1/9
val_I2 = gte_val * (1 + float(corr_I2))
dev_I2 = (val_I2 - nufit_best) / nufit_sigma_down
print(f"  NLO factor: 1 + 1/N_gen² = 1 + 1/9 = {1+float(corr_I2):.5f}")
print(f"  19/42 × (1 + 1/9) = {val_I2:.6f}, deviation = {dev_I2:.3f}σ")

# --- Mechanism J: Strand² correction ---
strand = 2
corr_J = (strand/b_mu)**2
val_J = gte_val + corr_J
dev_J = (val_J - nufit_best) / nufit_sigma_down
print(f"\nMechanism J: Strand² correction")
print(f"  strand²/b_{{L2}}² = {strand}²/{b_mu}² = {4}/{42**2} = {corr_J:.6f}")
print(f"  19/42 + {corr_J:.6f} = {val_J:.6f}, deviation = {dev_J:.3f}σ")

# --- Mechanism K: Casimir orbit sum formula ---
print(f"\nMechanism K: Casimir-shifted orbit denominator")
print(f"  (b_{{R3}}) / (b_{{L2}} - b₀) = {b_nuR3}/{b_mu - b0} = {Fraction(b_nuR3, b_mu - b0)} = {float(Fraction(b_nuR3, b_mu - b0)):.6f}")
dev_K = (float(Fraction(b_nuR3, b_mu - b0)) - nufit_best) / nufit_sigma_down
print(f"  Deviation: {dev_K:.3f}σ")
print(f"  Note: b_{{L2}} - b₀ = {b_mu} - {b0} = {b_mu - b0} = C(7,3) = {C73}")
val_K2 = Fraction(b_nuR3, b_mu + b0)
print(f"  {b_nuR3}/{b_mu + b0} = {val_K2} = {float(val_K2):.6f}")
dev_K2 = (float(val_K2) - nufit_best) / nufit_sigma_down
print(f"  Deviation: {dev_K2:.3f}σ")

# ============================================================
# Task 3: Best NLO Candidate Summary
# ============================================================
print(f"\n{'='*60}")
print("TASK 3: SUMMARY OF NLO CANDIDATES")
print(f"{'='*60}")
print(f"\nBaseline: 19/42 = {gte_val:.6f}, deviation = {deviation_gte:.3f}σ from NuFIT IC24 NH")
print(f"\nCandidate NLO formulas (sorted by σ deviation):")

candidates_nlo = [
    ("22/21 correction: 19/42 × (22/21)", float(Fraction(19*22, 42*21)), "F₂₁ off-diagonal O(1/21)"),
    ("Transit add: 19/42 + (b_νR2/b_τ)²", gte_val + (b_nuR2/b_tau)**2, "Transit factor sq"),
    ("(b_R2+b_R3)/(2×b_L2) = 15/21", float(Fraction(b_nuR2+b_nuR3, 2*b_mu)), "Average RH ν b-values"),
    ("19/42 × (1+1/15)", gte_val*(1+1/15), "ℤ₃×ℤ₅ NLO"),
    ("19/42 × (1+1/9)", gte_val*(1+1/9), "ℤ₃² NLO"),
    ("b_R3/(b_L2-b_R1) = 19/37", float(Fraction(b_nuR3, b_mu-b_nuR1)), "Shifted denominator"),
]

for name, val, mechanism in candidates_nlo:
    if val < 1.0:
        dev = (val - nufit_best) / (nufit_sigma_down if val < nufit_best else nufit_sigma_up)
        print(f"  {dev:+.3f}σ | {val:.6f} | {name}")
        print(f"           Mechanism: {mechanism}")

# ============================================================
# Task 4: Null test — verify 19/42 is tight
# ============================================================
print(f"\n{'='*60}")
print("TASK 4: NULL TEST — Adjacent orbit ratios")
print(f"  (Testing that 19/42 is NOT lucky — nearby ratios land elsewhere)")
print()
null_ratios = [
    (18, 42, "b_R3-1 / b_L2"),
    (20, 42, "b_R3+1 / b_L2"),
    (19, 41, "b_R3 / b_L2-1"),
    (19, 43, "b_R3 / b_L2+1"),
    (18, 40, "shifted down"),
    (20, 44, "shifted up"),
]
for num, den, name in null_ratios:
    val = num/den
    dev = (val - nufit_best) / (nufit_sigma_down if val < nufit_best else nufit_sigma_up)
    print(f"  {num}/{den} = {val:.6f}, dev = {dev:+.3f}σ — {name}")

# ============================================================
# Save results
# ============================================================
results = {
    "theta23_NLO_investigation": "GTE sin²θ₂₃ = 19/42 NLO mechanisms (P21)",
    "gte_prediction": {"fraction": "19/42", "value": gte_val, "sigma_deviation": float(f"{deviation_gte:.4f}")},
    "nufit_ic24_nh": {"best_fit": nufit_best, "sigma_up": nufit_sigma_up, "sigma_down": nufit_sigma_down},
    "candidates_within_05sigma": candidates_05[:10],
    "candidates_within_1sigma": candidates_1[:10],
    "nlo_mechanisms_tested": len(candidates_nlo),
    "nlo_candidates": [{"name": n, "value": round(v,6), "sigma": round((v-nufit_best)/(nufit_sigma_down if v < nufit_best else nufit_sigma_up),3)} for n,v,m in candidates_nlo if v < 1.0],
    "verdict": "PENDING — see session analysis",
}
with open("theta23_orbit_search_results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"\nResults saved to theta23_orbit_search_results.json")
signal.alarm(0)
print("\nDONE.")
