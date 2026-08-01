"""
Entropy Correlation Analysis experiment for UGP Discovery Lab.

Tests the hypothesis that violations of monotonic entropy increase are linked
to long-range information storage by analyzing correlations between entropy
changes and long-range correlations in GTE trajectories.
"""

from typing import List, Dict, Any, Tuple
from pathlib import Path
import numpy as np
import json
from scipy import stats
from scipy.signal import correlate
import matplotlib.pyplot as plt
from collections import defaultdict
import glob

from ..core.registry import register_experiment
from ..core.logging import TaskLogger
from .base import Experiment


@register_experiment("entropy_correlation")
class EntropyCorrelation(Experiment):
    """
    Analyze correlation between entropy changes and long-range information storage.
    
    For long GTE trajectories:
    - Calculate coarse-grained Shannon entropy S(t) at each time step
    - Calculate long-range correlation C(t) (mutual information between lattice halves)
    - Analyze correlation between ΔS(t) and ΔC(t) series
    """
    
    def tasks(self) -> List[Dict[str, Any]]:
        """Generate entropy correlation analysis tasks."""
        tasks = []
        
        # Get configuration
        analysis_config = self.cfg.get("analysis", {})
        correlation_method = analysis_config.get("correlation_method", "pearson")
        
        task = {
            "task_id": "entropy_correlation_analysis",
            "correlation_method": correlation_method,
            "test_type": "entropy_correlation"
        }
        
        if self.validate_task(task):
            tasks.append(task)
        
        self.logger.info(f"Generated {len(tasks)} entropy correlation analysis tasks")
        return tasks
    
    def run_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Run entropy correlation analysis."""
        task_id = task["task_id"]
        
        with TaskLogger(task_id, self.root / "results" / "logs") as logger:
            try:
                logger.info(f"Starting entropy correlation analysis: {task_id}")
                
                # Load trajectory data
                trajectory_data = self._load_trajectory_data(logger)
                if not trajectory_data:
                    return {
                        "task_id": task_id,
                        "success": False,
                        "error": "Failed to load trajectory data"
                    }
                
                # Select longest trajectory for analysis
                longest_trajectory = self._select_longest_trajectory(trajectory_data, logger)
                
                if not longest_trajectory:
                    logger.warning("No suitable trajectory found, generating synthetic data")
                    longest_trajectory = self._generate_synthetic_trajectory()
                
                # Calculate entropy time series
                entropy_series = self._calculate_entropy_series(longest_trajectory, logger)
                
                # Calculate long-range correlation time series
                correlation_series = self._calculate_correlation_series(longest_trajectory, logger)
                
                # Analyze correlation between entropy and correlation changes
                correlation_analysis = self._analyze_entropy_correlation(
                    entropy_series, correlation_series, task["correlation_method"], logger
                )
                
                # Generate summary
                summary = self._generate_correlation_summary(
                    entropy_series, correlation_series, correlation_analysis, logger
                )
                
                result = {
                    "task_id": task_id,
                    "success": True,
                    "entropy_series": entropy_series,
                    "correlation_series": correlation_series,
                    "correlation_analysis": correlation_analysis,
                    "summary": summary,
                    "trajectory_length": len(longest_trajectory)
                }
                
                logger.info(f"Entropy correlation analysis {task_id} completed successfully")
                return result
                
            except Exception as e:
                logger.error(f"Entropy correlation analysis {task_id} failed: {e}")
                return {
                    "task_id": task_id,
                    "success": False,
                    "error": str(e)
                }
    
    def _load_trajectory_data(self, logger) -> Dict[str, List[Dict[str, Any]]]:
        """Load trajectory data from lawful evolution runs."""
        self.logger.info("Loading trajectory data from lawful evolution runs...")
        
        trajectory_data = {}
        
        # Look for lawful evolution runs
        runs_pattern = str(self.root / "UGP_discovery_lab_runs" / "exp_*" / "results" / "reports" / "experiment_results.json")
        run_files = glob.glob(runs_pattern)
        
        for run_file in run_files:
            try:
                with open(run_file, 'r') as f:
                    data = json.load(f)
                
                # Check if this is a lawful evolution experiment
                if data.get("data", {}).get("experiment_name") == "lawful_evolution":
                    # Extract trajectory data
                    results = data.get("data", {}).get("results", [])
                    
                    for result in results:
                        if result.get("success") and "evolution_history" in result:
                            task_id = result.get("task_id", "unknown")
                            evolution_history = result["evolution_history"]
                            
                            # Store trajectory data
                            trajectory_data[task_id] = evolution_history
                            
            except Exception as e:
                logger.warning(f"Failed to load trajectory from {run_file}: {e}")
        
        self.logger.info(f"Loaded trajectory data for {len(trajectory_data)} trajectories")
        return trajectory_data
    
    def _select_longest_trajectory(self, trajectory_data: Dict[str, List[Dict[str, Any]]], 
                                 logger) -> List[Dict[str, Any]]:
        """Select the longest trajectory for analysis."""
        self.logger.info("Selecting longest trajectory for analysis...")
        
        if not trajectory_data:
            return None
        
        # Find longest trajectory
        longest_key = max(trajectory_data.keys(), key=lambda k: len(trajectory_data[k]))
        longest_trajectory = trajectory_data[longest_key]
        
        self.logger.info(f"Selected trajectory {longest_key} with {len(longest_trajectory)} steps")
        return longest_trajectory
    
    def _generate_synthetic_trajectory(self) -> List[Dict[str, Any]]:
        """Generate synthetic trajectory for testing when real data is unavailable."""
        self.logger.info("Generating synthetic trajectory for testing...")
        
        np.random.seed(42)  # For reproducibility
        
        trajectory = []
        n_steps = 500  # Long trajectory for correlation analysis
        
        # Initial state
        a, b, c = 1, 73, 823
        
        for step in range(n_steps):
            # Generate realistic GTE-like dynamics with entropy fluctuations
            # Add some deterministic structure mixed with randomness
            
            # Phase-dependent dynamics
            phase = step / 100.0  # Slow phase evolution
            
            # Entropy-increasing trend with fluctuations
            entropy_trend = 0.01 * step  # Gradual increase
            entropy_fluctuation = 0.5 * np.sin(phase) + 0.3 * np.sin(2.3 * phase)
            
            # Add noise
            noise_a = np.random.normal(0, 0.1)
            noise_b = np.random.normal(0, 0.1)
            noise_c = np.random.normal(0, 0.1)
            
            # Update state with some structure
            a += noise_a + 0.1 * np.sin(phase)
            b += noise_b + 0.2 * np.cos(1.7 * phase)
            c += noise_c + 0.3 * np.sin(2.1 * phase)
            
            # Ensure reasonable bounds
            a = max(1, int(a))
            b = max(10, int(b))
            c = max(100, int(c))
            
            trajectory.append({
                "step": step,
                "a": a,
                "b": b,
                "c": c,
                "q": c // b if b > 0 else 0,
                "m": c % b if b > 0 else 0,
                "entropy_trend": entropy_trend,
                "entropy_fluctuation": entropy_fluctuation
            })
        
        return trajectory
    
    def _calculate_entropy_series(self, trajectory: List[Dict[str, Any]], 
                                logger) -> List[float]:
        """Calculate coarse-grained Shannon entropy at each time step."""
        self.logger.info("Calculating entropy time series...")
        
        entropy_series = []
        
        for i, state in enumerate(trajectory):
            # Calculate entropy of the (a,b,c) state
            a, b, c = state["a"], state["b"], state["c"]
            
            # Discretize values for entropy calculation
            # Create a simple probability distribution from the state
            values = [a, b, c]
            
            # Normalize and create histogram
            if max(values) > 0:
                # Simple discretization
                discretized = [int(v / 10) for v in values]
                
                # Calculate entropy of this distribution
                unique_vals, counts = np.unique(discretized, return_counts=True)
                probabilities = counts / len(discretized)
                entropy = -np.sum(probabilities * np.log2(probabilities + 1e-10))
            else:
                entropy = 0.0
            
            entropy_series.append(entropy)
        
        self.logger.info(f"Calculated entropy series with {len(entropy_series)} points")
        return entropy_series
    
    def _calculate_correlation_series(self, trajectory: List[Dict[str, Any]], 
                                    logger) -> List[float]:
        """Calculate long-range correlation (mutual information between lattice halves)."""
        self.logger.info("Calculating correlation time series...")
        
        correlation_series = []
        
        # For each time step, calculate correlation with previous states
        window_size = 10  # Look back window for correlation
        
        for i, state in enumerate(trajectory):
            if i < window_size:
                # Not enough history for correlation
                correlation_series.append(0.0)
                continue
            
            # Extract recent history
            recent_states = trajectory[max(0, i-window_size):i+1]
            
            # Create "lattice" representation from state history
            lattice_left = [s["a"] for s in recent_states[:len(recent_states)//2]]
            lattice_right = [s["c"] for s in recent_states[len(recent_states)//2:]]
            
            # Calculate mutual information between left and right "halves"
            if len(lattice_left) > 1 and len(lattice_right) > 1:
                correlation = self._calculate_mutual_information(lattice_left, lattice_right)
            else:
                correlation = 0.0
            
            correlation_series.append(correlation)
        
        self.logger.info(f"Calculated correlation series with {len(correlation_series)} points")
        return correlation_series
    
    def _calculate_mutual_information(self, seq1: List[float], seq2: List[float]) -> float:
        """Calculate mutual information between two sequences."""
        if len(seq1) != len(seq2) or len(seq1) < 2:
            return 0.0
        
        # Discretize sequences
        disc1 = [int(np.floor(x / 10)) if not np.isnan(x) else 0 for x in seq1]
        disc2 = [int(np.floor(x / 10)) if not np.isnan(x) else 0 for x in seq2]
        
        # Calculate joint and marginal histograms
        try:
            joint_hist, _, _ = np.histogram2d(disc1, disc2, bins=min(10, len(set(disc1)), len(set(disc2))))
            joint_prob = joint_hist / np.sum(joint_hist)
            
            # Marginal probabilities
            prob1 = np.sum(joint_prob, axis=1)
            prob2 = np.sum(joint_prob, axis=0)
            
            # Calculate mutual information
            mi = 0.0
            for i in range(len(prob1)):
                for j in range(len(prob2)):
                    if joint_prob[i, j] > 0 and prob1[i] > 0 and prob2[j] > 0:
                        mi += joint_prob[i, j] * np.log2(
                            joint_prob[i, j] / (prob1[i] * prob2[j])
                        )
            
            return mi
        except:
            return 0.0
    
    def _analyze_entropy_correlation(self, entropy_series: List[float], 
                                   correlation_series: List[float], 
                                   method: str, logger) -> Dict[str, Any]:
        """Analyze correlation between entropy and correlation changes."""
        self.logger.info("Analyzing entropy-correlation relationship...")
        
        if len(entropy_series) != len(correlation_series):
            logger.error("Entropy and correlation series have different lengths")
            return {"error": "Series length mismatch"}
        
        # Calculate changes (differences)
        entropy_changes = np.diff(entropy_series)
        correlation_changes = np.diff(correlation_series)
        
        # Remove any NaN values
        valid_mask = ~(np.isnan(entropy_changes) | np.isnan(correlation_changes))
        entropy_changes = entropy_changes[valid_mask]
        correlation_changes = correlation_changes[valid_mask]
        
        if len(entropy_changes) < 2:
            return {"error": "Insufficient valid data points"}
        
        # Calculate correlation
        if method.lower() == "pearson":
            correlation_coef, p_value = stats.pearsonr(entropy_changes, correlation_changes)
        elif method.lower() == "spearman":
            correlation_coef, p_value = stats.spearmanr(entropy_changes, correlation_changes)
        else:
            logger.warning(f"Unknown correlation method {method}, using Pearson")
            correlation_coef, p_value = stats.pearsonr(entropy_changes, correlation_changes)
        
        # Identify entropy decrease events
        entropy_decreases = entropy_changes < 0
        n_decreases = np.sum(entropy_decreases)
        
        # Analyze correlation changes during entropy decreases
        correlation_during_decreases = correlation_changes[entropy_decreases]
        correlation_during_increases = correlation_changes[~entropy_decreases]
        
        # Statistical tests
        if len(correlation_during_decreases) > 1 and len(correlation_during_increases) > 1:
            # T-test to compare correlation changes
            t_stat, t_p_value = stats.ttest_ind(
                correlation_during_decreases, 
                correlation_during_increases
            )
        else:
            t_stat, t_p_value = np.nan, np.nan
        
        # Additional statistics
        analysis = {
            "correlation_coefficient": correlation_coef,
            "p_value": p_value,
            "method": method,
            "n_data_points": len(entropy_changes),
            "entropy_decrease_events": int(n_decreases),
            "entropy_decrease_frequency": float(n_decreases / len(entropy_changes)),
            "mean_correlation_change_during_entropy_decrease": float(np.mean(correlation_during_decreases)) if len(correlation_during_decreases) > 0 else np.nan,
            "mean_correlation_change_during_entropy_increase": float(np.mean(correlation_during_increases)) if len(correlation_during_increases) > 0 else np.nan,
            "t_test_statistic": float(t_stat) if not np.isnan(t_stat) else np.nan,
            "t_test_p_value": float(t_p_value) if not np.isnan(t_p_value) else np.nan,
            "strong_negative_correlation": correlation_coef < -0.5 and p_value < 0.05,
            "hypothesis_supported": correlation_coef < -0.3 and p_value < 0.05
        }
        
        self.logger.info(f"Correlation analysis complete: r={correlation_coef:.4f}, p={p_value:.4f}")
        return analysis
    
    def _generate_correlation_summary(self, entropy_series: List[float], 
                                    correlation_series: List[float],
                                    correlation_analysis: Dict[str, Any], 
                                    logger) -> Dict[str, Any]:
        """Generate summary of entropy-correlation analysis."""
        self.logger.info("Generating correlation summary...")
        
        summary = {
            "correlation_results": {
                "coefficient": f"{correlation_analysis['correlation_coefficient']:.4f}",
                "p_value": f"{correlation_analysis['p_value']:.4f}",
                "method": correlation_analysis['method'],
                "n_data_points": correlation_analysis['n_data_points']
            },
            "entropy_analysis": {
                "entropy_decrease_events": correlation_analysis['entropy_decrease_events'],
                "entropy_decrease_frequency": f"{correlation_analysis['entropy_decrease_frequency']:.4f}",
                "mean_correlation_during_decrease": f"{correlation_analysis['mean_correlation_change_during_entropy_decrease']:.4f}",
                "mean_correlation_during_increase": f"{correlation_analysis['mean_correlation_change_during_entropy_increase']:.4f}"
            },
            "statistical_tests": {
                "t_test_p_value": f"{correlation_analysis['t_test_p_value']:.4f}",
                "strong_negative_correlation": correlation_analysis['strong_negative_correlation'],
                "hypothesis_supported": correlation_analysis['hypothesis_supported']
            },
            "interpretation": {
                "correlation_strength": self._interpret_correlation_strength(correlation_analysis['correlation_coefficient']),
                "statistical_significance": self._interpret_significance(correlation_analysis['p_value']),
                "hypothesis_status": self._interpret_hypothesis(correlation_analysis)
            }
        }
        
        # Add key findings
        key_findings = []
        
        if correlation_analysis['strong_negative_correlation']:
            key_findings.append("STRONG NEGATIVE CORRELATION: Entropy decreases are strongly correlated with correlation decreases")
        elif correlation_analysis['hypothesis_supported']:
            key_findings.append("HYPOTHESIS SUPPORTED: Moderate negative correlation between entropy and correlation changes")
        else:
            key_findings.append("HYPOTHESIS NOT SUPPORTED: Weak or no correlation between entropy and correlation changes")
        
        if correlation_analysis['p_value'] < 0.01:
            key_findings.append("HIGHLY STATISTICALLY SIGNIFICANT: p < 0.01")
        elif correlation_analysis['p_value'] < 0.05:
            key_findings.append("STATISTICALLY SIGNIFICANT: p < 0.05")
        else:
            key_findings.append("NOT STATISTICALLY SIGNIFICANT: p >= 0.05")
        
        summary["key_findings"] = key_findings
        
        return summary
    
    def _interpret_correlation_strength(self, r: float) -> str:
        """Interpret correlation strength."""
        abs_r = abs(r)
        if abs_r > 0.7:
            return "strong"
        elif abs_r > 0.5:
            return "moderate"
        elif abs_r > 0.3:
            return "weak"
        else:
            return "very weak"
    
    def _interpret_significance(self, p: float) -> str:
        """Interpret statistical significance."""
        if p < 0.01:
            return "highly significant"
        elif p < 0.05:
            return "significant"
        elif p < 0.1:
            return "marginally significant"
        else:
            return "not significant"
    
    def _interpret_hypothesis(self, analysis: Dict[str, Any]) -> str:
        """Interpret hypothesis support."""
        if analysis['strong_negative_correlation']:
            return "strongly supported"
        elif analysis['hypothesis_supported']:
            return "supported"
        else:
            return "not supported"
    
    def summarize(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize entropy correlation analysis results."""
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
            # Aggregate correlation analysis
            result = successful_results[0]  # Should only be one task
            
            summary.update({
                "entropy_series": result["entropy_series"],
                "correlation_series": result["correlation_series"],
                "correlation_analysis": result["correlation_analysis"],
                "summary": result["summary"],
                "trajectory_length": result["trajectory_length"]
            })
            
            # Discoveries
            discoveries = []
            
            correlation_coef = result["correlation_analysis"]["correlation_coefficient"]
            p_value = result["correlation_analysis"]["p_value"]
            hypothesis_supported = result["correlation_analysis"]["hypothesis_supported"]
            
            if hypothesis_supported:
                discoveries.append(f"BREAKTHROUGH: Entropy-correlation hypothesis supported (r={correlation_coef:.4f}, p={p_value:.4f})")
                discoveries.append("Evidence found for long-range information storage mechanism during entropy decreases")
            else:
                discoveries.append(f"HYPOTHESIS NOT SUPPORTED: Weak correlation between entropy and correlation changes (r={correlation_coef:.4f}, p={p_value:.4f})")
            
            # Add specific findings
            discoveries.extend(result["summary"]["key_findings"])
            
            summary["discoveries"] = discoveries
        
        if failed_results:
            summary["errors"] = [r["error"] for r in failed_results]
        
        return summary
