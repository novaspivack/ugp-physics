"""
COMP-P01-LLL: VV coefficient derivation via discrete-flavor-symmetry basis
              (Priority 14 / Round 39; Path (a) follow-up to SC-JJJ and
              SC-KKK.)

GOAL: Test whether the VV coefficients (13/9, -7/6, -5/14) admit a
      structural interpretation via non-Abelian discrete flavor groups
      commonly used in BSM flavor physics (A_4, S_4, T', A_5, Δ(27),
      Δ(54), Σ(168), etc.).  Apply the same saturation null discipline
      as SC-JJJ to this discrete-flavor basis.

PROTOCOL:
1. Pre-register a basis of discrete-flavor-theoretic atoms:
   - Orders of small non-Abelian discrete groups (Ishimori et al.)
   - Dimensions of their irreducible representations
   - Indices of common subgroup chains
   - Cyclotomic roots of small orders
   - Small rationals
2. Commit SHA-256 of basis BEFORE scanning VV targets.
3. Scan basis at DL ≤ 3 for expressions matching each VV target.
4. Null test: 10^4 random 3-target triples in [-2, +2]; count fraction
   where all 3 match simultaneously at 1e-3.

OUTCOMES:
- Outcome A (WIN): discrete-flavor basis is NOT saturating AND one specific
  structural combination reproduces all three VV targets cleanly.  Would
  upgrade VV back to [T] with a flavor-symmetry interpretation.
- Outcome B (MAP): basis saturates OR no single structural combination
  stands out.  VV coefficients remain [C]; adds SC-LLL as third
  independent null-discipline artifact.
"""

import math, json, hashlib, datetime, os, itertools
import numpy as np

# =====================================================================
# PRE-REGISTERED DISCRETE-FLAVOR BASIS
# =====================================================================
# Atoms chosen from the Ishimori et al. (2010) catalog of small
# non-Abelian finite subgroups of SU(3) commonly used in BSM flavor
# models, plus small Abelian cyclotomics and rationals.  CRITICAL:
# committed BEFORE any VV-target scan.
# =====================================================================

DISCRETE_ATOMS = {
    # ---- Orders of small non-Abelian discrete groups ----
    # (standard BSM flavor-physics toolkit)
    'order_S3': 6, 'order_A4': 12, 'order_S4': 24, 'order_Tprime': 24,
    'order_A5': 60, 'order_S5': 120,
    'order_D4': 8, 'order_D5': 10, 'order_D6': 12, 'order_D7': 14,
    'order_D8': 16, 'order_D9': 18, 'order_D10': 20, 'order_D12': 24,
    'order_Q8': 8,   # quaternion group
    'order_Delta27': 27, 'order_Delta54': 54, 'order_Delta48': 48,
    'order_Delta75': 75, 'order_Delta96': 96, 'order_Delta108': 108,
    'order_Sigma36': 36, 'order_Sigma72': 72,
    'order_Sigma216': 216, 'order_Sigma168': 168, 'order_Sigma60': 60,

    # ---- Irrep dimensions of A_4 ----
    'A4_1': 1, 'A4_1prime': 1, 'A4_1dblprime': 1, 'A4_3': 3,

    # ---- Irrep dimensions of S_4 ----
    'S4_1': 1, 'S4_1prime': 1, 'S4_2': 2, 'S4_3': 3, 'S4_3prime': 3,

    # ---- Irrep dimensions of T' (binary tetrahedral) ----
    'Tp_1': 1, 'Tp_2': 2, 'Tp_2prime': 2, 'Tp_3': 3,

    # ---- Irrep dimensions of A_5 (icosahedral) ----
    'A5_1': 1, 'A5_3': 3, 'A5_3prime': 3, 'A5_4': 4, 'A5_5': 5,

    # ---- Irrep dimensions of Δ(27), Δ(54), Σ(168) ----
    'Delta27_3': 3, 'Delta27_1_11': 1, 'Delta27_3bar': 3,
    'Delta54_3': 3, 'Delta54_6': 6,
    'Sigma168_3': 3, 'Sigma168_6': 6, 'Sigma168_7': 7, 'Sigma168_8': 8,
    'Sigma216_3': 3, 'Sigma216_6': 6, 'Sigma216_8': 8,
    'Sigma72_3': 3, 'Sigma72_8': 8,
    'Sigma36_3': 3, 'Sigma36_4': 4,

    # ---- D_n dihedral group irrep dimensions ----
    'Dn_1': 1, 'Dn_1prime': 1, 'Dn_2': 2,

    # ---- Branching indices and common flavor-model subgroup indices ----
    'idx_S4_over_A4': 2,     # |S_4|/|A_4|
    'idx_S4_over_S3': 4,     # |S_4|/|S_3|
    'idx_A5_over_A4': 5,     # |A_5|/|A_4|
    'idx_Tprime_over_A4': 2, # |T'|/|A_4|

    # ---- Triangle / pentagon / heptagon invariants (flavor-texture literature) ----
    'n_tri_sides': 3, 'n_sq_sides': 4, 'n_pent_sides': 5,
    'n_hex_sides': 6, 'n_hep_sides': 7,

    # ---- Small cyclotomic-related atoms ----
    'cos_pi_3': math.cos(math.pi/3),       # 1/2
    'cos_pi_5': math.cos(math.pi/5),       # (1+√5)/4
    'cos_pi_7': math.cos(math.pi/7),
    'cos_2pi_5': math.cos(2*math.pi/5),
    'cos_2pi_7': math.cos(2*math.pi/7),

    # ---- Small rationals and basic integers ----
    '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8,
    '9': 9, '10': 10, '11': 11, '12': 12, '13': 13, '14': 14,
    'neg_1': -1, 'half': 1/2, 'third': 1/3, 'quarter': 1/4,
    'sixth': 1/6, 'eighth': 1/8,
}

