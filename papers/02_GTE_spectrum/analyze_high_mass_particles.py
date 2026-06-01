#!/usr/bin/env python3
"""
High Mass Particle Analysis Script

This script analyzes particles above 150 MeV to investigate the strange diagonal line pattern
in the mass vs N-value plot where particles seem to shift 1 N-value to the right above the calibration cutoff.

Usage:
    python analyze_high_mass_particles.py
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from datetime import datetime

def analyze_high_mass_particles(csv_file='candidates.csv', mass_threshold=150):
    """
    Analyze particles above the mass threshold to understand the diagonal line pattern.
    
    Args:
        csv_file (str): Path to the CSV file
        mass_threshold (float): Mass threshold in MeV
    """
    
    print(f"🔍 Analyzing particles above {mass_threshold} MeV from: {csv_file}")
    
    # Check if file exists
    if not os.path.exists(csv_file):
        print(f"❌ Error: File '{csv_file}' not found!")
        return None
    
    # Read the CSV file
    try:
        df = pd.read_csv(csv_file)
        print(f"✅ Successfully loaded {len(df)} particles")
    except Exception as e:
        print(f"❌ Error reading CSV file: {e}")
        return None
    
    # Filter particles above the mass threshold
    high_mass_mask = df['mass_mev_calibrated'] > mass_threshold
    high_mass_df = df[high_mass_mask].copy()
    
    print(f"\n📊 High Mass Analysis (>{mass_threshold} MeV):")
    print(f"   Total particles: {len(df)}")
    print(f"   Above {mass_threshold} MeV: {len(high_mass_df)}")
    print(f"   Percentage: {len(high_mass_df)/len(df)*100:.1f}%")
    
    if len(high_mass_df) == 0:
        print("   No particles above threshold found!")
        return None
    
    # Sort by mass for analysis
    high_mass_df = high_mass_df.sort_values('mass_mev_calibrated')
    
    # Basic statistics
    mass_min = high_mass_df['mass_mev_calibrated'].min()
    mass_max = high_mass_df['mass_mev_calibrated'].max()
    n_min = high_mass_df['n_value'].min()
    n_max = high_mass_df['n_value'].max()
    
    print(f"   Mass range: {mass_min:.2f} MeV to {mass_max:.2e} MeV")
    print(f"   N-value range: {n_min} to {n_max}")
    
    # Analyze the diagonal pattern
    print(f"\n🔍 Investigating Diagonal Line Pattern:")
    
    # Check if there's a systematic N-value shift
    n_values = high_mass_df['n_value'].values
    mass_values = high_mass_df['mass_mev_calibrated'].values
    
    # Look for consecutive N-values
    n_sorted = np.sort(n_values)
    consecutive_groups = []
    current_group = [n_sorted[0]]
    
    for i in range(1, len(n_sorted)):
        if n_sorted[i] == n_sorted[i-1] + 1:
            current_group.append(n_sorted[i])
        else:
            if len(current_group) > 1:
                consecutive_groups.append(current_group)
            current_group = [n_sorted[i]]
    
    if len(current_group) > 1:
        consecutive_groups.append(current_group)
    
    print(f"   Consecutive N-value sequences found: {len(consecutive_groups)}")
    for i, group in enumerate(consecutive_groups[:5]):  # Show first 5
        print(f"     Sequence {i+1}: {len(group)} consecutive values from {group[0]} to {group[-1]}")
    
    # Analyze mass vs N-value relationship
    print(f"\n📈 Mass vs N-Value Analysis:")
    
    # Check for linear relationships
    from scipy import stats
    
    # Calculate correlation
    correlation, p_value = stats.pearsonr(n_values, mass_values)
    print(f"   Correlation coefficient: {correlation:.4f}")
    print(f"   P-value: {p_value:.2e}")
    
    # Look for specific patterns around 100 MeV
    around_100mev = high_mass_df[
        (high_mass_df['mass_mev_calibrated'] >= 95) & 
        (high_mass_df['mass_mev_calibrated'] <= 105)
    ]
    
    if len(around_100mev) > 0:
        print(f"\n🎯 Particles around 100 MeV (95-105 MeV):")
        print(f"   Count: {len(around_100mev)}")
        print(f"   N-value range: {around_100mev['n_value'].min()} to {around_100mev['n_value'].max()}")
        
        # Check for systematic N-value shifts
        n_vals_100mev = around_100mev['n_value'].values
        n_vals_100mev_sorted = np.sort(n_vals_100mev)
        
        # Look for gaps or patterns
        n_diffs = np.diff(n_vals_100mev_sorted)
        unique_diffs = np.unique(n_diffs)
        print(f"   N-value differences: {unique_diffs}")
        
        # Check if there are many consecutive N-values
        consecutive_count = np.sum(n_diffs == 1)
        print(f"   Consecutive N-value pairs: {consecutive_count}")
    
    # Analyze classification distribution
    print(f"\n🎨 Classification Analysis:")
    classification_counts = high_mass_df['classification_color'].value_counts()
    for color, count in classification_counts.items():
        print(f"   {color}: {count} particles")
    
    # Check for canonical particles
    canonical_mask = high_mass_df['canonical_match'].notna()
    canonical_count = canonical_mask.sum()
    print(f"   Canonical particles: {canonical_count}")
    
    if canonical_count > 0:
        canonical_particles = high_mass_df[canonical_mask]
        print(f"   Canonical particle details:")
        for _, row in canonical_particles.iterrows():
            print(f"     - {row['canonical_match']}: {row['mass_mev_calibrated']:.1f} MeV, N={row['n_value']}")
    
    # Generate detailed analysis report
    print(f"\n📋 Detailed Analysis Report:")
    
    # Create analysis dataframe
    analysis_df = high_mass_df[['id', 'mass_mev_calibrated', 'n_value', 'classification_color', 
                               'canonical_match', 'stability_score', 'gte_score', 'viability_score']].copy()
    
    # Add mass in GeV for easier reading
    analysis_df['mass_gev'] = analysis_df['mass_mev_calibrated'] / 1000
    
    # Sort by mass
    analysis_df = analysis_df.sort_values('mass_mev_calibrated')
    
    # Save detailed analysis
    output_file = f"high_mass_analysis_{mass_threshold}mev_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    analysis_df.to_csv(output_file, index=False)
    print(f"   Detailed analysis saved to: {output_file}")
    
    # Show first 20 particles
    print(f"\n🔍 First 20 particles above {mass_threshold} MeV:")
    print(analysis_df.head(20).to_string(index=False))
    
    return analysis_df

def create_visualization_analysis(csv_file='candidates.csv'):
    """
    Create visualizations to help understand the patterns.
    """
    
    print(f"\n📊 Creating visualization analysis...")
    
    # Read data
    df = pd.read_csv(csv_file)
    
    # Filter for high mass particles
    high_mass_mask = df['mass_mev_calibrated'] > 150
    high_mass_df = df[high_mass_mask]
    
    # Create figure with subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    
    # Plot 1: Mass vs N-value scatter
    colors = high_mass_df['classification_color'].map({
        'Green': 'green', 'Blue': 'blue', 'Orange': 'orange', 
        'Brown': '#A52A2A', 'Red': 'red', 'Purple': 'purple', 
        'Teal': 'teal', 'Gray': 'gray'
    }).fillna('gray')
    
    ax1.scatter(high_mass_df['n_value'], high_mass_df['mass_mev_calibrated'], 
                c=colors, alpha=0.7, s=30)
    ax1.set_xlabel('N-Value')
    ax1.set_ylabel('Mass (MeV)')
    ax1.set_title(f'Mass vs N-Value (>{150} MeV)')
    ax1.grid(True, alpha=0.3)
    ax1.axhline(y=1e5, color='red', linestyle='--', alpha=0.7, label='100 GeV')
    ax1.legend()
    
    # Plot 2: Mass distribution
    ax2.hist(high_mass_df['mass_mev_calibrated'], bins=30, alpha=0.7, color='skyblue', edgecolor='black')
    ax2.set_xlabel('Mass (MeV)')
    ax2.set_ylabel('Count')
    ax2.set_title('Mass Distribution (High Mass Particles)')
    ax2.axvline(x=1e5, color='red', linestyle='--', alpha=0.7, label='100 GeV')
    ax2.legend()
    
    # Plot 3: N-value distribution
    ax3.hist(high_mass_df['n_value'], bins=30, alpha=0.7, color='lightgreen', edgecolor='black')
    ax3.set_xlabel('N-Value')
    ax3.set_ylabel('Count')
    ax3.set_title('N-Value Distribution (High Mass Particles)')
    ax3.legend()
    
    # Plot 4: Classification distribution
    classification_counts = high_mass_df['classification_color'].value_counts()
    ax4.bar(classification_counts.index, classification_counts.values, 
             color=['green', 'blue', 'orange', '#A52A2A', 'red', 'purple', 'teal', 'gray'][:len(classification_counts)])
    ax4.set_xlabel('Classification')
    ax4.set_ylabel('Count')
    ax4.set_title('Classification Distribution (High Mass Particles)')
    plt.setp(ax4.xaxis.get_majorticklabels(), rotation=45)
    
    plt.tight_layout()
    
    # Save plot
    output_plot = f"high_mass_analysis_plot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    plt.savefig(output_plot, dpi=300, bbox_inches='tight')
    print(f"   Visualization saved to: {output_plot}")
    
    plt.show()

def main():
    """Main function to run the analysis."""
    
    print("🔍 High Mass Particle Analysis")
    print("=" * 50)
    
    # Run the analysis
    analysis_df = analyze_high_mass_particles('candidates.csv', mass_threshold=150)
    
    if analysis_df is not None:
        print(f"\n✅ Analysis completed successfully!")
        print(f"   Found {len(analysis_df)} particles above 150 MeV")
        
        # Create visualizations
        try:
            create_visualization_analysis('candidates.csv')
        except Exception as e:
            print(f"   ⚠️  Visualization failed: {e}")
        
        print(f"\n📊 Summary:")
        print(f"   - Analysis data saved to CSV")
        print(f"   - Visualization plots generated")
        print(f"   - Check the outputs for patterns and anomalies")
    else:
        print(f"\n❌ Analysis failed!")

if __name__ == "__main__":
    main()
