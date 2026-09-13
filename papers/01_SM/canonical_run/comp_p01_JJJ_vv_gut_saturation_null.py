"""
COMP-P01-JJJ: VV GUT-basis saturation null test (Priority 9 / 37_SPEC /
              Round 37).  Tests whether the VV coefficient identifications
              (13/9, -7/6, -5/14) survive a combinatorial saturation null
              over a pre-registered "GUT-theoretic basis," using the same
              null-discipline methodology as SC-S3 (Higgs λ) and SC-T
              (engine PSLQ).

PROTOCOL:
1. Build a pre-registered basis of GUT-theoretic atoms (ranks, rep
   dimensions, SM hypercharges).  CRITICAL: basis is fixed before any
   target scan.
2. Commit SHA-256 of basis definition BEFORE scanning VV targets.
3. Scan basis at DL <= 3 for expressions matching each VV target at
   tolerances {1e-4, 1e-3, 1e-2} individually.
4. Null test: draw N = 10,000 random 3-target triples from a plausible
   distribution (uniform in [-2, +2] — envelope of VV coefficients);
   count fraction where all 3 can be simultaneously matched at <= 1e-3.
5. Compare VV's "3/3 matched" to null rate.

VERDICT CRITERIA:
- Outcome A (VV survives): R_null_triple(1e-3) <= 1%.  VV identifications
  are structurally distinguished from basis saturation.
- Outcome B (VV saturates): R_null_triple(1e-3) >= 10%.  VV identifications
  relegate to [C] appendix; paper narrative reshaped.
- Outcome C (moderate): 1% < R_null_triple(1e-3) < 10%.  Disclose as
  "moderate sparsity; identifications are suggestive but not independent."

IMPORTANT: the *VV log-linear relation* on masses (null density 1e-5, SC-VV)
is independent of this test and remains valid regardless of outcome.  Only
the GUT-representation-theoretic *interpretation* of the coefficient values
is under evaluation here.
"""

import math, json, hashlib, datetime, os, itertools
import numpy as np

# =====================================================================
# PRE-REGISTERED GUT-THEORETIC BASIS
# =====================================================================
# This basis is committed BEFORE running any target scan.  Its SHA-256
# is printed first so the user can verify no post-hoc basis modification.
#
# Atom selection rationale: we include every integer and rational that a
# GUT-theoretic identification of VV coefficients could plausibly use,
# based on the paper's current claims about 45_{SU(5)}, 126_{SO(10)},
# rank(SU(5)), dim(SU(3)_C^adj) + dim(U(1)_Y) = 9, and Y_{Q_L} = 1/6.
#
# The basis is DELIBERATELY DESIGNED to mimic what a GUT theorist would
# try when matching a new coefficient, NOT to hit the VV values exactly.
# =====================================================================

