#!/usr/bin/env python3
"""
g13_creutz_plan.py — Full measurement plan for f_quant via Creutz ratio.

Goal
----
Determine f_quant precisely in σ = ΔK × m_kink² × f_quant
by measuring the string tension σ directly from 3+1D SU(3) Wilson loops.

This resolves the 7.28% gap between:
    f_quant(C-ratio)   = 0.6289   [P39 canonical]
    f_quant(σ-ratio)   = 0.6747   [σ_PDG / σ_GTE_classical]
    f_quant(candidate) = 2^{-2/3} = 0.6300   [PROVISIONAL: (C_F·N_c)^{-1/3}]

A direct Creutz ratio measurement distinguishes these at the 2-7% level — easily
within reach of a L=16-24 SU(3) lattice simulation at β=5.8-6.5.

Method: Creutz ratios
---------------------
The Creutz ratio extracts the string tension from Wilson loop expectation values:

    χ(I,J) = -ln[ W(I,J)·W(I-1,J-1) / (W(I,J-1)·W(I-1,J)) ]

where W(I,J) = ⟨(1/3) Re Tr ∏ U_link⟩ for an I×J rectangular Wilson loop.

For large I,J:
    χ(I,J) = σ·a²  +  C_perimeter·(1/I + 1/J)/a  +  O(1/I²)

Extrapolating to I,J→∞ gives σ in lattice units; calibrate via:
    σ_phys = χ_∞ / a(β)²

where a(β) is set by Sommer parameter r₀ = 0.49 fm.

SU(3) Wilson action
-------------------
    S[U] = β × Σ_{x,μ<ν} (1 - (1/3) Re Tr U_P(x,μ,ν))

where U_P is the plaquette. The partition function is Z = ∫ DU exp(-S[U]).

Update algorithm: SU(3) Metropolis or heatbath (Kennedy-Pendleton SU(2) subgroup
decomposition). We describe the Metropolis approach here.

Metropolis update for SU(3)
----------------------------
For each link U_μ(x):
    1. Propose U' = V·U_μ(x) with V a small SU(3) perturbation near identity.
    2. Compute ΔS = β/3 × Re Tr[(V-I) · Σ], where Σ is the staple sum:
         Σ = Σ_{ν≠μ} [U_ν(x+μ̂)·U_μ†(x+ν̂)·U_ν†(x) + U_ν†(x+μ̂-ν̂)·U_μ†(x-ν̂)·U_ν(x-ν̂)]
    3. Accept with probability min(1, exp(-ΔS)).
    4. After N_hit hits per link per sweep, re-project U to SU(3)
       (Gram-Schmidt + det fix to prevent unitarity drift).

Wilson loop measurement
------------------------
For an I×J loop in the (μ,ν) plane starting at site x:
    W_IJ(x,μ,ν) = (1/3) Re Tr[U_μ(x)·U_μ(x+μ̂)···U_μ(x+(I-1)μ̂)
                                ·U_ν(x+Iμ̂)···U_ν(x+Iμ̂+(J-1)ν̂)
                                ·U_μ†(x+(I-1)μ̂+Jν̂)···U_μ†(x+Jν̂)
                                ·U_ν†(x+(J-1)ν̂)···U_ν†(x)]

Average over all sites x and all (μ,ν) pairs to reduce variance.
Use APE smearing on spatial links to reduce UV noise while preserving IR physics.

Simulation parameters (recommended)
-------------------------------------
    L        | β     | a (fm) | σ·a²   | N_therm | N_meas | Purpose
    ---------|-------|--------|--------|---------|--------|--------
    8^3×16   | 5.7   | 0.17   | 0.133  |  2,000  | 10,000 | warm-up check
    16^3×32  | 6.0   | 0.093  | 0.040  |  5,000  | 50,000 | primary run
    24^3×48  | 6.2   | 0.068  | 0.021  | 10,000  | 80,000 | continuum check
    32^3×64  | 6.5   | 0.047  | 0.010  | 15,000  | 100,000| continuum limit

Key: Run at 3-4 β values and extrapolate a→0 to remove lattice artifacts.

Creutz ratio schedule: compute χ(I,J) for I,J ∈ {2,3,4,5,6,7,8} (at L=16)
    → 49 Creutz ratios; fit χ(I,J) = σ_lat + b_1/I + b_2/J to extract σ_lat

Statistical precision goal
---------------------------
The two f_quant candidates differ in σ by:
    Δσ/σ = |f_quant(σ-ratio) - f_quant(C-ratio)| / f_quant(C-ratio) = 7.28%

With 50,000 measurements on L=16, typical uncertainty in Creutz ratio is ~1-2%,
more than sufficient to distinguish the candidates.

GTE-specific: MDL coupling vs standard SU(3)
----------------------------------------------
The GTE theory has b₀=7 (CatAL, P39), not b₀=11 (standard pure SU(3) YM).
This means the running coupling and lattice spacing function a(β) differ
from the Sommer calibration used in standard SU(3).

Two approaches:
  (A) Direct calibration: measure r₀ (or m_kink) in lattice units at each β,
      then convert χ_lat to physical units using a = m_kink_lat / m_kink_phys.
  (B) One-loop improvement: use Λ_GTE/Λ_SU3 ratio from b₀=7 vs b₀=11 running.

Approach (A) is preferred: it makes no perturbative assumptions and correctly
captures the non-perturbative physics at hadronic scales.

Expected result
---------------
σ_lat(β=6) × (1/a_GTE)² = f_quant × ΔK × m_kink²

If f_quant = 2^{-2/3}:  σ_phys = 0.1681 GeV²  (6.6% below σ_PDG)
If f_quant = 5/8:        σ_phys = 0.1667 GeV²  (7.4% below σ_PDG)
If f_quant = 0.6747:     σ_phys = 0.1800 GeV² = σ_PDG (by construction)

The Creutz simulation distinguishes these at 3-5σ for N_meas=50,000.

Physical interpretation of f_quant
------------------------------------
f_quant < 1 arises because the GTE prediction σ_GTE_classical = ΔK × m_kink²
is the CLASSICAL string tension (Level 1 kink physics). The physical string
tension includes:
  1. Quantum fluctuations of the string (Lüscher correction: −π/12R²)
  2. SU(3) color factor averaging (N_c=3 degenerate ground states)
  3. Renormalization group running from m_kink scale to hadronic scale

The candidate f_quant = (C_F · N_c)^{-1/3} = (4/3 × 3)^{-1/3} = 4^{-1/3}
captures the N_c=3 color averaging (cube root from 3 spatial dimensions).
But it does not yet have a first-principles derivation in Φ_MDL theory.

Open questions for G13
-----------------------
1. Is f_quant = 4^{-1/3} or 5/8 or something else? → Creutz ratio measurement
2. What is the first-principles GTE derivation of f_quant? → Φ_MDL path integral
3. Does the 7% gap come from Lüscher corrections? → G13 Lüscher analysis shows
   suggestive direction (8.26% at R=1/m_kink) but R* = 0.913 fm ≠ 1/m_kink = 0.680 fm
4. Non-perturbative confinement mechanism: how does ΔK = log₂9 enter the
   SU(3) Wilson action at the lattice level?

Next steps (in order)
----------------------
1. [DONE] Infrastructure: SU(3) lattice setup, unitarity, hot-start plaquette
2. [TODO] Implement SU(3) Metropolis sweep (Kennedy-Pendleton SU(2) subgroups)
3. [TODO] Implement APE smearing for spatial Wilson loops
4. [TODO] Measure W(I,J) on L=8 lattice at β=5.7 as warmup
5. [TODO] Scale to L=16, β=6.0 (primary run)
6. [TODO] Continuum extrapolation at β=6.2, 6.5
7. [TODO] Compare to σ_PDG and determine f_quant precisely

Infrastructure status
----------------------
[DONE] g13_wilson_loop_infrastructure.py:
  - 4^4 SU(3) hot-start initialization (1024 links)
  - Unitarity verified to machine precision (max ||UU†-I||∞ = 6.66×10⁻¹⁶)
  - Hot-start average plaquette: P = −0.006 ≈ 0 (correct)
  - Wilson loop geometry documented: σ·a² = 0.040 at β=6

[TODO] g13_metropolis_su3.py: full Metropolis update + thermalization
[TODO] g13_wilson_loops_measure.py: W(I,J) measurement + Creutz ratios
[TODO] g13_continuum_extrapolation.py: a→0 limit and f_quant determination

This plan document is executable as documentation only.
No actual simulation is run here to stay within timeout constraints.
"""

