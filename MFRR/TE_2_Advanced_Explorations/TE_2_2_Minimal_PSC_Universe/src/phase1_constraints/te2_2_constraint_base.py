"""
TE_2.2: Constraint Base Classes

Defines abstract base class for PSC universe constraints.

Cross-Reference:
- TE_2_2_1_KICKOFF.md
- TE_2_2_2_RESOURCE_SURVEY.md
- TE_2_X_6_IMPLEMENTATION_STRATEGY.md (lines 948-1483)

Author: AI Assistant
Date: 2025-11-20
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np


@dataclass
class UniverseParams:
    """
    Parameters defining a PSC universe.
    
    This is a simplified representation for the finite truncation.
    Full universe space is infinite-dimensional.
    """
    # Geometric parameters
    d: int = 4  # Spacetime dimensions (3+1)
    kappa: float = 0.0  # Curvature (0 = flat, >0 = positive, <0 = negative)
    topology: str = "flat"  # "flat", "spherical", "hyperbolic"
    
    # Gauge group
    gauge_group: str = "SU(3)xSU(2)xU(1)"  # SM gauge group
    gauge_couplings: Dict[str, float] = None  # {g1, g2, g3}
    
    # Matter content
    n_generations: int = 3
    yukawa_couplings: Dict[str, float] = None  # {y_t, y_b, y_tau, ...}
    
    # Cosmological parameters
    Lambda: float = 1e-122  # Cosmological constant (Planck units)
    
    # Coherence field
    psi_mass_squared: float = 0.0  # Ψ mass squared
    psi_coupling: float = 0.0  # Ψ self-coupling
    
    # Observer network
    n_observers: int = 1  # Number of reflexive observers
    profit_ratio: float = 1.13  # Gen/Drain ratio
    
    def __post_init__(self):
        """Initialize default dictionaries if not provided."""
        if self.gauge_couplings is None:
            # SM values at M_Z
            self.gauge_couplings = {
                'g1': 0.357421238,  # U(1)
                'g2': 0.651731473,  # SU(2)
                'g3': 1.21719969,   # SU(3)
            }
        
        if self.yukawa_couplings is None:
            # SM values at M_Z (top, bottom, tau)
            self.yukawa_couplings = {
                'y_t': 0.992281435,
                'y_b': 0.0240086617,
                'y_tau': 0.0102057490,
            }
    
    def is_sm_like(self, tol: float = 1e-3) -> bool:
        """Check if parameters are close to Standard Model."""
        if self.d != 4:
            return False
        if abs(self.kappa) > tol:
            return False
        if self.gauge_group != "SU(3)xSU(2)xU(1)":
            return False
        if self.n_generations != 3:
            return False
        # Check gauge couplings
        sm_g1 = 0.357421238
        sm_g2 = 0.651731473
        sm_g3 = 1.21719969
        if abs(self.gauge_couplings['g1'] - sm_g1) > tol:
            return False
        if abs(self.gauge_couplings['g2'] - sm_g2) > tol:
            return False
        if abs(self.gauge_couplings['g3'] - sm_g3) > tol:
            return False
        return True


@dataclass
class ConstraintViolation:
    """
    Represents a constraint violation.
    
    Attributes:
        constraint_name: Name of violated constraint
        violation_magnitude: ||C[Ψ]||² (squared norm)
        description: Human-readable description
        is_hard: If True, violation → D[Ψ] = ∞ (non-viable universe)
    """
    constraint_name: str
    violation_magnitude: float
    description: str
    is_hard: bool = False
    
    def __repr__(self) -> str:
        hard_str = " [HARD]" if self.is_hard else ""
        return f"{self.constraint_name}: ||C||² = {self.violation_magnitude:.6e}{hard_str}"


class PSCConstraint(ABC):
    """
    Abstract base class for PSC universe constraints.
    
    Each constraint C[Ψ] must:
    1. Evaluate to 0 for valid PSC universes
    2. Return violation magnitude ||C[Ψ]||²
    3. Indicate if violation is "hard" (→ infinite dissonance)
    """
    
    def __init__(self, weight: float = 1.0, name: str = ""):
        """
        Initialize constraint.
        
        Args:
            weight: Weight w_α in dissonance functional
            name: Human-readable constraint name
        """
        self.weight = weight
        self.name = name or self.__class__.__name__
    
    @abstractmethod
    def evaluate(self, universe: UniverseParams) -> float:
        """
        Evaluate constraint violation.
        
        Args:
            universe: Universe parameters
        
        Returns:
            ||C[Ψ]||²: Squared norm of constraint violation
        """
        pass
    
    @abstractmethod
    def is_satisfied(self, universe: UniverseParams, tol: float = 1e-6) -> bool:
        """
        Check if constraint is satisfied within tolerance.
        
        Args:
            universe: Universe parameters
            tol: Tolerance for satisfaction
        
        Returns:
            True if ||C[Ψ]||² < tol
        """
        pass
    
    @abstractmethod
    def get_description(self, universe: UniverseParams) -> str:
        """
        Get human-readable description of constraint status.
        
        Args:
            universe: Universe parameters
        
        Returns:
            Description string
        """
        pass
    
    def is_hard_constraint(self) -> bool:
        """
        Check if this is a hard constraint.
        
        Hard constraints: violation → D[Ψ] = ∞ (non-viable universe)
        Soft constraints: violation → finite contribution to D[Ψ]
        
        Returns:
            True if hard constraint
        """
        return False  # Override in subclasses
    
    def check_violation(self, universe: UniverseParams, tol: float = 1e-6) -> Optional[ConstraintViolation]:
        """
        Check for constraint violation.
        
        Args:
            universe: Universe parameters
            tol: Tolerance for satisfaction
        
        Returns:
            ConstraintViolation if violated, None if satisfied
        """
        violation_mag = self.evaluate(universe)
        
        if violation_mag < tol:
            return None  # Satisfied
        
        return ConstraintViolation(
            constraint_name=self.name,
            violation_magnitude=violation_mag,
            description=self.get_description(universe),
            is_hard=self.is_hard_constraint()
        )
    
    def contribution_to_dissonance(self, universe: UniverseParams) -> float:
        """
        Compute contribution to dissonance functional.
        
        D_α[Ψ] = w_α · ||C_α[Ψ]||²
        
        Args:
            universe: Universe parameters
        
        Returns:
            w_α · ||C_α[Ψ]||²
        """
        violation = self.evaluate(universe)
        
        if self.is_hard_constraint() and violation > 1e-6:
            return np.inf  # Hard constraint violation → infinite dissonance
        
        return self.weight * violation


class ConstraintCatalog:
    """
    Catalog of all PSC universe constraints.
    
    Manages collection of constraints and computes total dissonance.
    """
    
    def __init__(self):
        """Initialize empty catalog."""
        self.constraints: List[PSCConstraint] = []
    
    def add_constraint(self, constraint: PSCConstraint):
        """Add constraint to catalog."""
        self.constraints.append(constraint)
    
    def evaluate_all(self, universe: UniverseParams) -> Dict[str, float]:
        """
        Evaluate all constraints.
        
        Args:
            universe: Universe parameters
        
        Returns:
            Dictionary mapping constraint names to violation magnitudes
        """
        return {
            c.name: c.evaluate(universe)
            for c in self.constraints
        }
    
    def check_all_violations(self, universe: UniverseParams, tol: float = 1e-6) -> List[ConstraintViolation]:
        """
        Check all constraints for violations.
        
        Args:
            universe: Universe parameters
            tol: Tolerance for satisfaction
        
        Returns:
            List of constraint violations (empty if all satisfied)
        """
        violations = []
        for constraint in self.constraints:
            violation = constraint.check_violation(universe, tol)
            if violation is not None:
                violations.append(violation)
        return violations
    
    def is_viable(self, universe: UniverseParams, tol: float = 1e-6) -> bool:
        """
        Check if universe is viable (all constraints satisfied).
        
        Args:
            universe: Universe parameters
            tol: Tolerance for satisfaction
        
        Returns:
            True if all constraints satisfied
        """
        return len(self.check_all_violations(universe, tol)) == 0
    
    def total_dissonance(self, universe: UniverseParams) -> float:
        """
        Compute total dissonance functional.
        
        D[Ψ] = Σ_α w_α · ||C_α[Ψ]||²
        
        Args:
            universe: Universe parameters
        
        Returns:
            D[Ψ]: Total dissonance
        """
        total = 0.0
        for constraint in self.constraints:
            contribution = constraint.contribution_to_dissonance(universe)
            if np.isinf(contribution):
                return np.inf  # Hard constraint violated
            total += contribution
        return total
    
    def get_summary(self, universe: UniverseParams, tol: float = 1e-6) -> Dict:
        """
        Get summary of constraint status.
        
        Args:
            universe: Universe parameters
            tol: Tolerance for satisfaction
        
        Returns:
            Summary dictionary
        """
        violations = self.check_all_violations(universe, tol)
        n_hard = sum(1 for v in violations if v.is_hard)
        n_soft = len(violations) - n_hard
        
        return {
            'n_constraints': len(self.constraints),
            'n_satisfied': len(self.constraints) - len(violations),
            'n_violated': len(violations),
            'n_hard_violations': n_hard,
            'n_soft_violations': n_soft,
            'is_viable': len(violations) == 0,
            'total_dissonance': self.total_dissonance(universe),
            'violations': violations,
        }
    
    def print_summary(self, universe: UniverseParams, tol: float = 1e-6):
        """Print human-readable summary."""
        summary = self.get_summary(universe, tol)
        
        print("=" * 80)
        print("PSC UNIVERSE CONSTRAINT SUMMARY")
        print("=" * 80)
        print(f"Total constraints: {summary['n_constraints']}")
        print(f"Satisfied: {summary['n_satisfied']}")
        print(f"Violated: {summary['n_violated']}")
        print(f"  - Hard violations: {summary['n_hard_violations']}")
        print(f"  - Soft violations: {summary['n_soft_violations']}")
        print(f"Viable: {summary['is_viable']}")
        print(f"Total dissonance: D[Ψ] = {summary['total_dissonance']:.6e}")
        
        if summary['violations']:
            print("\nVIOLATIONS:")
            for v in summary['violations']:
                print(f"  {v}")
        
        print("=" * 80)


# Standard Model universe for testing
SM_UNIVERSE = UniverseParams(
    d=4,
    kappa=0.0,
    topology="flat",
    gauge_group="SU(3)xSU(2)xU(1)",
    n_generations=3,
    Lambda=1e-122,
)


if __name__ == "__main__":
    # Test base classes
    print("Testing PSC Constraint Base Classes")
    print("=" * 80)
    
    # Create SM universe
    sm = SM_UNIVERSE
    print(f"SM-like: {sm.is_sm_like()}")
    
    # Create empty catalog
    catalog = ConstraintCatalog()
    print(f"\nEmpty catalog: {len(catalog.constraints)} constraints")
    
    print("\nBase classes loaded successfully ✓")

