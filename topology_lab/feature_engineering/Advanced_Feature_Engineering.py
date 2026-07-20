#!/usr/bin/env python3
"""
Advanced Feature Engineering: Pushing Beyond 83% Accuracy

This script implements advanced feature engineering techniques to push the accuracy
beyond 83% and closer to the theoretical maximum.

Part of Project 2c: Foundational Fortification of the Braid Atlas
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, VotingRegressor
from sklearn.linear_model import LassoCV, RidgeCV, ElasticNetCV
from sklearn.neural_network import MLPRegressor
from sklearn.svm import SVR
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.model_selection import cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.pipeline import Pipeline
import warnings
warnings.filterwarnings('ignore')

# Import our existing components
try:
    from Dynamic_Feature_Analysis import DynamicFeatureAnalyzer, EnhancedFeatureVector  # type: ignore
except ImportError:
    # Fallback for linter
    DynamicFeatureAnalyzer = None  # type: ignore
    EnhancedFeatureVector = None  # type: ignore

class AdvancedFeatureEngineer:
    """
    Advanced feature engineering to push accuracy beyond 83%.
    """
    
    def __init__(self):
        """Initialize the advanced feature engineer."""
        self.base_analyzer = DynamicFeatureAnalyzer() if DynamicFeatureAnalyzer else None  # type: ignore
        self.scaler = StandardScaler()
        self.poly_features = PolynomialFeatures(degree=2, include_bias=False, interaction_only=True)
        
    def create_advanced_features(self, enhanced_vectors: List[object]) -> np.ndarray:  # type: ignore
        """
        Create advanced features including polynomial interactions, ratios, and derived features.
        
        Args:
            enhanced_vectors: List of enhanced feature vectors
            
        Returns:
            Advanced feature matrix
        """
        # Extract base features
        base_features_list = []
        for vector in enhanced_vectors:
            base_features_list.append(
                list(vector.static_features.values()) + list(vector.dynamic_features.values())  # type: ignore
            )
        
        X_base = np.array(base_features_list)
        
        # Create advanced features
        advanced_features = []
        
        for i, vector in enumerate(enhanced_vectors):
            static = vector.static_features  # type: ignore
            dynamic = vector.dynamic_features  # type: ignore
            
            # Advanced static features
            advanced_static = {
                # Polynomial features
                'a_squared': static['a'] ** 2,
                'b_squared': static['b'] ** 2,
                'c_squared': static['c'] ** 2,
                'a_times_b': static['a'] * static['b'],
                'a_times_c': static['a'] * static['c'],
                'b_times_c': static['b'] * static['c'],
                
                # Ratio features
                'a_over_b': static['a'] / (static['b'] + 1e-8),
                'b_over_c': static['b'] / (static['c'] + 1e-8),
                'a_over_c': static['a'] / (static['c'] + 1e-8),
                
                # Logarithmic features
                'log_a': np.log(abs(static['a']) + 1),
                'log_b': np.log(abs(static['b']) + 1),
                'log_c': np.log(abs(static['c']) + 1),
                
                # Modular arithmetic combinations
                'a_mod_7': static['a'] % 7,
                'b_mod_7': static['b'] % 7,
                'c_mod_7': static['c'] % 7,
                'a_mod_11': static['a'] % 11,
                'b_mod_11': static['b'] % 11,
                'c_mod_11': static['c'] % 11,
                
                # GCD combinations
                'gcd_ab': np.gcd(int(abs(static['a'])), int(abs(static['b']))),
                'gcd_ac': np.gcd(int(abs(static['a'])), int(abs(static['c']))),
                'gcd_abc': np.gcd(np.gcd(int(abs(static['a'])), int(abs(static['b']))), int(abs(static['c']))),
                
                # Prime-related features
                'a_is_prime': self._is_prime(int(abs(static['a']))),
                'b_is_prime': self._is_prime(int(abs(static['b']))),
                'c_is_prime': self._is_prime(int(abs(static['c']))),
                
                # Sum and product features
                'sum_abc': static['a'] + static['b'] + static['c'],
                'product_abc': static['a'] * static['b'] * static['c'],
                'sum_squares': static['a']**2 + static['b']**2 + static['c']**2,
            }
            
            # Advanced dynamic features
            advanced_dynamic = {
                # Frequency ratios
                'freq_ratio': dynamic['dominant_frequency'] / (dynamic['frequency_entropy'] + 1e-8),
                'lifetime_freq_product': dynamic['mean_lifetime'] * dynamic['dominant_frequency'],
                
                # Stability combinations
                'stability_complexity': dynamic['stability_index'] * dynamic['computational_irreducibility'],
                'dynamic_stability': dynamic['dynamic_complexity'] * dynamic['stability_index'],
                
                # Interaction features
                'field_interaction': dynamic['field_correlation_mean'] * dynamic['field_correlation_std'],
                'strand_field_interaction': dynamic['mean_cross_strand_interaction'] * dynamic['field_correlation_mean'],
                
                # Temporal features
                'temporal_complexity': dynamic['temporal_variance'] * dynamic['computational_irreducibility'],
                'oscillation_stability': dynamic['dominant_frequency'] * dynamic['stability_index'],
            }
            
            # Combine all features
            all_features = list(static.values()) + list(dynamic.values()) + \
                          list(advanced_static.values()) + list(advanced_dynamic.values())
            
            advanced_features.append(all_features)
        
        return np.array(advanced_features)
    
    def _is_prime(self, n: int) -> float:
        """Check if a number is prime."""
        if n < 2:
            return 0.0
        if n == 2:
            return 1.0
        if n % 2 == 0:
            return 0.0
        for i in range(3, int(np.sqrt(n)) + 1, 2):
            if n % i == 0:
                return 0.0
        return 1.0
    
    def create_ensemble_models(self) -> Dict[str, object]:
        """
        Create an ensemble of advanced models.
        
        Returns:
            Dictionary of trained models
        """
        models = {
            'lasso': LassoCV(cv=5, random_state=42, max_iter=10000),
            'ridge': RidgeCV(cv=5),
            'elastic_net': ElasticNetCV(cv=5, random_state=42, max_iter=10000),
            'random_forest': RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42),
            'gradient_boosting': GradientBoostingRegressor(n_estimators=200, max_depth=6, random_state=42),
            'neural_network': MLPRegressor(hidden_layer_sizes=(100, 50), max_iter=1000, random_state=42),
            'svr': SVR(kernel='rbf', C=1.0, gamma='scale'),
        }
        
        return models
    
    def train_advanced_models(self, enhanced_vectors: List[EnhancedFeatureVector]) -> Dict[str, Dict[str, float]]:  # type: ignore
        """
        Train advanced models with enhanced features.
        
        Args:
            enhanced_vectors: List of enhanced feature vectors
            
        Returns:
            Dictionary with model performance metrics
        """
        # Create advanced features
        X_advanced = self.create_advanced_features(enhanced_vectors)
        y = np.array([vector.actual_charge for vector in enhanced_vectors])  # type: ignore
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X_advanced)
        
        # Create models
        models = self.create_ensemble_models()
        
        # Train and evaluate models
        results = {}
        
        for name, model in models.items():
            try:
                # Train model
                model.fit(X_scaled, y)  # type: ignore
                
                # Make predictions
                y_pred = model.predict(X_scaled)  # type: ignore
                
                # Calculate metrics
                r2 = r2_score(y, y_pred)
                mse = mean_squared_error(y, y_pred)
                
                # Cross-validation
                cv_scores = cross_val_score(model, X_scaled, y, cv=5, scoring='r2')
                
                results[name] = {
                    'r2': float(r2),
                    'mse': float(mse),
                    'cv_mean': float(np.mean(cv_scores)),
                    'cv_std': float(np.std(cv_scores))
                }
                
                print(f"✅ {name}: R² = {r2:.4f}, CV = {np.mean(cv_scores):.4f} ± {np.std(cv_scores):.4f}")
                
            except Exception as e:
                print(f"❌ {name}: Failed - {str(e)}")
                results[name] = {
                    'r2': 0.0,
                    'mse': float('inf'),
                    'cv_mean': 0.0,
                    'cv_std': 0.0
                }
        
        return results
    
    def create_voting_ensemble(self, enhanced_vectors: List[EnhancedFeatureVector],  # type: ignore
                              model_results: Dict[str, Dict[str, float]]) -> Dict[str, float]:
        """
        Create a voting ensemble of the best models.
        
        Args:
            enhanced_vectors: List of enhanced feature vectors
            model_results: Results from individual models
            
        Returns:
            Ensemble performance metrics
        """
        # Create advanced features
        X_advanced = self.create_advanced_features(enhanced_vectors)
        y = np.array([vector.actual_charge for vector in enhanced_vectors])  # type: ignore
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X_advanced)
        
        # Select best models (R² > 0.7)
        best_models = []
        for name, results in model_results.items():
            if results['r2'] > 0.7:
                best_models.append(name)
        
        if len(best_models) < 2:
            print("⚠️  Not enough good models for ensemble")
            return {'r2': 0.0, 'mse': float('inf')}
        
        # Create voting ensemble
        estimators = []
        for name in best_models:
            model = self.create_ensemble_models()[name]
            estimators.append((name, model))
        
        voting_regressor = VotingRegressor(estimators)
        voting_regressor.fit(X_scaled, y)
        
        # Evaluate ensemble
        y_pred = voting_regressor.predict(X_scaled)
        r2 = r2_score(y, y_pred)
        mse = mean_squared_error(y, y_pred)
        
        print(f"🎯 Voting Ensemble: R² = {r2:.4f}")
        
        return {
            'r2': float(r2),
            'mse': float(mse)
        }

def main():
    """Run the advanced feature engineering analysis."""
    print("🚀 Advanced Feature Engineering: Pushing Beyond 83%")
    print("=" * 60)
    
    # Initialize analyzer
    engineer = AdvancedFeatureEngineer()
    base_analyzer = DynamicFeatureAnalyzer() if DynamicFeatureAnalyzer else None  # type: ignore
    
    # Create enhanced dataset
    print("📊 Creating enhanced dataset...")
    enhanced_vectors = base_analyzer.create_enhanced_dataset()
    print(f"✅ Created dataset with {len(enhanced_vectors)} particles")
    
    # Train advanced models
    print("🤖 Training advanced models with enhanced features...")
    model_results = engineer.train_advanced_models(enhanced_vectors)
    
    # Create voting ensemble
    print("🎯 Creating voting ensemble...")
    ensemble_results = engineer.create_voting_ensemble(enhanced_vectors, model_results)
    
    # Print results
    print("\n" + "=" * 60)
    print("📈 ADVANCED ANALYSIS RESULTS")
    print("=" * 60)
    
    # Find best individual model
    best_model = max(model_results.items(), key=lambda x: x[1]['r2'])
    print(f"Best Individual Model: {best_model[0]} (R² = {best_model[1]['r2']:.4f})")
    
    # Ensemble results
    if ensemble_results['r2'] > 0:
        print(f"Voting Ensemble: R² = {ensemble_results['r2']:.4f}")
        
        if ensemble_results['r2'] > 0.90:
            print("🎯 SUCCESS: >90% accuracy achieved!")
        elif ensemble_results['r2'] > 0.85:
            print("🎯 EXCELLENT: >85% accuracy achieved!")
        else:
            print("📈 Good improvement shown")
    
    # Compare with base results
    base_results = base_analyzer.train_models(enhanced_vectors)
    print(f"\nBase Combined Model: R² = {base_results['combined_r2']:.4f}")
    
    if ensemble_results['r2'] > base_results['combined_r2']:
        improvement = ensemble_results['r2'] - base_results['combined_r2']
        print(f"Improvement: +{improvement:.4f} ({improvement/base_results['combined_r2']*100:.1f}%)")
    
    print("\n🎯 Advanced Feature Engineering complete!")

if __name__ == "__main__":
    main()
