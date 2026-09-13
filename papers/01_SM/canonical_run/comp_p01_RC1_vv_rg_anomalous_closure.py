#!/usr/bin/env python3
"""
COMP-P01-RC1: VV RG-anomalous-dimension closure test.

SP-B of EPIC 13.  Reframed target from EPIC 7 Round 28:
  "Does the log-linear VV form Y_d = C * Y_u^(13/9) * Y_l^(-7/6) at EW scale
   arise from a GUT-scale linear Yukawa texture (SO(10) 10+126) under
   standard one-loop SM RG running?"

Method:
  - Choose three trial initial conditions at M_GUT = 2e16 GeV:
      (A) SO(10) 10+126 Georgi-Jarlskog pattern:
             Y_u_g = h_g + r_g
             Y_d_g = h_g - 3 r_g
             Y_l_g = h_g + 3 r_g
          with (h_g, r_g) solved to reproduce PDG Y_u and Y_l at M_Z
          after running DOWN; this is the "GUT linear" candidate
      (B) Minimal 10-only: Y_d = Y_u = Y_l at M_GUT (degenerate)
      (C) Null: random Yukawa pattern at M_GUT

  - Run one-loop SM Yukawa RG equations (Machacek-Vaughn-Jones) from
    M_GUT down to M_Z for all three sectors, per generation, with
    third-generation Yukawa self-coupling + gauge running

  - At M_Z, compute the "VV residual" per generation:
        log(Y_d_g) - [ (13/9) log(Y_u_g) + (-7/6) log(Y_l_g) + log(C) ]
    where C is the single best-fit constant across all 3 generations

  - Residual across 3 generations -> VV consistency metric

  - Null discipline: 50 random GUT-scale patterns; check what fraction
    of them produce VV residual comparable to scenario (A)

Gate A (success, VV is RG-consistent): scenario (A) residual <= 5% per gen
  AND null trials produce residual <= (A) in < 10% of cases
Gate B (partial): scenario (A) residual <= 20% per gen
Gate C: otherwise -- the Round-28 negative is upheld at one-loop level

NOTE: this is a one-loop test. Multi-week two-loop Mihaila-Salomon-Steinhauser
treatment is not attempted in this session.
"""

from __future__ import annotations
import hashlib
import json
import math
import os
import random
import sys
import time
import numpy as np
from scipy.integrate import solve_ivp


# ---------------------------------------------------------------------------
# SM one-loop running constants (Machacek-Vaughn + Buttazzo et al. 2013)
# ---------------------------------------------------------------------------

# Reference scales and PDG Yukawa values at M_Z (MSbar)
M_Z = 91.1876    # GeV
M_GUT = 2.0e16   # GeV
LN_RATIO = math.log(M_GUT / M_Z)

# PDG-central Yukawa couplings at M_Z (y_f = sqrt(2) m_f / v, v = 246.22 GeV)
PDG_Y_AT_MZ = {
    "u": 7.29e-6,    "c": 3.56e-3,    "t": 0.932,
    "d": 1.53e-5,    "s": 3.06e-4,    "b": 1.62e-2,
    "e": 2.77e-6,    "mu": 5.86e-4,   "tau": 1.00e-2,
}

# Gauge couplings at M_Z (MSbar)
G1_MZ = math.sqrt(5.0/3.0 * 4 * math.pi * 0.016923)  # hypercharge normalized
G2_MZ = math.sqrt(4 * math.pi * 0.033735)
G3_MZ = math.sqrt(4 * math.pi * 0.1179)  # alpha_s(M_Z)

# SM one-loop beta coefficients for gauge couplings (above m_t, 6-flavor)
# Standard values
B_G1 = 41.0 / 10.0
B_G2 = -19.0 / 6.0
B_G3 = -7.0

# ---------------------------------------------------------------------------
# Yukawa RG equations (one-loop, third-generation dominant; light flavors run)
# ---------------------------------------------------------------------------

