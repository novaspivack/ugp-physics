#!/usr/bin/env python3
"""
Debug Beta Function - Find out why it produces β₁=8.722 instead of 6.833
"""

import sys
sys.path.insert(0, 'ugp_discovery_lab')

import numpy as np
import pandas as pd
from ugp_discovery_lab.experiments.ugp_renormalization_finalizer_enhanced import UGPRenormalizationFinalizerEnhanced
from pathlib import Path

def debug_beta_function():
    """Debug the beta function calculation step by step."""
    
    print("🔍 DEBUGGING BETA FUNCTION CALCULATION")
    print("=" * 60)
    
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
    finalizer = UGPRenormalizationFinalizerEnhanced(config, Path('debug_beta_output'))
    
    # Load and process particle catalog
    print(f"\n🔬 LOADING PARTICLE CATALOG...")
    particle_catalog = pd.read_csv('inputs/candidates.csv')
    particle_catalog['mass'] = particle_catalog['mass_mev_calibrated'] / 1000.0  # Convert MeV to GeV
    particle_catalog['g'] = particle_catalog['generation']  # Map generation to g
    
    print(f"Loaded {len(particle_catalog)} particles")
    
    # Process particle catalog (apply filtering)
    print(f"\n⚙️ PROCESSING PARTICLE CATALOG...")
    # Apply the same filtering as in the finalizer
    from ugp_discovery_lab.experiments.ugp_renormalization_finalizer_enhanced import filter_particles_by_quality
    
    # Apply quality-based filtering directly
    processed_catalog = filter_particles_by_quality(
        particle_catalog,
        viability_threshold=0.7,
        stability_threshold=0.7
    )
    
    print(f"Processed {len(processed_catalog)} particles")
    
    # Test at a specific scale
    test_scale = 1e19  # Unification scale
    print(f"\n🧮 TESTING BETA FUNCTION AT SCALE {test_scale:.2e} GeV")
    
    # Get active particles
    active_particles = processed_catalog[processed_catalog['mass'] < test_scale]
    print(f"Active particles: {len(active_particles)}")
    
    # Check hypercharge assignment
    print(f"\n🔍 HYPERCHARGE ANALYSIS:")
    
    # Calculate hypercharges manually
    from ugp_discovery_lab.experiments.ugp_renormalization_finalizer_enhanced import assign_hypercharge
    
    hypercharges = []
    for _, particle in active_particles.iterrows():
        particle_dict = particle.to_dict()
        hypercharge = assign_hypercharge(particle_dict, config['hypercharge_model'])
        hypercharges.append(hypercharge)
    
    hypercharges = np.array(hypercharges)
    
    print(f"Hypercharge statistics:")
    print(f"  Min: {np.min(hypercharges):.6f}")
    print(f"  Max: {np.max(hypercharges):.6f}")
    print(f"  Mean: {np.mean(hypercharges):.6f}")
    print(f"  Std: {np.std(hypercharges):.6f}")
    
    # Calculate Y² contribution
    y_squared = hypercharges * hypercharges
    total_y_squared = np.sum(y_squared)
    
    print(f"\n📊 Y² CONTRIBUTION ANALYSIS:")
    print(f"  Total Y²: {total_y_squared:.6f}")
    print(f"  Average Y² per particle: {total_y_squared/len(hypercharges):.6f}")
    
    # Calculate beta function components
    sm_contribution = 41.0 / 6.0
    gte_contribution = (1.0 / 6.0) * total_y_squared
    total_beta = sm_contribution + gte_contribution
    
    print(f"\n🧮 BETA FUNCTION COMPONENTS:")
    print(f"  SM contribution (41/6): {sm_contribution:.6f}")
    print(f"  GTE contribution (Y²/6): {gte_contribution:.6f}")
    print(f"  Total β₁: {total_beta:.6f}")
    
    # Check if this matches what we're seeing
    print(f"\n🎯 COMPARISON:")
    print(f"  Expected β₁: 6.833 (SM only)")
    print(f"  Calculated β₁: {total_beta:.6f}")
    print(f"  Difference: {total_beta - 6.833:.6f}")
    print(f"  Relative error: {(total_beta - 6.833) / 6.833 * 100:.1f}%")
    
    # Show some example particles
    print(f"\n📋 SAMPLE PARTICLES:")
    sample_particles = active_particles.head(10)
    for i, (_, particle) in enumerate(sample_particles.iterrows()):
        hypercharge = hypercharges[i]
        print(f"  Particle {i+1}: mass={particle['mass']:.3f} GeV, generation={particle.get('g', 'N/A')}, hypercharge={hypercharge:.6f}")
    
    # Check if the issue is in the hypercharge assignment
    print(f"\n🔍 HYPERCHARGE ASSIGNMENT ANALYSIS:")
    print(f"  Hypercharge model: {config['hypercharge_model']}")
    
    # Check generation distribution
    if 'generation' in active_particles.columns:
        gen_counts = active_particles['generation'].value_counts().sort_index()
        print(f"  Generation distribution:")
        for gen, count in gen_counts.items():
            print(f"    Gen {gen}: {count} particles")
    
    # Check canonical matches
    if 'canonical_match' in active_particles.columns:
        canonical_count = active_particles['canonical_match'].notna().sum()
        print(f"  Canonical SM particles: {canonical_count}")
    
    print(f"\n✅ DEBUGGING COMPLETE")

if __name__ == "__main__":
    debug_beta_function()
