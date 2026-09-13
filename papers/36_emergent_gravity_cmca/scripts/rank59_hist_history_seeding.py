#!/usr/bin/env python3
"""
Rank 59-HIST: History-Window Inner CA Seeding SR Test
EPIC_072 — GTE Ontological Unification
2026-05-22

Tests whether seeding the inner CA from each outer cell's last M transition
states improves SR accuracy over fixed ETHER14 seeding.

Hypothesis: glider cells accumulate richer (more varied) transition histories
than ether cells (higher flip rate 57% vs 42%, Rank 52B). History windows with
more 0→1 / 1→0 transitions could yield harder inner CA transitions (higher τ_c),
pulling τ_c(glider)/τ_c(ether) closer to γ=1.659.

Connection to MFRR §26: Δt_eff ∝ 1/(1+ρ) where ρ is local information density.
Richer transition history → higher ρ → higher τ_c.
"""

import signal
import sys
import time
import json

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ── Timeout ──────────────────────────────────────────────────────────────────
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
RESULTS_FILE = 'rank59_hist_results.json'

# Canonical glider (Round 19): v ≈ 0.532 cells/step, γ ≈ 1.659
CANONICAL_SEED = '0100101001'
V_CANONICAL = 0.532
GAMMA_TARGET = 1.0 / np.sqrt(1.0 - (V_CANONICAL / C_EFF) ** 2)

ether_base = np.array([ETHER14[i % 14] for i in range(OUTER_L)], dtype=np.uint8)

# Canonical phase-12 center injection
_CENTER = OUTER_L // 2 - ((OUTER_L // 2 - 12) % 14)


# ── CA step helpers ───────────────────────────────────────────────────────────

def run_outer(state: np.ndarray) -> np.ndarray:
    """Vectorized Rule 110 step (periodic BC)."""
    l = np.roll(state, 1).astype(np.int32)
    c = state.astype(np.int32)
    r = np.roll(state, -1).astype(np.int32)
    return LUT110[(l << 2) | (c << 1) | r]


# ── Vectorized batch τ_c ─────────────────────────────────────────────────────

def batch_tau_c(hist: np.ndarray, cell_idx: np.ndarray,
                targets: np.ndarray, max_steps: int = MAX_INNER) -> np.ndarray:
    """
    Compute τ_c for a batch of cells using their history windows as inner CA seeds.

    Parameters
    ----------
    hist      : (OUTER_L, M) per-cell history buffers
    cell_idx  : 1D array of cell indices
    targets   : target majority bit for each cell (same length as cell_idx)
    max_steps : inner CA step limit

    Returns
    -------
    Float array of τ_c values, one per cell.
    """
    n = len(cell_idx)
    if n == 0:
        return np.array([], dtype=np.float32)

    states = hist[cell_idx].copy()          # (n, M)
    tgt = np.asarray(targets, dtype=np.uint8)
    results = np.full(n, max_steps, dtype=np.float32)
    done = np.zeros(n, dtype=bool)

    for step in range(max_steps):
        maj = (states.sum(axis=1) * 2 > M).astype(np.uint8)
        newly_done = (~done) & (maj == tgt)
        results[newly_done] = step
        done |= newly_done
        if done.all():
            break
        active = ~done
        s = states[active]                  # (n_active, M)
        l = np.roll(s, 1, axis=1).astype(np.int32)
        c = s.astype(np.int32)
        r = np.roll(s, -1, axis=1).astype(np.int32)
        states[active] = LUT110[(l << 2) | (c << 1) | r]

    return results


# ── History initialization ────────────────────────────────────────────────────

def make_history_ether14() -> np.ndarray:
    """Initialize history from ETHER14: each cell i gets ETHER14 phase-(i*M % 14)."""
    hist = np.empty((OUTER_L, M), dtype=np.uint8)
    for i in range(OUTER_L):
        for j in range(M):
            hist[i, j] = ETHER14[(i * M + j) % 14]
    return hist


