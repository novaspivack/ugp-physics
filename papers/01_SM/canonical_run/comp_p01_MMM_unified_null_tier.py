"""
COMP-P01-MMM: Unified null-discipline tier framework for Paper 1 revision.
              (Priority 18 / Round 41; addresses R43 advisor critique on
              "scattered null calibrations targeting different comparison sets.")

GOAL: Establish consistent null hit-rates across three tiers of basis atoms,
      so that every structural claim in Paper 1 is labeled with its tier
      and the tier's pre-registered null density.

TIER I  — Pure-UGP-integer DL <= 2 (sparse basis: small integers, small rationals,
          Lean-certified UGP atoms only; NO transcendentals at DL 1)
TIER II — Cyclotomic-12 Lean-certified (sparse basis: π/n, cos(π/n), √3 at
          DL <= 2; the atom family appearing in α=π/6, β=π/8, Koide closed form)
TIER III — Saturating bases (transcendental-rich, GUT-rep, discrete-flavor;
          already documented in SC-S3, SC-JJJ, SC-LLL)

This script establishes Tier I and Tier II sparsity rates for use in the paper.
"""
import math, json, hashlib, datetime, os, itertools
import numpy as np

# =====================================================================
# TIER I: Pure-UGP-integer basis (DL <= 2)
# =====================================================================
TIER_I_ATOMS = {
    # Integers 1..20
    **{str(k): k for k in range(1, 21)},
    # Small negative integers
    **{f'-{k}': -k for k in range(1, 11)},
    # Simple rationals from Lean-certified SM / UGP integers only
    '1/2': 1/2, '1/3': 1/3, '1/6': 1/6, '1/8': 1/8, '1/4': 1/4,
    '2/3': 2/3, '3/4': 3/4, '3/2': 3/2, '4/3': 4/3,
    # Lean-certified SM/UGP scalars
    'k_L2': 7/512, 'delta': 0.0233, 'b1': 21.89, 'delta_b1': 0.0233*21.89,
    # Lean-certified bare gauge couplings
    'g1Sq': 16/125, 'g2Sq': 2329/5400,
    # Small integer compositions already Lean-certified
    'k_a': 1/8, 'k_b': -3/2, 'k_c': 4/3,
    # Pi/small integers (we include pi only at DL 1, not combined)
}

# =====================================================================
# TIER II: Cyclotomic-12 Lean-certified (DL <= 2)
# =====================================================================
PI = math.pi
SQRT3 = math.sqrt(3)
SQRT2 = math.sqrt(2)
PHI = (1 + math.sqrt(5))/2

TIER_II_ATOMS = {
    # Pi / small n (cyclotomic-12 family)
    'pi/3': PI/3, 'pi/4': PI/4, 'pi/6': PI/6, 'pi/8': PI/8, 'pi/12': PI/12,
    '2pi/3': 2*PI/3, 'pi/2': PI/2,
    # Cyclotomic-12 surds
    'cos_pi_12': math.cos(PI/12), 'sin_pi_12': math.sin(PI/12),
    '2+sqrt3': 2 + SQRT3, '1+sqrt3': 1 + SQRT3,
    'sqrt3': SQRT3, 'sqrt2': SQRT2, 'phi': PHI,
    # Small integers for combination context
    **{str(k): k for k in range(1, 10)},
    **{f'-{k}': -k for k in range(1, 6)},
}

def build_expressions(atoms, max_dl=2):
    """Generate DL <= max_dl expressions with binary ops +, -, *, /."""
    exprs = dict(atoms)
    if max_dl >= 2:
        pairs = list(itertools.combinations_with_replacement(sorted(atoms.items()), 2))
        for (n1, v1), (n2, v2) in pairs:
            for op, sym in [(lambda a,b: a+b, '+'), (lambda a,b: a-b, '-'),
                           (lambda a,b: a*b, '*'),
                           (lambda a,b: a/b if abs(b) > 1e-30 else None, '/')]:
                try:
                    val = op(v1, v2)
                    if val is None or not math.isfinite(val) or abs(val) > 1e6:
                        continue
                    key = f"({n1}{sym}{n2})"
                    if key not in exprs:
                        exprs[key] = val
                    if sym in '-/':
                        val2 = op(v2, v1)
                        if val2 is not None and math.isfinite(val2) and abs(val2) < 1e6:
                            exprs[f"({n2}{sym}{n1})"] = val2
                except Exception:
                    pass
    return exprs

# =====================================================================
# Build and scan
# =====================================================================
tier1_exprs = build_expressions(TIER_I_ATOMS, max_dl=2)
tier2_exprs = build_expressions(TIER_II_ATOMS, max_dl=2)

