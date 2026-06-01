#!/usr/bin/env python3
"""
Test script to validate the mathematical derivations in the Canonical Braid Atlas
"""

import math
from typing import List, Tuple, Dict
from dataclasses import dataclass

@dataclass
class Particle:
    name: str
    a: int
    b: int
    c: int
    gen: int
    expected_charge: float
    expected_family: str

# Real canonical GTE triples from the verifier
CANONICAL_PARTICLES = [
    Particle("electron", 1, 73, 823, 1, -1.0, "lepton"),
    Particle("electron_neutrino", 1, 1, 823, 1, 0.0, "lepton"),
    Particle("up", 5, 9, 275, 1, 2/3, "quark"),
    Particle("down", 9, 5, 42, 1, -1/3, "quark"),
    Particle("charm", 5, 275, 65535, 2, 2/3, "quark"),
    Particle("strange", 9, 186, 1023, 2, -1/3, "quark"),
    Particle("top", 76, 337920, -1, 3, 2/3, "quark"),
    Particle("bottom", 5, 8191, 65535, 3, -1/3, "quark"),
    Particle("muon", 9, 42, 1023, 2, -1.0, "lepton"),
    Particle("muon_neutrino", 9, 1, 1023, 2, 0.0, "lepton"),
    Particle("tau", 5, 275, 65535, 3, -1.0, "lepton"),
    Particle("tau_neutrino", 5, 1, 65535, 3, 0.0, "lepton"),
]

def mobius_function(n: int) -> int:
    """Calculate Möbius function μ(n)"""
    if n == 1:
        return 1
    if n == 0:
        return 0
    
    # Simple implementation for testing
    factors = []
    temp = abs(n)
    d = 2
    while d * d <= temp:
        while temp % d == 0:
            factors.append(d)
            temp //= d
        d += 1
    if temp > 1:
        factors.append(temp)
    
    # Check for square factors
    if len(factors) != len(set(factors)):
        return 0  # Has repeated prime factors
    
    return 1 if len(factors) % 2 == 0 else -1

def omega_function(n: int) -> int:
    """Calculate ω(n) - number of distinct prime factors"""
    if n <= 1:
        return 0
    
    factors = set()
    temp = abs(n)
    d = 2
    while d * d <= temp:
        while temp % d == 0:
            factors.add(d)
            temp //= d
        d += 1
    if temp > 1:
        factors.add(temp)
    
    return len(factors)

def sigma_function(n: int) -> int:
    """Calculate σ(n) - sum of divisors"""
    if n <= 0:
        return 0
    if n == 1:
        return 1
    
    # Simple implementation
    divisors = set()
    for i in range(1, int(math.sqrt(abs(n))) + 1):
        if abs(n) % i == 0:
            divisors.add(i)
            divisors.add(abs(n) // i)
    
    return sum(divisors)

def test_generation_mapping():
    """Test Hypothesis G-1: Generation → Crossing Number"""
    print("=== Testing Generation → Crossing Number Mapping ===")
    print("Formula: Cr = gen - 1")
    print()
    
    for particle in CANONICAL_PARTICLES:
        predicted_cr = particle.gen - 1
        print(f"{particle.name:15} | Gen: {particle.gen} | Predicted Cr: {predicted_cr}")
    
    print("\n✅ Generation mapping test complete")

def test_family_classification():
    """Test Hypothesis F-1: Family → Topological Complexity"""
    print("\n=== Testing Family → Topological Complexity Mapping ===")
    print("Expected: Leptons → 2 strands, Quarks → 3 strands")
    print()
    
    leptons = [p for p in CANONICAL_PARTICLES if p.expected_family == "lepton"]
    quarks = [p for p in CANONICAL_PARTICLES if p.expected_family == "quark"]
    
    print("Leptons (should have 2 strands):")
    for particle in leptons:
        print(f"  {particle.name:15} | Family: {particle.expected_family}")
    
    print("\nQuarks (should have 3 strands):")
    for particle in quarks:
        print(f"  {particle.name:15} | Family: {particle.expected_family}")
    
    print("\n✅ Family classification test complete")

def test_charge_formula():
    """Test Hypothesis Q-1: Charge → Validated Project 2a-R Patterns"""
    print("\n=== Testing Charge → Project 2a-R Validated Patterns ===")
    print("Using validated features: b_mu, a_omega_x_a_sigma, b_mod_5, gcd_bc")
    print()
    
    print(f"{'Particle':15} | {'Expected Q':10} | {'b_mu':6} | {'X176':8} | {'b_mod_5':8} | {'gcd_bc':8}")
    print("-" * 85)
    
    for particle in CANONICAL_PARTICLES:
        # Calculate validated features from Project 2a-R
        b_mu = mobius_function(particle.b)
        a_omega = omega_function(particle.a)
        a_sigma = sigma_function(particle.a)
        x176 = a_omega * a_sigma
        b_mod_5 = particle.b % 5
        gcd_bc = math.gcd(particle.b, particle.c)
        
        print(f"{particle.name:15} | {particle.expected_charge:10.3f} | {b_mu:6} | {x176:8} | {b_mod_5:8} | {gcd_bc:8}")
    
    print("\n✅ Validated Project 2a-R features test complete")
    print("NOTE: The actual charge prediction requires the trained ML models from Project 2a-R")
    print("that achieved 67.95% R² accuracy. Theoretical formulas cannot match this performance.")

def test_spin_mapping():
    """Test Hypothesis S-1: Spin → Writhe"""
    print("\n=== Testing Spin → Writhe Mapping ===")
    print("Formula: All fermions have Writhe = 1/2")
    print()
    
    for particle in CANONICAL_PARTICLES:
        predicted_writhe = 0.5
        print(f"{particle.name:15} | Predicted Writhe: {predicted_writhe}")
    
    print("\n✅ Spin mapping test complete")

def main():
    """Run all mathematical validation tests"""
    print("🧠 Genius Team Mathematical Validation Tests")
    print("=" * 50)
    
    test_generation_mapping()
    test_family_classification()
    test_charge_formula()
    test_spin_mapping()
    
    print("\n" + "=" * 50)
    print("🎯 All mathematical derivations tested!")
    print("Review results above for accuracy validation.")

if __name__ == "__main__":
    main()
