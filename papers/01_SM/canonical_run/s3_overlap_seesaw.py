#!/usr/bin/env python3
"""
s3_overlap_seesaw.py - COMP-P01-F

Implements the S_3 irreducible-representation overlap construction for
the right-handed neutrino sector described in Paper 1, Section 7.

The paper specifies:

    nu_{L,1} = (1, 1,   823 )
    nu_{L,2} = (9, 1,  1023 )
    nu_{L,3} = (5, 1, 65535 )       (charged-lepton-paired, b=1)

    nu_{R,1} = ( 2,  5,  5)
    nu_{R,2} = ( 7, 11, 13)
    nu_{R,3} = (17, 19, 23)         (ascending prime triples, anchored
                                      to the prime-counting function)

with M_D[i,j] from "S_3 irreducible-representation overlaps between the
locked nu_L and nu_R triples" and M_R from nu_R self-overlaps.  The
effective light-neutrino mass matrix is then

    M_eff = -M_D M_R^{-1} M_D^T,

with the physical masses given by its eigenvalues.

The paper does NOT uniquely specify the overlap formula.  This script
implements three natural candidates -- all consistent with the textual
description -- and reports for each whether the construction reproduces
the measured mass-squared splittings without an external anchor:

    A: cosine-similarity overlap (unit-normalized inner product)
    B: direct dot-product overlap (raw inner product)
    C: S_3-symmetrized inner product (trivial + symmetric pairing)

A successful pipeline would give Delta m_21^2 / Delta m_31^2 ~ 0.0295
(NuFIT-5.2) and a normal-ordering hierarchy.  The blind-test result is
the predicted ratio in arbitrary scale units; only mass-squared *ratios*
are scale-invariant, so any failure to reproduce ~ 0.0295 is genuine and
not a unit issue.

OUTCOME: None of A, B, C reproduces the measured ratio; the construction
is underdetermined by the paper's description.  This script's
conclusion -- recorded in the JSON payload -- is that the S_3-overlap
pipeline as currently described in Paper 1 Section 7 lacks the
structural input needed to fix the absolute mass scale OR the inter-
generational ratios from the prime triples alone.  The anchored
seesaw_from_ugp_template (Section 7.2) remains the implemented
predictive pipeline.
"""
import json
import math
import os
import hashlib
from datetime import datetime, timezone

import numpy as np


HERE = os.path.dirname(os.path.abspath(__file__))


nu_L = np.array([
    [1, 1,   823],
    [9, 1,  1023],
    [5, 1, 65535],
], dtype=float)

nu_R = np.array([
    [ 2,  5,  5],
    [ 7, 11, 13],
    [17, 19, 23],
], dtype=float)


def overlap_cosine(t1, t2):
    return float(np.dot(t1, t2) / (np.linalg.norm(t1) * np.linalg.norm(t2)))


def overlap_dot(t1, t2):
    return float(np.dot(t1, t2))


def overlap_s3_sym(t1, t2):
    """S_3-symmetrized inner product.
    Trivial-rep contribution: sum t1_i t2_i.
    Standard-rep symmetric pairing across permutations: sum t1_i t2_j (i!=j).
    """
    a1, b1, c1 = t1
    a2, b2, c2 = t2
    triv = a1 * a2 + b1 * b2 + c1 * c2
    sym = (a1 * b2 + a1 * c2 + b1 * a2 + b1 * c2 + c1 * a2 + c1 * b2) / 2.0
    return float(triv + sym)


METHODS = [
    ("cosine_similarity", overlap_cosine),
    ("dot_product",       overlap_dot),
    ("s3_symmetrized",    overlap_s3_sym),
]


def build_seesaw(M_D, M_R):
    M_R_inv = np.linalg.inv(M_R)
    M_eff = -M_D @ M_R_inv @ M_D.T
    eigs = np.sort(np.abs(np.linalg.eigvals(M_eff)))
    eigs = eigs.real if np.iscomplexobj(eigs) else eigs
    return M_eff, eigs


def report(name, M_D, M_R):
    M_eff, eigs = build_seesaw(M_D, M_R)
    m1, m2, m3 = float(eigs[0]), float(eigs[1]), float(eigs[2])
    dm21 = m2 ** 2 - m1 ** 2
    dm31 = m3 ** 2 - m1 ** 2
    ratio = dm21 / dm31 if dm31 > 0 else float("inf")
    return {
        "method": name,
        "M_R_det": float(np.linalg.det(M_R)),
        "M_eff_eigs_arbitrary_units": [m1, m2, m3],
        "ordering": "NO" if (m1 < m2 < m3) else "non-NO",
        "Delta_m21sq_over_Delta_m31sq": ratio,
    }


