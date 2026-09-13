"""
COMP-P01-EE: sin²θ_W Phase 1 — Four Approach Candidates

Tests the four approach candidates from 05_SPEC §3 that go beyond SC-AA:
  Approach 1: RG-based  δ_G ∝ ln(M_G/M_Z)  using inverse-solved scales from SC-CC
  Approach 2: Casimir-based  δ_G ∝ C₂(G)  and  δ_G ∝ C₂(G)/dim(G)
  Approach 3: Anomalous-dimension  δ_G = c · b_G  for UGP-motivated c values
  Approach 4: Quarter-Lock-extended  using k_M, k_gen², k_L²

SHA-256 protocol: prediction block written BEFORE PDG comparison is appended.
Pre-commit required before running this script.

Lean-certified inputs:
  g₁² = 16/125 = 0.128
  g₂² = 2329/5400 ≈ 0.43130
  g₃² = 41075281/27648000 ≈ 1.48565
  k_L² = 7/512 = 0.013671875
  k_gen² = -φ/2  (φ = (1+√5)/2)
  δ_UGP = 1 + k_gen² + k_L²/4 - 1 = k_gen² + k_L²/4
  b₁ = 73  (the Paper 1 integer)

Inverse-solved scales from SC-CC (bare-only, 1-loop):
  M₁ = 108.811 GeV  (U(1)_Y)
  M₂ = 37.430 GeV   (SU(2))
  M₃ = 89.303 GeV   (SU(3))
  M_Z = 91.1876 GeV

PDG targets (MSbar at M_Z):
  sin²θ_W = 0.23122 ± 0.00004
  α_w = α₂/4π → g₂²/4π = 0.03377684 ± 0.000062

Closure windows (1σ) from SC-AA:
  δ₁ ∈ (-0.00289, -0.00244)
  δ₂ ∈ (-0.01768, -0.01406)

Reference: specs/IN-PROCESS/EPIC_CLUSTER7_RESEARCH_GRADE/05_SPEC_SIN2_THETAW_CLOSURE.md
"""

import json
import math
import hashlib
import datetime
import itertools

# ── Lean-certified bare inputs ──────────────────────────────────────────────
G1SQ_BARE = 16 / 125           # 0.128
G2SQ_BARE = 2329 / 5400        # 0.43129629...
G3SQ_BARE = 41075281 / 27648000  # 1.48565107...

PHI = (1 + math.sqrt(5)) / 2
K_GEN2 = -PHI / 2             # ≈ -0.80902
K_L2 = 7 / 512                # 0.013671875
DELTA_UGP = K_GEN2 + K_L2 / 4  # ≈ -0.80559 — NOTE: scalar, proven not to close sin²θ_W

# Quarter-Lock: k_M = k_gen² + k_L²/4 (same as delta_UGP per Paper Eq.9)
K_M = K_GEN2 + K_L2 / 4

B1_INT = 73                    # Paper 1 integer b₁

# ── Inverse-solved scales from SC-CC bare-only 1-loop (GeV) ────────────────
M_Z = 91.1876
M1_INV = 108.81135600787199   # U(1)_Y inverse-solved scale
M2_INV = 37.429810981226815   # SU(2) inverse-solved scale
M3_INV = 89.30268595964488    # SU(3) inverse-solved scale

# ── Standard-model 1-loop beta coefficients (SM, MSbar) ────────────────────
# U(1)_Y: b₁ = +41/6 (in the normalisation convention where b is positive for IR-free)
# SU(2): b₂ = -19/6
# SU(3): b₃ = -7
B_COEFF = {
    "U1": 41 / 6,           # +6.8333…
    "SU2": -19 / 6,         # -3.1667…
    "SU3": -7.0,
}

# ── Quadratic Casimirs and group dimensions ─────────────────────────────────
# For SU(N): C₂(fund) = (N²-1)/(2N), dim = N²-1
# For U(1)_Y: conventionally C₂ = Y² = (1/2)² = 1/4 for the lowest-weight doublet,
#             or 0 as an abelian group. We test both conventions.
# We use adjoint quadratic Casimir (= 0 for U(1), N for SU(N)):
C2_ADJ = {"U1": 0, "SU2": 2, "SU3": 3}  # N for SU(N), 0 for U(1)
C2_FUND = {"U1": 0, "SU2": 3 / 4, "SU3": 4 / 3}  # (N²-1)/(2N)
DIM_G = {"U1": 1, "SU2": 3, "SU3": 8}

# ── PDG targets and closure windows ────────────────────────────────────────
PDG_SIN2 = 0.23122
PDG_SIN2_SIGMA = 4e-5
PDG_AW = (G2SQ_BARE) / (4 * math.pi)  # nominal; actual from SC-AA below
PDG_AW_CENTRAL = 0.03377683684698846
PDG_AW_SIGMA = 6.221366725462189e-5

# Closure windows from SC-AA (1σ)
DELTA1_LO, DELTA1_HI = -0.002886818893320431, -0.002437965300768008
DELTA2_LO, DELTA2_HI = -0.017681223701159320, -0.014055873765564608


# ── Helper functions ────────────────────────────────────────────────────────

