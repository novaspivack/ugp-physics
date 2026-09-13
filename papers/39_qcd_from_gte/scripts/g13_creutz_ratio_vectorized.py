"""
G13: SU(3) Metropolis on 4^4 lattice — corrected Creutz ratio measurement.

Correct staple formulas (plaquette P(x,μ,ν) = U[x,μ] U[x+μ,ν] U[x+ν,μ]† U[x,ν]†):
  Forward staple:  U[x+μ, ν] @ U[x+ν, μ]† @ U[x, ν]†
  Backward staple: U[x+μ-ν, ν]† @ U[x-ν, μ]† @ U[x-ν, ν]

Previous implementations had a bug: used U[x+μ+ν, μ]† @ U[x+ν, ν]† (wrong positions).
"""
import numpy as np
import json, signal, sys, time

TIMEOUT_SECONDS = 470

def _timeout_handler(s, f):
    print(f"\nTIMEOUT after {TIMEOUT_SECONDS}s. Saving partial results.")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

np.random.seed(42)

L = 4
beta = 6.0
N_warmup = 300
N_meas = 40
delta = 0.15    # Metropolis step size (tuned for ~50% acceptance)
MEAS_INTERVAL = 3

t0 = time.time()


def project_su3(V):
    """Project 3x3 matrix to SU(3) via Gram-Schmidt + correct cross-product third column.

    For complex SU(3): v2_i = ε_{ijk} (v0*)_j (v1*)_k = np.cross(v0.conj(), v1.conj())
    The final .conj() must NOT be present — that reverts to the wrong bilinear formula.
    """
    v0 = V[:, 0].copy()
    v0 /= np.linalg.norm(v0)
    v1 = V[:, 1] - np.dot(v0.conj(), V[:, 1]) * v0
    v1 /= np.linalg.norm(v1)
    v2 = np.cross(v0.conj(), v1.conj())   # SU(3): ε_{ijk} (v0*)_j (v1*)_k, no extra conj
    return np.column_stack([v0, v1, v2])


# ── Storage: U[x0,x1,x2,x3,mu] = 3×3 complex SU(3) matrix ──────────────────
# Shape: (L, L, L, L, 4, 3, 3)
U = np.zeros((L, L, L, L, 4, 3, 3), dtype=complex)
for mu in range(4):
    U[:, :, :, :, mu] = np.eye(3)  # cold start

_e = np.eye(4, dtype=int)   # unit vectors in 4 directions


def compute_staple(U, x0, x1, x2, x3, mu):
    """Correct staple sum for link (x, mu).

    S_link = -(β/3) Re Tr[U[x,μ] @ staple], so staple = Σ_{ν≠μ}(Σ_ν^+ + Σ_ν^-)
      Forward:  Σ_ν^+ = U[x+μ,ν] @ U[x+ν,μ]† @ U[x,ν]†
      Backward: Σ_ν^- = U[x+μ-ν,ν]† @ U[x-ν,μ]† @ U[x-ν,ν]
    """
    L = U.shape[0]
    x = np.array([x0, x1, x2, x3])
    St = np.zeros((3, 3), dtype=complex)

    for nu in range(4):
        if nu == mu:
            continue

        xmu   = tuple((x + _e[mu]) % L)
        xnu   = tuple((x + _e[nu]) % L)
        xmnu  = tuple((x - _e[nu]) % L)
        xpmnu = tuple((x + _e[mu] - _e[nu]) % L)

        # Forward staple: U[x+μ,ν] @ U[x+ν,μ]† @ U[x,ν]†
        St += U[xmu][nu] @ U[xnu][mu].conj().T @ U[x0, x1, x2, x3, nu].conj().T

        # Backward staple: U[x+μ-ν,ν]† @ U[x-ν,μ]† @ U[x-ν,ν]
        St += U[xpmnu][nu].conj().T @ U[xmnu][mu].conj().T @ U[xmnu][nu]

    return St


