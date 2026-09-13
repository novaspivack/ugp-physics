#!/usr/bin/env python3
"""
Parity-projection forcing battery, Tier 1: additive homomorphisms.

Enumerates ALL nonzero weighted linear forms rho(a,b,c) = (alpha*a + beta*b
+ gamma*c) mod m for m in 2..7 (every additive group homomorphism Z^3 -> Z_m,
surjective or scaled-embedded), applies each to the 15 canonical GTE triples
(P01), places the three generation vectors on the canonical Z5 family ring,
and classifies the induced two-step orbit constraints (10 ring evaluations
+ vacuum transparency) over the multilinear GF(7) class:

  CONFLICT        -- same neighborhood point demands two outputs (no rule)
  NO_MULTILINEAR  -- functional but multilinear-inconsistent over GF(7)
  UNDERDETERMINED -- consistent, rank < 8 (orbit does not force a rule)
  FORCED          -- rank 8, unique multilinear rule

Pre-registered prediction P1: FORCED survivors = exactly the parity-factoring
forms (1,1,1) mod 2, (2,2,2) mod 4, (3,3,3) mod 6, each forcing the
t-conjugate g_t(L,C,R) = t*p(L/t, C/t, R/t) of p = C+R-CR-LCR (t = 1, 2, 3).

P1 outcome: FAILED as registered -- the enumeration found two additional
FORCED forms, (0,1,1) mod 5 and (2,5,4) mod 6, forcing non-conjugate rules.
Autopsy: both forced rules LEAK -- they map shadow values outside the
reduction's image (no proper invariant subalphabet at all), so the "shadow"
is not a cellular automaton on its own state space (the b+c mod 5 orbit
exits Z_5 one step after the data window). Re-registered P1': FORCED +
shadow-closure (the forced rule maps im(rho)^3 into im(rho) -- the certified
invariant-subalphabet condition of P28/P49, `rule110_unique_proper_invariant_subca`)
survivors = exactly the three parity-factoring forms. The script reports both
the raw FORCED set and the SCC-filtered set.

Also runs: named neighbor nulls, the native-field annex (solve over GF(m)
for prime m -- reproduces the R31 canonical battery + CUP-4), the
data-perturbation null (45 single-component +1 perturbations on total
parity), and brute-force verification of every FORCED verdict over all
7^8 multilinear rules (T1 method independence).

Expected output: survivor table matching P1; artifact
parity_projection_homomorphism_battery_results.json.
"""

import itertools
import json
import os
import signal
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))

TIMEOUT_SECONDS = 900


def _t(signum, frame):
    print(f"TIMEOUT: {TIMEOUT_SECONDS}s wall-clock limit reached.")
    sys.exit(1)


signal.signal(signal.SIGALRM, _t)
signal.alarm(TIMEOUT_SECONDS)

TRIPLES = {
    "e":   [(1, 73, 823), (9, 42, 1023), (5, 275, 65535)],
    "u":   [(5, 9, 275), (5, 275, 65535), (76, 337920, -1)],
    "d":   [(9, 5, 42), (9, 186, 1023), (5, 8191, 65535)],
    "nuR": [(2, 5, 5), (7, 11, 13), (17, 19, 23)],
    "nuL": [(1, 1, 823), (9, 1, 1023), (5, 1, 65535)],
}
ORDER = ["e", "u", "d", "nuR", "nuL"]

MONOMIALS = [(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1),
             (1, 1, 0), (1, 0, 1), (0, 1, 1), (1, 1, 1)]  # 1,L,C,R,LC,LR,CR,LCR
P_COEFFS = [0, 0, 1, 1, 0, 0, 6, 6]  # p = C+R-CR-LCR over GF(7)


def monomial_row(L, C, R, q):
    return [pow(L, eL, q) * pow(C, eC, q) * pow(R, eR, q) % q
            for (eL, eC, eR) in MONOMIALS]


def gf_solve(rows, rhs, q):
    """Gaussian elimination over GF(q). Returns (status, n_solutions, sol)."""
    m = [row[:] + [b % q] for row, b in zip(rows, rhs)]
    ncols = len(MONOMIALS)
    rank, pivots = 0, []
    for col in range(ncols):
        piv = next((r for r in range(rank, len(m)) if m[r][col] % q), None)
        if piv is None:
            continue
        m[rank], m[piv] = m[piv], m[rank]
        inv = pow(m[rank][col], q - 2, q)
        m[rank] = [(x * inv) % q for x in m[rank]]
        for r in range(len(m)):
            if r != rank and m[r][col] % q:
                f = m[r][col]
                m[r] = [(a - f * b) % q for a, b in zip(m[r], m[rank])]
        pivots.append(col)
        rank += 1
    for r in range(rank, len(m)):
        if m[r][ncols] % q:
            return "INCONSISTENT", 0, None
    sol = [0] * ncols
    for r, col in enumerate(pivots):
        sol[col] = m[r][ncols]
    return ("FORCED" if rank == ncols else "UNDERDETERMINED",
            q ** (ncols - rank), sol)


