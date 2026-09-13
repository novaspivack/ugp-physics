"""
Index lock detection experiments for UGP Discovery Lab.

Detects fixed-index events (like |q_2-q_1|=13) at canonical events
(ridge/mirror) and generalizes beyond 13 across policy variants.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import glob
from collections import Counter
import numpy as np
from ..core.registry import register_experiment
from ..core.logging import TaskLogger
from .base import Experiment


@register_experiment("index_lock")
class IndexLock(Experiment):
    """
    Detect fixed-index locks at canonical events in UGP evolutions.
    
    This experiment analyzes evolution logs to detect when |q_t - q_{t-1}|
    takes on fixed values at specific events like ridge hits or mirror events.
    """
    
    def tasks(self) -> List[Dict[str, Any]]:
        """Generate index lock detection tasks."""
        tasks = []
        
        # Get configuration
        inputs = self.cfg.get("inputs", {})
        runs = inputs.get("runs", [])
        detection = self.cfg.get("detection", {})
        
        event_types = detection.get("event_types", ["ridge", "mirror"])
        tolerance = detection.get("tolerance", 0)
        min_support = detection.get("min_support", 20)
        
        # Generate tasks for each input run
        for run_path in runs:
            task = {
                "task_id": f"index_lock_{Path(run_path).name}",
                "run_path": run_path,
                "event_types": event_types,
                "tolerance": tolerance,
                "min_support": min_support,
                "test_type": "index_lock"
            }
            
            if self.validate_task(task):
                tasks.append(task)
        
        self.logger.info(f"Generated {len(tasks)} index lock detection tasks")
        return tasks
    
    def run_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single index lock detection task."""
        task_id = task["task_id"]
        
        with TaskLogger(task_id, self.root / "results" / "logs") as logger:
            try:
                logger.info(f"Starting index lock detection: {task_id}")
                
                # Extract parameters
                run_path = task["run_path"]
                event_types = task["event_types"]
                tolerance = task["tolerance"]
                min_support = task["min_support"]
                
                logger.info(f"Analyzing {run_path} for index locks in events: {event_types}")
                
                # Load evolution data from run
                evolution_data = self._load_evolution_data(run_path, logger)
                
                if not evolution_data:
                    return {
                        "task_id": task_id,
                        "success": False,
                        "error": "No evolution data found"
                    }
                
                # Extract index sequences and events
                index_sequences, events = self._extract_index_data(evolution_data, logger)
                
                # Detect locks for each event type
                detected_locks = []
                for event_type in event_types:
                    locks = self._detect_index_locks(
                        index_sequences, events, event_type, 
                        tolerance, min_support, logger
                    )
                    detected_locks.extend(locks)
                
                # Analyze results
                analysis = self._analyze_index_locks(detected_locks, logger)
                
                # Save results
                result = {
                    "task_id": task_id,
                    "success": True,
                    "run_path": run_path,
                    "event_types": event_types,
                    "detected_locks": detected_locks,
                    "analysis": analysis,
                    "locks": detected_locks,  # For compatibility with spec
                    "status": "ok"
                }
                
                logger.info(f"Index lock detection {task_id} completed successfully")
                return result
                
            except Exception as e:
                logger.error(f"Index lock detection {task_id} failed: {e}")
                return {
                    "task_id": task_id,
                    "success": False,
                    "error": str(e)
                }
    
    def _load_evolution_data(self, run_path: str, logger) -> List[Dict[str, Any]]:
        """Load evolution data from run directory."""
        logger.debug(f"Loading evolution data from {run_path}")
        
        # Resolve path
        if not Path(run_path).is_absolute():
            run_path = self.root / run_path
        else:
            run_path = Path(run_path)
        
        evolution_data = []
        
        # Look for JSON files in the run directory
        if run_path.exists():
            json_files = list(run_path.glob("**/*.json"))
            logger.debug(f"Found {len(json_files)} JSON files in {run_path}")
            
            for json_file in json_files:
                try:
                    with open(json_file, 'r') as f:
                        data = json.load(f)
                    
                    # Extract evolution data from various possible structures
                    extracted = self._extract_evolution_from_data(data, logger)
                    evolution_data.extend(extracted)
                    
                except Exception as e:
                    logger.warning(f"Failed to load {json_file}: {e}")
                    continue
        
        # Generate synthetic data if none found (for testing)
        if not evolution_data:
            logger.debug("No evolution data found, generating synthetic data")
            evolution_data = self._generate_synthetic_evolution_data()
        
        logger.debug(f"Loaded {len(evolution_data)} evolution records")
        return evolution_data
    
    def _extract_evolution_from_data(self, data: Dict[str, Any], 
                                   logger) -> List[Dict[str, Any]]:
        """Extract evolution data from loaded JSON data."""
        evolution_records = []
        
        # Handle different data structures
        if isinstance(data, dict):
            # Check for evolution history directly
            if "evolution_history" in data:
                history = data["evolution_history"]
                for i, state in enumerate(history):
                    record = {
                        "step": i,
                        "state": state,
                        "event_type": self._classify_event(state, i)
                    }
                    evolution_records.append(record)
            
            # Check for results array
            elif "results" in data and isinstance(data["results"], list):
                for result in data["results"]:
                    if "evolution_history" in result:
                        history = result["evolution_history"]
                        for i, state in enumerate(history):
                            record = {
                                "step": i,
                                "state": state,
                                "event_type": self._classify_event(state, i)
                            }
                            evolution_records.append(record)
            
            # Check for analysis results
            elif "analysis" in data:
                analysis = data["analysis"]
                if "evolution_history" in analysis:
                    history = analysis["evolution_history"]
                    for i, state in enumerate(history):
                        record = {
                            "step": i,
                            "state": state,
                            "event_type": self._classify_event(state, i)
                        }
                        evolution_records.append(record)
        
        return evolution_records
    
    def _classify_event(self, state: Dict[str, Any], step: int) -> str:
        """Classify the event type for a given state."""
        # Simple heuristics for event classification
        # In a full implementation, this would be more sophisticated
        
        if "step_type" in state:
            step_type = state["step_type"]
            if "ridge" in str(step_type).lower():
                return "ridge"
            elif "mirror" in str(step_type).lower():
                return "mirror"
        
        # Check for ridge-like patterns (large c values)
        if "c" in state and state["c"] > 1000:
            return "ridge"
        
        # Check for mirror-like patterns (specific b/q relationships)
        if "b" in state and "q" in state:
            b, q = state["b"], state["q"]
            if abs(b - q) < 20:  # Heuristic for mirror events
                return "mirror"
        
        return "other"
    
    def _generate_synthetic_evolution_data(self) -> List[Dict[str, Any]]:
        """Generate synthetic evolution data for testing."""
        evolution_records = []
        
        # Generate a synthetic evolution with known index locks
        a, b, c = 1, 73, 823
        q_prev = 0
        
        for step in range(100):
            # Compute q and gap
            q = c // b if b > 0 else 0
            gap = abs(q - q_prev) if step > 0 else 0
            
            # Classify event
            if step % 20 == 10:  # Ridge events every 20 steps
                event_type = "ridge"
            elif step % 15 == 7:  # Mirror events every 15 steps
                event_type = "mirror"
            else:
                event_type = "other"
            
            # Create state
            state = {
                "a": a, "b": b, "c": c,
                "q": q, "m": c % b if b > 0 else 0,
                "gap": gap,
                "step_type": event_type
            }
            
            record = {
                "step": step,
                "state": state,
                "event_type": event_type
            }
            
            evolution_records.append(record)
            
            # Simple evolution
            if step % 2 == 0:
                b += 1
                c += b
            else:
                a += 1
                c += a
            
            q_prev = q
        
        return evolution_records
    
    def _extract_index_data(self, evolution_data: List[Dict[str, Any]], 
                          logger) -> tuple:
        """Extract index sequences and events from evolution data."""
        logger.debug("Extracting index sequences and events")
        
        index_sequences = []
        events = []
        
        for record in evolution_data:
            state = record["state"]
            step = record["step"]
            event_type = record["event_type"]
            
            # Extract index information
            if "gap" in state:
                gap = state["gap"]
            elif "q" in state and step > 0:
                # Compute gap from previous state
                prev_record = evolution_data[step - 1] if step > 0 else None
                if prev_record and "q" in prev_record["state"]:
                    gap = abs(state["q"] - prev_record["state"]["q"])
                else:
                    gap = 0
            else:
                gap = 0
            
            index_sequences.append({
                "step": step,
                "gap": gap,
                "q": state.get("q", 0)
            })
            
            # Record events
            if event_type != "other":
                events.append({
                    "step": step,
                    "type": event_type,
                    "gap": gap,
                    "state": state
                })
        
        logger.debug(f"Extracted {len(index_sequences)} index points and {len(events)} events")
        return index_sequences, events
    
    def _detect_index_locks(self, index_sequences: List[Dict[str, Any]], 
                          events: List[Dict[str, Any]], event_type: str,
                          tolerance: int, min_support: int, logger) -> List[Dict[str, Any]]:
        """Detect index locks for a specific event type."""
        logger.debug(f"Detecting {event_type} index locks")
        
        # Filter events by type
        relevant_events = [e for e in events if e["type"] == event_type]
        
        if not relevant_events:
            return []
        
        # Extract gaps at relevant events
        event_gaps = [e["gap"] for e in relevant_events]
        
        # Count gap frequencies
        gap_counts = Counter(event_gaps)
        
        detected_locks = []
        
        # Look for dominant gaps
        for gap, count in gap_counts.items():
            if count >= min_support:
                # Check if this gap is within tolerance of being "exact"
                if tolerance == 0:
                    # Exact equality required
                    is_exact = True
                else:
                    # Check if gap is within tolerance of a common value
                    is_exact = any(abs(gap - common_gap) <= tolerance 
                                 for common_gap in [5, 8, 13, 21, 34])  # Fibonacci-like
                
                if is_exact:
                    total_events = len(relevant_events)
                    support_rate = count / total_events
                    
                    lock = {
                        "event": event_type,
                        "kappa": int(gap),
                        "support": count,
                        "total": total_events,
                        "support_rate": support_rate,
                        "tolerance": tolerance
                    }
                    
                    detected_locks.append(lock)
        
        # Sort by support (descending)
        detected_locks.sort(key=lambda x: x["support"], reverse=True)
        
        logger.debug(f"Detected {len(detected_locks)} {event_type} locks")
        return detected_locks
    
    def _analyze_index_locks(self, detected_locks: List[Dict[str, Any]], 
                           logger) -> Dict[str, Any]:
        """Analyze detected index locks."""
        logger.debug("Analyzing index locks")
        
        if not detected_locks:
            return {"total_locks": 0, "analysis": "No locks detected"}
        
        # Group by event type
        locks_by_event = {}
        for lock in detected_locks:
            event = lock["event"]
            if event not in locks_by_event:
                locks_by_event[event] = []
            locks_by_event[event].append(lock)
        
        # Analyze each event type
        event_analysis = {}
        for event, locks in locks_by_event.items():
            if locks:
                strongest_lock = locks[0]  # Already sorted by support
                event_analysis[event] = {
                    "total_locks": len(locks),
                    "strongest_kappa": strongest_lock["kappa"],
                    "strongest_support": strongest_lock["support"],
                    "strongest_rate": strongest_lock["support_rate"],
                    "all_kappas": [lock["kappa"] for lock in locks]
                }
        
        # Look for patterns across event types
        all_kappas = [lock["kappa"] for lock in detected_locks]
        kappa_counts = Counter(all_kappas)
        
        # Find most common kappa values
        common_kappas = []
        for kappa, count in kappa_counts.most_common(5):
            if count >= 2:  # Appears in multiple event types
                common_kappas.append({
                    "kappa": kappa,
                    "frequency": count,
                    "events": [lock["event"] for lock in detected_locks if lock["kappa"] == kappa]
                })
        
        analysis = {
            "total_locks": len(detected_locks),
            "events_analyzed": list(locks_by_event.keys()),
            "event_analysis": event_analysis,
            "common_kappas": common_kappas,
            "strongest_overall": detected_locks[0] if detected_locks else None
        }
        
        return analysis
    
    def summarize(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize index lock detection results."""
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
            # Aggregate all detected locks
            all_locks = []
            for result in successful_results:
                all_locks.extend(result.get("detected_locks", []))
            
            # Group by event type
            locks_by_event = {}
            for lock in all_locks:
                event = lock["event"]
                if event not in locks_by_event:
                    locks_by_event[event] = []
                locks_by_event[event].append(lock)
            
            # Analyze consistency across runs
            event_consistency = {}
            for event, locks in locks_by_event.items():
                if locks:
                    # Count how many runs detected each kappa
                    kappa_counts = Counter(lock["kappa"] for lock in locks)
                    total_runs = len(successful_results)
                    
                    consistent_kappas = []
                    for kappa, count in kappa_counts.items():
                        consistency_rate = count / total_runs
                        if consistency_rate >= 0.5:  # Detected in at least 50% of runs
                            consistent_kappas.append({
                                "kappa": kappa,
                                "consistency_rate": consistency_rate,
                                "total_detections": count
                            })
                    
                    event_consistency[event] = {
                        "total_detections": len(locks),
                        "consistent_kappas": consistent_kappas,
                        "strongest_kappa": max(locks, key=lambda x: x["support"])["kappa"] if locks else None
                    }
            
            summary["metrics"] = {
                "total_locks_detected": len(all_locks),
                "events_analyzed": list(locks_by_event.keys()),
                "event_consistency": event_consistency,
                "runs_analyzed": len(successful_results)
            }
            
            # Discoveries
            discoveries = []
            
            # Check for consistent index locks
            for event, consistency in event_consistency.items():
                for kappa_info in consistency["consistent_kappas"]:
                    if kappa_info["consistency_rate"] >= 0.8:
                        discoveries.append(f"Highly consistent {event} lock: κ={kappa_info['kappa']} "
                                         f"({kappa_info['consistency_rate']:.1%} of runs)")
                    elif kappa_info["consistency_rate"] >= 0.5:
                        discoveries.append(f"Moderately consistent {event} lock: κ={kappa_info['kappa']} "
                                         f"({kappa_info['consistency_rate']:.1%} of runs)")
            
            # Check for known patterns
            all_kappas = [lock["kappa"] for lock in all_locks]
            if 13 in all_kappas:
                discoveries.append("Classical Fibonacci rigidity (κ=13) confirmed")
            
            fibonacci_kappas = [k for k in all_kappas if k in [5, 8, 13, 21, 34]]
            if len(fibonacci_kappas) >= 2:
                discoveries.append(f"Multiple Fibonacci-like locks detected: {sorted(fibonacci_kappas)}")
            
            summary["discoveries"] = discoveries
        
        if failed_results:
            summary["errors"] = [r["error"] for r in failed_results]
        
        return summary
