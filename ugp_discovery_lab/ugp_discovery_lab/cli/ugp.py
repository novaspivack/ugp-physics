"""
Main CLI interface for UGP Discovery Lab.
"""

import argparse
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from ..core.config import load_yaml, ensure_dirs, default_workers, validate_config
from ..core.registry import get_experiment, list_experiments
from ..core.workers import SafePool
from ..core.threading_pool import run_with_threading
from ..core.reporting import write_json_report, create_run_summary
from ..core.logging import get_logger, setup_root_logging


def _run_task_worker(args):
    """Top-level worker function for multiprocessing."""
    task, cfg, root_str, exp_name = args
    root = Path(root_str)
    
    # Get experiment class
    exp_cls = get_experiment(exp_name)
    exp = exp_cls(cfg, root)
    
    return exp.run_task_with_checkpointing(task)

# Import DataIntegrityError with fallback
try:
    from ..diagnostics.data_linter import DataIntegrityError  # type: ignore
except ImportError:
    class DataIntegrityError(Exception):  # type: ignore
        """Fallback DataIntegrityError if data_linter module is not available."""
        pass


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="UGP Discovery Lab - Universal Generative Principle Research Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ugp run-experiment -c configs/experiments/gte_lucas.yaml
  ugp run-suite -c configs/suites/starter_suite.yaml --workers 4
  ugp list-experiments
  ugp list-suites
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Run experiment command
    run_exp_parser = subparsers.add_parser("run-experiment", help="Run a single experiment")
    run_exp_parser.add_argument("-c", "--config", required=True, help="Experiment configuration file")
    run_exp_parser.add_argument("--workers", type=int, default=None, help="Number of worker processes")
    run_exp_parser.add_argument("--run-name", help="Custom run name (default: auto-generated)")
    run_exp_parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    run_exp_parser.add_argument("--plots", action="store_true", help="Generate plots (requires matplotlib)")
    run_exp_parser.add_argument("--analysis-only", action="store_true", help="Analysis-only mode: prohibit synthetic data generation")
    
    # Run suite command
    run_suite_parser = subparsers.add_parser("run-suite", help="Run a test suite")
    run_suite_parser.add_argument("-c", "--config", required=True, help="Suite configuration file")
    run_suite_parser.add_argument("--workers", type=int, default=None, help="Number of worker processes")
    run_suite_parser.add_argument("--run-name", help="Custom run name (default: auto-generated)")
    run_suite_parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    run_suite_parser.add_argument("--plots", action="store_true", help="Generate plots (requires matplotlib)")
    
    # List commands
    subparsers.add_parser("list-experiments", help="List available experiments")
    subparsers.add_parser("list-suites", help="List available test suites")
    subparsers.add_parser("list-checkpoints", help="List available checkpoints")
    
    # Documentation command
    docs_parser = subparsers.add_parser("docs", help="Generate documentation")
    docs_parser.add_argument("--output", help="Output directory for documentation", default="docs")
    
    # Resume command
    resume_parser = subparsers.add_parser("resume", help="Resume a checkpointed run")
    resume_parser.add_argument("-c", "--config", required=True, help="Original configuration file")
    resume_parser.add_argument("--workers", type=int, default=None, help="Number of worker processes")
    resume_parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    # Clean command
    clean_parser = subparsers.add_parser("clean", help="Clean up old checkpoints and logs")
    clean_parser.add_argument("--checkpoints", action="store_true", help="Clean checkpoints only")
    clean_parser.add_argument("--logs", action="store_true", help="Clean logs only")
    clean_parser.add_argument("--artifacts", action="store_true", help="Clean artifacts only")
    clean_parser.add_argument("--all", action="store_true", help="Clean everything")
    clean_parser.add_argument("--max-age-days", type=int, default=7, help="Maximum age of files to keep")
    clean_parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Set up logging
    log_level = "DEBUG" if getattr(args, "verbose", False) else "INFO"
    setup_root_logging(level=getattr(logging, log_level, logging.INFO))
    logger = get_logger("CLI")
    
    # Set up root directory
    root = Path(".").resolve()
    ensure_dirs(root)
    
    try:
        if args.command == "list-experiments":
            return list_experiments_command(logger)
        elif args.command == "list-suites":
            return list_suites_command(root, logger)
        elif args.command == "list-checkpoints":
            return list_checkpoints_command(root, logger)
        elif args.command == "run-experiment":
            return run_experiment_command(args, root, logger)
        elif args.command == "run-suite":
            return run_suite_command(args, root, logger)
        elif args.command == "resume":
            return resume_command(args, root, logger)
        elif args.command == "clean":
            return clean_command(args, root, logger)
        elif args.command == "docs":
            return docs_command(args, root, logger)
        else:
            logger.error(f"Unknown command: {args.command}")
            return 1
            
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if getattr(args, "verbose", False):
            import traceback
            logger.error(traceback.format_exc())
        return 1


