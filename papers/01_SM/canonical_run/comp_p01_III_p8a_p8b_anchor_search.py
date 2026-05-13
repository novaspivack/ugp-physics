"""
COMP-P01-III: P8a + P8b anchor search — structural scan for m_μ and quark
              absolute-scale anchors using the R21-34 extended atom library.
              (Round 35, 04_SPEC OP(i)-B + OP(i)-C.)

PRIOR WORK (NEGATIVE):
- SC-K: m_e ≈ δ·b₁ keV at +2.05 ppm (only structural lepton hit found).
- SC-K: m_μ, m_τ NOT structurally accessible at DL ≤ 2 precision.
- SC-BB: 16 structural R_g hypotheses + 32-atom brute force, all fail at >10%.
- 070_NOTE: 5 Round-3 approaches failed (GTE triples, Fibonacci, Möbius,
            entropy, α-coupled).

WHAT IS NEW (R21-34):
- TT-derived atoms: α = π/6, β = π/8, 2^g cascade
- Cyclotomic-12 atoms from R33: (2+√3) = 4cos²(π/12), cos(π/12)
- FN flavon VEVs from R22: ε_1 = e^(-π/3), ε_2 = e^(-π/8)
- SO(10) doubled-charge pattern (1, 2, 4) from R21

APPROACH:
- Build a ~200-atom extended UGP library at DL ≤ 3
- Scan for m_μ, m_μ/m_e, m_u, m_d, m_u/m_e, m_d/m_e at 4 precision levels
  (10⁻⁶, 10⁻⁴, 10⁻³, 10⁻²)
- Null test: 1000-permutation null across 8 R_g values, does scan find
  similar density of "hits" on random targets?

SUCCESS GATES:
- ≤ 1% hit with null fraction < 5%: candidate for structural anchor
- ≤ 10⁻³ hit with null fraction < 1%: strong candidate
- ≤ 10⁻⁴ hit with null fraction < 0.1%: effective closure
"""

import math, json, hashlib, datetime, os, itertools
import numpy as np

# =====================================================================
# PDG targets (R_g = m_particle / m_e for the non-electron 8 fermions)
# Using 2022 PDG central values.
# =====================================================================
MASSES = {
    'e':  0.0005109989461,
    'mu': 0.1056583755,
    'tau': 1.77686,
    'u':  2.16e-3,        # 2.16 +2.00 -0.73 at 2 GeV (PDG 2022)
    'd':  4.67e-3,        # 4.67 +1.48 -0.67 at 2 GeV
    's':  93.4e-3,        # 93.4 +8.6 -3.4
    'c':  1.27,           # 1.27 +0.02 -0.02
    'b':  4.18,           # 4.18 +0.03 -0.02
    't':  172.76,         # 172.76 ± 0.30
}

# Targets: log(R_g) where R_g = m_g / m_e
TARGETS = {f'log_R_{p}': math.log(MASSES[p]/MASSES['e']) for p in MASSES if p != 'e'}
# Also some direct pairwise ratios
TARGETS['log_m_mu_e'] = math.log(MASSES['mu']/MASSES['e'])
TARGETS['log_m_tau_mu'] = math.log(MASSES['tau']/MASSES['mu'])
TARGETS['log_m_u_e'] = math.log(MASSES['u']/MASSES['e'])
TARGETS['log_m_d_u'] = math.log(MASSES['d']/MASSES['u'])
TARGETS['log_m_s_d'] = math.log(MASSES['s']/MASSES['d'])

print(f"PDG log-ratio targets (absolute values):")
for k, v in TARGETS.items():
    print(f"  {k:20s} = {v:.6f}")

# =====================================================================
# Extended UGP atom library (post-R34)
# =====================================================================
PI = math.pi
E  = math.e
PHI = (1 + math.sqrt(5))/2
SQRT2 = math.sqrt(2)
SQRT3 = math.sqrt(3)

# Basic & transcendental atoms
BASIC = {
    '1': 1, '2': 2, '3': 3, '5': 5, '6': 6, '7': 7, '8': 8,
    '9': 9, '10': 10, '12': 12, '13': 13, '14': 14, '16': 16,
    'pi': PI, 'e': E, 'phi': PHI, 'phi2': PHI**2,
    'sqrt2': SQRT2, 'sqrt3': SQRT3,
    '1/2': 0.5, '1/3': 1/3, '1/6': 1/6, '1/8': 0.125,
}

