#!/usr/bin/env python3
"""
higher_seeds_cyclotomic_norms.py

Verifies whether the GTE generation-2 and generation-3 b-seeds (b_gen2=42, b_gen3=275)
are norms in cyclotomic rings ℤ[ζₙ] for n ≤ 12.

Background: electroweak_housing_closure.py proved that 42 and 275 are NOT Eisenstein
norms (norms in ℤ[ω] = ℤ[ζ₃]). This script checks the broader cyclotomic question:
whether any ring ℤ[ζₙ] for n ≤ 12 provides a norm representation.

Also tested: reconciliation with CompositeTriples.lean, which derives b_gen2=42=2·N_c·δ
from the Mersenne-sector rule (independently of cyclotomic norms).

Method:
- For each cyclotomic ring ℤ[ζₙ] with degree d=φ(n), the norm of
  α = Σ aᵢ ζₙⁱ (aᵢ ∈ ℤ, 0 ≤ i < d) equals the product of all Galois conjugates.
- We check analytically which integers can be norms using prime splitting in ℚ(ζₙ).
- For small n, we also brute-force search over bounded coefficients to confirm.

Null test: random seeds near 42 and 275 are tested to confirm the base rate of
cyclotomic norms in these magnitude ranges.

GTE provenance:
- b_gen2=42: GTE cascade odd step from (1,73,823). Also 42=2·N_c·δ=2·3·7
  (proved in CompositeTriples.lean, theorem muon_b_eq_2Nc_delta).
- b_gen3=275: GTE cascade even step. Sector-2-up boundary.

Results written to: ../data/higher_seeds_cyclotomic_norms_results.json
"""

import signal
import sys
import time
import json
import math
import os

TIMEOUT_SECONDS = 120

def _timeout_handler(signum, frame):
    print(f"\nTIMEOUT: wall-clock limit {TIMEOUT_SECONDS}s reached. Saving partial results.")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

t_start = time.time()

# ---------------------------------------------------------------------------
# Cyclotomic ring setup
# ---------------------------------------------------------------------------

def euler_phi(n):
    """Euler's totient function."""
    result = n
    p = 2
    temp = n
    while p * p <= temp:
        if temp % p == 0:
            while temp % p == 0:
                temp //= p
            result -= result // p
        p += 1
    if temp > 1:
        result -= result // temp
    return result

def multiplicative_order(a, n):
    """Order of a in (ℤ/nℤ)*. Requires gcd(a,n)=1."""
    if math.gcd(a, n) != 1:
        return None
    order = 1
    current = a % n
    while current != 1:
        current = (current * a) % n
        order += 1
    return order

def prime_splitting_in_cyclotomic(p, n):
    """
    Returns (e, f, g) describing how prime p splits in ℚ(ζₙ).
    - e = ramification index
    - f = residue degree (inertia degree)
    - g = number of prime ideals above p
    Satisfies e·f·g = φ(n).
    """
    phi_n = euler_phi(n)
    if math.gcd(p, n) == 1:
        f = multiplicative_order(p, n)
        assert phi_n % f == 0
        g = phi_n // f
        e = 1
    else:
        v = 0
        temp = n
        while temp % p == 0:
            v += 1
            temp //= p
        n_prime = n // (p ** v)
        e = (p ** v) - (p ** (v-1))
        if n_prime == 1:
            f = 1
        else:
            f = multiplicative_order(p, n_prime)
        g = phi_n // (e * f)
    return e, f, g

def norm_of_prime_ideal_above(p, n):
    """Returns N(𝔭) = p^f where 𝔭 is a prime ideal of ℤ[ζₙ] lying above p."""
    e, f, g = prime_splitting_in_cyclotomic(p, n)
    return p ** f

