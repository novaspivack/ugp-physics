"""Exact analytic derivation of the spin-7 transfer-matrix gap amplitude.

The 49x49 pair transfer matrix M(t)[(a,b),(b,c)] = t^p(a,b,c), t = e^(-beta),
p(L,C,R) = (C+R-CR-LCR) mod 7, has a 3-fold degenerate Perron multiplet at
t = 0 carried by the ground self-loops G = {(0,0),(1,1),(5,5)}.

This script performs the degenerate perturbation theory EXACTLY (rational
arithmetic, no floats, no fits):
  1. Splits states into G (3) and R (46); verifies M_GG = I exactly.
  2. Verifies the zero-weight digraph restricted to R is NILPOTENT (the
     certified rigidity structure: only cycles are the three uniform loops).
  3. Computes the Schur-complement effective 3x3 matrix
        H(t) = M_GG - I + M_GR (I - M_RR)^{-1} M_RG
     as exact truncated polynomials in t, using the t-adic Neumann series
     (I - M_RR)^{-1} = sum_j [(I-N)^{-1} W]^j (I-N)^{-1},  W = M_RR - N,
     which is finite order-by-order because N is nilpotent and val(W) >= 1.
  4. Reads off the exact integer through-R wall counts c10 (1->0, weight 1),
     c01 (0->1, weight 2) and bump counts b0, b1, b5.
  5. Solves the 3x3 characteristic polynomial as Puiseux series in
     u = sqrt(t) by formal Newton iteration; extracts
        lambda_1 = 1 + A u^3 + ...,   A = sqrt(c10*c01),
     the spectator eigenvalue lambda_2 = 1 + b5 t^4 + ..., and the gap
        Delta = ln(lambda_1/lambda_2) = A t^{3/2} (1 + (b0/2) t^{1/2} + O(t)).

Expected output: c10 = c01 = 1, hence amplitude A = 1 exactly; exact
integer b0 (correction coefficient b0/2); full Puiseux series printed.
"""

import json
import os
import signal
import sys
from fractions import Fraction

TIMEOUT_SECONDS = 600

def _timeout(s, f):
    print("TIMEOUT reached. Exiting.")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

Q = 7
DEG = 7          # truncation degree in t for the resolvent algebra
GS = [0, 1, 5]

def p_gf7(L, C, R):
    return (C + R - C * R - L * C * R) % Q

# ---------------------------------------------------------------- poly algebra
# polynomial in t = list of Fraction coefficients, index = power, len DEG+1
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
        Ai = A[i]
        for l in range(k):
            a = Ai[l]
            if all(c == 0 for c in a):
                continue
            Bl = B[l]
            for j in range(m):
                b = Bl[j]
                if all(c == 0 for c in b):
                    continue
                out[i][j] = padd(out[i][j], pmul(a, b))
    return out

def mat_add(A, B):
    return [[padd(x, y) for x, y in zip(ra, rb)] for ra, rb in zip(A, B)]

# ---------------------------------------------------------------- state split
nodes = [(a, b) for a in range(Q) for b in range(Q)]
G = [(g, g) for g in GS]
R = [v for v in nodes if v not in G]
gi = {v: i for i, v in enumerate(G)}
ri = {v: i for i, v in enumerate(R)}
nR = len(R)
print(f"|G| = {len(G)}, |R| = {nR}")

def edge_weight(u, v):
    """t-power of edge u -> v, or None if no de Bruijn overlap."""
    a, b = u
    bb, c = v
    if b != bb:
        return None
    return p_gf7(a, b, c)

# blocks as polynomial matrices
M_GG = [[pzero() for _ in G] for _ in G]
M_GR = [[pzero() for _ in R] for _ in G]
M_RG = [[pzero() for _ in G] for _ in R]
M_RR = [[pzero() for _ in R] for _ in R]
for u in nodes:
    for v in nodes:
        w = edge_weight(u, v)
        if w is None:
            continue
        if u in gi and v in gi:
            M_GG[gi[u]][gi[v]] = padd(M_GG[gi[u]][gi[v]], pmono(w))
        elif u in gi:
            M_GR[gi[u]][ri[v]] = padd(M_GR[gi[u]][ri[v]], pmono(w))
        elif v in gi:
            M_RG[ri[u]][gi[v]] = padd(M_RG[ri[u]][gi[v]], pmono(w))
        else:
            M_RR[ri[u]][ri[v]] = padd(M_RR[ri[u]][ri[v]], pmono(w))

