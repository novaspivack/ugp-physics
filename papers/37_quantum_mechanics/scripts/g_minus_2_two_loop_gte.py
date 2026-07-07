"""
EPIC_073 Rank 070-139 — (g−2)_μ beyond one loop: GTE two-loop and Fermilab anomaly assessment.

Assesses whether GTE predicts a two-loop (or hadronic) correction to a_μ comparable to
Δa_μ = a_μ^exp − a_μ^SM ≈ 2.49×10⁻⁹ (Fermilab 2023 vs PDG SM).

Prerequisites: 070-131 (one-loop CatA: a_μ^{GTE,1L} = 1/(274π)).

Sections:
  1. Standard two-loop QED with α_GTE = 1/137
  2. GTE-specific channels: Z₇ orbit, Φ_MDL kink VP, PSC/HVP scaling
  3. SM decomposition and gap closure analysis
  4. Fermilab anomaly falsifiability verdict

References:
  - Kinoshita et al., two-loop QED coefficient C₂ ≈ 0.765758490
  - PDG 2023 a_μ^SM breakdown (×10⁻¹¹ units)
  - P39: m_π^GTE = 136.485 MeV (GOR inversion, Rank 144-PIMASSFP)
  - P34/P39: M_kink = (8/49) m_τ = 290.10 MeV
"""

from __future__ import annotations

import json
import math
import signal
import sys
import time
from fractions import Fraction
from pathlib import Path

TIMEOUT_SECONDS = 300
OUTPUT_JSON = Path(__file__).with_name("g_minus_2_two_loop_gte_results.json")


def _timeout_handler(signum, frame):
    print(f"\nTIMEOUT: wall-clock limit {TIMEOUT_SECONDS}s reached. Saving partial results.")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
alpha_GTE = Fraction(1, 137)
alpha_PDG = 1 / 137.035999084
C2_QED = 0.765758490  # Kinoshita two-loop QED coefficient for a_μ

m_mu_MeV = 105.6583755
m_pi_PDG_MeV = 134.98
m_pi_GTE_MeV = 136.485  # Rank 144-PIMASSFP GOR inversion (P39)
M_kink_MeV = (8 / 49) * 1776.86  # (8/49) m_τ, m_τ GTE ≈ 1776.86 MeV

# PDG / Fermilab 2023 (same as 070-131)
a_mu_SM = 116591810e-11
a_mu_SM_err = 43e-11
a_mu_exp = 116592059e-11
a_mu_exp_err = 22e-11
delta_a_mu_obs = a_mu_exp - a_mu_SM

# SM sub-contributions (×10⁻¹¹), PDG 2023 / theory review consensus
a_mu_QED_total = 116584771e-11
a_mu_QED_1L = alpha_PDG / (2 * math.pi)
a_mu_had_total = 6937e-11
a_mu_hvp_lo = 6843e-11  # hadronic vacuum polarization (leading)
a_mu_hlbl = 94e-11  # light-by-light (approximate split)
a_mu_ew = 154e-11

t0 = time.time()

# ---------------------------------------------------------------------------
# Part 1: Two-loop QED
# ---------------------------------------------------------------------------
alpha_gte_f = float(alpha_GTE)
a_mu_GTE_1L = alpha_gte_f / (2 * math.pi)
a_mu_GTE_274pi = 1.0 / (274.0 * math.pi)

a_mu_GTE_2L_QED = (alpha_gte_f / math.pi) ** 2 * C2_QED
a_mu_PDG_2L_QED = (alpha_PDG / math.pi) ** 2 * C2_QED

a_mu_GTE_12L = a_mu_GTE_1L + a_mu_GTE_2L_QED

# Gap from GTE (1L+2L QED only) to full SM
gap_gte_qed12_to_sm = a_mu_SM - a_mu_GTE_12L

# Does two-loop QED close the Fermilab anomaly?
ratio_2L_to_anomaly = a_mu_GTE_2L_QED / abs(delta_a_mu_obs)
closes_anomaly_2L = abs(a_mu_GTE_2L_QED - delta_a_mu_obs) < 0.5e-9

# ---------------------------------------------------------------------------
# Part 2: GTE-specific channels
# ---------------------------------------------------------------------------

# 2a. Z₇ orbit correction — no two-loop mechanism in framework (070-131: none at 1L)
z7_orbit_correction = 0.0
z7_status = "NO_MECHANISM"
z7_note = (
    "One-loop GTE chain uses standard Schwinger vertex with α_GTE; no Z₇ orbit "
    "modification is established at one or two loops (P28 §subsec:g_minus_2)."
)

# 2b. Φ_MDL kink vacuum-polarization — scalar one-loop upper bound (unit Yukawa g=1)
# Δa_μ(φ) = (g²/8π²) ∫ dx x²(1-x)/((1-x)² + x² τ) with τ = M²/(4m_μ²)
tau_kink = M_kink_MeV**2 / (4 * m_mu_MeV**2)


