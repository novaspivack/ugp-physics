#!/usr/bin/env python3
"""
Rank 57-NBS: Neighborhood-Based Inner CA Seeding SR Test
EPIC_072 — GTE Ontological Unification
2026-05-22

Tests whether seeding the inner CA from the outer cell's local neighborhood (l,c,r)
produces a richer τ_c signal than the uniform ETHER14-phase seeding used in Round 19.

Two seeding strategies:
  A: Phase-shifted ETHER14 — neighborhood pattern (l,c,r) selects a phase offset,
     shifting the ETHER14 starting window. Locally curvature-sensitive, still ETHER14.
  B: Direct neighborhood encoding — inner CA seeded as [l,l,c,c,c,r,r],
     making the inner clock start from the outer cell's actual local environment.

SR baseline: Round 19 majority-vote ETHER14 seeding, 8.7% mean error (15 pairs).
True AFCA majority (Rank 31-ACS): 6.4% mean error.
"""

import signal
import sys
import time
import json
import numpy as np

# ── Wall-clock safety ──────────────────────────────────────────────────────────
WALL_CLOCK_LIMIT = 175
_t0 = time.time()


def _timeout_handler(s, f):
    print(f"\nWall-clock limit {WALL_CLOCK_LIMIT}s reached. Saving partial results.")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(WALL_CLOCK_LIMIT)

# ── Constants ──────────────────────────────────────────────────────────────────
ETHER14 = np.array([1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0], dtype=np.uint8)
LUT110 = np.array([(110 >> i) & 1 for i in range(8)], dtype=np.uint8)
C_EFF = 2.0 / 3.0
OUTER_L = 500
M = 7
MAX_INNER = 50

ether_base = np.array([ETHER14[i % 14] for i in range(OUTER_L)], dtype=np.uint8)


# ── CA primitives ──────────────────────────────────────────────────────────────

def run_outer(state: np.ndarray) -> np.ndarray:
    l = np.roll(state, 1).astype(np.int32)
    c = state.astype(np.int32)
    r = np.roll(state, -1).astype(np.int32)
    return LUT110[(l << 2) | (c << 1) | r]


def run_inner(state: np.ndarray) -> np.ndarray:
    l = np.roll(state, 1).astype(np.int32)
    c = state.astype(np.int32)
    r = np.roll(state, -1).astype(np.int32)
    return LUT110[(l << 2) | (c << 1) | r]


def majority(state: np.ndarray) -> int:
    return 1 if int(state.sum()) * 2 > len(state) else 0


# ── LUT construction ───────────────────────────────────────────────────────────

def build_strategy_A_lut() -> np.ndarray:
    """
    Shape (8, 2, 2): [nbr_idx, curr_bit, tgt_bit].

    For neighborhood (l,c,r), compute phase offset = (l*2 + c*4 + r*2) % 14 and
    seed the inner CA from ETHER14 at that phase. τ_c = steps until majority == tgt.

    Stored at lut[nbr_idx, c, tgt] because outer_now[i] == c by construction
    (c is the center cell of the neighborhood, which IS outer_now[i]).
    """
    lut = np.full((8, 2, 2), float(MAX_INNER), dtype=np.float32)
    for nbr_idx in range(8):
        l = (nbr_idx >> 2) & 1
        c = (nbr_idx >> 1) & 1
        r = nbr_idx & 1
        phase = (l * 2 + c * 4 + r * 2) % 14
        seed = np.array([ETHER14[(phase + j) % 14] for j in range(M)], dtype=np.uint8)
        for tgt in [0, 1]:
            s = seed.copy()
            for step in range(MAX_INNER):
                if majority(s) == tgt:
                    lut[nbr_idx, c, tgt] = float(step)
                    break
                s = run_inner(s)
    return lut


