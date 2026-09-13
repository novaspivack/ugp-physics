#!/usr/bin/env python3
"""
COMP-P01-MM: Generation-weighted threshold corrections for sin²θ_W (10_SPEC extension)

Motivation: LL (R7-012) established a HARD IMPOSSIBILITY for flavor-universal
additive SM 1-loop threshold corrections, because b_Y^(p) ∝ Y² ≥ 0 forces
δ_1 ≥ 0 when every SM particle is weighted equally.  The user-proposed
extension: UGP cascades naturally distinguish the three generations, so the
generation index gen ∈ {1, 2, 3} is a derivable structural atom.  Allowing
a per-generation weight w(gen) from a UGP-atom library drops flavor
universality and could permit δ_1 < 0 via negative weights on some generation.

Model:
    δ_G = (1 / 16π²) · Σ_{particles p} w(gen_p) · b_G^(p) · ln(μ_UV / m_p)

Scan: choose w = (w_1, w_2, w_3) where each w_i ∈ {UGP atom library}.
      For each weight triple and each μ_UV on a log-grid, check PDG 1σ window
      closure on both (δ_1, δ_2).  Null: randomize weight triples (1000 trials).

SM particle table (all 3 generations, fermions only, plus Higgs and SU(2)
gauge-self, with PDG masses):
    Gen 1: (e, ν_e, u, d)
    Gen 2: (μ, ν_μ, c, s)
    Gen 3: (τ, ν_τ, t, b)
    Flavor-neutral: Higgs, W (SU(2) gauge self)
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
import random
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import numpy as np

# PDG 1σ windows (same as LL)
DELTA1_WIN = (-0.00289, -0.00244)
DELTA2_WIN = (-0.01768, -0.01406)

PHI = (1.0 + math.sqrt(5.0)) / 2.0
M_Z = 91.1876
M_W = 80.379
M_H = 125.25


@dataclass
class SMParticle:
    name: str
    mass_GeV: float
    b_Y: float
    b_2: float
    gen: Optional[int]   # 1, 2, 3 for fermions; None for flavor-neutral


def sm_all_generations() -> List[SMParticle]:
    """SM particle table, all three generations, with PDG masses, plus flavor-neutral."""
    # Per-Weyl-fermion b's (non-GUT norm)
    # Q_L per family: b_Y = (2/3)·3·2·(1/6)² = 1/9; b_2 = (2/3)·3·(1/2) = 1
    # u_R per family:  b_Y = (2/3)·3·(2/3)² = 8/9; b_2 = 0
    # d_R per family:  b_Y = (2/3)·3·(1/3)² = 2/9; b_2 = 0
    # L_L per family: b_Y = (2/3)·1·2·(1/2)² = 1/3; b_2 = (2/3)·1·(1/2) = 1/3
    # e_R per family:  b_Y = (2/3)·1·(1)² = 2/3; b_2 = 0
    # Higgs (flavor-neutral): b_Y = (1/3)·2·(1/2)² = 1/6; b_2 = (1/3)·(1/2) = 1/6
    #   [Note per PDG conventions Higgs complex doublet has T(R) = 1/2, so b_2 = 1/6.]
    # SU(2) gauge self: b_2 = -(11/3)·T(adj) = -22/3; b_Y = 0 (abelian)
    particles: List[SMParticle] = []
    gen_masses = {
        1: {"Q_L_d": 4.7e-3, "u_R": 2.16e-3, "d_R": 4.7e-3, "L_L": 0.5109989088e-3, "e_R": 0.5109989088e-3, "ν_L": 1e-9},
        2: {"Q_L_d": 0.093, "u_R": 1.275, "d_R": 0.093, "L_L": 0.1056583777, "e_R": 0.1056583777, "ν_L": 1e-9},
        3: {"Q_L_d": 4.18, "u_R": 172.76, "d_R": 4.18, "L_L": 1.77686, "e_R": 1.77686, "ν_L": 1e-9},
    }
    # For Q_L doublet we take the heavier of (u-type, d-type) as the decoupling scale
    # (standard approach for EW threshold matching).
    for g in (1, 2, 3):
        m = gen_masses[g]
        m_qL = max(m["Q_L_d"], m["u_R"])  # top-family: use 173; else use heavier quark
        particles.append(SMParticle(f"Q{g}_L", m_qL, 1.0 / 9.0, 1.0, g))
        particles.append(SMParticle(f"u{g}_R", m["u_R"], 8.0 / 9.0, 0.0, g))
        particles.append(SMParticle(f"d{g}_R", m["d_R"], 2.0 / 9.0, 0.0, g))
        particles.append(SMParticle(f"L{g}_L", m["L_L"], 1.0 / 3.0, 1.0 / 3.0, g))
        particles.append(SMParticle(f"e{g}_R", m["e_R"], 2.0 / 3.0, 0.0, g))
    # Flavor-neutral: Higgs + SU(2) gauge self
    particles.append(SMParticle("Higgs", M_H, 1.0 / 6.0, 1.0 / 6.0, None))
    particles.append(SMParticle("SU2_gauge", M_W, 0.0, -22.0 / 3.0, None))
    return particles


def weight_library() -> Dict[str, Tuple[float, float, float]]:
    """UGP-structural per-generation weight functions (gen = 1, 2, 3 → 3-tuple)."""
    return {
        "identity":          (1.0, 1.0, 1.0),
        "gen":               (1.0, 2.0, 3.0),
        "inv_gen":           (1.0, 0.5, 1.0 / 3.0),
        "gen2":              (1.0, 4.0, 9.0),
        "alt_sign":          (-1.0, 1.0, -1.0),
        "alt_sign_pos":      (1.0, -1.0, 1.0),
        "fibonacci":         (1.0, 1.0, 2.0),
        "fib_shift":         (1.0, 2.0, 3.0),
        "lucas":             (1.0, 3.0, 4.0),
        "phi_pow":           (1.0, PHI, PHI ** 2),
        "inv_phi_pow":       (1.0, 1.0 / PHI, 1.0 / PHI ** 2),
        "phi_galois":        (1.0, -1.0 / PHI, 1.0 / PHI ** 2),         # (-1/φ)^(g-1)
        "phi_galois_shift":  (-1.0 / PHI, 1.0 / PHI ** 2, -1.0 / PHI ** 3),
        "alt_phi":           (1.0, -PHI, PHI ** 2),
        "alt_inv_phi":       (1.0, -1.0 / PHI, 1.0 / PHI ** 2),
        "kgen_pow":          (1.0, PHI * math.cos(math.pi / 10.0), (PHI * math.cos(math.pi / 10.0)) ** 2),
        "neg_identity":      (-1.0, -1.0, -1.0),
        "first_only":        (1.0, 0.0, 0.0),
        "last_only":         (0.0, 0.0, 1.0),
        "first_neg_rest_pos": (-1.0, 1.0, 1.0),
        "gen_minus_two":     (-1.0, 0.0, 1.0),
        "cos_2pi_gen_5":     (math.cos(2 * math.pi / 5), math.cos(4 * math.pi / 5), math.cos(6 * math.pi / 5)),
        "zeta3_re":          (math.cos(2 * math.pi / 3), math.cos(4 * math.pi / 3), 1.0),
    }


def delta_G_weighted(
    particles: List[SMParticle],
    mu_UV: float,
    w_by_gen: Tuple[float, float, float],
    w_flavor_neutral: float = 1.0,
) -> Tuple[float, float]:
    pref = 1.0 / (16.0 * math.pi ** 2)
    dY = 0.0
    d2 = 0.0
    for p in particles:
        if p.mass_GeV <= 0 or mu_UV <= 0:
            continue
        log = math.log(mu_UV / p.mass_GeV)
        if p.gen is None:
            w = w_flavor_neutral
        else:
            w = w_by_gen[p.gen - 1]
        dY += w * p.b_Y * log
        d2 += w * p.b_2 * log
    return pref * dY, pref * d2


def in_window(d1, d2):
    ok1 = DELTA1_WIN[0] <= d1 <= DELTA1_WIN[1]
    ok2 = DELTA2_WIN[0] <= d2 <= DELTA2_WIN[1]
    return ok1, ok2, ok1 and ok2


def scan_over_weights_and_mu(particles, weights: Dict[str, Tuple[float, float, float]], mus):
    hits = []
    near = []
    all_rows = []
    for wname, wvec in weights.items():
        # scan flavor-neutral weight separately, small library
        for wfn_label, wfn in [("w_neutral=+1", 1.0), ("w_neutral=0", 0.0), ("w_neutral=-1", -1.0),
                                ("w_neutral=phi", PHI), ("w_neutral=-phi", -PHI)]:
            for mu in mus:
                d1, d2 = delta_G_weighted(particles, mu, wvec, wfn)
                ok1, ok2, both = in_window(d1, d2)
                row = {
                    "weight": wname, "weight_vec": list(wvec),
                    "w_neutral": wfn, "w_neutral_label": wfn_label,
                    "mu_UV_GeV": float(mu),
                    "delta1": d1, "delta2": d2,
                    "in_delta1_window": ok1, "in_delta2_window": ok2, "both_in_window": both,
                }
                all_rows.append(row)
                if both:
                    hits.append(row)
                elif ok1 or ok2:
                    near.append(row)
    return hits, near, all_rows


def null_random_weights(particles, mus, n_trials=10000, seed=20260419):
    """Null: replace per-generation weights with random draws from (-2, 2), flat."""
    rng = random.Random(seed)
    hits = 0
    hits_mu = {}
    best = math.inf
    for t in range(n_trials):
        wvec = (rng.uniform(-2, 2), rng.uniform(-2, 2), rng.uniform(-2, 2))
        wfn = rng.uniform(-2, 2)
        mu = rng.choice(mus)
        d1, d2 = delta_G_weighted(particles, float(mu), wvec, wfn)
        _, _, both = in_window(d1, d2)
        if both:
            hits += 1
            hits_mu.setdefault(round(math.log10(mu), 1), 0)
            hits_mu[round(math.log10(mu), 1)] += 1
        dist = max(
            max(0, DELTA1_WIN[0] - d1, d1 - DELTA1_WIN[1]),
            max(0, DELTA2_WIN[0] - d2, d2 - DELTA2_WIN[1]),
        )
        best = min(best, dist)
    return {
        "trials": n_trials, "hits": hits, "hit_rate": hits / n_trials,
        "best_distance": best, "hits_by_log10_mu": hits_mu,
    }


def null_feature_randomization(particles, weights, mus, n_trials=1000, seed=20260421):
    """Null: randomize the generation assignment of fermions (permute gen labels 1↔2↔3)
    AND keep same atom-weight library.  Structural null against gen-assignment meaning."""
    rng = random.Random(seed)
    hits = 0
    for _ in range(n_trials):
        perm = list((1, 2, 3))
        rng.shuffle(perm)
        rand_particles = [
            SMParticle(p.name, p.mass_GeV, p.b_Y, p.b_2,
                        gen=perm[p.gen - 1] if p.gen is not None else None)
            for p in particles
        ]
        # Also random mass jitter ±10x in log
        rand_particles = [
            SMParticle(p.name, p.mass_GeV * 10 ** rng.uniform(-1, 1), p.b_Y, p.b_2, p.gen)
            for p in rand_particles
        ]
        wname = rng.choice(list(weights.keys()))
        wvec = weights[wname]
        wfn = rng.choice([1.0, 0.0, -1.0, PHI, -PHI])
        mu = rng.choice(mus)
        d1, d2 = delta_G_weighted(rand_particles, float(mu), wvec, wfn)
        _, _, both = in_window(d1, d2)
        if both:
            hits += 1
    return {"trials": n_trials, "hits": hits, "hit_rate": hits / n_trials}


def main():
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    particles = sm_all_generations()
    weights = weight_library()

    mus = list(np.logspace(math.log10(50.0), math.log10(1e19), 201))

    hits, near, all_rows = scan_over_weights_and_mu(particles, weights, mus)

    null_unif = null_random_weights(particles, mus, n_trials=10000)
    null_feat = null_feature_randomization(particles, weights, mus, n_trials=1000)

    # Characterize near-misses (single window)
    d1_only = [r for r in near if r["in_delta1_window"] and not r["in_delta2_window"]]
    d2_only = [r for r in near if r["in_delta2_window"] and not r["in_delta1_window"]]

    # Pick best joint candidate: minimize max distance to both windows
    def joint_dist(r):
        return max(
            max(0, DELTA1_WIN[0] - r["delta1"], r["delta1"] - DELTA1_WIN[1]),
            max(0, DELTA2_WIN[0] - r["delta2"], r["delta2"] - DELTA2_WIN[1]),
        )
    best_joint = min(all_rows, key=joint_dist)

    any_closure = len(hits) > 0
    null_disciplined = null_unif["hit_rate"] < 0.01 and null_feat["hit_rate"] < 0.01

    if any_closure and null_disciplined:
        verdict = "CLOSES_gen_weighted_threshold_beats_null"
    elif any_closure and not null_disciplined:
        verdict = "DENSITY_DOMINATED_nulls_fail"
    elif not any_closure:
        verdict = "MAP_gen_weighted_threshold_insufficient"

    prediction_block = {
        "comp_id": "COMP-P01-MM",
        "spec_reference": "10_SPEC extension: user-proposed generation-weighted threshold corrections",
        "hypothesis_tested": "δ_G = (1/16π²) Σ_p w(gen_p) · b_G^(p) · ln(μ_UV/m_p) with w from UGP-structural weight library",
        "closure_windows_PDG_1sigma": {"delta1_Y": list(DELTA1_WIN), "delta2_SU2": list(DELTA2_WIN)},
        "timestamp_utc": ts,
        "weight_library": {k: list(v) for k, v in weights.items()},
        "sm_particle_table": [asdict(p) for p in particles],
        "n_weight_triples": len(weights),
        "n_mu_grid_points": len(mus),
        "n_w_neutral_variants": 5,
        "total_scan_points": len(weights) * 5 * len(mus),
        "closures": hits,
        "n_closures": len(hits),
        "delta1_only_near_misses_count": len(d1_only),
        "delta2_only_near_misses_count": len(d2_only),
        "best_joint_distance_candidate": best_joint,
        "null_random_weights": null_unif,
        "null_feature_randomization": null_feat,
    }

    pred_json = json.dumps(prediction_block, sort_keys=True, separators=(",", ":"), default=str)
    sha = hashlib.sha256(pred_json.encode("utf-8")).hexdigest()

    pdg_cmp = {
        "prediction_block_sha256": sha,
        "any_closure": any_closure,
        "n_closures": len(hits),
        "null_random_weights_rate": null_unif["hit_rate"],
        "null_feature_randomization_rate": null_feat["hit_rate"],
        "null_disciplined": null_disciplined,
        "verdict": verdict,
        "best_joint_distance": joint_dist(best_joint),
    }

    return {
        "prediction_block_precomparison": prediction_block,
        "sha256_prediction_block": sha,
        "pdg_comparison": pdg_cmp,
    }


if __name__ == "__main__":
    out = main()
    path = "comp_p01_MM_generation_weighted_threshold.json"
    with open(path, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print()
    print(json.dumps(out["pdg_comparison"], indent=2, default=str))
    print(f"Written: {path}")
