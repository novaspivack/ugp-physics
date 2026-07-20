"""Exact transfer matrix of the 1D spin-7 ring.

The Hamiltonian H = sum_i p(s_{i-1}, s_i, s_{i+1}) with the three-site window
p(L,C,R) = (C+R-CR-LCR) mod 7 requires a transfer matrix on PAIR states:

    M[(a,b),(b',c)] = delta(b,b') * exp(-beta * p(a,b,c)),   a,b,c in Z_7,

a 49x49 matrix.  The ring partition function is exactly Z_N = Tr(M^N); this is
verified below against exhaustive enumeration over all 7^N configurations for
N = 5, 6, 7 at several beta.

Outputs:
  - spectral table: beta, lambda_1, |lambda_2|, gap, correlation length xi,
    pressure / entropy rate S(beta) = log lambda_1
  - rank of M (= 43 = Phi_6(7): the b=0 block p(a,0,c) = c is independent of
    a, contributing rank 1; the six b != 0 blocks have full rank 7)
  - zero-temperature support digraph: each of the 43 active pair states has
    out-degree exactly 1 (deterministic successor map); its only cycles are
    the three uniform self-loops (0,0), (1,1), (5,5) -- the combinatorial core
    of the ground-space rigidity theorem (Lean: SpinSevenGroundSpace.lean)
  - energy distribution over all 343 windows and the 43 = Phi_6(7) zero count
"""

import json
import signal
import sys
from itertools import product

import numpy as np

TIMEOUT_SECONDS = 300

def _timeout(s, f):
    print("TIMEOUT reached.")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

Q = 7

def p_gf7(L, C, R):
    return (C + R - C * R - L * C * R) % Q


def pair_transfer_matrix(beta):
    """Exact 49x49 pair-state transfer matrix M[(a,b),(b,c)] = e^{-beta p(a,b,c)}."""
    M = np.zeros((Q * Q, Q * Q))
    for a in range(Q):
        for b in range(Q):
            for c in range(Q):
                M[a * Q + b, b * Q + c] = np.exp(-beta * p_gf7(a, b, c))
    return M


def exact_Z_enumeration(N, beta):
    """Z_N by exhaustive enumeration over all 7^N ring configurations."""
    Z = 0.0
    for s in product(range(Q), repeat=N):
        E = sum(p_gf7(s[(i - 1) % N], s[i], s[(i + 1) % N]) for i in range(N))
        Z += np.exp(-beta * E)
    return Z


# ---------------------------------------------------------------- exactness
print("=== Exactness check: Tr(M^N) vs exhaustive enumeration ===")
checks = []
for N, beta in [(5, 0.5), (6, 1.0), (7, 2.0)]:
    M = pair_transfer_matrix(beta)
    Z_tm = float(np.trace(np.linalg.matrix_power(M, N)))
    Z_enum = float(exact_Z_enumeration(N, beta))
    rel = abs(Z_tm - Z_enum) / Z_enum
    print(f"N={N} beta={beta}: Tr(M^N)={Z_tm:.10f}  enumeration={Z_enum:.10f}  rel.err={rel:.2e}")
    assert rel < 1e-10, "transfer matrix identity violated"
    checks.append({"N": N, "beta": beta, "Z_transfer": Z_tm, "Z_enum": Z_enum})

# ---------------------------------------------------------------- spectrum
print("\n=== Spectral table (exact pair transfer matrix) ===")
print(f"{'beta':>6} {'lambda_1':>10} {'|lambda_2|':>10} {'gap':>9} {'xi':>9} {'S=log l1':>9} {'f/site':>9}")
table = []
for beta in [0.30, 0.35, 0.50, 1.00, 2.00, 3.00]:
    M = pair_transfer_matrix(beta)
    ev = np.linalg.eigvals(M)
    ev = sorted(ev, key=abs, reverse=True)
    lam1 = abs(ev[0])
    lam2 = abs(ev[1])
    gap = np.log(lam1 / lam2)
    xi = 1.0 / gap
    S = np.log(lam1)
    f = -S / beta
    print(f"{beta:>6.2f} {lam1:>10.5f} {lam2:>10.5f} {gap:>9.5f} {xi:>9.3f} {S:>9.5f} {f:>9.5f}")
    table.append({"beta": beta, "lambda_1": float(lam1), "lambda_2_abs": float(lam2),
                  "gap": float(gap), "xi": float(xi), "S_pressure": float(S),
                  "free_energy_per_site": float(f)})

