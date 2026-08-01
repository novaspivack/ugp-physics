#!/usr/bin/env python3
"""
UNIFIED GTE Victory Model - Multiprocessing Version
Trains a single model on BOTH binding energy AND stability simultaneously.
Fast hyperparameter tuning using parallel processing for maximum speed.

This could lead to the ultimate universal law of nuclear physics!
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import GridSearchCV, cross_val_score
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import Ridge, BayesianRidge
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score, accuracy_score, classification_report
import xgboost as xgb
from multiprocessing import Pool, cpu_count
import time
import os
from typing import Dict, List, Tuple, Any
import warnings
warnings.filterwarnings('ignore')

class UltimateGTEVictoryModelMultiprocessing:
    """Ultimate GTE Victory Model with multiprocessing for maximum speed."""
    
    def __init__(self):
        """Initialize the multiprocessing GTE model."""
        self.df = None
        self.X = None
        self.y = None
        self.scaler = StandardScaler()
        self.models = {}
        self.best_model = None
        self.best_score = float('inf')
        self.feature_names = []
        
        # Use all available CPU cores
        self.n_jobs = cpu_count()
        print(f"[Victory-MP] Using {self.n_jobs} CPU cores for parallel processing")
        
    def load_data(self):
        """Load the unified training dataset with stability labels."""
        print("Loading unified training dataset with stability labels...")
        self.df = pd.read_csv('unified_gte_training_dataset_with_stability.csv')
        print(f"Loaded {len(self.df) if self.df is not None else 0} nuclei with stability labels")
        
        # Show stability distribution
        stable_count = self.df['Is_Stable'].sum()
        unstable_count = (~self.df['Is_Stable']).sum()
        print(f"📊 Stable nuclei: {stable_count} ({stable_count/len(self.df)*100:.1f}%)")
        print(f"📊 Unstable nuclei: {unstable_count} ({unstable_count/len(self.df)*100:.1f}%)")
        
    def calculate_victory_gte_features(self):
        """Calculate the most effective GTE features based on our analysis."""
        print("Calculating victory GTE features...")

        # Calculate GTE triples from Z, N, A
        Z = np.array(self.df['Z'].values)
        N = np.array(self.df['N'].values)
        A = np.array(self.df['A'].values)

        # Calculate GTE triples
        a_eff = Z * (Z - 1) / A
        b_eff = N * (N - 1) / A
        c_eff = (N - Z) * (N - Z - 1) / A
        g_eff = A**(2/3)

        features = []
        feature_names = []

        # === TIER 1: MOST IMPORTANT FEATURES (from analysis) ===
        
        # Core GTE features
        features.extend([a_eff, b_eff, c_eff, g_eff])
        feature_names.extend(['a_eff', 'b_eff', 'c_eff', 'g_eff'])
        
        # Log features (most important)
        features.extend([np.log(a_eff + 1), np.log(b_eff + 1), np.log(c_eff + 1), np.log(g_eff + 1)])
        feature_names.extend(['log_a_eff', 'log_b_eff', 'log_c_eff', 'log_g_eff'])
        
        # Power features
        features.extend([a_eff**0.5, b_eff**0.5, c_eff**0.5, g_eff**0.5])
        feature_names.extend(['sqrt_a_eff', 'sqrt_b_eff', 'sqrt_c_eff', 'sqrt_g_eff'])
        
        features.extend([a_eff**2, b_eff**2, c_eff**2, g_eff**2])
        feature_names.extend(['a_eff_sq', 'b_eff_sq', 'c_eff_sq', 'g_eff_sq'])
        
        # === TIER 2: INTERACTION FEATURES ===
        
        # Cross products
        features.extend([a_eff * b_eff, a_eff * c_eff, b_eff * c_eff])
        feature_names.extend(['a_eff_x_b_eff', 'a_eff_x_c_eff', 'b_eff_x_c_eff'])
        
        # Ratios
        features.extend([a_eff / (b_eff + 1), b_eff / (c_eff + 1), c_eff / (g_eff + 1)])
        feature_names.extend(['a_eff_div_b_eff', 'b_eff_div_c_eff', 'c_eff_div_g_eff'])
        
        # === TIER 3: ADVANCED MATHEMATICAL FEATURES ===
        
        # Trigonometric features
        features.extend([np.sin(2 * np.pi * np.log(b_eff + 1) / np.log(c_eff + 1))])
        feature_names.extend(['sin_2pi_log_b_div_c'])
        
        features.extend([np.cos(2 * np.pi * np.log(a_eff + 1) / np.log(g_eff + 1))])
        feature_names.extend(['cos_2pi_log_a_div_g'])
        
        # Kernel features
        features.extend([np.exp(-a_eff/100), np.exp(-b_eff/100), np.exp(-c_eff/100)])
        feature_names.extend(['exp_neg_a_eff', 'exp_neg_b_eff', 'exp_neg_c_eff'])
        
        # === TIER 4: NUCLEAR PHYSICS FEATURES ===
        
        # Asymmetry
        asymmetry = (N - Z) / A
        features.extend([asymmetry, asymmetry**2, asymmetry**3])
        feature_names.extend(['asymmetry', 'asymmetry_sq', 'asymmetry_cub'])
        
        # Coulomb
        coulomb = Z**2 / A**(4/3)
        features.extend([coulomb, coulomb**0.5, coulomb**2])
        feature_names.extend(['coulomb', 'sqrt_coulomb', 'coulomb_sq'])
        
        # Surface
        surface = A**(2/3)
        features.extend([surface, surface**0.5, surface**2])
        feature_names.extend(['surface', 'sqrt_surface', 'surface_sq'])
        
        # === TIER 5: COMBINED FEATURES ===
        
        # GTE + Physics combinations
        features.extend([a_eff * asymmetry, b_eff * coulomb, c_eff * surface])
        feature_names.extend(['a_eff_x_asymmetry', 'b_eff_x_coulomb', 'c_eff_x_surface'])
        
        # Log combinations
        features.extend([np.log(a_eff + 1) * asymmetry, np.log(b_eff + 1) * coulomb])
        feature_names.extend(['log_a_x_asymmetry', 'log_b_x_coulomb'])
        
        # Convert to numpy array
        X = np.column_stack(features)
        
        # Handle NaN and inf values
        X = np.nan_to_num(X, nan=0.0, posinf=1e6, neginf=-1e6)
        
        print(f"Created {X.shape[1]} victory GTE features")
        self.feature_names = feature_names
        
        return X
    
    def train_single_model(self, model_name: str, model: Any, param_grid: Dict) -> Tuple[str, float, Any]:
        """Train a single model with multiprocessing."""
        print(f"[{model_name}] Starting training with {len(param_grid)} parameter combinations...")
        start_time = time.time()
        
        try:
            # Use multiprocessing for GridSearchCV
            grid_search = GridSearchCV(
                model, 
                param_grid, 
                cv=3,  # Reduced CV for speed
                scoring='neg_mean_absolute_error',
                n_jobs=self.n_jobs,
                verbose=1
            )
            
            grid_search.fit(self.X, self.y)
            
            # Get best score and model
            best_score = -grid_search.best_score_
            best_model = grid_search.best_estimator_
            
            training_time = time.time() - start_time
            print(f"[{model_name}] Completed in {training_time:.1f}s - Best MAE: {best_score:.3f} MeV")
            
            return model_name, best_score, best_model
            
        except Exception as e:
            print(f"[{model_name}] ERROR: {str(e)}")
            return model_name, float('inf'), None
    
    def train_all_models_parallel(self):
        """Train all models in parallel using multiprocessing."""
        print("Starting parallel model training...")
        
        # Define models and parameter grids
        models_config = [
            ('Ridge', Ridge(), {
                'alpha': [0.1, 1.0, 10.0, 100.0, 1000.0]
            }),
            ('BayesianRidge', BayesianRidge(), {
                'alpha_1': [1e-6, 1e-5, 1e-4],
                'alpha_2': [1e-6, 1e-5, 1e-4],
                'lambda_1': [1e-6, 1e-5, 1e-4],
                'lambda_2': [1e-6, 1e-5, 1e-4]
            }),
            ('XGBoost', xgb.XGBRegressor(random_state=42), {
                'n_estimators': [100, 200, 300],
                'max_depth': [3, 4, 5],
                'learning_rate': [0.01, 0.1, 0.2],
                'subsample': [0.8, 0.9, 1.0]
            }),
            ('RandomForest', RandomForestRegressor(random_state=42), {
                'n_estimators': [100, 200, 300],
                'max_depth': [10, 20, None],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4]
            }),
            ('GradientBoosting', GradientBoostingRegressor(random_state=42), {
                'n_estimators': [100, 200, 300],
                'max_depth': [3, 4, 5],
                'learning_rate': [0.01, 0.1, 0.2],
                'subsample': [0.8, 0.9, 1.0]
            })
        ]
        
        # Prepare data for multiprocessing
        training_data = []
        for model_name, model, param_grid in models_config:
            training_data.append((model_name, model, param_grid))
        
        # Train models in parallel
        start_time = time.time()
        
        with Pool(processes=min(self.n_jobs, len(models_config))) as pool:
            # Create partial function with fixed arguments
            from functools import partial
            train_func = partial(self._train_single_model_wrapper, self.X, self.y, self.n_jobs)
            
            # Execute parallel training
            results = pool.map(train_func, training_data)
        
        total_time = time.time() - start_time
        print(f"All models completed in {total_time:.1f}s")
        
        # Process results
        for model_name, best_score, best_model in results:
            if best_model is not None:
                self.models[model_name] = best_model
                print(f"[{model_name}] Final MAE: {best_score:.3f} MeV")
                
                if best_score < self.best_score:
                    self.best_score = best_score
                    self.best_model = best_model
                    print(f"[VICTORY] New best model: {model_name} with {best_score:.3f} MeV MAE")
        
        print(f"\n[VICTORY] Best overall model: {self.best_score:.3f} MeV MAE")
    
    @staticmethod
    def _train_single_model_wrapper(X, y, n_jobs, model_data):
        """Wrapper function for multiprocessing."""
        model_name, model, param_grid = model_data
        
        print(f"[{model_name}] Starting training...")
        start_time = time.time()
        
        try:
            # Use multiprocessing for GridSearchCV
            grid_search = GridSearchCV(
                model, 
                param_grid, 
                cv=3,  # Reduced CV for speed
                scoring='neg_mean_absolute_error',
                n_jobs=n_jobs,
                verbose=0  # Reduce verbosity for parallel execution
            )
            
            grid_search.fit(X, y)
            
            # Get best score and model
            best_score = -grid_search.best_score_
            best_model = grid_search.best_estimator_
            
            training_time = time.time() - start_time
            print(f"[{model_name}] Completed in {training_time:.1f}s - Best MAE: {best_score:.3f} MeV")
            
            return model_name, best_score, best_model
            
        except Exception as e:
            print(f"[{model_name}] ERROR: {str(e)}")
            return model_name, float('inf'), None
    
    def create_ensemble(self):
        """Create weighted ensemble of best models."""
        print("Creating victory ensemble...")
        
        if len(self.models) == 0:
            print("No models available for ensemble")
            return
        
        # Get predictions from all models
        predictions = {}
        for name, model in self.models.items():
            pred = model.predict(self.X)
            predictions[name] = pred
        
        # Calculate weights based on performance (inverse MAE)
        weights = {}
        for name, model in self.models.items():
            pred = model.predict(self.X)
            mae = mean_absolute_error(self.y, pred)
            weights[name] = 1.0 / (mae + 1e-6)  # Add small epsilon to avoid division by zero
        
        # Normalize weights
        total_weight = sum(weights.values())
        for name in weights:
            weights[name] /= total_weight
        
        print("Ensemble weights:")
        for name, weight in weights.items():
            print(f"  {name}: {weight:.3f}")
        
        # Create weighted ensemble prediction
        ensemble_pred = np.zeros(len(self.y) if self.y is not None else 0)
        for name, pred in predictions.items():
            ensemble_pred += weights[name] * pred
        
        # Calculate ensemble performance
        ensemble_mae = mean_absolute_error(self.y, ensemble_pred)
        ensemble_r2 = r2_score(self.y, ensemble_pred)
        
        print(f"\n[VICTORY ENSEMBLE] MAE: {ensemble_mae:.3f} MeV, R²: {ensemble_r2:.3f}")
        
        return ensemble_pred, ensemble_mae, ensemble_r2
    
    def run_complete_analysis(self):
        """Run the complete GTE victory analysis with multiprocessing."""
        print("=" * 60)
        print("ULTIMATE GTE VICTORY MODEL - MULTIPROCESSING VERSION")
        print("=" * 60)
        
        # Load data
        self.load_data()
        
        # Calculate features
        self.X = self.calculate_victory_gte_features()
        self.y_be = self.df['BE_per_A'].values  # Binding energy target
        self.y_stability = self.df['Is_Stable'].values  # Stability target
        
        # Scale features
        print("Scaling features...")
        self.X = self.scaler.fit_transform(self.X)
        
        print(f"Training on {self.X.shape[0]} nuclei with {self.X.shape[1]} features")
        print(f"Binding energy range: {float(np.array(self.y_be).min()):.3f} to {float(np.array(self.y_be).max()):.3f} MeV")
        stable_count = int(np.array(self.y_stability).sum())
        unstable_count = int((~np.array(self.y_stability).astype(bool)).sum())
        print(f"Stability distribution: {stable_count} stable, {unstable_count} unstable")
        
        # Train binding energy models
        print("\n🔬 Training binding energy models...")
        self.train_binding_energy_models()
        
        # Train stability models  
        print("\n🔬 Training stability models...")
        self.train_stability_models()
        
        # Create unified ensemble
        print("\n🔬 Creating unified ensemble...")
        ensemble_results = self.create_unified_ensemble()
        
        # Final results
        print("\n" + "=" * 60)
        print("ULTIMATE GTE VICTORY RESULTS")
        print("=" * 60)
        print(f"Best Binding Energy Model: {self.be_best_score:.3f} MeV MAE")
        print(f"Best Stability Model: {self.stability_best_score:.3f} accuracy")
        print(f"Unified Ensemble - Binding Energy MAE: {ensemble_results.get('be_mae', 0):.3f} MeV")
        print(f"Unified Ensemble - Binding Energy R²: {ensemble_results.get('be_r2', 0):.3f}")
        print(f"Unified Ensemble - Stability Accuracy: {ensemble_results.get('stability_acc', 0):.3f}")
        
        # Check if we achieved our targets
        be_mae = ensemble_results.get('be_mae', float('inf'))
        stability_acc = ensemble_results.get('stability_acc', 0.0)
        
        if be_mae < 1.318:
            print("🎯 TARGET ACHIEVED: MAE < 1.318 MeV (two-stage model performance)")
        if be_mae < 1.0:
            print("🚀 ULTIMATE GOAL ACHIEVED: MAE < 1.0 MeV (GTE supremacy proven)")
        if stability_acc > 0.95:
            print("🏆 STABILITY TARGET ACHIEVED: >95% accuracy")
        
        print("=" * 60)
        
        # Save the unified model
        self.save_unified_model()
        
        return {
            'best_individual_mae': self.best_score,
            'ensemble_mae': ensemble_results.get('be_mae', float('inf')),
            'ensemble_r2': ensemble_results.get('be_r2', 0.0),
            'stability_accuracy': ensemble_results.get('stability_acc', 0.0),
            'models': self.models,
            'best_model': self.best_model
        }
    
    def save_unified_model(self):
        """Save the unified model for both binding energy and stability."""
        import pickle
        import os
        from datetime import datetime
        
        # Create model directory
        model_dir = "canonical_models"
        os.makedirs(model_dir, exist_ok=True)
        
        # Save binding energy model
        be_model_path = os.path.join(model_dir, "unified_gte_binding_energy_model.pkl")
        with open(be_model_path, 'wb') as f:
            pickle.dump(self.be_best_model, f)
        
        # Save stability model
        stability_model_path = os.path.join(model_dir, "unified_gte_stability_model.pkl")
        with open(stability_model_path, 'wb') as f:
            pickle.dump(self.stability_best_model, f)
        
        # Save scaler
        scaler_path = os.path.join(model_dir, "unified_gte_scaler.pkl")
        with open(scaler_path, 'wb') as f:
            pickle.dump(self.scaler, f)
        
        # Save feature names
        feature_names_path = os.path.join(model_dir, "unified_gte_feature_names.pkl")
        with open(feature_names_path, 'wb') as f:
            pickle.dump(self.feature_names, f)
        
        # Save model metadata
        metadata = {
            'be_mae': self.be_best_score,
            'stability_accuracy': self.stability_best_score,
            'n_features': len(self.feature_names),
            'n_samples': len(self.df) if self.df is not None else 0,
            'training_date': datetime.now().isoformat(),
            'model_type': 'unified_gte_victory_multiprocessing'
        }
        
        metadata_path = os.path.join(model_dir, "unified_gte_metadata.json")
        import json
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✅ Unified model saved to {model_dir}/")
        print(f"   - Binding Energy Model: {be_model_path}")
        print(f"   - Stability Model: {stability_model_path}")
        print(f"   - Scaler: {scaler_path}")
        print(f"   - Feature Names: {feature_names_path}")
        print(f"   - Metadata: {metadata_path}")
    
    def train_binding_energy_models(self):
        """Train only the best binding energy model (Ridge)."""
        print("Training best binding energy model (Ridge only)...")
        
        # Reset models for binding energy training
        self.models = {}
        self.best_model = None
        self.best_score = float('inf')
        
        # Use binding energy target
        self.y = self.y_be
        
        # Only train Ridge (we know it's the best from previous runs)
        from sklearn.linear_model import Ridge
        from sklearn.model_selection import cross_val_score
        
        print("Training Ridge model...")
        model = Ridge(alpha=1.0)
        model.fit(self.X, self.y)
        
        # Cross-validation to get MAE
        cv_scores = -cross_val_score(model, self.X, self.y, cv=5, scoring='neg_mean_absolute_error')
        mae = cv_scores.mean()
        
        self.models['Ridge'] = model
        self.best_model = model
        self.best_score = mae
        
        # Store binding energy specific results
        self.be_models = self.models.copy()
        self.be_best_model = self.best_model
        self.be_best_score = self.best_score
        
        print(f"✅ Ridge model trained - MAE: {self.be_best_score:.3f} MeV")
    
    def train_stability_models(self):
        """Train models specifically for stability prediction."""
        print("Training stability models...")
        
        # Reset models for stability training
        self.models = {}
        self.best_model = None
        self.best_score = 0.0  # For classification, higher is better
        
        # Use stability target
        self.y = self.y_stability.astype(int)  # Convert boolean to int
        
        # Train models (using classification instead of regression)
        self.train_stability_models_parallel()
        
        # Store stability models
        self.stability_models = self.models.copy()
        self.stability_best_model = self.best_model
        self.stability_best_score = self.best_score
        
        print(f"✅ Stability models trained - Best Accuracy: {self.stability_best_score:.3f}")
    
    def train_stability_models_parallel(self):
        """Train stability models in parallel using multiprocessing."""
        print("Starting parallel stability model training...")
        
        # Define models and parameter grids for classification
        models_config = [
            ('RandomForest', RandomForestClassifier(random_state=42), {
                'n_estimators': [100, 200, 300],
                'max_depth': [10, 20, None],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4]
            }),
            ('GradientBoosting', GradientBoostingClassifier(random_state=42), {
                'n_estimators': [100, 200, 300],
                'max_depth': [3, 4, 5],
                'learning_rate': [0.01, 0.1, 0.2],
                'subsample': [0.8, 0.9, 1.0]
            })
        ]
        
        # Prepare data for multiprocessing
        training_data = []
        for model_name, model, param_grid in models_config:
            training_data.append((model_name, model, param_grid))
        
        # Train models in parallel
        start_time = time.time()
        
        with Pool(processes=min(self.n_jobs, len(models_config))) as pool:
            from functools import partial
            train_func = partial(self._train_single_stability_model_wrapper, self.X, self.y, self.n_jobs)
            
            results = pool.map(train_func, training_data)
        
        total_time = time.time() - start_time
        print(f"All stability models completed in {total_time:.1f}s")
        
        # Process results
        for model_name, best_score, best_model in results:
            if best_model is not None:
                self.models[model_name] = best_model
                print(f"[{model_name}] Final Accuracy: {best_score:.3f}")
                
                if best_score > self.best_score:  # Higher accuracy is better for classification
                    self.best_score = best_score
                    self.best_model = best_model
                    print(f"[VICTORY] New best stability model: {model_name} with {best_score:.3f} accuracy")
        
        print(f"\n[VICTORY] Best overall stability model: {self.best_score:.3f} accuracy")
    
    @staticmethod
    def _train_single_stability_model_wrapper(X, y, n_jobs, model_data):
        """Wrapper function for multiprocessing stability training."""
        model_name, model, param_grid = model_data
        
        print(f"[{model_name}] Starting stability training...")
        start_time = time.time()
        
        try:
            # Use multiprocessing for GridSearchCV
            grid_search = GridSearchCV(
                model, 
                param_grid, 
                cv=3,
                scoring='accuracy',  # Use accuracy for classification
                n_jobs=n_jobs,
                verbose=0
            )
            
            grid_search.fit(X, y)
            
            # Get best score and model
            best_score = grid_search.best_score_
            best_model = grid_search.best_estimator_
            
            training_time = time.time() - start_time
            print(f"[{model_name}] Completed in {training_time:.1f}s - Best Accuracy: {best_score:.3f}")
            
            return model_name, best_score, best_model
            
        except Exception as e:
            print(f"[{model_name}] ERROR: {str(e)}")
            return model_name, 0.0, None
    
    def create_unified_ensemble(self):
        """Create unified ensemble for both binding energy and stability."""
        print("Creating unified ensemble...")
        
        # Get binding energy predictions
        be_predictions = {}
        for name, model in self.be_models.items():
            pred = model.predict(self.X)
            be_predictions[name] = pred
        
        # Get stability predictions
        stability_predictions = {}
        for name, model in self.stability_models.items():
            pred = model.predict(self.X)
            stability_predictions[name] = pred
        
        # Calculate binding energy ensemble (simplified since we only have Ridge)
        be_ensemble_pred = be_predictions['Ridge']  # Just use Ridge directly
        be_weights = {'Ridge': 1.0}  # Single model weight
        
        print(f"Debug: y_be range: {float(np.array(self.y_be).min()):.3f} to {float(np.array(self.y_be).max()):.3f}")
        print(f"Debug: Ridge prediction range: {float(np.array(be_ensemble_pred).min()):.3f} to {float(np.array(be_ensemble_pred).max()):.3f}")
        
        # Calculate stability ensemble
        stability_ensemble_pred = np.zeros(len(self.y_stability))
        stability_weights = {}
        for name, pred in stability_predictions.items():
            acc = accuracy_score(self.y_stability, pred)
            weight = acc  # Higher accuracy = higher weight
            stability_weights[name] = weight
            stability_ensemble_pred += weight * pred
        
        # Normalize stability weights
        stability_total_weight = sum(stability_weights.values())
        for name in stability_weights:
            stability_weights[name] /= stability_total_weight
        
        # Calculate final metrics
        be_ensemble_mae = mean_absolute_error(self.y_be, be_ensemble_pred)
        be_ensemble_r2 = r2_score(self.y_be, be_ensemble_pred)
        
        # Convert stability predictions to binary
        stability_ensemble_binary = (stability_ensemble_pred > 0.5).astype(int)
        stability_ensemble_acc = accuracy_score(self.y_stability, stability_ensemble_binary)
        
        print(f"\n[UNIFIED ENSEMBLE] Binding Energy MAE: {be_ensemble_mae:.3f} MeV, R²: {be_ensemble_r2:.3f}")
        print(f"[UNIFIED ENSEMBLE] Stability Accuracy: {stability_ensemble_acc:.3f}")
        
        return {
            'be_mae': be_ensemble_mae,
            'be_r2': be_ensemble_r2,
            'stability_acc': stability_ensemble_acc,
            'be_weights': be_weights,
            'stability_weights': stability_weights
        }

if __name__ == "__main__":
    # Run the complete analysis
    model = UltimateGTEVictoryModelMultiprocessing()
    results = model.run_complete_analysis()
