#!/usr/bin/env python3
"""
GTE Feature Ablation Study - The Final Validation of UGP Theory

This script performs the critical three-way model comparison to prove whether
GTE features provide unique predictive power for nuclear binding energy prediction.

The experiment compares:
1. Physics-Only Model: Standard nuclear physics features only
2. GTE-Only Model: GTE triple features only  
3. Hybrid Model: Combined physics + GTE features

This is the definitive test of whether GTE theory adds value beyond standard physics.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score
import xgboost as xgb
import warnings
warnings.filterwarnings('ignore')

class GTEAblationStudy:
    """Comprehensive ablation study for GTE feature validation."""
    
    def __init__(self, dataset_path="filtered_experimental_dataset.csv"):
        """Initialize the ablation study with experimental dataset."""
        self.dataset_path = dataset_path
        self.k_gen = 0.0072973525693  # UGP Elegant Kernel constant
        
        # GTE triple constants (from oracle implementation)
        self.proton_gte = {'a_eff': 5, 'b_eff': 11459, 'c_eff': 15, 'g_eff': 3}
        self.neutron_gte = {'a_eff': 5, 'b_eff': 11441, 'c_eff': 15, 'g_eff': 3}
        
        # Load and prepare data
        self.load_data()
        self.prepare_feature_sets()
        
    def load_data(self):
        """Load the experimental dataset."""
        print("Loading experimental dataset...")
        self.df = pd.read_csv(self.dataset_path)
        print(f"Loaded {len(self.df)} nuclei from {self.dataset_path}")
        
        # Extract basic nuclear properties
        self.Z = self.df['Z'].values
        self.N = self.df['N'].values  
        self.A = self.df['A'].values
        self.y = self.df['BE'].values  # Target: binding energy
        
        print(f"Dataset range: Z={self.Z.min()}-{self.Z.max()}, A={self.A.min()}-{self.A.max()}")
        print(f"Binding energy range: {self.y.min():.1f} - {self.y.max():.1f} MeV")
        
    def get_canonical_gte_triple(self, Z, N):
        """Calculate canonical GTE triple for nucleus (Z, N)."""
        A = Z + N
        
        # Calculate composite GTE triple with correct composition rules
        # a_eff: multiplicative (p_a^Z * n_a^N)
        log_a_eff = Z * np.log(self.proton_gte['a_eff']) + N * np.log(self.neutron_gte['a_eff'])
        a_eff = np.exp(np.minimum(log_a_eff, 700))  # Cap to prevent overflow
        
        # Additive terms with bounds to prevent overflow
        b_eff = np.minimum(Z * self.proton_gte['b_eff'] + N * self.neutron_gte['b_eff'], 1e15)
        c_eff = np.minimum(Z * self.proton_gte['c_eff'] + N * self.neutron_gte['c_eff'], 1e15) 
        g_eff = np.minimum(Z * self.proton_gte['g_eff'] + N * self.neutron_gte['g_eff'], 1e15)
        
        # Ensure all values are finite and positive
        a_eff = np.maximum(a_eff, 1e-10)
        b_eff = np.maximum(b_eff, 1e-10)
        c_eff = np.maximum(c_eff, 1e-10)
        g_eff = np.maximum(g_eff, 1e-10)
        
        return a_eff, b_eff, c_eff, g_eff
        
    def calculate_physics_features(self, Z, N, A):
        """Calculate comprehensive physics-only features."""
        features = []
        
        # Basic nuclear properties
        features.extend([Z, N, A])
        
        # Standard SEMF terms
        surface = A ** (2/3)
        volume = A
        coulomb = Z * (Z - 1) / (A ** (1/3)) if A > 0 else 0
        asymmetry = ((N - Z) ** 2) / A if A > 0 else 0
        
        features.extend([surface, volume, coulomb, asymmetry])
        
        # Pairing terms
        z_even = (Z % 2 == 0).astype(int)
        n_even = (N % 2 == 0).astype(int)
        pairing = z_even * n_even  # Even-even = 1, others = 0
        
        features.extend([z_even, n_even, pairing])
        
        # Power terms
        features.extend([
            A ** (1/3), A ** (1/2), A ** (4/3),
            Z ** (1/3), Z ** (2/3), Z ** (4/3),
            N ** (1/3), N ** (2/3), N ** (4/3)
        ])
        
        # Logarithmic terms
        features.extend([
            np.log(A) if A > 0 else 0,
            np.log(Z) if Z > 0 else 0, 
            np.log(N) if N > 0 else 0
        ])
        
        # Interaction terms
        features.extend([
            Z * N, Z * A, N * A,
            Z * surface, N * surface, A * surface,
            Z * coulomb, N * coulomb, A * coulomb,
            Z * asymmetry, N * asymmetry, A * asymmetry
        ])
        
        # Ratio terms
        features.extend([
            Z / A if A > 0 else 0,
            N / A if A > 0 else 0,
            Z / N if N > 0 else 0,
            surface / A if A > 0 else 0,
            coulomb / A if A > 0 else 0,
            asymmetry / A if A > 0 else 0
        ])
        
        # Shell effects (magic numbers)
        magic_numbers = [2, 8, 20, 28, 50, 82, 126]
        z_shell = min([abs(Z - m) for m in magic_numbers])
        n_shell = min([abs(N - m) for m in magic_numbers])
        
        features.extend([z_shell, n_shell])
        
        # Fissility parameter
        fissility = Z ** 2 / A if A > 0 else 0
        features.append(fissility)
        
        return np.array(features)
        
    def calculate_gte_features(self, Z, N, A):
        """Calculate comprehensive GTE-only features."""
        features = []
        
        # Get canonical GTE triple
        a_eff, b_eff, c_eff, g_eff = self.get_canonical_gte_triple(Z, N)
        
        # Basic GTE triple features
        features.extend([a_eff, b_eff, c_eff, g_eff])
        
        # Logarithmic GTE features
        features.extend([
            np.log(a_eff + 1e-10),
            np.log(b_eff + 1e-10), 
            np.log(c_eff + 1e-10),
            np.log(g_eff + 1e-10)
        ])
        
        # Square root GTE features
        features.extend([
            np.sqrt(a_eff),
            np.sqrt(b_eff),
            np.sqrt(c_eff), 
            np.sqrt(g_eff)
        ])
        
        # Power GTE features
        features.extend([
            a_eff ** 2, b_eff ** 2, c_eff ** 2, g_eff ** 2,
            a_eff ** 3, b_eff ** 3, c_eff ** 3, g_eff ** 3
        ])
        
        # Cross GTE features
        features.extend([
            a_eff * b_eff, a_eff * c_eff, a_eff * g_eff,
            b_eff * c_eff, b_eff * g_eff, c_eff * g_eff
        ])
        
        # Ratio GTE features
        features.extend([
            b_eff / (a_eff + 1e-10),
            c_eff / (b_eff + 1e-10),
            g_eff / (c_eff + 1e-10),
            a_eff / (g_eff + 1e-10)
        ])
        
        # Geometric and harmonic means
        abc_geometric_mean = (a_eff * b_eff * c_eff) ** (1/3)
        abc_harmonic_mean = 3 / (1/(a_eff + 1e-10) + 1/(b_eff + 1e-10) + 1/(c_eff + 1e-10))
        
        features.extend([abc_geometric_mean, abc_harmonic_mean])
        
        # Mu parameters (fractional parts)
        mu_a = a_eff - np.floor(a_eff)
        mu_b = b_eff - np.floor(b_eff) 
        mu_c = c_eff - np.floor(c_eff)
        mu_g = g_eff - np.floor(g_eff)
        
        features.extend([mu_a, mu_b, mu_c, mu_g])
        
        # Mu interactions
        features.extend([
            mu_a + mu_b + mu_c + mu_g,
            mu_a * mu_b * mu_c * mu_g,
            abs(mu_a) + abs(mu_b) + abs(mu_c) + abs(mu_g)
        ])
        
        # Shell strength indicators (from GTE theory)
        shell_strength = np.log(b_eff / (c_eff + 1e-10))
        features.append(shell_strength)
        
        # Relative indices
        i_rel_b = b_eff / (a_eff + 1e-10)
        i_rel_c = c_eff / (b_eff + 1e-10)
        i_rel_g = g_eff / (c_eff + 1e-10)
        
        features.extend([i_rel_b, i_rel_c, i_rel_g])
        
        # GTE kernel interactions
        k_gen_surface = self.k_gen * (A ** (2/3))
        features.extend([
            k_gen_surface,
            k_gen_surface ** 2,
            np.exp(np.minimum(k_gen_surface, 50)),  # Cap exp to prevent overflow
            a_eff * k_gen_surface,
            b_eff * k_gen_surface,
            c_eff * k_gen_surface,
            g_eff * k_gen_surface
        ])
        
        # Convert to array and ensure all values are finite
        features_array = np.array(features)
        
        # Replace any infinite or NaN values with finite alternatives
        features_array = np.nan_to_num(features_array, nan=0.0, posinf=1e15, neginf=-1e15)
        
        return features_array
        
    def prepare_feature_sets(self):
        """Prepare the three feature sets for comparison."""
        print("Preparing feature sets...")
        
        # Calculate features for all nuclei
        physics_features = []
        gte_features = []
        
        for i in range(len(self.Z)):
            Z, N, A = self.Z[i], self.N[i], self.A[i]
            
            # Physics features
            phys_feat = self.calculate_physics_features(Z, N, A)
            physics_features.append(phys_feat)
            
            # GTE features  
            gte_feat = self.calculate_gte_features(Z, N, A)
            gte_features.append(gte_feat)
            
        # Convert to arrays
        self.X_physics = np.array(physics_features)
        self.X_gte = np.array(gte_features)
        self.X_hybrid = np.hstack([self.X_physics, self.X_gte])
        
        print(f"Physics features: {self.X_physics.shape[1]} features")
        print(f"GTE features: {self.X_gte.shape[1]} features") 
        print(f"Hybrid features: {self.X_hybrid.shape[1]} features")
        
    def train_model(self, X, y, model_name, test_size=0.2, random_state=42):
        """Train XGBoost model with cross-validation."""
        print(f"\nTraining {model_name} model...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # XGBoost parameters (optimized for nuclear binding energy)
        xgb_params = {
            'n_estimators': 1000,
            'max_depth': 6,
            'learning_rate': 0.1,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'random_state': random_state,
            'n_jobs': -1
        }
        
        # Train model
        model = xgb.XGBRegressor(**xgb_params)
        model.fit(X_train_scaled, y_train)
        
        # Cross-validation
        cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5, scoring='neg_mean_absolute_error')
        cv_mae = -cv_scores.mean()
        cv_std = cv_scores.std()
        
        # Test predictions
        y_pred = model.predict(X_test_scaled)
        test_mae = mean_absolute_error(y_test, y_pred)
        test_r2 = r2_score(y_test, y_pred)
        
        print(f"{model_name} Results:")
        print(f"  CV MAE: {cv_mae:.3f} ± {cv_std:.3f} MeV")
        print(f"  Test MAE: {test_mae:.3f} MeV")
        print(f"  Test R²: {test_r2:.3f}")
        
        return {
            'model': model,
            'scaler': scaler,
            'cv_mae': cv_mae,
            'cv_std': cv_std,
            'test_mae': test_mae,
            'test_r2': test_r2,
            'X_test': X_test,
            'y_test': y_test,
            'y_pred': y_pred
        }
        
    def run_ablation_study(self):
        """Run the complete ablation study."""
        print("=" * 80)
        print("GTE FEATURE ABLATION STUDY - THE FINAL VALIDATION")
        print("=" * 80)
        
        # Train all three models
        results = {}
        
        # 1. Physics-Only Model
        results['physics'] = self.train_model(
            self.X_physics, self.y, "Physics-Only"
        )
        
        # 2. GTE-Only Model  
        results['gte'] = self.train_model(
            self.X_gte, self.y, "GTE-Only"
        )
        
        # 3. Hybrid Model
        results['hybrid'] = self.train_model(
            self.X_hybrid, self.y, "Hybrid (Physics + GTE)"
        )
        
        # Generate final report
        self.generate_final_report(results)
        
        return results
        
    def generate_final_report(self, results):
        """Generate the definitive final report."""
        print("\n" + "=" * 80)
        print("FINAL ABLATION STUDY RESULTS")
        print("=" * 80)
        
        # Create results table
        results_data = []
        for model_name, result in results.items():
            results_data.append({
                'Model': model_name.replace('_', ' ').title(),
                'CV MAE (MeV)': f"{result['cv_mae']:.3f} ± {result['cv_std']:.3f}",
                'Test MAE (MeV)': f"{result['test_mae']:.3f}",
                'Test R²': f"{result['test_r2']:.3f}"
            })
            
        results_df = pd.DataFrame(results_data)
        print("\nPERFORMANCE COMPARISON:")
        print(results_df.to_string(index=False))
        
        # Calculate improvements
        physics_mae = results['physics']['test_mae']
        gte_mae = results['gte']['test_mae'] 
        hybrid_mae = results['hybrid']['test_mae']
        
        gte_improvement = (physics_mae - gte_mae) / physics_mae * 100
        hybrid_improvement = (physics_mae - hybrid_mae) / physics_mae * 100
        gte_vs_hybrid = (gte_mae - hybrid_mae) / gte_mae * 100
        
        print(f"\nIMPROVEMENT ANALYSIS:")
        print(f"GTE-Only vs Physics-Only: {gte_improvement:+.1f}% improvement")
        print(f"Hybrid vs Physics-Only: {hybrid_improvement:+.1f}% improvement") 
        print(f"Hybrid vs GTE-Only: {gte_vs_hybrid:+.1f}% improvement")
        
        # Generate conclusions
        print(f"\n" + "=" * 80)
        print("DEFINITIVE CONCLUSIONS")
        print("=" * 80)
        
        if hybrid_mae < physics_mae * 0.95:  # 5% improvement threshold
            print("✅ GTE FEATURES PROVIDE SIGNIFICANT VALUE")
            print("   The hybrid model significantly outperforms physics-only model.")
            print("   This proves GTE theory adds unique predictive information.")
        else:
            print("❌ GTE FEATURES PROVIDE MINIMAL VALUE")
            print("   The hybrid model does not significantly outperform physics-only model.")
            print("   GTE theory may not add substantial predictive information.")
            
        if gte_mae < physics_mae * 0.90:  # 10% improvement threshold
            print("🎯 GTE-ONLY MODEL IS COMPETITIVE")
            print("   GTE features alone can predict nuclear binding energies.")
            print("   This demonstrates the self-contained power of GTE theory.")
        else:
            print("⚠️  GTE-ONLY MODEL NEEDS IMPROVEMENT")
            print("   GTE features alone are not sufficient for accurate prediction.")
            print("   Physics features are still essential.")
            
        # Create visualization
        self.create_visualization(results)
        
        print(f"\n" + "=" * 80)
        print("ABLATION STUDY COMPLETE")
        print("=" * 80)
        
    def create_visualization(self, results):
        """Create visualization of results."""
        plt.figure(figsize=(12, 8))
        
        # Prepare data for plotting
        model_names = ['Physics-Only', 'GTE-Only', 'Hybrid']
        mae_values = [results['physics']['test_mae'], 
                     results['gte']['test_mae'], 
                     results['hybrid']['test_mae']]
        r2_values = [results['physics']['test_r2'],
                    results['gte']['test_r2'], 
                    results['hybrid']['test_r2']]
        
        # Create subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # MAE comparison
        bars1 = ax1.bar(model_names, mae_values, color=['red', 'blue', 'green'], alpha=0.7)
        ax1.set_ylabel('Mean Absolute Error (MeV)')
        ax1.set_title('Model Performance Comparison - MAE')
        ax1.grid(True, alpha=0.3)
        
        # Add value labels on bars
        for bar, value in zip(bars1, mae_values):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                    f'{value:.2f}', ha='center', va='bottom', fontweight='bold')
        
        # R² comparison
        bars2 = ax2.bar(model_names, r2_values, color=['red', 'blue', 'green'], alpha=0.7)
        ax2.set_ylabel('R² Score')
        ax2.set_title('Model Performance Comparison - R²')
        ax2.grid(True, alpha=0.3)
        
        # Add value labels on bars
        for bar, value in zip(bars2, r2_values):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{value:.3f}', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig('ablation_study_results.png', dpi=300, bbox_inches='tight')
        print(f"\nVisualization saved as 'ablation_study_results.png'")

def main():
    """Run the complete ablation study."""
    print("Starting GTE Feature Ablation Study...")
    
    # Initialize study
    study = GTEAblationStudy()
    
    # Run ablation study
    results = study.run_ablation_study()
    
    print("\nAblation study completed successfully!")
    print("Results saved to 'ablation_study_results.png'")

if __name__ == "__main__":
    main()
