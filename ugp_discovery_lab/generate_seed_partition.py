#!/usr/bin/env python3
"""
Generate seed partition heatmap from RG sweep results
"""
import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from collections import Counter

def load_rg_results(filepath):
    """Load RG sweep results"""
    with open(filepath, 'r') as f:
        data = json.load(f)
    return data

def extract_attractor_data(data):
    """Extract seed, window, policy, and alpha* from results"""
    results = []
    for item in data.get("data", {}).get("results", []):
        if not item.get("success", False):
            continue
            
        seeds = tuple(item.get("seeds", [None, None, None]))
        window = item.get("window", -1)
        law = item.get("law", {})
        policy = f"{law.get('c_policy', '?')}_{law.get('b_policy', '?')}_{law.get('a_policy', '?')}"
        
        trajectory = item.get("trajectory", [])
        if not trajectory:
            continue
            
        # Get the final alpha value
        alpha_star = trajectory[-1].get("alpha", np.nan)
        if not np.isfinite(alpha_star):
            continue
            
        results.append((seeds, window, policy, alpha_star))
    
    return results

def label_attractor(alpha, bins):
    """Map alpha* to attractor label"""
    for lo, hi, lab in bins:
        if lo <= alpha <= hi:
            return lab
    return "UNK"

def create_seed_partition_plot(data, output_dir):
    """Create the seed partition heatmap"""
    # Define attractor bins
    bins = [
        (-0.09, -0.08, "A"),
        (0.07, 0.08, "B"), 
        (0.26, 0.27, "C")
    ]
    
    # Extract data
    results = extract_attractor_data(data)
    
    if not results:
        print("No valid data found!")
        return None
    
    # Create CSV data
    csv_data = []
    for seeds, window, policy, alpha in results:
        label = label_attractor(alpha, bins)
        csv_data.append({
            'seed_1': seeds[0],
            'seed_2': seeds[1], 
            'seed_3': seeds[2],
            'window': window,
            'policy': policy,
            'alpha_star': alpha,
            'attractor_label': label
        })
    
    # Save CSV
    csv_path = output_dir / "seed_partition_data.csv"
    import pandas as pd
    df = pd.DataFrame(csv_data)
    df.to_csv(csv_path, index=False)
    print(f"Saved CSV data to {csv_path}")
    
    # Create heatmap
    # Group by window and policy
    windows = sorted(set(w for _, w, _, _ in results))
    policies = sorted(set(p for _, _, p, _ in results))
    
    # Create matrix: rows=windows, cols=policies, values=attractor labels
    matrix = np.zeros((len(windows), len(policies)))
    label_to_num = {"A": 0, "B": 1, "C": 2, "UNK": -1}
    
    for seeds, window, policy, alpha in results:
        label = label_attractor(alpha, bins)
        w_idx = windows.index(window)
        p_idx = policies.index(policy)
        matrix[w_idx, p_idx] = label_to_num[label]
    
    # Create plot
    fig, ax = plt.subplots(figsize=(12, 8))
    im = ax.imshow(matrix, cmap='RdYlBu_r', aspect='auto')
    
    ax.set_xticks(range(len(policies)))
    ax.set_yticks(range(len(windows)))
    ax.set_xticklabels(policies, rotation=45, ha='right')
    ax.set_yticklabels(windows)
    
    ax.set_xlabel('Policy')
    ax.set_ylabel('Window')
    ax.set_title('Seed Partition Map: RG Attractor Basins')
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Attractor Label (A=0, B=1, C=2)')
    
    # Add text annotations
    for i in range(len(windows)):
        for j in range(len(policies)):
            val = matrix[i, j]
            text = ax.text(j, i, f'{val:.0f}' if val >= 0 else '?',
                         ha="center", va="center", 
                         color="black" if abs(val) < 1 else "white")
    
    plt.tight_layout()
    
    # Save plot
    plot_path = output_dir / "seed_partition_heatmap.png"
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Saved plot to {plot_path}")
    
    # Print summary
    label_counts = Counter([label_attractor(alpha, bins) for _, _, _, alpha in results])
    print(f"\nAttractor distribution:")
    for label, count in label_counts.items():
        print(f"  {label}: {count} runs")
    
    return plot_path

if __name__ == "__main__":
    # Load data
    data_file = Path("UGP_discovery_lab_runs/exp_20250918_143052/results/reports/experiment_results.json")
    data = load_rg_results(data_file)
    
    # Create output directory
    output_dir = Path("plots")
    output_dir.mkdir(exist_ok=True)
    
    # Generate plot
    plot_path = create_seed_partition_plot(data, output_dir)
    
    if plot_path:
        print(f"Successfully generated seed partition heatmap: {plot_path}")
    else:
        print("Failed to generate plot")
