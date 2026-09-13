"""
G13: SU(3) L=16 — targeted Creutz ratio run.

Reduced warmup (200 sweeps); only the 9 Wilson loops needed for χ(2,2)–χ(5,5).
Saves incrementally so partial results survive a timeout.
"""
import numpy as np
import json, signal, sys, time

TIMEOUT_SECONDS = 520
_partial_results = {}   # filled incrementally

def _timeout_handler(signum, frame):
    print(f"\nTIMEOUT at {TIMEOUT_SECONDS}s. Saving partial results.", flush=True)
    _partial_results["timed_out"] = True
    with open("papers/39_qcd_from_gte/scripts/g13_su3_l16_results.json", "w") as f:
        json.dump(_partial_results, f, indent=2)
    print("Partial save done.", flush=True)
    sys.exit(0)

signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

rng = np.random.default_rng(42)
t0 = time.time()

L     = 16
beta  = 6.0
delta = 0.22

N_warmup      = 200   # cold start thermalizes by ~100 sweeps; 200 is safe
N_meas        = 80
MEAS_INTERVAL = 5

print(f"G13 SU(3) L={L} beta={beta} — targeted Creutz run")
print(f"N_warmup={N_warmup}, N_meas={N_meas}, interval={MEAS_INTERVAL}")
print(f"Estimated: warmup {N_warmup*0.5:.0f}s, meas {N_meas*(MEAS_INTERVAL*0.5+0.46):.0f}s", flush=True)


def project_su3_batch(V):
    v0 = V[..., :, 0].copy()
    v0 /= np.linalg.norm(v0, axis=-1, keepdims=True)
    dot01 = np.einsum('...i,...i->...', v0.conj(), V[..., :, 1])
    v1 = V[..., :, 1] - dot01[..., np.newaxis] * v0
    v1 /= np.linalg.norm(v1, axis=-1, keepdims=True)
    v2 = np.cross(v0.conj(), v1.conj())
    return np.stack([v0, v1, v2], axis=-1)


def compute_all_staples(U, mu):
    L = U.shape[0]
    St = np.zeros((L, L, L, L, 3, 3), dtype=complex)
    for nu in range(4):
        if nu == mu:
            continue
        Umu = U[..., mu, :, :]; Unu = U[..., nu, :, :]
        Unu_pmu  = np.roll(Unu, -1, axis=mu)
        Umu_pnu  = np.roll(Umu, -1, axis=nu)
        Umu_mnu  = np.roll(Umu,  1, axis=nu)
        Unu_mnu  = np.roll(Unu,  1, axis=nu)
        Unu_pmnu = np.roll(np.roll(Unu, -1, axis=mu), 1, axis=nu)
        fwd = np.matmul(np.matmul(Unu_pmu, Umu_pnu.conj().swapaxes(-1,-2)),
                        Unu.conj().swapaxes(-1,-2))
        bkd = np.matmul(np.matmul(Unu_pmnu.conj().swapaxes(-1,-2),
                                   Umu_mnu.conj().swapaxes(-1,-2)), Unu_mnu)
        St += fwd + bkd
    return St


def metropolis_sweep(U, beta, delta, rng):
    L = U.shape[0]; accepted = 0
    x0,x1,x2,x3 = np.mgrid[0:L,0:L,0:L,0:L]
    parity = (x0+x1+x2+x3) % 2
    I3 = np.eye(3, dtype=complex)
    for mu in range(4):
        St = compute_all_staples(U, mu)
        for color in [0,1]:
            mask = (parity == color); n = mask.sum()
            U_old = U[mask,mu].copy(); St_loc = St[mask]
            S_old = -beta/3.0 * np.trace(np.matmul(U_old,St_loc),axis1=-2,axis2=-1).real
            eps_r = rng.standard_normal((n,3,3)); eps_i = rng.standard_normal((n,3,3))
            eps = (eps_r + 1j*eps_i)*delta; eps = (eps - eps.conj().swapaxes(-1,-2))/2.0
            U_prop = np.matmul(U_old, I3[np.newaxis]+eps)
            U_new = project_su3_batch(U_prop)
            S_new = -beta/3.0 * np.trace(np.matmul(U_new,St_loc),axis1=-2,axis2=-1).real
            accept = np.log(rng.random(n)+1e-300) < (S_old-S_new)
            U_old[accept] = U_new[accept]; U[mask,mu] = U_old
            accepted += int(accept.sum())
            if color == 0: St = compute_all_staples(U, mu)
    return accepted / (L**4 * 4)


