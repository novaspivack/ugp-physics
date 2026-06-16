#!/usr/bin/env python3
"""
Triangle closure residual tests (pre-registered):

  (1) Mod-7 inconsistency: do the 10 Z7 orbit evaluations of f_MDL admit ANY
      multilinear GF(7) rule?  (If not, the parity shadow is the unique
      MDL-realizable reduction of the UGP orbit.)
      Also: minimal per-variable degree at which the Z7 orbit constraints
      become realizable by a polynomial rule (search degree caps 1,2,3).
  (2) Projection null battery: componentwise total-parity analogs mod m=3,5
      on the canonical triples; orbit-forcing test over the corresponding
      minimal embedding fields.
  (3) Ordering census: among all 120 orderings of the 5 families, how many
      admit any binary rule with orbit + vacuum transparency; survivor rules.
  (4) Seven-route: delta(N_c) = N_c + (N_c^2-1)/2 vs q_min(N_c) = minimal prime
      q with 2|q-1 and N_c|q-1; coincidence locus + neighbor nulls.
  (5) Coefficient-scan nulls: small-grammar search for (1,1,-1,-1) support
      pattern in ridge arithmetic with wrong-target nulls.

Artifact: triangle_residual_tests_results.json
"""

import itertools
import json
import os
import signal
import sys
from sympy import isprime

_HERE = os.path.dirname(os.path.abspath(__file__))

TIMEOUT_SECONDS = 600


def _t(signum, frame):
    print("TIMEOUT")
    sys.exit(1)


signal.signal(signal.SIGALRM, _t)
signal.alarm(TIMEOUT_SECONDS)

results = {}

TRIPLES = {
    "e":   [(1, 73, 823), (9, 42, 1023), (5, 275, 65535)],
    "u":   [(5, 9, 275), (5, 275, 65535), (76, 337920, -1)],
    "d":   [(9, 5, 42), (9, 186, 1023), (5, 8191, 65535)],
    "nuR": [(2, 5, 5), (7, 11, 13), (17, 19, 23)],
    "nuL": [(1, 1, 823), (9, 1, 1023), (5, 1, 65535)],
}
ORDER = ["e", "u", "d", "nuR", "nuL"]

# ----------------------------------------------------------------------
# (1) Mod-7 orbit constraints vs polynomial degree caps
# ----------------------------------------------------------------------
Z7_ORBIT = [  # (l,c,r) -> out, from P28 tab:fmdl_orbit_entries
    ((1, 1, 5), 2), ((1, 5, 2), 5), ((5, 2, 2), 2), ((2, 2, 1), 0), ((2, 1, 1), 2),
    ((2, 2, 5), 5), ((2, 5, 2), 6), ((5, 2, 0), 5), ((2, 0, 2), 3), ((0, 2, 2), 5),
]


def monomials_upto(d):
    return [(a, b, c) for a in range(d + 1) for b in range(d + 1) for c in range(d + 1)]


def gf_consistent(points, monos, p=7):
    """Rank test: is the linear system (eval matrix | rhs) consistent over GF(p)?
    Returns (consistent, n_solutions)."""
    rows = []
    for (pt, out) in points:
        L, C, R = pt
        rows.append([pow(L, eL, p) * pow(C, eC, p) * pow(R, eR, p) % p
                     for (eL, eC, eR) in monos] + [out % p])
    ncols = len(monos)
    rank, prow = 0, 0
    m = [r[:] for r in rows]
    pivcols = []
    for col in range(ncols):
        piv = next((r for r in range(rank, len(m)) if m[r][col] % p), None)
        if piv is None:
            continue
        m[rank], m[piv] = m[piv], m[rank]
        inv = pow(m[rank][col], p - 2, p)
        m[rank] = [(x * inv) % p for x in m[rank]]
        for r in range(len(m)):
            if r != rank and m[r][col] % p:
                f = m[r][col]
                m[r] = [(a - f * b) % p for a, b in zip(m[r], m[rank])]
        pivcols.append(col)
        rank += 1
    for r in range(rank, len(m)):
        if m[r][ncols] % p:
            return False, 0
    return True, p ** (ncols - rank)


