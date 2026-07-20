"""
kink_pole_mass_box_modesum_check.py

Independent cross-check (Route C) of the mu-independent bracket term
PREF*B = -(1/12pi) * B of kink_pole_mass_interface_dimreg.py, by a finite-box
mode sum that shares no machinery with the phase-shift route.

Method: on a Dirichlet box z in [-L/2, L/2], diagonalize
  H = -d^2/dz^2 + 1 + U(z),  U = -2 sech^2 z   (units m = 1)
in the free sine basis. Each 1D eigenvalue lambda_i = Omega_i^2 contributes the
analytic transverse dim-reg energy per unit area f(lambda) = -lambda^{3/2}/(12 pi).
The renormalized remainder

  R = sum_i [ f(lambda_i) - f(lambda_i^0) - f'(lambda_i^0) U_ii
              - ( f'(lambda_i^0) lam2_i + (1/2) f''(lambda_i^0) U_ii^2 ) ]

with lam2_i = sum_{j != i} |U_ij|^2/(lambda_i^0 - lambda_j^0) the second-order
Rayleigh-Schrodinger shift, removes exactly the same diagrammatic content
(tadpole + bubble) as the delta_1, delta_2 Born subtractions of the interface
formula. Hence R -> PREF*B = -0.00655351 m^3 as L -> inf, basis -> complete.

Expected output: R within ~1% of -0.0065535 with stable L/N trend.
"""

import signal, sys, json
import numpy as np

TIMEOUT = 900

def _timeout_handler(signum, frame):
    print(f"\nTIMEOUT: {TIMEOUT}s wall-clock limit reached.")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT)

TARGET = -0.00655351  # PREF*B from kink_pole_mass_interface_dimreg.py

def f(lam):
    lam = np.maximum(lam, 0.0)
    return -lam**1.5/(12.0*np.pi)

def fp(lam):
    return -1.5*np.sqrt(np.maximum(lam, 0.0))/(12.0*np.pi)

def fpp(lam):
    lam = np.maximum(lam, 1e-12)
    return -0.75/np.sqrt(lam)/(12.0*np.pi)

def run_case(L, N):
    """Sine basis phi_n(z) = sqrt(2/L) sin(n pi (z+L/2)/L), n = 1..N."""
    n = np.arange(1, N+1)
    k = n*np.pi/L
    lam0 = k**2 + 1.0

    # potential matrix in sine basis via grid quadrature
    Ng = 6000
    z = np.linspace(-L/2, L/2, Ng)
    w = np.full(Ng, z[1]-z[0]); w[0] *= 0.5; w[-1] *= 0.5
    U = -2.0/np.cosh(z)**2
    Phi = np.sqrt(2.0/L)*np.sin(np.outer(k, z + L/2))          # (N, Ng)
    Umat = (Phi * (U*w)) @ Phi.T                                # (N, N)
    Umat = 0.5*(Umat + Umat.T)

    H = np.diag(lam0) + Umat
    lam = np.linalg.eigvalsh(H)

    # first order: U_ii ; second order: sum_j |U_ij|^2/(lam0_i - lam0_j)
    U2 = Umat**2
    denom = lam0[:, None] - lam0[None, :]
    np.fill_diagonal(denom, 1.0)
    ratio = U2/denom
    np.fill_diagonal(ratio, 0.0)
    lam2 = ratio.sum(axis=1)

    Uii = np.diag(Umat)
    R = np.sum(f(lam)) - np.sum(f(lam0)) - np.sum(fp(lam0)*Uii) \
        - np.sum(fp(lam0)*lam2 + 0.5*fpp(lam0)*Uii**2)
    return R, lam[0]

print("=" * 72)
print("Route C: finite-box mode-sum cross-check of the interface bracket")
print("=" * 72)
print(f"target PREF*B = {TARGET:+.8f}\n")

cases = [(30.0, 600), (40.0, 900), (50.0, 1200), (60.0, 1600), (60.0, 2200)]
out_rows = []
for L, N in cases:
    R, lam_min = run_case(L, N)
    dev = R/TARGET - 1.0
    print(f"L = {L:5.1f}, N = {N:5d} (k_max = {N*np.pi/L:6.1f}): "
          f"R = {R:+.8f}  [dev vs target {100*dev:+.2f}%]  lambda_min = {lam_min:+.2e}")
    out_rows.append({"L": L, "N": N, "R": R, "deviation": dev, "lambda_min": lam_min})

results = {"description": "Finite-box mode-sum cross-check (Route C) of PREF*B",
           "rank": "088-R14",
           "target_PREF_B": TARGET,
           "cases": out_rows}

out = "/Users/nova/ugp-physics/papers/42_phimdl_field/scripts/kink_pole_mass_box_modesum_check_results.json"
with open(out, "w") as fjson:
    json.dump(results, fjson, indent=2)
print("\nResults saved to:", out)

signal.alarm(0)
print("Done.")
