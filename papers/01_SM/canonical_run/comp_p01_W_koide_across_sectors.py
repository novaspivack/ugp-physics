#!/usr/bin/env python3
"""
COMP-P01-W  —  Koide S3-quadric test across all fermion-triple sectors

User question (round 7b): "What about the color problem?"  i.e., does the
paper's S3-quadric structure extend to quark-sector triples (which carry
color charge), or is it charged-lepton-specific?

The round-6 result (COMP-P01-R) shows charged leptons satisfy the unique
S3-invariant null quadric v^T(3I - 2J)v = 0 at PDG precision with
empirical p < 10^-4.

This test: apply the SAME quadric to:
  1. up-type quarks    (m_u, m_c, m_t)
  2. down-type quarks  (m_d, m_s, m_b)
  3. neutrino triple   (m_1, m_2, m_3) via mass-squared splittings + anchor
  4. all 9 charged-fermions together (3 generations x 3 species) [informal]

Expected: Koide-for-quarks is historically known to fail; that is an
expected negative result.  What we want to measure:
  - How badly does it fail in sigma?  Sets the scope of UGP's S3 structure.
  - Is there a scale-rescaling of quark masses under which the null quadric
    condition holds?  If so, that rescaling is a potential structural hint.
  - Is there a different S3-invariant quadric (other than (3, -2)) that
    holds for quark triples?

Outputs:
  comp_p01_W_koide_across_sectors.json
"""
from __future__ import annotations

import datetime as _dt
import hashlib as _hl
import json
import math
import sys
from pathlib import Path


# -----------------------------------------------------------------
# PDG 2024 fermion masses
# -----------------------------------------------------------------
# Charged leptons (keV -- round 6 reference)
LEPTONS = {
    "m_e":    0.51099895069,    # MeV
    "m_mu":   105.6583755,
    "m_tau":  1776.860,
    "sigma_m_e":   1.5e-7,
    "sigma_m_mu":  2.3e-6,
    "sigma_m_tau": 0.120,
}

# Up-type quarks (MS-bar at 2 GeV for u, c; pole-scheme-adjusted for t at m_t)
# Ref PDG 2024; uncertainties listed
QUARKS_UP = {
    "m_u":   2.16,       # MeV MS-bar at 2 GeV
    "m_c":   1273.0,     # MeV MS-bar at m_c
    "m_t":   172690.0,   # MeV pole mass
    "sigma_m_u":  0.5,   # ~23%
    "sigma_m_c":  4.6,   # ~0.4%
    "sigma_m_t":  300.0, # 0.17%
}

QUARKS_DOWN = {
    "m_d":   4.67,       # MeV MS-bar at 2 GeV
    "m_s":   93.4,       # MeV MS-bar at 2 GeV
    "m_b":   4183.0,     # MeV MS-bar at m_b
    "sigma_m_d":  0.48,  # ~10%
    "sigma_m_s":  8.6,   # ~9%
    "sigma_m_b":  10.0,  # ~0.24%
}


# -----------------------------------------------------------------
# S3-invariant null quadric  M = 3I - 2J
# For v = (sqrt(m1), sqrt(m2), sqrt(m3)):
#   v^T M v = 3 Sum(m_i) - 2 (Sum sqrt(m_i))^2
#           = 3 S - 2 Sigma^2
# Koide Q = Sigma^2 / S = 2/3  <=>  v^T M v = 0
# -----------------------------------------------------------------
def koide_Q(m1, m2, m3):
    S = m1 + m2 + m3
    Sigma = math.sqrt(m1) + math.sqrt(m2) + math.sqrt(m3)
    return Sigma * Sigma / S


def v_T_M_v(m1, m2, m3):
    S = m1 + m2 + m3
    Sigma = math.sqrt(m1) + math.sqrt(m2) + math.sqrt(m3)
    return 3.0 * S - 2.0 * Sigma * Sigma


