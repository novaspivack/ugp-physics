#!/usr/bin/env python3
"""
Rank 120-LATTICE32 (full run, no timeout): F_21 → SU(3) deconstruction flow.

Improvements over rank120_lattice32_f21.py:
  - COLD START (all links = identity) for all runs → avoids non-trivial flat connections
  - Extended β range: 0.3, 0.5, 0.7, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0, 10.0
  - Longer thermalization: 2000 sweeps for L=8
  - Creutz-coupling b₀ extraction: g²_C(β) = -log(χ(2,2)) → runs via AF
  - Multi-L: L=8 all β; L=12 β∈{0.5,1.5,2.0,4.0,6.0}; L=16 β∈{4.0,6.0}

F_21 trivial-center physics:
  - Z(F_21) = {identity} → no center symmetry → no topological confinement
  - At high β, cold start → all links ≈ identity → plaquette → 1, Polyakov → 1
  - Expected: σ(β) strictly decreasing with β; σ → 0 as β → ∞ (AF + trivial center)
  - Phase transition at β_c ≈ 1.5 (first-order: disordered→Higgs)
"""

import numpy as np
import json
import sys
import time

OUTPUT_FILE = "rank120_lattice32_f21_full_results.json"

t_start = time.time()
results_data: dict = {"runs": [], "partial": False, "f21_algebra": {}}


def _save() -> None:
    with open(OUTPUT_FILE, "w") as fh:
        json.dump(results_data, fh, indent=2)
    print(f"  [saved {OUTPUT_FILE}]", flush=True)


# ─────────────────────────────────────────────────────────────────────────────
# F_21 = Z_7 ⋊ Z_3 algebra (identical to rank120 script)
# ─────────────────────────────────────────────────────────────────────────────

_P2 = [1, 2, 4]   # 2^k mod 7

MUL = np.empty((21, 21), dtype=np.int32)
for _k1 in range(3):
    for _j1 in range(7):
        _i1 = _j1 + 7 * _k1
        for _k2 in range(3):
            for _j2 in range(7):
                _i2 = _j2 + 7 * _k2
                MUL[_i1, _i2] = (_j1 + _P2[_k1] * _j2) % 7 + 7 * ((_k1 + _k2) % 3)

_IP2 = [1, 4, 2]   # (2^k)^{-1} mod 7
INV = np.empty(21, dtype=np.int32)
for _k in range(3):
    for _j in range(7):
        _idx = _j + 7 * _k
        INV[_idx] = (-_IP2[_k] * _j) % 7 + 7 * ((-_k) % 3)

assert all(MUL[i, INV[i]] == 0 for i in range(21))
assert all(MUL[INV[i], i] == 0 for i in range(21))

TRACE = np.zeros(21, dtype=np.float64)
for _k in range(3):
    for _j in range(7):
        _idx = _j + 7 * _k
        TRACE[_idx] = 3.0 if (_j == 0 and _k == 0) else (-0.5 if _k == 0 else 0.0)

assert abs(np.mean(TRACE)) < 1e-12

TRACE_CONTRIB = TRACE[MUL]   # (21, 21): TRACE_CONTRIB[g, s] = Re[Tr(ρ(g·s))]

results_data["f21_algebra"] = {
    "group_order": 21,
    "trace_values": sorted({float(x) for x in TRACE}),
    "group_avg_trace": float(np.mean(TRACE)),
    "center": "trivial (Z(F_21)={identity})",
    "expected_phase": "Higgs/deconfined for β>β_c; deconfinement by trivial center",
}
print("F_21 algebra: OK")
print(f"  Center: trivial → no Z_N confinement, theory in Higgs phase at large β")


# ─────────────────────────────────────────────────────────────────────────────
# Lattice operations
# ─────────────────────────────────────────────────────────────────────────────

def init_cold(L: int) -> np.ndarray:
    """Cold start: all links = identity (index 0)."""
    return np.zeros((L, L, L, L, 4), dtype=np.int32)


def init_hot(L: int, rng) -> np.ndarray:
    return rng.integers(0, 21, size=(L, L, L, L, 4), dtype=np.int32)


