"""
 Multi-pane animation for unified 3-body (two +, one -) with EM+Weak+Gravity

Panels:
- |psi|^2 (density)
- arg(psi) (phase)
- V_em (if enabled)
- V_weak (if enabled)
- curvature K (if enabled)
- gamma_eff (gravity local damping)


"""

import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import itertools


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
        dx -= int(np.sign(dx)) * L
    if abs(dy) > L // 2:
        dy -= int(np.sign(dy)) * L
    return float(np.sqrt(dx * dx + dy * dy))


def main():
    from pr0_system.integration import UnifiedPR0, OverlayConfig

    L = 64
    dt = 0.01
    frames = 800

    cfg = OverlayConfig(
        enable_em=True,
        enable_weak=False,
        enable_gravity=False,
        enable_strong=True,
        em_scale=0.20,
        weak_scale=0.01,
        gravity_scale=0.05,
        strong_scale=1.5,
        weak_gate_distance=5.0,
        density_threshold=0.5,
        gravity_curv_quantile=0.90,
    )
    sysu = UnifiedPR0(L_x=L, L_y=L, overlay=cfg, core_mode="al")

    # Initialize three quarks in small triangle (uud-like: +2/3, +2/3, -1/3 effective)
    # Use unit charges and small inward velocities for capture
    cx, cy = L // 2, L // 2
    tri_side = 10
    h = tri_side * np.sqrt(3.0) / 2.0
    sysu.set_soliton(x0=int(cx - tri_side//2), y0=int(cy - h//3), amplitude=3.0, width=3.0, velocity_x=+0.01, velocity_y=+0.01, charge=+1)
    sysu.set_soliton(x0=int(cx + tri_side//2), y0=int(cy - h//3), amplitude=3.0, width=3.0, velocity_x=-0.01, velocity_y=+0.01, charge=+1)
    sysu.set_soliton(x0=int(cx), y0=int(cy + 2*h//3), amplitude=3.0, width=3.0, velocity_x=0.00, velocity_y=-0.02, charge=-1)

    fig, axes = plt.subplots(2, 3, figsize=(10, 6))
    ax_psi, ax_phase, ax_em, ax_weak, ax_curv, ax_gamma = axes.flatten()
    for ax in axes.flatten():
        ax.set_aspect('equal')
        ax.axis('off')

    dens0 = np.abs(sysu.psi) ** 2
    vmax_d = max(1.0, np.percentile(dens0, 99))
    im_psi = ax_psi.imshow(dens0, cmap='magma', origin='lower', vmin=0, vmax=vmax_d)
    ax_psi.set_title('|psi|^2 + peaks')
    # Peak markers and trails
    coords0 = top3(sysu.psi)
    scat = ax_psi.scatter([c[1] for c in coords0], [c[0] for c in coords0], s=30, c=['cyan','yellow','lime'])
    trails = [ax_psi.plot([], [], linewidth=1.0, alpha=0.8, color=c)[0] for c in ('cyan','yellow','lime')]
    world = [[], [], []]  # per-peak lists of (x,y)
    prev_coords = coords0[:]

    phase0 = np.angle(sysu.psi)
    im_phase = ax_phase.imshow(phase0, cmap='twilight', origin='lower', vmin=-np.pi, vmax=np.pi)
    ax_phase.set_title('arg(psi)')

    # Overlays
    sysu.em_layer.psi = sysu.psi.copy()
    V_em0 = sysu.em_layer._compute_potential_field() if cfg.enable_em else np.zeros_like(dens0)
    vmax_em = max(1e-3, np.percentile(V_em0, 99))
    im_em = ax_em.imshow(V_em0, cmap='viridis', origin='lower', vmin=0, vmax=vmax_em)
    ax_em.set_title('V_em')

    sysu.weak_layer.psi = sysu.psi.copy()
    V_w0 = sysu.weak_layer._compute_potential_field() if cfg.enable_weak else np.zeros_like(dens0)
    vmax_w = max(1e-3, np.percentile(V_w0, 99))
    im_weak = ax_weak.imshow(V_w0, cmap='plasma', origin='lower', vmin=0, vmax=vmax_w)
    ax_weak.set_title('V_weak')

    sysu.gravity_layer.psi = sysu.psi.copy()
    sysu.gravity_layer.chi[:] = 0.0
    sysu.gravity_layer._update_curvature()
    K0 = sysu.gravity_layer.curvature if cfg.enable_gravity else np.zeros_like(dens0)
    vmax_k = max(1e-3, np.percentile(K0, 99))
    im_curv = ax_curv.imshow(K0, cmap='cividis', origin='lower', vmin=0, vmax=vmax_k)
    ax_curv.set_title('Curvature K')

    if cfg.enable_gravity:
        curv = np.clip(K0, 0, 5.0)
        gamma_base, gamma_scale = 0.013, 0.644
        gamma0 = gamma_base + gamma_scale * curv / (curv + 1.0)
    else:
        gamma0 = np.zeros_like(dens0)
    vmax_g = max(1e-3, np.percentile(gamma0, 99))
    im_gamma = ax_gamma.imshow(gamma0, cmap='inferno', origin='lower', vmin=0, vmax=vmax_g)
    ax_gamma.set_title('gamma_eff (gravity)')

    txt = fig.text(0.5, 0.02, '', ha='center', va='bottom', fontsize=10)

    def break_wrap(xs, ys, Lx, Ly):
        bx = []; by = []
        for i in range(len(xs)):
            if i > 0:
                dx = abs(xs[i] - xs[i-1]); dy = abs(ys[i] - ys[i-1])
                if dx > Lx/2 or dy > Ly/2:
                    bx.append(float('nan')); by.append(float('nan'))
            bx.append(xs[i]); by.append(ys[i])
        return bx, by

    def match3(prev, curr, L):
        """Return curr reordered to best match prev under toroidal distance."""
        if len(prev) != 3 or len(curr) != 3:
            return curr
        best = None; best_cost = 1e18
        for perm in itertools.permutations(curr, 3):
            cost = (torus_distance(prev[0], perm[0], L) +
                    torus_distance(prev[1], perm[1], L) +
                    torus_distance(prev[2], perm[2], L))
            if cost < best_cost:
                best_cost = cost; best = list(perm)
        return best if best is not None else curr

    def update(frame_idx):
        nonlocal vmax_d, vmax_em, vmax_w, vmax_k, vmax_g
        sysu.step(dt=dt)
        psi = sysu.psi
        dens = np.abs(psi) ** 2
        # Smooth color scaling to avoid flicker
        target_d = max(1.0, np.percentile(dens, 99))
        vmax_d = 0.9 * vmax_d + 0.1 * target_d
        im_psi.set_clim(0, vmax_d)
        im_psi.set_array(dens)
        im_phase.set_array(np.angle(psi))

        if cfg.enable_em:
            sysu.em_layer.psi = psi.copy()
            V_em = sysu.em_layer._compute_potential_field()
            target = max(1e-3, np.percentile(V_em, 99))
            vmax_em = 0.9 * vmax_em + 0.1 * target
            im_em.set_clim(0, vmax_em)
            im_em.set_array(V_em)
        if cfg.enable_weak:
            sysu.weak_layer.psi = psi.copy()
            V_w = sysu.weak_layer._compute_potential_field()
            target = max(1e-3, np.percentile(V_w, 99))
            vmax_w = 0.9 * vmax_w + 0.1 * target
            im_weak.set_clim(0, vmax_w)
            im_weak.set_array(V_w)
        if cfg.enable_gravity:
            sysu.gravity_layer.psi = psi.copy()
            sysu.gravity_layer.chi[:] = 0.0
            sysu.gravity_layer._update_curvature()
            K = sysu.gravity_layer.curvature
            target = max(1e-3, np.percentile(K, 99))
            vmax_k = 0.9 * vmax_k + 0.1 * target
            im_curv.set_clim(0, vmax_k)
            im_curv.set_array(K)
            curv = np.clip(K, 0, 5.0)
            gamma_base, gamma_scale = 0.013, 0.644
            gamma = gamma_base + gamma_scale * curv / (curv + 1.0)
            target = max(1e-3, np.percentile(gamma, 99))
            vmax_g = 0.9 * vmax_g + 0.1 * target
            im_gamma.set_clim(0, vmax_g)
            im_gamma.set_array(gamma)

        # Peaks and trails
        coords_raw = top3(psi)
        coords = match3(prev_coords, coords_raw, L)
        prev_coords[:] = coords
        scat.set_offsets(np.array([[c[1], c[0]] for c in coords]))
        for i, (y, x) in enumerate(coords):
            world[i].append((x, y))
            xs = [p[0] for p in world[i]]
            ys = [p[1] for p in world[i]]
            xb, yb = break_wrap(xs, ys, L, L)
            trails[i].set_data(xb, yb)

        p = sorted(coords, key=lambda c: c[1])
        d12 = torus_distance(p[0], p[1], L)
        d23 = torus_distance(p[1], p[2], L)
        txt.set_text(f't={frame_idx:04d}  d12={d12:5.1f} d23={d23:5.1f}')
        return [im_psi, scat, im_phase, im_em, im_weak, im_curv, im_gamma, txt] + trails

    out_dir = Path(__file__).resolve().parent.parent.parent / 'media'
    out_dir.mkdir(parents=True, exist_ok=True)
    out_mp4 = out_dir / 'unified_all_forces_3body.mp4'

    ani = animation.FuncAnimation(fig, update, frames=frames, interval=1, blit=False)
    if animation.writers.is_available('ffmpeg'):
        writer = animation.FFMpegWriter(fps=15, bitrate=2000)
        ani.save(out_mp4, writer=writer)
        print('Saved', out_mp4)
    else:
        out_gif = out_dir / 'unified_all_forces_3body.gif'
        ani.save(out_gif, writer=animation.PillowWriter(fps=12))
        print('Saved', out_gif)


if __name__ == '__main__':
    main()


