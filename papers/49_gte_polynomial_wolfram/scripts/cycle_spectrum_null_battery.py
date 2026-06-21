#!/usr/bin/env python3
"""Null battery for the n=7 cycle-spectrum specialness claims of the GTE polynomial.

Computes the full cycle spectrum, sigma-equivariant classification, and glider
drift data of the ring CA T_n for:
  (i)  30 random vacuum-preserving multilinear GF(7) rules
       f(L,C,R) = a1*L + a2*C + a3*R + a4*LC + a5*LR + a6*CR + a7*LCR  (a0 = 0),
  (ii) 10 structured competitors (mirror of p, coefficient perturbations of p,
       scalar multiple, truncations, linear rule, sign variants),
  (iii) the GTE polynomial p(L,C,R) = C+R-CR-LCR itself (reference row),
at ring sizes n = 5 and n = 7 (exhaustive enumeration, 16,807 and 823,543 states).

Pre-registered features per rule (recorded before interpretation):
  fix_count, n_cycles, cycle spectrum, per-cycle sigma class (invariant /
  free-orbit), reduced drift fractions, booleans: has length 14/21/49/189/602,
  all nontrivial lengths divisible by 7, has drift 3 cells per 7 steps,
  free-orbit lengths divisible by 7, n=5 spectrum equals {1, 475}.

Expected output range: per-rule feature table + null counts out of 30 random
rules for each feature shared with p.
"""
import os
import json
import signal
import sys
import time

import numpy as np

TIMEOUT_SECONDS = 1800
PER_RULE_SECONDS = 90

def _timeout(signum, frame):
    print(f"TIMEOUT {TIMEOUT_SECONDS}s reached; exiting")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

Q = 7
rng = np.random.default_rng(20260609)

# monomial order: (L, C, R, LC, LR, CR, LCR); constant term fixed to 0
P_COEFFS = (0, 1, 1, 0, 0, -1 % Q, -1 % Q)  # GTE polynomial p = C+R-CR-LCR

def mirror(c):
    # f(R,C,L): swap roles of L and R -> (a1,a2,a3,a4,a5,a6,a7) ->
    # L<->R: L->R term, LC->CR, LR->LR, CR->LC, LCR->LCR
    a1, a2, a3, a4, a5, a6, a7 = c
    return (a3, a2, a1, a6, a5, a4, a7)

structured = {
    "p_mirror_rule124": mirror(P_COEFFS),
    "p_coeff_C_to_2": (0, 2, 1, 0, 0, -1 % Q, -1 % Q),
    "p_coeff_R_to_2": (0, 1, 2, 0, 0, -1 % Q, -1 % Q),
    "p_coeff_CR_to_minus2": (0, 1, 1, 0, 0, -2 % Q, -1 % Q),
    "p_coeff_LCR_to_minus2": (0, 1, 1, 0, 0, -1 % Q, -2 % Q),
    "p_scaled_3p": tuple((3 * c) % Q for c in P_COEFFS),
    "p_truncated_quadratic": (0, 1, 1, 0, 0, -1 % Q, 0),
    "rule_linear_LCR_sum": (1, 1, 1, 0, 0, 0, 0),
    "p_all_plus_signs": (0, 1, 1, 0, 0, 1, 1),
    "p_qnr_twist_coeff3": (0, 1, 1, 0, 0, 3, 3),
}

def random_rule():
    return tuple(int(x) for x in rng.integers(0, Q, size=7))

rules = [("p_GTE", P_COEFFS)]
rules += [(name, c) for name, c in structured.items()]
seen = {P_COEFFS} | set(structured.values())
while sum(1 for nm, _ in rules if nm.startswith("rand")) < 30:
    c = random_rule()
    if c in seen:
        continue
    seen.add(c)
    rules.append((f"rand{len(rules):02d}", c))


