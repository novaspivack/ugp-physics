from pathlib import Path
SCRIPT_DIR = Path(__file__).resolve().parent
#!/usr/bin/env python3
"""
Rank 51-NLD: N-Level FCA Depth SR Test
EPIC_072

Tests whether SR accuracy improves as FCA recursion depth N increases (N=2,3,4).
Inner CA always ETHER14-seeded at every level — no LLN artifact from random init.

N=2: baseline, exactly reproduces Round 19 (tau_lut[curr_bit][tgt_bit] = [[0,1],[1,0]])
N=3: each level-2 step costs mean(tau_lut_n2[l2, l2_next]) level-3 steps
N=4: each level-2 step costs mean(tau_c_n3[tgt=l2_next[j], phase=(p+j)%14]) level-4 steps

Key improvement over Run SRT-6 (Round 7): ether-seeded inner CAs (not biased-random),
so no LLN collapse that artificially shrinks tau_c at larger N.
"""

import numpy as np
import json
import time
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ETHER14 = np.array([1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0], dtype=np.uint8)
LUT110 = np.array([(110 >> i) & 1 for i in range(8)], dtype=np.uint8)
C_EFF = 2.0 / 3.0
OUTER_L = 500
M = 7
MAX_INNER = 50

ether_base = np.tile(ETHER14, OUTER_L // 14 + 1)[:OUTER_L].astype(np.uint8)

# Base N=2 LUT: tau_lut_n2[curr_bit, tgt_bit]
tau_lut_n2 = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.float32)


# ─── CA stepping ─────────────────────────────────────────────────────────────

def run_outer(state):
    """Vectorized Rule 110 step on OUTER_L-cell ring."""
    l = np.roll(state, 1).astype(np.int32)
    c = state.astype(np.int32)
    r = np.roll(state, -1).astype(np.int32)
    return LUT110[(l << 2) | (c << 1) | r]


def run_inner_step(state):
    """Vectorized Rule 110 step on M-cell ring (periodic BC)."""
    l = np.roll(state, 1).astype(np.int32)
    c = state.astype(np.int32)
    r = np.roll(state, -1).astype(np.int32)
    return LUT110[(l << 2) | (c << 1) | r]


def inner_majority(state):
    return 1 if state.sum() * 2 > len(state) else 0


# ─── N=3 recursive τ_c ───────────────────────────────────────────────────────

def _tau_c_n3_raw(tgt_bit, phase):
    """
    N=3 τ_c: total level-3 step-equivalents for the level-2 inner CA
    (M=7, seeded from ETHER14 at `phase`) to reach majority == tgt_bit.
    Cost per level-2 step = mean(tau_lut_n2[l2, l2_next]) across M cells.
    Returns 0.0 if already at target majority.
    """
    l2 = np.array([ETHER14[(phase + j) % 14] for j in range(M)], dtype=np.uint8)
    total = 0.0
    for _ in range(MAX_INNER):
        if inner_majority(l2) == tgt_bit:
            break
        l2_next = run_inner_step(l2)
        total += float(tau_lut_n2[l2.astype(int), l2_next.astype(int)].mean())
        l2 = l2_next
    return total


# Memoize: only 14 × 2 = 28 unique (phase, tgt) pairs
_n3_cache: dict = {}


def tau_c_n3(tgt_bit, phase):
    key = (tgt_bit, phase)
    if key not in _n3_cache:
        _n3_cache[key] = _tau_c_n3_raw(tgt_bit, phase)
    return _n3_cache[key]


def build_phase_table_n3():
    """Precompute 14×2 N=3 phase table."""
    table = np.zeros((14, 2), dtype=np.float32)
    for phase in range(14):
        for tgt in range(2):
            table[phase, tgt] = tau_c_n3(tgt, phase)
    return table


# ─── N=4 recursive τ_c ───────────────────────────────────────────────────────

def _tau_c_n4_raw(tgt_bit, phase):
    """
    N=4 τ_c: level-2 inner CA (ETHER14-seeded at `phase`) runs until majority == tgt_bit.
    Cost per level-2 step = mean over M cells of tau_c_n3(tgt=l2_next[j], phase=(phase+j)%14).
    """
    l2 = np.array([ETHER14[(phase + j) % 14] for j in range(M)], dtype=np.uint8)
    total = 0.0
    for _ in range(MAX_INNER):
        if inner_majority(l2) == tgt_bit:
            break
        l2_next = run_inner_step(l2)
        l3_costs = np.array(
            [tau_c_n3(int(l2_next[j]), (phase + j) % 14) for j in range(M)],
            dtype=np.float32,
        )
        total += float(l3_costs.mean())
        l2 = l2_next
    return total


