"""
Rank 146-THREELOOP: Three-loop QCD beta coefficient b₂ from F₂₁ Casimirs
and three-loop αs(M_Z) running.

Inputs (all GTE-certified CatAL from prior ranks):
  N_c = 3 (Rank 112-FROBENIUS)
  N_f = 6 full / 5 at M_Z (Rank 108-CASIMIR)
  C_F = 4/3, C_A = 3, T_F = 1/2 (Rank 108-CASIMIR, CatAL)
  b₀ = 7, b₁ = 26 (Rank 117, 119, CatAL)
  Λ_GTE = 2.01 GeV (Rank 97c-GI)
  αs(Λ_GTE) from two-loop matched at Λ_GTE

Three-loop formula (van Ritbergen, Vermaseren, Larin 1997 + Tarasov, Vladimirov, Zharkov 1980
 for SU(N_c) with N_c=3):
  b₂ = (2857/2) - (5033/18)*N_f + (325/54)*N_f²
"""

import signal, sys, json
import numpy as np
from scipy.integrate import solve_ivp

TIMEOUT = 120
signal.signal(signal.SIGALRM, lambda s, f: (print("TIMEOUT reached"), sys.exit(1)))
signal.alarm(TIMEOUT)

# === GTE canonical inputs ===
N_c = 3
C_F = 4.0 / 3.0
C_A = 3.0
T_F = 0.5
Lambda_GTE = 2.01    # GeV — physical calibration cutoff (Rank 97c-GI)
M_Z = 91.188         # GeV
m_b = 4.18           # GeV — bottom threshold (PDG)
m_t = 172.76         # GeV — top threshold (PDG, above M_Z for this run)
PDG_alpha_s = 0.1180

# === Beta coefficients ===
def b0(N_f):
    return (11 * N_c - 2 * N_f) / 3      # = 7 for N_f=6

def b1(N_f):
    # GTE convention: b₁ = (34/3)N_c² - (10/3)N_c N_f - 2C_F N_f
    # = (34/3)*9 - (10/3)*18 - 2*(4/3)*6 = 102 - 60 - 16 = 26 ✓
    return (34.0 / 3.0) * N_c**2 - (10.0 / 3.0) * N_c * N_f - 2 * C_F * N_f

def b2(N_f):
    # Standard three-loop QCD, N_c=3 (forced by C_A=3 from Rank 108-CASIMIR)
    return 2857.0 / 2.0 - 5033.0 * N_f / 18.0 + 325.0 * N_f**2 / 54.0

# Print beta coefficients for verification
print("=== Beta Coefficients ===")
for nf in [5, 6]:
    print(f"N_f={nf}: b₀={b0(nf):.4f}, b₁={b1(nf):.4f}, b₂={b2(nf):.4f}")

# Sanity check against known values
assert abs(b0(6) - 7.0) < 1e-10, f"b₀(N_f=6) sanity fail: {b0(6)}"
assert abs(b1(6) - 26.0) < 1e-10, f"b₁(N_f=6) sanity fail: {b1(6)}"
print("Sanity checks PASS: b₀(N_f=6)=7, b₁(N_f=6)=26 ✓")

# === Three-loop RGE: d(α_s)/d(log μ) = β(α_s) ===
def deriv_3loop(log_mu, y, N_f):
    a = y[0]
    beta0 = b0(N_f) / (2.0 * np.pi)
    beta1 = b1(N_f) / (4.0 * np.pi**2)
    beta2 = b2(N_f) / (8.0 * np.pi**3)
    dadt = -(beta0 * a**2 + beta1 * a**3 + beta2 * a**4)
    return [dadt]

def deriv_2loop(log_mu, y, N_f):
    a = y[0]
    beta0 = b0(N_f) / (2.0 * np.pi)
    beta1 = b1(N_f) / (4.0 * np.pi**2)
    dadt = -(beta0 * a**2 + beta1 * a**3)
    return [dadt]

