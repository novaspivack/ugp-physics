#!/usr/bin/env python3
"""RG-improved vacuum-selection direction for the Z7 vacua (088-R07, Task 1).

Scheme: Lambda_GTE-anchored MSbar with the MDL matching condition -- the
certified Lagrangian is the complete dim-<=4 action at the EFT boundary
Lambda_GTE = 2.01 GeV (Rank 136-VCOUP uniqueness scan), so all Z7-breaking
local counterterms vanish at mu = Lambda_GTE and the vacuum-label difference
Delta V(k) is pure radiative running from Lambda_GTE down to the mass scales.
Leading logs are resummed with the CatAL beta coefficients b0 = 7, b1 = 26:

  V_i(k) = (n_i/64 pi^2) [ -c_i m_i^4(k; mu = m_i)
                           - 2 Int_{ln m_i}^{ln Lambda} m_i^4(k; mu) d ln mu ]

with running e^2(mu) (gauge) and g(mu) (chi mass, anomalous-dimension envelope
gamma_{m^2} in {0, +-6 e^2/16 pi^2}); spectrum per vacuum k: 3 dof vector
m_A = e sqrt(Z_k), 1 dof scalar m_chi = g/sqrt(Z_k); Z_k literal/compact.
Thermal piece: exact one-loop J_B with couplings at mu_T (pi T default),
optional daisy on the longitudinal mode.

Couplings (this session's Task-2 outputs): e^2(Lambda_GTE) in {3.5 (CatAL
Villain), 3.758 (PDG-matched)}; g(Lambda_GTE) = m_tau = 1.77686 GeV (CatB
zero-new-scale completion) with robustness bracket {0.29, 0.5, 1.0}.

Probes: P1 matching-scale Lambda -> Lambda/sqrt2, sqrt2 Lambda (anchor run
consistently); P2 running order + gamma_m envelope; P3 scheme change vs the
R06 decoupling scheme (fixed-coupling band reproduced for comparison);
P4 UV-decoupling damping 1/(1+(m/Lambda)^4); P5 mu_T in {pi T, 2 pi T}.
Validations: J_B(0) = -pi^4/45; fixed-coupling reduction to the standard CW
form; eps -> 0 linear vanishing + analytic derivative cross-check; T -> 0.
Deliverables: verdict table Delta V(0->1) + argmin(k = 0..6) over the
configuration grid; k <= 50 runaway probe; the ROBUST/flip verdict input.
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

EPS = 7.0 / 9.0
LAM0 = 2.01                     # GeV, Lambda_GTE (P39)
G_DERIVED = 1.77686             # g = m_tau (Task-2 CatB)
E2_VILLAIN = 3.5
E2_PDG = 3.758                  # PDG-matched (color_coupling_e_normalization)
B0, B1 = 7.0, 26.0              # CatAL (P39, F21 species count)
PI = math.pi

def Zk(k, reading):
    p = 2.0 * PI * k / 7.0
    if reading == "literal":
        return 1.0 + 2.0 * EPS * p * p
    return 1.0 + 4.0 * EPS * (1.0 - math.cos(p))

# ---------- running coupling tables ----------
def build_alpha_table(a_anchor, mu_anchor, loops, mu_min=0.05, mu_max=8.0, n=1600):
    """alpha(mu) on a log grid via RK4 both directions from the anchor."""
    def rhs(a):
        d = -(B0 / (2.0 * PI)) * a * a
        if loops >= 2:
            d += -(B1 / (8.0 * PI ** 2)) * a ** 3
        return d
    ts = [math.log(mu_min) + i * (math.log(mu_max) - math.log(mu_min)) / (n - 1)
          for i in range(n)]
    t_anchor = math.log(mu_anchor)
    # integrate from anchor outward
    vals = [None] * n
    # find nearest index
    i0 = min(range(n), key=lambda i: abs(ts[i] - t_anchor))
    # downward
    a = a_anchor
    t = t_anchor
    for i in range(i0, -1, -1):
        h = ts[i] - t
        # single RK4 step (h negative)
        k1 = rhs(a); k2 = rhs(a + 0.5*h*k1); k3 = rhs(a + 0.5*h*k2); k4 = rhs(a + h*k3)
        a = a + h / 6.0 * (k1 + 2*k2 + 2*k3 + k4)
        a = min(a, 3.0)
        vals[i] = a
        t = ts[i]
    # upward
    a = a_anchor
    t = t_anchor
    for i in range(i0, n):
        h = ts[i] - t
        k1 = rhs(a); k2 = rhs(a + 0.5*h*k1); k3 = rhs(a + 0.5*h*k2); k4 = rhs(a + h*k3)
        a = a + h / 6.0 * (k1 + 2*k2 + 2*k3 + k4)
        a = max(min(a, 3.0), 1e-4)
        vals[i] = a
        t = ts[i]
    return ts, vals

def make_running(e2_anchor, lam, loops, gamma_mode):
    """Return (e2_of_mu, g_of_mu_factory). gamma_mode in {0, +1, -1}:
    d ln m^2/d ln mu = gamma_mode * 6 e^2(mu)/(16 pi^2)."""
    ts, avals = build_alpha_table(e2_anchor / (4.0 * PI), lam, loops)
    def e2_of(mu):
        t = math.log(max(min(mu, 7.9), 0.051))
        # linear interp
        n = len(ts)
        x = (t - ts[0]) / (ts[1] - ts[0])
        i = max(0, min(n - 2, int(x)))
        w = x - i
        return 4.0 * PI * (avals[i] * (1 - w) + avals[i + 1] * w)
    # g(mu): integrate gamma from lam down once on the same grid
    gfac = [0.0] * len(ts)   # ln(m^2(mu)/m^2(lam))
    t_lam = math.log(lam)
    for i in range(len(ts)):
        # integrate gamma d ln mu from t_lam to ts[i] (trapz on the grid)
        lo, hi = (ts[i], t_lam) if ts[i] < t_lam else (t_lam, ts[i])
        s = 0.0
        m = 60
        for j in range(m):
            ta = lo + (hi - lo) * j / m
            tb = lo + (hi - lo) * (j + 1) / m
            ga = gamma_mode * 6.0 * e2_of(math.exp(ta)) / (16.0 * PI ** 2)
            gb = gamma_mode * 6.0 * e2_of(math.exp(tb)) / (16.0 * PI ** 2)
            s += 0.5 * (ga + gb) * (tb - ta)
        gfac[i] = s if ts[i] > t_lam else -s
    def gln_of(mu):
        t = math.log(max(min(mu, 7.9), 0.051))
        n = len(ts)
        x = (t - ts[0]) / (ts[1] - ts[0])
        i = max(0, min(n - 2, int(x)))
        w = x - i
        return gfac[i] * (1 - w) + gfac[i + 1] * w
    def g_of(mu, g_anchor):
        return g_anchor * math.exp(0.5 * gln_of(mu))
    return e2_of, g_of

# ---------- thermal function (precomputed J_B grid) ----------
_JB_Y2 = [10.0 ** (-6 + 10.5 * i / 1499) for i in range(1500)]
def _jb_exact(y2, n=3000, xmax=45.0):
    h = xmax / n
    tot = 0.0
    for i in range(1, n + 1):
        x = i * h
        w = 1.0 if i < n else 0.5
        en = math.sqrt(x * x + y2)
        if en < 700:
            tot += w * x * x * math.log1p(-math.exp(-en))
    return tot * h
_JB_V = [_jb_exact(y2) for y2 in _JB_Y2]
assert abs(_jb_exact(0.0) + PI ** 4 / 45.0) < 1e-4, "J_B(0) validation fails"

def J_B(y2):
    if y2 <= _JB_Y2[0]:
        return _JB_V[0]
    if y2 >= _JB_Y2[-1]:
        return 0.0
    t = math.log10(y2)
    x = (t + 6.0) / (10.5 / 1499)
    i = max(0, min(1498, int(x)))
    w = x - i
    return _JB_V[i] * (1 - w) + _JB_V[i + 1] * w

def F_T(m, T):
    if T <= 0:
        return 0.0
    return T ** 4 / (2.0 * PI ** 2) * J_B((m / T) ** 2)

# ---------- RG-improved CW per species ----------
def cw_rg(m_of_mu, lam, c_i, nseg=120):
    """(1/64pi^2)[-c m^4(m*) - 2 Int_{m*}^{lam} m^4(mu) dln mu], m* solves
    m* = m(m*) by iteration. m_of_mu returns the mass at scale mu.
    Returns value WITHOUT the n_i dof factor."""
    # self-consistent endpoint
    mstar = m_of_mu(lam)
    for _ in range(8):
        mstar = m_of_mu(max(mstar, 0.052))
    lo, hi = math.log(max(mstar, 0.052)), math.log(lam)
    sgn = 1.0
    if lo > hi:
        lo, hi = hi, lo
        sgn = -1.0
    s = 0.0
    for j in range(nseg):
        ta = lo + (hi - lo) * j / nseg
        tb = lo + (hi - lo) * (j + 1) / nseg
        fa = m_of_mu(math.exp(ta)) ** 4
        fb = m_of_mu(math.exp(tb)) ** 4
        s += 0.5 * (fa + fb) * (tb - ta)
    integ = sgn * s
    return (-c_i * mstar ** 4 - 2.0 * integ) / (64.0 * PI ** 2)

def delta_V(k1, k0, cfg):
    """V_eff(k1) - V_eff(k0), RG-improved Lambda-anchored scheme.
    cfg["lam"] = physical anchor scale; cfg["lam_ct"] = counterterm boundary
    (defaults to the anchor scale -- the MDL matching condition)."""
    e2_of, g_of = cfg["running"]
    lam = cfg["lam"]
    lam_ct = cfg.get("lam_ct", lam)
    reading = cfg["reading"]
    g_anchor = cfg["g_anchor"]
    T = cfg["T"]
    damp = cfg.get("uv_damp", False)
    daisy = cfg.get("daisy", False)
    mu_T_fac = cfg.get("mu_T_fac", 1.0)
    wv_match = cfg.get("match_vec", 1.0)   # P1c matching-constant perturbation
    ws_match = cfg.get("match_sc", 1.0)
    tot = 0.0
    for k, sign in ((k1, +1.0), (k0, -1.0)):
        Z = Zk(k, reading)
        mA = lambda mu, Z=Z: math.sqrt(e2_of(mu) * Z)
        mC = lambda mu, Z=Z: g_of(mu, g_anchor) / math.sqrt(Z)
        wA = 1.0 / (1.0 + (mA(lam) / lam) ** 4) if damp else 1.0
        wC = 1.0 / (1.0 + (mC(lam) / lam) ** 4) if damp else 1.0
        v = 3.0 * wA * wv_match * cw_rg(mA, lam_ct, 5.0 / 6.0) \
            + wC * ws_match * cw_rg(mC, lam_ct, 1.5)
        if T > 0:
            muT = max(mu_T_fac * PI * T, 0.052)
            e2T = e2_of(muT)
            mAT = math.sqrt(e2T * Z)
            mCT = g_of(muT, g_anchor) / math.sqrt(Z)
            if daisy:
                mL = math.sqrt(mAT ** 2 + e2T * T * T / 3.0)
                v += 2.0 * wA * F_T(mAT, T) + wA * F_T(mL, T)
            else:
                v += 3.0 * wA * F_T(mAT, T)
            v += wC * F_T(mCT, T)
        tot += sign * v
    return tot

# ---------- validation: fixed-coupling reduction ----------
print("=== 0. Validations ===")
const_run = (lambda mu: 3.5, lambda mu, g0: g0)
m_test = lambda mu: math.sqrt(3.5 * 2.25)
v_int = cw_rg(m_test, LAM0, 5.0 / 6.0)
m4 = (3.5 * 2.25) ** 2
v_ref = m4 * (math.log(3.5 * 2.25 / LAM0 ** 2) - 5.0 / 6.0) / (64.0 * PI ** 2)
print(f"  fixed-coupling reduction: integral form {v_int:+.6e} vs closed form "
      f"{v_ref:+.6e}  (rel err {abs(v_int-v_ref)/abs(v_ref):.2e})")
assert abs(v_int - v_ref) / abs(v_ref) < 1e-3

results = {"validations": {"JB0": _jb_exact(0.0), "minus_pi4_45": -PI**4/45,
                           "fixed_coupling_rel_err": abs(v_int-v_ref)/abs(v_ref)}}

# central running tables (cache per (anchor, lam, loops, gamma))
_run_cache = {}
def running_for(e2_anchor, lam, loops, gamma_mode):
    key = (e2_anchor, lam, loops, gamma_mode)
    if key not in _run_cache:
        _run_cache[key] = make_running(e2_anchor, lam, loops, gamma_mode)
    return _run_cache[key]

def cfg_make(reading="literal", TG=0.6999, e2a=E2_VILLAIN, g=G_DERIVED,
             loops=2, gamma=0, lam=LAM0, lam_ct=None, daisy=False, T=None,
             uv_damp=False, mu_T_fac=1.0, match_vec=1.0, match_sc=1.0):
    return {"reading": reading, "T": TG if T is None else T,
            "g_anchor": g, "lam": lam, "lam_ct": lam if lam_ct is None else lam_ct,
            "daisy": daisy, "uv_damp": uv_damp, "mu_T_fac": mu_T_fac,
            "match_vec": match_vec, "match_sc": match_sc,
            "running": running_for(e2a, lam, loops, gamma)}

def scan_ks(cfg, kmax=6):
    v = [0.0]
    for k in range(1, kmax + 1):
        v.append(v[-1] + delta_V(k, k - 1, cfg))
    return v

# ---------- 1. central point + factorial core ----------
print("\n=== 1. Verdict table: factorial core (reading x f-conv x anchor x daisy x T) ===")
core = {}
n_in, n_tot = 0, 0
for reading in ("literal", "compact"):
    for TG, fl in ((0.6999, "f=1"), (1.2435, "f=mphi")):
        for e2a, el in ((E2_VILLAIN, "e2=7/2"), (E2_PDG, "e2=PDG")):
            for daisy in (False, True):
                for T, tl in ((TG, "T=TG"), (0.0, "T=0")):
                    cfg = cfg_make(reading=reading, TG=TG, e2a=e2a,
                                   daisy=daisy, T=T)
                    v = scan_ks(cfg)
                    am = v.index(min(v))
                    ok = (am == 0) and v[1] > 0
                    n_tot += 1
                    n_in += ok
                    key = f"{reading}|{fl}|{el}|daisy={daisy}|{tl}"
                    core[key] = {"dV01": v[1], "argmin": am}
                    if not ok or (reading == "literal" and not daisy):
                        print(f"  {key:<48} dV(0->1) = {v[1]:+.3e}  argmin = {am}"
                              f"{'' if ok else '   <-- NOT INWARD'}")
print(f"  core: {n_in}/{n_tot} inward")
results["factorial_core"] = {"table": core, "inward": n_in, "total": n_tot}

# ---------- 2. one-at-a-time scheme probes from the central point ----------
print("\n=== 2. Scheme probes (central: literal, f=1, e2=7/2, g=1.77686, 2-loop, T=TG) ===")
probes = {}
central = cfg_make()
v_c = scan_ks(central)
probes["central"] = {"dV01": v_c[1], "argmin": v_c.index(min(v_c))}
print(f"  central                      dV(0->1) = {v_c[1]:+.3e}  argmin = {v_c.index(min(v_c))}")
plist = [
    ("P1a Lambda_GTE -10% (joint)", dict(lam=LAM0 * 0.9)),
    ("P1a Lambda_GTE +10% (joint)", dict(lam=LAM0 * 1.1)),
    ("P1b ct-boundary /sqrt2",      dict(lam_ct=LAM0 / math.sqrt(2.0))),
    ("P1b ct-boundary *sqrt2",      dict(lam_ct=LAM0 * math.sqrt(2.0))),
    ("P1c match vec+10% sc-10%",    dict(match_vec=1.10, match_sc=0.90)),
    ("P1c match vec-10% sc+10%",    dict(match_vec=0.90, match_sc=1.10)),
    ("P2 1-loop run",    dict(loops=1)),
    ("P2 gamma_m = +",   dict(gamma=+1)),
    ("P2 gamma_m = -",   dict(gamma=-1)),
    ("P4 UV damping",    dict(uv_damp=True)),
    ("P5 mu_T = 2piT",   dict(mu_T_fac=2.0)),
    ("g bracket 1.0",    dict(g=1.0)),
    ("g bracket 0.5",    dict(g=0.5)),
    ("g bracket 0.29",   dict(g=0.29)),
    ("T = 0.2 GeV",      dict(T=0.2)),
    ("T = 0",            dict(T=0.0)),
    ("P4 damp + ct*sqrt2",       dict(uv_damp=True, lam_ct=LAM0 * math.sqrt(2.0))),
    ("P4 damp + Lam_GTE +10%",   dict(uv_damp=True, lam=LAM0 * 1.1)),
    ("P4 damp + Lam_GTE -10%",   dict(uv_damp=True, lam=LAM0 * 0.9)),
    ("P4 damp + T = 0",          dict(uv_damp=True, T=0.0)),
]
all_in = v_c[1] > 0
for name, kw in plist:
    cfg = cfg_make(**kw)
    v = scan_ks(cfg)
    am = v.index(min(v))
    ok = (am == 0) and v[1] > 0
    all_in = all_in and ok
    probes[name] = {"dV01": v[1], "argmin": am}
    print(f"  {name:<28} dV(0->1) = {v[1]:+.3e}  argmin = {am}"
          f"{'' if ok else '   <-- NOT INWARD'}")
results["scheme_probes"] = probes

# critical counterterm boundary (anchor fixed at LAM0): where does the sign flip?
print("\n  P1b critical-boundary finder (anchor fixed e2(2.01) = 7/2):")
crit = {}
for damp in (False, True):
    for T, tl in ((0.6999, "T=TG"), (0.0, "T=0")):
        label = f"{tl}|damp={damp}"
        lo, hi = LAM0, 4.0 * LAM0
        d_lo = delta_V(1, 0, cfg_make(T=T, uv_damp=damp))
        d_hi = delta_V(1, 0, cfg_make(T=T, uv_damp=damp, lam_ct=hi))
        if d_lo > 0 and d_hi < 0:
            for _ in range(48):
                mid = math.sqrt(lo * hi)
                if delta_V(1, 0, cfg_make(T=T, uv_damp=damp, lam_ct=mid)) > 0:
                    lo = mid
                else:
                    hi = mid
            lam_crit = math.sqrt(lo * hi)
            crit[label] = lam_crit
            print(f"    {label}: Lambda_crit = {lam_crit:.3f} GeV = "
                  f"{lam_crit/LAM0:.3f} x Lambda_GTE")
        else:
            crit[label] = None
            print(f"    {label}: no flip in [Lambda_GTE, 4 Lambda_GTE] "
                  f"(d_lo = {d_lo:+.2e}, d_hi = {d_hi:+.2e})")
results["ct_boundary_critical"] = crit

# thermal-only diagnostic (scheme-clean piece of the epoch free energy)
print("\n  Thermal-only (scheme-clean) diagnostic:")
thermal_only = {}
for TG, fl in ((0.6999, "f=1"), (1.2435, "f=mphi")):
    for g in (G_DERIVED, 1.0, 0.5, 0.29):
        cT = cfg_make(TG=TG, g=g)
        c0 = cfg_make(TG=TG, g=g, T=0.0)
        d = delta_V(1, 0, cT) - delta_V(1, 0, c0)
        thermal_only[f"{fl}|g={g}"] = d
        print(f"    {fl:<7} g={g:<8} thermal-only dF(0->1) = {d:+.3e}"
              f"{'' if d > 0 else '   <-- outward thermal'}")
results["thermal_only"] = thermal_only

# ---------- 3. scheme change: R06 decoupling scheme comparison ----------
print("\n=== 3. P3 scheme change: R06 decoupling scheme at the derived couplings ===")
def dV_decoupling(k1, k0, e, g, T, reading, mu_fac, daisy=False):
    def cwv(m, mu):
        return 3.0 * m**4 * (math.log(m*m/(mu*mu)) - 5.0/6.0) / (64.0*PI**2)
    def cws(m, mu):
        return m**4 * (math.log(m*m/(mu*mu)) - 1.5) / (64.0*PI**2)
    Z0, Z1 = Zk(k0, reading), Zk(k1, reading)
    mA0, mA1 = e*math.sqrt(Z0), e*math.sqrt(Z1)
    mc0, mc1 = g/math.sqrt(Z0), g/math.sqrt(Z1)
    muA, muc = mu_fac*mA0, mu_fac*mc0
    d = (cwv(mA1, muA) - cwv(mA0, muA)) + (cws(mc1, muc) - cws(mc0, muc))
    if T > 0:
        d += 3.0*(F_T(mA1, T) - F_T(mA0, T)) + (F_T(mc1, T) - F_T(mc0, T))
    return d

e_der = math.sqrt(E2_VILLAIN)
dec = {}
for mu_fac in (0.5, 1.0, 2.0):
    d = dV_decoupling(1, 0, e_der, G_DERIVED, 0.6999, "literal", mu_fac)
    dec[mu_fac] = d
    print(f"  decoupling scheme mu_fac={mu_fac}: dV(0->1) = {d:+.3e}"
          f"{'' if d > 0 else '   <-- band-edge flip (fixed couplings, R06 artifact)'}")
band_old = max(dec.values()) - min(dec.values())
band_keys = ("central", "P1a Lambda_GTE -10% (joint)", "P1a Lambda_GTE +10% (joint)")
band_new = max(probes[p]["dV01"] for p in band_keys) \
         - min(probes[p]["dV01"] for p in band_keys)
print(f"  scheme agreement at centers: decoupling {dec[1.0]:+.3e} vs RG-improved {v_c[1]:+.3e}")
print(f"  band comparison: old fixed-coupling mu-band width {band_old:.3e}; "
      f"RG-improved matching band width {band_new:.3e}  (ratio {band_old/band_new:.1f}x)")
results["scheme_change"] = {"decoupling_band": dec, "old_band": band_old,
                            "new_band": band_new}

# ---------- 4. eps -> 0 and analytic derivative validation ----------
print("\n=== 4. eps -> 0 validation + analytic derivative ===")
eps_rows = {}
EPS_TRUE = EPS
for eps_test in (1e-3, 1e-2, 1e-1, EPS_TRUE):
    globals()["EPS"] = eps_test
    for T, tl in ((0.6999, "T=TG"), (0.0, "T=0")):
        cfg = cfg_make(T=T)
        d = delta_V(1, 0, cfg)
        eps_rows[f"eps={eps_test:g}|{tl}"] = d
        print(f"  eps = {eps_test:<8g} {tl:<6} dV(0->1) = {d:+.4e}"
              f"  (dV/eps = {d/eps_test:+.3e})")
globals()["EPS"] = EPS_TRUE
# analytic small-eps derivative at T=0, fixed couplings (e2 = 3.5, g = 1.77686):
e2, g2 = E2_VILLAIN, G_DERIVED ** 2
LA = math.log(e2 / LAM0 ** 2) - 5.0 / 6.0
LC = math.log(g2 / LAM0 ** 2) - 1.5
# vector: d/dZ [Z^2 (ln(e2 Z/Lam^2) - 5/6)] at Z=1 = 2 LA + 1
# scalar: d/dZ [Z^-2 (ln(g2/(Z Lam^2)) - 3/2)] at Z=1 = -(2 LC + 1)
dV_dZ = (3.0 * e2 ** 2 * (2.0 * LA + 1.0) - g2 ** 2 * (2.0 * LC + 1.0)) / (64.0 * PI ** 2)
dZ1_deps = 2.0 * (2.0 * PI / 7.0) ** 2
print(f"  analytic T=0 fixed-coupling derivative: dV/deps(0->1) = "
      f"{dV_dZ * dZ1_deps:+.3e}")
# numeric cross-check at FIXED couplings (validates the analytic formula;
# the running-coupling rows above differ by the resummation, as expected)
globals()["EPS"] = 1e-3
cfg_const = {"reading": "literal", "T": 0.0, "g_anchor": G_DERIVED,
             "lam": LAM0, "lam_ct": LAM0,
             "running": (lambda mu: E2_VILLAIN, lambda mu, g0: g0)}
d_const = delta_V(1, 0, cfg_const)
globals()["EPS"] = EPS_TRUE
print(f"  numeric  T=0 fixed-coupling dV/deps(0->1) = {d_const/1e-3:+.3e}  "
      f"(rel dev {abs(d_const/1e-3 - dV_dZ*dZ1_deps)/abs(dV_dZ*dZ1_deps):.2%})")
results["eps_limit"] = {"rows": eps_rows,
                        "analytic_T0_dV_deps": dV_dZ * dZ1_deps,
                        "numeric_T0_fixed_coupling_dV_deps": d_const / 1e-3}

# ---------- 5. runaway probe k <= 50 ----------
print("\n=== 5. Runaway probe (literal, k <= 50, central scheme) ===")
run = {}
for T in (0.6999, 0.2, 0.0):
    cfg = cfg_make(T=T)
    v = scan_ks(cfg, kmax=50)
    am = v.index(min(v))
    run[f"T={T}"] = {"argmin": am, "V50": v[50]}
    print(f"  T={T:5.3f}: argmin(k<=50) = {am}, V(50)-V(0) = {v[50]:+.3e} GeV^4")
results["runaway"] = run

# ---------- verdict ----------
core_ok = (n_in == n_tot)
probe_ok = all(p["dV01"] > 0 and p["argmin"] == 0 for p in probes.values())
run_ok = all(r["argmin"] == 0 for r in run.values())
verdict = core_ok and probe_ok and run_ok
print(f"\nVERDICT INPUT: k* = 0 across factorial core ({n_in}/{n_tot}), all scheme "
      f"probes ({probe_ok}), runaway ({run_ok}) -> {'ROBUST candidate' if verdict else 'NOT uniform'}")
results["verdict"] = {"core_all_inward": core_ok, "probes_all_inward": probe_ok,
                      "runaway_ok": run_ok, "k0_robust_input": bool(verdict)}

import os
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
          "vacuum_selection_rg_improved_direction_results.json"), "w") as fp:
    json.dump(results, fp, indent=1)
print("Saved vacuum_selection_rg_improved_direction_results.json")
signal.alarm(0)