def sin2_thetaw(g1sq, g2sq):
    return g1sq / (g1sq + g2sq)


def alpha_w(g2sq):
    return g2sq / (4 * math.pi)


def apply_delta(g_sq, delta):
    return g_sq * (1 + delta)


def sigma_from_target(val, central, sigma):
    return (val - central) / sigma


def in_window(delta, lo, hi):
    return lo <= delta <= hi


def window_distance(delta, lo, hi):
    """Signed distance to nearest edge of window (negative = inside)."""
    if delta < lo:
        return delta - lo
    if delta > hi:
        return delta - hi
    return 0.0


def evaluate_approach(delta1, delta2, label, description):
    """
    Given coupling-specific corrections δ₁ (U(1)_Y) and δ₂ (SU(2)),
    compute predicted observables and assess closure.
    """
    g1sq_new = apply_delta(G1SQ_BARE, delta1)
    g2sq_new = apply_delta(G2SQ_BARE, delta2)

    pred_sin2 = sin2_thetaw(g1sq_new, g2sq_new)
    pred_aw = alpha_w(g2sq_new)

    sin2_sigma = sigma_from_target(pred_sin2, PDG_SIN2, PDG_SIN2_SIGMA)
    aw_sigma = sigma_from_target(pred_aw, PDG_AW_CENTRAL, PDG_AW_SIGMA)

    d1_in = in_window(delta1, DELTA1_LO, DELTA1_HI)
    d2_in = in_window(delta2, DELTA2_LO, DELTA2_HI)
    both_in = d1_in and d2_in

    return {
        "label": label,
        "description": description,
        "delta_1": delta1,
        "delta_2": delta2,
        "delta_1_in_window": d1_in,
        "delta_2_in_window": d2_in,
        "both_in_window": both_in,
        "predicted_g1sq": g1sq_new,
        "predicted_g2sq": g2sq_new,
        "predicted_sin2_thetaW": pred_sin2,
        "predicted_alpha_w": pred_aw,
        "sin2_thetaW_sigma": sin2_sigma,
        "alpha_w_sigma": aw_sigma,
        "delta_1_window_dist": window_distance(delta1, DELTA1_LO, DELTA1_HI),
        "delta_2_window_dist": window_distance(delta2, DELTA2_LO, DELTA2_HI),
    }


# ──────────────────────────────────────────────────────────────────────────
# APPROACH 1: RG-based  δ_G = c · ln(M_G / M_Z)
# ──────────────────────────────────────────────────────────────────────────

def approach1_rg():
    """
    δ_G = c · ln(M_G / M_Z)
    where M_G is the group-specific inverse-solved scale from SC-CC bare-only.

    The ratios ln(M_G/M_Z) are fixed by SC-CC; only c is free.
    We search for c values that simultaneously land both δ₁ and δ₂
    in their 1σ windows.

    Additionally test UGP-motivated values of c:
      c = δ_UGP, c = k_L², c = k_gen², c = k_M,
      c = 1/b₁_int, c = k_L²/b₁_int, etc.
    """
    ln1 = math.log(M1_INV / M_Z)   # ln(108.81/91.19) ≈ +0.1763
    ln2 = math.log(M2_INV / M_Z)   # ln(37.43/91.19)  ≈ −0.8895
    ln3 = math.log(M3_INV / M_Z)   # ln(89.30/91.19)  ≈ −0.0209

    # For sin²θ_W closure we need only δ₁ and δ₂.
    # Window constraints:
    #   c·ln1 ∈ (DELTA1_LO, DELTA1_HI) → c ∈ (DELTA1_LO/ln1, DELTA1_HI/ln1)
    #   c·ln2 ∈ (DELTA2_LO, DELTA2_HI) → c ∈ (DELTA2_LO/ln2, DELTA2_HI/ln2)
    # ln1 > 0 so dividing preserves order; ln2 < 0 so dividing reverses order.

    c_from_d1_lo = DELTA1_LO / ln1
    c_from_d1_hi = DELTA1_HI / ln1
    c_from_d2_lo = DELTA2_LO / ln2   # ln2 < 0, reverses
    c_from_d2_hi = DELTA2_HI / ln2

    c_d1_interval = (min(c_from_d1_lo, c_from_d1_hi), max(c_from_d1_lo, c_from_d1_hi))
    c_d2_interval = (min(c_from_d2_lo, c_from_d2_hi), max(c_from_d2_lo, c_from_d2_hi))

    # Intersection
    c_intersect_lo = max(c_d1_interval[0], c_d2_interval[0])
    c_intersect_hi = min(c_d1_interval[1], c_d2_interval[1])
    has_intersection = c_intersect_lo < c_intersect_hi

    # UGP-motivated c candidates
    ugp_candidates = {
        "delta_UGP": DELTA_UGP,
        "k_L2": K_L2,
        "k_gen2": K_GEN2,
        "k_M": K_M,
        "1/b1_int": 1 / B1_INT,
        "k_L2/b1_int": K_L2 / B1_INT,
        "k_L2/phi": K_L2 / PHI,
        "k_gen2/b1_int": K_GEN2 / B1_INT,
        "1/phi": 1 / PHI,
        "1/phi^2": 1 / PHI**2,
        "k_L2*phi": K_L2 * PHI,
        "k_L2*phi^2": K_L2 * PHI**2,
    }
    if has_intersection:
        c_central = (c_intersect_lo + c_intersect_hi) / 2
        ugp_candidates["c_central_intersect"] = c_central

    candidate_results = []
    for name, c in ugp_candidates.items():
        delta1 = c * ln1
        delta2 = c * ln2
        res = evaluate_approach(delta1, delta2, f"A1_{name}", f"RG-based: δ_G = {name} · ln(M_G/M_Z)")
        res["c_value"] = c
        res["ln_M1_over_MZ"] = ln1
        res["ln_M2_over_MZ"] = ln2
        res["ln_M3_over_MZ"] = ln3
        candidate_results.append(res)

    return {
        "approach": "1_RG_based",
        "formula": "delta_G = c * ln(M_G / M_Z)",
        "log_ratios": {
            "ln_M1_over_MZ": ln1,
            "ln_M2_over_MZ": ln2,
            "ln_M3_over_MZ": ln3,
        },
        "analytical_c_windows": {
            "c_needed_for_delta1_window": list(c_d1_interval),
            "c_needed_for_delta2_window": list(c_d2_interval),
            "intersection_exists": has_intersection,
            "c_intersection": [c_intersect_lo, c_intersect_hi] if has_intersection else None,
            "c_intersection_width": (c_intersect_hi - c_intersect_lo) if has_intersection else 0,
        },
        "ugp_candidate_results": candidate_results,
        "any_candidate_closes": any(r["both_in_window"] for r in candidate_results),
    }


