#!/usr/bin/env python3
"""
Rank 58-CONT: Continuous Inner CA (No Re-Seeding) SR Test
EPIC_072 — GTE Ontological Unification
2026-05-22

Tests whether removing the ETHER14 re-seed between outer transitions improves
the SR time-dilation ratio.  In Rank 31-ACS the inner CA was re-seeded from
ETHER14 after every outer transition, discarding accumulated state.  Here the
inner CA runs continuously: it starts from ETHER14 once and is never reset.
After each outer transition the outer state and target are updated, tau_count
is reset to 0, but the inner state continues from wherever it currently is.

Two variants tested:
  (1) Continuous synchronous inner CA  — standard parallel Rule 110 inner step
  (2) Continuous Gauss-Seidel inner CA — sequential in-place update within each row

Reference values:
  Rank 31-ACS  (re-seed, synchronous):  ratio≈1.553, error=6.4%
  Rank 56-DAV  (re-seed, GS):           ratio≈1.565, error=5.7%
  γ = 1.659  (v=0.532 cells/step, c_eff=2/3)
"""

import json
import signal
import sys
import time

import numpy as np

# ── Wall-clock safety ────────────────────────────────────────────────────────
WALL_CLOCK_LIMIT = 175
_t0 = time.time()


def _wall_timeout(signum, frame):
    elapsed = time.time() - _t0
    print(f"\nWall-clock limit {WALL_CLOCK_LIMIT}s reached ({elapsed:.1f}s). Saving partial results.")
    sys.exit(1)


signal.signal(signal.SIGALRM, _wall_timeout)
signal.alarm(WALL_CLOCK_LIMIT)

# ── Constants ────────────────────────────────────────────────────────────────
ETHER14 = np.array([1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0], dtype=np.uint8)
RULE_NUM = 110
LUT = np.array([(RULE_NUM >> n) & 1 for n in range(8)], dtype=np.uint8)
C_EFF = 2.0 / 3.0

GLIDER_SEED = [0, 1, 0, 0, 1, 0, 1, 0, 0, 1]
CANONICAL_PHASE = 12
V_CANONICAL = 0.532   # cells/outer step (Round 19 canonical)
V_OVER_C = min(V_CANONICAL / C_EFF, 0.9999)
GAMMA = 1.0 / np.sqrt(max(1.0 - V_OVER_C ** 2, 1e-10))

OUTER_L = 200
M = 7
N_TRANS = 100
MAX_INNER_PER_TRANS = M * 20   # hard cap per transition to prevent runaway
DIFF_THRESHOLD = 0.05

RESULTS_FILE = 'rank58_cont_results.json'


# ── Rule 110 helpers ─────────────────────────────────────────────────────────

def _make_targets(outer: np.ndarray) -> np.ndarray:
    L = len(outer)
    l = outer[(np.arange(L) - 1) % L].astype(np.int32)
    c = outer.astype(np.int32)
    r = outer[(np.arange(L) + 1) % L].astype(np.int32)
    return LUT[(l << 2) | (c << 1) | r]


def _inner_step_sync(inner: np.ndarray) -> np.ndarray:
    """Synchronous (parallel) Rule 110 step for the (L, M) inner array."""
    ni = np.empty_like(inner)
    for j in range(M):
        lj = inner[:, (j - 1) % M].astype(np.int32)
        cj = inner[:, j].astype(np.int32)
        rj = inner[:, (j + 1) % M].astype(np.int32)
        ni[:, j] = LUT[(lj << 2) | (cj << 1) | rj]
    return ni


def _inner_step_gs(inner: np.ndarray) -> np.ndarray:
    """Gauss-Seidel (sequential in-place) Rule 110 step for (L, M) inner array."""
    result = inner.copy()
    for j in range(M):
        lj = result[:, (j - 1) % M].astype(np.int32)
        cj = result[:, j].astype(np.int32)
        rj = inner[:, (j + 1) % M].astype(np.int32)  # right: not yet updated
        result[:, j] = LUT[(lj << 2) | (cj << 1) | rj]
    return result


