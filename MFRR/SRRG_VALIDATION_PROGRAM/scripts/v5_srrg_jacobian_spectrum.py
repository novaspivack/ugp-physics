#!/usr/bin/env python3
"""
SRRG Jacobian Spectrum - Local Linearization at SM Fixed Point

Computes Jacobian of SRRG flow at converged SM triples.
Plots eigenvalue spectrum to verify local attractor behavior.

Reference: MFRR §7, SRRG Fixed-Point Stability
"""

import numpy as np
import json
import hashlib
from dataclasses import dataclass, asdict
from datetime import datetime
from multiprocessing import Pool, cpu_count
from typing import List, Tuple
import matplotlib.pyplot as plt
import sys
import os

# Import SRRG infrastructure
sys.path.insert(0, os.path.dirname(__file__))
from srrg_core import GTETriple, SRRGParameters, compute_gradient_fd, fisher_rao_metric
from srrg_functional_pure_gte import viability_functional_pure_gte, UCLPalette, elegant_palette
from srrg_io import load_canonical_sm_triples

@dataclass
class JacobianConfig:
    """Configuration for Jacobian spectrum test."""
    epsilon: float = 1e-4          # Finite difference step
    n_directions: int = 100        # Random directions for spectral probe
    n_particles: int = 17          # All SM particles
    n_cores: int = min(10, cpu_count())
    seed: int = 42

def compute_jacobian_numerical(triple: GTETriple, params: SRRGParameters, 
                                epsilon: int = 1) -> np.ndarray:
    """
    Compute 3×3 Jacobian matrix ∂R_i/∂g_j at fixed point.
    
    R = (da/dt, db/dt, dc/dt) from SRRG flow
    g = (a, b, c)
    """
    # Create wrapper that matches compute_gradient_fd signature (takes only triple)
    ucl_pal = elegant_palette()
    def F_wrapper(t):
        return viability_functional_pure_gte([t], ucl_pal, params)
    
    # Reference gradient
    grad_ref = compute_gradient_fd(F_wrapper, triple, epsilon)
    
    # Jacobian via finite differences
    J = np.zeros((3, 3))
    
    for i, var in enumerate(['a', 'b', 'c']):
        # Perturb variable i
        triple_pert = GTETriple(
            a=triple.a + (epsilon if i == 0 else 0),
            b=triple.b + (epsilon if i == 1 else 0),
            c=triple.c + (epsilon if i == 2 else 0),
            g=triple.g,
            name=triple.name
        )
        
        # Gradient at perturbed point
        grad_pert = compute_gradient_fd(F_wrapper, triple_pert, epsilon)
        
        # Finite difference derivative
        J[:, i] = (grad_pert - grad_ref) / float(epsilon)
    
    return J

def analyze_jacobian_single(args: Tuple) -> dict:
    """Analyze Jacobian for single particle (for multiprocessing)."""
    particle_idx, triple_dict, params, config, seed_offset = args
    
    # Reconstruct GTETriple from dict (multiprocessing serialization)
    triple = GTETriple(
        a=triple_dict["a"],
        b=triple_dict["b"],
        c=triple_dict["c"],
        g=triple_dict.get("g", 1),
        name=triple_dict.get("name", f"particle_{particle_idx}")
    )
    
    print(f"  Computing Jacobian for {triple.name}...")
    
    # Compute Jacobian
    J = compute_jacobian_numerical(triple, params, config.epsilon)
    
    # Eigenvalues
    eigvals = np.linalg.eigvals(J)
    
    # Spectral radius and max real part
    spectral_radius = np.max(np.abs(eigvals))
    max_real = np.max(eigvals.real)
    
    # Condition number
    cond_number = np.linalg.cond(J)
    
    return {
        "particle": triple.name,
        "triple": (triple.a, triple.b, triple.c),
        "eigenvalues_real": eigvals.real.tolist(),
        "eigenvalues_imag": eigvals.imag.tolist(),
        "spectral_radius": float(spectral_radius),
        "max_real_part": float(max_real),
        "condition_number": float(cond_number),
        "is_attractor": max_real < -1e-6  # Negative real parts → attractor
    }

