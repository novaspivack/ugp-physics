#!/usr/bin/env python3
"""
landscape_probe.py — comprehensive optimum-landscape audit

Tests the user's stated memory: "the UCL is a broad-flat optimum, not
a needle."  Three independent perturbation axes are exercised, all
against the same primary-sigma metric used by the canonical SD5 run:

  AXIS 1 — UCL coefficient jitter (the 9 frozen UCL2.3 coefficients
           in the dual-path table; what the user's memory most likely
           refers to).  Replaces each k_i one at a time with k_i*(1+f)
           and recomputes primary sigma.

  AXIS 2 — Engine-mixer parameter jitter (the 4 algebraic mixer
           parameters s_eng_1, s_eng_3, w_eng_phi, w_eng_b that
           COMP-P01-E perturbed).  Replicated here so AXIS 1 and
           AXIS 2 are reported with identical scoring methodology.

  AXIS 3 — (phase_k, renorm_k) engine knobs (the legacy ENGINE_CONFIG
           parameters fixed at phase_k=2.0, renorm_k=1400 — the
           knobs that the paper §10.5 historical DOF ledger calls
           out as the "2 frozen-canonical engine knobs").

For each axis, we report degradation ratio at jitter levels
±{0.01, 0.1, 1, 5, 10}%.

Honest classification per axis:
  "broad-flat" if at ±1% jitter the geomean ratio < 10
  "intermediate" if 10 < geomean ratio < 1000
  "narrow"     if geomean ratio > 1000

This probe is the empirical version of the question: at which layer
of the prediction pipeline does the optimum become narrow?
"""
import copy
import hashlib
import json
import math
import os
import sys
import tempfile
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
VERIFIER_DIR = os.path.join(REPO, "UGP_GTE_SM_Verifier")
sys.path.insert(0, VERIFIER_DIR)

_SCRATCH = tempfile.mkdtemp(prefix="p01_landscape_")
os.chdir(_SCRATCH)

import numpy as np  # noqa: E402
import UGP_GTE_SM_Verifier as M  # noqa: E402


CANONICAL_MIXER = copy.deepcopy(M._MIXER_V12)
CANONICAL_COEFF = M.COEFF_VECTOR.copy()
CANONICAL_PHASE_K = float(M.ENGINE_CONFIG.phase_k)
CANONICAL_RENORM_K = float(M.ENGINE_CONFIG.renorm_k)


JITTER_FRACTIONS = [1e-4, 1e-3, 1e-2, 5e-2, 0.10]


# -----------------------------------------------------------------
# Probes
# -----------------------------------------------------------------
def primary_sigma_canonical():
    M.set_physics_mixer_v12(copy.deepcopy(CANONICAL_MIXER))
    M.COEFF_VECTOR[:] = CANONICAL_COEFF
    M.ENGINE_CONFIG.phase_k = CANONICAL_PHASE_K
    M.ENGINE_CONFIG.renorm_k = CANONICAL_RENORM_K
    pred = M._predict_masses_with_bmode(bmode="canon")
    return float(M._primary_sigma_from_pred_map(pred))


def jitter_ucl_coeff(idx, scale):
    M.set_physics_mixer_v12(copy.deepcopy(CANONICAL_MIXER))
    M.ENGINE_CONFIG.phase_k = CANONICAL_PHASE_K
    M.ENGINE_CONFIG.renorm_k = CANONICAL_RENORM_K
    perturbed = CANONICAL_COEFF.copy()
    perturbed[idx] = perturbed[idx] * (1.0 + scale)
    M.COEFF_VECTOR[:] = perturbed
    pred = M._predict_masses_with_bmode(bmode="canon")
    return float(M._primary_sigma_from_pred_map(pred))


def jitter_engine_mixer(kind_key, scale):
    M.COEFF_VECTOR[:] = CANONICAL_COEFF
    M.ENGINE_CONFIG.phase_k = CANONICAL_PHASE_K
    M.ENGINE_CONFIG.renorm_k = CANONICAL_RENORM_K
    p = copy.deepcopy(CANONICAL_MIXER)
    kind, key = kind_key
    if kind == "gen":
        p["generation_scaling"][key] *= (1.0 + scale)
    else:
        p["weights"][key] *= (1.0 + scale)
    M.set_physics_mixer_v12(p)
    pred = M._predict_masses_with_bmode(bmode="canon")
    return float(M._primary_sigma_from_pred_map(pred))