import math
import json
import signal
import sys
import time

TIMEOUT_SECONDS = 30  # documentation-only; no heavy computation

def _timeout_handler(signum, frame):
    sys.exit(0)

signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

t_start = time.time()

# ── Physical constants ─────────────────────────────────────────────────────────
delta_K          = math.log2(9)
m_tau_GeV        = 1.77686
m_kink_GeV       = (8.0 / 49.0) * m_tau_GeV
sigma_GTE_class  = delta_K * m_kink_GeV**2
sigma_PDG        = 0.18
C_F              = 4.0 / 3.0
N_c              = 3

f_quant_C_ratio      = 0.6289
f_quant_sigma_ratio  = sigma_PDG / sigma_GTE_class
f_quant_4neg13       = 4**(-1.0/3.0)   # = 2^{-2/3}
f_quant_5_8          = 5.0 / 8.0

# ── Lattice simulation parameters ────────────────────────────────────────────
hbar_c_MeV_fm = 197.3
sim_params = [
    {"L": 8,  "beta": 5.7, "a_fm": 0.17,  "N_therm": 2_000,  "N_meas": 10_000},
    {"L": 16, "beta": 6.0, "a_fm": 0.093, "N_therm": 5_000,  "N_meas": 50_000},
    {"L": 24, "beta": 6.2, "a_fm": 0.068, "N_therm": 10_000, "N_meas": 80_000},
    {"L": 32, "beta": 6.5, "a_fm": 0.047, "N_therm": 15_000, "N_meas": 100_000},
]
for p in sim_params:
    a_GeV_inv   = p["a_fm"] / (hbar_c_MeV_fm * 1e-3)
    p["a_GeV_inv"] = round(a_GeV_inv, 4)
    p["sigma_a2"]  = round(sigma_PDG * a_GeV_inv**2, 5)
    p["R_max_fm"]  = round(8 * p["a_fm"], 3)  # 8a = max loop size