def plaquette_avg(U):
    L = U.shape[0]; total = 0.0; count = 0
    for mu in range(4):
        for nu in range(mu+1,4):
            Umu = U[...,mu,:,:]; Unu = U[...,nu,:,:]
            tmp = np.matmul(np.matmul(np.matmul(Umu, np.roll(Unu,-1,axis=mu)),
                            np.roll(Umu,-1,axis=nu).conj().swapaxes(-1,-2)),
                            Unu.conj().swapaxes(-1,-2))
            total += np.trace(tmp,axis1=-2,axis2=-1).real.sum()/3.0; count += L**4
    return total/count


def path_product(U, mu, R):
    P = U[...,mu,:,:].copy()
    for r in range(1,R): P = np.matmul(P, np.roll(U[...,mu,:,:],-r,axis=mu))
    return P


def wilson_loop_avg(U, R, T):
    if R >= L//2 or T >= L//2: return None
    nu=3; total=0.0; count=0
    PT = path_product(U,nu,T)
    for mu in range(3):
        PR = path_product(U,mu,R)
        W = np.matmul(np.matmul(np.matmul(PR, np.roll(PT,-R,axis=mu)),
                     np.roll(PR,-T,axis=nu).conj().swapaxes(-1,-2)),
                     PT.conj().swapaxes(-1,-2))
        total += np.trace(W,axis1=-2,axis2=-1).real.sum()/3.0; count += L**4
    return total/count


# ── Initialize ────────────────────────────────────────────────────────────────
U = np.zeros((L,L,L,L,4,3,3), dtype=complex)
for i in range(3): U[:,:,:,:,:,i,i] = 1.0

# ── Warmup ────────────────────────────────────────────────────────────────────
print(f"\n=== WARMUP ({N_warmup} sweeps) ===", flush=True)
for i in range(1, N_warmup+1):
    acc = metropolis_sweep(U, beta, delta, rng)
    if i % 50 == 0 and i <= 150:
        avg_acc = acc
        if avg_acc < 0.44: delta *= 0.9
        elif avg_acc > 0.56: delta *= 1.1
        delta = float(np.clip(delta, 0.05, 0.8))
    if i in [1,5,10,50,100,150,200] or i % 100 == 0:
        P = plaquette_avg(U)
        print(f"  Sweep {i:3d}: P={P:.4f}, acc={acc:.3f}, t={time.time()-t0:.1f}s", flush=True)

P_warmup = plaquette_avg(U)
print(f"After warmup: P = {P_warmup:.4f}", flush=True)

# ── Measurements ─────────────────────────────────────────────────────────────
# 9 targeted Wilson loops for χ(2,2)–χ(5,5)
TARGET_LOOPS = [(1,1),(2,1),(2,2),(3,2),(3,3),(4,3),(4,4),(5,4),(5,5)]
W_meas = {k: [] for k in TARGET_LOOPS}
P_meas = []

print(f"\n=== MEASUREMENT ({N_meas} × {MEAS_INTERVAL} sweeps) ===", flush=True)

for k in range(1, N_meas+1):
    for _ in range(MEAS_INTERVAL):
        metropolis_sweep(U, beta, delta, rng)

    P_meas.append(plaquette_avg(U))
    for (R,T) in TARGET_LOOPS:
        w = wilson_loop_avg(U, R, T)
        if w is not None and w > 1e-15:
            W_meas[(R,T)].append(w)

    if k % 20 == 0:
        elapsed = time.time()-t0
        print(f"  Meas {k:3d}/{N_meas}: P={P_meas[-1]:.4f}, t={elapsed:.1f}s", flush=True)

    # Save partial results every 10 measurements
    if k % 10 == 0:
        _partial_results.update({
            "k": k, "P_final": float(np.mean(P_meas)),
            "W_means": {f"W({R},{T})": float(np.mean(v)) for (R,T),v in W_meas.items() if v},
        })

print("\nMeasurements complete.", flush=True)


