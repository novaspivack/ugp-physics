"""
Standalone verification of the Information Profit Threshold (IPT) derivation.

Computes phi, Lambda, and IPT from closed-form expressions, verifies the
numerical values, and saves results to results/ipt_derivation_verification.json.

The Information Profit Threshold is:

    IPT = 1 + Lambda / 2,    Lambda = ln(phi) / ln(2*pi)

where phi = (1 + sqrt(5)) / 2 is the golden ratio.

Numerically: IPT ≈ 1.1309151921
"""

import json
import math
import os


TOLERANCE = 1e-4
EXPECTED_IPT_APPROX = 1.1309


def compute_ipt():
    phi = (1.0 + math.sqrt(5.0)) / 2.0
    ln_phi = math.log(phi)
    ln_2pi = math.log(2.0 * math.pi)
    lam = ln_phi / ln_2pi
    ipt = 1.0 + lam / 2.0
    return phi, ln_phi, ln_2pi, lam, ipt


def verify_ipt(ipt):
    return abs(ipt - EXPECTED_IPT_APPROX) < TOLERANCE


def main():
    phi, ln_phi, ln_2pi, lam, ipt = compute_ipt()

    print("=== Information Profit Threshold Derivation Verification ===")
    print(f"phi      = {phi:.10f}")
    print(f"ln(phi)  = {ln_phi:.10f}")
    print(f"ln(2*pi) = {ln_2pi:.10f}")
    print(f"Lambda   = {lam:.10f}")
    print(f"Lambda/2 = {lam / 2.0:.10f}")
    print(f"IPT      = {ipt:.10f}")

    passed = verify_ipt(ipt)
    status = "PASS" if passed else "FAIL"
    print(
        f"{status}: IPT = {ipt:.10f} is "
        + ("within" if passed else "NOT within")
        + f" {TOLERANCE:.0e} of {EXPECTED_IPT_APPROX}"
    )

    result = {
        "phi": phi,
        "ln_phi": ln_phi,
        "ln_2pi": ln_2pi,
        "Lambda": lam,
        "Lambda_over_2": lam / 2.0,
        "IPT": ipt,
        "expected_approx": EXPECTED_IPT_APPROX,
        "tolerance": TOLERANCE,
        "verification_passed": passed,
        "note": (
            "IPT = 1 + ln(phi) / (2 * ln(2*pi)) where phi is the golden ratio. "
            "This is a closed-form derivation; all values are exact to float64 precision."
        ),
    }

    os.makedirs("results", exist_ok=True)
    out_path = os.path.join("results", "ipt_derivation_verification.json")
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"Result saved to {out_path}")

    if not passed:
        raise AssertionError(
            f"Verification failed: IPT = {ipt:.10f}, expected within {TOLERANCE} of {EXPECTED_IPT_APPROX}"
        )


if __name__ == "__main__":
    main()
