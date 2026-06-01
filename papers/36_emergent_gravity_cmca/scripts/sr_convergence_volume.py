from pathlib import Path
SCRIPT_DIR = Path(__file__).resolve().parent
#!/usr/bin/env python3
"""
Rank 52-SCV: SR Statistical Convergence Test
EPIC_072

Tests whether the ~8.7% Round 19 SR residual is statistical (reduces as 1/√n)
or systematic (irreducible lattice correction).

Design:
- Fixed L=2000 (prevents periodic wrap-around for all run lengths; at v=0.532,
  1800 steps moves 958 cells from center 1000, well within L=2000).
- Vary n_steps: [200, 500, 1000, 1800]; record n_localized (steps with diff≤60)
  and τ_c paired ratio for each run length.
- Canonical γ=1.658 from Round 19 (L=500, n_steps=200) is used as the fixed
  SR prediction. We do NOT re-estimate γ via position tracking at longer run lengths
  (the diff-CoM drifts at long times due to glider wake growth, giving spurious γ).
  The convergence question is purely about the τ_c ratio: does hi_ratio/lo_ratio
  converge toward 1.658 as n_localized increases?

B ≈ 0 → residual is statistical, reducible with longer runs.
B > 0.03 → systematic floor exists, irreducible at this (M, c_eff) setting.
"""

import signal
import sys
import os
import time
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# --- Wall-clock timeout (3 minutes) ---
TIMEOUT = 180

def _timeout_handler(signum, frame):
    print(f"\nTIMEOUT: wall-clock limit {TIMEOUT}s reached. Saving partial results.")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT)

# --- CA constants (all from Round 19 canonical) ---
ETHER14 = np.array([1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0], dtype=np.uint8)
LUT110 = np.array([(110 >> i) & 1 for i in range(8)], dtype=np.uint8)
C_EFF = 2 / 3
M = 7

# Fixed τ_lut from Round 19: τ_lut[curr_bit][target_bit]
TAU_LUT = np.array([[0, 1], [1, 0]], dtype=np.float32)

# Canonical high-v seed: γ=1.658, v=+0.532 c_eff (Round 19, L=500, n_steps=200)
CANON_SEED = "0100101001"
CANONICAL_GAMMA = 1.658   # Round 19 gold-standard measurement

# Known low-v seeds from Round 19 — fast path before scanning
KNOWN_LOW_V = [
    "0000000111",   # v=-0.017, γ≈1.000, ratio≈0.919 (Round 19 best ref)
    "0000000000",
    "0000011011",
    "0010110011",
    "0011000000",
    "0000001110",
    "0000011100",
]

OUTER_L = 2000   # wrap-free for n_steps ≤ 1800 at v=0.532


def run_outer(state: np.ndarray) -> np.ndarray:
    l = np.roll(state, 1).astype(np.int32)
    c = state.astype(np.int32)
    r = np.roll(state, -1).astype(np.int32)
    return LUT110[(l << 2) | (c << 1) | r]


def phase12_center(outer_l: int) -> int:
    """Return nearest center position with c % 14 == 12."""
    c_base = outer_l // 2
    c = c_base - ((c_base - 12) % 14)
    if c < 0:
        c += 14
    if c >= outer_l:
        c -= 14
    return c


def build_ether_base(outer_l: int) -> np.ndarray:
    return np.array([ETHER14[i % 14] for i in range(outer_l)], dtype=np.uint8)


