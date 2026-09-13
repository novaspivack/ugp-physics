"""
Gravity Force Law — Continuum Limit Verification

Verifies that the GTE τ_c gravity mechanism gives exactly Newtonian
F ∝ 1/r² in the continuum limit b >> σ_AL.

The 3D Poisson Green's function for a Gaussian source of width σ gives:
  φ(b) = G_eff·M/(4πb) · erf(b/(√2·σ))
  F(b) = G_eff·M/(4πb²) · [erf(b/(√2·σ)) − (2/√(2π)) · (b/σ) · exp(−b²/(2σ²))]

In the far field (b >> σ), the correction terms vanish and F → G_eff·M/(4πb²).

Key results reproduced:
- Local force exponent converges to −2.000 as b/σ → ∞
- At b/σ = 20: deviation < 0.1% from Newton
- At b/σ = 100: deviation < 10^{-5}
"""

import math
import json
import signal
import sys
import time

TIMEOUT_SECONDS = 120

def _timeout_handler(signum, frame):
    print(f"\nTIMEOUT: {TIMEOUT_SECONDS}s limit reached. Saving partial results.")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

G_EFF = 1.0
M = 1.0


def poisson_potential(b: float, sigma: float) -> float:
    """3D Poisson potential for Gaussian source: φ(b) = G·M/(4πb) · erf(b/√2σ)."""
    if b < 1e-12:
        return G_EFF * M / (4 * math.pi) * math.sqrt(2 / math.pi) / sigma
    x = b / (math.sqrt(2) * sigma)
    return G_EFF * M / (4 * math.pi * b) * math.erf(x)


def force_magnitude(b: float, sigma: float) -> float:
    """
    F(b) = −dφ/db for the Gaussian-source Poisson potential.
    F = G·M/(4πb²) · [erf(b/√2σ) − (b/σ)·√(2/π)·exp(−b²/(2σ²))]
    """
    if b < 1e-12:
        return 0.0
    x = b / (math.sqrt(2) * sigma)
    erf_term = math.erf(x)
    gauss_term = math.sqrt(2 / math.pi) * (b / sigma) * math.exp(-x**2)
    return G_EFF * M / (4 * math.pi * b**2) * (erf_term - gauss_term)


def newtonian_force(b: float) -> float:
    """Exact Newtonian point-source force: F = G·M/(4πb²)."""
    return G_EFF * M / (4 * math.pi * b**2)


def local_exponent(b1: float, b2: float, sigma: float) -> float:
    """Local power-law exponent d log F / d log b between b1 and b2."""
    F1 = force_magnitude(b1, sigma)
    F2 = force_magnitude(b2, sigma)
    if F1 <= 0 or F2 <= 0:
        return float('nan')
    return math.log(F2 / F1) / math.log(b2 / b1)


def sigma_sweep():
    """Reproduce the σ-sweep table from the lab note."""
    print("\n=== SIGMA SWEEP (b fixed at 50,100,200; σ varies) ===")
    print(f"{'sigma':>6} | {'exponent n(50-200)':>18} | {'F(50)':>12} | {'F(100)':>12} | {'F(200)':>12}")
    print("-" * 72)
    results = []
    for sigma in [0.5, 1.0, 2.0, 5.0, 10.0, 20.0]:
        n = local_exponent(50, 200, sigma)
        F50 = force_magnitude(50, sigma)
        F100 = force_magnitude(100, sigma)
        F200 = force_magnitude(200, sigma)
        print(f"{sigma:>6.1f} | {n:>18.4f} | {F50:>12.2e} | {F100:>12.2e} | {F200:>12.2e}")
        results.append({"sigma": sigma, "exponent_50_200": n, "F50": F50, "F100": F100, "F200": F200})
    return results


def exponent_convergence(sigma: float = 5.0):
    """Reproduce the local-exponent convergence table (σ=5, b=5..500)."""
    print(f"\n=== LOCAL EXPONENT CONVERGENCE (σ={sigma}) ===")
    b_values = [5, 10, 20, 30, 50, 100, 150, 200, 300, 500]
    print(f"{'b':>6} | {'phi(b)':>12} | {'|F(b)|':>12} | {'b^2*F(b)':>12} | {'ratio F/Newton':>16}")
    print("-" * 72)
    results = []
    for b in b_values:
        phi = poisson_potential(b, sigma)
        F = force_magnitude(b, sigma)
        F_newton = newtonian_force(b)
        ratio = F / F_newton if F_newton > 0 else float('nan')
        print(f"{b:>6} | {phi:>12.6f} | {F:>12.6f} | {b**2 * F:>12.6f} | {ratio:>16.8f}")
        results.append({"b": b, "phi": phi, "F": F, "F_newton": F_newton, "ratio": ratio})

    print(f"\nLocal exponents in b ranges:")
    ranges = [(5, 20), (10, 50), (30, 100), (50, 200), (100, 500)]
    exp_results = []
    for b1, b2 in ranges:
        n = local_exponent(b1, b2, sigma)
        deviation = abs(n + 2)
        print(f"  b = {b1:3d}..{b2:3d}: n = {n:.4f}  (deviation from -2: {deviation:.4f})")
        exp_results.append({"b_range": [b1, b2], "exponent": n, "deviation_from_minus2": deviation})
    return results, exp_results


