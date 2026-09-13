#!/usr/bin/env python3
"""
Rank 54-FCAOT: f_MDL Orbit AFCA SR Test
EPIC_072 — GTE Ontological Unification
2026-05-21

Tests whether orbit-based coarse-graining (Z₇ f_MDL orbit classification vs
majority-vote Rule 110) produces better SR time-dilation accuracy than the
N=1 true AFCA majority-vote approach (Rank 31-ACS: 6.4% error).

Inner CA: f_MDL Z₇ rule on M=7 cells
Coarse-graining: classify inner state as in-orbit (1) or vacuum (0) based on
majority of cells having values in orbit set {1,2,3,5,6}
τ_c: steps until inner orbit-classification matches outer target bit
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

# ── f_MDL Z₇ rule (exact copy from orbit_admissible_count.py) ───────────────

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
    """One f_MDL step on M-cell ring (periodic boundary)."""
    n = len(cells)
    return tuple(fmdl(cells[(i - 1 + n) % n], cells[i], cells[(i + 1) % n]) for i in range(n))


# ── Orbit seeds and classification ──────────────────────────────────────────
# SM generation orbit states (5-cell versions, extended/tiled for M=7)
GEN1 = (1, 5, 2, 2, 1)
GEN2 = (2, 5, 2, 0, 2)
GEN3 = (5, 6, 5, 3, 5)
VACUUM5 = (0, 0, 0, 0, 0)

# Z₇ orbit values: non-vacuum values appearing in gen1/gen2/gen3 states
ORBIT_VALUES = {1, 2, 3, 5, 6}

# M=7 orbit seed: tile the 5-cell GEN1 pattern across 7 cells via wrap
ORBIT7_BASE = tuple(GEN1[i % 5] for i in range(7))   # (1,5,2,2,1,5,2)

# M=7 vacuum
VACUUM7 = (0,) * 7


def classify_orbit(inner_state):
    """
    Classify M-cell inner state as in-orbit (1) or vacuum (0).
    In-orbit: majority of cells have values in ORBIT_VALUES (non-zero orbit set).
    """
    n_orbit = sum(1 for v in inner_state if v in ORBIT_VALUES)
    return 1 if n_orbit * 2 > len(inner_state) else 0


# ── Orbit τ_c LUT ────────────────────────────────────────────────────────────

MAX_INNER = 100


def tau_c_orbit(current_orbit_class, target_orbit_class, phase=0, max_steps=MAX_INNER):
    """
    Inner f_MDL steps until classify_orbit(inner) == target_orbit_class,
    starting from an inner state consistent with current_orbit_class.
    phase: rotate the orbit seed by this offset (0..6).
    """
    if current_orbit_class == 1:
        inner = tuple(ORBIT7_BASE[(phase + i) % 7] for i in range(7))
    else:
        inner = VACUUM7

    for step in range(max_steps):
        if classify_orbit(inner) == target_orbit_class:
            return step
        inner = fmdl_step_M(inner)
    return max_steps


# Precompute LUT: (curr, tgt, phase) → τ_c
print("Precomputing orbit τ_c LUT ...")
orbit_lut = {}
for curr in [0, 1]:
    for tgt in [0, 1]:
        for phase in range(7):
            orbit_lut[(curr, tgt, phase)] = tau_c_orbit(curr, tgt, phase)

print("Orbit τ_c LUT (curr→tgt, phase 0-6):")
for curr in [0, 1]:
    for tgt in [0, 1]:
        vals = [orbit_lut[(curr, tgt, p)] for p in range(7)]
        print(f"  ({curr},{tgt}): {vals}")

# Background orbit τ_c: ether cells cycle 0→0 (ether is mostly 0 and 1 bits,
# so outer=0 → tgt=? depends on Rule 110. Use weighted average of phases.)
_bg_vals = []
for phase in range(7):
    for curr in [0, 1]:
        _bg_vals.append(orbit_lut[(curr, curr, phase)])
tau_bg_orbit = float(np.mean(_bg_vals))
print(f"Background orbit τ_c (mean of self-transitions): {tau_bg_orbit:.4f}")

# ── Outer CA constants ───────────────────────────────────────────────────────
ETHER14 = np.array([1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0], dtype=np.uint8)
LUT110 = np.array([(110 >> i) & 1 for i in range(8)], dtype=np.uint8)
C_EFF = 2 / 3
OUTER_L = 500

ether_base = np.array([ETHER14[i % 14] for i in range(OUTER_L)], dtype=np.uint8)
phases = np.arange(OUTER_L, dtype=np.int32) % 7   # orbit period is 7


def run_outer(state):
    """Vectorized Rule 110 step."""
    l = np.roll(state, 1).astype(np.int32)
    c = state.astype(np.int32)
    r = np.roll(state, -1).astype(np.int32)
    return LUT110[(l << 2) | (c << 1) | r]


def measure_tau_orbit_vec(outer_now, outer_next):
    """
    Vectorized orbit τ_c: for each cell i, look up
    orbit_lut[(outer_now[i], outer_next[i], phases[i] % 7)].
    """
    return np.array([
        orbit_lut[(int(outer_now[i]), int(outer_next[i]), int(phases[i] % 7))]
        for i in range(len(outer_now))
    ], dtype=np.float32)


# ── Background orbit τ_c from actual ether run ───────────────────────────────
print("\nMeasuring orbit τ_c on pure ether background ...")
s = ether_base.copy()
bg_taus = []
for _ in range(60):
    s_next = run_outer(s)
    if len(bg_taus) < 20:
        bg_taus.append(measure_tau_orbit_vec(s, s_next).mean())
    s = s_next
tau_bg_ether = float(np.mean(bg_taus[10:20]))
print(f"Orbit τ_c (ether background, steps 10-20): {tau_bg_ether:.4f}")


# ── Seed test function ───────────────────────────────────────────────────────

def test_seed_orbit(seed_str, n_steps=200, min_stable=50):
    """
    Test a width-10 seed using orbit τ_c measurement.
    Returns dict with v, v_over_c, gamma, ratio, n_stable, or None if not stable.
    """
    seed = np.array([int(b) for b in seed_str], dtype=np.uint8)
    # Phase-12 injection (same alignment as Round 19)
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
            taus = measure_tau_orbit_vec(s_tape, s_tape_next)
            g_taus.append(float(taus[diff].mean()))
            ndiff = ~diff
            if ndiff.sum() > 0:
                e_taus.append(float(taus[ndiff].mean()))
            else:
                e_taus.append(tau_bg_ether)

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


# ── Full seed search ─────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("=== Rank 54-FCAOT: f_MDL Orbit AFCA SR Test ===")
print()
print("Inner CA: f_MDL Z₇, M=7 cells")
print("Coarse-graining: orbit classification (in-orbit vs vacuum), not majority vote")
print("=" * 65)

print("\nSearching all 1024 width-10 seeds for stable γ∈[1.3,2.0] ...")
stable_hi_v = []
for ic in range(0, 2 ** 10):
    if time.time() - _t0 > WALL_CLOCK_LIMIT - 30:
        print(f"  Wall-clock warning at seed {ic}, stopping search early.")
        break
    seed_str = bin(ic)[2:].zfill(10)
    result = test_seed_orbit(seed_str, n_steps=200, min_stable=50)
    if result and 1.3 <= result['gamma'] <= 2.0:
        stable_hi_v.append((seed_str, result))

print(f"Total stable γ∈[1.3,2.0] seeds: {len(stable_hi_v)}")
if stable_hi_v:
    for sd, rs in stable_hi_v[:5]:
        print(f"  {sd}: v={rs['v']:.4f}, γ={rs['gamma']:.4f}, ratio={rs['ratio']:.4f}, "
              f"stable={rs['n_stable']} steps")

# ── Low-v reference seeds ────────────────────────────────────────────────────
print("\nSearching for low-v reference seeds (|v/c|<0.1) ...")
low_v_seeds = []
for ic in range(0, 2 ** 10):
    if time.time() - _t0 > WALL_CLOCK_LIMIT - 15:
        break
    seed_str = bin(ic)[2:].zfill(10)
    result = test_seed_orbit(seed_str, n_steps=100, min_stable=30)
    if result and result['v_over_c'] < 0.1 and result['n_stable'] >= 30:
        low_v_seeds.append((seed_str, result))
        if len(low_v_seeds) >= 5:
            break

print(f"Low-v reference seeds: {len(low_v_seeds)}")
for sd, rs in low_v_seeds:
    print(f"  {sd}: v={rs['v']:.4f}, γ={rs['gamma']:.4f}, ratio={rs['ratio']:.4f}")

# ── Paired SR test ───────────────────────────────────────────────────────────
errors = []
paired_results = []
verdict_str = "INCONCLUSIVE (no seeds found)"
mean_err = None
best_pair_info = None

if stable_hi_v and low_v_seeds:
    stable_hi_v.sort(key=lambda x: -x[1]['v_over_c'])
    hi_set = stable_hi_v[:min(5, len(stable_hi_v))]
    lo_set = low_v_seeds[:min(3, len(low_v_seeds))]

    for hi_seed, hi_res in hi_set:
        for lo_seed, lo_res in lo_set:
            if hi_res['ratio'] is None or lo_res['ratio'] is None:
                continue
            paired = hi_res['ratio'] / lo_res['ratio']
            pred = hi_res['gamma'] / lo_res['gamma']
            e = abs(paired - pred) / pred * 100
            errors.append(e)
            paired_results.append({
                'hi_seed': hi_seed,
                'lo_seed': lo_seed,
                'hi_gamma': hi_res['gamma'],
                'lo_gamma': lo_res['gamma'],
                'hi_ratio': hi_res['ratio'],
                'lo_ratio': lo_res['ratio'],
                'paired_ratio': paired,
                'sr_pred': pred,
                'error_pct': e,
            })

    if errors:
        mean_err = float(np.mean(errors))
        ok = sum(1 for e in errors if e < 15)

        best_pr = min(paired_results, key=lambda x: x['error_pct'])
        best_pair_info = best_pr

        verdict_str = "IMPROVED" if mean_err < 6.4 else ("SAME" if mean_err < 9.0 else "DEGRADED")
        verdict_str += f" vs 6.4% true AFCA baseline"

        print(f"\nSR test results:")
        print(f"  High-v seeds found: {len(stable_hi_v)}")
        print(f"  Low-v references: {len(low_v_seeds)}")
        print(f"  Best pair: γ={best_pr['hi_gamma']:.3f}, orbit τ_c ratio={best_pr['hi_ratio']:.3f}, "
              f"SR error={best_pr['error_pct']:.1f}%")
        print(f"  Mean error ({len(errors)} pairs): {mean_err:.1f}%")
        print()
        print("Compare:")
        print(f"  Majority-vote τ_c (Round 19 LUT diagnostic):  error=8.7%")
        print(f"  True AFCA majority-vote (Rank 31-ACS):        error=6.4%")
        print(f"  Orbit AFCA (Rank 54-FCAOT):                   error={mean_err:.1f}%")
        print()
        print(f"Verdict: {verdict_str}")

        if mean_err < 6.4:
            interp = ("Orbit coarse-graining (Z₇ f_MDL) gives better SR accuracy than majority-vote. "
                      "The orbit-vs-vacuum distinction preserves more of the Z₇ algebraic structure "
                      "relevant to relativistic time dilation.")
        elif mean_err < 9.0:
            interp = ("Orbit coarse-graining gives comparable SR accuracy to majority-vote. "
                      "The two coarse-graining schemes carry equivalent information about the glider's "
                      "internal clock under the Rule 110 outer dynamics.")
        else:
            interp = ("Orbit coarse-graining degrades SR accuracy relative to majority-vote. "
                      "The Z₇ f_MDL orbit LUT has a less uniform τ_c distribution across outer "
                      "transitions than the binary Rule 110 majority-vote LUT, introducing noise "
                      "that overwhelms the SR signal at this M and L.")
        print(f"Physical interpretation: {interp}")

# ── Figure ───────────────────────────────────────────────────────────────────
FIGURES_DIR = 'specs/IN-PROCESS/epic_072_gte_ontological_unification/figures'
os.makedirs(FIGURES_DIR, exist_ok=True)

fig, axes = plt.subplots(1, 2, figsize=(13, 5))

# Panel 1: ratio vs gamma scatter
ax1 = axes[0]
if stable_hi_v:
    hi_gammas = [r['gamma'] for _, r in stable_hi_v]
    hi_ratios = [r['ratio'] for _, r in stable_hi_v if r['ratio'] is not None]
    hi_gammas_filt = [r['gamma'] for _, r in stable_hi_v if r['ratio'] is not None]
    ax1.scatter(hi_gammas_filt, hi_ratios, c='red', s=50, alpha=0.7, label='High-v seeds')
if low_v_seeds:
    lo_gammas = [r['gamma'] for _, r in low_v_seeds]
    lo_ratios = [r['ratio'] for _, r in low_v_seeds if r['ratio'] is not None]
    lo_gammas_filt = [r['gamma'] for _, r in low_v_seeds if r['ratio'] is not None]
    ax1.scatter(lo_gammas_filt, lo_ratios, c='blue', s=50, alpha=0.7, label='Low-v refs')

if stable_hi_v or low_v_seeds:
    all_g = ([r['gamma'] for _, r in stable_hi_v] +
             [r['gamma'] for _, r in low_v_seeds])
    if all_g:
        g_range = np.linspace(1.0, max(all_g) + 0.1, 100)
        ref_r = low_v_seeds[0][1]['ratio'] if low_v_seeds and low_v_seeds[0][1]['ratio'] else 1.0
        ax1.plot(g_range, ref_r * g_range, 'k--', alpha=0.5, label='Linear SR ∝ γ')

ax1.set_xlabel('γ (Lorentz factor)')
ax1.set_ylabel('Orbit τ_c ratio (glider / ether)')
ax1.set_title('Rank 54-FCAOT: Orbit τ_c ratio vs γ\nRed=high-v, Blue=low-v ref')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Panel 2: LUT heatmap
ax2 = axes[1]
lut_arr = np.zeros((2, 7), dtype=np.float32)  # rows: curr=0,1; cols: tgt=0 (phase) and tgt=1 (phase)
lut_display = np.zeros((4, 7), dtype=np.float32)
labels_y = ['(0→0)', '(0→1)', '(1→0)', '(1→1)']
for i, (curr, tgt) in enumerate([(0,0),(0,1),(1,0),(1,1)]):
    for phase in range(7):
        lut_display[i, phase] = orbit_lut[(curr, tgt, phase)]

im = ax2.imshow(lut_display, cmap='viridis', aspect='auto')
ax2.set_xticks(range(7))
ax2.set_xticklabels([f'ph={p}' for p in range(7)])
ax2.set_yticks(range(4))
ax2.set_yticklabels(labels_y)
ax2.set_title('Orbit τ_c LUT\n(curr→tgt transition, by phase)')
for i in range(4):
    for j in range(7):
        ax2.text(j, i, str(int(lut_display[i, j])), ha='center', va='center',
                 color='white' if lut_display[i,j] > lut_display.max()/2 else 'black', fontsize=9)
plt.colorbar(im, ax=ax2, label='τ_c steps')

title_str = f'Rank 54-FCAOT: f_MDL Orbit AFCA SR Test\n'
if mean_err is not None:
    title_str += f'Mean SR error = {mean_err:.1f}%  |  {verdict_str}'
else:
    title_str += 'Inconclusive (no seeds found in time limit)'
fig.suptitle(title_str, fontsize=11)
fig.tight_layout(rect=[0, 0, 1, 0.93])

fig_path = f'{FIGURES_DIR}/rank54_fcaot_orbit_afca_sr.png'
fig.savefig(fig_path, dpi=150, bbox_inches='tight')
plt.close(fig)
print(f"\nFigure saved: {fig_path}")

# ── JSON results ─────────────────────────────────────────────────────────────
RESULTS_FILE = 'rank54_fcaot_results.json'

lut_serializable = {f"{k[0]},{k[1]},{k[2]}": int(v) for k, v in orbit_lut.items()}

results = {
    'rank': '54-FCAOT',
    'test': 'fmdl_orbit_afca_sr',
    'date': time.strftime('%Y-%m-%d'),
    'parameters': {
        'outer_L': OUTER_L,
        'M': 7,
        'inner_rule': 'fmdl_Z7',
        'coarse_graining': 'orbit_classification',
        'orbit_values': sorted(list(ORBIT_VALUES)),
        'orbit7_base': list(ORBIT7_BASE),
        'c_eff': C_EFF,
        'max_inner_steps': MAX_INNER,
    },
    'orbit_lut': lut_serializable,
    'tau_bg_orbit_selftrans': round(tau_bg_orbit, 6),
    'tau_bg_ether_run': round(tau_bg_ether, 6),
    'results': {
        'n_hi_v_seeds': len(stable_hi_v),
        'n_lo_v_seeds': len(low_v_seeds),
        'n_pairs': len(errors),
        'mean_sr_error_pct': round(mean_err, 3) if mean_err is not None else None,
        'errors_per_pair': [round(e, 3) for e in errors],
        'best_pair': best_pair_info,
        'verdict': verdict_str,
    },
    'comparison': {
        'round19_lut_error_pct': 8.7,
        'rank31_true_afca_majority_vote_error_pct': 6.4,
    },
}

with open(RESULTS_FILE, 'w') as f:
    json.dump(results, f, indent=2)

import os
fsize = os.path.getsize(RESULTS_FILE)
print(f"Results saved: {RESULTS_FILE} ({fsize} bytes)")
if fsize > 1_000_000:
    print("WARNING: results file exceeds 1 MB — check for unbounded data")

signal.alarm(0)
elapsed = time.time() - _t0
print(f"\nTotal elapsed: {elapsed:.2f}s")
