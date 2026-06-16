#!/usr/bin/env python3
"""
Rank 60-WHIST: Exponentially Weighted History Inner CA Seeding SR Test
EPIC_072 — GTE Ontological Unification
2026-05-22

Tests whether seeding the inner CA from an exponentially decayed causal
history h_t = Σ_{s≤t} α^(t-s) · outer_state(s) improves SR accuracy.

Connection to MFRR §26: h_t ∝ effective information density ρ at time t.
ρ_ether ≈ 0.43 (ETHER14 average), ρ_glider > 0.5 (more transitions).

Failure mode of Rank 59 (flat M=7 window):
  - Window too short for velocity estimation (need ~14+ steps for one ether period)
  - Flat weighting: no temporal gradient
  - Result: unscaled τ_c ratio 8.59 (5× overshoot vs γ=1.659)

Weighted history fix:
  - h_t = α·h_{t-1} + (1-α)·outer_state(t)  [EMA update, h ∈ [0,1]]
  - For α close to 1: long memory, converges to running average of all past states
  - n_ones = round(h_val * M) → seed majority reflects time-averaged state
  - Sweep α ∈ {0.80, 0.90, 0.95, 0.98, 0.99}
"""

import json
import signal
import sys
import time

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ── Wall-clock timeout ────────────────────────────────────────────────────────
WALL_LIMIT = 175
_t0 = time.time()


def _timeout_handler(signum, frame):
    elapsed = time.time() - _t0
    print(f"\nWall-clock limit {WALL_LIMIT}s reached ({elapsed:.1f}s). Exiting.")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(WALL_LIMIT)

# ── Constants ─────────────────────────────────────────────────────────────────
ETHER14 = np.array([1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0], dtype=np.uint8)
LUT110 = np.array([(110 >> i) & 1 for i in range(8)], dtype=np.uint8)
M = 7
OUTER_L = 500
C_EFF = 2 / 3
MAX_INNER = 50
N_WARMUP_STEPS = 100  # steps to warm up ether history before main run
N_RUN_STEPS = 150     # outer CA steps per seed trial
MIN_STABLE = 30       # minimum diff-active steps required

ALPHA_VALUES = [0.80, 0.90, 0.95, 0.98, 0.99]

CANONICAL_SEED = '0100101001'
V_CANONICAL = 0.532
GAMMA_TARGET = 1.0 / np.sqrt(1.0 - (V_CANONICAL / C_EFF) ** 2)

# Phase-12 aligned injection center
ether_base = np.array([ETHER14[i % 14] for i in range(OUTER_L)], dtype=np.uint8)
C_INJ = OUTER_L // 2 - ((OUTER_L // 2 - 12) % 14)

RESULTS_FILE = 'rank60_whist_results.json'

# ── CA helpers ────────────────────────────────────────────────────────────────

def run_outer(state: np.ndarray) -> np.ndarray:
    """Vectorized Rule 110 step (periodic BC)."""
    l = np.roll(state, 1).astype(np.int32)
    c = state.astype(np.int32)
    r = np.roll(state, -1).astype(np.int32)
    return LUT110[(l << 2) | (c << 1) | r]


def majority_batch(seeds: np.ndarray) -> np.ndarray:
    """Majority vote for a batch of (n, M) binary arrays. Returns length-n uint8."""
    return (seeds.sum(axis=1) * 2 > M).astype(np.uint8)


