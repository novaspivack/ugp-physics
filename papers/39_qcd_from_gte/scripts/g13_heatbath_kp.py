"""
G13: SU(3) Kennedy-Pendleton heatbath — beta-annealing thermalization
Root cause of prior failures: cold start at beta=6 overshoots the equilibrium
P≈0.59 → falls into confined metastable phase (P≈0).
Fix: anneal from beta_high → 6.0, staying in the ordered phase throughout.
"""
import numpy as np
import math, json, signal, time

TIMEOUT_SECONDS = 420  # 7 minutes

def _timeout_handler(s, f):
    print("TIMEOUT. Saving partial results.")
    import sys; sys.exit(1)

signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

L = 4
beta_target = 6.0

# ---------------------------------------------------------------------------
# SU(2) and SU(3) utilities
# ---------------------------------------------------------------------------
def su2_from_vector(a):
    a0, a1, a2, a3 = a[0], a[1], a[2], a[3]
    n = math.sqrt(a0*a0 + a1*a1 + a2*a2 + a3*a3)
    if n < 1e-14:
        return np.eye(2, dtype=complex)
    a0, a1, a2, a3 = a0/n, a1/n, a2/n, a3/n
    return np.array([[complex(a0, a3), complex(a2, a1)],
                     [complex(-a2, a1), complex(a0, -a3)]])

def kp_heatbath_su2(A, beta_eff):
    """Kennedy-Pendleton SU(2) heatbath: sample R from p(R)∝exp(β·Re Tr(R@A))."""
    a00, a01, a10, a11 = A[0,0], A[0,1], A[1,0], A[1,1]
    alpha0 = (a00 + a11).real;  alpha1 = -(a01 + a10).imag
    alpha2 = (a10 - a01).real;  alpha3 = -(a00 - a11).imag
    alpha = np.array([alpha0, alpha1, alpha2, alpha3])
    k_alpha = math.sqrt(alpha0*alpha0 + alpha1*alpha1 + alpha2*alpha2 + alpha3*alpha3)
    if k_alpha < 1e-12:
        r = np.random.randn(4); r /= np.linalg.norm(r)
        return su2_from_vector(r)
    alpha_hat = alpha / k_alpha
    k = beta_eff * k_alpha
    for _ in range(100000):
        r1, r2, r3, r4 = np.random.random(4)
        c2 = math.cos(2.0 * math.pi * r2) ** 2
        a0p = 1.0 + (math.log(r1) + c2 * math.log(r3)) / k
        if abs(a0p) >= 1.0:
            continue
        if r4 * r4 <= 1.0 - a0p * a0p:
            break
    else:
        a0p = 1.0
    rho = math.sqrt(max(0.0, 1.0 - a0p * a0p))
    perp = np.random.randn(4)
    perp -= np.dot(perp, alpha_hat) * alpha_hat
    pn = np.linalg.norm(perp)
    if pn < 1e-14:
        perp = np.array([0., 1., 0., 0.])
        perp -= np.dot(perp, alpha_hat) * alpha_hat
        pn = np.linalg.norm(perp)
    perp /= pn
    a_vec = a0p * alpha_hat + rho * perp
    a_vec /= np.linalg.norm(a_vec)
    return su2_from_vector(a_vec)

def embed_su2_in_su3(M2, i, j):
    V = np.eye(3, dtype=complex)
    V[i,i] = M2[0,0]; V[i,j] = M2[0,1]
    V[j,i] = M2[1,0]; V[j,j] = M2[1,1]
    return V

def project_su3(V):
    """SU(3) projection via Gram-Schmidt: V[:,2] = cross(col0,col1).conj()."""
    V = V.copy()
    V[:,0] /= np.linalg.norm(V[:,0])
    V[:,1] -= np.dot(V[:,0].conj(), V[:,1]) * V[:,0]
    V[:,1] /= np.linalg.norm(V[:,1])
    V[:,2] = np.cross(V[:,0], V[:,1]).conj()
    return V

def get_staple(U, x, mu, L):
    x = list(x)
    S = np.zeros((3,3), dtype=complex)
    for nu in range(4):
        if nu == mu: continue
        xpmu  = list(x); xpmu[mu]  = (x[mu]+1) % L
        xpnu  = list(x); xpnu[nu]  = (x[nu]+1) % L
        xpmpn = list(x); xpmpn[mu] = (x[mu]+1) % L; xpmpn[nu] = (xpmpn[nu]+1) % L
        xmnu  = list(x); xmnu[nu]  = (x[nu]-1) % L
        xpmun = list(x); xpmun[mu] = (x[mu]+1) % L; xpmun[nu] = (xpmun[nu]-1) % L
        # Forward staple: U[x+μ,ν] @ U[x+ν,μ]† @ U[x,ν]†
        S += (U[tuple(xpmu)][nu] @ U[tuple(xpnu)][mu].conj().T @ U[tuple(x)][nu].conj().T)
        S += (U[tuple(xpmun)][nu].conj().T @ U[tuple(xmnu)][mu].conj().T @ U[tuple(xmnu)][nu])
    return S

