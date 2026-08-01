#!/usr/bin/env python3
"""All-q classification of the master quadratic m(x) = x^2 + x - 1 over GF(q).

The diagonal fixed-point factor of the GTE polynomial p(L,C,R) = C+R-CR-LCR
satisfies p(x,x,x) - x = -x(x^2+x-1) over Z. This script verifies, for every
prime q < 10^4, the dichotomy proved via quadratic reciprocity:

  m has a root in GF(q)  <=>  (5|q) = +1  <=>  q = +-1 (mod 5)     [q != 2,5]
  q = 5: ramified, double root k = 2;   q = 2: irreducible (inert-like).

Also verifies the singleton-invariant-subset corollary: the number of
singleton invariant sub-CAs of p over GF(q) equals 1 + #roots(m in GF(q)),
i.e. 3 (split) / 2 (ramified q=5) / 1 (inert), by directly counting diagonal
fixed points p(k,k,k) = k.

Expected output: zero mismatches across all primes q < 10^4.
"""
import os
import json
import signal
import sys

TIMEOUT_SECONDS = 300

def _timeout(signum, frame):
    print(f"TIMEOUT {TIMEOUT_SECONDS}s reached")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

LIMIT = 10_000

def primes_upto(n):
    sieve = [True] * (n + 1)
    sieve[0:2] = [False, False]
    for i in range(2, int(n ** 0.5) + 1):
        if sieve[i]:
            for j in range(i * i, n + 1, i):
                sieve[j] = False
    return [i for i in range(2, n + 1) if sieve[i]]

def legendre(a, q):
    a %= q
    if a == 0:
        return 0
    return 1 if pow(a, (q - 1) // 2, q) == 1 else -1

def p_diag(x, q):
    # p(x,x,x) = 2x - x^2 - x^3 mod q
    return (2 * x - x * x - x * x * x) % q

results = {"limit": LIMIT, "mismatches": [], "summary": {}}
counts = {"split": 0, "inert": 0, "ramified": 0, "char2": 0}
examples = {"split": None, "inert": None}

for q in primes_upto(LIMIT):
    roots = [x for x in range(q) if (x * x + x - 1) % q == 0]
    # singleton invariant subsets = diagonal fixed points of p
    diag_fps = [x for x in range(q) if p_diag(x, q) == x]
    # corollary check: diag fps = {0} union roots(m)
    corollary_ok = sorted(diag_fps) == sorted(set([0] + roots))

    if q == 2:
        expected_roots = 0
        branch = "char2"
    elif q == 5:
        expected_roots = 1  # double root k=2 counted once as a set element
        branch = "ramified"
    else:
        leg = legendre(5, q)
        qm5 = q % 5
        # reciprocity-derived dichotomy
        rec_ok = (leg == 1) == (qm5 in (1, 4))
        expected_roots = 2 if leg == 1 else 0
        branch = "split" if leg == 1 else "inert"
        if not rec_ok:
            results["mismatches"].append({"q": q, "type": "reciprocity", "leg": leg, "q_mod_5": qm5})

    ok = (len(roots) == expected_roots) and corollary_ok
    if q == 5:
        ok = ok and roots == [2]
    if not ok:
        results["mismatches"].append({"q": q, "roots": roots, "expected_n_roots": expected_roots,
                                      "diag_fps": diag_fps, "corollary_ok": corollary_ok})
    counts[branch] += 1
    if branch in examples and examples[branch] is None:
        examples[branch] = {"q": q, "roots": roots, "diag_fps": diag_fps}

n_primes = sum(counts.values())
results["summary"] = {
    "n_primes_checked": n_primes,
    "branch_counts": counts,
    "first_examples": examples,
    "all_match": len(results["mismatches"]) == 0,
    "q5_double_root": 2,
    "q2_irreducible": True,
}

print(f"Primes checked: {n_primes} (q < {LIMIT})")
print(f"Branch counts: {counts}")
print(f"Mismatches: {len(results['mismatches'])}")
print(f"ALL MATCH (dichotomy + singleton corollary): {results['summary']['all_match']}")
print(f"First split example: {examples['split']}")
print(f"First inert example: {examples['inert']}")

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
          "golden_quadratic_all_q_classification_results.json"), "w") as f:
    json.dump(results, f, indent=1)
print("Saved golden_quadratic_all_q_classification_results.json")
signal.alarm(0)
