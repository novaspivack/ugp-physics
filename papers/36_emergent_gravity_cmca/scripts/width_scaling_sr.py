from pathlib import Path
SCRIPT_DIR = Path(__file__).resolve().parent
#!/usr/bin/env python3
"""
Rank 47-WDS: Inner CA Width Scaling — SR Accuracy vs M
EPIC_072

For each inner CA width M in [7, 11, 15, 21, 29] (all odd):
  - Precompute tau_c LUT for M-cell ether windows
  - Search all 1024 width-10 seeds for stable gliders with gamma in [1.3, 2.0]
  - Search for low-v reference seeds (|v/c| < 0.1)
  - Compute paired tau_c ratios and SR errors
  - Record: M, bg_tau_c, n_hi_seeds, n_lo_seeds, mean_error, best_error, pct_confirmed

Hypotheses tested:
  H1 (continuum limit): SR error decreases monotonically with M
  H2 (minimum resolution): accuracy plateaus at some M*
  H3 (no dependence): M-independent accuracy
"""

import numpy as np
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ETHER14 = np.array([1,1,1,1,1,0,0,0,1,0,0,1,1,0], dtype=np.uint8)
LUT110 = np.array([(110 >> i) & 1 for i in range(8)], dtype=np.uint8)
C_EFF = 2 / 3
OUTER_L = 400
MAX_INNER = 200
N_OUTER_STEPS = 150
MIN_STABLE_HI = 50
MIN_STABLE_LO = 30
M_VALUES = [7, 11, 15, 21, 29]
GAMMA_LO, GAMMA_HI = 1.3, 2.0
LOW_V_THRESH = 0.1

ether_base = np.array([ETHER14[i % 14] for i in range(OUTER_L)], dtype=np.uint8)


def run_rule110(state):
    """Vectorized Rule 110 step."""
    l = np.roll(state, 1).astype(np.int32)
    c = state.astype(np.int32)
    r = np.roll(state, -1).astype(np.int32)
    return LUT110[(l << 2) | (c << 1) | r]


def majority(state):
    return 1 if state.sum() * 2 > len(state) else 0


def precompute_tau_lut(M):
    """
    Build tau_lut[curr_bit][tgt_bit] = inner steps until majority flips to tgt_bit.
    Starting windows are drawn from ETHER14 slices of length M with correct majority.
    """
    windows = [np.array([ETHER14[(i + j) % 14] for j in range(M)], dtype=np.uint8)
               for i in range(14)]
    win_maj0 = [w for w in windows if w.sum() * 2 < M]
    win_maj1 = [w for w in windows if w.sum() * 2 > M]
    start0 = win_maj0[0].copy() if win_maj0 else np.zeros(M, dtype=np.uint8)
    start1 = win_maj1[0].copy() if win_maj1 else np.ones(M, dtype=np.uint8)

    tau_lut = np.zeros((2, 2), dtype=np.float32)
    for curr_bit, start in [(0, start0), (1, start1)]:
        for tgt_bit in [0, 1]:
            state = start.copy()
            for step in range(MAX_INNER):
                if majority(state) == tgt_bit:
                    tau_lut[curr_bit, tgt_bit] = step
                    break
                state = run_rule110(state)
            else:
                tau_lut[curr_bit, tgt_bit] = MAX_INNER
    return tau_lut


def measure_tau_fast(outer_now, outer_next, tau_lut):
    """O(L) tau_c measurement via precomputed LUT."""
    return tau_lut[outer_now.astype(int), outer_next.astype(int)]


def test_seed_full(seed_str, tau_lut, n_steps=N_OUTER_STEPS, min_stable=MIN_STABLE_HI):
    """Full stability test and tau_c measurement for a seed string."""
    seed = np.array([int(b) for b in seed_str], dtype=np.uint8)
    center = OUTER_L // 2
    tape = ether_base.copy()
    for j, bit in enumerate(seed):
        tape[(center + j) % OUTER_L] = bit

    s_tape = tape.copy()
    s_ref = ether_base.copy()

    positions = []
    g_taus, e_taus = [], []

    for _ in range(n_steps):
        s_tape_next = run_rule110(s_tape)
        s_ref_next = run_rule110(s_ref)

        diff = s_tape != s_ref
        diff_pos = np.where(diff)[0]

        if 2 <= len(diff_pos) <= 60:
            positions.append(float(diff_pos.mean()))
            taus = measure_tau_fast(s_tape, s_tape_next, tau_lut)
            g_taus.append(taus[diff].mean())
            ndiff = ~diff
            e_taus.append(taus[ndiff].mean() if ndiff.sum() > 0 else 0.43)

        s_tape = s_tape_next
        s_ref = s_ref_next

    if len(positions) < min_stable:
        return None

    v = np.polyfit(np.arange(len(positions)), np.array(positions), 1)[0]
    v_over_c = abs(v / C_EFF)

    if v_over_c >= 1.0:
        return None

    gam = 1.0 / np.sqrt(1 - v_over_c**2)
    ratio = float(np.mean(g_taus)) / float(np.mean(e_taus)) if e_taus else None

    return {'v': v, 'v_over_c': v_over_c, 'gamma': gam, 'ratio': ratio,
            'n_stable': len(positions)}


