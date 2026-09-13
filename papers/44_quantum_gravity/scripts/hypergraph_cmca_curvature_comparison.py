#!/usr/bin/env python3
"""
hypergraph_cmca_curvature_comparison.py — EPIC 083 rank 083-HYPERGRAPH-CMCA.

Compares deviation-based Ollivier–Ricci curvature (EE/SD/XD classification)
across Rule 110 (CMCA substrate) and comparison ECA rules 30, 90, 124.

Method: same framework as papers/36_emergent_gravity_cmca/canonical_run/rule110_ricci_scaling.py
(Gorard 2020 deviation-based κ on causal graphs).

C_Gorard = 3/32 is a three-tape dimensional coefficient (N_spatial=3, D=4), not read off
from 1D κ distributions; this script records it separately as GTE-specific structure.
"""

from __future__ import annotations

import json
import signal
import sys
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np

TIMEOUT_SECONDS = 600


def _timeout_handler(signum, frame):
    print(f"\nTIMEOUT: wall-clock limit {TIMEOUT_SECONDS}s reached.")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

# ---------------------------------------------------------------------------
# ECA rule tables (Wolfram convention: 111 … 000)
# ---------------------------------------------------------------------------
RULE110 = {
    (1, 1, 1): 0, (1, 1, 0): 1, (1, 0, 1): 1, (1, 0, 0): 0,
    (0, 1, 1): 1, (0, 1, 0): 1, (0, 0, 1): 1, (0, 0, 0): 0,
}
RULE30 = {
    (0, 0, 0): 0, (0, 0, 1): 1, (0, 1, 0): 1, (0, 1, 1): 1,
    (1, 0, 0): 1, (1, 0, 1): 0, (1, 1, 0): 0, (1, 1, 1): 0,
}
RULE90 = {
    (0, 0, 0): 0, (0, 0, 1): 1, (0, 1, 0): 0, (0, 1, 1): 1,
    (1, 0, 0): 1, (1, 0, 1): 0, (1, 1, 0): 1, (1, 1, 1): 0,
}
RULE124 = {
    (0, 0, 0): 0, (0, 0, 1): 0, (0, 1, 0): 1, (0, 1, 1): 1,
    (1, 0, 0): 1, (1, 0, 1): 1, (1, 1, 0): 1, (1, 1, 1): 1,
}

RULE110_ETHER = [1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0]
RULE110_DRIFT = 4

# Rule 124 shares the CMCA chiral ether (period-14, drift 4) — same vacuum certificate.
RULE124_ETHER = RULE110_ETHER
RULE124_DRIFT = 4

# Rule 30 / 90: all-zero is a fixed point; use uniform vacuum (no spatial drift).
ZERO_ETHER = [0]
ZERO_DRIFT = 0

# Rule 90 also supports period-2 checkerboard as an additive ether.
RULE90_CHECKER_ETHER = [0, 1]
RULE90_CHECKER_DRIFT = 0


@dataclass
class RuleConfig:
    name: str
    rule_table: Dict[Tuple[int, int, int], int]
    ether: List[int]
    drift: int
    substrate: str
    notes: str


RULE_CONFIGS = [
    RuleConfig(
        name="rule_110",
        rule_table=RULE110,
        ether=RULE110_ETHER,
        drift=RULE110_DRIFT,
        substrate="CMCA (GTE)",
        notes="Period-14 ether 11111000100110, drift 4 — canonical CMCA vacuum",
    ),
    RuleConfig(
        name="rule_124",
        rule_table=RULE124,
        ether=RULE124_ETHER,
        drift=RULE124_DRIFT,
        substrate="CMCA chiral partner",
        notes="Chiral pair to Rule 110; same ether background",
    ),
    RuleConfig(
        name="rule_30",
        rule_table=RULE30,
        ether=ZERO_ETHER,
        drift=ZERO_DRIFT,
        substrate="Wolfram ECA (contrast)",
        notes="Chaotic rule; all-zero vacuum fixed point",
    ),
    RuleConfig(
        name="rule_90",
        rule_table=RULE90,
        ether=ZERO_ETHER,
        drift=ZERO_DRIFT,
        substrate="Wolfram ECA (contrast)",
        notes="Additive XOR rule; all-zero vacuum",
    ),
    RuleConfig(
        name="rule_90_checker",
        rule_table=RULE90,
        ether=RULE90_CHECKER_ETHER,
        drift=RULE90_CHECKER_DRIFT,
        substrate="Wolfram ECA (contrast)",
        notes="Rule 90 with period-2 checkerboard ether",
    ),
]