def batch_tau_c_from_h(h_vals: np.ndarray, targets: np.ndarray,
                        max_steps: int = MAX_INNER) -> np.ndarray:
    """
    Compute τ_c for a batch of cells using their scalar weighted-history values.

    Parameters
    ----------
    h_vals  : 1D float array ∈ [0, 1], the EMA value for each cell
    targets : 1D uint8 array, target majority bit for each cell
    max_steps : inner CA step limit

    The M-cell seed for cell i: first n_ones[i] = round(h_vals[i]*M) bits are 1,
    rest 0. Deterministic and scale-preserving.

    Returns float array of τ_c values.
    """
    n = len(h_vals)
    if n == 0:
        return np.array([], dtype=np.float32)

    # Build seeds: (n, M) — sorted binary (all 1s first, then 0s)
    n_ones = np.clip(np.round(h_vals * M).astype(np.int32), 0, M)
    seeds = np.zeros((n, M), dtype=np.uint8)
    for i in range(M):
        seeds[:, i] = (i < n_ones).astype(np.uint8)

    results = np.full(n, max_steps, dtype=np.float32)
    done = np.zeros(n, dtype=bool)

    states = seeds.copy()
    for step in range(max_steps):
        maj = majority_batch(states)
        newly_done = (~done) & (maj == targets)
        results[newly_done] = step
        done |= newly_done
        if done.all():
            break
        active = ~done
        s = states[active]
        l = np.roll(s, 1, axis=1).astype(np.int32)
        c = s.astype(np.int32)
        r = np.roll(s, -1, axis=1).astype(np.int32)
        states[active] = LUT110[(l << 2) | (c << 1) | r]

    return results


# ── Ether baseline history initialization ────────────────────────────────────

def build_ether_baseline_history(alpha: float) -> tuple[np.ndarray, np.ndarray]:
    """
    Warm up exponential history on pure ether tape for N_WARMUP_STEPS steps.

    Returns (h_init, s_init) ready for the main run.
    h_init[i] ∈ [0,1] is the EMA of the ether at cell i after warm-up.
    s_init is the outer state after warm-up.
    """
    s = ether_base.copy()
    h = np.zeros(OUTER_L, dtype=np.float64)
    for _ in range(N_WARMUP_STEPS):
        h = alpha * h + (1.0 - alpha) * s.astype(np.float64)
        s = run_outer(s)
    return h.astype(np.float32), s


# ── SR test for a single seed ─────────────────────────────────────────────────

def test_seed_whist(seed_str: str, h_ether_init: np.ndarray,
                    alpha: float, ether_sample_stride: int = 20) -> dict | None:
    """
    SR test for one width-10 seed using exponentially weighted history seeding.

    h_tape[i] tracks the EMA of outer_state(i) over all past steps.
    h_ref[i]  tracks the same for the pure ether reference tape.

    τ_c is measured from the *weighted-history* EMA of the *tape* (not the ref),
    using the tape's current h_tape as the inner-CA seed.
    """
    seed_arr = np.array([int(b) for b in seed_str], dtype=np.uint8)
    tape = ether_base.copy()
    for j, bit in enumerate(seed_arr):
        tape[(C_INJ + j) % OUTER_L] = bit

    s_tape = tape.copy()
    s_ref = ether_base.copy()
    # Both histories start from the ether-warm baseline
    h_tape = h_ether_init.copy()
    h_ref = h_ether_init.copy()

    positions, g_taus, e_taus = [], [], []

    for _ in range(N_RUN_STEPS):
        s_tape_next = run_outer(s_tape)
        s_ref_next = run_outer(s_ref)

        # Update EMAs before τ_c measurement (use current step's state)
        h_tape = (alpha * h_tape + (1.0 - alpha) * s_tape.astype(np.float32))
        h_ref = (alpha * h_ref + (1.0 - alpha) * s_ref.astype(np.float32))

        diff = s_tape != s_ref
        diff_pos = np.where(diff)[0]

        if 2 <= len(diff_pos) <= 60:
            positions.append(float(diff_pos.mean()))

            g_vals = batch_tau_c_from_h(h_tape[diff_pos],
                                         s_tape_next[diff_pos].astype(np.uint8))
            g_taus.append(float(g_vals.mean()))

            ndiff_pos = np.where(~diff)[0][::ether_sample_stride]
            if len(ndiff_pos) > 0:
                e_vals = batch_tau_c_from_h(h_ref[ndiff_pos],
                                             s_ref_next[ndiff_pos].astype(np.uint8))
                e_taus.append(float(e_vals.mean()))
            else:
                e_taus.append(0.4)

        s_tape = s_tape_next
        s_ref = s_ref_next

    if len(positions) < MIN_STABLE:
        return None

    v = float(np.polyfit(np.arange(len(positions)), np.array(positions), 1)[0])
    v_over_c = abs(v / C_EFF)
    if v_over_c >= 1.0:
        return None

    gam = 1.0 / np.sqrt(1.0 - v_over_c ** 2)
    g_mean = float(np.mean(g_taus)) if g_taus else None
    e_mean = float(np.mean(e_taus)) if e_taus else None
    ratio = g_mean / e_mean if (g_mean and e_mean and e_mean > 0) else None

    return {'v': v, 'v_over_c': v_over_c, 'gamma': gam,
            'ratio': ratio, 'n_stable': len(positions),
            'g_tau_mean': g_mean, 'e_tau_mean': e_mean}


