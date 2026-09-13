#!/usr/bin/env python3
"""
UV spectral dimension of the 3+1D CMCA causal graph.
Computes d_s(sigma) = -2 * d log P(sigma) / d log sigma for small sigma.
CDT prediction: d_s(UV) -> 2, d_s(IR) -> 4.

Method: Full eigenvalue decomposition on a small graph, then Laplacian eigenvalue
        method on larger graphs with stochastic trace estimation for UV.

Key insight (from first run): partial eigsh with k << N cannot capture UV regime
because UV heat kernel requires ALL eigenvalues. Solution:
  (A) Compute ALL eigenvalues for small graph (L=8, T=4 -> 2048 nodes) -> full d_s curve
  (B) Stochastic trace estimation on larger graph for verification

Wall-clock timeout: 270 seconds.
"""

import json
import signal
import sys
import time

import numpy as np
from scipy import sparse
from scipy.linalg import eigh  # dense solver for small graphs — gets ALL eigenvalues
from scipy.sparse.linalg import eigsh

TIMEOUT = 270


def _timeout(s, f):
    print(f"\nTIMEOUT {TIMEOUT}s reached. Saving partial results.")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT)

t_start = time.time()

# ============================================================
# Helper: build 3+1D CMCA causal graph Laplacian
# ============================================================

def build_cmca_laplacian(L, T_time):
    """
    Build the normalized graph Laplacian for the 3+1D CMCA causal graph.
    Nodes: (t, x, y, z) for t in [0,T_time), x,y,z in [0,L).
    Edges (undirected, for symmetric Laplacian):
      - Spatial: 6-neighbor von Neumann (periodic BC), weight 1
      - Temporal: vertical links (t,xyz) <-> (t+1,xyz), weight 1
    This matches the P36 spectral_dimension_3d_fmdl.py construction.
    """
    N_spatial = L ** 3
    N_nodes = N_spatial * T_time

    def node_id(t, x, y, z):
        return t * N_spatial + (x % L) * L * L + (y % L) * L + (z % L)

    rows_list, cols_list = [], []
    for t in range(T_time):
        for x in range(L):
            for y in range(L):
                for z in range(L):
                    n = node_id(t, x, y, z)
                    # Spatial von Neumann neighbors (deduplicate: only +direction)
                    for dx, dy, dz in [(1, 0, 0), (0, 1, 0), (0, 0, 1)]:
                        m = node_id(t, x + dx, y + dy, z + dz)
                        rows_list.append(n); cols_list.append(m)
                        rows_list.append(m); cols_list.append(n)
                    # Temporal link
                    if t + 1 < T_time:
                        m = node_id(t + 1, x, y, z)
                        rows_list.append(n); cols_list.append(m)
                        rows_list.append(m); cols_list.append(n)

    data = np.ones(len(rows_list), dtype=np.float64)
    A = sparse.csr_matrix(
        (data, (rows_list, cols_list)), shape=(N_nodes, N_nodes)
    )
    A = (A + A.T) / 2
    A.data = np.clip(A.data, 0, 1)

    degrees = np.array(A.sum(axis=1)).flatten()
    D_inv_sqrt = sparse.diags(1.0 / np.sqrt(np.maximum(degrees, 1e-10)))
    L_norm = sparse.eye(N_nodes) - D_inv_sqrt @ A @ D_inv_sqrt
    return L_norm, N_nodes


