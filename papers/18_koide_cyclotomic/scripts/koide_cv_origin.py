#!/usr/bin/env python3
"""
080-KOIDE-EQUALNORM (Session 2): the ORIGIN of CV(sqrt m) = 1.

The Koide relation Q = 2/3 is exactly the statement that the charged-lepton
sqrt-mass spectrum has coefficient of variation CV(sqrt m) = 1 (std dev = mean),
equivalently the trivial (democratic) and standard (generation-splitting) S3
irreps carry equal L2 norm (cone amplitude b = sqrt 2).  This module pushes on
WHY CV = 1, testing the three proposed mechanisms and a new information-theoretic
reformulation.  It does NOT fabricate a derivation: every PASS/FAIL is reported.

TASKS
  T0    Sanity (MANDATORY, per understand-code-before-using): reproduce the known
        Koide CV(sqrt m_lepton) = 1 and Q = 2/3 from PDG masses.
  T1    Prompt hypothesis A_g^2 proportional to a_g (a-values {1,9,5}):
        does m_g proportional to a_g give CV(sqrt m)=1 and Koide Q=2/3?
  T2    Algebraic structure of {1,9,5}: arithmetic/geometric/harmonic means;
        the discrete identity 2 a_tau = a_e + a_mu; is there a clean CV=1?
  T3    Mass-generation models against (i) Koide Q=2/3, (ii) CV=1, (iii) the
        ACTUAL lepton mass ratios:
          Model 1  M_g = M0 * exp(lam * a_g)         (exponential in orbit pos.)
          Model 2  M_g proportional to a_g           (linear)
          Model 3  M_g proportional to a_g^alpha     (power law; scan alpha)
        Report which (if any) reproduces CV=1, and whether it also matches data.
  T_pr  NEW reformulation: Koide Q = inverse participation ratio of the
        normalized sqrt-mass vector p_g = sqrt(m_g)/sum(sqrt m).  Q = sum p_g^2
        (Simpson / Renyi-2 index).  Koide Q=2/3 <=> participation ratio
        PR = 1/Q = 3/2 = N_gen/2 (half the generations participate).
        PR = 3/(1 + CV^2); CV=1 <=> PR=3/2.  Phase-independent.
  T_max MaxEnt / MDL: CV=1 is the maximum-entropy-at-fixed-mean (exponential)
        signature; the 1-bit equipartition over the two S3 irrep TYPES gives
        b=sqrt2 exactly, while naive description-length minimization gives the
        WRONG democratic b=0.  Disclose the MDL/MaxEnt dual distinction.

JSON artifact saved alongside.  Wall-clock timeout 120s.
"""

import json
import math
import os
import signal
import sys

TIMEOUT_SECONDS = 120


def _timeout_handler(signum, frame):
    print(f"\nTIMEOUT: wall-clock limit {TIMEOUT_SECONDS}s reached.")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

# PDG charged-lepton masses (MeV)
M_E, M_MU, M_TAU = 0.51099895, 105.6583755, 1776.86
A_VALUES = [1, 9, 5]            # generation a-values from N_c=3: a_e, a_mu, a_tau
THETA_NC = 2.0 / 9.0           # Koide phase (radians), from N_c=3 (CatAL, P18)
SQRT2 = math.sqrt(2.0)

results = {"task": "080-KOIDE-EQUALNORM-Session2", "theta_Nc": THETA_NC}


# ---- helpers ---------------------------------------------------------------
def cv2(v):
    """Population coefficient of variation squared: Var/mean^2."""
    m = sum(v) / len(v)
    var = sum((x - m) ** 2 for x in v) / len(v)
    return var / (m * m)


def koide_Q_from_mass(masses):
    """Q = (sum m) / (sum sqrt m)^2."""
    sm = [math.sqrt(x) for x in masses]
    return sum(masses) / (sum(sm) ** 2)


def koide_Q_from_sqrt(v):
    """Q with v = sqrt-mass amplitudes: Q = (sum v^2)/(sum v)^2."""
    return sum(x * x for x in v) / (sum(v) ** 2)


def cone(theta, b=SQRT2, A=1.0):
    return [A * (1.0 + b * math.cos(theta + 2.0 * math.pi * g / 3.0)) for g in range(3)]


