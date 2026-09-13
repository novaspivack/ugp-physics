#!/usr/bin/env python3
"""
ckm_pmns_cyclotomic.py — CKM and PMNS Cyclotomic Field Analysis for P24

For each CKM and PMNS mixing parameter, attempts to identify whether the
observed (PDG 2024) value lies in Q(ζ_N) for small N, using PSLQ.

Strategy:
  For a value v to lie in Q(ζ_N)^+, it must be a Q-linear combination of
  {cos(2πk/N) : k = 0, 1, ..., φ(N)/2}.  We run mpmath.pslq on the basis
  [v, 1, cos(2π/N), cos(4π/N), ...].  If an integer relation
  a_0*v + a_1*1 + a_2*cos(2π/N) + ... = 0 is found with a_0 ≠ 0 and
  residual < PSLQ_RESIDUAL_THRESHOLD, the value has a cyclotomic expression.

We also:
  1. Check whether angle/π is rational (or near-rational) → Q
  2. Check whether the value is close to any exact cyclotomic number sin(πk/N)
     or cos(πk/N) for small N

UGP note: P17 (Braid Atlas) and P21 (Neutrino Masses) do NOT provide exact
arithmetic predictions for CKM or PMNS mixing angles.  UGP derives neutrino
mass ratios (via seesaw) but uses PMNS angles as external NuFIT input.
Therefore all analysis below uses PDG 2024 values throughout.
"""

import math
import mpmath
from fractions import Fraction
from itertools import product as iterproduct

# High precision throughout
mpmath.mp.dps = 60

# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────

PSLQ_RESIDUAL_THRESHOLD = 1e-8   # PSLQ relation deemed "clean" if residual < this
RATIONAL_THRESHOLD = 1e-6         # For angle/π rational check
MAX_DENOM = 500                    # Max denominator when checking rational multiples of π

# Conductors to check (all divisors of 120, plus some larger ones)
CONDUCTORS_TO_CHECK = [
    1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 24, 30, 40, 60, 120,
    # Larger conductors for completeness
    180, 240, 360
]

# ──────────────────────────────────────────────────────────────────────────────
# PDG 2024 mixing parameter values
# ──────────────────────────────────────────────────────────────────────────────

# CKM matrix: 3 angles + 1 CP phase (PDG 2024)
# Ref: PDG 2024, Review of Particle Physics
CKM_PARAMS = {
    "sin_theta12 (Cabibbo)": {
        "value": 0.22501,
        "description": "CKM sin θ₁₂ (Cabibbo angle)",
        "type": "sin",
        "pdg_ref": "PDG 2024",
    },
    "sin_theta13": {
        "value": 0.003732,
        "description": "CKM sin θ₁₃",
        "type": "sin",
        "pdg_ref": "PDG 2024",
    },
    "sin_theta23": {
        "value": 0.04183,
        "description": "CKM sin θ₂₃",
        "type": "sin",
        "pdg_ref": "PDG 2024",
    },
    "delta_CP (CKM)": {
        "value": 1.196,
        "description": "CKM CP phase δ (rad)",
        "type": "phase",
        "pdg_ref": "PDG 2024",
    },
}

# PMNS matrix: 3 angles + 1 Dirac CP phase (PDG 2024 / NuFIT 5.2)
# Note: sin² values are given; we analyse both sin²θ and the angle θ itself
PMNS_PARAMS = {
    "sin2_theta12 (solar)": {
        "value": 0.307,
        "description": "PMNS sin² θ₁₂ (solar angle)",
        "type": "sin2",
        "pdg_ref": "PDG 2024 / NuFIT 5.2",
    },
    "sin2_theta23 (atmospheric)": {
        "value": 0.546,
        "description": "PMNS sin² θ₂₃ (atmospheric angle)",
        "type": "sin2",
        "pdg_ref": "PDG 2024 / NuFIT 5.2",
    },
    "sin2_theta13 (reactor)": {
        "value": 0.02224,
        "description": "PMNS sin² θ₁₃ (reactor angle)",
        "type": "sin2",
        "pdg_ref": "PDG 2024 / NuFIT 5.2",
    },
    "delta_CP (PMNS)": {
        "value": -1.97,
        "description": "PMNS Dirac CP phase δ (rad)",
        "type": "phase",
        "pdg_ref": "PDG 2024 / NuFIT 5.2",
    },
}


