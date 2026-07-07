#!/usr/bin/env python3
import numpy as np
import matplotlib.pyplot as plt
import os, csv
from numpy.random import default_rng

rng = default_rng(12345)

def make_KU(N, density=1.0):
    # symmetric weights -> detailed balance w.r.t uniform
    W = rng.random((N, N))
    if density < 1.0:
        mask = rng.random((N,N)) < density
        W *= mask
        W = (W + W.T)/2
        W[np.diag_indices(N)] = 0.0
    W = (W + W.T)/2 + 1e-12
    KU = W / W.sum(axis=1, keepdims=True)
    pi = np.ones(N)/N  # stationary for symmetric stochastic matrix
    return KU, pi

def make_KPT(F, adjacency=None):
    # logit K_PT(y->z) ∝ A(y,z) * exp(+0.5*(Fz - Fy))
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
            # fallback: self-loop if isolated
            M[y,y] = 1.0
        else:
            M[y,:] = num / s
    return M  # K_PT

def sample_paths(KU, KPT, pi0, T=50, npaths=100_000, outdir="rft_outputs"):
    os.makedirs(outdir, exist_ok=True)
    N = pi0.size
    # precompute cumulative rows
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
        # we track x_t, y_t, x_{t+1}; but ΔS_ref telescopes -> F(x_T)-F(x_0)
        # so we can compute endpoints only.
        for t in range(T):
            y = draw_row(cKU[x])
            x = draw_row(cKPT[y])
        # store endpoints for later F-difference (filled outside)
        dS_list.append((x0, x))
    return np.array(dS_list, dtype=int)

def main():
    outdir = "rft_outputs"
    os.makedirs(outdir, exist_ok=True)

    N = 64
    KU, pi = make_KU(N, density=0.6)

    # random smooth-ish potential F
    base = rng.normal(0, 1, size=N)
    # smooth by mixing with neighbors in a ring graph
    F = base.copy()
    for _ in range(5):
        F = 0.6*F + 0.2*np.roll(F,1) + 0.2*np.roll(F,-1)
    # scale strength
    F *= 0.5

    KPT = make_KPT(F)

    # simulate
    T = 50
    npaths = 100_000
    endpoints = sample_paths(KU, KPT, pi, T=T, npaths=npaths, outdir=outdir)

    # compute ΔS_ref = F(x_T) - F(x_0)
    dS = F[endpoints[:,1]] - F[endpoints[:,0]]
    est = np.mean(np.exp(-dS))
    mean = np.mean(dS)
    std = np.std(dS)

    # save summary
    with open(os.path.join(outdir, "summary.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["N","T","npaths","E[exp(-dS)]","E[dS]","Std[dS]"])
        w.writerow([N, T, npaths, est, mean, std])

    # plots
    plt.figure(figsize=(6,4))
    plt.hist(dS, bins=80, density=True)
    plt.xlabel(r"$\Delta S_{ref}$")
    plt.ylabel("density")
    plt.title(f"RFT: N={N}, T={T}, n={npaths}\n<exp(-dS)>={est:.4f}, <dS>={mean:.4f}")
    plt.tight_layout()
    plt.savefig(os.path.join(outdir, "hist_dS.png"), dpi=160)
    plt.close()

    # convergence of <exp(-dS)>
    # sub-sample means for chunks
    chunk = 2000
    nc = npaths//chunk
    vals = []
    for i in range(nc):
        seg = dS[i*chunk:(i+1)*chunk]
        vals.append(np.mean(np.exp(-seg)))
    xs = np.arange(nc)*chunk
    plt.figure(figsize=(6,4))
    plt.plot(xs, vals, marker='o', ms=2, lw=1)
    plt.axhline(1.0, color='k', ls='--', lw=1)
    plt.xlabel("samples used")
    plt.ylabel(r"estimate of $\langle e^{-\Delta S_{ref}}\rangle$")
    plt.title("Convergence to 1 (Jarzynski-type identity)")
    plt.tight_layout()
    plt.savefig(os.path.join(outdir, "convergence.png"), dpi=160)
    plt.close()

    print(f"Done. Summary in {outdir}/summary.csv; plots in {outdir}/")

if __name__ == "__main__":
    main()
