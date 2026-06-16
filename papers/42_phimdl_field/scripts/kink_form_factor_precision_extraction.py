#!/usr/bin/env python3
"""Extraction of the kink broadening factor b from the precision campaign
(corrected estimator chain).

SUPERSEDES kink_form_factor_precision_analysis.py (biased t=1..3 effective
mass; broken negfrac expectation) and the first extraction pass (which ran
on campaign-2 data carrying the recentering sign defect).

Estimator chain (final, all elements benchmarked):
  recentering : exp(-ik shift) kernel (delta-test verified); two-pass
                windowed CM (+/-8 cells) — the same chain applied to the
                classical reference (bias cancellation preserved)
  mu          : cosh+const fit, dz in [1,12], jackknife over blocks;
                mu-defining ensemble = single-well vacuum; free-field gate
  w           : two-stage sech fit, jackknife over blocks; P3' inclusion
                (resid <= 0.025 AND quarter deviation <= 0.35 cells)
  cross-checks: moment width (window +/-12, tail-noise subtracted);
                campaign-2 salvage (per-block realignment, upper bound);
                patch-2 vs patch-4 capillary amplitude
  Route A     : tuning band at L=14 -> physical point; size trend L=10..20
  Route B     : coarse-grained wall-position spectrum P(k) = A/k^2 + C in
                the IR window; capillary L->inf correction A*(I3 - S3(L))

Outputs kink_form_factor_precision_extraction_results.json.
"""
import json
import math
import signal
import sys

import numpy as np

TIMEOUT_SECONDS = 1800


def _timeout(signum, frame):
    print(f"TIMEOUT {TIMEOUT_SECONDS}s reached")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

SB = "/Users/nova/ugp-physics/papers/42_phimdl_field/scripts"
TWO_PI_7 = 2.0 * math.pi / 7.0


def load(label):
    with open(f"{SB}/kink_form_factor_precision_run_{label}.json") as f:
        return json.load(f)


# ---------- shared estimator chain (identical to the runner) ----------
def recenter_fft(arr, shift):
    n = len(arr)
    k = np.fft.fftfreq(n) * 2.0 * math.pi
    return np.fft.ifft(np.fft.fft(arr) * np.exp(-1j * k * shift)).real


def wall_z0(gbar):
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


def cosh_const_fit(c, dz_min=1, dz_max=12):
    nz2 = len(c) - 1
    NZ = 2 * nz2
    dz = np.arange(dz_min, min(dz_max, nz2) + 1)
    y = np.array([c[d] for d in dz])

    def resid(mu):
        f = np.cosh(mu * (dz - NZ / 2.0))
        X = np.vstack([f, np.ones_like(f)]).T
        coef, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
        r = y - X @ coef
        return float(r @ r)

    g = (math.sqrt(5) - 1) / 2
    a, b = 0.05, 3.0
    c1, c2 = b - g * (b - a), a + g * (b - a)
    f1, f2 = resid(c1), resid(c2)
    for _ in range(200):
        if f1 < f2:
            b, c2, f2 = c2, c1, f1
            c1 = b - g * (b - a)
            f1 = resid(c1)
        else:
            a, c1, f1 = c1, c2, f2
            c2 = a + g * (b - a)
            f2 = resid(c2)
    return (a + b) / 2


def jk_mu(corr_blocks, **kw):
    cb = np.array(corr_blocks)
    nb = len(cb)
    full = cosh_const_fit(cb.mean(axis=0), **kw)
    jks = np.array([cosh_const_fit(np.delete(cb, j, axis=0).mean(axis=0),
                                   **kw) for j in range(nb)])
    return full, math.sqrt(max(nb - 1, 1) * float(np.var(jks)))


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


def sech_profile_fit(prof, wmax=8.0):
    z1_0 = float(np.argmax(prof))
    w, z1, r, N, C = sech_fit_pass(prof, np.linspace(0.15, wmax, 400),
                                   np.linspace(-1.0, 1.0, 21), z1_0)
    w, z1, r, N, C = sech_fit_pass(
        prof, np.linspace(max(w - 0.06, 0.05), w + 0.06, 61),
        np.linspace(z1 - z1_0 - 0.06, z1 - z1_0 + 0.06, 13), z1_0)
    return {"w_cells": w, "z1": z1, "rms_resid_over_N": r / max(abs(N), 1e-12),
            "N": N, "C": C}


