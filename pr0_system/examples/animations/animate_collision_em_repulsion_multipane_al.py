"""
Improved multi-pane EM repulsion (+/+) using AL core (PR0_Final) to show clear 2D motion.
- origin='lower' for imshow
- dynamic vmax via percentile
- peak markers overlaid

documentation of scattering sweeps, parameters, and annotated renders used with this tool.
"""

import numpy as np
import os
import csv
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import argparse


def top2_coords(psi: np.ndarray):
    dens = np.abs(psi) ** 2
    idx = np.argsort(dens.ravel())[::-1][:2]
    Ly, Lx = dens.shape
    coords = [divmod(int(i), Lx) for i in idx]
    return coords, dens

def main():
    # Use AL core directly for clearer drift behavior
    from pr0_system.evolution.ablowitz_ladik import PR0_Final
    from pr0_system.forces import em

    parser = argparse.ArgumentParser(description='EM repulsion multipane animation')
    parser.add_argument('--L', type=int, default=64)
    parser.add_argument('--dt', type=float, default=0.01)
    parser.add_argument('--frames', type=int, default=600)
    parser.add_argument('--vx', type=float, default=10.0, help='Initial speed magnitude along x for each peak (opposite signs)')
    parser.add_argument('--vy', type=float, default=0.0, help='Initial speed magnitude along y for slight off-angle setup (opposite signs)')
    parser.add_argument('--sep', type=int, default=14, help='Half-separation along x')
    parser.add_argument('--b', type=int, default=0, help='Impact parameter in pixels (vertical offset between peaks)')
    parser.add_argument('--accel_scale', type=float, default=12.0, help='Scale for acceleration from -∇V coupling')
    parser.add_argument('--momentum_gain', type=float, default=4.0, help='Gain for local phase-tilt momentum imprint from integrated velocity')
    parser.add_argument('--direct_boost', type=float, default=3.0, help='Direct k·x boost scale using instantaneous -∇V')
    parser.add_argument('--warmup_steps', type=int, default=200, help='Disable EM coupling and local boosts for initial steps to allow approach')
    parser.add_argument('--em_scale', type=float, default=1.0, help='Scale factor for EM phase rotation strength')
    parser.add_argument('--em_on_radius', type=float, default=12.0, help='Proximity radius (pixels) where EM ramps on')
    parser.add_argument('--em_ramp_width', type=float, default=4.0, help='Width of logistic ramp for EM activation')
    parser.add_argument('--scatter_window', type=int, default=60, help='Frames in early/late windows to estimate scattering angles')
    parser.add_argument('--scatter_csv', type=str, default='scattering_log.csv', help='CSV to append scattering results')
    parser.add_argument('--force_aim', action='store_true', help='Aim initial velocities of peaks toward each other for approach')
    parser.add_argument('--no_render', action='store_true', help='Run headless: simulate and write CSV without saving animation')
    parser.add_argument('--annotate_scattering', action='store_true', help='Overlay incoming/outgoing velocity arrows and scattering angles on the density pane (final frame)')
    parser.add_argument('--charges', type=str, default='repel', choices=['repel','attract'], help='repel: [+1,+1], attract: [+1,-1]')
    parser.add_argument('--seed', type=int, default=0, help='Seed for any initialization jitter')
    parser.add_argument('--init_jitter', type=float, default=0.25, help='Position jitter amplitude in pixels for initial peaks')
    parser.add_argument('--show_trails', action='store_true', help='Draw worldline trails on density panel')
    parser.add_argument('--mark_closest', action='store_true', help='Mark closest-approach locations on final frame')
    parser.add_argument('--preserve_norm', action='store_true', help='Renormalize psi after EM overlay to preserve ||psi||^2 (may break energy conservation)')
    parser.add_argument('--hamiltonian_flow', action='store_true', help='Use self-consistent Hamiltonian iteration for EM overlay (slower but conserves energy)')
    parser.add_argument('--ham_iters', type=int, default=3, help='Self-consistent iterations for Hamiltonian flow')
    args = parser.parse_args()

    Lx = Ly = args.L
    dt = args.dt
    frames = args.frames

    core = PR0_Final(L_x=Lx, L_y=Ly, g=0.0, gamma_base=0.0)
    # RNG for reproducibility and jitter
    rng = np.random.default_rng(int(args.seed))
    # Prime with initial velocity for visible interaction
    y_top = int(Ly//2 + (args.b // 2))
    y_bot = int(Ly//2 - (args.b - args.b // 2))
    x_left = Lx//2 - args.sep
    x_right = Lx//2 + args.sep
    # Apply small jitter
    j = float(args.init_jitter)
    x_left_j = (x_left + rng.uniform(-j, j)) % Lx
    x_right_j = (x_right + rng.uniform(-j, j)) % Lx
    y_bot_j = (y_bot + rng.uniform(-j, j)) % Ly
    y_top_j = (y_top + rng.uniform(-j, j)) % Ly
    if args.force_aim:
        # Aim initial velocities toward the other peak for approach
        dy = float(y_top_j - y_bot_j)
        # Handle toroidal shortest dx between peaks
        dx_raw = float(x_right_j - x_left_j)
        dx = dx_raw - np.round(dx_raw / Lx) * Lx
        norm = float(np.hypot(dx, dy)) + 1e-12
        ux, uy = dx / norm, dy / norm
        speed = float(abs(args.vx))
        # Left peak moves toward right; right peak toward left
        core.set_soliton(x0=int(x_left_j), y0=int(y_bot_j), amplitude=3.0, width=3.0, velocity_x=+speed * ux, velocity_y=+speed * uy, sign=+1)
        core.set_soliton(x0=int(x_right_j), y0=int(y_top_j), amplitude=3.0, width=3.0, velocity_x=-speed * ux, velocity_y=-speed * uy, sign=+1)
    else:
        core.set_soliton(x0=int(x_left_j), y0=int(y_bot_j), amplitude=3.0, width=3.0, velocity_x=+args.vx, velocity_y=+args.vy, sign=+1)
        core.set_soliton(x0=int(x_right_j), y0=int(y_top_j), amplitude=3.0, width=3.0, velocity_x=-args.vx, velocity_y=-args.vy, sign=+1)

    em_layer = em.BootstrapEM_Final(L_x=Lx, L_y=Ly)
    if args.charges == 'repel':
        em_layer.set_peak_charges([+1, +1])
    else:
        em_layer.set_peak_charges([+1, -1])

    fig, axes = plt.subplots(2, 2, figsize=(10, 7))
    ax_d, ax_p, ax_em, ax_grad = axes.flatten()
    for ax in axes.flatten():
        ax.set_aspect('equal')
        ax.axis('off')

    coords, dens0 = top2_coords(core.psi)
    vmax_d = max(1.0, np.percentile(dens0, 99))
    im_d = ax_d.imshow(dens0, cmap='magma', origin='lower', vmin=0, vmax=vmax_d)
    scat = ax_d.scatter([c[1] for c in coords], [c[0] for c in coords], s=30, c='cyan')
    ax_d.set_title('|psi|^2 + peaks')
    # Optional trails
    trail0, trail1 = None, None
    if args.show_trails:
        trail0, = ax_d.plot([], [], color='cyan', linewidth=1.0, alpha=0.7)
        trail1, = ax_d.plot([], [], color='yellow', linewidth=1.0, alpha=0.7)

    phase0 = np.angle(core.psi)
    im_p = ax_p.imshow(phase0, cmap='twilight', origin='lower', vmin=-np.pi, vmax=np.pi)
    ax_p.set_title('arg(psi)')

    em_layer.psi = core.psi.copy()
    V0 = em_layer._compute_potential_field()
    vmax_v = max(1e-3, np.percentile(V0, 99))
    im_em = ax_em.imshow(V0, cmap='viridis', origin='lower', vmin=0, vmax=vmax_v)
    ax_em.set_title('V_em')
    # Gradient magnitude panel
    dVy0, dVx0 = np.gradient(V0)
    gradmag0 = np.hypot(dVx0, dVy0)
    im_grad = ax_grad.imshow(gradmag0, cmap='magma', origin='lower', vmin=0, vmax=max(1e-6, np.percentile(gradmag0, 99)))
    ax_grad.set_title('|∇V_em|')

    # Parameter banner
    txt = fig.text(0.5, 0.02, '', ha='center', va='bottom', fontsize=10)
    fig.suptitle(f'EM Repulsion | L={Lx} dt={dt} frames={frames} vx={args.vx} vy={args.vy} sep={args.sep} b={args.b}', fontsize=11)

    # Field-driven motion state (two peaks)
    coords_init, _ = top2_coords(core.psi)
    peak_vel = [np.array([0.0, 0.0], dtype=float), np.array([0.0, 0.0], dtype=float)]  # (vy, vx)
    accel_scale = float(args.accel_scale)
    momentum_gain = float(args.momentum_gain)
    direct_boost = float(args.direct_boost)

    def torus_sep(a, b):
        y1, x1 = a; y2, x2 = b
        dx, dy = x2 - x1, y2 - y1
        if abs(dx) > Lx // 2:
            dx -= int(np.sign(dx)) * Lx
        if abs(dy) > Ly // 2:
            dy -= int(np.sign(dy)) * Ly
        return float(np.sqrt(dx * dx + dy * dy))

    worldline = []  # list of [(y1,x1),(y2,x2)] per frame
    sep_history = []

    # Diagnostics logging setup
    ts_run = datetime.now().strftime('%Y%m%d_%H%M%S')
    diag_dir = Path(__file__).resolve().parent.parent.parent / 'media'
    diag_dir.mkdir(parents=True, exist_ok=True)
    diag_path = diag_dir / f'em_repulsion_timeseries_{ts_run}.csv'
    with open(diag_path, 'w', newline='') as fdiag:
        w = csv.writer(fdiag)
        w.writerow(['t','K_proxy','V_em_proxy','E_proxy','H_proxy','sep','L','dt','frames','sep_init','b','vx','vy','charges','force_aim','seed','init_jitter'])

    def _toroidal_delta(d, L):
        if d > L / 2:
            return d - L
        if d < -L / 2:
            return d + L
        return d

    def _avg_velocity(track, idx, LxLoc, LyLoc, start, end):
        # Average velocity vector over [start,end) for particle idx (0 or 1)
        vx_sum = 0.0
        vy_sum = 0.0
        n = 0
        for t in range(start + 1, min(end, len(track))):
            (y_prev, x_prev), (y2_prev, x2_prev) = track[t-1]
            (y_cur, x_cur), (y2_cur, x2_cur) = track[t]
            if idx == 0:
                dx = _toroidal_delta(x_cur - x_prev, LxLoc)
                dy = _toroidal_delta(y_cur - y_prev, LyLoc)
            else:
                dx = _toroidal_delta(x2_cur - x2_prev, LxLoc)
                dy = _toroidal_delta(y2_cur - y2_prev, LyLoc)
            vx_sum += dx
            vy_sum += dy
            n += 1
        if n == 0:
            return 0.0, 0.0
        return vx_sum / n, vy_sum / n

    def _angle_between(v1, v2):
        a = np.array(v1, dtype=float)
        b = np.array(v2, dtype=float)
        na = np.linalg.norm(a) + 1e-12
        nb = np.linalg.norm(b) + 1e-12
        c = float(np.clip(np.dot(a, b) / (na * nb), -1.0, 1.0))
        return float(np.degrees(np.arccos(c)))

    # Identity-stable matching of current top-2 peaks to previous frame ordering
    def _match_peaks(prev_coords, curr_coords, LxLoc, LyLoc):
        if len(prev_coords) < 2 or len(curr_coords) < 2:
            return curr_coords
        (py1, px1), (py2, px2) = prev_coords
        (cy1, cx1), (cy2, cx2) = curr_coords
        # Cost matrix using toroidal distances
        def torus_d(a, b):
            return torus_sep(a, b)
        c11 = torus_d((py1, px1), (cy1, cx1))
        c12 = torus_d((py1, px1), (cy2, cx2))
        c21 = torus_d((py2, px2), (cy1, cx1))
        c22 = torus_d((py2, px2), (cy2, cx2))
        # Two assignments: (1->1,2->2) vs (1->2,2->1)
        if c11 + c22 <= c12 + c21:
            return [(cy1, cx1), (cy2, cx2)]
        else:
            return [(cy2, cx2), (cy1, cx1)]

    # Predictive matching with constant-velocity extrapolation
    def _predictive_match(prev_coords, curr_coords, worldline_hist, LxLoc, LyLoc):
        if len(prev_coords) < 2 or len(curr_coords) < 2 or len(worldline_hist) < 2:
            return _match_peaks(prev_coords, curr_coords, LxLoc, LyLoc)
        # Last two frames
        (p0_y1, p0_x1), (p0_y2, p0_x2) = worldline_hist[-1]
        (p1_y1, p1_x1), (p1_y2, p1_x2) = worldline_hist[-2]
        # Toroidal deltas to get velocities
        def dwrap(d, L):
            if d > L/2: return d - L
            if d < -L/2: return d + L
            return d
        v1x = dwrap(p0_x1 - p1_x1, LxLoc); v1y = dwrap(p0_y1 - p1_y1, LyLoc)
        v2x = dwrap(p0_x2 - p1_x2, LxLoc); v2y = dwrap(p0_y2 - p1_y2, LyLoc)
        # Predict next positions
        pred1 = (p0_y1 + v1y, p0_x1 + v1x)
        pred2 = (p0_y2 + v2y, p0_x2 + v2x)
        # Compute costs to current candidates
        (cy1, cx1), (cy2, cx2) = curr_coords
        def cost(pred, cur):
            py, px = pred; cy, cx = cur
            dx = dwrap(cx - px, LxLoc); dy = dwrap(cy - py, LyLoc)
            return float(np.hypot(dx, dy))
        a_cost = cost(pred1, (cy1, cx1)) + cost(pred2, (cy2, cx2))
        b_cost = cost(pred1, (cy2, cx2)) + cost(pred2, (cy1, cx1))
        if a_cost <= b_cost:
            return [(cy1, cx1), (cy2, cx2)]
        else:
            return [(cy2, cx2), (cy1, cx1)]

    prev_coords = coords_init[:]

    # Hold annotation artists so they persist
    ann_art = []

    def update(k):
        # Compute EM field from current psi
        em_layer.psi = core.psi.copy()
        V = em_layer._compute_potential_field()
        # Compute force from −∇V at peak centers and imprint momentum locally
        dVy, dVx = np.gradient(V)
        coords_now_raw, _dens_now = top2_coords(core.psi)
        LyLoc, LxLoc = core.psi.shape
        # Match to previous ordering for identity-stable tracking
        coords_now = _predictive_match(prev_coords, coords_now_raw, worldline, LxLoc, LyLoc) if len(coords_now_raw) >= 2 else coords_now_raw
        # update previous for next frame
        if len(coords_now) >= 2:
            prev_coords[:] = coords_now
        yy, xx = np.meshgrid(np.arange(LyLoc), np.arange(LxLoc), indexing='ij')
        # Proximity-gated EM activation: off at large separation, smoothly on when close
        sep_gate = 0.0
        if len(coords_now) >= 2:
            (y1, x1), (y2, x2) = coords_now[0], coords_now[1]
            dx = abs(x2 - x1)
            dy = abs(y2 - y1)
            if dx > LxLoc / 2:
                dx = LxLoc - dx
            if dy > LyLoc / 2:
                dy = LyLoc - dy
            sep = float(np.hypot(dx, dy))
            # Logistic ramp: ~0 when sep >> R_on; ~1 when sep << R_on
            k_ramp = 1.0 / max(1e-6, float(args.em_ramp_width))
            x_arg = (args.em_on_radius - sep) * k_ramp
            sep_gate = 1.0 / (1.0 + np.exp(-x_arg))
        # Also honor warmup gating for first steps
        time_gate = 1.0 if k >= args.warmup_steps else 0.0
        gate = sep_gate * time_gate
        # Warmup gating: disable EM-driven boosts initially to allow approach
        eff_accel = accel_scale * gate
        eff_mg = momentum_gain * gate
        eff_db = direct_boost * gate
        for i, (y, x) in enumerate(coords_now):
            yi, xi = int(y), int(x)
            y0, y1 = max(0, yi-1), min(LyLoc, yi+2)
            x0, x1 = max(0, xi-1), min(LxLoc, xi+2)
            gy = float(np.mean(dVy[y0:y1, x0:x1]))
            gx = float(np.mean(dVx[y0:y1, x0:x1]))
            ay, ax = -gy, -gx
            peak_vel[i][0] += eff_accel * ay * dt
            peak_vel[i][1] += eff_accel * ax * dt
            dx = xx - x
            dy = yy - y
            if np.abs(dx).mean() > 0:
                dx = np.where(np.abs(dx) > LxLoc // 2, dx - np.sign(dx) * LxLoc, dx)
            if np.abs(dy).mean() > 0:
                dy = np.where(np.abs(dy) > LyLoc // 2, dy - np.sign(dy) * LyLoc, dy)
            r2 = dx * dx + dy * dy
            mask = np.exp(-r2 / (2.0 * 2.25))
            if eff_mg != 0.0:
                phase_tilt = eff_mg * (peak_vel[i][1] * dx + peak_vel[i][0] * dy) * dt * mask
                core.psi *= np.exp(1j * phase_tilt)
            if eff_db != 0.0:
                direct_phase = eff_db * ((-gx) * dx + (-gy) * dy) * dt * mask
                core.psi *= np.exp(1j * direct_phase)
        # Evolve core and apply conservative EM potential
        # Track top-2 worldline
        if len(coords_now) >= 2:
            worldline.append([(float(coords_now[0][0]), float(coords_now[0][1])),
                              (float(coords_now[1][0]), float(coords_now[1][1]))])
            # Compute separation
            sep_inst = torus_sep(coords_now[0], coords_now[1])
            sep_history.append(sep_inst)

        core.step(dt=dt)
        em_scale_now = args.em_scale * gate
        if em_scale_now > 0.0:
            if args.hamiltonian_flow:
                # Self-consistent Hamiltonian iteration
                psi_work = core.psi.copy()
                for _ in range(args.ham_iters):
                    em_layer.psi = psi_work.copy()
                    V_iter = em_layer._compute_potential_field()
                    dVy, dVx = np.gradient(V_iter)
                    gy, gx = np.gradient(psi_work)
                    # Hamiltonian flow: dpsi/dt = -i(V·psi + ∇V·∇psi_conj-like coupling)
                    # Simplified: psi_new = psi - i·dt·(V·psi)
                    psi_work = core.psi - 1j * (em_scale_now * 2.0 * dt) * V_iter * core.psi
                core.psi = psi_work
            else:
                core.psi *= np.exp(-1j * (em_scale_now * 2.0 * V * dt))
                if args.preserve_norm:
                    norm = float(np.sqrt(np.sum(np.abs(core.psi)**2)))
                    if norm > 1e-12:
                        core.psi /= norm

        # Diagnostics: scale-invariant Hamiltonian H = ∫(|∇ψ|²/|ψ|² + V)·|ψ|² dx
        gy_psi, gx_psi = np.gradient(core.psi)
        grad_sq = np.abs(gx_psi)**2 + np.abs(gy_psi)**2
        dens_now = np.abs(core.psi)**2
        # Avoid division by zero
        dens_safe = np.maximum(dens_now, 1e-12)
        kinetic_density = grad_sq / dens_safe
        H_proxy = float(np.sum((kinetic_density + V) * dens_now))
        # Also track old proxies for comparison
        K_proxy = float(np.sum(grad_sq))
        V_em_proxy = float(np.sum(dens_now * V))
        E_proxy = K_proxy + V_em_proxy
        with open(diag_path, 'a', newline='') as fdiag:
            w = csv.writer(fdiag)
            w.writerow([k, K_proxy, V_em_proxy, E_proxy, H_proxy, sep_history[-1] if sep_history else float('nan'),
                        Lx, dt, frames, args.sep, args.b, args.vx, args.vy, args.charges, int(bool(args.force_aim)), args.seed, args.init_jitter])

        # On final frame, compute scattering metrics and append CSV
        if k + 1 == frames and len(worldline) >= max(4, args.scatter_window * 2):
            Lyy, Lxx = core.psi.shape
            W = min(args.scatter_window, len(worldline) // 3)
            vin0 = _avg_velocity(worldline, 0, Lxx, Lyy, 0, W)
            vout0 = _avg_velocity(worldline, 0, Lxx, Lyy, len(worldline) - W, len(worldline))
            vin1 = _avg_velocity(worldline, 1, Lxx, Lyy, 0, W)
            vout1 = _avg_velocity(worldline, 1, Lxx, Lyy, len(worldline) - W, len(worldline))
            theta0 = _angle_between(vin0, vout0)
            theta1 = _angle_between(vin1, vout1)
            # Compute minimum separation and time of closest approach
            min_sep = 1e9
            t_min = 0
            for t, ((y1, x1), (y2, x2)) in enumerate(worldline):
                dx = abs(x2 - x1)
                dy = abs(y2 - y1)
                if dx > Lxx / 2:
                    dx = Lxx - dx
                if dy > Lyy / 2:
                    dy = Lyy - dy
                sep = float(np.hypot(dx, dy))
                if sep < min_sep:
                    min_sep = sep
                    t_min = t
            # Engagement heuristic: require true close pass inside EM-on radius
            engaged = 1 if (min_sep <= args.em_on_radius) else 0
            if not engaged:
                theta0 = float('nan')
                theta1 = float('nan')
            # Ensure output directory
            out_csv = args.scatter_csv
            os.makedirs(os.path.dirname(out_csv), exist_ok=True)
            write_header = not os.path.exists(out_csv)
            with open(out_csv, mode='a', newline='') as f:
                w = csv.writer(f)
                if write_header:
                    w.writerow([
                        'timestamp','mode','L','dt','frames','sep_init','b','vx','vy',
                        'accel_scale','momentum_gain','direct_boost','warmup_steps',
                        'em_on_radius','em_ramp_width','em_scale','scatter_window',
                        'force_aim','theta0_deg','theta1_deg','min_sep','t_min_sep','engaged'
                    ])
                w.writerow([
                    datetime.now().isoformat(timespec='seconds'),
                    'em_repulsion_proximity_gated', Lxx, dt, frames, args.sep, args.b, args.vx, args.vy,
                    accel_scale, momentum_gain, direct_boost, args.warmup_steps,
                    args.em_on_radius, args.em_ramp_width, args.em_scale, args.scatter_window,
                    int(bool(args.force_aim)),
                    f"{theta0:.3f}", f"{theta1:.3f}", f"{min_sep:.3f}", t_min, engaged
                ])
            # Optional on-frame annotation (final frame)
            if args.annotate_scattering:
                # Draw arrows for avg incoming/outgoing velocities for both peaks
                # Use fixed anchors in data coords at corners for clarity
                scale = 6.0
                # Peak 0 arrows at bottom-left
                base0 = (4.0, 4.0)
                arr0_in = ax_d.arrow(base0[0], base0[1], vin0[0] * 0.0 + vin0[1] * scale, vin0[0] * scale, head_width=1.5, color='cyan', length_includes_head=True)
                arr0_out = ax_d.arrow(base0[0], base0[1], vout0[0] * 0.0 + vout0[1] * scale, vout0[0] * scale, head_width=1.5, color='yellow', length_includes_head=True)
                # Peak 1 arrows at bottom-right
                base1 = (LxLoc - 10.0, 4.0)
                arr1_in = ax_d.arrow(base1[0], base1[1], vin1[0] * 0.0 + vin1[1] * scale, vin1[0] * scale, head_width=1.5, color='cyan', length_includes_head=True)
                arr1_out = ax_d.arrow(base1[0], base1[1], vout1[0] * 0.0 + vout1[1] * scale, vout1[0] * scale, head_width=1.5, color='yellow', length_includes_head=True)
                # Legend text
                t_legend = ax_d.text(0.02, 0.98, f"θ0={theta0:.1f}°  θ1={theta1:.1f}°\nmin_sep={min_sep:.2f}", transform=ax_d.transAxes, va='top', ha='left', color='white', fontsize=9, bbox=dict(facecolor='black', alpha=0.35, pad=3))
                ann_art.extend([arr0_in, arr0_out, arr1_in, arr1_out, t_legend])

            # Closest-approach marker if requested
            if args.mark_closest and len(worldline) > 0:
                # Find min sep index (already computed above)
                t_star = t_min
                (y1s, x1s), (y2s, x2s) = worldline[t_star]
                m1 = ax_d.plot([x1s], [y1s], marker='*', color='red', markersize=8)[0]
                m2 = ax_d.plot([x2s], [y2s], marker='*', color='red', markersize=8)[0]
                ann_art.extend([m1, m2])

            # Console summary
            print(f"Scattering summary → b={args.b}, θ0={theta0:.2f}°, θ1={theta1:.2f}°, min_sep={min_sep:.2f} at t={t_min}, engaged={engaged}")

        coords, dens = top2_coords(core.psi)
        vmax_d = max(1.0, np.percentile(dens, 99))
        im_d.set_clim(0, vmax_d)
        im_d.set_array(dens)
        # Use matched coords for scatter overlay
        coords_scatter = coords_now if len(coords_now) >= 2 else coords
        scat.set_offsets(np.array([[c[1], c[0]] for c in coords_scatter]))
        if args.show_trails and len(worldline) >= 1:
            ys0 = [p[0][0] for p in worldline]; xs0 = [p[0][1] for p in worldline]
            ys1 = [p[1][0] for p in worldline]; xs1 = [p[1][1] for p in worldline]
            def break_wrap(xs, ys, LxLoc, LyLoc):
                bx = []; by = []
                for i in range(len(xs)):
                    if i > 0:
                        dx = abs(xs[i] - xs[i-1])
                        dy = abs(ys[i] - ys[i-1])
                        if dx > LxLoc/2 or dy > LyLoc/2:
                            bx.append(float('nan'))
                            by.append(float('nan'))
                    bx.append(xs[i]); by.append(ys[i])
                return bx, by
            xs0b, ys0b = break_wrap(xs0, ys0, LxLoc, LyLoc)
            xs1b, ys1b = break_wrap(xs1, ys1, LxLoc, LyLoc)
            trail0.set_data(xs0b, ys0b)
            trail1.set_data(xs1b, ys1b)

        im_p.set_array(np.angle(core.psi))

        # Smooth color scaling to avoid flicker/skips but still adapt
        nonlocal vmax_v
        target = max(1e-3, np.percentile(V, 99))
        vmax_v = 0.9 * vmax_v + 0.1 * target
        im_em.set_clim(0, vmax_v)
        im_em.set_array(V)
        # Update grad magnitude
        dVy, dVx = np.gradient(V)
        gradmag = np.hypot(dVx, dVy)
        im_grad.set_clim(0, max(1e-6, np.percentile(gradmag, 99)))
        im_grad.set_array(gradmag)

        sep = torus_sep(coords_scatter[0], coords_scatter[1])
        vmag = (np.linalg.norm(peak_vel[0]) + np.linalg.norm(peak_vel[1])) * 0.5
        txt.set_text(f't={k:04d}  sep={sep:5.1f}  |v|≈{vmag:4.2f}')
        return [im_d, scat, im_p, im_em, txt] + ann_art

    out_dir = Path(__file__).resolve().parent.parent.parent / 'media'
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_mp4 = out_dir / f'em_repulsion_solitons_{ts}.mp4'

    if args.no_render:
        for k in range(frames):
            update(k)
        return
    else:
        ani = animation.FuncAnimation(fig, update, frames=frames, interval=1, blit=False)
        if animation.writers.is_available('ffmpeg'):
            writer = animation.FFMpegWriter(fps=15, bitrate=2000)
            ani.save(out_mp4, writer=writer)
            print('Saved', out_mp4)
        else:
            out_gif = out_dir / 'em_repulsion_solitons.gif'
            ani.save(out_gif, writer=animation.PillowWriter(fps=12))
            print('Saved', out_gif)


if __name__ == '__main__':
    main()


