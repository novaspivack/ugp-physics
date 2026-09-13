#!/usr/bin/env python3
"""
TE_2.4 Parameter Sweep: Robustness Testing
==========================================

Tests JT gravity + coherence field across parameter space:
- Black hole mass: M ∈ [5, 10, 20, 50] M_Planck
- Coherence mass²: m² ∈ [0.01, 0.1, 0.5]
- Coupling: λ ∈ [0.001, 0.01, 0.1]

Validates:
1. Convergence across parameter space
2. Horizon location scaling (x_H ∝ M)
3. Temperature scaling (T_H ∝ 1/M)
4. Mode frequency scaling (ω_0 ∝ T_H)

Author: TE_2 Implementation Team
Date: November 20, 2025
"""

import numpy as np
import json
from pathlib import Path
from typing import Dict, List, Tuple
import time
from te2_4_jt_toy_model import JTGravityWithCoherence, JTGravityConfig

# Results directory
RESULTS_DIR = Path(__file__).parent.parent / "results" / "parameter_sweep"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


class ParameterSweep:
    """Run parameter sweep and analyze results."""
    
    def __init__(self):
        """Initialize parameter sweep."""
        # Parameter ranges
        self.masses = [5.0, 10.0, 20.0, 50.0]  # M_Planck
        self.psi_masses_sq = [0.01, 0.1, 0.5]  # m²
        self.couplings = [0.001, 0.01, 0.1]    # λ
        
        # Results storage
        self.results = []
        self.failed_runs = []
        
    def run_single(
        self, 
        M: float, 
        m_sq: float, 
        lam: float,
        verbose: bool = False
    ) -> Dict:
        """
        Run single parameter configuration.
        
        Args:
            M: Black hole mass (M_Planck)
            m_sq: Coherence field mass² (Planck⁻²)
            lam: Self-coupling (dimensionless)
            verbose: Print progress
            
        Returns:
            Dictionary of results
        """
        if verbose:
            print(f"\n{'='*60}")
            print(f"Testing: M={M:.1f}, m²={m_sq:.3f}, λ={lam:.3f}")
            print(f"{'='*60}")
        
        try:
            # Create configuration
            config = JTGravityConfig(
                bh_mass=M,
                psi_mass_squared=m_sq,
                psi_coupling=lam,
                dilaton_coupling=1.0,
                x_min=0.1,
                x_max=max(100.0, 5*M),  # Scale domain with M
                spatial_points=100,
                t_max=min(50.0, 5*M),   # Scale time with M
                time_points=100,
                rtol=1e-8,
                atol=1e-10,
                seed=1729
            )
            
            # Create model
            model = JTGravityWithCoherence(config)
            
            # Run simulation
            start_time = time.time()
            state = model.solve_background()
            runtime = time.time() - start_time
            
            # Extract results
            x_H = model.find_horizon(state)
            T_H = model.hawking_temperature(x_H)
            modes = model.mode_frequencies(x_H, n_modes=5)
            
            # Compute derived quantities
            expected_x_H = 2 * M
            x_H_error = abs(x_H - expected_x_H) / expected_x_H * 100
            
            expected_T_H = 1 / (8 * np.pi * M)
            T_H_error = abs(T_H - expected_T_H) / expected_T_H * 100
            
            omega_0 = modes[0]
            # Modes are ω_n = (n + 1/2) * ω_fundamental
            # So ω_0 = 0.5 * ω_fundamental = 0.5 * 2πT_H = πT_H
            expected_omega_0 = np.pi * T_H
            omega_error = abs(omega_0 - expected_omega_0) / expected_omega_0 * 100
            
            # Check mode spacing (should be uniform)
            spacings = np.diff(modes)
            spacing_std = np.std(spacings) / np.mean(spacings) * 100  # CV%
            
            result = {
                'M': M,
                'm_sq': m_sq,
                'lam': lam,
                'success': True,
                'runtime': runtime,
                'x_H': x_H,
                'x_H_expected': expected_x_H,
                'x_H_error_pct': x_H_error,
                'T_H': T_H,
                'T_H_expected': expected_T_H,
                'T_H_error_pct': T_H_error,
                'omega_0': omega_0,
                'omega_0_expected': expected_omega_0,
                'omega_error_pct': omega_error,
                'modes': modes.tolist(),
                'spacing_cv_pct': spacing_std,
            }
            
            if verbose:
                print(f"✓ Converged in {runtime:.2f}s")
                print(f"  Horizon: x_H = {x_H:.3f} (expected {expected_x_H:.3f}, error {x_H_error:.2f}%)")
                print(f"  Temperature: T_H = {T_H:.6f} (expected {expected_T_H:.6f}, error {T_H_error:.2f}%)")
                print(f"  Fundamental mode: ω_0 = {omega_0:.6f} (expected {expected_omega_0:.6f}, error {omega_error:.2f}%)")
                print(f"  Mode spacing CV: {spacing_std:.2f}%")
            
            return result
            
        except Exception as e:
            if verbose:
                print(f"✗ FAILED: {str(e)}")
            
            return {
                'M': M,
                'm_sq': m_sq,
                'lam': lam,
                'success': False,
                'error': str(e)
            }
    
    def run_mass_sweep(self, verbose: bool = True) -> None:
        """
        Sweep over black hole mass (most important parameter).
        
        Args:
            verbose: Print progress
        """
        print("\n" + "="*70)
        print("MASS SWEEP: Testing horizon and temperature scaling")
        print("="*70)
        
        # Fix other parameters
        m_sq = 0.1
        lam = 0.01
        
        for M in self.masses:
            result = self.run_single(M, m_sq, lam, verbose=verbose)
            self.results.append(result)
            
            if not result['success']:
                self.failed_runs.append(result)
    
    def run_coherence_mass_sweep(self, verbose: bool = True) -> None:
        """
        Sweep over coherence field mass.
        
        Args:
            verbose: Print progress
        """
        print("\n" + "="*70)
        print("COHERENCE MASS SWEEP: Testing field backreaction")
        print("="*70)
        
        # Fix other parameters
        M = 10.0
        lam = 0.01
        
        for m_sq in self.psi_masses_sq:
            result = self.run_single(M, m_sq, lam, verbose=verbose)
            self.results.append(result)
            
            if not result['success']:
                self.failed_runs.append(result)
    
    def run_coupling_sweep(self, verbose: bool = True) -> None:
        """
        Sweep over self-coupling.
        
        Args:
            verbose: Print progress
        """
        print("\n" + "="*70)
        print("COUPLING SWEEP: Testing nonlinear effects")
        print("="*70)
        
        # Fix other parameters
        M = 10.0
        m_sq = 0.1
        
        for lam in self.couplings:
            result = self.run_single(M, m_sq, lam, verbose=verbose)
            self.results.append(result)
            
            if not result['success']:
                self.failed_runs.append(result)
    
    def run_full_sweep(self, verbose: bool = False) -> None:
        """
        Full parameter space sweep (expensive!).
        
        Args:
            verbose: Print progress for each run
        """
        print("\n" + "="*70)
        print("FULL PARAMETER SWEEP")
        print("="*70)
        
        total = len(self.masses) * len(self.psi_masses_sq) * len(self.couplings)
        print(f"Total configurations: {total}")
        
        count = 0
        for M in self.masses:
            for m_sq in self.psi_masses_sq:
                for lam in self.couplings:
                    count += 1
                    if not verbose:
                        print(f"[{count}/{total}] M={M:.1f}, m²={m_sq:.3f}, λ={lam:.3f}...", end=" ")
                    
                    result = self.run_single(M, m_sq, lam, verbose=verbose)
                    self.results.append(result)
                    
                    if not result['success']:
                        self.failed_runs.append(result)
                        if not verbose:
                            print("✗ FAILED")
                    else:
                        if not verbose:
                            print(f"✓ ({result['runtime']:.1f}s)")
    
    def analyze_results(self) -> Dict:
        """
        Analyze sweep results.
        
        Returns:
            Dictionary of analysis results
        """
        print("\n" + "="*70)
        print("ANALYSIS")
        print("="*70)
        
        # Filter successful runs
        successful = [r for r in self.results if r['success']]
        n_success = len(successful)
        n_total = len(self.results)
        
        print(f"\nSuccess rate: {n_success}/{n_total} ({n_success/n_total*100:.1f}%)")
        
        if n_success == 0:
            print("✗ No successful runs!")
            return {'success_rate': 0.0}
        
        # Extract arrays
        x_H_errors = np.array([r['x_H_error_pct'] for r in successful])
        T_H_errors = np.array([r['T_H_error_pct'] for r in successful])
        omega_errors = np.array([r['omega_error_pct'] for r in successful])
        spacing_cvs = np.array([r['spacing_cv_pct'] for r in successful])
        runtimes = np.array([r['runtime'] for r in successful])
        
        # Statistics
        analysis = {
            'success_rate': n_success / n_total,
            'n_success': n_success,
            'n_total': n_total,
            'x_H_error': {
                'mean': float(np.mean(x_H_errors)),
                'std': float(np.std(x_H_errors)),
                'max': float(np.max(x_H_errors)),
                'min': float(np.min(x_H_errors)),
            },
            'T_H_error': {
                'mean': float(np.mean(T_H_errors)),
                'std': float(np.std(T_H_errors)),
                'max': float(np.max(T_H_errors)),
                'min': float(np.min(T_H_errors)),
            },
            'omega_error': {
                'mean': float(np.mean(omega_errors)),
                'std': float(np.std(omega_errors)),
                'max': float(np.max(omega_errors)),
                'min': float(np.min(omega_errors)),
            },
            'spacing_cv': {
                'mean': float(np.mean(spacing_cvs)),
                'std': float(np.std(spacing_cvs)),
                'max': float(np.max(spacing_cvs)),
                'min': float(np.min(spacing_cvs)),
            },
            'runtime': {
                'mean': float(np.mean(runtimes)),
                'std': float(np.std(runtimes)),
                'max': float(np.max(runtimes)),
                'min': float(np.min(runtimes)),
            }
        }
        
        # Print summary
        print(f"\nHorizon location error:")
        print(f"  Mean: {analysis['x_H_error']['mean']:.2f}% ± {analysis['x_H_error']['std']:.2f}%")
        print(f"  Range: [{analysis['x_H_error']['min']:.2f}%, {analysis['x_H_error']['max']:.2f}%]")
        
        print(f"\nHawking temperature error:")
        print(f"  Mean: {analysis['T_H_error']['mean']:.2f}% ± {analysis['T_H_error']['std']:.2f}%")
        print(f"  Range: [{analysis['T_H_error']['min']:.2f}%, {analysis['T_H_error']['max']:.2f}%]")
        
        print(f"\nFundamental mode error:")
        print(f"  Mean: {analysis['omega_error']['mean']:.2f}% ± {analysis['omega_error']['std']:.2f}%")
        print(f"  Range: [{analysis['omega_error']['min']:.2f}%, {analysis['omega_error']['max']:.2f}%]")
        
        print(f"\nMode spacing uniformity (CV%):")
        print(f"  Mean: {analysis['spacing_cv']['mean']:.2f}% ± {analysis['spacing_cv']['std']:.2f}%")
        print(f"  Range: [{analysis['spacing_cv']['min']:.2f}%, {analysis['spacing_cv']['max']:.2f}%]")
        
        print(f"\nRuntime:")
        print(f"  Mean: {analysis['runtime']['mean']:.2f}s ± {analysis['runtime']['std']:.2f}s")
        print(f"  Range: [{analysis['runtime']['min']:.2f}s, {analysis['runtime']['max']:.2f}s]")
        
        # Check scaling laws
        print("\n" + "-"*70)
        print("SCALING LAW VALIDATION")
        print("-"*70)
        
        # Group by parameter
        mass_results = [r for r in successful if r['m_sq'] == 0.1 and r['lam'] == 0.01]
        if len(mass_results) >= 2:
            masses = np.array([r['M'] for r in mass_results])
            x_Hs = np.array([r['x_H'] for r in mass_results])
            T_Hs = np.array([r['T_H'] for r in mass_results])
            
            # Linear fit: x_H vs M (should have slope ≈ 2)
            x_H_slope = np.polyfit(masses, x_Hs, 1)[0]
            print(f"\nHorizon scaling: x_H ∝ M")
            print(f"  Measured slope: {x_H_slope:.3f} (expected: 2.0)")
            print(f"  Error: {abs(x_H_slope - 2.0)/2.0 * 100:.1f}%")
            
            # Inverse fit: T_H vs 1/M
            T_H_coeff = np.polyfit(1/masses, T_Hs, 1)[0]
            expected_coeff = 1 / (8 * np.pi)
            print(f"\nTemperature scaling: T_H ∝ 1/M")
            print(f"  Measured coefficient: {T_H_coeff:.6f} (expected: {expected_coeff:.6f})")
            print(f"  Error: {abs(T_H_coeff - expected_coeff)/expected_coeff * 100:.1f}%")
            
            analysis['scaling'] = {
                'x_H_slope': float(x_H_slope),
                'x_H_slope_expected': 2.0,
                'x_H_slope_error_pct': float(abs(x_H_slope - 2.0)/2.0 * 100),
                'T_H_coeff': float(T_H_coeff),
                'T_H_coeff_expected': float(expected_coeff),
                'T_H_coeff_error_pct': float(abs(T_H_coeff - expected_coeff)/expected_coeff * 100),
            }
        
        # Pass/fail criteria
        print("\n" + "-"*70)
        print("PASS/FAIL CRITERIA")
        print("-"*70)
        
        criteria = {
            'success_rate': (analysis['success_rate'] >= 0.95, "Success rate ≥ 95%"),
            'x_H_error': (analysis['x_H_error']['mean'] < 5.0, "Mean horizon error < 5%"),
            'T_H_error': (analysis['T_H_error']['mean'] < 5.0, "Mean temperature error < 5%"),
            'omega_error': (analysis['omega_error']['mean'] < 5.0, "Mean mode error < 5%"),
            'spacing_cv': (analysis['spacing_cv']['mean'] < 1.0, "Mode spacing CV < 1%"),
        }
        
        all_passed = True
        for name, (passed, description) in criteria.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"{status}: {description}")
            if not passed:
                all_passed = False
        
        analysis['all_tests_passed'] = all_passed
        
        if all_passed:
            print("\n" + "="*70)
            print("✓ ALL TESTS PASSED - MODEL IS ROBUST")
            print("="*70)
        else:
            print("\n" + "="*70)
            print("✗ SOME TESTS FAILED - REVIEW RESULTS")
            print("="*70)
        
        return analysis
    
    def save_results(self, filename: str = "sweep_results.json") -> None:
        """
        Save results to JSON.
        
        Args:
            filename: Output filename
        """
        output_file = RESULTS_DIR / filename
        
        data = {
            'results': self.results,
            'failed_runs': self.failed_runs,
            'analysis': self.analyze_results() if self.results else None,
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n✓ Results saved to {output_file}")


def main():
    """Run parameter sweep tests."""
    print("="*70)
    print("TE_2.4 PARAMETER SWEEP: ROBUSTNESS TESTING")
    print("="*70)
    
    sweep = ParameterSweep()
    
    # Run individual sweeps (faster, more interpretable)
    sweep.run_mass_sweep(verbose=True)
    sweep.run_coherence_mass_sweep(verbose=True)
    sweep.run_coupling_sweep(verbose=True)
    
    # Analyze and save
    analysis = sweep.analyze_results()
    sweep.save_results("sweep_results.json")
    
    # Optional: Full sweep (uncomment if needed)
    # print("\n" + "="*70)
    # print("Running full parameter sweep (this will take longer)...")
    # print("="*70)
    # sweep_full = ParameterSweep()
    # sweep_full.run_full_sweep(verbose=False)
    # sweep_full.analyze_results()
    # sweep_full.save_results("sweep_results_full.json")
    
    return 0 if analysis.get('all_tests_passed', False) else 1


if __name__ == "__main__":
    exit(main())

