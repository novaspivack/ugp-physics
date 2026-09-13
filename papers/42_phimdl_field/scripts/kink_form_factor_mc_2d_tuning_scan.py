#!/usr/bin/env python3
"""2D tuning attempt at hbar = 1 (pre-registered in the 088-R15 protocol):
can ANY bare am0 give the physical meson mass a*mu = 0.8492 on the 1+1D
substrate-regulated lattice? Scan am0 over a wide range and measure a*mu.

Expected from the dissolution control: in 2D the cosine is irrelevant
(beta^2 = 49 > 8 pi); pinning may only reappear at very large bare am0.
This scan documents whether the 1+1D theory can host the physical meson
at the tape spacing at all.
"""
import json
import math
import signal
import sys

import numpy as np

TIMEOUT_SECONDS = 900


def _timeout(signum, frame):
    print(f"TIMEOUT {TIMEOUT_SECONDS}s reached")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

rng = np.random.default_rng(20260613)
TWO_PI_7 = 2.0 * math.pi / 7.0
NX, NT = 64, 64
MU_TARGET = math.acosh(1.0 + 0.875 ** 2 / 2.0)


def run_vac(am0, n_sweep, n_meas, step):
    phi = np.zeros((NX, NT))
    xx, tt = np.meshgrid(np.arange(NX), np.arange(NT), indexing="ij")
    masks = [((xx + tt) % 2) == p for p in (0, 1)]
    phibar = []
    for sweep in range(n_sweep):
        for par in (0, 1):
            nb = (np.roll(phi, -1, 0) + np.roll(phi, 1, 0)
                  + np.roll(phi, -1, 1) + np.roll(phi, 1, 1))
            prop = phi + step * rng.standard_normal(phi.shape)
            if sweep % 7 == 3:
                hop = TWO_PI_7 * rng.integers(-1, 2, size=phi.shape)
                prop = phi + hop * (rng.random(phi.shape) < 0.1) + \
                    step * rng.standard_normal(phi.shape)
            dS = (0.5 * (4 * prop ** 2 - 2 * prop * nb)
                  - 0.5 * (4 * phi ** 2 - 2 * phi * nb)
                  + (am0 ** 2 / 49.0) * (np.cos(7 * phi) - np.cos(7 * prop)))
            acc = (rng.random(phi.shape) < np.exp(-np.clip(dS, -50, 50))) & masks[par]
            phi = np.where(acc, prop, phi)
        if sweep >= n_sweep - n_meas and sweep % 10 == 0:
            phibar.append(np.mean(phi, axis=0).copy())
    arr = np.array(phibar)
    arr -= arr.mean()
    c = np.zeros(NT // 2 + 1)
    for dt in range(NT // 2 + 1):
        c[dt] = float(np.mean(arr * np.roll(arr, -dt, axis=1)))
    ms = []
    for t in (1, 2, 3):
        if c[t] > 0 and c[t + 1] > 0 and c[t - 1] > 0:
            r = (c[t - 1] + c[t + 1]) / (2.0 * c[t])
            if r > 1:
                ms.append(math.acosh(r))
    return float(np.mean(ms)) if ms else float("nan")


results = {"mu_target": MU_TARGET, "scan": {}}
print(f"=== 2D tuning scan at hbar = 1 (target a*mu = {MU_TARGET:.4f}) ===")
for am0 in (0.875, 2.0, 4.0, 8.0, 16.0, 32.0):
    step = min(0.9, 3.0 / max(am0, 1.0))
    mu = run_vac(am0, 5000, 3000, step)
    results["scan"][f"am0_{am0}"] = mu
    print(f"  am0 = {am0:6.3f}: a*mu = {mu:.4f}")

out = "/Users/nova/ugp-physics/papers/42_phimdl_field/scripts/kink_form_factor_mc_2d_tuning_scan_results.json"
with open(out, "w") as f:
    json.dump(results, f, indent=1)
print(f"Saved {out.split('/')[-1]}")
signal.alarm(0)
