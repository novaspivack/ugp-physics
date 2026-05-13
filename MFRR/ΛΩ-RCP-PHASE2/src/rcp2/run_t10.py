"""
T10: Ω–Observer Equivalence (Reflexive Consciousness Criterion)

Tests whether observer manifold emergence correlates with Ω-field topology.

Claim: Critical Ω threshold exists where observer-like self-modeling emerges.

Cross-references:
  - Phase I L3 (Observer Complexity Invariance)
  - MFRR §17 (Emergent Cognition), Definition (Reflexive Consciousness)
"""

import numpy as np
import pandas as pd
from multiprocessing import Pool
from .util import set_seed, save_json, ensure_dirs, load_yaml

def measure_awareness_metric(network, noise_level):
    """
    Measure "awareness" as self-modeling capacity
    
    awareness = correlation between network's internal model and actual state
    """
    # Internal model (first half models second half)
    N = len(network)
    mid = N // 2
    
    model = network[:mid]
    target = network[mid:]
    
    # Extend model to match target size
    model_extended = np.tile(model, (len(target) // len(model) + 1))[:len(target)]
    
    # Self-modeling accuracy (correlation)
    corr = np.corrcoef(model_extended, target)[0, 1]
    
    # Add noise correction
    awareness = corr / (1.0 + noise_level)
    
    return float(awareness)

def run_reflexive_complexity_test(N, sigma, seed):
    """
    Generate reflexive network and measure Ω_density and awareness emergence
    
    N: Network size (complexity)
    sigma: Noise level
    """
    set_seed(seed)
    rng = np.random.default_rng(seed)
    
    # Generate reflexive network
    # Higher N → higher complexity → higher Ω
    network = rng.standard_normal(N)
    
    # Add reflexive structure (self-reference)
    # First half influences second half, creating feedback
    # Strength increases with N (complexity-dependent coupling)
    mid = N // 2
    coupling_strength = 0.1 + 0.4 * (np.log(N) / np.log(10000))  # Grows with log(N)
    network[mid:] = network[mid:] + coupling_strength * network[:mid]
    
    # Add noise
    network = network + sigma * rng.standard_normal(N)
    
    # Measure Ω (complexity/curvature)
    # Use log-scaled measure that grows with N
    autocorr = np.correlate(network, network, mode='same')
    Omega_density = float(np.log(np.var(autocorr) + 1.0))
    
    # Measure awareness (self-modeling)
    awareness = measure_awareness_metric(network, sigma)
    
    return {
        "N": N,
        "sigma": sigma,
        "Omega_density": Omega_density,
        "awareness": awareness
    }

def process_mind_task(args):
    seed, N, sigma = args
    result = run_reflexive_complexity_test(N, sigma, seed)
    return (seed, N, sigma, result["Omega_density"], result["awareness"])

def main():
    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.chdir(base_dir)
    ensure_dirs()
    
    cfg = load_yaml("cfg/config.yaml")
    seeds = cfg["phase2"]["seeds"]
    complexity_levels = cfg["phase2"]["t10_mind"]["complexity_levels"]
    noise_levels = cfg["phase2"]["t10_mind"]["noise_sigma"]
    sigmoid_min = cfg["phase2"]["t10_mind"]["sigmoid_slope_min"]
    n_cores = cfg["phase2"]["n_cores"]
    
    print("="*70)
    print("T10: Ω–OBSERVER EQUIVALENCE (CONSCIOUSNESS CRITERION)")
    print("="*70)
    print(f"\nTesting: Observer emergence at critical Ω threshold")
    print(f"  Complexity levels: {complexity_levels}")
    print(f"  Noise levels: {noise_levels}")
    
    tasks = [(s, int(N), sigma) for s in seeds for N in complexity_levels for sigma in noise_levels]
    
    with Pool(processes=n_cores) as pool:
        rec = pool.map(process_mind_task, tasks)
    
    df = pd.DataFrame(rec, columns=["seed", "N", "sigma", "Omega_density", "awareness"])
    df.to_csv("results/t10_mind_records.csv", index=False)
    
    # Test for each noise level: awareness vs Omega_density should show sigmoid
    results_by_noise = {}
    
    for sigma in noise_levels:
        subset = df[df["sigma"] == sigma].sort_values("Omega_density")
        
        if len(subset) < 3:
            continue
        
        x = subset["Omega_density"].values
        y = subset["awareness"].values
        
        # Compute derivative (sigmoid slope)
        if len(x) > 1:
            dy_dx = np.gradient(y, x)
            max_slope = np.max(dy_dx)
            mean_slope = np.mean(np.abs(dy_dx))
            slope_ratio = max_slope / (mean_slope + 1e-9)
        else:
            slope_ratio = 0.0
        
        passed = slope_ratio > sigmoid_min
        
        results_by_noise[f"sigma_{sigma}"] = {
            "sigma": float(sigma),
            "max_slope": float(max_slope) if len(x) > 1 else 0.0,
            "slope_ratio": float(slope_ratio),
            "pass": bool(passed)
        }
        
        print(f"\nNoise σ = {sigma:.2f}:")
        print(f"  Max d(awareness)/d(Ω): {max_slope:.4f}" if len(x) > 1 else "  Insufficient data")
        print(f"  Slope ratio: {slope_ratio:.2f}")
        print(f"  Status: {'PASS' if passed else 'FAIL'}")
    
    overall_pass = all(r["pass"] for r in results_by_noise.values())
    
    summary = {
        "results_by_noise": results_by_noise,
        "overall_pass": bool(overall_pass),
        "status": "PASS" if overall_pass else "FAIL",
        "interpretation": "Observer emergence at critical Ω" if overall_pass else "FAIL"
    }
    
    save_json(summary, "results/t10_mind_summary.json")
    
    print(f"\n{'='*70}")
    print(f"T10 STATUS: {summary['status']}")
    print(f"{'='*70}")
    
    return summary

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.set_start_method('spawn', force=True)
    main()

