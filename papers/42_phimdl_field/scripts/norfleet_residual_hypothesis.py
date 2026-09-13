#!/usr/bin/env python3
"""Norfleet-constant hypothesis battery for 088-R11a (Task 3).

PRE-REGISTERED CANDIDATE FORMS (declared before computation; Round 1):
  Λ_N = ln(phi)/ln(2pi) = 0.261799...

Targets:
  T_A = sharp-vs-smooth residual = c_S5_tree - c_S1_tree = 2.2029
         (asymptotic form 4*gamma_E = 2.3089)
  T_B = c_S1_tree = 8 ln(8/7) = 1.06830 (exact)
  T_C_tree = c_tape_tree = -1.00 (tape control)
  T_C_pole = c_S1_pole = 1.8860
  T_D = ln(Lambda/m_phi)|_tree = ln(8/7) = 0.13353 (exact)
  T_D_pole = ln(Lambda/m_phi)|_pole = 0.23572

Pre-registered forms (tolerance 1.0%, except exact targets 0.1%):
  N1: T = k*Lambda_N, k in {1,2,...,12, 1/2, 3/2, 5/2}
  N2: gamma_E/2 == Lambda_N  (exact-grade: |x - y| < 1e-4)
  N3: c_S1_tree == 4*Lambda_N  (exact-grade)
  N4: ln(Lambda/m)|_pole == Lambda_N  (exact-grade)
  N5: Lambda/m_phi == 1 + Lambda_N/2  (1% tolerance)
  N6: generic scan over Lambda_N^+/-1 * GTE atoms

Null battery:
  Wrong-target nulls: same forms on |c_coset| = 1.00, Lambda-ratio 15.840,
                      lattice |kappa_s| = 0.125
  Neighbor nulls: Λ_N perturbed to 7 neighbors (ln phi / ln X, X perturbed)
  Monte Carlo: 20000 random magnitude-matched constants, count hits >= match rate

Decision rule:
  GOVERNS: tolerance match + ALL nulls pass + mechanism cited
  NUMEROLOGY: match but any null fails
  NO MATCH: no tolerance-grade match

Reports each form verdict with full arithmetic shown.
"""
import json
import math
import random
import signal
import sys

TIMEOUT_SECONDS = 300


def _timeout(signum, frame):
    print("TIMEOUT reached")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

# ─── Constants ────────────────────────────────────────────────────────────────
PHI = (1.0 + math.sqrt(5.0)) / 2.0
GAMMA_E = 0.5772156649015329
LAMBDA_N = math.log(PHI) / math.log(2.0 * math.pi)  # = 0.26179938...
PI = math.pi

print("=" * 65)
print("Norfleet Hypothesis Battery  —  088-R11a Task 3")
print("=" * 65)
print(f"\nΛ_N = ln(φ)/ln(2π) = {LAMBDA_N:.10f}")
print(f"φ   = {PHI:.10f}")
print(f"γ_E = {GAMMA_E:.10f}")
print(f"4γ_E = {4*GAMMA_E:.10f}  (asymptotic sharp-vs-smooth residual)")

# ─── Targets (from prior sessions, all pre-registered) ────────────────────────
T_A = 4.0 * GAMMA_E                  # asymptotic residual (exact form)
T_A_actual = 2.2029                  # tree-reading actual (finite-M)
T_B = 8.0 * math.log(8.0 / 7.0)     # c^{S1,tree} = 8 ln(8/7) = 1.0683
T_D_tree = math.log(8.0 / 7.0)      # ln(Λ/m)|_tree = 0.1335
T_D_pole = math.log(7.0 * 321.32 / 1776.86)  # ln(Λ/m)|_pole
T_S1_pole = 8.0 * T_D_pole           # c^{S1,pole} = 1.8860
T_tape = -1.00                       # tape control
T_coset = 1.00                       # |c_coset| (wrong-target null)
T_lambda_ratio = 15.840              # Λ_MS̄/Λ_HK from R09 (wrong-target null)
T_kappa = 0.125                      # lattice |κ_s| (wrong-target null)

