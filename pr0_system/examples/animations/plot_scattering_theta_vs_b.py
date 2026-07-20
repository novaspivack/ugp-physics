#!/usr/bin/env python3
"""
Quick plotter for scattering deflection vs impact parameter.

Cross-reference:

Reads scattering_log.csv and creates PNG(s) in media/
visualizations folder with timestamps.
"""
import argparse
import os
from datetime import datetime
import csv
from collections import defaultdict
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt


def load_scattering(csv_path: str):
    rows = []
    if not os.path.exists(csv_path):
        return rows
    with open(csv_path, newline='') as f:
        r = csv.DictReader(f)
        for row in r:
            try:
                b = float(row.get('b', 'nan'))
                theta0 = float(row.get('theta0_deg', 'nan'))
                theta1 = float(row.get('theta1_deg', 'nan'))
                mode = row.get('mode', '')
                rows.append({
                    'b': b,
                    'theta0': theta0,
                    'theta1': theta1,
                    'mode': mode,
                    'dt': float(row.get('dt', 'nan')),
                    'vx': float(row.get('vx', 'nan')),
                    'vy': float(row.get('vy', 'nan')),
                    'L': float(row.get('L', 'nan')),
                })
            except Exception:
                continue
    return rows


def plot_theta_vs_b(rows, out_png: str, title_suffix: str = ''):
    if not rows:
        print('No data to plot.')
        return
    # Aggregate by b: median(theta) to smooth noise
    b_to_thetas = defaultdict(list)
    for r in rows:
        if np.isfinite(r['b']) and np.isfinite(r['theta0']) and np.isfinite(r['theta1']):
            # Use average of the two particle deflections
            b_to_thetas[r['b']].append(0.5 * (r['theta0'] + r['theta1']))
    if not b_to_thetas:
        print('No finite b/theta values to plot.')
        return
    b_vals = sorted(b_to_thetas.keys())
    theta_med = [float(np.median(b_to_thetas[b])) for b in b_vals]

    plt.figure(figsize=(6, 4))
    plt.plot(b_vals, theta_med, 'o-', lw=2, ms=5)
    plt.xlabel('Impact parameter b (px)')
    plt.ylabel('Deflection angle θ (deg)')
    plt.title(f'Scattering θ vs b{title_suffix}')
    plt.grid(True, alpha=0.3)
    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    plt.tight_layout()
    plt.savefig(out_png, dpi=150)
    plt.close()
    print(f'Saved plot: {out_png}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv', default='scattering_log.csv')
    parser.add_argument('--out_dir', default=str(Path(__file__).resolve().parent.parent.parent / 'media'))
    parser.add_argument('--title', default='')
    args = parser.parse_args()

    rows = load_scattering(args.csv)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_png = os.path.join(args.out_dir, f'scattering_theta_vs_b_{ts}.png')
    title_suffix = f' {args.title}' if args.title else ''
    plot_theta_vs_b(rows, out_png, title_suffix)


if __name__ == '__main__':
    main()