def jitter_engine_knob(name, scale):
    M.set_physics_mixer_v12(copy.deepcopy(CANONICAL_MIXER))
    M.COEFF_VECTOR[:] = CANONICAL_COEFF
    M.ENGINE_CONFIG.phase_k = CANONICAL_PHASE_K
    M.ENGINE_CONFIG.renorm_k = CANONICAL_RENORM_K
    if name == "phase_k":
        M.ENGINE_CONFIG.phase_k = CANONICAL_PHASE_K * (1.0 + scale)
    elif name == "renorm_k":
        M.ENGINE_CONFIG.renorm_k = CANONICAL_RENORM_K * (1.0 + scale)
    pred = M._predict_masses_with_bmode(bmode="canon")
    return float(M._primary_sigma_from_pred_map(pred))


# -----------------------------------------------------------------
# Driver
# -----------------------------------------------------------------
COEF_NAMES = ["k_const", "k_L", "k_L2", "k_gen", "k_gen2", "k_M",
              "k_mu_a", "k_mu_b", "k_mu_c"]

ENGINE_PARAMS = [
    ("s_eng_1",   ("gen", 1)),
    ("s_eng_3",   ("gen", 3)),
    ("w_eng_phi", ("weight", "Phase")),
    ("w_eng_b",   ("weight", "Binding")),
]

ENGINE_KNOBS = ["phase_k", "renorm_k"]


def classify(geomean_ratio_at_1pct):
    if geomean_ratio_at_1pct < 10:
        return "broad-flat"
    if geomean_ratio_at_1pct < 1000:
        return "intermediate"
    return "narrow"


def gmean(xs):
    return math.exp(sum(math.log(max(x, 1e-30)) for x in xs) / len(xs))


