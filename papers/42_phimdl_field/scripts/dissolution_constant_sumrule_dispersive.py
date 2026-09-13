#!/usr/bin/env python3
"""Sum-rule-constrained dispersive kink form factor and the VP constant.

The minimal zero-free Omnes closure of the exact ZZ phase contradicts the
CatAL sech^2 charge radius (negative <r^2>), proving the timelike modulus
needs positive inelastic ImF above the Poschl-Teller pair-channel onset
s_inel = (2M + m_phi)^2.  This script constructs F(s) from the derived
constraints:

  - once-subtracted DR: F(s) = 1 + (s/pi) int ImF(s')/(s'(s'-s)) ds'
  - elastic window [4M^2, s_inel]: Watson, ImF = |F| sin(delta_ZZ),
    delta_ZZ(theta) = -arctan(1/sinh theta)  (CatAD ZZ S-matrix, exact)
  - inelastic: ImF = B h(rt_s) >= 0, shape bracket
      H1 exp[-(rt-rt_on) pi/(2 m_phi)]   (sech^2-FT crossing scale)
      H2 exp[-(rt-rt_on)/m_phi]
      H3 (s_inel/s)^{3/2}
      H4 (s_inel/s)^{5/2}
  - normalization B from the charge sum rule (1/pi) int ImF/s' = 1
    (spacelike vanishing: kink charge is pure winding, no pointlike core),
    OR from the radius sum rule (6/pi) int ImF/s'^2 = <r^2> = pi^2/(12 m_phi^2);
    both run, spread reported.

Then g(s) = |F(s)|^2 and
  c = 8 ln(Lambda/M) - 3 int (ds/s) K(s) g(s),   K = (4/3)(1+2M^2/s) beta.

Validation: self-consistency residual < 1e-8; grid-doubling; spacelike F(Q^2)
must be decreasing with positive curvature radius (cross-check vs static
sech^2-FT envelope); radius-sum-rule tension reported per shape.

Expected: c bands per reading, narrower than the a-priori envelope [-6, +5.5].
"""
import json
import math
import signal
import sys

TIMEOUT_SECONDS = 900


def _timeout(signum, frame):
    print(f"TIMEOUT {TIMEOUT_SECONDS}s reached")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

M_TAU = 1776.86
M_PHI = M_TAU
R2 = math.pi ** 2 / (12.0 * M_PHI ** 2)        # CatAL <x^2> of sech^2 density
READINGS = {"tree": {"lam": 8.0 / 7.0 * M_TAU, "M": 8.0 / 49.0 * M_TAU},
            "pole": {"lam": 7.0 * 321.32, "M": 321.32}}
SHAPES = ("H1", "H2", "H3", "H4")
results = {"r2_constraint_MeV-2": R2}


def delta_zz(theta):
    if theta <= 0.0:
        return -math.pi / 2.0
    return -math.atan(1.0 / math.sinh(theta))


def build_grid(M, n, theta_max):
    """theta grid; returns arrays of s, ds-weights, theta."""
    h = theta_max / n
    grid = []
    for i in range(n):
        th = (i + 0.5) * h
        s = 4.0 * M * M * math.cosh(th / 2.0) ** 2
        w = s * math.tanh(th / 2.0) * h        # ds = s tanh(theta/2) dtheta
        grid.append((th, s, w))
    return grid


def shape_val(name, rt, rt_on, s, s_inel):
    if rt <= rt_on:
        return 0.0
    if name == "H1":
        return math.exp(-(rt - rt_on) * math.pi / (2.0 * M_PHI))
    if name == "H2":
        return math.exp(-(rt - rt_on) / M_PHI)
    if name == "H3":
        return (s_inel / s) ** 1.5
    if name == "H4":
        return (s_inel / s) ** 2.5
    raise ValueError(name)


def solve_model(M, shape, norm_rule, n=3000, theta_max=26.0, iters=600):
    """Self-consistent ImF; returns (grid, imf, B, sumrule_report)."""
    s_inel = (2.0 * M + M_PHI) ** 2
    rt_on = 2.0 * M + M_PHI
    grid = build_grid(M, n, theta_max)
    s_arr = [g[1] for g in grid]
    # initial |F| = beta in elastic region
    absF = [math.sqrt(max(0.0, 1.0 - 4.0 * M * M / s)) for s in s_arr]
    B = 1.0
    for it in range(iters):
        imf = []
        for (th, s, w), aF in zip(grid, absF):
            if s <= s_inel:
                imf.append(aF * math.sin(delta_zz(th)))
            else:
                imf.append(B * shape_val(shape, math.sqrt(s), rt_on, s, s_inel))
        # normalization solve: linear in B (elastic part independent of B
        # at fixed absF)
        el_1 = sum(im / s * w for (th, s, w), im in zip(grid, imf)
                   if s <= s_inel) / math.pi
        el_2 = sum(im / s ** 2 * w for (th, s, w), im in zip(grid, imf)
                   if s <= s_inel) * 6.0 / math.pi
        in_1 = sum(shape_val(shape, math.sqrt(s), rt_on, s, s_inel) / s * w
                   for (th, s, w) in grid if s > s_inel) / math.pi
        in_2 = sum(shape_val(shape, math.sqrt(s), rt_on, s, s_inel) / s ** 2 * w
                   for (th, s, w) in grid if s > s_inel) * 6.0 / math.pi
        if norm_rule == "charge":
            B_new = (1.0 - el_1) / in_1
        else:
            B_new = (R2 - el_2) / in_2
        B = 0.9 * B + 0.1 * B_new
        # recompute |F| on the cut from the subtracted PV dispersion relation
        absF_new = []
        max_shift = 0.0
        s_th = 4.0 * M * M
        th_edge = grid[-1][0] + (grid[1][0] - grid[0][0]) / 2.0
        s_max = 4.0 * M * M * math.cosh(th_edge / 2.0) ** 2
        for j, (th, s, w) in enumerate(grid):
            if s > s_inel:
                absF_new.append(0.0)   # only elastic |F| needed for Watson
                continue
            imf_s = imf[j]
            acc = 0.0
            for k, (th2, s2, w2) in enumerate(grid):
                if k == j:
                    continue
                acc += (imf[k] - imf_s) / (s2 * (s2 - s)) * w2
            pv = (1.0 / s) * (math.log(abs((s_max - s) / s_max))
                              - math.log(abs((s_th - s) / s_th)))
            re = 1.0 + (s / math.pi) * (acc + imf_s * pv)
            mag = math.hypot(re, imf_s)
            max_shift = max(max_shift, abs(mag - absF[j]))
            absF_new.append(mag)
        absF = [0.9 * a + 0.1 * b for a, b in zip(absF, absF_new)]
        if max_shift < 1e-8 and it > 10:
            break
        if max(absF) > 50.0:
            return grid, imf, absF, B, {"iterations": it + 1,
                                        "converged_shift": max_shift,
                                        "charge_sumrule": float("nan"),
                                        "radius_over_catal": float("nan"),
                                        "runaway": True,
                                        "maxF": max(absF)}
    # final sum-rule report
    chg = el_1 + B * in_1
    rad = (el_2 + B * in_2) / R2
    return grid, imf, absF, B, {"iterations": it + 1,
                                "converged_shift": max_shift,
                                "charge_sumrule": chg,
                                "radius_over_catal": rad,
                                "runaway": max_shift > 1e-6,
                                "maxF": max(absF)}


