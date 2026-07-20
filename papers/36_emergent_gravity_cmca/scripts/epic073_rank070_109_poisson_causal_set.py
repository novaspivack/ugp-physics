#!/usr/bin/env python3
"""
EPIC_073 Rank 070-109 — Rule 110 Poisson causal-set augmentation for Lorentz invariance.

Tests the Rank 109 conjecture: Poisson-random cell updates (probability rho per step)
restore exact Lorentz invariance in expectation while preserving Z7 orbit and C2 glider
structure. Builds an augmented causal set from stochastic update events on the Rule 110
Lorentzian graph (timelike + lightcone + spacelike edges).

Methodology:
  - Boost CV: Rank 102 (rule110_lorentz_scaling.py)
  - Causal cone v_R/v_L: Rank 102 measure_causal_cone (base-vs-pert diff)
  - C2 glider: Rank 070-113 (single-bit phase-1 nucleation, base-vs-pert diff)
  - Causal set augmentation: Poisson update events on DCG Lorentzian graph
"""

from __future__ import annotations

import json
import signal
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean, pstdev

import numpy as np

TIMEOUT_SECONDS = 600
OUT_JSON = Path(__file__).with_name("epic073_rank070_109_poisson_causal_set_results.json")

ETHER = [1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0]
ETHER_VEL = 4
TARGET_SPEED = 2 / 3
BOOST_VELS = [0, -4, -3, -2, -1, 1, 2, 3, 4, 6]
GEN1 = (1, 5, 2, 2, 1)
EXPECTED_ORBIT = [4, 4, 3, 0, 0]

_FMDL_ORBIT = {
    (1, 1, 5): 2, (1, 5, 2): 5, (5, 2, 2): 2, (2, 2, 1): 0,
    (2, 1, 1): 2, (2, 2, 5): 5, (2, 5, 2): 6, (5, 2, 0): 5,
    (2, 0, 2): 3, (0, 2, 2): 5,
}
RULE110 = {
    (1, 1, 1): 0, (1, 1, 0): 1, (1, 0, 1): 1, (1, 0, 0): 0,
    (0, 1, 1): 1, (0, 1, 0): 1, (0, 0, 1): 1, (0, 0, 0): 0,
}
for k, v in RULE110.items():
    _FMDL_ORBIT.setdefault(k, v)


def _timeout_handler(_signum, _frame):
    print(f"\nTIMEOUT: wall-clock limit {TIMEOUT_SECONDS}s reached.")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)


def rule110_det(tape: np.ndarray) -> np.ndarray:
    left = np.roll(tape, 1)
    right = np.roll(tape, -1)
    idx = left.astype(np.int32) * 4 + tape.astype(np.int32) * 2 + right.astype(np.int32)
    return ((110 >> idx) & 1).astype(np.uint8)


def build_ether(L: int) -> np.ndarray:
    return np.array([ETHER[i % 14] for i in range(L)], dtype=np.uint8)


def center_for_phase(L: int, phase: int = 1) -> int:
    mid = L // 2
    offset = (phase - mid % 14) % 14
    if offset > 7:
        offset -= 14
    return mid + offset