def run_and_collect(seed_str: str, ether_base: np.ndarray, n_steps: int) -> dict:
    """
    Run seed for n_steps, return per-step τ_c arrays (g_tau, e_tau, n_diff).
    No stability filtering — caller decides what steps to use.
    """
    outer_l = len(ether_base)
    seed = np.array([int(b) for b in seed_str], dtype=np.uint8)
    c = phase12_center(outer_l)

    tape = ether_base.copy()
    for j, bit in enumerate(seed):
        tape[(c + j) % outer_l] = bit

    s_tape = tape.copy()
    s_ref = ether_base.copy()

    g_taus_all: list[float] = []
    e_taus_all: list[float] = []
    n_diffs: list[int] = []

    for _ in range(n_steps):
        s_tape_next = run_outer(s_tape)
        s_ref_next = run_outer(s_ref)

        diff = s_tape != s_ref
        diff_pos = np.where(diff)[0]
        n_diff = len(diff_pos)
        n_diffs.append(n_diff)

        if 2 <= n_diff <= 60:
            taus = TAU_LUT[s_tape.astype(int), s_tape_next.astype(int)]
            g_taus_all.append(float(taus[diff].mean()))
            ndiff_mask = ~diff
            e_taus_all.append(float(taus[ndiff_mask].mean()) if ndiff_mask.sum() > 0 else 0.43)
        else:
            g_taus_all.append(float('nan'))
            e_taus_all.append(float('nan'))

        s_tape = s_tape_next
        s_ref = s_ref_next

    return {
        'g_taus': np.array(g_taus_all),
        'e_taus': np.array(e_taus_all),
        'n_diffs': np.array(n_diffs)
    }


def tau_ratio_from_data(data: dict) -> tuple[float, int]:
    """Compute (τ_c ratio, n_localized) from run_and_collect output."""
    valid = np.isfinite(data['g_taus']) & np.isfinite(data['e_taus'])
    n_loc = int(valid.sum())
    if n_loc < 5:
        return float('nan'), 0
    ratio = float(np.nanmean(data['g_taus'][valid])) / float(np.nanmean(data['e_taus'][valid]))
    return ratio, n_loc


def test_seed_reference(seed_str: str, ether_base: np.ndarray,
                        n_steps: int = 200, min_stable: int = 30) -> dict | None:
    """Lightweight test for finding low-v seeds. Returns velocity info."""
    outer_l = len(ether_base)
    seed = np.array([int(b) for b in seed_str], dtype=np.uint8)
    c = phase12_center(outer_l)
    tape = ether_base.copy()
    for j, bit in enumerate(seed):
        tape[(c + j) % outer_l] = bit

    s_tape = tape.copy()
    s_ref = ether_base.copy()
    positions: list[float] = []

    for _ in range(n_steps):
        s_tape_next = run_outer(s_tape)
        s_ref_next = run_outer(s_ref)
        diff = s_tape != s_ref
        diff_pos = np.where(diff)[0]
        if 2 <= len(diff_pos) <= 60:
            positions.append(float(diff_pos.mean()))
        s_tape = s_tape_next
        s_ref = s_ref_next

    if len(positions) < min_stable:
        return None
    v = float(np.polyfit(np.arange(len(positions)), np.array(positions), 1)[0])
    v_over_c = abs(v / C_EFF)
    if v_over_c >= 1.0:
        return None
    gamma = 1.0 / np.sqrt(max(1e-12, 1.0 - v_over_c**2))
    return {'v': round(v, 5), 'v_over_c': round(v_over_c, 5), 'gamma': round(gamma, 5)}


def find_lo_v_seeds(ether_base: np.ndarray, n_needed: int = 3,
                    budget_s: float = 20.0) -> list:
    """Find (seed_str, v_info) pairs with |v/c| < 0.1 using short reference runs."""
    lo_v: list = []
    t0 = time.time()
    for seed_str in KNOWN_LOW_V:
        if time.time() - t0 > budget_s:
            break
        r = test_seed_reference(seed_str, ether_base, n_steps=200, min_stable=20)
        if r and r['v_over_c'] < 0.1:
            lo_v.append((seed_str, r))
            if len(lo_v) >= n_needed:
                return lo_v
    for ic in range(0, 2**10):
        if time.time() - t0 > budget_s or len(lo_v) >= n_needed:
            break
        seed_str = bin(ic)[2:].zfill(10)
        if seed_str == CANON_SEED or any(seed_str == k for k, _ in lo_v):
            continue
        r = test_seed_reference(seed_str, ether_base, n_steps=200, min_stable=20)
        if r and r['v_over_c'] < 0.1:
            lo_v.append((seed_str, r))
    return lo_v


# --- Setup ---
print("=" * 70)
print("Rank 52-SCV: SR Statistical Convergence Test")
print(f"L={OUTER_L} (fixed, wrap-free ≤1800 steps), M={M}, c_eff={C_EFF:.4f}")
print(f"Canon seed: {CANON_SEED}  Canonical γ (Round 19 gold standard): {CANONICAL_GAMMA}")
print("=" * 70)