def rge_rhs(t, y):
    """
    t = ln(mu) with mu = M_Z * exp(t); t=0 at M_Z, t=LN_RATIO at M_GUT.
    y = [y_u, y_c, y_t, y_d, y_s, y_b, y_e, y_mu, y_tau, g_1, g_2, g_3]
    Returns dy/dt at scale exp(t)*M_Z.
    """
    y_u, y_c, y_t, y_d, y_s, y_b, y_e, y_mu, y_tau, g1, g2, g3 = y
    t_trace = 3.0 * y_t**2 + 3.0 * y_b**2 + y_tau**2
    pi2 = 16.0 * math.pi**2

    # gauge-coupling running
    dg1 = B_G1 * g1**3 / pi2
    dg2 = B_G2 * g2**3 / pi2
    dg3 = B_G3 * g3**3 / pi2

    # up-type Yukawa -- only y_t affects the heavy limit; light quarks track t_trace
    def up_rge(yk):
        return yk * (t_trace + (3.0/2.0)*(yk**2) - (17.0/20.0)*g1**2 - (9.0/4.0)*g2**2 - 8.0*g3**2) / pi2

    def down_rge(yk):
        return yk * (t_trace + (3.0/2.0)*(yk**2) - (1.0/4.0)*g1**2 - (9.0/4.0)*g2**2 - 8.0*g3**2) / pi2

    def lep_rge(yk):
        return yk * (t_trace + (3.0/2.0)*(yk**2) - (9.0/4.0)*g1**2 - (9.0/4.0)*g2**2) / pi2

    dy_u   = up_rge(y_u)
    dy_c   = up_rge(y_c)
    dy_t   = up_rge(y_t)
    dy_d   = down_rge(y_d)
    dy_s   = down_rge(y_s)
    dy_b   = down_rge(y_b)
    dy_e   = lep_rge(y_e)
    dy_mu  = lep_rge(y_mu)
    dy_tau = lep_rge(y_tau)

    return [dy_u, dy_c, dy_t, dy_d, dy_s, dy_b, dy_e, dy_mu, dy_tau, dg1, dg2, dg3]


def run_up_to_gut(y0_at_mz):
    """Integrate from M_Z to M_GUT. y0 is state at t=0 (M_Z)."""
    sol = solve_ivp(rge_rhs, (0.0, LN_RATIO), y0_at_mz,
                    method="LSODA", rtol=1e-10, atol=1e-14, dense_output=False)
    if not sol.success:
        raise RuntimeError(f"RG-up integration failed: {sol.message}")
    return sol.y[:, -1]


def run_down_to_mz(y0_at_gut):
    """Integrate from M_GUT to M_Z. y0 is state at t=LN_RATIO."""
    sol = solve_ivp(rge_rhs, (LN_RATIO, 0.0), y0_at_gut,
                    method="LSODA", rtol=1e-10, atol=1e-14, dense_output=False)
    if not sol.success:
        raise RuntimeError(f"RG-down integration failed: {sol.message}")
    return sol.y[:, -1]


# ---------------------------------------------------------------------------
# VV residual metric
# ---------------------------------------------------------------------------

ALPHA_VV = 13.0 / 9.0
BETA_VV  = -7.0 / 6.0
GAMMA_VV = -5.0 / 14.0

def vv_residual(y_u_arr: np.ndarray, y_d_arr: np.ndarray, y_l_arr: np.ndarray):
    """Compute |log(y_d_g) - alpha_VV*log(y_u_g) - beta_VV*log(y_l_g) - log(C)|
    for g=0,1,2 with C = exp(best-fit intercept)."""
    lu = np.log(np.abs(y_u_arr))
    ld = np.log(np.abs(y_d_arr))
    ll = np.log(np.abs(y_l_arr))
    # predicted log(y_d) = alpha_VV * lu + beta_VV * ll + log_C
    # best-fit log_C is mean residual
    residuals_unfit = ld - (ALPHA_VV * lu + BETA_VV * ll)
    log_C = residuals_unfit.mean()
    residuals = residuals_unfit - log_C
    # return exp(residuals) - 1 as fractional error
    frac_err = np.exp(residuals) - 1.0
    return frac_err, log_C


