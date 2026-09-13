#!/usr/bin/env python3
"""
COMP-P01-U  —  CKM theta_23 number-theoretic-function null for n = 1008

Question (advisor, round 7): the paper derives sin theta_23 = tau(1008)/D_1 *
(m_s/m_b) = (30/16)*(m_s/m_b) = 0.0419, matching PDG ~0.0414 to ~1.2 %.  The
claim "tau is uniquely the only ridge function in the right magnitude range"
is selection-after-fact: the zoo of number-theoretic functions of a given
integer is large, and the paper has not enumerated the zoo to justify the
selection.

Null test (falsifiable):
  1. Fix n = 1008, D_1 = 16.
  2. Enumerate a zoo of number-theoretic functions of n:
       - tau(n)     : divisor count
       - sigma(n)   : sum of divisors
       - sigma_2(n) : sum of squares of divisors
       - sigma_3(n) : sum of cubes of divisors
       - phi(n)     : Euler totient
       - J_2(n)     : Jordan totient of index 2
       - J_3(n)     : Jordan totient of index 3
       - omega(n)   : number of distinct prime factors
       - Omega(n)   : number of prime factors with multiplicity
       - psi(n)     : Dedekind psi
       - lambda(n)  : Carmichael lambda function
       - liouville(n) : Liouville's lambda
       - pi(n)       : prime-counting function up to n
       - rad(n)      : radical (squarefree kernel)
       - smooth(n, k): k-smooth numbers count
       - a few miscellaneous arithmetic functions
  3. For each f(n), compute predicted sin theta_23 = (f(n)/D_1)*(m_s/m_b).
  4. Compare to PDG sin theta_23 = 0.0414 +/- 0.0006.
  5. Report per-function ppm/sigma deviations and full distribution.
  6. Decision rule (pre-registered in NOTE):
     - tau uniquely PDG-compatible (within 3 sigma): selection has force
     - >=3 functions PDG-compatible : demote to "one-of-many coincidence"

Outputs:
  comp_p01_U_ckm_ntf_null.json
"""
from __future__ import annotations

import datetime as _dt
import hashlib as _hl
import json
import math
import sys
from pathlib import Path


N = 1008
D1 = 16

# PDG 2024 values
SIN_THETA_23_PDG = 0.0414
SIN_THETA_23_SIGMA = 0.0006

# Quark mass ratio at common scale (from paper, PDG M_S-bar at 2 GeV)
M_S_OVER_M_B = 0.093 / 4.183   # ~0.0222
# (The paper uses m_s/m_b ~ 0.0224; the exact number doesn't affect zoo comparison
# since we hold m_s/m_b fixed across all functions.)


# -----------------------------------------------------------------
# Number-theoretic function implementations
# -----------------------------------------------------------------
def prime_factorization(n):
    """Return [(p, e), ...] for n >=2."""
    factors = []
    m = n
    p = 2
    while p * p <= m:
        e = 0
        while m % p == 0:
            m //= p
            e += 1
        if e > 0:
            factors.append((p, e))
        p += 1
    if m > 1:
        factors.append((m, 1))
    return factors


