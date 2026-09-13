#!/usr/bin/env python3
"""
Stinespring dilation analysis for the BH unitarity paper.

Imports the GKSL and Stinespring implementation from the TE2.4 source tree,
runs the analysis with the paper's model parameters, and saves results to
bh_unitarity/results/stinespring_results.json.

Model parameters:
  n_modes = 3, n_levels_per_mode = 2, T_H = 0.003979, coupling = 0.01
  total_dim = 8, dim(H_E) = 7

Usage (from repository root):
  python bh_unitarity/run_stinespring_analysis.py
"""

import sys
import json
import hashlib
import numpy as np
from pathlib import Path

# ---------------------------------------------------------------------------
# Locate the TE2.4 source tree relative to this file's position in the repo.
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "MFRR" / "TE_2_Advanced_Explorations" / "TE_2_4_BH_Unitarity" / "src"
DATA_FILE = (
    REPO_ROOT
    / "MFRR"
    / "TE_2_Advanced_Explorations"
    / "TE_2_4_BH_Unitarity"
    / "results"
    / "phase2_3_final"
    / "final_results.json"
)
RESULTS_DIR = Path(__file__).resolve().parent / "results"
OUTPUT_FILE = RESULTS_DIR / "stinespring_results.json"

EXPECTED_SHA256 = "bf2b079c9f3d2850434430356e9f4b1d49b448e6154c1cf808d348a730159b36"

if not SRC_DIR.exists():
    print(f"ERROR: TE2.4 source directory not found: {SRC_DIR}", file=sys.stderr)
    sys.exit(1)

sys.path.insert(0, str(SRC_DIR))

from te2_4_hilbert_space import HorizonHilbertSpace, HilbertSpaceConfig
from te2_4_gksl_constructor import GKSLMasterEquation, GKSLConfig
from te2_4_stinespring import StinespringDilation


# ---------------------------------------------------------------------------
# Verify primary data file integrity
# ---------------------------------------------------------------------------

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_data_file() -> None:
    if not DATA_FILE.exists():
        print(f"WARNING: Primary data file not found: {DATA_FILE}")
        return
    digest = sha256_file(DATA_FILE)
    if digest == EXPECTED_SHA256:
        print(f"SHA-256 verified: {digest}")
    else:
        print(f"WARNING: SHA-256 mismatch for primary data file.")
        print(f"  Expected: {EXPECTED_SHA256}")
        print(f"  Got:      {digest}")


# ---------------------------------------------------------------------------
# Build model
# ---------------------------------------------------------------------------

T_H = 0.003979
N_MODES = 3
N_LEVELS = 2
COUPLING = 0.01
DT = 0.01
FIDELITY_THRESHOLD = 1.0 - 1e-8


def build_model():
    mode_freqs = (np.arange(N_MODES) + 0.5) * np.pi * T_H

    hilbert_config = HilbertSpaceConfig(
        n_modes=N_MODES,
        n_levels_per_mode=N_LEVELS,
        hawking_temperature=T_H,
        mode_frequencies=mode_freqs,
    )

    gksl_config = GKSLConfig(
        hilbert_config=hilbert_config,
        coupling_strength=COUPLING,
        hawking_temperature=T_H,
        check_detailed_balance=True,
        check_cptp=True,
    )

    H = HorizonHilbertSpace(hilbert_config)
    gksl = GKSLMasterEquation(gksl_config, H)
    stine = StinespringDilation(gksl)

    return H, gksl, stine


# ---------------------------------------------------------------------------
# Compute Choi trace preservation error
# ---------------------------------------------------------------------------