targets = {
    "T_A (4 gamma_E)": T_A,
    "T_A_actual (tree residual)": T_A_actual,
    "T_B (8 ln(8/7))": T_B,
    "T_D_tree (ln(8/7))": T_D_tree,
    "T_D_pole": T_D_pole,
    "T_S1_pole": T_S1_pole,
    "T_tape (|c_latt|)": abs(T_tape),
}
wrong_targets = {
    "|c_coset|": T_coset,
    "Lambda_ratio 15.840": T_lambda_ratio,
    "|kappa_s| 0.125": T_kappa,
}

print(f"\nTargets:")
for k, v in targets.items():
    print(f"  {k:30s} = {v:.8f}")

# ─── N1: integer / half-integer multiples ─────────────────────────────────────
TOLERANCE = 0.010   # 1%
EXACT_TOL = 5e-4    # 0.05% for exact-grade named candidates

print("\n" + "=" * 65)
print("N1: T = k * Λ_N,  k ∈ {½, 1, 2, …, 12, 3/2, 5/2}")
print("=" * 65)

n1_hits = {}
ks = [0.5, 1.5, 2.5] + list(range(1, 13))
for tname, t in targets.items():
    for k in ks:
        pred = k * LAMBDA_N
        rel_err = abs(pred - t) / max(t, 1e-12)
        if rel_err < TOLERANCE:
            label = "EXACT" if rel_err < EXACT_TOL else "tol"
            n1_hits.setdefault(tname, []).append((k, pred, rel_err, label))
            print(f"  HIT: {tname} = {t:.6f}; k={k}; "
                  f"k*Λ_N = {pred:.6f}; err = {rel_err:.4e} [{label}]")

if not n1_hits:
    print("  No hits.")

# Count hits on wrong-target nulls
print("\nN1 wrong-target nulls:")
n1_null_hits = 0
for wname, wt in wrong_targets.items():
    for k in ks:
        pred = k * LAMBDA_N
        rel_err = abs(pred - wt) / max(wt, 1e-12)
        if rel_err < TOLERANCE:
            n1_null_hits += 1
            print(f"  NULL HIT: {wname} = {wt:.6f}; k={k}; "
                  f"k*Λ_N = {pred:.6f}; err = {rel_err:.4e} ← NULL FAILS")
if n1_null_hits == 0:
    print("  No null hits (good).")

# ─── N2: γ_E/2 == Λ_N ───────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("N2: γ_E/2 == Λ_N  (exact-grade)")
print("=" * 65)
gam_half = GAMMA_E / 2.0
print(f"  γ_E/2 = {gam_half:.10f}")
print(f"  Λ_N   = {LAMBDA_N:.10f}")
print(f"  diff  = {abs(gam_half - LAMBDA_N):.4e}  ({abs(gam_half - LAMBDA_N)/LAMBDA_N:.4e} relative)")
n2_pass = abs(gam_half - LAMBDA_N) / LAMBDA_N < EXACT_TOL
print(f"  RESULT: {'MATCH ← CHECK MECHANISM' if n2_pass else 'NO MATCH (well separated)'}")

# ─── N3: c^{S1,tree} == 4*Λ_N ────────────────────────────────────────────────
print("\n" + "=" * 65)
print("N3: 8 ln(8/7) == 4*Λ_N  (exact-grade, user-proposed)")
print("=" * 65)
four_lam = 4.0 * LAMBDA_N
print(f"  8 ln(8/7)  = {T_B:.10f}")
print(f"  4 * Λ_N    = {four_lam:.10f}")
print(f"  diff       = {abs(T_B - four_lam):.4e}  ({abs(T_B - four_lam)/T_B:.4e} relative)")
n3_pass = abs(T_B - four_lam) / T_B < EXACT_TOL
print(f"  RESULT: {'MATCH ← CHECK MECHANISM' if n3_pass else 'NO MATCH'}")

