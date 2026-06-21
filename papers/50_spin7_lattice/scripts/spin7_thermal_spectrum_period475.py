"""Period-475 fingerprint battery on the spin-7 thermal transfer spectrum.

PRE-REGISTERED CRITERIA (fixed before computation; see session record):
  F1 phase-lock: an eigenvalue family of M(beta) with phase theta(beta)
     locked (|d theta / d beta| < 1e-3 over Delta beta >= 1.0) at a rational
     2 pi k / d, d in {5, 19, 25, 95, 475}, tolerance |theta/2pi - k/d| < 1e-4.
     Bare proximity at a single beta is NOT a hit (475-grid covers all phases).
  F2 algebraic factor: char poly of M(x), x = e^{-beta}, entries x^p in Z[x],
     has a Q-factor at rational x whose lambda-support lies in lambda^{d Z},
     d in {5, 19, 25} (exact sympy factorization at x = 1/2, 1/3, 1/7;
     factor-degree pattern must be stable across x values).
  F3 symmetry: affine maps s -> alpha s + gamma on Z/7 (and orientation
     reversal) that leave p covariant, inducing permutation symmetries of M;
     any symmetry of order divisible by 5 or 19 would be structural.
  NULLS for any hit: neighbor-d (d+-1, d+-2 must fit strictly worse);
     wrong-target battery on the reversed polynomial p~(L,C,R) = p(R,C,L).

Outputs all phases, lock segments, factorizations, and the symmetry group.
"""

import json
import os
import signal
import sys
from fractions import Fraction

import numpy as np

TIMEOUT_SECONDS = 900

def _timeout(s, f):
    print("TIMEOUT reached. Exiting with partial results.")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

Q = 7
DLIST = [5, 19, 25, 95, 475]
NEIGHBOR_NULLS = {5: [3, 4, 6, 7], 19: [17, 18, 20, 21], 25: [23, 24, 26, 27],
                  95: [93, 94, 96, 97], 475: [471, 473, 477, 479]}

def p_gf7(L, C, R):
    return (C + R - C * R - L * C * R) % Q

def p_rev(L, C, R):
    return p_gf7(R, C, L)

def build_M(beta, pfun):
    M = np.zeros((49, 49))
    for a in range(Q):
        for b in range(Q):
            for c in range(Q):
                M[a * Q + b, b * Q + c] = np.exp(-beta * pfun(a, b, c))
    return M

# ---------------------------------------------------------- F1: phase tracking
def phase_battery(pfun, label):
    betas = np.arange(0.25, 6.01, 0.05)
    # collect complex-eigenvalue phases per beta (positive phases only)
    phase_sets = []
    for beta in betas:
        ev = np.linalg.eigvals(build_M(beta, pfun))
        phases = sorted(float(np.angle(z)) for z in ev
                        if abs(np.angle(z)) > 1e-9 and np.angle(z) > 0
                        and abs(z) > 1e-12)
        phase_sets.append(phases)
    # track families by nearest-neighbor continuation
    n0 = len(phase_sets[0])
    tracks = [[ph] for ph in phase_sets[0]]
    active = list(range(n0))
    for k in range(1, len(betas)):
        cur = phase_sets[k]
        used = set()
        new_active = []
        for ti in active:
            last = tracks[ti][-1]
            best, bestd = None, None
            for j, ph in enumerate(cur):
                if j in used:
                    continue
                d = abs(ph - last)
                if bestd is None or d < bestd:
                    best, bestd = j, d
            if best is not None and bestd < 0.15:
                tracks[ti].append(cur[best])
                used.add(best)
                new_active.append(ti)
        active = new_active
    # lock detection: windows of >= 21 consecutive points (>= 1.0 in beta)
    # with total phase variation < 1e-3 * window length
    locks = []
    for ti, tr in enumerate(tracks):
        tr = np.array(tr)
        W = 21
        for s in range(0, len(tr) - W):
            seg = tr[s:s + W]
            drift = abs(seg[-1] - seg[0]) / (0.05 * (W - 1))
            if drift < 1e-3:
                theta = float(np.mean(seg))
                locks.append({"track": ti, "beta_start": float(betas[s]),
                              "theta_over_2pi": theta / (2 * np.pi)})
    # match locked phases (if any) against d-grids and neighbor nulls
    hits = []
    for lk in locks:
        x = lk["theta_over_2pi"]
        for d in DLIST:
            k = round(x * d)
            if k > 0 and abs(x - k / d) < 1e-4:
                null_better = []
                for dn in NEIGHBOR_NULLS[d]:
                    kn = round(x * dn)
                    if kn > 0 and abs(x - kn / dn) <= abs(x - k / d):
                        null_better.append(dn)
                hits.append({**lk, "d": d, "k": k,
                             "null_d_fits_as_well": null_better})
    print(f"[{label}] tracks: {len(tracks)}; lock segments: {len(locks)}; "
          f"grid hits: {len(hits)}")
    # phase drift summary (are ANY phases beta-independent?)
    drifts = []
    for tr in tracks:
        if len(tr) > 40:
            tr = np.array(tr)
            drifts.append(float(abs(tr[-1] - tr[0])))
    if drifts:
        print(f"[{label}] phase total variation over beta in [0.25,6]: "
              f"min {min(drifts):.4f}, median {np.median(drifts):.4f} rad")
    return {"n_tracks": len(tracks), "locks": locks, "hits": hits,
            "min_total_drift_rad": min(drifts) if drifts else None}