def list_experiments_command(logger):
    """List available experiments."""
    logger.info("Available experiments:")
    try:
        experiments = list_experiments()
        if experiments:
            for exp_name in experiments:
                logger.info(f"  - {exp_name}")
        else:
            logger.info("  No experiments registered")
        return 0
    except Exception as e:
        logger.error(f"Error listing experiments: {e}")
        return 1


def list_suites_command(root: Path, logger):
    """List available test suites."""
    logger.info("Available test suites:")
    try:
        suites_dir = root / "configs" / "suites"
        if suites_dir.exists():
            suite_files = list(suites_dir.glob("*.yaml"))
            if suite_files:
                for suite_file in sorted(suite_files):
                    logger.info(f"  - {suite_file.name}")
            else:
                logger.info("  No suite files found")
        else:
            logger.info("  Configs directory not found")
        return 0
    except Exception as e:
        logger.error(f"Error listing suites: {e}")
        return 1


def list_checkpoints_command(root: Path, logger):
    """List available checkpoints."""
    logger.info("Available checkpoints:")
    try:
        from ..core.checkpoint import list_checkpoints
        checkpoints = list_checkpoints(root)
        if checkpoints:
            for ckpt in checkpoints:
                logger.info(f"  - {ckpt}")
        else:
            logger.info("  No checkpoints found")
        return 0
    except Exception as e:
        logger.error(f"Error listing checkpoints: {e}")
        return 1


def run_experiment_command(args, root: Path, logger):
    """Run a single experiment."""
    try:
        # Load and validate configuration
        config = load_yaml(args.config)
        validate_config(config)
        
        # Check analysis-only mode
        if args.analysis_only:
            analysis_only_validation(config, logger)
        
        # Generate run name if not provided
        run_name = args.run_name or f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Get experiment class and create instance
        exp_name = config["experiment"]["name"]
        exp_cls = get_experiment(exp_name)
        exp = exp_cls(config, root)
        
        # Generate tasks
        tasks = exp.tasks()
        if not tasks:
            logger.warning("No tasks generated for experiment")
            return 0
        
        # Set up workers
        workers = args.workers or default_workers()
        
        logger.info(f"Running experiment '{exp_name}' with {len(tasks)} tasks, workers={workers}")
        logger.info(f"Run name: {run_name}")
        
        # Run tasks
        results = []
        if workers == 1:
            # Single-threaded execution
            for i, task in enumerate(tasks):
                logger.info(f"Running task {i+1}/{len(tasks)}: {task['task_id']}")
                result = exp.run_task_with_checkpointing(task)
                results.append(result)
                if result.get("success", False) or result.get("status") in ["success", "ok"]:
                    logger.info(f"Task {task['task_id']} completed successfully")
                else:
                    logger.error(f"Task {task['task_id']} failed: {result.get('error', 'Unknown error')}")
        else:
            # Threading-based execution (avoids multiprocessing resource tracker issues)
            try:
                logger.info(f"Starting threading with {workers} workers")
                
                # Create a list of (task, experiment_config, root, exp_name) tuples
                task_args = [(task, exp.cfg, str(exp.root), exp_name) for task in tasks]
                
                # Use threading instead of multiprocessing to avoid resource tracker issues
                results = run_with_threading(_run_task_worker, task_args, max_workers=workers, title=exp_name)
                    
                # Log results
                for i, result in enumerate(results):
                    task_id = tasks[i]['task_id']
                    if result.get("success", False) or result.get("status") in ["success", "ok"]:
                        logger.info(f"Task {task_id} completed successfully")
                    else:
                        logger.error(f"Task {task_id} failed: {result.get('error', 'Unknown error')}")
                        
            except Exception as e:
                logger.error(f"Threading execution failed: {e}")
                logger.info("Falling back to single-threaded execution")
                results = []
                for i, task in enumerate(tasks):
                    logger.info(f"Running task {i+1}/{len(tasks)}: {task['task_id']}")
                    try:
                        result = exp.run_task_with_checkpointing(task)
                        results.append(result)
                        if result.get("success", False) or result.get("status") in ["success", "ok"]:
                            logger.info(f"Task {task['task_id']} completed successfully")
                        else:
                            logger.error(f"Task {task['task_id']} failed: {result.get('error', 'Unknown error')}")
                    except Exception as task_error:
                        logger.error(f"Task {task['task_id']} crashed: {task_error}")
                        results.append({
                            "task_id": task['task_id'],
                            "success": False,
                            "error": str(task_error),
                            "status": "error"
                        })
        
        # Generate summary
        summary = exp.summarize(results)
        
        # Save results
        run_dir = root / "UGP_discovery_lab_runs" / run_name
        run_dir.mkdir(parents=True, exist_ok=True)
        
        # Save detailed results
        results_file = write_json_report(run_dir, "experiment_results", {
            "run_name": run_name,
            "experiment_name": exp_name,
            "configuration": config,
            "results": results,
            "summary": summary,
            "timestamp": datetime.now().isoformat()
        }, config)
        
        # Create summary report
        create_run_summary(run_dir, run_name, {
            "total_tasks": len(tasks),
            "successful_tasks": summary.get("successful_tasks", 0),
            "failed_tasks": summary.get("failed_tasks", 0),
            "experiments": [{
                "experiment": exp_name,
                "summary": summary
            }],
            "configuration": config
        })
        
        logger.info(f"Experiment completed. Results saved to: {run_dir}")
        # Calculate success rate from summary data
        total_tasks = summary.get('total_tasks', 0)
        successful_tasks = summary.get('successful_tasks', 0)
        success_rate = (successful_tasks / total_tasks * 100) if total_tasks > 0 else 0
        logger.info(f"Success rate: {success_rate:.1f}%")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error running experiment: {e}")
        return 1


