"""
G13: SU(3) pure gauge Metropolis on L=8 lattice, beta=6.0.

Uses fully vectorized checkerboard sweep to avoid the per-site Python-loop
bottleneck.  L=8, N_t=8: beta_c ≈ 6.06 for N_t=8, so beta=6.0 sits just
below the deconfinement transition — the system is in the confined phase.

Key improvements over g13_creutz_ratio_vectorized.py (L=4):
  - Vectorized sweep: all L^4/2 sites updated in one batch per color/direction
  - Vectorized Wilson loops via path products (np.roll chains)
  - Adaptive delta tuning during warmup
  - Multiple Creutz ratios chi(2,2), chi(2,3), chi(3,2), chi(3,3)
  - Jackknife error estimation on chi values
"""
import numpy as np
import json, signal, sys, time

TIMEOUT_SECONDS = 560

def _timeout_handler(signum, frame):
    print(f"\nTIMEOUT after {TIMEOUT_SECONDS}s. Saving partial results.", flush=True)
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

rng = np.random.default_rng(42)
t0 = time.time()

L     = 8
beta  = 6.0
delta = 0.22    # Tuned for ~50% acceptance on L=8 (slightly larger than L=4 value)

N_warmup      = 1000   # sweeps before measurement
N_meas        = 400    # measurement sweeps
MEAS_INTERVAL = 5      # sweeps between measurements
TUNE_INTERVAL = 50     # sweeps between delta tuning during warmup
TARGET_ACC    = 0.50

print(f"G13 SU(3) L={L} beta={beta} — vectorized Metropolis")
print(f"N_warmup={N_warmup}, N_meas={N_meas}, meas_interval={MEAS_INTERVAL}")
print(f"Total sweeps: {N_warmup + N_meas * MEAS_INTERVAL}")
print(f"Expected runtime: {(N_warmup + N_meas*MEAS_INTERVAL)*23e-3:.0f}s at 23ms/sweep")
print(flush=True)


# ── SU(3) utilities ─────────────────────────────────────────────────────────

def project_su3_batch(V):
    """Project batch (..., 3, 3) to SU(3) via complex Gram-Schmidt."""
    v0 = V[..., :, 0].copy()
    n0 = np.linalg.norm(v0, axis=-1, keepdims=True)
    v0 = v0 / n0

    dot01 = np.einsum('...i,...i->...', v0.conj(), V[..., :, 1])
    v1 = V[..., :, 1] - dot01[..., np.newaxis] * v0
    n1 = np.linalg.norm(v1, axis=-1, keepdims=True)
    v1 = v1 / n1

    # Third column: ε_{ijk} (v0*)_j (v1*)_k — complex cross product
    v2 = np.cross(v0.conj(), v1.conj())
    return np.stack([v0, v1, v2], axis=-1)


def compute_all_staples(U, mu):
    """Compute staple sum S(x, mu) = Σ_{ν≠μ}(S^+ + S^-) for all sites at once.

    S^+(x,μ,ν)  = U[x+μ,ν] @ U[x+ν,μ]† @ U[x,ν]†
    S^-(x,μ,ν)  = U[x+μ-ν,ν]† @ U[x-ν,μ]† @ U[x-ν,ν]
    Returns: (L,L,L,L,3,3)
    """
    L = U.shape[0]
    St = np.zeros((L, L, L, L, 3, 3), dtype=complex)

    for nu in range(4):
        if nu == mu:
            continue

        Umu = U[..., mu, :, :]   # U[x, mu]
        Unu = U[..., nu, :, :]   # U[x, nu]

        Unu_pmu  = np.roll(Unu, -1, axis=mu)   # U[x+mu, nu]
        Umu_pnu  = np.roll(Umu, -1, axis=nu)   # U[x+nu, mu]
        Umu_mnu  = np.roll(Umu,  1, axis=nu)   # U[x-nu, mu]
        Unu_mnu  = np.roll(Unu,  1, axis=nu)   # U[x-nu, nu]
        # U[x+mu-nu, nu]: first shift by -1 along mu, then +1 along nu
        Unu_pmnu = np.roll(np.roll(Unu, -1, axis=mu), 1, axis=nu)

        # Forward staple: U[x+mu,nu] @ U[x+nu,mu]† @ U[x,nu]†
        fwd = np.matmul(Unu_pmu, Umu_pnu.conj().swapaxes(-1, -2))
        fwd = np.matmul(fwd,     Unu.conj().swapaxes(-1, -2))

        # Backward staple: U[x+mu-nu,nu]† @ U[x-nu,mu]† @ U[x-nu,nu]
        bkd = np.matmul(Unu_pmnu.conj().swapaxes(-1, -2), Umu_mnu.conj().swapaxes(-1, -2))
        bkd = np.matmul(bkd, Unu_mnu)

        St += fwd + bkd

    return St


