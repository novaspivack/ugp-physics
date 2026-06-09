"""
G13: SU(3) Wilson loop Metropolis simulation
Strategy: 4^4 lattice, cold start, beta=6.0
Cold start thermalizes from P=1 → P≈0.615 in ~100 sweeps (much faster than hot start).
Goals: measure Creutz ratios chi(2,1) and chi(2,2) to estimate sigma*a^2,
then extract sigma in GeV^2 using m_kink calibration from GTE.
"""
import numpy as np
import math, json, signal, time, sys

TIMEOUT_SECONDS = 480  # 8 minutes max

_partial_results = {}
_wl_data = {"W11": [], "W22": [], "W21": [], "W12": []}


def _save_and_exit(label):
    n = len(_wl_data["W11"])
    if n > 0:
        W11 = float(np.mean(_wl_data["W11"]))
        W22 = float(np.mean(_wl_data["W22"]))
        W21 = float(np.mean(_wl_data["W21"]))
        _partial_results.update({
            "status": label,
            "n_measurements": n,
            "W_11": W11, "W_22": W22, "W_21": W21,
        })
        if W22 > 0 and W11 > 0 and W21 > 0:
            _partial_results["chi_sq"] = -math.log(W22 * W11 / W21 ** 2)
    else:
        _partial_results["status"] = label
    out = "papers/39_qcd_from_gte/scripts/g13_metropolis_results.json"
    with open(out, "w") as fh:
        json.dump(_partial_results, fh, indent=2)
    print(f"\nPartial results ({n} meas) saved to {out}")


def _timeout_handler(s, f):
    print(f"\nTIMEOUT after {TIMEOUT_SECONDS}s.")
    _save_and_exit("TIMEOUT")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

# ─── Parameters ───────────────────────────────────────────────────────────────
L = 4           # 4^4 = 256 sites — fast enough to thermalize and measure
BETA = 6.0
N_WARMUP = 300  # cold start thermalizes fast; 300 sweeps gives P very close to 0.615
N_MEAS = 200    # measurement sweeps
MEAS_EVERY = 5  # measure Wilson loops every N sweeps → 40 measurements
DELTA = 0.20    # step size: tuned for ~50% acceptance in SU(3) at beta=6

_partial_results.update({"L": L, "beta": BETA, "N_warmup": N_WARMUP,
                          "N_meas": N_MEAS, "start": "cold"})


# ─── SU(3) utilities ──────────────────────────────────────────────────────────

def project_su3(M):
    """Project a 3×3 complex matrix to the nearest SU(3) via polar decomposition."""
    U, _, Vh = np.linalg.svd(M)
    Q = U @ Vh
    det = np.linalg.det(Q)
    Q = Q / (det ** (1.0 / 3.0))
    return Q


def random_su3_near_identity(delta):
    """Generate a random SU(3) matrix near the identity (for Metropolis proposal)."""
    noise = np.random.randn(3, 3) + 1j * np.random.randn(3, 3)
    return project_su3(np.eye(3, dtype=complex) + delta * noise)


def _nbr(x, mu, sign, L):
    """Return nearest-neighbour site of x shifted by sign in direction mu."""
    xn = list(x)
    xn[mu] = (xn[mu] + sign) % L
    return tuple(xn)


# ─── Staple sum ────────────────────────────────────────────────────────────────

def staple_sum(U, x, mu, L):
    """
    Staple sum A(x,mu) such that S_local = -(beta/3) Re Tr [U(x,mu) @ A†(x,mu)].
    Equivalently, dS = -(beta/3) Re Tr [(U_new - U_old) @ A†].
    We return A so that dS = -(beta/3) Re Tr [(V_new - V) @ A†].
    
    Standard formula (each nu ≠ mu contributes two terms):
      Forward:  U(x+mu,nu) @ U(x+mu+nu,mu)† @ U(x+nu,nu)†
      Backward: U(x+mu-nu,nu)† @ U(x-nu,mu)† @ U(x-nu,nu)
    """
    A = np.zeros((3, 3), dtype=complex)
    for nu in range(4):
        if nu == mu:
            continue
        xpmu     = _nbr(x,   mu, +1, L)
        xpnu     = _nbr(x,   nu, +1, L)
        xpmupnu  = _nbr(xpmu, nu, +1, L)
        xmnu     = _nbr(x,   nu, -1, L)
        xpmumnu  = _nbr(xpmu, nu, -1, L)
        # Forward staple
        A += U[xpmu][nu] @ U[xpmupnu][mu].conj().T @ U[xpnu][nu].conj().T
        # Backward staple
        A += U[xpmumnu][nu].conj().T @ U[xmnu][mu].conj().T @ U[xmnu][nu]
    return A


