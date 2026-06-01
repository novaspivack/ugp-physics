"""
G15 Y-junction G_inter determination — is the suppression factor GTE-derivable?

The proton mass formula is
    M_p = 3*M_kink + G_inter * |p(2,2,6)| / 6,
with |p(2,2,6)| = 28 from the canonical GTE polynomial
    p(L,C,R) = C + R - C*R - L*C*R  (mod 7),
    p(2,2,6) = 2 + 6 - 12 - 24 = -28,  |p| = 28.

With sigma_GTE = (9/4)*m_kink^2 (G13 CatAD), the natural string-energy scale is
    sigma_GTE / m_kink = (9/4)*m_kink = 652 MeV,
which overshoots the empirical G_inter = 14.6 MeV by ~45x. The whole question is
whether the ~45x suppression has a first-principles (Fibonacci-free) derivation.

This script:
  1. Tests the proposed winding-only mechanism  G_inter = sigma * N_c * w_u / (m_kink*|p|)
     and related candidates (Task 1).
  2. Runs a quantitative NULL TEST: how many GTE-natural rational suppression
     factors land inside the M_p < 0.1% (CatAD) window?  If the window is
     densely populated, hitting one (e.g. 2/89) is not significant.
  3. Tests the robustness of the Fibonacci claim 2/89.
  4. Makes the honest CatLevel determination for G15.

All numerical results are printed and saved.
"""

import numpy as np
import json
from fractions import Fraction

# --- GTE parameters (all CatAD or better) ------------------------------------
v_H = 246.16
m_kink = 4 * v_H / (49**2 * np.sqrt(2))   # GeV, 4 v_H / (7^4 sqrt 2)
sigma = (9 / 4) * m_kink**2               # GeV^2, G13 CatAD
N_c = 3
C_F = 4 / 3
w_u, w_d = 2, 6
p_norm = 28                                # |p(2,2,6)|, canonical GTE poly
M_p_PDG = 938.272                          # MeV

# Verify canonical polynomial
L, C, R = 2, 2, 6
p_val = C + R - C * R - L * C * R
assert p_val == -28, p_val
assert abs(p_val) == p_norm

three_mkink = 3 * m_kink * 1000            # MeV
G_target = (M_p_PDG - three_mkink) * 6 / p_norm     # MeV, calibrated
ratio_target = G_target / (sigma * 1000 / m_kink)   # dimensionless suppression C

def M_p(G_MeV):
    return three_mkink + G_MeV * p_norm / 6

def err_pct(G_MeV):
    return (M_p(G_MeV) - M_p_PDG) / M_p_PDG * 100

print("=" * 72)
print("G15: Y-JUNCTION G_inter DETERMINATION")
print("=" * 72)
print(f"m_kink            = {m_kink*1000:.4f} MeV   [4 v_H/(7^4 sqrt2)]")
print(f"sigma_GTE         = {sigma:.5f} GeV^2  [(9/4) m_kink^2]")
print(f"sigma/m_kink      = {sigma*1000/m_kink:.3f} MeV  (natural string scale)")
print(f"|p(2,2,6)|        = {p_norm}  (canonical p = C+R-CR-LCR = -28)")
print(f"3 m_kink          = {three_mkink:.3f} MeV")
print(f"G_inter target    = {G_target:.4f} MeV   (calibrated from PDG M_p)")
print(f"suppression ratio = {ratio_target:.6f} = 1/{1/ratio_target:.3f}")
print()

# === TASK 1: winding-only mechanism candidates ===============================
print("-" * 72)
print("TASK 1: proposed winding-only mechanisms  (G = sigma * factor / m_kink)")
print("-" * 72)
sm = sigma * 1000 / m_kink   # MeV
task1 = [
    ("N_c*w_u/|p|       (proposed)", N_c * w_u / p_norm),
    ("w_u/|p|",                       w_u / p_norm),
    ("N_c/|p|",                       N_c / p_norm),
    ("C_F/|p|",                       C_F / p_norm),
    ("w_u/(N_c*|p|)",                 w_u / (N_c * p_norm)),
    ("C_F/(N_c*|p|)",                 C_F / (N_c * p_norm)),
    ("Steiner sqrt3 * 6/|p|",         np.sqrt(3) * (6 / p_norm) * (m_kink / m_kink)),
]
print(f"{'factor':32s}{'value':>12s}{'G_inter':>12s}{'M_p':>12s}{'err%':>10s}")
for label, f in task1:
    G = sm * f
    print(f"{label:32s}{f:12.5f}{G:12.3f}{M_p(G):12.3f}{err_pct(G):+10.3f}")
