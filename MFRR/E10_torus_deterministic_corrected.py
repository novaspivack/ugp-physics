#!/usr/bin/env python3
"""
E10: 2D Torus DETERMINISTIC Coherence Test (Bug Fixed)

CRITICAL FIX: E8 was frozen because α=0.2 is too low for deterministic mode.

For deterministic firing (threshold > 0.5), we need α ≥ 1.0.

Test configurations:
1. balanced_1_3: α=1.0, β=3.0 (minimal firing α, moderate balance)
2. balanced_2_5: α=2.0, β=5.0 (higher firing, strong balance)
3. sharp_2_5: α=2.0, β=5.0, γ=10.0 (Conway-like sharp)

All FULLY DETERMINISTIC (no stochasticity).

Longer run: 2000 steps to see full dynamics.
Larger grid: 64×64 for rich structures.
"""

import json
import os
import sys
from datetime import datetime
from multiprocessing import Pool, cpu_count
from pathlib import Path
from typing import Dict, List

import matplotlib
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np

matplotlib.use("Agg")  # Non-interactive backend

# Add PR-1 torus infrastructure (paths relative to ugp-physics repository root)
_optimizer_tests = Path(__file__).resolve().parent.parent  # ugp-physics repository root
pr1_path = str(_optimizer_tests / "PR-1_UGP_Loop_CA/logos_search/logos_derivation_experiment/src")
sys.path.insert(0, pr1_path)

try:
    from pr1_grid_2d import PR1Grid2D
    from torus_executor_elegant import TorusExecutorElegant
    print("✅ 2D Torus infrastructure loaded\n")
except ImportError as e:
    print(f"❌ Error: {e}")
    sys.exit(1)


def calculate_dissonance_2d(grid: PR1Grid2D) -> float:
    """Dissonance = kink density + field disorder"""
    kinks_h = np.sum(grid.m != np.roll(grid.m, 1, axis=0))
    kinks_v = np.sum(grid.m != np.roll(grid.m, 1, axis=1))
    kink_density = (kinks_h + kinks_v) / (2 * grid.size)
    
    g_var = np.var(grid.g.astype(float)) / 16.0
    l_var = np.var(grid.l.astype(float)) / 64.0
    mu_std = np.std(grid.mu.astype(float)) / 2.0
    
    return kink_density + 0.5 * (g_var + l_var + mu_std)


def run_single_config(args):
    """Run single configuration (for multiprocessing)"""
    config_name, rho_c, alpha, beta, gamma, grid_size, n_steps, seed = args
    
    print(f"\n{'='*70}")
    print(f"  {config_name}")
    print(f"  ρ_c={rho_c}, α={alpha}, β={beta}, γ={gamma}")
    print(f"{'='*70}")
    
    # Initialize grid (20% initial density)
    np.random.seed(seed)
    grid = PR1Grid2D(grid_size, grid_size)
    
    for x in range(grid_size):
        for y in range(grid_size):
            if np.random.random() < 0.20:
                grid.m[x, y] = 1
            grid.g[x, y] = np.random.randint(0, 4)
            grid.l[x, y] = np.random.randint(0, 8)
            grid.mu[x, y] = np.random.choice([0, 1, 2])
    
    print(f"✅ Grid: {grid_size}×{grid_size}, ρ_init={np.mean(grid.m):.3f}")
    
    # Create DETERMINISTIC executor with CORRECTED parameters
    executor = TorusExecutorElegant(
        size_x=grid_size,
        size_y=grid_size,
        critical_density=rho_c,
        neighborhood_radius=5,
        deterministic=True,  # FULLY DETERMINISTIC
        stochastic_source='ugp',  # Only used if stochastic
        alpha=alpha,  # CORRECTED: ≥ 1.0 for deterministic
        beta=beta,
        gamma=gamma,
        base_rate=0.0,  # Zero noise
        ugp_seed=seed
    )
    
    # Arrays
    n_cells = grid_size * grid_size
    sigma = np.ones(n_cells, dtype=int)
    ugp_ok = np.ones(n_cells, dtype=bool)
    
    # History
    history = {
        'dissonance': [],
        'kinks': [],
        'density': [],
        'snapshots': []
    }
    
    print(f"Evolving for {n_steps} steps...")
    
    for t in range(n_steps):
        D = calculate_dissonance_2d(grid)
        kinks_h = np.sum(grid.m != np.roll(grid.m, 1, axis=0))
        kinks_v = np.sum(grid.m != np.roll(grid.m, 1, axis=1))
        kinks_total = int(kinks_h + kinks_v)
        density = float(np.mean(grid.m))
        
        history['dissonance'].append(float(D))
        history['kinks'].append(kinks_total)
        history['density'].append(density)
        
        # Save snapshots every 20 steps
        if t % 20 == 0:
            history['snapshots'].append({
                'm': grid.m.copy(),
                'g': grid.g.copy(),
                'l': grid.l.copy(),
                'mu': grid.mu.copy(),
                't': t
            })
        
        if t % 200 == 0:
            print(f"  Step {t:4d}: D={D:.4f}, kinks={kinks_total}, ρ={density:.3f}")
        
        # Evolve
        executor.evolve_step(grid, sigma, ugp_ok, timestep=t)
    
    return {
        'config_name': config_name,
        'rho_c': rho_c,
        'alpha': alpha,
        'beta': beta,
        'gamma': gamma,
        'history': history
    }


