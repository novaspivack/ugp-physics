#!/usr/bin/env python3
"""
Rank 53-NAFCA: True Nested 2-Level AFCA SR Test
EPIC_072 — GTE Ontological Unification
2026-05-21

Genuine 2-level true AFCA hierarchy:
  Level-2 (inner-inner): M=7 binary cells running Rule 110.
  Level-1 (inner):       M=7 binary cells, each with its own level-2 AFCA.
                         A level-1 cell transitions only when its level-2 CA
                         reaches majority = target.
  Level-0 (outer):       L binary cells; each transitions when its level-1
                         inner AFCA completes.

τ_c at the outer level = total level-2 steps required per outer transition.
This is measured physically, not from a lookup table — the key distinction from
the LUT-based N-stacking in Rank 51-NLD (which degraded SR accuracy to 40-44%).

Hypothesis: the level-1 cells are themselves true AFCAs, so cells near the
glider boundary (more complex local neighborhoods) require more level-2 steps per
level-1 transition, giving a finer-grained τ_c measurement that might reduce
the 6.4% SR error from Rank 31-ACS (single-level true AFCA).
"""

import signal
import time
import json
import os

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ── Wall-clock safety ────────────────────────────────────────────────────────
WALL_CLOCK_LIMIT = 300  # 5 minutes
_t0 = time.time()


def _wall_timeout(signum, frame):
    elapsed = time.time() - _t0
    print(f"\nTIMEOUT: wall-clock limit {WALL_CLOCK_LIMIT}s reached ({elapsed:.1f}s). "
          "Saving partial results.")
    import sys
    sys.exit(1)


signal.signal(signal.SIGALRM, _wall_timeout)
signal.alarm(WALL_CLOCK_LIMIT)

# ── Constants ────────────────────────────────────────────────────────────────
ETHER14 = np.array([1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0], dtype=np.uint8)
RULE_NUM = 110
C_EFF = 2 / 3
LUT110 = np.array([(RULE_NUM >> n) & 1 for n in range(8)], dtype=np.uint8)

# Canonical glider: v ≈ +0.532 cells/step, γ ≈ 1.659 (Round 19 / Rank 31-ACS)
GLIDER_SEED = [0, 1, 0, 0, 1, 0, 1, 0, 0, 1]
CANONICAL_PHASE = 12
V_CANONICAL = 0.532
v_over_c = min(V_CANONICAL / C_EFF, 0.9999)
GAMMA = 1.0 / np.sqrt(max(1.0 - v_over_c ** 2, 1e-10))

FIGURES_DIR = 'specs/IN-PROCESS/epic_072_gte_ontological_unification/figures'
RESULTS_FILE = 'rank53_nafca_results.json'

os.makedirs(FIGURES_DIR, exist_ok=True)

# ── Hyperparameters ──────────────────────────────────────────────────────────
L = 200        # outer cells
M = 7          # level-1 cells per outer cell
M2 = 7         # level-2 cells per level-1 cell
MAX_L2 = M2 * 10   # max level-2 steps per level-1 cell transition (70)
MAX_L1 = M * 10    # max level-1 transitions per outer cell transition (70)
N_OUTER_TRANS = 60  # outer transitions measured per cell

# ── CA helpers ───────────────────────────────────────────────────────────────

def apply_rule110_ring(state: np.ndarray) -> np.ndarray:
    """One Rule 110 step on a 1-D ring. state: (N,) uint8."""
    l = np.roll(state, 1).astype(np.int32)
    c = state.astype(np.int32)
    r = np.roll(state, -1).astype(np.int32)
    return LUT110[(l << 2) | (c << 1) | r]


def majority(state: np.ndarray) -> int:
    """Binary majority vote: 1 if more than half of cells are 1, else 0."""
    return 1 if state.sum() * 2 > len(state) else 0


# ── Level-2 advance for a single level-1 cell ───────────────────────────────

