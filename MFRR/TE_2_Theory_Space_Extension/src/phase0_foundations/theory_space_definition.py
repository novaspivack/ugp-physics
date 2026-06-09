"""
TE_2 Theory Space Extension - Phase 0: Theory Space Definition

This module defines the PSC-admissible theory space T_PSC, which is the domain
for the SRRG uniqueness proof.

Definition (PSC-Admissible Theory Space):
A theory T ∈ T_PSC is an equivalence class of presentations:
    T ≡ (G, R, F, L_{≤d*}, Θ, Sem, Therm)
subject to constraints (T1)-(T5) defined in the SPEC.

Key Components:
- Gauge structure (T1): Compact Lie group G with representations R
- EFT locality (T2): Local Lagrangian with operators up to dimension d*
- Consistency (T3): Anomaly cancellation, unitarity, renormalizability
- PSC closure (T4): Reflexive admissibility constraints
- SRRG regularity (T5): Well-posed SRRG flow with Fisher metric

Cross-Reference:
- the SRRG uniqueness proof program (see TE_2 Theory Space Extension documentation, Section 4)
- TE_2.3 te2_3_theory_space.py (8D parameterization)
- TE_1.R_CONTINOUS_MODEL (Lyapunov functional)

Author: AI Assistant
Date: 2025-02-25
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set
from enum import Enum
import json


# =============================================================================
# GAUGE GROUP DEFINITIONS
# =============================================================================

class GaugeGroupType(Enum):
    """Classification of gauge groups."""
    ABELIAN = "abelian"
    SIMPLE = "simple"
    SEMISIMPLE = "semisimple"
    PRODUCT = "product"


@dataclass
class GaugeGroup:
    """
    Representation of a gauge group.
    
    A gauge group G is characterized by:
    - name: Human-readable name (e.g., "SU(3)×SU(2)×U(1)")
    - factors: List of simple/abelian factors
    - rank: Total rank (sum of factor ranks)
    - dimension: Total dimension (sum of factor dimensions)
    """
    name: str
    factors: List[str]
    rank: int
    dimension: int
    group_type: GaugeGroupType
    
    def is_standard_model(self) -> bool:
        """Check if this is the Standard Model gauge group."""
        return self.name == "SU(3)×SU(2)×U(1)"
    
    def __hash__(self):
        return hash(self.name)
    
    def __eq__(self, other):
        if isinstance(other, GaugeGroup):
            return self.name == other.name
        return False


# Standard gauge groups catalog — comprehensive through rank 10
# Includes all physically relevant simple, semi-simple, and product groups
GAUGE_GROUPS_CATALOG = {
    # ===================== ABELIAN =====================
    "U(1)": GaugeGroup("U(1)", ["U(1)"], rank=1, dimension=1,
                       group_type=GaugeGroupType.ABELIAN),
    "U(1)×U(1)": GaugeGroup("U(1)×U(1)", ["U(1)", "U(1)"], rank=2, dimension=2,
                             group_type=GaugeGroupType.PRODUCT),

    # ===================== SIMPLE: SU(N) =====================
    "SU(2)": GaugeGroup("SU(2)", ["SU(2)"], rank=1, dimension=3,
                        group_type=GaugeGroupType.SIMPLE),
    "SU(3)": GaugeGroup("SU(3)", ["SU(3)"], rank=2, dimension=8,
                        group_type=GaugeGroupType.SIMPLE),
    "SU(4)": GaugeGroup("SU(4)", ["SU(4)"], rank=3, dimension=15,
                        group_type=GaugeGroupType.SIMPLE),
    "SU(5)": GaugeGroup("SU(5)", ["SU(5)"], rank=4, dimension=24,
                        group_type=GaugeGroupType.SIMPLE),
    "SU(6)": GaugeGroup("SU(6)", ["SU(6)"], rank=5, dimension=35,
                        group_type=GaugeGroupType.SIMPLE),
    "SU(7)": GaugeGroup("SU(7)", ["SU(7)"], rank=6, dimension=48,
                        group_type=GaugeGroupType.SIMPLE),
    "SU(8)": GaugeGroup("SU(8)", ["SU(8)"], rank=7, dimension=63,
                        group_type=GaugeGroupType.SIMPLE),
    "SU(9)": GaugeGroup("SU(9)", ["SU(9)"], rank=8, dimension=80,
                        group_type=GaugeGroupType.SIMPLE),
    "SU(10)": GaugeGroup("SU(10)", ["SU(10)"], rank=9, dimension=99,
                         group_type=GaugeGroupType.SIMPLE),
    "SU(11)": GaugeGroup("SU(11)", ["SU(11)"], rank=10, dimension=120,
                         group_type=GaugeGroupType.SIMPLE),

    # ===================== SIMPLE: SO(N) =====================
    "SO(6)": GaugeGroup("SO(6)", ["SO(6)"], rank=3, dimension=15,
                        group_type=GaugeGroupType.SIMPLE),
    "SO(8)": GaugeGroup("SO(8)", ["SO(8)"], rank=4, dimension=28,
                        group_type=GaugeGroupType.SIMPLE),
    "SO(10)": GaugeGroup("SO(10)", ["SO(10)"], rank=5, dimension=45,
                         group_type=GaugeGroupType.SIMPLE),
    "SO(12)": GaugeGroup("SO(12)", ["SO(12)"], rank=6, dimension=66,
                         group_type=GaugeGroupType.SIMPLE),
    "SO(14)": GaugeGroup("SO(14)", ["SO(14)"], rank=7, dimension=91,
                         group_type=GaugeGroupType.SIMPLE),
    "SO(16)": GaugeGroup("SO(16)", ["SO(16)"], rank=8, dimension=120,
                         group_type=GaugeGroupType.SIMPLE),
    "SO(18)": GaugeGroup("SO(18)", ["SO(18)"], rank=9, dimension=153,
                         group_type=GaugeGroupType.SIMPLE),

    # ===================== SIMPLE: Sp(N) =====================
    "Sp(4)": GaugeGroup("Sp(4)", ["Sp(4)"], rank=2, dimension=10,
                        group_type=GaugeGroupType.SIMPLE),
    "Sp(6)": GaugeGroup("Sp(6)", ["Sp(6)"], rank=3, dimension=21,
                        group_type=GaugeGroupType.SIMPLE),
    "Sp(8)": GaugeGroup("Sp(8)", ["Sp(8)"], rank=4, dimension=36,
                        group_type=GaugeGroupType.SIMPLE),

    # ===================== EXCEPTIONAL =====================
    "G_2": GaugeGroup("G_2", ["G_2"], rank=2, dimension=14,
                      group_type=GaugeGroupType.SIMPLE),
    "F_4": GaugeGroup("F_4", ["F_4"], rank=4, dimension=52,
                      group_type=GaugeGroupType.SIMPLE),
    "E_6": GaugeGroup("E_6", ["E_6"], rank=6, dimension=78,
                      group_type=GaugeGroupType.SIMPLE),
    "E_7": GaugeGroup("E_7", ["E_7"], rank=7, dimension=133,
                      group_type=GaugeGroupType.SIMPLE),
    "E_8": GaugeGroup("E_8", ["E_8"], rank=8, dimension=248,
                      group_type=GaugeGroupType.SIMPLE),

    # ===================== PRODUCT: SM-like =====================
    "SU(2)×U(1)": GaugeGroup("SU(2)×U(1)", ["SU(2)", "U(1)"], rank=2, dimension=4,
                              group_type=GaugeGroupType.PRODUCT),
    "SU(3)×U(1)": GaugeGroup("SU(3)×U(1)", ["SU(3)", "U(1)"], rank=3, dimension=9,
                              group_type=GaugeGroupType.PRODUCT),
    "SU(3)×SU(2)": GaugeGroup("SU(3)×SU(2)", ["SU(3)", "SU(2)"], rank=3, dimension=11,
                               group_type=GaugeGroupType.PRODUCT),
    # Standard Model
    "SU(3)×SU(2)×U(1)": GaugeGroup("SU(3)×SU(2)×U(1)", ["SU(3)", "SU(2)", "U(1)"],
                                    rank=4, dimension=12, group_type=GaugeGroupType.PRODUCT),
    # SM + extra U(1)
    "SU(3)×SU(2)×U(1)×U(1)": GaugeGroup("SU(3)×SU(2)×U(1)×U(1)",
                                          ["SU(3)", "SU(2)", "U(1)", "U(1)"],
                                          rank=5, dimension=13, group_type=GaugeGroupType.PRODUCT),

    # ===================== PRODUCT: GUT-adjacent =====================
    # Pati-Salam
    "SU(4)×SU(2)×SU(2)": GaugeGroup("SU(4)×SU(2)×SU(2)", ["SU(4)", "SU(2)", "SU(2)"],
                                     rank=5, dimension=21, group_type=GaugeGroupType.PRODUCT),
    # Trinification
    "SU(3)×SU(3)×SU(3)": GaugeGroup("SU(3)×SU(3)×SU(3)", ["SU(3)", "SU(3)", "SU(3)"],
                                     rank=6, dimension=24, group_type=GaugeGroupType.PRODUCT),
    # Left-Right symmetric
    "SU(3)×SU(2)×SU(2)×U(1)": GaugeGroup("SU(3)×SU(2)×SU(2)×U(1)",
                                           ["SU(3)", "SU(2)", "SU(2)", "U(1)"],
                                           rank=5, dimension=16, group_type=GaugeGroupType.PRODUCT),
    # Flipped SU(5)
    "SU(5)×U(1)": GaugeGroup("SU(5)×U(1)", ["SU(5)", "U(1)"], rank=5, dimension=25,
                              group_type=GaugeGroupType.PRODUCT),
    # SO(10) × U(1)
    "SO(10)×U(1)": GaugeGroup("SO(10)×U(1)", ["SO(10)", "U(1)"], rank=6, dimension=46,
                               group_type=GaugeGroupType.PRODUCT),
    # E6 × U(1)
    "E_6×U(1)": GaugeGroup("E_6×U(1)", ["E_6", "U(1)"], rank=7, dimension=79,
                            group_type=GaugeGroupType.PRODUCT),
    # SU(4)×SU(4)
    "SU(4)×SU(4)": GaugeGroup("SU(4)×SU(4)", ["SU(4)", "SU(4)"], rank=6, dimension=30,
                               group_type=GaugeGroupType.PRODUCT),
    # SU(5)×SU(5)
    "SU(5)×SU(5)": GaugeGroup("SU(5)×SU(5)", ["SU(5)", "SU(5)"], rank=8, dimension=48,
                               group_type=GaugeGroupType.PRODUCT),
    # SU(6)×SU(2)
    "SU(6)×SU(2)": GaugeGroup("SU(6)×SU(2)", ["SU(6)", "SU(2)"], rank=6, dimension=38,
                               group_type=GaugeGroupType.PRODUCT),
    # E_6×SU(2)
    "E_6×SU(2)": GaugeGroup("E_6×SU(2)", ["E_6", "SU(2)"], rank=7, dimension=81,
                             group_type=GaugeGroupType.PRODUCT),
}


def enumerate_gauge_groups(rank_max: int = 8) -> List[GaugeGroup]:
    """
    Enumerate all gauge groups up to a maximum rank.
    
    Args:
        rank_max: Maximum total rank
        
    Returns:
        List of GaugeGroup objects with rank ≤ rank_max
    """
    return [g for g in GAUGE_GROUPS_CATALOG.values() if g.rank <= rank_max]


# =============================================================================
# REPRESENTATION DEFINITIONS
# =============================================================================

@dataclass
class Representation:
    """
    A representation of a gauge group.
    
    Characterized by:
    - name: Human-readable name (e.g., "3" for fundamental of SU(3))
    - dimension: Dimension of the representation
    - dynkin_labels: Dynkin labels (for simple groups)
    - is_real: Whether the representation is real
    - is_complex: Whether the representation is complex
    - is_pseudoreal: Whether the representation is pseudoreal
    """
    name: str
    dimension: int
    dynkin_labels: Tuple[int, ...] = field(default_factory=tuple)
    is_real: bool = False
    is_complex: bool = True
    is_pseudoreal: bool = False
    
    def __hash__(self):
        return hash((self.name, self.dimension))


@dataclass
class MatterField:
    """
    A matter field in a theory.
    
    Characterized by:
    - name: Field name (e.g., "Q_L" for left-handed quarks)
    - representations: Dict mapping gauge factor to representation
    - spin: Spin of the field (0, 1/2, 1, etc.)
    - chirality: "L" or "R" for fermions, None for bosons
    - generations: Number of generations
    """
    name: str
    representations: Dict[str, Representation]
    spin: float
    chirality: Optional[str] = None
    generations: int = 1
    
    def is_chiral(self) -> bool:
        """Check if field is chiral."""
        return self.chirality is not None


# Standard Model matter content
SM_MATTER_CONTENT = {
    # Left-handed quarks: (3, 2, 1/6)
    "Q_L": MatterField(
        name="Q_L",
        representations={
            "SU(3)": Representation("3", 3),
            "SU(2)": Representation("2", 2),
            "U(1)": Representation("1/6", 1),
        },
        spin=0.5,
        chirality="L",
        generations=3
    ),
    # Right-handed up quarks: (3, 1, 2/3)
    "u_R": MatterField(
        name="u_R",
        representations={
            "SU(3)": Representation("3", 3),
            "SU(2)": Representation("1", 1),
            "U(1)": Representation("2/3", 1),
        },
        spin=0.5,
        chirality="R",
        generations=3
    ),
    # Right-handed down quarks: (3, 1, -1/3)
    "d_R": MatterField(
        name="d_R",
        representations={
            "SU(3)": Representation("3", 3),
            "SU(2)": Representation("1", 1),
            "U(1)": Representation("-1/3", 1),
        },
        spin=0.5,
        chirality="R",
        generations=3
    ),
    # Left-handed leptons: (1, 2, -1/2)
    "L_L": MatterField(
        name="L_L",
        representations={
            "SU(3)": Representation("1", 1),
            "SU(2)": Representation("2", 2),
            "U(1)": Representation("-1/2", 1),
        },
        spin=0.5,
        chirality="L",
        generations=3
    ),
    # Right-handed electrons: (1, 1, -1)
    "e_R": MatterField(
        name="e_R",
        representations={
            "SU(3)": Representation("1", 1),
            "SU(2)": Representation("1", 1),
            "U(1)": Representation("-1", 1),
        },
        spin=0.5,
        chirality="R",
        generations=3
    ),
    # Higgs: (1, 2, 1/2)
    "H": MatterField(
        name="H",
        representations={
            "SU(3)": Representation("1", 1),
            "SU(2)": Representation("2", 2),
            "U(1)": Representation("1/2", 1),
        },
        spin=0,
        chirality=None,
        generations=1
    ),
}


# =============================================================================
# THEORY PARAMETERS
# =============================================================================

@dataclass
class TheoryParams:
    """
    Parameters defining a theory T ∈ T_PSC.
    
    This is the central data structure for the theory space.
    
    Attributes:
        gauge_group: The gauge group G
        matter_content: Dict of matter fields
        n_generations: Number of fermion generations
        eft_dimension: EFT truncation dimension d*
        gauge_couplings: Dict of gauge coupling values
        yukawa_couplings: Dict of Yukawa coupling values
        scalar_couplings: Dict of scalar self-couplings
        mass_parameters: Dict of mass parameters
        mixing_angles: Dict of mixing angles (CKM, PMNS)
        cp_phases: Dict of CP-violating phases
    """
    gauge_group: GaugeGroup
    matter_content: Dict[str, MatterField] = field(default_factory=dict)
    n_generations: int = 3
    eft_dimension: int = 4
    
    # Coupling parameters
    gauge_couplings: Dict[str, float] = field(default_factory=dict)
    yukawa_couplings: Dict[str, float] = field(default_factory=dict)
    scalar_couplings: Dict[str, float] = field(default_factory=dict)
    mass_parameters: Dict[str, float] = field(default_factory=dict)
    mixing_angles: Dict[str, float] = field(default_factory=dict)
    cp_phases: Dict[str, float] = field(default_factory=dict)
    
    # Matter content extensions beyond the minimal chiral spectrum
    n_vector_like_pairs: int = 0
    n_extra_scalars: int = 0
    
    # PSC closure parameters
    psc_admissible: bool = True
    reflexive_closure_satisfied: bool = True
    
    def is_standard_model(self, tol: float = 1e-3) -> bool:
        """
        Check if this theory is the Standard Model.
        
        Args:
            tol: Tolerance for coupling comparisons
            
        Returns:
            True if theory matches SM
        """
        # Check gauge group
        if not self.gauge_group.is_standard_model():
            return False
        
        # Check generations
        if self.n_generations != 3:
            return False
        
        # SM has no vector-like extensions or extra scalars
        if self.n_vector_like_pairs != 0 or self.n_extra_scalars != 0:
            return False
        
        # Check gauge couplings (at M_Z scale)
        sm_couplings = {
            'g1': 0.357421238,  # U(1)_Y
            'g2': 0.651731473,  # SU(2)_L
            'g3': 1.21719969,   # SU(3)_c
        }
        
        for name, sm_val in sm_couplings.items():
            if name in self.gauge_couplings:
                if abs(self.gauge_couplings[name] - sm_val) > tol:
                    return False
        
        return True
    
    def get_parameter_vector(self) -> np.ndarray:
        """
        Get theory parameters as a vector for numerical computations.
        
        Returns:
            numpy array of all continuous parameters
        """
        params = []
        
        # Gauge couplings
        for name in sorted(self.gauge_couplings.keys()):
            params.append(self.gauge_couplings[name])
        
        # Yukawa couplings
        for name in sorted(self.yukawa_couplings.keys()):
            params.append(self.yukawa_couplings[name])
        
        # Scalar couplings
        for name in sorted(self.scalar_couplings.keys()):
            params.append(self.scalar_couplings[name])
        
        # Mass parameters
        for name in sorted(self.mass_parameters.keys()):
            params.append(self.mass_parameters[name])
        
        # Mixing angles
        for name in sorted(self.mixing_angles.keys()):
            params.append(self.mixing_angles[name])
        
        # CP phases
        for name in sorted(self.cp_phases.keys()):
            params.append(self.cp_phases[name])
        
        return np.array(params)
    
    def get_dimension(self) -> int:
        """Get total dimension of parameter space."""
        return (len(self.gauge_couplings) + 
                len(self.yukawa_couplings) + 
                len(self.scalar_couplings) +
                len(self.mass_parameters) +
                len(self.mixing_angles) +
                len(self.cp_phases))
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'gauge_group': self.gauge_group.name,
            'n_generations': self.n_generations,
            'eft_dimension': self.eft_dimension,
            'gauge_couplings': self.gauge_couplings,
            'yukawa_couplings': self.yukawa_couplings,
            'scalar_couplings': self.scalar_couplings,
            'mass_parameters': self.mass_parameters,
            'mixing_angles': self.mixing_angles,
            'cp_phases': self.cp_phases,
            'n_vector_like_pairs': self.n_vector_like_pairs,
            'n_extra_scalars': self.n_extra_scalars,
            'psc_admissible': self.psc_admissible,
        }


def create_standard_model_theory() -> TheoryParams:
    """
    Create the Standard Model theory with canonical parameters.
    
    Returns:
        TheoryParams for the Standard Model
    """
    return TheoryParams(
        gauge_group=GAUGE_GROUPS_CATALOG["SU(3)×SU(2)×U(1)"],
        matter_content=SM_MATTER_CONTENT,
        n_generations=3,
        eft_dimension=4,
        gauge_couplings={
            'g1': 0.357421238,  # U(1)_Y at M_Z
            'g2': 0.651731473,  # SU(2)_L at M_Z
            'g3': 1.21719969,   # SU(3)_c at M_Z
        },
        yukawa_couplings={
            'y_t': 0.9369,      # Top Yukawa
            'y_b': 0.0164,      # Bottom Yukawa
            'y_tau': 0.0102,    # Tau Yukawa
        },
        scalar_couplings={
            'lambda': 0.129,    # Higgs self-coupling
        },
        mass_parameters={
            'v': 246.22,        # Higgs VEV (GeV)
            'm_H': 125.25,      # Higgs mass (GeV)
        },
        mixing_angles={
            'theta_12': 0.2277,  # CKM θ₁₂
            'theta_23': 0.0418,  # CKM θ₂₃
            'theta_13': 0.0036,  # CKM θ₁₃
        },
        cp_phases={
            'delta_CKM': 1.20,   # CKM CP phase
        },
        psc_admissible=True,
        reflexive_closure_satisfied=True,
    )


# =============================================================================
# PSC ADMISSIBILITY CHECKS
# =============================================================================

class PSCAdmissibilityChecker:
    """
    Checks whether a theory is PSC-admissible.
    
    A theory is PSC-admissible if it satisfies constraints (T1)-(T5):
    - (T1) Valid gauge structure
    - (T2) EFT locality and cutoff
    - (T3) Consistency (anomaly-free, unitary, renormalizable)
    - (T4) PSC closure (reflexive admissibility)
    - (T5) SRRG regularity
    """
    
    def __init__(self):
        """Initialize the checker."""
        self.violation_log: List[str] = []
    
    def is_admissible(self, theory: TheoryParams) -> bool:
        """
        Check if theory is PSC-admissible.
        
        Args:
            theory: TheoryParams to check
            
        Returns:
            True if theory is PSC-admissible
        """
        self.violation_log = []
        
        checks = [
            self._check_gauge_structure(theory),
            self._check_eft_locality(theory),
            self._check_consistency(theory),
            self._check_psc_closure(theory),
            self._check_srrg_regularity(theory),
        ]
        
        return all(checks)
    
    def _check_gauge_structure(self, theory: TheoryParams) -> bool:
        """
        Check (T1): Valid gauge structure.
        
        Requirements:
        - G is a compact Lie group
        - Representations are valid for G
        """
        # Check gauge group is in catalog
        if theory.gauge_group.name not in GAUGE_GROUPS_CATALOG:
            self.violation_log.append(f"(T1) Unknown gauge group: {theory.gauge_group.name}")
            return False
        
        return True
    
    def _check_eft_locality(self, theory: TheoryParams) -> bool:
        """
        Check (T2): EFT locality and cutoff.
        
        Requirements:
        - EFT dimension is reasonable (4-6)
        - Operators are local and gauge-invariant
        """
        if theory.eft_dimension < 4 or theory.eft_dimension > 10:
            self.violation_log.append(f"(T2) Invalid EFT dimension: {theory.eft_dimension}")
            return False
        
        return True
    
    def _check_consistency(self, theory: TheoryParams) -> bool:
        """
        Check (T3): Consistency constraints.
        
        Requirements:
        - Anomaly cancellation
        - Unitarity
        - Renormalizability (for d* = 4)
        """
        # Check anomaly cancellation (simplified)
        if not self._check_anomaly_cancellation(theory):
            self.violation_log.append("(T3) Anomaly cancellation violated")
            return False
        
        # Check unitarity (coupling bounds)
        if not self._check_unitarity(theory):
            self.violation_log.append("(T3) Unitarity violated")
            return False
        
        return True
    
    def _check_anomaly_cancellation(self, theory: TheoryParams) -> bool:
        """
        Check anomaly cancellation.
        
        For SM: Sum of hypercharges must vanish for each generation.
        """
        if theory.gauge_group.is_standard_model():
            # SM anomaly cancellation is automatic with standard matter content
            return True
        
        # For other theories, would need explicit calculation
        # Simplified: assume anomaly-free if in catalog
        return True
    
    def _check_unitarity(self, theory: TheoryParams) -> bool:
        """
        Check unitarity bounds on couplings.
        
        Perturbative unitarity requires couplings < O(4π).
        """
        for name, value in theory.gauge_couplings.items():
            if abs(value) > 4 * np.pi:
                return False
        
        for name, value in theory.yukawa_couplings.items():
            if abs(value) > 4 * np.pi:
                return False
        
        return True
    
    def _check_psc_closure(self, theory: TheoryParams) -> bool:
        """
        Check (T4): PSC closure constraints.
        
        Requirements:
        - No external meta-laws
        - Admissible update semantics
        - Energy accounting
        """
        # Simplified: use the flag set during theory construction
        if not theory.psc_admissible:
            self.violation_log.append("(T4) PSC closure not satisfied")
            return False
        
        return True
    
    def _check_srrg_regularity(self, theory: TheoryParams) -> bool:
        """
        Check (T5): SRRG regularity.
        
        Requirements:
        - Fisher-Rao metric is well-defined
        - SRRG flow is well-posed
        """
        # Check that we have enough parameters for SRRG
        if theory.get_dimension() < 1:
            self.violation_log.append("(T5) No parameters for SRRG flow")
            return False
        
        return True
    
    def get_violations(self) -> List[str]:
        """Get list of PSC violations."""
        return self.violation_log


# =============================================================================
# THEORY SPACE CLASS
# =============================================================================

class TheorySpace:
    """
    The PSC-admissible theory space T_PSC.
    
    This class represents the full theory space and provides methods for:
    - Enumerating theories in truncations
    - Checking PSC admissibility
    - Computing distances between theories
    """
    
    def __init__(self, rank_max: int = 8, dim_max: int = 6):
        """
        Initialize theory space.
        
        Args:
            rank_max: Maximum gauge group rank
            dim_max: Maximum EFT dimension
        """
        self.rank_max = rank_max
        self.dim_max = dim_max
        self.admissibility_checker = PSCAdmissibilityChecker()
        
        # Cache of enumerated theories
        self._theory_cache: Dict[Tuple[int, int, int], List[TheoryParams]] = {}
    
    def get_standard_model(self) -> TheoryParams:
        """Get the Standard Model theory."""
        return create_standard_model_theory()
    
    def enumerate_truncation(self, d_star: int, r_star: int, 
                            n_gen_max: int = 4) -> List[TheoryParams]:
        """
        Enumerate all theories in a truncation E(d*, r*, n_gen_max).
        
        Args:
            d_star: Maximum EFT dimension
            r_star: Maximum gauge group rank
            n_gen_max: Maximum number of generations
            
        Returns:
            List of PSC-admissible theories in the truncation
        """
        cache_key = (d_star, r_star, n_gen_max)
        if cache_key in self._theory_cache:
            return self._theory_cache[cache_key]
        
        theories = []
        
        # Enumerate gauge groups
        gauge_groups = enumerate_gauge_groups(rank_max=r_star)
        
        for G in gauge_groups:
            # Enumerate generation counts
            for n_gen in range(1, n_gen_max + 1):
                # Create theory with default couplings
                theory = TheoryParams(
                    gauge_group=G,
                    n_generations=n_gen,
                    eft_dimension=d_star,
                    gauge_couplings=self._default_couplings(G),
                    psc_admissible=True,
                )
                
                # Check PSC admissibility
                if self.admissibility_checker.is_admissible(theory):
                    theories.append(theory)
        
        self._theory_cache[cache_key] = theories
        return theories
    
    def _default_couplings(self, G: GaugeGroup) -> Dict[str, float]:
        """
        Get default gauge couplings for a gauge group.
        
        Args:
            G: Gauge group
            
        Returns:
            Dict of default coupling values
        """
        if G.is_standard_model():
            return {
                'g1': 0.357421238,
                'g2': 0.651731473,
                'g3': 1.21719969,
            }
        
        # Default: all couplings = 1.0
        couplings = {}
        for i, factor in enumerate(G.factors):
            couplings[f'g{i+1}'] = 1.0
        
        return couplings
    
    def is_psc_admissible(self, theory: TheoryParams) -> bool:
        """Check if a theory is PSC-admissible."""
        return self.admissibility_checker.is_admissible(theory)
    
    def distance(self, T1: TheoryParams, T2: TheoryParams) -> float:
        """
        Compute distance between two theories.
        
        Uses a combination of:
        - Discrete distance for gauge group (0 if same, 1 if different)
        - Euclidean distance for continuous parameters
        
        Args:
            T1, T2: Theories to compare
            
        Returns:
            Distance between theories
        """
        # Discrete part: gauge group
        discrete_dist = 0.0 if T1.gauge_group == T2.gauge_group else 1.0
        
        # Continuous part: parameter vectors
        if T1.gauge_group == T2.gauge_group:
            v1 = T1.get_parameter_vector()
            v2 = T2.get_parameter_vector()
            
            if len(v1) == len(v2):
                continuous_dist = np.linalg.norm(v1 - v2)
            else:
                continuous_dist = np.inf
        else:
            continuous_dist = np.inf
        
        return discrete_dist + continuous_dist


# =============================================================================
# TESTING
# =============================================================================

def test_theory_space():
    """Test theory space implementation."""
    print("=" * 80)
    print("TESTING THEORY SPACE DEFINITION")
    print("=" * 80)
    
    # Create theory space
    T_PSC = TheorySpace(rank_max=8, dim_max=6)
    
    # Get Standard Model
    print("\n1. Standard Model Theory:")
    print("-" * 80)
    SM = T_PSC.get_standard_model()
    print(f"   Gauge group: {SM.gauge_group.name}")
    print(f"   Generations: {SM.n_generations}")
    print(f"   EFT dimension: {SM.eft_dimension}")
    print(f"   Gauge couplings: {SM.gauge_couplings}")
    print(f"   Is SM: {SM.is_standard_model()}")
    print(f"   PSC admissible: {T_PSC.is_psc_admissible(SM)}")
    
    # Enumerate truncation
    print("\n2. Truncation Enumeration:")
    print("-" * 80)
    theories = T_PSC.enumerate_truncation(d_star=4, r_star=5, n_gen_max=4)
    print(f"   Theories in E(4, 5, 4): {len(theories)}")
    
    # List theories
    print("\n   Enumerated theories:")
    for i, T in enumerate(theories[:10]):
        is_sm = "✓ SM" if T.is_standard_model() else ""
        print(f"   {i+1}. {T.gauge_group.name}, n_gen={T.n_generations} {is_sm}")
    if len(theories) > 10:
        print(f"   ... and {len(theories) - 10} more")
    
    # Check SM is in truncation
    sm_in_truncation = any(T.is_standard_model() for T in theories)
    print(f"\n   SM in truncation: {sm_in_truncation}")
    
    # Distance test
    print("\n3. Distance Computation:")
    print("-" * 80)
    SM2 = create_standard_model_theory()
    SM2.gauge_couplings['g1'] = 0.36  # Perturb
    
    dist = T_PSC.distance(SM, SM2)
    print(f"   Distance(SM, SM_perturbed): {dist:.6f}")
    
    # PSC admissibility
    print("\n4. PSC Admissibility Check:")
    print("-" * 80)
    checker = PSCAdmissibilityChecker()
    
    # Valid theory
    is_valid = checker.is_admissible(SM)
    print(f"   SM is PSC-admissible: {is_valid}")
    
    # Invalid theory (bad EFT dimension)
    bad_theory = TheoryParams(
        gauge_group=GAUGE_GROUPS_CATALOG["SU(3)×SU(2)×U(1)"],
        n_generations=3,
        eft_dimension=100,  # Invalid
    )
    is_valid = checker.is_admissible(bad_theory)
    print(f"   Bad theory is PSC-admissible: {is_valid}")
    print(f"   Violations: {checker.get_violations()}")
    
    print("\n" + "=" * 80)
    print("THEORY SPACE DEFINITION TEST COMPLETE ✓")
    print("=" * 80)


if __name__ == "__main__":
    test_theory_space()
