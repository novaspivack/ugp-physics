#!/usr/bin/env python3
import numpy as np
import matplotlib.pyplot as plt
import os, csv
from numpy.random import default_rng

rng = default_rng(20251104)

def dagger(A): return A.conj().T
def normalize(psi):
    n = np.linalg.norm(psi)
    return psi / n if n>0 else psi

def unitary(H, dt):
    # 1st-order expm surrogate is enough for small dt; or use exact for 2x2
    # Here: use eigendecomposition for stability.
    evals, evecs = np.linalg.eigh(H)
    U = (evecs) @ np.diag(np.exp(-1j*evals*dt)) @ dagger(evecs)
    return U

def sample_poisson_time(rate):
    # exponential waiting time
    u = rng.random()
    return -np.log(1.0 - u) / rate

def sample_discrete(probs):
    c = np.cumsum(probs)
    r = rng.random()
    return int(np.searchsorted(c, r, side='right'))

def projectors_z_qubit():
    # |0><0|, |1><1|
    P0 = np.array([[1,0],[0,0]], dtype=complex)
    P1 = np.array([[0,0],[0,1]], dtype=complex)
    return [P0, P1], ["0","1"]

def projectors_fourier_qutrit():
    # POVM of rank-1 projectors in Fourier basis
    w = np.exp(2j*np.pi/3)
    F = (1/np.sqrt(3))*np.array([[1,1,1],[1,w,w**2],[1,w**2,w]], dtype=complex)
    Es = []
    labels = []
    for k in range(3):
        ket = F[:,k].reshape(-1,1)
        Es.append(ket@dagger(ket))
        labels.append(f"f{k}")
    return Es, labels

def run_trajectories(dim=2, ntraj=20000, T=2.0, gamma=5.0, dt_unitary=1e-3):
    # Hamiltonian: random Hermitian with bounded norm
    A = rng.normal(size=(dim,dim)) + 1j*rng.normal(size=(dim,dim))
    H = 0.5*(A + dagger(A))
    # normalize spectrum scale
    H = H / np.max(np.abs(np.linalg.eigvals(H)))

    # POVM
    if dim==2:
        Es, labels = projectors_z_qubit()
    else:
        Es, labels = projectors_fourier_qutrit()
    m = len(Es)

    counts = np.zeros(m, dtype=int)

    # initial state: random pure normalized ket
    def random_ket(d):
        v = rng.normal(size=d) + 1j*rng.normal(size=d)
        return normalize(v)

    U_dt = unitary(H, dt_unitary)

    for k in range(ntraj):
        psi = random_ket(dim)
        t = 0.0
        t_next = sample_poisson_time(gamma)
        while t < T:
            # advance in small dt steps up to t_next (or T)
            while t < min(T, t_next):
                psi = U_dt @ psi
                psi = normalize(psi)
                t += dt_unitary
            if t >= T: break
            # adjudication event at t_next
            # probabilities P(i) := <psi|E_i|psi>
            probs = np.array([np.real(dagger(psi)@(E@psi)) for E in Es], dtype=float)
            probs = np.maximum(probs, 0.0)
            probs = probs / probs.sum()
            i = sample_discrete(probs)
            counts[i] += 1
            # post-measurement state: normalize sqrt(E_i)|psi>
            # for projectors, sqrt(E_i)=E_i
            sqrtEi = Es[i]  # projective case
            psi = sqrtEi @ psi
            psi = normalize(psi)
            # schedule next jump
            t_next = t + sample_poisson_time(gamma)

    # theoretical average over Haar-random psi is uniform for projective POVMs of orthonormal basis.
    # But because unitary dynamics scrambles phases, empirical mean ~ average Born weight.
    # We compute ensemble-mean predicted probs via many random pure states:
    n_est = 20000
    pred = np.zeros(m, dtype=float)
    for _ in range(n_est):
        v = random_ket(dim)
        pv = np.array([np.real(dagger(v)@(E@v)) for E in Es], dtype=float)
        pred += pv
    pred /= n_est

    freqs = counts / counts.sum()
    kl = np.sum(freqs * (np.log((freqs+1e-12)/(pred+1e-12))))
    l1 = np.sum(np.abs(freqs - pred))

    return dict(dim=dim, ntraj=ntraj, T=T, gamma=gamma, counts=counts,
                freqs=freqs, pred=pred, KL=kl, L1=l1, labels=labels)

def save_plots(res, outdir):
    os.makedirs(outdir, exist_ok=True)
    x = np.arange(len(res["labels"]))
    plt.figure(figsize=(6,4))
    plt.bar(x-0.15, res["pred"], width=0.3, label="Born (pred)")
    plt.bar(x+0.15, res["freqs"], width=0.3, label="Empirical")
    plt.xticks(x, res["labels"])
    plt.ylim(0, 1.0)
    ttl = f"dim={res['dim']}, ntraj={res['ntraj']}, KL={res['KL']:.4e}, L1={res['L1']:.4e}"
    plt.title(ttl)
    plt.ylabel("Probability")
    plt.legend()
    fn = f"traj_dim{res['dim']}_bar.png"
    plt.tight_layout()
    plt.savefig(os.path.join(outdir, fn), dpi=160)
    plt.close()
    return fn

def main():
    outdir = "qm_traj_outputs"
    os.makedirs(outdir, exist_ok=True)
    rows = []
    for dim in [2,3]:
        res = run_trajectories(dim=dim, ntraj=20000, T=2.0, gamma=5.0, dt_unitary=1e-3)
        fn = save_plots(res, outdir)
        rows.append([dim, res["ntraj"], res["T"], res["gamma"],
                     *res["counts"], *res["freqs"], *res["pred"],
                     res["KL"], res["L1"], fn])

    with open(os.path.join(outdir,"summary.csv"), "w", newline="") as f:
        w = csv.writer(f)
        # dynamic headers for counts/freqs/preds
        hdr = ["dim","ntraj","T","gamma"]
        hdr += [f"count_{i}" for i in range(3)]   # up to 3 outcomes max here
        hdr += [f"freq_{i}" for i in range(3)]
        hdr += [f"pred_{i}" for i in range(3)]
        hdr += ["KL","L1","barplot"]
        w.writerow(hdr)
        for r in rows: w.writerow(r)
    print(f"Done. See {outdir}/summary.csv and bar plots in {outdir}/")

if __name__ == "__main__":
    main()
