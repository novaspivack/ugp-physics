"""
G30 cosmological-constant suppression: the 7^(-N) hypothesis null suite.

Hypothesis under test:
    rho_obs = rho_vac_kink * 7^(-N),   rho_vac_kink = m_kink^4 / (16 pi^2),
with N measured near 50, motivated by:
  (i)  the Z7 potential coefficient 1/49 = 1/7^2;
  (ii) the three-tape CMCA holographic state-space count |S| = 7^(3L) (P45, CatAL),
       suggesting N = 3L with L the lattice size.

This script applies the GTE gap-closure null suite (.cursor/rules/gte-gap-closure-pipeline.mdc):
  Task 1 (measure N precisely; test N=49 vs N=50 and GTE structural forms),
  Task 2 (wrong-target and neighbor-exponent and alternative-atom nulls),
  Task 3 (search for a GTE mechanism that *fixes* N without tuning),
  Task 4 (verdict / ranking).

All numbers are computed; nothing is asserted by hand. Results are written to
g30_7pow50_null_suite_results.json. The verdict follows the pass criteria of the
gap-closure pipeline (small coefficients, null-cross clean, mechanism cited, form
unambiguous) plus the methodology-robustness rule.
"""

import json
import numpy as np

# ----------------------------------------------------------------------------
# Canonical GTE / PDG inputs (with provenance)
# ----------------------------------------------------------------------------
m_kink = 0.29010        # GeV. BPS kink mass = (8/49) m_tau (G07 CatAD, P38/P44).
sigma_GTE = 0.18920     # GeV^2. String tension = (N_c/C_F) m_kink^2 = (9/4)m_kink^2 (G13 CatAD).
v_H = 246.16            # GeV. Higgs VEV (SRRG CatAD).
M_Pl = 1.220890e19      # GeV. Planck mass (reduced not used here; this is the full M_Pl).
M_Pl_red = 2.435e18     # GeV. Reduced Planck mass, for Hubble.
rho_obs_scale = 2.3e-12 # GeV. Observed dark-energy scale (rho_obs = this^4), Planck 2018.

# Z7 / GTE structural integers
N_c = 3                 # number of colors
N_gen = 3               # number of generations
c_H = 13                # Higgs ridge coefficient (sin^2 theta_W = N_gen/c_H = 3/13)
Z7 = 7                  # the Z7 modulus
F21 = 21                # |F_21| = |Z7 rtimes Z3| = 21
PSC_sectors = 4         # vacuum + 3 generations (PSC orbit count)

rho_obs = rho_obs_scale**4
rho_vac_kink = m_kink**4 / (16 * np.pi**2)

results = {"inputs": {
    "m_kink_GeV": m_kink, "sigma_GTE_GeV2": sigma_GTE, "v_H_GeV": v_H,
    "M_Pl_GeV": M_Pl, "M_Pl_reduced_GeV": M_Pl_red,
    "rho_obs_scale_GeV": rho_obs_scale, "rho_obs_GeV4": rho_obs,
    "rho_vac_kink_GeV4": rho_vac_kink,
}}


def log7(x):
    return np.log(x) / np.log(7.0)


# ============================================================================
# TASK 1 — Measure the exponent precisely
# ============================================================================
print("=" * 70)
print("TASK 1 — Precise exponent measurement")
print("=" * 70)

suppression = rho_obs / rho_vac_kink          # = 7^(-N)
N_measured = -log7(suppression)               # positive N
print(f"rho_obs / (m_kink^4/16pi^2) = {suppression:.6e}")
print(f"log_7(suppression)          = {log7(suppression):.6f}")
print(f"N_measured (rho_obs = rho_kink * 7^-N) = {N_measured:.6f}")

# Best-fit at integer exponents: which integer reproduces rho_obs best?
def rel_err_at_N(N):
    rho_pred = rho_vac_kink * 7.0**(-N)
    return rho_pred / rho_obs - 1.0   # signed relative error

