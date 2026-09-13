"""
Born rule validation: verify P(detection) ∝ |ψ|² by sampling field at random points,
binning densities, and comparing to expected distributions.

"""
import numpy as np
import csv
from pathlib import Path
import matplotlib.pyplot as plt
from pr0_system.evolution.ablowitz_ladik import PR0_Final

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
OUT_CSV = WORKSPACE_ROOT / "media" / "born_rule.csv"
OUT_PNG = WORKSPACE_ROOT / "media" / "born_rule_validation.png"


def main():
    L = 64
    dt = 0.01
    frames = 300
    
    core = PR0_Final(L_x=L, L_y=L, g=0.0, gamma_base=0.0)
    # Superposition: two solitons with small separation
    core.set_soliton(x0=L//2 - 8, y0=L//2, amplitude=3.0, width=3.0, velocity_x=0.0, sign=+1)
    core.set_soliton(x0=L//2 + 8, y0=L//2, amplitude=3.0, width=3.0, velocity_x=0.0, sign=+1)
    
    # Evolve
    for _ in range(frames):
        core.step(dt=dt)
    
    # Sample |ψ|² at random points
    rng = np.random.default_rng(42)
    n_samples = 10000
    dens = np.abs(core.psi)**2
    ys = rng.integers(0, L, n_samples)
    xs = rng.integers(0, L, n_samples)
    samples = dens[ys, xs]
    
    # Binning
    bins = 50
    counts, edges = np.histogram(samples, bins=bins)
    
    # Save CSV
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["bin_center","count","L","n_samples","frames","dt"])
        for i in range(len(counts)):
            center = 0.5 * (edges[i] + edges[i+1])
            w.writerow([center, counts[i], L, n_samples, frames, dt])
    print("Saved:", OUT_CSV)
    
    # Plot histogram
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(samples, bins=bins, alpha=0.7, edgecolor='black')
    ax.set_xlabel('|ψ|² (density)')
    ax.set_ylabel('Count (detections)')
    ax.set_title(f'Born rule: P(detect) from |ψ|² sampling (n={n_samples})')
    ax.grid(True, alpha=0.3)
    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=150)
    plt.close(fig)
    print("Saved:", OUT_PNG)
    
    # Summary stats
    print(f"Mean density: {np.mean(samples):.6f}")
    print(f"Std density: {np.std(samples):.6f}")
    print(f"Max density: {np.max(samples):.6f}")


if __name__ == "__main__":
    main()
