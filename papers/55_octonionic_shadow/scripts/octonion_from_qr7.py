#!/usr/bin/env python3
"""
octonion_from_qr7.py

Verifies that the quadratic residues QR(7) = {1,2,4} of GF(7) generate the octonion
algebra via the oriented difference-set construction. All arithmetic is exact (integers /
Fractions). This script verifies:

  (A1) {1,2,4} = quadratic residues mod 7 = a perfect (7,3,1) planar difference set
       in Z/7.
  (A2) Its translates L_t = {1+t, 2+t, 4+t} are exactly the 7 lines of the Fano plane
       PG(2,2) on points {1..7}.
  (A3) The multiplier of the difference set is the QR subgroup {1,2,4}
       (Hall multiplier theorem instance: 2*D = D).
  (A4) Orienting each line cyclically as (1+t, 2+t, 4+t) and setting
         e_a e_b = e_c  (cyclic), e_b e_a = -e_c, e_i^2 = -1
       yields a real 8-dim algebra that IS the octonions:
       alternativity, Moufang identities, and norm composition N(xy) = N(x)N(y)
       all hold exactly (rational arithmetic).
  (A5) Non-associativity witness (so it is not a mislabeled associative algebra).
  (A6) There are exactly 30 Fano-plane structures on 7 labeled points, hence
       30 * 2^7 = 3840 oriented candidate tables, of which exactly 480 define
       composition algebras — the classical "480 octonion multiplication conventions".
  (A7) The subgroup of signed permutations of (e_1..e_7) preserving the standard
       table (the "frame group") has order 1344 = 2^3 * 168; its sign-only kernel has
       order 8; the quotient has order 168 and equals the Fano automorphism group.
       Since 7! * 2^7 / 1344 = 480, the signed-permutation action is transitive on the
       480 valid tables: the octonion structure attached to GF(7) is unique up to
       relabeling.
"""

import itertools
import random
from fractions import Fraction

random.seed(20260703)

# ----------------------------------------------------------------------
# (A1)-(A3) The difference set and the Fano plane from GF(7)
# ----------------------------------------------------------------------

P = 7
D = frozenset({1, 2, 4})  # quadratic residues mod 7

def quadratic_residues(p):
    return frozenset((x * x) % p for x in range(1, p)) - {0}

def is_planar_difference_set(D, p):
    """Every nonzero residue mod p arises exactly once as d1 - d2."""
    from collections import Counter
    c = Counter((a - b) % p for a in D for b in D if a != b)
    return set(c.keys()) == set(range(1, p)) and all(v == 1 for v in c.values())

def m7(x):
    """Represent Z/7 on {1..7} (7 plays the role of 0)."""
    return ((x - 1) % 7) + 1

LINES = [frozenset({m7(1 + t), m7(2 + t), m7(4 + t)}) for t in range(7)]

def is_fano(lines):
    lines = list(map(frozenset, lines))
    if len(set(lines)) != 7: return False
    if any(len(L) != 3 for L in lines): return False
    pts = set().union(*lines)
    if len(pts) != 7: return False
    # every pair of distinct points on exactly one common line
    for a, b in itertools.combinations(sorted(pts), 2):
        if sum(1 for L in lines if a in L and b in L) != 1:
            return False
    return True

assert quadratic_residues(7) == D, "QR(7) != {1,2,4}"
assert is_planar_difference_set(D, 7), "{1,2,4} not a (7,3,1) difference set"
assert frozenset(m7(2 * d) for d in D) == D, "2 is not a multiplier of D"
assert is_fano(LINES), "translates of D do not form a Fano plane"
print("[A1] QR(7) = {1,2,4}: OK")
print("[A2] translates of {1,2,4} form a Fano plane: OK")
print("[A3] multiplier group of D contains QR(7) (2*D = D): OK")

# ----------------------------------------------------------------------
# (A4) Octonions from the oriented difference set
# ----------------------------------------------------------------------
# Basis: e_0 = 1 (real unit), e_1..e_7 imaginary.
# Structure constants: dict (i,j) -> (k, sign) meaning e_i e_j = sign*e_k.

