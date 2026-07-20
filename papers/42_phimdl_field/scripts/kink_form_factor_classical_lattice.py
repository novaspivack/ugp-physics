#!/usr/bin/env python3
"""Classical discrete kink on the tape: discretization control for the
kink charge form factor (Route C of the 088-R15 measurement).

Solves the lattice Euler-Lagrange equation for the Z7 cosine kink

    (phi_{i+1} - 2 phi_i + phi_{i-1})/a^2 = V'(phi_i),
    V(phi) = (m^2/49)(1 - cos 7 phi),  phi(-L/2) = 0, phi(+L/2) = 2 pi/7

by damped Newton relaxation at am in {7/8, 7/16, 7/32, 7/64} (7/8 = the
physical tape point a = 1/Lambda_GTE on the tree reading).

Observables (definitions frozen in-session before running):
  - link gradient g = (phi_{i+1} - phi_i)/a
  - CD-BORN density  rho_B ~ g^2  (P42 CatAD Born density; classical sech^2)
  - CD-TOP  density  rho_T ~ g    (P42 topological winding density; sech)
  - self-centered second moments <x^2>; r_RMS
  - lattice meson pole mass a*mu = arccosh(1 + (a mtilde)^2/2) from the
    measured kink tail decay (same-lattice renormalization point)
  - broadening factor b = r_RMS * mu / r_class  (r_class = pi/(2 sqrt3) Born,
    pi/2 topological)
  - lattice form factor F(q) on the link lattice up to the BZ edge

Expected (pre-registered P1): |b_class - 1| <= 5 percent at am = 7/8.
"""
import json
import math
import signal
import sys

import numpy as np

TIMEOUT_SECONDS = 600


def _timeout(signum, frame):
    print(f"TIMEOUT {TIMEOUT_SECONDS}s reached")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

TWO_PI_7 = 2.0 * math.pi / 7.0
R_CLASS_BORN = math.pi / (2.0 * math.sqrt(3.0))   # r_RMS * m, sech^2
R_CLASS_TOP = math.pi / 2.0                       # r_RMS * m, sech


def solve_kink(am, n_halfwidth=60.0):
    """Newton-relax the lattice EL kink; returns phi array and a-grid."""
    n = int(2 * n_halfwidth / am) | 1            # odd site count
    x = (np.arange(n) - (n - 1) / 2.0) * am      # in units of 1/m
    phi = (4.0 / 7.0) * np.arctan(np.exp(x))     # continuum seed
    phi[0], phi[-1] = 0.0, TWO_PI_7
    m2 = 1.0                                     # work in units m = 1
    for it in range(3000):
        vp = (m2 / 7.0) * np.sin(7.0 * phi)
        vpp = m2 * np.cos(7.0 * phi)
        res = np.zeros_like(phi)
        res[1:-1] = (phi[2:] - 2 * phi[1:-1] + phi[:-2]) / am ** 2 - vp[1:-1]
        # Jacobi-Newton sweep (diagonal of the Jacobian)
        diag = -2.0 / am ** 2 - vpp
        dphi = np.zeros_like(phi)
        dphi[1:-1] = -res[1:-1] / diag[1:-1]
        phi += 0.8 * dphi
        rmax = float(np.max(np.abs(res[1:-1])))
        if rmax < 1e-13:
            break
    return x, phi, rmax, it + 1


def moments(xl, rho):
    rho = rho / rho.sum()
    x0 = float((xl * rho).sum())
    x2 = float(((xl - x0) ** 2 * rho).sum())
    return x0, x2


def tail_pole_mass(x, phi, am):
    """Measured pole mass from the kink tail decay phi ~ A e^{-mu x}."""
    dev = TWO_PI_7 - phi
    # fit window: deviation between 1e-3 and 1e-7 of the asymptote, right side
    mask = (x > 2.0) & (dev > 1e-9) & (dev < 1e-3 * TWO_PI_7)
    if mask.sum() < 4:
        mask = (x > 2.0) & (dev > 1e-12)
    xs, ds = x[mask], np.log(dev[mask])
    slope = np.polyfit(xs, ds, 1)[0]
    return -float(slope)                          # mu in units of m


