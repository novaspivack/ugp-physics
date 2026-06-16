"""
Direction E: Does UGP predict M_GUT from coupling unification?
If yes, can v/M_GUT be derived?

EPIC_051 Round 2, Direction E — GUT Scale Bridge
Hypothesis: M_GUT ≈ 2×10^16 GeV from gauge coupling unification.
If UGP can derive M_GUT from coupling unification, then v/M_GUT ≈ 10^{-13.7}
is a smaller hierarchy than v/M_Planck ≈ 10^{-16.7}. This 3-order reduction
might make the hierarchy expressible as a UGP-structural formula.
"""
import numpy as np
from fractions import Fraction
import json

phi = (1 + 5**0.5) / 2
pi = np.pi

# ─── Lean-certified bare couplings from P01 ────────────────────────────────
# g₂²_bare = 2329/5400 (Lean-certified zero sorry, GaugeCouplings.lean)
# g₁²_bare = 16/125    (Lean-certified from P01 table)
g1_sq_bare = Fraction(16, 125)    # = 0.12800
g2_sq_bare = Fraction(2329, 5400) # = 0.43130
# g₃ bare: from P01 canonical run. g3(M_Z) = 1.220 from SM fit.
# P01 assigns g3_bare = 1.2189 (from the SM-fit at M_2* scale after running).
# No exact-rational Lean form currently available for g3.
g3_bare = 1.2189  # from P01 canonical (not exact rational in Lean yet)

g1_bare = float(g1_sq_bare)**0.5   # ≈ 0.35777
g2_bare = float(g2_sq_bare)**0.5   # ≈ 0.65674

print("=" * 60)
print("Direction E: UGP Coupling Unification → M_GUT")
print("=" * 60)
print(f"\nBare couplings (from P01 / Lean-certified where noted):")
print(f"  g1_bare = sqrt(16/125) = {g1_bare:.6f}  [Lean-certified]")
print(f"  g2_bare = sqrt(2329/5400) = {g2_bare:.6f}  [Lean-certified]")
print(f"  g3_bare = {g3_bare:.6f}  [P01 canonical, not yet Lean rational]")

# Starting scale: UGP M₂* ≈ 34.6 GeV (the fundamental UGP mass scale, Paper 01)
M2_star = 34.6  # GeV

# ─── SM one-loop beta coefficients ─────────────────────────────────────────
# Above m_t threshold (SM, not SUSY)
# dg_i/d(ln μ) = b_i · g_i³ / (16π²)
b1 = 41.0 / 10.0   # = 4.1  (U(1)_Y with GUT normalization: b1_GUT = 41/10)
b2 = -19.0 / 6.0   # ≈ -3.167  (SU(2)_L)
b3 = -7.0           # (SU(3)_c)

def run_coupling_sq(g_sq_UV, b, mu_UV, mu):
    """Run g² from mu_UV to mu using one-loop RGE."""
    return 1.0 / (1.0 / g_sq_UV - (b / (8 * pi**2)) * np.log(mu / mu_UV))

def run_coupling(g_UV, b, mu_UV, mu):
    g_sq_result = run_coupling_sq(g_UV**2, b, mu_UV, mu)
    if g_sq_result <= 0:
        return float('nan')
    return g_sq_result**0.5

# ─── Scan over scales ───────────────────────────────────────────────────────
scales = np.logspace(np.log10(M2_star), 20, 100000)

g1_run = np.zeros(len(scales))
g2_run = np.zeros(len(scales))
g3_run = np.zeros(len(scales))

for i, mu in enumerate(scales):
    g1_run[i] = run_coupling(g1_bare, b1, M2_star, mu)
    g2_run[i] = run_coupling(g2_bare, b2, M2_star, mu)
    g3_run[i] = run_coupling(g3_bare, b3, M2_star, mu)

# Remove NaN / Landau poles
valid = np.isfinite(g1_run) & np.isfinite(g2_run) & np.isfinite(g3_run)
scales_v = scales[valid]
g1_v = g1_run[valid]
g2_v = g2_run[valid]
g3_v = g3_run[valid]

# Find closest approach
diff_12 = np.abs(g1_v - g2_v)
diff_23 = np.abs(g2_v - g3_v)
diff_13 = np.abs(g1_v - g3_v)
diff_all = diff_12 + diff_23 + diff_13

idx_12  = np.argmin(diff_12)
idx_23  = np.argmin(diff_23)
idx_all = np.argmin(diff_all)

print(f"\nSM one-loop running results:")
print(f"  g1 = g2 closest at μ = {scales_v[idx_12]:.3e} GeV  "
      f"(diff = {diff_12[idx_12]:.4f})")
print(f"  g2 = g3 closest at μ = {scales_v[idx_23]:.3e} GeV  "
      f"(diff = {diff_23[idx_23]:.4f})")