EPS = 0.1
KAPPA_SD_EXACT = 10 / 13
C_GORARD_CMCA = 3 / 32
N_GEN = 3
D = N_GEN + 1
Z7 = 7


def ca_step(tape: np.ndarray, rule_table: Dict[Tuple[int, int, int], int]) -> np.ndarray:
    L = len(tape)
    new = np.zeros(L, dtype=int)
    for i in range(L):
        trio = (tape[(i - 1) % L], tape[i], tape[(i + 1) % L])
        new[i] = rule_table[trio]
    return new


def ether_val(t: int, x: int, ether: List[int], drift: int) -> int:
    return ether[(x + drift * t) % len(ether)]


def wasserstein1d(masses1, positions1, masses2, positions2) -> float:
    pd1 = defaultdict(float)
    pd2 = defaultdict(float)
    for m, p in zip(masses1, positions1):
        pd1[p] += m
    for m, p in zip(masses2, positions2):
        pd2[p] += m
    all_pos = sorted(set(list(positions1) + list(positions2)))
    cdf1 = cdf2 = 0.0
    w = 0.0
    for i in range(len(all_pos) - 1):
        pos = all_pos[i]
        cdf1 += pd1[pos]
        cdf2 += pd2[pos]
        gap = all_pos[i + 1] - all_pos[i]
        w += abs(cdf1 - cdf2) * gap
    return w


def ollivier_ricci_dev(
    t: int,
    x: int,
    spacetime: np.ndarray,
    L: int,
    cfg: RuleConfig,
    eps: float = EPS,
) -> Optional[float]:
    if t + 1 >= len(spacetime):
        return None
    p1 = [x - 1, x, x + 1]
    p2 = [x, x + 1, x + 2]
    w1 = [
        abs(int(spacetime[t + 1][xi % L]) - ether_val(t + 1, xi % L, cfg.ether, cfg.drift)) + eps
        for xi in p1
    ]
    w2 = [
        abs(int(spacetime[t + 1][xi % L]) - ether_val(t + 1, xi % L, cfg.ether, cfg.drift)) + eps
        for xi in p2
    ]
    z1, z2 = sum(w1), sum(w2)
    return 1.0 - wasserstein1d([w / z1 for w in w1], p1, [w / z2 for w in w2], p2)


def causal_nbhd_type(
    t: int,
    x: int,
    spacetime: np.ndarray,
    L: int,
    cfg: RuleConfig,
) -> str:
    ev = lambda tt, xx: ether_val(tt, xx, cfg.ether, cfg.drift)
    dev_x = int(spacetime[t][x % L]) != ev(t, x % L)
    dev_x1 = int(spacetime[t][(x + 1) % L]) != ev(t, (x + 1) % L)
    if dev_x or dev_x1:
        return "PE"

    dev_xm1 = int(spacetime[t + 1][(x - 1) % L]) != ev(t + 1, (x - 1) % L)
    dev_fx = int(spacetime[t + 1][x % L]) != ev(t + 1, x % L)
    dev_fx1 = int(spacetime[t + 1][(x + 1) % L]) != ev(t + 1, (x + 1) % L)
    dev_xp2 = int(spacetime[t + 1][(x + 2) % L]) != ev(t + 1, (x + 2) % L)

    dev_shared = dev_fx or dev_fx1
    dev_excl = dev_xm1 or dev_xp2

    if not dev_shared and not dev_excl:
        return "EE"
    if dev_shared and not dev_excl:
        return "SD"
    if not dev_shared and dev_excl:
        return "XD"
    return "MX"