# ── Creutz ratios ─────────────────────────────────────────────────────────────
def creutz(R, T):
    RT     = np.array(W_meas.get((R,T), []))
    RTm1   = np.array(W_meas.get((R,T-1), []))
    Rm1T   = np.array(W_meas.get((R-1,T), []))
    Rm1Tm1 = np.array(W_meas.get((R-1,T-1), []))
    N = min(len(RT), len(RTm1), len(Rm1T), len(Rm1Tm1))
    if N < 2: return None, None
    chi = -np.log(np.maximum(RT[:N]*Rm1Tm1[:N], 1e-30) /
                  np.maximum(RTm1[:N]*Rm1T[:N], 1e-30))
    mean = float(chi.mean())
    jk = np.array([np.delete(chi,i).mean() for i in range(N)])
    err = float(np.sqrt((N-1)*np.mean((jk-jk.mean())**2)))
    return mean, err

print("\n=== Creutz Ratios ===", flush=True)
creutz_results = {}
for R in range(2, 6):
    val, err = creutz(R, R)
    if val is not None:
        creutz_results[f"chi({R},{R})"] = {"mean": val, "err": err, "N": len(W_meas[(R,R)])}
        print(f"  χ({R},{R}) = {val:.5f} ± {err:.5f}  (N={len(W_meas[(R,R)])})")

# String tension fit
sym_pairs = [(R, creutz_results[f"chi({R},{R})"])
             for R in range(2,6) if f"chi({R},{R})" in creutz_results]

if len(sym_pairs) >= 3:
    Rs   = np.array([p[0] for p in sym_pairs], float)
    vals = np.array([p[1]["mean"] for p in sym_pairs])
    errs = np.array([p[1]["err"] for p in sym_pairs])

    A  = np.column_stack([np.ones_like(Rs), 1.0/(Rs*(Rs-1))])
    W_wt = 1.0/errs**2
    try:
        params, *_ = np.linalg.lstsq((A*W_wt[:,None]).T @ A,
                                     (A*W_wt[:,None]).T @ vals, rcond=None)
        sigma_a2, alpha = params
        C_mat = np.linalg.inv((A * W_wt[:,None]).T @ A)
        sigma_a2_err = float(np.sqrt(C_mat[0,0]))

        print(f"\n=== String Tension Fit ===")
        print(f"σ·a² = {sigma_a2:.5f} ± {sigma_a2_err:.5f}")
        print(f"α    = {alpha:.5f}")

        m_kink = (8/49)*1.77686; DK = np.log2(9)
        sigma_GTE = DK * m_kink**2
        a_fm = 0.093; hc = 0.197326980
        sigma_phys = sigma_a2 * hc**2 / a_fm**2
        sigma_phys_err = sigma_a2_err * hc**2 / a_fm**2
        f_quant = sigma_phys / sigma_GTE
        f_quant_err = sigma_phys_err / sigma_GTE
        print(f"σ_phys = {sigma_phys:.4f} ± {sigma_phys_err:.4f} GeV²  (PDG=0.18)")
        print(f"f_quant (σ-ratio) = {f_quant:.5f} ± {f_quant_err:.5f}")
        print(f"f_quant (C-ratio) = {1/1.59:.5f}  [P39 canonical]")
        print(f"4^(-1/3)          = {4**(-1/3):.5f}")
        if f_quant_err > 0:
            print(f"Pull vs 4^(-1/3): {(f_quant - 4**(-1/3))/f_quant_err:.1f}σ")
            print(f"Pull vs 0.18/σGTE: {(f_quant - 0.18/sigma_GTE)/f_quant_err:.1f}σ")

        creutz_results["fit"] = {
            "sigma_a2": float(sigma_a2), "sigma_a2_err": float(sigma_a2_err),
            "alpha": float(alpha), "sigma_phys_GeV2": float(sigma_phys),
            "sigma_phys_err_GeV2": float(sigma_phys_err),
            "f_quant": float(f_quant), "f_quant_err": float(f_quant_err),
        }
    except Exception as e:
        print(f"Fit failed: {e}")

signal.alarm(0)

results = {
    "algorithm": "SU(3) L=16 vectorized Metropolis — targeted Creutz run",
    "L": L, "beta": beta, "N_warmup": N_warmup, "N_meas": N_meas,
    "P_warmup": float(P_warmup),
    "P_final": float(np.mean(P_meas)) if P_meas else None,
    "W_means": {f"W({R},{T})": float(np.mean(v)) for (R,T),v in W_meas.items() if v},
    "creutz_ratios": creutz_results,
    "elapsed_s": time.time()-t0,
}

with open("papers/39_qcd_from_gte/scripts/g13_su3_l16_results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"\nElapsed: {time.time()-t0:.1f}s")
print("Saved to research-sandbox/g13_su3_l16_fast_results.json")
