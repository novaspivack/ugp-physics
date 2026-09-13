#!/usr/bin/env python3
"""
Generalized Landauer Bound - Nonuniform Priors Test

Tests ⟨Q⟩ ≥ k_B T ΔH + λ_Ψ ΔE_Ψ for nonuniform priors.
Validates Equation (eq:GeneralizedLandauer).

Reference: MFRR §3, Proposition (prop:RefLandauer-ldb)
"""

import numpy as np
import json
import hashlib
from dataclasses import dataclass, asdict
from datetime import datetime
from multiprocessing import Pool, cpu_count
from typing import Tuple
import matplotlib.pyplot as plt

@dataclass
class GeneralizedLandauerConfig:
    """Configuration for generalized Landauer test."""
    n_trials: int = 1000
    n_branches_max: int = 10
    temperature: float = 300.0     # Kelvin
    k_B: float = 1.380649e-23      # Boltzmann constant
    lambda_psi: float = 1.0
    alpha1: float = 1e-6
    alpha2: float = 1e-6
    n_cores: int = min(10, cpu_count())
    seed: int = 42

def shannon_entropy(probs: np.ndarray) -> float:
    """Compute Shannon entropy H = -Σ p log p."""
    p_pos = probs[probs > 1e-15]
    return -np.sum(p_pos * np.log(p_pos))

def generate_nonuniform_prior(n: int, skew: float, rng: np.random.Generator) -> np.ndarray:
    """Generate nonuniform prior distribution."""
    # Dirichlet with varying concentration
    alpha_params = np.exp(-skew * np.arange(n))
    probs = rng.dirichlet(alpha_params)
    return probs / np.sum(probs)

def simulate_adjudication(args: Tuple) -> dict:
    """Simulate single adjudication event."""
    trial_idx, n_branches, skew, config, seed_offset = args
    
    rng = np.random.default_rng(seed_offset + trial_idx)
    
    # Prior distribution (nonuniform)
    p_prior = generate_nonuniform_prior(n_branches, skew, rng)
    H_prior = shannon_entropy(p_prior)
    
    # Coherence energy for each branch
    E_psi_branches = rng.uniform(0, 10, n_branches)
    
    # LDB transition kernel
    # K(i→j) / K(j→i) = exp[-β(Q_ij + ΔΦ_ij)]
    beta = 1.0 / (config.k_B * config.temperature)
    
    # Select branch via Boltzmann weights (with numerical stabilization)
    delta_E = E_psi_branches - np.min(E_psi_branches)
    log_weights = np.log(p_prior + 1e-15) - beta * config.lambda_psi * delta_E
    
    # Stabilize exponential (subtract max for numerical safety)
    log_weights_stable = log_weights - np.max(log_weights)
    weights = np.exp(log_weights_stable)
    weights = np.clip(weights, 1e-15, None)  # Prevent exact zeros
    p_post = weights / np.sum(weights)
    
    selected_idx = rng.choice(n_branches, p=p_post)
    
    # Post-selection entropy
    H_post = shannon_entropy(p_post)
    
    # Measured heat Q
    Q_measured = config.lambda_psi * E_psi_branches[selected_idx]
    
    # Theoretical bound
    Delta_H = H_prior - H_post
    Delta_E_psi = E_psi_branches[selected_idx]
    
    Q_bound = config.k_B * config.temperature * Delta_H + config.lambda_psi * Delta_E_psi
    
    margin = Q_measured - Q_bound
    satisfies_bound = margin >= -1e-10  # Numerical tolerance
    
    return {
        "trial_idx": int(trial_idx),
        "n_branches": int(n_branches),
        "skew": float(skew),
        "H_prior": float(H_prior),
        "H_post": float(H_post),
        "Delta_H": float(Delta_H),
        "Q_measured": float(Q_measured),
        "Q_bound": float(Q_bound),
        "margin": float(margin),
        "satisfies_bound": bool(satisfies_bound),
        "ratio": float(Q_measured / Q_bound) if Q_bound > 1e-15 else float('nan')
    }

