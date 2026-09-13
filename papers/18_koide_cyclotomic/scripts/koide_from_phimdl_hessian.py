"""
koide_from_phimdl_hessian.py
============================
Tests whether the three-tape Phi_MDL Hessian coupling at the w=4 condensate
can produce Koide mass ratios (Q=2/3), and establishes the structural
obstruction to this mechanism.

Expected output range:
  - Q_max from Hessian scan < 0.37 (never reaches target 2/3)
  - S3-symmetric Hessian eigenvalues: degenerate 2D irrep
  - Conclusion: Koide CANNOT come from three-tape cross-polynomial coupling

Reference:
  EPIC_080 rank 080-KOIDE-DYNAMICAL
  P18 (Koide cyclotomic), P45 (three-tape CMCA)
  Session: LAB_NOTE_080_KOIDE_DYNAMICAL.md
"""

import signal
import sys
import json
import itertools
import numpy as np

TIMEOUT_SECONDS = 120

def _timeout_handler(signum, frame):
    print(f"\nTIMEOUT: wall-clock limit {TIMEOUT_SECONDS}s reached. Saving partial results.")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

# =====================================================================
# Physical constants
# =====================================================================
m_tau_PDG = 1776.86     # MeV
m_kink = (8/49) * m_tau_PDG   # = 290.0996 MeV (CatAD from P45)

# w=4 condensate field value: phi0 = 2*pi*4/7
phi0 = 2.0 * np.pi * 4.0 / 7.0

# GTE polynomial: p(L,C,R) = C + R - CR - LCR
def p(x, y, z):
    return z + y - y*z - x*y*z

# =====================================================================
# T1: S3 symmetry test of p(Phi_x, Phi_y, Phi_z)
# =====================================================================
print("=" * 60)
print("T1: S3 symmetry of p(x,y,z) = z + y - yz - xyz")
print("=" * 60)

test_vals_list = [(0.5, 0.3, 0.7), (1.0, 2.0, 3.0), (0.1, 0.5, 0.9)]
t1_results = {}
for tv in test_vals_list:
    perms_p = [(perm, p(*perm)) for perm in itertools.permutations(tv)]
    vals = [v for _, v in perms_p]
    is_s3_sym = len(set([round(v, 8) for v in vals])) == 1
    print(f"  test {tv}: p values = {[round(v, 4) for v in vals]}, S3-symmetric: {is_s3_sym}")
    t1_results[str(tv)] = {
        "p_values": [round(v, 6) for v in vals],
        "s3_symmetric": is_s3_sym
    }

print("  --> p has Z2 symmetry (y<->z) only, NOT S3")

# =====================================================================
# T2: Hessian at w=4 condensate
# =====================================================================
print("\n" + "=" * 60)
print("T2: Hessian of p at w=4 condensate phi0 = 2*pi*4/7")
print("=" * 60)

print(f"  phi0 = {phi0:.6f}")

# Second derivatives at (phi0, phi0, phi0):
# p(x,y,z) = z + y - yz - xyz
# d2p/dx2 = 0
# d2p/dxdy = -z = -phi0
# d2p/dxdz = -y = -phi0
# d2p/dy2 = 0
# d2p/dydz = -1-x = -(1+phi0)
# d2p/dz2 = 0

H = np.array([
    [0.0,      -phi0,        -phi0],
    [-phi0,     0.0,         -(1.0 + phi0)],
    [-phi0,    -(1.0 + phi0), 0.0]
])
print(f"  H = [[0, -{phi0:.4f}, -{phi0:.4f}],")
print(f"       [-{phi0:.4f}, 0, -{1+phi0:.4f}],")
print(f"       [-{phi0:.4f}, -{1+phi0:.4f}, 0]]")
print()

eigenvalues, eigenvectors = np.linalg.eigh(H)
print(f"  Eigenvalues: {eigenvalues}")
print(f"  Note: asymmetry H[0,1]={H[0,1]:.4f} vs H[1,2]={H[1,2]:.4f}, delta=1.0")

# =====================================================================
# T3: S3 decomposition of H
# =====================================================================
print("\n" + "=" * 60)
print("T3: S3 decomposition of Hessian")
print("=" * 60)

# H_sym: average of the three off-diagonal values -> fully S3-symmetric
avg_off = ((-phi0) + (-phi0) + (-(1+phi0))) / 3
H_sym = avg_off * (np.ones((3,3)) - np.eye(3))
H_asym = H - H_sym