results = {"runs": {}}
print("=== classical discrete kink: discretization control ===")
print(f"r_class (Born) = {R_CLASS_BORN:.6f};  r_class (top) = {R_CLASS_TOP:.6f}")
for am in (7.0 / 8.0, 7.0 / 16.0, 7.0 / 32.0, 7.0 / 64.0):
    x, phi, rmax, iters = solve_kink(am)
    assert rmax < 1e-10, f"relaxation failed at am={am}: residual {rmax}"
    g = (phi[1:] - phi[:-1]) / am                 # link gradient
    xl = 0.5 * (x[1:] + x[:-1])                   # link positions
    _, x2_b = moments(xl, g ** 2)
    _, x2_t = moments(xl, np.abs(g))
    mu = tail_pole_mass(x, phi, am)
    # cross-check: lattice dispersion pole mass from bare m
    mu_disp = math.acosh(1.0 + am * am / 2.0) / am
    r_b = math.sqrt(x2_b)
    r_t = math.sqrt(x2_t)
    b_born_mu = r_b * mu / R_CLASS_BORN           # broadening vs measured mu
    b_born_m = r_b * 1.0 / R_CLASS_BORN           # broadening vs input m
    b_top_mu = r_t * mu / R_CLASS_TOP
    # lattice form factor on links
    qs = np.linspace(0.0, math.pi / am, 60)
    rho = g ** 2 / (g ** 2).sum()
    x0 = float((xl * rho).sum())
    F = np.array([abs(np.sum(rho * np.exp(1j * q * (xl - x0)))) for q in qs])
    row = {"am": am, "n_sites": len(x), "newton_iters": iters,
           "residual": rmax,
           "x2m2_born": x2_b, "x2m2_top": x2_t,
           "mu_tail_over_m": mu, "mu_disp_over_m": mu_disp,
           "b_born_vs_mu": b_born_mu, "b_born_vs_m": b_born_m,
           "b_top_vs_mu": b_top_mu,
           "F_q": {"q_over_m": qs.tolist()[:60], "F": F.tolist()[:60]}}
    results["runs"][f"am_{am:.5f}"] = row
    print(f"  am = {am:.5f}: <x^2>m^2 Born = {x2_b:.6f} "
          f"(cont {math.pi**2/12:.6f}), top = {x2_t:.6f} "
          f"(cont {math.pi**2/4:.6f}); mu_tail = {mu:.5f}, "
          f"mu_disp = {mu_disp:.5f}")
    print(f"            b(Born, vs mu) = {b_born_mu:.5f}; "
          f"b(Born, vs m) = {b_born_m:.5f}; b(top, vs mu) = {b_top_mu:.5f}")

# Richardson check: <x^2> should approach pi^2/12 as (am)^2 -> 0
ams = [7.0 / 8.0, 7.0 / 16.0, 7.0 / 32.0, 7.0 / 64.0]
x2s = [results["runs"][f"am_{a:.5f}"]["x2m2_born"] for a in ams]
print("\n  continuum approach (Born): " +
      ", ".join(f"{v:.6f}" for v in x2s) + f" -> {math.pi**2/12:.6f}")
slope = (x2s[0] - x2s[-1]) / (ams[0] ** 2 - ams[-1] ** 2)
print(f"  O((am)^2) coefficient of <x^2>m^2: {slope:+.5f}")
results["continuum_approach"] = {"x2_born_sequence": x2s,
                                 "am2_slope": slope,
                                 "continuum_value": math.pi ** 2 / 12}

phys = results["runs"]["am_0.87500"]
print(f"\n  PHYSICAL TAPE POINT am = 7/8: b(Born, vs mu) = "
      f"{phys['b_born_vs_mu']:.5f}  (P1 pass iff |b-1| <= 0.05: "
      f"{'PASS' if abs(phys['b_born_vs_mu']-1) <= 0.05 else 'FAIL'})")
results["P1_pass"] = bool(abs(phys["b_born_vs_mu"] - 1) <= 0.05)

out = "/Users/nova/ugp-physics/papers/42_phimdl_field/scripts/kink_form_factor_classical_lattice_results.json"
with open(out, "w") as f:
    json.dump(results, f, indent=1)
print(f"Saved {out.split('/')[-1]}")
signal.alarm(0)