def make_history_zero() -> np.ndarray:
    """Initialize history to all zeros."""
    return np.zeros((OUTER_L, M), dtype=np.uint8)


# ── SR test (single seed) ────────────────────────────────────────────────────

def test_seed(seed_str: str, init_mode: str = 'ether14',
              n_steps: int = 100, min_stable: int = 30,
              ether_sample_stride: int = 20) -> dict | None:
    """
    SR test for one seed using history-window inner CA seeding.

    Parameters
    ----------
    seed_str           : width-10 binary string
    init_mode          : 'ether14' or 'zero'
    n_steps            : outer CA steps
    min_stable         : minimum diff-active steps required
    ether_sample_stride: stride for sampling ether cells (reduces τ_c cost)

    Returns dict or None if not stable / out-of-range.
    """
    seed_arr = np.array([int(b) for b in seed_str], dtype=np.uint8)
    tape = ether_base.copy()
    for j, bit in enumerate(seed_arr):
        tape[(_CENTER + j) % OUTER_L] = bit

    hist = make_history_ether14() if init_mode == 'ether14' else make_history_zero()

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
            tgts_all = s_tape_next

            g_vals = batch_tau_c(hist, diff_pos, tgts_all[diff_pos])
            g_taus.append(float(g_vals.mean()))

            ndiff_pos = np.where(~diff)[0][::ether_sample_stride]
            if len(ndiff_pos) > 0:
                e_vals = batch_tau_c(hist, ndiff_pos, tgts_all[ndiff_pos])
                e_taus.append(float(e_vals.mean()))
            else:
                e_taus.append(0.4)

        # Update history: shift left by 1, append current outer state at right
        hist[:, :-1] = hist[:, 1:]
        hist[:, -1] = s_tape

        s_tape = s_tape_next
        s_ref = s_ref_next

    if len(positions) < min_stable:
        return None

    v = float(np.polyfit(np.arange(len(positions)), np.array(positions), 1)[0])
    v_over_c = abs(v / C_EFF)
    if v_over_c >= 1.0:
        return None

    gam = 1.0 / np.sqrt(1.0 - v_over_c ** 2)
    g_tau_mean = float(np.mean(g_taus)) if g_taus else None
    e_tau_mean = float(np.mean(e_taus)) if e_taus else None
    ratio = g_tau_mean / e_tau_mean if (g_tau_mean and e_tau_mean) else None

    return {
        'v': v,
        'v_over_c': v_over_c,
        'gamma': gam,
        'ratio': ratio,
        'n_stable': len(positions),
        'g_tau_mean': g_tau_mean,
        'e_tau_mean': e_tau_mean,
    }


# ── Full 1024-seed search ────────────────────────────────────────────────────

def run_full_search(init_mode: str, n_steps: int = 100, min_stable: int = 30,
                    ether_stride: int = 20):
    """
    Search all 1024 width-10 seeds, return hi-v (γ∈[1.3,2.0]) and lo-v results.
    """
    hi_v = []   # γ ∈ [1.3, 2.0]
    lo_v = []   # |v/c| < 0.1, n_stable >= 30

    for ic in range(1024):
        if time.time() - _t0 > WALL_LIMIT - 30:
            print(f"  [time budget] stopping at ic={ic}")
            break
        seed_str = bin(ic)[2:].zfill(10)
        res = test_seed(seed_str, init_mode=init_mode, n_steps=n_steps,
                        min_stable=min_stable, ether_sample_stride=ether_stride)
        if res is None:
            continue
        if 1.3 <= res['gamma'] <= 2.0:
            hi_v.append((seed_str, res))
        elif res['v_over_c'] < 0.1 and res['n_stable'] >= 30:
            lo_v.append((seed_str, res))

    return hi_v, lo_v


