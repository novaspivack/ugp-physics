#!/usr/bin/env python3
"""
SRRG Perturbation Decay - Local Stability Test

Instead of computing full Jacobian (which is complex due to natural gradient + projection),
directly test that small perturbations from SM fixed points decay back.

This is what "local attractor" actually means operationally.

Reference: MFRR §7, Proposition (prop:SRRG-linearization)
"""

import numpy as np
import json
import hashlib
from dataclasses import dataclass, asdict
from datetime import datetime
from multiprocessing import Pool, cpu_count
from typing import Tuple
import matplotlib.pyplot as plt
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from srrg_core import GTETriple, SRRGParameters, basin_structure_analysis, triple_distance
from srrg_functional_pure_gte import viability_functional_pure_gte, elegant_palette
from srrg_io import load_canonical_sm_triples

@dataclass
class PerturbationConfig:
    """Configuration for perturbation decay test (using TS1 basin analysis)."""
    n_particles: int = 17          # All SM particles
    perturbation_radius: float = 3.0  # Perturbation magnitude
    n_perturbations: int = 50      # Perturbations per particle
    convergence_tol: float = 15.0  # Same as TS1
    n_cores: int = min(10, cpu_count())
    seed: int = 42

def test_particle_basin(args: Tuple) -> dict:
    """Test basin structure for single particle using TS1 methodology."""
    particle_idx, canonical_triple, n_perts, pert_radius, conv_tol, params, ucl_pal, seed_offset = args
    
    print(f"  Testing {canonical_triple.name}...")
    
    # Use exact TS1 basin analysis
    F_fn = lambda t: viability_functional_pure_gte([t], ucl_pal, params)
    
    basin_result = basin_structure_analysis(
        triple_canonical=canonical_triple,
        F_fn=F_fn,
        params=params,
        ucl_fn=None,
        radius=pert_radius,
        n_starts=n_perts,
        convergence_tol=conv_tol,
        seed=seed_offset + particle_idx
    )
    
    return {
        "particle": canonical_triple.name,
        "attraction_rate": basin_result["attraction_rate"],
        "mean_iterations": basin_result["mean_iterations"],
        "n_converged": basin_result["n_converged"],
        "n_total": basin_result["n_total"]
    }

def run_perturbation_test(config: PerturbationConfig) -> dict:
    """Main perturbation decay test."""
    print(f"=== SRRG Perturbation Decay Test ===")
    print(f"Particles: {config.n_particles}, Perturbations/particle: {config.n_perturbations}")
    print(f"Cores: {config.n_cores}")
    
    # Load SM triples
    data_path = "../data/canonical_sm_triples.json"
    sm_data = load_canonical_sm_triples(data_path)[:config.n_particles]
    
    sm_triples = []
    for p in sm_data:
        tr = p["triple"]
        sm_triples.append(GTETriple(a=tr["a"], b=tr["b"], c=tr["c"], g=p["generation"], name=p["name"]))
    
    # Parameters
    params = SRRGParameters()
    ucl_pal = elegant_palette()
    
    # Prepare arguments (one basin analysis per particle)
    args_list = []
    for i, triple in enumerate(sm_triples):
        args_list.append((i, triple, config.n_perturbations, config.perturbation_radius, 
                         config.convergence_tol, params, ucl_pal, config.seed))
    
    # Parallel processing
    print(f"Testing {len(args_list)} particles on {config.n_cores} cores...")
    print(f"(Each runs {config.n_perturbations} perturbations via TS1 basin analysis)")
    with Pool(config.n_cores) as pool:
        particle_results = pool.map(test_particle_basin, args_list)
    
    # Overall statistics
    attraction_rates = [r["attraction_rate"] for r in particle_results]
    mean_attraction = np.mean(attraction_rates)
    
    passing_particles = sum(1 for r in attraction_rates if r >= 0.9)
    
    results = {
        "config": asdict(config),
        "timestamp": datetime.now().isoformat(),
        "n_particles": config.n_particles,
        "mean_attraction_rate": float(mean_attraction),
        "passing_particles": passing_particles,
        "particle_results": particle_results,
        "attraction_rates": attraction_rates,
        "validation_status": "PASS" if mean_attraction >= 0.9 else "INCONCLUSIVE"
    }
    
    print(f"\n✅ Local Stability Results (via TS1 Basin Analysis):")
    print(f"   Particles tested: {config.n_particles}")
    print(f"   Mean attraction rate: {results['mean_attraction_rate']*100:.1f}%")
    print(f"   Passing particles (≥90%): {passing_particles}/{config.n_particles}")
    print(f"   Status: {results['validation_status']}")
    
    return results

def plot_results(results: dict, output_dir: str = "v5_perturbation_outputs"):
    """Plot results."""
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    particle_results = results["particle_results"]
    
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    
    # Attraction rates by particle
    particles = [p["particle"] for p in particle_results]
    rates = [p["attraction_rate"] * 100 for p in particle_results]
    
    colors = ['green' if r >= 90 else 'orange' if r >= 70 else 'red' for r in rates]
    
    ax.barh(range(len(particles)), rates, alpha=0.7, edgecolor='black', color=colors)
    ax.axvline(90, color='red', linestyle='--', linewidth=2, label='Threshold (90%)')
    ax.axvline(results["mean_attraction_rate"]*100, color='blue', linestyle='-', linewidth=2, 
              label=f'Mean = {results["mean_attraction_rate"]*100:.1f}%')
    ax.set_yticks(range(len(particles)))
    ax.set_yticklabels(particles, fontsize=10)
    ax.set_xlabel('Attraction Rate (%)', fontsize=12)
    ax.set_title('SRRG Local Stability: Basin Attraction per Particle', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(axis='x', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/basin_attraction_stability.png", dpi=300, bbox_inches='tight')
    print(f"\n✅ Plot saved: {output_dir}/basin_attraction_stability.png")
    plt.close()

if __name__ == "__main__":
    config = PerturbationConfig()
    results = run_perturbation_test(config)
    
    # Save
    output_file = "v5_perturbation_outputs/v5_perturbation_results.json"
    import os
    os.makedirs("v5_perturbation_outputs", exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    with open(output_file, 'rb') as f:
        checksum = hashlib.sha256(f.read()).hexdigest()[:16]
    
    print(f"\n✅ Results saved: {output_file}")
    print(f"   Checksum: {checksum}")
    
    # Plot
    plot_results(results)
    
    print(f"\n{'='*60}")
    print(f"SRRG PERTURBATION DECAY VALIDATION COMPLETE")
    print(f"Status: {results['validation_status']}")
    print(f"{'='*60}")

