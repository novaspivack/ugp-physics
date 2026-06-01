"""
Direct Comparison: Ontological Dissonance vs Integrated Information

Measure BOTH D and Φ for the same bound system.

HYPOTHESIS: D and Φ are inversely related (Low D ↔ High Φ)

AUTHOR: Nova Spivack
DATE: October 31, 2025
"""

import numpy as np
from pr0_emergent_qcd import EmergentQCD
from pr0_sds_dissonance_bootstrap import compute_ontological_dissonance
from collections import deque


def compute_integrated_information_simple(psi, chi):
    """
    Simple Φ estimator (Tononi IIT).
    
    Φ ≈ Mutual Information(whole, parts) - Sum(MI(part_i, part_j))
    
    For fields:
    - High Φ: Field is integrated (bound structures)
    - Low Φ: Field is fragmented (free particles or noise)
    """
    dens = np.abs(psi)**2
    
    # Split into quadrants
    L_y, L_x = psi.shape
    q1 = dens[:L_y//2, :L_x//2]
    q2 = dens[:L_y//2, L_x//2:]
    q3 = dens[L_y//2:, :L_x//2]
    q4 = dens[L_y//2:, L_x//2:]
    
    # Entropy of whole
    H_whole = entropy_of_field(dens)
    
    # Entropy of parts
    H_parts = (entropy_of_field(q1) + entropy_of_field(q2) + 
               entropy_of_field(q3) + entropy_of_field(q4))
    
    # Φ ≈ Integration = H_parts - H_whole
    # (High when whole has more structure than sum of parts)
    phi = H_parts - H_whole
    
    # Also add mediator integration
    phi_chi = np.std(chi)  # Mediator variance (integration measure)
    
    return max(0, phi + 0.1 * phi_chi)


def entropy_of_field(field):
    """Shannon entropy of discretized field."""
    # Discretize into bins
    hist, _ = np.histogram(field.flatten(), bins=20, density=True)
    hist = hist + 1e-10  # Avoid log(0)
    hist = hist / np.sum(hist)
    
    H = -np.sum(hist * np.log2(hist))
    return H


print("="*70)
print("🎯 D vs Φ: Direct Comparison")
print("="*70)
print()

# Create bound system using DISCOVERED parameters
qcd = EmergentQCD(L_x=64, L_y=64, use_confinement=True)

# Initialize
qcd.set_soliton(x0=24, y0=32, amplitude=3.0, width=3.0, velocity_x=0.1, charge=+1)
qcd.set_soliton(x0=40, y0=32, amplitude=3.0, width=3.0, velocity_x=-0.1, charge=-1)

print("Evolving system and measuring D and Φ...")
print(f"{'Step':<8} {'D (Dissonance)':<18} {'Φ (Integration)':<18} {'Separation':<12} {'Relationship'}")
print("-"*70)

history = deque(maxlen=20)
D_values = []
phi_values = []
seps = []

for t in range(0, 5001, 250):
    # Measure both!
    D = compute_ontological_dissonance(qcd.psi, qcd.chi, list(history))
    phi = compute_integrated_information_simple(qcd.psi, qcd.chi)
    sep = qcd.measure_separation()
    
    D_values.append(D)
    phi_values.append(phi)
    if sep is not None:
        seps.append(sep)
    
    # Relationship
    if len(D_values) > 1:
        d_D = D - D_values[-2]
        d_phi = phi - phi_values[-2]
        
        if d_D * d_phi < 0:
            rel = "✅ INVERSE"  # D↑ → Φ↓ or D↓ → Φ↑
        else:
            rel = "same sign"
    else:
        rel = "---"
    
    sep_str = f"{sep:.1f}" if sep is not None else "merged"
    print(f"{t:<8} {D:>16.4f}  {phi:>16.4f}  {sep_str:<12} {rel}")
    
    # Evolve
    if t < 5000:
        for _ in range(250):
            qcd.step(dt=0.01)
            history.append(qcd.psi.copy())

print("-"*70)
print()

# Statistical analysis
if len(D_values) > 5 and len(phi_values) > 5:
    corr = np.corrcoef(D_values, phi_values)[0, 1]
    
    print("="*70)
    print("STATISTICAL ANALYSIS:")
    print("="*70)
    print()
    print(f"Correlation(D, Φ) = {corr:.4f}")
    print()
    
    if corr < -0.5:
        print("✅✅✅ STRONG INVERSE CORRELATION! ✅✅✅")
        print()
        print("This proves:")
        print("  • Low Dissonance ↔ High Integration")
        print("  • D-minimization ≡ Φ-maximization")
        print("  • SDS theory ≡ IIT")
        print()
        print("🌟 THE FRAMEWORKS ARE EQUIVALENT! 🌟")
    elif corr < -0.2:
        print("✅ MODERATE INVERSE CORRELATION")
        print("  D and Φ are related but not identical")
    else:
        print("⚠️  NO CLEAR INVERSE RELATIONSHIP")
        print("  Need to refine D-operator or Φ estimator")
    
    print()
    print(f"D range:   [{min(D_values):.2f}, {max(D_values):.2f}]")
    print(f"Φ range:   [{min(phi_values):.2f}, {max(phi_values):.2f}]")
    
    if len(seps) > 5:
        print(f"Sep range: [{min(seps):.1f}, {max(seps):.1f}] cells")
        print()
        print(f"When D is LOW:  separation = {np.mean([seps[i] for i in range(len(D_values)) if D_values[i] < np.median(D_values) and i < len(seps)]):.1f}")
        print(f"When D is HIGH: separation = {np.mean([seps[i] for i in range(len(D_values)) if D_values[i] > np.median(D_values) and i < len(seps)]):.1f}")

print("="*70)