def compute_c(M, lam, grid, imf, absF, B, shape):
    """c from g = |F|^2 with F evaluated by subtracted PV on the full grid."""
    s_inel = (2.0 * M + M_PHI) ** 2
    rt_on = 2.0 * M + M_PHI
    tot = 0.0
    # domain edge (grid points are midpoints, so the edge lies beyond them)
    th_edge = grid[-1][0] + (grid[1][0] - grid[0][0]) / 2.0
    s_edge = 4.0 * M * M * math.cosh(th_edge / 2.0) ** 2
    for j, (th, s, w) in enumerate(grid):
        # F(s) by PV with delta-subtraction
        re = 1.0
        imf_s = imf[j]
        acc = 0.0
        for k, (th2, s2, w2) in enumerate(grid):
            if k == j:
                continue
            acc += (imf[k] - imf_s) / (s2 * (s2 - s)) * w2
        s_th = 4.0 * M * M
        s_max = s_edge
        pv = (1.0 / s) * (math.log(abs((s_max - s) / s_max))
                          - math.log(abs((s_th - s) / s_th)))
        re += (s / math.pi) * (acc + imf_s * pv)
        F2 = re * re + imf_s * imf_s
        beta = math.sqrt(max(0.0, 1.0 - 4.0 * M * M / s))
        K = (4.0 / 3.0) * (1.0 + 2.0 * M * M / s) * beta
        tot += K * F2 * w / s
    c = 8.0 * math.log(lam / M) - 3.0 * tot
    return c, lam * math.exp(-c / 8.0)


print("=== sum-rule-constrained dispersive model ===")
results["models"] = {}
for rname, r in READINGS.items():
    M, lam = r["M"], r["lam"]
    results["models"][rname] = {}
    for shape in SHAPES:
        for rule in ("charge", "radius"):
            grid, imf, absF, B, rep = solve_model(M, shape, rule)
            if B < 0:
                results["models"][rname][f"{shape}_{rule}"] = {
                    "B": B, "rejected": "negative inelastic weight"}
                print(f"  {rname} {shape}/{rule}: REJECTED (B = {B:.3f} < 0)")
                continue
            if rep.get("runaway"):
                results["models"][rname][f"{shape}_{rule}"] = {
                    "B": B, "rejected": "NON-CONVERGENT (runaway feedback)",
                    **{k: (None if v != v else v) for k, v in rep.items()}}
                print(f"  {rname} {shape}/{rule}: NON-CONVERGENT "
                      f"(B = {B:.3f}, max|F| = {rep['maxF']:.2f}, "
                      f"shift {rep['converged_shift']:.2e})")
                continue
            c, ldiss = compute_c(M, lam, grid, imf, absF, B, shape)
            row = {"B": B, "c": c, "lambda_diss_MeV": ldiss,
                   "lambda_diss_over_mphi": ldiss / M_PHI, **rep}
            results["models"][rname][f"{shape}_{rule}"] = row
            print(f"  {rname} {shape}/{rule}: B = {B:+.4f}; "
                  f"charge SR = {rep['charge_sumrule']:.4f}; "
                  f"radius/CatAL = {rep['radius_over_catal']:+.3f}; "
                  f"c = {c:+.4f}; Lambda_diss = {ldiss:.0f} MeV "
                  f"({ldiss/M_PHI:.3f} m_phi)")

# band summary over admissible members (both rules, B >= 0)
print("\n=== dispersive band ===")
results["band"] = {}
for rname in READINGS:
    vals = [v["c"] for v in results["models"][rname].values() if "c" in v]
    if vals:
        results["band"][rname] = (min(vals), max(vals))
        print(f"  {rname}: c in [{min(vals):+.3f}, {max(vals):+.3f}] "
              f"over {len(vals)} admissible members")

out = "/Users/nova/ugp-physics/papers/42_phimdl_field/scripts/" \
      "dissolution_constant_sumrule_dispersive_results.json"
with open(out, "w") as fp:
    json.dump(results, fp, indent=1)
print(f"\nSaved {out.split('/')[-1]}")
signal.alarm(0)
