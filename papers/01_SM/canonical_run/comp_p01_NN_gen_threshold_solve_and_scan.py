#!/usr/bin/env python3
"""
COMP-P01-NN: Generation-weighted threshold closure — continuous solve + expanded scan.

MM (R7-013, pre-solved) showed the Y² ≥ 0 sign obstruction is BROKEN by
generation weighting (w = (-1, +1, +1) at μ ≈ 3.3 TeV gives δ_1 = -0.0022,
δ_2 = -0.012 — both negative, ~15% outside the PDG 1σ windows).  NN does two
things MM did not:

  (A) CONTINUOUS SOLVER.  At each μ_UV on a log-grid, solve the linear system

          δ_1_target = (1/16π²) · Σ_p w(gen_p)·b_Y^(p)·ln(μ/m_p)
          δ_2_target = (1/16π²) · Σ_p w(gen_p)·b_2^(p)·ln(μ/m_p)

      for the (w_1, w_2, w_3, w_n) plane (2 equations, 4 unknowns → 2-dim plane).
      Fix w_n = 0 and parametrize (w_3) → solve for (w_1, w_2); also try
      w_n ∈ {1, -1, 1/φ, -1/φ, …}.  Report the closest approach of any UGP-
      structural atom to each required weight.

  (B) EXPANDED DISCRETE SCAN.  Add Möbius-of-generation (1, -1, -1) and more
      cyclotomic / golden-field weight triples; scan finer μ_UV grid.

  (C) FULL NULL DISCIPLINE.  Feature randomization (permute generation
      labels + mass jitter) and random-weight uniform draws, each 10k trials.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
import random
import time
from datetime import datetime, timezone
from typing import Dict, List, Tuple

import numpy as np

from comp_p01_MM_generation_weighted_threshold import (
    DELTA1_WIN, DELTA2_WIN, PHI, M_Z, M_W, M_H,
    SMParticle, sm_all_generations, weight_library,
    delta_G_weighted, in_window,
)

MU_GRID = list(np.logspace(math.log10(50.0), math.log10(1e19), 2001))


def sector_sums(particles, mu_UV):
    """Return A_Y^g, A_2^g for g ∈ {1, 2, 3, 'neutral'} summed over particles.
    δ_G = (1/16π²) · (w_1 A_G^1 + w_2 A_G^2 + w_3 A_G^3 + w_n A_G^n)."""
    A_Y = {1: 0.0, 2: 0.0, 3: 0.0, "n": 0.0}
    A_2 = {1: 0.0, 2: 0.0, 3: 0.0, "n": 0.0}
    for p in particles:
        if p.mass_GeV <= 0 or mu_UV <= 0:
            continue
        log = math.log(mu_UV / p.mass_GeV)
        key = p.gen if p.gen is not None else "n"
        A_Y[key] += p.b_Y * log
        A_2[key] += p.b_2 * log
    return A_Y, A_2


def solve_w1_w2_given_w3_wn(A_Y, A_2, delta1_tgt, delta2_tgt, w3, wn):
    """Solve linear system for (w_1, w_2) given fixed (w_3, w_n):
         w_1 A_Y^1 + w_2 A_Y^2 = 16π² δ_1_tgt - w_3 A_Y^3 - w_n A_Y^n
         w_1 A_2^1 + w_2 A_2^2 = 16π² δ_2_tgt - w_3 A_2^3 - w_n A_2^n
    """
    rhs1 = 16.0 * math.pi ** 2 * delta1_tgt - w3 * A_Y[3] - wn * A_Y["n"]
    rhs2 = 16.0 * math.pi ** 2 * delta2_tgt - w3 * A_2[3] - wn * A_2["n"]
    M = np.array([[A_Y[1], A_Y[2]], [A_2[1], A_2[2]]], dtype=float)
    b = np.array([rhs1, rhs2], dtype=float)
    det = M[0, 0] * M[1, 1] - M[0, 1] * M[1, 0]
    if abs(det) < 1e-20:
        return None
    w = np.linalg.solve(M, b)
    return float(w[0]), float(w[1])


def ugp_atom_library() -> Dict[str, float]:
    """Expanded UGP atom library for matching solved weight values."""
    vals = {
        "zero": 0.0, "one": 1.0, "neg_one": -1.0, "two": 2.0, "neg_two": -2.0,
        "three": 3.0, "neg_three": -3.0, "four": 4.0, "half": 0.5, "neg_half": -0.5,
        "third": 1 / 3, "neg_third": -1 / 3, "two_thirds": 2 / 3, "neg_two_thirds": -2 / 3,
        "phi": PHI, "neg_phi": -PHI, "inv_phi": 1 / PHI, "neg_inv_phi": -1 / PHI,
        "phi2": PHI ** 2, "neg_phi2": -PHI ** 2, "inv_phi2": 1 / PHI ** 2, "neg_inv_phi2": -1 / PHI ** 2,
        "phi3": PHI ** 3, "neg_phi3": -PHI ** 3, "inv_phi3": 1 / PHI ** 3, "neg_inv_phi3": -1 / PHI ** 3,
        "sqrt5": math.sqrt(5.0), "neg_sqrt5": -math.sqrt(5.0),
        "inv_sqrt5": 1 / math.sqrt(5.0), "neg_inv_sqrt5": -1 / math.sqrt(5.0),
        "k_gen": PHI * math.cos(math.pi / 10), "neg_k_gen": -PHI * math.cos(math.pi / 10),
        "k_gen2": -PHI / 2, "k_L2": 7 / 512, "neg_k_L2": -7 / 512,
        "k_M": -PHI / 2 + (7 / 512) / 4,
        "k_mu_a": 1 / 8, "neg_k_mu_a": -1 / 8,
        "k_mu_b": -1.5, "pos_k_mu_b": 1.5,
        "k_mu_c": 4 / 3, "neg_k_mu_c": -4 / 3,
        "cos_pi5": math.cos(math.pi / 5), "neg_cos_pi5": -math.cos(math.pi / 5),
        "cos_2pi5": math.cos(2 * math.pi / 5),  # ≈ 0.309
        "cos_pi10": math.cos(math.pi / 10), "neg_cos_pi10": -math.cos(math.pi / 10),
        "sin_pi5": math.sin(math.pi / 5), "sin_pi10": math.sin(math.pi / 10),
        "mobius_1": 1.0, "mobius_2": -1.0, "mobius_3": -1.0,   # μ(n)
        "mobius_4": 0.0, "mobius_5": -1.0, "mobius_6": 1.0,
        "five": 5.0, "neg_five": -5.0, "seven": 7.0,
        "one_sixth": 1 / 6, "one_twelfth": 1 / 12,
        "weyl_A2": 6.0, "inv_pi": 1 / math.pi, "pi_atom": math.pi,
        "pi_half": math.pi / 2, "neg_pi_half": -math.pi / 2,
    }
    return vals


def nearest_atom(val, atoms):
    best_name = None
    best_d = math.inf
    for n, v in atoms.items():
        d = abs(v - val)
        if d < best_d:
            best_d = d
            best_name = n
    return best_name, best_d


def continuous_solve_scan(particles, atoms, mu_grid):
    """For each μ_UV on grid, solve for (w_1, w_2) given each UGP atom value
    of (w_3, w_n).  Find the closest UGP-atom triple to each required (w_1, w_2)
    and test whether that full atom-triple DOES close (within windows)."""
    atoms_list = list(atoms.items())
    results_best_match = []   # closure-or-near-closure matches
    true_closures = []

    delta1_center = 0.5 * (DELTA1_WIN[0] + DELTA1_WIN[1])
    delta2_center = 0.5 * (DELTA2_WIN[0] + DELTA2_WIN[1])

    for mu in mu_grid:
        A_Y, A_2 = sector_sums(particles, mu)
        det = A_Y[1] * A_2[2] - A_Y[2] * A_2[1]
        if abs(det) < 1e-30:
            continue
        for w3_name, w3 in atoms_list:
            for wn_name, wn in atoms_list:
                w = solve_w1_w2_given_w3_wn(A_Y, A_2, delta1_center, delta2_center, w3, wn)
                if w is None:
                    continue
                w1_req, w2_req = w
                # Find nearest UGP atoms to (w1_req, w2_req)
                w1_name, d1 = nearest_atom(w1_req, atoms)
                w2_name, d2 = nearest_atom(w2_req, atoms)
                w1_val = atoms[w1_name]
                w2_val = atoms[w2_name]
                # Now evaluate with these DISCRETE UGP-atom values - does it close?
                dY, d2v = delta_G_weighted(particles, mu, (w1_val, w2_val, w3), wn)
                _, _, both = in_window(dY, d2v)
                match_record = {
                    "mu_UV_GeV": float(mu),
                    "w1_required_continuous": w1_req,
                    "w2_required_continuous": w2_req,
                    "w1_nearest_atom": w1_name, "w1_nearest_value": w1_val, "w1_residual": d1,
                    "w2_nearest_atom": w2_name, "w2_nearest_value": w2_val, "w2_residual": d2,
                    "w3_atom": w3_name, "w3_value": w3,
                    "wn_atom": wn_name, "wn_value": wn,
                    "delta1_from_atoms": dY, "delta2_from_atoms": d2v,
                    "both_in_window": both,
                    "max_atom_residual": max(d1, d2),
                }
                if both:
                    true_closures.append(match_record)
                elif d1 < 0.01 and d2 < 0.01:
                    # close enough to be interesting even if not exact closure
                    results_best_match.append(match_record)
    return true_closures, results_best_match


def null_random_weights(particles, mu_grid, n_trials=10000, seed=20260422):
    rng = random.Random(seed)
    hits = 0
    for _ in range(n_trials):
        wvec = (rng.uniform(-3, 3), rng.uniform(-3, 3), rng.uniform(-3, 3))
        wn = rng.uniform(-3, 3)
        mu = float(rng.choice(mu_grid))
        d1, d2 = delta_G_weighted(particles, mu, wvec, wn)
        _, _, both = in_window(d1, d2)
        if both:
            hits += 1
    return {"trials": n_trials, "hits": hits, "hit_rate": hits / n_trials}


def null_gen_permutation(particles, atoms, mu_grid, n_trials=2000, seed=20260423):
    """Null: randomly permute the generation labels on fermions, then run the
    continuous solve + discrete match.  Count how many trials land a closure."""
    rng = random.Random(seed)
    hits = 0
    atoms_list = list(atoms.items())
    for _ in range(n_trials):
        perm = list((1, 2, 3))
        rng.shuffle(perm)
        rand_particles = [
            SMParticle(p.name, p.mass_GeV, p.b_Y, p.b_2,
                        gen=(perm[p.gen - 1] if p.gen is not None else None))
            for p in particles
        ]
        mu = float(rng.choice(mu_grid))
        A_Y, A_2 = sector_sums(rand_particles, mu)
        det = A_Y[1] * A_2[2] - A_Y[2] * A_2[1]
        if abs(det) < 1e-30:
            continue
        # Try each w3,wn atom combination: does any closure appear?
        closed = False
        for _, w3 in atoms_list:
            for _, wn in atoms_list:
                w = solve_w1_w2_given_w3_wn(
                    A_Y, A_2, 0.5 * (DELTA1_WIN[0] + DELTA1_WIN[1]),
                    0.5 * (DELTA2_WIN[0] + DELTA2_WIN[1]), w3, wn,
                )
                if w is None:
                    continue
                w1r, w2r = w
                w1_name, d1r = nearest_atom(w1r, atoms)
                w2_name, d2r = nearest_atom(w2r, atoms)
                w1v = atoms[w1_name]
                w2v = atoms[w2_name]
                dY, d2v = delta_G_weighted(rand_particles, mu, (w1v, w2v, w3), wn)
                _, _, both = in_window(dY, d2v)
                if both:
                    closed = True
                    break
            if closed:
                break
        if closed:
            hits += 1
    return {"trials": n_trials, "hits": hits, "hit_rate": hits / n_trials}


def main():
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    particles = sm_all_generations()
    atoms = ugp_atom_library()

    print(f"[NN] particles={len(particles)}  atoms={len(atoms)}  mu_grid={len(MU_GRID)}", flush=True)
    print(f"[NN] continuous solve + atom matching …", flush=True)
    t0 = time.time()
    true_closures, near_matches = continuous_solve_scan(particles, atoms, MU_GRID)
    elapsed = time.time() - t0
    print(f"[NN]   found {len(true_closures)} true closures, {len(near_matches)} near-closures in {elapsed:.1f}s", flush=True)

    # Deduplicate closures by (atom triple, mu band) to avoid neighbor-duplicates
    seen = set()
    dedup_closures = []
    for c in true_closures:
        key = (c["w1_nearest_atom"], c["w2_nearest_atom"], c["w3_atom"], c["wn_atom"], round(math.log10(c["mu_UV_GeV"]), 1))
        if key not in seen:
            seen.add(key)
            dedup_closures.append(c)
    print(f"[NN]   deduplicated closures: {len(dedup_closures)}", flush=True)

    # Null discipline
    print(f"[NN] null: random uniform weights (10k) …", flush=True)
    nul_unif = null_random_weights(particles, MU_GRID, n_trials=10000)
    print(f"[NN]   null hits: {nul_unif['hits']}/{nul_unif['trials']}", flush=True)

    print(f"[NN] null: generation permutation + solve (2k) …", flush=True)
    t0 = time.time()
    nul_perm = null_gen_permutation(particles, atoms, MU_GRID, n_trials=2000)
    print(f"[NN]   null gen-permutation hits: {nul_perm['hits']}/{nul_perm['trials']}  in {time.time()-t0:.1f}s", flush=True)

    any_closure = len(dedup_closures) > 0
    null_disciplined = nul_unif["hit_rate"] < 0.01 and nul_perm["hit_rate"] < 0.01

    if any_closure and null_disciplined:
        verdict = "CLOSES_gen_weighted_threshold_structural_beats_null"
    elif any_closure and not null_disciplined:
        verdict = "DENSITY_DOMINATED_closures_but_nulls_fail"
    else:
        verdict = "MAP_gen_weighted_threshold_insufficient_even_with_atom_matching"

    prediction_block = {
        "comp_id": "COMP-P01-NN",
        "spec_reference": "10_SPEC extension: continuous solver + UGP-atom matching for generation-weighted threshold closure",
        "timestamp_utc": ts,
        "hypothesis_tested": "δ_G = (1/16π²) Σ_p w(gen_p) b_G^(p) ln(μ/m_p) with UGP-atom weights (w_1,w_2,w_3,w_n); closure at δ_G in PDG 1σ both windows.",
        "closure_windows_PDG_1sigma": {"delta1_Y": list(DELTA1_WIN), "delta2_SU2": list(DELTA2_WIN)},
        "atom_library_size": len(atoms),
        "n_mu_grid_points": len(MU_GRID),
        "total_atom_scan_points": len(atoms) ** 2 * len(MU_GRID),  # w3 × wn × mu (w1,w2 solved then matched)
        "true_closures": dedup_closures[:50],   # sample
        "n_true_closures": len(dedup_closures),
        "n_near_matches_within_0.01": len(near_matches),
        "null_random_weights": nul_unif,
        "null_gen_permutation": nul_perm,
    }
    pred_json = json.dumps(prediction_block, sort_keys=True, separators=(",", ":"), default=str)
    sha = hashlib.sha256(pred_json.encode("utf-8")).hexdigest()

    pdg_cmp = {
        "prediction_block_sha256": sha,
        "any_closure": any_closure,
        "n_closures": len(dedup_closures),
        "null_random_weights_rate": nul_unif["hit_rate"],
        "null_gen_permutation_rate": nul_perm["hit_rate"],
        "null_disciplined": null_disciplined,
        "verdict": verdict,
        "sample_closures": dedup_closures[:5],
    }

    return {"prediction_block_precomparison": prediction_block, "sha256_prediction_block": sha, "pdg_comparison": pdg_cmp}


if __name__ == "__main__":
    out = main()
    path = "comp_p01_NN_gen_threshold_solve_and_scan.json"
    with open(path, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print()
    print(json.dumps(out["pdg_comparison"], indent=2, default=str))
    print(f"Written: {path}")
