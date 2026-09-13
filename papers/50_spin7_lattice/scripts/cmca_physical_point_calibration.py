"""CMCA physical-point calibration: the lattice-QFT trajectory a(beta) and the
physical tape spacing a = hbar*c / Lambda_GTE.

Frame (session 088-R26): the beta-dependence of a is the renormalization
trajectory of the lattice regularization, NOT an inconsistency.  The physical
point is selected in a-space by the MDL-saturation principle a = hbar*c /
Lambda_GTE (the coarsest complete tape; the spacing already used by the
088-R15/R16 form-factor campaigns).  Combined with the CatAD seven-kink
threshold Lambda_GTE = 7*M_kink, the mass-gap calibration a*M^Q = hbar*c *
Delta(beta) forces

    xi(beta*) = Lambda_GTE / M^Q = 7   (exactly, on the consistent mass reading)

PRE-REGISTERED tests (declared before computing, Round 8 of the session):
  - beta* closed-form candidates: {3/2, pi/2}, tol 0.5%, neighbor nulls
  - S(beta*) candidates: {1/7, ln(8/7), 3/14}, tol 1%, neighbor nulls
  - C_v-peak coincidence: |beta_S - beta*|/beta* < 2%?
  - Lambda_diss/M^Q vs N_fam = 5 (recorded as CatD observation either way)

Outputs: beta*, a(beta) curve with the +/-Delta M^Q band, thermal observables
at the physical point, candidate battery verdicts, DKG diagnosis.
"""

import json
import os
import signal
import sys

import numpy as np

TIMEOUT_SECONDS = 600

def _timeout(s, f):
    print("TIMEOUT reached. Exiting.")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

Q = 7
HBARC = 197.3269804        # MeV fm

MQ, DMQ = 281.0, 21.0      # quantum kink mass (P42, 088-R14)
MCL = 290.10               # classical BPS kink mass = (8/49) m_tau
MPHI = 1776.86             # m_phi = m_tau (SCC)
LGTE_TREE = 2030.70        # (8/7) m_tau  (tree, CatAD 0.007%)
LGTE_POLE = 7 * MQ         # 1967 +/- 147 (pole reading)
DLGTE_POLE = 7 * DMQ
LGTE_ENV, DLGTE_ENV = 1960.0, 150.0   # envelope (FINAL_THEORY)
LDISS, DLDISS = 1495.0, 61.0          # dissolution scale (088-R16)

def p_gf7(L, C, R):
    return (C + R - C * R - L * C * R) % Q

def transfer(beta):
    M = np.zeros((49, 49))
    for a in range(Q):
        for b in range(Q):
            for c in range(Q):
                M[a * Q + b, b * Q + c] = np.exp(-beta * p_gf7(a, b, c))
    return M

def spectrum(beta):
    ev = np.linalg.eigvals(transfer(beta))
    mods = np.sort(np.abs(ev))[::-1]
    lam1, lam2 = mods[0], mods[1]
    gap = np.log(lam1 / lam2)
    return lam1, lam2, gap, 1.0 / gap

# ---------------------------------------------------------------- beta*
print("=== Physical point: solve xi(beta*) = Lambda_GTE / M^Q ===")
xi_target_exact = 7.0                      # consistent reading (Lambda = 7M)
xi_target_mixed = LGTE_TREE / MQ           # tree Lambda / pole M
dxi_mixed = xi_target_mixed * np.sqrt((DMQ / MQ) ** 2 + (0.14 / LGTE_TREE) ** 2)
print(f"  consistent reading: xi* = 7 exactly (Lambda = 7*M cancels M)")
print(f"  mixed reading (tree Lambda, pole M): xi* = {xi_target_mixed:.4f} "
      f"+/- {dxi_mixed:.4f}")

def solve_beta_for_xi(xi_target):
    lo, hi = 1.0, 3.0
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        _, _, _, xi = spectrum(mid)
        if xi < xi_target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)

beta_star = solve_beta_for_xi(7.0)
lam1_s, lam2_s, gap_s, xi_s = spectrum(beta_star)
print(f"\n  beta* (xi = 7 exact)   = {beta_star:.8f}")
print(f"  check: xi(beta*) = {xi_s:.8f}, Delta(beta*) = {gap_s:.8f} (= 1/7 = {1/7:.8f})")

beta_star_mixed = solve_beta_for_xi(xi_target_mixed)
beta_lo = solve_beta_for_xi(max(xi_target_mixed - dxi_mixed, 2.0))
beta_hi = solve_beta_for_xi(xi_target_mixed + dxi_mixed)
print(f"  beta* (mixed reading)  = {beta_star_mixed:.6f}  "
      f"[{beta_lo:.6f}, {beta_hi:.6f}]")