def jk_w(prof_blocks):
    pb = np.array(prof_blocks)
    nb = len(pb)
    fit = sech_profile_fit(pb.mean(axis=0))
    ws = np.array([sech_profile_fit(np.delete(pb, j, axis=0).mean(axis=0))
                   ["w_cells"] for j in range(nb)])
    return fit, math.sqrt(max(nb - 1, 1) * float(np.var(ws)))


def quarter_ws(prof_blocks):
    pb = np.array(prof_blocks)
    return [sech_profile_fit(pb[i * 4:(i + 1) * 4].mean(axis=0))["w_cells"]
            for i in range(4)]


def moment_width(prof, win=12.0):
    """Second-moment width from a mean profile: tail-noise level estimated
    outside the window and subtracted; returns sqrt(<d^2>)."""
    nz = len(prof)
    z1 = sech_profile_fit(prof)["z1"]
    d = (np.arange(nz) - z1 + nz / 2.0) % nz - nz / 2.0
    inw = np.abs(d) <= win
    tail = float(np.mean(np.clip(np.asarray(prof)[~inw], 0, None))) \
        if (~inw).sum() else 0.0
    w_arr = np.clip(np.asarray(prof)[inw] - tail, 0, None)
    dd = d[inw]
    tot = float(w_arr.sum())
    return math.sqrt(float((w_arr * dd ** 2).sum()) / tot) if tot > 0 \
        else float("nan")


def classical_reference(am, nz):
    z = (np.arange(nz) - nz / 2.0)
    phi = (4.0 / 7.0) * np.arctan(np.exp(am * z))
    for _ in range(20000):
        up = np.roll(phi, -1).copy(); up[-1] += TWO_PI_7
        dn = np.roll(phi, 1).copy(); dn[0] -= TWO_PI_7
        vp = (am ** 2 / 7.0) * np.sin(7.0 * phi)
        vpp = am ** 2 * np.cos(7.0 * phi)
        res = up + dn - 2 * phi - vp
        phi += 0.8 * res / (2.0 + vpp)
        if np.max(np.abs(res)) < 1e-13:
            break
    g = np.diff(np.append(phi, phi[:1] + TWO_PI_7))
    rec = recenter_fft(g, nz / 2.0 - wall_z0(g))
    fit = sech_profile_fit(rec)
    fit["moment_w"] = moment_width(rec)
    return fit


def wls(X, y, e):
    W = np.diag(1.0 / np.asarray(e) ** 2)
    cov = np.linalg.inv(X.T @ W @ X)
    beta = cov @ X.T @ W @ y
    chi2 = float((y - X @ beta).T @ W @ (y - X @ beta))
    return beta, cov, chi2


results = {}
print("=== kink form factor precision extraction (corrected chain) ===\n")

# ---------- gates and shared mu ----------
mu_free, err_free = jk_mu(load("v2_free_L10")["corr_blocks"])
MU_EXACT = math.acosh(1.0 + 0.875 ** 2 / 2.0)
pull = (mu_free - MU_EXACT) / max(err_free, 1e-9)
print(f"free-field gate: a*mu = {mu_free:.4f} +/- {err_free:.4f} vs "
      f"{MU_EXACT:.4f} (pull {pull:+.2f}) -> "
      f"{'PASS' if abs(pull) < 2.0 else 'FAIL'}")
results["free_gate"] = {"mu": mu_free, "err": err_free, "pull": pull}

mus = {}
print("\n-- shared meson masses (single-well vacuum, cosh+const) --")
for am0, lbl in ((4.6, "v2_vac_460"), (5.09, "v2_vac_509"),
                 (5.3, "v2_vac_530"), (5.55, "v2_vac_555")):
    mu, err = jk_mu(load(lbl)["corr_blocks"])
    mus[am0] = (mu, err)
    print(f"  am0={am0}: a*mu = {mu:.4f} +/- {err:.4f}")
