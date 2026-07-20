"""
TE_2 Theory Space Extension - Phase 0: Physical Equivalence

This module defines the physical equivalence relation ~ on T_PSC.

Definition (Physical Equivalence):
Two theories T, T' ∈ T_PSC are physically equivalent (T ~ T') if there exists
a finite chain of transformations mapping one to the other while preserving
all on-shell predictions.

Allowed Transformations:
- (E1) Gauge isomorphism
- (E2) Field redefinitions
- (E3) RG scheme changes
- (E4) Decoupling equivalence
- (E5) Dualities

The quotient space T_PSC/~ is the space of physically distinct theories.

Cross-Reference:
- the SRRG uniqueness proof program (see TE_2 Theory Space Extension documentation, Section 4.3)
- TE_2.2 (physical equivalence for universes)

Author: AI Assistant
Date: 2025-02-25
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional, Callable
from enum import Enum
from abc import ABC, abstractmethod

from theory_space_definition import TheoryParams, GaugeGroup, GAUGE_GROUPS_CATALOG


# =============================================================================
# EQUIVALENCE TRANSFORMATION TYPES
# =============================================================================

class EquivalenceType(Enum):
    """Types of physical equivalence transformations."""
    GAUGE_ISOMORPHISM = "E1"      # G ≅ G'
    FIELD_REDEFINITION = "E2"     # φ → f(φ)
    RG_SCHEME_CHANGE = "E3"       # MS-bar ↔ on-shell
    DECOUPLING = "E4"             # Integrate out heavy fields
    DUALITY = "E5"                # S-duality, mirror symmetry, etc.


@dataclass
class EquivalenceTransformation:
    """
    A transformation that preserves physical equivalence.
    
    Attributes:
        type: Type of transformation
        description: Human-readable description
        source: Source theory (or pattern)
        target: Target theory (or pattern)
    """
    type: EquivalenceType
    description: str
    source: str
    target: str
    
    def __str__(self):
        return f"[{self.type.value}] {self.description}: {self.source} → {self.target}"


# =============================================================================
# GAUGE ISOMORPHISMS (E1)
# =============================================================================

# Known gauge isomorphisms
GAUGE_ISOMORPHISMS = [
    # SU(2) ≅ Sp(1) ≅ Spin(3)
    EquivalenceTransformation(
        type=EquivalenceType.GAUGE_ISOMORPHISM,
        description="SU(2) is isomorphic to Sp(1)",
        source="SU(2)",
        target="Sp(1)"
    ),
    # SO(3) ≅ SU(2)/Z_2
    EquivalenceTransformation(
        type=EquivalenceType.GAUGE_ISOMORPHISM,
        description="SO(3) is SU(2) mod center",
        source="SO(3)",
        target="SU(2)/Z_2"
    ),
    # SU(4) ≅ Spin(6)
    EquivalenceTransformation(
        type=EquivalenceType.GAUGE_ISOMORPHISM,
        description="SU(4) is isomorphic to Spin(6)",
        source="SU(4)",
        target="Spin(6)"
    ),
    # U(1) relabelings (hypercharge conventions)
    EquivalenceTransformation(
        type=EquivalenceType.GAUGE_ISOMORPHISM,
        description="U(1) hypercharge normalization",
        source="U(1)_Y",
        target="U(1)_Y'"
    ),
]


def are_gauge_isomorphic(G1: GaugeGroup, G2: GaugeGroup) -> bool:
    """
    Check if two gauge groups are isomorphic.
    
    Args:
        G1, G2: Gauge groups to compare
        
    Returns:
        True if G1 ≅ G2
    """
    # Same name is trivially isomorphic
    if G1.name == G2.name:
        return True
    
    # Check known isomorphisms
    isomorphic_pairs = [
        ("SU(2)", "Sp(1)"),
        ("SU(4)", "Spin(6)"),
    ]
    
    for a, b in isomorphic_pairs:
        if (G1.name == a and G2.name == b) or (G1.name == b and G2.name == a):
            return True
    
    # Check if same rank and dimension (necessary but not sufficient)
    if G1.rank != G2.rank or G1.dimension != G2.dimension:
        return False
    
    return False


# =============================================================================
# FIELD REDEFINITIONS (E2)
# =============================================================================

@dataclass
class FieldRedefinition:
    """
    A field redefinition φ → f(φ).
    
    Field redefinitions must be:
    - Local (no derivatives in transformation)
    - Invertible
    - Preserve S-matrix elements
    """
    field_name: str
    transformation: str  # Symbolic description
    jacobian: float      # |det(∂f/∂φ)|
    
    def is_valid(self) -> bool:
        """Check if redefinition is valid (invertible)."""
        return self.jacobian != 0


def coupling_under_field_redefinition(
    coupling: float, 
    field_name: str,
    scale_factor: float
) -> float:
    """
    Transform a coupling under field rescaling φ → α·φ.
    
    For a term g·φⁿ, under φ → α·φ:
    g → g/αⁿ
    
    Args:
        coupling: Original coupling value
        field_name: Name of field being rescaled
        scale_factor: Rescaling factor α
        
    Returns:
        Transformed coupling
    """
    # Simplified: assume quadratic coupling
    return coupling / (scale_factor ** 2)


# =============================================================================
# RG SCHEME CHANGES (E3)
# =============================================================================

class RGScheme(Enum):
    """Renormalization schemes."""
    MS_BAR = "MS-bar"           # Modified minimal subtraction
    ON_SHELL = "on-shell"       # On-shell scheme
    MOM = "MOM"                 # Momentum subtraction
    DREG = "dimensional_reg"   # Dimensional regularization


@dataclass
class SchemeConversion:
    """
    Conversion between RG schemes.
    
    Couplings transform as:
    g_new = g_old + Δg(g_old, μ)
    
    where Δg is scheme-dependent.
    """
    source_scheme: RGScheme
    target_scheme: RGScheme
    conversion_formula: str
    
    def convert_coupling(self, g: float, mu: float) -> float:
        """
        Convert coupling between schemes.
        
        Simplified: use leading-order conversion.
        
        Args:
            g: Coupling in source scheme
            mu: Renormalization scale
            
        Returns:
            Coupling in target scheme
        """
        # MS-bar to on-shell conversion (simplified)
        if (self.source_scheme == RGScheme.MS_BAR and 
            self.target_scheme == RGScheme.ON_SHELL):
            # Leading correction is O(g²)
            return g * (1 + 0.01 * g)
        
        # On-shell to MS-bar
        if (self.source_scheme == RGScheme.ON_SHELL and 
            self.target_scheme == RGScheme.MS_BAR):
            return g * (1 - 0.01 * g)
        
        # Same scheme
        return g


# Standard scheme conversions
SCHEME_CONVERSIONS = {
    ("MS-bar", "on-shell"): SchemeConversion(
        RGScheme.MS_BAR, RGScheme.ON_SHELL,
        "g_OS = g_MS * (1 + O(g²))"
    ),
    ("on-shell", "MS-bar"): SchemeConversion(
        RGScheme.ON_SHELL, RGScheme.MS_BAR,
        "g_MS = g_OS * (1 - O(g²))"
    ),
}


# =============================================================================
# DECOUPLING EQUIVALENCE (E4)
# =============================================================================

@dataclass
class DecouplingRelation:
    """
    Decoupling relation between UV and IR theories.
    
    When integrating out heavy fields of mass M, the UV theory T_UV
    matches onto IR theory T_IR with higher-dimensional operators
    suppressed by powers of 1/M.
    """
    uv_theory: str
    ir_theory: str
    heavy_field: str
    heavy_mass: float
    matching_scale: float
    
    def are_equivalent_below_scale(self, energy: float) -> bool:
        """Check if theories are equivalent below given energy."""
        return energy < self.matching_scale


# =============================================================================
# DUALITIES (E5)
# =============================================================================

@dataclass
class Duality:
    """
    A duality between two theories.
    
    Dualities are non-perturbative equivalences that may exchange
    strong and weak coupling, or map between different-looking theories.
    """
    name: str
    theory_a: str
    theory_b: str
    coupling_map: str  # How couplings transform
    is_proven: bool    # Whether duality is rigorously proven
    
    def __str__(self):
        status = "proven" if self.is_proven else "conjectured"
        return f"{self.name} ({status}): {self.theory_a} ↔ {self.theory_b}"


# Known dualities (relevant for PSC theories)
KNOWN_DUALITIES = [
    Duality(
        name="S-duality (N=4 SYM)",
        theory_a="N=4 SYM at g",
        theory_b="N=4 SYM at 1/g",
        coupling_map="g → 1/g",
        is_proven=True  # Montonen-Olive
    ),
    Duality(
        name="Mirror symmetry (3D N=4)",
        theory_a="3D N=4 theory A",
        theory_b="3D N=4 theory B",
        coupling_map="Coulomb ↔ Higgs",
        is_proven=True
    ),
]


# =============================================================================
# PHYSICAL EQUIVALENCE CHECKER
# =============================================================================

class PhysicalEquivalenceChecker:
    """
    Checks physical equivalence between theories.
    
    Two theories T ~ T' if connected by a chain of (E1)-(E5) transformations.
    """
    
    def __init__(self, tolerance: float = 1e-3):
        """
        Initialize checker.
        
        Args:
            tolerance: Numerical tolerance for coupling comparisons
        """
        self.tolerance = tolerance
        self.transformation_chain: List[EquivalenceTransformation] = []
    
    def are_equivalent(self, T1: TheoryParams, T2: TheoryParams) -> bool:
        """
        Check if two theories are physically equivalent.
        
        Args:
            T1, T2: Theories to compare
            
        Returns:
            True if T1 ~ T2
        """
        self.transformation_chain = []
        
        # Check (E1): Gauge isomorphism
        if not are_gauge_isomorphic(T1.gauge_group, T2.gauge_group):
            return False
        
        # Check generation count
        if T1.n_generations != T2.n_generations:
            return False
        
        # Check (E3): RG scheme equivalence
        # Couplings can differ by scheme-dependent corrections
        if not self._couplings_equivalent(T1, T2):
            return False
        
        return True
    
    def _couplings_equivalent(self, T1: TheoryParams, T2: TheoryParams) -> bool:
        """
        Check if couplings are equivalent up to scheme changes.
        
        Allows for O(g²) differences due to scheme dependence.
        """
        for name in T1.gauge_couplings:
            if name not in T2.gauge_couplings:
                return False
            
            g1 = T1.gauge_couplings[name]
            g2 = T2.gauge_couplings[name]
            
            # Allow scheme-dependent difference
            max_diff = self.tolerance + 0.01 * g1 * g1  # O(g²) correction
            
            if abs(g1 - g2) > max_diff:
                return False
        
        return True
    
    def get_equivalence_class(self, T: TheoryParams, 
                              all_theories: List[TheoryParams]) -> List[TheoryParams]:
        """
        Get all theories equivalent to T.
        
        Args:
            T: Reference theory
            all_theories: List of theories to check
            
        Returns:
            List of theories equivalent to T (including T)
        """
        return [T2 for T2 in all_theories if self.are_equivalent(T, T2)]
    
    def quotient_representatives(self, 
                                 theories: List[TheoryParams]) -> List[TheoryParams]:
        """
        Get one representative from each equivalence class.
        
        Args:
            theories: List of theories
            
        Returns:
            List of representatives (one per equivalence class)
        """
        representatives = []
        used = set()
        
        for T in theories:
            # Create a hashable key for the equivalence class
            key = self._equivalence_class_key(T)
            
            if key not in used:
                representatives.append(T)
                used.add(key)
        
        return representatives
    
    def _equivalence_class_key(self, T: TheoryParams) -> Tuple:
        """
        Create a hashable key for the equivalence class of T.
        
        Two theories with the same key are equivalent.
        """
        # Key components:
        # 1. Gauge group (up to isomorphism)
        gauge_key = self._canonical_gauge_name(T.gauge_group)
        
        # 2. Generation count
        gen_key = T.n_generations
        
        # 3. Couplings (rounded to account for scheme dependence)
        coupling_key = tuple(
            round(v, 2) for v in sorted(T.gauge_couplings.values())
        )
        
        return (gauge_key, gen_key, coupling_key)
    
    def _canonical_gauge_name(self, G: GaugeGroup) -> str:
        """
        Get canonical name for gauge group (accounting for isomorphisms).
        """
        # Map isomorphic groups to canonical representative
        canonical_map = {
            "Sp(1)": "SU(2)",
            "Spin(6)": "SU(4)",
        }
        
        return canonical_map.get(G.name, G.name)


# =============================================================================
# QUOTIENT SPACE
# =============================================================================

class QuotientTheorySpace:
    """
    The quotient space T_PSC/~.
    
    This represents the space of physically distinct theories,
    where equivalent theories are identified.
    """
    
    def __init__(self, theories: List[TheoryParams]):
        """
        Initialize quotient space from a list of theories.
        
        Args:
            theories: List of theories in T_PSC
        """
        self.equivalence_checker = PhysicalEquivalenceChecker()
        self.representatives = self.equivalence_checker.quotient_representatives(theories)
        
        # Build equivalence class map
        self._class_map: Dict[int, List[TheoryParams]] = {}
        for i, rep in enumerate(self.representatives):
            self._class_map[i] = self.equivalence_checker.get_equivalence_class(
                rep, theories
            )
    
    def __len__(self) -> int:
        """Number of equivalence classes."""
        return len(self.representatives)
    
    def __iter__(self):
        """Iterate over equivalence class representatives."""
        return iter(self.representatives)
    
    def get_class(self, T: TheoryParams) -> Optional[int]:
        """
        Get the equivalence class index for a theory.
        
        Args:
            T: Theory to look up
            
        Returns:
            Index of equivalence class, or None if not found
        """
        for i, rep in enumerate(self.representatives):
            if self.equivalence_checker.are_equivalent(T, rep):
                return i
        return None
    
    def get_representative(self, class_index: int) -> TheoryParams:
        """Get the representative of an equivalence class."""
        return self.representatives[class_index]
    
    def get_class_members(self, class_index: int) -> List[TheoryParams]:
        """Get all members of an equivalence class."""
        return self._class_map.get(class_index, [])
    
    def contains_sm(self) -> bool:
        """Check if SM equivalence class is in the quotient space."""
        for rep in self.representatives:
            if rep.is_standard_model():
                return True
        return False
    
    def get_sm_class_index(self) -> Optional[int]:
        """Get the index of the SM equivalence class."""
        for i, rep in enumerate(self.representatives):
            if rep.is_standard_model():
                return i
        return None


# =============================================================================
# TESTING
# =============================================================================

def test_physical_equivalence():
    """Test physical equivalence implementation."""
    print("=" * 80)
    print("TESTING PHYSICAL EQUIVALENCE")
    print("=" * 80)
    
    from theory_space_definition import create_standard_model_theory, TheorySpace
    
    # Create theories
    SM1 = create_standard_model_theory()
    SM2 = create_standard_model_theory()
    
    # Perturb SM2 slightly (within scheme tolerance)
    SM2.gauge_couplings['g1'] = 0.3575  # Small perturbation
    
    # Create non-SM theory
    from theory_space_definition import GAUGE_GROUPS_CATALOG
    SU5 = TheoryParams(
        gauge_group=GAUGE_GROUPS_CATALOG["SU(5)"],
        n_generations=3,
        gauge_couplings={'g': 0.5},
    )
    
    # Test equivalence checker
    print("\n1. Equivalence Checking:")
    print("-" * 80)
    checker = PhysicalEquivalenceChecker(tolerance=1e-2)
    
    print(f"   SM1 ~ SM2 (small perturbation): {checker.are_equivalent(SM1, SM2)}")
    print(f"   SM1 ~ SU(5): {checker.are_equivalent(SM1, SU5)}")
    
    # Test gauge isomorphism
    print("\n2. Gauge Isomorphisms:")
    print("-" * 80)
    G_SU2 = GAUGE_GROUPS_CATALOG["SU(2)"]
    G_SU3 = GAUGE_GROUPS_CATALOG["SU(3)"]
    
    print(f"   SU(2) ≅ SU(2): {are_gauge_isomorphic(G_SU2, G_SU2)}")
    print(f"   SU(2) ≅ SU(3): {are_gauge_isomorphic(G_SU2, G_SU3)}")
    
    # Test quotient space
    print("\n3. Quotient Space:")
    print("-" * 80)
    
    # Create a small theory space
    T_PSC = TheorySpace(rank_max=5, dim_max=4)
    theories = T_PSC.enumerate_truncation(d_star=4, r_star=5, n_gen_max=4)
    
    # Create quotient
    quotient = QuotientTheorySpace(theories)
    
    print(f"   Original theories: {len(theories)}")
    print(f"   Equivalence classes: {len(quotient)}")
    print(f"   SM class exists: {quotient.contains_sm()}")
    
    if quotient.contains_sm():
        sm_idx = quotient.get_sm_class_index()
        sm_class = quotient.get_class_members(sm_idx)
        print(f"   SM class index: {sm_idx}")
        print(f"   SM class size: {len(sm_class)}")
    
    # List equivalence classes
    print("\n   Equivalence class representatives:")
    for i, rep in enumerate(quotient):
        is_sm = "✓ SM" if rep.is_standard_model() else ""
        print(f"   [{i}] {rep.gauge_group.name}, n_gen={rep.n_generations} {is_sm}")
    
    print("\n" + "=" * 80)
    print("PHYSICAL EQUIVALENCE TEST COMPLETE ✓")
    print("=" * 80)


if __name__ == "__main__":
    test_physical_equivalence()
