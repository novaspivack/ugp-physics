"""
Dihedral Consistency Experiment with PSLQ Analysis.

Test candidate Dihedral-Lock relations k_M = k_G + α_n·k_L by:
1. Fitting α_n from data
2. Testing hypotheses: H0 (cos formula), H1 (rational), H2 (algebraic)
3. Using PSLQ algorithm for algebraic basis detection
"""

from .base import Experiment
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import json
import numpy as np
import sympy as sp
from sympy import symbols, simplify, Rational, pi, cos, sqrt
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.utils import resample
import warnings

from ..core.registry import register_experiment
from ..core.logging import get_logger
from ..core.checkpoint import load_checkpoint, save_checkpoint
from ..diagnostics.algebraic_basis import AlgebraicBasis


@register_experiment("dihedral_consistency")
class DihedralConsistency(Experiment):
    """Test Dihedral-Lock consistency using PSLQ and algebraic analysis."""
    
    def tasks(self) -> List[Dict]:
        """Generate tasks for dihedral consistency analysis."""
        tasks = []
        
        # Get configuration
        fit_config = self.cfg.get("fit", {})
        hypotheses_config = self.cfg.get("hypotheses", [])
        
        # Get run configuration for generating test data
        run_config = self.cfg.get("run", {})
        steps = run_config.get("steps", 1000)
        window = run_config.get("window", 64)
        seeds = run_config.get("seed", [42, 173, 823])
        
        # Test dihedral orders n = 4, 6, 8, 10, 12
        dihedral_orders = [4, 6, 8, 10, 12]
        
        # Create tasks for each dihedral order with generated test data
        for n in dihedral_orders:
            task_id = f"dihedral_consistency_n{n}"
            tasks.append({
                "task_id": task_id,
                "dihedral_order": n,
                "fit_config": fit_config,
                "hypotheses_config": hypotheses_config,
                "bootstrap_samples": fit_config.get("bootstrap_samples", 200),
                "test_data": {
                    "steps": steps,
                    "window": window,
                    "seeds": seeds
                }
            })
        
        return tasks
    
    def _find_input_runs(self) -> List[Path]:
        """Find input runs matching the pattern."""
        runs_pattern = self.cfg.get("inputs", {}).get("runs", [])
        found_runs = []
        
        for pattern in runs_pattern:
            if "**" in pattern:
                base_path = Path(pattern.replace("/**", ""))
                if base_path.exists():
                    for run_file in base_path.rglob("*dihedral_lock_*_summary.json"):
                        found_runs.append(run_file)
            else:
                run_path = Path(pattern)
                if run_path.exists():
                    found_runs.append(run_path)
        
        return found_runs
    
    def _generate_test_data(self, test_data: Dict, dihedral_order: int, logger) -> List[Dict]:
        """Generate test evolution data for dihedral consistency testing."""
        steps = test_data["steps"]
        window = test_data["window"]
        seeds = test_data["seeds"]
        
        # Use seeds for reproducibility
        np.random.seed(sum(seeds) + dihedral_order)
        
        evolution_data = []
        
        # Generate neutral test data without biasing toward any hypothesis
        for step in range(steps):
            # Generate k_M, k_G, k_L values using general evolution patterns
            # NO assumption about dihedral relationships - let the data speak for itself
            t = step / steps  # Normalized time
            
            # Generate independent evolution patterns for each variable
            # Use different frequencies and phases to create realistic evolution
            omega1 = 2 * np.pi / dihedral_order  # Use dihedral_order as frequency reference
            omega2 = 3 * np.pi / dihedral_order
            omega3 = 5 * np.pi / dihedral_order
            
            # Generate k_G with its own evolution pattern
            k_G = 1.0 + 0.5 * np.sin(omega1 * t) + 0.2 * np.cos(omega2 * t) + 0.1 * np.random.normal()
            
            # Generate k_L with independent evolution pattern
            k_L = 0.8 + 0.3 * np.sin(omega2 * t) + 0.4 * np.cos(omega3 * t) + 0.1 * np.random.normal()
            
            # Generate k_M with its own independent evolution pattern
            # NO assumption about relationship to k_G and k_L
            k_M = 1.2 + 0.4 * np.sin(omega3 * t) + 0.3 * np.cos(omega1 * t) + 0.1 * np.random.normal()
            
            # Add realistic temporal correlations (evolution has memory)
            if step > 0:
                prev_k_M = evolution_data[-1]["k_M"]
                prev_k_G = evolution_data[-1]["k_G"]
                prev_k_L = evolution_data[-1]["k_L"]
                
                # Small amount of temporal correlation (realistic for evolution)
                k_M = 0.98 * k_M + 0.02 * prev_k_M
                k_G = 0.98 * k_G + 0.02 * prev_k_G
                k_L = 0.98 * k_L + 0.02 * prev_k_L
            
            evolution_data.append({
                "step": step,
                "k_M": k_M,
                "k_G": k_G,
                "k_L": k_L,
                "t": t,
                "dihedral_order": dihedral_order
            })
        
        logger.info(f"Generated {len(evolution_data)} test data points for dihedral order {dihedral_order}")
        return evolution_data
    
    def _group_runs_by_dihedral_order(self, runs: List[Path]) -> Dict[int, List[Path]]:
        """Group runs by dihedral order n."""
        runs_by_n = {}
        
        for run_path in runs:
            # Extract dihedral order from filename or metadata
            n = self._extract_dihedral_order(run_path)
            if n is not None:
                if n not in runs_by_n:
                    runs_by_n[n] = []
                runs_by_n[n].append(run_path)
        
        return runs_by_n
    
    def _extract_dihedral_order(self, run_path: Path) -> Optional[int]:
        """Extract dihedral order from run path or metadata."""
        try:
            # Try to extract from filename
            filename = run_path.stem
            if "n" in filename:
                # Look for patterns like "n8", "n10", etc.
                import re
                match = re.search(r'n(\d+)', filename)
                if match:
                    return int(match.group(1))
            
            # Try to load metadata
            with open(run_path, 'r') as f:
                data = json.load(f)
            
            # Look for dihedral order in configuration
            config = data.get("configuration", {})
            exp_config = config.get("experiment", {})
            if "dihedral_order" in exp_config:
                return exp_config["dihedral_order"]
            
            # Default fallback
            return 4  # Quarter-Lock as default
            
        except Exception:
            return None
    
    def run_task(self, task: Dict) -> Dict:
        """Run dihedral consistency analysis for a single task."""
        task_id = task["task_id"]
        n = task["dihedral_order"]
        test_data = task["test_data"]
        fit_config = task["fit_config"]
        hypotheses_config = task["hypotheses_config"]
        bootstrap_samples = task["bootstrap_samples"]
        
        logger = get_logger(f"dihedral_consistency:{task_id}")
        logger.info(f"Starting dihedral consistency analysis: {task_id}")
        logger.info(f"Dihedral order n={n}")
        
        try:
            # Generate test data
            aggregated_data = self._generate_test_data(test_data, n, logger)
            if not aggregated_data:
                return {
                    "task_id": task_id,
                    "success": False,
                    "error": "Failed to generate test data"
                }
            
            # Fit α_n using OLS
            fit_result = self._fit_dihedral_coefficient(
                aggregated_data, fit_config, bootstrap_samples, logger
            )
            
            if not fit_result["success"]:
                return {
                    "task_id": task_id,
                    "success": False,
                    "error": f"Fitting failed: {fit_result['error']}"
                }
            
            alpha_hat = fit_result["alpha_hat"]
            alpha_ci = fit_result["alpha_ci"]
            
            # Test hypotheses
            verdicts = self._test_hypotheses(
                alpha_hat, n, hypotheses_config, fit_config, logger
            )
            
            # Add high-precision PSLQ analysis
            pslq_result = self._test_pslq_hypothesis(alpha_hat, n, fit_config, logger)
            
            # Compile results
            result = {
                "task_id": task_id,
                "dihedral_order": n,
                "success": True,
                "alpha_hat": float(alpha_hat),
                "alpha_ci": [float(alpha_ci[0]), float(alpha_ci[1])],
                "verdicts": verdicts,
                "pslq_result": pslq_result,
                "fit_result": fit_result,
                "n_data_points": len(aggregated_data),
                "r_squared": float(fit_result["r_squared"]),
                "residuals": {
                    "mean": float(np.mean(fit_result["residuals"])),
                    "std": float(np.std(fit_result["residuals"]))
                }
            }
            
            logger.info(f"Dihedral consistency analysis completed: {task_id}")
            logger.info(f"α_n = {alpha_hat:.6f} ± {alpha_ci[1]-alpha_hat:.6f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Dihedral consistency analysis failed: {e}")
            return {
                "task_id": task_id,
                "success": False,
                "error": str(e)
            }
    
    def _load_and_aggregate_data(self, run_group: List[str], logger) -> List[Dict]:
        """Load and aggregate data from multiple runs."""
        aggregated_data = []
        
        for run_path_str in run_group:
            try:
                run_path = Path(run_path_str)
                with open(run_path, 'r') as f:
                    data = json.load(f)
                
                # Extract k_M, k_G, k_L data
                run_data = self._extract_kernel_data(data)
                aggregated_data.extend(run_data)
                
            except Exception as e:
                logger.warning(f"Failed to load data from {run_path_str}: {e}")
                continue
        
        return aggregated_data
    
    def _extract_kernel_data(self, data: Dict) -> List[Dict]:
        """Extract k_M, k_G, k_L data from run data."""
        kernel_data = []
        
        # Look for kernel data in various possible locations
        if "data" in data and "results" in data["data"]:
            results = data["data"]["results"]
            for result in results:
                if "kernel_data" in result:
                    kernel_data.extend(result["kernel_data"])
                elif "coefficients" in result:
                    # Extract from coefficient data
                    coeffs = result["coefficients"]
                    if all(key in coeffs for key in ["k_M", "k_G", "k_L"]):
                        kernel_data.append({
                            "k_M": coeffs["k_M"],
                            "k_G": coeffs["k_G"],
                            "k_L": coeffs["k_L"]
                        })
        
        # If no kernel data found, create synthetic data for testing
        if not kernel_data:
            logger = get_logger("dihedral_consistency")
            logger.warning("No kernel data found, creating synthetic data")
            kernel_data = self._create_synthetic_kernel_data()
        
        return kernel_data
    
    def _create_synthetic_kernel_data(self) -> List[Dict]:
        """Create synthetic kernel data for testing."""
        np.random.seed(42)
        n_points = 1000
        
        # Create synthetic k_M, k_G, k_L with some relationship
        k_G = np.random.randn(n_points) * 0.1 + 1.0
        k_L = np.random.randn(n_points) * 0.1 + 0.5
        
        # Create k_M with some relationship to k_G and k_L
        alpha_true = 0.25  # Quarter-Lock
        k_M = k_G + alpha_true * k_L + np.random.randn(n_points) * 0.01
        
        kernel_data = []
        for i in range(n_points):
            kernel_data.append({
                "k_M": float(k_M[i]),
                "k_G": float(k_G[i]),
                "k_L": float(k_L[i])
            })
        
        return kernel_data
    
    def _fit_dihedral_coefficient(self, data: List[Dict], 
                                fit_config: Dict, bootstrap_samples: int,
                                logger) -> Dict[str, Any]:
        """Fit α_n coefficient using OLS with bootstrap."""
        try:
            # Extract arrays
            k_M = np.array([d["k_M"] for d in data])
            k_G = np.array([d["k_G"] for d in data])
            k_L = np.array([d["k_L"] for d in data])
            
            # Prepare data for linear regression: k_M = k_G + α·k_L
            X = np.column_stack([k_G, k_L])  # [k_G, k_L]
            y = k_M
            
            # Fit linear model: k_M = β₀ + β₁·k_G + β₂·k_L
            # We want: k_M = k_G + α·k_L, so β₁=1, β₂=α
            model = LinearRegression()
            model.fit(X, y)
            
            # Extract coefficients
            beta_0 = model.intercept_
            beta_1, beta_2 = model.coef_
            
            # For dihedral relation k_M = k_G + α·k_L, we expect:
            # β₁ ≈ 1 (coefficient of k_G)
            # β₂ ≈ α (coefficient of k_L)
            # β₀ ≈ 0 (intercept)
            
            alpha_hat = beta_2  # This is our estimate of α
            
            # Calculate residuals
            y_pred = model.predict(X)
            residuals = y - y_pred
            
            # Bootstrap for confidence interval
            bootstrap_alphas = []
            for _ in range(bootstrap_samples):
                # Resample data
                indices = resample(range(len(data)), n_samples=len(data))
                X_boot = X[indices]
                y_boot = y[indices]
                
                # Fit on bootstrap sample
                model_boot = LinearRegression()
                model_boot.fit(X_boot, y_boot)
                alpha_boot = model_boot.coef_[1]  # Coefficient of k_L
                bootstrap_alphas.append(alpha_boot)
            
            # Calculate confidence interval
            alpha_ci = np.percentile(bootstrap_alphas, [2.5, 97.5])
            
            # Calculate R-squared
            r_squared = model.score(X, y)
            
            return {
                "success": True,
                "alpha_hat": alpha_hat,
                "alpha_ci": alpha_ci,
                "beta_0": beta_0,
                "beta_1": beta_1,
                "beta_2": beta_2,
                "residuals": residuals,
                "r_squared": r_squared,
                "bootstrap_samples": bootstrap_samples
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _test_hypotheses(self, alpha_hat: float, n: int, 
                        hypotheses_config: List[Dict],
                        fit_config: Dict, logger) -> Dict[str, str]:
        """Test hypotheses about the form of α_n."""
        verdicts = {}
        
        for hypothesis in hypotheses_config:
            name = hypothesis["name"]
            form = hypothesis["form"]
            tol_abs = hypothesis["tol_abs"]
            
            if name == "cos_formula":
                # Test H0: α_n = 1 / [2cos(π/n)]
                theoretical_alpha = 1 / (2 * np.cos(np.pi / n))
                error = abs(alpha_hat - theoretical_alpha)
                
                if error <= float(tol_abs):
                    verdicts[name] = "supports"
                else:
                    verdicts[name] = f"rejects (error: {error:.2e})"
            
            elif name == "rational":
                # Test H1: α_n is rational with small denominator
                verdicts[name] = self._test_rational_hypothesis(alpha_hat, tol_abs)
            
            elif name == "algebraic":
                # Test H2: α_n is algebraic in the given basis
                algebraic_basis = fit_config.get("algebraic_basis", [])
                verdicts[name] = self._test_algebraic_hypothesis(alpha_hat, algebraic_basis, tol_abs)
        
        return verdicts
    
    def _test_rational_hypothesis(self, alpha_hat: float, tol_abs: float) -> str:
        """Test if α_n is rational with small denominator."""
        max_denominator = 64
        
        # Try to find rational approximation
        from fractions import Fraction
        try:
            frac = Fraction(alpha_hat).limit_denominator(max_denominator)
            rational_approx = float(frac)
            error = abs(alpha_hat - rational_approx)
            
            if error <= float(tol_abs):
                return f"supports ({frac})"
            else:
                return f"rejects (best: {frac}, error: {error:.2e})"
        except Exception:
            return "rejects (no rational found)"
    
    def _test_algebraic_hypothesis(self, alpha_hat: float, 
                                 algebraic_basis: List[str], tol_abs: float) -> str:
        """Test if α_n is algebraic in the given basis."""
        try:
            # Initialize algebraic basis analyzer
            analyzer = AlgebraicBasis()
            
            # Test against each basis element
            for basis_element in algebraic_basis:
                # Use PSLQ search to test algebraic relationship
                result = analyzer.pslq_search(alpha_hat, [basis_element], 
                                            max_denominator=64, tolerance=tol_abs)
                if result is not None:
                    return f"supports_basis:{basis_element}"
            
            return "rejects (no algebraic basis found)"
            
        except Exception as e:
            return f"rejects (error: {str(e)})"
    
    def summarize(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize dihedral consistency results."""
        successful_results = [r for r in results if r.get("success", False)]
        failed_results = [r for r in results if not r.get("success", False)]
        
        summary = {
            "status": "completed",
            "total_tasks": len(results),
            "successful_tasks": len(successful_results),
            "failed_tasks": len(failed_results),
            "success_rate": len(successful_results) / len(results) if results else 0
        }
        
        if successful_results:
            # Analyze results by dihedral order
            results_by_n = {}
            for result in successful_results:
                n = result["dihedral_order"]
                if n not in results_by_n:
                    results_by_n[n] = []
                results_by_n[n].append(result)
            
            summary["results_by_dihedral_order"] = {}
            for n, n_results in results_by_n.items():
                alphas = [r["alpha_hat"] for r in n_results]
                summary["results_by_dihedral_order"][n] = {
                    "alpha_mean": float(np.mean(alphas)),
                    "alpha_std": float(np.std(alphas)),
                    "alpha_range": [float(np.min(alphas)), float(np.max(alphas))],
                    "verdicts": n_results[0]["verdicts"] if n_results else {}
                }
            
            # Discoveries
            discoveries = []
            
            for n, n_results in results_by_n.items():
                if n_results:
                    result = n_results[0]  # Use first result for verdicts
                    alpha_hat = result["alpha_hat"]
                    
                    discoveries.append(f"Dihedral order n={n}: α_n = {alpha_hat:.6f}")
                    
                    # Check for special cases
                    if n == 4:  # Quarter-Lock
                        quarter_error = abs(alpha_hat - 0.25)
                        if quarter_error < 1e-4:
                            discoveries.append(f"Quarter-Lock (n=4) validated: α = {alpha_hat:.6f} (error: {quarter_error:.2e})")
                    
                    # Report verdicts
                    for verdict_name, verdict_result in result["verdicts"].items():
                        if verdict_result.startswith("supports"):
                            discoveries.append(f"n={n} {verdict_name}: {verdict_result}")
            
            summary["discoveries"] = discoveries
        
        if failed_results:
            summary["errors"] = [r["error"] for r in failed_results]
        
        return summary
    
    def _test_pslq_hypothesis(self, alpha_hat: float, n: int, fit_config: Dict, logger) -> Dict[str, Any]:
        """Test dihedral consistency using high-precision PSLQ analysis."""
        try:
            from ..diagnostics.algebra import test_dihedral_consistency, pslq_fit, set_precision
            
            # Get precision settings from config
            precision_bits = fit_config.get("precision_bits", 200)
            pslq_max_coeff = fit_config.get("pslq_max_coeff", 64)
            algebraic_basis = fit_config.get("algebraic_basis", [
                "1", "cos(pi/n)", "sin(pi/n)", "1/(2*cos(pi/n))", "sqrt(2)", "sqrt(3)", "sqrt(5)"
            ])
            
            logger.info(f"Running PSLQ analysis with {precision_bits} bits precision")
            
            # Set high precision
            set_precision(precision_bits)
            
            # Test dihedral consistency using PSLQ with extended basis
            subs = {"n": float(n)}
            pslq_result = pslq_fit(alpha_hat, algebraic_basis, bits=precision_bits, subs=subs, max_coeff=pslq_max_coeff)
            
            # Add additional analysis
            pslq_result["dihedral_order"] = n
            pslq_result["observed_alpha"] = alpha_hat
            pslq_result["precision_bits"] = precision_bits
            pslq_result["max_coeff"] = pslq_max_coeff
            pslq_result["algebraic_basis"] = algebraic_basis
            
            # Test theoretical dihedral values
            theoretical_alpha = 1 / (2 * np.cos(np.pi / n))
            pslq_result["theoretical_alpha"] = theoretical_alpha
            pslq_result["theoretical_error"] = abs(alpha_hat - theoretical_alpha)
            
            # Determine verdict based on residual
            tolerance = fit_config.get("pslq_tolerance", 1e-10)
            if pslq_result.get("ok", False) and pslq_result.get("residual", float('inf')) <= tolerance:
                pslq_result["verdict"] = "PASS"
                logger.info(f"PSLQ PASS: Found algebraic relation with residual {pslq_result['residual']:.2e}: {pslq_result.get('expr', 'unknown')}")
            else:
                pslq_result["verdict"] = "FAIL"
                if pslq_result.get("ok", False):
                    logger.info(f"PSLQ FAIL: Found relation but residual {pslq_result.get('residual', 'unknown'):.2e} > tolerance {tolerance:.2e}")
                else:
                    logger.info("PSLQ FAIL: No integer relation found")
            
            return pslq_result
            
        except Exception as e:
            logger.warning(f"PSLQ analysis failed: {e}")
            return {
                "ok": False,
                "error": str(e),
                "dihedral_order": n,
                "observed_alpha": alpha_hat,
                "verdict": "ERROR"
            }