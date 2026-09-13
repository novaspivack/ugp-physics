#!/usr/bin/env python3
import numpy as np, os, csv
import matplotlib.pyplot as plt
from numpy.random import default_rng
rng = default_rng(101)

def random_povm(dim=3, m=4):
    # build random positive semidefinite effects and normalize sum to I
    Es=[]
    for _ in range(m):
        v = rng.normal(size=(dim,))+1j*rng.normal(size=(dim,))
        v = v/np.linalg.norm(v)
        E = np.outer(v, np.conj(v))
        # scale by random weight
        w = rng.gamma(1.0)
        Es.append(w*E)
    S = sum(Es)
    # normalize: E_i <- S^{-1/2} E_i S^{-1/2}
    evals, evecs = np.linalg.eigh(S)
    Sinv2 = evecs @ np.diag(1.0/np.sqrt(evals+1e-12)) @ evecs.conj().T
    Es = [Sinv2 @ E @ Sinv2 for E in Es]
    # fix numerical: sum E_i ≈ I
    return Es

def normalize(v): n=np.linalg.norm(v); return v/n if n>0 else v
def dagger(A): return A.conj().T

def trajs(dim=3, m=4, ntraj=20000, T=2.0, gamma=5.0, dt=1e-3):
    Es = random_povm(dim=dim, m=m)
    # random bounded Hamiltonian
    A = rng.normal(size=(dim,dim))+1j*rng.normal(size=(dim,dim))
    H = 0.5*(A+dagger(A)); H = H / np.max(np.abs(np.linalg.eigvals(H)))
    # unitary
    evals, evecs = np.linalg.eigh(H)
    Udt = evecs @ np.diag(np.exp(-1j*evals*dt)) @ dagger(evecs)

    def random_ket(d):
        v = rng.normal(size=d)+1j*rng.normal(size=d); return normalize(v)

    counts = np.zeros(m, int)

    def next_exp(rate):
        u = rng.random(); return -np.log(1-u)/rate

    for k in range(ntraj):
        psi = random_ket(dim); t=0.0; t_next = next_exp(gamma)
        while t<T:
            while t<min(T,t_next):
                psi = Udt @ psi; psi = normalize(psi); t += dt
            if t>=T: break
            probs = np.array([np.real(np.vdot(psi, E@psi)) for E in Es])
            probs = np.maximum(probs,0.0); probs/=probs.sum()
            i = np.searchsorted(np.cumsum(probs), rng.random(), side='right')
            counts[i]+=1
            # Lüders for general effect: Kraus operator via polar decomposition; use sqrt via eigh
            evals, evecs = np.linalg.eigh(Es[i])
            sqrtE = evecs @ np.diag(np.sqrt(np.maximum(evals,0.0))) @ evecs.conj().T
            psi = sqrtE @ psi; psi = normalize(psi)
            t_next = t + next_exp(gamma)

    # predict average Born probs by Monte Carlo over Haar states
    n_est = 20000; pred = np.zeros(m)
    for _ in range(n_est):
        v = random_ket(dim)
        pred += np.array([np.real(np.vdot(v, E@v)) for E in Es])
    pred /= n_est
    freqs = counts / counts.sum()
    KL = np.sum(freqs * (np.log((freqs+1e-12)/(pred+1e-12))))
    L1 = np.sum(np.abs(freqs - pred))
    return dict(dim=dim, m=m, counts=counts, freqs=freqs, pred=pred, KL=KL, L1=L1)

def main():
    outdir="g23_qm_outputs"; os.makedirs(outdir, exist_ok=True)
    res = trajs(dim=3, m=4, ntraj=20000, T=2.0, gamma=5.0, dt=1e-3)
    x = np.arange(res["m"])
    plt.figure(figsize=(6,4))
    plt.bar(x-0.15, res["pred"], width=0.3, label="Born (pred)")
    plt.bar(x+0.15, res["freqs"], width=0.3, label="Empirical")
    plt.xticks(x, [f"E{i}" for i in range(res["m"])])
    plt.ylabel("Probability"); plt.legend()
    plt.title(f"Random POVM (dim=3, m=4): KL={res['KL']:.2e}, L1={res['L1']:.2e}")
    plt.tight_layout(); plt.savefig(os.path.join(outdir,"povm_bar.png"), dpi=160); plt.close()

    with open(os.path.join(outdir,"summary.csv"),"w",newline="") as f:
        import csv; w=csv.writer(f)
        w.writerow(["dim","m","KL","L1"]); w.writerow([res["dim"],res["m"],res["KL"],res["L1"]])
    print("G23: wrote g23_qm_outputs/summary.csv and povm_bar.png")

if __name__=="__main__":
    main()
