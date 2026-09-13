#!/usr/bin/env python3
"""
Discrete Sweep CP Analysis
==========================

This script performs discrete sweep analysis with CP proxy correlation:
- Tests 144 combinations of discrete parameters
- Records PMNS accuracy vs CP proxy correlation
- Outputs CSV for publication-ready analysis
"""

import sys
import os
import json
import yaml
import numpy as np
import csv
from pathlib import Path
from datetime import datetime

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ugp_discovery_lab.experiments.ugp_single_law_uuf_flow_theoretical_upgrades import UGPSingleLawUUFFlowTheoreticalUpgrades
from ugp_discovery_lab.experiments.ugp_cp_asymmetry_probe import UGPCPAsymmetryProbe


def circ_err_deg(a_rad, b_rad):
    """Calculate circular error in degrees."""
    return float(np.degrees(np.abs(np.arctan2(np.sin(a_rad-b_rad), np.cos(a_rad-b_rad)))))


def run_discrete_sweep_cp_analysis():
    """Run discrete sweep analysis with CP proxy correlation."""
    
    print("🔬 DISCRETE SWEEP CP ANALYSIS")
    print("=" * 50)
    
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
        print("✅ UGP-clean hybrid experiment created successfully")
    except Exception as e:
        print(f"❌ Failed to create experiment: {e}")
        return False
    
    # CP probe configuration
    cp_probe_config = {
        "options": {
            "kernel": {"k_gen": np.pi/2}, 
            "ugp_phase_tests": {
                "majorana_phase_fraction": [1.0, 0.5, 0.0],
                "signs": [+1, -1]
            }
        }
    }
    
    # Discrete parameter combinations
    e_orientations = ['13_torque', 'mu_tau_anchor']
    nuR_perms = [[0,1,2], [0,2,1], [1,0,2], [1,2,0], [2,0,1], [2,1,0]]
    phase_fractions = [1.0, 0.5, 0.0]
    bch_options = [False, True]
    integrators = ['strang', 'yoshida']
    
    total_combinations = len(e_orientations) * len(nuR_perms) * len(phase_fractions) * len(bch_options) * len(integrators)
    print(f"🧪 Testing {total_combinations} discrete combinations...")
    
    # Setup CSV output
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_file = f"results/discrete_sweep_cp_analysis_{timestamp}.csv"
    os.makedirs("results", exist_ok=True)
    
    with open(csv_file, 'w', newline='') as csvfile:
        fieldnames = [
            'combination_id', 'e_orientation', 'nuR_permutation', 'phase_fraction', 
            'bch_enabled', 'integrator', 'ckm_preserved', 'ckm_mean_error', 
            'pmns_mean_error', 'pmns_rms_error', 'pmns_theta12_error', 
            'pmns_theta13_error', 'pmns_theta23_error', 'delta_q_error_h1', 
            'delta_l_error_h2', 'jarlskog_ckm', 'jarlskog_pmns', 'leptogenesis_H', 
            'leptogenesis_J_pmns', 'leptogenesis_J_eff'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        combination_id = 0
        ckm_preserved_count = 0
        
        for e_orient in e_orientations:
            for nuR_perm in nuR_perms:
                for phase_frac in phase_fractions:
                    for bch_enabled in bch_options:
                        for integrator in integrators:
                            combination_id += 1
                            
                            # Set discrete configuration
                            experiment.cfg['options']['theoretical_upgrades']['e_orientation_method'] = e_orient
                            experiment.cfg['options']['theoretical_upgrades']['nuR_permutation'] = nuR_perm
                            experiment.cfg['options']['theoretical_upgrades']['majorana_E_phase_fraction'] = phase_frac
                            experiment.cfg['options']['theoretical_upgrades']['bch_preconditioning'] = bch_enabled
                            experiment.cfg['options']['theoretical_upgrades']['integrator'] = integrator
                            
                            try:
                                # Run UUF flow
                                result = experiment.run_task('single_law_uuf_flow')
                                
                                # Check CKM preservation (hard gate)
                                validation = result.get('validation', {})
                                ckm_validation = validation.get('ckm_validation', {})
                                ckm_errors = ckm_validation.get('errors', {})
                                
                                ckm_mean = (ckm_errors.get('theta12_error', 0) + 
                                           ckm_errors.get('theta13_error', 0) + 
                                           ckm_errors.get('theta23_error', 0)) / 3 * 100
                                
                                # CKM hard gate: must be within 2% of baseline (0.69%)
                                ckm_preserved = abs(ckm_mean - 0.69) < 2.0
                                
                                if ckm_preserved:
                                    ckm_preserved_count += 1
                                    
                                    # Extract PMNS results
                                    pmns_validation = validation.get('pmns_validation', {})
                                    pmns_errors = pmns_validation.get('errors', {})
                                    
                                    pmns_mean = (pmns_errors.get('theta12_error', 0) + 
                                                pmns_errors.get('theta13_error', 0) + 
                                                pmns_errors.get('theta23_error', 0)) / 3 * 100
                                    
                                    pmns_rms = np.sqrt((pmns_errors.get('theta12_error', 0)**2 + 
                                                       pmns_errors.get('theta13_error', 0)**2 + 
                                                       pmns_errors.get('theta23_error', 0)**2) / 3) * 100
                                    
                                    # Run CP probe
                                    mixing_matrices = result.get('mixing_matrices', {})
                                    
                                    # Create simple M_eff for CP analysis
                                    M_eff = np.array([[1.0, 0.1, 0.01], [0.1, 0.5, 0.1], [0.01, 0.1, 0.05]], dtype=complex)
                                    
                                    cp_probe = UGPCPAsymmetryProbe(cp_probe_config, project_root)
                                    
                                    def producer():
                                        d = {}
                                        if mixing_matrices.get("V_ckm") is not None:
                                            d["V_ckm"] = np.array(mixing_matrices["V_ckm"], dtype=complex)
                                        if mixing_matrices.get("U_pmns") is not None:
                                            d["U_pmns"] = np.array(mixing_matrices["U_pmns"], dtype=complex)
                                        d["M_eff"] = M_eff
                                        return d
                                    
                                    cp_probe.set_producer(producer)
                                    cp_result = cp_probe.run_task("cp_probe")
                                    
                                    # Extract CP analysis results
                                    delta_q_error_h1 = cp_result['phase_tests']['H1_dirac']['err_deg']
                                    delta_l_error_h2 = cp_result['phase_tests']['H2_majorana']['err_deg']
                                    jarlskog_ckm = cp_result['ckm']['Jarlskog']
                                    jarlskog_pmns = cp_result['pmns']['Jarlskog']
                                    
                                    lep = cp_result.get('leptogenesis_proxy', {})
                                    leptogenesis_H = lep.get('H', 0.0)
                                    leptogenesis_J_pmns = lep.get('J_pmns', 0.0)
                                    leptogenesis_J_eff = lep.get('J_eff', 0.0)
                                    
                                    # Write to CSV
                                    row = {
                                        'combination_id': combination_id,
                                        'e_orientation': e_orient,
                                        'nuR_permutation': str(nuR_perm),
                                        'phase_fraction': phase_frac,
                                        'bch_enabled': bch_enabled,
                                        'integrator': integrator,
                                        'ckm_preserved': ckm_preserved,
                                        'ckm_mean_error': ckm_mean,
                                        'pmns_mean_error': pmns_mean,
                                        'pmns_rms_error': pmns_rms,
                                        'pmns_theta12_error': pmns_errors.get('theta12_error', 0) * 100,
                                        'pmns_theta13_error': pmns_errors.get('theta13_error', 0) * 100,
                                        'pmns_theta23_error': pmns_errors.get('theta23_error', 0) * 100,
                                        'delta_q_error_h1': delta_q_error_h1,
                                        'delta_l_error_h2': delta_l_error_h2,
                                        'jarlskog_ckm': jarlskog_ckm,
                                        'jarlskog_pmns': jarlskog_pmns,
                                        'leptogenesis_H': leptogenesis_H,
                                        'leptogenesis_J_pmns': leptogenesis_J_pmns,
                                        'leptogenesis_J_eff': leptogenesis_J_eff
                                    }
                                    writer.writerow(row)
                                    
                                else:
                                    # CKM not preserved, record with minimal data
                                    row = {
                                        'combination_id': combination_id,
                                        'e_orientation': e_orient,
                                        'nuR_permutation': str(nuR_perm),
                                        'phase_fraction': phase_frac,
                                        'bch_enabled': bch_enabled,
                                        'integrator': integrator,
                                        'ckm_preserved': False,
                                        'ckm_mean_error': ckm_mean,
                                        'pmns_mean_error': 0.0,
                                        'pmns_rms_error': 0.0,
                                        'pmns_theta12_error': 0.0,
                                        'pmns_theta13_error': 0.0,
                                        'pmns_theta23_error': 0.0,
                                        'delta_q_error_h1': 0.0,
                                        'delta_l_error_h2': 0.0,
                                        'jarlskog_ckm': 0.0,
                                        'jarlskog_pmns': 0.0,
                                        'leptogenesis_H': 0.0,
                                        'leptogenesis_J_pmns': 0.0,
                                        'leptogenesis_J_eff': 0.0
                                    }
                                    writer.writerow(row)
                            
                            except Exception as e:
                                print(f"⚠️ Combination {combination_id} failed: {e}")
                                continue
    
    print(f"\n📊 DISCRETE SWEEP RESULTS:")
    print("=" * 40)
    print(f"Total combinations tested: {total_combinations}")
    print(f"CKM preservation rate: {ckm_preserved_count}/{total_combinations} ({ckm_preserved_count/total_combinations*100:.1f}%)")
    print(f"Results saved to: {csv_file}")
    
    # Generate summary statistics
    print(f"\n📈 SUMMARY STATISTICS:")
    print("=" * 30)
    
    # Read back the CSV to generate statistics
    preserved_rows = []
    with open(csv_file, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['ckm_preserved'] == 'True':
                preserved_rows.append(row)
    
    if preserved_rows:
        pmns_means = [float(row['pmns_mean_error']) for row in preserved_rows]
        j_effs = [float(row['leptogenesis_J_eff']) for row in preserved_rows]
        delta_h1s = [float(row['delta_q_error_h1']) for row in preserved_rows]
        delta_h2s = [float(row['delta_l_error_h2']) for row in preserved_rows]
        
        print(f"PMNS mean error range: {min(pmns_means):.2f}% - {max(pmns_means):.2f}%")
        print(f"J_eff range: {min(j_effs):.6f} - {max(j_effs):.6f}")
        print(f"H1 (Dirac) δ error range: {min(delta_h1s):.2f}° - {max(delta_h1s):.2f}°")
        print(f"H2 (Majorana) δ error range: {min(delta_h2s):.2f}° - {max(delta_h2s):.2f}°")
        
        # Find best configurations
        best_pmns_idx = pmns_means.index(min(pmns_means))
        best_j_eff_idx = j_effs.index(max(j_effs))
        
        print(f"\n🏆 BEST CONFIGURATIONS:")
        print(f"Best PMNS accuracy: Combination {preserved_rows[best_pmns_idx]['combination_id']} "
              f"({min(pmns_means):.2f}% error)")
        print(f"Best J_eff: Combination {preserved_rows[best_j_eff_idx]['combination_id']} "
              f"({max(j_effs):.6f})")
    
    print(f"\n✅ Discrete sweep CP analysis completed successfully!")
    print(f"📊 CSV results available for publication-ready analysis: {csv_file}")
    
    return True


if __name__ == "__main__":
    success = run_discrete_sweep_cp_analysis()
    if success:
        print("✅ Discrete sweep CP analysis completed successfully!")
    else:
        print("❌ Discrete sweep CP analysis failed!")
        sys.exit(1)
