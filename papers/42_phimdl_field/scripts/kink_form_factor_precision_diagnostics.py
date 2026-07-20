#!/usr/bin/env python3
"""Diagnostics on the first precision-campaign ensemble.

1. Corrected meson-mass estimator: fit C(dz) = A cosh(mu (dz - NZ/2)) + B
   (the constant B absorbs both the per-config zero-mode subtraction offset
   and any well-wandering contamination), jackknifed over blocks; validated
   first on synthetic cosh+constant+noise data.
2. Block-resolved (MC-time-resolved) sech widths from the stored
   prof_blocks of every kink run: equilibration trend test.

Expected: synthetic mu recovered unbiased to <0.5%; block trends reveal
which (L, run-length) combinations are equilibrated.
"""
import json
import math
import signal
import sys

import numpy as np

TIMEOUT_SECONDS = 600


def _timeout(signum, frame):
    print(f"TIMEOUT {TIMEOUT_SECONDS}s reached")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

SB = "/Users/nova/ugp-physics/papers/42_phimdl_field/scripts"
rng = np.random.default_rng(20260615)


def load(label):
    with open(f"{SB}/kink_form_factor_precision_run_{label}.json") as f:
        return json.load(f)


def cosh_const_fit(c, dz_min=1, dz_max=12):
    """Fit C(dz) = A cosh(mu (dz - NZ/2)) + B on dz in [dz_min, dz_max].
    Linear in (A, B) at fixed mu; 1D golden search over mu."""
    nz2 = len(c) - 1          # c has NZ/2+1 entries
    NZ = 2 * nz2
    dz = np.arange(dz_min, min(dz_max, nz2) + 1)
    y = np.array([c[d] for d in dz])

    def resid(mu):
        f = np.cosh(mu * (dz - NZ / 2.0))
        X = np.vstack([f, np.ones_like(f)]).T
        coef, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
        r = y - X @ coef
        return float(r @ r), coef

    lo, hi = 0.05, 3.0
    g = (math.sqrt(5) - 1) / 2
    a, b = lo, hi
    c1, c2 = b - g * (b - a), a + g * (b - a)
    f1, f2 = resid(c1)[0], resid(c2)[0]
    for _ in range(200):
        if f1 < f2:
            b, c2, f2 = c2, c1, f1
            c1 = b - g * (b - a)
            f1 = resid(c1)[0]
        else:
            a, c1, f1 = c1, c2, f2
            c2 = a + g * (b - a)
            f2 = resid(c2)[0]
    mu = (a + b) / 2
    return mu, resid(mu)[1]


def jackknife_mu_fit(corr_blocks, **kw):
    cb = np.array(corr_blocks)
    nb = len(cb)
    full, _ = cosh_const_fit(cb.mean(axis=0), **kw)
    jks = np.array([cosh_const_fit(np.delete(cb, j, axis=0).mean(axis=0),
                                   **kw)[0] for j in range(nb)])
    err = math.sqrt(max(nb - 1, 1) * float(np.var(jks)))
    return full, err


def sech_fit_pass(prof, ws, dzs, z1_0):
    nz = len(prof)
    z = np.arange(nz, dtype=float)
    best = None
    for w in ws:
        for dzv in dzs:
            z1 = z1_0 + dzv
            d = (z - z1 + nz / 2.0) % nz - nz / 2.0
            f = 1.0 / np.cosh(np.clip(d / w, -50, 50))
            M = np.vstack([f, np.ones_like(f)]).T
            coef, _, _, _ = np.linalg.lstsq(M, prof, rcond=None)
            r = float(np.sqrt(np.mean((M @ coef - prof) ** 2)))
            if best is None or r < best[2]:
                best = (float(w), float(z1), r, float(coef[0]), float(coef[1]))
    return best


def quick_w(prof):
    z1_0 = float(np.argmax(prof))
    w, z1, r, N, C = sech_fit_pass(prof, np.linspace(0.15, 8.0, 200),
                                   np.linspace(-1.0, 1.0, 11), z1_0)
    w, z1, r, N, C = sech_fit_pass(prof,
                                   np.linspace(max(w - 0.1, 0.05), w + 0.1, 41),
                                   [z1 - z1_0], z1_0)
    return w


results = {}
print("=== synthetic validation of the cosh+const mu fit ===")
NZ = 32
mu_true, A_true, B_true = 0.85, 0.05, 0.013
ok = True
for noise in (0.0, 1e-4, 5e-4):
    vals = []
    for trial in range(200):
        dz = np.arange(NZ // 2 + 1)
        c = A_true * np.cosh(mu_true * (dz - NZ / 2.0)) + B_true \
            + noise * rng.standard_normal(NZ // 2 + 1)
        mu, _ = cosh_const_fit(c)
        vals.append(mu)
    bias = float(np.mean(vals)) - mu_true
    print(f"  noise {noise:.0e}: mu = {np.mean(vals):.5f} +/- "
          f"{np.std(vals):.5f} (bias {bias:+.5f})")
    ok = ok and abs(bias) < 0.005
print(f"  synthetic gate: {'PASS' if ok else 'FAIL'}")
results["synthetic_gate"] = ok
assert ok, "synthetic mu fit gate failed"

print("\n=== corrected meson masses (cosh+const fit) ===")
for lbl in ("vac_460_L10", "vac_509_L10", "vac_560_L10", "vac_509_L14",
            "vac_272_L20z48"):
    d = load(lbl)
    mu, err = jackknife_mu_fit(d["corr_blocks"])
    mu2, err2 = jackknife_mu_fit(d["corr_blocks"], dz_min=2, dz_max=12)
    print(f"  {lbl}: a*mu = {mu:.4f} +/- {err:.4f} "
          f"(window dz>=2: {mu2:.4f} +/- {err2:.4f})")
    results[lbl] = {"mu": mu, "err": err, "mu_w2": mu2, "err_w2": err2}

print("\n=== MC-time-resolved sech widths (equilibration trends) ===")
for lbl in ("k509_L8_s1", "k509_L10_s1", "k509_L10_s2", "k509_L12_s1",
            "k509_L14_s1", "k509_L14_s2", "k509_L16_s1", "k509_L16_s2",
            "k509_L20_s1", "k460_L14_s1", "k560_L14_s1", "k272_L20z48"):
    d = load(lbl)
    pb = np.array(d["prof_blocks"])
    # quarters of the measurement window (4 blocks each)
    qs = [quick_w(pb[i * 4:(i + 1) * 4].mean(axis=0)) for i in range(4)]
    print(f"  {lbl} (L={d['L']}): w by quarter = "
          + "  ".join(f"{q:.3f}" for q in qs))
    results[f"trend_{lbl}"] = qs

out = f"{SB}/kink_form_factor_precision_diagnostics_results.json"
with open(out, "w") as f:
    json.dump(results, f, indent=1)
print(f"\nSaved {out.split('/')[-1]}")
signal.alarm(0)
