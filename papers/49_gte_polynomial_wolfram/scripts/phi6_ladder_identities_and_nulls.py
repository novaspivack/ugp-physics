#!/usr/bin/env python3
"""Phi_6 ladder of the GTE constants: identity skeleton + anti-numerology nulls.

PART A - exact identities (verified over wide integer ranges + exact algebra):
  I1 shift:          Phi_3(n) = Phi_6(n+1)
  I2 multiplication: Phi_6(n) * Phi_6(n+1) = Phi_6(n^2+1)
     instances: n=2: 3*7   = 21 = Phi_6(5)   (|F21| = N_gen * q = Phi_6(N_fam))
                n=3: 7*13  = 91 = Phi_6(10)  (q * c_H = Phi_6(n_ridge), NEW)
  I3 composition:    Phi_6(n^2) = Phi_12(n);  Phi_6(n^3) = Phi_18(n)
     instance: 73 = Phi_6(9) = Phi_12(3) = FGCI F(3); Frobenius tower
               {7, 73, 703} = Phi_6(3^k), k=1,2,3
  I4 canonical Z3:   n^3 + 1 = (n+1) * Phi_6(n), so -n is a cube root of
     unity mod Phi_6(n), order exactly 3 for n >= 3; orbit {1, -n, n^2}
     reduces to {1,4,2} at n=3 (the F21 color action)
  I5 Sylvester:      iterating n -> Phi_6(n) from 2 gives 2,3,7,43,1807,...
     (Sylvester's sequence, greedy Egyptian expansion of 1); the GTE chain
     {2, 3, 7, 43} = the maximal PRIME prefix (1807 = 13*139 composite)
  I6 Z[omega] factorizations: (2+omega)(3+omega) = 5+4omega ~ conj(5+omega);
     5+omega ~ lambda*pibar -- |F21| = N(lambda)*N(pi) = 3*7 exactly as norms

PART B - PRE-REGISTERED null battery (fixed before running; see scout script
eisenstein_norm_gte_constants.py for the original 20-atom registration):

  B1 rival-form null: 14 integer forms with value sets DIFFERENT from
     {n^2-n+1} (Phi_3 is excluded: identical value set by I1), scanned with
     the identical hit protocol (exists n >= 2 with f(n) = v) on the same
     20 atoms.  Forms:
       n^2+1, n^2-n-1, n^2+n-1, n^2+2, n^2-2, 2n^2-1, 2n^2+1, n^2+3,
       n^2+n (oblong), n(n+1)/2 (triangular), 2^n-1 (Mersenne), 2^n+1,
       n^3-n+1, n^3+n+1
  B2 wrong-target null: Phi_6 scan on 20 PRE-REGISTERED measured-physics
     integers (PDG rounding integers, no GTE-structural status):
       1836 (m_p/m_e), 207 (m_mu/m_e), 1777 (m_tau MeV), 80 (m_W GeV),
       91 (m_Z GeV), 125 (m_H GeV), 173 (m_t GeV), 4180 (m_b MeV),
       1270 (m_c MeV), 94 (m_s MeV), 938 (m_p MeV), 140 (m_pi MeV),
       494 (m_K MeV), 67 (H0), 32 (Omega_m*100), 965 (n_s*1000),
       2312 (sin^2thW*10^4), 137 (1/alpha), 128 (1/alpha(M_Z)), 210
       (Lambda_QCD MeV)
  B3 general-norm slice table: which atoms are Eisenstein norms a^2-ab+b^2
     at all (density caveat: norms ~ N/sqrt(log N), Phi_6 b=1 slice ~
     sqrt(N) -- only the slice claim is sharp)

Expected output: all identities PASS; rival forms score < 7 hits; wrong-target
scan scores ~ chance.
"""
import os
import json
import math
import signal
import sys

TIMEOUT_SECONDS = 300

def _timeout(signum, frame):
    print(f"TIMEOUT {TIMEOUT_SECONDS}s reached")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

def phi6(n):
    return n * n - n + 1

def phi3(n):
    return n * n + n + 1

def phi12(n):
    return n ** 4 - n ** 2 + 1

def phi18(n):
    return n ** 6 - n ** 3 + 1

results = {"identities": {}, "nulls": {}}

# ---------------- PART A: identities ---------------------------------------
RNG = range(-200, 201)
I1 = all(phi3(n) == phi6(n + 1) for n in RNG)
I2 = all(phi6(n) * phi6(n + 1) == phi6(n * n + 1) for n in RNG)
I3a = all(phi6(n * n) == phi12(n) for n in RNG)
I3b = all(phi6(n ** 3) == phi18(n) for n in RNG)
I4 = all((n ** 3 + 1) == (n + 1) * phi6(n) for n in RNG)
# order exactly 3 for n >= 3
I4_order = all(pow(-n % phi6(n), 3, phi6(n)) == 1 and
               (-n) % phi6(n) != 1 for n in range(3, 200))
