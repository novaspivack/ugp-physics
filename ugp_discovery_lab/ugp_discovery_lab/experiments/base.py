"""
Base experiment class for UGP Discovery Lab.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List
import time
from functools import wraps
from ..core.logging import get_logger
from ..core.checkpoint import load_checkpoint, save_checkpoint, checkpoint_exists
from ..utils.io import compute_reproducibility_hash, pyify


def timing_decorator(func):
    """Decorator to add timing information to experiment methods."""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        start_time = time.time()
        result = func(self, *args, **kwargs)
        end_time = time.time()
        
        # Add timing info to result if it's a dict
        if isinstance(result, dict):
            result[f"{func.__name__}_runtime_seconds"] = end_time - start_time
        
        return result
    return wrapper


class Experiment(ABC):
    """
    Abstract base class for all UGP Discovery Lab experiments.
    
    Each experiment defines:
    - What tasks to run (via tasks() method)
    - How to run each task (via run_task() method)  
    - How to summarize results (via summarize() method)
    """
    
    def __init__(self, cfg: Dict[str, Any], root: Path):
        """
        Initialize experiment with configuration and root directory.
        
        Args:
            cfg: Experiment configuration dictionary
            root: Root directory for the lab
        """
        # CLI loads full YAML with a top-level `experiment:` block; experiments read
        # fields (name, rg, param_grid, tests, …) from that block. Normalize here so
        # experiments can use self.cfg consistently.
        self.raw_cfg = cfg
        if isinstance(cfg, dict) and "experiment" in cfg and isinstance(cfg["experiment"], dict):
            self.cfg = cfg["experiment"]
        else:
            self.cfg = cfg
        self.root = root
        self.logger = get_logger(f"experiment:{self.__class__.__name__}")
        
        # Ensure directories exist
        self.ensure_directories()
    
    def ensure_directories(self) -> None:
        """Ensure all necessary directories exist."""
        from ..core.config import ensure_dirs
        ensure_dirs(self.root)
    
    @abstractmethod
    def tasks(self) -> List[Dict[str, Any]]:
        """
        Return a list of atomic task dictionaries.
        
        Each task dict must contain:
        - 'task_id': unique identifier for the task
        - Any other task-specific parameters
        
        Returns:
            List of task dictionaries
        """
        pass
    
    @abstractmethod
    @timing_decorator
    def run_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a single task and return results.
        
        Args:
            task: Task dictionary with task_id and parameters
            
        Returns:
            Dictionary containing task results (must be JSON-serializable)
            Must include 'task_id' and 'success' fields
        """
        pass
    
    @abstractmethod
    @timing_decorator
    def summarize(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate per-task results into a suite summary.
        
        Args:
            results: List of task result dictionaries
            
        Returns:
            Dictionary containing summary statistics and analysis
        """
        pass
    
    def compute_reproducibility_hash(self, results: List[Dict[str, Any]]) -> str:
        """Compute reproducibility hash for this experiment run."""
        # Extract seeds from results
        seeds = []
        for result in results:
            if "seed" in result:
                seeds.append(result["seed"])
            elif "task_id" in result and "seed" in result.get("task_data", {}):
                seeds.append(result["task_data"]["seed"])
        
        # Extract input files (if any)
        input_files = []
        for result in results:
            if "input_files" in result:
                input_files.extend(result["input_files"])
        
        # Compute hash
        return compute_reproducibility_hash(
            config=self.cfg,
            input_files=input_files,
            seeds=seeds,
            experiment_name=self.__class__.__name__,
            experiment_version="0.1.0"
        )
    
    def is_long_running(self, task: Dict[str, Any]) -> bool:
        """
        Determine if a task should use checkpointing.
        
        Override this method to enable checkpointing for long-running tasks.
        
        Args:
            task: Task dictionary
            
        Returns:
            True if task should use checkpointing
        """
        # Default: enable checkpointing if task has 'steps' > 200
        return task.get('steps', 0) > 200
    
    def run_task_with_checkpointing(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a task with optional checkpointing support.
        
        Args:
            task: Task dictionary
            
        Returns:
            Task results dictionary
        """
        task_id = task['task_id']
        
        # Check for existing checkpoint
        if checkpoint_exists(self.root, task_id):
            self.logger.info(f"Found checkpoint for task {task_id}, attempting to resume...")
            checkpoint_data = load_checkpoint(self.root, task_id)
            if checkpoint_data:
                # Modify task to resume from checkpoint
                task = {**task, **checkpoint_data}
                self.logger.info(f"Resumed task {task_id} from checkpoint")
        
        try:
            # Run the task
            result = self.run_task(task)
            
            # Clear checkpoint on successful completion
            if checkpoint_exists(self.root, task_id):
                from ..core.checkpoint import clear_checkpoint
                clear_checkpoint(self.root, task_id)
                self.logger.debug(f"Cleared checkpoint for completed task {task_id}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Task {task_id} failed: {e}")
            
            # Save error state to checkpoint if this was a long-running task
            if self.is_long_running(task):
                error_state = {
                    'error': str(e),
                    'failed_at': task.get('current_step', 0)
                }
                save_checkpoint(self.root, task_id, error_state)
                self.logger.info(f"Saved error state for task {task_id}")
            
            # Return error result
            return {
                'task_id': task_id,
                'success': False,
                'error': str(e)
            }
    
    def get_run_directory(self, run_name: str) -> Path:
        """
        Get the directory for a specific run.
        
        Args:
            run_name: Name of the run
            
        Returns:
            Path to the run directory
        """
        from ..core.config import get_run_dir
        return get_run_dir(self.root, run_name)
    
    def save_artifact(self, artifact_data: Any, artifact_name: str, 
                     run_name: str, subdir: str = "artifacts") -> Path:
        """
        Save an artifact to the run directory.
        
        Args:
            artifact_data: Data to save
            artifact_name: Name for the artifact file
            run_name: Name of the run
            subdir: Subdirectory within the run directory
            
        Returns:
            Path to the saved artifact
        """
        run_dir = self.get_run_directory(run_name)
        artifact_dir = run_dir / subdir
        artifact_dir.mkdir(parents=True, exist_ok=True)
        
        artifact_path = artifact_dir / artifact_name
        
        # Save based on file extension
        if artifact_name.endswith('.json'):
            import json
            artifact_path.write_text(json.dumps(artifact_data, indent=2), encoding='utf-8')
        elif artifact_name.endswith('.csv'):
            import pandas as pd
            if isinstance(artifact_data, (list, dict)):
                df = pd.DataFrame(artifact_data)
                df.to_csv(artifact_path, index=False)
            else:
                artifact_path.write_text(str(artifact_data), encoding='utf-8')
        else:
            # Default: save as text
            artifact_path.write_text(str(artifact_data), encoding='utf-8')
        
        self.logger.info(f"Saved artifact: {artifact_path}")
        return artifact_path
    
    def validate_task(self, task: Dict[str, Any]) -> bool:
        """
        Validate a task dictionary.
        
        Override this method to add task-specific validation.
        
        Args:
            task: Task dictionary to validate
            
        Returns:
            True if task is valid
        """
        required_fields = ['task_id']
        for field in required_fields:
            if field not in task:
                self.logger.error(f"Task missing required field: {field}")
                return False
        return True
    
    def get_experiment_info(self) -> Dict[str, Any]:
        """
        Get information about this experiment.
        
        Returns:
            Dictionary with experiment metadata
        """
        return {
            'name': self.__class__.__name__,
            'description': self.cfg.get('description', 'No description provided'),
            'configuration': self.cfg,
            'root_directory': str(self.root)
        }
