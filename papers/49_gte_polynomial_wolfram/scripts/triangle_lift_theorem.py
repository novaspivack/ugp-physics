#!/usr/bin/env python3
"""
Triangle Lift Theorem computation: is the GTE polynomial p(L,C,R)=C+R-CR-LCR
a derived structure of UGP?

Computes, with exact GF(7) arithmetic:
  (A) Provenance: total-parity vectors of the 15 canonical GTE triples (P01)
      reproduce the CUP-4 orbit vectors g1=[1,1,0,0,1], g2=[0,1,0,1,1], g3=[1,1,1,1,1].
  (B) CUP-4 replication: among 256 elementary CA rules, orbit-satisfiers = {110,111};
      orbit + vacuum transparency = {110}.
  (C) Lift space: the multilinear GF(7) polynomial class (8 coefficients);
      survivor counts under (i) the 10 orbit ring-evaluations alone, and
      (ii) orbit + vacuum transparency  -- expected 7 and 1 (the unique survivor = p),
      via GF(7) Gaussian elimination AND independent brute-force enumeration of 7^8.
  (D) Sparsity floor verification: the exponent-flattening homomorphism --
      binary restriction of any GF(7) polynomial equals that of its multilinear
      flattening; spot-verified on random polynomials.  (The >=4 monomial floor
      is then a 3-line support-class argument; verified for the multilinear class
      exhaustively.)
  (E) Field generality: the same interpolation is unique over GF(q) for q in
      {5,7,11,13}; diagonal fixed-point structure distinguishes q=7
      (no displaced vacuum) from q=5 (displaced vacuum at x=2).

Expected output: JSON artifact triangle_lift_theorem_results.json with all counts.
"""

import itertools
import json
import os
import random
import signal
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))

TIMEOUT_SECONDS = 600


def _timeout_handler(signum, frame):
    print(f"\nTIMEOUT: wall-clock limit {TIMEOUT_SECONDS}s reached.")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

results = {}

# ----------------------------------------------------------------------
# (A) Provenance: parity vectors from the canonical P01 triples
# ----------------------------------------------------------------------
TRIPLES = {  # family -> [gen1, gen2, gen3]
    "e":   [(1, 73, 823), (9, 42, 1023), (5, 275, 65535)],
    "u":   [(5, 9, 275), (5, 275, 65535), (76, 337920, -1)],
    "d":   [(9, 5, 42), (9, 186, 1023), (5, 8191, 65535)],
    "nuR": [(2, 5, 5), (7, 11, 13), (17, 19, 23)],
    "nuL": [(1, 1, 823), (9, 1, 1023), (5, 1, 65535)],
}
ORDER = ["e", "u", "d", "nuR", "nuL"]  # canonical CUP-4 ordering

parity_vectors = []
for g in range(3):
    vec = [sum(TRIPLES[f][g]) % 2 for f in ORDER]
    parity_vectors.append(vec)

G1, G2, G3 = parity_vectors
EXPECTED = ([1, 1, 0, 0, 1], [0, 1, 0, 1, 1], [1, 1, 1, 1, 1])
provenance_ok = (G1, G2, G3) == ([list(v) for v in EXPECTED][0],
                                 list(EXPECTED[1]), list(EXPECTED[2]))
results["A_parity_vectors"] = {"g1": G1, "g2": G2, "g3": G3,
                               "match_cup4_lean_vectors": provenance_ok}
print("(A) parity vectors from canonical triples:", G1, G2, G3,
      "| match CUP-4:", provenance_ok)

# ----------------------------------------------------------------------
# (B) CUP-4 replication over 256 elementary rules
# ----------------------------------------------------------------------
def eca_step(rule, cells):
    n = len(cells)
    return [ (rule >> (cells[(i - 1) % n] * 4 + cells[i] * 2 + cells[(i + 1) % n])) & 1
             for i in range(n) ]

orbit_rules = [r for r in range(256)
               if eca_step(r, G1) == G2 and eca_step(r, G2) == G3]
vt_orbit_rules = [r for r in orbit_rules if (r & 1) == 0]
results["B_cup4"] = {"orbit_satisfiers": orbit_rules,
                     "orbit_plus_vacuum_transparency": vt_orbit_rules}
print("(B) orbit satisfiers:", orbit_rules, "| + vacuum transparency:", vt_orbit_rules)

