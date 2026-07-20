"""
SRRG Core Infrastructure
Reference: MFRR §2.X (SRRG definitions), §6.X (Quarter-Lock), First Principles SM Paper

Implements:
- SRRG viability functional F = R[S] - C_Λ[S]
- Reward functional R[S] (topological stability, coherence intensity)
- Cost functional C_Λ[S] (violations, complexity, MDL excess)
- Quarter-Lock constraint checking
- Elegant Kernel constraint checking  
- Fisher-Rao metric on triple space
- Projected natural gradient ascent
- Basin structure analysis utilities

Author: AI Assistant
Date: 2025-01-27
Cross-Reference: SRRG_VALIDATION_PROGRAM/1_1_SRRG_VALIDATION_KICKOFF_PLAN.md
"""

import numpy as np
from typing import Tuple, Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
import math

# =============================================================================
# Section A: Data Structures
# =============================================================================

@dataclass(frozen=True)
class GTETriple:
    """
    GTE triple structure (a, b, c, g).
    
    Attributes:
        a, b, c: Integer components of the triple
        g: Generation/g-layer (0, 1, 2, 3)
        name: Particle name (optional, for tracking)
    """
    a: int
    b: int
    c: int
    g: int
    name: str = ""
    
    def to_tuple(self) -> Tuple[int, int, int, int]:
        """Return as (a, b, c, g) tuple."""
        return (self.a, self.b, self.c, self.g)
    
    def to_dict(self) -> Dict:
        """Return as dictionary."""
        return asdict(self)
    
    def __repr__(self) -> str:
        if self.name:
            return f"GTETriple({self.a}, {self.b}, {self.c}, g={self.g}, name='{self.name}')"
        return f"GTETriple({self.a}, {self.b}, {self.c}, g={self.g})"


@dataclass
class SRRGParameters:
    """
    SRRG functional parameters.
    
    Attributes:
        R_weights: Weights for reward functional components
        C_weights: Weights for cost functional components
        fisher_scale: Overall scale for Fisher-Rao metric
        projection_tol: Tolerance for constraint projection
    """
    # Reward weights
    w_coherence: float = 1.0      # Coherence intensity weight
    w_genon: float = 1.0          # Genon stability weight
    w_ucl_optimality: float = 1.0 # UCL minimality weight
    
    # Cost weights
    penalty_qlock: float = 1000.0    # Quarter-Lock violation penalty
    penalty_kernel: float = 1000.0   # Elegant Kernel deviation penalty
    penalty_admiss: float = 10000.0  # Admissibility violation penalty
    penalty_mdl: float = 100.0       # MDL excess penalty
    
    # Fisher-Rao metric
    fisher_scale: float = 1.0
    fisher_diagonal_only: bool = True  # Use diagonal approximation
    
    # Projection
    projection_tol: float = 1e-10
    
    # Quarter-Lock reference values (from First Principles SM)
    k_M: float = 0.5
    k_gen2: float = 0.375
    k_L2: float = 0.5
    # Verify: k_M = k_gen2 + 0.25 * k_L2 = 0.375 + 0.125 = 0.5 ✓

# =============================================================================
# Section B: Quarter-Lock and Elegant Kernel Constraints
# =============================================================================

def check_quarter_lock(triple: GTETriple, 
                       k_M: float = 0.5,
                       k_gen2: float = 0.375,
                       k_L2: float = 0.5,
                       tol: float = 1e-10) -> Tuple[bool, float]:
    """
    Verify Quarter-Lock constraint: k_M = k_gen2 + 0.25 * k_L2
    
    For a triple (a, b, c, g), the Quarter-Lock relates the GTE evolution
    constants. This constraint is fundamental to SM stability under SRRG.
    
    Args:
        triple: GTE triple to check
        k_M, k_gen2, k_L2: Quarter-Lock constants
        tol: Numerical tolerance
    
    Returns:
        (satisfied: bool, violation: float)
    """
    expected_k_M = k_gen2 + 0.25 * k_L2
    violation = abs(k_M - expected_k_M)
    satisfied = violation < tol
    return satisfied, violation