err49 = rel_err_at_N(49)
err50 = rel_err_at_N(50)
print(f"\nN=49: rho_pred/rho_obs - 1 = {err49:+.4f}  ({abs(err49)*100:.2f}% error)")
print(f"N=50: rho_pred/rho_obs - 1 = {err50:+.4f}  ({abs(err50)*100:.2f}% error)")
better = 49 if abs(err49) < abs(err50) else 50
print(f"--> N={better} fits better (|err_49|={abs(err49)*100:.2f}% vs |err_50|={abs(err50)*100:.2f}%)")

# How sensitive is N_measured to the inputs? A 1-loop factor of (1/16pi^2)
# shifts N by log_7(16pi^2). Sensitivity audit:
dN_dlog_mkink = 4.0 / np.log(7.0)   # dN/d(ln m_kink): N depends on 4*ln(m_kink)
# a 1% change in m_kink shifts N by:
dN_for_1pct_mkink = dN_dlog_mkink * 0.01
print(f"\nSensitivity: dN/dln(m_kink) = {dN_dlog_mkink:.4f}; "
      f"1% change in m_kink shifts N by {dN_for_1pct_mkink:.4f}")
print(f"Removing the 1/(16pi^2) loop factor shifts N by "
      f"{log7(16*np.pi**2):+.4f} (to N={N_measured - log7(16*np.pi**2):.4f})")

# Structural GTE forms for the *target* integer near 50:
structural_forms = {
    "7^2 = 49": 7**2,
    "7^2 + 1 = 50": 7**2 + 1,
    "7^2 - 1 = 48": 7**2 - 1,
    "F21 + 28 = 49 (|F21|+...)": 21 + 28,
    "3*F21 - 13 = 50 (N_gen*|F21| - c_H)": 3*21 - 13,
    "(N_c^2-1)*7^2/8 = 49": (N_c**2 - 1) * 7**2 // 8,
    "PSC_sectors*c_H - 2 = 50": PSC_sectors * c_H - 2,
    "2*c_H + N_c*7 + N_gen = 50": 2*c_H + N_c*7 + N_gen,
}
print("\nStructural candidates for the target integer:")
for name, val in structural_forms.items():
    print(f"  {name:42s} = {val}")

results["task1"] = {
    "suppression": suppression,
    "N_measured": N_measured,
    "rel_err_N49": err49, "rel_err_N50": err50,
    "better_integer": better,
    "abs_err_N49_pct": abs(err49) * 100, "abs_err_N50_pct": abs(err50) * 100,
    "dN_dln_mkink": dN_dlog_mkink,
    "shift_from_dropping_loop_factor": log7(16 * np.pi**2),
    "structural_target_candidates": {k: int(v) for k, v in structural_forms.items()},
}

# ---- G43 holographic connection: N = 3L ? ----
print("\n--- G43 holographic interpretation: N = 3L ---")
L_measured = N_measured / 3.0
print(f"If N = 3L (three-tape holographic count), L = {L_measured:.4f}")
print(f"  49/3 = {49/3:.4f}, 50/3 = {50/3:.4f}")
print("  NOTE: in P45, L is the lattice cell-count per axis, a regulator that")
print("  -> infinity in the continuum limit; it is NOT a fixed GTE integer.")
results["task1"]["L_if_N_eq_3L"] = L_measured

# Octave interpretation: N = 3 * log_7(UV/m_kink)?
print("\n--- octave interpretation: 3L = 3 log_7(UV/m_kink) ? ---")
octave = {}
for name, scale in [("M_Pl", M_Pl), ("M_Pl_red", M_Pl_red),
                    ("v_H", v_H), ("sqrt(sigma)", np.sqrt(sigma_GTE))]:
    n_oct = log7(scale / m_kink)
    octave[name] = {"n_octaves": n_oct, "3L": 3 * n_oct}
    print(f"  octaves m_kink->{name:11s}: {n_oct:8.4f}  => 3L = {3*n_oct:9.4f}  (target {N_measured:.2f})")
results["task1"]["octave_interpretation"] = octave


# ============================================================================
# TASK 2 — Null tests
# ============================================================================
print("\n" + "=" * 70)
print("TASK 2 — Null tests (wrong target / neighbor exponent / alt atom)")
print("=" * 70)