GUT_ATOMS = {
    # ---- Ranks of classical Lie groups ----
    'rank_SU2': 1, 'rank_SU3': 2, 'rank_SU4': 3, 'rank_SU5': 4, 'rank_SU6': 5,
    'rank_SU7': 6, 'rank_SU8': 7, 'rank_SO3': 1, 'rank_SO4': 2, 'rank_SO5': 2,
    'rank_SO6': 3, 'rank_SO7': 3, 'rank_SO8': 4, 'rank_SO9': 4, 'rank_SO10': 5,
    'rank_SO11': 5, 'rank_SO12': 6, 'rank_E6': 6, 'rank_E7': 7, 'rank_E8': 8,
    'rank_F4': 4, 'rank_G2': 2,

    # ---- Standard Lie-algebra dimensions ----
    'dim_SU2_adj': 3, 'dim_SU3_adj': 8, 'dim_SU4_adj': 15, 'dim_SU5_adj': 24,
    'dim_SU6_adj': 35, 'dim_SO10_adj': 45, 'dim_SO6_adj': 15, 'dim_SO8_adj': 28,
    'dim_E6_adj': 78, 'dim_E7_adj': 133, 'dim_E8_adj': 248,
    'dim_U1': 1,

    # ---- SU(5) reps commonly appearing in GUTs ----
    'dim_1_SU5': 1, 'dim_5_SU5': 5, 'dim_10_SU5': 10, 'dim_15_SU5': 15,
    'dim_24_SU5': 24, 'dim_40_SU5': 40, 'dim_45_SU5': 45, 'dim_50_SU5': 50,
    'dim_70_SU5': 70, 'dim_75_SU5': 75, 'dim_126_SU5': 126,
    'dim_175_SU5': 175, 'dim_200_SU5': 200,

    # ---- SO(10) reps ----
    'dim_1_SO10': 1, 'dim_10_SO10': 10, 'dim_16_SO10': 16, 'dim_45_SO10': 45,
    'dim_54_SO10': 54, 'dim_120_SO10': 120, 'dim_126_SO10': 126,
    'dim_144_SO10': 144, 'dim_210_SO10': 210,

    # ---- SU(3) reps (SM QCD) ----
    'dim_3_SU3': 3, 'dim_6_SU3': 6, 'dim_8_SU3': 8, 'dim_10_SU3': 10,
    'dim_15_SU3': 15, 'dim_27_SU3': 27,

    # ---- SU(2) reps ----
    'dim_2_SU2': 2, 'dim_3_SU2': 3, 'dim_4_SU2': 4, 'dim_5_SU2': 5,

    # ---- SM hypercharges ----
    'Y_QL': 1/6, 'Y_uR': 2/3, 'Y_dR': -1/3, 'Y_LL': -1/2, 'Y_eR': -1,
    'Y_H': 1/2, 'Y_QL_3': 1/2,                   # 3 * Y_QL = 1/2 (colour-charge unit)
    'B_L': 1/3,                                  # baryon-minus-lepton unit

    # ---- SM gauge-boson counts ----
    'n_gluons': 8, 'n_W': 3, 'n_B': 1, 'n_SM_bosons': 12,  # 8+3+1 = 12

    # ---- Small integers and simple ratios (minimal floor) ----
    'int_1': 1, 'int_2': 2, 'int_3': 3, 'int_4': 4, 'int_5': 5, 'int_6': 6,
    'int_7': 7, 'int_9': 9, 'int_12': 12, 'int_14': 14,

    # ---- Common fractions from physics ----
    'half': 1/2, 'third': 1/3, 'sixth': 1/6, 'quarter': 1/4,
    'neg_1': -1, 'neg_half': -1/2, 'neg_third': -1/3,

    # ---- Sign generators ----
    'minus_1': -1,
}

# =====================================================================
# Commit SHA of basis definition (pre-registration)
# =====================================================================
basis_def_str = json.dumps({k: v for k, v in sorted(GUT_ATOMS.items())},
                            indent=2, sort_keys=True)
basis_sha = hashlib.sha256(basis_def_str.encode('utf-8')).hexdigest()

# =====================================================================
# VV TARGETS (Paper 1 §4.9 current structural identifications)
# =====================================================================
VV_TARGETS = {
    'alpha_VV': 13/9,
    'beta_VV':  -7/6,
    'gamma_VV': -5/14,
}

# =====================================================================
# Expression-building (binary ops on atoms)
# =====================================================================
def build_expressions(atoms, max_dl=3):
    """Build dict of {expression_string: float_value} with DL <= max_dl."""
    exprs = dict(atoms)  # DL 1

    if max_dl >= 2:
        pairs = list(itertools.combinations_with_replacement(sorted(atoms.items()), 2))
        for (n1, v1), (n2, v2) in pairs:
            for op, sym in [(lambda a,b: a+b, '+'), (lambda a,b: a-b, '-'),
                           (lambda a,b: a*b, '*'),
                           (lambda a,b: a/b if abs(b) > 1e-30 else None, '/')]:
                try:
                    val = op(v1, v2)
                    if val is None or not math.isfinite(val) or abs(val) > 1e8:
                        continue
                    k = f"({n1}{sym}{n2})"
                    if k not in exprs:
                        exprs[k] = val
                    if sym in '-/':
                        val2 = op(v2, v1)
                        if val2 is not None and math.isfinite(val2) and abs(val2) < 1e8:
                            k2 = f"({n2}{sym}{n1})"
                            if k2 not in exprs:
                                exprs[k2] = val2
                except Exception:
                    pass

    if max_dl >= 3:
        # Limit DL=3 combinatorial explosion: cap DL-2 keys used
        dl2_keys = [k for k in exprs if k not in atoms][:2000]
        dl1_keys = list(atoms.keys())
        for k2 in dl2_keys:
            v2 = exprs[k2]
            for k1 in dl1_keys:
                v1 = exprs[k1]
                for op, sym in [(lambda a,b: a+b, '+'),
                               (lambda a,b: a*b, '*'),
                               (lambda a,b: a/b if abs(b) > 1e-30 else None, '/')]:
                    try:
                        val = op(v2, v1)
                        if val is None or not math.isfinite(val) or abs(val) > 1e8:
                            continue
                        k = f"({k2}{sym}{k1})"
                        if k not in exprs:
                            exprs[k] = val
                    except Exception:
                        pass
    return exprs