# ---------------------------------------------------------------------------
# T0 -- sanity: the known Koide CV=1 from PDG masses
# ---------------------------------------------------------------------------
def t0():
    out = {}
    masses = [M_E, M_MU, M_TAU]
    sm = [math.sqrt(x) for x in masses]
    out["sqrt_masses_MeV^0.5"] = sm
    out["CV_sqrt_m"] = math.sqrt(cv2(sm))
    out["CV2_sqrt_m"] = cv2(sm)
    out["Koide_Q"] = koide_Q_from_mass(masses)
    out["pass_CV1"] = abs(math.sqrt(cv2(sm)) - 1.0) < 1e-4
    out["pass_Q23"] = abs(koide_Q_from_mass(masses) - 2.0 / 3.0) < 1e-4
    out["verdict"] = ("SANITY PASS: PDG charged-lepton sqrt-masses have CV=1 and "
                      "Koide Q=2/3 (the known relation). This is the target CV=1.")
    return out


# ---------------------------------------------------------------------------
# T1 -- prompt hypothesis  A_g^2 proportional to a_g  (m_g proportional to a_g)
# ---------------------------------------------------------------------------
def t1():
    out = {}
    a = A_VALUES
    sa = [math.sqrt(x) for x in a]           # sqrt-mass amplitudes if m ~ a
    out["a_values"] = a
    out["sqrt_a"] = sa
    out["CV2_sqrt_a"] = cv2(sa)
    out["CV_sqrt_a"] = math.sqrt(cv2(sa))
    out["Koide_Q_if_m_prop_a"] = koide_Q_from_mass(a)   # = sum a /(sum sqrt a)^2
    out["pass_CV1"] = abs(math.sqrt(cv2(sa)) - 1.0) < 1e-3
    out["pass_Q23"] = abs(koide_Q_from_mass(a) - 2.0 / 3.0) < 1e-3
    out["verdict"] = (
        "NO. m_g proportional to a_g={1,9,5} gives Koide Q="
        f"{koide_Q_from_mass(a):.4f} (need 0.6667) and CV(sqrt m)="
        f"{math.sqrt(cv2(sa)):.4f} (need 1.0). The hypothesis A_g^2 ~ a_g FAILS "
        "both conditions. The raw orbit labels are not the sqrt-mass amplitudes; "
        "this is the continuum form of the mechanism-(c) negative.")
    return out


# ---------------------------------------------------------------------------
# T2 -- algebraic structure of {1,9,5}
# ---------------------------------------------------------------------------
def t2():
    out = {}
    a = A_VALUES
    out["arithmetic_mean"] = sum(a) / 3
    out["geometric_mean"] = (a[0] * a[1] * a[2]) ** (1.0 / 3.0)
    out["harmonic_mean"] = 3.0 / sum(1.0 / x for x in a)
    out["2*a_tau"] = 2 * a[2]
    out["a_e + a_mu"] = a[0] + a[1]
    out["arithmetic_mean_identity_holds"] = (2 * a[2] == a[0] + a[1])
    out["sum_a"] = sum(a)
    out["prod_a"] = a[0] * a[1] * a[2]
    out["sum_sq_a"] = sum(x * x for x in a)
    # equal-mode condition on a-values: 2(sum a)^2 = 3 sum a^2 ?
    out["2*(sum a)^2"] = 2 * sum(a) ** 2
    out["3*sum a^2"] = 3 * sum(x * x for x in a)
    out["a_values_equal_modes?"] = (2 * sum(a) ** 2 == 3 * sum(x * x for x in a))
    out["CV2_of_a_values"] = cv2([float(x) for x in a])
    out["verdict"] = (
        "The a-values carry ONE shadow of the cone: the arithmetic-mean identity "
        "2*a_tau = a_e + a_mu = 10 (holds). They do NOT carry the equal-variance / "
        "equal-mode condition (2*225=450 != 321=3*107), so CV(sqrt-of-a) != 1. No "
        "function of {1,9,5} alone (arithmetic/geometric/harmonic means) yields the "
        "continuum CV=1; the equal-norm lives in the continuum sqrt-mass amplitudes.")
    return out


# ---------------------------------------------------------------------------
# T3 -- mass-generation models vs (Koide, CV=1, ACTUAL masses)
# ---------------------------------------------------------------------------
def _bisect_for_cv1(f, lo, hi, tol=1e-12, itmax=200):
    """Find x in [lo,hi] with CV(model(x))=1, i.e. cv2-1 root, if a sign change exists."""
    flo = f(lo) - 1.0
    fhi = f(hi) - 1.0
    if flo * fhi > 0:
        return None
    for _ in range(itmax):
        mid = 0.5 * (lo + hi)
        fm = f(mid) - 1.0
        if abs(fm) < tol:
            return mid
        if flo * fm < 0:
            hi = mid
        else:
            lo, flo = mid, fm
    return 0.5 * (lo + hi)


