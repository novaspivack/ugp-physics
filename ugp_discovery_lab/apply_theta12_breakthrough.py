#!/usr/bin/env python3
"""
Apply θ₁₂ Breakthrough Configuration
====================================

Apply the breakthrough θ₁₂ configuration (0.90% error) to the main UUF system
and verify the overall PMNS improvement.
"""

import sys
import numpy as np
from pathlib import Path
import yaml

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ugp_discovery_lab.experiments.ugp_single_law_uuf_flow import UGPSingleLawUUFFlow

def apply_theta12_breakthrough():
    """Apply the breakthrough θ₁₂ configuration and test results."""
    
    print("🎯 APPLYING θ₁₂ BREAKTHROUGH CONFIGURATION")
    print("=" * 50)
    
    # Load configuration
    config_path = project_root / "configs" / "experiments" / "ugp_single_law_uuf_flow.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Create experiment instance
    experiment = UGPSingleLawUUFFlow(config, project_root)
    
    print("📊 BREAKTHROUGH NEUTRINO TRIPLES:")
    breakthrough_triples = [(4, 5, 10), (5, 10, 4), (10, 4, 5)]
    print(f"   {breakthrough_triples}")
    
    # Apply the breakthrough configuration
    print("\n🔧 Applying breakthrough configuration...")
    
    # Override neutrino triples in canonical_triples
    for i, triple in enumerate(breakthrough_triples):
        key = (f"nu_{['e', 'mu', 'tau'][i]}", "nu", i+1)
        experiment.canonical_triples[key] = triple
        print(f"   {key}: {triple}")
    
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
    
    # Get PMNS matrix
    pmns_matrix = mixing_matrices.get('U_pmns')
    if pmns_matrix is None:
        print("❌ No PMNS matrix found")
        return
    
    # Convert to numpy array if needed
    if isinstance(pmns_matrix, list):
        pmns_matrix = np.array(pmns_matrix)
    
    print(f"📊 PMNS Matrix Shape: {pmns_matrix.shape}")
    print(f"📊 PMNS Matrix:\n{pmns_matrix}")
    
    # Extract mixing angles
    def extract_mixing_angles(U):
        """Extract mixing angles from unitary matrix."""
        # Standard parameterization
        theta12 = np.arcsin(np.abs(U[0,1]))
        theta13 = np.arcsin(np.abs(U[0,2]))
        theta23 = np.arcsin(np.abs(U[1,2]))
        
        return np.degrees(theta12), np.degrees(theta13), np.degrees(theta23)
    
    theta12_pred, theta13_pred, theta23_pred = extract_mixing_angles(pmns_matrix)
    
    # PDG values
    theta12_pdg = 33.45
    theta13_pdg = 8.62
    theta23_pdg = 42.10
    
    # Calculate errors
    theta12_error = abs(theta12_pred - theta12_pdg) / theta12_pdg * 100
    theta13_error = abs(theta13_pred - theta13_pdg) / theta13_pdg * 100
    theta23_error = abs(theta23_pred - theta23_pdg) / theta23_pdg * 100
    
    avg_error = (theta12_error + theta13_error + theta23_error) / 3
    
    print(f"\n📊 BREAKTHROUGH RESULTS:")
    print(f"   θ₁₂: Predicted = {theta12_pred:.2f}°, PDG = {theta12_pdg:.2f}°, Error = {theta12_error:.2f}%")
    print(f"   θ₁₃: Predicted = {theta13_pred:.2f}°, PDG = {theta13_pdg:.2f}°, Error = {theta13_error:.2f}%")
    print(f"   θ₂₃: Predicted = {theta23_pred:.2f}°, PDG = {theta23_pdg:.2f}°, Error = {theta23_error:.2f}%")
    
    print(f"\n📊 PERCENTAGE ERRORS:")
    print(f"   θ₁₂ Error: {theta12_error:.2f}%")
    print(f"   θ₁₃ Error: {theta13_error:.2f}%")
    print(f"   θ₂₃ Error: {theta23_error:.2f}%")
    print(f"   Average Error: {avg_error:.2f}%")
    
    # Compare with baseline
    baseline_avg_error = 9.41  # From our analysis
    improvement = baseline_avg_error - avg_error
    
    print(f"\n🎯 COMPARISON WITH BASELINE:")
    print(f"   Baseline Average Error: {baseline_avg_error:.2f}%")
    print(f"   Breakthrough Average Error: {avg_error:.2f}%")
    print(f"   Improvement: {improvement:.2f} percentage points")
    
    if avg_error < baseline_avg_error:
        print(f"✅ SUCCESS: Overall PMNS improvement achieved!")
        if avg_error < 7.0:
            print(f"🎉 BREAKTHROUGH: Average error < 7% target achieved!")
        elif avg_error < 10.0:
            print(f"🎯 GOOD PROGRESS: Average error < 10% achieved")
    else:
        print(f"⚠️  TRADEOFF: θ₁₂ improved but overall error increased")
        print(f"   Need to balance θ₁₂ breakthrough with θ₁₃/θ₂₃ preservation")
    
    # Get CKM results for completeness
    ckm_matrix = mixing_matrices.get('V_ckm')
    if ckm_matrix is not None:
        if isinstance(ckm_matrix, list):
            ckm_matrix = np.array(ckm_matrix)
        
        ckm_theta12, ckm_theta13, ckm_theta23 = extract_mixing_angles(ckm_matrix)
        
        # PDG CKM values
        ckm_theta12_pdg = 13.04
        ckm_theta13_pdg = 0.201
        ckm_theta23_pdg = 2.38
        
        ckm_theta12_error = abs(ckm_theta12 - ckm_theta12_pdg) / ckm_theta12_pdg * 100
        ckm_theta13_error = abs(ckm_theta13 - ckm_theta13_pdg) / ckm_theta13_pdg * 100
        ckm_theta23_error = abs(ckm_theta23 - ckm_theta23_pdg) / ckm_theta23_pdg * 100
        
        print(f"\n🔒 CKM VALIDATION:")
        print(f"   CKM θ₁₂ Error: {ckm_theta12_error:.2f}%")
        print(f"   CKM θ₁₃ Error: {ckm_theta13_error:.2f}%")
        print(f"   CKM θ₂₃ Error: {ckm_theta23_error:.2f}%")
        
        if ckm_theta12_error < 2.0 and ckm_theta13_error < 2.0 and ckm_theta23_error < 2.0:
            print(f"✅ CKM preservation: EXCELLENT")
        elif ckm_theta12_error < 5.0 and ckm_theta13_error < 5.0 and ckm_theta23_error < 5.0:
            print(f"✅ CKM preservation: GOOD")
        else:
            print(f"⚠️  CKM preservation: NEEDS ATTENTION")
    
    return {
        'theta12_error': theta12_error,
        'theta13_error': theta13_error,
        'theta23_error': theta23_error,
        'avg_error': avg_error,
        'improvement': improvement,
        'breakthrough_triples': breakthrough_triples
    }

if __name__ == "__main__":
    results = apply_theta12_breakthrough()
