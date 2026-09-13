"""
 Animate unified 2-body with all forces (Strong core + EM + Weak + Gravity)

Cross-refs:
- # See pr0_system/PR0_SYSTEM_TECHNICAL_OVERVIEW.md
"""

import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.animation as animation


def main():
    from pr0_system.integration import UnifiedPR0, OverlayConfig

    L = 64
    dt = 0.01
    frames = 600

    cfg = OverlayConfig(
        enable_em=True,
        enable_weak=True,
        enable_gravity=True,
        em_scale=0.15,
        weak_scale=0.01,
        gravity_scale=0.05,
        weak_gate_distance=5.0,
        density_threshold=0.5,
        gravity_curv_quantile=0.90,
    )

    sysu = UnifiedPR0(L_x=L, L_y=L, overlay=cfg, core_mode="strong")

    # Initialize two opposite charges
    sysu.set_soliton(x0=L//2 - 10, y0=L//2, amplitude=3.0, width=3.0, velocity_x=+0.03, charge=+1)
    sysu.set_soliton(x0=L//2 + 10, y0=L//2, amplitude=3.0, width=3.0, velocity_x=-0.03, charge=-1)

    fig, ax = plt.subplots(figsize=(6, 6))
    im = ax.imshow(np.abs(sysu.psi) ** 2, cmap='magma', vmin=0, vmax=400, animated=True)
    ax.set_title('Unified PR-0: 2-body (All Forces)')
    ax.axis('off')

    def update(_):
        sysu.step(dt=dt)
        dens = np.abs(sysu.psi) ** 2
        im.set_array(dens)
        return [im]

    out_dir = Path(__file__).resolve().parent.parent.parent / 'media'
    out_dir.mkdir(parents=True, exist_ok=True)
    out_mp4 = out_dir / 'unified_all_forces_2body.mp4'

    if animation.writers.is_available('ffmpeg'):
        writer = animation.FFMpegWriter(fps=15, bitrate=1800)
    else:
        # Fallback to GIF via Pillow if ffmpeg is unavailable
        out_gif = out_dir / 'unified_all_forces_2body.gif'
        ani = animation.FuncAnimation(fig, update, frames=frames, interval=1, blit=True)
        ani.save(out_gif, writer=animation.PillowWriter(fps=15))
        print('Saved', out_gif)
        return

    ani = animation.FuncAnimation(fig, update, frames=frames, interval=1, blit=True)
    ani.save(out_mp4, writer=writer)
    print('Saved', out_mp4)


if __name__ == '__main__':
    main()