def compute_paired_errors(hi_v, lo_v, max_hi=5, max_lo=3):
    """Compute paired SR errors for all hi×lo combinations."""
    if not hi_v or not lo_v:
        return []
    hi_set = hi_v[:max_hi]
    lo_set = lo_v[:max_lo]
    pairs = []
    for hi_seed, hi_res in hi_set:
        for lo_seed, lo_res in lo_set:
            if hi_res['ratio'] is None or lo_res['ratio'] is None:
                continue
            p = hi_res['ratio'] / lo_res['ratio']
            q = hi_res['gamma'] / lo_res['gamma']
            e = abs(p - q) / q * 100
            pairs.append({
                'hi_seed': hi_seed,
                'lo_seed': lo_seed,
                'paired_ratio': round(p, 6),
                'sr_prediction': round(q, 6),
                'error_pct': round(e, 2),
            })
    return pairs


# ── History window analysis ───────────────────────────────────────────────────

def analyze_history_windows(init_mode: str, n_warmup: int = 50,
                             n_sample_steps: int = 20) -> dict:
    """
    Run the canonical seed and collect ether vs glider history windows.

    Warms up n_warmup outer steps, then samples history windows
    from glider cells and ether cells for comparison.
    """
    seed_arr = np.array([int(b) for b in CANONICAL_SEED], dtype=np.uint8)
    tape = ether_base.copy()
    for j, bit in enumerate(seed_arr):
        tape[(_CENTER + j) % OUTER_L] = bit

    hist = make_history_ether14() if init_mode == 'ether14' else make_history_zero()
    s_tape = tape.copy()
    s_ref = ether_base.copy()

    ether_windows, glider_windows = [], []
    ether_taus_samples, glider_taus_samples = [], []
    flip_counts_ether, flip_counts_glider = [], []

    for step in range(n_warmup + n_sample_steps):
        s_tape_next = run_outer(s_tape)
        s_ref_next = run_outer(s_ref)

        if step >= n_warmup:
            diff = s_tape != s_ref
            diff_pos = np.where(diff)[0]
            if 2 <= len(diff_pos) <= 60:
                # Sample a few glider and ether windows
                for i in diff_pos[:3]:
                    glider_windows.append(hist[i].tolist())
                    flips = int(np.abs(np.diff(hist[i].astype(int))).sum())
                    flip_counts_glider.append(flips)
                    tau = float(batch_tau_c(hist, np.array([i]),
                                            np.array([s_tape_next[i]]))[0])
                    glider_taus_samples.append(tau)

                ndiff_pos = np.where(~diff)[0][::30]
                for i in ndiff_pos[:3]:
                    ether_windows.append(hist[i].tolist())
                    flips = int(np.abs(np.diff(hist[i].astype(int))).sum())
                    flip_counts_ether.append(flips)
                    tau = float(batch_tau_c(hist, np.array([i]),
                                            np.array([s_tape_next[i]]))[0])
                    ether_taus_samples.append(tau)

        hist[:, :-1] = hist[:, 1:]
        hist[:, -1] = s_tape
        s_tape = s_tape_next
        s_ref = s_ref_next

    return {
        'ether_windows': ether_windows[:6],
        'glider_windows': glider_windows[:6],
        'ether_mean_flips': float(np.mean(flip_counts_ether)) if flip_counts_ether else 0.0,
        'glider_mean_flips': float(np.mean(flip_counts_glider)) if flip_counts_glider else 0.0,
        'ether_mean_tau': float(np.mean(ether_taus_samples)) if ether_taus_samples else 0.0,
        'glider_mean_tau': float(np.mean(glider_taus_samples)) if glider_taus_samples else 0.0,
    }


# ── Background τ_c (canonical seed, full history run) ────────────────────────

