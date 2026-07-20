"""
g13_luscher_correction.py  —  Lüscher quantum string correction analysis for G13.

Physical question
-----------------
Two definitions of f_quant in the GTE string tension σ = ΔK × m_kink² × f_quant
disagree by 7.28%:

    f_quant(C-ratio) = 1/C_ratio = 1/1.59 = 0.6289   [P39 canonical, from C = d_break×√σ]
    f_quant(σ-ratio) = σ_PDG/σ_GTE = 0.18/0.2668 = 0.6747

Is the 7.28% gap between the two definitions explained by the Lüscher quantum string
correction in 3+1D? The Lüscher term is the leading quantum correction to the string
tension in effective string theory:

    V(R) = σ_∞ R − π(d−2)/(24R) + O(1/R³)
    σ_eff(R) = σ_∞ − π(d−2)/(24R²)          [d=4 in 3+1D → coefficient π/12]

If σ_PDG = 0.18 GeV² is the UV (large-R) string tension and the C-ratio defines
the kink-scale string tension, the Lüscher term predicts a scale R* at which the
correction equals the gap.

Results
-------
    f_quant(C-ratio)        = 0.6289
    f_quant(σ-ratio)        = 0.6747
    Gap                     = 7.28%
    Lüscher at R=1/m_kink   = 8.26%  (comparable magnitude)
    R* (exact Lüscher match)= 4.629 GeV^-1 = 0.913 fm
    1/m_kink                = 3.447 GeV^-1 = 0.680 fm
    R*/R                    = 1.343  (34% mismatch)
    Direction               = CONSISTENT (σ_PDG as UV; C-ratio as kink-scale)
    Verdict                 = NO — Lüscher suggestive but does not close G13
"""

import math, json, signal, sys, time

TIMEOUT_SECONDS = 120

def _timeout_handler(signum, frame):
    print(f"\nTIMEOUT: wall-clock limit {TIMEOUT_SECONDS}s reached. Saving partial results.")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

t_start = time.time()

# ─── GTE inputs ───────────────────────────────────────────────────────────────
delta_K      = math.log2(9)            # MDL cost of Z₃ confinement
m_tau_GeV    = 1.77686                 # tau mass, PDG 2022
m_kink_GeV   = (8 / 49) * m_tau_GeV   # BPS kink mass (CatAD)
sigma_GTE    = delta_K * m_kink_GeV**2 # classical GTE string tension (f_quant=1)

# ─── P39 canonical C-ratio definition ─────────────────────────────────────────
C_QCD     = 2.62    # d_break × sqrt(σ) experimental (QCD)
C_ratio   = 1.59    # C_GTE/C_QCD from P39 calibration
f_quant_C = 1.0 / C_ratio   # = 0.6289 ← canonical

# ─── σ-ratio definition ───────────────────────────────────────────────────────
sigma_PDG     = 0.18            # GeV²  (PDG lattice average)
f_quant_sigma = sigma_PDG / sigma_GTE  # = 0.6747

gap_pct = (f_quant_sigma - f_quant_C) / f_quant_C * 100

# ─── Physical implications ────────────────────────────────────────────────────
sigma_Cratio   = sigma_GTE * f_quant_C      # string tension from C-ratio f_quant
sigma_sigmaratio = sigma_GTE * f_quant_sigma # = sigma_PDG by definition

# ─── Lüscher correction: 3+1D effective string theory ─────────────────────────
# V(R) = σR − π(d−2)R/(24R²) → σ_eff(R) = σ_∞ − π/(12R²) for d=4
d              = 4
luscher_coeff  = math.pi * (d - 2) / 24   # π/12 for d=4
R_kink         = 1.0 / m_kink_GeV          # kink Compton length [GeV^-1]
fm_per_GeV_inv = 0.19733                   # GeV^-1 → fm

luscher_abs    = luscher_coeff / R_kink**2          # |Δσ| at R=1/m_kink [GeV²]
luscher_frac   = luscher_abs / sigma_GTE            # fractional wrt σ_GTE
sigma_eff_kink = sigma_GTE - luscher_abs             # σ_eff at R=1/m_kink (UV=σ_GTE)

# ─── R* calculation: scale at which Lüscher exactly bridges the gap ───────────
# Interpretation: σ_PDG = UV string tension; C-ratio gives kink-scale σ
# Gap: Δσ = σ_PDG − σ_Cratio = σ_GTE × (f_quant_sigma − f_quant_C)
delta_sigma = sigma_GTE * (f_quant_sigma - f_quant_C)  # should equal σ_PDG - sigma_Cratio
R_star = math.sqrt(luscher_coeff / delta_sigma)
R_star_fm = R_star * fm_per_GeV_inv

# ─── Report ───────────────────────────────────────────────────────────────────
print("=" * 70)
print("G13 LÜSCHER CORRECTION ANALYSIS")
print("=" * 70)

print(f"\nGTE inputs:")
print(f"  ΔK = log₂9        = {delta_K:.6f}")
print(f"  m_kink            = {m_kink_GeV*1000:.4f} MeV")
print(f"  σ_GTE (classical) = {sigma_GTE:.6f} GeV²")
print(f"  σ_PDG             = {sigma_PDG:.4f} GeV²")

print(f"\nTwo f_quant definitions:")
print(f"  f_quant(C-ratio)  = 1/{C_ratio} = {f_quant_C:.6f}  [P39 canonical]")
print(f"  f_quant(σ-ratio)  = σ_PDG/σ_GTE = {f_quant_sigma:.6f}")
print(f"  Gap               = {gap_pct:.2f}%")

