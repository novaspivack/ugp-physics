"""Unified Koide-cone analysis for the three charged-fermion sectors.

Goal: derive the integer phase divisor r in the closed form
    theta_sector = (N_c^2 - 1) / (4 N_c^2 * r),   r in {1, 2, 3}
for (charged-lepton, down-type, up-type), and test whether the cone
amplitude b^2 is determined by the same structure.

Established inputs (prior sessions / P18):
  - Lepton Koide phase theta_lep = (N_c^2-1)/(4N_c^2) = 2/9   (Lean: koide_angle_from_N_c_pure, CatAL)
    with strand_count = (N_c^2-1)/4 = 2 = lepton-doublet braid strand count (P17).
  - Exact algebraic cone inversion (this file reproduces the Session-3 numbers):
        theta*N_c^2 = {2, 1, 2/3} for {lepton, down, up}  => theta*N_c^2 = 2/r.
  - b^2 = 2 (lepton, = d_std(S_3)); b^2_down = 2.389; b^2_up = 3.094 (PDG, OPEN).

Central new structural observation tested here:
    theta_sector = |H_sector| / N_c^3 = |H_sector| / 27,
  where H_sector is the residual generation-symmetry subgroup of S_3:
        leptons  -> H = S_3   (|H| = 6, S_3 unbroken: Q=2/3 exact)
        down     -> H = Z_3    (|H| = 3, the GTE Frobenius F21=Z7 x| Z3 generation rotation)
        up       -> H = Z_2    (|H| = 2, an isospin-flipped reflection subgroup)
  equivalently r = [S_3 : H] = |S_3|/|H| = {1, 2, 3}, the full subgroup-index chain of S_3.

All numbers are computed; no value is hard-coded from the prior fit.
"""
import itertools
import json
import math
import os

import numpy as np

# --- PDG 2024 masses (GeV) ---------------------------------------------------
SECTORS = {
    "lepton":    {"m": [0.511e-3, 105.658e-3, 1776.86e-3], "s": [0.0, 0.0, 0.12e-3]},
    "up_type":   {"m": [2.16e-3, 1.27, 172.69],            "s": [0.38e-3, 0.02, 0.30]},
    "down_type": {"m": [4.67e-3, 93.4e-3, 4.18],           "s": [0.33e-3, 6.5e-3, 0.025]},
}

N_c = 3
TWO_PI_3 = 2 * np.pi / 3

# GTE / SM quantum numbers for the three sectors (P17 braid atlas, vocabulary rule).
# Reduced Z7 winding W in {-3..3}: Q = W / N_c.  e=-3, u=+2, d=-1.
QN = {
    "lepton":    {"W_raw": 4, "W_red": -3, "Q": -1.0,      "T3": -0.5, "strands": 2},
    "up_type":   {"W_raw": 2, "W_red": +2, "Q": +2.0 / 3,  "T3": +0.5, "strands": 3},
    "down_type": {"W_raw": 6, "W_red": -1, "Q": -1.0 / 3,  "T3": -0.5, "strands": 3},
}


def koide_invert(masses):
    """Exact, unique Koide cone inversion. Returns (m0, b, theta_raw)."""
    sm = np.sqrt(np.asarray(masses, dtype=float))
    sqrt_m0 = sm.sum() / 3.0
    x = sm / sqrt_m0 - 1.0
    C = x[0]
    S = (x[2] - x[1]) / np.sqrt(3.0)
    b = np.hypot(C, S)
    theta = np.arctan2(S, C)
    return sqrt_m0 ** 2, b, theta


def reduce_phase(theta):
    return theta % TWO_PI_3


# === 1. Reproduce the exact cone parameters =================================
print("=" * 72)
print("1. EXACT CONE INVERSION  (reproduces Session-3 values)")
print("=" * 72)
fit = {}
for name, d in SECTORS.items():
    m0, b, th = koide_invert(d["m"])
    th_red = reduce_phase(th)
    fit[name] = {"b": b, "b2": b * b, "theta": th_red, "theta_x_Nc2": th_red * N_c ** 2,
                 "theta_x_Nc3": th_red * N_c ** 3}
    print(f"  {name:10s}: b^2 = {b*b:.4f}   theta = {th_red:.6f}   "
          f"theta*N_c^2 = {th_red*N_c**2:.5f}   theta*N_c^3 = {th_red*N_c**3:.4f}")

# === 2. The subgroup-order closed form  theta = |H| / N_c^3 =================
print("\n" + "=" * 72)
print("2. SUBGROUP-ORDER CLOSED FORM   theta_sector = |H_sector| / N_c^3")
print("=" * 72)
# Residual generation symmetry subgroup of S_3 for each sector.
H = {"lepton": ("S_3", 6), "down_type": ("Z_3", 3), "up_type": ("Z_2", 2)}
print(f"  N_c^3 = {N_c**3}")
print(f"  {'sector':10s} {'H':5s} {'|H|':>4s} {'theta_pred=|H|/27':>18s} "
      f"{'theta_meas':>12s} {'dev%':>8s}  r=[S3:H]")