# ----------------------------------------------------------------------
# (C) Lift space over GF(7): multilinear class, linear constraints
# ----------------------------------------------------------------------
P = 7
MONOMIALS = [(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1),
             (1, 1, 0), (1, 0, 1), (0, 1, 1), (1, 1, 1)]  # exponent vectors (L,C,R)


def monomial_row(L, C, R, p=P):
    return [pow(L, eL, p) * pow(C, eC, p) * pow(R, eR, p) % p
            for (eL, eC, eR) in MONOMIALS]


def gf_solve_count(rows, rhs, p=P):
    """Gaussian elimination over GF(p); returns (num_solutions, particular_solution or None)."""
    m = [row[:] + [b % p] for row, b in zip(rows, rhs)]
    nrows, ncols = len(m), len(MONOMIALS)
    rank, pivots = 0, []
    for col in range(ncols):
        piv = next((r for r in range(rank, nrows) if m[r][col] % p != 0), None)
        if piv is None:
            continue
        m[rank], m[piv] = m[piv], m[rank]
        inv = pow(m[rank][col], p - 2, p)
        m[rank] = [(x * inv) % p for x in m[rank]]
        for r in range(nrows):
            if r != rank and m[r][col] % p != 0:
                f = m[r][col]
                m[r] = [(a - f * b) % p for a, b in zip(m[r], m[rank])]
        pivots.append(col)
        rank += 1
    # consistency
    for r in range(rank, nrows):
        if m[r][ncols] % p != 0:
            return 0, None
    sol = [0] * ncols
    for r, col in enumerate(pivots):
        sol[col] = m[r][ncols]
    return p ** (ncols - rank), sol


# orbit constraints: 10 ring evaluations on binary vectors, outputs must equal
# the next generation's binary values AS ELEMENTS OF GF(7)
orbit_rows, orbit_rhs = [], []
for src, dst in ((G1, G2), (G2, G3)):
    n = len(src)
    for i in range(n):
        L, C, R = src[(i - 1) % n], src[i], src[(i + 1) % n]
        orbit_rows.append(monomial_row(L, C, R))
        orbit_rhs.append(dst[i])

count_orbit, _ = gf_solve_count(orbit_rows, orbit_rhs)
vt_rows = orbit_rows + [monomial_row(0, 0, 0)]
vt_rhs = orbit_rhs + [0]
count_vt, sol_vt = gf_solve_count(vt_rows, vt_rhs)

# the GTE polynomial's multilinear coefficient vector, ordered as MONOMIALS:
# 1, L, C, R, LC, LR, CR, LCR  ->  0,0,1,1,0,0,-1,-1
P_COEFFS = [0, 0, 1, 1, 0, 0, P - 1, P - 1]
results["C_lift_space"] = {
    "multilinear_class_size": P ** 8,
    "survivors_orbit_only": count_orbit,
    "survivors_orbit_plus_vacuum_transparency": count_vt,
    "unique_survivor_is_p": sol_vt == P_COEFFS,
    "unique_survivor_coeffs_1_L_C_R_LC_LR_CR_LCR": sol_vt,
}
print(f"(C) multilinear lift space 7^8={P**8}: orbit-only survivors={count_orbit}, "
      f"orbit+VT survivors={count_vt}, unique survivor == p: {sol_vt == P_COEFFS}")

# brute-force cross-check of the orbit+VT count over all 7^8 multilinear polys
# (vectorized via precomputed evaluation matrix on the 11 constraint points)
points = []
for src, dst in ((G1, G2), (G2, G3)):
    n = len(src)
    for i in range(n):
        points.append(((src[(i - 1) % n], src[i], src[(i + 1) % n]), dst[i]))
points.append(((0, 0, 0), 0))

# deduplicate identical (point, output) pairs; check for conflicts
point_map = {}
conflict = False
for (pt, out) in points:
    if pt in point_map and point_map[pt] != out:
        conflict = True
    point_map[pt] = out
results["C_constraint_points"] = {
    "distinct_binary_points_constrained": len(point_map),
    "consistent": not conflict,
    "points": {str(k): v for k, v in point_map.items()},
}
print(f"(C) distinct constrained binary points: {len(point_map)} (of 8), "
      f"consistent: {not conflict}")

