#!/usr/bin/env python3
"""
Verify Perfect CKM Configuration
================================

Check what the perfect CKM configuration should produce and ensure
we're using the right baseline for CKM-preserving optimization.
"""

import sys
import numpy as np
from pathlib import Path
import yaml

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ugp_discovery_lab.experiments.ugp_single_law_uuf_flow import UGPSingleLawUUFFlow

def verify_perfect_ckm_config():
    """Verify what the perfect CKM configuration should produce."""
    
    print("🔒 VERIFYING PERFECT CKM CONFIGURATION")
    print("=" * 50)
    
    # Load configuration
    config_path = project_root / "configs" / "experiments" / "ugp_single_law_uuf_flow.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Create experiment instance
    experiment = UGPSingleLawUUFFlow(config, project_root)
    
    print("📊 Current canonical triples:")
    for key, value in experiment.canonical_triples.items():
        print(f"   {key}: {value}")
    
    # Build all generators first
    generators = experiment._build_all_generators()
    
    # Apply UUF flow to all sectors
    uuf_results = experiment._apply_uuf_flow_to_all_sectors(generators)
    
    if not uuf_results:
        print("❌ Failed to get UUF flow results")
        return
    
    # Calculate mixing matrices
    mixing_matrices = experiment._calculate_mixing_matrices(uuf_results)
    
    if not mixing_matrices:
        print("❌ Failed to calculate mixing matrices")
        return
    
    print(f"📊 Available mixing matrices: {list(mixing_matrices.keys())}")
    
    # Get CKM matrix
    ckm_matrix = mixing_matrices.get('V_ckm')
    if ckm_matrix is None:
        print("❌ No CKM matrix found")
        return
    
    # Convert to numpy array if needed
    if isinstance(ckm_matrix, list):
        ckm_matrix = np.array(ckm_matrix)
    
    print(f"📊 CKM Matrix Shape: {ckm_matrix.shape}")
    print(f"📊 CKM Matrix:\n{ckm_matrix}")
    
    # Extract CKM mixing angles
    def extract_mixing_angles(U):
        """Extract mixing angles from unitary matrix."""
        theta12 = np.arcsin(np.abs(U[0,1]))
        theta13 = np.arcsin(np.abs(U[0,2]))
        theta23 = np.arcsin(np.abs(U[1,2]))
        return np.degrees(theta12), np.degrees(theta13), np.degrees(theta23)
    
    ckm_theta12, ckm_theta13, ckm_theta23 = extract_mixing_angles(ckm_matrix)
    
    # PDG CKM values
    ckm_theta12_pdg = 13.04
    ckm_theta13_pdg = 0.201
    ckm_theta23_pdg = 2.38
    
    # Calculate CKM errors
    ckm_theta12_error = abs(ckm_theta12 - ckm_theta12_pdg) / ckm_theta12_pdg * 100
    ckm_theta13_error = abs(ckm_theta13 - ckm_theta13_pdg) / ckm_theta13_pdg * 100
    ckm_theta23_error = abs(ckm_theta23 - ckm_theta23_pdg) / ckm_theta23_pdg * 100
    
    print(f"\n📊 CKM RESULTS:")
    print(f"   θ₁₂: Predicted = {ckm_theta12:.2f}°, PDG = {ckm_theta12_pdg:.2f}°, Error = {ckm_theta12_error:.2f}%")
    print(f"   θ₁₃: Predicted = {ckm_theta13:.2f}°, PDG = {ckm_theta13_pdg:.2f}°, Error = {ckm_theta13_error:.2f}%")
    print(f"   θ₂₃: Predicted = {ckm_theta23:.2f}°, PDG = {ckm_theta23_pdg:.2f}°, Error = {ckm_theta23_error:.2f}%")
    
    print(f"\n📊 CKM ERRORS:")
    print(f"   θ₁₂ Error: {ckm_theta12_error:.2f}%")
    print(f"   θ₁₃ Error: {ckm_theta13_error:.2f}%")
    print(f"   θ₂₃ Error: {ckm_theta23_error:.2f}%")
    
    # Check if this matches our expected perfect CKM
    if ckm_theta12_error < 2.0 and ckm_theta13_error < 2.0 and ckm_theta23_error < 2.0:
        print(f"✅ PERFECT CKM: All errors < 2%")
    elif ckm_theta12_error < 5.0 and ckm_theta13_error < 5.0 and ckm_theta23_error < 5.0:
        print(f"✅ GOOD CKM: All errors < 5%")
    else:
        print(f"❌ POOR CKM: Errors too high - need to fix baseline")
    
    # Get PMNS results too
    pmns_matrix = mixing_matrices.get('U_pmns')
    if pmns_matrix is not None:
        if isinstance(pmns_matrix, list):
            pmns_matrix = np.array(pmns_matrix)
        
        theta12_pred, theta13_pred, theta23_pred = extract_mixing_angles(pmns_matrix)
        
        # PDG PMNS values
        theta12_pdg = 33.45
        theta13_pdg = 8.62
        theta23_pdg = 42.10
        
        # Calculate PMNS errors
        theta12_error = abs(theta12_pred - theta12_pdg) / theta12_pdg * 100
        theta13_error = abs(theta13_pred - theta13_pdg) / theta13_pdg * 100
        theta23_error = abs(theta23_pred - theta23_pdg) / theta23_pdg * 100
        
        avg_error = (theta12_error + theta13_error + theta23_error) / 3
        
        print(f"\n📊 PMNS RESULTS:")
        print(f"   θ₁₂: Predicted = {theta12_pred:.2f}°, PDG = {theta12_pdg:.2f}°, Error = {theta12_error:.2f}%")
        print(f"   θ₁₃: Predicted = {theta13_pred:.2f}°, PDG = {theta13_pdg:.2f}°, Error = {theta13_error:.2f}%")
        print(f"   θ₂₃: Predicted = {theta23_pred:.2f}°, PDG = {theta23_pdg:.2f}°, Error = {theta23_error:.2f}%")
        print(f"   Average Error: {avg_error:.2f}%")
    
    return {
        'ckm_errors': {
            'theta12': ckm_theta12_error,
            'theta13': ckm_theta13_error,
            'theta23': ckm_theta23_error
        },
        'pmns_errors': {
            'theta12': theta12_error,
            'theta13': theta13_error,
            'theta23': theta23_error,
            'avg': avg_error
        }
    }

if __name__ == "__main__":
    results = verify_perfect_ckm_config()
