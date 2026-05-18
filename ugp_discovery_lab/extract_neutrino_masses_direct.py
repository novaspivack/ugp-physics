#!/usr/bin/env python3
"""
Direct neutrino mass extraction - bypasses package imports

This script directly loads and executes the seesaw code without
importing the full ugp_discovery_lab package (which has sklearn issues)
"""

import sys
import json
import numpy as np
from pathlib import Path
from scipy.linalg import expm, eigh, sqrtm, schur

# Add path for direct module import
discovery_lab_path = Path(__file__).parent / "ugp_discovery_lab"
sys.path.insert(0, str(discovery_lab_path))

print("=" * 80)
print("DIRECT NEUTRINO MASS EXTRACTION")
print("=" * 80)
print()

# Load the seesaw module directly
print("Loading Path B Seesaw module...")
try:
    # Import directly from the file
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "ugp_seesaw_pmns_refined",
        discovery_lab_path / "experiments" / "ugp_seesaw_pmns_refined.py"
    )
    seesaw_module = importlib.util.module_from_spec(spec)
    
    # We need to provide the base Experiment class
    # Let's create a minimal mock
    class MockExperiment:
        def __init__(self, config, root):
            pass
    
    # Create a minimal registry function
    def mock_register(name):
        def decorator(cls):
            return cls
        return decorator
    
    # Inject mocks into the module's namespace before loading
    sys.modules['ugp_discovery_lab.experiments.base'] = type('module', (), {'Experiment': MockExperiment})()
    sys.modules['ugp_discovery_lab.core.registry'] = type('module', (), {'register_experiment': mock_register})()
    
    spec.loader.exec_module(seesaw_module)
    
    print("✅ Module loaded successfully!")
    print()
    