# Cyclotomic-12 atoms (from R33 Koide)
CYCLOTOMIC = {
    'pi/12': PI/12, 'pi/6': PI/6, 'pi/4': PI/4, 'pi/3': PI/3,
    '2pi/3': 2*PI/3, 'pi/8': PI/8,
    'cos_pi/12': math.cos(PI/12), 'sin_pi/12': math.sin(PI/12),
    '2+sqrt3': 2+SQRT3, '1+sqrt3': 1+SQRT3,
    '4cos2_pi12': 4*math.cos(PI/12)**2,  # = 2+√3
}

# FN flavon VEVs and derived quantities (from R21-22)
FN_ATOMS = {
    'eps1': math.exp(-PI/3), 'eps2': math.exp(-PI/8),
    'log_eps1': -PI/3, 'log_eps2': -PI/8,
    'exp_pi': math.exp(PI), 'exp_2pi': math.exp(2*PI),
    'exp_pi/3': math.exp(PI/3), 'exp_pi/8': math.exp(PI/8),
    'exp_pi/6': math.exp(PI/6), 'exp_pi/4': math.exp(PI/4),
    'exp_2pi/3': math.exp(2*PI/3), 'exp_5pi/3': math.exp(5*PI/3),
    'exp_pi/2': math.exp(PI/2), 'exp_4pi/3': math.exp(4*PI/3),
}

# Lean-certified rational constants (gauge couplings, VV, etc.)
LEAN_ATOMS = {
    '16/125': 16/125, '2329/5400': 2329/5400,
    '13/9': 13/9, '7/6': 7/6, '5/14': 5/14,
    'delta': 0.0233, 'b1': 21.89,   # SC-K electron anchor
    'delta_b1': 0.0233 * 21.89,     # ~ 0.5100 keV
}

ALL_ATOMS = {}
ALL_ATOMS.update(BASIC)
ALL_ATOMS.update(CYCLOTOMIC)
ALL_ATOMS.update(FN_ATOMS)
ALL_ATOMS.update(LEAN_ATOMS)

print(f"\nTotal atoms in library: {len(ALL_ATOMS)}")

# =====================================================================
# Compose DL-1, DL-2, DL-3 expressions
# =====================================================================
def build_expressions(max_dl=3):
    """Generate a dict of {expr_str: value} with description length <= max_dl."""
    exprs = dict(ALL_ATOMS)  # DL=1

    if max_dl >= 2:
        # DL=2: binary ops between DL=1 atoms
        dl1 = list(ALL_ATOMS.items())
        for (n1, v1), (n2, v2) in itertools.combinations_with_replacement(dl1, 2):
            for op, sym in [(lambda a,b: a+b, '+'), (lambda a,b: a-b, '-'),
                           (lambda a,b: a*b, '*'), (lambda a,b: a/b if abs(b)>1e-20 else None, '/')]:
                try:
                    val = op(v1, v2)
                    if val is None or abs(val) > 1e20 or not math.isfinite(val):
                        continue
                    key = f"({n1}{sym}{n2})"
                    if key not in exprs and abs(val) < 1e15:
                        exprs[key] = val
                    if sym in '-/':
                        val2 = op(v2, v1)
                        if val2 is not None and math.isfinite(val2) and abs(val2) < 1e15:
                            exprs[f"({n2}{sym}{n1})"] = val2
                except Exception:
                    pass

    if max_dl >= 3:
        # DL=3: combine DL=2 with DL=1 (limited set to keep size manageable)
        dl2_keys = [k for k in exprs if k not in ALL_ATOMS][:500]   # top 500
        dl1_keys = list(ALL_ATOMS.keys())
        for k2 in dl2_keys:
            v2 = exprs[k2]
            for k1 in dl1_keys:
                v1 = exprs[k1]
                for op, sym in [(lambda a,b: a+b, '+'), (lambda a,b: a*b, '*')]:
                    try:
                        val = op(v2, v1)
                        if abs(val) < 1e15 and math.isfinite(val):
                            key = f"({k2}{sym}{k1})"
                            if key not in exprs:
                                exprs[key] = val
                    except Exception:
                        pass
    return exprs

print("\nBuilding expression library (DL ≤ 3, binary ops +, -, *, /)...")
exprs = build_expressions(max_dl=3)
print(f"Total expressions: {len(exprs)}")

# =====================================================================
# Scan for hits on each target
# =====================================================================
def scan_target(target_val, exprs, tol_ladder=[1e-6, 1e-4, 1e-3, 1e-2]):
    hits = {tol: [] for tol in tol_ladder}
    for name, val in exprs.items():
        if not math.isfinite(val):
            continue
        err = abs(val - target_val)
        rel = err / max(abs(target_val), 1e-20)
        for tol in tol_ladder:
            if rel < tol:
                hits[tol].append((name, val, rel))
    for tol in tol_ladder:
        hits[tol].sort(key=lambda x: x[2])
    return hits

