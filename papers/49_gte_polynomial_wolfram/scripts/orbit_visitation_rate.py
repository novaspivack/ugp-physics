#!/usr/bin/env python3
"""
orbit_visitation_rate.py — SM orbit triple visitation rate in p mod 7 chaotic bulk.

Measures how often the GTE polynomial CA p(L,C,R) mod 7 visits the 10 SM orbit
neighborhoods during chaotic evolution from ether + single-cell Z₇ injection.

The key question: does chaotic excitation dress the ether background with SM
orbit triple configurations (L,C,R) at a rate comparable to the HVP gap (26.9%)?

Output figure saved to figures/ subdirectory:
  p49_orbit_visitation_rates.png — bar chart of orbit visitation rates

f_MDL table: 10 SM orbit triples from the canonical P41 derivation, plus
8 binary Rule 110 entries.

Dependencies:
  numpy, matplotlib — pip install numpy matplotlib
  taichi 1.7.3      — pip install "taichi==1.7.3"
    IMPORTANT: do NOT add `from __future__ import annotations` to this file
    (breaks Taichi's kernel argument type inspection at import time).

Expected runtime: ~5 minutes on CPU (L=10 000, T=2 000). TIMEOUT_SECONDS=300.
"""

import json
import signal
import sys
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import taichi as ti

TIMEOUT_SECONDS = 300
SCRIPT_DIR = Path(__file__).resolve().parent
FIGURES_DIR = SCRIPT_DIR / "figures"

# --- f_MDL tables (verbatim from P41 two_layer_chiral_afca_prototype.py) ---

# 10 SM orbit triples (non-binary entries of f_MDL)
SM_ORBIT_TRIPLES = {
    (1, 1, 5): 2, (1, 5, 2): 5, (5, 2, 2): 2, (2, 2, 1): 0,
    (2, 1, 1): 2, (2, 2, 5): 5, (2, 5, 2): 6, (5, 2, 0): 5,
    (2, 0, 2): 3, (0, 2, 2): 5,
}

# 8 binary Rule 110 triples
RULE110_TRIPLES = {
    (1, 1, 1): 0, (1, 1, 0): 1, (1, 0, 1): 1, (1, 0, 0): 0,
    (0, 1, 1): 1, (0, 1, 0): 1, (0, 0, 1): 1, (0, 0, 0): 0,
}

# Period-14 Rule 110 ether background (all-binary, Lean-certified: rule110_z7_poly_rep)
ETHER_14 = [1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0]

L = 10_000
T = 2_000

# Triple-type lookup: index = L*49 + C*7 + R  (L,C,R in {0..6})
# 0 = off-orbit chaotic, 1 = binary Rule 110, 2 = SM orbit
TRIPLE_TYPE_LUT = np.zeros(343, dtype=np.int32)
for (l_, c_, r_) in RULE110_TRIPLES:
    TRIPLE_TYPE_LUT[l_ * 49 + c_ * 7 + r_] = 1
for (l_, c_, r_) in SM_ORBIT_TRIPLES:
    TRIPLE_TYPE_LUT[l_ * 49 + c_ * 7 + r_] = 2


def _timeout_handler(signum, frame):
    print(f"\nTIMEOUT: {TIMEOUT_SECONDS}s wall-clock limit reached. Saving partial results.")
    sys.exit(1)


# --- Taichi setup (reuses kernel pattern from z7_glider_search_taichi.py) ---
print("[Taichi] Initialising CPU backend...")
ti.init(arch=ti.cpu)

MAX_CELLS = L + 16
_cur = ti.field(dtype=ti.i32, shape=(MAX_CELLS,))
_nxt = ti.field(dtype=ti.i32, shape=(MAX_CELLS,))


@ti.func
def _poly(l, c, r):
    """p(L,C,R) = (C + R - C*R - L*C*R) mod 7 — always non-negative."""
    raw = c + r - c * r - l * c * r
    return ((raw % 7) + 7) % 7


@ti.kernel
def _step_kernel(n: ti.template()):
    for i in range(n):
        l = _cur[(i - 1 + n) % n]
        c = _cur[i]
        r = _cur[(i + 1) % n]
        _nxt[i] = _poly(l, c, r)


@ti.kernel
def _swap_kernel(n: ti.template()):
    for i in range(n):
        _cur[i] = _nxt[i]


def make_ether(size: int) -> np.ndarray:
    """Tile ETHER_14 to fill `size` cells."""
    reps = size // 14 + 2
    return np.array(ETHER_14 * reps, dtype=np.int32)[:size]


def load_state(arr: np.ndarray) -> None:
    padded = np.zeros(MAX_CELLS, dtype=np.int32)
    padded[:len(arr)] = arr
    _cur.from_numpy(padded)


