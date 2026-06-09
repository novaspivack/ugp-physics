"""
 Three-body EM interaction (multi-pane) using AL core with radial solitons.
Panels: |psi|^2 + peaks/worldlines, arg(psi), V_em, |∇V_em|.
Outputs MP4 to the session visualizations folder.
"""

import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from datetime import datetime
import argparse
import itertools


def parse_charges(s: str):
    vals = []
    for tok in s.split(','):
        tok = tok.strip()
        if tok.startswith('+'):
            vals.append(+1)
        elif tok.startswith('-'):
            vals.append(-1)
        else:
            vals.append(int(tok))
    return vals


def topk_coords(psi: np.ndarray, k: int = 3):
    dens = np.abs(psi) ** 2
    idx = np.argsort(dens.ravel())[::-1][:k]
    Ly, Lx = dens.shape
    coords = [divmod(int(i), Lx) for i in idx]
    return coords, dens


def torus_sep(a, b, Lx, Ly):
    y1, x1 = a; y2, x2 = b
    dx, dy = x2 - x1, y2 - y1
    if abs(dx) > Lx // 2:
        dx -= int(np.sign(dx)) * Lx
    if abs(dy) > Ly // 2:
        dy -= int(np.sign(dy)) * Ly
    return float(np.sqrt(dx * dx + dy * dy))


def match_three(prev, curr, Lx, Ly):
    # brute force minimal sum matching over 3! permutations
    best = None
    best_cost = 1e18
    for perm in itertools.permutations(curr, 3):
        cost = (torus_sep(prev[0], perm[0], Lx, Ly) +
                torus_sep(prev[1], perm[1], Lx, Ly) +
                torus_sep(prev[2], perm[2], Lx, Ly))
        if cost < best_cost:
            best_cost = cost
            best = list(perm)
    return best