def t3():
    out = {}
    a = A_VALUES
    data_masses = [M_E, M_MU, M_TAU]
    # We must compare model masses to data masses by ORBIT assignment.
    # Lab-note assignment: g=0->tau(a=1? ) -- but a-values index e,mu,tau as {1,9,5}.
    # Use the a-value ordering directly: model gives m(a_e),m(a_mu),m(a_tau).
    data_by_orbit = {1: M_E, 9: M_MU, 5: M_TAU}  # a_e=1->e, a_mu=9->mu, a_tau=5->tau

    # Model 1: M_g = M0 exp(lam a_g).  CV(sqrt m) as function of lam.
    def cv_model1(lam):
        sm = [math.exp(0.5 * lam * x) for x in a]   # sqrt(M) ~ exp(lam a/2); M0 cancels in CV
        return math.sqrt(cv2(sm))
    # scan lam for CV=1
    lam_cv1 = _bisect_for_cv1(cv_model1, 1e-6, 5.0)
    m1 = {"description": "M_g = M0 exp(lam a_g)"}
    if lam_cv1 is not None:
        m1["lam_for_CV1"] = lam_cv1
        sm = [math.exp(0.5 * lam_cv1 * x) for x in a]
        masses = [s * s for s in sm]
        m1["Koide_Q_at_CV1"] = koide_Q_from_sqrt(sm)
        # does the orbit ordering match the data ordering?
        order_model = sorted(range(3), key=lambda i: masses[i])
        order_data = sorted(range(3), key=lambda i: [data_by_orbit[a[i]] for i in range(3)][i])
        m1["model_mass_order_by_orbit(a)"] = [a[i] for i in order_model]
        m1["data_mass_order_by_orbit(a)"] = [a[i] for i in order_data]
        m1["orbit_ordering_matches_data"] = (order_model == order_data)
        m1["note"] = ("exp(lam a) orders masses by a-value (1<5<9 -> e<tau<mu) which does "
                      "NOT match data ordering e<mu<tau; even forcing CV=1 by tuning lam, "
                      "the model cannot reproduce the real mass hierarchy.")
    else:
        m1["lam_for_CV1"] = None
        m1["note"] = "no lam in (0,5] gives CV=1"
    out["model1_exponential"] = m1

    # Model 2: M_g ~ a_g (linear) -- already T1; record Q and CV.
    sa = [math.sqrt(x) for x in a]
    out["model2_linear"] = {
        "description": "M_g proportional to a_g",
        "Koide_Q": koide_Q_from_mass(a),
        "CV_sqrt_m": math.sqrt(cv2(sa)),
        "matches_data": False,
        "note": "Q=0.386 != 2/3; CV=0.396 != 1; mass ratios 1:9:5 != data 1:207:3477.",
    }

    # Model 3: M_g ~ a_g^alpha (power law).  Scan alpha for Koide Q=2/3 and for CV=1.
    def Q_model3(alpha):
        masses = [x ** alpha for x in a]
        sm = [math.sqrt(x) for x in masses]
        return koide_Q_from_sqrt(sm)
    def cv_model3(alpha):
        masses = [x ** alpha for x in a]
        sm = [math.sqrt(x) for x in masses]
        return math.sqrt(cv2(sm))
    # find alpha with Koide Q=2/3 (Q increases from 1/3 at alpha=0 toward 1)
    def Qroot(alpha):
        return Q_model3(alpha) - 2.0 / 3.0
    alpha_Q23 = None
    lo, hi = 0.01, 20.0
    if Qroot(lo) * Qroot(hi) < 0:
        for _ in range(200):
            mid = 0.5 * (lo + hi)
            if Qroot(lo) * Qroot(mid) < 0:
                hi = mid
            else:
                lo = mid
        alpha_Q23 = 0.5 * (lo + hi)
    m3 = {"description": "M_g proportional to a_g^alpha (scan alpha)"}
    if alpha_Q23 is not None:
        m3["alpha_for_Q23"] = alpha_Q23
        m3["CV_at_alpha_Q23"] = cv_model3(alpha_Q23)
        masses = [x ** alpha_Q23 for x in a]
        m3["mass_ratios_at_Q23"] = [x / min(masses) for x in masses]
        m3["data_mass_ratios"] = [m / M_E for m in (M_E, M_MU, M_TAU)]
        m3["matches_data"] = False
        m3["note"] = ("an alpha exists that forces Koide Q=2/3 (hence CV=1), but it is a "
                      "FIT to one number, and the resulting mass ratios do NOT match the "
                      "real lepton hierarchy. So power-law-in-a is not the mechanism.")
    out["model3_powerlaw"] = m3

    out["verdict"] = (
        "No a_g-based mass-generation model reproduces BOTH CV=1 and the real lepton "
        "masses without fitting. Exponential mis-orders the generations; linear gives "
        "Q=0.386; power-law can be tuned to Q=2/3 but then fails the mass ratios. "
        "CV=1 is a property of the continuum cone (theta=2/9, b=sqrt2), not of any "
        "simple closed form in the discrete orbit labels.")
    return out