# limits: beta -> 0 gives lambda_1 -> 7 (S -> log 7); beta -> infty gives
# lambda_1 -> 1 with the three uniform ground rings (S -> 0, rigidity)
M0 = pair_transfer_matrix(1e-4)
lam1_0 = max(abs(np.linalg.eigvals(M0)))
print(f"\nbeta->0: lambda_1 = {lam1_0:.4f} -> 7 exactly; S -> log 7 = {np.log(7):.4f} nats")

# ---------------------------------------------------------------- rank
M1 = pair_transfer_matrix(1.0)
rank = int(np.linalg.matrix_rank(M1))
print(f"rank(M) at beta=1: {rank}  (= Phi_6(7) = 43)")
block_ranks = {}
for b in range(Q):
    B = np.array([[np.exp(-p_gf7(a, b, c)) for c in range(Q)] for a in range(Q)])
    block_ranks[b] = int(np.linalg.matrix_rank(B))
print(f"per-block ranks (b=0..6): {list(block_ranks.values())}  "
      f"(b=0 block has p(a,0,c)=c independent of a)")

# ------------------------------------------------- zero-temperature digraph
print("\n=== Zero-temperature support digraph (ground-space rigidity core) ===")
succ = {}
for a in range(Q):
    for b in range(Q):
        cs = [c for c in range(Q) if p_gf7(a, b, c) == 0]
        if cs:
            succ[(a, b)] = cs
active = {k: v for k, v in succ.items() if len(v) >= 1}
outdeg = {k: len(v) for k, v in active.items()}
print(f"active pair states: {len(active)} (= 43 = Phi_6(7)); "
      f"out-degrees: {sorted(set(outdeg.values()))} (deterministic successor map)")
assert len(active) == 43 and set(outdeg.values()) == {1}

# cycles of the deterministic successor map
def find_cycles():
    cycles = set()
    for start in active:
        seen = {}
        cur, step = start, 0
        while cur in active and cur not in seen:
            seen[cur] = step
            cur = (cur[1], active[cur][0])
            step += 1
        if cur in seen:  # found a cycle
            cyc = []
            node = cur
            while True:
                cyc.append(node)
                node = (node[1], active[node][0])
                if node == cur:
                    break
            cycles.add(tuple(sorted(cyc)))
    return cycles

cycles = find_cycles()
print(f"cycles of the successor map: {sorted(cycles)}")
assert cycles == {(((0, 0)),), (((1, 1)),), (((5, 5)),)} or \
       cycles == {((0, 0),), ((1, 1),), ((5, 5),)}, cycles
print("=> only cycles are the three uniform self-loops (0,0), (1,1), (5,5):")
print("   every zero-energy ring of length n >= 3 is uniform 0^n, 1^n or 5^n")
print("   (machine-certified: gte_ring_ground_states_uniform_general, Lean 4)")

# ------------------------------------------------------ energy distribution
E_counts = {}
for L in range(Q):
    for C in range(Q):
        for R in range(Q):
            E = p_gf7(L, C, R)
            E_counts[E] = E_counts.get(E, 0) + 1
print("\nEnergy distribution over all 343 windows:")
for E in sorted(E_counts):
    print(f"  E={E}: {E_counts[E]} windows")
print(f"zero-energy windows: {E_counts[0]} (= Phi_6(7) = 43)")

signal.alarm(0)

results = {
    "exactness_checks": checks,
    "spectral_table": table,
    "lambda1_beta_to_0": float(lam1_0),
    "rank_M": rank,
    "block_ranks": block_ranks,
    "active_pairs": len(active),
    "successor_cycles": [list(c[0]) for c in sorted(cycles)],
    "energy_distribution": {str(k): v for k, v in sorted(E_counts.items())},
}
with open("spin7_transfer_matrix_results.json", "w") as f:
    json.dump(results, f, indent=2)
print("\nResults saved to spin7_transfer_matrix_results.json")
