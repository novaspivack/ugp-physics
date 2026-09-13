"""
Reversible UWCA implementation with history tracking for information preservation.
"""

from typing import List, Tuple, Optional, Dict, Any
from .uwca import ca_step, RULES


class ReversibleUWCA:
    """
    Reversible Universal Windowed Cellular Automaton with history tracking.
    
    This implements the Bennett trick for making CA updates reversible by
    preserving input history and using it for backward execution.
    """
    
    def __init__(self, width: int, rule: str = "rule110", wrap: bool = True):
        """
        Initialize reversible UWCA.
        
        Args:
            width: Width of the cellular automaton
            rule: CA rule to use
            wrap: Whether to use periodic boundary conditions
        """
        self.width = width
        self.rule = rule
        self.wrap = wrap
        self.history: List[List[Tuple[int, int, int]]] = []
        self.state_history: List[List[int]] = []
        self.step_count = 0
        
        if rule not in RULES:
            raise ValueError(f"Unknown rule: {rule}. Available: {list(RULES.keys())}")
    
    def forward_step(self, current_state: List[int]) -> List[int]:
        """
        Execute one forward step, preserving history for reversibility.
        
        Args:
            current_state: Current CA state
            
        Returns:
            Next CA state
        """
        if len(current_state) != self.width:
            raise ValueError(f"State width {len(current_state)} doesn't match CA width {self.width}")
        
        # Capture neighborhood history for this step
        neighborhoods = []
        for i in range(self.width):
            L = current_state[(i-1) % self.width] if self.wrap else (current_state[i-1] if i > 0 else 0)
            C = current_state[i]
            R = current_state[(i+1) % self.width] if self.wrap else (current_state[i+1] if i < self.width-1 else 0)
            neighborhoods.append((L, C, R))
        
        # Compute next state using standard CA rule
        next_state = ca_step(current_state, self.rule, self.wrap)
        
        # Store history
        self.history.append(neighborhoods)
        self.state_history.append(current_state.copy())
        self.step_count += 1
        
        return next_state
    
    def backward_step(self) -> Optional[List[int]]:
        """
        Execute one backward step using stored history.
        
        Returns:
            Previous CA state, or None if no history available
        """
        if not self.history or not self.state_history:
            return None
        
        # Get the most recent history
        neighborhoods = self.history.pop()
        previous_state = self.state_history.pop()
        self.step_count -= 1
        
        return previous_state
    
    def reset_history(self) -> None:
        """Clear all stored history."""
        self.history.clear()
        self.state_history.clear()
        self.step_count = 0
    
    def get_history_info(self) -> Dict[str, Any]:
        """
        Get information about stored history.
        
        Returns:
            Dictionary with history statistics
        """
        return {
            "steps_stored": len(self.history),
            "current_step": self.step_count,
            "rule": self.rule,
            "width": self.width,
            "wrap": self.wrap
        }
    
    def simulate_forward(self, initial_state: List[int], steps: int) -> List[List[int]]:
        """
        Simulate forward execution for multiple steps.
        
        Args:
            initial_state: Starting state
            steps: Number of steps to simulate
            
        Returns:
            List of all states (including initial)
        """
        states = [initial_state.copy()]
        current = initial_state.copy()
        
        for _ in range(steps):
            current = self.forward_step(current)
            states.append(current.copy())
        
        return states
    
    def simulate_backward(self, steps: int) -> List[List[int]]:
        """
        Simulate backward execution for multiple steps.
        
        Args:
            steps: Number of steps to go back
            
        Returns:
            List of states in reverse chronological order
        """
        states = []
        
        for _ in range(steps):
            prev_state = self.backward_step()
            if prev_state is None:
                break
            states.append(prev_state.copy())
        
        return states


