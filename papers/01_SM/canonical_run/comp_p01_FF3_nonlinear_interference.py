"""
COMP-P01-FF3: Non-Linear Complex Interference Model (08_SPEC §8)

Tests the mechanism the spec's §8 actually claims: the modulus of a sum of
complex terms produces hierarchical magnitudes through constructive/destructive
interference.  Model:

    z(g)  =  Σᵢ  αᵢ · fᵢ(g),    αᵢ ∈ ℂ,  fᵢ(g) ∈ ℂ.

We fit  |z(g)| = R_g  with z(electron) = 1+0i anchored (absorbs scale + phase
gauge; no residual gauge freedom).  Residuals are the 8 other fermion ratios
(log|z(g)| − log R_g for g ≠ electron).  Parameter count:

    total params   = 2k real   (k complex αᵢ)
    anchor  = 2 real constraints (Re = 1, Im = 0 at electron)
    free params    = 2(k−1)
    observations   = 8 (fermion ratios)

Regime:
    k = 2:  2 free  vs  8 eqs → OVER-DETERMINED by 6 (generically no solution)
    k = 3:  4 free  vs  8 eqs → OVER-DETERMINED by 4
    k = 4:  6 free  vs  8 eqs → OVER-DETERMINED by 2
    k = 5:  8 free  vs  8 eqs → SATURATED (generically local-solvable but the
                                image of α → |z(g)| is a non-linear manifold
                                that may not contain the target point)
    k ≥ 6: UNDER-DETERMINED → generically fits; NOT a structural test.

This parameter-counting shows the NON-LINEAR interference model is MORE
restrictive than the linear UCL (which at DL=4 has 4 params vs 8 eqs → also
overdetermined but LINEAR, so always has an OLS projection).  Cleanly testing
the spec §8 claim therefore means:

  - At DL ≤ 4: does any UGP-structural combination happen to reproduce log R_g
    to 2% despite being overdetermined?  (Would be a structural miracle.)
  - At DL = 5 saturated: does the image manifold pass through the target for
    some UGP-structural feature set?  (Generically yes if features are diverse,
    but requires good optimization.)
  - At DL = 5 null test: do random complex features also fit?  If yes, result
    is density-dominated and not structurally meaningful.

SHA-256 protocol: prediction block sealed before PDG comparison appended.
"""

import json
import math
import hashlib
import random
import datetime
import itertools
import time
import numpy as np
from scipy.optimize import least_squares

# ── Lean-certified UGP constants ──────────────────────────────────────────
PHI = (1 + math.sqrt(5)) / 2
INV_PHI = -1.0 / PHI
K_GEN2 = -PHI / 2
K_L2 = 7.0 / 512.0
K_M = K_GEN2 + K_L2 / 4.0

COEFFS_LEAN = {
    "k_const": -0.15486557,
    "k_L": 0.01969789,
    "k_L2": K_L2,
    "k_gen": PHI * math.cos(math.pi / 10),
    "k_gen2": K_GEN2,
    "k_M": K_M,
    "k_mu_a": 1 / 8,
    "k_mu_b": -3 / 2,
    "k_mu_c": 4 / 3,
}

CHARGED_FERMIONS = [
    ("electron", 1, "lepton",    (1, 73, 823),          0.5109989088),
    ("muon",     2, "lepton",    (9, 42, 1023),         105.6583777),
    ("tau",      3, "lepton",    (5, 275, -65535),      1776.859905),
    ("up",       1, "up_type",   (5, 9, 275),           2.16),
    ("down",     1, "down_type", (9, 5, 42),            4.67),
    ("strange",  2, "down_type", (9, 186, 1023),        93.4),
    ("charm",    2, "up_type",   (5, 275, 65535),       1275.0),
    ("bottom",   3, "down_type", (5, 8191, 65535),      4180.0),
    ("top",      3, "up_type",   (76, 337920, -1),      172760.0),
]


# ── Small helpers (shared with FF, FF2) ────────────────────────────────────
def _mobius_signed(n):
    nn = abs(int(n))
    if nn <= 0: return 0
    if nn == 1: return 1
    factors = {}; k = nn; p = 2
    while p * p <= k:
        while k % p == 0:
            factors[p] = factors.get(p, 0) + 1; k //= p
        p += 1
    if k > 1: factors[k] = factors.get(k, 0) + 1
    for cnt in factors.values():
        if cnt > 1: return 0
    return (-1) ** len(factors)

