#!/usr/bin/env python3
"""
E9: 2D Torus Extreme Configurations Test

Test the EXTREMES of the critical threshold range:
- ρ_c = 0.26 (low, sparse)
- ρ_c = 0.44 (high, dense)

Compare to E8's "sweet spot" (0.34-0.38).

All fully deterministic, same parameters as SESSION 16.4.
"""

import importlib.util
import os
import sys
from pathlib import Path

# PR-1 torus infrastructure (paths relative to ugp-physics repository root)
_optimizer_tests = Path(__file__).resolve().parent.parent  # ugp-physics repository root
sys.path.insert(
    0,
    str(_optimizer_tests / "PR-1_UGP_Loop_CA/logos_search/logos_derivation_experiment/src"),
)

# Load E8 as a module so `if __name__ == "__main__"` in E8 does not run
_e8_path = Path(__file__).resolve().parent / "E8_torus_rich_structures.py"
_spec = importlib.util.spec_from_file_location("e8_torus_rich_structures", _e8_path)
_e8 = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_e8)
run_rich_structure_evolution = _e8.run_rich_structure_evolution
create_video = _e8.create_video

def main_extremes():
    print("\n" + "=" * 70)
    print("  E9: 2D TORUS EXTREME CONFIGURATIONS TEST")
    print("  Testing Sparse (0.26) vs Dense (0.44)")
    print("=" * 70)
    
    print("\nQUESTION:")
    print("  Are the extremes (0.26, 0.44) better or worse than")
    print("  the sweet spot (0.34-0.38) for coherence?")
    print()
    print("HYPOTHESIS:")
    print("  Sweet spot (0.34-0.38) should show best balance of")
    print("  visual richness + coherence stability.")
    print()
    
    # Extreme configurations
    configs = [
        {
            'name': 'rho_c_0.26',
            'rho_c': 0.26,
            'description': 'Sparse (from SESSION 16.4)'
        },
        {
            'name': 'rho_c_0.44',
            'rho_c': 0.44,
            'description': 'Dense (from SESSION 16.4)'
        }
    ]
    
    # Run both extremes
    results = {}
    for config in configs:
        print(f"\n{'─' * 70}")
        print(f"CONFIGURATION: {config['name']}")
        print(f"Description: {config['description']}")
        print(f"{'─' * 70}")
        
        history = run_rich_structure_evolution(
            config_name=config['name'],
            rho_c=config['rho_c'],
            grid_size=64,
            n_steps=1000,
            seed=42,
            initial_density=0.20
        )
        
        results[config['name']] = {
            'config': config,
            'history': history
        }
    
    # Analyze results
    print("\n" + "=" * 70)
    print("  COHERENCE EMERGENCE ANALYSIS")
    print("=" * 70)
    
    print("\nE8 RESULTS (Sweet Spot - for comparison):")
    print("   ρ_c=0.34: D change -0.2% ✅")
    print("   ρ_c=0.36: D change -0.2% ✅")
    print("   ρ_c=0.38: D change -0.2% ✅")
    
    print("\nE9 RESULTS (Extremes):")
    for config in configs:
        name = config['name']
        hist = results[name]['history']
        
        D_initial = hist['dissonance'][0]
        D_final = hist['dissonance'][-1]
        D_change_pct = ((D_final - D_initial) / D_initial) * 100
        
        rho_initial = hist['m_density'][0]
        rho_final = hist['m_density'][-1]
        
        if D_change_pct < -5:
            verdict = "✅✅ STRONG COHERENCE"
        elif D_change_pct < 0:
            verdict = "✅ COHERENCE"
        elif D_change_pct < 5:
            verdict = "⚠️ STABLE"
        else:
            verdict = "❌ NO COHERENCE"
        
        print(f"\n{name} (ρ_c={config['rho_c']}):")
        print(f"   Initial: D={D_initial:.4f}, ρ={rho_initial:.3f}")
        print(f"   Final:   D={D_final:.4f}, ρ={rho_final:.3f}")
        print(f"   D change: {D_change_pct:+.1f}%")
        print(f"   {verdict}")
    
    # Save results
    from datetime import datetime
    import json
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"E9_extremes_results_{timestamp}.json"
    
    json_results = {}
    for name, data in results.items():
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
    import matplotlib.pyplot as plt
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Plot 1: Dissonance
    ax = axes[0, 0]
    for config in configs:
        name = config['name']
        hist = results[name]['history']
        ax.plot(hist['dissonance'], label=f"ρ_c={config['rho_c']}", linewidth=2)
    ax.set_xlabel('Time Step')
    ax.set_ylabel('Dissonance D(t)')
    ax.set_title('Dissonance: Sparse vs Dense')
    ax.legend()
    ax.grid(alpha=0.3)
    
    # Plot 2: Density evolution
    ax = axes[0, 1]
    for config in configs:
        name = config['name']
        hist = results[name]['history']
        ax.plot(hist['m_density'], label=f"ρ_c={config['rho_c']}", linewidth=2)
    ax.axhline(y=0.26, color='blue', linestyle='--', alpha=0.3)
    ax.axhline(y=0.44, color='red', linestyle='--', alpha=0.3)
    ax.set_xlabel('Time Step')
    ax.set_ylabel('Density ρ(t)')
    ax.set_title('Density Self-Regulation')
    ax.legend()
    ax.grid(alpha=0.3)
    
    # Plot 3: Kinks
    ax = axes[1, 0]
    for config in configs:
        name = config['name']
        hist = results[name]['history']
        ax.plot(hist['kinks_total'], label=f"ρ_c={config['rho_c']}", linewidth=2)
    ax.set_xlabel('Time Step')
    ax.set_ylabel('Total Kinks')
    ax.set_title('Structure Formation')
    ax.legend()
    ax.grid(alpha=0.3)
    
    # Plot 4: Summary comparison
    ax = axes[1, 1]
    
    all_configs = [
        ('0.26\n(sparse)', 0.26, results['rho_c_0.26']['history']),
        ('0.34-0.38\n(sweet)', 0.36, None),  # E8 average
        ('0.44\n(dense)', 0.44, results['rho_c_0.44']['history'])
    ]
    
    names = []
    changes = []
    colors = []
    
    for label, rho_c, hist in all_configs:
        names.append(label)
        if hist is None:
            # E8 average
            changes.append(-0.2)
            colors.append('lightgreen')
        else:
            D_change = ((hist['dissonance'][-1] - hist['dissonance'][0]) / hist['dissonance'][0]) * 100
            changes.append(D_change)
            colors.append('green' if D_change < -5 else 'lightgreen' if D_change < 0 else 'orange')
    
    bars = ax.bar(names, changes, color=colors, alpha=0.7, edgecolor='black')
    ax.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax.set_ylabel('D Change (%)')
    ax.set_title('Coherence: Extremes vs Sweet Spot')
    ax.grid(axis='y', alpha=0.3)
    
    for bar, change in zip(bars, changes):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{change:+.1f}%',
                ha='center', va='bottom' if height > 0 else 'top',
                fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    plot_file = f"E9_extremes_comparison_{timestamp}.png"
    plt.savefig(plot_file, dpi=150, bbox_inches='tight')
    print(f"✅ Comparison plot saved: {plot_file}")
    plt.close()
    
    # Create videos
    print("\n" + "=" * 70)
    print("  CREATING VIDEOS")
    print("=" * 70)
    for config in configs:
        name = config['name']
        create_video(results[name], config, timestamp)
    
    # Final verdict
    print("\n" + "=" * 70)
    print("  FINAL VERDICT")
    print("=" * 70)
    
    sparse_D = ((results['rho_c_0.26']['history']['dissonance'][-1] - 
                 results['rho_c_0.26']['history']['dissonance'][0]) / 
                results['rho_c_0.26']['history']['dissonance'][0]) * 100
    
    dense_D = ((results['rho_c_0.44']['history']['dissonance'][-1] - 
                results['rho_c_0.44']['history']['dissonance'][0]) / 
               results['rho_c_0.44']['history']['dissonance'][0]) * 100
    
    sweet_D = -0.2  # E8 average
    
    print(f"\nSparse (ρ_c=0.26): D change = {sparse_D:+.1f}%")
    print(f"Sweet  (ρ_c=0.34-0.38): D change = {sweet_D:+.1f}%")
    print(f"Dense  (ρ_c=0.44): D change = {dense_D:+.1f}%")
    
    if abs(sweet_D) >= abs(sparse_D) and abs(sweet_D) >= abs(dense_D):
        print("\n✅ SWEET SPOT CONFIRMED!")
        print("   ρ_c = 0.34-0.38 shows best coherence")
    elif abs(sparse_D) > abs(sweet_D):
        print("\n🎯 SPARSE BETTER!")
        print(f"   ρ_c = 0.26 shows stronger coherence ({sparse_D:+.1f}%)")
    else:
        print("\n🎯 DENSE BETTER!")
        print(f"   ρ_c = 0.44 shows stronger coherence ({dense_D:+.1f}%)")


if __name__ == "__main__":
    main_extremes()

