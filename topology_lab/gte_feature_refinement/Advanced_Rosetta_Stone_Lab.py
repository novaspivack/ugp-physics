"""
Advanced Rosetta Stone Discovery Lab v3.0

This module implements the most advanced experimental harness for discovering the mapping
between GTE triples and particle quantum numbers, leveraging critical insights from v2.0
to push beyond 67% accuracy.

Author: UGP Research Program
Version: 3.0 - Advanced Edition
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.linear_model import LogisticRegression, Lasso, Ridge, ElasticNet
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import accuracy_score, f1_score, r2_score, mean_squared_error
from sklearn.model_selection import cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.neural_network import MLPRegressor
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


class AdvancedRosettaStoneLab:
    """
    Most advanced experimental harness leveraging critical insights from v2.0.
    """
    
    def __init__(self):
        """Initialize the advanced lab with canonical data."""
        self.extractor = GTEFeatureExtractorV2()
        self.load_canonical_data()
        self.results = {}
        self.scaler = StandardScaler()
        self.poly_features = PolynomialFeatures(degree=2, include_bias=False, interaction_only=True)
        
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
        
        print(f"Created advanced unified dataset with {len(self.unified_df)} particles and {len(self.feature_df.columns)-1} features")
    
    def identify_feature_x176(self):
        """Identify which feature corresponds to X176 from symbolic regression."""
        print("\n" + "="*80)
        print("IDENTIFYING FEATURE X176")
        print("="*80)
        
        # Get feature names
        feature_names = self.extractor.get_feature_names()
        
        print(f"Total features: {len(feature_names)}")
        print("Feature X176 would be the 176th feature (0-indexed: 175)")
        
        if len(feature_names) > 175:
            x176_feature = feature_names[175]
            print(f"Feature X176 identified as: {x176_feature}")
            
            # Analyze this feature
            X = self.feature_df.drop(['particle'], axis=1)
            y = self.target_df['charge']
            
            if x176_feature in X.columns:
                feature_values = X[x176_feature].values
                print(f"Feature values: {feature_values}")
                print(f"Feature range: {np.min(feature_values)} to {np.max(feature_values)}")
                
                # Test correlation with charge
                correlation = np.corrcoef(feature_values, y)[0, 1]
                print(f"Correlation with charge: {correlation:.4f}")
                
                # Test if log transformation improves correlation
                log_feature = np.log(np.abs(feature_values) + 1)
                log_correlation = np.corrcoef(log_feature, y)[0, 1]
                print(f"Log correlation with charge: {log_correlation:.4f}")
                
                return x176_feature, feature_values, correlation, log_correlation
            else:
                print(f"Warning: Feature {x176_feature} not found in feature matrix")
                return None, None, None, None
        else:
            print("Warning: Not enough features to identify X176")
            return None, None, None, None
    
    def create_mobius_focused_features(self):
        """Create features focused on Möbius function insights."""
        print("\n" + "="*80)
        print("CREATING MÖBIUS-FOCUSED FEATURES")
        print("="*80)
        
        # Get basic features
        X = self.feature_df.drop(['particle'], axis=1)
        
        # Create Möbius-focused features
        mobius_features = pd.DataFrame()
        
        # Möbius function values
        mobius_features['a_mu'] = X['a_mu']
        mobius_features['b_mu'] = X['b_mu']
        mobius_features['c_mu'] = X['c_mu']
        
        # Möbius interactions with modular arithmetic
        mobius_features['a_mu_x_a_mod_3'] = X['a_mu'] * X['a_mod_3']
        mobius_features['b_mu_x_b_mod_5'] = X['b_mu'] * X['b_mod_5']
        mobius_features['c_mu_x_c_mod_3'] = X['c_mu'] * X['c_mod_3']
        
        # Möbius interactions with raw values
        mobius_features['a_mu_x_a_raw'] = X['a_mu'] * X['a_raw']
        mobius_features['b_mu_x_b_raw'] = X['b_mu'] * X['b_raw']
        mobius_features['c_mu_x_c_raw'] = X['c_mu'] * X['c_raw']
        
        # Möbius interactions with omega functions
        mobius_features['a_mu_x_a_omega'] = X['a_mu'] * X['a_omega']
        mobius_features['b_mu_x_b_omega'] = X['b_mu'] * X['b_omega']
        mobius_features['c_mu_x_c_omega'] = X['c_mu'] * X['c_omega']
        
        # Cross-component Möbius interactions
        mobius_features['a_mu_x_b_mu'] = X['a_mu'] * X['b_mu']
        mobius_features['a_mu_x_c_mu'] = X['a_mu'] * X['c_mu']
        mobius_features['b_mu_x_c_mu'] = X['b_mu'] * X['c_mu']
        
        # Möbius-based ratios
        mobius_features['a_mu_div_b_mu'] = np.where(X['b_mu'] != 0, X['a_mu'] / X['b_mu'], 0)
        mobius_features['b_mu_div_c_mu'] = np.where(X['c_mu'] != 0, X['b_mu'] / X['c_mu'], 0)
        mobius_features['a_mu_div_c_mu'] = np.where(X['c_mu'] != 0, X['a_mu'] / X['c_mu'], 0)
        
        # Möbius-based composite features
        mobius_features['mobius_sum'] = X['a_mu'] + X['b_mu'] + X['c_mu']
        mobius_features['mobius_product'] = X['a_mu'] * X['b_mu'] * X['c_mu']
        mobius_features['mobius_gcd'] = np.gcd(np.gcd(np.abs(X['a_mu']), np.abs(X['b_mu'])), np.abs(X['c_mu']))
        
        print(f"Created {len(mobius_features.columns)} Möbius-focused features")
        
        return mobius_features
    
    def create_logarithmic_features(self):
        """Create features based on logarithmic relationship insights."""
        print("\n" + "="*80)
        print("CREATING LOGARITHMIC FEATURES")
        print("="*80)
        
        # Get basic features
        X = self.feature_df.drop(['particle'], axis=1)
        
        # Create logarithmic features
        log_features = pd.DataFrame()
        
        # Log transformations of key features
        key_features = ['a_raw', 'b_raw', 'c_raw', 'a_tau', 'b_tau', 'c_tau', 
                        'a_sigma', 'b_sigma', 'c_sigma', 'a_radical', 'b_radical', 'c_radical']
        
        for feat in key_features:
            if feat in X.columns:
                # Safe log transformation
                log_features[f'log_{feat}'] = np.log(np.abs(X[feat]) + 1)
                # Log of log
                log_features[f'log_log_{feat}'] = np.log(np.log(np.abs(X[feat]) + 1) + 1)
        
        # Log of interaction terms
        interaction_features = [col for col in X.columns if '_x_' in col]
        for feat in interaction_features[:20]:  # Limit to avoid explosion
            if feat in X.columns:
                log_features[f'log_{feat}'] = np.log(np.abs(X[feat]) + 1)
        
        # Log of ratios
        ratio_features = [col for col in X.columns if '_div_' in col]
        for feat in ratio_features:
            if feat in X.columns:
                log_features[f'log_{feat}'] = np.log(np.abs(X[feat]) + 1)
        
        print(f"Created {len(log_features.columns)} logarithmic features")
        
        return log_features
    
    def create_advanced_interaction_features(self):
        """Create advanced interaction features based on v2.0 insights."""
        print("\n" + "="*80)
        print("CREATING ADVANCED INTERACTION FEATURES")
        print("="*80)
        
        # Get basic features
        X = self.feature_df.drop(['particle'], axis=1)
        
        # Create advanced interaction features
        advanced_features = pd.DataFrame()
        
        # Focus on top features from v2.0
        top_features = ['b_mu', 'c_raw', 'b_mod_5', 'b_raw', 'a_mod_5', 'c_mod_3']
        
        # Create all pairwise interactions of top features
        for i, feat1 in enumerate(top_features):
            for j, feat2 in enumerate(top_features[i+1:], i+1):
                if feat1 in X.columns and feat2 in X.columns:
                    advanced_features[f'{feat1}_x_{feat2}'] = X[feat1] * X[feat2]
                    # Also create ratio
                    advanced_features[f'{feat1}_div_{feat2}'] = np.where(X[feat2] != 0, X[feat1] / X[feat2], 0)
        
        # Create three-way interactions
        for i, feat1 in enumerate(top_features[:3]):
            for j, feat2 in enumerate(top_features[1:4], 1):
                for k, feat3 in enumerate(top_features[2:5], 2):
                    if (feat1 in X.columns and feat2 in X.columns and feat3 in X.columns and 
                        i != j and j != k and i != k):
                        advanced_features[f'{feat1}_x_{feat2}_x_{feat3}'] = X[feat1] * X[feat2] * X[feat3]
        
        # Create modular arithmetic combinations
        mod_features = ['a_mod_2', 'a_mod_3', 'a_mod_5', 'b_mod_2', 'b_mod_3', 'b_mod_5', 
                       'c_mod_2', 'c_mod_3', 'c_mod_5']
        
        for feat1 in mod_features:
            for feat2 in mod_features:
                if feat1 != feat2 and feat1 in X.columns and feat2 in X.columns:
                    advanced_features[f'{feat1}_plus_{feat2}'] = X[feat1] + X[feat2]
                    advanced_features[f'{feat1}_times_{feat2}'] = X[feat1] * X[feat2]
        
        print(f"Created {len(advanced_features.columns)} advanced interaction features")
        
        return advanced_features
    
    def discover_charge_mapping_advanced(self):
        """Advanced discovery of electric charge mapping using all insights."""
        print("\n" + "="*80)
        print("ADVANCED ELECTRIC CHARGE MAPPING DISCOVERY")
        print("="*80)
        
        # Prepare basic data
        X_basic = self.feature_df.drop(['particle'], axis=1)
        y = self.target_df['charge']
        
        print(f"Target values: {y.tolist()}")
        print(f"Basic feature matrix shape: {X_basic.shape}")
        
        # Create specialized feature sets
        mobius_features = self.create_mobius_focused_features()
        log_features = self.create_logarithmic_features()
        advanced_interactions = self.create_advanced_interaction_features()
        
        # Combine all features
        X_combined = pd.concat([X_basic, mobius_features, log_features, advanced_interactions], axis=1)
        
        print(f"Combined feature matrix shape: {X_combined.shape}")
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X_combined)
        X_scaled_df = pd.DataFrame(X_scaled, columns=X_combined.columns)
        
        results = {}
        
        # Method 1: Advanced XGBoost with hyperparameter tuning
        if XGBOOST_AVAILABLE:
            print("\n1. Advanced XGBoost Analysis:")
            try:
                # Hyperparameter grid
                param_grid = {
                    'n_estimators': [100, 200, 300],
                    'max_depth': [3, 4, 5],
                    'learning_rate': [0.05, 0.1, 0.15],
                    'subsample': [0.8, 0.9, 1.0]
                }
                
                xgb_model = xgb.XGBRegressor(random_state=42, verbosity=0)
                grid_search = GridSearchCV(xgb_model, param_grid, cv=3, scoring='r2', n_jobs=-1)
                grid_search.fit(X_scaled_df, y)
                
                best_xgb = grid_search.best_estimator_
                xgb_r2 = best_xgb.score(X_scaled_df, y)
                xgb_predictions = best_xgb.predict(X_scaled_df)
                
                print(f"Best XGBoost R²: {xgb_r2:.4f}")
                print(f"Best parameters: {grid_search.best_params_}")
                
                # Get feature importance
                feature_importance = pd.DataFrame({
                    'feature': X_combined.columns,
                    'importance': best_xgb.feature_importances_
                }).sort_values('importance', ascending=False)
                
                print("Top 15 features by XGBoost importance:")
                print(feature_importance.head(15))
                
                results['xgboost_advanced'] = {
                    'r2': xgb_r2,
                    'predictions': xgb_predictions,
                    'feature_importance': feature_importance.to_dict('records'),
                    'best_params': grid_search.best_params_
                }
                
            except Exception as e:
                print(f"Advanced XGBoost failed: {e}")
        
        # Method 2: Neural Network
        print("\n2. Neural Network Analysis:")
        try:
            mlp = MLPRegressor(
                hidden_layer_sizes=(100, 50, 25),
                activation='relu',
                solver='adam',
                alpha=0.001,
                learning_rate='adaptive',
                max_iter=1000,
                random_state=42
            )
            mlp.fit(X_scaled_df, y)
            
            mlp_r2 = mlp.score(X_scaled_df, y)
            mlp_predictions = mlp.predict(X_scaled_df)
            
            print(f"Neural Network R²: {mlp_r2:.4f}")
            
            results['neural_network'] = {
                'r2': mlp_r2,
                'predictions': mlp_predictions
            }
            
        except Exception as e:
            print(f"Neural Network failed: {e}")
        
        # Method 3: Ensemble Methods
        print("\n3. Ensemble Methods Analysis:")
        try:
            # Random Forest
            rf = RandomForestRegressor(n_estimators=200, max_depth=5, random_state=42)
            rf.fit(X_scaled_df, y)
            rf_r2 = rf.score(X_scaled_df, y)
            
            # Gradient Boosting
            gb = GradientBoostingRegressor(n_estimators=200, max_depth=3, random_state=42)
            gb.fit(X_scaled_df, y)
            gb_r2 = gb.score(X_scaled_df, y)
            
            print(f"Random Forest R²: {rf_r2:.4f}")
            print(f"Gradient Boosting R²: {gb_r2:.4f}")
            
            results['random_forest'] = {'r2': rf_r2, 'predictions': rf.predict(X_scaled_df)}
            results['gradient_boosting'] = {'r2': gb_r2, 'predictions': gb.predict(X_scaled_df)}
            
        except Exception as e:
            print(f"Ensemble methods failed: {e}")
        
        # Method 4: Advanced Symbolic Regression
        if GPLEARN_AVAILABLE:
            print("\n4. Advanced Symbolic Regression Analysis:")
            try:
                # Use only top features to avoid explosion
                top_feature_indices = feature_importance.head(20).index
                X_top = X_scaled_df.iloc[:, top_feature_indices]
                
                sr = SymbolicRegressor(
                    population_size=3000,
                    generations=50,
                    stopping_criteria=0.001,
                    p_crossover=0.7,
                    p_subtree_mutation=0.1,
                    p_hoist_mutation=0.05,
                    p_point_mutation=0.1,
                    max_samples=0.9,
                    verbose=1,
                    parsimony_coefficient=0.001,  # Very light penalty for complexity
                    random_state=42,
                    function_set=('add', 'sub', 'mul', 'div', 'sqrt', 'log', 'abs', 'neg', 'inv', 'sin', 'cos')
                )
                sr.fit(X_top, y)
                
                sr_r2 = sr.score(X_top, y)
                sr_predictions = sr.predict(X_top)
                
                print(f"Advanced Symbolic Regression R²: {sr_r2:.4f}")
                print(f"Best formula: {sr._program}")
                
                # Compute complexity
                complexity = len(str(sr._program).split())
                mdl_score = sr_r2 - 0.001 * complexity
                
                print(f"Formula complexity: {complexity} terms")
                print(f"MDL Score: {mdl_score:.4f}")
                
                results['symbolic_regression_advanced'] = {
                    'r2': sr_r2,
                    'formula': str(sr._program),
                    'complexity': complexity,
                    'mdl_score': mdl_score,
                    'predictions': sr_predictions
                }
                
            except Exception as e:
                print(f"Advanced symbolic regression failed: {e}")
        
        # Store results
        self.results['charge_advanced'] = results
        
        return results
    
    def run_advanced_discovery(self):
        """Run the complete advanced discovery protocol."""
        print("ADVANCED ROSETTA STONE DISCOVERY LAB v3.0")
        print("="*80)
        print("Starting comprehensive advanced discovery protocol...")
        
        # Identify Feature X176
        x176_feature, x176_values, x176_corr, x176_log_corr = self.identify_feature_x176()
        
        # Run advanced discovery methods
        self.discover_charge_mapping_advanced()
        
        # Generate advanced summary
        self.generate_advanced_summary()
        
        return self.results
    
    def generate_advanced_summary(self):
        """Generate an advanced summary of all discoveries."""
        print("\n" + "="*80)
        print("ADVANCED DISCOVERY SUMMARY")
        print("="*80)
        
        for property_name, result in self.results.items():
            print(f"\n{property_name.upper()}:")
            
            if property_name == 'charge_advanced':
                print("  Advanced Regression Results:")
                for method, data in result.items():
                    if 'r2' in data:
                        print(f"    {method}: R² = {data['r2']:.4f}")
                        
                # Find best method
                best_r2 = 0
                best_method = None
                for method, data in result.items():
                    if 'r2' in data and data['r2'] > best_r2:
                        best_r2 = data['r2']
                        best_method = method
                
                if best_method:
                    print(f"  Best Method: {best_method} (R² = {best_r2:.4f})")
                    
                    if best_r2 > 0.6795:
                        improvement = (best_r2 - 0.6795) / 0.6795 * 100
                        print(f"  Improvement over v2.0: +{improvement:.2f}%")
    
    def save_advanced_results(self, filename='advanced_rosetta_stone_results.csv'):
        """Save the advanced results."""
        # Save enhanced feature matrix
        self.feature_df.to_csv(filename, index=False)
        print(f"Advanced feature matrix saved to {filename}")


def main():
    """Main execution function for advanced discovery."""
    print("Initializing Advanced Rosetta Stone Discovery Lab v3.0...")
    
    lab = AdvancedRosettaStoneLab()
    
    print("\nRunning advanced discovery protocol...")
    results = lab.run_advanced_discovery()
    
    print("\nSaving advanced results...")
    lab.save_advanced_results('advanced_feature_matrix.csv')
    
    print("\nAdvanced discovery protocol completed!")
    return lab, results


if __name__ == "__main__":
    lab, results = main()
