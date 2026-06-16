#!/usr/bin/env python3
"""Parameterized 4D wall runner for the kink form-factor precision campaign.

Extends kink_form_factor_wall_profile_4d_final.py (read in full; Metropolis
core, twisted BC, hop-free one-kink projection, FFT recentering reused
verbatim) with:
  - vacuum mode with per-block correlators -> jackknifed meson mass
  - 16 jackknife blocks, measurements every 5 sweeps
  - two-stage sech fit (coarse 0.02-cell grid refined to 0.002 cells)
  - capillary accumulators on kink configs: per-column circular-CM wall
    position h(x,y,t), 3D FFT power spectrum P(k) averaged over configs,
    per-config Var(h) (for the capillary-decomposition estimator)

Usage:
  python3 kink_form_factor_precision_runner.py LABEL MODE AM0 L NZ AM NSWEEP NMEAS [SEED]
    MODE in {vac, vach, kink, freevac}
      vac     - vacuum, single-well (no hop proposals; cold start well 0):
                the mu-defining ensemble (meson mass in the selected vacuum)
      vach    - vacuum with Z7 well-hop proposals (systematic comparison)
      freevac - free field (quadratic potential (am^2/2) phi^2): full-chain
                validation, exact a*mu = arccosh(1 + (am)^2/2)
      kink    - one-kink sector (twisted BC, hop-free)

Writes papers/42_phimdl_field/scripts/kink_form_factor_precision_run_LABEL.json
Expected: acc_rate ~ 0.5-0.7; kink profiles sech with resid <= 0.025.
"""
import json
import math
import signal
import sys

import numpy as np

TIMEOUT_SECONDS = 5400


def _timeout(signum, frame):
    print(f"TIMEOUT {TIMEOUT_SECONDS}s reached")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

TWO_PI_7 = 2.0 * math.pi / 7.0
N_BLOCKS = 16
MEAS_EVERY = 5
STEP = 0.55


def make_masks(shape):
    idx = np.indices(shape).sum(axis=0)
    return [(idx % 2) == p for p in (0, 1)]


def sech_fit_pass(prof, ws, dzs, z1_0):
    nz = len(prof)
    z = np.arange(nz, dtype=float)
    best = None
    for w in ws:
        for dz in dzs:
            z1 = z1_0 + dz
            d = (z - z1 + nz / 2.0) % nz - nz / 2.0
            f = 1.0 / np.cosh(np.clip(d / w, -50, 50))
            M = np.vstack([f, np.ones_like(f)]).T
            coef, _, _, _ = np.linalg.lstsq(M, prof, rcond=None)
            r = float(np.sqrt(np.mean((M @ coef - prof) ** 2)))
            if best is None or r < best[2]:
                best = (float(w), float(z1), r, float(coef[0]), float(coef[1]))
    return best


def sech_profile_fit(prof, wmax=8.0):
    z1_0 = float(np.argmax(prof))
    w, z1, r, N, C = sech_fit_pass(prof, np.linspace(0.15, wmax, 400),
                                   np.linspace(-1.0, 1.0, 21), z1_0)
    # refinement pass: 0.002-cell w grid, 0.01-cell z1 grid around optimum
    w, z1, r, N, C = sech_fit_pass(
        prof, np.linspace(max(w - 0.06, 0.05), w + 0.06, 61),
        np.linspace(z1 - z1_0 - 0.06, z1 - z1_0 + 0.06, 13), z1_0)
    return {"w_cells": w, "z1": z1, "rms_resid_over_N": r / max(abs(N), 1e-12),
            "N": N, "C": C}


def recenter_fft(arr, shift):
    """Translate arr by +shift cells (f(z) -> f(z - shift)).

    Sign convention verified by delta test: a peak at z0 moves to z0+shift.
    The earlier exp(+ik*shift) kernel moved the peak to z0-shift, so the
    per-measurement 'recentering' DOUBLED wall drift instead of removing it
    (defect inherited from the parent-session estimator; root cause of the
    run-length- and box-size-dependent profile smearing).
    """
    n = len(arr)
    k = np.fft.fftfreq(n) * 2.0 * math.pi
    return np.fft.ifft(np.fft.fft(arr) * np.exp(-1j * k * shift)).real


