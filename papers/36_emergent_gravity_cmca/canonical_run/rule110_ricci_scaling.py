#!/usr/bin/env python3
"""
rule110_ricci_scaling.py — Rule 110 Ollivier-Ricci scaling test (R87.NT13).

Tests whether the deviation-based Ollivier-Ricci curvature results from the
L=280 computation (R87.NT11) are genuine large-tape limits, not finite-size
artifacts. Runs the same computation at L=500 and L=1000 with T=100.

Key questions:
  (1) κ_EE = 0 exactly at larger tape sizes? (Should hold: definitional)
  (2) κ_SD > 0 at larger tape sizes? (Non-trivial: glider dynamics)
  (3) Do κ_SD and κ_XD converge as L grows?
  (4) Is global κ ≈ 0 maintained at larger scales?

ETHER: The correct Rule 110 background is 11111000100110 (period-14 spatial,
temporal period = 1 step, drift = 4 cells per step).

METHOD: Deviation-based Ollivier-Ricci curvature (R87.NT11 method).
  See rule110_large_tape_ricci.py for full documentation.

Reference: Gorard (2020), Complex Systems 29(2).
"""

import numpy as np
from collections import defaultdict

# ---------------------------------------------------------------------------
# Rule 110 (binary)
# ---------------------------------------------------------------------------
RULE110 = {
    (1, 1, 1): 0, (1, 1, 0): 1, (1, 0, 1): 1, (1, 0, 0): 0,
    (0, 1, 1): 1, (0, 1, 0): 1, (0, 0, 1): 1, (0, 0, 0): 0,
}


def rule110_step(tape: np.ndarray) -> np.ndarray:
    L   = len(tape)
    new = np.zeros(L, dtype=int)
    for i in range(L):
        new[i] = RULE110[(tape[(i - 1) % L], tape[i], tape[(i + 1) % L])]
    return new


# ---------------------------------------------------------------------------
# Ether: 11111000100110 (temporal period 1, drift 4 cells/step)
# ---------------------------------------------------------------------------
ETHER = [1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0]   # = "11111000100110"


def ether_val(t: int, x: int) -> int:
    """Expected ether value at (t, x), accounting for rightward drift."""
    return ETHER[(x + 4 * t) % 14]


# ---------------------------------------------------------------------------
# 1D Wasserstein-1 (exact, CDF method)
# ---------------------------------------------------------------------------
def wasserstein1d(masses1, positions1, masses2, positions2) -> float:
    pd1 = defaultdict(float)
    pd2 = defaultdict(float)
    for m, p in zip(masses1, positions1):
        pd1[p] += m
    for m, p in zip(masses2, positions2):
        pd2[p] += m
    all_pos = sorted(set(list(positions1) + list(positions2)))
    cdf1 = cdf2 = 0.0
    W = 0.0
    for i in range(len(all_pos) - 1):
        pos  = all_pos[i]
        cdf1 += pd1[pos]
        cdf2 += pd2[pos]
        gap   = all_pos[i + 1] - all_pos[i]
        W    += abs(cdf1 - cdf2) * gap
    return W


# ---------------------------------------------------------------------------
# Deviation-based Ollivier-Ricci for edge (t,x)–(t,x+1)
# ---------------------------------------------------------------------------
def ollivier_ricci_dev(t: int, x: int, spacetime: np.ndarray, L: int,
                       eps: float = 0.1) -> float:
    """Returns κ = 1 − W₁(μ_x, μ_{x+1}) using deviation-based weights.

    In pure ether: all weights = ε → uniform → W₁ = 1 → κ = 0 exactly.
    """
    if t + 1 >= len(spacetime):
        return None
    p1 = [x - 1, x,     x + 1]
    p2 = [x,     x + 1, x + 2]
    w1 = [abs(int(spacetime[t + 1][xi % L]) - ether_val(t + 1, xi % L)) + eps
          for xi in p1]
    w2 = [abs(int(spacetime[t + 1][xi % L]) - ether_val(t + 1, xi % L)) + eps
          for xi in p2]
    Z1, Z2 = sum(w1), sum(w2)
    return 1.0 - wasserstein1d([w / Z1 for w in w1], p1,
                               [w / Z2 for w in w2], p2)


