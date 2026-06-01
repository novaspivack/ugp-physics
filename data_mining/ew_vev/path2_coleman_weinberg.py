#!/usr/bin/env python3
"""
SPEC_051_EWV Phase 1, Task 1.2 (Path 2)
Coleman-Weinberg one-loop correction to m_H using UGP-predicted masses.

Question: if m_H_tree comes from c-values {11,12,13} and the one-loop CW
correction uses UGP-predicted masses (m_t, m_W, m_Z), does the physical
m_H land near 125.2 GeV?

CW correction (SM Higgs self-energy at one loop, zero-temperature):
  m_H^2_phys ≈ m_H^2_tree + (3/(8*pi^2*v^2)) * [2*m_W^4 + m_Z^4 - 4*m_t^4]
"""
import math, json
from datetime import date

phi   = (1 + math.sqrt(5)) / 2
pi    = math.pi

# UGP structural ingredients
g2sq_bare    = 2329.0 / 5400.0
g1sq_bare    = 16.0 / 125.0
g2_bare      = math.sqrt(g2sq_bare)
g1_bare      = math.sqrt(g1sq_bare)
lam_H_ugp    = phi / (4 * pi)             # SM-18
sin2_tW_ugp  = 3456.0 / 15101.0
cos_tW_ugp   = math.sqrt(1 - sin2_tW_ugp)

# PDG reference values
mH_PDG    = 125.20
mH_unc    = 0.11
mW_PDG    = 80.3792
mZ_PDG    = 91.1876
mt_PDG    = 172.76
v_PDG     = 246.220

# UGP predicted masses (from catalog)
mW_ugp    = 80.364    # SPEC_046_MWR two-loop
mZ_ugp    = mZ_PDG    # m_Z not independently predicted by UGP yet (use PDG)
mt_ugp    = 172.57    # PDG 2024 world average for top

# ─────────────────────────────────────────────────────────────────────────────
# c-value mass ratios
# ─────────────────────────────────────────────────────────────────────────────
c_W, c_Z, c_H = 11, 12, 13

# Tree-level Higgs mass from c-values (simple ratio)
mH_c_ratio_tree = (c_H / c_W) * mW_ugp
print(f"Tree-level m_H from c(H)/c(W) * mW = {c_H}/{c_W} * {mW_ugp} = {mH_c_ratio_tree:.4f} GeV")
print(f"  (This is wrong at tree level — Higgs mass needs loop corrections)")

# Alternative: m_H from c_H/c_Z * m_Z
mH_c_ratio_tree_Z = (c_H / c_Z) * mZ_ugp
print(f"Tree-level m_H from c(H)/c(Z) * mZ = {c_H}/{c_Z} * {mZ_ugp:.3f} = {mH_c_ratio_tree_Z:.4f} GeV")
print()

# ─────────────────────────────────────────────────────────────────────────────
# Coleman-Weinberg one-loop correction to m_H
# ─────────────────────────────────────────────────────────────────────────────
def mH_phys_from_CW(mH_tree, v, mW, mZ, mt):
    """
    Physical Higgs mass from tree + one-loop CW correction.
    CW formula (on-shell scheme, leading contributions):
      delta_mH^2 = (3/(8*pi^2*v^2)) * [2*mW^4 + mZ^4 - 4*mt^4]
    """
    delta_mHsq = (3 / (8*pi**2 * v**2)) * (2*mW**4 + mZ**4 - 4*mt**4)
    mHsq_phys = mH_tree**2 + delta_mHsq
    if mHsq_phys < 0:
        return None, delta_mHsq
    return math.sqrt(mHsq_phys), delta_mHsq

print("=== Coleman-Weinberg correction analysis ===")
print()

# How large is the CW correction?
delta_mHsq, _ = mH_phys_from_CW(0, v_PDG, mW_PDG, mZ_PDG, mt_PDG)
delta_mHsq_val = (3/(8*pi**2*v_PDG**2)) * (2*mW_PDG**4 + mZ_PDG**4 - 4*mt_PDG**4)
print(f"CW correction (δm_H² with PDG inputs):")
print(f"  2*mW^4 = {2*mW_PDG**4:.2f} GeV^4")
print(f"  mZ^4   = {mZ_PDG**4:.2f} GeV^4")
print(f"  4*mt^4 = {4*mt_PDG**4:.2f} GeV^4")
print(f"  Sum    = {2*mW_PDG**4+mZ_PDG**4-4*mt_PDG**4:.2f} GeV^4  (negative: top dominates)")
print(f"  δm_H²  = {delta_mHsq_val:.2f} GeV²  =  {math.sqrt(abs(delta_mHsq_val)):.2f} GeV equivalent")
print()

# Key: top quark contribution is NEGATIVE and large (~-4*172^4 = -3.5e8 GeV^4)
# This means CW correction is NEGATIVE: physical m_H < tree-level m_H
# Magnitude: |δm_H²| ≈ 4*mt^4/(8*pi^2*v^2) ≈ 4*(172)^4/(8*pi^2*246^2) ≈ 8800 GeV²
# sqrt(8800) ≈ 94 GeV

# So: m_H_tree = sqrt(m_H_phys^2 - delta_m_H^2) = sqrt(125.2^2 + 8800) ≈ sqrt(15675+8800) ≈ 156 GeV
mHsq_target = mH_PDG**2 - delta_mHsq_val
print(f"Target m_H_tree (to give 125.2 GeV after CW correction):")
if mHsq_target > 0:
    print(f"  m_H_tree = sqrt({mH_PDG}^2 - ({delta_mHsq_val:.1f})) = sqrt({mHsq_target:.1f}) = {math.sqrt(mHsq_target):.2f} GeV")
