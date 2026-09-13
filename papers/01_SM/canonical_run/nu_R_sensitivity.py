#!/usr/bin/env python3
"""
nu_R_sensitivity.py - COMP-P01-C

Sensitivity of the Paper 1 neutrino-sector predictions (individual m_nu,
m_beta_beta range, right-handed Majorana scales M_R) to the two *free*
input choices of the seesaw pipeline:

  (a) The sum m_nu cosmological anchor (baseline 60 meV; varied over
      the preregistered window [55, 120] meV).
  (b) The measured mass-squared splittings (varied within experimental
      1-sigma uncertainties).

The nu_R construction is a template (seesaw_from_ugp_template) that
builds three neutrino states from UGP ridge levels n_set = (10,12,16)
and solves for the absolute mass scale using the anchor and splittings.
Reviewers have asked whether Sigma m_nu ~ 59 meV is a tuned output or
a robust prediction; this script gives the quantitative answer.

NOTE on the S3-overlap description in the paper body: the published
code base implements the anchor-plus-splitting version here; the S3
irreducible-representation overlap construction described in Sec. 7.2
is not yet implemented in code.  The sensitivity analysis therefore
characterises the ACTUAL pipeline; implementing the S3 overlap path
is tracked as an open computational step.
"""
import json
import os
import sys
import hashlib
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
VERIFIER_DIR = os.path.join(REPO, "UGP_GTE_SM_Verifier")
sys.path.insert(0, VERIFIER_DIR)

# Redirect all relative writes from UGP_GTE_SM_Verifier (which calls
# _write_json_rel_safe with CWD fallback) into a throwaway scratch
# directory so the canonical_run/ frozen artifacts are never clobbered.
import tempfile
_SCRATCH = tempfile.mkdtemp(prefix="p01c_scratch_")
os.chdir(_SCRATCH)

import UGP_GTE_SM_Verifier as M  # noqa: E402


# Baseline inputs (NuFIT-5.2-like + PDG):
DM21_CENTRAL = 7.42e-5   # eV^2
DM21_SIGMA = 0.21e-5     # NuFIT 5.2 +/- (approx)
DM31_CENTRAL = 2.517e-3  # eV^2 (NO)
DM31_SIGMA = 0.026e-3

# ----------------------------------------------------------------------
# Sweep definitions
# ----------------------------------------------------------------------
ANCHOR_SWEEP = [55.0, 60.0, 70.0, 80.0, 100.0, 120.0]

SPLIT_SWEEP = [
    ("central",       DM21_CENTRAL, DM31_CENTRAL),
    ("dm21_low_1s",   DM21_CENTRAL - DM21_SIGMA, DM31_CENTRAL),
    ("dm21_high_1s",  DM21_CENTRAL + DM21_SIGMA, DM31_CENTRAL),
    ("dm31_low_1s",   DM21_CENTRAL, DM31_CENTRAL - DM31_SIGMA),
    ("dm31_high_1s",  DM21_CENTRAL, DM31_CENTRAL + DM31_SIGMA),
]


def run_anchor(sum_mnu_meV):
    tmp = "/tmp/_seesaw_anchor.json"
    try: os.remove(tmp)
    except FileNotFoundError: pass
    res = M.seesaw_from_ugp_template(
        sum_mnu_meV=sum_mnu_meV, ordering="NO", out_json=tmp
    )
    try: os.remove(tmp)
    except FileNotFoundError: pass
    return res


def run_splittings(dm21, dm31, sum_mnu_meV=60.0):
    # Replicate UGP_GTE_SM_Verifier solve directly so we can vary dm21/dm31.
    masses = M._solve_sum_mnu("NO", sum_mnu_meV / 1000.0, dm21=dm21, dm3l=dm31)
    return masses


def mbb_range(m_eV, pmns_angles_deg, delta_CP_deg):
    import math, numpy as np
    s12 = math.sin(math.radians(pmns_angles_deg["theta12"]))
    c12 = math.cos(math.radians(pmns_angles_deg["theta12"]))
    s13 = math.sin(math.radians(pmns_angles_deg["theta13"]))
    c13 = math.cos(math.radians(pmns_angles_deg["theta13"]))
    Ue = np.array([c12*c13, s12*c13, s13 * np.exp(-1j*math.radians(delta_CP_deg))], dtype=complex)
    m = np.array(m_eV, dtype=float)
    grid = np.linspace(0.0, 2.0*math.pi, 721)
    mbb_vals = []
    for a1 in grid[::8]:
        for a2 in grid[::8]:
            ph = np.array([np.exp(1j*a1), np.exp(1j*a2), 1.0+0j], dtype=complex)
            mbb_vals.append(float(abs(np.sum((Ue**2) * m * ph))))
    return float(min(mbb_vals)), float(max(mbb_vals))


