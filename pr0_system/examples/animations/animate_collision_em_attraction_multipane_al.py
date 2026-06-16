"""
 EM attraction (+/-) multi-pane animation using AL core with radial solitons.
Shows 2D motion with smoothed V_em scaling and peak markers.
Outputs MP4 to the session visualizations folder.
"""

import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from datetime import datetime
import argparse
import csv


def top2_coords(psi: np.ndarray):
    dens = np.abs(psi) ** 2
    idx = np.argsort(dens.ravel())[::-1][:2]
    Ly, Lx = dens.shape
    coords = [divmod(int(i), Lx) for i in idx]
    return coords, dens


def main():
    from pr0_system.evolution.ablowitz_ladik import PR0_Final
    from pr0_system.forces import em

    parser = argparse.ArgumentParser(description='EM attraction multipane animation')
    parser.add_argument('--L', type=int, default=64)
    parser.add_argument('--dt', type=float, default=0.01)
    parser.add_argument('--frames', type=int, default=600)
    parser.add_argument('--sep', type=int, default=10)
    parser.add_argument('--vy', type=float, default=0.20, help='Tangential speed magnitude (± vy) for orbital tendency')
    parser.add_argument('--vx', type=float, default=0.00, help='Small initial ±vx to create off-angle approach')
    parser.add_argument('--accel_scale', type=float, default=12.0, help='Scale for acceleration from -∇V coupling')
    parser.add_argument('--momentum_gain', type=float, default=4.0, help='Gain for local phase-tilt momentum imprint from integrated velocity')
    parser.add_argument('--direct_boost', type=float, default=3.0, help='Direct k·x boost scale using instantaneous -∇V')
    args = parser.parse_args()

    Lx = Ly = args.L
    dt = args.dt
    frames = args.frames

    core = PR0_Final(L_x=Lx, L_y=Ly, g=0.0, gamma_base=0.0)
    # Opposite charges (+/-), moderate inward initial velocities for capture/orbit demos
    # Set tangential velocities (vy) to impart angular momentum for orbit
    core.set_soliton(x0=Lx//2 - args.sep, y0=Ly//2, amplitude=3.0, width=3.0, velocity_x=+args.vx, velocity_y=+args.vy, sign=+1)
    core.set_soliton(x0=Lx//2 + args.sep, y0=Ly//2, amplitude=3.0, width=3.0, velocity_x=-args.vx, velocity_y=-args.vy, sign=-1)

    em_layer = em.BootstrapEM_Final(L_x=Lx, L_y=Ly)
    em_layer.set_peak_charges([+1, -1])

    fig, axes = plt.subplots(2, 2, figsize=(10, 7))
    ax_d, ax_p, ax_em, ax_info = axes.flatten()
    for ax in axes.flatten():
        ax.set_aspect('equal')
        ax.axis('off')

    coords, dens0 = top2_coords(core.psi)
    vmax_d = max(1.0, np.percentile(dens0, 99))
    im_d = ax_d.imshow(dens0, cmap='magma', origin='lower', vmin=0, vmax=vmax_d)
    scat = ax_d.scatter([c[1] for c in coords], [c[0] for c in coords], s=30, c='cyan')
    ax_d.set_title('|psi|^2 + peaks')
    # Worldline overlays
    line1, = ax_d.plot([], [], color='cyan', linewidth=1.0, alpha=0.9)
    line2, = ax_d.plot([], [], color='yellow', linewidth=1.0, alpha=0.9)

    phase0 = np.angle(core.psi)
    im_p = ax_p.imshow(phase0, cmap='twilight', origin='lower', vmin=-np.pi, vmax=np.pi)
    ax_p.set_title('arg(psi)')

    em_layer.psi = core.psi.copy()
    V0 = em_layer._compute_potential_field()
    vmax_v = max(1e-3, np.percentile(V0, 99))
    im_em = ax_em.imshow(V0, cmap='viridis', origin='lower', vmin=0, vmax=vmax_v)
    ax_em.set_title('V_em')
    # Fourth panel: gradient magnitude |∇V_em|
    dVy0, dVx0 = np.gradient(V0)
    gradmag0 = np.hypot(dVx0, dVy0)
    im_grad = ax_info.imshow(gradmag0, cmap='magma', origin='lower', vmin=0, vmax=max(1e-6, np.percentile(gradmag0, 99)))
    ax_info.set_title('|∇V_em|')

    txt = fig.text(0.5, 0.02, '', ha='center', va='bottom', fontsize=10)
    fig.suptitle(f'EM Attraction | L={Lx} dt={dt} frames={frames} sep={args.sep} vy=±{args.vy} vx=±{args.vx}', fontsize=11)

    # Field-driven motion state
    coords_init, _ = top2_coords(core.psi)
    peak_vel = [np.array([0.0, 0.0], dtype=float), np.array([0.0, 0.0], dtype=float)]  # (vy, vx)
    accel_scale = float(args.accel_scale)
    momentum_gain = float(args.momentum_gain)
    direct_boost = float(args.direct_boost)
    # Identity tracking and worldlines
    prev_coords = coords_init[:]
    wl_y1, wl_x1 = [float(prev_coords[0][0])], [float(prev_coords[0][1])]
    wl_y2, wl_x2 = [float(prev_coords[1][0])], [float(prev_coords[1][1])]

    def torus_sep(a, b):
        y1, x1 = a; y2, x2 = b
        dx, dy = x2 - x1, y2 - y1
        if abs(dx) > Lx // 2:
            dx -= int(np.sign(dx)) * Lx
        if abs(dy) > Ly // 2:
            dy -= int(np.sign(dy)) * Ly
        return float(np.sqrt(dx * dx + dy * dy))

    def match_peaks(prev, curr):
        a0 = prev[0]; a1 = prev[1]
        b0 = curr[0]; b1 = curr[1]
        d00 = torus_sep(a0, b0); d01 = torus_sep(a0, b1)
        d10 = torus_sep(a1, b0); d11 = torus_sep(a1, b1)
        if d00 + d11 <= d01 + d10:
            return [b0, b1]
        else:
            return [b1, b0]

    # CSV logging
    out_csv = Path(__file__).resolve().parent.parent.parent / 'media' / 'em_attraction_orbit_log.csv'
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    csv_file = out_csv.open('w', newline='')
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(['t','y1','x1','y2','x2','sep'])

    def update(k):
        # Compute EM field from current psi
        em_layer.psi = core.psi.copy()
        V = em_layer._compute_potential_field()
        # Compute force from −∇V at peak centers and imprint momentum locally
        dVy, dVx = np.gradient(V)
        coords_now, _dens_now = top2_coords(core.psi)
        # Stable identity assignment
        matched = match_peaks(prev_coords, coords_now)
        prev_coords[:] = matched
        (y1c, x1c), (y2c, x2c) = matched[0], matched[1]
        LyLoc, LxLoc = core.psi.shape
        yy, xx = np.meshgrid(np.arange(LyLoc), np.arange(LxLoc), indexing='ij')
        for i, (y, x) in enumerate(coords_now):
            yi, xi = int(y), int(x)
            y0, y1 = max(0, yi-1), min(LyLoc, yi+2)
            x0, x1 = max(0, xi-1), min(LxLoc, xi+2)
            gy = float(np.mean(dVy[y0:y1, x0:x1]))
            gx = float(np.mean(dVx[y0:y1, x0:x1]))
            ay, ax = -gy, -gx
            peak_vel[i][0] += accel_scale * ay * dt
            peak_vel[i][1] += accel_scale * ax * dt
            dx = xx - x; dy = yy - y
            if np.abs(dx).mean() > 0:
                dx = np.where(np.abs(dx) > LxLoc // 2, dx - np.sign(dx) * LxLoc, dx)
            if np.abs(dy).mean() > 0:
                dy = np.where(np.abs(dy) > LyLoc // 2, dy - np.sign(dy) * LyLoc, dy)
            r2 = dx * dx + dy * dy
            mask = np.exp(-r2 / (2.0 * 2.25))  # sigma≈1.5
            phase_tilt = momentum_gain * (peak_vel[i][1] * dx + peak_vel[i][0] * dy) * dt * mask
            core.psi *= np.exp(1j * phase_tilt)
            direct_phase = direct_boost * ((-gx) * dx + (-gy) * dy) * dt * mask
            core.psi *= np.exp(1j * direct_phase)
        # Evolve core and apply conservative EM potential
        core.step(dt=dt)
        core.psi *= np.exp(-1j * (2.0 * V * dt))

        coords, dens = top2_coords(core.psi)
        vmax_d = max(1.0, np.percentile(dens, 99))
        im_d.set_clim(0, vmax_d)
        im_d.set_array(dens)
        scat.set_offsets(np.array([[x1c, y1c], [x2c, y2c]]))
        # Update worldlines
        wl_y1.append(float(y1c)); wl_x1.append(float(x1c))
        wl_y2.append(float(y2c)); wl_x2.append(float(x2c))
        line1.set_data(wl_x1, wl_y1)
        line2.set_data(wl_x2, wl_y2)

        im_p.set_array(np.angle(core.psi))

        # Smooth EM scaling per frame
        nonlocal vmax_v
        target = max(1e-3, np.percentile(V, 99))
        vmax_v = 0.9 * vmax_v + 0.1 * target
        im_em.set_clim(0, vmax_v)
        im_em.set_array(V)
        # Update gradient panel
        dVy, dVx = np.gradient(V)
        gradmag = np.hypot(dVx, dVy)
        im_grad.set_clim(0, max(1e-6, np.percentile(gradmag, 99)))
        im_grad.set_array(gradmag)

        sep = torus_sep((y1c, x1c), (y2c, x2c))
        csv_writer.writerow([k, f"{y1c:.4f}", f"{x1c:.4f}", f"{y2c:.4f}", f"{x2c:.4f}", f"{sep:.6f}"])
        vmag = (np.linalg.norm(peak_vel[0]) + np.linalg.norm(peak_vel[1])) * 0.5
        txt.set_text(f't={k:04d}  sep={sep:5.1f}  |v|≈{vmag:4.2f}')
        return [im_d, scat, line1, line2, im_p, im_em, im_grad, txt]

    out_dir = Path(__file__).resolve().parent.parent.parent / 'media'
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_mp4 = out_dir / f'em_attraction_solitons_{ts}.mp4'

    ani = animation.FuncAnimation(fig, update, frames=frames, interval=1, blit=False)
    if animation.writers.is_available('ffmpeg'):
        writer = animation.FFMpegWriter(fps=15, bitrate=2000)
        ani.save(out_mp4, writer=writer)
        csv_file.close()
        print('Saved', out_mp4)
    else:
        out_gif = out_dir / 'em_attraction_solitons.gif'
        ani.save(out_gif, writer=animation.PillowWriter(fps=12))
        csv_file.close()
        print('Saved', out_gif)


if __name__ == '__main__':
    main()


