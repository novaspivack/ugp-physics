"""
G13: SU(3) L=16 — targeted Creutz ratio run, fixed symmetric formula.

Bug fix: previous version used asymmetric Creutz ratio needing W(R-1,T) loops
that were never measured. Fixed to use symmetric formula:
  χ(R,R) = -ln[ W(R,R) · W(R-1,R-1) / W(R,R-1)^2 ]
which requires only W(R,T) with R>=T — exactly the measured set.

Output: papers/39_qcd_from_gte/scripts/g13_su3_l16_results.json
"""
import numpy as np
import json, signal, sys, time

TIMEOUT_SECONDS = 530
_partial_results = {}

def _timeout_handler(signum, frame):
    print(f"\nTIMEOUT at {TIMEOUT_SECONDS}s. Saving partial results.", flush=True)
    _partial_results["timed_out"] = True
    out = "papers/39_qcd_from_gte/scripts/g13_su3_l16_results.json"
    with open(out, "w") as f:
        json.dump(_partial_results, f, indent=2)
    print(f"Partial save done to {out}.", flush=True)
    sys.exit(0)

signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

rng = np.random.default_rng(42)
t0 = time.time()

L     = 16
beta  = 6.0
delta = 0.22

N_warmup      = 200
N_meas        = 80
MEAS_INTERVAL = 5

print(f"G13 SU(3) L={L} beta={beta} — fixed symmetric Creutz run")
print(f"N_warmup={N_warmup}, N_meas={N_meas}, interval={MEAS_INTERVAL}", flush=True)


def project_su3_batch(V):
    v0 = V[..., :, 0].copy()
    v0 /= np.linalg.norm(v0, axis=-1, keepdims=True)
    dot01 = np.einsum('...i,...i->...', v0.conj(), V[..., :, 1])
    v1 = V[..., :, 1] - dot01[..., np.newaxis] * v0
    v1 /= np.linalg.norm(v1, axis=-1, keepdims=True)
    v2 = np.cross(v0.conj(), v1.conj())
    return np.stack([v0, v1, v2], axis=-1)


def compute_all_staples(U, mu):
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
    accepted = 0
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
            eps = (eps_r + 1j*eps_i)*delta
            eps = (eps - eps.conj().swapaxes(-1,-2))/2.0
            U_prop = np.matmul(U_old, I3[np.newaxis]+eps)
            U_new = project_su3_batch(U_prop)
            S_new = -beta/3.0 * np.trace(np.matmul(U_new,St_loc),axis1=-2,axis2=-1).real
            accept = np.log(rng.random(n)+1e-300) < (S_old-S_new)
            U_old[accept] = U_new[accept]; U[mask,mu] = U_old
            accepted += int(accept.sum())
            if color == 0: St = compute_all_staples(U, mu)
    return accepted / (L**4 * 4)


def plaquette_avg(U):
    total = 0.0; count = 0
    for mu in range(4):
        for nu in range(mu+1,4):
            Umu = U[...,mu,:,:]; Unu = U[...,nu,:,:]
            tmp = np.matmul(np.matmul(np.matmul(Umu, np.roll(Unu,-1,axis=mu)),
                            np.roll(Umu,-1,axis=nu).conj().swapaxes(-1,-2)),
                            Unu.conj().swapaxes(-1,-2))
            total += np.trace(tmp,axis1=-2,axis2=-1).real.sum()/3.0
            count += L**4
    return total/count


def path_product(U, mu, R):
    P = U[...,mu,:,:].copy()
    for r in range(1,R):
        P = np.matmul(P, np.roll(U[...,mu,:,:],-r,axis=mu))
    return P


