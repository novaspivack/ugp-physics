#!/usr/bin/env python3
"""
E7: 2D Torus D-Minimization Test (Edge-of-Chaos Configurations)

Test if PR-1 on 2D torus shows D-minimization (coherence emergence).

Comparison:
- E6 (1D loop): D increased +26.7% (NO coherence)
- E7 (2D torus): D = ? (HYPOTHESIS: decreases due to 8× richer interactions)

Theory:
- 1D: Each cell has 2 neighbors → spatially starved
- 2D: Each cell has 4 neighbors (8 with diagonals) → self-organization possible

Uses SESSION 16's edge-of-chaos configurations:
1. conway_like (ρ_c=0.3, γ=10.0) - Best persistence
2. structured_v4_zero_noise (ρ_c=0.25, γ=5.0) - Pure
3. structured_v1 (ρ_c=0.25, γ=5.0, ε=0.01) - Sparse

Reference: E6_pr1_coherence_emergence.py (1D baseline)
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np

# Add PR-1 torus infrastructure (paths relative to ugp-physics repository root)
_optimizer_tests = Path(__file__).resolve().parent.parent  # ugp-physics repository root
pr1_torus_path = str(_optimizer_tests / "PR-1_UGP_Loop_CA/logos_search/logos_derivation_experiment/src")
sys.path.insert(0, pr1_torus_path)

try:
    from pr1_grid_2d import PR1Grid2D, PR1Cell2D
    from torus_executor_elegant import TorusExecutorElegant
    print("✅ 2D Torus infrastructure loaded successfully\n")
except ImportError as e:
    print(f"❌ Error loading 2D torus infrastructure: {e}")
    sys.exit(1)


# ============================================================================
# DISSONANCE METRICS FOR 2D TORUS
# ============================================================================

def calculate_dissonance_2d(grid: PR1Grid2D) -> float:
    """
    Calculate dissonance proxy for 2D torus grid.
    
    Dissonance = kink density + field disorder
    Higher D = more disorder (less coherent)
    Lower D = more order (more coherent)
    """
    # Kink density (horizontal + vertical domain walls)
    kinks_h = np.sum(grid.m != np.roll(grid.m, 1, axis=0))  # Horizontal kinks
    kinks_v = np.sum(grid.m != np.roll(grid.m, 1, axis=1))  # Vertical kinks
    kink_density = (kinks_h + kinks_v) / (2 * grid.size)
    
    # Field disorder (variance of g, l, mu)
    g_variance = np.var(grid.g.astype(float)) / 16.0  # Normalize by Z4^2
    l_variance = np.var(grid.l.astype(float)) / 64.0  # Normalize by Z8^2
    mu_std = np.std(grid.mu.astype(float)) / 2.0     # Normalize by max range
    
    # Combined dissonance
    dissonance = kink_density + 0.5 * (g_variance + l_variance + mu_std)
    
    return dissonance


def calculate_metrics_2d(grid: PR1Grid2D) -> Dict:
    """Calculate comprehensive metrics for 2D grid."""
    metrics = {}
    
    # Kink metrics
    kinks_h = np.sum(grid.m != np.roll(grid.m, 1, axis=0))
    kinks_v = np.sum(grid.m != np.roll(grid.m, 1, axis=1))
    metrics['kinks_total'] = int(kinks_h + kinks_v)
    metrics['kink_density'] = float((kinks_h + kinks_v) / (2 * grid.size))
    
    # Field metrics
    metrics['m_density'] = float(np.mean(grid.m))
    metrics['g_entropy'] = float(-np.sum(np.bincount(grid.g.flatten(), minlength=4) / grid.size * 
                                  np.log(np.bincount(grid.g.flatten(), minlength=4) / grid.size + 1e-10)))
    metrics['l_entropy'] = float(-np.sum(np.bincount(grid.l.flatten(), minlength=8) / grid.size * 
                                  np.log(np.bincount(grid.l.flatten(), minlength=8) / grid.size + 1e-10)))
    
    # Dissonance
    metrics['dissonance'] = float(calculate_dissonance_2d(grid))
    
    return metrics


# ============================================================================
# 2D TORUS RUNNER (Edge-of-Chaos Configurations)
# ============================================================================

def run_torus_evolution(
    config_name: str,
    rho_c: float,
    alpha: float,
    beta: float,
    gamma: float,
    epsilon: float,
    grid_size: int = 32,
    n_steps: int = 200,
    seed: int = 42
) -> Dict:
    """
    Run 2D torus evolution with edge-of-chaos configuration.
    
    Args:
        config_name: Configuration identifier
        rho_c: Critical density
        alpha: Creation rate multiplier
        beta: Annihilation rate multiplier
        gamma: Sigmoid sharpness
        epsilon: Baseline noise level
        grid_size: Grid size (NxN)
        n_steps: Number of evolution steps
        seed: Random seed
    
    Returns:
        Dict with evolution history
    """
    print(f"\n" + "=" * 70)
    print(f"  2D TORUS TEST: {config_name}")
    print("=" * 70)
    print(f"Parameters: ρ_c={rho_c}, α={alpha}, β={beta}, γ={gamma}, ε={epsilon}")
    
    # Initialize grid with random 40% density
    np.random.seed(seed)
    grid = PR1Grid2D(grid_size, grid_size)
    
    # Random initialization (40% density)
    for x in range(grid_size):
        for y in range(grid_size):
            if np.random.random() < 0.4:
                grid.m[x, y] = 1
            grid.g[x, y] = np.random.randint(0, 4)
            grid.l[x, y] = np.random.randint(0, 8)
            grid.mu[x, y] = np.random.choice([0, 1, 2])
    
    actual_density = np.mean(grid.m)
    print(f"✅ Grid initialized: {grid_size}×{grid_size} = {grid.size} cells")
    print(f"   Random seed with 40% target density")
    print(f"   Actual m-field density: {actual_density:.3f}")
    
    # Create executor with edge-of-chaos parameters
    executor = TorusExecutorElegant(
        size_x=grid_size,
        size_y=grid_size,
        critical_density=rho_c,
        neighborhood_radius=5,
        deterministic=True,  # Use deterministic mode
        stochastic_source='ugp',  # UGP-based for consistency
        alpha=alpha,
        beta=beta,
        gamma=gamma,
        base_rate=epsilon,
        ugp_seed=seed
    )
    
    # Evolution history
    history = {
        'dissonance': [],
        'kink_density': [],
        'kinks_total': [],
        'm_density': [],
        'g_entropy': [],
        'l_entropy': []
    }
    
    # Initialize sigma and ugp_ok arrays (required by TorusExecutorElegant)
    n_cells = grid_size * grid_size
    sigma = np.ones(n_cells, dtype=int)
    ugp_ok = np.ones(n_cells, dtype=bool)
    
    print(f"\nEvolving for {n_steps} steps...")
    
    for t in range(n_steps):
        # Measure metrics
        metrics = calculate_metrics_2d(grid)
        history['dissonance'].append(metrics['dissonance'])
        history['kink_density'].append(metrics['kink_density'])
        history['kinks_total'].append(metrics['kinks_total'])
        history['m_density'].append(metrics['m_density'])
        history['g_entropy'].append(metrics['g_entropy'])
        history['l_entropy'].append(metrics['l_entropy'])
        
        if t % 50 == 0:
            print(f"  Step {t:4d}: D = {metrics['dissonance']:.4f}, kinks = {metrics['kinks_total']}")
        
        # Evolve one step
        chi_X, chi_S, is_kink = executor.evolve_step(grid, sigma, ugp_ok, timestep=t)
    
    return history


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def main():
    print("\n" + "=" * 70)
    print("  E7: 2D TORUS COHERENCE EMERGENCE TEST")
    print("  Edge-of-Chaos Configurations from SESSION 16")
    print("=" * 70)
    
    print("\nQUESTION TO TEST:")
    print("  Does 2D topology enable D-minimization (coherence)?")
    print("  1D loop: D +26.7% (NO coherence) ← E6 result")
    print("  2D torus: D = ? ← THIS TEST")
    print()
    
    # Test configurations (SESSION 16's edge-of-chaos winners)
    configs = [
        {
            'name': 'conway_like',
            'rho_c': 0.3,
            'alpha': 0.1,
            'beta': 5.0,
            'gamma': 10.0,
            'epsilon': 0.0,
            'description': 'Conway-like (best persistence: 0.963)'
        },
        {
            'name': 'structured_v4_zero_noise',
            'rho_c': 0.25,
            'alpha': 0.2,
            'beta': 3.0,
            'gamma': 5.0,
            'epsilon': 0.0,
            'description': 'Pure (zero noise, persistence: 0.958)'
        },
        {
            'name': 'structured_v1',
            'rho_c': 0.25,
            'alpha': 0.2,
            'beta': 3.0,
            'gamma': 5.0,
            'epsilon': 0.01,
            'description': 'Sparse, stable (persistence: 0.960)'
        }
    ]
    
    # Run all configurations
    results = {}
    for config in configs:
        print(f"\n{'─' * 70}")
        print(f"CONFIGURATION: {config['name']}")
        print(f"Description: {config['description']}")
        print(f"{'─' * 70}")
        
        history = run_torus_evolution(
            config_name=config['name'],
            rho_c=config['rho_c'],
            alpha=config['alpha'],
            beta=config['beta'],
            gamma=config['gamma'],
            epsilon=config['epsilon'],
            grid_size=32,
            n_steps=200,
            seed=42
        )
        
        results[config['name']] = {
            'config': config,
            'history': history
        }
    
    # Analyze results
    print("\n" + "=" * 70)
    print("  COHERENCE EMERGENCE ANALYSIS")
    print("=" * 70)
    
    print("\n1D BASELINE (E6):")
    print("   Initial D: 0.265")
    print("   Final D:   0.336")
    print("   Change:    +26.7%")
    print("   ❌ NO COHERENCE (D increased)")
    
    print("\n2D TORUS RESULTS:")
    for config in configs:
        name = config['name']
        hist = results[name]['history']
        
        D_initial = hist['dissonance'][0]
        D_final = hist['dissonance'][-1]
        D_change_pct = ((D_final - D_initial) / D_initial) * 100
        
        # Check for D-minimization
        if D_change_pct < 0:
            verdict = "✅ COHERENCE EMERGED (D decreased)"
            symbol = "✅"
        elif D_change_pct < 10:
            verdict = "⚠️ WEAK COHERENCE (D nearly stable)"
            symbol = "⚠️"
        else:
            verdict = "❌ NO COHERENCE (D increased)"
            symbol = "❌"
        
        print(f"\n{name}:")
        print(f"   Initial D: {D_initial:.4f}")
        print(f"   Final D:   {D_final:.4f}")
        print(f"   Change:    {D_change_pct:+.1f}%")
        print(f"   {verdict}")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"E7_torus_coherence_results_{timestamp}.json"
    
    # Convert numpy arrays to lists for JSON
    json_results = {}
    for name, data in results.items():
        json_results[name] = {
            'config': data['config'],
            'history': {k: [float(v) for v in vals] for k, vals in data['history'].items()}
        }
    
    with open(results_file, 'w') as f:
        json.dump(json_results, f, indent=2)
    
    print(f"\n✅ Results saved: {results_file}")
    
    # Create comparison plot
    create_comparison_plot(results, configs)
    
    print("\n" + "=" * 70)
    print("  FINAL VERDICT")
    print("=" * 70)
    
    # Determine if ANY configuration showed coherence
    any_coherence = any(
        (results[cfg['name']]['history']['dissonance'][-1] - 
         results[cfg['name']]['history']['dissonance'][0]) < 0
        for cfg in configs
    )
    
    if any_coherence:
        print("\n✅ CRITICAL FINDING:")
        print("   2D topology ENABLES coherence emergence!")
        print("   → Spatial richness (4-8 neighbors) allows self-organization")
        print("   → 1D loop is fundamentally limited (2 neighbors)")
        print("   → Reflexive Reality requires 2D+ substrate for coherence")
    else:
        print("\n❌ UNEXPECTED RESULT:")
        print("   2D topology ALSO shows no coherence")
        print("   → May need specific force laws or higher density")
        print("   → Or: PR-1 framework needs modification")


def create_comparison_plot(results: Dict, configs: List[Dict]):
    """Create comparison plot of D(t) evolution for all configurations."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Plot 1: Dissonance evolution (all configs)
    ax = axes[0, 0]
    for config in configs:
        name = config['name']
        hist = results[name]['history']
        ax.plot(hist['dissonance'], label=name, linewidth=2)
    ax.axhline(y=0.265, color='red', linestyle='--', alpha=0.5, label='1D initial')
    ax.axhline(y=0.336, color='red', linestyle=':', alpha=0.5, label='1D final')
    ax.set_xlabel('Time Step')
    ax.set_ylabel('Dissonance D(t)')
    ax.set_title('Dissonance Evolution: 2D Torus vs 1D Loop')
    ax.legend()
    ax.grid(alpha=0.3)
    
    # Plot 2: Kink density evolution
    ax = axes[0, 1]
    for config in configs:
        name = config['name']
        hist = results[name]['history']
        ax.plot(hist['kink_density'], label=name, linewidth=2)
    ax.set_xlabel('Time Step')
    ax.set_ylabel('Kink Density')
    ax.set_title('Kink Density Evolution')
    ax.legend()
    ax.grid(alpha=0.3)
    
    # Plot 3: Field entropy (g-field)
    ax = axes[1, 0]
    for config in configs:
        name = config['name']
        hist = results[name]['history']
        ax.plot(hist['g_entropy'], label=name, linewidth=2)
    ax.set_xlabel('Time Step')
    ax.set_ylabel('g-Field Entropy')
    ax.set_title('g-Field Entropy Evolution')
    ax.legend()
    ax.grid(alpha=0.3)
    
    # Plot 4: D change comparison (bar chart)
    ax = axes[1, 1]
    names = []
    changes = []
    colors = []
    
    # Add 1D baseline
    names.append('1D Loop\n(E6)')
    changes.append(26.7)
    colors.append('red')
    
    # Add 2D configs
    for config in configs:
        name = config['name']
        hist = results[name]['history']
        D_initial = hist['dissonance'][0]
        D_final = hist['dissonance'][-1]
        D_change_pct = ((D_final - D_initial) / D_initial) * 100
        
        names.append(name.replace('_', '\n'))
        changes.append(D_change_pct)
        colors.append('green' if D_change_pct < 0 else 'orange' if D_change_pct < 10 else 'red')
    
    bars = ax.bar(names, changes, color=colors, alpha=0.7, edgecolor='black')
    ax.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax.set_ylabel('D Change (%)')
    ax.set_title('Dissonance Change: 1D vs 2D Torus')
    ax.grid(axis='y', alpha=0.3)
    
    # Add value labels on bars
    for bar, change in zip(bars, changes):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{change:+.1f}%',
                ha='center', va='bottom' if height > 0 else 'top',
                fontsize=9, fontweight='bold')
    
    plt.tight_layout()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    plot_file = f"E7_torus_coherence_comparison_{timestamp}.png"
    plt.savefig(plot_file, dpi=150, bbox_inches='tight')
    print(f"✅ Comparison plot saved: {plot_file}")
    plt.close()


if __name__ == "__main__":
    main()

