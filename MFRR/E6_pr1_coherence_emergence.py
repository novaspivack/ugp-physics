#!/usr/bin/env python3
"""
E6: PR-1 vs Rule 110 Coherence Comparison
==========================================

Empirical test to determine whether PR-1's reversible, UGP-constrained
substrate produces D-minimization compared to chaotic universal CAs.

THEORETICAL PREDICTION (to be tested):
- Reversibility + UGP constraints → potential D-minimization
- Chaotic universal CAs (Rule 110) → no D-minimization

CRITICAL: PR-1 is NOT explicitly designed to minimize D. This test
empirically determines whether reversibility and UGP constraints
are SUFFICIENT for coherence emergence.

Reference: MFRR Appendix H, §3.6 (Ontological Dissonance)
Baseline: AppendixH_Minimal_Reflexive_System.py (Rule 110)
PR-1 Spec: SESSION_10_21_CANONICAL_PR1_RULE_SPECIFICATION.md
Author: Nova Spivack
Date: November 3, 2025
"""

import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, Tuple
import json
from datetime import datetime

# Add PR-1 infrastructure to path
base_dir = Path(__file__).parent.parent  # ugp-physics repository root (MFRR/ → ugp-physics/)
pr1_root = base_dir / "PR-1_UGP_Loop_CA"
logos_search = pr1_root / "logos_search"
logos_experiment = logos_search / "logos_derivation_experiment"

sys.path.insert(0, str(logos_search))  # For pr1_core
sys.path.insert(0, str(pr1_root))  # For seed_strategies
sys.path.insert(0, str(logos_experiment / "src"))  # For executors

try:
    from pr1_core import PR1Grid, PR1Cell, UGPSidechannels, PR1RuleSpec
    from unilogos_executor_configurable_v3 import ConfigurableUniLogosExecutor
    from rule_number_converter import get_full_rule_spec_v2
    from seed_strategies import TwoClusterStrategy
    PR1_AVAILABLE = True
    print("✅ PR-1 infrastructure loaded successfully")
except ImportError as e:
    print(f"⚠️  PR-1 infrastructure not available: {e}")
    print("⚠️  Will run Rule 110 comparison only")
    PR1_AVAILABLE = False


# ============================================================================
# RULE 110 BASELINE (from Appendix H)
# ============================================================================

class Rule110Evaluator:
    """Rule 110 - chaotic universal CA (baseline for comparison)"""
    def __init__(self, size: int):
        self.size = size
        
    def evaluate(self, state: np.ndarray) -> np.ndarray:
        """Apply Rule 110"""
        new_state = state.copy()
        for i in range(self.size):
            left = state[(i-1) % self.size]
            center = state[i]
            right = state[(i+1) % self.size]
            pattern = (left << 2) | (center << 1) | right
            rule_110 = [0, 1, 1, 1, 0, 1, 1, 0]  
            new_state[i] = rule_110[pattern]
        return new_state


# ============================================================================
# DISSONANCE FUNCTIONALS
# ============================================================================

def compute_dissonance_bitstring(state: np.ndarray) -> float:
    """
    Dissonance for simple bitstring (Rule 110).
    D_inc: spatial roughness (transitions)
    D_comp: incompleteness (deviation from 50%)
    """
    transitions = np.sum(np.abs(np.diff(np.concatenate([state, [state[0]]]))))
    D_inc = transitions / len(state)
    
    density = np.mean(state)
    D_comp = abs(density - 0.5)
    
    D = 0.6 * D_inc + 0.4 * D_comp
    return D


def compute_dissonance_pr1(grid: 'PR1Grid') -> float:
    """
    Dissonance for PR-1's 4-field system (g, l, μ, m).
    
    D_inc: spatial roughness across all fields
    D_comp: field balance/uniformity
    D_temp: m-field defects (kink density)
    D_clos: phase coherence (g-field uniformity)
    """
    if not PR1_AVAILABLE:
        return 0.0
        
    N = grid.size
    
    # D_inc: Count field transitions
    g_trans = np.sum(grid.g != np.roll(grid.g, 1)) / N
    l_trans = np.sum(grid.l != np.roll(grid.l, 1)) / N
    mu_trans = np.sum(grid.mu != np.roll(grid.mu, 1)) / N
    m_trans = np.sum(grid.m != np.roll(grid.m, 1)) / N  # Kink density
    D_inc = (g_trans + l_trans + mu_trans) / 3.0
    
    # D_temp: m-field kink density (topological defects)
    D_temp = m_trans
    
    # D_comp: Field value distribution (entropy proxy)
    g_entropy = -np.sum(np.bincount(grid.g, minlength=4) / N * np.log(np.bincount(grid.g, minlength=4) / N + 1e-10))
    l_entropy = -np.sum(np.bincount(grid.l, minlength=8) / N * np.log(np.bincount(grid.l, minlength=8) / N + 1e-10))
    D_comp = 1.0 - (g_entropy / np.log(4) + l_entropy / np.log(8)) / 2.0  # Normalized
    
    # D_clos: Phase coherence (g-field clustering)
    g_var = np.var(grid.g.astype(float))
    D_clos = g_var / 2.0  # Normalized by max variance for Z₄
    
    # Combined (weighted as in MFRR §3.6)
    w_inc, w_comp, w_temp, w_clos = 0.3, 0.2, 0.3, 0.2
    D = w_inc * D_inc + w_comp * D_comp + w_temp * D_temp + w_clos * D_clos
    
    return D