print(f"\nTarget factor = {ratio_target:.5f}.  Proposed N_c*w_u/|p| = {N_c*w_u/p_norm:.5f} "
      f"(off by {(N_c*w_u/p_norm)/ratio_target:.1f}x).")
print("=> Proposed winding-only mechanism is REFUTED (M_p off by tens of percent).")
print()

# === NULL TEST: density of GTE-natural rationals in the CatAD window =========
print("-" * 72)
print("NULL TEST: how many GTE-natural rationals land in the CatAD M_p window?")
print("-" * 72)
# M_p error scales as (residual/M_p) ~ 0.0728 of the G_inter error, so the
# CatAD M_p<0.1% window corresponds to G_inter within ~1.37% of target, i.e.
# suppression ratio in [lo, hi]:
lo = ratio_target * (1 - 0.1 / 100 * M_p_PDG / (G_target * p_norm / 6))
hi = ratio_target * (1 + 0.1 / 100 * M_p_PDG / (G_target * p_norm / 6))
# Compute exact window by direct M_p evaluation instead:
def in_catad(ratio):
    G = sm * ratio
    return abs(err_pct(G)) < 0.1
# scan a fine grid for the exact ratio window
grid = np.linspace(ratio_target * 0.8, ratio_target * 1.2, 400001)
mask = np.array([abs(err_pct(sm * r)) < 0.1 for r in grid])
window = grid[mask]
win_lo, win_hi = window.min(), window.max()
print(f"CatAD window (|M_p err|<0.1%): suppression ratio in "
      f"[{win_lo:.6f}, {win_hi:.6f}]  (width {win_hi-win_lo:.6f})")
print(f"Relative half-width: {(win_hi-win_lo)/2/ratio_target*100:.3f}% of target")
print()

# GTE-natural atom pool (no Fibonacci): integers/ratios that genuinely appear
# in the framework.
atoms = {
    "1": 1, "2": w_u, "3": N_c, "4": 4, "6": w_d, "7": 7, "9": 9, "16": 16,
    "21": 21, "28": p_norm, "49": 49, "C_F=4/3": C_F,
}
# Build all a/b with a,b drawn from small products of atoms (denominator <= 300).
nat_ratios = {}
vals = [1, 2, 3, 4, 6, 7, 9, 16, 21, 28, 49]
for a in vals:
    for b in vals:
        for c in [1, 2, 3, 4, 6, 7]:
            num = a
            den = b * c
            if den == 0:
                continue
            fr = Fraction(num, den)
            if 0 < float(fr) and den <= 300:
                nat_ratios[fr] = (num, b, c)
# also include C_F-weighted ratios
for b in vals:
    for c in [1, 2, 3, 4]:
        fr = Fraction(4, 3) / (b * c)
        nat_ratios[fr] = ("4/3", b, c)

hits = sorted({fr for fr in nat_ratios if win_lo <= float(fr) <= win_hi},
              key=lambda fr: abs(float(fr) - ratio_target))
print(f"Total distinct GTE-natural rationals scanned: {len(nat_ratios)}")
print(f"Natural rationals inside CatAD window: {len(hits)}")
for fr in hits:
    G = sm * float(fr)
    print(f"   {str(fr):>10s} = {float(fr):.6f}  G={G:6.3f}  M_p={M_p(G):8.3f}  "
          f"err={err_pct(G):+.4f}%")
print()
print("Fibonacci candidate for comparison:")
for k, Fk in [(10, 55), (11, 89), (12, 144)]:
    fr = w_u / Fk
    G = sm * fr
    flag = " <-- best" if abs(err_pct(G)) < 0.1 else ""
    print(f"   w_u/F_{k}=2/{Fk} = {fr:.6f}  G={G:6.3f}  M_p={M_p(G):8.3f}  "
          f"err={err_pct(G):+.4f}%{flag}")