# check M_GG = I exactly
ok_GG = all(M_GG[i][j] == (pmono(0) if i == j else pzero())
            for i in range(3) for j in range(3))
print(f"M_GG == I exactly: {ok_GG}")
assert ok_GG

# ---------------------------------------------------------------- nilpotency
# N = M_RR at t = 0 (zero-weight edges within R), as integer 0/1 matrix
Nint = [[1 if M_RR[i][j][0] != 0 else 0 for j in range(nR)] for i in range(nR)]

def imat_mul(A, B):
    n = len(A)
    return [[sum(A[i][k] * B[k][j] for k in range(n)) for j in range(n)]
            for i in range(n)]

Pk = [row[:] for row in Nint]
nil_index = None
for k in range(2, nR + 2):
    Pk = imat_mul(Pk, Nint)
    if all(all(x == 0 for x in row) for row in Pk):
        nil_index = k
        break
print(f"N (zero-weight digraph on R) nilpotent: N^{nil_index} = 0")
assert nil_index is not None

# ---------------------------------------------------------------- resolvent
# (I - N)^{-1} = sum_{k < nil_index} N^k  (integer matrix)
InvIN = [[Fraction(1 if i == j else 0) for j in range(nR)] for i in range(nR)]
Pk = [[Fraction(1 if i == j else 0) for j in range(nR)] for i in range(nR)]
Nfr = [[Fraction(x) for x in row] for row in Nint]
for k in range(1, nil_index):
    Pk = [[sum(Pk[i][l] * Nfr[l][j] for l in range(nR)) for j in range(nR)]
          for i in range(nR)]
    InvIN = [[InvIN[i][j] + Pk[i][j] for j in range(nR)] for i in range(nR)]
InvIN_poly = [[pmono(0, InvIN[i][j]) if InvIN[i][j] != 0 else pzero()
               for j in range(nR)] for i in range(nR)]

# W = M_RR - N (positive t-valuation)
W = [[M_RR[i][j][:] for j in range(nR)] for i in range(nR)]
for i in range(nR):
    for j in range(nR):
        W[i][j][0] = Fraction(0)

# Qres = (I - M_RR)^{-1} = sum_j (InvIN W)^j InvIN, truncated at t^DEG
KW = mat_mul(InvIN_poly, W)          # valuation >= 1
Qres = [[InvIN_poly[i][j][:] for j in range(nR)] for i in range(nR)]
term = [[InvIN_poly[i][j][:] for j in range(nR)] for i in range(nR)]
for j in range(1, DEG + 1):
    term = mat_mul(KW, term)
    Qres = mat_add(Qres, term)

# H = M_GR Qres M_RG  (the M_GG - I part is zero)
H = mat_mul(mat_mul(M_GR, Qres), M_RG)

print("\n=== Effective 3x3 matrix H(t) [rows/cols = sectors 0,1,5; H[g][g'] = hop g->g'] ===")
sector_names = ["0", "1", "5"]
H_str = {}
for i in range(3):
    for j in range(3):
        terms = [f"{str(c)}*t^{k}" for k, c in enumerate(H[i][j]) if c != 0]
        s = " + ".join(terms) if terms else "0"
        H_str[f"{sector_names[i]}->{sector_names[j]}"] = s
        print(f"  H[{sector_names[i]}->{sector_names[j]}] = {s}")

c10 = H[1][0][1]   # through-R hop 1 -> 0, coefficient of t^1
c01 = H[0][1][2]   # through-R hop 0 -> 1, coefficient of t^2
b0 = H[0][0][2]    # sector-0 bump, coefficient of t^2
b1 = H[1][1][3]    # sector-1 bump, coefficient of t^3
b5 = H[2][2][4]    # sector-5 bump, coefficient of t^4
print(f"\nExact integer structure constants:")
print(f"  c10 (minimal through-R walls 1->0, weight 1) = {c10}")
print(f"  c01 (minimal through-R walls 0->1, weight 2) = {c01}")
print(f"  b0  (sector-0 bumps, weight 2)               = {b0}")
print(f"  b1  (sector-1 bumps, weight 3)               = {b1}")
print(f"  b5  (sector-5 bumps, weight 4)               = {b5}")

# ---------------------------------------------------------------- Puiseux
import sympy as sp