# ─── Observables ───────────────────────────────────────────────────────────────

def plaquette_avg(U, L):
    """Average plaquette <(1/3) Re Tr U_P>."""
    total = 0.0
    count = 0
    for x in np.ndindex(L, L, L, L):
        for mu in range(4):
            for nu in range(mu + 1, 4):
                xpmu    = _nbr(x,   mu, +1, L)
                xpnu    = _nbr(x,   nu, +1, L)
                xpmupnu = _nbr(xpmu, nu, +1, L)
                P = np.trace(
                    U[x][mu] @ U[xpmu][nu] @
                    U[xpmupnu][mu].conj().T @ U[xpnu][nu].conj().T
                ).real / 3.0
                total += P
                count += 1
    return total / count


def wilson_loop_avg(U, I, J, L):
    """
    Average I×J rectangular Wilson loop over all sites and direction pairs (mu,nu), mu<nu.
    Returns <(1/3) Re Tr W_IJ>.
    """
    total = 0.0
    count = 0
    for x0, x1, x2, x3 in np.ndindex(L, L, L, L):
        for mu in range(4):
            for nu in range(mu + 1, 4):
                path = np.eye(3, dtype=complex)
                xc = [x0, x1, x2, x3]
                # I steps forward in mu
                for _ in range(I):
                    path = path @ U[tuple(xc)][mu]
                    xc[mu] = (xc[mu] + 1) % L
                # J steps forward in nu
                for _ in range(J):
                    path = path @ U[tuple(xc)][nu]
                    xc[nu] = (xc[nu] + 1) % L
                # I steps back in mu
                for _ in range(I):
                    xc[mu] = (xc[mu] - 1) % L
                    path = path @ U[tuple(xc)][mu].conj().T
                # J steps back in nu
                for _ in range(J):
                    xc[nu] = (xc[nu] - 1) % L
                    path = path @ U[tuple(xc)][nu].conj().T
                total += np.trace(path).real / 3.0
                count += 1
    return total / count


# ─── Metropolis sweep ─────────────────────────────────────────────────────────

def sweep(U, beta, L, delta):
    """
    One full Metropolis sweep through all links.
    Returns acceptance rate.
    """
    accepts = 0
    total = 0
    for x in np.ndindex(L, L, L, L):
        for mu in range(4):
            V = U[x][mu]
            A = staple_sum(U, x, mu, L)
            # Propose V_new = dU @ V (random SU(3) near identity times old link)
            dU = random_su3_near_identity(delta)
            V_new = dU @ V
            # Action change: dS = -(beta/3) Re Tr [(V_new - V) @ A†]
            dS = -(beta / 3.0) * np.trace((V_new - V) @ A.conj().T).real
            if dS <= 0.0 or np.random.rand() < math.exp(-dS):
                U[x][mu] = V_new
                accepts += 1
            total += 1
    return accepts / total


# ─── Initialize lattice: cold start (all links = identity) ───────────────────
np.random.seed(42)
print(f"Cold-start initialization: {L}^4 SU(3) lattice (beta={BETA})...")
t0 = time.time()
U = {}
for x in np.ndindex(L, L, L, L):
    U[x] = np.array([np.eye(3, dtype=complex)] * 4)

P_init = plaquette_avg(U, L)
print(f"  Init done in {time.time()-t0:.2f}s  |  P(cold) = {P_init:.4f}  (should be 1.0000)")
_partial_results["P_cold_start"] = P_init

# ─── Warmup ──────────────────────────────────────────────────────────────────
print(f"\nWarmup ({N_WARMUP} sweeps) — expect P to drop from 1.0 toward 0.615...")
t_warm = time.time()
for i in range(N_WARMUP):
    ar = sweep(U, BETA, L, DELTA)
    if i % 50 == 0 or i == N_WARMUP - 1:
        P = plaquette_avg(U, L)
        elapsed = time.time() - t_warm
        eta = elapsed / (i + 1) * (N_WARMUP - i - 1) if i > 0 else 0
        print(f"  sweep {i+1:4d}: P={P:.5f}  accept={ar:.3f}  "
              f"elapsed={elapsed:.0f}s  eta={eta:.0f}s")
        _partial_results["last_warmup_plaquette"] = P

print(f"  Warmup done in {time.time()-t_warm:.1f}s")

# ─── Measurement ─────────────────────────────────────────────────────────────
print(f"\nMeasurement ({N_MEAS} sweeps, loops measured every {MEAS_EVERY} sweeps)...")
P_list = []
t_meas = time.time()

