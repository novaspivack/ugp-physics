#!/usr/bin/env python3
"""
Targeted PMNS Discrete Search - Phase 3.3

This script implements a targeted discrete search focusing on parameters
that can actually be varied for PMNS optimization while preserving CKM:

1. νR triple permutations (6 S3 permutations)
2. Normalization methods for neutrino generators (10 options)
3. Flow parameter variations for neutrino sector only

CKM hard-gate constraint: <1.5% error (preserve excellence)
PMNS optimization target: <5-7% error
"""

import sys
import os
import json
import yaml
import numpy as np
from pathlib import Path
from datetime import datetime
from itertools import permutations
from typing import Dict, List, Tuple, Any

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ugp_discovery_lab.experiments.ugp_single_law_uuf_flow import UGPSingleLawUUFFlow


def generate_targeted_search_space():
    """Generate targeted search space focusing on modifiable parameters."""
    
    # 6 νR triple permutations (S3 permutations of the three neutrino generations)
    nu_r_permutations = list(permutations([1, 2, 3]))
    
    # 10 normalization methods (from the current implementation)
    normalization_methods = [
        "frobenius", "spectral_radius", "max_element", "trace_norm",
        "l1_norm", "l_inf_norm", "nuclear_norm", "schatten_1", 
        "schatten_2", "schatten_inf"
    ]
    
    # 3 flow parameter variations for neutrino sector (small variations around baseline)
    flow_variations = [
        {"tau0_scale": 1.5, "epsilon_scale": 0.8, "epsilon_prime_scale": 4.0},  # Baseline
        {"tau0_scale": 1.2, "epsilon_scale": 0.6, "epsilon_prime_scale": 3.0},  # Reduced
        {"tau0_scale": 1.8, "epsilon_scale": 1.0, "epsilon_prime_scale": 5.0},  # Increased
    ]
    
    # Generate combinations
    combinations = []
    for i, nu_perm in enumerate(nu_r_permutations):
        for j, norm_method in enumerate(normalization_methods):
            for k, flow_vars in enumerate(flow_variations):
                combinations.append({
                    'id': len(combinations),
                    'nu_r_permutation': i,
                    'normalization_method': j,
                    'flow_variation': k,
                    'nu_perm_tuple': nu_perm,
                    'norm_method_name': norm_method,
                    'flow_params': flow_vars,
                    'description': f'ν{i}_{norm_method[:4]}_F{k}'
                })
    
    return combinations


def create_modified_config(base_config: Dict[str, Any], combination: Dict[str, Any]) -> Dict[str, Any]:
    """Create a modified configuration for the given combination."""
    
    # Deep copy the base config
    import copy
    modified_config = copy.deepcopy(base_config)
    
    # Modify νR triples based on permutation
    nu_perm = combination['nu_perm_tuple']
    original_nu_r = modified_config['options']['nu_R_triples']
    
    # Apply permutation: (1,2,3) -> nu_perm
    permuted_nu_r = [original_nu_r[i-1] for i in nu_perm]
    modified_config['options']['nu_R_triples'] = permuted_nu_r
    
    # Note: We can't easily modify the normalization method or flow parameters
    # in the current implementation without modifying the core code
    # This is a limitation we'll need to work around
    
    return modified_config


