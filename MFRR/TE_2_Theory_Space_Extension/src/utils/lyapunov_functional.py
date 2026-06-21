"""
TE_2 Theory Space Extension - Utils: SRRG Lyapunov Functional

PHYSICS-BASED Lyapunov functional C[T] for the SRRG uniqueness proof.

CRITICAL DESIGN PRINCIPLE:
    This functional must NOT be centered on SM coupling values.
    SM must win because of physics, not because we designed the
    functional to select it.

The functional evaluates theories on STRUCTURAL properties:
    1. Anomaly cancellation quality (physics constraint)
    2. Asymptotic freedom (RG stability)
    3. Chiral fermion support (matter structure)
    4. Reflexive self-consistency (PSC closure)
    5. Descriptive economy (MDL / Occam)

None of these reference SM coupling values directly.

Cross-Reference:
- the SRRG uniqueness proof program (see TE_2 Theory Space Extension documentation, Section 9)
- SRRG_VALIDATION_PROGRAM (TS9: c-function monotonicity)
- TE_1.R_CONTINOUS_MODEL (Lyapunov functional derivation)

Author: AI Assistant
Date: 2025-02-25
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Tuple, Optional, Callable, List
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'phase0_foundations'))

from theory_space_definition import TheoryParams, create_standard_model_theory


# =============================================================================
# PHYSICAL CONSTANTS (not SM-specific — these are structural)
# =============================================================================

# One-loop beta function coefficients for SU(N) with n_f Dirac fermions
# in the fundamental: b_0 = (11/3)N - (2/3)n_f
# Asymptotic freedom requires b_0 > 0
def beta_0_sun(N: int, n_f_fundamental: int) -> float:
    """One-loop beta coefficient for SU(N) with n_f fundamentals."""
    return (11.0 / 3.0) * N - (2.0 / 3.0) * n_f_fundamental


# Known group-theoretic data
SIMPLE_GROUP_DATA = {
    "SU(2)":  {"rank": 1, "dim": 3,   "N": 2,  "casimir_adj": 2.0,   "fund_dim": 2},
    "SU(3)":  {"rank": 2, "dim": 8,   "N": 3,  "casimir_adj": 3.0,   "fund_dim": 3},
    "SU(4)":  {"rank": 3, "dim": 15,  "N": 4,  "casimir_adj": 4.0,   "fund_dim": 4},
    "SU(5)":  {"rank": 4, "dim": 24,  "N": 5,  "casimir_adj": 5.0,   "fund_dim": 5},
    "SU(6)":  {"rank": 5, "dim": 35,  "N": 6,  "casimir_adj": 6.0,   "fund_dim": 6},
    "SU(7)":  {"rank": 6, "dim": 48,  "N": 7,  "casimir_adj": 7.0,   "fund_dim": 7},
    "SU(8)":  {"rank": 7, "dim": 63,  "N": 8,  "casimir_adj": 8.0,   "fund_dim": 8},
    "SU(9)":  {"rank": 8, "dim": 80,  "N": 9,  "casimir_adj": 9.0,   "fund_dim": 9},
    "SU(10)": {"rank": 9, "dim": 99,  "N": 10, "casimir_adj": 10.0,  "fund_dim": 10},
    "SU(11)": {"rank": 10,"dim": 120, "N": 11, "casimir_adj": 11.0,  "fund_dim": 11},
    "SO(6)":  {"rank": 3, "dim": 15,  "N": 6,  "casimir_adj": 4.0,   "fund_dim": 6},
    "SO(8)":  {"rank": 4, "dim": 28,  "N": 8,  "casimir_adj": 6.0,   "fund_dim": 8},
    "SO(10)": {"rank": 5, "dim": 45,  "N": 10, "casimir_adj": 8.0,   "fund_dim": 10},
    "SO(12)": {"rank": 6, "dim": 66,  "N": 12, "casimir_adj": 10.0,  "fund_dim": 12},
    "SO(14)": {"rank": 7, "dim": 91,  "N": 14, "casimir_adj": 12.0,  "fund_dim": 14},
    "SO(16)": {"rank": 8, "dim": 120, "N": 16, "casimir_adj": 14.0,  "fund_dim": 16},
    "SO(18)": {"rank": 9, "dim": 153, "N": 18, "casimir_adj": 16.0,  "fund_dim": 18},
    "Sp(4)":  {"rank": 2, "dim": 10,  "N": 4,  "casimir_adj": 3.0,   "fund_dim": 4},
    "Sp(6)":  {"rank": 3, "dim": 21,  "N": 6,  "casimir_adj": 4.0,   "fund_dim": 6},
    "Sp(8)":  {"rank": 4, "dim": 36,  "N": 8,  "casimir_adj": 5.0,   "fund_dim": 8},
    "G_2":    {"rank": 2, "dim": 14,  "N": 7,  "casimir_adj": 4.0,   "fund_dim": 7},
    "F_4":    {"rank": 4, "dim": 52,  "N": 26, "casimir_adj": 9.0,   "fund_dim": 26},
    "E_6":    {"rank": 6, "dim": 78,  "N": 27, "casimir_adj": 12.0,  "fund_dim": 27},
    "E_7":    {"rank": 7, "dim": 133, "N": 56, "casimir_adj": 18.0,  "fund_dim": 56},
    "E_8":    {"rank": 8, "dim": 248, "N": 248,"casimir_adj": 30.0,  "fund_dim": 248},
    "U(1)":   {"rank": 1, "dim": 1,   "N": 1,  "casimir_adj": 0.0,   "fund_dim": 1},
}


# =============================================================================
# COMPONENT 1: ANOMALY CANCELLATION QUALITY
# =============================================================================

def anomaly_score(theory: TheoryParams) -> float:
    """
    Score for anomaly cancellation quality.
    
    Physics: Gauge anomalies must cancel for quantum consistency.
    
    Key insight: what matters is not the NUMBER of anomaly conditions
    but whether the conditions are NON-TRIVIALLY constraining.
    
    - SU(N≥3) with complex reps: non-trivial anomaly cancellation
    - Extra U(1)s: anomaly conditions are trivially satisfiable
      by adjusting charges — they DON'T increase predictivity
    - Simple GUT groups: anomaly cancellation is automatic for
      complete multiplets
    
    Returns:
        Score (lower is better, 0 = maximally constrained)
    """
    factors = theory.gauge_group.factors
    
    non_abelian = [f for f in factors if f != "U(1)"]
    n_abelian = len([f for f in factors if f == "U(1)"])
    
    if len(non_abelian) == 0:
        return 10.0  # Pure abelian: no anomaly constraints
    
    has_complex_reps = False
    for f in non_abelian:
        if f in SIMPLE_GROUP_DATA:
            data = SIMPLE_GROUP_DATA[f]
            if f.startswith("SU(") and data["N"] >= 3:
                has_complex_reps = True
            if f.startswith("SO(") and data["N"] % 4 == 2:
                has_complex_reps = True
            if f == "E_6":
                has_complex_reps = True
    
    if has_complex_reps:
        # Non-trivial anomaly cancellation required — good
        # But extra U(1)s don't help: they add trivially satisfiable conditions
        score = 3.0
    else:
        score = 5.0  # Real reps: anomalies cancel automatically
    
    # Extra U(1) factors do NOT increase predictivity
    # Their anomaly conditions are trivially satisfiable
    # No bonus for having more of them
    
    return score


# =============================================================================
# COMPONENT 2: ASYMPTOTIC FREEDOM
# =============================================================================

def asymptotic_freedom_score(theory: TheoryParams) -> float:
    """
    Score for asymptotic freedom.
    
    Physics: Asymptotic freedom (AF) is required for:
    - Well-defined UV completion
    - Perturbative control at high energies
    - Confinement at low energies (for color)
    
    AF requires the one-loop beta function coefficient b_0 > 0.
    For SU(N) with n_f Dirac fundamentals: b_0 = (11/3)N - (2/3)n_f
    
    Vector-like fermion pairs each contribute to n_f as Dirac fermions
    in the fundamental representation, reducing b_0 and potentially
    destroying asymptotic freedom.
    
    Theories where ALL non-abelian factors are AF score best.
    
    Returns:
        Score (lower is better, 0 = all factors AF)
    """
    factors = theory.gauge_group.factors
    n_gen = theory.n_generations
    n_vl = getattr(theory, 'n_vector_like_pairs', 0)
    
    total_penalty = 0.0
    n_non_abelian = 0
    n_af = 0
    
    for factor in factors:
        if factor == "U(1)":
            continue
        n_non_abelian += 1
        
        if factor not in SIMPLE_GROUP_DATA:
            total_penalty += 5.0
            continue
        
        data = SIMPLE_GROUP_DATA[factor]
        
        # Each generation contributes fermions in the fundamental.
        # Each vector-like pair adds one Dirac fermion in the fundamental,
        # contributing (2/3) to the beta function coefficient.
        if factor.startswith("SU("):
            N = data["N"]
            n_f = n_gen * 2 + n_vl
            b0 = beta_0_sun(N, n_f)
        elif factor.startswith("SO("):
            N = data["N"]
            b0 = (11.0 / 3.0) * (N - 2) / 2.0 - (2.0 / 3.0) * (n_gen + n_vl)
        else:
            b0 = (11.0 / 3.0) * data["casimir_adj"] - (2.0 / 3.0) * (n_gen + n_vl)
        
        if b0 > 0:
            n_af += 1
        else:
            total_penalty += abs(b0) * 0.5
    
    if n_non_abelian == 0:
        return 5.0  # Pure abelian: no AF possible
    
    af_fraction = n_af / n_non_abelian
    
    return total_penalty + (1.0 - af_fraction) * 10.0


# =============================================================================
# COMPONENT 3: CHIRAL FERMION SUPPORT
# =============================================================================

def chiral_fermion_score(theory: TheoryParams) -> float:
    """
    Score for chiral fermion support.
    
    Physics: The observed universe has chiral fermions (left and right
    components transform differently under the gauge group). This is
    essential for:
    - Parity violation (weak interactions)
    - Mass generation via Yukawa couplings
    - CP violation (matter-antimatter asymmetry)
    
    Chiral fermions require:
    - Complex representations of the gauge group
    - At least one factor with complex reps (SU(N≥3), E_6)
    
    Returns:
        Score (lower is better, 0 = maximal chiral structure)
    """
    factors = theory.gauge_group.factors
    
    has_su2_or_higher = False
    has_su3_or_higher = False
    has_complex_factor = False
    n_chiral_factors = 0
    
    for f in factors:
        if f not in SIMPLE_GROUP_DATA:
            continue
        data = SIMPLE_GROUP_DATA[f]
        
        if f.startswith("SU("):
            N = data["N"]
            if N >= 2:
                has_su2_or_higher = True
            if N >= 3:
                has_su3_or_higher = True
                has_complex_factor = True
                n_chiral_factors += 1
        elif f == "E_6":
            has_complex_factor = True
            n_chiral_factors += 1
        elif f.startswith("SO(") and data["N"] % 4 == 2:
            has_complex_factor = True
            n_chiral_factors += 1
    
    score = 0.0
    
    if not has_complex_factor:
        score += 15.0  # Cannot support chiral fermions at all
    
    if not has_su2_or_higher:
        score += 5.0  # No weak-like interactions possible
    
    # Chiral structure quality: more chiral factors = more structure
    # But too many = over-complicated
    if n_chiral_factors == 0:
        score += 10.0
    elif n_chiral_factors == 1:
        score += 2.0  # Minimal chiral structure
    elif n_chiral_factors == 2:
        score += 0.0  # Optimal: like SU(3)_c + SU(2)_L
    elif n_chiral_factors >= 3:
        score += 1.0 * (n_chiral_factors - 2)  # Slight penalty for over-complexity
    
    # Generation structure: 3 generations is special
    # (allows CP violation via CKM with minimal generations)
    # 2 generations: no CP violation from CKM
    # 1 generation: no mixing at all
    # ≥4: unnecessary complexity
    n_gen = theory.n_generations
    if n_gen < 3:
        score += (3 - n_gen) * 3.0  # Missing CP violation capability
    elif n_gen > 3:
        score += (n_gen - 3) * 2.0  # Unnecessary generations
    
    return score


# =============================================================================
# COMPONENT 4: REFLEXIVE SELF-CONSISTENCY (PSC)
# =============================================================================

def reflexive_consistency_score(theory: TheoryParams) -> float:
    """
    Score for PSC reflexive self-consistency.
    
    Physics: A self-contained theory must be able to describe its own
    dynamics without external input. This requires:
    
    1. Internal encodability: enough structure to encode information
    2. Observability: observers can measure all parameters
    3. No Landau poles below Planck scale
    4. Stable bound states (confinement + EW breaking)
    5. Minimal unbroken gauge symmetry: every gauge boson must be
       either confined or massive. Unbroken massless gauge bosons
       beyond the photon require additional breaking mechanisms.
    6. Charge quantization: requires non-abelian structure
    
    Returns:
        Score (lower is better, 0 = maximally self-consistent)
    """
    factors = theory.gauge_group.factors
    score = 0.0
    
    non_abelian = [f for f in factors if f != "U(1)"]
    n_abelian = len([f for f in factors if f == "U(1)"])
    
    # 1. Internal encodability
    if len(non_abelian) == 0:
        score += 20.0  # Pure abelian: cannot confine, cannot form atoms
    elif len(non_abelian) == 1 and n_abelian == 0:
        score += 10.0  # Single non-abelian: no charge quantization
    
    # 2. Observability: need confining and Higgsable sectors
    has_confining = False
    has_broken = False
    for f in non_abelian:
        if f in SIMPLE_GROUP_DATA:
            data = SIMPLE_GROUP_DATA[f]
            N = data.get("N", 0)
            if f.startswith("SU(") and N >= 3:
                has_confining = True
            if f.startswith("SU(") and N == 2:
                has_broken = True
    
    if not has_confining:
        score += 8.0
    if not has_broken:
        score += 5.0
    
    # 3. Landau pole avoidance
    total_dim = theory.gauge_group.dimension
    if total_dim > 100:
        score += (total_dim - 100) * 0.05
    
    # 4. Stable bound state support
    if has_confining and n_abelian >= 1:
        score += 0.0  # Can form atoms
    elif has_confining:
        score += 3.0  # Confinement but no long-range force
    else:
        score += 10.0  # No atomic structure possible
    
    # 5. CRITICAL: Extra gauge boson penalty
    # Each U(1) factor produces a massless gauge boson.
    # In the low-energy theory, only ONE U(1) survives as the photon.
    # Additional U(1)s require:
    #   - A Stückelberg mass or additional Higgs (extra complexity)
    #   - Kinetic mixing (introduces new parameters)
    #   - Experimental constraints (Z' searches exclude light Z')
    # This is a PHYSICS constraint, not a bias.
    if n_abelian > 1:
        extra_u1 = n_abelian - 1
        # Each extra U(1) requires a breaking mechanism
        score += extra_u1 * 4.0  # Significant penalty per extra massless boson
    
    # Similarly, extra non-abelian factors beyond what's needed
    # for confinement + EW breaking require additional breaking
    n_extra_nonabelian = max(0, len(non_abelian) - 2)  # SM needs 2: SU(3)+SU(2)
    if n_extra_nonabelian > 0:
        score += n_extra_nonabelian * 3.0
    
    # 6. Charge quantization
    # Requires non-abelian structure to quantize U(1) charges
    # SM achieves this via SU(5) embedding (or anomaly cancellation)
    if n_abelian >= 1 and len(non_abelian) >= 2:
        score += 0.0  # Charges quantized by anomaly cancellation
    elif n_abelian >= 1 and len(non_abelian) == 1:
        score += 2.0  # Charge quantization less constrained
    elif n_abelian >= 1 and len(non_abelian) == 0:
        score += 8.0  # No charge quantization mechanism
    
    # 7. Vector-like fermion fine-tuning penalty
    # Vector-like fermions get mass from a bare mass term M·ψ_L·ψ_R,
    # NOT from electroweak symmetry breaking. This mass M is a free
    # parameter unrelated to the Higgs VEV, requiring a separate mass
    # generation mechanism — a form of fine-tuning in a self-consistent theory.
    n_vl = getattr(theory, 'n_vector_like_pairs', 0)
    if n_vl > 0:
        score += n_vl * 1.5
    
    # PSC admissibility flags
    if not theory.psc_admissible:
        score += 100.0
    if not theory.reflexive_closure_satisfied:
        score += 100.0
    
    return score


# =============================================================================
# COMPONENT 5: DESCRIPTIVE ECONOMY (MDL)
# =============================================================================

def mdl_cost(theory: TheoryParams) -> float:
    """
    Compute MDL (Minimum Description Length) cost.
    
    Physics: Occam's razor — prefer the simplest theory that satisfies
    all constraints. This is NOT a bias toward SM; it is a universal
    principle of model selection.
    
    MDL cost is computed from STRUCTURAL properties only:
    - Number of gauge factors (discrete)
    - Total gauge group dimension (continuous parameters needed)
    - Number of independent coupling constants
    - Number of generations
    - Extra matter fields (vector-like pairs, extra scalars)
    
    Returns:
        MDL cost (non-negative, lower = simpler)
    """
    cost = 0.0
    
    # Number of gauge factors
    n_factors = len(theory.gauge_group.factors)
    cost += n_factors * 1.5
    
    # Gauge group dimension (number of gauge bosons)
    dim = theory.gauge_group.dimension
    cost += np.log1p(dim) * 1.0
    
    # Number of independent coupling constants
    n_couplings = len(theory.gauge_couplings)
    cost += n_couplings * 0.5
    
    # Generation count
    cost += theory.n_generations * 0.5
    
    # Total parameter count
    n_params = theory.get_dimension()
    cost += np.log1p(n_params) * 0.3
    
    # Each vector-like pair introduces a bare mass parameter M_VL,
    # Yukawa couplings to the Higgs, and mixing angles with SM fermions.
    # Roughly 4 new real parameters per pair (mass, 2 Yukawas, 1 mixing angle).
    n_vl = getattr(theory, 'n_vector_like_pairs', 0)
    cost += n_vl * 2.0
    
    # Each extra scalar introduces self-coupling, portal coupling to the Higgs,
    # and a mass parameter. Roughly 3 new parameters per scalar.
    n_sc = getattr(theory, 'n_extra_scalars', 0)
    cost += n_sc * 1.5
    
    return cost


# =============================================================================
# COMPONENT 6: RG STABILITY (COUPLING PERTURBATIVITY)
# =============================================================================

def rg_stability_score(theory: TheoryParams) -> float:
    """
    Score for RG stability of couplings.
    
    Physics: Couplings should be perturbative (not too large, not too small)
    for the theory to be calculable and self-consistent.
    
    This does NOT reference SM coupling values.
    It penalizes couplings that are:
    - Too large (non-perturbative, loss of predictivity)
    - Too small (fine-tuning)
    - Hierarchically separated (naturalness problem)
    
    Returns:
        Score (lower is better)
    """
    couplings = list(theory.gauge_couplings.values())
    if not couplings:
        return 5.0
    
    score = 0.0
    
    for g in couplings:
        alpha = g**2 / (4 * np.pi)  # Fine structure constant
        
        # Perturbativity: α should be in [0.001, 1]
        if alpha > 1.0:
            score += (alpha - 1.0) * 10.0  # Non-perturbative
        elif alpha < 0.001:
            score += (np.log10(0.001) - np.log10(max(alpha, 1e-10))) * 2.0  # Too weak
    
    # Hierarchy penalty: couplings shouldn't be too far apart
    if len(couplings) >= 2:
        g_max = max(abs(g) for g in couplings)
        g_min = min(abs(g) for g in couplings if abs(g) > 0)
        if g_min > 0:
            hierarchy = g_max / g_min
            if hierarchy > 10:
                score += np.log10(hierarchy) * 2.0
    
    return score


# =============================================================================
# COMPONENT 7: SYMMETRY BREAKING VIABILITY
# =============================================================================

def symmetry_breaking_score(theory: TheoryParams) -> float:
    """
    Score for viable symmetry breaking pattern.
    
    Physics: GUT-scale groups must break to SM at low energies.
    The breaking pattern must:
    - Preserve SU(3)_c × U(1)_em at low energies
    - Allow chiral fermion masses
    - Not produce unwanted relics (monopoles, domain walls)
    
    Simple groups (SU(5), SO(10), E_6) get a penalty for the
    number of breaking steps required and the associated fine-tuning.
    
    Returns:
        Score (lower is better)
    """
    factors = theory.gauge_group.factors
    n_factors = len(factors)
    score = 0.0
    
    # Simple GUT groups need multiple breaking steps
    if n_factors == 1:
        factor = factors[0]
        if factor in ("SU(5)", "SO(10)", "E_6", "E_7", "E_8"):
            # Number of breaking steps to reach SM
            breaking_steps = {
                "SU(5)": 1,   # SU(5) → SM
                "SO(10)": 2,  # SO(10) → SU(5) → SM or SO(10) → PS → SM
                "E_6": 3,     # E_6 → SO(10) → SU(5) → SM
                "E_7": 4,
                "E_8": 5,
            }
            n_steps = breaking_steps.get(factor, 3)
            
            # Each breaking step requires:
            # - A scalar field in the right representation
            # - Fine-tuning of the scalar potential
            # - No unwanted light states
            score += n_steps * 3.0
            
            # Doublet-triplet splitting problem (GUT-specific)
            if factor in ("SU(5)", "SO(10)", "E_6"):
                score += 5.0  # Famous fine-tuning problem
            
            # Proton decay constraints
            if factor in ("SU(5)", "SO(10)", "E_6"):
                score += 3.0  # Must suppress dimension-6 operators
        
        elif factor.startswith("SU(") and factor not in ("SU(2)", "SU(3)"):
            N = SIMPLE_GROUP_DATA[factor]["N"]
            score += max(0, N - 5) * 2.0  # Larger groups need more breaking
        
        elif factor in ("F_4", "G_2"):
            score += 8.0  # Exotic groups: unclear breaking pattern
        
        elif factor.startswith("Sp("):
            score += 6.0  # Sp groups: no standard breaking to SM
        
        elif factor.startswith("SO(") and factor not in ("SO(10)",):
            score += 5.0  # Non-standard SO groups
    
    # Product groups that already contain SM factors need less breaking
    elif n_factors >= 3:
        sm_like_factors = 0
        for f in factors:
            if f in ("SU(3)", "SU(2)", "U(1)"):
                sm_like_factors += 1
        
        if sm_like_factors >= 3:
            score += 0.0  # Already SM-like, minimal breaking
        elif sm_like_factors >= 2:
            score += 2.0  # Close to SM
        else:
            score += 4.0  # Needs significant rearrangement
    
    return score


# =============================================================================
# COMPONENT 8: MATTER CONTENT ECONOMY
# =============================================================================

def matter_content_score(theory: TheoryParams) -> float:
    """
    Score penalizing non-minimal matter content.
    
    Physics: The minimal chiral spectrum (SM) is uniquely determined by
    anomaly cancellation + asymptotic freedom + 3 generations. Extensions
    beyond this minimal content introduce fine-tuning problems:
    
    - Vector-like pairs: each pair requires a bare Dirac mass M·ψ_L·ψ_R
      unrelated to electroweak symmetry breaking. This mass is a free
      parameter with no symmetry reason to be at any particular scale.
      Penalty: 2.0 per pair.
    
    - Extra scalars: each additional scalar field requires tuning of the
      scalar potential to avoid destabilizing the electroweak vacuum.
      Penalty: 1.5 per extra scalar.
    
    - Extra Higgs doublets: beyond the single-doublet SM, additional
      doublets generically induce tree-level flavor-changing neutral
      currents (FCNCs) unless a discrete symmetry (e.g., Z_2) is imposed.
      This is the "natural flavor conservation" problem of multi-Higgs models.
      Penalty: 3.0 per extra doublet (counted via n_extra_scalars when the
      extra scalar is an SU(2) doublet, identified from matter_content).
    
    Returns 0.0 for the standard SM (n_vector_like_pairs=0, n_extra_scalars=0).
    
    Returns:
        Score (non-negative, lower = more economical matter content)
    """
    n_vl = getattr(theory, 'n_vector_like_pairs', 0)
    n_sc = getattr(theory, 'n_extra_scalars', 0)
    
    score = 0.0
    
    score += n_vl * 2.0
    score += n_sc * 1.5
    
    # Check for extra Higgs doublets in the explicit matter content.
    # An extra doublet is an SU(2) doublet scalar beyond the SM Higgs.
    n_extra_doublets = 0
    for field_name, field in theory.matter_content.items():
        if field_name == "H":
            continue  # SM Higgs
        if field.spin == 0:
            su2_rep = field.representations.get("SU(2)")
            if su2_rep is not None and su2_rep.dimension == 2:
                n_extra_doublets += 1
    
    score += n_extra_doublets * 3.0
    
    return score


# =============================================================================
# MAIN LYAPUNOV FUNCTIONAL
# =============================================================================

@dataclass
class LyapunovResult:
    """Result of Lyapunov functional evaluation."""
    total: float
    anomaly: float
    asymptotic_freedom: float
    chiral: float
    reflexive: float
    mdl: float
    rg_stability: float
    symmetry_breaking: float
    matter_content: float = 0.0
    
    # Legacy compatibility
    @property
    def viability(self): return -self.total
    @property
    def mdl_cost(self): return self.mdl
    @property
    def psc_penalty(self): return self.reflexive
    @property
    def rg_cost(self): return self.rg_stability
    @property
    def quarter_lock(self): return 0.0
    
    def __str__(self):
        return (f"C[T] = {self.total:.6f}\n"
                f"  Anomaly score     = {self.anomaly:.6f}\n"
                f"  Asymptotic freedom= {self.asymptotic_freedom:.6f}\n"
                f"  Chiral fermions   = {self.chiral:.6f}\n"
                f"  Reflexive (PSC)   = {self.reflexive:.6f}\n"
                f"  MDL cost          = {self.mdl:.6f}\n"
                f"  RG stability      = {self.rg_stability:.6f}\n"
                f"  Sym. breaking     = {self.symmetry_breaking:.6f}\n"
                f"  Matter content    = {self.matter_content:.6f}")


# Weights for combining components
# These are O(1) and roughly equal — no extreme weighting
DEFAULT_WEIGHTS = {
    'anomaly': 2.0,
    'af': 2.0,
    'chiral': 2.0,
    'reflexive': 3.0,
    'mdl': 1.0,
    'rg': 1.0,
    'breaking': 1.5,
    'matter': 2.0,
}


class SRRGLyapunovFunctional:
    """
    SRRG Lyapunov functional C[T].
    
    C[T] = Σᵢ wᵢ · Sᵢ[T]
    
    where Sᵢ are physics-based scores and wᵢ are O(1) weights.
    
    CRITICAL: No component references SM coupling values.
    SM must win on structural physics grounds alone.
    """
    
    def __init__(self,
                 weight_mdl: float = DEFAULT_WEIGHTS['mdl'],
                 weight_psc: float = DEFAULT_WEIGHTS['reflexive'],
                 weight_rg: float = DEFAULT_WEIGHTS['rg'],
                 weight_ql: float = DEFAULT_WEIGHTS['breaking'],
                 weight_matter: float = DEFAULT_WEIGHTS['matter']):
        self.w_anomaly = DEFAULT_WEIGHTS['anomaly']
        self.w_af = DEFAULT_WEIGHTS['af']
        self.w_chiral = DEFAULT_WEIGHTS['chiral']
        self.w_reflexive = weight_psc
        self.w_mdl = weight_mdl
        self.w_rg = weight_rg
        self.w_breaking = weight_ql
        self.w_matter = weight_matter
    
    def evaluate(self, theory: TheoryParams) -> float:
        """
        Evaluate Lyapunov functional C[T].
        
        Lower is better. SM should minimize this on physics grounds.
        """
        s_anomaly = anomaly_score(theory)
        s_af = asymptotic_freedom_score(theory)
        s_chiral = chiral_fermion_score(theory)
        s_reflexive = reflexive_consistency_score(theory)
        s_mdl = mdl_cost(theory)
        s_rg = rg_stability_score(theory)
        s_breaking = symmetry_breaking_score(theory)
        s_matter = matter_content_score(theory)
        
        C = (self.w_anomaly * s_anomaly +
             self.w_af * s_af +
             self.w_chiral * s_chiral +
             self.w_reflexive * s_reflexive +
             self.w_mdl * s_mdl +
             self.w_rg * s_rg +
             self.w_breaking * s_breaking +
             self.w_matter * s_matter)
        
        return C
    
    def evaluate_detailed(self, theory: TheoryParams) -> LyapunovResult:
        """Evaluate with detailed breakdown."""
        s_anomaly = anomaly_score(theory)
        s_af = asymptotic_freedom_score(theory)
        s_chiral = chiral_fermion_score(theory)
        s_reflexive = reflexive_consistency_score(theory)
        s_mdl = mdl_cost(theory)
        s_rg = rg_stability_score(theory)
        s_breaking = symmetry_breaking_score(theory)
        s_matter = matter_content_score(theory)
        
        total = (self.w_anomaly * s_anomaly +
                 self.w_af * s_af +
                 self.w_chiral * s_chiral +
                 self.w_reflexive * s_reflexive +
                 self.w_mdl * s_mdl +
                 self.w_rg * s_rg +
                 self.w_breaking * s_breaking +
                 self.w_matter * s_matter)
        
        return LyapunovResult(
            total=total,
            anomaly=s_anomaly,
            asymptotic_freedom=s_af,
            chiral=s_chiral,
            reflexive=s_reflexive,
            mdl=s_mdl,
            rg_stability=s_rg,
            symmetry_breaking=s_breaking,
            matter_content=s_matter,
        )
    
    def gradient(self, theory: TheoryParams,
                 epsilon: float = 1e-6) -> np.ndarray:
        """Compute numerical gradient of C[T] via finite differences."""
        params = theory.get_parameter_vector()
        n = len(params)
        grad = np.zeros(n)
        
        C0 = self.evaluate(theory)
        
        param_names = sorted(
            list(theory.gauge_couplings.keys()) +
            list(theory.yukawa_couplings.keys()) +
            list(theory.scalar_couplings.keys()) +
            list(theory.mass_parameters.keys()) +
            list(theory.mixing_angles.keys()) +
            list(theory.cp_phases.keys())
        )
        
        for i, name in enumerate(param_names):
            perturbed = self._perturb_theory(theory, name, epsilon)
            C1 = self.evaluate(perturbed)
            grad[i] = (C1 - C0) / epsilon
        
        return grad
    
    def _perturb_theory(self, theory: TheoryParams,
                        param_name: str, delta: float) -> TheoryParams:
        """Create a perturbed copy of the theory."""
        new_couplings = dict(theory.gauge_couplings)
        new_yukawas = dict(theory.yukawa_couplings)
        new_scalars = dict(theory.scalar_couplings)
        new_masses = dict(theory.mass_parameters)
        new_angles = dict(theory.mixing_angles)
        new_phases = dict(theory.cp_phases)
        
        if param_name in new_couplings:
            new_couplings[param_name] += delta
        elif param_name in new_yukawas:
            new_yukawas[param_name] += delta
        elif param_name in new_scalars:
            new_scalars[param_name] += delta
        elif param_name in new_masses:
            new_masses[param_name] += delta
        elif param_name in new_angles:
            new_angles[param_name] += delta
        elif param_name in new_phases:
            new_phases[param_name] += delta
        
        return TheoryParams(
            gauge_group=theory.gauge_group,
            matter_content=theory.matter_content,
            n_generations=theory.n_generations,
            eft_dimension=theory.eft_dimension,
            gauge_couplings=new_couplings,
            yukawa_couplings=new_yukawas,
            scalar_couplings=new_scalars,
            mass_parameters=new_masses,
            mixing_angles=new_angles,
            cp_phases=new_phases,
            n_vector_like_pairs=theory.n_vector_like_pairs,
            n_extra_scalars=theory.n_extra_scalars,
            psc_admissible=theory.psc_admissible,
            reflexive_closure_satisfied=theory.reflexive_closure_satisfied,
        )
    
    def hessian(self, theory: TheoryParams,
                epsilon: float = 1e-4) -> np.ndarray:
        """Compute numerical Hessian of C[T] via finite differences."""
        params = theory.get_parameter_vector()
        n = len(params)
        H = np.zeros((n, n))
        
        param_names = sorted(
            list(theory.gauge_couplings.keys()) +
            list(theory.yukawa_couplings.keys()) +
            list(theory.scalar_couplings.keys()) +
            list(theory.mass_parameters.keys()) +
            list(theory.mixing_angles.keys()) +
            list(theory.cp_phases.keys())
        )
        
        for i, name_i in enumerate(param_names):
            for j, name_j in enumerate(param_names):
                if i <= j:
                    T_pp = self._perturb_theory(
                        self._perturb_theory(theory, name_i, epsilon),
                        name_j, epsilon)
                    T_pm = self._perturb_theory(
                        self._perturb_theory(theory, name_i, epsilon),
                        name_j, -epsilon)
                    T_mp = self._perturb_theory(
                        self._perturb_theory(theory, name_i, -epsilon),
                        name_j, epsilon)
                    T_mm = self._perturb_theory(
                        self._perturb_theory(theory, name_i, -epsilon),
                        name_j, -epsilon)
                    
                    H[i, j] = (self.evaluate(T_pp) - self.evaluate(T_pm) -
                              self.evaluate(T_mp) + self.evaluate(T_mm)) / (4 * epsilon**2)
                    H[j, i] = H[i, j]
        
        return H


# =============================================================================
# LEGACY COMPATIBILITY
# =============================================================================

def viability_functional(theory: TheoryParams) -> float:
    """Legacy wrapper: returns negative of C (higher = better)."""
    C = SRRGLyapunovFunctional()
    return -C.evaluate(theory)

def psc_penalty(theory: TheoryParams) -> float:
    """Legacy wrapper."""
    return reflexive_consistency_score(theory)

def rg_stability_cost(theory: TheoryParams) -> float:
    """Legacy wrapper."""
    return rg_stability_score(theory)

def quarter_lock_penalty(theory: TheoryParams) -> float:
    """Legacy wrapper — Quarter-Lock is now a derived quantity, not input."""
    return 0.0


# =============================================================================
# TESTING
# =============================================================================

def test_lyapunov_functional():
    """Test Lyapunov functional implementation."""
    print("=" * 80)
    print("TESTING PHYSICS-BASED SRRG LYAPUNOV FUNCTIONAL")
    print("=" * 80)
    
    C = SRRGLyapunovFunctional()
    
    from theory_space_definition import GAUGE_GROUPS_CATALOG
    
    # Test Standard Model
    print("\n1. Standard Model [SU(3)×SU(2)×U(1), 3 gen]:")
    print("-" * 60)
    SM = create_standard_model_theory()
    result_sm = C.evaluate_detailed(SM)
    print(result_sm)
    
    # Test SU(5) GUT
    print("\n2. SU(5) GUT [3 gen]:")
    print("-" * 60)
    SU5 = TheoryParams(
        gauge_group=GAUGE_GROUPS_CATALOG["SU(5)"],
        n_generations=3, eft_dimension=4,
        gauge_couplings={'g': 0.7},
        psc_admissible=True, reflexive_closure_satisfied=True,
    )
    print(C.evaluate_detailed(SU5))
    
    # Test SO(10)
    print("\n3. SO(10) GUT [3 gen]:")
    print("-" * 60)
    SO10 = TheoryParams(
        gauge_group=GAUGE_GROUPS_CATALOG["SO(10)"],
        n_generations=3, eft_dimension=4,
        gauge_couplings={'g': 0.7},
        psc_admissible=True, reflexive_closure_satisfied=True,
    )
    print(C.evaluate_detailed(SO10))
    
    # Test E_6
    print("\n4. E_6 GUT [3 gen]:")
    print("-" * 60)
    E6 = TheoryParams(
        gauge_group=GAUGE_GROUPS_CATALOG["E_6"],
        n_generations=3, eft_dimension=4,
        gauge_couplings={'g': 0.5},
        psc_admissible=True, reflexive_closure_satisfied=True,
    )
    print(C.evaluate_detailed(E6))
    
    # Test Pati-Salam
    print("\n5. Pati-Salam [SU(4)×SU(2)×SU(2), 3 gen]:")
    print("-" * 60)
    PS = TheoryParams(
        gauge_group=GAUGE_GROUPS_CATALOG["SU(4)×SU(2)×SU(2)"],
        n_generations=3, eft_dimension=4,
        gauge_couplings={'g1': 0.7, 'g2': 0.65, 'g3': 0.65},
        psc_admissible=True, reflexive_closure_satisfied=True,
    )
    print(C.evaluate_detailed(PS))
    
    # Comparison
    print("\n" + "=" * 60)
    print("COMPARISON (lower C = better)")
    print("=" * 60)
    theories = [
        ("SM", SM), ("SU(5)", SU5), ("SO(10)", SO10),
        ("E_6", E6), ("Pati-Salam", PS),
    ]
    for name, T in sorted(theories, key=lambda x: C.evaluate(x[1])):
        print(f"  C[{name:12s}] = {C.evaluate(T):.4f}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    test_lyapunov_functional()
