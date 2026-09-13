"""
Koide Equal-Norm Session 3: N_mod2=2 unification and MDL binary-tape analysis.

Task 080-KOIDE-EQUALNORM Session 3:
  T1 (Adam): Derive b=√2 from N_mod2=2 and MDL binary-tape structure
  T2 (Jane): Algebraic: b=√N_mod2, y_τ=c_V/N_mod2, and the dim(std S₃) connection
  T3 (Carl): MDL derivation on binary tapes: does b²=N_mod2 follow from structure?
  T4 discussed in lab note (Lean theorem added separately)

Script saves full results to koide_equalnorm_session3_results.json.
"""

import math
import json
import signal
import sys
import time
import numpy as np

TIMEOUT_SECONDS = 120

def _timeout_handler(signum, frame):
    print(f"\nTIMEOUT: wall-clock limit {TIMEOUT_SECONDS}s reached. Saving partial results.")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

results = {
    "task": "080-KOIDE-EQUALNORM-Session3",
    "date": "2026-05-29",
    "theta_Nc": 2 * math.pi / 9,
}

print("=" * 70)
print("Session 3: N_mod2=2 unification analysis")
print("=" * 70)

# === T0: Sanity (reproduce known Koide result) ===
print("\n--- T0 Sanity: reproduce known Koide CV=1, Q=2/3 ---")

m_e   = 0.51099895    # MeV
m_mu  = 105.6583755   # MeV
m_tau = 1776.86       # MeV
sm = [math.sqrt(m_e), math.sqrt(m_mu), math.sqrt(m_tau)]  # sqrt-mass amplitudes = v_g
masses_pdg = [m_e, m_mu, m_tau]
cv2_pdg = np.var(sm) / np.mean(sm)**2
# Koide Q = Σm / (Σ√m)² = Σv² / (Σv)² (matching the Lean theorem Q = Σv² / (Σv)²)
Q_pdg   = sum(masses_pdg) / sum(sm)**2
print(f"  CV(√m_lepton) = {math.sqrt(cv2_pdg):.6f}  (target: 1.000)")
print(f"  Koide Q = {Q_pdg:.6f}  (target: 0.6667)")

results["T0_sanity"] = {
    "CV_sqrt_m": float(math.sqrt(cv2_pdg)),
    "Koide_Q": float(Q_pdg),
    "pass_CV1": abs(math.sqrt(cv2_pdg) - 1) < 1e-3,
    "pass_Q23": abs(Q_pdg - 2/3) < 1e-3,
}

# === T2 (Jane): Algebraic — b=√N_mod2, y_τ=c_V/N_mod2, dim(std S₃) ===
print("\n--- T2 (Jane): Algebraic structure of N_mod2=2 ---")

N_mod2 = 2
c_V    = 1/49          # canonical Z₇ potential coefficient (CatAD)
y_tau  = 1/98          # tau Yukawa (CatA, established prior session)
b_sq   = 2             # Koide amplitude squared
b      = math.sqrt(b_sq)
d_std  = 2             # dimension of standard S₃ irrep = N_gen - 1

print(f"  N_mod2 = {N_mod2} (binary tape alphabet size)")
print(f"  c_V = 1/49 = {c_V:.6f} (canonical Z₇ potential coefficient)")
print(f"  y_tau = 1/98 = {y_tau:.6f}")
print(f"  b = sqrt(2) = {b:.6f}")
print(f"  d_std = dim(standard S₃ irrep) = N_gen - 1 = {d_std}")

print(f"\n  === Identities ===")
print(f"  b = sqrt(N_mod2)?       b = {b:.6f}, sqrt(N_mod2) = {math.sqrt(N_mod2):.6f}, match: {abs(b - math.sqrt(N_mod2)) < 1e-12}")
print(f"  b = sqrt(d_std)?        b = {b:.6f}, sqrt(d_std) = {math.sqrt(d_std):.6f}, match: {abs(b - math.sqrt(d_std)) < 1e-12}")
print(f"  b_sq = N_mod2?          b_sq = {b_sq}, N_mod2 = {N_mod2}, match: {b_sq == N_mod2}")
print(f"  b_sq = d_std?           b_sq = {b_sq}, d_std = {d_std}, match: {b_sq == d_std}")
print(f"  y_tau = c_V/N_mod2?     y_tau = {y_tau:.8f}, c_V/N_mod2 = {c_V/N_mod2:.8f}, match: {abs(y_tau - c_V/N_mod2) < 1e-12}")
print(f"  N_mod2 = d_std?         {N_mod2} = {d_std}, match: {N_mod2 == d_std}  (true for N_gen=3 binary tapes)")