def get_state() -> np.ndarray:
    return _cur.to_numpy()[:L]


def classify_triples(state: np.ndarray) -> np.ndarray:
    """
    Vectorized triple classification.
    For each cell i, the triple is (state[i-1], state[i], state[i+1]) (periodic).
    Returns int32 array of shape (L,): 0=off-orbit, 1=binary, 2=SM-orbit.
    """
    l_vals = np.roll(state, 1)   # l_vals[i] = state[i-1]
    r_vals = np.roll(state, -1)  # r_vals[i] = state[i+1]
    idx = l_vals * 49 + state * 7 + r_vals
    return TRIPLE_TYPE_LUT[idx]


def run_visitation(injection_value=3, label="injection_w3") -> dict:
    """
    Run p mod 7 CA for T steps from ether (+optional injection) IC.
    Accumulate triple-type counts and inside/outside light-cone breakdown.
    """
    center = L // 2
    ether = make_ether(L)

    state_init = ether.copy()
    if injection_value is not None:
        state_init[center] = injection_value

    load_state(state_init)
    state = get_state()

    # Global accumulators
    total_binary = 0
    total_orbit = 0
    total_other = 0

    # Inside/outside light-cone accumulators (for orbit and all triples)
    orbit_inside = 0
    orbit_outside = 0
    binary_inside = 0
    binary_outside = 0
    other_inside = 0
    other_outside = 0

    positions = np.arange(L, dtype=np.int32)

    t0 = time.time()
    completed_steps = 0

    for step in range(T):
        if time.time() - t0 > TIMEOUT_SECONDS - 50:
            print(f"  [{label}] Wall-clock limit at step {step}. Saving partial.")
            break

        # Classify triples of current state
        types = classify_triples(state)

        # Light-cone mask: inside if distance from center <= step
        inside = np.abs(positions - center) <= step

        b = int(np.sum(types == 1))
        o = int(np.sum(types == 2))
        oth = int(np.sum(types == 0))
        total_binary += b
        total_orbit += o
        total_other += oth

        orbit_inside += int(np.sum((types == 2) & inside))
        orbit_outside += int(np.sum((types == 2) & ~inside))
        binary_inside += int(np.sum((types == 1) & inside))
        binary_outside += int(np.sum((types == 1) & ~inside))
        other_inside += int(np.sum((types == 0) & inside))
        other_outside += int(np.sum((types == 0) & ~inside))

        # Advance CA
        _step_kernel(L)
        _swap_kernel(L)
        state = get_state()
        completed_steps += 1

        if step % 400 == 0 and step > 0:
            elapsed = time.time() - t0
            tot_so_far = total_binary + total_orbit + total_other
            pct = total_orbit / tot_so_far * 100 if tot_so_far > 0 else 0
            print(f"  [{label}] step {step}/{T} — orbit_rate={pct:.2f}%  elapsed={elapsed:.1f}s")

    total = total_binary + total_orbit + total_other
    total_inside = binary_inside + orbit_inside + other_inside
    total_outside = binary_outside + orbit_outside + other_outside
    elapsed = time.time() - t0

    def safe_rate(n, d):
        return n / d if d > 0 else 0.0

    result = {
        "label": label,
        "injection_value": injection_value,
        "completed_steps": completed_steps,
        "total_observations": total,
        "total_binary": total_binary,
        "total_orbit": total_orbit,
        "total_other": total_other,
        "binary_rate": safe_rate(total_binary, total),
        "orbit_rate": safe_rate(total_orbit, total),
        "other_rate": safe_rate(total_other, total),
        "orbit_inside": orbit_inside,
        "orbit_outside": orbit_outside,
        "total_inside": total_inside,
        "total_outside": total_outside,
        "orbit_inside_rate": safe_rate(orbit_inside, total_inside),
        "orbit_outside_rate": safe_rate(orbit_outside, total_outside),
        "binary_inside_rate": safe_rate(binary_inside, total_inside),
        "binary_outside_rate": safe_rate(binary_outside, total_outside),
        "other_inside_rate": safe_rate(other_inside, total_inside),
        "other_outside_rate": safe_rate(other_outside, total_outside),
        "wall_time_s": elapsed,
    }

    print(f"\n  [{label}] RESULTS (L={L}, T={completed_steps}):")
    print(f"    Total observations: {total:,}")
    print(f"    Binary rate:  {result['binary_rate']*100:.2f}%")
    print(f"    Orbit rate:   {result['orbit_rate']*100:.2f}%  ← KEY")
    print(f"    Other rate:   {result['other_rate']*100:.2f}%")
    print(f"    --- Light-cone split ---")
    print(f"    Orbit rate inside cone:   {result['orbit_inside_rate']*100:.2f}%")
    print(f"    Orbit rate outside cone:  {result['orbit_outside_rate']*100:.2f}%")
    print(f"    Binary inside:  {result['binary_inside_rate']*100:.2f}%  "
          f"Binary outside: {result['binary_outside_rate']*100:.2f}%")
    print(f"    Wall time: {elapsed:.1f}s")

    return result


