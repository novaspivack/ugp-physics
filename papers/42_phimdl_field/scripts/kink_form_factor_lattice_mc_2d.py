#!/usr/bin/env python3
"""Substrate-regulated 1+1D lattice MC of the Z7 cosine kink (Route Q, 2D leg).

Euclidean path integral P ~ exp(-S/hbar), S = sum [ (1/2)(dphi)^2 + a^2 V ],
V = (m0^2/49)(1 - cos 7 phi), on an Nx x Nt lattice at the physical tape
spacing a m0 = 7/8 (tree reading: a = 1/Lambda_GTE, m_phi = m_tau).

The 1+1D continuum theory does not exist at beta^2 = 49 > 8 pi (Coleman),
but the tape never takes a -> 0: the lattice ensemble at fixed a is the
substrate-regulated object. This leg is (i) the machinery validator and
(ii) the dissolution positive control: the cosine is irrelevant in 2D, so
strong kink broadening is REQUIRED here if the estimators are sound (P2).

Benchmarks (must pass before the physical point):
  B1 free field: <phi^2> vs exact lattice sum; cosh effective mass vs input
  B2 classical limit hbar = 0.05, kink sector: profile reproduces the
     deterministic Route C lattice values at the same am

Then: hbar ramp {0.05, 0.2, 0.5, 1.0} at fixed bare am0 = 7/8 (kink + vacuum
sectors); meson pole mass from the vacuum correlator; broadening factor
b = r_RMS * mu_meas / r_class per the frozen 088-R15 map.

Estimators: E-TOP <g(x - x0)> (mean link gradient; noise cancels linearly);
E-BORN <g^2(x - x0)> - <g^2>_vac (connected). x0 per slice from the
half-twist crossing of the slice-smeared field (two smear widths).
Errors: jackknife over configuration blocks.
"""
import json
import math
import signal
import sys

import numpy as np

TIMEOUT_SECONDS = 1500


def _timeout(signum, frame):
    print(f"TIMEOUT {TIMEOUT_SECONDS}s reached")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

rng = np.random.default_rng(20260609)

TWO_PI_7 = 2.0 * math.pi / 7.0
R_CLASS_BORN = math.pi / (2.0 * math.sqrt(3.0))
AM = 7.0 / 8.0
NX, NT = 64, 64


def action_density(phi, am0, twist):
    """Local contributions used by Metropolis (not the full action)."""
    raise NotImplementedError  # site-local updates computed inline


