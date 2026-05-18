"""
UGP Tools - Comprehensive toolkit for UGP (Universal Generative Principle) analysis and visualization.

This module provides functions for:
1. Prime number testing and factorization
2. Ridge scanning and survivor identification
3. Data export to CSV format
4. Figure generation for the UGP paper

Generated Figures:
- basin_plot.png: Scatter plot of c-attractors by level n
- fib_index_hist.png: Histogram of Fibonacci lift indices
- transition_diagram.png: State transition diagram with q-gap coloring

Generated Data Files:
- survivors.csv: Prime-locked survivors with full coordinates
- orders.csv: Order counts by n (mirror pair counts)
- fib_index_hist.csv: Fibonacci index histogram data

Core Functions:
- ridge_survivors(n): Generate survivors for specific n
- ridge_full_table(n): Full diagnostic table including composites
- orders_by_n(n_min, n_max): Count mirror pairs by level
- build_all(): Generate all figures and data files

Usage:
    from ugp_tools import build_all
    results = build_all(10, 18, "./output")
"""

from typing import List, Tuple, Dict
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Deterministic Miller-Rabin for 64-bit inputs
MR_BASES = (2, 3, 5, 7, 11, 13, 17)

def _mr_witness(a: int, d: int, s: int, n: int) -> bool:
    x = pow(a, d, n)
    if x == 1 or x == n - 1:
        return False
    for _ in range(s - 1):
        x = (x * x) % n
        if x == n - 1:
            return False
    return True  # composite

def is_probable_prime(n: int) -> bool:
    if n < 2:
        return False
    small = [2,3,5,7,11,13,17,19,23,29]
    for p in small:
        if n == p: return True
        if n % p == 0: return False
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2; s += 1
    for a in MR_BASES:
        if a % n == 0:
            continue
        if _mr_witness(a, d, s, n):
            return False
    return True

