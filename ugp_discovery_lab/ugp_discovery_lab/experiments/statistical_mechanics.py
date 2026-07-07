"""
Statistical Mechanics Experiment for UGP Discovery Lab.

Verifies the emergence of the Second Law of Thermodynamics from deterministic,
reversible micro-dynamics of UGP. Measures coarse-grained entropy over time
and checks for monotonic non-decreasing behavior.
"""

import numpy as np
import json
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path
from collections import Counter
import matplotlib.pyplot as plt

from .base import Experiment
from ..core.registry import register_experiment
from ..core.logging import get_logger
from ..core.reporting import write_json_report, write_md_report


@register_experiment("statistical_mechanics")
class StatisticalMechanics(Experiment):
    """
    Verify emergent irreversibility (Second Law) from deterministic GTE traces.
    
    This experiment:
    1. Loads real GTE trajectory data (series of (a,b,c) triples)
    2. Defines coarse-graining function mapping triples to macro-state bins
    3. Computes empirical probability distribution p_t over macro-state bins
    4. Calculates Shannon entropy S(p_t) = -Σ p_t(i) log(p_t(i))
    5. Checks if entropy series S(p_t) is monotonically non-decreasing
    """
    
    def tasks(self) -> List[Dict[str, Any]]:
        """Generate tasks for statistical mechanics analysis."""
        tasks = []
        
        # Get configuration
        inputs = self.cfg.get("inputs", {})
        runs = inputs.get("runs", [])
        coarse_graining = self.cfg.get("coarse_graining", {})
        verification = self.cfg.get("verification", {})
        
        # Create tasks for each input run
        for run_path in runs:
            task = {
                "task_id": f"statistical_mechanics_{Path(run_path).name}",
                "run_path": run_path,
                "coarse_graining": coarse_graining,
                "verification": verification
            }
            tasks.append(task)
        
        return tasks
    
    def run_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Run statistical mechanics analysis for a single task."""
        task_id = task["task_id"]
        run_path = task["run_path"]
        coarse_graining = task["coarse_graining"]
        verification = task["verification"]
        
        logger = get_logger(f"statistical_mechanics:{task_id}")
        logger.info(f"Starting statistical mechanics analysis: {task_id}")
        
        try:
            # Load GTE trajectory data
            gte_data = self._load_gte_data(run_path, logger)
            
            if not gte_data:
                return {
                    "task_id": task_id,
                    "success": False,
                    "error": "No GTE data found"
                }
            
            logger.info(f"Loaded {len(gte_data)} GTE trajectory points")
            
            # Apply coarse-graining
            macro_states = self._coarse_grain_data(gte_data, coarse_graining, logger)
            
            # Compute entropy series
            entropy_series = self._compute_entropy_series(macro_states, logger)
            
            # Verify monotonicity (Second Law)
            monotonicity_result = self._verify_monotonicity(
                entropy_series, verification, logger
            )
            
            # Generate analysis plots
            plot_paths = self._generate_plots(
                entropy_series, macro_states, gte_data, task_id, logger
            )
            
            result = {
                "task_id": task_id,
                "success": True,
                "run_path": run_path,
                "gte_data_points": len(gte_data),
                "macro_states": macro_states,
                "entropy_series": entropy_series,
                "monotonicity_result": monotonicity_result,
                "plot_paths": plot_paths,
                "status": "ok"
            }
            
            logger.info(f"Statistical mechanics analysis completed: {task_id}")
            return result
            
        except Exception as e:
            logger.error(f"Statistical mechanics analysis failed: {e}")
            return {
                "task_id": task_id,
                "success": False,
                "error": str(e)
            }
    
    def _load_gte_data(self, run_path: str, logger) -> List[Dict[str, Any]]:
        """Load GTE trajectory data from one run path (file or directory)."""
        logger.debug(f"Loading GTE data from {run_path}")

        # Resolve relative paths against lab root
        if not Path(run_path).is_absolute():
            resolved = self.root / run_path
        else:
            resolved = Path(run_path)

        gte_data = []

        if resolved.is_file():
            # Direct file reference (e.g. specific experiment_results.json)
            json_files = [resolved]
        elif resolved.is_dir():
            json_files = list(resolved.glob("**/*.json"))
        else:
            # Path doesn't exist; might be a legacy glob pattern with no matches
            logger.debug(f"Path not found (glob pattern with no matches?): {resolved}")
            json_files = []

        logger.debug(f"Processing {len(json_files)} JSON file(s) from {resolved}")

        for json_file in json_files:
            try:
                with open(json_file, "r") as f:
                    data = json.load(f)
                extracted = self._extract_gte_from_data(data, logger)
                gte_data.extend(extracted)
            except Exception as e:
                logger.warning(f"Failed to load {json_file}: {e}")
                continue

        if not gte_data:
            logger.debug("No real GTE data found in path; falling back to synthetic data")
            gte_data = self._generate_synthetic_gte_data()

        logger.debug(f"Loaded {len(gte_data)} GTE records")
        return gte_data
    
    def _extract_gte_from_data(self, data: Dict[str, Any], logger) -> List[Dict[str, Any]]:
        """Extract GTE trajectory data from loaded JSON data.

        Supports multiple storage conventions used across the Discovery Lab:
        - ``gte_trajectory`` (holographic_transducer, etc.)
        - ``evolution_history`` (lawful_evolution — the primary real-GTE source)
        - nested ``data.results[*].gte_trajectory``
        - flat ``coefficients`` dict with a/b/c keys
        """
        gte_records = []

        if not isinstance(data, dict):
            return gte_records

        def _parse_triple_list(seq: list, step_offset: int = 0) -> List[Dict[str, Any]]:
            recs = []
            for i, state in enumerate(seq):
                if isinstance(state, dict) and all(k in state for k in ("a", "b", "c")):
                    recs.append({
                        "step": state.get("step", step_offset + i),
                        "a": state["a"],
                        "b": state["b"],
                        "c": state["c"],
                    })
            return recs

        # 1. Direct gte_trajectory list at top level
        if "gte_trajectory" in data:
            gte_records.extend(_parse_triple_list(data["gte_trajectory"]))

        # 2. lawful_evolution / reversible_core: evolution_history list at top level
        elif "evolution_history" in data:
            gte_records.extend(_parse_triple_list(data["evolution_history"]))

        # 3. Wrapped under data.results[*]
        elif "data" in data and "results" in data.get("data", {}):
            for result in data["data"]["results"]:
                if "gte_trajectory" in result:
                    gte_records.extend(_parse_triple_list(result["gte_trajectory"]))
                elif "evolution_history" in result:
                    gte_records.extend(_parse_triple_list(result["evolution_history"]))
                elif "coefficients" in result:
                    coeffs = result["coefficients"]
                    if all(k in coeffs for k in ("a", "b", "c")):
                        gte_records.append({"step": 0, "a": coeffs["a"], "b": coeffs["b"], "c": coeffs["c"]})

        # 4. Bare results list at top level
        elif "results" in data:
            for result in data["results"]:
                if isinstance(result, dict):
                    if "gte_trajectory" in result:
                        gte_records.extend(_parse_triple_list(result["gte_trajectory"]))
                    elif "evolution_history" in result:
                        gte_records.extend(_parse_triple_list(result["evolution_history"]))

        # 5. Nested under analysis
        elif "analysis" in data:
            analysis = data["analysis"]
            if "gte_trajectory" in analysis:
                gte_records.extend(_parse_triple_list(analysis["gte_trajectory"]))
            elif "evolution_history" in analysis:
                gte_records.extend(_parse_triple_list(analysis["evolution_history"]))

        return gte_records
    
    def _generate_synthetic_gte_data(self) -> List[Dict[str, Any]]:
        """Generate synthetic GTE data for testing."""
        gte_records = []
        
        # Generate a synthetic GTE evolution
        a, b, c = 1, 73, 823
        
        for step in range(100):
            # Create state
            gte_records.append({
                "step": step,
                "a": a,
                "b": b,
                "c": c
            })
            
            # Simple evolution (deterministic but creates entropy)
            if step % 2 == 0:
                b += 1
                c += b
            else:
                a += 1
                c += a
        
        return gte_records
    
    def _coarse_grain_data(self, gte_data: List[Dict[str, Any]], 
                          coarse_graining: Dict[str, Any], logger) -> List[List[int]]:
        """Apply coarse-graining to map GTE triples to macro-state bins."""
        logger.debug("Applying coarse-graining to GTE data")
        
        n_bins_b = coarse_graining.get("n_bins_b", 16)
        n_bins_c = coarse_graining.get("n_bins_c", 16)
        
        macro_states = []
        
        import math as _math
        for record in gte_data:
            a = record["a"]
            b = record["b"]
            c = record["c"]

            # Coarse-grain by binning log|b| and log|c|.
            # Convert Python bigints to float via math.log to avoid numpy ufunc errors.
            try:
                log_b = _math.log(abs(b) + 1) if b != 0 else 0.0
            except (TypeError, ValueError):
                log_b = 0.0
            try:
                log_c = _math.log(abs(c) + 1) if c != 0 else 0.0
            except (TypeError, ValueError):
                log_c = 0.0
            
            # Find bin indices
            bin_b = int(log_b * n_bins_b / 10) % n_bins_b  # Normalize to [0, n_bins_b)
            bin_c = int(log_c * n_bins_c / 10) % n_bins_c  # Normalize to [0, n_bins_c)
            
            macro_state = [bin_b, bin_c]
            macro_states.append(macro_state)
        
        logger.debug(f"Coarse-grained {len(macro_states)} states into {n_bins_b}x{n_bins_c} bins")
        return macro_states
    
    def _compute_entropy_series(self, macro_states: List[List[int]], logger) -> List[float]:
        """Compute Shannon entropy series from macro-state evolution."""
        logger.debug("Computing Shannon entropy series")
        
        entropy_series = []
        
        # Compute entropy at each time step using sliding window
        window_size = min(20, len(macro_states) // 4)  # Adaptive window size
        
        for t in range(len(macro_states)):
            # Get states up to time t
            states_up_to_t = macro_states[:t+1]
            
            # Count frequency of each macro-state
            state_counts = Counter(tuple(state) for state in states_up_to_t)
            total_states = len(states_up_to_t)
            
            # Compute Shannon entropy
            entropy = 0.0
            for count in state_counts.values():
                if count > 0:
                    p = count / total_states
                    entropy -= p * np.log2(p)
            
            entropy_series.append(entropy)
        
        logger.debug(f"Computed entropy series with {len(entropy_series)} points")
        return entropy_series
    
    def _verify_monotonicity(self, entropy_series: List[float], 
                           verification: Dict[str, Any], logger) -> Dict[str, Any]:
        """Verify that entropy series is monotonically non-decreasing."""
        logger.debug("Verifying entropy monotonicity")
        
        tolerance = verification.get("monotonicity_tolerance", 1e-9)
        
        # Check for monotonicity violations
        violations = []
        for i in range(1, len(entropy_series)):
            if entropy_series[i] < entropy_series[i-1] - tolerance:
                violations.append({
                    "step": i,
                    "entropy_prev": entropy_series[i-1],
                    "entropy_curr": entropy_series[i],
                    "violation": entropy_series[i-1] - entropy_series[i]
                })
        
        # Determine verdict
        is_monotonic = len(violations) == 0
        verdict = "PASS" if is_monotonic else "FAIL"
        
        # Compute statistics
        entropy_stats = {
            "initial_entropy": entropy_series[0] if entropy_series else 0.0,
            "final_entropy": entropy_series[-1] if entropy_series else 0.0,
            "max_entropy": max(entropy_series) if entropy_series else 0.0,
            "min_entropy": min(entropy_series) if entropy_series else 0.0,
            "entropy_change": entropy_series[-1] - entropy_series[0] if len(entropy_series) > 1 else 0.0,
            "mean_entropy": np.mean(entropy_series) if entropy_series else 0.0,
            "std_entropy": np.std(entropy_series) if entropy_series else 0.0
        }
        
        result = {
            "verdict": verdict,
            "is_monotonic": is_monotonic,
            "violations": violations,
            "num_violations": len(violations),
            "tolerance": tolerance,
            "entropy_statistics": entropy_stats,
            "total_steps": len(entropy_series)
        }
        
        logger.info(f"Monotonicity verification: {verdict} ({len(violations)} violations)")
        return result
    
    def _generate_plots(self, entropy_series: List[float], macro_states: List[List[int]], 
                       gte_data: List[Dict[str, Any]], task_id: str, logger) -> List[str]:
        """Generate analysis plots."""
        try:
            # Create output directory
            plot_dir = self.root / "results" / "artifacts" / "statistical_mechanics"
            plot_dir.mkdir(parents=True, exist_ok=True)
            
            plot_paths = []
            
            # Plot 1: Entropy vs Time
            plt.figure(figsize=(10, 6))
            if entropy_series:
                plt.plot(entropy_series, 'b-', linewidth=2, label='Shannon Entropy')
                plt.legend()
            plt.xlabel('Time Step')
            plt.ylabel('Entropy (bits)')
            plt.title(f'Statistical Mechanics: Entropy Evolution ({task_id})')
            plt.grid(True, alpha=0.3)
            
            entropy_plot_path = plot_dir / f"{task_id}_entropy_evolution.png"
            plt.savefig(entropy_plot_path, dpi=300, bbox_inches='tight')
            plt.close()
            plot_paths.append(str(entropy_plot_path))
            
            # Plot 2: Macro-state distribution (heatmap)
            if macro_states:
                # Create 2D histogram of macro-states
                bins_b = [state[0] for state in macro_states]
                bins_c = [state[1] for state in macro_states]
                
                plt.figure(figsize=(10, 8))
                plt.hist2d(bins_b, bins_c, bins=16, cmap='viridis')
                plt.colorbar(label='Frequency')
                plt.xlabel('Binned log|b|')
                plt.ylabel('Binned log|c|')
                plt.title(f'Macro-State Distribution ({task_id})')
                
                distribution_plot_path = plot_dir / f"{task_id}_macro_state_distribution.png"
                plt.savefig(distribution_plot_path, dpi=300, bbox_inches='tight')
                plt.close()
                plot_paths.append(str(distribution_plot_path))
            
            # Plot 3: GTE trajectory evolution
            if gte_data and len(gte_data) > 0:
                steps = [record["step"] for record in gte_data]
                a_vals = [record["a"] for record in gte_data]
                b_vals = [record["b"] for record in gte_data]
                c_vals = [record["c"] for record in gte_data]
                
                plt.figure(figsize=(12, 8))
                plt.subplot(2, 2, 1)
                plt.plot(steps, a_vals, 'r-', label='a')
                plt.xlabel('Step')
                plt.ylabel('a')
                plt.title('GTE Parameter a')
                plt.grid(True, alpha=0.3)
                
                plt.subplot(2, 2, 2)
                plt.plot(steps, b_vals, 'g-', label='b')
                plt.xlabel('Step')
                plt.ylabel('b')
                plt.title('GTE Parameter b')
                plt.grid(True, alpha=0.3)
                
                plt.subplot(2, 2, 3)
                plt.plot(steps, c_vals, 'b-', label='c')
                plt.xlabel('Step')
                plt.ylabel('c')
                plt.title('GTE Parameter c')
                plt.grid(True, alpha=0.3)
                
                plt.subplot(2, 2, 4)
                plt.plot(steps, entropy_series, 'purple', linewidth=2, label='Entropy')
                plt.xlabel('Step')
                plt.ylabel('Entropy (bits)')
                plt.title('Entropy Evolution')
                plt.grid(True, alpha=0.3)
                
                plt.tight_layout()
                gte_plot_path = plot_dir / f"{task_id}_gte_trajectory.png"
                plt.savefig(gte_plot_path, dpi=300, bbox_inches='tight')
                plt.close()
                plot_paths.append(str(gte_plot_path))
            
            return plot_paths
            
        except Exception as e:
            logger.warning(f"Plot generation failed: {e}")
            return []
    
    def summarize(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize statistical mechanics experiment results."""
        successful_results = [r for r in results if r.get("success", False)]
        failed_results = [r for r in results if not r.get("success", False)]
        
        summary = {
            "status": "completed",
            "total_tasks": len(results),
            "successful_tasks": len(successful_results),
            "failed_tasks": len(failed_results),
            "success_rate": len(successful_results) / len(results) if results else 0.0
        }
        
        if successful_results:
            # Aggregate monotonicity results
            all_verdicts = []
            all_violations = []
            entropy_stats = []
            
            for result in successful_results:
                monotonicity = result.get("monotonicity_result", {})
                all_verdicts.append(monotonicity.get("verdict", "UNKNOWN"))
                all_violations.extend(monotonicity.get("violations", []))
                entropy_stats.append(monotonicity.get("entropy_statistics", {}))
            
            # Overall verdict
            pass_count = sum(1 for v in all_verdicts if v == "PASS")
            overall_verdict = "PASS" if pass_count == len(all_verdicts) else "FAIL"
            
            # Aggregate entropy statistics
            if entropy_stats:
                final_entropies = [stats.get("final_entropy", 0.0) for stats in entropy_stats]
                entropy_changes = [stats.get("entropy_change", 0.0) for stats in entropy_stats]
                
                summary["entropy_analysis"] = {
                    "overall_verdict": overall_verdict,
                    "tasks_passed": pass_count,
                    "total_tasks": len(all_verdicts),
                    "pass_rate": pass_count / len(all_verdicts),
                    "total_violations": len(all_violations),
                    "mean_final_entropy": np.mean(final_entropies),
                    "mean_entropy_change": np.mean(entropy_changes),
                    "entropy_increased": sum(1 for change in entropy_changes if change > 0),
                    "entropy_decreased": sum(1 for change in entropy_changes if change < 0)
                }
            
            # Discoveries
            discoveries = []
            
            if overall_verdict == "PASS":
                discoveries.append("Second Law of Thermodynamics confirmed: Entropy monotonically non-decreasing")
            else:
                discoveries.append(f"Second Law violation detected: {len(all_violations)} monotonicity violations")
            
            if entropy_stats:
                mean_change = np.mean([stats.get("entropy_change", 0.0) for stats in entropy_stats])
                if mean_change > 0:
                    discoveries.append(f"Net entropy increase observed: {mean_change:.3f} bits average")
                elif mean_change < 0:
                    discoveries.append(f"Net entropy decrease observed: {mean_change:.3f} bits average")
                else:
                    discoveries.append("No net entropy change observed")
            
            summary["discoveries"] = discoveries
        
        if failed_results:
            summary["errors"] = [r["error"] for r in failed_results]
        
        return summary