muh, errh = jk_mu(load("v2_vach_530")["corr_blocks"])
print(f"  hops-on systematic at 5.3: {muh:.4f} +/- {errh:.4f} "
      f"(shift {muh - mus[5.3][0]:+.4f})")
results["mu"] = {str(k): v for k, v in mus.items()}
results["mu_hops_shift"] = muh - mus[5.3][0]
mus_f = {}
for am0, lbl in ((2.72, "v2_vac_272f"), (2.90, "v2_vac_290f")):
    mu, err = jk_mu(load(lbl)["corr_blocks"])
    mus_f[am0] = (mu, err)
    print(f"  fine am0={am0}: a*mu = {mu:.4f} +/- {err:.4f}")

ref = classical_reference(0.875, 32)
W_REF, MU_CLASS = ref["w_cells"], MU_EXACT
ref_f = classical_reference(0.4375, 48)
MU_CLASS_F = math.acosh(1.0 + 0.4375 ** 2 / 2.0)
print(f"\nclassical refs: w_ref = {W_REF:.4f} (moment "
      f"{ref['moment_w']:.4f}); fine w_ref = {ref_f['w_cells']:.4f}")
results["refs"] = {"w_ref": W_REF, "w_ref_moment": ref["moment_w"],
                   "w_ref_fine": ref_f["w_cells"], "mu_class": MU_CLASS,
                   "mu_class_fine": MU_CLASS_F}

# ---------- Route A points ----------
POINTS = {
    (5.09, 10): ["v3_k509_L10"], (5.09, 12): ["v3_k509_L12"],
    (5.09, 14): ["v3_k509_L14a", "v3_k509_L14b"],
    (5.09, 16): ["v3_k509_L16", "v3_k509_L16b"],
    (5.09, 20): ["v3_k509_L20", "v3_k509_L20b"],
    (5.09, 24): ["v3_k509_L24"], (5.09, 28): ["v3_k509_L28"],
    (5.3, 14): ["v3_k530_L14a", "v3_k530_L14b"],
    (5.3, 16): ["v3_k530_L16"], (5.3, 20): ["v3_k530_L20"],
    (5.55, 14): ["v3_k555_L14a", "v3_k555_L14b"],
    (4.6, 14): ["v3_k460_L14"],
}
print("\n-- Route A points (corrected recentering; P3') --")
points = {}
for (am0, L), labels in sorted(POINTS.items()):
    runs = [load(x) for x in labels]
    pb = [b for r in runs for b in r["prof_blocks"]]
    fit, w_err = jk_w(pb)
    qws = [q for r in runs for q in quarter_ws(r["prof_blocks"])]
    qdev = float(np.max(np.abs(np.array(qws) - np.median(qws))))
    negf = float(np.mean([r["negfrac_mean"] for r in runs]))
    drift = float(np.sqrt(np.mean([v for r in runs
                                   for v in r["z0_block_var"]])))
    mw = moment_width(np.array(pb).mean(axis=0))
    mu, mu_err = mus[am0]
    b = fit["w_cells"] * mu / (W_REF * MU_CLASS)
    b_err = b * math.hypot(w_err / fit["w_cells"], mu_err / mu)
    ok = fit["rms_resid_over_N"] <= 0.025 and qdev <= 0.35
    print(f"  am0={am0} L={L}: w = {fit['w_cells']:.4f} +/- {w_err:.4f} "
          f"(resid {fit['rms_resid_over_N']:.4f}; qdev {qdev:.3f}; negfrac "
          f"{negf:.3f}; z0 drift/blk {drift:.2f}; moment_w {mw:.3f}); "
          f"b = {b:.4f} +/- {b_err:.4f} [{'OK' if ok else 'EXCLUDED'}]")
    points[(am0, L)] = {"w": fit["w_cells"], "w_err": w_err, "b": b,
                        "b_err": b_err, "resid": fit["rms_resid_over_N"],
                        "qdev": qdev, "negfrac": negf, "moment_w": mw,
                        "included": ok}
    results[f"pt_{am0}_{L}"] = points[(am0, L)]

# moment-vs-sech estimator cross-check at the band points
print("\n-- estimator dependence (moment/sech width ratio, quantum vs "
      "classical) --")