# ---------------------------------------------------------------------------
# Initial-condition scenarios
# ---------------------------------------------------------------------------

def scenario_A_so10_gut():
    """
    SO(10) 10+126 Georgi-Jarlskog-style: Y_u_g = h_g + r_g, Y_d_g = h_g - 3 r_g,
    Y_l_g = h_g + 3 r_g. Solve (h_g, r_g) per generation to reproduce PDG Y_u and Y_l
    AT M_GUT after running up from M_Z.
    We start by running PDG Y_u and Y_l up to M_GUT via the full RG, then construct
    h_g, r_g at M_GUT, then predict Y_d at M_GUT, then run the FULL system down.
    """
    # Run PDG state up to M_GUT
    y0 = [PDG_Y_AT_MZ["u"], PDG_Y_AT_MZ["c"], PDG_Y_AT_MZ["t"],
          PDG_Y_AT_MZ["d"], PDG_Y_AT_MZ["s"], PDG_Y_AT_MZ["b"],
          PDG_Y_AT_MZ["e"], PDG_Y_AT_MZ["mu"], PDG_Y_AT_MZ["tau"],
          G1_MZ, G2_MZ, G3_MZ]
    state_gut = run_up_to_gut(y0)
    yu_gut = state_gut[0:3].copy()
    yl_gut = state_gut[6:9].copy()
    # Solve (h_g, r_g) from Y_u_g = h + r and Y_l_g = h + 3 r
    # => r_g = (Y_l_g - Y_u_g)/2, h_g = Y_u_g - r_g
    r_gut = (yl_gut - yu_gut) / 2.0
    h_gut = yu_gut - r_gut
    # Construct GUT Y_d from the SO(10) 10+126 relation
    yd_gut_from_so10 = h_gut - 3.0 * r_gut
    # Run the full state down from M_GUT with SO(10)-predicted Y_d
    state_gut_so10 = state_gut.copy()
    state_gut_so10[3:6] = yd_gut_from_so10
    state_mz = run_down_to_mz(state_gut_so10)
    return state_mz, state_gut_so10


def scenario_B_10_only():
    """Minimal 10-only SO(10): Y_d_g = Y_u_g = Y_l_g at M_GUT.
    Use Y_u PDG as the common GUT anchor and propagate."""
    # Run PDG state up to M_GUT
    y0 = [PDG_Y_AT_MZ["u"], PDG_Y_AT_MZ["c"], PDG_Y_AT_MZ["t"],
          PDG_Y_AT_MZ["d"], PDG_Y_AT_MZ["s"], PDG_Y_AT_MZ["b"],
          PDG_Y_AT_MZ["e"], PDG_Y_AT_MZ["mu"], PDG_Y_AT_MZ["tau"],
          G1_MZ, G2_MZ, G3_MZ]
    state_gut = run_up_to_gut(y0)
    yu_gut = state_gut[0:3].copy()
    state_gut_10only = state_gut.copy()
    state_gut_10only[3:6] = yu_gut  # Y_d = Y_u at GUT
    state_gut_10only[6:9] = yu_gut  # Y_l = Y_u at GUT
    state_mz = run_down_to_mz(state_gut_10only)
    return state_mz, state_gut_10only


