"""
Direction H Round 3: PSC Self-Referential EW Closure Test
=========================================================

Test: Does L_EW(μ) = log₂(D_SU2(μ)²/(3g₂(μ)²)) = π/ln2 at μ = v ≈ 246 GeV?

The PSC formula:  v² = (ln2/π) × L_EW(v) × M_ref²
If L_EW(v) = π/ln2 exactly:  v² = (ln2/π)(π/ln2) M_ref² = M_ref²
  → v = M_ref   (self-referential PSC fixed point)

Key structural definitions (from gauge master formula, Round 2):
  g₂² = L_SU2 × D_SU2 / 5^γ_SU2  with L_SU2=2, γ_SU2=2
  →  D_SU2 = g₂² × 25/2  =  2329/432 ≈ 5.391

Running ansatz: D_SU2(μ) = g₂(μ)² × 25/2 (same functional relation, running g₂)
  L_EW(μ) = log₂(D_SU2(μ)²/(3g₂(μ)²))
           = log₂((g₂(μ)² × 25/2)² / (3g₂(μ)²))
           = log₂(g₂(μ)² × 625/12)
           = 2 log₂(g₂(μ)) + log₂(625/12)

L_EW depends on μ only through g₂(μ).  Since g₂ runs asymptotically free
(decreases as μ increases), L_EW DECREASES as μ increases.

Tested:
  (A) One-loop SM running     (b₂ = −19/6, M₂*=37.4 GeV)
  (B) Two-loop SM running     (with m_t threshold, M₂*=37.4 GeV)
  (C) Two-loop self-consistent (M₂*=34.56 GeV from ZZ SC-CC solve)
  (D) Closure scale search     (find μ where L_EW = π/ln2 exactly)

EPIC_051 Direction H Round 3
Date: 2026-05-15
"""

import numpy as np
from fractions import Fraction
from scipy.integrate import solve_ivp
from scipy.optimize import brentq
import json

phi  = (1 + 5**0.5) / 2
pi   = np.pi
ln2  = np.log(2)

# ---------------------------------------------------------------------------
# BARE COUPLINGS (Lean-certified)
# ---------------------------------------------------------------------------
g1_sq_bare = float(Fraction(16, 125))           # U(1):   0.128000
g2_sq_bare = float(Fraction(2329, 5400))        # SU(2):  0.431296...
g3_sq_bare = float(Fraction(41075281, 27648000)) # SU(3)
g2_bare    = g2_sq_bare**0.5

# D_SU2 from gauge master formula: g₂² = 2 × D_SU2 / 5²
# → D_SU2 = g₂² × 25/2
D_SU2_frac = Fraction(2329, 432)         # = 2329/5400 × 25/2 = 2329/432
D_SU2_bare = float(D_SU2_frac)
D1_bare    = float(Fraction(16))         # U(1) invariant

# Log₂(625/12) — the scale-independent part of L_EW(μ)
LOG2_625_OVER_12 = np.log2(625.0 / 12.0)   # = log₂((25/2)² / 3) = log₂(625/12)

# Reference scales
M2_star_1loop = 37.4              # GeV  (1-loop SC-CC inverse solve)
M2_star_2loop = 34.561907         # GeV  (2-loop SC-CC self-consistent, from ZZ)
V_PDG         = 246.22            # GeV  (EW VEV from G_F)
MT            = 172.76            # GeV  (top threshold)

pi_over_ln2 = pi / ln2

# ---------------------------------------------------------------------------
# HELPER: L_EW from g₂(μ)
# ---------------------------------------------------------------------------
def L_EW_from_g2(g2):
    """L_EW(μ) = log₂(g₂(μ)² × 625/12)"""
    return 2.0 * np.log2(abs(g2)) + LOG2_625_OVER_12

# ---------------------------------------------------------------------------
# SECTION 0: Verify Round 2 bare values
# ---------------------------------------------------------------------------
print("=" * 72)
print("DIRECTION H ROUND 3: PSC SELF-REFERENTIAL EW CLOSURE TEST")
print("=" * 72)

