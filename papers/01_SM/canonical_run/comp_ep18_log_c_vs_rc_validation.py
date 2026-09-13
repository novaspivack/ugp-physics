#!/usr/bin/env python3
"""
comp_ep18_log_c_vs_rc_validation: canonical triple c-component vs reflexive closure (RC).

Reproduces HANDOFF_SPEC.md Task 3.1 headline statistics using P01 Table 12 triples
and the PDG closure dataset (`ep18_particle_closure_dataset.py` — mirrored from
the closure handoff package).

Outputs JSON under this directory for archival (sha256-friendly).

Usage (from repo root):

    python3 papers/01_SM/canonical_run/comp_ep18_log_c_vs_rc_validation.py
    python3 papers/01_SM/canonical_run/comp_ep18_log_c_vs_rc_validation.py --json-out papers/01_SM/canonical_run/comp_ep18_validation.json

Composite triple rules tested (Task 3.2 robustness battery):

  heaviest   — c of heaviest-mass constituent (baseline / handoff heuristic)
  lightest   — c of lightest-mass constituent (opposite extreme)
  max_c      — max |c| among constituents (deepest Mersenne ladder)
  geom_mean  — geometric mean of |c| values across all constituents
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

_CANONICAL_RUN_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_CANONICAL_RUN_DIR))

from ep18_particle_closure_dataset import (  # noqa: E402
    PARTICLE_DATA,
    TRIPLES,
    QUARK_MASS_GeV,
    LEPTON_MASS_GeV,
    compute_RC,
)

try:
    from scipy import stats
except ImportError as e:  # pragma: no cover
    raise RuntimeError("scipy is required: pip install scipy") from e


# ---------------------------------------------------------------------------
# Composite triple rules
# ---------------------------------------------------------------------------

def _constituent_c_values(name: str) -> List[float]:
    """
    Return the |c| values for each named constituent of `name`.
    Returns empty list if any constituent has no triple or c <= 0.
    """
    if name not in PARTICLE_DATA:
        return []
    consts = PARTICLE_DATA[name]["constituents"]
    if len(consts) == 1 and consts[0] == name:
        # Elementary — return own c
        if name in TRIPLES:
            c = TRIPLES[name][2]
            return [abs(c)] if c != -1 else []
        return []
    vals: List[float] = []
    for q in consts:
        q_clean = q.replace("_bar", "")
        if q_clean in TRIPLES:
            c = TRIPLES[q_clean][2]
            if c == -1:
                return []   # top quark constituent: exclude whole particle
            vals.append(abs(float(c)))
        else:
            return []       # unknown constituent triple: exclude
    return vals


def _constituent_mass(q: str) -> float:
    q_clean = q.replace("_bar", "")
    m = QUARK_MASS_GeV.get(q_clean) or LEPTON_MASS_GeV.get(q_clean) or 0.0
    return m


COMPOSITE_RULES: Dict[str, Any] = {
    "heaviest": None,   # filled dynamically below — mirrors handoff logic exactly
    "lightest": None,
    "max_c": None,
    "geom_mean": None,
}


def _c_for_rule(name: str, rule: str) -> Optional[float]:
    """Return the |c| value for `name` under the given composite rule."""
    if name not in PARTICLE_DATA:
        return None
    consts = PARTICLE_DATA[name]["constituents"]

    # Elementary particle: use own triple directly
    if len(consts) == 1 and consts[0] == name:
        if name not in TRIPLES:
            return None
        c = TRIPLES[name][2]
        return abs(float(c)) if c != -1 else None

    # Composite: apply rule
    c_vals = _constituent_c_values(name)
    if not c_vals:
        return None

    if rule == "heaviest":
        # Heaviest-mass constituent (mirrors handoff heuristic)
        best_q, best_m = None, -1.0
        for q in consts:
            m = _constituent_mass(q)
            if m > best_m:
                best_m, best_q = m, q.replace("_bar", "")
        if best_q is None or best_q not in TRIPLES:
            return None
        c = TRIPLES[best_q][2]
        return abs(float(c)) if c != -1 else None

    elif rule == "lightest":
        # Lightest-mass constituent (opposite extreme)
        best_q, best_m = None, float("inf")
        for q in consts:
            m = _constituent_mass(q)
            if m < best_m:
                best_m, best_q = m, q.replace("_bar", "")
        if best_q is None or best_q not in TRIPLES:
            return None
        c = TRIPLES[best_q][2]
        return abs(float(c)) if c != -1 else None

    elif rule == "max_c":
        # Maximum |c| among constituents (deepest Mersenne ladder in the hadron)
        if not c_vals:
            return None
        return max(c_vals)

    elif rule == "geom_mean":
        # Geometric mean of |c| values
        if not c_vals:
            return None
        return float(np.exp(np.mean(np.log(c_vals))))

    else:
        raise ValueError(f"Unknown rule: {rule!r}")


# ---------------------------------------------------------------------------
# Core data collection: build one row per particle, one log_c column per rule
# ---------------------------------------------------------------------------

def _collect_rows() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for name, data in PARTICLE_DATA.items():
        rc = compute_RC(name)
        if rc is None:
            continue

        # Compute log_c for each rule
        log_c_by_rule: Dict[str, Optional[float]] = {}
        for rule in COMPOSITE_RULES:
            c_raw = _c_for_rule(name, rule)
            if c_raw is None or c_raw <= 0:
                log_c_by_rule[rule] = None
            else:
                log_c_by_rule[rule] = float(np.log10(c_raw))

        # A row is valid if at least the baseline rule has a value
        if log_c_by_rule["heaviest"] is None:
            continue

        is_composite = len(data["constituents"]) > 1 or (
            len(data["constituents"]) == 1 and data["constituents"][0] != name
        )
        rows.append(
            {
                "name": name,
                "RC": float(rc),
                "log_c_by_rule": log_c_by_rule,
                "is_composite": bool(is_composite),
                "M": float(data["M"]),
            }
        )
    return rows


# ---------------------------------------------------------------------------
# Statistics helpers
# ---------------------------------------------------------------------------

def _pearson(xs: np.ndarray, ys: np.ndarray) -> Tuple[float, float, int]:
    mask = np.isfinite(xs) & np.isfinite(ys)
    xs, ys = xs[mask], ys[mask]
    if len(xs) < 3:
        return (float("nan"), float("nan"), len(xs))
    r, p = stats.pearsonr(xs, ys)
    return (float(r), float(p), len(xs))


def _fisher_ci_pearson(r: float, n: int, z_alpha: float = 1.96) -> Tuple[float, float]:
    if n <= 3 or not np.isfinite(r) or abs(r) >= 1.0:
        return (float("nan"), float("nan"))
    z = np.arctanh(r)
    se = 1.0 / np.sqrt(n - 3)
    lo = np.tanh(z - z_alpha * se)
    hi = np.tanh(z + z_alpha * se)
    return (float(lo), float(hi))


def _rule_stats(rows: List[Dict[str, Any]], rule: str, composites_only: bool) -> Dict[str, Any]:
    sub = [r for r in rows if r["is_composite"]] if composites_only else rows
    log_c_arr = np.array(
        [r["log_c_by_rule"].get(rule) if r["log_c_by_rule"].get(rule) is not None else float("nan")
         for r in sub],
        dtype=float,
    )
    rc_arr = np.array([r["RC"] for r in sub], dtype=float)
    r, p, n = _pearson(log_c_arr, rc_arr)
    lo, hi = _fisher_ci_pearson(r, n)
    outcome = "A" if abs(r) >= 0.90 else ("B" if abs(r) >= 0.70 else "C")
    return {"r": r, "p": p, "n": n, "ci95": [lo, hi], "outcome": outcome}


SUBSAMPLES_SPEC = {
    "octet_ground_baryons": ["p", "n", "Lambda", "Sigma+", "Sigma-", "Xi0", "Xi-"],
    "pseudoscalar_mesons": ["pi+", "pi0", "K+", "K0_S", "K0_L", "eta", "eta_prime"],
    "vector_mesons": ["rho", "omega", "phi", "K*(892)"],
}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description="COMP-EP18 log10(|c|) vs RC — 4-rule robustness")
    ap.add_argument(
        "--json-out",
        type=Path,
        default=_CANONICAL_RUN_DIR / "comp_ep18_validation.json",
        help="Write full result payload for archival",
    )
    args = ap.parse_args()

    rows = _collect_rows()

    # ---- Full-spectrum and composites-only for every rule ----
    rule_results: Dict[str, Any] = {}
    for rule in COMPOSITE_RULES:
        rule_results[rule] = {
            "full_spectrum": _rule_stats(rows, rule, composites_only=False),
            "composites_only": _rule_stats(rows, rule, composites_only=True),
        }

    # ---- Subsample stress test (baseline rule only, composites only) ----
    subsamples: Dict[str, Any] = {}
    for label, plist in SUBSAMPLES_SPEC.items():
        name_set = set(plist)
        sub_rows = [r for r in rows if r["name"] in name_set and r["is_composite"]]
        log_c_arr = np.array(
            [r["log_c_by_rule"]["heaviest"] if r["log_c_by_rule"]["heaviest"] is not None else float("nan")
             for r in sub_rows],
            dtype=float,
        )
        rc_arr = np.array([r["RC"] for r in sub_rows], dtype=float)
        r_s, p_s, n_s = _pearson(log_c_arr, rc_arr)
        lo, hi = _fisher_ci_pearson(r_s, n_s)
        subsamples[label] = {"r": r_s, "p": p_s, "n": n_s, "ci95": [lo, hi]}

    # ---- Robustness summary ----
    baseline_r = rule_results["heaviest"]["composites_only"]["r"]
    r_spread = max(abs(rule_results[rl]["composites_only"]["r"]) for rl in COMPOSITE_RULES) - \
               min(abs(rule_results[rl]["composites_only"]["r"]) for rl in COMPOSITE_RULES)
    all_outcome_A = all(
        rule_results[rl]["composites_only"]["outcome"] == "A" for rl in COMPOSITE_RULES
    )

    # ---- Build payload ----
    payload: Dict[str, Any] = {
        "comp_id": "COMP-EP18",
        "triple_source": "P01_Table_12_values_in_ep18_particle_closure_dataset",
        "composite_rules_tested": list(COMPOSITE_RULES.keys()),
        "exclusions": [
            "Top quark: c=-1, excluded from log_c across all rules",
            "W,Z,H: no fermion-canonical triple — excluded",
        ],
        "rule_results": rule_results,
        "subsamples_composites_only_baseline_rule": subsamples,
        "robustness_summary": {
            "baseline_rule": "heaviest",
            "baseline_composites_r": baseline_r,
            "spread_in_abs_r_composites_across_rules": r_spread,
            "all_rules_outcome_A": all_outcome_A,
        },
        "lean_note": (
            "ugp-lean certifies canonical fundamental-fermion orbit triples; "
            "composite triple assignment remains heuristic until a proved rule lands."
        ),
    }

    text_wo_hash = json.dumps(payload, sort_keys=True, indent=2)
    h = hashlib.sha256(text_wo_hash.encode("utf-8")).hexdigest()
    payload["sha256_canonical_json_without_this_field"] = h
    text = json.dumps(payload, sort_keys=True, indent=2)

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(text + "\n", encoding="utf-8")

    # ---- Console output ----
    print("COMP-EP18  log10(|c|) vs RC — 4-rule composite robustness battery")
    print()
    print(f"  {'rule':12s}  {'r (composites)':>16s}  {'p':>10s}  {'n':>4s}  outcome  95% CI")
    print("  " + "-" * 72)
    for rule in COMPOSITE_RULES:
        s = rule_results[rule]["composites_only"]
        ci = s["ci95"]
        print(f"  {rule:12s}  {s['r']:>+16.4f}  {s['p']:>10.2e}  {s['n']:>4d}  "
              f"  {s['outcome']}    [{ci[0]:+.4f}, {ci[1]:+.4f}]")

    print()
    print(f"  Spread in |r| across rules (composites): {r_spread:.4f}")
    print(f"  All rules ≥ 0.90 (Outcome A):            {all_outcome_A}")
    print()
    print(f"  Wrote: {args.json_out}")
    print(f"  sha256: {h}")


if __name__ == "__main__":
    main()