def wall_z0(gbar):
    """Two-pass windowed circular CM: full-box CM is jitter-dominated by
    noise at long lever arms; second pass restricts to +/-8 cells around
    the smoothed peak."""
    nz = len(gbar)
    sm = (np.roll(gbar, 1) + gbar + np.roll(gbar, -1)) / 3.0
    zpk = int(np.argmax(sm))
    d = (np.arange(nz) - zpk + nz / 2.0) % nz - nz / 2.0
    win = np.abs(d) <= 8.0
    wgt = np.clip(gbar, 0, None) * win
    ang = 2.0 * math.pi * np.arange(nz) / nz
    zx = float((wgt * np.cos(ang)).sum())
    zy = float((wgt * np.sin(ang)).sum())
    return (math.atan2(zy, zx) % (2.0 * math.pi)) * nz / (2.0 * math.pi)


def circular_cm(wgt, axis=-1):
    """Circular center of mass along axis; wgt >= 0."""
    nz = wgt.shape[axis]
    ang = 2.0 * math.pi * np.arange(nz) / nz
    shp = [1] * wgt.ndim
    shp[axis] = nz
    ang = ang.reshape(shp)
    zx = (wgt * np.cos(ang)).sum(axis=axis)
    zy = (wgt * np.sin(ang)).sum(axis=axis)
    return (np.arctan2(zy, zx) % (2.0 * math.pi)) * nz / (2.0 * math.pi)


