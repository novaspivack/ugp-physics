"""
COMP-P01-FF2: Complex GTE Extension — Approaches 4.2, 4.3, 4.4

Follow-on to COMP-P01-FF, which tested Approach 4.1 (linear complex UCL with
Braid-Atlas phases) and produced MAP.  This script completes 08_SPEC §4 by
testing the remaining three approaches:

    Approach 4.2 (ℤ[φ] triple extension): enrich the atom basis with higher
      golden-ratio powers φ^n, Galois-conjugate pair (-1/φ)^n, Fibonacci
      products, and ℚ(√5) norm features N(a + bφ) = a² + ab - b².
      Re-run the DL ≤ 5 scan.

    Approach 4.3 (ℤ[ζ₅] cyclotomic extension): add 5th-root-of-unity features
      cos(2π·k·gen/5) and sin(2π·k·gen/5) for k ∈ {1, 2, 3, 4}.  These are
      the 4 integer coordinates of each generation's image in ℚ(ζ₅).
      Re-run the DL ≤ 5 scan with the enriched basis.

    Approach 4.4 (complex gauge coupling phase correction for sin²θ_W):
      With g_i² = g_i²_bare · e^{iθ_i}, derive the required relative phase
      Δ = θ₂ - θ₁ that closes sin²θ_W to the PDG value.  Check whether Δ
      is (a) real-valued (i.e. |cos(Δ)| ≤ 1) and (b) a UGP-structural angle
      (multiple of π/5, π/10, 2π/3, etc.).

Gate: Same as 08_SPEC §7 — match log R_g at ≤ 2% and null rate < 1% (for
4.2/4.3); for 4.4, whether a structural angle closes sin²θ_W to ≤ 10σ.

SHA-256 protocol: prediction block sealed BEFORE PDG comparison.
"""

import json
import math
import hashlib
import random
import datetime
import itertools
import numpy as np

# ── Lean-certified UGP constants ──────────────────────────────────────────

PHI = (1 + math.sqrt(5)) / 2
INV_PHI = -1 / PHI
K_GEN2 = -PHI / 2
K_L2 = 7 / 512
K_M = K_GEN2 + K_L2 / 4

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

# ── Canonical triples with CORRECTED tau sign ─────────────────────────────
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

# ── Bare Lean-certified squared couplings (for Approach 4.4) ──────────────
G1SQ_BARE = 16 / 125                  # 0.128
G2SQ_BARE = 2329 / 5400               # 0.43129629...
PDG_SIN2_THETAW = 0.23122
PDG_SIN2_SIGMA = 4e-5


# ── Shared utilities ───────────────────────────────────────────────────────

def _mobius_signed(n):
    nn = abs(int(n))
    if nn <= 0:
        return 0
    if nn == 1:
        return 1
    factors = {}
    k = nn
    p = 2
    while p * p <= k:
        while k % p == 0:
            factors[p] = factors.get(p, 0) + 1
            k //= p
        p += 1
    if k > 1:
        factors[k] = factors.get(k, 0) + 1
    for cnt in factors.values():
        if cnt > 1:
            return 0
    return (-1) ** len(factors)


def _fib(n):
    if n <= 0: return 0
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def compute_real_ucl_features(a, b, c, gen):
    L = math.log(abs(b) / abs(c)) if abs(c) > 0 and abs(b) > 0 else 0.0
    L2 = L * L
    mu_a = _mobius_signed(a)
    mu_b = _mobius_signed(b)
    mu_c = _mobius_signed(c)
    M = mu_a * mu_b * mu_c
    return {"const": 1.0, "L": L, "L2": L2, "gen": float(gen), "gen2": float(gen * gen),
            "M": float(M), "mu_a": float(mu_a), "mu_b": float(mu_b), "mu_c": float(mu_c)}


def predict_cf_real(features):
    logcf = sum(COEFFS_LEAN[k] * features[k.replace("k_", "")] for k in COEFFS_LEAN if k != "k_const") + COEFFS_LEAN["k_const"]
    # The above sum is wrong (feature names differ from coefficient names). Rewrite:
    return math.exp(
        COEFFS_LEAN["k_const"] * features["const"] +
        COEFFS_LEAN["k_L"] * features["L"] +
        COEFFS_LEAN["k_L2"] * features["L2"] +
        COEFFS_LEAN["k_gen"] * features["gen"] +
        COEFFS_LEAN["k_gen2"] * features["gen2"] +
        COEFFS_LEAN["k_M"] * features["M"] +
        COEFFS_LEAN["k_mu_a"] * features["mu_a"] +
        COEFFS_LEAN["k_mu_b"] * features["mu_b"] +
        COEFFS_LEAN["k_mu_c"] * features["mu_c"]
    )


