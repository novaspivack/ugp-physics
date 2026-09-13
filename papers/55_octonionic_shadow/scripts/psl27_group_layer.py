#!/usr/bin/env python3
"""
psl27_group_layer.py

Verifies the group-layer structure of PSL(2,7) ≅ GL(3,2) = Aut(Fano), the unique
Hurwitz group of order 168 that acts faithfully on the 7-point Fano geometry. All
computations are exhaustive finite enumeration; no randomness. Verifies:

  (B1) PSL(2,7), realized as Moebius transformations of the projective line over
       GF(7) (8 points), has order 168.
  (B2) GL(3,2), realized as invertible 3x3 matrices over GF(2), has order 168, and
       acting on the 7 nonzero vectors of GF(2)^3 it is EXACTLY the automorphism
       group of the Fano plane whose lines are {u, v, u+v}. This Fano plane is
       isomorphic (explicit relabeling computed) to the QR(7)-translate Fano plane
       of octonion_from_qr7.py, so GL(3,2) = Aut(octonion line structure).
  (B3) HURWITZ CERTIFICATION: both groups contain generator pairs (a,b) with
       a^2 = b^3 = (ab)^7 = [a,b]^4 = 1  and <a,b> = G.
       Since <a,b | a^2 = b^3 = (ab)^7 = [a,b]^4 = 1> is a group of order exactly
       168 (see hurwitz_coset_enumeration.py), both groups are isomorphic to it and
       hence to each other: PSL(2,7) ~= GL(3,2) (the exceptional isomorphism).
       The (2,3,7) generation simultaneously certifies both as Hurwitz groups:
       PSL(2,7) = Aut(Klein quartic), attaining the Hurwitz bound 84(g-1) at genus 3.
  (B4) The two inequivalent 7-point actions of the abstract group (points vs lines of
       the Fano plane) are swapped by duality; verified by showing point-stabilizers
       and line-stabilizers are non-conjugate S4-subgroups.
"""

import itertools

# ----------------------------------------------------------------------
# (B1) PSL(2,7) as Moebius permutations of P^1(F_7) = {0..6, inf=7}
# ----------------------------------------------------------------------
Q = 7
INF = 7
points8 = list(range(8))

def inv7(a): return pow(a, Q - 2, Q)

def moebius(mat):
    a, b, c, d = mat
    perm = []
    for x in points8:
        if x == INF:
            perm.append(INF if c % Q == 0 else (a * inv7(c)) % Q)
        else:
            num, den = (a * x + b) % Q, (c * x + d) % Q
            perm.append(INF if den == 0 else (num * inv7(den)) % Q)
    return tuple(perm)

psl27 = set()
for a, b, c, d in itertools.product(range(Q), repeat=4):
    if (a * d - b * c) % Q == 1:
        psl27.add(moebius((a, b, c, d)))
psl27 = sorted(psl27)
print(f"[B1] |PSL(2,7)| as Moebius permutations of P^1(F_7): {len(psl27)} (expect 168)")
assert len(psl27) == 168

# ----------------------------------------------------------------------
# (B2) GL(3,2) on nonzero vectors of F_2^3 = Aut(Fano)
# ----------------------------------------------------------------------
vecs = [v for v in itertools.product([0, 1], repeat=3) if any(v)]
vidx = {v: i for i, v in enumerate(vecs)}          # 7 points, indices 0..6

def matmul_f2(M, v):
    return tuple(sum(M[r][k] * v[k] for k in range(3)) % 2 for r in range(3))

def is_invertible_f2(M):
    # invertible iff the map on vecs is a bijection onto vecs
    img = {matmul_f2(M, v) for v in vecs}
    return img == set(vecs)

gl32_mats = [M for M in itertools.product(itertools.product([0,1],repeat=3), repeat=3)
             if is_invertible_f2(M)]
print(f"[B2a] |GL(3,2)| = {len(gl32_mats)} (expect 168)")
assert len(gl32_mats) == 168

gl32_perms = sorted({tuple(vidx[matmul_f2(M, v)] for v in vecs) for M in gl32_mats})
assert len(gl32_perms) == 168

# Fano plane on F_2^3 \ {0}: lines {u, v, u+v}
lines_f2 = set()
for u, v in itertools.combinations(vecs, 2):
    w = tuple((a + b) % 2 for a, b in zip(u, v))
    lines_f2.add(frozenset({vidx[u], vidx[v], vidx[w]}))
assert len(lines_f2) == 7

def preserves(perm, lineset):
    return frozenset(frozenset(perm[x] for x in L) for L in lineset) == frozenset(lineset)

assert all(preserves(g, lines_f2) for g in gl32_perms)
autos_f2 = [p for p in itertools.permutations(range(7)) if preserves(p, lines_f2)]
print(f"[B2b] GL(3,2) action = full Aut(Fano_F2): {len(autos_f2)} == 168 and "
      f"sets equal: {sorted(autos_f2) == gl32_perms}")
assert sorted(autos_f2) == gl32_perms

