"""

"""

import numpy as np
import time
from pathlib import Path


def measure_sep(psi: np.ndarray) -> float:
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
        dx = dx - int(np.sign(dx)) * L_x
    if abs(dy) > L_y // 2:
        dy = dy - int(np.sign(dy)) * L_y
    return float(np.sqrt(dx * dx + dy * dy))


def main():
    from pr0_system.integration import UnifiedPR0, OverlayConfig

    L = 32
    dt = 0.01
    steps = 1200

    cfg = OverlayConfig(enable_em=True, enable_weak=True, enable_gravity=True,
                        em_scale=0.15, weak_scale=0.01, gravity_scale=0.05,
                        weak_gate_distance=5.0, density_threshold=0.5,
                        gravity_curv_quantile=0.90)
    sysu = UnifiedPR0(L_x=L, L_y=L, overlay=cfg, core_mode="strong")

    sysu.set_soliton(x0=12, y0=16, amplitude=3.0, width=3.0, velocity_x=+0.03, charge=+1)
    sysu.set_soliton(x0=20, y0=16, amplitude=3.0, width=3.0, velocity_x=-0.03, charge=-1)

    out_dir = Path(__file__).resolve().parent
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / 'unified_timeseries.csv'
    f = out_file.open('w')
    f.write('t,sep,max_dens\n')

    print("== UnifiedPR0: EM+Weak+Gravity (logging) ==")
    print(f"Grid: {L}x{L}, dt={dt}, steps={steps}")
    print(f"Logging: {out_file}")
    start = time.time()

    for t in range(steps):
        sysu.step(dt=dt)
        if t % 20 == 0 or t == steps - 1:
            sep = measure_sep(sysu.psi)
            max_d = float(np.max(np.abs(sysu.psi) ** 2))
            f.write(f"{t},{sep:.4f},{max_d:.4f}\n")
            f.flush()

    f.close()
    dur = time.time() - start
    print("\nDone.")
    print(f"Runtime: {dur:.2f}s")


if __name__ == "__main__":
    main()


