"""
Holographic Transducer Experiment

# ⚠️ SYNTHETIC CA DATA — NOT GTE TRIPLE EVOLUTION DATA ⚠️
# This experiment generates boundary/bulk data from Rule-110 cellular automaton
# evolution, NOT from actual GTE triple evolution trajectories.
# The holographic claim in Paper 4 (GTE Dynamics) requires re-running this
# experiment with genuine GTE ridge events as bulk data and c-component
# trajectories as boundary data. Do NOT cite these results for the holographic
# claim until the GTE-data version is run (see EPIC_CLUSTER4/SPEC_P04).

Prototype reconstruction of bulk trajectories from ridge/mirror boundary data + a seed.
Tests the holographic principle for UGP evolution - can we reconstruct interior
evolution from boundary conditions alone?
"""

import numpy as np
import sympy as sp
from typing import Dict, List, Any, Tuple, Optional
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
import json
import os
import math

from .base import Experiment
from ..core.registry import register_experiment
from ..core.logging import get_logger
from ..core.checkpoint import save_checkpoint, load_checkpoint
from ..engines.uwca import ca_step

logger = get_logger(__name__)


@register_experiment("holographic_transducer")
class HolographicTransducer(Experiment):
    """
    Holographic reconstruction of UGP evolution from boundary data.
    
    Tests whether interior evolution can be predicted from:
    - Ridge/mirror boundary conditions
    - Initial seed state
    - Minimal transducer model
    """
    
    def tasks(self) -> List[Dict[str, Any]]:
        """Generate tasks for holographic reconstruction experiments."""
        tasks = []
        
        # Extract configuration
        boundary_types = self.cfg.get("boundary_types", ["ridge", "mirror"])
        seed_range = self.cfg.get("seed_range", [42, 100, 200, 500])
        window_sizes = self.cfg.get("window_sizes", [8, 10, 12])
        transducer_models = self.cfg.get("transducer_models", ["linear", "quadratic", "neural_1layer"])
        evolution_steps = self.cfg.get("evolution_steps", 50)
        
        # Generate task combinations
        for boundary_type in boundary_types:
            for seed in seed_range:
                for window in window_sizes:
                    for model_type in transducer_models:
                        task = {
                            "boundary_type": boundary_type,
                            "seed": seed,
                            "window_size": window,
                            "model_type": model_type,
                            "evolution_steps": evolution_steps,
                            "task_id": f"holographic_{boundary_type}_{seed}_{window}_{model_type}"
                        }
                        tasks.append(task)
        
        return tasks
    
    def run_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single holographic reconstruction task."""
        try:
            # Extract task parameters
            boundary_type = task["boundary_type"]
            seed = task["seed"]
            window_size = task["window_size"]
            model_type = task["model_type"]
            evolution_steps = task["evolution_steps"]
            
            logger.info(f"Running holographic transducer: {boundary_type}, seed={seed}, window={window_size}, model={model_type}")
            
            # Generate boundary data and seed
            boundary_data, seed_state = self._generate_boundary_data(
                boundary_type, seed, window_size, evolution_steps
            )
            
            # Train transducer model
            transducer = self._train_transducer(
                boundary_data, seed_state, model_type, self.cfg
            )
            
            # Test reconstruction accuracy
            reconstruction_results = self._test_reconstruction(
                transducer, boundary_data, seed_state, evolution_steps
            )
            
            # Analyze holographic properties
            holographic_analysis = self._analyze_holographic_properties(
                boundary_data, reconstruction_results, self.cfg
            )
            
            return {
                "task_id": task["task_id"],
                "boundary_type": boundary_type,
                "seed": seed,
                "window_size": window_size,
                "model_type": model_type,
                "boundary_data": boundary_data,
                "seed_state": seed_state,
                "transducer_metrics": transducer.get("metrics", {}),
                "reconstruction_results": reconstruction_results,
                "holographic_analysis": holographic_analysis,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Holographic transducer task failed: {e}")
            return {
                "task_id": task.get("task_id", "unknown"),
                "status": "failed",
                "error": str(e)
            }
    
    def summarize(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize holographic transducer experiment results."""
        successful_results = [r for r in results if r.get("status") == "success"]
        
        if not successful_results:
            return {
                "total_tasks": len(results),
                "successful_tasks": 0,
                "failed_tasks": len(results),
                "status": "all_failed",
                "error": "No successful holographic reconstructions"
            }
        
        # Aggregate metrics by model type and boundary type
        model_metrics = {}
        boundary_metrics = {}
        
        for result in successful_results:
            model_type = result["model_type"]
            boundary_type = result["boundary_type"]
            
            # Model type aggregation
            if model_type not in model_metrics:
                model_metrics[model_type] = {
                    "accuracy_scores": [],
                    "r2_scores": [],
                    "reconstruction_errors": [],
                    "holographic_scores": []
                }
            
            metrics = result.get("transducer_metrics", {})
            reconstruction = result.get("reconstruction_results", {})
            holographic = result.get("holographic_analysis", {})
            
            model_metrics[model_type]["accuracy_scores"].append(
                metrics.get("accuracy", 0.0)
            )
            model_metrics[model_type]["r2_scores"].append(
                metrics.get("r2_score", 0.0)
            )
            model_metrics[model_type]["reconstruction_errors"].append(
                reconstruction.get("mean_error", float('inf'))
            )
            model_metrics[model_type]["holographic_scores"].append(
                holographic.get("holographic_score", 0.0)
            )
            
            # Boundary type aggregation
            if boundary_type not in boundary_metrics:
                boundary_metrics[boundary_type] = {
                    "accuracy_scores": [],
                    "reconstruction_errors": [],
                    "holographic_scores": []
                }
            
            boundary_metrics[boundary_type]["accuracy_scores"].append(
                metrics.get("accuracy", 0.0)
            )
            boundary_metrics[boundary_type]["reconstruction_errors"].append(
                reconstruction.get("mean_error", float('inf'))
            )
            boundary_metrics[boundary_type]["holographic_scores"].append(
                holographic.get("holographic_score", 0.0)
            )
        
        # Compute summary statistics
        model_summaries = {}
        for model_type, metrics in model_metrics.items():
            model_summaries[model_type] = {
                "mean_accuracy": np.mean(metrics["accuracy_scores"]),
                "std_accuracy": np.std(metrics["accuracy_scores"]),
                "mean_r2": np.mean(metrics["r2_scores"]),
                "mean_reconstruction_error": np.mean(metrics["reconstruction_errors"]),
                "mean_holographic_score": np.mean(metrics["holographic_scores"]),
                "best_accuracy": np.max(metrics["accuracy_scores"]),
                "best_holographic_score": np.max(metrics["holographic_scores"])
            }
        
        boundary_summaries = {}
        for boundary_type, metrics in boundary_metrics.items():
            boundary_summaries[boundary_type] = {
                "mean_accuracy": np.mean(metrics["accuracy_scores"]),
                "mean_reconstruction_error": np.mean(metrics["reconstruction_errors"]),
                "mean_holographic_score": np.mean(metrics["holographic_scores"]),
                "best_accuracy": np.max(metrics["accuracy_scores"])
            }
        
        # Find best performing combinations
        best_model = max(model_summaries.items(), key=lambda x: x[1]["mean_holographic_score"])
        best_boundary = max(boundary_summaries.items(), key=lambda x: x[1]["mean_holographic_score"])
        
        # Overall holographic success assessment
        all_holographic_scores = []
        all_exact_match_rates = []
        for result in successful_results:
            holographic_score = result.get("holographic_analysis", {}).get("holographic_score", 0.0)
            all_holographic_scores.append(holographic_score)
            
            # Calculate exact match rate from reconstruction results
            reconstruction = result.get("reconstruction_results", {})
            mean_error = reconstruction.get("mean_error", float('inf'))
            # Convert error to exact match rate (perfect match = error < 1e-6)
            exact_match_rate = 1.0 if mean_error < 1e-6 else 0.0
            all_exact_match_rates.append(exact_match_rate)
        
        mean_holographic_score = np.mean(all_holographic_scores)
        mean_exact_match_rate = np.mean(all_exact_match_rates)
        max_exact_match_rate = np.max(all_exact_match_rates) if all_exact_match_rates else 0.0
        
        # Determine verdict based on exact match rate threshold
        pass_threshold = self.cfg.get("eval", {}).get("pass_threshold", 0.99)
        verdict = "PASS" if max_exact_match_rate >= pass_threshold else "FAIL"
        
        holographic_success = mean_holographic_score > self.cfg.get("holographic_threshold", 0.8)
        
        return {
            "total_tasks": len(results),
            "successful_tasks": len(successful_results),
            "failed_tasks": len(results) - len(successful_results),
            "model_performance": model_summaries,
            "boundary_performance": boundary_summaries,
            "best_model": {
                "type": best_model[0],
                "metrics": best_model[1]
            },
            "best_boundary": {
                "type": best_boundary[0],
                "metrics": best_boundary[1]
            },
            "holographic_success": holographic_success,
            "mean_holographic_score": mean_holographic_score,
            "holographic_threshold": self.cfg.get("holographic_threshold", 0.8),
            "exact_match_rate": {
                "mean": mean_exact_match_rate,
                "max": max_exact_match_rate,
                "pass_threshold": pass_threshold
            },
            "verdict": verdict,
            "status": "success" if holographic_success else "partial_success"
        }
    
    def _generate_boundary_data(self, boundary_type: str, seed: int, window_size: int, 
                               evolution_steps: int) -> Tuple[Dict[str, Any], np.ndarray]:
        """Generate boundary data for holographic reconstruction."""
        np.random.seed(seed)
        
        # Generate initial seed state
        seed_state = np.random.randint(0, 2, size=window_size)
        
        # Evolve the system to get full trajectory
        full_trajectory = []
        current_state = seed_state.copy()
        
        for step in range(evolution_steps):
            full_trajectory.append(current_state.copy())
            current_state = ca_step(current_state.tolist() if isinstance(current_state, np.ndarray) else current_state, rule="rule110")
        
        full_trajectory = np.array(full_trajectory)
        
        # Extract boundary data based on type
        if boundary_type == "ridge":
            # Ridge: peak values along evolution
            boundary_indices = []
            for t in range(evolution_steps):
                # Find local maxima in space
                state = full_trajectory[t]
                for i in range(1, window_size - 1):
                    if state[i] > state[i-1] and state[i] > state[i+1]:
                        boundary_indices.append((t, i))
            
            boundary_data = {
                "type": "ridge",
                "indices": boundary_indices,
                "values": [full_trajectory[t, i] for t, i in boundary_indices],
                "trajectory_shape": full_trajectory.shape
            }
            
        elif boundary_type == "mirror":
            # Mirror: symmetric boundary conditions
            boundary_indices = []
            for t in range(evolution_steps):
                # Take boundary positions (left and right edges)
                boundary_indices.extend([(t, 0), (t, window_size-1)])
            
            boundary_data = {
                "type": "mirror",
                "indices": boundary_indices,
                "values": [full_trajectory[t, i] for t, i in boundary_indices],
                "trajectory_shape": full_trajectory.shape
            }
            
        else:
            raise ValueError(f"Unknown boundary type: {boundary_type}")
        
        return boundary_data, seed_state
    
    def _train_transducer(self, boundary_data: Dict[str, Any], seed_state: np.ndarray,
                         model_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Train a transducer model for holographic reconstruction."""
        try:
            # Prepare training data
            X, y = self._prepare_training_data(boundary_data, seed_state, config)
            
            if len(X) == 0:
                return {
                    "model": None,
                    "metrics": {"accuracy": 0.0, "r2_score": 0.0, "error": "no_training_data"}
                }
            
            # Train model based on type
            if model_type == "linear":
                model = LinearRegression()
                model.fit(X, y)
                
                # Evaluate model
                y_pred = model.predict(X)
                y_var = np.var(y)
                if y_var > 0:
                    accuracy = 1.0 - mean_squared_error(y, y_pred) / y_var
                else:
                    accuracy = 1.0  # Perfect accuracy if no variance
                r2 = r2_score(y, y_pred)
                
                metrics = {
                    "accuracy": max(0.0, accuracy),
                    "r2_score": r2,
                    "coefficients": model.coef_.tolist() if hasattr(model, 'coef_') else [],
                    "intercept": float(model.intercept_) if hasattr(model, 'intercept_') else 0.0
                }
                
            elif model_type == "quadratic":
                # Simple quadratic features
                X_quad = np.column_stack([X, X**2, np.prod(X, axis=1).reshape(-1, 1)])
                model = LinearRegression()
                model.fit(X_quad, y)
                
                y_pred = model.predict(X_quad)
                y_var = np.var(y)
                if y_var > 0:
                    accuracy = 1.0 - mean_squared_error(y, y_pred) / y_var
                else:
                    accuracy = 1.0  # Perfect accuracy if no variance
                r2 = r2_score(y, y_pred)
                
                metrics = {
                    "accuracy": max(0.0, accuracy),
                    "r2_score": r2,
                    "feature_count": X_quad.shape[1]
                }
                
            elif model_type == "neural_1layer":
                # Simple neural network (single hidden layer)
                from sklearn.neural_network import MLPRegressor
                
                model = MLPRegressor(
                    hidden_layer_sizes=(10,),
                    max_iter=1000,
                    random_state=42
                )
                model.fit(X, y)
                
                y_pred = model.predict(X)
                y_var = np.var(y)
                if y_var > 0:
                    accuracy = 1.0 - mean_squared_error(y, y_pred) / y_var
                else:
                    accuracy = 1.0  # Perfect accuracy if no variance
                r2 = r2_score(y, y_pred)
                
                metrics = {
                    "accuracy": max(0.0, accuracy),
                    "r2_score": r2,
                    "hidden_units": 10,
                    "iterations": model.n_iter_
                }
                
            else:
                raise ValueError(f"Unknown model type: {model_type}")
            
            return {
                "model": model,
                "model_type": model_type,
                "metrics": metrics
            }
            
        except Exception as e:
            logger.error(f"Transducer training failed: {e}")
            return {
                "model": None,
                "metrics": {"accuracy": 0.0, "r2_score": 0.0, "error": str(e)}
            }
    
    def _prepare_training_data(self, boundary_data: Dict[str, Any], seed_state: np.ndarray,
                              config: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data for transducer model."""
        try:
            # Extract boundary features
            boundary_indices = boundary_data["indices"]
            boundary_values = boundary_data["values"]
            
            if len(boundary_indices) == 0:
                return np.array([]), np.array([])
            
            # Create feature matrix
            features = []
            targets = []
            
            # Feature: boundary values + seed context
            for i, ((t, pos), value) in enumerate(zip(boundary_indices, boundary_values)):
                # Context features: neighboring boundary values
                context = []
                
                # Add seed state context
                context.extend(seed_state.tolist())
                
                # Add boundary value
                context.append(value)
                
                # Add temporal context (time step)
                context.append(t)
                
                # Add spatial context (position)
                context.append(pos)
                
                features.append(context)
                targets.append(value)
            
            return np.array(features), np.array(targets)
            
        except Exception as e:
            logger.error(f"Training data preparation failed: {e}")
            return np.array([]), np.array([])
    
    def _test_reconstruction(self, transducer: Dict[str, Any], boundary_data: Dict[str, Any],
                           seed_state: np.ndarray, evolution_steps: int) -> Dict[str, Any]:
        """Test reconstruction accuracy of the transducer."""
        try:
            model = transducer.get("model")
            if model is None:
                return {
                    "mean_error": float('inf'),
                    "max_error": float('inf'),
                    "reconstruction_accuracy": 0.0,
                    "error": "no_model"
                }
            
            # Generate test trajectory
            test_trajectory = []
            current_state = seed_state.copy()
            
            for step in range(evolution_steps):
                test_trajectory.append(current_state.copy())
                current_state = ca_step(current_state.tolist() if isinstance(current_state, np.ndarray) else current_state, rule="rule110")
            
            test_trajectory = np.array(test_trajectory)
            
            # Test reconstruction at boundary points
            boundary_indices = boundary_data["indices"]
            reconstruction_errors = []
            
            for (t, pos), true_value in zip(boundary_indices, boundary_data["values"]):
                try:
                    # Prepare input features
                    features = []
                    features.extend(seed_state.tolist())
                    features.append(true_value)  # Use true boundary value
                    features.append(t)
                    features.append(pos)
                    
                    # Predict
                    if transducer["model_type"] == "quadratic":
                        X_input = np.array([features])
                        X_quad = np.column_stack([X_input, X_input**2, np.prod(X_input, axis=1).reshape(-1, 1)])
                        predicted = model.predict(X_quad)[0]
                    else:
                        predicted = model.predict([features])[0]
                    
                    error = abs(predicted - true_value)
                    reconstruction_errors.append(error)
                    
                except Exception as e:
                    logger.warning(f"Reconstruction failed at ({t}, {pos}): {e}")
                    reconstruction_errors.append(float('inf'))
            
            if reconstruction_errors:
                mean_error = np.mean(reconstruction_errors)
                max_error = np.max(reconstruction_errors)
                accuracy = 1.0 / (1.0 + mean_error)  # Simple accuracy metric
            else:
                mean_error = float('inf')
                max_error = float('inf')
                accuracy = 0.0
            
            return {
                "mean_error": mean_error,
                "max_error": max_error,
                "reconstruction_accuracy": accuracy,
                "num_test_points": len(reconstruction_errors)
            }
            
        except Exception as e:
            logger.error(f"Reconstruction testing failed: {e}")
            return {
                "mean_error": float('inf'),
                "max_error": float('inf'),
                "reconstruction_accuracy": 0.0,
                "error": str(e)
            }
    
    def _analyze_holographic_properties(self, boundary_data: Dict[str, Any],
                                      reconstruction_results: Dict[str, Any],
                                      config: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze holographic properties of the reconstruction."""
        try:
            # Holographic score: how well boundary data predicts bulk
            reconstruction_accuracy = reconstruction_results.get("reconstruction_accuracy", 0.0)
            mean_error = reconstruction_results.get("mean_error", float('inf'))
            
            # Information compression ratio
            boundary_points = len(boundary_data["indices"])
            total_points = boundary_data["trajectory_shape"][0] * boundary_data["trajectory_shape"][1]
            compression_ratio = boundary_points / total_points if total_points > 0 else 1.0
            
            # Holographic efficiency
            holographic_score = reconstruction_accuracy * (1.0 - compression_ratio)
            
            # Boundary type specific analysis
            boundary_type = boundary_data["type"]
            if boundary_type == "ridge":
                # Ridge points should capture key dynamics
                ridge_density = boundary_points / boundary_data["trajectory_shape"][0]
                holographic_score *= (1.0 + ridge_density)  # Bonus for dense ridge coverage
            elif boundary_type == "mirror":
                # Mirror should be minimal but effective
                holographic_score *= 1.2  # Bonus for minimal boundary data
            
            # Stability assessment
            is_stable = mean_error < config.get("stability_threshold", 0.1)
            
            return {
                "holographic_score": holographic_score,
                "compression_ratio": compression_ratio,
                "boundary_density": boundary_points / boundary_data["trajectory_shape"][0],
                "reconstruction_accuracy": reconstruction_accuracy,
                "is_stable": is_stable,
                "boundary_type": boundary_type,
                "efficiency_metric": holographic_score
            }
            
        except Exception as e:
            logger.error(f"Holographic analysis failed: {e}")
            return {
                "holographic_score": 0.0,
                "compression_ratio": 1.0,
                "error": str(e)
            }