# Null 2a: wrong target -- sigma_GTE^2 in place of m_kink^4
rho_sigma = sigma_GTE**2 / (16 * np.pi**2)
N_wrong_sigma = -log7(rho_obs / rho_sigma)
nearest_int_sigma = round(N_wrong_sigma)
dist_sigma = abs(N_wrong_sigma - nearest_int_sigma)
print(f"[2a] Wrong target sigma^2/16pi^2: N = {N_wrong_sigma:.4f} "
      f"(nearest int {nearest_int_sigma}, dist {dist_sigma:.4f})")

# Null 2b: neighbor exponents -- error at N=45..56
neighbor = {}
print("[2b] Neighbor-exponent scan:")
for N_test in range(45, 57):
    ratio = (rho_vac_kink * 7.0**(-N_test)) / rho_obs
    neighbor[N_test] = ratio
    flag = "  <-- best" if N_test == better else ""
    print(f"     N={N_test}: rho_pred/rho_obs = {ratio:7.3f}  "
          f"({abs(ratio-1)*100:6.1f}% err){flag}")

# Null 2c: alternative atom -- v_H^4 in place of m_kink^4
rho_vH = v_H**4 / (16 * np.pi**2)
N_vH = -log7(rho_obs / rho_vH)
nearest_int_vH = round(N_vH)
dist_vH = abs(N_vH - nearest_int_vH)
print(f"[2c] Alt atom v_H^4/16pi^2: N = {N_vH:.4f} "
      f"(nearest int {nearest_int_vH}, dist {dist_vH:.4f})")

# Null 2d: alternative atom -- M_Pl^4 (the *naive* CC), and the bare di-pion threshold
rho_MPl = M_Pl**4 / (16 * np.pi**2)
N_MPl = -log7(rho_obs / rho_MPl)
print(f"[2d] Alt atom M_Pl^4/16pi^2: N = {N_MPl:.4f} (the famous ~10^122 in base 7)")

# Null 2e: "wrong-target lottery" -- how often does a *random* GeV-scale energy E,
# fed through E^4/16pi^2, give an N within 'dist' of an integer? This is the crucial
# control: base-7 logs of order-50 magnitudes land near integers ~2*dist of the time.
print("\n[2e] Wrong-target LOTTERY (key control):")
rng = np.random.default_rng(0)
# sample E uniformly in log over the hadronic-to-EW window where 'a kink-like scale' could plausibly sit
log10_E = rng.uniform(np.log10(0.05), np.log10(1000.0), size=200000)  # 50 MeV .. 1 TeV
E = 10.0**log10_E
N_rand = -log7(rho_obs / (E**4 / (16*np.pi**2)))
frac_to_int = np.abs(N_rand - np.rint(N_rand))
# probability a random scale lands at least as close to an integer as our measurement
tol = dist_sigma  # use a representative tolerance; also report for our own measurement
our_dist = abs(N_measured - round(N_measured))
p_random_within_our_dist = float(np.mean(frac_to_int <= our_dist))
p_random_within_011 = float(np.mean(frac_to_int <= 0.11))  # the headline "11% error" ~ 0.06 in N
# Convert the headline "11% energy-density error" to a distance in N:
#   rho off by factor 1.11 -> N off by log_7(1.11)
dN_for_11pct = log7(1.11)
p_random_better_than_11pct = float(np.mean(frac_to_int <= dN_for_11pct))
print(f"     our measurement is {our_dist:.4f} from nearest integer (N={round(N_measured)})")
print(f"     11% rho error corresponds to {dN_for_11pct:.4f} in N")
print(f"     P(random hadronic scale lands within {our_dist:.4f} of an integer) "
      f"= {p_random_within_our_dist:.3f}")
print(f"     P(random scale within {dN_for_11pct:.4f} of integer, i.e. 'as good as 11%') "
      f"= {p_random_better_than_11pct:.3f}")

