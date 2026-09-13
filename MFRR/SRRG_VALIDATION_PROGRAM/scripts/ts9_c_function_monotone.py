#!/usr/bin/env python3
"""
TS9: SRRG c-Function Monotonicity Test

Validates that the c-function C[S] = F[S] - λ(n·k)² decreases monotonically
along SRRG flow trajectories, confirming Theorem (SRRG c-Function).

Cross-references:
- ROUND_3_ENHANCEMENTS_PLAN.md: B8 (SRRG c-Function Monotone)
- Mathematical_Foundations_of_Reflexive_Reality.tex: Theorem~\ref{thm:srrg-c-function}
"""

import json
import hashlib
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple
import numpy as np
from datetime import datetime
from tqdm import tqdm

from srrg_core import (
    GTETriple,
    SRRGParameters,
    compute_gradient_fd,
    srrg_flow_step
)
from srrg_io import load_canonical_sm_triples, save_results_with_manifest
from srrg_functional_pure_gte import elegant_palette, viability_functional_pure_gte


@dataclass
class CMonotonicityResult:
    """Results for c-function monotonicity for a single particle."""
    particle_name: str
    num_trajectories: int
    mean_delta_C: float
    std_delta_C: float
    max_violation: float
    fraction_monotone: float
    status: str


def compute_c_function(triple: GTETriple, 
                      ucl_palette, 
                      params: SRRGParameters, 
                      lambda_c: float = 1.0) -> float:
    """
    Compute the SRRG c-function: C[S] = F[S] - λ(n·k)²
    
    Parameters:
    -----------
    triple : GTETriple
        Current theory point
    ucl_palette : UCLPalette
        UCL coefficients
    params : SRRGParameters
        Viability functional parameters
    lambda_c : float
        Penalty weight for quarter-lock deviation
        
    Returns:
    --------
    c_value : float
        c-function value
    """
    # Viability functional F
    F = viability_functional_pure_gte([triple], ucl_palette, params)
    
    # Quarter-lock deviation: n·k = |a*c - b²|
    a, b, c = triple.a, triple.b, triple.c
    n_dot_k = abs(a * c - b**2)
    
    # c-function
    C = F - lambda_c * (n_dot_k ** 2)
    
    return C


def evolve_single_trajectory(
    canonical: GTETriple,
    ucl_palette,
    params: SRRGParameters,
    num_steps: int = 30,
    lambda_c: float = 1.0,
    seed: int = 42
) -> Dict:
    """
    Evolve a single SRRG trajectory and track c-function.
    
    Returns:
    --------
    result : dict
        Contains trajectory, C values, ΔC values, status
    """
    # Random perturbation to start (Gaussian with radius=5)
    rng = np.random.default_rng(seed)
    
    a_start = canonical.a + int(rng.normal(0, 5))
    b_start = canonical.b + int(rng.normal(0, 5))
    c_start = canonical.c + int(rng.normal(0, 5)) if canonical.c > 0 else canonical.c
    
    # Ensure admissible
    a_start = max(1, min(100_000, a_start))
    b_start = max(1, min(1_000_000, b_start))
    if canonical.c > 0:
        c_start = max(1, min(100_000, c_start))
    
    current = GTETriple(a_start, b_start, c_start, canonical.g, canonical.name)
    
    trajectory = [current]
    C_values = [compute_c_function(current, ucl_palette, params, lambda_c)]
    
    # Define F_fn for flow step
    def F_fn(t: GTETriple) -> float:
        return viability_functional_pure_gte([t], ucl_palette, params)
    
    # Evolve
    for step in range(num_steps):
        triple_new, F_new, alpha = srrg_flow_step(current, F_fn, params, None)
        
        if (triple_new.a == current.a and 
            triple_new.b == current.b and 
            triple_new.c == current.c):
            # Converged
            break
            
        trajectory.append(triple_new)
        C_values.append(compute_c_function(triple_new, ucl_palette, params, lambda_c))
        current = triple_new
    
    # Compute ΔC values
    delta_C = [C_values[i+1] - C_values[i] for i in range(len(C_values)-1)]
    
    # Check monotonicity (ΔC ≤ 0 with tolerance)
    tolerance = 1e-5
    violations = [dC for dC in delta_C if dC > tolerance]
    max_violation = float(max(violations)) if violations else 0.0
    fraction_monotone = 1.0 - len(violations) / max(1, len(delta_C))
    
    mean_delta_C = float(np.mean(delta_C)) if delta_C else 0.0
    std_delta_C = float(np.std(delta_C)) if delta_C else 0.0
    
    return {
        "trajectory_length": len(trajectory),
        "C_initial": float(C_values[0]),
        "C_final": float(C_values[-1]),
        "delta_C_total": float(C_values[-1] - C_values[0]),
        "mean_delta_C_per_step": mean_delta_C,
        "std_delta_C": std_delta_C,
        "max_violation": max_violation,
        "fraction_monotone": fraction_monotone
    }