def build_table(oriented_lines):
    """oriented_lines: list of ordered triples (a,b,c) meaning
    e_a e_b = e_c and cyclic."""
    mul = {}
    for (a, b, c) in oriented_lines:
        for (x, y, z) in [(a, b, c), (b, c, a), (c, a, b)]:
            mul[(x, y)] = (z, +1)
            mul[(y, x)] = (z, -1)
    return mul

STD_ORIENTED = [(m7(1 + t), m7(2 + t), m7(4 + t)) for t in range(7)]
MUL = build_table(STD_ORIENTED)

def omul(x, y, mul=MUL):
    """Multiply octonions given as length-8 sequences (index 0 = real)."""
    z = [0] * 8
    z[0] = x[0] * y[0]
    for i in range(1, 8):
        z[0] -= x[i] * y[i]          # e_i e_i = -1
        z[i] += x[0] * y[i] + x[i] * y[0]
    for i in range(1, 8):
        if x[i] == 0: continue
        for j in range(1, 8):
            if i == j or y[j] == 0: continue
            k, s = mul[(i, j)]
            z[k] += s * x[i] * y[j]
    return z

def oconj(x):
    return [x[0]] + [-c for c in x[1:]]

def onorm(x):
    return sum(c * c for c in x)

def basis(i):
    v = [0] * 8
    v[i] = 1
    return v

def rand_oct(rng=5):
    return [Fraction(random.randint(-rng, rng)) for _ in range(8)]

def sub(x, y): return [a - b for a, b in zip(x, y)]
def is_zero(x): return all(c == 0 for c in x)

# --- alternativity on ALL basis triples (exhaustive, exact) ---
ok = True
for i in range(8):
    for j in range(8):
        ei, ej = basis(i), basis(j)
        # left alternative: x(xy) = (xx)y ; right: (yx)x = y(xx)
        if not is_zero(sub(omul(ei, omul(ei, ej)), omul(omul(ei, ei), ej))): ok = False
        if not is_zero(sub(omul(omul(ej, ei), ei), omul(ej, omul(ei, ei)))): ok = False
assert ok
# linearized alternativity on random rationals
for _ in range(200):
    x, y = rand_oct(), rand_oct()
    assert is_zero(sub(omul(x, omul(x, y)), omul(omul(x, x), y)))
    assert is_zero(sub(omul(omul(y, x), x), omul(y, omul(x, x))))
print("[A4a] alternativity (exhaustive on basis + 200 random exact): OK")

# --- Moufang identity  (zx)(yz)=(z(xy))z ---
for _ in range(100):
    x, y, z = rand_oct(), rand_oct(), rand_oct()
    lhs = omul(omul(z, x), omul(y, z))
    rhs = omul(omul(z, omul(x, y)), z)
    assert is_zero(sub(lhs, rhs))
print("[A4b] Moufang identity (zx)(yz) = (z(xy))z, 100 random exact: OK")

# --- norm composition ---
for _ in range(300):
    x, y = rand_oct(), rand_oct()
    assert onorm(omul(x, y)) == onorm(x) * onorm(y)
print("[A4c] norm composition N(xy)=N(x)N(y), 300 random exact: OK")

# --- conjugation is an anti-automorphism, x*conj(x) = N(x) ---
for _ in range(100):
    x, y = rand_oct(), rand_oct()
    assert is_zero(sub(oconj(omul(x, y)), omul(oconj(y), oconj(x))))
    xc = omul(x, oconj(x))
    assert xc[0] == onorm(x) and is_zero([0] + xc[1:])
print("[A4d] conjugation anti-automorphism & x·x̄ = N(x): OK")

# ----------------------------------------------------------------------
# (A5) non-associativity witness
# ----------------------------------------------------------------------
w = None
for i, j, k in itertools.product(range(1, 8), repeat=3):
    l = omul(omul(basis(i), basis(j)), basis(k))
    r = omul(basis(i), omul(basis(j), basis(k)))
    if not is_zero(sub(l, r)):
        w = (i, j, k, l, r)
        break
