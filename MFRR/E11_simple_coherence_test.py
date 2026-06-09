#!/usr/bin/env python3
"""
E11 SIMPLE: Coherence Bias Test (Simplified)

Test whether explicit coherence bias produces D-minimization.

Strategy:
- Skip complex PR-1 infrastructure (which has frozen/empty grid issues)
- Build a MINIMAL coherence-aware CA from scratch
- Demonstrate the principle cleanly

Systems:
1. Rule 110 (chaotic baseline)
2. Simple Reversible CA (no coherence bias)
3. Coherence-Aware CA (WITH bias)
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime
import json
import os


def compute_dissonance(state):
    """Dissonance = kink density + entropy deviation."""
    kinks = np.sum(state != np.roll(state, 1))
    kink_density = kinks / len(state)
    
    density = np.mean(state)
    entropy_dev = abs(density - 0.5)
    
    return 0.7 * kink_density + 0.3 * entropy_dev


def rule110(state):
    """Rule 110: chaotic universal CA."""
    new_state = np.zeros_like(state)
    n = len(state)
    for i in range(n):
        left = state[(i-1) % n]
        center = state[i]
        right = state[(i+1) % n]
        pattern = (left << 2) | (center << 1) | right
        new_state[i] = (110 >> pattern) & 1
    return new_state


def simple_reversible_ca(state, reverse=False):
    """
    Simple reversible CA: swap adjacent opposite bits.
    
    Rule: if state[i] != state[i+1], swap them (involution).
    This is reversible but has NO coherence bias.
    """
    new_state = state.copy()
    n = len(state)
    
    # Apply to even pairs
    for i in range(0, n-1, 2):
        if new_state[i] != new_state[i+1]:
            new_state[i], new_state[i+1] = new_state[i+1], new_state[i]
    
    return new_state


def coherence_aware_ca(state):
    """
    Coherence-Aware CA: same as simple_reversible_ca BUT
    only swap if it REDUCES local dissonance.
    
    This implements explicit coherence bias (UGP Axiom 3 / MDL).
    """
    new_state = state.copy()
    n = len(state)
    
    # For each potential swap, check if it reduces D
    for i in range(0, n-1, 2):
        if new_state[i] != new_state[i+1]:
            # Compute local D before swap
            local_window = 5  # Radius for local D
            i_min = max(0, i - local_window)
            i_max = min(n, i + local_window + 2)
            
            D_before = compute_dissonance(new_state[i_min:i_max])
            
            # Simulate swap
            new_state[i], new_state[i+1] = new_state[i+1], new_state[i]
            D_after = compute_dissonance(new_state[i_min:i_max])
            
            # Only keep swap if D reduced or stayed same
            if D_after > D_before:
                # Undo swap (reject)
                new_state[i], new_state[i+1] = new_state[i+1], new_state[i]
    
    return new_state


def test_system(name, update_func, grid_size=64, n_steps=500, seed=42):
    """Test a CA system for coherence emergence."""
    print(f"\n{'='*70}")
    print(f"  {name}")
    print(f"{'='*70}")
    
    np.random.seed(seed)
    
    # Initialize: two clusters (matching other tests)
    state = np.zeros(grid_size, dtype=int)
    cluster_size = grid_size // 8
    state[:cluster_size] = 1
    state[grid_size//2:grid_size//2 + cluster_size] = 1
    
    history = {'dissonance': [], 'kinks': [], 'density': []}
    
    print(f"Initial: {np.sum(state)} ones, kinks={np.sum(state != np.roll(state, 1))}")
    print(f"Evolving for {n_steps} steps...")
    
    for t in range(n_steps):
        D = compute_dissonance(state)
        kinks = np.sum(state != np.roll(state, 1))
        density = np.mean(state)
        
        history['dissonance'].append(float(D))
        history['kinks'].append(int(kinks))
        history['density'].append(float(density))
        
        if t % 100 == 0:
            print(f"  Step {t:3d}: D={D:.4f}, kinks={kinks}, ρ={density:.3f}")
        
        # Evolve
        state = update_func(state)
    
    return history


def create_comparison_plot(results, output_dir):
    """Create comparison plots."""
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    
    colors = {'Rule 110': 'red', 'Simple Reversible': 'blue', 'Coherence-Aware': 'green'}
    
    # Plot 1: Dissonance
    ax = axes[0]
    for name, hist in results.items():
        ax.plot(hist['dissonance'], label=name, 
                color=colors[name], linewidth=2, alpha=0.8)
    ax.set_xlabel('Time Step', fontsize=12)
    ax.set_ylabel('Dissonance D(t)', fontsize=12)
    ax.set_title('Coherence Evolution', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(alpha=0.3)
    
    # Plot 2: Kinks
    ax = axes[1]
    for name, hist in results.items():
        ax.plot(hist['kinks'], label=name, 
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
        D_pct = ((D_f - D_i) / D_i) * 100 if D_i > 0 else 0
        
        names.append(name)
        changes.append(D_pct)
        
        if 'Coherence' in name and D_pct < -5:
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
    print("  E11 SIMPLE: COHERENCE BIAS DEMONSTRATION")
    print("  Minimal Test of Coherence-Aware Dynamics")
    print("="*70)
    print("\nHypothesis:")
    print("  Rule 110:          D ↑ (chaotic)")
    print("  Simple Reversible: D → (reversible, no bias)")
    print("  Coherence-Aware:   D ↓ (explicit MDL/compression)")
    print()
    
    n_steps = 500
    seed = 42
    
    results = {}
    
    # 1. Rule 110 (chaotic)
    results['Rule 110'] = test_system(
        "Rule 110 (Chaotic)", 
        rule110, 
        n_steps=n_steps, 
        seed=seed
    )
    
    # 2. Simple Reversible (no coherence bias)
    results['Simple Reversible'] = test_system(
        "Simple Reversible CA (No Coherence Bias)", 
        simple_reversible_ca, 
        n_steps=n_steps, 
        seed=seed
    )
    
    # 3. Coherence-Aware (WITH bias)
    results['Coherence-Aware'] = test_system(
        "Coherence-Aware CA (Explicit MDL Bias)", 
        coherence_aware_ca, 
        n_steps=n_steps, 
        seed=seed
    )
    
    # Analysis
    print("\n" + "="*70)
    print("  RESULTS SUMMARY")
    print("="*70)
    
    for name, hist in results.items():
        D_i = hist['dissonance'][0]
        D_f = hist['dissonance'][-1]
        D_pct = ((D_f - D_i) / D_i) * 100 if D_i > 0 else 0
        
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
        
        print(f"\n{name}:")
        print(f"  D: {D_i:.4f} → {D_f:.4f} ({D_pct:+.1f}%)")
        print(f"  Kinks: {kinks_i} → {kinks_f}")
        print(f"  {verdict}")
    
    # Save
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"E11_simple_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    
    with open(f"{output_dir}/results.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Results saved: {output_dir}/results.json")
    
    # Create plots
    create_comparison_plot(results, output_dir)
    
    print("\n" + "="*70)
    print("  CONCLUSION")
    print("="*70)
    print("\nIf Coherence-Aware CA shows D ↓ while others show D ↑ or D →,")
    print("this validates that EXPLICIT coherence bias (UGP Axiom 3/MDL)")
    print("is NECESSARY for emergent coherence.")
    print("\nThis supports the paper's claim that coherence requires")
    print("coherence-biased dynamics, not just reversibility.")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()

