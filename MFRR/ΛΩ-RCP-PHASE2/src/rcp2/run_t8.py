"""
T8: Universal Holographic Closure — Non-Circular Test (revised May 2026)

Claim: I_bulk = Λ^(-1) · A_F (Fisher boundary area)

Previous implementation (CIRCULAR): I_bulk was defined as A_F/Λ + correction,
making the test trivially pass. This revision computes I_bulk independently.

Independent measure:
    I_bulk = von Neumann / Shannon bulk entropy of the field configuration,
             computed without any reference to Λ.
    I_bulk = N_bulk × H(saturation)
    where H(s) = -s·ln(s) - (1-s)·ln(1-s)  [Shannon entropy per cell, nats]

The slope of I_bulk vs A_F is then compared to Λ^(-1).
If T8 holds, slope ≈ Λ^(-1) ≈ 3.82 for all (domain, saturation) pairs.

Cross-references:
  - Phase I L1 (Λ validated to 0.04% in PC test)
  - MFRR Reflexive Landauer Bound (T2, bridge premise)
"""

import numpy as np
import pandas as pd
from multiprocessing import Pool
from .util import set_seed, save_json, ensure_dirs, load_yaml, Lambda


def compute_fisher_boundary_area(domain_size, saturation):
    """
    Fisher boundary area (unchanged from original).
    A_F = (boundary nodes) × (Fisher metric intensity at boundary).
    Does NOT use Λ.
    """
    boundary_nodes = 6 * domain_size ** 2      # 6 faces of a cube
    fisher_intensity = 1.0 + 2.0 * saturation  # Fisher metric grows with saturation
    return float(boundary_nodes * fisher_intensity)


def compute_bulk_information_independent(domain_size, saturation):
    """
    Bulk information content — computed WITHOUT using Λ.

    Measure: von Neumann / Shannon entropy of the bulk field state.
        H(s) = -s·ln(s) - (1-s)·ln(1-s)   (nats per cell)
        I_bulk = N_bulk × H(saturation)

    Physical interpretation: number of nats needed to describe the full
    field configuration over the bulk volume, treating each cell as a
    two-state system with occupation probability = saturation.
    This is independent of Λ and gives a genuine holographic test.
    """
    n_bulk = domain_size ** 3
    s = np.clip(saturation, 1e-9, 1.0 - 1e-9)
    H = -(s * np.log(s) + (1.0 - s) * np.log(1.0 - s))   # nats per cell
    return float(n_bulk * H)


def process_holo_task(args):
    seed, domain_size, saturation = args
    set_seed(seed)

    A_F   = compute_fisher_boundary_area(domain_size, saturation)
    I_bulk = compute_bulk_information_independent(domain_size, saturation)

    # T8 prediction: I_bulk = Λ^(-1) · A_F
    Lam = Lambda()
    I_predicted = A_F / Lam
    rel_error = abs(I_bulk - I_predicted) / (I_predicted + 1e-9)

    # Dimensionless ratio (should ≈ 1 if T8 holds)
    ratio = I_bulk / (A_F / Lam) if A_F > 0 else float('nan')

    return (seed, domain_size, saturation, A_F, I_bulk, I_predicted, rel_error, ratio)


