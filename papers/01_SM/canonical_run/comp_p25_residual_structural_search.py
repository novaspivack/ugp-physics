#!/usr/bin/env python3
"""
comp_p25_residual_structural_search.py

Null-disciplined structural search for a closed-form identification of the
UGP electromagnetic-instantiation residual

    R = (b1_required - 73) / 73 = 2.39 x 10^-6   (= 2.39 ppm in alpha)

at 60-digit precision.  R is computed from the Lean-authoritative C_alg
(Quarter-Lock formula) and the non-circular CODATA-derived delta_target via
papers/01_SM/canonical_run/comp_p25_alpha_precision_floor.py.

This script tests three families of structural identifications against R,
SHA-256-pre-committed before any matching is performed:

  Family A   curated structural candidates (named integer or perturbative
             expressions in UGP atoms; tests prior structural hypotheses
             without enumeration, no fitting).

  Family B   bounded enumeration over UGP atoms only at depth <= 1
             (pure UGP integers and Lean-certified algebraic constants;
             no alpha).  A match here would identify R as a derived
             integer-algebraic fact independent of QED.

  Family C   bounded enumeration over UGP atoms together with alpha and pi
             at depth <= 1.  A match here would identify R with a specific
             one- or two-loop perturbative form factor.

Both Family B and Family C are accompanied by 30-trial null-randomization
discipline: each non-integer atom is replaced by a magnitude-matched random
real; the search is rerun to obtain a null distribution of best residuals.

Verdict thresholds (pre-committed; no post-hoc fitting):

  STRUCTURAL_FOUND_PURE_UGP    Family B beats null-min by >= 5x and < 1%
  STRUCTURAL_FOUND_WITH_ALPHA  Family C beats null-min by >= 5x and < 1%
  NAMED_CANDIDATE_MATCH        Family A best is < 1%
  WEAKLY_SUGGESTIVE            best 1-5% AND beats null-median by >= 3x
  PARITY_WITH_NULL             UGP best comparable to null distribution
  NO_MATCH                     UGP best > 10%

The Lean-certified UGP backbone is unaffected by this search; this script
characterizes the residual band rather than deriving R structurally.

Output: comp_p25_residual_structural_search.json
"""
from __future__ import annotations

import hashlib
import itertools
import json
import os
import random
from datetime import datetime, timezone
from typing import Any

import mpmath as mp

# mpmath's mpf type is not a standard PEP-484 type; use Any for annotations
# where mp.mpf would appear so static checkers (pyright/mypy) stay clean.
MpFloat = Any

HERE = os.path.dirname(os.path.abspath(__file__))

mp.mp.dps = 60


# --------------------------------------------------------- residual definition
# Computed by comp_p25_alpha_precision_floor.py from non-circular CODATA chain.
B1_REQ = mp.mpf("73.00017447")
R_REAL = (B1_REQ - 73) / 73                 # = 2.39e-6 (2.39 ppm)


# ----------------------------------------------------- structural atoms (Lean)
ALPHA_EM = mp.mpf("0.0072973525693")
PI = mp.pi
PHI = (mp.mpf(1) + mp.sqrt(5)) / 2
KAPPA = 2 * mp.cos(PI / 10)
COS2_PI12 = (mp.mpf(2) + mp.sqrt(3)) / 4

UGP_INTEGERS: dict[str, MpFloat] = {
    "1":    mp.mpf(1),
    "2":    mp.mpf(2),
    "3":    mp.mpf(3),    # Nc
    "4":    mp.mpf(4),
    "5":    mp.mpf(5),
    "7":    mp.mpf(7),    # delta = Nc + (Nc^2-1)/2
    "8":    mp.mpf(8),    # Nc^2 - 1
    "9":    mp.mpf(9),    # Nc^2
    "10":   mp.mpf(10),
    "11":   mp.mpf(11),
    "13":   mp.mpf(13),
    "16":   mp.mpf(16),
    "17":   mp.mpf(17),
    "29":   mp.mpf(29),
    "73":   mp.mpf(73),   # b1, sieve-forced
    "120":  mp.mpf(120),  # cyclotomic conductor
    "137":  mp.mpf(137),
    "233":  mp.mpf(233),
    "511":  mp.mpf(511),
    "823":  mp.mpf(823),  # c1
    "1008": mp.mpf(1008), # R_10
}