ether_base = build_ether_base(OUTER_L)
c_inj = phase12_center(OUTER_L)
print(f"Injection center: c={c_inj}, c%14={c_inj % 14}")

# Find 3 low-v reference seeds at n_steps=200
print("\nFinding low-v reference seeds (|v/c|<0.1, n_steps=200 reference run)...")
lo_v_seeds = find_lo_v_seeds(ether_base, n_needed=3, budget_s=20.0)
if not lo_v_seeds:
    print("ERROR: No low-v reference seeds found. Aborting.")
    sys.exit(1)
print(f"Found {len(lo_v_seeds)} low-v seeds:")
for s, r in lo_v_seeds:
    print(f"  {s}: v/c={r['v_over_c']:.5f}, γ={r['gamma']:.5f}")

# Canonical SR prediction = γ_hi / γ_lo (lo-v seeds have γ≈1)
# Use canonical γ_hi=1.658 (Round 19) and γ_lo from reference run.
# Note: γ_lo ≈ 1.000 for all lo-v seeds (|v/c| < 0.1 → γ < 1.005)
lo_gammas = [r['gamma'] for _, r in lo_v_seeds]
canonical_preds = [CANONICAL_GAMMA / g for g in lo_gammas]
print(f"SR canonical predictions: {[f'{p:.4f}' for p in canonical_preds]}")

# --- Pre-run ALL seeds for maximum n_steps to get full data arrays ---
N_MAX = 1800
print(f"\nPre-running all seeds for {N_MAX} steps (reused for all n_steps values)...")

t_pre = time.time()
hi_data = run_and_collect(CANON_SEED, ether_base, n_steps=N_MAX)
lo_data_list = [run_and_collect(s, ether_base, n_steps=N_MAX) for s, _ in lo_v_seeds]
print(f"Pre-run complete in {time.time()-t_pre:.1f}s")

# Report glider lifetime (how many steps it stays localized)
hi_n_loc_total = int(np.isfinite(hi_data['g_taus']).sum())
print(f"Hi-v glider: {hi_n_loc_total}/{N_MAX} steps localized (diff≤60 cells)")

# --- Test matrix: vary n_steps (use first n_steps of pre-run data) ---
N_STEPS_LIST = [200, 500, 1000, 1800]

results = []
for n_steps in N_STEPS_LIST:
    elapsed = time.time() - (t_pre - 0)  # time from start
    print(f"\n--- n_steps={n_steps} ---")

    # Slice first n_steps from pre-run data
    hi_sub = {k: v[:n_steps] for k, v in hi_data.items()}
    hi_ratio, hi_n_loc = tau_ratio_from_data(hi_sub)

    if hi_n_loc < 5:
        print(f"  Hi-v: not enough localized steps ({hi_n_loc})")
        results.append({'n_steps': n_steps, 'status': 'insufficient',
                        'n_localized': hi_n_loc, 'best_err': None, 'mean_err': None})
        continue

    print(f"  Hi-v: τ_c ratio={hi_ratio:.4f}, n_localized={hi_n_loc}")

    # Paired ratios against each lo-v seed
    pair_errs = []
    for (lo_seed, lo_vinfo), lo_data, canon_pred in zip(lo_v_seeds, lo_data_list, canonical_preds):
        lo_sub = {k: v[:n_steps] for k, v in lo_data.items()}
        lo_ratio, lo_n_loc = tau_ratio_from_data(lo_sub)
        if lo_n_loc < 5 or np.isnan(lo_ratio):
            continue
        paired = hi_ratio / lo_ratio
        err = abs(paired - canon_pred) / canon_pred * 100.0
        pair_errs.append(round(err, 2))
        print(f"    vs {lo_seed}: paired={paired:.4f}, pred={canon_pred:.4f}, err={err:.1f}%")

    if not pair_errs:
        results.append({'n_steps': n_steps, 'status': 'no_pairs',
                        'n_localized': hi_n_loc, 'best_err': None, 'mean_err': None})
        continue

    best_err = float(min(pair_errs))
    mean_err = float(np.mean(pair_errs))

    results.append({
        'n_steps': n_steps,
        'status': 'ok',
        'L': OUTER_L,
        'hi_ratio': round(hi_ratio, 5),
        'n_localized': hi_n_loc,
        'n_low_v_seeds': len(pair_errs),
        'pair_errors': pair_errs,
        'best_err': round(best_err, 2),
        'mean_err': round(mean_err, 2)
    })
    print(f"  n_localized={hi_n_loc}, best_err={best_err:.1f}%, mean_err={mean_err:.1f}%")