def one_heatbath_sweep(links: np.ndarray, beta: float, rng,
                        par: np.ndarray) -> None:
    """Full heat-bath sweep; par is precomputed parity grid."""
    bf3 = beta / 3.0
    L   = links.shape[0]

    for mu in range(4):
        for parity in range(2):
            x, y, z, t = np.where(par == parity)
            N = len(x)
            staples = np.empty((N, 6), dtype=np.int32)
            si = 0

            for nu in range(4):
                if nu == mu:
                    continue
                dmu = [int(mu == d) for d in range(4)]
                dnu = [int(nu == d) for d in range(4)]

                xpm = (x + dmu[0]) % L; ypm = (y + dmu[1]) % L
                zpm = (z + dmu[2]) % L; tpm = (t + dmu[3]) % L
                xpn = (x + dnu[0]) % L; ypn = (y + dnu[1]) % L
                zpn = (z + dnu[2]) % L; tpn = (t + dnu[3]) % L
                xmn = (x - dnu[0]) % L; ymn = (y - dnu[1]) % L
                zmn = (z - dnu[2]) % L; tmn = (t - dnu[3]) % L
                xpmn = (xpm - dnu[0]) % L; ypmn = (ypm - dnu[1]) % L
                zpmn = (zpm - dnu[2]) % L; tpmn = (tpm - dnu[3]) % L

                U_pmu_nu     = links[xpm, ypm, zpm, tpm, nu]
                U_pnu_mu     = links[xpn, ypn, zpn, tpn, mu]
                U_nu         = links[x,   y,   z,   t,   nu]
                U_pmu_mnu_nu = links[xpmn, ypmn, zpmn, tpmn, nu]
                U_mnu_mu     = links[xmn, ymn, zmn, tmn, mu]
                U_mnu_nu     = links[xmn, ymn, zmn, tmn, nu]

                sf = MUL[MUL[U_pmu_nu, INV[U_pnu_mu]], INV[U_nu]]
                sb = MUL[MUL[INV[U_pmu_mnu_nu], INV[U_mnu_mu]], U_mnu_nu]
                staples[:, si]     = sf
                staples[:, si + 1] = sb
                si += 2

            log_w = np.zeros((N, 21), dtype=np.float64)
            for i in range(6):
                log_w += TRACE_CONTRIB[:, staples[:, i]].T
            log_w *= bf3
            log_w -= log_w.max(axis=1, keepdims=True)
            w = np.exp(log_w)
            w /= w.sum(axis=1, keepdims=True)
            cdf = np.cumsum(w, axis=1)
            r = rng.random((N, 1))
            new_v = (cdf < r).sum(axis=1).clip(0, 20).astype(np.int32)
            links[x, y, z, t, mu] = new_v


def make_parity(L: int) -> np.ndarray:
    xi = np.arange(L)
    xg, yg, zg, tg = np.meshgrid(xi, xi, xi, xi, indexing="ij")
    return (xg + yg + zg + tg) % 2


def measure_plaquette(links: np.ndarray) -> float:
    L = links.shape[0]
    total = 0.0
    n = 0
    for mu in range(4):
        for nu in range(mu + 1, 4):
            Um   = links[..., mu]
            Un   = links[..., nu]
            UPmn = np.roll(links[..., nu], -1, axis=mu)
            UPnm = np.roll(links[..., mu], -1, axis=nu)
            p = MUL[MUL[MUL[Um, UPmn], INV[UPnm]], INV[Un]]
            total += float(np.sum(TRACE[p]))
            n += L ** 4
    return total / (n * 3.0)


def measure_polyakov(links: np.ndarray) -> tuple:
    L = links.shape[0]
    P = np.zeros((L, L, L), dtype=np.int32)
    for tt in range(L):
        P = MUL[P, links[:, :, :, tt, 3]]
    tr = TRACE[P] / 3.0
    return float(abs(np.mean(tr))), float(np.real(np.mean(tr)))


