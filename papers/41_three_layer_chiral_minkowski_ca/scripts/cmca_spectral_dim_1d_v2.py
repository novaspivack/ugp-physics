"""
Spectral dimension of 1D CMCA causal graph — corrected (undirected walk).
Rank 074-SPECDIM-1D v2

Standard spectral dimension uses the UNDIRECTED graph Laplacian / heat kernel.
The directed (forward-only) walk measures d_s = 1 for Z² because it collapses
to 1D diffusion. This script uses bidirectional walks on the full spacetime.

Expected:
  A) Static undirected Z^2:          d_s ~ 2.0
  B) Non-vacuum R110 spacetime:      d_s ~ fractal_dim (likely 1.5-2.0)
  C) Non-vacuum undirected + CMCA:   same, but from CMCA 3-layer rule
"""

import numpy as np
import json, time, signal, sys

TIMEOUT_SECONDS = 300
def _t(s,f): print("TIMEOUT"); sys.exit(1)
signal.signal(signal.SIGALRM, _t); signal.alarm(TIMEOUT_SECONDS)

RNG = np.random.default_rng(42)

RULE110 = np.array([0,1,1,1,0,1,1,0], dtype=np.int8)
RULE124 = np.array([0,0,1,1,1,1,1,0], dtype=np.int8)

def step_rule(row, rule_lut):
    L = len(row)
    idx = (np.roll(row,1)*4 + row*2 + np.roll(row,-1)).astype(int)
    return rule_lut[idx]

def gen_spacetime(L, T, rule_lut, ic=None):
    sp = np.zeros((T, L), dtype=np.int8)
    if ic is None: sp[0, L//2] = 1
    else: sp[0] = ic
    for t in range(1, T): sp[t] = step_rule(sp[t-1], rule_lut)
    return sp


def fit_ds(return_prob, t_min=15, t_max_fit=100):
    ts = np.arange(len(return_prob))
    mask = (ts >= t_min) & (ts < t_max_fit) & (return_prob > 1e-9)
    if mask.sum() < 6: return None
    log_t = np.log(ts[mask])
    log_p = np.log(return_prob[mask])
    slope, _ = np.polyfit(log_t, log_p, 1)
    return float(-2 * slope)


def spectral_dim_undirected(spacetime, n_walks=3000, t_max=150):
    """
    Undirected random walk on the non-vacuum cells of a 2D spacetime array.
    At each step the walker can move to any of its 8 Moore-2D neighbors
    (both temporal directions) that are non-vacuum. Time wraps.
    """
    T, L = spacetime.shape
    return_counts = np.zeros(t_max, dtype=np.float64)
    valid = 0

    for _ in range(n_walks):
        # Find a non-vacuum starting cell
        nonvac = np.argwhere(spacetime == 1)
        if len(nonvac) == 0: continue
        idx = RNG.integers(len(nonvac))
        t0, x0 = int(nonvac[idx,0]), int(nonvac[idx,1])
        t, x = t0, x0
        valid += 1

        for step in range(t_max):
            # Undirected Moore-2D neighbors (dt in {-1,+1}, dx in {-1,0,+1})
            cands = []
            for dt in (-1, 1):
                for dx in (-1, 0, 1):
                    tn = (t + dt) % T
                    xn = (x + dx) % L
                    if spacetime[tn, xn] == 1:
                        cands.append((tn, xn))
            if cands:
                pick = RNG.integers(len(cands))
                t, x = cands[pick]
            if t == t0 and x == x0:
                return_counts[step] += 1

    if valid == 0: return np.zeros(t_max), 0
    return return_counts / valid, valid


# ── A: static undirected Z^2 (calibration, expected d_s=2) ────────────────────
print("A) Static undirected Z^2 (calibration, expected d_s~2.0)...")
# Build a uniform 1x1 grid spacetime (all cells = 1) and use undirected walk
T, L = 200, 200
uniform_sp = np.ones((T, L), dtype=np.int8)
rp_uniform, v = spectral_dim_undirected(uniform_sp, n_walks=2000, t_max=130)
ds_uniform = fit_ds(rp_uniform, t_min=15, t_max_fit=90)
print(f"   d_s (uniform Z^2 undirected) = {ds_uniform:.3f}  [expected ~2.0]")

# ── B: R110 single-seed (fractal pattern) ─────────────────────────────────────
print("B) R110 single-seed spacetime (fractal Sierpinski)...")
sp_r110_single = gen_spacetime(400, 400, RULE110)
rp_r110_s, v = spectral_dim_undirected(sp_r110_single, n_walks=2000, t_max=130)
ds_r110_s = fit_ds(rp_r110_s, t_min=15, t_max_fit=90)
print(f"   d_s (R110 single-seed) = {ds_r110_s:.3f}")

# ── C: R110 random IC (complex aperiodic pattern) ─────────────────────────────
print("C) R110 random-IC spacetime (complex aperiodic pattern)...")
ic_rand = (RNG.random(400) < 0.3).astype(np.int8)
sp_r110_rand = gen_spacetime(400, 400, RULE110, ic_rand)
rp_r110_r, v = spectral_dim_undirected(sp_r110_rand, n_walks=2000, t_max=130)
ds_r110_r = fit_ds(rp_r110_r, t_min=15, t_max_fit=90)
print(f"   d_s (R110 random IC)   = {ds_r110_r:.3f}")

# ── D: CMCA two-layer (R110 + R124 interleaved) ───────────────────────────────
print("D) CMCA two-layer (R110 + R124 interleaved) spacetime...")
sp_cmca = np.zeros((400, 400), dtype=np.int8)
sp_cmca[0, 200] = 1
for t in range(1, 400):
    rule = RULE110 if t % 2 == 0 else RULE124
    sp_cmca[t] = step_rule(sp_cmca[t-1], rule)
rp_cmca, v = spectral_dim_undirected(sp_cmca, n_walks=2000, t_max=130)
ds_cmca = fit_ds(rp_cmca, t_min=15, t_max_fit=90)
print(f"   d_s (CMCA two-layer)   = {ds_cmca:.3f}")

elapsed = 0  # not measuring total here

print("\n── Summary ──────────────────────────────────────────────────────────────")
rows = [
    ("uniform Z^2 (calibration)", ds_uniform, "~2.0 expected"),
    ("R110 single-seed (Sierpinski)", ds_r110_s, "fractal — below 2?"),
    ("R110 random IC (aperiodic)", ds_r110_r, "complex — near 2?"),
    ("CMCA two-layer R110+R124", ds_cmca, "key question: does chiral pair lift d_s?"),
]
for name, ds, note in rows:
    if ds is None: print(f"  {name:45s}: d_s = None  [{note}]")
    else:
        flag = ("★ d_s~4 CANDIDATE" if abs(ds-4)<0.6
                else "d_s~2 (expected)" if abs(ds-2)<0.4
                else f"d_s~{ds:.2f}")
        print(f"  {name:45s}: d_s = {ds:.3f}  [{flag}]  ({note})")

out = {'uniform_z2': ds_uniform, 'r110_single': ds_r110_s,
       'r110_random': ds_r110_r, 'cmca_two_layer': ds_cmca}
with open('papers/41_three_layer_chiral_minkowski_ca/scripts/cmca_spectral_dim_1d_v2_results.json','w') as f:
    json.dump(out, f, indent=2)
print("\nSaved: cmca_spectral_dim_1d_v2_results.json")
signal.alarm(0)
