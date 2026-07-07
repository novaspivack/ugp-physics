"""
UGP → Neutrino Mass Generation with Seesaw Mechanism Integration
Research Question 1.2: Priority 2 - Integrate neutrino mass generation more deeply with seesaw mechanism

This experiment implements a comprehensive seesaw mechanism within the UGP framework,
integrating neutrino mass generation with the existing flow dynamics and canonical GTE triples.
"""

import math
import cmath
import numpy as np
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from scipy.linalg import expm, sqrtm

from ..core.registry import register_experiment
from .base import Experiment

@dataclass
class NeutrinoMassResult:
    """Results from neutrino mass generation with seesaw mechanism."""
    light_neutrino_masses: np.ndarray
    heavy_neutrino_masses: np.ndarray
    light_mass_eigenstates: np.ndarray
    heavy_mass_eigenstates: np.ndarray
    pmns_matrix: np.ndarray
    seesaw_scale: float
    seesaw_efficiency: float
    mass_hierarchy_type: str
    pmns_angles: Dict[str, float]
    jarlskog_invariant: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "light_neutrino_masses": [float(x) for x in self.light_neutrino_masses],
            "heavy_neutrino_masses": [float(x) for x in self.heavy_neutrino_masses],
            "light_mass_eigenstates": [[{"real": float(x.real), "imag": float(x.imag)} for x in row] for row in self.light_mass_eigenstates],
            "heavy_mass_eigenstates": [[{"real": float(x.real), "imag": float(x.imag)} for x in row] for row in self.heavy_mass_eigenstates],
            "pmns_matrix": [[{"real": float(x.real), "imag": float(x.imag)} for x in row] for row in self.pmns_matrix],
            "seesaw_scale": float(self.seesaw_scale),
            "seesaw_efficiency": float(self.seesaw_efficiency),
            "mass_hierarchy_type": self.mass_hierarchy_type,
            "pmns_angles": self.pmns_angles,
            "jarlskog_invariant": float(self.jarlskog_invariant)
        }

