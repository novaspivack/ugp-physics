#!/usr/bin/env python3
"""
COMP-P01-SS: 04_SPEC Phase 1 gate check — single R_g UGP-atom match (OP(i)-B)

Phase 1 gate (04_SPEC §5): "Can we identify any single R_g ratio that matches
a low-complexity UGP-atom expression at ≤ 1%?"

Prior work context:
  - SC-BB: 16 hypotheses + 32-atom brute-force DL ≤ 2, best ~10% for best fermion
  - 08_SPEC FF3: 59-atom library DL ≤ 5 with disciplined null, best 22% across 9 fermions
  - The 1% Phase 1 gate is strictly tighter than both prior MAP results

Expanded atom library this comp:
  - 59 atoms from 09_SPEC/HH library (UGP Lean-certified + cyclotomic + Fibonacci + Lucas)
  - PLUS 04_SPEC §3(i)-B NEW candidates:
      * Gauge-group Casimirs: C₂(SU(3)) = 4/3 (quarks), C₂(SU(2)) = 3/4 (leptons)
      * Braid-Atlas composite invariants: log(|a|·|b|·|c|), |c|^(1/gen), strand-count proxy
      * Cascade evolution multipliers: gen-indexed structural weights

Test:
  (A) For each R_g target, find the best DL=1 (single atom) match; report
      minimum fractional error |atom − log(R_g)| / log(R_g).
  (B) For each R_g target, find the best DL=2 (log atom product = sum of logs)
      match; report minimum fractional error.
  (C) Null discipline: randomize which fermion carries which R_g (permute
      R_g assignments across fermions); recompute best atom match;
      measure hit rate in 2000 trials.

Gate:
  - PASS (Phase 1 success): ≥ 1 R_g matches at ≤ 1% with null hit rate < 1%.
  - MAP: all R_g miss at 1%; or matches are density-dominated.
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

# R_g targets from 04_SPEC §3(i)-B (log₁₀ space for readability, but we will
# use natural log for the UGP-atom compositions because log atoms are natural)
R_g_TARGETS = {
    "up":      2.72,
    "down":    4.68,
    "strange": 229.3,
    "muon":    242.0,
    "charm":   838.2,
    "tau":     14252.0,
    "bottom":  22078.0,
    "top":     142518.0,
}

LOG_R_g = {k: math.log(v) for k, v in R_g_TARGETS.items()}

# Fermion metadata
FERMION_META = {
    "up":      {"gen": 1, "type": "u"},
    "down":    {"gen": 1, "type": "d"},
    "strange": {"gen": 2, "type": "d"},
    "muon":    {"gen": 2, "type": "e"},
    "charm":   {"gen": 2, "type": "u"},
    "tau":     {"gen": 3, "type": "e"},
    "bottom":  {"gen": 3, "type": "d"},
    "top":     {"gen": 3, "type": "u"},
}

PHI = (1.0 + math.sqrt(5.0)) / 2.0


def ugp_atom_library_extended() -> Dict[str, float]:
    """Extended atom library including 04_SPEC §3(i)-B NEW candidates."""
    atoms: Dict[str, float] = {}
    # Standard UGP atoms (signs + golden field + cyclotomic)
    small_integers = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
        "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
    }
    for k, v in small_integers.items():
        atoms[k] = float(v)
    # log integers - natural for R_g
    for k, v in small_integers.items():
        atoms[f"log_{k}"] = math.log(v)
    # Fractions
    for numer in (1, 2, 3, 4, 5):
        for denom in (2, 3, 4, 5, 6, 7, 8, 12):
            if numer < denom:
                atoms[f"frac_{numer}_{denom}"] = numer / denom
    # Golden field
    atoms.update({
        "phi": PHI, "phi2": PHI ** 2, "phi3": PHI ** 3, "phi4": PHI ** 4, "phi5": PHI ** 5,
        "phi6": PHI ** 6, "phi7": PHI ** 7, "phi8": PHI ** 8,
        "inv_phi": 1 / PHI, "inv_phi2": 1 / PHI ** 2, "inv_phi3": 1 / PHI ** 3,
        "log_phi": math.log(PHI), "log_phi2": math.log(PHI ** 2),
        "log_phi3": math.log(PHI ** 3), "log_phi4": math.log(PHI ** 4),
        "log_phi5": math.log(PHI ** 5), "log_phi6": math.log(PHI ** 6),
        "log_phi7": math.log(PHI ** 7), "log_phi8": math.log(PHI ** 8),
        "log_phi10": math.log(PHI ** 10), "log_phi12": math.log(PHI ** 12),
        "sqrt5": math.sqrt(5.0), "log_sqrt5": math.log(math.sqrt(5.0)),
    })
    # UGP Lean-certified coefficients
    atoms.update({
        "k_gen": PHI * math.cos(math.pi / 10),
        "k_gen2": -PHI / 2,
        "k_L2": 7 / 512,
        "k_mu_a": 1 / 8, "k_mu_b": -3 / 2, "k_mu_c": 4 / 3,
        "k_M": -PHI / 2 + (7 / 512) / 4,
        "log_k_gen": math.log(PHI * math.cos(math.pi / 10)),
    })
    # Cyclotomic / D5
    for k in (5, 10):
        atoms[f"cos_pi_{k}"] = math.cos(math.pi / k)
        atoms[f"log_cos_pi_{k}_plus_phi"] = math.log(PHI + math.cos(math.pi / k))
    # Fibonacci log ratios
    fib = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144]
    for i in range(2, 10):
        atoms[f"log_fib_{i}"] = math.log(fib[i])
    # Lucas log ratios
    luc = [2, 1, 3, 4, 7, 11, 18, 29, 47, 76, 123]
    for i in range(2, 10):
        atoms[f"log_luc_{i}"] = math.log(luc[i])
    # Powers of e for reference
    for k in range(1, 13):
        atoms[f"const_{k}"] = float(k)     # pure log scale
    # 04_SPEC §3(i)-B NEW candidates:
    # Gauge-group Casimirs
    atoms.update({
        "C2_SU3_fund": 4 / 3,       # fundamental of SU(3)
        "C2_SU2_fund": 3 / 4,       # fundamental of SU(2)
        "C2_SU3_adj": 3.0,          # adjoint of SU(3)
        "C2_SU2_adj": 2.0,          # adjoint of SU(2)
    })
    # Braid-Atlas composite invariants (from fermion triples)
    fermion_triples = {
        "up": (5, 9, 275), "charm": (5, 275, 65535), "top": (76, 337920, -1),
        "down": (9, 5, 42), "strange": (9, 186, 1023), "bottom": (5, 8191, 65535),
        "muon": (9, 42, 1023), "tau": (5, 275, -65535),
    }
    # log(|a|·|b|·|c|) per fermion (generation-3 composites)
    atoms.update({
        "log_abc_top":    math.log(abs(76 * 337920 * 1)),
        "log_abc_tau":    math.log(abs(5 * 275 * 65535)),
        "log_abc_bottom": math.log(abs(5 * 8191 * 65535)),
    })
    # PDG-like structural scaling factors
    atoms.update({
        "log_2_pow_16": 16 * math.log(2),    # log(2^16) — Mersenne scale of c=65535
        "log_2_pow_13": 13 * math.log(2),    # log(2^13) — bottom's b
        "log_2_pow_10": 10 * math.log(2),    # log(2^10) — muon's c
    })
    return atoms


def best_match(target: float, atoms: Dict[str, float], dl: int = 1) -> Tuple[str, float, float]:
    """Find best atom expression at given DL matching target. Return (name, value, frac_err)."""
    best_name = None
    best_val = None
    best_err = math.inf
    atom_items = list(atoms.items())

    if dl == 1:
        for name, val in atom_items:
            err = abs(val - target) / max(abs(target), 1e-30)
            if err < best_err:
                best_err = err
                best_name = name
                best_val = val
    elif dl == 2:
        # DL=2: sum of two atoms (since we're in log space, product → sum)
        for i, (n1, v1) in enumerate(atom_items):
            for n2, v2 in atom_items[i:]:
                s = v1 + v2
                err = abs(s - target) / max(abs(target), 1e-30)
                if err < best_err:
                    best_err = err
                    best_name = f"{n1} + {n2}"
                    best_val = s
    elif dl == 3:
        # DL=3: sum of three atoms
        for i, (n1, v1) in enumerate(atom_items):
            for j, (n2, v2) in enumerate(atom_items[i:], start=i):
                for n3, v3 in atom_items[j:]:
                    s = v1 + v2 + v3
                    err = abs(s - target) / max(abs(target), 1e-30)
                    if err < best_err:
                        best_err = err
                        best_name = f"{n1} + {n2} + {n3}"
                        best_val = s
    return best_name, best_val, best_err


def scan_all_fermions(atoms: Dict[str, float], dl: int) -> Dict[str, Dict]:
    out = {}
    for fermion_name, target in LOG_R_g.items():
        name, val, err = best_match(target, atoms, dl=dl)
        out[fermion_name] = {
            "target_log_R_g": target, "R_g_target": R_g_TARGETS[fermion_name],
            "best_expression": name,
            "best_value": val,
            "fractional_error": err,
            "matches_at_1pct": err <= 0.01,
            "matches_at_2pct": err <= 0.02,
            "matches_at_5pct": err <= 0.05,
            "matches_at_10pct": err <= 0.10,
        }
    return out


def null_permutation(atoms: Dict[str, float], dl: int, n_trials: int, seed: int = 20260427) -> Dict:
    """Null: permute fermion → R_g assignments; count how often the random
    permutation has at least one match at ≤ 1%."""
    rng = random.Random(seed)
    targets = list(LOG_R_g.values())
    hits_1pct = 0
    hits_2pct = 0
    for _ in range(n_trials):
        perm = list(targets)
        rng.shuffle(perm)
        # For each permuted target, find best atom match
        any_1pct = False
        any_2pct = False
        for tgt in perm:
            _, _, err = best_match(tgt, atoms, dl=dl)
            if err <= 0.01:
                any_1pct = True
            if err <= 0.02:
                any_2pct = True
            if any_1pct and any_2pct:
                break
        if any_1pct:
            hits_1pct += 1
        if any_2pct:
            hits_2pct += 1
    return {
        "n_trials": n_trials,
        "any_1pct_hit_rate": hits_1pct / n_trials,
        "any_2pct_hit_rate": hits_2pct / n_trials,
    }


def main():
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    atoms = ugp_atom_library_extended()

    print(f"[SS] Atom library: {len(atoms)} atoms")

    # DL=1 real scan
    print(f"[SS] DL=1 real scan per fermion ...")
    dl1 = scan_all_fermions(atoms, dl=1)
    for fermion, rec in dl1.items():
        flag = "✓" if rec["matches_at_1pct"] else ("~" if rec["matches_at_10pct"] else "✗")
        print(f"[SS]   DL=1 {fermion:10s} target={rec['target_log_R_g']:6.3f}  best={rec['best_value']:6.3f} ({rec['best_expression']}) err={rec['fractional_error']:.4g}  {flag}")

    # DL=2 real scan
    print(f"[SS] DL=2 real scan per fermion (this takes longer) ...")
    t0 = time.time()
    dl2 = scan_all_fermions(atoms, dl=2)
    print(f"[SS]   DL=2 scan done in {time.time()-t0:.1f}s")
    for fermion, rec in dl2.items():
        flag = "✓" if rec["matches_at_1pct"] else ("~" if rec["matches_at_10pct"] else "✗")
        print(f"[SS]   DL=2 {fermion:10s} err={rec['fractional_error']:.4g}  {flag}  best={rec['best_expression']}")

    # Null discipline
    print(f"[SS] Null (permutation) DL=1 × 2000 trials ...")
    null1 = null_permutation(atoms, dl=1, n_trials=2000)
    print(f"[SS]   null DL=1: any_1pct_hit_rate={null1['any_1pct_hit_rate']:.4f}  any_2pct={null1['any_2pct_hit_rate']:.4f}")

    print(f"[SS] Null DL=2 × 500 trials ...")
    t0 = time.time()
    null2 = null_permutation(atoms, dl=2, n_trials=500)
    print(f"[SS]   null DL=2 in {time.time()-t0:.1f}s: any_1pct_hit_rate={null2['any_1pct_hit_rate']:.4f}  any_2pct={null2['any_2pct_hit_rate']:.4f}")

    # Gate analysis
    any_real_1pct_match = any(r["matches_at_1pct"] for r in dl1.values()) or any(r["matches_at_1pct"] for r in dl2.values())
    null_disciplined_1pct = null1["any_1pct_hit_rate"] < 0.01 and null2["any_1pct_hit_rate"] < 0.01

    # Best single R_g match
    best_per_fermion = {
        f: min(dl1[f]["fractional_error"], dl2[f]["fractional_error"]) for f in dl1
    }
    worst_residual = max(best_per_fermion.values())
    median_residual = sorted(best_per_fermion.values())[len(best_per_fermion) // 2]

    if any_real_1pct_match and null_disciplined_1pct:
        verdict = "PASS_PhaseI_gate_structural_R_g_found"
    elif any_real_1pct_match and not null_disciplined_1pct:
        verdict = "DENSITY_DOMINATED_PhaseI_matches_fail_null"
    else:
        verdict = "MAP_PhaseI_gate_no_R_g_closes_at_1pct"

    prediction_block = {
        "comp_id": "COMP-P01-SS",
        "spec_reference": "04_SPEC Phase 1 gate — single R_g UGP-atom match at ≤ 1%",
        "timestamp_utc": ts,
        "R_g_targets": {k: {"value": R_g_TARGETS[k], "log": LOG_R_g[k], "gen": FERMION_META[k]["gen"], "type": FERMION_META[k]["type"]} for k in R_g_TARGETS},
        "atom_library_size": len(atoms),
        "DL1_real": dl1,
        "DL2_real": dl2,
        "best_residual_per_fermion_across_DL": best_per_fermion,
        "worst_residual_across_fermions": worst_residual,
        "median_residual_across_fermions": median_residual,
        "null_DL1": null1,
        "null_DL2": null2,
    }
    pred_json = json.dumps(prediction_block, sort_keys=True, separators=(",", ":"), default=str)
    sha = hashlib.sha256(pred_json.encode("utf-8")).hexdigest()

    pdg_cmp = {
        "prediction_block_sha256": sha,
        "any_R_g_matches_at_1pct_DL1_or_DL2": any_real_1pct_match,
        "best_residual_per_fermion": best_per_fermion,
        "worst_residual": worst_residual,
        "median_residual": median_residual,
        "null_1pct_hit_rate_DL1": null1["any_1pct_hit_rate"],
        "null_1pct_hit_rate_DL2": null2["any_1pct_hit_rate"],
        "null_disciplined_1pct": null_disciplined_1pct,
        "verdict": verdict,
    }

    return {"prediction_block_precomparison": prediction_block,
            "sha256_prediction_block": sha,
            "pdg_comparison": pdg_cmp}


if __name__ == "__main__":
    out = main()
    path = "comp_p01_SS_04spec_phase1_single_Rg.json"
    with open(path, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print()
    print(json.dumps(out["pdg_comparison"], indent=2, default=str))
    print(f"Written: {path}")
