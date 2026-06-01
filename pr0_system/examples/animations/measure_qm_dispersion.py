"""
QM emergence validation: dispersion relation ω(k) and ℏ extraction.

Evolve plane-wave packets at different k, measure frequency ω via phase accumulation,
plot ω(k) and fit to quadratic ω = ℏ k² / (2m) to extract effective Planck's constant.

"""
import numpy as np
import csv
from pathlib import Path
import matplotlib.pyplot as plt
from pr0_system.evolution.ablowitz_ladik import PR0_Final

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
OUT_CSV = WORKSPACE_ROOT / "media" / "qm_dispersion.csv"
OUT_PNG = WORKSPACE_ROOT / "media" / "dispersion_relation_omega_k.png"


def measure_omega(k_x, k_y, L, frames, dt):
    """Evolve a plane-wave packet and measure frequency ω from phase accumulation."""
    core = PR0_Final(L_x=L, L_y=L, g=0.0, gamma_base=0.0)
    # Initialize plane wave: psi = exp(i k·x)
    yy, xx = np.meshgrid(np.arange(L), np.arange(L), indexing='ij')
    core.psi = np.exp(1j * (k_x * xx + k_y * yy))
    
    # Track phase at a fixed point
    y0, x0 = L//2, L//2
    phases = []
    for t in range(frames):
        phases.append(np.angle(core.psi[y0, x0]))
        core.step(dt=dt)
    
    # Unwrap and fit slope
    phases_arr = np.unwrap(np.array(phases))
    ts = np.arange(len(phases)) * dt
    # Linear fit: phase ≈ ω t
    if len(ts) > 1:
        slope, _ = np.polyfit(ts, phases_arr, 1)
        omega = float(-slope)  # convention: -dφ/dt = ω
    else:
        omega = 0.0
    
    return omega


def main():
    L = 64
    frames = 200
    dt = 0.01
    
    # Sample k-space
    k_vals = np.linspace(0.1, 1.5, 10)
    results = []
    
    for k_mag in k_vals:
        # Use k along x for simplicity
        omega = measure_omega(k_x=k_mag, k_y=0.0, L=L, frames=frames, dt=dt)
        results.append((k_mag, omega))
        print(f"k={k_mag:.3f}, ω={omega:.6f}")
    
    # Save CSV
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["k_mag","omega","L","frames","dt"])
        for k, om in results:
            w.writerow([k, om, L, frames, dt])
    print("Saved:", OUT_CSV)
    
    # Plot ω(k) and fit quadratic
    k_arr = np.array([r[0] for r in results])
    om_arr = np.array([r[1] for r in results])
    
    # Fit ω = A k²
    A = float(np.dot(om_arr, k_arr**2) / np.dot(k_arr**2, k_arr**2))
    fit = A * k_arr**2
    
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(k_arr, om_arr, 'o', label='measured ω')
    ax.plot(k_arr, fit, '-', label=f'ω = {A:.4f} k² (fit)')
    ax.set_xlabel('k (wave number)')
    ax.set_ylabel('ω (frequency)')
    ax.set_title(f'Dispersion relation (ℏ_eff ≈ 2m·A = {2.0*A:.4f})')
    ax.grid(True, alpha=0.3)
    ax.legend()
    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=150)
    plt.close(fig)
    print("Saved:", OUT_PNG)


if __name__ == "__main__":
    main()
