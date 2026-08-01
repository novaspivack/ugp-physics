#!/usr/bin/env python3
"""
E26: Long-Range Self-Organization & Hysteresis (Multiprocessing)

Validates:
- Thm. LR-order: Correlation length ξ diverges near threshold
- Prop. hysteresis: Memory-dependent hysteresis loops

Uses 2D lattice, sparse couplings, multiprocessing for parallel tau sweeps.
"""

import numpy as np
from numpy.random import default_rng
from scipy.sparse import csr_matrix, lil_matrix
from scipy.sparse.linalg import eigsh
import json
from pathlib import Path
from multiprocessing import Pool, cpu_count
from dataclasses import dataclass, asdict
import time

@dataclass
class SimParams:
    L: int = 40  # Lattice size (40x40 = 1600 sites)
    J_base: float = 0.06
    jitter: float = 0.05
    steps_eq: int = 150
    steps_meas: int = 100
    dt: float = 1.0
    tau_J: float = 20.0
    mem_gain: float = 0.6
    sweep_vals: int = 12
    seed: int = 12345

def build_lattice_adjacency(L):
    """2D square lattice with periodic BC."""
    N = L * L
    A = lil_matrix((N, N), dtype=np.float64)
    
    def idx(i, j):
        return (i % L) * L + (j % L)
    
    for i in range(L):
        for j in range(L):
            u = idx(i, j)
            neighbors = [idx(i+1,j), idx(i-1,j), idx(i,j+1), idx(i,j-1)]
            for v in neighbors:
                A[u, v] = 1.0
    
    return A.tocsr()

def init_couplings(A, J_base, jitter, seed):
    """Weighted coupling matrix from adjacency."""
    rng = default_rng(seed)
    N = A.shape[0]
    deg = np.maximum(A.sum(axis=1).A.ravel(), 1.0)
    W = lil_matrix(A.shape, dtype=np.float64)
    rows, cols = A.nonzero()
    
    for i, j in zip(rows, cols):
        if i < j:
            sigma = J_base / np.sqrt(0.5 * (deg[i] + deg[j]))
            wij = (1.0 + rng.normal(0.0, jitter)) * sigma
            W[i, j] = wij
            W[j, i] = wij
    
    return W.tocsr()

def spectral_norm(W):
    """Approximate ||W||_2."""
    try:
        vals = eigsh(W, k=1, which="LM", return_eigenvectors=False)
        return float(np.abs(vals[0]))
    except:
        return 0.0

def best_response_step(b, W_scaled, mem_field, seed_offset):
    """Asynchronous best-response with memory."""
    rng = default_rng(seed_offset)
    N = len(b)
    idxs = rng.permutation(N)
    b_new = b.copy()
    
    for i in idxs:
        h = W_scaled[i, :].dot(b_new) + mem_field[i]
        b_new[i] = 1 if h >= 0 else -1
    
    return b_new

def update_memory(mem_field, b, dt, tau_J, gain):
    """Exponential memory update."""
    if tau_J <= 0:
        return np.zeros_like(mem_field)
    alpha = dt / tau_J
    return (1 - alpha) * mem_field + alpha * (gain * b)

def coords_2d(L):
    """2D lattice coordinates."""
    xs, ys = np.meshgrid(np.arange(L), np.arange(L), indexing='ij')
    return np.stack([xs.ravel(), ys.ravel()], axis=1)

def radial_correlation(b, L, max_r=None, n_bins=15):
    """Compute radial correlation function C(r)."""
    if max_r is None:
        max_r = L // 2
    
    coords = coords_2d(L)
    mean_b = b.mean()
    
    # Minimal image distances on torus
    diffs = coords[:, None, :] - coords[None, :, :]
    diffs = (diffs + L/2) % L - L/2
    dists = np.sqrt((diffs[..., 0]**2 + diffs[..., 1]**2))
    
    # Correlations
    bb = np.outer(b, b)
    corr = bb - mean_b**2
    
    # Radial bins
    r_edges = np.linspace(0, max_r, n_bins + 1)
    r_centers = 0.5 * (r_edges[:-1] + r_edges[1:])
    C_r = np.zeros_like(r_centers)
    
    for k in range(n_bins):
        mask = (dists >= r_edges[k]) & (dists < r_edges[k+1])
        if np.any(mask):
            C_r[k] = corr[mask].mean()
        else:
            C_r[k] = np.nan
    
    return r_centers, C_r

def fit_xi(r, C_r):
    """Fit correlation length from C(r) ~ exp(-r/ξ)."""
    valid = (~np.isnan(C_r)) & (C_r > 1e-12)
    if np.sum(valid) < 3:
        return np.nan
    
    r_v = r[valid]
    C_v = C_r[valid]
    
    # Mid-range fit
    i0 = len(r_v) // 4
    i1 = 3 * len(r_v) // 4
    if i1 <= i0 + 2:
        i0, i1 = 0, len(r_v)
    
    r_fit = r_v[i0:i1]
    C_fit = C_v[i0:i1]
    
    if len(r_fit) < 3:
        return np.nan
    
    # log C ~ -r/xi + const
    y = np.log(C_fit)
    slope = np.polyfit(r_fit, y, 1)[0]
    
    if slope >= 0:
        return np.nan
    
    return -1.0 / slope

