#!/usr/bin/env python3
"""
Rank 54B: Orbit AFCA Symmetric τ_c Fix
EPIC_072 — GTE Ontological Unification
2026-05-22

Fixes the reachability-asymmetric τ_c LUT from Rank 54A (f_MDL orbit AFCA),
where 0→1 transitions maxed at 100 steps because vacuum-seeded f_MDL can never
enter the orbit closed cycle.

Two options tested:
  Option A: Symmetric LUT — both 0→1 and 1→0 fixed at τ_c=2 (orbit lifetime)
  Option B: Orbit-fraction τ_c — τ_c(curr→tgt) = fraction of n_steps spent
            in orbit when starting from the target seed (orbit or vacuum)
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
WALL_CLOCK_LIMIT = 180
_t0 = time.time()


def _wall_timeout(s, f):
    elapsed = time.time() - _t0
    print(f"\nWall-clock limit {WALL_CLOCK_LIMIT}s reached ({elapsed:.1f}s elapsed). Saving partial results.")
    raise SystemExit(1)


signal.signal(signal.SIGALRM, _wall_timeout)
signal.alarm(WALL_CLOCK_LIMIT)

# ── f_MDL Z₇ rule ────────────────────────────────────────────────────────────

def fmdl(l, c, r):
    if l == 1 and c == 1 and r == 5: return 2
    if l == 1 and c == 5 and r == 2: return 5
    if l == 5 and c == 2 and r == 2: return 2
    if l == 2 and c == 2 and r == 1: return 0
    if l == 2 and c == 1 and r == 1: return 2
    if l == 2 and c == 2 and r == 5: return 5
    if l == 2 and c == 5 and r == 2: return 6
    if l == 5 and c == 2 and r == 0: return 5
    if l == 2 and c == 0 and r == 2: return 3
    if l == 0 and c == 2 and r == 2: return 5
    if l == 0 and c == 0 and r == 0: return 0
    if l == 0 and c == 0 and r == 1: return 1
    if l == 0 and c == 1 and r == 0: return 1
    if l == 0 and c == 1 and r == 1: return 1
    if l == 1 and c == 0 and r == 0: return 0
    if l == 1 and c == 0 and r == 1: return 1
    if l == 1 and c == 1 and r == 0: return 1
    if l == 1 and c == 1 and r == 1: return 0
    return 0


def fmdl_step_M(cells):
    n = len(cells)
    return tuple(fmdl(cells[(i - 1 + n) % n], cells[i], cells[(i + 1) % n]) for i in range(n))


# ── Orbit classification ──────────────────────────────────────────────────────
GEN1 = (1, 5, 2, 2, 1)
ORBIT_VALUES = {1, 2, 3, 5, 6}
ORBIT7_BASE = tuple(GEN1[i % 5] for i in range(7))   # (1,5,2,2,1,5,2)
VACUUM7 = (0,) * 7


def classify_orbit(inner_state):
    n_orbit = sum(1 for v in inner_state if v in ORBIT_VALUES)
    return 1 if n_orbit * 2 > len(inner_state) else 0


# ── Outer CA constants ────────────────────────────────────────────────────────
ETHER14 = np.array([1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0], dtype=np.uint8)
LUT110 = np.array([(110 >> i) & 1 for i in range(8)], dtype=np.uint8)
C_EFF = 2 / 3
OUTER_L = 500

ether_base = np.array([ETHER14[i % 14] for i in range(OUTER_L)], dtype=np.uint8)


def run_outer(state):
    l = np.roll(state, 1).astype(np.int32)
    c = state.astype(np.int32)
    r = np.roll(state, -1).astype(np.int32)
    return LUT110[(l << 2) | (c << 1) | r]


# ── Option A: Symmetric LUT ───────────────────────────────────────────────────
# Both 0→1 and 1→0 fixed at τ_c=2 (the orbit lifetime = steps to collapse from ORBIT7_BASE).
# This eliminates the 100-step maxout on 0→1 from Rank 54A, making the LUT symmetric.
#   (0,0): 0  — vacuum stays vacuum: no inner transition needed
#   (0,1): 2  — vacuum→orbit: use orbit lifetime (symmetric with 1→0)
#   (1,0): 2  — orbit→vacuum: f_MDL orbit collapses in 2 inner steps
#   (1,1): 0  — orbit stays orbit: no inner transition needed
lut_a_arr = np.array([[0.0, 2.0],
                       [2.0, 0.0]], dtype=np.float32)


def measure_tau_a_vec(outer_now, outer_next):
    """Vectorized Option A τ_c lookup via numpy 2D array indexing."""
    return lut_a_arr[outer_now, outer_next]


# ── Option B: Orbit-fraction τ_c ─────────────────────────────────────────────
# τ_c(curr→tgt) = fraction of ORBIT_FRACTION_STEPS that the target seed spends
# classified as in-orbit under f_MDL evolution.
# Interpretation: τ_c measures the "orbit persistence" of the target state.
ORBIT_FRACTION_STEPS = 14  # one Z₇ orbit period


def orbit_fraction(seed, n_steps=ORBIT_FRACTION_STEPS):
    """Fraction of n_steps the seed state spends classified as in-orbit."""
    inner = seed
    count = 0
    for _ in range(n_steps):
        if classify_orbit(inner) == 1:
            count += 1
        inner = fmdl_step_M(inner)
    return count / n_steps


frac_orbit = orbit_fraction(ORBIT7_BASE)
frac_vacuum = orbit_fraction(VACUUM7)

# LUT: τ_c depends only on target (not on current class)
lut_b_arr = np.array([[frac_vacuum, frac_orbit],
                       [frac_vacuum, frac_orbit]], dtype=np.float32)


def measure_tau_b_vec(outer_now, outer_next):
    """Vectorized Option B τ_c lookup via numpy 2D array indexing."""
    return lut_b_arr[outer_now, outer_next]


# ── Print LUT info ────────────────────────────────────────────────────────────
print("=== Rank 54B: Orbit AFCA Symmetric τ_c ===")
print()
print("Option A: Symmetric LUT")
print("  (0→0): 0   (0→1): 2   (1→0): 2   (1→1): 0")
print()
print("Option B: Orbit-fraction τ_c")
print(f"  orbit_fraction(ORBIT7_BASE, n={ORBIT_FRACTION_STEPS}): {frac_orbit:.4f}")
print(f"  orbit_fraction(VACUUM7, n={ORBIT_FRACTION_STEPS}): {frac_vacuum:.4f}")
print(f"  (0→0): {frac_vacuum:.4f}   (0→1): {frac_orbit:.4f}"
      f"   (1→0): {frac_vacuum:.4f}   (1→1): {frac_orbit:.4f}")


# ── Background τ_c from ether run ─────────────────────────────────────────────
s_a = ether_base.copy()
s_b = ether_base.copy()
bg_taus_a, bg_taus_b = [], []
for _ in range(60):
    s_a_next = run_outer(s_a)
    s_b_next = run_outer(s_b)
    if len(bg_taus_a) < 20:
        bg_taus_a.append(float(measure_tau_a_vec(s_a, s_a_next).mean()))
        bg_taus_b.append(float(measure_tau_b_vec(s_b, s_b_next).mean()))
    s_a = s_a_next
    s_b = s_b_next

tau_bg_a = float(np.mean(bg_taus_a[10:20]))
tau_bg_b = float(np.mean(bg_taus_b[10:20]))
print()
print(f"Background τ_c (ether steps 10-20):")
print(f"  Option A: {tau_bg_a:.4f}")
print(f"  Option B: {tau_bg_b:.4f}")


# ── Generic seed test function ────────────────────────────────────────────────

def test_seed(seed_str, measure_fn, tau_bg_ether, n_steps=200, min_stable=50):
    """
    Test a width-10 seed with the given τ_c measurement function.
    Returns dict with v, v_over_c, gamma, ratio, n_stable, or None if not stable.
    """
    seed = np.array([int(b) for b in seed_str], dtype=np.uint8)
    center = OUTER_L // 2 - ((OUTER_L // 2 - 12) % 14)
    tape = ether_base.copy()
    for j, bit in enumerate(seed):
        tape[(center + j) % OUTER_L] = bit

    s_tape = tape.copy()
    s_ref = ether_base.copy()
    positions, g_taus, e_taus = [], [], []

    for _ in range(n_steps):
        s_tape_next = run_outer(s_tape)
        s_ref_next = run_outer(s_ref)

        diff = s_tape != s_ref
        diff_pos = np.where(diff)[0]

        if 2 <= len(diff_pos) <= 60:
            positions.append(float(diff_pos.mean()))
            taus = measure_fn(s_tape, s_tape_next)
            g_taus.append(float(taus[diff].mean()))
            ndiff = ~diff
            e_taus.append(float(taus[ndiff].mean()) if ndiff.sum() > 0 else tau_bg_ether)

        s_tape = s_tape_next
        s_ref = s_ref_next

    if len(positions) < min_stable:
        return None

    v = float(np.polyfit(np.arange(len(positions)), np.array(positions), 1)[0])
    v_over_c = abs(v / C_EFF)
    if v_over_c >= 1.0:
        return None

    gam = 1.0 / np.sqrt(1.0 - v_over_c ** 2)
    ratio = float(np.mean(g_taus)) / float(np.mean(e_taus)) if e_taus else None
    return {'v': v, 'v_over_c': v_over_c, 'gamma': gam, 'ratio': ratio,
            'n_stable': len(positions)}


def run_paired_sr(hi_seeds, lo_seeds):
    """Compute paired SR errors from up to 5 hi-v × 3 lo-v seeds."""
    errors = []
    paired = []
    if not hi_seeds or not lo_seeds:
        return errors, paired, None, None
    hi_set = sorted(hi_seeds, key=lambda x: -x[1]['v_over_c'])[:5]
    lo_set = lo_seeds[:3]
    for hi_seed, hi_res in hi_set:
        for lo_seed, lo_res in lo_set:
            if hi_res['ratio'] is None or lo_res['ratio'] is None:
                continue
            p_ratio = hi_res['ratio'] / lo_res['ratio']
            pred = hi_res['gamma'] / lo_res['gamma']
            e = abs(p_ratio - pred) / pred * 100
            errors.append(e)
            paired.append({
                'hi_seed': hi_seed, 'lo_seed': lo_seed,
                'hi_gamma': hi_res['gamma'], 'lo_gamma': lo_res['gamma'],
                'hi_ratio': hi_res['ratio'], 'lo_ratio': lo_res['ratio'],
                'paired_ratio': p_ratio, 'sr_pred': pred, 'error_pct': e,
            })
    mean_err = float(np.mean(errors)) if errors else None
    best = min(paired, key=lambda x: x['error_pct']) if paired else None
    return errors, paired, mean_err, best


# ── Option A: Full seed search ────────────────────────────────────────────────
print()
print("--- Option A: Searching all 1024 seeds (symmetric LUT) ---")
stable_hi_v_a = []
for ic in range(2 ** 10):
    if time.time() - _t0 > 80:
        print(f"  Stopping Option A at seed {ic} (wall-clock 80s).")
        break
    seed_str = bin(ic)[2:].zfill(10)
    r = test_seed(seed_str, measure_tau_a_vec, tau_bg_a, n_steps=200, min_stable=50)
    if r and 1.3 <= r['gamma'] <= 2.0:
        stable_hi_v_a.append((seed_str, r))
print(f"  High-v seeds (γ∈[1.3,2.0]): {len(stable_hi_v_a)}")

low_v_seeds_a = []
for ic in range(2 ** 10):
    if time.time() - _t0 > 90:
        break
    seed_str = bin(ic)[2:].zfill(10)
    r = test_seed(seed_str, measure_tau_a_vec, tau_bg_a, n_steps=100, min_stable=30)
    if r and r['v_over_c'] < 0.1 and r['n_stable'] >= 30:
        low_v_seeds_a.append((seed_str, r))
        if len(low_v_seeds_a) >= 5:
            break
print(f"  Low-v reference seeds: {len(low_v_seeds_a)}")

errors_a, paired_a, mean_err_a, best_a = run_paired_sr(stable_hi_v_a, low_v_seeds_a)
if mean_err_a is not None:
    print(f"  Best pair SR error: {best_a['error_pct']:.1f}%")
    print(f"  Mean SR error ({len(errors_a)} pairs): {mean_err_a:.1f}%")
else:
    print("  Result: INCONCLUSIVE (insufficient seeds)")

# ── Option B: Full seed search ────────────────────────────────────────────────
print()
print("--- Option B: Searching all 1024 seeds (orbit-fraction τ_c) ---")
stable_hi_v_b = []
for ic in range(2 ** 10):
    if time.time() - _t0 > 150:
        print(f"  Stopping Option B at seed {ic} (wall-clock 150s).")
        break
    seed_str = bin(ic)[2:].zfill(10)
    r = test_seed(seed_str, measure_tau_b_vec, tau_bg_b, n_steps=200, min_stable=50)
    if r and 1.3 <= r['gamma'] <= 2.0:
        stable_hi_v_b.append((seed_str, r))
print(f"  High-v seeds (γ∈[1.3,2.0]): {len(stable_hi_v_b)}")

low_v_seeds_b = []
for ic in range(2 ** 10):
    if time.time() - _t0 > 160:
        break
    seed_str = bin(ic)[2:].zfill(10)
    r = test_seed(seed_str, measure_tau_b_vec, tau_bg_b, n_steps=100, min_stable=30)
    if r and r['v_over_c'] < 0.1 and r['n_stable'] >= 30:
        low_v_seeds_b.append((seed_str, r))
        if len(low_v_seeds_b) >= 5:
            break
print(f"  Low-v reference seeds: {len(low_v_seeds_b)}")

errors_b, paired_b, mean_err_b, best_b = run_paired_sr(stable_hi_v_b, low_v_seeds_b)
if mean_err_b is not None:
    print(f"  Best pair SR error: {best_b['error_pct']:.1f}%")
    print(f"  Mean SR error ({len(errors_b)} pairs): {mean_err_b:.1f}%")
else:
    print("  Result: INCONCLUSIVE (insufficient seeds)")

# ── Summary output ────────────────────────────────────────────────────────────
print()
print("=" * 65)
print("=== Rank 54B: Orbit AFCA Symmetric τ_c — Summary ===")
print()
print("Option A (symmetric LUT, both 0→1=1→0=2):")
print(f"  Background τ_c: {tau_bg_a:.4f}")
if mean_err_a is not None:
    print(f"  Best pair SR error: {best_a['error_pct']:.1f}%")
    print(f"  Mean error ({len(errors_a)} pairs): {mean_err_a:.1f}%")
else:
    print("  INCONCLUSIVE")
print()
print("Option B (orbit fraction τ_c):")
print(f"  Background τ_c: {tau_bg_b:.4f}")
if mean_err_b is not None:
    print(f"  Best pair SR error: {best_b['error_pct']:.1f}%")
    print(f"  Mean error ({len(errors_b)} pairs): {mean_err_b:.1f}%")
else:
    print("  INCONCLUSIVE")
print()
print("Compare:")
print("  Rank 54A (asymmetric LUT): 18.5% mean / 4.1% best")
print("  Rank 31-ACS (true AFCA majority): 6.4%")
a_str = (f"{mean_err_a:.1f}% mean / {best_a['error_pct']:.1f}% best"
         if mean_err_a is not None else "INCONCLUSIVE")
b_str = (f"{mean_err_b:.1f}% mean / {best_b['error_pct']:.1f}% best"
         if mean_err_b is not None else "INCONCLUSIVE")
print(f"  Rank 54B option A: {a_str}")
print(f"  Rank 54B option B: {b_str}")

# determine verdict
all_means = [(v, lbl) for v, lbl in [(mean_err_a, "A"), (mean_err_b, "B")] if v is not None]
if all_means:
    best_mean, best_opt = min(all_means, key=lambda x: x[0])
    if best_mean < 6.4:
        verdict = (f"orbit coarse-graining COMPETITIVE with majority vote — "
                   f"Option {best_opt} achieves {best_mean:.1f}% (< 6.4% AFCA baseline); "
                   f"symmetric τ_c fix resolves the 0→1 maxout bias")
    elif best_mean < 9.0:
        verdict = (f"orbit coarse-graining COMPARABLE to majority vote — "
                   f"Option {best_opt} achieves {best_mean:.1f}% (near 6.4% AFCA baseline); "
                   f"symmetric τ_c fix substantially reduces asymmetry bias from 18.5%")
    else:
        verdict = (f"orbit coarse-graining NOT COMPETITIVE with majority vote even with symmetric τ_c — "
                   f"best option {best_opt} achieves {best_mean:.1f}% vs 6.4% AFCA baseline; "
                   f"orbit structure too noisy for SR discrimination at M=7, L=500")
else:
    best_opt = "neither"
    verdict = "orbit coarse-graining inconclusive — insufficient stable seeds found in time limit"

print()
print(f"Verdict: {verdict}")

# ── Figures ───────────────────────────────────────────────────────────────────
FIGURES_DIR = 'specs/IN-PROCESS/epic_072_gte_ontological_unification/figures'
os.makedirs(FIGURES_DIR, exist_ok=True)

fig, axes = plt.subplots(2, 2, figsize=(13, 10))

for opt_idx, (opt_name, hi_seeds, lo_seeds, errors, paired_res, tau_bg) in enumerate([
    ("Option A: Symmetric LUT\n(0→1=1→0=2)", stable_hi_v_a, low_v_seeds_a, errors_a, paired_a, tau_bg_a),
    ("Option B: Orbit-fraction τ_c", stable_hi_v_b, low_v_seeds_b, errors_b, paired_b, tau_bg_b),
]):
    ax_scatter = axes[opt_idx][0]
    ax_err = axes[opt_idx][1]

    if hi_seeds:
        hg = [r['gamma'] for _, r in hi_seeds if r['ratio'] is not None]
        hr = [r['ratio'] for _, r in hi_seeds if r['ratio'] is not None]
        ax_scatter.scatter(hg, hr, c='red', s=50, alpha=0.7, label='High-v seeds')
    if lo_seeds:
        lg = [r['gamma'] for _, r in lo_seeds if r['ratio'] is not None]
        lr = [r['ratio'] for _, r in lo_seeds if r['ratio'] is not None]
        ax_scatter.scatter(lg, lr, c='blue', s=50, alpha=0.7, label='Low-v refs')
    if lo_seeds and lo_seeds[0][1]['ratio'] is not None:
        ref_r = lo_seeds[0][1]['ratio']
        g_range = np.linspace(1.0, 2.2, 100)
        ax_scatter.plot(g_range, ref_r * g_range, 'k--', alpha=0.5, label='SR ∝ γ')
    ax_scatter.set_xlabel('γ (Lorentz factor)')
    ax_scatter.set_ylabel('τ_c ratio (glider/ether)')
    ax_scatter.set_title(f'{opt_name}\nτ_c ratio vs γ  (bg={tau_bg:.4f})')
    ax_scatter.legend(fontsize=8)
    ax_scatter.grid(True, alpha=0.3)

    if errors:
        mean_e = float(np.mean(errors))
        sorted_e = sorted(errors)
        colors = ['green' if e < 10 else 'orange' for e in sorted_e]
        ax_err.bar(range(len(sorted_e)), sorted_e, color=colors)
        ax_err.axhline(mean_e, color='red', linestyle='--', label=f'Mean={mean_e:.1f}%')
        ax_err.axhline(6.4, color='blue', linestyle=':', label='Rank 31-ACS 6.4%')
        ax_err.axhline(18.5, color='gray', linestyle=':', label='Rank 54A 18.5%')
        ax_err.set_xlabel('Pair index (sorted by error)')
        ax_err.set_ylabel('SR error (%)')
        ax_err.set_title(f'{opt_name}\nSR error per pair (mean={mean_e:.1f}%)')
        ax_err.legend(fontsize=8)
        ax_err.grid(True, alpha=0.3)
    else:
        ax_err.text(0.5, 0.5, 'No pairs (insufficient seeds)', ha='center', va='center',
                    transform=ax_err.transAxes)
        ax_err.set_title(f'{opt_name}\nSR error — INCONCLUSIVE')

fig.suptitle('Rank 54B: Orbit AFCA Symmetric τ_c Fix\n'
             'Option A (symmetric LUT) vs Option B (orbit-fraction τ_c)', fontsize=11)
fig.tight_layout(rect=[0, 0, 1, 0.94])

fig_path = f'{FIGURES_DIR}/rank54b_orbit_afca_symmetric.png'
fig.savefig(fig_path, dpi=150, bbox_inches='tight')
plt.close(fig)
print(f"\nFigure saved: {fig_path}")

# ── JSON results ──────────────────────────────────────────────────────────────
RESULTS_FILE = 'rank54b_results.json'

results = {
    'rank': '54B',
    'test': 'orbit_afca_symmetric_tau_c',
    'date': time.strftime('%Y-%m-%d'),
    'parameters': {
        'outer_L': OUTER_L,
        'M': 7,
        'inner_rule': 'fmdl_Z7',
        'coarse_graining': 'orbit_classification',
        'orbit_values': sorted(list(ORBIT_VALUES)),
        'orbit7_base': list(ORBIT7_BASE),
        'c_eff': C_EFF,
        'orbit_fraction_steps_B': ORBIT_FRACTION_STEPS,
    },
    'option_a': {
        'name': 'symmetric_lut',
        'lut': {'0,0': 0, '0,1': 2, '1,0': 2, '1,1': 0},
        'tau_bg': round(tau_bg_a, 6),
        'n_hi_v_seeds': len(stable_hi_v_a),
        'n_lo_v_seeds': len(low_v_seeds_a),
        'n_pairs': len(errors_a),
        'mean_sr_error_pct': round(mean_err_a, 3) if mean_err_a is not None else None,
        'best_pair_error_pct': round(best_a['error_pct'], 3) if best_a is not None else None,
        'errors_per_pair': [round(e, 3) for e in errors_a],
    },
    'option_b': {
        'name': 'orbit_fraction',
        'orbit_fraction_steps': ORBIT_FRACTION_STEPS,
        'frac_orbit': round(frac_orbit, 6),
        'frac_vacuum': round(frac_vacuum, 6),
        'lut': {'0,0': round(frac_vacuum, 6), '0,1': round(frac_orbit, 6),
                '1,0': round(frac_vacuum, 6), '1,1': round(frac_orbit, 6)},
        'tau_bg': round(tau_bg_b, 6),
        'n_hi_v_seeds': len(stable_hi_v_b),
        'n_lo_v_seeds': len(low_v_seeds_b),
        'n_pairs': len(errors_b),
        'mean_sr_error_pct': round(mean_err_b, 3) if mean_err_b is not None else None,
        'best_pair_error_pct': round(best_b['error_pct'], 3) if best_b is not None else None,
        'errors_per_pair': [round(e, 3) for e in errors_b],
    },
    'comparison': {
        'rank54a_asymmetric_mean_pct': 18.5,
        'rank54a_asymmetric_best_pct': 4.1,
        'rank31_acs_true_afca_majority_pct': 6.4,
    },
    'verdict': verdict,
}

with open(RESULTS_FILE, 'w') as f:
    json.dump(results, f, indent=2)

fsize = os.path.getsize(RESULTS_FILE)
print(f"Results saved: {RESULTS_FILE} ({fsize} bytes)")
if fsize > 1_000_000:
    print("WARNING: results file exceeds 1 MB — check for unbounded data")

signal.alarm(0)
elapsed = time.time() - _t0
print(f"\nTotal elapsed: {elapsed:.2f}s")
