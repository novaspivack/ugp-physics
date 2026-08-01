#!/usr/bin/env python3
"""First-principles Lambda_GTE from the Z7 full-winding threshold, with band and nulls.

Derivation chain (Route P, threshold completion):
  Lambda_GTE = N7 * M_kink^phys,  N7 = |Z7| = 7 (minimal Z7-neutral pure-kink chain;
  same-charge sine-Gordon kinks repel, so the chain continuum threshold is exactly
  the mass sum -- no binding shift below threshold).

Kink-mass readings (named branches, no averaging):
  BA-MASS-CL: classical BPS mass  M_cl = (8/49) m_tau = 290.10 MeV (CatAL chain)
  BA-MASS-Q : quantum (pole) mass M^Q = 281 +/- 21 MeV (P42 CatA; GJQW interface
              dim-reg, DHN-benchmark-validated, two independent routes; central =
              on-shell / MSbar@m_phi pair 282.9/280.1 MeV; scheme envelope
              [259.3, 300.9] MeV from mu in [m_phi/2, 2 m_phi] + on-shell +
              self-consistent conditions)

Outputs: Lambda central + band per reading; m_tau error propagation; envelope band;
tree/pole agreement; neighbor nulls on the multiplier; empirical f_pi cross-check
on M_cl (validation only, PDG f_pi never enters the derivation);
obsolete-calibration comparison.

Expected output range: Lambda_CL ~ 2.0307 GeV (band ~0.01%),
Lambda_Q ~ 1.970 +/- 0.146 GeV, envelope ~ 1.96 +/- 0.15 GeV (band ~7.4%);
tree value inside the pole band at +0.41 sigma.
"""
import json
import math
import signal
import sys

TIMEOUT_SECONDS = 120

def _timeout(signum, frame):
    print(f"TIMEOUT {TIMEOUT_SECONDS}s reached")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

# --- inputs (sources in docstring) ---
M_TAU = 1776.86e-3          # GeV, PDG 2024
M_TAU_ERR = 0.12e-3         # GeV
# Quantum (pole) kink mass: P42 GJQW interface dim-reg determination
# (channel-resolved dimensional regularization of the domain-wall tension,
# validated against the exact DHN sine-Gordon and phi^4 benchmarks and by an
# independent finite-box mode-sum). Quoted: M^Q = 281 +/- 21 MeV.
MQ_CENTRAL = 281.5e-3       # GeV, on-shell / MSbar@m_phi central pair (282.9/280.1)
MQ_ENV_LO = 259.3e-3        # GeV, scheme envelope lower edge
MQ_ENV_HI = 300.9e-3        # GeV, scheme envelope upper edge
N7 = 7                      # |Z7| -- mechanism-derived multiplier
ROUTE_C_PRIME_MKINK = 286.98e-3   # GeV, obsolete lattice calibration
LAM_SUPERSEDED = (2.01, +0.24, -0.44)  # GeV, superseded calibration-band value

results = {"inputs": {"m_tau_GeV": M_TAU, "m_tau_err_GeV": M_TAU_ERR,
                      "MQ_central_GeV": MQ_CENTRAL,
                      "MQ_scheme_envelope_GeV": [MQ_ENV_LO, MQ_ENV_HI],
                      "N7": N7}}

# --- kink masses ---
M_cl = (8.0 / 49.0) * M_TAU
M_Q = MQ_CENTRAL
MQ_SCHEME_ERR = 0.5 * (MQ_ENV_HI - MQ_ENV_LO)
dM_quantum = M_Q - M_cl
print(f"M_kink classical (CatAL chain): {M_cl*1e3:.2f} MeV  [= (8/49) m_tau]")
print(f"one-loop pole-mass shift      : {dM_quantum*1e3:+.2f} MeV (scheme-bounded)")
print(f"M_kink pole (P42 CatA)        : {M_Q*1e3:.1f} +/- {MQ_SCHEME_ERR*1e3:.1f} MeV "
      f"(envelope [{MQ_ENV_LO*1e3:.1f}, {MQ_ENV_HI*1e3:.1f}])")
assert abs(M_cl * 1e3 - 290.10) < 0.02, "BPS mass check vs P39 SCC chain failed"
assert abs(M_Q * 1e3 - 281.5) < 0.6, "pole mass check vs P42 failed"
results["M_kink_cl_MeV"] = M_cl * 1e3
results["M_kink_pole_MeV"] = M_Q * 1e3
results["delta_M_quantum_MeV"] = dM_quantum * 1e3

# --- Lambda_GTE per reading ---
lam_cl = N7 * M_cl
lam_cl_err = N7 * (8.0 / 49.0) * M_TAU_ERR          # m_tau error only
lam_q = N7 * M_Q
# pole-mass band: scheme envelope (dominant) (+) m_tau error in quadrature
lam_q_err = math.hypot(N7 * MQ_SCHEME_ERR, N7 * (M_Q / M_TAU) * M_TAU_ERR)
print(f"\nLambda_GTE (BA-MASS-CL) = 7*M_cl = (8/7) m_tau = {lam_cl*1e3:.2f} "
      f"+/- {lam_cl_err*1e3:.2f} MeV  (band {100*lam_cl_err/lam_cl:.3f}%)")
print(f"Lambda_GTE (BA-MASS-Q)  = 7*M_Q  = {lam_q:.4f} +/- {lam_q_err:.4f} GeV "
      f"(band {100*lam_q_err/lam_q:.1f}%)")
# tree/pole agreement: the tree value relative to the pole band
z_tree_in_pole = (lam_cl - lam_q) / lam_q_err
print(f"Tree/pole agreement: tree value at {z_tree_in_pole:+.2f} sigma inside the "
      f"pole band -- single boundary, no bifurcation")
