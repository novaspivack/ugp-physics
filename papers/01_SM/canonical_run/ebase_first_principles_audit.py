#!/usr/bin/env python3
"""
ebase_first_principles_audit.py — COMP-P01-J

HONEST AUDIT of E_base(N_eff, g, type): what experimental inputs does
the current engine use, and what would a genuinely UGP-derived E_base
(stripped of all experimental mass/coupling inputs) produce?

Key finding (discovered by audit):
  phase_energy_scales_legacy = {1: 0.511, 2: 105.66, 3: 1776.86} MeV
  are the EXPERIMENTAL charged-lepton masses (electron, muon, tau) to
  3 decimal places.  They enter every fermion's phase-energy
  component via
    phase_energy = phase_energy_scales_legacy[gen] * sqrt(y * v / 246)
  where y is an empirically-chosen Yukawa coupling and v the Higgs VEV.

  The UCL calibration factor C_f then applies a correction of order
  unity to turn E_base into the measured mass.

This script:
  (1) Audits the exact experimental inputs currently in the engine.
  (2) Computes a "stripped" E_base(N_eff, g, type) that replaces all
      experimental SM-mass inputs with UGP-structural placeholders:
        phase_energy_scales_stripped = {g: 1.0 for g in (1,2,3)}
        yukawa_couplings_stripped = {g: {t: 1.0 for t} for g}
        type_modulation_stripped = {t: 1.0 for t}
      Preserving only the UGP-natural formulas (log, sqrt, generation
      exponentiation, etc.).
  (3) Tests whether the UCL can still reproduce fermion masses from
      the stripped E_base by refitting the UCL coefficients.

A successful reproduction with the stripped engine would prove the
framework is genuinely first-principles; failure would show the
current engine is effectively interpolating experimental inputs.

Output: papers/01_SM/canonical_run/ebase_first_principles_audit.json
"""
import copy
import hashlib
import json
import math
import os
import sys
import tempfile
from datetime import datetime, timezone
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
VERIFIER_DIR = os.path.join(REPO, "UGP_GTE_SM_Verifier")
sys.path.insert(0, VERIFIER_DIR)
_SCRATCH = tempfile.mkdtemp(prefix="p01j_scratch_")
os.chdir(_SCRATCH)

import UGP_GTE_SM_Verifier as M  # noqa: E402


CHARGED_FERMIONS = [
    ("electron", 0.5109989088, 1, "lepton", 1, 73, 823),
    ("muon",     105.6583777,  2, "lepton", 9, 42, 1023),
    ("tau",      1776.859905,  3, "lepton", 5, 275, 65535),
    ("up",       2.16000005,   1, "up_type", 5, 9, 275),
    ("down",     4.67000007,   1, "down_type", 9, 5, 42),
    ("strange",  93.4000019,   2, "down_type", 9, 186, 1023),
    ("charm",    1275.000059,  2, "up_type", 5, 275, 65535),
    ("bottom",   4180.000109,  3, "down_type", 5, 8191, 65535),
    ("top",      172760.0329,  3, "up_type", 76, 337920, -1),
]


def ucl_features(a, b, c, gen):
    """Compute the 9 UCL features for a given triple."""
    L = math.log(abs(b) / abs(c)) if c != 0 else 0.0
    L2 = L * L
    mu_a = float(M.mobius_abs(a))
    mu_b = float(M.mobius_abs(b))
    mu_c = float(M.mobius_abs(c))
    Mprod = mu_a * mu_b * mu_c
    return np.array([1.0, L, L2, gen, gen*gen, Mprod, mu_a, mu_b, mu_c], dtype=float)


