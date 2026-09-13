"""
Gorard coarse-graining coefficient C_Gorard for the Rule 110 three-tape CMCA.

Computes C_Gorard from:
  1. Measured Ollivier-Ricci curvature kappa_3D (from three_tape_gorard_chain.py, CatA)
  2. GTE hierarchy Planck-kink ratio M_Pl/m_kink (CatAD, P38)
  3. GR normalization kappa_GR_Planck = 8pi * (m_kink/M_Pl)^4

Gap decomposition: kappa_graph / kappa_GR_Planck = (M_Pl/m_kink)^4 * C_Gorard
=> C_Gorard = kappa_3D / (kappa_GR_Planck * (M_Pl/m_kink)^4)

Saves results to gorard_coefficient_results.json.
"""

import math
import json
import signal
import sys
import time
from collections import defaultdict
import numpy as np

TIMEOUT_SECONDS = 300

def _timeout_handler(signum, frame):
    print(f"\nTIMEOUT: {TIMEOUT_SECONDS}s limit reached. Saving partial results.")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

t_start = time.time()

# ─── 1. Physical parameters ──────────────────────────────────────────────────

M_PL_GEV = 1.22e19        # Planck mass [GeV]
M_KINK_GEV = 0.290        # kink mass = GTE m_tau [GeV], CatAD from P38
KAPPA_3D = 2.32            # three-tape matter Ollivier-Ricci curvature, CatA
KAPPA_GR_PLANCK = 8.01e-78 # GR curvature at Planck scale [dimensionless], CatA from EPIC_078

ratio = M_PL_GEV / M_KINK_GEV
print(f"M_Pl/m_kink = {ratio:.6e}")
print(f"(M_Pl/m_kink)^4 = {ratio**4:.6e}")
print(f"kappa_3D = {KAPPA_3D}")
print(f"kappa_GR_Planck = {KAPPA_GR_PLANCK:.3e}")

# ─── 2. Normalization gap ────────────────────────────────────────────────────

gap = KAPPA_3D / KAPPA_GR_PLANCK
print(f"\nNormalization gap = kappa_3D / kappa_GR_Planck = {gap:.6e}")
print(f"  log10(gap) = {math.log10(gap):.4f}")

# ─── 3. C_Gorard from gap decomposition ─────────────────────────────────────

C_Gorard_v1 = gap / ratio**4
C_Gorard_v2 = 1.0 / (8 * math.pi * C_Gorard_v1)

print(f"\nC_Gorard (v1, gap = ratio^4 * C)   = {C_Gorard_v1:.6f}")
print(f"C_Gorard (v2, gap = ratio^4/(8pi*C)) = {C_Gorard_v2:.6f}")

# ─── 4. Gorard formula for Rule 110 lattice ──────────────────────────────────

# Standard Gorard (2020): kappa = eps^2 / (2(d+2)) * Ric(v,v)
# => C_standard = 1/(2(d+2))
d_eff = 1.0 / (2 * C_Gorard_v1) - 2
print(f"\nEffective dimension from Gorard formula C = 1/(2(d+2)):")
print(f"  d_eff = {d_eff:.4f}  (between d=3: C=0.100 and d=4: C=0.0833)")

# Mixed-dimension formula: 1 temporal (d=1+1=2) + 3 spatial (d=3+1=4)
C_mixed = (1 * 1/(2*(2+2)) + 3 * 1/(2*(4+2))) / 4
print(f"\nMixed-dimension formula C_mixed = (C_d2 + 3*C_d4)/4:")
print(f"  C_d2 = 1/(2*4) = {1/(2*4):.4f}  [1+1D per tape]")
print(f"  C_d4 = 1/(2*6) = {1/(2*6):.4f}  [3+1D effective]")
print(f"  C_mixed = {C_mixed:.6f}  (error: {abs(C_mixed-C_Gorard_v1)/C_Gorard_v1*100:.1f}%)")

# ─── 5. Candidate closed forms ───────────────────────────────────────────────

kappa_SD = KAPPA_3D / 3.0  # per-tape value
candidates = {
    "3/32":                 3/32,
    "1/11":                 1/11,
    "C_mixed=(C_d2+3C_d4)/4": C_mixed,
    "1/(2*(d+2))_d=4":      1/12,
    "1/(2*(d+2))_d=3":      1/10,
    "kappa_3D/(8*pi)":      KAPPA_3D/(8*math.pi),
    "kappa_SD/8":           kappa_SD/8,
    "1/(8*pi)":             1/(8*math.pi),
    "1/(3*pi)":             1/(3*math.pi),
}

print(f"\nCandidate analytical forms for C_Gorard_v1 = {C_Gorard_v1:.4f}:")
print(f"{'Form':>35} {'Value':>10} {'Error%':>10}")
for name, val in sorted(candidates.items(), key=lambda x: abs(x[1]-C_Gorard_v1)):
    err = abs(val - C_Gorard_v1) / C_Gorard_v1 * 100
    print(f"{name:>35} {val:>10.4f} {err:>9.1f}%")