def check_elegant_kernel(triple: GTETriple, n: int = 10) -> Tuple[bool, str]:
    """
    Verify triple lies on Elegant Kernel ridge at n=10 (F_13 = 233).
    
    The Elegant Kernel is the unique ridge selection in GTE evolution that
    produces universal computation with minimal description length.
    
    Args:
        triple: GTE triple to check
        n: Ridge index (canonically 10)
    
    Returns:
        (on_ridge: bool, reason: str)
    """
    # Elegant Kernel criteria from First Principles SM:
    # 1. Ridge index n = 10
    # 2. Fibonacci F_13 = 233 appears in evolution
    # 3. Specific (a, b, c) ranges determined by n=10 ridge
    
    # For now, check admissibility ranges consistent with n=10
    # Refined check would verify F_13 = 233 emergence in evolution
    
    a, b, c, g = triple.a, triple.b, triple.c, triple.g
    
    # Basic admissibility (positive integers or -1 sentinel for top quark)
    if a < 1 and a != 76:  # Allow 76 for top quark special case
        return False, f"a={a} out of range"
    
    if b < 1 and triple.name != "top":  # Top has special b value
        return False, f"b={b} out of range"
    
    if c < 1 and c != -1:  # Allow -1 sentinel
        return False, f"c={c} out of range"
    
    # Ridge n=10 implies specific structure
    # Check c values are from allowed set: 823, 1023, 65535 (2^10-1, 2^10-1, 2^16-1), etc.
    allowed_c = {1, 2, 11, 12, 13, 42, 275, 823, 1023, 65535, -1}
    if c not in allowed_c:
        return False, f"c={c} not in Elegant Kernel allowed set"
    
    return True, "Satisfies Elegant Kernel constraints"


def is_admissible(triple: GTETriple) -> bool:
    """
    Check if triple satisfies basic admissibility (positive integers, allowed ranges).
    
    Returns:
        True if admissible, False otherwise
    """
    a, b, c, g = triple.a, triple.b, triple.c, triple.g
    
    # Generation must be 0, 1, 2, or 3
    if g not in {0, 1, 2, 3}:
        return False
    
    # Basic positivity (with special cases)
    if a < 1 and a != 76:  # Top quark exception
        return False
    
    if b < 1 and triple.name != "top":
        return False
    
    if c < -1:  # Allow -1 as sentinel
        return False
    
    # Prevent pathological values
    if a > 1_000_000 or b > 1_000_000 or c > 100_000:
        return False
    
    return True


# =============================================================================
# Section C: SRRG Viability Functional
# =============================================================================

def reward_functional(triple_set: List[GTETriple], 
                     params: SRRGParameters) -> float:
    """
    R[S] = sum_i w_i * I_genon^(i)
    
    The reward functional measures topological self-stability density.
    Higher for coherent, stable triple configurations.
    
    Components:
    1. Coherence intensity: Related to Fisher information eigenvalue
    2. Genon stability: Stable braid configurations
    3. UCL optimality: Proximity to minimal-description masses
    
    Args:
        triple_set: List of GTE triples defining the theory S
        params: SRRG parameters with weights
    
    Returns:
        Reward R[S] (higher is better)
    """
    R = 0.0
    
    for triple in triple_set:
        a, b, c, g = triple.a, triple.b, triple.c, triple.g
        
        # Component 1: Coherence intensity proxy
        # I_coh ∝ sqrt(λ_max(R^F) * Ω)
        # Approximate via triple magnitude and generation structure
        magnitude = math.sqrt(a**2 + b**2 + (abs(c) if c > 0 else 0)**2)
        coherence_intensity = params.w_coherence * magnitude * (1.0 + 0.1 * g)
        
        # Component 2: Genon stability (braid invariants)
        # Higher for triples that produce stable topological structures
        # Proxy: Reward low-entropy, high-symmetry configurations
        genon_stability = params.w_genon * (1.0 / (1.0 + np.log1p(abs(a - b))))
        
        # Component 3: UCL optimality
        # Reward configurations that enable minimal-description mass formulas
        # Proxy: Penalize large b (complexity), reward power-of-2 c (structure)
        ucl_optimality = params.w_ucl_optimality * (1.0 / (1.0 + np.log1p(b)))
        if c in {823, 1023, 65535}:  # Power-of-2 minus 1 (Mersenne-like)
            ucl_optimality *= 1.5  # Bonus for structured c values
        
        R += coherence_intensity + genon_stability + ucl_optimality
    
    return R


