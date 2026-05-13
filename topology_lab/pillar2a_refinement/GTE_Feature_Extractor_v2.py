"""
GTE Feature Extractor Module v2.0 - Enhanced Edition

This module extracts comprehensive number-theoretic features from GTE triples (a, b, c),
including interaction terms, non-linear transformations, and ratio features.

Author: UGP Research Program
Version: 2.0 - Refinement Edition
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, Union, List
import sympy as sp
from sympy.ntheory import factorint, mobius, divisor_count, divisor_sigma, primefactors
from sympy.ntheory.factor_ import totient
import itertools
import warnings
warnings.filterwarnings('ignore')


class GTEFeatureExtractorV2:
    """
    Enhanced feature extractor with expanded feature engineering capabilities.
    
    Features include:
    - Raw values and basic modular arithmetic
    - Prime factorization properties (Möbius, omega, etc.)
    - Divisor properties (tau, sigma)
    - Interaction terms (pairwise products)
    - Non-linear transformations (log, square, inverse)
    - Ratio features (component ratios)
    """
    
    def __init__(self, include_interactions=True, include_nonlinear=True, include_ratios=True):
        """
        Initialize the enhanced feature extractor.
        
        Args:
            include_interactions: Whether to include pairwise interaction terms
            include_nonlinear: Whether to include non-linear transformations
            include_ratios: Whether to include ratio features
        """
        self.include_interactions = include_interactions
        self.include_nonlinear = include_nonlinear
        self.include_ratios = include_ratios
        self.feature_names = self._generate_feature_names()
    
    def _generate_feature_names(self) -> list:
        """Generate systematic feature names for all combinations."""
        features = []
        components = ['a', 'b', 'c']
        
        # Basic features (same as v1)
        for comp in components:
            features.append(f"{comp}_raw")
        
        # Modular arithmetic
        moduli = [2, 3, 5]
        for comp in components:
            for mod in moduli:
                features.append(f"{comp}_mod_{mod}")
        
        # Prime factorization properties
        prime_features = ['mu', 'omega', 'omega_total', 'radical', 'max_prime']
        for comp in components:
            for feat in prime_features:
                features.append(f"{comp}_{feat}")
        
        # Divisor properties
        divisor_features = ['tau', 'sigma']
        for comp in components:
            for feat in divisor_features:
                features.append(f"{comp}_{feat}")
        
        # Composite features
        features.extend(['sum_raw', 'product_raw', 'gcd_ab', 'gcd_ac', 'gcd_bc', 'gcd_all'])
        
        # Non-linear transformations
        if self.include_nonlinear:
            for comp in components:
                # Log transformations (with +1 to avoid log(0))
                features.append(f"{comp}_log_raw")
                features.append(f"{comp}_log_tau")
                features.append(f"{comp}_log_sigma")
                features.append(f"{comp}_log_radical")
                
                # Square transformations
                features.append(f"{comp}_square_raw")
                features.append(f"{comp}_square_tau")
                features.append(f"{comp}_square_sigma")
                
                # Inverse transformations (with safe division)
                features.append(f"{comp}_inv_tau")
                features.append(f"{comp}_inv_sigma")
                features.append(f"{comp}_inv_radical")
        
        # Interaction terms
        if self.include_interactions:
            # Get all basic feature names for interactions
            basic_features = [f"{comp}_{feat}" for comp in components 
                            for feat in ['raw', 'mod_2', 'mod_3', 'mod_5', 'mu', 'omega', 'tau', 'sigma']]
            
            # Add pairwise interactions
            for feat1, feat2 in itertools.combinations(basic_features, 2):
                features.append(f"{feat1}_x_{feat2}")
        
        # Ratio features
        if self.include_ratios:
            ratio_features = ['raw', 'tau', 'sigma', 'radical', 'omega']
            for feat in ratio_features:
                features.append(f"a_{feat}_div_b_{feat}")
                features.append(f"a_{feat}_div_c_{feat}")
                features.append(f"b_{feat}_div_c_{feat}")
        
        return features
    
    def _safe_factorint(self, n: int) -> dict:
        """Safely factorize integer, handling edge cases."""
        if n == 0:
            return {0: 1}
        elif n == 1:
            return {}
        elif n == -1:
            return {-1: 1}
        else:
            return factorint(abs(n))
    
    def _mobius_function(self, n: int) -> int:
        """Compute Möbius function μ(n)."""
        if n == 0:
            return 0
        elif n == 1:
            return 1
        elif n == -1:
            return -1
        else:
            return int(mobius(abs(n)))  # type: ignore
    
    def _omega_function(self, n: int) -> int:
        """Compute ω(n) - number of distinct prime factors."""
        if n == 0:
            return 0
        elif n == 1 or n == -1:
            return 0
        else:
            return int(len(primefactors(abs(n))))
    
    def _omega_total_function(self, n: int) -> int:
        """Compute Ω(n) - total number of prime factors with multiplicity."""
        if n == 0:
            return 0
        elif n == 1 or n == -1:
            return 0
        else:
            factors = self._safe_factorint(n)
            return int(sum(factors.values()))
    
    def _radical_function(self, n: int) -> int:
        """Compute rad(n) - product of distinct prime factors."""
        if n == 0:
            return 0
        elif n == 1 or n == -1:
            return 1
        else:
            factors = primefactors(abs(n))
            if not factors:
                return 1
            result = 1
            for p in factors:
                result *= p
            return result
    
    def _max_prime_function(self, n: int) -> int:
        """Compute the largest prime factor of n."""
        if n == 0:
            return 0
        elif n == 1 or n == -1:
            return 1
        else:
            factors = primefactors(abs(n))
            return max(factors) if factors else 1
    
    def _tau_function(self, n: int) -> int:
        """Compute τ(n) - number of positive divisors."""
        if n == 0:
            return 0
        else:
            return int(divisor_count(abs(n)))
    
    def _sigma_function(self, n: int) -> int:
        """Compute σ(n) - sum of positive divisors."""
        if n == 0:
            return 0
        else:
            return int(divisor_sigma(abs(n)))  # type: ignore
    
    def _safe_log(self, x: Union[int, float]) -> float:
        """Safely compute log(1 + x) to avoid log(0)."""
        if x == 0:
            return 0.0
        else:
            return np.log(1 + abs(float(x)))
    
    def _safe_inv(self, x: Union[int, float]) -> float:
        """Safely compute 1/x with handling for x=0."""
        if x == 0:
            return 0.0
        else:
            return 1.0 / abs(float(x))
    
    def _safe_ratio(self, x: Union[int, float], y: Union[int, float]) -> float:
        """Safely compute x/y with handling for y=0."""
        if y == 0:
            return 0.0
        else:
            return float(x) / float(y)
    
    def extract_features(self, triple: Tuple[int, int, int]) -> Dict[str, Union[int, float]]:
        """
        Extract comprehensive features from a GTE triple.
        
        Args:
            triple: Tuple of (a, b, c) integers
            
        Returns:
            Dictionary mapping feature names to values
        """
        a, b, c = triple
        
        features = {}
        
        # Basic features (same as v1)
        features['a_raw'] = a
        features['b_raw'] = b
        features['c_raw'] = c
        
        # Modular arithmetic
        for n, comp in [(a, 'a'), (b, 'b'), (c, 'c')]:
            features[f'{comp}_mod_2'] = n % 2
            features[f'{comp}_mod_3'] = n % 3
            features[f'{comp}_mod_5'] = n % 5
        
        # Prime factorization properties
        for n, comp in [(a, 'a'), (b, 'b'), (c, 'c')]:
            features[f'{comp}_mu'] = self._mobius_function(n)
            features[f'{comp}_omega'] = self._omega_function(n)
            features[f'{comp}_omega_total'] = self._omega_total_function(n)
            features[f'{comp}_radical'] = self._radical_function(n)
            features[f'{comp}_max_prime'] = self._max_prime_function(n)
        
        # Divisor properties
        for n, comp in [(a, 'a'), (b, 'b'), (c, 'c')]:
            features[f'{comp}_tau'] = self._tau_function(n)
            features[f'{comp}_sigma'] = self._sigma_function(n)
        
        # Composite features
        features['sum_raw'] = a + b + c
        features['product_raw'] = a * b * c
        features['gcd_ab'] = np.gcd(abs(a), abs(b)) if a != 0 and b != 0 else 0
        features['gcd_ac'] = np.gcd(abs(a), abs(c)) if a != 0 and c != 0 else 0
        features['gcd_bc'] = np.gcd(abs(b), abs(c)) if b != 0 and c != 0 else 0
        features['gcd_all'] = np.gcd(np.gcd(abs(a), abs(b)), abs(c)) if a != 0 and b != 0 and c != 0 else 0
        
        # Non-linear transformations
        if self.include_nonlinear:
            for n, comp in [(a, 'a'), (b, 'b'), (c, 'c')]:
                # Log transformations
                features[f'{comp}_log_raw'] = self._safe_log(n)
                features[f'{comp}_log_tau'] = self._safe_log(self._tau_function(n))
                features[f'{comp}_log_sigma'] = self._safe_log(self._sigma_function(n))
                features[f'{comp}_log_radical'] = self._safe_log(self._radical_function(n))
                
                # Square transformations
                features[f'{comp}_square_raw'] = n * n
                features[f'{comp}_square_tau'] = self._tau_function(n) ** 2
                features[f'{comp}_square_sigma'] = self._sigma_function(n) ** 2
                
                # Inverse transformations
                features[f'{comp}_inv_tau'] = self._safe_inv(self._tau_function(n))
                features[f'{comp}_inv_sigma'] = self._safe_inv(self._sigma_function(n))
                features[f'{comp}_inv_radical'] = self._safe_inv(self._radical_function(n))
        
        # Interaction terms
        if self.include_interactions:
            # Create interaction features
            basic_features = {
                'a_raw': a, 'b_raw': b, 'c_raw': c,
                'a_mod_2': a % 2, 'b_mod_2': b % 2, 'c_mod_2': c % 2,
                'a_mod_3': a % 3, 'b_mod_3': b % 3, 'c_mod_3': c % 3,
                'a_mod_5': a % 5, 'b_mod_5': b % 5, 'c_mod_5': c % 5,
                'a_mu': self._mobius_function(a), 'b_mu': self._mobius_function(b), 'c_mu': self._mobius_function(c),
                'a_omega': self._omega_function(a), 'b_omega': self._omega_function(b), 'c_omega': self._omega_function(c),
                'a_tau': self._tau_function(a), 'b_tau': self._tau_function(b), 'c_tau': self._tau_function(c),
                'a_sigma': self._sigma_function(a), 'b_sigma': self._sigma_function(b), 'c_sigma': self._sigma_function(c)
            }
            
            # Add pairwise interactions
            for (feat1, val1), (feat2, val2) in itertools.combinations(basic_features.items(), 2):
                features[f"{feat1}_x_{feat2}"] = val1 * val2
        
        # Ratio features
        if self.include_ratios:
            # Raw ratios
            features['a_raw_div_b_raw'] = self._safe_ratio(a, b)
            features['a_raw_div_c_raw'] = self._safe_ratio(a, c)
            features['b_raw_div_c_raw'] = self._safe_ratio(b, c)
            
            # Tau ratios
            features['a_tau_div_b_tau'] = self._safe_ratio(self._tau_function(a), self._tau_function(b))
            features['a_tau_div_c_tau'] = self._safe_ratio(self._tau_function(a), self._tau_function(c))
            features['b_tau_div_c_tau'] = self._safe_ratio(self._tau_function(b), self._tau_function(c))
            
            # Sigma ratios
            features['a_sigma_div_b_sigma'] = self._safe_ratio(self._sigma_function(a), self._sigma_function(b))
            features['a_sigma_div_c_sigma'] = self._safe_ratio(self._sigma_function(a), self._sigma_function(c))
            features['b_sigma_div_c_sigma'] = self._safe_ratio(self._sigma_function(b), self._sigma_function(c))
            
            # Radical ratios
            features['a_radical_div_b_radical'] = self._safe_ratio(self._radical_function(a), self._radical_function(b))
            features['a_radical_div_c_radical'] = self._safe_ratio(self._radical_function(a), self._radical_function(c))
            features['b_radical_div_c_radical'] = self._safe_ratio(self._radical_function(b), self._radical_function(c))
            
            # Omega ratios
            features['a_omega_div_b_omega'] = self._safe_ratio(self._omega_function(a), self._omega_function(b))
            features['a_omega_div_c_omega'] = self._safe_ratio(self._omega_function(a), self._omega_function(c))
            features['b_omega_div_c_omega'] = self._safe_ratio(self._omega_function(b), self._omega_function(c))
        
        return features
    
    def extract_features_dataframe(self, triples: list) -> pd.DataFrame:
        """
        Extract features for multiple triples and return as DataFrame.
        
        Args:
            triples: List of (a, b, c) tuples
            
        Returns:
            DataFrame with features as columns
        """
        feature_dicts = [self.extract_features(triple) for triple in triples]
        return pd.DataFrame(feature_dicts)
    
    def get_feature_names(self) -> list:
        """Return list of all feature names."""
        return self.feature_names.copy()
    
    def get_feature_count(self) -> int:
        """Return total number of features."""
        return len(self.feature_names)


def main():
    """Test the enhanced feature extractor with sample data."""
    extractor = GTEFeatureExtractorV2()
    
    # Test with sample triples from the specification
    test_triples = [
        (1, 73, 823),    # electron
        (5, 9, 275),     # up quark
        (9, 5, 42),      # down quark
    ]
    
    print("Testing Enhanced GTE Feature Extractor v2.0")
    print("=" * 60)
    print(f"Total features: {extractor.get_feature_count()}")
    print(f"Include interactions: {extractor.include_interactions}")
    print(f"Include non-linear: {extractor.include_nonlinear}")
    print(f"Include ratios: {extractor.include_ratios}")
    
    for i, triple in enumerate(test_triples):
        print(f"\nTriple {i+1}: {triple}")
        features = extractor.extract_features(triple)
        
        # Show some key features
        key_features = ['a_mu', 'b_omega', 'c_mod_3', 'sum_raw', 'gcd_all']
        for feat in key_features:
            if feat in features:
                print(f"  {feat}: {features[feat]}")
        
        # Show some interaction features
        interaction_features = [k for k in features.keys() if '_x_' in k][:3]
        for feat in interaction_features:
            print(f"  {feat}: {features[feat]}")
        
        # Show some ratio features
        ratio_features = [k for k in features.keys() if '_div_' in k][:3]
        for feat in ratio_features:
            print(f"  {feat}: {features[feat]}")
    
    # Test DataFrame extraction
    df = extractor.extract_features_dataframe(test_triples)
    print(f"\nFeature matrix shape: {df.shape}")
    print(f"Number of features: {len(extractor.get_feature_names())}")
    
    print("\nEnhanced feature extraction test completed successfully!")


if __name__ == "__main__":
    main()