# ─── N4: ln(Λ/m)|_pole == Λ_N ────────────────────────────────────────────────
print("\n" + "=" * 65)
print("N4: ln(Λ/m)|_pole == Λ_N  (exact-grade)")
print("=" * 65)
print(f"  ln(Λ/m)|_pole = {T_D_pole:.10f}")
print(f"  Λ_N           = {LAMBDA_N:.10f}")
print(f"  diff          = {abs(T_D_pole - LAMBDA_N):.4e}  "
      f"({abs(T_D_pole - LAMBDA_N)/LAMBDA_N:.4e} relative)")
n4_pass = abs(T_D_pole - LAMBDA_N) / LAMBDA_N < EXACT_TOL
print(f"  RESULT: {'MATCH ← VERIFY' if n4_pass else 'NO MATCH'}")

# ─── N5: Λ/m_phi == 1 + Λ_N/2 (Information Profit form) ─────────────────────
print("\n" + "=" * 65)
print("N5: Λ/m_phi == 1 + Λ_N/2  (Info-Profit form, pole reading)")
print("=" * 65)
m_phi = 1776.86
lam_pole = 7.0 * 321.32
ratio_pole = lam_pole / m_phi
pred_n5 = 1.0 + LAMBDA_N / 2.0
print(f"  Λ_pole/m_phi = {ratio_pole:.8f}")
print(f"  1 + Λ_N/2   = {pred_n5:.8f}")
print(f"  diff         = {abs(ratio_pole - pred_n5):.4e}  "
      f"({abs(ratio_pole - pred_n5)/pred_n5:.4e} relative)")
n5_pass = abs(ratio_pole - pred_n5) / pred_n5 < TOLERANCE
print(f"  RESULT: {'MATCH ← VERIFY' if n5_pass else 'NO MATCH'}")

# ─── N6: generic scan with GTE atoms ─────────────────────────────────────────
print("\n" + "=" * 65)
print("N6: T = Λ_N^{±1} * X,  X over GTE atom set")
print("=" * 65)
atoms_raw = {
    "1": 1.0, "2": 2.0, "3": 3.0, "4": 4.0, "7": 7.0, "8": 8.0,
    "1/2": 0.5, "1/7": 1.0/7.0, "8/7": 8.0/7.0,
    "pi": PI, "2pi": 2.0*PI, "gamma_E": GAMMA_E,
    "ln2": math.log(2.0), "ln7": math.log(7.0),
    "e": math.e, "phi": PHI, "1/phi": 1.0/PHI,
    "sqrt2": math.sqrt(2.0), "sqrt3": math.sqrt(3.0),
}
n6_hits = {}
for tname, t in targets.items():
    for aname, a in atoms_raw.items():
        for sign in (1, -1):
            pred = LAMBDA_N ** sign * a
            if pred <= 0:
                continue
            rel_err = abs(pred - t) / max(t, 1e-12)
            if rel_err < TOLERANCE:
                n6_hits.setdefault(tname, []).append(
                    (f"Λ_N^{sign}*{aname}", pred, rel_err))
                print(f"  HIT: {tname} = {t:.6f}; "
                      f"Λ_N^{sign}*{aname} = {pred:.6f}; err = {rel_err:.4e}")

if not n6_hits:
    print("  No hits.")

# ─── Neighbor nulls ───────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("Neighbor nulls: perturb ln(2π) denominator")
print("=" * 65)
neighbors = {
    "ln(2pi*e)": math.log(PHI) / math.log(2.0 * PI * math.e),
    "ln(pi)": math.log(PHI) / math.log(PI),
    "ln(4pi)": math.log(PHI) / math.log(4.0 * PI),
    "ln(2)/ln(2pi)": math.log(2.0) / math.log(2.0 * PI),
    "ln(3)/ln(2pi)": math.log(3.0) / math.log(2.0 * PI),
    "pi/12": PI / 12.0,
    "ln(phi)/pi": math.log(PHI) / PI,
}
neighbor_hits = 0
for nname, nval in neighbors.items():
    for tname, t in targets.items():
        for k in ks:
            pred = k * nval
            rel_err = abs(pred - t) / max(t, 1e-12)
            if rel_err < TOLERANCE:
                neighbor_hits += 1
                print(f"  NEIGHBOR HIT: {tname} = {t:.6f}; "
                      f"k={k}*{nname}={pred:.6f}; err={rel_err:.4e} ← NULL FAILS")