def compute_spectral_dimension(eigvals_nontrivial, N_nodes, sigma_range=None, label=""):
    """
    Given non-trivial Laplacian eigenvalues (zeros removed), compute d_s(sigma).
    Heat kernel: K(sigma) = (1 + sum_i exp(-lambda_i * sigma)) / N_nodes
    (the trivial zero mode contributes 1.0)
    Spectral dim: d_s(sigma) = -2 * d log K / d log sigma
    """
    if sigma_range is None:
        sigma_range = np.logspace(-3, 2, 80)

    K_vals = []
    for sig in sigma_range:
        K = (1.0 + float(np.sum(np.exp(-eigvals_nontrivial * sig)))) / N_nodes
        K_vals.append(K)

    log_t = np.log(sigma_range)
    log_K = np.log(np.maximum(K_vals, 1e-300))

    d_s_vals, t_mid = [], []
    for i in range(1, len(sigma_range) - 1):
        dlogK_dlogt = (log_K[i + 1] - log_K[i - 1]) / (log_t[i + 1] - log_t[i - 1])
        d_s = -2.0 * dlogK_dlogt
        d_s_vals.append(float(d_s))
        t_mid.append(float(sigma_range[i]))

    d_s_arr = np.array(d_s_vals)
    t_arr = np.array(t_mid)

    uv_mask = t_arr < 0.05
    ir_mask = t_arr > 5.0
    mid_mask = (t_arr >= 0.05) & (t_arr <= 5.0)

    d_s_uv = float(np.mean(d_s_arr[uv_mask])) if np.sum(uv_mask) > 0 else None
    d_s_mid = float(np.mean(d_s_arr[mid_mask])) if np.sum(mid_mask) > 0 else None
    d_s_ir = float(np.mean(d_s_arr[ir_mask])) if np.sum(ir_mask) > 0 else None

    if label:
        print(f"  [{label}] UV (sigma<0.05): d_s = {d_s_uv}")
        print(f"  [{label}] Mid (0.05-5.0):  d_s = {d_s_mid}")
        print(f"  [{label}] IR (sigma>5.0):   d_s = {d_s_ir}")

    return {
        "sigma_vals": [float(v) for v in sigma_range],
        "K_vals": [float(v) for v in K_vals],
        "d_s_vals": d_s_vals,
        "t_mid": t_mid,
        "d_s_uv": d_s_uv,
        "d_s_mid": d_s_mid,
        "d_s_ir": d_s_ir,
        "n_uv_pts": int(np.sum(uv_mask)),
        "n_ir_pts": int(np.sum(ir_mask)),
    }


results = {}

# ============================================================
# APPROACH A: SMALL GRAPH — FULL EIGENVALUE SPECTRUM
# ============================================================
# L=8, T=4 gives 8^3*4 = 2048 nodes — all eigenvalues via dense eigh

L_small = 8
T_small = 4
N_small = L_small ** 3 * T_small

print("=" * 60)
print(f"APPROACH A: Full eigenspectrum, L={L_small}^3 x T={T_small} = {N_small} nodes")
print("=" * 60)

t1 = time.time()
L_norm_small, _ = build_cmca_laplacian(L_small, T_small)
# Convert to dense for full diagonalization
L_dense = L_norm_small.toarray()
print(f"Dense matrix built in {time.time()-t1:.1f}s. Diagonalizing...")
t2 = time.time()
eigvals_small_all = eigh(L_dense, eigvals_only=True)
print(f"All {len(eigvals_small_all)} eigenvalues computed in {time.time()-t2:.1f}s")

# Remove near-zero (trivial zero mode)
eigvals_small = eigvals_small_all[eigvals_small_all > 1e-8]
n_nontrivial = len(eigvals_small)
print(f"Non-trivial eigenvalues: {n_nontrivial}")
print(f"Eigenvalue range: [{eigvals_small.min():.4f}, {eigvals_small.max():.4f}]")

res_A = compute_spectral_dimension(eigvals_small, N_small, label=f"L={L_small} T={T_small}")
results["approach_A"] = {
    "L": L_small, "T": T_small, "N_nodes": N_small,
    "n_eigenvalues": n_nontrivial,
    "eigval_min": float(eigvals_small.min()),
    "eigval_max": float(eigvals_small.max()),
    **res_A,
}

# Summarize the running
print(f"\n--- APPROACH A SUMMARY ---")
print(f"UV d_s (sigma < 0.05):    {res_A['d_s_uv']:.4f}")
print(f"Mid d_s (0.05 < s < 5):   {res_A['d_s_mid']:.4f}")
print(f"IR d_s (sigma > 5.0):     {res_A['d_s_ir']:.4f}")
print(f"UV running detected (UV < IR): {res_A['d_s_uv'] is not None and res_A['d_s_ir'] is not None and res_A['d_s_uv'] < res_A['d_s_ir']}")
print()