def successor_array(coeffs, n):
    """Vectorized successor map over all Q**n ring states."""
    N = Q ** n
    v = np.arange(N, dtype=np.int64)
    digits = [(v // Q ** i) % Q for i in range(n)]  # digit i = cell i
    a1, a2, a3, a4, a5, a6, a7 = coeffs
    nxt = np.zeros(N, dtype=np.int64)
    for i in range(n):
        L = digits[(i - 1) % n]
        C = digits[i]
        R = digits[(i + 1) % n]
        val = (a1 * L + a2 * C + a3 * R + a4 * L * C + a5 * L * R
               + a6 * C * R + a7 * L * C * R) % Q
        nxt += val * Q ** i
    return nxt


def periodic_states(succ):
    """Batched Kahn peel: return boolean mask of states on cycles."""
    N = len(succ)
    indeg = np.bincount(succ, minlength=N)
    removed = np.zeros(N, dtype=bool)
    queue = np.flatnonzero(indeg == 0)
    while queue.size:
        removed[queue] = True
        dec = np.bincount(succ[queue], minlength=N)
        indeg -= dec
        cand = np.unique(succ[queue])
        queue = cand[(indeg[cand] == 0) & ~removed[cand]]
    return ~removed


def dec_state(v, n):
    return tuple(int((v // Q ** i) % Q) for i in range(n))


def enc_state(s):
    return sum(x * Q ** i for i, x in enumerate(s))


def shift_state(s, j):
    n = len(s)
    return tuple(s[(i + j) % n] for i in range(n))


def analyze_rule(coeffs, n, deadline):
    succ = successor_array(coeffs, n)
    per = periodic_states(succ)
    cyc_nodes = np.flatnonzero(per)
    seen = set()
    cycles = []
    for v in cyc_nodes:
        v = int(v)
        if v in seen:
            continue
        cyc = [v]
        w = int(succ[v])
        while w != v:
            cyc.append(w)
            w = int(succ[w])
        seen.update(cyc)
        cycles.append(cyc)
        if time.time() > deadline:
            return None
    # classify each cycle: sigma-invariant? glider (k,j)?
    spectrum = {}
    cyc_info = []
    cycle_id_of = {}
    for idx, cyc in enumerate(cycles):
        for v in cyc:
            cycle_id_of[v] = idx
    for idx, cyc in enumerate(cycles):
        L = len(cyc)
        spectrum[L] = spectrum.get(L, 0) + 1
        s0 = dec_state(cyc[0], n)
        sig = enc_state(shift_state(s0, 1))
        sigma_invariant = cycle_id_of[sig] == idx
        kj = None
        if sigma_invariant and L <= 200000:
            s = s0
            for k in range(1, L + 1):
                vv = int(succ[enc_state(s)])
                s = dec_state(vv, n)
                hit = next((j for j in range(n) if s == shift_state(s0, j)), None)
                if hit is not None:
                    kj = (k, hit)
                    break
                if time.time() > deadline:
                    return None
        cyc_info.append({"L": L, "sigma_invariant": bool(sigma_invariant),
                         "kj": kj})
    return spectrum, cyc_info


def features(spectrum, cyc_info, n):
    lengths = sorted(spectrum)
    nontriv = [L for L in lengths if L > 1]
    drifts = set()
    for c in cyc_info:
        if c["kj"] and c["kj"][1] != 0:
            from math import gcd
            k, j = c["kj"]
            g = gcd(k, j)
            drifts.add(f"{j // g}/{k // g}")
    free_lengths = sorted({c["L"] for c in cyc_info if not c["sigma_invariant"]})
    return {
        "fix_count": spectrum.get(1, 0),
        "n_cycles": sum(spectrum.values()),
        "spectrum": {str(k): v for k, v in sorted(spectrum.items())},
        "drift_fractions": sorted(drifts),
        "has_14": 14 in spectrum, "has_21": 21 in spectrum,
        "has_49": 49 in spectrum, "has_189": 189 in spectrum,
        "has_602": 602 in spectrum,
        "all_nontrivial_div_n": all(L % n == 0 for L in nontriv),
        "has_drift_3_per_7": "3/7" in drifts,
        "free_orbit_lengths": free_lengths,
        "free_orbits_all_div_n": (all(L % n == 0 for L in free_lengths)
                                   if free_lengths else None),
    }


results = {"rules": {}, "meta": {"seed": 20260609, "n_random": 30,
                                  "monomials": "L,C,R,LC,LR,CR,LCR (a0=0)"}}
t0 = time.time()
for name, coeffs in rules:
    deadline = time.time() + PER_RULE_SECONDS
    row = {"coeffs": list(coeffs)}
    out5 = analyze_rule(coeffs, 5, deadline)
    if out5 is None:
        row["n5"] = "TIMEOUT"
    else:
        sp5, ci5 = out5
        row["n5"] = features(sp5, ci5, 5)
        row["n5"]["matches_p_n5_spectrum"] = (sorted(sp5.items())
                                               == [(1, 1), (475, 1)])
    out7 = analyze_rule(coeffs, 7, deadline)
    if out7 is None:
        row["n7"] = "TIMEOUT"
    else:
        sp7, ci7 = out7
        row["n7"] = features(sp7, ci7, 7)
    results["rules"][name] = row
    f7 = row["n7"] if isinstance(row["n7"], str) else \
        {k: row["n7"][k] for k in ("fix_count", "n_cycles", "spectrum",
                                    "drift_fractions", "all_nontrivial_div_n")}
    print(f"{name:26s} {f7}")

# null statistics over the 30 random rules
rand_rows = [r["n7"] for nm, r in results["rules"].items()
             if nm.startswith("rand") and isinstance(r["n7"], dict)]
n_ok = len(rand_rows)
null_stats = {"n_random_completed": n_ok}
for feat in ("has_14", "has_21", "has_49", "has_189", "has_602",
             "all_nontrivial_div_n", "has_drift_3_per_7"):
    null_stats[feat] = sum(1 for r in rand_rows if r[feat])
null_stats["fix_count_eq_1"] = sum(1 for r in rand_rows
                                    if r["fix_count"] == 1)
null_stats["n_cycles_le_12"] = sum(1 for r in rand_rows
                                    if r["n_cycles"] <= 12)
null_stats["free_orbits_all_div_7"] = sum(
    1 for r in rand_rows if r["free_orbits_all_div_n"] is True)
null_stats["free_orbits_some_rule_has_them"] = sum(
    1 for r in rand_rows if r["free_orbit_lengths"])
rand5 = [r["n5"] for nm, r in results["rules"].items()
         if nm.startswith("rand") and isinstance(r["n5"], dict)]
null_stats["n5_matches_p_spectrum"] = sum(
    1 for r in rand5 if r.get("matches_p_n5_spectrum"))
results["null_stats"] = null_stats
print("\nNULL STATS (out of", n_ok, "random rules):")
for k, v in null_stats.items():
    print(f"  {k}: {v}")
print(f"elapsed {time.time() - t0:.1f}s")

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
          "cycle_spectrum_null_battery_results.json"), "w") as f:
    json.dump(results, f, indent=1)
print("Saved cycle_spectrum_null_battery_results.json")
signal.alarm(0)