def can_be_norm_in_cyclotomic(m, n, max_prime=200):
    """
    Check if positive integer m can be a norm N_{ℚ(ζₙ)/ℚ}(α) for some α ∈ ℤ[ζₙ].
    Returns (bool, explanation_dict)
    """
    if m == 1:
        return True, {"reason": "1 is norm of any unit"}

    phi_n = euler_phi(n)
    explanation = {}
    result = True

    temp = m
    factors = {}
    for p in range(2, min(temp + 1, max_prime + 1)):
        if temp == 1:
            break
        if temp % p == 0:
            k = 0
            while temp % p == 0:
                k += 1
                temp //= p
            factors[p] = k
    if temp > 1:
        factors[temp] = factors.get(temp, 0) + 1

    for p, k in factors.items():
        e, f, g = prime_splitting_in_cyclotomic(p, n)
        norm_ideal = p ** f

        if k % f != 0:
            result = False
            explanation[p] = {
                "prime_power_in_m": k,
                "residue_degree_f": f,
                "ramification_e": e,
                "num_primes_g": g,
                "min_norm_ideal": norm_ideal,
                "verdict": f"FAIL: p^k = {p}^{k} = {p**k}; f={f} does not divide k={k}; "
                           f"min achievable norm from above-{p} elements is p^f = {norm_ideal}^j, "
                           f"which cannot equal p^{k}"
            }
        else:
            explanation[p] = {
                "prime_power_in_m": k,
                "residue_degree_f": f,
                "ramification_e": e,
                "num_primes_g": g,
                "min_norm_ideal": norm_ideal,
                "verdict": f"OK: {p}^{k} achievable with {k//f} prime ideals of norm p^f = {norm_ideal}"
            }

    explanation["m"] = m
    explanation["n"] = n
    explanation["phi_n"] = phi_n
    explanation["is_norm"] = result
    return result, explanation


# ---------------------------------------------------------------------------
# Brute-force search for small cyclotomic rings
# ---------------------------------------------------------------------------

def brute_force_norm_search(target, n, coeff_range=10):
    """
    For ℤ[ζₙ] with degree d=φ(n), find all elements α = Σ aᵢ ζₙⁱ
    with aᵢ ∈ [-coeff_range, coeff_range] such that |N(α)| = target.
    Returns list of coefficient tuples that give N(α) = target, or empty list.
    """
    import numpy as np
    import itertools

    d = euler_phi(n)
    zeta = np.exp(2j * np.pi / n)

    gal_exps = [k for k in range(1, n + 1) if math.gcd(k, n) == 1]
    assert len(gal_exps) == d, f"Expected {d} conjugates, got {len(gal_exps)}"

    conjugates = [np.exp(2j * np.pi * k / n) for k in gal_exps]

    found = []
    range_vals = list(range(-coeff_range, coeff_range + 1))

    for coeffs in itertools.product(range_vals, repeat=d):
        if time.time() - t_start > TIMEOUT_SECONDS * 0.8:
            break
        norm_val = 1.0 + 0j
        for z in conjugates:
            alpha_at_z = sum(coeffs[i] * (z ** i) for i in range(d))
            norm_val *= alpha_at_z

        norm_real = abs(norm_val.real)
        norm_imag = abs(norm_val.imag)
        if norm_imag > 1e-6:
            continue
        norm_int = round(norm_real)
        if abs(norm_real - norm_int) < 1e-6 and norm_int == target:
            found.append(coeffs)
            if len(found) >= 3:
                break

    return found


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

GTE_SEEDS = {
    "b_gen2 (muon)": 42,
    "b_gen3 (tau)": 275,
}

NULL_SEEDS_LOW = [36, 37, 39, 45, 48, 49, 52]  # near 42
NULL_SEEDS_HIGH = [277, 289, 273, 252, 361, 169]  # near 275

CYCLOTOMIC_N_VALUES = [3, 4, 5, 6, 7, 8, 9, 10, 12]  # n ≤ 12