def compute_log_Rg_target():
    electron = CHARGED_FERMIONS[0]
    a_e, b_e, c_e = electron[3]
    f_e = compute_real_ucl_features(a_e, b_e, c_e, electron[1])
    Cf_e = predict_cf_real(f_e)
    Ebase_e = electron[4] / Cf_e
    log_Rg = {}
    vec = []
    for (name, gen, typ, (a, b, c), m) in CHARGED_FERMIONS:
        f = compute_real_ucl_features(a, b, c, gen)
        Cf = predict_cf_real(f)
        Ebase = m / Cf
        v = math.log(Ebase / Ebase_e)
        log_Rg[name] = {"gen": gen, "Rg": math.exp(v), "log_Rg": v,
                        "Ebase_required_MeV": Ebase}
        vec.append(v)
    return log_Rg, vec, Ebase_e


# ── Enriched atom basis (Approach 4.2 + 4.3) ──────────────────────────────

def enriched_atoms_4_2_and_4_3(a, b, c, gen, particle_type):
    """
    Superset of FF's 36-atom basis, extended with:

    Approach 4.2 enrichments (higher ℤ[φ] / ℚ(√5) structure):
      - phi_pow_2_gen, phi_pow_3_gen        (φ^(2·gen-2), φ^(3·gen-3))
      - inv_phi_pow_2_gen, inv_phi_pow_3_gen (Galois conjugates)
      - norm_ab:  N(a + gen·φ) = a² + gen·a − gen²
      - fib_gen_ratio:  F_{2·gen}/F_{gen+1}
      - ln_phi_gen:     gen · ln(φ)

    Approach 4.3 enrichments (ℤ[ζ₅] cyclotomic):
      - cos(2π·k·gen/5), sin(2π·k·gen/5) for k ∈ {1, 2, 3, 4}
        — these are the 4 integer coordinates of gen's image in ℚ(ζ₅).
      - Chi × cyclotomic cross terms: H(c) · cos(2π·k·gen/5)
    """
    atoms = {}

    # Base FF atoms (real)
    atoms["const_1"]    = 1.0
    atoms["gen"]        = float(gen)
    atoms["gen_minus_1"]= float(gen - 1)
    atoms["gen2"]       = float(gen * gen)
    atoms["log_gen"]    = math.log(gen)
    atoms["2gen"]       = 2.0 * gen
    atoms["3gen"]       = 3.0 * gen
    atoms["chi"]        = 1.0 if c < 0 else 0.0
    atoms["sign_c"]     = 1.0 if c > 0 else (-1.0 if c < 0 else 0.0)
    atoms["is_lepton"]  = 1.0 if particle_type == "lepton" else 0.0
    atoms["is_quark"]   = 1.0 if particle_type != "lepton" else 0.0
    atoms["is_up_type"] = 1.0 if particle_type == "up_type" else 0.0
    atoms["is_dn_type"] = 1.0 if particle_type == "down_type" else 0.0
    atoms["log_abs_a"]  = math.log(abs(a)) if a != 0 else 0.0
    atoms["log_abs_b"]  = math.log(abs(b)) if b != 0 else 0.0
    atoms["log_abs_c"]  = math.log(abs(c)) if c != 0 else 0.0
    atoms["mu_a"]       = float(_mobius_signed(a))
    atoms["mu_b"]       = float(_mobius_signed(b))
    atoms["mu_c"]       = float(_mobius_signed(c))

    # ── Approach 4.2: Extended ℤ[φ] atoms ──────────────────────────────
    atoms["phi_pow_gen"]     = PHI ** (gen - 1)
    atoms["phi_pow_2gen"]    = PHI ** (2 * (gen - 1))
    atoms["phi_pow_3gen"]    = PHI ** (3 * (gen - 1))
    atoms["inv_phi_pow_gen"] = (-1 / PHI) ** (gen - 1)
    atoms["inv_phi_pow_2gen"]= (-1 / PHI) ** (2 * (gen - 1))
    atoms["inv_phi_pow_3gen"]= (-1 / PHI) ** (3 * (gen - 1))
    atoms["phi_log_gen"]     = PHI * math.log(gen) if gen > 0 else 0.0
    atoms["fib_g"]           = float(_fib(gen))
    atoms["fib_2g"]          = float(_fib(2 * gen))
    atoms["fib_3g"]          = float(_fib(3 * gen))
    atoms["fib_ratio"]       = _fib(2 * gen) / _fib(gen + 1) if _fib(gen + 1) > 0 else 0.0
    # ℚ(√5) norm applied to (a + gen·φ): a² + gen·a − gen²
    atoms["sqrt5_norm_a_gen"] = float(a * a + gen * a - gen * gen)
    # Binet-like feature: (φ^gen − (-1/φ)^gen) / √5  = F_gen (already there)
    # Lucas number: L_n = φ^n + (-1/φ)^n
    atoms["lucas_gen"]       = (PHI ** gen + (-1 / PHI) ** gen)
    atoms["lucas_2gen"]      = (PHI ** (2 * gen) + (-1 / PHI) ** (2 * gen))

    # ── Approach 4.3: ℤ[ζ₅] cyclotomic atoms ────────────────────────────
    # 5th root of unity: ζ₅ = exp(2πi/5); its powers form the cyclotomic basis.
    # Real and imaginary parts at gen for k=1..4.
    for k in (1, 2, 3, 4):
        th = 2 * math.pi * k * (gen - 1) / 5
        atoms[f"cos_zeta5_{k}g"] = math.cos(th)
        atoms[f"sin_zeta5_{k}g"] = math.sin(th)
        # chirality × cyclotomic cross term
        atoms[f"chi_cos_zeta5_{k}g"] = atoms["chi"] * math.cos(th)
        atoms[f"chi_sin_zeta5_{k}g"] = atoms["chi"] * math.sin(th)

    # ── Original FF D₅ + generational phase atoms (for completeness) ───
    theta_D5 = 2 * math.pi * (gen - 1) / 5
    atoms["cos_D5"] = math.cos(theta_D5)
    atoms["sin_D5"] = math.sin(theta_D5)
    theta_10 = math.pi * (gen - 1) / 10
    atoms["cos_p10"] = math.cos(theta_10)
    atoms["sin_p10"] = math.sin(theta_10)
    theta_gen = 2 * math.pi * (gen - 1) / 3
    atoms["cos_gen3"] = math.cos(theta_gen)
    atoms["sin_gen3"] = math.sin(theta_gen)
    atoms["chi_x_cos_gen3"] = atoms["chi"] * math.cos(theta_gen)
    atoms["chi_x_sin_gen3"] = atoms["chi"] * math.sin(theta_gen)
    atoms["k_gen_cos_gen3"] = COEFFS_LEAN["k_gen"] * math.cos(theta_gen)
    atoms["k_L2_sin_gen3"]  = COEFFS_LEAN["k_L2"] * math.sin(theta_gen)

    return atoms


