#!/usr/bin/env python3
"""
Examine 100 MeV Region Script

This script examines particles around 100 MeV to understand the diagonal line pattern.
"""

import pandas as pd
import numpy as np

def examine_100mev_region():
    """Examine particles from 90 MeV and up to see the diagonal pattern."""
    
    print("🔍 Examining particles from 90 MeV and up...")
    
    # Read the CSV file
    df = pd.read_csv('candidates.csv')
    
    # Filter particles from 90 MeV and up
    high_mass = df[df['mass_mev_calibrated'] >= 90].copy()
    
    print(f"📊 Found {len(high_mass)} particles from 90 MeV and up")
    
    if len(high_mass) == 0:
        print("   No particles found in this range!")
        return
    
    # Sort by mass to see the progression
    high_mass = high_mass.sort_values(by='mass_mev_calibrated', ascending=True, na_position='last').reset_index(drop=True)
    
    print(f"\n🎯 Mass distribution:")
    mass_values = high_mass['mass_mev_calibrated'].to_numpy()
    print(f"   Mass range: {mass_values.min():.2f} MeV to {mass_values.max():.2e} MeV")
    print(f"   Total particles: {len(high_mass)}")
    
    # Show the data progression
    print(f"\n📋 First 30 particles from 90 MeV up:")
    print(f"{'N-value':>8} {'Mass (MeV)':>10} {'Color':>8} {'ID':>20}")
    print("-" * 50)
    
    for i, (_, row) in enumerate(high_mass.iterrows()):
        if i >= 30:  # Show first 30
            break
        n_val = row['n_value']
        mass = row['mass_mev_calibrated']
        color = row['classification_color']
        particle_id = row['id'][:20]  # Truncate long IDs
        
        print(f"{n_val:8d} {mass:10.1f} {color:8s} {particle_id:20s}")
    
    # Look for patterns in N-value progression
    print(f"\n🔍 N-value Pattern Analysis:")
    
    # Check N-value distribution
    n_values = high_mass['n_value'].to_numpy()
    print(f"   N-value range: {n_values.min()} to {n_values.max()}")
    print(f"   Unique N-values: {len(np.unique(n_values))}")
    
    # Look for specific mass ranges where you see the diagonal pattern
    print(f"\n🎯 Specific Mass Ranges:")
    
    # 90-110 MeV (around the cutoff)
    range_90_110 = high_mass[
        (high_mass['mass_mev_calibrated'] >= 90) & 
        (high_mass['mass_mev_calibrated'] <= 110)
    ]
    print(f"   90-110 MeV: {len(range_90_110)} particles")
    if len(range_90_110) > 0:
        print(f"     N-value range: {range_90_110['n_value'].min()} to {range_90_110['n_value'].max()}")
        # Show first few
        for i, (_, row) in enumerate(range_90_110.head(10).iterrows()):
            print(f"       N={row['n_value']:6d}, M={row['mass_mev_calibrated']:6.1f} MeV, {row['classification_color']}")
    
    # 100-120 MeV (just above cutoff)
    range_100_120 = high_mass[
        (high_mass['mass_mev_calibrated'] >= 100) & 
        (high_mass['mass_mev_calibrated'] <= 120)
    ]
    print(f"   100-120 MeV: {len(range_100_120)} particles")
    if len(range_100_120) > 0:
        print(f"     N-value range: {range_100_120['n_value'].min()} to {range_100_120['n_value'].max()}")
        # Show first few
        for i, (_, row) in enumerate(range_100_120.head(10).iterrows()):
            print(f"       N={row['n_value']:6d}, M={row['mass_mev_calibrated']:6.1f} MeV, {row['classification_color']}")
    
    # Check for systematic N-value shifts
    print(f"\n🔍 Looking for Diagonal Pattern:")
    
    # Calculate mass-N correlation
    mass_n_pairs = high_mass[['mass_mev_calibrated', 'n_value']].to_numpy()
    if len(mass_n_pairs) > 1:
        correlation = np.corrcoef(mass_n_pairs[:, 0], mass_n_pairs[:, 1])[0, 1]
        print(f"   Overall Mass-N correlation: {correlation:.4f}")
    
    # Look for consecutive N-values in specific mass ranges
    for mass_range in [(90, 110), (100, 120), (110, 130)]:
        range_data = high_mass[
            (high_mass['mass_mev_calibrated'] >= mass_range[0]) & 
            (high_mass['mass_mev_calibrated'] <= mass_range[1])
        ]
        if len(range_data) > 1:
            n_vals = range_data['n_value'].tolist()
            n_sorted = sorted(n_vals)
            consecutive_count = 0
            for i in range(1, len(n_sorted)):
                if n_sorted[i] == n_sorted[i-1] + 1:
                    consecutive_count += 1
            print(f"   {mass_range[0]}-{mass_range[1]} MeV: {consecutive_count} consecutive N-value pairs")

if __name__ == "__main__":
    examine_100mev_region()