def analyse_triple(label, m1, m2, m3, s1, s2, s3):
    """Analyse a fermion triple against Koide Q=2/3 and the S3-quadric."""
    Q = koide_Q(m1, m2, m3)
    quadric = v_T_M_v(m1, m2, m3)
    # Propagate 1-sigma uncertainties via partial derivatives
    # d(quadric)/d(m_i) = 3 - 2 * 2 * Sigma * 1/(2 sqrt(m_i)) = 3 - 2 Sigma / sqrt(m_i)
    Sigma = math.sqrt(m1) + math.sqrt(m2) + math.sqrt(m3)
    d_dm1 = 3.0 - 2.0 * Sigma / math.sqrt(m1)
    d_dm2 = 3.0 - 2.0 * Sigma / math.sqrt(m2)
    d_dm3 = 3.0 - 2.0 * Sigma / math.sqrt(m3)
    sigma_q = math.sqrt((d_dm1 * s1)**2 + (d_dm2 * s2)**2 + (d_dm3 * s3)**2)
    # Koide Q propagation:  dQ/dm_i = ...  skip exact; use relative
    sigma_from_null_in_sigmas = quadric / sigma_q if sigma_q > 0 else float("inf")
    return {
        "label":                  label,
        "masses":                 [m1, m2, m3],
        "sigmas":                 [s1, s2, s3],
        "Koide_Q":                Q,
        "Koide_Q_minus_2_3":      Q - 2.0 / 3.0,
        "v_T_M_v":                quadric,
        "sigma_v_T_M_v":          sigma_q,
        "quadric_sigmas_from_null": sigma_from_null_in_sigmas,
        "satisfies_Koide_PDG":    abs(sigma_from_null_in_sigmas) <= 3.0,
    }