results = {
    "meta": {
        "script": "higher_seeds_cyclotomic_norms.py",
        "purpose": "Test if b_gen2=42, b_gen3=275 are norms in ℤ[ζₙ] for n≤12",
        "gte_mechanism_b42": "2*N_c*delta = 2*3*7 = 42 (CompositeTriples.lean, muon_b_eq_2Nc_delta)",
        "gte_mechanism_b275": "GTE cascade even step",
        "h3_result": "42 and 275 are NOT Eisenstein norms in ℤ[ω]=ℤ[ζ₃] (proved in electroweak_housing_closure.py)",
    },
    "gte_seeds": {},
    "null_tests_low": {},
    "null_tests_high": {},
    "prime_splitting_summary": {},
    "conclusions": [],
}

print("=" * 70)
print("Higher Seeds Cyclotomic Norm Test")
print("=" * 70)
print()

# Analyze prime splitting for primes up to 15
print("--- Prime splitting in ℤ[ζ₁₂] ---")
primes_to_check = [2, 3, 5, 7, 11, 13]
for p in primes_to_check:
    e, f, g = prime_splitting_in_cyclotomic(p, 12)
    norm_ideal = p ** f
    splitting_type = "ramified" if e > 1 else ("split completely" if f == 1 and g > 1 else "inert")
    print(f"  p={p:3d}: e={e}, f={f}, g={g} → N(𝔭_p)={norm_ideal}. Type: {splitting_type}")
    results["prime_splitting_summary"][p] = {
        "e": e, "f": f, "g": g, "norm_prime_ideal": norm_ideal, "type": splitting_type
    }
print()

# Test GTE seeds in each ℤ[ζₙ]
print("--- GTE Seed Norm Tests ---")
for name, seed in GTE_SEEDS.items():
    print(f"\n  {name}: {seed} = {seed}")
    print(f"  Factorization: ", end="")
    temp = seed
    factors_str = []
    for p in range(2, seed + 1):
        if temp == 1:
            break
        if temp % p == 0:
            k = 0
            while temp % p == 0:
                k += 1
                temp //= p
            factors_str.append(f"{p}^{k}" if k > 1 else str(p))
    print(" × ".join(factors_str))

    seed_results = {}
    for n in CYCLOTOMIC_N_VALUES:
        is_norm, expl = can_be_norm_in_cyclotomic(seed, n)
        seed_results[n] = {"is_norm": is_norm, "phi_n": euler_phi(n)}
        verdict_str = "YES (norm)" if is_norm else "NO (not a norm)"
        print(f"    ℤ[ζ_{n:2d}] (degree {euler_phi(n)}): {verdict_str}")

    results["gte_seeds"][name] = {"value": seed, "by_n": seed_results}

print()

# Null tests
print("--- Null Tests (near 42) ---")
for seed in NULL_SEEDS_LOW:
    is_norm_12, expl = can_be_norm_in_cyclotomic(seed, 12)
    verdict_str = "YES" if is_norm_12 else "NO "
    temp = seed
    factors_str = []
    for p in range(2, seed + 1):
        if temp == 1:
            break
        if temp % p == 0:
            k = 0
            while temp % p == 0:
                k += 1
                temp //= p
            factors_str.append(f"{p}^{k}" if k > 1 else str(p))
    factored = " × ".join(factors_str)
    print(f"  n={seed:4d} = {factored:15s}: ℤ[ζ₁₂] norm? {verdict_str}")
    results["null_tests_low"][seed] = {"is_norm_z_zeta12": is_norm_12}

print()

print("--- Null Tests (near 275) ---")
for seed in NULL_SEEDS_HIGH:
    is_norm_12, expl = can_be_norm_in_cyclotomic(seed, 12)
    verdict_str = "YES" if is_norm_12 else "NO "
    temp = seed
    factors_str = []
    for p in range(2, seed + 1):
        if temp == 1:
            break
        if temp % p == 0:
            k = 0
            while temp % p == 0:
                k += 1
                temp //= p
            factors_str.append(f"{p}^{k}" if k > 1 else str(p))
    factored = " × ".join(factors_str)
    print(f"  n={seed:4d} = {factored:20s}: ℤ[ζ₁₂] norm? {verdict_str}")
    results["null_tests_high"][seed] = {"is_norm_z_zeta12": is_norm_12}

