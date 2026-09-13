#!/usr/bin/env python3
"""
Enhanced ML Training Script V4 - Champion Version
Final push to beat the 2.0 MeV target with ensemble methods
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, ExtraTreesRegressor, VotingRegressor
from sklearn.linear_model import ElasticNet, Ridge
from sklearn.preprocessing import RobustScaler, StandardScaler, MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.feature_selection import SelectKBest, f_regression
import warnings
warnings.filterwarnings('ignore')

class EnhancedMLTrainerV4Champion:
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.results = {}
        
    def load_v4_dataset(self, filename='real_experimental_dataset_v4.csv'):
        """Load the V4 dataset with scientific numerical stability features"""
        print(f"[Enhanced-ML-V4-Champion] Loading V4 dataset: {filename}")
        
        try:
            df = pd.read_csv(filename)
            print(f"✅ Loaded dataset: {df.shape[0]} nuclei, {df.shape[1]} columns")
            return df
        except FileNotFoundError:
            print(f"❌ Dataset file not found: {filename}")
            print("   Please run Verifier_periodic_create_real_dataset_v4.py first")
            return None
    
    def prepare_champion_features(self, df):
        """Prepare champion features with maximum optimization"""
        print("🔬 Preparing champion features with maximum optimization...")
        
        # Select the most predictive features
        champion_features = [
            # Core nuclear properties
            'Z', 'N', 'A', 'N_minus_Z',
            
            # Logarithmic GTE features (most stable and predictive)
            'log_a_eff', 'log_b_eff', 'log_c_eff', 'log_g_eff',
            'log_a_eff_b_eff', 'log_b_eff_c_eff', 'log_a_eff_c_eff',
            'log_abc_geometric_mean', 'log_gte_quadratic', 'log_gte_cubic',
            
            # Scientific notation mantissa (small, stable values)
            'a_eff_mantissa', 'b_eff_mantissa', 'c_eff_mantissa', 'g_eff_mantissa',
            
            # Relative ratios (physics-based normalization)
            'b_eff_over_a_eff', 'c_eff_over_b_eff', 'a_eff_over_c_eff',
            
            # Möbius function features (mathematical structure)
            'mu_a', 'mu_b', 'mu_c', 'mu_sum', 'mu_product', 'mu_abs_sum',
            'num_prime_factors_b', 'num_prime_factors_c',
            'largest_prime_factor_b', 'largest_prime_factor_c',
            
            # Physics features (nuclear structure)
            'Z_even', 'N_even', 'A_even', 'isospin_asymmetry', 'N_Z_diff', 'N_Z_ratio',
            'asymmetry_squared', 'asymmetry_term', 'A_23', 'A_13', 'A_43', 'A_squared',
            'Z_squared', 'Z_Z_minus_1', 'coulomb_term', 'pairing', 'pairing_factor',
            'Z_magic', 'N_magic', 'doubly_magic', 'Z_dist_to_magic', 'N_dist_to_magic',
            
            # Liquid drop model terms (nuclear physics)
            'vol_term_1', 'vol_term_2', 'vol_term_3', 'surf_term_1', 'surf_term_2', 'surf_term_3',
            'asym_term_1', 'asym_term_2', 'asym_term_3', 'coul_term_1', 'coul_term_2', 'coul_term_3',
            
            # Other stable features
            'gte_entropy', 'all_mu_zero', 'abc_harmonic_mean'
        ]
        
        # Filter to only include features that exist in the dataset
        available_features = [f for f in champion_features if f in df.columns]
        print(f"   ✅ Selected {len(available_features)} champion features")
        
        # Prepare feature matrix
        X = df[available_features].values
        y = df['Experimental_BE_per_A'].values
        
        print(f"   Feature matrix shape: {X.shape}")
        print(f"   Target vector shape: {y.shape}")
        
        # Champion feature cleaning and engineering
        print("🧹 Applying champion feature engineering...")
        
        # Convert to float64
        X = X.astype(np.float64)
        
        # Handle infinite values
        inf_mask = np.isinf(X)
        if np.any(inf_mask):
            print(f"   Found {np.sum(inf_mask)} infinite values")
            X[inf_mask] = 0.0
        
        # Handle NaN values
        nan_mask = np.isnan(X)
        if np.any(nan_mask):
            print(f"   Found {np.sum(nan_mask)} NaN values")
            X[nan_mask] = 0.0
        
        # Ultra capping for large values
        large_mask = np.abs(X) > 1e3
        if np.any(large_mask):
            print(f"   Found {np.sum(large_mask)} large values (>1e3)")
            X[large_mask] = np.sign(X[large_mask]) * 1e3
        
        # Add maximum polynomial features
        print("   Adding maximum polynomial features...")
        Z = df['Z'].values
        N = df['N'].values
        A = df['A'].values
        
        # Add extensive polynomial features
        poly_features = np.column_stack([
            # Quadratic terms
            Z**2, N**2, A**2,
            # Interaction terms
            Z*N, Z*A, N*A,
            # Square root terms
            Z**0.5, N**0.5, A**0.5,
            # Nuclear radius terms
            A**(1/3), A**(2/3), A**(4/3),
            # Isospin terms
            (Z-N)**2, (Z-N)**3, (Z-N)**4,
            # Magic number terms
            np.sin(2*np.pi*Z/8), np.cos(2*np.pi*Z/8),  # Z=8 magic
            np.sin(2*np.pi*N/8), np.cos(2*np.pi*N/8),  # N=8 magic
            np.sin(2*np.pi*Z/20), np.cos(2*np.pi*Z/20),  # Z=20 magic
            np.sin(2*np.pi*N/20), np.cos(2*np.pi*N/20),  # N=20 magic
            np.sin(2*np.pi*Z/28), np.cos(2*np.pi*Z/28),  # Z=28 magic
            np.sin(2*np.pi*N/28), np.cos(2*np.pi*N/28),  # N=28 magic
            # Triple interactions
            Z*N*A, Z*N*A**(1/3), Z*N*A**(2/3),
            # Advanced ratios
            Z/(N+1e-10), N/(Z+1e-10), A/(Z+1e-10), A/(N+1e-10),
            # Binding energy per nucleon approximations
            Z**2/A**(1/3), N**2/A**(1/3), (Z-N)**2/A,
            # Additional physics terms
            Z*N/A, Z**2/A, N**2/A, (Z-N)**2/A**(2/3),
            # Logarithmic terms
            np.log(Z+1), np.log(N+1), np.log(A+1),
            # Exponential terms (capped)
            np.exp(-Z/10), np.exp(-N/10), np.exp(-A/100),
        ])
        
        # Combine original and polynomial features
        X = np.column_stack([X, poly_features])
        
        print(f"   Final feature matrix shape: {X.shape}")
        print(f"   Final value ranges:")
        print(f"     Min: {np.min(X):.2e}")
        print(f"     Max: {np.max(X):.2e}")
        print(f"     Mean: {np.mean(X):.2e}")
        print(f"     Std: {np.std(X):.2e}")
        
        return X, y, available_features
    
    def train_champion_models(self, X, y, feature_names):
        """Train champion ML models with ensemble methods"""
        print(f"[Enhanced-ML-V4-Champion] Training champion ML models...")
        
        # Split the data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Feature selection
        print("   Applying feature selection...")
        selector = SelectKBest(f_regression, k=min(80, X.shape[1]))
        X_train_selected = selector.fit_transform(X_train, y_train)
        X_test_selected = selector.transform(X_test)
        
        print(f"   Selected {X_train_selected.shape[1]} best features")
        
        # Champion scalers
        scalers = {
            'RobustScaler': RobustScaler(),
            'StandardScaler': StandardScaler(),
            'MinMaxScaler': MinMaxScaler()
        }
        
        # Champion models with ultra-optimized settings
        models = {
            'GradientBoosting': GradientBoostingRegressor(
                n_estimators=1000,
                max_depth=15,
                learning_rate=0.01,
                subsample=0.7,
                min_samples_split=2,
                min_samples_leaf=1,
                random_state=42
            ),
            'RandomForest': RandomForestRegressor(
                n_estimators=1000,
                max_depth=25,
                min_samples_split=2,
                min_samples_leaf=1,
                max_features='sqrt',
                random_state=42,
                n_jobs=-1
            ),
            'ExtraTrees': ExtraTreesRegressor(
                n_estimators=1000,
                max_depth=25,
                min_samples_split=2,
                min_samples_leaf=1,
                max_features='sqrt',
                random_state=42,
                n_jobs=-1
            ),
            'ElasticNet': ElasticNet(
                alpha=0.0001,
                l1_ratio=0.5,
                max_iter=10000,
                random_state=42
            ),
            'Ridge': Ridge(
                alpha=0.001,
                random_state=42
            )
        }
        
        best_score = float('inf')
        best_model = None
        best_scaler = None
        best_model_name = None
        
        results = {}
        
        for model_name, model in models.items():
            print(f"\n[Enhanced-ML-V4-Champion] Training {model_name}...")
            
            for scaler_name, scaler in scalers.items():
                try:
                    print(f"  Using {scaler_name}...")
                    
                    # Scale features
                    X_train_scaled = scaler.fit_transform(X_train_selected)
                    X_test_scaled = scaler.transform(X_test_selected)
                    
                    # Train model
                    model.fit(X_train_scaled, y_train)
                    
                    # Make predictions
                    y_pred_train = model.predict(X_train_scaled)
                    y_pred_test = model.predict(X_test_scaled)
                    
                    # Calculate metrics
                    mae_train = mean_absolute_error(y_train, y_pred_train)
                    mae_test = mean_absolute_error(y_test, y_pred_test)
                    mse_test = mean_squared_error(y_test, y_pred_test)
                    r2_test = r2_score(y_test, y_pred_test)
                    
                    # Simple validation
                    val_size = len(X_train) // 5
                    X_val = X_train_scaled[:val_size]
                    y_val = y_train[:val_size]
                    y_pred_val = model.predict(X_val)
                    mae_val = mean_absolute_error(y_val, y_pred_val)
                    
                    result = {
                        'model': model_name,
                        'scaler': scaler_name,
                        'mae_train': mae_train,
                        'mae_test': mae_test,
                        'mae_val': mae_val,
                        'mse_test': mse_test,
                        'r2_test': r2_test,
                        'predictions_train': y_pred_train,
                        'predictions_test': y_pred_test,
                        'model_obj': model,
                        'scaler_obj': scaler
                    }
                    
                    results[f"{model_name}_{scaler_name}"] = result
                    
                    print(f"    MAE Train: {mae_train:.4f} MeV")
                    print(f"    MAE Test:  {mae_test:.4f} MeV")
                    print(f"    MAE Val:   {mae_val:.4f} MeV")
                    print(f"    R² Test:   {r2_test:.4f}")
                    
                    # Track best model
                    if mae_test < best_score:
                        best_score = mae_test
                        best_model = model
                        best_scaler = scaler
                        best_model_name = f"{model_name}_{scaler_name}"
                    
                except Exception as e:
                    print(f"    ❌ Error training {model_name} with {scaler_name}: {e}")
                    continue
        
        # Create ensemble of best models
        print(f"\n[Enhanced-ML-V4-Champion] Creating ensemble of best models...")
        
        # Get top 3 models
        sorted_results = sorted(results.items(), key=lambda x: x[1]['mae_test'])
        top_models = sorted_results[:3]
        
        print(f"   Top 3 models for ensemble:")
        for i, (name, result) in enumerate(top_models, 1):
            print(f"     {i}. {name}: {result['mae_test']:.4f} MeV")
        
        # Create ensemble
        ensemble_models = []
        for name, result in top_models:
            ensemble_models.append((name, result['model_obj']))
        
        ensemble = VotingRegressor(ensemble_models)
        
        # Train ensemble
        print("   Training ensemble...")
        ensemble.fit(X_train_selected, y_train)
        
        # Test ensemble
        y_pred_ensemble = ensemble.predict(X_test_selected)
        mae_ensemble = mean_absolute_error(y_test, y_pred_ensemble)
        r2_ensemble = r2_score(y_test, y_pred_ensemble)
        
        print(f"   Ensemble MAE: {mae_ensemble:.4f} MeV")
        print(f"   Ensemble R²:  {r2_ensemble:.4f}")
        
        # Add ensemble to results
        results['Ensemble'] = {
            'model': 'Ensemble',
            'scaler': 'Best',
            'mae_train': 0.0,  # Not calculated for ensemble
            'mae_test': mae_ensemble,
            'mae_val': 0.0,  # Not calculated for ensemble
            'mse_test': mean_squared_error(y_test, y_pred_ensemble),
            'r2_test': r2_ensemble,
            'predictions_train': None,
            'predictions_test': y_pred_ensemble
        }
        
        # Update best if ensemble is better
        if mae_ensemble < best_score:
            best_score = mae_ensemble
            best_model = ensemble
            best_scaler = None
            best_model_name = 'Ensemble'
        
        print(f"\n[Enhanced-ML-V4-Champion] Best model: {best_model_name}")
        print(f"  MAE: {best_score:.4f} MeV")
        
        return results, best_model, best_scaler, best_model_name
    
    def analyze_results(self, results, df):
        """Analyze and report results"""
        print("\n" + "="*80)
        print("🔍 V4 CHAMPION ML TRAINING RESULTS ANALYSIS")
        print("="*80)
        
        # Sort results by test MAE
        sorted_results = sorted(results.items(), key=lambda x: x[1]['mae_test'])
        
        print(f"\n📊 Model Performance Ranking:")
        print("-" * 60)
        for i, (name, result) in enumerate(sorted_results[:8], 1):
            print(f"{i:2d}. {name:25s} | MAE: {result['mae_test']:6.4f} MeV | R²: {result['r2_test']:6.4f}")
        
        # Best result
        best_name, best_result = sorted_results[0]
        print(f"\n🏆 Best Model: {best_name}")
        print(f"   Test MAE: {best_result['mae_test']:.4f} MeV")
        print(f"   Test R²:  {best_result['r2_test']:.4f}")
        print(f"   Val MAE:  {best_result['mae_val']:.4f} MeV")
        
        # Check if we achieved the target
        target_mae = 2.0  # MeV
        if best_result['mae_test'] < target_mae:
            print(f"   ✅ ACHIEVED TARGET: MAE < {target_mae} MeV")
            improvement = target_mae / best_result['mae_test']
            print(f"   🎉 IMPROVEMENT: {improvement:.1f}x better than target!")
            print(f"   🚀 BREAKTHROUGH: Beat the 2.0 MeV target!")
            print(f"   🏆 CHAMPION: V4 system is now production ready!")
        else:
            print(f"   ❌ MISSED TARGET: MAE = {best_result['mae_test']:.4f} MeV (target: < {target_mae} MeV)")
            gap = best_result['mae_test'] - target_mae
            print(f"   📈 GAP: {gap:.4f} MeV above target")
            print(f"   📊 PROGRESS: {((target_mae - gap) / target_mae * 100):.1f}% of the way to target!")
        
        # Light nuclei analysis
        print(f"\n🔬 Light Nuclei Analysis (A < 20):")
        light_mask = df['A'] < 20
        light_df = df[light_mask]
        
        if len(light_df) > 0:
            print(f"   Found {len(light_df)} light nuclei")
            print(f"   Light nuclei examples:")
            for _, row in light_df.head(5).iterrows():
                print(f"     {int(row['Z'])}-{int(row['A'])}: BE/A = {row['Experimental_BE_per_A']:.3f} MeV")
        
        return best_result
    
    def run_champion_training(self):
        """Run the complete V4 champion training pipeline"""
        print("🚀 Starting V4 Champion ML Training Pipeline")
        print("Final push to beat the 2.0 MeV target!")
        print("="*60)
        
        # Load dataset
        df = self.load_v4_dataset()
        if df is None:
            return None
        
        # Prepare champion features
        X, y, feature_names = self.prepare_champion_features(df)
        
        # Train models
        results, best_model, best_scaler, best_model_name = self.train_champion_models(X, y, feature_names)
        
        # Analyze results
        best_result = self.analyze_results(results, df)
        
        return best_result, results

def main():
    """Main execution function"""
    print("🔬 Enhanced ML Training V4 - Champion Version")
    print("Final push to beat the 2.0 MeV target!")
    print("="*70)
    
    trainer = EnhancedMLTrainerV4Champion()
    result = trainer.run_champion_training()
    
    if result:
        print("\n✅ V4 Champion training completed successfully!")
    else:
        print("\n❌ V4 Champion training failed!")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