def compute_bg_tau(init_mode: str, n_steps: int = 60) -> float:
    """Mean τ_c of pure ether tape (no glider injection) using history seeding."""
    hist = make_history_ether14() if init_mode == 'ether14' else make_history_zero()
    s = ether_base.copy()
    taus = []
    for step in range(n_steps):
        s_next = run_outer(s)
        if step >= 10:  # skip warm-up
            sample_idx = np.arange(0, OUTER_L, 20)
            tau_vals = batch_tau_c(hist, sample_idx, s_next[sample_idx])
            taus.append(float(tau_vals.mean()))
        hist[:, :-1] = hist[:, 1:]
        hist[:, -1] = s
        s = s_next
    return float(np.mean(taus)) if taus else 0.0


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 65)
    print("=== Rank 59-HIST: History-Window Inner CA Seeding ===")
    print(f"M={M}, OUTER_L={OUTER_L}, MAX_INNER={MAX_INNER}")
    print(f"γ target = {GAMMA_TARGET:.4f} (v/c = {V_CANONICAL/C_EFF:.4f})")
    print("=" * 65)

    # Rank 31-ACS baseline (ETHER14 re-seeding)
    BASELINE_RATIO = 1.553
    BASELINE_ERROR = 6.4

    results_out = {
        'rank': '59-HIST',
        'test': 'history_window_seeding_sr',
        'date': time.strftime('%Y-%m-%d'),
        'parameters': {
            'M': M, 'OUTER_L': OUTER_L, 'MAX_INNER': MAX_INNER,
            'n_steps': 100, 'min_stable': 30,
            'gamma_target': round(GAMMA_TARGET, 6),
            'v_canonical': V_CANONICAL,
        },
        'baseline': {
            'rank31_acs_ratio': BASELINE_RATIO,
            'rank31_acs_error_pct': BASELINE_ERROR,
        },
        'modes': {},
    }

    for mode in ['ether14', 'zero']:
        if time.time() - _t0 > WALL_LIMIT - 20:
            print(f"\nSkipping mode={mode} (time budget exhausted)")
            break

        label = 'ETHER14-initialized' if mode == 'ether14' else 'Zero-initialized'
        print(f"\n{'─'*55}")
        print(f"History-window seeding ({label}):")

        t_mode = time.time()

        # Background τ_c (pure ether)
        bg_tau = compute_bg_tau(mode)
        print(f"  Background τ_c (ether):  {bg_tau:.4f}")

        # Full 1024-seed search
        print("  Searching 1024 seeds (γ∈[1.3,2.0], n_steps=100, min_stable=30)...")
        hi_v, lo_v = run_full_search(init_mode=mode, n_steps=100, min_stable=30,
                                     ether_stride=20)
        print(f"  hi-v seeds (γ∈[1.3,2.0]): {len(hi_v)}")
        print(f"  lo-v reference seeds:      {len(lo_v)}")

        if hi_v:
            hi_v.sort(key=lambda x: -x[1]['v_over_c'])
            mean_hi_ratio = float(np.mean([r['ratio'] for _, r in hi_v
                                           if r['ratio'] is not None]))
            mean_hi_g_tau = float(np.mean([r['g_tau_mean'] for _, r in hi_v
                                           if r['g_tau_mean'] is not None]))
            mean_hi_e_tau = float(np.mean([r['e_tau_mean'] for _, r in hi_v
                                           if r['e_tau_mean'] is not None]))
            print(f"  τ_c ratio (hi-v, mean):  {mean_hi_ratio:.4f}  "
                  f"(γ target: {GAMMA_TARGET:.4f})")
            print(f"  Mean glider τ_c (hi-v):  {mean_hi_g_tau:.4f}")
            print(f"  Mean ether  τ_c (hi-v):  {mean_hi_e_tau:.4f}")
        else:
            mean_hi_ratio = None
            mean_hi_g_tau = None
            mean_hi_e_tau = None
            print("  No hi-v seeds found.")

        # Paired errors
        pairs = compute_paired_errors(hi_v, lo_v)
        if pairs:
            all_errs = [p['error_pct'] for p in pairs]
            mean_err = float(np.mean(all_errs))
            ok = sum(1 for e in all_errs if e < 15)
            print(f"\n  Paired SR error ({len(pairs)} pairs): mean={mean_err:.1f}%, "
                  f"{ok}/{len(pairs)} < 15%")
            sr_verdict = ("IMPROVED" if mean_err < BASELINE_ERROR
                          else "SAME" if abs(mean_err - BASELINE_ERROR) < 1.0
                          else "DEGRADED")
            print(f"  vs baseline (6.4%): {sr_verdict}")

            # Show top pairs
            pairs_sorted = sorted(pairs, key=lambda p: p['error_pct'])
            for p in pairs_sorted[:3]:
                print(f"    {p['hi_seed']} vs {p['lo_seed']}: "
                      f"paired={p['paired_ratio']:.4f}, "
                      f"pred={p['sr_prediction']:.4f}, "
                      f"err={p['error_pct']:.1f}%")
        else:
            mean_err = None
            sr_verdict = "INSUFFICIENT_DATA"
            ok = 0
            print("  No paired comparison possible (missing hi-v or lo-v seeds).")

        # History window analysis for canonical seed
        print(f"\n  Analyzing history windows (canonical seed {CANONICAL_SEED}):")
        analysis = analyze_history_windows(mode)
        print(f"  Ether mean flips in M={M} window:  {analysis['ether_mean_flips']:.2f}")
        print(f"  Glider mean flips in M={M} window: {analysis['glider_mean_flips']:.2f}")
        print(f"  Ether mean τ_c from history:  {analysis['ether_mean_tau']:.4f}")
        print(f"  Glider mean τ_c from history: {analysis['glider_mean_tau']:.4f}")
        ratio_analysis = (analysis['glider_mean_tau'] / analysis['ether_mean_tau']
                          if analysis['ether_mean_tau'] > 0 else None)
        if ratio_analysis:
            sr_err_analysis = abs(ratio_analysis - GAMMA_TARGET) / GAMMA_TARGET * 100
            print(f"  τ_c ratio (canonical seed analysis): {ratio_analysis:.4f}  "
                  f"(SR error: {sr_err_analysis:.1f}%)")
        else:
            sr_err_analysis = None

        if analysis['ether_windows']:
            print(f"  Ether window examples:  {analysis['ether_windows'][:3]}")
        if analysis['glider_windows']:
            print(f"  Glider window examples: {analysis['glider_windows'][:3]}")

        flip_increase = (analysis['glider_mean_flips'] > analysis['ether_mean_flips'])
        tau_increase = (analysis['glider_mean_tau'] > analysis['ether_mean_tau'])
        print(f"  Glider windows have MORE flips than ether: {'YES' if flip_increase else 'NO'}")
        print(f"  More flips → higher τ_c: {'YES' if tau_increase else 'NO'}")

        elapsed_mode = time.time() - t_mode
        print(f"\n  Mode elapsed: {elapsed_mode:.1f}s")

        results_out['modes'][mode] = {
            'label': label,
            'bg_tau_ether': round(bg_tau, 6),
            'n_hi_v_seeds': len(hi_v),
            'n_lo_v_seeds': len(lo_v),
            'mean_hi_v_ratio': round(mean_hi_ratio, 6) if mean_hi_ratio else None,
            'mean_hi_v_g_tau': round(mean_hi_g_tau, 6) if mean_hi_g_tau else None,
            'mean_hi_v_e_tau': round(mean_hi_e_tau, 6) if mean_hi_e_tau else None,
            'n_pairs': len(pairs),
            'mean_sr_error_pct': round(mean_err, 3) if mean_err is not None else None,
            'n_pairs_under_15pct': ok,
            'sr_verdict': sr_verdict,
            'history_analysis': {
                'ether_mean_flips': round(analysis['ether_mean_flips'], 4),
                'glider_mean_flips': round(analysis['glider_mean_flips'], 4),
                'ether_mean_tau': round(analysis['ether_mean_tau'], 6),
                'glider_mean_tau': round(analysis['glider_mean_tau'], 6),
                'tau_ratio_canonical': round(ratio_analysis, 6) if ratio_analysis else None,
                'sr_error_canonical_pct': round(sr_err_analysis, 3) if sr_err_analysis else None,
                'glider_windows_sample': analysis['glider_windows'][:3],
                'ether_windows_sample': analysis['ether_windows'][:3],
                'glider_has_more_flips': bool(flip_increase),
                'more_flips_gives_higher_tau': bool(tau_increase),
            },
            'pairs_top5': sorted(pairs, key=lambda p: p['error_pct'])[:5],
            'elapsed_s': round(elapsed_mode, 2),
        }

    # ── Overall verdict ──────────────────────────────────────────────────────
    print("\n" + "=" * 65)
    print("=== Summary ===")
    print(f"Standard ETHER14 re-seeding (Rank 31-ACS baseline): "
          f"ratio={BASELINE_RATIO}, error={BASELINE_ERROR}%")
    print()

    all_verdicts = []
    for mode in ['ether14', 'zero']:
        if mode not in results_out['modes']:
            continue
        m = results_out['modes'][mode]
        label = m['label']
        err = m['mean_sr_error_pct']
        verdict = m['sr_verdict']
        ratio = m['mean_hi_v_ratio']
        print(f"History-window seeding ({label}):")
        print(f"  Background τ_c (ether): {m['bg_tau_ether']:.4f}")
        print(f"  τ_c ratio (hi-v mean):  {ratio:.4f}" if ratio else "  τ_c ratio: N/A")
        print(f"  Mean SR error: {err:.1f}%" if err is not None else "  SR error: N/A")
        print(f"  Verdict vs baseline:    {verdict}")
        print()
        all_verdicts.append(verdict)

    # Key findings
    print("Key findings:")
    for mode in ['ether14', 'zero']:
        if mode not in results_out['modes']:
            continue
        ha = results_out['modes'][mode]['history_analysis']
        label = 'ETHER14-init' if mode == 'ether14' else 'Zero-init'
        flip_diff = ha['glider_mean_flips'] - ha['ether_mean_flips']
        tau_diff = ha['glider_mean_tau'] - ha['ether_mean_tau']
        print(f"  [{label}] Glider flip excess vs ether: {flip_diff:+.2f} in M={M} window")
        print(f"  [{label}] Glider τ_c excess vs ether:  {tau_diff:+.4f}")
        print(f"  Glider windows have more flips: {ha['glider_has_more_flips']}")
        print(f"  More flips → higher τ_c: {ha['more_flips_gives_higher_tau']}")
        print()

    overall = ("IMPROVED" if any(v == "IMPROVED" for v in all_verdicts)
               else "SAME" if any(v == "SAME" for v in all_verdicts)
               else "DEGRADED")
    print(f"Overall verdict: {overall} vs ETHER14 re-seeding baseline")
    print()
    print("Physical interpretation:")
    e14_mode = results_out['modes'].get('ether14', {})
    ha14 = e14_mode.get('history_analysis', {})
    if ha14.get('glider_has_more_flips'):
        print("  Glider cells DO accumulate more varied history windows (higher flip count).")
    else:
        print("  Glider cells do NOT accumulate notably more varied history windows.")
    if ha14.get('more_flips_gives_higher_tau'):
        print("  Richer history → harder inner CA transition (higher τ_c): confirmed.")
        print("  Consistent with MFRR §26: higher information density → higher τ_c.")
    else:
        print("  Richer history does NOT reliably produce higher τ_c.")
        print("  History content does not encode glider/ether discrimination "
              "in the majority-vote signal.")
    print("=" * 65)

    # ── Save JSON ─────────────────────────────────────────────────────────────
    results_out['total_elapsed_s'] = round(time.time() - _t0, 2)
    with open(RESULTS_FILE, 'w') as f:
        json.dump(results_out, f, indent=2)
    print(f"\nResults saved: {RESULTS_FILE}")

    # ── Figure ────────────────────────────────────────────────────────────────
    _make_figure(results_out)

    return results_out


