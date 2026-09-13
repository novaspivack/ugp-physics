#!/usr/bin/env python3
"""
COMP-P01-OO: Number-theoretic triple-property threshold corrections (10_SPEC-3rd-ext)

Motivation (R7-013 + user-proposed): generation-weighting breaks the Y² ≥ 0
sign barrier but is density-dominated under gen-permutation null because the
SM generation assignment is weakly discriminating.  The UGP triples
(a, b, c) are PER-PARTICLE structural data — strictly richer than generation
labels.  If a number-theoretic property of (a, b, c) enters as the per-
particle 4th weight, closures that survive TRIPLE-permutation null are
genuine structural derivations; closures that vanish are not.

Model:
    δ_G = α · (1 / 16π²) · Σ_p F(triple(p)) · b_G^(p) · ln(μ_UV / m_p)
        + α_n · (1 / 16π²) · (b_G^(H) ln(μ/m_H) + b_G^(W) ln(μ/m_W))

where F is one of a catalog of number-theoretic per-particle functions of
the particle's triple, α is a UGP atom, and α_n is a UGP atom for the
flavor-neutral Higgs / SU(2)-gauge contribution (treated separately since
Higgs and W don't have a generation triple).

Decisive null: PERMUTE the 9 charged-fermion triples across the 9
particle slots (9! = 362880 permutations; sample 2000).  If closure rate
under permutation < 1%, the specific SM triple-to-particle assignment is
structurally discriminating.  If not, it's density-dominated.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
import random
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np

# ── Closure windows ───────────────────────────────────────────────────────
DELTA1_WIN = (-0.00289, -0.00244)
DELTA2_WIN = (-0.01768, -0.01406)
DELTA1_C = 0.5 * sum(DELTA1_WIN)
DELTA2_C = 0.5 * sum(DELTA2_WIN)
DELTA1_HW = 0.5 * (DELTA1_WIN[1] - DELTA1_WIN[0])
DELTA2_HW = 0.5 * (DELTA2_WIN[1] - DELTA2_WIN[0])

PHI = (1.0 + math.sqrt(5.0)) / 2.0
M_Z = 91.1876
M_W = 80.379
M_H = 125.25

# ── Charged-fermion triples (canonical, Braid-Atlas chirality for c) ──────
# (a, b, c) — matches FF3/GG/HH/II/JJ/KK/MM/NN
FERMION_TRIPLES: Dict[str, Tuple[int, int, int]] = {
    "electron": (1, 73, 823),
    "muon":     (9, 42, 1023),
    "tau":      (5, 275, -65535),
    "up":       (5, 9, 275),
    "charm":    (5, 275, 65535),
    "top":      (76, 337920, -1),
    "down":     (9, 5, 42),
    "strange":  (9, 186, 1023),
    "bottom":   (5, 8191, 65535),
}

# PDG masses (GeV)
FERMION_MASSES_GeV: Dict[str, float] = {
    "electron": 0.5109989088e-3, "muon": 0.1056583777, "tau": 1.77686,
    "up": 2.16e-3, "charm": 1.275, "top": 172.76,
    "down": 4.7e-3, "strange": 0.093, "bottom": 4.18,
}


# ── Number-theoretic helpers ─────────────────────────────────────────────
def is_prime(n: int) -> bool:
    n = abs(int(n))
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0:
        return False
    r = int(n ** 0.5) + 1
    for i in range(3, r + 1, 2):
        if n % i == 0:
            return False
    return True


def is_mersenne_form(n: int, k_min: int = 2) -> bool:
    n = abs(int(n))
    if n < (2 ** k_min - 1):
        return False
    return ((n + 1) & n) == 0 and (n + 1) > 2


def mobius(n: int) -> int:
    n = abs(int(n))
    if n == 0:
        return 0
    if n == 1:
        return 1
    p = 2
    factors: Dict[int, int] = {}
    while p * p <= n:
        while n % p == 0:
            factors[p] = factors.get(p, 0) + 1
            n //= p
        p += 1
    if n > 1:
        factors[n] = factors.get(n, 0) + 1
    if any(e > 1 for e in factors.values()):
        return 0
    return (-1) ** len(factors)


def omega(n: int) -> int:
    n = abs(int(n))
    if n == 0:
        return 0
    p = 2
    s = 0
    while p * p <= n:
        if n % p == 0:
            s += 1
            while n % p == 0:
                n //= p
        p += 1
    if n > 1:
        s += 1
    return s


# ── Weight-function catalog ──────────────────────────────────────────────
def _f(name, fn):
    return (name, fn)


WeightFn = Callable[[Tuple[int, int, int]], float]


def weight_catalog() -> Dict[str, WeightFn]:
    return {
        # Single-property signed weights
        "mu_a":         lambda t: float(mobius(t[0])),
        "mu_b":         lambda t: float(mobius(t[1])),
        "mu_c":         lambda t: float(mobius(t[2])),
        "mu_prod":      lambda t: float(mobius(t[0]) * mobius(t[1]) * mobius(t[2])),
        "sgn_c":        lambda t: float(1 if t[2] > 0 else -1),
        "chi":          lambda t: float(1 if t[2] < 0 else 0),      # H(writhe)
        # Mersenne-form binary, ±1
        "mers_c_pm":    lambda t: float(1 if is_mersenne_form(t[2]) else -1),
        "mers_b_pm":    lambda t: float(1 if is_mersenne_form(t[1]) else -1),
        "mers_a_pm":    lambda t: float(1 if is_mersenne_form(t[0]) else -1),
        # Primality binary, ±1
        "prime_c_pm":   lambda t: float(1 if is_prime(t[2]) else -1),
        "prime_b_pm":   lambda t: float(1 if is_prime(t[1]) else -1),
        "prime_a_pm":   lambda t: float(1 if is_prime(t[0]) else -1),
        # Omega (number of distinct primes), centered
        "omega_c_c3":   lambda t: float(omega(t[2]) - 3),
        "omega_b_c2":   lambda t: float(omega(t[1]) - 2),
        # Products and mixed
        "mu_c_x_sgn_c": lambda t: float(mobius(t[2]) * (1 if t[2] > 0 else -1)),
        "mers_c_x_sgn_c": lambda t: float((1 if is_mersenne_form(t[2]) else -1) * (1 if t[2] > 0 else -1)),
        "prime_b_x_mu_c": lambda t: float((1 if is_prime(t[1]) else -1) * mobius(t[2])),
        "mers_c_x_mu_b":  lambda t: float((1 if is_mersenne_form(t[2]) else -1) * mobius(t[1])),
        # Continuous: normalized log of |c|
        "log_abs_c":    lambda t: math.log(abs(t[2])) if t[2] != 0 else 0.0,
        "log_abs_b":    lambda t: math.log(abs(t[1])) if t[1] != 0 else 0.0,
    }


# ── SM particle table with per-particle triple assignment ────────────────
@dataclass
class Particle:
    name: str
    mass_GeV: float
    b_Y: float
    b_2: float
    triple: Optional[Tuple[int, int, int]]   # None for flavor-neutral


def build_sm_particles(triple_assignment: Dict[str, Tuple[int, int, int]]) -> List[Particle]:
    """triple_assignment maps charged-fermion name ('electron', 'up', 'down', …)
    to the triple to use for that fermion in the scan (default = SM assignment).
    Q_L and L_L use the heavier-flavor member's triple (top for Q3_L, etc.)."""
    gen_map = {1: ["electron", "up", "down"],
               2: ["muon", "charm", "strange"],
               3: ["tau", "top", "bottom"]}
    tr = triple_assignment

    parts: List[Particle] = []
    # u-type right-handed (color triplet)
    for g, u_name in enumerate(["up", "charm", "top"], start=1):
        parts.append(Particle(f"uR_{g}", FERMION_MASSES_GeV[u_name],
                               b_Y=(2.0 / 3.0) * 3 * (2.0 / 3.0) ** 2,
                               b_2=0.0, triple=tr[u_name]))
    # d-type right-handed
    for g, d_name in enumerate(["down", "strange", "bottom"], start=1):
        parts.append(Particle(f"dR_{g}", FERMION_MASSES_GeV[d_name],
                               b_Y=(2.0 / 3.0) * 3 * (1.0 / 3.0) ** 2,
                               b_2=0.0, triple=tr[d_name]))
    # e-type right-handed
    for g, e_name in enumerate(["electron", "muon", "tau"], start=1):
        parts.append(Particle(f"eR_{g}", FERMION_MASSES_GeV[e_name],
                               b_Y=(2.0 / 3.0) * 1 * (1.0) ** 2,
                               b_2=0.0, triple=tr[e_name]))
    # Q_L (SU(2) doublet): decouples at top for gen 3, at charm for gen 2, at up for gen 1
    for g, u_name in enumerate(["up", "charm", "top"], start=1):
        parts.append(Particle(f"QL_{g}", FERMION_MASSES_GeV[u_name],
                               b_Y=(2.0 / 3.0) * 3 * 2 * (1.0 / 6.0) ** 2,
                               b_2=(2.0 / 3.0) * 3 * (1.0 / 2.0),
                               triple=tr[u_name]))
    # L_L (lepton SU(2) doublet): decouples at charged lepton mass
    for g, e_name in enumerate(["electron", "muon", "tau"], start=1):
        parts.append(Particle(f"LL_{g}", FERMION_MASSES_GeV[e_name],
                               b_Y=(2.0 / 3.0) * 1 * 2 * (1.0 / 2.0) ** 2,
                               b_2=(2.0 / 3.0) * 1 * (1.0 / 2.0),
                               triple=tr[e_name]))
    # Flavor-neutral: Higgs + SU(2) gauge
    parts.append(Particle("Higgs", M_H, b_Y=(1.0 / 3.0) * 2 * (1.0 / 2.0) ** 2,
                           b_2=(1.0 / 3.0) * (1.0 / 2.0), triple=None))
    parts.append(Particle("SU2_gauge", M_W, b_Y=0.0, b_2=-22.0 / 3.0, triple=None))
    return parts