# ──────────────────────────────────────────────────────────────────────────
# APPROACH 2: Casimir-based  δ_G ∝ C₂(G)  or  C₂(G)/dim(G)
# ──────────────────────────────────────────────────────────────────────────

def approach2_casimir():
    """
    Test several Casimir-based forms:
      2a. δ_G = c · C₂_adj(G)       (adjoint Casimir: 0, 2, 3)
      2b. δ_G = c · C₂_fund(G)      (fundamental Casimir: 0, 3/4, 4/3)
      2c. δ_G = c · C₂_adj(G)/dim(G)  (= 0, 2/3, 3/8)
      2d. δ_G = c · C₂_fund(G)/dim(G) (= 0, 1/4, 1/6)

    U(1)_Y has C₂_adj = 0 and C₂_fund ~ 0 in the pure-abelian limit.
    This means any Casimir-based form gives δ₁ = 0, which is NOT in the
    δ₁ window (which requires δ₁ ∈ (-0.00289, -0.00244)).

    We test this explicitly, document the structural reason it fails,
    and also test non-zero U(1) Casimir conventions.

    Alternative U(1) Casimir conventions:
      Weak hypercharge: Y = 1/2 for doublet → C₂_Y = Y² = 1/4
      The SM uses g₁ = g_Y (hypercharge coupling), so C₂ = (Y)² = 1/4
      for the standard doublet normalization.
    """
    forms = {
        "adj": (C2_ADJ["U1"], C2_ADJ["SU2"], C2_ADJ["SU3"]),
        "fund": (C2_FUND["U1"], C2_FUND["SU2"], C2_FUND["SU3"]),
        "adj_over_dim": (
            C2_ADJ["U1"] / DIM_G["U1"],
            C2_ADJ["SU2"] / DIM_G["SU2"],
            C2_ADJ["SU3"] / DIM_G["SU3"],
        ),
        "fund_over_dim": (
            C2_FUND["U1"] / DIM_G["U1"],
            C2_FUND["SU2"] / DIM_G["SU2"],
            C2_FUND["SU3"] / DIM_G["SU3"],
        ),
        # Y = 1/2 hypercharge Casimir for U(1)
        "Y_half_adj": (1 / 4, C2_ADJ["SU2"], C2_ADJ["SU3"]),
        "Y_half_fund": (1 / 4, C2_FUND["SU2"], C2_FUND["SU3"]),
        # Y = 1 convention
        "Y_one_adj": (1, C2_ADJ["SU2"], C2_ADJ["SU3"]),
    }

    ugp_c_values = {
        "k_L2": K_L2,
        "k_gen2": K_GEN2,
        "delta_UGP": DELTA_UGP,
        "1/b1_int": 1 / B1_INT,
        "-k_L2": -K_L2,
        "-1/b1_int": -1 / B1_INT,
        "k_L2/phi": K_L2 / PHI,
        "-k_L2/phi": -K_L2 / PHI,
        "-k_L2/b1_int": -K_L2 / B1_INT,
    }

    all_results = []

    for form_name, (c1_factor, c2_factor, c3_factor) in forms.items():
        form_info = {
            "form": form_name,
            "casimir_factors": {"U1": c1_factor, "SU2": c2_factor, "SU3": c3_factor},
            "delta1_is_zero": (c1_factor == 0),
            "analytical_notes": [],
        }

        if c1_factor == 0:
            form_info["analytical_notes"].append(
                "U(1) Casimir is 0 → δ₁ = 0 always → cannot enter δ₁ window → structural miss for this Casimir form"
            )
            # Still compute c window for δ₂ only
            if c2_factor != 0:
                c_for_d2_lo = DELTA2_LO / c2_factor
                c_for_d2_hi = DELTA2_HI / c2_factor
                form_info["c_window_for_delta2_only"] = sorted([c_for_d2_lo, c_for_d2_hi])
        else:
            # Compute analytical c windows
            c_d1_lo = DELTA1_LO / c1_factor
            c_d1_hi = DELTA1_HI / c1_factor
            c_d2_lo = DELTA2_LO / c2_factor
            c_d2_hi = DELTA2_HI / c2_factor
            c_int_lo = max(min(c_d1_lo, c_d1_hi), min(c_d2_lo, c_d2_hi))
            c_int_hi = min(max(c_d1_lo, c_d1_hi), max(c_d2_lo, c_d2_hi))
            has_int = c_int_lo < c_int_hi
            form_info["c_intersection"] = {
                "exists": has_int,
                "range": [c_int_lo, c_int_hi] if has_int else None,
                "c_central": (c_int_lo + c_int_hi) / 2 if has_int else None,
            }
            if has_int:
                form_info["analytical_notes"].append(
                    f"Intersection exists: c ∈ ({c_int_lo:.6g}, {c_int_hi:.6g})"
                )

        # Test UGP-motivated c values
        candidate_results = []
        for c_name, c in ugp_c_values.items():
            delta1 = c * c1_factor
            delta2 = c * c2_factor
            res = evaluate_approach(
                delta1, delta2,
                f"A2_{form_name}_{c_name}",
                f"Casimir-based ({form_name}): δ_G = {c_name} · C₂_({form_name})(G)"
            )
            res["c_value"] = c
            candidate_results.append(res)

        form_info["candidate_results"] = candidate_results
        form_info["any_candidate_closes"] = any(r["both_in_window"] for r in candidate_results)
        all_results.append(form_info)

    return {
        "approach": "2_Casimir_based",
        "forms_tested": [r["form"] for r in all_results],
        "structural_finding": (
            "Pure-abelian Casimir forms (adj, fund, adj/dim, fund/dim) give δ₁=0, "
            "which lies ~6σ above the δ₁ window — structural miss unless non-zero Y convention used."
        ),
        "results_by_form": all_results,
        "any_form_closes": any(r["any_candidate_closes"] for r in all_results),
    }