def metropolis_sweep(U, beta, delta):
    L = U.shape[0]
    accepted = 0
    total = L ** 4 * 4
    I3 = np.eye(3, dtype=complex)

    for x0 in range(L):
        for x1 in range(L):
            for x2 in range(L):
                for x3 in range(L):
                    for mu in range(4):
                        U_old = U[x0, x1, x2, x3, mu]
                        St = compute_staple(U, x0, x1, x2, x3, mu)
                        S_old = -beta / 3.0 * np.trace(U_old @ St).real

                        # Propose: U_old @ exp(i·ε) with anti-Hermitian ε
                        eps = (np.random.randn(3, 3) + 1j * np.random.randn(3, 3)) * delta
                        eps = (eps - eps.conj().T) / 2.0
                        U_prop = U_old @ (I3 + eps)
                        U_new = project_su3(U_prop)

                        S_new = -beta / 3.0 * np.trace(U_new @ St).real

                        if np.log(np.random.rand() + 1e-300) < S_old - S_new:
                            U[x0, x1, x2, x3, mu] = U_new
                            accepted += 1

    return accepted / total


def plaquette_avg(U):
    """Vectorized correct plaquette: Tr[U[x,μ] U[x+μ,ν] U[x+ν,μ]† U[x,ν]†] / 3."""
    total = 0.0
    count = 0

    for mu in range(4):
        for nu in range(mu + 1, 4):
            Umu = U[:, :, :, :, mu]          # (L,L,L,L,3,3)
            Unu = U[:, :, :, :, nu]
            Unu_pmu = np.roll(Unu, -1, axis=mu)   # U[x+μ, ν]
            Umu_pnu = np.roll(Umu, -1, axis=nu)    # U[x+ν, μ]

            # P = U[x,μ] @ U[x+μ,ν] @ U[x+ν,μ]† @ U[x,ν]†
            tmp = np.matmul(Umu, Unu_pmu)
            tmp = np.matmul(tmp, Umu_pnu.conj().swapaxes(-1, -2))
            tmp = np.matmul(tmp, Unu.conj().swapaxes(-1, -2))

            P_sites = np.trace(tmp, axis1=-2, axis2=-1).real / 3.0
            total += P_sites.sum()
            count += P_sites.size

    return total / count


def wilson_loop_avg(U, R, T):
    """<Re Tr W(R,T)> / 3: R spatial, T temporal, averaged over sites and spatial planes."""
    L = U.shape[0]
    if R >= L or T >= L:
        return None

    total = 0.0
    count = 0
    nu = 3  # temporal direction

    for mu in range(3):  # spatial directions
        for x0 in range(L):
            for x1 in range(L):
                for x2 in range(L):
                    for x3 in range(L):
                        xc = [x0, x1, x2, x3]
                        W = np.eye(3, dtype=complex)

                        for _ in range(R):
                            W = W @ U[xc[0], xc[1], xc[2], xc[3], mu]
                            xc[mu] = (xc[mu] + 1) % L
                        for _ in range(T):
                            W = W @ U[xc[0], xc[1], xc[2], xc[3], nu]
                            xc[nu] = (xc[nu] + 1) % L
                        for _ in range(R):
                            xc[mu] = (xc[mu] - 1) % L
                            W = W @ U[xc[0], xc[1], xc[2], xc[3], mu].conj().T
                        for _ in range(T):
                            xc[nu] = (xc[nu] - 1) % L
                            W = W @ U[xc[0], xc[1], xc[2], xc[3], nu].conj().T

                        total += np.trace(W).real / 3.0
                        count += 1

    return total / count if count > 0 else None


# ── Initial state check ──────────────────────────────────────────────────────
P0 = plaquette_avg(U)
print(f"Cold start L={L}, β={beta}: P = {P0:.4f} (should be 1.0000)")

# ── Warmup ───────────────────────────────────────────────────────────────────
print(f"\nWarmup ({N_warmup} sweeps, δ={delta})...")
thermalized = False
thermalized_at = None

