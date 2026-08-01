#!/usr/bin/env python3
"""Eisenstein/motivic structure of the GTE polynomial zero variety V(p).

p(L,C,R) = C + R - C*R - L*C*R.

Verifies:
  (1) |V(p)(GF(q))| = q^2 - q + 1 = Phi_6(q) = N(q + omega) for ALL prime
      powers q <= 49 (including genuine extension fields GF(4), GF(8), GF(9),
      GF(16), GF(25), GF(27), GF(32), GF(49)), extending the P49 prime-only
      computational check to the full prime-power statement.
  (2) The scissor decomposition behind the motivic identity
      [V(p)] = L + (L-1)^2 = Phi_6(L) in K0(Var):
      stratum A (R=0, C=0) has exactly q points; stratum B (R != 0,
      1 - R(1+L) != 0) has exactly (q-1)^2; stratum C is empty.
  (3) Zeta consistency: N_m = Phi_6(q0^m) for q0 in {2,3,5,7}, m = 1,2
      (using the extension-field counts), matching
      Z(V,t) = (1-q0 t)/((1-t)(1-q0^2 t)).
  (4) Pointwise symmetry scan at q = 7: which affine-diagonal maps
      (L,C,R) -> (aL+b, cC+d, eR+f) preserve V(p)(GF(7)) as a set
      (full 6^3*7^3 = 74,088 scan), and is the mu_3 cubic-residue scaling
      (L,C,R) -> (4L,4C,4R) among them?  Honest test of whether the
      Eisenstein structure exists pointwise or only at the counting level.

Expected output: counts match Phi_6(q) for all q; strata counts (q, (q-1)^2);
symmetry group report at q=7.
"""
import os
import json
import signal
import sys
from itertools import product

TIMEOUT_SECONDS = 600

def _timeout(signum, frame):
    print(f"TIMEOUT {TIMEOUT_SECONDS}s reached")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

# ---------------- finite field GF(p^k) via polynomial quotient -------------
def is_prime(n):
    if n < 2:
        return False
    i = 2
    while i * i <= n:
        if n % i == 0:
            return False
        i += 1
    return True

def poly_mul_mod(u, v, mod_poly, p):
    k = len(mod_poly) - 1
    out = [0] * (len(u) + len(v) - 1)
    for i, a in enumerate(u):
        if a:
            for j, b in enumerate(v):
                out[i + j] = (out[i + j] + a * b) % p
    # reduce by mod_poly (monic, degree k)
    for i in range(len(out) - 1, k - 1, -1):
        c = out[i]
        if c:
            for j in range(k + 1):
                out[i - k + j] = (out[i - k + j] - c * mod_poly[j]) % p
    return tuple(out[:k])

def find_irreducible(p, k):
    """Smallest monic irreducible polynomial of degree k over GF(p),
    coefficients low->high, by brute force root/factor test."""
    if k == 1:
        return [0, 1]
    for tail in product(range(p), repeat=k):
        poly = list(tail) + [1]
        if poly[0] == 0:
            continue
        # irreducible iff no factor of degree <= k//2; test by gcd with
        # x^(p^d) - x  -> simpler: brute-force check no monic factor deg<=k//2
        if _is_irreducible(poly, p):
            return poly
    raise RuntimeError("no irreducible found")

def _poly_divmod(num, den, p):
    num = list(num)
    dl = len(den) - 1
    while len(num) - 1 >= dl and any(num):
        if num[-1] == 0:
            num.pop()
            continue
        c = (num[-1] * pow(den[-1], -1, p)) % p
        shift = len(num) - 1 - dl
        for i in range(len(den)):
            num[shift + i] = (num[shift + i] - c * den[i]) % p
        while num and num[-1] == 0:
            num.pop()
    return num  # remainder