# ──────────────────────────────────────────────────────────────────────────
# APPROACH 3: Anomalous-dimension  δ_G = c · b_G
# ──────────────────────────────────────────────────────────────────────────

def approach3_anomalous_dim():
    """
    δ_G = c · b_G where b_G are the 1-loop SM beta coefficients:
      b_{U(1)_Y} = +41/6 ≈ +6.833
      b_{SU(2)}  = -19/6 ≈ -3.167
      b_{SU(3)}  = -7

    Closure windows need δ₁ < 0 and δ₂ < 0.
    Since b₁ > 0 we need c < 0 for δ₁ < 0.
    Since b₂ < 0 and c < 0 we get δ₂ > 0 — this creates a sign conflict.

    So the simple δ_G = c · b_G form cannot simultaneously achieve
    δ₁ < 0 AND δ₂ < 0. We document this structural obstruction.

    Alternative: δ_G = c · |b_G| — but this doesn't use the sign information.
    Alternative: δ_G = c · (b_G + offset) — we scan for offsets.
    Alternative: δ_G = c₁ · b_G + c₀ — two-parameter fit (not UGP-native unless c₀ derivable).

    We test:
      3a. δ_G = c · b_G  (simple; show sign obstruction)
      3b. δ_G = c · |b_G|  (absolute value)
      3c. δ_G = c · b_G + d  for UGP-motivated d offsets
      3d. δ_G = (c · b_G) / b₁_int  (normalised by Paper 1 integer b₁)
    """
    b1 = B_COEFF["U1"]    # +6.8333
    b2 = B_COEFF["SU2"]   # -3.1667
    b3 = B_COEFF["SU3"]   # -7.0

    # ── 3a: simple c·b_G ───────────────────────────────────────────────────
    # Window constraints: c·b₁ ∈ (DELTA1_LO, DELTA1_HI) → c < 0 (since b₁ > 0)
    #                     c·b₂ ∈ (DELTA2_LO, DELTA2_HI) → c > 0 (since b₂ < 0) — conflict!
    c_for_d1 = (DELTA1_LO / b1, DELTA1_HI / b1)     # both negative
    c_for_d2 = (DELTA2_LO / b2, DELTA2_HI / b2)     # b₂ < 0 → reverses
    c_d1_interval = (min(*c_for_d1), max(*c_for_d1))
    c_d2_interval = (min(*c_for_d2), max(*c_for_d2))
    sign_conflict = (c_d1_interval[1] < c_d2_interval[0]) or (c_d2_interval[1] < c_d1_interval[0])

    simple_candidates = []
    for c_name, c in {
        "k_L2": K_L2, "-k_L2": -K_L2,
        "k_gen2": K_GEN2, "-k_gen2": -K_GEN2,
        "delta_UGP": DELTA_UGP, "-delta_UGP": -DELTA_UGP,
        "1/b1_int": 1/B1_INT, "-1/b1_int": -1/B1_INT,
        "k_L2/b1_int": K_L2/B1_INT, "-k_L2/b1_int": -K_L2/B1_INT,
        "k_L2/phi": K_L2/PHI, "-k_L2/phi": -K_L2/PHI,
    }.items():
        res = evaluate_approach(c * b1, c * b2, f"A3a_{c_name}", f"Anomalous-dim (simple): δ_G = {c_name}·b_G")
        res["c_value"] = c
        simple_candidates.append(res)

    # ── 3b: c·|b_G| ────────────────────────────────────────────────────────
    abs_b = {"U1": abs(b1), "SU2": abs(b2), "SU3": abs(b3)}
    # Both |b₁| > 0 and |b₂| > 0; need c < 0 for both windows.
    c_for_abs_d1 = (DELTA1_LO / abs(b1), DELTA1_HI / abs(b1))
    c_for_abs_d2 = (DELTA2_LO / abs(b2), DELTA2_HI / abs(b2))
    c_abs_d1_interval = (min(*c_for_abs_d1), max(*c_for_abs_d1))
    c_abs_d2_interval = (min(*c_for_abs_d2), max(*c_for_abs_d2))
    c_abs_int_lo = max(c_abs_d1_interval[0], c_abs_d2_interval[0])
    c_abs_int_hi = min(c_abs_d1_interval[1], c_abs_d2_interval[1])
    abs_has_intersection = c_abs_int_lo < c_abs_int_hi

    abs_candidates = []
    for c_name, c in {
        "-k_L2": -K_L2, "-k_gen2/b1_int": -K_GEN2/B1_INT,
        "-1/b1_int": -1/B1_INT, "-k_L2/phi": -K_L2/PHI,
        "-k_L2/b1_int": -K_L2/B1_INT, "-k_L2*phi": -K_L2*PHI,
        "-delta_UGP/10": DELTA_UGP/10,  # delta_UGP is negative; /10 makes it less negative
    }.items():
        res = evaluate_approach(c * abs(b1), c * abs(b2), f"A3b_{c_name}", f"Anomalous-dim (abs): δ_G = {c_name}·|b_G|")
        res["c_value"] = c
        abs_candidates.append(res)

    if abs_has_intersection:
        c_abs_central = (c_abs_int_lo + c_abs_int_hi) / 2
        res = evaluate_approach(c_abs_central * abs(b1), c_abs_central * abs(b2),
                                "A3b_c_central", "Anomalous-dim (abs): c at intersection center")
        res["c_value"] = c_abs_central
        abs_candidates.append(res)

    # ── 3c: (c·b_G)/b₁_int normalised form ─────────────────────────────────
    norm_candidates = []
    for c_name, c in {
        "k_L2": K_L2, "-k_L2": -K_L2,
        "k_gen2": K_GEN2, "1.0": 1.0, "-1.0": -1.0,
        "k_L2*phi": K_L2*PHI, "-k_L2*phi": -K_L2*PHI,
    }.items():
        d1 = c * b1 / B1_INT
        d2 = c * b2 / B1_INT
        res = evaluate_approach(d1, d2, f"A3c_{c_name}", f"Anomalous-dim (norm): δ_G = {c_name}·b_G/b₁_int")
        res["c_value"] = c
        norm_candidates.append(res)

    return {
        "approach": "3_Anomalous_dimension",
        "beta_coefficients": {"b_U1": b1, "b_SU2": b2, "b_SU3": b3},
        "form_3a_simple": {
            "formula": "delta_G = c * b_G",
            "sign_conflict_present": sign_conflict,
            "sign_conflict_explanation": (
                "b_U1 > 0 and b_SU2 < 0; δ₁ window requires c < 0 but δ₂ window requires c > 0 — "
                "no single c can close both simultaneously in this form."
            ) if sign_conflict else "No sign conflict (unexpected).",
            "c_window_for_delta1": list(c_d1_interval),
            "c_window_for_delta2": list(c_d2_interval),
            "candidate_results": simple_candidates,
        },
        "form_3b_absolute": {
            "formula": "delta_G = c * |b_G|",
            "c_intersection_exists": abs_has_intersection,
            "c_intersection": [c_abs_int_lo, c_abs_int_hi] if abs_has_intersection else None,
            "candidate_results": abs_candidates,
        },
        "form_3c_normalised": {
            "formula": "delta_G = c * b_G / b1_int",
            "candidate_results": norm_candidates,
        },
        "any_form_closes": (
            any(r["both_in_window"] for r in simple_candidates) or
            any(r["both_in_window"] for r in abs_candidates) or
            any(r["both_in_window"] for r in norm_candidates)
        ),
    }


