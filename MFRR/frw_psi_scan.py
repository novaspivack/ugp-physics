#!/usr/bin/env python3
import numpy as np
from dataclasses import dataclass
from typing import Tuple, Dict
from math import isfinite
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp
from numpy.linalg import lstsq
import csv
import os

# --------------------------
# Physical / numerical setup
# --------------------------
G = 6.67430e-11         # m^3 kg^-1 s^-2
c = 299792458.0         # m/s
H0_km_s_Mpc = 70.0      # baseline H0 for plotting [km/s/Mpc]
Mpc = 3.085677581e22    # m
H0 = (H0_km_s_Mpc*1000.0)/Mpc # s^-1

# Normalize with 8πG/3 absorbed in rho crit normalization
rho_crit0 = 3.0*H0**2/(8.0*np.pi*G)   # J·s^2/m^5? (we treat as energy density equivalently)
Omega_m0 = 0.3
Omega_de0 = 1.0 - Omega_m0

# We work in units where scale factor a=1 today at t=0
# We integrate backward in time using ln(a) as time variable: x = ln a; a = e^x
# dz/dx = - (1+z)

@dataclass
class Params:
    m: float                 # [s^-1], effective mass parameter via m_phys / ħ ; we treat phenomenologically
    beta: float              # dimensionless coupling
    omega_bar: float         # <omega>, dimensionless
    Rf_bar: float            # <R_F>, dimensionless; maps to Lambda_eff
    H0: float                # s^-1
    Omega_m0: float          # present matter fraction
    zmax: float              # max redshift to integrate to
    nsteps: int              # steps in x=ln a

def V_eff(psi: float, p: Params) -> float:
    # Effective potential: nearly pure cosmological constant with tiny perturbations
    # For w ~ -1 and w_a ~ 0, we need V to be very nearly constant
    # Rf_bar is the fraction of rho_crit0 that comes from the constant term
    # For standard ΛCDM, we want V ~ 0.7 * rho_crit0 today
    
    # Dominant constant term: Rf_bar directly sets fraction of rho_crit0
    Lambda_eff = p.Rf_bar * rho_crit0
    
    # Tiny mass term: (1/2) m^2 psi^2, scaled to ~1e-5 of critical density
    # This allows small slow-roll evolution without spoiling w ~ -1
    U0 = 0.5 * (p.m**2) * psi * psi * (1e-5 * rho_crit0)
    
    # Tiny linear tilt from fiber coupling: beta * omega_bar * psi
    # Scaled even smaller to avoid any phantom behavior
    U1 = p.beta * p.omega_bar * psi * (1e-6 * rho_crit0)
    
    return Lambda_eff + U0 + U1

def dV_dpsi(psi: float, p: Params) -> float:
    return (p.m**2) * psi * (1e-5 * rho_crit0) + p.beta * p.omega_bar * (1e-6 * rho_crit0)

def H_of(a: float, psi: float, ppsi: float, p: Params) -> float:
    # rho_m(a) - safeguard against a=0
    a_safe = max(a, 1e-10)
    rho_m = rho_crit0 * p.Omega_m0 * a_safe**(-3)
    # rho_psi
    rho_psi = 0.5*ppsi*ppsi + V_eff(psi, p)
    rho_total = rho_m + rho_psi
    if rho_total <= 0:
        return 1e-30  # prevent sqrt of negative
    return np.sqrt( (8.0*np.pi*G/3.0) * rho_total )

def rhs(x: float, y: np.ndarray, p: Params) -> np.ndarray:
    # x = ln a; y = [psi, dpsi/dt]
    a = np.exp(x)
    psi = y[0]
    ppsi = y[1]
    H = H_of(a, psi, ppsi, p)
    # dpsi/dx = dpsi/dt / (da/dt * 1/a) = ppsi / (H)
    dpsi_dx = ppsi / H
    # dppsi/dx = (dppsi/dt) / (H) = -(3H*ppsi + dV/dpsi)/H
    dppsi_dx = ( -3.0*H*ppsi - dV_dpsi(psi, p) ) / H
    return np.array([dpsi_dx, dppsi_dx])

def integrate_background(p: Params, psi0: float=0.1, ppsi0: float=0.0) -> Dict[str, np.ndarray]:
    # integrate from x=0 (today) to x_min = ln a_min with a_min = 1/(1+zmax)
    x0 = 0.0
    xmin = -np.log(1.0 + p.zmax)
    xs = np.linspace(x0, xmin, p.nsteps)

    sol = solve_ivp(lambda x,y: rhs(x,y,p), (x0, xmin), np.array([psi0, ppsi0]),
                    t_eval=xs, method='RK45', rtol=1e-7, atol=1e-9)

    x = sol.t
    a = np.exp(x)
    z = 1.0/a - 1.0
    psi = sol.y[0]
    ppsi = sol.y[1]
    H = np.array([H_of(ai, ps, pp, p) for ai,ps,pp in zip(a, psi, ppsi)])
    rho_m = rho_crit0 * p.Omega_m0 * a**(-3)
    rho_psi = 0.5*ppsi*ppsi + np.array([V_eff(ps, p) for ps in psi])
    p_psi = 0.5*ppsi*ppsi - np.array([V_eff(ps, p) for ps in psi])
    w_psi = p_psi / rho_psi

    # effective w(z)
    rho_tot = rho_m + rho_psi
    p_tot = p_psi
    w_eff = p_tot / rho_tot

    return dict(x=x, a=a, z=z, H=H, psi=psi, ppsi=ppsi,
                rho_m=rho_m, rho_psi=rho_psi, w_psi=w_psi, w_eff=w_eff)

