"""
G10: Strong coupling α_s(M_Z) estimate from GTE string tension with f_quant correction.

Computes σ_GTE = ΔK · m_kink² · f_quant and extracts α_s(M_Z) via 1-loop Nambu-Goto.

f_quant provisional value: 2^{-2/3} = (C_F · N_c)^{-1/3}  (CatA, EPIC_080-SU3-FQUANT)
  where C_F = 4/3 (SU(3) fundamental Casimir), N_c = 3.

Reference: EPIC_080, Rank G10, G13, SU3-FQUANT.
"""
import math
import json
import signal

TIMEOUT_SECONDS = 60

def _timeout_handler(signum, frame):
    print(f"\nTIMEOUT after {TIMEOUT_SECONDS}s")
    raise SystemExit(1)

signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

# --- GTE inputs ---
m_tau_GeV = 1776.86e-3          # tau lepton mass (SCC fixed parameter, P35/P42)
m_kink_GeV = (8 / 49) * m_tau_GeV   # BPS kink mass = 8m/49 (CatAL, G07)
delta_K = math.log2(9)           # ΔK = log₂(9), Z₇ kink entropy (CatAL, P39)

# f_quant: quantum string-tension suppression factor
# Provisional CatA: f_quant = 2^{-2/3} = (C_F · N_c)^{-1/3}
# C_F = 4/3 (SU(3) fundamental Casimir), N_c = 3 → C_F · N_c = 4
C_F = 4.0 / 3.0
N_c = 3.0
f_quant_provisional = (C_F * N_c) ** (-1.0 / 3.0)  # = 2^{-2/3} ≈ 0.6300

# --- String tension σ = ΔK · m_kink² · f_quant ---
sigma_GTE_fquant = delta_K * m_kink_GeV**2 * f_quant_provisional
sigma_GTE_fquant1 = delta_K * m_kink_GeV**2 * 1.0   # f_quant = 1 reference

# --- Λ_QCD from σ via Nambu-Goto SU(3): σ = (π/12) Λ_QCD² ---
sigma_prefactor = math.pi / 12.0
Lambda_QCD_fquant = math.sqrt(sigma_GTE_fquant / sigma_prefactor)
Lambda_QCD_fquant1 = math.sqrt(sigma_GTE_fquant1 / sigma_prefactor)

# --- α_s(M_Z) from 1-loop running: α_s(μ) = 2π / (b₀ log(μ/Λ_QCD)) ---
# b₀ = 7 from Z₇ β-function (CatAL, P39)
b0 = 7
M_Z = 91.188  # GeV

alpha_s_fquant = 2 * math.pi / (b0 * math.log(M_Z / Lambda_QCD_fquant))
alpha_s_fquant1 = 2 * math.pi / (b0 * math.log(M_Z / Lambda_QCD_fquant1))

alpha_s_PDG = 0.1185
pdg_lambda_low = 0.200   # GeV, PDG Λ_QCD range 200-330 MeV
pdg_lambda_high = 0.330

print("=" * 60)
print("G10: α_s(M_Z) from GTE string tension")
print("=" * 60)
print(f"\nInputs:")
print(f"  m_kink = (8/49) × m_τ = {m_kink_GeV*1000:.2f} MeV (CatAL)")
print(f"  ΔK = log₂(9) = {delta_K:.6f}")
print(f"  f_quant (provisional) = 2^(-2/3) = {f_quant_provisional:.6f}")
print(f"    = (C_F·N_c)^(-1/3) = ({C_F:.4f}·{N_c})^(-1/3)")

print(f"\n--- f_quant = 2^(-2/3) [CatA provisional] ---")
print(f"  σ_GTE = {sigma_GTE_fquant:.6f} GeV²")
print(f"  Λ_QCD = {Lambda_QCD_fquant*1000:.1f} MeV  (PDG: 200-330 MeV)")
print(f"  α_s(M_Z) = {alpha_s_fquant:.4f}  (PDG: {alpha_s_PDG})")
err_fquant = (alpha_s_fquant - alpha_s_PDG) / alpha_s_PDG * 100
print(f"  Error: {err_fquant:+.1f}%")

print(f"\n--- f_quant = 1 [no correction, reference] ---")
print(f"  σ_GTE = {sigma_GTE_fquant1:.6f} GeV²")
print(f"  Λ_QCD = {Lambda_QCD_fquant1*1000:.1f} MeV  (PDG: 200-330 MeV)")
print(f"  α_s(M_Z) = {alpha_s_fquant1:.4f}  (PDG: {alpha_s_PDG})")
err_fquant1 = (alpha_s_fquant1 - alpha_s_PDG) / alpha_s_PDG * 100
print(f"  Error: {err_fquant1:+.1f}%")

print(f"\n--- Improvement from f_quant correction ---")
print(f"  Δα_s = {alpha_s_fquant1 - alpha_s_fquant:.4f} (reduction from f_quant=1)")
print(f"  Error reduction: {abs(err_fquant1) - abs(err_fquant):.1f} pp")
print(f"  Conclusion: f_quant=2^(-2/3) moves α_s closer to PDG by ~8 pp")
print(f"  but Nambu-Goto σ→Λ_QCD formula overcounts Λ_QCD by ~3x.")
print(f"  Root cause: full 3+1D string tension (G13) needed for precise Λ_QCD.")

results = {
    "f_quant_provisional": f_quant_provisional,
    "f_quant_formula": "2^(-2/3) = (C_F*N_c)^(-1/3)",
    "C_F": C_F,
    "N_c": N_c,
    "m_kink_GeV": m_kink_GeV,
    "delta_K": delta_K,
    "sigma_prefactor": sigma_prefactor,
    "f_quant_2m2o3": {
        "sigma_GTE_GeV2": sigma_GTE_fquant,
        "Lambda_QCD_MeV": Lambda_QCD_fquant * 1000,
        "alpha_s_MZ": alpha_s_fquant,
        "alpha_s_PDG": alpha_s_PDG,
        "error_pct": err_fquant,
    },
    "f_quant_1": {
        "sigma_GTE_GeV2": sigma_GTE_fquant1,
        "Lambda_QCD_MeV": Lambda_QCD_fquant1 * 1000,
        "alpha_s_MZ": alpha_s_fquant1,
        "error_pct": err_fquant1,
    },
    "b0": b0,
    "M_Z_GeV": M_Z,
    "note": (
        "Nambu-Goto pi/12 formula overestimates Lambda_QCD; "
        "board estimate (549 MeV, 48% error) uses a calibrated rough 1-loop formula. "
        "Precise Λ_QCD requires G13 (full 3+1D string tension)."
    ),
}

with open("papers/35_gte_unification/scripts/g10_strong_coupling_fquant_results.json", "w") as f:
    json.dump(results, f, indent=2)
print("\nResults written to g10_strong_coupling_fquant_results.json")

signal.alarm(0)