import numpy as np
coeff_grid = np.array(list(itertools.product(range(P), repeat=8)), dtype=np.int64)
eval_matrix = np.array([monomial_row(*pt) for pt in point_map], dtype=np.int64)
targets = np.array(list(point_map.values()), dtype=np.int64)
vals = (coeff_grid @ eval_matrix.T) % P
mask = (vals == targets).all(axis=1)
bf_count = int(mask.sum())
bf_sol = coeff_grid[mask][0].tolist() if bf_count == 1 else None
results["C_bruteforce_check"] = {"survivors": bf_count, "survivor_is_p": bf_sol == P_COEFFS}
print(f"(C) brute-force 7^8 cross-check: survivors={bf_count}, == p: {bf_sol == P_COEFFS}")

# ----------------------------------------------------------------------
# (D) Exponent-flattening homomorphism spot-verification
# ----------------------------------------------------------------------
def eval_poly(monos, coefs, L, C, R, p=P):
    tot = 0
    for (eL, eC, eR), c in zip(monos, coefs):
        tot += c * pow(L, eL, p) * pow(C, eC, p) * pow(R, eR, p)
    return tot % p


def flatten(monos, coefs, p=P):
    """Replace every exponent >=1 by 1; merge coefficients by support class."""
    acc = {}
    for (eL, eC, eR), c in zip(monos, coefs):
        key = (min(eL, 1), min(eC, 1), min(eR, 1))
        acc[key] = (acc.get(key, 0) + c) % p
    return acc


rng = random.Random(20260610)
flatten_ok = True
for _ in range(20000):
    k = rng.randint(1, 6)
    monos = [tuple(rng.randint(0, 6) for _ in range(3)) for _ in range(k)]
    coefs = [rng.randint(1, 6) for _ in range(k)]
    flat = flatten(monos, coefs)
    fmonos, fcoefs = list(flat.keys()), list(flat.values())
    for (L, C, R) in itertools.product((0, 1), repeat=3):
        if eval_poly(monos, coefs, L, C, R) != eval_poly(fmonos, fcoefs, L, C, R):
            flatten_ok = False
            break
    if not flatten_ok:
        break
results["D_flattening_homomorphism_spotcheck"] = {"trials": 20000, "all_agree": flatten_ok}
print("(D) flattening homomorphism agrees on binary inputs (20k random polys):", flatten_ok)

# support classes of p's flattening (must each carry a nonzero merged coefficient)
p_flat = flatten(MONOMIALS, P_COEFFS)
nonzero_classes = [k for k, v in p_flat.items() if v != 0]
results["D_sparsity_floor"] = {
    "nonzero_support_classes_of_p": [str(k) for k in nonzero_classes],
    "count": len(nonzero_classes),
    "floor_statement": "any GF(7) rule with binary restriction Rule 110 needs >= 4 monomials",
}
print("(D) nonzero support classes of p:", nonzero_classes, "->\u2265 4-monomial floor")

# ----------------------------------------------------------------------
# (E) Field generality and diagonal structure
# ----------------------------------------------------------------------
field_results = {}
for q in (5, 7, 11, 13):
    rows = [monomial_row(*pt, p=q) for pt in point_map]
    rhs = [v % q for v in point_map.values()]
    cnt, sol = gf_solve_count(rows, rhs, p=q)
    # diagonal fixed points: p_q(x,x,x) = x  with p_q = C+R-CR-LCR mod q
    fixed = [x for x in range(q)
             if (2 * x - x * x - x ** 3) % q == x % q]
    diag_roots = [x for x in range(q) if (2 * x - x * x - x ** 3) % q == 0]
    field_results[q] = {
        "interpolant_unique": cnt == 1,
        "coeffs": sol,
        "coeffs_equal_CplusR_minus_CR_minus_LCR": sol == [0, 0, 1, 1, 0, 0, q - 1, q - 1],
        "diagonal_fixed_points_of_p": fixed,
        "diagonal_roots_p_eq_0": diag_roots,
    }
    print(f"(E) GF({q}): unique interpolant={cnt == 1}, same form={sol == [0,0,1,1,0,0,q-1,q-1]}, "
          f"fixed points p(x,x,x)=x: {fixed}")
results["E_field_generality"] = field_results

with open(os.path.join(_HERE, "triangle_lift_theorem_results.json"), "w") as f:
    json.dump(results, f, indent=1)
print("\nArtifact: triangle_lift_theorem_results.json")
signal.alarm(0)