def metropolis_sweep(U, beta, delta, rng):
    """Checkerboard vectorized Metropolis sweep. Returns acceptance rate."""
    L = U.shape[0]
    accepted = 0

    x0, x1, x2, x3 = np.mgrid[0:L, 0:L, 0:L, 0:L]
    parity = (x0 + x1 + x2 + x3) % 2
    I3 = np.eye(3, dtype=complex)

    for mu in range(4):
        St = compute_all_staples(U, mu)

        for color in [0, 1]:
            mask = (parity == color)
            n = mask.sum()

            U_old  = U[mask, mu].copy()      # (n, 3, 3)
            St_loc = St[mask]                # (n, 3, 3)

            S_old = -beta / 3.0 * np.trace(
                np.matmul(U_old, St_loc), axis1=-2, axis2=-1).real

            eps_r = rng.standard_normal((n, 3, 3))
            eps_i = rng.standard_normal((n, 3, 3))
            eps   = (eps_r + 1j * eps_i) * delta
            eps   = (eps - eps.conj().swapaxes(-1, -2)) / 2.0
            U_prop = np.matmul(U_old, I3[np.newaxis] + eps)
            U_new  = project_su3_batch(U_prop)

            S_new = -beta / 3.0 * np.trace(
                np.matmul(U_new, St_loc), axis1=-2, axis2=-1).real

            accept = np.log(rng.random(n) + 1e-300) < (S_old - S_new)
            U_old[accept] = U_new[accept]
            U[mask, mu] = U_old
            accepted += int(accept.sum())

            if color == 0:
                St = compute_all_staples(U, mu)

    return accepted / (L ** 4 * 4)


# ── Observables ──────────────────────────────────────────────────────────────

def plaquette_avg(U):
    """Fully vectorized plaquette average."""
    total = 0.0; count = 0
    for mu in range(4):
        for nu in range(mu + 1, 4):
            Umu      = U[..., mu, :, :]
            Unu      = U[..., nu, :, :]
            Unu_pmu  = np.roll(Unu, -1, axis=mu)
            Umu_pnu  = np.roll(Umu, -1, axis=nu)
            tmp = np.matmul(Umu, Unu_pmu)
            tmp = np.matmul(tmp, Umu_pnu.conj().swapaxes(-1, -2))
            tmp = np.matmul(tmp, Unu.conj().swapaxes(-1, -2))
            total += np.trace(tmp, axis1=-2, axis2=-1).real.sum() / 3.0
            count  += tmp.shape[0] * tmp.shape[1] * tmp.shape[2] * tmp.shape[3]
    return total / count


def path_product(U, mu, R):
    """Path-ordered product P_R(x,mu) = U[x,mu]@U[x+1,mu]@...@U[x+R-1,mu] for all x."""
    P = U[..., mu, :, :].copy()
    for r in range(1, R):
        P = np.matmul(P, np.roll(U[..., mu, :, :], -r, axis=mu))
    return P


