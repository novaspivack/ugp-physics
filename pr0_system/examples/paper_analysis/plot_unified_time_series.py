"""
Plot unified time series CSV produced by run_unified_all_forces_log.py
"""

import csv
from pathlib import Path
import matplotlib.pyplot as plt


def main():
    csv_dir = Path(__file__).resolve().parent
    csv_path = csv_dir / 'unified_timeseries.csv'
    png_dir = Path(__file__).resolve().parent.parent.parent / 'media'
    png_path = png_dir / 'unified_all_forces_timeseries.png'

    t, sep, maxd = [], [], []
    with csv_path.open() as f:
        r = csv.DictReader(f)
        for row in r:
            t.append(int(float(row['t'])))
            sep.append(float(row['sep']))
            maxd.append(float(row['max_dens']))

    fig, ax1 = plt.subplots(figsize=(8, 4))
    ax1.plot(t, sep, label='Separation', color='tab:blue')
    ax1.set_xlabel('t')
    ax1.set_ylabel('Separation', color='tab:blue')
    ax2 = ax1.twinx()
    ax2.plot(t, maxd, label='Max |psi|^2', color='tab:red', alpha=0.7)
    ax2.set_ylabel('Max |psi|^2', color='tab:red')
    fig.tight_layout()
    fig.savefig(png_path, dpi=150)
    print('Saved', png_path)


if __name__ == '__main__':
    main()