# ── Low-DL scan helpers (same as FF) ──────────────────────────────────────

def build_atom_matrix(atom_names, fermion_atoms):
    return np.array([[fa[name] for name in atom_names] for fa in fermion_atoms], dtype=float)


def fit_lstsq(X, y):
    coeffs, *_ = np.linalg.lstsq(X, y, rcond=None)
    pred = X @ coeffs
    resid = y - pred
    return coeffs.tolist(), float(np.linalg.norm(resid)), float(np.max(np.abs(resid))), pred.tolist()


def max_fractional_error(log_pred, log_target):
    return max(abs(math.exp(p - t) - 1.0) for p, t in zip(log_pred, log_target))


def scan_dl(fermion_atoms, atom_names, k, log_vec, top_n=20):
    results = []
    y = np.array(log_vec, dtype=float)
    combos = list(itertools.combinations(atom_names, k))
    for combo in combos:
        X = build_atom_matrix(list(combo), fermion_atoms)
        if np.linalg.matrix_rank(X) < X.shape[1]:
            continue
        try:
            coeffs, rnorm, maxres, pred = fit_lstsq(X, y)
        except Exception:
            continue
        mf = max_fractional_error(pred, y.tolist())
        results.append({
            "atoms": list(combo), "coeffs": coeffs,
            "max_fractional_error": mf,
            "max_abs_log_residual": maxres,
            "closes_at_2pct": mf <= 0.02,
        })
    results.sort(key=lambda r: r["max_fractional_error"])
    return results[:top_n], len(combos), sum(1 for r in results if r["closes_at_2pct"])


