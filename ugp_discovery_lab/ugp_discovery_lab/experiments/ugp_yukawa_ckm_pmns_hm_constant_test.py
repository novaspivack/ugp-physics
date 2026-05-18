# HM Constant Testing: Systematic test of alternative HM normalization constants
# ======================================================================================================
# This experiment tests different HM constants derived from parallel-additivity proof
# to find the optimal value for mixing angle predictions

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
class HMConstantTestResult:
    """Results from HM constant testing."""
    hm_constant: float
    ckm_matrix: np.ndarray
    pmns_matrix: np.ndarray
    ckm_angles: Dict[str, float]
    pmns_angles: Dict[str, float]
    ckm_score: float
    perm_choice: Tuple[int, ...]
    experimental_errors: Dict[str, float]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "hm_constant": float(self.hm_constant),
            "ckm_matrix": [[{"real": float(x.real), "imag": float(x.imag)} for x in row] for row in self.ckm_matrix],
            "pmns_matrix": [[{"real": float(x.real), "imag": float(x.imag)} for x in row] for row in self.pmns_matrix],
            "ckm_angles": self.ckm_angles,
            "pmns_angles": self.pmns_angles,
            "ckm_score": float(self.ckm_score),
            "perm_choice": list(self.perm_choice),
            "experimental_errors": self.experimental_errors
        }