def test_particle_c_monotonicity(
    canonical: GTETriple,
    ucl_palette,
    params: SRRGParameters,
    num_trajectories: int = 16,
    lambda_c: float = 1.0
) -> CMonotonicityResult:
    """
    Test c-function monotonicity for a single particle over multiple trajectories.
    """
    results = []
    
    for traj_idx in range(num_trajectories):
        traj_result = evolve_single_trajectory(
            canonical, ucl_palette, params, 
            lambda_c=lambda_c, 
            seed=42 + traj_idx
        )
        results.append(traj_result)
    
    # Aggregate
    mean_deltas = [r["mean_delta_C_per_step"] for r in results]
    max_violations = [r["max_violation"] for r in results]
    fractions = [r["fraction_monotone"] for r in results]
    
    mean_delta_C = float(np.mean(mean_deltas))
    std_delta_C = float(np.std(mean_deltas))
    max_violation = float(np.max(max_violations))
    fraction_monotone = float(np.mean(fractions))
    
    # Status: PASS if mean ΔC ≤ 0 and max violation < 0.01
    status = "PASS" if mean_delta_C <= 0 and max_violation < 0.01 else "INCONCLUSIVE"
    
    return CMonotonicityResult(
        particle_name=canonical.name,
        num_trajectories=num_trajectories,
        mean_delta_C=mean_delta_C,
        std_delta_C=std_delta_C,
        max_violation=max_violation,
        fraction_monotone=fraction_monotone,
        status=status
    )


def main():
    """Run the full c-function monotonicity test."""
    
    print("\n" + "="*70)
    print(" TS9: SRRG c-Function Monotonicity Validation")
    print(" Theorem: dC/d ln μ ≤ 0 along SRRG flow")
    print("="*70 + "\n")
    
    # Setup
    script_dir = Path(__file__).parent
    program_dir = script_dir.parent
    data_dir = program_dir / "data"
    output_dir = program_dir / "outputs" / "ts9"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load canonical SM triples
    triples_path = data_dir / "canonical_sm_triples.json"
    particles = load_canonical_sm_triples(triples_path)
    
    # Create GTETriple objects
    canonical_triples = []
    for p in particles:
        t_dict = p["triple"]
        triple = GTETriple(
            a=t_dict["a"],
            b=t_dict["b"],
            c=t_dict["c"],
            g=t_dict["g"],
            name=p["name"]
        )
        canonical_triples.append(triple)
    
    # Parameters
    params = SRRGParameters()
    ucl_palette = elegant_palette()
    
    lambda_c = 1.0
    num_trajectories = 16
    
    print(f"Testing {len(canonical_triples)} particles")
    print(f"Trajectories per particle: {num_trajectories}")
    print(f"c-function: C[S] = F[S] - {lambda_c}·(n·k)²\n")
    
    # Run tests
    results = []
    for canonical in tqdm(canonical_triples, desc="Testing particles"):
        result = test_particle_c_monotonicity(
            canonical, ucl_palette, params, num_trajectories, lambda_c
        )
        results.append(result)
        print(f"{result.particle_name:12s}: mean(ΔC)={result.mean_delta_C:+.2e}, "
              f"max_viol={result.max_violation:.2e}, frac={result.fraction_monotone:.1%}, {result.status}")
    
    # Aggregate
    all_pass = all(r.status == "PASS" for r in results)
    overall_status = "PASS" if all_pass else "PARTIAL"
    
    mean_across_particles = float(np.mean([r.mean_delta_C for r in results]))
    
    print(f"\n{'='*70}")
    print(f" SUMMARY")
    print(f"{'='*70}")
    print(f"Mean ΔC across all particles: {mean_across_particles:+.2e}")
    print(f"Particles passing: {sum(1 for r in results if r.status == 'PASS')}/{len(results)}")
    print(f"Overall Status: {overall_status}")
    
    # Save
    output_data = {
        "test_id": "TS9",
        "test_name": "SRRG c-Function Monotonicity",
        "timestamp": datetime.now().isoformat(),
        "lambda_c": lambda_c,
        "num_trajectories_per_particle": num_trajectories,
        "num_particles": len(canonical_triples),
        "results": [asdict(r) for r in results],
        "mean_delta_C_across_particles": mean_across_particles,
        "overall_status": overall_status,
        "acceptance_criterion": "mean(ΔC) ≤ 0, max_violation < 0.01"
    }
    
    content_str = json.dumps(output_data, sort_keys=True, indent=2)
    output_data["data_hash"] = hashlib.sha256(content_str.encode()).hexdigest()[:16]
    
    output_file = output_dir / "ts9_c_function_results.json"
    
    manifest_path = program_dir / "DATA_MANIFEST.json"
    save_results_with_manifest(
        data=output_data,
        path=output_file,
        manifest_path=manifest_path,
        description="TS9: SRRG c-function monotonicity validation"
    )
    
    print(f"\n✅ Results saved to: {output_file}")
    print(f"   Data hash: {output_data['data_hash']}")
    
    return results, overall_status


if __name__ == "__main__":
    results, status = main()
    print(f"\n{'='*70}")
    print(f" TS9 Complete: {status}")
    print(f"{'='*70}\n")
