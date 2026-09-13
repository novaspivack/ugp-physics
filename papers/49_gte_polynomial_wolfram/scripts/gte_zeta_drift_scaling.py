#!/usr/bin/env python3
"""Drift-3/7 mechanism tests: GTE-polynomial ring cycles vs CMCA ether rate.

Shift convention used throughout: (sigma^j s)[i] = s[(i+j) mod n]  (pattern
displaced LEFT by j cells). A glider relation T^k = sigma^j therefore means
the pattern moves left by j cells every k steps; mod-n equivalence j == j-n.

Tests:
 1. n=7 GF(7) ring: glider data of all cycles (reference) + binarity profile
    of the L=49 drift cycle (fraction of cell values in {0,1}).
 2. Rule 110 on binary rings n = 3..22: full cycle spectra + glider (k,j)
    data; occurrences of T^7 = sigma^{3 or 4} analogues.
 3. The P45 14-cell ether tile [1,0,0,1,1,0,1,1,1,1,1,0,0,0] on the 14-ring:
    minimal (k,j) with T^k = sigma^j; per-parity state-1 occupancy per period
    (P45 firing counts 3/7 odd, 5/7 even).
 4. GF(7) bulk sampling at n = 8..14: 300 random initial states per n,
    iterate to the attractor cycle (hash detection, step cap), classify
    glider (k,j) of each distinct attractor with L <= cap; report drift
    classes, especially any T^7 = sigma^{+-3} analogues.

Expected output: ether (k,j) and occupancies; drift-class tables per n.
"""
import os
import json
import signal
import sys
import time
from math import gcd

TIMEOUT_SECONDS = 1200
signal.signal(signal.SIGALRM, lambda s, f: sys.exit("TIMEOUT"))
signal.alarm(TIMEOUT_SECONDS)

Q = 7

def step_gf7(s, n):
    return tuple((s[i] + s[(i + 1) % n] - s[i] * s[(i + 1) % n]
                  - s[(i - 1) % n] * s[i] * s[(i + 1) % n]) % Q
                 for i in range(n))

def rule110_step(s, n):
    out = []
    for i in range(n):
        L, C, R = s[(i - 1) % n], s[i], s[(i + 1) % n]
        out.append((C + R - C * R - L * C * R) % 2)
    return tuple(out)

def shift(s, j, n):
    return tuple(s[(i + j) % n] for i in range(n))

def glider_data(s0, stepf, n, cap=250000):
    """Minimal (k, j) with stepf^k(s0) = sigma^j(s0); also the cycle length."""
    s = s0
    for k in range(1, cap + 1):
        s = stepf(s, n)
        for j in range(n):
            if s == shift(s0, j, n):
                # cycle length L = k * order of sigma^j on the orbit closure
                L = k
                t = s
                while t != s0:
                    for _ in range(k):
                        t = stepf(t, n)
                    L += k
                return k, j, L
    return None

results = {}

# --- Part 1: n=7 reference + binarity of the 49-cycle ---
n = 7
# find the 49-cycle by iterating from states until hitting length-49 cycle
import itertools, random
random.seed(7)
found_cycles = {}
for trial in range(4000):
    s = tuple(random.randrange(Q) for _ in range(n))
    seen = {}
    t = 0
    while s not in seen and t < 5000:
        seen[s] = t
        s = step_gf7(s, n)
        t += 1
    if s in seen:
        L = t - seen[s]
        if L not in found_cycles:
            found_cycles[L] = s
    if set(found_cycles) >= {14, 21, 49, 189, 602}:
        break
ref = {}
for L, s0 in sorted(found_cycles.items()):
    kd = glider_data(s0, step_gf7, n)
    # binarity: fraction of cell values in {0,1} around the cycle
    vals = []
    s = s0
    for _ in range(L):
        vals.extend(s)
        s = step_gf7(s, n)
    binfrac = sum(1 for v in vals if v in (0, 1)) / len(vals)
    ref[L] = {"k": kd[0], "j": kd[1], "binary_fraction": round(binfrac, 4)}
    print(f"n=7 cycle L={L}: T^{kd[0]} = sigma^{kd[1]}, "
          f"binary fraction {binfrac:.3f}")