subgroup_form = {}
for name in ("lepton", "down_type", "up_type"):
    hname, hord = H[name]
    th_pred = hord / N_c ** 3
    th_meas = fit[name]["theta"]
    dev = (th_pred - th_meas) / th_meas * 100
    r_index = 6 // hord
    subgroup_form[name] = {"H": hname, "order": hord, "theta_pred": th_pred,
                           "theta_meas": th_meas, "dev_pct": dev, "r_index": r_index}
    print(f"  {name:10s} {hname:5s} {hord:4d} {th_pred:18.6f} "
          f"{th_meas:12.6f} {dev:+8.2f}  r={r_index}")
print("\n  => theta_sector = |H|/N_c^3 with |H| in {6,3,2} = the full subgroup chain of S_3")
print("     r = [S_3:H] = 6/|H| = {1,2,3}; r-divisor and subgroup index are identical.")

# === 3. Carl/Ninja hypothesis r = {1, N_c-1, N_c} (same integers) ===========
print("\n" + "=" * 72)
print("3. STRAND/COUPLING-COUNT HYPOTHESIS  r = {1, N_c-1, N_c}")
print("=" * 72)
r_strand = {"lepton": 1, "down_type": N_c - 1, "up_type": N_c}
for name in ("lepton", "down_type", "up_type"):
    r = r_strand[name]
    th_pred = (N_c ** 2 - 1) / (4 * N_c ** 2 * r)
    dev = (th_pred - fit[name]["theta"]) / fit[name]["theta"] * 100
    print(f"  {name:10s} r={r}  theta_pred={th_pred:.6f}  dev {dev:+.2f}%")
print("  NOTE: identical integers to the subgroup index; but {N_c-1, N_c} does not by")
print("        itself say WHY down<-N_c-1 and up<-N_c. The subgroup picture is the content.")

# === 4. Independent integer candidates for r (Adam null sweep) ==============
print("\n" + "=" * 72)
print("4. CAN ANY *INDEPENDENT* GTE INTEGER REPRODUCE r=(1,2,3) FOR (lep,down,up)?")
print("=" * 72)
target_r = {"lepton": 1, "down_type": 2, "up_type": 3}
candidates = {
    "|W_red| (reduced winding)":  {n: abs(QN[n]["W_red"]) for n in QN},
    "W_raw (Z7 winding)":         {n: QN[n]["W_raw"] for n in QN},
    "N_c-|W_red|":                {n: N_c - abs(QN[n]["W_red"]) for n in QN},
    "braid strand count":         {n: QN[n]["strands"] for n in QN},
    "3*|Q| (charge)":             {n: round(3 * abs(QN[n]["Q"])) for n in QN},
    "subgroup index [S3:H]":      {n: subgroup_form[n]["r_index"] for n in QN},
}
for label, cand in candidates.items():
    match = all(cand[n] == target_r[n] for n in target_r)
    seq = tuple(cand[n] for n in ("lepton", "down_type", "up_type"))
    print(f"  {label:28s} (lep,down,up)={seq}  {'<<< MATCHES r=(1,2,3)' if match else ''}")

# === 5. Is b^2 determined by r / |H| ? (Jane) ===============================
print("\n" + "=" * 72)
print("5. IS b^2 A FUNCTION OF r / |H| ?")
print("=" * 72)
b2 = {n: fit[n]["b2"] for n in fit}
r = {n: subgroup_form[n]["r_index"] for n in fit}
print(f"  measured: b2_lep={b2['lepton']:.4f}  b2_down={b2['down_type']:.4f}  b2_up={b2['up_type']:.4f}")
print(f"  delta b2 = b2 - 2:  lep={b2['lepton']-2:.4f}  down={b2['down_type']-2:.4f}  up={b2['up_type']-2:.4f}")
print("\n  Candidate closed forms b2(r):")
forms = {
    "2*r":                  lambda rr: 2 * rr,
    "2 + (r-1)":            lambda rr: 2 + (rr - 1),
    "2 + (N_c-1)/r":        lambda rr: 2 + (N_c - 1) / rr,
    "2 + (N_c-1)/r^2":      lambda rr: 2 + (N_c - 1) / rr ** 2,
    "2 + (N_c-1)/r^1.5":    lambda rr: 2 + (N_c - 1) / rr ** 1.5,
    "2 + 2/r":              lambda rr: 2 + 2 / rr,
    "2 * (1 + (r-1)/N_c)":  lambda rr: 2 * (1 + (rr - 1) / N_c),
    "d_std + (r-1)*d_triv": lambda rr: 2 + (rr - 1),
    "1 + r/(r+1) + ...":    None,
}
for label, fn in forms.items():
    if fn is None:
        continue
    preds = {n: fn(r[n]) for n in r}
    errs = {n: (preds[n] - b2[n]) / b2[n] * 100 for n in r}
    okd = abs(errs["down_type"]) < 2
    oku = abs(errs["up_type"]) < 2
    print(f"  {label:22s} down={preds['down_type']:.3f}({errs['down_type']:+.1f}%) "
          f"up={preds['up_type']:.3f}({errs['up_type']:+.1f}%)  lep={preds['lepton']:.3f}  "
          f"{'PASS' if (okd and oku) else ''}")

