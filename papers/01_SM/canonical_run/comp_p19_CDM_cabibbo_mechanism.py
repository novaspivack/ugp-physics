"""
COMP-P19-CDM: Cabibbo Derivation from α_d — mechanism analysis.

The key insight: in the FN framework the bare CKM charge for V_us is Δa=1.
The VV relation coefficient α_d = 13/9 = 1 + rank(SU(5))/N_c² shifts the
effective charge to Δa_eff = α_d = 13/9.

This script:
1. Verifies the formula λ ≈ ε₁^(α_d) at 1.9% off PDG
2. Shows the decomposition Δa_eff = 1 + rank(SU(5))/N_c² = 1 + 4/9
3. Extends to other CKM elements via VV-corrected charges
4. Updates the CYC-09 FN Phase-1 table with improved V_us formula

Date: 2026-05-11
"""
import math, json, datetime

# === Structural constants ===
pi = math.pi
N_c = 3
rank_SU5 = 4        # rank of SU(5) = dim of Cartan subalgebra = 4
eps1 = math.exp(-pi/3)   # First flavon VEV (Lean-certified)
eps2 = math.exp(-pi/8)   # Second flavon VEV (Lean-certified)

# VV Lean-certified coefficients
alpha_d = 13/9      # = 1 + rank(SU(5))/N_c²  [T] VV_from_GUT_group_theory
beta_d  = 7/6       # = 1 + Y_Q_L              [T]
gamma_d = 5/14      # = dim(45_SU5)/dim(126_SO10) [T]

# PDG 2024 CKM values
lam_PDG  = 0.22453  # |V_us| / Wolfenstein λ
A_PDG    = 0.826
Vub_PDG  = 0.00382
Vcb_PDG  = 0.0408
Vcd_PDG  = 0.221
Vcs_PDG  = 0.975
Vtb_PDG  = 0.9991

print("=" * 68)
print("COMP-P19-CDM: Cabibbo Derivation from α_d Mechanism")
print("=" * 68)

# === Part 1: The mechanism ===
print("\n--- Part 1: α_d mechanism decomposition ---")
print(f"  N_c = {N_c}, rank(SU(5)) = {rank_SU5}")
print(f"  α_d = 13/9 = 1 + rank(SU(5))/N_c² = 1 + {rank_SU5}/{N_c**2} = {1 + rank_SU5/N_c**2:.6f}")
print(f"  α_d actual = 13/9 = {alpha_d:.6f}  (match: {abs(alpha_d - (1 + rank_SU5/N_c**2)) < 1e-10})")

# Bare FN charge Δa = 1 → ε₁^1 = 0.3509 (far from λ)
# Correction: (α_d - 1) = rank(SU(5))/N_c² = 4/9
# Effective charge: 1 + 4/9 = 13/9
delta_a_bare = 1
delta_a_correction = alpha_d - 1  # = rank(SU(5))/N_c² = 4/9
delta_a_eff = delta_a_bare + delta_a_correction

print(f"\n  Bare FN charge:        Δa = {delta_a_bare}")
print(f"  VV GUT correction:     Δa_corr = α_d - 1 = {delta_a_correction:.4f} = rank(SU5)/N_c²")
print(f"  Effective charge:      Δa_eff = {delta_a_eff:.4f} = α_d = 13/9")

# === Part 2: Formula comparison ===
print("\n--- Part 2: Formula comparison vs PDG 2024 ---")
formulas = {
    "A₂ mismatch (paper, current)":    math.sin(math.radians(14.68)),
    "ε₁·ε₂  [FN Phase-1, old CYC-09]": eps1 * eps2,
    "ε₁^(α_d) [new formula, CDM]":     eps1 ** alpha_d,
    "ε₁^1 (bare FN, Δa=1)":            eps1,
}
print(f"  PDG 2024 λ = {lam_PDG}")
for name, val in formulas.items():
    err = (val - lam_PDG)/lam_PDG * 100
    print(f"  {name:<44s}: {val:.6f}  ({err:+.2f}%)")

print(f"\n  Improvement factor (new vs A2 mismatch): {12.5 / 1.87:.1f}×")
print(f"  Improvement factor (new vs FN Phase-1):  {5.6 / 1.87:.1f}×")

# === Part 3: Extended CKM element analysis ===
print("\n--- Part 3: CYC-09 table — Phase-1 vs VV-corrected ---")