def orbit_constraints(vectors):
    """10 ring evaluations from gen1->gen2, gen2->gen3; returns point map or
    None on a point-level conflict (orbit not a CA evolution of any rule)."""
    pm = {}
    for src, dst in ((vectors[0], vectors[1]), (vectors[1], vectors[2])):
        for i in range(5):
            pt = (src[(i - 1) % 5], src[i], src[(i + 1) % 5])
            if pt in pm and pm[pt] != dst[i]:
                return None
            pm[pt] = dst[i]
    return pm


def classify(vectors, q=7, vt=True):
    pm = orbit_constraints(vectors)
    if pm is None:
        return {"status": "CONFLICT"}
    if vt:
        if pm.get((0, 0, 0), 0) != 0:
            return {"status": "CONFLICT", "detail": "vacuum transparency violated"}
        pm[(0, 0, 0)] = 0
    rows = [monomial_row(*pt, q=q) for pt in pm]
    rhs = list(pm.values())
    status, nsol, sol = gf_solve(rows, rhs, q)
    if status == "INCONSISTENT":
        return {"status": "NO_MULTILINEAR", "distinct_points": len(pm)}
    out = {"status": status, "n_solutions": nsol, "distinct_points": len(pm)}
    if status == "FORCED":
        out["rule_coeffs"] = sol
    return out


def conjugates_of_p(q=7):
    """g_t(L,C,R) = t*p(t^-1 L, t^-1 C, t^-1 R) for units t; coefficient
    vectors in MONOMIALS order: scale coefficient of degree-d monomial by
    t^(1-d)."""
    conj = {}
    for t in range(1, q):
        coeffs = []
        for (eL, eC, eR), c in zip(MONOMIALS, P_COEFFS):
            d = eL + eC + eR
            coeffs.append(c * pow(t, (1 - d) % (q - 1), q) % q)
        conj[t] = coeffs
    return conj


CONJ = conjugates_of_p()


def reduce_triples(alpha, beta, gamma, m):
    return [[(alpha * TRIPLES[f][g][0] + beta * TRIPLES[f][g][1]
              + gamma * TRIPLES[f][g][2]) % m for f in ORDER] for g in range(3)]


def eval_rule(coeffs, L, C, R, q=7):
    return sum(c * pow(L, e[0], q) * pow(C, e[1], q) * pow(R, e[2], q)
               for e, c in zip(MONOMIALS, coeffs)) % q


def shadow_closed(coeffs, image):
    """Shadow-Closure Criterion: rule maps image^3 into image."""
    return all(eval_rule(coeffs, x, y, z) in image
               for x in image for y in image for z in image)


def hom_image(alpha, beta, gamma, m):
    """Image of the form over Z^3 = subgroup generated by gcd(alpha,beta,gamma,m)."""
    import math
    d = math.gcd(math.gcd(alpha, beta), math.gcd(gamma, m)) or m
    d = math.gcd(d, m)
    return set(range(0, m, d)) if d else {0}


def bruteforce_check(vectors, expected_sol, q=7):
    """T1: verify FORCED verdict over all q^8 multilinear rules."""
    pm = orbit_constraints(vectors)
    pm[(0, 0, 0)] = 0
    import numpy as np
    grid = np.array(list(itertools.product(range(q), repeat=8)), dtype=np.int64)
    em = np.array([monomial_row(*pt, q=q) for pt in pm], dtype=np.int64)
    tg = np.array(list(pm.values()), dtype=np.int64)
    mask = ((grid @ em.T) % q == tg).all(axis=1)
    n = int(mask.sum())
    sol = grid[mask][0].tolist() if n == 1 else None
    return n == 1 and sol == expected_sol


results = {"tier1_gf7": {}, "summary": {}}
forced = []
status_counts = {}
total_forms = 0

for m in range(2, 8):
    for alpha, beta, gamma in itertools.product(range(m), repeat=3):
        if (alpha, beta, gamma) == (0, 0, 0):
            continue
        total_forms += 1
        vec = reduce_triples(alpha, beta, gamma, m)
        res = classify(vec)
        status_counts[res["status"]] = status_counts.get(res["status"], 0) + 1
        if res["status"] == "FORCED":
            sol = res["rule_coeffs"]
            tmatch = next((t for t, c in CONJ.items() if c == sol), None)
            bf = bruteforce_check(vec, sol)
            img = hom_image(alpha, beta, gamma, m)
            scc = shadow_closed(sol, img)
            forced.append({"form": [alpha, beta, gamma], "m": m,
                           "rule_coeffs": sol, "conjugate_of_p_t": tmatch,
                           "bruteforce_verified": bf,
                           "image": sorted(img), "shadow_closed": scc})
            print(f"FORCED: ({alpha},{beta},{gamma}) mod {m} -> rule {sol} "
                  f"= g_t, t={tmatch}; brute-force 7^8 verified: {bf}; "
                  f"shadow-closed on im={sorted(img)}: {scc}")

results["tier1_gf7"] = {"total_nonzero_forms": total_forms,
                        "status_counts": status_counts,
                        "forced_survivors": forced}
print(f"\nTier 1 (GF(7) variant): {total_forms} forms; statuses {status_counts}")

