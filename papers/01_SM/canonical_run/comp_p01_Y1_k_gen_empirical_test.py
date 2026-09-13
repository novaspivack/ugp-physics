#!/usr/bin/env python3
"""
COMP-P01-Y1 — Empirical sensitivity test for k_gen = π/2 vs 1.5448

Question: is k_gen = π/2 structurally correct, or is the empirical value
1.5448 closer to truth?

Test: compute the UCL log_Cf predictions for the 9 charged fermions, using
theoretical UCL2.3 coefficients for everything EXCEPT k_gen.  Vary k_gen
over the scan {1.52, 1.5448, π/2 = 1.5708, 1.60} and compare to the
empirical UCL2.3 predictions (which match PDG masses exactly).

If π/2 gives lower residual → k_gen = π/2 is structurally correct;
   the 1.68% dual-path deviation reflects calibration noise absorbing
   error from other coefficients.

If 1.5448 gives lower residual → k_gen = π/2 is NOT exactly the right value;
   the true k_gen is closer to 1.5448 and π/2 is an approximation.

Reference:
  - UCL formula: log C_f = K_CONST + K_L·L + K_L²·L² + K_GEN·g + K_GEN²·g²
                         + K_M·M + K_μa·μ(a) + K_μb·μ(b) + K_μc·μ(c)
  - Canonical triples: from Paper 1 & UGP_GTE_SM_Verifier (electron, muon, tau,
                       up, charm, top, down, strange, bottom)
"""
from __future__ import annotations

import math
import sys
from fractions import Fraction
from pathlib import Path
import json
import hashlib
import datetime


def mobius(n: int) -> int:
    """Classical Möbius function μ(n)."""
    if n == 0:
        return 0
    n = abs(n)
    if n == 1:
        return 1
    primes = []
    x = n
    p = 2
    while p * p <= x:
        e = 0
        while x % p == 0:
            x //= p
            e += 1
        if e >= 2:
            return 0
        if e == 1:
            primes.append(p)
        p += 1
    if x > 1:
        primes.append(x)
    return (-1) ** len(primes)


# 9 charged fermions with their canonical triples (from UGP_GTE_SM_Verifier line 1556-1585)
# (a, b, c, gen, name)
CHARGED_FERMIONS = [
    (1,   73,      823,    1, "electron"),
    (9,   42,     1023,    2, "muon"),
    (5,   275,   65535,    3, "tau"),
    (5,   9,       275,    1, "up"),
    (5,   275,   65535,    2, "charm"),
    (76,  337920,   -1,    3, "top"),   # c = -1 (special)
    (9,   5,        42,    1, "down"),
    (9,   186,    1023,    2, "strange"),
    (5,   8191,  65535,    3, "bottom"),
]


# Theoretical UCL2.3 (Elegant Kernel) coefficients
# Reference: Paper 1 §3 Eq. eq:kernel (line 416)
# and the dual-path table (line 453-461)
PHI = (1 + math.sqrt(5)) / 2
PI = math.pi

THEORETICAL_UCL = {
    "k_const": -0.15203,           # empirical; theoretical derivation partial
    "k_L":     +0.01974,           # = -2·k_L²·L* = (21/512)·ln(φ)
    "k_L2":    7.0 / 512.0,        # = δ/2^(n-1) = 7/512  [Lean-certified]
    "k_gen":   PI / 2,             # = π/2 (theoretical "quarter-turn gauge")
    "k_gen2":  -PHI / 2,           # = -φ/2 (D₅ pentagonal, Lean-certified Phase C)
    "k_M":     -PHI / 2 + 7.0 / 2048.0,   # Quarter-Lock: k_M = k_gen² + k_L²/4
    "k_mu_a":  1.0 / 8.0,          # = 1/8 (Möbius triple, THM-UCL-3 Lean-certified)
    "k_mu_b":  -3.0 / 2.0,         # = -3/2
    "k_mu_c":  4.0 / 3.0,          # = 4/3
}