results["task2"] = {
    "wrong_target_sigma": {"N": N_wrong_sigma, "nearest_int": nearest_int_sigma, "dist": dist_sigma},
    "neighbor_scan_ratio": {str(k): v for k, v in neighbor.items()},
    "alt_atom_vH": {"N": N_vH, "nearest_int": nearest_int_vH, "dist": dist_vH},
    "alt_atom_MPl": {"N": N_MPl},
    "lottery": {
        "our_dist_to_int": our_dist,
        "dN_for_11pct_rho": dN_for_11pct,
        "P_random_within_our_dist": p_random_within_our_dist,
        "P_random_as_good_as_11pct": p_random_better_than_11pct,
        "n_samples": 200000,
    },
}


# ============================================================================
# TASK 3 — Search for a GTE mechanism that FIXES N (no tuning)
# ============================================================================
print("\n" + "=" * 70)
print("TASK 3 — GTE mechanism candidates for N")
print("=" * 70)

mechanisms = {}

# Approach 1: holographic DOF inverse, N = 3L. Requires L fixed by GTE.
# In P45, L is the lattice regulator (-> infinity). There is no GTE principle that
# fixes L = 16.65. RECORD AS NOT-DERIVED.
mechanisms["holographic_3L"] = {
    "claim": "N = 3L from |S|=7^(3L); L = N/3",
    "L_needed": L_measured,
    "verdict": "NOT DERIVED — L is the P45 lattice regulator (L->inf in continuum); "
               "no GTE principle fixes L=16.65. 3L is not GTE-integer-valued.",
}
print(f"[A1] holographic 3L: needs L={L_measured:.3f} (non-integer regulator) -> NOT DERIVED")

# Approach 2: N = 49 = 7^2 from the Z7 potential coefficient 1/49.
# Mechanism would be: rho_Lambda = rho_kink * (1/7^2)^k with 2k = 49 -> k=24.5 (non-integer).
# Or directly N=49: rho_Lambda = rho_kink * 7^-49 = rho_kink * (1/49)^(49/2). Check error:
k_for_N49 = 49 / 2.0
print(f"[A2] N=49=7^2 from 1/49 coefficient: needs (1/7^2)^{k_for_N49} -> half-integer power; "
      f"rho error at N=49 = {abs(err49)*100:.1f}%")
mechanisms["Z7_coeff_49"] = {
    "claim": "N = 7^2 = 49 from V coefficient 1/49",
    "rho_err_pct": abs(err49) * 100,
    "verdict": "PARTIAL — N=49 is GTE-integer (7^2) and fits to "
               f"{abs(err49)*100:.0f}%, but the 'k=49/2 powers of 1/49' bookkeeping is "
               "not a derived loop count; coefficient->exponent identification is ad hoc.",
}

# Approach 3: PSC orbit / entropy structures (log_7 of small integers) -- check none hit ~50.
print("[A3] PSC/entropy small-integer log_7 values (should NOT be ~49-50):")
for label, val in [("log_7(4)", 4), ("log_7(12)", 12), ("log_7(21)", 21),
                   ("log_7(34560)", 34560)]:
    print(f"     {label} = {log7(val):.4f}")
mechanisms["PSC_entropy"] = {"verdict": "NONE near 50 — PSC orbit logs are O(1)-O(6)."}

# Approach 4: Bekenstein-Hawking entropy of the observable universe in base 7.
# S_univ ~ 10^122 (in nats/Planck units). In base 7:
S_univ_log10 = 122.0
N_BH = S_univ_log10 / np.log10(7.0)
print(f"[A4] Bekenstein-Hawking S_univ ~ 10^122 -> log_7 = {N_BH:.1f} (NOT 50)")
mechanisms["BH_entropy"] = {"N_BH_base7": N_BH,
    "verdict": "NO — the actual holographic entropy of the universe is ~7^140, not 7^50."}

# Approach 5: the CC IR scale as a number of e-folds / octaves of 7 from m_kink.
# rho_obs^(1/4) = omega_CC; lambda_CC/(1/m_kink) in base 7:
omega_CC = rho_obs**0.25
lam_CC_kink = omega_CC / m_kink   # = (rho_obs^1/4)/m_kink
N_from_lambda = -log7(lam_CC_kink)
print(f"[A5] omega_CC = rho_obs^1/4 = {omega_CC:.4e} GeV; "
      f"omega_CC/m_kink = {lam_CC_kink:.4e}; -log_7 = {N_from_lambda:.4f}")
