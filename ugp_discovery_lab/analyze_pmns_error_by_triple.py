#!/usr/bin/env python3
"""
PMNS Error Analysis by Individual Neutrino Triple
=================================================

This script analyzes the 12.98% PMNS baseline to understand which neutrino triple
is contributing the most error. This will help us focus optimization efforts.
"""

import sys
import numpy as np
from pathlib import Path
import yaml

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ugp_discovery_lab.experiments.ugp_single_law_uuf_flow import UGPSingleLawUUFFlow

def analyze_pmns_error_by_triple():
    """Analyze PMNS error contribution by individual neutrino triple."""
    
    print("🔍 PMNS ERROR ANALYSIS BY NEUTRINO TRIPLE")
    print("=" * 60)
    
    # Load configuration
    config_path = project_root / "configs" / "experiments" / "ugp_single_law_uuf_flow.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Create experiment instance
    experiment = UGPSingleLawUUFFlow(config, project_root)
    
    # Run the baseline configuration to get the 12.98% result
    print("🔒 Running baseline configuration...")
    
    # Build all generators first
    generators = experiment._build_all_generators()
    
    # Apply UUF flow to all sectors
    uuf_results = experiment._apply_uuf_flow_to_all_sectors(generators)
    
    if not uuf_results:
        print("❌ Failed to get UUF flow results")
        return
    
    # Extract mixing matrices
    mixing_matrices = experiment._calculate_mixing_matrices(uuf_results)
    
    if not mixing_matrices:
        print("❌ Failed to calculate mixing matrices")
        return
    
    print(f"📊 Available mixing matrices: {list(mixing_matrices.keys())}")
    
    # Get the PMNS matrix
    pmns_matrix = mixing_matrices.get('U_pmns')
    if pmns_matrix is None:
        print("❌ No PMNS matrix found")
        print(f"📊 Available keys: {list(mixing_matrices.keys())}")
        return
    
    # Convert to numpy array if it's a list
    if isinstance(pmns_matrix, list):
        pmns_matrix = np.array(pmns_matrix)
    
    print(f"📊 PMNS Matrix Shape: {pmns_matrix.shape}")
    print(f"📊 PMNS Matrix:\n{pmns_matrix}")
    
    # Calculate PMNS mixing angles
    def extract_mixing_angles(U):
        """Extract mixing angles from unitary matrix."""
        # Standard parameterization
        s12 = np.abs(U[0, 1])
        s13 = np.abs(U[0, 2])
        s23 = np.abs(U[1, 2])
        
        theta12 = np.arcsin(s12) * 180 / np.pi
        theta13 = np.arcsin(s13) * 180 / np.pi
        theta23 = np.arcsin(s23) * 180 / np.pi
        
        return theta12, theta13, theta23
    
    # PDG experimental values (in degrees)
    pdg_theta12 = 33.45  # ±0.77
    pdg_theta13 = 8.62   # ±0.13
    pdg_theta23 = 42.1   # ±1.1
    
    # Calculate our predicted angles
    theta12_pred, theta13_pred, theta23_pred = extract_mixing_angles(pmns_matrix)
    
    print(f"\n📊 MIXING ANGLE COMPARISON:")
    print(f"   θ₁₂: Predicted = {theta12_pred:.2f}°, PDG = {pdg_theta12:.2f}°, Error = {abs(theta12_pred - pdg_theta12):.2f}°")
    print(f"   θ₁₃: Predicted = {theta13_pred:.2f}°, PDG = {pdg_theta13:.2f}°, Error = {abs(theta13_pred - pdg_theta13):.2f}°")
    print(f"   θ₂₃: Predicted = {theta23_pred:.2f}°, PDG = {pdg_theta23:.2f}°, Error = {abs(theta23_pred - pdg_theta23):.2f}°")
    
    # Calculate percentage errors
    error_12 = abs(theta12_pred - pdg_theta12) / pdg_theta12 * 100
    error_13 = abs(theta13_pred - pdg_theta13) / pdg_theta13 * 100
    error_23 = abs(theta23_pred - pdg_theta23) / pdg_theta23 * 100
    avg_error = (error_12 + error_13 + error_23) / 3
    
    print(f"\n📊 PERCENTAGE ERRORS:")
    print(f"   θ₁₂ Error: {error_12:.2f}%")
    print(f"   θ₁₃ Error: {error_13:.2f}%")
    print(f"   θ₂₃ Error: {error_23:.2f}%")
    print(f"   Average Error: {avg_error:.2f}%")
    
    # Identify the worst angle
    errors = [error_12, error_13, error_23]
    angles = ['θ₁₂', 'θ₁₃', 'θ₂₃']
    worst_idx = np.argmax(errors)
    worst_angle = angles[worst_idx]
    worst_error = errors[worst_idx]
    
    print(f"\n🎯 FOCUS ANALYSIS:")
    print(f"   Worst Angle: {worst_angle} ({worst_error:.2f}% error)")
    print(f"   This angle contributes {worst_error/avg_error*100:.1f}% of the total error")
    
    # Analyze neutrino mass matrix structure
    print(f"\n🔬 NEUTRINO MASS MATRIX ANALYSIS:")
    
    # Get the neutrino mass matrix from uuf_results
    neutrino_mass = uuf_results.get('neutrino', {}).get('M_evolved')
    if neutrino_mass is not None:
        print(f"   Mass Matrix Shape: {neutrino_mass.shape}")
        print(f"   Mass Matrix:\n{neutrino_mass}")
        
        # Check if it's symmetric
        is_symmetric = np.allclose(neutrino_mass, neutrino_mass.T)
        print(f"   Is Symmetric: {is_symmetric}")
        
        # Eigenvalues (mass eigenvalues)
        eigenvals = np.linalg.eigvals(neutrino_mass)
        print(f"   Eigenvalues: {eigenvals}")
        
        # Check hierarchy
        if len(eigenvals) >= 3:
            eigenvals_sorted = np.sort(np.abs(eigenvals))[::-1]
            hierarchy_ratio = eigenvals_sorted[0] / eigenvals_sorted[2] if eigenvals_sorted[2] != 0 else np.inf
            print(f"   Mass Hierarchy Ratio (m₁/m₃): {hierarchy_ratio:.2e}")
    else:
        print("   No neutrino mass matrix found in results")
    
    # Analyze neutrino triples used
    print(f"\n🧮 NEUTRINO TRIPLES ANALYSIS:")
    
    # Get the canonical triples used
    canonical_triples = experiment.canonical_triples
    
    # Extract neutrino triples from the canonical triples structure
    neutrino_triples = []
    for key in canonical_triples.keys():
        if isinstance(key, tuple) and len(key) == 3 and key[1] == "nu":
            neutrino_triples.append(canonical_triples[key])
    
    if neutrino_triples:
        print(f"   Neutrino Triples Used: {neutrino_triples}")
        
        # Analyze each triple
        for i, triple in enumerate(neutrino_triples):
            print(f"   Triple {i+1}: {triple}")
            print(f"     - Sum: {sum(triple)}")
            print(f"     - Product: {np.prod(triple)}")
            print(f"     - Range: {max(triple) - min(triple)}")
            print(f"     - Ratio (max/min): {max(triple) / min(triple):.2f}")
    else:
        print("   No neutrino triples found in canonical_triples")
    
    # Recommendations
    print(f"\n💡 OPTIMIZATION RECOMMENDATIONS:")
    print(f"   1. Focus on {worst_angle} - it's the biggest contributor to error")
    print(f"   2. Target {worst_angle} error reduction from {worst_error:.2f}% to <5%")
    print(f"   3. If {worst_angle} can be fixed, average error could drop to ~{(avg_error - worst_error + 5)/3:.2f}%")
    
    if worst_angle == 'θ₁₂':
        print(f"   4. θ₁₂ is controlled by the (1,2) element of PMNS matrix")
    elif worst_angle == 'θ₁₃':
        print(f"   4. θ₁₃ is controlled by the (1,3) element of PMNS matrix")
    elif worst_angle == 'θ₂₃':
        print(f"   4. θ₂₃ is controlled by the (2,3) element of PMNS matrix")
    
    return {
        'theta12_error': error_12,
        'theta13_error': error_13,
        'theta23_error': error_23,
        'worst_angle': worst_angle,
        'worst_error': worst_error,
        'pmns_matrix': pmns_matrix,
        'neutrino_triples': neutrino_triples
    }

if __name__ == "__main__":
    results = analyze_pmns_error_by_triple()
