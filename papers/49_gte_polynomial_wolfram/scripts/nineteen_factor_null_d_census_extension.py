#!/usr/bin/env python3
"""Extended null d-census for the nineteen-factor neighborhood question.

24 additional Rule-110-compatible non-multilinear cubics over GF(7) on the
5-ring (seed 88, disjoint from the battery's seed 20260609):
f = p + (L^2-L) l1 + (C^2-C) l2 + (R^2-R) l3 with li random linear forms.
All agree with Rule 110 on the 8 binary points by construction.

Records the n-free part d of every sigma-linked cycle and whether d = 19 or
d = 9 (the two GF(7^3)-carried candidates among divisors of 342) ever occurs.
"""
import os
import json
import random
import signal
import sys

TIMEOUT_SECONDS = 900
signal.signal(signal.SIGALRM, lambda s, f: sys.exit("TIMEOUT"))
signal.alarm(TIMEOUT_SECONDS)

Q, n = 7, 5
R110 = {(1, 1, 1): 0, (1, 1, 0): 1, (1, 0, 1): 1, (1, 0, 0): 0,
        (0, 1, 1): 1, (0, 1, 0): 1, (0, 0, 1): 1, (0, 0, 0): 0}


def enumerate_cycles(step):
    N = Q ** n
    nxt = [0] * N
    for v in range(N):
        vv, s = v, [0] * n
        for i in range(n - 1, -1, -1):
            s[i] = vv % Q
            vv //= Q
        w = step(tuple(s))
        e = 0
        for c in w:
            e = e * Q + c
        nxt[v] = e
    visited = [False] * N
    cycles = {}
    for v0 in range(N):
        if visited[v0]:
            continue
        path, pos, v = [], {}, v0
        while not visited[v] and v not in pos:
            pos[v] = len(path)
            path.append(v)
            v = nxt[v]
        if v in pos:
            cyc = path[pos[v]:]
            cycles.setdefault(len(cyc), []).append(cyc[0])
        for u in path:
            visited[u] = True
    return cycles


def dec(v):
    s = [0] * n
    for i in range(n - 1, -1, -1):
        s[i] = v % Q
        v //= Q
    return tuple(s)


def nfree(N):
    d = N
    while d % n == 0:
        d //= n
    return d


random.seed(88)
census = {}
rule_summaries = []
for trial in range(24):
    co = [[random.randrange(7) for _ in range(4)] for _ in range(3)]

    def rule(L, C, R, co=co):
        base = C + R - C * R - L * C * R
        vL = (L * L - L) * (co[0][0] + co[0][1] * L + co[0][2] * C + co[0][3] * R)
        vC = (C * C - C) * (co[1][0] + co[1][1] * L + co[1][2] * C + co[1][3] * R)
        vR = (R * R - R) * (co[2][0] + co[2][1] * L + co[2][2] * C + co[2][3] * R)
        return (base + vL + vC + vR) % 7
    assert all(rule(*k) == v for k, v in R110.items())

    def step(s):
        return tuple(rule(s[(i - 1) % n], s[i], s[(i + 1) % n])
                     for i in range(n))
    cycles = enumerate_cycles(step)
    ds = []
    for Lc, reps in cycles.items():
        if Lc == 1:
            continue
        # sigma-linked iff shift of a cycle state stays on the same cycle
        s0 = dec(reps[0])
        cyc = [s0]
        s = step(s0)
        while s != s0:
            cyc.append(s)
            s = step(s)
        sh = tuple(s0[(i + 1) % n] for i in range(n))
        if sh in set(cyc):
            d = nfree(Lc)
            ds.append((Lc, d))
            census[d] = census.get(d, 0) + 1
    rule_summaries.append({"trial": trial, "sigma_linked_N_d": ds})
    print(f"rule #{trial}: sigma-linked (N, d) = {ds}")

print(f"\nextended census (24 rules, seed 88): {dict(sorted(census.items()))}")
print(f"d = 19 occurrences: {census.get(19, 0)}; "
      f"d = 9 occurrences: {census.get(9, 0)}")
out = {"seed": 88, "n_rules": 24,
       "census": {str(k): v for k, v in sorted(census.items())},
       "d19": census.get(19, 0), "d9": census.get(9, 0),
       "rules": rule_summaries}
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
          "nineteen_factor_null_d_census_extension_results.json"), "w") as f:
    json.dump(out, f, indent=1)
print("Saved nineteen_factor_null_d_census_extension_results.json")
signal.alarm(0)