# ---------------------------------------------------------------------------
# T_pr -- participation-ratio (Simpson/Renyi-2) reformulation
# ---------------------------------------------------------------------------
def t_pr():
    out = {}
    masses = [M_E, M_MU, M_TAU]
    sm = [math.sqrt(x) for x in masses]
    tot = sum(sm)
    p = [s / tot for s in sm]                # normalized sqrt-mass distribution
    out["p_g (normalized sqrt m)"] = p
    out["sum_p"] = sum(p)
    out["IPR_sum_p_sq"] = sum(x * x for x in p)     # = Koide Q
    out["Koide_Q"] = koide_Q_from_mass(masses)
    out["participation_ratio_PR"] = 1.0 / sum(x * x for x in p)
    out["N_gen_over_2"] = 3.0 / 2.0
    out["PR_eq_Ngen_over_2?"] = abs(1.0 / sum(x * x for x in p) - 1.5) < 1e-3
    # phase-independence: PR=3/(1+CV^2); on the cone CV=1 -> PR=3/2 for every theta
    rows = []
    for theta in (0.0, THETA_NC, 0.5, 1.0):
        v = cone(theta, b=SQRT2)
        vv = [abs(x) for x in v]    # use |v| for the distribution (v can be negative formally)
        s = sum(vv)
        pg = [x / s for x in vv]
        ipr = sum(x * x for x in pg)
        rows.append({"theta": theta, "Q_from_v^2/(sum v)^2": koide_Q_from_sqrt(v),
                     "CV2": cv2(v)})
    out["cone_phase_scan"] = rows
    out["identity"] = ("Q = sum p_g^2 (inverse participation ratio of normalized sqrt-mass) "
                       "= Simpson/Renyi-2 index; PR = 1/Q = 3/(1+CV^2). "
                       "Koide Q=2/3 <=> CV=1 <=> PR = 3/2 = N_gen/2.")
    out["verdict"] = ("EXACT reformulation (Lean-certifiable, equivalent to CV=1): the "
                      "normalized sqrt-mass vector has inverse participation ratio 2/3, "
                      "i.e. effective participation N_gen/2 = 1.5. Half the generations "
                      "participate. This is a complementary face of the same sqrt2; it is "
                      "NOT an independent derivation of CV=1.")
    return out


# ---------------------------------------------------------------------------
# T_max -- MaxEnt / MDL distinction (1-bit equipartition over irrep TYPES)
# ---------------------------------------------------------------------------
def t_max():
    out = {}
    # 1-bit equipartition over irrep types: trivial energy = standard energy -> b=sqrt2
    v = cone(THETA_NC, b=SQRT2)
    A0 = sum(v) / 3.0
    triv = 3 * A0 * A0
    std = sum(x * x for x in v) - triv
    out["trivial_energy"] = triv
    out["standard_energy"] = std
    out["equipartition_1to1?"] = abs(triv - std) < 1e-9
    out["b_from_equipartition"] = SQRT2
    # naive length-min -> democratic
    out["Q_at_b0_democratic"] = koide_Q_from_sqrt(cone(THETA_NC, b=0.0))
    out["distinction"] = (
        "Two opposite selection principles act on the cone amplitude b: "
        "(i) NAIVE description-length minimization minimizes the number of "
        "non-democratic bits -> b=0 (democratic, Q=1/3) -- WRONG. "
        "(ii) 1-bit MaxEnt / equipartition over the TWO S3 irrep TYPES "
        "(democratic vs splitting), assigning equal L2 energy to each because there "
        "is no information to prefer one -> trivial=standard energy -> b=sqrt2, Q=2/3. "
        "CV=1 is the maximally-noncommittal (MaxEnt-at-fixed-mean / exponential) "
        "signature; MDL selects the maximally-noncommittal GENERATIVE MODEL (MaxEnt "
        "prior), NOT the minimal-bit spectrum. This is the leading PRINCIPLED "
        "candidate but is a selection-principle assumption, not a Phi_MDL "
        "field-equation output -- PROVISIONAL.")
    out["verdict"] = ("PROVISIONAL (CatAD): 1-bit equipartition over S3 irrep types gives "
                      "b=sqrt2 exactly and is phase-independent and sharp, but it is an "
                      "assumed selection principle, not derived from the Phi_MDL "
                      "kink-condensate Lagrangian. No smuggling: not claimed as closure.")
    return out


