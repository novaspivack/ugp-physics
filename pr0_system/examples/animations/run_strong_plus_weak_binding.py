"""
 Strong + Weak integration smoke test (Yukawa overlay)

"""

import numpy as np
import time
from scipy.ndimage import distance_transform_edt


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
    from pr0_system.forces import strong, weak

    L = 32
    dt = 0.01
    steps = 800

    system = strong.BootstrapPR0(L_x=L, L_y=L)
    weak_layer = weak.BootstrapWeak_Final(L_x=L, L_y=L)

    # Start close (touch-range bias)
    system.set_soliton(x0=14, y0=16, amplitude=3.0, width=3.0, velocity_x=+0.02, charge=+1)
    system.set_soliton(x0=18, y0=16, amplitude=3.0, width=3.0, velocity_x=-0.02, charge=-1)

    # Overlay controls (proximity-gated)
    overlay_scale = 0.05   # lower strength
    gate_distance = 5.0    # apply where proximity to a soliton is within this many cells
    density_threshold = 0.5

    print("== Strong + Weak Integration Smoke Test (proximity-gated) ==")
    print(f"Grid: {L}x{L}, dt={dt}, steps={steps}, scale={overlay_scale}, gate<= {gate_distance}")
    start = time.time()

    for t in range(steps):
        # Compute Yukawa field from current configuration
        weak_layer.psi = system.psi.copy()
        V = weak_layer._compute_potential_field()

        # Strong step
        system.step(dt=dt)

        # Proximity map from current density
        dens = np.abs(system.psi) ** 2
        mask = (dens > density_threshold).astype(float)
        sep_map = distance_transform_edt(1.0 - mask)
        near = (sep_map <= gate_distance)

        V_eff = overlay_scale * V * near

        # Apply short-range attraction overlay (Yukawa)
        system.psi += (-V_eff * system.psi) * dt

        if t % 50 == 0 or t == steps - 1:
            sep = measure_separation(system.psi)
            max_d = float(np.max(np.abs(system.psi) ** 2))
            print(f"t={t:4d}  sep={sep:5.1f}  max|ψ|²={max_d:6.2f}")

    dur = time.time() - start
    print("\nDone.")
    print(f"Runtime: {dur:.2f}s")


if __name__ == "__main__":
    main()