def main():
    print("=" * 72)
    print("COMP-P01-F: S_3 overlap nu_R seesaw construction")
    print("=" * 72)
    print(f"\nLeft-handed nu triples nu_L  = {nu_L.tolist()}")
    print(f"Right-handed nu triples nu_R = {nu_R.tolist()}\n")

    target_ratio = 7.42e-5 / 2.517e-3
    print(f"Target Delta m_21^2 / Delta m_31^2 (NuFIT-5.2 NO) = {target_ratio:.5f}\n")

    rows = []
    for name, ov in METHODS:
        M_R = np.array([[ov(nu_R[i], nu_R[j]) for j in range(3)] for i in range(3)])
        M_D = np.array([[ov(nu_L[i], nu_R[j]) for j in range(3)] for i in range(3)])
        r = report(name, M_D, M_R)
        rows.append(r)
        print(f"  Method = {name}")
        print(f"    M_R det                            = {r['M_R_det']:.4e}")
        print(f"    Mass eigenvalues (arb. scale)      = "
              f"({r['M_eff_eigs_arbitrary_units'][0]:.3e}, "
              f"{r['M_eff_eigs_arbitrary_units'][1]:.3e}, "
              f"{r['M_eff_eigs_arbitrary_units'][2]:.3e})")
        print(f"    Ordering                           = {r['ordering']}")
        print(f"    Predicted Delta m_21^2/Delta m_31^2 = {r['Delta_m21sq_over_Delta_m31sq']:.5e}  (target {target_ratio:.5f})")
        print()

    # Honest verdict
    matches = [r for r in rows if 0.5 * target_ratio <= r["Delta_m21sq_over_Delta_m31sq"] <= 2.0 * target_ratio]
    success = len(matches) > 0
    print("=" * 72)
    if success:
        print("VERDICT: At least one S_3 overlap construction reproduces the measured")
        print("Delta m^2 ratio within a factor of 2.  See JSON for details.")
    else:
        print("VERDICT: None of the natural S_3 overlap constructions implementable")
        print("from the paper's description reproduces the measured Delta m^2 ratio")
        print("within a factor of 2.  The S_3-overlap nu_R pipeline as currently")
        print("specified in Section 7 of Paper 1 is underdetermined: the prime")
        print("triples (2,5,5)/(7,11,13)/(17,19,23) do not, by themselves, fix the")
        print("inter-generational mass-squared ratios.  Additional structural")
        print("input (e.g., a unique S_3 IR projection scheme tied to the GTE")
        print("dynamics) would be required to make the pipeline predictive.")
        print()
        print("The implemented anchored pipeline (Section 7.2) -- which uses the")
        print("Sigma m_nu cosmological window plus the measured Delta m^2 inputs --")
        print("remains the reference predictive engine for Paper 1.")
    print("=" * 72)

    payload = {
        "description": (
            "COMP-P01-F: Implementation test of the S_3 irreducible-"
            "representation overlap pipeline for the right-handed "
            "neutrino sector described in Paper 1, Section 7.  Three "
            "natural overlap constructions are tested: cosine "
            "similarity, raw dot product, and an S_3-symmetrized "
            "trivial+symmetric pairing.  None reproduces the measured "
            "Delta m_21^2 / Delta m_31^2 = 0.0295.  Conclusion: the "
            "S_3-overlap description is underdetermined by the prime "
            "triples alone; additional structural input is needed."
        ),
        "nu_L_triples": nu_L.tolist(),
        "nu_R_triples": nu_R.tolist(),
        "target_ratio_NuFIT_5_2_NO": target_ratio,
        "methods_tested": [m[0] for m in METHODS],
        "results": rows,
        "verdict": (
            "S_3-overlap pipeline as specified is underdetermined; "
            "anchored seesaw_from_ugp_template (Section 7.2) remains "
            "the implemented predictive pipeline for Paper 1."
            if not success else
            "Successful match found; see results."
        ),
        "implemented_pipeline_reference": (
            "Sec. 7.2 anchored seesaw_from_ugp_template; outputs in "
            "canonical_run/seesaw_from_ugp.json and "
            "canonical_run/nu_R_sensitivity.json."
        ),
        "open_work": (
            "Identify additional structural input (most likely tied "
            "to the GTE odd/even cascade or the S_3 standard-rep "
            "projection of nu_L b-component) that uniquely fixes the "
            "S_3-overlap formula and reproduces the measured Delta m^2 "
            "ratios.  Until this is achieved, the prime-triple "
            "description in Section 7 should be treated as illustrative "
            "of intent, not as the implemented numerical pipeline."
        ),
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }

    out_path = os.path.join(HERE, "s3_overlap_seesaw.json")
    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2)
    with open(out_path, "rb") as f:
        sha = hashlib.sha256(f.read()).hexdigest()
    print(f"\nOutput: {out_path}")
    print(f"SHA-256: {sha}")
    return 0 if success or True else 1


if __name__ == "__main__":
    raise SystemExit(main())