# ============================================================================
# PR-1 RUNNER
# ============================================================================

def run_pr1_evolution(
    rule_id: str = "R580997408235520",
    grid_size: int = 512,
    n_steps: int = 200,
    seed: int = 42
) -> Dict:
    """
    Run PR-1 winner rule and measure D(t) evolution.
    """
    if not PR1_AVAILABLE:
        print("❌ PR-1 infrastructure not available")
        return {'error': 'PR1 not available'}
    
    print("\n" + "=" * 70)
    print(f"  PR-1 COHERENCE TEST: {rule_id}")
    print("=" * 70)
    
    # Decode rule
    try:
        rule_spec = get_full_rule_spec_v2(rule_id)
        print(f"✅ Rule decoded: {rule_id}")
        print(f"   X-mask: {rule_spec.x_required_mask}")
        print(f"   R-forbidden: {rule_spec.r_forbidden_mask}")
    except Exception as e:
        print(f"❌ Error decoding rule: {e}")
        return {'error': str(e)}
    
    # Initialize grid with TwoCluster seed (matches Rule 110 test)
    np.random.seed(seed)
    grid = PR1Grid(grid_size)
    
    # Use TwoCluster strategy (same as SESSION 15 cosmology tests)
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
    
    actual_density = np.sum(grid.m) / grid_size
    print(f"✅ Grid initialized: {grid_size} cells, TwoCluster seed")
    print(f"   Cluster 1 & 2: density ≈ 0.6")
    print(f"   Background: density ≈ 0.0")
    print(f"   Overall m-field density: {actual_density:.3f}")
    
    # Initialize sidechannels
    sidechannels = UGPSidechannels.init_demo(grid_size)
    
    # Create executor
    executor = ConfigurableUniLogosExecutor(grid_size=grid_size)
    executor.configure(
        r_rotation=rule_spec.r_rotation,
        x_transform=rule_spec.x_transform,
        s_shear=rule_spec.s_shear,
        s_condition=rule_spec.s_condition,
        r_forbidden_mask=rule_spec.r_forbidden_mask,
        x_required_mask=rule_spec.x_required_mask,
        even_perm=rule_spec.even_perm,
        odd_perm=rule_spec.odd_perm,
        phase_order=rule_spec.phase_order,
        witness_enabled=rule_spec.witness_enabled,
        witness_mode=rule_spec.witness_mode
    )
    
    # Evolution
    history = {
        'dissonance': [],
        'kink_density': [],
        'g_phase_variance': [],
        'l_field_entropy': []
    }
    
    print(f"\nEvolving for {n_steps} steps...")
    
    for t in range(n_steps):
        # Measure dissonance
        D_t = compute_dissonance_pr1(grid)
        kink_density = np.sum(grid.m != np.roll(grid.m, 1)) / grid_size
        g_var = np.var(grid.g.astype(float))
        l_entropy = -np.sum(np.bincount(grid.l, minlength=8) / grid_size * 
                           np.log(np.bincount(grid.l, minlength=8) / grid_size + 1e-10))
        
        history['dissonance'].append(D_t)
        history['kink_density'].append(kink_density)
        history['g_phase_variance'].append(g_var)
        history['l_field_entropy'].append(l_entropy)
        
        if t % 50 == 0:
            print(f"  Step {t:4d}: D = {D_t:.4f}, kinks = {kink_density:.3f}")
        
        # Evolve one step (PR-1 uses sigma field for T/T† alternation)
        sigma = np.ones(grid_size, dtype=np.uint8)  # Dummy sigma field
        executor.evolve_with_sigma(grid, sigma, sidechannels)
    
    return history


