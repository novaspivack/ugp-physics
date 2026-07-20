"""Continuum-limit scaling study of the spin-7 chain's exact 49x49 transfer matrix.

Computes the dimensionless lattice gap Delta(beta) = log(lambda_1/|lambda_2|)
= 1/xi(beta) for beta up to 12, using float64 for beta <= 7 and mpmath
(dps = 50) for beta >= 6 (overlap region cross-checks the two backends).

Tests the analytic directed-wall-gas prediction
    Delta(beta) ~ 2*sqrt(w01*w10) * exp(-beta*(E01+E10)/2) = 2*exp(-1.5*beta)
from spin7_wall_translation_classes.py:
  - local slope s(beta) = -d ln Delta / d beta via central differences,
    Richardson-extrapolated to beta -> infinity
  - prefactor A(beta) = Delta * exp(1.5*beta), extrapolated

Expected output: slope -> 1.500... (>= 4 digits), prefactor -> 2.000...
"""

import json
import os
import signal
import sys

import numpy as np
import mpmath as mp

TIMEOUT_SECONDS = 900

def _timeout(s, f):
    print("TIMEOUT reached. Exiting with partial results.")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

Q = 7

def p_gf7(L, C, R):
    return (C + R - C * R - L * C * R) % Q

P_TABLE = [[[p_gf7(a, b, c) for c in range(Q)] for b in range(Q)]
           for a in range(Q)]

def gap_float64(beta):
    M = np.zeros((49, 49))
    for a in range(Q):
        for b in range(Q):
            for c in range(Q):
                M[a * Q + b, b * Q + c] = np.exp(-beta * P_TABLE[a][b][c])
    ev = np.linalg.eigvals(M)
    mods = np.sort(np.abs(ev))[::-1]
    lam1, lam2 = mods[0], mods[1]
    return float(np.log(lam1 / lam2)), float(lam1), float(lam2)

def gap_mpmath(beta, dps=50):
    with mp.workdps(dps):
        b = mp.mpf(beta)
        M = mp.zeros(49, 49)
        for a in range(Q):
            for bb in range(Q):
                for c in range(Q):
                    M[a * Q + bb, bb * Q + c] = mp.e**(-b * P_TABLE[a][bb][c])
        ev = mp.eig(M, left=False, right=False)
        mods = sorted([abs(x) for x in ev], reverse=True)
        lam1, lam2 = mods[0], mods[1]
        return mp.log(lam1 / lam2), lam1, lam2

# ------------------------------------------------------------------ table
print("=== Delta(beta) table ===")
betas_f = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0]
betas_m = [6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0]

rows = []
for beta in betas_f:
    d, l1, l2 = gap_float64(beta)
    rows.append({"beta": beta, "Delta": d, "lambda1": l1, "lambda2": l2,
                 "backend": "float64"})
    print(f"  beta={beta:5.2f}  Delta={d:.10e}  lam1={l1:.8f}  (float64)")

mp_rows = []
for beta in betas_m:
    d, l1, l2 = gap_mpmath(beta)
    mp_rows.append({"beta": beta, "Delta": float(d), "lambda1": float(l1),
                    "lambda2": float(l2), "backend": "mpmath_dps50"})
    print(f"  beta={beta:5.2f}  Delta={float(d):.10e}  lam1={float(l1):.10f}  (mpmath)")

# cross-check overlap
f6 = next(r for r in rows if r["beta"] == 6.0)["Delta"]
m6 = next(r for r in mp_rows if r["beta"] == 6.0)["Delta"]
f7 = next(r for r in rows if r["beta"] == 7.0)["Delta"]
m7 = next(r for r in mp_rows if r["beta"] == 7.0)["Delta"]
print(f"\nBackend cross-check: beta=6 rel diff {abs(f6-m6)/m6:.2e}; "
      f"beta=7 rel diff {abs(f7-m7)/m7:.2e}")

# ------------------------------------------------- slope and prefactor
print("\n=== Local slope s(beta) = -d ln Delta / d beta (central diff, h=1) ===")
allrows = {r["beta"]: r["Delta"] for r in rows}
allrows.update({r["beta"]: r["Delta"] for r in mp_rows})
bs = sorted(allrows)
slopes = {}
for i in range(1, len(bs) - 1):
    b0, b1, b2 = bs[i - 1], bs[i], bs[i + 1]
    s = -(np.log(allrows[b2]) - np.log(allrows[b0])) / (b2 - b0)
    slopes[b1] = s
    print(f"  beta={b1:5.2f}  s={s:.8f}")

print("\n=== Prefactor A(beta) = Delta * exp(1.5*beta) ===")
prefs = {}
for b in bs:
    A = allrows[b] * np.exp(1.5 * b)
    prefs[b] = A
    print(f"  beta={b:5.2f}  A={A:.8f}")

# Richardson-style extrapolation: corrections O(e^{-beta/2}) expected
# (next channel and diagonal terms), so fit s(beta) = s_inf + c*exp(-beta/2)
# on the last few points.
tail = [b for b in slopes if b >= 8.0]
if len(tail) >= 3:
    import numpy.linalg as la
    Xm = np.array([[1.0, np.exp(-b / 2)] for b in tail])
    yv = np.array([slopes[b] for b in tail])
    coef, *_ = la.lstsq(Xm, yv, rcond=None)
    s_inf = coef[0]
    print(f"\nExtrapolated slope s_inf (fit s = s_inf + c*e^(-beta/2) on beta >= 8): "
          f"{s_inf:.8f}")
    Xp = np.array([[1.0, np.exp(-b / 2)] for b in tail])
    yp = np.array([prefs[b] for b in tail])
    coefp, *_ = la.lstsq(Xp, yp, rcond=None)
    A_inf = coefp[0]
    print(f"Extrapolated prefactor A_inf: {A_inf:.8f}")
else:
    s_inf, A_inf = None, None

print(f"\nPREDICTED:  slope 1.5 exactly, prefactor 2*sqrt(w01*w10) = 2")
if s_inf is not None:
    print(f"MEASURED:   slope {s_inf:.6f}, prefactor {A_inf:.6f}")
    print(f"slope agreement: |s_inf - 1.5| = {abs(s_inf-1.5):.2e}")
    print(f"prefactor agreement: |A_inf - 2| = {abs(A_inf-2):.2e}")

signal.alarm(0)

out = {
    "table_float64": rows,
    "table_mpmath": mp_rows,
    "local_slopes": {str(k): v for k, v in slopes.items()},
    "prefactors": {str(k): float(v) for k, v in prefs.items()},
    "extrapolated_slope": float(s_inf) if s_inf is not None else None,
    "extrapolated_prefactor": float(A_inf) if A_inf is not None else None,
    "prediction": {"slope": 1.5, "prefactor": 2.0,
                   "law": "Delta ~ 2*exp(-1.5*beta) (directed wall gas, "
                          "geometric mean of E_w(0->1)=2 and E_w(1->0)=1)"},
}
_out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "spin7_continuum_scaling_law.json")
with open(_out_path, "w") as f:
    json.dump(out, f, indent=2)
print("\nSaved", _out_path)