def run(mode, am0, L, NZ, am, n_sweep, n_meas, seed):
    rng = np.random.default_rng(seed)
    shape = (L, L, L, NZ)
    twist = TWO_PI_7 if mode == "kink" else 0.0
    phi = np.zeros(shape)
    if mode == "kink":
        zz = (np.arange(NZ) - NZ / 2.0)
        prof = (4.0 / 7.0) * np.arctan(np.exp(zz * am))
        phi += prof[None, None, None, :]
    masks = make_masks(shape)
    hops = (mode == "vach")

    def nb_sum(p):
        s = np.zeros_like(p)
        for ax in range(3):
            s += np.roll(p, -1, axis=ax) + np.roll(p, 1, axis=ax)
        up = np.roll(p, -1, axis=3).copy()
        up[..., -1] += twist
        dn = np.roll(p, 1, axis=3).copy()
        dn[..., 0] -= twist
        return s + up + dn

    if mode == "freevac":
        def pot(p):
            return 0.5 * am ** 2 * p ** 2
    else:
        def pot(p):
            return (am0 ** 2 / 49.0) * (1.0 - np.cos(7.0 * p))

    acc = tries = 0
    prof_blocks = [np.zeros(NZ) for _ in range(N_BLOCKS)]
    nb_counts = [0] * N_BLOCKS
    corr_blocks = [np.zeros(NZ // 2 + 1) for _ in range(N_BLOCKS)]
    h_var_blocks = [0.0] * N_BLOCKS
    pk_blocks = None
    pk_counts = [0] * N_BLOCKS
    z0_blocks = [[] for _ in range(N_BLOCKS)]
    r2_blocks = [[] for _ in range(N_BLOCKS)]
    patch = 4 if L % 4 == 0 else 2
    phi2_list, negfrac_list = [], []
    meas_done = 0
    n_meas_pts = max(n_meas // MEAS_EVERY, 1)
    for sweep in range(n_sweep):
        for par in (0, 1):
            nb = nb_sum(phi)
            prop = phi + STEP * rng.standard_normal(shape)
            if hops and sweep % 7 == 3:
                hop = TWO_PI_7 * rng.integers(-1, 2, size=shape)
                prop = phi + hop * (rng.random(shape) < 0.1) + \
                    STEP * rng.standard_normal(shape)
            dS = (0.5 * (8.0 * prop ** 2 - 2.0 * prop * nb)
                  - 0.5 * (8.0 * phi ** 2 - 2.0 * phi * nb)
                  + pot(prop) - pot(phi))
            accept = (rng.random(shape) <
                      np.exp(-np.clip(dS, -50, 50))) & masks[par]
            phi = np.where(accept, prop, phi)
            acc += int(accept.sum())
            tries += int(masks[par].sum())
        if sweep < n_sweep - n_meas:
            continue
        if (sweep - (n_sweep - n_meas)) % MEAS_EVERY:
            continue
        blk = min((meas_done * N_BLOCKS) // n_meas_pts, N_BLOCKS - 1)
        phi2_list.append(float(np.mean(phi ** 2)))
        if mode != "kink":
            pb = np.mean(phi, axis=(0, 1, 2))
            pb = pb - pb.mean()
            for dz in range(NZ // 2 + 1):
                corr_blocks[blk][dz] += float(np.mean(pb * np.roll(pb, -dz)))
            nb_counts[blk] += 1
        else:
            gz = np.diff(np.concatenate([phi, phi[..., :1] + twist], axis=3),
                         axis=3)
            gbar = np.mean(gz, axis=(0, 1, 2))
            sm = (np.roll(gbar, 1) + gbar + np.roll(gbar, -1)) / 3.0
            neg = float(np.abs(np.clip(sm, None, 0)).sum())
            tot = float(np.abs(sm).sum())
            if tot > 0:
                negfrac_list.append(neg / tot)
            z0 = wall_z0(gbar)
            rec = recenter_fft(gbar, NZ / 2.0 - z0)
            prof_blocks[blk] += rec
            nb_counts[blk] += 1
            z0_blocks[blk].append(z0)
            # windowed second moment (+/-12 cells) of the recentered profile
            dd = (np.arange(NZ) - NZ / 2.0)
            wmask = np.abs(dd) <= 12.0
            wpos = np.clip(rec, 0, None) * wmask
            tot = float(wpos.sum())
            if tot > 0:
                r2_blocks[blk].append(float((wpos * dd ** 2).sum()) / tot)
            # capillary accumulators: patch-coarse-grained wall position
            gp = gz.reshape(L // patch, patch, L // patch, patch,
                            L // patch, patch, NZ).mean(axis=(1, 3, 5))
            h = circular_cm(np.clip(gp, 0, None), axis=-1)
            h = (h - z0 + NZ / 2.0) % NZ - NZ / 2.0
            h = h - h.mean()
            h_var_blocks[blk] += float(np.mean(h ** 2))
            ph = np.abs(np.fft.fftn(h)) ** 2 / h.size
            if pk_blocks is None:
                pk_blocks = [np.zeros_like(ph) for _ in range(N_BLOCKS)]
            pk_blocks[blk] += ph
            pk_counts[blk] += 1
        meas_done += 1
    out = {"mode": mode, "am0": am0, "L": L, "NZ": NZ, "am": am,
           "n_sweep": n_sweep, "n_meas": n_meas, "seed": seed,
           "acc_rate": acc / max(tries, 1),
           "phi2": float(np.mean(phi2_list)), "n_meas_done": meas_done}
    if mode != "kink":
        out["corr_blocks"] = [(c / max(n, 1)).tolist()
                              for c, n in zip(corr_blocks, nb_counts)]
        out["nb_counts"] = nb_counts
    else:
        out["prof_blocks"] = [(b / max(c, 1)).tolist()
                              for b, c in zip(prof_blocks, nb_counts)]
        out["nb_counts"] = nb_counts
        out["negfrac_mean"] = float(np.mean(negfrac_list))
        out["h_var_blocks"] = [v / max(c, 1)
                               for v, c in zip(h_var_blocks, nb_counts)]
        pk_b = [pb / max(c, 1) for pb, c in zip(pk_blocks, pk_counts)]
        out["pk_mean"] = (sum(pk_b) / N_BLOCKS).tolist()
        # quarters of the measurement window for equilibration diagnostics
        out["pk_quarters"] = [
            (sum(pk_b[i * 4:(i + 1) * 4]) / 4.0).tolist() for i in range(4)]
        out["patch"] = patch
        out["z0_block_mean"] = [float(np.mean(z)) if z else 0.0
                                for z in z0_blocks]
        out["z0_block_var"] = [float(np.var(z)) if z else 0.0
                               for z in z0_blocks]
        out["r2_block_mean"] = [float(np.mean(r)) if r else 0.0
                                for r in r2_blocks]
    return out


if __name__ == "__main__":
    label, mode = sys.argv[1], sys.argv[2]
    am0, L, NZ = float(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
    am = float(sys.argv[6])
    n_sweep, n_meas = int(sys.argv[7]), int(sys.argv[8])
    seed = int(sys.argv[9]) if len(sys.argv) > 9 else 20260613
    import time
    t0 = time.time()
    res = run(mode, am0, L, NZ, am, n_sweep, n_meas, seed)
    res["wall_seconds"] = time.time() - t0
    out = ("/Users/nova/ugp-physics/papers/42_phimdl_field/scripts/"
           f"kink_form_factor_precision_run_{label}.json")
    with open(out, "w") as f:
        json.dump(res, f)
    print(f"{label}: mode={mode} am0={am0} L={L} acc={res['acc_rate']:.3f} "
          f"phi2={res['phi2']:.4f} t={res['wall_seconds']:.0f}s")
    signal.alarm(0)
