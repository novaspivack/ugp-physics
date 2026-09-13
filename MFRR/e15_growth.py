#!/usr/bin/env python3
import numpy as np
import matplotlib.pyplot as plt
import os, csv

# ----------------------------
# Background H(a) helper (flat)
# ----------------------------
def Ez2(a, Omega_m0=0.3, w0=-1.0, wa=0.0):
    # CPL w(a) = w0 + wa (1-a); rho_DE(a) ∝ a^{-3(1+w0+wa)} exp[-3 wa (1-a)]
    Omega_de0 = 1.0 - Omega_m0
    fac = a**(-3.0*(1.0 + w0 + wa)) * np.exp(-3.0*wa*(1.0 - a))
    return Omega_m0 * a**(-3.0) + Omega_de0 * fac

def H_of_a(a, H0=1.0, Omega_m0=0.3, w0=-1.0, wa=0.0):
    return H0 * np.sqrt(Ez2(a, Omega_m0, w0, wa))

def dlnH_dlnA(a, Omega_m0=0.3, w0=-1.0, wa=0.0):
    # d ln H / d ln a = (1/2) d ln E^2 / d ln a
    E2 = Ez2(a, Omega_m0, w0, wa)
    Omega_de0 = 1.0 - Omega_m0
    # d ln rho_m / d ln a = -3 ; d ln rho_de / d ln a = -3(1+w(a)) with CPL derivative
    w_a = w0 + wa*(1.0 - a)
    drho_m = -3.0 * (Omega_m0 * a**(-3.0))
    drho_de = -3.0*(1.0 + w_a) * (Omega_de0 * a**(-3.0*(1+w0+wa)) * np.exp(-3.0*wa*(1.0 - a)))
    dE2_dlnA = drho_m + drho_de
    return 0.5 * dE2_dlnA / E2

def Omega_m_of_a(a, Omega_m0=0.3, w0=-1.0, wa=0.0):
    E2 = Ez2(a, Omega_m0, w0, wa)
    return (Omega_m0 * a**(-3.0)) / E2

def Omega_de_of_a(a, Omega_m0=0.3, w0=-1.0, wa=0.0):
    E2 = Ez2(a, Omega_m0, w0, wa)
    return (1.0 - Omega_m0) * (a**(-3.0*(1+w0+wa)) * np.exp(-3.0*wa*(1.0 - a))) / E2

# ----------------------------
# Growth ODE in x = ln a
# ----------------------------
def solve_growth(Omega_m0=0.3, w0=-1.0, wa=0.0, eps_mu=0.0,
                 sigma8_0=0.8, zmax=2.0, nsteps=2000):
    # grid in ln a
    a_min = 1.0/(1.0+zmax)
    x = np.linspace(np.log(a_min), 0.0, nsteps)
    a = np.exp(x)
    # ODE for D: D'' + [2 + dlnH/dln a] D' - 3/2 mu Omega_m D = 0
    D = np.zeros_like(a)
    G = np.zeros_like(a)  # D' w.r.t x
    # initial conditions deep in matter era: D ~ a, so in x = ln a variable
    # D ~ e^x = a, and G = dD/dx = a.  Both D and G equal a at the initial point.
    D[0] = a[0]
    G[0] = a[0]

    for i in range(nsteps-1):
        ai = a[i]
        dlnH = dlnH_dlnA(ai, Omega_m0, w0, wa)
        Om = Omega_m_of_a(ai, Omega_m0, w0, wa)
        Ode = Omega_de_of_a(ai, Omega_m0, w0, wa)
        mu = 1.0 + eps_mu * (Ode / (Om + Ode))
        # RHS in x variable:
        # D'' = - [2 + dlnH] D' + (3/2) mu Om D
        D2 = - (2.0 + dlnH) * G[i] + 1.5 * mu * Om * D[i]
        # step (simple RK2)
        dx = x[i+1] - x[i]
        G_mid = G[i] + 0.5*dx*D2
        D_mid = D[i] + 0.5*dx*G[i]
        # recompute coefficients at midpoint (approx using ai)
        G_next = G[i] + dx*D2
        D_next = D[i] + dx*G_mid
        D[i+1] = D_next
        G[i+1] = G_next

    # normalize D to D(a=1)=1
    D /= D[-1]
    f = G / D  # since f = d ln D / d ln a = (D'/D)
    # sigma8(z)
    sigma8 = sigma8_0 * D
    z = 1.0/a - 1.0
    f_sigma8 = f * sigma8
    return dict(z=z, a=a, D=D, f=f, fs8=f_sigma8)

