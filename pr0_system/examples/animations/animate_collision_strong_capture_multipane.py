"""
 Multi-pane animation for strong capture head-on collision (+/-)

Panels: |psi|^2, arg(psi); overlays off; focus on wave dynamics and binding
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

    cfg = OverlayConfig(enable_em=False, enable_weak=False, enable_gravity=False)
    sysu = UnifiedPR0(L_x=L, L_y=L, overlay=cfg, core_mode="strong")

    # Opposite charges (+/-) toward each other; strong capture expected at low relative momentum
    sysu.set_soliton(x0=L//2 - 12, y0=L//2, amplitude=3.0, width=3.0, velocity_x=+0.02, charge=+1)
    sysu.set_soliton(x0=L//2 + 12, y0=L//2, amplitude=3.0, width=3.0, velocity_x=-0.02, charge=-1)

    fig, axes = plt.subplots(1, 2, figsize=(8, 4))
    ax_psi, ax_phase = axes
    for ax in axes:
        ax.axis('off')

    dens0 = np.abs(sysu.psi) ** 2
    im_psi = ax_psi.imshow(dens0, cmap='magma', vmin=0, vmax=max(1.0, np.percentile(dens0, 99)))
    ax_psi.set_title('|psi|^2')

    phase0 = np.angle(sysu.psi)
    im_phase = ax_phase.imshow(phase0, cmap='twilight', vmin=-np.pi, vmax=np.pi)
    ax_phase.set_title('arg(psi)')

    txt = fig.text(0.5, 0.02, '', ha='center', va='bottom', fontsize=10)

    def measure_sep(psi: np.ndarray) -> float:
        dens = np.abs(psi) ** 2
        flat = dens.flatten()
        idx = np.argsort(flat)[::-1][:2]
        if flat[idx[1]] < 1.0:
            return 0.0
        y1, x1 = divmod(int(idx[0]), L)
        y2, x2 = divmod(int(idx[1]), L)
        dx, dy = x2 - x1, y2 - y1
        if abs(dx) > L // 2:
            dx -= int(np.sign(dx)) * L
        if abs(dy) > L // 2:
            dy -= int(np.sign(dy)) * L
        return float(np.sqrt(dx * dx + dy * dy))

    def update(frame_idx):
        sysu.step(dt=dt)
        psi = sysu.psi
        dens = np.abs(psi) ** 2
        im_psi.set_array(dens)
        im_phase.set_array(np.angle(psi))
        sep = measure_sep(psi)
        txt.set_text(f't={frame_idx:04d}  sep={sep:5.1f}')
        return [im_psi, im_phase, txt]

    out_dir = Path(__file__).resolve().parent.parent.parent / 'media'
    out_dir.mkdir(parents=True, exist_ok=True)
    out_mp4 = out_dir / 'strong_force_capture.mp4'

    ani = animation.FuncAnimation(fig, update, frames=frames, interval=1, blit=False)
    if animation.writers.is_available('ffmpeg'):
        writer = animation.FFMpegWriter(fps=15, bitrate=2000)
        ani.save(out_mp4, writer=writer)
        print('Saved', out_mp4)
    else:
        out_gif = out_dir / 'strong_force_capture.gif'
        ani.save(out_gif, writer=animation.PillowWriter(fps=12))
        print('Saved', out_gif)


if __name__ == '__main__':
    main()


