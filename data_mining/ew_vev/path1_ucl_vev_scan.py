#!/usr/bin/env python3
"""
SPEC_051_EWV Phase 1, Task 1.1 (Path 3)
Scan UCL / Quarter-Lock / ElegantKernel / structural constants for expressions
that match v/m_W ≈ 3.063 or equivalently 2/g2(M_W) ≈ 3.065.

Also scan for v/m_Z ≈ 2.700 and v itself ≈ 246.22 GeV normalised to
structural energy units.
"""
import math, itertools, json
from datetime import date

# ─────────────────────────────────────────────────────────────────────────────
# Targets (dimensionless ratios)
# ─────────────────────────────────────────────────────────────────────────────
mW_PDG = 80.3792
mZ_PDG = 91.1876
v_PDG  = 246.220
g2_MZ  = math.sqrt(4*math.pi / (127.952 * 0.23122))   # SM g2 at M_Z

TARGET_V_MW  = v_PDG / mW_PDG          # = 3.06324  (= 2/g2(M_W))
TARGET_V_MZ  = v_PDG / mZ_PDG          # = 2.70044
TARGET_2_G2b = 2.0 / math.sqrt(2329.0/5400.0)  # = 2/g2_bare = 3.04538

# ─────────────────────────────────────────────────────────────────────────────
# Structural atoms — from UGP/GTE framework
# ─────────────────────────────────────────────────────────────────────────────
phi  = (1 + math.sqrt(5)) / 2          # golden ratio ≈ 1.61803
pi   = math.pi
sqrt2 = math.sqrt(2)
sqrt3 = math.sqrt(3)
sqrt5 = math.sqrt(5)

# GTE / Braid structural integers and rationals
delta = 7                               # delta_from_N_c: 7
b1    = 73                              # lepton seed b1
Nc    = 3                               # QCD colour
n10   = 10                              # ridge level
strand = 2                              # strand_count = (Nc^2-1)/4
theta_Koide = 2/9                       # Koide phase from Nc
exp_seesaw  = 29/9                      # seesaw exponent

# UCL / ElegantKernel constants (Lean-certified)
k_L2     = 7/512                        # k_L2 = delta/2^(n-1)
k_gen2   = -phi/2                       # thm_ucl2_fully_unconditional
k_gen    = phi * math.cos(pi/10)        # thm_ucl2_fully_unconditional
k_M      = k_gen2 + k_L2/4             # quarterLockLaw: k_M = k_gen2 + (1/4)*k_L2
k_a, k_b, k_c = 1/8, -3/2, 4/3        # Möbius triple (thm_ucl_3)

# EW boson c-values
c_W, c_Z, c_H = 11, 12, 13

# Bare gauge couplings
g1sq = 16/125                           # Lean: g1Sq_bare_eq
g2sq = 2329/5400                        # Lean: g2Sq_bare_eq
g3sq = 41075281/27648000               # Lean: g3Sq_bare_eq
g1, g2, g3 = math.sqrt(g1sq), math.sqrt(g2sq), math.sqrt(g3sq)

# sin2_tW from bare couplings: sin2 = g1^2/(g1^2+g2^2) [GUT normalized]
sin2_tW_bare = g1sq / (g1sq + g2sq)    # SM-08
cos_tW_bare  = math.sqrt(1 - sin2_tW_bare)

# L_model (cosmological constant derivation)
L_model = math.log2(2000/3)            # = log2(D1 * 5^3 / 3)

