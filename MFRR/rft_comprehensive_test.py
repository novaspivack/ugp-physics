#!/usr/bin/env python3
"""
Comprehensive test of Reflexive Fluctuation Theorem
Tests: (1) convergence with path length, (2) LDB violation effects
"""
import numpy as np
import matplotlib.pyplot as plt
import os, csv
from numpy.random import default_rng

rng = default_rng(12345)

def make_KU(N, density=1.0):
    W = rng.random((N, N))
    if density < 1.0:
        mask = rng.random((N,N)) < density
        W *= mask
        W = (W + W.T)/2
        W[np.diag_indices(N)] = 0.0
    W = (W + W.T)/2 + 1e-12
    KU = W / W.sum(axis=1, keepdims=True)
    pi = np.ones(N)/N
    return KU, pi

def make_KPT(F, adjacency=None):
    N = F.size
    if adjacency is None:
        A = np.ones((N,N), dtype=float)
        np.fill_diagonal(A, 0.0)
    else:
        A = adjacency.astype(float)
        np.fill_diagonal(A, 0.0)

    M = np.zeros((N,N), dtype=float)
    for y in range(N):
        num = A[y,:] * np.exp(0.5*(F - F[y]))
        s = num.sum()
        if s == 0:
            M[y,y] = 1.0
        else:
            M[y,:] = num / s
    return M

def perturb_LDB(KPT, eps):
    """Break LDB by exponentiating with power (1+eps)"""
    K = KPT**(1.0 + eps)
    K /= K.sum(axis=1, keepdims=True)
    return K

def sample_paths(KU, KPT, pi0, T=50, npaths=100_000):
    N = pi0.size
    cKU = np.cumsum(KU, axis=1)
    cKPT = np.cumsum(KPT, axis=1)
    cpi = np.cumsum(pi0)

    def draw_row(crow):
        r = rng.random()
        return int(np.searchsorted(crow, r, side='right'))

    dS_list = []
    for k in range(npaths):
        x0 = draw_row(cpi)
        x = x0
        for t in range(T):
            y = draw_row(cKU[x])
            x = draw_row(cKPT[y])
        dS_list.append((x0, x))
    return np.array(dS_list, dtype=int)

def run_test(N, T, npaths, F, eps_ldb=0.0, tag=""):
    """Run one test case"""
    KU, pi = make_KU(N, density=0.6)
    KPT = make_KPT(F)
    
    if eps_ldb != 0.0:
        KPT = perturb_LDB(KPT, eps_ldb)
    
    endpoints = sample_paths(KU, KPT, pi, T=T, npaths=npaths)
    dS = F[endpoints[:,1]] - F[endpoints[:,0]]
    est = np.mean(np.exp(-dS))
    mean_dS = np.mean(dS)
    std_dS = np.std(dS)
    
    return {
        "N": N, "T": T, "npaths": npaths, "eps_ldb": eps_ldb,
        "E[exp(-dS)]": est, "E[dS]": mean_dS, "Std[dS]": std_dS,
        "dS_data": dS, "tag": tag
    }