print(f"\nImplied string tensions:")
print(f"  σ_GTE × f_quant(C-ratio)  = {sigma_Cratio:.6f} GeV²  (undershoots PDG by {(sigma_PDG-sigma_Cratio)/sigma_PDG*100:.2f}%)")
print(f"  σ_GTE × f_quant(σ-ratio)  = {sigma_sigmaratio:.6f} GeV²  (= σ_PDG by definition)")

print(f"\nLüscher correction (d=4, 3+1D):")
print(f"  Coefficient π/12 = {luscher_coeff:.6f}")
print(f"  R = 1/m_kink     = {R_kink:.4f} GeV^-1 = {R_kink*fm_per_GeV_inv:.4f} fm")
print(f"  π/(12R²) at R=1/m_kink = {luscher_abs:.6f} GeV²")
print(f"  Fractional correction   = {luscher_frac*100:.2f}% of σ_GTE  [negative, reduces σ_eff]")
print(f"  σ_eff(1/m_kink) if σ_∞=σ_GTE: {sigma_eff_kink:.6f} GeV²")

print(f"\nR* analysis (scale at which Lüscher exactly matches the gap):")
print(f"  Δσ = σ_GTE × (f_σ − f_C)  = {delta_sigma:.6f} GeV²")
print(f"  R* = sqrt(π/(12Δσ))        = {R_star:.4f} GeV^-1 = {R_star_fm:.4f} fm")
print(f"  1/m_kink                   = {R_kink:.4f} GeV^-1 = {R_kink*fm_per_GeV_inv:.4f} fm")
print(f"  R*/R = {R_star/R_kink:.4f}  (1.0 = exact kink-scale match)")

print(f"\nDirection check:")
print(f"  Lüscher: σ_eff(R) < σ_∞  (quantum < UV classical) ✓")
print(f"  If σ_∞ = σ_PDG = 0.18 and σ_eff(kink) = σ_GTE×f_C = {sigma_Cratio:.4f}: CONSISTENT ✓")
print(f"  But R* = {R_star_fm:.3f} fm ≠ 1/m_kink = {R_kink*fm_per_GeV_inv:.3f} fm  (34% mismatch)")

print(f"\n{'='*70}")
print(f"VERDICT: Does Lüscher explain the 7% gap?  NO")
print(f"  1. Magnitude: Lüscher {luscher_frac*100:.2f}% vs gap {gap_pct:.2f}%  — off by 1 ppt")
print(f"  2. Direction: consistent (σ_PDG as UV string tension)")
print(f"  3. Scale: R* = {R_star_fm:.3f} fm vs 1/m_kink = {R_kink*fm_per_GeV_inv:.3f} fm  (R*/R = {R_star/R_kink:.3f})")
print(f"  4. Full suppression σ_GTE→σ_PDG = {(1-sigma_PDG/sigma_GTE)*100:.1f}%  >>  Lüscher 8.26%")
print(f"  5. G13 remains OPEN: 3+1D lattice simulation still required")
print(f"{'='*70}")

# ─── Save JSON artifact ───────────────────────────────────────────────────────
results = {
    "GTE_inputs": {
        "delta_K":      delta_K,
        "m_kink_GeV":   m_kink_GeV,
        "sigma_GTE_GeV2": sigma_GTE,
        "sigma_PDG_GeV2": sigma_PDG,
    },
    "f_quant_definitions": {
        "f_quant_C_ratio":    f_quant_C,
        "f_quant_sigma_ratio": f_quant_sigma,
        "gap_pct":            gap_pct,
        "C_ratio":            C_ratio,
    },
    "Luscher_analysis": {
        "d_spacetime":          d,
        "luscher_coefficient":  luscher_coeff,
        "R_kink_GeV_inv":       R_kink,
        "R_kink_fm":            R_kink * fm_per_GeV_inv,
        "luscher_abs_GeV2":     luscher_abs,
        "luscher_frac_pct":     luscher_frac * 100,
        "sigma_eff_at_kink_GeV2": sigma_eff_kink,
        "delta_sigma_GeV2":     delta_sigma,
        "R_star_GeV_inv":       R_star,
        "R_star_fm":            R_star_fm,
        "R_star_over_R_kink":   R_star / R_kink,
    },
    "verdict": {
        "Luscher_explains_gap": False,
        "direction_consistent": True,
        "magnitude_match_pct_diff": abs(luscher_frac*100 - gap_pct),
        "scale_mismatch_factor": R_star / R_kink,
        "full_suppression_pct": (1 - sigma_PDG/sigma_GTE)*100,
        "G13_status": "OPEN",
        "notes": (
            "Lüscher term is suggestive: direction consistent (σ_PDG as UV), "
            "magnitude comparable (8.26% vs 7.28%), but R* = 0.913 fm ≠ 1/m_kink = 0.680 fm "
            "(34% mismatch). Full classical→quantum suppression 32.5% far exceeds Lüscher 8.26%. "
            "G13 requires 3+1D lattice simulation for definitive closure."
        ),
    },
    "elapsed_s": time.time() - t_start,
}

import os
out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "g13_luscher_correction_results.json")
with open(out_path, "w") as fh:
    json.dump(results, fh, indent=2)
print(f"\nResults saved to {out_path}")

signal.alarm(0)