# ── Threshold sum with per-particle weight F(triple) ─────────────────────
def T_sums(particles: List[Particle], F: WeightFn, mu_UV: float) -> Tuple[float, float, float, float]:
    """Return (T_Y_triple, T_2_triple, T_Y_neutral, T_2_neutral)
    where T_G_triple = Σ_{p with triple} F(triple_p) · b_G^(p) · ln(μ/m_p)
    and T_G_neutral = Σ_{p no triple} b_G^(p) · ln(μ/m_p)."""
    TY = T2 = TYn = T2n = 0.0
    for p in particles:
        if p.mass_GeV <= 0 or mu_UV <= 0:
            continue
        log = math.log(mu_UV / p.mass_GeV)
        if p.triple is not None:
            w = F(p.triple)
            TY += w * p.b_Y * log
            T2 += w * p.b_2 * log
        else:
            TYn += p.b_Y * log
            T2n += p.b_2 * log
    return TY, T2, TYn, T2n


def solve_alpha_both(TY, T2, TYn, T2n, alpha_n):
    """Given fixed alpha_n (flavor-neutral UGP-atom coefficient), solve for alpha
    that lands δ_1 and δ_2 in their windows simultaneously.  Returns (alpha_opt,
    both_in_window, delta1, delta2) — alpha_opt is the analytic intersection
    of the two window-centered α's if they agree within tolerance; else None.
    """
    pref = 1.0 / (16.0 * math.pi ** 2)
    # δ_1 = pref · (α·TY + α_n·TYn) ; δ_2 = pref · (α·T2 + α_n·T2n)
    # Requested: δ_1 ∈ window_1, δ_2 ∈ window_2.
    if abs(TY) < 1e-30 or abs(T2) < 1e-30:
        return None, False, None, None
    # Solve per window: α such that δ_G = δ_G_center
    a1 = (DELTA1_C / pref - alpha_n * TYn) / TY
    a2 = (DELTA2_C / pref - alpha_n * T2n) / T2
    # Tolerances in α from window half-widths
    ta1 = DELTA1_HW / pref / abs(TY)
    ta2 = DELTA2_HW / pref / abs(T2)
    # Intersection must exist
    lo = max(a1 - ta1, a2 - ta2)
    hi = min(a1 + ta1, a2 + ta2)
    if lo > hi:
        return None, False, None, None
    alpha_mid = 0.5 * (lo + hi)
    d1 = pref * (alpha_mid * TY + alpha_n * TYn)
    d2 = pref * (alpha_mid * T2 + alpha_n * T2n)
    in_w = (DELTA1_WIN[0] <= d1 <= DELTA1_WIN[1]) and (DELTA2_WIN[0] <= d2 <= DELTA2_WIN[1])
    return alpha_mid, in_w, d1, d2