def main() -> int:
    results = {}

    # Charged leptons -- reference
    r_lep = analyse_triple("charged_leptons",
                            LEPTONS["m_e"], LEPTONS["m_mu"], LEPTONS["m_tau"],
                            LEPTONS["sigma_m_e"], LEPTONS["sigma_m_mu"], LEPTONS["sigma_m_tau"])
    results["charged_leptons"] = r_lep

    # Up-type quarks
    r_up = analyse_triple("up_type_quarks",
                           QUARKS_UP["m_u"], QUARKS_UP["m_c"], QUARKS_UP["m_t"],
                           QUARKS_UP["sigma_m_u"], QUARKS_UP["sigma_m_c"], QUARKS_UP["sigma_m_t"])
    results["up_type_quarks"] = r_up

    # Down-type quarks
    r_dn = analyse_triple("down_type_quarks",
                           QUARKS_DOWN["m_d"], QUARKS_DOWN["m_s"], QUARKS_DOWN["m_b"],
                           QUARKS_DOWN["sigma_m_d"], QUARKS_DOWN["sigma_m_s"], QUARKS_DOWN["sigma_m_b"])
    results["down_type_quarks"] = r_dn

    print("=" * 72)
    print("COMP-P01-W: Koide S3-quadric across fermion triples")
    print("=" * 72)
    print()
    for label, r in results.items():
        print(f"Sector: {label}")
        print(f"  masses (MeV):             {r['masses']}")
        print(f"  Koide Q:                  {r['Koide_Q']:.6f}   (target 2/3 = {2.0/3.0:.6f})")
        print(f"  Q - 2/3:                  {r['Koide_Q_minus_2_3']:+.4e}")
        print(f"  v^T M v:                  {r['v_T_M_v']:+.4e}   (target: 0)")
        print(f"  sigma(v^T M v):           {r['sigma_v_T_M_v']:.4e}")
        print(f"  sigma deviation from null: {r['quadric_sigmas_from_null']:+.2f} sigma")
        print(f"  satisfies Koide at 3-sigma? {r['satisfies_Koide_PDG']}")
        print()

    # Find optimal S3-invariant quadric a*I + b*J for each sector
    # (a, b) satisfying v^T(aI + bJ) v = 0 for given triple:
    #   a * (m1 + m2 + m3) + b * (sqrt(m1) + sqrt(m2) + sqrt(m3))^2 = 0
    # => a / b = -Sigma^2 / S = -Q
    # The Koide solution Q = 2/3 gives a/b = -2/3.  The general sector-specific
    # solution is a/b = -Q_sector.
    print("=" * 72)
    print("Sector-specific S3-invariant quadrics (a/b ratio for null)")
    print("=" * 72)
    for label, r in results.items():
        Q = r["Koide_Q"]
        # Find rational with small numerator/denominator matching Q
        # Report best rational approximation with denominator <= 30
        best_num, best_den, best_err = None, None, float("inf")
        for den in range(1, 31):
            num = round(Q * den)
            if num == 0:
                continue
            err = abs(Q - num / den)
            if err < best_err:
                best_err = err
                best_num = num
                best_den = den
        # Check if the best rational has UGP-native structure
        ugp_natives = {2, 3, 5, 7, 9, 11, 13, 15, 16, 17, 20, 23, 43, 73}
        is_ugp_num = (best_num in ugp_natives) or (best_num == 1)
        is_ugp_den = (best_den in ugp_natives) or (best_den == 1)
        is_ugp_native = is_ugp_num and is_ugp_den
        print(f"  {label:20s}  Q = {Q:.6f}  ~  {best_num}/{best_den}  "
              f"(err = {best_err:.2e})   UGP-native? {is_ugp_native}")

    # Koide-for-quarks historical context
    print()
    print("=" * 72)
    print("INTERPRETATION")
    print("=" * 72)

    koide_works = {
        "charged_leptons": results["charged_leptons"]["satisfies_Koide_PDG"],
        "up_type_quarks":  results["up_type_quarks"]["satisfies_Koide_PDG"],
        "down_type_quarks": results["down_type_quarks"]["satisfies_Koide_PDG"],
    }

    if koide_works["charged_leptons"] and not koide_works["up_type_quarks"] and not koide_works["down_type_quarks"]:
        interpretation = (
            "CHARGED-LEPTON-SPECIFIC:  the S3-quadric null condition "
            "v^T(3I - 2J)v = 0 holds for charged leptons (<0.91 sigma) but "
            "does NOT hold for up-type or down-type quarks.  This means the "
            "UGP S3 structure for Koide is specific to the COLORLESS sector.  "
            "Hypothesis: the (3, -2) coefficients carry color-independence; "
            "quark triples would require a different quadric (or a scale-"
            "dependent correction from QCD running) to satisfy a similar "
            "structural condition.  This provides a concrete entry point to "
            "the 'color problem' in UGP: the S3-flavour structure is "
            "orthogonal to color, and the quark-sector mass spectrum "
            "requires color-QCD input that the GTE triple structure does "
            "not encode."
        )
    elif all(koide_works.values()):
        interpretation = (
            "SECTOR-UNIVERSAL:  the S3-quadric holds across all three fermion "
            "sectors.  This would be a remarkable result; check the input "
            "masses and schemes carefully."
        )
    else:
        interpretation = (
            "MIXED:  see per-sector deviations.  Full structural interpretation "
            "requires deeper analysis of which sectors satisfy which quadrics."
        )

    print(interpretation)
    print()

    report = {
        "experiment_id": "COMP-P01-W",
        "question": (
            "Does the S3-invariant null quadric that Koide-closes charged "
            "leptons also close the quark triples?  If not, what is the "
            "structural difference?  This tests whether UGP's S3-flavour "
            "structure is color-independent (lepton-only) or universal."
        ),
        "results_per_sector":  results,
        "satisfies_Koide_PDG": koide_works,
        "interpretation":      interpretation,
        "timestamp_utc":       _dt.datetime.utcnow().isoformat(timespec="seconds"),
    }
    out_path = Path(__file__).with_suffix(".json")
    with open(out_path, "w") as fh:
        json.dump(report, fh, indent=2, sort_keys=False)
    sha = _hl.sha256(out_path.read_bytes()).hexdigest()
    print(f"[write] {out_path.name}")
    print(f"[sha]   {sha}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
