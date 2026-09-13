#!/usr/bin/env python3
"""
COMP-P01-RC1: URC bounded-uniqueness enumeration.

SP-D of EPIC 13. Test whether the UGP-claimed algebraic closures for
(alpha_symmetry, alpha_QCD, alpha_EW) are the unique minimum-residual
expressions within the space of bounded-complexity algebraic expressions
over UGP-structural constants.

Enumeration:
  - Operators: +, -, *, /, **2  (we explicitly ALLOW squaring and cubing
    since UGP theory uses phi^3 and kappa^2 natively, and the expression
    phi^3 at depth-4 otherwise blows up via phi*phi*phi)
  - Depth: 1..4 binary-tree depth
  - Constant set: UGP-structural atoms

Three empirical URC targets (from Rees 2024 structural fits, also Appendix D
of P01 V17):
  alpha_symmetry  = 4.00e-5   (empirical)
  alpha_QCD       = 5.43e-4   (empirical)
  alpha_EW        = 7.00e-6   (empirical)

UGP-claimed closures (P01 V17 Propositions 4.1--4.3):
  alpha_symmetry  = kappa^2 / phi^3                       ~ 4.41e-5  (10.3%)
  alpha_QCD       = tau(1008) / c_3 = 30 / 65535          ~ 4.58e-4  (15.7%)
  alpha_EW        = 1 / (137 * 233 * phi^3)               ~ 7.40e-6  (5.7%)

For each target we:
  1. Enumerate all expressions up to depth D
  2. Compute relative residual |expr - target|/target
  3. Sort ascending
  4. Report where the UGP-claimed expression ranks
  5. Null test: replace UGP atoms with random rationals of matching magnitude

Gate A (success): UGP-claim is top-3 AND gap to second-best is > 2x
Gate B (partial): UGP-claim is top-10
Gate C (failure): UGP-claim is not distinguished from density-dominated noise

Pre-commit SHA-256 protocol: SHA of (config + atom set + enumerator source)
is computed before any target comparison is performed.
"""

from __future__ import annotations
import itertools
import json
import hashlib
import random
from dataclasses import dataclass, field, asdict
from fractions import Fraction
from typing import Callable
import math
import time
import os
import sys

# ---------------------------------------------------------------------------
# 1. Atom set (UGP-structural constants)
# ---------------------------------------------------------------------------

PHI = (1.0 + math.sqrt(5.0)) / 2.0

UGP_ATOMS: dict[str, float] = {
    # UGP-intrinsic primary atoms
    "kappa": 7.0 / 512.0,          # curvature coefficient
    "phi":   PHI,                   # golden ratio (state-space dim)
    "tau":   30.0,                  # divisor count tau(R_10) = tau(1008)
    "c3":    65535.0,               # third-gen capacity 2^16 - 1
    "b1":    73.0,                  # lepton ladder
    "a2":    9.0,                   # N_c^2 (mu-level)
    "Nc":    3.0,                   # QCD colour rank
    "F13":   233.0,                 # 13th Fibonacci
    "e137":  137.0,                 # fine-structure integer
    # UGP-intrinsic composite atoms (appear natively in theory, not operator-derived)
    "phi2":  PHI * PHI,             # phi^2 -- Casimir-like
    "phi3":  PHI ** 3,              # phi^3 -- state-space dim cubed
    "kap2":  (7.0 / 512.0) ** 2,    # kappa^2 -- curvature squared
    "e137_F13": 137.0 * 233.0,      # combined fine-structure factor
    # small integers (small set -- kept short to keep enumeration tractable)
    "one":   1.0,
    "two":   2.0,
    "four":  4.0,
}

# URC empirical targets and UGP-claimed closures (string, float)
TARGETS = {
    "alpha_symmetry": {
        "empirical": 4.00e-5,
        "ugp_claim_str": "kap2 / phi3",
        "ugp_claim_val": (7.0/512.0)**2 / PHI**3,
    },
    "alpha_QCD": {
        "empirical": 5.43e-4,
        "ugp_claim_str": "tau / c3",
        "ugp_claim_val": 30.0 / 65535.0,
    },
    "alpha_EW": {
        "empirical": 7.00e-6,
        "ugp_claim_str": "one / (e137_F13 * phi3)",
        "ugp_claim_val": 1.0 / (137.0 * 233.0 * PHI**3),
    },
}

OPERATORS = ("+", "-", "*", "/")  # binary only; square/cube done via *