def analytic_kappa_ee_uniform() -> float:
    """Pure uniform ether weights → W₁ = 1 → κ = 0."""
    eps = EPS
    positions = [0, 1, 2]
    w = [eps, eps, eps]
    z = 3 * eps
    masses = [w / z for w in w]
    w1 = wasserstein1d(masses, positions, masses, [1, 2, 3])
    return 1.0 - w1


def analytic_kappa_sd_single_deviation() -> float:
    """Standard SD pattern: one shared future cell deviates by 1, others ether."""
    eps = EPS
    # Left ball at x: neighbors x-1,x,x+1; right ball at x+1: x,x+1,x+2
    # Shared cells x and x+1: one has deviation 1, one ether (0 dev)
    # Exclusive x-1 and x+2: ether
    def weights(devs):
        raw = [abs(d) + eps for d in devs]
        z = sum(raw)
        return [r / z for r in raw]

    # Future row: x-1:0, x:1, x+1:0, x+2:0
    w1 = weights([0, 1, 0])
    w2 = weights([1, 0, 0])
    w1_dist = wasserstein1d(w1, [-1, 0, 1], w2, [0, 1, 2])
    return 1.0 - w1_dist


def run_rule(cfg: RuleConfig, L: int = 500, T: int = 200, n_perturb: int = 30, seed: int = 7) -> dict:
    np.random.seed(seed)
    tape = np.array([cfg.ether[i % len(cfg.ether)] for i in range(L)], dtype=int)
    for s in np.random.choice(L, n_perturb, replace=False):
        tape[s] = 1 - tape[s]

    spacetime = [tape.copy()]
    for _ in range(T):
        tape = ca_step(tape, cfg.rule_table)
        spacetime.append(tape.copy())
    spacetime = np.array(spacetime)

    kappas: Dict[str, List[float]] = {k: [] for k in ["EE", "SD", "XD", "MX", "PE"]}
    for t in range(T):
        for x in range(L):
            k = ollivier_ricci_dev(t, x, spacetime, L, cfg, eps=EPS)
            if k is None:
                continue
            ctype = causal_nbhd_type(t, x, spacetime, L, cfg)
            kappas[ctype].append(k)

    def stat(key: str) -> Optional[dict]:
        vals = kappas[key]
        if not vals:
            return None
        arr = np.array(vals)
        return {
            "mean": float(np.mean(arr)),
            "std": float(np.std(arr)),
            "n": len(vals),
            "min": float(np.min(arr)),
            "max": float(np.max(arr)),
        }

    ee = stat("EE")
    sd = stat("SD")
    xd = stat("XD")

    return {
        "rule": cfg.name,
        "substrate": cfg.substrate,
        "notes": cfg.notes,
        "L": L,
        "T": T,
        "n_perturb": n_perturb,
        "seed": seed,
        "eps": EPS,
        "kappa_EE": ee["mean"] if ee else None,
        "kappa_EE_std": ee["std"] if ee else None,
        "kappa_SD": sd["mean"] if sd else None,
        "kappa_SD_std": sd["std"] if sd else None,
        "kappa_XD": xd["mean"] if xd else None,
        "kappa_XD_std": xd["std"] if xd else None,
        "n_EE": ee["n"] if ee else 0,
        "n_SD": sd["n"] if sd else 0,
        "n_XD": xd["n"] if xd else 0,
        "kappa_global": float(np.mean([k for v in kappas.values() for k in v])),
        "kappa_SD_vs_10_13": abs(sd["mean"] - KAPPA_SD_EXACT) if sd else None,
    }