UGP_ALGEBRAIC: dict[str, MpFloat] = {
    "phi":         PHI,
    "phi^2":       PHI ** 2,
    "phi^3":       PHI ** 3,
    "kappa":       KAPPA,
    "kappa^2":     KAPPA ** 2,
    "cos2(pi/12)": COS2_PI12,
    "k_L2":        mp.mpf(7) / 512,
    "1/k_gen2":    mp.mpf(-2) / PHI,
    "C_alg":       mp.mpf("1.21173843356"),
}

UGP_ATOMS: dict[str, MpFloat] = {**UGP_INTEGERS, **UGP_ALGEBRAIC}

ALPHA_ATOMS: dict[str, MpFloat] = {
    "alpha":     ALPHA_EM,
    "alpha^2":   ALPHA_EM ** 2,
    "pi":        PI,
    "pi^2":      PI ** 2,
    "pi^3":      PI ** 3,
    "4pi":       4 * PI,
    "2pi":       2 * PI,
    "8pi":       8 * PI,
    "4pi^2":     4 * PI ** 2,
    "2pi^2":     2 * PI ** 2,
}


# ---------------------------------------------------- Family A: named priors
def named_candidates() -> list[tuple[str, MpFloat]]:
    """Curated structural candidates in UGP atoms (no fitting).

    Mixes pure-integer rationals (would be derived if matched), single- and
    two-loop perturbative forms (canonical QED radiative magnitudes), and
    Lean-certified algebraic-K combinations.
    """
    b1 = mp.mpf(73)
    Nc = mp.mpf(3)
    delta = mp.mpf(7)
    a = ALPHA_EM
    return [
        # Pure-integer guesses (if matched, R is a derived integer-algebraic fact)
        ("1/b1^3",                  1 / b1 ** 3),
        ("1/(b1^3*Nc)",             1 / (b1 ** 3 * Nc)),
        ("1/(2*b1^3)",              1 / (2 * b1 ** 3)),
        ("Nc/b1^3",                 Nc / b1 ** 3),
        ("delta/b1^3",              delta / b1 ** 3),
        ("1/(b1^2*Nc^3)",           1 / (b1 ** 2 * Nc ** 3)),
        ("1/(b1^2*delta)",          1 / (b1 ** 2 * delta)),
        ("delta/(b1^2*Nc^3)",       delta / (b1 ** 2 * Nc ** 3)),
        ("1/(b1*c1)",               1 / (73 * 823)),
        ("1/(b1*1008)",             1 / (73 * 1008)),
        ("1/(c1*Nc)",               1 / (823 * 3)),
        ("1/(b1^2*delta^2)",        1 / (b1 ** 2 * delta ** 2)),
        ("1/(b1^2*delta*Nc)",       1 / (b1 ** 2 * delta * Nc)),
        # alpha-involving candidates (one- or two-loop QED radiative)
        ("alpha^2/(2*pi^2)",        a ** 2 / (2 * PI ** 2)),
        ("alpha^2/(pi^2)",          a ** 2 / PI ** 2),
        ("alpha^2/(4*pi^2)",        a ** 2 / (4 * PI ** 2)),
        ("alpha^2/(b1*pi)",         a ** 2 / (b1 * PI)),
        ("alpha^2/(b1*pi^2)",       a ** 2 / (b1 * PI ** 2)),
        ("alpha^2*Nc/(2*pi^2)",     a ** 2 * Nc / (2 * PI ** 2)),
        ("alpha/(b1^2*pi)",         a / (b1 ** 2 * PI)),
        ("alpha/(b1^2*4*pi)",       a / (b1 ** 2 * 4 * PI)),
        ("alpha/(b1^2*delta)",      a / (b1 ** 2 * delta)),
        ("alpha/(b1*c1)",           a / (b1 * 823)),
        ("alpha/(b1*1008)",         a / (b1 * 1008)),
        # Mixed: k_L2-scaled
        ("k_L2/(b1^3)",             (mp.mpf(7) / 512) / b1 ** 3),
        ("k_L2/(b1*c1)",            (mp.mpf(7) / 512) / (b1 * 823)),
        ("k_L2*alpha/(2*pi)",       (mp.mpf(7) / 512) * a / (2 * PI)),
        ("k_L2^2*alpha",            (mp.mpf(7) / 512) ** 2 * a),
    ]


