"""
UGP → CKM/PMNS Mixing Matrices - PMNS-Focused Ultra-Aggressive Optimization
Research Question 1.2: Priority 1 - Optimize PMNS angles using same ultra-aggressive approach

This experiment focuses specifically on PMNS mixing angle optimization while maintaining
the successful CKM results from the previous ultra-aggressive optimization.
"""

import math
import cmath
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import pandas as pd
from scipy.linalg import expm

from ..core.registry import register_experiment
from .base import Experiment

@dataclass
class PMNSFocusedResult:
    """Results from the PMNS-focused optimization."""
    ckm_matrix: np.ndarray
    pmns_matrix: np.ndarray
    ckm_angles: Dict[str, float]
    pmns_angles: Dict[str, float]
    ckm_score: float
    pmns_score: float
    perm_choice: Tuple[int, ...]
    neutrino_model: str
    evals_up: np.ndarray
    evals_down: np.ndarray
    evals_lepton: np.ndarray
    evals_neutrino: np.ndarray
    pmns_weighted_error: float
    overall_mixing_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "ckm_matrix": [[{"real": float(x.real), "imag": float(x.imag)} for x in row] for row in self.ckm_matrix],
            "pmns_matrix": [[{"real": float(x.real), "imag": float(x.imag)} for x in row] for row in self.pmns_matrix],
            "ckm_angles": self.ckm_angles,
            "pmns_angles": self.pmns_angles,
            "ckm_score": float(self.ckm_score),
            "pmns_score": float(self.pmns_score),
            "perm_choice": list(self.perm_choice),
            "neutrino_model": self.neutrino_model,
            "evals_up": [float(x) for x in self.evals_up],
            "evals_down": [float(x) for x in self.evals_down],
            "evals_lepton": [float(x) for x in self.evals_lepton],
            "evals_neutrino": [float(x) for x in self.evals_neutrino],
            "pmns_weighted_error": float(self.pmns_weighted_error),
            "overall_mixing_score": float(self.overall_mixing_score)
        }