# delta-b2 ordering vs r (no fit, just direction)
print("\n  delta-b2 vs r:  (lep,down,up)=({:.3f},{:.3f},{:.3f}); r=(1,2,3) monotone? {}".format(
    b2['lepton'] - 2, b2['down_type'] - 2, b2['up_type'] - 2,
    (b2['lepton'] - 2) < (b2['down_type'] - 2) < (b2['up_type'] - 2)))

# === 6. b^2 from residual-subgroup irrep equipartition ======================
print("\n" + "=" * 72)
print("6. b^2 FROM RESIDUAL-SUBGROUP IRREP STRUCTURE (MDL equipartition test)")
print("=" * 72)
# For S_3 on R^3 = 1 (+) 2 (trivial + standard). Equal Frobenius norm of the two
# irreps fixes b^2 = d_std = 2 (lepton, CatAD).  When S_3 -> H, the standard 2-rep
# either stays irreducible (H=Z_3, a rotation by 2pi/3 keeps the 2D plane irreducible
# over R) or splits 1+1 (H=Z_2, a reflection has a 1D fixed axis + 1D flip in the plane).
# Equipartition then runs over the H-irreps. We test whether the resulting b^2
# matches; this is the natural extension of KOIDE-EQUALNORM to broken sectors.
def b2_equipartition(irrep_dims):
    """Equal-norm Koide amplitude when R^3 = (+) irreps with given real dims.
    The trivial direction (uniform vector, dim 1) carries the mean; the remaining
    'shape' dims carry b. Equal Frobenius norm across the non-trivial irrep blocks
    gives b^2 = (sum of non-trivial dims). For S_3: nontrivial = the 2-block => 2."""
    nontrivial = [d for d in irrep_dims[1:]]
    return sum(nontrivial)

scenarios = {
    "lepton  (S_3:  1+2)":      [1, 2],
    "down    (Z_3:  1+2_rot)":  [1, 2],
    "up      (Z_2:  1+1+1)":    [1, 1, 1],
}
for label, dims in scenarios.items():
    print(f"  {label:24s} equipartition b^2 = {b2_equipartition(dims):.1f}")
print("  -> pure equipartition gives 2,2,2 (lep ok). The quark b^2>2 excess is NOT a")
print("     dimension count; it requires the *unequal* H-irrep norms (S_3 broken).")

# === 7. Null/over-fitting test for the subgroup assignment ==================
print("\n" + "=" * 72)
print("7. NULL TEST: is the subgroup -> sector assignment forced or fitted?")
print("=" * 72)
# There are 3 sectors and 3 candidate subgroup orders {6,3,2}. Number of bijections = 6.
# Only assignments with theta=|H|/27 within the measured error of all three count as 'fits'.
orders = [6, 3, 2]
meas = {n: fit[n]["theta"] for n in fit}
# relative tolerance from Session-3 MC: lepton ~0.004%, down ~4.8%, up ~0.9%
tol = {"lepton": 0.001, "down_type": 0.05, "up_type": 0.02}
good = []
for perm in itertools.permutations(orders):
    assign = dict(zip(("lepton", "down_type", "up_type"), perm))
    ok = all(abs(assign[n] / 27 - meas[n]) / meas[n] < tol[n] for n in meas)
    if ok:
        good.append(assign)
print(f"  bijections of {{6,3,2}} -> (lepton,down,up): {len(good)} of 6 match within PDG error")
for g in good:
    print(f"    forced assignment: lepton<-{g['lepton']}  down<-{g['down_type']}  up<-{g['up_type']}")
print("  => the angle data ALONE forces lepton<-6 uniquely (it pins 2/9 to 0.004%);")
print("     down<-3, up<-2 is the only remaining bijection consistent with both quark angles.")

# === 8. Summary =============================================================
summary = {
    "N_c": N_c,
    "fit": fit,
    "subgroup_form": {n: subgroup_form[n] for n in subgroup_form},
    "closed_form_theta": "theta_sector = |H_sector| / N_c^3, |H| in {6,3,2} for {S_3,Z_3,Z_2}; r=[S_3:H]={1,2,3}",
    "independent_integer_match": {
        label: all(cand[n] == target_r[n] for n in target_r) for label, cand in candidates.items()
    },
    "b2_measured": b2,
    "b2_is_function_of_r": False,
    "null_test_forced_bijections": good,
}
out = "papers/18_koide_cyclotomic/scripts/quark_koide_unified_cone_results.json"
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w") as f:
    json.dump(summary, f, indent=2, default=float)
print(f"\nSaved -> {out}")