u = sp.Symbol('u', positive=True)   # u = sqrt(t)
ORD = 8                              # work modulo u^ORD

def to_sympy(poly):
    return sum(sp.Rational(c.numerator, c.denominator) * u**(2 * k)
               for k, c in enumerate(poly) if c != 0)

Hs = [[sp.expand(to_sympy(H[i][j])) for j in range(3)] for i in range(3)]
eps = sp.Symbol('eps')
# char poly of H^T acting on sector amplitudes; eigenvalues unaffected
Mch = sp.Matrix(3, 3, lambda i, j: Hs[i][j] - (eps if i == j else 0))
P = sp.expand(Mch.det())
Pp = sp.diff(P, eps)

def series_trunc(expr, n=ORD):
    return sp.expand(sp.series(sp.expand(expr), u, 0, n).removeO())

def newton_root(start, iters=6):
    x = start
    for _ in range(iters):
        num = series_trunc(P.subs(eps, x))
        den = series_trunc(Pp.subs(eps, x))
        # formal division as series in u
        corr = series_trunc(sp.expand(num / den).rewrite(sp.Pow))
        # robust: multiply by series inverse of den
        d0 = den.subs(u, 0)
        if d0 == 0:
            # factor lowest power of u
            pol_n = sp.Poly(num, u)
            pol_d = sp.Poly(den, u)
            vn = min(m[0] for m in pol_n.monoms()) if pol_n.monoms() else ORD
            vd = min(m[0] for m in pol_d.monoms())
            num2 = sp.expand(num / u**vd)
            den2 = sp.expand(den / u**vd)
            corr = series_trunc(num2 * series_inverse(den2))
        else:
            corr = series_trunc(num * series_inverse(den))
        x = series_trunc(x - corr)
    return x

def series_inverse(expr):
    """1/expr as series in u, expr(0) != 0."""
    c0 = expr.subs(u, 0)
    g = sp.expand(expr / c0 - 1)
    inv = sp.Integer(1)
    gp = sp.Integer(1)
    for k in range(1, ORD):
        gp = series_trunc(gp * (-g))
        inv = sp.expand(inv + gp)
    return series_trunc(inv / c0)

A_lead = sp.sqrt(sp.Rational(int(c10 * c01)))
roots = {}
for name, start in [("plus", A_lead * u**3), ("minus", -A_lead * u**3),
                    ("spectator", sp.Rational(int(b5)) * u**8 if b5 != 0 else u**8)]:
    roots[name] = newton_root(start)
    print(f"\neps_{name} = {sp.nsimplify(roots[name])}")

lam1 = 1 + roots["plus"]
lam2 = 1 + roots["spectator"]
Delta = series_trunc(sp.log(lam1) - sp.log(lam2))
# A(beta) = Delta / u^3 as series in u
Aser = series_trunc(sp.expand(Delta / u**3), ORD - 3)
print(f"\nGap series:  Delta = {sp.nsimplify(Delta)}")
print(f"Amplitude series:  A(u) = Delta * t^(-3/2) = {sp.nsimplify(Aser)}")
A0 = Aser.subs(u, 0)
A1 = sp.diff(Aser, u).subs(u, 0)
A2 = (sp.diff(Aser, u, 2) / 2).subs(u, 0)
print(f"\n*** AMPLITUDE A = {A0}  (exact) ***")
print(f"*** correction:  A(beta) = {A0} + {A1} e^(-beta/2) + {A2} e^(-beta) + ... ***")

signal.alarm(0)

out = {
    "ground_states": [list(g) for g in G],
    "nR": nR,
    "M_GG_is_identity": ok_GG,
    "nilpotency_index": nil_index,
    "H_effective": H_str,
    "structure_constants": {
        "c10": str(c10), "c01": str(c01),
        "b0": str(b0), "b1": str(b1), "b5": str(b5)},
    "amplitude_exact": str(A0),
    "amplitude_series_coeffs": {"u0": str(A0), "u1": str(A1), "u2": str(A2)},
    "eigenvalue_series": {k: str(sp.nsimplify(v)) for k, v in roots.items()},
    "law": "Delta(beta) = A e^(-3beta/2) (1 + (b0/2) e^(-beta/2) + O(e^-beta)), "
           "A = sqrt(c10*c01)",
}
_out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "spin7_gap_amplitude_resolvent.json")
with open(_out_path, "w") as f:
    json.dump(out, f, indent=2)
print("\nSaved", _out_path)