# ──────────────────────────────────────────────────────────────────────────
# APPROACH 4: Quarter-Lock-extended
# ──────────────────────────────────────────────────────────────────────────

def approach4_quarter_lock():
    """
    The Quarter-Lock identity: k_M = k_gen² + k_L²/4

    Explore whether the gauge sector has an analogous decomposition
    that produces coupling-specific corrections.

    thm_ucl_3 (Möbius triple Vandermonde-uniqueness) shows the gauge sector
    has three invariants. We hypothesize:
      δ_G = f_G(k_gen², k_L², k_M)  coupling-specific via some group index.

    Forms to test:
      4a. δ_G = k_gen² · w_G where w_G is a group-specific weight
      4b. δ_G = k_M · w_G (quarter-lock value)
      4c. δ_G = (k_gen² + α_G · k_L²) for group-specific α_G
      4d. δ_G uses Weyl order L_G as the coupling-specific index

    We also test the ratio δ₂/δ₁ ≈ 5.96 structural interpretation:
      From SC-AA, the target is δ₂/δ₁ ≈ 5.96.
      The Quarter-Lock constants:
        k_M = -0.8056..., k_L² = 0.01367..., k_gen² = -0.8090...
        k_L²/k_gen² = -0.01689..., k_gen²/k_L² = -59.17...
      Is 5.96 related to any of these?
    """
    # Target ratio
    target_ratio = (DELTA2_LO + DELTA2_HI) / 2 / ((DELTA1_LO + DELTA1_HI) / 2)  # ≈ 5.96

    # UGP constants
    k_gen2 = K_GEN2
    k_l2 = K_L2
    k_m = K_M

    # Weyl orders from SC-AA
    L_G = {"U1": 1, "SU2": 2, "SU3": 6}

    results = []

    # ── 4a: δ_G = k_gen² · w_G for various w_G ─────────────────────────────
    # We need δ₁/δ₂ ≈ 1/5.96 ≈ 0.1678
    # So w_1/w_2 ≈ 0.1678
    # Candidates: w_G ∝ 1/L_G, w_G ∝ 1/L_G², w_G ∝ k_L² · L_G, etc.
    for w_label, (w1, w2) in {
        "1/L_G": (1/L_G["U1"], 1/L_G["SU2"]),
        "1/L_G^2": (1/L_G["U1"]**2, 1/L_G["SU2"]**2),
        "k_L2*L_G": (k_l2 * L_G["U1"], k_l2 * L_G["SU2"]),
        "1/(L_G*phi)": (1/(L_G["U1"]*PHI), 1/(L_G["SU2"]*PHI)),
        "1/(L_G*b1_int)": (1/(L_G["U1"]*B1_INT), 1/(L_G["SU2"]*B1_INT)),
        "L_G/(b1_int^2)": (L_G["U1"]/B1_INT**2, L_G["SU2"]/B1_INT**2),
    }.items():
        d1 = k_gen2 * w1
        d2 = k_gen2 * w2
        res = evaluate_approach(d1, d2, f"A4a_{w_label}", f"QL-ext: δ_G = k_gen² · ({w_label})")
        res["ratio_delta2_delta1"] = d2/d1 if d1 != 0 else None
        results.append(res)

    # ── 4b: δ_G = k_M · w_G ────────────────────────────────────────────────
    for w_label, (w1, w2) in {
        "1/L_G": (1/L_G["U1"], 1/L_G["SU2"]),
        "k_L2*L_G": (k_l2 * L_G["U1"], k_l2 * L_G["SU2"]),
    }.items():
        d1 = k_m * w1
        d2 = k_m * w2
        res = evaluate_approach(d1, d2, f"A4b_{w_label}", f"QL-ext: δ_G = k_M · ({w_label})")
        res["ratio_delta2_delta1"] = d2/d1 if d1 != 0 else None
        results.append(res)

    # ── 4c: δ_G = (k_gen² + α_G · k_L²) for group-specific α_G ────────────
    # We need δ_G to be coupling-specific; use α_G = c_G as a group weight.
    # Special case: if α_G = L_G/4 → δ_G = k_gen² + L_G * k_L²/4
    for alpha_label, alpha_fn in {
        "L_G/4": lambda lg: lg / 4,
        "L_G": lambda lg: lg,
        "L_G^2/4": lambda lg: lg**2 / 4,
        "1/(L_G*4)": lambda lg: 1 / (lg * 4),
    }.items():
        d1 = k_gen2 + alpha_fn(L_G["U1"]) * k_l2
        d2 = k_gen2 + alpha_fn(L_G["SU2"]) * k_l2
        res = evaluate_approach(d1, d2, f"A4c_{alpha_label}", f"QL-ext: δ_G = k_gen² + (α_G={alpha_label})·k_L²")
        res["alpha_1"] = alpha_fn(L_G["U1"])
        res["alpha_2"] = alpha_fn(L_G["SU2"])
        res["ratio_delta2_delta1"] = d2/d1 if d1 != 0 else None
        results.append(res)

    # ── 4d: Is δ₂/δ₁ ratio ≈ 5.96 explained by any QL ratio? ───────────────
    ratio_checks = {
        "k_gen2/k_L2": k_gen2 / k_l2,
        "k_L2/k_gen2": k_l2 / k_gen2,
        "1/k_L2": 1 / k_l2,
        "1/k_gen2": 1 / k_gen2,
        "b1_int*k_L2": B1_INT * k_l2,
        "b1_int/10": B1_INT / 10,
        "phi^4": PHI**4,
        "phi^3": PHI**3,
        "phi^2*2": PHI**2 * 2,
        "L_SU2/k_L2": L_G["SU2"] / k_l2,
        "1/(k_L2*phi)": 1 / (k_l2 * PHI),
    }
    ratio_analysis = {
        "target_delta2_over_delta1": target_ratio,
        "ugp_ratio_candidates": {k: {"value": v, "distance_from_target": abs(v - target_ratio)}
                                 for k, v in ratio_checks.items()},
    }
    # Find closest
    closest = min(ratio_checks.items(), key=lambda kv: abs(kv[1] - target_ratio))
    ratio_analysis["closest_candidate"] = {"name": closest[0], "value": closest[1],
                                            "distance": abs(closest[1] - target_ratio)}

    return {
        "approach": "4_Quarter_Lock_extended",
        "ugp_constants": {
            "k_gen2": k_gen2, "k_L2": k_l2, "k_M": k_m,
            "phi": PHI, "b1_int": B1_INT,
        },
        "target_ratio_delta2_over_delta1": target_ratio,
        "ratio_analysis": ratio_analysis,
        "candidate_results": results,
        "any_candidate_closes": any(r["both_in_window"] for r in results),
    }