# ─────────────────────────────────────────────────────────────────────────────
# Build expression library (depth ≤ 2 combinations of atoms)
# ─────────────────────────────────────────────────────────────────────────────
atoms = {
    "phi":        phi,
    "1/phi":      1/phi,
    "phi^2":      phi**2,
    "1/phi^2":    1/phi**2,
    "sqrt(phi)":  math.sqrt(phi),
    "pi":         pi,
    "2*pi":       2*pi,
    "pi/2":       pi/2,
    "pi/3":       pi/3,
    "pi/4":       pi/4,
    "sqrt(2)":    sqrt2,
    "sqrt(3)":    sqrt3,
    "sqrt(5)":    sqrt5,
    "sqrt(6)":    math.sqrt(6),
    "sqrt(10)":   math.sqrt(10),
    "e":          math.e,
    "ln(2)":      math.log(2),
    "1/ln(2)":    1/math.log(2),
    "Nc":         Nc,
    "Nc+1":       Nc+1,
    "2*Nc":       2*Nc,
    "n10":        n10,
    "delta":      delta,
    "c_H/c_W":    c_H/c_W,
    "c_Z/c_W":    c_Z/c_W,
    "c_H/c_Z":    c_H/c_Z,
    "c_H+c_W":    c_H+c_W,
    "sqrt(c_H)":  math.sqrt(c_H),
    "k_gen":      k_gen,
    "k_gen2":     k_gen2,
    "k_M":        k_M,
    "k_L2":       k_L2,
    "-k_gen2":    -k_gen2,
    "|k_gen2|":   abs(k_gen2),
    "2/g2_bare":  2/g2,
    "2/g1_bare":  2/g1,
    "2/g3_bare":  2/g3,
    "g2_bare":    g2,
    "g1_bare":    g1,
    "1/g2_bare":  1/g2,
    "sin2_tW":    sin2_tW_bare,
    "cos_tW":     cos_tW_bare,
    "1/cos_tW":   1/cos_tW_bare,
    "2/cos_tW":   2/cos_tW_bare,
    "L_model":    L_model,
    "exp_seesaw": exp_seesaw,
    "theta_Koide":theta_Koide,
    "strand":     strand,
    "k_a":        k_a,
    "k_b":        k_b,
    "k_c":        k_c,
}

# Generate depth-1 combinations (single atoms, and simple ops)
exprs = {}
for name, val in atoms.items():
    if math.isfinite(val) and val > 0:
        exprs[name] = val

# Depth-2: products, ratios, sums of pairs
atom_list = list(atoms.items())
for i, (n1, v1) in enumerate(atom_list):
    for j, (n2, v2) in enumerate(atom_list):
        if not (math.isfinite(v1) and math.isfinite(v2) and v2 != 0 and v1 != 0):
            continue
        # product
        val = v1 * v2
        if 2.5 < val < 3.5 and math.isfinite(val):
            exprs[f"{n1}*{n2}"] = val
        # ratio
        val = v1 / v2
        if 2.5 < val < 3.5 and math.isfinite(val):
            exprs[f"{n1}/{n2}"] = val
        # sum (only if both ~1.5)
        val = v1 + v2
        if 2.5 < val < 3.5 and math.isfinite(val):
            exprs[f"{n1}+{n2}"] = val

# ─────────────────────────────────────────────────────────────────────────────
# Score against targets
# ─────────────────────────────────────────────────────────────────────────────
TOL = 0.02  # 2% tolerance for reporting

hits_v_mW, hits_v_mZ, hits_2g2b = [], [], []
for name, val in exprs.items():
    for target, label, store in [
        (TARGET_V_MW,  "v/mW=3.063",  hits_v_mW),
        (TARGET_V_MZ,  "v/mZ=2.700",  hits_v_mZ),
        (TARGET_2_G2b, "2/g2b=3.045", hits_2g2b),
    ]:
        dev = abs(val - target) / target
        if dev < TOL:
            store.append({"expr": name, "val": val, "dev_pct": 100*dev})

for store, label in [(hits_v_mW, "v/mW ≈ 3.063"), (hits_v_mZ, "v/mZ ≈ 2.700"), (hits_2g2b, "2/g2_bare ≈ 3.045")]:
    store.sort(key=lambda x: x["dev_pct"])
    print(f"\n{'='*60}")
    print(f"Target: {label}  (within 2%)")
    print(f"{'='*60}")
    for h in store[:15]:
        print(f"  {h['expr']:<40} = {h['val']:.6f}  dev={h['dev_pct']:.3f}%")

# ─────────────────────────────────────────────────────────────────────────────
# Special checks: exact structural expressions
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print("Special structural checks:")
print(f"{'='*60}")

