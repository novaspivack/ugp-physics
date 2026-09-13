"""
Example 1: Create and Evolve a Single Soliton

This example demonstrates:
- Creating a lattice
- Initializing a field state
- Adding a soliton
- Basic field evolution

Author: AI Assistant
Date: October 31, 2025
"""

import sys
sys.path.insert(0, '..')

from pr0_system.core import Lattice, FieldState
import numpy as np

# Create lattice
print("Creating 64×64 square lattice with periodic boundaries...")
lattice = Lattice(L_x=64, L_y=64, lattice_type='square', periodic=True)
print(f"  {lattice}")

# Create field state
print("\nInitializing field state...")
state = FieldState(lattice)
print(f"  {state}")

# Add a soliton
print("\nAdding soliton at center...")
state.add_soliton(
    x0=32, y0=32,
    amplitude=3.0,
    width=3.0,
    velocity_x=0.05,
    charge=+1
)

print(f"  After adding soliton: {state}")
print(f"  Total energy: {state.get_total_energy():.3f}")
print(f"  Total charge: {state.get_total_charge():.3f}")

# Evolve (without forces - just free propagation)
print("\nEvolving for 100 steps...")
for t in range(100):
    # Simple Euler step (for demonstration)
    lap_psi = lattice.laplacian(state.psi)
    dpsi_dt = 1j * lap_psi  # Free Schrödinger
    state.psi += 0.01 * dpsi_dt
    
    if t % 20 == 0:
        state.save_history()

state.timestep = 100

print(f"  After evolution: {state}")
print(f"  Total energy: {state.get_total_energy():.3f}")
print(f"  Total charge: {state.get_total_charge():.3f}")

print("\n✅ Example complete!")
print("\nThe soliton has propagated freely with velocity_x=0.05")