def ugp_atom_library() -> Dict[str, float]:
    # re-use the library from NN (slightly reduced)
    return {
        "zero": 0.0, "one": 1.0, "neg_one": -1.0, "two": 2.0, "neg_two": -2.0,
        "three": 3.0, "neg_three": -3.0, "four": 4.0, "half": 0.5, "neg_half": -0.5,
        "third": 1 / 3, "neg_third": -1 / 3, "two_thirds": 2 / 3,
        "phi": PHI, "neg_phi": -PHI, "inv_phi": 1 / PHI, "neg_inv_phi": -1 / PHI,
        "phi2": PHI ** 2, "inv_phi2": 1 / PHI ** 2,
        "phi3": PHI ** 3, "inv_phi3": 1 / PHI ** 3,
        "sqrt5": math.sqrt(5.0), "inv_sqrt5": 1 / math.sqrt(5.0),
        "k_gen": PHI * math.cos(math.pi / 10), "k_gen2": -PHI / 2,
        "k_L2": 7 / 512, "k_mu_a": 1 / 8, "k_mu_b": -3 / 2, "k_mu_c": 4 / 3,
        "cos_pi5": math.cos(math.pi / 5), "cos_2pi5": math.cos(2 * math.pi / 5),
        "cos_pi10": math.cos(math.pi / 10),
    }


