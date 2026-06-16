#!/usr/bin/env python3
"""Kibble foam statistics for the Z7 vacuum choice and biased-collapse test.

Simulates the configuration left behind by the Z7 ordering crossover:
  1. A correlated random phase field theta(x) (two smoothed Gaussian fields,
     theta = atan2) on a 3D lattice, digitized to vacuum labels
     k = floor(7 theta / 2pi): equiprobable, correlated over xi ~ smoothing.
  2. Foam statistics: wall area fraction, signed winding inventory of walls
     (Delta k = 1..6 -- including the PSC-forbidden/dark types {1,5}),
     per-label percolation (scipy.ndimage.label).
  3. 7-state Potts relaxation (checkerboard Metropolis), unbiased vs biased
     (uniform pressure h on k != 0), at T = 0 and at finite T (beta = 1):
     T = 0 single-spin dynamics demonstrates lattice locking (flat walls
     pinned -- the discrete analog of the P50 beta ~ 1.7 arrest); at finite T
     the bias drives wall collapse, as in the continuum where walls
     accelerate freely under any volume pressure.

Expected output: wall inventory dominated by |Delta k| = 1 (smooth field ->
adjacent-vacuum walls); correlated domains DO percolate (correlated
percolation, unlike naive p = 1/7 site percolation); finite-T biased
relaxation reaches the favored vacuum while unbiased coarsening stalls.
"""
import json
import signal
import sys
import time

import numpy as np

TIMEOUT_SECONDS = 600
t_start = time.time()

def _timeout(signum, frame):
    print(f"TIMEOUT {TIMEOUT_SECONDS}s reached")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

rng = np.random.default_rng(7)
L = 48
XI = 3.0   # smoothing scale in lattice units

results = {"L": L, "xi": XI}

def smooth_field():
    g = rng.standard_normal((L, L, L))
    kx = np.fft.fftfreq(L)[:, None, None]
    ky = np.fft.fftfreq(L)[None, :, None]
    kz = np.fft.fftfreq(L)[None, None, :]
    filt = np.exp(-0.5 * (2 * np.pi * XI) ** 2 * (kx ** 2 + ky ** 2 + kz ** 2))
    return np.real(np.fft.ifftn(np.fft.fftn(g) * filt))

g1, g2 = smooth_field(), smooth_field()
theta = np.arctan2(g2, g1) + np.pi          # [0, 2pi)
labels = np.floor(7.0 * theta / (2.0 * np.pi)).astype(np.int64) % 7

print("=== 1. Foam statistics at formation ===")
counts = np.bincount(labels.ravel(), minlength=7) / labels.size
print(f"  label populations: {np.round(counts, 3)} (target 1/7 = 0.143)")
results["populations"] = counts.tolist()

inv = np.zeros(7, dtype=np.int64)
wall_pairs = 0
total_pairs = 0
for ax in range(3):
    nb = np.roll(labels, -1, axis=ax)
    d = (nb - labels) % 7
    wall_pairs += int(np.count_nonzero(d))
    total_pairs += d.size
    inv += np.bincount(d.ravel(), minlength=7)
frac = wall_pairs / total_pairs
inv_frac = inv[1:] / inv[1:].sum()
print(f"  wall (unequal-neighbor) pair fraction: {frac:.4f}")
print(f"  winding inventory Delta k = 1..6: {np.round(inv_frac, 3)}")
print(f"  dark-type (Delta k in {{1,5}}) share of wall area: "
      f"{inv_frac[0] + inv_frac[4]:.3f}")
results["wall_pair_fraction"] = frac
results["winding_inventory_1to6"] = inv_frac.tolist()

try:
    from scipy import ndimage
    perc = {}
    structure = np.zeros((3, 3, 3), dtype=bool)
    structure[1, 1, :] = structure[1, :, 1] = structure[:, 1, 1] = True
    for k in range(7):
        lab, n = ndimage.label(labels == k, structure=structure)
        # percolation: any cluster touching opposite x faces
        front = set(np.unique(lab[0])) - {0}
        back = set(np.unique(lab[-1])) - {0}
        perc[k] = bool(front & back)
    print(f"  per-label percolation (x-direction): {perc} "
          f"(p = 1/7 < p_c ~ 0.31 -> none expected)")
    results["percolation"] = {str(k): v for k, v in perc.items()}