for i in range(N_MEAS):
    ar = sweep(U, BETA, L, DELTA)
    if (i + 1) % MEAS_EVERY == 0:
        w11 = wilson_loop_avg(U, 1, 1, L)
        w22 = wilson_loop_avg(U, 2, 2, L)
        w21 = wilson_loop_avg(U, 2, 1, L)
        w12 = wilson_loop_avg(U, 1, 2, L)
        P   = plaquette_avg(U, L)
        _wl_data["W11"].append(w11)
        _wl_data["W22"].append(w22)
        _wl_data["W21"].append(w21)
        _wl_data["W12"].append(w12)
        P_list.append(P)
        n = len(_wl_data["W11"])
        elapsed = time.time() - t_meas
        eta = elapsed / (i + 1) * (N_MEAS - i - 1) if i > 0 else 0
        print(f"  meas {n:3d}: W(1,1)={w11:.5f}  W(2,2)={w22:.5f}  "
              f"W(2,1)={w21:.5f}  P={P:.5f}  ar={ar:.3f}  eta={eta:.0f}s")
        # Update partial results continuously
        _partial_results.update({
            "n_measurements": n,
            "W_11_running": float(np.mean(_wl_data["W11"])),
            "W_22_running": float(np.mean(_wl_data["W22"])),
            "W_21_running": float(np.mean(_wl_data["W21"])),
            "last_plaquette": P,
        })

print(f"\nMeasurement done in {time.time()-t_meas:.1f}s")
signal.alarm(0)

# ─── Compute Creutz ratios ────────────────────────────────────────────────────
W11 = float(np.mean(_wl_data["W11"]))
W22 = float(np.mean(_wl_data["W22"]))
W21 = float(np.mean(_wl_data["W21"]))
W12 = float(np.mean(_wl_data["W12"]))
W11_err = float(np.std(_wl_data["W11"]) / math.sqrt(len(_wl_data["W11"])))
W22_err = float(np.std(_wl_data["W22"]) / math.sqrt(len(_wl_data["W22"])))
W21_err = float(np.std(_wl_data["W21"]) / math.sqrt(len(_wl_data["W21"])))
W12_err = float(np.std(_wl_data["W12"]) / math.sqrt(len(_wl_data["W12"])))

# Standard Creutz ratio: chi(2,1) = -ln[ W(2,1)*W(1,1)^{-1}*W(2,2)^{0}... ]
# Most robust form uses chi(I,J) = -ln[ W(I,J)*W(I-1,J-1) / (W(I-1,J)*W(I,J-1)) ]
# For chi(2,2): W(2,2)*W(1,1) / W(2,1)^2   [symmetric form; most used]
# For chi(2,1): we need W(1,0) which we don't measure; use asymmetric approximation

# Symmetric chi(2,2):
if W22 > 0 and W11 > 0 and W21 > 0:
    chi_22 = -math.log(W22 * W11 / W21 ** 2)
else:
    chi_22 = float("nan")

# Asymmetric estimator: chi_asym = -ln[W(2,1)/W(1,1)^2] (rough)
if W21 > 0 and W11 > 0:
    chi_asym = -math.log(W21 / W11 ** 2) if W21 / W11 ** 2 > 0 else float("nan")
else:
    chi_asym = float("nan")

# Single plaquette: direct extraction via -ln W(1,1) per unit area ≈ sigma*a^2 (rough)
sigma_a2_plaq = -math.log(W11) if W11 > 0 else float("nan")

print(f"\n{'='*62}")
print(f"RESULTS (L={L}, beta={BETA}, {len(_wl_data['W11'])} measurements)")
print(f"{'='*62}")
print(f"<P>          = {np.mean(P_list):.5f}  (expected ~0.615 at beta=6)")
print(f"W(1,1)       = {W11:.6f} ± {W11_err:.6f}")
print(f"W(2,1)       = {W21:.6f} ± {W21_err:.6f}")
print(f"W(1,2)       = {W12:.6f} ± {W12_err:.6f}")
print(f"W(2,2)       = {W22:.6f} ± {W22_err:.6f}")
print(f"")
print(f"chi(2,2)     = -ln[W(2,2)*W(1,1)/W(2,1)^2] = {chi_22:.6f}   ← sigma*a^2")
print(f"chi_asym     = -ln[W(2,1)/W(1,1)^2]        = {chi_asym:.6f}  (rough check)")
print(f"-ln W(1,1)   = {sigma_a2_plaq:.6f}  (single-plaquette approx)")

# ─── Physical extraction ──────────────────────────────────────────────────────
# At beta=6.0 in quenched SU(3), lattice spacing a ≈ 0.093 fm (well-established)
a_fm = 0.093
hbarc = 0.1973269804   # GeV·fm
a_GeV_inv = a_fm / hbarc