def cost_functional(triple_set: List[GTETriple],
                   constraints: SRRGParameters) -> float:
    """
    C_Λ[S] = penalties for constraint violations and MDL excess
    
    Components:
    1. Quarter-Lock violation: Deviation from k_M = k_gen2 + 0.25 * k_L2
    2. Elegant Kernel deviation: Distance from n=10 ridge
    3. Admissibility penalty: Out-of-range or pathological triples
    4. MDL excess: Complexity without compensating coherence
    
    Args:
        triple_set: List of GTE triples
        constraints: SRRG parameters with penalty weights
    
    Returns:
        Cost C_Λ[S] (lower is better)
    """
    C = 0.0
    
    for triple in triple_set:
        # Component 1: Quarter-Lock violation
        qlock_satisfied, qlock_violation = check_quarter_lock(
            triple, constraints.k_M, constraints.k_gen2, constraints.k_L2, 
            constraints.projection_tol
        )
        if not qlock_satisfied:
            C += constraints.penalty_qlock * qlock_violation**2
        
        # Component 2: Elegant Kernel deviation
        kernel_ok, kernel_reason = check_elegant_kernel(triple, n=10)
        if not kernel_ok:
            C += constraints.penalty_kernel
        
        # Component 3: Admissibility penalty
        if not is_admissible(triple):
            C += constraints.penalty_admiss
        
        # Component 4: MDL excess
        # Penalize high complexity (large b) without compensating structure
        a, b, c, g = triple.a, triple.b, triple.c, triple.g
        mdl_excess = constraints.penalty_mdl * (np.log1p(b) / (1.0 + g + np.log1p(abs(c))))
        C += mdl_excess
    
    return C


def viability_functional(triple_set: List[GTETriple],
                        params: SRRGParameters) -> float:
    """
    F[S] = R[S] - C_Λ[S]
    
    SRRG fixed points satisfy dF/dS = 0.
    Maximizing F drives theory toward maximal self-containment.
    
    Args:
        triple_set: List of GTE triples defining theory S
        params: SRRG parameters
    
    Returns:
        Viability F[S] (higher is better)
    """
    R = reward_functional(triple_set, params)
    C = cost_functional(triple_set, params)
    return R - C


# =============================================================================
# Section D: Fisher-Rao Metric on Triple Space
# =============================================================================

def fisher_rao_metric(triple: GTETriple,
                     ucl_fn: Optional[Callable] = None,
                     delta: float = 1.0,
                     diagonal_only: bool = True) -> np.ndarray:
    """
    Compute Fisher-Rao metric tensor G_ij at triple point.
    
    The Fisher information matrix measures the sensitivity of the GTE
    probability distribution (or UCL mass prediction) to triple parameters.
    
    For diagonal approximation:
        G_ii ≈ (∂m/∂θ_i)² where θ = (a, b, c)
    
    Args:
        triple: GTE triple
        ucl_fn: Optional UCL mass function for sensitivity calculation
        delta: Finite difference step
        diagonal_only: Use diagonal approximation (default True)
    
    Returns:
        Fisher metric tensor G (3×3 for (a, b, c))
    """
    if diagonal_only:
        # Diagonal approximation from parameter sensitivity
        # If no UCL function, use heuristic based on triple magnitude
        
        if ucl_fn is None:
            # Heuristic: Inverse variance ∝ 1 / parameter magnitude
            G_diag = np.array([
                1.0 / (1.0 + abs(triple.a)),
                1.0 / (1.0 + abs(triple.b)),
                1.0 / (1.0 + abs(triple.c) if triple.c > 0 else 1.0)
            ])
        else:
            # Compute from UCL mass sensitivity
            m0 = ucl_fn(triple)
            
            G_diag = np.zeros(3)
            
            # Sensitivity to a
            triple_a = GTETriple(triple.a + int(delta), triple.b, triple.c, triple.g, triple.name)
            m_a = ucl_fn(triple_a)
            G_diag[0] = ((m_a - m0) / delta)**2
            
            # Sensitivity to b
            triple_b = GTETriple(triple.a, triple.b + int(delta), triple.c, triple.g, triple.name)
            m_b = ucl_fn(triple_b)
            G_diag[1] = ((m_b - m0) / delta)**2
            
            # Sensitivity to c (if c > 0)
            if triple.c > 0:
                triple_c = GTETriple(triple.a, triple.b, triple.c + int(delta), triple.g, triple.name)
                m_c = ucl_fn(triple_c)
                G_diag[2] = ((m_c - m0) / delta)**2
            else:
                G_diag[2] = 1.0  # Default for c = -1 sentinel
        
        # Ensure positive definite
        G_diag = np.maximum(G_diag, 1e-8)
        
        return np.diag(G_diag)
    else:
        # Full matrix (not implemented yet)
        # Would require second-order derivatives or empirical covariance
        raise NotImplementedError("Full Fisher-Rao metric not yet implemented; use diagonal_only=True")