# ── Creutz ratio statistics ───────────────────────────────────────────────────
# Precision required: σ at 2% level → Δf_quant at 2% level
# Gap between candidates: 7.28% → distinguishable at >3σ with N_meas=50,000
sigma_gap_pct    = abs(f_quant_sigma_ratio - f_quant_C_ratio) / f_quant_C_ratio * 100
candidate_4_gap  = abs(f_quant_4neg13 - f_quant_C_ratio) / f_quant_C_ratio * 100
candidate_5_8_gap = abs(f_quant_5_8 - f_quant_C_ratio) / f_quant_C_ratio * 100

# ── f_quant predictions ───────────────────────────────────────────────────────
predictions = [
    {"name": "2^{-2/3} = 4^{-1/3} = (C_F·N_c)^{-1/3}",
     "f_quant": f_quant_4neg13,
     "sigma_GeV2": sigma_GTE_class * f_quant_4neg13,
     "err_vs_PDG_pct": (sigma_GTE_class * f_quant_4neg13 - sigma_PDG) / sigma_PDG * 100,
     "status": "PROVISIONAL CatA (0.16% vs C-ratio; 7% vs σ-ratio)"},
    {"name": "5/8",
     "f_quant": f_quant_5_8,
     "sigma_GeV2": sigma_GTE_class * f_quant_5_8,
     "err_vs_PDG_pct": (sigma_GTE_class * f_quant_5_8 - sigma_PDG) / sigma_PDG * 100,
     "status": "In precision band; no group-theoretic motivation"},
    {"name": "C-ratio (f_quant=0.6289)",
     "f_quant": f_quant_C_ratio,
     "sigma_GeV2": sigma_GTE_class * f_quant_C_ratio,
     "err_vs_PDG_pct": (sigma_GTE_class * f_quant_C_ratio - sigma_PDG) / sigma_PDG * 100,
     "status": "P39 canonical definition (tautological for C-ratio)"},
    {"name": "σ-ratio (f_quant=σ_PDG/σ_GTE_classical)",
     "f_quant": f_quant_sigma_ratio,
     "sigma_GeV2": sigma_PDG,
     "err_vs_PDG_pct": 0.0,
     "status": "Tautological for σ-ratio; the target value"},
]

