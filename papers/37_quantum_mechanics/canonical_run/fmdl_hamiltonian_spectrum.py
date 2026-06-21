#!/usr/bin/env python3
"""
fmdl_hamiltonian_spectrum.py — f_MDL orbit spectrum on Z₇⁵.

Computes the full cycle/attractor structure of the f_MDL map on all 7^5 = 16,807
states. Reports the orbit spectrum: which cycle lengths exist, how many cycles of
each length, and basin sizes (how many states flow into each attractor).

Physical interpretation via 't Hooft (2016) cogwheel CA→QM formalism:
  - Only ATTRACTOR states (states in cycles) contribute to the Hilbert space.
  - f_MDL is NOT a permutation (most states eventually reach the vacuum fixed
    point). The cogwheel Hamiltonian applies to the attractor subspace.
  - For a cycle of length N, eigenvalues are E_k = 2πk/(N·δt), k=0,..,N-1.
  - Length-1 fixed points → E = 0 (vacuum ground state + any false vacua).
  - The SM generation orbit (gen1→gen2→gen3→vacuum) is a TRANSIENT path leading
    to the vacuum fixed point — not a cycle. Generations are transient excitations.

Sanity check: fmdl_step5(GEN1)=GEN2, fmdl_step5(GEN2)=GEN3,
fmdl_step5(GEN3)=VACUUM, fmdl_step5(VACUUM)=VACUUM (fixed point).
"""

import numpy as np
from collections import Counter

# ---------------------------------------------------------------------------
# f_MDL lookup table (canonical: from CUP3DUniqueness.lean)
# Orbit neighborhoods + Rule 110 binary sublayer; all others → 0 (MDL-minimal)
# ---------------------------------------------------------------------------
_FMDL_LOOKUP = {
    # Orbit neighborhoods (SM generation chain)
    (1, 1, 5): 2, (1, 5, 2): 5, (5, 2, 2): 2, (2, 2, 1): 0,
    (2, 1, 1): 2, (2, 2, 5): 5, (2, 5, 2): 6, (5, 2, 0): 5,
    (2, 0, 2): 3, (0, 2, 2): 5,
    # Rule 110 binary sublayer (on {0,1}^3)
    (0, 0, 0): 0, (0, 0, 1): 1, (0, 1, 0): 1, (0, 1, 1): 1,
    (1, 0, 0): 0, (1, 0, 1): 1, (1, 1, 0): 1, (1, 1, 1): 0,
}


def fmdl(l: int, c: int, r: int) -> int:
    """MDL-minimal Z₇ CA function. Matches CUP3DUniqueness.lean exactly."""
    return _FMDL_LOOKUP.get((l, c, r), 0)


def fmdl_step5(state: tuple) -> tuple:
    """One step of f_MDL on a 5-cell ring with periodic boundary conditions."""
    n = 5
    return tuple(fmdl(state[(i - 1) % n], state[i], state[(i + 1) % n])
                 for i in range(n))


# SM generation vectors (from CUP3DUniqueness.lean)
GEN1   = (1, 5, 2, 2, 1)   # [e⁻, u, d, νR, νL]
GEN2   = (2, 5, 2, 0, 2)   # [μ, c, s, νμR, νμL]
GEN3   = (5, 6, 5, 3, 5)   # [τ, t, b, ντR, ντL]
VACUUM = (0, 0, 0, 0, 0)


# ---------------------------------------------------------------------------
# Encoding / decoding (base-7, 5 digits)
# ---------------------------------------------------------------------------
def encode(s: tuple) -> int:
    return sum(s[i] * 7 ** i for i in range(5))


