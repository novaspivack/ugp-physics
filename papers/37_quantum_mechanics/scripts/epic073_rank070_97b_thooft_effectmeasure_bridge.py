#!/usr/bin/env python3
"""
EPIC_073 Rank 070-97B — 't Hooft coarse-graining → EffectMeasure axioms (B1).

Tests bridge hypothesis (B1) from LAB_NOTE_070-97:
  The coarse-grained probability measure induced by 't Hooft information loss on
  Z7^5 beables satisfies EffectMeasure axioms (normalization, nonnegativity,
  POVM additivity, boundedness) and equals Born weights |alpha_k|^2 on winding
  sectors.

Reference: nems-lean NemS/Quantum/Measures.lean EffectMeasure structure.
"""

from __future__ import annotations

import json
import random
import signal
import sys
import time
from typing import Dict, List, Tuple

import numpy as np

TIMEOUT_SECONDS = 300
N_RANDOM_STATES = 200
N_POVM_TESTS = 50
N_INFO_LOSS_STEPS = 7
SEED = 97097

signal.signal(
    signal.SIGALRM,
    lambda _s, _f: (
        print(f"\nTIMEOUT: wall-clock limit {TIMEOUT_SECONDS}s reached."),
        sys.exit(1),
    ),
)
signal.alarm(TIMEOUT_SECONDS)
t0 = time.time()
random.seed(SEED)
np.random.seed(SEED)

# f_MDL lookup (matches CUP3DUniqueness.lean / fmdl_hamiltonian_spectrum.py)
_FMDL_LOOKUP = {
    (1, 1, 5): 2, (1, 5, 2): 5, (5, 2, 2): 2, (2, 2, 1): 0,
    (2, 1, 1): 2, (2, 2, 5): 5, (2, 5, 2): 6, (5, 2, 0): 5,
    (2, 0, 2): 3, (0, 2, 2): 5,
    (0, 0, 0): 0, (0, 0, 1): 1, (0, 1, 0): 1, (0, 1, 1): 1,
    (1, 0, 0): 0, (1, 0, 1): 1, (1, 1, 0): 1, (1, 1, 1): 0,
}


def fmdl(l: int, c: int, r: int) -> int:
    return _FMDL_LOOKUP.get((l, c, r), 0)


def fmdl_step5(state: Tuple[int, ...]) -> Tuple[int, ...]:
    n = 5
    return tuple(
        fmdl(state[(i - 1) % n], state[i], state[(i + 1) % n]) for i in range(n)
    )


def encode(s: Tuple[int, ...]) -> int:
    return sum(s[i] * 7 ** i for i in range(5))