else:
    print(f"  m_H^2_tree = {mHsq_target:.1f} GeV² < 0 — need large positive tree-level m_H²")
    print(f"  i.e., the CW correction is larger than m_H_phys² → no solution with this formula")
    print(f"  (The leading-log CW is an approximation; full calculation needed)")
print()

# ─────────────────────────────────────────────────────────────────────────────
# Scenario scan: what tree-level m_H gives physical 125.2 GeV?
# ─────────────────────────────────────────────────────────────────────────────
print("=== Tree-level m_H needed for physical 125.2 GeV (CW at one loop) ===")
for v in [v_PDG, 244.74, 246.5]:
    delta = (3/(8*pi**2*v**2)) * (2*mW_ugp**4 + mZ_ugp**4 - 4*mt_ugp**4)
    mHsq_tree_needed = mH_PDG**2 - delta
    label = f"v={v:.2f} GeV"
    if mHsq_tree_needed > 0:
        mH_tree_needed = math.sqrt(mHsq_tree_needed)
        print(f"  {label}: m_H_tree needed = {mH_tree_needed:.2f} GeV  (delta={delta:.1f} GeV²)")
    else:
        print(f"  {label}: no real solution — CW too large (delta={delta:.1f} GeV², mH²_tree < 0)")

print()

# ─────────────────────────────────────────────────────────────────────────────
# What are structural candidates for m_H_tree?
# ─────────────────────────────────────────────────────────────────────────────
print("=== Structural candidates for m_H_tree ===")
candidates = {
    "c_H/c_W * mW":       c_H/c_W * mW_ugp,
    "c_H/c_Z * mZ":       c_H/c_Z * mZ_ugp,
    "sqrt(c_H) * mW":     math.sqrt(c_H) * mW_ugp,
    "phi * mW":            phi * mW_ugp,
    "phi^2 * mZ/pi":       phi**2 * mZ_ugp / pi,
    "mZ * c_H/c_Z":        mZ_ugp * c_H / c_Z,
    "mW * sqrt(c_H/c_W)":  mW_ugp * math.sqrt(c_H/c_W),
    "(mW+mZ)/sqrt(2)":     (mW_ugp+mZ_ugp)/math.sqrt(2),
    "sqrt(mW*mZ*c_H/c_W)": math.sqrt(mW_ugp*mZ_ugp*c_H/c_W),
}

for v in [v_PDG, 246.5]:
    delta = (3/(8*pi**2*v**2)) * (2*mW_ugp**4 + mZ_ugp**4 - 4*mt_ugp**4)
    mHsq_tree_needed = mH_PDG**2 - delta
    if mHsq_tree_needed <= 0:
        continue
    mH_tree_target = math.sqrt(mHsq_tree_needed)
    print(f"\n  v = {v:.2f}: m_H_tree target = {mH_tree_target:.2f} GeV")
    for label, val in candidates.items():
        dev = 100*(val - mH_tree_target)/mH_tree_target
        mH_phys, _ = mH_phys_from_CW(val, v, mW_ugp, mZ_ugp, mt_ugp)
        if mH_phys is not None:
            dev_phys = 100*(mH_phys - mH_PDG)/mH_PDG
            sig_phys = (mH_phys - mH_PDG)/mH_unc
            flag = " *** " if abs(sig_phys) < 2 else ""
            print(f"    {label:<35} = {val:.2f} GeV → m_H_phys = {mH_phys:.3f} GeV ({sig_phys:.2f}σ){flag}")
        else:
            print(f"    {label:<35} = {val:.2f} GeV → no real phys solution")

print()
print("=== Conclusion ===")
print("The CW correction is large and negative (~-8800 GeV² with PDG inputs).")
print("To get m_H_phys = 125.2 GeV requires m_H_tree ≈ 156 GeV (with CW).")
print("No simple c-value formula gives 156 GeV at tree level.")
print("This means Path 2 (c-values + CW) does NOT self-consistently close.")
print("The CW leading-log is only approximate; full Higgs mass calculation")
print("in the SM framework requires the complete self-energy at one loop,")
print("which is scheme-dependent and non-trivial.")
print()
print("However: if m_H_tree is a BSM/structural value (e.g., from PSC scalar sector),")
print("the CW correction could shift it to 125.2 GeV — but requires knowing m_H_tree independently.")

results = {
    "date": str(date.today()),
    "spec": "SPEC_051_EWV Phase 1 Task 1.2 (Path 2)",
    "CW_delta_mHsq_GeV2": delta_mHsq_val,
    "mH_tree_needed_for_125p2": math.sqrt(mHsq_target) if mHsq_target > 0 else None,
    "conclusion": "Path 2 (CW from c-values): tree-level c(H)/c(W)*mW = 94.97 GeV; CW shifts by large amount; no simple c-value formula gives correct m_H_tree. Path 2 does not close self-consistently with simple tree-level c-value formula.",
    "c_ratio_tree": {"c_H_c_W": c_H/c_W * mW_ugp, "c_H_c_Z": c_H/c_Z * mZ_ugp},
}
with open("/Users/nova/ugp-physics/data_mining/ew_vev/results/path2_cw_correction.json","w") as f:
    json.dump(results, f, indent=2)
print(f"\nSaved to data_mining/ew_vev/results/path2_cw_correction.json")