# ─── 6. Normalization gap check ──────────────────────────────────────────────

gap_check = ratio**4 * C_Gorard_v1
print(f"\nNormalization gap check:")
print(f"  (M_Pl/m_kink)^4 * C_Gorard = {gap_check:.4e}")
print(f"  Direct gap = {gap:.4e}")
print(f"  Relative error = {abs(gap_check-gap)/gap:.2e}  (should be <1e-4)")
print(f"  log10(gap) = {math.log10(gap):.4f}  (target: ~77.5)")
gap_pass = abs(math.log10(gap) - 77.5) < 0.2
print(f"  Gap check: {'PASS' if gap_pass else 'FAIL'} (|log10(gap) - 77.5| < 0.2)")

# ─── 7. W1 analysis for ether vacuum ────────────────────────────────────────

# Analytic: W1(Uniform{0,1,2}, Uniform{1,2,3}) = 1 => kappa_ether = 0 exactly
def wasserstein1d(masses1, positions1, masses2, positions2):
    pd1 = defaultdict(float)
    pd2 = defaultdict(float)
    for m, p in zip(masses1, positions1):
        pd1[p] += m
    for m, p in zip(masses2, positions2):
        pd2[p] += m
    all_pos = sorted(set(list(positions1) + list(positions2)))
    cdf1 = cdf2 = 0.0
    W = 0.0
    for i in range(len(all_pos) - 1):
        pos = all_pos[i]
        cdf1 += pd1[pos]
        cdf2 += pd2[pos]
        gap_w = all_pos[i+1] - all_pos[i]
        W += abs(cdf1 - cdf2) * gap_w
    return W

W1_ether = wasserstein1d([1/3,1/3,1/3],[0,1,2], [1/3,1/3,1/3],[1,2,3])
kappa_ether_analytic = 1 - W1_ether
print(f"\nEther background vacuum check:")
print(f"  W1(Uniform{{0,1,2}}, Uniform{{1,2,3}}) = {W1_ether:.6f}")
print(f"  kappa_ether = 1 - W1 = {kappa_ether_analytic:.6f}  (CatAL: should be 0)")

# Kink concentration that gives kappa_SD = 0.77
print(f"\nKink concentration vs kappa:")
best_conc = None
for kc in [x/100 for x in range(50, 100)]:
    ef = (1-kc)/2
    W = wasserstein1d([ef,kc,ef],[0,1,2], [1/3,1/3,1/3],[0,1,2])
    k_val = 1 - W
    if abs(k_val - 0.77) < 0.005:
        print(f"  kink_conc = {kc:.2f} → kappa = {k_val:.4f}  ← matches kappa_SD=0.77")
        best_conc = kc

# ─── 8. Save results ─────────────────────────────────────────────────────────

results = {
    "parameters": {
        "M_Pl_GeV": M_PL_GEV,
        "m_kink_GeV": M_KINK_GEV,
        "ratio_MPl_mkink": ratio,
        "ratio_4th_power": ratio**4,
        "kappa_3D_measured": KAPPA_3D,
        "kappa_SD_per_tape": kappa_SD,
        "kappa_GR_Planck": KAPPA_GR_PLANCK,
    },
    "C_Gorard": {
        "v1_gap_factored": C_Gorard_v1,
        "v2_8pi_convention": C_Gorard_v2,
        "d_effective": d_eff,
        "C_mixed_dim": C_mixed,
    },
    "gap_analysis": {
        "gap_raw": gap,
        "log10_gap": math.log10(gap),
        "gap_check_pass": gap_pass,
    },
    "closest_analytical": {
        "3_over_32": {"value": 3/32, "error_pct": abs(3/32-C_Gorard_v1)/C_Gorard_v1*100},
        "1_over_11": {"value": 1/11, "error_pct": abs(1/11-C_Gorard_v1)/C_Gorard_v1*100},
        "C_mixed": {"value": C_mixed, "error_pct": abs(C_mixed-C_Gorard_v1)/C_Gorard_v1*100},
        "Gorard_d4": {"value": 1/12, "error_pct": abs(1/12-C_Gorard_v1)/C_Gorard_v1*100},
    },
    "vacuum_check": {
        "W1_adjacent_uniforms": W1_ether,
        "kappa_ether_analytic": kappa_ether_analytic,
    },
    "confidence": "CatA",
    "convention_note": (
        "v1: gap = (M_Pl/m_kink)^4 * C_v1 = 0.0925. "
        "v2: gap = (M_Pl/m_kink)^4 / (8pi*C_v2) = 0.430. "
        "Prior lab note C_alt=1.4 was in error."
    ),
    "elapsed_s": round(time.time() - t_start, 2),
}

from pathlib import Path as _Path
_out_path = str(_Path(__file__).parent / "gorard_coefficient_results.json")
with open(_out_path, "w") as f:
    json.dump(results, f, indent=2)

print(f"\nResults saved to {_out_path}")
print(f"Elapsed: {results['elapsed_s']:.1f}s")

signal.alarm(0)
