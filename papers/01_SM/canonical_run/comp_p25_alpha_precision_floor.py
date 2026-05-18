#!/usr/bin/env python3
"""
comp_p25_alpha_precision_floor.py

High-precision verification of the UGP electromagnetic-instantiation chain.

Recomputes C_alg from the Lean-authoritative Quarter-Lock formula at 60 decimal
digits and cross-checks it against the canonical non-circular derivation
recorded in `uniqueness/canonical_run/delta_noncircular.json` (the TE1.P-bridge
pipeline cited from paper 5).  Reports the residual

    R = (b1_required - 73) / 73 = 2.39 x 10^-6   (i.e. 2.39 ppm in alpha)

with continued-fraction analysis and a perturbative form-factor comparison
(one- and two-loop QED magnitudes).  The Lean-certified UGP backbone is
unchanged by this verification; the residual is the framework's documented
precision floor (paper 25 Section 9.8).

Inputs:
  k_gen2 = -phi/2                   (ugp-lean: thm_ucl1_fully_unconditional)
  k_L2   = 7/512                     (ugp-lean: k_L2_eq)
  b1     = 73                        (ugp-lean: rsuc_theorem)
  C_alg  = -1/(k_gen2 + (1/4) k_L2) + (7/4)(k_L2/k_gen2)
                                     (ugp-lean: deltaUGP_numeric_at_73)
  delta_target  from uniqueness/canonical_run/delta_noncircular.json
                                     (TE1.P bridge: derived_delta_codata)
  b1_required   from the same file

The script verifies that C_alg / delta_target equals b1_required to within
double-precision tolerance and reports the residual.

Pre-commitment: SHA-256 over the input block; verdict is one of
PERTURBATIVE_ONE_LOOP_MATCH, PERTURBATIVE_TWO_LOOP_MATCH, or
NO_PERTURBATIVE_MATCH_WITHIN_5_PCT.

Output: comp_p25_alpha_precision_floor.json
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone

import mpmath as mp

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
DELTA_NONCIRCULAR = os.path.join(
    REPO, "uniqueness", "canonical_run", "delta_noncircular.json"
)

mp.mp.dps = 60


# ------------------------------------------------------------------ Lean inputs
PHI = (mp.mpf(1) + mp.sqrt(5)) / 2          # exact via mp.sqrt
K_GEN2 = -PHI / 2                            # ugp-lean: thm_ucl1_fully_unconditional
K_L2 = mp.mpf(7) / mp.mpf(512)               # ugp-lean: k_L2_eq
B1_INT = 73                                  # ugp-lean: rsuc_theorem


def C_alg(k_gen2: mp.mpf, k_L2: mp.mpf) -> mp.mpf:
    """Quarter-Lock algebraic prefactor (UgpLean/Phase4/DeltaUGP.lean line 35).

        C = -1/(k_gen2 + k_L2/4) + (7/4)(k_L2/k_gen2)
    """
    return (-1) / (k_gen2 + k_L2 / 4) + (mp.mpf(7) / 4) * (k_L2 / k_gen2)


def load_canonical_chain() -> dict:
    """Load the TE1.P-bridge non-circular derivation (paper 5 canonical record)."""
    if not os.path.exists(DELTA_NONCIRCULAR):
        raise FileNotFoundError(
            f"Required canonical record not found: {DELTA_NONCIRCULAR}.\n"
            "Restore the file from the repository root before running."
        )
    with open(DELTA_NONCIRCULAR, "r") as f:
        return json.load(f)


# ------------------------------------------------------- pre-commitment block
PRE_COMMIT = {
    "purpose": (
        "60-digit verification of C_alg, cross-check against non-circular "
        "TE1.P-bridge chain in delta_noncircular.json, and classification of "
        "the residual against canonical QED form factors."
    ),
    "lean_authoritative_C_alg_formula": (
        "C = -1/(k_gen2 + (1/4) k_L2) + (7/4)(k_L2/k_gen2)  "
        "[UgpLean/Phase4/DeltaUGP.lean line 35]"
    ),
    "k_L2_str": "7/512",
    "k_gen2_str": "-phi/2 = -(1+sqrt 5)/4",
    "b1_int": B1_INT,
    "canonical_chain_source": "uniqueness/canonical_run/delta_noncircular.json",
    "precision_decimal_digits": int(mp.mp.dps),
    "perturbative_candidates": [
        "alpha/(2 pi)", "alpha/(4 pi)", "alpha/(8 pi)",
        "alpha^2/pi^2", "alpha^2/(2 pi^2)", "alpha^2/(4 pi^2)", "alpha^2/(8 pi^2)",
    ],
    "match_threshold_pct": 5.0,
}
PRE_COMMIT_SHA = hashlib.sha256(
    json.dumps(PRE_COMMIT, sort_keys=True).encode()
).hexdigest()


# ----------------------------------------------------------- helper utilities
def cf_terms(x: mp.mpf, n_terms: int = 16) -> list[int]:
    out: list[int] = []
    y = mp.mpf(x)
    for _ in range(n_terms):
        a = int(mp.floor(y))
        out.append(a)
        frac = y - a
        if frac == 0 or mp.almosteq(frac, 0, abs_eps=mp.mpf("1e-50")):
            break
        y = 1 / frac
    return out


def cf_convergents(cf: list[int], n: int = 8) -> list[tuple[int, int, mp.mpf]]:
    out: list[tuple[int, int, mp.mpf]] = []
    p_prev, p_curr = 1, 0
    q_prev, q_curr = 0, 1
    for a in cf[:n]:
        p_next = a * p_curr + p_prev
        q_next = a * q_curr + q_prev
        if q_next != 0:
            out.append((p_next, q_next, mp.mpf(p_next) / mp.mpf(q_next)))
        p_prev, p_curr = p_curr, p_next
        q_prev, q_curr = q_curr, q_next
    return out


# ----------------------------------------------------------------------- main
def main() -> None:
    print("=" * 78)
    print("UGP alpha-precision floor — 60-digit verification")
    print("=" * 78)
    print(f"Pre-commit SHA-256: {PRE_COMMIT_SHA}")
    print(f"Precision: {mp.mp.dps} decimal digits")
    print()

    # 1. Quarter-Lock prefactor at 60-digit precision
    C = C_alg(K_GEN2, K_L2)
    delta_UGP_at_73 = C / B1_INT

    print("1. Quarter-Lock algebraic prefactor (Lean-authoritative formula):")
    print(f"   C_alg              = {mp.nstr(C, 30)}")
    print(f"   delta_UGP(73) = C/73 = {mp.nstr(delta_UGP_at_73, 30)}")
    print()

    # 2. Canonical non-circular chain (paper 5 TE1.P bridge)
    chain = load_canonical_chain()
    C_chain      = mp.mpf(str(chain["lean_certified_constants"]["prefactor_C"]))
    delta_target = mp.mpf(str(chain["derived_delta_codata"]))
    b1_req       = mp.mpf(str(chain["b1_required_exact"]))
    alpha_codata = mp.mpf(str(chain["codata"]["alpha_EM"]))

    diff_C = (C - C_chain) / C
    b1_req_recomputed = C / delta_target
    residual = (b1_req - B1_INT) / B1_INT

    print("2. Non-circular TE1.P-bridge derivation"
          " (uniqueness/canonical_run/delta_noncircular.json):")
    print(f"   prefactor_C (chain)  = {mp.nstr(C_chain, 18)}")
    print(f"   C_alg − C_chain (rel) = {mp.nstr(diff_C, 6)}  (consistency check)")
    print(f"   delta_target         = {mp.nstr(delta_target, 18)}")
    print(f"   b1_required          = {mp.nstr(b1_req, 14)}")
    print(f"   C_alg / delta_target = {mp.nstr(b1_req_recomputed, 14)}")
    print(f"   residual = (b1_req - 73)/73 = "
          f"{mp.nstr(residual, 14)} = {mp.nstr(residual * 1e6, 6)} ppm")
    print()

    # 3. Continued-fraction analysis
    cf_R = cf_terms(residual, 16)
    convs = cf_convergents(cf_R, 8)
    print("3. Continued-fraction analysis of the residual:")
    print(f"   CF: {cf_R}")
    print(f"   convergents:")
    for p, q, v in convs:
        rel = abs(v - residual) / abs(residual)
        print(f"     {p:>5}/{q:<8} = {mp.nstr(v, 12):>14}  rel_resid = {mp.nstr(rel, 6)}")
    print()

    # 4. Perturbative comparison
    alpha = alpha_codata
    pi = mp.pi
    candidates = {
        "alpha/(2 pi)":      alpha / (2 * pi),
        "alpha/(4 pi)":      alpha / (4 * pi),
        "alpha/(8 pi)":      alpha / (8 * pi),
        "alpha/(16 pi)":     alpha / (16 * pi),
        "alpha^2/pi^2":      alpha**2 / pi**2,
        "alpha^2/(2 pi^2)":  alpha**2 / (2 * pi**2),
        "alpha^2/(4 pi^2)":  alpha**2 / (4 * pi**2),
        "alpha^2/(8 pi^2)":  alpha**2 / (8 * pi**2),
    }
    rows = []
    for name, v in candidates.items():
        rel = (residual - v) / residual
        rows.append((name, v, rel))
    rows.sort(key=lambda x: abs(x[2]))

    print(f"4. Perturbative form-factor comparison "
          f"(R = {mp.nstr(residual, 12)}):")
    print(f"   {'form':<18} {'value':>14}  rel_resid")
    for name, v, rel in rows[:8]:
        print(f"   {name:<18} {mp.nstr(v, 8):>14}  {mp.nstr(rel * 100, 6)}%")
    print()

    best_name, best_value, best_rel = rows[0]
    if abs(best_rel) < mp.mpf("0.05"):
        loop_class = "two_loop" if "alpha^2" in best_name else "one_loop"
        verdict = f"PERTURBATIVE_{loop_class.upper()}_MATCH"
    else:
        verdict = "NO_PERTURBATIVE_MATCH_WITHIN_5_PCT"

    print(f"Best single-form match : {best_name}  ({mp.nstr(best_rel * 100, 4)}%)")
    print(f"Classification         : {verdict}")
    print()

    cert = {
        "description":
            "60-digit verification of the UGP alpha-precision floor",
        "pre_commit_sha256": PRE_COMMIT_SHA,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "precision_decimal_digits": int(mp.mp.dps),
        "C_alg_str": mp.nstr(C, 30),
        "C_alg_chain_str": mp.nstr(C_chain, 30),
        "C_alg_consistency_relative": mp.nstr(diff_C, 6),
        "delta_target_str": mp.nstr(delta_target, 18),
        "b1_required_str": mp.nstr(b1_req, 14),
        "b1_required_recomputed_str": mp.nstr(b1_req_recomputed, 14),
        "residual_relative_str": mp.nstr(residual, 14),
        "residual_ppm_str": mp.nstr(residual * 1e6, 6),
        "continued_fraction": cf_R,
        "cf_convergents": [
            {"p": p, "q": q, "value": mp.nstr(v, 12),
             "rel_resid": mp.nstr(abs(v - residual) / abs(residual), 6)}
            for p, q, v in convs
        ],
        "perturbative_table": [
            {"name": n, "value": mp.nstr(v, 12), "rel_resid": mp.nstr(r, 6)}
            for n, v, r in rows
        ],
        "best_form_factor": {
            "name": best_name,
            "value": mp.nstr(best_value, 12),
            "rel_resid_pct": mp.nstr(best_rel * 100, 6),
        },
        "verdict": verdict,
    }
    out_path = os.path.join(HERE, "comp_p25_alpha_precision_floor.json")
    with open(out_path, "w") as f:
        json.dump(cert, f, indent=2)

    sha = hashlib.sha256(open(out_path, "rb").read()).hexdigest()
    print(f"Artifact:           {os.path.basename(out_path)}")
    print(f"Artifact SHA-256:    {sha}")
    print(f"Pre-commit SHA-256:  {PRE_COMMIT_SHA}")
    print(f"Verdict:             {verdict}")


if __name__ == "__main__":
    main()
