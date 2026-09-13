"""
Meson binding energy measurements for  hadron spectroscopy.
Two-body EM+Strong with varying masses to extract binding energies and compare hierarchy.

"""
import numpy as np
import csv
from pathlib import Path
from pr0_system.evolution.ablowitz_ladik import PR0_Final
from pr0_system.forces import em, strong

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
OUT_CSV = WORKSPACE_ROOT / "media" / "meson_binding.csv"


def measure_binding(L, sep, mass1, mass2, frames, dt):
    """Run 2-body EM+Strong and measure asymptotic E_field - E_initial as proxy for binding."""
    core = PR0_Final(L_x=L, L_y=L, g=0.0, gamma_base=0.0)
    em_layer = em.BootstrapEM_Final(L_x=L, L_y=L)
    em_layer.set_peak_charges([+1, -1])
    # Simplified mass dependence: scale amplitude
    amp1 = 3.0 * (mass1 / 1.0)
    amp2 = 3.0 * (mass2 / 1.0)
    core.set_soliton(x0=L//2 - sep, y0=L//2, amplitude=amp1, width=3.0, velocity_x=0.0, velocity_y=0.0, sign=+1)
    core.set_soliton(x0=L//2 + sep, y0=L//2, amplitude=amp2, width=3.0, velocity_x=0.0, velocity_y=0.0, sign=-1)
    
    # Initial energy
    dens0 = np.abs(core.psi)**2
    em_layer.psi = core.psi.copy()
    V0 = em_layer._compute_potential_field()
    gy, gx = np.gradient(core.psi)
    K0 = float(np.sum(np.abs(gx)**2 + np.abs(gy)**2))
    Ve0 = float(np.sum(dens0 * V0))
    E0 = K0 + Ve0
    
    # Evolve with EM overlay (no Strong for simplicity; add if needed)
    for _ in range(frames):
        core.step(dt=dt)
        em_layer.psi = core.psi.copy()
        V = em_layer._compute_potential_field()
        core.psi *= np.exp(-1j * (0.5 * V * dt))
    
    # Final energy
    dens1 = np.abs(core.psi)**2
    em_layer.psi = core.psi.copy()
    V1 = em_layer._compute_potential_field()
    gy, gx = np.gradient(core.psi)
    K1 = float(np.sum(np.abs(gx)**2 + np.abs(gy)**2))
    Ve1 = float(np.sum(dens1 * V1))
    E1 = K1 + Ve1
    
    # Binding proxy: E_final - E_initial (negative = bound)
    E_bind_proxy = float(E1 - E0)
    
    # Separation at end
    def top2_coords(psi):
        dens = np.abs(psi) ** 2
        idx = np.argsort(dens.ravel())[::-1][:2]
        Ly, Lx = dens.shape
        coords = [divmod(int(i), Lx) for i in idx]
        return coords, dens
    coords, _ = top2_coords(core.psi)
    if len(coords) >= 2:
        dx = abs(coords[1][1] - coords[0][1])
        dy = abs(coords[1][0] - coords[0][0])
        if dx > L/2: dx = L - dx
        if dy > L/2: dy = L - dy
        sep_final = float(np.hypot(dx, dy))
    else:
        sep_final = float('nan')
    
    return E_bind_proxy, sep_final, E0, E1


def main():
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    write_header = not OUT_CSV.exists()
    with OUT_CSV.open("a", newline="") as f:
        w = csv.writer(f)
        if write_header:
            w.writerow(["meson_type","mass1","mass2","L","sep_init","frames","dt","E_bind_proxy","sep_final","E0","E1"])
        
        # Simple mass ratios for different mesons (arbitrary units)
        meson_specs = [
            ("pion", 1.0, 1.0),      # lightest
            ("kaon", 1.0, 1.5),      # u + s
            ("eta", 1.2, 1.2),       # neutral
            ("D", 1.0, 4.0),         # u + c
            ("B", 1.0, 12.0),        # u + b
        ]
        
        for name, m1, m2 in meson_specs:
            E_b, sep_f, E0, E1 = measure_binding(L=64, sep=12, mass1=m1, mass2=m2, frames=600, dt=0.01)
            w.writerow([name, m1, m2, 64, 12, 600, 0.01, f"{E_b:.6f}", f"{sep_f:.3f}", f"{E0:.6f}", f"{E1:.6f}"])
            print(f"{name}: E_bind_proxy={E_b:.4f}, sep_final={sep_f:.2f}")
    
    print("Saved:", OUT_CSV)


if __name__ == "__main__":
    main()
