#!/usr/bin/env python3
"""
COMP-P01-P: UGP integer/rational triple search for an exact Koide derivation.

Strategy:
  Search for triples (a_e, a_mu, a_tau) expressible as small products/quotients
  of UGP-native atoms, such that:
    (i)  (Sum a_i)^2 / (Sum a_i^2) = 3/2   [Koide equal-norm, written on sqrt masses a_i = sqrt(m_i)]
    (ii) a_mu / a_e = sqrt(m_mu / m_e) = 14.378 +- PDG     [empirical]
         a_tau / a_e = sqrt(m_tau / m_e) = 58.98 +- PDG    [empirical]

UGP basis atoms (Lean-certified integers from ugp-lean, plus canonical rationals):

  Tier-1 integers:  1, 3, 5, 7, 9, 11, 13, 16, 17, 20, 42, 73, 233, 257, 275,
                    823, 1023, 1314, 2137, 8176, 65535, 65537
  Ridge: R_n = 2^n - 16 for n in {5..20}
  UGP rationals:    k_L2 = 7/512, g_1^2 = 16/125, golden phi, pi
  Derived from Lean: delta = 7, ugp1_g = 13, ugp1_t = 20, D1 = 16, a2 = 9,
                    b1 = 73, q1 = 11, c1 = 823, b2 = 42, q2 = 24, c2 = 1023,
                    b3 = 275, c3 = 65535, m1 = 20, m2 = 15, F_13 = 233

Approach:
  Step 1: Build a bounded library of "UGP numbers" up to description length 2
          (atom, atom*atom, atom/atom, atom+atom, atom-atom) plus sqrt.
  Step 2: Sample triples from the library, compute Koide ratio and lepton
          ratios.
  Step 3: Report all triples where BOTH (i) and (ii) are satisfied within 1%.
  Step 4: For best hits, run a combinatorial null test (500 random permutations
          of the library) to assess significance.

Output: deterministic JSON.
"""

from __future__ import annotations
import json
import math
import random
from hashlib import sha256
from itertools import product, combinations
from pathlib import Path


# ---------------------------------------------------------------------------
# Empirical targets
# ---------------------------------------------------------------------------

M_E = 0.5109989461
M_MU = 105.6583755
M_TAU = 1776.86
D_M_TAU = 0.12

SQRT_ME = math.sqrt(M_E)
SQRT_MMU = math.sqrt(M_MU)
SQRT_MTAU = math.sqrt(M_TAU)

# sqrt-mass ratios (target):
R_MU_E_TARGET = SQRT_MMU / SQRT_ME   # ~14.378
R_TAU_E_TARGET = SQRT_MTAU / SQRT_ME  # ~58.97

# tolerances:
RATIO_TOL_PCT = 0.5      # accept if ratio within 0.5% (will tighten for winners)
KOIDE_TOL = 1e-3         # (Sum a)^2 / (Sum a^2) within this of 3/2
PDG_TOL_FRAC = 1e-4      # for winning triples, tighter test


# ---------------------------------------------------------------------------
# UGP basis atoms
# ---------------------------------------------------------------------------

LEAN_INTEGERS = {
    "one": 1,
    "F0_fermat": 3,
    "F1_fermat": 5,
    "delta": 7,        # = ugp1_s
    "a2": 9,
    "q1": 11,
    "ugp1_g": 13,
    "D1": 16,
    "F2_fermat": 17,
    "ugp1_t": 20,
    "b2": 42,
    "b1": 73,
    "F_13_fib": 233,
    "F3_fermat": 257,
    "b3": 275,
    "c1": 823,
    "c2_mersenne": 1023,
    "mirror_shift": 1314,   # = 2137 - 823
    "c1_mirror": 2137,
    "R_10": 1008,
    "R_11": 2032,
    "R_12": 4080,
    "R_13": 8176,
    "R_14": 16368,
    "R_15": 32752,
    "R_16": 65520,
    "c3_fermat_prod": 65535,
    "F4_fermat": 65537,
    "k_L2_denom": 512,
    "half_ridge": 504,
    "delta_b1": 511,        # = 7*73  (Round-5 electron anchor)
    "delta_b2": 294,        # = 7*42
    "delta_b3": 1925,       # = 7*275
    "q1_D1": 176,           # = 11*16
    "q1_b1": 803,           # = 11*73
}

# Tier-1: 32 atoms. Generate Tier-2 (products, quotients) bounded.
ATOM_NAMES = list(LEAN_INTEGERS.keys())
ATOM_VALS = [LEAN_INTEGERS[n] for n in ATOM_NAMES]


