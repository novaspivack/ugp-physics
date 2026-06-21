"""
 Parameter sweep for high-energy EM attraction (off-angle) to map capture/orbit regions.
Outputs a CSV with metrics per run.
"""

import argparse
import csv
from pathlib import Path
from itertools import product
import subprocess
import sys
import numpy as np


def parse_list(s: str, cast=float):
    return [cast(x.strip()) for x in s.split(',') if x.strip()]


def top2_coords(psi: np.ndarray):
    dens = np.abs(psi) ** 2
    idx = np.argsort(dens.ravel())[::-1][:2]
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


def match_peaks(prev, curr, Lx, Ly):
    a0 = prev[0]; a1 = prev[1]
    b0 = curr[0]; b1 = curr[1]
    d00 = torus_sep(a0, b0, Lx, Ly); d01 = torus_sep(a0, b1, Lx, Ly)
    d10 = torus_sep(a1, b0, Lx, Ly); d11 = torus_sep(a1, b1, Lx, Ly)
    if d00 + d11 <= d01 + d10:
        return [b0, b1]
    else:
        return [b1, b0]


def simulate_one(L, dt, frames, sep, vy, vx, accel_scale, momentum_gain, direct_boost):
    from pr0_system.evolution.ablowitz_ladik import PR0_Final
    from pr0_system.forces import em

    Lx = Ly = L
    core = PR0_Final(L_x=Lx, L_y=Ly, g=0.0, gamma_base=0.0)
    # Off-angle initial velocities, opposite charges for attraction
    core.set_soliton(x0=Lx//2 - sep, y0=Ly//2, amplitude=3.0, width=3.0, velocity_x=+vx, velocity_y=+vy, sign=+1)
    core.set_soliton(x0=Lx//2 + sep, y0=Ly//2, amplitude=3.0, width=3.0, velocity_x=-vx, velocity_y=-vy, sign=-1)

    em_layer = em.BootstrapEM_Final(L_x=Lx, L_y=Ly)
    em_layer.set_peak_charges([+1, -1])

    coords_prev, _ = top2_coords(core.psi)
    # Relative angle tracking (peak1 to peak2)
    angle_series = []
    sep_series = []
    energy_series = []

    # Precompute mesh
    yy, xx = np.meshgrid(np.arange(Ly), np.arange(Lx), indexing='ij')
    peak_vel = [np.array([0.0, 0.0], dtype=float), np.array([0.0, 0.0], dtype=float)]

    for _k in range(frames):
        # EM potential
        em_layer.psi = core.psi.copy()
        V = em_layer._compute_potential_field()
        dVy, dVx = np.gradient(V)
        coords_now, dens_now = top2_coords(core.psi)
        matched = match_peaks(coords_prev, coords_now, Lx, Ly)
        coords_prev[:] = matched
        (y1c, x1c), (y2c, x2c) = matched[0], matched[1]

        # Acceleration and local momentum imprint
        for i, (y, x) in enumerate(matched):
            yi, xi = int(y), int(x)
            y0, y1 = max(0, yi-1), min(Ly, yi+2)
            x0, x1 = max(0, xi-1), min(Lx, xi+2)
            gy = float(np.mean(dVy[y0:y1, x0:x1]))
            gx = float(np.mean(dVx[y0:y1, x0:x1]))
            ay, ax = -gy, -gx
            peak_vel[i][0] += accel_scale * ay * dt
            peak_vel[i][1] += accel_scale * ax * dt
            dx = xx - x; dy = yy - y
            if np.abs(dx).mean() > 0:
                dx = np.where(np.abs(dx) > Lx // 2, dx - np.sign(dx) * Lx, dx)
            if np.abs(dy).mean() > 0:
                dy = np.where(np.abs(dy) > Ly // 2, dy - np.sign(dy) * Ly, dy)
            r2 = dx * dx + dy * dy
            mask = np.exp(-r2 / (2.0 * 2.25))
            phase_tilt = momentum_gain * (peak_vel[i][1] * dx + peak_vel[i][0] * dy) * dt * mask
            core.psi *= np.exp(1j * phase_tilt)
            direct_phase = direct_boost * ((-gx) * dx + (-gy) * dy) * dt * mask
            core.psi *= np.exp(1j * direct_phase)

        # Evolve + conservative EM phase
        core.step(dt=dt)
        core.psi *= np.exp(-1j * (2.0 * V * dt))

        # Metrics
        # Relative angle (peak2 - peak1)
        dy_rel = (y2c - y1c)
        dx_rel = (x2c - x1c)
        # Wrap for torus minimal vector
        if abs(dx_rel) > Lx // 2:
            dx_rel -= int(np.sign(dx_rel)) * Lx
        if abs(dy_rel) > Ly // 2:
            dy_rel -= int(np.sign(dy_rel)) * Ly
        ang = np.arctan2(dy_rel, dx_rel)
        angle_series.append(ang)
        sep_val = torus_sep((y1c, x1c), (y2c, x2c), Lx, Ly)
        sep_series.append(sep_val)

        # Simple energy proxy: gradient energy + EM potential energy
        gy_dens, gx_dens = np.gradient(dens_now)
        K = float(np.mean(gx_dens**2 + gy_dens**2))
        U = float(np.mean(V))
        energy_series.append(K + U)

    # Post-process metrics
    angles = np.unwrap(np.array(angle_series))
    revolutions = float((angles[-1] - angles[0]) / (2.0 * np.pi)) if len(angles) > 1 else 0.0
    min_sep = float(np.min(sep_series)) if sep_series else 0.0
    max_sep = float(np.max(sep_series)) if sep_series else 0.0
    bound_fraction = float(np.mean(np.array(sep_series) < (0.75 * (2 * sep)))) if sep_series else 0.0
    e0 = energy_series[0] if energy_series else 0.0
    eN = energy_series[-1] if energy_series else 0.0
    energy_drift = float((eN - e0) / (abs(e0) + 1e-9))

    # Classification
    if revolutions >= 0.9 and bound_fraction > 0.6:
        outcome = 'orbit'
    elif bound_fraction > 0.7 and min_sep < 0.6 * (2 * sep):
        outcome = 'capture'
    elif max_sep > 0.8 * Lx:
        outcome = 'escape'
    else:
        outcome = 'scatter'

    return {
        'vy': vy, 'vx': vx, 'accel_scale': accel_scale, 'momentum_gain': momentum_gain, 'direct_boost': direct_boost,
        'sep': sep, 'dt': dt, 'frames': frames,
        'revolutions': revolutions, 'min_sep': min_sep, 'max_sep': max_sep, 'bound_fraction': bound_fraction,
        'energy_drift': energy_drift, 'outcome': outcome
    }


def main():
    p = argparse.ArgumentParser(description='Sweep EM attraction parameters for orbit/capture mapping')
    p.add_argument('--L', type=int, default=96)
    p.add_argument('--dt', type=float, default=0.008)
    p.add_argument('--frames', type=int, default=1400)
    p.add_argument('--sep', type=int, default=12)
    p.add_argument('--vy_list', type=str, default='0.8,1.0,1.2')
    p.add_argument('--vx_list', type=str, default='0.2,0.3')
    p.add_argument('--accel_list', type=str, default='20,22,24')
    p.add_argument('--mg_list', type=str, default='8,10,12')
    p.add_argument('--db_list', type=str, default='8,10,12')
    p.add_argument('--limit', type=int, default=24, help='Max combinations to run (for quick tests)')
    p.add_argument('--render_top', type=int, default=0, help='Render top-N most interesting runs (by orbit/revolutions)')
    p.add_argument('--render_script', type=str, default='animate_collision_em_attraction_multipane_al.py')
    p.add_argument('--out_csv', type=str, default=str(Path(__file__).resolve().parent.parent.parent / 'media' / 'em_high_energy_sweep.csv'))
    args = p.parse_args()

    vy_list = parse_list(args.vy_list)
    vx_list = parse_list(args.vx_list)
    accel_list = parse_list(args.accel_list)
    mg_list = parse_list(args.mg_list)
    db_list = parse_list(args.db_list)

    combos = list(product(vy_list, vx_list, accel_list, mg_list, db_list))
    if args.limit and len(combos) > args.limit:
        combos = combos[: args.limit]

    outp = Path(args.out_csv)
    outp.parent.mkdir(parents=True, exist_ok=True)
    results = []
    with outp.open('w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['vy','vx','accel_scale','momentum_gain','direct_boost','sep','dt','frames','revolutions','min_sep','max_sep','bound_fraction','energy_drift','outcome'])
        for vy, vx, a, mg, db in combos:
            res = simulate_one(args.L, args.dt, args.frames, args.sep, vy, vx, a, mg, db)
            results.append(res)
            w.writerow([
                res['vy'], res['vx'], res['accel_scale'], res['momentum_gain'], res['direct_boost'],
                res['sep'], res['dt'], res['frames'], res['revolutions'], res['min_sep'], res['max_sep'],
                res['bound_fraction'], res['energy_drift'], res['outcome']
            ])
    print('Saved sweep results to', outp)

    # Optional rendering of top-N runs
    if args.render_top and results:
        # Prefer 'orbit', then 'capture', sorted by revolutions desc and bound_fraction desc
        def key_fn(r):
            return (r['outcome'] == 'orbit', r['outcome'] == 'capture', r['revolutions'], r['bound_fraction'])
        ranked = sorted(results, key=key_fn, reverse=True)
        top = ranked[: args.render_top]
        script_path = Path(__file__).parent / args.render_script
        for r in top:
            cmd = [
                sys.executable,
                str(script_path),
                '--L', str(args.L),
                '--dt', str(args.dt),
                '--frames', str(args.frames),
                '--sep', str(args.sep),
                '--vy', str(r['vy']),
                '--vx', str(r['vx']),
                '--accel_scale', str(r['accel_scale']),
                '--momentum_gain', str(r['momentum_gain']),
                '--direct_boost', str(r['direct_boost'])
            ]
            print('Rendering:', ' '.join(cmd))
            subprocess.run(cmd, check=True)


if __name__ == '__main__':
    main()