ratio_cl = ref["moment_w"] / W_REF
for a0 in (5.09, 5.3, 5.55):
    p = points[(a0, 14)]
    rq = p["moment_w"] / p["w"]
    print(f"  am0={a0} L=14: quantum {rq:.4f} vs classical {ratio_cl:.4f} "
          f"(diff {100 * (rq / ratio_cl - 1):+.1f}%)")
    results[f"moment_check_{a0}"] = rq / ratio_cl

# ---------- campaign-2 salvage cross-check ----------
def salvage(labels):
    pbs = []
    for x in labels:
        for p in load(x)["prof_blocks"]:
            f = sech_profile_fit(p)
            pbs.append(recenter_fft(np.array(p), len(p) / 2.0 - f["z1"]))
    return jk_w(pbs)


print("\n-- campaign-2 salvage (per-block realignment; upper bound) --")
for (am0, L), labels in (((5.09, 14), ["v2_k509_L14a", "v2_k509_L14b"]),
                         ((5.3, 14), ["v2_k530_L14a", "v2_k530_L14b"]),
                         ((5.09, 16), ["v2_k509_L16"])):
    fit, w_err = salvage(labels)
    print(f"  am0={am0} L={L}: salvaged w = {fit['w_cells']:.4f} +/- "
          f"{w_err:.4f} (resid {fit['rms_resid_over_N']:.4f}) "
          f"vs v3 w = {points[(am0, L)]['w']:.4f}")
    results[f"salvage_{am0}_{L}"] = {"w": fit["w_cells"], "w_err": w_err}

# ---------- Route A: size trend ----------
print("\n-- Route A size trend at am0 = 5.09 --")
scan = [(L, p["b"], p["b_err"]) for (a0, L), p in sorted(points.items())
        if a0 == 5.09 and p["included"]]
Ls = np.array([s[0] for s in scan], float)
bs = np.array([s[1] for s in scan])
es = np.array([s[2] for s in scan])
fits = {}
if len(Ls) >= 3:
    X1 = np.vstack([np.ones_like(Ls), -1.0 / Ls]).T
    b1, c1m, x1 = wls(X1, bs, es)
    fits["F1"] = {"b_inf": float(b1[0]), "err": float(np.sqrt(c1m[0, 0])),
                  "c1": float(b1[1]), "chi2_dof": x1 / max(len(Ls) - 2, 1)}
    mu509 = mus[5.09][0]
    X2 = np.vstack([np.ones_like(Ls), np.exp(-mu509 * Ls)]).T
    b2, c2m, x2 = wls(X2, bs, es)
    fits["F2"] = {"b_inf": float(b2[0]), "err": float(np.sqrt(c2m[0, 0])),
                  "c2": float(b2[1]), "chi2_dof": x2 / max(len(Ls) - 2, 1)}
X3 = np.ones((len(Ls), 1))
b3, c3m, x3 = wls(X3, bs, es)
fits["F3"] = {"b_inf": float(b3[0]), "err": float(np.sqrt(c3m[0, 0])),
              "chi2_dof": x3 / max(len(Ls) - 1, 1)}
for n, f in fits.items():
    print(f"  {n}: b_inf = {f['b_inf']:.4f} +/- {f['err']:.4f}; "
          f"chi2/dof = {f['chi2_dof']:.2f}")
results["sizefits"] = fits
results["scan"] = {"L": Ls.tolist(), "b": bs.tolist(), "e": es.tolist()}


# geometry-true capillary form: b(L) = b_inf - kappa * (I3 - S3(L))
def khat2_fine(L):
    k = 2.0 * np.pi * np.fft.fftfreq(int(L))
    KX, KY, KT = np.meshgrid(k, k, k, indexing="ij")
    return 4.0 * (np.sin(KX / 2) ** 2 + np.sin(KY / 2) ** 2
                  + np.sin(KT / 2) ** 2)


def S3_geo(L):
    k2 = khat2_fine(L)
    m = k2 > 1e-12
    return float(np.sum(1.0 / k2[m]) / k2.size)


def I3_geo(n=300):
    k = 2.0 * np.pi * (np.arange(n) + 0.5) / n - np.pi
    KX, KY, KT = np.meshgrid(k, k, k, indexing="ij")
    k2 = 4.0 * (np.sin(KX / 2) ** 2 + np.sin(KY / 2) ** 2
                + np.sin(KT / 2) ** 2)
    return float(np.mean(1.0 / k2))


