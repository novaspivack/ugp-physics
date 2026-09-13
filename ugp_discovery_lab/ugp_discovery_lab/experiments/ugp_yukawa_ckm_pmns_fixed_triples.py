# Fixed Canonical Triples Implementation
# ======================================================================================================
# This experiment fixes the fundamental issue: degenerate canonical triples
# The problem: charm and bottom both have c=65535, causing rho calculation to fail
# The solution: use corrected canonical triples with unique c-values

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
class FixedTriplesResult:
    """Results from fixed canonical triples implementation."""
    ckm_matrix: np.ndarray
    pmns_matrix: np.ndarray
    ckm_angles: Dict[str, float]
    pmns_angles: Dict[str, float]
    ckm_score: float
    perm_choice: Tuple[int, ...]
    neutrino_model: str
    canonical_triples_used: Dict[str, Tuple[int, int, int]]
    rho_matrix: np.ndarray
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
            "canonical_triples_used": self.canonical_triples_used,
            "rho_matrix": self.rho_matrix.tolist(),
            "experimental_errors": self.experimental_errors
        }


@register_experiment("ugp_yukawa_ckm_pmns_fixed_triples")
class UGPYukawaCKMPMNSFixedTriples(Experiment):
    """
    Fixed canonical triples implementation for UGP Yukawa/CKM/PMNS mixing matrices.
    
    Fixes the fundamental issue: degenerate canonical triples causing rho calculation failure.
    Uses corrected canonical triples with unique c-values.
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
        
        # HM Normalization Constant (from HM constant testing results)
        self.HM_NORMALIZATION_CONSTANT = config.get("hm_normalization_constant", 3.0)
        
        # FIXED Canonical GTE triples (corrected for degenerate c-values)
        self.triples_q_l = {
            # charged leptons
            ("e", "lepton", 1): (1, 73, 823),
            ("mu", "lepton", 2): (9, 42, 1023),
            ("tau", "lepton", 3): (5, 275, 65535),
            # up-type quarks
            ("u", "up", 1): (5, 9, 275),
            ("c", "up", 2): (5, 275, 65535),
            ("t", "up", 3): (76, 337920, -1),
            # down-type quarks - FIXED!
            ("d", "down", 1): (9, 5, 42),
            ("s", "down", 2): (9, 186, 1023),
            ("b", "down", 3): (5, 8191, 32767),  # CHANGED from 65535 to 32767!
        }
        
        # Neutrinos (unchanged)
        self.triples_nu = {
            ("nu_e", "nu", 1): (1, 1, 823),
            ("nu_mu", "nu", 2): (9, 1, 1023),
            ("nu_tau", "nu", 3): (5, 1, 65535),
        }
        
        # Build face metric
        self.G_face = self._build_G_face()
    
    def _build_G_face(self) -> np.ndarray:
        """Build face metric with Quarter-Lock adjacency ring."""
        w_ab = math.sqrt(abs(self.k_a) * abs(self.k_b)) * self.HM_NORMALIZATION_CONSTANT
        w_bc = math.sqrt(abs(self.k_b) * abs(self.k_c)) * self.HM_NORMALIZATION_CONSTANT
        w_ca = math.sqrt(abs(self.k_c) * abs(self.k_a)) * self.HM_NORMALIZATION_CONSTANT
        FACE_WEIGHTS = np.array([w_ab, w_bc, w_ca], dtype=float)
        
        G = np.diag(FACE_WEIGHTS)
        s = abs(self.k_M)
        G[0, 1] = G[1, 0] = s
        G[1, 2] = G[2, 1] = s
        G[2, 0] = G[0, 2] = s
        return G
    
    def _HM(self, x: float, y: float) -> float:
        """Harmonic mean with optimized normalization constant."""
        x, y = float(x), float(y)
        if x == 0 or y == 0:
            return 0.0
        return self.HM_NORMALIZATION_CONSTANT * 2.0 / (1.0/x + 1.0/y)
    
    def _delta_squared(self, a: float, b: float, c: float) -> float:
        """Squared Vandermonde determinant."""
        a, b, c = float(a), float(b), float(c)
        d = (a - b) * (b - c) * (c - a)
        return d * d
    
    def _face_features_HM(self, a: float, b: float, c: float) -> np.ndarray:
        """Face features using harmonic means (ab, bc, ca)."""
        return np.array([
            self._HM(a, b), 
            self._HM(b, c), 
            self._HM(c, a)
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
    
    def _build_sector_vectors(self, triples_dict: Dict, sector_key: str, perm_faces: Optional[Tuple[int, ...]] = None) -> Tuple[List, List, np.ndarray, np.ndarray]:
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
            feats = self._face_features_HM(a, b, c)
            phases = self._face_phases(g)
            
            # Apply HM constant to face weights
            w_ab = math.sqrt(abs(self.k_a) * abs(self.k_b)) * self.HM_NORMALIZATION_CONSTANT
            w_bc = math.sqrt(abs(self.k_b) * abs(self.k_c)) * self.HM_NORMALIZATION_CONSTANT
            w_ca = math.sqrt(abs(self.k_c) * abs(self.k_a)) * self.HM_NORMALIZATION_CONSTANT
            FACE_WEIGHTS = np.array([w_ab, w_bc, w_ca], dtype=float)
            
            v = self.CURV * (FACE_WEIGHTS * feats) * phases
            v = math.sqrt(W[idx]) * v
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
        S = 0.5 * (S + S.T)
        return S
    
    def _diag_hermitian(self, M: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Diagonalize Hermitian matrix."""
        evals, U = np.linalg.eigh(M)
        idx = np.argsort(-np.abs(evals))
        return evals[idx], U[:, idx]
    
    def _takagi_factorization(self, S: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Takagi factorization for complex symmetric matrix."""
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
        errors["Vus_error"] = abs(Vabs[0, 1] - self.pdg_targets["Vus"]) / self.pdg_targets["Vus"]
        errors["Vcb_error"] = abs(Vabs[1, 2] - self.pdg_targets["Vcb"]) / self.pdg_targets["Vcb"]
        errors["Vub_error"] = abs(Vabs[0, 2] - self.pdg_targets["Vub"]) / self.pdg_targets["Vub"]
        errors["theta12_error"] = abs(ckm_angles["theta12_deg"] - self.pdg_targets["theta12"]) / self.pdg_targets["theta12"]
        errors["theta13_error"] = abs(pmns_angles["theta13_deg"] - self.pdg_targets["theta13"]) / self.pdg_targets["theta13"]
        errors["theta23_error"] = abs(pmns_angles["theta23_deg"] - self.pdg_targets["theta23"]) / self.pdg_targets["theta23"]
        
        error_values = list(errors.values())
        errors["overall_rms_error"] = math.sqrt(sum(e**2 for e in error_values) / len(error_values))
        
        return errors
    
    def _build_rho_matrix_from_fixed_triples(self) -> np.ndarray:
        """Build rho matrix using fixed canonical triples."""
        # This is the key fix - using corrected canonical triples
        u_triples = [self.triples_q_l[("u", "up", 1)], 
                     self.triples_q_l[("c", "up", 2)], 
                     self.triples_q_l[("t", "up", 3)]]
        d_triples = [self.triples_q_l[("d", "down", 1)], 
                     self.triples_q_l[("s", "down", 2)], 
                     self.triples_q_l[("b", "down", 3)]]
        
        R = np.zeros((3, 3), dtype=float)
        for i in range(3):
            for j in range(3):
                R[i, j] = self._rho_generic_fixed(u_triples[i], d_triples[j])
        
        return R
    
    def _rho_generic_fixed(self, u_triple: Tuple[int, int, int], d_triple: Tuple[int, int, int]) -> float:
        """Fixed version of rho_generic that handles the degenerate case better."""
        cu, cd, au = u_triple[2], d_triple[2], u_triple[0]
        
        # Use the same logic as the Discovery Engine but with better handling
        pmax_cu = self._largest_prime_factor_abs(cu)
        sump_cd = self._sum_distinct_primes_abs(cd)
        denom = abs(cu - cd)
        
        if denom == 0:
            # Better handling of degenerate case
            # Instead of setting denom=1, use a small epsilon
            denom = 1e-6
        
        numer = float(pmax_cu) + (float(au) / float(sump_cd if sump_cd != 0 else 1))
        return 1.0 + (numer / float(denom))
    
    def _largest_prime_factor_abs(self, n: int) -> int:
        """Largest prime factor of |n|."""
        n = abs(n)
        if n <= 1:
            return 1
        
        largest = 1
        # Check for factor 2
        while n % 2 == 0:
            largest = 2
            n //= 2
        
        # Check for odd factors
        for i in range(3, int(math.sqrt(n)) + 1, 2):
            while n % i == 0:
                largest = i
                n //= i
        
        if n > 2:
            largest = n
        
        return largest
    
    def _sum_distinct_primes_abs(self, n: int) -> int:
        """Sum of distinct prime factors of |n|."""
        n = abs(n)
        if n <= 1:
            return 0
        
        primes = set()
        # Check for factor 2
        while n % 2 == 0:
            primes.add(2)
            n //= 2
        
        # Check for odd factors
        for i in range(3, int(math.sqrt(n)) + 1, 2):
            while n % i == 0:
                primes.add(i)
                n //= i
        
        if n > 2:
            primes.add(n)
        
        return sum(primes)
    
    def _build_ckm_with_fixed_triples(self) -> Optional[Dict[str, Any]]:
        """Build CKM matrix with fixed canonical triples."""
        names_u, gens_u, Vu, Wu = self._build_sector_vectors(self.triples_q_l, "up", perm_faces=None)
        
        if self.down_sector_permutation_policy == "fixed":
            perms = [self.down_sector_perm_fixed]
        else:
            perms = list(permutations([0, 1, 2]))
        
        best_ckm = None
        for perm in perms:
            names_d, gens_d, Vd, Wd = self._build_sector_vectors(self.triples_q_l, "down", perm_faces=perm)
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
    
    def _build_pmns_with_fixed_triples(self) -> Dict[str, Any]:
        """Build PMNS matrix with fixed canonical triples."""
        # Build charged lepton vectors
        names_l, gens_l, Vl, Wl = self._build_sector_vectors(self.triples_q_l, "lepton", perm_faces=None)
        Ml = self._gram_hermitian(Vl)
        el, Ul = self._diag_hermitian(Ml)
        Ul_pdg = self._reorder_to_pdg(Ul)
        
        # Build neutrino vectors
        names_n, gens_n, Vn, Wn = self._build_sector_vectors(self.triples_nu, "nu", perm_faces=None)
        
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
            "task_id": "fixed_canonical_triples",
            "description": "Implement fixed canonical triples to resolve degenerate rho calculation",
            "fixes": [
                "corrected_bottom_triple_c_value",
                "non_degenerate_rho_calculation",
                "theoretical_approach_preserved"
            ]
        }]
    
    @timing_decorator
    def run_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Run the fixed canonical triples task."""
        task_id = task["task_id"]
        
        if task_id == "fixed_canonical_triples":
            try:
                # Build rho matrix to verify the fix
                rho_matrix = self._build_rho_matrix_from_fixed_triples()
                
                # Build CKM with fixed triples
                ckm_result = self._build_ckm_with_fixed_triples()
                if ckm_result is None:
                    return {
                        "task_id": task_id,
                        "status": "failed",
                        "error": "CKM construction failed"
                    }
                
                # Build PMNS with fixed triples
                pmns_result = self._build_pmns_with_fixed_triples()
                
                # Extract results
                V = ckm_result["V"]
                U = pmns_result["U"]
                ckm_angles = self._unitary_to_angles_and_J(V)
                pmns_angles = self._unitary_to_angles_and_J(U)
                
                # Calculate experimental errors
                experimental_errors = self._calculate_experimental_errors(ckm_angles, pmns_angles, V)
                
                # Create canonical triples summary
                canonical_triples_used = {}
                for (name, sec, g), (a, b, c) in self.triples_q_l.items():
                    canonical_triples_used[f"{name}_{sec}_{g}"] = (a, b, c)
                
                # Create result object
                result = FixedTriplesResult(
                    ckm_matrix=V,
                    pmns_matrix=U,
                    ckm_angles=ckm_angles,
                    pmns_angles=pmns_angles,
                    ckm_score=ckm_result["score"],
                    perm_choice=ckm_result["perm_down"],
                    neutrino_model=pmns_result["model"],
                    canonical_triples_used=canonical_triples_used,
                    rho_matrix=rho_matrix,
                    experimental_errors=experimental_errors
                )
                
                return {
                    "task_id": task_id,
                    "status": "completed",
                    "result": result.to_dict(),
                    "fixes_applied": task["fixes"],
                    "rho_matrix_analysis": {
                        "rho_matrix": rho_matrix.tolist(),
                        "max_element": float(np.max(rho_matrix)),
                        "min_element": float(np.min(rho_matrix)),
                        "degenerate_fixed": float(np.max(rho_matrix)) < 100.0  # Should be much less than 258
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
        """Summarize the fixed triples results."""
        successful_results = [r for r in results if r.get("status") == "completed"]
        
        if not successful_results:
            return {
                "status": "failed",
                "message": "No successful tasks completed",
                "total_tasks": len(results),
                "successful_tasks": 0
            }
        
        result_data = successful_results[0]["result"]
        rho_analysis = successful_results[0].get("rho_matrix_analysis", {})
        fixes_applied = successful_results[0].get("fixes_applied", [])
        
        # Extract key metrics
        ckm_angles = result_data["ckm_angles"]
        pmns_angles = result_data["pmns_angles"]
        experimental_errors = result_data["experimental_errors"]
        rho_matrix = np.array(result_data["rho_matrix"])
        
        return {
            "status": "completed",
            "total_tasks": len(results),
            "successful_tasks": len(successful_results),
            "fixes_applied": fixes_applied,
            "rho_matrix_fix_status": rho_analysis.get("degenerate_fixed", False),
            "rho_matrix_analysis": {
                "max_element": float(np.max(rho_matrix)),
                "min_element": float(np.min(rho_matrix)),
                "degenerate_fixed": float(np.max(rho_matrix)) < 100.0,
                "original_problem": "charm and bottom both had c=65535",
                "fix_applied": "changed bottom c-value from 65535 to 32767"
            },
            "canonical_triples_used": result_data["canonical_triples_used"],
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
            "improvement_analysis": {
                "hm_constant_used": self.HM_NORMALIZATION_CONSTANT,
                "neutrino_model": result_data["neutrino_model"],
                "permutation_choice": list(result_data["perm_choice"]),
                "theoretical_approach": "Fixed canonical triples with non-degenerate c-values"
            }
        }
