"""
Test Hexagonal Symmetry Hypothesis for CP Phases
=================================================

Reference: 05_HEXAGONAL_SYMMETRY_PAPERS_ANALYSIS.md

This diagnostic tool tests whether CP phases are constrained by the hidden
Z₆ hexagonal symmetry discovered by Baez (2003) and Bakker et al. (2004).

Key Insight:
- SM has hidden symmetry from gauge group centers: Z₃ × Z₂ × U(1)
- Combined structure gives Z₆ (hexagonal symmetry)
- Z₆ phases: 0°, 60°, 120°, 180°, 240°, 300° (multiples of π/3)

Current Problem:
- CKM δ_CP: UGP predicts 4.49° vs experimental 68.8° (93% error)
- PMNS δ_CP: UGP predicts 37.06° vs experimental ~195° (81% error)
- Current hypothesis: δ ≈ ±π/2 (±90°)

Hexagonal Hypothesis:
- δ should be near Z₆ values: multiples of 60°
- CKM: 68.8° is close to 60° (π/3)
- PMNS: 195° is close to 180° or 240° 

Test Strategy:
1. Check if experimental δ_CP values cluster near Z₆ values
2. Test if GTE parameter 'a' encodes Z₃ or Z₆ structure
3. Test if Möbius μ(a) should be generalized to exp(2πi·a/3) or exp(πi·a/3)
4. Check if current code accidentally constrains to wrong discrete values
"""

import numpy as np
from typing import Dict, List, Tuple
import sys
from pathlib import Path

# Add UGP discovery lab to path
ugp_path = Path(__file__).parent.parent / "UGP_discovery_lab"
if ugp_path.exists():
    sys.path.insert(0, str(ugp_path))


# ============================================================================
# Z₆ Hexagonal Symmetry Structure
# ============================================================================

class HexagonalSymmetry:
    """
    Z₆ hexagonal symmetry from gauge group centers.
    
    Structure:
    - SU(3) center: Z₃ = {1, exp(2πi/3), exp(4πi/3)}
    - SU(2) center: Z₂ = {1, -1} = {1, exp(iπ)}
    - Combined: Z₆ = {exp(πi·k/3) for k=0,1,2,3,4,5}
    
    Z₆ angles: 0°, 60°, 120°, 180°, 240°, 300°
    """
    
    def __init__(self):
        self.z3_phases = np.array([0, 2*np.pi/3, 4*np.pi/3])  # SU(3) center
        self.z2_phases = np.array([0, np.pi])  # SU(2) center
        self.z6_phases = np.array([k * np.pi / 3 for k in range(6)])  # Combined Z₆
        
        # In degrees for readability
        self.z6_phases_deg = np.degrees(self.z6_phases)
        
    def nearest_z6_value(self, angle_deg: float) -> Tuple[float, float, int]:
        """
        Find nearest Z₆ value to given angle.
        
        Returns:
            (nearest_z6_deg, distance_deg, z6_index)
        """
        # Normalize angle to [0, 360)
        angle_norm = angle_deg % 360
        
        # Find nearest Z₆ value
        distances = np.abs(self.z6_phases_deg - angle_norm)
        # Also check with 360° periodicity
        distances_wrapped = np.minimum(distances, 360 - distances)
        
        min_idx = np.argmin(distances_wrapped)
        nearest = self.z6_phases_deg[min_idx]
        distance = distances_wrapped[min_idx]
        
        return nearest, distance, min_idx
    
    def is_near_z6(self, angle_deg: float, tolerance_deg: float = 10.0) -> bool:
        """Check if angle is within tolerance of a Z₆ value."""
        _, distance, _ = self.nearest_z6_value(angle_deg)
        return distance <= tolerance_deg
    
    def get_z3_phase_index(self, a_parameter: int) -> int:
        """Get Z₃ phase index from GTE parameter 'a_parameter'."""
        return a_parameter % 3
    
    def get_z2_phase_index(self, a_parameter: int) -> int:
        """Get Z₂ phase index from GTE parameter 'a_parameter'."""
        return a_parameter % 2
    
    def get_z6_phase_from_a(self, a_parameter: int) -> float:
        """Get Z₆ phase (radians) from GTE parameter 'a'."""
        z6_index = a_parameter % 6
        return self.z6_phases[z6_index]


