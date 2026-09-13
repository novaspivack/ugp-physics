#!/usr/bin/env python3
"""
E28: Topology-Dependent Criticality
====================================

Tests that critical threshold J_c is determined by network topology through
spectral properties: J_c ∝ 1/λ_max(W)

Compares three network types:
- Erdős-Rényi (random): Baseline
- Watts-Strogatz (small-world): High clustering
- Barabási-Albert (scale-free): Hubs

Prediction: J_c ordering should be BA < WS < ER

Cross-reference:
    ADVANCED_ENSEMBLE_TESTS/docs/1_1_ADVANCED_ENSEMBLE_KICKOFF.md
    Mathematical_Foundations_of_Reflexive_Reality.tex (Synchronization Threshold Theorem)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
from numpy.random import default_rng
import json
import matplotlib.pyplot as plt
from multiprocessing import Pool
import time

from common.ensemble_core import (
    avalanche_update, compute_spectral_norm, 
    estimate_critical_point, compute_eigenspectrum
)
from common.graph_builders import (
    build_erdos_renyi, build_watts_strogatz, build_barabasi_albert,
    init_coupling_matrix, compute_graph_properties, match_edge_density
)


class E28Config:
    """Configuration for E28 topology test."""
    N = 2000               # Network size
    target_density = 0.004  # Target: mean degree ~ 8
    
    # Topologies to test
    topologies = ['ER', 'WS', 'BA']
    
    # Coupling sweep (coarse then fine near critical point)
    J_coarse = np.linspace(0.02, 0.30, 15)
    
    # Simulation per J
    n_cascades_per_J = 200
    max_iter = 800
    seed_fraction = 0.02
    
    n_cores = 8
    seed = 45


def run_topology_sweep(args):
    """Run cascade sweep for one topology type and one J value."""
    topology_type, J, cfg, task_seed = args
    
    rng = default_rng(task_seed)
    
    # Build graph based on topology
    if topology_type == 'ER':
        params = match_edge_density(cfg.N, cfg.target_density, 'erdos')
        A = build_erdos_renyi(params['N'], params['p'], rng)
        topo_name = 'Erdős-Rényi'
    elif topology_type == 'WS':
        params = match_edge_density(cfg.N, cfg.target_density, 'watts_strogatz')
        A = build_watts_strogatz(params['N'], params['k'], 0.3, rng)
        topo_name = 'Watts-Strogatz'
    elif topology_type == 'BA':
        params = match_edge_density(cfg.N, cfg.target_density, 'barabasi_albert')
        A = build_barabasi_albert(params['N'], params['m'], rng)
        topo_name = 'Barabási-Albert'
    else:
        raise ValueError(f"Unknown topology: {topology_type}")
    
    # Initialize coupling
    W = init_coupling_matrix(A, J, rng)
    W_norm = compute_spectral_norm(W, k=5)
    
    # Graph properties
    props = compute_graph_properties(A)
    
    # Run cascades
    b = rng.integers(0, 2, size=cfg.N)
    psi = rng.uniform(0.01, 0.1, size=cfg.N)
    bias = rng.uniform(0.0, 1.0, size=cfg.N)
    kappa = rng.uniform(0.1, 1.0, size=cfg.N)
    
    cascade_sizes = []
    
    for _ in range(cfg.n_cascades_per_J):
        size, _ = avalanche_update(
            W, b, psi, bias, kappa,
            max_iter=cfg.max_iter,
            seed_fraction=cfg.seed_fraction,
            rng=rng
        )
        if size > 0:
            cascade_sizes.append(size)
    
    mean_size = float(np.mean(cascade_sizes)) if cascade_sizes else 0.0
    std_size = float(np.std(cascade_sizes)) if cascade_sizes else 0.0
    max_size = int(np.max(cascade_sizes)) if cascade_sizes else 0
    
    return {
        'topology': topology_type,
        'topology_name': topo_name,
        'J': J,
        'W_norm': W_norm,
        'avg_degree': props['avg_degree'],
        'clustering': props['clustering_coeff'],
        'n_cascades': len(cascade_sizes),
        'mean_size': mean_size,
        'std_size': std_size,
        'max_size': max_size
    }


def analyze_criticality(results_by_topo, cfg, output_dir):
    """Analyze critical points for each topology."""
    print("\n" + "=" * 80)
    print("CRITICAL POINT ANALYSIS")
    print("=" * 80)
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # Plot 1: Mean cascade size vs J for all topologies
    ax1 = axes[0, 0]
    # Plot 2: Susceptibility (d<S>/dJ) for all topologies  
    ax2 = axes[0, 1]
    # Plot 3: Spectral norm vs J
    ax3 = axes[1, 0]
    # Plot 4: J_c vs lambda_max comparison
    ax4 = axes[1, 1]
    
    colors = {'ER': 'blue', 'WS': 'green', 'BA': 'red'}
    labels = {'ER': 'Erdős-Rényi', 'WS': 'Watts-Strogatz', 'BA': 'Barabási-Albert'}
    
    critical_points = {}
    
    for topo in cfg.topologies:
        data = results_by_topo[topo]
        J_vals = np.array([d['J'] for d in data])
        mean_sizes = np.array([d['mean_size'] for d in data])
        std_sizes = np.array([d['std_size'] for d in data])
        W_norms = np.array([d['W_norm'] for d in data])
        
        # Sort by J
        idx = np.argsort(J_vals)
        J_vals = J_vals[idx]
        mean_sizes = mean_sizes[idx]
        std_sizes = std_sizes[idx]
        W_norms = W_norms[idx]
        
        # Plot mean cascade size
        ax1.errorbar(J_vals, mean_sizes, yerr=std_sizes, 
                    fmt='o-', label=labels[topo], color=colors[topo],
                    capsize=3, linewidth=2, markersize=6)
        
        # Compute and plot susceptibility
        if len(J_vals) > 1:
            susceptibility = np.gradient(mean_sizes, J_vals)
            ax2.plot(J_vals, susceptibility, 'o-', label=labels[topo],
                    color=colors[topo], linewidth=2, markersize=6)
        
        # Plot spectral norm
        ax3.plot(J_vals, W_norms, 'o-', label=labels[topo],
                color=colors[topo], linewidth=2, markersize=6)
        
        # Estimate critical point
        crit = estimate_critical_point(J_vals, mean_sizes)
        critical_points[topo] = crit
        
        # Mark critical point on plots
        if not np.isnan(crit['J_c']):
            ax1.axvline(crit['J_c'], color=colors[topo], linestyle='--', alpha=0.5)
            ax2.axvline(crit['J_c'], color=colors[topo], linestyle='--', alpha=0.5)
        
        print(f"\n{labels[topo]}:")
        print(f"  Average degree: {data[0]['avg_degree']:.2f}")
        print(f"  Clustering: {data[0]['clustering']:.4f}")
        print(f"  Estimated J_c: {crit['J_c']:.4f} ± {crit['uncertainty']:.4f}")
        print(f"  Max susceptibility: {crit['max_susceptibility']:.2f}")
        
        # Get spectral norm at J_c
        J_c_idx = np.argmin(np.abs(J_vals - crit['J_c']))
        lambda_max_at_Jc = W_norms[J_c_idx]
        print(f"  ||W||₂ at J_c: {lambda_max_at_Jc:.4f}")
        
        # Plot on J_c vs lambda_max
        if not np.isnan(crit['J_c']):
            ax4.scatter(lambda_max_at_Jc, crit['J_c'], s=200, 
                       color=colors[topo], marker='o', 
                       label=labels[topo], edgecolors='black', linewidths=2)
    
    # Format plots
    ax1.set_xlabel('Coupling Strength $J$', fontsize=12)
    ax1.set_ylabel('Mean Cascade Size $\\langle S \\rangle$', fontsize=12)
    ax1.set_title('Phase Transition: Cascade Size vs Coupling', fontsize=13)
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)
    
    ax2.set_xlabel('Coupling Strength $J$', fontsize=12)
    ax2.set_ylabel('Susceptibility $d\\langle S \\rangle / dJ$', fontsize=12)
    ax2.set_title('Critical Point Detection', fontsize=13)
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)
    
    ax3.set_xlabel('Coupling Strength $J$', fontsize=12)
    ax3.set_ylabel('Spectral Norm $||W||_2$', fontsize=12)
    ax3.set_title('Spectral Norm vs Coupling', fontsize=13)
    ax3.legend(fontsize=10)
    ax3.grid(True, alpha=0.3)
    
    ax4.set_xlabel('$||W||_2$ at $J_c$', fontsize=12)
    ax4.set_ylabel('Critical Coupling $J_c$', fontsize=12)
    ax4.set_title('Spectral Control of Criticality', fontsize=13)
    ax4.legend(fontsize=10)
    ax4.grid(True, alpha=0.3)
    
    # Theoretical prediction: J_c ~ 1/lambda_max
    if len(critical_points) > 0:
        lambda_vals = []
        Jc_vals = []
        for topo in cfg.topologies:
            cp = critical_points[topo]
            if not np.isnan(cp['J_c']):
                data = results_by_topo[topo]
                J_vals = np.array([d['J'] for d in data])
                W_norms = np.array([d['W_norm'] for d in data])
                idx = np.argmin(np.abs(J_vals - cp['J_c']))
                lambda_vals.append(W_norms[idx])
                Jc_vals.append(cp['J_c'])
        
        if len(lambda_vals) > 0:
            lambda_vals = np.array(lambda_vals)
            Jc_vals = np.array(Jc_vals)
            
            # Fit J_c = a / lambda_max
            a_fit = np.mean(Jc_vals * lambda_vals)
            lambda_fit = np.linspace(min(lambda_vals), max(lambda_vals), 50)
            Jc_fit = a_fit / lambda_fit
            
            ax4.plot(lambda_fit, Jc_fit, 'k--', linewidth=2, alpha=0.6,
                    label=f'$J_c \\propto 1/\\lambda_{{max}}$')
            ax4.legend(fontsize=10)
    
    plt.tight_layout()
    fig_path = output_dir / 'e28_topology_criticality.png'
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    print(f"\n✓ Figure saved: {fig_path}")
    plt.close()
    
    return critical_points


def main():
    """Run E28: Topology-dependent criticality test."""
    cfg = E28Config()
    
    print("=" * 80)
    print("E28: TOPOLOGY-DEPENDENT CRITICALITY")
    print("=" * 80)
    print(f"Network size: N = {cfg.N}")
    print(f"Target density: ⟨k⟩/N ≈ {cfg.target_density:.4f}")
    print(f"Topologies: {cfg.topologies}")
    print(f"Coupling sweep: J ∈ [{cfg.J_coarse[0]:.2f}, {cfg.J_coarse[-1]:.2f}] ({len(cfg.J_coarse)} points)")
    print(f"Cascades per point: {cfg.n_cascades_per_J}")
    print(f"Parallelization: {cfg.n_cores} cores")
    print("=" * 80)
    print("\n🎯 HYPOTHESIS: J_c ordering should be BA < WS < ER (spectral control)")
    print("=" * 80)
    
    # Prepare tasks (all topology × J combinations)
    tasks = []
    task_id = 0
    for topo in cfg.topologies:
        for J in cfg.J_coarse:
            tasks.append((topo, J, cfg, cfg.seed + task_id))
            task_id += 1
    
    print(f"\nLaunching {len(tasks)} simulations...")
    
    start_time = time.time()
    
    with Pool(cfg.n_cores) as pool:
        results = pool.map(run_topology_sweep, tasks)
    
    elapsed = time.time() - start_time
    print(f"\nAll simulations complete in {elapsed/60:.1f} minutes")
    
    # Group by topology
    results_by_topo = {topo: [] for topo in cfg.topologies}
    for r in results:
        results_by_topo[r['topology']].append(r)
    
    # Create output directory
    output_dir = Path(__file__).parent.parent / 'outputs' / 'e28_outputs'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Analyze
    critical_points = analyze_criticality(results_by_topo, cfg, output_dir)
    
    # Final summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY: TOPOLOGY-DEPENDENT CRITICALITY")
    print("=" * 80)
    
    print("\nCritical Coupling Values:")
    Jc_values = {}
    for topo in cfg.topologies:
        cp = critical_points[topo]
        Jc_values[topo] = cp['J_c']
        print(f"  {topo}: J_c = {cp['J_c']:.4f} ± {cp['uncertainty']:.4f}")
    
    # Check ordering
    print("\nPredicted ordering: J_c(BA) < J_c(WS) < J_c(ER)")
    print(f"Observed ordering:  J_c(BA)={Jc_values['BA']:.3f} "
          f"{'<' if Jc_values['BA'] < Jc_values['WS'] else '>'} "
          f"J_c(WS)={Jc_values['WS']:.3f} "
          f"{'<' if Jc_values['WS'] < Jc_values['ER'] else '>'} "
          f"J_c(ER)={Jc_values['ER']:.3f}")
    
    correct_ordering = (Jc_values['BA'] < Jc_values['WS'] < Jc_values['ER'])
    
    if correct_ordering:
        print("\n✅ HYPOTHESIS CONFIRMED: Spectral properties control criticality!")
    else:
        print("\n⚠️  Ordering differs from prediction (may need more statistics)")
    
    # Save results
    output_data = {
        'config': {
            'N': cfg.N,
            'target_density': cfg.target_density,
            'J_sweep': cfg.J_coarse.tolist(),
            'topologies': cfg.topologies
        },
        'critical_points': {k: v for k, v in critical_points.items()},
        'results_by_topology': {
            k: v[:5]  # Save sample only
            for k, v in results_by_topo.items()
        }
    }
    
    results_file = output_dir / 'e28_results.json'
    with open(results_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n✓ Results saved: {results_file}")
    print("\n" + "=" * 80)
    print("E28 COMPLETE")
    print("=" * 80)


if __name__ == '__main__':
    main()