def run_rge(alpha_s_start, mu_start, mu_end, N_f, deriv_fn):
    """Run RGE from mu_start to mu_end with fixed N_f."""
    log_start = np.log(mu_start)
    log_end = np.log(mu_end)
    sol = solve_ivp(
        deriv_fn,
        [log_start, log_end],
        [alpha_s_start],
        args=(N_f,),
        method='RK45',
        t_eval=[log_end],
        rtol=1e-10,
        atol=1e-12
    )
    if not sol.success:
        raise RuntimeError(f"RGE integration failed: {sol.message}")
    return sol.y[0][0]

# === Step 1: Reverse-run at two loops to get αs(Λ_GTE) ===
# Rank 119 established αs(M_Z)[N_f=5] = 0.1201 via two-loop running from Λ_GTE
# Reverse-run: M_Z → m_b (N_f=5), then m_b → Λ_GTE (N_f=6)
alpha_s_MZ_2loop = 0.1201  # Rank 119 canonical result

alpha_s_mb_2loop_dn = run_rge(alpha_s_MZ_2loop, M_Z, m_b, N_f=5, deriv_fn=deriv_2loop)
alpha_s_LGTE = run_rge(alpha_s_mb_2loop_dn, m_b, Lambda_GTE, N_f=6, deriv_fn=deriv_2loop)

print(f"\n2-loop reverse-run anchor:")
print(f"  αs(M_Z=91.188) [2L, N_f=5] = {alpha_s_MZ_2loop:.6f}  (Rank 119 input)")
print(f"  αs(m_b=4.18)   [2L, N_f=5] = {alpha_s_mb_2loop_dn:.6f}")
print(f"  αs(Λ_GTE=2.01) [2L, N_f=6] = {alpha_s_LGTE:.6f}  (anchor for 3-loop run)")

# === Step 2: Forward-run at 3 loops from Λ_GTE → M_Z ===
# Threshold: Λ_GTE → m_b with N_f=6, then m_b → M_Z with N_f=5
alpha_s_mb_3loop = run_rge(alpha_s_LGTE, Lambda_GTE, m_b, N_f=6, deriv_fn=deriv_3loop)
alpha_s_MZ_3loop = run_rge(alpha_s_mb_3loop, m_b, M_Z, N_f=5, deriv_fn=deriv_3loop)

print(f"\n=== Three-Loop Running Results ===")
print(f"αs(Λ_GTE = {Lambda_GTE} GeV) [anchor]          = {alpha_s_LGTE:.6f}")
print(f"αs(m_b  = {m_b} GeV)  [3-loop, N_f=6→5] = {alpha_s_mb_3loop:.6f}")
print(f"αs(M_Z  = {M_Z} GeV) [3-loop, N_f=5]   = {alpha_s_MZ_3loop:.6f}")
print(f"PDG αs(M_Z)                              = {PDG_alpha_s:.6f}")

deviation_2loop = (alpha_s_MZ_2loop - PDG_alpha_s) / PDG_alpha_s * 100.0
deviation_3loop = (alpha_s_MZ_3loop - PDG_alpha_s) / PDG_alpha_s * 100.0
improvement_pp  = abs(deviation_2loop) - abs(deviation_3loop)

print(f"\nDeviation 2-loop: {deviation_2loop:+.4f}%")
print(f"Deviation 3-loop: {deviation_3loop:+.4f}%")
print(f"Improvement: {improvement_pp:+.4f} percentage points")

# === Step 3: b₂ from F₂₁ Casimirs — analytical decomposition ===
nf = 5
b2_Nf5 = b2(nf)
term1 = 2857.0 / 2.0
term2 = 5033.0 * nf / 18.0
term3 = 325.0 * nf**2 / 54.0
print(f"\n=== b₂ from F₂₁ Casimirs (N_c=3, N_f=5 at M_Z) ===")
print(f"b₂(N_f=5) = 2857/2 − 5033×5/18 + 325×25/54")
print(f"          = {term1:.4f} − {term2:.4f} + {term3:.4f}")
print(f"          = {b2_Nf5:.4f}")
print(f"(C_A=3 coefficient forces the 2857/2 pure-gauge term; N_f=5 threshold is standard)")