def _make_figure(results_out: dict) -> None:
    """Summary figure: τ_c ratio vs mode, and history window flip distribution."""
    modes_present = [m for m in ['ether14', 'zero'] if m in results_out['modes']]
    if not modes_present:
        return

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    # Left: τ_c ratio comparison across modes
    ax = axes[0]
    labels = ['ETHER14\nre-seed\n(baseline)', 'History\nETHER14-init', 'History\nZero-init']
    ratios = [1.553]
    colors = ['steelblue']
    for mode in ['ether14', 'zero']:
        if mode in results_out['modes']:
            r = results_out['modes'][mode]['mean_hi_v_ratio']
            ratios.append(r if r is not None else 0.0)
            colors.append('darkorange' if mode == 'ether14' else 'forestgreen')

    x = np.arange(len(ratios))
    bars = ax.bar(x, ratios, color=colors, alpha=0.85, edgecolor='black', width=0.6)
    ax.axhline(GAMMA_TARGET, color='red', linestyle='--', linewidth=1.5,
               label=f'γ target = {GAMMA_TARGET:.3f}')
    ax.axhline(1.553, color='steelblue', linestyle=':', linewidth=1.0,
               label='Baseline ratio = 1.553')
    ax.set_xticks(x)
    ax.set_xticklabels(labels[:len(ratios)], fontsize=9)
    ax.set_ylabel('Mean τ_c ratio (glider / ether)')
    ax.set_title('τ_c Ratio Comparison\nHistory-window vs ETHER14 baseline')
    ax.legend(fontsize=8)
    ax.set_ylim(0, GAMMA_TARGET * 1.3)
    ax.grid(axis='y', alpha=0.3)
    for bar, r in zip(bars, ratios):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
                f'{r:.3f}', ha='center', va='bottom', fontsize=9)

    # Right: flip count distribution in history windows
    ax2 = axes[1]
    for mode, color, label_str in zip(
            ['ether14', 'zero'],
            ['darkorange', 'forestgreen'],
            ['ETHER14-init', 'Zero-init']):
        if mode not in results_out['modes']:
            continue
        ha = results_out['modes'][mode]['history_analysis']
        e_flips = ha['ether_mean_flips']
        g_flips = ha['glider_mean_flips']
        ether_clr = 'sandybrown' if mode == 'ether14' else 'lightgreen'
        glider_clr = color
        ax2.bar([f'Ether\n{label_str}', f'Glider\n{label_str}'],
                [e_flips, g_flips],
                color=[ether_clr, glider_clr],
                edgecolor='black', width=0.5,
                label=f'{label_str}: ether={e_flips:.2f}, glider={g_flips:.2f}')
    ax2.set_ylabel(f'Mean flips in M={M} history window')
    ax2.set_title('History Window Flip Complexity\nGlider vs Ether cells')
    ax2.legend(fontsize=8)
    ax2.grid(axis='y', alpha=0.3)

    fig.suptitle(
        f'Rank 59-HIST: History-Window Inner CA Seeding — Rule 110, L={OUTER_L}\n'
        f'γ={GAMMA_TARGET:.3f}, baseline ratio=1.553 (6.4% error)',
        fontsize=11
    )
    fig.tight_layout()
    outpath = 'rank59_hist_results.png'
    fig.savefig(outpath, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Figure saved: {outpath}")


if __name__ == '__main__':
    main()
    signal.alarm(0)
    print(f"\nTotal elapsed: {time.time() - _t0:.2f}s")