def main():
    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.chdir(base_dir)
    ensure_dirs()

    cfg = load_yaml("cfg/config.yaml")
    seeds       = cfg["phase2"]["seeds"]
    domains     = cfg["phase2"]["t8_holo"]["domains"]
    saturations = cfg["phase2"]["t8_holo"]["saturation"]
    tol         = cfg["phase2"]["t8_holo"]["tol_holo"]
    n_cores     = cfg["phase2"]["n_cores"]

    print("=" * 70)
    print("T8: UNIVERSAL HOLOGRAPHIC CLOSURE (non-circular test, May 2026)")
    print("=" * 70)
    print(f"\nClaim: I_bulk = Λ^(-1) · A_F")
    print(f"  I_bulk = Shannon bulk entropy (independent of Λ)")
    print(f"  Λ  = {Lambda():.6f}")
    print(f"  Λ⁻¹ = {1.0/Lambda():.4f}  (expected slope)")
    print(f"  Domain sizes: {domains}")
    print(f"  Saturation levels: {saturations}")

    tasks = [(s, d, sat) for s in seeds for d in domains for sat in saturations]

    with Pool(processes=n_cores) as pool:
        rec = pool.map(process_holo_task, tasks)

    df = pd.DataFrame(rec, columns=[
        "seed", "domain", "saturation",
        "A_F", "I_bulk", "I_predicted", "rel_error", "ratio"
    ])
    df.to_csv("results/t8_holo_records.csv", index=False)

    # ── Summary statistics ──────────────────────────────────────────────────
    Lam = Lambda()
    Lam_inv = 1.0 / Lam

    # Fit I_bulk = a · A_F  across all (domain, saturation) points
    X = df["A_F"].values
    y = df["I_bulk"].values
    a = np.polyfit(X, y, 1)[0]                       # slope
    yhat = a * X
    ss_res = np.sum((y - yhat) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2) + 1e-12
    r2 = 1.0 - ss_res / ss_tot

    slope_rel_err = abs(a - Lam_inv) / Lam_inv

    # Per-domain statistics (slope varies by domain if I_bulk ∝ d³ but A_F ∝ d²)
    print(f"\n{'─'*70}")
    print(f"{'Domain':>8} | {'Mean ratio I_bulk/(Λ⁻¹·A_F)':>30} | {'SD':>8}")
    print(f"{'─'*70}")
    for d in sorted(df["domain"].unique()):
        sub = df[df["domain"] == d]
        print(f"{d:>8} | {sub['ratio'].mean():>30.4f} | {sub['ratio'].std():>8.4f}")

    print(f"\n{'─'*70}")
    print(f"Overall linear fit  I_bulk = a · A_F")
    print(f"  Fitted slope a  = {a:.4f}")
    print(f"  Expected Λ⁻¹    = {Lam_inv:.4f}")
    print(f"  Slope error     = {slope_rel_err*100:.1f}%")
    print(f"  R²              = {r2:.4f}")

    # T8 verdict: passes only if slope ≈ Λ⁻¹ within tolerance
    high_sat = df[df["saturation"] >= 0.8]
    mean_err_high = high_sat["rel_error"].mean() if len(high_sat) > 0 else 1.0
    overall_pass = slope_rel_err < tol

    print(f"\nHigh-saturation regime (s ≥ 0.8) mean relative error: {mean_err_high:.4f}")
    print(f"Tolerance: {tol:.2f}")
    print(f"\n{'='*70}")
    print(f"T8 STATUS: {'PASS' if overall_pass else 'FAIL (slope ≠ Λ⁻¹ — T8 not computationally certified)'}")
    print(f"{'='*70}")
    print(f"\nNote: T8's ANALYTICAL derivation from Reflexive Landauer + Fisher area law")
    print(f"stands independently of this test. The computational test above uses")
    print(f"I_bulk = Shannon entropy (non-circular). If FAIL, T8 remains [B] (bridge).")

    summary = {
        "fitted_slope":         float(a),
        "Lambda_inv_expected":  float(Lam_inv),
        "slope_rel_error":      float(slope_rel_err),
        "R2":                   float(r2),
        "high_sat_mean_error":  float(mean_err_high),
        "tolerance":            float(tol),
        "pass":                 bool(overall_pass),
        "status":               "PASS" if overall_pass else "FAIL",
        "method":               "Shannon bulk entropy (independent of Lambda, May 2026)",
        "note":                 (
            "Non-circular test: I_bulk = d^3 * H(s) where H = Shannon entropy per cell. "
            "Slope of I_bulk vs A_F compared to Λ^(-1). "
            "Analytical derivation of T8 unaffected by this result."
        ),
    }
    save_json(summary, "results/t8_holo_summary.json")
    return summary


if __name__ == "__main__":
    import multiprocessing
    multiprocessing.set_start_method('spawn', force=True)
    main()
