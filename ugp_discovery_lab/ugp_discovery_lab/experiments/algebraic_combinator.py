# ugp_discovery_lab/experiments/algebraic_combinator.py
from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import json
import numpy as np
import math
import random
from fractions import Fraction
import itertools

from .base import Experiment
from ..core.registry import register_experiment
from ..core.logging import get_logger
from ..core.reporting import write_json_report, write_md_report

logger = get_logger(__name__)

class AlgebraicCombinator:
    """
    Systematic search for algebraic expressions combining UGP constants.
    Uses a genetic algorithm approach with guided random search.
    """
    
    def __init__(self, constants: Dict[str, float], target_value: float, max_complexity: int = 10):
        self.constants = constants
        self.target_value = target_value
        self.max_complexity = max_complexity
        self.epsilon = 1e-12  # Small value to avoid division by zero
        
        # Define operations and their complexities
        self.operations = {
            '+': (lambda a, b: a + b, 1),
            '-': (lambda a, b: a - b, 1),
            '*': (lambda a, b: a * b, 1),
            '/': (lambda a, b: a / (b + self.epsilon), 1),
            'sqrt': (lambda a: math.sqrt(abs(a) + self.epsilon), 2),
            'log': (lambda a: math.log(abs(a) + self.epsilon), 2),
            'exp': (lambda a: math.exp(a), 2),
            'sin': (lambda a: math.sin(a), 2),
            'cos': (lambda a: math.cos(a), 2),
            'pow2': (lambda a: a**2, 2),
            'pow3': (lambda a: a**3, 3),
            'pow-1': (lambda a: 1/(abs(a) + self.epsilon), 2),
            'pow-2': (lambda a: 1/((abs(a) + self.epsilon)**2), 3),
            'pow1/2': (lambda a: math.sqrt(abs(a) + self.epsilon), 2),
            'pow1/3': (lambda a: (abs(a) + self.epsilon)**(1/3), 3),
        }
        
        # Power operations with integer/rational powers
        self.powers = [-2, -1, -0.5, 0.5, 1, 2, 3]
    
    def generate_random_expression(self) -> Tuple[float, str, int]:
        """Generate a random algebraic expression and evaluate it."""
        try:
            # Choose number of constants to use (1 to 3)
            num_constants = random.randint(1, min(3, len(self.constants)))
            selected_constants = random.sample(list(self.constants.items()), num_constants)
            
            # Start with a constant
            result = selected_constants[0][1]
            expression = selected_constants[0][0]
            complexity = 0
            
            # Apply operations
            for _ in range(random.randint(0, 3)):
                if len(selected_constants) > 1:
                    # Binary operation
                    op_name = random.choice(['+', '-', '*', '/'])
                    op_func, op_complexity = self.operations[op_name]
                    
                    other_constant = random.choice(selected_constants)[1]
                    result = op_func(result, other_constant)
                    expression = f"({expression} {op_name} {other_constant:.6f})"
                    complexity += op_complexity
                else:
                    # Unary operation
                    op_name = random.choice(['sqrt', 'log', 'exp', 'sin', 'cos', 'pow2', 'pow-1'])
                    op_func, op_complexity = self.operations[op_name]
                    
                    result = op_func(result)
                    expression = f"{op_name}({expression})"
                    complexity += op_complexity
                
                # Check for complex numbers or invalid results
                if isinstance(result, complex) or not np.isfinite(result):
                    return float('inf'), "ERROR", self.max_complexity + 1
                
                # Check complexity limit
                if complexity > self.max_complexity:
                    break
            
            # Apply a power operation at the end
            if random.random() < 0.3:  # 30% chance
                power = random.choice(self.powers)
                result = result**power
                expression = f"({expression})^{power}"
                complexity += 2
            
            return result, expression, complexity
            
        except (ZeroDivisionError, OverflowError, ValueError, TypeError):
            return float('inf'), "ERROR", self.max_complexity + 1
    
    def fitness_function(self, value: float, complexity: int) -> float:
        """Calculate fitness: higher is better."""
        # Handle complex numbers and invalid values
        if isinstance(value, complex) or not np.isfinite(value) or value <= 0:
            return 0.0
        
        # Convert to real number if needed
        if hasattr(value, 'real'):
            value = value.real
        
        # Accuracy component (exponential decay from target)
        accuracy = math.exp(-abs(value - self.target_value) / self.target_value)
        
        # Complexity penalty (parsimony)
        complexity_penalty = math.exp(-complexity / 5.0)
        
        # Combined fitness
        fitness = accuracy * complexity_penalty
        
        return fitness
    
    def search(self, generations: int = 1000, population_size: int = 500) -> List[Dict[str, Any]]:
        """Run the genetic algorithm search."""
        logger.info(f"Starting algebraic combinator search with {generations} generations, population {population_size}")
        
        # Initialize population
        population = []
        for _ in range(population_size):
            value, expression, complexity = self.generate_random_expression()
            fitness = self.fitness_function(value, complexity)
            population.append({
                'value': value,
                'expression': expression,
                'complexity': complexity,
                'fitness': fitness,
                'relative_error': abs(value - self.target_value) / self.target_value if np.isfinite(value) else float('inf')
            })
        
        best_candidates = []
        
        for generation in range(generations):
            # Sort by fitness
            population.sort(key=lambda x: x['fitness'], reverse=True)
            
            # Keep best candidates
            best_candidates.extend(population[:10])
            
            # Select parents (top 20% + some random)
            parents = population[:population_size // 5]
            parents.extend(random.sample(population, population_size // 5))
            
            # Generate new population
            new_population = []
            for _ in range(population_size):
                if random.random() < 0.7:  # 70% mutation
                    parent = random.choice(parents)
                    # Mutate by generating new expression
                    value, expression, complexity = self.generate_random_expression()
                else:  # 30% crossover (just copy parent)
                    parent = random.choice(parents)
                    value, expression, complexity = parent['value'], parent['expression'], parent['complexity']
                
                fitness = self.fitness_function(value, complexity)
                new_population.append({
                    'value': value,
                    'expression': expression,
                    'complexity': complexity,
                    'fitness': fitness,
                    'relative_error': abs(value - self.target_value) / self.target_value if np.isfinite(value) else float('inf')
                })
            
            population = new_population
            
            if generation % 100 == 0:
                best = max(population, key=lambda x: x['fitness'])
                logger.info(f"Generation {generation}: Best fitness = {best['fitness']:.6f}, "
                          f"Error = {best['relative_error']:.6%}, Expression = {best['expression']}")
        
        # Sort all candidates by fitness
        best_candidates.sort(key=lambda x: x['fitness'], reverse=True)
        
        # Remove duplicates and return top candidates
        seen = set()
        unique_candidates = []
        for candidate in best_candidates:
            key = (candidate['expression'], candidate['complexity'])
            if key not in seen:
                seen.add(key)
                unique_candidates.append(candidate)
        
        return unique_candidates[:50]  # Return top 50 unique candidates

@register_experiment("algebraic_combinator")
class AlgebraicCombinatorExperiment(Experiment):
    """
    Systematic search for an algebraic expression for g1_squared.
    Uses genetic algorithm to find the most accurate and parsimonious formula.
    """

    def tasks(self) -> List[Dict[str, Any]]:
        return [{"task_id": "search_algebraic_expression"}]

    def run_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Starting Algebraic Combinator Search: {task['task_id']}")

        # UGP Fundamental Constants
        constants = {
            # Elegant Kernel constants
            'k_a': 1/8,
            'k_b': -3/2,
            'k_c': 4/3,
            'k_L2': 7/512,
            
            # Universal RG Attractors (from previous analysis)
            'alpha_A': -0.08503468530335825,  # Primary RG attractor
            'alpha_B': 0.075413,              # Attractor B
            'alpha_C': 0.264418,              # Attractor C
            'quarter_lock': 0.25,             # Quarter-lock attractor
            
            # Fundamental constants
            'pi': math.pi,
            'e': math.e,
            'phi': (1 + math.sqrt(5)) / 2,    # Golden ratio
        }
        
        # Target value for g1^2
        target_g1_squared = 0.128  # Based on number-theoretic analysis
        
        # Search parameters
        generations = self.cfg.get('search', {}).get('generations', 1000)
        population_size = self.cfg.get('search', {}).get('population_size', 500)
        max_complexity = self.cfg.get('search', {}).get('max_complexity', 10)
        
        # Initialize combinator
        combinator = AlgebraicCombinator(constants, target_g1_squared, max_complexity)
        
        # Run search
        candidates = combinator.search(generations, population_size)
        
        # Analyze results
        best_candidates = candidates[:10]  # Top 10
        
        logger.info(f"Algebraic combinator search completed:")
        logger.info(f"  Total candidates evaluated: {len(candidates)}")
        logger.info(f"  Best error: {best_candidates[0]['relative_error']:.6%}")
        logger.info(f"  Best expression: {best_candidates[0]['expression']}")
        
        result = {
            "task_id": task["task_id"],
            "search_parameters": {
                "generations": generations,
                "population_size": population_size,
                "max_complexity": max_complexity,
                "target_g1_squared": target_g1_squared
            },
            "constants_used": constants,
            "best_candidates": best_candidates,
            "all_candidates": candidates[:50],  # Top 50 for analysis
            "success": True,
            "status": "completed"
        }
        return result

    def summarize(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize algebraic combinator results."""
        successful_results = [r for r in results if r.get("success", False)]
        
        if not successful_results:
            summary_data: Dict[str, Any] = {
                "total_tasks": len(results),
                "successful_tasks": 0,
                "failed_tasks": len(results),
                "success_rate": 0.0,
                "status": "failed",
                "error": "No successful algebraic combinator searches"
            }
        else:
            result = successful_results[0]
            
            # Analyze the best candidates
            best_candidates = result["best_candidates"]
            best_candidate = best_candidates[0] if best_candidates else None
            
            summary_success: Dict[str, Any] = {
                "total_tasks": len(results),
                "successful_tasks": len(successful_results),
                "failed_tasks": len(results) - len(successful_results),
                "success_rate": len(successful_results) / len(results) if results else 0.0,
                "status": "completed",
                "search_parameters": result["search_parameters"],
                "constants_used": result["constants_used"],
                "best_candidate": best_candidate,
                "top_10_candidates": best_candidates,
                "total_candidates_evaluated": len(result["all_candidates"])
            }
            
            # Use the success summary for the rest of the function
            summary_data = summary_success
        
        # Write reports
        write_json_report(self.root, "algebraic_combinator_summary", summary_data)
        
        # Create markdown report
        md_lines = [
            "# Algebraic Combinator Search — Summary",
            "",
            f"- **Total Tasks:** {summary_data.get('total_tasks', 0)}",
            f"- **Successful Tasks:** {summary_data.get('successful_tasks', 0)}",
            f"- **Success Rate:** {summary_data.get('success_rate', 0):.1%}",
            ""
        ]
        
        if successful_results and summary_data.get('best_candidate'):
            best = summary_data['best_candidate']
            
            md_lines.extend([
                "## Best Candidate Expression",
                f"- **Expression:** {best['expression']}",
                f"- **Derived g₁²:** {best['value']:.6f}",
                f"- **Target g₁²:** {summary_data['search_parameters']['target_g1_squared']:.6f}",
                f"- **Relative Error:** {best['relative_error']:.6%}",
                f"- **Complexity:** {best['complexity']}",
                f"- **Fitness:** {best['fitness']:.6f}",
                "",
                "## Search Parameters",
                f"- **Generations:** {summary_data['search_parameters']['generations']}",
                f"- **Population Size:** {summary_data['search_parameters']['population_size']}",
                f"- **Max Complexity:** {summary_data['search_parameters']['max_complexity']}",
                f"- **Total Candidates Evaluated:** {summary_data['total_candidates_evaluated']}",
                "",
                "## Top 10 Candidates",
                ""
            ])
            
            for i, candidate in enumerate(summary_data['top_10_candidates']):
                md_lines.extend([
                    f"### {i+1}. {candidate['expression']}",
                    f"- Derived g₁²: {candidate['value']:.6f}",
                    f"- Relative Error: {candidate['relative_error']:.6%}",
                    f"- Complexity: {candidate['complexity']}",
                    f"- Fitness: {candidate['fitness']:.6f}",
                    ""
                ])
            
            md_lines.extend([
                "## Constants Used",
                ""
            ])
            
            for name, value in summary_data['constants_used'].items():
                md_lines.append(f"- **{name}:** {value:.10f}")
            
            md_lines.append("")
        
        write_md_report(self.root, "algebraic_combinator_summary", "\n".join(md_lines))
        return summary_data
