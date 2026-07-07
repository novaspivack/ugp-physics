#!/usr/bin/env python3
"""
TE_2.4 Phase 2: Hilbert Space Construction
==========================================

Constructs the quantum Hilbert space for the 1+1D JT black hole:
    H = H_interior ⊗ H_exterior

In 1+1D, the horizon is a 0+1D object (point in space), so the Hilbert
space is finite-dimensional, spanned by near-horizon modes.

Key features:
- Finite-dimensional Fock space for each mode
- Interior/exterior factorization at horizon
- Thermal state construction
- Density matrix operations

Author: TE_2 Implementation Team
Date: November 20, 2025
"""

import numpy as np
from numpy.typing import NDArray
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import json
from pathlib import Path
from scipy.linalg import expm
import qutip as qt

# Type aliases
DensityMatrix = NDArray[np.complex128]
Operator = NDArray[np.complex128]


@dataclass
class HilbertSpaceConfig:
    """
    Configuration for Hilbert space construction.
    
    Parameters:
        n_modes: Number of near-horizon modes
        n_levels_per_mode: Fock space truncation (0, 1, ..., n_levels-1)
        hawking_temperature: T_H in Planck units
        mode_frequencies: Array of mode frequencies ω_n
    """
    n_modes: int = 5
    n_levels_per_mode: int = 3  # 0, 1, 2 (ground, 1st excited, 2nd excited)
    hawking_temperature: float = 0.003979
    mode_frequencies: NDArray[np.float64] = None
    
    def __post_init__(self):
        """Validate configuration."""
        if self.mode_frequencies is None:
            # Default: harmonic oscillator spectrum
            n = np.arange(self.n_modes)
            self.mode_frequencies = (n + 0.5) * np.pi * self.hawking_temperature
        
        if len(self.mode_frequencies) != self.n_modes:
            raise ValueError(f"mode_frequencies length {len(self.mode_frequencies)} != n_modes {self.n_modes}")


