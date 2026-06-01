#!/usr/bin/env python3
"""
Test Script for Extended Discrete Search (144 combinations)

This script tests the extended discrete search with all possible combinations:
- E-orientations: 2 (13-torque, mu-tau anchor)
- νR permutations: 6 (S3 permutations)
- Integrators: 2 (Strang, Yoshida)
- Phase fractions: 3 (1.0, 0.5, 0.0)
- BCH options: 2 (off, on)

Total: 2 × 6 × 2 × 3 × 2 = 144 combinations
"""

import numpy as np
import yaml
from pathlib import Path
import sys
import os
import json
from datetime import datetime

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ugp_discovery_lab.experiments.ugp_single_law_uuf_flow_theoretical_upgrades import UGPSingleLawUUFFlowTheoreticalUpgrades  # type: ignore

def test_extended_discrete_search():
    """Test the extended discrete search over 144 combinations."""
    
    print("🔬 TESTING EXTENDED DISCRETE SEARCH (144 combinations)")
    print("=" * 70)
    
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
    
    # Run extended discrete search
    print(f"\n🚀 Starting extended discrete search...")
    start_time = datetime.now()
    
    try:
        search_results = experiment._extended_discrete_search()
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        print(f"\n⏱️ Search completed in: {duration}")
        
        # Analyze results
        total_combinations = search_results['total_combinations']
        successful_combinations = search_results['successful_combinations']
        ckm_hard_gate_passed = search_results['ckm_hard_gate_passed']
        best_result = search_results['best_result']
        
        print(f"\n📊 EXTENDED DISCRETE SEARCH RESULTS:")
        print(f"Total combinations tested: {total_combinations}")
        print(f"Successful combinations: {successful_combinations}")
        print(f"CKM hard gate passed: {ckm_hard_gate_passed}")
        print(f"Success rate: {successful_combinations/total_combinations*100:.1f}%")
        print(f"CKM preservation rate: {ckm_hard_gate_passed/successful_combinations*100:.1f}%" if successful_combinations > 0 else "CKM preservation rate: N/A")
        
        if best_result:
            print(f"\n🏆 BEST COMBINATION FOUND:")
            print(f"E-orientation: {best_result['e_orientation']}")
            print(f"νR permutation: {best_result['nuR_permutation']}")
            print(f"Integrator: {best_result['integrator']}")
            print(f"Phase fraction: {best_result['phase_fraction']}")
            print(f"BCH enabled: {best_result['bch_enabled']}")
            print(f"CKM errors: θ₁₂={best_result['ckm_errors'][0]:.2f}%, θ₁₃={best_result['ckm_errors'][1]:.2f}%, θ₂₃={best_result['ckm_errors'][2]:.2f}%")
            print(f"PMNS errors: θ₁₂={best_result['pmns_errors'][0]:.2f}%, θ₁₃={best_result['pmns_errors'][1]:.2f}%, θ₂₃={best_result['pmns_errors'][2]:.2f}%")
            print(f"CKM average error: {best_result['ckm_avg_error']:.2f}%")
            print(f"PMNS average error: {best_result['pmns_avg_error']:.2f}%")
            print(f"Overall average error: {best_result['overall_avg_error']:.2f}%")
            
            # Assessment
            if best_result['ckm_avg_error'] < 5.0 and best_result['pmns_avg_error'] < 15.0:
                print(f"\n🎉 EXTENDED SEARCH SUCCESS!")
                print(f"✅ CKM preservation achieved (error: {best_result['ckm_avg_error']:.2f}%)")
                print(f"✅ PMNS improvement achieved (error: {best_result['pmns_avg_error']:.2f}%)")
                success = True
            elif best_result['ckm_avg_error'] < 5.0:
                print(f"\n✅ CKM PRESERVATION SUCCESS!")
                print(f"✅ CKM preservation achieved (error: {best_result['ckm_avg_error']:.2f}%)")
                print(f"⚠️ PMNS needs further work (error: {best_result['pmns_avg_error']:.2f}%)")
                success = True
            else:
                print(f"\n⚠️ MIXED RESULTS")
                print(f"❌ CKM preservation failed (error: {best_result['ckm_avg_error']:.2f}%)")
                print(f"⚠️ PMNS results: {best_result['pmns_avg_error']:.2f}% error")
                success = False
        else:
            print(f"\n❌ NO SUCCESSFUL COMBINATIONS FOUND")
            success = False
        
        # Save detailed results
        results_file = project_root / "extended_discrete_search_results.json"
        with open(results_file, 'w') as f:
            json.dump(search_results, f, indent=2, default=str)
        print(f"\n💾 Detailed results saved to: {results_file}")
        
        return success
        
    except Exception as e:
        print(f"❌ Extended discrete search failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_specific_combinations():
    """Test specific interesting combinations."""
    
    print(f"\n🧪 TESTING SPECIFIC COMBINATIONS")
    print("-" * 50)
    
    # Load configuration
    config_path = project_root / "configs" / "experiments" / "ugp_single_law_uuf_flow_theoretical_upgrades.yaml"
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    experiment = UGPSingleLawUUFFlowTheoreticalUpgrades(config, project_root)
    
    # Test specific combinations
    test_combinations = [
        {
            'name': '13-torque + Strang + BCH + Phase 1.0',
            'e_orientation': '13_torque',
            'integrator': 'strang',
            'bch_enabled': True,
            'phase_fraction': 1.0
        },
        {
            'name': 'mu-tau anchor + Yoshida + BCH + Phase 0.5',
            'e_orientation': 'mu_tau_anchor',
            'integrator': 'yoshida',
            'bch_enabled': True,
            'phase_fraction': 0.5
        },
        {
            'name': '13-torque + Yoshida + No BCH + Phase 0.0',
            'e_orientation': '13_torque',
            'integrator': 'yoshida',
            'bch_enabled': False,
            'phase_fraction': 0.0
        }
    ]
    
    for i, combo in enumerate(test_combinations):
        print(f"\n📊 Testing combination {i+1}: {combo['name']}")
        
        # Update configuration
        experiment.cfg['options']['theoretical_upgrades']['e_orientation_method'] = combo['e_orientation']
        experiment.cfg['options']['theoretical_upgrades']['integrator_method'] = combo['integrator']
        experiment.cfg['options']['theoretical_upgrades']['bch_preconditioning'] = combo['bch_enabled']
        experiment.cfg['options']['theoretical_upgrades']['majorana_E_phase_fraction'] = combo['phase_fraction']
        
        try:
            # Run the experiment
            result = experiment.run_task('single_law_uuf_flow')
            
            if result['status'] == 'success':
                # Extract results
                mixing_matrices = result['mixing_matrices']
                ckm_angles = mixing_matrices['ckm_angles']
                pmns_angles = mixing_matrices['pmns_angles']
                
                # Calculate errors
                ckm_errors = [
                    abs(ckm_angles['theta12'] - 33.44) / 33.44 * 100,
                    abs(ckm_angles['theta13'] - 8.57) / 8.57 * 100,
                    abs(ckm_angles['theta23'] - 49.2) / 49.2 * 100
                ]
                
                pmns_errors = [
                    abs(pmns_angles['theta12'] - 33.44) / 33.44 * 100,
                    abs(pmns_angles['theta13'] - 8.57) / 8.57 * 100,
                    abs(pmns_angles['theta23'] - 49.0) / 49.0 * 100
                ]
                
                ckm_avg_error = np.mean(ckm_errors)
                pmns_avg_error = np.mean(pmns_errors)
                
                print(f"  CKM Errors: θ₁₂={ckm_errors[0]:.2f}%, θ₁₃={ckm_errors[1]:.2f}%, θ₂₃={ckm_errors[2]:.2f}%")
                print(f"  PMNS Errors: θ₁₂={pmns_errors[0]:.2f}%, θ₁₃={pmns_errors[1]:.2f}%, θ₂₃={pmns_errors[2]:.2f}%")
                print(f"  CKM Average: {ckm_avg_error:.2f}%")
                print(f"  PMNS Average: {pmns_avg_error:.2f}%")
                
                if ckm_avg_error < 5.0:
                    print(f"  ✅ CKM PRESERVATION: PASSED")
                else:
                    print(f"  ❌ CKM PRESERVATION: FAILED")
                    
            else:
                print(f"  ❌ Experiment failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 STARTING EXTENDED DISCRETE SEARCH TEST")
    print("=" * 70)
    
    # Test specific combinations first (quick test)
    test_specific_combinations()
    
    # Run the full 144-combination search automatically
    print(f"\n🚀 Running full 144-combination search...")
    print("This will take several minutes to complete.")
    
    success = test_extended_discrete_search()
    print(f"\n🎯 FINAL STATUS: {'SUCCESS' if success else 'NEEDS WORK'}")
    
    print("=" * 70)