L_model_check = np.log2(D1_bare**2 / (3 * g1_sq_bare))
L_EW_bare     = np.log2(D_SU2_bare**2 / (3 * g2_sq_bare))
gap_bare_pct  = (pi_over_ln2 - L_EW_bare) / pi_over_ln2 * 100

print(f"\nBare-scale values (μ = M₂* ≈ 37.4 GeV):")
print(f"  D_SU2_bare  = {D_SU2_frac} = {D_SU2_bare:.8f}")
print(f"  g₂_bare     = {g2_bare:.8f}")
print(f"  D1_bare     = {D1_bare:.0f}")
print(f"  L_model     = {L_model_check:.6f} bits  (should be log₂(2000/3) ≈ 9.3808)")
print(f"  L_EW_bare   = {L_EW_bare:.8f} bits")
print(f"  π/ln2       = {pi_over_ln2:.8f} bits")
print(f"  Gap_bare    = {gap_bare_pct:+.4f}%   (L_EW is {abs(gap_bare_pct):.4f}% below π/ln2 at bare)")

# ---------------------------------------------------------------------------
# SECTION 1: g₂ needed for exact closure
# ---------------------------------------------------------------------------
print("\n--- SECTION 1: Required g₂ for L_EW = π/ln2 ---")

# L_EW = π/ln2  ↔  2log₂(g₂) = π/ln2 − log₂(625/12)
log2_g2_needed = (pi_over_ln2 - LOG2_625_OVER_12) / 2.0
g2_needed = 2.0**log2_g2_needed
g2_needed_sq = g2_needed**2

print(f"  Target: L_EW = π/ln2 = {pi_over_ln2:.8f} bits")
print(f"  log₂(625/12) = {LOG2_625_OVER_12:.8f} bits")
print(f"  2log₂(g₂) needed = {2*log2_g2_needed:.8f}")
print(f"  g₂ needed  = {g2_needed:.8f}")
print(f"  g₂_bare    = {g2_bare:.8f}")
print(f"  g₂_needed > g₂_bare: {g2_needed > g2_bare}  (closure requires running DOWN in μ)")

# ---------------------------------------------------------------------------
# SECTION 2: One-loop running
# ---------------------------------------------------------------------------
print("\n--- SECTION 2: ONE-LOOP RUNNING ---")

b2_1loop = -19.0 / 6.0

def g2_1loop(mu, M2_star=M2_star_1loop, g2_UV=g2_bare):
    """Analytic one-loop running of g₂, from M2_star to mu."""
    # d(1/g²)/d(lnμ) = -b₂/(8π²) = +19/(6·8π²)  > 0
    inv_sq = 1.0/g2_UV**2 + (-b2_1loop/(8*pi**2)) * np.log(mu/M2_star)
    if np.isscalar(inv_sq):
        if inv_sq <= 0:
            return np.nan
    else:
        inv_sq = np.where(inv_sq > 0, inv_sq, np.nan)
    return 1.0 / np.sqrt(inv_sq)

# Values at key scales
checkpoints = [1.0, 5.0, 6.9, 10.0, 20.0, 30.0, 37.4, 50.0, 80.0, 91.2,
               120.0, 172.76, 200.0, 246.22, 300.0, 500.0, 1000.0]
print(f"\n  {'μ (GeV)':>10}  {'g₂ (1-loop)':>14}  {'L_EW (bits)':>14}  {'Gap (%)':>12}")
for mu in checkpoints:
    g2v = g2_1loop(mu)
    if not np.isnan(g2v):
        lew = L_EW_from_g2(g2v)
        gap = (pi_over_ln2 - lew) / pi_over_ln2 * 100
        marker = " ◄ bare" if mu == M2_star_1loop else (" ◄ v_PDG" if mu == 246.22 else "")
        print(f"  {mu:>10.2f}  {g2v:>14.8f}  {lew:>14.8f}  {gap:>+11.4f}%{marker}")