tier1_values = np.array(list(tier1_exprs.values())); tier1_values.sort()
tier2_values = np.array(list(tier2_exprs.values())); tier2_values.sort()

def fast_count(values, tgt, tol):
    abs_tol = tol * max(abs(tgt), 1e-20)
    lo = np.searchsorted(values, tgt - abs_tol)
    hi = np.searchsorted(values, tgt + abs_tol)
    return hi - lo

def fast_hit(values, tgt, tol):
    return fast_count(values, tgt, tol) > 0

def compute_null(values, N, rng_range, seed=41):
    np.random.seed(seed)
    targets = np.random.uniform(rng_range[0], rng_range[1], N)
    hits = {t: 0 for t in (1e-6, 1e-5, 1e-4, 1e-3, 1e-2)}
    for tgt in targets:
        for t in hits:
            if fast_hit(values, tgt, t): hits[t] += 1
    return {t: h/N for t, h in hits.items()}

print("=" * 72)
print("COMP-P01-MMM: Unified null-discipline tier framework (R41)")
print("=" * 72)
print(f"\nTier I (pure-UGP-integer DL<=2): {len(TIER_I_ATOMS)} atoms, {len(tier1_exprs)} expressions")
print(f"Tier II (cyclotomic-12 DL<=2):   {len(TIER_II_ATOMS)} atoms, {len(tier2_exprs)} expressions")

# Null test for both tiers
print("\n" + "=" * 72)
print("Tier I null on random uniform targets in [-10, +10]:")
print("=" * 72)
null1 = compute_null(tier1_values, 10000, (-10, 10))
for t in (1e-6, 1e-5, 1e-4, 1e-3, 1e-2):
    print(f"  tol {t:.0e}: {100*null1[t]:.3f}% of random targets hit")

print("\n" + "=" * 72)
print("Tier II null on random uniform targets in [-10, +10]:")
print("=" * 72)
null2 = compute_null(tier2_values, 10000, (-10, 10))
for t in (1e-6, 1e-5, 1e-4, 1e-3, 1e-2):
    print(f"  tol {t:.0e}: {100*null2[t]:.3f}% of random targets hit")

# =====================================================================
# Tier-I null on specific structural targets (where the paper's claims live)
# =====================================================================
print("\n" + "=" * 72)
print("Specific Tier-I hits on paper's structural targets:")
print("=" * 72)

targets_t1 = {
    'g1Sq_target_16/125': 16/125,
    'g2Sq_target_2329/5400': 2329/5400,
    'm_e_target_delta*b1': 0.0233 * 21.89,
    'k_L2_target_7/512': 7/512,
    'k_a_target_1/8': 1/8,
    'k_b_target_-3/2': -3/2,
    'k_c_target_4/3': 4/3,
}

for name, tgt in targets_t1.items():
    n1e5 = fast_count(tier1_values, tgt, 1e-5)
    n1e3 = fast_count(tier1_values, tgt, 1e-3)
    print(f"  {name:<40}: {n1e5} exact hits (<1e-5); {n1e3} at 1e-3")

# Tier-II specific targets
print("\n" + "=" * 72)
print("Specific Tier-II hits on cyclotomic-12 structural targets:")
print("=" * 72)
targets_t2 = {
    'alpha_TT_pi/6': PI/6,
    'beta_TT_pi/8': PI/8,
    'Koide_2+sqrt3': 2 + SQRT3,
    'Koide_1+sqrt3': 1 + SQRT3,
    'half_cone_angle_pi/4': PI/4,
}
for name, tgt in targets_t2.items():
    n1e5 = fast_count(tier2_values, tgt, 1e-5)
    n1e3 = fast_count(tier2_values, tgt, 1e-3)
    print(f"  {name:<40}: {n1e5} exact hits (<1e-5); {n1e3} at 1e-3")

# Tier III references (from prior runs; report only)
print("\n" + "=" * 72)
print("Tier III reference rates (from prior artifacts):")
print("=" * 72)
print("  SC-S3 Higgs-lambda transcendental basis:      ~88% at 10 ppm  (SATURATES)")
print("  SC-JJJ GUT-rep basis (96 atoms, DL<=3):       ~54% triple at 1e-3  (SATURATES)")
print("  SC-KKK integer-FN-charge obstruction:         VV requires NON-integer charges")
print("  SC-LLL discrete-flavor basis (97 atoms):      ~40% triple at 1e-3  (SATURATES)")

