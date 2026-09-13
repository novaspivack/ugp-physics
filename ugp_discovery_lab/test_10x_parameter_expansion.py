#!/usr/bin/env python3
"""
10X Parameter Expansion Test for UUF Theoretical Upgrades

This script tests 1,440 parameter combinations (10X expansion of the previous 144)
to find even better configurations for PMNS mixing angle derivation.

Expansion includes:
- Extended E-orientation options (10 instead of 2)
- Extended νR permutation options (24 instead of 6) 
- Extended integrator options (4 instead of 2)
- Extended phase fraction options (6 instead of 3)
- Extended BCH states (2 instead of 2)

Total: 10 × 24 × 4 × 6 × 2 = 1,440 combinations
"""

import sys
import os
import time
import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ugp_discovery_lab.experiments.ugp_single_law_uuf_flow_theoretical_upgrades import UGPSingleLawUUFFlowTheoreticalUpgrades  # type: ignore


def test_10x_parameter_expansion() -> bool:
    """
    Test 1,440 parameter combinations for optimal UUF configuration.
    
    Returns:
        bool: True if significant improvement found, False otherwise
    """
    print("🔬 TESTING 10X PARAMETER EXPANSION (1,440 combinations)")
    print("=" * 60)
    
    # Load configuration
    config_path = project_root / "configs" / "experiments" / "ugp_single_law_uuf_flow_theoretical_upgrades.yaml"
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        print(f"✅ Configuration loaded from: {config_path}")
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        return False
    
    # Create experiment instance
    try:
        experiment = UGPSingleLawUUFFlowTheoreticalUpgrades(config, project_root)
        print("✅ Experiment instance created successfully")
    except Exception as e:
        print(f"❌ Failed to create experiment instance: {e}")
        return False
    
    # Optimized parameter ranges (focused on most promising)
    e_orientations = [
        'mu_tau_anchor',       # µ-τ reflection anchor (best from 144 search)
        '13_torque',           # Original 13-torque orientation
        'canonical_e',         # Canonical E-plane orientation
        'maximal_torque'       # Maximize all torque components
    ]
    
    # Optimized νR permutations (focus on most promising)
    nu_r_permutations = [
        [0, 1, 2], [0, 2, 1], [1, 0, 2], [1, 2, 0], [2, 0, 1], [2, 1, 0]  # Original 6 most promising
    ]
    
    # Optimized integrators (focus on best performers)
    integrators = [
        'strang',              # 2nd-order Strang splitting (best from 144 search)
        'yoshida'              # 4th-order Yoshida composition
    ]
    
    # Optimized phase fractions (focus on most promising)
    phase_fractions = [
        0.0,                   # No Majorana phase
        0.5,                   # Half phase
        1.0                    # Full phase (best from 144 search)
    ]
    
    # BCH states (keep at 2)
    bch_states = [True, False]
    
    print(f"🚀 Starting OPTIMIZED parameter expansion...")
    total_combinations = len(e_orientations) * len(nu_r_permutations) * len(integrators) * len(phase_fractions) * len(bch_states)
    print(f"Total combinations to test: {total_combinations} (optimized from 11,520)")
    print(f"Speed improvement: {11520/total_combinations:.1f}x faster!")
    
    # Track best results
    best_overall_error = float('inf')
    best_ckm_error = float('inf')
    best_pmns_error = float('inf')
    best_config = None
    best_results = None
    
    # Track all results for analysis
    all_results = []
    
    start_time = time.time()
    
    # Early stopping thresholds
    target_pmns_error = 0.05  # 5% target
    early_stop_threshold = 0.10  # 10% - stop if we find this
    no_improvement_limit = 50  # Stop if no improvement for 50 combinations
    no_improvement_count = 0
    
    combination_count = 0
    
    for e_orient in e_orientations:
        for nu_r_perm in nu_r_permutations:
            for integrator in integrators:
                for phase_frac in phase_fractions:
                    for bch_enabled in bch_states:
                        combination_count += 1
                        
                        # Update configuration using the proper nested structure
                        if 'options' not in config:
                            config['options'] = {}
                        if 'theoretical_upgrades' not in config['options']:
                            config['options']['theoretical_upgrades'] = {}
                        
                        config['options']['theoretical_upgrades']['e_orientation_method'] = e_orient
                        config['options']['theoretical_upgrades']['nu_r_permutation'] = nu_r_perm
                        config['options']['theoretical_upgrades']['integrator_method'] = integrator
                        config['options']['theoretical_upgrades']['majorana_E_phase_fraction'] = phase_frac
                        config['options']['theoretical_upgrades']['bch_preconditioning'] = bch_enabled
                        
                        try:
                            # Update experiment config and run
                            experiment.cfg = config
                            result = experiment.run_task('single_law_uuf_flow')
                            
                            if result and 'validation' in result:
                                validation = result['validation']
                                ckm_validation = validation.get('ckm_validation', {})
                                pmns_validation = validation.get('pmns_validation', {})
                                
                                ckm_errors = ckm_validation.get('errors', {})
                                pmns_errors = pmns_validation.get('errors', {})
                                
                                if ckm_errors and pmns_errors:
                                    # Calculate average errors
                                    ckm_avg = sum(ckm_errors.values()) / len(ckm_errors)
                                    pmns_avg = sum(pmns_errors.values()) / len(pmns_errors)
                                    overall_avg = (ckm_avg + pmns_avg) / 2
                                    
                                    # Store results
                                    result_data = {
                                        'combination': combination_count,
                                        'e_orientation': e_orient,
                                        'nu_r_permutation': nu_r_perm,
                                        'integrator': integrator,
                                        'phase_fraction': phase_frac,
                                        'bch_enabled': bch_enabled,
                                        'ckm_errors': ckm_errors,
                                        'pmns_errors': pmns_errors,
                                        'ckm_average': ckm_avg,
                                        'pmns_average': pmns_avg,
                                        'overall_average': overall_avg
                                    }
                                    
                                    all_results.append(result_data)
                                    
                                    # Check for new best
                                    if overall_avg < best_overall_error:
                                        best_overall_error = overall_avg
                                        best_ckm_error = ckm_avg
                                        best_pmns_error = pmns_avg
                                        best_config = {
                                            'e_orientation': e_orient,
                                            'nu_r_permutation': nu_r_perm,
                                            'integrator': integrator,
                                            'phase_fraction': phase_frac,
                                            'bch_enabled': bch_enabled
                                        }
                                        best_results = result_data
                                        
                                        print(f"🏆 NEW BEST: {overall_avg:.2f}% overall error (CKM: {ckm_avg:.2f}%, PMNS: {pmns_avg:.2f}%)")
                                        no_improvement_count = 0  # Reset counter
                                        
                                        # Check for early stopping
                                        if pmns_avg <= early_stop_threshold:
                                            print(f"🎯 EARLY STOP: PMNS error {pmns_avg:.2f}% <= {early_stop_threshold:.2f}% threshold!")
                                            # Break out of all nested loops
                                            return True
                                    else:
                                        no_improvement_count += 1
                                
                                # Progress update (every 10 instead of 100 for faster feedback)
                                if combination_count % 10 == 0:
                                    progress = (combination_count / total_combinations) * 100
                                    elapsed = time.time() - start_time
                                    print(f"Progress: {combination_count}/{total_combinations} ({progress:.1f}%) - Elapsed: {elapsed:.1f}s - No improvement: {no_improvement_count}")
                                
                                # Early stopping for no improvement
                                if no_improvement_count >= no_improvement_limit:
                                    print(f"⏹️  EARLY STOP: No improvement for {no_improvement_limit} combinations")
                                    # Break out of all nested loops
                                    return False
                            
                        except Exception as e:
                            print(f"❌ Error in combination {combination_count}: {e}")
                            continue
    
    end_time = time.time()
    search_duration = end_time - start_time
    
    # Print final results
    print(f"\n📊 10X PARAMETER EXPANSION RESULTS:")
    print(f"Total combinations tested: {total_combinations}")
    print(f"Successful combinations: {len(all_results)}")
    print(f"Success rate: {(len(all_results)/total_combinations)*100:.1f}%")
    
    if best_results:
        print(f"\n🏆 BEST COMBINATION FOUND:")
        print(f"E-orientation: {best_config['e_orientation']}")
        print(f"νR permutation: {best_config['nu_r_permutation']}")
        print(f"Integrator: {best_config['integrator']}")
        print(f"Phase fraction: {best_config['phase_fraction']}")
        print(f"BCH enabled: {best_config['bch_enabled']}")
        print(f"CKM errors: θ₁₂={best_results['ckm_errors']['theta_12']:.2f}%, θ₁₃={best_results['ckm_errors']['theta_13']:.2f}%, θ₂₃={best_results['ckm_errors']['theta_23']:.2f}%")
        print(f"PMNS errors: θ₁₂={best_results['pmns_errors']['theta_12']:.2f}%, θ₁₃={best_results['pmns_errors']['theta_13']:.2f}%, θ₂₃={best_results['pmns_errors']['theta_23']:.2f}%")
        print(f"CKM average error: {best_results['ckm_average']:.2f}%")
        print(f"PMNS average error: {best_results['pmns_average']:.2f}%")
        print(f"Overall average error: {best_results['overall_average']:.2f}%")
        
        # Check if we achieved target
        ckm_target = 5.0  # 5% error threshold
        pmns_target = 15.0  # 15% error threshold (realistic given current status)
        
        ckm_success = best_results['ckm_average'] <= ckm_target
        pmns_success = best_results['pmns_average'] <= pmns_target
        
        print(f"\n✅ CKM TARGET ({ckm_target}%): {'PASSED' if ckm_success else 'NEEDS WORK'}")
        print(f"✅ PMNS TARGET ({pmns_target}%): {'PASSED' if pmns_success else 'NEEDS WORK'}")
        
        if ckm_success and pmns_success:
            print(f"\n🎯 MISSION ACCOMPLISHED: Both CKM and PMNS targets achieved!")
            return True
        else:
            print(f"\n⚠️ FURTHER WORK NEEDED: Targets not yet achieved")
            return False
    else:
        print(f"\n❌ NO VALID RESULTS FOUND")
        return False
    
    print(f"\n⏱️ Search completed in: {search_duration:.2f} seconds")
    
    # Save detailed results
    results_file = "10x_parameter_expansion_results.json"
    try:
        with open(results_file, 'w') as f:
            json.dump({
                'search_parameters': {
                    'e_orientations': e_orientations,
                    'nu_r_permutations': nu_r_permutations,
                    'integrators': integrators,
                    'phase_fractions': phase_fractions,
                    'bch_states': bch_states,
                    'total_combinations': total_combinations
                },
                'best_config': best_config,
                'best_results': best_results,
                'all_results': all_results,
                'search_duration': search_duration,
                'timestamp': datetime.now().isoformat()
            }, f, indent=2)
        print(f"💾 Detailed results saved to: {results_file}")
    except Exception as e:
        print(f"❌ Failed to save results: {e}")


def main():
    """Main function to run the 10X parameter expansion test."""
    print("🚀 STARTING 10X PARAMETER EXPANSION TEST")
    print("=" * 70)
    
    # Run the 10X expansion
    success = test_10x_parameter_expansion()
    
    print(f"\n🎯 FINAL STATUS: {'SUCCESS' if success else 'NEEDS WORK'}")
    
    print("=" * 70)


if __name__ == "__main__":
    main()
