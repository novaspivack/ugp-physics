from pathlib import Path
SCRIPT_DIR = Path(__file__).resolve().parent
#!/usr/bin/env python3
"""
Check if M=5 Rule 110's 7 majority=0 attractors are phase offsets of ether.

The period-14 ether pattern: 11111000100110
Sampled at 7 phase offsets × 5 consecutive cells gives 7 × 5 = 35 possible
5-cell windows... but there are only 14 cells × 5-cell windows = 14 windows.

The hypothesis: the 7 majority=0 attractors of M=5 Rule 110 (periodic) are
exactly the 7 distinct 5-cell windows from the ether pattern that have
majority=0 (≤2 ones in 5 cells).

If true: Z₇ is embedded in M=5 binary Rule 110 via ether phase labeling.
"""

import numpy as np

RULE = 110
M = 5
ETHER = [1,1,1,1,1,0,0,0,1,0,0,1,1,0]  # period-14

def apply_rule110(state):
    L = len(state)
    return np.array([(RULE >> (state[(i-1)%L]*4 + state[i]*2 + state[(i+1)%L])) & 1 
                     for i in range(L)], dtype=np.uint8)

def find_attractor(initial, max_steps=500):
    """Find the eventual cycle that this IC enters."""
    state = initial.copy()
    seen = {}
    traj = []
    for step in range(max_steps):
        key = tuple(state)
        if key in seen:
            cycle_start = seen[key]
            cycle = traj[cycle_start:]
            maj_seq = [int(s.sum() * 2 > M) for s in cycle]
            return cycle[0], len(cycle), maj_seq
        seen[key] = step
        traj.append(state.copy())
        state = apply_rule110(state)
    return None, None, None

print("=" * 60)
print("M=5 Rule 110: Attractor Z₇ Phase Analysis")
print("=" * 60)

# Extract all 14 five-cell windows from the ether
ether_windows = []
for start in range(14):
    window = np.array([ETHER[(start+j) % 14] for j in range(M)], dtype=np.uint8)
    ether_windows.append((start, window, int(window.sum() * 2 > M)))

print(f"\n14 five-cell windows from ether (phase → window → majority):")
windows_maj0 = []
windows_maj1 = []
for phase, win, maj in ether_windows:
    label = "maj=0" if maj == 0 else "maj=1"
    print(f"  Phase {phase:2d}: {win.tolist()} → {label}")
    if maj == 0:
        windows_maj0.append((phase, win))
    else:
        windows_maj1.append((phase, win))

print(f"\nMajority=0 windows: {len(windows_maj0)} (phases: {[p for p,_ in windows_maj0]})")
print(f"Majority=1 windows: {len(windows_maj1)} (phases: {[p for p,_ in windows_maj1]})")

# Find all M=5 attractors
print(f"\nFinding all M=5 Rule 110 attractors (2^5 = 32 ICs)...")
attractors_0 = []
attractors_1 = []
seen_attractors = set()

for ic in range(2**M):
    initial = np.array([(ic >> (M-1-j)) & 1 for j in range(M)], dtype=np.uint8)
    cycle_state, period, maj_seq = find_attractor(initial)
    
    if cycle_state is None:
        continue
    
    key = tuple(cycle_state)
    if key in seen_attractors:
        continue
    seen_attractors.add(key)
    
    majority_type = all(m == 0 for m in maj_seq)
    if majority_type:
        attractors_0.append(cycle_state)
    else:
        attractors_1.append(cycle_state)

print(f"\nDistinct attractors:")
print(f"  Majority=0: {len(attractors_0)} attractors")
print(f"  Majority=1: {len(attractors_1)} attractors")

# Check if majority=0 attractors match ether windows
print(f"\nDo majority=0 attractors match ether windows?")
matched = 0
for attr in attractors_0:
    attr_list = attr.tolist()
    for phase, win in windows_maj0:
        if attr_list == win.tolist():
            print(f"  ✅ Attractor {attr_list} = ether phase {phase}")
            matched += 1
            break
    else:
        # Check if it's a cycle that visits ether windows
        print(f"  ? Attractor {attr_list} — not a direct ether window match")

print(f"\n{'='*60}")
print(f"CONCLUSION:")
if matched == len(attractors_0):
    print(f"✅ ALL {len(attractors_0)} majority=0 attractors are ether windows!")
    print(f"   Z₇ embedding CONFIRMED: M=5 attractors ↔ ether phases {[p for p,_ in windows_maj0]}")
    print(f"   The 7 attractors correspond to the 7 phases of the period-14 ether")
    print(f"   with majority=0 when sampled on 5 consecutive cells.")
else:
    print(f"  {matched}/{len(attractors_0)} attractors matched ether windows")
    print(f"  Partial Z₇ embedding or different structure")