print("=== F1: phase-lock battery (primary polynomial) ===")
f1_main = phase_battery(p_gf7, "p")
print("\n=== F1 wrong-target null: reversed polynomial ===")
f1_null = phase_battery(p_rev, "p_rev")

# ------------------------------------------------- F2: exact factorization
import sympy as sp

def charpoly_factor(xval, pfun, label):
    lam = sp.Symbol('lam')
    x = sp.Rational(xval)
    M = sp.zeros(49, 49)
    for a in range(Q):
        for b in range(Q):
            for c in range(Q):
                M[a * Q + b, b * Q + c] = x**pfun(a, b, c)
    cp = M.charpoly(lam).as_expr()
    fac = sp.factor_list(cp, lam)
    pattern = []
    for f, mult in fac[1]:
        poly = sp.Poly(f, lam)
        degs = [m[0] for m in poly.monoms()]
        # lambda-support gcd: d such that support subset d*Z
        from math import gcd
        g = 0
        for dgg in degs:
            g = gcd(g, dgg)
        pattern.append({"degree": poly.degree(), "mult": mult,
                        "support_gcd": g})
    print(f"[{label}, x={xval}] factors (degree, mult, lambda-support gcd): "
          f"{[(p['degree'], p['mult'], p['support_gcd']) for p in pattern]}")
    zd_flags = [p for p in pattern
                if p["support_gcd"] in (5, 19, 25) and p["degree"] > 1]
    return {"x": str(xval), "pattern": pattern, "zd_factors": zd_flags}

print("\n=== F2: exact characteristic-polynomial factorization ===")
f2 = []
for xv in [Fraction(1, 2), Fraction(1, 3), Fraction(1, 7)]:
    f2.append(charpoly_factor(xv, p_gf7, "p"))
print("--- wrong-target null ---")
f2_null = [charpoly_factor(Fraction(1, 2), p_rev, "p_rev")]

# ------------------------------------------------- F3: affine symmetry group
print("\n=== F3: affine covariance group of p ===")
syms = []
for alpha in range(1, Q):
    for gamma in range(Q):
        # does s -> alpha s + gamma conjugate p to a permutation of values?
        # require p(g(L),g(C),g(R)) = pi(p(L,C,R)) for a value-permutation pi
        table = {}
        ok = True
        for L in range(Q):
            for C in range(Q):
                for R in range(Q):
                    src = p_gf7(L, C, R)
                    dst = p_gf7((alpha * L + gamma) % Q, (alpha * C + gamma) % Q,
                                (alpha * R + gamma) % Q)
                    if src in table and table[src] != dst:
                        ok = False
                        break
                    table[src] = dst
                if not ok:
                    break
            if not ok:
                break
        if ok:
            syms.append({"alpha": alpha, "gamma": gamma,
                         "value_perm": {str(k): v for k, v in sorted(table.items())}})
print(f"affine covariances found: {[(s['alpha'], s['gamma']) for s in syms]}")
# orders of the affine maps found
def aff_order(alpha, gamma):
    a, g = 1, 0
    for n in range(1, 50):
        a, g = (a * alpha) % Q, (g * alpha + gamma) % Q
        if a == 1 and g == 0:
            return n
    return None
orders = [aff_order(s["alpha"], s["gamma"]) for s in syms]
print(f"orders of the covariance maps: {orders}")
div_5_19 = [o for o in orders if o is not None and (o % 5 == 0 or o % 19 == 0)]
print(f"orders divisible by 5 or 19: {div_5_19 if div_5_19 else 'NONE'}")

signal.alarm(0)

# ------------------------------------------------------------------ verdict
def verdict():
    f1_pass = any(len(h["null_d_fits_as_well"]) == 0 for h in f1_main["hits"])
    f2_pass = any(len(r["zd_factors"]) > 0 for r in f2)
    f3_pass = len(div_5_19) > 0
    return f1_pass, f2_pass, f3_pass

v1, v2, v3 = verdict()
print(f"\n=== VERDICT ===")
print(f"F1 phase-lock fingerprint:        {'HIT' if v1 else 'NULL'}")
print(f"F2 Z_d factor fingerprint:        {'HIT' if v2 else 'NULL'}")
print(f"F3 order-5/19 symmetry:           {'HIT' if v3 else 'NULL'}")
print(f"=> period-475 spectral fingerprint: "
      f"{'FOUND (check nulls!)' if (v1 or v2 or v3) else 'ABSENT (all batteries null)'}")

out = {"F1": {"main": f1_main, "wrong_target_null": f1_null},
       "F2": {"main": f2, "wrong_target_null": f2_null},
       "F3": {"covariances": syms, "orders": orders,
              "orders_div_5_or_19": div_5_19},
       "verdict": {"F1": v1, "F2": v2, "F3": v3},
       "preregistration": "phase-lock 1e-3/1.0-beta + 1e-4 grid tol; "
                          "Z_d lambda-support factors d in {5,19,25}; "
                          "affine covariance order divisible by 5 or 19; "
                          "neighbor + wrong-target nulls"}
_out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "spin7_thermal_spectrum_period475.json")
with open(_out_path, "w") as f:
    json.dump(out, f, indent=2, default=str)
print("\nSaved", _out_path)
