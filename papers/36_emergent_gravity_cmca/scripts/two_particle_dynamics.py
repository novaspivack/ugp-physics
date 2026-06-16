"""
Rank 6-MPD: First Multi-Particle Dynamics Simulation
EPIC_072 — GTE Ontological Unification

Places two gen₁ orbit states (Z₇^5 ring pattern [1,5,2,2,1]) on a shared
3D f_MDL tape and observes their interaction.

This is the FIRST simulation of particle-particle dynamics in the GTE framework.
Previous work only studied: vertex catalogs, single-particle orbits, abundance stats.

Questions:
1. Do two gen₁ patterns attract, repel, or pass through each other?
2. Is Z₇ winding conserved in the interaction?
3. Do they scatter into gen₂/gen₃ patterns (excited states)?
4. Is there any long-range interaction before contact?
"""

import numpy as np
from itertools import product

# ─────────────────────────────────────────────────────────────
# Z₇ f_MDL rule (from GUTStructure.lean)
# ─────────────────────────────────────────────────────────────

def fmdl(l, c, r):
    """The MDL-minimal Z₇ CA rule."""
    return (l + 2*c + r) % 7

def fmdl_step5(ring):
    """One step of fmdl on a 5-cell periodic ring."""
    L = len(ring)
    return [fmdl(ring[(i-1)%L], ring[i], ring[(i+1)%L]) for i in range(L)]

# Known orbit states from GUTStructure.lean
GEN1 = [1, 5, 2, 2, 1]  # gen₁ = Garden of Eden
GEN2 = [2, 5, 2, 0, 2]  # gen₂
GEN3 = [5, 6, 5, 3, 5]  # gen₃
VACUUM = [0, 0, 0, 0, 0] # vacuum

def classify_ring(ring):
    """Classify a 5-cell ring state."""
    if ring == GEN1: return "gen₁"
    if ring == GEN2: return "gen₂"
    if ring == GEN3: return "gen₃"
    if ring == VACUUM: return "vacuum"
    return f"other[{ring}]"

def z7_sum(ring):
    return sum(ring) % 7

# ─────────────────────────────────────────────────────────────
# 1D tape simulation (two gen₁ rings placed at different positions)
# ─────────────────────────────────────────────────────────────

print("=" * 70)
print("Rank 6-MPD: First Multi-Particle Dynamics Simulation")
print("EPIC_072 — GTE Ontological Unification")
print("=" * 70)
print()

# Represent a 1D tape as a list of 5-cell rings
# Tape: N rings arranged in a 1D line
N = 20  # number of ring positions
T = 30  # timesteps

# Initialize: place two gen₁ patterns at positions 5 and 14
# Other positions = vacuum
tape = [VACUUM[:] for _ in range(N)]
tape[5] = GEN1[:]
tape[14] = GEN1[:]

print(f"Initial configuration ({N} ring positions, T={T} steps):")
print(f"  Position 5:  gen₁ = {GEN1} (Z₇ sum = {z7_sum(GEN1)})")
print(f"  Position 14: gen₁ = {GEN1} (Z₇ sum = {z7_sum(GEN1)})")
print(f"  All others:  vacuum = {VACUUM}")
print()

# Evolve: apply fmdl_step5 to each ring position
# Also apply inter-ring coupling: neighboring rings influence each other
# Coupling: the rightmost cell of ring i sees the leftmost cell of ring i+1

def evolve_tape(tape, T):
    """Evolve tape of 5-cell rings for T steps."""
    N = len(tape)
    history = [tape[:]]

    current = [r[:] for r in tape]

    for t in range(T):
        new_tape = []
        for i in range(N):
            # Get the 5-cell ring at position i
            ring = current[i]
            # Internal evolution of the ring
            new_ring = fmdl_step5(ring)
            # Inter-ring coupling: mix with neighbors
            # Left neighbor's rightmost cell influences this ring's leftmost
            left_influence = current[(i-1)%N][-1]  # rightmost cell of left neighbor
            right_influence = current[(i+1)%N][0]   # leftmost cell of right neighbor
            # Apply coupling: ring[0] is influenced by left, ring[4] by right
            new_ring[0] = fmdl(left_influence, new_ring[0], new_ring[1]) if len(new_ring) > 1 else new_ring[0]
            new_ring[4] = fmdl(new_ring[3], new_ring[4], right_influence) if len(new_ring) > 4 else new_ring[4]
            new_tape.append(new_ring)
        current = new_tape
        history.append([r[:] for r in current])

    return history

