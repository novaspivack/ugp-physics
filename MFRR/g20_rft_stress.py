#!/usr/bin/env python3
import numpy as np, os, csv
import matplotlib.pyplot as plt
from numpy.random import default_rng
rng = default_rng(42)

def make_adj(N, kind="dense"):
    A = np.zeros((N,N), float)
    if kind=="dense":
        A[:] = 1.0
    elif kind=="ring":
        for i in range(N):
            A[i,(i-1)%N] = 1; A[i,(i+1)%N] = 1
    elif kind=="band3":
        for i in range(N):
            for d in [-2,-1,1,2]:
                A[i,(i+d)%N]=1
    np.fill_diagonal(A,0.0)
    return A

def make_KU(N, density=1.0):
    W = rng.random((N,N))
    if density<1.0:
        mask = rng.random((N,N)) < density
        W *= mask
    W = (W+W.T)/2 + 1e-12
    KU = W / W.sum(axis=1, keepdims=True)
    pi = np.ones(N)/N
    return KU, pi

def make_KPT(F, A, beta=1.0):
    N = len(F)
    K = np.zeros((N,N), float)
    for y in range(N):
        num = A[y,:]*np.exp(0.5*beta*(F - F[y]))
        s = num.sum()
        K[y,:] = num/s if s>0 else np.eye(N)[y]
    return K

def sample_paths(KU, KPT, pi, T, npaths=50000):
    N = len(pi)
    cKU = np.cumsum(KU, axis=1); cKPT = np.cumsum(KPT, axis=1); cpi = np.cumsum(pi)
    def draw_row(crow):
        r = rng.random(); return int(np.searchsorted(crow, r, side='right'))
    ends = np.empty((npaths,2), int)
    for k in range(npaths):
        x0 = draw_row(cpi); x = x0
        for t in range(T):
            y = draw_row(cKU[x]); x = draw_row(cKPT[y])
        ends[k,0]=x0; ends[k,1]=x
    return ends

def main():
    outdir="g20_rft_outputs"; os.makedirs(outdir, exist_ok=True)
    rows = []
    Ns = [32, 64, 128]
    Ts = [10, 50, 200]
    kinds = ["dense","ring","band3"]
    betas = [0.5, 1.0, 2.0]
    for N in Ns:
        for kind in kinds:
            A = make_adj(N, kind)
            KU, pi = make_KU(N, density=0.6 if kind!="dense" else 1.0)
            # smooth random potential
            F = rng.normal(0,1,size=N); 
            for _ in range(5): F = 0.6*F + 0.2*np.roll(F,1)+0.2*np.roll(F,-1)
            F *= 0.5
            for beta in betas:
                KPT = make_KPT(F, A, beta=beta)
                for T in Ts:
                    ends = sample_paths(KU, KPT, pi, T, npaths=100_000)
                    dS = F[ends[:,1]] - F[ends[:,0]]
                    est = np.mean(np.exp(-dS))
                    mean = float(np.mean(dS))
                    rows.append([N,kind,beta,T,est,mean])
    with open(os.path.join(outdir,"summary.csv"),"w",newline="") as f:
        w=csv.writer(f); w.writerow(["N","adj","beta","T","Eexp(-dS)","E[dS]"])
        w.writerows(rows)
    # quick panel: Eexp(-dS) vs T for each N at beta=1 & ring
    plot = []
    for N in Ns:
        filt = [(r[0]==N and r[1]=="ring" and abs(r[2]-1.0)<1e-9) for r in rows]
        Tvals = [rows[i][3] for i,b in enumerate(filt) if b]
        ests  = [rows[i][4] for i,b in enumerate(filt) if b]
        plot.append((N, Tvals, ests))
    plt.figure(figsize=(6,4))
    for N,Tvals,ests in plot:
        idx = np.argsort(Tvals); Tvals=np.array(Tvals)[idx]; ests=np.array(ests)[idx]
        plt.plot(Tvals, ests, marker='o', label=f"N={N}")
    plt.axhline(1.0, color='k', ls='--', lw=1)
    plt.xlabel("T"); plt.ylabel(r"$\langle e^{-\Delta \mathcal S_{\rm ref}}\rangle$")
    plt.title("RFT finite-size/length convergence (ring, β=1)")
    plt.legend(); plt.tight_layout()
    plt.savefig(os.path.join(outdir,"panel_convergence.png"), dpi=160); plt.close()
    print("G20: wrote g20_rft_outputs/summary.csv and panel_convergence.png")

if __name__=="__main__":
    main()