signal.alarm(0)  # cancel timeout

# --- Summary table ---
ok_results = [r for r in results if r['status'] == 'ok']

print("\n\n=== Rank 52-SCV: SR Statistical Convergence ===")
print(f"Canonical prediction = γ_hi/γ_lo = {CANONICAL_GAMMA}/1.000 = {CANONICAL_GAMMA}")
print(f"(γ_hi from Round 19 gold-standard; using fixed value avoids long-run drift)\n")
hdr = f"{'steps':>7} {'localized':>10} {'hi_ratio':>10} {'best_err':>10} {'mean_err':>10}"
print(hdr)
print("-" * len(hdr))
for r in results:
    hr = f"{r.get('hi_ratio','N/A'):.5f}" if isinstance(r.get('hi_ratio'), float) else "N/A"
    be = f"{r['best_err']:.1f}%" if r.get('best_err') is not None else "N/A"
    me = f"{r['mean_err']:.1f}%" if r.get('mean_err') is not None else "N/A"
    print(f"{r['n_steps']:>7} {r['n_localized']:>10} {hr:>10} {be:>10} {me:>10}")

# --- Convergence fit ---
A_fit = B_fit = None
fit_success = False
verdict = "INSUFFICIENT DATA (need ≥3 successful cases)"
projections: dict = {}

if len(ok_results) >= 3:
    n_loc = np.array([r['n_localized'] for r in ok_results], dtype=float)
    errs = np.array([r['mean_err'] / 100.0 for r in ok_results], dtype=float)

    def model(n, A, B):
        return A / np.sqrt(n) + B

    try:
        popt, _ = curve_fit(model, n_loc, errs,
                            p0=[0.05, 0.10],
                            bounds=([0.0, 0.0], [5.0, 1.0]),
                            maxfev=5000)
        A_fit, B_fit = float(popt[0]), float(popt[1])
        fit_success = True

        e_10k = A_fit / np.sqrt(10_000) + B_fit
        e_100k = A_fit / np.sqrt(100_000) + B_fit
        projections = {
            'n_10000': round(e_10k * 100, 3),
            'n_100000': round(e_100k * 100, 3)
        }

        if B_fit < 0.02:
            verdict = ("PRIMARILY STATISTICAL — residual reducible with longer runs; "
                       f"systematic floor < 2%")
        elif B_fit < 0.05:
            verdict = (f"MIXED — systematic floor ≈ {B_fit*100:.1f}% "
                       f"with statistical amplitude A={A_fit:.4f}")
        else:
            verdict = (f"SYSTEMATIC FLOOR EXISTS at {B_fit*100:.1f}% — "
                       f"irreducible at (M={M}, c_eff={C_EFF:.3f})")

        print(f"\nConvergence fit: error ≈ A/√n_localized + B")
        print(f"  A = {A_fit:.4f}  (statistical noise amplitude)")
        print(f"  B = {B_fit:.4f}  (systematic floor)")
        print(f"  Estimated error at n_localized =  10,000: {e_10k*100:.2f}%")
        print(f"  Estimated error at n_localized = 100,000: {e_100k*100:.2f}%")

    except Exception as ex:
        print(f"\nFit failed: {ex}")
        verdict = f"FIT FAILED: {ex}"

elif len(ok_results) == 2:
    d_err = ok_results[1]['mean_err'] - ok_results[0]['mean_err']
    verdict = (f"ONLY 2 DATA POINTS — Δerr={d_err:+.1f}% from "
               f"n={ok_results[0]['n_localized']} to n={ok_results[1]['n_localized']}; "
               f"{'flat/increasing (systematic)' if d_err >= 0 else 'decreasing (statistical)'}")

print(f"\nVerdict:\n  {verdict}")

# --- Plot ---
fig, axes = plt.subplots(1, 2, figsize=(13, 5))