history = evolve_tape(tape, T)

# ─────────────────────────────────────────────────────────────
# Analysis
# ─────────────────────────────────────────────────────────────

print("EVOLUTION RESULTS:")
print(f"{'Step':>4} {'Position summary'}")
print("-" * 70)

for t in [0, 5, 10, 15, 20, 25, 30]:
    if t < len(history):
        state = history[t]
        # Classify each ring
        classifications = [classify_ring(r) for r in state]
        non_vacuum = [(i, c) for i, c in enumerate(classifications) if c != "vacuum"]
        z7_total = sum(z7_sum(r) for r in state) % 7
        print(f"  t={t:2d}: {non_vacuum}  Z₇_total={z7_total}")

print()

# Check Z₇ winding conservation
print("Z₇ WINDING CONSERVATION:")
initial_z7 = sum(z7_sum(r) for r in history[0]) % 7
print(f"  Initial Z₇ total (mod 7): {initial_z7}")
for t in [5, 10, 15, 20, 25, 30]:
    if t < len(history):
        current_z7 = sum(z7_sum(r) for r in history[t]) % 7
        conserved = "YES" if current_z7 == initial_z7 else "NO"
        print(f"  t={t:2d}: Z₇ total = {current_z7}  conserved={conserved}")

print()

# Identify when the two particles meet (collision)
print("INTERACTION ANALYSIS:")
collision_detected = False
for t in range(len(history)):
    state = history[t]
    non_vacuum_positions = [i for i, r in enumerate(state) if r != VACUUM]
    if len(non_vacuum_positions) >= 2:
        if max(non_vacuum_positions) - min(non_vacuum_positions) <= 3:
            print(f"  t={t}: Particles in contact at positions {non_vacuum_positions}")
            collision_detected = True
            # Show state detail at collision
            print(f"  Ring states at collision:")
            for pos in non_vacuum_positions:
                print(f"    pos {pos}: {state[pos]} -> {classify_ring(state[pos])}")
            break
    elif len(non_vacuum_positions) == 0:
        print(f"  t={t}: Both particles annihilated!")
        collision_detected = True
        break

if not collision_detected:
    print(f"  Particles did not interact within T={T} steps")
    print(f"  (may need larger tape or different initial positions)")
    # Show final non-vacuum positions
    final_state = history[-1]
    final_non_vacuum = [(i, classify_ring(r), r) for i, r in enumerate(final_state) if r != VACUUM]
    print(f"  Final non-vacuum positions: {[(i,c) for i,c,r in final_non_vacuum]}")

print()

# Track each particle's "center of mass" over time
print("PARTICLE TRAJECTORIES:")
print("  (tracking non-vacuum ring positions over time)")
for t in range(0, T+1, 5):
    if t < len(history):
        state = history[t]
        non_vac = [(i, classify_ring(r)) for i, r in enumerate(state) if r != VACUUM]
        print(f"  t={t:2d}: {non_vac}")

print()

# Track gen₁ vs gen₂/gen₃ counts over time
print("GENERATION COMPOSITION OVER TIME:")
print(f"  {'t':>4} {'gen₁':>8} {'gen₂':>8} {'gen₃':>8} {'other':>8}")
print(f"  {'-'*4} {'-'*8} {'-'*8} {'-'*8} {'-'*8}")
for t in range(0, T+1, 5):
    if t < len(history):
        state = history[t]
        classes = [classify_ring(r) for r in state]
        g1 = classes.count("gen₁")
        g2 = classes.count("gen₂")
        g3 = classes.count("gen₃")
        other = sum(1 for c in classes if c not in ("vacuum","gen₁","gen₂","gen₃"))
        print(f"  {t:>4} {g1:>8} {g2:>8} {g3:>8} {other:>8}")

print()
print("─" * 50)
print("SUMMARY")
print("─" * 50)
print("""
   This is the FIRST particle-particle interaction simulation in GTE.

   Notes on the coupling model:
   - This uses a simplified inter-ring coupling (boundary cell exchange)
   - The 'correct' coupling depends on the 3D f_MDL spatial embedding
   - This simulation establishes the methodology; results are preliminary

   Key questions answered here:
   1. Do particles evolve independently? -> Check if non-vacuum sites appear away from initial positions
   2. Is Z₇ winding conserved? -> See conservation table above
   3. Do they produce gen₂/gen₃ on interaction? -> See generation composition table
""")