# String tension from Creutz ratio
sigma_GeV2 = chi_22 / a_GeV_inv ** 2 if not math.isnan(chi_22) else float("nan")
sigma_GeV2_asym = chi_asym / a_GeV_inv ** 2 if not math.isnan(chi_asym) else float("nan")

print(f"\nPhysical extraction (a={a_fm} fm = {a_GeV_inv:.4f} GeV⁻¹):")
print(f"  sigma [chi(2,2)] = {sigma_GeV2:.4f} GeV²")
print(f"  sigma [asym]     = {sigma_GeV2_asym:.4f} GeV²")
print(f"  PDG reference:   ~ 0.18 GeV²")

# ─── GTE f_quant extraction ───────────────────────────────────────────────────
m_tau_MeV   = 1776.86
m_kink_MeV  = (8.0 / 49.0) * m_tau_MeV
m_kink_GeV  = m_kink_MeV / 1000.0
delta_K     = math.log2(9)          # log₂(N_c²) for SU(3)
sigma_GTE   = delta_K * m_kink_GeV ** 2

print(f"\nGTE classical string tension:")
print(f"  m_kink = {m_kink_MeV:.3f} MeV")
print(f"  delta_K = log₂(9) = {delta_K:.6f}")
print(f"  sigma_GTE = {sigma_GTE:.6f} GeV²")

f_quant = sigma_GeV2 / sigma_GTE if not math.isnan(sigma_GeV2) and sigma_GeV2 > 0 else float("nan")

candidates = {
    "2^{-2/3}":     2.0 ** (-2.0 / 3.0),   # ≈ 0.6300
    "5/8":          5.0 / 8.0,              # 0.6250
    "sigma_ratio":  0.18 / sigma_GTE,       # from PDG sigma
    "C_ratio":      0.6289,                 # Casimir ratio estimate
}

print(f"\nf_quant extraction:")
print(f"  f_quant (measured) = {f_quant:.6f}" if not math.isnan(f_quant) else "  f_quant: nan (chi_22 not converged)")
for name, val in candidates.items():
    if not math.isnan(f_quant):
        diff = abs(f_quant - val) / val * 100
        print(f"  {name:20s} = {val:.6f}   diff = {diff:.1f}%")
    else:
        print(f"  {name:20s} = {val:.6f}")

if not math.isnan(f_quant):
    best = min(candidates, key=lambda k: abs(f_quant - candidates[k]))
    print(f"\n  ↳ Closest candidate: {best} = {candidates[best]:.6f}")
else:
    best = "undetermined"

# ─── Save full results ────────────────────────────────────────────────────────
results = {
    "run": {
        "L": L, "beta": BETA, "N_warmup": N_WARMUP,
        "N_meas": N_MEAS, "meas_every": MEAS_EVERY,
        "n_measurements": len(_wl_data["W11"]),
        "start": "cold",
        "status": "COMPLETE",
    },
    "plaquette": {
        "mean": float(np.mean(P_list)),
        "std":  float(np.std(P_list)),
        "expected_beta6": 0.615,
    },
    "wilson_loops": {
        "W_11": W11, "W_11_err": W11_err,
        "W_21": W21, "W_21_err": W21_err,
        "W_12": W12, "W_12_err": W12_err,
        "W_22": W22, "W_22_err": W22_err,
    },
    "creutz": {
        "chi_22":   chi_22,
        "chi_asym": chi_asym,
        "sigma_a2": chi_22,
        "note": "chi(2,2) = -ln[W(2,2)*W(1,1)/W(2,1)^2]; sigma*a^2 in lattice units",
    },
    "physical": {
        "a_fm": a_fm, "a_GeV_inv": a_GeV_inv,
        "sigma_GeV2":      sigma_GeV2,
        "sigma_GeV2_asym": sigma_GeV2_asym,
        "sigma_PDG":       0.18,
    },
    "gte": {
        "m_kink_MeV":        m_kink_MeV,
        "m_kink_GeV":        m_kink_GeV,
        "delta_K":           delta_K,
        "sigma_GTE_GeV2":    sigma_GTE,
        "f_quant_measured":  f_quant,
        "candidates":        candidates,
        "best_candidate":    best,
    },
    "epic": "EPIC_080",
    "rank": "080-G13",
    "date": "2026-05-29",
}

out = "papers/39_qcd_from_gte/scripts/g13_metropolis_results.json"
with open(out, "w") as fh:
    json.dump(results, fh, indent=2)
print(f"\nFull results saved to {out}")
print("Done.")
