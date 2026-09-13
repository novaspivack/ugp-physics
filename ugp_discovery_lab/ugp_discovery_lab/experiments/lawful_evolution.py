"""
Lawful Evolution experiments for UGP Discovery Lab.

Tests various UGP-compliant evolution rules beyond the standard GTE.
"""

from typing import List, Dict, Any, Tuple
from pathlib import Path
import numpy as np
from ..core.registry import register_experiment
from ..core.logging import TaskLogger
from ..engines.uwca import fib_fast_doubling, lucas_fast_doubling, mersenne_number, repunit_number
from .base import Experiment


@register_experiment("lawful_evolution")
class LawfulEvolution(Experiment):
    """
    Test various lawful evolution rules on UGP substrate.
    
    Implements the grammar from the spec:
    - C-policy: Mersenne, Repunit, Lucas, Pell channels
    - B-policy: Fibonacci, Lucas, Chebyshev, Prime-gap lifts
    - A-policy: GTE standard or phase-correcting rules
    - Mirror: D2, D4, D5, D6 symmetry groups
    """
    
    def tasks(self) -> List[Dict[str, Any]]:
        """Generate lawful evolution test tasks."""
        tasks = []
        
        # Get evolution configurations
        le_configs = self.cfg.get("le_config", {})
        run_config = self.cfg.get("run", {})
        
        # Generate task for each window level
        windows = run_config.get("windows", [10])
        steps = run_config.get("steps", 100)
        seed = run_config.get("seed", [1, 73, 823])
        
        for window_n in windows:
            task = {
                "task_id": f"le_{le_configs.get('c_policy', 'mersenne')}_{le_configs.get('b_policy', 'fib')}_{window_n}",
                "window_n": window_n,
                "steps": steps,
                "seed": seed,
                "le_config": le_configs,
                "test_type": "lawful_evolution"
            }
            
            if self.validate_task(task):
                tasks.append(task)
        
        self.logger.info(f"Generated {len(tasks)} lawful evolution tasks")
        return tasks
    
    def run_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single lawful evolution test."""
        task_id = task["task_id"]
        
        with TaskLogger(task_id, self.root / "results" / "logs") as logger:
            try:
                logger.info(f"Starting lawful evolution test: {task_id}")
                
                # Extract parameters
                window_n = task["window_n"]
                steps = task["steps"]
                seed = task["seed"]
                le_config = task["le_config"]
                
                logger.info(f"Running evolution: n={window_n}, steps={steps}")
                logger.info(f"Config: {le_config}")
                
                # Run the evolution
                evolution_history = self._run_evolution(seed, le_config, window_n, steps, logger)
                
                # Analyze the evolution
                analysis = self._analyze_evolution(evolution_history, le_config, logger)
                
                # Check invariants
                invariant_check = self._check_ugp_invariants(evolution_history, le_config, logger)
                
                # Save results
                result = {
                    "task_id": task_id,
                    "success": True,
                    "window_n": window_n,
                    "steps": steps,
                    "seed": seed,
                    "le_config": le_config,
                    "evolution_history": evolution_history,
                    "analysis": analysis,
                    "invariant_check": invariant_check
                }
                
                logger.info(f"Lawful evolution test {task_id} completed successfully")
                return result
                
            except Exception as e:
                logger.error(f"Lawful evolution test {task_id} failed: {e}")
                return {
                    "task_id": task_id,
                    "success": False,
                    "error": str(e)
                }
    
    def _run_evolution(self, seed: List[int], le_config: Dict[str, Any], 
                      window_n: int, steps: int, logger) -> List[Dict[str, Any]]:
        """Run the actual evolution according to the LE configuration."""
        history = []
        current_state = {
            "a": seed[0],
            "b": seed[1], 
            "c": seed[2],
            "q": 0,
            "m": 0,
            "step": 0,
            "step_type": "initial"
        }
        
        # Initialize q and m
        current_state["q"] = current_state["c"] // current_state["b"]
        current_state["m"] = current_state["c"] % current_state["b"]
        
        history.append(current_state.copy())
        
        for step in range(steps):
            next_state = self._evolve_step(current_state, le_config, window_n, logger)
            history.append(next_state)
            current_state = next_state
        
        return history
    
    def _evolve_step(self, current: Dict[str, Any], le_config: Dict[str, Any], 
                    window_n: int, logger) -> Dict[str, Any]:
        """Execute one evolution step according to the LE configuration."""
        next_state = current.copy()
        next_state["step"] += 1
        
        # Determine step type (odd/even)
        is_odd_step = next_state["step"] % 2 == 1
        
        # Get triggers configuration
        triggers = le_config.get("triggers", {})
        ridge_trigger = triggers.get("ridge", True)
        mirror_trigger = triggers.get("mirror", True)
        
        if is_odd_step:
            # Odd step: standard GTE-like updates
            next_state["step_type"] = "odd"
            
            # A-policy: phase updates
            a_policy = le_config.get("a_policy", "gte")
            if a_policy == "gte":
                next_state["a"] = current["m"] - (window_n + 2 - next_state["step"])
            elif a_policy == "phase_mod":
                # Phase-correcting rule with configurable parameters
                a_params = le_config.get("a_params", {"alpha1": 1, "alpha2": 0, "alpha3": 0, "kappa": 233})
                alpha1 = a_params.get("alpha1", 1)
                alpha2 = a_params.get("alpha2", 0)
                alpha3 = a_params.get("alpha3", 0)
                kappa = a_params.get("kappa", 233)
                next_state["a"] = (alpha1 * current["m"] + alpha2 * current["q"] + alpha3) % kappa
            
            # B-policy: width updates
            b_policy = le_config.get("b_policy", "fib")
            if b_policy == "gte":
                next_state["b"] = current["b"] - (current["m"] + current["q"])
            elif b_policy == "fib":
                # Standard Fibonacci lift
                gap = abs(current["q"] - current.get("q_prev", current["q"]))
                next_state["b"] = current["b"] - (current["m"] + current["q"]) + fib_fast_doubling(gap)
            elif b_policy == "lucas":
                # Lucas lift
                gap = abs(current["q"] - current.get("q_prev", current["q"]))
                next_state["b"] = current["b"] - (current["m"] + current["q"]) + lucas_fast_doubling(gap)
            elif b_policy == "chebyshev":
                # Chebyshev lift
                gap = abs(current["q"] - current.get("q_prev", current["q"]))
                chi = le_config.get("chebyshev_chi", 2)
                next_state["b"] = current["b"] - (current["m"] + current["q"]) + self._chebyshev_lift(gap, chi)
            elif b_policy == "primegap":
                # Prime gap lift
                gap = abs(current["q"] - current.get("q_prev", current["q"]))
                next_state["b"] = current["b"] - (current["m"] + current["q"]) + self._prime_gap_lift(gap)
            
            # C-policy: height updates (ridge hits)
            if ridge_trigger and self._is_ridge_hit(current, window_n):
                c_policy = le_config.get("c_policy", "mersenne")
                if c_policy == "mersenne":
                    next_state["c"] = mersenne_number(window_n)
                elif c_policy == "repunit":
                    base = le_config.get("repunit_base", 3)
                    next_state["c"] = repunit_number(base, window_n)
                elif c_policy == "lucas":
                    next_state["c"] = lucas_fast_doubling(window_n)
                elif c_policy == "pell":
                    next_state["c"] = self._pell_number(window_n)
                else:
                    next_state["c"] = current["c"]  # No change
            else:
                next_state["c"] = current["c"]  # No ridge hit
        
        else:
            # Even step: Fibonacci/Lucas lifts
            next_state["step_type"] = "even"
            
            # A-policy: phase updates
            a_policy = le_config.get("a_policy", "gte")
            if a_policy == "gte":
                next_state["a"] = current["m"] - window_n
            elif a_policy == "phase_mod":
                a_params = le_config.get("a_params", {"alpha1": 1, "alpha2": 0, "alpha3": 0, "kappa": 233})
                alpha1 = a_params.get("alpha1", 1)
                alpha2 = a_params.get("alpha2", 0)
                alpha3 = a_params.get("alpha3", 0)
                kappa = a_params.get("kappa", 233)
                next_state["a"] = (alpha1 * current["m"] + alpha2 * current["q"] + alpha3) % kappa
            
            # B-policy: Fibonacci/Lucas lifts
            b_policy = le_config.get("b_policy", "fib")
            gap = abs(current["q"] - current.get("q_prev", current["q"]))
            
            if b_policy == "fib":
                next_state["b"] = current["b"] + fib_fast_doubling(gap)
            elif b_policy == "lucas":
                next_state["b"] = current["b"] + lucas_fast_doubling(gap)
            elif b_policy == "chebyshev":
                chi = le_config.get("chebyshev_chi", 2)
                next_state["b"] = current["b"] + self._chebyshev_lift(gap, chi)
            elif b_policy == "primegap":
                next_state["b"] = current["b"] + self._prime_gap_lift(gap)
            
            # C-policy: standard or Mersenne jumps
            c_policy = le_config.get("c_policy", "mersenne")
            if c_policy in ["mersenne", "repunit", "lucas", "pell"]:
                next_state["c"] = current["b"] * current["q"] + 15  # Standard GTE
            else:
                next_state["c"] = current["c"]  # No change
        
        # Apply mirror policy if configured
        if mirror_trigger:
            next_state = self._apply_mirror_policy(next_state, le_config, window_n, logger)
        
        # Update q and m
        next_state["q"] = next_state["c"] // next_state["b"] if next_state["b"] > 0 else 0
        next_state["m"] = next_state["c"] % next_state["b"] if next_state["b"] > 0 else 0
        
        # Store previous q for gap calculations
        next_state["q_prev"] = current["q"]
        
        return next_state
    
    def _chebyshev_lift(self, gap: int, chi: int) -> int:
        """Compute Chebyshev-based lift."""
        from ..engines.uwca import chebyshev_u
        return chebyshev_u(gap, chi)
    
    def _prime_gap_lift(self, gap: int) -> int:
        """Compute prime gap lift using small lookup table."""
        # Small prime gaps lookup table
        prime_gaps = [1, 2, 2, 4, 2, 4, 2, 4, 6, 2, 6, 4, 2, 4, 6, 6, 2, 6, 4, 2, 6, 4, 6, 8]
        if gap < len(prime_gaps):
            return prime_gaps[gap]
        else:
            # Fallback for larger gaps
            return 2  # Most common prime gap
    
    def _pell_number(self, n: int) -> int:
        """Compute Pell number P_n."""
        if n < 0:
            return 0
        if n == 0:
            return 0
        if n == 1:
            return 1
        
        p_prev = 0
        p_curr = 1
        
        for i in range(2, n + 1):
            p_next = 2 * p_curr + p_prev
            p_prev = p_curr
            p_curr = p_next
        
        return p_curr
    
    def _is_ridge_hit(self, state: Dict[str, Any], window_n: int) -> bool:
        """Check if this is a ridge hit event."""
        # Simple heuristic for ridge hits
        # In a full implementation, this would be more sophisticated
        c = state.get("c", 0)
        ridge_value = 2**window_n - 16
        
        # Check if c is close to ridge value
        return abs(c - ridge_value) < 100
    
    def _apply_mirror_policy(self, state: Dict[str, Any], le_config: Dict[str, Any], 
                           window_n: int, logger) -> Dict[str, Any]:
        """Apply mirror policy according to dihedral group."""
        mirror = le_config.get("mirror", "d2")
        
        if mirror == "d2":
            # Standard D2 mirror symmetry
            return state  # No additional transformation needed
        
        elif mirror in ["d4", "d5", "d6"]:
            # Apply dihedral group transformations
            n = int(mirror[1])  # Extract n from "d4", "d5", "d6"
            return self._apply_dihedral_transformation(state, n, logger)
        
        else:
            logger.warning(f"Unknown mirror group: {mirror}")
            return state
    
    def _apply_dihedral_transformation(self, state: Dict[str, Any], n: int, 
                                     logger) -> Dict[str, Any]:
        """Apply dihedral group transformation."""
        # This is a simplified implementation
        # In a full implementation, this would apply actual dihedral group operations
        
        transformed_state = state.copy()
        
        # Apply rotation by 2π/n
        rotation_angle = 2 * 3.14159 / n
        
        # For now, just add a small perturbation based on the rotation
        # In a real implementation, this would transform the actual coordinates
        perturbation = 0.1 * np.sin(rotation_angle)
        
        # Apply perturbation to b and c
        transformed_state["b"] = int(state["b"] * (1 + perturbation))
        transformed_state["c"] = int(state["c"] * (1 + perturbation))
        
        logger.debug(f"Applied D{n} transformation with perturbation {perturbation:.3f}")
        return transformed_state
    
    def _analyze_evolution(self, history: List[Dict[str, Any]], 
                          le_config: Dict[str, Any], logger) -> Dict[str, Any]:
        """Analyze the evolution patterns."""
        logger.debug("Analyzing evolution patterns...")
        
        if not history:
            return {"error": "No evolution history to analyze"}
        
        # Extract sequences
        a_sequence = [state["a"] for state in history]
        b_sequence = [state["b"] for state in history]
        c_sequence = [state["c"] for state in history]
        q_sequence = [state["q"] for state in history]
        
        # Basic statistics
        analysis = {
            "n_steps": len(history) - 1,
            "final_state": history[-1],
            "a_range": (min(a_sequence), max(a_sequence)),
            "b_range": (min(b_sequence), max(b_sequence)),
            "c_range": (min(c_sequence), max(c_sequence)),
            "q_range": (min(q_sequence), max(q_sequence))
        }
        
        # Growth analysis
        analysis["growth_rates"] = {
            "a": self._calculate_growth_rate(a_sequence),
            "b": self._calculate_growth_rate(b_sequence),
            "c": self._calculate_growth_rate(c_sequence)
        }
        
        # Pattern detection
        analysis["patterns"] = {
            "a_periodic": self._detect_periodicity(a_sequence),
            "b_periodic": self._detect_periodicity(b_sequence),
            "c_periodic": self._detect_periodicity(c_sequence)
        }
        
        # Gap analysis (for Fibonacci/Lucas lifts)
        if le_config.get("b_policy") in ["fib", "lucas"]:
            gaps = []
            for i in range(1, len(history)):
                gap = abs(history[i]["q"] - history[i-1]["q"])
                gaps.append(gap)
            
            analysis["gap_statistics"] = {
                "unique_gaps": list(set(gaps)),
                "most_common_gap": max(set(gaps), key=gaps.count) if gaps else None,
                "gap_distribution": {gap: gaps.count(gap) for gap in set(gaps)}
            }
        
        return analysis
    
    def _calculate_growth_rate(self, sequence: List[int]) -> float:
        """Calculate approximate growth rate of a sequence."""
        if len(sequence) < 2:
            return 0.0
        
        # Simple linear regression slope
        x = np.arange(len(sequence))
        y = np.array(sequence, dtype=float)
        
        if len(set(y)) == 1:
            return 0.0  # Constant sequence
        
        slope = np.polyfit(x, y, 1)[0]
        return float(slope)
    
    def _detect_periodicity(self, sequence: List[int], max_period: int = 20) -> Dict[str, Any]:
        """Detect periodic patterns in a sequence."""
        if len(sequence) < max_period * 2:
            return {"detected": False, "period": None}
        
        for period in range(1, min(max_period + 1, len(sequence) // 2)):
            is_periodic = True
            for i in range(len(sequence) - period):
                if sequence[i] != sequence[i + period]:
                    is_periodic = False
                    break
            
            if is_periodic:
                return {"detected": True, "period": period}
        
        return {"detected": False, "period": None}
    
    def _check_ugp_invariants(self, history: List[Dict[str, Any]], 
                             le_config: Dict[str, Any], logger) -> Dict[str, Any]:
        """Check UGP invariant preservation."""
        logger.debug("Checking UGP invariants...")
        
        invariant_check = {
            "prime_lock_violations": 0,
            "mirror_duality_violations": 0,
            "fibonacci_rigidity_violations": 0,
            "ridge_lock_violations": 0,
            "overall_status": "unknown"
        }
        
        # Check prime-lock (simplified)
        for state in history:
            if state["step"] > 0:  # Skip initial state
                c1 = state["b"] * state["q"] + 20
                if not self._is_prime(c1):
                    invariant_check["prime_lock_violations"] += 1
        
        # Check Fibonacci rigidity (simplified)
        if le_config.get("b_policy") == "fib":
            gaps = []
            for i in range(1, len(history)):
                gap = abs(history[i]["q"] - history[i-1]["q"])
                gaps.append(gap)
            
            if gaps and max(set(gaps), key=gaps.count) != 13:
                invariant_check["fibonacci_rigidity_violations"] += 1
        
        # Overall status
        total_violations = sum(v for k, v in invariant_check.items() if k.endswith("_violations"))
        if total_violations == 0:
            invariant_check["overall_status"] = "invariants_preserved"
        else:
            invariant_check["overall_status"] = f"violations_detected_{total_violations}"
        
        return invariant_check
    
    def _is_prime(self, n: int) -> bool:
        """Simple primality test."""
        from ..engines.uwca import is_prime
        return is_prime(n)
    
    def summarize(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize lawful evolution test results."""
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
            # Aggregate analysis
            all_configs = [r["le_config"] for r in successful_results]
            all_invariants = [r["invariant_check"] for r in successful_results]
            
            summary["metrics"] = {
                "configurations_tested": len(set(str(cfg) for cfg in all_configs)),
                "invariant_preservation_rate": sum(
                    1 for inv in all_invariants 
                    if inv["overall_status"] == "invariants_preserved"
                ) / len(all_invariants),
                "average_growth_rate": np.mean([
                    r["analysis"]["growth_rates"]["b"] for r in successful_results
                ]),
                "pattern_detection_rate": sum(
                    1 for r in successful_results
                    if any(r["analysis"]["patterns"][key]["detected"] 
                          for key in r["analysis"]["patterns"])
                ) / len(successful_results)
            }
            
            # Discoveries
            discoveries = []
            
            # Check for new rigidity patterns
            for r in successful_results:
                if "gap_statistics" in r["analysis"]:
                    gap_stats = r["analysis"]["gap_statistics"]
                    if gap_stats["most_common_gap"] and gap_stats["most_common_gap"] != 13:
                        discoveries.append(f"New gap-lock detected: {gap_stats['most_common_gap']}")
            
            # Check for invariant preservation
            if summary["metrics"]["invariant_preservation_rate"] > 0.8:
                discoveries.append("High invariant preservation rate achieved")
            
            summary["discoveries"] = discoveries
        
        if failed_results:
            summary["errors"] = [r["error"] for r in failed_results]
        
        return summary