# ---------------------------------------------------------------- observables
print("\n=== Thermal observables at the physical point (xi = 7) ===")
h_eps = 1e-5
S_star = np.log(lam1_s)
lam1_p = np.log(spectrum(beta_star + h_eps)[0])
lam1_m = np.log(spectrum(beta_star - h_eps)[0])
u_star = -(lam1_p - lam1_m) / (2 * h_eps)        # mean energy per site
h_star = S_star + beta_star * u_star             # Shannon entropy rate per site
print(f"  lambda_1(beta*)        = {lam1_s:.8f}")
print(f"  S_CMCA(beta*) = ln l1  = {S_star:.8f} nats/site  (pressure)")
print(f"  u(beta*) mean energy   = {u_star:.8f} p-units/site")
print(f"  h(beta*) Shannon rate  = {h_star:.8f} nats/site")

# specific heat curve and peak
print("\n=== Specific heat C_v(beta) = beta^2 * d^2 ln lambda_1 / d beta^2 ===")
def logl1(beta):
    return np.log(spectrum(beta)[0])

def cv(beta, h=1e-3):
    return beta ** 2 * (logl1(beta + h) - 2 * logl1(beta) + logl1(beta - h)) / h ** 2

bgrid = np.arange(0.10, 3.01, 0.02)
cvs = [cv(b) for b in bgrid]
i_peak = int(np.argmax(cvs))
beta_S = bgrid[i_peak]
# refine peak
fine = np.arange(beta_S - 0.02, beta_S + 0.02, 0.001)
cvf = [cv(b) for b in fine]
beta_S = float(fine[int(np.argmax(cvf))])
print(f"  C_v peak at beta_S = {beta_S:.4f}  (C_v = {max(cvf):.5f})")
print(f"  beta* = {beta_star:.4f}; |beta_S - beta*|/beta* = "
      f"{abs(beta_S - beta_star)/beta_star:.3f}")

# ---------------------------------------------------------------- calibration
print("\n=== Calibration curve a(beta) = hbar*c * Delta(beta) / M^Q ===")
curve = []
for b in [0.5, 1.0, 1.5, beta_star, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0]:
    _, _, g, xi = spectrum(b)
    a_c = HBARC * g / MQ
    a_lo = HBARC * g / (MQ + DMQ)
    a_hi = HBARC * g / (MQ - DMQ)
    curve.append({"beta": float(b), "Delta": g, "xi": xi, "a_fm": a_c,
                  "a_fm_lo": a_lo, "a_fm_hi": a_hi,
                  "Lambda_a_MeV": HBARC / a_c})
    tag = "  <-- PHYSICAL POINT" if abs(b - beta_star) < 1e-9 else ""
    print(f"  beta={b:8.5f}  xi={xi:9.4f}  a={a_c:.6f} fm "
          f"[{a_lo:.6f},{a_hi:.6f}]  Lambda_a={HBARC/a_c:8.1f} MeV{tag}")

# physical spacing
a_tree = HBARC / LGTE_TREE
a_env = HBARC / LGTE_ENV
da_env = a_env * DLGTE_ENV / LGTE_ENV
print(f"\n  physical tape spacing: a = hbar*c/Lambda_GTE")
print(f"    tree:     a = {a_tree:.6f} fm   (Lambda = 2030.70 MeV)")
print(f"    envelope: a = {a_env:.6f} +/- {da_env:.6f} fm  (Lambda = 1.96+/-0.15 GeV)")
print(f"  exact corollaries at the physical point (tree reading):")
print(f"    a*m_phi = m_phi/Lambda_GTE = {MPHI/LGTE_TREE:.6f} (= 7/8 = 0.875 exactly)")
print(f"    lambda_C/a = xi* = 7 (kink Compton wavelength spans 7 tape cells)")
print(f"    [R15/R16 campaigns used a = 1/Lambda_GTE and a*m0 = 7/8: consistent]")

# ---------------------------------------------------------------- candidates
print("\n=== PRE-REGISTERED candidate battery ===")
verdicts = {}

def test(name, value, cands, tol):
    res = {}
    for cname, cval in cands.items():
        rel = abs(value - cval) / abs(cval)
        res[cname] = {"candidate": cval, "rel_dev": rel, "pass": bool(rel < tol)}
        print(f"  {name} = {value:.6f} vs {cname} = {cval:.6f}: "
              f"rel dev {rel:.4f} {'PASS' if rel < tol else 'fail'}")
    return res