# ============================================================
# APPROACH A2: Larger graph — probe IR convergence
# ============================================================
# L=12, T=4 gives 12^3*4 = 6912 nodes — still manageable with full eigh?
# Actually 6912x6912 dense matrix is ~380 MB float64. May be tight but try.

if time.time() - t_start < 60:
    L_med = 10
    T_med = 4
    N_med = L_med ** 3 * T_med

    print("=" * 60)
    print(f"APPROACH A2: Full eigenspectrum, L={L_med}^3 x T={T_med} = {N_med} nodes")
    print("=" * 60)

    t3 = time.time()
    L_norm_med, _ = build_cmca_laplacian(L_med, T_med)
    L_dense_med = L_norm_med.toarray()
    print(f"Dense matrix built in {time.time()-t3:.1f}s. Diagonalizing...")
    t4 = time.time()
    eigvals_med_all = eigh(L_dense_med, eigvals_only=True)
    print(f"All {len(eigvals_med_all)} eigenvalues in {time.time()-t4:.1f}s")
    eigvals_med = eigvals_med_all[eigvals_med_all > 1e-8]

    res_A2 = compute_spectral_dimension(eigvals_med, N_med, label=f"L={L_med} T={T_med}")
    results["approach_A2"] = {
        "L": L_med, "T": T_med, "N_nodes": N_med,
        "n_eigenvalues": len(eigvals_med),
        **res_A2,
    }
    print(f"\n--- APPROACH A2 SUMMARY ---")
    print(f"UV d_s (sigma < 0.05):    {res_A2['d_s_uv']:.4f}")
    print(f"Mid d_s (0.05 < s < 5):   {res_A2['d_s_mid']:.4f}")
    print(f"IR d_s (sigma > 5.0):     {res_A2['d_s_ir']:.4f}")
else:
    print("Skipping Approach A2 (time budget).")

# ============================================================
# APPROACH B: STOCHASTIC TRACE ESTIMATION (larger graph)
# ============================================================
# For larger graphs (L=16, T=4, N=16384), use Hutchinson stochastic estimator:
# Tr(exp(-sigma * L)) ≈ (1/M) * sum_{i=1}^{M} v_i^T exp(-sigma * L) v_i
# where v_i are random ±1 vectors and exp(-sigma * L) v is approximated via
# Lanczos polynomial method (Chebyshev expansion).
#
# Simpler version: Taylor expansion approach.
# exp(-sigma * L) * v ≈ sum_{k=0}^{K} (-sigma)^k / k! * L^k * v
# For small sigma (UV), need K large; for large sigma, fast decay.