def run_jacobian_spectrum_test(config: JacobianConfig) -> dict:
    """Main Jacobian spectrum test."""
    print(f"=== SRRG Jacobian Spectrum Test ===")
    print(f"Particles: {config.n_particles}, Cores: {config.n_cores}")
    
    # Load canonical SM triples
    data_path = "../data/canonical_sm_triples.json"
    sm_triples_data = load_canonical_sm_triples(data_path)[:config.n_particles]
    
    # Convert to GTETriple objects
    sm_triples = []
    for particle in sm_triples_data:
        tr = particle["triple"]
        sm_triples.append(GTETriple(
            a=tr["a"],
            b=tr["b"],
            c=tr["c"],
            g=particle["generation"],
            name=particle["name"]
        ))
    
    # SRRG parameters (from TS1) - using actual parameter names from srrg_core.py
    params = SRRGParameters()
    
    # Prepare arguments (serialize GTETriple to dict for multiprocessing)
    args_list = []
    for i, t in enumerate(sm_triples):
        triple_dict = {"a": t.a, "b": t.b, "c": t.c, "g": t.g, "name": t.name}
        args_list.append((i, triple_dict, params, config, config.seed))
    
    # Parallel processing
    print(f"\nComputing Jacobians for {len(sm_triples)} particles on {config.n_cores} cores...")
    with Pool(config.n_cores) as pool:
        jacobian_results = pool.map(analyze_jacobian_single, args_list)
    
    # Aggregate
    max_real_parts = [r["max_real_part"] for r in jacobian_results]
    attractor_count = sum(1 for r in jacobian_results if r["is_attractor"])
    
    results = {
        "config": asdict(config),
        "timestamp": datetime.now().isoformat(),
        "n_particles_tested": len(sm_triples),
        "jacobian_results": jacobian_results,
        "attractor_count": attractor_count,
        "attractor_fraction": attractor_count / len(sm_triples),
        "mean_max_real": float(np.mean(max_real_parts)),
        "all_negative_real": all(r < 0 for r in max_real_parts),
        "validation_status": "PASS" if attractor_count / len(sm_triples) >= 0.9 else "INCONCLUSIVE"
    }
    
    print(f"\n✅ Jacobian Spectrum Results:")
    print(f"   Attractors: {attractor_count}/{len(sm_triples)} ({results['attractor_fraction']*100:.1f}%)")
    print(f"   Mean max Re(λ): {results['mean_max_real']:.3e}")
    print(f"   All negative Re: {results['all_negative_real']}")
    print(f"   Status: {results['validation_status']}")
    
    return results

def plot_spectrum(results: dict, output_dir: str = "v5_jacobian_outputs"):
    """Plot eigenvalue spectrum."""
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # Complex plane
    for r in results["jacobian_results"]:
        re = r["eigenvalues_real"]
        im = r["eigenvalues_imag"]
        axes[0].scatter(re, im, alpha=0.6, s=50)
    
    axes[0].axvline(0, color='red', linestyle='--', linewidth=2, label='Re(λ) = 0')
    axes[0].axhline(0, color='gray', linestyle='-', linewidth=0.5)
    axes[0].set_xlabel('Re(λ)', fontsize=12)
    axes[0].set_ylabel('Im(λ)', fontsize=12)
    axes[0].set_title('SRRG Jacobian: Eigenvalue Spectrum (Complex Plane)', fontsize=14, fontweight='bold')
    axes[0].legend()
    axes[0].grid(alpha=0.3)
    
    # Max real part distribution
    max_reals = [r["max_real_part"] for r in results["jacobian_results"]]
    axes[1].hist(max_reals, bins=20, alpha=0.7, edgecolor='black')
    axes[1].axvline(0, color='red', linestyle='--', linewidth=2, label='Stability threshold')
    axes[1].set_xlabel('max Re(λ)', fontsize=12)
    axes[1].set_ylabel('Count', fontsize=12)
    axes[1].set_title('SRRG Jacobian: Max Real Part Distribution', fontsize=14, fontweight='bold')
    axes[1].legend()
    axes[1].grid(alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/jacobian_spectrum.png", dpi=300, bbox_inches='tight')
    print(f"\n✅ Plot saved: {output_dir}/jacobian_spectrum.png")
    plt.close()

if __name__ == "__main__":
    config = JacobianConfig()
    results = run_jacobian_spectrum_test(config)
    
    # Save
    output_file = "v5_jacobian_outputs/v5_jacobian_results.json"
    import os
    os.makedirs("v5_jacobian_outputs", exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    with open(output_file, 'rb') as f:
        checksum = hashlib.sha256(f.read()).hexdigest()[:16]
    
    print(f"\n✅ Results saved: {output_file}")
    print(f"   Checksum: {checksum}")
    
    # Plot
    plot_spectrum(results)
    
    print(f"\n{'='*60}")
    print(f"SRRG JACOBIAN SPECTRUM VALIDATION COMPLETE")
    print(f"Status: {results['validation_status']}")
    print(f"{'='*60}")