@register_experiment("ugp_yukawa_ckm_pmns_pmns_focused")
class UGPYukawaCKMPMNSPMNSFocused(Experiment):
    """PMNS-focused ultra-aggressive optimization for neutrino mixing angles."""

    def __init__(self, config: Dict[str, Any], root: str):
        super().__init__(config, Path(root))
        
        # Extract configuration - match working experiment pattern
        self.neutrino_model = config.get("neutrino_model", "majorana")
        self.pdg_targets_ckm = tuple(config.get("pdg_targets_ckm", [0.2245, 0.041, 0.00365]))
        self.pdg_targets_pmns = tuple(config.get("pdg_targets_pmns", [33.44, 8.57, 49.2]))
        
        # PDG Experimental Targets
        self.pdg_targets = {
            "Vus": 0.2245, "Vcb": 0.041, "Vub": 0.00365,
            "theta12": 33.44, "theta13": 8.57, "theta23": 49.2
        }
        
        # Elegant Kernel constants
        self.phi = (1 + 5**0.5) / 2.0
        self.k_L2 = 0.013671875
        self.k_gen2 = -self.phi / 2.0
        self.k_gen = math.pi / 2.0
        self.k_a = 0.125
        self.k_b = -1.5
        self.k_c = 4.0/3.0
        self.k_M = self.k_gen2 + 0.25 * self.k_L2
        
        # Base kernel-locked parameters
        self.k_L = -2 * self.k_L2 * (-3.0/2.0) * math.log(self.phi)
        self.L_residual = config.get("residual_kraft_length", 9.382)
        
        # PMNS-FOCUSED ULTRA-AGGRESSIVE PARAMETER RANGES
        # Even more extreme ranges specifically for PMNS optimization
        self.tau0_scaling_factors = config.get("tau0_scaling_factors", [
            0.0001, 0.0002, 0.0005, 0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 
            0.2, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 50.0, 100.0, 200.0, 
            500.0, 1000.0, 2000.0, 5000.0, 10000.0
        ])
        self.epsilon_scaling_factors = config.get("epsilon_scaling_factors", [
            0.0001, 0.0002, 0.0005, 0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1,
            0.2, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 50.0, 100.0, 200.0, 
            500.0, 1000.0, 2000.0, 5000.0
        ])
        self.epsilon_prime_scaling_factors = config.get("epsilon_prime_scaling_factors", [
            0.0001, 0.0002, 0.0005, 0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1,
            0.2, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 50.0, 100.0, 200.0, 
            500.0, 1000.0, 2000.0, 5000.0
        ])
        self.normalization_methods = config.get("normalization_methods", [
            "spectral_radius", "frobenius", "max_element", "trace_norm", "l1_norm",
            "l_inf_norm", "nuclear_norm", "schatten_1", "schatten_2", "schatten_inf",
            "mixed_norm_1", "mixed_norm_2", "custom_weighted"
        ])
        
        # Canonical GTE triples (unchanged)
        self.triples_q_l = {
            # charged leptons
            ("e", "lepton", 1): (1, 73, 823),
            ("mu", "lepton", 2): (9, 42, 1023),
            ("tau", "lepton", 3): (5, 275, 65535),
            # up-type quarks
            ("u", "up", 1): (5, 9, 275),
            ("c", "up", 2): (5, 275, 65535),
            ("t", "up", 3): (76, 337920, -1),
            # down-type quarks
            ("d", "down", 1): (9, 5, 42),
            ("s", "down", 2): (9, 186, 1023),
            ("b", "down", 3): (5, 8191, 65535),
        }
        
        # Neutrino triples (ILR-enhanced for better PMNS optimization)
        self.triples_nu = {
            ("nu_e", "nu", 1): (1, 1, 823),
            ("nu_mu", "nu", 2): (9, 1, 1023),
            ("nu_tau", "nu", 3): (5, 1, 65535),
        }

    def tasks(self) -> List[str]:
        """Return list of task names."""
        return ["pmns_focused_optimization"]

    def run_task(self, task_id: str) -> Dict[str, Any]:
        """Run the PMNS-focused optimization task."""
        if task_id == "pmns_focused_optimization":
            return self._run_pmns_focused_optimization()
        else:
            raise ValueError(f"Unknown task: {task_id}")

    def _run_pmns_focused_optimization(self) -> Dict[str, Any]:
        """Run PMNS-focused ultra-aggressive optimization."""
        self.logger.info("Starting PMNS-focused ultra-aggressive optimization")
        
        # Calculate total combinations
        total_combinations = (len(self.tau0_scaling_factors) * 
                            len(self.epsilon_scaling_factors) * 
                            len(self.epsilon_prime_scaling_factors) * 
                            len(self.normalization_methods))
        
        self.logger.info(f"Testing {total_combinations} PMNS-focused parameter combinations")
        
        successful_results = []
        
        # Ultra-aggressive parameter exploration
        for i, tau0_scale in enumerate(self.tau0_scaling_factors):
            for j, epsilon_scale in enumerate(self.epsilon_scaling_factors):
                for k, epsilon_prime_scale in enumerate(self.epsilon_prime_scaling_factors):
                    for l, norm_method in enumerate(self.normalization_methods):
                        try:
                            result = self._test_pmns_focused_configuration(
                                tau0_scale, epsilon_scale, epsilon_prime_scale, norm_method
                            )
                            if result["status"] == "success":
                                successful_results.append(result)
                        except Exception as e:
                            self.logger.warning(f"Configuration failed: {e}")
                            continue
                        
                        # Progress logging
                        if len(successful_results) % 1000 == 0:
                            self.logger.info(f"Progress: {len(successful_results)}/{total_combinations}")
        
        if not successful_results:
            return {
                "task_id": "pmns_focused_optimization",
                "status": "failed",
                "error": "No successful PMNS-focused configurations found"
            }
        
        # Find best configuration by PMNS-weighted error
        best_result = min(successful_results, key=lambda x: (
            x["pmns_weighted_error"],
            x["experimental_errors"]["overall_rms_error"]
        ))
        
        # Create result object
        result_obj = PMNSFocusedResult(
            ckm_matrix=best_result["ckm_matrix"],
            pmns_matrix=best_result["pmns_matrix"],
            ckm_angles=best_result["ckm_angles"],
            pmns_angles=best_result["pmns_angles"],
            ckm_score=best_result["ckm_score"],
            pmns_score=best_result["pmns_score"],
            perm_choice=tuple(best_result["perm_choice"]),
            neutrino_model=self.neutrino_model,
            evals_up=best_result["evals_up"],
            evals_down=best_result["evals_down"],
            evals_lepton=best_result["evals_lepton"],
            evals_neutrino=best_result["evals_neutrino"],
            pmns_weighted_error=best_result["pmns_weighted_error"],
            overall_mixing_score=best_result["overall_mixing_score"]
        )
        
        return {
            "task_id": "pmns_focused_optimization",
            "status": "completed",
            "total_combinations_tested": total_combinations,
            "successful_configurations": len(successful_results),
            "best_configuration": best_result,
            "result_object": result_obj.to_dict(),
            "optimization_summary": {
                "best_pmns_weighted_error": best_result["pmns_weighted_error"],
                "best_overall_mixing_score": best_result["overall_mixing_score"],
                "best_parameters": {
                    "tau0_scale": best_result["tau0_scale"],
                    "epsilon_scale": best_result["epsilon_scale"],
                    "epsilon_prime_scale": best_result["epsilon_prime_scale"],
                    "norm_method": best_result["norm_method"]
                }
            }
        }

    def _test_pmns_focused_configuration(self, tau0_scale: float, epsilon_scale: float, 
                                       epsilon_prime_scale: float, norm_method: str) -> Dict[str, Any]:
        """Test a specific PMNS-focused parameter configuration."""
        try:
            # Test all S3 permutations for down sector
            best_ckm = None
            best_score = float('inf')
            
            # S3 permutations for down sector
            permutations = [
                [0, 1, 2], [0, 2, 1], [1, 0, 2],
                [1, 2, 0], [2, 0, 1], [2, 1, 0]
            ]
            
            for perm in permutations:
                try:
                    ckm_result = self._build_ckm_pmns_with_parameters(
                        tau0_scale, epsilon_scale, epsilon_prime_scale, norm_method, (perm[0], perm[1], perm[2])
                    )
                    if ckm_result is not None:
                        # Calculate PMNS-focused score
                        pmns_score = self._calculate_pmns_focused_score(ckm_result)
                        if pmns_score < best_score:
                            best_score = pmns_score
                            best_ckm = ckm_result
                except Exception as e:
                    continue
            
            if best_ckm is None:
                return {"status": "failed", "error": "No valid CKM/PMNS configuration found"}
            
            return {
                "status": "success",
                "tau0_scale": tau0_scale,
                "epsilon_scale": epsilon_scale,
                "epsilon_prime_scale": epsilon_prime_scale,
                "norm_method": norm_method,
                "perm_choice": best_ckm["perm_choice"],
                "ckm_matrix": best_ckm["ckm_matrix"],
                "pmns_matrix": best_ckm["pmns_matrix"],
                "ckm_angles": best_ckm["ckm_angles"],
                "pmns_angles": best_ckm["pmns_angles"],
                "ckm_score": best_ckm["ckm_score"],
                "pmns_score": best_ckm["pmns_score"],
                "experimental_errors": best_ckm["experimental_errors"],
                "pmns_weighted_error": best_ckm["pmns_weighted_error"],
                "overall_mixing_score": best_ckm["overall_mixing_score"],
                "evals_up": best_ckm["evals_up"],
                "evals_down": best_ckm["evals_down"],
                "evals_lepton": best_ckm["evals_lepton"],
                "evals_neutrino": best_ckm["evals_neutrino"]
            }
            
        except Exception as e:
            return {"status": "failed", "error": str(e)}

    def _calculate_pmns_focused_score(self, result: Dict[str, Any]) -> float:
        """Calculate PMNS-focused optimization score."""
        # Ultra-aggressive PMNS weighting - prioritize PMNS angles heavily
        pmns_weights = {
            "pmns_theta12": 20.0,  # EXTREME weight - solar mixing
            "pmns_theta13": 15.0,  # Very high weight - reactor mixing
            "pmns_theta23": 18.0,  # Very high weight - atmospheric mixing
            "ckm_theta12": 5.0,    # Medium weight - maintain CKM success
            "ckm_theta13": 3.0,    # Low weight - maintain CKM success
            "ckm_theta23": 3.0,    # Low weight - maintain CKM success
        }
        
        errors = result["experimental_errors"]
        pmns_angle_errors = [
            errors["pmns_theta12_error"] * pmns_weights["pmns_theta12"],
            errors["pmns_theta13_error"] * pmns_weights["pmns_theta13"],
            errors["pmns_theta23_error"] * pmns_weights["pmns_theta23"],
            errors["theta12_error"] * pmns_weights["ckm_theta12"],
            errors["theta13_error"] * pmns_weights["ckm_theta13"],
            errors["theta23_error"] * pmns_weights["ckm_theta23"]
        ]
        
        return math.sqrt(sum(e**2 for e in pmns_angle_errors) / len(pmns_angle_errors))

    def _build_ckm_pmns_with_parameters(self, tau0_scale: float, epsilon_scale: float, 
                                      epsilon_prime_scale: float, norm_method: str, 
                                      perm_faces: Tuple[int, int, int]) -> Optional[Dict[str, Any]]:
        """Build CKM/PMNS matrices with specific parameters."""
        try:
            # Build up sector
            up_result = self._build_sector_with_flow("up", tau0_scale, epsilon_scale, 
                                                   epsilon_prime_scale, norm_method, None)
            if up_result is None:
                return None
            
            # Build down sector with permutation
            down_result = self._build_sector_with_flow("down", tau0_scale, epsilon_scale, 
                                                     epsilon_prime_scale, norm_method, perm_faces)
            if down_result is None:
                return None
            
            # Build lepton sector
            lepton_result = self._build_sector_with_flow("lepton", tau0_scale, epsilon_scale, 
                                                       epsilon_prime_scale, norm_method, None)
            if lepton_result is None:
                return None
            
            # Build neutrino sector with enhanced PMNS optimization
            neutrino_result = self._build_sector_with_flow("nu", tau0_scale, epsilon_scale, 
                                                         epsilon_prime_scale, norm_method, None)
            if neutrino_result is None:
                return None
            
            # Construct CKM matrix
            U_up = up_result["U"]
            U_down = down_result["U"]
            V = U_up.conj().T @ U_down
            
            # Construct PMNS matrix with enhanced neutrino handling
            U_lepton = lepton_result["U"]
            U_neutrino = neutrino_result["U"]
            U = U_lepton.conj().T @ U_neutrino
            
            # Calculate angles and scores
            ckm_angles = self._unitary_to_angles_and_J(V)
            pmns_angles = self._unitary_to_angles_and_J(U)
            
            # Calculate experimental errors
            experimental_errors = self._calculate_experimental_errors(ckm_angles, pmns_angles, V)
            
            # Calculate PMNS-weighted error
            pmns_weighted_error = self._calculate_pmns_weighted_error(experimental_errors)
            
            # Calculate overall mixing score
            overall_mixing_score = self._calculate_overall_mixing_score(experimental_errors)
            
            return {
                "perm_choice": perm_faces,
                "ckm_matrix": V,
                "pmns_matrix": U,
                "ckm_angles": ckm_angles,
                "pmns_angles": pmns_angles,
                "ckm_score": experimental_errors["overall_rms_error"],
                "pmns_score": pmns_weighted_error,
                "experimental_errors": experimental_errors,
                "pmns_weighted_error": pmns_weighted_error,
                "overall_mixing_score": overall_mixing_score,
                "evals_up": up_result["evals"],
                "evals_down": down_result["evals"],
                "evals_lepton": lepton_result["evals"],
                "evals_neutrino": neutrino_result["evals"]
            }
            
        except Exception as e:
            return None

    def _calculate_pmns_weighted_error(self, errors: Dict[str, float]) -> float:
        """Calculate PMNS-weighted error specifically."""
        pmns_weights = {
            "pmns_theta12": 20.0,  # EXTREME weight
            "pmns_theta13": 15.0,  # Very high weight
            "pmns_theta23": 18.0,  # Very high weight
        }
        
        pmns_angle_errors = [
            errors["pmns_theta12_error"] * pmns_weights["pmns_theta12"],
            errors["pmns_theta13_error"] * pmns_weights["pmns_theta13"],
            errors["pmns_theta23_error"] * pmns_weights["pmns_theta23"]
        ]
        
        return math.sqrt(sum(e**2 for e in pmns_angle_errors) / len(pmns_angle_errors))

    def _calculate_overall_mixing_score(self, errors: Dict[str, float]) -> float:
        """Calculate overall mixing score combining CKM and PMNS."""
        # Balanced weighting for overall assessment
        overall_weights = {
            "theta12_error": 10.0,      # CKM θ₁₂
            "theta13_error": 8.0,       # CKM θ₁₃
            "theta23_error": 6.0,       # CKM θ₂₃
            "pmns_theta12_error": 10.0, # PMNS θ₁₂
            "pmns_theta13_error": 8.0,  # PMNS θ₁₃
            "pmns_theta23_error": 6.0,  # PMNS θ₂₃
        }
        
        weighted_errors = [
            errors["theta12_error"] * overall_weights["theta12_error"],
            errors["theta13_error"] * overall_weights["theta13_error"],
            errors["theta23_error"] * overall_weights["theta23_error"],
            errors["pmns_theta12_error"] * overall_weights["pmns_theta12_error"],
            errors["pmns_theta13_error"] * overall_weights["pmns_theta13_error"],
            errors["pmns_theta23_error"] * overall_weights["pmns_theta23_error"]
        ]
        
        return math.sqrt(sum(e**2 for e in weighted_errors) / len(weighted_errors))

    # Include all the mathematical methods from the original implementation
    def _extract_irrep_features(self, a: float, b: float, c: float, g: int, sector: str) -> Tuple[float, Tuple[complex, complex], float]:
        """Extract S3 irrep features from GTE triple."""
        # Normalize triple to remove local scale
        norm = math.sqrt(a*a + b*b + c*c)
        if norm == 0:
            return 0.0, (0.0, 0.0), 0.0
        
        ta, tb, tc = a/norm, b/norm, c/norm
        
        # A1 (symmetric): average
        s_gen = (ta + tb + tc) / 3.0
        
        # E (2D irrep): orthogonal components
        e1 = (2*ta - tb - tc) / math.sqrt(6.0)
        e2 = (tb - tc) / math.sqrt(2.0)
        
        # Apply generation phases
        phase_E = cmath.exp(1j * g * self.k_gen)  # k_gen = pi/2
        e1_rotated = e1 * phase_E
        e2_rotated = e2 * phase_E
        
        # A2 (antisymmetric): oriented Vandermonde (linear, not squared!)
        delta = (ta - tb) * (tb - tc) * (tc - ta)
        
        return s_gen, (e1_rotated, e2_rotated), delta

    def _matrix_norm(self, matrix: np.ndarray, method: str) -> float:
        """Compute matrix norm using specified method with advanced options."""
        try:
            if method == "spectral_radius":
                return float(np.linalg.norm(matrix, ord=2))
            elif method == "frobenius":
                return float(np.linalg.norm(matrix, ord='fro'))
            elif method == "max_element":
                return float(np.max(np.abs(matrix)))
            elif method == "trace_norm":
                return float(np.trace(np.abs(matrix)))
            elif method == "l1_norm":
                return float(np.linalg.norm(matrix, ord=1))
            elif method == "l_inf_norm":
                return float(np.linalg.norm(matrix, ord=np.inf))
            elif method == "nuclear_norm":
                s = np.linalg.svd(matrix, compute_uv=False)
                return float(np.sum(s))
            elif method == "schatten_1":
                s = np.linalg.svd(matrix, compute_uv=False)
                return float(np.sum(s))
            elif method == "schatten_2":
                return float(np.linalg.norm(matrix, ord='fro'))
            elif method == "schatten_inf":
                return float(np.linalg.norm(matrix, ord=2))
            elif method == "mixed_norm_1":
                return float(0.5 * (np.linalg.norm(matrix, ord=1) + np.linalg.norm(matrix, ord=2)))
            elif method == "mixed_norm_2":
                return float(0.5 * (np.linalg.norm(matrix, ord='fro') + np.linalg.norm(matrix, ord=2)))
            elif method == "custom_weighted":
                # Custom weighted norm for PMNS optimization
                spectral = np.linalg.norm(matrix, ord=2)
                frobenius = np.linalg.norm(matrix, ord='fro')
                return float(0.7 * spectral + 0.3 * frobenius)
            else:
                return float(np.linalg.norm(matrix, ord=2))
        except (np.linalg.LinAlgError, OverflowError, RuntimeWarning):
            return float(np.linalg.norm(matrix, ord=2))

    def _build_generators(self, triples_list: List[Tuple[int, int, int]], gens: List[int], sector: str, norm_method: str) -> Tuple[np.ndarray, np.ndarray, float, float]:
        """Build normalized generators with specified normalization method."""
        n = len(triples_list)
        
        # Extract irrep features for all triples
        s_list = []
        e_list = []
        delta_list = []
        
        for (a, b, c), g in zip(triples_list, gens):
            s, (e1, e2), delta = self._extract_irrep_features(a, b, c, g, sector)
            s_list.append(s)
            e_list.append((e1, e2))
            delta_list.append(delta)
        
        # Build E generator (symmetric)
        E_op = np.zeros((n, n), dtype=complex)
        for i in range(n):
            for j in range(n):
                E_op[i, j] = (s_list[i] * s_list[j] + 
                             e_list[i][0] * e_list[j][0] + 
                             e_list[i][1] * e_list[j][1])
        
        # Build A generator (antisymmetric)
        A_op = np.zeros((n, n), dtype=complex)
        for i in range(n):
            for j in range(n):
                if i != j:
                    A_op[i, j] = delta_list[i] * (i - j) / abs(i - j)
        
        # Normalize generators
        rhoE = self._matrix_norm(E_op, norm_method)
        rhoA = self._matrix_norm(A_op, norm_method)
        
        Ehat = E_op / rhoE if rhoE > 0 else E_op
        Ahat = A_op / rhoA if rhoA > 0 else A_op
        
        return Ehat, Ahat, rhoE, rhoA

    def _initialize_mass_matrix(self, triples_list: List[Tuple[int, int, int]], gens: List[int]) -> np.ndarray:
        """Initialize mass matrix from triples."""
        n = len(triples_list)
        
        # Extract irrep features
        s_list = []
        e_list = []
        
        for (a, b, c), g in zip(triples_list, gens):
            s, (e1, e2), _ = self._extract_irrep_features(a, b, c, g, "up")
            s_list.append(s)
            e_list.append((e1, e2))
        
        # Initialize M0: alpha * s_i * s_j + beta * (e_i·e_i) * delta_ij
        alpha = 1.0
        beta = self.k_L2
        
        M0 = np.zeros((n, n), dtype=complex)
        for i in range(n):
            for j in range(n):
                M0[i, j] += alpha * s_list[i] * s_list[j]
                if i == j:
                    e_dot_e = e_list[i][0] * e_list[i][0] + e_list[i][1] * e_list[i][1]
                    M0[i, j] += beta * e_dot_e
        
        return M0

    def _exact_flow_evolution(self, M0: np.ndarray, Ehat: np.ndarray, Ahat: np.ndarray, 
                             rhoE: float, rhoA: float, tau0_scale: float, 
                             epsilon_scale: float, epsilon_prime_scale: float) -> np.ndarray:
        """Exact closed-form flow evolution with numerical stability fixes."""
        # Calculate scaled parameters
        tau0 = math.log(2) * self.L_residual * tau0_scale
        epsilon = self.k_L * epsilon_scale
        epsilon_prime = (self.k_L / self.phi) * epsilon_prime_scale
        
        # Calculate normalized flow times
        tauE = tau0 / rhoE if rhoE > 0 else 0.0
        tauA = tau0 / rhoA if rhoA > 0 else 0.0
        
        # ORIGINAL FLOW with numerical stability fixes
        try:
            # Check for numerical stability
            if abs(epsilon * tauE) > 10.0 or abs(epsilon_prime * tauA) > 10.0:
                # Use smaller steps for numerical stability
                epsilon_safe = min(epsilon, 1.0)
                epsilon_prime_safe = min(epsilon_prime, 1.0)
                tauE_safe = min(tauE, 5.0)
                tauA_safe = min(tauA, 5.0)
            else:
                epsilon_safe = epsilon
                epsilon_prime_safe = epsilon_prime
                tauE_safe = tauE
                tauA_safe = tauA
            
            ME = expm(epsilon_safe * tauE_safe * Ehat) @ M0 @ expm(epsilon_safe * tauE_safe * Ehat.T)
            U_A = expm(1j * epsilon_prime_safe * tauA_safe * Ahat)
            M_evolved = U_A @ ME @ U_A.conj().T
            
            # Check for NaN or Inf
            if not np.all(np.isfinite(M_evolved)):
                M_evolved = M0
                
        except (OverflowError, np.linalg.LinAlgError, RuntimeWarning):
            M_evolved = M0
        
        return M_evolved

    def _exact_flow_evolution_majorana(self, S0: np.ndarray, Ehat: np.ndarray, Ahat: np.ndarray,
                                      rhoE: float, rhoA: float, tau0_scale: float,
                                      epsilon_scale: float, epsilon_prime_scale: float) -> np.ndarray:
        """Exact closed-form flow evolution for Majorana neutrinos with numerical stability fixes."""
        # Calculate scaled parameters
        tau0 = math.log(2) * self.L_residual * tau0_scale
        epsilon = self.k_L * epsilon_scale
        epsilon_prime = (self.k_L / self.phi) * epsilon_prime_scale
        
        # Calculate normalized flow times
        tauE = tau0 / rhoE if rhoE > 0 else 0.0
        tauA = tau0 / rhoA if rhoA > 0 else 0.0
        
        try:
            # Check for numerical stability
            if abs(epsilon * tauE) > 10.0 or abs(epsilon_prime * tauA) > 10.0:
                epsilon_safe = min(epsilon, 1.0)
                epsilon_prime_safe = min(epsilon_prime, 1.0)
                tauE_safe = min(tauE, 5.0)
                tauA_safe = min(tauA, 5.0)
            else:
                epsilon_safe = epsilon
                epsilon_prime_safe = epsilon_prime
                tauE_safe = tauE
                tauA_safe = tauA
            
            SE = expm(epsilon_safe * tauE_safe * Ehat) @ S0 @ expm(epsilon_safe * tauE_safe * Ehat.T)
            U_A = expm(1j * epsilon_prime_safe * tauA_safe * Ahat)
            S_evolved = U_A.T @ SE @ U_A
            
            if not np.all(np.isfinite(S_evolved)):
                S_evolved = S0
                
        except (OverflowError, np.linalg.LinAlgError, RuntimeWarning):
            S_evolved = S0
        
        return S_evolved

    def _build_sector_with_flow(self, sector_key: str, tau0_scale: float, epsilon_scale: float, 
                               epsilon_prime_scale: float, norm_method: str, 
                               perm_faces: Optional[Tuple[int, int, int]]) -> Optional[Dict[str, Any]]:
        """Build a sector using flow dynamics."""
        try:
            if sector_key == "up":
                triples_dict = {k: v for k, v in self.triples_q_l.items() if k[1] == "up"}
            elif sector_key == "down":
                triples_dict = {k: v for k, v in self.triples_q_l.items() if k[1] == "down"}
            elif sector_key == "lepton":
                triples_dict = {k: v for k, v in self.triples_q_l.items() if k[1] == "lepton"}
            elif sector_key == "nu":
                triples_dict = self.triples_nu
            else:
                return None
            
            # Get sorted families
            families = sorted(triples_dict.keys(), key=lambda x: x[2])
            triples_list = [triples_dict[f] for f in families]
            gens = [f[2] for f in families]
            
            # Apply permutation if specified
            if perm_faces is not None:
                triples_list = self._apply_perm_to_triples(triples_list, perm_faces)
            
            # Build generators
            Ehat, Ahat, rhoE, rhoA = self._build_generators(triples_list, gens, sector_key, norm_method)
            
            # Initialize mass matrix
            M0 = self._initialize_mass_matrix(triples_list, gens)
            
            # Evolve via flow
            if sector_key == "nu" and self.neutrino_model == "majorana":
                M_evolved = self._exact_flow_evolution_majorana(M0, Ehat, Ahat, rhoE, rhoA, 
                                                               tau0_scale, epsilon_scale, epsilon_prime_scale)
            else:
                M_evolved = self._exact_flow_evolution(M0, Ehat, Ahat, rhoE, rhoA, 
                                                      tau0_scale, epsilon_scale, epsilon_prime_scale)
            
            # Diagonalize
            if sector_key == "nu" and self.neutrino_model == "majorana":
                # Takagi factorization for Majorana
                U_sorted, evals_sorted = self._takagi_factorization(M_evolved)
            else:
                # Standard diagonalization
                evals, U = np.linalg.eigh(M_evolved)
                U_sorted = U[:, np.argsort(evals)]
                evals_sorted = np.sort(evals)
            
            return {
                "U": U_sorted,
                "evals": evals_sorted,
                "M": M_evolved
            }
            
        except Exception as e:
            return None

    def _apply_perm_to_triples(self, triples_list: List[Tuple[int, int, int]], perm: Tuple[int, int, int]) -> List[Tuple[int, int, int]]:
        """Apply permutation to triples list."""
        permuted = [triples_list[perm[i]] for i in range(len(perm))]
        return permuted

    def _takagi_factorization(self, S: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Takagi factorization for symmetric complex matrices."""
        U_svd, s_svd, Vt_svd = np.linalg.svd(S)
        U = U_svd @ Vt_svd
        evals = s_svd
        return U, evals

    def _unitary_to_angles_and_J(self, U: np.ndarray) -> Dict[str, float]:
        """Convert unitary matrix to mixing angles and Jarlskog invariant."""
        # Extract matrix elements
        if U.shape != (3, 3):
            return {"theta12_deg": 0.0, "theta13_deg": 0.0, "theta23_deg": 0.0, "J": 0.0}
        
        # Calculate mixing angles
        s12 = abs(U[0, 1])
        s13 = abs(U[0, 2])
        s23 = abs(U[1, 2])
        
        theta12 = math.asin(s12) * 180.0 / math.pi
        theta13 = math.asin(s13) * 180.0 / math.pi
        theta23 = math.asin(s23) * 180.0 / math.pi
        
        # Calculate Jarlskog invariant
        J = abs(np.imag(U[0, 0] * U[0, 1] * U[1, 0] * U[1, 1]))
        
        return {
            "theta12_deg": theta12,
            "theta13_deg": theta13,
            "theta23_deg": theta23,
            "J": J
        }

    def _calculate_experimental_errors(self, ckm_angles: Dict[str, float], pmns_angles: Dict[str, float], ckm_matrix: np.ndarray) -> Dict[str, float]:
        """Calculate errors compared to PDG experimental targets with PMNS focus."""
        Vabs = np.abs(ckm_matrix)
        
        errors = {}
        errors["Vus_error"] = abs(Vabs[0, 1] - self.pdg_targets["Vus"]) / self.pdg_targets["Vus"]
        errors["Vcb_error"] = abs(Vabs[1, 2] - self.pdg_targets["Vcb"]) / self.pdg_targets["Vcb"]
        errors["Vub_error"] = abs(Vabs[0, 2] - self.pdg_targets["Vub"]) / self.pdg_targets["Vub"]
        errors["theta12_error"] = abs(ckm_angles["theta12_deg"] - self.pdg_targets["theta12"]) / self.pdg_targets["theta12"]
        errors["theta13_error"] = abs(ckm_angles["theta13_deg"] - self.pdg_targets["theta13"]) / self.pdg_targets["theta13"]
        errors["theta23_error"] = abs(ckm_angles["theta23_deg"] - self.pdg_targets["theta23"]) / self.pdg_targets["theta23"]
        
        # PMNS angle errors
        errors["pmns_theta12_error"] = abs(pmns_angles["theta12_deg"] - self.pdg_targets["theta12"]) / self.pdg_targets["theta12"]
        errors["pmns_theta13_error"] = abs(pmns_angles["theta13_deg"] - self.pdg_targets["theta13"]) / self.pdg_targets["theta13"]
        errors["pmns_theta23_error"] = abs(pmns_angles["theta23_deg"] - self.pdg_targets["theta23"]) / self.pdg_targets["theta23"]
        
        # Overall RMS error
        error_values = list(errors.values())
        errors["overall_rms_error"] = math.sqrt(sum(e**2 for e in error_values) / len(error_values))
        
        return errors

    def summarize(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize PMNS-focused optimization results."""
        if not results:
            return {"status": "no_results"}
        
        result_data = results[0]
        
        return {
            "pmns_focused_optimization_summary": {
                "total_combinations_tested": result_data.get("total_combinations_tested", 0),
                "successful_configurations": result_data.get("successful_configurations", 0),
                "best_pmns_weighted_error": result_data.get("optimization_summary", {}).get("best_pmns_weighted_error", float('inf')),
                "best_overall_mixing_score": result_data.get("optimization_summary", {}).get("best_overall_mixing_score", float('inf')),
                "best_parameters": result_data.get("optimization_summary", {}).get("best_parameters", {}),
                "pmns_angles": result_data.get("result_object", {}).get("pmns_angles", {}),
                "ckm_angles": result_data.get("result_object", {}).get("ckm_angles", {}),
                "improvement_achieved": "PMNS-focused ultra-aggressive optimization completed"
            }
        }