if neighbor_hits == 0:
    print("  No neighbor hits (good).")

# ─── Monte Carlo coincidence rate ─────────────────────────────────────────────
print("\n" + "=" * 65)
print("Monte Carlo: 20000 random magnitudes, count at-or-above hit rate")
print("=" * 65)
random.seed(20260609)
# magnitude range: cover all targets [0.1, 20]
n_mc = 20000
all_targets_vals = list(targets.values())
hits_mc = 0
for _ in range(n_mc):
    c = random.uniform(0.05, 25.0)
    for t in all_targets_vals:
        if abs(c - t) / max(t, 1e-12) < TOLERANCE:
            hits_mc += 1
            break
rate_mc = hits_mc / n_mc
# actual total N1 hits on targets:
n1_target_hits = sum(len(v) for v in n1_hits.values())
n6_target_hits = sum(len(v) for v in n6_hits.values())
total_struct_hits = n1_target_hits + n6_target_hits + (1 if n3_pass else 0)
print(f"  Random hit rate at 1% tolerance over [0.05, 25]: {rate_mc:.4f}")
print(f"  Expected hits from random in N1 (k in {len(ks)} values × "
      f"{len(targets)} targets): {len(ks)*len(targets)*rate_mc:.2f}")
print(f"  Actual N1 hits: {n1_target_hits}")
print(f"  Total structured hits (N1+N3+N6): {total_struct_hits}")

# ─── VERDICT ──────────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("VERDICT SUMMARY")
print("=" * 65)

print(f"\nN2 (γ_E/2 = Λ_N): {'FAIL (not equal)' if not n2_pass else 'MATCH'}")
print(f"  γ_E/2 = {GAMMA_E/2:.8f}, Λ_N = {LAMBDA_N:.8f}, "
      f"diff = {abs(GAMMA_E/2 - LAMBDA_N):.6f} ({abs(GAMMA_E/2 - LAMBDA_N)/LAMBDA_N*100:.2f}%)")

print(f"\nN3 (8 ln(8/7) = 4 Λ_N): {'FAIL (not equal)' if not n3_pass else 'MATCH'}")
print(f"  8 ln(8/7) = {T_B:.8f}, 4Λ_N = {4*LAMBDA_N:.8f}, "
      f"diff = {abs(T_B - 4*LAMBDA_N):.6f} ({abs(T_B - 4*LAMBDA_N)/T_B*100:.2f}%)")

print(f"\nN4 (ln(Λ/m)|_pole = Λ_N): {'FAIL (not equal)' if not n4_pass else 'MATCH'}")
print(f"  ln(Λ/m)|_pole = {T_D_pole:.8f}, Λ_N = {LAMBDA_N:.8f}, "
      f"diff = {abs(T_D_pole - LAMBDA_N):.6f} ({abs(T_D_pole - LAMBDA_N)/LAMBDA_N*100:.2f}%)")

print(f"\nN5 (Λ_pole/m = 1+Λ_N/2): {'MATCH' if n5_pass else 'FAIL (not equal)'}")
print(f"  Λ_pole/m = {ratio_pole:.6f}, 1+Λ_N/2 = {pred_n5:.6f}, "
      f"diff = {abs(ratio_pole - pred_n5):.6f} ({abs(ratio_pole - pred_n5)/pred_n5*100:.2f}%)")