def create_video_multifield(result: Dict, output_dir: str):
    """Create 4-panel video"""
    name = result['config_name']
    snapshots = result['history']['snapshots']
    
    print(f"\nCreating video: {name} ({len(snapshots)} frames)...")
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 12))
    fig.suptitle(f"{name}: 2D Torus Deterministic Evolution", fontsize=14, fontweight='bold')
    
    # Initialize
    im_m = axes[0, 0].imshow(snapshots[0]['m'], cmap='binary', interpolation='nearest')
    axes[0, 0].set_title('m-field (Domain)')
    axes[0, 0].axis('off')
    
    im_g = axes[0, 1].imshow(snapshots[0]['g'], cmap='twilight', vmin=0, vmax=3, interpolation='nearest')
    axes[0, 1].set_title('g-field (Phase)')
    axes[0, 1].axis('off')
    
    im_l = axes[1, 0].imshow(snapshots[0]['l'], cmap='viridis', vmin=0, vmax=7, interpolation='nearest')
    axes[1, 0].set_title('l-field (Slope)')
    axes[1, 0].axis('off')
    
    im_mu = axes[1, 1].imshow(snapshots[0]['mu'], cmap='RdYlGn', vmin=0, vmax=2, interpolation='nearest')
    axes[1, 1].set_title('μ-field')
    axes[1, 1].axis('off')
    
    time_text = fig.text(0.5, 0.02, '', ha='center', fontsize=11)
    
    def update(frame):
        snap = snapshots[frame]
        im_m.set_array(snap['m'])
        im_g.set_array(snap['g'])
        im_l.set_array(snap['l'])
        im_mu.set_array(snap['mu'])
        time_text.set_text(f"Step: {snap['t']} / 2000")
        return [im_m, im_g, im_l, im_mu, time_text]
    
    anim = animation.FuncAnimation(fig, update, frames=len(snapshots), interval=50, blit=True)
    
    video_file = f"{output_dir}/{name}.mp4"
    try:
        writer = animation.FFMpegWriter(fps=20, bitrate=3000)
        anim.save(video_file, writer=writer)
        print(f"  ✅ Video: {video_file}")
    except Exception as e:
        print(f"  ⚠️ FFmpeg error: {e}")
    
    plt.close(fig)