def main():
    outdir = "rft_outputs"
    os.makedirs(outdir, exist_ok=True)
    
    N = 64
    # Smooth potential
    base = rng.normal(0, 1, size=N)
    F = base.copy()
    for _ in range(5):
        F = 0.6*F + 0.2*np.roll(F,1) + 0.2*np.roll(F,-1)
    F *= 0.5
    
    # Test 1: Vary path length T
    print("Test 1: Path length dependence")
    results_T = []
    for T in [10, 50, 200]:
        print(f"  T={T}...")
        res = run_test(N, T, 100_000, F, eps_ldb=0.0, tag=f"T{T}")
        results_T.append(res)
        print(f"    <exp(-dS)> = {res['E[exp(-dS)]']:.4f}")
    
    # Test 2: Vary LDB violation
    print("\nTest 2: LDB violation")
    results_eps = []
    for eps in [0.0, 0.05, 0.10, 0.15]:
        print(f"  eps={eps}...")
        res = run_test(N, 50, 100_000, F, eps_ldb=eps, tag=f"eps{eps:.2f}")
        results_eps.append(res)
        print(f"    <exp(-dS)> = {res['E[exp(-dS)]']:.4f}")
    
    # Save comprehensive summary
    with open(os.path.join(outdir, "comprehensive_summary.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Test","N","T","npaths","eps_ldb","E[exp(-dS)]","E[dS]","Std[dS]"])
        for res in results_T:
            w.writerow(["T_var", res["N"], res["T"], res["npaths"], res["eps_ldb"],
                       res["E[exp(-dS)]"], res["E[dS]"], res["Std[dS]"]])
        for res in results_eps:
            w.writerow(["eps_var", res["N"], res["T"], res["npaths"], res["eps_ldb"],
                       res["E[exp(-dS)]"], res["E[dS]"], res["Std[dS]"]])
    
    # Plot 1: LDB identity vs path length
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
    Ts = [r["T"] for r in results_T]
    ests = [r["E[exp(-dS)]"] for r in results_T]
    ax1.plot(Ts, ests, 'o-', ms=8, lw=2)
    ax1.axhline(1.0, color='k', ls='--', lw=1)
    ax1.set_xlabel("Path length T")
    ax1.set_ylabel(r"$\langle e^{-\Delta S_{ref}}\rangle$")
    ax1.set_title("RFT identity vs path length")
    ax1.grid(alpha=0.3)
    
    # Plot 2: LDB violation effect
    epsilons = [r["eps_ldb"] for r in results_eps]
    ests_eps = [r["E[exp(-dS)]"] for r in results_eps]
    ax2.plot(epsilons, ests_eps, 's-', ms=8, lw=2, color='C1')
    ax2.axhline(1.0, color='k', ls='--', lw=1)
    ax2.set_xlabel(r"LDB violation $\epsilon$")
    ax2.set_ylabel(r"$\langle e^{-\Delta S_{ref}}\rangle$")
    ax2.set_title("RFT breakdown under LDB violation")
    ax2.grid(alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(outdir, "comprehensive_tests.png"), dpi=160)
    plt.close()
    
    # Plot 3: Histogram for best case (T=200)
    best = results_T[2]  # T=200
    plt.figure(figsize=(7,5))
    plt.hist(best["dS_data"], bins=100, density=True, alpha=0.7, color='C0')
    plt.xlabel(r"$\Delta S_{ref}$")
    plt.ylabel("Probability density")
    plt.title(f"RFT: N={N}, T={best['T']}, paths={best['npaths']}\n" +
              f"$\\langle e^{{-\\Delta S_{{ref}}}}\\rangle$ = {best['E[exp(-dS)]']:.4f}, " +
              f"$\\langle\\Delta S_{{ref}}\\rangle$ = {best['E[dS]']:.4f}")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(outdir, "hist_best.png"), dpi=160)
    plt.close()
    
    print(f"\n✓ All tests complete. Results in {outdir}/")
    print(f"\nSummary:")
    print(f"  T=10:  <exp(-dS)> = {results_T[0]['E[exp(-dS)]']:.4f}")
    print(f"  T=50:  <exp(-dS)> = {results_T[1]['E[exp(-dS)]']:.4f}")
    print(f"  T=200: <exp(-dS)> = {results_T[2]['E[exp(-dS)]']:.4f}")
    print(f"\n  eps=0.00: <exp(-dS)> = {results_eps[0]['E[exp(-dS)]']:.4f}")
    print(f"  eps=0.05: <exp(-dS)> = {results_eps[1]['E[exp(-dS)]']:.4f}")
    print(f"  eps=0.10: <exp(-dS)> = {results_eps[2]['E[exp(-dS)]']:.4f}")
    print(f"  eps=0.15: <exp(-dS)> = {results_eps[3]['E[exp(-dS)]']:.4f}")

if __name__ == "__main__":
    main()