def reversible_step(row: List[int], rule: str, history: Optional[List[Tuple[int, int, int]]] = None, 
                   wrap: bool = True) -> Tuple[List[int], List[Tuple[int, int, int]]]:
    """
    Execute one reversible CA step with history tracking.
    
    Args:
        row: Current CA state
        rule: CA rule to apply
        history: Optional existing history to extend
        wrap: Whether to use periodic boundary conditions
        
    Returns:
        Tuple of (next_state, updated_history)
    """
    if history is None:
        history = []
    
    # Capture neighborhoods for this step
    n = len(row)
    neighborhoods = []
    
    for i in range(n):
        L = row[(i-1) % n] if wrap else (row[i-1] if i > 0 else 0)
        C = row[i]
        R = row[(i+1) % n] if wrap else (row[i+1] if i < n-1 else 0)
        neighborhoods.append((L, C, R))
    
    # Compute next state
    next_state = ca_step(row, rule, wrap)
    
    # Update history
    history.extend(neighborhoods)
    
    return next_state, history


def uncompute_step(history: List[Tuple[int, int, int]], rule: str, wrap: bool = True) -> Optional[List[int]]:
    """
    Uncompute one CA step using history (reverse operation).
    
    Args:
        history: History of neighborhoods
        rule: CA rule that was applied
        wrap: Whether periodic boundary conditions were used
        
    Returns:
        Previous state, or None if history is insufficient
    """
    if rule not in RULES:
        raise ValueError(f"Unknown rule: {rule}. Available: {list(RULES.keys())}")
    
    ones = RULES[rule]
    n = len(history)
    
    if n == 0:
        return None
    
    # Reconstruct previous state from neighborhoods
    # This is a simplified version - full reconstruction requires more sophisticated methods
    prev_state = [0] * n
    
    for i, (L, C, R) in enumerate(history[-n:]):
        # Try to determine the previous state at position i
        # This is complex in general, but for some rules we can work backwards
        if rule == "rule110":
            # For Rule 110, we can sometimes work backwards
            # This is a simplified heuristic
            if C == 0 and (L, C, R) not in ones:
                prev_state[i] = 0
            elif C == 1 and (L, C, R) in ones:
                prev_state[i] = 1
            else:
                # Ambiguous case - use heuristics or require more context
                prev_state[i] = C  # Fallback to current state
    
    return prev_state


class EntropyTracker:
    """
    Track information entropy in reversible CA computations.
    
    This can be used to detect conserved quantities and measure
    information flow in UGP computations.
    """
    
    def __init__(self):
        self.entropy_history: List[float] = []
        self.state_counts: Dict[tuple, int] = {}
        self.total_states = 0
    
    def update(self, state: List[int]) -> float:
        """
        Update entropy tracking with a new state.
        
        Args:
            state: Current CA state
            
        Returns:
            Current entropy estimate
        """
        state_tuple = tuple(state)
        self.state_counts[state_tuple] = self.state_counts.get(state_tuple, 0) + 1
        self.total_states += 1
        
        # Calculate entropy: H = -sum(p_i * log2(p_i))
        entropy = 0.0
        for count in self.state_counts.values():
            if count > 0:
                p = count / self.total_states
                import math
                entropy -= p * math.log2(p) if p > 0 else 0
        
        self.entropy_history.append(entropy)
        return entropy
    
    def get_entropy_trend(self) -> Dict[str, Any]:
        """
        Analyze entropy trends.
        
        Returns:
            Dictionary with entropy statistics
        """
        if len(self.entropy_history) < 2:
            return {"current_entropy": 0.0, "entropy_change": 0.0, "trend": "insufficient_data"}
        
        current = self.entropy_history[-1]
        previous = self.entropy_history[-2]
        change = current - previous
        
        if abs(change) < 1e-10:
            trend = "stable"
        elif change > 0:
            trend = "increasing"
        else:
            trend = "decreasing"
        
        return {
            "current_entropy": current,
            "entropy_change": change,
            "trend": trend,
            "unique_states": len(self.state_counts),
            "total_observations": self.total_states
        }
    
    def reset(self) -> None:
        """Reset entropy tracking."""
        self.entropy_history.clear()
        self.state_counts.clear()
        self.total_states = 0