def main():
    print("\n" + "=" * 70)
    print("  E10: DETERMINISTIC 2D TORUS (Bug Fixed)")
    print("  Corrected α for deterministic mode")
    print("=" * 70)
    
    print("\nBUG FIX:")
    print("  E8 was frozen: α=0.2 too low for deterministic (threshold < 0.5)")
    print("  E10 correction: α ≥ 1.0 required for firing")
    print()
    
    # Configurations with CORRECTED α for deterministic mode
    configs = [
        ('balanced_1_3', 0.34, 1.0, 3.0, 5.0),   # Minimal α for firing
        ('balanced_2_5', 0.36, 2.0, 5.0, 5.0),   # Higher α, stronger balance
        ('sharp_2_5', 0.36, 2.0, 5.0, 10.0),     # Conway-like sharp
        ('sparse_1_3', 0.26, 1.0, 3.0, 5.0),     # Low ρ_c (sparse)
        ('dense_2_5', 0.44, 2.0, 5.0, 5.0),      # High ρ_c (dense)
    ]
    
    grid_size = 64
    n_steps = 2000  # Longer run
    seed = 42
    
    # Prepare arguments for multiprocessing
    args_list = [
        (config_name, rho_c, alpha, beta, gamma, grid_size, n_steps, seed)
        for config_name, rho_c, alpha, beta, gamma in configs
    ]
    
    # Use multiprocessing for simulations (not videos)
    n_processes = min(len(configs), cpu_count())
    print(f"\n🚀 Running {len(configs)} configurations using {n_processes} parallel processes...")
    
    with Pool(processes=n_processes) as pool:
        results = pool.map(run_single_config, args_list)
    
    # Analysis
    print("\n" + "=" * 70)
    print("  COHERENCE ANALYSIS")
    print("=" * 70)
    
    print("\nCOMPARISON:")
    print("  1D Loop (E6): D +26.7% ❌ (chaos)")
    print("  E8 (frozen):  D -0.0% (but FROZEN due to low α)")
    print()
    
    print("E10 RESULTS (Deterministic, Corrected α):")
    for result in results:
        name = result['config_name']
        hist = result['history']
        
        D_i = hist['dissonance'][0]
        D_f = hist['dissonance'][-1]
        D_pct = ((D_f - D_i) / D_i) * 100
        
        rho_i = hist['density'][0]
        rho_f = hist['density'][-1]
        
        kinks_i = hist['kinks'][0]
        kinks_f = hist['kinks'][-1]
        
        if D_pct < -5:
            verdict = "✅✅ STRONG COHERENCE"
        elif D_pct < 0:
            verdict = "✅ COHERENCE"
        elif D_pct < 5:
            verdict = "⚠️ STABLE"
        else:
            verdict = "❌ DISORDER"
        
        print(f"\n{name} (ρ_c={result['rho_c']}, α={result['alpha']}, β={result['beta']}, γ={result['gamma']}):")
        print(f"  D: {D_i:.4f} → {D_f:.4f} ({D_pct:+.1f}%)")
        print(f"  ρ: {rho_i:.3f} → {rho_f:.3f}")
        print(f"  Kinks: {kinks_i} → {kinks_f} ({kinks_f-kinks_i:+d})")
        print(f"  {verdict}")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"E10_deterministic_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    
    # Save JSON (without snapshots)
    json_results = []
    for result in results:
        json_results.append({
            'config_name': result['config_name'],
            'rho_c': result['rho_c'],
            'alpha': result['alpha'],
            'beta': result['beta'],
            'gamma': result['gamma'],
            'history': {
                'dissonance': result['history']['dissonance'],
                'kinks': result['history']['kinks'],
                'density': result['history']['density']
            }
        })
    
    with open(f"{output_dir}/results.json", 'w') as f:
        json.dump(json_results, f, indent=2)
    
    print(f"\n✅ Results saved: {output_dir}/results.json")
    
    # Create comparison plot
    create_comparison_plot(results, output_dir)
    
    # Create videos
    print("\n" + "=" * 70)
    print("  CREATING VIDEOS (2000 step evolution)")
    print("=" * 70)
    for result in results:
        create_video_multifield(result, output_dir)
    
    print("\n" + "=" * 70)
    print("  COMPLETE")
    print("=" * 70)
    print(f"\nAll outputs in: {output_dir}/")
    print(f"  - results.json")
    print(f"  - comparison.png")
    print(f"  - {len(results)} videos (.mp4)")


def create_comparison_plot(results: List[Dict], output_dir: str):
    """Create 3-panel comparison plot"""
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    
    # Plot 1: Dissonance
    ax = axes[0]
    for result in results:
        name = result['config_name']
        ax.plot(result['history']['dissonance'], 
                label=f"{name} (ρ_c={result['rho_c']})", linewidth=1.5)
    ax.set_xlabel('Time Step')
    ax.set_ylabel('Dissonance D(t)')
    ax.set_title('Coherence Evolution')
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    
    # Plot 2: Density
    ax = axes[1]
    for result in results:
        name = result['config_name']
        ax.plot(result['history']['density'], 
                label=f"{name}", linewidth=1.5)
        ax.axhline(y=result['rho_c'], linestyle='--', alpha=0.3)
    ax.set_xlabel('Time Step')
    ax.set_ylabel('Density ρ(t)')
    ax.set_title('Self-Regulation to ρ_c')
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    
    # Plot 3: D change summary
    ax = axes[2]
    names = []
    changes = []
    colors = []
    
    for result in results:
        D_change = ((result['history']['dissonance'][-1] - result['history']['dissonance'][0]) / 
                    result['history']['dissonance'][0]) * 100
        names.append(result['config_name'])
        changes.append(D_change)
        colors.append('green' if D_change < -5 else 'lightgreen' if D_change < 0 else 'orange')
    
    bars = ax.bar(names, changes, color=colors, alpha=0.7, edgecolor='black')
    ax.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax.set_ylabel('D Change (%)')
    ax.set_title('Coherence Summary')
    ax.grid(axis='y', alpha=0.3)
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    for bar, change in zip(bars, changes):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{change:+.1f}%',
                ha='center', va='bottom' if height > 0 else 'top',
                fontsize=9, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/comparison.png", dpi=150, bbox_inches='tight')
    print(f"✅ Plot: {output_dir}/comparison.png")
    plt.close()


if __name__ == "__main__":
    main()