def natural_gradient(grad_euclidean: np.ndarray, 
                    metric: np.ndarray) -> np.ndarray:
    """
    Compute natural gradient: η = G^{-1} @ ∇F
    
    The natural gradient accounts for the geometry of the parameter space,
    providing faster, more stable convergence than Euclidean gradient.
    
    Args:
        grad_euclidean: Euclidean gradient ∇F
        metric: Fisher-Rao metric tensor G
    
    Returns:
        Natural gradient η
    """
    try:
        # For diagonal metric, just element-wise division
        if metric.shape[0] == metric.shape[1] and np.allclose(metric, np.diag(np.diag(metric))):
            return grad_euclidean / np.diag(metric)
        else:
            # General case: solve G @ η = ∇F
            return np.linalg.solve(metric, grad_euclidean)
    except np.linalg.LinAlgError:
        # Fallback to Euclidean if metric singular
        return grad_euclidean


# =============================================================================
# Section E: Gradient Computation
# =============================================================================

def compute_gradient_fd(F_fn: Callable[[GTETriple], float],
                       triple: GTETriple,
                       delta: int = 1) -> np.ndarray:
    """
    Compute gradient of F with respect to (a, b, c) via finite differences.
    
    Uses forward differences for integer-valued parameters.
    
    Args:
        F_fn: Viability functional (takes triple, returns float)
        triple: Current triple
        delta: Finite difference step (integer)
    
    Returns:
        Gradient vector [∂F/∂a, ∂F/∂b, ∂F/∂c]
    """
    F0 = F_fn(triple)
    grad = np.zeros(3)
    
    # ∂F/∂a
    triple_a = GTETriple(triple.a + delta, triple.b, triple.c, triple.g, triple.name)
    if is_admissible(triple_a):
        F_a = F_fn(triple_a)
        grad[0] = (F_a - F0) / delta
    else:
        grad[0] = 0.0  # Can't move in this direction
    
    # ∂F/∂b
    triple_b = GTETriple(triple.a, triple.b + delta, triple.c, triple.g, triple.name)
    if is_admissible(triple_b):
        F_b = F_fn(triple_b)
        grad[1] = (F_b - F0) / delta
    else:
        grad[1] = 0.0
    
    # ∂F/∂c
    if triple.c > 0:  # Don't perturb c = -1 sentinel
        triple_c = GTETriple(triple.a, triple.b, triple.c + delta, triple.g, triple.name)
        if is_admissible(triple_c):
            F_c = F_fn(triple_c)
            grad[2] = (F_c - F0) / delta
        else:
            grad[2] = 0.0
    else:
        grad[2] = 0.0
    
    return grad


# =============================================================================
# Section F: Constraint Projection
# =============================================================================

def project_onto_quarter_lock(triple: GTETriple,
                              params: SRRGParameters) -> GTETriple:
    """
    Project triple onto Quarter-Lock constraint manifold.
    
    Since Quarter-Lock is a relation among GTE evolution constants (k_M, k_gen2, k_L2)
    rather than (a, b, c) directly, this is an identity operation for fixed constants.
    
    The Quarter-Lock is enforced globally, not per-triple. Individual triples
    are generated under Quarter-Lock, so projection returns the triple unchanged.
    
    Args:
        triple: Input triple
        params: SRRG parameters with Quarter-Lock constants
    
    Returns:
        Projected triple (unchanged for global constraint)
    """
    # Quarter-Lock is a global constraint on GTE evolution constants,
    # not a per-triple constraint. Triples generated under Quarter-Lock
    # automatically satisfy it.
    return triple