def main():
    print("=" * 72)
    print("COMP-P01-C: Neutrino-sector sensitivity to anchor and splittings")
    print("=" * 72)

    # Canonical PMNS angles used throughout (from the seesaw template's
    # PDG-anchored reference).
    ref = run_anchor(60.0)
    pmns_angles = {
        "theta12": 33.44,
        "theta13": 8.57,
        "theta23": 49.20,
    }
    # Use the UGP-extracted delta_l from the canonical run (not the
    # Z6 branch) so that this test measures m_beta_beta sensitivity
    # under *a fixed delta*.  The Z6 structural prediction is separate.
    delta_seesaw = ref["delta_l_deg"]

    # ------------------------------------------------------------------
    # (a) Sum m_nu anchor sweep
    # ------------------------------------------------------------------
    print("\n--- (a) Anchor sweep ---")
    anchor_rows = []
    for s in ANCHOR_SWEEP:
        p = run_anchor(s)
        m_eV = p["m_nu_eV"]
        lo, hi = p["m_beta_beta_min_eV"] * 1000.0, p["m_beta_beta_max_eV"] * 1000.0
        row = {
            "sum_mnu_anchor_meV": s,
            "m_nu_meV": [1000.0 * x for x in m_eV],
            "m_beta_beta_meV": [lo, hi],
            "MR_GeV": p["MR_GeV"],
            "delta_CP_deg": p["delta_l_deg"],
        }
        anchor_rows.append(row)
        print(f"  Sigma = {s:6.1f} meV : m_nu = {[round(1000*x,3) for x in m_eV]}  m_bb = [{lo:.3f}, {hi:.3f}] meV  M_R3 = {p['MR_GeV'][-1]:.2e} GeV")

    # ------------------------------------------------------------------
    # (b) Splittings sweep (at anchor = 60 meV)
    # ------------------------------------------------------------------
    print("\n--- (b) Delta m^2 sweep (anchor = 60 meV) ---")
    split_rows = []
    for label, dm21, dm31 in SPLIT_SWEEP:
        m_eV = run_splittings(dm21, dm31, 60.0)
        lo, hi = mbb_range(m_eV, pmns_angles, delta_seesaw)
        row = {
            "label": label,
            "dm21_eV2": dm21,
            "dm31_eV2": dm31,
            "m_nu_meV": [1000.0 * x for x in m_eV],
            "m_beta_beta_meV": [lo * 1000.0, hi * 1000.0],
            "sum_mnu_meV": 1000.0 * sum(m_eV),
        }
        split_rows.append(row)
        print(f"  {label:15s}: dm21 = {dm21:.2e}, dm31 = {dm31:.2e}")
        print(f"    -> m_nu = {[round(x,4) for x in row['m_nu_meV']]} meV   m_bb = [{lo*1000:.3f}, {hi*1000:.3f}] meV")

    # ------------------------------------------------------------------
    # Stability summary
    # ------------------------------------------------------------------
    mbb_lows = [r["m_beta_beta_meV"][0] for r in anchor_rows]
    mbb_highs = [r["m_beta_beta_meV"][1] for r in anchor_rows]
    # For the preregistered window [55, 120] meV (the paper's actual
    # prediction), collect the union of m_beta_beta ranges.
    in_window = [r for r in anchor_rows if 55.0 <= r["sum_mnu_anchor_meV"] <= 120.0]
    global_mbb_lo = min(r["m_beta_beta_meV"][0] for r in in_window)
    global_mbb_hi = max(r["m_beta_beta_meV"][1] for r in in_window)
    m3_range = [r["m_nu_meV"][2] for r in anchor_rows]
    print("\nStability summary:")
    print(f"  m_beta_beta min across anchors [{min(mbb_lows):.3f}, {max(mbb_lows):.3f}] meV")
    print(f"  m_beta_beta max across anchors [{min(mbb_highs):.3f}, {max(mbb_highs):.3f}] meV")
    print(f"  Union over preregistered window [55,120] meV: m_bb in [{global_mbb_lo:.3f}, {global_mbb_hi:.3f}] meV")
    print(f"  m_3 range across anchors: [{min(m3_range):.3f}, {max(m3_range):.3f}] meV")

    split_mbb_lo = [r["m_beta_beta_meV"][0] for r in split_rows]
    split_mbb_hi = [r["m_beta_beta_meV"][1] for r in split_rows]
    print(f"  m_beta_beta min under splittings 1-sigma: [{min(split_mbb_lo):.3f}, {max(split_mbb_lo):.3f}] meV")
    print(f"  m_beta_beta max under splittings 1-sigma: [{min(split_mbb_hi):.3f}, {max(split_mbb_hi):.3f}] meV")

    out = {
        "description": (
            "COMP-P01-C: Sensitivity of Paper 1 seesaw neutrino-sector "
            "predictions to (a) the Sigma m_nu anchor within the "
            "preregistered window [55, 120] meV, and (b) the measured "
            "mass-squared splittings within experimental 1-sigma uncertainties. "
            "The nu_R triple construction in seesaw_from_ugp_template "
            "(n_set = (10,12,16)) is held fixed.  Note: the S_3 "
            "irreducible-representation overlap construction described in the "
            "paper body is not yet implemented in code; this test "
            "characterises the implemented pipeline."
        ),
        "pmns_reference_angles_deg": pmns_angles,
        "delta_CP_used_deg_seesaw_extraction": delta_seesaw,
        "anchor_sweep": {
            "values_meV": ANCHOR_SWEEP,
            "rows": anchor_rows,
            "preregistered_window_meV": [55.0, 120.0],
            "preregistered_window_mbb_meV": [global_mbb_lo, global_mbb_hi],
        },
        "splittings_sweep": {
            "rows": split_rows,
            "anchor_meV": 60.0,
            "central_dm21_eV2": DM21_CENTRAL,
            "central_dm31_eV2": DM31_CENTRAL,
            "dm21_sigma_eV2": DM21_SIGMA,
            "dm31_sigma_eV2": DM31_SIGMA,
        },
        "summary": {
            "preregistered_mbb_bound_meV": [global_mbb_lo, global_mbb_hi],
            "central_anchor_mbb_meV": [r["m_beta_beta_meV"][0] for r in anchor_rows if r["sum_mnu_anchor_meV"] == 60.0][0:1] + [r["m_beta_beta_meV"][1] for r in anchor_rows if r["sum_mnu_anchor_meV"] == 60.0][0:1],
            "splittings_mbb_variation_meV": {
                "mbb_low_range": [min(split_mbb_lo), max(split_mbb_lo)],
                "mbb_high_range": [min(split_mbb_hi), max(split_mbb_hi)],
            },
        },
        "open_work": (
            "Implement S_3 irreducible-representation overlap construction for "
            "M_D and M_R (currently only anchor-plus-splitting pipeline is "
            "implemented) so that the prime-triple sensitivity (2,5,5), "
            "(7,11,13), (17,19,23) can be computed directly."
        ),
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    json_path = os.path.join(HERE, "nu_R_sensitivity.json")
    with open(json_path, "w") as f:
        json.dump(out, f, indent=2)
    with open(json_path, "rb") as f:
        sha = hashlib.sha256(f.read()).hexdigest()
    print(f"\nJSON output: {json_path}")
    print(f"  SHA-256: {sha}")

    # Clean up scratch dir if empty; otherwise note it for diagnosis.
    import shutil
    try:
        shutil.rmtree(_SCRATCH)
    except Exception:
        print(f"  (scratch dir left at {_SCRATCH})")

    # ------------------------------------------------------------------
    # LaTeX table (anchor sweep is the key predictive test)
    # ------------------------------------------------------------------
    bs = "\\"
    lines = [
        "% COMP-P01-C anchor sweep table",
        "% Auto-generated by nu_R_sensitivity.py",
        "\\begin{table}[H]",
        "\\centering",
        "\\caption{Sensitivity of neutrino-sector predictions to the $\\sum m_\\nu$ "
        "cosmological anchor across the preregistered window $[55, 120]$~meV. "
        "Individual masses $(m_1, m_2, m_3)$ are forced by $\\Delta m^2_{21}$ and "
        "$\\Delta m^2_{31}$ once $\\sum m_\\nu$ is specified; the $m_{\\beta\\beta}$ "
        "range is over the Majorana-phase grid at the seesaw-extracted $\\delta$. "
        "The canonical anchor used in the paper body is 60~meV.}",
        "\\label{tab:nu_sensitivity}",
        "\\renewcommand{\\arraystretch}{1.15}",
        "\\small",
        "\\begin{tabular}{@{}c c c c c c@{}}",
        "\\toprule",
        "$\\sum m_\\nu$ (meV) & $m_1$ (meV) & $m_2$ (meV) & $m_3$ (meV) & "
        "$m_{\\beta\\beta}$ (meV) & $M_{R,3}$ (GeV) \\\\",
        "\\midrule",
    ]
    for r in anchor_rows:
        s = r["sum_mnu_anchor_meV"]
        m1, m2, m3 = r["m_nu_meV"]
        lo, hi = r["m_beta_beta_meV"]
        MR3 = r["MR_GeV"][-1]
        lines.append(
            f"{s:.1f} & {m1:.3f} & {m2:.3f} & {m3:.3f} & "
            f"{lo:.2f}--{hi:.2f} & {MR3:.2e} " + bs + bs
        )
    lines += [
        "\\bottomrule",
        "\\end{tabular}",
        "\\end{table}",
        "",
    ]
    tex_path = os.path.join(HERE, "nu_R_sensitivity_table.tex")
    with open(tex_path, "w") as f:
        f.write("\n".join(lines))
    print(f"LaTeX table: {tex_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
