#!/usr/bin/env python3
"""
comp_p01_EBF_05_mfrr_reflexive_landauer_bridge.py
EPIC 8 — E_base Foundations, Sub-project B, Computation 5

QUESTION:
    Can the MFRR (Mathematical Foundations of Reflexive Reality) framework —
    specifically the Reflexive Landauer Bound and Information Profit Threshold —
    provide a first-principles derivation of the E_base inter-generational
    mass hierarchy?

MFRR KEY CONSTANTS:
    Λ = ln(φ) / ln(2π)   — universal reflexive coupling constant (Norfleet)
    IPT = 1 + Λ/2        — Information Profit Threshold ≈ 1.13
    φ = (1+√5)/2         — golden ratio

MFRR REFLEXIVE LANDAUER BOUND:
    ΔE_PT ≥ k_B T ln(n) + λ_Ψ E_Ψ
    where n = number of adjudicable states, λ_Ψ is a coupling constant

APPROACH:
    Map each GTE orbit (a, b, c, g) to MFRR information quantities and
    test all natural MFRR-motivated formulas for E_base.

    Candidates:
    (1) E ∝ exp(orbit_info / Λ)                  — Landauer-inverse scaling
    (2) E ∝ orbit_complexity^(1/Λ)              — power-law Landauer
    (3) E ∝ φ^(g × log(2π)/log(φ))              — IPT generation scaling
    (4) E ∝ |L|^(1/Λ)                            — L-feature Landauer
    (5) E ∝ N_eff^(1/(2π))                       — holographic Landauer
    (6) E ∝ exp(IPT × g)                         — IPT generation exponent
    (7) E ∝ (|b| × |c|)^Λ                       — orbit-area Landauer
    (8) E ∝ 2^(crossing_number/Λ)               — braid-crossing Landauer
    (9) E ∝ log(|abc|)/Λ                         — log orbit-volume
    (10) Check if required E_base ratios are close to powers of (2π)^(Λg)

    For each formula, compute inter-generational E_base ratios and compare
    to the required values from COMP-EBF-04.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
from datetime import datetime, timezone

# ─────────────────────────────────────────────────────────────────────────────
# MFRR constants
# ─────────────────────────────────────────────────────────────────────────────

PHI      = (1.0 + math.sqrt(5.0)) / 2.0       # golden ratio
LAMBDA_N = math.log(PHI) / math.log(2*math.pi) # Norfleet Λ = ln(φ)/ln(2π)
IPT      = 1.0 + LAMBDA_N / 2.0               # Information Profit Threshold
K_GEN    = PHI * math.cos(math.pi / 10.0)     # derived k_gen
K_GEN2   = -PHI / 2.0                         # derived k_gen2

print("=" * 72)
print("MFRR constants:")
print(f"  φ (golden ratio)               = {PHI:.8f}")
print(f"  Λ = ln(φ)/ln(2π) (Norfleet)   = {LAMBDA_N:.8f}")
print(f"  IPT = 1 + Λ/2                 = {IPT:.8f}")
print(f"  1/Λ                            = {1/LAMBDA_N:.8f}")
print(f"  k_gen (Pentagon-Lock)          = {K_GEN:.8f}")
print(f"  k_gen + k_gen2 = φ(cos10-cos60) = {K_GEN + K_GEN2:.8f}")
print(f"  Λ / log(φ)                     = {LAMBDA_N/math.log(PHI):.8f}  (= 1/log(2π))")
print()

# ─────────────────────────────────────────────────────────────────────────────
# Required E_base ratios (from COMP-EBF-04)
# ─────────────────────────────────────────────────────────────────────────────

# E_base_g = m_g / C_f_g  (from UCL2.3)
# These were computed in COMP-EBF-04
REQUIRED_Rg = {
    # name: R_g = E_base / E_base_electron
    "electron": 1.0000,
    "muon":     241.989,
    "tau":      14251.735,
    "up":       2.7228,
    "charm":    838.231,
    "top":      142517.612,
    "down":     4.6776,
    "strange":  229.322,
    "bottom":   22078.351,
}

# Lepton E_base ratios (the key hierarchy to explain)
R_mu_e  = REQUIRED_Rg["muon"]          # 241.989
R_tau_e = REQUIRED_Rg["tau"]           # 14251.735
R_tau_mu = R_tau_e / R_mu_e            # 58.894

print(f"Required E_base ratios (from COMP-EBF-04, UCL2.3):")
print(f"  E_mu/E_e   = {R_mu_e:.3f}   (m_mu/m_e = 206.77)")
print(f"  E_tau/E_mu = {R_tau_mu:.3f}   (m_tau/m_mu = 16.82)")
print(f"  E_tau/E_e  = {R_tau_e:.3f}")
print()

# ─────────────────────────────────────────────────────────────────────────────
# GTE orbit quantities for leptons
# ─────────────────────────────────────────────────────────────────────────────

# Canonical triples (|c| convention, UCL-consistent)
LEPTONS = [
    ("electron", 1,  1,   73,    823),
    ("muon",     2,  9,   42,   1023),
    ("tau",      3,  5,  275,  65535),
]

def mobius(n):
    n = abs(n)
    if n <= 1: return 1 if n == 1 else 0
    out = 1; p = 2
    while p*p <= n:
        if n % p == 0:
            cnt = 0
            while n % p == 0: n //= p; cnt += 1
            if cnt >= 2: return 0
            out = -out
        p += 1
    if n > 1: out = -out
    return out

# Compute orbit quantities
orbit_data = {}
for name, g, a, b, c in LEPTONS:
    abc = a * b * c
    bc  = b * c
    L   = math.log(b / c)  # negative for all leptons
    orbit_data[name] = {
        "g": g, "a": a, "b": b, "c": c,
        "crossing_number": g - 1,          # braid crossing number = gen - 1
        "abc": abc, "bc": bc,
        "log_abc": math.log(abc),
        "log_b":   math.log(b),
        "log_c":   math.log(c),
        "log2_c":  math.log2(c),
        "log2_cp1": math.log2(c+1),
        "L":       L,
        "L_abs":   abs(L),
        "L_sq":    L**2,
        "N_eff":   b,                      # standard N_eff
        "mobius":  mobius(a)*mobius(b)*mobius(c),
        # MFRR information quantities
        "I_log_c":     math.log(c) / LAMBDA_N,    # orbit info in units of Λ
        "I_log_abc":   math.log(abc) / LAMBDA_N,
        "I_Lsq":       L**2 / LAMBDA_N,
        "I_log_bc":    math.log(bc) / LAMBDA_N,
        # IPT-based
        "IPT_g":       IPT ** g,
        "IPT_2g":      IPT ** (2**g),
        "two_pi_Lambda_g": (2*math.pi)**( LAMBDA_N * g),
        "phi_over_Lambda_g": PHI ** (g / LAMBDA_N),
    }

# Print orbit quantities
print("=" * 72)
print("Orbit quantities for leptons:")
keys = ["g", "abc", "L", "L_sq", "log2_cp1", "I_log_c", "I_log_abc",
        "IPT_g", "two_pi_Lambda_g"]
print(f"  {'Quantity':25s}  {'electron':>12s}  {'muon':>12s}  {'tau':>12s}")
print("  " + "-" * 65)
for k in keys:
    e_v = orbit_data["electron"][k]
    m_v = orbit_data["muon"][k]
    t_v = orbit_data["tau"][k]
    print(f"  {k:25s}  {e_v:12.4f}  {m_v:12.4f}  {t_v:12.4f}")

# ─────────────────────────────────────────────────────────────────────────────
# Test MFRR formulas — compute predicted R_g ratios
# ─────────────────────────────────────────────────────────────────────────────

print()
print("=" * 72)
print("Testing MFRR-motivated formulas for E_base ratios:")
print(f"  Target: E_mu/E_e = {R_mu_e:.2f},  E_tau/E_mu = {R_tau_mu:.2f}")
print()

def test_formula(name, fn):
    """Compute E_base ∝ fn(orbit) and report ratios vs targets."""
    vals = {p: fn(orbit_data[p]) for p in ["electron","muon","tau"]}
    if vals["electron"] == 0: return
    r_mu_e  = vals["muon"] / vals["electron"]
    r_tau_mu = vals["tau"] / vals["muon"]
    dev_mu  = abs(r_mu_e - R_mu_e) / R_mu_e * 100
    dev_tau = abs(r_tau_mu - R_tau_mu) / R_tau_mu * 100
    max_dev = max(dev_mu, dev_tau)
    marker = " ✓" if max_dev < 10 else " ~" if max_dev < 50 else ""
    print(f"  {name:45s}: R21={r_mu_e:9.2f}({dev_mu:5.1f}%)  R32={r_tau_mu:9.2f}({dev_tau:5.1f}%){marker}")
    return max_dev, r_mu_e, r_tau_mu

# Formula bank
formulas = [
    # Standard orbit invariants
    ("N_eff = |b|",                   lambda d: d["b"]),
    ("orbit vol |abc|",               lambda d: d["abc"]),
    ("log|abc|",                      lambda d: d["log_abc"]),
    ("|L| = |log(b/c)|",              lambda d: d["L_abs"]),
    ("|L|^2",                         lambda d: d["L_sq"]),
    ("log|c|",                        lambda d: d["log_c"]),
    ("log2(c+1)",                     lambda d: d["log2_cp1"]),
    # MFRR Landauer: E ∝ exp(quantity / Λ)
    ("exp(log|c| / Λ) = |c|^(1/Λ)",  lambda d: d["c"] ** (1/LAMBDA_N)),
    ("exp(log|abc| / Λ)",             lambda d: math.exp(d["log_abc"] / LAMBDA_N)),
    ("exp(L^2 / Λ)",                  lambda d: math.exp(d["L_sq"] / LAMBDA_N)),
    # MFRR IPT generation scaling
    ("IPT^g",                         lambda d: IPT ** d["g"]),
    ("IPT^(2^g)",                     lambda d: IPT ** (2**d["g"])),
    ("(2π)^(Λ*g)",                   lambda d: (2*math.pi) ** (LAMBDA_N * d["g"])),
    ("φ^(g/Λ)",                       lambda d: PHI ** (d["g"] / LAMBDA_N)),
    ("2^(crossing/Λ)",                lambda d: 2 ** (d["crossing_number"] / LAMBDA_N)),
    ("exp(IPT * g)",                  lambda d: math.exp(IPT * d["g"])),
    # Combinations
    ("exp(L^2 * g / Λ)",              lambda d: math.exp(d["L_sq"] * d["g"] / LAMBDA_N)),
    ("|c|^(g*Λ)",                     lambda d: d["c"] ** (d["g"] * LAMBDA_N)),
    ("log|c| * g",                    lambda d: d["log_c"] * d["g"]),
    ("log2(c+1) * g",                 lambda d: d["log2_cp1"] * d["g"]),
    ("|abc|^(Λ)",                     lambda d: d["abc"] ** LAMBDA_N),
    ("|bc|^(Λ)",                      lambda d: d["bc"] ** LAMBDA_N),
    ("|L|^(1/Λ)",                     lambda d: d["L_abs"] ** (1/LAMBDA_N)),
    # Fibonacci-MFRR hybrids
    ("φ^(log2(c+1))",                 lambda d: PHI ** d["log2_cp1"]),
    ("φ^(L^2/π)",                     lambda d: PHI ** (d["L_sq"] / math.pi)),
    ("(2π)^(|L|)",                    lambda d: (2*math.pi) ** d["L_abs"]),
    ("(2π)^(L^2)",                    lambda d: (2*math.pi) ** d["L_sq"]),
    ("exp(|L| / Λ)",                  lambda d: math.exp(d["L_abs"] / LAMBDA_N)),
    # IPT-orbit product
    ("IPT^g * |c|^Λ",                lambda d: IPT**d["g"] * d["c"]**LAMBDA_N),
    ("log|c| / Λ",                    lambda d: d["log_c"] / LAMBDA_N),
    # Note: some formulas may overflow; handle via try/except
]

results = []
for fname, fn in formulas:
    try:
        r = test_formula(fname, fn)
        if r:
            results.append((fname, r[0], r[1], r[2]))
    except (OverflowError, ZeroDivisionError, ValueError):
        print(f"  {fname:45s}: OVERFLOW/ERROR")

# Sort by max_dev
results.sort(key=lambda x: x[1])

print()
print(f"  Best formulas (sorted by max deviation from targets):")
print(f"  {'Formula':45s}  {'R21':>9s}  {'Dev21%':>7s}  {'R32':>9s}  {'Dev32%':>7s}")
print("  " + "-" * 80)
for fname, max_dev, r21, r32 in results[:10]:
    dev21 = abs(r21 - R_mu_e) / R_mu_e * 100
    dev32 = abs(r32 - R_tau_mu) / R_tau_mu * 100
    print(f"  {fname:45s}  {r21:9.2f}  {dev21:7.1f}%  {r32:9.2f}  {dev32:7.1f}%")

# ─────────────────────────────────────────────────────────────────────────────
# Deep analysis: the anti-correlation problem
# ─────────────────────────────────────────────────────────────────────────────

print()
print("=" * 72)
print("DEEP ANALYSIS: The anti-correlation problem")
print("=" * 72)
print()
print("For ANY function f(triple) to give the correct E_base ratios:")
print(f"  f(muon)/f(electron) must = {R_mu_e:.1f}  [LARGE ratio]")
print(f"  f(tau)/f(muon)     must = {R_tau_mu:.1f}  [SMALL ratio]")
print()
print("But looking at how triple components change across generations:")
print()
for key in ["a", "b", "c", "abc", "L", "L_sq", "log2_cp1"]:
    e = orbit_data["electron"][key]
    m = orbit_data["muon"][key]
    t = orbit_data["tau"][key]
    if abs(e) > 1e-10 and abs(m) > 1e-10:
        ratio_me = m / e
        ratio_tm = t / m if abs(m) > 1e-10 else float('inf')
        print(f"  {key:12s}: e={e:10.3f}, mu={m:10.3f}, tau={t:10.3f}  "
              f"| mu/e={ratio_me:8.3f}  tau/mu={ratio_tm:8.3f}")

print()
print("  CRITICAL OBSERVATION:")
print("  - From e→μ: all orbit quantities change by MODEST amounts (factors 0.5-9)")
print("  - From μ→τ: c jumps by factor 64 (2^10→2^16); everything else modest")
print()
print("  Yet E_base ratios are: e→μ LARGE (×242), μ→τ MUCH SMALLER (×59)")
print("  This is ANTI-CORRELATED with the c-value jump.")
print()
print("  Any monotone function of orbit quantities will give:")
print("  - SMALL ratio for e→μ (orbit quantities change little)")
print("  - LARGE ratio for μ→τ (c jumps enormously)")
print("  This is the OPPOSITE of what we need.")
print()
print("  => No simple orbit-based formula can reproduce the lepton E_base hierarchy")
print("     because the hierarchy is ANTI-CORRELATED with ALL observable triple changes.")

# ─────────────────────────────────────────────────────────────────────────────
# Analysis: what WOULD be needed from MFRR
# ─────────────────────────────────────────────────────────────────────────────

print()
print("=" * 72)
print("THEORETICAL ANALYSIS: What the MFRR bridge would need to provide")
print("=" * 72)
print()
print("For the MFRR bridge to work, we need a quantity I_orbit(g) such that:")
print(f"  I_orbit(μ) - I_orbit(e) = Λ × log(E_mu/E_e) = {LAMBDA_N:.4f} × {math.log(R_mu_e):.4f} = {LAMBDA_N*math.log(R_mu_e):.4f} nats")
print(f"  I_orbit(τ) - I_orbit(μ) = Λ × log(E_tau/E_mu) = {LAMBDA_N:.4f} × {math.log(R_tau_mu):.4f} = {LAMBDA_N*math.log(R_tau_mu):.4f} nats")
print()
I_diff_me  = LAMBDA_N * math.log(R_mu_e)
I_diff_tau_mu = LAMBDA_N * math.log(R_tau_mu)
print(f"  Required I_diff (e→μ):  {I_diff_me:.4f} nats = {I_diff_me/math.log(2):.4f} bits")
print(f"  Required I_diff (μ→τ):  {I_diff_tau_mu:.4f} nats = {I_diff_tau_mu/math.log(2):.4f} bits")
print(f"  Ratio of increments: {I_diff_me/I_diff_tau_mu:.4f}  (e→μ is {I_diff_me/I_diff_tau_mu:.2f}× bigger than μ→τ)")
print()
print("  This quantity I_orbit must:")
print("  1. Increase by MORE from e→μ than from μ→τ  (despite the triple changing LESS)")
print("  2. Not be a simple function of (a,b,c)")
print("  3. Potentially encode CASCADE PATH information (not just terminal triple)")
print()
print("  POSSIBLE MFRR interpretation:")
print("  The 'information content' is the PATH entropy — not the terminal orbit entropy,")
print("  but the ACCUMULATED entropy over all g cascade steps leading to this particle.")
print()
print("  If each cascade STEP adds a fixed information increment Δ, then:")
print(f"  I_orbit(g) = Δ × (some function of g)")
print()

# What function of g gives the correct increments?
# log(E_g) ∝ Δ(g), so we need Δ(2) - Δ(1) >> Δ(3) - Δ(2)
log_E = {
    1: 0.0,
    2: math.log(R_mu_e),
    3: math.log(R_tau_e),
}
print("  log(E_g/E_e) for leptons:")
for g, v in log_E.items():
    print(f"    g={g}: log(R_g) = {v:.4f}")
print()
print("  Differences: Δ(2→1)={:.4f}  Δ(3→2)={:.4f}".format(
    log_E[2]-log_E[1], log_E[3]-log_E[2]))
print(f"  Ratio Δ21/Δ32 = {(log_E[2]-log_E[1])/(log_E[3]-log_E[2]):.4f}")
print()
print("  If log(E_g) = α × h(g), need h(2)-h(1) >> h(3)-h(2).")
print("  Candidate: h(g) = 2^g. Then h(2)-h(1)=2, h(3)-h(2)=4. Wrong direction.")
print("  Candidate: h(g) = g². Then h(2)-h(1)=3, h(3)-h(2)=5. Wrong direction.")
print("  Candidate: h(g) = f_g (Fibonacci). f1=1,f2=1,f3=2. Δ=0,1. Wrong.")
print()
print("  The ONLY simple function giving decreasing increments: h(g) = log(g).")
print("  h(2)-h(1) = log(2)=0.693, h(3)-h(2) = log(3/2)=0.405. Ratio=1.71 vs required",
      f"{(log_E[2]-log_E[1])/(log_E[3]-log_E[2]):.2f}")
print("  Wrong direction (ratio should be > 1, but value doesn't match).")
print()
print("  CONCLUSION: No simple function g→h(g) gives both increments simultaneously.")
print("  The mass hierarchy is NOT a simple generation-indexed function.")

# ─────────────────────────────────────────────────────────────────────────────
# Check the 13_SPEC TT formula: can it give E_base ratios?
# ─────────────────────────────────────────────────────────────────────────────

print()
print("=" * 72)
print("CHECK: Can 13_SPEC TT formula give E_base ratios via cross-sector route?")
print("=" * 72)
print()
print("TT formula: log(m_u_g / m_lep_g) = (π/6) * 2^g + β")
print("This gives cross-SECTOR ratios, not intra-sector hierarchy.")
print()
print("But: if log(m_u_g) ≈ (π/6)*2^g + log(m_lep_g) + β,")
print("then log(m_lep_g) ≈ log(m_u_g) - (π/6)*2^g - β")
print("=> log(m_lep_g+1) - log(m_lep_g) = [log(m_u_g+1) - log(m_u_g)] - π/6*(2^(g+1) - 2^g)")
print("                                  = [up-sector step] - π/6 * 2^g")
print()
print("Up-sector mass steps:")
m_up_sector = [2.16, 1275.0, 172760.0]
for i in range(2):
    step = math.log(m_up_sector[i+1]/m_up_sector[i])
    g = i+1
    tt_sub = math.pi/6 * 2**g
    lep_step = step - tt_sub
    print(f"  g={g}→{g+1}: log(m_u) step = {step:.4f},  π/6*2^g = {tt_sub:.4f},  predicted lep step = {lep_step:.4f}")

print()
m_lep = [0.511, 105.66, 1776.86]
for i in range(2):
    actual_step = math.log(m_lep[i+1]/m_lep[i])
    print(f"  Actual lepton step g={i+1}→{i+2}: {actual_step:.4f}")

print()
print("  The TT formula gives cross-sector ratios; to get lepton steps we need")
print("  to know the up-quark steps independently. Not a closed prediction.")

# ─────────────────────────────────────────────────────────────────────────────
# Verdict and JSON output
# ─────────────────────────────────────────────────────────────────────────────

print()
print("=" * 72)
print("VERDICT")
print("=" * 72)

best_formula = results[0] if results else ("None", 1e9, 0, 0)
best_max_dev = best_formula[1]

if best_max_dev < 10:
    verdict = f"STRUCTURAL HIT: '{best_formula[0]}' gives both ratios within 10%."
elif best_max_dev < 30:
    verdict = f"PARTIAL: '{best_formula[0]}' gives max dev {best_max_dev:.1f}% — suggestive."
else:
    verdict = (
        f"FAIL: No MFRR formula achieves < 30% on both lepton ratios. "
        f"Best: '{best_formula[0]}' at {best_max_dev:.1f}% max deviation.\n\n"
        f"STRUCTURAL DIAGNOSIS: The inter-generational E_base hierarchy is "
        f"ANTI-CORRELATED with all GTE orbit invariants. E_mu/E_e = 242 requires "
        f"a large step from a MODEST triple change (electron→muon). "
        f"E_tau/E_mu = 59 requires a smaller step from a LARGE triple change (muon→tau). "
        f"No monotone function of orbit data can reproduce this inversion.\n\n"
        f"The MFRR bridge would need to provide a quantity that encodes the CASCADE "
        f"PATH DEPTH differently from the terminal triple — not yet derived. "
        f"This is a genuine unsolved problem requiring new theoretical development."
    )

print(f"\n{verdict}")

output = {
    "experiment_id": "COMP-P01-EBF-05",
    "epic": "EPIC_8_EBASE_FOUNDATIONS",
    "question": "Does the MFRR Reflexive Landauer framework bridge GTE orbits to E_base mass hierarchy?",
    "mfrr_constants": {
        "phi": PHI,
        "Lambda": LAMBDA_N,
        "IPT": IPT,
        "one_over_Lambda": 1/LAMBDA_N,
    },
    "required_Rg_lepton": {
        "E_mu_over_E_e": R_mu_e,
        "E_tau_over_E_mu": R_tau_mu,
        "E_tau_over_E_e": R_tau_e,
    },
    "n_formulas_tested": len(formulas),
    "best_formulas": [
        {"rank": i+1, "name": r[0], "max_dev_pct": r[1], "R21": r[2], "R32": r[3]}
        for i, r in enumerate(results[:5])
    ],
    "structural_diagnosis": (
        "Anti-correlation: E_base increment is LARGE for modest triple change (e→μ) "
        "and SMALL for large triple change (μ→τ). All monotone orbit functions give "
        "the opposite pattern. No MFRR formula resolves this without cascade-path encoding."
    ),
    "theoretical_requirement": {
        "I_orbit_increment_e_to_mu_nats": I_diff_me,
        "I_orbit_increment_mu_to_tau_nats": I_diff_tau_mu,
        "ratio_of_increments": I_diff_me / I_diff_tau_mu,
        "interpretation": (
            "Need orbit information I(g) with I(μ)-I(e) = 1.44 nats > I(τ)-I(μ) = 1.07 nats "
            "despite the tau triple being far more complex. Cascade path depth, not terminal "
            "triple structure, must encode this."
        )
    },
    "verdict": verdict,
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
}

sha = hashlib.sha256(
    json.dumps({k: v for k, v in output.items() if k != "timestamp_utc"},
               sort_keys=True, default=str).encode()
).hexdigest()
output["sha256"] = sha

out_path = "comp_p01_EBF_05_mfrr_reflexive_landauer_bridge.json"
with open(out_path, "w") as f:
    json.dump(output, f, indent=2, default=str)
print(f"\nResults written to {out_path}")