def compute_background_tau(tau_lut):
    """Average tau_c of pure ether evolved for 60 steps (skip warmup)."""
    s = ether_base.copy()
    bg_taus = []
    for _ in range(60):
        s_next = run_rule110(s)
        bg_taus.append(measure_tau_fast(s, s_next, tau_lut).mean())
        s = s_next
    return float(np.mean(bg_taus[10:20]))


def run_for_M(M):
    """Full SR test pipeline for a given inner CA width M."""
    print(f"\n{'='*60}")
    print(f"M = {M}")
    print(f"{'='*60}")

    tau_lut = precompute_tau_lut(M)
    print(f"  tau_lut: {tau_lut}")

    bg_tau_c = compute_background_tau(tau_lut)
    print(f"  Background tau_c = {bg_tau_c:.4f}")

    # Search high-v seeds
    stable_hi_v = []
    for ic in range(2**10):
        seed_str = bin(ic)[2:].zfill(10)
        result = test_seed_full(seed_str, tau_lut, n_steps=N_OUTER_STEPS,
                                min_stable=MIN_STABLE_HI)
        if result and GAMMA_LO <= result['gamma'] <= GAMMA_HI:
            stable_hi_v.append((seed_str, result))
    print(f"  Stable gamma in [{GAMMA_LO}, {GAMMA_HI}]: {len(stable_hi_v)} seeds")

    # Search low-v reference seeds
    low_v_seeds = []
    for ic in range(2**10):
        seed_str = bin(ic)[2:].zfill(10)
        result = test_seed_full(seed_str, tau_lut, n_steps=100, min_stable=MIN_STABLE_LO)
        if result and result['v_over_c'] < LOW_V_THRESH and result['n_stable'] >= MIN_STABLE_LO:
            low_v_seeds.append((seed_str, result))
            if len(low_v_seeds) >= 5:
                break
    print(f"  Low-v reference seeds: {len(low_v_seeds)}")

    if not stable_hi_v or not low_v_seeds:
        print(f"  SKIPPED: insufficient seeds (hi={len(stable_hi_v)}, lo={len(low_v_seeds)})")
        return {
            'M': M, 'bg_tau_c': bg_tau_c,
            'n_hi_seeds': len(stable_hi_v), 'n_lo_seeds': len(low_v_seeds),
            'mean_error': None, 'best_error': None,
            'pct_confirmed': None, 'n_pairs': 0,
            'n_confirmed': 0, 'errors': [],
        }

    stable_hi_v.sort(key=lambda x: -x[1]['v_over_c'])
    hi_set = stable_hi_v[:min(5, len(stable_hi_v))]
    lo_set = low_v_seeds[:min(3, len(low_v_seeds))]

    errors = []
    for hi_seed, hi_res in hi_set:
        for lo_seed, lo_res in lo_set:
            if hi_res['ratio'] is None or lo_res['ratio'] is None:
                continue
            p = hi_res['ratio'] / lo_res['ratio']
            q = hi_res['gamma'] / lo_res['gamma']
            e = abs(p - q) / q * 100
            errors.append(e)

    n_confirmed = sum(1 for e in errors if e < 15)
    mean_err = float(np.mean(errors)) if errors else None
    best_err = float(np.min(errors)) if errors else None
    pct_conf = n_confirmed / len(errors) if errors else None

    print(f"  Pairs tested: {len(errors)}")
    if mean_err is not None:
        print(f"  Mean error: {mean_err:.1f}%  Best: {best_err:.1f}%  "
              f"Confirmed: {n_confirmed}/{len(errors)}")

    return {
        'M': M, 'bg_tau_c': bg_tau_c,
        'n_hi_seeds': len(stable_hi_v), 'n_lo_seeds': len(low_v_seeds),
        'mean_error': mean_err, 'best_error': best_err,
        'pct_confirmed': pct_conf, 'n_pairs': len(errors),
        'n_confirmed': n_confirmed, 'errors': errors,
    }


def print_summary(results):
    """Print formatted results table."""
    print("\n" + "=" * 75)
    print("Width Scaling Results:")
    print(f"{'M':>4} | {'bg_tau_c':>8} | {'hi_seeds':>8} | {'lo_seeds':>8} | "
          f"{'mean_err':>8} | {'best_err':>8} | {'confirmed':>12}")
    print("-" * 75)
    for r in results:
        mean_s = f"{r['mean_error']:.1f}%" if r['mean_error'] is not None else "   N/A  "
        best_s = f"{r['best_error']:.1f}%" if r['best_error'] is not None else "   N/A  "
        conf_s = (f"{r['n_confirmed']}/{r['n_pairs']}"
                  if r['n_pairs'] > 0 else "N/A")
        print(f"{r['M']:>4} | {r['bg_tau_c']:>8.4f} | {r['n_hi_seeds']:>8} | "
              f"{r['n_lo_seeds']:>8} | {mean_s:>8} | {best_s:>8} | {conf_s:>12}")
    print("=" * 75)