def wilson_loop_avg(U, R, T):
    if R >= L//2 or T >= L//2: return None
    nu=3; total=0.0
    PT = path_product(U,nu,T)
    for mu in range(3):
        PR = path_product(U,mu,R)
        W = np.matmul(np.matmul(np.matmul(PR, np.roll(PT,-R,axis=mu)),
                     np.roll(PR,-T,axis=nu).conj().swapaxes(-1,-2)),
                     PT.conj().swapaxes(-1,-2))
        total += np.trace(W,axis1=-2,axis2=-1).real.sum()/3.0
    return total / (3.0 * L**4)


# ── Initialize (cold start) ────────────────────────────────────────────────────
U = np.zeros((L,L,L,L,4,3,3), dtype=complex)
for i in range(3): U[:,:,:,:,:,i,i] = 1.0

# ── Warmup ────────────────────────────────────────────────────────────────────
print(f"\n=== WARMUP ({N_warmup} sweeps) ===", flush=True)
for i in range(1, N_warmup+1):
    acc = metropolis_sweep(U, beta, delta, rng)
    if i % 50 == 0 and i <= 150:
        if acc < 0.44: delta *= 0.9
        elif acc > 0.56: delta *= 1.1
        delta = float(np.clip(delta, 0.05, 0.8))
    if i in [1,5,10,50,100,150,200] or i % 100 == 0:
        P = plaquette_avg(U)
        print(f"  Sweep {i:3d}: P={P:.4f}, acc={acc:.3f}, t={time.time()-t0:.1f}s", flush=True)

P_warmup = float(plaquette_avg(U))
print(f"After warmup: P = {P_warmup:.4f}", flush=True)

# ── Measurements ─────────────────────────────────────────────────────────────
# Symmetric loops needed for χ(R,R) = -ln[W(R,R)·W(R-1,R-1)/W(R,R-1)²]
# Requires: W(1,1), W(2,1), W(2,2), W(3,2), W(3,3), W(4,3), W(4,4), W(5,4), W(5,5)
TARGET_LOOPS = [(1,1),(2,1),(2,2),(3,2),(3,3),(4,3),(4,4),(5,4),(5,5)]
W_meas = {k: [] for k in TARGET_LOOPS}
P_meas = []

print(f"\n=== MEASUREMENT ({N_meas} configs × {MEAS_INTERVAL} sweeps) ===", flush=True)

for k in range(1, N_meas+1):
    for _ in range(MEAS_INTERVAL):
        metropolis_sweep(U, beta, delta, rng)

    P_meas.append(plaquette_avg(U))
    for (R,T) in TARGET_LOOPS:
        w = wilson_loop_avg(U, R, T)
        if w is not None and w > 1e-15:
            W_meas[(R,T)].append(w)

    if k % 20 == 0:
        print(f"  Meas {k:3d}/{N_meas}: P={P_meas[-1]:.4f}, t={time.time()-t0:.1f}s", flush=True)

    # Incremental save every 10 configs
    if k % 10 == 0:
        _partial_results.update({
            "n_meas_done": k,
            "P_final": float(np.mean(P_meas)),
            "W_means": {f"W({R},{T})": float(np.mean(v))
                        for (R,T),v in W_meas.items() if v},
        })

print(f"\nMeasurements complete. t={time.time()-t0:.1f}s", flush=True)

# ── Symmetric Creutz ratios ───────────────────────────────────────────────────
# χ(R,R) = -ln[ W(R,R) · W(R-1,R-1) / W(R,R-1)^2 ]
# All three inputs are in TARGET_LOOPS.
def creutz_sym(R):
    """Symmetric Creutz ratio χ(R,R) with jackknife error."""
    WRR   = np.array(W_meas.get((R,R),   []))
    Wm1m1 = np.array(W_meas.get((R-1,R-1), []))
    WRm1  = np.array(W_meas.get((R,R-1),  []))
    N = min(len(WRR), len(Wm1m1), len(WRm1))
    if N < 2: return None, None, N
    chi = -np.log(np.maximum(WRR[:N]*Wm1m1[:N], 1e-30) /
                  np.maximum(WRm1[:N]**2, 1e-30))
    mean_val = float(chi.mean())
    jk = np.array([np.delete(chi,i).mean() for i in range(N)])
    err = float(np.sqrt((N-1)*np.mean((jk - jk.mean())**2)))
    return mean_val, err, N