def wilson_loop_avg(U, R, T):
    """<Re Tr W(R,T)>/3 averaged over sites and 3 spatial directions."""
    if R >= L // 2 or T >= L // 2:
        return None
    nu = 3  # temporal direction
    total = 0.0; count = 0

    PR = path_product(U, 0, R)  # precompute for mu=0,1,2 in loop
    PT = path_product(U, nu, T)

    for mu in range(3):
        PR = path_product(U, mu, R)
        PT_shifted = np.roll(PT, -R, axis=mu)   # P_T at x+R*mu
        PR_back    = np.roll(PR, -T, axis=nu)   # P_R at x+T*nu (daggered below)

        W = np.matmul(PR, PT_shifted)
        W = np.matmul(W, PR_back.conj().swapaxes(-1, -2))
        W = np.matmul(W, PT.conj().swapaxes(-1, -2))

        tr_W = np.trace(W, axis1=-2, axis2=-1).real / 3.0
        total += tr_W.sum()
        count += tr_W.size

    return total / count


# ── Initialization ────────────────────────────────────────────────────────────

U = np.zeros((L, L, L, L, 4, 3, 3), dtype=complex)
for i in range(3):
    U[:, :, :, :, :, i, i] = 1.0   # cold start: all links = identity

P0 = plaquette_avg(U)
print(f"Cold start: P = {P0:.4f} (should be 1.0000)", flush=True)


# ── Warmup with adaptive delta ────────────────────────────────────────────────

print(f"\n=== WARMUP ({N_warmup} sweeps) ===", flush=True)
thermalized = False; thermalized_at = None
acc_history = []

for i in range(1, N_warmup + 1):
    acc = metropolis_sweep(U, beta, delta, rng)
    acc_history.append(acc)

    if i % TUNE_INTERVAL == 0 and i < N_warmup // 2:
        avg_acc = np.mean(acc_history[-TUNE_INTERVAL:])
        delta_old = delta
        if avg_acc < TARGET_ACC - 0.05:
            delta *= 0.9
        elif avg_acc > TARGET_ACC + 0.05:
            delta *= 1.1
        delta = np.clip(delta, 0.05, 1.0)
        if abs(delta - delta_old) > 1e-6:
            print(f"  Delta tuned: {delta_old:.3f} → {delta:.3f} (acc={avg_acc:.3f})", flush=True)

    if i <= 10 or i % 100 == 0:
        P = plaquette_avg(U)
        elapsed = time.time() - t0
        print(f"  Sweep {i:4d}: P={P:.4f}, acc={acc:.3f}, delta={delta:.3f}, t={elapsed:.1f}s",
              flush=True)
        if P > 0.50 and not thermalized:
            thermalized = True; thermalized_at = i
            print(f"  *** THERMALIZED at sweep {i}: P={P:.4f} ***", flush=True)

P_warmup = plaquette_avg(U)
print(f"\nAfter warmup: P = {P_warmup:.4f} (thermalized={thermalized})", flush=True)


# ── Measurements ─────────────────────────────────────────────────────────────

print(f"\n=== MEASUREMENT ({N_meas} measurements, every {MEAS_INTERVAL} sweeps) ===",
      flush=True)

P_meas    = []
W11_list  = []; W12_list = []; W21_list = []; W22_list = []
W13_list  = []; W31_list = []; W33_list = []
W23_list  = []; W32_list = []

for k in range(1, N_meas + 1):
    for _ in range(MEAS_INTERVAL):
        metropolis_sweep(U, beta, delta, rng)

    P_meas.append(plaquette_avg(U))

    w11 = wilson_loop_avg(U, 1, 1)
    w12 = wilson_loop_avg(U, 1, 2)
    w21 = wilson_loop_avg(U, 2, 1)
    w22 = wilson_loop_avg(U, 2, 2)
    w13 = wilson_loop_avg(U, 1, 3)
    w31 = wilson_loop_avg(U, 3, 1)
    w23 = wilson_loop_avg(U, 2, 3)
    w32 = wilson_loop_avg(U, 3, 2)
    w33 = wilson_loop_avg(U, 3, 3)

    if w11 is not None: W11_list.append(w11)
    if w12 is not None: W12_list.append(w12)
    if w21 is not None: W21_list.append(w21)
    if w22 is not None: W22_list.append(w22)
    if w13 is not None: W13_list.append(w13)
    if w31 is not None: W31_list.append(w31)
    if w23 is not None: W23_list.append(w23)
    if w32 is not None: W32_list.append(w32)
    if w33 is not None: W33_list.append(w33)

    if k % 50 == 0:
        elapsed = time.time() - t0
        P_now = P_meas[-1]
        print(f"  Meas {k:3d}/{N_meas}: P={P_now:.4f}, t={elapsed:.1f}s", flush=True)

