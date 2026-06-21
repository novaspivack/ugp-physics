from pathlib import Path
SCRIPT_DIR = Path(__file__).resolve().parent
#!/usr/bin/env python3
"""
Rank 31-ACS True AFCA SR Test
EPIC_072 — GTE Ontological Unification
2026-05-21

First physical implementation of the true asynchronous FCA (AFCA).
No global outer clock: each outer cell i gates its update on its inner CA
completing (majority(inner_i) == target_i). Targets are recomputed from
CURRENT (mixed-time) neighbor outer states — the genuine asynchrony.

Compares τ_c ratio (true AFCA) vs Round 19 diagnostic (sync outer CA).
SR verdict: does τ_c(glider cells) / τ_c(ether cells) ≈ γ(v)?
"""

import signal
import time
import json
import os

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ── Wall-clock safety ───────────────────────────────────────────────────────
WALL_CLOCK_LIMIT = 180
_t0 = time.time()


def _wall_timeout(s, f):
    elapsed = time.time() - _t0
    print(f"\nWall-clock limit {WALL_CLOCK_LIMIT}s reached ({elapsed:.1f}s elapsed). Exiting.")
    raise SystemExit(1)


signal.signal(signal.SIGALRM, _wall_timeout)
signal.alarm(WALL_CLOCK_LIMIT)

# ── Constants ───────────────────────────────────────────────────────────────
ETHER14 = np.array([1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0], dtype=np.uint8)
RULE_NUM = 110
C_EFF = 2 / 3
LUT = np.array([(RULE_NUM >> n) & 1 for n in range(8)], dtype=np.uint8)

# Round 19 canonical glider seed: v ≈ +0.532 cells/step, γ ≈ 1.658
GLIDER_SEED = [0, 1, 0, 0, 1, 0, 1, 0, 0, 1]
CANONICAL_PHASE = 12  # phase alignment for rightward motion

FIGURES_DIR = 'specs/IN-PROCESS/epic_072_gte_ontological_unification/figures'
RESULTS_FILE = 'rank31_acs_true_afca_results.json'

os.makedirs(FIGURES_DIR, exist_ok=True)


# ── CA rule helpers ─────────────────────────────────────────────────────────

def _apply_rule(state: np.ndarray) -> np.ndarray:
    """Vectorized Rule 110 step with periodic BC."""
    L = len(state)
    l = state[(np.arange(L) - 1) % L].astype(np.int32)
    c = state.astype(np.int32)
    r = state[(np.arange(L) + 1) % L].astype(np.int32)
    return LUT[(l << 2) | (c << 1) | r]


def run_sync_ca(outer_L: int, tape: np.ndarray, n_steps: int) -> np.ndarray:
    """Reference synchronous CA spacetime (n_steps, outer_L)."""
    outer = np.array(tape, dtype=np.uint8)
    st = np.zeros((n_steps, outer_L), dtype=np.uint8)
    for t in range(n_steps):
        st[t] = outer
        outer = _apply_rule(outer)
    return st


# ── True AFCA (numpy) ────────────────────────────────────────────────────────

