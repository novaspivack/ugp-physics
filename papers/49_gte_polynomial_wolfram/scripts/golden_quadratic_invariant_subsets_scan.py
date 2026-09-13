#!/usr/bin/env python3
"""Complete invariant-subset lattice of the GTE polynomial p over GF(q).

A subset S of GF(q) is an invariant sub-CA alphabet iff p(a,b,c) in S for all
(a,b,c) in S^3, where p(L,C,R) = C+R-CR-LCR mod q.

Exhaustive enumeration of all 2^q subsets for q in {2,3,5,7,11,13,17,19}
(and q=23 with early exit, capped by timeout). For q=29 (2^29 infeasible),
partial coverage: closures of all singletons and pairs are computed instead
and reported as such.

Purpose: establish the invariant-subset taxonomy per splitting branch of the
master quadratic x^2+x-1 (split q=+-1 mod 5 / inert q=+-2 mod 5 / ramified
q=5), in particular whether the binary floor {0,1} survives in the split
branch and what extra invariant structure golden roots generate.

Expected: {0} and {0,1} invariant for all q; extra golden singletons {k+-}
exactly in the split branch; q=5 carries the degenerate {2} plus known {0,2}
second ether.
"""
import os
import json
import signal
import sys
from itertools import combinations

TIMEOUT_SECONDS = 900

def _timeout(signum, frame):
    print(f"TIMEOUT {TIMEOUT_SECONDS}s reached; saving partial results")
    _save()
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

EXHAUSTIVE_Q = [2, 3, 5, 7, 11, 13, 17, 19, 23]
PARTIAL_Q = [29]

results = {"exhaustive": {}, "partial_closures": {}}

def _save():
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
          "golden_quadratic_invariant_subsets_scan_results.json"), "w") as f:
        json.dump(results, f, indent=1)

def p_table(q):
    tbl = {}
    for a in range(q):
        for b in range(q):
            for c in range(q):
                tbl[(a, b, c)] = (b + c - b * c - a * b * c) % q
    return tbl

def is_invariant(S, tbl):
    for a in S:
        for b in S:
            for c in S:
                if tbl[(a, b, c)] not in S:
                    return False
    return True

def closure(S0, tbl, q):
    S = set(S0)
    while True:
        new = set()
        for a in S:
            for b in S:
                for c in S:
                    v = tbl[(a, b, c)]
                    if v not in S:
                        new.add(v)
        if not new:
            return frozenset(S)
        S |= new
        if len(S) == q:
            return frozenset(S)

for q in EXHAUSTIVE_Q:
    tbl = p_table(q)
    invariant = []
    # iterate subsets by bitmask; check smallest first via popcount ordering not
    # needed -- early exit in is_invariant is fast enough
    for mask in range(1, 1 << q):
        S = frozenset(i for i in range(q) if mask >> i & 1)
        if is_invariant(S, tbl):
            invariant.append(sorted(S))
    proper = [s for s in invariant if 0 < len(s) < q]
    roots_m = [x for x in range(q) if (x * x + x - 1) % q == 0]
    results["exhaustive"][q] = {
        "q_mod_5": q % 5,
        "roots_master_quadratic": roots_m,
        "n_invariant_nonempty": len(invariant),
        "all_invariant_subsets": [sorted(s) for s in invariant],
        "proper_nontrivial": proper,
    }
    print(f"q={q} (q mod 5 = {q%5}): roots(m)={roots_m}  proper invariant subsets: {proper}")

for q in PARTIAL_Q:
    tbl = p_table(q)
    roots_m = [x for x in range(q) if (x * x + x - 1) % q == 0]
    closures = {}
    gens = [(k,) for k in range(q)] + list(combinations(range(q), 2))
    for g in gens:
        cl = closure(g, tbl, q)
        if len(cl) < q:
            closures[str(list(g))] = sorted(cl)
    # dedupe closed sets found
    distinct = sorted({tuple(v) for v in closures.values()})
    results["partial_closures"][q] = {
        "q_mod_5": q % 5,
        "roots_master_quadratic": roots_m,
        "coverage": "closures of all singletons and pairs only (2^29 exhaustive infeasible)",
        "distinct_proper_closed_sets": [list(t) for t in distinct],
    }
    print(f"q={q} (partial): roots(m)={roots_m}  distinct proper closed sets from <=2 generators: {[list(t) for t in distinct]}")

_save()
print("Saved golden_quadratic_invariant_subsets_scan_results.json")
signal.alarm(0)