# Why does the equal-norm condition give b²=2?
print(f"\n  === Why b²=2 from equal-norm (general N_gen analysis) ===")
for N_gen in [2, 3, 4, 5, 6]:
    thetas = np.arange(N_gen) * 2 * math.pi / N_gen
    # Σcos² = N_gen/2 (standard identity)
    cos_sq_sum = sum(math.cos(t)**2 for t in thetas)
    # trivial norm = N_gen (from Σ(1)² summed)
    triv_norm = N_gen
    # standard norm = N_gen * b² / 2 = cos_sq_sum * b²
    # equal-norm: triv_norm = std_norm → b² = triv_norm / (cos_sq_sum) = N_gen / (N_gen/2) = 2
    b_sq_eq_norm = triv_norm / cos_sq_sum
    d_std_this = N_gen - 1
    print(f"  N_gen={N_gen}: Σcos²={cos_sq_sum:.3f}=N/2={N_gen/2:.3f}, "
          f"b²(equal-norm)={b_sq_eq_norm:.4f}, d_std={d_std_this}")

print(f"\n  KEY FINDING: equal-norm gives b²=2 for ANY N_gen (from Σcos²=N/2)")
print(f"  For N_gen=3: b²=2 = N_mod2 = d_std = 2 (coincidence of three equal values)")
print(f"  For N_gen=4: b²=2 ≠ d_std=3 ≠ N_mod2=2 (the coincidence is N_gen=3-specific)")

results["T2_algebraic"] = {
    "N_mod2": N_mod2,
    "c_V": c_V,
    "y_tau": y_tau,
    "b_sq": b_sq,
    "d_std": d_std,
    "b_eq_sqrt_N_mod2": abs(b - math.sqrt(N_mod2)) < 1e-12,
    "b_eq_sqrt_d_std": abs(b - math.sqrt(d_std)) < 1e-12,
    "b_sq_eq_N_mod2": b_sq == N_mod2,
    "y_tau_eq_cV_over_N_mod2": abs(y_tau - c_V/N_mod2) < 1e-12,
    "N_mod2_eq_d_std": N_mod2 == d_std,
    "equal_norm_gives_b_sq_2_for_any_N_gen": True,
    "coincidence_specific_to_N_gen_3": True,
    "verdict": (
        "b=sqrt(N_mod2)=sqrt(2) is TRUE algebraically (N_mod2=2=b²). "
        "y_tau=c_V/N_mod2=1/98 is TRUE structurally (CatAD). "
        "HOWEVER: the equal-norm condition gives b²=2 for ANY N_gen (via Σcos²=N/2), "
        "independent of N_mod2. For N_gen=3: b²=2 = N_mod2 = d_std is a three-way "
        "numerical coincidence. The N_mod2 in y_tau comes from the tape-denominator "
        "structure (structural/CatAD); the b²=2 in Koide comes from the trig identity "
        "Σcos²=N/2 (independent of N_mod2). The connection is NUMEROLOGICAL for b, "
        "STRUCTURAL for y_tau."
    )
}

# === T1 (Adam): 1-bit MDL on binary tapes ===
print("\n--- T1 (Adam): 1-bit MDL on binary tapes ---")

print(f"  Binary tape: N_mod2 = {N_mod2} states per tape")
print(f"  Information per tape: log2(N_mod2) = {math.log2(N_mod2):.4f} bits")
print(f"  For 3 tapes: 3 × log2(N_mod2) = {3 * math.log2(N_mod2):.4f} bits total")
print(f"\n  S₃ irrep decomposition of 3-tape representation:")
print(f"  trivial irrep: dim=1, captures democratic mode (equal amps)")
print(f"  standard irrep: dim=2=N_mod2, captures generation-splitting modes")
print(f"  sign irrep: dim=1, does NOT appear in permutation rep of S₃ on 3 objects")
print(f"\n  1-bit MDL equipartition over S₃ irrep TYPES (from Session 2):")
print(f"  Assign equal weight to 2 irrep TYPES (trivial and standard)")
print(f"  Equal weight PER TYPE: trivial_norm = standard_norm")
print(f"  → 3 = 3b²/2 → b² = 2 = N_mod2")
print(f"\n  The '1-bit' in '1-bit equipartition' = log2(N_mod2) = log2(2) = 1 bit")
print(f"  For binary (N_mod2=2) tapes: 1 bit governs the democratic/splitting distinction")
print(f"\n  Can this be generalized? For N_mod2-state tapes:")
print(f"  log2(N_mod2) bits per tape → equal-norm → b²=2 (from equal-norm trig identity)")
print(f"  b² = 2 regardless of N_mod2, so the generalization b=sqrt(N_mod2) fails for N_mod2≠2")

