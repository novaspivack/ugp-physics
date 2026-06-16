#!/usr/bin/env python3
"""
comp_p25_o3_scale_probe.py — EPIC 25 O3 (Q-beta)

Re-run the SP-1A matching-scale analysis with the CORRECTED 2.39 ppm residual
(not the chimeric 0.062% from SP-1A's original run).

Also tests whether the beta-function-derived scale from O4b (Λ ≈ 0.51 MeV)
coincides with the formal QED matching point found in this new analysis.

The question (from 003_SPEC Q-β):
  "Does the SP-1A formal matching scale at Q ≈ 0.76 MeV have physical
  meaning when applied to the corrected 2.39 ppm residual rather than
  the chimeric 0.062%?"

For the corrected residual R_real = 2.39 ppm, the formal QED matching
scale is the Q such that |Δα/α|_leading-log = R_real.

Leading-log lepton contribution:
  Δ(1/α)_lepton(Q) = -(1/(3π)) × Σ_ℓ 2 log(Q/m_ℓ)  for Q > m_ℓ

Output: comp_p25_o3_scale_probe.json
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from datetime import datetime, timezone

import mpmath as mp

HERE = os.path.dirname(os.path.abspath(__file__))

mp.mp.dps = 60

ALPHA_EM = mp.mpf("0.0072973525693")
R_REAL = mp.mpf("2.39e-6")            # corrected residual

M_E   = mp.mpf("0.5109989461e-3")     # GeV
M_MU  = mp.mpf("105.6583755e-3")
M_TAU = mp.mpf("1776.86e-3")

PRE_COMMIT = {
    "purpose": "O3 Q-beta: matching-scale for corrected 2.39 ppm residual",
    "alpha_EM": str(ALPHA_EM),
    "R_real_ppm": "2.39",
    "lepton_masses_GeV": {
        "m_e": "0.5109989461e-3",
        "m_mu": "105.6583755e-3",
        "m_tau": "1776.86e-3",
    },
}
PRE_COMMIT_SHA = hashlib.sha256(
    json.dumps(PRE_COMMIT, sort_keys=True).encode()
).hexdigest()


def lepton_running(Q: mp.mpf) -> mp.mpf:
    """Leading-log lepton contribution to Δ(1/α) from q=0 to Q."""
    contrib = mp.mpf(0)
    for m in (M_E, M_MU, M_TAU):
        if Q > m:
            contrib += -(1 / (3 * mp.pi)) * 2 * mp.log(Q / m)
    return contrib


def relative_shift_alpha(Q: mp.mpf) -> mp.mpf:
    """Relative shift |Δα/α| from q=0 to Q."""
    return abs(-ALPHA_EM * lepton_running(Q))


def find_matching_scale(target: mp.mpf, lo: mp.mpf, hi: mp.mpf) -> mp.mpf:
    """Binary search for Q such that relative_shift_alpha(Q) = target."""
    for _ in range(200):
        mid = (lo + hi) / 2
        if relative_shift_alpha(mid) < target:
            lo = mid
        else:
            hi = mid
        if (hi - lo) / lo < mp.mpf("1e-12"):
            break
    return (lo + hi) / 2


def main() -> None:
    print("=" * 78)
    print("O3 Q-beta: QED matching scale for corrected 2.39 ppm residual")
    print("=" * 78)
    print(f"Pre-commit SHA-256: {PRE_COMMIT_SHA}")
    print(f"Target R_real = {float(R_REAL):.3e} ({mp.nstr(R_REAL * 1e6, 4)} ppm)")
    print()

    # Scan key scales
    scales = {
        "m_e+epsilon": M_E * mp.mpf("1.001"),
        "0.5 MeV":     mp.mpf("0.5e-3"),
        "0.51 MeV":    mp.mpf("0.51e-3"),  # O4b beta-function result
        "0.76 MeV":    mp.mpf("0.76e-3"),  # original SP-1A (chimera) formal match
        "1 MeV":       mp.mpf("1e-3"),
        "m_mu":        M_MU,
        "m_tau":       M_TAU,
        "1 GeV":       mp.mpf("1"),
        "M_Z":         mp.mpf("91.1876"),
    }
    print(f"{'scale':<16} {'Q [GeV]':>12}  {'|Δα/α|':>14}  {'ratio to R_real':>16}")
    print("-" * 70)
    rows = []
    for name, Q in scales.items():
        shift = relative_shift_alpha(Q)
        ratio = shift / R_REAL
        rows.append({"scale": name, "Q_GeV": float(Q),
                     "shift": float(shift), "ratio_to_r_real": float(ratio)})
        print(f"{name:<16} {float(Q):>12.4g}  {float(shift):>14.4e}  {float(ratio):>16.3f}×")

    # Find formal matching scale for corrected residual
    Q_match_corr = find_matching_scale(R_REAL,
                                       M_E * mp.mpf("1.001"),
                                       mp.mpf("1e3"))
    print()
    print(f"Formal matching scale for 2.39 ppm (corrected): Q = {mp.nstr(Q_match_corr * 1000, 6)} MeV")

    # Comparison to O4b result (0.51 MeV)
    Q_o4b = mp.mpf("0.51e-3")
    shift_o4b = relative_shift_alpha(Q_o4b)
    print(f"O4b beta-function scale (0.51 MeV): |Δα/α| = {mp.nstr(shift_o4b * 1e6, 4)} ppm")
    print(f"Ratio O4b scale / corrected formal scale: {mp.nstr(Q_o4b / Q_match_corr, 4)}")

    cert = {
        "description": "O3 Q-beta: QED matching scale for corrected 2.39 ppm residual",
        "pre_commit_sha256": PRE_COMMIT_SHA,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "target_ppm": 2.39,
        "scale_scan": rows,
        "formal_matching_scale_MeV": float(Q_match_corr * 1000),
        "o4b_beta_function_scale_MeV": 0.51,
        "ratio_o4b_to_formal": float(Q_o4b / Q_match_corr),
    }
    out_path = os.path.join(HERE, "comp_p25_o3_scale_probe.json")
    with open(out_path, "w") as f:
        json.dump(cert, f, indent=2)
    sha = hashlib.sha256(open(out_path, "rb").read()).hexdigest()
    print(f"\nArtifact:           {os.path.basename(out_path)}")
    print(f"Artifact SHA-256:   {sha}")
    print(f"Pre-commit SHA-256: {PRE_COMMIT_SHA}")


if __name__ == "__main__":
    main()