def _majority(inner: np.ndarray) -> np.ndarray:
    """(L,) uint8: majority vote over M inner cells for each outer cell."""
    return (inner.sum(axis=1) * 2 > M).astype(np.uint8)


# ── Continuous AFCA (core) ───────────────────────────────────────────────────

def run_continuous_afca(initial_tape: np.ndarray, inner_step_fn, label: str):
    """
    True AFCA with continuous inner CA — no re-seeding between outer transitions.

    Parameters
    ----------
    initial_tape   : (OUTER_L,) uint8 initial outer state
    inner_step_fn  : callable(inner) -> inner_new, vectorised over (L, M)
    label          : string for progress prints

    Returns
    -------
    tau_c_per_cell : (OUTER_L,) float64 — mean inner steps per outer transition
    n_trans        : (OUTER_L,) int32 — number of completed transitions per cell
    """
    L = OUTER_L
    outer = np.array(initial_tape, dtype=np.uint8).copy()

    # Inner CA initialised from ETHER14 exactly once — never reset
    inner = np.zeros((L, M), dtype=np.uint8)
    for i in range(L):
        for j in range(M):
            inner[i, j] = ETHER14[((i * M) + j) % 14]

    targets = _make_targets(outer)
    tau_count = np.zeros(L, dtype=np.int32)
    tau_accum = np.zeros(L, dtype=np.float64)
    n_trans = np.zeros(L, dtype=np.int32)

    # Phase A: instant-completion check flag (set at start and after each completion)
    needs_check = np.ones(L, dtype=bool)

    istep = 0
    t_start = time.time()

    while True:
        # ── timeout guard ────────────────────────────────────────────────────
        if time.time() - t_start > 160 or (time.time() - _t0) > WALL_CLOCK_LIMIT - 10:
            print(f"  [{label}] timeout protection at istep={istep}, "
                  f"min_trans={n_trans.min()}")
            break

        # ── Phase A: instant completions (τ_c = 0) ──────────────────────────
        # After a transition completes, inner state continues and might already
        # satisfy the new target without any further inner steps.
        advance_skip = np.zeros(L, dtype=bool)
        if needs_check.any():
            maj = _majority(inner)
            instant = needs_check & (maj == targets)
            if instant.any():
                idx_a = np.where(instant)[0]
                outer[idx_a] = maj[idx_a]
                tau_accum[idx_a] += tau_count[idx_a].astype(np.float64)
                n_trans[idx_a] += 1
                # Recompute targets from current (mixed-time) outer
                l_nb = outer[(idx_a - 1) % L]
                r_nb = outer[(idx_a + 1) % L]
                targets[idx_a] = LUT[
                    (l_nb.astype(np.int32) << 2) |
                    (outer[idx_a].astype(np.int32) << 1) |
                    r_nb.astype(np.int32)
                ]
                tau_count[idx_a] = 0
                # inner state NOT reset — continues from current state
                advance_skip[idx_a] = True
                needs_check[idx_a] = True   # re-check on next iteration
            needs_check[needs_check & ~instant] = False

        # ── Phase B: advance inner CA for non-skipped cells ─────────────────
        adv = ~advance_skip
        if adv.any():
            new_inner = inner_step_fn(inner)
            inner[adv] = new_inner[adv]
            tau_count[adv] += 1
        istep += 1

        # ── Phase C: check completion ────────────────────────────────────────
        maj = _majority(inner)
        done = adv & ((maj == targets) | (tau_count >= MAX_INNER_PER_TRANS))
        if done.any():
            idx_c = np.where(done)[0]
            outer[idx_c] = maj[idx_c]
            tau_accum[idx_c] += tau_count[idx_c].astype(np.float64)
            n_trans[idx_c] += 1
            l_nb = outer[(idx_c - 1) % L]
            r_nb = outer[(idx_c + 1) % L]
            targets[idx_c] = LUT[
                (l_nb.astype(np.int32) << 2) |
                (outer[idx_c].astype(np.int32) << 1) |
                r_nb.astype(np.int32)
            ]
            tau_count[idx_c] = 0
            # inner state NOT reset — continuous
            needs_check[idx_c] = True

        # ── termination ──────────────────────────────────────────────────────
        if n_trans.min() >= N_TRANS:
            break
        if istep > N_TRANS * MAX_INNER_PER_TRANS * 3:
            print(f"  [{label}] failsafe at istep={istep}")
            break

    tau_c_per_cell = np.where(
        n_trans > 0, tau_accum / np.maximum(n_trans, 1), 0.0
    )
    return tau_c_per_cell, n_trans