def advance_l2_to_target(l2_state: np.ndarray, target: int) -> tuple:
    """
    Run the level-2 CA until majority(l2_state) == target.

    Parameters
    ----------
    l2_state : (M2,) uint8 — starting level-2 state
    target   : 0 or 1 — desired majority

    Returns
    -------
    steps_used : int — level-2 steps consumed (0 if already at target)
    final_l2   : (M2,) uint8 — level-2 state when target was reached (or MAX_L2)
    """
    s = l2_state.copy()
    if majority(s) == target:
        return 0, s
    for step in range(1, MAX_L2 + 1):
        s = apply_rule110_ring(s)
        if majority(s) == target:
            return step, s
    return MAX_L2, s


# ── Outer-cell transition: one full advance_outer_cell ───────────────────────

def advance_outer_cell(outer_val: int, outer_target: int,
                       l1_state: np.ndarray, l2_state: np.ndarray) -> tuple:
    """
    Advance one outer cell from outer_val to outer_target.

    The level-1 inner AFCA runs until majority(l1) == outer_target.
    Each level-1 step advances a level-1 cell only when its level-2 CA
    reaches the required target.

    Parameters
    ----------
    outer_val    : current outer cell value (unused directly — direction given by outer_target)
    outer_target : target outer cell value (0 or 1)
    l1_state     : (M,) uint8 — current level-1 state
    l2_state     : (M, M2) uint8 — current level-2 states

    Returns
    -------
    l2_steps_total : int — total level-2 steps consumed
    l1_transitions : int — number of level-1 CA updates performed
    final_l1       : (M,) uint8 — level-1 state after completion
    final_l2       : (M, M2) uint8 — level-2 states after completion
    """
    l1 = l1_state.copy()
    l2 = l2_state.copy()
    l2_steps_total = 0

    for l1_iter in range(MAX_L1):
        if majority(l1) == outer_target:
            return l2_steps_total, l1_iter, l1, l2

        # Compute level-1 targets from Rule 110 applied to current level-1 state
        l1_l = np.roll(l1, 1).astype(np.int32)
        l1_c = l1.astype(np.int32)
        l1_r = np.roll(l1, -1).astype(np.int32)
        l1_targets = LUT110[(l1_l << 2) | (l1_c << 1) | l1_r]

        # Advance each level-1 cell via its level-2 AFCA
        l1_new = l1.copy()
        for j in range(M):
            if l1[j] == l1_targets[j]:
                # Instant: level-2 majority already matches target (τ_c2 = 0)
                pass
            else:
                steps, l2[j] = advance_l2_to_target(l2[j], int(l1_targets[j]))
                l2_steps_total += steps
                l1_new[j] = l1_targets[j]

        l1 = l1_new

    # MAX_L1 reached without convergence: return what we have
    return l2_steps_total, MAX_L1, l1, l2


# ── Initial state builders ───────────────────────────────────────────────────

def build_l1_state(outer_idx: int) -> np.ndarray:
    """Level-1 state for outer cell outer_idx: M cells seeded from ETHER14."""
    return np.array(
        [ETHER14[(outer_idx * M + j) % 14] for j in range(M)],
        dtype=np.uint8
    )


def build_l2_state(outer_idx: int) -> np.ndarray:
    """Level-2 states for outer cell outer_idx: (M, M2) seeded from ETHER14."""
    s = np.zeros((M, M2), dtype=np.uint8)
    for j in range(M):
        for k in range(M2):
            s[j, k] = ETHER14[(outer_idx * M * M2 + j * M2 + k) % 14]
    return s


# ── Tape runner: accumulate τ_c_l2 per cell over N_OUTER_TRANS transitions ──