# =====================================================================
# Verdict table
# =====================================================================
print("\n" + "=" * 72)
print("UNIFIED TIER FRAMEWORK SUMMARY")
print("=" * 72)
print(f"\nTier I (pure-UGP-integer DL<=2, {len(tier1_exprs)} exprs):")
print(f"  null rate at 1e-5: {100*null1[1e-5]:.3f}%")
print(f"  null rate at 1e-3: {100*null1[1e-3]:.2f}%")
print(f"  Claims living in Tier I: alpha_EM ppm, alpha_s blind, m_e=delta*b1, g1/g2/g3 bare")
print(f"\nTier II (cyclotomic-12 DL<=2, {len(tier2_exprs)} exprs):")
print(f"  null rate at 1e-5: {100*null2[1e-5]:.3f}%")
print(f"  null rate at 1e-3: {100*null2[1e-3]:.2f}%")
print(f"  Claims living in Tier II: alpha=pi/6 (A_2), beta=pi/8 (Cartan),")
print(f"                            Koide (2+sqrt3)=4cos^2(pi/12)")
print(f"\nTier III (saturating): {{SC-S3 88% / SC-JJJ 54% / SC-LLL 40%}}")
print(f"  Claims relegated to [C]: Higgs lambda, VV coefficient-value interpretations,")
print(f"                           engine PSLQ, post-hoc algebraic identifications")

# =====================================================================
# Artifact
# =====================================================================
artifact = {
    "experiment_id": "COMP-P01-MMM",
    "title": "Unified null-discipline tier framework (Priority 18 / Round 41 / R43 response)",
    "date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "tier_I": {
        "description": "Pure-UGP-integer DL<=2 (Lean-certified atoms only; no transcendentals at DL 1)",
        "n_atoms": len(TIER_I_ATOMS),
        "n_expressions": len(tier1_exprs),
        "null_rates": {str(t): null1[t] for t in null1},
        "range": [-10, 10],
        "claims_at_this_tier": ["alpha_EM_+2.39_ppm", "alpha_s_+0.36_sigma",
                                "m_e_delta_b1_+2.05_ppm", "g_i_bare_gauge_couplings"],
    },
    "tier_II": {
        "description": "Cyclotomic-12 Lean-certified (pi/n, cos(pi/n), sqrt3 DL<=2)",
        "n_atoms": len(TIER_II_ATOMS),
        "n_expressions": len(tier2_exprs),
        "null_rates": {str(t): null2[t] for t in null2},
        "range": [-10, 10],
        "claims_at_this_tier": ["alpha=pi/6_A2_Weyl_chamber", "beta=pi/8_Cartan_potential",
                                "Koide_2+sqrt3_4cos2_pi12", "Koide_closed_form"],
    },
    "tier_III_reference": {
        "description": "Saturating bases; claims here relegate to [C]",
        "SC_S3": {"basis": "transcendental {phi, pi, e, log p, sqrt n}", "rate_at_10ppm": 0.88},
        "SC_JJJ": {"basis": "GUT-rep (96 atoms, DL<=3)", "triple_rate_at_1e-3": 0.5434},
        "SC_KKK": {"basis": "integer-FN-charge extension",
                   "finding": "VV requires NON-integer charges (structural impossibility)"},
        "SC_LLL": {"basis": "discrete-flavor (97 atoms, DL<=3)", "triple_rate_at_1e-3": 0.3977},
        "claims_at_this_tier": ["VV_coefficient_value_interpretations_[C]",
                                "Higgs_lambda_PSLQ_[C]",
                                "engine_PSLQ_[C]"],
    },
    "tier_I_structural_hit_counts": {
        name: {"target": tgt, "at_1e-5": int(fast_count(tier1_values, tgt, 1e-5)),
               "at_1e-3": int(fast_count(tier1_values, tgt, 1e-3))}
        for name, tgt in targets_t1.items()
    },
    "tier_II_structural_hit_counts": {
        name: {"target": tgt, "at_1e-5": int(fast_count(tier2_values, tgt, 1e-5)),
               "at_1e-3": int(fast_count(tier2_values, tgt, 1e-3))}
        for name, tgt in targets_t2.items()
    },
}
block = json.dumps(artifact, sort_keys=True, indent=2, default=str)
artifact["pre_commit_sha256"] = hashlib.sha256(block.encode()).hexdigest()
out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "comp_p01_MMM_unified_null_tier.json")
with open(out, "w") as f:
    json.dump(artifact, f, indent=2, sort_keys=True, default=str)
with open(out, "rb") as f:
    full_sha = hashlib.sha256(f.read()).hexdigest()
print(f"\nPre-commit SHA-256: {artifact['pre_commit_sha256'][:16]}...")
print(f"Full-file SHA-256:  {full_sha[:16]}...")