def run_suite_command(args, root: Path, logger):
    """Run a test suite."""
    try:
        # Load suite configuration
        suite_config = load_yaml(args.config)
        
        # Generate run name if not provided
        run_name = args.run_name or f"suite_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Set up workers
        workers = args.workers or default_workers()
        
        logger.info(f"Running test suite with workers={workers}")
        logger.info(f"Run name: {run_name}")
        
        overall_results = {
            "run_name": run_name,
            "suite_config": suite_config,
            "experiments": [],
            "total_tasks": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "timestamp": datetime.now().isoformat()
        }
        
        # Run each experiment in the suite
        for exp_config in suite_config.get("experiments", []):
            exp_name = exp_config["name"]
            logger.info(f"Running experiment: {exp_name}")
            
            try:
                # Load experiment configuration from file
                exp_config_path = exp_config.get("config")
                if not exp_config_path:
                    logger.error(f"No config path specified for experiment {exp_name}")
                    continue
                
                # Load the actual experiment configuration
                actual_exp_config = load_yaml(exp_config_path)
                
                # Create experiment instance with full configuration
                exp_cls = get_experiment(exp_name)
                exp = exp_cls(actual_exp_config, root)
                
                # Generate tasks
                tasks = exp.tasks()
                overall_results["total_tasks"] += len(tasks)
                
                if not tasks:
                    logger.warning(f"No tasks generated for experiment {exp_name}")
                    continue
                
                logger.info(f"Experiment {exp_name}: {len(tasks)} tasks")
                
                # Run tasks
                results = []
                if workers == 1:
                    for task in tasks:
                        result = exp.run_task_with_checkpointing(task)
                        results.append(result)
                else:
                    try:
                        # Use threading instead of multiprocessing to avoid resource tracker issues
                        task_args = [(task, exp.cfg, str(exp.root), exp_name) for task in tasks]
                        results = run_with_threading(_run_task_worker, task_args, max_workers=workers, title=exp_name)
                    except Exception as e:
                        logger.error(f"Threading failed for {exp_name}: {e}")
                        logger.info(f"Falling back to single-threaded execution for {exp_name}")
                        results = []
                        for task in tasks:
                            try:
                                result = exp.run_task_with_checkpointing(task)
                                results.append(result)
                            except Exception as task_error:
                                logger.error(f"Task {task['task_id']} crashed: {task_error}")
                                results.append({
                                    "task_id": task['task_id'],
                                    "success": False,
                                    "error": str(task_error),
                                    "status": "error"
                                })
                
                # Generate summary
                summary = exp.summarize(results)
                overall_results["experiments"].append({
                    "experiment": exp_name,
                    "summary": summary
                })
                
                overall_results["successful_tasks"] += summary.get("successful_tasks", 0)
                overall_results["failed_tasks"] += summary.get("failed_tasks", 0)
                
                logger.info(f"Experiment {exp_name} completed")
                
            except Exception as e:
                logger.error(f"Error running experiment {exp_name}: {e}")
                overall_results["experiments"].append({
                    "experiment": exp_name,
                    "error": str(e)
                })
        
        # Save suite results
        run_dir = root / "UGP_discovery_lab_runs" / run_name
        run_dir.mkdir(parents=True, exist_ok=True)
        
        write_json_report(run_dir, "suite_results", overall_results, suite_config)
        create_run_summary(run_dir, run_name, overall_results)
        
        logger.info(f"Suite completed. Results saved to: {run_dir}")
        if overall_results['total_tasks'] > 0:
            success_rate = overall_results['successful_tasks']/overall_results['total_tasks']*100
            logger.info(f"Total success rate: {success_rate:.1f}%")
        else:
            logger.info("No tasks run")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error running suite: {e}")
        return 1