def wilson_mu_nu(links: np.ndarray, mu: int, nu: int, R: int, T: int) -> float:
    bot = np.zeros(links.shape[:4], dtype=np.int32)
    for r in range(R):
        bot = MUL[bot, np.roll(links[..., mu], -r, axis=mu)]
    right = np.zeros_like(bot)
    for ts in range(T):
        lnk = np.roll(np.roll(links[..., nu], -R, axis=mu), -ts, axis=nu)
        right = MUL[right, lnk]
    top_f = np.zeros_like(bot)
    for r in range(R):
        top_f = MUL[top_f, np.roll(np.roll(links[..., mu], -r, axis=mu), -T, axis=nu)]
    top = INV[top_f]
    left_f = np.zeros_like(bot)
    for ts in range(T):
        left_f = MUL[left_f, np.roll(links[..., nu], -ts, axis=nu)]
    left = INV[left_f]
    loop = MUL[MUL[MUL[bot, right], top], left]
    return float(np.mean(TRACE[loop])) / 3.0


def measure_all_wilson(links: np.ndarray, R_max: int = 3) -> dict:
    W: dict = {}
    for R in range(1, R_max + 1):
        for T in range(1, R_max + 1):
            vals = [wilson_mu_nu(links, mu, 3, R, T) for mu in range(3)]
            W[f"W_{R}_{T}"] = float(np.mean(vals))
    return W


def creutz_ratios(W: dict) -> dict:
    chi: dict = {}
    for R in range(2, 4):
        wRR   = W.get(f"W_{R}_{R}")
        wR1R1 = W.get(f"W_{R-1}_{R-1}")
        wRR1  = W.get(f"W_{R}_{R-1}")
        wR1R  = W.get(f"W_{R-1}_{R}")
        if None in (wRR, wR1R1, wRR1, wR1R):
            continue
        denom = wRR1 * wR1R
        if abs(denom) < 1e-14:
            chi[f"chi_{R}_{R}"] = None
            chi[f"sigma_{R}_{R}"] = None
            continue
        c = (wRR * wR1R1) / denom
        chi[f"chi_{R}_{R}"] = float(c)
        chi[f"sigma_{R}_{R}"] = float(-np.log(c)) if c > 1e-14 else None
    return chi


# ─────────────────────────────────────────────────────────────────────────────
# Run configurations (cold start, extended β, longer therm)
# ─────────────────────────────────────────────────────────────────────────────

RUNS = []

# L=8: full β sweep (cold start) — backbone of the analysis
for beta in [0.3, 0.5, 0.7, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0, 10.0]:
    RUNS.append({"L": 8,  "beta": beta, "n_therm": 2000, "n_meas": 3000, "start": "cold"})

# L=12: key β values (cold start) — finite-size scaling / multi-L agreement
for beta in [0.5, 1.5, 2.0, 4.0, 6.0]:
    RUNS.append({"L": 12, "beta": beta, "n_therm": 1000, "n_meas": 1500, "start": "cold"})

# L=16: weak-coupling regime (cold start)
for beta in [4.0, 6.0]:
    RUNS.append({"L": 16, "beta": beta, "n_therm": 500,  "n_meas": 800,  "start": "cold"})

MEAS_INTERVAL   = 10    # plaquette / Polyakov every 10 sweeps
WILSON_INTERVAL = 50    # Wilson loops every 50 sweeps (more expensive)

rng          = np.random.default_rng(1337)
parity_cache: dict = {}


def get_parity(L: int) -> np.ndarray:
    if L not in parity_cache:
        parity_cache[L] = make_parity(L)
    return parity_cache[L]


print(f"\nTotal runs: {len(RUNS)}", flush=True)