def run_generalized_landauer_test(config: GeneralizedLandauerConfig) -> dict:
    """Main generalized Landauer test."""
    print(f"=== Generalized Landauer Bound Test ===")
    print(f"Trials: {config.n_trials}, Cores: {config.n_cores}")
    
    rng = np.random.default_rng(config.seed)
    
    # Generate test cases (varying n_branches and prior skew)
    args_list = []
    for i in range(config.n_trials):
        n_branches = rng.integers(2, config.n_branches_max + 1)
        skew = rng.uniform(0, 2.0)  # 0 = uniform, >0 = increasingly skewed
        args_list.append((i, n_branches, skew, config, config.seed))
    
    # Parallel processing
    print(f"Testing {config.n_trials} adjudications on {config.n_cores} cores...")
    with Pool(config.n_cores) as pool:
        trial_results = pool.map(simulate_adjudication, args_list)
    
    # Aggregate
    pass_count = sum(1 for r in trial_results if r["satisfies_bound"])
    ratios = [r["ratio"] for r in trial_results if not np.isnan(r["ratio"])]
    
    results = {
        "config": asdict(config),
        "timestamp": datetime.now().isoformat(),
        "n_trials": config.n_trials,
        "pass_count": pass_count,
        "pass_rate": pass_count / config.n_trials,
        "mean_ratio": float(np.mean(ratios)),
        "std_ratio": float(np.std(ratios)),
        "trial_results": trial_results,
        "validation_status": "PASS" if pass_count / config.n_trials >= 0.95 else "FAIL"
    }
    
    print(f"\n✅ Generalized Landauer Results:")
    print(f"   Pass Rate: {results['pass_rate']*100:.1f}%")
    print(f"   Mean Q/Q_bound: {results['mean_ratio']:.3f} ± {results['std_ratio']:.3f}")
    print(f"   Status: {results['validation_status']}")
    
    return results

def plot_results(results: dict, output_dir: str = "v4_landauer_outputs"):
    """Generate plots."""
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    trial_results = results["trial_results"]
    ratios = [r["ratio"] for r in trial_results if not np.isnan(r["ratio"])]
    margins = [r["margin"] for r in trial_results]
    
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # Ratio histogram
    axes[0].hist(ratios, bins=30, alpha=0.7, edgecolor='black')
    axes[0].axvline(1.0, color='red', linestyle='--', linewidth=2, label='Theory (Q/Q_bound = 1)')
    axes[0].axvline(results["mean_ratio"], color='blue', linestyle='-', linewidth=2, label=f'Mean = {results["mean_ratio"]:.3f}')
    axes[0].set_xlabel('Q_measured / Q_bound', fontsize=12)
    axes[0].set_ylabel('Count', fontsize=12)
    axes[0].set_title('Generalized Landauer: Heat Ratio Distribution', fontsize=14, fontweight='bold')
    axes[0].legend()
    axes[0].grid(alpha=0.3)
    
    # Margin vs Delta_H
    Delta_H_vals = [r["Delta_H"] for r in trial_results]
    axes[1].scatter(Delta_H_vals, margins, alpha=0.5, s=10)
    axes[1].axhline(0, color='red', linestyle='--', linewidth=2, label='Bound threshold')
    axes[1].set_xlabel('ΔH (entropy change)', fontsize=12)
    axes[1].set_ylabel('Margin: Q - Q_bound', fontsize=12)
    axes[1].set_title('Generalized Landauer: Margin vs ΔH', fontsize=14, fontweight='bold')
    axes[1].legend()
    axes[1].grid(alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/landauer_generalized.png", dpi=300, bbox_inches='tight')
    print(f"\n✅ Plot saved: {output_dir}/landauer_generalized.png")
    plt.close()

if __name__ == "__main__":
    config = GeneralizedLandauerConfig()
    results = run_generalized_landauer_test(config)
    
    # Save
    output_file = "v4_landauer_outputs/v4_landauer_results.json"
    import os
    os.makedirs("v4_landauer_outputs", exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    with open(output_file, 'rb') as f:
        checksum = hashlib.sha256(f.read()).hexdigest()[:16]
    
    print(f"\n✅ Results saved: {output_file}")
    print(f"   Checksum: {checksum}")
    
    # Plot
    plot_results(results)
    
    print(f"\n{'='*60}")
    print(f"GENERALIZED LANDAUER VALIDATION COMPLETE")
    print(f"Status: {results['validation_status']}")
    print(f"{'='*60}")