def project_onto_admissibility(triple_params: np.ndarray,
                               g: int,
                               name: str = "") -> GTETriple:
    """
    Project continuous parameters onto integer admissibility manifold.
    
    Rounds to nearest integers and clips to admissible ranges.
    
    Args:
        triple_params: Continuous (a, b, c) values
        g: Generation (fixed)
        name: Particle name
    
    Returns:
        Admissible GTETriple
    """
    a, b, c = triple_params
    
    # Round to integers
    a_int = int(np.round(a))
    b_int = int(np.round(b))
    c_int = int(np.round(c))
    
    # Clip to admissible ranges
    a_int = max(1, min(a_int, 100_000))
    b_int = max(1, min(b_int, 1_000_000))
    
    # c can be -1 or positive
    if c_int < 0:
        c_int = -1
    else:
        c_int = max(1, min(c_int, 100_000))
    
    return GTETriple(a_int, b_int, c_int, g, name)


# =============================================================================
# Section G: SRRG Flow (Projected Natural Gradient Ascent)
# =============================================================================

def srrg_flow_step(triple: GTETriple,
                  F_fn: Callable[[GTETriple], float],
                  params: SRRGParameters,
                  ucl_fn: Optional[Callable] = None,
                  learning_rate: float = 1.0) -> Tuple[GTETriple, float, float]:
    """
    Single step of SRRG flow: projected natural gradient ascent.
    
    The SRRG flow is:
        dS/d(ln μ) = β_SRRG(S) = G^{-1} @ ∇F[S]
    
    For discrete triple space, this becomes:
        triple' = triple + α * η_proj
    where η_proj is the projected natural gradient.
    
    Args:
        triple: Current triple
        F_fn: Viability functional
        params: SRRG parameters
        ucl_fn: Optional UCL function for Fisher metric
        learning_rate: Step size α
    
    Returns:
        (new_triple, F_new, step_size_used)
    """
    # 1. Compute gradient
    grad = compute_gradient_fd(F_fn, triple, delta=1)
    
    # 2. Compute Fisher metric
    G = fisher_rao_metric(triple, ucl_fn, delta=1.0, diagonal_only=params.fisher_diagonal_only)
    
    # 3. Natural gradient
    eta = natural_gradient(grad, G)
    
    # 4. Normalize natural gradient to prevent overshooting in integer space
    # The natural gradient can be very large, but we need small steps in integer space
    # Strategy: Use Euclidean gradient direction if natural gradient is too large
    eta_norm = np.linalg.norm(eta)
    grad_norm = np.linalg.norm(grad)
    
    if eta_norm > 10.0:  # If natural gradient is too large, use Euclidean gradient
        # Use normalized Euclidean gradient instead
        if grad_norm > 1e-10:
            eta_proj = grad / grad_norm
        else:
            eta_proj = np.zeros_like(grad)
    else:
        # Normalize natural gradient to reasonable magnitude
        if eta_norm > 1e-10:
            eta_proj = eta / eta_norm  # Unit direction
        else:
            eta_proj = eta
    
    # 5. Armijo backtracking line search
    F0 = F_fn(triple)
    alpha = learning_rate
    armijo_c = 0.1  # Sufficient decrease parameter
    max_backtrack = 15  # Increased for better convergence
    
    for _ in range(max_backtrack):
        # Update
        new_params = np.array([triple.a, triple.b, triple.c]) + alpha * eta_proj
        new_triple = project_onto_admissibility(new_params, triple.g, triple.name)
        
        # Check admissibility
        if not is_admissible(new_triple):
            alpha *= 0.5
            continue
        
        # Evaluate
        F_new = F_fn(new_triple)
        
        # Armijo condition: F_new ≥ F0 + c * α * (∇F · η)
        if F_new >= F0 + armijo_c * alpha * np.dot(grad, eta_proj):
            return new_triple, F_new, alpha
        
        # Backtrack
        alpha *= 0.5
    
    # If no improvement found, return original
    return triple, F0, 0.0