assert w is not None
i, j, k, l, r = w
print(f"[A5] non-associativity witness: (e{i} e{j}) e{k} = {l}  !=  e{i}(e{j} e{k}) = {r}")

# ----------------------------------------------------------------------
# (A6) exactly 480 valid oriented tables among 30 * 128 = 3840
# ----------------------------------------------------------------------
STD_LINESET = frozenset(LINES)
all_fanos = set()
pts = list(range(1, 8))
for perm in itertools.permutations(pts):
    pm = dict(zip(pts, perm))
    all_fanos.add(frozenset(frozenset(pm[x] for x in L) for L in STD_LINESET))
assert all(is_fano(f) for f in all_fanos)
print(f"[A6a] number of Fano-plane structures on 7 labeled points: {len(all_fanos)} (expect 30)")
assert len(all_fanos) == 30

def table_is_composition(mul):
    """Exact probabilistic test: norm composition on 6 random exact pairs,
    then exhaustive alternativity on basis if it survives."""
    for _ in range(6):
        x, y = rand_oct(3), rand_oct(3)
        if onorm(omul(x, y, mul)) != onorm(x) * onorm(y):
            return False
    for i in range(1, 8):
        for j in range(1, 8):
            ei, ej = basis(i), basis(j)
            if not is_zero(sub(omul(ei, omul(ei, ej, mul), mul),
                               omul(omul(ei, ei, mul), ej, mul))):
                return False
    return True

count_valid = 0
valid_examples = []
for fano in all_fanos:
    lines = [tuple(sorted(L)) for L in fano]
    for orient in itertools.product([0, 1], repeat=7):
        oriented = []
        for (a, b, c), o in zip(lines, orient):
            oriented.append((a, b, c) if o == 0 else (a, c, b))
        mul = build_table(oriented)
        if table_is_composition(mul):
            count_valid += 1
print(f"[A6b] valid octonion tables among 3840 oriented candidates: {count_valid} (expect 480)")
assert count_valid == 480

# ----------------------------------------------------------------------
# (A7) frame group = 1344, sign kernel = 8, quotient = Fano autos = 168
# ----------------------------------------------------------------------
# Fano automorphisms: permutations of 1..7 preserving the line set
fano_autos = []
for perm in itertools.permutations(pts):
    pm = dict(zip(pts, perm))
    if frozenset(frozenset(pm[x] for x in L) for L in STD_LINESET) == STD_LINESET:
        fano_autos.append(pm)
print(f"[A7a] |Aut(Fano)| = {len(fano_autos)} (expect 168)")
assert len(fano_autos) == 168

PAIRS = [(i, j) for i in range(1, 8) for j in range(1, 8) if i != j]

def is_frame_auto(pm, signs):
    """signs: dict i -> ±1. Check s_i s_j sigma(e_i e_j) = e_{s(i)} e_{s(j)}."""
    for (i, j) in PAIRS:
        k, s = MUL[(i, j)]
        k2, s2 = MUL[(pm[i], pm[j])]
        if pm[k] != k2 or signs[i] * signs[j] * s * signs[k] != s2:
            return False
    return True

frame_group = 0
sign_only = 0
for pm in fano_autos:                       # perm must preserve lines
    for bits in itertools.product([1, -1], repeat=7):
        signs = dict(zip(range(1, 8), bits))
        if is_frame_auto(pm, signs):
            frame_group += 1
            if all(pm[i] == i for i in pts):
                sign_only += 1
print(f"[A7b] |frame group| = {frame_group} (expect 1344 = 2^3 * 168)")
print(f"[A7c] sign-only kernel = {sign_only} (expect 8 = 2^3)")
assert frame_group == 1344 and sign_only == 8
assert frame_group // sign_only == 168
total_signed_perms = 5040 * 128
print(f"[A7d] orbit size = |signed perms| / |frame group| = "
      f"{total_signed_perms}/{frame_group} = {total_signed_perms // frame_group} "
      f"= number of valid tables ({count_valid}) => action transitive: OK")
assert total_signed_perms // frame_group == count_valid

print("\nALL CHECKS PASSED: the octonions are the unique (up to relabeling)")
print("composition algebra generated by the oriented QR(7) difference set.")
