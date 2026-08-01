"""
Test script to validate Research Program 1.4a predictions with existing flow optimization module.

This script tests the predicted lepton sector flow parameters:
- ε_lepton = 0.639983
- ε'_lepton = 0.005205

Against the existing flow optimization framework to validate PMNS derivation.
"""

import sys
import json
from pathlib import Path

_LAB_ROOT = Path(__file__).resolve().parent
if str(_LAB_ROOT) not in sys.path:
    sys.path.insert(0, str(_LAB_ROOT))

from ugp_discovery_lab.experiments.ugp_yukawa_ckm_pmns_flow_optimization import UGPYukawaCKMPMNSFlowOptimization


def test_predicted_lepton_parameters():
    """Test the predicted lepton parameters from Research Program 1.4a."""
    
    print("=== Research Program 1.4a Validation Test ===")
    print()
    
    # Load the predicted parameters from Research Program 1.4a
    with open('research_program_1_4a_results.json', 'r') as f:
        rp1_4a_results = json.load(f)
    
    predicted_params = rp1_4a_results['predicted_lepton_parameters']
    
    print("Predicted Lepton Parameters from Research Program 1.4a:")
    print(f"  τ₀_scaling = {predicted_params['tau0_scaling']}")
    print(f"  ε_scaling = {predicted_params['epsilon_scaling']:.6f}")
    print(f"  ε'_scaling = {predicted_params['epsilon_prime_scaling']:.6f}")
    print(f"  normalization_method = {predicted_params['normalization_method']}")
    print(f"  down_sector_permutation = {predicted_params['down_sector_permutation']}")
    print()
    
    # Load the flow optimization configuration
    config_path = Path('configs/experiments/ugp_yukawa_ckm_pmns_flow_optimization.yaml')
    
    if not config_path.exists():
        print(f"Error: Configuration file not found at {config_path}")
        return None
    
    # Load the configuration
    import yaml
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Create the experiment instance
    output_dir = Path('.')
    experiment = UGPYukawaCKMPMNSFlowOptimization(config, output_dir)
    
    print("Testing predicted parameters with flow optimization module...")
    print()
    
    # Test the baseline configuration with predicted parameters
    try:
        result = experiment.test_baseline_configuration(
            tau0_scale=predicted_params['tau0_scaling'],
            epsilon_scale=predicted_params['epsilon_scaling'],
            epsilon_prime_scale=predicted_params['epsilon_prime_scaling'],
            norm_method=predicted_params['normalization_method']
        )
        
        print("Validation Results:")
        print("-" * 50)
        
        # Handle the actual result format from the flow optimization module
        print("Available result keys:", list(result.keys()))
        
        # Extract angles from the result format
        if 'experimental_errors' in result:
            errors = result['experimental_errors']
            
            # Extract CKM and PMNS angles from the errors structure
            ckm_angles = []
            pmns_angles = []
            
            # Look for angle values in the experimental_errors
            for key, value in errors.items():
                if 'ckm_theta_12' in key.lower():
                    ckm_angles.append(value if isinstance(value, (int, float)) else 0)
                elif 'ckm_theta_13' in key.lower():
                    ckm_angles.append(value if isinstance(value, (int, float)) else 0)
                elif 'ckm_theta_23' in key.lower():
                    ckm_angles.append(value if isinstance(value, (int, float)) else 0)
                elif 'pmns_theta_12' in key.lower():
                    pmns_angles.append(value if isinstance(value, (int, float)) else 0)
                elif 'pmns_theta_13' in key.lower():
                    pmns_angles.append(value if isinstance(value, (int, float)) else 0)
                elif 'pmns_theta_23' in key.lower():
                    pmns_angles.append(value if isinstance(value, (int, float)) else 0)
            
            if len(ckm_angles) == 3 and len(pmns_angles) == 3:
                print("CKM Angles (should preserve locked configuration):")
                print(f"  θ₁₂ = {ckm_angles[0]:.3f}° (target: 33.44°)")
                print(f"  θ₁₃ = {ckm_angles[1]:.3f}° (target: 8.57°)")
                print(f"  θ₂₃ = {ckm_angles[2]:.3f}° (target: 49.2°)")
                print()
                
                print("PMNS Angles (Research Program 1.4a prediction):")
                print(f"  θ₁₂ = {pmns_angles[0]:.3f}° (target: 33.44°)")
                print(f"  θ₁₃ = {pmns_angles[1]:.3f}° (target: 8.57°)")
                print(f"  θ₂₃ = {pmns_angles[2]:.3f}° (target: 49.2°)")
                print()
                
                # Calculate errors
                ckm_errors = [
                    abs(ckm_angles[0] - 33.44) / 33.44 * 100,
                    abs(ckm_angles[1] - 8.57) / 8.57 * 100,
                    abs(ckm_angles[2] - 49.2) / 49.2 * 100
                ]
                
                pmns_errors = [
                    abs(pmns_angles[0] - 33.44) / 33.44 * 100,
                    abs(pmns_angles[1] - 8.57) / 8.57 * 100,
                    abs(pmns_angles[2] - 49.2) / 49.2 * 100
                ]
                
                print("Error Analysis:")
                print(f"  CKM Average Error: {sum(ckm_errors)/3:.2f}%")
                print(f"  PMNS Average Error: {sum(pmns_errors)/3:.2f}%")
                print()
                
                # Check if PMNS errors are < 5% (success criterion)
                pmns_success = all(error < 5.0 for error in pmns_errors)
                ckm_preserved = sum(ckm_errors)/3 < 2.0  # Should preserve CKM accuracy
                
                print("Success Criteria:")
                print(f"  PMNS < 5% error: {'✅ PASS' if pmns_success else '❌ FAIL'}")
                print(f"  CKM preserved: {'✅ PASS' if ckm_preserved else '❌ FAIL'}")
                print()
                
                if pmns_success and ckm_preserved:
                    print("🎉 Research Program 1.4a SUCCESS!")
                    print("Sector-decoupled flow dynamics successfully derived PMNS with high precision")
                    print("while preserving the locked CKM configuration!")
                else:
                    print("⚠️  Research Program 1.4a needs refinement")
                    if not pmns_success:
                        print("PMNS angles need improvement (< 5% error required)")
                    if not ckm_preserved:
                        print("CKM configuration was not preserved")
                
                return {
                    'success': pmns_success and ckm_preserved,
                    'ckm_angles': ckm_angles,
                    'pmns_angles': pmns_angles,
                    'ckm_errors': ckm_errors,
                    'pmns_errors': pmns_errors,
                    'pmns_success': pmns_success,
                    'ckm_preserved': ckm_preserved,
                    'raw_result': result
                }
            else:
                print(f"Could not extract angles from result. Found {len(ckm_angles)} CKM angles, {len(pmns_angles)} PMNS angles")
                print("Full result structure:")
                print(json.dumps(result, indent=2))
                return None
            
        else:
            print("Error: Result format unexpected")
            print("Available keys:", list(result.keys()))
            return None
            
    except Exception as e:
        print(f"Error during validation: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Run the validation test."""
    
    # Run from the lab package root (configs, JSON inputs)
    import os
    os.chdir(_LAB_ROOT)
    
    # Run the validation test
    results = test_predicted_lepton_parameters()
    
    if results:
        print("\n" + "=" * 80)
        print("Research Program 1.4a Validation Complete")
        print("=" * 80)
        
        # Save validation results
        with open('research_program_1_4a_validation_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"Validation results saved to: research_program_1_4a_validation_results.json")
    else:
        print("\nValidation failed - see error messages above")


if __name__ == "__main__":
    main()
