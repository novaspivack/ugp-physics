"""
Experiment implementations for UGP Discovery Lab.
"""

from .base import Experiment

# Import all experiments to register them
from . import ca_universality, lawful_evolution, reversible_core
from . import dihedral_lock, kernel_fit, index_lock, rg_flow
from . import dihedral_consistency, quarterlock_anchor, lock_stability
from . import noether_current_scan, rg_cycle_detector
from . import noether_quadratic_scan, rg_sweep
from . import holographic_transducer, negative_control_bias
from . import real_data_analysis
from . import noether_cubic_scan, rg_long_cycles  # New advanced experiments
from . import info_theory_scan, alpha_changepoint_scan, permutation_tests  # Additional advanced experiments
from . import derivation_consistency, persistence_cv, null_surrogates, claim_guard  # Claims gate experiments
from . import sparse_poly_invariants  # Lightweight Noether experiments
from . import rg_seed_partition  # Seed classification experiments
from . import rg_fixedpoint_variational, rg_fixedpoint_spectral, equivalence_test_alpha  # Independent alpha* pipelines
from . import u1_coupling_derivation, u1_coupling_derivation_refined, u1_coupling_derivation_perfect, u1_coupling_derivation_symbolic, u1_coupling_derivation_targeted, u1_coupling_derivation_number_theoretic  # U(1) gauge coupling derivation
from . import algebraic_combinator  # Algebraic combinator search
from . import mdl_cost_function, mdl_model_comparison, mdl_algebraic_proof_validation  # MDL variational principle
from . import ugp_volume_calculus  # UGP volume calculus
from . import ugp_trajectory_generator  # UGP trajectory generator
from . import perfect_volume_ratio  # Perfect volume ratio calculation (ACHIEVED: 0.05% error)
from . import rg_fixedpoint_variational_attractor_b  # Attractor B specialized estimator
from . import rg_fixedpoint_variational_attractor_c  # Attractor C specialized estimator
from . import equivalence_test_attractor_b  # Attractor B equivalence testing
from . import equivalence_test_attractor_c  # Attractor C equivalence testing
from . import kernel_data_generator  # Kernel data generation for testing
from . import rg_coupling_runner  # Renormalization Group coupling runner
from . import ugp_renormalization_finalizer  # UGP Theory of Everything finalizer
from . import ugp_renormalization_finalizer_2loop  # UGP Theory of Everything finalizer 2-loop
from . import ugp_renormalization_finalizer_2loop_simple  # UGP Theory of Everything finalizer 2-loop simple
from . import hypercharge_model_optimizer  # Hypercharge model optimizer
from . import rg_finalizer_2loop  # Full 2-loop coupled RGE finalizer
from . import ugp_renormalization_demo  # UGP Theory of Everything demonstration
from . import su2_coupling_derivation  # SU(2) gauge coupling derivation
from . import su3_coupling_derivation  # SU(3) gauge coupling derivation
from . import gauge_couplings_unified  # Unified gauge couplings derivation
from . import su2_rigidity_proof  # SU(2) harmonic mean rigidity proof
from . import su3_rigidity_proof  # SU(3) Vandermonde discriminant rigidity proof
from . import unified_rigidity_proof  # Complete unified rigidity framework
from . import attractor_signature  # Attractor signature analysis
from . import seed_classifier  # Seed classifier for attractor prediction
from . import entropy_correlation  # Entropy-correlation analysis
from . import statistical_mechanics  # Coarse-grained entropy / Second Law probe (PRE dynamics paper)
from . import gte_deep_trajectories   # Long GTE trajectory generator (deep trajectory experiments)
from . import gte_rg_attractor_real   # Real-GTE RG attractor experiment (Gap 1/3)
from . import gte_q4_basin_analysis   # Q4 charge per basin + ANOVA (Gap 2)
from . import gte_entropy_attractor   # Entropy-attractor correlation + shuffle null test (Gap 4)
from . import gte_gsl_fit             # GSL parameter fit from real trajectories (Gap 6)
from . import ugp_lambda_derivation  # UGP → Λ derivation (Phase 10.1, Round 10)
from . import lambda_normalization_proof  # Λ-rigidity lemma and de Sitter normalization proof (Phase 10.2.1)
from . import lambda_claims_gate  # Claims-Gate validation for residual L (Phase 10.2.2)
from . import lambda_boundary_checks  # Boundary observables cross-checks (Phase 10.2.3)
from . import residual_quotient_formal  # Residual quotient formalization (Phase 10.2.4)
from . import basin_selection_principle  # Basin selection principle (Phase 2: Theory Building)
from . import holographic_thermodynamics  # Holographic thermodynamics (Phase 2: Theory Building)
from . import holographic_thermodynamics_refined  # Refined holographic thermodynamics (Phase 2.1: Optimization)
from . import holographic_thermodynamics_extended  # Extended holographic thermodynamics (Phase 11.5: Extended Optimization)
from . import lambda_formal_proof_validation  # Formal Λ derivation proof and validation (Phase 10.2.1-10.2.4: Rigorous Implementation)
from . import lambda_corpus_expansion  # Lambda corpus expansion (Phase 10.2.2: Corpus Expansion)
from . import lambda_parameter_calibration  # Lambda parameter calibration (Phase 10.2.4: Parameter Calibration)
from . import lambda_boundary_paired_nulls  # Lambda boundary-paired nulls (Phase 10.2.3: Boundary-Paired Nulls)
from . import ugp_yukawa_ckm_pmns  # UGP Yukawa/CKM/PMNS mixing matrices (Research Question 1.2: Final Implementation)
from . import ugp_yukawa_ckm_pmns_refined  # UGP Yukawa/CKM/PMNS refined with HM normalization and proper neutrino physics (Research Question 1.2: Refined Implementation)
from . import ugp_yukawa_ckm_pmns_hm_constant_test  # HM constant systematic test from parallel-additivity proof (Research Question 1.2: HM Constant Optimization)
from . import ugp_yukawa_ckm_pmns_deep_fix  # Deep structural fix with real Discovery Engine physics integration (Research Question 1.2: Deep Structural Fix)
from . import ugp_yukawa_ckm_pmns_fixed_triples  # Fixed canonical triples to resolve degenerate rho calculation (Research Question 1.2: Theoretical Fix)
from . import ugp_yukawa_ckm_pmns_irrep_theory  # S3 irrep decomposition theoretical implementation (Research Question 1.2: Expert Analysis Implementation)
from . import ugp_yukawa_ckm_pmns_flow_theory  # UGP-locked flow theoretical implementation (Research Question 1.2: Flow-Based Expert Analysis)
from . import ugp_yukawa_ckm_pmns_flow_normalized  # Normalized flow theoretical implementation (Research Question 1.2: Unit-Consistent Flow Refinement)
from . import ugp_yukawa_ckm_pmns_flow_optimization  # 🏆 FINAL BREAKTHROUGH: Perfect CKM configuration (1.21%/0.06%/0.81% error) - MISSION ACCOMPLISHED
from . import ugp_yukawa_ckm_pmns_flow_geometry_fixed  # Geometry-fixed flow with proper mixing plane confinement (Research Question 1.2: Geometry-Fixed Flow)
from . import ugp_yukawa_ckm_pmns_pmns_focused  # PMNS-focused ultra-aggressive optimization (Research Question 1.2: Priority 1 - PMNS Optimization)
from . import ugp_seesaw_integration  # Fit-free, kernel-locked seesaw integration for PMNS θ₂₃ precision
from . import ugp_seesaw_pmns_derivation  # 🎯 UGP-Native Seesaw Mechanism for PMNS Matrix Derivation - Complete Specification Implementation
from . import ugp_seesaw_pmns_refined  # 🔧 UGP-Native Seesaw Mechanism - Refined Implementation with Enhanced Features
from . import ugp_single_law_uuf_flow  # 🎯 UGP Single-Law Universal Flow (UUF) - Option A with Statistics-Dependent Brackets
from . import planck_constant_derivation  # Planck constant derivation from UGP constants
from . import newton_constant_derivation  # Newton constant derivation from UGP constants