def resume_command(args, root: Path, logger):
    """Resume a checkpointed run."""
    logger.info("Resume functionality - checkpoints will be automatically detected and used")
    logger.info("Running with original configuration...")
    
    # For now, just run the original command
    if "experiment" in args.config.lower():
        return run_experiment_command(args, root, logger)
    else:
        return run_suite_command(args, root, logger)


def clean_command(args, root: Path, logger):
    """Clean up old files."""
    try:
        from ..utils.io import cleanup_files
        
        if args.dry_run:
            logger.info("DRY RUN - showing what would be cleaned up")
        
        total_removed = 0
        
        # Determine what to clean
        clean_all = args.all or (not any([args.checkpoints, args.logs, args.artifacts]))
        
        if clean_all or args.checkpoints:
            removed_checkpoints = cleanup_files(
                str(root / "UGP_discovery_lab_runs" / "**" / "checkpoints"),
                args.max_age_days, args.dry_run, logger
            )
            total_removed += removed_checkpoints
        
        if clean_all or args.logs:
            removed_logs = cleanup_files(
                str(root / "UGP_discovery_lab_runs" / "**" / "results" / "logs"),
                args.max_age_days, args.dry_run, logger
            )
            total_removed += removed_logs
        
        if clean_all or args.artifacts:
            removed_artifacts = cleanup_files(
                str(root / "UGP_discovery_lab_runs" / "**" / "results" / "artifacts"),
                args.max_age_days, args.dry_run, logger
            )
            total_removed += removed_artifacts
        
        if args.dry_run:
            logger.info(f"Would remove {total_removed} files total")
        else:
            logger.info(f"Removed {total_removed} files total")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        return 1


def docs_command(args, root: Path, logger):
    """Generate documentation."""
    try:
        from ..utils.docs import generate_experiment_docs
        
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Generating documentation in {output_dir}")
        
        # Generate experiment documentation
        docs_path = generate_experiment_docs(output_dir)
        
        logger.info(f"Documentation generated: {docs_path}")
        return 0
        
    except Exception as e:
        logger.error(f"Error generating documentation: {e}")
        return 1


def analysis_only_validation(config: Dict[str, Any], logger) -> None:
    """
    Validate that configuration is suitable for analysis-only mode.
    
    Args:
        config: Configuration dictionary
        logger: Logger instance
        
    Raises:
        ValueError: If configuration is not suitable for analysis-only mode
    """
    
    # Check if inputs.runs is empty or points to synthetic data
    # Look in the experiment configuration
    experiment_config = config.get("experiment", {})
    inputs = experiment_config.get("inputs", {})
    runs = inputs.get("runs", [])
    
    if not runs:
        raise DataIntegrityError(
            "Analysis-only mode requires non-empty inputs.runs. "
            "No input data sources specified."
        )
    
    # Check if any runs point to synthetic data
    synthetic_patterns = [
        "synthetic", "neutral", "generated", "test_data"
    ]
    
    for run_path in runs:
        if isinstance(run_path, str):
            for pattern in synthetic_patterns:
                if pattern.lower() in run_path.lower():
                    raise DataIntegrityError(
                        f"Analysis-only mode prohibits synthetic data sources. "
                        f"Found synthetic pattern '{pattern}' in run path: {run_path}"
                    )
    
    # Check for data generation sections that would create synthetic data
    data_generation_sections = ["generator", "neutral", "synthesis", "test_data"]
    
    for section in data_generation_sections:
        if section in config:
            raise DataIntegrityError(
                f"Analysis-only mode prohibits data generation sections. "
                f"Found '{section}' section in configuration."
            )
    
    # Check for run configuration that might generate data
    run_config = config.get("run", {})
    if "steps" in run_config or "seed" in run_config:
        logger.warning(
            "Analysis-only mode: run configuration found. "
            "This may indicate data generation capability."
        )
    
    logger.info("✅ Analysis-only validation passed - configuration suitable for real data analysis")


if __name__ == "__main__":
    sys.exit(main())
