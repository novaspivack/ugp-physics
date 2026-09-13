"""
UGP → CP Violation → Matter–Antimatter Asymmetry Probe
=====================================================

What this module does
---------------------
1) Computes CP observables from mixing matrices:
   - Jarlskog invariants: J_CKM, J_PMNS
   - Dirac CP phases: δ_q, δ_ℓ (via J = s12 s13 s23 c12 c13^2 c23 sin δ)

2) Tests UGP-locked E-phase hypotheses *without fitting*:
   H1 (Dirac):  δ_q ≈ σ_q * k_gen
   H2 (Majorana): δ_ℓ ≈ σ_ℓ * f * k_gen,  with f ∈ {1.0, 0.5, 0.0} (Takagi-consistent)
   Signs σ_* ∈ {+1, -1} are discrete (orientation parity).

3) Builds a leptogenesis proxy from M_eff (symmetric light ν mass matrix):
   - Extracts ν masses & mixing (Takagi)
   - Forms a dimensionless CP-proxy: J_ℓ_eff = J_PMNS · 𝓗, where
     𝓗 = (m3 - m2) (m2 - m1) (m3 - m1) / (m3 + m2 + m1)^3
     (purely scale-free, monotone in hierarchy & splittings)
   - Reports η̂_B ∝ J_ℓ_eff (normalized), for comparisons across runs.

Inputs (any of the following, in order of preference)
----------------------------------------------------
- Provide raw matrices: V_ckm (3x3 complex), U_pmns (3x3 complex), M_eff (3x3 complex symmetric)
- Or provide angle dictionaries: angles_ckm, angles_pmns (deg)
- Or pass a "producer" callable that returns a dict with the above (e.g., call your existing experiment)

No external data or fitting. NumPy/Scipy only.

Usage
-----
from ugp_discovery_lab.experiments.ugp_cp_asymmetry_probe import UGPCPAsymmetryProbe
probe = UGPCPAsymmetryProbe(config, root)
result = probe.run_task("cp_probe")

Config options (all optional)
-----------------------------
options:
  kernel:
    phi: 1.618033988749895
    k_gen: 1.5707963267948966
  ugp_phase_tests:
    majorana_phase_fraction: [1.0, 0.5, 0.0]   # discrete, tested automatically
    signs: [+1, -1]
  inputs:
    # you can pass explicit matrices here if you want
    V_ckm: null
    U_pmns: null
    M_eff: null
"""

from __future__ import annotations
import numpy as np
from typing import Any, Dict, Optional, Tuple, Callable
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
from scipy.linalg import eigh, svd

# ---------------------------------------------------------------------
#                     Math utilities (mixing, phases)
# ---------------------------------------------------------------------

def _safe_arcsin(x: float) -> float:
    return np.arcsin(np.clip(x, -1.0, 1.0))

def angles_from_unitary(U: np.ndarray) -> Dict[str, float]:
    """
    PDG-like extraction (magnitudes only):
    s13 = |U_e3|; c13 = sqrt(1 - s13^2)
    s12 = |U_e2| / c13; s23 = |U_μ3| / c13
    Returns degrees.
    """
    Uabs = np.abs(U)
    s13 = Uabs[0, 2]
    c13 = float(np.sqrt(max(0.0, 1.0 - s13 * s13)))
    s12 = float(Uabs[0, 1] / (c13 + 1e-18))
    s23 = float(Uabs[1, 2] / (c13 + 1e-18))
    s12 = float(np.clip(s12, 0.0, 1.0))
    s23 = float(np.clip(s23, 0.0, 1.0))
    return {
        "theta12": float(np.degrees(_safe_arcsin(s12))),
        "theta13": float(np.degrees(_safe_arcsin(s13))),
        "theta23": float(np.degrees(_safe_arcsin(s23))),
    }