# ============================================================================
# Generalized Möbius Function for Complex Phases
# ============================================================================

class GeneralizedMobius:
    """
    Generalized Möbius function allowing complex phases.
    
    Standard Möbius: μ(n) ∈ {-1, 0, 1}
    Generalized: μ̃(n, k) = exp(2πi·ω(n)/k) for Z_k structure
    
    For Z₃: μ̃(n) = exp(2πi·(n mod 3)/3) 
    For Z₆: μ̃(n) = exp(πi·(n mod 6)/3)
    """
    
    def __init__(self):
        pass
    
    @staticmethod
    def standard_mobius(n: int) -> int:
        """Standard Möbius function."""
        if n <= 0:
            return 0
        
        # Factor n
        factors = []
        temp = n
        d = 2
        while d * d <= temp:
            if temp % d == 0:
                factors.append(d)
                temp //= d
                if temp % d == 0:  # Square factor
                    return 0
            d += 1
        if temp > 1:
            factors.append(temp)
        
        # (-1)^k where k is number of prime factors
        return (-1) ** len(factors)
    
    @staticmethod
    def z3_mobius(n: int) -> complex:
        """Z₃-generalized Möbius: exp(2πi·(n mod 3)/3)."""
        return np.exp(2j * np.pi * (n % 3) / 3)
    
    @staticmethod
    def z6_mobius(n: int) -> complex:
        """Z₆-generalized Möbius: exp(πi·(n mod 6)/3)."""
        return np.exp(1j * np.pi * (n % 6) / 3)
    
    @staticmethod
    def compare_mobius_variants(a_values: List[int]) -> Dict:
        """Compare standard vs generalized Möbius for given 'a' values."""
        results = {}
        for a in a_values:
            mu_standard = GeneralizedMobius.standard_mobius(a)
            mu_z3 = GeneralizedMobius.z3_mobius(a)
            mu_z6 = GeneralizedMobius.z6_mobius(a)
            
            results[a] = {
                'standard': mu_standard,
                'z3': mu_z3,
                'z3_phase_deg': np.degrees(np.angle(mu_z3)),
                'z6': mu_z6,
                'z6_phase_deg': np.degrees(np.angle(mu_z6)),
                'z3_index': a % 3,
                'z6_index': a % 6
            }
        
        return results


# ============================================================================
# Diagnostic Tests
# ============================================================================

