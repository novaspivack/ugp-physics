#!/usr/bin/env python3
"""
Test script to extract neutrino masses from Path B Seesaw

This script runs the refined Path B Seesaw and extracts:
1. Neutrino masses squared
2. Mass differences (Δm²₂₁, Δm²₃₁)
3. Comparison to experimental values
"""

import sys
import json
from pathlib import Path

# Add UGP discovery lab to path
sys.path.insert(0, str(Path(__file__).parent))

from ugp_discovery_lab.experiments.ugp_seesaw_pmns_refined import UGPSeesawPMNSRefined

def main():
    print("=" * 80)
    print("NEUTRINO MASS EXTRACTION TEST")
    print("=" * 80)
    print()
    
    # Configuration
    config = {
        'options': {
            # Use default right-handed neutrino triples
            'nu_R_triples': [(2, 5, 5), (7, 11, 13), (17, 19, 23)]
        }
    }
    
    # Output directory
    output_dir = Path('./neutrino_mass_test_output')
    output_dir.mkdir(exist_ok=True)
    
    print("Running Path B Seesaw with refined implementation...")
    print()
    
    # Create experiment instance
    exp = UGPSeesawPMNSRefined(config, output_dir)
    
    # Run the experiment
    result = exp.run_task("refined_seesaw_pmns_derivation")
    
    # Check for errors
    if result.get('status') == 'error':
        print("❌ ERROR:", result.get('error'))
        print("Traceback:", result.get('traceback'))
        return
    
    print("✅ Path B Seesaw completed successfully!")
    print()
    
    # Extract PMNS result
    pmns_result = result['sophisticated_pmns_derivation']
    
    # Extract neutrino masses
    print("=" * 80)
    print("NEUTRINO MASS RESULTS")
    print("=" * 80)
    print()
    
    if 'neutrino_masses_squared' in pmns_result:
        masses_sq_GeV = pmns_result['neutrino_masses_squared']
        print(f"✅ Neutrino masses² found in results!")
        print()
        print(f"Neutrino masses² (GeV²):")
        for i, m_sq in enumerate(masses_sq_GeV, 1):
            print(f"  m_{i}² = {m_sq:.6e} GeV²")
        
        print()
        
        # Convert to eV²
        GeV_to_eV = 1e9
        masses_sq_eV = [m * GeV_to_eV**2 for m in masses_sq_GeV]
        print(f"Neutrino masses² (eV²):")
        for i, m_sq in enumerate(masses_sq_eV, 1):
            print(f"  m_{i}² = {m_sq:.6e} eV²")
        
        print()
        
        # Calculate masses
        import numpy as np
        masses_eV = [np.sqrt(abs(m)) for m in masses_sq_eV]
        print(f"Neutrino masses (eV):")
        for i, m in enumerate(masses_eV, 1):
            print(f"  m_{i} = {m:.6e} eV")
        
        print()
        
    else:
        print("⚠️  WARNING: 'neutrino_masses_squared' not found in pmns_result")
        print(f"Available keys: {list(pmns_result.keys())}")
        print()
    
    # Extract mass differences
    print("=" * 80)
    print("MASS DIFFERENCES")
    print("=" * 80)
    print()
    
    if 'mass_squared_differences' in pmns_result:
        mass_diffs = pmns_result['mass_squared_differences']
        print(f"✅ Mass differences found in results!")
        print()
        
        delta_m21_sq = mass_diffs['delta_m21_squared']
        delta_m31_sq = mass_diffs['delta_m31_squared']
        
        print(f"Δm²₂₁ (GeV²)  = {delta_m21_sq:.6e}")
        print(f"Δm²₃₁ (GeV²)  = {delta_m31_sq:.6e}")
        print()
        
        # Convert to eV²
        delta_m21_sq_eV = delta_m21_sq * GeV_to_eV**2
        delta_m31_sq_eV = delta_m31_sq * GeV_to_eV**2
        
        print(f"Δm²₂₁ (eV²)   = {delta_m21_sq_eV:.6e}")
        print(f"Δm²₃₁ (eV²)   = {delta_m31_sq_eV:.6e}")
        print()
        
    else:
        print("⚠️  WARNING: 'mass_squared_differences' not found in pmns_result")
        print(f"Available keys: {list(pmns_result.keys())}")
        print()
    
    # Compare to experimental values
    print("=" * 80)
    print("COMPARISON TO EXPERIMENTS")
    print("=" * 80)
    print()
    
    exp_delta_m21_sq = 7.5e-5  # eV²
    exp_delta_m31_sq = 2.5e-3  # eV²
    exp_sum_masses = 0.12      # eV (cosmology upper bound)
    
    print(f"Experimental values:")
    print(f"  Δm²₂₁ (exp)     = {exp_delta_m21_sq:.6e} eV² (Super-Kamiokande)")
    print(f"  |Δm²₃₁| (exp)   = {exp_delta_m31_sq:.6e} eV² (experiments)")
    print(f"  Σm_i (limit)    < {exp_sum_masses:.2f} eV (cosmology)")
    print()
    
    if 'mass_squared_differences' in pmns_result:
        print(f"UGP predictions:")
        print(f"  Δm²₂₁ (UGP)     = {delta_m21_sq_eV:.6e} eV²")
        print(f"  Δm²₃₁ (UGP)     = {delta_m31_sq_eV:.6e} eV²")
        
        if 'neutrino_masses_squared' in pmns_result:
            sum_masses = np.sum(masses_eV)
            print(f"  Σm_i (UGP)      = {sum_masses:.6e} eV")
        
        print()
        
        # Calculate errors
        error_21 = abs(delta_m21_sq_eV - exp_delta_m21_sq) / exp_delta_m21_sq
        error_31 = abs(abs(delta_m31_sq_eV) - exp_delta_m31_sq) / exp_delta_m31_sq
        
        print(f"Errors:")
        print(f"  Δm²₂₁ error     = {error_21*100:.2f}%")
        print(f"  |Δm²₃₁| error   = {error_31*100:.2f}%")
        print()
        
        if error_21 < 0.15 and error_31 < 0.15:
            print("✅ EXCELLENT: Both mass differences within 15% of experimental values!")
        elif error_21 < 0.30 and error_31 < 0.30:
            print("✅ GOOD: Both mass differences within 30% of experimental values")
        else:
            print("⚠️  Mass differences need refinement")
        print()
    
    # Determine hierarchy
    print("=" * 80)
    print("MASS HIERARCHY")
    print("=" * 80)
    print()
    
    if 'neutrino_masses_squared' in pmns_result:
        sorted_masses = sorted(enumerate(masses_eV, 1), key=lambda x: x[1])
        print(f"Mass ordering (lightest to heaviest):")
        for i, (idx, m) in enumerate(sorted_masses):
            print(f"  Position {i+1}: m_{idx} = {m:.6e} eV")
        
        print()
        
        # Determine hierarchy type
        if sorted_masses[0][0] == 1:  # m1 is lightest
            if sorted_masses[1][0] == 2:  # m1 < m2 < m3
                hierarchy = "NORMAL"
            else:
                hierarchy = "UNKNOWN"
        elif sorted_masses[0][0] == 3:  # m3 is lightest
            if sorted_masses[1][0] == 1:  # m3 < m1 < m2
                hierarchy = "INVERTED"
            else:
                hierarchy = "UNKNOWN"
        else:
            hierarchy = "UNKNOWN"
        
        print(f"Mass hierarchy: {hierarchy}")
        print(f"  (Experimental hint: Normal hierarchy slightly favored)")
        print()
    
    # Save results to JSON
    output_file = output_dir / "neutrino_mass_results.json"
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    print("=" * 80)
    print(f"✅ Full results saved to: {output_file}")
    print("=" * 80)
    print()
    
    # Also save PMNS angles for reference
    print("PMNS ANGLES (for reference):")
    pmns_angles = pmns_result.get('pmns_angles', {})
    print(f"  θ₁₂ = {pmns_angles.get('theta12', 'N/A')}°")
    print(f"  θ₁₃ = {pmns_angles.get('theta13', 'N/A')}°")
    print(f"  θ₂₃ = {pmns_angles.get('theta23', 'N/A')}°")
    print()
    
    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()

