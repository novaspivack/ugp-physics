#!/usr/bin/env python3
"""Parameters of the GTE constraint code over GF(7).

Codewords of length n: cyclic strings s in GF(7)^n with
p(s_{i-1}, s_i, s_{i+1}) = 0 mod 7 for all i (indices cyclic), where
p(L,C,R) = C+R-CR-LCR. The codeword set is exactly the zero-energy
(ground-state) space of the P50 spin-7 chain on a ring.

Computes, for n = 3..12:
  - K(n): number of codewords (transfer-matrix count on pair states, plus
    direct enumeration cross-check for n <= 8)
  - k(n) = log_7 K(n): effective code dimension
  - d(n): exact minimum nonzero Hamming distance between distinct codewords
    (exhaustive over codeword pairs; codeword sets are small)
  - rate R = k/n and relative distance delta = d/n

Expected output: K(7) related to Phi_6(7)=43 structure; distance growth trend.
"""
import json
import signal
import sys
from itertools import product
from pathlib import Path

TIMEOUT_SECONDS = 600

def _timeout(signum, frame):
    print(f"TIMEOUT {TIMEOUT_SECONDS}s reached")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

Q = 7

def p(L, C, R):
    return (C + R - C * R - L * C * R) % Q

# V(p): allowed windows
V = {(L, C, R) for L in range(Q) for C in range(Q) for R in range(Q)
     if p(L, C, R) == 0}
print(f"|V(p)(GF(7))| = {len(V)} (= Phi_6(7) = 43 expected)")

# Transfer matrix on pair states (a,b) -> (b,c) allowed iff (a,b,c) in V
import numpy as np
pairs = [(a, b) for a in range(Q) for b in range(Q)]
idx = {pr: i for i, pr in enumerate(pairs)}
T = np.zeros((49, 49), dtype=np.int64)
for (a, b) in pairs:
    for c in range(Q):
        if (a, b, c) in V:
            T[idx[(a, b)], idx[(b, c)]] += 1

def count_cyclic(n):
    # number of cyclic strings with all windows allowed = trace(T^n)
    return int(np.trace(np.linalg.matrix_power(T, n)))

def enumerate_codewords(n):
    # direct enumeration (feasible n <= 8: 7^8 = 5.7M)
    words = []
    for s in product(range(Q), repeat=n):
        ok = all(p(s[(i - 1) % n], s[i], s[(i + 1) % n]) == 0 for i in range(n))
        if ok:
            words.append(s)
    return words

def min_distance(words):
    if len(words) < 2:
        return None
    best = None
    for i in range(len(words)):
        wi = words[i]
        for j in range(i + 1, len(words)):
            d = sum(1 for a, b in zip(wi, words[j]) if a != b)
            if best is None or d < best:
                best = d
    return best

import math
rows = []
for n in range(3, 13):
    K_tm = count_cyclic(n)
    entry = {"n": n, "K_transfer_matrix": K_tm,
             "k_log7": math.log(K_tm, 7) if K_tm > 0 else 0}
    if n <= 8:
        words = enumerate_codewords(n)
        assert len(words) == K_tm, f"mismatch at n={n}: {len(words)} vs {K_tm}"
        d = min_distance(words)
        entry["K_enumerated"] = len(words)
        entry["d_min"] = d
        entry["rate"] = entry["k_log7"] / n
        entry["rel_distance"] = (d / n) if d else None
        # sample codewords for inspection (cap)
        entry["sample_codewords"] = [list(w) for w in words[:12]]
    rows.append(entry)
    dstr = entry.get("d_min", "—")
    print(f"n={n:2d}  K={K_tm:8d}  k=log7(K)={entry['k_log7']:.3f}  d_min={dstr}")

# Spectral data of T (growth rate of code size)
eigs = np.linalg.eigvals(T.astype(float))
lam1 = max(abs(eigs))
print(f"\nPerron eigenvalue of pair transfer matrix: {lam1:.6f} "
      f"(asymptotic codewords ~ lam1^n; rate -> log7(lam1) = {math.log(lam1,7):.4f})")

results = {"V_size": len(V), "table": rows,
           "perron_eigenvalue": float(lam1),
           "asymptotic_rate_log7": float(math.log(lam1, 7))}
with open(Path(__file__).resolve().parent / "gte_code_parameters_results.json", "w") as f:
    json.dump(results, f, indent=1)
print("Saved gte_code_parameters_results.json")
signal.alarm(0)