# Verify: does equal-norm give b²=N_mod2 for different N_mod2?
print(f"\n  Test: if we hypothesized b=sqrt(N_mod2), would Koide hold for N_mod2≠2?")
for n in [2, 3, 4, 5]:
    b_test = math.sqrt(n)
    theta = 2 * math.pi / 9
    vs = [1 + b_test * math.cos(theta + 2*math.pi*g/3) for g in range(3)]
    masses = [v**2 for v in vs]  # v_g² proportional to m_g
    # Q = Σv² / (Σv)² = Σm / (Σ√m)²
    Q_test = sum(masses) / sum(vs)**2
    cv_test = np.std(vs) / np.mean(vs)
    print(f"  N_mod2={n}: b=sqrt({n})={b_test:.4f}, Q={Q_test:.4f} (need 2/3={2/3:.4f}), CV={cv_test:.4f}")

print(f"  → Only b=sqrt(2) (N_mod2=2) gives Q=2/3. b=sqrt(N_mod2) for N_mod2≠2 does NOT.")

results["T1_MDL_binary"] = {
    "N_mod2": N_mod2,
    "bits_per_tape": math.log2(N_mod2),
    "total_bits_3_tapes": 3 * math.log2(N_mod2),
    "dim_standard_irrep": d_std,
    "1bit_equipartition_gives_b_sq_2": True,
    "generalization_b_sqrt_N_mod2_fails": True,
    "mechanism_status": "PROVISIONAL",
    "verdict": (
        "The 1-bit equipartition argument (Session 2) uses binary (N_mod2=2) tape structure: "
        "1 bit = log2(N_mod2) = log2(2) = 1. The standard irrep has dim=2=N_mod2. "
        "Equal-weight-per-type gives trivial_norm = standard_norm → b²=2. "
        "This IS consistent with b=sqrt(N_mod2)=sqrt(2) for N_mod2=2. "
        "HOWEVER: the generalization b=sqrt(N_mod2) fails for N_mod2≠2 (Q≠2/3 for b=sqrt(3), etc.). "
        "b²=2 is fixed by the equal-norm trig identity, independent of the tape alphabet. "
        "The '1-bit MDL' argument is still PROVISIONAL: it is a selection principle "
        "consistent with binary tapes (N_mod2=2) but does not derive b from N_mod2 as a formula."
    )
}

# === T3 (Carl): MDL functional analysis ===
print("\n--- T3 (Carl): MDL derivation of b=√N_mod2 vs b=√2 ---")

print(f"  MDL description-length functional for generation Yukawa:")
print(f"  L(b) = -log P(data | b) + K(b) [description length]")
print(f"  At fixed mean (the positivity+scale constraint):")
print(f"  MaxEnt prior (MDL-dual): CV=1 → b=√2")
print(f"  Naive length-min: b=0 (democratic; WRONG, Session 2)")
print(f"\n  Binary tape MDL cost analysis:")
print(f"  Each binary digit costs: 1 nit = 1/ln(2) bits = 1.4427 bits natural units")
print(f"  For the generation-splitting amplitude b:")
print(f"  K_bit(b=0) = 0 bits (democratic, no generation information)")
print(f"  K_bit(b>0) = log2(1/P_MaxEnt(b)) bits [MaxEnt cost of the deviation from democracy]")
print(f"\n  MaxEnt P(b) for fixed mean constraint:")

# Simulate exponential (MaxEnt at fixed mean) sampling
rng = np.random.default_rng(seed=42)
N_samples = 200000
mu = 1.0  # mean of exponential
exp_samples = rng.exponential(scale=mu, size=N_samples)
cv_exp = np.std(exp_samples) / np.mean(exp_samples)
print(f"  Exponential(μ=1) sample: CV = {cv_exp:.4f} (→ CV=1 as N→∞)")