# Left: error vs n_localized
ax = axes[0]
if ok_results:
    n_loc_arr = np.array([r['n_localized'] for r in ok_results])
    err_arr = np.array([r['mean_err'] for r in ok_results])

    ax.scatter(n_loc_arr, err_arr, s=100, zorder=5, color='steelblue',
               label='Mean SR error (3 lo-v seeds)')
    for x, y, r in zip(n_loc_arr, err_arr, ok_results):
        ax.annotate(f"steps={r['n_steps']}", (x, y),
                    textcoords='offset points', xytext=(5, 5), fontsize=9)

    if fit_success and A_fit is not None and B_fit is not None:
        n_fit = np.logspace(np.log10(max(10, n_loc_arr.min() * 0.5)),
                            np.log10(n_loc_arr.max() * 3.0), 300)
        ax.plot(n_fit, (A_fit / np.sqrt(n_fit) + B_fit) * 100, 'r--', linewidth=1.8,
                label=f'Fit: {A_fit:.4f}/√n + {B_fit:.4f}')
        ax.axhline(B_fit * 100, color='orange', linestyle=':', linewidth=1.4, alpha=0.85,
                   label=f'Systematic floor B={B_fit*100:.2f}%')

ax.set_xscale('log')
ax.set_xlabel('n_localized', fontsize=11)
ax.set_ylabel('Mean SR error (%)', fontsize=11)
ax.set_title('SR Error vs Run Length\n(canonical pred = 1.658 fixed from Round 19)', fontsize=10)
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)

# Right: τ_c ratio of hi-v seed vs n_steps
ax2 = axes[1]
if ok_results:
    hi_ratios = [r['hi_ratio'] for r in ok_results]
    n_steps_arr = [r['n_steps'] for r in ok_results]
    ax2.plot(n_steps_arr, hi_ratios, 'bo-', markersize=8, linewidth=1.5,
             label='Hi-v τ_c ratio (0100101001)')
    ax2.axhline(CANONICAL_GAMMA, color='red', linestyle='--', linewidth=1.5,
                label=f'Target γ = {CANONICAL_GAMMA}')
    ax2.set_xlabel('n_steps', fontsize=11)
    ax2.set_ylabel('τ_c ratio (hi-v seed)', fontsize=11)
    ax2.set_title('Does τ_c ratio converge toward γ=1.658?', fontsize=10)
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3)

plt.suptitle('Rank 52-SCV: SR Statistical vs Systematic Convergence  (L=2000, wrap-free)',
             fontsize=11, y=1.01)
plt.tight_layout()

plot_path = 'rank52_scv_convergence.png'
plt.savefig(plot_path, dpi=150, bbox_inches='tight')
plt.close()
print(f"\nPlot saved: {plot_path}")

# --- Save JSON ---
output = {
    'rank': '52-SCV',
    'date': '2026-05-21',
    'description': 'SR statistical vs systematic convergence (L=2000, canonical pred fixed)',
    'design_note': (
        'Fixed L=2000 to prevent wrap-around distortion. Canonical gamma=1.658 from '
        'Round 19 used as fixed SR prediction (not re-estimated per run length). '
        'Error = |hi_ratio/lo_ratio - 1.658| / 1.658.'
    ),
    'parameters': {
        'OUTER_L': OUTER_L,
        'canonical_seed': CANON_SEED,
        'canonical_gamma': CANONICAL_GAMMA,
        'M': M, 'c_eff': C_EFF,
        'tau_lut': [[0, 1], [1, 0]],
        'injection_center': c_inj,
        'lo_v_seeds': [(s, r) for s, r in lo_v_seeds]
    },
    'glider_lifetime_steps': hi_n_loc_total,
    'convergence_fit': {
        'A': round(A_fit, 6) if A_fit is not None else None,
        'B': round(B_fit, 6) if B_fit is not None else None,
        'fit_success': fit_success,
        'verdict': verdict,
        'projections': projections
    },
    'results': results
}

json_path = 'rank52_scv_results.json'
with open(json_path, 'w') as f:
    json.dump(output, f, separators=(',', ':'))

json_kb = os.path.getsize(json_path) // 1024
print(f"Results saved: {json_path} ({json_kb} KB)")
print("\nRank 52-SCV complete.")