def scan_over_F_alpha_mu(particles: List[Particle], atoms: Dict[str, float], mus) -> List[Dict]:
    """For each weight function F, α_n ∈ atoms, α ∈ atoms, μ ∈ mus: check closure."""
    cat = weight_catalog()
    closures: List[Dict] = []
    for fname, F in cat.items():
        for an_name, an in atoms.items():
            for mu in mus:
                TY, T2, TYn, T2n = T_sums(particles, F, mu)
                # iterate α atoms
                for a_name, a in atoms.items():
                    pref = 1.0 / (16.0 * math.pi ** 2)
                    d1 = pref * (a * TY + an * TYn)
                    d2 = pref * (a * T2 + an * T2n)
                    if DELTA1_WIN[0] <= d1 <= DELTA1_WIN[1] and DELTA2_WIN[0] <= d2 <= DELTA2_WIN[1]:
                        closures.append({
                            "weight_fn": fname, "alpha_atom": a_name, "alpha_val": a,
                            "alpha_n_atom": an_name, "alpha_n_val": an,
                            "mu_UV_GeV": float(mu),
                            "delta1": d1, "delta2": d2,
                        })
    return closures


def analytic_closure_F_mu(particles, F, mus, atoms) -> List[Dict]:
    """Analytic version: for each (F, μ, α_n) solve for α and check if any
    α-atom matches within window half-width."""
    matches: List[Dict] = []
    for mu in mus:
        TY, T2, TYn, T2n = T_sums(particles, F, mu)
        if abs(TY) < 1e-30 or abs(T2) < 1e-30:
            continue
        for an_name, an in atoms.items():
            pref = 1.0 / (16.0 * math.pi ** 2)
            a1 = (DELTA1_C / pref - an * TYn) / TY
            a2 = (DELTA2_C / pref - an * T2n) / T2
            ta1 = DELTA1_HW / pref / abs(TY)
            ta2 = DELTA2_HW / pref / abs(T2)
            lo = max(a1 - ta1, a2 - ta2)
            hi = min(a1 + ta1, a2 + ta2)
            if lo > hi:
                continue
            # Any UGP atom α in [lo, hi]?
            for a_name, a in atoms.items():
                if lo <= a <= hi:
                    d1 = pref * (a * TY + an * TYn)
                    d2 = pref * (a * T2 + an * T2n)
                    matches.append({
                        "mu_UV_GeV": float(mu), "alpha_atom": a_name, "alpha_val": a,
                        "alpha_n_atom": an_name, "alpha_n_val": an,
                        "alpha_window": [lo, hi],
                        "delta1": d1, "delta2": d2,
                    })
    return matches