basis_def_str = json.dumps({k: v for k, v in sorted(DISCRETE_ATOMS.items())},
                            indent=2, sort_keys=True)
basis_sha = hashlib.sha256(basis_def_str.encode('utf-8')).hexdigest()

VV_TARGETS = {
    'alpha_VV': 13/9,
    'beta_VV':  -7/6,
    'gamma_VV': -5/14,
}

# =====================================================================
# Expression building (same as SC-JJJ but discrete-flavor atoms)
# =====================================================================
def build_expressions(atoms, max_dl=3):
    exprs = dict(atoms)
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
# Execute
# =====================================================================
if __name__ == "__main__":
    print("=" * 72)
    print("COMP-P01-LLL: VV discrete-flavor-symmetry basis saturation null")
    print("Priority 14 / Round 39; Path (a) follow-up to SC-JJJ, SC-KKK")
    print("=" * 72)
    print()
    print(f"Pre-registered discrete-flavor basis: {len(DISCRETE_ATOMS)} atoms")
    print(f"Basis definition SHA-256: {basis_sha}")
    print(f"(Committed BEFORE any target scan; no post-hoc changes allowed.)")
    print()

    print("Building DL <= 3 expressions...")
    exprs = build_expressions(DISCRETE_ATOMS, max_dl=3)
    print(f"Total expressions: {len(exprs)}")

    exprs_values = np.array(list(exprs.values()))
    exprs_values.sort()

    def fast_count(tgt, tol):
        abs_tol = tol * max(abs(tgt), 1e-20)
        lo = np.searchsorted(exprs_values, tgt - abs_tol)
        hi = np.searchsorted(exprs_values, tgt + abs_tol)
        return hi - lo

    def fast_hit(tgt, tol):
        return fast_count(tgt, tol) > 0

    def scan_target_exact(target, exprs, tol):
        hits = []
        for name, val in exprs.items():
            if not math.isfinite(val):
                continue
            rel = abs(val - target) / max(abs(target), 1e-20)
            if rel < tol:
                hits.append((name, val, rel))
        hits.sort(key=lambda x: x[2])
        return hits

    # ---- Scan VV targets ----
    print()
    print("=" * 72)
    print("Phase 1: Scan VV coefficient targets")
    print("=" * 72)
    vv_hit_summary = {}
    for name, tgt in VV_TARGETS.items():
        hits_1e4 = scan_target_exact(tgt, exprs, 1e-4)
        n_1e5 = fast_count(tgt, 1e-5)
        n_1e4 = fast_count(tgt, 1e-4)
        n_1e3 = fast_count(tgt, 1e-3)
        n_1e2 = fast_count(tgt, 1e-2)
        vv_hit_summary[name] = {
            'target': tgt,
            'n_at_1e-5': n_1e5, 'n_at_1e-4': n_1e4,
            'n_at_1e-3': n_1e3, 'n_at_1e-2': n_1e2,
            'top_5_at_1e-4': [(n, float(v), float(r)) for n, v, r in hits_1e4[:5]],
        }
        print(f"\n{name} = {tgt:+.6f}:")
        print(f"  Hits at 1e-5: {n_1e5}   1e-4: {n_1e4}   1e-3: {n_1e3}   1e-2: {n_1e2}")
        for n, v, r in hits_1e4[:5]:
            print(f"    {n[:60]:<60}  ->  {v:+.6f}  (rel {r:.2e})")

    # ---- Null test: single-target ----
    print()
    print("=" * 72)
    print("Phase 2: Single-target null on [-2, +2]")
    print("=" * 72)
    np.random.seed(39)
    N1 = 10000
    null_random_1tgt = np.random.uniform(-2, 2, N1)
    null_1_tol = {t: 0 for t in (1e-5, 1e-4, 1e-3, 1e-2)}
    for tgt in null_random_1tgt:
        for t in null_1_tol:
            if fast_count(tgt, t) > 0:
                null_1_tol[t] += 1

    print()
    for t in (1e-5, 1e-4, 1e-3, 1e-2):
        frac = null_1_tol[t] / N1
        print(f"  tol {t:.0e}: {null_1_tol[t]}/{N1} ({100*frac:.2f}%) random 1-targets hit")

    # ---- Null test: triple-target ----
    print()
    print("=" * 72)
    print("Phase 3: TRIPLE-TARGET null")
    print("=" * 72)
    N3 = 10000
    np.random.seed(139)
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
              f"triples matched ALL 3")

    # ---- Verdict ----
    print()
    print("=" * 72)
    print("VERDICT")
    print("=" * 72)
    triple_null_1e3 = null_3_tol[1e-3] / N3
    triple_null_1e4 = null_3_tol[1e-4] / N3
    # Are the VV target hit counts distinguished from null?
    vv_all_at_1e5 = all(vv_hit_summary[k]['n_at_1e-5'] > 0 for k in vv_hit_summary)
    vv_all_at_1e4 = all(vv_hit_summary[k]['n_at_1e-4'] > 0 for k in vv_hit_summary)
    vv_all_at_1e3 = all(vv_hit_summary[k]['n_at_1e-3'] > 0 for k in vv_hit_summary)

    if triple_null_1e3 <= 0.01 and vv_all_at_1e3:
        verdict = (f"OUTCOME A (POTENTIAL WIN): discrete-flavor basis NOT saturating at 1e-3 ({100*triple_null_1e3:.2f}%) "
                   f"AND all three VV targets matched.  Investigate specific structural matches.")
    elif triple_null_1e3 >= 0.10:
        verdict = (f"OUTCOME B (MAP): discrete-flavor basis SATURATES at 1e-3 ({100*triple_null_1e3:.2f}% random triples matched).  "
                   f"VV identifications via discrete flavor groups are not distinguished from basis expressivity.  "
                   f"[C] classification further supported; SC-LLL adds third independent null strike.")
    elif not vv_all_at_1e3:
        verdict = (f"OUTCOME C (MISS): discrete-flavor basis not saturating at 1e-3 ({100*triple_null_1e3:.2f}%) "
                   f"but one or more VV targets MISS in this basis.  No structural interpretation available via discrete flavor.")
    else:
        verdict = (f"OUTCOME D (MODERATE): triple null at 1e-3 = {100*triple_null_1e3:.2f}% (between 1% and 10%); "
                   f"discrete-flavor basis is moderately sparse; VV matches are suggestive but not clean.")

    print(verdict)

    # ---- Write artifact ----
    artifact = {
        "experiment_id": "COMP-P01-LLL",
        "title": "VV discrete-flavor-symmetry basis saturation null (Priority 14, Round 39)",
        "date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "pre_registered_basis_sha256": basis_sha,
        "pre_registered_basis_n_atoms": len(DISCRETE_ATOMS),
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
                       "comp_p01_LLL_vv_discrete_flavor_null.json")
    with open(out, "w") as f:
        json.dump(artifact, f, indent=2, sort_keys=True, default=str)
    with open(out, "rb") as f:
        full_sha = hashlib.sha256(f.read()).hexdigest()

    print()
    print(f"Pre-commit SHA-256: {artifact['pre_commit_sha256'][:16]}...")
    print(f"Full-file SHA-256:  {full_sha[:16]}...")