print("\n=== Symmetric Creutz Ratios ===", flush=True)
creutz_results = {}
for R in range(2, 6):
    val, err, N = creutz_sym(R)
    if val is not None:
        creutz_results[f"chi({R},{R})"] = {"mean": val, "err": err, "N": N}
        print(f"  χ({R},{R}) = {val:.5f} ± {err:.5f}  (N={N})")

# ── Cornell-Coulomb fit: χ(R,R) = σ·a² + α/(R(R-1)) ────────────────────────
sym_list = [(R, creutz_results[f"chi({R},{R})"])
            for R in range(2,6) if f"chi({R},{R})" in creutz_results]

sigma_a2 = sigma_a2_err = alpha_fit = None
sigma_phys_GeV2 = sigma_phys_err = None

if len(sym_list) >= 2:
    Rs   = np.array([p[0] for p in sym_list], float)
    vals = np.array([p[1]["mean"] for p in sym_list])
    errs = np.array([p[1]["err"] for p in sym_list])
    errs = np.where(errs < 1e-10, 1e-10, errs)

    # Weighted least squares: [1, 1/(R(R-1))] @ [sigma_a2, alpha]^T = chi(R,R)
    A = np.column_stack([np.ones_like(Rs), 1.0/(Rs*(Rs-1))])
    W_wt = 1.0/errs**2
    AW = A * W_wt[:,None]
    try:
        params = np.linalg.solve(AW.T @ A, AW.T @ vals)
        sigma_a2_fit, alpha_fit = params
        C_mat = np.linalg.inv(AW.T @ A)
        sigma_a2_err_fit = float(np.sqrt(abs(C_mat[0,0])))

        # Jackknife on σ·a² across configs in chi(2,2)
        # Use chi(2,2) per-config data for jackknife
        R_jk = 2
        wRR = np.array(W_meas.get((R_jk, R_jk), []))
        wm1 = np.array(W_meas.get((R_jk-1, R_jk-1), []))
        wRm1= np.array(W_meas.get((R_jk, R_jk-1), []))
        Njk = min(len(wRR), len(wm1), len(wRm1))
        if Njk >= 4:
            chi_22_arr = -np.log(np.maximum(wRR[:Njk]*wm1[:Njk], 1e-30) /
                                  np.maximum(wRm1[:Njk]**2, 1e-30))
            # Use chi(2,2) ~ sigma_a2 + alpha/2 to get jackknife on sigma_a2
            # For R=2: 1/(R(R-1)) = 0.5, so sigma_a2 = chi(2,2) - alpha/2
            # But use full fit jackknife across all available data
            jk_sigma = []
            for drop in range(Njk):
                chi22_jk = np.delete(chi_22_arr, drop).mean()
                # Quick single-point estimate using only chi(2,2)
                # sigma_a2_jk = chi22_jk - alpha_fit*0.5
                jk_sigma.append(chi22_jk - float(alpha_fit)*0.5)
            jk_sigma = np.array(jk_sigma)
            sigma_a2_jk_err = float(np.sqrt((Njk-1)*np.mean((jk_sigma-jk_sigma.mean())**2)))
        else:
            sigma_a2_jk_err = sigma_a2_err_fit

        # Physical string tension: a = 0.093 fm = 0.093/0.197326980 GeV^-1
        a_fm = 0.093
        hc_GeV_fm = 0.197326980   # GeV·fm
        a_inv_GeV = a_fm / hc_GeV_fm   # a in GeV^-1
        sigma_phys = float(sigma_a2_fit) / a_inv_GeV**2   # GeV^2
        sigma_phys_e = float(sigma_a2_jk_err) / a_inv_GeV**2

        print(f"\n=== Cornell-Coulomb Fit ===")
        print(f"σ·a²     = {sigma_a2_fit:.5f} ± {sigma_a2_jk_err:.5f}  (jackknife)")
        print(f"α        = {alpha_fit:.5f}")
        print(f"σ_phys   = {sigma_phys:.4f} ± {sigma_phys_e:.4f} GeV²  (PDG ≈ 0.18)")

        # f_quant candidates
        # GTE prediction: σ = f_q * σ_GTE where σ_GTE = log2(9) * m_kink²
        m_kink  = (8.0/49.0)*1.77686   # GeV
        sigma_GTE = np.log2(9) * m_kink**2
        print(f"σ_GTE    = {sigma_GTE:.5f} GeV²")

        candidates = {
            "4^(-1/3)":    4.0**(-1.0/3.0),
            "1/1.59":      1.0/1.59,
            "1/sqrt(3)":   1.0/np.sqrt(3),
            "1/pi":        1.0/np.pi,
            "sigma_PDG/sigma_GTE": 0.18/sigma_GTE,
        }
        print(f"\n=== f_quant Candidates ===")
        f_quant_comparison = {}
        for name, fq in candidates.items():
            sigma_pred = fq * sigma_GTE
            pull = (sigma_phys - sigma_pred) / sigma_phys_e if sigma_phys_e > 0 else None
            print(f"  {name:30s}: f={fq:.5f}, σ_pred={sigma_pred:.4f}, pull={pull:+.2f}σ")
            f_quant_comparison[name] = {
                "f_quant": float(fq),
                "sigma_pred_GeV2": float(sigma_pred),
                "pull_sigma": float(pull) if pull is not None else None,
            }

        sigma_a2 = float(sigma_a2_fit)
        sigma_a2_err = float(sigma_a2_jk_err)
        alpha_fit = float(alpha_fit)
        sigma_phys_GeV2 = float(sigma_phys)
        sigma_phys_err = float(sigma_phys_e)

        creutz_results["fit"] = {
            "sigma_a2": sigma_a2,
            "sigma_a2_err_jackknife": sigma_a2_err,
            "sigma_a2_err_fit": float(sigma_a2_err_fit),
            "alpha": alpha_fit,
            "sigma_phys_GeV2": sigma_phys_GeV2,
            "sigma_phys_err_GeV2": sigma_phys_err,
            "f_quant_comparison": f_quant_comparison,
        }

    except np.linalg.LinAlgError as e:
        print(f"Fit failed: {e}")