def choi_trace_error(gksl: GKSLMasterEquation, H: HorizonHilbertSpace) -> float:
    """
    Compute the Choi trace preservation error for the GKSL channel at dt = DT.

    Trace preservation of the CPTP map Phi means:
        Tr[Phi(rho)] = 1  for all rho with Tr[rho] = 1.

    Equivalently, sum_k K_k^dag K_k = I  (completeness of Kraus operators).
    We measure max|sum_k K_k^dag K_k - I|.
    """
    from te2_4_stinespring import StinespringDilation
    stine_tmp = StinespringDilation(gksl)
    kraus_ops = stine_tmp.kraus_operators(DT)

    d = H.total_dim
    completeness = np.zeros((d, d), dtype=np.complex128)
    for K in kraus_ops:
        completeness += K.conj().T @ K

    error = float(np.max(np.abs(completeness - np.eye(d))))
    return error


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 70)
    print("BH REFLEXIVE UNITARITY — STINESPRING DILATION ANALYSIS")
    print("=" * 70)

    print(f"\nModel parameters:")
    print(f"  n_modes          = {N_MODES}")
    print(f"  n_levels_per_mode = {N_LEVELS}")
    print(f"  T_H              = {T_H}")
    print(f"  coupling (gamma0) = {COUPLING}")
    print(f"  total_dim        = {N_LEVELS ** N_MODES}")
    print(f"  dt (test step)   = {DT}")

    print("\nVerifying primary data file...")
    verify_data_file()

    print("\nBuilding model...")
    H, gksl, stine = build_model()

    print(f"\nStinespring parameters:")
    print(f"  System dimension:      {H.total_dim}")
    print(f"  Environment dimension: {stine.dim_env}")
    print(f"  Total dimension:       {H.total_dim * stine.dim_env}")

    # -----------------------------------------------------------------------
    # Fidelity check on three test states
    # -----------------------------------------------------------------------
    test_states = [
        ("Vacuum",      H.vacuum_state()),
        ("Thermal",     H.thermal_state()),
        ("Fock(1,0,0)", H.fock_state([1, 0, 0])),
    ]

    print(f"\nStinespring fidelity checks (dt = {DT}):")
    fidelities = []
    for name, rho in test_states:
        F, _, _ = stine.verify_equivalence(rho, DT)
        status = "PASS" if F >= FIDELITY_THRESHOLD else "FAIL"
        print(f"  {name:15s}: F = {F:.10f}  [{status}]")
        fidelities.append(float(F))

    F_min = float(np.min(fidelities))
    F_mean = float(np.mean(fidelities))
    stinespring_pass = F_min >= FIDELITY_THRESHOLD

    # -----------------------------------------------------------------------
    # Choi trace preservation error
    # -----------------------------------------------------------------------
    choi_err = choi_trace_error(gksl, H)
    choi_pass = choi_err <= 1e-10

    # -----------------------------------------------------------------------
    # Print summary
    # -----------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("RESULTS SUMMARY")
    print("=" * 70)
    print(f"  dim(H_E):                    {stine.dim_env}")
    print(f"  Stinespring fidelity (min):  F = {F_min:.6e}  "
          f"(threshold 1 - 1e-8 = {FIDELITY_THRESHOLD:.6e})  "
          f"[{'PASS' if stinespring_pass else 'FAIL'}]")
    print(f"  Choi trace preservation:     error = {choi_err:.2e}  "
          f"[{'PASS' if choi_pass else 'FAIL'}]")
    print("=" * 70)

    if not stinespring_pass:
        print("WARNING: Stinespring fidelity below threshold.")
    if not choi_pass:
        print("WARNING: Choi trace preservation error exceeds 1e-10.")

    # -----------------------------------------------------------------------
    # Save results
    # -----------------------------------------------------------------------
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    results = {
        "model_parameters": {
            "n_modes": N_MODES,
            "n_levels_per_mode": N_LEVELS,
            "T_H": T_H,
            "coupling": COUPLING,
            "total_dim": H.total_dim,
            "dim_H_E": stine.dim_env,
            "dt_tested": DT,
        },
        "stinespring": {
            "fidelities": fidelities,
            "F_min": F_min,
            "F_mean": F_mean,
            "threshold": FIDELITY_THRESHOLD,
            "pass": stinespring_pass,
        },
        "choi_trace_preservation": {
            "error": choi_err,
            "threshold": 1e-10,
            "pass": choi_pass,
        },
        "primary_data_sha256": EXPECTED_SHA256,
        "primary_data_file": str(DATA_FILE.relative_to(REPO_ROOT)),
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to {OUTPUT_FILE.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
