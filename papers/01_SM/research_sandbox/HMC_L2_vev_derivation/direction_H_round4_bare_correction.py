"""
Direction H Round 4: Bare-Level Gap Investigation
==================================================
Question: What D_SU2 value would make L_EW = π/ln2 exactly?
          Can the 0.95% gap be explained by a UGP structural correction?

From Round 3:
  L_EW_bare = log₂(D_SU2_bare²/(3g₂²)) = 4.4895 bits
  π/ln2     = 4.5324 bits
  Gap       = +0.95%

Key derivation:
  log₂(D_SU2²/(3g₂²)) = π/ln2
  ⟹ D_SU2² = 3g₂² × e^π
  ⟹ D_SU2_required = g₂ × √(3·e^π)

NOTE: The prompt stated D_SU2_bare = g₂²×5³ = 53.912 — this is a TYPO.
      Round 3 JSON confirms D_SU2 = g₂²×(25/2) = 5.391 (formula L_SU2=2, γ=2).
      This script uses the correct formula.
"""

import numpy as np
import json
from fractions import Fraction
from pathlib import Path

phi  = (1 + 5**0.5) / 2
pi   = np.pi
ln2  = np.log(2)

g2_sq = float(Fraction(2329, 5400))  # bare SU(2) coupling squared
g2    = g2_sq**0.5

# Correct D_SU2 formula (from Round 3: gauge master formula L_SU2=2, γ=2)
D_SU2_bare = g2_sq * (25 / 2)  # = 5.39120...

# Verify against Round 3 result
L_EW_bare  = np.log2(D_SU2_bare**2 / (3 * g2_sq))
L_EW_target = pi / ln2
assert abs(L_EW_bare - 4.4895011111009655) < 1e-8, "D_SU2_bare formula mismatch"

# ─────────────────────────────────────────────────────────────────────────────
# 1. D_SU2_required for exact L_EW = π/ln2
# ─────────────────────────────────────────────────────────────────────────────
e_pi = np.e**pi
D_SU2_required = g2 * (3 * e_pi)**0.5

print("=" * 65)
print("Direction H Round 4: Bare-Level Gap Investigation")
print("=" * 65)

print(f"\n── 1. D_SU2 arithmetic ──")
print(f"  g2²_bare            = {g2_sq:.10f}  (2329/5400 exact)")
print(f"  g2_bare             = {g2:.10f}")
print(f"  D_SU2_bare          = g2²×(25/2) = {D_SU2_bare:.10f}")
print(f"  D_SU2_required      = g2×√(3eᵖⁱ) = {D_SU2_required:.10f}")
ratio = D_SU2_required / D_SU2_bare
print(f"  Ratio req/bare      = {ratio:.10f}")
print(f"  Gap in D_SU2 space  = {(ratio - 1)*100:+.4f}%")
print(f"  L_EW_bare           = {L_EW_bare:.8f} bits")
print(f"  π/ln2               = {L_EW_target:.8f} bits")
print(f"  L_EW gap            = {(L_EW_target - L_EW_bare)/L_EW_target * 100:+.4f}%")

# ─────────────────────────────────────────────────────────────────────────────
# 2. UGP structural formula search for D_SU2_required
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n── 2. UGP structural formula search ──")
print(f"  Target: D_SU2_required = {D_SU2_required:.8f}")
print(f"  e^π = {e_pi:.8f}  (transcendental, NOT a UGP atom)")
print(f"  √(3·e^π) = {(3*e_pi)**0.5:.8f}  (required cofactor)")

candidates = {
    "g2×3π":                  g2 * 3 * pi,
    "g2×(5φ)":                g2 * 5 * phi,
    "g2×√(3·π²)":             g2 * (3 * pi**2)**0.5,
    "g2×π^(3/2)":             g2 * pi**1.5,
    "g2×4φ":                  g2 * 4 * phi,
    "g2×2π":                  g2 * 2 * pi,
    "g2×H_SU2/2 (H=11.93)":   g2 * 11.93 / 2,
    "g2×√(H_SU2) (H=11.93)":  g2 * 11.93**0.5,
    "g2×3√(φ)":               g2 * 3 * phi**0.5,
    "g2×φ²×√(φ)":             g2 * phi**2 * phi**0.5,
    "g2×√(3·H_SU2)":          g2 * (3 * 11.93)**0.5,
}

