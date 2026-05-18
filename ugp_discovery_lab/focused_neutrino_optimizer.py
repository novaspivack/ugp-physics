#!/usr/bin/env python3
"""
Focused Neutrino Triple Optimizer

This script focuses on systematic variations around our breakthrough
to find even better neutrino triple configurations.

Breakthrough: [(1,4,9), (16,25,36), (49,64,81)] → 24.95% PMNS error
Goal: Find configurations with even lower PMNS error
"""

import sys
import os
import json
import yaml
import numpy as np
import copy
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ugp_discovery_lab.experiments.ugp_single_law_uuf_flow import UGPSingleLawUUFFlow


def generate_focused_variations():
    """Generate focused variations around our breakthrough."""
    
    # Our breakthrough configuration
    breakthrough = [(1, 4, 9), (16, 25, 36), (49, 64, 81)]
    
    variations = []
    
    # 1. Variations around squares
    print("🔢 Generating square-based variations...")
    
    # Different square progressions
    square_variations = [
        # Original breakthrough
        [(1, 4, 9), (16, 25, 36), (49, 64, 81)],
        
        # Shifted squares
        [(4, 9, 16), (25, 36, 49), (64, 81, 100)],
        [(9, 16, 25), (36, 49, 64), (81, 100, 121)],
        
        # Different square patterns
        [(1, 9, 25), (36, 49, 64), (81, 100, 121)],
        [(4, 16, 36), (49, 64, 81), (100, 121, 144)],
        [(1, 16, 49), (25, 36, 64), (81, 100, 121)],
        
        # Smaller squares
        [(1, 4, 9), (16, 25, 36), (49, 64, 81)],
        [(1, 4, 9), (16, 25, 36), (64, 81, 100)],
        [(1, 4, 9), (25, 36, 49), (64, 81, 100)],
        
        # Larger squares
        [(4, 9, 16), (25, 36, 49), (64, 81, 100)],
        [(9, 16, 25), (36, 49, 64), (81, 100, 121)],
        [(16, 25, 36), (49, 64, 81), (100, 121, 144)],
    ]
    
    variations.extend(square_variations)
    
    # 2. Cube-based variations
    print("🔢 Generating cube-based variations...")
    
    cube_variations = [
        [(1, 8, 27), (64, 125, 216), (343, 512, 729)],
        [(8, 27, 64), (125, 216, 343), (512, 729, 1000)],
        [(1, 27, 125), (64, 216, 343), (512, 729, 1000)],
        [(8, 64, 216), (125, 343, 512), (729, 1000, 1331)],
    ]
    
    variations.extend(cube_variations)
    
    # 3. Fibonacci-based variations
    print("🔢 Generating Fibonacci-based variations...")
    
    fib = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144]
    fib_variations = [
        [(1, 2, 3), (5, 8, 13), (21, 34, 55)],
        [(2, 3, 5), (8, 13, 21), (34, 55, 89)],
        [(3, 5, 8), (13, 21, 34), (55, 89, 144)],
        [(1, 3, 8), (13, 21, 34), (55, 89, 144)],
        [(2, 5, 13), (21, 34, 55), (89, 144, 233)],
    ]
    
    variations.extend(fib_variations)
    
    # 4. Prime-based variations
    print("🔢 Generating prime-based variations...")
    
    primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97]
    prime_variations = [
        [(2, 3, 5), (7, 11, 13), (17, 19, 23)],
        [(3, 5, 7), (11, 13, 17), (19, 23, 29)],
        [(5, 7, 11), (13, 17, 19), (23, 29, 31)],
        [(2, 5, 11), (13, 17, 23), (29, 31, 37)],
        [(3, 7, 13), (17, 19, 29), (31, 37, 41)],
    ]
    
    variations.extend(prime_variations)
    
    # 5. Arithmetic progression variations
    print("🔢 Generating arithmetic progression variations...")
    
    arith_variations = [
        [(1, 2, 3), (4, 5, 6), (7, 8, 9)],
        [(2, 4, 6), (8, 10, 12), (14, 16, 18)],
        [(3, 6, 9), (12, 15, 18), (21, 24, 27)],
        [(1, 3, 5), (7, 9, 11), (13, 15, 17)],
        [(2, 5, 8), (11, 14, 17), (20, 23, 26)],
    ]
    
    variations.extend(arith_variations)
    
    # 6. Geometric progression variations
    print("🔢 Generating geometric progression variations...")
    
    geom_variations = [
        [(1, 2, 4), (8, 16, 32), (64, 128, 256)],
        [(2, 4, 8), (16, 32, 64), (128, 256, 512)],
        [(1, 3, 9), (27, 81, 243), (729, 2187, 6561)],
        [(2, 6, 18), (54, 162, 486), (1458, 4374, 13122)],
    ]
    
    variations.extend(geom_variations)
    
    print(f"✅ Generated {len(variations)} focused variations")
    return variations