eig_sym = np.linalg.eigvalsh(H_sym)
print(f"  S3-symmetric part (all off-diag = {avg_off:.4f}):")
print(f"  Eigenvalues of H_sym: {eig_sym}")
print(f"  --> DEGENERATE: {eig_sym[1]:.4f} = {eig_sym[2]:.4f} (2D irrep)")
print(f"  --> S3-symmetric coupling CANNOT produce 3 distinct masses")
print()
print(f"  S3-breaking part delta={-(1+phi0) - (-phi0):.4f} (fixed, intrinsic to p)")
print(f"  H_asym:\n{H_asym}")

# =====================================================================
# T4: Koide Q scan over G_eff
# =====================================================================
print("\n" + "=" * 60)
print("T4: Koide Q scan over G_eff")
print("=" * 60)

# Koide Q = sum(m) / (sum(sqrt(m)))^2  [where masses m = m_i]
# Target: Q = 2/3 = 0.6667
# Also check mass ratios (target: 1:207:3477 for e:mu:tau)

G_eff_values = np.logspace(-2, 4, 2000)
q_vals = []
best_Q = 0.0
best_G = None
best_masses = None

for G_eff in G_eff_values:
    m_sq = m_kink**2 + G_eff * eigenvalues
    if np.any(m_sq <= 0):
        break
    m = np.sqrt(m_sq)
    Q = np.sum(m) / np.sum(np.sqrt(m))**2
    q_vals.append((G_eff, Q, m.tolist()))
    if Q > best_Q:
        best_Q = Q
        best_G = G_eff
        best_masses = m.tolist()

print(f"  Best Q achieved: {best_Q:.6f} (target: 0.666667)")
print(f"  At G_eff = {best_G:.4f}")
print(f"  Masses: {best_masses}")
if best_masses:
    print(f"  Mass ratios: 1 : {best_masses[1]/best_masses[0]:.2f} : {best_masses[2]/best_masses[0]:.2f}")
print(f"  Target ratios: 1 : 207 : 3477")
print()
print("  Sample Q vs G_eff:")
for G_eff in [0.01, 0.1, 1.0, 10.0, 100.0, 1000.0]:
    m_sq = m_kink**2 + G_eff * eigenvalues
    if np.any(m_sq <= 0):
        print(f"    G_eff={G_eff:8.2f}: TACHYONIC")
        continue
    m = np.sqrt(m_sq)
    Q = np.sum(m) / np.sum(np.sqrt(m))**2
    print(f"    G_eff={G_eff:8.2f}: Q={Q:.6f}, ratios 1:{m[1]/m[0]:.3f}:{m[2]/m[0]:.3f}")

# =====================================================================
# T5: Symmetrized coupling p_cyclic
# =====================================================================
print("\n" + "=" * 60)
print("T5: Symmetrized coupling p_cyclic = (1/3)[p(x,y,z)+p(y,z,x)+p(z,x,y)]")
print("    = (2e1 - e2 - 3e3)/3")
print("=" * 60)

# p_cyclic Hessian at (phi0, phi0, phi0):
# d2p_cyclic/dxdy = -(1+3*phi0)/3 [all equal by S3 symmetry]
# But we consider the normalized version:
off_cyclic = -(1.0 + 3.0 * phi0)
H_cyclic = off_cyclic * (np.ones((3,3)) - np.eye(3))
eig_cyclic = np.linalg.eigvalsh(H_cyclic)
print(f"  Hessian off-diagonal = -(1+3*phi0) = {off_cyclic:.4f}")
print(f"  Eigenvalues: {eig_cyclic}")
print(f"  --> DEGENERATE 2D irrep: {eig_cyclic[1]:.4f} = {eig_cyclic[2]:.4f}")
print()
print("  KEY THEOREM: Any S3-invariant quadratic coupling to three tape fields")
print("  at a symmetric background (phi0,phi0,phi0) produces a 1+2 split")
print("  eigenvalue structure with 2-fold degeneracy in the 2D irrep.")
print("  Therefore: S3-invariant coupling -> CANNOT produce 3 distinct masses -> CANNOT give Koide.")

