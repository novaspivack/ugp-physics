# S3 Irrep Decomposition Theoretical Implementation
# ======================================================================================================
# This implements the theoretical fix based on expert analysis:
# - S3 irrep decomposition: A1 (symmetric), E (2-dim), A2 (antisymmetric)
# - Left-handed vectors with A1⊕E⊕A2 content
# - Kernel-locked scales and phases (no continuous parameters)
# - Discrete S3 embedding search only

import numpy as np
import pandas as pd
import math
import cmath
import json
from itertools import permutations
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Any
import os

from .base import Experiment, timing_decorator
from ..core.registry import register_experiment


@dataclass
class IrrepTheoryResult:
    """Results from S3 irrep decomposition theoretical implementation."""
    ckm_matrix: np.ndarray
    pmns_matrix: np.ndarray
    ckm_angles: Dict[str, float]
    pmns_angles: Dict[str, float]
    ckm_score: float
    perm_choice: Tuple[int, ...]
    neutrino_model: str
    irrep_features_used: Dict[str, Any]
    kernel_scales: Dict[str, float]
    experimental_errors: Dict[str, float]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "ckm_matrix": [[{"real": float(x.real), "imag": float(x.imag)} for x in row] for row in self.ckm_matrix],
            "pmns_matrix": [[{"real": float(x.real), "imag": float(x.imag)} for x in row] for row in self.pmns_matrix],
            "ckm_angles": self.ckm_angles,
            "pmns_angles": self.pmns_angles,
            "ckm_score": float(self.ckm_score),
            "perm_choice": list(self.perm_choice),
            "neutrino_model": self.neutrino_model,
            "irrep_features_used": self.irrep_features_used,
            "kernel_scales": self.kernel_scales,
            "experimental_errors": self.experimental_errors
        }