# Gap at v under 1-loop running
g2_at_v_1loop = g2_1loop(V_PDG)
L_EW_at_v_1loop = L_EW_from_g2(g2_at_v_1loop)
gap_at_v_1loop = (pi_over_ln2 - L_EW_at_v_1loop) / pi_over_ln2 * 100

# 1-loop closure scale (running DOWN from M₂*)
# 1/g₂(μ)² = 1/g₂_bare² + (-b₂/8π²)·ln(μ/M₂*)
# At closure: 1/g₂_needed² = 1/g₂_bare² + (-b₂/8π²)·ln(μ_c/M₂*)
# → ln(μ_c/M₂*) = (1/g₂_needed² − 1/g₂_bare²) / (-b₂/8π²)
deriv_1over_g2sq = -b2_1loop / (8 * pi**2)  # = 19/(48π²) > 0
delta_inv = 1.0/g2_needed_sq - 1.0/g2_sq_bare   # negative: g₂_needed > g₂_bare
ln_ratio_1loop = delta_inv / deriv_1over_g2sq
mu_closure_1loop = M2_star_1loop * np.exp(ln_ratio_1loop)
dist_1loop = (mu_closure_1loop - V_PDG) / V_PDG * 100

print(f"\n  Summary (1-loop, M₂*=37.4 GeV):")
print(f"    L_EW at bare (37.4 GeV)  = {L_EW_bare:.8f} bits  (gap = {gap_bare_pct:+.4f}%)")
print(f"    L_EW at v   (246.2 GeV)  = {L_EW_at_v_1loop:.8f} bits  (gap = {gap_at_v_1loop:+.4f}%)")
print(f"    Running from M₂* → v WIDENS the gap (L_EW decreases, π/ln2 not reached)")
print(f"    Closure scale (1-loop)   = {mu_closure_1loop:.4f} GeV  [{dist_1loop:+.1f}% from v_PDG]")

# ---------------------------------------------------------------------------
# SECTION 3: Two-loop running with m_t threshold
# ---------------------------------------------------------------------------
print("\n--- SECTION 3: TWO-LOOP RUNNING (with m_t = 172.76 GeV threshold) ---")

# SM beta-function coefficients (MSbar, Buttazzo et al. 2013)
b_1L_SM6 = np.array([ 41.0/10.0, -19.0/6.0, -7.0])
b_1L_SM5 = np.array([ 21.0/5.0,  -3.0,      -23.0/3.0])

b_2L_SM6 = np.array([
    [199.0/50.0, 27.0/10.0, 44.0/5.0],
    [  9.0/10.0, 35.0/6.0,  12.0   ],
    [ 11.0/10.0,  9.0/2.0,  -26.0  ],
])
b_2L_SM5 = np.array([
    [199.0/50.0 - 17.0/10.0, 27.0/10.0 - 3.0/10.0, 44.0/5.0 - 4.0  ],
    [  9.0/10.0 -  3.0/10.0, 35.0/6.0  - 3.0/2.0,  12.0     - 4.0  ],
    [ 11.0/10.0 - 11.0/30.0,  9.0/2.0  - 1.0/2.0,  -26.0 + 22.0/3.0],
])

def rge_2loop(t, g_vec, above_mt):
    b1 = b_1L_SM6 if above_mt else b_1L_SM5
    b2 = b_2L_SM6 if above_mt else b_2L_SM5
    dg = np.zeros(3)
    g_sq = g_vec**2
    for i in range(3):
        dg[i] = (b1[i] * g_vec[i]**3 / (16*pi**2)
                 + g_vec[i]**3 / (16*pi**2)**2 * np.dot(b2[i], g_sq))
    return dg