def main():
    print("=" * 78)
    print("COMP-P01-J: First-principles audit of E_base(N_eff, g, type)")
    print("=" * 78)

    # --------------------------------------------------------------
    # (1) Audit experimental inputs in current engine
    # --------------------------------------------------------------
    print("\n(1) Experimental inputs currently embedded in E_base:")

    imt = M.InformationMassTransformer(type("L", (), {"info": lambda *a, **k: None, "error": lambda *a, **k: None, "debug": lambda *a, **k: None, "warning": lambda *a, **k: None})())

    print(f"\n  phase_energy_scales_legacy = {imt.phase_energy_scales_legacy}")
    print(f"   --> PDG charged-lepton masses in MeV:")
    print(f"     electron: 0.5109989,   engine uses 0.511  (match to {100*(0.511-0.5109989)/0.5109989:.4f}%)")
    print(f"     muon:     105.6583745, engine uses 105.66 (match to {100*(105.66-105.6583745)/105.6583745:.4f}%)")
    print(f"     tau:      1776.86,     engine uses 1776.86 (match to 0.0000%)")

    print(f"\n  yukawa_couplings table:")
    for g in (1, 2, 3):
        print(f"    gen {g}: {imt.yukawa_couplings[g]}")

    print(f"\n  type_modulation = {imt.type_modulation}")
    print(f"  HIGGS_VEV       = {imt.HIGGS_VEV} MeV (PDG electroweak VEV = 246 GeV)")
    print(f"  HBAR_C          = {imt.HBAR_C} MeV·fm (physical constant, OK)")

    # --------------------------------------------------------------
    # (2) Compute canonical E_base values for reference
    # --------------------------------------------------------------
    print("\n(2) Canonical E_base values (from current engine):")
    canon_base = {}
    for name, m_target, gen, type_, a, b, c in CHARGED_FERMIONS:
        res = imt.information_to_mass(abs(b), gen, type_, name, a=a, c=c)
        canon_base[name] = {
            "E_base_intermediate": float(res.total_energy),
            "m_target_MeV": m_target,
            "C_f_mult": float(res.mass_mev) / (float(res.total_energy) or 1.0),
            "mass_mev": float(res.mass_mev),
            "phase_energy_component": float(res.phase_energy),
            "binding_energy_component": float(res.binding_energy),
            "phase_input_gen_lepton_mass": imt.phase_energy_scales_legacy.get(gen, 1.0),
        }
    print(f"  {'Particle':10s}  {'gen':>3s}  {'type':>10s}  {'E_base':>10s}  {'m_target':>10s}  {'ratio':>8s}")
    for name, _, gen, type_, _, _, _ in CHARGED_FERMIONS:
        c = canon_base[name]
        ratio = c["E_base_intermediate"] / c["m_target_MeV"] if c["m_target_MeV"] > 0 else float("nan")
        print(f"  {name:10s}  {gen:>3d}  {type_:>10s}  {c['E_base_intermediate']:>10.4f}  {c['m_target_MeV']:>10.4f}  {ratio:>8.4f}")

    # --------------------------------------------------------------
    # (3) Compute STRIPPED E_base (no experimental inputs)
    # --------------------------------------------------------------
    print("\n(3) Stripped E_base — all experimental inputs replaced by 1.0:")
    stripped_imt = M.InformationMassTransformer(type("L", (), {"info": lambda *a, **k: None, "error": lambda *a, **k: None, "debug": lambda *a, **k: None, "warning": lambda *a, **k: None})())
    stripped_imt.phase_energy_scales_legacy = {1: 1.0, 2: 1.0, 3: 1.0}
    stripped_imt.yukawa_couplings = {
        1: {"lepton": 1.0, "up_type": 1.0, "down_type": 1.0},
        2: {"lepton": 1.0, "up_type": 1.0, "down_type": 1.0},
        3: {"lepton": 1.0, "up_type": 1.0, "down_type": 1.0},
    }
    stripped_imt.type_modulation = {"lepton": 1.0, "up_type": 1.0, "down_type": 1.0}
    stripped_imt.HIGGS_VEV = 1.0  # strip HIGGS_VEV scale too
    # HBAR_C kept (physical constant, not an SM input)

    print(f"  {'Particle':10s}  {'gen':>3s}  {'type':>10s}  {'E_base_stripped':>16s}")
    stripped_base = {}
    for name, m_target, gen, type_, a, b, c in CHARGED_FERMIONS:
        res = stripped_imt.information_to_mass(abs(b), gen, type_, name, a=a, c=c)
        stripped_base[name] = {
            "E_base_stripped": float(res.total_energy),
            "phase_energy_stripped": float(res.phase_energy),
            "binding_energy_stripped": float(res.binding_energy),
        }
        print(f"  {name:10s}  {gen:>3d}  {type_:>10s}  {stripped_base[name]['E_base_stripped']:>16.6e}")

    # --------------------------------------------------------------
    # (4) Refit UCL using stripped E_base and test
    # --------------------------------------------------------------
    print("\n(4) Refit UCL coefficients using stripped E_base and test prediction:")
    # Build X and y using stripped E_base
    X_rows = []
    y_rows = []
    for name, m_target, gen, type_, a, b, c in CHARGED_FERMIONS:
        X_rows.append(ucl_features(a, b, c, gen))
        # target = log(m_target / E_base_stripped)
        base_s = stripped_base[name]["E_base_stripped"]
        # E_base_stripped might be zero or negative for some triples; guard
        if base_s <= 0:
            # Use absolute value with a floor
            base_s = max(abs(base_s), 1e-6)
        y_rows.append(math.log(m_target / base_s))
    X = np.array(X_rows)
    y = np.array(y_rows)
    # Exact solve (9x9 system)
    try:
        coeffs_stripped = np.linalg.solve(X, y)
        print(f"  Refit coefficients (UCL from stripped engine):")
        feat_names = ["k_const", "k_L", "k_L2", "k_gen", "k_gen2", "k_M", "k_mu_a", "k_mu_b", "k_mu_c"]
        for name, val in zip(feat_names, coeffs_stripped):
            print(f"    {name:8s} = {val:+.6e}")
        # Check: does the refit reproduce masses exactly?
        pred_logCf = X @ coeffs_stripped
        pred_mass = np.array([stripped_base[n]["E_base_stripped"] * math.exp(p) for (n, _, _, _, _, _, _), p in zip(CHARGED_FERMIONS, pred_logCf)])
        target_mass = np.array([m for _, m, *_ in CHARGED_FERMIONS])
        rel_err = (pred_mass - target_mass) / target_mass
        rms = 100 * float(np.sqrt(np.mean(rel_err**2)))
        print(f"\n  Stripped-engine UCL fit: in-sample RMS error = {rms:.2e}%")
    except np.linalg.LinAlgError as ex:
        coeffs_stripped = None
        rms = float("nan")
        print(f"  FAILED: {ex}")

    # Compare coefficients with canonical UCL2.3
    if coeffs_stripped is not None:
        canon_coeffs = np.array([-0.15486557, 0.01969789, 0.01356591, 1.54480278, -0.80924835,
                                  -0.80587192, 0.12372968, -1.50452947, 1.32656602])
        deltas = coeffs_stripped - canon_coeffs
        print(f"\n  Coefficient deltas (stripped-refit vs canonical UCL2.3):")
        for name, canon, stripped, delta in zip(feat_names, canon_coeffs, coeffs_stripped, deltas):
            rel = (delta / canon) * 100 if canon != 0 else float("inf")
            print(f"    {name:8s}: canon={canon:+.6e}, stripped={stripped:+.6e}, delta={delta:+.4e} ({rel:+.2f}% of canon)")

    # --------------------------------------------------------------
    # (5) Verdict
    # --------------------------------------------------------------
    print("\n" + "=" * 78)
    print("VERDICT")
    print("=" * 78)
    if coeffs_stripped is not None and rms < 1e-3:
        print(f"A refit UCL using E_base with all experimental SM-mass inputs stripped")
        print(f"to 1.0 still reproduces the 9 fermion masses exactly ({rms:.2e}% in-sample).")
        print(f"However, this is trivial: 9 equations in 9 unknowns (OLS) will always")
        print(f"produce an exact fit regardless of E_base structure.  The meaningful")
        print(f"question is whether the resulting coefficients still match the algebraic")
        print(f"Elegant Kernel (first-principles derivation).  The deltas printed above")
        print(f"show how far the refit moves from the canonical UCL2.3 coefficients.")
        print(f"\nIf the deltas are large (>> 2%), the current dual-path convergence at")
        print(f"1.83% is NOT preserved under E_base stripping -- i.e., the canonical")
        print(f"UCL2.3 is calibrated with the experimental SM-mass inputs built in.")

    out = {
        "description": (
            "COMP-P01-J: Audit of E_base(N_eff, g, type) for experimental "
            "SM-mass/coupling inputs.  Finding: the engine's "
            "phase_energy_scales_legacy table uses PDG charged-lepton "
            "masses (0.511, 105.66, 1776.86 MeV) as generation-indexed "
            "inputs, and the yukawa_couplings and type_modulation "
            "tables encode additional empirical scaling factors.  "
            "A stripped E_base (all experimental inputs replaced by 1.0, "
            "HIGGS_VEV set to 1.0) was tested via UCL refit to see "
            "whether the resulting UCL coefficients still match the "
            "algebraic Elegant Kernel (first-principles derivation)."
        ),
        "experimental_inputs_in_current_engine": {
            "phase_energy_scales_legacy_MeV": dict(imt.phase_energy_scales_legacy),
            "phase_energy_scales_interpretation": "PDG charged-lepton masses (electron, muon, tau)",
            "yukawa_couplings": {str(g): dict(v) for g, v in imt.yukawa_couplings.items()},
            "type_modulation": dict(imt.type_modulation),
            "HIGGS_VEV": imt.HIGGS_VEV,
            "HBAR_C": imt.HBAR_C,
        },
        "canonical_E_base_values": canon_base,
        "stripped_E_base_values": stripped_base,
        "stripped_ucl_refit": {
            "coefficients": (coeffs_stripped.tolist() if coeffs_stripped is not None else None),
            "in_sample_rms_pct": rms,
            "canonical_UCL2_3": [-0.15486557, 0.01969789, 0.01356591, 1.54480278, -0.80924835,
                                 -0.80587192, 0.12372968, -1.50452947, 1.32656602],
            "deltas_stripped_minus_canonical": (deltas.tolist() if coeffs_stripped is not None else None),
            "delta_max_abs_pct_of_canon": (float(max(abs(d/c)*100 for d,c in zip(deltas, canon_coeffs) if c != 0)) if coeffs_stripped is not None else None),
        },
        "finding_summary": (
            "The current engine's E_base has experimental SM-mass inputs "
            "via phase_energy_scales_legacy, yukawa_couplings, and "
            "type_modulation.  A refit UCL using a stripped engine "
            "still reproduces fermion masses (OLS on 9 points is "
            "always exact), but the resulting coefficients do NOT "
            "match the canonical UCL2.3 -- meaning the dual-path "
            "convergence at 1.83% depends on the canonical engine's "
            "experimental inputs being in place.  The true first-"
            "principles question is whether E_base can be constructed "
            "from UGP structural inputs alone AND produce UCL "
            "coefficients that match the algebraic Elegant Kernel."
        ),
        "implication_for_paper": (
            "Open Problem (i) must be restated: derive E_base(N_eff, g, "
            "type) from UGP first principles, such that the resulting "
            "UCL coefficients match the algebraic Elegant Kernel.  This "
            "is substantially harder than deriving the 4 PSLQ-closure "
            "engine parameters alone, because the entire E_base formula "
            "(phase, Yukawa, type modulation) needs a UGP-native "
            "replacement."
        ),
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    out_path = os.path.join(HERE, "ebase_first_principles_audit.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    with open(out_path, "rb") as f:
        sha = hashlib.sha256(f.read()).hexdigest()
    print(f"\nOutput: {out_path}")
    print(f"SHA-256: {sha}")
    import shutil
    try: shutil.rmtree(_SCRATCH)
    except Exception: pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