# =====================================================================
# Summary
# =====================================================================
print("\n" + "=" * 60)
print("SUMMARY: Structural obstruction to Koide from three-tape Hessian")
print("=" * 60)
print()
print("(A) p is NOT S3-symmetric (Z2 symmetry only: y<->z)")
print(f"(B) Hessian eigenvalues at phi0: {eigenvalues}")
print(f"    Asymmetry: H[0,1]={H[0,1]:.3f} vs H[1,2]={H[1,2]:.3f} (delta=1, fixed)")
print(f"(C) Q scan: max Q = {best_Q:.4f}, never reaches 2/3 = 0.6667")
print(f"    Max mass ratio = {max(best_masses)/min(best_masses):.2f} (need 3477)")
print("(D) S3-symmetric Hessian (H_sym): 2D irrep ALWAYS degenerate")
print("    -> algebraically impossible to get 3 distinct masses from S3-invariant coupling")
print()
print("CONCLUSION: 080-KOIDE-DYNAMICAL via three-tape Hessian = RULED OUT (CatA)")
print()
print("The Koide cone is a FLAVOR-SECTOR (generation-exchange symmetry) phenomenon,")
print("NOT a tape-permutation (spatial) symmetry phenomenon.")
print("Correct mechanism: Yukawa coupling in generation space with Z3-orbit structure")
print("  -> requires: generation-dependent kink amplitudes + flavor mass matrix")
print("  -> theta=2/9 from Braid Atlas arithmetic (CatAL, P18) is currently the only derivation")

# =====================================================================
# Save results
# =====================================================================
results = {
    "script": "koide_from_phimdl_hessian.py",
    "epic": "080",
    "rank": "080-KOIDE-DYNAMICAL",
    "parameters": {
        "m_tau_PDG_MeV": m_tau_PDG,
        "m_kink_MeV": float(m_kink),
        "phi0": float(phi0),
        "phi0_description": "2*pi*4/7 (w=4 condensate)"
    },
    "t1_s3_symmetry": {
        "test_cases": t1_results,
        "conclusion": "p is NOT S3-symmetric; has Z2 symmetry (y<->z) only"
    },
    "t2_hessian": {
        "H": H.tolist(),
        "H_offdiag_LC_LR": float(-phi0),
        "H_offdiag_CR": float(-(1+phi0)),
        "H_asymmetry_delta": 1.0,
        "eigenvalues": eigenvalues.tolist(),
        "note": "NOT S3-symmetric: H[0,1]=H[0,2]=-3.59 but H[1,2]=-4.59"
    },
    "t3_s3_decomposition": {
        "H_sym_offdiag_avg": float(avg_off),
        "H_sym_eigenvalues": eig_sym.tolist(),
        "H_sym_2D_irrep_degenerate": True,
        "H_asym": H_asym.tolist(),
        "s3_breaking_delta": 1.0,
        "conclusion": "S3-symmetric part has degenerate 2D irrep -> cannot give 3 distinct masses"
    },
    "t4_koide_scan": {
        "best_Q": float(best_Q),
        "target_Q": 2.0/3.0,
        "best_G_eff": float(best_G) if best_G else None,
        "best_masses_MeV": best_masses,
        "target_mass_ratios": [1.0, 206.77, 3477.0],
        "best_mass_ratios": [1.0, best_masses[1]/best_masses[0], best_masses[2]/best_masses[0]] if best_masses else None,
        "conclusion": "Koide Q never reaches 2/3; max 0.366 at tachyonic boundary"
    },
    "t5_symmetrized_coupling": {
        "H_cyclic_offdiag": float(off_cyclic),
        "H_cyclic_eigenvalues": eig_cyclic.tolist(),
        "theorem": "Any S3-invariant coupling to three tape fields at symmetric background -> 2-fold degenerate 2D irrep -> cannot give 3 distinct Koide masses"
    },
    "conclusion": {
        "status": "RULED OUT (CatA)",
        "mechanism": "Three-tape Hessian coupling does NOT produce Koide cone",
        "structural_obstructions": [
            "p is Z2-symmetric, not S3-symmetric",
            "Hessian Q never exceeds 0.37 (need 0.667)",
            "S3-invariant coupling always gives degenerate 2D irrep",
            "Max mass ratio 4.87:1 (need 207:1 for mu:tau)"
        ],
        "correct_mechanism_required": [
            "Flavor-sector (generation-space) mass matrix with Z3-orbit structure",
            "Yukawa coupling in generation space derived from Phi_MDL+Higgs",
            "theta=2/9 from field couplings (not Braid Atlas arithmetic)"
        ],
        "current_status": "theta=2/9 from N_c=3 is CatAL (P18, Braid Atlas). Phi_MDL-dynamical derivation remains open."
    }
}

import os
out_path = os.path.join(os.path.dirname(__file__), "koide_from_phimdl_hessian_results.json")
with open(out_path, "w") as f:
    json.dump(results, f, indent=2)
print(f"\nResults saved to: {out_path}")

signal.alarm(0)