# Empirical UCL2.3 (dual-path table column "Empirical")
EMPIRICAL_UCL = {
    "k_const": -0.15487,
    "k_L":     +0.01970,
    "k_L2":    +0.01357,
    "k_gen":   +1.54480,           # This is 1.54480; theoretical is π/2 = 1.5708
    "k_gen2":  -0.80925,
    "k_M":     -0.80587,
    "k_mu_a":  +0.12373,
    "k_mu_b":  -1.50453,
    "k_mu_c":  +1.32657,
}


def compute_log_Cf(triple, coeffs):
    """Evaluate the UCL formula for a given triple and coefficient set."""
    a, b, c, gen, _name = triple
    # Handle special case c = -1 (e.g., top quark): set L = 0 (log(|b|/|c|) undefined for c = 0 or < 0 literal)
    # For c = -1, use |c| = 1 so L = log(|b|).
    if c != 0:
        L = math.log(abs(b) / abs(c))
    else:
        L = 0.0
    mu_a = mobius(abs(a))
    mu_b = mobius(abs(b))
    mu_c = mobius(abs(c))
    M = mu_a * mu_b * mu_c

    log_Cf = (
        coeffs["k_const"]
        + coeffs["k_L"] * L
        + coeffs["k_L2"] * L * L
        + coeffs["k_gen"] * gen
        + coeffs["k_gen2"] * gen * gen
        + coeffs["k_M"] * M
        + coeffs["k_mu_a"] * mu_a
        + coeffs["k_mu_b"] * mu_b
        + coeffs["k_mu_c"] * mu_c
    )
    return log_Cf


def compute_residuals_from_empirical(k_gen_value, other_theoretical=True):
    """Compute residuals of theoretical log_Cf vs empirical log_Cf,
    using the given k_gen and ALL OTHER coefficients at their theoretical values
    (if other_theoretical) or empirical values (if not).
    """
    if other_theoretical:
        base = THEORETICAL_UCL.copy()
    else:
        base = EMPIRICAL_UCL.copy()
    base["k_gen"] = k_gen_value

    residuals = []
    for triple in CHARGED_FERMIONS:
        log_Cf_test = compute_log_Cf(triple, base)
        log_Cf_empirical = compute_log_Cf(triple, EMPIRICAL_UCL)
        residuals.append({
            "name":             triple[4],
            "gen":              triple[3],
            "log_Cf_test":      log_Cf_test,
            "log_Cf_empirical": log_Cf_empirical,
            "residual":         log_Cf_test - log_Cf_empirical,
            "abs_residual":     abs(log_Cf_test - log_Cf_empirical),
        })
    return residuals


def rms(values):
    return math.sqrt(sum(v * v for v in values) / len(values))