deg_results = {}
for d in (1, 2, 3, 6):
    ok, nsol = gf_consistent(Z7_ORBIT, monomials_upto(d))
    deg_results[d] = {"consistent": ok, "n_solutions": nsol if ok else 0}
    print(f"(1) Z7 orbit constraints, per-variable degree <= {d}: "
          f"consistent={ok}, solutions={nsol if ok else 0}")
results["1_z7_orbit_polynomial_realizability"] = deg_results

# same test with the binary-parity orbit (control: must be consistent at d=1)
G = [[sum(TRIPLES[f][g]) % 2 for f in ORDER] for g in range(3)]
par_points = []
for src, dst in ((G[0], G[1]), (G[1], G[2])):
    for i in range(5):
        par_points.append(((src[(i - 1) % 5], src[i], src[(i + 1) % 5]), dst[i]))
par_points.append(((0, 0, 0), 0))
ok1, n1 = gf_consistent(par_points, monomials_upto(1))
results["1_parity_orbit_multilinear_control"] = {"consistent": ok1, "n_solutions": n1}
print(f"(1-control) parity orbit + VT, multilinear: consistent={ok1}, solutions={n1}")

# ----------------------------------------------------------------------
# (2) Projection null battery: total component-sum mod m, m = 3, 5
# ----------------------------------------------------------------------
proj_results = {}
for m in (3, 5):
    vecs = [[sum(TRIPLES[f][g]) % m for f in ORDER] for g in range(3)]
    # minimal prime field containing all values: q >= max value+1 and q prime,
    # use q = m if m prime (alphabet Z_m itself); rule space: all functions
    # would be huge -- but the analog of CUP-4 is the *rule count* among
    # k=m lookup tables consistent with the orbit + VT, which is m^(m^3 - n_constrained).
    # The meaningful forcing test mirrors CUP-4: multilinear polynomial class over GF(q).
    q = m  # m = 3, 5 are prime
    points = []
    for src, dst in ((vecs[0], vecs[1]), (vecs[1], vecs[2])):
        for i in range(5):
            points.append(((src[(i - 1) % 5], src[i], src[(i + 1) % 5]), dst[i]))
    points.append(((0, 0, 0), 0))
    # deduplicate, detect conflicts
    pm, conflict = {}, False
    for pt, out in points:
        if pt in pm and pm[pt] != out:
            conflict = True
        pm[pt] = out
    if conflict:
        proj_results[m] = {"orbit_vectors": vecs, "conflict_in_constraints": True}
        print(f"(2) mod-{m} projection: orbit constraint CONFLICT (no rule of any kind)")
        continue
    pts = list(pm.items())
    ok, nsol = gf_consistent(pts, monomials_upto(1), p=q)
    proj_results[m] = {"orbit_vectors": vecs, "conflict_in_constraints": False,
                       "distinct_points": len(pm),
                       "multilinear_consistent": ok,
                       "multilinear_solutions": nsol if ok else 0}
    print(f"(2) mod-{m} projection: vectors={vecs}, distinct pts={len(pm)}, "
          f"multilinear consistent={ok}, solutions={nsol if ok else 0}")
results["2_projection_null_battery"] = proj_results

# ----------------------------------------------------------------------
# (3) Ordering census over 120 permutations
# ----------------------------------------------------------------------
def eca_step(rule, cells):
    n = len(cells)
    return [(rule >> (cells[(i - 1) % n] * 4 + cells[i] * 2 + cells[(i + 1) % n])) & 1
            for i in range(n)]


par = {f: [sum(TRIPLES[f][g]) % 2 for g in range(3)] for f in ORDER}
census = {"orderings_with_some_vt_rule": 0, "orderings_with_some_rule": 0,
          "survivor_rules_by_ordering": {}}