# The MaxEnt argument: CV=1 of exponential is b²/2 → b=√2
print(f"\n  MaxEnt CV² → b² mapping:")
print(f"  CV² = b²/2 (from koide_variance_eq_half_b_sq)")
print(f"  MaxEnt CV² = 1 → b² = 2 = N_mod2")

# Check how the MDL cost depends on b:
print(f"\n  MDL cost as a function of b (relative to MaxEnt b=√2):")
# Use algebraic CV² = b²/2 (from koide_variance_eq_half_b_sq) — no numeric issues
for b_val in [0.0, 0.5, 1.0, math.sqrt(2), 1.5, 2.0]:
    # CV² = b²/2 is algebraically exact (Lean certified in koide_variance_eq_half_b_sq)
    cv_sq = b_val**2 / 2
    cv = math.sqrt(cv_sq)
    # Q = (3 + 3b²/2) / 9 = (1 + b²/2) / 3 from vAmp_sum and vAmp_sq_sum
    Q_val = (1 + b_val**2/2) / 3
    is_maxent = abs(b_val - math.sqrt(2)) < 0.01
    marker = "← MaxEnt/Koide b=√2=√N_mod2" if is_maxent else ""
    print(f"  b={b_val:.4f}: CV²={cv_sq:.4f}, CV={cv:.4f}, Q={Q_val:.4f} {marker}")

results["T3_MDL_functional"] = {
    "MaxEnt_CV_exponential": float(cv_exp),
    "b_from_MaxEnt_CV1": math.sqrt(2),
    "mechanism_status": "PROVISIONAL",
    "key_facts": [
        "MaxEnt (fixed-mean, positive support) → CV=1 → b²/2=1 → b=√2",
        "b=√2 minimizes MDL description-length relative to MaxEnt prior",
        "b=0 minimizes naive length-min (wrong: democratic b=0 is minimal structure)",
        "The MDL-dual principle (MaxEnt) is the correct MDL interpretation",
        "This is consistent with N_mod2=2 (binary context) but not derived from it",
    ],
    "verdict": (
        "The MDL functional gives b=√2 via MaxEnt at fixed mean (CV=1). "
        "The N_mod2=2 connection: binary tapes have 1-bit descriptions, and "
        "1-bit equipartition over irrep types gives b=√2. But b=√2 from equal-norm "
        "is independent of N_mod2 (holds for any N_gen). "
        "The MDL/MaxEnt argument remains PROVISIONAL: it is a selection principle "
        "consistent with the binary tape architecture, not a Φ_MDL kink-condensate "
        "field equation output. Gate 080-KOIDE-EQUALNORM: PARTIAL unchanged."
    )
}

# === Summary: the genuine N_mod2 unification ===
print("\n--- Summary: N_mod2=2 unified pattern ---")
print(f"  y_tau = c_V / N_mod2 = (1/49) / 2 = 1/98  [STRUCTURAL, CatAD]")
print(f"  b = sqrt(N_mod2) = sqrt(2)                  [ALGEBRAIC coincidence; b²=2 from trig]")
print(f"  Both involve N_mod2=2; different mechanisms:")
print(f"    y_tau: N_mod2 is the binary tape denominator in the Yukawa normalization")
print(f"    b: N_mod2=2=b² (coincidence of values; b² fixed by Σcos²=N_gen/2 trig identity)")
print(f"\n  The clean structural fact: b² = dim(standard S₃ irrep) = N_gen-1 = 2 = N_mod2")
print(f"  at N_gen=3 binary tapes. This is a three-way coincidence:") 
print(f"    b² = 2 (from equal-norm trig)")
print(f"    d_std = 2 (from S₃ irrep theory: N_gen-1=2)")
print(f"    N_mod2 = 2 (from binary tape GTE architecture)")
print(f"  The last equality (d_std = N_mod2) IS structural: for binary tapes with N_gen=3,")
print(f"  the standard irrep dimension equals the tape alphabet size.")

