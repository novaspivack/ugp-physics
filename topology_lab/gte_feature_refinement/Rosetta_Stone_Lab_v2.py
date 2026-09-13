"""
Rosetta Stone Discovery Lab v2.0 - Enhanced Edition

This module implements the refined experimental harness for discovering the mapping
between GTE triples and particle quantum numbers using advanced ML methods.

Author: UGP Research Program
Version: 2.0 - Refinement Edition
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.linear_model import LogisticRegression, Lasso, Ridge
from sklearn.metrics import accuracy_score, f1_score, r2_score, mean_squared_error
from sklearn.model_selection import cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

# Import our enhanced feature extractor
from GTE_Feature_Extractor_v2 import GTEFeatureExtractorV2

# Try to import advanced ML libraries
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    print("Warning: XGBoost not available. Will use alternative methods.")
    XGBOOST_AVAILABLE = False

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    print("Warning: LightGBM not available. Will use alternative methods.")
    LIGHTGBM_AVAILABLE = False

# Try to import gplearn for symbolic regression
try:
    from gplearn.genetic import SymbolicRegressor, SymbolicClassifier  # type: ignore
    from gplearn.functions import make_function  # type: ignore
    GPLEARN_AVAILABLE = True
except ImportError:
    print("Warning: gplearn not available. Symbolic regression will be skipped.")
    GPLEARN_AVAILABLE = False


class RosettaStoneLabV2:
    """
    Enhanced experimental harness for discovering the GTE-to-Physics mapping.
    """
    
    def __init__(self, include_interactions=True, include_nonlinear=True, include_ratios=True):
        """Initialize the enhanced lab with canonical data."""
        self.extractor = GTEFeatureExtractorV2(
            include_interactions=include_interactions,
            include_nonlinear=include_nonlinear,
            include_ratios=include_ratios
        )
        self.load_canonical_data()
        self.results = {}
        self.scaler = StandardScaler()
        
    def load_canonical_data(self):
        """Load the canonical GTE triples and particle properties."""
        
        # Canonical GTE triples from specification
        self.gte_data = {
            'electron': (1, 73, 823),
            'muon': (9, 42, 1023),
            'tau': (5, 275, 65535),
            'electron_neutrino': (1, 1, 823),
            'muon_neutrino': (9, 1, 1023),
            'tau_neutrino': (5, 1, 65535),
            'up': (5, 9, 275),
            'charm': (5, 275, 65535),
            'top': (76, 337920, -1),
            'down': (9, 5, 42),
            'strange': (9, 186, 1023),
            'bottom': (5, 8191, 65535)
        }
        
        # Canonical particle properties from PDG
        self.particle_properties = {
            'electron': {'charge': -1, 'spin': 0.5, 'lepton_num': 1, 'baryon_num': 0, 'generation': 1, 'family': 'Lepton'},
            'muon': {'charge': -1, 'spin': 0.5, 'lepton_num': 1, 'baryon_num': 0, 'generation': 2, 'family': 'Lepton'},
            'tau': {'charge': -1, 'spin': 0.5, 'lepton_num': 1, 'baryon_num': 0, 'generation': 3, 'family': 'Lepton'},
            'electron_neutrino': {'charge': 0, 'spin': 0.5, 'lepton_num': 1, 'baryon_num': 0, 'generation': 1, 'family': 'Lepton'},
            'muon_neutrino': {'charge': 0, 'spin': 0.5, 'lepton_num': 1, 'baryon_num': 0, 'generation': 2, 'family': 'Lepton'},
            'tau_neutrino': {'charge': 0, 'spin': 0.5, 'lepton_num': 1, 'baryon_num': 0, 'generation': 3, 'family': 'Lepton'},
            'up': {'charge': 2/3, 'spin': 0.5, 'lepton_num': 0, 'baryon_num': 1/3, 'generation': 1, 'family': 'Quark'},
            'charm': {'charge': 2/3, 'spin': 0.5, 'lepton_num': 0, 'baryon_num': 1/3, 'generation': 2, 'family': 'Quark'},
            'top': {'charge': 2/3, 'spin': 0.5, 'lepton_num': 0, 'baryon_num': 1/3, 'generation': 3, 'family': 'Quark'},
            'down': {'charge': -1/3, 'spin': 0.5, 'lepton_num': 0, 'baryon_num': 1/3, 'generation': 1, 'family': 'Quark'},
            'strange': {'charge': -1/3, 'spin': 0.5, 'lepton_num': 0, 'baryon_num': 1/3, 'generation': 2, 'family': 'Quark'},
            'bottom': {'charge': -1/3, 'spin': 0.5, 'lepton_num': 0, 'baryon_num': 1/3, 'generation': 3, 'family': 'Quark'}
        }
        
        # Create unified dataset
        self.create_unified_dataset()
    
    def create_unified_dataset(self):
        """Create unified dataset with enhanced features and targets."""
        
        # Extract features for all particles
        particles = list(self.gte_data.keys())
        triples = [self.gte_data[p] for p in particles]
        
        # Create enhanced feature matrix
        self.feature_df = self.extractor.extract_features_dataframe(triples)
        self.feature_df['particle'] = particles
        
        # Create target dataframe
        target_data = []
        for particle in particles:
            props = self.particle_properties[particle].copy()
            props['particle'] = particle
            target_data.append(props)
        
        self.target_df = pd.DataFrame(target_data)
        
        # Merge datasets
        self.unified_df = self.feature_df.merge(self.target_df, on='particle')
        
        print(f"Created enhanced unified dataset with {len(self.unified_df)} particles and {len(self.feature_df.columns)-1} features")
        print(f"Feature count breakdown:")
        print(f"  - Basic features: ~39")
        print(f"  - Interaction terms: {len([c for c in self.feature_df.columns if '_x_' in c])}")
        print(f"  - Non-linear transforms: {len([c for c in self.feature_df.columns if any(x in c for x in ['_log_', '_square_', '_inv_'])])}")
        print(f"  - Ratio features: {len([c for c in self.feature_df.columns if '_div_' in c])}")
    
    def mdl_score(self, accuracy: float, complexity: int, w_accuracy: float = 1.0, w_complexity: float = 0.01) -> float:
        """
        Compute MDL (Minimum Description Length) score.
        
        Args:
            accuracy: Model accuracy (0-1)
            complexity: Model complexity (number of nodes/parameters)
            w_accuracy: Weight for accuracy term
            w_complexity: Weight for complexity penalty
            
        Returns:
            MDL score (higher is better)
        """
        return w_accuracy * accuracy - w_complexity * complexity
    
    def discover_charge_mapping_enhanced(self):
        """Enhanced discovery of electric charge mapping."""
        print("\n" + "="*80)
        print("ENHANCED ELECTRIC CHARGE MAPPING DISCOVERY")
        print("="*80)
        
        # Prepare data
        X = self.feature_df.drop(['particle'], axis=1)
        y = self.target_df['charge']
        
        print(f"Target values: {y.tolist()}")
        print(f"Feature matrix shape: {X.shape}")
        
        # Scale features for better performance
        X_scaled = self.scaler.fit_transform(X)
        X_scaled_df = pd.DataFrame(X_scaled, columns=X.columns)
        
        results = {}
        
        # Method 1: XGBoost Benchmark (if available)
        if XGBOOST_AVAILABLE:
            print("\n1. XGBoost Benchmark Analysis:")
            try:
                xgb_model = xgb.XGBRegressor(
                    n_estimators=100,
                    max_depth=3,
                    learning_rate=0.1,
                    random_state=42,
                    verbosity=0
                )
                xgb_model.fit(X_scaled_df, y)
                
                xgb_r2 = xgb_model.score(X_scaled_df, y)
                xgb_predictions = xgb_model.predict(X_scaled_df)
                
                print(f"XGBoost R²: {xgb_r2:.4f}")
                
                # Get feature importance
                feature_importance = pd.DataFrame({
                    'feature': X.columns,
                    'importance': xgb_model.feature_importances_
                }).sort_values('importance', ascending=False)
                
                print("Top 10 features by XGBoost importance:")
                print(feature_importance.head(10))
                
                results['xgboost'] = {
                    'r2': xgb_r2,
                    'predictions': xgb_predictions,
                    'feature_importance': feature_importance.to_dict('records')
                }
                
            except Exception as e:
                print(f"XGBoost failed: {e}")
        
        # Method 2: LightGBM Benchmark (if available)
        if LIGHTGBM_AVAILABLE:
            print("\n2. LightGBM Benchmark Analysis:")
            try:
                lgb_model = lgb.LGBMRegressor(
                    n_estimators=100,
                    max_depth=3,
                    learning_rate=0.1,
                    random_state=42,
                    verbosity=-1
                )
                lgb_model.fit(X_scaled_df, y)
                
                lgb_r2 = lgb_model.score(X_scaled_df, y)  # type: ignore
                lgb_predictions = lgb_model.predict(X_scaled_df)
                
                print(f"LightGBM R²: {lgb_r2:.4f}")
                
                # Get feature importance
                feature_importance = pd.DataFrame({
                    'feature': X.columns,
                    'importance': lgb_model.feature_importances_
                }).sort_values('importance', ascending=False)
                
                print("Top 10 features by LightGBM importance:")
                print(feature_importance.head(10))
                
                results['lightgbm'] = {
                    'r2': lgb_r2,
                    'predictions': lgb_predictions,
                    'feature_importance': feature_importance.to_dict('records')
                }
                
            except Exception as e:
                print(f"LightGBM failed: {e}")
        
        # Method 3: Enhanced Lasso Regression
        print("\n3. Enhanced Lasso Regression Analysis:")
        
        # Try different alpha values
        alphas = [0.001, 0.01, 0.1, 1.0]
        best_lasso_r2 = 0
        best_lasso_model = None
        best_lasso_alpha = None
        
        for alpha in alphas:
            lasso = Lasso(alpha=alpha, random_state=42, max_iter=2000)
            lasso.fit(X_scaled_df, y)
            r2 = lasso.score(X_scaled_df, y)
            
            if r2 > best_lasso_r2:
                best_lasso_r2 = r2
                best_lasso_model = lasso
                best_lasso_alpha = alpha
        
        print(f"Best Lasso R²: {best_lasso_r2:.4f} (alpha={best_lasso_alpha})")
        
        # Get non-zero coefficients
        coef_df = pd.DataFrame({
            'feature': X.columns,
            'coefficient': best_lasso_model.coef_
        })
        coef_df = coef_df[coef_df['coefficient'] != 0]
        coef_df['abs_coef'] = np.abs(coef_df['coefficient'])  # type: ignore
        coef_df = coef_df.sort_values('abs_coef', ascending=False).drop('abs_coef', axis=1)  # type: ignore
        
        print("Non-zero Lasso coefficients:")
        print(coef_df.head(15))
        
        results['lasso'] = {
            'r2': best_lasso_r2,
            'alpha': best_lasso_alpha,
            'coefficients': coef_df.to_dict('records'),
            'predictions': best_lasso_model.predict(X_scaled_df)
        }
        
        # Method 4: Enhanced Symbolic Regression
        if GPLEARN_AVAILABLE:
            print("\n4. Enhanced Symbolic Regression Analysis:")
            try:
                # Define custom fitness function with MDL principle
                def mdl_fitness(y_true, y_pred, sample_weight=None):
                    """Custom fitness function emphasizing MDL principle."""
                    mse = mean_squared_error(y_true, y_pred)
                    r2 = 1 - mse / np.var(y_true)
                    return r2  # We'll handle complexity in the parsimony coefficient
                
                sr = SymbolicRegressor(
                    population_size=2000,
                    generations=30,
                    stopping_criteria=0.01,
                    p_crossover=0.7,
                    p_subtree_mutation=0.1,
                    p_hoist_mutation=0.05,
                    p_point_mutation=0.1,
                    max_samples=0.9,
                    verbose=1,
                    parsimony_coefficient=0.01,  # Strong penalty for complexity
                    random_state=42,
                    function_set=('add', 'sub', 'mul', 'div', 'sqrt', 'log', 'abs', 'neg', 'inv')
                )
                sr.fit(X_scaled_df, y)
                
                sr_r2 = sr.score(X_scaled_df, y)
                sr_predictions = sr.predict(X_scaled_df)
                
                print(f"Symbolic Regression R²: {sr_r2:.4f}")
                print(f"Best formula: {sr._program}")
                
                # Compute complexity
                complexity = len(str(sr._program).split())
                mdl_score = self.mdl_score(sr_r2, complexity)
                
                print(f"Formula complexity: {complexity} terms")
                print(f"MDL Score: {mdl_score:.4f}")
                
                results['symbolic_regression'] = {
                    'r2': sr_r2,
                    'formula': str(sr._program),
                    'complexity': complexity,
                    'mdl_score': mdl_score,
                    'predictions': sr_predictions
                }
                
            except Exception as e:
                print(f"Enhanced symbolic regression failed: {e}")
        
        # Method 5: Ridge Regression for comparison
        print("\n5. Ridge Regression Analysis:")
        ridge = Ridge(alpha=1.0, random_state=42)
        ridge.fit(X_scaled_df, y)
        ridge_r2 = ridge.score(X_scaled_df, y)
        
        print(f"Ridge R²: {ridge_r2:.4f}")
        
        results['ridge'] = {
            'r2': ridge_r2,
            'predictions': ridge.predict(X_scaled_df)
        }
        
        # Store results
        self.results['charge'] = results
        
        return results
    
    def discover_family_mapping_enhanced(self):
        """Enhanced discovery of family mapping."""
        print("\n" + "="*80)
        print("ENHANCED FAMILY MAPPING DISCOVERY")
        print("="*80)
        
        # Prepare data
        X = self.feature_df.drop(['particle'], axis=1)
        y = self.target_df['family']
        
        print(f"Target values: {y.tolist()}")
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        X_scaled_df = pd.DataFrame(X_scaled, columns=X.columns)
        
        results = {}
        
        # Method 1: XGBoost Classification (if available)
        if XGBOOST_AVAILABLE:
            print("\n1. XGBoost Classification Analysis:")
            try:
                xgb_clf = xgb.XGBClassifier(
                    n_estimators=100,
                    max_depth=3,
                    learning_rate=0.1,
                    random_state=42,
                    verbosity=0
                )
                xgb_clf.fit(X_scaled_df, y)
                
                xgb_accuracy = xgb_clf.score(X_scaled_df, y)
                xgb_predictions = xgb_clf.predict(X_scaled_df)
                
                print(f"XGBoost Accuracy: {xgb_accuracy:.4f}")
                
                # Get feature importance
                feature_importance = pd.DataFrame({
                    'feature': X.columns,
                    'importance': xgb_clf.feature_importances_
                }).sort_values('importance', ascending=False)
                
                print("Top 10 features by XGBoost importance:")
                print(feature_importance.head(10))
                
                results['xgboost'] = {
                    'accuracy': xgb_accuracy,
                    'predictions': xgb_predictions,
                    'feature_importance': feature_importance.to_dict('records')
                }
                
            except Exception as e:
                print(f"XGBoost classification failed: {e}")
        
        # Method 2: Enhanced Logistic Regression
        print("\n2. Enhanced Logistic Regression Analysis:")
        
        # Try different regularization strengths
        C_values = [0.1, 1.0, 10.0, 100.0]
        best_lr_accuracy = 0
        best_lr_model = None
        best_lr_C = None
        
        for C in C_values:
            lr = LogisticRegression(C=C, random_state=42, max_iter=1000)
            lr.fit(X_scaled_df, y)
            accuracy = lr.score(X_scaled_df, y)
            
            if accuracy > best_lr_accuracy:
                best_lr_accuracy = accuracy
                best_lr_model = lr
                best_lr_C = C
        
        print(f"Best Logistic Regression Accuracy: {best_lr_accuracy:.4f} (C={best_lr_C})")
        
        # Get coefficients
        coef_df = pd.DataFrame({
            'feature': X.columns,
            'coefficient': best_lr_model.coef_[0]
        }).sort_values('coefficient', key=lambda x: abs(x), ascending=False)
        
        print("Top coefficients:")
        print(coef_df.head(15))
        
        results['logistic_regression'] = {
            'accuracy': best_lr_accuracy,
            'C': best_lr_C,
            'coefficients': coef_df.to_dict('records'),
            'predictions': best_lr_model.predict(X_scaled_df)
        }
        
        # Store results
        self.results['family'] = results
        
        return results
    
    def run_enhanced_discovery(self):
        """Run the complete enhanced discovery protocol."""
        print("ENHANCED ROSETTA STONE DISCOVERY LAB v2.0")
        print("="*80)
        print("Starting comprehensive enhanced discovery protocol...")
        
        # Run enhanced discovery methods
        self.discover_charge_mapping_enhanced()
        self.discover_family_mapping_enhanced()
        
        # Generate enhanced summary
        self.generate_enhanced_summary()
        
        return self.results
    
    def generate_enhanced_summary(self):
        """Generate an enhanced summary of all discoveries."""
        print("\n" + "="*80)
        print("ENHANCED DISCOVERY SUMMARY")
        print("="*80)
        
        for property_name, result in self.results.items():
            print(f"\n{property_name.upper()}:")
            
            if property_name == 'charge':
                print("  Regression Results:")
                for method, data in result.items():
                    if 'r2' in data:
                        print(f"    {method}: R² = {data['r2']:.4f}")
                    elif 'accuracy' in data:
                        print(f"    {method}: Accuracy = {data['accuracy']:.4f}")
                        
                # Find best method
                best_r2 = 0
                best_method = None
                for method, data in result.items():
                    if 'r2' in data and data['r2'] > best_r2:
                        best_r2 = data['r2']
                        best_method = method
                
                if best_method:
                    print(f"  Best Method: {best_method} (R² = {best_r2:.4f})")
                    
            elif property_name == 'family':
                print("  Classification Results:")
                for method, data in result.items():
                    if 'accuracy' in data:
                        print(f"    {method}: Accuracy = {data['accuracy']:.4f}")
                        
                # Find best method
                best_accuracy = 0
                best_method = None
                for method, data in result.items():
                    if 'accuracy' in data and data['accuracy'] > best_accuracy:
                        best_accuracy = data['accuracy']
                        best_method = method
                
                if best_method:
                    print(f"  Best Method: {best_method} (Accuracy = {best_accuracy:.4f})")
    
    def save_enhanced_results(self, filename='rosetta_stone_results_v2.csv'):
        """Save the enhanced feature matrix and results."""
        # Save enhanced feature matrix
        self.feature_df.to_csv(filename, index=False)
        print(f"Enhanced feature matrix saved to {filename}")
        
        # Save unified dataset
        unified_filename = filename.replace('.csv', '_unified.csv')
        self.unified_df.to_csv(unified_filename, index=False)
        print(f"Enhanced unified dataset saved to {unified_filename}")


def main():
    """Main execution function for enhanced discovery."""
    print("Initializing Enhanced Rosetta Stone Discovery Lab v2.0...")
    
    lab = RosettaStoneLabV2()
    
    print("\nRunning enhanced discovery protocol...")
    results = lab.run_enhanced_discovery()
    
    print("\nSaving enhanced results...")
    lab.save_enhanced_results('feature_matrix_v2.csv')
    
    print("\nEnhanced discovery protocol completed!")
    return lab, results


if __name__ == "__main__":
    lab, results = main()