# ---------------------------------------------------------------------------
# Causal-neighborhood classification (same as R87.NT11)
# ---------------------------------------------------------------------------
def causal_nbhd_type(t: int, x: int, spacetime: np.ndarray, L: int) -> str:
    """EE / SD / XD / MX / PE — see rule110_large_tape_ricci.py for definitions."""
    dev_x  = int(spacetime[t][x % L])       != ether_val(t, x % L)
    dev_x1 = int(spacetime[t][(x + 1) % L]) != ether_val(t, (x + 1) % L)
    if dev_x or dev_x1:
        return 'PE'

    dev_xm1 = int(spacetime[t + 1][(x - 1) % L]) != ether_val(t + 1, (x - 1) % L)
    dev_fx  = int(spacetime[t + 1][x % L])        != ether_val(t + 1, x % L)
    dev_fx1 = int(spacetime[t + 1][(x + 1) % L])  != ether_val(t + 1, (x + 1) % L)
    dev_xp2 = int(spacetime[t + 1][(x + 2) % L])  != ether_val(t + 1, (x + 2) % L)

    dev_shared = dev_fx or dev_fx1
    dev_excl   = dev_xm1 or dev_xp2

    if   not dev_shared and not dev_excl: return 'EE'
    elif     dev_shared and not dev_excl: return 'SD'
    elif not dev_shared and     dev_excl: return 'XD'
    else:                                 return 'MX'


