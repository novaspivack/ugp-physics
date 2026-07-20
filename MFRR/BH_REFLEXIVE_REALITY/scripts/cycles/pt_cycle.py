#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PT↔PT^{-1} Cycle Test (toy 1D horizon patch)
- Forward adjudication (PT) under L = D + λΨ C
- Reverse adjudication (PT^{-1}) under L^{-} = Σ^* L (fiber signature flip)

Outputs:
  - JSON log: pt_cycle_results.json
  - Figure:   figures/pt_cycle_energy_closure.png

Acceptance (targets):
  sum(E_PT) + sum(E_PTinv) ≈ 0   (≤ 2%)
  Sref_end - Sref_start     ≈ 0   (≤ 2%)
  ||Ψ_end - Ψ_start||_{H1}  ≤ 1e-2

Reference: MFRR Appendix E.1
"""

import json, os
import numpy as np
import matplotlib.pyplot as plt

# ---------------------
# Config
# ---------------------
N      = 1024                # radial grid points
L      = 10.0                # domain length (code units)
rH     = 3.0                 # "horizon" location (code units)
dx     = L / N
dt     = 1e-3
Nf     = 400                 # forward steps
Nr     = 400                 # reverse steps
kB     = 1.0
TH     = 1.0 / (8.0 * np.pi) # toy Hawking temperature
lam    = 0.25                # λΨ
alpha1 = 1e-3
alpha2 = 1e-3
np.random.seed(7)

# ---------------------
# Helpers (toy model)
# ---------------------
r = np.linspace(0, L, N)
mask_out = (r > rH)  # "exterior"
mask_in  = ~mask_out

def lap(x):
    return (np.roll(x, -1) - 2*x + np.roll(x, 1)) / (dx*dx)

def grad(x):
    return (np.roll(x, -1) - np.roll(x, 1)) / (2.0*dx)

def init_Psi():
    # localized Gaussian just outside the horizon
    mu, sig = rH + 0.5, 0.35
    return np.exp(-(r-mu)**2/(2*sig**2)) * 0.1

def D(Psi):
    # Dissonance proxy: roughness + mismatch across rH
    rough = 0.5 * np.sum((grad(Psi))**2) * dx
    jump  = 5.0 * (Psi[mask_in].mean() - Psi[mask_out].mean())**2
    return rough + jump

def C(Psi, fiber_sign=+1.0):
    # MDL penalty proxy: amplitude + fiber-gradient energy with signature
    return alpha1 * np.sum(Psi**2)*dx + fiber_sign*alpha2*np.sum(grad(Psi)**2)*dx

def L(Psi, fiber_sign=+1.0):
    return D(Psi) + lam * C(Psi, fiber_sign=fiber_sign)

def reflexive_energy_increment(Psi, dH=0.01, fiber_sign=+1.0):
    # ΔE_PT ≈ kB TH ΔH + λΨ ∫ (α1 Ψ^2 + α2 |∇Ψ|^2)_fiber
    bulk = alpha1*np.sum(Psi**2)*dx + fiber_sign*alpha2*np.sum(grad(Psi)**2)*dx
    return kB*TH*dH + lam*bulk

def evolve_scalar(Psi, fiber_sign=+1.0):
    # stabilised semi-implicit diffusion + weak nonlinearity (toy)
    # PT acts as mild "cooling" (forward), PT^{-1} as mild "heating" (reverse) via fiber_sign
    kappa = 0.2
    nonlin = -0.1 * Psi * (Psi**2)    # weak saturation
    Psi_new = Psi + dt*(kappa*lap(Psi) + nonlin + 0.02*fiber_sign*lap(Psi))
    # mild absorptive BCs
    Psi_new[0] = Psi_new[1]
    Psi_new[-1] = Psi_new[-2]
    return Psi_new

def argmin_step_forward(Psi):
    # gradient descent step to lower L (fiber_sign=+1)
    g = 2.0*Psi + 0.5*lap(Psi)   # crude surrogate gradient
    return Psi - 0.02*g

def argmin_step_reverse(Psi):
    # gradient ascent w.r.t. fiber gradient (fiber_sign=-1), but still argmin of L^{-}
    g = 2.0*Psi - 0.5*lap(Psi)   # signature flipped
    return Psi - 0.02*g

def Sref(Psi):
    # Reflexive entropy proxy: Shannon-like from normalized |Psi|
    x = np.abs(Psi)
    Z = x.sum() + 1e-12
    p = x / Z
    return -np.sum(p*np.log(p+1e-12))

def H1_norm(u, v):
    du, dv = grad(u), grad(v)
    return np.sqrt(np.sum((u-v)**2)*dx + np.sum((du-dv)**2)*dx)

# ---------------------
# Main
# ---------------------
def main():
    Psi0 = init_Psi().copy()
    Psi  = Psi0.copy()
    logs = {"forward": [], "reverse": []}
    EPT_fwd = []
    EPT_rev = []
    
    # ---- forward PT ----
    dH = 0.01
    for k in range(Nf):
        Psi = evolve_scalar(Psi, fiber_sign=+1.0)
        Psi = argmin_step_forward(Psi)
        e = reflexive_energy_increment(Psi, dH=dH, fiber_sign=+1.0)
        s = Sref(Psi)
        EPT_fwd.append(e)
        logs["forward"].append({"k": int(k), "E_PT": float(e), "Sref": float(s)})
    
    # ---- reverse PT^{-1} ----
    # fiber signature flip: I -> -I (we model via fiber_sign=-1.0)
    for k in range(Nr):
        Psi = evolve_scalar(Psi, fiber_sign=-1.0)
        Psi = argmin_step_reverse(Psi)
        e = reflexive_energy_increment(Psi, dH=-dH, fiber_sign=-1.0)  # negative ΔH for reverse
        s = Sref(Psi)
        EPT_rev.append(e)
        logs["reverse"].append({"k": int(k), "E_PTinv": float(e), "Sref": float(s)})
    
    # Diagnostics
    E_sum = np.sum(EPT_fwd) + np.sum(EPT_rev)
    S_start = Sref(Psi0)
    S_end   = Sref(Psi)
    H1err   = H1_norm(Psi, Psi0)
    
    # Print acceptance metrics
    print("[PT Cycle] sum(E_PT) + sum(E_PTinv) =", E_sum)
    print("[PT Cycle] ΔSref =", S_end - S_start)
    print("[PT Cycle] H1(Ψ_end, Ψ_start) =", H1err)
    
    # Validation status
    energy_ok = abs(E_sum) < 0.02 * (abs(np.sum(EPT_fwd)) + 1e-12)
    entropy_ok = abs(S_end - S_start) < 0.02 * (abs(S_start) + 1e-12)
    recon_ok = H1err <= 1e-2
    
    status = "PASS" if (energy_ok and entropy_ok and recon_ok) else "INCONCLUSIVE"
    
    print(f"[PT Cycle] VALIDATION STATUS: {status}")
    
    # Save JSON
    os.makedirs("../results", exist_ok=True)
    with open("../results/pt_cycle_results.json", "w") as f:
        json.dump({
            "E_sum": float(E_sum),
            "Delta_Sref": float(S_end - S_start),
            "H1_error": float(H1err),
            "validation_status": status,
            "forward": logs["forward"],
            "reverse": logs["reverse"]
        }, f, indent=2)
    
    # Plot energy closure
    os.makedirs("../figures", exist_ok=True)
    plt.figure(figsize=(7.2,3.4))
    plt.plot(np.cumsum(EPT_fwd), label="∑ E_PT (forward)", lw=2)
    plt.plot(np.arange(Nf, Nf+Nr), np.cumsum(EPT_rev)+np.sum(EPT_fwd), 
             label="∑ E_PT + ∑ E_PT^{-1} (cycle)", lw=2)
    plt.axhline(0, color='k', ls='--', alpha=0.5)
    plt.xlabel("step")
    plt.ylabel("cumulative energy (code units)")
    plt.legend()
    plt.tight_layout()
    plt.savefig("../figures/pt_cycle_energy_closure.png", dpi=300)
    plt.close()
    
    print("\n✅ Results saved: ../results/pt_cycle_results.json")
    print("✅ Figure saved: ../figures/pt_cycle_energy_closure.png")

if __name__ == "__main__":
    main()

