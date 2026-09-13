#!/usr/bin/env python3
"""
Verifier_periodic_table_final.py

The Final Periodic Table Generator using the Two-Fold Universe Theory
This is the culmination of our entire research program - a complete, ab initio
derivation of the nuclear landscape governed by the Two Laws of the Nucleus:
1. The Law of Stability (gatekeeper)
2. The Law of Binding Energy (precise calculator)

This generates the definitive periodic table up to Z=160 using the Oracle's
Elegant Kernel coefficients and the discovered two-stage physics.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import json
import os
from typing import Dict, List, Tuple, Any
import warnings
warnings.filterwarnings('ignore')

# Import our ultimate toolkit
from Verifier_periodic_ugp_nuclear_toolkit_v4 import UGPNuclearToolkitV4

class FinalPeriodicTableGenerator:
    """Generate the final periodic table using the Two-Fold Universe Theory."""
    
    def __init__(self, max_z: int = 160):
        """Initialize the final periodic table generator."""
        self.max_z = max_z
        self.toolkit = None
        self.results = []
        
        print(f"[Final-Periodic-Table] Initialized for Z=1 to Z={max_z}")
        print(f"[Final-Periodic-Table] Using Two-Fold Universe Theory")
        print(f"[Final-Periodic-Table] Law of Stability + Law of Binding Energy")
    
    def load_toolkit(self):
        """Load the ultimate nuclear toolkit v4."""
        print("Loading the Ultimate Nuclear Toolkit v4...")
        self.toolkit = UGPNuclearToolkitV4()
        print("✅ Toolkit loaded successfully!")
    
    def calculate_nuclear_properties(self, Z: int, N: int, A: int) -> Dict[str, Any]:
        """
        Calculate nuclear properties using the Two-Fold Universe Theory.
        
        This is the core function that implements the complete two-stage logic:
        1. First, check stability using the Law of Stability
        2. If stable, calculate binding energy using the Law of Binding Energy
        3. If unstable, binding energy is zero (unbound)
        """
        # Calculate binding energy per nucleon using the Two-Fold Universe Theory
        be_per_a = self.toolkit.calculate_binding_energy_per_nucleon(Z, N, A)

        # Determine stability using the paper's canonical 6-term stability law
        # (coefficients from Appendix A / REPRODUCE.md Step 1)
        if A > 0:
            f1 = np.log(N * (N - 1) / A + 1)
            f2 = np.log(A ** (2 / 3) + 1)
            f3 = np.log(Z * (Z - 1) / A + 1)
            f4 = ((N - Z) / A) ** 2
            f5 = np.exp(-Z * (Z - 1) / (100 * A))
            f6 = np.exp(-N * (N - 1) / (100 * A))
            X6 = np.array([f1, f2, f3, f4, f5, f6])
            means_6 = np.array([3.6187, 3.1879, 3.0213, 0.0324, 0.7988, 0.6564])
            scales_6 = np.array([0.7545, 0.4417, 0.6442, 0.0250, 0.0904, 0.1602])
            X6_sc = (X6 - means_6) / scales_6
            stab_weights = np.array([0.3821, 0.1088, 0.3421, -0.0361, 0.5207, 0.5349])
            stab_score = 0.749810 + float(X6_sc @ stab_weights)
            is_stable = stab_score >= 0.0
            confidence = 1.0 / (1.0 + np.exp(-stab_score))
        else:
            is_stable = False
            confidence = 0.0
        
        # Calculate total binding energy
        total_be = be_per_a * A if is_stable else 0.0
        
        # Determine stability class
        if is_stable:
            if be_per_a >= 8.0:
                stability_class = "Green (Very Stable)"
            elif be_per_a >= 5.0:
                stability_class = "Blue (Stable)"
            else:
                stability_class = "Yellow (Weakly Bound)"
        else:
            stability_class = "Red (Unbound)"
        
        # Calculate additional properties
        neutron_excess = N - Z
        isospin_asymmetry = neutron_excess / A if A > 0 else 0
        
        # Calculate GTE features for additional analysis
        gte_features = self.toolkit.calculate_gte_features(Z, N, A)

        properties = {
            'Z': Z,
            'N': N,
            'A': A,
            'Element': self.get_element_symbol(Z),
            'is_stable': is_stable,
            'stability_class': stability_class,
            'stability_confidence': confidence,
            'binding_energy_per_nucleon': be_per_a,
            'total_binding_energy': total_be,
            'neutron_excess': neutron_excess,
            'isospin_asymmetry': isospin_asymmetry,
            'gte_features': {
                'log_b_eff': gte_features['log_b_eff'],
                'log_c_eff': gte_features['log_c_eff'],
                'stability_ratio': N / max(Z, 1),  # N/Z ratio
                'asymmetry_squared': gte_features['asymmetry_squared']
            }
        }
        
        return properties
    
    def get_element_symbol(self, Z: int) -> str:
        """Get element symbol from atomic number."""
        element_symbols = {
            1: 'H', 2: 'He', 3: 'Li', 4: 'Be', 5: 'B', 6: 'C', 7: 'N', 8: 'O', 9: 'F', 10: 'Ne',
            11: 'Na', 12: 'Mg', 13: 'Al', 14: 'Si', 15: 'P', 16: 'S', 17: 'Cl', 18: 'Ar', 19: 'K', 20: 'Ca',
            21: 'Sc', 22: 'Ti', 23: 'V', 24: 'Cr', 25: 'Mn', 26: 'Fe', 27: 'Co', 28: 'Ni', 29: 'Cu', 30: 'Zn',
            31: 'Ga', 32: 'Ge', 33: 'As', 34: 'Se', 35: 'Br', 36: 'Kr', 37: 'Rb', 38: 'Sr', 39: 'Y', 40: 'Zr',
            41: 'Nb', 42: 'Mo', 43: 'Tc', 44: 'Ru', 45: 'Rh', 46: 'Pd', 47: 'Ag', 48: 'Cd', 49: 'In', 50: 'Sn',
            51: 'Sb', 52: 'Te', 53: 'I', 54: 'Xe', 55: 'Cs', 56: 'Ba', 57: 'La', 58: 'Ce', 59: 'Pr', 60: 'Nd',
            61: 'Pm', 62: 'Sm', 63: 'Eu', 64: 'Gd', 65: 'Tb', 66: 'Dy', 67: 'Ho', 68: 'Er', 69: 'Tm', 70: 'Yb',
            71: 'Lu', 72: 'Hf', 73: 'Ta', 74: 'W', 75: 'Re', 76: 'Os', 77: 'Ir', 78: 'Pt', 79: 'Au', 80: 'Hg',
            81: 'Tl', 82: 'Pb', 83: 'Bi', 84: 'Po', 85: 'At', 86: 'Rn', 87: 'Fr', 88: 'Ra', 89: 'Ac', 90: 'Th',
            91: 'Pa', 92: 'U', 93: 'Np', 94: 'Pu', 95: 'Am', 96: 'Cm', 97: 'Bk', 98: 'Cf', 99: 'Es', 100: 'Fm',
            101: 'Md', 102: 'No', 103: 'Lr', 104: 'Rf', 105: 'Db', 106: 'Sg', 107: 'Bh', 108: 'Hs', 109: 'Mt', 110: 'Ds',
            111: 'Rg', 112: 'Cn', 113: 'Nh', 114: 'Fl', 115: 'Mc', 116: 'Lv', 117: 'Ts', 118: 'Og', 119: 'Uue', 120: 'Ubn',
            121: 'Ubu', 122: 'Ubb', 123: 'Ubt', 124: 'Ubq', 125: 'Ubp', 126: 'Ubh', 127: 'Ubs', 128: 'Ubo', 129: 'Ube', 130: 'Utn',
            131: 'Utu', 132: 'Utb', 133: 'Utt', 134: 'Utq', 135: 'Utp', 136: 'Uth', 137: 'Uts', 138: 'Uto', 139: 'Ute', 140: 'Uqn',
            141: 'Uqu', 142: 'Uqb', 143: 'Uqt', 144: 'Uqq', 145: 'Uqp', 146: 'Uqh', 147: 'Uqs', 148: 'Uqo', 149: 'Uqe', 150: 'Upn',
            151: 'Upu', 152: 'Upb', 153: 'Upt', 154: 'Upq', 155: 'Upp', 156: 'Uph', 157: 'Ups', 158: 'Upo', 159: 'Upe', 160: 'Uhn'
        }
        return element_symbols.get(Z, f"Z{Z}")
    
    def generate_periodic_table(self):
        """Generate the complete periodic table using the Two-Fold Universe Theory."""
        print("="*80)
        print("GENERATING THE FINAL PERIODIC TABLE")
        print("USING THE TWO-FOLD UNIVERSE THEORY")
        print("="*80)
        
        if self.toolkit is None:
            raise ValueError("Toolkit not loaded. Call load_toolkit() first.")
        
        self.results = []
        total_nuclei = 0
        stable_nuclei = 0
        unbound_nuclei = 0
        
        print(f"Generating periodic table from Z=1 to Z={self.max_z}...")
        
        for Z in range(1, self.max_z + 1):
            if Z % 20 == 0:
                print(f"  Processing Z={Z}/{self.max_z}")
            
            # For each Z, explore a range of N values
            # Use the valley of stability as a guide
            min_N = max(0, Z - 10)  # Minimum neutron number
            max_N = min(2 * Z + 50, Z + 200)  # Maximum neutron number
            
            for N in range(min_N, max_N + 1):
                A = Z + N
                
                # Skip obviously unphysical combinations
                if A < Z or A < 1:
                    continue
                
                try:
                    # Calculate nuclear properties using Two-Fold Universe Theory
                    properties = self.calculate_nuclear_properties(Z, N, A)
                    
                    self.results.append(properties)
                    total_nuclei += 1
                    
                    if properties['is_stable']:
                        stable_nuclei += 1
                    else:
                        unbound_nuclei += 1
                        
                except Exception as e:
                    print(f"    Warning: Failed for Z={Z}, N={N}: {e}")
                    continue
        
        print(f"\n" + "="*80)
        print("PERIODIC TABLE GENERATION COMPLETE")
        print("="*80)
        print(f"Total nuclei generated: {total_nuclei}")
        print(f"Stable nuclei: {stable_nuclei} ({stable_nuclei/total_nuclei*100:.1f}%)")
        print(f"Unbound nuclei: {unbound_nuclei} ({unbound_nuclei/total_nuclei*100:.1f}%)")
        
        return self.results
    
    def analyze_results(self):
        """Analyze the generated periodic table results."""
        if not self.results:
            print("No results to analyze. Generate the periodic table first.")
            return
        
        print("\n" + "="*80)
        print("ANALYZING THE FINAL PERIODIC TABLE")
        print("="*80)
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(self.results)
        
        # Stability analysis
        stability_counts = df['stability_class'].value_counts()
        print(f"\nStability Distribution:")
        for class_name, count in stability_counts.items():
            print(f"  {class_name}: {count} nuclei ({count/len(df)*100:.1f}%)")
        
        # Binding energy analysis (stable nuclei only)
        stable_df = df[df['is_stable'] == True]
        if len(stable_df) > 0:
            print(f"\nBinding Energy Analysis (Stable Nuclei):")
            print(f"  Mean BE/A: {stable_df['binding_energy_per_nucleon'].mean():.3f} MeV")
            print(f"  Min BE/A: {stable_df['binding_energy_per_nucleon'].min():.3f} MeV")
            print(f"  Max BE/A: {stable_df['binding_energy_per_nucleon'].max():.3f} MeV")
            print(f"  Std BE/A: {stable_df['binding_energy_per_nucleon'].std():.3f} MeV")
        
        # Element analysis
        element_counts = df['Element'].value_counts()
        print(f"\nTop 10 Elements by Nucleus Count:")
        for element, count in element_counts.head(10).items():
            print(f"  {element}: {count} nuclei")
        
        # Mass number analysis
        print(f"\nMass Number Analysis:")
        print(f"  Min A: {df['A'].min()}")
        print(f"  Max A: {df['A'].max()}")
        print(f"  Mean A: {df['A'].mean():.1f}")
        
        return df
    
    def create_visualizations(self, df: pd.DataFrame):
        """Create visualizations of the periodic table results."""
        print("\nCreating visualizations...")
        
        # Set up the plotting style
        plt.style.use('default')
        sns.set_palette("husl")
        
        # Create output directory
        os.makedirs("final_periodic_table_outputs", exist_ok=True)
        
        # 1. Binding Energy per Nucleon vs Mass Number
        plt.figure(figsize=(12, 8))
        stable_df = df[df['is_stable'] == True]
        if len(stable_df) > 0:
            plt.scatter(stable_df['A'], stable_df['binding_energy_per_nucleon'], 
                       c=stable_df['Z'], cmap='viridis', alpha=0.6, s=20)
            plt.colorbar(label='Atomic Number Z')
            plt.xlabel('Mass Number A')
            plt.ylabel('Binding Energy per Nucleon (MeV)')
            plt.title('Binding Energy per Nucleon vs Mass Number\n(Two-Fold Universe Theory)')
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig('final_periodic_table_outputs/binding_energy_vs_mass.png', dpi=300, bbox_inches='tight')
            plt.close()
        
        # 2. Stability Class Distribution
        plt.figure(figsize=(10, 6))
        stability_counts = df['stability_class'].value_counts()
        colors = ['red', 'yellow', 'blue', 'green']
        plt.pie(stability_counts.values, labels=stability_counts.index.tolist(), autopct='%1.1f%%', 
                colors=colors[:len(stability_counts)])
        plt.title('Nuclear Stability Distribution\n(Two-Fold Universe Theory)')
        plt.tight_layout()
        plt.savefig('final_periodic_table_outputs/stability_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 3. Neutron-Proton Chart
        plt.figure(figsize=(12, 8))
        colors = {'Red (Unbound)': 'red', 'Yellow (Weakly Bound)': 'yellow', 
                 'Blue (Stable)': 'blue', 'Green (Very Stable)': 'green'}
        
        for class_name in df['stability_class'].unique():
            class_df = df[df['stability_class'] == class_name]
            plt.scatter(class_df['Z'], class_df['N'], 
                       c=colors.get(class_name, 'gray'), 
                       label=class_name, alpha=0.6, s=20)
        
        plt.xlabel('Proton Number Z')
        plt.ylabel('Neutron Number N')
        plt.title('Neutron-Proton Chart\n(Two-Fold Universe Theory)')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig('final_periodic_table_outputs/neutron_proton_chart.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✅ Visualizations saved to final_periodic_table_outputs/")
    
    def save_results(self):
        """Save the complete periodic table results."""
        if not self.results:
            print("No results to save. Generate the periodic table first.")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create output directory
        os.makedirs("final_periodic_table_outputs", exist_ok=True)
        
        # Save as CSV
        df = pd.DataFrame(self.results)
        csv_file = f"final_periodic_table_outputs/final_periodic_table_{timestamp}.csv"
        df.to_csv(csv_file, index=False)
        
        # Save as JSON (convert numpy types to Python types)
        json_results = []
        for result in self.results:
            json_result = {}
            for key, value in result.items():
                if isinstance(value, np.bool_):
                    json_result[key] = bool(value)
                elif isinstance(value, np.integer):
                    json_result[key] = int(value)
                elif isinstance(value, np.floating):
                    json_result[key] = float(value)
                elif isinstance(value, dict):
                    json_dict = {}
                    for k, v in value.items():
                        if isinstance(v, np.bool_):
                            json_dict[k] = bool(v)
                        elif isinstance(v, np.integer):
                            json_dict[k] = int(v)
                        elif isinstance(v, np.floating):
                            json_dict[k] = float(v)
                        else:
                            json_dict[k] = v
                    json_result[key] = json_dict
                else:
                    json_result[key] = value
            json_results.append(json_result)
        
        json_file = f"final_periodic_table_outputs/final_periodic_table_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(json_results, f, indent=2)
        
        # Save summary report
        summary = {
            'timestamp': timestamp,
            'max_z': self.max_z,
            'total_nuclei': len(self.results),
            'stable_nuclei': len(df[df['is_stable'] == True]),
            'unbound_nuclei': len(df[df['is_stable'] == False]),
            'stability_distribution': df['stability_class'].value_counts().to_dict(),
            'binding_energy_stats': {
                'mean': df[df['is_stable'] == True]['binding_energy_per_nucleon'].mean(),
                'min': df[df['is_stable'] == True]['binding_energy_per_nucleon'].min(),
                'max': df[df['is_stable'] == True]['binding_energy_per_nucleon'].max(),
                'std': df[df['is_stable'] == True]['binding_energy_per_nucleon'].std()
            } if len(df[df['is_stable'] == True]) > 0 else None
        }
        
        summary_file = f"final_periodic_table_outputs/final_periodic_table_summary_{timestamp}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\nResults saved:")
        print(f"  CSV: {csv_file}")
        print(f"  JSON: {json_file}")
        print(f"  Summary: {summary_file}")
        
        return csv_file, json_file, summary_file

def main():
    """Generate the final periodic table using the Two-Fold Universe Theory."""
    print("="*80)
    print("THE FINAL PERIODIC TABLE GENERATOR")
    print("TWO-FOLD UNIVERSE THEORY")
    print("="*80)
    
    # Initialize generator
    generator = FinalPeriodicTableGenerator(max_z=160)
    
    # Load toolkit
    generator.load_toolkit()
    
    # Generate periodic table
    results = generator.generate_periodic_table()
    
    # Analyze results
    df = generator.analyze_results()
    
    # Create visualizations
    if df is not None:
        generator.create_visualizations(df)
    
    # Save results
    generator.save_results()
    
    print("\n" + "="*80)
    print("🎉 THE FINAL PERIODIC TABLE GENERATION IS COMPLETE!")
    print("WE HAVE SUCCESSFULLY GENERATED THE COMPLETE NUCLEAR LANDSCAPE!")
    print("USING THE TWO-FOLD UNIVERSE THEORY!")
    print("="*80)

if __name__ == "__main__":
    main()