_n4_cache: dict = {}


def tau_c_n4(tgt_bit, phase):
    key = (tgt_bit, phase)
    if key not in _n4_cache:
        _n4_cache[key] = _tau_c_n4_raw(tgt_bit, phase)
    return _n4_cache[key]


def build_phase_table_n4():
    """Precompute 14×2 N=4 phase table."""
    table = np.zeros((14, 2), dtype=np.float32)
    for phase in range(14):
        for tgt in range(2):
            table[phase, tgt] = tau_c_n4(tgt, phase)
    return table


# ─── Background τ_c measurement ──────────────────────────────────────────────

def measure_bg_tau(N, tau_phase_table=None, n_warmup=10, n_measure=10):
    """
    Measure background τ_c on pure ETHER14-tiled tape over n_measure steps
    after n_warmup warmup steps.
    N=2 uses tau_lut_n2[s[i], s_next[i]] directly (exact Round 19 match).
    N=3,4 use tau_phase_table[phase, s_next[i]].
    """
    phases = np.arange(OUTER_L, dtype=np.int32) % 14
    s = ether_base.copy()
    bg_vals = []
    for step in range(n_warmup + n_measure):
        s_next = run_outer(s)
        if step >= n_warmup:
            if N == 2:
                taus = tau_lut_n2[s.astype(int), s_next.astype(int)]
            else:
                taus = tau_phase_table[phases, s_next.astype(int)]
            bg_vals.append(float(taus.mean()))
        s = s_next
    return float(np.mean(bg_vals))


# ─── Seed test ───────────────────────────────────────────────────────────────

def test_seed_full_n(seed_str, N, tau_phase_table=None, n_steps=200, min_stable=50):
    """
    Stability test + τ_c measurement for a width-10 seed.
    N=2: uses tau_lut_n2[s_tape, s_tape_next] — exact Round 19 formulation.
    N=3,4: uses tau_phase_table[phase, s_tape_next].
    Returns dict with v, v_over_c, gamma, ratio, n_stable, or None if unstable.
    """
    seed = np.array([int(b) for b in seed_str], dtype=np.uint8)
    center = OUTER_L // 2
    tape = ether_base.copy()
    for j, bit in enumerate(seed):
        tape[(center + j) % OUTER_L] = bit

    s_tape = tape.copy()
    s_ref = ether_base.copy()
    phases = np.arange(OUTER_L, dtype=np.int32) % 14
    fallback_tau = (
        float(tau_lut_n2.mean())
        if N == 2
        else float(tau_phase_table[:, 0].mean())
    )

    positions, g_taus, e_taus = [], [], []

    for _ in range(n_steps):
        s_tape_next = run_outer(s_tape)
        s_ref_next = run_outer(s_ref)

        diff = s_tape != s_ref
        diff_pos = np.where(diff)[0]

        if 2 <= len(diff_pos) <= 60:
            positions.append(float(diff_pos.mean()))
            if N == 2:
                taus = tau_lut_n2[s_tape.astype(int), s_tape_next.astype(int)]
            else:
                taus = tau_phase_table[phases, s_tape_next.astype(int)]
            g_taus.append(float(taus[diff].mean()))
            ndiff = ~diff
            e_taus.append(
                float(taus[ndiff].mean()) if ndiff.sum() > 0 else fallback_tau
            )

        s_tape = s_tape_next
        s_ref = s_ref_next

    if len(positions) < min_stable:
        return None

    v = np.polyfit(np.arange(len(positions)), np.array(positions), 1)[0]
    v_over_c = abs(v / C_EFF)
    if v_over_c >= 1.0:
        return None

    gam = 1.0 / np.sqrt(1.0 - v_over_c**2)
    ratio = (
        float(np.mean(g_taus)) / float(np.mean(e_taus))
        if e_taus and np.mean(e_taus) > 0
        else None
    )
    return {
        "v": float(v),
        "v_over_c": float(v_over_c),
        "gamma": float(gam),
        "ratio": float(ratio) if ratio is not None else None,
        "n_stable": len(positions),
    }