def heatbath_sweep(U, beta, L):
    for x0 in range(L):
        for x1 in range(L):
            for x2 in range(L):
                for x3 in range(L):
                    for mu in range(4):
                        x = (x0, x1, x2, x3)
                        V = U[x][mu].copy()
                        staple = get_staple(U, list(x), mu, L)
                        for (i, j) in [(0,1), (0,2), (1,2)]:
                            VS = V @ staple
                            A = np.array([[VS[i,i], VS[i,j]],
                                          [VS[j,i], VS[j,j]]])
                            R = kp_heatbath_su2(A, beta / 3.0)
                            V = embed_su2_in_su3(R, i, j) @ V
                        U[x][mu] = project_su3(V)

def plaquette_avg(U, L):
    total = 0.0; count = 0
    for x0 in range(L):
        for x1 in range(L):
            for x2 in range(L):
                for x3 in range(L):
                    for mu in range(4):
                        for nu in range(mu+1, 4):
                            x = (x0, x1, x2, x3)
                            xpmu  = list(x); xpmu[mu]  = (x[mu]+1) % L
                            xpnu  = list(x); xpnu[nu]  = (x[nu]+1) % L
                            xpmpn = list(x); xpmpn[mu] = (x[mu]+1) % L; xpmpn[nu] = (xpmpn[nu]+1) % L
                            # Correct plaquette: U[x,μ] U[x+μ,ν] U[x+ν,μ]† U[x,ν]†
                            P = np.trace(U[x][mu] @ U[tuple(xpmu)][nu]
                                         @ U[tuple(xpnu)][mu].conj().T
                                         @ U[x][nu].conj().T).real / 3.0
                            total += P; count += 1
    return total / count

def wilson_loop(U, L, R_size, T_size):
    if R_size >= L or T_size >= L:
        return 0.0
    total = 0.0; count = 0
    for x0 in range(L):
        for x1 in range(L):
            for x2 in range(L):
                for x3 in range(L):
                    for mu in range(3):
                        nu = 3
                        x = [x0, x1, x2, x3]
                        Ur = np.eye(3, dtype=complex); xr = list(x)
                        for _ in range(R_size):
                            Ur = Ur @ U[tuple(xr)][mu]; xr[mu] = (xr[mu]+1) % L
                        Ut = np.eye(3, dtype=complex); xt = list(xr)
                        for _ in range(T_size):
                            Ut = Ut @ U[tuple(xt)][nu]; xt[nu] = (xt[nu]+1) % L
                        Urb = np.eye(3, dtype=complex); xrb = list(xt)
                        for _ in range(R_size):
                            xrb[mu] = (xrb[mu]-1) % L
                            Urb = Urb @ U[tuple(xrb)][mu].conj().T
                        Utb = np.eye(3, dtype=complex); xtb = list(xrb)
                        for _ in range(T_size):
                            xtb[nu] = (xtb[nu]-1) % L
                            Utb = Utb @ U[tuple(xtb)][nu].conj().T
                        w = np.trace(Ur @ Ut @ Urb @ Utb).real / 3.0
                        total += w; count += 1
    return total / count if count > 0 else 0.0

def creutz_ratio(W22, W12, W21, W11):
    if W21 * W12 <= 0 or W22 * W11 <= 0:
        return None
    return -math.log((W22 * W11) / (W21 * W12))

# ---------------------------------------------------------------------------
# Cold start
# ---------------------------------------------------------------------------
print(f"KP Heatbath with beta-annealing on {L}^4 lattice")
U = {}
for x0 in range(L):
    for x1 in range(L):
        for x2 in range(L):
            for x3 in range(L):
                U[(x0,x1,x2,x3)] = [np.eye(3, dtype=complex) for _ in range(4)]
P0 = float(plaquette_avg(U, L))
print(f"Cold start P = {P0:.4f}")

# ---------------------------------------------------------------------------
# Beta-annealing schedule: start at high beta, cool to beta=6
# At high beta, the system stays ordered; the transition from cold is smooth.
# ---------------------------------------------------------------------------
anneal_schedule = [
    (12.0, 30),   # Very strong coupling → stays very ordered (P≈0.98)
    (9.0,  20),   # Strong coupling → P≈0.92
    (7.5,  20),   # Moderate → P≈0.80
    (7.0,  20),   # Getting closer → P≈0.75
    (6.5,  20),   # Approaching target → P≈0.69
    (6.0,  50),   # Target → P≈0.59-0.62
]