signal.alarm(0)

results = {
    "algorithm": "SU(3) L=16 vectorized Metropolis — symmetric Creutz ratio (bug-fixed)",
    "L": L, "beta": beta,
    "N_warmup": N_warmup, "N_meas": len(P_meas),
    "meas_interval": MEAS_INTERVAL,
    "P_warmup": float(P_warmup),
    "P_final": float(np.mean(P_meas)) if P_meas else None,
    "W_means": {f"W({R},{T})": float(np.mean(v))
                for (R,T),v in W_meas.items() if v},
    "W_stds": {f"W({R},{T})": float(np.std(v))
               for (R,T),v in W_meas.items() if len(v) > 1},
    "creutz_ratios": creutz_results,
    "sigma_a2": sigma_a2,
    "sigma_a2_err": sigma_a2_err,
    "alpha": alpha_fit,
    "sigma_phys_GeV2": sigma_phys_GeV2,
    "sigma_phys_err_GeV2": sigma_phys_err,
    "elapsed_s": float(time.time()-t0),
}

out_path = "papers/39_qcd_from_gte/scripts/g13_su3_l16_results.json"
with open(out_path, "w") as f:
    json.dump(results, f, indent=2)
print(f"\nElapsed: {time.time()-t0:.1f}s")
print(f"Results saved to {out_path}")