def _fib(n):
    if n <= 0: return 0
    a, b = 0, 1
    for _ in range(n): a, b = b, a + b
    return a

def _lucas(n):
    if n == 0: return 2
    if n == 1: return 1
    a, b = 2, 1
    for _ in range(n - 1): a, b = b, a + b
    return b


def compute_log_Rg_target():
    electron = CHARGED_FERMIONS[0]
    a_e, b_e, c_e = electron[3]
    L_e = math.log(abs(b_e) / abs(c_e))
    mu_a_e, mu_b_e, mu_c_e = _mobius_signed(a_e), _mobius_signed(b_e), _mobius_signed(c_e)
    logcf_e = (
        COEFFS_LEAN["k_const"] + COEFFS_LEAN["k_L"] * L_e + COEFFS_LEAN["k_L2"] * L_e * L_e
        + COEFFS_LEAN["k_gen"] * 1 + COEFFS_LEAN["k_gen2"] * 1
        + COEFFS_LEAN["k_M"] * (mu_a_e * mu_b_e * mu_c_e)
        + COEFFS_LEAN["k_mu_a"] * mu_a_e + COEFFS_LEAN["k_mu_b"] * mu_b_e + COEFFS_LEAN["k_mu_c"] * mu_c_e
    )
    Cf_e = math.exp(logcf_e)
    Ebase_e = electron[4] / Cf_e

    log_Rg = {}
    vec = []
    for (name, gen, typ, (a, b, c), m) in CHARGED_FERMIONS:
        L = math.log(abs(b) / abs(c))
        mu_a, mu_b, mu_c = _mobius_signed(a), _mobius_signed(b), _mobius_signed(c)
        logcf = (
            COEFFS_LEAN["k_const"] + COEFFS_LEAN["k_L"] * L + COEFFS_LEAN["k_L2"] * L * L
            + COEFFS_LEAN["k_gen"] * gen + COEFFS_LEAN["k_gen2"] * gen * gen
            + COEFFS_LEAN["k_M"] * (mu_a * mu_b * mu_c)
            + COEFFS_LEAN["k_mu_a"] * mu_a + COEFFS_LEAN["k_mu_b"] * mu_b + COEFFS_LEAN["k_mu_c"] * mu_c
        )
        Cf = math.exp(logcf)
        Ebase = m / Cf
        v = math.log(Ebase / Ebase_e)
        log_Rg[name] = {"gen": gen, "type": typ, "Rg": math.exp(v), "log_Rg": v}
        vec.append(v)
    return log_Rg, np.array(vec, dtype=float), Ebase_e


def complex_features(a, b, c, gen, particle_type):
    chi = 1.0 if c < 0 else 0.0
    is_up = 1.0 if particle_type == "up_type" else 0.0
    is_dn = 1.0 if particle_type == "down_type" else 0.0
    is_lep = 1.0 if particle_type == "lepton" else 0.0

    def z5(k): return complex(math.cos(2*math.pi*k*(gen-1)/5.0), math.sin(2*math.pi*k*(gen-1)/5.0))
    pentagon = complex(math.cos(math.pi*(gen-1)/5.0), math.sin(math.pi*(gen-1)/5.0))
    dec = complex(math.cos(math.pi*(gen-1)/10.0), math.sin(math.pi*(gen-1)/10.0))
    z3 = complex(math.cos(2*math.pi*(gen-1)/3.0), math.sin(2*math.pi*(gen-1)/3.0))

    phi_gm1 = PHI ** (gen - 1)
    inv_phi_gm1 = INV_PHI ** (gen - 1)

    return {
        "const_1":           complex(1.0, 0.0),
        "chi_real":          complex(chi, 0.0),
        "sign_c_real":       complex(1.0 if c > 0 else -1.0, 0.0),
        "inv_phi_gm1_real":  complex(inv_phi_gm1, 0.0),
        "zeta5_1g":  z5(1),
        "zeta5_2g":  z5(2),
        "zeta5_3g":  z5(3),
        "zeta5_4g":  z5(4),
        "pentagon_g":  pentagon,
        "zeta10_g":    dec,
        "zeta3_g":   z3,
        "phi_zeta5_g":       complex(phi_gm1, 0.0) * z5(1),
        "phi_pentagon_g":    complex(phi_gm1, 0.0) * pentagon,
        "inv_phi_zeta5_g":   complex(inv_phi_gm1, 0.0) * z5(1),
        "inv_phi_pentagon":  complex(inv_phi_gm1, 0.0) * pentagon,
        "fib_zeta3_g":       complex(_fib(gen), 0.0) * z3,
        "fib_pentagon_g":    complex(_fib(gen), 0.0) * pentagon,
        "lucas_pentagon_g":  complex(_lucas(gen), 0.0) * pentagon,
        "chi_zeta3_g":       complex(chi, 0.0) * z3,
        "chi_pentagon_g":    complex(chi, 0.0) * pentagon,
        "uptype_pentagon_g": complex(is_up, 0.0) * pentagon,
        "leptn_pentagon_g":  complex(is_lep, 0.0) * pentagon,
        "log_c_zeta5_g":     complex(math.log(abs(c)) if c != 0 else 0.0, 0.0) * z5(1),
        "log_b_pentagon_g":  complex(math.log(abs(b)) if b != 0 else 0.0, 0.0) * pentagon,
        "muc_zeta5_g":       complex(_mobius_signed(c), 0.0) * z5(1),
        "gen_zeta5_g":       complex(gen, 0.0) * z5(1),
    }