# ============================================================================
# RULE 110 RUNNER (Baseline)
# ============================================================================

def run_rule110_evolution(
    grid_size: int = 512,
    n_steps: int = 200,
    seed: int = 42,
    use_two_cluster: bool = True
) -> Dict:
    """
    Run Rule 110 (chaotic CA) and measure D(t) evolution.
    This is the baseline from Appendix H.
    """
    print("\n" + "=" * 70)
    print("  RULE 110 BASELINE (Chaotic Universal CA)")
    print("=" * 70)
    
    np.random.seed(seed)
    evaluator = Rule110Evaluator(grid_size)
    
    # Initialize: TwoCluster seed (same structure as PR-1 test)
    if use_two_cluster:
        state = np.zeros(grid_size, dtype=int)
        # Cluster 1: first 1/4 of grid
        cluster1_start = 0
        cluster1_end = grid_size // 4
        for i in range(cluster1_start, cluster1_end):
            if np.random.random() < 0.6:
                state[i] = 1
        
        # Cluster 2: around 3/4 point
        cluster2_start = 3 * grid_size // 4
        cluster2_end = grid_size
        for i in range(cluster2_start, cluster2_end):
            if np.random.random() < 0.6:
                state[i] = 1
        
        print(f"✅ Grid initialized: {grid_size} bits, TwoCluster seed")
        print(f"   Cluster 1: [{cluster1_start}:{cluster1_end}], density ≈ 0.6")
        print(f"   Cluster 2: [{cluster2_start}:{cluster2_end}], density ≈ 0.6")
        print(f"   Background: density ≈ 0.0")
        print(f"   Overall density: {np.mean(state):.3f}")
    else:
        state = np.random.randint(0, 2, size=grid_size)
        print(f"✅ Grid initialized: {grid_size} bits, random, density = {np.mean(state):.2f}")
    
    history = {
        'dissonance': [],
        'bit_density': [],
        'transitions': []
    }
    
    print(f"\nEvolving for {n_steps} steps...")
    
    for t in range(n_steps):
        D_t = compute_dissonance_bitstring(state)
        density = np.mean(state)
        transitions = np.sum(np.abs(np.diff(np.concatenate([state, [state[0]]])))) / grid_size
        
        history['dissonance'].append(D_t)
        history['bit_density'].append(density)
        history['transitions'].append(transitions)
        
        if t % 50 == 0:
            print(f"  Step {t:4d}: D = {D_t:.4f}, density = {density:.3f}")
        
        # Evolve
        state = evaluator.evaluate(state)
    
    return history


# ============================================================================
# ANALYSIS & COMPARISON
# ============================================================================