def sines_cosines_from_angles_deg(ang: Dict[str, float]) -> Dict[str, float]:
    d2r = np.pi / 180.0
    t12, t13, t23 = [ang[k] * d2r for k in ("theta12", "theta13", "theta23")]
    s12, s13, s23 = np.sin((t12, t13, t23))
    c12, c13, c23 = np.cos((t12, t13, t23))
    return {"s12": s12, "s13": s13, "s23": s23, "c12": c12, "c13": c13, "c23": c23}

def jarlskog_from_unitary(U: np.ndarray) -> float:
    """
    Basis-invariant definition: pick any quartet; here (ud, cs, us, cd).
    J = Im(U_11 U_22 U_12* U_21*)
    """
    return float(np.imag(U[0,0]*U[1,1]*np.conj(U[0,1])*np.conj(U[1,0])))

def delta_from_J_and_angles(J: float, ang: Dict[str, float]) -> float:
    """
    J = s12 s23 s13 c12 c23 c13^2 sin δ   ->  δ in radians (with sign of J).
    Returns δ in radians in [-pi, pi].
    """
    sc = sines_cosines_from_angles_deg(ang)
    denom = sc["s12"]*sc["s23"]*sc["s13"]*sc["c12"]*sc["c23"]*(sc["c13"]**2) + 1e-18
    x = np.clip(J / denom, -1.0, 1.0)
    return float(np.arcsin(x))