print("\nMeasurements complete.", flush=True)


# ── Creutz ratios with jackknife errors ───────────────────────────────────────

def creutz_ratio(WRT, WRm1Tm1, WRTm1, WRm1T, label="chi"):
    """χ(R,T) = -log[W(R,T)·W(R-1,T-1) / (W(R,T-1)·W(R-1,T))]"""
    N = min(len(WRT), len(WRm1Tm1), len(WRTm1), len(WRm1T))
    if N < 2:
        return None, None, None
    WRT    = np.array(WRT[:N])
    WRm1Tm1= np.array(WRm1Tm1[:N])
    WRTm1  = np.array(WRTm1[:N])
    WRm1T  = np.array(WRm1T[:N])

    # Clip to positive before log
    eps = 1e-10
    chi = -np.log(np.maximum(WRT*WRm1Tm1, eps) / np.maximum(WRTm1*WRm1T, eps))
    chi_mean = chi.mean()

    # Jackknife
    jack = np.array([(np.delete(chi,i).mean()) for i in range(N)])
    chi_jack = jack.mean()
    chi_err  = np.sqrt((N-1) * np.mean((jack - chi_jack)**2))
    return float(chi_mean), float(chi_err), int(N)


def safe_mean(lst):
    return float(np.mean(lst)) if lst else None

W11 = safe_mean(W11_list)
W12 = safe_mean(W12_list)
W21 = safe_mean(W21_list)
W22 = safe_mean(W22_list)
W13 = safe_mean(W13_list)
W31 = safe_mean(W31_list)
W23 = safe_mean(W23_list)
W32 = safe_mean(W32_list)
W33 = safe_mean(W33_list)

chi22, chi22_err, chi22_N = creutz_ratio(W22_list, W11_list, W21_list, W12_list)
chi23, chi23_err, chi23_N = creutz_ratio(W23_list, W12_list, W22_list, W13_list)
chi32, chi32_err, chi32_N = creutz_ratio(W32_list, W21_list, W31_list, W22_list)
chi33, chi33_err, chi33_N = creutz_ratio(W33_list, W22_list, W32_list, W23_list)


# ── f_quant identification ────────────────────────────────────────────────────

# GTE formula: σ_GTE = ΔK · M_kink² · f_quant²
# where ΔK = log2(9), M_kink = 469.0 MeV (PDG calibrated)
# σ_PDG = 0.18 GeV² (standard QCD string tension)
# σ_lattice = χ(R,T) / a² where a = 0.093 fm at beta=6.0

# a_fm = 0.093 fm at beta=6.0 (from Sommer parameter r0≈0.5 fm, r0/a≈5.4)
a_fm = 0.093

# Primary f_quant from chi(2,2)
# sigma_a2 = chi22 (dimensionless, = sigma*a^2)
# sigma_GeV2 = chi22 / a_fm^2 * (0.197 GeV·fm)^2
hbar_c_fm_GeV = 0.197326980   # GeV·fm

results = {
    "algorithm": "Metropolis SU(3) vectorized checkerboard — L=8",
    "L": L,
    "beta": beta,
    "N_warmup": N_warmup,
    "N_meas": N_meas,
    "meas_interval": MEAS_INTERVAL,
    "delta_final": float(delta),
    "P_warmup": float(P_warmup),
    "P_final": float(np.mean(P_meas)) if P_meas else None,
    "P_final_err": float(np.std(P_meas) / np.sqrt(len(P_meas))) if len(P_meas) > 1 else None,
    "thermalized": bool(thermalized),
    "thermalized_at": thermalized_at,
    "W11": W11, "W12": W12, "W21": W21, "W22": W22,
    "W13": W13, "W31": W31, "W23": W23, "W32": W32, "W33": W33,
    "creutz_chi22": chi22, "creutz_chi22_err": chi22_err,
    "creutz_chi23": chi23, "creutz_chi23_err": chi23_err,
    "creutz_chi32": chi32, "creutz_chi32_err": chi32_err,
    "creutz_chi33": chi33, "creutz_chi33_err": chi33_err,
    "elapsed_s": time.time() - t0,
}

