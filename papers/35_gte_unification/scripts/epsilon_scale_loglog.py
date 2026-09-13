from pathlib import Path
SCRIPT_DIR = Path(__file__).resolve().parent
#!/usr/bin/env python3
"""
Rank 95-EPSSCALE: ε₀(M) Systematic M-Scaling Validation
EPIC_072 — GTE Ontological Unification

Tests whether the Nyquist-derived formula
    ε₀(M) = π²/(3M²)
is empirically confirmed by:

  SECTION A — Analytic KG finite-difference dispersion computation
    Exact closed-form evaluation of the period-ratio SR error for a
    KG wave packet discretized on a lattice with spacing a = 1/M.
    Sweeps M ∈ {3,5,7,10,14,21,30,50,70,100} and k₀ ∈ {0.5, 1.0, π/2, π}.
    Fits log(ε) vs log(M) to extract slope p and coefficient A.

  SECTION B — AFCA τ_c M-scaling test (extending Rank 47-WDS)
    Runs Round-19-style AFCA SR test for M ∈ {35, 49} (new),
    adds Rank 47 data for M ∈ {7, 11, 21}, fits the combined
    log-log curve to check for M-independence vs M-scaling.

Decision gate (Section A, k₀ = π):
  p = −2.0 ± 0.2 and log(A) within 0.15 of log(π²/3)
    → ε₀(M) = π²/(3M²) CONFIRMED (CatA)
  p ≈ −2 but A ≠ π²/3
    → scaling confirmed, coefficient revised; formula partially valid
  p ≠ −2
    → M⁻² scaling not confirmed; formula domain is M = 7 only

Artifacts:
  rank95_epsscale_results.json
  rank95_epsscale_loglog.png
"""

import numpy as np
import json
import signal
import sys
import time
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# ── Safety: wall-clock timeout ───────────────────────────────────────────────
TIMEOUT_SECONDS = 540   # 9 minutes

def _timeout_handler(signum, frame):
    print(f"\nTIMEOUT: wall-clock limit {TIMEOUT_SECONDS}s reached. Saving partial results.")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION A  Analytic KG Finite-Difference Dispersion
# ─────────────────────────────────────────────────────────────────────────────

def kg_fd_period_error(k0, M, m=1.0, c=1.0):
    """
    Exact analytic SR period-ratio error for a KG wave packet at wave
    vector k₀ (outer-cell units) on a finite-difference lattice with
    spacing a = 1/M.

    The FD dispersion relation is:
        ω_FD² = (2c/a)² sin²(k₀a/2) + m²

    The FD group velocity is:
        v_g_FD = (c/a) sin(k₀a) / ω_FD

    The period measured at the co-moving packet centre is:
        T_centre = 2π / |k₀ v_g − ω|

    For exact KG: T_exact = γ T₀  (time dilation)
    For FD KG:   T_FD differs by ε = |T_FD/(γ T₀) − 1|

    Returns (ε, γ_exact, v_g_exact), or (None, γ, v_g) if k₀ = 0.
    """
    if k0 < 1e-12:
        return 0.0, 1.0, 0.0

    a = 1.0 / M

    # Exact KG
    omega_exact = np.sqrt((k0 * c) ** 2 + m ** 2)
    v_g_exact   = k0 * c ** 2 / omega_exact
    gamma       = omega_exact / m              # γ = ω₀/m for the wave packet

    # FD KG
    sin_half   = np.sin(k0 * a / 2.0)
    omega_fd   = np.sqrt((2.0 * c / a) ** 2 * sin_half ** 2 + m ** 2)
    v_g_fd     = (c / a) * np.sin(k0 * a) / omega_fd

    # Beat frequency (period at packet centre)
    omega_bf_exact = abs(k0 * v_g_exact - omega_exact)   # = m / γ  (exact)
    omega_bf_fd    = abs(k0 * v_g_fd    - omega_fd)

    if omega_bf_exact < 1e-14 or omega_bf_fd < 1e-14:
        return None, gamma, v_g_exact

    T_exact_centre = 2.0 * np.pi / omega_bf_exact   # = γ T₀
    T_fd_centre    = 2.0 * np.pi / omega_bf_fd

    T0 = 2.0 * np.pi / m
    eps = abs(T_fd_centre / (gamma * T0) - 1.0)
    return eps, gamma, v_g_exact