def main():
    from pr0_system.evolution.ablowitz_ladik import PR0_Final
    from pr0_system.forces import em

    p = argparse.ArgumentParser(description='Three-body EM multipane animation')
    p.add_argument('--L', type=int, default=96)
    p.add_argument('--dt', type=float, default=0.008)
    p.add_argument('--frames', type=int, default=1800)
    p.add_argument('--sep', type=int, default=12, help='Triangle size parameter')
    p.add_argument('--vy', type=float, default=0.7, help='Base tangential speed magnitude')
    p.add_argument('--vx', type=float, default=0.2, help='Base off-angle speed magnitude')
    p.add_argument('--charges', type=str, default='+1,+1,-1', help='Comma list of three charges, e.g., "+1,+1,-1"')
    p.add_argument('--accel_scale', type=float, default=22.0)
    p.add_argument('--momentum_gain', type=float, default=10.0)
    p.add_argument('--direct_boost', type=float, default=8.0)
    args = p.parse_args()

    Lx = Ly = args.L
    dt = args.dt
    frames = args.frames
    sep = args.sep
    charges = parse_charges(args.charges)
    if len(charges) != 3:
        raise ValueError('charges must contain exactly three entries')

    core = PR0_Final(L_x=Lx, L_y=Ly, g=0.0, gamma_base=0.0)
    cx, cy = Lx // 2, Ly // 2
    # Equilateral triangle offsets (approx): (±sep, 0), (0, 0.866*sep)
    dx = sep
    dy = int(round(0.866 * sep))

    # Initial velocities: small off-angle components; rotate for each vertex
    v_list = [(+args.vx, +args.vy), (-args.vx, +args.vy), (0.0, -args.vy)]
    pos_list = [(cx - dx, cy), (cx + dx, cy), (cx, cy + dy)]

    for (x0, y0), (vx0, vy0), q in zip(pos_list, v_list, charges):
        core.set_soliton(x0=x0, y0=y0, amplitude=3.0, width=3.0,
                         velocity_x=vx0, velocity_y=vy0, sign=+1 if q > 0 else -1)

    em_layer = em.BootstrapEM_Final(L_x=Lx, L_y=Ly)
    em_layer.set_peak_charges(charges)

    fig, axes = plt.subplots(2, 2, figsize=(10, 7))
    ax_d, ax_p, ax_em, ax_grad = axes.flatten()
    for ax in axes.flatten():
        ax.set_aspect('equal')
        ax.axis('off')

    coords, dens0 = topk_coords(core.psi, k=3)
    vmax_d = max(1.0, np.percentile(dens0, 99))
    im_d = ax_d.imshow(dens0, cmap='magma', origin='lower', vmin=0, vmax=vmax_d)
    scat = ax_d.scatter([c[1] for c in coords], [c[0] for c in coords], s=30, c=['cyan','yellow','lime'])
    line1, = ax_d.plot([], [], color='cyan', linewidth=1.0, alpha=0.9)
    line2, = ax_d.plot([], [], color='yellow', linewidth=1.0, alpha=0.9)
    line3, = ax_d.plot([], [], color='lime', linewidth=1.0, alpha=0.9)
    ax_d.set_title('|psi|^2 + peaks (3-body)')

    phase0 = np.angle(core.psi)
    im_p = ax_p.imshow(phase0, cmap='twilight', origin='lower', vmin=-np.pi, vmax=np.pi)
    ax_p.set_title('arg(psi)')

    em_layer.psi = core.psi.copy()
    V0 = em_layer._compute_potential_field()
    vmax_v = max(1e-3, np.percentile(V0, 99))
    im_em = ax_em.imshow(V0, cmap='viridis', origin='lower', vmin=0, vmax=vmax_v)
    ax_em.set_title('V_em')
    dVy0, dVx0 = np.gradient(V0)
    gradmag0 = np.hypot(dVx0, dVy0)
    im_grad = ax_grad.imshow(gradmag0, cmap='magma', origin='lower', vmin=0, vmax=max(1e-6, np.percentile(gradmag0, 99)))
    ax_grad.set_title('|∇V_em|')

    txt = fig.text(0.5, 0.02, '', ha='center', va='bottom', fontsize=10)
    fig.suptitle(f'3-body EM | L={Lx} dt={dt} frames={frames} sep={sep} charges={charges} vy={args.vy} vx={args.vx}', fontsize=11)

    # Trackers
    coords_prev, _ = topk_coords(core.psi, k=3)
    peak_vel = [np.array([0.0, 0.0], dtype=float) for _ in range(3)]  # (vy, vx)
    wl_y = [[float(coords[i][0])] for i in range(3)]
    wl_x = [[float(coords[i][1])] for i in range(3)]

    yy, xx = np.meshgrid(np.arange(Ly), np.arange(Lx), indexing='ij')

    def update(k):
        nonlocal vmax_v
        # EM potential
        em_layer.psi = core.psi.copy()
        V = em_layer._compute_potential_field()
        dVy, dVx = np.gradient(V)
        coords_now, dens_now = topk_coords(core.psi, k=3)
        matched = match_three(coords_prev, coords_now, Lx, Ly)
        coords_prev[:] = matched

        # Acceleration and local momentum imprint
        for i, (y, x) in enumerate(matched):
            yi, xi = int(y), int(x)
            y0, y1 = max(0, yi-1), min(Ly, yi+2)
            x0, x1 = max(0, xi-1), min(Lx, xi+2)
            gy = float(np.mean(dVy[y0:y1, x0:x1]))
            gx = float(np.mean(dVx[y0:y1, x0:x1]))
            ay, ax = -gy, -gx
            peak_vel[i][0] += args.accel_scale * ay * dt
            peak_vel[i][1] += args.accel_scale * ax * dt
            dxv = xx - x; dyv = yy - y
            if np.abs(dxv).mean() > 0:
                dxv = np.where(np.abs(dxv) > Lx // 2, dxv - np.sign(dxv) * Lx, dxv)
            if np.abs(dyv).mean() > 0:
                dyv = np.where(np.abs(dyv) > Ly // 2, dyv - np.sign(dyv) * Ly, dyv)
            r2 = dxv * dxv + dyv * dyv
            mask = np.exp(-r2 / (2.0 * 2.25))
            phase_tilt = args.momentum_gain * (peak_vel[i][1] * dxv + peak_vel[i][0] * dyv) * dt * mask
            core.psi *= np.exp(1j * phase_tilt)
            direct_phase = args.direct_boost * ((-gx) * dxv + (-gy) * dyv) * dt * mask
            core.psi *= np.exp(1j * direct_phase)

        # Evolve core and apply conservative EM potential
        core.step(dt=dt)
        core.psi *= np.exp(-1j * (2.0 * V * dt))

        # Update visuals
        coords_u, dens_u = topk_coords(core.psi, k=3)
        vmax_d_loc = max(1.0, np.percentile(dens_u, 99))
        im_d.set_clim(0, vmax_d_loc)
        im_d.set_array(dens_u)
        scat.set_offsets(np.array([[c[1], c[0]] for c in coords_u]))
        # Worldlines
        for i in range(3):
            wl_y[i].append(float(coords_u[i][0]))
            wl_x[i].append(float(coords_u[i][1]))
        line1.set_data(wl_x[0], wl_y[0])
        line2.set_data(wl_x[1], wl_y[1])
        line3.set_data(wl_x[2], wl_y[2])

        im_p.set_array(np.angle(core.psi))

        target = max(1e-3, np.percentile(V, 99))
        vmax_v = 0.9 * vmax_v + 0.1 * target
        im_em.set_clim(0, vmax_v)
        im_em.set_array(V)
        dVy2, dVx2 = np.gradient(V)
        gradmag = np.hypot(dVx2, dVy2)
        im_grad.set_clim(0, max(1e-6, np.percentile(gradmag, 99)))
        im_grad.set_array(gradmag)

        txt.set_text(f't={k:04d}')
        return [im_d, scat, line1, line2, line3, im_p, im_em, im_grad, txt]

    out_dir = Path(__file__).resolve().parent.parent.parent / 'media'
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_mp4 = out_dir / f'collision_em_3body_multipanel_AL_{ts}.mp4'

    ani = animation.FuncAnimation(fig, update, frames=frames, interval=1, blit=False)
    if animation.writers.is_available('ffmpeg'):
        writer = animation.FFMpegWriter(fps=15, bitrate=2000)
        ani.save(out_mp4, writer=writer)
        print('Saved', out_mp4)
    else:
        out_gif = out_dir / f'collision_em_3body_multipanel_AL_{ts}.gif'
        ani.save(out_gif, writer=animation.PillowWriter(fps=12))
        print('Saved', out_gif)


if __name__ == '__main__':
    main()