# explicit relabeling between the F_2^3 Fano plane and the QR(7) Fano plane
def m7(x): return ((x - 1) % 7) + 1
LINES_QR = frozenset(frozenset({m7(1+t), m7(2+t), m7(4+t)}) for t in range(7))
relabel = None
for perm in itertools.permutations(range(1, 8)):
    pm = dict(zip(range(7), perm))                  # F2 index -> QR label
    if frozenset(frozenset(pm[x] for x in L) for L in lines_f2) == LINES_QR:
        relabel = pm
        break
assert relabel is not None
print(f"[B2c] explicit Fano isomorphism  F_2^3-plane -> QR(7)-plane: {relabel}")

# ----------------------------------------------------------------------
# (B3) Hurwitz (2,3,7;4) generator pairs in both groups
# ----------------------------------------------------------------------
def pcompose(p, q):            # (p*q)(x) = p(q(x))
    return tuple(p[q[i]] for i in range(len(q)))

def pinv(p):
    r = [0]*len(p); 
    for i, v in enumerate(p): r[v] = i
    return tuple(r)

def porder(p):
    n, q, ident = 1, p, tuple(range(len(p)))
    while q != ident:
        q = pcompose(q, p); n += 1
    return n

def closure(gens, bound=200):
    ident = tuple(range(len(gens[0])))
    seen, frontier = {ident}, [ident]
    while frontier:
        nxt = []
        for x in frontier:
            for g in gens:
                y = pcompose(x, g)
                if y not in seen:
                    seen.add(y); nxt.append(y)
        frontier = nxt
    return seen

def find_hurwitz_pair(group_perms):
    invol = [g for g in group_perms if porder(g) == 2]
    ord3  = [g for g in group_perms if porder(g) == 3]
    for a in invol:
        for b in ord3:
            ab = pcompose(a, b)
            if porder(ab) != 7: continue
            comm = pcompose(pcompose(a, b), pcompose(pinv(a), pinv(b)))
            if porder(comm) != 4: continue
            if len(closure([a, b])) == 168:
                return a, b
    return None

pair_psl = find_hurwitz_pair(psl27)
pair_gl  = find_hurwitz_pair(gl32_perms)
assert pair_psl and pair_gl
print(f"[B3a] PSL(2,7) Hurwitz pair found: a={pair_psl[0]}, b={pair_psl[1]}")
print(f"[B3b] GL(3,2)  Hurwitz pair found: a={pair_gl[0]}, b={pair_gl[1]}")
for tag, (a, b) in [("PSL(2,7)", pair_psl), ("GL(3,2)", pair_gl)]:
    ab = pcompose(a, b)
    comm = pcompose(pcompose(a, b), pcompose(pinv(a), pinv(b)))
    print(f"      {tag}: ord(a)={porder(a)}, ord(b)={porder(b)}, "
          f"ord(ab)={porder(ab)}, ord([a,b])={porder(comm)}, |<a,b>|={len(closure([a,b]))}")
print("[B3c] both are quotients of <a,b | a^2=b^3=(ab)^7=[a,b]^4=1> of full order 168")
print("      => PSL(2,7) ~= GL(3,2)  (exceptional isomorphism, modulo the classical")
print("         fact |H(2,3,7;4)| = 168; see hurwitz_coset_enumeration.py).")
print("      Hurwitz (2,3,7) generation => PSL(2,7) = Aut(Klein quartic), 168 = 84(g-1) at g = 3.")

# ----------------------------------------------------------------------
# (B4) points vs lines: two index-7 actions (duality)
# ----------------------------------------------------------------------
lines_sorted = sorted(tuple(sorted(L)) for L in lines_f2)
def line_action(perm):
    imgs = []
    for L in lines_sorted:
        imgs.append(lines_sorted.index(tuple(sorted(perm[x] for x in L))))
    return tuple(imgs)

point_stab = [g for g in gl32_perms if g[0] == 0]
line_perms = sorted({line_action(g) for g in gl32_perms})
line_stab  = [g for g in gl32_perms if line_action(g)[0] == 0]
print(f"[B4] |point stabilizer| = {len(point_stab)} (expect 24), "
      f"|line stabilizer| = {len(line_stab)} (expect 24), "
      f"line action faithful onto {len(line_perms)} perms (expect 168)")
assert len(point_stab) == 24 and len(line_stab) == 24 and len(line_perms) == 168

# The two 7-point actions are inequivalent as G-sets: verified by checking that no
# point-stabilizer coincides with a line-stabilizer as a subgroup.
ps_sets = [frozenset(g for g in gl32_perms if g[i] == i) for i in range(7)]
ls_sets = [frozenset(g for g in gl32_perms if line_action(g)[j] == j) for j in range(7)]
overlap = any(p == l for p in ps_sets for l in ls_sets)
print(f"[B4b] some point-stabilizer coincides with some line-stabilizer: {overlap} (expect False)")
assert not overlap
print("      => the 7-point and 7-line actions are inequivalent: the two conjugacy")
print("         classes of index-7 S4 subgroups, swapped by Out(PSL(2,7)) = Z/2 (duality).")

print("\nALL GROUP CHECKS PASSED.")