print("I1 shift  Phi3(n) = Phi6(n+1):", I1)
print("I2 mult   Phi6(n)Phi6(n+1) = Phi6(n^2+1):", I2)
print("I3 comp   Phi6(n^2) = Phi12(n), Phi6(n^3) = Phi18(n):", I3a and I3b)
print("I4 Z3     n^3+1 = (n+1)Phi6(n); -n has order 3 mod Phi6(n):",
      I4 and I4_order)

# instances
inst = {
    "cH_eq_phi6_D_eq_phi3_Ngen": phi6(4) == phi3(3) == 13,
    "F21_eq_phi6_Nfam_eq_Ngen_times_q": phi6(5) == 21 == 3 * 7
                                        and phi6(2) * phi6(3) == phi6(5),
    "q_cH_eq_phi6_nridge_91": phi6(3) * phi6(4) == 91 == phi6(10),
    "b1_eq_phi6_9_eq_phi12_3_FGCI": phi6(9) == 73 == phi12(3),
    "frobenius_tower_phi6_powers_of_3":
        [phi6(3), phi6(9), phi6(27)] == [7, 73, 703],
    "tower_terminates_703_composite": 703 == 19 * 37,
}
for k, v in inst.items():
    print(f"  instance {k}: {v}")

# I5 Sylvester chain
chain = [2]
for _ in range(5):
    chain.append(phi6(chain[-1]))
def is_prime(n):
    if n < 2:
        return False
    i = 2
    while i * i <= n:
        if n % i == 0:
            return False
        i += 1
    return True
sylv_primality = [(s, is_prime(s)) for s in chain]
egyptian = sum(1.0 / s for s in chain[:4])
print(f"I5 Sylvester chain from 2: {chain}")
print(f"   primality: {sylv_primality}")
print(f"   1/2+1/3+1/7+1/43 = {egyptian:.10f} = 1 - 1/1806 "
      f"({abs(egyptian - (1 - 1/1806)) < 1e-12})")
print(f"   1807 = 13*139: {1807 == 13 * 139} (prime prefix ends at 43)")

# I6 Z[omega] factorization identities
def emul(z, w):
    a, b = z
    c, d = w
    return (a * c - b * d, a * d + b * c - b * d)

def enorm(z):
    return z[0] ** 2 - z[0] * z[1] + z[1] ** 2

units = [(1, 0), (-1, 0), (0, 1), (0, -1), (-1, -1), (1, 1)]
prod23 = emul((2, 1), (3, 1))            # (2+w)(3+w)
conj5w = (5 - 1, -1)                     # conj(5+w) = 5+w^2 = 4-w
assoc = any(emul(conj5w, u) == prod23 for u in units)
lam, pib = (1, -1), (2, -1)
lam_pib = emul(lam, pib)                 # lambda*pibar
five_w_assoc = any(emul(lam_pib, u) == (5, 1) for u in units)
I6 = (prod23 == (5, 4) and enorm(prod23) == 21 and assoc
      and enorm((5, 1)) == 21 and five_w_assoc)
print(f"I6 Z[omega]: (2+w)(3+w) = 5+4w ~ conj(5+w); 5+w ~ lambda*pibar: {I6}")

results["identities"] = {
    "I1_shift": I1, "I2_multiplication": I2,
    "I3_composition": I3a and I3b, "I4_canonical_Z3": I4 and I4_order,
    "instances": {k: bool(v) for k, v in inst.items()},
    "I5_sylvester_chain": chain, "sylvester_primality": sylv_primality,
    "I6_eisenstein_factorizations": I6,
    "canonical_Z3_orbits": {
        str(phi6(n)): sorted({1, (-n) % phi6(n), (n * n) % phi6(n)})
        for n in (3, 4, 5, 7, 9)},
}
print("canonical Z3 orbits {1,-n,n^2} mod Phi6(n):",
      results["identities"]["canonical_Z3_orbits"])

# ---------------- PART B: nulls --------------------------------------------
ATOMS = [
    ("N_gen", 3), ("N_fam", 5), ("q", 7), ("b0", 7), ("n_ridge", 10),
    ("c_Z", 12), ("c_H", 13), ("K_CA_bits", 19), ("F21_order", 21),
    ("b2_muon", 42), ("GS_degeneracy", 43), ("b1_electron", 73),
    ("alpha_inv_MZ", 128), ("alpha_inv_0", 137), ("b3_tau", 275),
    ("orbit_period", 475), ("seed_c", 823), ("ridge_R10", 1008),
    ("D_spacetime", 4), ("D_squared", 16),
]
VALUES = [v for _, v in ATOMS]

