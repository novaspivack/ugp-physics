#!/usr/bin/env python3
"""
Regenerates triangle_projection_battery_results.json (the canonical
four-projection battery artifact: total / a / b / c parity of the GTE
triples) with the comparison flags computed in the pinned monomial ordering
(1, L, C, R, LC, LR, CR, LCR).  The originally shipped artifact carried
stale comparison flags ("unique_and_equal_p": false for total parity) from
a pre-correction run of an inline snippet whose comparison constant used a
different monomial ordering; the solver mathematics agreed throughout and
the corrected verdicts were recorded in the session record, but the JSON
was never re-emitted.  This script re-derives all four entries exactly and
writes the corrected artifact.

Expected: total parity -> 1 multilinear solution == p; a/b parity ->
CONFLICT; c parity -> 343 solutions, p not among them.
"""

import json
import os
import signal
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))

TIMEOUT_SECONDS = 300


def _t(signum, frame):
    print("TIMEOUT")
    sys.exit(1)


signal.signal(signal.SIGALRM, _t)
signal.alarm(TIMEOUT_SECONDS)

MONOMIALS = [(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1),
             (1, 1, 0), (1, 0, 1), (0, 1, 1), (1, 1, 1)]
P_COEFFS = [0, 0, 1, 1, 0, 0, 6, 6]
TRIPLES = {
    "e":   [(1, 73, 823), (9, 42, 1023), (5, 275, 65535)],
    "u":   [(5, 9, 275), (5, 275, 65535), (76, 337920, -1)],
    "d":   [(9, 5, 42), (9, 186, 1023), (5, 8191, 65535)],
    "nuR": [(2, 5, 5), (7, 11, 13), (17, 19, 23)],
    "nuL": [(1, 1, 823), (9, 1, 1023), (5, 1, 65535)],
}
ORDER = ["e", "u", "d", "nuR", "nuL"]


def monomial_row(L, C, R):
    return [pow(L, eL, 7) * pow(C, eC, 7) * pow(R, eR, 7) % 7
            for (eL, eC, eR) in MONOMIALS]


def gf7_solve_full(pm):
    """Returns (n_solutions, unique_sol_or_None, all_sols_if_small)."""
    rows = [monomial_row(*pt) + [out % 7] for pt, out in pm.items()]
    rank, pivots = 0, []
    for col in range(8):
        piv = next((r for r in range(rank, len(rows)) if rows[r][col] % 7), None)
        if piv is None:
            continue
        rows[rank], rows[piv] = rows[piv], rows[rank]
        inv = pow(rows[rank][col], 5, 7)
        rows[rank] = [(x * inv) % 7 for x in rows[rank]]
        for r in range(len(rows)):
            if r != rank and rows[r][col] % 7:
                f = rows[r][col]
                rows[r] = [(a - f * b) % 7 for a, b in zip(rows[r], rows[rank])]
        pivots.append(col)
        rank += 1
    for r in range(rank, len(rows)):
        if rows[r][8] % 7:
            return 0, None, []
    nsol = 7 ** (8 - rank)
    part = [0] * 8
    for r, col in enumerate(pivots):
        part[col] = rows[r][8]
    if rank == 8:
        return 1, part, [part]
    # enumerate the affine solution space if small enough to check p-membership
    free_cols = [c for c in range(8) if c not in pivots]
    sols = []
    if nsol <= 7 ** 4:
        import itertools
        for assign in itertools.product(range(7), repeat=len(free_cols)):
            sol = part[:]
            for fc, val in zip(free_cols, assign):
                sol[fc] = val
            # re-solve pivot entries given free values
            ok_sol = sol[:]
            # build from reduced rows: pivot var = rhs - sum(free coeffs)
            for r, col in enumerate(pivots):
                s = rows[r][8]
                for fc in free_cols:
                    s -= rows[r][fc] * ok_sol[fc]
                ok_sol[col] = s % 7
            sols.append(ok_sol)
    return nsol, None, sols


def projection(component):
    """component: 'total', 0, 1, 2 -> parity vectors of the triples."""
    vecs = []
    for g in range(3):
        row = []
        for f in ORDER:
            t = TRIPLES[f][g]
            v = sum(t) % 2 if component == "total" else t[component] % 2
            row.append(v)
        vecs.append(row)
    return vecs


results = {"_provenance": (
    "Regenerated with the pinned monomial ordering (1,L,C,R,LC,LR,CR,LCR); "
    "supersedes the originally shipped artifact whose comparison flags "
    "(unique_and_equal_p / p_among_solutions) were emitted by a "
    "pre-correction snippet with a mismatched comparison constant. "
    "Solver verdicts (solution counts, conflicts) unchanged.")}

for name, comp in [("total_parity", "total"), ("a_parity", 0),
                   ("b_parity", 1), ("c_parity", 2)]:
    vecs = projection(comp)
    pm = {}
    conflict = False
    for src, dst in ((vecs[0], vecs[1]), (vecs[1], vecs[2])):
        for i in range(5):
            pt = (src[(i - 1) % 5], src[i], src[(i + 1) % 5])
            if pt in pm and pm[pt] != dst[i]:
                conflict = True
            pm[pt] = dst[i]
    entry = {"vectors": vecs}
    if conflict:
        entry["verdict"] = "CONFLICT (not functional)"
    else:
        if pm.get((0, 0, 0), 0) != 0:
            entry["verdict"] = "CONFLICT (vacuum transparency violated)"
        else:
            pm[(0, 0, 0)] = 0
            nsol, uniq, sols = gf7_solve_full(pm)
            entry["verdict"] = f"{nsol} multilinear solutions"
            entry["unique_and_equal_p"] = (nsol == 1 and uniq == P_COEFFS)
            entry["p_among_solutions"] = P_COEFFS in sols if sols else None
    results[name] = entry
    print(f"{name}: {entry['verdict']}"
          + (f" | unique==p: {entry.get('unique_and_equal_p')}"
             f" | p among: {entry.get('p_among_solutions')}"
             if "unique_and_equal_p" in entry else ""))

with open(os.path.join(_HERE, "triangle_projection_battery_results.json"), "w") as f:
    json.dump(results, f, indent=1)
print("\nArtifact rewritten: triangle_projection_battery_results.json")
signal.alarm(0)
