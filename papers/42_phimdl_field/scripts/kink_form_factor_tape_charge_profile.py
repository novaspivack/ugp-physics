#!/usr/bin/env python3
"""Level-2 CMCA tape measurement of the kink Z3 charge profile (Route T).

Uses the canonical P45/P41 implementations directly (no re-implementation):
ether tile, Rule 110 step, f_MDL orbit table, GEN1, canonical glider seeds.

Objects measured:
  (1) the PSC kink beable: GEN1 -> GEN2 -> GEN3 orbit on the Z7^5 ring under
      canonical f_MDL; per-step circularly recentered Z3-coset charge second
      moment, averaged over the 3 non-vacuum orbit states.
  (2) glider complexes on the long binary tape (canonical seeds: C2 single
      flip [P41], 10-cell GLIDER_SEED [P41], GLIDER_CELLS triple [P45]),
      synchronous Rule 110; deviation cluster = op XOR evolved-ether; charge
      density = Z3 coset of w = 2*(dev) mod 7 (every deviating cell has
      w = 2 in {1,2,4} -> color +1); per-step circular recentering; width
      boundedness diagnostic; L in {280, 560, 1120}, T = 560, transient 140.

Charge map (F21 Z3 cosets of Z7*): {1,2,4} -> +1, {3,5,6} -> -1, 0 -> 0.

Output: r_RMS in tape units a, per object and L; boundedness flags.
Cross-level consistency target from Route C (not tuned): r ~ 1.0-1.1 a.
"""
import json
import math
import signal
import sys

import numpy as np

sys.path.insert(0, "/Users/nova/ugp-physics/papers/45_three_tape_cmca/scripts")
sys.path.insert(0, "/Users/nova/ugp-physics/papers/41_three_layer_chiral_minkowski_ca/scripts")

TIMEOUT_SECONDS = 900


def _timeout(signum, frame):
    print(f"TIMEOUT {TIMEOUT_SECONDS}s reached")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

import three_tape_cmca as ttc
import two_layer_chiral_afca_prototype as p41

signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

Z3_COLOR = {0: 0, 1: +1, 2: +1, 4: +1, 3: -1, 5: -1, 6: -1}


def circ_moment(weights):
    """Circular mean position and second moment (in cells) of nonneg weights."""
    n = len(weights)
    w = np.asarray(weights, dtype=float)
    tot = w.sum()
    if tot <= 0:
        return None, None
    ang = 2.0 * math.pi * np.arange(n) / n
    zx = float((w * np.cos(ang)).sum())
    zy = float((w * np.sin(ang)).sum())
    th0 = math.atan2(zy, zx)
    # signed circular distance in cells
    d = (np.arange(n) - th0 * n / (2 * math.pi) + n / 2.0) % n - n / 2.0
    x0 = float((w * d).sum() / tot)
    x2 = float((w * (d - x0) ** 2).sum() / tot)
    return x0, x2


results = {}

# ── (1) PSC kink beable on the Z7^5 ring ─────────────────────────────────────
print("=== (1) PSC kink beable: GEN orbit Z3 charge profile (ring) ===")
orbit = [p41.GEN1]
s = p41.GEN1
for _ in range(2):
    s = p41.fmdl_step5(s)
    orbit.append(s)
ring_rows = []
for state in orbit:
    q = [Z3_COLOR[v] for v in state]
    absq = [abs(c) for c in q]
    _, x2 = circ_moment(absq)
    ring_rows.append({"state": list(state), "charges": q, "x2_cells2": x2})
    print(f"  state {state}: charges {q}; <x^2> = {x2:.4f} cells^2")
x2_ring = float(np.mean([r["x2_cells2"] for r in ring_rows]))
r_ring = math.sqrt(x2_ring)
print(f"  orbit-averaged r_RMS = {r_ring:.4f} a  (ring of 5)")
results["ring_beable"] = {"rows": ring_rows, "x2_mean_cells2": x2_ring,
                          "r_rms_cells": r_ring}

# ── (2) glider complexes on the long tape ────────────────────────────────────
print("\n=== (2) long-tape glider complexes (sync Rule 110, canonical) ===")
T_TOTAL, T_CUT = 560, 140
SEEDS = {}


def seed_c2(eth, L):
    t = eth.copy(); t[L // 2] ^= 1; return t


def seed_p41glider(eth, L):
    t, _ = p41.inject_glider_seed(eth, L)
    return t


def seed_gcells(eth, L):
    t = eth.copy()
    for xp in ttc.GLIDER_CELLS:
        t[(L // 2 + xp - 128) % L] ^= 1
    return t


def seed_gen1(eth, L):
    t = eth.copy()
    for k, v in enumerate(p41.GEN1):
        t[(L // 2 + k) % L] = v % 2
    return t


SEEDS = {"C2_single_flip": seed_c2, "P41_glider_seed": seed_p41glider,
         "P45_glider_cells": seed_gcells, "GEN1_mod2": seed_gen1}

results["tape"] = {}
for L in (280, 560, 1120):
    eth0 = ttc.make_ether(L)
    results["tape"][f"L_{L}"] = {}
    for name, fn in SEEDS.items():
        eth = eth0.copy()
        tape = fn(eth0, L)
        x2_series, width_series = [], []
        for t in range(T_TOTAL):
            eth = ttc._step_rule_vec(eth, ttc._R110_ARR)
            tape = ttc._step_rule_vec(tape, ttc._R110_ARR)
            dev = (tape ^ eth).astype(float)      # every dev cell: w=2, color +1
            if t < T_CUT:
                continue
            x0, x2 = circ_moment(dev)
            if x2 is None:
                continue
            x2_series.append(x2)
            idx = np.where(dev > 0)[0]
            if len(idx):
                # circular extent
                gaps = np.diff(np.sort(idx))
                wrap = L - (idx.max() - idx.min())
                ext = L - max(gaps.max() if len(gaps) else 0, wrap)
                width_series.append(ext)
        x2_arr = np.array(x2_series)
        wid = np.array(width_series, dtype=float)
        # boundedness: linear growth test of width over the window
        tgrid = np.arange(len(wid))
        growth = float(np.polyfit(tgrid, wid, 1)[0]) if len(wid) > 10 else 0.0
        bounded = abs(growth) < 0.02              # cells per step
        r_rms = float(np.sqrt(np.mean(x2_arr))) if len(x2_arr) else float("nan")
        row = {"r_rms_cells": r_rms,
               "x2_mean": float(np.mean(x2_arr)) if len(x2_arr) else None,
               "x2_std": float(np.std(x2_arr)) if len(x2_arr) else None,
               "mean_width_cells": float(np.mean(wid)) if len(wid) else None,
               "width_growth_cells_per_step": growth,
               "bounded": bool(bounded)}
        results["tape"][f"L_{L}"][name] = row
        if row["mean_width_cells"] is None or math.isnan(r_rms):
            print(f"  L={L:5d} {name:18s}: deviation DECAYED to ether "
                  f"(no charge cluster after transient)")
            row["decayed"] = True
        else:
            print(f"  L={L:5d} {name:18s}: r_RMS = {r_rms:7.3f} a; "
                  f"mean width = {row['mean_width_cells']:7.2f}; "
                  f"growth = {growth:+.4f} c/step; "
                  f"{'BOUNDED' if bounded else 'DELOCALIZED'}")

out = "/Users/nova/ugp-physics/papers/42_phimdl_field/scripts/kink_form_factor_tape_charge_profile_results.json"
with open(out, "w") as f:
    json.dump(results, f, indent=1)
print(f"\nSaved {out.split('/')[-1]}")
signal.alarm(0)
