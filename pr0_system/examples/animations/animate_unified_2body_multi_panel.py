"""
 Multi-pane animation for unified 2-body (Strong core + EM + Weak + Gravity)

Panels:
- |psi|^2 (density)
- arg(psi) (phase)
- V_em (if enabled)
- V_weak (if enabled)
- curvature K (if enabled)
- gamma_eff (gravity local damping) or sep map

"""

import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.animation as animation


def measure_sep(psi: np.ndarray) -> float:
    dens = np.abs(psi) ** 2
    flat = dens.flatten()
    idx = np.argsort(flat)[::-1][:2]
    if flat[idx[1]] < 1.0:
        return 0.0
    L_y, L_x = psi.shape
    y1, x1 = divmod(int(idx[0]), L_x)
    y2, x2 = divmod(int(idx[1]), L_x)
    dx, dy = x2 - x1, y2 - y1
    if abs(dx) > L_x // 2:
        dx -= int(np.sign(dx)) * L_x
    if abs(dy) > L_y // 2:
        dy -= int(np.sign(dy)) * L_y
    return float(np.sqrt(dx * dx + dy * dy))


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

    # Initialize two opposite charges moving towards each other
    sysu.set_soliton(x0=L//2 - 12, y0=L//2, amplitude=3.0, width=3.0, velocity_x=+0.03, charge=+1)
    sysu.set_soliton(x0=L//2 + 12, y0=L//2, amplitude=3.0, width=3.0, velocity_x=-0.03, charge=-1)

    # Figure with 2x3 grid
    fig, axes = plt.subplots(2, 3, figsize=(10, 6))
    ax_psi, ax_phase, ax_em, ax_weak, ax_curv, ax_gamma = axes.flatten()
    for ax in axes.flatten():
        ax.axis('off')

    dens0 = np.abs(sysu.psi) ** 2
    im_psi = ax_psi.imshow(dens0, cmap='magma', vmin=0, vmax=max(1.0, np.percentile(dens0, 99)))
    ax_psi.set_title('|psi|^2')

    phase0 = np.angle(sysu.psi)
    im_phase = ax_phase.imshow(phase0, cmap='twilight', vmin=-np.pi, vmax=np.pi)
    ax_phase.set_title('arg(psi)')

    # Pre-allocate overlays
    sysu.em_layer.psi = sysu.psi.copy()
    V_em0 = sysu.em_layer._compute_potential_field() if cfg.enable_em else np.zeros_like(dens0)
    im_em = ax_em.imshow(V_em0, cmap='viridis', vmin=0, vmax=max(1e-3, np.percentile(V_em0, 99)))
    ax_em.set_title('V_em')

    sysu.weak_layer.psi = sysu.psi.copy()
    V_w0 = sysu.weak_layer._compute_potential_field() if cfg.enable_weak else np.zeros_like(dens0)
    im_weak = ax_weak.imshow(V_w0, cmap='plasma', vmin=0, vmax=max(1e-3, np.percentile(V_w0, 99)))
    ax_weak.set_title('V_weak')

    sysu.gravity_layer.psi = sysu.psi.copy()
    sysu.gravity_layer.chi[:] = 0.0
    sysu.gravity_layer._update_curvature()
    K0 = sysu.gravity_layer.curvature if cfg.enable_gravity else np.zeros_like(dens0)
    im_curv = ax_curv.imshow(K0, cmap='cividis', vmin=0, vmax=max(1e-3, np.percentile(K0, 99)))
    ax_curv.set_title('Curvature K')

    # gamma_eff
    if cfg.enable_gravity:
        curv = np.clip(K0, 0, 5.0)
        gamma_base, gamma_scale = 0.013, 0.644
        gamma0 = gamma_base + gamma_scale * curv / (curv + 1.0)
    else:
        gamma0 = np.zeros_like(dens0)
    im_gamma = ax_gamma.imshow(gamma0, cmap='inferno', vmin=0, vmax=max(1e-3, np.percentile(gamma0, 99)))
    ax_gamma.set_title('gamma_eff (gravity)')

    txt = fig.text(0.5, 0.02, '', ha='center', va='bottom', fontsize=10)

    def update(frame_idx):
        sysu.step(dt=dt)
        psi = sysu.psi
        dens = np.abs(psi) ** 2
        im_psi.set_array(dens)

        phase = np.angle(psi)
        im_phase.set_array(phase)

        # EM potential
        if cfg.enable_em:
            sysu.em_layer.psi = psi.copy()
            V_em = sysu.em_layer._compute_potential_field()
            im_em.set_array(V_em)

        # Weak potential
        if cfg.enable_weak:
            sysu.weak_layer.psi = psi.copy()
            V_w = sysu.weak_layer._compute_potential_field()
            im_weak.set_array(V_w)

        # Curvature and gamma
        if cfg.enable_gravity:
            sysu.gravity_layer.psi = psi.copy()
            sysu.gravity_layer.chi[:] = 0.0
            sysu.gravity_layer._update_curvature()
            K = sysu.gravity_layer.curvature
            im_curv.set_array(K)
            curv = np.clip(K, 0, 5.0)
            gamma_base, gamma_scale = 0.013, 0.644
            gamma = gamma_base + gamma_scale * curv / (curv + 1.0)
            im_gamma.set_array(gamma)

        sep = measure_sep(psi)
        txt.set_text(f't={frame_idx:04d}  sep={sep:5.1f}')
        return [im_psi, im_phase, im_em, im_weak, im_curv, im_gamma, txt]

    out_dir = Path(__file__).resolve().parent.parent.parent / 'media'
    out_dir.mkdir(parents=True, exist_ok=True)
    out_mp4 = out_dir / 'unified_2body_all_forces_multipanel.mp4'

    ani = animation.FuncAnimation(fig, update, frames=frames, interval=1, blit=False)
    if animation.writers.is_available('ffmpeg'):
        writer = animation.FFMpegWriter(fps=15, bitrate=2000)
        ani.save(out_mp4, writer=writer)
        print('Saved', out_mp4)
    else:
        out_gif = out_dir / 'unified_2body_all_forces_multipanel.gif'
        ani.save(out_gif, writer=animation.PillowWriter(fps=12))
        print('Saved', out_gif)


if __name__ == '__main__':
    main()