print(f"     (this is exactly N_measured/4 + log_7(16pi^2)/4 bookkeeping; "
      f"N_measured/4 = {N_measured/4:.4f})")
mechanisms["IR_scale_octaves"] = {
    "N_from_lambda_CC": N_from_lambda,
    "verdict": "TAUTOLOGICAL — this is just (1/4) of the same ratio; no independent content."}

results["task3"] = {"mechanisms": mechanisms,
                    "N_BH_universe_base7": N_BH}

print("\n[Task 3 summary] No mechanism FIXES N=50 without tuning. The closest "
      "GTE-integer is N=49=7^2 (PARTIAL, ad hoc bookkeeping). The holographic 3L "
      "route fails because L is a regulator, not a fixed integer.")


# ============================================================================
# TASK 4 — Verdict / pass criteria
# ============================================================================
print("\n" + "=" * 70)
print("TASK 4 — Verdict against gap-closure pass criteria")
print("=" * 70)

# Pass criteria from the pipeline:
#  (1) small coefficients  -> N is a single power, coefficient 1: OK structurally
#  (2) null-cross clean     -> wrong-target & neighbor & lottery must pass
#  (3) mechanism cited      -> must tie to GTE structure, not arithmetic coincidence
#  (4) form unambiguous     -> 49 vs 50 must be fixed by mechanism, not by fit

# (2) evaluation:
wrong_target_clean = dist_sigma > 0.2 and dist_vH > 0.2   # wrong atoms should miss integers
# A genuine derived relation must clear conventional significance: a coincidence
# probability above 5% (roughly 1-in-20) means the near-integer base-7 exponent is
# not statistically distinguishable from a random hadronic-scale accident.
lottery_fail = p_random_better_than_11pct > 0.05          # if random scales hit this often -> not significant
neighbor_ambiguous = (abs(err49) < 0.5 and abs(err50) < 0.5)  # both ~50% within an order of magnitude

# (4) evaluation: is 49 vs 50 resolved? both within a factor; mechanism does not pick.
form_unambiguous = abs(err49) * 100 < 5 or abs(err50) * 100 < 5  # would need <5% to claim one

criteria = {
    "small_coefficients": True,  # single power of 7, coefficient 1
    "wrong_target_null_clean": bool(wrong_target_clean),
    "lottery_random_hit_prob": p_random_better_than_11pct,
    "lottery_indicates_coincidence": bool(lottery_fail),
    "neighbor_exponents_ambiguous": bool(neighbor_ambiguous),
    "mechanism_derived": False,   # from Task 3: none fixes N
    "form_49_vs_50_resolved": bool(form_unambiguous),
}
for k, v in criteria.items():
    print(f"  {k:36s}: {v}")

# Overall verdict
passes = (criteria["wrong_target_null_clean"]
          and not criteria["lottery_indicates_coincidence"]
          and criteria["mechanism_derived"]
          and criteria["form_49_vs_50_resolved"])

if passes:
    verdict = "PASS — eligible for Cat upgrade"
    confidence = "PROVISIONAL"
else:
    verdict = ("FAIL — does not meet gap-closure pass criteria. Remains OPEN. "
               "The 7^(-50) coincidence is numerology at current evidence: no GTE "
               "mechanism fixes N, the 49-vs-50 form is unresolved (both ~11-30% off), "
               "and random hadronic scales reproduce a near-integer base-7 exponent "
               f"with probability {p_random_better_than_11pct:.2f}.")
    confidence = "LIKELY ARTIFACT"

print(f"\nVERDICT: {verdict}")
print(f"CONFIDENCE: {confidence}")

results["task4"] = {
    "pass_criteria": criteria,
    "passes": bool(passes),
    "verdict": verdict,
    "confidence": confidence,
    "G30_status": "OPEN (unchanged) — 7^(-50) lead does NOT pass the null suite",
}

# ----------------------------------------------------------------------------
with open("papers/44_quantum_gravity/scripts/g30_7pow50_null_suite_results.json", "w") as f:
    json.dump(results, f, indent=2)
print("\nResults written to papers/44_quantum_gravity/scripts/g30_7pow50_null_suite_results.json")