class HorizonHilbertSpace:
    """
    Hilbert space for 1+1D JT black hole horizon.
    
    The horizon is a 0+1D object, so we use a finite-dimensional
    Fock space for near-horizon modes:
        H = ⊗_{n=0}^{N-1} H_n
    where H_n is the Fock space for mode n.
    
    For black hole physics, we further factorize:
        H = H_interior ⊗ H_exterior
    at the horizon.
    """
    
    def __init__(self, config: HilbertSpaceConfig):
        """
        Initialize Hilbert space.
        
        Args:
            config: Configuration parameters
        """
        self.config = config
        
        # Compute dimensions
        self.dim_per_mode = config.n_levels_per_mode
        self.total_dim = self.dim_per_mode ** config.n_modes
        
        # For interior/exterior split, assume half the modes are interior
        self.n_interior_modes = config.n_modes // 2
        self.n_exterior_modes = config.n_modes - self.n_interior_modes
        
        self.dim_interior = self.dim_per_mode ** self.n_interior_modes
        self.dim_exterior = self.dim_per_mode ** self.n_exterior_modes
        
        print(f"Hilbert space constructed:")
        print(f"  Total modes: {config.n_modes}")
        print(f"  Levels per mode: {config.n_levels_per_mode}")
        print(f"  Total dimension: {self.total_dim}")
        print(f"  Interior dimension: {self.dim_interior}")
        print(f"  Exterior dimension: {self.dim_exterior}")
    
    def creation_operator(self, mode_idx: int) -> Operator:
        """
        Creation operator a†_n for mode n.
        
        Args:
            mode_idx: Mode index (0 to n_modes-1)
            
        Returns:
            Creation operator as matrix
        """
        # Use QuTiP for convenience
        a_dag = qt.create(self.dim_per_mode)
        
        # Embed in full Hilbert space (tensor product with identity on other modes)
        operators = []
        for i in range(self.config.n_modes):
            if i == mode_idx:
                operators.append(a_dag)
            else:
                operators.append(qt.qeye(self.dim_per_mode))
        
        # Tensor product
        full_op = qt.tensor(*operators)
        
        return full_op.full()
    
    def annihilation_operator(self, mode_idx: int) -> Operator:
        """
        Annihilation operator a_n for mode n.
        
        Args:
            mode_idx: Mode index (0 to n_modes-1)
            
        Returns:
            Annihilation operator as matrix
        """
        # Use QuTiP for convenience
        a = qt.destroy(self.dim_per_mode)
        
        # Embed in full Hilbert space
        operators = []
        for i in range(self.config.n_modes):
            if i == mode_idx:
                operators.append(a)
            else:
                operators.append(qt.qeye(self.dim_per_mode))
        
        # Tensor product
        full_op = qt.tensor(*operators)
        
        return full_op.full()
    
    def number_operator(self, mode_idx: int) -> Operator:
        """
        Number operator n_n = a†_n a_n for mode n.
        
        Args:
            mode_idx: Mode index (0 to n_modes-1)
            
        Returns:
            Number operator as matrix
        """
        a_dag = self.creation_operator(mode_idx)
        a = self.annihilation_operator(mode_idx)
        
        return a_dag @ a
    
    def hamiltonian(self) -> Operator:
        """
        Free Hamiltonian H = Σ_n ω_n (n_n + 1/2).
        
        Returns:
            Hamiltonian as matrix
        """
        H = np.zeros((self.total_dim, self.total_dim), dtype=np.complex128)
        
        for n in range(self.config.n_modes):
            omega_n = self.config.mode_frequencies[n]
            n_n = self.number_operator(n)
            
            # H += ω_n (n_n + 1/2)
            H += omega_n * (n_n + 0.5 * np.eye(self.total_dim))
        
        return H
    
    def thermal_state(self, temperature: Optional[float] = None) -> DensityMatrix:
        """
        Thermal (Gibbs) state at given temperature:
            ρ_thermal = exp(-H/T) / Z
        where Z = Tr[exp(-H/T)] is the partition function.
        
        Args:
            temperature: Temperature in Planck units (default: Hawking temperature)
            
        Returns:
            Thermal density matrix
        """
        if temperature is None:
            temperature = self.config.hawking_temperature
        
        H = self.hamiltonian()
        
        # Compute exp(-H/T)
        beta = 1.0 / temperature
        rho_unnorm = expm(-beta * H)
        
        # Normalize
        Z = np.trace(rho_unnorm)
        rho = rho_unnorm / Z
        
        return rho
    
    def vacuum_state(self) -> DensityMatrix:
        """
        Vacuum state |0⟩⟨0| (all modes in ground state).
        
        Returns:
            Vacuum density matrix
        """
        # Vacuum is |0,0,...,0⟩
        psi_vac = np.zeros(self.total_dim, dtype=np.complex128)
        psi_vac[0] = 1.0
        
        # Density matrix
        rho_vac = np.outer(psi_vac, psi_vac.conj())
        
        return rho_vac
    
    def fock_state(self, occupation_numbers: List[int]) -> DensityMatrix:
        """
        Fock state |n_0, n_1, ..., n_{N-1}⟩.
        
        Args:
            occupation_numbers: List of occupation numbers for each mode
            
        Returns:
            Fock state density matrix
        """
        if len(occupation_numbers) != self.config.n_modes:
            raise ValueError(f"Need {self.config.n_modes} occupation numbers, got {len(occupation_numbers)}")
        
        # Convert to state index
        state_idx = 0
        for i, n_i in enumerate(occupation_numbers):
            if n_i >= self.dim_per_mode:
                raise ValueError(f"Occupation number {n_i} exceeds truncation {self.dim_per_mode}")
            state_idx += n_i * (self.dim_per_mode ** i)
        
        # Create state vector
        psi = np.zeros(self.total_dim, dtype=np.complex128)
        psi[state_idx] = 1.0
        
        # Density matrix
        rho = np.outer(psi, psi.conj())
        
        return rho
    
    def partial_trace_interior(self, rho: DensityMatrix) -> DensityMatrix:
        """
        Partial trace over interior modes: ρ_exterior = Tr_interior[ρ].
        
        Args:
            rho: Full density matrix
            
        Returns:
            Reduced density matrix for exterior
        """
        # Use QuTiP for partial trace
        rho_qobj = qt.Qobj(rho, dims=[[self.dim_per_mode]*self.config.n_modes]*2)
        
        # Trace out interior modes (first n_interior_modes)
        keep_indices = list(range(self.n_interior_modes, self.config.n_modes))
        
        rho_exterior_qobj = rho_qobj.ptrace(keep_indices)
        
        return rho_exterior_qobj.full()
    
    def partial_trace_exterior(self, rho: DensityMatrix) -> DensityMatrix:
        """
        Partial trace over exterior modes: ρ_interior = Tr_exterior[ρ].
        
        Args:
            rho: Full density matrix
            
        Returns:
            Reduced density matrix for interior
        """
        # Use QuTiP for partial trace
        rho_qobj = qt.Qobj(rho, dims=[[self.dim_per_mode]*self.config.n_modes]*2)
        
        # Trace out exterior modes (last n_exterior_modes)
        keep_indices = list(range(self.n_interior_modes))
        
        rho_interior_qobj = rho_qobj.ptrace(keep_indices)
        
        return rho_interior_qobj.full()
    
    def von_neumann_entropy(self, rho: DensityMatrix) -> float:
        """
        Von Neumann entropy S = -Tr[ρ log ρ].
        
        Args:
            rho: Density matrix
            
        Returns:
            Entropy (in natural units, i.e., nats)
        """
        # Eigenvalues
        eigvals = np.linalg.eigvalsh(rho)
        
        # Remove zeros (log(0) = -∞)
        eigvals = eigvals[eigvals > 1e-15]
        
        # S = -Σ λ_i log λ_i
        S = -np.sum(eigvals * np.log(eigvals))
        
        return S
    
    def entanglement_entropy(self, rho: DensityMatrix) -> float:
        """
        Entanglement entropy between interior and exterior:
            S_ent = S(ρ_interior) = S(ρ_exterior)
        
        Args:
            rho: Full density matrix
            
        Returns:
            Entanglement entropy
        """
        rho_interior = self.partial_trace_exterior(rho)
        S_ent = self.von_neumann_entropy(rho_interior)
        
        return S_ent
    
    def purity(self, rho: DensityMatrix) -> float:
        """
        Purity Tr[ρ²].
        
        Args:
            rho: Density matrix
            
        Returns:
            Purity (1 for pure state, 1/dim for maximally mixed)
        """
        return np.real(np.trace(rho @ rho))
    
    def fidelity(self, rho1: DensityMatrix, rho2: DensityMatrix) -> float:
        """
        Fidelity F(ρ1, ρ2) = Tr[√(√ρ1 ρ2 √ρ1)]².
        
        For pure states |ψ⟩ and |φ⟩: F = |⟨ψ|φ⟩|²
        
        Args:
            rho1: First density matrix
            rho2: Second density matrix
            
        Returns:
            Fidelity (0 to 1)
        """
        # Use QuTiP for convenience
        rho1_qobj = qt.Qobj(rho1)
        rho2_qobj = qt.Qobj(rho2)
        
        F = qt.fidelity(rho1_qobj, rho2_qobj)
        
        return F
    
    def expectation_value(self, rho: DensityMatrix, operator: Operator) -> complex:
        """
        Expectation value ⟨O⟩ = Tr[ρ O].
        
        Args:
            rho: Density matrix
            operator: Operator
            
        Returns:
            Expectation value
        """
        return np.trace(rho @ operator)
    
    def occupation_numbers(self, rho: DensityMatrix) -> NDArray[np.float64]:
        """
        Average occupation numbers ⟨n_i⟩ for each mode.
        
        Args:
            rho: Density matrix
            
        Returns:
            Array of occupation numbers
        """
        n_avg = np.zeros(self.config.n_modes)
        
        for i in range(self.config.n_modes):
            n_i = self.number_operator(i)
            n_avg[i] = np.real(self.expectation_value(rho, n_i))
        
        return n_avg
    
    def save_state(self, rho: DensityMatrix, filepath: Path, metadata: Optional[Dict] = None) -> None:
        """
        Save density matrix to file.
        
        Args:
            rho: Density matrix
            filepath: Output file path
            metadata: Optional metadata dictionary
        """
        data = {
            'density_matrix_real': rho.real.tolist(),
            'density_matrix_imag': rho.imag.tolist(),
            'config': {
                'n_modes': self.config.n_modes,
                'n_levels_per_mode': self.config.n_levels_per_mode,
                'hawking_temperature': self.config.hawking_temperature,
                'mode_frequencies': self.config.mode_frequencies.tolist(),
            },
            'dimensions': {
                'total': self.total_dim,
                'interior': self.dim_interior,
                'exterior': self.dim_exterior,
            },
            'metadata': metadata or {},
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✓ State saved to {filepath}")


def test_hilbert_space():
    """Test Hilbert space construction."""
    print("="*70)
    print("TESTING HILBERT SPACE CONSTRUCTION")
    print("="*70)
    
    # Configuration
    T_H = 0.003979
    n_modes = 5
    mode_freqs = (np.arange(n_modes) + 0.5) * np.pi * T_H
    
    config = HilbertSpaceConfig(
        n_modes=n_modes,
        n_levels_per_mode=3,
        hawking_temperature=T_H,
        mode_frequencies=mode_freqs
    )
    
    # Create Hilbert space
    H = HorizonHilbertSpace(config)
    
    print("\n" + "-"*70)
    print("TEST 1: Vacuum state")
    print("-"*70)
    
    rho_vac = H.vacuum_state()
    print(f"Purity: {H.purity(rho_vac):.6f} (expected: 1.0)")
    print(f"Entropy: {H.von_neumann_entropy(rho_vac):.6f} (expected: 0.0)")
    print(f"Occupation numbers: {H.occupation_numbers(rho_vac)}")
    
    print("\n" + "-"*70)
    print("TEST 2: Thermal state")
    print("-"*70)
    
    rho_thermal = H.thermal_state()
    print(f"Purity: {H.purity(rho_thermal):.6f} (expected: < 1.0)")
    print(f"Entropy: {H.von_neumann_entropy(rho_thermal):.6f} (expected: > 0.0)")
    print(f"Occupation numbers: {H.occupation_numbers(rho_thermal)}")
    
    # Theoretical thermal occupation: ⟨n⟩ = 1/(exp(ω/T) - 1)
    n_thermal_theory = 1 / (np.exp(mode_freqs / T_H) - 1)
    print(f"Theoretical thermal occupation: {n_thermal_theory}")
    
    print("\n" + "-"*70)
    print("TEST 3: Entanglement entropy")
    print("-"*70)
    
    # For thermal state, interior and exterior are entangled
    S_ent_thermal = H.entanglement_entropy(rho_thermal)
    print(f"Thermal state entanglement entropy: {S_ent_thermal:.6f}")
    
    # For vacuum, no entanglement (product state)
    S_ent_vac = H.entanglement_entropy(rho_vac)
    print(f"Vacuum state entanglement entropy: {S_ent_vac:.6f} (expected: 0.0)")
    
    print("\n" + "-"*70)
    print("TEST 4: Fidelity")
    print("-"*70)
    
    F_vac_thermal = H.fidelity(rho_vac, rho_thermal)
    print(f"Fidelity(vacuum, thermal): {F_vac_thermal:.6f}")
    
    F_vac_vac = H.fidelity(rho_vac, rho_vac)
    print(f"Fidelity(vacuum, vacuum): {F_vac_vac:.6f} (expected: 1.0)")
    
    print("\n" + "-"*70)
    print("TEST 5: Hamiltonian")
    print("-"*70)
    
    H_op = H.hamiltonian()
    E_vac = np.real(H.expectation_value(rho_vac, H_op))
    E_thermal = np.real(H.expectation_value(rho_thermal, H_op))
    
    # Vacuum energy: E_0 = Σ_n ω_n / 2
    E_vac_theory = np.sum(mode_freqs) / 2
    
    print(f"Vacuum energy: {E_vac:.6f} (expected: {E_vac_theory:.6f})")
    print(f"Thermal energy: {E_thermal:.6f}")
    
    print("\n" + "="*70)
    print("✓ ALL TESTS COMPLETE")
    print("="*70)


if __name__ == "__main__":
    test_hilbert_space()