def run_g2_2loop(mu_target, mu_UV=M2_star_1loop, g2_UV=g2_bare,
                 g1_UV=None, g3_UV=None, mt=MT):
    if g1_UV is None: g1_UV = g1_sq_bare**0.5
    if g3_UV is None: g3_UV = g3_sq_bare**0.5
    g0 = np.array([g1_UV, g2_UV, g3_UV])
    t_start, t_end = np.log(mu_UV), np.log(mu_target)
    t_mt = np.log(mt)

    direction = np.sign(t_end - t_start)
    # Does the path cross mt?
    crosses_mt = ((direction > 0 and t_start < t_mt < t_end) or
                  (direction < 0 and t_end < t_mt < t_start))
    above_start = mu_UV > mt

    if crosses_mt:
        above_leg = above_start
        sol1 = solve_ivp(lambda t, g: rge_2loop(t, g, above_leg),
                         [t_start, t_mt], g0, method='RK45',
                         rtol=1e-10, atol=1e-12)
        g_at_mt = sol1.y[:, -1]
        sol2 = solve_ivp(lambda t, g: rge_2loop(t, g, not above_leg),
                         [t_mt, t_end], g_at_mt, method='RK45',
                         rtol=1e-10, atol=1e-12)
        return sol2.y[1, -1]
    else:
        sol = solve_ivp(lambda t, g: rge_2loop(t, g, above_start),
                        [t_start, t_end], g0, method='RK45',
                        rtol=1e-10, atol=1e-12)
        return sol.y[1, -1]

# Two-loop at key scales
g2_at_v_2loop_37 = run_g2_2loop(V_PDG, mu_UV=M2_star_1loop)
L_EW_at_v_2loop_37 = L_EW_from_g2(g2_at_v_2loop_37)
gap_at_v_2loop_37 = (pi_over_ln2 - L_EW_at_v_2loop_37) / pi_over_ln2 * 100

g2_at_v_2loop_35 = run_g2_2loop(V_PDG, mu_UV=M2_star_2loop)
L_EW_at_v_2loop_35 = L_EW_from_g2(g2_at_v_2loop_35)
gap_at_v_2loop_35 = (pi_over_ln2 - L_EW_at_v_2loop_35) / pi_over_ln2 * 100

print(f"\n  At μ = v_PDG = {V_PDG} GeV:")
print(f"    1-loop  (M₂*=37.4):  g₂={g2_at_v_1loop:.8f}  L_EW={L_EW_at_v_1loop:.8f}  gap={gap_at_v_1loop:+.4f}%")
print(f"    2-loop  (M₂*=37.4):  g₂={g2_at_v_2loop_37:.8f}  L_EW={L_EW_at_v_2loop_37:.8f}  gap={gap_at_v_2loop_37:+.4f}%")
print(f"    2-loop  (M₂*=34.56): g₂={g2_at_v_2loop_35:.8f}  L_EW={L_EW_at_v_2loop_35:.8f}  gap={gap_at_v_2loop_35:+.4f}%")
print(f"    π/ln2:                                        {pi_over_ln2:.8f}")
print(f"\n  Running from M₂* UP to v_PDG:")
print(f"    Gap at bare: {gap_bare_pct:+.4f}%  →  Gap at v (2-loop): {gap_at_v_2loop_35:+.4f}%")
print(f"    Running INCREASES the gap by {abs(gap_at_v_2loop_35) - abs(gap_bare_pct):.4f}% (moves further from π/ln2)")

# ---------------------------------------------------------------------------
# SECTION 4: Find the 2-loop closure scale
# ---------------------------------------------------------------------------
print("\n--- SECTION 4: TWO-LOOP CLOSURE SCALE SEARCH ---")
print("  (searching for μ where L_EW(μ) = π/ln2 under 2-loop running)")

def L_EW_at_scale_2loop(mu, M2_star=M2_star_2loop):
    g2 = run_g2_2loop(mu, mu_UV=M2_star)
    return L_EW_from_g2(g2)

def residual_2loop(mu):
    return L_EW_at_scale_2loop(mu) - pi_over_ln2

