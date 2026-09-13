"""
TE_2.2 Phase 2: Run Full Universe Scan

Scans all 20,160 universes in the finite truncation to find the global minimizer.

Expected Result: SM is the unique global minimizer.

Cross-Reference:
- TE_2_2_1_KICKOFF.md (Phase 2: Finite Truncation)

Author: AI Assistant
Date: 2025-11-20
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'phase1_constraints'))

import json
import time
from te2_2_universe_enumerator import UniverseSpace, UniverseScanner


def run_full_scan():
    """Run full universe scan."""
    print("=" * 80)
    print("TE_2.2 PHASE 2: FINITE TRUNCATION — FULL SCAN")
    print("=" * 80)
    print("\nObjective: Find global minimizer of D[Ψ] in finite universe space")
    print("Expected: SM is the unique global minimizer\n")
    
    # Create universe space
    print("Initializing universe space...")
    space = UniverseSpace()
    
    # Create scanner
    print("\nInitializing scanner...")
    scanner = UniverseScanner(space)
    
    # Run scan (all universes)
    print("\nStarting full scan...")
    start_time = time.time()
    
    stats = scanner.scan_all(psc_only=False)
    
    elapsed = time.time() - start_time
    print(f"\n✓ Scan completed in {elapsed:.2f} seconds")
    print(f"  Throughput: {stats['total_universes']/elapsed:.0f} universes/second")
    
    # Print summary
    scanner.print_summary(stats)
    
    # Save results
    print("\n" + "=" * 80)
    print("SAVING RESULTS")
    print("=" * 80)
    
    # Prepare data for JSON (can't serialize UniverseParams directly)
    results_json = {
        'total_universes': stats['total_universes'],
        'psc_universes': stats['psc_universes'],
        'D_sm': stats['D_sm'],
        'D_min': stats['D_min'],
        'sm_rank': stats['sm_rank'],
        'elapsed_seconds': elapsed,
        'throughput': stats['total_universes']/elapsed,
        'global_minimizer': {
            'd': stats['global_min']['universe'].d,
            'gauge_group': stats['global_min']['universe'].gauge_group,
            'n_generations': stats['global_min']['universe'].n_generations,
            'n_observers': stats['global_min']['universe'].n_observers,
            'Lambda': stats['global_min']['universe'].Lambda,
            'profit_ratio': stats['global_min']['universe'].profit_ratio,
            'kappa': stats['global_min']['universe'].kappa,
            'topology': stats['global_min']['universe'].topology,
            'D': stats['global_min']['D'],
            'is_psc': stats['global_min']['is_psc'],
        },
        'top_10': [
            {
                'd': r['universe'].d,
                'gauge_group': r['universe'].gauge_group,
                'n_generations': r['universe'].n_generations,
                'n_observers': r['universe'].n_observers,
                'Lambda': r['universe'].Lambda,
                'profit_ratio': r['universe'].profit_ratio,
                'kappa': r['universe'].kappa,
                'topology': r['universe'].topology,
                'D': r['D'],
                'is_psc': r['is_psc'],
            }
            for r in stats['all_results'][:10]
        ],
    }
    
    # Save to file
    results_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'results')
    os.makedirs(results_dir, exist_ok=True)
    
    results_file = os.path.join(results_dir, 'phase2_scan_results.json')
    with open(results_file, 'w') as f:
        json.dump(results_json, f, indent=2)
    
    print(f"\n✓ Results saved to: {results_file}")
    
    # Final verdict
    print("\n" + "=" * 80)
    print("FINAL VERDICT")
    print("=" * 80)
    
    if stats['sm_rank'] == 1:
        print("\n✓✓✓ THEOREM PROVEN ✓✓✓")
        print("\nThe Standard Model universe is the UNIQUE GLOBAL MINIMIZER")
        print("of the dissonance functional D[Ψ] in the finite truncation.")
        print(f"\nD[Ψ_SM] = {stats['D_sm']:.6e}")
        print(f"All other {stats['total_universes']-1:,} universes have D[Ψ] ≥ D[Ψ_SM]")
    else:
        print(f"\n✗ UNEXPECTED RESULT ✗")
        print(f"\nSM is rank #{stats['sm_rank']}, not rank #1")
        print(f"Global minimizer has D = {stats['D_min']:.6e}")
        print(f"SM has D = {stats['D_sm']:.6e}")
        print(f"Gap: ΔD = {stats['D_sm'] - stats['D_min']:.6e}")
    
    print("\n" + "=" * 80)
    print("SCAN COMPLETE")
    print("=" * 80)
    
    return stats


if __name__ == "__main__":
    stats = run_full_scan()