for perm in itertools.permutations(ORDER):
    g1 = [par[f][0] for f in perm]
    g2 = [par[f][1] for f in perm]
    g3 = [par[f][2] for f in perm]
    rules = [r for r in range(256) if eca_step(r, g1) == g2 and eca_step(r, g2) == g3]
    vt = [r for r in rules if (r & 1) == 0]
    if rules:
        census["orderings_with_some_rule"] += 1
        census["survivor_rules_by_ordering"][",".join(perm)] = {"rules": rules, "vt": vt}
    if vt:
        census["orderings_with_some_vt_rule"] += 1
all_vt_rules = sorted({r for v in census["survivor_rules_by_ordering"].values()
                       for r in v["vt"]})
census["distinct_vt_rules_across_orderings"] = all_vt_rules
results["3_ordering_census"] = census
print(f"(3) ordering census: {census['orderings_with_some_rule']}/120 orderings admit a rule; "
      f"{census['orderings_with_some_vt_rule']}/120 admit a VT rule; "
      f"distinct VT rules across all orderings: {all_vt_rules}")

# ----------------------------------------------------------------------
# (4) Seven-route: delta(N_c) vs minimal derivable prime q_min(N_c)
# ----------------------------------------------------------------------
def q_min(nc):
    q = 2
    while True:
        if isprime(q) and (q - 1) % 2 == 0 and (q - 1) % nc == 0:
            return q
        q += 1


seven = {}
for nc in (2, 3, 4, 5, 6, 7, 9, 11):
    d2 = nc + (nc * nc - 1) / 2
    delta = int(d2) if d2 == int(d2) else None
    q = q_min(nc)
    seven[nc] = {"delta": delta if delta is not None else f"{d2} (non-integer)",
                 "q_min": q, "coincide": delta == q}
    print(f"(4) N_c={nc}: delta={d2}, q_min={q}, coincide={delta == q}")
results["4_seven_route_delta_vs_qmin"] = seven

# ----------------------------------------------------------------------
# (5) Coefficient-pattern scan with nulls
# ----------------------------------------------------------------------
# GTE atoms (certified integers from the ridge arithmetic)
ATOMS = {"a_e": 1, "b1": 73, "c1": 823, "a_mu": 9, "b2": 42, "c2": 1023,
         "a_tau": 5, "b3": 275, "c3": 65535, "q1": 11, "q2": 24, "m1": 20,
         "m2": 15, "n": 10, "delta": 7, "F13": 233, "Nc": 3, "Nfam": 5,
         "cH": 13}
# target: the coefficient 4-vector of p on supports (C, R, CR, LCR) = (1,1,-1,-1) mod 7
# = (1,1,6,6).  Grammar: residues mod 7 of atoms and pairwise differences/sums.
target = (1, 1, 6, 6)
hits = []
atoms_items = list(ATOMS.items())
for combo in itertools.permutations(atoms_items, 4):
    vec = tuple(v % 7 for _, v in combo)
    if vec == target:
        hits.append([k for k, _ in combo])
        if len(hits) >= 50:
            break
# null: how many 4-permutations hit an arbitrary wrong-target pattern, e.g. (2,3,4,5)?
null_hits = sum(1 for combo in itertools.permutations(atoms_items, 4)
                if tuple(v % 7 for _, v in combo) == (2, 3, 4, 5))
total_perms = 0
for _ in itertools.permutations(atoms_items, 4):
    total_perms += 1
results["5_coefficient_scan"] = {
    "target_residues_mod7": target,
    "hits_first50": hits[:50], "n_hits_capped": len(hits),
    "wrong_target_2345_hits": null_hits,
    "total_4_perms": total_perms,
    "verdict": "any hits are volume-dominated; see hit counts vs null",
}
print(f"(5) coefficient scan: {len(hits)} hits (cap 50) for target {target} among "
      f"{total_perms} 4-perms; wrong-target (2,3,4,5) hits: {null_hits}")

with open(os.path.join(_HERE, "triangle_residual_tests_results.json"), "w") as f:
    json.dump(results, f, indent=1, default=str)
print("\nArtifact: triangle_residual_tests_results.json")
signal.alarm(0)
