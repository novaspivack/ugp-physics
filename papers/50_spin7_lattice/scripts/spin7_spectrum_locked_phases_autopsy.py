"""Autopsy of the two F-battery observations from the period-475 scan.

(1) Locked phases: identify the values of the beta-independent eigenvalue
    phases of M(beta) (the F1 scan found families with zero total drift).
    Compare against 2 pi k / d for ALL d <= 30 plus {95, 475}; identify the
    structural origin (trivial multiplets vs genuine rotational families).

(2) Kernel/factor structure: the char poly factors as lam^11 * (irreducible
    deg 38) at every tested x for BOTH p and the reflection-conjugate p_rev.
    38 = 2*19 is a post-hoc reading; reflection conjugacy preserves orbit
    periods, so p_rev cannot kill a 19-claim.  Tests:
      (a) account for the kernel dimension 11 by exact row/column dependency
          counting (structural, beta-independent);
      (b) genuine wrong-targets: cubics with DIFFERENT deterministic orbit
          structure -- q1 = C+R-CR+LCR, q2 = C+R-2CR-LCR, q3 = C+2R-CR-LCR
          (mod 7) -- factor their transfer char polys; if deg(big factor) is
          generically 49 - dim ker and dim ker varies with the rule, the
          "38 = 2*19" reading is row-bookkeeping, not attractor content.
"""

import json
import os
import signal
import sys
from fractions import Fraction
from math import gcd

import numpy as np
import sympy as sp

TIMEOUT_SECONDS = 600

def _timeout(s, f):
    print("TIMEOUT reached. Exiting.")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

Q = 7

def make_p(cLCR, cCR=-1, cR=1, cC=1):
    def f(L, C, R):
        return (cC * C + cR * R + cCR * C * R + cLCR * L * C * R) % Q
    return f

p_main = make_p(-1)

# ---------------------------------------------------------- (1) locked phases
print("=== (1) locked-phase identification ===")
def build_M(beta, pfun):
    M = np.zeros((49, 49))
    for a in range(Q):
        for b in range(Q):
            for c in range(Q):
                M[a * Q + b, b * Q + c] = np.exp(-beta * pfun(a, b, c))
    return M

locked = {}
for beta in [0.5, 1.0, 2.0, 4.0, 6.0]:
    ev = np.linalg.eigvals(build_M(beta, p_main))
    phases = sorted(float(np.angle(z)) for z in ev
                    if np.angle(z) > 1e-9 and abs(z) > 1e-12)
    locked[beta] = phases
    print(f"beta={beta:4.1f}: positive phases/2pi = "
          f"{[round(ph / (2 * np.pi), 6) for ph in phases]}")

# which phase values recur identically across beta?
vals0 = np.array(locked[0.5])
stable = []
for v in vals0:
    if all(any(abs(v - w) < 1e-9 for w in locked[b]) for b in locked):
        stable.append(v)
print(f"\nbeta-independent phases/2pi: {[round(v/(2*np.pi), 8) for v in stable]}")
for v in stable:
    x = v / (2 * np.pi)
    best = None
    for d in list(range(2, 31)) + [95, 475]:
        k = round(x * d)
        if k > 0:
            err = abs(x - k / d)
            if best is None or err < best[2]:
                best = (k, d, err)
    print(f"  theta/2pi = {x:.8f}  ~ {best[0]}/{best[1]}  (err {best[2]:.2e})")

# ------------------------------------------- (2a) kernel dimension accounting
print("\n=== (2a) kernel dimension accounting ===")
def kernel_account(pfun, label):
    # exact symbolic rank at x = 1/2
    x = sp.Rational(1, 2)
    M = sp.zeros(49, 49)
    for a in range(Q):
        for b in range(Q):
            for c in range(Q):
                M[a * Q + b, b * Q + c] = x**pfun(a, b, c)
    rank = M.rank()
    # row-coincidence count: rows (a,b) and (a',b) equal iff the c-profile
    # p(a,b,.) == p(a',b,.)
    dep = 0
    for b in range(Q):
        profiles = {}
        for a in range(Q):
            prof = tuple(pfun(a, b, c) for c in range(Q))
            profiles.setdefault(prof, []).append(a)
        for prof, alist in profiles.items():
            dep += len(alist) - 1
    print(f"[{label}] rank = {rank}, dim ker = {49 - rank}, "
          f"row-coincidence dependencies = {dep}")
    return rank, dep

rank_p, dep_p = kernel_account(p_main, "p")

# ------------------------------------------------- (2b) genuine wrong-targets
print("\n=== (2b) genuine wrong-target factorizations ===")
def orbit_period_5ring(pfun):
    """Period of the attractor reached from a fixed seed on the 5-cell ring."""
    s = (1, 2, 3, 4, 5)
    seen = {}
    t = 0
    while s not in seen:
        seen[s] = t
        s = tuple(pfun(s[(i - 1) % 5], s[i], s[(i + 1) % 5]) for i in range(5))
        t += 1
        if t > 20000:
            return None, None
    return seen[s], t - seen[s]   # transient, period

def factor_pattern(pfun, label):
    lam = sp.Symbol('lam')
    x = sp.Rational(1, 2)
    M = sp.zeros(49, 49)
    for a in range(Q):
        for b in range(Q):
            for c in range(Q):
                M[a * Q + b, b * Q + c] = x**pfun(a, b, c)
    cp = M.charpoly(lam).as_expr()
    fac = sp.factor_list(cp, lam)
    pat = []
    for f, mult in fac[1]:
        poly = sp.Poly(f, lam)
        degs = [m[0] for m in poly.monoms()]
        g = 0
        for dg in degs:
            g = gcd(g, dg)
        pat.append((poly.degree(), mult, g))
    tr, per = orbit_period_5ring(pfun)
    print(f"[{label}] 5-ring attractor period (seed 12345): {per}; "
          f"charpoly pattern (deg, mult, support_gcd): {pat}")
    return {"label": label, "period": per, "pattern": pat}

targets = [("p (main)", p_main),
           ("q1 = C+R-CR+LCR", make_p(+1)),
           ("q2 = C+R-2CR-LCR", make_p(-1, cCR=-2)),
           ("q3 = C+2R-CR-LCR", make_p(-1, cR=2))]
results = [factor_pattern(f, lab) for lab, f in targets]

signal.alarm(0)

out = {"locked_phases_over_2pi": [float(v / (2 * np.pi)) for v in stable],
       "kernel": {"rank": int(rank_p), "row_dependencies": int(dep_p)},
       "wrong_targets": [{"label": r["label"], "period": r["period"],
                          "pattern": [list(map(int, t)) for t in r["pattern"]]}
                         for r in results]}
_out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "spin7_spectrum_locked_phases_autopsy.json")
with open(_out_path, "w") as f:
    json.dump(out, f, indent=2)
print("\nSaved", _out_path)
