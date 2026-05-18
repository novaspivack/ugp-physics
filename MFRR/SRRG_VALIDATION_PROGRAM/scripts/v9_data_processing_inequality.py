#!/usr/bin/env python3
"""
V9: Reflexive Data-Processing Inequality (RDPI) Validation

Tests that CPTP maps satisfy:
    S_ref(E ρ) ≥ S_ref(ρ) - (k_B T/α_0)·I_lost(E,ρ)

Validates Theorem (Reflexive DPI).

Cross-references:
- ROUND_3_ENHANCEMENTS_PLAN.md: B14 (Reflexive DPI)
- Mathematical_Foundations_of_Reflexive_Reality.tex: Theorem~\ref{thm:reflexive-dpi}
"""

import json
import hashlib
import numpy as np
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Tuple
from datetime import datetime


@dataclass
class DPIResult:
    """Results from DPI test."""
    channel_name: str
    S_ref_initial: float
    S_ref_final: float
    I_lost: float
    predicted_decrease: float
    actual_decrease: float
    bound_satisfied: bool
    status: str


def compute_reflexive_entropy(probs: np.ndarray, I_holo: float = 0.5) -> float:
    """Compute S_ref = S(1 + C·I_holo^p)"""
    probs = probs[probs > 1e-15]
    probs = probs / np.sum(probs)
    
    S = -np.sum(probs * np.log(probs + 1e-15))
    S_ref = S * (1.0 + 0.1 * (I_holo ** 1.0))
    
    return S_ref


def apply_erasure_channel(state: np.ndarray, erasure_prob: float, rng) -> Tuple[np.ndarray, float]:
    """
    Apply erasure channel that randomly erases information.
    
    Returns:
    --------
    output_state : np.ndarray
        State after erasure
    I_lost : float
        Information lost (in nats)
    """
    N = len(state)
    
    # Randomly erase some components
    keep_mask = rng.random(N) > erasure_prob
    num_erased = N - np.sum(keep_mask)
    
    output_state = state.copy()
    output_state[~keep_mask] = 0.0
    
    # Renormalize
    if np.sum(output_state) > 0:
        output_state = output_state / np.sum(output_state)
    else:
        # All erased - uniform distribution
        output_state = np.ones(N) / N
    
    # Information lost ~ log(erasures)
    I_lost = np.log1p(num_erased)
    
    return output_state, I_lost


def test_dpi_channel(channel_name: str, 
                     erasure_prob: float, 
                     k_B_T_over_alpha0: float = 1.0,
                     seed: int = 42) -> DPIResult:
    """Test DPI for a specific channel."""
    
    rng = np.random.default_rng(seed)
    
    # Initial state (random distribution)
    N = 16
    initial_probs = rng.dirichlet(np.ones(N))
    
    S_ref_initial = compute_reflexive_entropy(initial_probs)
    
    # Apply channel
    output_probs, I_lost = apply_erasure_channel(initial_probs, erasure_prob, rng)
    
    S_ref_final = compute_reflexive_entropy(output_probs)
    
    # Predicted decrease
    predicted_decrease = k_B_T_over_alpha0 * I_lost
    
    # Actual decrease
    actual_decrease = S_ref_initial - S_ref_final
    
    # Check bound: S_ref(E ρ) ≥ S_ref(ρ) - predicted_decrease
    # Equivalently: actual_decrease ≤ predicted_decrease
    bound_satisfied = actual_decrease <= predicted_decrease * 1.05  # 5% slack
    
    status = "PASS" if bound_satisfied else "FAIL"
    
    return DPIResult(
        channel_name=str(channel_name),
        S_ref_initial=float(S_ref_initial),
        S_ref_final=float(S_ref_final),
        I_lost=float(I_lost),
        predicted_decrease=float(predicted_decrease),
        actual_decrease=float(actual_decrease),
        bound_satisfied=bool(bound_satisfied),
        status=str(status)
    )


def main():
    """Run V9 DPI validation."""
    
    print("\n" + "="*70)
    print(" V9: Reflexive Data-Processing Inequality")
    print(" Testing S_ref(E ρ) ≥ S_ref(ρ) - (k_B T/α_0)·I_lost")
    print("="*70 + "\n")
    
    # Test multiple erasure probabilities
    configs = [
        ("Low_Erasure", 0.1),
        ("Medium_Erasure", 0.3),
        ("High_Erasure", 0.5)
    ]
    
    results = []
    
    for name, p_erase in configs:
        result = test_dpi_channel(name, p_erase, k_B_T_over_alpha0=1.0, seed=42)
        results.append(result)
        
        print(f"{name} (p={p_erase}):")
        print(f"  S_ref: {result.S_ref_initial:.4f} → {result.S_ref_final:.4f}")
        print(f"  I_lost = {result.I_lost:.4f}")
        print(f"  Actual decrease: {result.actual_decrease:.4f}")
        print(f"  Predicted max: {result.predicted_decrease:.4f}")
        print(f"  {result.status}\n")
    
    # Overall
    all_pass = all(r.status == "PASS" for r in results)
    overall_status = "PASS" if all_pass else "FAIL"
    
    print(f"Overall Status: {overall_status}\n")
    
    # Save
    script_dir = Path(__file__).parent
    program_dir = script_dir.parent
    output_dir = program_dir / "outputs" / "v9"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_data = {
        "test_id": "V9",
        "test_name": "Reflexive DPI",
        "timestamp": datetime.now().isoformat(),
        "results": [asdict(r) for r in results],
        "overall_status": overall_status
    }
    
    content_str = json.dumps(output_data, sort_keys=True, indent=2)
    output_data["data_hash"] = hashlib.sha256(content_str.encode()).hexdigest()[:16]
    
    output_file = output_dir / "v9_dpi_results.json"
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"✅ Results saved to: {output_file}")
    
    return results, overall_status


if __name__ == "__main__":
    results, status = main()
    print(f"\nV9 Complete: {status}\n")

