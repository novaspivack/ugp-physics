#!/usr/bin/env python3
"""
080-KOIDE-EQUALNORM: Why does the Phi_MDL kink condensate produce EQUAL norms for
the trivial (democratic) and standard (generation-splitting) S3 irreps?

Equal-irrep-norm  <=>  Koide cone amplitude b = sqrt(2)  <=>  Koide Q = 2/3.

This script tests the three proposed mechanisms and establishes the exact
reformulations and null results.

Generation Yukawa on the Z3 orbit (g = 0,1,2):
    v_g = sqrt(m_g) = A * (1 + b * cos(theta + 2*pi*g/3))
  trivial-irrep (DC)        : A_0 = mean(v)              ; |v_triv|^2 = 3 A_0^2
  standard-irrep (AC pair)  : A_1, A_2 (conj)            ; |v_std|^2  = 6|A_1|^2
  equal-norm  <=>  3 A_0^2 = 6|A_1|^2  <=>  |A_0|^2 = |A_1|^2 + |A_2|^2

TASKS
  T_neg  Mechanism (c) [Z7 a-values force equal modes]: NEGATIVE test.
         Z3-Fourier of raw a-values {1,9,5}: is |A_0|^2 = |A_1|^2 + |A_2|^2 ?
  T_cv   EXACT reformulation: equal-norm <=> coefficient-of-variation CV(sqrt m)=1
         <=> Var = mean^2 ; and Q = (1 + CV^2)/3.  (CatAL-able)
  T_max  Mechanism (a) [MDL / MaxEnt]: CV=1 is the maximum-entropy (exponential)
         signature on [0,inf) at fixed mean.  Also: naive K-minimization gives the
         DEMOCRATIC b=0 (disclose), so plain length-min is NOT the principle; the
         correct dual statement is MaxEnt-at-fixed-mean.
  T_ker  Mechanism (b) [local kernel / BPS support]: which Z3 convolution kernels
         (real, symmetric) produce equal trivial/standard output norm?  Scan and
         characterize the 50/50 (irrep-type equipartition) locus.
  T_irr  irrep-type vs dimension equipartition: show equal-norm = equipartition over
         the 2 S3 irrep TYPES (1:1), NOT over the 3 Z3 modes/dimensions (1:2).

Expected:
  - T_neg: NOT equal (225 vs 96) -> mechanism (c) literal form ruled out.
  - T_cv : CV^2 = 1.000000 exactly on the cone; Q=(1+CV^2)/3 holds.
  - T_max: exponential CV=1; MaxEnt fixed-mean -> CV=1.
  - T_ker: kernels with k0^2 (DC power) = 2*|k_AC|^2 give equal-norm output.

JSON artifact saved alongside. Wall-clock timeout 120s.
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

SQRT2 = math.sqrt(2.0)
THETA_NC = 2.0 / 9.0
A_VALUES = [1, 9, 5]  # generation a-values from N_c=3 (e, mu, tau), g=0->e,1->mu,2->tau

results = {"task": "080-KOIDE-EQUALNORM", "theta_Nc": THETA_NC}


def z3_fourier(vec):
    """Complex Z3-Fourier transform A_k = sum_g vec_g exp(2pi i k g /3)."""
    import cmath
    return [sum(vec[g] * cmath.exp(2j * math.pi * k * g / 3.0) for g in range(3))
            for k in range(3)]


def cone(theta, b=SQRT2, A=1.0):
    return [A * (1.0 + b * math.cos(theta + 2.0 * math.pi * g / 3.0)) for g in range(3)]


def koide_Q(v):
    s = sum(v)
    return sum(x * x for x in v) / (s * s)


def cv2(v):
    """Population coefficient of variation squared: Var/mean^2."""
    m = sum(v) / len(v)
    var = sum((x - m) ** 2 for x in v) / len(v)
    return var / (m * m)


# ---------------------------------------------------------------------------
# T_neg -- mechanism (c): raw Z7 a-values, NEGATIVE test
# ---------------------------------------------------------------------------
def t_neg():
    out = {}
    A = z3_fourier([float(x) for x in A_VALUES])
    mags2 = [abs(A[k]) ** 2 for k in range(3)]
    out["a_values"] = A_VALUES
    out["|A_k|^2"] = mags2
    out["|A_0|^2"] = mags2[0]
    out["|A_1|^2 + |A_2|^2"] = mags2[1] + mags2[2]
    out["equal_modes?"] = abs(mags2[0] - (mags2[1] + mags2[2])) < 1e-9
    # also as integers (exact): |A_0|^2 = 15^2 = 225; |A_1|^2 = |A_2|^2 = 48
    out["exact_int"] = {"|A0|^2": 225, "|A1|^2": 48, "|A2|^2": 48,
                        "|A1|^2+|A2|^2": 96}
    # CV of raw a-values (just to show it is NOT 1)
    out["cv2_of_a_values"] = cv2([float(x) for x in A_VALUES])
    out["verdict"] = ("RULED OUT: raw Z7 a-values {1,9,5} do NOT satisfy equal-norm "
                      "(225 != 96). Mechanism (c) as literally posed fails: the discrete "
                      "orbit labels are not the continuous sqrt-mass amplitudes.")
    return out


# ---------------------------------------------------------------------------
# T_cv -- exact reformulation: equal-norm <=> CV(sqrt m) = 1
# ---------------------------------------------------------------------------
def t_cv():
    out = {}
    # On the cone (b=sqrt2, any theta) CV^2 must be 1 and Q must be 2/3.
    rows = []
    for theta in (0.0, THETA_NC, 0.5, 1.0, math.pi / 4):
        v = cone(theta, b=SQRT2)
        if min(v) <= 0:
            rows.append({"theta": theta, "cv2": cv2(v), "Q": koide_Q(v),
                         "note": "neg amplitude (formal)"})
        else:
            rows.append({"theta": theta, "cv2": cv2(v), "Q": koide_Q(v)})
    out["cone_b_sqrt2"] = rows
    # General b: cv2 = (3/2 b^2)/3 = b^2/2 ; Q = (1+cv2)/3 = 1/3 + b^2/6
    out["analytic"] = {
        "cv2_eq_b2_over_2": "Var/mean^2 = b^2/2 for v_g=1+b cos(theta+2pi g/3)",
        "Q_eq_(1+cv2)/3": "Q = (1 + CV^2)/3 ; Q=2/3 <=> CV^2=1 <=> b^2=2 <=> b=sqrt2",
    }
    # numeric verification of Q=(1+cv2)/3 over a b-scan
    chk = []
    for b in (0.0, 0.5, 1.0, SQRT2, 1.5, 2.0):
        v = cone(THETA_NC, b=b)
        c2 = cv2(v)
        q = koide_Q(v)
        chk.append({"b": b, "cv2": c2, "Q": q, "(1+cv2)/3": (1 + c2) / 3,
                    "match": abs(q - (1 + c2) / 3) < 1e-12})
    out["b_scan_Q_eq_(1+cv2)/3"] = chk
    out["verdict"] = ("EXACT: equal-irrep-norm <=> CV(sqrt m)=1 <=> Var=mean^2 ; "
                      "Q=(1+CV^2)/3. Koide Q=2/3 is exactly CV=1 (std dev of sqrt-mass "
                      "= mean of sqrt-mass). CatAL-certifiable.")
    return out


# ---------------------------------------------------------------------------
# T_max -- mechanism (a): MaxEnt / MDL. CV=1 is the exponential (MaxEnt) signature.
# ---------------------------------------------------------------------------
def t_max():
    out = {}
    # Exponential distribution: mean=mu, var=mu^2, CV=1 EXACTLY (MaxEnt on [0,inf), fixed mean).
    out["exponential_CV"] = 1.0
    out["maxent_statement"] = ("MaxEnt on [0,inf) with fixed mean => exponential p(x)="
                               "(1/mu)exp(-x/mu); var=mu^2; CV=1. CV=1 is the unique "
                               "MaxEnt-at-fixed-mean signature for a positive spectrum.")
    # Sample the exponential to confirm CV->1
    import random
    random.seed(7)
    N = 200000
    mu = 3.3
    xs = [random.expovariate(1.0 / mu) for _ in range(N)]
    m = sum(xs) / N
    v = sum((x - m) ** 2 for x in xs) / N
    out["exp_sample_cv2"] = v / (m * m)
    out["exp_sample_note"] = f"empirical CV^2 over N={N} exponential samples -> ~1.0"
    # Naive MDL/length minimization: minimize 'structure' at fixed mean -> b=0 (democratic).
    out["naive_K_min"] = ("Minimizing description length of the orbit Yukawa at fixed "
                          "mean prefers b=0 (perfectly democratic, all generations equal) "
                          "-> Q=1/3, NOT 2/3. So plain length-minimization is the WRONG "
                          "principle; it must be MaxEnt-at-fixed-mean (MDL dual), which "
                          "yields the maximally-noncommittal positive spectrum CV=1.")
    out["Q_at_b0"] = koide_Q(cone(THETA_NC, b=0.0))   # should be 1/3
    out["verdict"] = ("PROVISIONAL (CatAD): equal-norm = CV=1 is the maximum-entropy "
                      "(MDL-dual) signature of a positive spectrum at fixed mean. This is "
                      "a principled origin but is NOT a Phi_MDL field-equation output; we "
                      "do not assert it as a derivation.")
    return out


# ---------------------------------------------------------------------------
# T_ker -- mechanism (b): which real symmetric Z3 kernels give equal-norm output?
# ---------------------------------------------------------------------------
def t_ker():
    """
    A real symmetric nearest-neighbor kernel on Z3: K = [k0, k1, k1].
    Its Z3-Fourier: K0 = k0 + 2 k1 ; K1 = K2 = k0 - k1.
    If the generation Yukawa = K convolved with a localized (delta) condensate seed,
    the output's trivial/standard split mirrors |K0|^2 vs 2|K1|^2.
    Equal-norm output <=> |K0|^2 = 2|K1|^2 <=> (k0+2k1)^2 = 2(k0-k1)^2.
    Scan the (k0,k1) locus and report the ratio r = k1/k0 that gives equal-norm.
    """
    out = {}
    sols = []
    # (k0+2k1)^2 = 2(k0-k1)^2 ; set k0=1, solve for k1=r:
    # (1+2r)^2 = 2(1-r)^2 -> 1+4r+4r^2 = 2 -4r +2r^2 -> 2r^2 +8r -1 = 0
    # r = (-8 +/- sqrt(64+8))/4 = (-8 +/- sqrt72)/4 = -2 +/- (3 sqrt2)/2
    import math as _m
    for sign in (+1, -1):
        r = -2.0 + sign * (3.0 * _m.sqrt(2.0) / 2.0)
        k0, k1 = 1.0, r
        K0 = k0 + 2 * k1
        K1 = k0 - k1
        sols.append({"k1/k0": r, "|K0|^2": K0 * K0, "2|K1|^2": 2 * K1 * K1,
                     "equal": abs(K0 * K0 - 2 * K1 * K1) < 1e-9})
    out["equal_norm_kernel_roots(k1/k0)"] = sols
    out["note"] = ("A real symmetric Z3 kernel gives equal trivial/standard OUTPUT norm "
                   "on a 1-parameter locus 2r^2+8r-1=0 (r=k1/k0). Equal-norm is NOT "
                   "generic: it is a codimension-1 condition on the kernel. So mechanism "
                   "(b) requires the specific BPS-kink overlap kernel to land on this "
                   "locus; that is an un-derived field input, not a generic consequence.")
    out["verdict"] = ("PLAUSIBLE but UN-DERIVED: equal-norm is codimension-1 in kernel "
                      "space; producing it requires the specific BPS overlap profile. We "
                      "do not fabricate that profile (would be smuggling).")
    return out


# ---------------------------------------------------------------------------
# T_irr -- irrep-TYPE equipartition (1:1) vs dimension/mode equipartition (1:2)
# ---------------------------------------------------------------------------
def t_irr():
    out = {}
    v = cone(THETA_NC, b=SQRT2)
    A0 = sum(v) / 3.0
    # trivial subspace energy and standard subspace energy
    triv = 3 * A0 * A0
    std = sum(x * x for x in v) - triv
    out["trivial_energy"] = triv
    out["standard_energy"] = std
    out["ratio_triv:std"] = triv / std
    out["type_equipartition_1:1"] = abs(triv - std) < 1e-9
    # per-mode (dimension) equipartition would be 1 (trivial dim) : 2 (standard dim) = 1:2
    out["mode_equipartition_would_be_1:2"] = ("If energy were split per Z3 mode/dimension, "
                                              "trivial:standard = 1:2 -> b would satisfy "
                                              "3A0^2 = 3|A1|^2 (per-mode) giving Q!=2/3.")
    out["interpretation"] = ("Equal-norm = equipartition over the TWO S3 irrep TYPES "
                             "(symmetric/democratic vs generation-splitting), each carrying "
                             "half the sqrt-mass L2 energy -- a 1-bit MaxEnt over irrep "
                             "label, NOT equipartition over the 3 modes (which gives 1:2).")
    return out


def main():
    results["T_neg_raw_avalues"] = t_neg()
    results["T_cv_reformulation"] = t_cv()
    results["T_max_maxent_mdl"] = t_max()
    results["T_ker_local_kernel"] = t_ker()
    results["T_irr_irrep_type_equipartition"] = t_irr()

    signal.alarm(0)

    here = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(here, "koide_equalnorm_mechanism_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)

    print("=" * 72)
    print("080-KOIDE-EQUALNORM: origin of equal trivial/standard S3-irrep norm")
    print("=" * 72)

    tn = results["T_neg_raw_avalues"]
    print(f"\n[T_neg] raw a-values {tn['a_values']}  Z3-Fourier |A_k|^2 = "
          f"{[round(x,3) for x in tn['|A_k|^2']]}")
    print(f"        |A0|^2 = {tn['|A_0|^2']:.1f} vs |A1|^2+|A2|^2 = "
          f"{tn['|A_1|^2 + |A_2|^2']:.1f}  equal? {tn['equal_modes?']}")
    print(f"        -> {tn['verdict']}")

    tc = results["T_cv_reformulation"]
    print(f"\n[T_cv]  cone (b=sqrt2):")
    for r in tc["cone_b_sqrt2"]:
        print(f"          theta={r['theta']:.4f}  CV^2={r['cv2']:.6f}  Q={r['Q']:.6f}")
    print(f"        Q=(1+CV^2)/3 check over b-scan:")
    for r in tc["b_scan_Q_eq_(1+cv2)/3"]:
        print(f"          b={r['b']:.4f}  CV^2={r['cv2']:.4f}  Q={r['Q']:.4f}  "
              f"(1+CV^2)/3={r['(1+cv2)/3']:.4f}  match={r['match']}")
    print(f"        -> {tc['verdict']}")

    tm = results["T_max_maxent_mdl"]
    print(f"\n[T_max] exponential (MaxEnt fixed-mean) CV=1 ; sample CV^2="
          f"{tm['exp_sample_cv2']:.4f}")
    print(f"        naive length-min -> b=0 democratic, Q={tm['Q_at_b0']:.4f} (=1/3, WRONG)")
    print(f"        -> {tm['verdict']}")

    tk = results["T_ker_local_kernel"]
    print(f"\n[T_ker] equal-norm kernel locus 2r^2+8r-1=0 (r=k1/k0):")
    for s in tk["equal_norm_kernel_roots(k1/k0)"]:
        print(f"          r={s['k1/k0']:+.5f}  |K0|^2={s['|K0|^2']:.4f}  "
              f"2|K1|^2={s['2|K1|^2']:.4f}  equal={s['equal']}")
    print(f"        -> {tk['verdict']}")

    ti = results["T_irr_irrep_type_equipartition"]
    print(f"\n[T_irr] trivial energy={ti['trivial_energy']:.4f}  "
          f"standard energy={ti['standard_energy']:.4f}  "
          f"1:1? {ti['type_equipartition_1:1']}")
    print(f"        {ti['interpretation']}")

    print(f"\nJSON: {out_path}")


if __name__ == "__main__":
    main()