for run_cfg in RUNS:
    L    = run_cfg["L"]
    beta = run_cfg["beta"]
    nth  = run_cfg["n_therm"]
    nms  = run_cfg["n_meas"]
    cold = run_cfg["start"] == "cold"

    t_run = time.time()
    print(f"\nRun L={L:2d}  β={beta:5.1f}  therm={nth}  meas={nms}  start={'cold' if cold else 'hot'}",
          flush=True)

    links = init_cold(L) if cold else init_hot(L, rng)
    par   = get_parity(L)

    # Thermalization
    for sw in range(nth):
        one_heatbath_sweep(links, beta, rng, par)
        if sw % 500 == 499:
            p = measure_plaquette(links)
            print(f"  therm {sw+1}/{nth}: plaq={p:.4f}", flush=True)

    # Measurement sweeps
    plaq_list: list = []
    poly_list: list = []
    poly_re_list: list = []
    W_acc: dict = {f"W_{R}_{T}": [] for R in range(1, 4) for T in range(1, 4)}

    for sw in range(nms):
        one_heatbath_sweep(links, beta, rng, par)

        if sw % MEAS_INTERVAL == 0:
            plaq_list.append(measure_plaquette(links))
            pabs, pre = measure_polyakov(links)
            poly_list.append(pabs)
            poly_re_list.append(pre)

        if sw % WILSON_INTERVAL == 0:
            Wm = measure_all_wilson(links, R_max=3)
            for k, v in Wm.items():
                W_acc[k].append(v)

    plaq_avg = float(np.mean(plaq_list))   if plaq_list else None
    plaq_err = float(np.std(plaq_list) / np.sqrt(max(1, len(plaq_list) - 1))) if len(plaq_list) > 1 else None
    poly_avg = float(np.mean(poly_list))   if poly_list else None
    poly_re  = float(np.mean(poly_re_list)) if poly_re_list else None
    W_avg    = {k: float(np.mean(v)) if v else None for k, v in W_acc.items()}
    chi      = creutz_ratios(W_avg)

    elapsed = time.time() - t_run
    chi22   = chi.get("chi_2_2")
    sigma22 = chi.get("sigma_2_2")
    chi22_s   = f"{chi22:.5f}" if chi22 is not None else "N/A"
    sigma22_s = f"{sigma22:.5f}" if sigma22 is not None else "N/A"
    print(f"  → plaq={plaq_avg:.5f}  |P|={poly_avg:.4f}  Re[P]={poly_re:.4f}  "
          f"χ(2,2)={chi22_s}  σ(2,2)={sigma22_s}  t={elapsed:.1f}s", flush=True)

    results_data["runs"].append({
        "L": L, "beta": beta, "n_therm": nth, "n_meas": nms, "start": "cold",
        "plaquette_avg": plaq_avg, "plaquette_err": plaq_err,
        "polyakov_abs": poly_avg, "polyakov_re": poly_re,
        "wilson_loops": W_avg, "creutz_ratios": chi,
        "elapsed_s": float(elapsed),
        "n_plaq_samples": len(plaq_list),
        "n_wilson_samples": len(W_acc.get("W_1_1", [])),
    })
    _save()


# ─────────────────────────────────────────────────────────────────────────────
# Analysis: β-function via Creutz-coupling step scaling
# ─────────────────────────────────────────────────────────────────────────────

print("\n=== Creutz-coupling b₀ extraction ===", flush=True)

l8 = {r["beta"]: r for r in results_data["runs"] if r["L"] == 8}

# g²_C(β) = σ(2,2)(β) = -log(χ(2,2))
# For asymptotic freedom: g²_C should decrease as β increases (string tension → 0)
# b₀_eff = -8π² × dg²_C/d(log β) / g⁴_C

b0_creutz: list = []
betas_sorted = sorted(l8.keys())
for i in range(len(betas_sorted) - 1):
    b1, b2 = betas_sorted[i], betas_sorted[i + 1]
    if b1 not in l8 or b2 not in l8:
        continue
    s1 = l8[b1].get("creutz_ratios", {}).get("sigma_2_2")
    s2 = l8[b2].get("creutz_ratios", {}).get("sigma_2_2")
    if s1 is None or s2 is None or s1 <= 0 or s2 <= 0:
        continue
    g2_1, g2_2 = s1, s2
    dg2   = g2_2 - g2_1
    dlogb = float(np.log(b2 / b1))
    g2m   = 0.5 * (g2_1 + g2_2)
    b0e   = -8.0 * np.pi**2 * (dg2 / dlogb) / g2m**2
    b0_creutz.append({
        "beta_pair": [b1, b2],
        "sigma_1": g2_1, "sigma_2": g2_2,
        "b0_Creutz": float(b0e),
        "dg2_dlogbeta": float(dg2 / dlogb),
    })
    print(f"  β={b1}→{b2}: σ={g2_1:.5f}→{g2_2:.5f}  "
          f"dσ/d(log β)={dg2/dlogb:.5f}  b₀_Creutz={b0e:.2f}", flush=True)

results_data["beta_function"] = {
    "b0_creutz_estimates": b0_creutz,
    "b0_analytic": 7.0,
    "note": (
        "Creutz coupling g²_C = σ(2,2) = -log(χ(2,2)). "
        "b₀_Creutz = -8π² × d(g²_C)/d(log β) / g⁴_C. "
        "At large β: g²_C → 0 and b₀_Creutz should approach the renormalized b₀. "
        "Bare coupling: g²_bare=1/β gives b₀=8π²β (expected ≫7; see lab notes)."
    ),
}