def analyze_coherence_emergence(pr1_history: Dict, rule110_history: Dict) -> Dict:
    """
    Compare coherence emergence between PR-1 and Rule 110.
    
    Key prediction: PR-1 should show D↓ (coherence), Rule 110 should not.
    """
    print("\n" + "=" * 70)
    print("  COHERENCE EMERGENCE ANALYSIS")
    print("=" * 70)
    
    results = {}
    
    # Analyze Rule 110 (baseline)
    D_rule110 = np.array(rule110_history['dissonance'])
    D_rule110_initial = np.mean(D_rule110[:20])
    D_rule110_final = np.mean(D_rule110[-20:])
    D_rule110_trend = (D_rule110_final - D_rule110_initial) / D_rule110_initial * 100
    
    print("\n1. RULE 110 (Chaotic, Non-Reversible)")
    print(f"   Initial D: {D_rule110_initial:.4f}")
    print(f"   Final D:   {D_rule110_final:.4f}")
    print(f"   Change:    {D_rule110_trend:+.1f}%")
    
    if D_rule110_trend < -10:
        print("   ⚠️  Unexpected coherence (chaotic CA)")
        results['rule110_coherent'] = True
    else:
        print("   ✅ Expected: No coherence (D flat/increasing)")
        results['rule110_coherent'] = False
    
    results['rule110_initial'] = float(D_rule110_initial)
    results['rule110_final'] = float(D_rule110_final)
    results['rule110_trend'] = float(D_rule110_trend)
    
    # Analyze PR-1 (coherence-biased)
    if PR1_AVAILABLE and 'dissonance' in pr1_history:
        D_pr1 = np.array(pr1_history['dissonance'])
        D_pr1_initial = np.mean(D_pr1[:20])
        D_pr1_final = np.mean(D_pr1[-20:])
        D_pr1_trend = (D_pr1_final - D_pr1_initial) / D_pr1_initial * 100
        
        print("\n2. PR-1 Winner (R580997408235520, Reversible + UGP-Constrained)")
        print(f"   Initial D: {D_pr1_initial:.4f}")
        print(f"   Final D:   {D_pr1_final:.4f}")
        print(f"   Change:    {D_pr1_trend:+.1f}%")
        
        if D_pr1_trend < -10:
            print("   ✅ D DECREASED (coherence emerged!)")
            print("   → Reversibility + UGP constraints SUFFICIENT for coherence")
            results['pr1_coherent'] = True
        elif abs(D_pr1_trend) < 10:
            print("   ⚠️  D STABLE (equilibrium)")
            print("   → Reversibility maintains structure but doesn't improve it")
            results['pr1_coherent'] = 'equilibrium'
        else:
            print("   ❌ D INCREASED (no coherence)")
            print("   → Reversibility alone insufficient")
            results['pr1_coherent'] = False
        
        results['pr1_initial'] = float(D_pr1_initial)
        results['pr1_final'] = float(D_pr1_final)
        results['pr1_trend'] = float(D_pr1_trend)
        
        # Comparison
        print("\n3. COMPARISON")
        print(f"   ΔD(Rule 110): {D_rule110_trend:+.1f}%")
        print(f"   ΔD(PR-1):     {D_pr1_trend:+.1f}%")
        print(f"   Difference:   {D_pr1_trend - D_rule110_trend:.1f} percentage points")
        
        if D_pr1_trend < D_rule110_trend - 10:
            print("   ✅ PR-1 shows GREATER coherence than Rule 110")
            print("   ✅ EMPIRICAL EVIDENCE: Reversibility + UGP → D-minimization")
            results['validation'] = 'PASS'
        elif abs(D_pr1_trend - D_rule110_trend) < 10:
            print("   ⚠️  Similar behavior (both equilibrium)")
            results['validation'] = 'INCONCLUSIVE'
        else:
            print("   ❌ PR-1 LESS coherent than Rule 110")
            print("   ❌ Unexpected result")
            results['validation'] = 'FAIL'
    else:
        results['pr1_coherent'] = None
        results['validation'] = 'N/A'
    
    return results


# ============================================================================
# VISUALIZATION
# ============================================================================

