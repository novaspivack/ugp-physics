"""
 Strong + Gravity integration smoke test (geometric damping overlay)

"""

import numpy as np
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
    from pr0_system.forces import strong, gravity

    L = 32
    dt = 0.01
    steps = 800

    system = strong.BootstrapPR0(L_x=L, L_y=L)
    grav = gravity.BootstrapGravity(L_x=L, L_y=L)

    # Two masses
    system.set_soliton(x0=12, y0=16, amplitude=3.0, width=3.0, velocity_x=+0.03, charge=+1)
    system.set_soliton(x0=20, y0=16, amplitude=3.0, width=3.0, velocity_x=-0.03, charge=-1)

    # Overlay controls
    gravity_scale = 0.10  # scale down damping strength
    curvature_quantile = 0.90  # apply only where curvature is high

    print("== Strong + Gravity Integration Smoke Test (scaled/gated) ==")
    print(f"Grid: {L}x{L}, dt={dt}, steps={steps}, scale={gravity_scale}, curve>=Q{int(curvature_quantile*100)}")
    start = time.time()

    for t in range(steps):
        # Update gravity curvature based on current energy
        grav.psi = system.psi.copy()
        grav.chi[:] = 0.0
        grav._update_curvature()

        curvature_safe = np.clip(grav.curvature, 0, 5.0)
        gamma_base, gamma_scale = 0.013, 0.644
        gamma_loc = gamma_base + gamma_scale * curvature_safe / (curvature_safe + 1.0)
        gamma_loc = np.clip(gamma_loc, gamma_base, 1.0)

        # Gate by high-curvature regions
        thr = np.quantile(curvature_safe, curvature_quantile)
        mask = (curvature_safe >= thr)
        gamma_eff = gravity_scale * gamma_loc * mask

        # Strong step
        system.step(dt=dt)

        # Apply geometric damping overlay (scaled & gated)
        system.psi += (-gamma_eff * system.psi) * dt

        if t % 50 == 0 or t == steps - 1:
            sep = measure_separation(system.psi)
            max_d = float(np.max(np.abs(system.psi) ** 2))
            print(f"t={t:4d}  sep={sep:5.1f}  max|ψ|²={max_d:6.2f}")

    dur = time.time() - start
    print("\nDone.")
    print(f"Runtime: {dur:.2f}s")


if __name__ == "__main__":
    main()