# ── Full 1024-seed search ─────────────────────────────────────────────────────

def run_alpha_sweep(alpha: float) -> dict:
    """Run full 1024-seed SR search for one α value."""
    t_alpha = time.time()
    print(f"\n=== α = {alpha} ===")

    h_ether_init, _ = build_ether_baseline_history(alpha)

    # Background τ_c: pure ether, no glider
    s_bg = ether_base.copy()
    h_bg = h_ether_init.copy()
    bg_taus = []
    for step in range(N_RUN_STEPS):
        s_next = run_outer(s_bg)
        h_bg = alpha * h_bg + (1.0 - alpha) * s_bg.astype(np.float32)
        if step >= 10:
            samp = np.arange(0, OUTER_L, 20)
            bg_taus.append(float(
                batch_tau_c_from_h(h_bg[samp], s_next[samp].astype(np.uint8)).mean()
            ))
        s_bg = s_next
    bg_tau = float(np.mean(bg_taus)) if bg_taus else 0.0
    print(f"  Background τ_c (ether): {bg_tau:.4f}")

    hi_v = []
    lo_v = []

    for ic in range(1024):
        if time.time() - _t0 > WALL_LIMIT - 20:
            print(f"  [time budget] stopping at ic={ic}")
            break
        seed_str = bin(ic)[2:].zfill(10)
        res = test_seed_whist(seed_str, h_ether_init, alpha)
        if res is None:
            continue
        if 1.3 <= res['gamma'] <= 2.0:
            hi_v.append((seed_str, res))
        elif res['v_over_c'] < 0.1 and res['n_stable'] >= MIN_STABLE:
            lo_v.append((seed_str, res))

    print(f"  hi-v seeds (γ∈[1.3,2.0]): {len(hi_v)}")
    print(f"  lo-v reference seeds:      {len(lo_v)}")

    # Paired SR errors (top-5 hi × top-3 lo)
    pairs = []
    if hi_v and lo_v:
        hi_v.sort(key=lambda x: -x[1]['v_over_c'])
        hi_set = hi_v[:5]
        lo_set = lo_v[:3]
        for hi_s, hi_r in hi_set:
            for lo_s, lo_r in lo_set:
                if hi_r['ratio'] is None or lo_r['ratio'] is None:
                    continue
                p = hi_r['ratio'] / lo_r['ratio']
                q = hi_r['gamma'] / lo_r['gamma']
                e = abs(p - q) / q * 100.0
                pairs.append({'hi_seed': hi_s, 'lo_seed': lo_s,
                               'paired_ratio': round(p, 6),
                               'sr_prediction': round(q, 6),
                               'error_pct': round(e, 2)})

    pairs_sorted = sorted(pairs, key=lambda p: p['error_pct'])

    all_errs = [p['error_pct'] for p in pairs]
    mean_err = float(np.mean(all_errs)) if all_errs else 999.0
    best_err = float(np.min(all_errs)) if all_errs else 999.0

    if all_errs:
        ok15 = sum(1 for e in all_errs if e < 15)
        print(f"  Paired SR: {len(pairs)} pairs, mean={mean_err:.1f}%, "
              f"best={best_err:.1f}%, {ok15}/{len(pairs)} < 15%")
        if pairs_sorted:
            best = pairs_sorted[0]
            print(f"  Best pair: {best['hi_seed']} vs {best['lo_seed']}: "
                  f"ratio={best['paired_ratio']:.4f}, "
                  f"pred={best['sr_prediction']:.4f}, "
                  f"err={best['error_pct']:.1f}%")
    else:
        ok15 = 0
        print(f"  No paired comparison (insufficient hi-v or lo-v seeds).")

    mean_hi_ratio = None
    if hi_v:
        ratios = [r['ratio'] for _, r in hi_v if r['ratio'] is not None]
        mean_hi_ratio = float(np.mean(ratios)) if ratios else None

    elapsed = time.time() - t_alpha
    print(f"  Elapsed: {elapsed:.1f}s")

    return {
        'alpha': alpha,
        'bg_tau_ether': round(bg_tau, 6),
        'n_hi_v': len(hi_v),
        'n_lo_v': len(lo_v),
        'n_pairs': len(pairs),
        'mean_sr_error_pct': round(mean_err, 3),
        'best_sr_error_pct': round(best_err, 3),
        'n_pairs_under_15pct': ok15,
        'mean_hi_v_ratio': round(mean_hi_ratio, 6) if mean_hi_ratio else None,
        'pairs_top5': pairs_sorted[:5],
        'elapsed_s': round(elapsed, 2),
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 65)
    print("=== Rank 60-WHIST: Exponentially Weighted History SR Test ===")
    print(f"OUTER_L={OUTER_L}, M={M}, MAX_INNER={MAX_INNER}")
    print(f"γ target = {GAMMA_TARGET:.4f}  (v/c = {V_CANONICAL/C_EFF:.4f})")
    print(f"α sweep: {ALPHA_VALUES}")
    print(f"Rank 31-ACS baseline: ratio=1.553, error=6.4%")
    print("=" * 65)

    BASELINE_ERROR = 6.4

    results_by_alpha = {}

    for alpha in ALPHA_VALUES:
        if time.time() - _t0 > WALL_LIMIT - 30:
            print(f"\nTime budget exhausted before α={alpha}. Stopping sweep.")
            break
        results_by_alpha[alpha] = run_alpha_sweep(alpha)

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 65)
    print("=== Summary ===")
    print(f"Baseline (Rank 31-ACS ETHER14 re-seed): error = {BASELINE_ERROR}%\n")
    print(f"{'α':>5}  {'bg_τ':>7}  {'hi':>5}  {'lo':>5}  {'pairs':>6}  "
          f"{'mean%':>7}  {'best%':>7}  {'verdict':}")
    print("-" * 65)

    best_alpha = None
    best_err = 999.0

    for alpha, r in sorted(results_by_alpha.items()):
        me = r['mean_sr_error_pct']
        be = r['best_sr_error_pct']
        verdict = ("IMPROVED" if me < BASELINE_ERROR
                   else "SAME" if abs(me - BASELINE_ERROR) < 1.0
                   else "DEGRADED") if me < 900 else "NO_DATA"
        print(f"{alpha:>5.2f}  {r['bg_tau_ether']:>7.4f}  {r['n_hi_v']:>5}  "
              f"{r['n_lo_v']:>5}  {r['n_pairs']:>6}  "
              f"{me:>7.1f}  {be:>7.1f}  {verdict}")
        if me < best_err and me < 900:
            best_err = me
            best_alpha = alpha

    print()
    if best_alpha is not None:
        print(f"Best α: {best_alpha} → mean error {best_err:.1f}%")
        if best_err < BASELINE_ERROR:
            print("WEIGHTED HISTORY IMPROVES SR vs ETHER14 baseline!")
        elif best_err < 12.0:
            print("Competitive but not better than ETHER14 baseline.")
        else:
            print("Degraded vs ETHER14 baseline.")
    else:
        print("No valid results obtained.")

    # ── Save JSON ─────────────────────────────────────────────────────────────
    total_elapsed = round(time.time() - _t0, 2)
    out = {
        'rank': '60-WHIST',
        'test': 'exponentially_weighted_history_sr',
        'date': time.strftime('%Y-%m-%d'),
        'parameters': {
            'OUTER_L': OUTER_L, 'M': M, 'MAX_INNER': MAX_INNER,
            'N_WARMUP_STEPS': N_WARMUP_STEPS,
            'N_RUN_STEPS': N_RUN_STEPS, 'MIN_STABLE': MIN_STABLE,
            'ALPHA_VALUES': ALPHA_VALUES,
            'gamma_target': round(GAMMA_TARGET, 6),
            'v_canonical': V_CANONICAL,
            'c_eff': C_EFF,
        },
        'baseline': {
            'rank31_acs_ratio': 1.553,
            'rank31_acs_error_pct': 6.4,
        },
        'best_alpha': best_alpha,
        'best_mean_error_pct': round(best_err, 3) if best_err < 900 else None,
        'results_by_alpha': {
            str(a): r for a, r in results_by_alpha.items()
        },
        'total_elapsed_s': total_elapsed,
    }
    with open(RESULTS_FILE, 'w') as f:
        json.dump(out, f, indent=2)
    print(f"\nResults saved: {RESULTS_FILE}")

    # ── Figure ────────────────────────────────────────────────────────────────
    _make_figure(out)

    return out