def build_strategy_B_lut() -> np.ndarray:
    """
    Shape (2, 2, 2, 2, 2): [l, c, r, curr_bit, tgt_bit].

    Inner CA seeded as [l, l, c, c, c, r, r] for outer neighborhood (l, c, r).
    Makes the inner clock start directly from the outer cell's local environment.
    Stored at lut[l, c_val, r, c_val, tgt] (curr == c_val always).
    """
    lut = np.full((2, 2, 2, 2, 2), float(MAX_INNER), dtype=np.float32)
    for l in range(2):
        for c_val in range(2):
            for r in range(2):
                seed = np.array([l, l, c_val, c_val, c_val, r, r], dtype=np.uint8)
                for tgt in [0, 1]:
                    s = seed.copy()
                    for step in range(MAX_INNER):
                        if majority(s) == tgt:
                            lut[l, c_val, r, c_val, tgt] = float(step)
                            break
                        s = run_inner(s)
    return lut


# ── Vectorized τ_c measurement functions ──────────────────────────────────────

def measure_tau_A(outer_now: np.ndarray, outer_next: np.ndarray) -> np.ndarray:
    """Strategy A: phase from neighborhood (l,c,r) → ETHER14-shifted seed."""
    l_arr = np.roll(outer_now, 1).astype(np.int32)
    c_arr = outer_now.astype(np.int32)
    r_arr = np.roll(outer_now, -1).astype(np.int32)
    nbr_idx = (l_arr << 2) | (c_arr << 1) | r_arr
    return lut_A[nbr_idx,
                 outer_now.astype(np.int32),
                 outer_next.astype(np.int32)]


def measure_tau_B(outer_now: np.ndarray, outer_next: np.ndarray) -> np.ndarray:
    """Strategy B: direct [l,l,c,c,c,r,r] neighborhood seed."""
    l_arr = np.roll(outer_now, 1).astype(np.int32)
    c_arr = outer_now.astype(np.int32)
    r_arr = np.roll(outer_now, -1).astype(np.int32)
    return lut_B[l_arr, c_arr, r_arr,
                 outer_now.astype(np.int32),
                 outer_next.astype(np.int32)]


# ── Helper: background τ_c over pure ether ────────────────────────────────────

def compute_background_tau(measure_fn, n_warmup: int = 10, n_samples: int = 20) -> float:
    s = ether_base.copy()
    taus = []
    for step in range(n_warmup + n_samples):
        s_next = run_outer(s)
        if step >= n_warmup:
            taus.append(float(measure_fn(s, s_next).mean()))
        s = s_next
    return float(np.mean(taus))


# ── Seed scan: velocity only (no τ_c), O(n_steps × L) ────────────────────────

def scan_seed_velocity(seed_str: str, n_steps: int = 200, min_stable: int = 30):
    """Compute velocity and γ for a seed without any τ_c measurement."""
    seed = np.array([int(b) for b in seed_str], dtype=np.uint8)
    center = OUTER_L // 2
    tape = ether_base.copy()
    for j, bit in enumerate(seed):
        tape[(center + j) % OUTER_L] = bit

    s_tape = tape.copy()
    s_ref = ether_base.copy()
    positions = []

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
    v = np.polyfit(np.arange(len(positions)), np.array(positions), 1)[0]
    v_over_c = abs(v / C_EFF)
    if v_over_c >= 1.0:
        return None
    gam = 1.0 / np.sqrt(1.0 - v_over_c ** 2)
    return {'v': v, 'v_over_c': v_over_c, 'gamma': gam, 'n_stable': len(positions)}


# ── τ_c measurement for a specific seed using a given measure function ─────────