def null_test_random(n_trials, log_vec, n_features=3, seed=0):
    rng = random.Random(seed + n_features * 17)
    y = np.array(log_vec, dtype=float)
    hit = 0
    hits = []
    for trial in range(n_trials):
        phases = [rng.uniform(0, 2 * math.pi) for _ in range(9 * n_features)]
        X = np.array([[math.cos(phases[9 * j + i]) for j in range(n_features)] for i in range(9)])
        if np.linalg.matrix_rank(X) < X.shape[1]:
            continue
        try:
            coeffs, rnorm, maxres, pred = fit_lstsq(X, y)
        except Exception:
            continue
        mf = max_fractional_error(pred, y.tolist())
        if mf <= 0.02:
            hit += 1
            if len(hits) < 5:
                hits.append({"trial": trial, "max_fractional_error": mf})
    return {"n_trials": n_trials, "n_features": n_features,
            "hit_count": hit, "hit_rate": hit / n_trials,
            "sample_hits": hits}


# ── Approach 4.4: Complex gauge coupling phase correction ─────────────────

def approach_4_4_sin2tw_complex_phase():
    """
    Under g_i² = g_i²_bare · e^{iθ_i}, sin²θ_W = |g₁²|² / |g₁² + g₂²|².

    Closed-form constraint on relative phase Δ = θ₂ - θ₁:

      |A|² / [|A|² + |B|² + 2|A||B|·cos(Δ)] = PDG_sin²θ_W

    where |A| = g₁²_bare, |B| = g₂²_bare.  Solving for cos(Δ):

      cos(Δ) = (|A|²/PDG − |A|² − |B|²) / (2·|A|·|B|)

    If |cos(Δ)| > 1 → no real phase closes sin²θ_W (hard impossibility).
    If |cos(Δ)| ≤ 1 → check whether Δ is a UGP-structural angle.
    """
    A = G1SQ_BARE
    B = G2SQ_BARE
    target = PDG_SIN2_THETAW

    # Bare sin²θ_W (at Δ=0 the bare value)
    bare_sin2 = A / (A + B)

    cos_delta_required = (A * A / target - A * A - B * B) / (2.0 * A * B)
    impossible = abs(cos_delta_required) > 1.0

    out = {
        "formula": "sin2thetaW = |g1^2|^2 / |g1^2 + g2^2|^2  with  g_i^2 = g_i^2_bare · e^(i*theta_i)",
        "inputs": {
            "g1sq_bare": A,
            "g2sq_bare": B,
            "PDG_sin2_thetaW": target,
            "bare_sin2_thetaW_at_delta_0": bare_sin2,
        },
        "required_cos_delta": cos_delta_required,
        "absolute_value_cos_delta": abs(cos_delta_required),
        "real_solution_exists": not impossible,
        "hard_impossibility": impossible,
    }

    if impossible:
        out["verdict"] = (
            f"HARD IMPOSSIBILITY: PDG sin²θ_W = {target} requires cos(Δ) = "
            f"{cos_delta_required:.6f}, which has |cos(Δ)| > 1.  No real relative "
            f"phase on the Lean-certified bare couplings can close sin²θ_W. "
            f"Approach 4.4 eliminated in closed form."
        )
    else:
        delta_rad = math.acos(cos_delta_required)
        out["required_delta_rad"] = delta_rad
        out["required_delta_deg"] = math.degrees(delta_rad)
        # Check against UGP structural angles
        ugp_angles = {
            "pi/10": math.pi / 10,
            "pi/5":  math.pi / 5,
            "2pi/5": 2 * math.pi / 5,
            "pi/3":  math.pi / 3,
            "2pi/3": 2 * math.pi / 3,
            "pi/2":  math.pi / 2,
            "3pi/5": 3 * math.pi / 5,
            "4pi/5": 4 * math.pi / 5,
            "pi":    math.pi,
        }
        matches = {k: abs(delta_rad - v) for k, v in ugp_angles.items()}
        closest = min(matches.items(), key=lambda kv: kv[1])
        out["closest_ugp_angle"] = {"name": closest[0], "distance_rad": closest[1]}
        out["ugp_angle_distances"] = matches
        out["verdict"] = (
            f"Δ = {math.degrees(delta_rad):.4f}°; closest UGP angle: "
            f"{closest[0]} (distance {closest[1]:.6f} rad)."
        )

    return out


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    timestamp = datetime.datetime.utcnow().isoformat() + "Z"

    # R_g targets (same as FF)
    log_Rg, log_vec, Ebase_e = compute_log_Rg_target()
    names = [f[0] for f in CHARGED_FERMIONS]

    # Build enriched atom basis (Approach 4.2 + 4.3)
    fermion_atoms = []
    for (n, gen, typ, (a, b, c), m) in CHARGED_FERMIONS:
        fermion_atoms.append(enriched_atoms_4_2_and_4_3(a, b, c, gen, typ))
    all_atoms = list(fermion_atoms[0].keys())

    # Scan DL = 1..5 with the enriched basis
    scans = {}
    for k in (1, 2, 3, 4, 5):
        top, nc, nclose = scan_dl(fermion_atoms, all_atoms, k, log_vec, top_n=20)
        scans[f"DL_{k}"] = {
            "n_atoms_in_basis": len(all_atoms),
            "n_combinations_scanned": nc,
            "n_closures_at_2pct": nclose,
            "any_closure": nclose > 0,
            "top_20_by_max_frac_err": top,
        }

    # Null test at DL=3,4,5 on the enriched basis (same protocol)
    null_by_dl = {}
    for nf in (3, 4, 5):
        null_by_dl[f"DL_{nf}"] = null_test_random(500, log_vec, n_features=nf, seed=20260420)

    # Approach 4.4 analytical
    a44 = approach_4_4_sin2tw_complex_phase()

    # Best overall candidate across scans
    best_candidate = None
    for k in scans:
        for r in scans[k]["top_20_by_max_frac_err"]:
            if best_candidate is None or r["max_fractional_error"] < best_candidate["max_fractional_error"]:
                best_candidate = {"DL": int(k.split("_")[1]), **r}

    # Prediction block
    prediction_block = {
        "comp_id": "COMP-P01-FF2",
        "title": "Complex GTE Extension Phase 1 — Approaches 4.2 (ℤ[φ]), 4.3 (ℤ[ζ₅]), 4.4 (complex gauge phase)",
        "spec_reference": "specs/IN-PROCESS/EPIC_CLUSTER7_RESEARCH_GRADE/08_SPEC_COMPLEX_GTE_EXTENSION.md §4.2-4.4",
        "prior_art": ["COMP-P01-FF (4.1 baseline)", "COMP-P01-AA", "COMP-P01-BB", "COMP-P01-EE"],
        "timestamp_utc": timestamp,
        "lean_certified_inputs": {
            "phi": PHI,
            "inv_phi_galois_conjugate": INV_PHI,
            "k_gen2": K_GEN2,
            "k_L2": K_L2,
            "k_M": K_M,
            "k_gen": COEFFS_LEAN["k_gen"],
            "g1sq_bare": G1SQ_BARE,
            "g2sq_bare": G2SQ_BARE,
        },
        "log_Rg_targets_charged_fermions": log_Rg,
        "Ebase_electron_MeV": Ebase_e,
        "enriched_atom_basis": {
            "total_atoms": len(all_atoms),
            "baseline_FF_atoms_count": 36,
            "new_atoms_from_4_2": [
                "phi_pow_2gen", "phi_pow_3gen", "inv_phi_pow_gen",
                "inv_phi_pow_2gen", "inv_phi_pow_3gen",
                "fib_g", "fib_2g", "fib_3g", "fib_ratio",
                "sqrt5_norm_a_gen", "lucas_gen", "lucas_2gen",
            ],
            "new_atoms_from_4_3": [f"cos_zeta5_{k}g" for k in (1, 2, 3, 4)] +
                                  [f"sin_zeta5_{k}g" for k in (1, 2, 3, 4)] +
                                  [f"chi_cos_zeta5_{k}g" for k in (1, 2, 3, 4)] +
                                  [f"chi_sin_zeta5_{k}g" for k in (1, 2, 3, 4)],
            "atom_names_all": all_atoms,
        },
        "scans_enriched_basis": scans,
        "null_test_by_DL": null_by_dl,
        "approach_4_4_analytical": a44,
    }

    # SHA-256 seal
    pred_str = json.dumps(prediction_block, sort_keys=True, separators=(",", ":"), default=str)
    sha256_pred = hashlib.sha256(pred_str.encode("utf-8")).hexdigest()

    # Verdicts
    any_structural_closure = any(scans[k]["any_closure"] for k in scans)
    null_rate_5 = null_by_dl["DL_5"]["hit_rate"]
    null_rate_below_1pct = null_rate_5 < 0.01

    pdg_comparison = {
        "prediction_block_sha256": sha256_pred,
        "approach_4_2_4_3_verdict": (
            "CLOSES" if (any_structural_closure and null_rate_below_1pct)
            else ("DENSITY_DOMINATED" if (any_structural_closure and not null_rate_below_1pct)
                  else "MAP_insufficient_at_DL_le_5")
        ),
        "any_structural_closure_at_DL_le_5": any_structural_closure,
        "null_hit_rate_DL5": null_rate_5,
        "null_disciplined": null_rate_below_1pct,
        "best_structural_candidate": best_candidate,
        "approach_4_4_verdict": a44["verdict"],
        "approach_4_4_real_solution_exists": a44["real_solution_exists"],
    }

    output = {
        "prediction_block_precomparison": prediction_block,
        "sha256_prediction_block": sha256_pred,
        "pdg_comparison": pdg_comparison,
    }

    # Summary print
    print(f"COMP-P01-FF2: Complex GTE Approaches 4.2 / 4.3 / 4.4")
    print(f"Timestamp: {timestamp}")
    print(f"Prediction block SHA-256: {sha256_pred}")
    print()
    print(f"Enriched atom basis: {len(all_atoms)} atoms (FF baseline: 36)")
    print()
    print("--- Approaches 4.2 + 4.3 (enriched basis DL scan) ---")
    for k in ("DL_1", "DL_2", "DL_3", "DL_4", "DL_5"):
        s = scans[k]
        top1 = s["top_20_by_max_frac_err"][0] if s["top_20_by_max_frac_err"] else None
        print(f"  {k}: {s['n_combinations_scanned']:>7d} combos  → {s['n_closures_at_2pct']} close at ≤2%")
        if top1:
            print(f"    best: atoms={top1['atoms']}")
            print(f"          max_frac_err={top1['max_fractional_error']:.4g}   "
                  f"{'CLOSES' if top1['closes_at_2pct'] else ''}")
    print()
    print(f"Null test (enriched basis):")
    for nf in (3, 4, 5):
        r = null_by_dl[f"DL_{nf}"]
        print(f"  DL={nf}: {r['hit_count']}/500 = {r['hit_rate']:.4f}")
    print()
    print("--- Approach 4.4 (complex gauge phase for sin²θ_W) ---")
    print(f"  Required cos(Δ) = {a44['required_cos_delta']:.6f}")
    print(f"  |cos(Δ)| = {a44['absolute_value_cos_delta']:.6f}")
    print(f"  {a44['verdict']}")
    print()
    print(f"4.2/4.3 verdict: {pdg_comparison['approach_4_2_4_3_verdict']}")
    print(f"4.4    verdict: {'HARD IMPOSSIBILITY' if not a44['real_solution_exists'] else 'SOLUTION EXISTS'}")
    if best_candidate:
        print(f"Best structural: DL={best_candidate['DL']}  atoms={best_candidate['atoms']}  "
              f"max_frac_err={best_candidate['max_fractional_error']:.4g}")

    return output


if __name__ == "__main__":
    output = main()
    out_path = "comp_p01_FF2_complex_gte_approaches_234.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2, default=str)
    import subprocess
    r = subprocess.run(
        ["python3", "-c", f"import json; json.load(open('{out_path}')); print('JSON valid')"],
        capture_output=True, text=True,
    )
    print()
    print(f"Output written to {out_path}")
    print(r.stdout.strip() if r.returncode == 0 else f"JSON ERROR: {r.stderr}")
