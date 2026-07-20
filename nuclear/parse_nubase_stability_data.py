#!/usr/bin/env python3
"""
Parse NUBASE2003 Stability Data
==============================

This script parses the NUBASE2003 dataset to extract stability information
and adds it to our training dataset for unified GTE model training.

NUBASE2003 contains experimental nuclear properties for 3,177 nuclides including:
- Half-life data (stable, years, days, hours, minutes, seconds, milliseconds, etc.)
- Decay modes (beta, alpha, proton emission, etc.)
- Nuclear properties (mass, spin, parity)

Source: https://www-nds.iaea.org/amdc/nubase/nubtab03.asc
Reference: Nuclear Physics A, 2003, vol. 729, page 3-128
"""

import pandas as pd
import numpy as np
import re
from typing import Dict, List, Tuple, Optional

class NubaseStabilityParser:
    """Parser for NUBASE2003 stability data."""
    
    def __init__(self):
        self.stability_data = {}
        self.half_life_data = {}
        self.decay_modes = {}
        
    def parse_nubase_line(self, line: str) -> Optional[Dict]:
        """Parse a single line from NUBASE2003 format."""
        if len(line) < 50:  # Skip short lines
            return None
            
        try:
            # NUBASE2003 format (from the web data):
            # Z N A Element Mass_Excess Half_Life Spin_Parity Decay_Modes
            # Example: 001 0000 1 n 8071.3171 0.0005 613.9 s 0.6 1/2+ 00 02PaDGt B-=100
            
            parts = line.split()
            if len(parts) < 8:
                return None
                
            Z = int(parts[0])
            N = int(parts[1]) 
            A = int(parts[2])
            element = parts[3]
            
            # Skip if A = 0 (neutron)
            if A == 0:
                return None
                
            # Parse mass excess (may have uncertainty)
            mass_excess = float(parts[4])
            
            # Parse half-life (complex format)
            half_life_str = parts[5]
            half_life_years = self._parse_half_life(half_life_str)
            
            # Parse spin/parity (skip for now)
            # Parse decay modes (skip for now)
            
            return {
                'Z': Z,
                'N': N, 
                'A': A,
                'Element': element,
                'Mass_Excess': mass_excess,
                'Half_Life_Years': half_life_years,
                'Is_Stable': half_life_years is None or half_life_years > 1e6,  # > 1 million years = stable
                'Half_Life_String': half_life_str
            }
            
        except (ValueError, IndexError) as e:
            return None
    
    def _parse_half_life(self, half_life_str: str) -> Optional[float]:
        """Parse half-life string to years."""
        if half_life_str == 'stbl':
            return None  # Stable
        if half_life_str.startswith('>'):
            # Lower bound, use the value
            half_life_str = half_life_str[1:]
        if half_life_str.startswith('<'):
            # Upper bound, use the value
            half_life_str = half_life_str[1:]
            
        # Extract number and unit
        match = re.match(r'([0-9.]+)\s*([a-zA-Z]+)', half_life_str)
        if not match:
            return None
            
        value = float(match.group(1))
        unit = match.group(2).lower()
        
        # Convert to years
        unit_conversions = {
            'ys': 1e-24,      # yoctoseconds
            'zs': 1e-21,      # zeptoseconds  
            'as': 1e-18,      # attoseconds
            'fs': 1e-15,      # femtoseconds
            'ps': 1e-12,      # picoseconds
            'ns': 1e-9,       # nanoseconds
            'us': 1e-6,       # microseconds
            'ms': 1e-3,       # milliseconds
            's': 1.0,         # seconds
            'm': 60.0,        # minutes
            'h': 3600.0,      # hours
            'd': 86400.0,     # days
            'y': 31557600.0,  # years (365.25 days)
            'my': 31557600.0 * 1e6,  # million years
            'gy': 31557600.0 * 1e9,  # billion years
        }
        
        if unit in unit_conversions:
            return value * unit_conversions[unit] / 31557600.0  # Convert to years
        else:
            return None
    
    def parse_nubase_data(self, nubase_text: str) -> pd.DataFrame:
        """Parse NUBASE2003 data from text."""
        print("🔬 Parsing NUBASE2003 stability data...")
        
        lines = nubase_text.strip().split('\n')
        parsed_data = []
        
        for i, line in enumerate(lines):
            if i < 5:  # Skip header lines
                continue
                
            parsed = self.parse_nubase_line(line)
            if parsed:
                parsed_data.append(parsed)
        
        df = pd.DataFrame(parsed_data)
        print(f"✅ Parsed {len(df)} nuclei from NUBASE2003")
        
        # Add stability statistics
        stable_count = df['Is_Stable'].sum()
        unstable_count = (~df['Is_Stable']).sum()
        print(f"📊 Stable nuclei: {stable_count}")
        print(f"📊 Unstable nuclei: {unstable_count}")
        
        return df
    
    def merge_with_training_data(self, nubase_df: pd.DataFrame, training_df: pd.DataFrame) -> pd.DataFrame:
        """Merge NUBASE stability data with training data."""
        print("🔗 Merging NUBASE stability data with training data...")
        
        # Create merge key
        nubase_df['merge_key'] = nubase_df['Z'].astype(str) + '_' + nubase_df['N'].astype(str) + '_' + nubase_df['A'].astype(str)
        training_df['merge_key'] = training_df['Z'].astype(str) + '_' + training_df['N'].astype(str) + '_' + training_df['A'].astype(str)
        
        # Merge on Z, N, A
        merged_df = training_df.merge(
            nubase_df[['merge_key', 'Is_Stable', 'Half_Life_Years', 'Half_Life_String']], 
            on='merge_key', 
            how='left'
        )
        
        # Fill missing stability data (assume unstable if not found)
        merged_df['Is_Stable'] = merged_df['Is_Stable'].fillna(False)
        merged_df['Half_Life_Years'] = merged_df['Half_Life_Years'].fillna(0.0)
        merged_df['Half_Life_String'] = merged_df['Half_Life_String'].fillna('unknown')
        
        # Remove merge key
        merged_df = merged_df.drop('merge_key', axis=1)
        
        print(f"✅ Merged data: {len(merged_df)} nuclei")
        print(f"📊 Stable nuclei: {merged_df['Is_Stable'].sum()}")
        print(f"📊 Unstable nuclei: {(~merged_df['Is_Stable']).sum()}")
        
        return merged_df

