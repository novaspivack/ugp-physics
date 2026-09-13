#!/usr/bin/env python3
"""
GSL parameter fit from real GTE trajectories — inline script.
Fits I_total = S × (1 + C × I_holo^p) to 24 real GTE trajectories.
"""
import math, numpy as np, json
from pathlib import Path
from collections import Counter, defaultdict
try:
    from scipy import stats as st
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

N_BINS = 16
C_GRID = [0.01, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0, 1.5, 2.0]
P_GRID = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0]
WINDOW = 50  # sliding window for entropy and MI


def coarse_single(a, b, c):
    try:
        lb = math.log(abs(int(b))+1); lc = math.log(abs(int(c))+1)
        return (int(lb*N_BINS/10) % N_BINS, int(lc*N_BINS/10) % N_BINS)
    except:
        return (0, 0)


def is_boundary(e):
    return e.get("step", 0) % 2 == 0  # ridge events on even steps


def mutual_info(xs, ys):
    if not xs: return 0.0
    n = len(xs)
    cx = Counter(xs); cy = Counter(ys); cxy = Counter(zip(xs, ys))
    mi = 0.0
    for (xi, yi), c in cxy.items():
        pxy = c/n; px = cx[xi]/n; py = cy[yi]/n
        if pxy > 0 and px > 0 and py > 0:
            mi += pxy * math.log2(pxy / (px * py))
    return max(0.0, mi)


def process_trajectory(evo):
    all_states = [coarse_single(e["a"], e["b"], e["c"]) for e in evo]
    b_states = [coarse_single(e["a"], e["b"], e["c"]) for e in evo if is_boundary(e)]
    k_states = [coarse_single(e["a"], e["b"], e["c"]) for e in evo if not is_boundary(e)]
    
    # Map boundary and bulk to aligned steps
    b_idx = [i for i, e in enumerate(evo) if is_boundary(e)]
    k_idx = [i for i, e in enumerate(evo) if not is_boundary(e)]
    
    min_len = min(len(b_idx), len(k_idx))
    if min_len < 50: return None
    
    S_series = []
    Ih_series = []
    cnt_all = Counter()
    
    for t in range(min_len):
        bi = b_idx[t]
        # Local entropy in window
        lo = max(0, t - WINDOW)
        seg = all_states[bi-WINDOW:bi+1] if bi >= WINDOW else all_states[:bi+1]
        if not seg: continue
        c_s = Counter(seg); tot = len(seg)
        S = -sum((c/tot)*math.log2(c/tot) for c in c_s.values() if c > 0)
        
        # MI between recent boundary and bulk states
        Bs = b_states[lo:t+1]
        Ks = k_states[lo:t+1]
        min_bk = min(len(Bs), len(Ks))
        Ih = mutual_info(Bs[:min_bk], Ks[:min_bk]) if min_bk > 3 else 0.0
        
        S_series.append(S); Ih_series.append(Ih)
    
    S_arr = np.array(S_series); Ih_arr = np.array(Ih_series)
    if S_arr.mean() == 0: return None
    
    cv_s = float(S_arr.std() / S_arr.mean())
    
    best_cv = float("inf"); best_C = 0; best_p = 1.0
    for C in C_GRID:
        for p in P_GRID:
            I_total = S_arr * (1 + C * (Ih_arr**p))
            if I_total.mean() > 0:
                cv = float(I_total.std() / I_total.mean())
                if cv < best_cv:
                    best_cv = cv; best_C = C; best_p = p
    
    imp = (cv_s - best_cv) / cv_s if cv_s > 0 else 0
    
    delta_S = np.diff(S_arr); delta_Ih = np.diff(Ih_arr)
    r_corr = p_corr = None
    if HAS_SCIPY and len(delta_S) > 5:
        try:
            r_corr, p_corr = st.pearsonr(delta_S, delta_Ih)
        except: pass
    
    return {
        "best_C": best_C, "best_p": best_p, "cv_best": best_cv,
        "cv_entropy_only": cv_s, "improvement": imp,
        "r_delta_S_Ih": float(r_corr) if r_corr is not None else None,
        "p_delta": float(p_corr) if p_corr is not None else None,
        "n_steps": len(S_arr),
    }


f = Path("UGP_discovery_lab_runs/exp_20260413_deep_trajectories/results/reports/experiment_results.json")
d = json.loads(f.read_text())["data"]
results_list = [r for r in d["results"] if r.get("success")]

print(f"Processing {len(results_list)} trajectories for GSL fit...")

all_fit = []
best_pair_counts = defaultdict(int)

for idx, r in enumerate(results_list):
    basin = r["basin"]; seed = r["seed"]
    evo = r["evolution_history"]
    fit = process_trajectory(evo)
    if fit is None: continue
    fit["basin"] = basin; fit["seed"] = seed
    all_fit.append(fit)
    best_pair_counts[(fit["best_C"], fit["best_p"])] += 1
    print(f"[{idx+1}/{len(results_list)}] basin={basin} seed={seed[:3]}: C={fit['best_C']}, p={fit['best_p']}, improvement={fit['improvement']:.1%}, r={fit['r_delta_S_Ih']}", flush=True)

print("\n" + "="*65)
print("GSL FIT SUMMARY")
print("="*65)
n = len(all_fit)
print(f"Trajectories fitted: {n}")
print("Best (C, p) distribution:")
for (C, p), cnt in sorted(best_pair_counts.items(), key=lambda x: -x[1])[:8]:
    print(f"  C={C}, p={p}: {cnt} trajectories ({100*cnt/n:.1f}%)")

imps = [x["improvement"] for x in all_fit]
print(f"Mean improvement over entropy-only: {np.mean(imps):.1%}")

corrs = [x["r_delta_S_Ih"] for x in all_fit if x["r_delta_S_Ih"] is not None]
if corrs:
    print(f"Mean ΔS vs ΔI_holo correlation: r={np.mean(corrs):.4f}")

modal_pair = max(best_pair_counts.items(), key=lambda x: x[1])
print(f"\nModal best parameters: C={modal_pair[0][0]}, p={modal_pair[0][1]} ({modal_pair[1]}/{n} trajectories)")

out = {
    "n_trajectories": n,
    "modal_C": modal_pair[0][0], "modal_p": modal_pair[0][1],
    "best_pair_distribution": {f"C{k[0]}_p{k[1]}": v for k, v in best_pair_counts.items()},
    "mean_improvement": float(np.mean(imps)),
    "mean_delta_S_Ih_r": float(np.mean(corrs)) if corrs else None,
    "trajectories": all_fit,
}
out_path = Path("results/reports/gte_gsl_fit_inline_summary.json")
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(out, indent=2))
print(f"\nSaved to {out_path}")