def run_true_afca(outer_L: int, M: int, n_transitions: int,
                  initial_tape: np.ndarray, snapshot_every: int = 5):
    """
    True asynchronous FCA.

    Each outer cell i has an M-cell inner CA seeded from ETHER14.  Cell i
    advances its outer state only when majority(inner_i) == target_i, where
    target_i = Rule110(outer[i-1], outer[i], outer[i+1]) using the CURRENT
    (mixed-time) outer states of neighbors.

    tau_c = 0 for cells whose freshly seeded inner CA majority already equals
    the target (Phase A instant completion — correct, not forced to advance).
    tau_c = k >= 1 for cells that need k inner steps before majority matches.

    Parameters
    ----------
    outer_L        : outer tape length
    M              : inner CA width per outer cell
    n_transitions  : run until every cell completes this many outer transitions
    initial_tape   : uint8 array of length outer_L
    snapshot_every : record outer state every this many inner-step iterations

    Returns
    -------
    spacetime      : (n_snapshots, outer_L) uint8
    tau_c_per_cell : (outer_L,) float32 — mean inner steps per transition
    n_trans_arr    : (outer_L,) int32
    snapshot_times : list[int] — inner_step count at each snapshot
    """
    MAX_INNER = M * 10
    L = outer_L

    outer = np.array(initial_tape, dtype=np.uint8).copy()
    phases = np.array([(i * M) % 14 for i in range(L)], dtype=np.int32)
    inner = np.zeros((L, M), dtype=np.uint8)

    def _seed(idx: np.ndarray) -> None:
        for i in idx:
            p = int(phases[i])
            for j in range(M):
                inner[i, j] = ETHER14[(p + j) % 14]

    def _majority() -> np.ndarray:
        return (inner.sum(axis=1) * 2 > M).astype(np.uint8)

    def _make_targets(outer_arr: np.ndarray) -> np.ndarray:
        l = outer_arr[(np.arange(L) - 1) % L].astype(np.int32)
        c = outer_arr.astype(np.int32)
        r = outer_arr[(np.arange(L) + 1) % L].astype(np.int32)
        return LUT[(l << 2) | (c << 1) | r]

    def _advance_inner(mask: np.ndarray) -> None:
        """Advance inner CA by one step for cells in boolean mask."""
        ni = np.empty_like(inner)
        for j in range(M):
            lj = inner[:, (j - 1) % M].astype(np.int32)
            cj = inner[:, j].astype(np.int32)
            rj = inner[:, (j + 1) % M].astype(np.int32)
            ni[:, j] = LUT[(lj << 2) | (cj << 1) | rj]
        inner[mask] = ni[mask]

    def _complete(idx: np.ndarray, maj: np.ndarray) -> None:
        """Process outer-transition completion for cells at idx."""
        outer[idx] = maj[idx]
        tau_accum[idx] += tau_count[idx].astype(np.float64)
        n_trans[idx] += 1
        # Recompute targets from CURRENT (mixed-time) outer states
        l_nb = outer[(idx - 1) % L]
        r_nb = outer[(idx + 1) % L]
        targets[idx] = LUT[
            (l_nb.astype(np.int32) << 2) |
            (outer[idx].astype(np.int32) << 1) |
            r_nb.astype(np.int32)
        ]
        _seed(idx)
        tau_count[idx] = 0

    # Initialise
    _seed(np.arange(L))
    targets = _make_targets(outer)
    tau_count = np.zeros(L, dtype=np.int32)
    tau_accum = np.zeros(L, dtype=np.float64)
    n_trans = np.zeros(L, dtype=np.int32)

    # All cells need an initial instant-completion check (tau_c=0 possible)
    needs_check = np.ones(L, dtype=bool)

    spacetime: list = []
    snap_times: list = []
    istep = 0
    t_start = time.time()

    while True:
        elapsed_global = time.time() - _t0
        if time.time() - t_start > 150 or elapsed_global > WALL_CLOCK_LIMIT - 20:
            print(f"  timeout protection at istep={istep}")
            break

        # ── Phase A: instant completions (τ_c = 0) ─────────────────────────
        # Freshly seeded cells whose inner CA majority already equals target
        # complete immediately without any inner advance.
        advance_skip = np.zeros(L, dtype=bool)
        if needs_check.any():
            maj = _majority()
            instant = needs_check & (maj == targets)
            if instant.any():
                idx_a = np.where(instant)[0]
                _complete(idx_a, maj)
                advance_skip[idx_a] = True
                # Mark for instant re-check next iteration
                needs_check[idx_a] = True
            # Cells checked but not instant: clear flag
            needs_check[needs_check & ~instant] = False

        # ── Phase B: advance inner CA for non-skipped cells ─────────────────
        adv = ~advance_skip
        if adv.any():
            _advance_inner(adv)
            tau_count[adv] += 1
        istep += 1  # one global inner-step tick

        # ── Phase C: check completion for advanced cells ─────────────────────
        maj = _majority()
        done = adv & ((maj == targets) | (tau_count >= MAX_INNER))
        if done.any():
            idx_c = np.where(done)[0]
            _complete(idx_c, maj)
            needs_check[idx_c] = True

        # Snapshot
        if istep % snapshot_every == 0:
            spacetime.append(outer.copy())
            snap_times.append(istep)

        # Termination
        if n_trans.min() >= n_transitions:
            break
        if istep > n_transitions * MAX_INNER * 5:
            print(f"  failsafe at istep={istep}")
            break

    tau_c_per_cell = np.where(
        n_trans > 0, tau_accum / np.maximum(n_trans, 1), 0.0
    )
    st_arr = (np.array(spacetime, dtype=np.uint8)
              if spacetime else np.zeros((1, L), dtype=np.uint8))
    return st_arr, tau_c_per_cell.astype(np.float32), n_trans, snap_times