# ─────────────────────────────────────────────────────────────────────────────
# ROBUST criteria evaluation
# ─────────────────────────────────────────────────────────────────────────────

print("\n=== ROBUST criteria ===", flush=True)

l12 = {r["beta"]: r for r in results_data["runs"] if r["L"] == 12}
l16 = {r["beta"]: r for r in results_data["runs"] if r["L"] == 16}

robust: dict = {}

# C1: σ > 0 at strong coupling (β < β_c ≈ 1.5)
# Use β=0.5 (confirmed below phase transition at β_c≈1.5)
r05 = l8.get(0.5, {})
s22_05 = r05.get("creutz_ratios", {}).get("sigma_2_2")
c22_05 = r05.get("creutz_ratios", {}).get("chi_2_2")
c1_pass = (s22_05 is not None and s22_05 > 0)
robust["C1_sigma_gt0_strong_coupling"] = {
    "pass": c1_pass,
    "beta": 0.5,
    "chi_2_2": c22_05,
    "sigma_2_2": s22_05,
    "plaquette": r05.get("plaquette_avg"),
}
print(f"  C1 σ>0 at β=0.5: {'✅ PASS' if c1_pass else '❌ FAIL'}  "
      f"σ(2,2)={s22_05}  plaq={r05.get('plaquette_avg','?'):.4f}", flush=True)

# C2: σ → 0 at weak coupling (β ≥ 4.0, threshold |σ| < 0.10)
# With cold start and trivial center, the Higgs phase gives σ≈0 at weak coupling
r60 = l8.get(6.0, {})
s22_60 = r60.get("creutz_ratios", {}).get("sigma_2_2")
c22_60 = r60.get("creutz_ratios", {}).get("chi_2_2")
# Tighter threshold than before: σ < 0.10 (if Higgs phase is properly found)
c2_pass = (s22_60 is not None and abs(s22_60) < 0.10)
# Fallback: if σ still > 0.10 but < 0.30, note it; if < 0.30 and monotone, still provisional
c2_pass_loose = (s22_60 is not None and abs(s22_60) < 0.30)
robust["C2_sigma_0_weak_coupling"] = {
    "pass": c2_pass,
    "pass_loose": c2_pass_loose,
    "beta": 6.0,
    "chi_2_2": c22_60,
    "sigma_2_2": s22_60,
    "threshold_tight": 0.10,
    "threshold_loose": 0.30,
}
print(f"  C2 σ→0 at β=6.0: {'✅ PASS' if c2_pass else '❌ FAIL (tight)'}  "
      f"{'⚠ PASS_LOOSE' if c2_pass_loose and not c2_pass else ''}  "
      f"σ(2,2)={s22_60}", flush=True)

# C3: Plaquette monotone increasing AND b₀ sign > 0 (asymptotic freedom)
plaq_betas = sorted(l8.keys())
plaq_vals  = [l8[b].get("plaquette_avg") for b in plaq_betas]
monotone   = all(
    plaq_vals[i] is not None and plaq_vals[i+1] is not None
    and plaq_vals[i+1] >= plaq_vals[i] - 1e-4   # 1e-4 tolerance for noise
    for i in range(len(plaq_vals) - 1)
)
sigma_decreasing = all(
    (l8[plaq_betas[i]].get("creutz_ratios", {}).get("sigma_2_2") is None
     or l8[plaq_betas[i+1]].get("creutz_ratios", {}).get("sigma_2_2") is None
     or (l8[plaq_betas[i]].get("creutz_ratios", {}).get("sigma_2_2", 0) >=
         l8[plaq_betas[i+1]].get("creutz_ratios", {}).get("sigma_2_2", 0) - 0.02))
    for i in range(len(plaq_betas) - 1)
)
c3_pass = monotone and sigma_decreasing
robust["C3_AF_ordering"] = {
    "pass": c3_pass,
    "plaquette_monotone": monotone,
    "string_tension_decreasing": sigma_decreasing,
    "plaquette_table": {str(b): v for b, v in zip(plaq_betas, plaq_vals)},
}
print(f"  C3 AF ordering (plaq mono + σ decr): {'✅ PASS' if c3_pass else '❌ FAIL'}  "
      f"mono={monotone}  σ_decr={sigma_decreasing}", flush=True)

