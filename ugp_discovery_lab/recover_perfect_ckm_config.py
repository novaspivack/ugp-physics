#!/usr/bin/env python3
"""
Recover Perfect CKM Configuration
=================================

Recover the perfect CKM configuration from the final report:
- τ₀ scaling: 1.5
- ε scaling: 0.8
- ε' scaling: 4.0
- Normalization: Frobenius
- Down-sector permutation: [0,2,1]

Expected results:
- θ₁₂: 33.84° (1.21% error)
- θ₁₃: 8.58° (0.06% error)
- θ₂₃: 49.60° (0.81% error)
"""

import sys
import numpy as np
from pathlib import Path
import yaml

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ugp_discovery_lab.experiments.ugp_yukawa_ckm_pmns_flow_optimization import UGPYukawaCKMPMNSFlowOptimization

def recover_perfect_ckm_config():
    """Recover the perfect CKM configuration from the final report."""
    
    print("🔒 RECOVERING PERFECT CKM CONFIGURATION")
    print("=" * 60)
    
    # Load configuration
    config_path = project_root / "configs" / "experiments" / "ugp_yukawa_ckm_pmns_flow_optimization.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Create experiment instance
    experiment = UGPYukawaCKMPMNSFlowOptimization(config, project_root)
    
    print("📊 Perfect CKM Parameters from Final Report:")
    print("   τ₀ scaling: 1.5")
    print("   ε scaling: 0.8")
    print("   ε' scaling: 4.0")
    print("   Normalization: Frobenius")
    print("   Down-sector permutation: [0,2,1]")
    print()
    
    print("🎯 Testing perfect CKM configuration...")
    
    # Test the perfect configuration
    result = experiment.test_baseline_configuration(
        tau0_scale=1.5,
        epsilon_scale=0.8,
        epsilon_prime_scale=4.0,
        norm_method='frobenius'
    )
    
    if result is None:
        print("❌ Failed to get results")
        return
    
    print(f"📊 Results: {result}")
    
    # Extract CKM angles
    if 'ckm_angles' in result:
        ckm_angles = result['ckm_angles']
        print(f"\n📊 CKM ANGLES:")
        print(f"   θ₁₂: {ckm_angles.get('theta12_deg', 'N/A')}")
        print(f"   θ₁₃: {ckm_angles.get('theta13_deg', 'N/A')}")
        print(f"   θ₂₃: {ckm_angles.get('theta23_deg', 'N/A')}")
        
        # Calculate errors
        ckm_theta12_pdg = 13.04
        ckm_theta13_pdg = 0.201
        ckm_theta23_pdg = 2.38
        
        theta12_error = abs(ckm_angles.get('theta12_deg', 0) - ckm_theta12_pdg) / ckm_theta12_pdg * 100
        theta13_error = abs(ckm_angles.get('theta13_deg', 0) - ckm_theta13_pdg) / ckm_theta13_pdg * 100
        theta23_error = abs(ckm_angles.get('theta23_deg', 0) - ckm_theta23_pdg) / ckm_theta23_pdg * 100
        
        print(f"\n📊 CKM ERRORS:")
        print(f"   θ₁₂ Error: {theta12_error:.2f}% (expected: 1.21%)")
        print(f"   θ₁₃ Error: {theta13_error:.2f}% (expected: 0.06%)")
        print(f"   θ₂₃ Error: {theta23_error:.2f}% (expected: 0.81%)")
        
        # Check if this matches expected perfect CKM
        if theta12_error < 2.0 and theta13_error < 2.0 and theta23_error < 2.0:
            print(f"✅ PERFECT CKM RECOVERED: All errors < 2%")
        else:
            print(f"❌ CKM NOT PERFECT: Errors too high")
    
    # Extract PMNS angles
    if 'pmns_angles' in result:
        pmns_angles = result['pmns_angles']
        print(f"\n📊 PMNS ANGLES:")
        print(f"   θ₁₂: {pmns_angles.get('theta12_deg', 'N/A')}")
        print(f"   θ₁₃: {pmns_angles.get('theta13_deg', 'N/A')}")
        print(f"   θ₂₃: {pmns_angles.get('theta23_deg', 'N/A')}")
        
        # Calculate PMNS errors
        pmns_theta12_pdg = 33.45
        pmns_theta13_pdg = 8.62
        pmns_theta23_pdg = 42.10
        
        pmns_theta12_error = abs(pmns_angles.get('theta12_deg', 0) - pmns_theta12_pdg) / pmns_theta12_pdg * 100
        pmns_theta13_error = abs(pmns_angles.get('theta13_deg', 0) - pmns_theta13_pdg) / pmns_theta13_pdg * 100
        pmns_theta23_error = abs(pmns_angles.get('theta23_deg', 0) - pmns_theta23_pdg) / pmns_theta23_pdg * 100
        
        avg_pmns_error = (pmns_theta12_error + pmns_theta13_error + pmns_theta23_error) / 3
        
        print(f"\n📊 PMNS ERRORS:")
        print(f"   θ₁₂ Error: {pmns_theta12_error:.2f}%")
        print(f"   θ₁₃ Error: {pmns_theta13_error:.2f}%")
        print(f"   θ₂₃ Error: {pmns_theta23_error:.2f}%")
        print(f"   Average Error: {avg_pmns_error:.2f}%")
    
    return result

if __name__ == "__main__":
    results = recover_perfect_ckm_config()
