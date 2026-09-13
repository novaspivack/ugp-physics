"""
G46: Hawking Kink Emission Near the Critical Black Hole Mass
============================================================

Computes the Hawking thermal emission rate for Z7-topological kinks (BPS solitons
of the Phi_MDL sine-Gordon potential) as a function of M_BH / M_crit.

Key parameters:
  m_kink = 8*m_tau/49 = 290.10 MeV   (BPS kink mass from SG kink formula)
  m_tau  = 1776.86 MeV                (Phi_MDL field mass)
  M_crit = M_Pl^2/(8*pi*m_tau) = 3.34e39 MeV  (T_H = m_tau threshold)
  M_kink_crit = M_Pl^2/(8*pi*m_kink) = (49/8)*M_crit  (T_H = m_kink threshold)

At M_crit: T_H = m_tau, so m_kink/T_H = 8/49 ~ 0.163 (kinks abundantly produced).
At M_kink_crit: T_H = m_kink (kink threshold; thermal factor = 1/(e-1) ~ 0.582).

Output: data/hawking_kink_emission_results.json

Source: EPIC_080 G46.
Claim level: CatA (numerical); CatAD (analytic threshold identities).
"""

import signal
import sys
import math
import json

TIMEOUT_SECONDS = 120


def _timeout_handler(signum, frame):
    print(f"\nTIMEOUT: wall-clock limit {TIMEOUT_SECONDS}s reached.")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)


