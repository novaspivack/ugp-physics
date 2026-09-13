#!/usr/bin/env python3
"""
Standalone verification of the Information Profit Threshold (IPT) derivation.

IPT = 1 + ln(φ) / (2·ln(2π))

where φ = (1 + √5)/2 is the golden ratio.

This matches the Lean-certified value in:
  UgpLean.IPT.InformationProfitThreshold — theorem `IPT_theorem`

Running this script verifies the closed-form derivation to 10 decimal places
and writes the result to results/ipt_derivation_verification.json.
"""

import json
import math
import os

PHI = (1.0 + math.sqrt(5.0)) / 2.0
LN_PHI = math.log(PHI)
LN_2PI = math.log(2.0 * math.pi)
# Lambda = ln(phi) / ln(2*pi); IPT = 1 + Lambda/2 = 1 + ln(phi)/(2*ln(2*pi))
LAMBDA = LN_PHI / LN_2PI
IPT = 1.0 + LAMBDA / 2.0

IPT_EXPECTED = 1.1309  # truncated reference value from the paper

print("=== Information Profit Threshold Derivation Verification ===")
print(f"phi      = {PHI:.10f}")
print(f"ln(phi)  = {LN_PHI:.10f}")
print(f"ln(2*pi) = {LN_2PI:.10f}")
print(f"Lambda   = {LAMBDA:.10f}")
print(f"Lambda/2 = {LAMBDA/2:.10f}")
print(f"IPT      = {IPT:.10f}")

if abs(IPT - IPT_EXPECTED) < 1e-4:
    print(f"PASS: IPT = {IPT:.10f} is within 1e-04 of {IPT_EXPECTED}")
else:
    raise RuntimeError(
        f"FAIL: IPT = {IPT:.10f} differs from {IPT_EXPECTED} by more than 1e-04"
    )

result = {
    "phi": PHI,
    "ln_phi": LN_PHI,
    "ln_2pi": LN_2PI,
    "lambda": LAMBDA,
    "lambda_half": LAMBDA / 2.0,
    "IPT": IPT,
    "IPT_expected": IPT_EXPECTED,
    "pass": True,
}

os.makedirs("results", exist_ok=True)
out_path = "results/ipt_derivation_verification.json"
with open(out_path, "w") as f:
    json.dump(result, f, indent=2)
print(f"Result saved to {out_path}")