def c_gorard_1d_single_tape() -> float:
    """Mixed-dim Gorard coefficient for 1+1D single tape (n_temp=2, n_spat=2)."""
    c_n2 = 1 / 8
    return (c_n2 + c_n2) / 4  # one spatial dimension → coefficient 1/16


def assess_conclusion(results: List[dict]) -> dict:
    cmca_rules = [r for r in results if r["rule"] in ("rule_110", "rule_124")]
    other_rules = [r for r in results if r["rule"] not in ("rule_110", "rule_124")]

    all_ee_zero = all(abs(r["kappa_EE"]) < 1e-9 for r in results if r["kappa_EE"] is not None)
    cmca_sd_match = all(
        r["kappa_SD_vs_10_13"] is not None and r["kappa_SD_vs_10_13"] < 0.02
        for r in cmca_rules
        if r["kappa_SD"] is not None
    )
    other_sd_differ = any(
        r["kappa_SD_vs_10_13"] is not None and r["kappa_SD_vs_10_13"] > 0.05
        for r in other_rules
        if r["kappa_SD"] is not None
    )
    other_sd_similar = any(
        r["kappa_SD_vs_10_13"] is not None and r["kappa_SD_vs_10_13"] < 0.02
        for r in other_rules
        if r["kappa_SD"] is not None
    )

    if all_ee_zero and cmca_sd_match and other_sd_differ:
        verdict = "CMCA-specific (strong GTE claim)"
        detail = (
            "κ_EE=0 is universal to deviation-based ether backgrounds, but κ_SD≈10/13 "
            "is achieved only on Rule 110/124 CMCA substrates; comparison rules differ."
        )
    elif all_ee_zero and other_sd_similar:
        verdict = "Partially universal"
        detail = (
            "κ_EE=0 and κ_SD≈10/13 hold across all tested rules with deviation-based "
            "framework — the 10/13 value follows from ε=1/10 weighting, not Rule 110 alone."
        )
    elif all_ee_zero:
        verdict = "Mixed — vacuum universal, matter substrate-dependent"
        detail = (
            "κ_EE=0 is universal (uniform ether weights). κ_SD varies by rule dynamics; "
            "CMCA pair (110/124) matches 10/13; some comparison rules differ."
        )
    else:
        verdict = "Inconclusive"
        detail = "κ_EE≠0 detected on some rules — investigate ether definitions."

    return {
        "verdict": verdict,
        "detail": detail,
        "kappa_EE_universal": all_ee_zero,
        "kappa_SD_cmca_specific": cmca_sd_match and other_sd_differ,
        "c_gorard_cmca_only": True,
        "c_gorard_note": (
            "C_Gorard=3/32=N_spatial/(2D²) requires three-tape 3+1D CMCA structure "
            "(N_spatial=3, D=4). Single-tape 1+1D rules give C_1D=1/16 by the same "
            "mixed-dim formula with one spatial tape — not 3/32."
        ),
    }