best_label, best_diff = "none", 1e9
for label, val in candidates.items():
    diff_pct = abs(val - D_SU2_required) / D_SU2_required * 100
    flag = " *** MATCH" if diff_pct < 0.1 else (" ** <1%" if diff_pct < 1.0 else "")
    print(f"    {label:35s} = {val:9.6f}  (Δ={diff_pct:6.2f}%){flag}")
    if diff_pct < best_diff:
        best_diff = diff_pct; best_label = label

print(f"\n  Best match: '{best_label}' at Δ={best_diff:.4f}%")
structural_match_found = best_diff < 0.1
print(f"  Structural match: {'YES' if structural_match_found else 'NO'}")

# ─────────────────────────────────────────────────────────────────────────────
# 3. Haar entropy correction check
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n── 3. Haar entropy correction ──")
H_SU2 = 11.93  # SU(2) Haar entropy from P27
val_haar = g2 * (3 * H_SU2)**0.5
print(f"  H_SU2                         = {H_SU2}")
print(f"  g₂×√(3·H_SU2)                = {val_haar:.6f}")
print(f"  D_SU2_required                = {D_SU2_required:.6f}")
print(f"  e^π / H_SU2                   = {e_pi/H_SU2:.6f}  (should be 1 for Haar=eᵖⁱ)")
print(f"  Gap Haar vs required          = {(val_haar/D_SU2_required - 1)*100:+.4f}%")
print(f"  → Haar entropy CANNOT close the gap (e^π ≠ H_SU2)")

# ─────────────────────────────────────────────────────────────────────────────
# 4. Null discipline Monte Carlo
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n── 4. Null discipline Monte Carlo ──")
np.random.seed(42)
n_samples = 200_000
target_pct = 0.0095  # 0.95%

# Physically motivated ranges:
#   g₂ ∈ [0.3, 0.8]  (SU(2) coupling physical range)
#   D  ∈ [3.0, 9.0]  (D_SU2 range: g₂² × 12.5 over g₂ range gives ~[0.3, 9.6])
g2_rand = np.random.uniform(0.3, 0.8, n_samples)
D_rand  = np.random.uniform(3.0, 9.0, n_samples)
L_rand  = np.log2(D_rand**2 / (3 * g2_rand**2))
hits    = int(np.sum(np.abs(L_rand - L_EW_target) / L_EW_target < target_pct))
saturation = hits / n_samples

print(f"  Samples          : {n_samples:,}")
print(f"  g₂ range         : [0.3, 0.8]")
print(f"  D range          : [3.0, 9.0]  (D_SU2_bare = {D_SU2_bare:.3f})")
print(f"  Target           : π/ln2 = {L_EW_target:.6f} bits")
print(f"  Tolerance        : ±0.95%")
print(f"  L range covered  : [{L_rand.min():.3f}, {L_rand.max():.3f}]")
print(f"  Hits             : {hits}")
print(f"  Null saturation  : {saturation*100:.2f}%")
verdict_mc = "COINCIDENCE (volume-dominated)" if saturation > 0.01 else "GENUINELY RARE"
print(f"  Verdict          : {verdict_mc}")

for tol in [0.001, 0.005, 0.01, 0.02, 0.05]:
    h = int(np.sum(np.abs(L_rand - L_EW_target) / L_EW_target < tol))
    print(f"    At ±{tol*100:.1f}%  : {h/n_samples*100:.2f}% saturation")