print(f"  Three-way closest at μ = {scales_v[idx_all]:.3e} GeV")
print(f"    g1 = {g1_v[idx_all]:.5f}")
print(f"    g2 = {g2_v[idx_all]:.5f}")
print(f"    g3 = {g3_v[idx_all]:.5f}")
print(f"    |g1-g2| = {diff_12[idx_all]:.5f}, |g2-g3| = {diff_23[idx_all]:.5f}")

# ─── VEV hierarchy analysis ─────────────────────────────────────────────────
M_GUT_SM = scales_v[idx_all]
v_PDG = 246.22    # GeV
M_Planck = 1.221e19  # GeV (reduced: 2.44e18; full: 1.22e19)

print(f"\nHierarchy analysis:")
print(f"  v_PDG         = {v_PDG:.3f} GeV")
print(f"  M_GUT (SM 1L) = {M_GUT_SM:.3e} GeV")
print(f"  M_Planck      = {M_Planck:.3e} GeV")
print(f"  v/M_GUT       = {v_PDG/M_GUT_SM:.4e}")
print(f"  v/M_Planck    = {v_PDG/M_Planck:.4e}")
print(f"  log10(v/M_GUT)    = {np.log10(v_PDG/M_GUT_SM):.4f}")
print(f"  log10(v/M_Planck) = {np.log10(v_PDG/M_Planck):.4f}")
print(f"  Hierarchy reduction from GUT bridge: "
      f"{np.log10(v_PDG/M_Planck) - np.log10(v_PDG/M_GUT_SM):.2f} orders")

# ─── UGP structural formula search for ln(v/M_GUT) ─────────────────────────
target_log = np.log(v_PDG / M_GUT_SM)
print(f"\nSearching for UGP formula: ln(v/M_GUT) = {target_log:.6f} nats")
print(f"  (log10 = {np.log10(v_PDG/M_GUT_SM):.6f})")

atoms = {
    'ln_phi': np.log(phi),      # ≈ 0.48121
    'ln_2':   np.log(2),        # ≈ 0.69315
    'pi':     pi,               # ≈ 3.14159
    'ln_3':   np.log(3),        # ≈ 1.09861
}
print(f"\n  Atom values: ln(φ)={atoms['ln_phi']:.5f}, ln(2)={atoms['ln_2']:.5f}, "
      f"π={atoms['pi']:.5f}, ln(3)={atoms['ln_3']:.5f}")

print(f"\nSearching via numpy vectorization (4-atom basis: ln φ, ln 2, π, ln 3):")
# Vectorized search: a·ln(φ) + b·ln(2) + c·π + d·ln(3) + e = target_log
# Use a coarse grid first; complexity limit = 8 (MDL-meaningful)
A_range = np.arange(-20, 21)
B_range = np.arange(-20, 21)
C_range = np.arange(-6, 7)
D_range = np.arange(-4, 5)

aA = atoms['ln_phi'] * A_range  # shape (41,)
bB = atoms['ln_2'] * B_range    # shape (41,)
cC = atoms['pi'] * C_range      # shape (13,)
dD = atoms['ln_3'] * D_range    # shape (9,)

# Build partial sums: (41,41) grid of a*ln_phi + b*ln_2
AB = (aA[:, None] + bB[None, :]).ravel()  # 41*41 = 1681 values