# =====================================================================
# Target scan helper
# =====================================================================
def scan_target(target, exprs, tols=(1e-5, 1e-4, 1e-3, 1e-2)):
    """Return dict tol -> list of (expr_name, expr_value, rel_err), sorted."""
    hits = {t: [] for t in tols}
    for name, val in exprs.items():
        if not math.isfinite(val):
            continue
        rel = abs(val - target) / max(abs(target), 1e-20)
        for t in tols:
            if rel < t:
                hits[t].append((name, val, rel))
    for t in tols:
        hits[t].sort(key=lambda x: x[2])
    return hits

# =====================================================================
# Execute
# =====================================================================
if __name__ == "__main__":
    print("=" * 72)
    print("COMP-P01-JJJ: VV GUT-basis saturation null test (Round 37)")
    print("Priority 9 of 37_SPEC; advisor's strongest pre-submission critique.")
    print("=" * 72)
    print()
    print(f"Pre-registered basis:   {len(GUT_ATOMS)} atoms")
    print(f"Basis definition SHA-256: {basis_sha}")
    print(f"(This SHA is committed BEFORE any target scan; no post-hoc changes allowed.)")
    print()

    print("Building DL <= 3 expressions...")
    exprs = build_expressions(GUT_ATOMS, max_dl=3)
    print(f"Total expressions: {len(exprs)}")
    print()

    # ---- Scan VV targets ----
    print("=" * 72)
    print("Phase 1: Scan VV coefficient targets")
    print("=" * 72)
    vv_hit_summary = {}
    for name, tgt in VV_TARGETS.items():
        hits = scan_target(tgt, exprs)
        vv_hit_summary[name] = {
            'target': tgt,
            'n_at_1e-5': len(hits[1e-5]),
            'n_at_1e-4': len(hits[1e-4]),
            'n_at_1e-3': len(hits[1e-3]),
            'n_at_1e-2': len(hits[1e-2]),
            'top_5_at_1e-3': [(n, float(v), float(r)) for n, v, r in hits[1e-3][:5]],
        }
        print(f"\n{name} = {tgt:+.6f}:")
        print(f"  Hits at 1e-5: {len(hits[1e-5])}")
        print(f"  Hits at 1e-4: {len(hits[1e-4])}")
        print(f"  Hits at 1e-3: {len(hits[1e-3])}")
        print(f"  Hits at 1e-2: {len(hits[1e-2])}")
        for n, v, r in hits[1e-3][:3]:
            print(f"    {n}  ->  {v:+.6f}  (rel {r:.2e})")

    # Pre-sort expression values for fast binary-search hit lookups
    exprs_values = np.array(list(exprs.values()))
    exprs_values.sort()
    print(f"Sorted expression value array ready ({len(exprs_values)} entries).")

    def fast_hit(tgt, tol):
        """Does any expression match tgt within tol (relative)?  O(log N)."""
        abs_tol = tol * max(abs(tgt), 1e-20)
        lo = np.searchsorted(exprs_values, tgt - abs_tol)
        hi = np.searchsorted(exprs_values, tgt + abs_tol)
        return hi > lo

    def fast_count(tgt, tol):
        abs_tol = tol * max(abs(tgt), 1e-20)
        lo = np.searchsorted(exprs_values, tgt - abs_tol)
        hi = np.searchsorted(exprs_values, tgt + abs_tol)
        return hi - lo

    # ---- Null test: individual-coefficient random-target scan ----
    print()
    print("=" * 72)
    print("Phase 2: Null test — single-target matching rate")
    print("=" * 72)
    print("Draw 10^4 random 1-targets uniform in [-2, +2];")
    print("count fraction with >= 1 basis expression at each tolerance.")

    np.random.seed(37)
    N1 = 10000
    null_random_1tgt = np.random.uniform(-2, 2, N1)
    null_1_tol = {t: 0 for t in (1e-5, 1e-4, 1e-3, 1e-2)}
    null_1_hits = {t: [] for t in (1e-5, 1e-4, 1e-3, 1e-2)}
    for tgt in null_random_1tgt:
        for t in null_1_tol:
            n = fast_count(tgt, t)
            if n > 0:
                null_1_tol[t] += 1
            null_1_hits[t].append(n)

    print()
    for t in (1e-5, 1e-4, 1e-3, 1e-2):
        frac = null_1_tol[t] / N1
        mean_n = np.mean(null_1_hits[t])
        print(f"  tol {t:.0e}: {null_1_tol[t]}/{N1} ({100*frac:.2f}%) random 1-targets hit; "
              f"mean hits (across all trials) = {mean_n:.2f}")

    # ---- Null test: triple-target simultaneous matching rate ----
    print()
    print("=" * 72)
    print("Phase 3: TRIPLE-TARGET null (THE key test)")
    print("=" * 72)
    print("For each of 10^4 random 3-targets (all uniform in [-2, +2]),")
    print("does the basis match ALL three simultaneously at tol <= X?")

    N3 = 10000
    np.random.seed(137)
    null_3 = np.random.uniform(-2, 2, (N3, 3))
    null_3_tol = {t: 0 for t in (1e-5, 1e-4, 1e-3, 1e-2)}

    for triple in null_3:
        for t in null_3_tol:
            if fast_hit(triple[0], t) and fast_hit(triple[1], t) and fast_hit(triple[2], t):
                null_3_tol[t] += 1

    print()
    for t in (1e-5, 1e-4, 1e-3, 1e-2):
        frac = null_3_tol[t] / N3
        print(f"  tol {t:.0e}: {null_3_tol[t]}/{N3} ({100*frac:.2f}%) of random "
              f"triples matched ALL 3 simultaneously")

    # ---- Verdict ----
    print()
    print("=" * 72)
    print("VERDICT")
    print("=" * 72)
    triple_null_1e3 = null_3_tol[1e-3] / N3
    if triple_null_1e3 <= 0.01:
        verdict = (f"OUTCOME A (VV SURVIVES): R_null_triple(1e-3) = "
                   f"{100*triple_null_1e3:.2f}% <= 1%.  VV identifications are "
                   f"structurally distinguished from GUT-basis saturation.")
    elif triple_null_1e3 >= 0.10:
        verdict = (f"OUTCOME B (VV SATURATES): R_null_triple(1e-3) = "
                   f"{100*triple_null_1e3:.2f}% >= 10%.  VV GUT identifications "
                   f"carry no independent structural information; relegate to "
                   f"[C] appendix per Higgs-lambda / engine-PSLQ precedent.")
    else:
        verdict = (f"OUTCOME C (MODERATE): R_null_triple(1e-3) = "
                   f"{100*triple_null_1e3:.2f}% (between 1% and 10%).  Identifications "
                   f"are suggestive but not independent of basis expressivity; "
                   f"disclose with caveats.")
    print(verdict)

    # ---- Write artifact ----
    artifact = {
        "experiment_id": "COMP-P01-JJJ",
        "title": "VV GUT-basis saturation null test (Priority 9 / 37_SPEC / Round 37)",
        "date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "pre_registered_basis_sha256": basis_sha,
        "pre_registered_basis_n_atoms": len(GUT_ATOMS),
        "expressions_count": len(exprs),
        "VV_targets": VV_TARGETS,
        "vv_hit_summary": vv_hit_summary,
        "null_1target": {
            "N": N1, "range": [-2, 2],
            "at_1e-5": null_1_tol[1e-5] / N1,
            "at_1e-4": null_1_tol[1e-4] / N1,
            "at_1e-3": null_1_tol[1e-3] / N1,
            "at_1e-2": null_1_tol[1e-2] / N1,
        },
        "null_3target_simultaneous": {
            "N": N3, "range": [-2, 2],
            "at_1e-5": null_3_tol[1e-5] / N3,
            "at_1e-4": null_3_tol[1e-4] / N3,
            "at_1e-3": null_3_tol[1e-3] / N3,
            "at_1e-2": null_3_tol[1e-2] / N3,
        },
        "verdict": verdict,
    }
    block = json.dumps(artifact, sort_keys=True, indent=2, default=str)
    artifact["pre_commit_sha256"] = hashlib.sha256(block.encode()).hexdigest()

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "comp_p01_JJJ_vv_gut_saturation_null.json")
    with open(out, "w") as f:
        json.dump(artifact, f, indent=2, sort_keys=True, default=str)
    with open(out, "rb") as f:
        full_sha = hashlib.sha256(f.read()).hexdigest()

    print()
    print(f"Pre-commit SHA-256: {artifact['pre_commit_sha256'][:16]}...")
    print(f"Full-file SHA-256:  {full_sha[:16]}...")