I3g = I3_geo()
# fit on the w-ladder: w jackknife errors are mu-independent (the shared-mu
# error is common-mode across L and must not enter the size fit); grid
# resolution floor 0.003 cells on the jackknife errors
wsL = np.array([points[(5.09, int(L))]["w"] for L in Ls])
weL = np.array([max(points[(5.09, int(L))]["w_err"], 0.003) for L in Ls])
xg = np.array([I3g - S3_geo(L) for L in Ls])
Xg = np.vstack([np.ones_like(xg), -xg]).T
bg, cg, x2g = wls(Xg, wsL, weL)
kappa_w = float(bg[1])
print(f"  KAPPA (geometry-true, w-ladder): w_inf = {bg[0]:.4f} +/- "
      f"{math.sqrt(cg[0, 0]):.4f}; kappa_w = {kappa_w:.3f}; chi2/dof = "
      f"{x2g / max(len(Ls) - 2, 1):.2f}")
# completion applied at L = 14 (the band lattice), scaled into b units
d14 = I3g - S3_geo(14)
dw_kappa = kappa_w * d14
dw_err = float(np.sqrt(cg[1, 1])) * d14
w14 = points[(5.09, 14)]["w"]
# F1-form cross-check on the w-ladder
X1w = np.vstack([np.ones_like(Ls), -1.0 / Ls]).T
b1w, c1w, _ = wls(X1w, wsL, weL)
dw_F1 = float(b1w[1]) / 14.0
size_rel = dw_kappa / w14
size_rel_spread = max(dw_err, abs(dw_F1 - dw_kappa)) / w14
print(f"  w completion at L=14: kappa {dw_kappa:+.4f} +/- {dw_err:.4f}; "
      f"F1 {dw_F1:+.4f} -> relative {size_rel:+.4f} +/- "
      f"{size_rel_spread:.4f}")
results["size_completion"] = {"delta_rel": size_rel,
                              "spread_rel": size_rel_spread,
                              "kappa_w": kappa_w, "dw_kappa": dw_kappa,
                              "dw_F1": dw_F1,
                              "inv_sigma_eff_IR":
                                  kappa_w * 2 * w14 * (math.pi ** 2 / 4)}

# ---------- physical point at L = 14 ----------
# mu-noise-cancelling formulation: at the physical point (measured mu =
# mu_class) the interpolated b reduces to w(am0*)/w_ref where mu(am0*) =
# mu_class; common mu fluctuations cancel, leaking only via dw/dam0.
print("\n-- physical-point interpolation at L = 14 (mu-cancelling) --")
A0 = np.array([4.6, 5.09, 5.3, 5.55])
WW = np.array([points[(a, 14)]["w"] for a in A0])
# error floor = fit-grid resolution (jackknife variance can quantize to 0)
WE = np.array([max(points[(a, 14)]["w_err"], 0.003) for a in A0])
MM = np.array([mus[a][0] for a in A0])
ME = np.array([mus[a][1] for a in A0])
Xw = np.vstack([np.ones_like(A0), A0 - 5.2]).T
bw, cw, x2w = wls(Xw, WW, WE)
Xm = np.vstack([np.ones_like(A0), A0 - 5.2]).T
bmu, cmu, x2m = wls(Xm, MM, ME)
dmu_dam0 = float(bmu[1])
am0_star = 5.2 + (MU_CLASS - float(bmu[0])) / dmu_dam0
am0_star_err = float(np.sqrt(cmu[0, 0])) / abs(dmu_dam0)
w_star = float(bw[0] + bw[1] * (am0_star - 5.2))
dw_dam0 = float(bw[1])
w_star_err = math.hypot(float(np.sqrt(cw[0, 0])),
                        dw_dam0 * am0_star_err)
b_phys14 = w_star / W_REF
b_phys14_err = w_star_err / W_REF
print(f"  am0* = {am0_star:.3f} +/- {am0_star_err:.3f} "
      f"(dmu/dam0 = {dmu_dam0:.3f}; w-fit chi2/dof "
      f"{x2w / 2:.2f}; mu-fit chi2/dof {x2m / 2:.2f})")