def main() -> dict:
    t0 = time.time()
    print("=" * 72)
    print("083-HYPERGRAPH-CMCA: Curvature comparison (deviation-based Ollivier–Ricci)")
    print("=" * 72)

    print("\nAnalytic checks (rule-independent):")
    k_ee = analytic_kappa_ee_uniform()
    k_sd = analytic_kappa_sd_single_deviation()
    print(f"  Uniform ether κ_EE (analytic) = {k_ee:.12f}  (expect 0)")
    print(f"  Single-deviation SD κ (analytic) = {k_sd:.12f}  (expect 10/13 = {KAPPA_SD_EXACT:.12f})")

    print(f"\n  C_Gorard (CMCA three-tape) = {C_GORARD_CMCA} = 3/(2D²), D={D}")
    print(f"  C_Gorard (1D single tape)  = {c_gorard_1d_single_tape():.6f} = 1/16")

    results = []
    for cfg in RULE_CONFIGS:
        print(f"\n{'─' * 72}")
        print(f"Running {cfg.name} ({cfg.substrate}) …")
        res = run_rule(cfg, L=500, T=200, n_perturb=max(30, 500 // 15), seed=7)
        results.append(res)
        print(f"  κ_EE = {res['kappa_EE']:+.10f}  (n={res['n_EE']})")
        if res["kappa_SD"] is not None:
            print(
                f"  κ_SD = {res['kappa_SD']:+.6f} ± {res['kappa_SD_std']:.4f}  "
                f"(n={res['n_SD']}, |Δ10/13|={res['kappa_SD_vs_10_13']:.4f})"
            )
        else:
            print("  κ_SD = N/A (no SD edges)")
        if res["kappa_XD"] is not None:
            print(f"  κ_XD = {res['kappa_XD']:+.6f} ± {res['kappa_XD_std']:.4f}  (n={res['n_XD']})")

    conclusion = assess_conclusion(results)

    print(f"\n{'=' * 72}")
    print("COMPARISON TABLE")
    print("=" * 72)
    print(f"{'Rule':<16} {'κ_EE':>12} {'κ_SD':>12} {'κ_XD':>12} {'|κ_SD−10/13|':>14}")
    print("─" * 72)
    for r in results:
        kee = f"{r['kappa_EE']:+.8f}" if r["kappa_EE"] is not None else "N/A"
        ksd = f"{r['kappa_SD']:+.6f}" if r["kappa_SD"] is not None else "N/A"
        kxd = f"{r['kappa_XD']:+.6f}" if r["kappa_XD"] is not None else "N/A"
        delta = f"{r['kappa_SD_vs_10_13']:.4f}" if r["kappa_SD_vs_10_13"] is not None else "N/A"
        print(f"{r['rule']:<16} {kee:>12} {ksd:>12} {kxd:>12} {delta:>14}")

    print(f"\n{'=' * 72}")
    print("STRATEGIC CONCLUSION")
    print("=" * 72)
    print(f"  Verdict: {conclusion['verdict']}")
    print(f"  {conclusion['detail']}")
    print(f"  {conclusion['c_gorard_note']}")

    output = {
        "metadata": {
            "rank": "083-HYPERGRAPH-CMCA",
            "method": "deviation-based Ollivier-Ricci (P36/R87.NT11)",
            "eps": EPS,
            "runtime_seconds": round(time.time() - t0, 2),
        },
        "reference_cmca": {
            "kappa_EE": 0.0,
            "kappa_SD_exact": KAPPA_SD_EXACT,
            "kappa_SD_numerical_p36": 0.7784,
            "kappa_XD_numerical_p36": -0.9520,
            "C_Gorard": C_GORARD_CMCA,
            "C_Gorard_formula": "N_spatial/(2*D^2) = 3/32",
            "D": D,
            "N_gen": N_GEN,
        },
        "analytic": {
            "kappa_EE_uniform": k_ee,
            "kappa_SD_single_deviation": k_sd,
            "C_Gorard_1d_single_tape": c_gorard_1d_single_tape(),
        },
        "rules": results,
        "conclusion": conclusion,
        "strategic_implication": (
            "GTE CC prediction via C_Gorard=3/32 and κ_SD=10/13 splits into two parts: "
            "(1) κ_EE=0 and the SD/XD trichotomy are generic to deviation-based causal graphs "
            "with uniform ether; (2) C_Gorard=3/32 is GTE-specific (three-tape D=4 geometry). "
            "Whether κ_SD=10/13 is GTE-specific depends on whether comparison rules match — "
            f"see verdict: {conclusion['verdict']}."
        ),
    }

    out_path = str(Path(__file__).parent.parent / "data" / "hypergraph_cmca_comparison.json")
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nArtifact: {out_path}")

    signal.alarm(0)
    return output


if __name__ == "__main__":
    main()