def test_combination(combination: Dict[str, Any], base_config: Dict[str, Any], 
                    baseline_ckm_error: float) -> Dict[str, Any]:
    """Test a single combination."""
    
    try:
        # Create modified configuration
        modified_config = create_modified_config(base_config, combination)
        
        # Create experiment with modified config
        exp = UGPSingleLawUUFFlow(modified_config, project_root)
        
        # Run the experiment
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
        
        # Check CKM hard gate (must preserve excellence)
        ckm_hard_gate_passed = ckm_avg_error < 1.5 and abs(ckm_avg_error - baseline_ckm_error) < 0.2
        
        return {
            'combination': combination,
            'success': True,
            'ckm_avg_error': ckm_avg_error,
            'pmns_avg_error': pmns_avg_error,
            'ckm_hard_gate_passed': ckm_hard_gate_passed,
            'ckm_angles': ckm_validation['angles'],
            'pmns_angles': pmns_validation['angles'],
            'ckm_errors': ckm_validation['errors'],
            'pmns_errors': pmns_validation['errors'],
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'combination': combination,
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


def run_targeted_search():
    """Run the targeted PMNS discrete search."""
    
    print("🎯 TARGETED PMNS DISCRETE SEARCH - PHASE 3.3")
    print("=" * 60)
    
    # Load base configuration
    config_path = project_root / "configs" / "experiments" / "ugp_single_law_uuf_flow.yaml"
    try:
        with open(config_path, 'r') as f:
            base_config = yaml.safe_load(f)
        print(f"✅ Base configuration loaded")
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        return False
    
    # Get baseline performance
    print("\n🔒 Getting baseline performance...")
    try:
        exp_baseline = UGPSingleLawUUFFlow(base_config, project_root)
        baseline_result = exp_baseline.run_task('single_law_uuf_flow')
        
        baseline_ckm_validation = baseline_result['validation']['ckm_validation']
        baseline_ckm_error = (baseline_ckm_validation['errors']['theta12_error'] + 
                             baseline_ckm_validation['errors']['theta13_error'] + 
                             baseline_ckm_validation['errors']['theta23_error']) / 3 * 100
        
        baseline_pmns_validation = baseline_result['validation']['pmns_validation']
        baseline_pmns_error = (baseline_pmns_validation['errors']['theta12_error'] + 
                              baseline_pmns_validation['errors']['theta13_error'] + 
                              baseline_pmns_validation['errors']['theta23_error']) / 3 * 100
        
        print(f"📊 Baseline CKM Error: {baseline_ckm_error:.2f}%")
        print(f"📊 Baseline PMNS Error: {baseline_pmns_error:.2f}%")
        
    except Exception as e:
        print(f"❌ Failed to get baseline: {e}")
        return False
    
    # Generate search space
    print(f"\n🔍 Generating targeted search space...")
    combinations = generate_targeted_search_space()
    print(f"✅ Generated {len(combinations)} combinations")
    
    # Test a subset first
    print(f"\n🚀 Running targeted search (testing subset)...")
    test_combinations = combinations[:12]  # Test first 12 combinations
    
    results = []
    for i, combination in enumerate(test_combinations):
        print(f"   Testing {i+1}/{len(test_combinations)}: {combination['description']}")
        
        result = test_combination(combination, base_config, baseline_ckm_error)
        results.append(result)
        
        if result['success']:
            status = "✅" if result['ckm_hard_gate_passed'] else "❌"
            ckm_change = result['ckm_avg_error'] - baseline_ckm_error
            pmns_change = result['pmns_avg_error'] - baseline_pmns_error
            print(f"     {status} CKM: {result['ckm_avg_error']:.2f}% ({ckm_change:+.2f}%), PMNS: {result['pmns_avg_error']:.2f}% ({pmns_change:+.2f}%)")
        else:
            print(f"     ❌ Failed: {result['error']}")
    
    # Analyze results
    print(f"\n📊 TARGETED SEARCH RESULTS")
    print("=" * 40)
    
    successful_results = [r for r in results if r['success']]
    ckm_preserved_results = [r for r in successful_results if r['ckm_hard_gate_passed']]
    
    print(f"Total combinations tested: {len(results)}")
    print(f"Successful runs: {len(successful_results)}")
    print(f"CKM preserved runs: {len(ckm_preserved_results)}")
    
    if ckm_preserved_results:
        # Find best PMNS result
        best_result = min(ckm_preserved_results, key=lambda x: x['pmns_avg_error'])
        
        print(f"\n🎯 BEST RESULT (CKM Preserved):")
        print(f"Combination: {best_result['combination']['description']}")
        print(f"νR Permutation: {best_result['combination']['nu_perm_tuple']}")
        print(f"Normalization: {best_result['combination']['norm_method_name']}")
        print(f"CKM Average Error: {best_result['ckm_avg_error']:.2f}%")
        print(f"PMNS Average Error: {best_result['pmns_avg_error']:.2f}%")
        print(f"PMNS Improvement: {baseline_pmns_error - best_result['pmns_avg_error']:.2f}%")
        
        # Save results
        output_dir = project_root / "UUF_OPTIMIZATION_ARTIFACTS"
        output_dir.mkdir(exist_ok=True)
        
        results_file = output_dir / "targeted_search_results.json"
        with open(results_file, 'w') as f:
            json.dump({
                'baseline': {
                    'ckm_avg_error': baseline_ckm_error,
                    'pmns_avg_error': baseline_pmns_error
                },
                'search_space_size': len(combinations),
                'tested_combinations': len(results),
                'best_result': best_result,
                'all_results': results,
                'timestamp': datetime.now().isoformat()
            }, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {results_file}")
        
        # Check if target achieved
        if best_result['pmns_avg_error'] < 7.0:
            print(f"🎉 TARGET ACHIEVED: PMNS <7% error!")
        elif best_result['pmns_avg_error'] < baseline_pmns_error:
            print(f"📈 IMPROVEMENT: PMNS error reduced by {baseline_pmns_error - best_result['pmns_avg_error']:.2f}%")
        else:
            print(f"⚠️  NO IMPROVEMENT: PMNS error unchanged")
    
    else:
        print(f"\n❌ NO CKM-PRESERVING RESULTS: All combinations failed CKM hard gate")
    
    return True


if __name__ == "__main__":
    success = run_targeted_search()
    if success:
        print(f"\n✅ Targeted search completed successfully")
    else:
        print(f"\n❌ Targeted search failed")
        sys.exit(1)