def _make_figure(out: dict) -> None:
    """Summary figure: SR error and τ_c ratio vs α."""
    alphas_done = sorted(float(a) for a in out['results_by_alpha'])
    if not alphas_done:
        return

    res_list = [out['results_by_alpha'][str(a)] for a in alphas_done]

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    # Left: mean SR error vs α
    ax = axes[0]
    errs = [r['mean_sr_error_pct'] for r in res_list]
    best_errs = [r['best_sr_error_pct'] for r in res_list]
    valid_mask = [e < 900 for e in errs]
    xs = [a for a, v in zip(alphas_done, valid_mask) if v]
    ys = [e for e, v in zip(errs, valid_mask) if v]
    ys_best = [e for e, v in zip(best_errs, valid_mask) if v]

    if xs:
        ax.plot(xs, ys, 'o-', color='darkorange', linewidth=2,
                markersize=8, label='Mean SR error')
        ax.plot(xs, ys_best, 's--', color='steelblue', linewidth=1.5,
                markersize=6, label='Best SR error')
    ax.axhline(6.4, color='red', linestyle='--', linewidth=1.5,
               label='Baseline (Rank 31-ACS) 6.4%')
    ax.set_xlabel('α (EMA decay parameter)', fontsize=11)
    ax.set_ylabel('SR error (%)', fontsize=11)
    ax.set_title('SR Error vs α\nWeighted History Inner CA Seeding', fontsize=11)
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)

    # Right: τ_c ratio (hi-v mean) vs α + γ target
    ax2 = axes[1]
    ratios = [r['mean_hi_v_ratio'] for r in res_list]
    valid_r = [(a, r) for a, r in zip(alphas_done, ratios) if r is not None]
    if valid_r:
        ax2.plot([a for a, _ in valid_r], [r for _, r in valid_r],
                 'D-', color='forestgreen', linewidth=2, markersize=8,
                 label='Mean hi-v τ_c ratio')
    ax2.axhline(GAMMA_TARGET, color='red', linestyle='--', linewidth=1.5,
                label=f'γ target = {GAMMA_TARGET:.4f}')
    ax2.axhline(1.553, color='steelblue', linestyle=':', linewidth=1.5,
                label='Baseline ratio = 1.553')
    ax2.set_xlabel('α (EMA decay parameter)', fontsize=11)
    ax2.set_ylabel('Mean τ_c ratio (glider / ether)', fontsize=11)
    ax2.set_title('τ_c Ratio vs α\nTarget = γ = 1.659', fontsize=11)
    ax2.legend(fontsize=9)
    ax2.grid(alpha=0.3)

    fig.suptitle(
        f'Rank 60-WHIST: Weighted History SR Test — Rule 110, L={OUTER_L}\n'
        f'γ={GAMMA_TARGET:.4f}, baseline error=6.4% (Rank 31-ACS)',
        fontsize=11
    )
    fig.tight_layout()
    outpath = 'rank60_whist_results.png'
    fig.savefig(outpath, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Figure saved: {outpath}")


if __name__ == '__main__':
    main()
    signal.alarm(0)
    print(f"\nTotal elapsed: {time.time() - _t0:.2f}s")