def main():
    baseline = primary_sigma_canonical()
    print("=" * 78)
    print("Optimum-landscape probe — three independent perturbation axes")
    print("=" * 78)
    print(f"Canonical baseline primary sigma = {baseline:.6e}\n")

    out = {
        "description": (
            "Three-axis landscape probe to characterize the optimum at "
            "each layer of the prediction pipeline.  Asks the question "
            "'is the optimum broad-flat or narrow?' separately for "
            "(1) the 9 UCL2.3 coefficients, (2) the 4 algebraic mixer "
            "parameters, (3) the 2 legacy engine knobs (phase_k, renorm_k)."
        ),
        "baseline_primary_sigma": baseline,
        "jitter_fractions": JITTER_FRACTIONS,
        "axes": {},
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }

    # -----------------------------------------
    # AXIS 1 — UCL coefficient jitter
    # -----------------------------------------
    print("AXIS 1 — UCL coefficient jitter (9 coefficients × 5 jitter levels × 2 signs)")
    axis1 = {"items": [], "summary_per_jitter": {}}
    for f in JITTER_FRACTIONS:
        ratios = []
        for idx, name in enumerate(COEF_NAMES):
            for sign in (-1, +1):
                s = sign * f
                sigma = jitter_ucl_coeff(idx, s)
                r = sigma / baseline
                ratios.append(r)
                axis1["items"].append({"coeff": name, "scale_pct": 100*s,
                                       "sigma": sigma, "ratio": r})
        gm = gmean(ratios)
        mn, mx = min(ratios), max(ratios)
        axis1["summary_per_jitter"][f"{100*f:g}%"] = {
            "min_ratio": mn, "max_ratio": mx, "geom_mean_ratio": gm,
            "classification": classify(gm if abs(f - 0.01) < 1e-9 else None) if abs(f - 0.01) < 1e-9 else None,
        }
        print(f"  ±{100*f:5.2f}%: min={mn:.2e}, max={mx:.2e}, geomean={gm:.2e}")
    cls1 = classify(axis1["summary_per_jitter"]["1%"]["geom_mean_ratio"])
    axis1["classification_at_1pct"] = cls1
    print(f"  --> CLASSIFICATION at ±1%: {cls1.upper()}")
    print()
    out["axes"]["UCL_coefficients_9"] = axis1

    # -----------------------------------------
    # AXIS 2 — Engine mixer parameters
    # -----------------------------------------
    print("AXIS 2 — Engine mixer parameter jitter (4 params × 5 jitter levels × 2 signs)")
    axis2 = {"items": [], "summary_per_jitter": {}}
    for f in JITTER_FRACTIONS:
        ratios = []
        for name, kind_key in ENGINE_PARAMS:
            for sign in (-1, +1):
                s = sign * f
                sigma = jitter_engine_mixer(kind_key, s)
                r = sigma / baseline
                ratios.append(r)
                axis2["items"].append({"param": name, "scale_pct": 100*s,
                                       "sigma": sigma, "ratio": r})
        gm = gmean(ratios)
        mn, mx = min(ratios), max(ratios)
        axis2["summary_per_jitter"][f"{100*f:g}%"] = {
            "min_ratio": mn, "max_ratio": mx, "geom_mean_ratio": gm,
        }
        print(f"  ±{100*f:5.2f}%: min={mn:.2e}, max={mx:.2e}, geomean={gm:.2e}")
    cls2 = classify(axis2["summary_per_jitter"]["1%"]["geom_mean_ratio"])
    axis2["classification_at_1pct"] = cls2
    print(f"  --> CLASSIFICATION at ±1%: {cls2.upper()}")
    print()
    out["axes"]["engine_mixer_params_4"] = axis2

    # -----------------------------------------
    # AXIS 3 — (phase_k, renorm_k)
    # -----------------------------------------
    print("AXIS 3 — Engine knobs (phase_k=2.0, renorm_k=1400) jitter (2 knobs × 5 levels × 2 signs)")
    axis3 = {"items": [], "summary_per_jitter": {}}
    for f in JITTER_FRACTIONS:
        ratios = []
        for name in ENGINE_KNOBS:
            for sign in (-1, +1):
                s = sign * f
                sigma = jitter_engine_knob(name, s)
                r = sigma / baseline
                ratios.append(r)
                axis3["items"].append({"knob": name, "scale_pct": 100*s,
                                       "sigma": sigma, "ratio": r})
        gm = gmean(ratios)
        mn, mx = min(ratios), max(ratios)
        axis3["summary_per_jitter"][f"{100*f:g}%"] = {
            "min_ratio": mn, "max_ratio": mx, "geom_mean_ratio": gm,
        }
        print(f"  ±{100*f:5.2f}%: min={mn:.2e}, max={mx:.2e}, geomean={gm:.2e}")
    cls3 = classify(axis3["summary_per_jitter"]["1%"]["geom_mean_ratio"])
    axis3["classification_at_1pct"] = cls3
    print(f"  --> CLASSIFICATION at ±1%: {cls3.upper()}")
    print()
    out["axes"]["engine_knobs_2"] = axis3

    # -----------------------------------------
    # Verdict
    # -----------------------------------------
    print("=" * 78)
    print("VERDICT")
    print("=" * 78)
    print(f"  AXIS 1 (UCL 9 coefficients):     {cls1.upper()} optimum")
    print(f"  AXIS 2 (engine mixer 4 params):  {cls2.upper()} optimum")
    print(f"  AXIS 3 (phase_k, renorm_k):      {cls3.upper()} optimum")
    print()
    out["verdict"] = {
        "UCL_coefficients_9": cls1,
        "engine_mixer_params_4": cls2,
        "engine_knobs_2": cls3,
    }

    # Restore canonical state
    M.set_physics_mixer_v12(copy.deepcopy(CANONICAL_MIXER))
    M.COEFF_VECTOR[:] = CANONICAL_COEFF
    M.ENGINE_CONFIG.phase_k = CANONICAL_PHASE_K
    M.ENGINE_CONFIG.renorm_k = CANONICAL_RENORM_K

    out_path = os.path.join(HERE, "landscape_probe.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    with open(out_path, "rb") as f:
        sha = hashlib.sha256(f.read()).hexdigest()
    print(f"Output: {out_path}")
    print(f"SHA-256: {sha}")

    import shutil
    try:
        shutil.rmtree(_SCRATCH)
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
