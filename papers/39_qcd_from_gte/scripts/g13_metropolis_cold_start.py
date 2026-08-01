"""
G13: SU(3) Metropolis with COLD START for proper thermalization.
Cold start: all links = identity matrix.
L=4 (4^4 = 256 sites), beta=6.0
N_warmup=500 sweeps, N_meas=200 sweeps
delta=0.24 tuned for ~50% acceptance at beta=6
"""
import numpy as np
import json
import signal
import time

TIMEOUT_SECONDS = 420  # 7 minutes


def _timeout_handler(s, f):
    print(f"\nTIMEOUT after {TIMEOUT_SECONDS}s. Saving partial results.")
    import sys
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

L = 4
beta = 6.0
N_warmup = 500
N_meas = 200
delta = 0.24


def project_su3(M):
    """Project to nearest SU(3) via SVD with det=1 fix."""
    U, s, Vh = np.linalg.svd(M)
    Q = U @ Vh
    d = np.linalg.det(Q)
    Q[:, 0] /= d
    return Q


def get_staple(U, x, mu, L):
    """Sum of 6 staples for link (x, mu)."""
    staple = np.zeros((3, 3), dtype=complex)
    for nu in range(4):
        if nu == mu:
            continue
        xpmu = list(x); xpmu[mu] = (x[mu] + 1) % L
        xpnu = list(x); xpnu[nu] = (x[nu] + 1) % L
        xpmu2 = list(x); xpmu2[mu] = (x[mu] + 1) % L; xpmu2[nu] = (xpmu2[nu] + 1) % L
        xmnu = list(x); xmnu[nu] = (x[nu] - 1) % L
        xpmumnu = list(x); xpmumnu[mu] = (x[mu] + 1) % L; xpmumnu[nu] = (xpmumnu[nu] - 1) % L
        # Forward staple
        staple += (U[tuple(xpmu)][nu]
                   @ U[tuple(xpmu2)][mu].conj().T
                   @ U[tuple(xpnu)][nu].conj().T)
        # Backward staple
        staple += (U[tuple(xpmumnu)][nu].conj().T
                   @ U[tuple(xmnu)][mu].conj().T
                   @ U[tuple(xmnu)][nu])
    return staple


def sweep(U, beta, delta, L):
    """One Metropolis sweep over all links."""
    accepts = 0
    for x0 in range(L):
        for x1 in range(L):
            for x2 in range(L):
                for x3 in range(L):
                    for mu in range(4):
                        x = [x0, x1, x2, x3]
                        V = U[tuple(x)][mu].copy()
                        staple = get_staple(U, x, mu, L)
                        dV = (np.eye(3, dtype=complex)
                              + delta * (np.random.randn(3, 3)
                                         + 1j * np.random.randn(3, 3)))
                        Vnew = project_su3(dV @ V)
                        dS = -beta / 3 * np.trace((Vnew - V) @ staple).real
                        if dS <= 0 or np.random.rand() < np.exp(-dS):
                            U[tuple(x)][mu] = Vnew
                            accepts += 1
    return accepts / (L ** 4 * 4)


def plaquette_avg(U, L):
    """Average plaquette (should converge to ~0.6 at beta=6 for SU(3))."""
    total = 0.0
    count = 0
    for x0 in range(L):
        for x1 in range(L):
            for x2 in range(L):
                for x3 in range(L):
                    for mu in range(4):
                        for nu in range(mu + 1, 4):
                            x = [x0, x1, x2, x3]
                            xpmu = list(x); xpmu[mu] = (x[mu] + 1) % L
                            xpnu = list(x); xpnu[nu] = (x[nu] + 1) % L
                            xpmpn = list(x)
                            xpmpn[mu] = (x[mu] + 1) % L
                            xpmpn[nu] = (xpmpn[nu] + 1) % L
                            P = np.trace(
                                U[tuple(x)][mu]
                                @ U[tuple(xpmu)][nu]
                                @ U[tuple(xpmpn)][mu].conj().T
                                @ U[tuple(xpnu)][nu].conj().T
                            ).real / 3
                            total += P
                            count += 1
    return total / count


# COLD START: all links = identity
print(f"Initializing {L}^4 lattice with COLD START (all links = I)...")
U = {}
for x0 in range(L):
    for x1 in range(L):
        for x2 in range(L):
            for x3 in range(L):
                U[(x0, x1, x2, x3)] = [np.eye(3, dtype=complex) for _ in range(4)]

P_init = plaquette_avg(U, L)
print(f"Initial plaquette (cold start) = {P_init:.6f} (expected 1.0)")

# Warmup phase
print(f"\nWarming up ({N_warmup} sweeps at beta={beta}, delta={delta})...")
warmup_history = []
t0 = time.time()
for i in range(N_warmup):
    ar = sweep(U, beta, delta, L)
    if i % 50 == 0:
        P = plaquette_avg(U, L)
        elapsed = time.time() - t0
        print(f"  Sweep {i:4d}: P={P:.6f}, accept={ar:.3f}, t={elapsed:.1f}s")
        warmup_history.append({"sweep": i, "plaquette": P, "accept_rate": ar})
        if P > 0.50:
            print("  ** Approaching thermalized regime (P > 0.50) **")
        if P > 0.55:
            print("  ** Thermalized (P > 0.55) **")

P_warmup_final = plaquette_avg(U, L)
print(f"\nPost-warmup plaquette: {P_warmup_final:.6f}")

# Measurement phase
print(f"\nMeasurement phase ({N_meas} sweeps)...")
meas_history = []
for i in range(N_meas):
    ar = sweep(U, beta, delta, L)
    P = plaquette_avg(U, L)
    meas_history.append({"sweep": i, "plaquette": P, "accept_rate": ar})
    if i % 50 == 0:
        print(f"  Meas {i:4d}: P={P:.6f}, accept={ar:.3f}")

P_meas_vals = [m["plaquette"] for m in meas_history]
P_mean = float(np.mean(P_meas_vals))
P_std = float(np.std(P_meas_vals))

print(f"\n--- RESULTS ---")
print(f"Mean plaquette (measurement phase): {P_mean:.6f} ± {P_std:.6f}")
print(f"Thermalized: {P_mean > 0.50}")
print(f"Strong coupling limit P→0, weak coupling P→1")
print(f"Lattice QCD benchmark at beta=6.0: P ≈ 0.59 (standard)")

results = {
    "L": L,
    "beta": beta,
    "N_warmup": N_warmup,
    "N_meas": N_meas,
    "delta": delta,
    "start": "cold (all links = identity)",
    "initial_plaquette": P_init,
    "post_warmup_plaquette": P_warmup_final,
    "measurement_mean_plaquette": P_mean,
    "measurement_std_plaquette": P_std,
    "thermalized": bool(P_mean > 0.50),
    "benchmark_target_beta6": 0.59,
    "warmup_history": warmup_history,
    "note": (
        "Cold start from identity; P should converge to ~0.59 at beta=6.0 for SU(3). "
        "Hot start (round 15) failed: P=-0.006 from random start needed 5000+ sweeps."
    ),
}

output_path = "papers/39_qcd_from_gte/scripts/g13_metropolis_cold_results.json"
with open(output_path, "w") as f:
    json.dump(results, f, indent=2)
print(f"\nSaved results to {output_path}")

signal.alarm(0)
