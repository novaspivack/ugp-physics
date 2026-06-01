#!/usr/bin/env python3
"""
Test Script for UGP CP Asymmetry Probe Integration

This script demonstrates how to integrate the CP asymmetry probe with our existing
UUF flow system to analyze CP violation and matter-antimatter asymmetry.
"""

import sys
import os
import json
import yaml
import numpy as np
from pathlib import Path
from datetime import datetime

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ugp_discovery_lab.experiments.ugp_cp_asymmetry_probe import UGPCPAsymmetryProbe
from ugp_discovery_lab.experiments.ugp_single_law_uuf_flow_theoretical_upgrades import UGPSingleLawUUFFlowTheoreticalUpgrades


def test_cp_asymmetry_probe_integration():
    """Test the CP asymmetry probe integrated with Single-Law flow system (working approach)."""
    
    print("🔬 TESTING UGP CP ASYMMETRY PROBE INTEGRATION")
    print("🚀 USING SINGLE-LAW APPROACH (Working & Reliable)")
    print("=" * 60)
    
    # Load Single-Law configuration (working approach)
    single_law_config_path = project_root / "configs" / "experiments" / "ugp_single_law_uuf_flow_theoretical_upgrades.yaml"
    
    try:
        with open(single_law_config_path, 'r') as f:
            single_law_config = yaml.safe_load(f)
        print(f"✅ Single-Law configuration loaded from: {single_law_config_path}")
    except Exception as e:
        print(f"❌ Failed to load Single-Law configuration: {e}")
        return False
    
    # Create Single-Law experiment instance (working approach)
    try:
        single_law_experiment = UGPSingleLawUUFFlowTheoreticalUpgrades(single_law_config, project_root)
        print("✅ Single-Law experiment instance created successfully")
    except Exception as e:
        print(f"❌ Failed to create Single-Law experiment: {e}")
        return False
    
    # Run Single-Law flow to get mixing matrices (working approach)
    print("\n🚀 Running Single-Law flow to generate mixing matrices...")
    try:
        single_law_result = single_law_experiment.run_task('single_law_uuf_flow')
        print("✅ Single-Law flow completed successfully")
    except Exception as e:
        print(f"❌ Single-Law flow failed: {e}")
        return False
    
    # Extract mixing matrices from Single-Law result (working approach)
    mixing_matrices = single_law_result.get('mixing_matrices', {})
    print(f"\n📊 Single-Law Results Summary (Working Approach):")
    
    # Display validation results from the correct structure
    validation = single_law_result.get('validation', {})
    if 'ckm_validation' in validation:
        ckm_validation = validation['ckm_validation']
        ckm_errors = ckm_validation.get('errors', {})
        print(f"  CKM θ₁₂: {ckm_errors.get('theta12_error', 0)*100:.2f}% error")
        print(f"  CKM θ₁₃: {ckm_errors.get('theta13_error', 0)*100:.2f}% error")
        print(f"  CKM θ₂₃: {ckm_errors.get('theta23_error', 0)*100:.2f}% error")
    
    if 'pmns_validation' in validation:
        pmns_validation = validation['pmns_validation']
        pmns_errors = pmns_validation.get('errors', {})
        print(f"  PMNS θ₁₂: {pmns_errors.get('theta12_error', 0)*100:.2f}% error")
        print(f"  PMNS θ₁₃: {pmns_errors.get('theta13_error', 0)*100:.2f}% error")
        print(f"  PMNS θ₂₃: {pmns_errors.get('theta23_error', 0)*100:.2f}% error")
    
    # Set up CP probe configuration
    cp_probe_config = {
        "options": {
            "kernel": {
                "phi": 1.618033988749895,  # golden ratio
                "k_gen": 1.5707963267948966  # π/2
            },
            "ugp_phase_tests": {
                "majorana_phase_fraction": [1.0, 0.5, 0.0],
                "signs": [+1, -1]
            }
        }
    }
    
    # Create CP probe instance
    try:
        cp_probe = UGPCPAsymmetryProbe(cp_probe_config, project_root)
        print("✅ CP asymmetry probe created successfully")
    except Exception as e:
        print(f"❌ Failed to create CP probe: {e}")
        return False
    
    # Set up producer function to feed UUF results to CP probe
    def producer():
        data = {}
        
        # Extract CKM matrix
        if 'V_ckm' in mixing_matrices and mixing_matrices['V_ckm'] is not None:
            data['V_ckm'] = np.array(mixing_matrices['V_ckm'], dtype=complex)
            print(f"  ✅ CKM matrix extracted: {data['V_ckm'].shape}")
        
        # Extract PMNS matrix
        if 'U_pmns' in mixing_matrices and mixing_matrices['U_pmns'] is not None:
            data['U_pmns'] = np.array(mixing_matrices['U_pmns'], dtype=complex)
            print(f"  ✅ PMNS matrix extracted: {data['U_pmns'].shape}")
        
        # Extract effective neutrino mass matrix (if available)
        if 'M_eff' in mixing_matrices and mixing_matrices['M_eff'] is not None:
            data['M_eff'] = np.array(mixing_matrices['M_eff'], dtype=complex)
            print(f"  ✅ M_eff matrix extracted: {data['M_eff'].shape}")
        
        return data
    
    # Set the producer and run CP probe
    cp_probe.set_producer(producer)
    
    print(f"\n🔬 Running CP asymmetry probe analysis...")
    try:
        cp_result = cp_probe.run_task("cp_probe")
        print("✅ CP asymmetry probe completed successfully")
    except Exception as e:
        print(f"❌ CP asymmetry probe failed: {e}")
        return False
    
    # Display results
    print(f"\n📊 CP ASYMMETRY PROBE RESULTS:")
    print("=" * 50)
    
    # Kernel information
    kernel = cp_result.get('kernel', {})
    print(f"🧮 UGP Kernel Constants:")
    print(f"  φ (golden ratio): {kernel.get('phi', 'N/A'):.15f}")
    print(f"  k_gen (π/2): {kernel.get('k_gen', 'N/A'):.15f}")
    
    # CKM observables
    ckm = cp_result.get('ckm', {})
    if ckm:
        print(f"\n🔬 CKM CP Observables:")
        if 'angles_deg' in ckm:
            angles = ckm['angles_deg']
            print(f"  θ₁₂: {angles.get('theta12', 'N/A'):.4f}°")
            print(f"  θ₁₃: {angles.get('theta13', 'N/A'):.4f}°")
            print(f"  θ₂₃: {angles.get('theta23', 'N/A'):.4f}°")
        
        if 'Jarlskog' in ckm:
            print(f"  J_CKM: {ckm['Jarlskog']:.6f}")
        
        if 'delta_deg' in ckm:
            print(f"  δ_q: {ckm['delta_deg']:.4f}°")
    
    # PMNS observables
    pmns = cp_result.get('pmns', {})
    if pmns:
        print(f"\n🔬 PMNS CP Observables:")
        if 'angles_deg' in pmns:
            angles = pmns['angles_deg']
            print(f"  θ₁₂: {angles.get('theta12', 'N/A'):.4f}°")
            print(f"  θ₁₃: {angles.get('theta13', 'N/A'):.4f}°")
            print(f"  θ₂₃: {angles.get('theta23', 'N/A'):.4f}°")
        
        if 'Jarlskog' in pmns:
            print(f"  J_PMNS: {pmns['Jarlskog']:.6f}")
        
        if 'delta_deg' in pmns:
            print(f"  δ_ℓ: {pmns['delta_deg']:.4f}°")
    
    # UGP phase tests
    phase_tests = cp_result.get('phase_tests', {})
    if phase_tests:
        print(f"\n🧪 UGP Phase Tests (Discrete, No Fitting):")
        
        if 'H1_dirac' in phase_tests:
            h1 = phase_tests['H1_dirac']
            print(f"  H1 (Dirac): δ_q ≈ σ_q * k_gen")
            print(f"    Best fit: f={h1.get('frac', 'N/A')}, σ={h1.get('sign', 'N/A')}")
            print(f"    Predicted δ_q: {np.degrees(h1.get('pred_rad', 0)):.4f}°")
            print(f"    Error: {h1.get('err_deg', 'N/A'):.4f}°")
        
        if 'H2_majorana' in phase_tests:
            h2 = phase_tests['H2_majorana']
            print(f"  H2 (Majorana): δ_ℓ ≈ σ_ℓ * f * k_gen")
            print(f"    Best fit: f={h2.get('frac', 'N/A')}, σ={h2.get('sign', 'N/A')}")
            print(f"    Predicted δ_ℓ: {np.degrees(h2.get('pred_rad', 0)):.4f}°")
            print(f"    Error: {h2.get('err_deg', 'N/A'):.4f}°")
    
    # Leptogenesis proxy
    lep = cp_result.get('leptogenesis_proxy', {})
    if lep:
        print(f"\n🌌 Leptogenesis Proxy (Dimensionless):")
        if 'm1' in lep and 'm2' in lep and 'm3' in lep:
            print(f"  ν masses: m₁={lep['m1']:.6f}, m₂={lep['m2']:.6f}, m₃={lep['m3']:.6f}")
        
        if 'H' in lep:
            print(f"  Hierarchy factor H: {lep['H']:.6f}")
        
        if 'J_pmns' in lep:
            print(f"  J_PMNS: {lep['J_pmns']:.6f}")
        
        if 'J_eff' in lep:
            print(f"  J_eff = J_PMNS × H: {lep['J_eff']:.6f}")
            print(f"  → η̂_B ∝ J_eff (baryon asymmetry proxy)")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = project_root / f"cp_asymmetry_probe_results_{timestamp}.json"
    
    try:
        with open(results_file, 'w') as f:
            json.dump(cp_result, f, indent=2, default=str)
        print(f"\n💾 Results saved to: {results_file}")
    except Exception as e:
        print(f"⚠️  Failed to save results: {e}")
    
    print(f"\n🎯 CP ASYMMETRY PROBE INTEGRATION COMPLETE")
    return True


if __name__ == "__main__":
    success = test_cp_asymmetry_probe_integration()
    if success:
        print("✅ Integration test completed successfully!")
    else:
        print("❌ Integration test failed!")
        sys.exit(1)