# pre-registered P1 check (raw FORCED) and re-registered P1' (FORCED + SCC)
p1_expected = {((1, 1, 1), 2): 1, ((2, 2, 2), 4): 2, ((3, 3, 3), 6): 3}
p1_found = {(tuple(f["form"]), f["m"]): f["conjugate_of_p_t"] for f in forced}
results["summary"]["P1_raw_pass"] = p1_found == p1_expected
p1p_found = {(tuple(f["form"]), f["m"]): f["conjugate_of_p_t"]
             for f in forced if f["shadow_closed"]}
results["summary"]["P1prime_scc_pass"] = p1p_found == p1_expected
print(f"P1 raw (FORCED only): {results['summary']['P1_raw_pass']}  found={p1_found}")
print(f"P1' (FORCED + shadow-closure): {results['summary']['P1prime_scc_pass']}  "
      f"found={p1p_found}")

# ----------------------------------------------------------------------
# Named neighbor nulls (must each FAIL forcing)
# ----------------------------------------------------------------------
neighbors = {
    "sum_mod_4": (1, 1, 1, 4), "sum_mod_6": (1, 1, 1, 6),
    "sum_mod_3": (1, 1, 1, 3), "sum_mod_5": (1, 1, 1, 5),
    "sum_mod_7": (1, 1, 1, 7),
    "two_two_two_mod_6_factors_through_mod3": (2, 2, 2, 6),
    "pair_ab_parity": (1, 1, 0, 2), "pair_ac_parity": (1, 0, 1, 2),
    "pair_bc_parity": (0, 1, 1, 2),
    "a_parity": (1, 0, 0, 2), "b_parity": (0, 1, 0, 2), "c_parity": (0, 0, 1, 2),
}
nn = {}
for name, (a, b, c, m) in neighbors.items():
    res = classify(reduce_triples(a, b, c, m))
    nn[name] = {k: v for k, v in res.items() if k != "rule_coeffs"}
    nn[name]["forcing_fails"] = res["status"] != "FORCED"
    print(f"neighbor null {name}: {res['status']}"
          + (f" (n={res.get('n_solutions')})" if "n_solutions" in res else ""))
results["neighbor_nulls"] = nn
results["summary"]["all_neighbor_nulls_fail_forcing"] = all(
    v["forcing_fails"] for v in nn.values())

# ----------------------------------------------------------------------
# Native-field annex: solve over GF(m) for prime m (R31 continuity)
# ----------------------------------------------------------------------
native = {}
for m in (2, 3, 5, 7):
    res = classify(reduce_triples(1, 1, 1, m), q=m)
    native[m] = res
    print(f"native GF({m}) sum-mod-{m}: {res['status']}"
          + (f" rule={res.get('rule_coeffs')}" if res["status"] == "FORCED" else ""))
# CUP-4 anchor: GF(2) multilinear class == all 256 ECA rules; orbit-only count
pm2 = orbit_constraints(reduce_triples(1, 1, 1, 2))
rows2 = [monomial_row(*pt, q=2) for pt in pm2]
st2, n2, _ = gf_solve(rows2, list(pm2.values()), 2)
native["gf2_orbit_only_solutions"] = n2  # expect 2 == |{110, 111}|
print(f"native GF(2) orbit-only solutions: {n2} (expect 2 = |{{110,111}}|)")
results["native_field_annex"] = native

# ----------------------------------------------------------------------
# Data-perturbation null: +1 on any single component of any single triple
# ----------------------------------------------------------------------
pert = {"total": 0, "forcing_p_survives": 0, "outcomes": {}}
for fam in ORDER:
    for g in range(3):
        for comp in range(3):
            t2 = {f: [list(x) for x in v] for f, v in TRIPLES.items()}
            t2[fam][g][comp] += 1
            vec = [[(sum(t2[f][gg])) % 2 for f in ORDER] for gg in range(3)]
            pm = orbit_constraints(vec)
            if pm is None:
                st = "CONFLICT"
            elif pm.get((0, 0, 0), 0) != 0:
                st = "CONFLICT"
            else:
                pm[(0, 0, 0)] = 0
                s, n, sol = gf_solve([monomial_row(*pt, q=7) for pt in pm],
                                     list(pm.values()), 7)
                st = ("FORCED_p" if s == "FORCED" and sol == P_COEFFS else
                      "FORCED_other" if s == "FORCED" else
                      "NO_MULTILINEAR" if s == "INCONSISTENT" else "UNDERDETERMINED")
            pert["outcomes"][st] = pert["outcomes"].get(st, 0) + 1
            pert["total"] += 1
            if st == "FORCED_p":
                pert["forcing_p_survives"] += 1
results["data_perturbation_null"] = pert
print(f"data-perturbation null (45 single +1 perturbations): {pert['outcomes']}; "
      f"perturbations still forcing p: {pert['forcing_p_survives']}")

with open(os.path.join(_HERE, "parity_projection_homomorphism_battery_results.json"),
          "w") as f:
    json.dump(results, f, indent=1)
print("\nArtifact: parity_projection_homomorphism_battery_results.json")
signal.alarm(0)