def run_baseline_ether() -> dict:
    """
    Run pure ether (no injection) as the baseline.
    Expected: orbit_rate = 0% since ether is all-binary.
    """
    ether = make_ether(L)
    load_state(ether)
    state = get_state()

    total_binary = 0
    total_orbit = 0
    total_other = 0

    t0 = time.time()
    completed_steps = 0

    # Only need a few hundred steps — ether is periodic, rates won't change
    T_baseline = min(T, 500)
    for step in range(T_baseline):
        if time.time() - t0 > 60:
            print(f"  [baseline] Stopping early at step {step}")
            break

        types = classify_triples(state)
        total_binary += int(np.sum(types == 1))
        total_orbit += int(np.sum(types == 2))
        total_other += int(np.sum(types == 0))

        _step_kernel(L)
        _swap_kernel(L)
        state = get_state()
        completed_steps += 1

    total = total_binary + total_orbit + total_other
    elapsed = time.time() - t0

    result = {
        "label": "pure_ether",
        "injection_value": None,
        "completed_steps": completed_steps,
        "total_observations": total,
        "total_binary": total_binary,
        "total_orbit": total_orbit,
        "total_other": total_other,
        "binary_rate": total_binary / total if total else 0.0,
        "orbit_rate": total_orbit / total if total else 0.0,
        "other_rate": total_other / total if total else 0.0,
        "wall_time_s": elapsed,
    }

    print(f"\n  [baseline] RESULTS (L={L}, T={completed_steps}):")
    print(f"    Total observations: {total:,}")
    print(f"    Binary rate:  {result['binary_rate']*100:.4f}%")
    print(f"    Orbit rate:   {result['orbit_rate']*100:.4f}%  (expected: 0.00%)")
    print(f"    Other rate:   {result['other_rate']*100:.4f}%")
    print(f"    Wall time: {elapsed:.1f}s")

    return result


