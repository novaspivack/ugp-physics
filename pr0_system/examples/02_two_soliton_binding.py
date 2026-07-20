"""
Example 2: Two Solitons with Mediator - Binding

This example demonstrates:
- Two opposite-charge solitons
- Mediator field evolution
- Adaptive damping
- Binding behavior

Author: AI Assistant
Date: October 31, 2025
"""

import sys
sys.path.insert(0, '..')

from pr0_system.core import Lattice, FieldState
from pr0_system.evolution import MediatorField, AdaptiveDamping
import numpy as np

# Create system
print("Setting up two-soliton system...")
lattice = Lattice(L_x=64, L_y=64, lattice_type='square', periodic=True)
state = FieldState(lattice)

# Add two solitons approaching each other
state.add_soliton(x0=24, y0=32, amplitude=3.0, width=3.0, 
                 velocity_x=0.02, charge=+1)
state.add_soliton(x0=40, y0=32, amplitude=3.0, width=3.0,
                 velocity_x=-0.02, charge=-1)

print(f"Initial state: {state}")

# Create evolution operators
mediator = MediatorField(g=0.1, gamma_chi=0.1, m_chi=0.0)
damping = AdaptiveDamping(gamma_base=0.013, gamma_scale=0.644)

print(f"Mediator: {mediator}")
print(f"Damping: {damping}")

# Evolve
print("\nEvolving for 1000 steps...")
dt = 0.01

for t in range(1000):
    # Ablowitz-Ladik (simplified)
    lap_psi = lattice.laplacian(state.psi)
    psi_mag = np.abs(state.psi)
    alpha = 0.5
    nonlin = alpha * psi_mag**2 * state.psi / (1.0 + alpha * psi_mag**2)
    
    # Start with AL equation
    dpsi_dt = 1j * (lap_psi + nonlin)
    
    # Add mediator force
    med_force = mediator.compute_force_on_psi(state.chi, state.psi)
    dpsi_dt += med_force
    
    # Add damping
    damp_term = damping.apply(state.psi, dt)
    dpsi_dt += damp_term
    
    # Update ψ
    state.psi += dt * dpsi_dt
    state.clip_fields()
    
    # Update χ
    state.chi, state.chi_dot = mediator.evolve(state.chi, state.chi_dot, 
                                               state.psi, dt)
    
    # Track
    if t % 200 == 0:
        state.save_history()
        print(f"  Step {t:4d}: E={state.get_total_energy():8.3f}, "
              f"|ψ|²_max={np.max(np.abs(state.psi)**2):6.3f}")

state.timestep = 1000

print(f"\nFinal state: {state}")
print("\n✅ Example complete!")
print("\nThe two solitons should have bound together via the mediator field.")

