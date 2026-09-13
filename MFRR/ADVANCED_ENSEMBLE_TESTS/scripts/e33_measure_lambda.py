#!/usr/bin/env python3
"""
E33: Direct Measurement of Λ from Simulation
=============================================

Tests the hypothesis that Norfleet's dimensional constant Λ can be measured
directly from our information-geometry simulations as the ratio of:

    Λ = (Rate of discrete structure formation) / (Rate of continuous flow)
      = ln(φ) / ln(2π)
      ≈ 0.2618

where φ is golden ratio.

Method:
- Measure discrete events (ω spikes, CP flips) 
- Measure continuous flow (ω diffusion, Ψ gradients)
- Compute ratio and compare to Λ_Norfleet = 0.2618

Cross-reference:
    Norfleet "Dimensional Dynamics in Multifractals"
    Oracle insight: "Λ is static ratio, 1.13 is dynamic threshold"
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
from numpy.random import default_rng
import json
import matplotlib.pyplot as plt
from scipy.ndimage import convolve
from multiprocessing import Pool
import time


# Norfleet's theoretical value
LAMBDA_NORFLEET = np.log(1.618033988749895) / np.log(2*np.pi)  # ln(φ)/ln(2π)

print(f"Theoretical Λ (Norfleet): {LAMBDA_NORFLEET:.6f}")


class E33Config:
    """Configuration for Lambda measurement."""
    L = 60
    steps_total = 1500
    n_sources = 12
    
    # Use optimal parameters from E30d
    source_strength = 0.5
    gamma = 0.05
    J_base = 0.15
    beta = 7.0
    D_omega = 0.15
    kappa = 1.0
    m_squared = 0.03
    
    # Multiple realizations for statistics
    n_realizations = 8
    n_cores = 8
    
    seed_base = 200


def solve_psi_fft(omega, kappa, m_squared):
    """Solve for Psi."""
    L = omega.shape[0]
    omega_k = np.fft.fft2(omega)
    kx = 2*np.pi*np.fft.fftfreq(L)
    ky = 2*np.pi*np.fft.fftfreq(L)
    KX, KY = np.meshgrid(kx, ky, indexing='ij')
    k_squared = KX**2 + KY**2
    denom = k_squared + m_squared
    denom[0,0] = 1.0
    psi_k = kappa * omega_k / denom
    psi_k[0,0] = 0.0
    return np.fft.ifft2(psi_k).real


def update_omega_diffusion(omega, D, gamma, dt=1.0):
    """Diffusion-decay."""
    laplacian_kernel = np.array([[0,1,0],[1,-4,1],[0,1,0]])
    laplacian = convolve(omega, laplacian_kernel, mode='wrap')
    omega_new = omega + dt * (D * laplacian - gamma * omega)
    return np.maximum(omega_new, 0.0)


def run_lambda_measurement(args):
    """Run simulation and measure discrete vs continuous rates."""
    real_idx, cfg, run_seed = args
    
    rng = default_rng(run_seed)
    L = cfg.L
    
    # Place sources
    sources = []
    for _ in range(cfg.n_sources):
        i, j = rng.integers(0, L), rng.integers(0, L)
        sources.append((i, j))
    
    # Initialize
    psi = np.zeros((L, L))
    omega = np.zeros((L, L))
    
    # Storage for rate measurements
    discrete_events = []   # Count of ω spikes (sharp local increases)
    continuous_flux = []   # ∫|∇ω| dA (total diffusive flux)
    
    psi_gradient_norms = []  # ∫|∇Ψ| dA
    omega_discrete_rate = []  # Rate of discrete jumps
    
    # Evolution
    for step in range(cfg.steps_total):
        omega_before = omega.copy()
        
        # Inject at sources (DISCRETE events)
        for i, j in sources:
            omega[i, j] += cfg.source_strength
        
        # Diffuse (CONTINUOUS flow)
        omega = update_omega_diffusion(omega, cfg.D_omega, cfg.gamma, dt=1.0)
        
        # Solve for Psi
        psi = solve_psi_fft(omega, cfg.kappa, cfg.m_squared)
        
        # Measure discrete rate: Count sharp local increases in ω
        omega_delta = omega - omega_before
        n_discrete = np.sum(omega_delta > 0.1)  # Threshold for "discrete" event
        discrete_events.append(n_discrete)
        
        # Measure continuous flux: Total gradient magnitude
        grad_omega_x = np.gradient(omega, axis=0)
        grad_omega_y = np.gradient(omega, axis=1)
        grad_mag = np.sqrt(grad_omega_x**2 + grad_omega_y**2)
        total_flux = np.sum(grad_mag)
        continuous_flux.append(total_flux)
        
        # Psi gradient (for alternative measurement)
        grad_psi_x = np.gradient(psi, axis=0)
        grad_psi_y = np.gradient(psi, axis=1)
        psi_grad_mag = np.sqrt(grad_psi_x**2 + grad_psi_y**2)
        psi_gradient_norms.append(np.sum(psi_grad_mag))
    
    # Compute rates (average over time)
    discrete_rate = np.mean(discrete_events)
    continuous_rate = np.mean(continuous_flux)
    psi_grad_rate = np.mean(psi_gradient_norms)
    
    # Compute Λ_measured
    # Method 1: omega-based
    if continuous_rate > 0:
        lambda_measured_omega = discrete_rate / continuous_rate
    else:
        lambda_measured_omega = np.nan
    
    # Method 2: Structure count vs flow
    # Discrete: number of high-omega regions (structures)
    # Continuous: total Psi gradient (continuous field)
    omega_final = omega
    n_structures = np.sum(omega_final > np.mean(omega_final) + 0.5*np.std(omega_final))
    
    if psi_grad_rate > 0:
        lambda_measured_structure = n_structures / psi_grad_rate
    else:
        lambda_measured_structure = np.nan
    
    # Method 3: Growth rates
    # Fit exponential growth to discrete and continuous metrics
    steps = np.arange(len(discrete_events))
    
    # Discrete: cumulative events
    discrete_cumulative = np.cumsum(discrete_events)
    continuous_cumulative = np.cumsum(continuous_flux)
    
    # Fit linear (log of cumulative ~ growth rate × time)
    if len(steps) > 100:
        late_steps = steps[-500:]
        discrete_late = discrete_cumulative[-500:]
        continuous_late = continuous_cumulative[-500:]
        
        # Growth rates from slopes
        discrete_growth = np.polyfit(late_steps, discrete_late, 1)[0]
        continuous_growth = np.polyfit(late_steps, continuous_late, 1)[0]
        
        if continuous_growth > 0:
            lambda_measured_growth = discrete_growth / continuous_growth
        else:
            lambda_measured_growth = np.nan
    else:
        lambda_measured_growth = np.nan
    
    return {
        'realization': real_idx,
        'lambda_omega': lambda_measured_omega,
        'lambda_structure': lambda_measured_structure,
        'lambda_growth': lambda_measured_growth,
        'discrete_rate': discrete_rate,
        'continuous_rate': continuous_rate,
        'n_structures': n_structures
    }


def analyze_lambda(results, output_dir):
    """Analyze measured Lambda values."""
    print("\n" + "=" * 80)
    print("LAMBDA MEASUREMENT ANALYSIS")
    print("=" * 80)
    
    # Extract values
    lambda_omega = [r['lambda_omega'] for r in results if not np.isnan(r['lambda_omega'])]
    lambda_struct = [r['lambda_structure'] for r in results if not np.isnan(r['lambda_structure'])]
    lambda_growth = [r['lambda_growth'] for r in results if not np.isnan(r['lambda_growth'])]
    
    print(f"\nMethod 1 (omega discrete/continuous):")
    print(f"  Mean Λ: {np.mean(lambda_omega):.6f} ± {np.std(lambda_omega):.6f}")
    print(f"  Norfleet Λ: {LAMBDA_NORFLEET:.6f}")
    print(f"  Deviation: {abs(np.mean(lambda_omega) - LAMBDA_NORFLEET):.6f}")
    
    print(f"\nMethod 2 (structure count/flow):")
    print(f"  Mean Λ: {np.mean(lambda_struct):.6f} ± {np.std(lambda_struct):.6f}")
    print(f"  Deviation: {abs(np.mean(lambda_struct) - LAMBDA_NORFLEET):.6f}")
    
    print(f"\nMethod 3 (growth rate ratio):")
    if lambda_growth:
        print(f"  Mean Λ: {np.mean(lambda_growth):.6f} ± {np.std(lambda_growth):.6f}")
        print(f"  Deviation: {abs(np.mean(lambda_growth) - LAMBDA_NORFLEET):.6f}")
    else:
        print(f"  Could not compute (insufficient data)")
    
    # Best estimate (use method with smallest variance)
    methods = [
        ('omega', lambda_omega, 'Discrete/Continuous'),
        ('structure', lambda_struct, 'Structure/Flow'),
        ('growth', lambda_growth, 'Growth rates')
    ]
    
    best_method = None
    best_std = float('inf')
    
    for name, values, label in methods:
        if values and len(values) > 0:
            if np.std(values) < best_std:
                best_std = np.std(values)
                best_method = (name, values, label)
    
    if best_method:
        name, values, label = best_method
        lambda_best = np.mean(values)
        lambda_std = np.std(values)
        
        print(f"\n{'='*80}")
        print(f"BEST ESTIMATE: {label} method")
        print(f"{'='*80}")
        print(f"Λ_measured = {lambda_best:.6f} ± {lambda_std:.6f}")
        print(f"Λ_Norfleet = {LAMBDA_NORFLEET:.6f}")
        print(f"Deviation: {abs(lambda_best - LAMBDA_NORFLEET):.6f}")
        print(f"Relative error: {100*abs(lambda_best - LAMBDA_NORFLEET)/LAMBDA_NORFLEET:.2f}%")
    else:
        lambda_best = np.nan
        lambda_std = np.nan
    
    # Visualization
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    
    # Plot 1: Lambda distributions
    ax1 = axes[0, 0]
    if lambda_omega:
        ax1.hist(lambda_omega, bins=20, alpha=0.6, color='blue', 
                edgecolor='black', label='Ω discrete/continuous')
    if lambda_struct:
        ax1.hist(lambda_struct, bins=20, alpha=0.6, color='green',
                edgecolor='black', label='Structure/flow')
    ax1.axvline(LAMBDA_NORFLEET, color='red', linestyle='--', linewidth=3,
               label=f'Λ_Norfleet = {LAMBDA_NORFLEET:.4f}')
    ax1.set_xlabel('Measured Λ', fontsize=12)
    ax1.set_ylabel('Frequency', fontsize=12)
    ax1.set_title('Λ Measurement Distribution', fontsize=13)
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: All measurements with error bars
    ax2 = axes[0, 1]
    method_names = []
    method_means = []
    method_stds = []
    
    for name, values, label in methods:
        if values and len(values) > 0:
            method_names.append(label)
            method_means.append(np.mean(values))
            method_stds.append(np.std(values))
    
    x_pos = np.arange(len(method_names))
    ax2.errorbar(x_pos, method_means, yerr=method_stds,
                fmt='o', markersize=12, capsize=8, capthick=2,
                color='purple', linewidth=2)
    ax2.axhline(LAMBDA_NORFLEET, color='red', linestyle='--', linewidth=2,
               label='Λ_Norfleet')
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(method_names, rotation=15, ha='right')
    ax2.set_ylabel('Λ', fontsize=12)
    ax2.set_title('Λ by Measurement Method', fontsize=13)
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Plot 3: Validation of Profit = 1 + Λ/2
    ax3 = axes[1, 0]
    if not np.isnan(lambda_best):
        predicted_profit = 1 + lambda_best / 2
        measured_profit = 1.13  # From E32
        
        ax3.bar(['Measured\n(E32)', 'Predicted\n(1+Λ/2)'],
               [measured_profit, predicted_profit],
               color=['blue', 'green'], alpha=0.7, edgecolor='black', linewidth=2)
        ax3.axhline(measured_profit, color='blue', linestyle=':', alpha=0.5)
        ax3.set_ylabel('Profit Threshold', fontsize=12)
        ax3.set_title(f'Validation: 1.13 vs 1+Λ/2 = {predicted_profit:.4f}', fontsize=13)
        ax3.grid(True, alpha=0.3, axis='y')
    
    # Plot 4: Summary
    ax4 = axes[1, 1]
    ax4.axis('off')
    
    summary = "LAMBDA MEASUREMENT\n\n"
    summary += f"Norfleet's Λ: {LAMBDA_NORFLEET:.6f}\n"
    summary += f"(= ln(φ)/ln(2π))\n\n"
    
    if not np.isnan(lambda_best):
        summary += f"Best measured: {lambda_best:.6f}\n"
        summary += f"Std deviation: {lambda_std:.6f}\n"
        summary += f"Rel. error: {100*abs(lambda_best-LAMBDA_NORFLEET)/LAMBDA_NORFLEET:.2f}%\n\n"
        
        predicted_profit = 1 + lambda_best / 2
        summary += f"PROFIT FORMULA:\n"
        summary += f"  1 + Λ/2 = {predicted_profit:.4f}\n"
        summary += f"  E32 measured = 1.1300\n"
        summary += f"  Match: {abs(predicted_profit - 1.13) < 0.01}\n"
    
    ax4.text(0.1, 0.9, summary, transform=ax4.transAxes,
            fontsize=11, verticalalignment='top', family='monospace',
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.5))
    
    plt.tight_layout()
    fig_path = output_dir / 'e33_lambda_measurement.png'
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    print(f"\n✓ Figure saved: {fig_path}")
    plt.close()
    
    return lambda_best, lambda_std


def main():
    """Run E33: Measure Lambda from simulation."""
    cfg = E33Config()
    
    print("=" * 80)
    print("E33: DIRECT MEASUREMENT OF Λ")
    print("=" * 80)
    print(f"\n🎯 HYPOTHESIS: Our simulations contain Λ = ln(φ)/ln(2π) ≈ 0.2618")
    print(f"   Measure as ratio of discrete/continuous rates")
    print("=" * 80)
    
    print(f"\nConfiguration:")
    print(f"  Lattice: {cfg.L}×{cfg.L}")
    print(f"  Sources: {cfg.n_sources}")
    print(f"  Evolution: {cfg.steps_total} steps")
    print(f"  Realizations: {cfg.n_realizations}")
    print(f"  Cores: {cfg.n_cores}")
    
    # Generate tasks
    tasks = [(i, cfg, cfg.seed_base + i) for i in range(cfg.n_realizations)]
    
    print(f"\nLaunching {len(tasks)} simulations...")
    start_time = time.time()
    
    with Pool(cfg.n_cores) as pool:
        results = pool.map(run_lambda_measurement, tasks)
    
    elapsed = time.time() - start_time
    print(f"\nComplete in {elapsed:.1f}s")
    
    # Output
    output_dir = Path(__file__).parent.parent / 'outputs' / 'e33_outputs'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    lambda_best, lambda_std = analyze_lambda(results, output_dir)
    
    # Final summary
    print("\n" + "=" * 80)
    print("FINAL RESULT: E33 LAMBDA MEASUREMENT")
    print("=" * 80)
    
    if not np.isnan(lambda_best):
        print(f"\nΛ_measured = {lambda_best:.6f} ± {lambda_std:.6f}")
        print(f"Λ_Norfleet = {LAMBDA_NORFLEET:.6f}")
        print(f"Deviation: {abs(lambda_best - LAMBDA_NORFLEET):.6f}")
        print(f"Relative error: {100*abs(lambda_best - LAMBDA_NORFLEET)/LAMBDA_NORFLEET:.2f}%")
        
        predicted_profit = 1 + lambda_best / 2
        print(f"\n🔗 PROFIT FORMULA VALIDATION:")
        print(f"   1 + Λ_measured/2 = 1 + {lambda_best:.6f}/2 = {predicted_profit:.4f}")
        print(f"   E32 measured profit = 1.1300")
        print(f"   Difference: {abs(predicted_profit - 1.13):.4f}")
        
        if abs(lambda_best - LAMBDA_NORFLEET) < 0.05:
            print(f"\n🎉 SUCCESS: Λ measured from simulation!")
            print(f"   Frameworks are UNIFIED!")
        else:
            print(f"\n⚠️  Measurement differs from theory")
            print(f"   May need different rate definitions")
    
    # Save
    output_data = {
        'hypothesis': 'Lambda = ln(phi)/ln(2pi) measurable from discrete/continuous rates',
        'Lambda_Norfleet': LAMBDA_NORFLEET,
        'Lambda_measured': float(lambda_best) if not np.isnan(lambda_best) else None,
        'Lambda_std': float(lambda_std) if not np.isnan(lambda_std) else None,
        'predicted_profit': float(1 + lambda_best/2) if not np.isnan(lambda_best) else None,
        'measured_profit_E32': 1.13,
        'results': results
    }
    
    with open(output_dir / 'e33_results.json', 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n✓ Results saved: {output_dir / 'e33_results.json'}")
    print("\n" + "=" * 80)
    print("E33 COMPLETE")
    print("=" * 80)


if __name__ == '__main__':
    main()

