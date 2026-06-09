#!/usr/bin/env python3
"""
E11: PR-1C Coherence Emergence Test

Compare dissonance evolution across three systems:
1. Rule 110: Chaotic universal CA (baseline)
2. PR-1: Reversible + UGP, NO coherence bias
3. PR-1C: Reversible + UGP + EXPLICIT coherence bias (MDL/compression)

Hypothesis:
- Rule 110: D increases (chaotic)
- PR-1: D stable/increases (reversible but no coherence pressure)
- PR-1C: D DECREASES (coherence-biased, satisfies UGP Axiom 3)

This test validates that explicit coherence bias is NECESSARY and SUFFICIENT
for emergent coherence, and that PR-1C properly implements UGP Axiom 3 (MDL).
"""

import sys
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime
import json
from pathlib import Path

# Add PR-1 infrastructure to path (matching E6 pattern)
base_dir = Path(__file__).parent.parent  # ugp-physics repository root (MFRR/ → ugp-physics/)
pr1_root = base_dir / "PR-1_UGP_Loop_CA"
logos_search = pr1_root / "logos_search"
logos_experiment = logos_search / "logos_derivation_experiment"

sys.path.insert(0, str(logos_search))  # For pr1_core
sys.path.insert(0, str(pr1_root))  # For seed_strategies
sys.path.insert(0, str(logos_experiment / "src"))  # For executors, pr1_grid_2d

try:
    from pr1_core import PR1Grid, UGPSidechannels
    from unilogos_executor_configurable_v3 import ConfigurableUniLogosExecutor
    from seed_strategies import TwoClusterStrategy
    from pr1_grid_2d import PR1Grid2D
    print("✅ PR-1 infrastructure loaded")
except ImportError as e:
    print(f"❌ Error importing PR-1: {e}")
    sys.exit(1)

# Import PR-1C
try:
    from pr1c_coherence_aware_executor import PR1CCoherenceExecutor
    print("✅ PR-1C coherence executor loaded")
except ImportError as e:
    print(f"❌ Error importing PR-1C: {e}")
    sys.exit(1)


def calculate_dissonance_1d(grid: PR1Grid) -> float:
    """Dissonance for 1D grids (Rule 110, PR-1)."""
    kinks = np.sum(grid.m != np.roll(grid.m, 1))
    kink_density = kinks / len(grid.m)
    
    g_var = np.var(grid.g.astype(float)) / 16.0
    l_var = np.var(grid.l.astype(float)) / 64.0
    mu_std = np.std(grid.mu.astype(float)) / 2.0
    
    return kink_density + 0.5 * (g_var + l_var + mu_std)


def calculate_dissonance_2d(grid: PR1Grid2D) -> float:
    """Dissonance for 2D grids (PR-1C)."""
    kinks_h = np.sum(grid.m != np.roll(grid.m, 1, axis=0))
    kinks_v = np.sum(grid.m != np.roll(grid.m, 1, axis=1))
    kink_density = (kinks_h + kinks_v) / (2 * grid.size)
    
    g_var = np.var(grid.g.astype(float)) / 16.0
    l_var = np.var(grid.l.astype(float)) / 64.0
    mu_std = np.std(grid.mu.astype(float)) / 2.0
    
    return kink_density + 0.5 * (g_var + l_var + mu_std)


def rule110(state):
    """Rule 110 elementary cellular automaton."""
    new_state = np.zeros_like(state)
    n = len(state)
    for i in range(n):
        left = state[(i-1) % n]
        center = state[i]
        right = state[(i+1) % n]
        
        # Rule 110: 01101110 in binary
        pattern = (left << 2) | (center << 1) | right
        new_state[i] = (110 >> pattern) & 1
    
    return new_state