def triple_permutation_null(F_name: str, F: WeightFn, atoms, mus,
                              n_perm: int = 2000, seed: int = 20260424) -> Dict:
    """Permute triples across 9 charged-fermion slots, rerun analytic closure test,
    report hit rate."""
    rng = random.Random(seed)
    names = list(FERMION_TRIPLES.keys())
    original = [FERMION_TRIPLES[n] for n in names]
    hits = 0
    for _ in range(n_perm):
        perm = list(original)
        rng.shuffle(perm)
        assignment = {names[i]: perm[i] for i in range(9)}
        particles = build_sm_particles(assignment)
        matches = analytic_closure_F_mu(particles, F, mus, atoms)
        if matches:
            hits += 1
    return {"weight_fn": F_name, "n_perm": n_perm, "hits": hits, "hit_rate": hits / n_perm}


def main():
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    atoms = ugp_atom_library()
    cat = weight_catalog()

    # Physical μ_UV grid: from just above top threshold up to near-Planck
    mus = list(np.logspace(math.log10(200.0), math.log10(1e19), 501))

    real_assignment = {n: FERMION_TRIPLES[n] for n in FERMION_TRIPLES}
    real_particles = build_sm_particles(real_assignment)

    # Real scan (analytic)
    print(f"[OO] real SM triple assignment, analytic closure over {len(cat)} F × {len(atoms)} α_n × {len(mus)} μ...", flush=True)
    real_by_F: Dict[str, List[Dict]] = {}
    for fname, F in cat.items():
        matches = analytic_closure_F_mu(real_particles, F, mus, atoms)
        real_by_F[fname] = matches
        print(f"[OO]   F={fname:20s}  closures={len(matches)}", flush=True)

    # Triple permutation null
    print(f"\n[OO] triple-permutation null (2000 perms) per F ...", flush=True)
    null_by_F: Dict[str, Dict] = {}
    t0 = time.time()
    for fname, F in cat.items():
        # only test null for F's that have REAL closures — otherwise null is vacuously 0
        n_perm = 2000 if len(real_by_F[fname]) > 0 else 500
        nres = triple_permutation_null(fname, F, atoms, mus, n_perm=n_perm)
        null_by_F[fname] = nres
        print(f"[OO]   F={fname:20s}  null_hits={nres['hits']}/{nres['n_perm']}  rate={nres['hit_rate']:.4f}  [t={time.time()-t0:.0f}s]", flush=True)

    # Summary
    structural = []
    for fname in cat:
        real_hits = len(real_by_F[fname])
        null_rate = null_by_F[fname]["hit_rate"]
        if real_hits > 0 and null_rate < 0.01:
            structural.append({
                "weight_fn": fname, "real_closures": real_hits,
                "null_perm_rate": null_rate,
                "sample_closure": real_by_F[fname][0],
            })

    prediction_block = {
        "comp_id": "COMP-P01-OO",
        "spec_reference": "10_SPEC extension: number-theoretic per-particle triple properties as threshold-correction weights",
        "timestamp_utc": ts,
        "mu_UV_grid": {"n": len(mus), "range_GeV": [mus[0], mus[-1]]},
        "weight_catalog": list(cat.keys()),
        "atom_library_size": len(atoms),
        "closure_windows_PDG_1sigma": {"delta1": list(DELTA1_WIN), "delta2": list(DELTA2_WIN)},
        "real_closures_by_F": {k: {"n_closures": len(v), "samples": v[:5]} for k, v in real_by_F.items()},
        "triple_permutation_null": null_by_F,
        "structural_closures": structural,
    }
    pred_json = json.dumps(prediction_block, sort_keys=True, separators=(",", ":"), default=str)
    sha = hashlib.sha256(pred_json.encode("utf-8")).hexdigest()

    n_structural = len(structural)
    pdg_cmp = {
        "prediction_block_sha256": sha,
        "n_weight_functions_tested": len(cat),
        "n_weight_functions_with_real_closure": sum(1 for v in real_by_F.values() if v),
        "n_structural_closures_passing_permutation_null": n_structural,
        "structural_weight_functions": [s["weight_fn"] for s in structural],
        "verdict": ("STRUCTURAL_CLOSURE_CONFIRMED" if n_structural > 0 else
                    "MAP_numtheoretic_triple_weights_insufficient_or_density_dominated"),
    }
    return {
        "prediction_block_precomparison": prediction_block,
        "sha256_prediction_block": sha,
        "pdg_comparison": pdg_cmp,
    }


if __name__ == "__main__":
    out = main()
    path = "comp_p01_OO_numtheoretic_triple_threshold.json"
    with open(path, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print()
    print(json.dumps(out["pdg_comparison"], indent=2, default=str))
    print(f"Written: {path}")