def equilibrate_and_measure(L, W, s, params, seed_offset):
    """Equilibrate at coupling s, measure m and ξ."""
    rng = default_rng(params.seed + seed_offset)
    N = L * L
    
    b = rng.choice([-1, 1], size=N)
    mem = np.zeros(N, dtype=float)
    W_scaled = (s * W).tocsr()
    
    # Equilibrate
    for step in range(params.steps_eq):
        mem = update_memory(mem, b, params.dt, params.tau_J, params.mem_gain)
        b = best_response_step(b, W_scaled, mem, params.seed + seed_offset + step)
    
    # Measure
    ms = []
    xis = []
    
    for step in range(params.steps_meas):
        mem = update_memory(mem, b, params.dt, params.tau_J, params.mem_gain)
        b = best_response_step(b, W_scaled, mem, params.seed + seed_offset + params.steps_eq + step)
        ms.append(b.mean())
        
        if step % 10 == 0:
            r, C_r = radial_correlation(b, L, max_r=L//2, n_bins=15)
            xi = fit_xi(r, C_r)
            xis.append(xi)
    
    m_avg = float(np.mean(ms))
    xi_avg = float(np.nanmean(xis)) if len(xis) > 0 else np.nan
    
    return m_avg, xi_avg

def run_tau_sweep(params_tau_tuple):
    """Run full sweep for one tau value (for multiprocessing)."""
    params, tau, sweep_type = params_tau_tuple
    params.tau_J = tau
    
    rng = default_rng(params.seed)
    
    print(f"[τ={tau:.1f}] Building lattice L={params.L}...", flush=True)
    A = build_lattice_adjacency(params.L)
    W = init_couplings(A, params.J_base, params.jitter, params.seed)
    normW = spectral_norm(W)
    
    # Sweep values
    s_vals = np.linspace(0.2, 2.0, params.sweep_vals)
    if sweep_type == "down":
        s_vals = s_vals[::-1]
    
    print(f"[τ={tau:.1f}] Running {sweep_type} sweep (||W||_2={normW:.4f})...", flush=True)
    
    m_list = []
    xi_list = []
    
    for idx, s in enumerate(s_vals):
        m, xi = equilibrate_and_measure(params.L, W, s, params, idx * 1000)
        m_list.append(m)
        xi_list.append(xi)
        
        if idx % 3 == 0:
            print(f"[τ={tau:.1f}] {sweep_type} s={s:.3f}: m={m:.4f}, ξ={xi:.2f}", flush=True)
    
    return {
        "tau": float(tau),
        "sweep_type": sweep_type,
        "s_vals": s_vals.tolist(),
        "m_vals": m_list,
        "xi_vals": xi_list,
        "normW_base": float(normW)
    }

def compute_hysteresis_area(s_up, m_up, s_dn, m_dn):
    """Compute hysteresis loop area via shoelace formula."""
    # Align down sweep
    s_dn_rev = s_dn[::-1]
    m_dn_rev = m_dn[::-1]
    
    s_poly = np.concatenate([s_up, s_dn_rev])
    m_poly = np.concatenate([m_up, m_dn_rev])
    
    area = 0.5 * np.abs(np.dot(s_poly, np.roll(m_poly, -1)) - 
                        np.dot(m_poly, np.roll(s_poly, -1)))
    return area

if __name__ == "__main__":
    print("=" * 70)
    print("E26: Long-Range Self-Organization & Hysteresis (Multiprocessing)")
    print("=" * 70)
    
    params = SimParams(L=40, J_base=0.06, sweep_vals=12, 
                       steps_eq=150, steps_meas=100)
    
    tau_list = [5.0, 20.0, 80.0]
    
    # Create parameter sets: (params, tau, sweep_type) for up and down
    param_sets = []
    for tau in tau_list:
        param_sets.append((params, tau, "up"))
        param_sets.append((params, tau, "down"))
    
    n_cores = min(cpu_count(), len(param_sets))
    print(f"\nUsing {n_cores} cores for {len(param_sets)} sweeps")
    print(f"L={params.L}x{params.L}, sweep_vals={params.sweep_vals}\n")
    
    start_time = time.time()
    
    with Pool(n_cores) as pool:
        results_list = pool.map(run_tau_sweep, param_sets)
    
    elapsed = time.time() - start_time
    print(f"\n✓ All sweeps complete in {elapsed:.1f}s")
    
    # Organize results
    results_by_tau = {}
    for r in results_list:
        tau = r['tau']
        sweep = r['sweep_type']
        if tau not in results_by_tau:
            results_by_tau[tau] = {}
        results_by_tau[tau][sweep] = r
    
    # Compute hysteresis areas
    hysteresis_areas = {}
    for tau, sweeps in results_by_tau.items():
        if 'up' in sweeps and 'down' in sweeps:
            area = compute_hysteresis_area(
                np.array(sweeps['up']['s_vals']),
                np.array(sweeps['up']['m_vals']),
                np.array(sweeps['down']['s_vals']),
                np.array(sweeps['down']['m_vals'])
            )
            hysteresis_areas[tau] = float(area)
            print(f"τ={tau}: Hysteresis area = {area:.6f}")
    
    # Save results
    output_dir = Path("e26_lr_outputs")
    output_dir.mkdir(exist_ok=True)
    
    output_data = {
        "params": asdict(params),
        "tau_list": tau_list,
        "sweeps": results_by_tau,
        "hysteresis_areas": hysteresis_areas,
        "elapsed_time": elapsed
    }
    
    output_file = output_dir / "e26_lr_results.json"
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n✓ Results saved to {output_file}")
    print("\nNext: Run e26_lr_plots.py to generate figures")