def determine_hypothesis(results):
    """Classify H1/H2/H3 from the error trend across M values."""
    valid = [(r['M'], r['mean_error']) for r in results if r['mean_error'] is not None]
    if len(valid) < 2:
        return "INCONCLUSIVE (insufficient data)"
    ms = [v[0] for v in valid]
    errs = [v[1] for v in valid]
    # Fit linear trend to errors vs M
    slope = np.polyfit(ms, errs, 1)[0]
    err_range = max(errs) - min(errs)
    if err_range < 3.0:
        return "H3 (no dependence) — SR error is M-independent within 3%"
    if slope < -0.5:
        return "H1 (continuum limit) — SR error decreases with M"
    # Check for plateau: later values flat, early values higher
    early_mean = np.mean(errs[:len(errs)//2])
    late_mean = np.mean(errs[len(errs)//2:])
    if early_mean - late_mean > 3.0 and abs(slope) < 0.5:
        return "H2 (minimum resolution) — accuracy plateaus after an initial improvement"
    if slope > 0.5:
        return "H3-variant — SR error slightly increases with M (noise or regime shift)"
    return f"H2/H3 ambiguous — slope={slope:.2f}, range={err_range:.1f}%"


def make_plot(results, outpath):
    """Two-panel plot: mean SR error vs M, and background tau_c vs M."""
    valid = [r for r in results if r['mean_error'] is not None]
    ms = [r['M'] for r in valid]
    mean_errs = [r['mean_error'] for r in valid]
    best_errs = [r['best_error'] for r in valid]
    bg_taus = [r['bg_tau_c'] for r in results]
    all_ms = [r['M'] for r in results]

    # Error bars: std of per-pair errors
    err_stds = []
    for r in valid:
        err_stds.append(np.std(r['errors']) if len(r['errors']) > 1 else 0)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Left: mean SR error vs M
    ax = axes[0]
    if ms:
        ax.errorbar(ms, mean_errs, yerr=err_stds, fmt='o-', color='steelblue',
                    capsize=4, label='Mean SR error', linewidth=2, markersize=8)
        ax.plot(ms, best_errs, 's--', color='darkorange', label='Best error', markersize=7)
    ax.axhline(15, color='green', linestyle='--', alpha=0.7, label='15% threshold')
    ax.set_xlabel('Inner CA width M')
    ax.set_ylabel('SR error (%)')
    ax.set_title('SR Accuracy vs Inner CA Width M')
    ax.legend()
    ax.grid(True, alpha=0.3)
    if ms:
        ax.set_xlim(min(ms) - 1, max(ms) + 1)
    ax.set_xticks(M_VALUES)

    # Right: background tau_c vs M
    ax2 = axes[1]
    ax2.plot(all_ms, bg_taus, 'o-', color='crimson', linewidth=2, markersize=8)
    ax2.set_xlabel('Inner CA width M')
    ax2.set_ylabel('Background τ_c')
    ax2.set_title('Background τ_c vs Inner CA Width M')
    ax2.grid(True, alpha=0.3)
    ax2.set_xticks(M_VALUES)

    plt.tight_layout()
    plt.savefig(outpath, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Plot saved: {outpath}")


def main():
    print("=" * 65)
    print("Rank 47-WDS: Inner CA Width Scaling — SR Accuracy vs M")
    print(f"M values: {M_VALUES}  (all odd, majority-vote safe)")
    print(f"OUTER_L={OUTER_L}, n_steps={N_OUTER_STEPS}, seeds=1024 (width-10)")
    print("=" * 65)

    results = []
    for M in M_VALUES:
        r = run_for_M(M)
        results.append(r)

    print_summary(results)
    hypothesis = determine_hypothesis(results)
    print(f"\nHypothesis verdict: {hypothesis}")

    # Save JSON
    json_path = 'rank47_wds_results.json'
    out = {
        'M_values': M_VALUES,
        'outer_L': OUTER_L,
        'n_outer_steps': N_OUTER_STEPS,
        'gamma_range': [GAMMA_LO, GAMMA_HI],
        'hypothesis_verdict': hypothesis,
        'results': {str(r['M']): {k: v for k, v in r.items() if k != 'M'}
                    for r in results},
    }
    with open(json_path, 'w') as f:
        json.dump(out, f, indent=2)
    print(f"Results saved: {json_path}")

    # Save plot
    plot_path = 'rank47_wds_sr_vs_M.png'
    make_plot(results, plot_path)

    print("\nRank 47-WDS complete.")
    return results, hypothesis


if __name__ == '__main__':
    main()