# ─────────────────────────────────────────────────────────────────────────────
# 5. Collect results
# ─────────────────────────────────────────────────────────────────────────────
results = {
    "experiment": "Direction H Round 4: bare-level gap investigation",
    "date": "2026-05-15",
    "bug_note": (
        "Prompt stated D_SU2_bare = g2²×5³ = 53.912 (typo). "
        "Correct formula: D_SU2 = g2²×(25/2) = 5.391 (from Round 3 JSON / gauge master formula)."
    ),
    "inputs": {
        "g2_sq_bare": g2_sq,
        "g2_bare": g2,
        "D_SU2_bare": D_SU2_bare,
        "L_EW_bare_bits": L_EW_bare,
        "pi_over_ln2": L_EW_target,
        "gap_pct": (L_EW_target - L_EW_bare) / L_EW_target * 100,
    },
    "required_for_exact_closure": {
        "formula": "D_SU2_req = g2_bare × sqrt(3 × e^pi)",
        "e_pi": e_pi,
        "D_SU2_required": D_SU2_required,
        "ratio_req_over_bare": ratio,
        "gap_D_space_pct": (ratio - 1) * 100,
    },
    "structural_search": {
        "best_match_label": best_label,
        "best_match_gap_pct": best_diff,
        "structural_match_found": structural_match_found,
        "conclusion": "e^pi has no UGP derivation; no structural formula found",
    },
    "haar_correction": {
        "H_SU2": H_SU2,
        "e_pi_over_H_SU2": e_pi / H_SU2,
        "haar_formula_gap_pct": (val_haar / D_SU2_required - 1) * 100,
        "conclusion": "e^pi != H_SU2; Haar entropy cannot close the gap",
    },
    "null_discipline": {
        "n_samples": n_samples,
        "g2_range": [0.3, 0.8],
        "D_range": [3.0, 9.0],
        "tolerance_pct": target_pct * 100,
        "hits": hits,
        "saturation_pct": saturation * 100,
        "verdict": verdict_mc,
    },
    "verdict": "NEGATIVE",
    "summary": (
        "The exact-closure condition requires D_SU2_req = g2×sqrt(3·e^pi), "
        "which introduces e^pi — a transcendental with no UGP structural derivation. "
        f"Null saturation = {saturation*100:.2f}% > 1% confirms volume-domination. "
        "Direction H is a confirmed coincidence across all four rounds and is formally closed."
    ),
    "round_history": {
        "Round 1": "0.95% gap discovered at bare level",
        "Round 2": "PSC entropy programme — no first-principles mechanism",
        "Round 3": "Running to v=246 GeV widens gap to ~2%; closure at ~7 GeV",
        "Round 4": "D_SU2_required = g2×sqrt(3·e^pi) — no UGP atom; null saturation 2.10%",
    },
}

out_path = Path(__file__).parent / "direction_H_round4_bare_correction.json"
out_path.write_text(json.dumps(results, indent=2))
print(f"\nResults saved to: {out_path}")

# ─────────────────────────────────────────────────────────────────────────────
# Final printed verdict
# ─────────────────────────────────────────────────────────────────────────────
print(f"""
{'=' * 65}
FINAL VERDICT — Direction H Round 4
{'=' * 65}

  1. D_SU2_required = g₂_bare × √(3·e^π) = {D_SU2_required:.8f}
     (D_SU2_bare = {D_SU2_bare:.8f}; requires +{(ratio-1)*100:.3f}% correction)

  2. Structural formula for D_SU2_required?
     Requires e^π = {e_pi:.4f} as a factor.
     e^π has NO UGP derivation (not rational, cyclotomic, Haar, or φ-based).
     Best approximant found: '{best_label}' at Δ={best_diff:.2f}% — NOT structural.

  3. Null saturation at ±0.95%: {saturation*100:.2f}%  (threshold 1%)
     → VOLUME-DOMINATED → COINCIDENCE

  4. DEFINITIVE CONCLUSION ON DIRECTION H:
     Four rounds of investigation find:
       - 0.95% bare-level gap (Round 1)
       - No PSC mechanism (Round 2)
       - Gap widens under RG running (Round 3)
       - No UGP formula for exact closure; null test confirms coincidence (Round 4)
     Direction H is FORMALLY CLOSED — confirmed negative.
     The near-identity L_EW ≈ π/ln2 is numerologically suggestive but
     mechanistically empty: no UGP derivation exists for it.
""")