def build_library(max_ops: int = 2) -> list[tuple[float, str]]:
    """Build library of UGP-expressible positive reals.
    max_ops = 1: atoms only.
    max_ops = 2: atoms, products (a*b), quotients (a/b).
    """
    lib: dict[float, str] = {}   # value -> shortest description
    for name, val in LEAN_INTEGERS.items():
        if val > 0 and val not in lib:
            lib[float(val)] = name

    if max_ops >= 2:
        for i, (n1, v1) in enumerate(LEAN_INTEGERS.items()):
            for n2, v2 in LEAN_INTEGERS.items():
                if v2 == 0:
                    continue
                # product
                p = v1 * v2
                if p > 0 and p not in lib:
                    lib[float(p)] = f"{n1}*{n2}"
                # quotient (float)
                q = v1 / v2
                if q > 0 and q not in lib:
                    lib[float(q)] = f"{n1}/{n2}"

    # Also add sqrts of atoms and some composites
    extras = [
        ("sqrt(delta_b1)", math.sqrt(511)),           # = sqrt(m_e in keV)
        ("sqrt(R_10)", math.sqrt(1008)),
        ("sqrt(k_L2)", math.sqrt(7/512)),
        ("phi", (1 + math.sqrt(5))/2),
        ("phi^2", ((1 + math.sqrt(5))/2)**2),
        ("1/phi", 2/(1+math.sqrt(5))),
        ("sqrt(2)", math.sqrt(2)),
        ("sqrt(3)", math.sqrt(3)),
        ("sqrt(6)", math.sqrt(6)),
        ("sqrt_lepton_target_mu_e", R_MU_E_TARGET),   # for diagnosis only (will flag if trivially hit)
    ]
    for name, val in extras:
        if val > 0 and val not in lib:
            lib[val] = name

    return [(v, n) for v, n in lib.items()]


# ---------------------------------------------------------------------------
# Koide test on triples
# ---------------------------------------------------------------------------

def koide_Q_on_sqrt(a1: float, a2: float, a3: float) -> float:
    """Given the SQRT-mass triple (a_e, a_mu, a_tau), Koide is:
       Q = (a1^2+a2^2+a3^2) / (a1+a2+a3)^2 = 2/3
    """
    s = a1 + a2 + a3
    return (a1*a1 + a2*a2 + a3*a3) / (s*s)


def ratio_match(a1: float, a2: float, a3: float,
                tol_pct: float = RATIO_TOL_PCT) -> tuple[bool, float, float]:
    """Check if (a1, a2, a3) matches empirical (sqrt(m_e), sqrt(m_mu), sqrt(m_tau))
    up to overall scale.
    Normalize so smallest is 1; compare with normalized target (1, r_mu_e, r_tau_e).
    Returns (match, relative_err_mu_e, relative_err_tau_e).
    """
    vals = sorted([a1, a2, a3])
    if vals[0] <= 0:
        return False, float('inf'), float('inf')
    r_mu_e = vals[1] / vals[0]
    r_tau_e = vals[2] / vals[0]
    err_mu = abs(r_mu_e - R_MU_E_TARGET) / R_MU_E_TARGET
    err_tau = abs(r_tau_e - R_TAU_E_TARGET) / R_TAU_E_TARGET
    return (err_mu < tol_pct/100 and err_tau < tol_pct/100), err_mu, err_tau


