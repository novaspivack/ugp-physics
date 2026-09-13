#!/usr/bin/env python3
"""
E8: 2D Torus Rich Structures Test (User-Approved Configurations)

Test the configurations that showed "complex closed shapes (ellipses, tubes)"
from SESSION 16.4 - Critical Threshold Search.

User feedback: ρ_c = 0.34-0.38 showed the most interesting dynamics.

Parameters (fully deterministic):
- ρ_c = 0.34, 0.36, 0.38
- α = 0.2 (low creation)
- β = 3.0 (high annihilation)
- γ = 5.0 (moderate sharpness)
- ε = 0.0 (ZERO noise - fully deterministic!)

Question: Do these visually rich configurations also show D-minimization?

Reference: 
- E7 (edge-of-chaos) showed D stability but less visual richness
- SESSION_16_4 critical threshold search showed these had best structures
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np

# Add PR-1 torus infrastructure (paths relative to ugp-physics repository root)
_optimizer_tests = Path(__file__).resolve().parent.parent  # ugp-physics repository root
pr1_torus_path = str(_optimizer_tests / "PR-1_UGP_Loop_CA/logos_search/logos_derivation_experiment/src")
sys.path.insert(0, pr1_torus_path)

try:
    from pr1_grid_2d import PR1Grid2D
    from torus_executor_elegant import TorusExecutorElegant
    print("✅ 2D Torus infrastructure loaded successfully\n")
except ImportError as e:
    print(f"❌ Error loading 2D torus infrastructure: {e}")
    sys.exit(1)


# ============================================================================
# DISSONANCE METRICS (same as E7)
# ============================================================================

def calculate_dissonance_2d(grid: PR1Grid2D) -> float:
    """Calculate dissonance proxy for 2D torus grid."""
    kinks_h = np.sum(grid.m != np.roll(grid.m, 1, axis=0))
    kinks_v = np.sum(grid.m != np.roll(grid.m, 1, axis=1))
    kink_density = (kinks_h + kinks_v) / (2 * grid.size)
    
    g_variance = np.var(grid.g.astype(float)) / 16.0
    l_variance = np.var(grid.l.astype(float)) / 64.0
    mu_std = np.std(grid.mu.astype(float)) / 2.0
    
    dissonance = kink_density + 0.5 * (g_variance + l_variance + mu_std)
    return dissonance


def calculate_metrics_2d(grid: PR1Grid2D) -> Dict:
    """Calculate comprehensive metrics for 2D grid."""
    metrics = {}
    
    kinks_h = np.sum(grid.m != np.roll(grid.m, 1, axis=0))
    kinks_v = np.sum(grid.m != np.roll(grid.m, 1, axis=1))
    metrics['kinks_total'] = int(kinks_h + kinks_v)
    metrics['kink_density'] = float((kinks_h + kinks_v) / (2 * grid.size))
    
    metrics['m_density'] = float(np.mean(grid.m))
    metrics['g_entropy'] = float(-np.sum(np.bincount(grid.g.flatten(), minlength=4) / grid.size * 
                                  np.log(np.bincount(grid.g.flatten(), minlength=4) / grid.size + 1e-10)))
    metrics['l_entropy'] = float(-np.sum(np.bincount(grid.l.flatten(), minlength=8) / grid.size * 
                                  np.log(np.bincount(grid.l.flatten(), minlength=8) / grid.size + 1e-10)))
    
    metrics['dissonance'] = float(calculate_dissonance_2d(grid))
    
    return metrics


# ============================================================================
# 2D TORUS RUNNER (User-Approved Rich Structure Configs)
# ============================================================================

def run_rich_structure_evolution(
    config_name: str,
    rho_c: float,
    grid_size: int = 64,  # Larger than E7 for richer dynamics
    n_steps: int = 1000,   # Longer than E7 to see structures emerge
    seed: int = 42,
    initial_density: float = 0.20  # Lower than E7 for more organization space
) -> Dict:
    """
    Run 2D torus with user-approved "rich structure" configuration.
    
    These configs showed complex closed shapes (ellipses, tubes, loops)
    in SESSION 16.4 visual inspection.
    """
    print(f"\n" + "=" * 70)
    print(f"  2D TORUS: {config_name}")
    print("=" * 70)
    print(f"Parameters: ρ_c={rho_c}, α=0.2, β=3.0, γ=5.0, ε=0.0")
    print(f"Grid: {grid_size}×{grid_size} = {grid_size*grid_size} cells")
    print(f"Initial density: {initial_density:.0%}")
    
    # Initialize grid with lower initial density for more organization space
    np.random.seed(seed)
    grid = PR1Grid2D(grid_size, grid_size)
    
    for x in range(grid_size):
        for y in range(grid_size):
            if np.random.random() < initial_density:
                grid.m[x, y] = 1
            grid.g[x, y] = np.random.randint(0, 4)
            grid.l[x, y] = np.random.randint(0, 8)
            grid.mu[x, y] = np.random.choice([0, 1, 2])
    
    actual_density = np.mean(grid.m)
    print(f"✅ Grid initialized")
    print(f"   Actual m-field density: {actual_density:.3f}")
    
    # Create executor with SESSION 16.4 parameters
    # These are FULLY DETERMINISTIC (base_rate=0.0)
    executor = TorusExecutorElegant(
        size_x=grid_size,
        size_y=grid_size,
        critical_density=rho_c,
        neighborhood_radius=5,
        deterministic=True,  # Fully deterministic
        stochastic_source='ugp',
        alpha=0.2,   # Low creation (from SESSION 16.4)
        beta=3.0,    # High annihilation (from SESSION 16.4)
        gamma=5.0,   # Moderate sharpness (from SESSION 16.4)
        base_rate=0.0,  # ZERO noise (from SESSION 16.4)
        ugp_seed=seed
    )
    
    # Evolution history
    history = {
        'dissonance': [],
        'kink_density': [],
        'kinks_total': [],
        'm_density': [],
        'g_entropy': [],
        'l_entropy': [],
        'grid_snapshots': []  # Store snapshots for video
    }
    
    # Initialize sigma and ugp_ok arrays
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
        
        # Save snapshot every 10 steps for video
        if t % 10 == 0:
            history['grid_snapshots'].append({
                'm': grid.m.copy(),
                'g': grid.g.copy(),
                'l': grid.l.copy(),
                'mu': grid.mu.copy()
            })
        
        if t % 100 == 0:
            print(f"  Step {t:4d}: D = {metrics['dissonance']:.4f}, "
                  f"kinks = {metrics['kinks_total']}, "
                  f"ρ = {metrics['m_density']:.3f}")
        
        # Evolve one step
        chi_X, chi_S, is_kink = executor.evolve_step(grid, sigma, ugp_ok, timestep=t)
    
    return history


def create_video(result: Dict, config: Dict, timestamp: str):
    """Create 4-panel video showing m, g, l, mu fields."""
    snapshots = result['history']['grid_snapshots']
    name = config['name']
    
    print(f"\nCreating video for {name}...")
    print(f"  Frames: {len(snapshots)}")
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 12))
    fig.suptitle(f"{name} (ρ_c={config['rho_c']}): 2D Torus Evolution", fontsize=14, fontweight='bold')
    
    # Initialize images
    im_m = axes[0, 0].imshow(snapshots[0]['m'], cmap='binary', interpolation='nearest')
    axes[0, 0].set_title('m-field (Domain)', fontsize=12)
    axes[0, 0].axis('off')
    
    im_g = axes[0, 1].imshow(snapshots[0]['g'], cmap='twilight', vmin=0, vmax=3, interpolation='nearest')
    axes[0, 1].set_title('g-field (Phase ℤ₄)', fontsize=12)
    axes[0, 1].axis('off')
    
    im_l = axes[1, 0].imshow(snapshots[0]['l'], cmap='viridis', vmin=0, vmax=7, interpolation='nearest')
    axes[1, 0].set_title('l-field (Slope ℤ₈)', fontsize=12)
    axes[1, 0].axis('off')
    
    im_mu = axes[1, 1].imshow(snapshots[0]['mu'], cmap='RdYlGn', vmin=0, vmax=2, interpolation='nearest')
    axes[1, 1].set_title('μ-field (Slope Change)', fontsize=12)
    axes[1, 1].axis('off')
    
    # Colorbars
    plt.colorbar(im_g, ax=axes[0, 1], fraction=0.046, pad=0.04)
    plt.colorbar(im_l, ax=axes[1, 0], fraction=0.046, pad=0.04)
    plt.colorbar(im_mu, ax=axes[1, 1], fraction=0.046, pad=0.04)
    
    # Time text
    time_text = fig.text(0.5, 0.02, '', ha='center', fontsize=11)
    
    def update(frame):
        snapshot = snapshots[frame]
        im_m.set_array(snapshot['m'])
        im_g.set_array(snapshot['g'])
        im_l.set_array(snapshot['l'])
        im_mu.set_array(snapshot['mu'])
        time_text.set_text(f'Step: {frame * 10} / 1000')
        return [im_m, im_g, im_l, im_mu, time_text]
    
    anim = animation.FuncAnimation(fig, update, frames=len(snapshots), interval=50, blit=True)
    
    video_file = f"E8_{name}_{timestamp}.mp4"
    writer = animation.FFMpegWriter(fps=20, bitrate=2000)
    
    try:
        anim.save(video_file, writer=writer)
        print(f"  ✅ Video saved: {video_file}")
    except Exception as e:
        print(f"  ⚠️ Video creation failed (FFmpeg not available?): {e}")
        print(f"     Saving first/last frame comparison instead...")
        
        # Fallback: save static comparison
        fig_static, axes_static = plt.subplots(2, 4, figsize=(16, 8))
        fig_static.suptitle(f"{name} Evolution: Start vs End", fontsize=14, fontweight='bold')
        
        # First frame
        axes_static[0, 0].imshow(snapshots[0]['m'], cmap='binary')
        axes_static[0, 0].set_title('m (t=0)')
        axes_static[0, 0].axis('off')
        
        axes_static[0, 1].imshow(snapshots[0]['g'], cmap='twilight', vmin=0, vmax=3)
        axes_static[0, 1].set_title('g (t=0)')
        axes_static[0, 1].axis('off')
        
        axes_static[0, 2].imshow(snapshots[0]['l'], cmap='viridis', vmin=0, vmax=7)
        axes_static[0, 2].set_title('l (t=0)')
        axes_static[0, 2].axis('off')
        
        axes_static[0, 3].imshow(snapshots[0]['mu'], cmap='RdYlGn', vmin=0, vmax=2)
        axes_static[0, 3].set_title('μ (t=0)')
        axes_static[0, 3].axis('off')
        
        # Last frame
        axes_static[1, 0].imshow(snapshots[-1]['m'], cmap='binary')
        axes_static[1, 0].set_title('m (t=1000)')
        axes_static[1, 0].axis('off')
        
        axes_static[1, 1].imshow(snapshots[-1]['g'], cmap='twilight', vmin=0, vmax=3)
        axes_static[1, 1].set_title('g (t=1000)')
        axes_static[1, 1].axis('off')
        
        axes_static[1, 2].imshow(snapshots[-1]['l'], cmap='viridis', vmin=0, vmax=7)
        axes_static[1, 2].set_title('l (t=1000)')
        axes_static[1, 2].axis('off')
        
        axes_static[1, 3].imshow(snapshots[-1]['mu'], cmap='RdYlGn', vmin=0, vmax=2)
        axes_static[1, 3].set_title('μ (t=1000)')
        axes_static[1, 3].axis('off')
        
        plt.tight_layout()
        static_file = f"E8_{name}_{timestamp}_comparison.png"
        plt.savefig(static_file, dpi=150, bbox_inches='tight')
        print(f"  ✅ Static comparison saved: {static_file}")
        plt.close(fig_static)
    
    plt.close(fig)


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def main():
    print("\n" + "=" * 70)
    print("  E8: 2D TORUS RICH STRUCTURES TEST")
    print("  User-Approved Configurations (SESSION 16.4)")
    print("=" * 70)
    
    print("\nQUESTION:")
    print("  Do visually rich configs (ellipses, tubes, loops) ALSO show")
    print("  D-minimization (coherence emergence)?")
    print()
    print("PREVIOUS RESULTS:")
    print("  E7 (edge-of-chaos): D stable (-0.0%) but less visually rich")
    print("  SESSION 16.4: ρ_c=0.34-0.38 showed best visual structures")
    print()
    
    # User-approved configurations from SESSION 16.4
    configs = [
        {
            'name': 'rho_c_0.34',
            'rho_c': 0.34,
            'description': 'Complex closed shapes (user-approved)'
        },
        {
            'name': 'rho_c_0.36',
            'rho_c': 0.36,
            'description': 'Ellipses, tubes (user-approved)'
        },
        {
            'name': 'rho_c_0.38',
            'rho_c': 0.38,
            'description': 'Loops (user-approved)'
        }
    ]
    
    # Run all configurations
    results = {}
    for config in configs:
        print(f"\n{'─' * 70}")
        print(f"CONFIGURATION: {config['name']}")
        print(f"Description: {config['description']}")
        print(f"{'─' * 70}")
        
        history = run_rich_structure_evolution(
            config_name=config['name'],
            rho_c=config['rho_c'],
            grid_size=64,  # Larger for richer structures
            n_steps=1000,  # Longer to see structure emergence
            seed=42,
            initial_density=0.20  # Lower to allow more organization
        )
        
        results[config['name']] = {
            'config': config,
            'history': history
        }
    
    # Analyze results
    print("\n" + "=" * 70)
    print("  COHERENCE EMERGENCE ANALYSIS")
    print("=" * 70)
    
    print("\nCOMPARISON TO E7 (Edge-of-Chaos):")
    print("   E7 configs: D change ≈ -0.0% (stable)")
    print("   → Showed coherence but less visual richness")
    
    print("\nE8 RESULTS (Rich Structures):")
    for config in configs:
        name = config['name']
        hist = results[name]['history']
        
        D_initial = hist['dissonance'][0]
        D_final = hist['dissonance'][-1]
        D_change_pct = ((D_final - D_initial) / D_initial) * 100
        
        # Check for D-minimization
        if D_change_pct < -5:
            verdict = "✅ STRONG COHERENCE (D decreased significantly)"
            symbol = "✅✅"
        elif D_change_pct < 0:
            verdict = "✅ COHERENCE EMERGED (D decreased)"
            symbol = "✅"
        elif D_change_pct < 5:
            verdict = "⚠️ STABLE (D nearly constant)"
            symbol = "⚠️"
        else:
            verdict = "❌ NO COHERENCE (D increased)"
            symbol = "❌"
        
        print(f"\n{name} (ρ_c={config['rho_c']}):")
        print(f"   Initial D: {D_initial:.4f}")
        print(f"   Final D:   {D_final:.4f}")
        print(f"   Change:    {D_change_pct:+.1f}%")
        print(f"   {verdict}")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"E8_rich_structures_results_{timestamp}.json"
    
    json_results = {}
    for name, data in results.items():
        # Exclude grid_snapshots from JSON (too large)
        history_for_json = {k: [float(v) for v in vals] 
                           for k, vals in data['history'].items() 
                           if k != 'grid_snapshots'}
        json_results[name] = {
            'config': data['config'],
            'history': history_for_json
        }
    
    with open(results_file, 'w') as f:
        json.dump(json_results, f, indent=2)
    
    print(f"\n✅ Results saved: {results_file}")
    
    # Create comparison plot
    create_comparison_plot(results, configs)
    
    # Create videos for each configuration
    print("\n" + "=" * 70)
    print("  CREATING VIDEOS")
    print("=" * 70)
    for config in configs:
        name = config['name']
        create_video(results[name], config, timestamp)
    
    print("\n" + "=" * 70)
    print("  FINAL VERDICT")
    print("=" * 70)
    
    # Determine best configuration
    best_config = None
    best_D_drop = 0
    
    for config in configs:
        name = config['name']
        hist = results[name]['history']
        D_drop = ((hist['dissonance'][-1] - hist['dissonance'][0]) / hist['dissonance'][0]) * 100
        
        if D_drop < best_D_drop:
            best_D_drop = D_drop
            best_config = name
    
    if best_config and best_D_drop < -5:
        print(f"\n✅ WINNER: {best_config}")
        print(f"   D decreased by {abs(best_D_drop):.1f}%")
        print(f"   → BOTH visually rich AND coherent!")
        print(f"   → Best configuration for Reflexive Reality substrate")
    elif best_D_drop < 0:
        print(f"\n⚠️ PARTIAL SUCCESS:")
        print(f"   All configs stable/slightly coherent")
        print(f"   → Visual richness without disorder increase")
    else:
        print(f"\n❓ NEUTRAL RESULT:")
        print(f"   No strong D-minimization in rich structure regime")
        print(f"   → May need different parameter balance")


def create_comparison_plot(results: Dict, configs: List[Dict]):
    """Create comparison plot of D(t) and structure metrics."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Plot 1: Dissonance evolution
    ax = axes[0, 0]
    for config in configs:
        name = config['name']
        hist = results[name]['history']
        ax.plot(hist['dissonance'], label=f"ρ_c={config['rho_c']}", linewidth=2)
    ax.set_xlabel('Time Step')
    ax.set_ylabel('Dissonance D(t)')
    ax.set_title('Dissonance Evolution: Rich Structure Configs')
    ax.legend()
    ax.grid(alpha=0.3)
    
    # Plot 2: Density evolution
    ax = axes[0, 1]
    for config in configs:
        name = config['name']
        hist = results[name]['history']
        ax.plot(hist['m_density'], label=f"ρ_c={config['rho_c']}", linewidth=2)
    ax.set_xlabel('Time Step')
    ax.set_ylabel('Density ρ(t)')
    ax.set_title('Density Evolution (Self-Regulation)')
    ax.legend()
    ax.grid(alpha=0.3)
    
    # Plot 3: Kink count evolution
    ax = axes[1, 0]
    for config in configs:
        name = config['name']
        hist = results[name]['history']
        ax.plot(hist['kinks_total'], label=f"ρ_c={config['rho_c']}", linewidth=2)
    ax.set_xlabel('Time Step')
    ax.set_ylabel('Total Kinks')
    ax.set_title('Kink Count Evolution (Structure Formation)')
    ax.legend()
    ax.grid(alpha=0.3)
    
    # Plot 4: D change comparison
    ax = axes[1, 1]
    names = []
    changes = []
    colors = []
    
    for config in configs:
        name = config['name']
        hist = results[name]['history']
        D_initial = hist['dissonance'][0]
        D_final = hist['dissonance'][-1]
        D_change_pct = ((D_final - D_initial) / D_initial) * 100
        
        names.append(f"ρ_c={config['rho_c']}")
        changes.append(D_change_pct)
        colors.append('green' if D_change_pct < -5 else 'lightgreen' if D_change_pct < 0 else 'orange')
    
    bars = ax.bar(names, changes, color=colors, alpha=0.7, edgecolor='black')
    ax.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax.axhline(y=-0.02, color='green', linestyle='--', alpha=0.3, label='E7 level')
    ax.set_ylabel('D Change (%)')
    ax.set_title('Dissonance Change: Rich Structure Configs')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    
    # Add value labels
    for bar, change in zip(bars, changes):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{change:+.1f}%',
                ha='center', va='bottom' if height > 0 else 'top',
                fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    plot_file = f"E8_rich_structures_comparison_{timestamp}.png"
    plt.savefig(plot_file, dpi=150, bbox_inches='tight')
    print(f"✅ Comparison plot saved: {plot_file}")
    plt.close()


if __name__ == "__main__":
    main()