except Exception as e:
    print(f"❌ Error loading module: {e}")
    print()
    print("Trying alternative approach...")
    
    # Alternative: Read and parse an existing result file
    result_file = Path("improved_pathb_results_20250920_163453.json")
    if result_file.exists():
        print(f"Found existing result file: {result_file}")
        with open(result_file) as f:
            old_result = json.load(f)
        
        print()
        print("=" * 80)
        print("EXTRACTING FROM EXISTING RESULT FILE (Sept 2024)")
        print("=" * 80)
        print()
        
        # Check if it has M_eff
        if 'M_eff' in old_result:
            print("✅ Found M_eff in results!")
            M_eff_data = old_result['M_eff']
            
            # Parse M_eff (it's stored as strings with complex numbers)
            M_eff = np.zeros((3, 3), dtype=complex)
            for i in range(3):
                for j in range(3):
                    # Parse complex string like "(-4.29e-18-1.07e-17j)"
                    val_str = M_eff_data[i][j]
                    M_eff[i, j] = complex(val_str)
            
            print(f"M_eff shape: {M_eff.shape}")
            print()
            
            # Calculate eigenvalues
            print("Calculating eigenvalues...")
            eigenvals = np.linalg.eigvals(M_eff)
            print(f"Eigenvalues (GeV²): {eigenvals}")
            print()
            
            # Get masses
            masses_sq_GeV = np.abs(eigenvals)
            masses_GeV = np.sqrt(masses_sq_GeV)
            
            print("=" * 80)
            print("NEUTRINO MASSES")
            print("=" * 80)
            print()
            
            print("Masses² (GeV²):")
            for i, m_sq in enumerate(masses_sq_GeV, 1):
                print(f"  m_{i}² = {m_sq:.6e} GeV²")
            print()
            
            # Convert to eV
            GeV_to_eV = 1e9
            masses_sq_eV = masses_sq_GeV * GeV_to_eV**2
            masses_eV = masses_GeV * GeV_to_eV
            
            print("Masses² (eV²):")
            for i, m_sq in enumerate(masses_sq_eV, 1):
                print(f"  m_{i}² = {m_sq:.6e} eV²")
            print()
            
            print("Masses (eV):")
            for i, m in enumerate(masses_eV, 1):
                print(f"  m_{i} = {m:.6e} eV")
            print()
            
            # Calculate mass differences
            sorted_masses_sq = np.sort(masses_sq_eV)
            delta_m21_sq = sorted_masses_sq[1] - sorted_masses_sq[0]
            delta_m31_sq = sorted_masses_sq[2] - sorted_masses_sq[0]
            
            print("=" * 80)
            print("MASS DIFFERENCES")
            print("=" * 80)
            print()
            
            print(f"Δm²₂₁ = {delta_m21_sq:.6e} eV²")
            print(f"Δm²₃₁ = {delta_m31_sq:.6e} eV²")
            print()
            
            # Compare to experiments
            exp_delta_m21_sq = 7.5e-5
            exp_delta_m31_sq = 2.5e-3
            
            print("=" * 80)
            print("COMPARISON TO EXPERIMENTS")
            print("=" * 80)
            print()
            
            print("Experimental values:")
            print(f"  Δm²₂₁ (exp) = {exp_delta_m21_sq:.6e} eV²")
            print(f"  |Δm²₃₁| (exp) = {exp_delta_m31_sq:.6e} eV²")
            print()
            
            print("UGP values:")
            print(f"  Δm²₂₁ (UGP) = {delta_m21_sq:.6e} eV²")
            print(f"  Δm²₃₁ (UGP) = {delta_m31_sq:.6e} eV²")
            print()
            
            error_21 = abs(delta_m21_sq - exp_delta_m21_sq) / exp_delta_m21_sq
            error_31 = abs(abs(delta_m31_sq) - exp_delta_m31_sq) / exp_delta_m31_sq
            
            print(f"Errors:")
            print(f"  Δm²₂₁ error = {error_21*100:.2f}%")
            print(f"  |Δm²₃₁| error = {error_31*100:.2f}%")
            print()
            
            if error_21 < 0.15 and error_31 < 0.15:
                print("✅ EXCELLENT: Both < 15% error!")
            elif error_21 < 0.30 and error_31 < 0.30:
                print("✅ GOOD: Both < 30% error")
            else:
                print("⚠️  Needs refinement")
            print()
            
            # Hierarchy
            print("=" * 80)
            print("MASS HIERARCHY")
            print("=" * 80)
            print()
            
            # Sort with indices
            sorted_indices = np.argsort(masses_eV)
            print("Mass ordering (lightest to heaviest):")
            for i, idx in enumerate(sorted_indices):
                print(f"  Position {i+1}: m_{idx+1} = {masses_eV[idx]:.6e} eV")
            print()
            
            # Determine hierarchy
            if sorted_indices[0] == 0:  # m1 is lightest
                hierarchy = "NORMAL (m₁ < m₂ < m₃)"
            elif sorted_indices[0] == 2:  # m3 is lightest
                hierarchy = "INVERTED (m₃ < m₁ < m₂)"
            else:
                hierarchy = "UNUSUAL/UNKNOWN"
            
            print(f"Hierarchy: {hierarchy}")
            print(f"(Experimental hint: Normal hierarchy slightly favored)")
            print()
            
            # Sum of masses
            sum_masses = np.sum(masses_eV)
            print(f"Sum of masses: Σm_i = {sum_masses:.6e} eV")
            print(f"Cosmology limit: Σm_i < 0.12 eV")
            if sum_masses < 0.12:
                print("✅ Within cosmological bounds")
            else:
                print("⚠️  Exceeds cosmological bounds")
            print()
            
            print("=" * 80)
            print("✅ EXTRACTION COMPLETE FROM SEPT 2024 DATA")
            print("=" * 80)
            print()
            print("⚠️  NOTE: This is from September 2024 run")
            print("   Current code may give different values")
            print("   Consider running fresh when environment is fixed")
            
        else:
            print("❌ No M_eff found in result file")
    
    sys.exit(0)

# If we got here, module loaded successfully
print("Creating experiment instance...")

config = {
    'options': {
        'nu_R_triples': [(2, 5, 5), (7, 11, 13), (17, 19, 23)]
    }
}

output_dir = Path('./neutrino_extraction_output')
output_dir.mkdir(exist_ok=True)

try:
    exp = seesaw_module.UGPSeesawPMNSRefined(config, output_dir)
    print("✅ Experiment instance created!")
    print()
    
    print("Running Path B Seesaw...")
    result = exp.run_task("refined_seesaw_pmns_derivation")
    
    if result.get('status') == 'error':
        print(f"❌ Error: {result.get('error')}")
        sys.exit(1)
    
    print("✅ Path B Seesaw completed!")
    print()
    
    # Extract and display results
    pmns_result = result['sophisticated_pmns_derivation']
    
    # ... rest of extraction code ...
    
except Exception as e:
    print(f"❌ Error running experiment: {e}")
    import traceback
    traceback.print_exc()

