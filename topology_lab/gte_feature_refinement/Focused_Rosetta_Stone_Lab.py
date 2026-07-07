"""
Focused Rosetta Stone Discovery Lab v3.1

This module implements a focused approach to push beyond 67% accuracy by leveraging
the critical insights: Möbius function dominance, Feature X176, and logarithmic relationships.

Author: UGP Research Program
Version: 3.1 - Focused Edition
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


class FocusedRosettaStoneLab:
    """
    Focused experimental harness targeting specific insights to push beyond 67%.
    """
    
    def __init__(self):
        """Initialize the focused lab with canonical data."""
        self.extractor = GTEFeatureExtractorV2()
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
        
        print(f"Created focused unified dataset with {len(self.unified_df)} particles and {len(self.feature_df.columns)-1} features")
    
    def create_focused_feature_set(self):
        """Create a focused feature set based on critical insights."""
        print("\n" + "="*80)
        print("CREATING FOCUSED FEATURE SET")
        print("="*80)
        
        # Get basic features
        X = self.feature_df.drop(['particle'], axis=1)
        
        # Create focused feature set
        focused_features = pd.DataFrame()
        
        # 1. Möbius function features (dominant insight)
        print("Adding Möbius function features...")
        focused_features['a_mu'] = X['a_mu']
        focused_features['b_mu'] = X['b_mu']  # Most important from v2.0
        focused_features['c_mu'] = X['c_mu']
        
        # Möbius interactions with modular arithmetic
        focused_features['b_mu_x_b_mod_5'] = X['b_mu'] * X['b_mod_5']  # Key interaction from v2.0
        focused_features['b_mu_x_c_mod_3'] = X['b_mu'] * X['c_mod_3']
        focused_features['a_mu_x_a_mod_3'] = X['a_mu'] * X['a_mod_3']
        
        # 2. Feature X176 and related features
        print("Adding Feature X176 and related features...")
        # X176 was identified as a_omega_x_a_sigma
        focused_features['a_omega_x_a_sigma'] = X['a_omega_x_a_sigma']  # Feature X176
        focused_features['log_a_omega_x_a_sigma'] = np.log(np.abs(X['a_omega_x_a_sigma']) + 1)
        focused_features['sqrt_a_omega_x_a_sigma'] = np.sqrt(np.abs(X['a_omega_x_a_sigma']))
        
        # Related omega and sigma features
        focused_features['a_omega'] = X['a_omega']
        focused_features['a_sigma'] = X['a_sigma']
        focused_features['b_omega'] = X['b_omega']
        focused_features['c_omega'] = X['c_omega']
        
        # 3. Top features from v2.0
        print("Adding top features from v2.0...")
        focused_features['c_raw'] = X['c_raw']  # Second most important
        focused_features['b_mod_5'] = X['b_mod_5']  # Third most important
        focused_features['b_raw'] = X['b_raw']
        focused_features['a_mod_5'] = X['a_mod_5']
        focused_features['c_mod_3'] = X['c_mod_3']
        
        # 4. Key interaction terms from v2.0
        print("Adding key interaction terms...")
        focused_features['b_mod_5_x_c_mod_5'] = X['b_mod_5_x_c_mod_5']
        focused_features['c_mod_3_x_a_omega'] = X['c_mod_3_x_a_omega']
        focused_features['a_mod_3_x_c_mod_3'] = X['a_mod_3_x_c_mod_3']
        focused_features['gcd_bc'] = X['gcd_bc']
        
        # 5. Logarithmic transformations of key features
        print("Adding logarithmic transformations...")
        key_features = ['b_mu', 'c_raw', 'b_mod_5', 'b_raw', 'a_mod_5', 'c_mod_3']
        for feat in key_features:
            if feat in X.columns:
                focused_features[f'log_{feat}'] = np.log(np.abs(X[feat]) + 1)
                focused_features[f'sqrt_{feat}'] = np.sqrt(np.abs(X[feat]))
        
        # 6. Advanced Möbius combinations
        print("Adding advanced Möbius combinations...")
        focused_features['mobius_sum'] = X['a_mu'] + X['b_mu'] + X['c_mu']
        focused_features['mobius_product'] = X['a_mu'] * X['b_mu'] * X['c_mu']
        focused_features['mobius_gcd'] = np.gcd(np.gcd(np.abs(X['a_mu']), np.abs(X['b_mu'])), np.abs(X['c_mu']))
        
        # Möbius ratios
        focused_features['b_mu_div_c_mu'] = np.where(X['c_mu'] != 0, X['b_mu'] / X['c_mu'], 0)
        focused_features['a_mu_div_b_mu'] = np.where(X['b_mu'] != 0, X['a_mu'] / X['b_mu'], 0)
        
        # 7. Modular arithmetic combinations
        print("Adding modular arithmetic combinations...")
        focused_features['mod_sum_5'] = X['a_mod_5'] + X['b_mod_5'] + X['c_mod_5']
        focused_features['mod_sum_3'] = X['a_mod_3'] + X['b_mod_3'] + X['c_mod_3']
        focused_features['mod_product_5'] = X['a_mod_5'] * X['b_mod_5'] * X['c_mod_5']
        focused_features['mod_product_3'] = X['a_mod_3'] * X['b_mod_3'] * X['c_mod_3']
        
        # 8. Composite features
        print("Adding composite features...")
        focused_features['sum_raw'] = X['sum_raw']
        focused_features['product_raw'] = X['product_raw']
        focused_features['gcd_all'] = X['gcd_all']
        
        print(f"Created focused feature set with {len(focused_features.columns)} features")
        
        return focused_features
    
    def discover_charge_mapping_focused(self):
        """Focused discovery of electric charge mapping using critical insights."""
        print("\n" + "="*80)
        print("FOCUSED ELECTRIC CHARGE MAPPING DISCOVERY")
        print("="*80)
        
        # Prepare data
        y = self.target_df['charge']
        print(f"Target values: {y.tolist()}")
        
        # Create focused feature set
        X_focused = self.create_focused_feature_set()
        print(f"Focused feature matrix shape: {X_focused.shape}")
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X_focused)
        X_scaled_df = pd.DataFrame(X_scaled, columns=X_focused.columns)
        
        results = {}
        
        # Method 1: Focused XGBoost (simpler approach)
        if XGBOOST_AVAILABLE:
            print("\n1. Focused XGBoost Analysis:")
            try:
                xgb_model = xgb.XGBRegressor(
                    n_estimators=200,
                    max_depth=4,
                    learning_rate=0.1,
                    subsample=0.9,
                    colsample_bytree=0.9,
                    random_state=42,
                    verbosity=0
                )
                xgb_model.fit(X_scaled_df, y)
                
                xgb_r2 = xgb_model.score(X_scaled_df, y)
                xgb_predictions = xgb_model.predict(X_scaled_df)
                
                print(f"Focused XGBoost R²: {xgb_r2:.4f}")
                
                # Get feature importance
                feature_importance = pd.DataFrame({
                    'feature': X_focused.columns,
                    'importance': xgb_model.feature_importances_
                }).sort_values('importance', ascending=False)
                
                print("Top 15 features by XGBoost importance:")
                print(feature_importance.head(15))
                
                results['xgboost_focused'] = {
                    'r2': xgb_r2,
                    'predictions': xgb_predictions,
                    'feature_importance': feature_importance.to_dict('records')
                }
                
            except Exception as e:
                print(f"Focused XGBoost failed: {e}")
        
        # Method 2: Advanced Lasso with focused features
        print("\n2. Advanced Lasso Analysis:")
        try:
            # Try different alpha values
            alphas = [0.0001, 0.001, 0.01, 0.1]
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
                'feature': X_focused.columns,
                'coefficient': best_lasso_model.coef_
            })
            coef_df = coef_df[coef_df['coefficient'] != 0]
            coef_df['abs_coef'] = np.abs(coef_df['coefficient'])  # type: ignore
            coef_df = coef_df.sort_values('abs_coef', ascending=False).drop('abs_coef', axis=1)  # type: ignore
            
            print("Non-zero Lasso coefficients:")
            print(coef_df.head(15))
            
            results['lasso_focused'] = {
                'r2': best_lasso_r2,
                'alpha': best_lasso_alpha,
                'coefficients': coef_df.to_dict('records'),
                'predictions': best_lasso_model.predict(X_scaled_df)
            }
            
        except Exception as e:
            print(f"Advanced Lasso failed: {e}")
        
        # Method 3: Neural Network with focused features
        print("\n3. Neural Network Analysis:")
        try:
            mlp = MLPRegressor(
                hidden_layer_sizes=(50, 25),
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
            
            results['neural_network_focused'] = {
                'r2': mlp_r2,
                'predictions': mlp_predictions
            }
            
        except Exception as e:
            print(f"Neural Network failed: {e}")
        
        # Method 4: Gradient Boosting with focused features
        print("\n4. Gradient Boosting Analysis:")
        try:
            gb = GradientBoostingRegressor(
                n_estimators=200,
                max_depth=4,
                learning_rate=0.1,
                subsample=0.9,
                random_state=42
            )
            gb.fit(X_scaled_df, y)
            
            gb_r2 = gb.score(X_scaled_df, y)
            gb_predictions = gb.predict(X_scaled_df)
            
            print(f"Gradient Boosting R²: {gb_r2:.4f}")
            
            # Get feature importance
            feature_importance = pd.DataFrame({
                'feature': X_focused.columns,
                'importance': gb.feature_importances_
            }).sort_values('importance', ascending=False)
            
            print("Top 10 features by Gradient Boosting importance:")
            print(feature_importance.head(10))
            
            results['gradient_boosting_focused'] = {
                'r2': gb_r2,
                'predictions': gb_predictions,
                'feature_importance': feature_importance.to_dict('records')
            }
            
        except Exception as e:
            print(f"Gradient Boosting failed: {e}")
        
        # Method 5: Elastic Net (combination of Lasso and Ridge)
        print("\n5. Elastic Net Analysis:")
        try:
            elastic_net = ElasticNet(alpha=0.001, l1_ratio=0.5, random_state=42, max_iter=2000)
            elastic_net.fit(X_scaled_df, y)
            
            en_r2 = elastic_net.score(X_scaled_df, y)
            en_predictions = elastic_net.predict(X_scaled_df)
            
            print(f"Elastic Net R²: {en_r2:.4f}")
            
            results['elastic_net_focused'] = {
                'r2': en_r2,
                'predictions': en_predictions
            }
            
        except Exception as e:
            print(f"Elastic Net failed: {e}")
        
        # Store results
        self.results['charge_focused'] = results
        
        return results
    
    def run_focused_discovery(self):
        """Run the focused discovery protocol."""
        print("FOCUSED ROSETTA STONE DISCOVERY LAB v3.1")
        print("="*80)
        print("Starting focused discovery protocol targeting critical insights...")
        
        # Run focused discovery methods
        self.discover_charge_mapping_focused()
        
        # Generate focused summary
        self.generate_focused_summary()
        
        return self.results
    
    def generate_focused_summary(self):
        """Generate a focused summary of all discoveries."""
        print("\n" + "="*80)
        print("FOCUSED DISCOVERY SUMMARY")
        print("="*80)
        
        for property_name, result in self.results.items():
            print(f"\n{property_name.upper()}:")
            
            if property_name == 'charge_focused':
                print("  Focused Regression Results:")
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
                    elif best_r2 > 0.677:
                        improvement = (best_r2 - 0.677) / 0.677 * 100
                        print(f"  Improvement over v1.0: +{improvement:.2f}%")
    
    def save_focused_results(self, filename='focused_rosetta_stone_results.csv'):
        """Save the focused results."""
        # Save focused feature matrix
        self.feature_df.to_csv(filename, index=False)
        print(f"Focused feature matrix saved to {filename}")


def main():
    """Main execution function for focused discovery."""
    print("Initializing Focused Rosetta Stone Discovery Lab v3.1...")
    
    lab = FocusedRosettaStoneLab()
    
    print("\nRunning focused discovery protocol...")
    results = lab.run_focused_discovery()
    
    print("\nSaving focused results...")
    lab.save_focused_results('focused_feature_matrix.csv')
    
    print("\nFocused discovery protocol completed!")
    return lab, results


if __name__ == "__main__":
    lab, results = main()
