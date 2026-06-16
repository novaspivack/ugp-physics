"""
 Strong + EM integration smoke test


Purpose:
- Use pr0_system as the canonical codebase.
- Evolve a strong-binding system and apply an EM potential overlay each step.
- Verify that binding persists with EM present and log basic metrics.
"""

import numpy as np
from pathlib import Path
import sys
import time


def measure_separation(psi: np.ndarray) -> float:
    dens = np.abs(psi) ** 2
    flat = dens.flatten()
    idx = np.argsort(flat)[::-1][:2]
    if flat[idx[1]] < 1.0:
        return 0.0
    L_y, L_x = psi.shape
    y1, x1 = divmod(idx[0], L_x)
    y2, x2 = divmod(idx[1], L_x)
    dx, dy = x2 - x1, y2 - y1
    if abs(dx) > L_x // 2:
        dx = dx - np.sign(dx) * L_x
    if abs(dy) > L_y // 2:
        dy = dy - np.sign(dy) * L_y
    return float(np.sqrt(dx * dx + dy * dy))


def main():
    from pr0_system.forces import strong, em

    L = 32
    dt = 0.01
    steps = 1000

    system = strong.BootstrapPR0(L_x=L, L_y=L)
    em_layer = em.BootstrapEM_Final(L_x=L, L_y=L)

    # Initialize two opposite-charge solitons
    system.set_soliton(x0=12, y0=16, amplitude=3.0, width=3.0, velocity_x=+0.04, charge=+1)
    system.set_soliton(x0=20, y0=16, amplitude=3.0, width=3.0, velocity_x=-0.04, charge=-1)

    # Sync EM layer's psi for potential computation baseline
    em_layer.psi = system.psi.copy()

    print("== Strong + EM Integration Smoke Test ==")
    print(f"Grid: {L}x{L}, dt={dt}, steps={steps}")
    start = time.time()

    sep_hist = []
    max_d_hist = []

    for t in range(steps):
        # Compute EM potential from current field
        em_layer.psi = system.psi.copy()
        V = em_layer._compute_potential_field()  # using internal routine for experiment

        # Take strong step
        system.step(dt=dt)

        # Apply EM overlay: dψ/dt ← dψ/dt - V·ψ (Euler kick)
        # Here: approximate by direct Euler update
        system.psi += (-V * system.psi) * dt

        if t % 50 == 0 or t == steps - 1:
            dens = np.abs(system.psi) ** 2
            sep = measure_separation(system.psi)
            sep_hist.append(sep)
            max_d = float(np.max(dens))
            max_d_hist.append(max_d)
            print(f"t={t:4d}  sep={sep:5.1f}  max|ψ|²={max_d:6.2f}")

    dur = time.time() - start
    print("\nDone.")
    print(f"Runtime: {dur:.2f}s")
    if sep_hist:
        print(f"Separation: mean={np.mean(sep_hist):.2f}, last={sep_hist[-1]:.2f}")
        print(f"Max |ψ|²: mean={np.mean(max_d_hist):.2f}, last={max_d_hist[-1]:.2f}")


if __name__ == "__main__":
    main()


