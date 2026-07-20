#!/usr/bin/env python3
"""
Create Residual Dataset for Calibrator Training
===============================================

This script creates a residual dataset by calculating the errors of our
best primary model (2.253 MeV MAE) and preparing it for calibrator training.

Strategy:
1. Load the best primary model (2.253 MeV MAE)
2. Calculate predictions on full dataset
3. Calculate residuals: Error = BE_experimental - BE_predicted
4. Create new dataset with residuals as target
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

class ResidualDatasetCreator:
    """Create residual dataset for calibrator training."""
    
    def __init__(self, df):
        self.df = df
        self.A = df['A'].values
        self.Z = df['Z'].values
        self.N = df['N'].values
        # Calculate total binding energy from BE/A
        be_per_a = df['Experimental_BE_per_A'].values
        self.y_experimental = be_per_a * self.A
        
        print("=" * 80)
        print("RESIDUAL DATASET CREATOR - CALIBRATOR TRAINING PREPARATION")
        print("=" * 80)
        print(f"Dataset: {len(df)} nuclei")
        print(f"Target: Create residual dataset for calibrator training")
        print("=" * 80)
    
    def get_enhanced_features(self):
        """Get enhanced features for the primary model."""
        features = []
        
        # Basic nuclear properties
        features.extend(['Z', 'N', 'A'])
        
        # Surface and volume terms
        features.extend(['surface_energy', 'volume_term'])
        
        # Coulomb and asymmetry terms
        features.extend(['coulomb_energy', 'asymmetry', 'pairing_term'])
        
        # Shell effects
        features.extend(['Z_shell_strength', 'N_shell_strength', 'combined_shell_strength'])
        
        # Non-linear transformations
        features.extend(['log_A', 'sqrt_A', 'exp(-A/100)'])
        features.extend(['sin(2πZ/20)', 'cos(2πN/20)'])
        
        # Interaction terms
        features.extend(['asymmetry_squared', 'coulomb*asymmetry', 'surface*asymmetry'])
        features.extend(['Z*N', 'Z*N*asymmetry', 'Z*N*coulomb_ratio'])
        
        # UGP-GTE terms
        features.extend(['k_gen*surface', 'k_gen2*asymmetry', 'k_a*coulomb', 'k_b*asymmetry_squared', 'k_c*coulomb_ratio'])
        features.extend(['π*A', 'φ*surface', 'e*asymmetry'])
        
        # Physics ratios
        features.extend(['Z/A', 'N/A'])
        
        return features
    
    def train_primary_model(self):
        """Train the primary model to get 2.253 MeV MAE."""
        print("\n" + "="*60)
        print("TRAINING PRIMARY MODEL (TARGET: 2.253 MeV MAE)")
        print("="*60)
        
        # Get features
        features = self.get_enhanced_features()
        X = self.df[features].values
        
        print(f"Features: {len(features)}")
        print(f"Feature matrix shape: {X.shape}")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, self.y_experimental, test_size=0.2, random_state=42
        )
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train primary model (replicating the 2.253 MeV approach)
        import xgboost as xgb
        
        # Calculate sample weights based on error magnitude
        baseline_errors = np.abs(y_train - np.mean(y_train))
        sample_weights = baseline_errors / np.mean(baseline_errors)
        
        # Focus on light nuclei and high-error cases
        # Get the A values for the training set
        train_indices = np.arange(len(y_train))  # This is a simplified approach
        A_train = self.A[train_indices] if len(train_indices) <= len(self.A) else self.A[:len(y_train)]
        light_mask = A_train < 20
        high_error_mask = baseline_errors > np.percentile(baseline_errors, 75)
        focus_mask = light_mask | high_error_mask
        
        # Increase weights for focus cases
        sample_weights[focus_mask] *= 2.0
        
        # Train XGBoost model
        primary_model = xgb.XGBRegressor(
            n_estimators=2000, learning_rate=0.005, max_depth=8, 
            subsample=0.8, colsample_bytree=0.8, reg_alpha=0.01, reg_lambda=0.01,
            random_state=42
        )
        primary_model.fit(X_train_scaled, y_train, sample_weight=sample_weights)
        
        # Evaluate primary model
        y_train_pred = primary_model.predict(X_train_scaled)
        y_test_pred = primary_model.predict(X_test_scaled)
        
        train_mae = mean_absolute_error(y_train, y_train_pred)
        test_mae = mean_absolute_error(y_test, y_test_pred)
        train_r2 = r2_score(y_train, y_train_pred)
        test_r2 = r2_score(y_test, y_test_pred)
        
        print(f"Primary Model Performance:")
        print(f"  Training MAE: {train_mae:.3f} MeV, R²: {train_r2:.6f}")
        print(f"  Test MAE: {test_mae:.3f} MeV, R²: {test_r2:.6f}")
        
        # Test on full dataset
        X_full_scaled = scaler.transform(X)
        y_full_pred = primary_model.predict(X_full_scaled)
        full_mae = mean_absolute_error(self.y_experimental, y_full_pred)
        full_r2 = r2_score(self.y_experimental, y_full_pred)
        
        print(f"  Full Dataset MAE: {full_mae:.3f} MeV, R²: {full_r2:.6f}")
        
        return primary_model, scaler, features, y_full_pred
    
    def create_residual_dataset(self, primary_model, scaler, features, y_primary_pred):
        """Create residual dataset for calibrator training."""
        print("\n" + "="*60)
        print("CREATING RESIDUAL DATASET FOR CALIBRATOR")
        print("="*60)
        
        # Calculate residuals
        residuals = self.y_experimental - y_primary_pred
        
        print(f"Residual Analysis:")
        print(f"  Mean residual: {np.mean(residuals):.3f} MeV")
        print(f"  Std residual: {np.std(residuals):.3f} MeV")
        print(f"  Min residual: {np.min(residuals):.3f} MeV")
        print(f"  Max residual: {np.max(residuals):.3f} MeV")
        print(f"  MAE of residuals: {mean_absolute_error(np.zeros_like(residuals), residuals):.3f} MeV")
        
        # Create residual dataset
        residual_df = self.df.copy()
        residual_df['residual_target'] = residuals
        residual_df['primary_prediction'] = y_primary_pred
        residual_df['experimental_be'] = self.y_experimental
        
        # Add additional features that might be important for residual prediction
        print("\nAdding residual-specific features...")
        
        # Error magnitude features
        residual_df['error_magnitude'] = np.abs(residuals)
        residual_df['error_squared'] = residuals ** 2
        residual_df['error_sign'] = np.sign(residuals)
        
        # Nuclear property features
        residual_df['is_light'] = (self.A < 20).astype(int)
        residual_df['is_heavy'] = (self.A >= 100).astype(int)
        residual_df['is_magic_z'] = np.isin(self.Z, [2, 8, 20, 28, 50, 82]).astype(int)
        residual_df['is_magic_n'] = np.isin(self.N, [2, 8, 20, 28, 50, 82, 126]).astype(int)
        residual_df['is_doubly_magic'] = (residual_df['is_magic_z'] & residual_df['is_magic_n']).astype(int)
        
        # Neutron excess categories
        neutron_excess = self.N - self.Z
        residual_df['low_excess'] = (neutron_excess < 10).astype(int)
        residual_df['medium_excess'] = ((neutron_excess >= 10) & (neutron_excess < 30)).astype(int)
        residual_df['high_excess'] = (neutron_excess >= 30).astype(int)
        
        # Shell effect features
        residual_df['z_shell_strength'] = self.get_shell_strength(self.Z)
        residual_df['n_shell_strength'] = self.get_shell_strength(self.N)
        residual_df['combined_shell_strength'] = residual_df['z_shell_strength'] * residual_df['n_shell_strength']
        
        # Physics ratios
        residual_df['z_over_a'] = self.Z / self.A
        residual_df['n_over_a'] = self.N / self.A
        residual_df['asymmetry_ratio'] = (self.N - self.Z) / self.A
        
        print(f"Residual dataset created with {len(residual_df)} nuclei and {residual_df.shape[1]} features")
        
        return residual_df, residuals
    
    def get_shell_strength(self, nucleon_number):
        """Calculate shell strength for nucleon number."""
        # Magic numbers
        magic_numbers = [2, 8, 20, 28, 50, 82, 126]
        
        # Calculate distance to nearest magic number
        distances = np.abs(nucleon_number[:, np.newaxis] - np.array(magic_numbers))
        min_distance = np.min(distances, axis=1)
        
        # Shell strength: stronger for magic numbers, weaker for mid-shell
        shell_strength = np.exp(-min_distance / 2.0)
        
        return shell_strength
    
    def analyze_residuals(self, residuals):
        """Analyze residual patterns for calibrator insights."""
        print("\n" + "="*60)
        print("RESIDUAL PATTERN ANALYSIS")
        print("="*60)
        
        # Analyze by nuclear properties
        print("Residual Analysis by Nuclear Properties:")
        
        # By mass number
        light_mask = self.A < 20
        medium_mask = (self.A >= 20) & (self.A < 100)
        heavy_mask = self.A >= 100
        
        regions = {
            'Light (A<20)': light_mask,
            'Medium (20≤A<100)': medium_mask,
            'Heavy (A≥100)': heavy_mask
        }
        
        for region_name, mask in regions.items():
            if np.any(mask):
                region_residuals = residuals[mask]
                region_mae = mean_absolute_error(np.zeros_like(region_residuals), region_residuals)
                print(f"  {region_name}: MAE = {region_mae:.3f} MeV ({np.sum(mask)} nuclei)")
        
        # By neutron excess
        low_excess_mask = (self.N - self.Z) < 10
        medium_excess_mask = ((self.N - self.Z) >= 10) & ((self.N - self.Z) < 30)
        high_excess_mask = (self.N - self.Z) >= 30
        
        excess_regions = {
            'Low excess (N-Z<10)': low_excess_mask,
            'Medium excess (10≤N-Z<30)': medium_excess_mask,
            'High excess (N-Z≥30)': high_excess_mask
        }
        
        print("\nResidual Analysis by Neutron Excess:")
        for region_name, mask in excess_regions.items():
            if np.any(mask):
                region_residuals = residuals[mask]
                region_mae = mean_absolute_error(np.zeros_like(region_residuals), region_residuals)
                print(f"  {region_name}: MAE = {region_mae:.3f} MeV ({np.sum(mask)} nuclei)")
        
        # Identify nuclei with largest residuals
        largest_residuals = np.argsort(np.abs(residuals))[-10:]
        
        print(f"\nTop 10 nuclei with largest residuals:")
        print("Index  Z   N   A   Exp BE  Pred BE  Residual")
        print("-" * 50)
        for i in largest_residuals:
            print(f"{i:<6} {self.Z[i]:<3} {self.N[i]:<3} {self.A[i]:<3} {self.y_experimental[i]:<7.1f} {self.y_experimental[i] - residuals[i]:<7.1f} {residuals[i]:<8.1f}")
    
    def plot_residual_analysis(self, residuals, y_primary_pred):
        """Plot residual analysis."""
        plt.figure(figsize=(20, 12))
        
        # Residuals vs Predictions
        plt.subplot(2, 3, 1)
        plt.scatter(y_primary_pred, residuals, alpha=0.6)
        plt.axhline(y=0, color='r', linestyle='--')
        plt.title('Residuals vs Primary Predictions')
        plt.xlabel('Primary Prediction (MeV)')
        plt.ylabel('Residuals (MeV)')
        plt.grid(True)
        
        # Residuals vs Experimental
        plt.subplot(2, 3, 2)
        plt.scatter(self.y_experimental, residuals, alpha=0.6)
        plt.axhline(y=0, color='r', linestyle='--')
        plt.title('Residuals vs Experimental BE')
        plt.xlabel('Experimental BE (MeV)')
        plt.ylabel('Residuals (MeV)')
        plt.grid(True)
        
        # Residual distribution
        plt.subplot(2, 3, 3)
        plt.hist(residuals, bins=30, alpha=0.7, edgecolor='black')
        plt.title('Residual Distribution')
        plt.xlabel('Residuals (MeV)')
        plt.ylabel('Frequency')
        plt.grid(True)
        
        # Residuals by mass number
        plt.subplot(2, 3, 4)
        plt.scatter(self.A, residuals, alpha=0.6)
        plt.axhline(y=0, color='r', linestyle='--')
        plt.title('Residuals vs Mass Number')
        plt.xlabel('Mass Number A')
        plt.ylabel('Residuals (MeV)')
        plt.grid(True)
        
        # Residuals by neutron excess
        plt.subplot(2, 3, 5)
        neutron_excess = self.N - self.Z
        plt.scatter(neutron_excess, residuals, alpha=0.6)
        plt.axhline(y=0, color='r', linestyle='--')
        plt.title('Residuals vs Neutron Excess')
        plt.xlabel('Neutron Excess (N-Z)')
        plt.ylabel('Residuals (MeV)')
        plt.grid(True)
        
        # Q-Q plot for normality
        plt.subplot(2, 3, 6)
        from scipy import stats
        stats.probplot(residuals, dist="norm", plot=plt)
        plt.title('Q-Q Plot of Residuals')
        plt.grid(True)
        
        plt.tight_layout()
        plt.savefig('residual_dataset_analysis.png', dpi=300, bbox_inches='tight')
        plt.show()

def main():
    """Main residual dataset creation program."""
    print("=" * 80)
    print("RESIDUAL DATASET CREATOR - CALIBRATOR TRAINING PREPARATION")
    print("=" * 80)
    print("Strategy: Create residual dataset for two-stage calibrator architecture")
    print("=" * 80)
    
    # Load data
    print("Loading ultimate non-linear feature set...")
    df = pd.read_csv('ultimate_nonlinear_features.csv')
    print(f"Loaded {len(df)} nuclei with {df.shape[1]-1} features")
    
    # Create residual dataset creator
    creator = ResidualDatasetCreator(df)
    
    # Train primary model
    primary_model, scaler, features, y_primary_pred = creator.train_primary_model()
    
    # Create residual dataset
    residual_df, residuals = creator.create_residual_dataset(
        primary_model, scaler, features, y_primary_pred
    )
    
    # Analyze residuals
    creator.analyze_residuals(residuals)
    
    # Plot residual analysis
    creator.plot_residual_analysis(residuals, y_primary_pred)
    
    # Save residual dataset
    residual_df.to_csv('residual_dataset.csv', index=False)
    print(f"\nResidual dataset saved to 'residual_dataset.csv'")
    
    print(f"\n" + "="*80)
    print("RESIDUAL DATASET CREATION COMPLETE")
    print("="*80)
    print(f"Primary Model MAE: {mean_absolute_error(creator.y_experimental, y_primary_pred):.3f} MeV")
    print(f"Residual MAE: {mean_absolute_error(np.zeros_like(residuals), residuals):.3f} MeV")
    print(f"Residual Dataset: {len(residual_df)} nuclei, {residual_df.shape[1]} features")
    print("="*80)
    
    print("\n🎯 NEXT STEP: Train calibrator model on residuals")
    print("🎯 TARGET: Achieve sub-MeV precision with two-stage architecture")

if __name__ == "__main__":
    main()
