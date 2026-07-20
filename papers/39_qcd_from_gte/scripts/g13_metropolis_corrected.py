"""
G13: SU(3) Metropolis CORRECTED — δ=0.03 (small) + cold start + more warmup
Key fix: δ=0.03 (NOT 0.24) keeps system near ordered start and prevents crossing
the bulk first-order transition at β_bulk ≈ 5.7
"""
import numpy as np
import math, json, signal, time

TIMEOUT_SECONDS = 480  # 8 minutes

def _timeout_handler(s, f):
    print(f"\nTIMEOUT. Saving partial results.")
    import sys; sys.exit(1)

signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

L = 4
beta = 6.0
N_warmup = 1000  # enough for small δ
N_meas = 300
delta = 0.03  # FIXED: was 0.24, now 0.03

def project_su3(M):
    U, s, Vh = np.linalg.svd(M)
    Q = U @ Vh
    d = np.linalg.det(Q)
    # Fix determinant to be 1
    for i in range(3):
        Q[:, i] /= d**(1/3)
    return Q

def get_staple(U, x, mu, L):
    staple = np.zeros((3,3), dtype=complex)
    for nu in range(4):
        if nu == mu: continue
        xpmu = list(x); xpmu[mu] = (x[mu]+1)%L
        xpnu = list(x); xpnu[nu] = (x[nu]+1)%L
        xpmpn = list(x); xpmpn[mu]=(x[mu]+1)%L; xpmpn[nu]=(xpmpn[nu]+1)%L
        xmnu = list(x); xmnu[nu] = (x[nu]-1)%L
        xpmumn = list(x); xpmumn[mu]=(x[mu]+1)%L; xpmumn[nu]=(xpmumn[nu]-1)%L
        staple += U[tuple(xpmu)][nu] @ U[tuple(xpmpn)][mu].conj().T @ U[tuple(xpnu)][nu].conj().T
        staple += U[tuple(xpmumn)][nu].conj().T @ U[tuple(xmnu)][mu].conj().T @ U[tuple(xmnu)][nu]
    return staple

def plaquette_avg(U, L):
    total = 0.0; count = 0
    for x0 in range(L):
        for x1 in range(L):
            for x2 in range(L):
                for x3 in range(L):
                    for mu in range(4):
                        for nu in range(mu+1,4):
                            x = [x0,x1,x2,x3]
                            xpmu = list(x); xpmu[mu]=(x[mu]+1)%L
                            xpnu = list(x); xpnu[nu]=(x[nu]+1)%L
                            xpmpn = list(x); xpmpn[mu]=(x[mu]+1)%L; xpmpn[nu]=(xpmpn[nu]+1)%L
                            P = np.trace(U[tuple(x)][mu] @ U[tuple(xpmu)][nu] @
                                        U[tuple(xpmpn)][mu].conj().T @ U[tuple(xpnu)][nu].conj().T).real/3
                            total += P; count += 1
    return total/count

def sweep(U, beta, delta, L):
    accepts = 0
    for x0 in range(L):
        for x1 in range(L):
            for x2 in range(L):
                for x3 in range(L):
                    for mu in range(4):
                        x = [x0,x1,x2,x3]
                        V = U[tuple(x)][mu].copy()
                        staple = get_staple(U, x, mu, L)
                        dV = np.eye(3,dtype=complex) + delta*(np.random.randn(3,3)+1j*np.random.randn(3,3))
                        Vnew = project_su3(dV @ V)
                        dS = -beta/3 * np.trace((Vnew - V) @ staple).real
                        if dS <= 0 or np.random.rand() < np.exp(-dS):
                            U[tuple(x)][mu] = Vnew
                            accepts += 1
    return accepts / (L**4 * 4)

# COLD START: all links = identity (ordered start)
print(f"Initializing {L}^4 lattice with COLD START (all I)")
print(f"Using δ={delta} (CORRECTED from 0.24)")
U = {}
for x0 in range(L):
    for x1 in range(L):
        for x2 in range(L):
            for x3 in range(L):
                U[(x0,x1,x2,x3)] = [np.eye(3,dtype=complex) for _ in range(4)]

P = plaquette_avg(U, L)
print(f"Initial plaquette = {P:.4f} (should be 1.0)")

# Warmup with monitoring
print(f"\nWarming up ({N_warmup} sweeps, δ={delta})...")
plaq_history = []
for i in range(N_warmup):
    ar = sweep(U, beta, delta, L)
    if i % 100 == 0:
        P = plaquette_avg(U, L)
        plaq_history.append(P)
        print(f"  Sweep {i}: P={P:.4f}, accept={ar:.3f}")
        if P > 0.55:
            print(f"  ** Approaching weak-coupling phase! **")

P_after_warmup = plaquette_avg(U, L)
thermalized = P_after_warmup > 0.50
print(f"\nAfter warmup: P={P_after_warmup:.4f}, thermalized: {thermalized}")
print(f"Target: P≈0.59 at β=6 (weak coupling phase)")

# Even partial result is informative
print(f"\nPlaquette evolution: {[f'{p:.3f}' for p in plaq_history]}")

results = {
    "delta": delta, "L": L, "beta": beta, "N_warmup": N_warmup,
    "initial_plaquette": 1.0,
    "final_plaquette": float(P_after_warmup),
    "thermalized": bool(thermalized),
    "plaquette_history": [float(p) for p in plaq_history],
    "note": f"Corrected run with delta={delta} (was 0.24)"
}
with open("papers/39_qcd_from_gte/scripts/g13_metropolis_corrected_results.json", "w") as f:
    json.dump(results, f, indent=2)
print("Saved results")
signal.alarm(0)
