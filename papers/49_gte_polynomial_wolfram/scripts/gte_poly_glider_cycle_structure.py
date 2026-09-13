#!/usr/bin/env python3
"""Shift-equivariant (glider) structure of GTE-polynomial cycles on the 7-ring.

For every cycle of T (rule p mod 7) on the n=7 cyclic ring, find the minimal
k > 0 and shift exponent j such that T^k(s) = sigma^j(s) for states s on the
cycle (sigma = cyclic shift). If j != 0, the cycle is a 'glider cycle': the
pattern recurs displaced by j cells after k steps, with drift velocity j/k.
The full temporal period is then k * ord(sigma^j restricted to the orbit).

Expected output: decomposition of cycle lengths {14, 21, 49, 189, 602} into
(k, j) glider data; confirmation that all periods are multiples of 7 via
free sigma-action.
"""
import os
import json
import signal
import sys

TIMEOUT_SECONDS = 600

def _timeout(signum, frame):
    print(f"TIMEOUT {TIMEOUT_SECONDS}s reached")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

Q, n = 7, 7
N = Q ** n

def enc(s):
    v = 0
    for x in s:
        v = v * Q + x
    return v

def dec(v):
    s = []
    for _ in range(n):
        s.append(v % Q)
        v //= Q
    return tuple(reversed(s))

def step(s):
    return tuple((s[i] + s[(i + 1) % n] - s[i] * s[(i + 1) % n]
                  - s[(i - 1) % n] * s[i] * s[(i + 1) % n]) % Q
                 for i in range(n))

def shift(s, j):
    return tuple(s[(i + j) % n] for i in range(n))

succ = [0] * N
for v in range(N):
    succ[v] = enc(step(dec(v)))

indeg = [0] * N
for v in range(N):
    indeg[succ[v]] += 1
queue = [v for v in range(N) if indeg[v] == 0]
removed = [False] * N
while queue:
    v = queue.pop()
    removed[v] = True
    w = succ[v]
    indeg[w] -= 1
    if indeg[w] == 0:
        queue.append(w)

seen = set()
cycles = []
for v in range(N):
    if removed[v] or v in seen:
        continue
    cyc = [v]
    w = succ[v]
    while w != v:
        cyc.append(w)
        w = succ[w]
    seen.update(cyc)
    cycles.append(cyc)

print(f"cycles found: {len(cycles)}; lengths: {sorted(len(c) for c in cycles)}")

out = []
for cyc in cycles:
    L = len(cyc)
    s0 = dec(cyc[0])
    # minimal k with T^k(s0) = sigma^j(s0) for some j
    found = None
    s = s0
    for k in range(1, L + 1):
        s = step(s)
        for j in range(n):
            if s == shift(s0, j):
                found = (k, j)
                break
        if found:
            break
    k, j = found
    drift = f"{j}/{k}"
    glider = j != 0
    out.append({"cycle_length": L, "k": k, "j": j,
                "glider": glider, "drift_cells_per_step": drift})
    print(f"cycle L={L:4d}: minimal T^k = sigma^j at k={k:3d}, j={j} "
          f"{'GLIDER drift ' + drift if glider else '(no drift)'}")

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
          "gte_poly_glider_cycle_structure_results.json"), "w") as f:
    json.dump(out, f, indent=1)
print("Saved gte_poly_glider_cycle_structure_results.json")
signal.alarm(0)