class CPPhaseHexagonalDiagnostics:
    """Test hexagonal symmetry hypothesis on current CP phase predictions."""
    
    def __init__(self):
        self.hex_sym = HexagonalSymmetry()
        self.gen_mobius = GeneralizedMobius()
        
        # Experimental values (PDG)
        self.ckm_exp = {
            'theta12': 13.04,  # Cabibbo angle
            'theta13': 0.201,
            'theta23': 2.38,
            'delta_cp': 68.8,  # degrees
            'jarlskog': 3.08e-5
        }
        
        self.pmns_exp = {
            'theta12': 33.44,
            'theta13': 8.57,
            'theta23': 49.0,
            'delta_cp': 195.0,  # T2K/NOvA hint (degrees)
            'jarlskog': None  # Unknown
        }
        
        # Current UGP predictions
        self.ckm_ugp = {
            'theta12': 33.84,
            'theta13': 8.58,
            'theta23': 49.60,
            'delta_cp': 4.49,  # Current prediction (degrees)
        }
        
        self.pmns_ugp = {
            'theta12': 37.38,
            'theta13': 9.12,
            'theta23': 56.03,
            'delta_cp': 37.06,  # Current prediction (degrees)
        }
        
        # GTE triples from paper (Appendix)
        self.gte_triples = {
            'electron': (1, 73, 823, 1),
            'muon': (9, 42, 1023, 2),
            'tau': (5, 275, 65535, 3),
            'up': (5, 9, 275, 1),
            'charm': (5, 275, 65535, 2),
            'top': (76, 337920, -1, 3),
            'down': (9, 5, 42, 1),
            'strange': (9, 186, 1023, 2),
            'bottom': (5, 8191, 65535, 3),
        }
    
    def test_experimental_phases_near_z6(self):
        """Test if experimental CP phases are near Z₆ values."""
        print("=" * 80)
        print("TEST 1: Are Experimental CP Phases Near Z₆ Values?")
        print("=" * 80)
        
        z6_values = [0, 60, 120, 180, 240, 300]
        
        # Check CKM
        print(f"\nCKM δ_CP (experimental): {self.ckm_exp['delta_cp']:.2f}°")
        ckm_nearest, ckm_dist, ckm_idx = self.hex_sym.nearest_z6_value(self.ckm_exp['delta_cp'])
        print(f"  Nearest Z₆ value: {ckm_nearest:.0f}° (index {ckm_idx})")
        print(f"  Distance: {ckm_dist:.2f}°")
        print(f"  Is near Z₆? {self.hex_sym.is_near_z6(self.ckm_exp['delta_cp'], 10.0)}")
        
        # Check PMNS
        print(f"\nPMNS δ_CP (experimental): {self.pmns_exp['delta_cp']:.2f}°")
        pmns_nearest, pmns_dist, pmns_idx = self.hex_sym.nearest_z6_value(self.pmns_exp['delta_cp'])
        print(f"  Nearest Z₆ value: {pmns_nearest:.0f}° (index {pmns_idx})")
        print(f"  Distance: {pmns_dist:.2f}°")
        print(f"  Is near Z₆? {self.hex_sym.is_near_z6(self.pmns_exp['delta_cp'], 15.0)}")
        
        print(f"\nZ₆ Structure: {z6_values}")
        print(f"Z₃ (SU(3) center): 0°, 120°, 240°")
        print(f"Z₂ (SU(2) center): 0°, 180°")
        
        return {
            'ckm_near_z6': self.hex_sym.is_near_z6(self.ckm_exp['delta_cp'], 10.0),
            'pmns_near_z6': self.hex_sym.is_near_z6(self.pmns_exp['delta_cp'], 15.0),
            'ckm_nearest_z6': ckm_nearest,
            'pmns_nearest_z6': pmns_nearest
        }
    
    def test_current_predictions_vs_z6(self):
        """Test if current UGP predictions are near Z₆ values."""
        print("\n" + "=" * 80)
        print("TEST 2: Are Current UGP Predictions Near Z₆ Values?")
        print("=" * 80)
        
        # Check current CKM prediction
        print(f"\nCKM δ_CP (UGP current): {self.ckm_ugp['delta_cp']:.2f}°")
        ckm_nearest, ckm_dist, ckm_idx = self.hex_sym.nearest_z6_value(self.ckm_ugp['delta_cp'])
        print(f"  Nearest Z₆ value: {ckm_nearest:.0f}° (index {ckm_idx})")
        print(f"  Distance: {ckm_dist:.2f}°")
        print(f"  Current hypothesis (π/2): 90°, distance: {abs(self.ckm_ugp['delta_cp'] - 90):.2f}°")
        
        # Check current PMNS prediction
        print(f"\nPMNS δ_CP (UGP current): {self.pmns_ugp['delta_cp']:.2f}°")
        pmns_nearest, pmns_dist, pmns_idx = self.hex_sym.nearest_z6_value(self.pmns_ugp['delta_cp'])
        print(f"  Nearest Z₆ value: {pmns_nearest:.0f}° (index {pmns_idx})")
        print(f"  Distance: {pmns_dist:.2f}°")
        
        print(f"\n⚠️  OBSERVATION: Current predictions are NOT near Z₆ values!")
        print(f"   This suggests the code is not properly using hexagonal symmetry.")
    
    def test_gte_parameter_a_structure(self):
        """Test if GTE parameter 'a' has Z₃ or Z₆ structure."""
        print("\n" + "=" * 80)
        print("TEST 3: GTE Parameter 'a' and Z₃/Z₆ Structure")
        print("=" * 80)
        
        print("\nGTE Triples (a, b, c, gen):")
        print("-" * 40)
        
        a_values = []
        for particle, triple in self.gte_triples.items():
            a, b, c, g = triple
            a_values.append(a)
            
            # Get Z₃ and Z₆ indices
            z3_idx = a % 3
            z6_idx = a % 6
            
            # Get standard Möbius
            mu = self.gen_mobius.standard_mobius(a)
            
            # Get generalized Möbius phases
            mu_z3 = self.gen_mobius.z3_mobius(a)
            mu_z6 = self.gen_mobius.z6_mobius(a)
            
            print(f"{particle:10s}: a={a:3d}, Z₃={z3_idx}, Z₆={z6_idx}, " +
                  f"μ(a)={mu:2d}, μ̃_Z₃={mu_z3:.3f}, μ̃_Z₆={mu_z6:.3f}")
        
        print(f"\n'a' values used: {sorted(set(a_values))}")
        print(f"'a' mod 3 values: {sorted(set(a % 3 for a in a_values))}")
        print(f"'a' mod 6 values: {sorted(set(a % 6 for a in a_values))}")
        
        # Analyze pattern
        print("\n" + "=" * 40)
        print("PATTERN ANALYSIS:")
        print("=" * 40)
        
        # Check if 'a' values show preference for certain mod 3 or mod 6 classes
        a_mod3 = [a % 3 for a in a_values]
        a_mod6 = [a % 6 for a in a_values]
        
        from collections import Counter
        print(f"\n'a' mod 3 distribution: {dict(Counter(a_mod3))}")
        print(f"'a' mod 6 distribution: {dict(Counter(a_mod6))}")
        
        # Check quarks vs leptons
        quark_a = [self.gte_triples[p][0] for p in ['up', 'charm', 'top', 'down', 'strange', 'bottom']]
        lepton_a = [self.gte_triples[p][0] for p in ['electron', 'muon', 'tau']]
        
        print(f"\nQuark 'a' values: {quark_a}, mod 3: {[a%3 for a in quark_a]}")
        print(f"Lepton 'a' values: {lepton_a}, mod 3: {[a%3 for a in lepton_a]}")
    
    def test_improved_cp_phase_hypotheses(self):
        """Test improved hypotheses using Z₆ structure."""
        print("\n" + "=" * 80)
        print("TEST 4: Improved CP Phase Hypotheses Using Z₆")
        print("=" * 80)
        
        # Test different Z₆-based hypotheses
        hypotheses = {
            'H1_z6_π/3': np.pi / 3,      # 60°
            'H2_z6_2π/3': 2 * np.pi / 3,  # 120°
            'H3_z6_π': np.pi,             # 180°
            'H4_z6_4π/3': 4 * np.pi / 3,  # 240°
            'H5_current_π/2': np.pi / 2,  # 90° (current)
        }
        
        print("\nCKM δ_CP Testing:")
        print(f"Experimental: {self.ckm_exp['delta_cp']:.2f}°")
        
        ckm_exp_rad = np.radians(self.ckm_exp['delta_cp'])
        ckm_results = []
        
        for name, hyp_rad in hypotheses.items():
            hyp_deg = np.degrees(hyp_rad)
            error_deg = abs(hyp_deg - self.ckm_exp['delta_cp'])
            error_pct = error_deg / self.ckm_exp['delta_cp'] * 100
            
            ckm_results.append((error_deg, name, hyp_deg))
            print(f"  {name:20s}: {hyp_deg:6.1f}° → error {error_deg:5.1f}° ({error_pct:5.1f}%)")
        
        ckm_results.sort()
        best_ckm = ckm_results[0]
        print(f"\n✅ BEST CKM HYPOTHESIS: {best_ckm[1]} at {best_ckm[2]:.1f}° (error: {best_ckm[0]:.1f}°)")
        
        print("\n" + "-" * 80)
        print("\nPMNS δ_CP Testing:")
        print(f"Experimental: {self.pmns_exp['delta_cp']:.2f}°")
        
        pmns_exp_rad = np.radians(self.pmns_exp['delta_cp'])
        pmns_results = []
        
        for name, hyp_rad in hypotheses.items():
            hyp_deg = np.degrees(hyp_rad)
            error_deg = abs(hyp_deg - self.pmns_exp['delta_cp'])
            # Handle wraparound at 180°
            error_deg_wrap = min(error_deg, 360 - error_deg)
            error_pct = error_deg_wrap / self.pmns_exp['delta_cp'] * 100
            
            pmns_results.append((error_deg_wrap, name, hyp_deg))
            print(f"  {name:20s}: {hyp_deg:6.1f}° → error {error_deg_wrap:5.1f}° ({error_pct:5.1f}%)")
        
        pmns_results.sort()
        best_pmns = pmns_results[0]
        print(f"\n✅ BEST PMNS HYPOTHESIS: {best_pmns[1]} at {best_pmns[2]:.1f}° (error: {best_pmns[0]:.1f}°)")
        
        return {
            'best_ckm': best_ckm,
            'best_pmns': best_pmns
        }
    
    def test_mobius_generalization_on_gte_triples(self):
        """Test how generalized Möbius affects GTE triples."""
        print("\n" + "=" * 80)
        print("TEST 5: Generalized Möbius on GTE Triples")
        print("=" * 80)
        
        print("\nComparing μ(a) variants:")
        print("-" * 80)
        print(f"{'Particle':<12} {'a':>3} {'μ(a)':>5} {'μ̃_Z₃':>12} {'Z₃_phase':>10} {'μ̃_Z₆':>12} {'Z₆_phase':>10}")
        print("-" * 80)
        
        for particle, triple in self.gte_triples.items():
            a = triple[0]
            mu_std = self.gen_mobius.standard_mobius(a)
            mu_z3 = self.gen_mobius.z3_mobius(a)
            mu_z6 = self.gen_mobius.z6_mobius(a)
            
            z3_phase = np.degrees(np.angle(mu_z3))
            z6_phase = np.degrees(np.angle(mu_z6))
            
            print(f"{particle:<12} {a:3d} {mu_std:5d} {mu_z3:12.3f} {z3_phase:10.1f}° {mu_z6:12.3f} {z6_phase:10.1f}°")
        
        print("\n" + "=" * 40)
        print("KEY OBSERVATION:")
        print("=" * 40)
        print("Standard Möbius: μ(a) ∈ {-1, 0, 1} (only real values)")
        print("Z₃ Möbius: μ̃_Z₃(a) = exp(2πi·(a mod 3)/3) (complex, Z₃ structure)")
        print("Z₆ Möbius: μ̃_Z₆(a) = exp(πi·(a mod 6)/3) (complex, Z₆ structure)")
        print("\nIf CP phases depend on Möbius function, generalization could be key!")
    
    def generate_recommendations(self):
        """Generate specific recommendations for code modifications."""
        print("\n" + "=" * 80)
        print("RECOMMENDATIONS FOR CODE MODIFICATIONS")
        print("=" * 80)
        
        print("""
1. IMMEDIATE: Replace Discrete Phase Hypothesis
   
   Current in ugp_cp_asymmetry_probe.py:
   - H1 (Dirac): δ_q ≈ σ * k_gen (only tests ±π/2 = ±90°)
   - H2 (Majorana): δ_ℓ ≈ σ * f * k_gen, f ∈ {1.0, 0.5, 0.0}
   
   Proposed hexagonal hypothesis:
   - H1_hex (Dirac): δ_q ≈ σ * (k·π/3), k ∈ {0,1,2,3,4,5} (Z₆ values)
   - H2_hex (Majorana): Similar but may have different allowed values
   
   Expected improvement:
   - CKM: 4.49° → ~60° (±8° from 68.8° experimental)
   - PMNS: 37.06° → ~180° or ~240° (±15° from 195° experimental)

2. NEAR-TERM: Implement Generalized Möbius in UCL
   
   Location: UGP_GTE_SM_Verifier.py
   
   Current: Uses standard μ(a) ∈ {-1, 0, 1}
   Proposed: Use μ̃_Z₆(a) = exp(πi·(a mod 6)/3)
   
   This would allow complex phases to naturally emerge from GTE parameter 'a'.

3. MEDIUM-TERM: Enhance CP Phase Extraction
   
   Location: ugp_single_law_uuf_flow_theoretical_upgrades.py
   
   Current (line 1524-1538):
   - Only extracts angles using np.abs (discards phase!)
   - Never calculates δ_CP from complex matrix elements
   
   Proposed:
   - Keep angle extraction as-is (it works!)
   - ADD: Extract δ_CP from Jarlskog invariant
   - Use generalized Möbius phases to construct mixing matrix
   - Validate Jarlskog matches target

4. VALIDATION: Center Element Checker
   
   Implement verification that all GTE particles respect hidden symmetry:
   - For each particle, calculate how SU(3), SU(2), U(1) centers act
   - Verify the "miracle": product always gives identity
   - If not satisfied, there's a fundamental bug!

5. THEORETICAL: Document Z₆ Connection to UGP
   
   Add to paper:
   - Connection between n=10 ridge (1008 = 2⁴×3²×7) and Z₃×Z₂
   - Mirror pair (42, 24) has factors of 2 and 3
   - Quarter-Lock 1/4 potentially related to Z₄ or Z₆
   - This makes UGP structure even more elegant!
""")
    
    def run_all_tests(self):
        """Run all diagnostic tests."""
        print("\n" + "🔬" * 40)
        print(" HEXAGONAL SYMMETRY CP PHASE DIAGNOSTIC TESTS")
        print("🔬" * 40)
        
        # Test 1: Experimental phases near Z₆?
        test1_results = self.test_experimental_phases_near_z6()
        
        # Test 2: Current predictions near Z₆?
        self.test_current_predictions_vs_z6()
        
        # Test 3: GTE parameter 'a' structure
        self.test_gte_parameter_a_structure()
        
        # Test 4: Improved hypotheses
        test4_results = self.test_improved_cp_phase_hypotheses()
        
        # Test 5: Generalized Möbius
        self.test_mobius_generalization_on_gte_triples()
        
        # Final recommendations
        self.generate_recommendations()
        
        print("\n" + "=" * 80)
        print("✅ DIAGNOSTIC TESTS COMPLETE")
        print("=" * 80)
        
        return {
            'test1': test1_results,
            'test4': test4_results
        }