# ─── Seed search ─────────────────────────────────────────────────────────────

def search_hi_v_seeds(N, tau_phase_table, gamma_low=1.3, gamma_high=2.0):
    """All 1024 width-10 seeds; keep those with stable γ ∈ [gamma_low, gamma_high]."""
    found = []
    for ic in range(1024):
        s = bin(ic)[2:].zfill(10)
        r = test_seed_full_n(s, N, tau_phase_table, n_steps=200, min_stable=50)
        if r and gamma_low <= r["gamma"] <= gamma_high and r["ratio"] is not None:
            found.append((s, r))
    return found


def search_lo_v_seeds(N, tau_phase_table, n_max=5, v_thr=0.1):
    """Search for low-v reference seeds (|v/c| < v_thr, stable ≥ 30 steps)."""
    found = []
    for ic in range(1024):
        s = bin(ic)[2:].zfill(10)
        r = test_seed_full_n(s, N, tau_phase_table, n_steps=100, min_stable=30)
        if r and r["v_over_c"] < v_thr and r["ratio"] is not None:
            found.append((s, r))
            if len(found) >= n_max:
                break
    return found


def paired_sr_test(hi_seeds, lo_seeds, n_hi=5, n_lo=3):
    """Run n_hi × n_lo paired SR error tests."""
    hi_set = sorted(hi_seeds, key=lambda x: -x[1]["v_over_c"])[:n_hi]
    lo_set = lo_seeds[:n_lo]
    errors, pairs = [], []
    for hs, hr in hi_set:
        for ls, lr in lo_set:
            if hr["ratio"] is None or lr["ratio"] is None or lr["ratio"] == 0:
                continue
            paired = hr["ratio"] / lr["ratio"]
            pred = hr["gamma"] / lr["gamma"]
            err = abs(paired - pred) / pred * 100.0
            errors.append(err)
            pairs.append(
                {
                    "hi": hs,
                    "lo": ls,
                    "hi_gamma": hr["gamma"],
                    "lo_gamma": lr["gamma"],
                    "paired": paired,
                    "pred": pred,
                    "err": err,
                }
            )
    if not errors:
        return None
    return {
        "mean_err": float(np.mean(errors)),
        "best_err": float(np.min(errors)),
        "confirmed": int(sum(1 for e in errors if e < 15)),
        "n_pairs": len(errors),
        "pairs": pairs,
    }


# ─── Main experiment ─────────────────────────────────────────────────────────

def run_n_level(N, tau_phase_table):
    """Run the full SR test for a given N level."""
    print(f"\n{'='*60}")
    print(f"N={N} level")
    print(f"{'='*60}")

    t0 = time.time()

    # Background τ_c
    bg = measure_bg_tau(N, tau_phase_table, n_warmup=10, n_measure=10)
    print(f"  bg_τ_c = {bg:.4f}")

    # Hi-v seed search
    print(f"  Searching hi-v seeds (γ∈[1.3,2.0], 200 steps)...")
    hi_seeds = search_hi_v_seeds(N, tau_phase_table)
    print(f"  Found {len(hi_seeds)} hi-v seeds")
    for s, r in sorted(hi_seeds, key=lambda x: -x[1]["v_over_c"])[:3]:
        print(f"    {s}: γ={r['gamma']:.4f} ratio={r['ratio']:.4f}")

    # Lo-v seed search
    print(f"  Searching lo-v reference seeds (|v/c|<0.1)...")
    lo_seeds = search_lo_v_seeds(N, tau_phase_table)
    print(f"  Found {len(lo_seeds)} lo-v seeds")
    for s, r in lo_seeds:
        print(f"    {s}: γ={r['gamma']:.4f} ratio={r['ratio']:.4f}")

    # Paired SR test
    sr = None
    if hi_seeds and lo_seeds:
        sr = paired_sr_test(hi_seeds, lo_seeds, n_hi=5, n_lo=3)
        if sr:
            print(f"\n  SR test ({sr['n_pairs']} pairs):")
            print(f"    mean_err = {sr['mean_err']:.1f}%")
            print(f"    best_err = {sr['best_err']:.1f}%")
            print(f"    confirmed (<15%) = {sr['confirmed']}/{sr['n_pairs']}")
            for p in sr["pairs"][:3]:
                print(
                    f"    {p['hi']} vs {p['lo']}: "
                    f"paired={p['paired']:.4f} pred={p['pred']:.4f} err={p['err']:.1f}%"
                )

    elapsed = time.time() - t0
    print(f"  Elapsed: {elapsed:.1f}s")

    return {
        "N": N,
        "bg_tau_c": bg,
        "hi_seeds": [(s, r) for s, r in hi_seeds],
        "lo_seeds": [(s, r) for s, r in lo_seeds],
        "hi_seed_count": len(hi_seeds),
        "lo_seed_count": len(lo_seeds),
        "sr": sr,
    }