def measure_tau_for_seed(seed_str: str, measure_fn,
                          n_steps: int = 200, min_stable: int = 50):
    """
    Run outer CA for seed_str and measure τ_c using measure_fn.
    Returns {ratio, g_tau, e_tau, n_valid} or None if not stable.
    """
    seed = np.array([int(b) for b in seed_str], dtype=np.uint8)
    center = OUTER_L // 2
    tape = ether_base.copy()
    for j, bit in enumerate(seed):
        tape[(center + j) % OUTER_L] = bit

    s_tape = tape.copy()
    s_ref = ether_base.copy()
    g_taus, e_taus = [], []
    n_valid = 0

    for _ in range(n_steps):
        s_tape_next = run_outer(s_tape)
        s_ref_next = run_outer(s_ref)
        diff = s_tape != s_ref
        diff_pos = np.where(diff)[0]
        if 2 <= len(diff_pos) <= 60:
            n_valid += 1
            taus = measure_fn(s_tape, s_tape_next)
            g_taus.append(float(taus[diff].mean()))
            ndiff = ~diff
            if ndiff.sum() > 0:
                e_taus.append(float(taus[ndiff].mean()))
        s_tape = s_tape_next
        s_ref = s_ref_next

    if n_valid < min_stable or not e_taus:
        return None
    g_mean = float(np.mean(g_taus))
    e_mean = float(np.mean(e_taus))
    return {
        'ratio': g_mean / max(e_mean, 1e-9),
        'g_tau': g_mean,
        'e_tau': e_mean,
        'n_valid': n_valid,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

print("=" * 65)
print("Rank 57-NBS: Neighborhood-Based Inner CA Seeding SR Test")
print(f"M={M}, OUTER_L={OUTER_L}, MAX_INNER={MAX_INNER}, timeout={WALL_CLOCK_LIMIT}s")
print("=" * 65)

# Build LUTs
lut_A = build_strategy_A_lut()
lut_B = build_strategy_B_lut()
print(f"\nLUT A shape={lut_A.shape}, mean={lut_A.mean():.4f}")
print(f"LUT B shape={lut_B.shape}, mean={lut_B.mean():.4f}")

# Per-neighborhood LUT A details
print("\nLUT A: τ_c per neighborhood (phase-shifted ETHER14 seed)")
print(f"  {'nbr':>5} {'l,c,r':>7} {'phase':>6} {'seed_maj':>9} "
      f"{'τ_same':>7} {'τ_flip':>7}")
for nbr_idx in range(8):
    l_v = (nbr_idx >> 2) & 1
    c_v = (nbr_idx >> 1) & 1
    r_v = nbr_idx & 1
    ph = (l_v * 2 + c_v * 4 + r_v * 2) % 14
    seed_v = np.array([ETHER14[(ph + j) % 14] for j in range(M)], dtype=np.uint8)
    sm = majority(seed_v)
    t_same = lut_A[nbr_idx, c_v, c_v]
    t_flip = lut_A[nbr_idx, c_v, 1 - c_v]
    print(f"  {nbr_idx:5d} {l_v},{c_v},{r_v}    {ph:6d}    {sm:9d}   "
          f"{t_same:6.0f}   {t_flip:6.0f}")

# Per-neighborhood LUT B details
print("\nLUT B: τ_c per neighborhood (direct [l,l,c,c,c,r,r] seed)")
print(f"  {'l,c,r':>7} {'seed':>17} {'seed_maj':>9} {'τ_same':>7} {'τ_flip':>7}")
for l_v in range(2):
    for c_v in range(2):
        for r_v in range(2):
            seed_v = np.array([l_v, l_v, c_v, c_v, c_v, r_v, r_v], dtype=np.uint8)
            sm = majority(seed_v)
            t_same = lut_B[l_v, c_v, r_v, c_v, c_v]
            t_flip = lut_B[l_v, c_v, r_v, c_v, 1 - c_v]
            print(f"  {l_v},{c_v},{r_v}  {list(seed_v)}  {sm:9d}   "
                  f"{t_same:6.0f}   {t_flip:6.0f}")

# Background τ_c
tau_bg_A = compute_background_tau(measure_tau_A)
tau_bg_B = compute_background_tau(measure_tau_B)
print(f"\nBackground τ_c (pure ether, {OUTER_L} cells):")
print(f"  Strategy A: {tau_bg_A:.4f}")
print(f"  Strategy B: {tau_bg_B:.4f}")

# ── Pre-scan all 1024 seeds ────────────────────────────────────────────────────
print(f"\nPre-scanning all 1024 width-10 seeds (velocity classification)...")
hi_v_candidates = []
lo_v_candidates = []

for ic in range(2 ** 10):
    seed_str = bin(ic)[2:].zfill(10)
    res = scan_seed_velocity(seed_str, n_steps=200, min_stable=30)
    if res is None:
        continue
    if 1.3 <= res['gamma'] <= 2.0 and res['n_stable'] >= 50:
        hi_v_candidates.append((seed_str, res))
    if res['v_over_c'] < 0.1 and len(lo_v_candidates) < 8:
        lo_v_candidates.append((seed_str, res))

hi_v_candidates.sort(key=lambda x: -x[1]['v_over_c'])
print(f"Found {len(hi_v_candidates)} hi-v seeds (γ∈[1.3,2.0], n_stable≥50)")
print(f"Found {len(lo_v_candidates)} lo-v seeds (v/c<0.1)")

hi_set = hi_v_candidates[:5]
lo_set = lo_v_candidates[:3]

print("\nTop hi-v seeds (up to 5):")
for s_str, r in hi_set:
    print(f"  {s_str}: v/c={r['v_over_c']:.4f}, γ={r['gamma']:.4f}, "
          f"n_stable={r['n_stable']}")
print("Lo-v reference seeds (up to 3):")
for s_str, r in lo_set:
    print(f"  {s_str}: v/c={r['v_over_c']:.4f}, γ={r['gamma']:.4f}, "
          f"n_stable={r['n_stable']}")

if not hi_set:
    print("\nERROR: No hi-v seeds found. Cannot run SR test.")
    sys.exit(1)
if not lo_set:
    print("\nERROR: No lo-v seeds found. Cannot run SR test.")
    sys.exit(1)

# ── Strategy A: measure τ_c for hi-v and lo-v seeds ───────────────────────────
print("\n=== Strategy A: Neighborhood-Phase Seeding ===")

hi_A: dict = {}
for s_str, vel in hi_set:
    tr = measure_tau_for_seed(s_str, measure_tau_A, n_steps=200, min_stable=50)
    hi_A[s_str] = (vel, tr)
    if tr:
        print(f"  hi-v {s_str}: g_τ={tr['g_tau']:.4f}, e_τ={tr['e_tau']:.4f}, "
              f"ratio={tr['ratio']:.4f}")
    else:
        print(f"  hi-v {s_str}: τ_c measurement failed (not stable)")

lo_A: dict = {}
for s_str, vel in lo_set:
    tr = measure_tau_for_seed(s_str, measure_tau_A, n_steps=200, min_stable=30)
    lo_A[s_str] = (vel, tr)
    if tr:
        print(f"  lo-v {s_str}: g_τ={tr['g_tau']:.4f}, e_τ={tr['e_tau']:.4f}, "
              f"ratio={tr['ratio']:.4f}")
    else:
        print(f"  lo-v {s_str}: τ_c measurement failed (not stable)")

errors_A = []
print(f"\nPaired SR errors (Strategy A):")
for hi_str, (hi_vel, hi_tau) in hi_A.items():
    if hi_tau is None:
        continue
    for lo_str, (lo_vel, lo_tau) in lo_A.items():
        if lo_tau is None:
            continue
        paired = hi_tau['ratio'] / max(lo_tau['ratio'], 1e-9)
        pred = hi_vel['gamma'] / lo_vel['gamma']
        err = abs(paired - pred) / pred * 100
        errors_A.append(err)
        print(f"  {hi_str}(γ={hi_vel['gamma']:.4f}) vs {lo_str}: "
              f"paired={paired:.4f}, pred={pred:.4f}, err={err:.1f}%")

mean_err_A = float(np.mean(errors_A)) if errors_A else float('nan')
best_err_A = float(min(errors_A)) if errors_A else float('nan')
print(f"\nStrategy A: {len(errors_A)} pairs, mean error = {mean_err_A:.1f}%, "
      f"best = {best_err_A:.1f}%")

# ── Strategy B: measure τ_c for hi-v and lo-v seeds ───────────────────────────
print("\n=== Strategy B: Direct Neighborhood Encoding [l,l,c,c,c,r,r] ===")

hi_B: dict = {}
for s_str, vel in hi_set:
    tr = measure_tau_for_seed(s_str, measure_tau_B, n_steps=200, min_stable=50)
    hi_B[s_str] = (vel, tr)
    if tr:
        print(f"  hi-v {s_str}: g_τ={tr['g_tau']:.4f}, e_τ={tr['e_tau']:.4f}, "
              f"ratio={tr['ratio']:.4f}")
    else:
        print(f"  hi-v {s_str}: τ_c measurement failed (not stable)")

lo_B: dict = {}
for s_str, vel in lo_set:
    tr = measure_tau_for_seed(s_str, measure_tau_B, n_steps=200, min_stable=30)
    lo_B[s_str] = (vel, tr)
    if tr:
        print(f"  lo-v {s_str}: g_τ={tr['g_tau']:.4f}, e_τ={tr['e_tau']:.4f}, "
              f"ratio={tr['ratio']:.4f}")
    else:
        print(f"  lo-v {s_str}: τ_c measurement failed (not stable)")

errors_B = []
print(f"\nPaired SR errors (Strategy B):")
for hi_str, (hi_vel, hi_tau) in hi_B.items():
    if hi_tau is None:
        continue
    for lo_str, (lo_vel, lo_tau) in lo_B.items():
        if lo_tau is None:
            continue
        paired = hi_tau['ratio'] / max(lo_tau['ratio'], 1e-9)
        pred = hi_vel['gamma'] / lo_vel['gamma']
        err = abs(paired - pred) / pred * 100
        errors_B.append(err)
        print(f"  {hi_str}(γ={hi_vel['gamma']:.4f}) vs {lo_str}: "
              f"paired={paired:.4f}, pred={pred:.4f}, err={err:.1f}%")

mean_err_B = float(np.mean(errors_B)) if errors_B else float('nan')
best_err_B = float(min(errors_B)) if errors_B else float('nan')
print(f"\nStrategy B: {len(errors_B)} pairs, mean error = {mean_err_B:.1f}%, "
      f"best = {best_err_B:.1f}%")

# ── Summary ────────────────────────────────────────────────────────────────────
BASELINE_ROUND19 = 8.7
BASELINE_ACS = 6.4

print("\n" + "=" * 65)
print("=== Rank 57-NBS: Neighborhood-Based Seeding — SUMMARY ===")
print("=" * 65)

print(f"\nBackground τ_c (pure ether, {OUTER_L} cells):")
print(f"  Strategy A (neighborhood phase): {tau_bg_A:.4f}")
print(f"  Strategy B (direct encoding):    {tau_bg_B:.4f}")

print(f"\nSR accuracy comparison:")
print(f"  Standard ETHER14 seeding (Round 19):     {BASELINE_ROUND19:.1f}%")
print(f"  True AFCA majority (Rank 31-ACS):        {BASELINE_ACS:.1f}%")
print(f"  Strategy A (neighborhood phase):         "
      f"{'N/A' if np.isnan(mean_err_A) else f'{mean_err_A:.1f}%'}")
print(f"  Strategy B (direct encoding):            "
      f"{'N/A' if np.isnan(mean_err_B) else f'{mean_err_B:.1f}%'}")


def verdict_str(mean_err: float) -> str:
    if np.isnan(mean_err):
        return "INSUFFICIENT DATA"
    if mean_err < BASELINE_ACS:
        return f"IMPROVED — beats ACS baseline ({BASELINE_ACS}%)"
    if mean_err < BASELINE_ROUND19:
        return f"IMPROVED vs Round 19 ({BASELINE_ROUND19}%)"
    return f"DEGRADED vs Round 19 ({BASELINE_ROUND19}%)"


print(f"\nVerdict:")
print(f"  Strategy A: {verdict_str(mean_err_A)}")
print(f"  Strategy B: {verdict_str(mean_err_B)}")

# LUT analysis: which neighborhood patterns have high/low τ_c in each strategy
print("\nKey LUT differences:")
print("  Strategy A: τ_c spread across neighborhoods?")
a_flip_vals = [lut_A[i, (i >> 1) & 1, 1 - ((i >> 1) & 1)] for i in range(8)]
print(f"    τ_flip values across 8 neighborhoods: {[f'{x:.0f}' for x in a_flip_vals]}")
print(f"    Range: {min(a_flip_vals):.0f}–{max(a_flip_vals):.0f} "
      f"(Round 19 standard: all = 1)")

print("  Strategy B: which (l,c,r) have high τ_flip (potential clock signal)?")
for l_v in range(2):
    for c_v in range(2):
        for r_v in range(2):
            t_flip = lut_B[l_v, c_v, r_v, c_v, 1 - c_v]
            t_same = lut_B[l_v, c_v, r_v, c_v, c_v]
            seed_v = [l_v, l_v, c_v, c_v, c_v, r_v, r_v]
            sm = majority(np.array(seed_v, dtype=np.uint8))
            mismatch = "*" if sm != c_v else " "
            print(f"    ({l_v},{c_v},{r_v}){mismatch}: same={t_same:.0f}, flip={t_flip:.0f}"
                  f"  {'← high τ_flip' if t_flip >= 10 else ''}"
                  f"  {'← seed_maj≠c' if sm != c_v else ''}")

print("\nPhysical interpretation:")
if not np.isnan(mean_err_A):
    if mean_err_A < BASELINE_ROUND19:
        print("  Strategy A: Neighborhood phase shift gives more varied τ_c seeds,")
        print("  improving glider/ether discrimination over uniform ETHER14 seeding.")
        print("  Local curvature (neighborhood) carries Lorentz-factor information.")
    else:
        print("  Strategy A: Neighborhood phase shift does not improve SR accuracy.")
        print("  Phase offsets 0,2,4,6,8 do not create additional discriminating power")
        print("  over uniform seeding — the majority-vote mechanism is phase-insensitive.")

if not np.isnan(mean_err_B):
    if mean_err_B < BASELINE_ROUND19:
        print("  Strategy B: Direct [l,l,c,c,c,r,r] encoding gives richer τ_c signal.")
        print("  Seeds whose majority disagrees with c (mismatch neighborhoods) create")
        print("  longer first-passage times, amplifying the glider/ether contrast.")
    else:
        print("  Strategy B: Direct encoding does not improve SR accuracy.")
        print("  The [l,l,c,c,c,r,r] seeds reach target states at similar rates for")
        print("  glider and ether cells — the neighborhood information does not add")
        print("  discriminating power beyond the standard (curr→tgt) pair asymmetry.")

# ── Save JSON ──────────────────────────────────────────────────────────────────
lut_A_detail = {}
for nbr_idx in range(8):
    l_v = (nbr_idx >> 2) & 1
    c_v = (nbr_idx >> 1) & 1
    r_v = nbr_idx & 1
    ph = (l_v * 2 + c_v * 4 + r_v * 2) % 14
    seed_v = [int(ETHER14[(ph + j) % 14]) for j in range(M)]
    lut_A_detail[f"{l_v}{c_v}{r_v}"] = {
        "phase": ph,
        "seed": seed_v,
        "seed_maj": int(majority(np.array(seed_v, dtype=np.uint8))),
        "tau_same": float(lut_A[nbr_idx, c_v, c_v]),
        "tau_flip": float(lut_A[nbr_idx, c_v, 1 - c_v]),
    }

lut_B_detail = {}
for l_v in range(2):
    for c_v in range(2):
        for r_v in range(2):
            seed_v = [l_v, l_v, c_v, c_v, c_v, r_v, r_v]
            lut_B_detail[f"{l_v}{c_v}{r_v}"] = {
                "seed": seed_v,
                "seed_maj": int(majority(np.array(seed_v, dtype=np.uint8))),
                "tau_same": float(lut_B[l_v, c_v, r_v, c_v, c_v]),
                "tau_flip": float(lut_B[l_v, c_v, r_v, c_v, 1 - c_v]),
            }

results = {
    "rank": "57-NBS",
    "test": "neighborhood_based_inner_ca_seeding_sr_test",
    "date": "2026-05-22",
    "parameters": {
        "M": M,
        "outer_L": OUTER_L,
        "max_inner": MAX_INNER,
        "wall_clock_limit": WALL_CLOCK_LIMIT,
        "c_eff": C_EFF,
        "ether14": ETHER14.tolist(),
    },
    "lut_a_neighborhood_phase": {
        "shape": list(lut_A.shape),
        "mean": round(float(lut_A.mean()), 6),
        "background_tau_ether": round(tau_bg_A, 6),
        "per_neighborhood": lut_A_detail,
    },
    "lut_b_direct_encoding": {
        "shape": list(lut_B.shape),
        "mean": round(float(lut_B.mean()), 6),
        "background_tau_ether": round(tau_bg_B, 6),
        "per_neighborhood": lut_B_detail,
    },
    "seed_search": {
        "n_hi_v_found": len(hi_v_candidates),
        "n_lo_v_found": len(lo_v_candidates),
        "hi_v_set": [
            {"seed": s, "v_over_c": round(r["v_over_c"], 6),
             "gamma": round(r["gamma"], 6), "n_stable": r["n_stable"]}
            for s, r in hi_set
        ],
        "lo_v_set": [
            {"seed": s, "v_over_c": round(r["v_over_c"], 6),
             "gamma": round(r["gamma"], 6), "n_stable": r["n_stable"]}
            for s, r in lo_set
        ],
    },
    "strategy_A_results": {
        "n_pairs": len(errors_A),
        "mean_error_pct": round(mean_err_A, 2) if not np.isnan(mean_err_A) else None,
        "best_error_pct": round(best_err_A, 2) if not np.isnan(best_err_A) else None,
        "hi_v_tau": {
            s: {"g_tau": round(tr["g_tau"], 6), "e_tau": round(tr["e_tau"], 6),
                "ratio": round(tr["ratio"], 6), "n_valid": tr["n_valid"]}
            for s, (_, tr) in hi_A.items() if tr
        },
        "lo_v_tau": {
            s: {"g_tau": round(tr["g_tau"], 6), "e_tau": round(tr["e_tau"], 6),
                "ratio": round(tr["ratio"], 6), "n_valid": tr["n_valid"]}
            for s, (_, tr) in lo_A.items() if tr
        },
    },
    "strategy_B_results": {
        "n_pairs": len(errors_B),
        "mean_error_pct": round(mean_err_B, 2) if not np.isnan(mean_err_B) else None,
        "best_error_pct": round(best_err_B, 2) if not np.isnan(best_err_B) else None,
        "hi_v_tau": {
            s: {"g_tau": round(tr["g_tau"], 6), "e_tau": round(tr["e_tau"], 6),
                "ratio": round(tr["ratio"], 6), "n_valid": tr["n_valid"]}
            for s, (_, tr) in hi_B.items() if tr
        },
        "lo_v_tau": {
            s: {"g_tau": round(tr["g_tau"], 6), "e_tau": round(tr["e_tau"], 6),
                "ratio": round(tr["ratio"], 6), "n_valid": tr["n_valid"]}
            for s, (_, tr) in lo_B.items() if tr
        },
    },
    "comparison": {
        "round19_ether14_seeding_pct": BASELINE_ROUND19,
        "rank31_acs_true_afca_pct": BASELINE_ACS,
        "strategy_A_pct": round(mean_err_A, 2) if not np.isnan(mean_err_A) else None,
        "strategy_B_pct": round(mean_err_B, 2) if not np.isnan(mean_err_B) else None,
    },
    "verdict": {
        "strategy_A": verdict_str(mean_err_A),
        "strategy_B": verdict_str(mean_err_B),
    },
}

OUT_JSON = "rank57_nbs_results.json"
with open(OUT_JSON, "w") as f:
    json.dump(results, f, indent=2)

import os
json_size = os.path.getsize(OUT_JSON)
assert json_size < 1_000_000, f"JSON too large: {json_size} bytes"
print(f"\nResults saved: {OUT_JSON} ({json_size / 1024:.1f} KB)")

signal.alarm(0)
elapsed = time.time() - _t0
print(f"Total elapsed: {elapsed:.2f}s")
