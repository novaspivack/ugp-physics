#!/usr/bin/env python3
"""
fmdl_z74_orbit_spectrum.py — f_MDL orbit spectrum on Z₇⁴ (dark sector ring).

Applies the same orbit decomposition as fmdl_hamiltonian_spectrum.py (Z₇⁵, SM sector)
to the 4-cell periodic ring Z₇⁴ (2401 states). The dark sector has N_gen^dark = 4
(one fewer generation than the visible sector), suggesting it corresponds to a 4-cell
ring rather than the SM 5-cell ring.

Physical questions tested:
  1. Does Z₇⁴ have any cycles of length > 1?
     (If yes, those are stable dark sector quantum states in the 't Hooft framework.)
  2. What is the maximum tail length in Z₇⁴?
     (Compare to Z₇⁵ maximum tail length = 7 steps.)
  3. Are there states in Z₇⁴ that parallel the SM generation structure?
  4. GoE count and predecessor structure — does Z₇⁴ share the information-loss
     character of Z₇⁵?

Reference:
    Lab notes: 77_LAB_NOTES_RANK95_ROUND01_fmdl_hamiltonian_spectrum.md
    (Z₇⁵ result: 1 cycle = vacuum, max tail = 7, 16,590 GoE states)
"""

from collections import Counter

# ---------------------------------------------------------------------------
# f_MDL lookup table (canonical, identical to Z₇⁵ analysis)
# ---------------------------------------------------------------------------
_FMDL_LOOKUP = {
    # SM generation orbit neighborhoods
    (1, 1, 5): 2, (1, 5, 2): 5, (5, 2, 2): 2, (2, 2, 1): 0,
    (2, 1, 1): 2, (2, 2, 5): 5, (2, 5, 2): 6, (5, 2, 0): 5,
    (2, 0, 2): 3, (0, 2, 2): 5,
    # Rule 110 binary sublayer on {0,1}^3
    (0, 0, 0): 0, (0, 0, 1): 1, (0, 1, 0): 1, (0, 1, 1): 1,
    (1, 0, 0): 0, (1, 0, 1): 1, (1, 1, 0): 1, (1, 1, 1): 0,
}

N_CELLS = 4   # dark sector: 4-cell ring (vs SM 5-cell ring)
L       = 7 ** N_CELLS   # = 2401 states


def fmdl(l: int, c: int, r: int) -> int:
    """MDL-minimal Z₇ CA function. Matches CUP3DUniqueness.lean exactly."""
    return _FMDL_LOOKUP.get((l, c, r), 0)


def fmdl_step4(state: tuple) -> tuple:
    """One f_MDL step on a 4-cell ring (periodic boundary)."""
    return tuple(fmdl(state[(i - 1) % N_CELLS], state[i], state[(i + 1) % N_CELLS])
                 for i in range(N_CELLS))


# ---------------------------------------------------------------------------
# Encoding / decoding: base-7, 4 digits
# ---------------------------------------------------------------------------
def encode4(s: tuple) -> int:
    return sum(s[i] * 7 ** i for i in range(N_CELLS))


