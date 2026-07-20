#!/usr/bin/env python3
"""
Diagnostic script to investigate hypercharge calculation and GTE contributions
in the particle-dependent beta function approach.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add the UGP discovery lab to the Python path
sys.path.insert(0, str(Path(__file__).parent / "ugp_discovery_lab"))

from ugp_discovery_lab.experiments.ugp_renormalization_finalizer_enhanced import (
    assign_hypercharge, 
    get_b1_1loop_scale_dependent,
    initialize_optimizations,
    ThresholdType
)

def diagnose_hypercharge_calculation():
    """Diagnose the hypercharge calculation and GTE contributions."""
    print("🔍 DIAGNOSTIC: Hypercharge Calculation and GTE Contributions")
    print("=" * 70)
    
    # Load the small test dataset
    catalog_path = './inputs/residual_deconstruction_experiment/particle_catalog.parquet'
    df = pd.read_parquet(catalog_path)
    small_df = df.sample(n=1000, random_state=42)
    
    print(f"📊 Loaded {len(small_df):,} particles from test dataset")
    print(f"   Mass range: {small_df['mass_mev_calibrated'].min()/1000:.3f} - {small_df['mass_mev_calibrated'].max()/1000:.3f} GeV")
    print(f"   Generation range: {small_df['generation'].min()} - {small_df['generation'].max()}")
    
    # Hypercharge model
    hypercharge_model = {
        'g_factor': 1.0/3.0,
        'c_state_latched_15_offset': 1.0/6.0
    }
    
    # Process the data like the finalizer does
    small_df['mass'] = small_df['mass_mev_calibrated'] / 1000.0  # Convert MeV to GeV
    small_df['g'] = small_df['generation']  # Map generation to g
    small_df['c_state'] = small_df['c_state'].fillna('ridge_default')
    
    print("\n🎯 HYPERCHARGE CALCULATION ANALYSIS:")
    print("-" * 50)
    
    # Sample a few particles and show their hypercharge calculation
    sample_particles = small_df.head(10)
    
    for idx, particle in sample_particles.iterrows():
        particle_dict = particle.to_dict()
        hypercharge = assign_hypercharge(particle_dict, hypercharge_model)
        
        print(f"Particle {idx}:")
        print(f"  Mass: {particle['mass']:.3f} GeV")
        print(f"  Generation (g): {particle['g']}")
        print(f"  C-state: {particle['c_state']}")
        print(f"  Hypercharge: {hypercharge:.6f}")
        print(f"  Y² contribution: {hypercharge**2:.6f}")
        print()
    
    print("\n🎯 BETA FUNCTION COEFFICIENT ANALYSIS:")
    print("-" * 50)
    
    # Test different energy scales
    test_scales = [1e19, 1e15, 1e12, 1e9, 1e6, 1e3, 91.1876]  # GeV
    
    for mu in test_scales:
        print(f"\n📊 Testing at scale μ = {mu:.2e} GeV:")
        
        # Constant approach
        b1_constant = get_b1_1loop_scale_dependent(
            mu, small_df, hypercharge_model, 
            use_particle_dependent=False
        )
        
        # Particle-dependent approach
        b1_particle = get_b1_1loop_scale_dependent(
            mu, small_df, hypercharge_model,
            use_particle_dependent=True
        )
        
        print(f"  Constant β₁: {b1_constant:.6f}")
        print(f"  Particle-dependent β₁: {b1_particle:.6f}")
        print(f"  Difference: {b1_particle - b1_constant:.6f}")
        print(f"  Relative difference: {((b1_particle - b1_constant) / b1_constant * 100):.2f}%")
    
    print("\n🎯 GTE CONTRIBUTION BREAKDOWN:")
    print("-" * 50)
    
    # Calculate total Y² contribution at a reference scale
    mu_ref = 1e15  # GeV
    active_particles = small_df[small_df['mass'] < mu_ref]
    
    total_y_squared = 0.0
    hypercharge_summary = {}
    
    for idx, particle in active_particles.iterrows():
        particle_dict = particle.to_dict()
        hypercharge = assign_hypercharge(particle_dict, hypercharge_model)
        y_squared = hypercharge ** 2
        total_y_squared += y_squared
        
        gen = int(particle['g'])
        if gen not in hypercharge_summary:
            hypercharge_summary[gen] = {'count': 0, 'total_y_squared': 0.0}
        hypercharge_summary[gen]['count'] += 1
        hypercharge_summary[gen]['total_y_squared'] += y_squared
    
    print(f"📊 Analysis at μ = {mu_ref:.2e} GeV:")
    print(f"  Active particles: {len(active_particles):,}")
    print(f"  Total Σ Y²: {total_y_squared:.6f}")
    print(f"  GTE contribution: (1/6) × Σ Y² = {total_y_squared/6:.6f}")
    print(f"  SM contribution: 41/6 = {41/6:.6f}")
    print(f"  Total β₁: {41/6 + total_y_squared/6:.6f}")
    
    print(f"\n📊 By generation:")
    for gen in sorted(hypercharge_summary.keys()):
        info = hypercharge_summary[gen]
        avg_y_squared = info['total_y_squared'] / info['count'] if info['count'] > 0 else 0
        print(f"  Generation {gen}: {info['count']:,} particles, avg Y² = {avg_y_squared:.6f}, total Y² = {info['total_y_squared']:.6f}")
    
    print("\n🎯 SCALING ANALYSIS:")
    print("-" * 50)
    
    # Test how the GTE contribution scales with particle count
    particle_counts = [100, 500, 1000]
    
    for n_particles in particle_counts:
        subset = small_df.head(n_particles)
        subset_active = subset[subset['mass'] < mu_ref]
        
        subset_total_y_squared = 0.0
        for idx, particle in subset_active.iterrows():
            particle_dict = particle.to_dict()
            hypercharge = assign_hypercharge(particle_dict, hypercharge_model)
            subset_total_y_squared += hypercharge ** 2
        
        subset_b1 = 41/6 + subset_total_y_squared/6
        
        print(f"  {n_particles:,} particles: Σ Y² = {subset_total_y_squared:.6f}, β₁ = {subset_b1:.6f}")
    
    print("\n🔍 DIAGNOSIS COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    diagnose_hypercharge_calculation()
