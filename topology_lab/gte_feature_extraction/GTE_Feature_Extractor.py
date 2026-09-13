"""
GTE Feature Extractor Module

This module extracts number-theoretic features from GTE triples (a, b, c).
It implements all the required features as specified in the Pillar 2a specification.

Author: UGP Research Program
Version: 1.0
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, Union
import sympy as sp
from sympy.ntheory import factorint, mobius, divisor_count, divisor_sigma, primefactors
from sympy.ntheory.factor_ import totient


class GTEFeatureExtractor:
    """
    Extracts comprehensive number-theoretic features from GTE triples.
    
    Features include:
    - Raw values
    - Modular arithmetic (mod 2, 3, 5)
    - Prime factorization properties (Möbius, omega, etc.)
    - Divisor properties (tau, sigma)
    """
    
    def __init__(self):
        """Initialize the feature extractor."""
        self.feature_names = self._generate_feature_names()
    
    def _generate_feature_names(self) -> list:
        """Generate systematic feature names for all combinations."""
        features = []
        components = ['a', 'b', 'c']
        
        # Raw values
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
            return mobius(abs(n))
    
    def _omega_function(self, n: int) -> int:
        """Compute ω(n) - number of distinct prime factors."""
        if n == 0:
            return 0
        elif n == 1 or n == -1:
            return 0
        else:
            return len(primefactors(abs(n)))
    
    def _omega_total_function(self, n: int) -> int:
        """Compute Ω(n) - total number of prime factors with multiplicity."""
        if n == 0:
            return 0
        elif n == 1 or n == -1:
            return 0
        else:
            factors = self._safe_factorint(n)
            return sum(factors.values())
    
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
            return divisor_count(abs(n))
    
    def _sigma_function(self, n: int) -> int:
        """Compute σ(n) - sum of positive divisors."""
        if n == 0:
            return 0
        else:
            return divisor_sigma(abs(n))
    
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
        
        # Raw values
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


def main():
    """Test the feature extractor with sample data."""
    extractor = GTEFeatureExtractor()
    
    # Test with sample triples from the specification
    test_triples = [
        (1, 73, 823),    # electron
        (5, 9, 275),     # up quark
        (9, 5, 42),      # down quark
    ]
    
    print("Testing GTE Feature Extractor")
    print("=" * 50)
    
    for i, triple in enumerate(test_triples):
        print(f"\nTriple {i+1}: {triple}")
        features = extractor.extract_features(triple)
        
        # Show some key features
        key_features = ['a_mu', 'b_omega', 'c_mod_3', 'sum_raw', 'gcd_all']
        for feat in key_features:
            if feat in features:
                print(f"  {feat}: {features[feat]}")
    
    # Test DataFrame extraction
    df = extractor.extract_features_dataframe(test_triples)
    print(f"\nFeature matrix shape: {df.shape}")
    print(f"Number of features: {len(extractor.get_feature_names())}")
    
    print("\nFeature extraction test completed successfully!")


if __name__ == "__main__":
    main()