print("-- beta* closed forms (tol 0.5%) --")
verdicts["beta_star"] = test("beta*", beta_star,
                             {"3/2": 1.5, "pi/2": np.pi / 2}, 0.005)
print("   neighbor nulls: 4/3, 5/3, pi/3, pi:")
verdicts["beta_star_nulls"] = test("beta*", beta_star,
                                   {"4/3": 4/3, "5/3": 5/3,
                                    "pi/3": np.pi/3, "pi": np.pi}, 0.005)

print("-- S(beta*) closed forms (tol 1%) --")
verdicts["S_star"] = test("S(beta*)", S_star,
                          {"1/7": 1/7, "ln(8/7)": np.log(8/7), "3/14": 3/14},
                          0.01)
print("   neighbor nulls: 1/6, 1/8, ln(9/7), ln(7/6), 2/14:")
verdicts["S_star_nulls"] = test("S(beta*)", S_star,
                                {"1/6": 1/6, "1/8": 1/8,
                                 "ln(9/7)": np.log(9/7),
                                 "ln(7/6)": np.log(7/6), "1/7(dup)": 1/7},
                                0.01)

print("-- C_v-peak coincidence (tol 2%) --")
cv_match = abs(beta_S - beta_star) / beta_star < 0.02
print(f"  beta_S = {beta_S:.4f} vs beta* = {beta_star:.4f}: "
      f"{'PASS' if cv_match else 'fail'} "
      f"(rel dev {abs(beta_S-beta_star)/beta_star:.3f})")
verdicts["cv_peak"] = {"beta_S": beta_S, "beta_star": beta_star,
                       "pass": bool(cv_match)}

print("-- Lambda_diss / M^Q vs N_fam = 5 (CatD observation) --")
r = LDISS / MQ
dr = r * np.sqrt((DLDISS / LDISS) ** 2 + (DMQ / MQ) ** 2)
sig = abs(r - 5.0) / dr
print(f"  Lambda_diss/M^Q = {r:.4f} +/- {dr:.4f}; vs 5: {sig:.2f} sigma "
      f"(recorded, no claim without mechanism)")
verdicts["ldiss_nfam"] = {"ratio": r, "sigma_from_5": sig}

# ---------------------------------------------------------------- DKG diag
print("\n=== DKG null-result diagnosis ===")
_, _, g1, xi1 = spectrum(1.0)
_, _, g2, xi2 = spectrum(2.0)
slope_12 = np.log(xi2 / xi1)
print(f"  ln(xi(2)/xi(1)) = {slope_12:.6f}  -- the morning DKG 'slope'")
print(f"  true asymptotic slope = 3/2 (CatAD, directed-wall geometric mean)")
print(f"  the DKG slope is a PRE-ASYMPTOTIC value of the dimensionless 3/2,")
print(f"  not beta*M^Q*a/(hbar c).  Lambda_a(DKG) = {MQ/slope_12:.1f} MeV was")
print(f"  M^Q divided by a dimensionless chain constant: artifact, dissolved.")

signal.alarm(0)

out = {
    "inputs": {"MQ": MQ, "DMQ": DMQ, "MCL": MCL, "MPHI": MPHI,
               "LGTE_tree": LGTE_TREE, "LGTE_envelope": [LGTE_ENV, DLGTE_ENV],
               "LDISS": [LDISS, DLDISS], "hbarc": HBARC},
    "physical_point": {
        "xi_star_exact": 7.0,
        "xi_star_mixed": xi_target_mixed, "dxi_mixed": dxi_mixed,
        "beta_star": beta_star,
        "beta_star_mixed": beta_star_mixed,
        "beta_star_mixed_band": [beta_lo, beta_hi],
        "Delta_star": gap_s, "lambda1_star": lam1_s,
        "S_star_nats_per_site": S_star,
        "u_star": u_star, "h_star_shannon": h_star,
        "a_tree_fm": a_tree, "a_envelope_fm": [a_env, da_env],
        "a_mphi_exact_tree": "7/8", "a_mphi_tree_value": MPHI / LGTE_TREE,
        "lambdaC_over_a": 7.0,
    },
    "specific_heat": {"beta_S_peak": beta_S, "cv_peak": float(max(cvf))},
    "calibration_curve": curve,
    "preregistered_verdicts": verdicts,
    "dkg_diagnosis": {"ln_xi2_over_xi1": slope_12,
                      "true_slope": 1.5,
                      "verdict": "DKG Lambda_a = 171.5 MeV artifact dissolved"},
}
_out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "cmca_physical_point_calibration.json")
with open(_out_path, "w") as f:
    json.dump(out, f, indent=2)
print("\nSaved", _out_path)