hits = []
tol = 0.001  # 0.1% tolerance (more lenient for initial scan)
for c_val in cC:
    for d_val in dD:
        AB_target = target_log - c_val - d_val  # what a*lnphi + b*ln2 must equal (before integer e)
        # Try integer offsets e
        for e in range(-40, 41):
            needed = AB_target - e
            # Find closest AB values
            diffs = np.abs(AB - needed)
            close_idx = np.where(diffs / (abs(target_log) + 1e-10) < tol)[0]
            for idx in close_idx:
                a = A_range[idx // len(B_range)]
                b = B_range[idx % len(B_range)]
                c_int = round(c_val / atoms['pi'])
                d_int = round(d_val / atoms['ln_3'])
                val = a*atoms['ln_phi'] + b*atoms['ln_2'] + c_int*atoms['pi'] + d_int*atoms['ln_3'] + e
                err_frac = abs(val - target_log) / abs(target_log)
                if err_frac < tol:
                    cplx = abs(a) + abs(b) + abs(c_int) + abs(d_int) + abs(e)
                    hits.append((cplx, a, b, c_int, d_int, e, val, err_frac))

# Deduplicate
seen = set()
unique_hits = []
for h in hits:
    key = (h[1], h[2], h[3], h[4], h[5])
    if key not in seen:
        seen.add(key)
        unique_hits.append(h)
unique_hits.sort()

if unique_hits:
    print(f"\n  Top formula hits (within 0.1% of target, sorted by complexity):")
    for h in unique_hits[:8]:
        cplx, a, b, c, d, e, val, err = h
        print(f"    {a}·ln(φ)+{b}·ln(2)+{c}·π+{d}·ln(3)+{e} = {val:.6f}  "
              f"(err={err*100:.3f}%, complexity={cplx})")
    best_cplx = unique_hits[0][0]
    if best_cplx <= 8:
        print(f"\n  ✓ LOW-COMPLEXITY FORMULA FOUND (complexity={best_cplx})")
    else:
        print(f"\n  ✗ All hits have complexity ≥ {best_cplx} — not MDL-competitive")
else:
    print(f"  ✗ No formula found within 0.1% tolerance in 4-atom basis")

hits = unique_hits  # for downstream use

# ─── GUT scale vs UGP structural numbers ───────────────────────────────────
print(f"\nDoes M_GUT_SM express cleanly in UGP units?")
M2_star_val = 34.6   # GeV
M_Z = 91.2           # GeV
m_W = 80.379         # GeV
for label, ref in [("M2*", M2_star_val), ("M_Z", M_Z), ("m_W", m_W), ("M_P", M_Planck)]:
    ratio = M_GUT_SM / ref
    print(f"  M_GUT / {label} = {ratio:.4e}  (log10 = {np.log10(ratio):.4f})")

# ─── Null discipline (fast version) ─────────────────────────────────────────
print(f"\nNull discipline: 10 random targets in same log10 range")
np.random.seed(42)
log10_target = np.log10(v_PDG / M_GUT_SM)
null_counts = []
for _ in range(10):
    rand_log = np.random.uniform(log10_target - 0.5, log10_target + 0.5)
    rand_nat = rand_log * np.log(10)
    count = 0
    for c_val in cC:
        for d_val in dD:
            for e in range(-40, 41):
                needed = rand_nat - c_val - d_val - e
                diffs = np.abs(AB - needed)
                close_idx = np.where(diffs / (abs(rand_nat) + 1e-10) < tol)[0]
                count += len(close_idx)
    null_counts.append(count)
null_median = np.median(null_counts)
n_real = len(unique_hits)
print(f"  Real hits: {n_real}, Null median: {null_median:.0f}")
if n_real == 0:
    print(f"  Verdict: NULL — no formula found")
elif n_real <= null_median * 1.5:
    print(f"  Verdict: VOLUME-DOMINATED")
else:
    print(f"  Verdict: SIGNIFICANT")

# ─── SM unification assessment ─────────────────────────────────────────────
print(f"\n{'='*60}")
print("ASSESSMENT")
print(f"{'='*60}")
three_way_miss = diff_all[idx_all]
if three_way_miss > 0.1:
    print(f"NEGATIVE: SM gauge couplings do NOT unify at one loop.")
    print(f"  Three-way spread at best-fit scale: Δ = {three_way_miss:.4f}")
    print(f"  (SUSY GUTs give unification; SM does not)")
    print(f"  UGP bare couplings inherit the SM non-unification pattern.")
    print(f"  There is no M_GUT derivable from UGP at SM one-loop.")
else:
    print(f"POSITIVE: Near-unification found at μ = {M_GUT_SM:.3e} GeV")

# ─── Save results ─────────────────────────────────────────────────────────
results = {
    "direction": "E",
    "title": "GUT Scale Bridge",
    "g1_bare": g1_bare,
    "g2_bare": g2_bare,
    "g3_bare": g3_bare,
    "M2_star_GeV": M2_star,
    "SM_beta_b1": b1, "SM_beta_b2": b2, "SM_beta_b3": b3,
    "scale_g1_eq_g2_GeV": float(scales_v[idx_12]),
    "scale_g2_eq_g3_GeV": float(scales_v[idx_23]),
    "three_way_scale_GeV": float(M_GUT_SM),
    "three_way_g1": float(g1_v[idx_all]),
    "three_way_g2": float(g2_v[idx_all]),
    "three_way_g3": float(g3_v[idx_all]),
    "three_way_spread": float(diff_all[idx_all]),
    "log10_v_over_M_GUT": float(np.log10(v_PDG / M_GUT_SM)),
    "log10_v_over_M_Planck": float(np.log10(v_PDG / M_Planck)),
    "formula_hits": len(hits),
    "null_median_hits": float(null_median),
    "verdict": (
        "NEGATIVE: SM gauge couplings do not unify at one loop; "
        "UGP bare couplings inherit SM non-unification; "
        "no M_GUT derivable; "
        "formula search volume-dominated or null"
        if three_way_miss > 0.1 else
        "CONDITIONAL: near-unification found, see three_way_scale_GeV"
    ),
}
with open("direction_E_gut_scale.json", "w") as f:
    json.dump(results, f, indent=2)
print("\nSaved direction_E_gut_scale.json")