# ---------------------------------------------------- pre-commitment block
PRE_COMMIT = {
    "purpose": "null-disciplined structural search of the 2.39 ppm residual",
    "real_residual_value": str(R_REAL),
    "b1_required_value": str(B1_REQ),
    "atom_count_ugp_integers": len(UGP_INTEGERS),
    "atom_count_ugp_algebraic": len(UGP_ALGEBRAIC),
    "atom_count_alpha_extras": len(ALPHA_ATOMS),
    "named_candidate_count": len(named_candidates()),
    "search_depth_max": 1,
    "operators": ["+", "-", "*", "/"],
    "null_trials": 30,
    "verdict_options": [
        "STRUCTURAL_FOUND_PURE_UGP",
        "STRUCTURAL_FOUND_WITH_ALPHA",
        "NAMED_CANDIDATE_MATCH",
        "WEAKLY_SUGGESTIVE",
        "PARITY_WITH_NULL",
        "NO_MATCH",
    ],
    "verdict_thresholds": {
        "STRUCTURAL_FOUND_factor_over_null_min": 5.0,
        "STRUCTURAL_FOUND_residual_pct": 1.0,
        "NAMED_CANDIDATE_residual_pct": 1.0,
        "WEAKLY_SUGGESTIVE_residual_pct": 5.0,
        "WEAKLY_SUGGESTIVE_factor_over_null_median": 3.0,
        "NO_MATCH_residual_pct": 10.0,
    },
}
PRE_COMMIT_SHA = hashlib.sha256(
    json.dumps(PRE_COMMIT, sort_keys=True, default=str).encode()
).hexdigest()


# -------------------------------------------------------- enumeration helpers
def enumerate_depth1(atoms: dict[str, MpFloat]) -> list[tuple[str, MpFloat]]:
    """All atoms plus binary combinations a OP b, OP in {+, -, *, /}."""
    out: list[tuple[str, MpFloat]] = list(atoms.items())
    seen_keys: set[str] = set()
    for (sa, va), (sb, vb) in itertools.product(atoms.items(), repeat=2):
        for sym, fn in (
            ("+", lambda a, b: a + b),
            ("-", lambda a, b: a - b),
            ("*", lambda a, b: a * b),
            ("/", lambda a, b: a / b if abs(b) > mp.mpf("1e-50") else None),
        ):
            v = fn(va, vb)
            if v is None or not (mp.isfinite(v) and v > 0):
                continue
            key = mp.nstr(v, 12)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            out.append((f"({sa}{sym}{sb})", v))
    return out


def best_n(target: MpFloat, expressions: list[tuple[str, MpFloat]],
           n: int = 20) -> list[tuple[str, MpFloat, MpFloat]]:
    rows: list[tuple[str, MpFloat, MpFloat]] = []
    for sym, val in expressions:
        if val <= 0:
            continue
        rel = abs(val - target) / target
        rows.append((sym, val, rel))
    rows.sort(key=lambda x: x[2])
    return rows[:n]