def metropolis_run(am0, hbar, twist, n_sweep, n_meas, step, free_field=False,
                   meas_every=10, seed_kink=False):
    """Checkerboard Metropolis; returns measurement dict."""
    phi = np.zeros((NX, NT))
    if seed_kink and twist != 0.0:
        x = (np.arange(NX) - NX / 2.0) * 1.0
        prof = (4.0 / 7.0) * np.arctan(np.exp(x * AM))   # lattice-units seed
        phi += prof[:, None]
    masks = []
    xx, tt = np.meshgrid(np.arange(NX), np.arange(NT), indexing="ij")
    for par in (0, 1):
        masks.append(((xx + tt) % 2) == par)

    def neighbors_sum_and_twistgrad(p):
        # x-direction with twist: phi(NX) = phi(0) + twist
        up_x = np.roll(p, -1, axis=0).copy()
        up_x[-1, :] += twist
        dn_x = np.roll(p, 1, axis=0).copy()
        dn_x[0, :] -= twist
        up_t = np.roll(p, -1, axis=1)
        dn_t = np.roll(p, 1, axis=1)
        return up_x + dn_x + up_t + dn_t

    def local_pot(p):
        if free_field:
            return 0.5 * (AM if am0 is None else am0) ** 2 * p ** 2
        return (am0 ** 2 / 49.0) * (1.0 - np.cos(7.0 * p))

    acc = 0
    tries = 0
    ac_g = np.zeros(NX)        # autocorrelation of the link gradient g
    ac_u = np.zeros(NX)        # autocorrelation of u = g^2
    n_ac = 0
    phi2_list, phibar_t = [], []
    g2_mean_list = []
    for sweep in range(n_sweep):
        for par in (0, 1):
            nb = neighbors_sum_and_twistgrad(phi)
            prop = phi + step * rng.standard_normal(phi.shape)
            # occasional well hop
            if not free_field and sweep % 7 == 3:
                hop = TWO_PI_7 * rng.integers(-1, 2, size=phi.shape)
                prop = phi + hop * (rng.random(phi.shape) < 0.1) + \
                    step * rng.standard_normal(phi.shape)
            dS = (0.5 * (4.0 * prop ** 2 - 2.0 * prop * nb)
                  - 0.5 * (4.0 * phi ** 2 - 2.0 * phi * nb)
                  + local_pot(prop) - local_pot(phi))
            accept = (rng.random(phi.shape) < np.exp(-np.clip(dS, -50, 50) / hbar)) & masks[par]
            phi = np.where(accept, prop, phi)
            acc += int(accept.sum())
            tries += int(masks[par].sum())
        if sweep < n_sweep - n_meas:
            continue
        if (sweep - (n_sweep - n_meas)) % meas_every:
            continue
        # measurements
        phi2_list.append(float(np.mean(phi ** 2)))
        phibar_t.append(np.mean(phi, axis=0).copy())   # for meson correlator
        gx = np.diff(np.append(phi, phi[:1, :] + twist, axis=0), axis=0)
        g2_mean_list.append(float(np.mean(gx ** 2)))
        # translation-invariant autocorrelations over x, averaged over t slices
        fg = np.fft.fft(gx, axis=0)
        ac_g += np.mean(np.fft.ifft(np.abs(fg) ** 2, axis=0).real, axis=1) / NX
        u = gx ** 2
        fu = np.fft.fft(u, axis=0)
        ac_u += np.mean(np.fft.ifft(np.abs(fu) ** 2, axis=0).real, axis=1) / NX
        n_ac += 1
    out = {"acc_rate": acc / max(tries, 1),
           "phi2": float(np.mean(phi2_list)),
           "phi2_err": float(np.std(phi2_list) / math.sqrt(max(len(phi2_list), 1))),
           "g2_mean": float(np.mean(g2_mean_list)),
           "ac_g": ac_g / max(n_ac, 1), "ac_u": ac_u / max(n_ac, 1),
           "n_ac": n_ac}
    if phibar_t:
        # meson correlator from time-slice means (vacuum sector)
        arr = np.array(phibar_t)              # (n_meas, NT)
        arr -= arr.mean()
        c = np.zeros(NT // 2 + 1)
        for dt in range(NT // 2 + 1):
            c[dt] = float(np.mean(arr * np.roll(arr, -dt, axis=1)))
        out["corr"] = c
    return out


def ac_moment(ac_kink, ac_vac, window=10):
    """<x^2> of the density from connected autocorrelation: moment(A)/2.

    A_conn(d) = AC_kink - AC_vac, far-region baseline removed; the second
    moment over |d| <= window (and 2*window for the stability check) equals
    2<x^2> of the underlying density, translation-invariantly.
    """
    n = len(ac_kink)
    a = ac_kink - ac_vac
    d = np.arange(n)
    d = np.where(d > n // 2, d - n, d).astype(float)
    base = float(np.mean(a[np.abs(d) > n / 4]))
    a = a - base
    vals = []
    for win in (window, 2 * window):
        m = np.abs(d) <= win
        tot = a[m].sum()
        if tot <= 0:
            vals.append(float("nan"))
            continue
        vals.append(float((a[m] * d[m] ** 2).sum() / tot / 2.0))
    return vals[0], vals[1]


def cosh_mass(c):
    """Effective mass from cosh ratio at small t (correlation length ~ 1)."""
    ms = []
    for t in (1, 2, 3):
        if c[t] > 0 and c[t + 1] > 0 and c[t - 1] > 0:
            r = (c[t - 1] + c[t + 1]) / (2.0 * c[t])
            if r > 1:
                ms.append(math.acosh(r))
    return float(np.mean(ms)) if ms else float("nan")


def ac_sech_fit(ac_kink, ac_vac, dmax=16):
    """Fit A_conn(d) to the sech-family autocorrelation N*(d/w)/sinh(d/w) + C.

    The kink gradient autocorrelation for a sech profile of width w is exactly
    proportional to (d/w)/sinh(d/w) (=1 at d=0). w-scan with linear solve for
    (N, C); returns (w, rms_residual_over_N, x2_top, x2_born) where
    x2_top = pi^2 w^2 / 4 and x2_born = pi^2 w^2 / 12 (BA-SHAPE family link).
    """
    n = len(ac_kink)
    a = ac_kink - ac_vac
    d = np.arange(n)
    d = np.where(d > n // 2, d - n, d).astype(float)
    m = np.abs(d) <= dmax
    dd, aa = np.abs(d[m]), a[m]
    best = None
    for w in np.linspace(0.2, 6.0, 581):
        x = dd / w
        f = np.where(x < 1e-9, 1.0, x / np.sinh(np.clip(x, 1e-9, 50)))
        # linear least squares in (N, C)
        M = np.vstack([f, np.ones_like(f)]).T
        coef, res, _, _ = np.linalg.lstsq(M, aa, rcond=None)
        r = float(np.sqrt(np.mean((M @ coef - aa) ** 2)))
        if best is None or r < best[1]:
            best = (float(w), r, float(coef[0]), float(coef[1]))
    w, r, N, C = best
    return {"w_cells": w, "rms_resid_over_N": r / max(abs(N), 1e-12),
            "N": N, "C": C,
            "x2_top_cells2": math.pi ** 2 * w ** 2 / 4.0,
            "x2_born_cells2": math.pi ** 2 * w ** 2 / 12.0}


def classical_reference():
    """Deterministic lattice kink on the same NX grid with twisted BC;
    same estimator (AC + sech fit) => reference width w_ref and mu_class.
    Using the identical estimator on the classical configuration makes the
    MC/classical ratio b free of estimator bias by construction."""
    x = (np.arange(NX) - NX / 2.0) * 1.0
    phi = (4.0 / 7.0) * np.arctan(np.exp(AM * x))
    for it in range(8000):
        up = np.roll(phi, -1).copy(); up[-1] += TWO_PI_7
        dn = np.roll(phi, 1).copy(); dn[0] -= TWO_PI_7
        vp = (AM ** 2 / 7.0) * np.sin(7.0 * phi)
        vpp = AM ** 2 * np.cos(7.0 * phi)
        res = up + dn - 2 * phi - vp
        phi += 0.8 * res / (2.0 + vpp)
        if np.max(np.abs(res)) < 1e-13:
            break
    g = np.diff(np.append(phi, phi[:1] + TWO_PI_7))
    fg = np.fft.fft(g)
    ac = np.fft.ifft(np.abs(fg) ** 2).real / NX
    fit = ac_sech_fit(ac, np.zeros(NX))
    mu_class = math.acosh(1.0 + AM ** 2 / 2.0)
    return fit, mu_class


results = {}
print("=== Route Q (2D): benchmarks ===")
# B1 free field at am = 7/8
b1 = metropolis_run(AM, 1.0, 0.0, 4000, 2000, 0.9, free_field=True)
# exact lattice <phi^2> for free field
ks = 2.0 * math.pi * np.arange(NX) / NX
kt = 2.0 * math.pi * np.arange(NT) / NT
KX, KT = np.meshgrid(ks, kt, indexing="ij")
khat2 = 4 * np.sin(KX / 2) ** 2 + 4 * np.sin(KT / 2) ** 2
phi2_exact = float(np.mean(1.0 / (khat2 + AM ** 2)))
mu_b1 = cosh_mass(b1["corr"])
mu_disp = math.acosh(1.0 + AM ** 2 / 2.0)
print(f"B1 free field: <phi^2> = {b1['phi2']:.4f} +/- {b1['phi2_err']:.4f} "
      f"(exact {phi2_exact:.4f}); a*mu = {mu_b1:.4f} (dispersion {mu_disp:.4f}); "
      f"acc = {b1['acc_rate']:.2f}")
results["B1"] = {"phi2": b1["phi2"], "phi2_err": b1["phi2_err"],
                 "phi2_exact": phi2_exact, "amu_meas": mu_b1,
                 "amu_disp": mu_disp}
assert abs(b1["phi2"] - phi2_exact) < 6 * max(b1["phi2_err"], 1e-4), "B1 phi^2 FAIL"
assert abs(mu_b1 - mu_disp) < 0.06, "B1 mass FAIL"

# B2 classical limit: kink + vacuum sectors, hbar -> 0 extrapolation
# classical reference with the IDENTICAL estimator (bias cancels in ratios)
fit_ref, MU_CLASS = classical_reference()
W_REF = fit_ref["w_cells"]
print(f"classical reference (same estimator): w_ref = {W_REF:.4f} cells "
      f"(resid {fit_ref['rms_resid_over_N']:.4f}); a*mu_class = {MU_CLASS:.4f}")
results["classical_ref"] = {"fit": fit_ref, "amu_class": MU_CLASS}

# quantum broadening is linear in hbar at small hbar (one loop); the
# benchmark is the hbar -> 0 intercept of w(hbar), which must hit w_ref.
b2_ws = {}
for hb in (0.025, 0.05):
    st = 0.18 * math.sqrt(hb / 0.05)
    v = metropolis_run(AM, hb, 0.0, 4000, 2000, st)
    k = metropolis_run(AM, hb, TWO_PI_7, 4000, 2000, st, seed_kink=True)
    fit_hb = ac_sech_fit(k["ac_g"], v["ac_g"])
    b2_ws[hb] = fit_hb["w_cells"]
    print(f"B2 hbar = {hb:.3f}: sech-fit w = {fit_hb['w_cells']:.4f} "
          f"(resid {fit_hb['rms_resid_over_N']:.4f})")
w_intercept = b2_ws[0.025] - (b2_ws[0.05] - b2_ws[0.025])     # linear in hbar
b_b2 = w_intercept / W_REF
print(f"B2 classical-limit extrapolation: w(hbar->0) = {w_intercept:.4f} "
      f"vs w_ref = {W_REF:.4f}; ratio = {b_b2:.4f}")
results["B2"] = {"w_by_hbar": b2_ws, "w_intercept": w_intercept,
                 "b_intercept_vs_ref": b_b2}
assert abs(b_b2 - 1.0) < 0.10, "B2 FAIL: hbar->0 intercept misses w_ref"

print("\n=== Route Q (2D): hbar ramp at bare am0 = 7/8 ===")
results["ramp"] = {}
for hbar in (0.05, 0.2, 0.5, 1.0):
    step = 0.18 * math.sqrt(hbar / 0.05)
    vac = metropolis_run(AM, hbar, 0.0, 6000, 3000, step)
    kin = metropolis_run(AM, hbar, TWO_PI_7, 6000, 3000, step, seed_kink=True)
    mu = cosh_mass(vac["corr"])
    fit = ac_sech_fit(kin["ac_g"], vac["ac_g"])
    # bias-cancelling broadening factor: same estimator on MC and classical
    b_fac = (fit["w_cells"] * mu) / (W_REF * MU_CLASS) if mu == mu else float("nan")
    # raw moment cross-check (window 10 / 20)
    x2_top_m, x2_top_m2 = ac_moment(kin["ac_g"], vac["ac_g"])
    row = {"hbar": hbar, "amu_meas": mu, "phi2_vac": vac["phi2"],
           "fit": fit, "b_broadening": b_fac,
           "x2_top_moment_w10": x2_top_m, "x2_top_moment_w20": x2_top_m2,
           "acc_vac": vac["acc_rate"], "acc_kink": kin["acc_rate"]}
    results["ramp"][f"hbar_{hbar}"] = row
    print(f"  hbar = {hbar:4.2f}: a*mu = {mu:.4f}; <phi^2>_vac = {vac['phi2']:.4f}; "
          f"sech-fit w = {fit['w_cells']:.4f} (resid {fit['rms_resid_over_N']:.4f}); "
          f"b = (w mu)/(w_ref mu_cl) = {b_fac:.4f}")

out = "/Users/nova/ugp-physics/papers/42_phimdl_field/scripts/kink_form_factor_lattice_mc_2d_results.json"
with open(out, "w") as f:
    json.dump({k: (v if not isinstance(v, dict) else
                   {kk: (vv.tolist() if isinstance(vv, np.ndarray) else vv)
                    for kk, vv in v.items()}) for k, v in results.items()},
              f, indent=1, default=lambda o: float(o) if np.isscalar(o) else str(o))
print(f"\nSaved {out.split('/')[-1]}")
signal.alarm(0)