# ── Cell identification ──────────────────────────────────────────────────────

def identify_glider_cells(glider_tape, ether_tape):
    """
    Identify glider cells from initial tape difference.
    Returns boolean mask of length OUTER_L.
    """
    diff = np.abs(np.array(glider_tape, dtype=np.int32)
                  - np.array(ether_tape, dtype=np.int32))
    return diff > 0


# ── SR ratio computation ─────────────────────────────────────────────────────

def compute_sr_stats(tau_glider_run, tau_ether_run, is_glider):
    """
    Compute τ_c ratio and SR error from two runs.

    Uses ether cells in the glider-tape run as the reference (same run, same
    dynamics), matching Rank 31-ACS methodology.
    """
    tau_g = float(tau_glider_run[is_glider].mean()) if is_glider.sum() > 0 else 0.0
    tau_e_gt = float(tau_glider_run[~is_glider].mean()) if (~is_glider).sum() > 0 else 0.0
    tau_e_pure = float(tau_ether_run.mean())
    ratio = tau_g / max(tau_e_gt, 1e-9)
    sr_error = abs(ratio - GAMMA) / GAMMA * 100
    return {
        'tau_ether_pure': tau_e_pure,
        'tau_ether_in_glider_tape': tau_e_gt,
        'tau_glider_cells': tau_g,
        'ratio': ratio,
        'sr_error_pct': sr_error,
    }


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 65)
    print("Rank 58-CONT: Continuous Inner CA SR Test")
    print(f"L={OUTER_L}, M={M}, N_trans={N_TRANS}, max_inner/trans={MAX_INNER_PER_TRANS}")
    print(f"γ = {GAMMA:.4f}  (v={V_CANONICAL}, c_eff={C_EFF})")
    print(f"Reference: Rank 31-ACS ratio=1.553 (6.4%), Rank 56-DAV ratio=1.565 (5.7%)")
    print("=" * 65)

    # ── Build tapes ──────────────────────────────────────────────────────────
    ether_tape = np.array([ETHER14[i % 14] for i in range(OUTER_L)], dtype=np.uint8)
    c = OUTER_L // 2 - ((OUTER_L // 2 - CANONICAL_PHASE) % 14)
    glider_tape = ether_tape.copy()
    for j, b in enumerate(GLIDER_SEED):
        glider_tape[(c + j) % OUTER_L] = b
    print(f"Glider injected at cell={c} (phase={c % 14})")

    is_glider = identify_glider_cells(glider_tape, ether_tape)
    n_glider = int(is_glider.sum())
    print(f"Initial glider cells: {n_glider}")

    all_results = {}

    # ── Variant 1: Continuous synchronous inner CA ───────────────────────────
    print("\n[1/4] Continuous synchronous — ether tape ...")
    t1 = time.time()
    tau_cont_sync_ether, n_trans_cse = run_continuous_afca(
        ether_tape, _inner_step_sync, "cont-sync-ether")
    print(f"  Done in {time.time()-t1:.1f}s | min_trans={n_trans_cse.min()} "
          f"| mean_tau={tau_cont_sync_ether.mean():.4f}")

    print("[2/4] Continuous synchronous — glider tape ...")
    t2 = time.time()
    tau_cont_sync_glider, n_trans_csg = run_continuous_afca(
        glider_tape, _inner_step_sync, "cont-sync-glider")
    print(f"  Done in {time.time()-t2:.1f}s | min_trans={n_trans_csg.min()} "
          f"| mean_tau={tau_cont_sync_glider.mean():.4f}")

    stats_cont_sync = compute_sr_stats(tau_cont_sync_glider, tau_cont_sync_ether, is_glider)

    # ── Variant 2: Continuous Gauss-Seidel inner CA ──────────────────────────
    print("\n[3/4] Continuous Gauss-Seidel — ether tape ...")
    t3 = time.time()
    tau_cont_gs_ether, n_trans_cge = run_continuous_afca(
        ether_tape, _inner_step_gs, "cont-gs-ether")
    print(f"  Done in {time.time()-t3:.1f}s | min_trans={n_trans_cge.min()} "
          f"| mean_tau={tau_cont_gs_ether.mean():.4f}")

    print("[4/4] Continuous Gauss-Seidel — glider tape ...")
    t4 = time.time()
    tau_cont_gs_glider, n_trans_cgg = run_continuous_afca(
        glider_tape, _inner_step_gs, "cont-gs-glider")
    print(f"  Done in {time.time()-t4:.1f}s | min_trans={n_trans_cgg.min()} "
          f"| mean_tau={tau_cont_gs_glider.mean():.4f}")

    stats_cont_gs = compute_sr_stats(tau_cont_gs_glider, tau_cont_gs_ether, is_glider)

    # ── Summary table ─────────────────────────────────────────────────────────
    print("\n" + "=" * 65)
    print("=== Rank 58-CONT: Continuous Inner CA SR Test ===")
    print(f"γ = {GAMMA:.4f}")
    print()
    header = f"{'Method':<34} | {'τ_c ether':>9} | {'τ_c glider':>10} | {'ratio':>6} | {'SR error':>8}"
    print(header)
    print("-" * len(header))
    rows = [
        ("Re-seed synchronous (Rank 31-ACS)",
         0.329, 0.511, 1.553, 6.4),
        ("Re-seed Gauss-Seidel (Rank 56-DAV)",
         0.329, 0.514, 1.565, 5.7),
        ("Continuous synchronous [THIS]",
         stats_cont_sync['tau_ether_in_glider_tape'],
         stats_cont_sync['tau_glider_cells'],
         stats_cont_sync['ratio'],
         stats_cont_sync['sr_error_pct']),
        ("Continuous Gauss-Seidel [THIS]",
         stats_cont_gs['tau_ether_in_glider_tape'],
         stats_cont_gs['tau_glider_cells'],
         stats_cont_gs['ratio'],
         stats_cont_gs['sr_error_pct']),
    ]
    for name, te, tg, r, err in rows:
        print(f"{name:<34} | {te:>9.4f} | {tg:>10.4f} | {r:>6.4f} | {err:>7.1f}%")
    print("=" * 65)

    # ── Verdicts ──────────────────────────────────────────────────────────────
    def verdict_line(stats, ref_error=6.4):
        err = stats['sr_error_pct']
        r = stats['ratio']
        if err < 2.0:
            return f"CONTINUOUS AFCA NEAR-EXACT SR: ratio={r:.4f}, error={err:.1f}%."
        elif err < ref_error - 0.5:
            improvement = ref_error - err
            return (f"CONTINUOUS AFCA IMPROVES SR: ratio={r:.4f}, error={err:.1f}% "
                    f"(improvement {improvement:.1f}pp vs re-seed {ref_error:.1f}%).")
        elif err < ref_error + 0.5:
            return (f"CONTINUOUS AFCA SAME AS RE-SEED: ratio={r:.4f}, "
                    f"error={err:.1f}% ≈ {ref_error:.1f}%.")
        else:
            degradation = err - ref_error
            return (f"CONTINUOUS AFCA WORSE: ratio={r:.4f}, error={err:.1f}% "
                    f"({degradation:.1f}pp worse than re-seed {ref_error:.1f}%).")

    print(f"\nContinuous synchronous: {verdict_line(stats_cont_sync)}")
    print(f"Continuous Gauss-Seidel: {verdict_line(stats_cont_gs, ref_error=5.7)}")

    # Physical interpretation
    print("\nPhysical interpretation:")
    cs_ratio = stats_cont_sync['ratio']
    gs_ratio = stats_cont_gs['ratio']
    if abs(cs_ratio - GAMMA) < 0.03 or abs(gs_ratio - GAMMA) < 0.03:
        print("  Re-seeding discards history that encodes SR dilation. The continuous inner CA")
        print("  accumulates dynamical state that distinguishes glider from ether cells.")
    elif cs_ratio < 1.553 and gs_ratio < 1.553:
        print("  Continuous inner CA over-mixes: accumulated state obscures glider/ether")
        print("  contrast. The re-seed from ETHER14 resets to a canonical reference that")
        print("  preserves the transition-type discrimination.")
    elif abs(cs_ratio - 1.553) < 0.01 and abs(gs_ratio - 1.565) < 0.01:
        print("  Continuous inner CA gives the same result as re-seeded: the majority-vote")
        print("  τ_c signal is determined by transition-type asymmetry, not accumulated state.")
        print("  After many transitions the inner CA ergodically explores the same distribution")
        print("  regardless of initial state, making re-seeding irrelevant.")
    else:
        print(f"  Mixed result: synchronous ratio={cs_ratio:.4f}, GS ratio={gs_ratio:.4f}.")
        print("  Inner CA history partially alters glider/ether discrimination but does not")
        print("  systematically close the gap to γ.")

    # ── JSON output ───────────────────────────────────────────────────────────
    elapsed = time.time() - _t0
    results = {
        'rank': '58-CONT',
        'test': 'continuous_inner_ca_sr',
        'date': time.strftime('%Y-%m-%d'),
        'parameters': {
            'outer_L': OUTER_L,
            'M': M,
            'n_transitions': N_TRANS,
            'max_inner_per_trans': MAX_INNER_PER_TRANS,
            'rule': RULE_NUM,
            'c_eff': C_EFF,
            'v_canonical': V_CANONICAL,
            'gamma': round(GAMMA, 6),
            'glider_seed': GLIDER_SEED,
            'glider_phase': int(c % 14),
            'glider_cell': int(c),
            'diff_threshold': DIFF_THRESHOLD,
        },
        'results': {
            'continuous_sync': {
                **{k: round(v, 6) for k, v in stats_cont_sync.items()},
                'n_glider_cells': n_glider,
                'min_transitions_ether': int(n_trans_cse.min()),
                'min_transitions_glider': int(n_trans_csg.min()),
            },
            'continuous_gauss_seidel': {
                **{k: round(v, 6) for k, v in stats_cont_gs.items()},
                'n_glider_cells': n_glider,
                'min_transitions_ether': int(n_trans_cge.min()),
                'min_transitions_glider': int(n_trans_cgg.min()),
            },
        },
        'reference': {
            'rank31_acs_reseed_sync': {'ratio': 1.553, 'sr_error_pct': 6.4},
            'rank56_dav_reseed_gs':   {'ratio': 1.565, 'sr_error_pct': 5.7},
            'gamma': round(GAMMA, 6),
        },
        'elapsed_s': round(elapsed, 1),
    }

    with open(RESULTS_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved: {RESULTS_FILE}")

    return results


if __name__ == '__main__':
    results = main()
    signal.alarm(0)
    print(f"\nTotal elapsed: {time.time() - _t0:.1f}s")