def scalar_a_mu_integral(tau: float, n: int = 20000) -> float:
    """Neutral scalar φ with L = -g μ̄μφ; g=1 upper bound."""
    s = 0.0
    for i in range(1, n):
        x = i / n
        denom = (1 - x) ** 2 + x**2 * tau
        if denom > 0:
            s += x**2 * (1 - x) / denom
    return s / (8 * math.pi**2 * n)


kink_a_mu_unit_coupling = scalar_a_mu_integral(tau_kink)
kink_ratio_to_anomaly = kink_a_mu_unit_coupling / abs(delta_a_mu_obs)
kink_status = "NO_GTE_COUPLING"
kink_note = (
    f"Unit-coupling scalar upper bound Δa_μ ≈ {kink_a_mu_unit_coupling:.4e} "
    f"({kink_ratio_to_anomaly:.0f}× anomaly). GTE does not specify kink–photon–muon "
    "coupling; not a GTE prediction."
)

# 2c. HVP scaling from GTE pion mass (sensitivity estimate, not first-principles GTE VP)
delta_mpi_rel = m_pi_GTE_MeV / m_pi_PDG_MeV - 1.0
# Leading sensitivity: δa_HVP/a_HVP ≈ 2 δm_π/m_π (Jegerlehner scaling, approximate)
hvp_sensitivity_factor = 2.0
delta_hvp_from_mpi = hvp_sensitivity_factor * delta_mpi_rel * a_mu_hvp_lo
hvp_status = "SCALING_ESTIMATE_ONLY"
hvp_note = (
    f"m_π^GTE = {m_pi_GTE_MeV} MeV (+{100*delta_mpi_rel:.2f}% vs PDG); "
    f"approximate HVP shift ≈ {delta_hvp_from_mpi:.4e} (not a GTE loop integral)."
)

# 2d. PSC selection — no established modification of hadronic VP estimate
psc_correction = 0.0
psc_status = "NO_MECHANISM"
psc_note = "PSC axioms do not yet specify a hadronic VP functional in the GTE CA framework."

# ---------------------------------------------------------------------------
# Part 3: What GTE would need for Δa_μ
# ---------------------------------------------------------------------------
# Residual after GTE QED through 2L vs experiment
gte_qed12_vs_exp = a_mu_exp - a_mu_GTE_12L
# Remaining SM pieces not in GTE QED 2L
sm_missing_from_gte_qed12 = (
    (a_mu_QED_total - a_mu_QED_1L - a_mu_PDG_2L_QED)  # higher QED
    + a_mu_had_total
    + a_mu_ew
)

required_for_anomaly = delta_a_mu_obs
required_vs_gte_qed12_to_sm = a_mu_SM - a_mu_GTE_12L

# ---------------------------------------------------------------------------
# Part 4: Falsifiability verdict
# ---------------------------------------------------------------------------
# GTE has no complete two-loop+ prediction; neutral on anomaly
gte_predicts_2L = True  # standard QED 2L with α_GTE only
gte_predicts_hadronic = False
gte_predicts_anomaly = False

if not gte_predicts_hadronic and not closes_anomaly_2L:
    falsifiability_verdict = "NEUTRAL_NO_COMPLETE_2L_PLUS_PREDICTION"
    cat_level = "CatD"
else:
    falsifiability_verdict = "INCONCLUSIVE"
    cat_level = "CatAD"

# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
print("=" * 72)
print("EPIC_073 Rank 070-139 — (g−2)_μ two-loop GTE assessment")
print("=" * 72)
print()
print("1. TWO-LOOP QED (standard, α_GTE = 1/137)")
print(f"   C₂ (Kinoshita)     = {C2_QED}")
print(f"   a_μ^{{GTE,1L}}      = 1/(274π) = {a_mu_GTE_1L:.10e}")
print(f"   a_μ^{{GTE,2L,QED}}  = (α/π)² C₂ = {a_mu_GTE_2L_QED:.10e}")
print(f"   a_μ^{{GTE,1L+2L}}   = {a_mu_GTE_12L:.10e}")
print(f"   a_μ^{{SM}} (PDG)    = {a_mu_SM:.10e}")
print(f"   Δa_μ (exp−SM)       = {delta_a_mu_obs:.4e}")
print(f"   |a_μ^{{2L}}| / |Δa_μ| = {ratio_2L_to_anomaly:.0f}×")
print(f"   2L QED closes anomaly? {'YES' if closes_anomaly_2L else 'NO'}")
print(f"   GTE QED(1L+2L) − a_SM = {a_mu_GTE_12L - a_mu_SM:.4e}")
print(f"   Remaining to SM after GTE QED 2L = {gap_gte_qed12_to_sm:.4e}")
print()
print("2. GTE-SPECIFIC CORRECTIONS")
print(f"   Z₇ orbit VP:        {z7_orbit_correction:.4e}  [{z7_status}]")
print(f"   Kink loop (g=1 UB): {kink_a_mu_unit_coupling:.4e}  [{kink_status}]")
print(f"   HVP from m_π^GTE:   {delta_hvp_from_mpi:.4e}  [{hvp_status}]")
print(f"   PSC HVP modify:     {psc_correction:.4e}  [{psc_status}]")
print()
print("3. GTE HADRONIC INPUTS")
print(f"   m_π^GTE (GOR NLO)   = {m_pi_GTE_MeV} MeV  (PDG {m_pi_PDG_MeV} MeV, +{100*delta_mpi_rel:.2f}%)")
print(f"   M_kink^GTE          = {M_kink_MeV:.2f} MeV  ((8/49) m_τ)")
print(f"   π⁺ in GTE           = pseudo-NGB from chiral orbit (P39; Lean gte_pion_is_pseudo_ngb)")
print()
print("4. FERMILAB ANOMALY ASSESSMENT")
print(f"   GTE QED(1L+2L) vs exp residual = {gte_qed12_vs_exp:.4e}")
print(f"   SM pieces beyond GTE QED 2L    ≈ {sm_missing_from_gte_qed12:.4e}")
print(f"   To account for Δa_μ = {required_for_anomaly:.4e}, GTE would need a")
print(f"   hadronic/EW/new-physics prediction not yet derived (HVP integral, 3L+ QED,")
print(f"   or BSM loop with specified GTE couplings).")
print()
print(f"VERDICT: {falsifiability_verdict}")
print(f"CAT LEVEL: {cat_level}")
print()
print("INTERPRETATION:")
print("  Standard two-loop QED with α_GTE contributes ~4.1×10⁻⁶ — ~1660× the Fermilab")
print("  anomaly and does NOT close the gap. It partially fills the 1L→SM deficit but")
print("  leaves ~O(10⁻⁸) before hadronic/EW. GTE has no complete two-loop+ CA prediction;")
print("  neutral on Δa_μ (not falsified, not explanatory).")
print()