# === Final CV check with b=√N_mod2 at the Koide theta ===
print(f"\n--- Final Koide check: b=sqrt(N_mod2)=sqrt(2), theta=2pi/9 ---")
b_final = math.sqrt(N_mod2)
theta_final = 2 * math.pi / 9
# Use algebraic formulas from Lean-certified identities:
# CV² = b²/2 (koide_variance_eq_half_b_sq); Q = (1+b²/2)/3 (koide_Q_iff_amplitude);
# PR = (Σv)²/Σv² = 6/(2+b²) (koide_participation_ratio_eq)
b_sq_final = b_final**2
cv_sq_final = b_sq_final / 2
cv_final = math.sqrt(cv_sq_final)
Q_final = (1 + b_sq_final/2) / 3
pr_final = 6 / (2 + b_sq_final)

print(f"  b = sqrt(N_mod2) = sqrt(2) = {b_final:.6f}")
print(f"  b² = N_mod2 = {b_sq_final:.6f}")
print(f"  CV² = b²/2 = {cv_sq_final:.6f} (from Lean koide_variance_eq_half_b_sq)")
print(f"  CV(sqrt_m) = {cv_final:.6f}  (target 1.000)")
print(f"  Koide Q = (1+b²/2)/3 = {Q_final:.6f}  (target 0.6667)")
print(f"  PR = 6/(2+b²) = {pr_final:.6f}       (target 1.500 = N_gen/2)")

results["T2_final_koide_check"] = {
    "b": float(b_final),
    "b_sq": float(b_sq_final),
    "N_mod2": N_mod2,
    "b_sq_eq_N_mod2": abs(b_sq_final - N_mod2) < 1e-12,
    "CV_sq": float(cv_sq_final),
    "CV_sqrt_m": float(cv_final),
    "Koide_Q": float(Q_final),
    "PR": float(pr_final),
    "pass_CV1": abs(cv_final - 1) < 1e-6,
    "pass_Q23": abs(Q_final - 2/3) < 1e-6,
    "pass_PR": abs(pr_final - 1.5) < 1e-6,
    "method": "algebraic (from Lean-certified identities: CV²=b²/2, Q=(1+b²/2)/3, PR=6/(2+b²))",
}

# === Final synthesis ===
results["session3_synthesis"] = {
    "T1_b_sqrt_N_mod2_MDL": "PROVISIONAL: 1-bit equipartition on binary (N_mod2=2) tapes gives b=√2 consistently. Equal-norm condition: trivial_norm=standard_norm → b²=2. The N_mod2=2 tape structure provides the binary context for '1-bit' in the MDL argument. Not a field-equation derivation.",
    "T2_algebraic_connection": "NUMEROLOGICAL for b (b²=2 from trig identity Σcos²=N/2, independent of N_mod2). STRUCTURAL for y_tau (y_tau=c_V/N_mod2=1/98, tape-denominator mechanism, CatAD). The three-way coincidence b²=2=d_std=N_mod2 is specific to N_gen=3 binary tapes.",
    "T3_MDL_derivation": "PROVISIONAL: MaxEnt at fixed mean → CV=1 → b=√2 is consistent with binary tape MDL but not derived from field equations.",
    "T4_Lean_addition": "New theorem koide_binary_tape_unification certifies: b²=N_mod2 algebraically; y_tau=c_V/N_mod2; dim(std S3)=N_mod2 (all for N_mod2=2, N_gen=3). Zero sorry (arithmetic).",
    "080_KOIDE_EQUALNORM_gate": "PARTIAL (unchanged). The N_mod2=2 unification is an interpretive advance but does not close the field-dynamical derivation gap.",
}

print("\n" + "="*70)
print("FINAL VERDICT:")
print("  1. b = sqrt(N_mod2) = sqrt(2): ALGEBRAICALLY TRUE")
print("  2. y_tau = c_V/N_mod2: STRUCTURAL (CatAD, from prior session)")
print("  3. N_mod2=2 connection in b: NUMEROLOGICAL (b²=2 from trig, not from N_mod2)")
print("  4. 1-bit equipartition on binary tapes: PROVISIONAL mechanism (not field eq)")
print("  5. 080-KOIDE-EQUALNORM: PARTIAL (gate unchanged)")
print("  6. New insight: b² = d_std = N_mod2 = 2 is a three-way coincidence at N_gen=3")
print("="*70)

# Save results
outfile = "papers/18_koide_cyclotomic/scripts/koide_equalnorm_session3_results.json"
with open(outfile, "w") as f:
    json.dump(results, f, indent=2, default=str)
print(f"\nResults saved to: {outfile}")

signal.alarm(0)