print(f"  w* = {w_star:.4f} +/- {w_star_err:.4f} (dw/dam0 = {dw_dam0:+.3f})")
print(f"  b(phys, L=14) = {b_phys14:.4f} +/- {b_phys14_err:.4f}")
results["phys14"] = {"b": b_phys14, "err": b_phys14_err,
                     "am0_star": am0_star, "am0_star_err": am0_star_err,
                     "w_star": w_star, "dw_dam0": dw_dam0}

# mu-window systematic: refit the band with dz in [2,12]
MM2 = []
for a0, lbl in ((4.6, "v2_vac_460"), (5.09, "v2_vac_509"),
                (5.3, "v2_vac_530"), (5.55, "v2_vac_555")):
    MM2.append(jk_mu(load(lbl)["corr_blocks"], dz_min=2)[0])
MM2 = np.array(MM2)
bmu2, _, _ = wls(Xm, MM2, ME)
am0_star2 = 5.2 + (MU_CLASS - float(bmu2[0])) / float(bmu2[1])
b_window = (float(bw[0] + bw[1] * (am0_star2 - 5.2))) / W_REF
print(f"  mu-window systematic: dz>=2 gives am0* = {am0_star2:.3f}, "
      f"b = {b_window:.4f} (shift {b_window - b_phys14:+.4f})")
results["mu_window_syst"] = b_window - b_phys14

# ---------- Route B: capillary spectrum ----------
print("\n-- Route B: capillary amplitude and L->inf correction --")


def khat2_fine(L):
    k = 2.0 * np.pi * np.fft.fftfreq(L)
    KX, KY, KT = np.meshgrid(k, k, k, indexing="ij")
    return 4.0 * (np.sin(KX / 2) ** 2 + np.sin(KY / 2) ** 2
                  + np.sin(KT / 2) ** 2)


def S3_fine(L):
    k2 = khat2_fine(L)
    m = k2 > 1e-12
    return float(np.sum(1.0 / k2[m]) / k2.size)


def I3_inf(n=300):
    k = 2.0 * np.pi * (np.arange(n) + 0.5) / n - np.pi
    KX, KY, KT = np.meshgrid(k, k, k, indexing="ij")
    k2 = 4.0 * (np.sin(KX / 2) ** 2 + np.sin(KY / 2) ** 2
                + np.sin(KT / 2) ** 2)
    return float(np.mean(1.0 / k2))


def cap_fit(pk, L, patch):
    """Fit P(m) = A / k_phys^2 + C on coarse-grid IR modes
    (k_phys = 2 pi m / L in fine-lattice units; window |m_i| <= Lp/4)."""
    Lp = L // patch
    m = np.fft.fftfreq(Lp) * Lp
    MX, MY, MT = np.meshgrid(m, m, m, indexing="ij")
    k2 = (2 * np.pi / L) ** 2 * (MX ** 2 + MY ** 2 + MT ** 2)
    sel = (k2 > 1e-12) & (np.abs(MX) <= Lp / 4) & (np.abs(MY) <= Lp / 4) \
        & (np.abs(MT) <= Lp / 4)
    x = 1.0 / k2[sel]
    y = np.asarray(pk)[sel]
    A, C = 1.0, float(np.median(y))
    for _ in range(80):
        pred = np.clip(A * x + C, 1e-12, None)
        wgt = 1.0 / pred ** 2
        S = np.array([[np.sum(wgt * x * x), np.sum(wgt * x)],
                      [np.sum(wgt * x), np.sum(wgt)]])
        v = np.array([np.sum(wgt * x * y), np.sum(wgt * y)])
        An, Cn = np.linalg.solve(S, v)
        if abs(An - A) < 1e-14 and abs(Cn - C) < 1e-14:
            break
        A, C = float(An), float(Cn)
    return A, C