# ── Anchored non-linear fit ────────────────────────────────────────────────

def anchored_residual_factory(X_c, y_log, anchor_col=0):
    """Residual for |z(g)| = exp(y_log[g]) with z(electron) = 1+0i anchored.
    Column anchor_col of X_c[0, :] is used to solve for α_{anchor_col}.
    Free params: all other α_i → 2(k-1) real numbers.
    Residuals: log|z(g)| - y_log[g] for g = 1..8 (electron skipped).
    """
    N, k = X_c.shape
    X0 = X_c[0, :]
    if abs(X0[anchor_col]) < 1e-14:
        return None  # can't anchor on this column
    anchor_val = X0[anchor_col]
    other = [i for i in range(k) if i != anchor_col]
    X0_other = X0[other]

    def resid(params):
        af = params[:k-1] + 1j * params[k-1:2*(k-1)]
        # Solve anchor: α_anchor = (1 − Σ α_other · X0_other) / X0[anchor]
        alpha_anchor = (1.0 - np.dot(af, X0_other)) / anchor_val
        # Assemble full alpha
        alpha = np.empty(k, dtype=complex)
        alpha[anchor_col] = alpha_anchor
        for idx, i in enumerate(other):
            alpha[i] = af[idx]
        z = X_c @ alpha
        abs_z = np.abs(z)
        safe = np.maximum(abs_z, 1e-14)
        return np.log(safe[1:]) - y_log[1:]

    return resid, anchor_col


def fit_anchored(X_c, y_log, n_restarts=5, seed=0, n_anchors=2):
    """Try multiple anchor columns + restarts; return best (max_frac, alpha, |z|)."""
    N, k = X_c.shape
    best_cost = np.inf
    best_data = None  # (max_frac, alpha, abs_z)

    anchor_order = np.argsort(-np.abs(X_c[0, :]))[:min(n_anchors, k)]
    rng = np.random.default_rng(seed)

    for anchor_col in anchor_order:
        factory = anchored_residual_factory(X_c, y_log, int(anchor_col))
        if factory is None:
            continue
        resid_fn, _ = factory
        n_free = 2 * (k - 1)
        for trial in range(n_restarts):
            # Diverse init strategies
            if trial == 0:
                p0 = np.zeros(n_free)                              # all zero
            elif trial == 1:
                p0 = np.ones(n_free) * 0.1                         # small positive
            else:
                scale = 10 ** rng.uniform(-1.5, 2.5)
                p0 = rng.standard_normal(n_free) * scale
            try:
                res = least_squares(
                    resid_fn, p0, method="lm",
                    max_nfev=600, xtol=1e-10, ftol=1e-10,
                )
            except Exception:
                continue
            if not np.isfinite(res.cost):
                continue
            if res.cost < best_cost:
                # Recover α from res.x
                af = res.x[:k-1] + 1j * res.x[k-1:2*(k-1)]
                X0 = X_c[0, :]
                other = [i for i in range(k) if i != int(anchor_col)]
                alpha_anchor = (1.0 - np.dot(af, X0[other])) / X0[int(anchor_col)]
                alpha = np.empty(k, dtype=complex)
                alpha[int(anchor_col)] = alpha_anchor
                for idx, i in enumerate(other):
                    alpha[i] = af[idx]
                z = X_c @ alpha
                abs_z = np.abs(z)
                diffs = np.log(np.maximum(abs_z, 1e-14)) - y_log
                max_frac = float(np.max(np.abs(np.exp(diffs) - 1.0)))
                best_cost = res.cost
                best_data = (max_frac, alpha.tolist(), abs_z.tolist())

    if best_data is None:
        return 1e9, None, None
    return best_data


