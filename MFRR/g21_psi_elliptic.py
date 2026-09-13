#!/usr/bin/env python3
import numpy as np, os, csv
import matplotlib.pyplot as plt
from scipy.sparse import diags, eye
from scipy.sparse.linalg import cg
from numpy.random import default_rng
rng = default_rng(7)

def make_field(N, L=1.0, corr=0.05):
    # synthetic omega: filtered white noise -> finite correlation
    x = np.linspace(0,L,N,endpoint=False); y=x
    kx = np.fft.fftfreq(N, d=L/N); ky=kx
    KX, KY = np.meshgrid(kx, ky, indexing='ij')
    filt = np.exp(-(KX**2+KY**2)*(2*np.pi*corr)**2)
    W = rng.normal(size=(N,N))
    Wk = np.fft.fftn(W); Sk = Wk * filt
    w = np.fft.ifftn(Sk).real
    w -= w.mean()
    return w, x, y

def laplacian_2d(N, h):
    main = -4*np.ones(N); off = np.ones(N-1)
    L1 = diags([off, main, off],[ -1, 0, +1 ])
    I = eye(N)
    L2 = diags([off, main, off],[ -1, 0, +1 ])
    # 2D Laplace with periodic BCs (wrap edges)
    # Build with Kronecker sums:
    # periodic tweak: add corners in banded way
    L1 = L1.tolil(); L2 = L2.tolil()
    L1[0,-1] = 1; L1[-1,0] = 1
    L2[0,-1] = 1; L2[-1,0] = 1
    L = np.kron(I.toarray(), L1.toarray()) + np.kron(L2.toarray(), I.toarray())
    return (1.0/h**2)*diags(L.diagonal()) + (1.0/h**2)*(diags(L.ravel(),0) - diags(L.diagonal()))  # compact; fine for N<=128

def solve_psi(N=128, L=1.0, m=40.0, kappa=1.0, corr=0.05):
    # grid
    h = L/N
    w, x, y = make_field(N, L, corr=corr)
    # operator A = (-Δ + m^2)
    # using 5-point Laplacian (periodic implemented in laplacian_2d crude build)
    # For speed, approximate with spectral diagonalization (FFT): exact on periodic grid
    # Here: spectral solve
    kx = 2*np.pi*np.fft.fftfreq(N, d=h); ky=kx
    KX, KY = np.meshgrid(kx, ky, indexing='ij')
    Lk = (KX**2 + KY**2)
    Wk = np.fft.fftn(w)
    Psik = kappa * Wk / (Lk + m*m + 1e-12)
    psi = np.fft.ifftn(Psik).real
    return psi, w, x, y

def radial_averages(psi, w, N, L, nR=10):
    # center at grid center
    xx = (np.arange(N)+0.5)*L/N - 0.5*L
    X,Y = np.meshgrid(xx,xx,indexing='ij')
    R = np.sqrt(X**2 + Y**2)
    Rmax = 0.4*L
    Rs = np.linspace(0.05*L, Rmax, nR)
    out = []
    for r in Rs:
        mask = (R<=r)
        V = np.sum(mask)
        psi_bar = psi[mask].mean()
        Omega = w[mask].sum()* (L/N)**2  # integrate w over region
        out.append([r, psi_bar, Omega, V])
    return np.array(out)

def main():
    outdir = "g21_psi_outputs"; os.makedirs(outdir, exist_ok=True)
    N=128; L=1.0
    m = 60.0  # large mass -> mr >> 1 for tested radii
    psi, w, x, y = solve_psi(N=N, L=L, m=m, kappa=1.0, corr=0.05)
    av = radial_averages(psi, w, N, L, nR=12)
    r, psibar, Omega, V = av.T

    # linear fit psibar vs Omega/Area
    A = np.vstack([Omega/(np.pi*r*r), np.ones_like(r)]).T
    coeff, *_ = np.linalg.lstsq(A, psibar, rcond=None)
    slope, intercept = coeff
    # correlation / R^2
    yhat = A@coeff; R2 = 1 - np.sum((psibar-yhat)**2)/np.sum((psibar-psibar.mean())**2)

    with open(os.path.join(outdir,"scaling.csv"),"w",newline="") as f:
        wtr = csv.writer(f); wtr.writerow(["r","psi_bar","Omega","Area"])
        for i in range(len(r)):
            wtr.writerow([r[i], psibar[i], Omega[i], np.pi*r[i]*r[i]])
        wtr.writerow(["slope", slope]); wtr.writerow(["intercept", intercept]); wtr.writerow(["R2", R2])

    # Plot
    plt.figure(figsize=(6,4))
    plt.plot(Omega/(np.pi*r*r), psibar, 'o', label='data')
    xfit = np.linspace(min(Omega/(np.pi*r*r)), max(Omega/(np.pi*r*r)), 100)
    plt.plot(xfit, slope*xfit + intercept, '-', label=f'fit: slope={slope:.3g}, R2={R2:.4f}')
    plt.xlabel(r'$\Omega(B_r)/{\rm Area}(B_r)$')
    plt.ylabel(r'$\overline{\Psi}(B_r)$')
    plt.legend(); plt.tight_layout()
    plt.savefig(os.path.join(outdir,"psi_scaling.png"), dpi=160); plt.close()
    print("G21: wrote g21_psi_outputs/scaling.csv and psi_scaling.png")

if __name__=="__main__":
    main()
