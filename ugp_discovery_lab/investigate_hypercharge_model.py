#!/usr/bin/env python3
"""
Investigate the hypercharge model and particle distribution in the full dataset.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
from typing import Any, Dict, List

# Add the UGP discovery lab to the Python path
sys.path.insert(0, str(Path(__file__).parent / "ugp_discovery_lab"))

from ugp_discovery_lab.experiments.ugp_renormalization_finalizer_enhanced import assign_hypercharge

def investigate_hypercharge_model():
    """Investigate the hypercharge model and particle distribution."""
    print("🔍 INVESTIGATION: Hypercharge Model and Particle Distribution")
    print("=" * 70)
    
    # Load the full dataset
    catalog_path = './inputs/residual_deconstruction_experiment/particle_catalog.parquet'
    df = pd.read_parquet(catalog_path)
    
    print(f"📊 Full dataset: {len(df):,} particles")
    
    # Hypercharge model
    hypercharge_model = {
        'g_factor': 1.0/3.0,
        'c_state_latched_15_offset': 1.0/6.0
    }
    
    # Process the data
    df['mass'] = df['mass_mev_calibrated'] / 1000.0  # Convert MeV to GeV
    df['g'] = df['generation']  # Map generation to g
    df['c_state'] = df['c_state'].fillna('ridge_default')
    
    print(f"   Mass range: {df['mass'].min():.3f} - {df['mass'].max():.3f} GeV")
    print(f"   Generation range: {df['generation'].min()} - {df['generation'].max()}")
    print(f"   C-state values: {df['c_state'].unique()}")
    
    print("\n🎯 GENERATION DISTRIBUTION:")
    print("-" * 50)
    gen_counts = df['generation'].value_counts().sort_index()
    for gen, count in gen_counts.items():
        percentage = count / len(df) * 100
        print(f"  Generation {gen}: {count:,} particles ({percentage:.1f}%)")
    
    print("\n🎯 C-STATE DISTRIBUTION:")
    print("-" * 50)
    c_state_counts = df['c_state'].value_counts()
    for c_state, count in c_state_counts.items():
        percentage = count / len(df) * 100
        print(f"  {c_state}: {count:,} particles ({percentage:.1f}%)")
    
    print("\n🎯 HYPERCHARGE CALCULATION SAMPLES:")
    print("-" * 50)
    
    # Sample particles from each generation and c-state
    for gen in sorted(df['generation'].unique()):
        gen_particles = df[df['generation'] == gen]
        
        c_states: np.ndarray = gen_particles['c_state'].unique()  # type: ignore
        for c_state in c_states:
            c_state_particles = gen_particles[gen_particles['c_state'] == c_state]
            
            if len(c_state_particles) > 0:
                # Sample a few particles
                sample_size = min(3, len(c_state_particles))
                sample = c_state_particles.sample(n=sample_size, random_state=42)  # type: ignore
                
                for idx, particle in sample.iterrows():
                    particle_dict = particle.to_dict()
                    hypercharge = assign_hypercharge(particle_dict, hypercharge_model)
                    
                    print(f"Gen {gen}, {c_state}: Mass={particle['mass']:.3f} GeV, Y={hypercharge:.6f}")
    
    print("\n🎯 HYPERCHARGE DISTRIBUTION:")
    print("-" * 50)
    
    # Calculate hypercharges for all particles
    hypercharges = []
    for idx, particle in df.iterrows():
        particle_dict = particle.to_dict()
        hypercharge = assign_hypercharge(particle_dict, hypercharge_model)
        hypercharges.append(hypercharge)
    
    hypercharges = np.array(hypercharges)
    
    unique_hypercharges, counts = np.unique(hypercharges, return_counts=True)
    
    for hypercharge, count in zip(unique_hypercharges, counts):
        percentage = count / len(hypercharges) * 100
        print(f"  Hypercharge {hypercharge:.6f}: {count:,} particles ({percentage:.1f}%)")
    
    print(f"\n📊 HYPERCHARGE STATISTICS:")
    print(f"  Mean: {np.mean(hypercharges):.6f}")
    print(f"  Std: {np.std(hypercharges):.6f}")
    print(f"  Min: {np.min(hypercharges):.6f}")
    print(f"  Max: {np.max(hypercharges):.6f}")
    
    print("\n🎯 MASS DISTRIBUTION BY GENERATION:")
    print("-" * 50)
    
    for gen in sorted(df['generation'].unique()):
        gen_particles = df[df['generation'] == gen]
        masses = gen_particles['mass']
        
        print(f"  Generation {gen}: {len(gen_particles):,} particles")
        print(f"    Mass range: {masses.min():.3f} - {masses.max():.3f} GeV")
        print(f"    Mean mass: {masses.mean():.3f} GeV")
        median_mass = float(masses.median())  # type: ignore
        print(f"    Median mass: {median_mass:.3f} GeV")
    
    print("\n🎯 PARTICLES ABOVE Z-POLE MASS:")
    print("-" * 50)
    
    z_pole_mass = 91.1876  # GeV
    above_z_pole = df[df['mass'] > z_pole_mass]
    
    print(f"  Particles above Z-pole mass ({z_pole_mass} GeV): {len(above_z_pole):,}")
    print(f"  Percentage: {len(above_z_pole)/len(df)*100:.1f}%")
    
    if len(above_z_pole) > 0:
        print(f"  Mass range above Z-pole: {above_z_pole['mass'].min():.3f} - {above_z_pole['mass'].max():.3f} GeV")
        
        # Show generation distribution above Z-pole
        gen_series = above_z_pole['generation']
        gen_counts_above = gen_series.value_counts().sort_index()  # type: ignore
        for gen, count in gen_counts_above.items():
            percentage = count / len(above_z_pole) * 100
            print(f"    Generation {gen}: {count:,} particles ({percentage:.1f}%)")
    
    print("\n🎯 GTE CONTRIBUTION ANALYSIS:")
    print("-" * 50)
    
    # Calculate total Y² contribution
    total_y_squared = np.sum(hypercharges ** 2)
    
    print(f"  Total Σ Y²: {total_y_squared:.6f}")
    print(f"  GTE contribution: (1/6) × Σ Y² = {total_y_squared/6:.6f}")
    print(f"  SM contribution: 41/6 = {41/6:.6f}")
    print(f"  Total β₁: {41/6 + total_y_squared/6:.6f}")
    
    # By generation
    print(f"\n📊 By generation:")
    for gen in sorted(df['generation'].unique()):
        gen_particles = df[df['generation'] == gen]
        gen_hypercharges = []
        
        for idx, particle in gen_particles.iterrows():
            particle_dict = particle.to_dict()
            hypercharge = assign_hypercharge(particle_dict, hypercharge_model)
            gen_hypercharges.append(hypercharge)
        
        gen_y_squared = np.sum(np.array(gen_hypercharges) ** 2)
        print(f"  Generation {gen}: {len(gen_particles):,} particles, Σ Y² = {gen_y_squared:.6f}")
    
    print("\n🔍 INVESTIGATION COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    investigate_hypercharge_model()