def plot_results(baseline: dict, injection: dict, out_path: Path) -> None:
    """Bar chart comparing visitation rates: baseline vs injection, inside vs outside cone."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # --- Left panel: overall rates comparison ---
    ax = axes[0]
    categories = ['Binary\n(Rule 110)', 'SM Orbit\n(10 triples)', 'Other\n(off-orbit)']
    x = np.arange(3)
    width = 0.35

    base_vals = [baseline['binary_rate'] * 100,
                 baseline['orbit_rate'] * 100,
                 baseline['other_rate'] * 100]
    inj_vals = [injection['binary_rate'] * 100,
                injection['orbit_rate'] * 100,
                injection['other_rate'] * 100]

    bars1 = ax.bar(x - width / 2, base_vals, width, label='Pure ether (baseline)', color='steelblue', alpha=0.8)
    bars2 = ax.bar(x + width / 2, inj_vals, width, label=f"Ether + w=3 injection", color='darkorange', alpha=0.8)
    ax.axhline(y=26.9, color='red', linestyle='--', linewidth=1.5, label='HVP gap target (26.9%)')
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.set_ylabel('Visitation rate (%)')
    ax.set_title(f'SM Orbit Triple Visitation Rate\n(overall, L={L}, T={injection["completed_steps"]})')
    ax.legend(fontsize=9)

    for bar in bars1:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h + 0.3, f'{h:.1f}%', ha='center', va='bottom', fontsize=8)
    for bar in bars2:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h + 0.3, f'{h:.1f}%', ha='center', va='bottom', fontsize=8)

    # --- Right panel: inside vs outside cone (orbit triples) ---
    ax2 = axes[1]
    cone_labels = ['Outside cone\n(unperturbed ether)', 'Inside cone\n(chaotic excitation)']
    out_pct = injection.get('orbit_outside_rate', 0) * 100
    in_pct = injection.get('orbit_inside_rate', 0) * 100

    colors = ['steelblue', 'darkorange']
    bars3 = ax2.bar(cone_labels, [out_pct, in_pct], color=colors, alpha=0.8, width=0.5)
    ax2.axhline(y=26.9, color='red', linestyle='--', linewidth=1.5, label='HVP gap target (26.9%)')
    ax2.axhline(y=100 * 10 / 343, color='gray', linestyle=':', linewidth=1.2, label='Naive random (2.9%)')
    ax2.set_ylabel('Orbit triple fraction (% of all triples in region)')
    ax2.set_title('SM Orbit Visitation: Inside vs Outside\nCausal Light Cone')
    ax2.legend(fontsize=9)

    for bar in bars3:
        h = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width() / 2, h + 0.3, f'{h:.2f}%', ha='center', va='bottom', fontsize=11, fontweight='bold')

    fig.suptitle('SM Orbit Triple Visitation Rate in p mod 7 CA', fontsize=13, fontweight='bold')
    fig.tight_layout()
    fig.savefig(out_path, dpi=130, bbox_inches='tight')
    plt.close(fig)
    print(f"Plot saved: {out_path.name}")


def main() -> dict:
    signal.signal(signal.SIGALRM, _timeout_handler)
    signal.alarm(TIMEOUT_SECONDS)
    t_global = time.time()

    print("=" * 65)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    print("SM Orbit Triple Visitation Rate in p mod 7 CA")
    print(f"GTE polynomial: p(L,C,R) = (C+R-C*R-L*C*R) mod 7")
    print(f"L={L:,}, T={T:,}")
    print(f"SM orbit triples (10): {list(SM_ORBIT_TRIPLES.keys())}")
    print(f"Binary triples (8): {list(RULE110_TRIPLES.keys())}")
    print(f"Naive random expectation: orbit={10/343*100:.2f}%, binary={8/343*100:.2f}%")
    print(f"HVP gap target: 26.9%")
    print("=" * 65)

    print("\n=== Pass 1: Pure ether baseline ===")
    baseline = run_baseline_ether()

    print("\n=== Pass 2: Ether + w=3 injection ===")
    injection = run_visitation(injection_value=3, label="injection_w3")

    # Plot
    plot_path = FIGURES_DIR / "p49_orbit_visitation_rates.png"
    plot_results(baseline, injection, plot_path)

    # Verdict
    orbit_rate_pct = injection['orbit_rate'] * 100
    orbit_inside_pct = injection.get('orbit_inside_rate', 0) * 100
    baseline_orbit_pct = baseline['orbit_rate'] * 100
    injection_increase = orbit_inside_pct - baseline_orbit_pct

    print("\n" + "=" * 65)
    print("VERDICT")
    print("=" * 65)
    print(f"Baseline (pure ether) orbit rate:       {baseline_orbit_pct:.4f}%")
    print(f"Injection overall orbit rate:            {orbit_rate_pct:.2f}%")
    print(f"Injection INSIDE CONE orbit rate:        {orbit_inside_pct:.2f}%  ← KEY")
    print(f"Injection outside cone orbit rate:       {injection.get('orbit_outside_rate',0)*100:.4f}%")
    print(f"Injection increases orbit visits:        {injection_increase:.2f}pp above baseline")
    print(f"HVP gap target:                          26.90%")
    print(f"Naive random expectation:                {10/343*100:.2f}%")

    near_hvp = 20.0 <= orbit_inside_pct <= 35.0
    near_hvp_overall = 20.0 <= orbit_rate_pct <= 35.0

    if near_hvp:
        verdict = f"HIT — inside-cone orbit rate {orbit_inside_pct:.2f}% is near HVP gap 26.9%"
    elif near_hvp_overall:
        verdict = f"NEAR HIT — overall orbit rate {orbit_rate_pct:.2f}% is near HVP gap 26.9%"
    elif orbit_inside_pct < 5.0:
        verdict = f"RULED OUT — inside-cone rate {orbit_inside_pct:.2f}% << HVP gap (near naive random)"
    elif orbit_inside_pct > 50.0:
        verdict = f"RULED OUT — inside-cone rate {orbit_inside_pct:.2f}% >> HVP gap (near uniform chaotic)"
    else:
        verdict = f"MISS — inside-cone rate {orbit_inside_pct:.2f}% does not match HVP gap 26.9%"

    print(f"\nVerdict: {verdict}")

    # Save results
    results = {
        "run_label": "sm_orbit_visitation",
        "L": L,
        "T": T,
        "baseline": baseline,
        "injection": injection,
        "hvp_target": 0.269,
        "naive_random_orbit": 10 / 343,
        "orbit_rate_pct": orbit_rate_pct,
        "orbit_inside_rate_pct": orbit_inside_pct,
        "injection_increase_pp": injection_increase,
        "verdict": verdict,
        "near_hvp_inside": near_hvp,
        "near_hvp_overall": near_hvp_overall,
        "sm_orbit_triples": [list(k) for k in SM_ORBIT_TRIPLES.keys()],
        "total_wall_time_s": time.time() - t_global,
    }

    json_path = SCRIPT_DIR / "orbit_visitation_results.json"
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved: {json_path.name}")
    print(f"Total wall time: {time.time() - t_global:.1f}s")

    signal.alarm(0)
    return results


if __name__ == "__main__":
    main()