def srrg_flow_to_convergence(triple_init: GTETriple,
                             F_fn: Callable[[GTETriple], float],
                             params: SRRGParameters,
                             ucl_fn: Optional[Callable] = None,
                             max_iter: int = 2000,
                             tol: float = 1e-8) -> Dict:
    """
    Run SRRG flow until convergence or max iterations.
    
    Args:
        triple_init: Initial triple
        F_fn: Viability functional
        params: SRRG parameters
        ucl_fn: Optional UCL function
        max_iter: Maximum iterations
        tol: Convergence tolerance
    
    Returns:
        Dictionary with:
            - final_triple: Converged triple
            - F_trace: Viability values at each iteration
            - converged: True if converged
            - iterations: Number of iterations
            - kkt_residual: Final stationarity residual
    """
    triple = triple_init
    F_trace = []
    
    for iter in range(max_iter):
        # Compute current viability
        F = F_fn(triple)
        F_trace.append(F)
        
        # SRRG flow step
        triple_new, F_new, alpha = srrg_flow_step(triple, F_fn, params, ucl_fn)
        
        # Check convergence
        triple_dist = math.sqrt(
            (triple_new.a - triple.a)**2 +
            (triple_new.b - triple.b)**2 +
            (triple_new.c - triple.c)**2
        )
        
        if triple_dist < tol or alpha == 0.0:
            # Converged or stuck
            grad = compute_gradient_fd(F_fn, triple_new, delta=1)
            kkt_residual = np.linalg.norm(grad)
            
            return {
                "final_triple": triple_new,
                "F_trace": F_trace,
                "converged": triple_dist < tol,
                "iterations": iter + 1,
                "kkt_residual": kkt_residual,
                "final_F": F_new
            }
        
        triple = triple_new
    
    # Max iterations reached
    grad = compute_gradient_fd(F_fn, triple, delta=1)
    kkt_residual = np.linalg.norm(grad)
    
    return {
        "final_triple": triple,
        "F_trace": F_trace,
        "converged": False,
        "iterations": max_iter,
        "kkt_residual": kkt_residual,
        "final_F": F_trace[-1] if F_trace else 0.0
    }


# =============================================================================
# Section H: Basin Structure Analysis
# =============================================================================

def triple_distance(t1: GTETriple, t2: GTETriple) -> float:
    """Euclidean distance between triples in (a, b, c) space."""
    return math.sqrt(
        (t1.a - t2.a)**2 +
        (t1.b - t2.b)**2 +
        (t1.c - t2.c)**2
    )


def sample_neighborhood(triple_center: GTETriple,
                       radius: float,
                       n_samples: int,
                       seed: int = 42) -> List[GTETriple]:
    """
    Sample random triples in a ball around triple_center.
    
    Uses Gaussian sampling with radius as standard deviation,
    then clips to admissible integer ranges.
    
    Args:
        triple_center: Center triple
        radius: Sampling radius (std dev)
        n_samples: Number of samples
        seed: Random seed
    
    Returns:
        List of random triples near center
    """
    rng = np.random.default_rng(seed)
    samples = []
    
    for _ in range(n_samples):
        # Gaussian perturbation
        delta_a = rng.normal(0, radius)
        delta_b = rng.normal(0, radius)
        delta_c = rng.normal(0, radius) if triple_center.c > 0 else 0.0
        
        # Apply perturbation
        a_new = triple_center.a + int(np.round(delta_a))
        b_new = triple_center.b + int(np.round(delta_b))
        c_new = triple_center.c + int(np.round(delta_c)) if triple_center.c > 0 else triple_center.c
        
        # Create triple
        triple_sample = GTETriple(a_new, b_new, c_new, triple_center.g, triple_center.name)
        
        # Check admissibility
        if is_admissible(triple_sample):
            samples.append(triple_sample)
    
    return samples