checks = [
    ("2/g2_bare (no running)", 2/g2),
    ("2*pi/phi^2",             2*pi/phi**2),
    ("sqrt(10)",               math.sqrt(10)),
    ("pi/cos_tW_bare",         pi/cos_tW_bare),
    ("2*Nc/g2_bare",           2*Nc/g2),
    ("c_Z/cos_tW",             c_Z/cos_tW_bare),
    ("(c_H+c_W)/cos_tW",       (c_H+c_W)/cos_tW_bare),
    ("sqrt(c_H*c_W)/cos_tW",   math.sqrt(c_H*c_W)/cos_tW_bare),
    ("phi*e",                  phi*math.e),
    ("phi^2 + 1/phi",          phi**2 + 1/phi),
    ("2 + phi/pi",             2 + phi/pi),
    ("pi - 1/phi",             pi - 1/phi),
    ("1/(sin2_tW * g2_bare)",  1/(sin2_tW_bare*g2)),
    ("2/(g2_bare*(1-k_L2))",   2/(g2*(1-k_L2))),
    ("(2+k_L2)/g2_bare",       (2+k_L2)/g2),
]
for label, val in checks:
    dev_vmw = 100*abs(val - TARGET_V_MW)/TARGET_V_MW
    dev_2g2 = 100*abs(val - TARGET_2_G2b)/TARGET_2_G2b
    marker = " *** CLOSE ***" if dev_vmw < 0.5 else ""
    print(f"  {label:<40} = {val:.6f}  dev(v/mW)={dev_vmw:.3f}%  dev(2/g2b)={dev_2g2:.3f}%{marker}")

# ─────────────────────────────────────────────────────────────────────────────
# Key insight: v/mW = 2/g2(MW) = 2/g2_bare * correction_factor
# What is the running correction factor?
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print("Running correction analysis:")
print(f"{'='*60}")
# g2(M_W) ~ g2_bare * correction (from running)
# From Phase 0: g2(M_W) ≈ 0.6528 (computed by ZZ script)
# We can estimate the correction analytically
# 1-loop SU(2) running above m_t: b2 = -19/6
# Delta t = ln(M_W/M2) = ln(80.4/37.4) = 0.762
# Delta g2^(-2) = b2/(8pi^2) * Delta_t = (-19/6)/(8pi^2) * 0.762
b2_above = -19.0/6.0
Delta_t_M2_to_MW = math.log(mW_PDG / 37.4)
Delta_g2inv2_1loop = b2_above / (8*pi**2) * Delta_t_M2_to_MW
g2sq_at_MW_1loop_est = 1 / (1/g2**2 - Delta_g2inv2_1loop)  # perturbative estimate
g2_at_MW_1loop_est = math.sqrt(abs(g2sq_at_MW_1loop_est))
correction_1loop = g2_at_MW_1loop_est / g2  # should be < 1 (SU(2) is IR-free for EW)
v_1loop = 2 * mW_PDG / g2_at_MW_1loop_est

print(f"  1-loop estimate of g2(M_W) = {g2_at_MW_1loop_est:.6f}")
print(f"  Running factor g2(M_W)/g2_bare (1-loop est) = {correction_1loop:.6f}")
print(f"  v_1loop = 2*mW/g2(M_W)_1loop = {v_1loop:.4f} GeV")
print(f"  Is the running factor a simple structural number?")
print(f"  1/(1 - b2*Delta_t/(8pi^2)) = {1/(1-b2_above*Delta_t_M2_to_MW/(8*pi**2)):.6f}")
print(f"  b2 = -19/6, Delta_t = ln(mW/M2) = {Delta_t_M2_to_MW:.4f}")

# Save
results = {
    "date": str(date.today()),
    "spec": "SPEC_051_EWV Phase 1 Task 1.1 (Path 3)",
    "target_v_over_mW": TARGET_V_MW,
    "target_v_over_mZ": TARGET_V_MZ,
    "hits_v_over_mW_top10": hits_v_mW[:10],
    "hits_v_over_mZ_top10": hits_v_mZ[:10],
    "n_exprs_scanned": len(exprs),
    "1loop_g2_mW_estimate": g2_at_MW_1loop_est,
    "1loop_correction_factor": correction_1loop,
    "v_from_1loop_running": v_1loop,
}
with open("/Users/nova/ugp-physics/data_mining/ew_vev/results/path1_ucl_scan.json","w") as f:
    json.dump(results, f, indent=2)
print(f"\nSaved to data_mining/ew_vev/results/path1_ucl_scan.json")