def fit_w0_wa(z: np.ndarray, w: np.ndarray, zmax_fit=1.5) -> Tuple[float,float]:
    # CPL: w(z) = w0 + wa * z/(1+z)
    mask = (z>=0.0) & (z<=zmax_fit) & np.isfinite(w)
    if mask.sum()<5:
        return np.nan, np.nan
    X = np.column_stack([np.ones(mask.sum()), z[mask]/(1.0+z[mask])])
    y = w[mask]
    coeffs, *_ = lstsq(X, y, rcond=None)
    w0, wa = coeffs.tolist()
    return w0, wa

def main():
    outdir = "frw_psi_outputs"
    os.makedirs(outdir, exist_ok=True)
    print(f"Created output directory: {outdir}")

    # Parameter grid (fine-tuned for cosmological viability)
    # Target: w0 ~ -1, |w_a| < 0.05
    # Strategy: Rf_bar ~ 0.7 (standard Omega_Lambda), tiny m, tiny beta*omega_bar
    ms = [0.0, 0.01*H0, 0.05*H0]         # s^-1, very small mass (nearly frozen field)
    betas = [0.0, 0.01, 0.05]            # tiny coupling to avoid phantom behavior
    omega_bars = [0.0, 0.01, 0.05]       # tiny fiber average
    Rf_bars = [0.65, 0.70, 0.75]         # Omega_Lambda ~ 0.7 for standard cosmology

    total_cases = len(ms) * len(betas) * len(omega_bars) * len(Rf_bars)
    print(f"Starting scan: {total_cases} parameter combinations")

    results = []
    case_num = 0
    for m in ms:
        for beta in betas:
            for ob in omega_bars:
                for rf in Rf_bars:
                    case_num += 1
                    p = Params(m=m, beta=beta, omega_bar=ob, Rf_bar=rf,
                               H0=H0, Omega_m0=Omega_m0, zmax=2.0, nsteps=2000)
                    print(f"[{case_num}/{total_cases}] Integrating m={m:.2e}, beta={beta:.2f}, omega_bar={ob:.2f}, Rf_bar={rf:.2f}")
                    # Start with tiny Psi (nearly frozen field) and zero velocity
                    sol = integrate_background(p, psi0=0.001, ppsi0=0.0)
                    # Fit the DARK ENERGY equation of state w_psi, not total w_eff
                    w0, wa = fit_w0_wa(sol["z"], sol["w_psi"], zmax_fit=1.5)

                    tag = f"m{m:.2e}_b{beta:.2f}_ob{ob:.2f}_rf{rf:.2f}"
                    print(f"  -> w0={w0:.4f}, wa={wa:.4f}")
                    # plots
                    plt.figure(figsize=(6,4))
                    plt.plot(sol["z"], sol["w_eff"])
                    plt.gca().invert_xaxis()
                    plt.xlabel("z"); plt.ylabel("w_eff(z)")
                    plt.title(f"w(z): {tag}\nw0={w0:.3f}, wa={wa:.3f}")
                    plt.tight_layout()
                    plt.savefig(os.path.join(outdir, f"wz_{tag}.png"), dpi=150)
                    plt.close()

                    plt.figure(figsize=(6,4))
                    plt.plot(sol["z"], sol["H"]/H0)
                    plt.gca().invert_xaxis()
                    plt.xlabel("z"); plt.ylabel("H(z)/H0")
                    plt.title(f"H/H0: {tag}")
                    plt.tight_layout()
                    plt.savefig(os.path.join(outdir, f"H_{tag}.png"), dpi=150)
                    plt.close()

                    plt.figure(figsize=(6,4))
                    plt.plot(sol["z"], sol["psi"])
                    plt.gca().invert_xaxis()
                    plt.xlabel("z"); plt.ylabel("Psi(z)")
                    plt.title(f"Psi: {tag}")
                    plt.tight_layout()
                    plt.savefig(os.path.join(outdir, f"psi_{tag}.png"), dpi=150)
                    plt.close()

                    results.append(dict(m=m, beta=beta, omega_bar=ob, Rf_bar=rf,
                                        w0=w0, wa=wa))

    # write CSV
    csv_path = os.path.join(outdir, "scan_results.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["m","beta","omega_bar","Rf_bar","w0","wa"])
        writer.writeheader()
        for r in results:
            writer.writerow(r)

    # quick summary: count mildly running cases
    mild = [r for r in results if isfinite(r["wa"]) and abs(r["wa"])<=0.05]
    print(f"Total cases: {len(results)}, |wa|<=0.05: {len(mild)}")
    print(f"CSV: {csv_path}\nPNG figs in: {outdir}")

if __name__ == "__main__":
    main()
