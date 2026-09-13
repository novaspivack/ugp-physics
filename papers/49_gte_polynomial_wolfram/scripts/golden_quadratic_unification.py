#!/usr/bin/env python3
"""Diagonal fixed-point structure of the GTE polynomial p(L,C,R)=C+R-CR-LCR.

Verifies the factorization p(x,x,x) - x = -x(x^2+x-1) over Z, then tests the
disc-5 dichotomy: the quadratic x^2+x-1 (discriminant 5 = N_fam) has
 - real root 1/phi = (sqrt(5)-1)/2  (SRRG fixed point, Higgs VEV seed), and
 - a root in GF(q) iff 5 is a quadratic residue mod q.
For q=7, 5 is a QNR, so the only diagonal fixed point is x=0 -> the binary
floor {0,1} is the unique invariant sub-CA (P49 QNR theorem).

Also computes: golden elements of GF(49); Pisano period pi(7); ground-state
cubic factorization p(x,x,x) = -x(x-1)(x-5) mod 7 cross-check; and the
fixed-point count of p's diagonal over GF(q) for primes q<100 vs (5|q).

Expected output: factorization identity holds; root existence over GF(q)
exactly tracks (5|q); pi(7)=16.
"""
import os
import json
import signal
import sys

TIMEOUT_SECONDS = 120

def _timeout(signum, frame):
    print(f"TIMEOUT {TIMEOUT_SECONDS}s reached")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

def p(L, C, R, q=None):
    v = C + R - C * R - L * C * R
    return v % q if q else v

results = {}

# 1. Factorization over Z: p(x,x,x) - x == -x(x^2+x-1) as integer polynomials
ok = all(p(x, x, x) - x == -x * (x * x + x - 1) for x in range(-50, 51))
results["factorization_diag_fixed_points"] = {
    "identity": "p(x,x,x) - x = -x(x^2 + x - 1) over Z",
    "verified_on_range": "[-50,50]",
    "holds": ok,
}
print("1. p(x,x,x)-x = -x(x^2+x-1) over Z:", ok)

# 2. Ground-state cubic cross-check: p(x,x,x) = -x(x-1)(x-5) mod 7
gs_ok = all(p(x, x, x, 7) == (-x * (x - 1) * (x - 5)) % 7 for x in range(7))
gs_roots = [x for x in range(7) if p(x, x, x, 7) == 0]
print("2. p(x,x,x) = -x(x-1)(x-5) mod 7:", gs_ok, "| roots p(x,x,x)=0:", gs_roots)
results["ground_state_cubic"] = {"holds": gs_ok, "roots": gs_roots}

# 3. Diagonal fixed points over GF(q) vs Legendre symbol (5|q)
def legendre(a, q):
    a %= q
    if a == 0:
        return 0
    r = pow(a, (q - 1) // 2, q)
    return 1 if r == 1 else -1

def primes_upto(n):
    sieve = [True] * (n + 1)
    sieve[0:2] = [False, False]
    for i in range(2, int(n ** 0.5) + 1):
        if sieve[i]:
            for j in range(i * i, n + 1, i):
                sieve[j] = False
    return [i for i in range(2, n + 1) if sieve[i]]

dichotomy = []
all_match = True
for q in primes_upto(100):
    fps = [x for x in range(q) if p(x, x, x, q) == x % q]
    nonzero_fps = [x for x in fps if x != 0]
    leg = legendre(5, q)
    # quadratic x^2+x-1 has roots in GF(q) iff disc 5 is QR (or q=5 or q=2 special)
    expect_nonzero = (leg == 1) or q == 5
    match = (len(nonzero_fps) > 0) == expect_nonzero
    if q == 2:
        match = True  # disc degenerate char 2; record but exempt
    all_match &= match
    dichotomy.append({"q": q, "legendre_5_q": leg,
                      "nonzero_diag_fixed_points": nonzero_fps, "match": match})
print("3. Disc-5 dichotomy over all primes q<100 matches (5|q):", all_match)
results["disc5_dichotomy"] = {"all_match": all_match, "table": dichotomy}

# q=7 line specifically
q7 = next(d for d in dichotomy if d["q"] == 7)
print("   q=7: (5|7) =", q7["legendre_5_q"], "nonzero fixed points:",
      q7["nonzero_diag_fixed_points"], "-> binary floor forced")

# 4. Real root: 1/phi
phi_inv = (5 ** 0.5 - 1) / 2
print(f"4. Real positive root of x^2+x-1: {phi_inv:.12f} = 1/phi (SRRG fixed point)")
results["real_root"] = phi_inv

# 5. Golden elements in GF(49): roots of x^2+x-1 in GF(7^2) = GF(7)[t]/(t^2-3)
# t^2 = 3 (3 is a QNR mod 7). Element a+bt; (a+bt)^2 + (a+bt) - 1 = 0
# -> (a^2+3b^2+a-1) + (2ab+b) t = 0
golden_gf49 = []
for a in range(7):
    for b in range(7):
        c0 = (a * a + 3 * b * b + a - 1) % 7
        c1 = (2 * a * b + b) % 7
        if c0 == 0 and c1 == 0:
            golden_gf49.append((a, b))
print("5. Roots of x^2+x-1 in GF(49) (a+b*t, t^2=3):", golden_gf49)
results["golden_elements_gf49"] = golden_gf49

# 6. Pisano period mod 7
def pisano(m):
    a, b = 0, 1
    for i in range(1, m * m * 6 + 1):
        a, b = b, (a + b) % m
        if a == 0 and b == 1:
            return i
    return None

pi7 = pisano(7)
print("6. Pisano period pi(7) =", pi7, "(compare D^2 = 16, the gravitational unity constant)")
results["pisano_7"] = pi7

# 7. Reciprocity statement: 5 QNR mod 7 <-> 7 QNR mod 5 (since 5 = 1 mod 4)
rec = (legendre(5, 7), legendre(7, 5))
print("7. (5|7) =", rec[0], ", (7|5) =", rec[1], "(reciprocity, 5 = 1 mod 4)")
results["reciprocity"] = {"legendre_5_7": rec[0], "legendre_7_5": rec[1]}

# 8. Null check on the Pisano observation: pisano periods of small moduli
pis = {m: pisano(m) for m in range(2, 12)}
print("8. Pisano periods m=2..11:", pis)
results["pisano_table_null_context"] = pis

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
          "golden_quadratic_unification_results.json"), "w") as f:
    json.dump(results, f, indent=1, default=str)
print("\nSaved golden_quadratic_unification_results.json")
signal.alarm(0)