def main():
    results["T0_sanity"] = t0()
    results["T1_Ag2_prop_a"] = t1()
    results["T2_algebraic_avalues"] = t2()
    results["T3_mass_models"] = t3()
    results["T_pr_participation_ratio"] = t_pr()
    results["T_max_maxent_mdl"] = t_max()

    signal.alarm(0)

    here = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(here, "koide_cv_origin_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)

    print("=" * 74)
    print("080-KOIDE-EQUALNORM Session 2 — the origin of CV(sqrt m)=1")
    print("=" * 74)

    t = results["T0_sanity"]
    print(f"\n[T0] PDG leptons: CV(sqrt m)={t['CV_sqrt_m']:.6f}  Koide Q={t['Koide_Q']:.6f}"
          f"  (target CV=1, Q=2/3)  PASS={t['pass_CV1'] and t['pass_Q23']}")

    t = results["T1_Ag2_prop_a"]
    print(f"\n[T1] A_g^2 ~ a_g={A_VALUES}:  Koide Q={t['Koide_Q_if_m_prop_a']:.4f}  "
          f"CV(sqrt m)={t['CV_sqrt_a']:.4f}")
    print(f"     -> {t['verdict']}")

    t = results["T2_algebraic_avalues"]
    print(f"\n[T2] means of {A_VALUES}: arith={t['arithmetic_mean']:.3f} "
          f"geom={t['geometric_mean']:.3f} harm={t['harmonic_mean']:.3f}")
    print(f"     2*a_tau={t['2*a_tau']} vs a_e+a_mu={t['a_e + a_mu']}  "
          f"(identity holds={t['arithmetic_mean_identity_holds']});  "
          f"equal-modes? {t['a_values_equal_modes?']}")
    print(f"     -> {t['verdict']}")

    t = results["T3_mass_models"]
    m1 = t["model1_exponential"]
    print(f"\n[T3] Model1 exp(lam a): lam_for_CV1={m1.get('lam_for_CV1')}  "
          f"orbit-order matches data={m1.get('orbit_ordering_matches_data')}")
    m2 = t["model2_linear"]
    print(f"     Model2 linear: Q={m2['Koide_Q']:.4f} CV={m2['CV_sqrt_m']:.4f} "
          f"matches_data={m2['matches_data']}")
    m3 = t["model3_powerlaw"]
    print(f"     Model3 a^alpha: alpha_for_Q23={m3.get('alpha_for_Q23'):.4f}  "
          f"matches_data={m3.get('matches_data')}")
    print(f"     -> {t['verdict']}")

    t = results["T_pr_participation_ratio"]
    print(f"\n[T_pr] Q = sum p^2 = {t['IPR_sum_p_sq']:.6f}  PR = 1/Q = "
          f"{t['participation_ratio_PR']:.6f}  (N_gen/2 = 1.5;  match={t['PR_eq_Ngen_over_2?']})")
    print(f"       {t['identity']}")

    t = results["T_max_maxent_mdl"]
    print(f"\n[T_max] equipartition over irrep types: trivial={t['trivial_energy']:.4f} "
          f"standard={t['standard_energy']:.4f} (1:1={t['equipartition_1to1?']}) -> b=sqrt2")
    print(f"        naive length-min -> Q={t['Q_at_b0_democratic']:.4f} (democratic, WRONG)")
    print(f"        -> {t['verdict']}")

    print(f"\nJSON: {out_path}")


if __name__ == "__main__":
    main()