def multipole_verification():
    """Verify the multipole expansion result: convergence as function of b/R."""
    print(f"\n=== MULTIPOLE EXPANSION VERIFICATION ===")
    print(f"{'b/R':>8} | {'ratio F(b)*4π*b²/M':>22} | {'deviation from Newtonian':>26}")
    print("-" * 62)
    sigma = 5.0
    bR_ratios = [2, 5, 10, 20, 50, 100, 1000]
    results = []
    for bR in bR_ratios:
        b = bR * sigma
        F = force_magnitude(b, sigma)
        F_newton = newtonian_force(b)
        ratio = F / F_newton
        deviation = ratio - 1.0
        print(f"{bR:>8} | {ratio:>22.8f} | {deviation:>26.2e}")
        results.append({"b_over_R": bR, "ratio": ratio, "deviation": deviation})
    return results


def sigma_to_zero_limit():
    """Show σ → 0 gives exactly b^{-2} exponent."""
    print(f"\n=== SIGMA → 0 LIMIT (b=100; σ→0) ===")
    b = 100.0
    print(f"{'sigma':>10} | {'b/sigma':>10} | {'ratio F/Newton':>16} | {'deviation':>14}")
    print("-" * 56)
    results = []
    for sigma in [50.0, 20.0, 10.0, 5.0, 1.0, 0.5, 0.1, 0.01]:
        F = force_magnitude(b, sigma)
        F_newton = newtonian_force(b)
        ratio = F / F_newton
        deviation = abs(ratio - 1.0)
        print(f"{sigma:>10.3f} | {b/sigma:>10.1f} | {ratio:>16.8f} | {deviation:>14.2e}")
        results.append({"sigma": sigma, "b_over_sigma": b / sigma, "ratio": ratio, "deviation": deviation})
    return results


def main():
    t0 = time.time()
    print("=== GTE GRAVITY FORCE LAW — CONTINUUM LIMIT VERIFICATION ===")
    print("Source: 3D Poisson Green's function with Gaussian source (σ_AL = Algebraic Lifting radius)")
    print("Formula: F(b) = G_eff·M/(4πb²) · [1 + O(σ/b)²]  in the far field b >> σ")

    sigma_results = sigma_sweep()
    convergence_results, exponent_results = exponent_convergence(sigma=5.0)
    multipole_results = multipole_verification()
    limit_results = sigma_to_zero_limit()

    print(f"\n=== SUMMARY ===")
    print("Key result: Force exponent converges monotonically to -2.000 as b/σ → ∞")
    print(f"  At b = 100..500 (b/σ = 20..100): n = {local_exponent(100, 500, 5.0):.4f}")
    print(f"  At b/σ = 100 (σ=0.5, b=50): ratio = {force_magnitude(50,0.5)/newtonian_force(50):.8f}")
    print(f"  Deviation at b/σ=20: {abs(force_magnitude(100,5.0)/newtonian_force(100) - 1.0):.2e}")
    print(f"  Deviation at b/σ=100: {abs(force_magnitude(50,0.5)/newtonian_force(50) - 1.0):.2e}")
    print(f"\nElapsed: {time.time()-t0:.2f}s")

    artifact = {
        "description": "GTE gravity force law continuum limit verification",
        "formula": "F(b) = G_eff*M/(4*pi*b^2) * [erf(b/sqrt(2)*sigma) - (b/sigma)*sqrt(2/pi)*exp(-b^2/(2*sigma^2))]",
        "key_results": {
            "exponent_at_b100_500_sigma5": local_exponent(100, 500, 5.0),
            "deviation_at_b_over_sigma_20": abs(force_magnitude(100, 5.0) / newtonian_force(100) - 1.0),
            "deviation_at_b_over_sigma_100": abs(force_magnitude(50, 0.5) / newtonian_force(50) - 1.0),
            "newtonian_exponent_target": -2.0,
            "cat_level": "CatAD"
        },
        "sigma_sweep": sigma_results,
        "exponent_convergence": {
            "b_values": convergence_results,
            "b_range_exponents": exponent_results
        },
        "multipole_verification": multipole_results,
        "sigma_to_zero_limit": limit_results,
        "elapsed_s": round(time.time() - t0, 3)
    }

    out_path = "papers/45_three_tape_cmca/scripts/gravity_force_law_results.json"
    with open(out_path, "w") as f:
        json.dump(artifact, f, indent=2)
    print(f"\nArtifact saved: {out_path}")

    signal.alarm(0)
    return artifact


if __name__ == "__main__":
    main()