def plot_comparison(pr1_history: Dict, rule110_history: Dict, results: Dict, 
                   filename: str = 'E6_pr1_coherence_comparison.png'):
    """
    Plot D(t) for both systems side-by-side.
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Rule 110
    steps_110 = np.arange(len(rule110_history['dissonance']))
    D_110 = rule110_history['dissonance']
    
    axes[0].plot(steps_110, D_110, 'b-', linewidth=2, label='D(t)')
    axes[0].axhline(y=results['rule110_initial'], color='gray', linestyle='--', 
                   alpha=0.5, label='Initial mean')
    axes[0].axhline(y=results['rule110_final'], color='red', linestyle='--', 
                   alpha=0.5, label='Final mean')
    axes[0].set_xlabel('Time Step', fontsize=12)
    axes[0].set_ylabel('Dissonance D', fontsize=12)
    axes[0].set_title(f'Rule 110 (Chaotic CA)\nΔD = {results["rule110_trend"]:+.1f}%', 
                     fontsize=14, fontweight='bold')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # PR-1 (if available)
    if PR1_AVAILABLE and 'dissonance' in pr1_history:
        steps_pr1 = np.arange(len(pr1_history['dissonance']))
        D_pr1 = pr1_history['dissonance']
        
        axes[1].plot(steps_pr1, D_pr1, 'g-', linewidth=2, label='D(t)')
        axes[1].axhline(y=results['pr1_initial'], color='gray', linestyle='--', 
                       alpha=0.5, label='Initial mean')
        axes[1].axhline(y=results['pr1_final'], color='red', linestyle='--', 
                       alpha=0.5, label='Final mean')
        axes[1].set_xlabel('Time Step', fontsize=12)
        axes[1].set_ylabel('Dissonance D', fontsize=12)
        axes[1].set_title(f'PR-1 Winner (Reversible + UGP-Constrained)\nΔD = {results["pr1_trend"]:+.1f}%', 
                         fontsize=14, fontweight='bold')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)
        
        # Add validation verdict
        verdict = results.get('validation', 'N/A')
        if verdict == 'PASS':
            fig.text(0.5, 0.02, '✅ VALIDATES: PR-1 shows greater coherence than Rule 110', 
                    ha='center', fontsize=13, color='green', fontweight='bold')
        elif verdict == 'INCONCLUSIVE':
            fig.text(0.5, 0.02, '⚠️  INCONCLUSIVE: Both show similar behavior', 
                    ha='center', fontsize=13, color='orange', fontweight='bold')
        else:
            fig.text(0.5, 0.02, f'Validation: {verdict}', 
                    ha='center', fontsize=13)
    else:
        axes[1].text(0.5, 0.5, 'PR-1 Test\nNot Available', 
                    ha='center', va='center', fontsize=18, color='gray')
        axes[1].set_title('PR-1 Winner', fontsize=14, fontweight='bold')
    
    plt.tight_layout(rect=[0, 0.05, 1, 1])
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    print(f"\n✅ Comparison plot saved: {filename}")
    
    return filename


# ============================================================================
# MAIN
# ============================================================================

def main():
    """
    Run the critical comparison test:
    Chaotic CA (Rule 110) vs Coherence-Biased CA (PR-1 winner)
    """
    print("\n" + "=" * 70)
    print("  E6: PR-1 vs RULE 110 COHERENCE COMPARISON")
    print("  Empirical Test: Does Reversibility + UGP → Coherence?")
    print("=" * 70)
    print("\nQUESTION TO TEST:")
    print("  Does PR-1 (reversible + UGP-constrained) show D-minimization?")
    print("  Or is reversibility alone insufficient for coherence?")
    print("\nBASELINE:")
    print("  Rule 110 (chaotic universal CA) → D flat or ↑ (no coherence)")
    print()
    
    # Run Rule 110 (baseline)
    print("\n" + "-" * 70)
    print("PHASE 1: Rule 110 Baseline")
    print("-" * 70)
    rule110_history = run_rule110_evolution(grid_size=512, n_steps=200, seed=42)
    
    # Run PR-1 (test)
    print("\n" + "-" * 70)
    print("PHASE 2: PR-1 Winner Test")
    print("-" * 70)
    if PR1_AVAILABLE:
        pr1_history = run_pr1_evolution(
            rule_id="R580997408235520",
            grid_size=512,
            n_steps=200,
            seed=42
        )
    else:
        pr1_history = {}
        print("\n⚠️  Skipping PR-1 test (infrastructure not available)")
    
    # Analyze
    results = analyze_coherence_emergence(pr1_history, rule110_history)
    
    # Visualize
    plot_filename = plot_comparison(pr1_history, rule110_history, results)
    
    # Final verdict
    print("\n" + "=" * 70)
    print("  FINAL VERDICT")
    print("=" * 70)
    
    if results.get('validation') == 'PASS':
        print("\n✅✅✅ EMPIRICAL FINDING: PR-1 SHOWS COHERENCE ✅✅✅")
        print("\nPR-1 (reversible + UGP-constrained) → D decreased")
        print("Rule 110 (chaotic universal CA) → D flat/increased")
        print("\n→ CONCLUSION: Reversibility + UGP constraints ARE sufficient")
        print("  for emergent coherence (D-minimization)")
        print("\nThis empirically validates the theoretical framework!")
    elif results.get('validation') == 'INCONCLUSIVE':
        print("\n⚠️  INCONCLUSIVE")
        print("\nBoth systems show similar D evolution (equilibrium)")
        print("May need longer runs or different D-functional")
    elif results.get('validation') == 'N/A':
        print("\n⚠️  PR-1 TEST NOT RUN")
        print("(Infrastructure not available)")
    else:
        print("\n❌ UNEXPECTED RESULT")
        print("PR-1 did not show greater coherence than Rule 110")
    
    # Save results
    output_data = {
        'metadata': {
            'date': datetime.now().isoformat(),
            'grid_size': 512,
            'n_steps': 200,
            'seed': 42
        },
        'results': results,
        'rule110_history': {
            'dissonance': [float(x) for x in rule110_history['dissonance']],
            'bit_density': [float(x) for x in rule110_history['bit_density']]
        }
    }
    
    if PR1_AVAILABLE and 'dissonance' in pr1_history:
        output_data['pr1_history'] = {
            'dissonance': [float(x) for x in pr1_history['dissonance']],
            'kink_density': [float(x) for x in pr1_history['kink_density']]
        }
    
    with open('E6_pr1_coherence_results.json', 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n✅ Results saved: E6_pr1_coherence_results.json")
    print(f"✅ Plot saved: {plot_filename}")
    
    return results


if __name__ == "__main__":
    main()

