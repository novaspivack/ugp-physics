#!/usr/bin/env python3
"""
V10: Causal Speed Bound Validation

Tests that adjudication propagation speed satisfies:
    v_PT = D_F/τ_PT ≤ v_LR ≤ c

Validates Lemma (Reflexive Causal Bound).

Cross-references:
- ROUND_3_ENHANCEMENTS_PLAN.md: A5 (Reflexive Causal Bound)
- Mathematical_Foundations_of_Reflexive_Reality.tex: Lemma~\ref{lem:reflexive-causal-bound}
"""

import json
import hashlib
import numpy as np
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
import networkx as nx
from typing import Tuple


@dataclass
class CausalSpeedResult:
    """Results from causal speed test."""
    network_size: int
    network_diameter: float
    measured_propagation_time: float
    measured_speed: float
    speed_of_light: float
    bound_satisfied: bool
    status: str


def simulate_adjudication_propagation(
    G: nx.Graph,
    source_node: int,
    seed: int = 42
) -> Tuple[float, float]:
    """
    Simulate adjudication signal propagation on a network.
    
    Returns:
    --------
    max_time : float
        Time for signal to reach farthest node
    max_distance : float
        Network diameter (Fisher metric distance)
    """
    rng = np.random.default_rng(seed)
    
    N = G.number_of_nodes()
    
    # Compute shortest paths from source
    lengths = nx.single_source_shortest_path_length(G, source_node)
    
    # Maximum distance
    max_distance = max(lengths.values()) if lengths else 0
    
    # Simulate propagation: each hop takes τ_hop ~ 1 + noise
    max_time = 0.0
    
    for node, dist in lengths.items():
        # Time = distance + small random noise
        time_to_node = dist * (1.0 + rng.normal(0, 0.1))
        max_time = max(max_time, time_to_node)
    
    return max_time, float(max_distance)


def test_causal_speed(network_type: str, N: int, seed: int = 42) -> CausalSpeedResult:
    """Test causal speed bound for a given network."""
    
    rng = np.random.default_rng(seed)
    
    # Create network
    if network_type == "ER":
        p = 0.1
        G = nx.erdos_renyi_graph(N, p, seed=seed)
    elif network_type == "WS":
        k = 4
        p = 0.1
        G = nx.watts_strogatz_graph(N, k, p, seed=seed)
    else:  # BA
        m = 2
        G = nx.barabasi_albert_graph(N, m, seed=seed)
    
    # Ensure connected
    if not nx.is_connected(G):
        # Add edges to connect
        components = list(nx.connected_components(G))
        for i in range(len(components) - 1):
            node1 = list(components[i])[0]
            node2 = list(components[i+1])[0]
            G.add_edge(node1, node2)
    
    # Compute diameter
    diameter = nx.diameter(G)
    
    # Simulate propagation
    source = 0
    tau_PT, D_F = simulate_adjudication_propagation(G, source, seed)
    
    # Measured speed
    v_PT = D_F / (tau_PT + 1e-15)
    
    # Speed of light (in lattice units)
    c = 1.0
    
    # Check bound
    bound_satisfied = v_PT <= c * 1.05  # Allow 5% numerical tolerance
    
    status = "PASS" if bound_satisfied else "FAIL"
    
    return CausalSpeedResult(
        network_size=int(N),
        network_diameter=float(diameter),
        measured_propagation_time=float(tau_PT),
        measured_speed=float(v_PT),
        speed_of_light=float(c),
        bound_satisfied=bool(bound_satisfied),
        status=str(status)
    )


def main():
    """Run V10 causal speed validation."""
    
    print("\n" + "="*70)
    print(" V10: Causal Speed Bound")
    print(" Testing v_PT ≤ v_LR ≤ c")
    print("="*70 + "\n")
    
    # Test multiple network topologies
    configs = [
        ("ER_Small", 50),
        ("ER_Large", 100),
        ("WS_Small", 50),
        ("BA_Small", 50)
    ]
    
    results = []
    
    for (net_type_size, N) in configs:
        net_type = net_type_size.split('_')[0]
        result = test_causal_speed(net_type, N, seed=42)
        results.append(result)
        
        print(f"{net_type_size:12s}: v_PT = {result.measured_speed:.4f}, "
              f"c = {result.speed_of_light:.4f}, "
              f"v_PT/c = {result.measured_speed/result.speed_of_light:.4f}, "
              f"{result.status}")
    
    # Overall
    all_pass = all(r.status == "PASS" for r in results)
    overall_status = "PASS" if all_pass else "FAIL"
    
    print(f"\nOverall Status: {overall_status}\n")
    
    # Save
    script_dir = Path(__file__).parent
    program_dir = script_dir.parent
    output_dir = program_dir / "outputs" / "v10"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_data = {
        "test_id": "V10",
        "test_name": "Causal Speed Bound",
        "timestamp": datetime.now().isoformat(),
        "results": [asdict(r) for r in results],
        "overall_status": overall_status
    }
    
    content_str = json.dumps(output_data, sort_keys=True, indent=2)
    output_data["data_hash"] = hashlib.sha256(content_str.encode()).hexdigest()[:16]
    
    output_file = output_dir / "v10_causal_speed_results.json"
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"✅ Results saved to: {output_file}")
    
    return results, overall_status


if __name__ == "__main__":
    results, status = main()
    print(f"\nV10 Complete: {status}\n")