def hits_for(f, values, n_min=2, n_max=4000):
    out = []
    image = set()
    for n in range(n_min, n_max):
        y = f(n)
        if y > max(values) * 2:
            break
        image.add(y)
    for name, v in ATOMS:
        if v in image:
            out.append((name, v))
    return out

FORMS = {
    "phi6_n2-n+1 (REFERENCE)": lambda n: n * n - n + 1,
    "gauss_n2+1": lambda n: n * n + 1,
    "golden_n2-n-1": lambda n: n * n - n - 1,
    "golden_n2+n-1": lambda n: n * n + n - 1,
    "n2+2": lambda n: n * n + 2,
    "n2-2": lambda n: n * n - 2,
    "2n2-1": lambda n: 2 * n * n - 1,
    "2n2+1": lambda n: 2 * n * n + 1,
    "n2+3": lambda n: n * n + 3,
    "oblong_n2+n": lambda n: n * n + n,
    "triangular": lambda n: n * (n + 1) // 2,
    "mersenne_2^n-1": lambda n: 2 ** n - 1,
    "fermat_2^n+1": lambda n: 2 ** n + 1,
    "cubic_n3-n+1": lambda n: n ** 3 - n + 1,
    "cubic_n3+n+1": lambda n: n ** 3 + n + 1,
}
print("\nB1 rival-form null (same 20 atoms, same protocol, n >= 2):")
form_scores = {}
for fname, f in FORMS.items():
    h = hits_for(f, VALUES)
    form_scores[fname] = {"n_hits": len(h), "hits": h}
    print(f"  {fname:>24}: {len(h):>2} hits  {[x[1] for x in h]}")

ref = form_scores["phi6_n2-n+1 (REFERENCE)"]["n_hits"]
rivals = [v["n_hits"] for k, v in form_scores.items() if "REFERENCE" not in k]
print(f"  Phi_6 reference: {ref} hits; rival max: {max(rivals)}; "
      f"rival mean: {sum(rivals)/len(rivals):.2f}")

# B2 wrong-target null
WRONG_TARGETS = [1836, 207, 1777, 80, 91, 125, 173, 4180, 1270, 94,
                 938, 140, 494, 67, 32, 965, 2312, 137, 128, 210]
def is_phi6_value(v):
    d = 4 * v - 3
    r = math.isqrt(d)
    return r * r == d and (1 + r) % 2 == 0 and (1 + r) // 2 >= 2

wt_hits = [v for v in WRONG_TARGETS if is_phi6_value(v)]
print(f"\nB2 wrong-target null (20 measured-physics integers): "
      f"{len(wt_hits)} hits {wt_hits}")
# chance expectation: per-value density of Phi_6 numbers near v is ~1/(2 sqrt v)
exp_hits = sum(1.0 / (2 * math.sqrt(v)) for v in WRONG_TARGETS)
print(f"   chance expectation ~ {exp_hits:.2f} hits")

# B3 general-norm membership (density caveat)
def is_eisenstein_norm(v):
    # v is a norm iff every prime = 2 mod 3 divides v to an even power
    n = v
    d = 2
    while d * d <= n:
        if n % d == 0:
            e = 0
            while n % d == 0:
                n //= d
                e += 1
            if d % 3 == 2 and e % 2 == 1:
                return False
        d += 1
    if n > 1 and n % 3 == 2:
        return False
    return True

norm_table = {}
for name, v in ATOMS:
    norm_table[name] = {"value": v, "general_norm": is_eisenstein_norm(v),
                        "phi6_slice": is_phi6_value(v)}
n_norms = sum(1 for r in norm_table.values() if r["general_norm"])
n_slice = sum(1 for r in norm_table.values() if r["phi6_slice"])
print(f"\nB3 norm-slice table: {n_norms}/20 atoms are general Eisenstein "
      f"norms (weak: norms are dense ~N/sqrt(log N)); {n_slice}/20 are on "
      f"the b=1 slice Phi_6 (sharp claim, density ~sqrt(N))")
for name, r in norm_table.items():
    print(f"  {name:>16} = {r['value']:>4}  norm={'Y' if r['general_norm'] else 'n'}"
          f"  phi6={'Y' if r['phi6_slice'] else 'n'}")

results["nulls"] = {
    "B1_rival_forms": {k: {"n_hits": v["n_hits"],
                           "hit_values": [x[1] for x in v["hits"]]}
                       for k, v in form_scores.items()},
    "B1_reference_hits": ref,
    "B1_rival_max": max(rivals),
    "B2_wrong_target": {"targets": WRONG_TARGETS, "hits": wt_hits,
                        "n_hits": len(wt_hits),
                        "chance_expectation": exp_hits},
    "B3_norm_slice_table": norm_table,
}
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
          "phi6_ladder_identities_and_nulls_results.json"), "w") as f:
    json.dump(results, f, indent=1)
print("\nSaved phi6_ladder_identities_and_nulls_results.json")
signal.alarm(0)