# ── Scan ──────────────────────────────────────────────────────────────────

def scan_dl(feats_list, feat_names, k, y_log, n_restarts=10, top_n=15,
            seed_offset=0):
    y = np.asarray(y_log)
    combos = list(itertools.combinations(feat_names, k))
    results = []
    t0 = time.time()
    for ic, combo in enumerate(combos):
        X_c = np.array([[fl[n] for n in combo] for fl in feats_list], dtype=complex)
        # Skip if anchor column all zero at electron
        if np.all(np.abs(X_c[0, :]) < 1e-14):
            continue
        # Skip rank-deficient (check real-flat rank)
        if np.linalg.matrix_rank(np.hstack([X_c.real, X_c.imag])) < min(X_c.shape):
            # Accept rank-limited combos but note it; they may still fit
            pass
        seed = seed_offset + ic * 9973 + k * 104729
        mf, alpha, abs_z = fit_anchored(X_c, y, n_restarts=n_restarts, seed=seed)
        results.append({
            "atoms": list(combo),
            "alpha_real": [a.real for a in alpha] if alpha is not None else None,
            "alpha_imag": [a.imag for a in alpha] if alpha is not None else None,
            "abs_z_per_fermion": abs_z,
            "max_fractional_error": mf,
            "closes_at_2pct": mf <= 0.02,
        })
    t1 = time.time()
    results.sort(key=lambda r: r["max_fractional_error"])
    n_close = sum(1 for r in results if r["closes_at_2pct"])
    # Histogram of max_frac
    hist = {
        "count_le_0.02": sum(1 for r in results if r["max_fractional_error"] <= 0.02),
        "count_le_0.10": sum(1 for r in results if r["max_fractional_error"] <= 0.10),
        "count_le_0.50": sum(1 for r in results if r["max_fractional_error"] <= 0.50),
        "count_le_1.00": sum(1 for r in results if r["max_fractional_error"] <= 1.00),
        "count_le_2.00": sum(1 for r in results if r["max_fractional_error"] <= 2.00),
    }
    return {
        "DL": k,
        "n_combinations": len(combos),
        "n_fitted": len(results),
        "n_closures_at_2pct": n_close,
        "elapsed_seconds": t1 - t0,
        "top_k": results[:top_n],
        "histogram": hist,
    }


# ── Null test at each DL ──────────────────────────────────────────────────

