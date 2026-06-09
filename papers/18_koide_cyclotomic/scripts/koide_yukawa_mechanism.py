#!/usr/bin/env python3
"""
080-KOIDE-YUKAWA: Generation-labeled Yukawa coupling from Phi_MDL orbit amplitudes.

Question: Is the charged-lepton Koide cone

    sqrt(m_g) = M * (1 + sqrt(2) * cos(theta + 2*pi*g/3)),   theta = 2/9,  g in {0,1,2}

derivable from a Phi_MDL generation-space Yukawa coupling, where the three
generations are the three Z3-orbit positions (a-values {1, 9, 5}) of the shared
w = 4 kink condensate?

Strategy (after the KOIDE-DYNAMICAL three-tape Hessian no-go):
  T0  Canonical IMT sanity check (UGP_GTE_SM_Verifier.py) -- reproduce e/mu/tau.
  T1  Koide cone amplitudes kappa_g = 1 + sqrt(2) cos(theta + 2*pi*g/3); Koide Q;
      mass ratios m_g ~ kappa_g^2; test all g->{e,mu,tau} assignments and powers.
      Also test the (mistaken) theta = 2*pi/9 to confirm theta = 2/9 is the value.
  T2  a-values {1,9,5} from N_c=3; the 2*a_tau = a_e + a_mu identity; the Z3-Fourier
      (irrep) decomposition of the generation Yukawa: trivial(1D) + standard(2D).
  T3  Where does the cone amplitude sqrt(2) come from? Test equal-norm-per-irrep
      vs. equipartition-per-mode; confirm sqrt(2) is the Q=2/3 cone condition and is
      theta-independent. Test whether the a-values directly encode kappa_g.

Output range: Koide Q for the cone amplitudes must equal 2/3 = 0.6667 exactly
(it is the cone by construction); m_mu/m_e from theta=2/9 must reproduce 206.77.

Saves JSON artifact alongside. Wall-clock timeout 120s.
"""

import json
import math
import os
import pathlib
import signal
import sys
import itertools

TIMEOUT_SECONDS = 120


def _timeout_handler(signum, frame):
    print(f"\nTIMEOUT: wall-clock limit {TIMEOUT_SECONDS}s reached.")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

SQRT2 = math.sqrt(2.0)
THETA_NC = 2.0 / 9.0          # P18 Koide phase = (N_c^2 - 1)/(4 N_c^2), N_c = 3
PDG = {"e": 0.51099895000, "mu": 105.6583755, "tau": 1776.86}  # MeV

results = {"task": "080-KOIDE-YUKAWA", "theta_Nc": THETA_NC}


# ---------------------------------------------------------------------------
# T0 -- canonical IMT sanity check
# ---------------------------------------------------------------------------
def t0_imt_sanity():
    out = {"status": "not_run", "rows": []}
    verifier = str(pathlib.Path(__file__).parents[2] / "01_SM" / "canonical_run")
    sys.path.insert(0, verifier)
    try:
        import UGP_GTE_SM_Verifier as mod
    except Exception as e:  # noqa: BLE001
        out["status"] = f"import_failed: {e}"
        return out
    triples = {
        "electron": dict(n_value=73, generation=1, particle_type="lepton", a=1, c=823),
        "muon":     dict(n_value=42, generation=2, particle_type="lepton", a=9, c=1023),
        "tau":      dict(n_value=275, generation=3, particle_type="lepton", a=5, c=-65535),
    }
    targets = {"electron": 0.5109989461, "muon": 105.6583745, "tau": 1776.86}
    max_err = 0.0
    for name, kw in triples.items():
        r = mod.calculate_particle_mass_verifier(particle_name=name, **kw)
        m = float(r.get("mass_mev", 0.0))
        tgt = targets[name]
        err = abs(m - tgt) / tgt * 100.0
        max_err = max(max_err, err)
        out["rows"].append({"name": name, "mass_mev": m, "pdg": tgt, "err_pct": err})
    out["max_err_pct"] = max_err
    out["status"] = "PASS" if max_err < 1.0 else "FAIL"
    return out


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def cone_amplitudes(theta, amp=SQRT2):
    """kappa_g = 1 + amp*cos(theta + 2 pi g / 3), g = 0,1,2."""
    return [1.0 + amp * math.cos(theta + 2.0 * math.pi * g / 3.0) for g in range(3)]


