# ml_model_tester.py
"""
ML Model Testing and Refinement Tool for Hypercharge Prediction

This module provides comprehensive testing and refinement capabilities for the
hypercharge prediction ML model used in the UGP Renormalization Finalizer.
"""

import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPRegressor
import joblib
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class HyperchargeMLTester:
    """Comprehensive ML model testing and refinement tool."""
    
    def __init__(self, particle_catalog: pd.DataFrame, hypercharge_model: Dict[str, Any]):
        self.particle_catalog = particle_catalog
        self.hypercharge_model = hypercharge_model
        # Use features that actually matter for hypercharge prediction
        # Based on discovery engine analysis: GTE score and stability score are ignored
        # Focus on physical properties that determine hypercharge
        self.feature_names = ['mass_mev_calibrated', 'generation', 'n_value', 'a', 'b', 'c', 'viability_score']
        self.models = {}
        self.results = {}
        
    def analyze_data_distribution(self) -> Dict[str, Any]:
        """Analyze the distribution of particles across different categories."""
        logger.info("Analyzing particle data distribution...")
        
        analysis = {}
        
        # Generation distribution
        analysis['generation_dist'] = self.particle_catalog['generation'].value_counts().to_dict()
        
        # Mass distribution
        analysis['mass_stats'] = {
            'min': self.particle_catalog['mass'].min(),
            'max': self.particle_catalog['mass'].max(),
            'mean': self.particle_catalog['mass'].mean(),
            'median': self.particle_catalog['mass'].median(),
            'std': self.particle_catalog['mass'].std()
        }
        
        # Stability distribution
        if 'stability_score' in self.particle_catalog.columns:
            analysis['stability_dist'] = {
                'min': self.particle_catalog['stability_score'].min(),
                'max': self.particle_catalog['stability_score'].max(),
                'mean': self.particle_catalog['stability_score'].mean(),
                'std': self.particle_catalog['stability_score'].std()
            }
        
        # GTE score distribution
        if 'gte_score' in self.particle_catalog.columns:
            analysis['gte_dist'] = {
                'min': self.particle_catalog['gte_score'].min(),
                'max': self.particle_catalog['gte_score'].max(),
                'mean': self.particle_catalog['gte_score'].mean(),
                'std': self.particle_catalog['gte_score'].std()
            }
        
        # Rejection status
        if 'is_rejected' in self.particle_catalog.columns:
            analysis['rejection_dist'] = self.particle_catalog['is_rejected'].value_counts().to_dict()
        
        # Print summary
        print("📊 DATA DISTRIBUTION ANALYSIS:")
        print(f"Total particles: {len(self.particle_catalog):,}")
        print(f"Generations: {analysis['generation_dist']}")
        print(f"Mass range: {analysis['mass_stats']['min']:.3f} - {analysis['mass_stats']['max']:.3f} GeV")
        print(f"Mass median: {analysis['mass_stats']['median']:.3f} GeV")
        
        if 'stability_dist' in analysis:
            print(f"Stability range: {analysis['stability_dist']['min']:.3f} - {analysis['stability_dist']['max']:.3f}")
        
        if 'rejection_dist' in analysis:
            print(f"Rejection status: {analysis['rejection_dist']}")
        
        return analysis
    
    def calculate_true_hypercharges(self, sample_size: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray]:
        """Calculate true hypercharges for a sample of particles."""
        try:
            from .ugp_renormalization_finalizer_enhanced import assign_hypercharge
        except ImportError:
            from ugp_discovery_lab.experiments.ugp_renormalization_finalizer_enhanced import assign_hypercharge
        
        if sample_size is None:
            sample_size = min(50000, len(self.particle_catalog))
        
        logger.info(f"Calculating true hypercharges for {sample_size} particles...")
        
        # Stratified sampling by generation
        sample_particles = []
        for gen in [1, 2, 3]:
            gen_particles = self.particle_catalog[self.particle_catalog['generation'] == gen]
            if len(gen_particles) > 0:
                gen_sample_size = min(sample_size // 3, len(gen_particles))
                sample_particles.append(gen_particles.sample(n=gen_sample_size, random_state=42))
        
        if not sample_particles:
            raise ValueError("No particles found for hypercharge calculation")
        
        sample_df = pd.concat(sample_particles, ignore_index=True)
        
        # Calculate features and targets
        X = sample_df[self.feature_names].fillna(0).values
        y = []
        
        for _, particle in sample_df.iterrows():
            try:
                particle_dict = particle.to_dict()
                
                # Fix column mapping for hypercharge calculation
                if 'mass' not in particle_dict:
                    particle_dict['mass'] = particle_dict.get('mass_mev_calibrated', 1000.0) / 1000.0  # Convert MeV to GeV
                if 'g' not in particle_dict:
                    particle_dict['g'] = particle_dict.get('generation', 1)
                if pd.isna(particle_dict.get('c_state')) or particle_dict.get('c_state') is None:
                    particle_dict['c_state'] = 'ridge_default'  # Default value
                
                hypercharge = assign_hypercharge(particle_dict, self.hypercharge_model)
                y.append(hypercharge)
            except Exception as e:
                y.append(0.0)
        
        return np.array(X), np.array(y)
    
    def test_model_performance(self, model_name: str, model, X_train: np.ndarray, X_test: np.ndarray, 
                             y_train: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
        """Test a single model and return performance metrics."""
        # Train model
        model.fit(X_train, y_train)
        
        # Make predictions
        y_pred_train = model.predict(X_train)
        y_pred_test = model.predict(X_test)
        
        # Calculate metrics
        metrics = {
            'train_mse': mean_squared_error(y_train, y_pred_train),
            'test_mse': mean_squared_error(y_test, y_pred_test),
            'train_r2': r2_score(y_train, y_pred_train),
            'test_r2': r2_score(y_test, y_pred_test),
            'train_mae': mean_absolute_error(y_train, y_pred_train),
            'test_mae': mean_absolute_error(y_test, y_pred_test),
            'overfitting': r2_score(y_train, y_pred_train) - r2_score(y_test, y_pred_test)
        }
        
        return metrics
    
    def test_multiple_models(self, X: np.ndarray, y: np.ndarray, test_size: float = 0.2) -> Dict[str, Dict]:
        """Test multiple ML models and compare their performance."""
        logger.info("Testing multiple ML models...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42)
        
        # Define models to test
        models_to_test = {
            'RandomForest': RandomForestRegressor(n_estimators=200, max_depth=15, random_state=42),
            'GradientBoosting': GradientBoostingRegressor(n_estimators=200, max_depth=10, random_state=42),
            'MLPRegressor': MLPRegressor(hidden_layer_sizes=(100, 50), max_iter=1000, random_state=42),
            'RandomForest_Tuned': RandomForestRegressor(n_estimators=500, max_depth=20, min_samples_split=5, random_state=42)
        }
        
        results = {}
        
        for name, model in models_to_test.items():
            logger.info(f"Testing {name}...")
            try:
                metrics = self.test_model_performance(name, model, X_train, X_test, y_train, y_test)
                results[name] = metrics
                self.models[name] = model
                
                print(f"✅ {name}:")
                print(f"   Test R²: {metrics['test_r2']:.4f}")
                print(f"   Test MSE: {metrics['test_mse']:.6f}")
                print(f"   Overfitting: {metrics['overfitting']:.4f}")
                
            except Exception as e:
                logger.error(f"Failed to test {name}: {e}")
                results[name] = {'error': str(e)}
        
        self.results = results
        return results
    
    def hyperparameter_tuning(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """Perform hyperparameter tuning for the best model."""
        logger.info("Performing hyperparameter tuning...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Define parameter grid for RandomForest
        param_grid = {
            'n_estimators': [200, 500, 1000],
            'max_depth': [10, 15, 20, None],
            'min_samples_split': [2, 5, 10],
            'min_samples_leaf': [1, 2, 4]
        }
        
        # Perform grid search
        rf = RandomForestRegressor(random_state=42)
        grid_search = GridSearchCV(rf, param_grid, cv=5, scoring='r2', n_jobs=-1, verbose=1)
        grid_search.fit(X_train, y_train)
        
        # Get best model
        best_model = grid_search.best_estimator_
        best_params = grid_search.best_params_
        best_score = grid_search.best_score_
        
        # Test best model
        y_pred = best_model.predict(X_test)
        test_r2 = r2_score(y_test, y_pred)
        test_mse = mean_squared_error(y_test, y_pred)
        
        results = {
            'best_params': best_params,
            'cv_score': best_score,
            'test_r2': test_r2,
            'test_mse': test_mse,
            'model': best_model
        }
        
        print(f"🎯 Best parameters: {best_params}")
        print(f"   CV R²: {best_score:.4f}")
        print(f"   Test R²: {test_r2:.4f}")
        print(f"   Test MSE: {test_mse:.6f}")
        
        return results
    
    def analyze_feature_importance(self, model) -> Dict[str, float]:
        """Analyze feature importance from a trained model."""
        if hasattr(model, 'feature_importances_'):
            importance = model.feature_importances_
            feature_importance = dict(zip(self.feature_names, importance))
            
            # Sort by importance
            sorted_importance = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True))
            
            print("🔍 FEATURE IMPORTANCE:")
            for feature, imp in sorted_importance.items():
                print(f"   {feature}: {imp:.4f}")
            
            return sorted_importance
        else:
            print("⚠️  Model does not support feature importance analysis")
            return {}
    
    def save_model(self, model, filepath: str):
        """Save the trained model to disk."""
        joblib.dump(model, filepath)
        logger.info(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load a trained model from disk."""
        model = joblib.load(filepath)
        logger.info(f"Model loaded from {filepath}")
        return model


def run_ml_model_testing(particle_catalog_path: str, config_path: str, output_dir: str):
    """Run comprehensive ML model testing."""
    logger.info("Starting ML model testing and refinement...")
    
    # Load configuration
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Load particle catalog
    particle_catalog = pd.read_parquet(particle_catalog_path)
    particle_catalog['mass'] = particle_catalog['mass_mev_calibrated'] / 1000.0
    
    # Initialize tester
    tester = HyperchargeMLTester(particle_catalog, config['hypercharge_model'])
    
    # Analyze data distribution
    distribution_analysis = tester.analyze_data_distribution()
    
    # Calculate true hypercharges
    X, y = tester.calculate_true_hypercharges(sample_size=100000)  # Use more data
    
    # Test multiple models
    model_results = tester.test_multiple_models(X, y)
    
    # Find best model
    best_model_name = max(model_results.keys(), 
                         key=lambda k: model_results[k].get('test_r2', -1) if 'test_r2' in model_results[k] else -1)
    
    print(f"\n🏆 BEST MODEL: {best_model_name}")
    print(f"   Test R²: {model_results[best_model_name]['test_r2']:.4f}")
    
    # Hyperparameter tuning
    if best_model_name.startswith('RandomForest'):
        tuning_results = tester.hyperparameter_tuning(X, y)
        
        # Analyze feature importance
        feature_importance = tester.analyze_feature_importance(tuning_results['model'])
        
        # Save best model
        output_path = Path(output_dir) / 'best_hypercharge_model.pkl'
        tester.save_model(tuning_results['model'], str(output_path))
        
        return tuning_results['model'], tuning_results
    else:
        # Analyze feature importance of best model
        feature_importance = tester.analyze_feature_importance(tester.models[best_model_name])
        
        # Save best model
        output_path = Path(output_dir) / 'best_hypercharge_model.pkl'
        tester.save_model(tester.models[best_model_name], str(output_path))
        
        return tester.models[best_model_name], model_results[best_model_name]


if __name__ == "__main__":
    # Example usage
    particle_catalog_path = "./inputs/residual_deconstruction_experiment/particle_catalog.parquet"
    config_path = "./residual_deconstruction_config.json"
    output_dir = "./results/ml_model_testing"
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    best_model, results = run_ml_model_testing(particle_catalog_path, config_path, output_dir)
    print(f"\n✅ ML model testing completed. Best model saved to {output_dir}")