# Scan to find sign change
print(f"\n  Scan of L_EW(μ) - π/ln2 (2-loop, M₂*=34.56):")
scan_pts = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 10.0, 15.0, 20.0,
            30.0, 34.56, 37.4, 50.0, 80.0, 120.0, 172.76, 246.22, 500.0]
residuals = {}
for mu in scan_pts:
    try:
        r = residual_2loop(mu)
        residuals[mu] = r
        print(f"    μ={mu:8.2f} GeV: residual = {r:+.6f} bits  (L_EW = {r + pi_over_ln2:.6f})")
    except Exception as e:
        print(f"    μ={mu:8.2f} GeV: ERROR {e}")

# Find bracket where sign changes
mu_closure_2loop = None
dist_2loop = None
for i, mu_a in enumerate(scan_pts[:-1]):
    mu_b = scan_pts[i+1]
    ra, rb = residuals.get(mu_a), residuals.get(mu_b)
    if ra is not None and rb is not None and ra * rb < 0:
        print(f"\n  Sign change found between {mu_a} and {mu_b} GeV")
        try:
            mu_closure_2loop = brentq(residual_2loop, mu_a, mu_b,
                                      xtol=0.01, rtol=1e-6)
            dist_2loop = (mu_closure_2loop - V_PDG) / V_PDG * 100
            print(f"  → 2-loop closure scale = {mu_closure_2loop:.4f} GeV")
            print(f"  → v_PDG               = {V_PDG:.4f} GeV")
            print(f"  → Distance from v_PDG = {dist_2loop:+.1f}%")
        except Exception as e:
            print(f"  → Brentq failed: {e}")

# Also do 1-loop scan for comparison
print(f"\n  1-loop closure scale = {mu_closure_1loop:.4f} GeV  ({dist_1loop:+.1f}% from v_PDG)")

# ---------------------------------------------------------------------------
# SECTION 5: Self-consistent fixed-point analysis
# ---------------------------------------------------------------------------
print("\n--- SECTION 5: SELF-CONSISTENT FIXED-POINT ANALYSIS ---")
print("  PSC formula: v² = (ln2/π) × L_EW(μ=v) × M_ref²")
print("  If M_ref = v and L_EW(v) = π/ln2:  v = v (trivially consistent)")
print()

for label, L_val in [("bare (M₂*=37.4)", L_EW_bare),
                      ("1-loop (v_PDG)", L_EW_at_v_1loop),
                      ("2-loop M₂*=34.56 (v_PDG)", L_EW_at_v_2loop_35)]:
    coeff = (ln2/pi) * L_val
    print(f"  {label}:")
    print(f"    L_EW = {L_val:.6f} bits,  (ln2/π)×L_EW = {coeff:.6f}")
    print(f"    M_ref needed for v=246.22 GeV: {V_PDG / coeff**0.5:.4f} GeV")
    print()

# What M_ref = v_PDG would give?
# v_self² = (ln2/π) × L_EW(v) × v² → v_self = v × sqrt((ln2/π) × L_EW(v))
v_self_2loop = V_PDG * ((ln2/pi) * L_EW_at_v_2loop_35)**0.5
print(f"  If M_ref = v_PDG (self-referential with 2-loop L_EW):")
print(f"    v_self = v_PDG × √((ln2/π)×L_EW) = {V_PDG} × {((ln2/pi)*L_EW_at_v_2loop_35)**0.5:.6f}")
print(f"    v_self = {v_self_2loop:.4f} GeV  (should equal 246.22 if closure holds)")
print(f"    Residual: {v_self_2loop - V_PDG:+.4f} GeV  ({(v_self_2loop-V_PDG)/V_PDG*100:+.4f}%)")

# ---------------------------------------------------------------------------
# VERDICT
# ---------------------------------------------------------------------------
print("\n" + "=" * 72)
print("VERDICT")
print("=" * 72)