def test_rule110(grid_size=64, n_steps=500, seed=42):
    """Test Rule 110 (chaotic baseline)."""
    print(f"\n{'='*70}")
    print(f"  Rule 110: Chaotic Universal CA")
    print(f"{'='*70}")
    
    np.random.seed(seed)
    
    # Initialize with two clusters (matching PR-1 test)
    state = np.zeros(grid_size, dtype=int)
    cluster_size = grid_size // 8
    state[:cluster_size] = 1
    state[grid_size//2:grid_size//2 + cluster_size] = 1
    
    history = {'dissonance': [], 'kinks': [], 'density': []}
    
    print(f"Initial state: {np.sum(state)} ones, {grid_size - np.sum(state)} zeros")
    print(f"Evolving for {n_steps} steps...")
    
    for t in range(n_steps):
        # Compute metrics (treating state as m-field)
        kinks = np.sum(state != np.roll(state, 1))
        density = np.mean(state)
        
        # Simple dissonance: just kink density
        D = kinks / grid_size
        
        history['dissonance'].append(float(D))
        history['kinks'].append(int(kinks))
        history['density'].append(float(density))
        
        if t % 100 == 0:
            print(f"  Step {t:3d}: D={D:.4f}, kinks={kinks}, ρ={density:.3f}")
        
        # Evolve
        state = rule110(state)
    
    return history


def test_pr1_1d(grid_size=64, n_steps=500, seed=42):
    """Test PR-1 on 1D loop (reversible, no coherence bias)."""
    print(f"\n{'='*70}")
    print(f"  PR-1: Reversible 1D Loop (No Coherence Bias)")
    print(f"{'='*70}")
    
    # Initialize grid with two-cluster strategy (matching E6)
    grid = PR1Grid(grid_size)
    seed_strategy = TwoClusterStrategy(
        strategy_type="two_cluster",
        grid_size=grid_size,
        seed_number=seed,
        cluster1_density=0.6,
        cluster2_density=0.6,
        background_density=0.0
    )
    cells = seed_strategy.generate()
    for i, cell in enumerate(cells):
        grid.g[i] = cell.g
        grid.l[i] = cell.l
        grid.mu[i] = cell.mu
        grid.m[i] = cell.m
    
    # Initialize sidechannels
    sidechannels = UGPSidechannels.init_demo(grid_size)
    
    # Create executor (standard PR-1, no coherence)
    executor = ConfigurableUniLogosExecutor(grid_size=grid_size)
    executor.configure(
        x_transform='identity',
        r_mode='standard',
        s_mode='standard'
    )
    
    print(f"Initial: ρ={np.mean(grid.m):.3f}")
    print(f"Evolving for {n_steps} steps...")
    
    history = {'dissonance': [], 'kinks': [], 'density': []}
    sigma = np.ones(grid_size, dtype=int)
    
    for t in range(n_steps):
        D = calculate_dissonance_1d(grid)
        kinks = np.sum(grid.m != np.roll(grid.m, 1))
        density = np.mean(grid.m)
        
        history['dissonance'].append(float(D))
        history['kinks'].append(int(kinks))
        history['density'].append(float(density))
        
        if t % 100 == 0:
            print(f"  Step {t:3d}: D={D:.4f}, kinks={kinks}, ρ={density:.3f}")
        
        # Evolve
        executor.evolve_with_sigma(grid, sigma, sidechannels)
    
    return history


def test_pr1c_2d(grid_size=32, n_steps=500, seed=42):
    """Test PR-1C on 2D torus (reversible + coherence bias)."""
    print(f"\n{'='*70}")
    print(f"  PR-1C: Coherence-Aware 2D Torus")
    print(f"{'='*70}")
    
    np.random.seed(seed)
    
    # Initialize grid (two-cluster pattern)
    grid = PR1Grid2D(grid_size, grid_size)
    
    # Two clusters in 2D
    cluster_size = grid_size // 4
    for x in range(cluster_size):
        for y in range(cluster_size):
            grid.m[x, y] = 1
            grid.m[x + grid_size//2, y + grid_size//2] = 1
    
    # Random g, l, μ
    grid.g = np.random.randint(0, 4, size=(grid_size, grid_size), dtype=np.int8)
    grid.l = np.random.randint(0, 8, size=(grid_size, grid_size), dtype=np.int8)
    grid.mu = np.random.choice([0, 1, 2], size=(grid_size, grid_size)).astype(np.int8)
    
    print(f"Initial: ρ={np.mean(grid.m):.3f}, grid={grid_size}×{grid_size}")
    print(f"Evolving for {n_steps} steps with coherence bias...")
    
    # Create PR-1C executor
    executor = PR1CCoherenceExecutor(
        size_x=grid_size,
        size_y=grid_size,
        critical_density=0.34,
        neighborhood_radius=5,
        deterministic=True,
        alpha=2.0,
        beta=5.0,
        gamma=5.0,
        coherence_radius=3,  # Local coherence check
        ugp_seed=seed
    )
    
    n_cells = grid_size * grid_size
    sigma = np.ones(n_cells, dtype=int)
    ugp_ok = np.ones(n_cells, dtype=bool)
    
    history = {'dissonance': [], 'kinks': [], 'density': []}
    
    for t in range(n_steps):
        D = calculate_dissonance_2d(grid)
        kinks_h = np.sum(grid.m != np.roll(grid.m, 1, axis=0))
        kinks_v = np.sum(grid.m != np.roll(grid.m, 1, axis=1))
        kinks = int(kinks_h + kinks_v)
        density = np.mean(grid.m)
        
        history['dissonance'].append(float(D))
        history['kinks'].append(kinks)
        history['density'].append(float(density))
        
        if t % 100 == 0:
            print(f"  Step {t:3d}: D={D:.4f}, kinks={kinks}, ρ={density:.3f}")
        
        # Evolve with coherence awareness
        executor.evolve_step_coherent(grid, sigma, ugp_ok, timestep=t)
    
    # Print coherence stats
    executor.print_coherence_stats()
    
    return history


def create_comparison_plot(results, output_dir):
    """Create comparison plots."""
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    
    colors = {'rule110': 'red', 'pr1': 'blue', 'pr1c': 'green'}
    labels = {
        'rule110': 'Rule 110 (Chaotic)',
        'pr1': 'PR-1 (Reversible, No Bias)',
        'pr1c': 'PR-1C (Coherence-Aware)'
    }
    
    # Plot 1: Dissonance
    ax = axes[0]
    for name, hist in results.items():
        ax.plot(hist['dissonance'], label=labels[name], 
                color=colors[name], linewidth=2, alpha=0.8)
    ax.set_xlabel('Time Step', fontsize=12)
    ax.set_ylabel('Dissonance D(t)', fontsize=12)
    ax.set_title('Coherence Evolution', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(alpha=0.3)
    
    # Plot 2: Kinks
    ax = axes[1]
    for name, hist in results.items():
        ax.plot(hist['kinks'], label=labels[name], 
                color=colors[name], linewidth=2, alpha=0.8)
    ax.set_xlabel('Time Step', fontsize=12)
    ax.set_ylabel('Kink Count', fontsize=12)
    ax.set_title('Kink Evolution', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(alpha=0.3)
    
    # Plot 3: D change summary
    ax = axes[2]
    names = []
    changes = []
    bar_colors = []
    
    for name, hist in results.items():
        D_i = hist['dissonance'][0]
        D_f = hist['dissonance'][-1]
        D_pct = ((D_f - D_i) / D_i) * 100
        
        names.append(labels[name])
        changes.append(D_pct)
        
        if name == 'pr1c' and D_pct < -5:
            bar_colors.append('darkgreen')
        elif D_pct < 0:
            bar_colors.append('lightgreen')
        elif D_pct < 5:
            bar_colors.append('orange')
        else:
            bar_colors.append('red')
    
    bars = ax.bar(range(len(names)), changes, color=bar_colors, alpha=0.7, edgecolor='black')
    ax.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=15, ha='right')
    ax.set_ylabel('D Change (%)', fontsize=12)
    ax.set_title('Coherence Summary', fontsize=14, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    
    for bar, change in zip(bars, changes):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{change:+.1f}%',
                ha='center', va='bottom' if height > 0 else 'top',
                fontsize=11, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/comparison.png", dpi=150, bbox_inches='tight')
    print(f"✅ Plot: {output_dir}/comparison.png")
    plt.close()


def main():
    print("\n" + "="*70)
    print("  E11: PR-1C COHERENCE EMERGENCE TEST")
    print("  Comparing Rule 110, PR-1, and PR-1C")
    print("="*70)
    print("\nHypothesis:")
    print("  Rule 110: D ↑ (chaotic)")
    print("  PR-1:     D → (reversible, no coherence bias)")
    print("  PR-1C:    D ↓ (coherence-aware, UGP Axiom 3)")
    print()
    
    n_steps = 500
    seed = 42
    
    # Test all three systems
    results = {}
    
    # 1. Rule 110 (1D, chaotic)
    results['rule110'] = test_rule110(grid_size=64, n_steps=n_steps, seed=seed)
    
    # 2. PR-1 (1D, reversible, no coherence)
    results['pr1'] = test_pr1_1d(grid_size=64, n_steps=n_steps, seed=seed)
    
    # 3. PR-1C (2D, coherence-aware)
    results['pr1c'] = test_pr1c_2d(grid_size=32, n_steps=n_steps, seed=seed)
    
    # Analysis
    print("\n" + "="*70)
    print("  RESULTS SUMMARY")
    print("="*70)
    
    for name, hist in results.items():
        D_i = hist['dissonance'][0]
        D_f = hist['dissonance'][-1]
        D_pct = ((D_f - D_i) / D_i) * 100
        
        kinks_i = hist['kinks'][0]
        kinks_f = hist['kinks'][-1]
        
        if name == 'rule110':
            label = "Rule 110 (Chaotic)"
        elif name == 'pr1':
            label = "PR-1 (No Bias)"
        else:
            label = "PR-1C (Coherence)"
        
        if D_pct < -5:
            verdict = "✅✅ STRONG COHERENCE"
        elif D_pct < 0:
            verdict = "✅ COHERENCE"
        elif D_pct < 5:
            verdict = "⚠️ STABLE"
        else:
            verdict = "❌ DISORDER"
        
        print(f"\n{label}:")
        print(f"  D: {D_i:.4f} → {D_f:.4f} ({D_pct:+.1f}%)")
        print(f"  Kinks: {kinks_i} → {kinks_f}")
        print(f"  {verdict}")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"E11_pr1c_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    
    with open(f"{output_dir}/results.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Results saved: {output_dir}/results.json")
    
    # Create plots
    create_comparison_plot(results, output_dir)
    
    print("\n" + "="*70)
    print("  CONCLUSION")
    print("="*70)
    print("\nIf PR-1C shows D ↓ while Rule 110 and PR-1 show D ↑ or D →,")
    print("this validates that EXPLICIT coherence bias (UGP Axiom 3/MDL)")
    print("is NECESSARY for emergent coherence.")
    print("\nPR-1C is MORE UGP-compliant than vanilla PR-1, as it explicitly")
    print("implements the Compression/MDL axiom.")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()