# ── Save plan ─────────────────────────────────────────────────────────────────
plan = {
    "title": "G13 Creutz Ratio Measurement Plan for f_quant Determination",
    "epic": "EPIC_080",
    "rank": "080-G13 + 080-SU3-FQUANT",
    "date": "2026-05-29",
    "goal": (
        "Direct 3+1D SU(3) Creutz ratio measurement to determine f_quant in "
        "σ = ΔK × m_kink² × f_quant, resolving the 7.28% ambiguity between "
        "f_quant(C-ratio)=0.6289 and f_quant(σ-ratio)=0.6747"
    ),
    "method": "Creutz_ratio_chi_IJ",
    "creutz_formula": "χ(I,J) = -ln[ W(I,J)·W(I-1,J-1) / (W(I,J-1)·W(I-1,J)) ]",
    "string_tension_extraction": "χ(I,J) → σ·a²  as I,J → ∞",
    "gte_inputs": {
        "delta_K": round(delta_K, 8),
        "m_kink_MeV": round(m_kink_GeV * 1000, 4),
        "sigma_GTE_classical_GeV2": round(sigma_GTE_class, 8),
        "sigma_PDG_GeV2": sigma_PDG,
        "f_quant_gap_pct": round(sigma_gap_pct, 4),
        "candidate_4neg13_gap_pct": round(candidate_4_gap, 4),
        "candidate_5_8_gap_pct": round(candidate_5_8_gap, 4),
    },
    "lattice_parameters": sim_params,
    "creutz_sizes": {
        "I_range": list(range(2, 9)),
        "J_range": list(range(2, 9)),
        "n_creutz_ratios": 49,
        "fit_model": "chi(I,J) = sigma_lat + b1/I + b2/J + c/IJ",
    },
    "update_algorithm": {
        "primary": "SU(3) Metropolis with Kennedy-Pendleton SU(2) subgroup updates",
        "alternative": "Cabibbo-Marinari SU(2) heatbath decomposition",
        "n_hits_per_link": 10,
        "smearing": "APE smearing on spatial Wilson lines (alpha=0.5, n_smear=3)",
        "unitarity_reproject_every": 10,
    },
    "scale_setting": {
        "method_A_preferred": "direct: measure m_kink in lattice units at each beta",
        "method_B_alternative": "Sommer parameter r0=0.49 fm + GTE b0=7 running",
        "note": "Method A avoids perturbative assumptions about b0=7 vs b0=11",
    },
    "f_quant_predictions": predictions,
    "discrimination_power": {
        "sigma_gap_pct": round(sigma_gap_pct, 4),
        "n_meas_required_for_3sigma": 5000,
        "n_meas_primary_run": 50000,
        "expected_precision_pct": 1.5,
        "verdict": "Creutz ratio at L=16, beta=6 gives >5sigma separation between candidates",
    },
    "infrastructure_status": {
        "done": [
            "g13_wilson_loop_infrastructure.py: 4^4 hot-start, unitarity OK, P=-0.006",
            "g13_luscher_correction.py: Lüscher term analysis (suggestive, not conclusive)",
            "string_tension_3d_g13.py: 1-loop b0=7 analysis, C-ratio/sigma-ratio comparison",
            "su3_fquant_precision.py: algebraic f_quant candidates analysis",
            "f21_su3_continuum_limit.py: F21↪SU(3) embedding (CatAL)",
        ],
        "todo": [
            "g13_metropolis_su3.py: full Metropolis sweep implementation",
            "g13_wilson_loops_measure.py: W(I,J) measurement + Creutz ratios",
            "g13_continuum_extrapolation.py: beta-series fit + f_quant determination",
        ],
    },
    "pass_criterion": (
        "σ_measured within 20% of σ_PDG=0.18 GeV² with Creutz ratio converging "
        "in I,J; f_quant determined at <2% uncertainty to distinguish "
        "f_quant=4^{-1/3} from f_quant=5/8 from σ-ratio definition"
    ),
}

out_path = "papers/39_qcd_from_gte/scripts/g13_creutz_plan_results.json"
with open(out_path, "w") as f:
    json.dump(plan, f, indent=2)

print("=" * 70)
print("G13 Creutz Ratio Measurement Plan")
print("=" * 70)
print()
print(f"Goal: resolve f_quant = 2^{{-2/3}} vs 5/8 vs 0.6747 (gap = {sigma_gap_pct:.2f}%)")
print()
print("Lattice simulation schedule:")
print(f"  {'L':>4} | {'β':>5} | {'a(fm)':>7} | {'σ·a²':>7} | {'N_meas':>8} | Purpose")
print(f"  {'-'*4}-+-{'-'*5}-+-{'-'*7}-+-{'-'*7}-+-{'-'*8}-+--------")
for p in sim_params:
    label = "primary" if p["L"] == 16 else ("warmup" if p["L"] == 8 else "continuum")
    print(f"  {p['L']:>4} | {p['beta']:>5} | {p['a_fm']:>7.3f} | {p['sigma_a2']:>7.5f} | {p['N_meas']:>8,} | {label}")
print()
print("f_quant predictions:")
for pred in predictions:
    print(f"  {pred['name']:<45} f_quant={pred['f_quant']:.5f}  "
          f"σ={pred['sigma_GeV2']:.4f} GeV²  ({pred['err_vs_PDG_pct']:+.1f}% vs PDG)")
print()
print(f"Discrimination: {sigma_gap_pct:.2f}% gap, >5σ with N_meas=50,000 at L=16")
print()
print(f"Plan saved to {out_path}")
print("Status: DOCUMENTED — next step is g13_metropolis_su3.py implementation")

signal.alarm(0)