print(f"""
  QUESTION: Does L_EW(μ=v) = π/ln2 under two-loop RG running?

  ANSWER: NO — definitively negative for the specific hypothesis.

  Numerical results:
    π/ln2                        = {pi_over_ln2:.8f} bits
    L_EW at bare (M₂*=37.4)     = {L_EW_bare:.8f} bits  (gap: {gap_bare_pct:+.4f}%)
    L_EW at v=246 GeV (2-loop)  = {L_EW_at_v_2loop_35:.8f} bits  (gap: {gap_at_v_2loop_35:+.4f}%)

  Key structural finding:
    L_EW(μ) = 2·log₂(g₂(μ)) + log₂(625/12)
    Since g₂ is asymptotically free (decreases as μ increases),
    L_EW DECREASES monotonically as μ increases from M₂* to v.
    Running from M₂*=37.4 GeV UP to v=246 GeV makes the gap WIDER.
    The hypothesis that the gap closes under upward running is FALSE.

  Closure scale (where L_EW = π/ln2 exactly):
    1-loop: μ_closure ≈ {mu_closure_1loop:.2f} GeV  (running DOWN from M₂*)
    2-loop: μ_closure ≈ {f"{mu_closure_2loop:.2f}" if mu_closure_2loop else "not found"} GeV  (running DOWN from M₂*)
    Both are ~30 GeV below M₂*, nowhere near v = 246 GeV.

  Rating: NEGATIVE — PSC self-referential condition L_EW(v) = π/ln2
          is NOT satisfied at the EW scale under SM running.
          Gap grows from −0.95% at M₂* to −{abs(gap_at_v_2loop_35):.2f}% at v.
""")

# ---------------------------------------------------------------------------
# SAVE JSON
# ---------------------------------------------------------------------------
results = {
    "experiment": "Direction H Round 3: PSC Self-Referential EW Closure",
    "date": "2026-05-15",
    "formula": "L_EW(mu) = 2*log2(g2(mu)) + log2(625/12)",
    "structural_note": "D_SU2 = g2^2 * 25/2 = 2329/432 (gauge master formula, L_SU2=2, gamma=2)",
    "pi_over_ln2": pi_over_ln2,
    "log2_625_over_12": LOG2_625_OVER_12,
    "bare": {
        "D_SU2": D_SU2_bare,
        "g2_sq": g2_sq_bare,
        "L_EW": L_EW_bare,
        "gap_pct": gap_bare_pct,
    },
    "one_loop": {
        "M2_star_GeV": M2_star_1loop,
        "g2_at_v": g2_at_v_1loop,
        "L_EW_at_v": L_EW_at_v_1loop,
        "gap_at_v_pct": gap_at_v_1loop,
        "mu_closure_GeV": mu_closure_1loop,
        "dist_closure_from_v_pct": dist_1loop,
    },
    "two_loop_M2_37p4": {
        "M2_star_GeV": M2_star_1loop,
        "g2_at_v": g2_at_v_2loop_37,
        "L_EW_at_v": L_EW_at_v_2loop_37,
        "gap_at_v_pct": gap_at_v_2loop_37,
    },
    "two_loop_M2_34p56": {
        "M2_star_GeV": M2_star_2loop,
        "g2_at_v": g2_at_v_2loop_35,
        "L_EW_at_v": L_EW_at_v_2loop_35,
        "gap_at_v_pct": gap_at_v_2loop_35,
        "mu_closure_GeV": mu_closure_2loop,
        "dist_closure_from_v_pct": dist_2loop,
    },
    "verdict": "NEGATIVE",
    "summary": (
        "L_EW(mu) decreases monotonically as mu increases (asymptotic freedom). "
        "Running from M2*=37.4 GeV up to v=246 GeV widens the gap from -0.95% to ~-1.99%. "
        "Closure scale is ~7 GeV (1-loop), not 246 GeV. "
        "PSC self-referential fixed point is NOT at the EW scale."
    ),
}

with open("direction_H_round3_closure.json", "w") as f:
    json.dump(results, f, indent=2)

print("Saved: direction_H_round3_closure.json")