def divisors(n):
    ds = []
    for i in range(1, int(math.isqrt(n)) + 1):
        if n % i == 0:
            ds.append(i)
            if i != n // i:
                ds.append(n // i)
    return sorted(ds)


def tau(n):
    """Divisor count."""
    return len(divisors(n))


def sigma_k(n, k=1):
    """Sum of k-th powers of divisors."""
    return sum(d**k for d in divisors(n))


def phi(n):
    """Euler totient."""
    result = n
    for p, _ in prime_factorization(n):
        result = result * (p - 1) // p
    return result


def jordan_J(n, k):
    """Jordan totient J_k(n) = n^k * prod(1 - p^-k)."""
    result = n**k
    for p, _ in prime_factorization(n):
        result = result * (p**k - 1) // (p**k)
    return result


def omega_small(n):
    """Number of distinct prime factors."""
    return len(prime_factorization(n))


def big_omega(n):
    """Number of prime factors counted with multiplicity."""
    return sum(e for _, e in prime_factorization(n))


def dedekind_psi(n):
    """Dedekind psi: n * prod(1 + 1/p)."""
    result = n
    for p, _ in prime_factorization(n):
        result = result * (p + 1) // p
    return result


def carmichael_lambda(n):
    """Carmichael lambda function."""
    def lcm(a, b):
        return a * b // math.gcd(a, b)
    if n == 1:
        return 1
    result = 1
    for p, e in prime_factorization(n):
        if p == 2 and e >= 3:
            contrib = 2**(e - 2)
        else:
            contrib = (p**e) * (p - 1) // p
        result = lcm(result, contrib)
    return result


def liouville(n):
    """Liouville lambda: (-1)^Omega(n)."""
    return (-1) ** big_omega(n)


def pi_count(n):
    """Prime-counting function."""
    sieve = [True] * (n + 1)
    sieve[0] = sieve[1] = False
    for i in range(2, int(math.isqrt(n)) + 1):
        if sieve[i]:
            for j in range(i*i, n + 1, i):
                sieve[j] = False
    return sum(1 for x in sieve if x)


def radical(n):
    """Squarefree kernel: product of distinct prime factors."""
    r = 1
    for p, _ in prime_factorization(n):
        r *= p
    return r


def mobius(n):
    """Mobius function."""
    factors = prime_factorization(n)
    for p, e in factors:
        if e >= 2:
            return 0
    return (-1) ** len(factors)


def mertens(n):
    """Mertens function M(n) = sum_{k<=n} mu(k)."""
    return sum(mobius(k) for k in range(1, n + 1))


def prime_sum(n):
    """Sum of primes up to n (pre-sieving)."""
    sieve = [True] * (n + 1)
    sieve[0] = sieve[1] = False
    for i in range(2, int(math.isqrt(n)) + 1):
        if sieve[i]:
            for j in range(i*i, n + 1, i):
                sieve[j] = False
    return sum(i for i, is_prime in enumerate(sieve) if is_prime)


# -----------------------------------------------------------------
# Evaluate the zoo at n = 1008
# -----------------------------------------------------------------
def evaluate_zoo():
    zoo = {
        "tau":        tau(N),
        "sigma_1":    sigma_k(N, 1),
        "sigma_2":    sigma_k(N, 2),
        "sigma_3":    sigma_k(N, 3),
        "phi":        phi(N),
        "jordan_J2":  jordan_J(N, 2),
        "jordan_J3":  jordan_J(N, 3),
        "omega":      omega_small(N),
        "big_Omega":  big_omega(N),
        "psi":        dedekind_psi(N),
        "lambda_car": carmichael_lambda(N),
        "liouville":  liouville(N),
        "pi_count":   pi_count(N),
        "radical":    radical(N),
        "mobius":     mobius(N),
        "mertens":    mertens(N),
        "prime_sum":  prime_sum(N),
        "log_n_floor_x100": int(round(math.log(N) * 100)),   # rough integer from log
        "sqrt_n_floor":     int(math.isqrt(N)),
    }
    return zoo


def main() -> int:
    zoo = evaluate_zoo()

    print(f"n = {N}, D_1 = {D1}")
    print(f"Using m_s/m_b = {M_S_OVER_M_B:.6f}")
    print(f"PDG sin theta_23 = {SIN_THETA_23_PDG} +/- {SIN_THETA_23_SIGMA}")
    print()

    results = {}
    for name, f_n in zoo.items():
        if f_n is None:
            continue
        # sin theta_23 = (f(n) / D_1) * (m_s / m_b)
        ratio = f_n / D1
        predicted = ratio * M_S_OVER_M_B
        deviation = predicted - SIN_THETA_23_PDG
        rel = deviation / SIN_THETA_23_PDG
        sigma = deviation / SIN_THETA_23_SIGMA
        compatible_3sigma = abs(sigma) <= 3.0
        compatible_1sigma = abs(sigma) <= 1.0
        results[name] = {
            "function_value":              f_n,
            "function_over_D1":            ratio,
            "predicted_sin_theta_23":      predicted,
            "pdg_deviation_abs":           deviation,
            "pdg_deviation_rel":           rel,
            "pdg_deviation_sigma":         sigma,
            "compatible_within_1sigma":    compatible_1sigma,
            "compatible_within_3sigma":    compatible_3sigma,
        }
        print(f"  {name:15s}  f(n) = {f_n:>12}   ratio/D1 = {ratio:>12.4f}   "
              f"sin_th_23 pred = {predicted:>9.4f}   dev = {sigma:+7.2f} sigma   "
              f"{'1sigma' if compatible_1sigma else ('3sigma' if compatible_3sigma else '')}")

    # Count PDG-compatible functions
    n_3sigma = sum(1 for r in results.values() if r["compatible_within_3sigma"])
    n_1sigma = sum(1 for r in results.values() if r["compatible_within_1sigma"])
    tau_3sigma = results["tau"]["compatible_within_3sigma"]
    tau_1sigma = results["tau"]["compatible_within_1sigma"]

    if tau_3sigma and n_3sigma == 1:
        verdict = (
            f"PASS (weak): tau is the unique PDG-3sigma-compatible function "
            f"in the zoo of {len(results)} number-theoretic functions.  "
            f"Selection argument has some force, though still post-hoc "
            f"(the zoo itself is a choice)."
        )
        decision = "RETAIN_WITH_ZOO_DISCLOSURE"
    elif n_3sigma >= 3:
        verdict = (
            f"FAIL: {n_3sigma} functions in the zoo are PDG-3sigma-compatible; "
            f"tau is one of many.  Demote CKM theta_23 = tau(1008)/D_1 to "
            f"'numerical coincidence, one of several'."
        )
        decision = "DEMOTE_ONE_OF_MANY"
    elif n_3sigma == 2:
        verdict = (
            f"AMBIGUOUS: 2 functions in the zoo are PDG-3sigma-compatible.  "
            f"Disclose the companion function explicitly; the selection is "
            f"less strong than 'unique' but not open."
        )
        decision = "DISCLOSE_COMPANION"
    else:
        verdict = (
            f"NOTE: {n_3sigma} functions PDG-3sigma-compatible; tau status "
            f"is '{'COMPATIBLE' if tau_3sigma else 'NOT COMPATIBLE'}'.  "
            f"Interpret per raw distribution."
        )
        decision = "INTERPRET_MANUALLY"

    report = {
        "experiment_id": "COMP-P01-U",
        "question": (
            "Combinatorial null for the CKM theta_23 selection "
            "sin theta_23 = tau(1008)/D_1 * (m_s/m_b).  How many functions "
            "in a zoo of number-theoretic functions of 1008 produce a "
            "PDG-compatible sin theta_23 prediction?"
        ),
        "inputs": {
            "n":                N,
            "D1":               D1,
            "m_s_over_m_b":     M_S_OVER_M_B,
            "pdg_sin_theta_23": SIN_THETA_23_PDG,
            "pdg_sigma":        SIN_THETA_23_SIGMA,
        },
        "zoo_size":                     len(results),
        "per_function_results":         results,
        "count_1sigma_compatible":      n_1sigma,
        "count_3sigma_compatible":      n_3sigma,
        "tau_is_1sigma_compatible":     tau_1sigma,
        "tau_is_3sigma_compatible":     tau_3sigma,
        "tau_uniquely_3sigma":          tau_3sigma and n_3sigma == 1,
        "verdict":                      verdict,
        "decision":                     decision,
        "timestamp_utc":                _dt.datetime.utcnow().isoformat(timespec="seconds"),
    }

    out_path = Path(__file__).with_suffix(".json")
    with open(out_path, "w") as fh:
        json.dump(report, fh, indent=2, sort_keys=False)
    sha = _hl.sha256(out_path.read_bytes()).hexdigest()
    print(f"\n[write] {out_path.name}")
    print(f"[sha]   {sha}")

    print("\n====  CKM zoo summary  ====")
    print(f"  Zoo size:                                      {len(results)}")
    print(f"  Functions PDG-compatible within 1 sigma:       {n_1sigma}")
    print(f"  Functions PDG-compatible within 3 sigma:       {n_3sigma}")
    print(f"  tau(1008) 1-sigma compatible?                  {tau_1sigma}")
    print(f"  tau(1008) 3-sigma compatible?                  {tau_3sigma}")
    print(f"  tau uniquely 3-sigma compatible?               {tau_3sigma and n_3sigma == 1}")
    print(f"\n{verdict}")
    print(f"Decision: {decision}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