@register_experiment("ugp_neutrino_mass_seesaw_integration")
class UGPNeutrinoMassSeesawIntegration(Experiment):
    """Neutrino mass generation with seesaw mechanism integration within UGP framework."""

    def __init__(self, config: Dict[str, Any], root: str):
        super().__init__(config, Path(root))
        
        # Extract configuration
        self.seesaw_scale_range = config.get("seesaw_scale_range", [1e12, 1e15, 1e16])  # GeV
        self.seesaw_types = config.get("seesaw_types", ["type1", "type2", "type3"])
        self.mass_hierarchy_preference = config.get("mass_hierarchy_preference", "normal")
        
        # PDG Experimental Targets for neutrino masses (eV)
        self.pdg_neutrino_mass_targets = {
            "m1_target": 0.0,  # Lightest neutrino mass
            "m2_target": 0.0086,  # Solar mass difference sqrt(Δm²₂₁)
            "m3_target": 0.050,   # Atmospheric mass difference sqrt(Δm²₃₁)
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
        
        # Canonical neutrino GTE triples (ILR-enhanced)
        self.triples_nu = {
            ("nu_e", "nu", 1): (1, 1, 823),
            ("nu_mu", "nu", 2): (9, 1, 1023),
            ("nu_tau", "nu", 3): (5, 1, 65535),
        }
        
        # Lepton triples for seesaw mechanism
        self.triples_lepton = {
            ("e", "lepton", 1): (1, 73, 823),
            ("mu", "lepton", 2): (9, 42, 1023),
            ("tau", "lepton", 3): (5, 275, 65535),
        }

    def tasks(self) -> List[str]:
        """Return list of task names."""
        return ["seesaw_mass_generation", "mass_hierarchy_analysis", "pmns_validation"]

    def run_task(self, task_id: str) -> Dict[str, Any]:
        """Run the specified task."""
        if task_id == "seesaw_mass_generation":
            return self._run_seesaw_mass_generation()
        elif task_id == "mass_hierarchy_analysis":
            return self._run_mass_hierarchy_analysis()
        elif task_id == "pmns_validation":
            return self._run_pmns_validation()
        else:
            raise ValueError(f"Unknown task: {task_id}")

    def _run_seesaw_mass_generation(self) -> Dict[str, Any]:
        """Run seesaw mechanism neutrino mass generation."""
        self.logger.info("Starting seesaw mechanism neutrino mass generation")
        
        best_result = None
        best_score = float('inf')
        
        # Test different seesaw scales and types
        for seesaw_scale in self.seesaw_scale_range:
            for seesaw_type in self.seesaw_types:
                try:
                    result = self._generate_seesaw_masses(seesaw_scale, seesaw_type)
                    if result is not None:
                        score = self._evaluate_seesaw_result(result)
                        if score < best_score:
                            best_score = score
                            best_result = result
                except Exception as e:
                    self.logger.warning(f"Seesaw generation failed for scale={seesaw_scale}, type={seesaw_type}: {e}")
                    continue
        
        if best_result is None:
            return {
                "task_id": "seesaw_mass_generation",
                "status": "failed",
                "error": "No successful seesaw mass generation found"
            }
        
        return {
            "task_id": "seesaw_mass_generation",
            "status": "completed",
            "best_result": best_result.to_dict(),
            "best_score": best_score,
            "seesaw_scale": best_result.seesaw_scale,
            "seesaw_type": best_result.mass_hierarchy_type
        }

    def _generate_seesaw_masses(self, seesaw_scale: float, seesaw_type: str) -> Optional[NeutrinoMassResult]:
        """Generate neutrino masses using seesaw mechanism."""
        try:
            # Build Dirac mass matrix from lepton triples
            M_D = self._build_dirac_mass_matrix()
            
            # Build Majorana mass matrix for heavy neutrinos
            M_R = self._build_majorana_mass_matrix(seesaw_scale)
            
            # Apply seesaw mechanism
            if seesaw_type == "type1":
                M_light = self._type1_seesaw(M_D, M_R)
            elif seesaw_type == "type2":
                M_light = self._type2_seesaw(M_D, M_R)
            elif seesaw_type == "type3":
                M_light = self._type3_seesaw(M_D, M_R)
            else:
                return None
            
            # Diagonalize light neutrino mass matrix
            light_masses, light_states = np.linalg.eigh(M_light)
            
            # Diagonalize heavy neutrino mass matrix
            heavy_masses, heavy_states = np.linalg.eigh(M_R)
            
            # Build PMNS matrix from light neutrino states
            pmns_matrix = self._build_pmns_matrix(light_states)
            
            # Calculate mixing angles
            pmns_angles = self._calculate_pmns_angles(pmns_matrix)
            
            # Calculate Jarlskog invariant
            jarlskog_invariant = self._calculate_jarlskog_invariant(pmns_matrix)
            
            # Determine mass hierarchy
            mass_hierarchy_type = self._determine_mass_hierarchy(light_masses)
            
            # Calculate seesaw efficiency
            seesaw_efficiency = self._calculate_seesaw_efficiency(M_D, M_R, M_light)
            
            return NeutrinoMassResult(
                light_neutrino_masses=light_masses,
                heavy_neutrino_masses=heavy_masses,
                light_mass_eigenstates=light_states,
                heavy_mass_eigenstates=heavy_states,
                pmns_matrix=pmns_matrix,
                seesaw_scale=seesaw_scale,
                seesaw_efficiency=seesaw_efficiency,
                mass_hierarchy_type=mass_hierarchy_type,
                pmns_angles=pmns_angles,
                jarlskog_invariant=jarlskog_invariant
            )
            
        except Exception as e:
            self.logger.warning(f"Seesaw mass generation failed: {e}")
            return None

    def _build_dirac_mass_matrix(self) -> np.ndarray:
        """Build Dirac mass matrix from lepton triples using UGP flow dynamics."""
        # Extract lepton triples
        families = sorted(self.triples_lepton.keys(), key=lambda x: x[2])
        triples_list = [self.triples_lepton[f] for f in families]
        gens = [f[2] for f in families]
        
        # Build generators using UGP flow dynamics
        Ehat, Ahat, rhoE, rhoA = self._build_generators(triples_list, gens, "lepton", "spectral_radius")
        
        # Initialize mass matrix
        M0 = self._initialize_mass_matrix(triples_list, gens)
        
        # Evolve via UGP flow
        tau0 = math.log(2) * self.L_residual * 2.0  # Use optimal tau0 from PMNS optimization
        epsilon = self.k_L * 0.2  # Use optimal epsilon from PMNS optimization
        epsilon_prime = (self.k_L / self.phi) * 2.0  # Use optimal epsilon_prime from PMNS optimization
        
        tauE = tau0 / rhoE if rhoE > 0 else 0.0
        tauA = tau0 / rhoA if rhoA > 0 else 0.0
        
        try:
            ME = expm(epsilon * tauE * Ehat) @ M0 @ expm(epsilon * tauE * Ehat.T)
            U_A = expm(1j * epsilon_prime * tauA * Ahat)
            M_D = U_A @ ME @ U_A.conj().T
            
            if not np.all(np.isfinite(M_D)):
                M_D = M0
                
        except (OverflowError, np.linalg.LinAlgError, RuntimeWarning):
            M_D = M0
        
        return M_D

    def _build_majorana_mass_matrix(self, seesaw_scale: float) -> np.ndarray:
        """Build Majorana mass matrix for heavy neutrinos."""
        # Extract neutrino triples
        families = sorted(self.triples_nu.keys(), key=lambda x: x[2])
        triples_list = [self.triples_nu[f] for f in families]
        gens = [f[2] for f in families]
        
        # Build generators using UGP flow dynamics
        Ehat, Ahat, rhoE, rhoA = self._build_generators(triples_list, gens, "nu", "spectral_radius")
        
        # Initialize mass matrix
        M0 = self._initialize_mass_matrix(triples_list, gens)
        
        # Scale by seesaw scale
        M_R_base = M0 * seesaw_scale
        
        # Apply UGP flow with stronger parameters for heavy neutrinos
        tau0 = math.log(2) * self.L_residual * 10.0  # Stronger flow for heavy neutrinos
        epsilon = self.k_L * 1.0
        epsilon_prime = (self.k_L / self.phi) * 5.0
        
        tauE = tau0 / rhoE if rhoE > 0 else 0.0
        tauA = tau0 / rhoA if rhoA > 0 else 0.0
        
        try:
            ME = expm(epsilon * tauE * Ehat) @ M_R_base @ expm(epsilon * tauE * Ehat.T)
            U_A = expm(1j * epsilon_prime * tauA * Ahat)
            M_R = U_A @ ME @ U_A.conj().T
            
            if not np.all(np.isfinite(M_R)):
                M_R = M_R_base
                
        except (OverflowError, np.linalg.LinAlgError, RuntimeWarning):
            M_R = M_R_base
        
        return M_R

    def _type1_seesaw(self, M_D: np.ndarray, M_R: np.ndarray) -> np.ndarray:
        """Type-I seesaw mechanism: M_light = -M_D^T M_R^{-1} M_D"""
        try:
            M_R_inv = np.linalg.inv(M_R)
            M_light = -M_D.T @ M_R_inv @ M_D
            return M_light
        except np.linalg.LinAlgError:
            return np.zeros_like(M_D)

    def _type2_seesaw(self, M_D: np.ndarray, M_R: np.ndarray) -> np.ndarray:
        """Type-II seesaw mechanism: M_light = M_L - M_D^T M_R^{-1} M_D"""
        # For simplicity, use M_L = M_D (left-handed Majorana mass)
        M_L = M_D
        try:
            M_R_inv = np.linalg.inv(M_R)
            M_light = M_L - M_D.T @ M_R_inv @ M_D
            return M_light
        except np.linalg.LinAlgError:
            return M_L

    def _type3_seesaw(self, M_D: np.ndarray, M_R: np.ndarray) -> np.ndarray:
        """Type-III seesaw mechanism: Similar to Type-I but with triplet scalars"""
        # For simplicity, use same formula as Type-I
        return self._type1_seesaw(M_D, M_R)

    def _build_pmns_matrix(self, light_states: np.ndarray) -> np.ndarray:
        """Build PMNS matrix from light neutrino eigenstates."""
        # The PMNS matrix is the unitary matrix that diagonalizes the light neutrino mass matrix
        # In the seesaw mechanism, this comes from the mixing between active and sterile neutrinos
        return light_states

    def _calculate_pmns_angles(self, pmns_matrix: np.ndarray) -> Dict[str, float]:
        """Calculate PMNS mixing angles from PMNS matrix."""
        if pmns_matrix.shape != (3, 3):
            return {"theta12_deg": 0.0, "theta13_deg": 0.0, "theta23_deg": 0.0}
        
        # Extract matrix elements
        s12 = abs(pmns_matrix[0, 1])
        s13 = abs(pmns_matrix[0, 2])
        s23 = abs(pmns_matrix[1, 2])
        
        theta12 = math.asin(s12) * 180.0 / math.pi
        theta13 = math.asin(s13) * 180.0 / math.pi
        theta23 = math.asin(s23) * 180.0 / math.pi
        
        return {
            "theta12_deg": theta12,
            "theta13_deg": theta13,
            "theta23_deg": theta23
        }

    def _calculate_jarlskog_invariant(self, pmns_matrix: np.ndarray) -> float:
        """Calculate Jarlskog invariant for CP violation."""
        if pmns_matrix.shape != (3, 3):
            return 0.0
        
        # Jarlskog invariant: J = Im(U_11 U_12* U_21* U_22)
        U = pmns_matrix
        J = abs(np.imag(U[0, 0] * U[0, 1].conj() * U[1, 0].conj() * U[1, 1]))
        return float(J)

    def _determine_mass_hierarchy(self, light_masses: np.ndarray) -> str:
        """Determine neutrino mass hierarchy (normal, inverted, or degenerate)."""
        # Sort masses
        sorted_masses = np.sort(light_masses)
        
        # Check for normal hierarchy: m1 < m2 < m3
        if sorted_masses[1] > sorted_masses[0] and sorted_masses[2] > sorted_masses[1]:
            return "normal"
        # Check for inverted hierarchy: m3 < m1 < m2
        elif sorted_masses[0] > sorted_masses[2] and sorted_masses[1] > sorted_masses[0]:
            return "inverted"
        else:
            return "degenerate"

    def _calculate_seesaw_efficiency(self, M_D: np.ndarray, M_R: np.ndarray, M_light: np.ndarray) -> float:
        """Calculate seesaw mechanism efficiency."""
        try:
            # Efficiency = |M_light| / (|M_D|^2 / |M_R|)
            M_D_norm = np.linalg.norm(M_D)
            M_R_norm = np.linalg.norm(M_R)
            M_light_norm = np.linalg.norm(M_light)
            
            expected_light_norm = (M_D_norm**2) / M_R_norm
            efficiency = M_light_norm / expected_light_norm if expected_light_norm > 0 else 0.0
            
            return float(efficiency)
        except:
            return 0.0

    def _evaluate_seesaw_result(self, result: NeutrinoMassResult) -> float:
        """Evaluate seesaw result quality."""
        # Calculate error from PDG targets
        errors = []
        
        # Check mass hierarchy
        if result.mass_hierarchy_type != self.mass_hierarchy_preference:
            errors.append(1.0)  # Penalty for wrong hierarchy
        
        # Check PMNS angles against targets
        pmns_targets = {"theta12_deg": 33.44, "theta13_deg": 8.57, "theta23_deg": 49.2}
        for angle_name, target in pmns_targets.items():
            if angle_name in result.pmns_angles:
                error = abs(result.pmns_angles[angle_name] - target) / target
                errors.append(error)
        
        # Check seesaw efficiency (should be close to 1)
        efficiency_error = abs(result.seesaw_efficiency - 1.0)
        errors.append(efficiency_error)
        
        # Return RMS error
        return math.sqrt(sum(e**2 for e in errors) / len(errors)) if errors else float('inf')

    def _run_mass_hierarchy_analysis(self) -> Dict[str, Any]:
        """Analyze neutrino mass hierarchy patterns."""
        self.logger.info("Starting neutrino mass hierarchy analysis")
        
        # Generate masses for different seesaw configurations
        hierarchy_results = []
        
        for seesaw_scale in self.seesaw_scale_range:
            for seesaw_type in self.seesaw_types:
                try:
                    result = self._generate_seesaw_masses(seesaw_scale, seesaw_type)
                    if result is not None:
                        hierarchy_results.append({
                            "seesaw_scale": seesaw_scale,
                            "seesaw_type": seesaw_type,
                            "mass_hierarchy": result.mass_hierarchy_type,
                            "light_masses": result.light_neutrino_masses.tolist(),
                            "heavy_masses": result.heavy_neutrino_masses.tolist(),
                            "pmns_angles": result.pmns_angles,
                            "seesaw_efficiency": result.seesaw_efficiency
                        })
                except Exception as e:
                    continue
        
        # Analyze hierarchy patterns
        normal_count = sum(1 for r in hierarchy_results if r["mass_hierarchy"] == "normal")
        inverted_count = sum(1 for r in hierarchy_results if r["mass_hierarchy"] == "inverted")
        degenerate_count = sum(1 for r in hierarchy_results if r["mass_hierarchy"] == "degenerate")
        
        return {
            "task_id": "mass_hierarchy_analysis",
            "status": "completed",
            "total_configurations": len(hierarchy_results),
            "hierarchy_distribution": {
                "normal": normal_count,
                "inverted": inverted_count,
                "degenerate": degenerate_count
            },
            "results": hierarchy_results
        }

    def _run_pmns_validation(self) -> Dict[str, Any]:
        """Validate PMNS matrix properties from seesaw mechanism."""
        self.logger.info("Starting PMNS validation from seesaw mechanism")
        
        # Generate best seesaw configuration
        best_result = None
        best_score = float('inf')
        
        for seesaw_scale in self.seesaw_scale_range:
            for seesaw_type in self.seesaw_types:
                try:
                    result = self._generate_seesaw_masses(seesaw_scale, seesaw_type)
                    if result is not None:
                        score = self._evaluate_seesaw_result(result)
                        if score < best_score:
                            best_score = score
                            best_result = result
                except Exception as e:
                    continue
        
        if best_result is None:
            return {
                "task_id": "pmns_validation",
                "status": "failed",
                "error": "No valid seesaw configuration found"
            }
        
        # Validate PMNS matrix properties
        pmns_matrix = best_result.pmns_matrix
        
        # Check unitarity
        unitary_check = np.allclose(pmns_matrix @ pmns_matrix.conj().T, np.eye(3), atol=1e-10)
        
        # Check determinant
        det_check = abs(np.linalg.det(pmns_matrix)) - 1.0 < 1e-10
        
        # Check Jarlskog invariant
        jarlskog_valid = 0.0 <= best_result.jarlskog_invariant <= 1.0
        
        return {
            "task_id": "pmns_validation",
            "status": "completed",
            "pmns_matrix_valid": unitary_check and det_check and jarlskog_valid,
            "unitarity_check": unitary_check,
            "determinant_check": det_check,
            "jarlskog_valid": jarlskog_valid,
            "pmns_angles": best_result.pmns_angles,
            "jarlskog_invariant": best_result.jarlskog_invariant,
            "mass_hierarchy": best_result.mass_hierarchy_type,
            "seesaw_efficiency": best_result.seesaw_efficiency
        }

    # Include the mathematical methods from the previous experiments
    def _extract_irrep_features(self, a: float, b: float, c: float, g: int, sector: str) -> Tuple[float, Tuple[complex, complex], float]:
        """Extract S3 irrep features from GTE triple."""
        norm = math.sqrt(a*a + b*b + c*c)
        if norm == 0:
            return 0.0, (0.0, 0.0), 0.0
        
        ta, tb, tc = a/norm, b/norm, c/norm
        
        s_gen = (ta + tb + tc) / 3.0
        e1 = (2*ta - tb - tc) / math.sqrt(6.0)
        e2 = (tb - tc) / math.sqrt(2.0)
        
        phase_E = cmath.exp(1j * g * self.k_gen)
        e1_rotated = e1 * phase_E
        e2_rotated = e2 * phase_E
        
        delta = (ta - tb) * (tb - tc) * (tc - ta)
        
        return s_gen, (e1_rotated, e2_rotated), delta

    def _build_generators(self, triples_list: List[Tuple[int, int, int]], gens: List[int], sector: str, norm_method: str) -> Tuple[np.ndarray, np.ndarray, float, float]:
        """Build normalized generators with specified normalization method."""
        n = len(triples_list)
        
        s_list = []
        e_list = []
        delta_list = []
        
        for (a, b, c), g in zip(triples_list, gens):
            s, (e1, e2), delta = self._extract_irrep_features(a, b, c, g, sector)
            s_list.append(s)
            e_list.append((e1, e2))
            delta_list.append(delta)
        
        E_op = np.zeros((n, n), dtype=complex)
        for i in range(n):
            for j in range(n):
                E_op[i, j] = (s_list[i] * s_list[j] + 
                             e_list[i][0] * e_list[j][0] + 
                             e_list[i][1] * e_list[j][1])
        
        A_op = np.zeros((n, n), dtype=complex)
        for i in range(n):
            for j in range(n):
                if i != j:
                    A_op[i, j] = delta_list[i] * (i - j) / abs(i - j)
        
        rhoE = np.linalg.norm(E_op, ord=2)
        rhoA = np.linalg.norm(A_op, ord=2)
        
        Ehat = E_op / rhoE if rhoE > 0 else E_op
        Ahat = A_op / rhoA if rhoA > 0 else A_op
        
        return Ehat, Ahat, rhoE, rhoA

    def _initialize_mass_matrix(self, triples_list: List[Tuple[int, int, int]], gens: List[int]) -> np.ndarray:
        """Initialize mass matrix from triples."""
        n = len(triples_list)
        
        s_list = []
        e_list = []
        
        for (a, b, c), g in zip(triples_list, gens):
            s, (e1, e2), _ = self._extract_irrep_features(a, b, c, g, "up")
            s_list.append(s)
            e_list.append((e1, e2))
        
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

    def summarize(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize neutrino mass seesaw integration results."""
        if not results:
            return {"status": "no_results"}
        
        summary = {
            "seesaw_integration_summary": {
                "total_tasks_completed": len(results),
                "successful_tasks": sum(1 for r in results if r.get("status") == "completed"),
                "tasks": [r.get("task_id", "unknown") for r in results]
            }
        }
        
        # Add specific summaries for each task
        for result in results:
            task_id = result.get("task_id", "unknown")
            if task_id == "seesaw_mass_generation":
                summary["seesaw_mass_generation"] = {
                    "best_seesaw_scale": result.get("seesaw_scale", "unknown"),
                    "best_seesaw_type": result.get("seesaw_type", "unknown"),
                    "best_score": result.get("best_score", float('inf'))
                }
            elif task_id == "mass_hierarchy_analysis":
                summary["mass_hierarchy_analysis"] = result.get("hierarchy_distribution", {})
            elif task_id == "pmns_validation":
                summary["pmns_validation"] = {
                    "pmns_matrix_valid": result.get("pmns_matrix_valid", False),
                    "mass_hierarchy": result.get("mass_hierarchy", "unknown"),
                    "seesaw_efficiency": result.get("seesaw_efficiency", 0.0)
                }
        
        return summary