# C4: Multi-L plaquette agreement within 5% at same β
multi_l: list = []
for b in sorted(set(l8.keys()) & set(l12.keys())):
    p8  = l8[b].get("plaquette_avg")
    p12 = l12[b].get("plaquette_avg")
    if p8 is not None and p12 is not None and abs(p8) > 1e-6:
        diff = abs(p8 - p12) / abs(p8)
        multi_l.append({"beta": b, "L8": p8, "L12": p12,
                         "diff_frac": float(diff), "pass": diff < 0.05})
c4_pass = bool(multi_l) and all(c["pass"] for c in multi_l)
robust["C4_multi_L_agreement"] = {
    "pass": c4_pass, "checks": multi_l, "threshold": 0.05,
}
print(f"  C4 Multi-L (L=8 vs 12, 5%): {'✅ PASS' if c4_pass else '❌ FAIL'}  "
      f"({len(multi_l)} β checked)", flush=True)

# C5: FSS — χ(2,2) L-independent at β=0.5 (confined phase, string tension universal)
chi22_l8  = l8.get(0.5, {}).get("creutz_ratios", {}).get("chi_2_2")
chi22_l12 = l12.get(0.5, {}).get("creutz_ratios", {}).get("chi_2_2")
if chi22_l8 is not None and chi22_l12 is not None and abs(chi22_l8) > 1e-12:
    spread  = abs(chi22_l8 - chi22_l12) / abs(chi22_l8)
    c5_pass = spread < 0.20
    robust["C5_FSS"] = {
        "pass": c5_pass, "chi_2_2_L8": chi22_l8, "chi_2_2_L12": chi22_l12,
        "spread_frac": float(spread), "threshold": 0.20,
    }
    print(f"  C5 FSS χ(2,2) at β=0.5: {'✅ PASS' if c5_pass else '❌ FAIL'}  "
          f"L8={chi22_l8:.5f}  L12={chi22_l12:.5f}  spread={spread:.3f}", flush=True)
else:
    robust["C5_FSS"] = {
        "pass": False, "note": "L=12 β=0.5 data missing or χ(2,2) undefined",
        "chi_2_2_L8": chi22_l8, "chi_2_2_L12": chi22_l12,
    }
    print("  C5 FSS: ❌ FAIL (data missing or χ undefined)", flush=True)

n_pass  = sum(1 for v in robust.values() if v.get("pass", False))
n_loose = sum(1 for v in robust.values()
              if v.get("pass", False) or v.get("pass_loose", False))
verdict = "ROBUST" if n_pass >= 4 else ("PROVISIONAL" if n_pass >= 3 else "INSUFFICIENT")

results_data["robust_criteria"] = robust
results_data["robust_verdict"]  = {
    "n_pass": n_pass, "n_total": 5,
    "n_pass_with_loose": n_loose,
    "verdict": verdict,
}

print(f"\n  {n_pass}/5 criteria pass → VERDICT: {verdict}", flush=True)

# ─────────────────────────────────────────────────────────────────────────────
# Phase transition analysis
# ─────────────────────────────────────────────────────────────────────────────

print("\n=== Phase transition scan (L=8) ===", flush=True)
for b in plaq_betas:
    r = l8.get(b, {})
    p  = r.get("plaquette_avg", 0.0)
    pl = r.get("polyakov_abs", 0.0)
    pr = r.get("polyakov_re", 0.0)
    s  = r.get("creutz_ratios", {}).get("sigma_2_2")
    c  = r.get("creutz_ratios", {}).get("chi_2_2")
    print(f"  β={b:5.1f}  plaq={p:.5f}  |P|={pl:.4f}  Re[P]={pr:.4f}  "
          f"χ(2,2)={c:.5f if c else 'N/A':>10}  σ={s:.5f if s else 'N/A':>10}")

results_data["total_elapsed_s"] = float(time.time() - t_start)
_save()
print(f"\nTotal elapsed: {time.time()-t_start:.1f}s", flush=True)
print(f"Results → {OUTPUT_FILE}", flush=True)