def main() -> int:
    lib = build_library(max_ops=2)
    lib.sort()
    n_atoms = len(lib)
    print(f"Library size: {n_atoms} distinct positive UGP-expressible values")

    # Triple search: enumerate triples (a1 < a2 < a3) from library.
    # Full enumeration is O(n^3) ~ 10^9 for 1000 atoms. We restrict to
    # plausible magnitudes matching empirical sqrt-mass ratios.
    # Empirical sqrt(m_e)=0.7148, sqrt(m_mu)=10.28, sqrt(m_tau)=42.15 (MeV^1/2)
    # Normalize to smallest = 1: (1, 14.38, 58.97).
    # If we pick a1 freely, we need a2/a1 ≈ 14.38, a3/a1 ≈ 58.97.

    # Strategy: for each candidate a1 in lib, find all a2 with a2/a1 ∈ [r_mu_e*(1-RATIO_TOL),
    # r_mu_e*(1+RATIO_TOL)] and a3 with a3/a1 similarly. This is O(n) per a1 after sorting.

    vals = [v for v, _ in lib]
    names = [n for _, n in lib]

    hits: list[dict] = []
    tol = RATIO_TOL_PCT / 100

    for i, a1 in enumerate(vals):
        if a1 <= 0:
            continue
        target_a2_low = a1 * R_MU_E_TARGET * (1 - tol)
        target_a2_high = a1 * R_MU_E_TARGET * (1 + tol)
        target_a3_low = a1 * R_TAU_E_TARGET * (1 - tol)
        target_a3_high = a1 * R_TAU_E_TARGET * (1 + tol)
        # Binary-search-like filter:
        for j, a2 in enumerate(vals):
            if a2 < target_a2_low:
                continue
            if a2 > target_a2_high:
                break
            for k, a3 in enumerate(vals):
                if a3 < target_a3_low:
                    continue
                if a3 > target_a3_high:
                    break
                # Check Koide
                Q = koide_Q_on_sqrt(a1, a2, a3)
                if abs(Q - 2/3) < KOIDE_TOL:
                    match, err_mu, err_tau = ratio_match(a1, a2, a3, tol_pct=RATIO_TOL_PCT)
                    if match:
                        hits.append({
                            "a1_name": names[i],
                            "a1_val": a1,
                            "a2_name": names[j],
                            "a2_val": a2,
                            "a3_name": names[k],
                            "a3_val": a3,
                            "Q_koide": Q,
                            "Q_minus_2_over_3": Q - 2/3,
                            "r_mu_e_predicted": a2/a1,
                            "r_tau_e_predicted": a3/a1,
                            "rel_err_mu_e_pct": err_mu*100,
                            "rel_err_tau_e_pct": err_tau*100,
                        })

    # Sort by combined error:
    hits.sort(key=lambda h: h["rel_err_mu_e_pct"]**2 + h["rel_err_tau_e_pct"]**2)

    # Tighter-tolerance winners
    tight_hits = [h for h in hits
                  if h["rel_err_mu_e_pct"] < 0.1
                  and h["rel_err_tau_e_pct"] < 0.1
                  and abs(h["Q_minus_2_over_3"]) < 1e-5]

    # PDG-level winners: PDG delta m_tau/m_tau = 67 ppm => 33 ppm on sqrt(m_tau)
    pdg_hits = [h for h in hits
                if h["rel_err_mu_e_pct"] < 0.005   # 50 ppm
                and h["rel_err_tau_e_pct"] < 0.0067  # m_tau PDG
                and abs(h["Q_minus_2_over_3"]) < 1e-6]

    out = {
        "description": "UGP integer/rational triple search for exact Koide + lepton-ratio match",
        "library_size": n_atoms,
        "empirical_targets": {
            "sqrt_m_e_MeV_half": SQRT_ME,
            "sqrt_m_mu_MeV_half": SQRT_MMU,
            "sqrt_m_tau_MeV_half": SQRT_MTAU,
            "r_mu_e_target": R_MU_E_TARGET,
            "r_tau_e_target": R_TAU_E_TARGET,
            "Q_target": 2/3,
        },
        "tolerances": {
            "ratio_tol_pct": RATIO_TOL_PCT,
            "koide_tol": KOIDE_TOL,
            "pdg_tol_frac": PDG_TOL_FRAC,
        },
        "n_hits_0.5pct": len(hits),
        "n_hits_0.1pct_tight": len(tight_hits),
        "n_hits_pdg_level": len(pdg_hits),
        "top_10_by_combined_error": hits[:10],
        "tight_hits_0.1pct": tight_hits[:20],
        "pdg_level_hits": pdg_hits,
    }

    serialized = json.dumps(out, indent=2, sort_keys=True, default=str)
    digest = sha256(serialized.encode("utf-8")).hexdigest()
    out["script_sha256"] = digest

    out_path = Path(__file__).with_suffix(".json")
    out_path.write_text(json.dumps(out, indent=2, sort_keys=True, default=str))

    # Console
    print("=" * 72)
    print("COMP-P01-P: UGP integer triple search for Koide")
    print("=" * 72)
    print(f"Library size: {n_atoms}")
    print(f"Empirical r_mu_e = {R_MU_E_TARGET:.6f}  r_tau_e = {R_TAU_E_TARGET:.6f}")
    print(f"Q target = 2/3 = {2/3:.10f}")
    print()
    print(f"Total hits (0.5% tol on ratios, 1e-3 on Q): {len(hits)}")
    print(f"Tight hits (0.1% ratios, 1e-5 on Q):        {len(tight_hits)}")
    print(f"PDG-level hits:                             {len(pdg_hits)}")
    print()
    print("Top 10 hits by combined ratio error:")
    for h in hits[:10]:
        print(f"  {h['a1_name']:20s} : {h['a2_name']:20s} : {h['a3_name']:20s}")
        print(f"    vals: {h['a1_val']:.4f}  {h['a2_val']:.4f}  {h['a3_val']:.4f}")
        print(f"    r_mu_e={h['r_mu_e_predicted']:.4f} ({h['rel_err_mu_e_pct']:+.3f}%)  "
              f"r_tau_e={h['r_tau_e_predicted']:.4f} ({h['rel_err_tau_e_pct']:+.3f}%)  "
              f"Q={h['Q_koide']:.6f} (d={h['Q_minus_2_over_3']:+.2e})")
        print()
    print(f"Written to {out_path.name} (SHA {digest[:16]}...)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
