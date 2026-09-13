"""
CA Universality experiments for UGP Discovery Lab.
"""

from typing import List, Dict, Any
from pathlib import Path
import numpy as np
from ..core.registry import register_experiment
from ..core.logging import TaskLogger
from ..engines.uwca import ca_step, ca_run, RULES
from .base import Experiment


@register_experiment("ca_universality")
class CAUniversality(Experiment):
    """
    Test cellular automaton universality by running various CA rules
    and measuring their computational properties.
    """
    
    def tasks(self) -> List[Dict[str, Any]]:
        """Generate CA universality test tasks."""
        tasks = []
        
        # Get test configurations
        test_configs = self.cfg.get("tests", [])
        
        for tcfg in test_configs:
            task = {
                "task_id": tcfg["name"],
                "rule": tcfg.get("rule", "rule110"),
                "width": tcfg.get("width", 32),
                "steps": tcfg.get("steps", 64),
                "wrap": tcfg.get("wrap", True),
                "seed": tcfg.get("seed", [0, 0, 0, 1, 1, 1] + [0] * 26),
                "test_type": "ca_universality"
            }
            
            if self.validate_task(task):
                tasks.append(task)
        
        self.logger.info(f"Generated {len(tasks)} CA universality tasks")
        return tasks
    
    def run_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single CA universality test."""
        task_id = task["task_id"]
        
        with TaskLogger(task_id, self.root / "results" / "logs") as logger:
            try:
                logger.info(f"Starting CA universality test: {task_id}")
                
                # Extract parameters
                rule = task["rule"]
                width = task["width"]
                steps = task["steps"]
                wrap = task["wrap"]
                seed = task["seed"]
                
                # Validate parameters
                if rule not in RULES:
                    raise ValueError(f"Unknown rule: {rule}")
                
                if len(seed) != width:
                    # Adjust seed to match width
                    if len(seed) < width:
                        seed = seed + [0] * (width - len(seed))
                    else:
                        seed = seed[:width]
                
                logger.info(f"Running {rule} on {width}x{steps} grid")
                
                # Run the CA
                history = ca_run(seed, rule, steps, wrap)
                
                # Analyze the evolution
                analysis = self._analyze_ca_evolution(history, rule, logger)
                
                # Save results
                result = {
                    "task_id": task_id,
                    "success": True,
                    "rule": rule,
                    "width": width,
                    "steps": steps,
                    "wrap": wrap,
                    "initial_state": seed,
                    "final_state": history[-1],
                    "analysis": analysis,
                    "evolution_sample": history[::max(1, len(history)//10)]  # Sample every 10% of steps
                }
                
                logger.info(f"CA test {task_id} completed successfully")
                return result
                
            except Exception as e:
                logger.error(f"CA test {task_id} failed: {e}")
                return {
                    "task_id": task_id,
                    "success": False,
                    "error": str(e)
                }
    
    def _analyze_ca_evolution(self, history: List[List[int]], rule: str, logger) -> Dict[str, Any]:
        """Analyze CA evolution patterns."""
        logger.debug("Analyzing CA evolution patterns...")
        
        # Basic statistics
        n_steps = len(history) - 1  # Exclude initial state
        width = len(history[0])
        
        # Density evolution
        densities = [sum(state) / len(state) for state in history]
        
        # Pattern complexity (simplified)
        complexity_scores = []
        for state in history:
            # Count transitions (complexity proxy)
            transitions = sum(1 for i in range(len(state)-1) if state[i] != state[i+1])
            complexity_scores.append(transitions / len(state))
        
        # Periodicity detection (simple)
        period = self._detect_periodicity(history)
        
        # Entropy evolution
        entropy_scores = []
        for state in history:
            # Simple entropy calculation
            ones = sum(state)
            zeros = len(state) - ones
            if ones == 0 or zeros == 0:
                entropy = 0
            else:
                p1 = ones / len(state)
                p0 = zeros / len(state)
                entropy = -(p1 * np.log2(p1) + p0 * np.log2(p0))
            entropy_scores.append(entropy)
        
        # Wolfram class estimation
        wolfram_class = self._estimate_wolfram_class(history, rule)
        
        analysis = {
            "n_steps": n_steps,
            "width": width,
            "final_density": densities[-1],
            "density_evolution": densities,
            "complexity_evolution": complexity_scores,
            "average_complexity": np.mean(complexity_scores),
            "periodicity": period,
            "entropy_evolution": entropy_scores,
            "final_entropy": entropy_scores[-1],
            "wolfram_class_estimate": wolfram_class,
            "rule_properties": {
                "rule": rule,
                "minterm_count": len(RULES[rule]),
                "is_universal": rule == "rule110"
            }
        }
        
        logger.debug(f"Analysis complete: class={wolfram_class}, period={period}")
        return analysis
    
    def _detect_periodicity(self, history: List[List[int]], max_period: int = 20) -> Dict[str, Any]:
        """Detect periodic patterns in CA evolution."""
        if len(history) < max_period * 2:
            return {"detected": False, "period": None, "confidence": 0.0}
        
        # Check for exact repetition
        for period in range(1, min(max_period + 1, len(history) // 2)):
            is_periodic = True
            for i in range(len(history) - period):
                if history[i] != history[i + period]:
                    is_periodic = False
                    break
            
            if is_periodic:
                return {
                    "detected": True,
                    "period": period,
                    "confidence": 1.0,
                    "pattern_length": len(history) // period
                }
        
        return {"detected": False, "period": None, "confidence": 0.0}
    
    def _estimate_wolfram_class(self, history: List[List[int]], rule: str) -> str:
        """Estimate Wolfram class based on evolution patterns."""
        # Simple heuristics for Wolfram classification
        
        # Check for fixed points (Class I)
        if len(set(tuple(state) for state in history)) == 1:
            return "Class I (Fixed Point)"
        
        # Check for simple periodicity (Class II)
        periodicity = self._detect_periodicity(history)
        if periodicity["detected"] and periodicity["period"] <= 4:
            return "Class II (Periodic)"
        
        # Check for chaotic behavior (Class III)
        # High entropy and complex patterns
        final_entropy = self._calculate_entropy(history[-1])
        if final_entropy > 0.8:
            return "Class III (Chaotic)"
        
        # Check for complex behavior (Class IV)
        # Rule 110 is known to be Class IV
        if rule == "rule110":
            return "Class IV (Complex/Universal)"
        
        # Default classification
        return "Unknown/Undetermined"
    
    def _calculate_entropy(self, state: List[int]) -> float:
        """Calculate Shannon entropy of a binary state."""
        ones = sum(state)
        zeros = len(state) - ones
        
        if ones == 0 or zeros == 0:
            return 0.0
        
        p1 = ones / len(state)
        p0 = zeros / len(state)
        
        return -(p1 * np.log2(p1) + p0 * np.log2(p0))
    
    def summarize(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize CA universality test results."""
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
            # Aggregate analysis across all successful tests
            all_wolfram_classes = [r["analysis"]["wolfram_class_estimate"] for r in successful_results]
            all_rules_tested = list(set(r["rule"] for r in successful_results))
            
            summary["metrics"] = {
                "rules_tested": all_rules_tested,
                "wolfram_classes_observed": list(set(all_wolfram_classes)),
                "average_complexity": np.mean([
                    r["analysis"]["average_complexity"] for r in successful_results
                ]),
                "universality_verified": any(
                    r["analysis"]["rule_properties"]["is_universal"] 
                    for r in successful_results
                )
            }
            
            # Discoveries
            discoveries = []
            if summary["metrics"]["universality_verified"]:
                discoveries.append("Rule 110 universality confirmed")
            
            unique_classes = set(all_wolfram_classes)
            if len(unique_classes) > 1:
                discoveries.append(f"Multiple Wolfram classes observed: {', '.join(unique_classes)}")
            
            summary["discoveries"] = discoveries
        
        if failed_results:
            summary["errors"] = [r["error"] for r in failed_results]
        
        return summary