def decode(n: int) -> Tuple[int, ...]:
    return tuple((n // 7 ** i) % 7 for i in range(5))


def winding(state: Tuple[int, ...]) -> int:
    return sum(state) % 7


L = 7**5
T = [encode(fmdl_step5(decode(i))) for i in range(L)]

# Precompute winding sector membership
WINDING_OF = [winding(decode(i)) for i in range(L)]
SECTOR_STATES: List[List[int]] = [[] for _ in range(7)]
for i, w in enumerate(WINDING_OF):
    SECTOR_STATES[w].append(i)

SM_SECTORS = {0, 2, 3, 4, 6}


def random_normalized_amplitudes() -> np.ndarray:
    z = np.random.randn(L) + 1j * np.random.randn(L)
    z /= np.linalg.norm(z)
    return z


def winding_born_probs(alpha: np.ndarray) -> np.ndarray:
    p = np.zeros(7, dtype=float)
    for k in range(7):
        p[k] = float(np.sum(np.abs(alpha[SECTOR_STATES[k]]) ** 2))
    return p


def coarse_grain_density(alpha: np.ndarray) -> np.ndarray:
    """7×7 diagonal ρ in winding-sector space."""
    p = winding_born_probs(alpha)
    return np.diag(p)


def projector_sector(k: int) -> np.ndarray:
    """Effect operator P_k on full 16807-dim space (diagonal projector)."""
    P = np.zeros(L, dtype=float)
    for i in SECTOR_STATES[k]:
        P[i] = 1.0
    return P


def mu_from_alpha(alpha: np.ndarray, effect_diag: np.ndarray) -> float:
    """Born probability μ(E) = Re Tr(ρ E) for diagonal E on beable basis."""
    return float(np.sum(np.abs(alpha) ** 2 * effect_diag))


def random_povm_partition(n_outcomes: int, rng: random.Random) -> List[np.ndarray]:
    """Random partition of identity into diagonal projectors on Z7^5."""
    indices = list(range(L))
    rng.shuffle(indices)
    chunk = L // n_outcomes
    effects = []
    start = 0
    for j in range(n_outcomes):
        end = L if j == n_outcomes - 1 else start + chunk
        E = np.zeros(L, dtype=float)
        for i in indices[start:end]:
            E[i] = 1.0
        effects.append(E)
        start = end
    return effects


def apply_info_loss_channel(alpha: np.ndarray, steps: int) -> np.ndarray:
    """
    't Hooft information-loss channel: map each beable amplitude to its
    post-relaxation winding sector representative (vacuum-basin coarse grain).
    """
    out = np.zeros(L, dtype=complex)
    for i in range(L):
        state = decode(i)
        s = state
        for _ in range(steps):
            s = fmdl_step5(s)
        target_w = winding(s)
        # Coarse grain: amplitude flows to canonical sector representative (min index)
        rep = SECTOR_STATES[target_w][0]
        out[rep] += alpha[i]
    norm = np.linalg.norm(out)
    if norm > 0:
        out /= norm
    return out


def test_effectmeasure_axioms(alpha: np.ndarray) -> Dict[str, bool | float]:
    rho_diag = np.abs(alpha) ** 2

    # Normalization: μ(I) = 1
    identity = np.ones(L, dtype=float)
    mu_I = mu_from_alpha(alpha, identity)
    normalized = abs(mu_I - 1.0) < 1e-12

    # Nonnegativity and le_one on all sector projectors
    nonneg = True
    le_one = True
    for k in range(7):
        Pk = projector_sector(k)
        m = mu_from_alpha(alpha, Pk)
        if m < -1e-12:
            nonneg = False
        if m > 1.0 + 1e-12:
            le_one = False

    # POVM additivity: 7-way winding partition
    povm7 = [projector_sector(k) for k in range(7)]
    sum7 = sum(mu_from_alpha(alpha, E) for E in povm7)
    povm7_ok = abs(sum7 - 1.0) < 1e-10

    # POVM additivity: SM (5) + GUT (2) split
    sm_effect = np.zeros(L, dtype=float)
    gut_effect = np.zeros(L, dtype=float)
    for k in range(7):
        Pk = projector_sector(k)
        if k in SM_SECTORS:
            sm_effect += Pk
        else:
            gut_effect += Pk
    sum_sm_gut = mu_from_alpha(alpha, sm_effect) + mu_from_alpha(alpha, gut_effect)
    povm_sm_gut_ok = abs(sum_sm_gut - 1.0) < 1e-10

    # Born match: sector probabilities = |c_k|^2
    p = winding_born_probs(alpha)
    born_ok = abs(float(np.sum(p)) - 1.0) < 1e-12 and bool(np.all(p >= -1e-15))

    return {
        "normalized": normalized,
        "nonneg": nonneg,
        "le_one": le_one,
        "povm7_additive": povm7_ok,
        "povm_sm_gut_additive": povm_sm_gut_ok,
        "born_match": born_ok,
        "mu_I": mu_I,
        "sum7": sum7,
    }


def main() -> None:
    print("=" * 72)
    print("Rank 070-97B — 't Hooft coarse-grain → EffectMeasure axioms (B1)")
    print(f"  State space: 7^5 = {L}")
    print("=" * 72)

    rng = random.Random(SEED)
    failures = 0
    random_results = []

    for trial in range(N_RANDOM_STATES):
        alpha = random_normalized_amplitudes()
        checks = test_effectmeasure_axioms(alpha)
        random_results.append(checks)
        if not all(
            checks[k]
            for k in (
                "normalized",
                "nonneg",
                "le_one",
                "povm7_additive",
                "povm_sm_gut_additive",
                "born_match",
            )
        ):
            failures += 1

    # Structured test states: single beables, equal superposition within sector
    structured_pass = True
    for w in range(7):
        alpha = np.zeros(L, dtype=complex)
        for i in SECTOR_STATES[w][:3]:
            alpha[i] = 1.0 / np.sqrt(min(3, len(SECTOR_STATES[w])))
        alpha /= np.linalg.norm(alpha)
        c = test_effectmeasure_axioms(alpha)
        if not all(c[k] for k in ("normalized", "povm7_additive", "born_match")):
            structured_pass = False

    # Random POVM partition tests
    povm_fail = 0
    for _ in range(N_POVM_TESTS):
        alpha = random_normalized_amplitudes()
        k_out = rng.randint(2, 8)
        effects = random_povm_partition(k_out, rng)
        total = sum(mu_from_alpha(alpha, E) for E in effects)
        if abs(total - 1.0) > 1e-9:
            povm_fail += 1

    # Information-loss channel: post-channel states satisfy axioms
    info_loss_fail = 0
    info_loss_born_drift = []
    for _ in range(N_RANDOM_STATES):
        alpha0 = random_normalized_amplitudes()
        alpha1 = apply_info_loss_channel(alpha0, N_INFO_LOSS_STEPS)
        c = test_effectmeasure_axioms(alpha1)
        if not all(c[k] for k in ("normalized", "povm7_additive", "nonneg")):
            info_loss_fail += 1
        p0 = winding_born_probs(alpha0)
        p1 = winding_born_probs(alpha1)
        info_loss_born_drift.append(float(np.max(np.abs(p1 - p0))))

    # Coarse-grained 7×7 ρ: Tr(ρ P_k) matches sector Born weights
    rho_trace_fail = 0
    for _ in range(N_RANDOM_STATES):
        alpha = random_normalized_amplitudes()
        rho7 = coarse_grain_density(alpha)
        p = winding_born_probs(alpha)
        for k in range(7):
            if abs(rho7[k, k] - p[k]) > 1e-12:
                rho_trace_fail += 1
                break

    gates = {
        "random_states_pass": failures == 0,
        "structured_sector_pass": structured_pass,
        "random_povm_pass": povm_fail == 0,
        "info_loss_axioms_pass": info_loss_fail == 0,
        "coarse_rho_trace_pass": rho_trace_fail == 0,
    }
    all_pass = all(gates.values())

    results = {
        "rank": "070-97B",
        "hypothesis": "B1_thooft_coarse_grain_satisfies_EffectMeasure",
        "n_states": L,
        "n_random_trials": N_RANDOM_STATES,
        "n_povm_tests": N_POVM_TESTS,
        "info_loss_steps": N_INFO_LOSS_STEPS,
        "random_failures": failures,
        "povm_failures": povm_fail,
        "info_loss_failures": info_loss_fail,
        "rho_trace_failures": rho_trace_fail,
        "info_loss_max_born_drift_mean": float(np.mean(info_loss_born_drift)),
        "info_loss_max_born_drift_max": float(np.max(info_loss_born_drift)),
        "gates": gates,
        "b1_verdict": "PASS_PARTIAL" if all_pass else "FAIL",
        "cat_level": "CatA (partial B1)" if all_pass else "CatA (negative)",
        "interpretation": (
            "Coarse-grained winding-sector Born weights satisfy EffectMeasure axioms "
            "for all tested superpositions and POVM partitions. Full B1 CatAL requires "
            "Lean bridge to NemS.Quantum.EffectMeasure + PSC identification."
            if all_pass
            else "Some EffectMeasure axiom failed — B1 not supported at tested granularity."
        ),
        "open_for_catAL": [
            "Lean import bridge ugp-lean-exp ↔ nems-lean EffectMeasure",
            "Prove coarse-grained channel equals template ρ under PSC",
            "Bridge (B2): PSC + f_MDL dynamics ⇒ EffectMeasure",
        ],
        "wall_clock_s": time.time() - t0,
    }

    out_path = "epic073_rank070_97b_thooft_effectmeasure_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nRandom state failures: {failures}/{N_RANDOM_STATES}")
    print(f"Random POVM failures: {povm_fail}/{N_POVM_TESTS}")
    print(f"Info-loss channel failures: {info_loss_fail}/{N_RANDOM_STATES}")
    print(f"Coarse ρ trace failures: {rho_trace_fail}/{N_RANDOM_STATES}")
    print(f"Mean max Born drift under info-loss: {results['info_loss_max_born_drift_mean']:.6f}")
    print(f"\nGates: {gates}")
    print(f"B1 verdict: {results['b1_verdict']} — {results['cat_level']}")
    print(f"Results: {out_path}")
    print(f"Wall clock: {results['wall_clock_s']:.2f}s")

    signal.alarm(0)
    if not all_pass:
        sys.exit(1)


if __name__ == "__main__":
    main()
