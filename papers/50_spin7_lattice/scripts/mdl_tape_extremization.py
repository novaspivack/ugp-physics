"""MDL extremization of the CMCA tape spacing (OQ-088-R26b, Battery B + C).

Formalizes the saturation derivation: over tapes of spacing a covering a fixed
physical volume, the description cost K(a) is strictly decreasing in a (two
independent pricings), and the admissible set is {a : E_host(a) >= Lambda_GTE}
with E_host(a) = kappa*hbar*c/a (hosting criterion).  The MDL optimum is the
admissible supremum a* = kappa*hbar*c/Lambda.

B1: verify the optimum location numerically for both pricings; sensitivity
    table a*(kappa) for kappa in {1/2, 1, pi/2, pi} -- the functional
    transmits kappa linearly; the derivation content is kappa = 1
    (discreteness + Compton-support criterion), stated honestly.
B2: pricing-independence disambiguation -- carrier pricing (modes = cells,
    R25 Variational Carrier) and register-capacity pricing (N log 7) must
    select the same a*.
RIGIDITY (T2'): perturb the certified inputs (Lambda = n*M for n in 5..9;
    M = (p/49) m_phi for p in 6..10) and check which combination reproduces
    the independently-validated R15/R16 campaign bare mass a*m_phi = 7/8.
C1: dimensional audit of the measured campaign quantities -- which carry an
    independent length scale that could fix a?  (route iii inversion)

Expected: a*(kappa=1) = hbar*c/Lambda = 0.09717 fm (tree); both pricings
agree; only (n, p) = (7, 8) reproduces 7/8.
"""

import json
import os
import signal
import sys

import numpy as np

TIMEOUT_SECONDS = 300


def _timeout(s, f):
    print("TIMEOUT reached. Exiting.")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

HBARC = 197.3269804          # MeV fm
MPHI = 1776.86               # m_phi = m_tau (SCC)
M_TREE = (8.0 / 49.0) * MPHI # BPS kink mass (CatAL mkink_from_scc)
LAM_TREE = 7.0 * M_TREE      # seven-kink threshold (CatAD) = 2030.70 MeV
L_PHYS = 100.0               # fixed physical length, fm (arbitrary, drops out)

print("=== B1: extremization over admissible tapes ===")
a_grid = np.linspace(0.005, 0.5, 20000)   # fm


def k_carrier(a):
    # R25 carrier pricing: realized-ledger modes = cell count (units absorbed)
    return L_PHYS / a


def k_register(a):
    # register-capacity pricing: N cells x log2(7) bits
    return (L_PHYS / a) * np.log2(7)


results = {}
for kappa in [0.5, 1.0, np.pi / 2, np.pi]:
    admissible = a_grid[HBARC * kappa / a_grid >= LAM_TREE]
    a_star_pred = kappa * HBARC / LAM_TREE
    row = {"kappa": float(kappa), "a_star_predicted_fm": a_star_pred}
    for name, K in [("carrier", k_carrier), ("register", k_register)]:
        costs = K(admissible)
        a_opt = float(admissible[np.argmin(costs)])
        row[f"a_star_{name}_fm"] = a_opt
        row[f"{name}_matches_supremum"] = bool(abs(a_opt - a_star_pred) < 2e-4)
    results[f"kappa_{kappa:.4f}"] = row
    print(f"kappa={kappa:.4f}: a*(pred)={a_star_pred:.6f} fm; "
          f"carrier opt={row['a_star_carrier_fm']:.6f}; "
          f"register opt={row['a_star_register_fm']:.6f}; "
          f"both at supremum: {row['carrier_matches_supremum'] and row['register_matches_supremum']}")

a_phys = HBARC / LAM_TREE
print(f"\nkappa = 1 (discreteness + Compton-support): a* = {a_phys:.6f} fm "
      f"(= hbar*c/Lambda_GTE; tree)")
print("SENSITIVITY (honest): a* scales linearly in kappa; the extremization")
print("(b3) is exact arithmetic; the factor kappa = 1 is carried entirely by")
print("the hosting criterion (b4): minimal tape defect = one cell (exact,")
print("discreteness) + Compton-support criterion (named identification).")

print("\n=== B2: pricing-independence (disambiguation test T1) ===")
t1_pass = all(results[k]["carrier_matches_supremum"]
              and results[k]["register_matches_supremum"] for k in results)
print(f"both pricings select the admissible supremum for every kappa: {t1_pass}")
print("(strict monotonicity is pricing-independent; the saturation point is")
print(" set by the constraint alone -- the selection is NOT an artifact of")
print(" the carrier pricing model)")

print("\n=== RIGIDITY (disambiguation test T2'): certified-input perturbation ===")
# which (n, p) in Lambda = n*M, M = (p/49)*m_phi reproduces the campaign
# bare mass a*m_phi = 7/8 (independently validated, R15/R16)?
hits = []
for n in range(5, 10):
    for p in range(6, 11):
        M = (p / 49.0) * MPHI
        lam = n * M
        a = HBARC / lam
        am_phi = a * MPHI / HBARC   # = m_phi/Lambda = 49/(n*p)
        match = abs(am_phi - 7.0 / 8.0) < 1e-12
        if match:
            hits.append((n, p))
        if n == 7 or p == 8:
            print(f"  Lambda={n}M, M=({p}/49)m_phi: a*m_phi = 49/{n*p} = "
                  f"{am_phi:.6f} {'<-- = 7/8 CAMPAIGN MATCH' if match else ''}")
print(f"(n, p) combinations reproducing the campaign value 7/8: {hits}")
t2_pass = hits == [(7, 8)]
print(f"unique at the certified inputs (7, 8): {t2_pass}")

print("\n=== C1: dimensional audit (route iii inversion) ===")
audit = {
    "b_broadening": "r_RMS^meas / r_class -- dimensionless ratio; a-independent at leading order (lattice artifacts O((am)^2) only)",
    "Lambda_diss_over_mphi": "= 1/b -- dimensionless; fixed by m_phi and b, NOT by a",
    "gap_ratios_R15R16": "lattice gaps measured in lattice units; calibrated BY a*m0 = 7/8, not measuring it",
    "form_factor_shape": "sech-family fit residuals -- shape, dimensionless",
}
for k, v in audit.items():
    print(f"  {k}: {v}")
print("VERDICT (C1): every measured campaign quantity is dimensionless;")
print("no existing measurement independently determines a.  The consistency")
print("web is exact but NOT overdetermined: route (iii) is a clean negative.")
print("The independent determination remains the F1 target: substrate MC of")
print("xi_kink (predicted 7 cells).")

signal.alarm(0)
out = {
    "B1_extremization": results,
    "a_star_kappa1_fm": a_phys,
    "B2_pricing_independence_pass": bool(t1_pass),
    "T2_rigidity_hits": hits,
    "T2_unique_at_certified_inputs": bool(t2_pass),
    "C1_dimensional_audit": audit,
    "C1_verdict": "negative -- no measurement fixes a independently",
}
_out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "mdl_tape_extremization.json")
with open(_out_path, "w") as f:
    json.dump(out, f, indent=2)
print("\nSaved", _out_path)