def sec(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


# ─────────────────────────────────────────────────────────────────────────────
# Physical constants
# ─────────────────────────────────────────────────────────────────────────────

M_Pl_MeV = 1.22090e22    # Planck mass in MeV
m_tau_MeV = 1776.86      # tau mass / Phi_MDL field mass in MeV

# BPS kink mass: sine-Gordon V = (m^2/beta^2)(1-cos(beta*phi))
# For V_MDL = (m_tau^2/49)(1-cos(7*Phi)): beta=7, m=m_tau
# Kink mass M_kink = 8*m/beta^2 = 8*m_tau/49
m_kink_MeV = (8.0 / 49.0) * m_tau_MeV   # = 290.10 MeV


# ─────────────────────────────────────────────────────────────────────────────
# T1: Verify M_crit and compute kink emission threshold
# ─────────────────────────────────────────────────────────────────────────────

sec("T1: Critical masses and kink BPS formula")

# M_crit where T_H = m_tau (established in P38/P44)
M_crit_MeV = M_Pl_MeV**2 / (8.0 * math.pi * m_tau_MeV)

# M_kink_crit where T_H = m_kink (kink-specific threshold)
M_kink_crit_MeV = M_Pl_MeV**2 / (8.0 * math.pi * m_kink_MeV)

# Hawking temperature at M_crit
T_H_at_Mcrit = M_Pl_MeV**2 / (8.0 * math.pi * M_crit_MeV)
# This equals m_tau by construction

# Check T_H = m_tau at M_crit
T_H_equals_m_tau = abs(T_H_at_Mcrit - m_tau_MeV) / m_tau_MeV < 1e-10

print(f"  m_tau       = {m_tau_MeV:.4f} MeV")
print(f"  m_kink      = (8/49)*m_tau = {m_kink_MeV:.4f} MeV")
print(f"  m_kink / m_tau = 8/49 = {m_kink_MeV/m_tau_MeV:.6f}  (exact: {8/49:.6f})")
print()
print(f"  M_Pl        = {M_Pl_MeV:.4e} MeV")
print(f"  M_crit      = M_Pl^2/(8*pi*m_tau) = {M_crit_MeV:.4e} MeV")
print(f"  T_H(M_crit) = {T_H_at_Mcrit:.4f} MeV  [should = m_tau = {m_tau_MeV:.4f}]")
print(f"  Check T_H(M_crit) = m_tau: {T_H_equals_m_tau}")
print()
print(f"  M_kink_crit = M_Pl^2/(8*pi*m_kink) = {M_kink_crit_MeV:.4e} MeV")
print(f"  M_kink_crit / M_crit = 49/8 = {M_kink_crit_MeV/M_crit_MeV:.4f}  (exact: {49/8:.4f})")
print()
print(f"  HIERARCHY: M_crit < M_kink_crit: {M_crit_MeV:.3e} < {M_kink_crit_MeV:.3e} MeV")
print(f"  At M_crit: T_H = m_tau >> m_kink  (kinks ABUNDANTLY produced)")
print(f"  At M_kink_crit = (49/8)*M_crit: T_H = m_kink  (kink threshold)")


# ─────────────────────────────────────────────────────────────────────────────
# T2: Thermal emission factor at key masses
# ─────────────────────────────────────────────────────────────────────────────

sec("T2: Thermal emission factors at key masses")

def T_H(M_BH_MeV):
    """Hawking temperature T_H = M_Pl^2 / (8*pi*M_BH) in MeV."""
    return M_Pl_MeV**2 / (8.0 * math.pi * M_BH_MeV)


def planck_factor(m_MeV, T_MeV):
    """
    Planck factor for massive species: 1/(exp(m/T) - 1).
    Returns 0 for extreme Boltzmann suppression (m/T > 700).
    """
    ratio = m_MeV / T_MeV
    if ratio > 700:
        return 0.0
    return 1.0 / (math.exp(ratio) - 1.0)


def boltzmann_factor(m_MeV, T_MeV):
    """Boltzmann suppression exp(-m/T) for m/T >> 1."""
    ratio = m_MeV / T_MeV
    if ratio > 700:
        return 0.0
    return math.exp(-ratio)


# At M_crit: T_H = m_tau
ratio_at_Mcrit = m_kink_MeV / T_H(M_crit_MeV)
factor_at_Mcrit = planck_factor(m_kink_MeV, T_H(M_crit_MeV))

print(f"  AT M_crit (T_H = m_tau = {m_tau_MeV:.2f} MeV):")
print(f"    m_kink/T_H = {ratio_at_Mcrit:.6f}  (= 8/49 = {8/49:.6f})")
print(f"    Planck factor 1/(exp(m_kink/T_H)-1) = {factor_at_Mcrit:.4f}")
print(f"    => kinks emitted at {factor_at_Mcrit:.1%} above Bose-Einstein maximum")
print()

# At M_kink_crit: T_H = m_kink (the kink threshold)
ratio_at_kink_crit = m_kink_MeV / T_H(M_kink_crit_MeV)
factor_at_kink_crit = planck_factor(m_kink_MeV, T_H(M_kink_crit_MeV))
reference_e_minus_1 = 1.0 / (math.e - 1.0)

print(f"  AT M_kink_crit = (49/8)*M_crit (T_H = m_kink = {m_kink_MeV:.2f} MeV):")
print(f"    m_kink/T_H = {ratio_at_kink_crit:.6f}  (exact: 1.0)")
print(f"    Planck factor 1/(exp(1)-1) = {factor_at_kink_crit:.4f}  [exact: {reference_e_minus_1:.4f}]")
print()

# At 0.5*M_crit (hot regime)
M_half = 0.5 * M_crit_MeV
ratio_half = m_kink_MeV / T_H(M_half)
factor_half = planck_factor(m_kink_MeV, T_H(M_half))
print(f"  AT 0.5*M_crit: T_H = {T_H(M_half):.2f} MeV, m_kink/T_H = {ratio_half:.4f}, factor = {factor_half:.4f}")

# At 10*M_kink_crit (cold regime)
M_cold = 10 * M_kink_crit_MeV
ratio_cold = m_kink_MeV / T_H(M_cold)
factor_cold = boltzmann_factor(m_kink_MeV, T_H(M_cold))
print(f"  AT 10*M_kink_crit: T_H = {T_H(M_cold):.3f} MeV, m_kink/T_H = {ratio_cold:.2f}, Boltzmann = {factor_cold:.2e}")


# ─────────────────────────────────────────────────────────────────────────────
# T3: Emission rate profile M/M_crit from 0.1 to 20
# ─────────────────────────────────────────────────────────────────────────────

sec("T3: Emission rate profile vs M/M_crit (kink emission)")

# Grid of M/M_crit values
ratios = [0.1, 0.2, 0.5, 0.8, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 6.125, 7.0, 8.0, 10.0, 15.0, 20.0]

profile = []
print(f"  {'M/M_crit':>10}  {'T_H (MeV)':>12}  {'m_k/T_H':>10}  {'Planck factor':>14}  {'Regime':>15}")
print(f"  {'-'*10}  {'-'*12}  {'-'*10}  {'-'*14}  {'-'*15}")

for r in ratios:
    M_BH = r * M_crit_MeV
    T = T_H(M_BH)
    x = m_kink_MeV / T  # m_kink / T_H
    if x > 700:
        pf = 0.0
        regime = "Boltzmann-suppressed"
    elif x < 1:
        pf = planck_factor(m_kink_MeV, T)
        regime = "Bose-enhanced"
    elif abs(x - 1.0) < 0.05:
        pf = planck_factor(m_kink_MeV, T)
        regime = "at threshold"
    else:
        pf = planck_factor(m_kink_MeV, T)
        regime = "suppressed"
    profile.append({
        "M_over_Mcrit": r,
        "M_BH_MeV": M_BH,
        "T_H_MeV": T,
        "m_kink_over_T_H": x,
        "planck_factor": pf,
        "regime": regime,
    })
    print(f"  {r:>10.3f}  {T:>12.2f}  {x:>10.4f}  {pf:>14.4f}  {regime:>15}")


# ─────────────────────────────────────────────────────────────────────────────
# T4: Evaporation endpoint analysis
# ─────────────────────────────────────────────────────────────────────────────

sec("T4: Evaporation endpoint — does it terminate at M_kink_crit?")

print("""
  Evaporation physics:

  For M_BH >> M_kink_crit:
    T_H << m_kink  =>  kink emission suppressed as exp(-m_kink/T_H)
    BH evaporates via massless/ultralight species (photons, gravitons)

  For M_BH ~ M_kink_crit:
    T_H ~ m_kink  =>  kink emission thermal (Planck factor ~ 1/(e-1))
    BH begins emitting kinks; loses mass faster than via massless species only

  For M_crit < M_BH < M_kink_crit:
    T_H between m_kink and m_tau
    Kinks emitted (T_H > m_kink); tau-scale field still suppressed (T_H < m_tau)
    Bose-enhanced kink emission (m_kink/T_H < 1)

  For M_BH < M_crit:
    T_H > m_tau > m_kink
    Both Phi_MDL and kinks freely emitted; rapid evaporation
    No stable remnant from kink physics alone

  STABLE REMNANT QUESTION:
  Whether the kink BPS structure creates a stable remnant at M_BH ~ M_kink is
  NOT settled by the Hawking calculation alone.  The BPS bound gives a lower
  limit on the kink mass but NOT on the black hole mass.  The Z7 superselection
  rule could in principle forbid final evaporation below a minimum mass, but
  this requires non-perturbative analysis (open — G46 partially addresses it).

  KEY CONCLUSION: No termination of evaporation at M_kink_crit is forced by
  the Hawking thermal argument.  Evaporation continues smoothly through
  M_kink_crit via massless species, with kink emission becoming thermally
  accessible below M_kink_crit.
""")

# Rate comparison at M_kink_crit: kink vs massless
T_at_kink_threshold = T_H(M_kink_crit_MeV)
kink_factor_at_threshold = planck_factor(m_kink_MeV, T_at_kink_threshold)
massless_factor = 2.404  # Riemann zeta(3) ~ number density for massless boson (in units T^3)

print(f"  At M_kink_crit = {M_kink_crit_MeV:.3e} MeV:")
print(f"    T_H = m_kink = {T_at_kink_threshold:.2f} MeV")
print(f"    Kink Planck factor: {kink_factor_at_threshold:.4f}")
print(f"    Massless Planck factor at omega=T: 1/(e-1) = {1/(math.e-1):.4f}")
print(f"    Kink / massless ratio (at threshold energy): {kink_factor_at_threshold/(1/(math.e-1)):.4f}")
print(f"    => Kinks contribute comparably to massless at threshold")


# ─────────────────────────────────────────────────────────────────────────────
# T5: Analytic m_kink / T_H ratio as function of M/M_crit
# ─────────────────────────────────────────────────────────────────────────────

sec("T5: Analytic identity — m_kink/T_H as function of M/M_crit")

print("""
  ANALYTIC DERIVATION:

  m_kink/T_H(M) = m_kink / [M_Pl^2/(8*pi*M)]
               = 8*pi*m_kink*M / M_Pl^2
               = (m_kink/m_tau) * (8*pi*m_tau*M/M_Pl^2)
               = (8/49) * (M / M_crit)

  because M_crit = M_Pl^2/(8*pi*m_tau)  =>  8*pi*m_tau/M_Pl^2 = 1/M_crit

  RESULT: m_kink/T_H(M) = (8/49) * (M/M_crit)

  The kink emission threshold (m_kink/T_H = 1) occurs at:
    M_kink_crit = (49/8) * M_crit = 6.125 * M_crit

  At M = M_crit: m_kink/T_H = 8/49 = 0.1633
  At M = M_kink_crit: m_kink/T_H = 1.000  (threshold)
  At M = 10*M_crit: m_kink/T_H = 80/49 = 1.633  (suppressed)
  At M = 100*M_crit: m_kink/T_H = 800/49 = 16.33  (strongly suppressed)
""")

# Verify the analytic identity numerically
print("  Numerical verification of m_kink/T_H = (8/49)*(M/M_crit):")
for r in [0.5, 1.0, 2.0, 6.125, 10.0, 100.0]:
    M_BH = r * M_crit_MeV
    T = T_H(M_BH)
    x_numerical = m_kink_MeV / T
    x_analytic = (8.0 / 49.0) * r
    match = abs(x_numerical - x_analytic) / max(x_analytic, 1e-15) < 1e-8
    print(f"    M/M_crit = {r:>6.3f}: numerical = {x_numerical:.6f}, analytic = {x_analytic:.6f}, match = {match}")


# ─────────────────────────────────────────────────────────────────────────────
# T6: Summary
# ─────────────────────────────────────────────────────────────────────────────

sec("T6: Summary of G46 results")

# Exact values
x_at_Mcrit = 8.0 / 49.0
pf_at_Mcrit = 1.0 / (math.exp(x_at_Mcrit) - 1.0)
x_at_kink_crit = 1.0
pf_at_kink_crit = 1.0 / (math.e - 1.0)

print(f"""
  G46 SUMMARY — Hawking Kink Emission Near M_crit

  NOTATION:
    M_crit     = M_Pl^2/(8*pi*m_tau) = {M_crit_MeV:.3e} MeV  (T_H = m_tau; CatA, P38/P44)
    M_kink_crit = M_Pl^2/(8*pi*m_kink) = (49/8)*M_crit = {M_kink_crit_MeV:.3e} MeV  (T_H = m_kink)
    m_kink     = (8/49)*m_tau = {m_kink_MeV:.4f} MeV  (BPS sine-Gordon kink; CatAD)

  ANALYTIC IDENTITY (CatAD):
    m_kink/T_H(M) = (8/49) * (M/M_crit)
    => kink threshold at M_kink_crit = (49/8)*M_crit = 6.125*M_crit

  THERMAL EMISSION FACTORS:
    At M_crit (T_H = m_tau):  m_kink/T_H = 8/49 = {x_at_Mcrit:.4f}
      Planck factor = 1/(exp(8/49)-1) = {pf_at_Mcrit:.4f}
      => kinks ABUNDANTLY produced (factor > 5; Bose-enhanced)

    At M_kink_crit (T_H = m_kink):  m_kink/T_H = 1.000
      Planck factor = 1/(e-1) = {pf_at_kink_crit:.4f}  [threshold]
      => kinks at thermal threshold

    At M = 10*M_crit (T_H = m_tau/10):  m_kink/T_H = 80/49 = {80/49:.4f}
      Boltzmann factor = exp(-80/49) = {math.exp(-80/49):.4f}
      => kink emission significantly suppressed

    At M = 100*M_crit (T_H = m_tau/100):  m_kink/T_H = 800/49 = {800/49:.4f}
      Boltzmann factor = exp(-{800/49:.2f}) = {math.exp(-800/49):.2e}
      => kink emission negligible

  EVAPORATION ENDPOINT (CatD — open):
    No termination at M_kink_crit from the Hawking thermal argument alone.
    Evaporation continues via massless species through M_kink_crit.
    Z7 superselection may impose non-perturbative constraints; open question.

  CLAIM LEVEL:
    CatAD: T_H = m_tau at M_crit (near-horizon screening; P38/P44)
    CatAD: m_kink = (8/49)*m_tau (BPS sine-Gordon formula; CatAD)
    CatAD: m_kink/T_H = (8/49)*(M/M_crit) (analytic identity)
    CatAD: M_kink_crit = (49/8)*M_crit (derived from above)
    CatA:  Planck factors at key masses (numerical; this script)
    CatD:  Evaporation endpoint / stable remnant (open)
""")


# ─────────────────────────────────────────────────────────────────────────────
# Save results
# ─────────────────────────────────────────────────────────────────────────────

sec("Saving results to JSON")

results = {
    "description": "G46: Hawking kink emission near M_crit — threshold analysis",
    "epic": "epic_080",
    "rank": "080-G46",
    "claim_level": "CatAD (analytic), CatA (numerical)",
    "parameters": {
        "m_tau_MeV": m_tau_MeV,
        "m_kink_MeV": round(m_kink_MeV, 4),
        "m_kink_over_m_tau_exact": "8/49",
        "M_Pl_MeV": M_Pl_MeV,
        "M_crit_MeV": round(M_crit_MeV, 4),
        "M_kink_crit_MeV": round(M_kink_crit_MeV, 4),
        "M_kink_crit_over_M_crit_exact": "49/8",
        "T_H_at_Mcrit_MeV": round(T_H_at_Mcrit, 4),
        "T_H_equals_m_tau_at_Mcrit": T_H_equals_m_tau,
    },
    "analytic_identity": {
        "formula": "m_kink / T_H(M) = (8/49) * (M / M_crit)",
        "kink_threshold_mass": "M_kink_crit = (49/8) * M_crit = 6.125 * M_crit",
    },
    "thermal_factors": {
        "at_Mcrit": {
            "M_over_Mcrit": 1.0,
            "T_H_MeV": round(T_H_at_Mcrit, 4),
            "m_kink_over_T_H": round(x_at_Mcrit, 6),
            "m_kink_over_T_H_exact": "8/49",
            "planck_factor": round(pf_at_Mcrit, 6),
            "regime": "Bose-enhanced (m_kink < T_H)",
        },
        "at_M_kink_crit": {
            "M_over_Mcrit": 49.0 / 8.0,
            "T_H_MeV": round(m_kink_MeV, 4),
            "m_kink_over_T_H": 1.0,
            "planck_factor": round(pf_at_kink_crit, 6),
            "regime": "at kink threshold",
        },
        "at_10_Mcrit": {
            "M_over_Mcrit": 10.0,
            "m_kink_over_T_H": round(80.0 / 49.0, 6),
            "m_kink_over_T_H_exact": "80/49",
            "boltzmann_factor": round(math.exp(-80.0 / 49.0), 6),
            "regime": "suppressed",
        },
    },
    "emission_profile": profile,
    "evaporation_endpoint": {
        "terminates_at_M_kink_crit": False,
        "reason": (
            "Hawking thermal argument shows no forced termination at M_kink_crit. "
            "Evaporation via massless species continues through the kink threshold. "
            "Z7 superselection / non-perturbative constraints: open (G46 CatD residual)."
        ),
    },
    "board_update": {
        "G46_status": "PARTIAL CatAD",
        "closed": [
            "T_H unmodified by m_kink (near-horizon screening): CatAD",
            "Kink BPS mass m_kink = (8/49)*m_tau: CatAD",
            "Analytic identity m_kink/T_H = (8/49)*(M/M_crit): CatAD",
            "Kink emission threshold M_kink_crit = (49/8)*M_crit: CatAD",
            "Planck factors computed at all key masses: CatA",
        ],
        "open": [
            "Evaporation endpoint / stable remnant at M_kink_crit: CatD",
            "Z7 superselection in non-perturbative kink regime: CatD",
        ],
    },
}

import os
out_dir = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "hawking_kink_emission_results.json")
with open(out_path, "w") as f:
    json.dump(results, f, indent=2)

print(f"  Saved: {out_path}")

signal.alarm(0)
print("\nSCRIPT COMPLETE — hawking_kink_emission.py")