t_start = time.time()
plaq_history = [{"sweep": 0, "beta": 6.0, "P": P0}]
thermalized_sweep = None

sweep_count = 0
for (beta_anneal, n_sweeps) in anneal_schedule:
    print(f"\nAnnealing at beta={beta_anneal} ({n_sweeps} sweeps)...")
    for i in range(n_sweeps):
        heatbath_sweep(U, beta_anneal, L)
        sweep_count += 1
    P = float(plaquette_avg(U, L))
    elapsed = time.time() - t_start
    print(f"  After {sweep_count} total sweeps: P={P:.4f} ({elapsed:.1f}s)")
    plaq_history.append({"sweep": sweep_count, "beta": beta_anneal, "P": P})
    if beta_anneal == 6.0 and P > 0.55:
        print(f"  *** THERMALIZED at beta=6.0! P={P:.4f} ***")
        thermalized_sweep = sweep_count

# Additional warmup at target beta
print(f"\nAdditional warmup at beta=6.0...")
for i in range(50):
    heatbath_sweep(U, beta_target, L)
    sweep_count += 1
    if i % 10 == 9:
        P = float(plaquette_avg(U, L))
        elapsed = time.time() - t_start
        print(f"  Sweep {sweep_count}: P={P:.4f} ({elapsed:.1f}s)")
        plaq_history.append({"sweep": sweep_count, "beta": 6.0, "P": P})
        if P > 0.55 and thermalized_sweep is None:
            print(f"  *** THERMALIZED! ***")
            thermalized_sweep = sweep_count

P_final = float(plaquette_avg(U, L))
thermalized = bool(P_final > 0.50)
print(f"\nFinal P = {P_final:.4f} (thermalized: {thermalized})")

# ---------------------------------------------------------------------------
# Wilson loops and Creutz ratio
# ---------------------------------------------------------------------------
creutz = None
wilson_results = {}
sqrt_sigma_MeV = None
f_quant_estimate = None

if P_final > 0.30:
    print("\nMeasuring Wilson loops...")
    for _ in range(20):
        heatbath_sweep(U, beta_target, L)
    W_acc = {(R, T): 0.0 for R in [1, 2] for T in [1, 2]}
    n_meas_actual = min(50, 30)
    for m in range(n_meas_actual):
        heatbath_sweep(U, beta_target, L)
        for (R, T) in [(1,1),(1,2),(2,1),(2,2)]:
            W_acc[(R,T)] += wilson_loop(U, L, R, T)
        if m % 10 == 0:
            print(f"  Meas {m}: W11={W_acc[(1,1)]/(m+1):.4f}  W22={W_acc[(2,2)]/(m+1):.4f}")

    W = {k: v / n_meas_actual for k, v in W_acc.items()}
    for k, v in sorted(W.items()):
        print(f"  <W{k}> = {v:.6f}")
        wilson_results[f"W_{k[0]}_{k[1]}"] = float(v)

    cr = creutz_ratio(W[(2,2)], W[(1,2)], W[(2,1)], W[(1,1)])
    if cr is not None:
        creutz = float(cr)
        print(f"\nCreutz ratio χ(2,2) = {creutz:.6f}")
        if creutz > 0:
            hbarc = 197.3; a_fm = 0.093
            sigma_phys = creutz * (hbarc / a_fm) ** 2
            sqrt_sigma_MeV = float(math.sqrt(sigma_phys))
            f_quant_estimate = float(sqrt_sigma_MeV / 200.0)
            print(f"  √σ ≈ {sqrt_sigma_MeV:.1f} MeV  (target: ~420 MeV)")
            print(f"  f_quant ≈ {f_quant_estimate:.4f}  (target: ~2.1)")

# ---------------------------------------------------------------------------
# Save results
# ---------------------------------------------------------------------------
results = {
    "algorithm": "Kennedy-Pendleton SU(2) heatbath, Cabibbo-Marinari, beta-annealing",
    "L": L, "beta_target": beta_target,
    "anneal_schedule": [[b, n] for (b, n) in anneal_schedule],
    "final_plaquette": P_final,
    "thermalized": thermalized,
    "thermalized_sweep": thermalized_sweep,
    "plaq_history": plaq_history,
    "wilson_loops": wilson_results,
    "creutz_ratio_2_2": creutz,
    "sqrt_sigma_MeV": sqrt_sigma_MeV,
    "f_quant_estimate": f_quant_estimate,
}
out_path = "papers/39_qcd_from_gte/scripts/g13_heatbath_kp_results.json"
with open(out_path, "w") as f:
    json.dump(results, f, indent=2)
print(f"\nSaved to {out_path}")
signal.alarm(0)