@register_experiment("ugp_yukawa_ckm_pmns_irrep_theory")
class UGPYukawaCKMPMNSIrrepTheory(Experiment):
    """
    S3 irrep decomposition theoretical implementation for UGP Yukawa/CKM/PMNS mixing matrices.
    
    Based on expert analysis:
    - Uses A1⊕E⊕A2 irrep decomposition to fix structural failures
    - Implements left-handed vectors with proper irrep content
    - Kernel-locked scales and phases (no continuous parameters)
    - Discrete S3 embedding search only
    """
    
    def __init__(self, config: Dict[str, Any], root: str):
        super().__init__(config, Path(root))
        
        # Extract configuration
        self.neutrino_model = config.get("neutrino_model", "majorana")
        self.down_sector_permutation_policy = config.get("down_sector_permutation_policy", "optimize")
        self.down_sector_perm_fixed = tuple(config.get("down_sector_perm_fixed", [0, 1, 2]))
        self.pdg_targets_ckm = tuple(config.get("pdg_targets_ckm", [0.2245, 0.041, 0.00365]))
        
        # PDG Experimental Targets
        self.pdg_targets = {
            "Vus": 0.2245, "Vcb": 0.041, "Vub": 0.00365,
            "theta12": 33.44, "theta13": 8.57, "theta23": 49.2
        }
        
        # Elegant Kernel constants
        self.phi = (1 + 5**0.5) / 2.0
        self.k_L2 = 7.0 / 512.0
        self.k_gen2 = -self.phi / 2.0
        self.k_gen = math.pi / 2.0
        self.k_a, self.k_b, self.k_c = 1.0/8.0, -3.0/2.0, 4.0/3.0
        self.k_M = self.k_gen2 + 0.25 * self.k_L2
        self.CURV = math.sqrt(self.k_L2)
        
        # Kernel-locked scales for irreps
        self.kernel_scales = {
            "w_A1": math.sqrt(abs(self.k_a) * abs(self.k_b) * abs(self.k_c)),  # From face weights
            "w_E": abs(self.k_M),  # Quarter-Lock magnitude
            "w_A2": abs(self.k_M) / self.phi,  # Orientation cost
        }
        
        # Kernel-locked phases for irreps
        self.kernel_phases = {
            "phi_A1": 0.0,  # A1 can be real
            "phi_E": self.k_gen,  # E uses generational phase
            "phi_A2": self.k_gen + self.k_gen2,  # A2 uses oriented phase
        }
        
        # Canonical GTE triples (unchanged from original)
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
        
        # Neutrinos (unchanged)
        self.triples_nu = {
            ("nu_e", "nu", 1): (1, 1, 823),
            ("nu_mu", "nu", 2): (9, 1, 1023),
            ("nu_tau", "nu", 3): (5, 1, 65535),
        }
        
        # Build left-handed metric (kernel-locked)
        self.G_left = self._build_left_handed_metric()
    
    def _build_left_handed_metric(self) -> np.ndarray:
        """Build left-handed metric G_left with kernel-locked structure."""
        # 3x3 metric for A1⊕E⊕A2 space
        G = np.zeros((3, 3), dtype=float)
        
        # A1 block (diagonal)
        G[0, 0] = self.kernel_scales["w_A1"]
        
        # E block (2x2 submatrix)
        w_E = self.kernel_scales["w_E"]
        G[1, 1] = w_E
        G[2, 2] = w_E
        
        # A2 block (orientation-sensitive)
        G[2, 2] = self.kernel_scales["w_A2"]
        
        return G
    
    def _irrep_features(self, a: float, b: float, c: float) -> Tuple[float, Tuple[float, float], float]:
        """
        Extract S3 irrep features from triple (a,b,c).
        
        Returns:
        - A1: symmetric content (scalar)
        - E: 2-dimensional irrep (e1, e2)
        - A2: antisymmetric content (scalar with sign)
        """
        a, b, c = float(a), float(b), float(c)
        
        # A1 (symmetric): HM-like symmetric combination
        # Use harmonic mean of face features as A1 content
        hm_ab = 2.0 / (1.0/a + 1.0/b) if a != 0 and b != 0 else 0.0
        hm_bc = 2.0 / (1.0/b + 1.0/c) if b != 0 and c != 0 else 0.0
        hm_ca = 2.0 / (1.0/c + 1.0/a) if c != 0 and a != 0 else 0.0
        A1 = (hm_ab + hm_bc + hm_ca) / 3.0  # Symmetric average
        
        # E (2-dimensional): differences for misalignment
        e1 = a - b  # First E component
        e2 = (a + b - 2*c) / math.sqrt(3.0)  # Second E component (orthonormal)
        
        # A2 (antisymmetric): oriented Vandermonde (linear, not squared!)
        A2 = (a - b) * (b - c) * (c - a)  # Keep the sign for orientation
        
        return A1, (e1, e2), A2
    
    def _map_left_vector(self, a: float, b: float, c: float, g: int) -> np.ndarray:
        """
        Map triple (a,b,c) with generation g to left-handed vector using A1⊕E⊕A2.
        
        This is the key theoretical fix: using all three S3 irreps to break
        the over-symmetry that was causing simultaneous diagonalizability.
        """
        # Extract irrep features
        A1, (e1, e2), A2 = self._irrep_features(a, b, c)
        
        # Kernel-locked phases
        phase_A1 = cmath.exp(1j * g * self.kernel_phases["phi_A1"])
        phase_E = cmath.exp(1j * g * self.kernel_phases["phi_E"])
        phase_A2 = cmath.exp(1j * g * self.kernel_phases["phi_A2"])
        
        # Kernel-locked scales
        s_A1 = math.sqrt(self.kernel_scales["w_A1"]) * A1
        s_E = math.sqrt(self.kernel_scales["w_E"]) * e1  # Use e1 for left-doublet alignment
        s_A2 = math.sqrt(self.kernel_scales["w_A2"]) * A2
        
        # Assemble 3-component left vector: [A1, E_component, i*A2]
        # The "i" ensures A2 affects CP structure correctly
        v = np.array([
            s_A1 * phase_A1,
            s_E * phase_E,
            1j * s_A2 * phase_A2  # Imaginary for antisymmetric CP content
        ], dtype=complex)
        
        # Include global curvature factor
        v *= self.CURV
        
        return v
    
    def _sector_family_list(self, triples_dict: Dict, sector_key: str) -> List:
        """Get sorted list of families for a sector."""
        return sorted([k for k in triples_dict if k[1] == sector_key], key=lambda x: x[2])
    
    def _apply_perm_to_triples(self, triple: Tuple[int, int, int], perm: Tuple[int, ...]) -> Tuple[int, int, int]:
        """Apply S3 permutation to triple (a,b,c)."""
        a, b, c = triple
        permuted = [a, b, c]
        permuted = [permuted[i] for i in perm]
        return tuple(permuted)
    
    def _build_sector_vectors(self, triples_dict: Dict, sector_key: str, perm_faces: Optional[Tuple[int, ...]] = None) -> Tuple[List, List, np.ndarray]:
        """Build sector vectors using irrep decomposition."""
        fams = self._sector_family_list(triples_dict, sector_key)
        
        vectors = []
        names = []
        gens = []
        
        for name, sec, g in fams:
            a, b, c = triples_dict[(name, sec, g)]
            
            # Apply permutation if specified
            if perm_faces is not None:
                a, b, c = self._apply_perm_to_triples((a, b, c), perm_faces)
            
            # Map to left-handed vector
            v = self._map_left_vector(a, b, c, g)
            vectors.append(v)
            names.append(name)
            gens.append(g)
        
        return names, gens, np.array(vectors)
    
    def _gram_hermitian(self, vecs: np.ndarray) -> np.ndarray:
        """Hermitian inner products with left-handed metric."""
        n = len(vecs)
        M = np.zeros((n, n), dtype=complex)
        for i in range(n):
            for j in range(n):
                M[i, j] = np.conj(vecs[i]) @ self.G_left @ vecs[j]
        return M
    
    def _gram_symmetric(self, vecs: np.ndarray) -> np.ndarray:
        """Symmetric inner products with left-handed metric."""
        n = len(vecs)
        S = np.zeros((n, n), dtype=complex)
        for i in range(n):
            for j in range(n):
                S[i, j] = (vecs[i].T) @ self.G_left @ vecs[j]
        S = 0.5 * (S + S.T)
        return S
    
    def _diag_hermitian(self, M: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Diagonalize Hermitian matrix."""
        evals, U = np.linalg.eigh(M)
        idx = np.argsort(-np.abs(evals))  # Heavy to light
        return evals[idx], U[:, idx]
    
    def _takagi_factorization(self, S: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Takagi factorization for complex symmetric matrix (Majorana neutrinos)."""
        U, s, Vh = np.linalg.svd(S)
        M = U.conj().T @ S @ U
        phases = np.ones(len(s), dtype=complex)
        for i, di in enumerate(np.diag(M)):
            if abs(di) > 0:
                phases[i] = cmath.exp(-1j * cmath.phase(di) / 2.0)
        U2 = U @ np.diag(phases)
        D = U2.T @ S @ U2
        diag_vals = np.real(np.diag(D))
        diag_vals = np.maximum(diag_vals, 0.0)
        idx = np.argsort(diag_vals)  # Light to heavy for neutrinos
        return U2[:, idx], diag_vals[idx]
    
    def _reorder_to_pdg(self, U_sorted_heavy_to_light: np.ndarray) -> np.ndarray:
        """Reorder to PDG ordering (light→mid→heavy)."""
        idx = [2, 1, 0]
        return U_sorted_heavy_to_light[:, idx]
    
    def _ckm_score(self, V: np.ndarray, targets: Tuple[float, ...]) -> Tuple[float, Tuple[float, ...]]:
        """CKM score for discrete search optimization."""
        Vabs = np.abs(V)
        Vus, Vcb, Vub = Vabs[0, 1], Vabs[1, 2], Vabs[0, 2]
        tu, tc, tb = targets
        return ((Vus - tu) / tu)**2 + ((Vcb - tc) / tc)**2 + ((Vub - tb) / tb)**2, (Vus, Vcb, Vub)
    
    def _unitary_to_angles_and_J(self, U: np.ndarray) -> Dict[str, float]:
        """Extract mixing angles and Jarlskog invariant from unitary matrix."""
        Uabs = np.abs(U)
        s13 = Uabs[0, 2]
        c13 = math.sqrt(max(0.0, 1.0 - s13 * s13))
        s12 = Uabs[0, 1] / c13 if c13 > 1e-12 else 0.0
        s23 = Uabs[1, 2] / c13 if c13 > 1e-12 else 0.0
        s12 = min(max(s12, 0.0), 1.0)
        s23 = min(max(s23, 0.0), 1.0)
        t12 = math.degrees(math.asin(s12))
        t13 = math.degrees(math.asin(s13))
        t23 = math.degrees(math.asin(s23))
        J = float(np.imag(U[0, 0] * U[1, 1] * np.conj(U[0, 1]) * np.conj(U[1, 0])))
        c12 = math.sqrt(max(0.0, 1.0 - s12 * s12))
        c23 = math.sqrt(max(0.0, 1.0 - s23 * s23))
        denom = c12 * s12 * c23 * s23 * (c13**2) * s13
        if denom > 1e-15:
            arg = max(-1.0, min(1.0, J / denom))
            delta = math.degrees(math.asin(arg))
        else:
            delta = float('nan')
        return {
            "theta12_deg": t12,
            "theta13_deg": t13,
            "theta23_deg": t23,
            "J": J,
            "delta_deg_from_J": delta
        }
    
    def _calculate_experimental_errors(self, ckm_angles: Dict[str, float], pmns_angles: Dict[str, float], ckm_matrix: np.ndarray) -> Dict[str, float]:
        """Calculate errors compared to PDG experimental targets."""
        Vabs = np.abs(ckm_matrix)
        
        errors = {}
        errors["Vus_error"] = abs(Vabs[0, 1] - self.pdg_targets["Vus"]) / self.pdg_targets["Vus"]
        errors["Vcb_error"] = abs(Vabs[1, 2] - self.pdg_targets["Vcb"]) / self.pdg_targets["Vcb"]
        errors["Vub_error"] = abs(Vabs[0, 2] - self.pdg_targets["Vub"]) / self.pdg_targets["Vub"]
        errors["theta12_error"] = abs(ckm_angles["theta12_deg"] - self.pdg_targets["theta12"]) / self.pdg_targets["theta12"]
        errors["theta13_error"] = abs(pmns_angles["theta13_deg"] - self.pdg_targets["theta13"]) / self.pdg_targets["theta13"]
        errors["theta23_error"] = abs(pmns_angles["theta23_deg"] - self.pdg_targets["theta23"]) / self.pdg_targets["theta23"]
        
        error_values = list(errors.values())
        errors["overall_rms_error"] = math.sqrt(sum(e**2 for e in error_values) / len(error_values))
        
        return errors
    
    def _build_ckm_with_irrep_theory(self) -> Optional[Dict[str, Any]]:
        """Build CKM matrix using irrep decomposition theory."""
        names_u, gens_u, Vu = self._build_sector_vectors(self.triples_q_l, "up", perm_faces=None)
        
        if self.down_sector_permutation_policy == "fixed":
            perms = [self.down_sector_perm_fixed]
        else:
            perms = list(permutations([0, 1, 2]))
        
        best_ckm = None
        for perm in perms:
            names_d, gens_d, Vd = self._build_sector_vectors(self.triples_q_l, "down", perm_faces=perm)
            Mu = self._gram_hermitian(Vu)
            Md = self._gram_hermitian(Vd)
            eu, Uu = self._diag_hermitian(Mu)
            ed, Ud = self._diag_hermitian(Md)
            Uu_pdg = self._reorder_to_pdg(Uu)
            Ud_pdg = self._reorder_to_pdg(Ud)
            V = Uu_pdg.conj().T @ Ud_pdg
            score, trip = self._ckm_score(V, self.pdg_targets_ckm)
            if (best_ckm is None) or (score < best_ckm["score"]):
                best_ckm = {
                    "perm_down": perm,
                    "V": V, "score": float(score), "triplet": trip,
                    "Mu": Mu, "Md": Md, "evals_u": eu, "evals_d": ed,
                    "names_u": names_u, "names_d": names_d
                }
        
        return best_ckm
    
    def _build_pmns_with_irrep_theory(self) -> Dict[str, Any]:
        """Build PMNS matrix using irrep decomposition theory."""
        # Build charged lepton vectors
        names_l, gens_l, Vl = self._build_sector_vectors(self.triples_q_l, "lepton", perm_faces=None)
        Ml = self._gram_hermitian(Vl)
        el, Ul = self._diag_hermitian(Ml)
        Ul_pdg = self._reorder_to_pdg(Ul)
        
        # Build neutrino vectors
        names_n, gens_n, Vn = self._build_sector_vectors(self.triples_nu, "nu", perm_faces=None)
        
        if self.neutrino_model == "dirac":
            Mn = self._gram_hermitian(Vn)
            en, Un = self._diag_hermitian(Mn)
            Un_pdg = self._reorder_to_pdg(Un)
            U = Ul_pdg.conj().T @ Un_pdg
            evals_n = np.real(en[[2, 1, 0]])
            return {
                "model": "dirac",
                "U": U, "Ml": Ml, "Mn": Mn,
                "evals_l": el[[2, 1, 0]], "evals_n": evals_n,
                "names_l": names_l, "names_n": names_n
            }
        else:  # majorana
            Sn = self._gram_symmetric(Vn)
            Un_sorted, mn_sorted = self._takagi_factorization(Sn)
            U = Ul_pdg.conj().T @ Un_sorted
            return {
                "model": "majorana",
                "U": U, "Ml": Ml, "Sn": Sn,
                "evals_l": el[[2, 1, 0]], "evals_n": mn_sorted,
                "names_l": names_l, "names_n": names_n
            }
    
    def tasks(self) -> List[Dict[str, Any]]:
        """Return list of tasks for this experiment."""
        return [{
            "task_id": "irrep_theory_implementation",
            "description": "Implement S3 irrep decomposition theoretical approach",
            "theoretical_fixes": [
                "A1_symmetric_content",
                "E_2dim_misalignment", 
                "A2_antisymmetric_orientation",
                "kernel_locked_scales_phases",
                "left_handed_vectors_only"
            ]
        }]
    
    @timing_decorator
    def run_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Run the irrep theory implementation task."""
        task_id = task["task_id"]
        
        if task_id == "irrep_theory_implementation":
            try:
                # Build CKM with irrep theory
                ckm_result = self._build_ckm_with_irrep_theory()
                if ckm_result is None:
                    return {
                        "task_id": task_id,
                        "status": "failed",
                        "error": "CKM construction failed"
                    }
                
                # Build PMNS with irrep theory
                pmns_result = self._build_pmns_with_irrep_theory()
                
                # Extract results
                V = ckm_result["V"]
                U = pmns_result["U"]
                ckm_angles = self._unitary_to_angles_and_J(V)
                pmns_angles = self._unitary_to_angles_and_J(U)
                
                # Calculate experimental errors
                experimental_errors = self._calculate_experimental_errors(ckm_angles, pmns_angles, V)
                
                # Document irrep features used
                irrep_features_used = {
                    "A1_definition": "Symmetric harmonic mean average of face features",
                    "E_definition": "2-dimensional irrep with e1=a-b, e2=(a+b-2c)/√3",
                    "A2_definition": "Linear oriented Vandermonde Δ=(a-b)(b-c)(c-a)",
                    "left_vector_structure": "[A1, E_component, i*A2] with kernel-locked scales/phases"
                }
                
                # Create result object
                result = IrrepTheoryResult(
                    ckm_matrix=V,
                    pmns_matrix=U,
                    ckm_angles=ckm_angles,
                    pmns_angles=pmns_angles,
                    ckm_score=ckm_result["score"],
                    perm_choice=ckm_result["perm_down"],
                    neutrino_model=pmns_result["model"],
                    irrep_features_used=irrep_features_used,
                    kernel_scales=self.kernel_scales,
                    experimental_errors=experimental_errors
                )
                
                return {
                    "task_id": task_id,
                    "status": "completed",
                    "result": result.to_dict(),
                    "theoretical_fixes": task["theoretical_fixes"],
                    "irrep_analysis": {
                        "A1_contribution": "Symmetric content for magnitude geometry",
                        "E_contribution": "2-dim misalignment for Cabibbo and mixing",
                        "A2_contribution": "Oriented content for CP and 13 mixing",
                        "kernel_locking": "All scales and phases locked to Elegant Kernel constants"
                    }
                }
                
            except Exception as e:
                return {
                    "task_id": task_id,
                    "status": "failed",
                    "error": str(e),
                    "traceback": str(e.__traceback__) if hasattr(e, '__traceback__') else "No traceback available"
                }
        
        else:
            return {
                "task_id": task_id,
                "status": "failed",
                "error": f"Unknown task: {task_id}"
            }
    
    def summarize(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize the irrep theory results."""
        successful_results = [r for r in results if r.get("status") == "completed"]
        
        if not successful_results:
            return {
                "status": "failed",
                "message": "No successful tasks completed",
                "total_tasks": len(results),
                "successful_tasks": 0
            }
        
        result_data = successful_results[0]["result"]
        theoretical_fixes = successful_results[0].get("theoretical_fixes", [])
        irrep_analysis = successful_results[0].get("irrep_analysis", {})
        
        # Extract key metrics
        ckm_angles = result_data["ckm_angles"]
        pmns_angles = result_data["pmns_angles"]
        experimental_errors = result_data["experimental_errors"]
        
        return {
            "status": "completed",
            "total_tasks": len(results),
            "successful_tasks": len(successful_results),
            "theoretical_fixes": theoretical_fixes,
            "irrep_analysis": irrep_analysis,
            "experimental_performance": {
                "overall_rms_error": experimental_errors["overall_rms_error"],
                "individual_errors": {
                    "Vus": experimental_errors["Vus_error"],
                    "Vcb": experimental_errors["Vcb_error"],
                    "Vub": experimental_errors["Vub_error"],
                    "theta12": experimental_errors["theta12_error"],
                    "theta13": experimental_errors["theta13_error"],
                    "theta23": experimental_errors["theta23_error"]
                }
            },
            "mixing_angles": {
                "ckm": ckm_angles,
                "pmns": pmns_angles
            },
            "kernel_scales": result_data["kernel_scales"],
            "irrep_features": result_data["irrep_features_used"],
            "theoretical_approach": "S3 irrep decomposition with A1⊕E⊕A2 content and kernel-locked scales/phases"
        }