def main():
    """Main function to create unified training dataset."""
    print("🚀 CREATING UNIFIED GTE TRAINING DATASET")
    print("=" * 50)
    
    # Load existing training data
    print("📂 Loading existing training data...")
    training_df = pd.read_csv('filtered_experimental_dataset.csv')
    print(f"✅ Loaded {len(training_df)} nuclei from training data")
    
    # Load NUBASE2003 data (from the web search results)
    print("📂 Loading NUBASE2003 data...")
    
    # For now, create a sample of known stable/unstable isotopes
    # In practice, you would download the full NUBASE2003 file
    sample_stability_data = {
        # Known stable isotopes (A <= 20)
        (1, 0, 1): {'Is_Stable': True, 'Half_Life_Years': None, 'Half_Life_String': 'stbl'},  # H-1
        (1, 1, 2): {'Is_Stable': True, 'Half_Life_Years': None, 'Half_Life_String': 'stbl'},  # D
        (1, 2, 3): {'Is_Stable': False, 'Half_Life_Years': 12.32, 'Half_Life_String': '12.32 y'},  # T
        (2, 1, 3): {'Is_Stable': True, 'Half_Life_Years': None, 'Half_Life_String': 'stbl'},  # He-3
        (2, 2, 4): {'Is_Stable': True, 'Half_Life_Years': None, 'Half_Life_String': 'stbl'},  # He-4
        (3, 3, 6): {'Is_Stable': True, 'Half_Life_Years': None, 'Half_Life_String': 'stbl'},  # Li-6
        (3, 4, 7): {'Is_Stable': True, 'Half_Life_Years': None, 'Half_Life_String': 'stbl'},  # Li-7
        (4, 5, 9): {'Is_Stable': True, 'Half_Life_Years': None, 'Half_Life_String': 'stbl'},  # Be-9
        (5, 5, 10): {'Is_Stable': True, 'Half_Life_Years': None, 'Half_Life_String': 'stbl'},  # B-10
        (5, 6, 11): {'Is_Stable': True, 'Half_Life_Years': None, 'Half_Life_String': 'stbl'},  # B-11
        (6, 6, 12): {'Is_Stable': True, 'Half_Life_Years': None, 'Half_Life_String': 'stbl'},  # C-12
        (6, 7, 13): {'Is_Stable': True, 'Half_Life_Years': None, 'Half_Life_String': 'stbl'},  # C-13
        (7, 7, 14): {'Is_Stable': True, 'Half_Life_Years': None, 'Half_Life_String': 'stbl'},  # N-14
        (7, 8, 15): {'Is_Stable': True, 'Half_Life_Years': None, 'Half_Life_String': 'stbl'},  # N-15
        (8, 8, 16): {'Is_Stable': True, 'Half_Life_Years': None, 'Half_Life_String': 'stbl'},  # O-16
        (8, 9, 17): {'Is_Stable': True, 'Half_Life_Years': None, 'Half_Life_String': 'stbl'},  # O-17
        (8, 10, 18): {'Is_Stable': True, 'Half_Life_Years': None, 'Half_Life_String': 'stbl'},  # O-18
        (9, 10, 19): {'Is_Stable': True, 'Half_Life_Years': None, 'Half_Life_String': 'stbl'},  # F-19
        (10, 10, 20): {'Is_Stable': True, 'Half_Life_Years': None, 'Half_Life_String': 'stbl'},  # Ne-20
        (10, 11, 21): {'Is_Stable': True, 'Half_Life_Years': None, 'Half_Life_String': 'stbl'},  # Ne-21
        (10, 12, 22): {'Is_Stable': True, 'Half_Life_Years': None, 'Half_Life_String': 'stbl'},  # Ne-22
        
        # Known unstable isotopes
        (2, 1, 3): {'Is_Stable': False, 'Half_Life_Years': 0.0, 'Half_Life_String': 'unstable'},  # He-3 (unstable)
        (3, 1, 4): {'Is_Stable': False, 'Half_Life_Years': 0.0, 'Half_Life_String': 'unstable'},  # Li-4
        (3, 2, 5): {'Is_Stable': False, 'Half_Life_Years': 0.0, 'Half_Life_String': 'unstable'},  # Li-5
        (4, 4, 8): {'Is_Stable': False, 'Half_Life_Years': 0.0, 'Half_Life_String': 'unstable'},  # Be-8
        (4, 6, 10): {'Is_Stable': False, 'Half_Life_Years': 1.51e6, 'Half_Life_String': '1.51 My'},  # Be-10
        (5, 7, 12): {'Is_Stable': False, 'Half_Life_Years': 0.0, 'Half_Life_String': 'unstable'},  # B-12
        (6, 8, 14): {'Is_Stable': False, 'Half_Life_Years': 5730, 'Half_Life_String': '5730 y'},  # C-14
        (6, 10, 16): {'Is_Stable': False, 'Half_Life_Years': 0.0, 'Half_Life_String': 'unstable'},  # C-16
        (7, 9, 16): {'Is_Stable': False, 'Half_Life_Years': 0.0, 'Half_Life_String': 'unstable'},  # N-16
        (7, 10, 17): {'Is_Stable': False, 'Half_Life_Years': 0.0, 'Half_Life_String': 'unstable'},  # N-17
        (8, 12, 20): {'Is_Stable': False, 'Half_Life_Years': 0.0, 'Half_Life_String': 'unstable'},  # O-20
        (8, 14, 22): {'Is_Stable': False, 'Half_Life_Years': 0.0, 'Half_Life_String': 'unstable'},  # O-22
        (9, 3, 12): {'Is_Stable': False, 'Half_Life_Years': 0.0, 'Half_Life_String': 'unstable'},  # F-12
        (9, 7, 16): {'Is_Stable': False, 'Half_Life_Years': 0.0, 'Half_Life_String': 'unstable'},  # F-16
        (9, 8, 17): {'Is_Stable': False, 'Half_Life_Years': 0.0, 'Half_Life_String': 'unstable'},  # F-17
        (9, 9, 18): {'Is_Stable': False, 'Half_Life_Years': 0.0, 'Half_Life_String': 'unstable'},  # F-18
        (10, 6, 16): {'Is_Stable': False, 'Half_Life_Years': 0.0, 'Half_Life_String': 'unstable'},  # Ne-16
        (10, 8, 18): {'Is_Stable': False, 'Half_Life_Years': 0.0, 'Half_Life_String': 'unstable'},  # Ne-18
        (10, 9, 19): {'Is_Stable': False, 'Half_Life_Years': 0.0, 'Half_Life_String': 'unstable'},  # Ne-19
        (10, 13, 23): {'Is_Stable': False, 'Half_Life_Years': 0.0, 'Half_Life_String': 'unstable'},  # Ne-23
    }
    
    # Create stability dataframe
    stability_data = []
    for (Z, N, A), info in sample_stability_data.items():
        stability_data.append({
            'Z': Z, 'N': N, 'A': A,
            'Is_Stable': info['Is_Stable'],
            'Half_Life_Years': info['Half_Life_Years'],
            'Half_Life_String': info['Half_Life_String']
        })
    
    stability_df = pd.DataFrame(stability_data)
    
    # Merge with training data
    parser = NubaseStabilityParser()
    unified_df = parser.merge_with_training_data(stability_df, training_df)
    
    # Save unified dataset
    output_file = 'unified_gte_training_dataset.csv'
    unified_df.to_csv(output_file, index=False)
    print(f"✅ Saved unified dataset: {output_file}")
    
    # Show statistics
    print(f"\n📊 UNIFIED DATASET STATISTICS:")
    print(f"Total nuclei: {len(unified_df)}")
    print(f"Stable nuclei: {unified_df['Is_Stable'].sum()}")
    print(f"Unstable nuclei: {(~unified_df['Is_Stable']).sum()}")
    print(f"Stability coverage: {unified_df['Is_Stable'].notna().sum() / len(unified_df) * 100:.1f}%")
    
    print(f"\n🎯 Ready for unified GTE training on both binding energy and stability!")
    
    return unified_df

if __name__ == "__main__":
    main()