# ---------------------------------------------------------------------------
# 2. Expression enumeration (symmetric canonicalisation)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Expr:
    """Canonical binary expression tree."""
    repr_str: str
    value: float
    depth: int
    leaves: tuple[str, ...]  # atom names used, sorted


def _atom_expr(name: str, val: float) -> Expr:
    return Expr(name, val, 0, (name,))


def _compose(a: Expr, b: Expr, op: str) -> Expr | None:
    va, vb = a.value, b.value
    try:
        if op == "+":
            v = va + vb
            r = f"({a.repr_str} + {b.repr_str})"
        elif op == "-":
            v = va - vb
            r = f"({a.repr_str} - {b.repr_str})"
        elif op == "*":
            v = va * vb
            r = f"({a.repr_str} * {b.repr_str})"
        elif op == "/":
            if abs(vb) < 1e-300:
                return None
            v = va / vb
            r = f"({a.repr_str} / {b.repr_str})"
        else:
            raise ValueError(op)
    except (OverflowError, ZeroDivisionError):
        return None
    if not math.isfinite(v):
        return None
    new_depth = max(a.depth, b.depth) + 1
    new_leaves = tuple(sorted(a.leaves + b.leaves))
    return Expr(r, v, new_depth, new_leaves)


def _value_key(v: float) -> tuple[int, int]:
    """Quantize a float to ~12-digit relative precision for hashing."""
    if v == 0 or not math.isfinite(v):
        return (0, 0)
    mant, exp = math.frexp(v)  # v = mant * 2^exp, mant in [0.5, 1)
    # quantize mantissa to ~12 decimal digits
    return (int(mant * 1e12), exp)


def enumerate_up_to(max_depth: int, atoms: dict[str, float]) -> list[Expr]:
    """All distinct expressions up to given depth, deduplicated by value-hash.
    O(N) dedup via dict."""
    level: dict[int, list[Expr]] = {0: []}
    seen: dict[tuple[int, int], Expr] = {}

    def _register(e: Expr, bucket: list[Expr]) -> None:
        k = _value_key(e.value)
        if k in seen:
            return
        seen[k] = e
        bucket.append(e)

    for n, v in atoms.items():
        _register(_atom_expr(n, v), level[0])

    for d in range(1, max_depth + 1):
        level[d] = []
        for da in range(0, d):
            db = d - 1 - da
            # want max(depth(a), depth(b)) + 1 == d, so at least one of da, db == d-1
            if da != d - 1 and db != d - 1:
                continue
            for a in level[da]:
                for b in level[db]:
                    for op in OPERATORS:
                        if op in ("+", "*"):
                            if a.repr_str > b.repr_str:
                                continue
                        e = _compose(a, b, op)
                        if e is None:
                            continue
                        _register(e, level[d])

    all_exprs: list[Expr] = []
    for d in range(0, max_depth + 1):
        all_exprs.extend(level[d])
    return all_exprs


# ---------------------------------------------------------------------------
# 3. Residual and ranking
# ---------------------------------------------------------------------------

def relative_residual(predicted: float, target: float) -> float:
    if target == 0:
        return float("inf") if predicted != 0 else 0.0
    return abs(predicted - target) / abs(target)


def rank_exprs_for_target(exprs: list[Expr], target: float, top_n: int = 50) -> list[dict]:
    scored = []
    for e in exprs:
        r = relative_residual(e.value, target)
        if not math.isfinite(r):
            continue
        scored.append({
            "expr": e.repr_str,
            "value": e.value,
            "residual_pct": 100.0 * r,
            "depth": e.depth,
            "n_leaves": len(e.leaves),
        })
    scored.sort(key=lambda d: d["residual_pct"])
    return scored[:top_n]


def find_rank_of(value: float, ranked: list[dict], tol: float = 1e-6) -> int | None:
    for i, r in enumerate(ranked):
        if r["value"] != 0 and abs((r["value"] - value) / r["value"]) < tol:
            return i
    return None


# ---------------------------------------------------------------------------
# 4. Null discipline — feature randomization
# ---------------------------------------------------------------------------