def test_triple_set(triple_set: List[Tuple[int, int, int]], base_config: Dict[str, Any]) -> Dict[str, Any]:
    """Test a specific set of neutrino triples."""
    
    try:
        # Create modified config
        modified_config = copy.deepcopy(base_config)
        modified_config['options']['nu_R_triples'] = triple_set
        
        # Test the configuration
        exp = UGPSingleLawUUFFlow(modified_config, project_root)
        result = exp.run_task('single_law_uuf_flow')
        
        # Extract results
        ckm_validation = result['validation']['ckm_validation']
        pmns_validation = result['validation']['pmns_validation']
        
        ckm_avg_error = (ckm_validation['errors']['theta12_error'] + 
                        ckm_validation['errors']['theta13_error'] + 
                        ckm_validation['errors']['theta23_error']) / 3 * 100
        
        pmns_avg_error = (pmns_validation['errors']['theta12_error'] + 
                         pmns_validation['errors']['theta13_error'] + 
                         pmns_validation['errors']['theta23_error']) / 3 * 100
        
        # Check CKM preservation
        ckm_preserved = ckm_avg_error < 1.5 and abs(ckm_avg_error - 0.69) < 0.2
        
        return {
            'triple_set': triple_set,
            'success': True,
            'ckm_avg_error': ckm_avg_error,
            'pmns_avg_error': pmns_avg_error,
            'ckm_preserved': ckm_preserved,
            'pmns_improvement': 24.95 - pmns_avg_error,  # Improvement from current breakthrough
            'ckm_angles': ckm_validation['angles'],
            'pmns_angles': pmns_validation['angles'],
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'triple_set': triple_set,
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


def run_focused_optimization():
    """Run the focused neutrino triple optimization."""
    
    print("🎯 FOCUSED NEUTRINO TRIPLE OPTIMIZER")
    print("=" * 50)
    print("Current Breakthrough: [(1,4,9), (16,25,36), (49,64,81)] → 24.95% PMNS")
    print("Goal: Find even better configurations")
    print()
    
    # Load base configuration
    config_path = project_root / "configs" / "experiments" / "ugp_single_law_uuf_flow.yaml"
    try:
        with open(config_path, 'r') as f:
            base_config = yaml.safe_load(f)
        print(f"✅ Base configuration loaded")
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        return False
    
    # Generate focused variations
    variations = generate_focused_variations()
    
    print(f"\n🧪 Testing {len(variations)} focused variations...")
    
    results = []
    improvements = []
    
    for i, triple_set in enumerate(variations):
        print(f"   Testing {i+1}/{len(variations)}: {triple_set}")
        
        result = test_triple_set(triple_set, base_config)
        results.append(result)
        
        if result['success']:
            status = "✅" if result['ckm_preserved'] else "❌"
            ckm_change = result['ckm_avg_error'] - 0.69
            pmns_change = result['pmns_avg_error'] - 24.95
            print(f"     {status} CKM: {result['ckm_avg_error']:.2f}% ({ckm_change:+.2f}%), PMNS: {result['pmns_avg_error']:.2f}% ({pmns_change:+.2f}%)")
            
            if result['pmns_improvement'] > 0:
                improvements.append(result)
                print(f"     🎯 IMPROVEMENT: {result['pmns_improvement']:.2f}% better!")
        else:
            print(f"     ❌ Failed: {result['error']}")
    
    # Analyze results
    print(f"\n📊 FOCUSED OPTIMIZATION RESULTS")
    print("=" * 40)
    
    successful_results = [r for r in results if r['success']]
    ckm_preserved_results = [r for r in successful_results if r['ckm_preserved']]
    
    print(f"Total variations tested: {len(results)}")
    print(f"Successful runs: {len(successful_results)}")
    print(f"CKM preserved runs: {len(ckm_preserved_results)}")
    print(f"PMNS improvements: {len(improvements)}")
    
    if improvements:
        # Find best improvement
        best_improvement = max(improvements, key=lambda x: x['pmns_improvement'])
        
        print(f"\n🎯 BEST IMPROVEMENT:")
        print(f"Triple Set: {best_improvement['triple_set']}")
        print(f"CKM Average Error: {best_improvement['ckm_avg_error']:.2f}%")
        print(f"PMNS Average Error: {best_improvement['pmns_avg_error']:.2f}%")
        print(f"PMNS Improvement: {best_improvement['pmns_improvement']:.2f}%")
        print(f"Total Improvement from Baseline: {32.80 - best_improvement['pmns_avg_error']:.2f}%")
        
        # Save results
        output_dir = project_root / "UUF_OPTIMIZATION_ARTIFACTS"
        output_dir.mkdir(exist_ok=True)
        
        results_file = output_dir / "focused_neutrino_optimization_results.json"
        with open(results_file, 'w') as f:
            json.dump({
                'baseline': {
                    'ckm_error': 0.69,
                    'pmns_error': 32.80
                },
                'current_breakthrough': {
                    'pmns_error': 24.95,
                    'triples': [(1, 4, 9), (16, 25, 36), (49, 64, 81)]
                },
                'best_improvement': best_improvement,
                'all_improvements': improvements,
                'all_results': results,
                'timestamp': datetime.now().isoformat()
            }, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {results_file}")
        
        # Check if we've achieved significant progress
        if best_improvement['pmns_avg_error'] < 15.0:
            print(f"🎉 MAJOR BREAKTHROUGH: PMNS error < 15%!")
        elif best_improvement['pmns_avg_error'] < 20.0:
            print(f"🎯 SIGNIFICANT BREAKTHROUGH: PMNS error < 20%!")
        elif best_improvement['pmns_avg_error'] < 24.95:
            print(f"📈 IMPROVEMENT: PMNS error reduced by {best_improvement['pmns_improvement']:.2f}%")
    
    else:
        print(f"\n⚠️  NO IMPROVEMENTS: All variations failed to improve PMNS")
        print("This suggests our breakthrough configuration may be near-optimal")
    
    return True


if __name__ == "__main__":
    success = run_focused_optimization()
    if success:
        print(f"\n✅ Focused neutrino optimization completed successfully")
    else:
        print(f"\n❌ Focused neutrino optimization failed")
        sys.exit(1)
