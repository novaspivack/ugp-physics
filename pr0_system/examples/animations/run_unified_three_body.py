"""
UnifiedPR0: 3-body EM + Gravity (two +, one -) with logging
"""

import numpy as np
import time
from pathlib import Path


def top3(psi: np.ndarray):
    dens = np.abs(psi) ** 2
    flat = dens.flatten()
    idx = np.argsort(flat)[::-1][:3]
    L_y, L_x = psi.shape
    return [divmod(int(i), L_x) for i in idx]


def torus_distance(a, b, L):
    y1, x1 = a
    y2, x2 = b
    dx, dy = x2 - x1, y2 - y1
    if abs(dx) > L // 2:
        dx = dx - int(np.sign(dx)) * L
    if abs(dy) > L // 2:
        dy = dy - int(np.sign(dy)) * L
    return float(np.sqrt(dx * dx + dy * dy))


def main():
    from pr0_system.integration import UnifiedPR0, OverlayConfig

    L = 48
    dt = 0.01
    steps = 1200

    cfg = OverlayConfig(enable_em=True, enable_weak=False, enable_gravity=True,
                        em_scale=0.25, gravity_scale=0.05,
                        gravity_curv_quantile=0.90)
    sysu = UnifiedPR0(L_x=L, L_y=L, overlay=cfg, core_mode="strong")

    y0 = L // 2
    sysu.set_soliton(x0=14, y0=y0, amplitude=3.0, width=3.0, velocity_x=+0.02, charge=+1)
    sysu.set_soliton(x0=24, y0=y0, amplitude=3.0, width=3.0, velocity_x=0.00,  charge=-1)
    sysu.set_soliton(x0=34, y0=y0, amplitude=3.0, width=3.0, velocity_x=-0.02, charge=+1)

    out_dir = Path(__file__).resolve().parent.parent.parent / 'media'
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / 'unified_three_body.csv'
    f = out_file.open('w')
    f.write('t,d12,d23,d13,max_dens\n')

    print("== UnifiedPR0: 3-body EM+Gravity (logging) ==")
    print(f"Grid: {L}x{L}, dt={dt}, steps={steps}")
    print(f"Logging: {out_file}")
    start = time.time()

    for t in range(steps):
        sysu.step(dt=dt)
        if t % 20 == 0 or t == steps - 1:
            p = top3(sysu.psi)
            # order by x
            p = sorted(p, key=lambda c: c[1])
            d12 = torus_distance(p[0], p[1], L)
            d23 = torus_distance(p[1], p[2], L)
            d13 = torus_distance(p[0], p[2], L)
            max_d = float(np.max(np.abs(sysu.psi) ** 2))
            f.write(f"{t},{d12:.4f},{d23:.4f},{d13:.4f},{max_d:.4f}\n")
            f.flush()

    f.close()
    dur = time.time() - start
    print("\nDone.")
    print(f"Runtime: {dur:.2f}s")


if __name__ == '__main__':
    main()