def main():
    outdir = "e15_growth_outputs"
    os.makedirs(outdir, exist_ok=True)

    Om0 = 0.3
    sig8 = 0.8

    # Baseline LCDM and reflexive model (w0=-1, wa=0)
    base = solve_growth(Omega_m0=Om0, w0=-1.0, wa=0.0, eps_mu=0.0, sigma8_0=sig8)
    psi0 = solve_growth(Omega_m0=Om0, w0=-1.0, wa=0.0, eps_mu=0.0, sigma8_0=sig8)

    # Small departures: mildly running w(a) and small eps_mu
    psi_wa = solve_growth(Omega_m0=Om0, w0=-1.0, wa=+0.05, eps_mu=0.0, sigma8_0=sig8)
    psi_eps = solve_growth(Omega_m0=Om0, w0=-1.0, wa=0.0, eps_mu=+0.05, sigma8_0=sig8)

    # Plots: fs8(z)
    def plot_fs8(label, sol, fname):
        plt.figure(figsize=(6,4))
        plt.plot(sol["z"], sol["fs8"], label=label)
        plt.gca().invert_xaxis()
        plt.xlabel("z"); plt.ylabel(r"$f\sigma_8(z)$")
        plt.legend(); plt.tight_layout()
        plt.savefig(os.path.join(outdir, fname), dpi=150); plt.close()

    plot_fs8("LCDM", base, "fs8_lcdm.png")
    plot_fs8("Reflexive (w=-1, eps=0)", psi0, "fs8_reflexive.png")
    plot_fs8("Reflexive (w_a=+0.05)", psi_wa, "fs8_reflexive_wa.png")
    plot_fs8("Reflexive (eps=+0.05)", psi_eps, "fs8_reflexive_eps.png")

    # Ratios to LCDM
    def plot_ratio(sol, base, fname, label):
        plt.figure(figsize=(6,4))
        plt.plot(sol["z"], sol["fs8"]/base["fs8"] - 1.0, label=label)
        plt.gca().invert_xaxis()
        plt.axhline(0, color='k', lw=0.8, ls='--')
        plt.xlabel("z"); plt.ylabel(r"$f\sigma_8/\,(f\sigma_8)_{\Lambda{\rm CDM}}-1$")
        plt.legend(); plt.tight_layout()
        plt.savefig(os.path.join(outdir, fname), dpi=150); plt.close()

    plot_ratio(psi0, base, "ratio_reflexive.png", "Reflexive / LCDM")
    plot_ratio(psi_wa, base, "ratio_reflexive_wa.png", "Reflexive w_a=+0.05")
    plot_ratio(psi_eps, base, "ratio_reflexive_eps.png", "Reflexive eps=+0.05")

    # Present-day values
    rows = []
    for name, sol in [("LCDM", base), ("Reflexive", psi0),
                      ("Reflexive_wa+0.05", psi_wa), ("Reflexive_eps+0.05", psi_eps)]:
        # z=0 is the last index
        fs8_0 = sol["fs8"][-1]
        f0 = sol["f"][-1]
        rows.append([name, f0, fs8_0])

    with open(os.path.join(outdir,"fs8_summary.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["model","f0","fs8_0"])
        w.writerows(rows)

    print("Wrote e15_growth_outputs/: fs8 plots and fs8_summary.csv")

if __name__ == "__main__":
    main()