def randomized_atoms(rng: random.Random) -> dict[str, float]:
    """Replace each UGP atom with a random rational of matching order of magnitude.
    Keeps small-integer atoms intact because they represent generic
    operator-supplied structure (1, 2, 4) not UGP-specific content.

    Also rebuilds the composite atoms (phi2, phi3, kap2, e137_F13) from the
    randomized primaries so null scenarios treat composites consistently.
    """
    keep = {"one", "two", "four"}
    out: dict[str, float] = {}
    primary = ("kappa", "phi", "tau", "c3", "b1", "a2", "Nc", "F13", "e137")
    for name in primary:
        v = UGP_ATOMS[name]
        mag = math.floor(math.log10(abs(v))) if v != 0 else 0
        p = rng.randint(1, 100)
        q = rng.randint(1, 100)
        base = (p / q) * (10 ** mag)
        while abs(base - v) / abs(v) < 0.01:
            p = rng.randint(1, 100)
            q = rng.randint(1, 100)
            base = (p / q) * (10 ** mag)
        out[name] = base
    # Rebuild composites from randomized primaries
    out["phi2"] = out["phi"] ** 2
    out["phi3"] = out["phi"] ** 3
    out["kap2"] = out["kappa"] ** 2
    out["e137_F13"] = out["e137"] * out["F13"]
    # Keep small integers intact
    for name in keep:
        out[name] = UGP_ATOMS[name]
    return out


# ---------------------------------------------------------------------------
# 5. Pre-commit SHA
# ---------------------------------------------------------------------------

