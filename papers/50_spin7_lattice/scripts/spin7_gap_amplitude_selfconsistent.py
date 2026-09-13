"""Self-consistent (full lambda-dependence) gap-amplitude series for spin-7.

Extends spin7_gap_amplitude_resolvent.py: the Schur eigenvalue condition at
lambda = 1 + eps uses the exact resolvent expansion
   (lambda I - M_RR)^{-1} = Q - eps Q^2 + eps^2 Q^3 - ...,
   Q = (I - M_RR)^{-1}  (finite t-adic series; nilpotent zero-weight core),
so the three near-1 eigenvalues solve
   det( H0 - eps (I + H1) + eps^2 H2 - ... ) = 0,
   Hk = M_GR Q^{k+1} M_RG  (exact polynomial matrices in t).

Solves the chiral 2x2 + spectator system as Puiseux series in u = sqrt(t)
by formal Newton iteration on the full determinant (sympy, exact rationals),
yielding the EXACT amplitude series

   Delta e^{3 beta/2} = A(u) = a0 + a1 u + a2 u^2 + ...

valid to the stated order with no lambda=1 truncation bias.

Expected: a0 = 1, a1 = 1/2, a2 = 1/8 (unchanged), exact a3, a4 (new).
"""

import json
import os
import signal
import sys
from fractions import Fraction

import sympy as sp

TIMEOUT_SECONDS = 900

def _timeout(s, f):
    print("TIMEOUT reached. Exiting.")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

Q7 = 7
DEG = 8
GS = [0, 1, 5]

def p_gf7(L, C, R):
    return (C + R - C * R - L * C * R) % Q7

def pzero():
    return [Fraction(0)] * (DEG + 1)

def pmono(k, c=1):
    v = pzero()
    if k <= DEG:
        v[k] = Fraction(c)
    return v

def padd(a, b):
    return [x + y for x, y in zip(a, b)]

def pmul(a, b):
    out = pzero()
    for i, ai in enumerate(a):
        if ai == 0:
            continue
        for j, bj in enumerate(b):
            if bj == 0 or i + j > DEG:
                continue
            out[i + j] += ai * bj
    return out

def mat_mul(A, B):
    n, m, k = len(A), len(B[0]), len(B)
    out = [[pzero() for _ in range(m)] for _ in range(n)]
    for i in range(n):
        for l in range(k):
            a = A[i][l]
            if all(c == 0 for c in a):
                continue
            for j in range(m):
                b = B[l][j]
                if all(c == 0 for c in b):
                    continue
                out[i][j] = padd(out[i][j], pmul(a, b))
    return out

def mat_add(A, B):
    return [[padd(x, y) for x, y in zip(ra, rb)] for ra, rb in zip(A, B)]

nodes = [(a, b) for a in range(Q7) for b in range(Q7)]
G = [(g, g) for g in GS]
R = [v for v in nodes if v not in G]
gi = {v: i for i, v in enumerate(G)}
ri = {v: i for i, v in enumerate(R)}
nR = len(R)

def edge_weight(u, v):
    a, b = u
    bb, c = v
    if b != bb:
        return None
    return p_gf7(a, b, c)

M_GR = [[pzero() for _ in R] for _ in G]
M_RG = [[pzero() for _ in G] for _ in R]
M_RR = [[pzero() for _ in R] for _ in R]
for uu in nodes:
    for vv in nodes:
        w = edge_weight(uu, vv)
        if w is None:
            continue
        if uu in gi and vv in gi:
            continue
        elif uu in gi:
            M_GR[gi[uu]][ri[vv]] = padd(M_GR[gi[uu]][ri[vv]], pmono(w))
        elif vv in gi:
            M_RG[ri[uu]][gi[vv]] = padd(M_RG[ri[uu]][gi[vv]], pmono(w))
        else:
            M_RR[ri[uu]][ri[vv]] = padd(M_RR[ri[uu]][ri[vv]], pmono(w))

# Q = (I - M_RR)^{-1} via nilpotent core + t-adic Neumann series
Nint = [[1 if M_RR[i][j][0] != 0 else 0 for j in range(nR)] for i in range(nR)]
InvIN = [[Fraction(1 if i == j else 0) for j in range(nR)] for i in range(nR)]
Pk = [[Fraction(1 if i == j else 0) for j in range(nR)] for i in range(nR)]
Nfr = [[Fraction(x) for x in row] for row in Nint]
k = 0
while True:
    k += 1
    Pk = [[sum(Pk[i][l] * Nfr[l][j] for l in range(nR)) for j in range(nR)]
          for i in range(nR)]
    if all(all(x == 0 for x in row) for row in Pk):
        break
    InvIN = [[InvIN[i][j] + Pk[i][j] for j in range(nR)] for i in range(nR)]
print(f"nilpotency index: {k + 1}")
InvIN_poly = [[pmono(0, InvIN[i][j]) if InvIN[i][j] != 0 else pzero()
               for j in range(nR)] for i in range(nR)]