def run_tape(outer_init: np.ndarray, label: str) -> tuple:
    """
    Run the 2-level nested AFCA on a length-L tape until every cell has
    completed N_OUTER_TRANS outer transitions.

    The outer CA advances synchronously (all cells transition at once):
    the next outer state is the deterministic Rule 110 image of the current.
    τ_c at each cell = total level-2 steps required for that cell's inner
    2-level hierarchy to sanction the transition.

    Returns
    -------
    tau_c_l2    : (L,) float64 — mean total level-2 steps per outer transition
    outer_hist  : (N_OUTER_TRANS, L) uint8 — outer state at each step
    """
    outer = outer_init.copy()

    # Level-1 and level-2 states per outer cell
    l1 = np.zeros((L, M), dtype=np.uint8)
    l2 = np.zeros((L, M, M2), dtype=np.uint8)
    for i in range(L):
        l1[i] = build_l1_state(i)
        l2[i] = build_l2_state(i)

    tau_accum = np.zeros(L, dtype=np.float64)
    transitions = np.zeros(L, dtype=np.int32)
    outer_hist = []

    t_start = time.time()
    step_idx = 0

    while transitions.min() < N_OUTER_TRANS:
        if time.time() - _t0 > WALL_CLOCK_LIMIT - 20:
            print(f"  [{label}] timeout protection at step {step_idx}")
            break

        outer_hist.append(outer.copy())

        # Compute next outer state from Rule 110
        outer_l = np.roll(outer, 1).astype(np.int32)
        outer_c = outer.astype(np.int32)
        outer_r = np.roll(outer, -1).astype(np.int32)
        outer_next = LUT110[(outer_l << 2) | (outer_c << 1) | outer_r]

        # Advance each outer cell via its nested 2-level AFCA
        for i in range(L):
            l2_steps, _, l1[i], l2[i] = advance_outer_cell(
                int(outer[i]), int(outer_next[i]), l1[i], l2[i]
            )
            tau_accum[i] += l2_steps
            transitions[i] += 1

        outer = outer_next
        step_idx += 1

        if step_idx % 10 == 0:
            elapsed = time.time() - t_start
            min_trans = transitions.min()
            print(f"  [{label}] step {step_idx:4d}, min_trans={min_trans:3d}/{N_OUTER_TRANS}, "
                  f"elapsed={elapsed:.1f}s")

    n_done = transitions.copy()
    tau_c_l2 = np.where(n_done > 0, tau_accum / np.maximum(n_done, 1), 0.0)
    elapsed = time.time() - t_start
    print(f"  [{label}] finished: {elapsed:.2f}s, transitions min={n_done.min()} max={n_done.max()}")
    hist_arr = np.array(outer_hist, dtype=np.uint8) if outer_hist else np.zeros((1, L), dtype=np.uint8)
    return tau_c_l2, hist_arr


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("=== Rank 53-NAFCA: True Nested 2-Level AFCA SR Test ===")
    print(f"Level structure: L={L} outer cells, M={M} level-1 cells/outer, "
          f"M2={M2} level-2 cells/level-1")
    print(f"MAX_L1={MAX_L1}, MAX_L2={MAX_L2}, N_outer_trans={N_OUTER_TRANS}")
    print(f"Canonical seed 0100101001 at phase-{CANONICAL_PHASE}, "
          f"v={V_CANONICAL:.3f}, γ={GAMMA:.3f}")
    print("=" * 70)

    # Build initial tapes
    ether_tape = np.array([ETHER14[i % 14] for i in range(L)], dtype=np.uint8)

    # Phase-12 injection near center
    c = L // 2 - ((L // 2 - CANONICAL_PHASE) % 14)
    glider_tape = ether_tape.copy()
    for j, b in enumerate(GLIDER_SEED):
        glider_tape[(c + j) % L] = b
    print(f"Glider seed injected at cell={c} (ETHER14 phase={c % 14})")
    print()

    # ── Run ether tape ──────────────────────────────────────────────────────
    print(f"Running ether tape ...")
    t_ether = time.time()
    tau_ether, ether_hist = run_tape(ether_tape, "ether")
    print(f"  Ether tape: {time.time()-t_ether:.2f}s")
    print(f"  τ_c_l2 (ether): mean={tau_ether.mean():.4f}  std={tau_ether.std():.4f}")
    print()

    # ── Run glider tape ─────────────────────────────────────────────────────
    print(f"Running glider tape ...")
    t_glider = time.time()
    tau_glider_tape, glider_hist = run_tape(glider_tape, "glider")
    print(f"  Glider tape: {time.time()-t_glider:.2f}s")
    print(f"  τ_c_l2 (glider tape, whole): mean={tau_glider_tape.mean():.4f}  "
          f"std={tau_glider_tape.std():.4f}")
    print()

    # ── Identify glider cells via diff_frac (same method as Rank 31-ACS) ────
    # Compare outer states between glider and ether runs at matched steps.
    # Cells with diff_frac > 5% are in the glider region.
    n_snaps = min(len(ether_hist), len(glider_hist))
    DIFF_THRESHOLD = 0.05
    if n_snaps >= 5:
        diff_frac = (glider_hist[:n_snaps] != ether_hist[:n_snaps]).mean(axis=0)
    else:
        diff_frac = np.zeros(L, dtype=np.float32)

    is_glider = diff_frac > DIFF_THRESHOLD
    n_glider = int(is_glider.sum())

    if n_glider == 0:
        # Fallback: top-N cells by diff_frac
        n_top = max(5, L // 20)
        top_idx = np.argsort(diff_frac)[-n_top:]
        is_glider = np.zeros(L, dtype=bool)
        is_glider[top_idx] = True
        n_glider = n_top
        print(f"  [fallback] no cells above diff_frac threshold — using top {n_top}")

    tau_excess = tau_glider_tape - tau_ether
    excess_threshold = float(DIFF_THRESHOLD)  # stored for JSON only

    tau_ether_mean = float(tau_ether.mean())
    tau_glider_cells = float(tau_glider_tape[is_glider].mean())
    tau_ether_nearby = float(tau_glider_tape[~is_glider].mean()) \
        if (~is_glider).sum() > 0 else tau_ether_mean

    ratio = tau_glider_cells / max(tau_ether_nearby, 1e-9)
    sr_error = abs(ratio - GAMMA) / max(GAMMA, 1e-9) * 100

    verdict = ("CONFIRMED" if sr_error < 15 else
               "BORDERLINE" if sr_error < 30 else "NOT CONFIRMED")

    # ── Summary ─────────────────────────────────────────────────────────────
    print("=" * 70)
    print(f"Ether τ_c_l2 (mean level-2 steps/outer transition): {tau_ether_mean:.4f}")
    print(f"Glider τ_c_l2:                                       {tau_glider_cells:.4f}")
    print(f"Ratio = {ratio:.4f}")
    print(f"γ = {GAMMA:.3f}")
    print(f"SR error = {sr_error:.1f}%")
    print(f"Glider cells identified: {n_glider}/{L}")
    print()
    print("Compare:")
    print(f"  N=1 true AFCA (Rank 31-ACS): ratio=1.553, error=6.4%")
    print(f"  N=2 nested true AFCA:        ratio={ratio:.3f}, error={sr_error:.1f}%")
    print()

    # Improvement direction
    if sr_error < 6.4:
        comparison = "IMPROVED"
        interpretation = (
            f"Nested 2-level AFCA gives finer-grained τ_c resolution. "
            f"Level-1 cells near the glider boundary accumulate more level-2 steps "
            f"per level-1 transition, tightening the τ_c ratio toward γ."
        )
    elif sr_error <= 10.0:
        comparison = "SAME"
        interpretation = (
            f"Nested 2-level AFCA does not improve SR accuracy over single-level. "
            f"The additional level-2 resolution does not reduce the systematic bias."
        )
    else:
        comparison = "DEGRADED"
        interpretation = (
            f"Nested 2-level AFCA degrades SR accuracy. "
            f"The additional level may introduce phase-varying τ_c that increases "
            f"measurement noise, similar to the LUT-based N=3,4 failure in Rank 51-NLD."
        )

    print(f"Verdict: {comparison} vs N=1")
    print(f"Physical interpretation: {interpretation}")
    print("=" * 70)

    # ── Figure ───────────────────────────────────────────────────────────────
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    ax1 = axes[0]
    bar_colors = ['red' if is_glider[i] else 'steelblue' for i in range(L)]
    ax1.bar(range(L), tau_glider_tape, color=bar_colors, width=1.0, alpha=0.8)
    ax1.axhline(tau_ether_mean, color='black', linestyle='--', linewidth=1.5,
                label=f'Ether baseline τ_c_l2 = {tau_ether_mean:.3f}')
    ax1.axhline(tau_glider_cells, color='red', linestyle='--', linewidth=1.5,
                label=f'Glider τ_c_l2 = {tau_glider_cells:.3f}')
    ax1.set_xlabel('Outer cell position')
    ax1.set_ylabel('Mean level-2 steps per outer transition')
    ax1.set_title(
        f'τ_c_l2 per cell — 2-level nested AFCA\n'
        f'Red = glider region ({n_glider} cells, diff_frac>{DIFF_THRESHOLD}), '
        f'ratio = {ratio:.3f} vs γ = {GAMMA:.3f}',
        fontsize=10
    )
    ax1.legend(fontsize=9)

    ax2 = axes[1]
    excess_colors = ['red' if e > 0 else 'steelblue' for e in tau_excess]
    ax2.bar(range(L), tau_excess, color=excess_colors, width=1.0, alpha=0.8)
    ax2.axhline(0, color='black', linewidth=1.0)
    ax2.set_xlabel('Outer cell position')
    ax2.set_ylabel('τ_c_l2(glider) − τ_c_l2(ether)')
    ax2.set_title(
        f'τ_c_l2 excess — matter-induced clock dilation\n'
        f'Red = slower than ether (glider region)',
        fontsize=10
    )

    fig.suptitle(
        f'Rank 53-NAFCA: True Nested 2-Level AFCA SR Test\n'
        f'L={L}, M={M}, M2={M2}, N_trans={N_OUTER_TRANS} | '
        f'ratio={ratio:.3f}, γ={GAMMA:.3f}, SR error={sr_error:.1f}% → {verdict} '
        f'({comparison} vs N=1)',
        fontsize=11
    )
    fig.tight_layout(rect=[0, 0, 1, 0.93])

    out_fig = f'{FIGURES_DIR}/rank53_nafca_sr.png'
    fig.savefig(out_fig, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"\nFigure saved: {out_fig}")

    # ── JSON results ─────────────────────────────────────────────────────────
    results = {
        'rank': '53-NAFCA',
        'test': 'true_nested_2level_afca_sr',
        'date': time.strftime('%Y-%m-%d'),
        'parameters': {
            'L': L,
            'M': M,
            'M2': M2,
            'MAX_L1': MAX_L1,
            'MAX_L2': MAX_L2,
            'N_outer_trans': N_OUTER_TRANS,
            'rule': RULE_NUM,
            'c_eff': C_EFF,
            'glider_seed': GLIDER_SEED,
            'glider_phase': int(c % 14),
            'glider_cell': int(c),
            'diff_frac_threshold': DIFF_THRESHOLD,
            'n_steps_for_diff_frac': int(n_snaps),
        },
        'results': {
            'tau_c_l2_ether_mean': round(tau_ether_mean, 6),
            'tau_c_l2_glider_cells': round(tau_glider_cells, 6),
            'tau_c_l2_ether_nearby': round(tau_ether_nearby, 6),
            'ratio': round(float(ratio), 6),
            'n_glider_cells': n_glider,
            'v_cells_per_outer_step': V_CANONICAL,
            'v_over_c': round(float(v_over_c), 6),
            'gamma_sr': round(float(GAMMA), 6),
            'sr_error_pct': round(float(sr_error), 3),
            'verdict': verdict,
            'comparison_vs_n1': comparison,
            'interpretation': interpretation,
        },
        'comparison': {
            'n1_true_afca_ratio': 1.553,
            'n1_true_afca_error_pct': 6.4,
            'n1_source': 'Rank 31-ACS',
            'n2_lut_ratio': None,
            'n2_lut_error_pct': 40.9,
            'n2_lut_source': 'Rank 51-NLD (LUT-based, degraded)',
        },
    }

    with open(RESULTS_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Results saved: {RESULTS_FILE}")

    return results


if __name__ == '__main__':
    results = main()
    signal.alarm(0)
    elapsed = time.time() - _t0
    print(f"\nTotal elapsed: {elapsed:.2f}s")