for i in range(1, N_warmup + 1):
    acc = metropolis_sweep(U, beta, delta)

    if i <= 10 or i % 50 == 0:
        P = plaquette_avg(U)
        elapsed = time.time() - t0
        print(f"  Sweep {i:3d}: P={P:.4f}, acc={acc:.3f}, t={elapsed:.0f}s")
        if P > 0.50 and not thermalized:
            thermalized = True
            thermalized_at = i
            print(f"  *** THERMALIZED at sweep {i}! P={P:.4f} ***")

    if time.time() - t0 > 420:
        print("Wall-clock limit in warmup. Stopping early.")
        break

P_final = plaquette_avg(U)
thermalized = P_final > 0.50
print(f"\nAfter warmup: P = {P_final:.4f}  (thermalized={thermalized})")

# ── Wilson loop measurements ─────────────────────────────────────────────────
W11_list, W12_list, W21_list, W22_list = [], [], [], []
creutz_chi22 = None
W11 = W12 = W21 = W22 = None

if thermalized:
    print(f"\nMeasurements ({N_meas} configs, every {MEAS_INTERVAL} sweeps)...")
    t_meas = time.time()

    for i in range(N_meas):
        if time.time() - t0 > 455:
            print(f"  Wall-clock limit at measurement {i}. Stopping.")
            break

        for _ in range(MEAS_INTERVAL):
            metropolis_sweep(U, beta, delta)

        w11 = wilson_loop_avg(U, 1, 1)
        w12 = wilson_loop_avg(U, 1, 2)
        w21 = wilson_loop_avg(U, 2, 1)
        w22 = wilson_loop_avg(U, 2, 2)

        if w11 is not None:
            W11_list.append(w11)
            W12_list.append(w12)
            W21_list.append(w21)
            W22_list.append(w22)

        if i % 10 == 0:
            print(f"  Meas {i:2d}: W(1,1)={w11:.5f}, W(2,2)={w22:.5f}, t={time.time()-t0:.0f}s")

    if W11_list:
        W11 = float(np.mean(W11_list))
        W12 = float(np.mean(W12_list))
        W21 = float(np.mean(W21_list))
        W22 = float(np.mean(W22_list))

        denom = W21 * W12
        numer = W22 * W11
        if denom > 0 and numer > 0:
            creutz_chi22 = float(-np.log(numer / denom))

        f_quant = 4.0 ** (-1.0 / 3.0)
        sigma_fq = float(-np.log(f_quant))  # = log(4)/3 ≈ 0.4621

        print(f"\n=== Results ===")
        print(f"P_final          = {P_final:.5f}  (target ~0.56 for β=6 L=4)")
        print(f"W(1,1) = {W11:.5f}")
        print(f"W(1,2) = {W12:.5f}")
        print(f"W(2,1) = {W21:.5f}")
        print(f"W(2,2) = {W22:.5f}")
        if creutz_chi22 is not None:
            print(f"Creutz χ(2,2)    = {creutz_chi22:.5f}")
            print(f"σ_lattice(f_quant=4^-1/3) = {sigma_fq:.5f}")
            print(f"Discrepancy      = {abs(creutz_chi22 - sigma_fq) / sigma_fq * 100:.2f}%")
            print(f"f_quant = 4^(-1/3) = {f_quant:.6f}")
        print(f"N_configs = {len(W11_list)}")

# ── Save results ─────────────────────────────────────────────────────────────
results = {
    "algorithm": "Metropolis SU(3) — corrected staple (2026-05-29)",
    "L": L,
    "beta": beta,
    "N_warmup": N_warmup,
    "delta": delta,
    "N_meas": len(W11_list),
    "P_final": float(P_final),
    "thermalized": bool(thermalized),
    "thermalized_at": thermalized_at,
    "W11": W11,
    "W12": W12,
    "W21": W21,
    "W22": W22,
    "creutz_chi22": creutz_chi22,
    "f_quant_4m1o3": float(4.0 ** (-1.0 / 3.0)),
    "sigma_lattice_from_fquant": float(-np.log(4.0 ** (-1.0 / 3.0))),
    "elapsed_s": float(time.time() - t0),
}

out_path = "papers/39_qcd_from_gte/scripts/g13_creutz_ratio_vectorized_results.json"
with open(out_path, "w") as f:
    json.dump(results, f, indent=2)
print(f"\nSaved to {out_path}")
signal.alarm(0)