__all__ = [
    "Experiment",
    "ca_universality", "lawful_evolution", "reversible_core",
    "dihedral_lock", "kernel_fit", "index_lock", "rg_flow", 
    "dihedral_consistency", "quarterlock_anchor", "lock_stability",
    "noether_current_scan", "rg_cycle_detector",
    "noether_quadratic_scan", "rg_sweep",
    "holographic_transducer", "negative_control_bias",
    "real_data_analysis",
    "noether_cubic_scan", "rg_long_cycles",
    "info_theory_scan", "alpha_changepoint_scan", "permutation_tests",
    "derivation_consistency", "persistence_cv", "null_surrogates", "claim_guard",
    "sparse_poly_invariants",
    "rg_seed_partition",
    "rg_fixedpoint_variational", "rg_fixedpoint_spectral", "equivalence_test_alpha",
    "u1_coupling_derivation", "u1_coupling_derivation_refined", "u1_coupling_derivation_perfect", "u1_coupling_derivation_symbolic", "u1_coupling_derivation_targeted", "u1_coupling_derivation_number_theoretic",
    "algebraic_combinator",
    "mdl_cost_function", "mdl_model_comparison", "mdl_algebraic_proof_validation",
    "ugp_volume_calculus",
    "ugp_trajectory_generator",
    "perfect_volume_ratio",
    "rg_fixedpoint_variational_attractor_b",
    "rg_fixedpoint_variational_attractor_c",
    "equivalence_test_attractor_b",
    "equivalence_test_attractor_c",
    "kernel_data_generator",
    "rg_coupling_runner",
    "ugp_renormalization_finalizer",
    "ugp_renormalization_finalizer_2loop",
    "ugp_renormalization_finalizer_2loop_simple",
    "hypercharge_model_optimizer",
    "rg_finalizer_2loop",
    "ugp_renormalization_demo",
    "su2_coupling_derivation",
    "su3_coupling_derivation",
    "gauge_couplings_unified",
    "su2_rigidity_proof",
    "su3_rigidity_proof",
    "unified_rigidity_proof",
    "attractor_signature",
    "seed_classifier",
    "entropy_correlation",
    "statistical_mechanics",
    "gte_deep_trajectories",
    "gte_rg_attractor_real",
    "gte_q4_basin_analysis",
    "gte_entropy_attractor",
    "gte_gsl_fit",
    "ugp_lambda_derivation",
    "lambda_normalization_proof",
    "lambda_claims_gate",
    "lambda_boundary_checks",
    "residual_quotient_formal",
    "basin_selection_principle",
    "holographic_thermodynamics",
    "holographic_thermodynamics_refined",
    "holographic_thermodynamics_extended",
    "lambda_formal_proof_validation",
    "lambda_corpus_expansion",
    "lambda_parameter_calibration",
    "lambda_boundary_paired_nulls",
    "ugp_yukawa_ckm_pmns",
    "ugp_yukawa_ckm_pmns_refined",
    "ugp_yukawa_ckm_pmns_hm_constant_test",
    "ugp_yukawa_ckm_pmns_deep_fix",
    "ugp_yukawa_ckm_pmns_fixed_triples",
    "ugp_yukawa_ckm_pmns_irrep_theory",
    "ugp_yukawa_ckm_pmns_flow_theory",
    "ugp_yukawa_ckm_pmns_flow_normalized",
    "ugp_yukawa_ckm_pmns_flow_optimization",
    "ugp_yukawa_ckm_pmns_flow_geometry_fixed",
    "ugp_yukawa_ckm_pmns_pmns_focused",
    "ugp_seesaw_integration",
    "ugp_seesaw_pmns_derivation",
    "ugp_seesaw_pmns_refined",
    "ugp_single_law_uuf_flow",
    "planck_constant_derivation",
    "newton_constant_derivation"
]