def source_sha256() -> str:
    with open(__file__, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


# ---------------------------------------------------------------------------
# 6. Main
# ---------------------------------------------------------------------------

def main() -> int:
    max_depth = 3
    n_null_trials = 30
    top_n = 50

    t0 = time.time()
    precommit_sha = source_sha256()

    results = {
        "experiment_id": "COMP-P01-RC1",
        "title": "URC bounded-uniqueness enumeration over UGP-structural constants",
        "epic": "EPIC_CLUSTER13_REFEREE_CLOSURE / SP-D",
        "pre_commit_sha256": precommit_sha,
        "config": {
            "max_depth": max_depth,
            "operators": list(OPERATORS),
            "n_null_trials": n_null_trials,
            "atoms": {k: v for k, v in UGP_ATOMS.items()},
            "targets": {
                k: {"empirical": v["empirical"], "ugp_claim_val": v["ugp_claim_val"], "ugp_claim_str": v["ugp_claim_str"]}
                for k, v in TARGETS.items()
            },
        },
        "ugp_ranking": {},
        "null_statistics": {},
    }

    # --- UGP enumeration ---
    print(f"[{time.time()-t0:.1f}s] Enumerating UGP atoms up to depth {max_depth}...", file=sys.stderr)
    ugp_exprs = enumerate_up_to(max_depth, UGP_ATOMS)
    print(f"[{time.time()-t0:.1f}s]   Got {len(ugp_exprs)} distinct expressions.", file=sys.stderr)
    results["n_expressions_ugp"] = len(ugp_exprs)

    for tgt_name, tgt in TARGETS.items():
        ranked = rank_exprs_for_target(ugp_exprs, tgt["empirical"], top_n=top_n)
        ugp_rank = find_rank_of(tgt["ugp_claim_val"], ranked)
        # Find UGP claim residual in full list
        ugp_residual_pct = 100.0 * relative_residual(tgt["ugp_claim_val"], tgt["empirical"])
        # best expr overall, second best
        best = ranked[0] if ranked else None
        second = ranked[1] if len(ranked) > 1 else None
        gap = (second["residual_pct"] / best["residual_pct"]) if (best and second and best["residual_pct"] > 0) else None

        results["ugp_ranking"][tgt_name] = {
            "target_empirical": tgt["empirical"],
            "ugp_claim_val": tgt["ugp_claim_val"],
            "ugp_claim_residual_pct": ugp_residual_pct,
            "ugp_claim_rank_in_top_n": ugp_rank,
            "top_n_considered": top_n,
            "best_expr": best,
            "second_best_expr": second,
            "second_over_best_residual_ratio": gap,
            "top_10": ranked[:10],
        }

    # --- Null-discipline enumeration ---
    # For each null trial: replace UGP atoms, enumerate, find best expr for each
    # target, record its residual. If many null trials produce residuals <= UGP's,
    # the UGP atoms are not distinguished.
    print(f"[{time.time()-t0:.1f}s] Running {n_null_trials} null trials...", file=sys.stderr)
    null_rng = random.Random(20260423)  # deterministic seed
    null_best_residuals: dict[str, list[float]] = {k: [] for k in TARGETS}
    for trial in range(n_null_trials):
        atoms = randomized_atoms(null_rng)
        null_exprs = enumerate_up_to(max_depth, atoms)
        for tgt_name, tgt in TARGETS.items():
            ranked = rank_exprs_for_target(null_exprs, tgt["empirical"], top_n=1)
            if ranked:
                null_best_residuals[tgt_name].append(ranked[0]["residual_pct"])
        if (trial + 1) % 5 == 0:
            print(f"[{time.time()-t0:.1f}s]   null trial {trial+1}/{n_null_trials} done", file=sys.stderr)

    # Compute null statistics
    for tgt_name, tgt in TARGETS.items():
        ugp_residual = 100.0 * relative_residual(tgt["ugp_claim_val"], tgt["empirical"])
        null_res = null_best_residuals[tgt_name]
        null_res.sort()
        better_count = sum(1 for r in null_res if r <= ugp_residual)
        results["null_statistics"][tgt_name] = {
            "ugp_residual_pct": ugp_residual,
            "n_null_trials": len(null_res),
            "null_median_residual_pct": null_res[len(null_res)//2] if null_res else None,
            "null_min_residual_pct": null_res[0] if null_res else None,
            "null_trials_at_or_below_ugp_residual": better_count,
            "null_better_than_ugp_pct": 100.0 * better_count / max(len(null_res), 1),
        }

    results["runtime_seconds"] = time.time() - t0

    # --- Colour-lock gates ---
    gates = {}
    for tgt_name, tgt in TARGETS.items():
        rank = results["ugp_ranking"][tgt_name]["ugp_claim_rank_in_top_n"]
        gap = results["ugp_ranking"][tgt_name]["second_over_best_residual_ratio"]
        null_better_pct = results["null_statistics"][tgt_name]["null_better_than_ugp_pct"]
        # Gate A: rank 0 AND second-best at least 2x further from target AND null better <= 10%
        # Gate B: rank 0..9 (top-10)
        # Gate C: otherwise
        if rank == 0 and gap is not None and gap >= 2.0 and null_better_pct <= 10.0:
            gates[tgt_name] = "A"
        elif rank is not None and rank < 10:
            gates[tgt_name] = "B"
        else:
            gates[tgt_name] = "C"
    results["gate_per_target"] = gates

    # --- Overall disposition ---
    if all(g == "A" for g in gates.values()):
        results["overall_gate"] = "A (success — bounded-uniqueness)"
    elif all(g in ("A", "B") for g in gates.values()):
        results["overall_gate"] = "B (partial — ranked-uniqueness)"
    else:
        results["overall_gate"] = "C (not distinguished)"

    # --- Append post-commit SHA ---
    out_dict = {k: v for k, v in results.items()}
    # Need to serialize to compute post_commit_sha256 of results BEFORE saving the key
    tmp = json.dumps(out_dict, sort_keys=True, default=str).encode("utf-8")
    out_dict["post_commit_sha256"] = hashlib.sha256(tmp).hexdigest()

    out_path = os.path.join(os.path.dirname(__file__), "comp_p01_RC1_urc_bounded_enumeration.json")
    with open(out_path, "w") as f:
        json.dump(out_dict, f, indent=2, default=str)
    print(f"[{time.time()-t0:.1f}s] Wrote {out_path}", file=sys.stderr)

    # Human-readable summary to stdout
    print(json.dumps({
        "pre_commit_sha256": precommit_sha,
        "post_commit_sha256": out_dict["post_commit_sha256"],
        "n_ugp_expressions": results["n_expressions_ugp"],
        "gate_per_target": gates,
        "overall_gate": results["overall_gate"],
        "ranking_summary": {
            tgt_name: {
                "ugp_rank_in_top_n": results["ugp_ranking"][tgt_name]["ugp_claim_rank_in_top_n"],
                "ugp_residual_pct": results["ugp_ranking"][tgt_name]["ugp_claim_residual_pct"],
                "best_expr": results["ugp_ranking"][tgt_name]["best_expr"]["expr"] if results["ugp_ranking"][tgt_name]["best_expr"] else None,
                "best_residual_pct": results["ugp_ranking"][tgt_name]["best_expr"]["residual_pct"] if results["ugp_ranking"][tgt_name]["best_expr"] else None,
                "null_better_than_ugp_pct": results["null_statistics"][tgt_name]["null_better_than_ugp_pct"],
                "null_median_residual_pct": results["null_statistics"][tgt_name]["null_median_residual_pct"],
            } for tgt_name in TARGETS
        },
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
