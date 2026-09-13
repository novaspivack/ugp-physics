from pathlib import Path
SCRIPT_DIR = Path(__file__).resolve().parent
#!/usr/bin/env python3
"""
Rank 3-SRT Round 19: Definitive High-Velocity SR Test
EPIC_072

Uses vectorized numpy operations for speed.
Searches all 1024 width-10 seeds, filtered to γ ∈ [1.3, 2.0].
Verifies stability over 200+ outer steps.
Tests paired SR comparison with sufficient γ signal (20-45% dilation).

Key speedup over prior rounds:
  - Vectorized run_outer via numpy roll + LUT (no Python loops over cells)
  - Precomputed τ_c table: for the two fixed starting windows (win_maj0[0], win_maj1[0]),
    precompute τ_c[current_bit][target_bit] once. Then measure_tau is O(L) lookup.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ETHER14 = np.array([1,1,1,1,1,0,0,0,1,0,0,1,1,0], dtype=np.uint8)
LUT110 = np.array([(110 >> i) & 1 for i in range(8)], dtype=np.uint8)
C_EFF = 2/3
OUTER_L = 500
M = 7

ether_base = np.array([ETHER14[i % 14] for i in range(OUTER_L)], dtype=np.uint8)


def run_outer(state):
    """Vectorized Rule 110 step."""
    l = np.roll(state, 1).astype(np.int32)
    c = state.astype(np.int32)
    r = np.roll(state, -1).astype(np.int32)
    return LUT110[(l << 2) | (c << 1) | r]


def run_inner(state):
    """Vectorized Rule 110 step for M-cell inner window."""
    l = np.roll(state, 1).astype(np.int32)
    c = state.astype(np.int32)
    r = np.roll(state, -1).astype(np.int32)
    return LUT110[(l << 2) | (c << 1) | r]


def majority(state):
    return 1 if state.sum() * 2 > len(state) else 0


# Build M=7 windows from ETHER14
windows = [np.array([ETHER14[(i + j) % 14] for j in range(M)], dtype=np.uint8)
           for i in range(14)]
win_maj0 = [w for w in windows if majority(w) == 0]
win_maj1 = [w for w in windows if majority(w) == 1]

# Precompute τ_c lookup table for two fixed starting windows.
# tau_lut[current_bit][target_bit] = steps until majority(inner) == target_bit
MAX_INNER = 100

def precompute_tau_lut():
    starts = {
        1: win_maj1[0].copy() if win_maj1 else np.zeros(M, dtype=np.uint8),
        0: win_maj0[0].copy() if win_maj0 else np.zeros(M, dtype=np.uint8),
    }
    tau_lut = np.zeros((2, 2), dtype=np.float32)
    for curr in [0, 1]:
        for tgt in [0, 1]:
            state = starts[curr].copy()
            for step in range(MAX_INNER):
                if majority(state) == tgt:
                    tau_lut[curr, tgt] = step
                    break
                state = run_inner(state)
            else:
                tau_lut[curr, tgt] = MAX_INNER
    return tau_lut


tau_lut = precompute_tau_lut()
print(f"τ_c LUT: {tau_lut}")


def measure_tau_fast(outer_now, outer_next):
    """O(L) τ_c measurement via precomputed LUT."""
    return tau_lut[outer_now.astype(int), outer_next.astype(int)]


def test_seed_full(seed_str, n_steps=200, min_stable=50):
    """Full stability test and τ_c measurement for a seed string."""
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
        s_tape_next = run_outer(s_tape)
        s_ref_next = run_outer(s_ref)

        diff = s_tape != s_ref
        diff_pos = np.where(diff)[0]

        if 2 <= len(diff_pos) <= 60:
            positions.append(float(diff_pos.mean()))
            taus = measure_tau_fast(s_tape, s_tape_next)
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


print("=" * 65)
print("Round 19: Definitive High-Velocity SR Test")
print("Filter: γ ∈ [1.3, 2.0], 200+ step stability (vectorized)")
print("=" * 65)

# Background τ_c from pure ether
s = ether_base.copy()
bg_taus = []
for _ in range(60):
    s_next = run_outer(s)
    if len(bg_taus) < 20:
        bg_taus.append(measure_tau_fast(s, s_next).mean())
    s = s_next
tau_bg = float(np.mean(bg_taus[10:20]))
print(f"Background τ_c = {tau_bg:.4f}")

# Systematic search: all 1024 width-10 seeds
print("\nSearching all 1024 width-10 seeds for stable γ∈[1.3,2.0]...")
stable_hi_v = []
n_shown = 0
for ic in range(0, 2**10):
    seed_str = bin(ic)[2:].zfill(10)
    result = test_seed_full(seed_str, n_steps=200, min_stable=50)
    if result and 1.3 <= result['gamma'] <= 2.0:
        stable_hi_v.append((seed_str, result))
        if n_shown < 5:
            print(f"  Found: {seed_str}, v={result['v']:.4f}, γ={result['gamma']:.4f}, "
                  f"ratio={result['ratio']:.4f}, stable={result['n_stable']} steps")
            n_shown += 1

print(f"Total stable γ∈[1.3,2.0] seeds found: {len(stable_hi_v)}")

# Search for low-v reference seeds
print("\nSearching for low-v reference seeds (|v/c|<0.1, γ<1.005)...")
low_v_seeds = []
for ic in range(0, 2**10):
    seed_str = bin(ic)[2:].zfill(10)
    result = test_seed_full(seed_str, n_steps=100, min_stable=30)
    if result and result['v_over_c'] < 0.1 and result['n_stable'] >= 30:
        low_v_seeds.append((seed_str, result))
        if len(low_v_seeds) >= 5:
            break

print(f"Low-v reference seeds found: {len(low_v_seeds)}")
for sd, rs in low_v_seeds:
    print(f"  {sd}: v={rs['v']:.4f}, γ={rs['gamma']:.4f}, ratio={rs['ratio']:.4f}")

# Paired SR test
if stable_hi_v and low_v_seeds:
    stable_hi_v.sort(key=lambda x: -x[1]['v_over_c'])

    print("\n=== DEFINITIVE SR TEST ===")
    best_hi = stable_hi_v[0]
    best_lo = low_v_seeds[0]

    paired = best_hi[1]['ratio'] / best_lo[1]['ratio']
    pred = best_hi[1]['gamma'] / best_lo[1]['gamma']
    err = abs(paired - pred) / pred * 100

    print(f"High-v: seed={best_hi[0]}, v={best_hi[1]['v']:.4f}, γ={best_hi[1]['gamma']:.4f}, "
          f"ratio={best_hi[1]['ratio']:.4f}")
    print(f"Low-v:  seed={best_lo[0]}, v={best_lo[1]['v']:.4f}, γ={best_lo[1]['gamma']:.4f}, "
          f"ratio={best_lo[1]['ratio']:.4f}")
    print(f"Paired ratio: {paired:.4f}")
    print(f"SR prediction: {pred:.4f}")
    print(f"SR error: {err:.1f}%")
    print(f"VERDICT: {'SR CONFIRMED' if err < 15 else 'BORDERLINE' if err < 30 else 'NOT CONFIRMED'}")

    # Test multiple pairs
    print("\nMultiple pair test:")
    errors = []
    hi_set = stable_hi_v[:min(5, len(stable_hi_v))]
    lo_set = low_v_seeds[:min(3, len(low_v_seeds))]
    for hi_seed, hi_res in hi_set:
        for lo_seed, lo_res in lo_set:
            p = hi_res['ratio'] / lo_res['ratio']
            q = hi_res['gamma'] / lo_res['gamma']
            e = abs(p - q) / q * 100
            errors.append(e)
            print(f"  {hi_seed} vs {lo_seed}: paired={p:.4f}, pred={q:.4f}, err={e:.1f}%")

    if errors:
        mean_err = float(np.mean(errors))
        ok = sum(1 for e in errors if e < 15)
        print(f"\nMean error across {len(errors)} pairs: {mean_err:.1f}%")
        print(f"SR confirmed (<15% err): {ok}/{len(errors)} pairs")

        # Summary visualization
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        all_results = stable_hi_v + low_v_seeds
        gammas = [r['gamma'] for _, r in all_results]
        ratios = [r['ratio'] for _, r in all_results]
        colors = ['red'] * len(stable_hi_v) + ['blue'] * len(low_v_seeds)
        axes[0].scatter(gammas, ratios, c=colors, alpha=0.7, s=60)
        lo_ratio_ref = low_v_seeds[0][1]['ratio'] if low_v_seeds else 1.0
        gs_plot = np.linspace(1.0, max(gammas) + 0.05, 100)
        axes[0].plot(gs_plot, lo_ratio_ref * gs_plot, 'k--', alpha=0.5, label='Linear SR ∝ γ')
        axes[0].set_xlabel('γ (Lorentz factor)')
        axes[0].set_ylabel('τ_c ratio (glider / ether)')
        axes[0].set_title('Round 19: τ_c ratio vs γ\nRed=high-v, Blue=low-v ref')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)

        axes[1].hist(errors, bins=max(5, len(errors)//2), color='steelblue',
                     edgecolor='black', alpha=0.8)
        axes[1].axvline(15, color='green', linestyle='--', label='15% threshold')
        axes[1].axvline(mean_err, color='red', linestyle='-', label=f'Mean={mean_err:.1f}%')
        axes[1].set_xlabel('SR error (%)')
        axes[1].set_ylabel('Count')
        axes[1].set_title(f'Round 19 SR Error Distribution\n{ok}/{len(errors)} pairs <15%')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)

        plt.tight_layout()
        outpath = 'round19_sr_results.png'
        plt.savefig(outpath, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"\nPlot saved: {outpath}")

elif not stable_hi_v:
    print("\nNo stable γ∈[1.3,2.0] seeds found; checking Round 18 known candidates...")
    for seed_str in ["1100111011", "0101110011", "0000010011", "1100011011", "0110111001"]:
        result = test_seed_full(seed_str, n_steps=200, min_stable=30)
        if result:
            print(f"  {seed_str}: γ={result['gamma']:.4f}, v/c={result['v_over_c']:.4f}, "
                  f"stable={result['n_stable']}, ratio={result['ratio']:.4f}")
        else:
            print(f"  {seed_str}: not stable at 200 steps / γ out of range")

print("\nRound 19 complete.")