def scenario_null_random(rng: random.Random):
    """Random Yukawa pattern at M_GUT: each Yukawa is PDG_Y_GUT * exp(random Gaussian)."""
    # Run PDG state up to M_GUT (to get realistic gauge couplings at GUT)
    y0 = [PDG_Y_AT_MZ["u"], PDG_Y_AT_MZ["c"], PDG_Y_AT_MZ["t"],
          PDG_Y_AT_MZ["d"], PDG_Y_AT_MZ["s"], PDG_Y_AT_MZ["b"],
          PDG_Y_AT_MZ["e"], PDG_Y_AT_MZ["mu"], PDG_Y_AT_MZ["tau"],
          G1_MZ, G2_MZ, G3_MZ]
    state_gut = run_up_to_gut(y0)
    # Perturb Yukawas randomly (log-Gaussian with std 0.5)
    state_rnd = state_gut.copy()
    for i in range(9):
        state_rnd[i] *= math.exp(rng.gauss(0.0, 0.5))
    state_mz = run_down_to_mz(state_rnd)
    return state_mz, state_rnd


def source_sha256() -> str:
    with open(__file__, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def main() -> int:
    t0 = time.time()
    precommit_sha = source_sha256()
    n_null = 50

    results = {
        "experiment_id": "COMP-P01-RC1-VV",
        "title": "VV RG-anomalous-dimension closure test (one-loop SM)",
        "epic": "EPIC_CLUSTER13_REFEREE_CLOSURE / SP-B",
        "pre_commit_sha256": precommit_sha,
        "config": {
            "M_GUT_GeV": M_GUT,
            "M_Z_GeV": M_Z,
            "alpha_VV_target": ALPHA_VV,
            "beta_VV_target": BETA_VV,
            "gamma_VV_target": GAMMA_VV,
            "n_null": n_null,
            "loop_order": 1,
            "note": "Third-generation dominant Machacek-Vaughn one-loop; "
                    "SM flavor-diagonal running above m_t (6-flavor); no threshold matching at m_t "
                    "(tree-level matching only). Two-loop + Mihaila threshold not attempted in this session.",
        },
    }

    # --- PDG control (verification that RG integrator is working) ---
    print(f"[{time.time()-t0:.1f}s] Control run: PDG at M_Z roundtrip...", file=sys.stderr)
    y0_pdg = [PDG_Y_AT_MZ["u"], PDG_Y_AT_MZ["c"], PDG_Y_AT_MZ["t"],
              PDG_Y_AT_MZ["d"], PDG_Y_AT_MZ["s"], PDG_Y_AT_MZ["b"],
              PDG_Y_AT_MZ["e"], PDG_Y_AT_MZ["mu"], PDG_Y_AT_MZ["tau"],
              G1_MZ, G2_MZ, G3_MZ]
    pdg_at_gut = run_up_to_gut(y0_pdg)
    pdg_roundtrip = run_down_to_mz(pdg_at_gut)
    roundtrip_err = [abs(pdg_roundtrip[i] - y0_pdg[i]) / abs(y0_pdg[i]) for i in range(12)]
    results["pdg_roundtrip_max_rel_err"] = float(max(roundtrip_err))
    # Also VV residual at PDG state itself
    pdg_frac_err, pdg_log_C = vv_residual(np.array(y0_pdg[0:3]), np.array(y0_pdg[3:6]), np.array(y0_pdg[6:9]))
    results["pdg_at_mz_vv_fractional_residual"] = [float(x) for x in pdg_frac_err]
    results["pdg_at_mz_vv_log_C"] = float(pdg_log_C)

    # --- Scenario A: SO(10) 10+126 ---
    print(f"[{time.time()-t0:.1f}s] Scenario A: SO(10) 10+126...", file=sys.stderr)
    state_mz_A, state_gut_A = scenario_A_so10_gut()
    frac_err_A, log_C_A = vv_residual(state_mz_A[0:3], state_mz_A[3:6], state_mz_A[6:9])
    results["scenario_A_SO10"] = {
        "Y_u_at_MZ": state_mz_A[0:3].tolist(),
        "Y_d_at_MZ": state_mz_A[3:6].tolist(),
        "Y_l_at_MZ": state_mz_A[6:9].tolist(),
        "Y_d_at_MGUT_SO10_input": state_gut_A[3:6].tolist(),
        "vv_fractional_residual_per_gen": [float(x) for x in frac_err_A],
        "vv_best_fit_log_C": float(log_C_A),
        "vv_max_frac_err_pct": float(100 * np.max(np.abs(frac_err_A))),
    }

    # --- Scenario B: 10-only degenerate ---
    print(f"[{time.time()-t0:.1f}s] Scenario B: 10-only degenerate...", file=sys.stderr)
    state_mz_B, state_gut_B = scenario_B_10_only()
    frac_err_B, log_C_B = vv_residual(state_mz_B[0:3], state_mz_B[3:6], state_mz_B[6:9])
    results["scenario_B_10only"] = {
        "Y_u_at_MZ": state_mz_B[0:3].tolist(),
        "Y_d_at_MZ": state_mz_B[3:6].tolist(),
        "Y_l_at_MZ": state_mz_B[6:9].tolist(),
        "vv_fractional_residual_per_gen": [float(x) for x in frac_err_B],
        "vv_max_frac_err_pct": float(100 * np.max(np.abs(frac_err_B))),
    }

    # --- Null distribution ---
    print(f"[{time.time()-t0:.1f}s] Null trials ({n_null})...", file=sys.stderr)
    rng = random.Random(20260423)
    null_max_frac = []
    for k in range(n_null):
        state_mz_n, _ = scenario_null_random(rng)
        frac_err_n, _ = vv_residual(state_mz_n[0:3], state_mz_n[3:6], state_mz_n[6:9])
        null_max_frac.append(float(100 * np.max(np.abs(frac_err_n))))
        if (k+1) % 10 == 0:
            print(f"[{time.time()-t0:.1f}s]   null {k+1}/{n_null}", file=sys.stderr)
    null_max_frac.sort()
    null_median = null_max_frac[len(null_max_frac)//2]
    ugp_resid_A = results["scenario_A_SO10"]["vv_max_frac_err_pct"]
    null_better_count = sum(1 for v in null_max_frac if v <= ugp_resid_A)
    results["null"] = {
        "n_trials": n_null,
        "max_frac_err_percentiles": {
            "min": null_max_frac[0],
            "median": null_median,
            "90th": null_max_frac[int(0.9 * n_null)],
            "max": null_max_frac[-1],
        },
        "scenario_A_max_frac_err_pct": ugp_resid_A,
        "null_better_than_scenario_A_fraction": null_better_count / n_null,
    }

    # --- Gate ---
    if ugp_resid_A <= 5.0 and results["null"]["null_better_than_scenario_A_fraction"] < 0.10:
        gate = "A"
    elif ugp_resid_A <= 20.0:
        gate = "B"
    else:
        gate = "C"
    results["gate"] = gate
    results["runtime_seconds"] = time.time() - t0

    tmp = json.dumps(results, sort_keys=True, default=str).encode("utf-8")
    results["post_commit_sha256"] = hashlib.sha256(tmp).hexdigest()

    out_path = os.path.join(os.path.dirname(__file__), "comp_p01_RC1_vv_rg_anomalous_closure.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"[{time.time()-t0:.1f}s] Wrote {out_path}", file=sys.stderr)

    print(json.dumps({
        "pre_commit_sha256": precommit_sha,
        "post_commit_sha256": results["post_commit_sha256"],
        "gate": gate,
        "scenario_A_max_frac_err_pct": ugp_resid_A,
        "scenario_B_max_frac_err_pct": results["scenario_B_10only"]["vv_max_frac_err_pct"],
        "pdg_at_mz_vv_max_frac_err_pct": float(100 * np.max(np.abs(pdg_frac_err))),
        "null_median_frac_err_pct": null_median,
        "null_better_than_scenario_A_fraction": results["null"]["null_better_than_scenario_A_fraction"],
        "pdg_roundtrip_max_rel_err": results["pdg_roundtrip_max_rel_err"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
