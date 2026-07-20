#!/usr/bin/env python3
"""
Inline entropy-attractor analysis on real GTE trajectories.
Runs in about 3 minutes for all 24 trajectories (50K steps each).
Replaces the hanging experiment runner for this compute-intensive analysis.
"""
import math, random, numpy as np, json
from pathlib import Path
from collections import Counter, defaultdict
try:
    from scipy import stats as st
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

N_BINS = 16
N_SHUFFLE = 20
BATCH_SIZE = 500  # use a rolling window for efficiency


def entropy_series_rolling(states, window=500):
    """
    Compute entropy at each step using a ROLLING window (not cumulative).
    This is more physically meaningful and much faster for 50K steps.
    """
    H = []
    for t in range(len(states)):
        lo = max(0, t - window)
        seg = states[lo:t+1]
        cnt = Counter(seg)
        total = len(seg)
        h = -sum((c/total)*math.log2(c/total) for c in cnt.values() if c > 0)
        H.append(h)
    return H


def entropy_series_cumulative_fast(states):
    """Faster cumulative entropy using running counter."""
    H = []
    cnt = Counter()
    for t, s in enumerate(states):
        cnt[s] += 1
        total = t + 1
        h = -sum((c/total)*math.log2(c/total) for c in cnt.values() if c > 0)
        H.append(h)
    return H


def coarse_grain(evo):
    states = []
    for e in evo:
        try:
            b = abs(int(e["b"])); c = abs(int(e["c"]))
            lb = math.log(b+1); lc = math.log(c+1)
            states.append((int(lb*N_BINS/10) % N_BINS, int(lc*N_BINS/10) % N_BINS))
        except:
            pass
    return states


def attractor_convergence_step(states, window=200):
    """Find first step where the dominant macro-state has >70% share in window."""
    from collections import Counter as C
    mode = Counter(states).most_common(1)[0][0]
    for t in range(window, len(states)):
        frac = states[t-window:t].count(mode) / window
        if frac >= 0.70:
            return t - window
    return None


f = Path("UGP_discovery_lab_runs/exp_20260413_deep_trajectories/results/reports/experiment_results.json")
d = json.loads(f.read_text())["data"]
results_list = [r for r in d["results"] if r.get("success")]

print(f"Processing {len(results_list)} trajectories, 50K steps each...")

all_results = []
tol = 1e-9

for idx, r in enumerate(results_list):
    basin = r["basin"]
    seed = r["seed"]
    evo = r["evolution_history"]
    
    states = coarse_grain(evo)
    
    # Cumulative entropy
    H = entropy_series_cumulative_fast(states)
    
    viols = sum(1 for i in range(1, len(H)) if H[i] < H[i-1] - tol)
    peak_idx = int(np.argmax(H))
    peak_val = H[peak_idx]
    post = H[peak_idx:]
    slope = float(np.polyfit(range(len(post)), post, 1)[0]) if len(post) > 10 else 0
    
    # Shuffled null
    shuf_viols = []
    for _ in range(N_SHUFFLE):
        shuf = states.copy(); random.shuffle(shuf)
        Hs = entropy_series_cumulative_fast(shuf)
        sv = sum(1 for i in range(1, len(Hs)) if Hs[i] < Hs[i-1] - tol)
        shuf_viols.append(sv)
    
    conv = attractor_convergence_step(states)
    
    res = {
        "seed": seed, "basin": basin,
        "n_steps": len(H), "n_unique_states": len(set(states)),
        "n_violations_real": viols, "violation_rate_real": viols/len(H),
        "n_violations_shuf_mean": float(np.mean(shuf_viols)),
        "violation_rate_shuf": float(np.mean(shuf_viols))/len(H),
        "peak_idx": peak_idx, "peak_entropy": peak_val,
        "post_peak_slope": slope, "slope_negative": slope < -1e-7,
        "attractor_conv_step": conv,
    }
    all_results.append(res)
    print(f"[{idx+1}/{len(results_list)}] basin={basin} seed={seed[:3]}: "
          f"viols={viols}/{len(H)}({100*viols/len(H):.1f}%), "
          f"slope={slope:.5f}, shuf_viols_mean={np.mean(shuf_viols):.1f}, "
          f"conv_step={conv}", flush=True)

print("\n" + "="*65)
print("ENTROPY-ATTRACTOR SUMMARY")
print("="*65)

n = len(all_results)
neg_slope = sum(1 for x in all_results if x["slope_negative"])
real_rates = [x["violation_rate_real"] for x in all_results]
shuf_rates = [x["violation_rate_shuf"] for x in all_results]

print(f"Trajectories: {n}")
print(f"Post-peak entropy collapse (slope<0): {neg_slope}/{n} = {100*neg_slope/n:.1f}%")
print(f"Mean violation rate (real): {np.mean(real_rates):.4f} ({100*np.mean(real_rates):.1f}%)")
print(f"Mean violation rate (shuffled): {np.mean(shuf_rates):.4f} ({100*np.mean(shuf_rates):.1f}%)")
print(f"Ratio real/shuffled: {np.mean(real_rates)/max(np.mean(shuf_rates),1e-9):.1f}x")

if HAS_SCIPY:
    conv_steps = [x["attractor_conv_step"] for x in all_results if x["attractor_conv_step"] is not None]
    peak_steps = [x["peak_idx"] for x in all_results if x.get("attractor_conv_step") is not None]
    if len(conv_steps) > 3:
        r_val, p_val = st.pearsonr(conv_steps, peak_steps)
        print(f"Attractor convergence ↔ entropy peak: r={r_val:.4f}, p={p_val:.2e}")

# Save JSON
out = {
    "n_trajectories": n, "negative_slope_pct": 100*neg_slope/n,
    "mean_violation_rate_real": float(np.mean(real_rates)),
    "mean_violation_rate_shuffled": float(np.mean(shuf_rates)),
    "per_trajectory": all_results,
}
out_path = Path("results/reports/gte_entropy_attractor_inline_summary.json")
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(out, indent=2))
print(f"\nSaved to {out_path}")
