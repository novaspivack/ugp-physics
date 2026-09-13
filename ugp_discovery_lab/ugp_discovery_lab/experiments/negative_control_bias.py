"""
Negative Control Bias Experiment

This experiment deliberately uses biased data generation to verify that
the integrity linter and checks properly detect and reject biased generators.
This serves as a test to ensure the integrity system works correctly.
"""

from typing import List, Dict, Any
import numpy as np
from ..core.logging import get_logger
from ..diagnostics.data_linter import validate_data_integrity, DataIntegrityError
from ..experiments.base import Experiment
from ..core.registry import register_experiment


@register_experiment("negative_control_bias")
class NegativeControlBias(Experiment):
    """
    Negative control experiment that deliberately uses biased data generation.
    
    This experiment should FAIL due to integrity violations, proving that
    the integrity system is working correctly.
    """
    
    def tasks(self) -> List[Dict[str, Any]]:
        """Generate tasks for negative control bias testing."""
        tasks = []
        
        # Get configuration
        generator_config = self.cfg.get("generator", {})
        run_config = self.cfg.get("run", {})
        integrity_config = self.cfg.get("integrity", {})
        
        # Create tasks that should trigger integrity violations
        task_configs = [
            {
                "task_id": "negctrl_alpha_hardcoded",
                "generator_type": "biased_linear",
                "params": {
                    "alpha": 0.25,  # This should trigger suspicion
                    "noise": 0.0,
                    "relationship": "k_M = k_G + alpha * k_L"  # This should trigger dependency check
                }
            },
            {
                "task_id": "negctrl_lambda_formula", 
                "generator_type": "biased_dihedral",
                "params": {
                    "lambda_n": "1/(2*cos(pi/n))",  # This should trigger hardcoded relationship
                    "formula": "cos(pi/n)",  # This should trigger suspicious field
                    "noise": 0.05
                }
            },
            {
                "task_id": "negctrl_conservation",
                "generator_type": "biased_conserved",
                "params": {
                    "conserved_quantity": "M + G + L = constant",  # This should trigger relationship
                    "target": "linear_conservation",  # This should trigger suspicious field
                    "noise": 0.1
                }
            }
        ]
        
        for task_config in task_configs:
            tasks.append({
                "task_id": task_config["task_id"],
                "generator_type": task_config["generator_type"],
                "generator_params": task_config["params"],
                "run_config": run_config,
                "integrity_config": integrity_config
            })
        
        return tasks
    
    def run_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Run a negative control bias task."""
        task_id = task["task_id"]
        generator_type = task["generator_type"]
        generator_params = task["generator_params"]
        integrity_config = task["integrity_config"]
        
        logger = get_logger(f"negative_control_bias:{task_id}")
        logger.info(f"Starting negative control bias test: {task_id}")
        logger.info(f"Generator type: {generator_type}")
        logger.info(f"Parameters: {generator_params}")
        
        try:
            # This should trigger integrity violations
            fail_on_warning = integrity_config.get("fail_on_warning", True)
            
            # Create a configuration that should trigger warnings
            cfg = {
                "generator": {
                    "type": generator_type,
                    "params": generator_params,
                    "code": self._get_biased_code(generator_type, generator_params)
                },
                "data": generator_params,  # Put params in data section to trigger suspicion
                "integrity": integrity_config
            }
            
            context = {
                "seeds": [42, 173, 823],
                "task_id": task_id
            }
            
            # This should raise DataIntegrityError
            validate_data_integrity(cfg, context, fail_on_warning=fail_on_warning)
            
            # If we get here, the integrity check failed to catch the bias!
            logger.error(f"INTEGRITY FAILURE: Bias was not detected for {task_id}")
            return {
                "task_id": task_id,
                "status": "integrity_failure",
                "error": "Bias was not detected by integrity checks",
                "expected_failure": True,
                "actual_result": "passed_incorrectly"
            }
            
        except DataIntegrityError as e:
            # This is the expected result - integrity check caught the bias
            logger.info(f"✅ INTEGRITY SUCCESS: Bias detected for {task_id}")
            logger.info(f"Integrity error: {str(e)}")
            return {
                "task_id": task_id,
                "status": "blocked_by_integrity",
                "integrity_warnings": str(e),
                "expected_failure": True,
                "actual_result": "correctly_blocked"
            }
            
        except Exception as e:
            logger.error(f"Unexpected error in negative control: {e}")
            return {
                "task_id": task_id,
                "status": "unexpected_error",
                "error": str(e),
                "expected_failure": True,
                "actual_result": "unexpected_error"
            }
    
    def _get_biased_code(self, generator_type: str, params: Dict[str, Any]) -> str:
        """Generate biased code that should trigger integrity violations."""
        
        if generator_type == "biased_linear":
            alpha = params.get("alpha", 0.25)
            return f"""
