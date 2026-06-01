"""
Gauge coupling constants g, g', g_s from GTE/Phi_MDL inputs.

GTE inputs used (all CatAL or CatAD):
  - sin^2(theta_W) = 3/13          (CatAL, orbit arithmetic, P31)
  - alpha_EM(q=0)  = 1/137.036     (CatAL, N_eff arithmetic, P43)
  - v_H            = 246.16 GeV    (CatAD, SRRG, P45)
  - b0             = 7             (CatAL, Z7 structure, P39)
  - Delta_K        = log2(9)       (CatAL, MDL confinement, P39/P46)
  - M_kink         = (8/49)*m_tau  (CatA,  Phi_MDL kink integral, P39)

Outputs:
  - g, g', m_W, m_Z  (CatAD: exact algebraic relations from CatAL inputs)
  - g_s, Lambda_QCD  (CatA:  estimate, requires Phi_MDL string tension)

Result file: coupling_constants_gte_results.json
"""

import math
import json
import signal
import sys

# ── wall-clock safety ────────────────────────────────────────────────────────
TIMEOUT_SECONDS = 120

def _timeout_handler(signum, frame):
    print(f"\nTIMEOUT: wall-clock limit {TIMEOUT_SECONDS}s reached.")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

# ── GTE inputs ───────────────────────────────────────────────────────────────

# Electromagnetic fine structure constant at q=0 (CatAL, P43)
ALPHA_EM_Q0 = 1.0 / 137.036

# Running EM coupling at M_Z (standard QED running, used for scale-matched results)
ALPHA_EM_MZ = 1.0 / 128.9

# Weinberg angle: sin^2(theta_W) = 3/13  (CatAL, orbit arithmetic, P31)
SIN2_THETA_W = 3.0 / 13.0
COS2_THETA_W = 1.0 - SIN2_THETA_W  # = 10/13

# Higgs VEV (CatAD, SRRG, P45)
V_H = 246.16  # GeV

# QCD Z7 beta-function coefficient (CatAL, Z7 structure, P39)
B0_GTE = 7

# Confinement MDL cost (CatAL, ColorConfinementMDL.lean, P39/P46)
DELTA_K = math.log2(9)  # = log2(N_c^2) = 2*log2(3)  bits

# Phi_MDL kink mass: M_kink = (8/49)*m_tau  (CatA, Phi_MDL kink integral, P39)
M_TAU_GEV = 1.776_86  # GeV  (PDG input — tau mass)
M_KINK_GTE = (8.0 / 49.0) * M_TAU_GEV

# CatA quantization factor from P39 Monte Carlo
F_QUANT = 0.629

# PDG reference values (for comparison only — NOT used in derivation)
PDG = {
    "g":        0.6527,
    "g_prime":  0.3497,
    "g_s":      1.2205,  # = sqrt(4*pi*alpha_s) at M_Z, alpha_s = 0.1185
    "alpha_s":  0.1185,
    "m_W":      80.377,
    "m_Z":      91.188,
    "m_Z_ref":  91.188,  # reference scale
    "Lambda_QCD_MeV": 210.0,  # PDG MSbar 5-flavor (central)
}

# ── T1: EW coupling constants ────────────────────────────────────────────────

def ew_couplings(alpha_em, sin2_tw, cos2_tw):
    """Compute g, g' from alpha_EM and sin^2(theta_W).
    
    Tree-level relations:
        alpha_EM = g^2 * sin^2(theta_W) / (4*pi)
        alpha_EM = g'^2 * cos^2(theta_W) / (4*pi)
    """
    g_sq  = 4.0 * math.pi * alpha_em / sin2_tw
    gp_sq = 4.0 * math.pi * alpha_em / cos2_tw
    return math.sqrt(g_sq), math.sqrt(gp_sq), g_sq, gp_sq


def boson_masses(g_sq, gp_sq, v_H):
    m_W = math.sqrt(g_sq)  * v_H / 2.0
    m_Z = math.sqrt(g_sq + gp_sq) * v_H / 2.0
    return m_W, m_Z


# --- at q=0 (α_EM from GTE, no RG running) ---
g_q0, gp_q0, g_sq_q0, gp_sq_q0 = ew_couplings(ALPHA_EM_Q0, SIN2_THETA_W, COS2_THETA_W)
m_W_q0, m_Z_q0 = boson_masses(g_sq_q0, gp_sq_q0, V_H)

# --- at M_Z (α_EM(M_Z) from standard QED running — not a new GTE input) ---
g_MZ, gp_MZ, g_sq_MZ, gp_sq_MZ = ew_couplings(ALPHA_EM_MZ, SIN2_THETA_W, COS2_THETA_W)
m_W_MZ, m_Z_MZ = boson_masses(g_sq_MZ, gp_sq_MZ, V_H)

# ── T2: Strong coupling from GTE ─────────────────────────────────────────────

# String tension from Phi_MDL kink structure (CatA, P39)
a_cell = 1.0 / M_KINK_GTE  # GeV^-1
sigma_GTE = DELTA_K * F_QUANT / a_cell**2  # GeV^2