# ──────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────

def main():
    timestamp = datetime.datetime.utcnow().isoformat() + "Z"

    # ── Build prediction block (NO PDG values appended yet) ─────────────────
    prediction_block = {
        "comp_id": "COMP-P01-EE",
        "title": "sin²θ_W Phase 1 — Four Approach Candidates",
        "spec_reference": "specs/IN-PROCESS/EPIC_CLUSTER7_RESEARCH_GRADE/05_SPEC_SIN2_THETAW_CLOSURE.md",
        "prior_art": ["COMP-P01-Z", "COMP-P01-AA", "COMP-P01-CC"],
        "timestamp_utc": timestamp,
        "lean_certified_inputs": {
            "g1sq_bare": {"exact": "16/125", "float": G1SQ_BARE},
            "g2sq_bare": {"exact": "2329/5400", "float": G2SQ_BARE},
            "g3sq_bare": {"exact": "41075281/27648000", "float": G3SQ_BARE},
            "k_gen2": {"exact": "-phi/2", "float": K_GEN2},
            "k_L2": {"exact": "7/512", "float": K_L2},
            "k_M": {"exact": "k_gen2 + k_L2/4", "float": K_M},
            "delta_UGP": {"exact": "k_gen2 + k_L2/4", "float": DELTA_UGP},
            "phi": PHI,
            "b1_int": B1_INT,
        },
        "sc_cc_inputs": {
            "M1_inv_solved_GeV": M1_INV,
            "M2_inv_solved_GeV": M2_INV,
            "M3_inv_solved_GeV": M3_INV,
            "M_Z_GeV": M_Z,
        },
        "pdg_targets": {
            "sin2_thetaW_central": PDG_SIN2,
            "sin2_thetaW_sigma": PDG_SIN2_SIGMA,
            "alpha_w_central": PDG_AW_CENTRAL,
            "alpha_w_sigma": PDG_AW_SIGMA,
        },
        "closure_windows_1sigma": {
            "delta1_window": [DELTA1_LO, DELTA1_HI],
            "delta1_central": (DELTA1_LO + DELTA1_HI) / 2,
            "delta2_window": [DELTA2_LO, DELTA2_HI],
            "delta2_central": (DELTA2_LO + DELTA2_HI) / 2,
            "target_ratio_delta2_over_delta1": ((DELTA2_LO + DELTA2_HI) / 2) / ((DELTA1_LO + DELTA1_HI) / 2),
        },
        "approach_results": {
            "approach_1": approach1_rg(),
            "approach_2": approach2_casimir(),
            "approach_3": approach3_anomalous_dim(),
            "approach_4": approach4_quarter_lock(),
        },
    }

    # ── SHA-256 the prediction block BEFORE appending PDG comparison ────────
    pred_json_str = json.dumps(prediction_block, sort_keys=True, separators=(",", ":"))
    sha256_pred = hashlib.sha256(pred_json_str.encode("utf-8")).hexdigest()

    # ── Summary: which approaches close? ────────────────────────────────────
    a1 = prediction_block["approach_results"]["approach_1"]
    a2 = prediction_block["approach_results"]["approach_2"]
    a3 = prediction_block["approach_results"]["approach_3"]
    a4 = prediction_block["approach_results"]["approach_4"]

    any_close = (
        a1["any_candidate_closes"] or
        a2["any_form_closes"] or
        a3["any_form_closes"] or
        a4["any_candidate_closes"]
    )

    # ── Best near-miss (closest to closing both windows) ────────────────────
    all_candidates = []
    for r in a1["ugp_candidate_results"]:
        all_candidates.append(r)
    for form in a2["results_by_form"]:
        all_candidates.extend(form.get("candidate_results", []))
    for r in a3["form_3a_simple"]["candidate_results"]:
        all_candidates.append(r)
    for r in a3["form_3b_absolute"]["candidate_results"]:
        all_candidates.append(r)
    for r in a3["form_3c_normalised"]["candidate_results"]:
        all_candidates.append(r)
    all_candidates.extend(a4["candidate_results"])

    def closeness_score(r):
        d1_dist = abs(r.get("delta_1_window_dist", 1.0))
        d2_dist = abs(r.get("delta_2_window_dist", 1.0))
        return d1_dist + d2_dist

    sorted_candidates = sorted(all_candidates, key=closeness_score)
    top5_near_miss = sorted_candidates[:5]

    # ── PDG comparison block ────────────────────────────────────────────────
    pdg_comparison = {
        "prediction_block_sha256": sha256_pred,
        "phase1_verdict": "CLOSES" if any_close else "MAP (all miss)",
        "any_approach_closes_both_windows": any_close,
        "approach_1_closes": a1["any_candidate_closes"],
        "approach_1_analytical_intersection_exists": a1["analytical_c_windows"]["intersection_exists"],
        "approach_1_intersection": a1["analytical_c_windows"]["c_intersection"],
        "approach_2_closes": a2["any_form_closes"],
        "approach_2_structural_finding": a2["structural_finding"],
        "approach_3_closes": a3["any_form_closes"],
        "approach_3_sign_conflict": a3["form_3a_simple"]["sign_conflict_present"],
        "approach_3b_intersection_exists": a3["form_3b_absolute"]["c_intersection_exists"],
        "approach_3b_intersection": a3["form_3b_absolute"]["c_intersection"],
        "approach_4_closes": a4["any_candidate_closes"],
        "approach_4_ratio_closest": a4["ratio_analysis"]["closest_candidate"],
        "top5_near_miss_candidates": top5_near_miss,
        "pdg_bare_sin2_thetaW": sin2_thetaw(G1SQ_BARE, G2SQ_BARE),
        "pdg_target_sin2_thetaW": PDG_SIN2,
        "pdg_bare_gap_sigma": sigma_from_target(sin2_thetaw(G1SQ_BARE, G2SQ_BARE), PDG_SIN2, PDG_SIN2_SIGMA),
    }

    # ── Full output ─────────────────────────────────────────────────────────
    output = {
        "prediction_block_precomparison": prediction_block,
        "sha256_prediction_block": sha256_pred,
        "pdg_comparison": pdg_comparison,
    }

    # Print summary to stdout
    print(f"COMP-P01-EE: sin²θ_W Phase 1")
    print(f"Timestamp: {timestamp}")
    print(f"Prediction block SHA-256: {sha256_pred}")
    print()
    print(f"RESULTS:")
    print(f"  Approach 1 (RG-based):            {'✅ CLOSES' if a1['any_candidate_closes'] else '❌ miss'}")
    print(f"    → analytical c-intersection:    {'EXISTS' if a1['analytical_c_windows']['intersection_exists'] else 'EMPTY'}")
    if a1["analytical_c_windows"]["intersection_exists"]:
        lo, hi = a1["analytical_c_windows"]["c_intersection"]
        print(f"    → c ∈ ({lo:.6g}, {hi:.6g})")
    print(f"  Approach 2 (Casimir-based):        {'✅ CLOSES' if a2['any_form_closes'] else '❌ miss'}")
    print(f"  Approach 3 (Anomalous-dim):        {'✅ CLOSES' if a3['any_form_closes'] else '❌ miss'}")
    print(f"    → sign conflict (simple form):  {a3['form_3a_simple']['sign_conflict_present']}")
    print(f"    → |b_G| intersection exists:    {a3['form_3b_absolute']['c_intersection_exists']}")
    if a3["form_3b_absolute"]["c_intersection_exists"]:
        lo, hi = a3["form_3b_absolute"]["c_intersection"]
        print(f"    → c ∈ ({lo:.6g}, {hi:.6g})")
    print(f"  Approach 4 (Quarter-Lock-ext):     {'✅ CLOSES' if a4['any_candidate_closes'] else '❌ miss'}")
    print()
    print(f"Phase 1 verdict: {'🎯 CLOSES — proceed to Phase 2!' if any_close else '📋 MAP — all approaches miss; document structural obstructions'}")
    print()
    print("Top 5 near-miss candidates (by combined window distance):")
    for i, r in enumerate(top5_near_miss, 1):
        d1d = r.get("delta_1_window_dist", "n/a")
        d2d = r.get("delta_2_window_dist", "n/a")
        both = r.get("both_in_window", False)
        print(f"  {i}. {r['label']}: δ₁={r['delta_1']:.6g}, δ₂={r['delta_2']:.6g}  "
              f"[d1_dist={d1d:.4g}, d2_dist={d2d:.4g}] {'✅' if both else ''}")

    return output


if __name__ == "__main__":
    output = main()
    out_path = "comp_p01_EE_sin2_thetaW_phase1.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nOutput written to {out_path}")
    import subprocess
    result = subprocess.run(
        ["python3", "-c", f"import json; json.load(open('{out_path}')); print('JSON valid')"],
        capture_output=True, text=True
    )
    print(result.stdout.strip() if result.returncode == 0 else f"JSON ERROR: {result.stderr}")
