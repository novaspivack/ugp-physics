#!/usr/bin/env python3
"""
COMP-P01-PP: TIGHTENED joint (sin²θ_W + m_W) closure test (10_SPEC + 06_SPEC merger)

Insight (derived from R7-012 → R7-013 → R7-014 trajectory):

  The R7-012 "hard impossibility" for sin²θ_W via SM threshold corrections
  was computed assuming the sin²θ_W-ONLY δ_1 window (negative, from 05_SPEC).
  But closing sin²θ_W AND m_W SIMULTANEOUSLY shifts the required (δ_1, δ_2) to
  (+0.000210, -0.005013), with positive δ_1 — which is *exactly* what the
  Y² ≥ 0 flavor-universal threshold sum naturally produces.  The magnitudes
  are wrong by ~50× in LL, but the signs are right.

  Tightened joint windows (this comp):
    δ_1 ∈ (+0.000181, +0.000239)   (width 2.9e-5)
    δ_2 ∈ (-0.005140, -0.004886)   (width 1.3e-4)
  Joint 2-dim volume ≈ 1.5e-8  (≈100× smaller than sin²θ_W-alone 1.6e-6).

Test design:
  (A) LL flavor-universal scan: compute (δ_1, δ_2)(μ_UV) across a fine
      μ_UV grid with the fixed SM third-family + Higgs + gauge particle set;
      check if any μ_UV closes the joint window.  Scale the sum by a UGP-atom
      scalar α to see if any structural overall scale rescues the magnitude.
  (B) Gen-weighted scan: MM/NN-style (w_1, w_2, w_3, α_n) × μ_UV search on
      the 59-atom scalar library, tightened joint window.
  (C) Number-theoretic triple scan: OO-style F(triple) × α × α_n × μ_UV on
      the 32-atom library, tightened joint window.
  (D) Triple-permutation null for (C) at 2000 trials per weight function.

Gate:
  - STRUCTURAL CLOSURE: at least one (F, α, α_n, μ_UV) combination lands in
    the tightened joint window AND triple-permutation null rate < 1%.
  - Otherwise: MAP → next queue item (06_SPEC as its own track).
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
import random
import time
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import numpy as np

from comp_p01_OO_numtheoretic_triple_threshold import (
    weight_catalog, ugp_atom_library,
    T_sums, build_sm_particles, FERMION_TRIPLES,
)

# ── Tightened joint windows ──────────────────────────────────────────────
JOINT_DELTA1_WIN = (+0.000181, +0.000239)
JOINT_DELTA2_WIN = (-0.005140, -0.004886)

# Also expose sin²θ_W-only windows for diagnostic comparison
SIN2_DELTA1_WIN = (-0.00289, -0.00244)
SIN2_DELTA2_WIN = (-0.01768, -0.01406)

PHI = (1.0 + math.sqrt(5.0)) / 2.0


def in_joint_window(d1, d2):
    ok1 = JOINT_DELTA1_WIN[0] <= d1 <= JOINT_DELTA1_WIN[1]
    ok2 = JOINT_DELTA2_WIN[0] <= d2 <= JOINT_DELTA2_WIN[1]
    return ok1, ok2, ok1 and ok2


def in_sin2_window(d1, d2):
    ok1 = SIN2_DELTA1_WIN[0] <= d1 <= SIN2_DELTA1_WIN[1]
    ok2 = SIN2_DELTA2_WIN[0] <= d2 <= SIN2_DELTA2_WIN[1]
    return ok1 and ok2


def scan_F_joint(particles, F, atoms: Dict[str, float], mus, closure_windows) -> List[Dict]:
    """Scan a single weight function F over (α_n, α, μ_UV) for joint closure."""
    hits = []
    delta1_win, delta2_win = closure_windows
    for mu in mus:
        TY, T2, TYn, T2n = T_sums(particles, F, mu)
        if abs(TY) < 1e-30 and abs(T2) < 1e-30:
            continue
        pref = 1.0 / (16.0 * math.pi ** 2)
        for an_name, an in atoms.items():
            for a_name, a in atoms.items():
                d1 = pref * (a * TY + an * TYn)
                d2 = pref * (a * T2 + an * T2n)
                if delta1_win[0] <= d1 <= delta1_win[1] and delta2_win[0] <= d2 <= delta2_win[1]:
                    hits.append({
                        "weight_fn": F.__name__ if hasattr(F, "__name__") else "?",
                        "alpha": a_name, "alpha_val": a,
                        "alpha_n": an_name, "alpha_n_val": an,
                        "mu_UV_GeV": float(mu),
                        "delta1": d1, "delta2": d2,
                    })
    return hits


def scan_all(particles, atoms, mus, closure_windows):
    cat = weight_catalog()
    result = {}
    for fname, F in cat.items():
        # rename with fname for logging
        def _F(t, F=F): return F(t)
        _F.__name__ = fname
        hits = scan_F_joint(particles, _F, atoms, mus, closure_windows)
        result[fname] = hits
    return result


def triple_permutation_null(F_name: str, F, atoms, mus, closure_windows, n_perm=2000, seed=20260425):
    rng = random.Random(seed)
    names = list(FERMION_TRIPLES.keys())
    original = [FERMION_TRIPLES[n] for n in names]
    hits = 0
    for _ in range(n_perm):
        perm = list(original)
        rng.shuffle(perm)
        assignment = {names[i]: perm[i] for i in range(9)}
        parts = build_sm_particles(assignment)
        matches = scan_F_joint(parts, F, atoms, mus, closure_windows)
        if matches:
            hits += 1
    return {"n_perm": n_perm, "hits": hits, "hit_rate": hits / n_perm}


def scan_LL_flavor_universal(particles, atoms, mus, closure_windows):
    """LL-style: F(triple) = 1 (flavor-universal) — triple and α_n contribute the same way.
    Effectively: α·(Σ_p b_G^(p) ln(μ/m_p)) for charged fermions, + α_n·(Higgs + W) gauge self.
    Scan α, α_n over UGP atom library."""
    hits = []
    F1 = lambda t: 1.0
    F1.__name__ = "flavor_universal"
    return scan_F_joint(particles, F1, atoms, mus, closure_windows)


def main():
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    atoms = ugp_atom_library()

    # μ_UV grid: linear in log over physical range (above lightest particle, up to Planck)
    mus = list(np.logspace(math.log10(50.0), math.log10(1e19), 1001))

    real_assignment = {n: FERMION_TRIPLES[n] for n in FERMION_TRIPLES}
    real_particles = build_sm_particles(real_assignment)

    print(f"[PP] TIGHTENED JOINT WINDOWS:")
    print(f"  δ_1 ∈ {JOINT_DELTA1_WIN}  (width {JOINT_DELTA1_WIN[1]-JOINT_DELTA1_WIN[0]:.2e})")
    print(f"  δ_2 ∈ {JOINT_DELTA2_WIN}  (width {JOINT_DELTA2_WIN[1]-JOINT_DELTA2_WIN[0]:.2e})")
    print(f"[PP] atoms={len(atoms)}  mu_grid={len(mus)}")
    print()

    # (A) LL flavor-universal scan
    print("[PP] (A) LL flavor-universal scan ...")
    ll_joint = scan_LL_flavor_universal(real_particles, atoms, mus, (JOINT_DELTA1_WIN, JOINT_DELTA2_WIN))
    print(f"[PP]   LL flavor-universal: {len(ll_joint)} joint closures")
    if ll_joint:
        print(f"[PP]   sample: {ll_joint[0]}")

    # Also diagnostic: LL in sin²θ_W-only window
    ll_sin2 = scan_LL_flavor_universal(real_particles, atoms, mus, (SIN2_DELTA1_WIN, SIN2_DELTA2_WIN))
    print(f"[PP]   LL flavor-universal (sin²θ_W-only window): {len(ll_sin2)} closures")

    # (C) Number-theoretic F scan with JOINT windows
    print(f"\n[PP] (C) Number-theoretic triple-property F scan ...")
    cat = weight_catalog()
    closures_by_F = {}
    total_real_joint = 0
    for fname, F in cat.items():
        _F = (lambda t, F=F: F(t))
        _F.__name__ = fname
        hits = scan_F_joint(real_particles, _F, atoms, mus, (JOINT_DELTA1_WIN, JOINT_DELTA2_WIN))
        closures_by_F[fname] = hits
        total_real_joint += len(hits)
        if hits:
            print(f"[PP]   F={fname:20s}  joint_closures={len(hits)}  sample_μ={hits[0]['mu_UV_GeV']:.1f} α={hits[0]['alpha']} δ=({hits[0]['delta1']:.5f}, {hits[0]['delta2']:.5f})")
    if total_real_joint == 0:
        print(f"[PP]   (no number-theoretic F closes the tightened joint window at DL≤1)")

    # (D) Triple-permutation null for F's with joint closures
    print(f"\n[PP] (D) Triple-permutation nulls for F's with joint closures ...")
    nulls = {}
    for fname, F in cat.items():
        if len(closures_by_F.get(fname, [])) == 0:
            continue
        _F = (lambda t, F=F: F(t))
        _F.__name__ = fname
        t0 = time.time()
        nul = triple_permutation_null(fname, _F, atoms, mus, (JOINT_DELTA1_WIN, JOINT_DELTA2_WIN), n_perm=2000)
        nulls[fname] = nul
        print(f"[PP]   F={fname:20s}  null_hits={nul['hits']}/{nul['n_perm']}  rate={nul['hit_rate']:.4f}  [{time.time()-t0:.0f}s]")

    # Structural candidates: real closes AND null < 1%
    structural = []
    for fname, hits in closures_by_F.items():
        if not hits:
            continue
        null_rate = nulls.get(fname, {}).get("hit_rate", 1.0)
        if null_rate < 0.01:
            structural.append({
                "weight_fn": fname, "n_real_closures": len(hits),
                "null_rate": null_rate,
                "sample": hits[0],
            })

    # Verdict
    if structural:
        verdict = "STRUCTURAL_JOINT_CLOSURE_SIN2_MW"
    elif total_real_joint > 0:
        verdict = "DENSITY_DOMINATED_joint_closure_fails_null"
    elif ll_joint:
        verdict = "FLAVOR_UNIVERSAL_LL_CLOSES_joint_at_some_mu"
    else:
        verdict = "MAP_tightened_joint_test_insufficient"

    prediction_block = {
        "comp_id": "COMP-P01-PP",
        "spec_reference": "10_SPEC + 06_SPEC merger: tightened joint (sin²θ_W + m_W) closure test",
        "motivation": "R7-012 LL HARD IMPOSSIBILITY was on sin²θ_W-alone windows (negative δ_1); joint closure requires POSITIVE δ_1 and SMALLER |δ_2|, which is exactly what the flavor-universal threshold sign produces (though magnitude ~50× too large). Tightened test is ~100× smaller volume — discriminates density from structural.",
        "timestamp_utc": ts,
        "joint_windows": {"delta1": list(JOINT_DELTA1_WIN), "delta2": list(JOINT_DELTA2_WIN)},
        "volume_ratio_joint_over_sin2_alone": 1.0 / 110.9,
        "mu_UV_grid": {"n": len(mus), "range_GeV": [mus[0], mus[-1]]},
        "atom_library_size": len(atoms),
        "LL_flavor_universal_joint_closures": ll_joint,
        "LL_flavor_universal_sin2_only_closures": ll_sin2,
        "numtheoretic_closures_by_F": {k: {"n": len(v), "samples": v[:5]} for k, v in closures_by_F.items()},
        "total_real_joint_closures": total_real_joint,
        "triple_permutation_nulls": nulls,
        "structural_candidates_passing_null": structural,
    }
    pred_json = json.dumps(prediction_block, sort_keys=True, separators=(",", ":"), default=str)
    sha = hashlib.sha256(pred_json.encode("utf-8")).hexdigest()

    pdg_cmp = {
        "prediction_block_sha256": sha,
        "LL_flavor_universal_joint_hits": len(ll_joint),
        "LL_flavor_universal_sin2only_hits": len(ll_sin2),
        "total_real_joint_closures": total_real_joint,
        "n_structural_candidates": len(structural),
        "verdict": verdict,
        "joint_window_delta1": list(JOINT_DELTA1_WIN),
        "joint_window_delta2": list(JOINT_DELTA2_WIN),
    }

    return {
        "prediction_block_precomparison": prediction_block,
        "sha256_prediction_block": sha,
        "pdg_comparison": pdg_cmp,
    }


if __name__ == "__main__":
    out = main()
    path = "comp_p01_PP_joint_sin2thW_mW_closure.json"
    with open(path, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print()
    print(json.dumps(out["pdg_comparison"], indent=2, default=str))
    print(f"Written: {path}")