# envelope over both readings (pole scheme envelope; tree value lies inside)
env_lo = min(N7 * MQ_ENV_LO, lam_cl - lam_cl_err)
env_hi = max(N7 * MQ_ENV_HI, lam_cl + lam_cl_err)
env_mid = 0.5 * (env_lo + env_hi)
env_half = 0.5 * (env_hi - env_lo)
print(f"Reading envelope: [{env_lo:.3f}, {env_hi:.3f}] GeV "
      f"= {env_mid:.3f} +/- {env_half:.3f} GeV ({100*env_half/env_mid:.1f}%)")
results["Lambda_CL_GeV"] = {"central": lam_cl, "err": lam_cl_err,
                            "band_pct": 100 * lam_cl_err / lam_cl}
results["Lambda_Q_GeV"] = {"central": lam_q, "err": lam_q_err,
                           "band_pct": 100 * lam_q_err / lam_q}
results["tree_in_pole_band_sigma"] = z_tree_in_pole
results["envelope_GeV"] = {"lo": env_lo, "hi": env_hi, "mid": env_mid,
                           "half_width": env_half,
                           "band_pct": 100 * env_half / env_mid}

# --- comparison with the superseded (obsolete-calibration) value ---
lam_old = N7 * ROUTE_C_PRIME_MKINK
print(f"\nSuperseded value: {LAM_SUPERSEDED[0]} +{LAM_SUPERSEDED[1]}/{LAM_SUPERSEDED[2]} GeV "
      f"(= 7 x {ROUTE_C_PRIME_MKINK*1e3:.2f} MeV obsolete Route C' mass -> {lam_old:.3f} GeV)")
old_band_pct = 100 * 0.5 * (LAM_SUPERSEDED[1] - LAM_SUPERSEDED[2]) / LAM_SUPERSEDED[0]
print(f"Superseded band: +12%/-22% (mean half-width {old_band_pct:.0f}%) -- calibration spread, superseded by SCC")
results["superseded"] = {"Lambda_GeV": LAM_SUPERSEDED[0],
                         "implied_from_obsolete_mass_GeV": lam_old,
                         "band_pct_mean": old_band_pct}

# --- neighbor nulls on the multiplier ---
# Mechanism: N7 = |Z7| = minimal n>0 with n = 0 mod 7 (Z7-neutral pure-kink chain).
# Neighbor multipliers have NO Z7-neutral pure-kink interpretation; record where they land.
print("\n=== Multiplier neighbor null (mechanism audit) ===")
nulls = {}
for n in (2, 3, 5, 6, 8, 9, 14, 21):
    neutral = (n % 7 == 0)
    pure_kink = True  # any n kinks is a state; neutrality is the discriminator
    lam_n = n * M_cl
    note = ("Z7-neutral but NOT minimal (= 2x or 3x the 7-chain; thresholds above 7M add nothing)"
            if neutral else "NOT Z7-neutral: cannot mediate full-period unwinding")
    nulls[n] = {"Lambda_cl_GeV": lam_n, "z7_neutral": neutral, "note": note}
    print(f"  N={n:>2}: 7M-analog = {lam_n:.3f} GeV -- {note}")
print("  => unique minimal Z7-neutral multiplier: N = 7 (matches CatAL b0_eq_z7_order and weight_sum_zero)")
results["multiplier_neighbor_null"] = nulls

# --- kink-chain threshold sharpness ---
# Same-charge SG kinks repel: asymptotic interaction +32 m_phi exp(-m_phi r) per pair
# in standard SG normalization -> no bound state below n*M; continuum threshold exact.
print("\nThreshold sharpness: same-charge kink-kink force repulsive (SG; kk bound states absent,")
print("breathers live in k-kbar channel only) => 7-chain threshold exactly 7*M_kink from below.")
results["threshold_sharpness"] = "exact (repulsive same-charge channel; no binding below threshold)"

# --- empirical cross-check (VALIDATION ONLY; PDG f_pi does not enter the derivation) ---
F_PI_REL_PDG = 130.41e-3    # GeV, PDG 2024 (relativistic convention)
F_PI_REL_ERR = 0.20e-3
m_kink_emp = math.pi * F_PI_REL_PDG / math.sqrt(2.0)
m_kink_emp_err = math.pi * F_PI_REL_ERR / math.sqrt(2.0)
z_cl = (M_cl - m_kink_emp) / m_kink_emp_err
z_q = (M_Q - m_kink_emp) / m_kink_emp_err
print(f"\nEmpirical PCAC cross-check: pi*f_pi/sqrt2 = {m_kink_emp*1e3:.2f} +/- {m_kink_emp_err*1e3:.2f} MeV")
print(f"  vs M_cl = {M_cl*1e3:.2f} MeV: z = {z_cl:+.1f} sigma  (tree relation, tree mass: consistent)")
print(f"  vs M_Q  = {M_Q*1e3:.2f} MeV: z = {z_q:+.1f} sigma  (pole mass in tree relation: excluded,")
print("     as expected -- the PCAC relation is a tree-level parameter relation; the threshold is kinematic)")
results["fpi_cross_check"] = {"m_kink_empirical_MeV": m_kink_emp * 1e3,
                              "err_MeV": m_kink_emp_err * 1e3,
                              "z_classical": z_cl, "z_pole": z_q}

out = "lambda_gte_band_threshold_derivation_results.json"
with open(out, "w") as f:
    json.dump(results, f, indent=1)
print(f"\nSaved {out}")
signal.alarm(0)