def randomized_null(atoms: dict[str, MpFloat], target: MpFloat,
                    trials: int = 30, seed: int = 1234) -> list[MpFloat]:
    """Magnitude-matched random replacement of non-integer atoms; null distribution."""
    rng = random.Random(seed)
    integer_atoms = {k for k, v in atoms.items() if v == int(v)}
    bests: list[MpFloat] = []
    for _ in range(trials):
        perturbed: dict[str, MpFloat] = {}
        for name, val in atoms.items():
            if name in integer_atoms:
                perturbed[name] = val
            else:
                mag = mp.log10(abs(val))
                factor = mp.mpf(rng.uniform(0.5, 1.7))
                sign = mp.mpf(1) if val >= 0 else mp.mpf(-1)
                perturbed[name] = sign * factor * mp.mpf(10) ** mag
        exprs = enumerate_depth1(perturbed)
        top = best_n(target, exprs, n=1)
        bests.append(top[0][2] if top else mp.mpf("inf"))
    return bests


# ----------------------------------------------------------------------- main
def main() -> None:
    print("=" * 78)
    print("UGP residual structural search — null-disciplined, 60-digit")
    print("=" * 78)
    print(f"Pre-commit SHA-256: {PRE_COMMIT_SHA}")
    print(f"Target R = {mp.nstr(R_REAL, 16)}  ({mp.nstr(R_REAL * 1e6, 6)} ppm)")
    print()

    # Family A
    print("Family A — Curated named structural candidates:")
    rows_A = []
    for name, val in named_candidates():
        rel = abs(val - R_REAL) / R_REAL
        rows_A.append((name, val, rel))
    rows_A.sort(key=lambda x: x[2])
    print(f"  {'expression':<28} {'value':>14} {'rel resid':>14}")
    for name, val, rel in rows_A:
        print(f"  {name:<28} {mp.nstr(val, 8):>14} {mp.nstr(rel * 100, 6) + '%':>14}")
    best_A = rows_A[0]
    print(f"\n  Best Family-A: {best_A[0]}  ({mp.nstr(best_A[2] * 100, 6)}%)")
    print()

    # Family B
    print("Family B — Pure UGP-atom search (depth <= 1, no alpha):")
    exprs_B = enumerate_depth1(UGP_ATOMS)
    print(f"  Total candidate expressions: {len(exprs_B):,}")
    top_B = best_n(R_REAL, exprs_B, n=10)
    print(f"  Top 10:")
    print(f"    {'expression':<48} {'value':>14} {'rel resid':>14}")
    for sym, val, rel in top_B:
        sym_d = sym if len(sym) <= 46 else sym[:43] + "..."
        print(f"    {sym_d:<48} {mp.nstr(val, 8):>14} {mp.nstr(rel * 100, 6) + '%':>14}")
    null_B = randomized_null(UGP_ATOMS, R_REAL, trials=30, seed=2424)
    null_B_min = min(null_B)
    null_B_med = sorted(null_B)[len(null_B) // 2]
    print(f"\n  Null discipline (30 trials): min = {mp.nstr(null_B_min * 100, 6)}%, "
          f"median = {mp.nstr(null_B_med * 100, 6)}%")
    print(f"  UGP best: {mp.nstr(top_B[0][2] * 100, 6)}%, "
          f"null/UGP ratio = {mp.nstr(null_B_min / top_B[0][2], 4)}")
    print()

    # Family C
    print("Family C — UGP-atom + alpha search (depth <= 1):")
    atoms_C = {**UGP_ATOMS, **ALPHA_ATOMS}
    exprs_C = enumerate_depth1(atoms_C)
    print(f"  Total candidate expressions: {len(exprs_C):,}")
    top_C = best_n(R_REAL, exprs_C, n=10)
    print(f"  Top 10:")
    print(f"    {'expression':<48} {'value':>14} {'rel resid':>14}")
    for sym, val, rel in top_C:
        sym_d = sym if len(sym) <= 46 else sym[:43] + "..."
        print(f"    {sym_d:<48} {mp.nstr(val, 8):>14} {mp.nstr(rel * 100, 6) + '%':>14}")
    null_C = randomized_null(atoms_C, R_REAL, trials=30, seed=3535)
    null_C_min = min(null_C)
    null_C_med = sorted(null_C)[len(null_C) // 2]
    print(f"\n  Null discipline (30 trials): min = {mp.nstr(null_C_min * 100, 6)}%, "
          f"median = {mp.nstr(null_C_med * 100, 6)}%")
    print(f"  UGP+alpha best: {mp.nstr(top_C[0][2] * 100, 6)}%, "
          f"null/UGP+alpha ratio = {mp.nstr(null_C_min / top_C[0][2], 4)}")
    print()

    # Verdict
    best_B_residual = top_B[0][2]
    best_C_residual = top_C[0][2]
    best_A_residual = best_A[2]

    def factor(num: MpFloat, den: MpFloat) -> MpFloat:
        if den <= 0:
            return mp.mpf("inf")
        return num / den

    if (best_B_residual < mp.mpf("0.01")
            and factor(null_B_min, best_B_residual) >= 5):
        verdict = "STRUCTURAL_FOUND_PURE_UGP"
    elif (best_C_residual < mp.mpf("0.01")
            and factor(null_C_min, best_C_residual) >= 5):
        verdict = "STRUCTURAL_FOUND_WITH_ALPHA"
    elif best_A_residual < mp.mpf("0.01"):
        verdict = "NAMED_CANDIDATE_MATCH"
    elif (min(best_A_residual, best_B_residual, best_C_residual) < mp.mpf("0.05")
          and factor(null_C_med, min(best_B_residual, best_C_residual)) >= 3):
        verdict = "WEAKLY_SUGGESTIVE"
    elif min(best_B_residual, best_C_residual) > mp.mpf("0.10"):
        verdict = "NO_MATCH"
    else:
        verdict = "PARITY_WITH_NULL"

    print(f"VERDICT: {verdict}")
    print(f"  Family A best: {best_A[0]}  -> {mp.nstr(best_A_residual * 100, 6)}%")
    print(f"  Family B best: {top_B[0][0]}  -> {mp.nstr(best_B_residual * 100, 6)}%")
    print(f"  Family C best: {top_C[0][0]}  -> {mp.nstr(best_C_residual * 100, 6)}%")
    print()

    cert = {
        "description":
            "Null-disciplined structural search of the UGP alpha-precision residual",
        "pre_commit_sha256": PRE_COMMIT_SHA,
        "precision_decimal_digits": int(mp.mp.dps),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "real_residual": mp.nstr(R_REAL, 18),
        "real_residual_ppm": mp.nstr(R_REAL * 1e6, 6),
        "b1_req": mp.nstr(B1_REQ, 14),
        "family_A_named_candidates": [
            {"name": n, "value": mp.nstr(v, 14), "rel_pct": mp.nstr(r * 100, 6)}
            for n, v, r in rows_A
        ],
        "family_B_pure_ugp": {
            "expression_count": len(exprs_B),
            "top_10": [
                {"expression": s, "value": mp.nstr(v, 14), "rel_pct": mp.nstr(r * 100, 6)}
                for s, v, r in top_B
            ],
            "null_min_pct": mp.nstr(null_B_min * 100, 6),
            "null_median_pct": mp.nstr(null_B_med * 100, 6),
        },
        "family_C_ugp_plus_alpha": {
            "expression_count": len(exprs_C),
            "top_10": [
                {"expression": s, "value": mp.nstr(v, 14), "rel_pct": mp.nstr(r * 100, 6)}
                for s, v, r in top_C
            ],
            "null_min_pct": mp.nstr(null_C_min * 100, 6),
            "null_median_pct": mp.nstr(null_C_med * 100, 6),
        },
        "verdict": verdict,
    }

    out_path = os.path.join(HERE, "comp_p25_residual_structural_search.json")
    with open(out_path, "w") as f:
        json.dump(cert, f, indent=2)

    sha = hashlib.sha256(open(out_path, "rb").read()).hexdigest()
    print(f"Artifact:           {os.path.basename(out_path)}")
    print(f"Artifact SHA-256:    {sha}")
    print(f"Pre-commit SHA-256:  {PRE_COMMIT_SHA}")


if __name__ == "__main__":
    main()