if time.time() - t_start < 120:
    print()
    print("=" * 60)
    L_large = 16
    T_large = 4
    N_large = L_large ** 3 * T_large
    print(f"APPROACH B: Stochastic trace, L={L_large}^3 x T={T_large} = {N_large} nodes")
    print("=" * 60)

    L_norm_large, _ = build_cmca_laplacian(L_large, T_large)

    def stochastic_heat_kernel(L_op, N, sigma, n_vectors=30, K_poly=40):
        """
        Stochastic estimate of K(sigma) = Tr(exp(-sigma*L)) / N via Hutchinson.
        Uses degree-K Chebyshev polynomial approximation to exp(-sigma*lambda).
        L_op must have eigenvalues in [0, lambda_max].
        """
        # Estimate lambda_max (largest eigenvalue of normalized Laplacian <= 2)
        lambda_max = 2.0
        # Scale L to [-1, 1]: L_scaled = 2*L/lambda_max - I
        # Then exp(-sigma*L) = exp(-sigma*lambda_max/2) * exp(-sigma*lambda_max/2 * (L_scaled+I))

        total = 0.0
        for _ in range(n_vectors):
            v = np.random.choice([-1.0, 1.0], size=N)
            # Compute exp(-sigma * L) * v via Taylor series
            # exp(-sigma*L)*v = v - sigma*L*v + (sigma^2/2)*L^2*v - ...
            result = v.copy()
            Lv = v.copy()
            coeff = 1.0
            for k in range(1, K_poly + 1):
                Lv = L_op.dot(Lv)
                coeff *= (-sigma) / k
                result = result + coeff * Lv
                if abs(coeff) < 1e-14:
                    break
            total += float(v.dot(result))
        return total / (n_vectors * N)

    sigma_vals_b = np.logspace(-2, 1.5, 40)
    K_vals_b = []
    n_vec_b = 20
    K_poly_b = 30

    print(f"  Stochastic estimator: {n_vec_b} random vectors, degree-{K_poly_b} Taylor")
    for sig in sigma_vals_b:
        K_est = stochastic_heat_kernel(L_norm_large, N_large, sig, n_vectors=n_vec_b, K_poly=K_poly_b)
        K_vals_b.append(float(K_est))

    log_t_b = np.log(sigma_vals_b)
    log_K_b = np.log(np.maximum(K_vals_b, 1e-12))
    d_s_vals_b, t_mid_b = [], []
    for i in range(1, len(sigma_vals_b) - 1):
        dlogK = (log_K_b[i+1] - log_K_b[i-1]) / (log_t_b[i+1] - log_t_b[i-1])
        d_s_b = -2.0 * dlogK
        d_s_vals_b.append(float(d_s_b))
        t_mid_b.append(float(sigma_vals_b[i]))
        if i <= 6 or i % 6 == 0:
            print(f"  sigma={sigma_vals_b[i]:.4f}: K={K_vals_b[i]:.4e}, d_s={d_s_b:.3f}")

    d_sb_arr = np.array(d_s_vals_b)
    t_b_arr = np.array(t_mid_b)
    uv_b = t_b_arr < 0.05
    ir_b = t_b_arr > 5.0

    d_s_uv_b = float(np.mean(d_sb_arr[uv_b])) if np.sum(uv_b) > 0 else None
    d_s_ir_b = float(np.mean(d_sb_arr[ir_b])) if np.sum(ir_b) > 0 else None

    print(f"\n--- APPROACH B SUMMARY ---")
    print(f"UV d_s (sigma < 0.05):    {d_s_uv_b}")
    print(f"IR d_s (sigma > 5.0):     {d_s_ir_b}")

    results["approach_B"] = {
        "L": L_large, "T": T_large, "N_nodes": N_large,
        "method": f"stochastic Taylor ({n_vec_b} vecs, deg {K_poly_b})",
        "sigma_vals": [float(v) for v in sigma_vals_b],
        "K_vals": K_vals_b,
        "d_s_vals": d_s_vals_b,
        "t_mid": t_mid_b,
        "d_s_uv": d_s_uv_b,
        "d_s_ir": d_s_ir_b,
    }
else:
    print("Skipping Approach B (time budget).")

signal.alarm(0)
results["elapsed_s"] = time.time() - t_start
print(f"\nTotal elapsed: {results['elapsed_s']:.1f}s")

out_path = "spectral_dimension_uv_cmca_results.json"
with open(out_path, "w") as f:
    json.dump(results, f, indent=2)
print(f"Saved to {out_path}")

# Summary
print("\n========== FINAL SUMMARY ==========")
for key in ["approach_A", "approach_A2", "approach_B"]:
    if key in results:
        r = results[key]
        uv_v = r.get("d_s_uv")
        ir_v = r.get("d_s_ir")
        mid_v = r.get("d_s_mid")
        print(f"{key} (L={r.get('L')}, T={r.get('T')}, N={r.get('N_nodes')}):")
        print(f"  UV d_s (sigma<0.05): {uv_v}")
        print(f"  Mid d_s (0.05-5):    {mid_v}")
        print(f"  IR d_s (sigma>5):    {ir_v}")
        if uv_v is not None and ir_v is not None:
            print(f"  Running UV->IR: {uv_v:.3f} -> {ir_v:.3f} (CDT: 2 -> 4)")