except ImportError:
    print("  scipy not available: percolation sub-test NOT RUN (explicit skip)")
    results["percolation"] = "scipy unavailable - not run"

# --- 3. zero-temperature relaxation, unbiased vs biased -----------------------
print("\n=== 2. Potts relaxation: unbiased vs biased (h on k != 0) ===")

def neighbor_count_equal(lab, cand):
    s = np.zeros(lab.shape)
    for ax in range(3):
        for sh in (1, -1):
            s += (np.roll(lab, sh, axis=ax) == cand)
    return s

def relax(labels0, h, sweeps, beta):
    lab = labels0.copy()
    iz, iy, ix = np.indices(lab.shape)
    parity = (ix + iy + iz) % 2
    hist = []
    for s in range(sweeps):
        for par in (0, 1):
            cand = rng.integers(0, 7, size=lab.shape)
            e_cur = -neighbor_count_equal(lab, lab) + h * (lab != 0)
            e_new = -neighbor_count_equal(lab, cand) + h * (cand != 0)
            dE = e_new - e_cur
            if beta is None:                       # T = 0 greedy
                acc_prob = (dE <= 0).astype(float)
            else:
                acc_prob = np.minimum(1.0, np.exp(-beta * np.maximum(dE, 0.0)))
                acc_prob = np.where(dE <= 0, 1.0, acc_prob)
            acc = (rng.random(lab.shape) < acc_prob) & (parity == par)
            lab = np.where(acc, cand, lab)
        if s % 10 == 0 or s == sweeps - 1:
            wp = sum(int(np.count_nonzero((np.roll(lab, -1, axis=ax) != lab)))
                     for ax in range(3)) / (3 * lab.size)
            f0 = float(np.mean(lab == 0))
            hist.append((s, wp, f0))
        if time.time() - t_start > TIMEOUT_SECONDS - 60:
            print("  [relax] near wall-clock limit; stopping early")
            break
    return lab, hist

sweeps = 60
_, h_T0_unb = relax(labels, h=0.0, sweeps=sweeps, beta=None)
_, h_T0_bia = relax(labels, h=0.5, sweeps=sweeps, beta=None)
_, h_fT_unb = relax(labels, h=0.0, sweeps=sweeps, beta=1.0)
_, h_fT_bia = relax(labels, h=0.5, sweeps=sweeps, beta=1.0)
print("  sweep | T=0 unb | T=0 h=.5 | beta=1 unb | beta=1 h=.5 | f(k=0) beta=1 h=.5")
d0u, d0b = {s: w for s, w, _ in h_T0_unb}, {s: w for s, w, _ in h_T0_bia}
dfu, dfb = {s: w for s, w, _ in h_fT_unb}, {s: (w, f) for s, w, f in h_fT_bia}
for s in sorted(d0u):
    print(f"  {s:5d} | {d0u[s]:.4f}  | {d0b[s]:.4f}   | {dfu[s]:.4f}     | "
          f"{dfb[s][0]:.4f}      | {dfb[s][1]:.3f}")
results["relaxation"] = {"T0_unbiased": h_T0_unb, "T0_biased": h_T0_bia,
                         "beta1_unbiased": h_fT_unb, "beta1_biased": h_fT_bia}
print("  -> T = 0 single-spin dynamics is lattice-pinned for BOTH cases (the")
print("     discrete locking artifact, cf. P50 beta ~ 1.7 arrest); at finite T")
print("     the bias drives the favored-vacuum fraction up and walls down, while")
print("     the unbiased network only coarsens. Continuum walls are never")
print("     lattice-pinned: they accelerate under any volume pressure.")

import os
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
          "z7_domain_wall_kibble_foam_results.json"), "w") as fp:
    json.dump(results, fp, indent=1)
print("\nSaved z7_domain_wall_kibble_foam_results.json")
signal.alarm(0)