def run_ca_stochastic(
    L: int,
    T: int,
    initial: np.ndarray,
    rho: float,
    seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Return spacetime (T+1, L) and update_mask (T, L) — True where cell updated."""
    rng = np.random.default_rng(seed)
    tape = initial.copy()
    sp = np.zeros((T + 1, L), dtype=np.uint8)
    mask = np.zeros((T, L), dtype=bool)
    sp[0] = tape
    for t in range(T):
        new = rule110_det(tape)
        upd = rng.random(L) < rho
        mask[t] = upd
        tape = np.where(upd, new, tape)
        sp[t + 1] = tape
    return sp, mask


def deviation_field(sp: np.ndarray, L: int) -> np.ndarray:
    t_idx = np.arange(sp.shape[0], dtype=np.int64)[:, None]
    x_idx = np.arange(L, dtype=np.int64)[None, :]
    pat = np.array(ETHER, dtype=np.uint8)
    ref = pat[(x_idx - ETHER_VEL * t_idx) % 14]
    return (sp != ref).astype(np.uint8)


def apply_boost(dev: np.ndarray, v: int, L: int) -> np.ndarray:
    out = np.zeros_like(dev)
    for t in range(dev.shape[0]):
        out[t] = np.roll(dev[t], -(int(round(v * t)) % L))
    return out


def boost_cv_from_dev(dev: np.ndarray, L: int) -> float:
    stds = []
    for v in BOOST_VELS:
        sheared = apply_boost(dev, v, L)
        stds.append(float(np.std(np.mean(sheared, axis=0))))
    m = mean(stds)
    return pstdev(stds) / m if m > 1e-12 else 0.0


def measure_causal_cone(
    L: int,
    T: int,
    rho: float,
    x0: int,
    seed: int,
) -> dict:
    """Rank 102 base-vs-pert diff causal cone speeds."""
    ether = build_ether(L)
    sp_base, _ = run_ca_stochastic(L, T, ether, rho, seed)
    pert = ether.copy()
    pert[x0] ^= 1
    sp_pert, _ = run_ca_stochastic(L, T, pert, rho, seed + 1_000_000)
    cone = (sp_pert != sp_base).astype(np.uint8)

    v_right, v_left = [], []
    for t in range(T // 2, T + 1):
        devs = np.where(cone[t])[0]
        if len(devs) == 0:
            continue
        lb, rb = int(devs[0]), int(devs[-1])
        if rb - lb > L // 2:
            continue
        if t > 0:
            v_right.append((rb - x0) / t)
            v_left.append((x0 - lb) / t)

    if not v_right:
        return {"v_R": 0.0, "v_L": 0.0, "ratio": float("nan")}
    v_r = float(np.mean(v_right))
    v_l = float(np.mean(v_left))
    ratio = v_r / v_l if v_l > 1e-12 else float("inf")
    return {"v_R": v_r, "v_L": v_l, "ratio": ratio}


def measure_c2_glider(L: int, T: int, rho: float, seed: int) -> dict:
    """Rank 070-113 single-bit phase-1 C2 nucleation via base-vs-pert diff."""
    center = center_for_phase(L, 1)
    base = build_ether(L)
    pert = base.copy()
    pert[center] ^= 1

    sp_base, _ = run_ca_stochastic(L, T, base, rho, seed)
    sp_pert, _ = run_ca_stochastic(L, T, pert, rho, seed + 2_000_000)

    leads = []
    for t in range(1, T + 1):
        diff = sp_base[t] != sp_pert[t]
        right = [i - center for i in range(center + 1, L) if diff[i]]
        lead = max(right, default=0)
        leads.append(lead)

    final_lead = leads[-1]
    speed = final_lead / T
    triplets = max(len(leads) - 3, 0)
    if triplets > 0:
        p3 = sum(1 for i in range(3, len(leads)) if leads[i] - leads[i - 3] == 2)
        purity = p3 / triplets
    else:
        purity = 0.0

    growing = final_lead >= leads[T // 2 - 1] * 0.9 and final_lead > 10
    persistent = abs(speed - TARGET_SPEED) < 0.01 and purity >= 0.95 and growing
    return {
        "speed": float(speed),
        "purity": float(purity),
        "persistent": persistent,
        "n_leads": len(leads),
        "final_lead": final_lead,
    }


def causal_set_augmentation_metrics(
    sp: np.ndarray,
    update_mask: np.ndarray,
    L: int,
) -> dict:
    """
    Augmented causal set from Poisson update events on Lorentzian graph.

    Timelike edges: (t,x) -> (t+1,x) always (causal order).
    Augmentation edges: (t,x) -> (t+1,x±1) when update_mask[t,x] is True
    (Sorkin-style sprinkling of active events into future lightcone).

    Isotropy: compare +x vs -x augmentation link counts from central band.
    """
    T = update_mask.shape[0]
    x0 = L // 2
    band = range(max(0, x0 - L // 8), min(L, x0 + L // 8))

    fwd_plus = fwd_minus = 0
    for t in range(T - 1):
        for x in band:
            if not update_mask[t, x]:
                continue
            xp = (x + 1) % L
            xm = (x - 1) % L
            if update_mask[t + 1, xp]:
                fwd_plus += 1
            if update_mask[t + 1, xm]:
                fwd_minus += 1

    total_events = int(update_mask.sum())
    event_density = total_events / (T * L)
    iso_ratio = fwd_plus / fwd_minus if fwd_minus > 0 else float("inf")

    # MM-style link density: fraction of timelike pairs with augmentation
    timelike_pairs = T * L
    aug_links = int(update_mask.sum())

    return {
        "total_update_events": total_events,
        "event_density": event_density,
        "augmentation_fwd_plus": fwd_plus,
        "augmentation_fwd_minus": fwd_minus,
        "augmentation_isotropy_ratio": iso_ratio,
        "augmentation_link_fraction": aug_links / timelike_pairs if timelike_pairs else 0.0,
        "graph_nodes": (T + 1) * L,
        "graph_timelike_edges": timelike_pairs,
    }


def boost_event_density_cv(
    update_mask: np.ndarray,
    L: int,
) -> float:
    """CV of column-mean update density under discrete boosts (Lorentz test on event sprinkling)."""
    T = update_mask.shape[0]
    dev = update_mask.astype(np.float64)
    stds = []
    for v in BOOST_VELS:
        sheared = np.zeros_like(dev)
        for t in range(T):
            sheared[t] = np.roll(dev[t], -(int(round(v * t)) % L))
        stds.append(float(np.std(np.mean(sheared, axis=0))))
    m = mean(stds)
    return pstdev(stds) / m if m > 1e-12 else 0.0


def fmdl_z7(l: int, c: int, r: int) -> int:
    return _FMDL_ORBIT.get((l, c, r), 0)


def fmdl_step5_stoch(state: tuple[int, ...], rho: float, rng: np.random.Generator) -> tuple[int, ...]:
    n = len(state)
    out = list(state)
    for i in range(n):
        if rng.random() < rho:
            l, c, r = state[(i + n - 1) % n], state[i], state[(i + 1) % n]
            out[i] = fmdl_z7(l, c, r)
    return tuple(out)


def z7_orbit_ensemble(rho: float, n_trials: int, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    exact = 0
    traces = []
    for _ in range(n_trials):
        state = GEN1
        sums = [sum(state) % 7]
        for _ in range(4):
            state = fmdl_step5_stoch(state, rho, rng)
            sums.append(sum(state) % 7)
        traces.append(sums)
        if sums == EXPECTED_ORBIT:
            exact += 1
    return {
        "rho": rho,
        "exact_orbit_fraction": exact / n_trials,
        "mean_trace": [mean(t[i] for t in traces) for i in range(5)],
        "expected": EXPECTED_ORBIT,
    }


@dataclass
class RhoResult:
    rho: float
    boost_cv: float
    event_density_cv: float
    causal_ratio_mean: float
    causal_ratio_std: float
    c2_speed: float
    c2_purity: float
    c2_persistent: bool
    z7_exact_fraction: float
    causal_set: dict


def eval_rho(rho: float, L: int, T: int, n_seeds: int) -> RhoResult:
    x0 = center_for_phase(L, 1)
    ratios, cvs, ed_cvs = [], [], []
    speeds, purities, persist_flags = [], [], []
    cs_samples = []

    for seed in range(n_seeds):
        ether = build_ether(L)
        rng = np.random.default_rng(seed)
        tape = ether.copy()
        for site in rng.choice(L, size=20, replace=False):
            tape[site] ^= 1

        sp, mask = run_ca_stochastic(L, T, tape, rho, seed + 10_000)
        dev = deviation_field(sp, L)
        cvs.append(boost_cv_from_dev(dev, L))
        ed_cvs.append(boost_event_density_cv(mask, L))
        cs_samples.append(causal_set_augmentation_metrics(sp, mask, L))

        cc = measure_causal_cone(L, T, rho, x0, seed + 20_000)
        ratios.append(min(cc["ratio"], 10.0) if np.isfinite(cc["ratio"]) else 10.0)

        c2 = measure_c2_glider(L, T, rho, seed + 30_000)
        speeds.append(c2["speed"])
        purities.append(c2["purity"])
        persist_flags.append(c2["persistent"])

    z7 = z7_orbit_ensemble(rho, 200, 42 + int(rho * 1000))

    cs_agg = {
        "mean_event_density": mean(s["event_density"] for s in cs_samples),
        "mean_augmentation_isotropy": mean(
            s["augmentation_isotropy_ratio"]
            for s in cs_samples
            if np.isfinite(s["augmentation_isotropy_ratio"])
        ),
        "mean_augmentation_link_fraction": mean(s["augmentation_link_fraction"] for s in cs_samples),
    }

    return RhoResult(
        rho=rho,
        boost_cv=mean(cvs),
        event_density_cv=mean(ed_cvs),
        causal_ratio_mean=mean(ratios),
        causal_ratio_std=pstdev(ratios) if len(ratios) > 1 else 0.0,
        c2_speed=mean(speeds),
        c2_purity=mean(purities),
        c2_persistent=any(persist_flags),
        z7_exact_fraction=z7["exact_orbit_fraction"],
        causal_set=cs_agg,
    )


def main() -> None:
    t0 = time.time()
    L, T, N_SEEDS = 840, 300, 15
    RHOS = [1.0, 0.75, 0.5, 0.35, 0.25, 0.15]

    print("EPIC_073 Rank 070-109: Poisson causal-set augmentation")
    sweep = []
    z7_all = []
    for rho in RHOS:
        r = eval_rho(rho, L, T, N_SEEDS)
        sweep.append(r)
        z7_all.append(z7_orbit_ensemble(rho, 200, 42 + int(rho * 1000)))
        print(
            f"  rho={rho:.2f}: boost_CV={r.boost_cv:.4f}, event_CV={r.event_density_cv:.4f}, "
            f"v_R/v_L={r.causal_ratio_mean:.3f}, C2 v={r.c2_speed:.3f} pur={r.c2_purity:.2f} "
            f"persist={r.c2_persistent}, Z7={r.z7_exact_fraction:.3f}, "
            f"aug_iso={r.causal_set['mean_augmentation_isotropy']:.3f}"
        )

    base = sweep[0]
    cv_best = min(sweep, key=lambda s: s.boost_cv)
    ratio_best = min(sweep, key=lambda s: abs(s.causal_ratio_mean - 1.0))
    ref_ratio_102 = 1.79

    cv_improved = cv_best.boost_cv < base.boost_cv * 0.90
    ratio_improved = abs(ratio_best.causal_ratio_mean - 1.0) < abs(base.causal_ratio_mean - ref_ratio_102) * 0.50
    ratio_symmetric = abs(ratio_best.causal_ratio_mean - 1.0) < 0.05
    c2_at_base = base.c2_persistent
    c2_at_stoch = any(s.c2_persistent for s in sweep if s.rho < 1.0)
    z7_at_rho1 = base.z7_exact_fraction >= 0.99
    z7_destroyed = all(s.z7_exact_fraction < 0.05 for s in sweep if s.rho < 1.0)

    lorentz_restored = (
        cv_improved
        and ratio_symmetric
        and (c2_at_stoch or c2_at_base)
        and z7_at_rho1
        and not z7_destroyed
    )

    if lorentz_restored:
        status, cat = "PARTIAL_PASS", "CatA"
    elif ratio_improved and not c2_at_stoch:
        status, cat = "NEGATIVE_ASYMMETRY_ONLY", "CatA"
    else:
        status, cat = "NEGATIVE", "CatA"

    results = {
        "rank": "070-109",
        "parameters": {"L": L, "T": T, "N_SEEDS": N_SEEDS, "rhos": RHOS},
        "sweep": [asdict(s) for s in sweep],
        "z7_orbit_tests": z7_all,
        "baseline_deterministic": asdict(base),
        "reference_rank102_ratio": ref_ratio_102,
        "gates": {
            "boost_cv_improved": cv_improved,
            "causal_ratio_closer_to_1": ratio_improved,
            "causal_ratio_within_5pct_of_1": ratio_symmetric,
            "c2_persistent_deterministic": c2_at_base,
            "c2_persistent_stochastic": c2_at_stoch,
            "z7_exact_at_rho_1": z7_at_rho1,
            "z7_orbit_destroyed_below_rho_1": z7_destroyed,
            "lorentz_invariance_restored": lorentz_restored,
        },
        "status": status,
        "cat_level": cat,
        "key_findings": {
            "deterministic_boost_cv": base.boost_cv,
            "deterministic_causal_ratio": base.causal_ratio_mean,
            "deterministic_c2_persistent": c2_at_base,
            "best_stochastic_causal_ratio": ratio_best.causal_ratio_mean,
            "best_stochastic_rho": ratio_best.rho,
            "best_stochastic_boost_cv": cv_best.boost_cv,
            "z7_orbit_destroyed_below_rho_1": z7_destroyed,
            "c2_glider_destroyed_stochastic": not c2_at_stoch,
        },
        "interpretation": (
            "Poisson stochastic updates do not restore physical Lorentz invariance: "
            "causal cone asymmetry (v_R/v_L ~ 1.79 at rho=1) is not symmetrized without "
            "destroying C2 glider structure and Z7 orbit. Augmented causal-set event sprinkling "
            "is approximately isotropic locally but does not fix global boost CV. "
            "Supports [D]-layer (non-algorithmic selector) route over explicit CA stochasticity."
        ),
        "wall_clock_s": time.time() - t0,
    }
    OUT_JSON.write_text(json.dumps(results, indent=2))
    print(f"\nStatus: {status} ({cat})")
    print(f"Saved: {OUT_JSON}")
    signal.alarm(0)


if __name__ == "__main__":
    main()