# BIASED CODE - This should be detected!
def generate_data():
    k_M = k_G + {alpha} * k_L  # This creates the relationship being tested!
    return k_M, k_G, k_L
"""
        
        elif generator_type == "biased_dihedral":
            lambda_n = params.get("lambda_n", "1/(2*cos(pi/n))")
            return f"""
# BIASED CODE - This should be detected!
def generate_data():
    lambda_n = {lambda_n}  # Hardcoded dihedral formula!
    k_M = k_G + lambda_n * k_L  # Creates exact relationship
    return k_M, k_G, k_L
"""
        
        elif generator_type == "biased_conserved":
            return """
# BIASED CODE - This should be detected!
def generate_data():
    # Create data that satisfies conservation law
    M = random()
    G = random() 
    L = constant - M - G  # Forces M + G + L = constant!
    return M, G, L
"""
        
        else:
            return "# Unknown biased generator type"
    
    def summarize(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize negative control bias experiment results."""
        
        # Count different types of results
        blocked_by_integrity = [r for r in results if r.get("status") == "blocked_by_integrity"]
        integrity_failures = [r for r in results if r.get("status") == "integrity_failure"]
        unexpected_errors = [r for r in results if r.get("status") == "unexpected_error"]
        
        # Calculate success metrics
        total_tasks = len(results)
        correctly_blocked = len(blocked_by_integrity)
        integrity_failure_count = len(integrity_failures)
        unexpected_error_count = len(unexpected_errors)
        
        # Integrity system effectiveness
        integrity_effectiveness = (correctly_blocked / total_tasks) if total_tasks > 0 else 0
        
        # Determine overall status
        if integrity_failure_count > 0:
            overall_status = "integrity_system_failed"
            message = f"CRITICAL: Integrity system failed to detect {integrity_failure_count} biases"
        elif unexpected_error_count > 0:
            overall_status = "unexpected_errors"
            message = f"Unexpected errors in {unexpected_error_count} tasks"
        elif correctly_blocked == total_tasks:
            overall_status = "integrity_system_working"
            message = "✅ Integrity system working correctly - all biases detected"
        else:
            overall_status = "partial_success"
            message = f"Integrity system partially working - {correctly_blocked}/{total_tasks} biases detected"
        
        # Compile integrity warnings
        integrity_warnings = []
        for result in blocked_by_integrity:
            warnings = result.get("integrity_warnings", "")
            if warnings:
                integrity_warnings.append({
                    "task_id": result["task_id"],
                    "warnings": warnings
                })
        
        summary = {
            "total_tasks": total_tasks,
            "correctly_blocked": correctly_blocked,
            "integrity_failures": integrity_failure_count,
            "unexpected_errors": unexpected_error_count,
            "integrity_effectiveness": integrity_effectiveness,
            "overall_status": overall_status,
            "message": message,
            "integrity_warnings": integrity_warnings,
            "data_origin": {
                "type": "synthetic_negative_control",
                "generator": "biased_generators",
                "purpose": "test_integrity_system",
                "expected_behavior": "should_be_blocked"
            }
        }
        
        return summary
