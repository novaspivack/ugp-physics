#!/usr/bin/env python3
"""
COMP-P01-K (null)  —  permutation null for the UGP structural-integer × keV search.

Motivation: the search in comp_p01_K_charged_lepton_integer_search.py returned
"<10 ppm hits" for every charged-lepton target.  This is prima facie suspicious:
with 21 basis atoms and coefficient range ±20, the two-atom linear search
considers ~720 000 candidates per target, and the product-ratio search with
coef ≤ 500 considers ~4.6 million candidates.  Even random numbers in the same
magnitude range will admit "<10 ppm hits" by sheer combinatorics.

This script measures the false-hit rate explicitly.  For each real lepton
target, we draw 500 random targets from a log-uniform distribution spanning
roughly the same magnitude, run the identical search, and report the
distribution of best-achievable ppm.  We also impose a description-length
penalty: only hits with descr_len ≤ L_MAX count as "structural".

Only hits that are BOTH (a) in the few-ppm class AND (b) of genuinely small
description length (≤ ~6 elementary atoms) count as non-trivial.  We report the
electron case as the reference: 73 × δ = 511 has descr_len ≈ 3 (two atoms +
coefficient 73), and we compare the μ, τ best hits on the same footing.

Output: comp_p01_K_null_test.json
"""
from __future__ import annotations

import datetime as _dt
import hashlib as _hl
import json
import math
import random
import sys
from pathlib import Path

# reuse basis from the main search
import comp_p01_K_charged_lepton_integer_search as K


def best_hit(target: float, descr_max: int) -> dict:
    """Run the identical search under a description-length cap and return the
    single best hit (lowest ppm among hits with descr_len ≤ descr_max)."""
    candidates: list[dict] = []
    candidates += K.search_single(target, "t", max_n=100)
    candidates += K.search_two_linear(target, "t", C=20)
    candidates += K.search_product_ratio(target, "t")
    capped = [h for h in candidates if h["descr_len"] <= descr_max]
    if not capped:
        return {"ppm": 1e30, "formula": None, "descr_len": None}
    best = min(capped, key=lambda h: h["ppm"])
    return best


def null_distribution(center: float, n_trials: int, descr_max: int,
                      width_decades: float = 0.3, rng=None) -> list[float]:
    if rng is None:
        rng = random.Random(20260417)
    ppms = []
    log_c = math.log10(center)
    for _ in range(n_trials):
        log_t = log_c + rng.uniform(-width_decades, width_decades)
        t = 10.0 ** log_t
        h = best_hit(t, descr_max)
        ppms.append(h["ppm"])
    return ppms


def main() -> int:
    random.seed(20260417)
    rng = random.Random(20260417)

    # Cap description length so that only genuinely small formulas qualify.
    # The electron reference (73·δ, i.e. b₁·δ) has descr_len = 74 under the
    # "single_atom" scoring (because coef=73 contributes 73) but descr_len = 2
    # under a multiplicative scoring (just two atoms).  To be fair we compare
    # each target to its own null at the SAME descr_max cap.
    #
    # We use two caps:
    #   L1 = 10   (very tight: coef·atom with |coef| ≤ ~10, or 2-atom linear with small coefs)
    #   L2 = 20   (moderate: corresponds to 2-atom linear with coefs of order 10)
    DESCR_CAPS = [10, 20]

    TARGETS = K.TARGETS
    report = {
        "experiment_id": "COMP-P01-K-null",
        "question":      "Are the <10 ppm hits in COMP-P01-K structural, or do they arise from sheer combinatorial density of the search space?",
        "method":         "For each real charged-lepton target, draw 500 random targets from log-uniform(center ± 0.3 dex) and run the identical search with a description-length cap. Report the distribution of best ppm attained under the null.",
        "n_trials_per_target": 500,
        "descr_caps":     DESCR_CAPS,
        "real_targets":   {k: float(v) for k, v in TARGETS.items()},
        "results": {},
    }

    for name, tgt in TARGETS.items():
        print(f"[null] {name}  target={tgt:.6f}")
        per_cap = {}
        for cap in DESCR_CAPS:
            real_best = best_hit(tgt, cap)
            null_ppms = null_distribution(tgt, n_trials=500, descr_max=cap, rng=random.Random(hash(name) & 0xffffffff))
            null_ppms_sorted = sorted(null_ppms)
            # rank of real best among null
            rank = sum(1 for p in null_ppms if p <= real_best["ppm"])
            p_value = (rank + 1) / (len(null_ppms) + 1)
            per_cap[f"descr_cap_{cap}"] = {
                "real_best_ppm":     real_best["ppm"],
                "real_best_formula": real_best.get("formula"),
                "real_descr_len":    real_best.get("descr_len"),
                "null_ppm_p05":      null_ppms_sorted[int(0.05 * len(null_ppms))],
                "null_ppm_p25":      null_ppms_sorted[int(0.25 * len(null_ppms))],
                "null_ppm_median":   null_ppms_sorted[len(null_ppms) // 2],
                "null_ppm_p75":      null_ppms_sorted[int(0.75 * len(null_ppms))],
                "p_value":           p_value,
                "fraction_null_beating_real": sum(1 for p in null_ppms if p < real_best["ppm"]) / len(null_ppms),
            }
            print(f"   cap={cap:2d}  real_ppm={real_best['ppm']:10.3f}  null_med={per_cap[f'descr_cap_{cap}']['null_ppm_median']:10.3f}  p={p_value:.4f}  [{real_best.get('formula')}]")
        report["results"][name] = per_cap

    # Global verdict: is any target a statistically non-trivial hit?
    interpretations = {}
    for name in TARGETS:
        pc = report["results"][name]
        # We require at least one cap where p < 0.05
        best_p = min(pc[c]["p_value"] for c in pc)
        if best_p < 0.01:
            lab = "STRUCTURALLY SIGNIFICANT  (p<0.01 under null)"
        elif best_p < 0.05:
            lab = "MARGINALLY SIGNIFICANT    (0.01 ≤ p < 0.05)"
        elif best_p < 0.2:
            lab = "WEAK                       (0.05 ≤ p < 0.2)"
        else:
            lab = "NOT STRUCTURAL             (p ≥ 0.2; explained by combinatorial density)"
        interpretations[name] = {"best_p": best_p, "label": lab}
    report["interpretations"] = interpretations
    report["timestamp_utc"] = _dt.datetime.utcnow().isoformat(timespec="seconds")

    out_path = Path(__file__).with_suffix(".json")
    out_path.write_text(json.dumps(report, indent=2))
    sha = _hl.sha256(out_path.read_bytes()).hexdigest()
    print(f"\n[write] {out_path.name}")
    print(f"[sha]   {sha}")

    print("\n====  NULL-CALIBRATED VERDICTS  ====")
    for name, v in interpretations.items():
        print(f"  {name:18s}  best_p = {v['best_p']:.4f}   →  {v['label']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