I3 = I3_inf()
results["I3"] = I3
capA = {}
for (am0, L), labels in sorted(POINTS.items()):
    runs = [load(x) for x in labels]
    patch = runs[0].get("patch", 2)
    if L // patch < 4:   # coarse grid too small for an IR window
        continue
    pk = np.mean([np.array(r["pk_mean"]) for r in runs], axis=0)
    A, C = cap_fit(pk, L, patch)
    dI = A * (I3 - S3_fine(L))
    capA[(am0, L)] = {"A": A, "C": C, "patch": patch, "delta_inf": dI}
    print(f"  am0={am0} L={L} (patch {patch}): A = 1/sigma = {A:.3f}, "
          f"C = {C:.3f}; capillary L->inf adds {dI:+.4f} cells^2")
    results[f"cap_{am0}_{L}"] = capA[(am0, L)]
sigma_cl = 8.0 * 0.875 / 49.0
print(f"  classical-tension reference: 1/sigma_cl = {1 / sigma_cl:.3f}")
results["inv_sigma_classical"] = 1 / sigma_cl

# Route B physical point: capillary completion of the L=14 band value
A14 = float(np.mean([capA[(a, 14)]["A"] for a in (5.09, 5.3, 5.55)]))
corr = A14 * (I3 - S3_fine(14))
r2_ref = (math.pi ** 2 / 4.0) * W_REF ** 2
w_phys14 = b_phys14 * W_REF
r2_phys14 = (math.pi ** 2 / 4.0) * w_phys14 ** 2
b_B = math.sqrt(max(r2_phys14 + corr, 1e-9) / r2_ref)
print(f"  Route B: A(L14 mean) = {A14:.3f}; correction = {corr:+.4f} "
      f"cells^2 => b_B(phys, inf) = {b_B:.4f}")
results["routeB"] = {"A14": A14, "corr": corr, "b_B": b_B}

# ---------- finer spacing ----------
print("\n-- finer-spacing physical point (am = 7/16, L = 20) --")
fine = {}
for am0, lbl in ((2.72, "v3_k272f_L20"), (2.90, "v3_k290f_L20")):
    r = load(lbl)
    fit, w_err = jk_w(r["prof_blocks"])
    mu, mu_err = mus_f[am0]
    b = fit["w_cells"] * mu / (ref_f["w_cells"] * MU_CLASS_F)
    b_err = b * math.hypot(w_err / fit["w_cells"], mu_err / mu)
    fine[am0] = (mu, b, b_err)
    print(f"  am0={am0}: w = {fit['w_cells']:.4f} +/- {w_err:.4f} (resid "
          f"{fit['rms_resid_over_N']:.4f}); b = {b:.4f} +/- {b_err:.4f}")
    results[f"fine_{am0}"] = {"w": fit["w_cells"], "b": b, "b_err": b_err}
fm = np.array([fine[a][0] for a in (2.72, 2.90)])
fb = np.array([fine[a][1] for a in (2.72, 2.90)])
fe = np.array([fine[a][2] for a in (2.72, 2.90)])
sl = (fb[1] - fb[0]) / (fm[1] - fm[0])
b_fine = float(fb[0] + sl * (MU_CLASS_F - fm[0]))
b_fine_err = float(np.sqrt(np.mean(fe ** 2)))
print(f"  fine physical point: b = {b_fine:.4f} +/- {b_fine_err:.4f}")
results["fine_phys"] = {"b": b_fine, "err": b_fine_err}

# ---------- systematic folds for the verdict (pre-registered) ----------
# estimator shape: half-spread sech vs moment width ratio at the band
devs = [abs(results[f"moment_check_{a}"] - 1.0) for a in (5.09, 5.3, 5.55)]
shape_syst = 0.5 * float(np.mean(devs)) * b_phys14
# spacing: half the coarse-fine physical-point difference
spacing_fold = 0.5 * abs(b_phys14 - b_fine)
results["shape_syst"] = shape_syst
results["spacing_fold"] = spacing_fold
print(f"\nsystematic folds: shape = {shape_syst:.4f}; spacing = "
      f"{spacing_fold:.4f}; mu-window = {abs(results['mu_window_syst']):.4f}")

out = f"{SB}/kink_form_factor_precision_extraction_results.json"
with open(out, "w") as f:
    json.dump(results, f, indent=1,
              default=lambda o: float(o) if isinstance(o, np.floating) else o)
print(f"\nSaved {out.split('/')[-1]}")
signal.alarm(0)