print()
print("=" * 72)
print("SCAN RESULTS")
print("=" * 72)

hit_summary = {}
for tgt_name, tgt_val in TARGETS.items():
    hits = scan_target(tgt_val, exprs)
    tight = hits[1e-4]
    moderate = hits[1e-3]
    loose = hits[1e-2]
    hit_summary[tgt_name] = {
        'target_value': tgt_val,
        'n_hits_1e-6': len(hits[1e-6]),
        'n_hits_1e-4': len(tight),
        'n_hits_1e-3': len(moderate),
        'n_hits_1e-2': len(loose),
        'best_5_hits': [(n, float(v), float(r)) for n, v, r in hits[1e-2][:5]],
    }
    status = "MISS" if len(loose) == 0 else ("LOOSE" if len(moderate) == 0 else ("TIGHT" if len(tight) == 0 else "PRECISION"))
    print(f"\n{tgt_name} = {tgt_val:.6f}  [{status}]")
    print(f"  Hits at tol: 1e-6:{len(hits[1e-6]):>4}  1e-4:{len(tight):>4}  1e-3:{len(moderate):>4}  1e-2:{len(loose):>4}")
    for name, val, rel in hits[1e-2][:3]:
        print(f"    {name}  →  {val:.6f}  (rel. err {rel:.2e})")

# =====================================================================
# Null discipline: scan random target values in the same range
# =====================================================================
print()
print("=" * 72)
print("NULL DISCIPLINE")
print("=" * 72)
print("Scanning 200 random log-ratio targets in [-8, +12] for same library:")

np.random.seed(42)
N_null = 200
null_hit_counts = {1e-6: [], 1e-4: [], 1e-3: [], 1e-2: []}
for _ in range(N_null):
    tgt = np.random.uniform(-8, 12)
    hits = scan_target(tgt, exprs)
    for tol in null_hit_counts:
        null_hit_counts[tol].append(len(hits[tol]))

for tol in [1e-6, 1e-4, 1e-3, 1e-2]:
    counts = null_hit_counts[tol]
    print(f"  tol {tol:.0e}: null median = {np.median(counts):.1f},  mean = {np.mean(counts):.2f},  "
          f"random-target hit rate = {100*np.mean([c > 0 for c in counts]):.1f}%")

# =====================================================================
# Concluding verdict
# =====================================================================
print()
print("=" * 72)
print("VERDICT")
print("=" * 72)

# Classification
strong_hits = [k for k, v in hit_summary.items() if v['n_hits_1e-4'] > 0]
moderate_hits = [k for k, v in hit_summary.items() if v['n_hits_1e-3'] > 0]
mean_null_hits_1e3 = np.mean(null_hit_counts[1e-3])

verdict_str = (
    f"Strong hits (< 1e-4 precision): {len(strong_hits)}/{len(TARGETS)} → {strong_hits}\n"
    f"Moderate hits (< 1e-3 precision): {len(moderate_hits)}/{len(TARGETS)} → {moderate_hits}\n"
    f"Null mean hits at 1e-3: {mean_null_hits_1e3:.2f} "
    f"(a structural signal requires observed >> null)\n"
)
print(verdict_str)

# =====================================================================
# Artifact
# =====================================================================
prediction = {
    "experiment_id": "COMP-P01-III",
    "title": "P8a + P8b structural anchor search (m_μ and quark absolute scales)",
    "date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "library_size": len(exprs),
    "targets": hit_summary,
    "null_test": {
        "N_random_targets": N_null,
        "mean_hits_at_1e-2": float(np.mean(null_hit_counts[1e-2])),
        "mean_hits_at_1e-3": float(np.mean(null_hit_counts[1e-3])),
        "mean_hits_at_1e-4": float(np.mean(null_hit_counts[1e-4])),
        "random_target_hit_rate_1e-3": float(np.mean([c > 0 for c in null_hit_counts[1e-3]])),
    },
    "verdict": verdict_str,
}
block = json.dumps(prediction, sort_keys=True, indent=2, default=str)
prediction["pre_commit_sha256"] = hashlib.sha256(block.encode("utf-8")).hexdigest()
out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "comp_p01_III_p8a_p8b_anchor_search.json")
with open(out, "w") as f:
    json.dump(prediction, f, indent=2, sort_keys=True, default=str)
with open(out, "rb") as f:
    full_sha = hashlib.sha256(f.read()).hexdigest()
print()
print(f"Pre-commit SHA-256: {prediction['pre_commit_sha256'][:16]}...")
print(f"Full-file SHA-256:  {full_sha[:16]}...")