@register_experiment("ugp_yukawa_ckm_pmns_hm_constant_test")
class UGPYukawaCKMPMNSHMConstantTest(Experiment):
    """
    Systematic test of alternative HM normalization constants from parallel-additivity proof.
    
    Tests multiple HM constants to find optimal value for mixing angle predictions.
    """
    
    def __init__(self, config: Dict[str, Any], root: str):
        super().__init__(config, Path(root))
        
        # Extract configuration
        self.hm_constants_to_test = config.get("hm_constants_to_test", [
            1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0,  # Basic range
            1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5,  # Half-steps
            math.pi, math.e, math.sqrt(2), math.sqrt(3), math.sqrt(5),  # Mathematical constants
            1.618033988749895,  # Golden ratio
            1.4142135623730951,  # sqrt(2)
            2.718281828459045,   # e
            3.141592653589793,   # pi
        ])
        self.down_sector_permutation_policy = config.get("down_sector_permutation_policy", "optimize")
        self.down_sector_perm_fixed = tuple(config.get("down_sector_perm_fixed", [0, 1, 2]))
        self.pdg_targets_ckm = tuple(config.get("pdg_targets_ckm", [0.2245, 0.041, 0.00365]))
        
        # PDG Experimental Targets for comparison
        self.pdg_targets = {
            # CKM mixing elements
            "Vus": 0.2245,
            "Vcb": 0.041,
            "Vub": 0.00365,
            # PMNS mixing angles (degrees)
            "theta12": 33.44,  # Solar mixing angle
            "theta13": 8.57,   # Reactor mixing angle  
            "theta23": 49.2,   # Atmospheric mixing angle
        }
        
        # Elegant Kernel constants (exact where feasible)
        self.phi = (1 + 5**0.5) / 2.0
        self.k_L2 = 7.0 / 512.0
        self.k_gen2 = -self.phi / 2.0
        self.k_gen = math.pi / 2.0
        self.k_a, self.k_b, self.k_c = 1.0/8.0, -3.0/2.0, 4.0/3.0
        self.k_M = self.k_gen2 + 0.25 * self.k_L2
        self.CURV = math.sqrt(self.k_L2)  # global curvature scalar
        
        # Canonical GTE triples (Verifier V8)
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
        
        # Neutrinos with proper Discovery Engine physics
        self.triples_nu = {
            ("nu_e", "nu", 1): (1, 1, 823),
            ("nu_mu", "nu", 2): (9, 1, 1023),
            ("nu_tau", "nu", 3): (5, 1, 65535),
        }
        
        # Build face metric with Quarter-Lock adjacency ring
        self.G_face = self._build_G_face()
    
    def _build_G_face(self) -> np.ndarray:
        """Build face metric with Quarter-Lock adjacency ring."""
        # Face weights from |k| magnitudes (positive)
        w_ab = math.sqrt(abs(self.k_a) * abs(self.k_b))
        w_bc = math.sqrt(abs(self.k_b) * abs(self.k_c))
        w_ca = math.sqrt(abs(self.k_c) * abs(self.k_a))
        FACE_WEIGHTS = np.array([w_ab, w_bc, w_ca], dtype=float)
        
        G = np.diag(FACE_WEIGHTS)
        s = abs(self.k_M)
        # adjacency ring (ab-bc, bc-ca, ca-ab)
        G[0, 1] = G[1, 0] = s  # ab↔bc share b
        G[1, 2] = G[2, 1] = s  # bc↔ca share c
        G[2, 0] = G[0, 2] = s  # ca↔ab share a
        return G
    
    def _HM(self, x: float, y: float, hm_constant: float) -> float:
        """Harmonic mean of x and y with specified HM normalization constant."""
        x, y = float(x), float(y)
        if x == 0 or y == 0:
            return 0.0
        # Apply specified HM normalization constant
        return hm_constant * 2.0 / (1.0/x + 1.0/y)
    
    def _delta_squared(self, a: float, b: float, c: float) -> float:
        """Squared Vandermonde determinant."""
        a, b, c = float(a), float(b), float(c)
        d = (a - b) * (b - c) * (c - a)
        return d * d
    
    def _face_features_HM(self, a: float, b: float, c: float, hm_constant: float) -> np.ndarray:
        """Face features using harmonic means (ab, bc, ca) with specified HM normalization."""
        return np.array([
            self._HM(a, b, hm_constant), 
            self._HM(b, c, hm_constant), 
            self._HM(c, a, hm_constant)
        ], dtype=float)
    
    def _face_phases(self, g: int) -> np.ndarray:
        """Generational phases on faces (average of endpoint phases)."""
        ph_a = 0.0
        ph_b = self.k_gen
        ph_c = self.k_gen + self.k_gen2
        ph_ab = 0.5 * (ph_a + ph_b)
        ph_bc = 0.5 * (ph_b + ph_c)
        ph_ca = 0.5 * (ph_c + ph_a)
        return np.array([
            cmath.exp(1j * g * ph_ab),
            cmath.exp(1j * g * ph_bc),
            cmath.exp(1j * g * ph_ca)
        ], dtype=complex)
    
    def _sector_family_list(self, triples_dict: Dict, sector_key: str) -> List:
        """Get sorted list of families for a sector."""
        return sorted([k for k in triples_dict if k[1] == sector_key], key=lambda x: x[2])
    
    def _apply_perm_to_faces(self, vec3: np.ndarray, perm: Tuple[int, ...]) -> np.ndarray:
        """Apply permutation to face vector."""
        return vec3[list(perm)]
    
    def _build_sector_vectors(self, triples_dict: Dict, sector_key: str, hm_constant: float, perm_faces: Optional[Tuple[int, ...]] = None) -> Tuple[List, List, np.ndarray, np.ndarray]:
        """Build sector vectors with HM + Δ², optional face-permutation."""
        fams = self._sector_family_list(triples_dict, sector_key)
        
        # Δ² weights per family, normalized
        deltas = np.array([self._delta_squared(*triples_dict[(name, sec, g)]) for (name, sec, g) in fams], dtype=float)
        if np.all(deltas == 0):
            W = np.ones(len(fams)) / len(fams)
        else:
            W = deltas / np.sum(deltas)
        
        vectors = []
        names = []
        gens = []
        for idx, (name, sec, g) in enumerate(fams):
            a, b, c = triples_dict[(name, sec, g)]
            feats = self._face_features_HM(a, b, c, hm_constant)  # HM faces with specified normalization
            phases = self._face_phases(g)  # face phases
            
            # Apply HM constant to face weights
            w_ab = math.sqrt(abs(self.k_a) * abs(self.k_b)) * hm_constant
            w_bc = math.sqrt(abs(self.k_b) * abs(self.k_c)) * hm_constant
            w_ca = math.sqrt(abs(self.k_c) * abs(self.k_a)) * hm_constant
            FACE_WEIGHTS = np.array([w_ab, w_bc, w_ca], dtype=float)
            
            v = self.CURV * (FACE_WEIGHTS * feats) * phases  # weights & phases
            v = math.sqrt(W[idx]) * v  # Δ² factor
            if perm_faces is not None:
                v = self._apply_perm_to_faces(v, perm_faces)
            vectors.append(v.astype(complex))
            names.append(name)
            gens.append(g)
        return names, gens, np.array(vectors), W
    
    def _gram_hermitian(self, vecs: np.ndarray) -> np.ndarray:
        """Hermitian inner products."""
        n = len(vecs)
        M = np.zeros((n, n), dtype=complex)
        for i in range(n):
            for j in range(n):
                M[i, j] = np.conj(vecs[i]) @ self.G_face @ vecs[j]
        return M
    
    def _gram_symmetric(self, vecs: np.ndarray) -> np.ndarray:
        """Symmetric inner products."""
        n = len(vecs)
        S = np.zeros((n, n), dtype=complex)
        for i in range(n):
            for j in range(n):
                S[i, j] = (vecs[i].T) @ self.G_face @ vecs[j]
        # enforce symmetry numerically
        S = 0.5 * (S + S.T)
        return S
    
    def _diag_hermitian(self, M: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Diagonalize Hermitian matrix."""
        evals, U = np.linalg.eigh(M)  # ascending
        idx = np.argsort(-np.abs(evals))  # heavy→light
        return evals[idx], U[:, idx]
    
    def _takagi_factorization(self, S: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Takagi factorization for complex symmetric matrix."""
        # S complex symmetric; find U s.t. U^T S U = diag(s_i >= 0)
        U, s, Vh = np.linalg.svd(S)
        # phase alignment for positive real diagonal
        M = U.conj().T @ S @ U
        phases = np.ones(len(s), dtype=complex)
        for i, di in enumerate(np.diag(M)):
            if abs(di) > 0:
                phases[i] = cmath.exp(-1j * cmath.phase(di) / 2.0)
        U2 = U @ np.diag(phases)
        D = U2.T @ S @ U2
        diag_vals = np.real(np.diag(D))
        diag_vals = np.maximum(diag_vals, 0.0)
        # sort ascending (ν1 lightest)
        idx = np.argsort(diag_vals)
        return U2[:, idx], diag_vals[idx]
    
    def _reorder_to_pdg(self, U_sorted_heavy_to_light: np.ndarray) -> np.ndarray:
        """Reorder to PDG ordering (light→mid→heavy)."""
        idx = [2, 1, 0]
        return U_sorted_heavy_to_light[:, idx]
    
    def _ckm_score(self, V: np.ndarray, targets: Tuple[float, ...]) -> Tuple[float, Tuple[float, ...]]:
        """CKM score (for logging only; no continuous optimization)."""
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
        
        # CKM mixing elements
        errors["Vus_error"] = abs(Vabs[0, 1] - self.pdg_targets["Vus"]) / self.pdg_targets["Vus"]
        errors["Vcb_error"] = abs(Vabs[1, 2] - self.pdg_targets["Vcb"]) / self.pdg_targets["Vcb"]
        errors["Vub_error"] = abs(Vabs[0, 2] - self.pdg_targets["Vub"]) / self.pdg_targets["Vub"]
        
        # PMNS mixing angles
        errors["theta12_error"] = abs(ckm_angles["theta12_deg"] - self.pdg_targets["theta12"]) / self.pdg_targets["theta12"]
        errors["theta13_error"] = abs(pmns_angles["theta13_deg"] - self.pdg_targets["theta13"]) / self.pdg_targets["theta13"]
        errors["theta23_error"] = abs(pmns_angles["theta23_deg"] - self.pdg_targets["theta23"]) / self.pdg_targets["theta23"]
        
        # Overall error (RMS)
        error_values = list(errors.values())
        errors["overall_rms_error"] = math.sqrt(sum(e**2 for e in error_values) / len(error_values))
        
        return errors
    
    def _build_ckm_pmns_with_hm_constant(self, hm_constant: float) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        """Build CKM and PMNS matrices with specified HM constant."""
        names_u, gens_u, Vu, Wu = self._build_sector_vectors(self.triples_q_l, "up", hm_constant, perm_faces=None)
        
        if self.down_sector_permutation_policy == "fixed":
            perms = [self.down_sector_perm_fixed]
        else:
            perms = list(permutations([0, 1, 2]))
        
        best_ckm = None
        for perm in perms:
            names_d, gens_d, Vd, Wd = self._build_sector_vectors(self.triples_q_l, "down", hm_constant, perm_faces=perm)
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
        
        # Build PMNS
        names_l, gens_l, Vl, Wl = self._build_sector_vectors(self.triples_q_l, "lepton", hm_constant, perm_faces=None)
        Ml = self._gram_hermitian(Vl)
        el, Ul = self._diag_hermitian(Ml)
        Ul_pdg = self._reorder_to_pdg(Ul)
        
        names_n, gens_n, Vn, Wn = self._build_sector_vectors(self.triples_nu, "nu", hm_constant, perm_faces=None)
        Sn = self._gram_symmetric(Vn)
        Un_sorted, mn_sorted = self._takagi_factorization(Sn)
        U = Ul_pdg.conj().T @ Un_sorted
        
        pmns_result = {
            "model": "majorana", "U": U, "Ml": Ml, "Sn": Sn,
            "evals_l": el[[2, 1, 0]], "evals_n": mn_sorted,
            "names_l": names_l, "names_n": names_n
        }
        
        return best_ckm, pmns_result
    
    def tasks(self) -> List[Dict[str, Any]]:
        """Return list of tasks for this experiment."""
        return [{
            "task_id": "hm_constant_systematic_test",
            "description": "Systematic test of alternative HM normalization constants",
            "hm_constants": self.hm_constants_to_test,
            "pdg_targets": self.pdg_targets
        }]
    
    @timing_decorator
    def run_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Run the HM constant systematic test."""
        task_id = task["task_id"]
        
        if task_id == "hm_constant_systematic_test":
            results = []
            
            for hm_constant in self.hm_constants_to_test:
                try:
                    # Build CKM and PMNS matrices with this HM constant
                    ckm_result, pmns_result = self._build_ckm_pmns_with_hm_constant(hm_constant)
                    
                    if ckm_result is None:
                        continue
                    
                    # Extract results
                    V = ckm_result["V"]
                    U = pmns_result["U"]
                    ckm_angles = self._unitary_to_angles_and_J(V)
                    pmns_angles = self._unitary_to_angles_and_J(U)
                    
                    # Calculate experimental errors
                    experimental_errors = self._calculate_experimental_errors(ckm_angles, pmns_angles, V)
                    
                    # Create result object
                    result = HMConstantTestResult(
                        hm_constant=hm_constant,
                        ckm_matrix=V,
                        pmns_matrix=U,
                        ckm_angles=ckm_angles,
                        pmns_angles=pmns_angles,
                        ckm_score=ckm_result["score"],
                        perm_choice=ckm_result["perm_down"],
                        experimental_errors=experimental_errors
                    )
                    
                    results.append(result.to_dict())
                    
                except Exception as e:
                    print(f"Error testing HM constant {hm_constant}: {e}")
                    continue
            
            # Sort results by overall RMS error
            results.sort(key=lambda x: x["experimental_errors"]["overall_rms_error"])
            
            return {
                "task_id": task_id,
                "status": "completed",
                "results": results,
                "best_hm_constant": results[0]["hm_constant"] if results else None,
                "best_overall_error": results[0]["experimental_errors"]["overall_rms_error"] if results else None
            }
        
        else:
            return {
                "task_id": task_id,
                "status": "failed",
                "error": f"Unknown task: {task_id}"
            }
    
    def summarize(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize the HM constant test results."""
        successful_results = [r for r in results if r.get("status") == "completed"]
        
        if not successful_results:
            return {
                "status": "failed",
                "message": "No successful tasks completed",
                "total_tasks": len(results),
                "successful_tasks": 0
            }
        
        # Extract results from successful task
        task_results = successful_results[0]["results"]
        best_hm_constant = successful_results[0]["best_hm_constant"]
        best_overall_error = successful_results[0]["best_overall_error"]
        
        # Create summary table
        summary_table = []
        for result in task_results[:10]:  # Top 10 results
            summary_table.append({
                "hm_constant": result["hm_constant"],
                "overall_rms_error": result["experimental_errors"]["overall_rms_error"],
                "Vus_error": result["experimental_errors"]["Vus_error"],
                "theta13_error": result["experimental_errors"]["theta13_error"],
                "theta12_error": result["experimental_errors"]["theta12_error"],
                "theta23_error": result["experimental_errors"]["theta23_error"]
            })
        
        # Find best constants for specific observables
        best_vus = min(task_results, key=lambda x: x["experimental_errors"]["Vus_error"])
        best_theta13 = min(task_results, key=lambda x: x["experimental_errors"]["theta13_error"])
        best_theta12 = min(task_results, key=lambda x: x["experimental_errors"]["theta12_error"])
        best_theta23 = min(task_results, key=lambda x: x["experimental_errors"]["theta23_error"])
        
        return {
            "status": "completed",
            "total_tasks": len(results),
            "successful_tasks": len(successful_results),
            "total_constants_tested": len(task_results),
            "best_overall_hm_constant": best_hm_constant,
            "best_overall_error": best_overall_error,
            "summary_table": summary_table,
            "best_constants_by_observable": {
                "Vus": {
                    "hm_constant": best_vus["hm_constant"],
                    "error": best_vus["experimental_errors"]["Vus_error"]
                },
                "theta13": {
                    "hm_constant": best_theta13["hm_constant"],
                    "error": best_theta13["experimental_errors"]["theta13_error"]
                },
                "theta12": {
                    "hm_constant": best_theta12["hm_constant"],
                    "error": best_theta12["experimental_errors"]["theta12_error"]
                },
                "theta23": {
                    "hm_constant": best_theta23["hm_constant"],
                    "error": best_theta23["experimental_errors"]["theta23_error"]
                }
            },
            "improvement_over_current": {
                "current_hm_constant": 4.0,
                "current_error": "unknown",
                "best_hm_constant": best_hm_constant,
                "best_error": best_overall_error
            }
        }