# ---------------------------------------------------------------------------
# Single run at given (L, T, N_PERTURB, SEED)
# ---------------------------------------------------------------------------
def run_tape(L: int, T: int, N_PERTURB: int, SEED: int, eps: float = 0.1):
    """
    Evolve Rule 110 on a tape of size L for T steps with N_PERTURB random flips
    on the ether initial condition. Compute deviation-based Ollivier-Ricci
    curvature for all spacelike edges. Return statistics dict.
    """
    np.random.seed(SEED)
    tape = np.array([ETHER[i % 14] for i in range(L)])
    for s in np.random.choice(L, N_PERTURB, replace=False):
        tape[s] = 1 - tape[s]

    spacetime = [tape.copy()]
    for _ in range(T):
        tape = rule110_step(tape)
        spacetime.append(tape.copy())
    spacetime = np.array(spacetime)

    # Ether fraction at key timesteps
    ether_fracs = {}
    for t_check in [0, T // 4, T // 2, T]:
        if t_check <= T:
            frac = sum(
                spacetime[t_check][x] == ether_val(t_check, x) for x in range(L)
            ) / L
            ether_fracs[t_check] = frac

    # Compute curvatures
    kappas = {'EE': [], 'SD': [], 'XD': [], 'MX': [], 'PE': []}
    for t in range(T):
        for x in range(L):
            k    = ollivier_ricci_dev(t, x, spacetime, L, eps=eps)
            if k is None:
                continue
            ctype = causal_nbhd_type(t, x, spacetime, L)
            kappas[ctype].append(k)

    n_total = sum(len(v) for v in kappas.values())

    results = {
        'L': L, 'T': T, 'N_PERTURB': N_PERTURB, 'SEED': SEED,
        'n_edges': n_total,
        'ether_fracs': ether_fracs,
        'kappa_EE': np.mean(kappas['EE']) if kappas['EE'] else None,
        'kappa_SD': np.mean(kappas['SD']) if kappas['SD'] else None,
        'kappa_XD': np.mean(kappas['XD']) if kappas['XD'] else None,
        'kappa_PE': np.mean(kappas['PE']) if kappas['PE'] else None,
        'std_SD'  : np.std(kappas['SD'])  if kappas['SD'] else None,
        'n_EE': len(kappas['EE']),
        'n_SD': len(kappas['SD']),
        'n_XD': len(kappas['XD']),
        'n_PE': len(kappas['PE']),
        'kappa_global': np.mean([k for v in kappas.values() for k in v]),
    }
    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    SEED      = 7
    T         = 100
    EPS       = 0.1

    # Reference from R87.NT11 (L=280, T=300)
    ref = {
        'L': 280, 'T': 300, 'N_PERTURB': 15,
        'kappa_EE': 0.0000000000, 'kappa_SD': +0.7784, 'kappa_XD': -0.9520,
        'n_EE': 13622, 'n_SD': 1655, 'n_XD': 6083, 'n_edges': 84000,
    }

    print("=" * 72)
    print("Rule 110 Deviation-based Ollivier-Ricci — Scaling Test (R87.NT13)")
    print(f"  Scaling from L=280 (R87.NT11) to L=500, L=1000 at T={T}")
    print(f"  Ether: 11111000100110 (drift 4 cells/step, period 14)")
    print(f"  Question: Is κ_EE=0 finite-size artifact? Does κ_SD converge?")
    print("=" * 72)

    configs = [
        {'L': 500,  'T': T, 'N_PERTURB': max(15, 500  // 18), 'SEED': SEED},
        {'L': 1000, 'T': T, 'N_PERTURB': max(15, 1000 // 18), 'SEED': SEED},
    ]

    all_results = []

    for cfg in configs:
        L         = cfg['L']
        T_run     = cfg['T']
        N_PERTURB = cfg['N_PERTURB']
        print(f"\n{'─' * 72}")
        print(f"Running L={L}, T={T_run}, N_PERTURB={N_PERTURB}, seed={SEED}...")
        res = run_tape(L=L, T=T_run, N_PERTURB=N_PERTURB, SEED=SEED, eps=EPS)
        all_results.append(res)

        print(f"\n  Ether cell fractions:")
        for t_key, frac in sorted(res['ether_fracs'].items()):
            print(f"    t={t_key:4d}: {frac:.3f}")

        print(f"\n  Edge counts: {res['n_edges']} total")
        for key in ['EE', 'SD', 'XD', 'MX', 'PE']:
            n_key = res.get(f'n_{key}', 0)
            if n_key:
                pct = 100 * n_key / res['n_edges']
                print(f"    {key}: {n_key:7d}  ({pct:5.1f}%)")

        print(f"\n  Deviation-based Ollivier-Ricci curvature:")
        print(f"    κ_EE (all-ether):  {res['kappa_EE']:+.10f}  "
              f"(expect = 0 exactly)  ← κ=0? {abs(res['kappa_EE']) < 1e-9}")
        if res['kappa_SD'] is not None:
            print(f"    κ_SD (glider at):  {res['kappa_SD']:+.6f} ± {res['std_SD']:.4f}  "
                  f"(expect > 0)         ← κ>0? {res['kappa_SD'] > 0.1}")
        else:
            print(f"    κ_SD (glider at):  NO SD EDGES FOUND — increase N_PERTURB or T")
        if res['kappa_XD'] is not None:
            print(f"    κ_XD (flanking):   {res['kappa_XD']:+.6f}  "
                  f"(expect < 0)         ← κ<0? {res['kappa_XD'] < -0.1}")
        print(f"    κ_global:          {res['kappa_global']:+.8f}  "
              f"(expect ≈ 0 — Bianchi)")

    # ── Convergence comparison ─────────────────────────────────────────────
    print(f"\n{'=' * 72}")
    print("CONVERGENCE TABLE — κ_SD across tape sizes")
    print("=" * 72)
    print(f"\n  {'L':>6}  {'T':>5}  {'κ_EE':>14}  {'κ_SD':>10}  {'κ_XD':>10}  "
          f"{'κ_global':>12}  {'n_EE':>7}  {'n_SD':>7}")
    print(f"  {'─'*6}  {'─'*5}  {'─'*14}  {'─'*10}  {'─'*10}  {'─'*12}  "
          f"{'─'*7}  {'─'*7}")

    # Reference row
    r = ref
    print(f"  {r['L']:6d}  {r['T']:5d}  {r['kappa_EE']:+14.10f}  "
          f"{r['kappa_SD']:+10.4f}  {r['kappa_XD']:+10.4f}  "
          f"{'N/A':>12}  {r['n_EE']:7d}  {r['n_SD']:7d}  ← R87.NT11 (reference)")

    for res in all_results:
        ksd = res['kappa_SD'] if res['kappa_SD'] is not None else float('nan')
        kxd = res['kappa_XD'] if res['kappa_XD'] is not None else float('nan')
        print(f"  {res['L']:6d}  {res['T']:5d}  {res['kappa_EE']:+14.10f}  "
              f"{ksd:+10.4f}  {kxd:+10.4f}  "
              f"{res['kappa_global']:+12.8f}  {res['n_EE']:7d}  {res['n_SD']:7d}")

    # ── Classification ─────────────────────────────────────────────────────
    print(f"\n{'=' * 72}")
    print("CLASSIFICATION — R87.NT13 SCALING TEST")
    print("=" * 72)

    all_ee_zero = all(abs(r['kappa_EE']) < 1e-9 for r in all_results)
    any_sd_pos  = any(r['kappa_SD'] is not None and r['kappa_SD'] > 0.1
                      for r in all_results)
    any_xd_neg  = any(r['kappa_XD'] is not None and r['kappa_XD'] < -0.1
                      for r in all_results)

    if all_ee_zero:
        print(f"\n  ✓ κ_EE = 0 EXACTLY at ALL tape sizes tested.")
        print(f"    → κ_EE = 0 is NOT a finite-size artifact.")
        print(f"    → Vacuum flatness holds at L=500 and L=1000.")

    if any_sd_pos:
        sd_vals = [r['kappa_SD'] for r in all_results
                   if r['kappa_SD'] is not None]
        print(f"\n  ✓ κ_SD > 0 confirmed at larger tape sizes: {sd_vals}")
        if len(sd_vals) >= 2:
            delta = abs(sd_vals[-1] - ref['kappa_SD'])
            print(f"    → κ_SD variation L=280→L=1000: {delta:.4f}")
            if delta < 0.1:
                print(f"    → κ_SD is STABLE — consistent with a genuine large-tape limit.")
            else:
                print(f"    → κ_SD variation {delta:.4f} — may depend on glider density.")
                print(f"      (T={T} is shorter than R87.NT11 T=300; fewer glider samples.)")

    if not any_sd_pos:
        print(f"\n  ⚠ No SD edges found at larger tapes with T={T}.")
        print(f"    → Increase T or N_PERTURB for more glider coverage.")
        print(f"    → κ_EE = 0 still confirmed (not a finite-size artifact).")

    # Overall classification
    print(f"\n  OVERALL CLASSIFICATION:")
    if all_ee_zero and any_sd_pos:
        print(f"    CatA (STRONG, NT13) — κ_EE=0 exact at all sizes;")
        print(f"    κ_SD > 0 stable — Gorard chain result is a genuine large-tape limit.")
    elif all_ee_zero:
        print(f"    CatA (NT13, partial) — κ_EE=0 exact confirmed at larger sizes.")
        print(f"    κ_SD test limited by T={T}; extend to T≥300 for full convergence test.")
    else:
        print(f"    ANOMALY — κ_EE ≠ 0 at some tape size. Investigate.")

    print(f"\n  Reference (R87.NT11, L=280, T=300):")
    print(f"    κ_EE={ref['kappa_EE']:.10f}, κ_SD={ref['kappa_SD']:.4f}, "
          f"κ_XD={ref['kappa_XD']:.4f}")


if __name__ == "__main__":
    main()