def divisors(n: int) -> List[int]:
    ds = []
    i = 1
    while i * i <= n:
        if n % i == 0:
            ds.append(i)
            if i * i != n:
                ds.append(n // i)
        i += 1
    ds.sort()
    return ds

def fib(k: int) -> int:
    a, b = 0, 1
    for _ in range(k):
        a, b = b, a + b
    return a

def ridge_survivors(n: int):
    """
    Yields (n, b2, q2, b1, q1, c1, is_prime) for UGP-1 candidates with b2 | (2^n-16), b2 > 15.
    Only survivors (is_prime=1) are yielded by this function.
    """
    R = (1 << n) - 16
    for b2 in divisors(R):
        if b2 <= 15: 
            continue
        q2 = R // b2
        b1 = b2 + q2 + 7
        q1 = q2 - 13
        c1 = b1 * q1 + 20
        if is_probable_prime(c1):
            yield (n, b2, q2, b1, q1, c1, 1)

def ridge_full_table(n: int):
    """
    Returns full table including composite rows:
    (n, b2, q2, b1, q1, c1, is_prime, reason)
    where reason is a short composite note or '-' for primes.
    """
    R = (1 << n) - 16
    out = []
    for b2 in divisors(R):
        if b2 <= 15: 
            continue
        q2 = R // b2
        b1 = b2 + q2 + 7
        q1 = q2 - 13
        c1 = b1 * q1 + 20
        isp = 1 if is_probable_prime(c1) else 0
        reason = '-'
        if not isp:
            # quick reason sieve
            if q1 % 2 == 0:
                reason = 'q1 even'
            elif any(q1 % p == 0 for p in (3,5,7,11,13)):
                # record first small factor
                for p in (3,5,7,11,13):
                    if q1 % p == 0:
                        reason = f'q1 divisible by {p}'
                        break
            else:
                # fall back to small factor of c1
                for p in (2,3,5,7,11,13,17,19,23,29):
                    if c1 % p == 0:
                        reason = f'c1 divisible by {p}'
                        break
        out.append((n, b2, q2, b1, q1, c1, isp, reason))
    return out

def orders_by_n(n_min: int, n_max: int):
    """
    Returns list of (n, order) where order is the count of unique mirror pairs among survivors.
    """
    rows = []
    for n in range(n_min, n_max + 1):
        pairs = []
        for (nn, b2, q2, b1, q1, c1, isp) in ridge_survivors(n):
            pairs.append((min(b2,q2), max(b2,q2)))
        rows.append((n, len(set(pairs))))
    return rows

def export_survivors_csv(path: str, n_min: int, n_max: int):
    import csv
    with open(path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['n','b2','q2','b1','q1','c1','is_prime'])
        for n in range(n_min, n_max+1):
            for row in ridge_survivors(n):
                w.writerow(row)

def export_orders_csv(path: str, n_min: int, n_max: int):
    import csv
    with open(path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['n','order'])
        for (n, order) in orders_by_n(n_min, n_max):
            w.writerow([n, order])

# ============================================================================
# NEW PLOTTING FUNCTIONS FOR PHASE 3
# ============================================================================

def generate_basin_plot(n_min: int = 10, n_max: int = 18, output_path: str = "basin_plot.png"):
    """
    Generate basin plot showing c-attractors for different n values.
    
    Args:
        n_min: Minimum n value to scan
        n_max: Maximum n value to scan  
        output_path: Path to save the generated PNG
    """
    # Collect data
    basin_data = []
    for n in range(n_min, n_max + 1):
        for (nn, b2, q2, b1, q1, c1, isp) in ridge_survivors(n):
            if isp:  # Only survivors
                basin_data.append((n, c1))
    
    if not basin_data:
        print("No survivor data found for basin plot")
        return
    
    # Create plot
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Separate data by n for different colors
    for n in range(n_min, n_max + 1):
        n_data = [c1 for nn, c1 in basin_data if nn == n]
        if n_data:
            ax.scatter([n] * len(n_data), n_data, alpha=0.7, s=50, label=f'n={n}')
    
    ax.set_xlabel('n (level, c₂ = 2ⁿ-1)')
    ax.set_ylabel('c₁ (first-generation capacity)')
    ax.set_title('Basin Plot: c-Attractors by Level n')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Save plot
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Basin plot saved to {output_path}")

def generate_fib_index_histogram(n_min: int = 10, n_max: int = 18, output_path: str = "fib_index_hist.png"):
    """
    Generate histogram of Fibonacci lift indices from survivor data.
    
    Args:
        n_min: Minimum n value to scan
        n_max: Maximum n value to scan
        output_path: Path to save the generated PNG
    """
    # Collect Fibonacci indices
    fib_indices = []
    for n in range(n_min, n_max + 1):
        for (nn, b2, q2, b1, q1, c1, isp) in ridge_survivors(n):
            if isp:  # Only survivors
                fib_indices.append(abs(q2 - q1))
    
    if not fib_indices:
        print("No survivor data found for Fibonacci histogram")
        return
    
    # Create histogram
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Create histogram with integer bins
    max_idx = max(fib_indices)
    bins = np.arange(0, max_idx + 2) - 0.5
    
    ax.hist(fib_indices, bins=bins, alpha=0.7, edgecolor='black', linewidth=0.5)
    ax.set_xlabel('Fibonacci Index |q₂ - q₁|')
    ax.set_ylabel('Count')
    ax.set_title('Histogram of Fibonacci Lift Indices from Survivors')
    ax.grid(True, alpha=0.3)
    
    # Set x-axis to show integer values
    ax.set_xticks(range(0, max_idx + 1))
    
    # Save plot
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Fibonacci histogram saved to {output_path}")
    
    # Also save CSV for LaTeX integration
    from collections import Counter
    counter = Counter(fib_indices)
    csv_path = output_path.replace('.png', '.csv')
    with open(csv_path, 'w', newline='') as f:
        import csv
        w = csv.writer(f)
        w.writerow(['k', 'count'])
        for k in sorted(counter.keys()):
            w.writerow([k, counter[k]])
    print(f"Fibonacci histogram data saved to {csv_path}")

def generate_transition_diagram(n_min: int = 10, n_max: int = 18, output_path: str = "transition_diagram.png"):
    """
    Generate transition diagram showing the flow between different states.
    
    Args:
        n_min: Minimum n value to scan
        n_max: Maximum n value to scan
        output_path: Path to save the generated PNG
    """
    # Collect transition data
    transitions = []
    for n in range(n_min, n_max + 1):
        for (nn, b2, q2, b1, q1, c1, isp) in ridge_survivors(n):
            if isp:  # Only survivors
                # Calculate next state
                m1 = c1 % b1
                a2 = m1 - (12 - n)
                b2_next = b1 - (m1 + q1)
                c2_next = b2 * q2 + 15
                
                transitions.append({
                    'n': n,
                    'from_state': (b1, c1),
                    'to_state': (b2_next, c2_next),
                    'q_gap': abs(q2 - q1)
                })
    
    if not transitions:
        print("No survivor data found for transition diagram")
        return
    
    # Create plot
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Plot transitions as arrows
    for trans in transitions:
        from_b, from_c = trans['from_state']
        to_b, to_c = trans['to_state']
        q_gap = trans['q_gap']
        
        # Color code by q_gap
        if q_gap == 13:
            color = 'red'  # Special case
        elif q_gap < 20:
            color = 'blue'
        else:
            color = 'green'
        
        # Draw arrow
        ax.annotate('', xy=(to_b, to_c), xytext=(from_b, from_c),
                   arrowprops=dict(arrowstyle='->', color=color, alpha=0.6, lw=1))
        
        # Add label for q_gap
        mid_b = (from_b + to_b) / 2
        mid_c = (from_c + to_c) / 2
        ax.annotate(f'q_gap={q_gap}', (mid_b, mid_c), 
                   xytext=(5, 5), textcoords='offset points', 
                   fontsize=8, alpha=0.7)
    
    ax.set_xlabel('b coordinate')
    ax.set_ylabel('c coordinate')
    ax.set_title('Transition Diagram: State Transitions from Survivors')
    ax.grid(True, alpha=0.3)
    
    # Save plot
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Transition diagram saved to {output_path}")

def build_all(n_min: int = 10, n_max: int = 18, output_dir: str = "."):
    """
    Build all figures and data files for the UGP paper.
    
    Args:
        n_min: Minimum n value to scan
        n_max: Maximum n value to scan
        output_dir: Directory to save all outputs
    """
    import os
    
    print(f"Building UGP paper assets for n={n_min} to n={n_max}")
    print(f"Output directory: {output_dir}")
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate CSV files
    print("\n1. Generating CSV files...")
    survivors_path = os.path.join(output_dir, "survivors.csv")
    orders_path = os.path.join(output_dir, "orders.csv")
    
    export_survivors_csv(survivors_path, n_min, n_max)
    export_orders_csv(orders_path, n_min, n_max)
    print(f"   - survivors.csv: {survivors_path}")
    print(f"   - orders.csv: {orders_path}")
    
    # Generate plots
    print("\n2. Generating plots...")
    
    basin_path = os.path.join(output_dir, "basin_plot.png")
    generate_basin_plot(n_min, n_max, basin_path)
    
    fib_path = os.path.join(output_dir, "fib_index_hist.png")
    generate_fib_index_histogram(n_min, n_max, fib_path)
    
    trans_path = os.path.join(output_dir, "transition_diagram.png")
    generate_transition_diagram(n_min, n_max, trans_path)
    
    print("\n3. Building complete!")
    print(f"Generated files:")
    print(f"   - {basin_path}")
    print(f"   - {fib_path}")
    print(f"   - {trans_path}")
    print(f"   - {survivors_path}")
    print(f"   - {orders_path}")
    
    return {
        'survivors': survivors_path,
        'orders': orders_path,
        'basin_plot': basin_path,
        'fib_hist': fib_path,
        'transition_diagram': trans_path
    }