def koide_Q(sqrt_m):
    s = sum(sqrt_m)
    n = sum(x * x for x in sqrt_m)
    return n / (s * s)


# ---------------------------------------------------------------------------
# T1 -- cone amplitudes, Koide Q, mass-ratio assignment
# ---------------------------------------------------------------------------
def t1_cone():
    out = {}
    kappa = cone_amplitudes(THETA_NC)            # the sqrt(m) cone values (up to scale M)
    out["kappa_g (theta=2/9)"] = kappa
    out["koide_Q_on_kappa"] = koide_Q(kappa)     # must be 2/3 by construction
    # masses ~ kappa^2 ; ratios
    masses = [k * k for k in kappa]
    out["kappa_sq (mass ~)"] = masses

    # PDG sqrt-mass vector and its empirical Koide Q + phase
    sm = {k: math.sqrt(v) for k, v in PDG.items()}
    out["koide_Q_PDG"] = koide_Q([sm["e"], sm["mu"], sm["tau"]])

    # Try every assignment of g in {0,1,2} to {e,mu,tau}; mass ~ kappa^power.
    best = None
    for perm in itertools.permutations(range(3)):
        kap = [kappa[perm[i]] for i in range(3)]   # order: e, mu, tau
        for power in (2.0, 1.0):
            mvals = [k ** power for k in kap]
            if min(abs(x) for x in mvals) < 1e-12:
                continue
            mnorm = [x / mvals[0] for x in mvals]            # normalise to electron
            pdgnorm = [PDG["e"] / PDG["e"], PDG["mu"] / PDG["e"], PDG["tau"] / PDG["e"]]
            rel = [abs(mnorm[i] - pdgnorm[i]) / pdgnorm[i] for i in range(3)]
            score = max(rel)
            cand = {"perm": perm, "power": power, "mnorm": mnorm,
                    "pdgnorm": pdgnorm, "max_rel": score}
            if best is None or score < best["max_rel"]:
                best = cand
    out["best_assignment"] = best

    # Direct zero-parameter ratios from theta=2/9 with the standard Koide assignment
    # (Foot convention: g=0->tau, g=1->e, g=2->mu reproduces ascending order with M anchor)
    # m_g ~ kappa_g^2 ; use the assignment that gives ascending masses
    order = sorted(range(3), key=lambda g: kappa[g] ** 2)   # ascending kappa^2
    sm_sorted = [kappa[g] ** 2 for g in order]
    out["ascending_mass_order_g"] = order
    out["m_mu_over_m_e_pred"] = sm_sorted[1] / sm_sorted[0]
    out["m_tau_over_m_mu_pred"] = sm_sorted[2] / sm_sorted[1]
    out["m_mu_over_m_e_PDG"] = PDG["mu"] / PDG["e"]
    out["m_tau_over_m_mu_PDG"] = PDG["tau"] / PDG["mu"]
    out["m_mu_over_m_e_err_pct"] = abs(out["m_mu_over_m_e_pred"] - out["m_mu_over_m_e_PDG"]) / out["m_mu_over_m_e_PDG"] * 100

    # confirm the prompt's theta=2*pi/9 is WRONG
    kappa_wrong = cone_amplitudes(2.0 * math.pi / 9.0)
    masses_wrong = sorted([k * k for k in kappa_wrong])
    out["theta_2pi9_kappa"] = kappa_wrong
    out["theta_2pi9_m_mu_over_m_e"] = (masses_wrong[1] / masses_wrong[0]) if masses_wrong[0] > 1e-12 else None
    return out