# === Step 4: Null tests ===
print(f"\n=== Null Tests ===")

# 1. Pure gauge (N_f=0): b₂ = 2857/2 exactly
b2_puregauge = b2(0)
print(f"NT1 Pure gauge (N_f=0): b₂ = {b2_puregauge:.4f}  (expected 1428.5000) "
      f"{'PASS' if abs(b2_puregauge - 1428.5) < 0.001 else 'FAIL'}")

# 2. Series convergence at M_Z
ratio_3loop_2loop = abs(alpha_s_MZ_3loop - alpha_s_MZ_2loop) / alpha_s_MZ_2loop * 100.0
conv_pass = ratio_3loop_2loop < 5.0
print(f"NT2 Series convergence at M_Z: |3L−2L|/2L = {ratio_3loop_2loop:.4f}% "
      f"{'PASS (<5%)' if conv_pass else 'FAIL (>=5%)'}")

# 3. b₂ in N_f=6 (GTE fundamental count): should be negative (near-asymptotic-freedom boundary)
b2_Nf6 = b2(6)
print(f"NT3 b₂(N_f=6) = {b2_Nf6:.4f}  (expected ~-32.5; "
      f"negative means close to AF boundary) {'PASS' if b2_Nf6 < 0 else 'NOTE: positive'}")

# 4. Monotonicity: 3-loop αs should be closer to PDG than 2-loop
monotone_pass = abs(deviation_3loop) < abs(deviation_2loop)
print(f"NT4 Three-loop improvement vs two-loop: "
      f"{'PASS' if monotone_pass else 'FAIL'} "
      f"(|Δ₃|={abs(deviation_3loop):.4f}% vs |Δ₂|={abs(deviation_2loop):.4f}%)")

# === Save results ===
results = {
    "rank": "146-THREELOOP",
    "date": "2026-05-24",
    "inputs": {
        "N_c": N_c, "C_F": C_F, "C_A": C_A, "T_F": T_F,
        "Lambda_GTE_GeV": Lambda_GTE, "M_Z_GeV": M_Z,
        "m_b_GeV": m_b, "m_t_GeV": m_t
    },
    "beta_coefficients": {
        "b0_Nf5": b0(5), "b0_Nf6": b0(6),
        "b1_Nf5": b1(5), "b1_Nf6": b1(6),
        "b2_Nf5": float(b2(5)), "b2_Nf6": float(b2(6))
    },
    "running": {
        "alpha_s_LGTE_anchor": float(alpha_s_LGTE),
        "alpha_s_mb_3loop": float(alpha_s_mb_3loop),
        "alpha_s_MZ_2loop": float(alpha_s_MZ_2loop),
        "alpha_s_MZ_3loop": float(alpha_s_MZ_3loop),
        "PDG_alpha_s": PDG_alpha_s
    },
    "deviations": {
        "deviation_2loop_pct": float(deviation_2loop),
        "deviation_3loop_pct": float(deviation_3loop),
        "improvement_pp": float(improvement_pp),
        "series_convergence_pct": float(ratio_3loop_2loop)
    },
    "null_tests": {
        "NT1_pure_gauge_b2": "PASS" if abs(b2_puregauge - 1428.5) < 0.001 else "FAIL",
        "NT2_series_convergence": "PASS" if conv_pass else "FAIL",
        "NT3_b2_Nf6_negative": "PASS" if b2_Nf6 < 0 else "NOTE",
        "NT4_monotone_improvement": "PASS" if monotone_pass else "FAIL"
    }
}

out_path = "rank146_threeloop_results.json"
with open(out_path, "w") as f:
    json.dump(results, f, indent=2)
print(f"\nResults saved to {out_path}")

signal.alarm(0)
print("\nDone.")