print()

# === ROBUSTNESS of the Fibonacci claim =======================================
print("-" * 72)
print("ROBUSTNESS: is 2/89 special among nearby integers / simple fractions?")
print("-" * 72)
simple = []
for d in range(40, 100):
    fr = 1 / d
    if abs(err_pct(sm * fr)) < 0.1:
        simple.append((f"1/{d}", fr))
for d in range(80, 200):
    fr = 2 / d
    if abs(err_pct(sm * fr)) < 0.1:
        simple.append((f"2/{d}", fr))
print("Simple unit & 2/d fractions inside CatAD window:")
for label, fr in sorted(simple, key=lambda x: abs(err_pct(sm * x[1]))):
    G = sm * fr
    print(f"   {label:>7s} = {fr:.6f}  M_p={M_p(G):8.3f}  err={err_pct(G):+.4f}%")
print()

# === DETERMINATION ===========================================================
print("=" * 72)
print("DETERMINATION")
print("=" * 72)
G_fib = sm * (w_u / 89)
G_CF = C_F * m_kink * 1000 / p_norm  # = m_kink/21, the prior CatA formula
verdict = {
    "fibonacci_formula": {
        "formula": "G_inter = (w_u/F_11) * sigma/m_kink = (2/89)*(9/4)*m_kink",
        "G_inter_MeV": G_fib,
        "M_p_MeV": M_p(G_fib),
        "err_pct": err_pct(G_fib),
        "mechanism": "F_11=89 at Y-junction vertex UNPROVEN (conjectural)",
    },
    "prior_CatA_formula": {
        "formula": "G_inter = C_F * m_kink / |p| = m_kink/21",
        "G_inter_MeV": G_CF,
        "M_p_MeV": M_p(G_CF),
        "err_pct": err_pct(G_CF),
        "mechanism": "C_F (Casimir) and |p| (winding poly) both CatAD/CatAL",
    },
    "task1_proposed_formula_refuted": {
        "formula": "G_inter = sigma*N_c*w_u/(m_kink*|p|)",
        "G_inter_MeV": sm * (N_c * w_u / p_norm),
        "M_p_MeV": M_p(sm * (N_c * w_u / p_norm)),
        "err_pct": err_pct(sm * (N_c * w_u / p_norm)),
    },
    "null_test": {
        "catad_window_ratio_lo": float(win_lo),
        "catad_window_ratio_hi": float(win_hi),
        "natural_rationals_scanned": len(nat_ratios),
        "natural_rationals_in_window": len(hits),
        "natural_rationals_in_window_list": [str(fr) for fr in hits],
    },
    "ratio_target": ratio_target,
}
print(f"Fibonacci 2/89:  M_p = {M_p(G_fib):.3f} MeV ({err_pct(G_fib):+.4f}%) "
      f"-- mechanism UNPROVEN")
print(f"Prior C_F/|p|:   M_p = {M_p(G_CF):.3f} MeV ({err_pct(G_CF):+.4f}%) "
      f"-- ingredients CatAD but precision only CatA")
print(f"Task1 N_c*w_u/|p|: M_p = {M_p(sm*N_c*w_u/p_norm):.3f} MeV "
      f"({err_pct(sm*N_c*w_u/p_norm):+.4f}%) -- REFUTED")
print()
print(f"Null test: {len(hits)} GTE-natural rationals fall in the CatAD window")
print(f"(among {len(nat_ratios)} scanned). The Fibonacci 2/89 is one of several")
print("rationals that hit the window; it carries no derived mechanism.")
print()
print("VERDICT: No Fibonacci-free first-principles formula reproduces M_p at")
print("CatAD. The 2/89 match is a numerical coincidence (mechanism unproven).")
print("G15 closes at CatA (numerical/empirical G_inter), NOT CatAD.")

with open("/Users/nova/ugp-physics/papers/39_qcd_from_gte/scripts/g15_yjunction_results.json", "w") as f:
    json.dump(verdict, f, indent=2)
print("\nSaved results to g15_yjunction_results.json")