W = [[M_RR[i][j][:] for j in range(nR)] for i in range(nR)]
for i in range(nR):
    for j in range(nR):
        W[i][j][0] = Fraction(0)
KW = mat_mul(InvIN_poly, W)
Qres = [[InvIN_poly[i][j][:] for j in range(nR)] for i in range(nR)]
term = [[InvIN_poly[i][j][:] for j in range(nR)] for i in range(nR)]
for j in range(1, DEG + 1):
    term = mat_mul(KW, term)
    Qres = mat_add(Qres, term)

# Hk = M_GR Q^{k+1} M_RG for k = 0, 1, 2, 3
Hs = []
Qpow = Qres
for kk in range(4):
    Hs.append(mat_mul(mat_mul(M_GR, Qpow), M_RG))
    if kk < 3:
        Qpow = mat_mul(Qpow, Qres)

u = sp.Symbol('u', positive=True)
eps = sp.Symbol('eps')
ORD = 10

def to_sympy(poly):
    return sum(sp.Rational(c.numerator, c.denominator) * u**(2 * kx)
               for kx, c in enumerate(poly) if c != 0)

def trunc(e, n=ORD):
    return sp.expand(sp.series(sp.expand(e), u, 0, n).removeO())

H0 = sp.Matrix(3, 3, lambda i, j: to_sympy(Hs[0][i][j]))
H1 = sp.Matrix(3, 3, lambda i, j: to_sympy(Hs[1][i][j]))
H2 = sp.Matrix(3, 3, lambda i, j: to_sympy(Hs[2][i][j]))
H3 = sp.Matrix(3, 3, lambda i, j: to_sympy(Hs[3][i][j]))
Ieye = sp.eye(3)

Mfull = H0 - eps * (Ieye + H1) + eps**2 * H2 - eps**3 * H3
P = sp.expand(Mfull.det())
Pp = sp.diff(P, eps)

def series_inverse(expr):
    c0 = expr.subs(u, 0)
    g = sp.expand(expr / c0 - 1)
    inv = sp.Integer(1)
    gp = sp.Integer(1)
    for kx in range(1, ORD):
        gp = trunc(gp * (-g))
        inv = sp.expand(inv + gp)
    return trunc(inv / c0)

def newton_root(start, iters=8):
    x = start
    for _ in range(iters):
        num = trunc(P.subs(eps, x), ORD + 6)
        den = trunc(Pp.subs(eps, x), ORD + 6)
        if num == 0:
            return x
        pn = sp.Poly(num, u)
        pd = sp.Poly(den, u)
        vd = min(m[0] for m in pd.monoms())
        num2 = sp.expand(sp.cancel(num / u**vd))
        den2 = sp.expand(sp.cancel(den / u**vd))
        corr = trunc(num2 * series_inverse(den2))
        x = trunc(x - corr)
    return x

# Newton from the three known leading behaviors
eps_plus = newton_root(u**3)
eps_minus = newton_root(-u**3)
eps_spec = newton_root(2 * u**8)
print(f"eps_plus      = {eps_plus}")
print(f"eps_minus     = {eps_minus}")
print(f"eps_spectator = {eps_spec}")

# residual check on the full determinant
for name, root in [("plus", eps_plus), ("minus", eps_minus), ("spec", eps_spec)]:
    resid = trunc(P.subs(eps, root), ORD + 4)
    if resid == 0:
        print(f"residual eps_{name}: 0 (to working order) PASS")
    else:
        pol = sp.Poly(resid, u)
        val = min(m[0] for m in pol.monoms())
        print(f"residual eps_{name}: O(u^{val})  "
              f"({'PASS' if val >= ORD else 'CHECK'})")

lam1 = 1 + eps_plus
lam2 = 1 + eps_spec
Delta = trunc(sp.log(lam1).series(u, 0, ORD).removeO()
              - sp.log(lam2).series(u, 0, ORD).removeO())
Aser = trunc(sp.expand(Delta / u**3), ORD - 3)
print(f"\nDelta(u) = {Delta}")
print(f"A(u) = {Aser}")
coeffs = {kx: sp.nsimplify(Aser.coeff(u, kx)) for kx in range(0, ORD - 3)}
print("\nEXACT amplitude coefficients (self-consistent):")
for kx, c in coeffs.items():
    print(f"  a_{kx} = {c}")

signal.alarm(0)

out = {
    "eps_plus": str(eps_plus), "eps_minus": str(eps_minus),
    "eps_spectator": str(eps_spec),
    "Delta_series": str(Delta), "A_series": str(Aser),
    "A_coeffs": {str(kx): str(c) for kx, c in coeffs.items()},
    "method": "Schur complement with full resolvent lambda-dependence "
              "(Q - eps Q^2 + eps^2 Q^3 - eps^3 Q^4), exact rationals",
}
_out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "spin7_gap_amplitude_selfconsistent.json")
with open(_out_path, "w") as f:
    json.dump(out, f, indent=2)
print("\nSaved", _out_path)