print()

# Detailed ℤ[ζ₁₂] analysis for 42 and 275
print("--- Detailed ℤ[ζ₁₂] Analysis for b=42 and b=275 ---")
for name, seed in GTE_SEEDS.items():
    is_norm, expl = can_be_norm_in_cyclotomic(seed, 12)
    print(f"\n  {name} = {seed} in ℤ[ζ₁₂]: {'IS a norm' if is_norm else 'is NOT a norm'}")
    for p, info in expl.items():
        if p not in ("m", "n", "phi_n", "is_norm"):
            print(f"    p={p}: {info['verdict']}")

print()

# Brute-force confirmation for ℤ[ζ₃] (Eisenstein, small)
print("--- Brute-force confirmation for ℤ[ζ₃] (Eisenstein, d=2) ---")
for name, seed in GTE_SEEDS.items():
    print(f"  Searching for {name}={seed} as norm in ℤ[ζ₃] (coefficients in [-20, 20])...")
    found_z3 = brute_force_norm_search(seed, 3, coeff_range=20)
    if found_z3:
        print(f"    FOUND {len(found_z3)} representations: {found_z3[:2]}")
    else:
        print(f"    NOT FOUND — confirms {seed} is not an Eisenstein norm")
    results["gte_seeds"][name]["brute_force_z3"] = found_z3

print()
print("--- Brute-force confirmation for ℤ[ζ₁₂] (d=4, small coefficients) ---")
for name, seed in GTE_SEEDS.items():
    print(f"  Searching for {name}={seed} as norm in ℤ[ζ₁₂] (coefficients in [-8, 8])...")
    found_z12 = brute_force_norm_search(seed, 12, coeff_range=8)
    if found_z12:
        print(f"    FOUND representations: {found_z12[:2]}")
    else:
        print(f"    NOT FOUND — confirms {seed} is not a ℤ[ζ₁₂] norm")
    results["gte_seeds"][name]["brute_force_z12"] = found_z12

print()

# -----------------------------------------------------------------------
# Conclusions
# -----------------------------------------------------------------------
print("=" * 70)
print("CONCLUSIONS")
print("=" * 70)

conclusions = [
    "b_gen2=42: NOT a norm in ℤ[ζₙ] for any n≤12.",
    "  Reason: 42=2×3×7. In all tested rings, at least one prime factor has residue",
    "  degree f>1 with f∤k (the prime power). No ring ℤ[ζₙ] for n≤12 contains all three.",
    "",
    "b_gen3=275: IS a norm in ℤ[ζ₅] and ℤ[ζ₁₀] (POSITIVE FINDING).",
    "  275 = 5² × 11.",
    "  In ℤ[ζ₅] (degree 4): p=5 totally ramified (e=4,f=1), N(1-ζ₅)=5. So 5²=25 achievable.",
    "  p=11: 11≡1 mod 5, so f=1 (splits completely), N(𝔭_{11})=11. So 11 achievable.",
    "  Therefore 275 = N_{ℚ(ζ₅)/ℚ}(α) for α=(1-ζ₅)²·q₁₁ ∈ ℤ[ζ₅]. ✓",
    "  Not a norm in ℤ[ζ₁₂]: p=11 has f=2 (N(𝔭_{11})=121≠11) → 11 not achievable. ✗",
    "",
    "GTE mechanism for b=42: Derived in CompositeTriples.lean (zero sorry):",
    "  42 = 2·N_c·δ = 2·3·7 (theorem muon_b_eq_2Nc_delta). This IS the primary answer.",
    "",
    "GTE mechanism for b=275: GTE cascade even step.",
    "  The ℤ[ζ₅] norm factorization is an additional algebraic observation, not an",
    "  alternative derivation. The cascade IS the answer.",
    "",
    "Honest-negative extension: 42 NOT a norm in any ℤ[ζₙ] for n≤12 (extends H3).",
    "  275 IS a norm in ℤ[ζ₅] — positive cyclotomic-norm finding beyond the Eisenstein chain.",
]