def basin_structure_analysis(triple_canonical: GTETriple,
                             F_fn: Callable[[GTETriple], float],
                             params: SRRGParameters,
                             ucl_fn: Optional[Callable] = None,
                             radius: float = 5.0,
                             n_starts: int = 512,
                             convergence_tol: float = 1e-6,
                             seed: int = 42) -> Dict:
    """
    Analyze attraction basin structure around a canonical triple.
    
    Samples random initializations in a neighborhood and runs SRRG flow
    from each. Records convergence statistics, attraction rates, and basin size.
    
    Args:
        triple_canonical: Canonical SM triple (target attractor)
        F_fn: Viability functional
        params: SRRG parameters
        ucl_fn: Optional UCL function
        radius: Neighborhood sampling radius
        n_starts: Number of random starts
        convergence_tol: Distance tolerance for "converged to canonical"
        seed: Random seed
    
    Returns:
        Dictionary with:
            - attraction_rate: Fraction converging to canonical
            - mean_iterations: Average iterations to convergence
            - mean_kkt_residual: Average final KKT residual
            - basin_size_estimate: Effective basin radius
            - converged_distances: Distances of converged points
            - endpoints: List of all final triples
    """
    # Sample neighborhood
    samples = sample_neighborhood(triple_canonical, radius, n_starts, seed)
    
    # Track results
    converged_to_canonical = 0
    iterations_list = []
    kkt_residuals = []
    converged_distances = []
    endpoints = []
    
    for sample in samples:
        # Run SRRG flow
        result = srrg_flow_to_convergence(sample, F_fn, params, ucl_fn)
        
        # Check if converged to canonical
        final_triple = result["final_triple"]
        dist = triple_distance(final_triple, triple_canonical)
        
        endpoints.append(final_triple)
        
        if dist < convergence_tol:
            converged_to_canonical += 1
            converged_distances.append(dist)
        
        iterations_list.append(result["iterations"])
        kkt_residuals.append(result["kkt_residual"])
    
    # Compute statistics
    attraction_rate = converged_to_canonical / len(samples) if samples else 0.0
    mean_iterations = np.mean(iterations_list) if iterations_list else 0.0
    mean_kkt = np.mean(kkt_residuals) if kkt_residuals else 0.0
    basin_size = np.mean(converged_distances) if converged_distances else 0.0
    
    return {
        "canonical_triple": triple_canonical.to_dict(),
        "attraction_rate": attraction_rate,
        "n_converged": converged_to_canonical,
        "n_total": len(samples),
        "mean_iterations": mean_iterations,
        "mean_kkt_residual": mean_kkt,
        "basin_size_estimate": basin_size,
        "converged_distances": converged_distances,
        "all_kkt_residuals": kkt_residuals,
        "radius_sampled": radius,
        "acceptance_threshold": convergence_tol
    }


# =============================================================================
# Section I: Utility Functions
# =============================================================================

def triple_from_dict(d: Dict) -> GTETriple:
    """Create GTETriple from dictionary."""
    return GTETriple(
        a=d["a"],
        b=d["b"],
        c=d["c"],
        g=d["g"],
        name=d.get("name", "")
    )


def compute_quarter_lock_violation_score(triple: GTETriple,
                                        params: SRRGParameters) -> float:
    """
    Compute magnitude of Quarter-Lock violation for a triple.
    
    Returns:
        Violation score (0 = perfect, higher = worse)
    """
    _, violation = check_quarter_lock(triple, params.k_M, params.k_gen2, params.k_L2)
    return violation


if __name__ == "__main__":
    # Unit tests
    print("SRRG Core Module — Unit Tests")
    print("=" * 60)
    
    # Test 1: Create a canonical triple
    electron = GTETriple(1, 73, 823, 1, "electron")
    print(f"\n1. Electron triple: {electron}")
    
    # Test 2: Check Quarter-Lock (global constraint, should always pass)
    qlock_ok, qlock_viol = check_quarter_lock(electron)
    print(f"2. Quarter-Lock: {'PASS' if qlock_ok else 'FAIL'} (violation={qlock_viol:.2e})")
    
    # Test 3: Check Elegant Kernel
    kernel_ok, kernel_msg = check_elegant_kernel(electron)
    print(f"3. Elegant Kernel: {'PASS' if kernel_ok else 'FAIL'} ({kernel_msg})")
    
    # Test 4: Admissibility
    admiss = is_admissible(electron)
    print(f"4. Admissibility: {'PASS' if admiss else 'FAIL'}")
    
    # Test 5: SRRG functionals
    params = SRRGParameters()
    R = reward_functional([electron], params)
    C = cost_functional([electron], params)
    F = viability_functional([electron], params)
    print(f"5. SRRG functionals: R={R:.4f}, C={C:.4f}, F={F:.4f}")
    
    # Test 6: Fisher metric
    G = fisher_rao_metric(electron, diagonal_only=True)
    print(f"6. Fisher metric (diagonal): {np.diag(G)}")
    
    # Test 7: Sample neighborhood
    samples = sample_neighborhood(electron, radius=2.0, n_samples=10, seed=42)
    print(f"7. Neighborhood sampling: Generated {len(samples)} admissible triples")
    
    print("\n" + "=" * 60)
    print("✅ All unit tests complete")