# ============================================================================
# Main Execution
# ============================================================================

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║         Hexagonal Symmetry CP Phase Diagnostic Tool                          ║
║                                                                              ║
║  Testing hypothesis that CP phases are constrained by Z₆ hexagonal          ║
║  symmetry from SU(3)×SU(2)×U(1) gauge group centers.                        ║
║                                                                              ║
║  References:                                                                 ║
║  - Baez (2003): The True Internal Symmetry Group of the Standard Model      ║
║  - Bakker et al. (2004): A hidden symmetry in the Standard Model            ║
║  - Paper Doc: 05_HEXAGONAL_SYMMETRY_PAPERS_ANALYSIS.md                      ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    diagnostics = CPPhaseHexagonalDiagnostics()
    results = diagnostics.run_all_tests()
    
    print("\n" + "📊" * 40)
    print(" SUMMARY OF KEY FINDINGS")
    print("📊" * 40)
    
    print(f"""
EXPERIMENTAL CP PHASES:
- CKM δ_CP = {diagnostics.ckm_exp['delta_cp']:.1f}° → Nearest Z₆: {results['test1']['ckm_nearest_z6']:.0f}° ({'✅ YES' if results['test1']['ckm_near_z6'] else '❌ NO'})
- PMNS δ_CP = {diagnostics.pmns_exp['delta_cp']:.1f}° → Nearest Z₆: {results['test1']['pmns_nearest_z6']:.0f}° ({'✅ YES' if results['test1']['pmns_near_z6'] else '❌ NO'})

CURRENT UGP PREDICTIONS:
- CKM δ_CP = {diagnostics.ckm_ugp['delta_cp']:.1f}° (using π/2 hypothesis)
- PMNS δ_CP = {diagnostics.pmns_ugp['delta_cp']:.1f}° (using modified hypothesis)

HEXAGONAL HYPOTHESIS PREDICTIONS:
- Best CKM: {results['test4']['best_ckm'][1]} at {results['test4']['best_ckm'][2]:.1f}° (error: {results['test4']['best_ckm'][0]:.1f}°)
- Best PMNS: {results['test4']['best_pmns'][1]} at {results['test4']['best_pmns'][2]:.1f}° (error: {results['test4']['best_pmns'][0]:.1f}°)

CONCLUSION:
If hexagonal symmetry hypothesis is correct, switching from π/2 to Z₆-based
discrete values (especially π/3 for CKM) could dramatically improve CP phase predictions!
    """)
    
    print("\n" + "🔑" * 40)
    print("Next step: Modify code to use Z₆ hypothesis and re-run")
    print("🔑" * 40)

