#!/usr/bin/env python3
"""
Debug RG Evolution - Find out why it produces 0.123335 instead of 0.1279
"""

import sys
sys.path.insert(0, 'ugp_discovery_lab')

import numpy as np
from decimal import Decimal, getcontext
from ugp_discovery_lab.experiments.ugp_renormalization_finalizer_enhanced import UGPRenormalizationFinalizerEnhanced
from pathlib import Path

def debug_rg_evolution():
    """Debug the RG evolution step by step."""
    
    print("🔍 DEBUGGING RG EVOLUTION")
    print("=" * 60)
    
    # Set high precision
    getcontext().prec = 50
    
    # Configuration
    config = {
        'inputs': {
            'bare_g1_squared': '16/125',
            'particle_catalog_path': 'inputs/candidates.csv',
            'use_particle_dependent_beta': True,
            'particle_viability_threshold': 0.7,
            'particle_stability_threshold': 0.7
        },
        'hypercharge_model': {'g_factor': 1.0/3.0, 'c_state_latched_15_offset': 1.0/6.0},
        'target': {'experimental_g1_squared_at_z_pole': 0.1279}
    }
    
    # Initialize finalizer
    finalizer = UGPRenormalizationFinalizerEnhanced(config, Path('debug_output'))
    
    print(f"\n📊 CONFIGURATION:")
    print(f"g₁²_bare = {config['inputs']['bare_g1_squared']} = 0.128")
    print(f"g₁²_experimental = {config['target']['experimental_g1_squared_at_z_pole']}")
    print(f"Use particle-dependent beta: {config['inputs']['use_particle_dependent_beta']}")
    
    # Test 1: Run with original bare coupling
    print(f"\n🚀 TEST 1: Original bare coupling (0.128)")
    try:
        result1 = finalizer.run_task({'task_id': 'debug_test_1'})
        g1_final = result1.get('g1_squared_final', 'N/A')
        print(f"Result: g₁²_final = {g1_final}")
        if g1_final != 'N/A':
            error1 = (g1_final - 0.1279) / 0.1279 * 100
            print(f"Error: {error1:.3f}%")
    except Exception as e:
        print(f"ERROR: {e}")
    
    # Test 2: Test with different initial values
    print(f"\n🚀 TEST 2: Different initial values")
    
    test_values = [0.128, 0.130, 0.132, 0.135, 0.140]
    
    for test_val in test_values:
        try:
            # Create config with different bare coupling
            test_config = config.copy()
            test_config['inputs'] = config['inputs'].copy()
            test_config['inputs']['bare_g1_squared'] = str(test_val)
            
            test_finalizer = UGPRenormalizationFinalizerEnhanced(test_config, Path('debug_output'))
            result = test_finalizer.run_task({'task_id': f'debug_test_{test_val}'})
            
            g1_final = result.get('g1_squared_final', 'N/A')
            if g1_final != 'N/A':
                error = (g1_final - 0.1279) / 0.1279 * 100
                print(f"Initial {test_val:.3f} → Final {g1_final:.6f} (Error: {error:.3f}%)")
            else:
                print(f"Initial {test_val:.3f} → ERROR: No result")
        except Exception as e:
            print(f"Initial {test_val:.3f} → ERROR: {e}")
    
    # Test 3: Test with constant beta function
    print(f"\n🚀 TEST 3: Constant beta function")
    try:
        const_config = config.copy()
        const_config['inputs'] = config['inputs'].copy()
        const_config['inputs']['use_particle_dependent_beta'] = False
        
        const_finalizer = UGPRenormalizationFinalizerEnhanced(const_config, Path('debug_output'))
        result = const_finalizer.run_task({'task_id': 'debug_test_const'})
        
        g1_final = result.get('g1_squared_final', 'N/A')
        print(f"Constant beta result: g₁²_final = {g1_final}")
        if g1_final != 'N/A':
            error = (g1_final - 0.1279) / 0.1279 * 100
            print(f"Error: {error:.3f}%")
    except Exception as e:
        print(f"ERROR: {e}")
    
    # Test 4: Test different integration methods
    print(f"\n🚀 TEST 4: Different integration methods")
    
    integration_methods = ['RK45', 'RK23', 'RADAU', 'BDF', 'LSODA']
    
    for method in integration_methods:
        try:
            method_config = config.copy()
            method_config['inputs'] = config['inputs'].copy()
            method_config['inputs']['integration_method'] = method
            
            method_finalizer = UGPRenormalizationFinalizerEnhanced(method_config, Path('debug_output'))
            result = method_finalizer.run_task({'task_id': f'debug_test_{method}'})
            
            g1_final = result.get('g1_squared_final', 'N/A')
            if g1_final != 'N/A':
                error = (g1_final - 0.1279) / 0.1279 * 100
                print(f"Method {method:6s}: Final {g1_final:.6f} (Error: {error:.3f}%)")
            else:
                print(f"Method {method:6s}: ERROR: No result")
        except Exception as e:
            print(f"Method {method:6s}: ERROR - {e}")
    
    print(f"\n✅ DEBUGGING COMPLETE")

if __name__ == "__main__":
    debug_rg_evolution()