# Estimate Lambda_QCD from string tension
# Using the relation σ ≈ (b0/4π) * Λ_QCD^2 (rough 1-loop lattice estimate)
Lambda_QCD_GTE = math.sqrt(sigma_GTE * 4.0 * math.pi / B0_GTE)

# 1-loop alpha_s at M_Z given b0=7 and GTE Lambda_QCD
alpha_s_GTE = 2.0 * math.pi / (B0_GTE * math.log(PDG["m_Z_ref"] / Lambda_QCD_GTE))
g_s_GTE = math.sqrt(4.0 * math.pi * alpha_s_GTE)

# For comparison: what Λ_QCD is implied by b0=7 and PDG alpha_s?
ln_ratio_pdg = 2.0 * math.pi / (B0_GTE * PDG["alpha_s"])
Lambda_QCD_implied = PDG["m_Z_ref"] / math.exp(ln_ratio_pdg)

# ── results ───────────────────────────────────────────────────────────────────

results = {
    "inputs": {
        "alpha_EM_q0":       ALPHA_EM_Q0,
        "alpha_EM_MZ":       ALPHA_EM_MZ,
        "sin2_theta_W":      SIN2_THETA_W,
        "sin2_theta_W_exact": "3/13",
        "cos2_theta_W":      COS2_THETA_W,
        "cos2_theta_W_exact": "10/13",
        "v_H_GeV":           V_H,
        "b0_GTE":            B0_GTE,
        "delta_K_confinement_bits": DELTA_K,
        "M_kink_GeV":        M_KINK_GTE,
        "f_quant_CatA":      F_QUANT,
    },
    "ew_couplings_q0": {
        "description": "Tree-level EW couplings using alpha_EM at q=0 (GTE CatAL)",
        "g_squared":  g_sq_q0,
        "g":          g_q0,
        "g_exact_symbolic": "sqrt(4*pi*alpha_EM * 13/3)",
        "g_prime_squared": gp_sq_q0,
        "g_prime":    gp_q0,
        "g_prime_exact_symbolic": "sqrt(4*pi*alpha_EM * 13/10)",
        "g_over_g_prime": g_q0 / gp_q0,
        "g_over_g_prime_exact": "sqrt(10/3)",
        "m_W_GeV":    m_W_q0,
        "m_Z_GeV":    m_Z_q0,
        "PDG_g":      PDG["g"],
        "PDG_g_prime": PDG["g_prime"],
        "PDG_m_W":    PDG["m_W"],
        "PDG_m_Z":    PDG["m_Z"],
        "error_g_pct":   abs(g_q0  - PDG["g"])       / PDG["g"]       * 100,
        "error_gp_pct":  abs(gp_q0 - PDG["g_prime"]) / PDG["g_prime"] * 100,
        "error_mW_pct":  abs(m_W_q0 - PDG["m_W"])    / PDG["m_W"]     * 100,
        "error_mZ_pct":  abs(m_Z_q0 - PDG["m_Z"])    / PDG["m_Z"]     * 100,
    },
    "ew_couplings_MZ_scale": {
        "description": "Tree-level EW couplings using alpha_EM(M_Z) — scale-matched comparison",
        "g":          g_MZ,
        "g_prime":    gp_MZ,
        "m_W_GeV":    m_W_MZ,
        "m_Z_GeV":    m_Z_MZ,
        "error_g_pct":  abs(g_MZ  - PDG["g"])       / PDG["g"]       * 100,
        "error_gp_pct": abs(gp_MZ - PDG["g_prime"]) / PDG["g_prime"] * 100,
        "error_mW_pct": abs(m_W_MZ - PDG["m_W"])    / PDG["m_W"]     * 100,
        "error_mZ_pct": abs(m_Z_MZ - PDG["m_Z"])    / PDG["m_Z"]     * 100,
    },
    "strong_coupling": {
        "description": "Strong coupling estimate from GTE b0=7 and Phi_MDL string tension (CatA)",
        "b0_GTE":        B0_GTE,
        "delta_K_bits":  DELTA_K,
        "sigma_GTE_GeV2": sigma_GTE,
        "sigma_PDG_GeV2": 0.18,
        "sigma_ratio":   sigma_GTE / 0.18,
        "Lambda_QCD_GTE_GeV": Lambda_QCD_GTE,
        "Lambda_QCD_GTE_MeV": Lambda_QCD_GTE * 1000,
        "Lambda_QCD_PDG_MeV": PDG["Lambda_QCD_MeV"],
        "alpha_s_GTE_MZ": alpha_s_GTE,
        "g_s_GTE":       g_s_GTE,
        "PDG_alpha_s_MZ": PDG["alpha_s"],
        "PDG_g_s":       PDG["g_s"],
        "error_alpha_s_pct": abs(alpha_s_GTE - PDG["alpha_s"]) / PDG["alpha_s"] * 100,
        "Lambda_QCD_implied_by_b0_7_and_PDG_alpha_s_MeV": Lambda_QCD_implied * 1000,
        "status": "CatA — string tension requires Phi_MDL kink calibration; open gap",
    },
    "status_summary": {
        "g":       {"value": g_q0, "CatLevel": "CatAD",
                    "note": "Algebraically exact from sin2_theta_W=3/13 (CatAL) and alpha_EM (CatAL); q=0 value, ~3.4% below PDG at M_Z due to RG running"},
        "g_prime": {"value": gp_q0, "CatLevel": "CatAD",
                    "note": "Same; ~1.3% below PDG at M_Z due to RG running"},
        "m_W":     {"value": m_W_q0, "CatLevel": "CatAD",
                    "note": "Tree-level from GTE g and v_H=246.16 GeV (CatAD); ~3.5% below PDG"},
        "m_Z":     {"value": m_Z_q0, "CatLevel": "CatAD",
                    "note": "Tree-level from GTE g, g', v_H; ~3.0% below PDG"},
        "g_s":     {"value": g_s_GTE, "CatLevel": "CatA",
                    "note": "Estimate from b0=7 (CatAL) and string tension (CatA); 33% error — Phi_MDL kink calibration needed"},
        "Lambda_QCD": {"value_MeV": Lambda_QCD_GTE * 1000, "CatLevel": "CatA",
                       "note": "Inferred from Phi_MDL string tension estimate; open gap"},
    },
    "open_gaps": [
        "Λ_QCD: requires precise Phi_MDL 3+1D string tension from kink condensate (G13)",
        "alpha_s(M_Z): b0=7 is CatAL but normalization convention (GTE vs MSbar) needs matching",
        "RG running of sin2_theta_W from Z7 orbit scale to M_Z: small correction, currently external input",
        "Radiative corrections delta_r to m_W, m_Z: ~1% EW loop effects not yet in Phi_MDL",
    ],
}

