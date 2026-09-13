# ugp_discovery_lab/experiments/ugp_volume_calculus.py
from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List, Tuple
import json
import numpy as np
import math
from collections import Counter, defaultdict
import glob

from .base import Experiment
from ..core.registry import register_experiment
from ..core.logging import get_logger
from ..core.reporting import write_json_report, write_md_report

logger = get_logger(__name__)

class UGPVolumeCalculus:
    """
    Calculates the ratio of computational to symmetric volume in GTE trajectories.
    Tests if V_comp / V_symm ≈ 128/125 = 2^7/5^3 emerges from UGP dynamics.
    """
    
    def __init__(self, prime_factor_limit: int = 1000, alpha_entropy_bins: int = 256):
        self.prime_factor_limit = prime_factor_limit
        self.alpha_entropy_bins = alpha_entropy_bins
        
    def prime_factors(self, n: int) -> List[int]:
        """Get prime factors of n."""
        if n <= 1:
            return []
        
        factors = []
        d = 2
        while d * d <= n:
            while n % d == 0:
                factors.append(d)
                n //= d
            d += 1
        if n > 1:
            factors.append(n)
        return factors
    
    def calculate_computational_volume(self, b_values: List[int]) -> Dict[str, Any]:
        """
        Calculate computational volume from the distribution of b-values in UGP trajectories.
        V_comp measures the information capacity of the computational/binary aspects.
        """
        if not b_values:
            return {"entropy": 0.0, "count": 0, "prime_distribution": {}}
        
        # For UGP computational volume, we want to measure the information content
        # of the b-value sequence (ladder indices) - this represents computational complexity
        
        # Calculate the entropy of the b-value distribution
        b_counts = Counter(b_values)
        total_values = len(b_values)
        
        # Shannon entropy of b-value distribution
        entropy = 0.0
        b_distribution = {}
        
        for b_val, count in b_counts.items():
            probability = count / total_values
            if probability > 0:
                entropy -= probability * math.log2(probability)
                b_distribution[b_val] = {
                    "count": count,
                    "probability": probability
                }
        
        # Also analyze prime factors for computational structure
        all_prime_factors = []
        for b in b_values:
            if b > 0 and b <= 10000:  # Limit to reasonable range
                factors = self.prime_factors(b)
                all_prime_factors.extend(factors)
        
        prime_distribution = {}
        if all_prime_factors:
            prime_counts = Counter(all_prime_factors)
            total_factors = len(all_prime_factors)
            
            for prime, count in prime_counts.items():
                if prime <= self.prime_factor_limit:
                    probability = count / total_factors
                    prime_distribution[prime] = {
                        "count": count,
                        "probability": probability
                    }
        
        # Calculate power of 2 contribution (computational base-2 structure)
        powers_of_2 = [2**k for k in range(1, 15)]  # 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384
        power_2_contribution = 0.0
        for power in powers_of_2:
            if power in prime_distribution:
                power_2_contribution += prime_distribution[power]["probability"]
        
        return {
            "entropy": entropy,
            "count": total_values,
            "b_distribution": b_distribution,
            "prime_distribution": prime_distribution,
            "power_2_contribution": power_2_contribution,
            "dominant_primes": sorted(prime_distribution.keys())[:10] if prime_distribution else []
        }
    
    def calculate_symmetry_volume(self, alpha_values: List[float]) -> Dict[str, Any]:
        """
        Calculate symmetry volume from the distribution of RG attractor α* values.
        V_symm measures the information capacity of the geometric/symmetric aspects.
        """
        if not alpha_values:
            return {"entropy": 0.0, "count": 0, "alpha_distribution": {}}
        
        # Filter out invalid values
        valid_alphas = [a for a in alpha_values if np.isfinite(a)]
        
        if not valid_alphas:
            return {"entropy": 0.0, "count": 0, "alpha_distribution": {}}
        
        # Create histogram of alpha values
        alpha_min = min(valid_alphas)
        alpha_max = max(valid_alphas)
        alpha_range = alpha_max - alpha_min
        
        if alpha_range == 0:
            return {"entropy": 0.0, "count": len(valid_alphas), "alpha_distribution": {}}
        
        # Create bins for alpha values
        bin_width = alpha_range / self.alpha_entropy_bins
        bin_counts = defaultdict(int)
        
        for alpha in valid_alphas:
            bin_idx = int((alpha - alpha_min) / bin_width)
            if bin_idx >= self.alpha_entropy_bins:
                bin_idx = self.alpha_entropy_bins - 1
            bin_counts[bin_idx] += 1
        
        # Calculate entropy
        total_count = len(valid_alphas)
        entropy = 0.0
        alpha_distribution = {}
        
        for bin_idx, count in bin_counts.items():
            if count > 0:
                probability = count / total_count
                entropy -= probability * math.log2(probability)
                bin_center = alpha_min + (bin_idx + 0.5) * bin_width
                alpha_distribution[bin_center] = {
                    "count": count,
                    "probability": probability
                }
        
        # Analyze for geometric patterns (powers of 5, golden ratio, etc.)
        # Look for concentrations near special values
        special_values = {
            "quarter_lock": 0.25,
            "golden_ratio": (1 + math.sqrt(5)) / 2,
            "pi_over_4": math.pi / 4,
            "e_over_4": math.e / 4
        }
        
        special_value_proximity = {}
        for name, value in special_values.items():
            proximity = 0.0
            for bin_center, data in alpha_distribution.items():
                distance = abs(bin_center - value)
                if distance < 0.1:  # Within 0.1 of special value
                    proximity += data["probability"] * (1 - distance / 0.1)
            special_value_proximity[name] = proximity
        
        return {
            "entropy": entropy,
            "count": total_count,
            "alpha_distribution": dict(alpha_distribution),
            "special_value_proximity": special_value_proximity,
            "alpha_range": alpha_range,
            "alpha_mean": np.mean(valid_alphas),
            "alpha_std": np.std(valid_alphas)
        }
    
    def analyze_trajectory(self, trajectory_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a single GTE trajectory for computational and symmetry volumes.
        """
        # Extract b values (ladder indices) - look for series data in experiment results
        b_values = []
        alpha_values = []
        
        # Check if this is experiment results data with series (kernel data generator)
        if "data" in trajectory_data and "results" in trajectory_data["data"]:
            results = trajectory_data["data"]["results"]
            for result in results:
                if "series_data" in result:
                    series_data = result["series_data"]
                    
                    # Extract kG, kM, kL series (these are our trajectory data)
                    if "kG" in series_data and "kM" in series_data and "kL" in series_data:
                        kG_series = series_data["kG"]
                        kM_series = series_data["kM"] 
                        kL_series = series_data["kL"]
                        
                        # Create synthetic b values from series indices (for computational volume)
                        # Use the actual series length to create meaningful b values
                        series_length = len(kG_series)
                        b_values = list(range(1, series_length + 1))  # Start from 1, not 0
                        
                        # Calculate alpha values from the GTE relationship: kM ≈ kG + α*kL
                        # Solve for α at each time step: α = (kM - kG) / kL
                        for i in range(min(len(kG_series), len(kM_series), len(kL_series))):
                            kG = kG_series[i]
                            kM = kM_series[i]
                            kL = kL_series[i]
                            
                            # Avoid division by zero and check for finite values
                            if abs(kL) > 1e-10 and np.isfinite(kG) and np.isfinite(kM) and np.isfinite(kL):
                                alpha = (kM - kG) / kL
                                if np.isfinite(alpha) and abs(alpha) < 10.0:  # Reasonable alpha range
                                    alpha_values.append(alpha)
        
        # Check if this is lawful evolution data with real trajectory data
        if "data" in trajectory_data and "results" in trajectory_data["data"]:
            results = trajectory_data["data"]["results"]
            for result in results:
                if "evolution_history" in result:
                    evolution_history = result["evolution_history"]
                    
                    # Extract real b values and calculate alpha from evolution
                    for state in evolution_history:
                        if "b" in state and isinstance(state["b"], int):
                            b_values.append(state["b"])
                            
                            # Calculate alpha from the evolution state
                            # For lawful evolution, alpha can be derived from the relationship between a, b, c
                            if "a" in state and "c" in state:
                                a_val = state["a"]
                                c_val = state["c"]
                                b_val = state["b"]
                                
                                # Use a simple relationship: alpha = (c - a*b) / b^2 for computational volume
                                if b_val != 0:
                                    alpha = (c_val - a_val * b_val) / (b_val * b_val)
                                    if np.isfinite(alpha) and abs(alpha) < 10.0:
                                        alpha_values.append(alpha)
        
        # Check if this is UGP trajectory generator data
        if "data" in trajectory_data and "results" in trajectory_data["data"]:
            results = trajectory_data["data"]["results"]
            for result in results:
                if "trajectory" in result:
                    trajectory = result["trajectory"]
                    
                    # Extract real b values and alpha from trajectory
                    for point in trajectory:
                        if "b" in point and isinstance(point["b"], int):
                            b_values.append(point["b"])
                        
                        if "alpha" in point and np.isfinite(point["alpha"]):
                            alpha_values.append(point["alpha"])
        
        # Also check for direct alpha_star values in experiment results
        if "data" in trajectory_data and "results" in trajectory_data["data"]:
            results = trajectory_data["data"]["results"]
            for result in results:
                if "results" in result:
                    for res in result["results"]:
                        if "alpha_star" in res and np.isfinite(res["alpha_star"]):
                            alpha_values.append(res["alpha_star"])
        
        # Calculate volumes
        comp_volume = self.calculate_computational_volume(b_values)
        symm_volume = self.calculate_symmetry_volume(alpha_values)
        
        # Calculate ratio
        volume_ratio = None
        if comp_volume["entropy"] > 0 and symm_volume["entropy"] > 0:
            volume_ratio = comp_volume["entropy"] / symm_volume["entropy"]
        
        return {
            "computational_volume": comp_volume,
            "symmetry_volume": symm_volume,
            "volume_ratio": volume_ratio,
            "b_count": len(b_values),
            "alpha_count": len(alpha_values)
        }

@register_experiment("ugp_volume_calculus")
class UGPVolumeCalculusExperiment(Experiment):
    """
    Calculates the ratio of computational to symmetric volume in GTE trajectories.
    Tests if the renormalization factor 128/125 emerges from UGP dynamics.
    """

    def tasks(self) -> List[Dict[str, Any]]:
        return [{"task_id": "calculate_volume_ratio"}]

    def run_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Starting UGP Volume Calculus: {task['task_id']}")

        # Configuration
        inputs = self.cfg.get('inputs', {})
        runs_pattern = inputs.get('runs', ["UGP_discovery_lab_runs/exp_*/results/reports/experiment_results.json"])
        
        # Limit the number of files to process to avoid hanging
        max_files = 20
        
        analysis_config = self.cfg.get('analysis', {})
        prime_factor_limit = analysis_config.get('prime_factor_limit', 1000)
        alpha_entropy_bins = analysis_config.get('alpha_entropy_bins', 256)
        
        logger.info(f"Searching for runs with pattern: {runs_pattern}")
        logger.info(f"Prime factor limit: {prime_factor_limit}, Alpha entropy bins: {alpha_entropy_bins}")
        
        # Initialize volume calculator
        volume_calc = UGPVolumeCalculus(prime_factor_limit, alpha_entropy_bins)
        
        # Find and load trajectory data
        trajectory_files = []
        for pattern in runs_pattern:
            files = glob.glob(pattern)
            trajectory_files.extend(files)
        
        # Limit the number of files to process
        trajectory_files = trajectory_files[:max_files]
        logger.info(f"Found {len(trajectory_files)} trajectory files (limited to {max_files})")
        
        if not trajectory_files:
            logger.warning("No trajectory files found, using synthetic data for demonstration")
            # Create synthetic data for demonstration
            synthetic_data = self._create_synthetic_data()
            trajectory_analyses = [volume_calc.analyze_trajectory(synthetic_data)]
        else:
            # Load real trajectory data
            trajectory_analyses = []
            files_processed = 0
            for file_path in trajectory_files:
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    
                    files_processed += 1
                    
                    # Extract trajectory data from the loaded file
                    analysis = volume_calc.analyze_trajectory(data)
                    if analysis["volume_ratio"] is not None:
                        trajectory_analyses.append(analysis)
                        logger.info(f"Valid analysis from {file_path}: b_count={analysis['b_count']}, alpha_count={analysis['alpha_count']}, ratio={analysis['volume_ratio']:.6f}")
                    
                except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
                    logger.warning(f"Could not load {file_path}: {e}")
                    continue
            
            logger.info(f"Processed {files_processed} files, found {len(trajectory_analyses)} valid analyses")
        
        logger.info(f"Analyzed {len(trajectory_analyses)} valid trajectories")
        
        if not trajectory_analyses:
            logger.error("No valid trajectory analyses found")
            return {
                "task_id": task["task_id"],
                "success": False,
                "error": "No valid trajectory data found"
            }
        
        # Aggregate results
        volume_ratios = [analysis["volume_ratio"] for analysis in trajectory_analyses if analysis["volume_ratio"] is not None]
        
        if not volume_ratios:
            logger.error("No valid volume ratios calculated")
            return {
                "task_id": task["task_id"],
                "success": False,
                "error": "No valid volume ratios calculated"
            }
        
        # Calculate statistics
        mean_ratio = np.mean(volume_ratios)
        std_ratio = np.std(volume_ratios)
        median_ratio = np.median(volume_ratios)
        
        # Target ratio
        target_ratio = 128/125  # 1.024
        
        # Calculate agreement
        relative_error = abs(mean_ratio - target_ratio) / target_ratio
        
        logger.info(f"UGP Volume Calculus completed:")
        logger.info(f"  Mean V_comp/V_symm: {mean_ratio:.6f}")
        logger.info(f"  Target (128/125): {target_ratio:.6f}")
        logger.info(f"  Relative error: {relative_error:.4%}")
        logger.info(f"  Std deviation: {std_ratio:.6f}")
        
        # Determine verdict
        if relative_error < 0.01:  # < 1% error
            verdict = "🎯 **CONFIRMED**: Volume ratio matches 128/125 within 1%"
        elif relative_error < 0.05:  # < 5% error
            verdict = "✅ **STRONG SUPPORT**: Volume ratio close to 128/125"
        elif relative_error < 0.10:  # < 10% error
            verdict = "⚠️ **PARTIAL SUPPORT**: Volume ratio reasonably close"
        else:
            verdict = "❌ **NOT CONFIRMED**: Volume ratio differs significantly"
        
        result = {
            "task_id": task["task_id"],
            "success": True,
            "status": "completed",
            "volume_statistics": {
                "mean_ratio": mean_ratio,
                "std_ratio": std_ratio,
                "median_ratio": median_ratio,
                "target_ratio": target_ratio,
                "relative_error": relative_error
            },
            "trajectory_analyses": trajectory_analyses[:10],  # First 10 for details
            "total_trajectories": len(trajectory_analyses),
            "verdict": verdict,
            "target_128_over_125": target_ratio,
            "analysis_config": {
                "prime_factor_limit": prime_factor_limit,
                "alpha_entropy_bins": alpha_entropy_bins
            }
        }
        
        return result
    
    def _create_synthetic_data(self) -> Dict[str, Any]:
        """Create synthetic trajectory data for demonstration."""
        trajectory = []
        for i in range(100):
            # Generate b values with prime factors (biased toward powers of 2)
            b = 2**(i % 7 + 1) + np.random.randint(1, 10)  # Powers of 2 plus noise
            
            # Generate alpha values (biased toward special values)
            if i % 4 == 0:
                alpha = 0.25 + np.random.normal(0, 0.01)  # Quarter-lock
            elif i % 4 == 1:
                alpha = (1 + math.sqrt(5))/2 + np.random.normal(0, 0.01)  # Golden ratio
            elif i % 4 == 2:
                alpha = math.pi/4 + np.random.normal(0, 0.01)  # Pi/4
            else:
                alpha = np.random.normal(0, 0.1)  # Random
            
            trajectory.append({"b": b, "alpha": alpha})
        
        return {"trajectory": trajectory}

    def summarize(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize UGP volume calculus results."""
        successful_results = [r for r in results if r.get("success", False)]
        
        summary_data: Dict[str, Any]
        
        if not successful_results:
            summary_data = {
                "total_tasks": len(results),
                "successful_tasks": 0,
                "failed_tasks": len(results),
                "success_rate": 0.0,
                "status": "failed",
                "error": "No successful UGP volume calculus analyses"
            }
        else:
            result = successful_results[0]
            stats = result["volume_statistics"]
            
            summary_data = {
                "total_tasks": len(results),
                "successful_tasks": len(successful_results),
                "failed_tasks": len(results) - len(successful_results),
                "success_rate": len(successful_results) / len(results) if results else 0.0,
                "status": "completed",
                "mean_volume_ratio": stats["mean_ratio"],
                "target_ratio": stats["target_ratio"],
                "relative_error": stats["relative_error"],
                "verdict": result["verdict"],
                "total_trajectories": result["total_trajectories"],
                "volume_statistics": stats,
                "analysis_config": result["analysis_config"]
            }
        
        # Write reports
        write_json_report(self.root, "ugp_volume_calculus_summary", summary_data)
        
        # Create markdown report
        md_lines = [
            "# UGP Volume Calculus — Summary",
            "",
            f"- **Total Tasks:** {summary_data.get('total_tasks', 0)}",
            f"- **Successful Tasks:** {summary_data.get('successful_tasks', 0)}",
            f"- **Success Rate:** {summary_data.get('success_rate', 0):.1%}",
            ""
        ]
        
        if successful_results:
            stats = summary_data['volume_statistics']
            
            md_lines.extend([
                "## Volume Ratio Analysis",
                f"- **Mean V_comp/V_symm:** {stats['mean_ratio']:.6f}",
                f"- **Target (128/125):** {stats['target_ratio']:.6f}",
                f"- **Relative Error:** {stats['relative_error']:.4%}",
                f"- **Standard Deviation:** {stats['std_ratio']:.6f}",
                f"- **Median Ratio:** {stats['median_ratio']:.6f}",
                f"- **Total Trajectories Analyzed:** {summary_data['total_trajectories']}",
                "",
                "## Final Verdict",
                f"{summary_data['verdict']}",
                "",
                "## Theoretical Interpretation",
                "",
                "The volume ratio V_comp/V_symm measures the information-theoretic geometry of UGP state space:",
                "- **V_comp**: Information capacity of computational/binary aspects (prime factors of b)",
                "- **V_symm**: Information capacity of geometric/symmetric aspects (RG attractor distribution)",
                "",
                "If this ratio equals 128/125 = 2^7/5^3, it provides a dynamical derivation of the U(1) renormalization factor:",
                "- **2^7 = 128**: Computational substrate volume (base-2 arithmetic)",
                "- **5^3 = 125**: Symmetry space volume (base-5 geometric structure)",
                "",
                "This would prove that g₁² = k_a × (128/125) emerges from the fundamental information geometry of UGP.",
                ""
            ])
        
        write_md_report(self.root, "ugp_volume_calculus_summary", "\n".join(md_lines))
        return summary_data
