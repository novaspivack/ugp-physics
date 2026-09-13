#!/usr/bin/env python3
"""Convert the NPZ replay artifacts (format v1.0) into browser-friendly files.

For each run this writes into replay/ (relative to this script):
  <name>.meta.json  — grid metadata (nx, nt, x0, dx, t0, dt, physical constants)
  <name>.field.f32  — Phi(t,x) row-major float32, little-endian

The app does NOT need this script to run: the pre-exported replay/*.meta.json
and replay/*.field.f32 files already ship alongside it. This script is only
needed to regenerate those files from a fresh raw NPZ simulation run (e.g.
after re-running the many-kink-gas producer scripts elsewhere). The raw NPZ
files are not part of this app, so their location is not assumed by default.

Usage:
  python3 export_replay_json.py [--source-dir DIR]

If --source-dir is omitted, this script looks next to itself first (for a
self-contained regeneration setup); if the NPZ files are not found there, it
reports exactly what is missing rather than silently skipping.
"""

import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "replay")

RUNS = {
    "pure": ("z7_kink_gas_run.npz", True),
    "perturbed": ("z7_perturbed_gas_run.npz", False),
}


def export(name, npz_file, pure, source_dir):
    path = os.path.join(source_dir, npz_file)
    if not os.path.exists(path):
        print(f"skip {name}: {path} not found. Pass --source-dir pointing at the "
              f"directory containing {npz_file} (the raw NPZ producer-script output).")
        return False
    d = np.load(path)
    x = np.asarray(d["x"], dtype=np.float64)
    t = np.asarray(d["t"], dtype=np.float64)
    field = np.asarray(d["field"], dtype=np.float32)
    nt, nx = field.shape
    assert nx == len(x) and nt == len(t), "field shape mismatch with grids"
    dx = float(x[1] - x[0])
    dt = float(t[1] - t[0])
    # verify uniform grids before storing them as (start, step)
    assert np.allclose(np.diff(x), dx, atol=1e-4), "non-uniform x grid"
    assert np.allclose(np.diff(t), dt, atol=1e-4), "non-uniform t grid"

    meta = {
        "name": name,
        "pure": pure,
        "model": str(d["model"]),
        "nx": int(nx),
        "nt": int(nt),
        "x0": float(x[0]),
        "dx": dx,
        "t0": float(t[0]),
        "dt": dt,
        "m_phi_MeV": float(d["m_phi_MeV"]),
        "M_kink_MeV": float(d["M_kink_MeV"]),
        "length_unit_fm": float(d["length_unit_fm"]),
    }
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, f"{name}.meta.json"), "w") as f:
        json.dump(meta, f, indent=1)
    field.astype("<f4").tofile(os.path.join(OUT, f"{name}.field.f32"))
    mb = os.path.getsize(os.path.join(OUT, f"{name}.field.f32")) / 1e6
    print(f"wrote replay/{name}.meta.json + replay/{name}.field.f32 ({mb:.1f} MB)")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", default=HERE,
                         help="directory containing the raw *_run.npz files "
                              "(default: next to this script)")
    args = parser.parse_args()
    ok = [export(n, f, p, args.source_dir) for n, (f, p) in RUNS.items()]
    sys.exit(0 if any(ok) else 1)