def decode4(n: int) -> tuple:
    return tuple((n // 7 ** i) % 7 for i in range(N_CELLS))


# ---------------------------------------------------------------------------
# Build transition table T4[i] = encode4(fmdl_step4(decode4(i)))
# ---------------------------------------------------------------------------
def build_transition_table() -> list:
    T4 = [0] * L
    for i in range(L):
        T4[i] = encode4(fmdl_step4(decode4(i)))
    return T4


# ---------------------------------------------------------------------------
# Cycle finder — O(L) two-color functional-graph DFS (same as Z₇⁵ version)
# ---------------------------------------------------------------------------
def find_cycles(T4: list):
    """Returns (cycle_lengths, on_cycle, tail_length, predecessor_count)."""
    color        = [0] * L   # 0=unvisited, 1=in-progress, 2=done
    on_cycle     = [False] * L
    cycle_id_arr = [-1] * L
    cycle_lengths = []

    for start in range(L):
        if color[start] == 2:
            continue
        path = []
        path_pos = {}
        state = start
        while color[state] == 0:
            color[state] = 1
            path_pos[state] = len(path)
            path.append(state)
            state = T4[state]

        if color[state] == 1:
            cycle_start_idx = path_pos[state]
            cycle = path[cycle_start_idx:]
            cid = len(cycle_lengths)
            cycle_lengths.append(len(cycle))
            for s in cycle:
                on_cycle[s] = True
                cycle_id_arr[s] = cid
                color[s] = 2
            for s in path[:cycle_start_idx]:
                cycle_id_arr[s] = cid
                color[s] = 2
        else:
            cid = cycle_id_arr[state]
            for s in path:
                cycle_id_arr[s] = cid
                color[s] = 2

    # Compute tail lengths by forward-tracing from each state
    tail_length = [-1] * L
    for s in range(L):
        if on_cycle[s]:
            tail_length[s] = 0

    # BFS backward from cycle states to compute tail lengths
    # (assign tail length = distance to nearest cycle state)
    predecessor_lists = [[] for _ in range(L)]
    for s in range(L):
        nxt = T4[s]
        predecessor_lists[nxt].append(s)

    from collections import deque
    queue = deque()
    for s in range(L):
        if on_cycle[s]:
            queue.append(s)

    while queue:
        current = queue.popleft()
        for pred in predecessor_lists[current]:
            if tail_length[pred] == -1:
                tail_length[pred] = tail_length[current] + 1
                queue.append(pred)

    # Predecessor count (states with 0 predecessors = Garden of Eden)
    predecessor_count = [len(predecessor_lists[s]) for s in range(L)]

    return cycle_lengths, on_cycle, cycle_id_arr, tail_length, predecessor_count


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    VACUUM4 = (0, 0, 0, 0)

    print("=" * 72)
    print("f_MDL Orbit Spectrum on Z₇⁴ — Dark Sector 4-Cell Ring")
    print(f"  State space: 7^4 = {L} states (dark sector ring)")
    print(f"  Comparison: Z₇⁵ = 16,807 states (SM visible sector ring)")
    print("=" * 72)

    # ── Sanity check: vacuum is a fixed point on the 4-cell ring ────────────
    assert fmdl_step4(VACUUM4) == VACUUM4, \
        f"Vacuum not fixed in Z₇⁴: {fmdl_step4(VACUUM4)}"
    print("✓ Sanity check: vacuum (0,0,0,0) is a fixed point in Z₇⁴")
    vac_enc = encode4(VACUUM4)
    print(f"  Vacuum encodes to: {vac_enc}")
    print()

    # ── Build transition table ───────────────────────────────────────────────
    print(f"Building transition table ({L} states)...")
    T4 = build_transition_table()
    print("  Done.")
    print()

    # ── Find all cycles ──────────────────────────────────────────────────────
    print("Finding all cycles in Z₇⁴ functional graph...")
    cycle_lengths, on_cycle, cycle_id_arr, tail_length, pred_count = find_cycles(T4)

    n_cycles    = len(cycle_lengths)
    n_attractor = sum(1 for x in on_cycle if x)
    n_transient = L - n_attractor
    n_goe       = sum(1 for p in pred_count if p == 0)
    max_tail    = max(tail_length)

    print(f"  Total distinct cycles:              {n_cycles}")
    print(f"  Attractor states (on cycles):       {n_attractor}")
    print(f"  Transient states:                   {n_transient}")
    print(f"  GoE states (no predecessors):       {n_goe}  ({100*n_goe/L:.2f}%)")
    print(f"  Maximum tail length:                {max_tail} steps")
    print()

    # ── Orbit spectrum ────────────────────────────────────────────────────────
    length_counter = Counter(cycle_lengths)

    print("=" * 72)
    print("ORBIT SPECTRUM — cycle length distribution")
    print("=" * 72)
    print(f"\n{'Length':>8}  {'# cycles':>10}  {'# attractor states':>20}  {'% total':>10}")
    print("-" * 60)

    for length in sorted(length_counter.keys()):
        count = length_counter[length]
        states_in = count * length
        pct = 100 * states_in / L
        print(f"  {length:6d}    {count:10d}    {states_in:18d}    {pct:9.3f}%")

    print("-" * 60)
    print(f"  Total: {n_cycles} cycle(s), {n_attractor} attractor states ({100*n_attractor/L:.3f}%)")
    print()

    # ── Fixed points ─────────────────────────────────────────────────────────
    print("=" * 72)
    print("FIXED POINTS (cycle length = 1)")
    print("=" * 72)
    fixed_pts = [i for i in range(L) if on_cycle[i] and
                 cycle_lengths[cycle_id_arr[i]] == 1]
    print(f"\n  Number of fixed points: {len(fixed_pts)}")
    for fp_enc in fixed_pts:
        fp = decode4(fp_enc)
        label = " ← VACUUM (ground state)" if fp == VACUUM4 else " ← dark sector fixed point"
        preds = pred_count[fp_enc]
        print(f"    {fp}  [enc={fp_enc}, predecessors={preds}]{label}")
    print()

    # ── Cycles of length > 1 (dark sector quantum states) ────────────────────
    long_cycles = [(cid, cl) for cid, cl in enumerate(cycle_lengths) if cl > 1]
    print("=" * 72)
    print("CYCLES OF LENGTH > 1 (potential dark sector quantum states)")
    print("=" * 72)
    if not long_cycles:
        print("\n  NONE FOUND — Z₇⁴ also has a unique vacuum attractor.")
        print("  Dark sector cycle structure = same as visible sector.")
        print("  Prediction: dark sector has no stable non-vacuum periodic orbits.")
    else:
        print(f"\n  Found {len(long_cycles)} cycle(s) of length > 1:")
        for cid, cl in long_cycles:
            # Find states on this cycle
            cycle_states = [s for s in range(L) if cycle_id_arr[s] == cid and on_cycle[s]]
            print(f"\n  Cycle (length={cl}):")
            for s in cycle_states[:8]:
                print(f"    state {decode4(s)}  [enc={s}, predecessors={pred_count[s]}]")
            if len(cycle_states) > 8:
                print(f"    ... and {len(cycle_states) - 8} more states on this cycle")
    print()

    # ── Tail length distribution ──────────────────────────────────────────────
    tail_counter = Counter(tail_length)
    goe_by_tail  = Counter(
        tail_length[s] for s in range(L) if pred_count[s] == 0
    )

    print("=" * 72)
    print("TAIL LENGTH DISTRIBUTION (transient states)")
    print("=" * 72)
    print(f"\n{'Tail length':>12}  {'Total states':>14}  {'GoE states':>12}  {'GoE %':>8}")
    print("-" * 55)
    for tl in sorted(tail_counter.keys()):
        total = tail_counter[tl]
        goe   = goe_by_tail.get(tl, 0)
        goe_pct = 100 * goe / max(total, 1)
        marker = " ← maximum tail" if tl == max_tail else ""
        print(f"  {tl:10d}    {total:12d}    {goe:10d}    {goe_pct:6.1f}%{marker}")
    print()

    # ── Predecessor count distribution ────────────────────────────────────────
    pred_counter = Counter(pred_count)
    print("=" * 72)
    print("PREDECESSOR COUNT DISTRIBUTION")
    print("=" * 72)
    print(f"\n  GoE states (0 predecessors): {pred_counter.get(0, 0)}  ({100*pred_counter.get(0,0)/L:.2f}%)")
    for k in sorted(pred_counter.keys()):
        if k > 0:
            print(f"  {k:3d} predecessors: {pred_counter[k]:6d} states")
    print(f"\n  Vacuum (enc={vac_enc}) predecessors: {pred_count[vac_enc]}")
    print()

    # ── Z₇ winding structure ─────────────────────────────────────────────────
    winding_counter = Counter(
        sum(decode4(s)) % 7
        for s in range(L) if not on_cycle[s]
    )
    print("=" * 72)
    print("Z₇ WINDING SUM DISTRIBUTION (among tail states)")
    print("=" * 72)
    print(f"\n{'Winding sum':>12}  {'Count':>10}  {'Fraction':>10}")
    print("-" * 36)
    total_tail = sum(winding_counter.values())
    for w in sorted(winding_counter.keys()):
        print(f"  {w:10d}    {winding_counter[w]:8d}    {winding_counter[w]/total_tail:.4f}")
    print()

    # ── Comparison with Z₇⁵ (SM sector) ─────────────────────────────────────
    print("=" * 72)
    print("COMPARISON: Z₇⁴ (dark sector) vs Z₇⁵ (SM visible sector)")
    print("=" * 72)

    sm_n_cycles    = 1
    sm_n_attractor = 1
    sm_max_tail    = 7
    sm_goe         = 16590
    sm_total       = 16807

    print(f"\n{'Quantity':<35} {'Z₇⁵ (SM, N=5)':>20} {'Z₇⁴ (dark, N=4)':>20}")
    print("-" * 78)
    print(f"  {'Total states':<33} {sm_total:>20} {L:>20}")
    print(f"  {'Distinct cycles':<33} {sm_n_cycles:>20} {n_cycles:>20}")
    print(f"  {'Attractor states':<33} {sm_n_attractor:>20} {n_attractor:>20}")
    print(f"  {'Transient states':<33} {sm_total - sm_n_attractor:>20} {n_transient:>20}")
    print(f"  {'GoE states':<33} {sm_goe:>20} {n_goe:>20}")
    print(f"  {'GoE fraction':<33} {'98.71%':>20} {100*n_goe/L:.2f}%:>20")
    print(f"  {'Maximum tail length':<33} {sm_max_tail:>20} {max_tail:>20}")
    print(f"  {'Cycles of length > 1':<33} {'None':>20} {'None' if not long_cycles else str(len(long_cycles)):>20}")
    print()

    # ── Physical interpretation ───────────────────────────────────────────────
    print("=" * 72)
    print("PHYSICAL INTERPRETATION")
    print("=" * 72)

    if n_cycles == 1 and length_counter.get(1, 0) == 1:
        print("""
  UNIQUE VACUUM ATTRACTOR confirmed in Z₇⁴ (dark sector ring).
  The f_MDL Unique Attractor Theorem extends to N=4:
    - f_MDL on any Z₇ᴺ ring (N=4 and N=5 both verified) has EXACTLY ONE CYCLE:
      the vacuum fixed point (0,…,0).
    - Every state in Z₇⁴ converges to the vacuum in at most {0} steps.

  Dark sector implications ('t Hooft Ch.7 framework):
    - The physical Hilbert space from f_MDL on Z₇⁴ is also 1-dimensional (vacuum only).
    - There are NO stable periodic dark sector states in this framework.
    - Dark sector "particles" would be TRANSIENT states — identical in character to
      the SM generation states in Z₇⁵.

  Stability hierarchy conjecture (CatD → requires dark sector mass ordering):
    - If dark sector has 4 generations analogous to SM 3 generations, we expect
      tail lengths 1, 2, 3, 4 for the four dark generations (heaviest to lightest).
    - The maximum tail in Z₇⁴ is {0} steps. This bounds the number of
      distinguishable dark sector "lifetimes" in this framework.
""".format(max_tail))

    elif long_cycles:
        n_dark_states = sum(cl for _, cl in long_cycles if cl > 1)
        print(f"""
  NON-VACUUM CYCLES FOUND in Z₇⁴ — unexpected and physically significant.
  {len(long_cycles)} cycle(s) of length > 1 exist, containing {n_dark_states} states.
  These cycles ARE stable quantum states in 't Hooft's cogwheel framework.
  They represent potential dark sector particles with non-zero Hamiltonian eigenvalues.

  This is the key distinction from Z₇⁵ (visible sector):
    - Z₇⁵: 1 cycle (vacuum only) → no stable excited SM states (SM particles are transient)
    - Z₇⁴: {len(long_cycles)} non-vacuum cycle(s) → stable dark sector eigenstates exist

  Eigenvalue spectrum from 't Hooft (cycle length N → E_k = 2πk/N):
""")
        for cid, cl in long_cycles:
            if cl > 1:
                eigs = [f"2π·{k}/{cl}" for k in range(cl)]
                print(f"    Cycle of length {cl}: E = {', '.join(eigs)}")

    print()

    # ── Summary ───────────────────────────────────────────────────────────────
    print("=" * 72)
    print("SUMMARY")
    print("=" * 72)
    print(f"  State space:          Z₇⁴, {L} states")
    print(f"  Distinct cycles:      {n_cycles}")
    print(f"  Cycles of length > 1: {len(long_cycles)}")
    print(f"  Attractor states:     {n_attractor}  ({100*n_attractor/L:.3f}%)")
    print(f"  Transient states:     {n_transient}  ({100*n_transient/L:.3f}%)")
    print(f"  GoE states:           {n_goe}  ({100*n_goe/L:.2f}%)")
    print(f"  Maximum tail length:  {max_tail} steps")
    print(f"  Vacuum predecessors:  {pred_count[vac_enc]}")

    if n_cycles == 1:
        print()
        print("  CONCLUSION: f_MDL Unique Attractor Theorem holds for N=4.")
        print("  Z₇⁴ has the same cycle structure as Z₇⁵: unique vacuum attractor.")
        print("  Dark sector shares the 1-dimensional Hilbert space structure.")
    else:
        print()
        print(f"  CONCLUSION: Z₇⁴ has {n_cycles} cycles (including {len(long_cycles)} non-vacuum).")
        print("  Dark sector differs structurally from the visible sector.")
        print("  Non-vacuum cycles = potential stable dark sector quantum states.")

    print()


if __name__ == "__main__":
    main()