print(f"\nN1 non-trivial hits on physics targets: {n1_target_hits}")
print(f"N6 non-trivial hits: {n6_target_hits}")
print(f"Wrong-target null failures: {n1_null_hits}")
print(f"Neighbor null failures: {neighbor_hits}")
print(f"\nMonte Carlo rate: {rate_mc:.4f}; "
      f"expected random hits in N1: {len(ks)*len(targets)*rate_mc:.2f}; "
      f"actual: {n1_target_hits}")

# ─── specific value check: 4 gamma_E vs 8 Λ_N ────────────────────────────────
print("\n" + "=" * 65)
print("Key arithmetic: the asymptotic residual 4γ_E vs 8Λ_N")
print("=" * 65)
print(f"  4γ_E    = {4*GAMMA_E:.10f}")
print(f"  8Λ_N    = {8*LAMBDA_N:.10f}")
print(f"  ratio   = {4*GAMMA_E / (8*LAMBDA_N):.10f}")
print(f"  diff    = {abs(4*GAMMA_E - 8*LAMBDA_N):.6f}  ({abs(4*GAMMA_E - 8*LAMBDA_N)/(4*GAMMA_E)*100:.2f}%)")
hits_4gam_8lam = abs(4*GAMMA_E - 8*LAMBDA_N) / (4*GAMMA_E) < EXACT_TOL
print(f"  4γ_E == 8Λ_N? {'YES (exact match)' if hits_4gam_8lam else 'NO (well separated)'}")

# ─── Output ───────────────────────────────────────────────────────────────────
results = {
    "lambda_N": LAMBDA_N, "gamma_E": GAMMA_E, "phi": PHI,
    "targets": targets,
    "N2_gamma_half_vs_lambda_N": {
        "gamma_half": GAMMA_E/2, "lambda_N": LAMBDA_N,
        "diff": abs(GAMMA_E/2 - LAMBDA_N),
        "rel_err": abs(GAMMA_E/2 - LAMBDA_N)/LAMBDA_N, "pass": n2_pass},
    "N3_8ln87_vs_4lambdaN": {
        "8ln87": T_B, "4lambdaN": 4*LAMBDA_N,
        "diff": abs(T_B - 4*LAMBDA_N),
        "rel_err": abs(T_B - 4*LAMBDA_N)/T_B, "pass": n3_pass},
    "N4_logwindow_pole_vs_lambdaN": {
        "logwindow_pole": T_D_pole, "lambda_N": LAMBDA_N,
        "diff": abs(T_D_pole - LAMBDA_N),
        "rel_err": abs(T_D_pole - LAMBDA_N)/LAMBDA_N, "pass": n4_pass},
    "N5_ratio_vs_profit_form": {
        "ratio_pole": ratio_pole, "1_plus_lambdaN_over_2": pred_n5,
        "diff": abs(ratio_pole - pred_n5),
        "rel_err": abs(ratio_pole - pred_n5)/pred_n5, "pass": n5_pass},
    "N1_hits": n1_hits,
    "N6_hits": n6_hits,
    "wrong_target_null_failures": n1_null_hits,
    "neighbor_null_failures": neighbor_hits,
    "mc_random_rate": rate_mc,
    "mc_expected_n1_hits": len(ks)*len(targets)*rate_mc,
    "n1_actual_hits": n1_target_hits,
    "4gamma_vs_8lambdaN": {
        "4gamma": 4*GAMMA_E, "8lambdaN": 8*LAMBDA_N,
        "diff": abs(4*GAMMA_E - 8*LAMBDA_N),
        "rel_err": abs(4*GAMMA_E - 8*LAMBDA_N)/(4*GAMMA_E),
        "pass": hits_4gam_8lam}
}
out = "/Users/nova/ugp-physics/papers/42_phimdl_field/scripts/" \
      "norfleet_residual_hypothesis_results.json"
with open(out, "w") as fp:
    json.dump(results, fp, indent=1)
print(f"\nSaved {out.split('/')[-1]}")
signal.alarm(0)
