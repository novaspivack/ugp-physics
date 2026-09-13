#!/usr/bin/env python3
"""
Debug the RG sweep data structure
"""
import json
from pathlib import Path

def debug_data():
    data_file = Path("UGP_discovery_lab_runs/exp_20250918_143052/results/reports/experiment_results.json")
    
    with open(data_file, 'r') as f:
        data = json.load(f)
    
    print("Top-level keys:", list(data.keys()))
    print("\nResults structure:")
    results = data.get("results", [])
    print(f"Number of results: {len(results)}")
    
    if results:
        print("\nFirst result keys:", list(results[0].keys()))
        print("\nFirst result:")
        print(json.dumps(results[0], indent=2)[:1000] + "...")
        
        # Check trajectory
        traj = results[0].get("trajectory", [])
        print(f"\nTrajectory length: {len(traj)}")
        if traj:
            print("First trajectory item:", traj[0])
            print("Last trajectory item:", traj[-1])

if __name__ == "__main__":
    debug_data()