# ─── Entry point ─────────────────────────────────────────────────────────────

print("=" * 70)
print("Rank 51-NLD: N-Level FCA Depth SR Test (EPIC_072)")
print("=" * 70)

# Build phase tables
print("\nBuilding N=3 phase table...")
t0 = time.time()
phase_table_n3 = build_phase_table_n3()
print(f"  N=3 table built in {time.time()-t0:.2f}s")
print(f"  N=3 phase table:\n{phase_table_n3}")

print("\nBuilding N=4 phase table...")
t0 = time.time()
phase_table_n4 = build_phase_table_n4()
print(f"  N=4 table built in {time.time()-t0:.2f}s")
print(f"  N=4 phase table:\n{phase_table_n4}")

# Summary of LUTs
print("\nN-level τ_c tables:")
print(f"  N=2 LUT (direct): {tau_lut_n2.tolist()}")
print(f"  N=3 phase table (14×2):\n{phase_table_n3}")
print(f"  N=4 phase table (14×2):\n{phase_table_n4}")

# Run experiment for each N
results = {}
N_configs = [
    (2, None),
    (3, phase_table_n3),
    (4, phase_table_n4),
]

for N, tbl in N_configs:
    res = run_n_level(N, tbl)
    results[str(N)] = res

# ─── Print summary table ──────────────────────────────────────────────────────

print("\n" + "=" * 70)
print("=== N-Level FCA Depth SR Test (Rank 51-NLD) ===")
print("=" * 70)
print(
    f"\n{'N':>2} | {'bg_tau_c':>8} | {'hi_seeds':>8} | {'lo_seeds':>8} | "
    f"{'mean_err':>8} | {'best_err':>8} | {'confirmed':>10}"
)
print("-" * 70)

table_rows = {}
for N_str, res in sorted(results.items(), key=lambda x: int(x[0])):
    N = int(N_str)
    bg = res["bg_tau_c"]
    hi = res["hi_seed_count"]
    lo = res["lo_seed_count"]
    sr = res["sr"]
    if sr:
        me = f"{sr['mean_err']:.1f}%"
        be = f"{sr['best_err']:.1f}%"
        conf = f"{sr['confirmed']}/{sr['n_pairs']}"
    else:
        me = be = conf = "N/A"
    print(f"{N:>2} | {bg:>8.4f} | {hi:>8} | {lo:>8} | {me:>8} | {be:>8} | {conf:>10}")
    table_rows[N_str] = {
        "bg_tau_c": bg,
        "hi_seed_count": hi,
        "lo_seed_count": lo,
        "mean_err": sr["mean_err"] if sr else None,
        "best_err": sr["best_err"] if sr else None,
        "confirmed": sr["confirmed"] if sr else None,
        "n_pairs": sr["n_pairs"] if sr else None,
    }

# Hypothesis verdict
sr2 = results["2"]["sr"]
sr3 = results["3"]["sr"]
sr4 = results["4"]["sr"]

if sr2 and sr3 and sr4:
    err2 = sr2["mean_err"]
    err3 = sr3["mean_err"]
    err4 = sr4["mean_err"]
    # H1: monotone improvement
    if err3 < err2 - 1.0 and err4 < err3 - 1.0:
        verdict = "H1"
        verdict_desc = "depth improves SR accuracy (continuum limit)"
    # H3: flat / no improvement
    elif abs(err3 - err2) < 3.0 and abs(err4 - err2) < 3.0:
        verdict = "H3"
        verdict_desc = "depth-independent; M=7 N=2 already optimal"
    else:
        verdict = "MIXED"
        verdict_desc = "partial improvement or non-monotone"
else:
    verdict = "INCONCLUSIVE"
    verdict_desc = "insufficient seeds for one or more N levels"