def takagi_unitary(Ms: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Takagi factorization for complex symmetric Ms: Ms = U diag(m_i) U^T, m_i ≥ 0.
    Robust via eig(M* M).
    """
    Ms = 0.5*(Ms + Ms.T)
    H = Ms.conj() @ Ms
    w, Z = eigh(H)
    idx = np.argsort(w)[::-1]
    Z = Z[:, idx]
    D = Z.T @ Ms @ Z
    phases = np.exp(-0.5j * np.angle(np.diag(D)+1e-30))
    U = Z @ np.diag(phases)
    m = np.real(np.diag(U.T @ Ms @ U))
    m = np.clip(m, 0.0, None)
    return U, m

# ---------------------------------------------------------------------
#                       UGP phase tests (discrete)
# ---------------------------------------------------------------------

@dataclass
class UGPPhaseKernel:
    phi: float = (1.0 + 5.0**0.5) / 2.0    # golden ratio
    k_gen: float = np.pi / 2.0             # π/2

def ugp_phase_hypotheses(kernel: UGPPhaseKernel) -> Dict[str, Dict[str, Any]]:
    """
    Returns Z₆ hexagonal symmetry discrete hypothesis families (fit-free).
    
    Based on gauge group center structure (Baez 2003, Bakker et al. 2004):
    - SU(3) center: Z₃ → exp(2πi/3)
    - SU(2) center: Z₂ → exp(iπ) = -1
    - Combined: Z₆ → exp(πi/3) (sixth root of unity)
    
    Z₆ values: 0°, 60°, 120°, 180°, 240°, 300° (k·π/3 for k=0,1,2,3,4,5)
    
    H1_hex (quarks/CKM): δ_q ∈ {k·π/3: k=0,1,2,3,4,5} × {±1}
    H2_hex (leptons/PMNS): δ_ℓ ∈ {k·π/3: k=0,1,2,3,4,5} × {±1}
    
    Old hypothesis (H1/H2 using π/2) deprecated - not consistent with gauge centers.
    """
    # Z₆ fundamental angle is π/3 (60°)
    # Fractions: k/3 for k=0,1,2,3,4,5 gives all Z₆ values when multiplied by π
    z6_fractions = [0.0, 1.0/3.0, 2.0/3.0, 1.0, 4.0/3.0, 5.0/3.0]
    
    return {
        "H1_hex_ckm": {
            "fractions": z6_fractions,
            "signs": [+1, -1], 
            "k": np.pi,  # Base is π, fractions give k·π/3
            "description": "Z₆ hexagonal symmetry for quarks (CKM)"
        },
        "H2_hex_pmns": {
            "fractions": z6_fractions,
            "signs": [+1, -1], 
            "k": np.pi,  # Same Z₆ structure for leptons
            "description": "Z₆ hexagonal symmetry for leptons (PMNS)"
        },
        # Keep old hypotheses for comparison
        "H1_dirac_old": {"fractions": [1.0], "signs": [+1, -1], "k": kernel.k_gen, "description": "Old π/2 hypothesis (deprecated)"},
        "H2_majorana_old": {"fractions": [1.0, 0.5, 0.0], "signs": [+1, -1], "k": kernel.k_gen, "description": "Old π/2 variants (deprecated)"},
    }

def evaluate_phase_hypothesis(delta_obs_rad: float, k: float, fractions, signs) -> Dict[str, Any]:
    """
    Finds the discrete (f,σ) minimizing |delta_obs - σ f k| on the circle.
    Returns the best discrete prediction and circular error in degrees.
    """
    def circ_err(a, b):
        # circular absolute difference in [-π,π]
        d = np.arctan2(np.sin(a-b), np.cos(a-b))
        return abs(d)

    best = None
    for f in fractions:
        for s in signs:
            pred = s * f * k
            err = circ_err(delta_obs_rad, pred)
            rec = {"frac": f, "sign": int(s), "pred_rad": float(pred), "err_rad": float(err)}
            if (best is None) or (err < best["err_rad"]):
                best = rec
    
    # Ensure we always return a valid dictionary
    if best is None:
        # Fallback if fractions or signs are empty
        best = {"frac": 1.0, "sign": 1, "pred_rad": 0.0, "err_rad": float('inf')}
    
    best["err_deg"] = float(np.degrees(best["err_rad"]))
    return best

# ---------------------------------------------------------------------
#                Leptogenesis proxy from M_eff (dimensionless)
# ---------------------------------------------------------------------

def leptogenesis_proxy(M_eff: np.ndarray, U_pmns: Optional[np.ndarray]=None) -> Dict[str, float]:
    """
    Dimensionless proxy:
      1) Takagi(M_eff) -> U_ν, m_i
      2) J_PMNS from U_PMNS or U_ℓ† U_ν if U_pmns is omitted (we can only report m-structure)
      3) 𝓗 = (Δ31 Δ21 Δ32) / (Σ m_i)^3  (scale-free hierarchy measure, ≥ 0)
      4) J_ℓ_eff = |J_PMNS| · 𝓗  (if U_pmns provided), else just 𝓗
    Returns {m1,m2,m3, H, J_eff (optional)}
    """
    U_nu, m = takagi_unitary(M_eff)
    m = np.sort(m)  # ascending
    dm21, dm31, dm32 = (m[1]-m[0]), (m[2]-m[0]), (m[2]-m[1])
    denom = (m.sum() + 1e-18)**3
    H = max(0.0, (dm31*dm21*dm32) / denom)  # ≥ 0

    out = {"m1": float(m[0]), "m2": float(m[1]), "m3": float(m[2]), "H": float(H)}

    if U_pmns is not None:
        Jl = abs(jarlskog_from_unitary(U_pmns))
        out["J_pmns"] = float(Jl)
        out["J_eff"]  = float(Jl * H)
    return out

# ---------------------------------------------------------------------
#                       Experiment wrapper (Lab)
# ---------------------------------------------------------------------

from ..core.registry import register_experiment
from .base import Experiment

@register_experiment("ugp_cp_asymmetry_probe")
class UGPCPAsymmetryProbe(Experiment):
    """
    UGP CP Probe:
    - Consumes mixing matrices (or angles), and M_eff if available.
    - Computes Jarlskog invariants, δ phases, UGP-phase discrete tests.
    - Reports a leptogenesis proxy (dimensionless) from M_eff.
    """

    def __init__(self, config: Dict[str, Any], root: Path):
        super().__init__(config, root)
        opts = config.get("options", {})
        kern = opts.get("kernel", {})
        self.kernel = UGPPhaseKernel(
            phi  = float(kern.get("phi",  (1.0 + 5.0**0.5)/2.0)),
            k_gen= float(kern.get("k_gen", np.pi/2.0))
        )
        self.inputs_cfg = opts.get("inputs", {})
        self.phase_cfg  = opts.get("ugp_phase_tests", {})
        self.producer: Optional[Callable[[], Dict[str, Any]]] = None

    def tasks(self) -> list[str]:
        return ["cp_probe"]

    # Optional: allow injection of a producer callable
    def set_producer(self, producer: Callable[[], Dict[str, Any]]) -> None:
        self.producer = producer

    def _get_inputs(self) -> Dict[str, Any]:
        if self.producer:
            data = self.producer()
        else:
            data = {}

        # config-level matrices can override or fill missing
        for key in ("V_ckm", "U_pmns", "M_eff"):
            if key in self.inputs_cfg and self.inputs_cfg[key] is not None:
                data[key] = np.array(self.inputs_cfg[key], dtype=complex)

        # angle fallback (deg)
        data.setdefault("angles_ckm", None)
        data.setdefault("angles_pmns", None)
        return data

    def run_task(self, task_id: str) -> Dict[str, Any]:
        if task_id != "cp_probe":
            raise ValueError(f"Unknown task: {task_id}")

        data = self._get_inputs()

        # 1) Build or extract unitary matrices
        V = data.get("V_ckm", None)
        U = data.get("U_pmns", None)

        # If angles only are provided (rare), you can build toy unitaries here if desired.
        # For now, we just require U,V or angles (for δ only via J formula).

        # 2) CKM observables
        ckm = {}
        if V is not None:
            ang_ckm = angles_from_unitary(V)
            Jq = jarlskog_from_unitary(V)
            δq = delta_from_J_and_angles(Jq, ang_ckm)
            ckm = {
                "angles_deg": ang_ckm,
                "Jarlskog": Jq,
                "delta_rad": δq,
                "delta_deg": float(np.degrees(δq))
            }
        elif data.get("angles_ckm", None):
            ang_ckm = data["angles_ckm"]
            # If no V, we only report δ via J formula is impossible; skip Jq
            ckm = {"angles_deg": ang_ckm}

        # 3) PMNS observables
        pmns = {}
        if U is not None:
            ang_pmns = angles_from_unitary(U)
            Jl = jarlskog_from_unitary(U)
            δl = delta_from_J_and_angles(Jl, ang_pmns)
            pmns = {
                "angles_deg": ang_pmns,
                "Jarlskog": Jl,
                "delta_rad": δl,
                "delta_deg": float(np.degrees(δl))
            }
        elif data.get("angles_pmns", None):
            ang_pmns = data["angles_pmns"]
            pmns = {"angles_deg": ang_pmns}

        # 4) UGP-phase discrete tests (no fitting)
        phase_tests = {}
        if ckm.get("delta_rad", None) is not None:
            H1 = ugp_phase_hypotheses(self.kernel)["H1_dirac"]
            best = evaluate_phase_hypothesis(ckm["delta_rad"], H1["k"], H1["fractions"], H1["signs"])
            phase_tests["H1_dirac"] = best

        if pmns.get("delta_rad", None) is not None:
            cfg = self.phase_cfg
            fracs = cfg.get("majorana_phase_fraction", [1.0, 0.5, 0.0])
            signs = cfg.get("signs", [+1, -1])
            best = evaluate_phase_hypothesis(pmns["delta_rad"], self.kernel.k_gen, fracs, signs)
            phase_tests["H2_majorana"] = best

        # 5) Leptogenesis proxy (dimensionless)
        lep = {}
        if data.get("M_eff", None) is not None:
            lep = leptogenesis_proxy(data["M_eff"], U_pmns=U)

        # === artifact writing ===
        try:
            from ugp_discovery_lab.tools.cp_summary_writer import write_both
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_dir = f"results/cp_probe_{timestamp}"
            paths = write_both(results_dir, {
                "kernel": {"phi": self.kernel.phi, "k_gen": self.kernel.k_gen},
                "ckm": ckm, "pmns": pmns,
                "phase_tests": phase_tests,
                "leptogenesis_proxy": lep
            })
        except Exception as _e:
            paths = {}

        return {
            "status": "success",
            "kernel": {"phi": self.kernel.phi, "k_gen": self.kernel.k_gen},
            "ckm": ckm,
            "pmns": pmns,
            "phase_tests": phase_tests,
            "leptogenesis_proxy": lep,
            "artifacts": paths
        }
    
    def summarize(self, results: list[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize multiple CP asymmetry probe results."""
        if not results:
            return {"status": "no_results"}
        
        # Aggregate results
        summary = {
            "total_runs": len(results),
            "successful_runs": sum(1 for r in results if r.get("status") == "success"),
            "kernel_analysis": {},
            "ckm_analysis": {},
            "pmns_analysis": {},
            "phase_test_analysis": {},
            "leptogenesis_analysis": {}
        }
        
        # Analyze CKM results
        ckm_deltas = []
        ckm_jarlskog = []
        for result in results:
            if result.get("ckm", {}).get("delta_deg") is not None:
                ckm_deltas.append(result["ckm"]["delta_deg"])
            if result.get("ckm", {}).get("Jarlskog") is not None:
                ckm_jarlskog.append(result["ckm"]["Jarlskog"])
        
        if ckm_deltas:
            summary["ckm_analysis"] = {
                "delta_mean": float(np.mean(ckm_deltas)),
                "delta_std": float(np.std(ckm_deltas)),
                "delta_range": [float(np.min(ckm_deltas)), float(np.max(ckm_deltas))]
            }
        
        if ckm_jarlskog:
            summary["ckm_analysis"]["jarlskog_mean"] = float(np.mean(ckm_jarlskog))
            summary["ckm_analysis"]["jarlskog_std"] = float(np.std(ckm_jarlskog))
        
        # Analyze PMNS results
        pmns_deltas = []
        pmns_jarlskog = []
        for result in results:
            if result.get("pmns", {}).get("delta_deg") is not None:
                pmns_deltas.append(result["pmns"]["delta_deg"])
            if result.get("pmns", {}).get("Jarlskog") is not None:
                pmns_jarlskog.append(result["pmns"]["Jarlskog"])
        
        if pmns_deltas:
            summary["pmns_analysis"] = {
                "delta_mean": float(np.mean(pmns_deltas)),
                "delta_std": float(np.std(pmns_deltas)),
                "delta_range": [float(np.min(pmns_deltas)), float(np.max(pmns_deltas))]
            }
        
        if pmns_jarlskog:
            summary["pmns_analysis"]["jarlskog_mean"] = float(np.mean(pmns_jarlskog))
            summary["pmns_analysis"]["jarlskog_std"] = float(np.std(pmns_jarlskog))
        
        # Analyze phase test results
        h1_errors = []
        h2_errors = []
        for result in results:
            phase_tests = result.get("phase_tests", {})
            if "H1_dirac" in phase_tests:
                h1_errors.append(phase_tests["H1_dirac"]["err_deg"])
            if "H2_majorana" in phase_tests:
                h2_errors.append(phase_tests["H2_majorana"]["err_deg"])
        
        if h1_errors:
            summary["phase_test_analysis"]["H1_dirac"] = {
                "error_mean": float(np.mean(h1_errors)),
                "error_std": float(np.std(h1_errors)),
                "best_error": float(np.min(h1_errors))
            }
        
        if h2_errors:
            summary["phase_test_analysis"]["H2_majorana"] = {
                "error_mean": float(np.mean(h2_errors)),
                "error_std": float(np.std(h2_errors)),
                "best_error": float(np.min(h2_errors))
            }
        
        # Analyze leptogenesis proxy
        j_eff_values = []
        for result in results:
            lep = result.get("leptogenesis_proxy", {})
            if "J_eff" in lep:
                j_eff_values.append(lep["J_eff"])
        
        if j_eff_values:
            summary["leptogenesis_analysis"] = {
                "J_eff_mean": float(np.mean(j_eff_values)),
                "J_eff_std": float(np.std(j_eff_values)),
                "J_eff_range": [float(np.min(j_eff_values)), float(np.max(j_eff_values))]
            }
        
        return summary