# ── print summary ─────────────────────────────────────────────────────────────
print("=" * 65)
print("GTE Gauge Coupling Constants — Summary")
print("=" * 65)
print(f"EW COUPLINGS (using α_EM at q=0, CatAL inputs):")
print(f"  g² = 4π·α_EM·(13/3)  = {g_sq_q0:.6f}  →  g  = {g_q0:.6f}")
print(f"  g'²= 4π·α_EM·(13/10) = {gp_sq_q0:.6f}  →  g' = {gp_q0:.6f}")
print(f"  g/g' = sqrt(10/3)    = {g_q0/gp_q0:.6f}")
print(f"  m_W = {m_W_q0:.4f} GeV   m_Z = {m_Z_q0:.4f} GeV")
print(f"  PDG: g={PDG['g']}, g'={PDG['g_prime']}, m_W={PDG['m_W']}, m_Z={PDG['m_Z']}")
print(f"  Errors (q=0→M_Z RG not applied): g={results['ew_couplings_q0']['error_g_pct']:.2f}%,")
print(f"    g'={results['ew_couplings_q0']['error_gp_pct']:.2f}%,")
print(f"    m_W={results['ew_couplings_q0']['error_mW_pct']:.2f}%,")
print(f"    m_Z={results['ew_couplings_q0']['error_mZ_pct']:.2f}%")
print()
print(f"EW COUPLINGS at M_Z scale (α_EM(M_Z) RG-matched):")
print(f"  g = {g_MZ:.6f} ({results['ew_couplings_MZ_scale']['error_g_pct']:.2f}% vs PDG),",
      f"  g' = {gp_MZ:.6f} ({results['ew_couplings_MZ_scale']['error_gp_pct']:.2f}% vs PDG)")
print(f"  m_W = {m_W_MZ:.4f} GeV ({results['ew_couplings_MZ_scale']['error_mW_pct']:.2f}%),",
      f"  m_Z = {m_Z_MZ:.4f} GeV ({results['ew_couplings_MZ_scale']['error_mZ_pct']:.2f}%)")
print()
print(f"STRONG COUPLING (CatA estimate):")
print(f"  σ_GTE = {sigma_GTE:.4f} GeV²  (PDG ~0.18 GeV², ratio {sigma_GTE/0.18:.3f})")
print(f"  Λ_QCD(GTE) ≈ {Lambda_QCD_GTE*1000:.1f} MeV  (PDG ~210-330 MeV)")
print(f"  α_s(M_Z)|GTE ≈ {alpha_s_GTE:.4f}  (PDG 0.1185, error {results['strong_coupling']['error_alpha_s_pct']:.1f}%)")
print(f"  g_s(M_Z)|GTE ≈ {g_s_GTE:.4f}  (PDG 1.2203)")
print(f"  Status: CatA — b0=7 CatAL but Λ_QCD derivation incomplete (open gap G13)")

# ── write JSON ────────────────────────────────────────────────────────────────
out_path = "coupling_constants_gte_results.json"
import os
script_dir = os.path.dirname(os.path.abspath(__file__))
out_path = os.path.join(script_dir, "coupling_constants_gte_results.json")
with open(out_path, "w") as f:
    json.dump(results, f, indent=2)
print(f"\nResults written to: {out_path}")

signal.alarm(0)