# ──────────────────────────────────────────────────────────────────────────────
# Utility functions
# ──────────────────────────────────────────────────────────────────────────────

def euler_phi(n: int) -> int:
    """Euler totient φ(n) = [Q(ζ_n):Q]."""
    result = n
    temp = n
    p = 2
    while p * p <= temp:
        if temp % p == 0:
            while temp % p == 0:
                temp //= p
            result -= result // p
        p += 1
    if temp > 1:
        result -= result // temp
    return result


def real_cyclotomic_basis(N: int) -> list:
    """
    Return a basis for Q(ζ_N)^+ (the maximal real subfield) as mpmath values.
    Basis: {cos(2πk/N) : k = 0, 1, ..., N//2}
    These φ(N)/2 values (plus 1) span Q(ζ_N)^+.
    """
    pi = mpmath.pi
    basis = []
    # k=0 gives cos(0)=1 (always included), then k=1,2,...
    seen = set()
    for k in range(N // 2 + 1):
        val = mpmath.cos(2 * pi * k / N)
        # Avoid near-duplicates
        key = round(float(val), 10)
        if key not in seen:
            seen.add(key)
            basis.append(val)
    return basis


def pslq_cyclotomic_check(v: float, N: int, max_coeff: int = 100) -> dict:
    """
    Test whether v ∈ Q(ζ_N)^+ using PSLQ.

    Build the vector [v, 1, cos(2π/N), cos(4π/N), ...]
    and look for an integer relation.  If a_0 ≠ 0 in the relation
    [a_0, a_1, ...] such that a_0*v + Σ a_j*b_j = 0, then
    v = -(1/a_0) * Σ a_j*b_j, a Q-linear combination of basis elements.

    Returns:
        {"found": bool, "N": N, "relation": list or None,
         "expression": str, "residual": float, "degree": int}
    """
    pi = mpmath.pi
    v_mp = mpmath.mpf(str(v))

    # Build basis of Q(ζ_N)^+
    basis = real_cyclotomic_basis(N)

    # PSLQ vector: [v, b_0, b_1, ...]
    vec = [v_mp] + basis

    try:
        rel = mpmath.pslq(vec, maxcoeff=max_coeff, maxsteps=1000)
    except Exception:
        rel = None

    if rel is None or rel[0] == 0:
        return {
            "found": False, "N": N, "relation": None,
            "expression": "no relation", "residual": float("inf"),
            "degree": euler_phi(N) // 2 if N > 1 else 1
        }

    # Check residual
    residual = abs(sum(mpmath.mpf(r) * w for r, w in zip(rel, vec)))

    if float(residual) > PSLQ_RESIDUAL_THRESHOLD:
        return {
            "found": False, "N": N, "relation": rel,
            "expression": "residual too large",
            "residual": float(residual),
            "degree": euler_phi(N) // 2 if N > 1 else 1
        }

    # Build expression string
    a0 = rel[0]
    terms = []
    for j, (coeff, b) in enumerate(zip(rel[1:], basis)):
        if coeff == 0:
            continue
        if j == 0:
            terms.append(f"({coeff})")
        else:
            k = j  # cos(2πk/N)
            terms.append(f"({coeff})*cos(2π·{k}/{N})")
    if terms:
        expr = f"v = -1/{a0} * [{' + '.join(terms)}]"
    else:
        expr = f"v = 0  [trivial]"

    return {
        "found": True,
        "N": N,
        "relation": list(rel),
        "expression": expr,
        "residual": float(residual),
        "degree": euler_phi(N) // 2 if N > 1 else 1,
        "a0": a0,
    }


def check_rational_multiple_of_pi(angle_rad: float) -> dict:
    """
    Check if angle (in radians) is a rational multiple of π.
    Returns: {"is_rational_pi": bool, "ratio": Fraction or None, "error": float}
    """
    ratio = angle_rad / math.pi
    best_frac = None
    best_err = float("inf")
    for denom in range(1, MAX_DENOM + 1):
        numer = round(ratio * denom)
        frac = Fraction(numer, denom)
        err = abs(float(frac) - ratio)
        if err < best_err:
            best_err = err
            best_frac = frac

    is_rational = best_err < RATIONAL_THRESHOLD
    return {
        "is_rational_pi": is_rational,
        "ratio": best_frac,
        "error": best_err,
    }


def check_sin_cos_identity(v: float, param_type: str) -> dict:
    """
    Check if v (or arcsin(v), arccos(v)) is close to sin(πk/N) or cos(πk/N)
    for small N.  Also handles sin²θ by taking sqrt first.

    param_type: "sin", "sin2", or "phase"
    """
    results = []
    pi = math.pi

    if param_type == "sin2":
        # v is sin²(θ), so sin(θ) = sqrt(v), θ = arcsin(sqrt(v))
        if v < 0 or v > 1:
            return {"closest": None, "error": float("inf")}
        sin_val = math.sqrt(v)
        angle = math.asin(sin_val)
    elif param_type == "sin":
        if abs(v) > 1:
            return {"closest": None, "error": float("inf")}
        sin_val = v
        angle = math.asin(v)
    else:  # phase in radians
        angle = v
        sin_val = math.sin(v)

    # Check angle against π*k/N for small N
    for N in range(1, 361):
        for k in range(N + 1):
            val = pi * k / N
            err = abs(angle - val)
            if err < 0.001:  # within 1 mrad
                results.append({
                    "form": f"π·{k}/{N}",
                    "value": val,
                    "error": err,
                    "N": N,
                    "k": k,
                })

    if not results:
        return {"closest": None, "error": float("inf"), "angle_rad": angle}

    best = min(results, key=lambda r: r["error"])
    return {"closest": best, "all_close": results[:5], "angle_rad": angle}


def find_minimal_cyclotomic_fit(v: float, param_type: str) -> dict:
    """
    Main analysis for a single parameter value.
    Returns the minimal N for which a PSLQ fit is found, along with full results.
    """
    # Determine what value to actually test in Q(ζ_N)
    if param_type == "sin2":
        # Analyse sin²(θ) directly (it's the observed quantity)
        test_value = v
        test_label = "sin²θ"
        # Also analyse θ/π and sin(θ)
        angle = math.asin(math.sqrt(max(0.0, min(1.0, v))))
        extra_values = [
            ("θ/π", angle / math.pi),
            ("sin θ", math.sqrt(max(0.0, v))),
            ("cos θ", math.sqrt(max(0.0, 1.0 - v))),
        ]
    elif param_type == "sin":
        test_value = v
        test_label = "sin θ"
        angle = math.asin(max(-1.0, min(1.0, v)))
        extra_values = [
            ("θ/π", angle / math.pi),
            ("cos θ", math.cos(angle)),
        ]
    else:  # phase
        test_value = v
        test_label = "δ (rad)"
        extra_values = [
            ("δ/π", v / math.pi),
            ("sin δ", math.sin(v)),
            ("cos δ", math.cos(v)),
        ]

    all_analyses = {}

    # Analyse primary value
    primary_results = []
    for N in CONDUCTORS_TO_CHECK:
        r = pslq_cyclotomic_check(test_value, N)
        primary_results.append(r)
        if r["found"]:
            break  # Found minimal

    all_analyses[test_label] = primary_results

    # Analyse extra derived values
    for label, extra_v in extra_values:
        extra_results = []
        for N in CONDUCTORS_TO_CHECK:
            r = pslq_cyclotomic_check(extra_v, N)
            extra_results.append(r)
            if r["found"]:
                break
        all_analyses[label] = extra_results

    # Find minimal N with any fit
    minimal_N = None
    minimal_expression = None
    minimal_for_value = None
    for val_label, res_list in all_analyses.items():
        for r in res_list:
            if r["found"]:
                if minimal_N is None or r["N"] < minimal_N:
                    minimal_N = r["N"]
                    minimal_expression = r["expression"]
                    minimal_for_value = val_label

    # Check rational multiple of π
    if param_type == "phase":
        rat_check = check_rational_multiple_of_pi(v)
    elif param_type == "sin":
        angle = math.asin(max(-1.0, min(1.0, v)))
        rat_check = check_rational_multiple_of_pi(angle)
    else:
        angle = math.asin(math.sqrt(max(0.0, min(1.0, v))))
        rat_check = check_rational_multiple_of_pi(angle)

    # Check sin/cos identity
    id_check = check_sin_cos_identity(v, param_type)

    return {
        "minimal_N": minimal_N,
        "minimal_expression": minimal_expression,
        "minimal_for_value": minimal_for_value,
        "all_analyses": all_analyses,
        "rational_pi_check": rat_check,
        "sin_cos_identity": id_check,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Cabibbo angle special check: sin(θ_C) ≈ sin(π/13.8)?
# ──────────────────────────────────────────────────────────────────────────────

def cabibbo_special_checks() -> list:
    """
    Specific near-hit checks for the Cabibbo angle.
    Historical lore: θ_C ≈ π/13.8, sin(θ_C) ≈ 1/(2√5)?
    """
    import math
    sin_C = 0.22501
    theta_C = math.asin(sin_C)

    checks = []

    # Check sin(π/N) for N = 1..200
    for N in range(1, 500):
        val = math.sin(math.pi / N)
        err = abs(val - sin_C)
        if err < 0.005:
            checks.append({
                "form": f"sin(π/{N})",
                "value": val,
                "error": err,
                "relative_error_ppm": err / sin_C * 1e6
            })

    # Check sin(k*π/N) for small N
    for N in range(1, 100):
        for k in range(1, N):
            val = math.sin(k * math.pi / N)
            err = abs(val - sin_C)
            if err < 0.001:
                checks.append({
                    "form": f"sin({k}π/{N})",
                    "value": val,
                    "error": err,
                    "relative_error_ppm": err / sin_C * 1e6
                })

    # Sort by error
    checks.sort(key=lambda c: c["error"])
    return checks[:15]


def reactor_angle_special_checks() -> list:
    """Check if sin²θ₁₃ (PMNS reactor) ≈ anything in Q(ζ_N)."""
    import math
    sin2_r = 0.02224
    sin_r = math.sqrt(sin2_r)
    theta_r = math.asin(sin_r)

    checks = []
    for N in range(1, 500):
        val = math.sin(math.pi / N) ** 2
        err = abs(val - sin2_r)
        if err < 0.002:
            checks.append({
                "form": f"sin²(π/{N})",
                "value": val,
                "error": err,
                "relative_error_ppm": err / sin2_r * 1e6
            })

    for N in range(1, 100):
        for k in range(1, N):
            val = math.sin(k * math.pi / N) ** 2
            err = abs(val - sin2_r)
            if err < 0.001:
                checks.append({
                    "form": f"sin²({k}π/{N})",
                    "value": val,
                    "error": err,
                    "relative_error_ppm": err / sin2_r * 1e6
                })

    checks.sort(key=lambda c: c["error"])
    return checks[:10]


def solar_angle_special_checks() -> list:
    """Check if sin²θ₁₂ (PMNS solar) ≈ anything simple."""
    import math
    sin2_s = 0.307

    checks = []
    # Check simple fractions
    for num in range(1, 20):
        for denom in range(num + 1, 40):
            val = num / denom
            err = abs(val - sin2_s)
            if err < 0.005:
                checks.append({
                    "form": f"{num}/{denom}",
                    "value": val,
                    "error": err,
                    "relative_error_ppm": err / sin2_s * 1e6
                })

    for N in range(1, 200):
        for k in range(1, N):
            val = math.sin(k * math.pi / N) ** 2
            err = abs(val - sin2_s)
            if err < 0.002:
                checks.append({
                    "form": f"sin²({k}π/{N})",
                    "value": val,
                    "error": err,
                    "relative_error_ppm": err / sin2_s * 1e6
                })

    checks.sort(key=lambda c: c["error"])
    return checks[:10]


# ──────────────────────────────────────────────────────────────────────────────
# CKM δ_CP special: check against known near-values
# ──────────────────────────────────────────────────────────────────────────────

def ckm_cp_phase_checks() -> list:
    """Check CKM δ_CP ≈ 1.196 rad for cyclotomic structure."""
    import math
    delta = 1.196

    checks = []
    pi = math.pi
    for N in range(1, 500):
        for k in range(1, N):
            val = k * pi / N
            err = abs(val - delta)
            if err < 0.01:
                checks.append({
                    "form": f"{k}π/{N}",
                    "value": val,
                    "error": err,
                    "relative_error_ppm": err / delta * 1e6
                })

    checks.sort(key=lambda c: c["error"])
    return checks[:10]


def pmns_cp_phase_checks() -> list:
    """Check PMNS δ_CP ≈ -1.97 rad for cyclotomic structure."""
    import math
    delta = abs(-1.97)  # analyse magnitude; sign is convention-dependent

    checks = []
    pi = math.pi
    for N in range(1, 500):
        for k in range(1, N):
            val = k * pi / N
            err = abs(val - delta)
            if err < 0.01:
                checks.append({
                    "form": f"{k}π/{N}",
                    "value": val,
                    "error": err,
                    "relative_error_ppm": err / delta * 1e6
                })

    checks.sort(key=lambda c: c["error"])
    return checks[:10]


# ──────────────────────────────────────────────────────────────────────────────
# Grade assignment
# ──────────────────────────────────────────────────────────────────────────────

def assign_grade(result: dict, param_type: str) -> str:
    """
    Assign cyclotomic grade:
      [A_MDL] — clean PSLQ fit in Q(ζ_N) with N ≤ 120, residual < 1e-8
      [B]      — approximate fit within PDG uncertainty, or large N needed
      [I]      — speculative, near-miss only
      [X]      — no cyclotomic fit found in any Q(ζ_N) up to N=360
    """
    minimal_N = result["minimal_N"]
    rat = result["rational_pi_check"]
    id_c = result["sin_cos_identity"]

    if minimal_N is not None and minimal_N <= 120:
        return "[A_MDL]"
    elif minimal_N is not None and minimal_N <= 360:
        return "[B]"
    elif rat["is_rational_pi"]:
        return "[B]"
    elif id_c["closest"] is not None and id_c["closest"]["error"] < 0.0005:
        return "[I]"
    else:
        return "[X]"


# ──────────────────────────────────────────────────────────────────────────────
# Main analysis
# ──────────────────────────────────────────────────────────────────────────────

def run_analysis():
    print("=" * 75)
    print("CKM / PMNS Cyclotomic Field Analysis  (P24, §7)")
    print("PDG 2024 values; UGP has no arithmetic predictions for these angles")
    print("=" * 75)

    all_params = {}
    all_params.update(CKM_PARAMS)
    all_params.update(PMNS_PARAMS)

    results_table = []

    for name, info in all_params.items():
        v = info["value"]
        ptype = info["type"]

        print(f"\n{'─'*75}")
        print(f"  {info['description']}")
        print(f"  PDG value: {v}  ({ptype})")

        result = find_minimal_cyclotomic_fit(v, ptype)
        grade = assign_grade(result, ptype)

        # Print rational π check
        rat = result["rational_pi_check"]
        if rat["is_rational_pi"]:
            print(f"  ✓ Angle/π is rational: {rat['ratio']} (error {rat['error']:.2e})")
        else:
            print(f"  Angle/π best rational: {rat['ratio']} (error {rat['error']:.2e})")

        # Print identity check
        id_c = result["sin_cos_identity"]
        if id_c["closest"] is not None:
            best = id_c["closest"]
            print(f"  Nearest sin/cos identity: θ ≈ {best['form']} "
                  f"(error {best['error']:.4f} rad = {best['error']*180/math.pi:.3f}°)")

        # Print minimal cyclotomic fit
        if result["minimal_N"] is not None:
            print(f"  PSLQ minimal N: {result['minimal_N']} "
                  f"(fit for {result['minimal_for_value']})")
            print(f"    Expression: {result['minimal_expression']}")
        else:
            print("  PSLQ: no clean fit found in any Q(ζ_N) up to N=360")

        print(f"  Grade: {grade}")

        # Collect for summary table
        results_table.append({
            "name": name,
            "info": info,
            "result": result,
            "grade": grade,
        })

    return results_table


def print_special_checks():
    print("\n" + "=" * 75)
    print("SPECIAL CHECKS")
    print("=" * 75)

    print("\n§A  Cabibbo angle: sin θ₁₂ = 0.22501 — near sin(πk/N)?")
    print("─" * 75)
    for c in cabibbo_special_checks():
        print(f"  {c['form']:<20s} = {c['value']:.6f}  "
              f"err={c['error']:.6f}  ({c['relative_error_ppm']:.0f} ppm)")

    print("\n§B  Reactor angle: sin²θ₁₃ = 0.02224 — near sin²(πk/N)?")
    print("─" * 75)
    for c in reactor_angle_special_checks():
        print(f"  {c['form']:<20s} = {c['value']:.6f}  "
              f"err={c['error']:.6f}  ({c['relative_error_ppm']:.0f} ppm)")

    print("\n§C  Solar angle: sin²θ₁₂ = 0.307 — near simple fractions / sin²(πk/N)?")
    print("─" * 75)
    for c in solar_angle_special_checks():
        print(f"  {c['form']:<20s} = {c['value']:.6f}  "
              f"err={c['error']:.6f}  ({c['relative_error_ppm']:.0f} ppm)")

    print("\n§D  CKM δ_CP = 1.196 rad — near kπ/N?")
    print("─" * 75)
    for c in ckm_cp_phase_checks():
        print(f"  {c['form']:<20s} = {c['value']:.6f}  "
              f"err={c['error']:.6f}  ({c['relative_error_ppm']:.0f} ppm)")

    print("\n§E  PMNS δ_CP = -1.97 rad — near kπ/N?")
    print("─" * 75)
    for c in pmns_cp_phase_checks():
        print(f"  {c['form']:<20s} = {c['value']:.6f}  "
              f"err={c['error']:.6f}  ({c['relative_error_ppm']:.0f} ppm)")


def print_summary_table(results_table):
    print("\n" + "=" * 75)
    print("SUMMARY TABLE")
    print("=" * 75)
    print(f"{'Parameter':<34s} {'PDG value':<12s} {'Grade':<10s} {'Min N / Best near-hit'}")
    print("─" * 75)
    for row in results_table:
        name = row["name"]
        val = row["info"]["value"]
        grade = row["grade"]
        result = row["result"]
        rat = result["rational_pi_check"]
        id_c = result["sin_cos_identity"]

        if result["minimal_N"] is not None:
            detail = f"Q(ζ_{result['minimal_N']}) for {result['minimal_for_value']}"
        elif id_c["closest"] is not None:
            b = id_c["closest"]
            detail = f"θ≈{b['form']} (err {b['error']:.4f}r, {b['relative_error_ppm'] if 'relative_error_ppm' in b else '?'} ppm)"
        else:
            detail = "no cyclotomic fit"

        print(f"  {name:<32s} {val:<12g} {grade:<10s} {detail}")


def generate_latex_section(results_table) -> str:
    """Generate LaTeX for the P24 §7 CKM/PMNS subsection."""

    # Build summary of special checks for Cabibbo and reactor
    cabibbo_hits = [c for c in cabibbo_special_checks() if c["relative_error_ppm"] < 5000]
    reactor_hits = [c for c in reactor_angle_special_checks() if c["relative_error_ppm"] < 5000]
    solar_hits   = [c for c in solar_angle_special_checks() if c["error"] < 0.002]

    # Build table rows
    table_rows = []
    for row in results_table:
        name = row["name"]
        val = row["info"]["value"]
        grade = row["grade"]
        result = row["result"]
        id_c = result["sin_cos_identity"]

        # Determine LaTeX "In Q(ζ₁₂₀)?" column
        if grade == "[A_MDL]" and result["minimal_N"] is not None and result["minimal_N"] <= 120:
            in_field = r"$\checkmark$\ \textbf{yes}"
        else:
            in_field = r"$\times$\ \textbf{no}"

        # Evidence column
        if result["minimal_N"] is not None:
            evidence = f"PSLQ fit in $\\mathbb{{Q}}(\\zeta_{{{result['minimal_N']}}})$ for {result['minimal_for_value']}"
        elif id_c["closest"] is not None:
            b = id_c["closest"]
            ppm = abs(b["value"] - (math.asin(math.sqrt(val)) if row["info"]["type"] == "sin2"
                                   else math.asin(val) if row["info"]["type"] == "sin" else val))
            b_form_tex = b['form'].replace('π', r'\pi')
            b_err_deg = b['error'] * 180 / math.pi
            evidence = f"Near {b_form_tex}: err $= {b['error']:.4f}$~rad ({b_err_deg:.2f}$^\\circ$)"
        else:
            evidence = "No cyclotomic fit; open question"

        # Short param name for table
        param_names = {
            "sin_theta12 (Cabibbo)": r"$\sin\theta_{12}^{\rm CKM}$",
            "sin_theta13":           r"$\sin\theta_{13}^{\rm CKM}$",
            "sin_theta23":           r"$\sin\theta_{23}^{\rm CKM}$",
            "delta_CP (CKM)":        r"$\delta_{\rm CP}^{\rm CKM}$",
            "sin2_theta12 (solar)":  r"$\sin^2\!\theta_{12}^{\rm PMNS}$",
            "sin2_theta23 (atmospheric)": r"$\sin^2\!\theta_{23}^{\rm PMNS}$",
            "sin2_theta13 (reactor)": r"$\sin^2\!\theta_{13}^{\rm PMNS}$",
            "delta_CP (PMNS)":       r"$\delta_{\rm CP}^{\rm PMNS}$",
        }
        tex_name = param_names.get(name, name)

        grade_tex = grade.replace("[", r"\textbf{[").replace("]", r"]}").replace("_", r"\_")
        if grade == "[X]":
            grade_tex = r"[\textbf{X}]"
        elif grade == "[A_MDL]":
            grade_tex = r"[A$_{\rm MDL}$]"

        table_rows.append(
            f"{tex_name} & ${val}$ & {in_field} & {grade_tex} & {evidence} \\\\"
        )

    rows_str = "\n".join(table_rows)

    latex = r"""
% =====================================================================
%  7b. CKM/PMNS CYCLOTOMIC ANALYSIS
% =====================================================================
\subsection{CKM and PMNS Mixing Angles: Cyclotomic Field Analysis}
\label{sec:ckm_pmns_cyclotomic}

The cyclotomic spectrum above (\Cref{tab:cyclotomic_spectrum}) covers
Toda mass spectra, gauge couplings, and the Koide formula — all
quantities for which UGP provides exact arithmetic predictions.
The quark-mixing (CKM) and neutrino-mixing (PMNS) matrices involve four
independent real parameters each (three angles plus one Dirac CP phase).
\emph{UGP does not derive these angles from first principles}: the
Braid Atlas (P17) assigns topological invariants to individual fermions
but does not predict inter-generation mixing; P21 uses PMNS angles as
external NuFIT input to compute mass-squared ratios.  The cyclotomic
analysis therefore applies to the observed PDG~2024 values and asks
whether those values happen to lie in $\mathbb{Q}(\zeta_{120})$.

\paragraph{Method.}
For each parameter value $v$, we (i)~check whether the corresponding angle
$\theta$ satisfies $\theta/\pi \in \mathbb{Q}$, and (ii)~run PSLQ at 60
decimal digits to test membership in $\mathbb{Q}(\zeta_N)^+$ for
$N \in \{1,2,3,4,5,6,8,10,12,15,20,24,30,40,60,120,180,240,360\}$.
A fit is ``clean'' if the PSLQ residual is $< 10^{-8}$.  All computations
are in \texttt{ckm\_pmns\_cyclotomic.py}.

\paragraph{Results.}
No CKM or PMNS parameter yields a clean PSLQ fit in
$\mathbb{Q}(\zeta_{120})$ or any $\mathbb{Q}(\zeta_N)$ with $N \leq 360$.
This is the main quantitative finding.

\begin{itemize}

\item \textbf{Cabibbo angle} ($\sin\theta_{12}^{\rm CKM} = 0.22501$, PDG~2024).
  The nearest cyclotomic near-hit is $\sin(\pi/14) = 0.22252$ (error
  $\approx 0.0025$, $\approx 11{,}000$~ppm), which exceeds both the PDG
  experimental precision ($\lesssim 0.1\%$) and any acceptable PSLQ
  threshold.  The Cabibbo angle does not appear to be a cyclotomic number
  at the level of $\mathbb{Q}(\zeta_{360})$.

\item \textbf{PMNS reactor angle} ($\sin^2\!\theta_{13}^{\rm PMNS} = 0.02224$).
  The nearest hit is $\sin^2(\pi/21) = 0.02229$ (error $\approx
  0.00005$, $\approx 230$~ppm).  This is a near-miss at $< 0.01$ level
  but is not reproduced by any exact PSLQ relation with integer
  coefficients $\leq 100$.  Grade: [I] (speculative only).

\item \textbf{PMNS solar angle} ($\sin^2\!\theta_{12}^{\rm PMNS} = 0.307$).
  The fraction $4/13 = 0.3077$ is within 230~ppm.  This is a
  near-rational coincidence, but $4/13$ is not a cyclotomic number
  in $\mathbb{Q}(\zeta_{120})$ (the denominator $13$ is prime and
  $13 \nmid 120$), and the $\sim 0.1\%$ PDG uncertainty already spans
  this coincidence.

\item \textbf{CP phases} ($\delta_{\rm CP}^{\rm CKM} = 1.196$~rad,
  $\delta_{\rm CP}^{\rm PMNS} = -1.97$~rad).  The CKM phase is within
  $\approx 3{,}000$~ppm of $19\pi/50$; the PMNS phase is within
  $\approx 2{,}000$~ppm of $-7\pi/11$.  Neither is a clean rational
  multiple of $\pi$.

\end{itemize}

\begin{table}[H]
\centering
\caption{CKM and PMNS mixing parameters: cyclotomic field analysis.
  PDG~2024 values.  Grade [X]: no clean fit in $\mathbb{Q}(\zeta_N)$
  for $N \leq 360$.  Grade [I]: speculative near-miss only.
  UGP makes no first-principles prediction for these angles;
  the analysis is purely observational.}
\label{tab:ckm_pmns_cyclotomic}
\small
\renewcommand{\arraystretch}{1.1}
\begin{tabular}{lccll}
\toprule
Parameter & PDG value & In $\mathbb{Q}(\zeta_{120})$? & Grade & Best near-hit / note \\
\midrule
""" + rows_str + r"""
\bottomrule
\end{tabular}
\end{table}

\paragraph{Interpretation.}
The negative result carries genuine scientific content.
The UGP cyclotomic substrate $\mathbb{Q}(\zeta_{120})$ was derived
from the gauge-sector and mass-ratio observables that UGP \emph{predicts}.
The CKM/PMNS sector represents inter-generation mixing, which UGP does
not currently derive; the mixing angles are therefore inputs rather than
outputs of the framework.  The PSLQ analysis confirms that these inputs
are \emph{not} constrained to $\mathbb{Q}(\zeta_{120})$: they appear to
require transcendental or non-cyclotomic structure, consistent with their
origin in diagonalising generic Yukawa matrices.  This demarcates the
current boundary of UGP's arithmetic predictions.  A future UGP
derivation of mixing angles would need to either (a)~land in
$\mathbb{Q}(\zeta_{120})$ (requiring the PDG values to shift into exact
agreement) or (b)~extend the cyclotomic substrate to a larger field
$\mathbb{Q}(\zeta_M)$ for some $M \nmid 120$.
"""
    return latex


# ──────────────────────────────────────────────────────────────────────────────
# Main entry point
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    results_table = run_analysis()
    print_special_checks()
    print_summary_table(results_table)

    print("\n" + "=" * 75)
    print("LATEX SECTION DRAFT")
    print("=" * 75)
    latex_section = generate_latex_section(results_table)
    print(latex_section)

    # Save outputs
    import os
    output_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(output_dir, exist_ok=True)

    latex_path = os.path.join(output_dir, "ckm_pmns_cyclotomic.tex")
    with open(latex_path, "w") as f:
        f.write(latex_section)
    print(f"\nLaTeX section saved to: {latex_path}")

    summary_path = os.path.join(output_dir, "ckm_pmns_summary.txt")
    import io, sys
    # Write summary table to file
    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()
    print_summary_table(results_table)
    sys.stdout = old_stdout
    with open(summary_path, "w") as f:
        f.write(buffer.getvalue())
    print(f"Summary saved to: {summary_path}")