def _is_irreducible(poly, p):
    k = len(poly) - 1
    for d in range(1, k // 2 + 1):
        for tail in product(range(p), repeat=d):
            den = list(tail) + [1]
            rem = _poly_divmod(poly, den, p)
            if not rem:
                return False
    return True

class GF:
    def __init__(self, p, k):
        self.p, self.k = p, k
        self.q = p ** k
        self.mod_poly = find_irreducible(p, k)
        self.elems = [tuple(t) for t in product(range(p), repeat=k)]
        self.zero = tuple([0] * k)
        self.one = tuple([1] + [0] * (k - 1))

    def add(self, u, v):
        return tuple((a + b) % self.p for a, b in zip(u, v))

    def sub(self, u, v):
        return tuple((a - b) % self.p for a, b in zip(u, v))

    def mul(self, u, v):
        return poly_mul_mod(list(u), list(v), self.mod_poly, self.p)

# ---------------- the GTE polynomial over any GF ---------------------------
def p_val(F, L, C, R):
    CR = F.mul(C, R)
    LCR = F.mul(L, CR)
    return F.sub(F.sub(F.add(C, R), CR), LCR)

def phi6(q):
    return q * q - q + 1

prime_powers = []
for q in range(2, 50):
    # smallest prime factor of q
    p = next(d for d in range(2, q + 1) if q % d == 0)
    if is_prime(p):
        k = 0
        qq = q
        while qq % p == 0:
            qq //= p
            k += 1
        if qq == 1 and k >= 1:
            prime_powers.append((q, p, k))

count_table = []
all_ok = True
strata_ok = True
for q, p, k in prime_powers:
    F = GF(p, k)
    n_total = 0
    n_A = 0   # R=0, C=0
    n_B = 0   # R!=0, 1-R(1+L) != 0
    n_C = 0   # R!=0, 1-R(1+L) == 0 (must contribute 0)
    for L in F.elems:
        for C in F.elems:
            for R in F.elems:
                if p_val(F, L, C, R) == F.zero:
                    n_total += 1
                    if R == F.zero:
                        n_A += 1
                    else:
                        u = F.sub(F.one, F.mul(R, F.add(F.one, L)))
                        if u != F.zero:
                            n_B += 1
                        else:
                            n_C += 1
    ok = n_total == phi6(q)
    s_ok = (n_A == q and n_B == (q - 1) ** 2 and n_C == 0)
    all_ok &= ok
    strata_ok &= s_ok
    count_table.append({"q": q, "p": p, "k": k, "count": n_total,
                        "phi6": phi6(q), "match": ok,
                        "stratum_A": n_A, "stratum_B": n_B, "stratum_C": n_C,
                        "strata_match": s_ok})
    print(f"q={q:>2} (GF({p}^{k})): |V| = {n_total:>4}  Phi6(q) = {phi6(q):>4}"
          f"  {'OK' if ok else 'MISMATCH'}   strata A={n_A} B={n_B} C={n_C}"
          f" {'OK' if s_ok else 'MISMATCH'}")

print(f"\nAll prime powers q<=49 match Phi_6(q): {all_ok}")
print(f"All scissor strata match (q, (q-1)^2, 0): {strata_ok}")

# (3) zeta consistency N_m = Phi6(q0^m)
zeta_ok = True
for q0 in (2, 3, 5, 7):
    for m in (1, 2):
        qm = q0 ** m
        row = next(r for r in count_table if r["q"] == qm)
        if row["count"] != phi6(qm):
            zeta_ok = False
print(f"Zeta consistency N_m = Phi6(q0^m) for q0 in {{2,3,5,7}}, m=1,2: {zeta_ok}")

# (4) symmetry scan at q = 7 ------------------------------------------------
q = 7
V7 = frozenset((L, C, R) for L in range(7) for C in range(7) for R in range(7)
               if (C + R - C * R - L * C * R) % 7 == 0)
print(f"\n|V(p)(GF(7))| = {len(V7)}")

syms = []
units = [1, 2, 3, 4, 5, 6]
for a in units:
    for b in range(7):
        # precompute maps for L coordinate
        for c in units:
            for d in range(7):
                for e in units:
                    for f in range(7):
                        ok = True
                        for (L, C, R) in V7:
                            t = ((a * L + b) % 7, (c * C + d) % 7,
                                 (e * R + f) % 7)
                            if t not in V7:
                                ok = False
                                break
                        if ok:
                            syms.append((a, b, c, d, e, f))

print(f"Affine-diagonal symmetries of V(p)(GF(7)): {len(syms)} found")
for s in syms[:20]:
    print(f"  (L,C,R) -> ({s[0]}L+{s[1]}, {s[2]}C+{s[3]}, {s[4]}R+{s[5]})")
mu3_scaling_in = (4, 0, 4, 0, 4, 0) in syms
print(f"mu_3 scaling (4L,4C,4R) preserves V: {mu3_scaling_in}")

# (5) torus action g_u: (L,C,R) -> (uL+u-1, C/u, R/u), p o g_u = p/u --------
print("\nTorus action analysis g_u: (L,C,R) -> (uL+u-1, C/u, R/u)")
equivariance_ok = True
for qq in (5, 7, 11, 13):
    for u in range(1, qq):
        ui = pow(u, -1, qq)
        for L in range(qq):
            for C in range(qq):
                for R in range(qq):
                    lhs = (C * ui + R * ui
                           - ui * C * ui * R
                           - (u * L + u - 1) * ui * C * ui * R) % qq
                    rhs = (ui * (C + R - C * R - L * C * R)) % qq
                    if lhs != rhs:
                        equivariance_ok = False
print(f"  p(g_u(x)) = u^-1 p(x) for q in {{5,7,11,13}}, all u, all x: "
      f"{equivariance_ok}")

orbit_summary = {}
freeness_ok = True
for qq in (3, 5, 7, 11, 13):
    Vq = [(L, C, R) for L in range(qq) for C in range(qq) for R in range(qq)
          if (C + R - C * R - L * C * R) % qq == 0]
    Vset = set(Vq)
    ether = ((qq - 1) % qq, 0, 0)
    assert ether in Vset
    # orbit decomposition
    seen = set()
    orbits = []
    for x in Vq:
        if x in seen:
            continue
        orb = set()
        for u in range(1, qq):
            ui = pow(u, -1, qq)
            y = ((u * x[0] + u - 1) % qq, (ui * x[1]) % qq, (ui * x[2]) % qq)
            orb.add(y)
        orbits.append(len(orb))
        seen |= orb
    fixed = [n for n in orbits if n == 1]
    free = [n for n in orbits if n == qq - 1]
    ok = (len(fixed) == 1 and len(free) == qq and
          len(fixed) + len(free) == len(orbits))
    freeness_ok &= ok
    orbit_summary[qq] = {"n_points": len(Vq), "fixed_orbits": len(fixed),
                         "free_orbits": len(free),
                         "decomposition_1_plus_q_free": ok}
    print(f"  q={qq:>2}: |V|={len(Vq):>4} = {len(fixed)} fixed (ether) + "
          f"{len(free)} free orbits of size {qq-1}  "
          f"{'OK' if ok else 'MISMATCH'}")

# unit group reduction: mu_6 = <-omega> -> GF(7)*, -omega -> -4 = 3 (prim root)
mu6_gen_image = (-4) % 7
prim_root = all(pow(mu6_gen_image, k, 7) != 1 for k in range(1, 6))
print(f"  mu_6 generator -omega maps to {mu6_gen_image} mod pi; primitive "
      f"root mod 7: {prim_root}")

# also test coordinate permutations (combined with identity affine part)
perm_results = {}
for name, perm in [("LCR->RCL", lambda t: (t[2], t[1], t[0])),
                   ("LCR->CLR", lambda t: (t[1], t[0], t[2])),
                   ("LCR->LRC", lambda t: (t[0], t[2], t[1]))]:
    perm_results[name] = all(perm(x) in V7 for x in V7)
print(f"Coordinate permutation symmetries: {perm_results}")

results = {
    "polynomial": "p(L,C,R) = C + R - CR - LCR",
    "count_table": count_table,
    "all_prime_powers_match_phi6": bool(all_ok),
    "scissor_strata_match": bool(strata_ok),
    "motivic_identity": "[V(p)] = L + (L-1)^2 = L^2 - L + 1 = Phi_6(Lefschetz)",
    "zeta": "Z(V,t) = (1-qt)/((1-t)(1-q^2 t)); N_m = Phi6(q^m) verified m=1,2",
    "zeta_consistency": bool(zeta_ok),
    "gf7_symmetry_scan": {
        "n_affine_diagonal_symmetries": len(syms),
        "symmetries": syms[:50],
        "mu3_scaling_preserves_V": bool(mu3_scaling_in),
        "coordinate_permutations": perm_results,
    },
    "torus_action": {
        "map": "g_u: (L,C,R) -> (uL+u-1, C/u, R/u)",
        "equivariance_p_weight_minus_1": bool(equivariance_ok),
        "orbit_summary": orbit_summary,
        "freeness_and_decomposition_ok": bool(freeness_ok),
        "unique_fixed_point": "ether point (L,C,R) = (-1, 0, 0)",
        "count_form": "Phi6(q) = 1 + q*(q-1): ether + q free F_q^* orbits",
        "mu6_generator_image_mod_pi": mu6_gen_image,
        "mu6_reduces_isomorphically_to_gf7_star": bool(prim_root),
    },
}
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
          "eisenstein_variety_point_count_prime_powers_results.json"), "w") as f:
    json.dump(results, f, indent=1)
print("\nSaved eisenstein_variety_point_count_prime_powers_results.json")
signal.alarm(0)