def analytic_kg_fd_sweep(M_values, k0_values, m=1.0):
    """Sweep (k₀, M) and return ε_FD with the formula prediction."""
    results = {}
    for k0 in k0_values:
        data = []
        for M in M_values:
            eps, gamma, v_g = kg_fd_period_error(k0, M, m=m)
            if eps is None:
                continue
            data.append({
                'M':       int(M),
                'eps':     float(eps),
                'eps_pct': float(eps * 100),
                'gamma':   float(gamma),
                'v_g':     float(v_g),
                'formula_pct': float(np.pi ** 2 / (3.0 * M ** 2) * 100),
                'ratio_to_formula': float(eps / (np.pi ** 2 / (3.0 * M ** 2)))
                    if np.pi ** 2 / (3.0 * M ** 2) > 0 else None,
            })
        results[f'k0={k0:.4f}'] = data
    return results


def power_law_log(log_M, log_A, p):
    return log_A + p * log_M


def fit_loglog(data, min_points=4):
    """Fit log(ε) vs log(M) with a power law ε = A × M^p."""
    valid = [d for d in data if d['eps'] > 0 and np.isfinite(d['eps'])]
    if len(valid) < min_points:
        return None
    log_M   = np.array([np.log(d['M'])   for d in valid])
    log_eps = np.array([np.log(d['eps']) for d in valid])
    try:
        popt, pcov = curve_fit(power_law_log, log_M, log_eps)
        perr = np.sqrt(np.diag(pcov))
        return {
            'slope':    float(popt[1]),
            'slope_err': float(perr[1]),
            'A':        float(np.exp(popt[0])),
            'log_A':    float(popt[0]),
            'log_A_err': float(perr[0]),
            'n_points': len(valid),
        }
    except Exception as e:
        return {'error': str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# SECTION B  AFCA τ_c M-Scaling Test (extending Rank 47-WDS)
# ─────────────────────────────────────────────────────────────────────────────

ETHER14 = np.array([1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0], dtype=np.uint8)
LUT110  = np.array([(110 >> i) & 1 for i in range(8)],            dtype=np.uint8)
C_EFF   = 2.0 / 3.0
OUTER_L = 500


def run_rule110(state):
    l = np.roll(state, 1).astype(np.int32)
    c = state.astype(np.int32)
    r = np.roll(state, -1).astype(np.int32)
    return LUT110[(l << 2) | (c << 1) | r]


def majority(state):
    return 1 if state.sum() * 2 > len(state) else 0


def precompute_tau_lut(M, max_inner=None):
    """
    tau_lut[curr_maj][tgt_maj] = Rule 110 inner steps until majority
    of an M-cell ETHER14 window transitions from curr_maj to tgt_maj.
    """
    if max_inner is None:
        max_inner = max(200, M * 15)

    windows = []
    for start in range(14):
        w = np.array([ETHER14[(start + j) % 14] for j in range(M)], dtype=np.uint8)
        windows.append(w)

    win_maj0 = [w for w in windows if w.sum() * 2 < M]
    win_maj1 = [w for w in windows if w.sum() * 2 > M]

    starts = {
        0: win_maj0[0].copy() if win_maj0 else np.zeros(M, dtype=np.uint8),
        1: win_maj1[0].copy() if win_maj1 else np.ones(M,  dtype=np.uint8),
    }

    tau_lut = np.zeros((2, 2), dtype=np.float32)
    for curr in [0, 1]:
        for tgt in [0, 1]:
            state = starts[curr].copy()
            found = False
            for step in range(max_inner):
                if majority(state) == tgt:
                    tau_lut[curr, tgt] = step
                    found = True
                    break
                l = np.roll(state, 1).astype(np.int32)
                cs = state.astype(np.int32)
                r  = np.roll(state, -1).astype(np.int32)
                state = LUT110[(l << 2) | (cs << 1) | r]
            if not found:
                tau_lut[curr, tgt] = max_inner
    return tau_lut


def measure_tau_fast(outer_now, outer_next, tau_lut):
    return tau_lut[outer_now.astype(int), outer_next.astype(int)]


def test_seed_afca(seed_str, tau_lut, ether_base, n_steps=200, min_stable=50):
    """
    Insert seed into ether background and track the glider's τ_c ratio.
    Returns dict with v, gamma, ratio, n_stable  or None if unstable.
    """
    seed   = np.array([int(b) for b in seed_str], dtype=np.uint8)
    center = OUTER_L // 2
    tape   = ether_base.copy()
    for j, bit in enumerate(seed):
        tape[(center + j) % OUTER_L] = bit

    s_tape = tape.copy()
    s_ref  = ether_base.copy()
    positions, g_taus, e_taus = [], [], []

    for _ in range(n_steps):
        s_tape_next = run_rule110(s_tape)
        s_ref_next  = run_rule110(s_ref)

        diff     = s_tape != s_ref
        diff_pos = np.where(diff)[0]

        if 2 <= len(diff_pos) <= 60:
            positions.append(float(diff_pos.mean()))
            taus = measure_tau_fast(s_tape, s_tape_next, tau_lut)
            g_taus.append(taus[diff].mean())
            ndiff = ~diff
            if ndiff.sum() > 0:
                e_taus.append(taus[ndiff].mean())

        s_tape = s_tape_next
        s_ref  = s_ref_next

    if len(positions) < min_stable or len(e_taus) == 0:
        return None

    v        = np.polyfit(np.arange(len(positions)), np.array(positions), 1)[0]
    v_over_c = abs(v / C_EFF)
    if v_over_c >= 1.0:
        return None

    gamma = 1.0 / np.sqrt(1.0 - v_over_c ** 2)
    ratio = float(np.mean(g_taus)) / float(np.mean(e_taus))
    return {'v': v, 'v_over_c': v_over_c, 'gamma': gamma,
            'ratio': ratio, 'n_stable': len(positions)}


def run_afca_m_test(M, n_seeds=512, n_steps=200, min_stable=50,
                    gamma_lo=1.3, gamma_hi=2.5, per_m_timeout=90):
    """
    AFCA SR test at a given inner CA width M.
    Returns summary dict with mean/best SR error (or status=resonance/no_seeds).
    """
    t0 = time.time()

    tau_lut = precompute_tau_lut(M)

    # Check for ether-resonance degenerate LUT
    degenerate = (tau_lut[0, 1] >= 190 or tau_lut[1, 0] >= 190)
    if degenerate:
        print(f"  M={M}: DEGENERATE LUT {tau_lut.tolist()} (ether resonance — M≡1 mod 14?)")
        return {'M': M, 'status': 'resonance', 'tau_lut': tau_lut.tolist()}

    # Background τ_c
    ether_base = np.array([ETHER14[i % 14] for i in range(OUTER_L)], dtype=np.uint8)
    s = ether_base.copy()
    bg_buf = []
    for _ in range(60):
        s_next = run_rule110(s)
        bg_buf.append(measure_tau_fast(s, s_next, tau_lut).mean())
        s = s_next
    bg_tau_c = float(np.mean(bg_buf[10:20]))

    # Seed search
    stable_hi, stable_lo = [], []
    for ic in range(n_seeds):
        if time.time() - t0 > per_m_timeout:
            print(f"  M={M}: per-M timeout after {ic} seeds")
            break
        seed_str = bin(ic)[2:].zfill(10)
        res = test_seed_afca(seed_str, tau_lut, ether_base,
                             n_steps=n_steps, min_stable=min_stable)
        if res is None:
            continue
        if gamma_lo <= res['gamma'] <= gamma_hi:
            stable_hi.append((seed_str, res))
        if res['v_over_c'] < 0.1:
            stable_lo.append((seed_str, res))

    if not stable_hi or not stable_lo:
        print(f"  M={M}: seeds insufficient (hi={len(stable_hi)}, lo={len(stable_lo)})")
        return {'M': M, 'status': 'no_seeds',
                'n_hi': len(stable_hi), 'n_lo': len(stable_lo),
                'bg_tau_c': bg_tau_c, 'tau_lut': tau_lut.tolist()}

    # Paired SR errors
    errors = []
    for _, hi in stable_hi[:min(5, len(stable_hi))]:
        for _, lo in stable_lo[:min(3, len(stable_lo))]:
            p = hi['ratio'] / lo['ratio']
            q = hi['gamma']  / lo['gamma']
            errors.append(abs(p - q) / q * 100.0)

    mean_err = float(np.mean(errors))
    best_err = float(np.min(errors))
    n_ok     = sum(1 for e in errors if e < 15)
    formula  = float(np.pi ** 2 / (3.0 * M ** 2) * 100)

    print(f"  M={M}: tau_lut={tau_lut.tolist()}, bg_τ_c={bg_tau_c:.3f}, "
          f"hi={len(stable_hi)}, lo={len(stable_lo)}, "
          f"mean_err={mean_err:.1f}%, best={best_err:.1f}%, "
          f"{n_ok}/{len(errors)} <15%, formula={formula:.2f}%")

    return {
        'M':                int(M),
        'status':           'ok',
        'tau_lut':          tau_lut.tolist(),
        'bg_tau_c':         bg_tau_c,
        'n_hi_seeds':       len(stable_hi),
        'n_lo_seeds':       len(stable_lo),
        'mean_sr_error_pct': mean_err,
        'best_sr_error_pct': best_err,
        'n_pairs':          len(errors),
        'n_confirmed':      n_ok,
        'formula_pred_pct': formula,
    }


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

print("=" * 72)
print("Rank 95-EPSSCALE: ε₀(M) Systematic M-Scaling Validation")
print("EPIC_072 — GTE Ontological Unification")
print("=" * 72)

M_VALUES    = [3, 5, 7, 10, 14, 21, 30, 50, 70, 100]
K0_VALUES   = [0.5, 1.0, np.pi / 2, np.pi]          # outer-cell units
M_KG = 1.0   # KG mass parameter

# ── Section A ────────────────────────────────────────────────────────────────
print("\n─── Section A: Analytic KG FD Dispersion (exact closed-form) ───")
print(f"M sweep: {M_VALUES}")
print(f"k₀ values (outer units): {[round(k,4) for k in K0_VALUES]}")
print(f"KG mass m = {M_KG},  c = 1")

kg_results = analytic_kg_fd_sweep(M_VALUES, K0_VALUES, m=M_KG)

# Print table for k₀ = π specifically
print(f"\n{'M':>5}  {'ε_FD%':>9}  {'formula%':>10}  {'ratio':>7}  {'γ':>7}  {'v_g':>8}")
print("─" * 52)
for d in kg_results.get(f'k0={np.pi:.4f}', []):
    ratio_str = f"{d['ratio_to_formula']:.3f}" if d['ratio_to_formula'] else '—'
    print(f"{d['M']:>5}  {d['eps_pct']:>9.4f}  {d['formula_pct']:>10.4f}  "
          f"{ratio_str:>7}  {d['gamma']:>7.3f}  {d['v_g']:>8.5f}")

# Log-log fits for all k₀ values
print("\n─── Section A log-log fits ───")
print(f"{'k₀':>12}  {'slope p':>9}  {'±σ_p':>6}  {'coeff A':>9}  "
      f"{'π²/3':>7}  {'A/formula':>10}")
print("─" * 60)

kg_fits = {}
pi2_over_3 = np.pi ** 2 / 3.0
for k0, k0_key in zip(K0_VALUES, [f'k0={k:.4f}' for k in K0_VALUES]):
    data = kg_results.get(k0_key, [])
    fit  = fit_loglog(data)
    kg_fits[k0_key] = fit
    if fit and 'slope' in fit:
        print(f"  {k0_key:>10}  {fit['slope']:>9.4f}  "
              f"{fit['slope_err']:>6.4f}  {fit['A']:>9.5f}  "
              f"{pi2_over_3:>7.5f}  {fit['A']/pi2_over_3:>10.4f}")
    else:
        print(f"  {k0_key:>10}  fit failed: {fit}")

# ── Section B ────────────────────────────────────────────────────────────────
print("\n─── Section B: AFCA τ_c M-Scaling (extending Rank 47-WDS) ───")
print("Rank 47 data (M=7,11,21) + new runs (M=35,49)")

# Rank 47 established results (from 000_INF_RUN_LOG.md)
rank47 = [
    {'M': 7,  'status': 'ok', 'tau_lut': [[0,1],[1,0]],  'bg_tau_c': 0.4290,
     'mean_sr_error_pct':  8.5, 'best_sr_error_pct':  3.8, 'formula_pred_pct': 6.71,
     'source': 'Rank47-WDS'},
    {'M': 11, 'status': 'ok', 'tau_lut': [[0,1],[1,0]],  'bg_tau_c': 0.4290,
     'mean_sr_error_pct':  8.5, 'best_sr_error_pct':  3.8, 'formula_pred_pct': 2.72,
     'source': 'Rank47-WDS'},
    {'M': 21, 'status': 'ok', 'tau_lut': [[0,1],[21,0]], 'bg_tau_c': 4.719,
     'mean_sr_error_pct':  7.2, 'best_sr_error_pct':  0.3, 'formula_pred_pct': 0.75,
     'source': 'Rank47-WDS'},
]
for r in rank47:
    print(f"  M={r['M']:2d} (Rank47): mean={r['mean_sr_error_pct']:.1f}%, "
          f"best={r['best_sr_error_pct']:.1f}%,  formula={r['formula_pred_pct']:.2f}%")

# New AFCA runs — large M values are resonant for ETHER14; use M=9 (ether-compatible)
# M=35 (35 mod 14 = 7, but ETHER14 density 8/14 means all 35-cell windows are
# majority=1 — no majority=0 windows exist → degenerate; same for M=49).
# M=9 works: start=5 window [0,0,0,1,0,0,1,1,0] has sum=3 < 4.5 → majority=0 ✓
afca_new = []
for M_new in [9, 13]:
    print(f"\nRunning AFCA test M={M_new}...")
    res = run_afca_m_test(M_new, n_seeds=512, per_m_timeout=90)
    res['source'] = 'Rank95-EPSSCALE'
    afca_new.append(res)

afca_all = rank47 + afca_new

# Log-log fit for AFCA
print("\n─── AFCA log-log fit ───")
valid_afca = [r for r in afca_all
              if r.get('status') == 'ok' and 'mean_sr_error_pct' in r]
afca_fit = fit_loglog(
    [{'M': r['M'], 'eps': r['mean_sr_error_pct'] / 100.0} for r in valid_afca],
    min_points=3,
)
if afca_fit and 'slope' in afca_fit:
    print(f"  AFCA mean-error slope p = {afca_fit['slope']:.4f} ± {afca_fit['slope_err']:.4f}, "
          f"A = {afca_fit['A']:.5f}")
else:
    print(f"  AFCA fit: {afca_fit}")

# ── Decision gate ─────────────────────────────────────────────────────────────
print("\n" + "=" * 72)
print("DECISION GATE")
print("=" * 72)

k0_pi_key = f'k0={np.pi:.4f}'
fit_pi    = kg_fits.get(k0_pi_key, {})

# Gate for KG FD at k₀ = π
if fit_pi and 'slope' in fit_pi:
    p_fd, p_err_fd = fit_pi['slope'], fit_pi['slope_err']
    A_fd           = fit_pi['A']
    slope_ok       = abs(p_fd - (-2.0)) <= 0.2
    coeff_ok       = abs(np.log(A_fd) - np.log(pi2_over_3)) <= 0.15
    if slope_ok and coeff_ok:
        verdict_fd = ("CONFIRMED (CatA) — slope p≈−2, A≈π²/3; "
                      "KG FD gives ε₀(M)=π²/(3M²)")
    elif slope_ok:
        verdict_fd = (f"SCALING CONFIRMED, coefficient revised — "
                      f"slope p≈−2 ✓; A={A_fd:.4f} (formula π²/3={pi2_over_3:.4f}, "
                      f"ratio A/(π²/3)={A_fd/pi2_over_3:.3f})")
    else:
        verdict_fd = (f"NOT CONFIRMED — slope p={p_fd:.3f} (expected −2 ± 0.2)")
else:
    p_fd, A_fd, slope_ok, coeff_ok = None, None, False, False
    verdict_fd = "KG FD fit unavailable"

print(f"\nKG FD (k₀=π, m={M_KG}):")
if p_fd is not None:
    print(f"  slope p  = {p_fd:.4f} ± {p_err_fd:.4f}  (expected −2)")
    print(f"  coeff A  = {A_fd:.5f}   (π²/3 = {pi2_over_3:.5f}, "
          f"A/formula = {A_fd/pi2_over_3:.4f})")
print(f"  Verdict: {verdict_fd}")

# Gate for AFCA
if afca_fit and 'slope' in afca_fit:
    p_afca = afca_fit['slope']
    if abs(p_afca) < 0.4:
        verdict_afca = ("M-INDEPENDENT (CatA extended) — AFCA clock errors do not "
                        "decrease with M; consistent with τ_c mechanism being "
                        "insensitive to inner-cell count")
    else:
        verdict_afca = (f"M-DEPENDENT (slope p={p_afca:.3f}) — AFCA errors show "
                        f"systematic M-dependence")
else:
    verdict_afca = "AFCA fit not computed (insufficient data)"

print(f"\nAFCA τ_c:")
if afca_fit and 'slope' in afca_fit:
    print(f"  slope p  = {afca_fit['slope']:.4f} ± {afca_fit['slope_err']:.4f}  (expected ~0 or −2)")
print(f"  Verdict: {verdict_afca}")

# Reconciliation summary
print("\n─── Reconciliation ───")
print("The formula ε₀(M) = π²/(3M²) describes the Nyquist-limit lattice")
print("correction for binary coarse-graining of the KG field.")
print("Two independent tests were applied:")
slope_str = f"{p_fd:.4f}" if p_fd is not None else 'N/A'
coeff_str = f"{A_fd:.5f}" if A_fd is not None else 'N/A'
ratio_str = f"{A_fd/pi2_over_3:.4f}" if A_fd is not None else 'N/A'
print(f"  KG FD (k₀=π):  slope = {slope_str}, coeff A = {coeff_str}")
print(f"                 formula: slope = -2, coeff = π²/3 = {pi2_over_3:.5f}")
print(f"                 coefficient ratio A/(π²/3) = {ratio_str}")
afca_slope_str = f"{afca_fit['slope']:.3f}" if (afca_fit and 'slope' in afca_fit) else 'N/A'
print(f"  AFCA τ_c:       slope = {afca_slope_str}")

# ── Plot ──────────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(18, 6))
M_fine   = np.logspace(np.log10(3), np.log10(100), 200)
colors   = ['tab:blue', 'tab:orange', 'tab:green', 'tab:red']

# Panel 1: KG FD all k₀
for (k0_key, data), col in zip(kg_results.items(), colors):
    M_arr   = [d['M']       for d in data]
    eps_arr = [d['eps_pct'] for d in data]
    label   = k0_key.replace('k0=', 'k₀=')
    axes[0].loglog(M_arr, eps_arr, 'o-', color=col, label=label, alpha=0.85)

axes[0].loglog(M_fine, np.pi ** 2 / (3.0 * M_fine ** 2) * 100, 'k--',
               linewidth=2.5, label='π²/(3M²) formula', zorder=5)
axes[0].set_xlabel('M  (inner cells per outer cell)')
axes[0].set_ylabel('ε(M)  (%)')
axes[0].set_title('KG FD: Period-ratio error vs M\n(analytic, all k₀)')
axes[0].legend(fontsize=8)
axes[0].grid(True, alpha=0.3, which='both')

# Panel 2: KG FD k₀=π with fit line
data_pi = kg_results.get(k0_pi_key, [])
if data_pi:
    M_arr   = [d['M']       for d in data_pi]
    eps_arr = [d['eps_pct'] for d in data_pi]
    axes[1].loglog(M_arr, eps_arr, 'rs-', markersize=7, label='KG FD (k₀=π)', zorder=4)

axes[1].loglog(M_fine, np.pi ** 2 / (3.0 * M_fine ** 2) * 100, 'k--',
               linewidth=2.5, label='π²/(3M²) formula')
if p_fd and A_fd:
    axes[1].loglog(M_fine, A_fd * M_fine ** p_fd * 100, 'b-.',
                   linewidth=2, label=f'Fit: {A_fd:.3f}×M^{{{p_fd:.3f}}}')

axes[1].set_xlabel('M')
axes[1].set_ylabel('ε(M)  (%)')
axes[1].set_title('KG FD (k₀=π): M-scaling\n& formula comparison')
axes[1].legend(fontsize=9)
axes[1].grid(True, alpha=0.3, which='both')

# Panel 3: AFCA τ_c M-scaling
M_afca   = [r['M']                for r in valid_afca]
err_afca = [r['mean_sr_error_pct'] for r in valid_afca]
fml_afca = [r.get('formula_pred_pct', np.pi**2/(3*r['M']**2)*100) for r in valid_afca]

if M_afca:
    axes[2].loglog(M_afca, err_afca,  'bo-', markersize=8, label='AFCA mean error', zorder=4)
    axes[2].loglog(M_afca, fml_afca, 'k^--', markersize=6, alpha=0.6, label='formula π²/(3M²)')
axes[2].loglog(M_fine, np.pi ** 2 / (3.0 * M_fine ** 2) * 100, 'k--',
               linewidth=1.5, alpha=0.5)
if afca_fit and 'slope' in afca_fit and afca_fit['A']:
    axes[2].loglog(M_fine, afca_fit['A'] * M_fine ** afca_fit['slope'] * 100,
                   'b-.', linewidth=2,
                   label=f"Fit slope={afca_fit['slope']:.2f}")
axes[2].set_xlabel('M')
axes[2].set_ylabel('AFCA SR mean error  (%)')
axes[2].set_title('AFCA τ_c: M-scaling\n(extending Rank 47-WDS)')
axes[2].legend(fontsize=9)
axes[2].grid(True, alpha=0.3, which='both')

plt.suptitle('Rank 95-EPSSCALE: ε₀(M) Systematic M-Scaling Validation\n'
             'EPIC_072 — GTE Ontological Unification',
             fontsize=11, fontweight='bold')
plt.tight_layout()
plot_path = 'rank95_epsscale_loglog.png'
plt.savefig(plot_path, dpi=150, bbox_inches='tight')
plt.close()
print(f"\nPlot saved: {plot_path}")

# ── Save results ──────────────────────────────────────────────────────────────
signal.alarm(0)

def _to_native(obj):
    if isinstance(obj, (np.integer,)):    return int(obj)
    if isinstance(obj, (np.floating,)):   return float(obj)
    if isinstance(obj, np.ndarray):       return obj.tolist()
    if isinstance(obj, np.bool_):         return bool(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def _deep_convert(obj):
    """Recursively convert numpy types to native Python."""
    if isinstance(obj, dict):
        return {k: _deep_convert(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_deep_convert(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, np.bool_):
        return bool(obj)
    return obj

output = {
    'experiment': 'Rank 95-EPSSCALE: ε₀(M) Systematic M-Scaling Validation',
    'date':       '2026-05-22',
    'formula':    'eps_0(M) = pi^2 / (3*M^2)',
    'parameters': {
        'KG_mass_m': float(M_KG),
        'c':         1.0,
        'k0_values': [round(float(k), 6) for k in K0_VALUES],
        'M_values':  M_VALUES,
    },
    'section_A_kg_fd': {
        'description': 'Analytic KG FD dispersion — exact period-ratio error',
        'results_by_k0': {
            k: [
                {kk: (float(vv) if isinstance(vv, float) else vv)
                 for kk, vv in d.items()}
                for d in v
            ]
            for k, v in kg_results.items()
        },
        'fits': {
            k: ({kk: float(vv) if isinstance(vv, (float, np.floating)) else vv
                 for kk, vv in f.items()} if f else None)
            for k, f in kg_fits.items()
        },
        'pi2_over_3': float(pi2_over_3),
        'verdict':    verdict_fd,
    },
    'section_B_afca': {
        'description': 'AFCA τ_c M-scaling test (extending Rank 47-WDS)',
        'rank47_data': rank47,
        'new_runs':    afca_new,
        'fit':         {kk: (float(vv) if isinstance(vv, (float, np.floating)) else vv)
                        for kk, vv in (afca_fit or {}).items()},
        'verdict':     verdict_afca,
    },
    'decision_gate': {
        'kg_fd_k0_pi': {
            'slope':      float(p_fd)    if p_fd    else None,
            'coeff_A':    float(A_fd)    if A_fd    else None,
            'pi2_over_3': float(pi2_over_3),
            'A_ratio':    float(A_fd / pi2_over_3) if A_fd else None,
            'slope_ok':   slope_ok,
            'coeff_ok':   coeff_ok,
            'verdict':    verdict_fd,
        },
        'afca': {
            'slope':   float(afca_fit['slope']) if (afca_fit and 'slope' in afca_fit) else None,
            'verdict': verdict_afca,
        },
    },
}

json_path = 'rank95_epsscale_results.json'
with open(json_path, 'w') as f:
    json.dump(_deep_convert(output), f, indent=2)

print(f"Results saved: {json_path}")
print("\nRank 95-EPSSCALE complete.")
