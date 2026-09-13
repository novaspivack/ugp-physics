#!/usr/bin/env python3
"""p-adic root structure of the master quadratic m(x) = x^2 + x - 1.

Verifies the three p-adic behaviors predicted by the splitting of q in the
golden ring Z[phi] (disc 5):

  INERT (q = 7, and 3, 13 as controls): no root of m mod q^k for any k --
    the QNR binary-floor obstruction is 7-adic, not merely mod-7.
  SPLIT (q = 11, 19, 29): the two roots mod q lift uniquely mod q^k for all
    k (Hensel), i.e. golden elements exist in Z_q.
  RAMIFIED (q = 5): the double root k=2 mod 5 does NOT lift mod 25 (m(2)=5),
    and no root exists mod 5^k for k >= 2 -- sqrt(5) is not in Q_5.

Expected output: root counts mod q^k matching the three branches exactly,
k = 1..10 (capped so q^k stays below ~10^12; roots found by Hensel stepping,
not brute force, for large moduli).
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

def m(x, mod):
    return (x * x + x - 1) % mod

def roots_mod(modulus, prev_roots, prime, k):
    """Roots mod prime^k from roots mod prime^(k-1) by lifting (all candidates
    x0 + t*prime^(k-1)); exact, covers singular (non-Hensel) cases too."""
    if k == 1:
        return [x for x in range(prime) if m(x, prime) == 0]
    base = prime ** (k - 1)
    out = []
    for r in prev_roots:
        for t in range(prime):
            x = r + t * base
            if m(x, modulus) == 0:
                out.append(x)
    return sorted(set(out))

KMAX = 10
cases = {"inert": [3, 7, 13], "split": [11, 19, 29], "ramified": [5]}
results = {}

for branch, qs in cases.items():
    for q in qs:
        per_k = {}
        prev = []
        for k in range(1, KMAX + 1):
            modulus = q ** k
            prev = roots_mod(modulus, prev, q, k)
            per_k[k] = {"n_roots": len(prev), "roots": prev if len(prev) <= 4 else prev[:4]}
        results[q] = {"branch": branch, "roots_mod_q_pow_k": per_k}
        ns = [per_k[k]["n_roots"] for k in range(1, KMAX + 1)]
        print(f"q={q:2d} ({branch:8s}): #roots mod q^k, k=1..{KMAX}: {ns}")

# Branch verdicts
ok_inert = all(all(v["n_roots"] == 0 for v in results[q]["roots_mod_q_pow_k"].values())
               for q in cases["inert"])
ok_split = all(all(v["n_roots"] == 2 for v in results[q]["roots_mod_q_pow_k"].values())
               for q in cases["split"])
ram = results[5]["roots_mod_q_pow_k"]
ok_ram = ram[1]["n_roots"] == 1 and all(ram[k]["n_roots"] == 0 for k in range(2, KMAX + 1))

print(f"\nINERT: zero roots at every 7-adic (and 3-,13-adic) depth: {ok_inert}")
print(f"SPLIT: exactly 2 roots lift to every depth (Hensel): {ok_split}")
print(f"RAMIFIED q=5: double root mod 5 does not lift past k=1: {ok_ram}")

results["verdicts"] = {"inert_no_roots_all_depths": ok_inert,
                       "split_two_roots_all_depths": ok_split,
                       "ramified_no_lift_past_k1": ok_ram}

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
          "golden_quadratic_padic_hensel_results.json"), "w") as f:
    json.dump(results, f, indent=1)
print("Saved golden_quadratic_padic_hensel_results.json")
signal.alarm(0)