def main() -> int:
    print("=" * 72)
    print("COMP-P01-Y1: Empirical test — k_gen = π/2 vs 1.5448")
    print("=" * 72)
    print()
    print(f"Theoretical k_gen = π/2 = {PI/2:.8f}")
    print(f"Empirical k_gen  = 1.5448")
    print(f"Difference        = {PI/2 - 1.5448:.6f}  ({100*(PI/2 - 1.5448)/1.5448:.2f}%)")
    print()

    # Scan over candidate k_gen values
    candidates = [
        ("1.5200",        1.5200),
        ("1.5300",        1.5300),
        ("1.5400",        1.5400),
        ("1.5448 (empirical)", 1.5448),
        ("1.5500",        1.5500),
        ("1.5600",        1.5600),
        ("1.5700",        1.5700),
        ("π/2 (theoretical)",  PI/2),
        ("1.5800",        1.5800),
        ("1.6000",        1.6000),
    ]

    print("Residuals with all OTHER coefficients at theoretical values:")
    print(f"  {'k_gen':<22s}{'RMS residual':<20s}{'Max |residual|'}")
    print("-" * 72)
    scan_results = []
    for label, k_gen in candidates:
        residuals = compute_residuals_from_empirical(k_gen, other_theoretical=True)
        r_values = [r["residual"] for r in residuals]
        r_rms = rms(r_values)
        r_max = max(abs(r) for r in r_values)
        scan_results.append({
            "k_gen_label": label,
            "k_gen_value": k_gen,
            "rms_residual": r_rms,
            "max_abs_residual": r_max,
            "per_fermion": residuals,
        })
        marker = ""
        if abs(k_gen - PI/2) < 1e-6:
            marker = "  ← π/2"
        elif abs(k_gen - 1.5448) < 1e-6:
            marker = "  ← empirical"
        print(f"  {label:<22s}{r_rms:<20.6f}{r_max:.6f}{marker}")
    print()

    # Find the k_gen that minimizes RMS residual
    best = min(scan_results, key=lambda r: r["rms_residual"])
    print(f"Best-fit k_gen over scan (all others at theoretical):")
    print(f"  {best['k_gen_label']}  RMS residual = {best['rms_residual']:.6f}")
    print()

    # Compare π/2 to empirical directly
    pi_over_2 = next(r for r in scan_results if abs(r["k_gen_value"] - PI/2) < 1e-6)
    empirical = next(r for r in scan_results if abs(r["k_gen_value"] - 1.5448) < 1e-6)
    print("DIRECT COMPARISON:")
    print(f"  k_gen = π/2 = {PI/2:.6f}:  RMS = {pi_over_2['rms_residual']:.6f}")
    print(f"  k_gen = 1.5448:             RMS = {empirical['rms_residual']:.6f}")
    if pi_over_2['rms_residual'] < empirical['rms_residual']:
        print(f"  → π/2 gives LOWER residual; structurally correct despite 1.68% dual-path deviation.")
    else:
        print(f"  → 1.5448 gives LOWER residual; π/2 is an approximation, not exact.")
    ratio = pi_over_2['rms_residual'] / empirical['rms_residual'] if empirical['rms_residual'] > 0 else float('inf')
    print(f"  ratio RMS(π/2) / RMS(1.5448) = {ratio:.4f}")
    print()

    # Show per-fermion residuals for both
    print("Per-fermion log_Cf test residuals:")
    print(f"  {'Fermion':<10s}{'gen':>4s}{'log_Cf(π/2)':>16s}{'log_Cf(1.5448)':>17s}{'Δ':>10s}")
    for i, (triple, r_pi, r_emp) in enumerate(zip(CHARGED_FERMIONS, pi_over_2["per_fermion"], empirical["per_fermion"])):
        dev_pi = r_pi["residual"]
        dev_emp = r_emp["residual"]
        print(f"  {triple[4]:<10s}{triple[3]:>4d}"
              f"{r_pi['log_Cf_test']:>16.6f}{r_emp['log_Cf_test']:>17.6f}"
              f"{r_pi['log_Cf_test']-r_emp['log_Cf_test']:>10.6f}")

    report = {
        "experiment_id": "COMP-P01-Y1",
        "question": (
            "Is k_gen = π/2 structurally correct, or closer to 1.5448? "
            "Test by computing log_Cf residuals across k_gen scan."
        ),
        "theoretical_UCL": THEORETICAL_UCL,
        "empirical_UCL":   EMPIRICAL_UCL,
        "scan_results":    scan_results,
        "best_fit":        best,
        "verdict": (
            "π/2 lower" if pi_over_2['rms_residual'] < empirical['rms_residual']
            else "1.5448 lower"
        ),
        "rms_pi_over_2":   pi_over_2['rms_residual'],
        "rms_empirical":   empirical['rms_residual'],
        "ratio":           ratio,
        "timestamp_utc":   datetime.datetime.utcnow().isoformat(timespec="seconds"),
    }
    out_path = Path(__file__).with_suffix(".json")
    with open(out_path, "w") as fh:
        json.dump(report, fh, indent=2, sort_keys=False)
    sha = hashlib.sha256(out_path.read_bytes()).hexdigest()
    print(f"\n[write] {out_path.name}")
    print(f"[sha]   {sha}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