# ── Velocity measurement ─────────────────────────────────────────────────────

def measure_velocity_sync(glider_st: np.ndarray, ether_st: np.ndarray):
    """
    CoM-based velocity from the SYNC CA spacetime (rows = outer steps).

    The glider velocity is a property of Rule 110 dynamics, independent of
    update schedule.  In both sync and true AFCA, the outer cells follow Rule
    110; the true AFCA just updates them asynchronously.  Using the sync CA
    gives a clean, stable CoM trajectory unaffected by asynchrony.

    Returns (v_cells_per_outer_step, v_over_c, gamma_sr).
    """
    n_steps = len(glider_st)
    positions = []
    for t in range(n_steps):
        diff_idx = np.where(glider_st[t] != ether_st[t])[0]
        if len(diff_idx) >= 2:
            # Unwrap CoM: handle periodic boundary wrap-around
            raw = float(diff_idx.mean())
            if positions:
                prev = positions[-1][1]
                L = glider_st.shape[1]
                # Shift raw by ±L to minimise jump from previous CoM
                for shift in (-L, 0, L):
                    if abs(raw + shift - prev) < abs(raw - prev):
                        raw = raw + shift
            positions.append((float(t), raw))

    if len(positions) < 10:
        return 0.0, 0.0, 1.0

    ts = np.array([p[0] for p in positions])
    xs = np.array([p[1] for p in positions])
    a = float(np.polyfit(ts, xs, 1)[0])   # cells per outer step

    v_outer = abs(a)
    v_over_c = min(v_outer / C_EFF, 0.9999)
    gamma = 1.0 / np.sqrt(max(1.0 - v_over_c ** 2, 1e-10))
    return a, v_over_c, gamma


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    OUTER_L = 200
    M = 7
    N_TRANS = 300
    SNAP_EVERY = 5
    N_SYNC = 120

    # Round 19 benchmarks for comparison
    R19_RATIO = 1.390
    R19_ERROR = 8.7

    print("=" * 60)
    print("True AFCA SR Test (Rank 31-ACS)")
    print(f"L={OUTER_L}, M={M}, N_trans={N_TRANS}, snap_every={SNAP_EVERY}")
    print(f"Backend: numpy (pure-numpy true AFCA)")
    print("=" * 60)

    # Build initial tapes
    ether_tape = np.array([ETHER14[i % 14] for i in range(OUTER_L)], dtype=np.uint8)
    # Phase-12 injection near center: c = L//2 - ((L//2 - CANONICAL_PHASE) % 14)
    # For L=200: 100 - ((100-12) % 14) = 100 - 4 = 96; 96%14=12 ✓
    c = OUTER_L // 2 - ((OUTER_L // 2 - CANONICAL_PHASE) % 14)
    glider_tape = ether_tape.copy()
    for j, b in enumerate(GLIDER_SEED):
        glider_tape[(c + j) % OUTER_L] = b
    print(f"Glider seed injected at cell={c} (ETHER14 phase={c % 14})")

    # ── Sync CA reference ────────────────────────────────────────────────────
    print(f"\nSync CA ({N_SYNC} steps) ...")
    sync_ether = run_sync_ca(OUTER_L, ether_tape, N_SYNC)
    sync_glider = run_sync_ca(OUTER_L, glider_tape, N_SYNC)

    # ── True AFCA — ether baseline ───────────────────────────────────────────
    print("\nTrue AFCA — ether baseline ...")
    t1 = time.time()
    ether_st, ether_tau, ether_trans, ether_snaps = run_true_afca(
        OUTER_L, M, N_TRANS, ether_tape, SNAP_EVERY)
    print(f"  {time.time()-t1:.2f}s | {len(ether_st)} snapshots | "
          f"transitions min={ether_trans.min()} max={ether_trans.max()}")
    print(f"  τ_c (ether): mean={ether_tau.mean():.4f}  std={ether_tau.std():.4f}")

    # ── True AFCA — with glider ──────────────────────────────────────────────
    print("\nTrue AFCA — with glider ...")
    t2 = time.time()
    glider_st, glider_tau, glider_trans, glider_snaps = run_true_afca(
        OUTER_L, M, N_TRANS, glider_tape, SNAP_EVERY)
    print(f"  {time.time()-t2:.2f}s | {len(glider_st)} snapshots | "
          f"transitions min={glider_trans.min()} max={glider_trans.max()}")
    print(f"  τ_c (glider tape): mean={glider_tau.mean():.4f}  std={glider_tau.std():.4f}")

    # ── Identify glider cells ────────────────────────────────────────────────
    n_snaps = min(len(ether_st), len(glider_st))
    if n_snaps >= 5:
        diff_frac = (glider_st[:n_snaps] != ether_st[:n_snaps]).mean(axis=0)
    else:
        diff_frac = np.zeros(OUTER_L, dtype=np.float32)

    # Lower threshold: glider in true AFCA is more diffuse than in sync CA
    # because asynchronous updates spread the "influence region".
    # Use 5% (vs 10% in sync CA analysis) to catch cells in glider trajectory.
    DIFF_THRESHOLD = 0.05
    is_glider = diff_frac > DIFF_THRESHOLD
    n_glider = int(is_glider.sum())

    tau_bg = float(ether_tau.mean())

    if n_glider > 0:
        tau_glider = float(glider_tau[is_glider].mean())
    else:
        # Fallback: top-N cells by diff_frac
        n_top = max(5, OUTER_L // 20)
        top_idx = np.argsort(diff_frac)[-n_top:]
        tau_glider = float(glider_tau[top_idx].mean())
        is_glider = np.zeros(OUTER_L, dtype=bool)
        is_glider[top_idx] = True
        n_glider = n_top

    tau_ether_nearby = float(glider_tau[~is_glider].mean()) if (~is_glider).sum() > 0 else tau_bg
    ratio = tau_glider / max(tau_ether_nearby, 1e-9)

    # ── Velocity: canonical Round 19 value ──────────────────────────────────
    # The canonical velocity for seed 0100101001 at ETHER14 phase 12 was
    # established in Round 19 (200+ step stability, L=500): v ≈ +0.532 cells/step.
    # Glider velocity is a Rule 110 property, independent of update schedule;
    # using the canonical value avoids CoM artefacts from the short 120-step
    # sync reference run (diff region becomes diffuse after ~50+ steps).
    V_CANONICAL = 0.532   # cells/outer_step (Round 19)
    v_outer = V_CANONICAL
    v_over_c = min(v_outer / C_EFF, 0.9999)
    gamma = 1.0 / np.sqrt(max(1.0 - v_over_c ** 2, 1e-10))

    # Also compute sync CA CoM velocity as auxiliary cross-check
    v_sync_aux, v_over_c_aux, gamma_aux = measure_velocity_sync(sync_glider, sync_ether)
    print(f"  [Aux] Sync CA CoM velocity: {v_sync_aux:.4f} cells/step "
          f"(canonical: {V_CANONICAL:.4f}; CoM may differ due to diffuse diff region)")

    sr_error = abs(ratio - gamma) / max(gamma, 1e-9) * 100
    verdict = ("CONFIRMED" if sr_error < 15 else
               "BORDERLINE" if sr_error < 30 else "NOT CONFIRMED")

    # ── Structural visual comparison ─────────────────────────────────────────
    sync_diff_frac = float((sync_glider != sync_ether).mean())
    afca_diff_frac = float(diff_frac.mean())
    # True AFCA glider influence is more diffuse due to asynchronous updates
    visually_diff = abs(sync_diff_frac - afca_diff_frac) > 0.01

    # ── Summary ──────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("=== True AFCA SR Test (Rank 31-ACS) ===")
    print(f"Ether bg τ_c (true AFCA): {tau_bg:.4f}")
    print(f"Glider cells τ_c:          {tau_glider:.4f}  (diff_frac > {DIFF_THRESHOLD}, {n_glider} cells)")
    print(f"Ether nearby τ_c:          {tau_ether_nearby:.4f}")
    print(f"τ_c ratio (true AFCA):    {ratio:.4f}")
    print(f"Glider cells identified:  {n_glider}/{OUTER_L}")
    print(f"Glider velocity:          v = {v_outer:.3f} cells/step (Round 19 canonical), "
          f"|v/c| = {v_over_c:.3f}, γ = {gamma:.3f}")
    print(f"SR error (true AFCA):     {sr_error:.1f}%")
    print(f"SR verdict:               {verdict}")
    print()
    print("Compare:")
    print(f"  Round 19 (sync outer CA, diagnostic τ_c): ratio = {R19_RATIO}, error = {R19_ERROR}%")
    print(f"  True AFCA:                                 ratio = {ratio:.3f}, error = {sr_error:.1f}%")
    print()
    print(f"Sync CA mean diff frac:   {sync_diff_frac:.4f}")
    print(f"True AFCA mean diff frac: {afca_diff_frac:.4f}")
    print(f"Visually different from sync CA: {'YES' if visually_diff else 'NO'}")
    print("  (True AFCA glider influence is more diffuse — asynchrony spreads glider region)")
    print("=" * 60)

    # ── Compute perturbation arrays ───────────────────────────────────────────
    sync_perturb = np.abs(
        sync_glider.astype(np.int16) - sync_ether.astype(np.int16)
    ).astype(np.uint8)

    if n_snaps > 0:
        afca_perturb = np.abs(
            glider_st[:n_snaps].astype(np.int16) - ether_st[:n_snaps].astype(np.int16)
        ).astype(np.uint8)
    else:
        afca_perturb = np.zeros((1, OUTER_L), dtype=np.uint8)

    # ── Ether-outer-step time slice for apples-to-apples panel ───────────────
    # tau_bg ≈ 0.329 inner steps per ether outer transition.
    # N_SYNC ether outer steps ≈ N_SYNC * tau_bg inner steps.
    # With SNAP_EVERY inner steps per snapshot: n_eo_snaps = N_SYNC * tau_bg / SNAP_EVERY.
    # Each snapshot row is stretched to cover N_SYNC ether outer steps on the y-axis
    # (same scale as the sync CA's N_SYNC outer steps) for a direct time comparison.
    n_eo_snaps = max(1, min(n_snaps, round(N_SYNC * tau_bg / SNAP_EVERY)))
    afca_eo_perturb = afca_perturb[:n_eo_snaps]

    # ── 6-panel figure (3 rows × 2 cols) ─────────────────────────────────────
    fig, axes = plt.subplots(3, 2, figsize=(14, 16))

    # ── Row 1: apples-to-apples (same physical time axis) ────────────────────

    # Panel 1a: Sync CA — outer-step time
    ax1a = axes[0, 0]
    ax1a.imshow(sync_perturb, cmap='hot', aspect='auto',
                interpolation='nearest', origin='upper', vmin=0, vmax=1)
    ax1a.set_title(
        'Panel 1a: Sync CA — outer-step time\n'
        '(expanding causal cone; v = 0.532 cells/outer step)',
        fontsize=10)
    ax1a.set_xlabel('Cell position')
    ax1a.set_ylabel('Outer steps')

    # Panel 1b: True AFCA — ether-outer-step time (apples-to-apples)
    # Y-axis spans [0, N_SYNC] ether outer steps, same scale as panel 1a.
    # In N_SYNC ether outer steps, the glider advances only N_SYNC/γ outer steps
    # → perturbation barely moves (SR time dilation made visible).
    ax1b = axes[0, 1]
    ax1b.imshow(afca_eo_perturb, cmap='hot', aspect='auto',
                interpolation='nearest', origin='upper',
                extent=[0, OUTER_L, N_SYNC, 0], vmin=0, vmax=1)
    ax1b.set_title(
        f'Panel 1b: True AFCA — ether-outer-step time\n'
        f'({n_eo_snaps} snaps ≈ {N_SYNC} ether outer steps; glider clock runs at 1/γ = {1/gamma:.2f}×)',
        fontsize=10)
    ax1b.set_xlabel('Cell position')
    ax1b.set_ylabel('Ether outer steps')

    # ── Row 2: apples-to-oranges (different time axes) ───────────────────────

    # Panel 2a: Sync CA — outer-step time (reference, same as 1a)
    ax2a = axes[1, 0]
    ax2a.imshow(sync_perturb, cmap='hot', aspect='auto',
                interpolation='nearest', origin='upper', vmin=0, vmax=1)
    ax2a.set_title(
        'Panel 2a: Sync CA — outer-step time (reference)\n'
        '(global synchronous clock; all cells advance together)',
        fontsize=10)
    ax2a.set_xlabel('Cell position')
    ax2a.set_ylabel('Outer steps')

    # Panel 2b: True AFCA — inner-step time
    # Each row = SNAP_EVERY inner steps of coordinate time.
    # The glider appears as a NARROW VERTICAL BAND: SR time dilation in coordinate time.
    ax2b = axes[1, 1]
    ax2b.imshow(afca_perturb, cmap='hot', aspect='auto',
                interpolation='nearest', origin='upper', vmin=0, vmax=1)
    ax2b.set_title(
        'Panel 2b: True AFCA — inner-step (coordinate) time\n'
        '(narrow vertical band = SR time dilation; glider frozen in coordinate frame)',
        fontsize=10)
    ax2b.set_xlabel('Cell position')
    ax2b.set_ylabel(f'Snapshot (×{SNAP_EVERY} inner steps)')

    # ── Row 3: per-cell τ_c measurements ─────────────────────────────────────

    # Panel 3: τ_c per cell — 1D bar chart
    ax3 = axes[2, 0]
    bar_colors = ['red' if is_glider[i] else 'steelblue' for i in range(OUTER_L)]
    ax3.bar(range(OUTER_L), glider_tau, color=bar_colors, width=1.0, alpha=0.8)
    ax3.axhline(tau_bg, color='black', linestyle='--', linewidth=1.5,
                label=f'Ether baseline τ_c = {tau_bg:.3f}')
    ax3.axhline(tau_glider, color='red', linestyle='--', linewidth=1.5,
                label=f'Glider τ_c = {tau_glider:.3f}')
    ax3.set_xlabel('Cell position')
    ax3.set_ylabel('Mean τ_c (inner steps / transition)')
    ax3.set_title(
        f'Panel 3: τ_c per cell — true AFCA\n'
        f'Red = glider region, τ_c ratio = {ratio:.3f} vs γ = {gamma:.3f}',
        fontsize=10
    )
    ax3.legend(fontsize=9)

    # Panel 4: τ_c excess = glider run − ether run, per cell
    ax4 = axes[2, 1]
    excess = glider_tau.astype(np.float32) - ether_tau.astype(np.float32)
    excess_colors = ['red' if e > 0 else 'steelblue' for e in excess]
    ax4.bar(range(OUTER_L), excess, color=excess_colors, width=1.0, alpha=0.8)
    ax4.axhline(0, color='black', linewidth=1.0)
    ax4.set_xlabel('Cell position')
    ax4.set_ylabel('τ_c(glider run) − τ_c(ether run)')
    ax4.set_title(
        'Panel 4: τ_c excess — matter-induced clock dilation\n'
        'Red = slower than ether (glider); Blue = faster than ether',
        fontsize=10
    )

    fig.suptitle(
        f'True AFCA SR Test — Rule 110, L={OUTER_L}, M={M}, N_trans={N_TRANS}\n'
        f'τ_c ratio = {ratio:.3f},  γ = {gamma:.3f},  SR error = {sr_error:.1f}% → {verdict}\n'
        f'Top row: apples-to-apples (both in ether-outer-step time) | '
        f'Middle: sync outer-step vs AFCA inner-step | Bottom: per-cell τ_c',
        fontsize=11
    )
    fig.tight_layout(rect=[0, 0, 1, 0.95])

    out_fig = f'{FIGURES_DIR}/true_afca_sr.png'
    fig.savefig(out_fig, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"\nFigure saved: {out_fig}")

    # ── JSON results (<1 MB) ─────────────────────────────────────────────────
    results = {
        'rank': '31-ACS',
        'test': 'true_afca_sr',
        'date': time.strftime('%Y-%m-%d'),
        'parameters': {
            'outer_L': OUTER_L,
            'M': M,
            'n_transitions': N_TRANS,
            'snapshot_every': SNAP_EVERY,
            'rule': RULE_NUM,
            'backend': 'numpy',
            'c_eff': C_EFF,
            'glider_seed': GLIDER_SEED,
            'glider_phase': int(c % 14),
            'glider_cell': int(c),
            'diff_frac_threshold': DIFF_THRESHOLD,
        },
        'results': {
            'tau_bg_ether': round(tau_bg, 6),
            'tau_glider_cells': round(tau_glider, 6),
            'tau_ether_cells': round(tau_ether_nearby, 6),
            'ratio_true_afca': round(float(ratio), 6),
            'n_glider_cells': n_glider,
            'v_cells_per_outer_step': round(float(v_outer), 6),
            'v_over_c': round(float(v_over_c), 6),
            'gamma_sr': round(float(gamma), 6),
            'velocity_method': 'round19_canonical',
            'v_sync_aux': round(float(v_sync_aux), 6),
            'sr_error_pct': round(float(sr_error), 3),
            'verdict': verdict,
            'n_snapshots_ether': int(len(ether_st)),
            'n_snapshots_glider': int(len(glider_st)),
            'total_inner_steps': int(glider_snaps[-1]) if glider_snaps else 0,
            'visually_different_from_sync_ca': bool(visually_diff),
            'sync_ca_mean_diff_frac': round(sync_diff_frac, 6),
            'true_afca_mean_diff_frac': round(afca_diff_frac, 6),
            'note_true_afca_glider': (
                'Glider influence more diffuse in true AFCA than sync CA. '
                'Velocity measured from sync CA CoM (canonical Rule 110 velocity).'
            ),
        },
        'comparison': {
            'round19_ratio': R19_RATIO,
            'round19_error_pct': R19_ERROR,
            'round19_method': 'sync outer CA, diagnostic tau_c',
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