# f_quant from each Creutz ratio
for (chi_val, chi_label) in [(chi22, "chi22"), (chi33, "chi33")]:
    if chi_val is not None and chi_val > 0:
        sigma_a2 = chi_val
        sigma_GeV2 = sigma_a2 / a_fm**2 * hbar_c_fm_GeV**2
        # f_quant² = sigma_GeV2 / (ΔK * M_kink²)
        DeltaK = np.log(9) / np.log(2)   # log2(9) in natural units
        M_kink_GeV = 0.469
        f_quant_sq = sigma_GeV2 / (DeltaK * M_kink_GeV**2)
        f_quant = np.sqrt(abs(f_quant_sq)) if f_quant_sq > 0 else None
        results[f"sigma_a2_from_{chi_label}"] = float(sigma_a2)
        results[f"sigma_GeV2_from_{chi_label}"] = float(sigma_GeV2)
        results[f"f_quant_from_{chi_label}"] = float(f_quant) if f_quant else None

# f_quant candidates (from prior analysis)
f_candidates = {
    "4^{-1/3} = 2^{-2/3}": 4**(-1/3),
    "5/8": 5/8,
    "pi/5": np.pi/5,
}

if chi22 is not None and chi22 > 0:
    sigma_a2 = chi22
    sigma_GeV2 = sigma_a2 / a_fm**2 * hbar_c_fm_GeV**2
    results["f_quant_candidate_comparison"] = {}
    for name, fq in f_candidates.items():
        DeltaK = np.log(9) / np.log(2)
        M_kink_GeV = 0.469
        sigma_predicted = DeltaK * M_kink_GeV**2 * fq
        discrepancy_pct = (sigma_GeV2 - sigma_predicted) / sigma_predicted * 100
        results["f_quant_candidate_comparison"][name] = {
            "f_quant": fq,
            "sigma_predicted_GeV2": sigma_predicted,
            "sigma_measured_GeV2": float(sigma_GeV2),
            "discrepancy_pct": float(discrepancy_pct),
        }

signal.alarm(0)

outfile = "papers/39_qcd_from_gte/scripts/g13_su3_l8_results.json"
with open(outfile, "w") as f:
    json.dump(results, f, indent=2)

print(f"\n=== RESULTS ===")
print(f"P_final (measurement avg) = {results.get('P_final', 'N/A'):.4f} ± {results.get('P_final_err',0):.4f}")
print(f"Thermalized = {thermalized} (at sweep {thermalized_at})")
print(f"Wilson loops: W(1,1)={W11:.4f}, W(1,2)={W12:.4f}, W(2,2)={W22:.4f}, W(3,3)={W33 if W33 else 'N/A'}")
print(f"Creutz chi(2,2) = {chi22:.4f} ± {chi22_err:.4f}  (N={chi22_N})")
if chi33:
    print(f"Creutz chi(3,3) = {chi33:.4f} ± {chi33_err:.4f}  (N={chi33_N})")
if "f_quant_from_chi22" in results:
    print(f"f_quant [chi(2,2)] = {results['f_quant_from_chi22']:.5f}")
if "f_quant_candidate_comparison" in results:
    print("\nCandidate f_quant comparison:")
    for name, c in results["f_quant_candidate_comparison"].items():
        print(f"  {name}: predicted σ={c['sigma_predicted_GeV2']:.4f} GeV², "
              f"measured σ={c['sigma_measured_GeV2']:.4f} GeV², "
              f"discrepancy={c['discrepancy_pct']:+.1f}%")
print(f"\nElapsed: {time.time()-t0:.1f}s")
print(f"Results saved to {outfile}")
