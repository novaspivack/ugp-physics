"""
Rosetta Stone Discovery Lab

This module implements the experimental harness for discovering the mapping
between GTE triples and particle quantum numbers using interpretable ML methods.

Author: UGP Research Program
Version: 1.0
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.linear_model import LogisticRegression, Lasso
from sklearn.metrics import accuracy_score, f1_score, r2_score, mean_squared_error
from sklearn.model_selection import cross_val_score
import warnings
warnings.filterwarnings('ignore')

# Import our feature extractor
from GTE_Feature_Extractor import GTEFeatureExtractor

# Try to import gplearn for symbolic regression
try:
    from gplearn.genetic import SymbolicRegressor, SymbolicClassifier  # type: ignore
    from gplearn.functions import make_function  # type: ignore
    GPLEARN_AVAILABLE = True
except ImportError:
    print("Warning: gplearn not available. Symbolic regression will be skipped.")
    GPLEARN_AVAILABLE = False


class RosettaStoneLab:
    """
    Main experimental harness for discovering the GTE-to-Physics mapping.
    """
    
    def __init__(self):
        """Initialize the lab with canonical data."""
        self.extractor = GTEFeatureExtractor()
        self.load_canonical_data()
        self.results = {}
        
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
        """Create unified dataset with features and targets."""
        
        # Extract features for all particles
        particles = list(self.gte_data.keys())
        triples = [self.gte_data[p] for p in particles]
        
        # Create feature matrix
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
        
        print(f"Created unified dataset with {len(self.unified_df)} particles and {len(self.feature_df.columns)-1} features")
    
    def discover_charge_mapping(self):
        """Discover the mapping for electric charge."""
        print("\n" + "="*60)
        print("DISCOVERING ELECTRIC CHARGE MAPPING")
        print("="*60)
        
        # Prepare data
        X = self.feature_df.drop(['particle'], axis=1)
        y = self.target_df['charge']
        
        print(f"Target values: {y.tolist()}")
        
        # Method 1: Decision Tree
        print("\n1. Decision Tree Analysis:")
        dt_reg = DecisionTreeRegressor(max_depth=3, random_state=42)
        dt_reg.fit(X, y)
        
        # Get feature importance
        feature_importance = pd.DataFrame({
            'feature': X.columns,
            'importance': dt_reg.score(X, y)
        }).sort_values('importance', ascending=False)
        
        print("Top features by importance:")
        print(feature_importance.head(10))
        
        # Method 2: Lasso Regression
        print("\n2. Lasso Regression Analysis:")
        lasso = Lasso(alpha=0.01, random_state=42)
        lasso.fit(X, y)
        
        # Get non-zero coefficients
        coef_df = pd.DataFrame({
            'feature': X.columns,
            'coefficient': lasso.coef_
        })
        coef_df = coef_df[coef_df['coefficient'] != 0]
        coef_df['abs_coef'] = np.abs(coef_df['coefficient'])  # type: ignore
        coef_df = coef_df.sort_values('abs_coef', ascending=False).drop('abs_coef', axis=1)  # type: ignore
        
        print("Non-zero Lasso coefficients:")
        print(coef_df)
        
        # Method 3: Symbolic Regression (if available)
        if GPLEARN_AVAILABLE:
            print("\n3. Symbolic Regression Analysis:")
            try:
                sr = SymbolicRegressor(
                    population_size=1000,
                    generations=20,
                    stopping_criteria=0.01,
                    p_crossover=0.7,
                    p_subtree_mutation=0.1,
                    p_hoist_mutation=0.05,
                    p_point_mutation=0.1,
                    max_samples=0.9,
                    verbose=1,
                    parsimony_coefficient=0.01,
                    random_state=42
                )
                sr.fit(X, y)
                
                print(f"Best formula: {sr._program}")
                print(f"R² score: {sr.score(X, y):.4f}")
                
                # Store results
                self.results['charge'] = {
                    'method': 'symbolic_regression',
                    'formula': str(sr._program),
                    'score': sr.score(X, y),
                    'predictions': sr.predict(X)
                }
                
            except Exception as e:
                print(f"Symbolic regression failed: {e}")
        
        # Store simple results
        self.results['charge'] = {
            'method': 'lasso',
            'coefficients': coef_df.to_dict('records'),
            'score': lasso.score(X, y),
            'predictions': lasso.predict(X)
        }
        
        return self.results['charge']
    
    def discover_spin_mapping(self):
        """Discover the mapping for spin."""
        print("\n" + "="*60)
        print("DISCOVERING SPIN MAPPING")
        print("="*60)
        
        # Prepare data
        X = self.feature_df.drop(['particle'], axis=1)
        y = self.target_df['spin']
        
        print(f"Target values: {y.tolist()}")
        
        # Since all particles have spin 1/2, this is a constant prediction
        print("\nNote: All fundamental fermions have spin 1/2")
        print("This suggests spin may be a fundamental property not derived from GTE triples")
        
        # Still run analysis to see if there are any patterns
        dt_reg = DecisionTreeRegressor(max_depth=2, random_state=42)
        dt_reg.fit(X, y)
        
        print(f"Decision tree R²: {dt_reg.score(X, y):.4f}")
        
        self.results['spin'] = {
            'method': 'constant',
            'value': 0.5,
            'note': 'All fundamental fermions have spin 1/2'
        }
        
        return self.results['spin']
    
    def discover_family_mapping(self):
        """Discover the mapping for particle family (Lepton/Quark)."""
        print("\n" + "="*60)
        print("DISCOVERING FAMILY MAPPING")
        print("="*60)
        
        # Prepare data
        X = self.feature_df.drop(['particle'], axis=1)
        y = self.target_df['family']
        
        print(f"Target values: {y.tolist()}")
        
        # Method 1: Decision Tree
        print("\n1. Decision Tree Analysis:")
        dt_clf = DecisionTreeClassifier(max_depth=3, random_state=42)
        dt_clf.fit(X, y)
        
        accuracy = dt_clf.score(X, y)
        print(f"Decision tree accuracy: {accuracy:.4f}")
        
        # Get feature importance
        feature_importance = pd.DataFrame({
            'feature': X.columns,
            'importance': dt_clf.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("Top features by importance:")
        print(feature_importance.head(10))
        
        # Method 2: Logistic Regression
        print("\n2. Logistic Regression Analysis:")
        lr = LogisticRegression(random_state=42, max_iter=1000)
        lr.fit(X, y)
        
        # Get coefficients
        coef_df = pd.DataFrame({
            'feature': X.columns,
            'coefficient': lr.coef_[0]
        }).sort_values('coefficient', key=abs, ascending=False)
        
        print("Top coefficients:")
        print(coef_df.head(10))
        
        # Method 3: Symbolic Classification (if available)
        if GPLEARN_AVAILABLE:
            print("\n3. Symbolic Classification Analysis:")
            try:
                sc = SymbolicClassifier(
                    population_size=1000,
                    generations=20,
                    stopping_criteria=0.01,
                    p_crossover=0.7,
                    p_subtree_mutation=0.1,
                    p_hoist_mutation=0.05,
                    p_point_mutation=0.1,
                    max_samples=0.9,
                    verbose=1,
                    parsimony_coefficient=0.01,
                    random_state=42
                )
                sc.fit(X, y)
                
                print(f"Best formula: {sc._program}")
                print(f"Accuracy: {sc.score(X, y):.4f}")
                
                self.results['family'] = {
                    'method': 'symbolic_classification',
                    'formula': str(sc._program),
                    'accuracy': sc.score(X, y),
                    'predictions': sc.predict(X)
                }
                
            except Exception as e:
                print(f"Symbolic classification failed: {e}")
        
        # Store results
        self.results['family'] = {
            'method': 'logistic_regression',
            'coefficients': coef_df.to_dict('records'),
            'accuracy': lr.score(X, y),
            'predictions': lr.predict(X)
        }
        
        return self.results['family']
    
    def discover_generation_mapping(self):
        """Discover the mapping for generation."""
        print("\n" + "="*60)
        print("DISCOVERING GENERATION MAPPING")
        print("="*60)
        
        # Prepare data
        X = self.feature_df.drop(['particle'], axis=1)
        y = self.target_df['generation']
        
        print(f"Target values: {y.tolist()}")
        
        # Method 1: Decision Tree
        print("\n1. Decision Tree Analysis:")
        dt_clf = DecisionTreeClassifier(max_depth=3, random_state=42)
        dt_clf.fit(X, y)
        
        accuracy = dt_clf.score(X, y)
        print(f"Decision tree accuracy: {accuracy:.4f}")
        
        # Get feature importance
        feature_importance = pd.DataFrame({
            'feature': X.columns,
            'importance': dt_clf.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("Top features by importance:")
        print(feature_importance.head(10))
        
        # Store results
        self.results['generation'] = {
            'method': 'decision_tree',
            'accuracy': accuracy,
            'feature_importance': feature_importance.to_dict('records')
        }
        
        return self.results['generation']
    
    def run_full_discovery(self):
        """Run the complete discovery protocol."""
        print("ROSETTA STONE DISCOVERY LAB")
        print("="*60)
        print("Starting comprehensive discovery protocol...")
        
        # Run all discovery methods
        self.discover_charge_mapping()
        self.discover_spin_mapping()
        self.discover_family_mapping()
        self.discover_generation_mapping()
        
        # Generate summary
        self.generate_summary()
        
        return self.results
    
    def generate_summary(self):
        """Generate a summary of all discoveries."""
        print("\n" + "="*60)
        print("DISCOVERY SUMMARY")
        print("="*60)
        
        for property_name, result in self.results.items():
            print(f"\n{property_name.upper()}:")
            print(f"  Method: {result['method']}")
            if 'score' in result:
                print(f"  Score: {result['score']:.4f}")
            elif 'accuracy' in result:
                print(f"  Accuracy: {result['accuracy']:.4f}")
            if 'formula' in result:
                print(f"  Formula: {result['formula']}")
    
    def save_results(self, filename='rosetta_stone_results.csv'):
        """Save the feature matrix and results."""
        # Save feature matrix
        self.feature_df.to_csv(filename, index=False)
        print(f"Feature matrix saved to {filename}")
        
        # Save unified dataset
        unified_filename = filename.replace('.csv', '_unified.csv')
        self.unified_df.to_csv(unified_filename, index=False)
        print(f"Unified dataset saved to {unified_filename}")


def main():
    """Main execution function."""
    print("Initializing Rosetta Stone Discovery Lab...")
    
    lab = RosettaStoneLab()
    
    print("\nRunning full discovery protocol...")
    results = lab.run_full_discovery()
    
    print("\nSaving results...")
    lab.save_results('feature_matrix.csv')
    
    print("\nDiscovery protocol completed!")
    return lab, results


if __name__ == "__main__":
    lab, results = main()