results["n7_reference"] = {str(k): v for k, v in ref.items()}

# --- Part 2: Rule 110 on rings n=3..19 (memoized transient routing) ---
r110 = {}
for n in range(3, 20):
    spec = {}
    gl = []
    visited = set()       # any state already routed to its attractor
    cycle_states = set()
    for bits in itertools.product((0, 1), repeat=n):
        if bits in visited:
            continue
        path = []
        s = bits
        while s not in visited:
            visited.add(s)
            path.append(s)
            s = rule110_step(s, n)
        if s in cycle_states or s not in set(path):
            continue  # ran into an already-known attractor
        # new cycle found, starting at s
        cyc = [s]
        w = rule110_step(s, n)
        while w != s:
            cyc.append(w)
            w = rule110_step(w, n)
        cycle_states.update(cyc)
        Lc = len(cyc)
        spec[Lc] = spec.get(Lc, 0) + 1
        kd = glider_data(s, rule110_step, n)
        if kd and kd[1] != 0:
            gl.append(f"T^{kd[0]}=s^{kd[1]}")
    r110[n] = {"spectrum": {str(k): v for k, v in sorted(spec.items())},
               "gliders": sorted(set(gl))}
    print(f"R110 ring n={n:2d}: spectrum {dict(sorted(spec.items()))} "
          f"gliders {sorted(set(gl))}")
results["rule110_rings"] = r110

# --- Part 3: the P45 ether tile on the 14-ring ---
ether = (1, 0, 0, 1, 1, 0, 1, 1, 1, 1, 1, 0, 0, 0)
n = 14
kd = glider_data(ether, rule110_step, n)
print(f"\nP45 ether tile on 14-ring: T^{kd[0]} = sigma^{kd[1]} "
      f"(cycle length {kd[2]})")
# occupancy: fraction of steps each cell is 1 over one temporal period
period = kd[2]
occ = [0] * n
s = ether
for _ in range(period):
    for i in range(n):
        occ[i] += s[i]
    s = rule110_step(s, n)
odd_occ = [occ[i] / period for i in range(1, n, 2)]
even_occ = [occ[i] / period for i in range(0, n, 2)]
print(f"ether occupancy per cell over period {period}: "
      f"{[round(o / period, 3) for o in occ]}")
print(f"odd cells mean occupancy = {sum(odd_occ)/len(odd_occ):.4f}, "
      f"even cells mean = {sum(even_occ)/len(even_occ):.4f}")
results["ether_tile"] = {"k": kd[0], "j": kd[1], "cycle_length": kd[2],
                         "occupancy_per_cell": [o / period for o in occ],
                         "odd_mean": sum(odd_occ) / len(odd_occ),
                         "even_mean": sum(even_occ) / len(even_occ)}

# --- Part 4: GF(7) bulk sampling n=8..14 ---
bulk = {}
for n in range(8, 15):
    t_n0 = time.time()
    drift_classes = {}
    spectra = {}
    for trial in range(300):
        if time.time() - t_n0 > 90:
            break
        s = tuple(random.randrange(Q) for _ in range(n))
        seen = {}
        t = 0
        while s not in seen and t < 100000:
            seen[s] = t
            s = step_gf7(s, n)
            t += 1
        if s not in seen:
            continue
        L = t - seen[s]
        if L in spectra:
            spectra[L] += 1
            continue
        spectra[L] = 1
        if L <= 20000:
            kd = glider_data(s, step_gf7, n, cap=L + 1)
            if kd:
                key = f"T^{kd[0]}=s^{kd[1]}"
                drift_classes[key] = drift_classes.get(key, 0) + 1
    bulk[n] = {"attractor_lengths_sampled": {str(k): v for k, v in
                                              sorted(spectra.items())},
               "drift_classes": drift_classes}
    print(f"GF7 bulk n={n:2d}: attractors {dict(sorted(spectra.items()))} "
          f"drift {drift_classes}")
results["gf7_bulk_sampling"] = bulk

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
          "gte_zeta_drift_scaling_results.json"), "w") as f:
    json.dump(results, f, indent=1)
print("Saved gte_zeta_drift_scaling_results.json")
signal.alarm(0)