def null_test(n_trials, y_log, k, n_restarts=5, seed=0):
    y = np.asarray(y_log)
    rng = np.random.default_rng(seed + k * 31337)
    hit = 0
    hits = []
    t0 = time.time()
    N = len(y_log)
    for t in range(n_trials):
        phases = rng.uniform(0.0, 2 * math.pi, size=(N, k))
        X_c = np.exp(1j * phases)  # unit-modulus complex features
        mf, alpha, _ = fit_anchored(X_c, y, n_restarts=n_restarts, seed=seed + t)
        if mf <= 0.02:
            hit += 1
            if len(hits) < 5:
                hits.append({"trial": t, "max_fractional_error": mf})
    t1 = time.time()
    return {
        "DL": k, "n_trials": n_trials,
        "hit_count": hit, "hit_rate": hit / n_trials,
        "elapsed_seconds": t1 - t0,
        "sample_hits": hits,
    }


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    timestamp = datetime.datetime.utcnow().isoformat() + "Z"

    log_Rg, y_log_vec, Ebase_e = compute_log_Rg_target()
    feat_list = [complex_features(*f[3], f[1], f[2]) for f in CHARGED_FERMIONS]
    feat_names = list(feat_list[0].keys())

    # Structural scans at DL = 2, 3, 4 (full) + DL = 5 (subset sanity)
    scans = {}
    for k in (2, 3, 4):
        print(f"[scan DL={k}] {math.comb(len(feat_names), k)} combos …", flush=True)
        scans[f"DL_{k}"] = scan_dl(feat_list, feat_names, k, y_log_vec,
                                    n_restarts=5, top_n=15, seed_offset=k*7)
        s = scans[f"DL_{k}"]
        best = s["top_k"][0]
        print(f"  {s['elapsed_seconds']:.1f}s  → {s['n_closures_at_2pct']} close at 2%;"
              f" best mf = {best['max_fractional_error']:.4g} "
              f"(atoms = {best['atoms']})", flush=True)

    # DL=5 saturated: subset scan (first-12 features → C(12,5)=792 combos)
    print(f"[scan DL=5 (saturated, subset)] 792 combos on first 12 features …", flush=True)
    scans["DL_5_subset"] = scan_dl(feat_list, feat_names[:12], 5, y_log_vec,
                                    n_restarts=8, top_n=15, seed_offset=5*7)
    s = scans["DL_5_subset"]
    best = s["top_k"][0]
    print(f"  {s['elapsed_seconds']:.1f}s  → {s['n_closures_at_2pct']} close at 2%;"
          f" best mf = {best['max_fractional_error']:.4g}", flush=True)

    # Null test at DL = 2, 3, 4, 5
    null_by_dl = {}
    for k in (2, 3, 4, 5):
        print(f"[null DL={k}] 500 trials …", flush=True)
        null_by_dl[f"DL_{k}"] = null_test(500, y_log_vec, k, n_restarts=3, seed=20260419)
        r = null_by_dl[f"DL_{k}"]
        print(f"  {r['elapsed_seconds']:.1f}s  → hits {r['hit_count']}/500 "
              f"= {r['hit_rate']:.4f}", flush=True)

    # Prediction block
    prediction_block = {
        "comp_id": "COMP-P01-FF3",
        "title": "Non-linear complex interference model for 08_SPEC §8 (anchored fit)",
        "spec_reference": "specs/IN-PROCESS/EPIC_CLUSTER7_RESEARCH_GRADE/08_SPEC_COMPLEX_GTE_EXTENSION.md §8",
        "prior_art": ["COMP-P01-FF (linear 4.1)", "COMP-P01-FF2 (linear 4.2/4.3 + analytical 4.4)",
                      "COMP-P01-BB", "COMP-P01-AA"],
        "timestamp_utc": timestamp,
        "model": "|z(g)| = |Σ αᵢ fᵢ(g)|; anchor z(electron) = 1+0i; residuals are 8 other fermion log-ratios.",
        "parameter_count_analysis": {
            "total_real_params_at_DLk": "2k",
            "anchor_constraints": 2,
            "free_params_at_DLk": "2(k-1)",
            "observations": 8,
            "regime_by_DL": {
                "2": "OVERDETERMINED by 6 (2 free vs 8 eqs); generically no solution",
                "3": "OVERDETERMINED by 4",
                "4": "OVERDETERMINED by 2",
                "5": "SATURATED (8 vs 8); local-solvable if image manifold reaches target",
                "≥6": "UNDERDETERMINED (density-dominated; not a structural test)",
            },
        },
        "lean_certified_inputs": {
            "phi": PHI, "inv_phi_galois": INV_PHI,
            "k_gen2": K_GEN2, "k_L2": K_L2, "k_M": K_M,
            "k_gen": COEFFS_LEAN["k_gen"],
        },
        "charged_fermions": [{"name": f[0], "gen": f[1], "type": f[2],
                              "triple": list(f[3]), "m_PDG_MeV": f[4]} for f in CHARGED_FERMIONS],
        "log_Rg_targets": log_Rg,
        "log_Rg_vector": y_log_vec.tolist(),
        "complex_feature_library": {
            "n_features": len(feat_names),
            "feature_names": feat_names,
        },
        "scans": {k: {kk: vv for kk, vv in v.items() if kk != "elapsed_seconds"} for k, v in scans.items()},
        "scans_timing_s": {k: v["elapsed_seconds"] for k, v in scans.items()},
        "null_test_by_DL": {k: {kk: vv for kk, vv in v.items() if kk != "elapsed_seconds"} for k, v in null_by_dl.items()},
        "null_timing_s": {k: v["elapsed_seconds"] for k, v in null_by_dl.items()},
    }

    # SHA-256 seal
    pred_json = json.dumps(prediction_block, sort_keys=True, separators=(",", ":"), default=str)
    sha256_pred = hashlib.sha256(pred_json.encode("utf-8")).hexdigest()

    # Verdict
    scan_keys_for_best = ("DL_2", "DL_3", "DL_4", "DL_5_subset")
    any_closure = any(scans[k]["n_closures_at_2pct"] > 0 for k in scan_keys_for_best)
    best = None
    for kk in scan_keys_for_best:
        for r in scans[kk]["top_k"]:
            if best is None or r["max_fractional_error"] < best["max_fractional_error"]:
                best = {"DL_label": kk, **r}

    null_rates = {k: null_by_dl[k]["hit_rate"] for k in null_by_dl}

    # At DL=5 (saturated), the meaningful comparison: structural vs null
    dl5_struct_closures = scans["DL_5_subset"]["n_closures_at_2pct"]
    dl5_null_rate = null_rates["DL_5"]
    dl5_null_disciplined = dl5_null_rate < 0.01

    if any_closure and dl5_null_disciplined:
        verdict = f"CLOSES_structural_beats_null"
    elif any_closure and not dl5_null_disciplined:
        verdict = "CLOSES_but_density_dominated_at_DL5"
    elif not any_closure and not dl5_null_disciplined:
        verdict = "MAP_nonlinear_saturated_trivially_hits_BUT_UGP_structural_does_not_close"
    else:
        verdict = "MAP_nonlinear_interference_insufficient_at_DL_2_to_5"

    pdg_comparison = {
        "prediction_block_sha256": sha256_pred,
        "any_closure_at_DL_2_to_5": any_closure,
        "null_hit_rates": null_rates,
        "dl5_structural_closures": dl5_struct_closures,
        "dl5_null_hit_rate": dl5_null_rate,
        "dl5_null_disciplined": dl5_null_disciplined,
        "verdict": verdict,
        "best_structural_candidate": best,
    }

    output = {
        "prediction_block_precomparison": prediction_block,
        "sha256_prediction_block": sha256_pred,
        "pdg_comparison": pdg_comparison,
    }

    # Summary print
    print()
    print("=" * 72)
    print(f"COMP-P01-FF3: Non-linear complex interference (anchored)")
    print(f"Prediction block SHA-256: {sha256_pred}")
    print()
    print(f"Parameter regime by DL:")
    print(f"  DL=2: 2 free / 8 eqs - overdetermined by 6")
    print(f"  DL=3: 4 free / 8 eqs - overdetermined by 4")
    print(f"  DL=4: 6 free / 8 eqs - overdetermined by 2")
    print(f"  DL=5: 8 free / 8 eqs - saturated")
    print()
    print(f"Feature library: {len(feat_names)} complex UGP-structural features")
    print()
    print("Structural scan (max_frac_err histogram):")
    for k in ("DL_2", "DL_3", "DL_4", "DL_5_subset"):
        s = scans[k]
        h = s["histogram"]
        b = s["top_k"][0]
        print(f"  {k}: {s['n_combinations']:>6d} combos  best={b['max_fractional_error']:.4g}  "
              f"[<0.02: {h['count_le_0.02']}, <0.10: {h['count_le_0.10']}, "
              f"<0.50: {h['count_le_0.50']}, <1.0: {h['count_le_1.00']}]")
        print(f"    best atoms: {b['atoms']}")
    print()
    print(f"Null test (500 random-complex-phase trials):")
    for k in ("DL_2", "DL_3", "DL_4", "DL_5"):
        r = null_by_dl[k]
        print(f"  {k}: {r['hit_count']}/500 = {r['hit_rate']:.4f}  "
              f"{'disciplined (<1%)' if r['hit_rate'] < 0.01 else 'DENSITY-DOMINATED'}")
    print()
    print(f"Verdict: {verdict}")
    if best:
        print(f"Best overall: {best['DL_label']}  mf={best['max_fractional_error']:.4g}  "
              f"atoms={best['atoms']}")

    return output


if __name__ == "__main__":
    output = main()
    out_path = "comp_p01_FF3_nonlinear_interference.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2, default=str)
    import subprocess
    r = subprocess.run(
        ["python3", "-c", f"import json; json.load(open('{out_path}')); print('JSON valid')"],
        capture_output=True, text=True
    )
    print()
    print(f"Output written to {out_path}")
    print(r.stdout.strip() if r.returncode == 0 else f"JSON ERROR: {r.stderr}")