print(f"\nHypothesis verdict: {verdict} ({verdict_desc})")
print(f"  N=2 mean_err: {sr2['mean_err']:.1f}%" if sr2 else "  N=2: no SR result")
print(f"  N=3 mean_err: {sr3['mean_err']:.1f}%" if sr3 else "  N=3: no SR result")
print(f"  N=4 mean_err: {sr4['mean_err']:.1f}%" if sr4 else "  N=4: no SR result")

# ─── Save JSON ────────────────────────────────────────────────────────────────

json_out = {
    "experiment": "Rank 51-NLD: N-Level FCA Depth SR Test",
    "epic": "EPIC_072",
    "date": "2026-05-21",
    "N_values": [2, 3, 4],
    "parameters": {
        "OUTER_L": OUTER_L,
        "M": M,
        "MAX_INNER": MAX_INNER,
        "C_EFF": C_EFF,
        "gamma_range": [1.3, 2.0],
        "n_seeds_searched": 1024,
        "n_steps_hi": 200,
        "n_steps_lo": 100,
        "min_stable_hi": 50,
        "min_stable_lo": 30,
        "n_hi_per_pair": 5,
        "n_lo_per_pair": 3,
    },
    "luts": {
        "N2": tau_lut_n2.tolist(),
        "N3": phase_table_n3.tolist(),
        "N4": phase_table_n4.tolist(),
    },
    "results": table_rows,
    "hypothesis": verdict,
    "key_finding": verdict_desc,
}

json_path = "rank51_nld_depth_results.json"
with open(json_path, "w") as f:
    json.dump(json_out, f, indent=2)
print(f"\nResults saved: {json_path}")

# ─── Plot ─────────────────────────────────────────────────────────────────────

fig, axes = plt.subplots(1, 2, figsize=(13, 5))

N_vals = [2, 3, 4]
bg_vals = [results[str(N)]["bg_tau_c"] for N in N_vals]
mean_errs = [
    results[str(N)]["sr"]["mean_err"] if results[str(N)]["sr"] else np.nan
    for N in N_vals
]
best_errs = [
    results[str(N)]["sr"]["best_err"] if results[str(N)]["sr"] else np.nan
    for N in N_vals
]
conf_rates = [
    results[str(N)]["sr"]["confirmed"] / results[str(N)]["sr"]["n_pairs"] * 100
    if results[str(N)]["sr"] and results[str(N)]["sr"]["n_pairs"] > 0
    else np.nan
    for N in N_vals
]

# Left panel: SR error vs N
ax = axes[0]
ax.plot(N_vals, mean_errs, "o-", color="steelblue", lw=2, ms=8, label="Mean error")
ax.plot(N_vals, best_errs, "s--", color="green", lw=1.5, ms=7, label="Best error")
ax.axhline(15.0, color="red", linestyle="--", alpha=0.7, label="15% threshold")
ax.set_xlabel("N (FCA depth)", fontsize=12)
ax.set_ylabel("SR error (%)", fontsize=12)
ax.set_title(f"SR Accuracy vs FCA Depth N (M={M} fixed)\nVerdict: {verdict}", fontsize=11)
ax.set_xticks(N_vals)
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)
if not all(np.isnan(mean_errs)):
    ymax = max([e for e in mean_errs + best_errs if not np.isnan(e)] + [20])
    ax.set_ylim(0, ymax + 2)

# Right panel: background τ_c vs N
ax = axes[1]
ax.plot(N_vals, bg_vals, "o-", color="darkorange", lw=2, ms=8)
ax.set_xlabel("N (FCA depth)", fontsize=12)
ax.set_ylabel("Background τ_c", fontsize=12)
ax.set_title(f"Background τ_c vs FCA Depth N\n(Pure ETHER14 tape, M={M})", fontsize=11)
ax.set_xticks(N_vals)
ax.grid(True, alpha=0.3)
for i, (n, bg) in enumerate(zip(N_vals, bg_vals)):
    ax.annotate(f"{bg:.4f}", (n, bg), textcoords="offset points",
                xytext=(5, 5), fontsize=9)

plt.tight_layout()
plot_path = "rank51_nld_sr_vs_N.png"
plt.savefig(plot_path, dpi=150, bbox_inches="tight")
plt.close()
print(f"Plot saved: {plot_path}")

print("\nRank 51-NLD complete.")
