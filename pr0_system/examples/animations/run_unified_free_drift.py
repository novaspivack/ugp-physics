"""
 Unified free-drift test (moving particles, periodic BC)
Logs peak positions, separations, and max density.
"""

import numpy as np
import time
from pathlib import Path


def find_top2(psi: np.ndarray):
    dens = np.abs(psi) ** 2
    flat = dens.flatten()
    idx = np.argsort(flat)[::-1][:2]
    L_y, L_x = psi.shape
    return [divmod(int(i), L_x) for i in idx]


def torus_sep(a, b, Lx, Ly):
    y1, x1 = a
    y2, x2 = b
    dx, dy = x2 - x1, y2 - y1
    if abs(dx) > Lx // 2:
        dx -= int(np.sign(dx)) * Lx
    if abs(dy) > Ly // 2:
        dy -= int(np.sign(dy)) * Ly
    return float(np.sqrt(dx * dx + dy * dy))


def main():
    from pr0_system.integration import UnifiedPR0, OverlayConfig

    L = 64
    dt = 0.01
    steps = 1200

    cfg = OverlayConfig(enable_em=False, enable_weak=False, enable_gravity=False)
    sysu = UnifiedPR0(L_x=L, L_y=L, overlay=cfg, core_mode="strong")

    # Opposite charges moving right/left; periodic domain
    sysu.set_soliton(x0=L//2 - 20, y0=L//2, amplitude=3.0, width=3.0, velocity_x=+0.04, charge=+1)
    sysu.set_soliton(x0=L//2 + 20, y0=L//2, amplitude=3.0, width=3.0, velocity_x=-0.04, charge=-1)

    out_dir = Path(__file__).resolve().parent.parent.parent / 'media'
    out_dir.mkdir(parents=True, exist_ok=True)
    out_csv = out_dir / 'unified_free_drift.csv'
    f = out_csv.open('w')
    f.write('t,x1,y1,x2,y2,sep,max_dens\n')

    print("== Unified Free Drift (Periodic) ==")
    print(f"Logging: {out_csv}")
    start = time.time()

    for t in range(steps):
        sysu.step(dt=dt)
        p = find_top2(sysu.psi)
        sep = torus_sep(p[0], p[1], L, L)
        max_d = float(np.max(np.abs(sysu.psi) ** 2))
        if t % 10 == 0 or t == steps - 1:
            f.write(f"{t},{p[0][1]},{p[0][0]},{p[1][1]},{p[1][0]},{sep:.4f},{max_d:.4f}\n")
            f.flush()

    f.close()
    dur = time.time() - start
    print("Done. Runtime:", f"{dur:.2f}s")


if __name__ == '__main__':
    main()