results = {
    "rank": "070-139",
    "script": "g_minus_2_two_loop_gte.py",
    "wall_clock_s": time.time() - t0,
    "gte_parameters": {
        "alpha_GTE": "1/137",
        "C2_QED": C2_QED,
        "m_pi_GTE_MeV": m_pi_GTE_MeV,
        "m_pi_PDG_MeV": m_pi_PDG_MeV,
        "M_kink_MeV": M_kink_MeV,
        "m_mu_MeV": m_mu_MeV,
    },
    "two_loop_qed": {
        "a_mu_GTE_1L": a_mu_GTE_1L,
        "a_mu_GTE_274pi": a_mu_GTE_274pi,
        "a_mu_GTE_2L_QED": a_mu_GTE_2L_QED,
        "a_mu_GTE_12L": a_mu_GTE_12L,
        "a_mu_PDG_2L_QED": a_mu_PDG_2L_QED,
        "ratio_2L_to_anomaly": ratio_2L_to_anomaly,
        "closes_fermilab_anomaly": closes_anomaly_2L,
        "gap_gte_qed12_to_SM": gap_gte_qed12_to_sm,
    },
    "gte_specific_channels": {
        "z7_orbit": {"delta_a_mu": z7_orbit_correction, "status": z7_status, "note": z7_note},
        "kink_vp": {
            "delta_a_mu_unit_coupling_ub": kink_a_mu_unit_coupling,
            "ratio_to_anomaly": kink_ratio_to_anomaly,
            "status": kink_status,
            "note": kink_note,
        },
        "hvp_mpi_scaling": {
            "delta_a_mu_estimate": delta_hvp_from_mpi,
            "delta_mpi_rel": delta_mpi_rel,
            "status": hvp_status,
            "note": hvp_note,
        },
        "psc": {"delta_a_mu": psc_correction, "status": psc_status, "note": psc_note},
    },
    "comparison": {
        "a_mu_SM": a_mu_SM,
        "a_mu_exp": a_mu_exp,
        "delta_a_mu_obs": delta_a_mu_obs,
        "a_mu_had_total": a_mu_had_total,
        "a_mu_hvp_lo": a_mu_hvp_lo,
        "a_mu_ew": a_mu_ew,
        "gte_qed12_vs_exp": gte_qed12_vs_exp,
        "sm_missing_from_gte_qed12": sm_missing_from_gte_qed12,
    },
    "falsifiability": {
        "gte_predicts_standard_2L_QED": gte_predicts_2L,
        "gte_predicts_hadronic_hvp": gte_predicts_hadronic,
        "explains_fermilab_anomaly": gte_predicts_anomaly,
        "verdict": falsifiability_verdict,
        "required_for_anomaly": required_for_anomaly,
    },
    "follow_on_required": [
        "Full GTE hadronic VP dispersion integral with GTE spectral function ρ(s)",
        "Two-loop vertex corrections in GTE CA / beable Hilbert space beyond QED",
        "Specified kink–photon–muon coupling from Φ_MDL for kink loop contribution",
        "Three-loop+ QED and EW loops with GTE α and W/Z thresholds from 158-EWS",
    ],
    "cat_level": cat_level,
    "status": "COMPLETE",
}

with open(OUTPUT_JSON, "w") as f:
    json.dump(results, f, indent=2)

print(f"Results written to {OUTPUT_JSON}")
signal.alarm(0)