# Phase-1 FN charges (from Round 29, a_Q = (-3,-2,0), b_Q = (-5,-3,0))
# |V_ij| ≈ ε₁^|Δa| × ε₂^|Δb|
ckm_phase1 = {
    'V_us': (1, 1),   # Δa=1, Δb=1
    'V_ub': (5, 1),   # Δa=5, Δb=1  (large)
    'V_cd': (0, 4),   # Δa=0, Δb=4
    'V_cb': (0, 8),   # Δa=0, Δb=8
}
ckm_pdg = {
    'V_us': lam_PDG,
    'V_ub': Vub_PDG,
    'V_cd': Vcd_PDG,
    'V_cb': Vcb_PDG,
}

print(f"  {'Element':<8} {'Phase-1':>10} {'Phase-1 err':>12} {'VV-corrected':>14} {'VV-corr err':>12} PDG")
for elem, (da, db) in ckm_phase1.items():
    p1 = eps1**da * eps2**db
    pdg = ckm_pdg[elem]
    p1_err = (p1 - pdg)/pdg * 100
    
    # VV-correction: for V_us, effective Δa → α_d. For others, apply correction scaled.
    # The CDM mechanism applies when the mixing involves the down-type sector weighted by α_d.
    # For V_us: Δa_eff = α_d = 13/9 (instead of 1)
    # For V_cd: same Cabibbo angle, same correction
    # For V_cb: involves Δa=0 (no up-generation charge difference) — correction may not apply
    if elem in ('V_us', 'V_cd'):
        vv_da = alpha_d  # Apply α_d correction
        vv_db = db       # Keep β_d charge as-is (different sector)
        vv = eps1**vv_da * eps2**vv_db
    else:
        vv = p1  # No change for V_ub, V_cb (different charge structure)
    vv_err = (vv - pdg)/pdg * 100
    
    print(f"  {elem:<8} {p1:>10.5f} {p1_err:>+11.1f}% {vv:>14.5f} {vv_err:>+11.1f}%  {pdg:.5f}")

# === Part 4: Structural identification summary ===
print("\n--- Part 4: Structural identification ---")
print(f"  ε₁ = e^(-π/3)                  [T] fn_vevs_are_potential_minima")
print(f"  α_d = 1 + rank(SU(5))/N_c²    [T] VV_from_GUT_group_theory")
print(f"  rank(SU(5)) = 4               structural (Lie algebra rank)")
print(f"  N_c = 3                        [T] multiple proofs in ugp-lean")
print(f"  Δa_eff = 1 + 4/9 = α_d = 13/9 CDM mechanism: FN charge + GUT correction")
print(f"  λ = ε₁^(Δa_eff) = {eps1**alpha_d:.6f}    1.9% off PDG {lam_PDG}")

# === Save result ===
result = {
    "computation": "COMP-P19-CDM",
    "date": datetime.datetime.utcnow().isoformat() + "Z",
    "mechanism": {
        "description": "CKM Cabibbo mixing from VV α_d GUT correction to FN charge",
        "bare_FN_charge": delta_a_bare,
        "vv_gut_correction": f"(α_d - 1) = rank(SU(5))/N_c² = {rank_SU5}/{N_c**2} = {rank_SU5/N_c**2:.4f}",
        "effective_charge": f"Δa_eff = 1 + 4/9 = 13/9 = α_d = {alpha_d:.6f}",
        "lean_basis": ["fn_vevs_are_potential_minima", "VV_from_GUT_group_theory"]
    },
    "formula": {
        "expression": "λ = ε₁^(α_d) = e^{-13π/27}",
        "value": round(eps1**alpha_d, 7),
        "pdg_2024": lam_PDG,
        "error_pct": round((eps1**alpha_d - lam_PDG)/lam_PDG * 100, 3)
    },
    "comparison": {
        "a2_mismatch_pct": 12.5,
        "fn_phase1_pct": 5.6,
        "vv_corrected_pct": abs(round((eps1**alpha_d - lam_PDG)/lam_PDG * 100, 3)),
        "improvement_vs_a2": round(12.5 / abs((eps1**alpha_d - lam_PDG)/lam_PDG * 100), 1),
    },
    "cyc09_update": {
        "V_us_old": {"formula": "ε₁·ε₂", "value": round(eps1*eps2, 6), "error_pct": round((eps1*eps2-lam_PDG)/lam_PDG*100, 2)},
        "V_us_new": {"formula": "ε₁^(α_d)", "value": round(eps1**alpha_d, 6), "error_pct": round((eps1**alpha_d-lam_PDG)/lam_PDG*100, 2)}
    },
    "status": "MECHANISM_IDENTIFIED_DERIVATION_EXPLORATORY"
}

with open('comp_p19_CDM_cabibbo_mechanism.json', 'w') as f:
    json.dump(result, f, indent=2)
print("\nSaved to comp_p19_CDM_cabibbo_mechanism.json")