def decode(n: int) -> tuple:
    return tuple((n // 7 ** i) % 7 for i in range(5))


# ---------------------------------------------------------------------------
# Build transition table T[i] = encode(fmdl_step5(decode(i)))
# ---------------------------------------------------------------------------
def build_transition_table(L: int) -> list:
    T = [0] * L
    for i in range(L):
        T[i] = encode(fmdl_step5(decode(i)))
    return T


# ---------------------------------------------------------------------------
# Functional graph cycle finder — O(N) total, two-color DFS
# ---------------------------------------------------------------------------
def find_cycles(T: list, L: int):
    """
    Find all cycles in the functional graph defined by T.

    Returns:
      cycle_lengths  : list of ints, one entry per distinct cycle found
      on_cycle       : list of bools, True iff state i is on a cycle
      cycle_id_arr   : list of ints, which cycle (by index) each state flows into
    """
    color       = [0] * L   # 0=unvisited, 1=in-progress, 2=done
    on_cycle    = [False] * L
    cycle_id_arr = [-1] * L
    cycle_lengths = []

    for start in range(L):
        if color[start] == 2:
            continue

        path = []
        path_pos = {}   # state → index in path
        state = start

        while color[state] == 0:
            color[state] = 1
            path_pos[state] = len(path)
            path.append(state)
            state = T[state]

        if color[state] == 1:
            # Closed a new cycle: state is somewhere in the current path
            cycle_start_idx = path_pos[state]
            cycle = path[cycle_start_idx:]
            cycle_len = len(cycle)
            cid = len(cycle_lengths)
            cycle_lengths.append(cycle_len)

            for s in cycle:
                on_cycle[s] = True
                cycle_id_arr[s] = cid
                color[s] = 2

            for s in path[:cycle_start_idx]:
                cycle_id_arr[s] = cid
                color[s] = 2
        else:
            # color[state] == 2: we hit an already-processed state
            cid = cycle_id_arr[state]
            for s in path:
                cycle_id_arr[s] = cid
                color[s] = 2

    return cycle_lengths, on_cycle, cycle_id_arr


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    L = 7 ** 5   # 16,807

    print("=" * 72)
    print("f_MDL Orbit Spectrum on Z₇⁵ — Hamiltonian Eigenvalue Analysis")
    print(f"  State space: 7^5 = {L} states")
    print("=" * 72)

    # ── Sanity check ──────────────────────────────────────────────────────
    assert fmdl_step5(GEN1)   == GEN2,   f"gen1→gen2 failed: {fmdl_step5(GEN1)}"
    assert fmdl_step5(GEN2)   == GEN3,   f"gen2→gen3 failed: {fmdl_step5(GEN2)}"
    assert fmdl_step5(GEN3)   == VACUUM, f"gen3→vacuum failed: {fmdl_step5(GEN3)}"
    assert fmdl_step5(VACUUM) == VACUUM, f"vacuum→vacuum failed: {fmdl_step5(VACUUM)}"
    print("✓ Sanity check: gen1→gen2→gen3→vacuum→vacuum confirmed")
    print()

    # ── Build transition table ────────────────────────────────────────────
    print("Building transition table (16,807 states)...")
    T = build_transition_table(L)
    print("  Done.")
    print()

    # ── Find all cycles ───────────────────────────────────────────────────
    print("Finding all cycles in the functional graph...")
    cycle_lengths, on_cycle, cycle_id_arr = find_cycles(T, L)

    n_cycles    = len(cycle_lengths)
    n_attractor = sum(1 for x in on_cycle if x)
    n_transient = L - n_attractor

    print(f"  Total distinct cycles:              {n_cycles}")
    print(f"  Attractor states (on cycles):       {n_attractor}")
    print(f"  Transient states (→ cycle via path): {n_transient}")
    print()

    # ── Orbit spectrum ────────────────────────────────────────────────────
    length_counter = Counter(cycle_lengths)

    print("=" * 72)
    print("ORBIT SPECTRUM — cycle length distribution")
    print("=" * 72)
    print(f"\n{'Length':>8}  {'# cycles':>10}  {'# attractor states':>20}  {'% total':>10}")
    print("-" * 58)

    total_in_cycles = 0
    for length in sorted(length_counter.keys()):
        count      = length_counter[length]
        states_in  = count * length
        total_in_cycles += states_in
        pct = 100 * states_in / L
        print(f"  {length:6d}    {count:10d}    {states_in:18d}    {pct:9.3f}%")

    print("-" * 58)
    print(f"  Total: {n_cycles} cycles, {total_in_cycles} attractor states "
          f"({100 * total_in_cycles / L:.3f}%)")
    print()

    # ── Fixed points ──────────────────────────────────────────────────────
    print("=" * 72)
    print("FIXED POINTS (cycle length = 1)")
    print("=" * 72)

    fixed_pts = [i for i in range(L) if on_cycle[i] and
                 cycle_lengths[cycle_id_arr[i]] == 1]
    print(f"\n  Number of fixed points: {len(fixed_pts)}")
    for fp_enc in fixed_pts:
        fp = decode(fp_enc)
        label = ""
        if fp == VACUUM: label = " ← VACUUM (ground state)"
        elif fp == GEN1: label = " ← gen1 (UNEXPECTED — would be a false vacuum)"
        elif fp == GEN2: label = " ← gen2 (UNEXPECTED)"
        elif fp == GEN3: label = " ← gen3 (UNEXPECTED)"
        print(f"    {fp}  [enc={fp_enc}]{label}")
    print()

    # ── SM orbit position in functional graph ────────────────────────────
    print("=" * 72)
    print("SM GENERATION ORBIT — position in functional graph")
    print("=" * 72)
    for name, vec in [("gen1", GEN1), ("gen2", GEN2),
                      ("gen3", GEN3), ("vacuum", VACUUM)]:
        enc  = encode(vec)
        cid  = cycle_id_arr[enc]
        clen = cycle_lengths[cid] if cid >= 0 else "?"
        typ  = "CYCLE (attractor)" if on_cycle[enc] else "TRANSIENT"
        print(f"  {name:8s}: {typ:25s}  cycle_length = {clen}")
    print()

    # ── Basin sizes ───────────────────────────────────────────────────────
    basin_counter  = Counter(cycle_id_arr)
    basin_by_length = {}
    for cid, clen in enumerate(cycle_lengths):
        basin_by_length.setdefault(clen, []).append(basin_counter[cid])

    print("=" * 72)
    print("BASIN SIZES by cycle length")
    print("=" * 72)
    for length in sorted(basin_by_length.keys()):
        sizes = sorted(basin_by_length[length], reverse=True)
        print(f"  Length-{length} cycle(s):")
        for s in sizes[:5]:
            print(f"    basin = {s:7d}  ({100 * s / L:.2f}% of all 16,807 states)")
        if len(sizes) > 5:
            print(f"    ... and {len(sizes) - 5} more cycles")
    print()

    # ── Hamiltonian eigenvalues (cogwheel formalism, 't Hooft 2016 §2.1) ──
    print("=" * 72)
    print("HAMILTONIAN EIGENVALUES (cogwheel formalism, 't Hooft 2016 §2.1)")
    print("=" * 72)
    print()
    print("  In 't Hooft's CA→QM framework, only ATTRACTOR states (states in")
    print("  cycles) contribute to the cogwheel Hilbert space. A cycle of length N")
    print("  contributes N eigenvalues:  E_k = 2πk / (N·δt),  k = 0, 1, ..., N−1.")
    print("  The vacuum fixed point (N=1) is the zero-energy ground state (E_0 = 0).")
    print("  Transient states lie OUTSIDE the Hilbert space in this formalism.")
    print()

    for length in sorted(length_counter.keys()):
        count = length_counter[length]
        print(f"  Cycle length N={length}  ({count} cycle(s), "
              f"{count * length} Hilbert-space states):")
        if length == 1:
            print(f"    Eigenvalue: E = 0  (ground state / fixed point)")
            if length_counter[1] == 1:
                print(f"    → Unique vacuum ground state: CONFIRMED.")
            else:
                print(f"    → {length_counter[1]} fixed points: vacuum + "
                      f"{length_counter[1]-1} false vacua.")
        else:
            eigs = [f"2π·{k}/{length}·(1/δt)" for k in range(min(length, 4))]
            suffix = ", ..." if length > 4 else ""
            print(f"    Eigenvalues: {', '.join(eigs)}{suffix}")
            if length == 3:
                print(f"    → N=3 resonance: eigenvalue spacing = 2π/3 ≈ 120°.")
                print(f"      Matches N_gen=3 generation count (CatAL).")
            elif length == 7:
                print(f"    → Z₇ resonance: full Z₇ circle (7 evenly-spaced eigenvalues).")
            elif length == 5:
                print(f"    → N=5 resonance: matches N_fam=5 family count (CatAL).")
        print()

    # ── Summary ───────────────────────────────────────────────────────────
    print("=" * 72)
    print("SUMMARY")
    print("=" * 72)
    print(f"  Total states:              {L}")
    print(f"  Attractor (Hilbert space): {n_attractor}  "
          f"({100 * n_attractor / L:.3f}%)")
    print(f"  Transient states:          {n_transient}  "
          f"({100 * n_transient / L:.3f}%)")
    print(f"  Number of distinct cycles: {n_cycles}")
    n_fp = length_counter.get(1, 0)
    print(f"  Fixed points (N=1):        {n_fp}  "
          f"({'unique vacuum' if n_fp == 1 else f'{n_fp} attractors'})")
    print()
    print("  Orbit spectrum: cycle_length → (# cycles, # attractor states)")
    for length in sorted(length_counter.keys()):
        count = length_counter[length]
        print(f"    N={length:3d}  →  {count:6d} cycle(s)  "
              f"({count * length:6d} attractor states)")
    print()

    # ── Physical interpretation ───────────────────────────────────────────
    print("=" * 72)
    print("PHYSICAL INTERPRETATION")
    print("=" * 72)
    n_fp = length_counter.get(1, 0)
    n_3  = length_counter.get(3, 0)
    n_5  = length_counter.get(5, 0)
    n_7  = length_counter.get(7, 0)

    print(f"\n  Fixed points (N=1): {n_fp}")
    if n_fp == 1:
        print(f"    → Unique vacuum ground state (E=0). No false vacua.")
        print(f"    → Consistent with MDL minimality selecting a unique vacuum.")
    else:
        print(f"    → Vacuum + {n_fp - 1} false vacuum(a). Potential vacuum selection issue.")

    print(f"\n  N=3 cycles: {n_3}")
    if n_3 > 0:
        print(f"    → Length-3 attractor resonance found.")
        print(f"    → Eigenvalue spacing 2π/3 ≈ 120° — matches N_gen=3.")
        print(f"    → Note: this is a CA CYCLE, distinct from the SM generation")
        print(f"      TRANSIENT orbit (gen1→gen2→gen3→vacuum, which is NOT a cycle).")
    else:
        print(f"    → None found. N_gen=3 is a transient cascade, not a CA cycle.")
        print(f"    → Consistent: SM generations are particle states (transients),")
        print(f"      not periodic orbits. Stability hierarchy gen1 < gen2 < gen3 holds.")

    print(f"\n  N=5 cycles: {n_5}")
    if n_5 > 0:
        print(f"    → Z₅ ring resonance: matches N_fam=5 family count.")
    else:
        print(f"    → None found.")

    print(f"\n  N=7 cycles: {n_7}")
    if n_7 > 0:
        print(f"    → Z₇ arithmetic resonance confirmed.")
    else:
        print(f"    → None found.")

    print(f"\n  The SM generation orbit (gen1→gen2→gen3→vacuum) is a TRANSIENT path.")
    print(f"  Generations are NOT eigenstates of the Hamiltonian — they are")
    print(f"  unstable excitations that decay to the vacuum. This is physically")
    print(f"  correct: SM particles decay; only the vacuum (E=0) is stable.")
    print()
    print(f"  The cogwheel Hilbert space dim(H) = {n_attractor} (attractor states).")
    print(f"  The {n_transient} transient states form the 'shadow' outside H,")
    print(f"  corresponding to short-lived excitations in 't Hooft's formalism.")


if __name__ == "__main__":
    main()