# ---------------------------------------------------------------------------
# T2 -- a-values, N_c, irrep (Z3-Fourier) decomposition
# ---------------------------------------------------------------------------
def t2_avalues_irrep():
    out = {}
    N_c = 3
    a = {"e": 1, "mu": N_c**2, "tau": (N_c**2 + 1) // 2}     # {1, 9, 5}
    out["a_values"] = a
    out["2*a_tau"] = 2 * a["tau"]
    out["a_e + a_mu"] = a["e"] + a["mu"]
    out["arith_mean_identity_holds"] = (2 * a["tau"] == a["e"] + a["mu"])

    # Z3-Fourier (S3 irrep) decomposition of the cone sqrt-mass vector.
    kappa = cone_amplitudes(THETA_NC)
    # trivial (democratic) component: projection on (1,1,1)/sqrt3
    e_hat = [1 / math.sqrt(3)] * 3
    proj_triv = sum(kappa[i] * e_hat[i] for i in range(3))   # scalar
    v_triv = [proj_triv * e_hat[i] for i in range(3)]
    v_std = [kappa[i] - v_triv[i] for i in range(3)]
    norm_triv = math.sqrt(sum(x * x for x in v_triv))
    norm_std = math.sqrt(sum(x * x for x in v_std))
    out["norm_trivial_irrep"] = norm_triv
    out["norm_standard_irrep"] = norm_std
    out["std_over_triv_ratio"] = norm_std / norm_triv
    out["equal_norm (Koide cone)"] = abs(norm_std - norm_triv) < 1e-9
    out["note"] = ("Koide Q=2/3 <=> equal-norm of 1D trivial and 2D standard S3 irreps "
                   "of the generation sqrt-mass vector. The cone amplitude sqrt(2) is "
                   "exactly what equalizes the irrep norms.")
    return out


# ---------------------------------------------------------------------------
# T3 -- where does sqrt(2) come from? cone is theta-independent
# ---------------------------------------------------------------------------
def t3_amplitude_origin():
    out = {}
    # Scan amplitude b in sqrt(m_g)=1 + b cos(theta+2pi g/3); find b giving Q=2/3.
    # Analytic: trivial norm^2 = 3, standard norm^2 = (3/2) b^2; equal => b^2=2 => b=sqrt2.
    out["analytic_b_for_cone"] = SQRT2
    out["sqrt_dim_standard_rep"] = math.sqrt(2.0)   # standard rep is 2-dimensional
    # numerically confirm Q=2/3 holds for amp=sqrt2 at SEVERAL thetas (theta-independence)
    rows = []
    for theta in (0.0, THETA_NC, 0.5, 1.0, math.pi / 4):
        kap = cone_amplitudes(theta, amp=SQRT2)
        if min(kap) <= 0:   # need positive sqrt-masses for physical Q
            rows.append({"theta": theta, "Q": None, "note": "non-physical (neg amplitude)"})
        else:
            rows.append({"theta": theta, "Q": koide_Q(kap)})
    out["Q_vs_theta_at_amp_sqrt2"] = rows
    # confirm a wrong amplitude breaks Q=2/3
    out["Q_at_amp_1.0_theta_2_9"] = koide_Q([1 + 1.0 * math.cos(THETA_NC + 2 * math.pi * g / 3) for g in range(3)])
    out["Q_at_amp_1.5_theta_2_9"] = koide_Q([1 + 1.5 * math.cos(THETA_NC + 2 * math.pi * g / 3) for g in range(3)])

    # Does the discrete a-value vector {1,9,5} sit on the Koide cone? (Should NOT;
    # the a-values are the discrete L1 shadow, not the continuous sqrt-masses.)
    a_vec = [1.0, 9.0, 5.0]
    out["koide_Q_on_a_values"] = koide_Q([math.sqrt(x) for x in a_vec])  # if a~m
    out["koide_Q_on_sqrt_a_as_sqrtm"] = koide_Q(a_vec)                   # if a~sqrt(m)
    out["conclusion"] = ("sqrt(2) is the equal-norm (Q=2/3) cone amplitude, INDEPENDENT "
                         "of theta. theta=2/9 (CatAL, N_c=3) only selects the point on the "
                         "cone. The a-values do NOT directly lie on the cone; they are the "
                         "discrete Z3-orbit labels whose arithmetic-mean identity 2a_tau="
                         "a_e+a_mu is the a-component shadow of the equal-norm condition.")
    return out


def main():
    results["T0_IMT_sanity"] = t0_imt_sanity()
    results["T1_cone"] = t1_cone()
    results["T2_avalues_irrep"] = t2_avalues_irrep()
    results["T3_amplitude_origin"] = t3_amplitude_origin()

    signal.alarm(0)

    here = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(here, "koide_yukawa_mechanism_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)

    # ---- console summary ----
    print("=" * 70)
    print("080-KOIDE-YUKAWA: generation Yukawa from Phi_MDL orbit amplitudes")
    print("=" * 70)
    t0 = results["T0_IMT_sanity"]
    print(f"\n[T0] IMT sanity: {t0['status']}  (max_err {t0.get('max_err_pct', float('nan')):.4f}%)")
    for r in t0["rows"]:
        print(f"     {r['name']:9s} {r['mass_mev']:12.5f} MeV  PDG {r['pdg']:12.5f}  err {r['err_pct']:.4f}%")

    t1 = results["T1_cone"]
    print(f"\n[T1] kappa_g (theta=2/9)        : {[round(x,4) for x in t1['kappa_g (theta=2/9)']]}")
    print(f"     Koide Q on kappa (cone)     : {t1['koide_Q_on_kappa']:.6f}  (target 2/3=0.666667)")
    print(f"     Koide Q on PDG sqrt-masses  : {t1['koide_Q_PDG']:.6f}")
    print(f"     m_mu/m_e  pred / PDG        : {t1['m_mu_over_m_e_pred']:.3f} / {t1['m_mu_over_m_e_PDG']:.3f}  ({t1['m_mu_over_m_e_err_pct']:.4f}%)")
    print(f"     m_tau/m_mu pred / PDG       : {t1['m_tau_over_m_mu_pred']:.3f} / {t1['m_tau_over_m_mu_PDG']:.3f}")
    print(f"     best fit  (perm,power,err)  : {t1['best_assignment']['perm']}, {t1['best_assignment']['power']}, {t1['best_assignment']['max_rel']:.4f}")
    print(f"     theta=2pi/9 (WRONG) m_mu/m_e: {t1['theta_2pi9_m_mu_over_m_e']}")

    t2 = results["T2_avalues_irrep"]
    print(f"\n[T2] a-values {t2['a_values']}  2a_tau={t2['2*a_tau']} a_e+a_mu={t2['a_e + a_mu']}  id={t2['arith_mean_identity_holds']}")
    print(f"     trivial-irrep norm          : {t2['norm_trivial_irrep']:.5f}")
    print(f"     standard-irrep norm         : {t2['norm_standard_irrep']:.5f}")
    print(f"     std/triv ratio              : {t2['std_over_triv_ratio']:.6f}  (equal-norm={t2['equal_norm (Koide cone)']})")

    t3 = results["T3_amplitude_origin"]
    print(f"\n[T3] analytic cone amplitude b  : {t3['analytic_b_for_cone']:.6f} = sqrt(dim standard rep)={t3['sqrt_dim_standard_rep']:.6f}")
    print(f"     Q vs theta at amp=sqrt2     :")
    for row in t3["Q_vs_theta_at_amp_sqrt2"]:
        print(f"        theta={row['theta']:.4f}  Q={row['Q']}")
    print(f"     Q at amp=1.0 (theta=2/9)    : {t3['Q_at_amp_1.0_theta_2_9']:.6f}  (breaks cone)")
    print(f"     Q at amp=1.5 (theta=2/9)    : {t3['Q_at_amp_1.5_theta_2_9']:.6f}  (breaks cone)")

    print(f"\nJSON: {out_path}")


if __name__ == "__main__":
    main()