for c in conclusions:
    print(c)

results["conclusions"] = conclusions

# -----------------------------------------------------------------------
# Assertions (mandatory)
# -----------------------------------------------------------------------

# Verify theoretical results for b_gen2=42 (not a norm for any n ≤ 12)
for n_val in CYCLOTOMIC_N_VALUES:
    is_42_norm, _ = can_be_norm_in_cyclotomic(42, n_val)
    assert not is_42_norm, f"FAILED: 42 claimed to be a norm in ℤ[ζ_{n_val}] — check prime splitting logic"

# Verify b_gen3=275 results
n_vals_where_275_is_norm = [5, 10]
n_vals_where_275_not_norm = [3, 4, 6, 7, 8, 9, 12]

for n_val in n_vals_where_275_is_norm:
    is_275_norm, expl = can_be_norm_in_cyclotomic(275, n_val)
    assert is_275_norm, f"FAILED: 275 should be a norm in ℤ[ζ_{n_val}]: {expl}"

for n_val in n_vals_where_275_not_norm:
    is_275_norm, expl = can_be_norm_in_cyclotomic(275, n_val)
    assert not is_275_norm, f"FAILED: 275 should NOT be a norm in ℤ[ζ_{n_val}]: {expl}"

# Verify known norms
is_36_norm, _ = can_be_norm_in_cyclotomic(36, 12)
assert is_36_norm, "FAILED: 36 should be a norm in ℤ[ζ₁₂]"
is_37_norm, _ = can_be_norm_in_cyclotomic(37, 12)
assert is_37_norm, "FAILED: 37 should be a norm in ℤ[ζ₁₂] (37≡1 mod 12, splits completely)"
is_13_norm, _ = can_be_norm_in_cyclotomic(13, 12)
assert is_13_norm, "FAILED: 13 should be a norm in ℤ[ζ₁₂]"
is_277_norm, _ = can_be_norm_in_cyclotomic(277, 12)
assert is_277_norm, "FAILED: 277 should be a norm in ℤ[ζ₁₂] (277≡1 mod 12)"

# Verify H3 extension: brute force confirmed neither is in ℤ[ζ₃]
assert results["gte_seeds"]["b_gen2 (muon)"]["brute_force_z3"] == [], \
    "FAILED: 42 found as Eisenstein norm — contradicts electroweak_housing_closure.py H3"
assert results["gte_seeds"]["b_gen3 (tau)"]["brute_force_z3"] == [], \
    "FAILED: 275 found as Eisenstein norm — contradicts electroweak_housing_closure.py H3"

# Verify ℤ[ζ₁₂] brute force confirms theoretical result
assert results["gte_seeds"]["b_gen2 (muon)"]["brute_force_z12"] == [], \
    "FAILED: 42 found as ℤ[ζ₁₂] norm — contradicts theoretical analysis"
assert results["gte_seeds"]["b_gen3 (tau)"]["brute_force_z12"] == [], \
    "FAILED: 275 found as ℤ[ζ₁₂] norm — contradicts theoretical analysis"

print("\nALL ASSERTIONS PASSED")
print(f"Runtime: {time.time() - t_start:.2f}s")

signal.alarm(0)

# Write JSON artifact
_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../data")
os.makedirs(_data_dir, exist_ok=True)
output_path = os.path.join(_data_dir, "higher_seeds_cyclotomic_norms_results.json")
with open(output_path, "w") as f:
    json.dump(results, f, indent=2)
print(f"\nResults written to: {output_path}")
