"""
Spectral Dimension of Rule 110 Causal Graph

Computes the spectral dimension d_s of the Rule 110 causal graph via
random-walk diffusion analysis (heat-kernel method).

Method:
1. Run Rule 110 on a 1D tape to generate a spacetime configuration.
2. Build the causal graph (spatial adjacency + timelike + light-cone edges).
3. Run random walks on the graph; measure return probability K(t).
4. Estimate d_s(t) = -2 d(log K) / d(log t) and average over t = 30--70.

Result: d_s ≈ 2.0--2.5 at large scales for the 1D Rule 110 causal graph.
This is consistent with the topological dimension of a 1D×T grid (2D).
The D = 4 argument in the paper (§2) is arithmetic from the f_MDL orbit
structure, not a spectral-geometric property of the causal graph.

Parameters used in the paper:
  L = 200 (tape length), T = 200 (timesteps)
  300 random walks × 80 start nodes (bulk only)
  Initial condition: period-14 ether (primary), random (confirmation)

References:
  Ambjorn, Jurkiewicz, Loll (2005), Phys. Rev. Lett. 95, 171301
  P36: Emergent Gravity from Rule 110 (this paper)
"""

import numpy as np
import random
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from collections import defaultdict

# ─────────────────────────────────────────────────────────────
# Rule 110 Evolution
# ─────────────────────────────────────────────────────────────

RULE110 = {}
for n in range(8):
    l, c, r = (n >> 2) & 1, (n >> 1) & 1, n & 1
    RULE110[(l, c, r)] = (110 >> n) & 1


def evolve_rule110(state, T):
    """Evolve Rule 110 for T steps. Returns spacetime array."""
    L = len(state)
    spacetime = np.zeros((T + 1, L), dtype=np.int8)
    spacetime[0] = state
    for t in range(T):
        for x in range(L):
            l, c, r = spacetime[t][(x-1) % L], spacetime[t][x], spacetime[t][(x+1) % L]
            spacetime[t+1][x] = RULE110[(l, c, r)]
    return spacetime


# ─────────────────────────────────────────────────────────────
# Causal Graph Construction
# ─────────────────────────────────────────────────────────────

def build_causal_graph(spacetime):
    """
    Build the undirected causal graph from a Rule 110 spacetime.

    Nodes: (t, x) spacetime events.
    Edges:
      - Spacelike:  (t, x) -- (t, x±1)   [spatial adjacency at each slice]
      - Timelike:   (t, x) -- (t+1, x)   [temporal propagation]
      - Light-cone: (t, x) -- (t+1, x±1) [causal cone edges]
    """
    T, L = spacetime.shape
    T -= 1
    adj = defaultdict(set)
    for t in range(T):
        for x in range(L):
            node = (t, x)
            adj[node].add((t+1, x))
            adj[(t+1, x)].add(node)
            adj[node].add((t+1, (x+1) % L))
            adj[(t+1, (x+1) % L)].add(node)
            adj[node].add((t+1, (x-1) % L))
            adj[(t+1, (x-1) % L)].add(node)
        for x in range(L):
            adj[(t, x)].add((t, (x+1) % L))
            adj[(t, (x+1) % L)].add((t, x))
    return adj


def build_directed_causal_graph(spacetime):
    """
    Directed causal graph (forward-time edges only), then symmetrised for
    random-walk use.  Uses only causal edges (no extra spacelike).
    """
    T, L = spacetime.shape
    T -= 1
    adj_out = defaultdict(set)
    for t in range(T):
        for x in range(L):
            node = (t, x)
            for dx in (0, 1, -1):
                succ = (t+1, (x+dx) % L)
                adj_out[node].add(succ)
    adj_sym = defaultdict(set)
    for node, succs in adj_out.items():
        for s in succs:
            adj_sym[node].add(s)
            adj_sym[s].add(node)
    return adj_sym


# ─────────────────────────────────────────────────────────────
# Spectral Dimension via Random Walk
# ─────────────────────────────────────────────────────────────

def heat_kernel_trace(adj, nodes_list, max_steps,
                      n_walks_per_node=200, n_start_nodes=100):
    """
    Estimate the normalised heat-kernel trace K(t) = (1/N) Tr(exp(-tL))
    via random walks averaged over many starting nodes.

    K(t) ≈ (1/n_start) Σ_v P_v(t),  P_v(t) = return probability from v.

    Start nodes are drawn from the bulk (central 60% of timesteps) to
    avoid boundary artefacts.

    Returns K(t) for t = 0, 1, ..., max_steps.
    """
    n_start_nodes = min(n_start_nodes, len(nodes_list))
    t_max = max(x[0] for x in nodes_list)
    bulk_nodes = [n for n in nodes_list
                  if t_max * 0.2 < n[0] < t_max * 0.8]
    if not bulk_nodes:
        bulk_nodes = nodes_list
    start_nodes = random.sample(bulk_nodes, min(n_start_nodes, len(bulk_nodes)))

    K = np.zeros(max_steps + 1)
    K[0] = 1.0

    for v in start_nodes:
        returns_v = np.zeros(max_steps + 1)
        for _ in range(n_walks_per_node):
            pos = v
            for step in range(1, max_steps + 1):
                neighbors = list(adj[pos])
                if not neighbors:
                    break
                pos = random.choice(neighbors)
                if pos == v:
                    returns_v[step] += 1
        K += returns_v / n_walks_per_node

    K /= len(start_nodes)
    return K


def compute_spectral_dimension(K):
    """
    Compute d_s(t) = -2 d(log K(t)) / d(log t) via central finite differences.
    """
    P = K.copy()
    P[P < 1e-8] = np.nan
    log_t = np.log(np.arange(1, len(P)))
    log_P = np.log(P[1:])
    d_s = np.full(len(log_t), np.nan)
    for i in range(1, len(log_t) - 1):
        if np.isnan(log_P[i-1]) or np.isnan(log_P[i+1]):
            continue
        d_log_P = log_P[i+1] - log_P[i-1]
        d_log_t = log_t[i+1] - log_t[i-1]
        if d_log_t != 0:
            d_s[i] = -2.0 * d_log_P / d_log_t
    return d_s


def smooth_ds(d_s, window=5):
    """Simple moving-average smoother for d_s(t) estimates."""
    out = np.full_like(d_s, np.nan)
    for i in range(len(d_s)):
        lo = max(0, i - window // 2)
        hi = min(len(d_s), i + window // 2 + 1)
        vals = d_s[lo:hi]
        vals = vals[~np.isnan(vals)]
        if len(vals) > 0:
            out[i] = float(np.mean(vals))
    return out


def report_ds(label, d_s, t_values=(5, 10, 20, 40, 60, 80)):
    """Print d_s at specified t values and return the large-scale average."""
    d_s_sm = smooth_ds(d_s)
    print(f"\n  [{label}]")
    for t in t_values:
        if t < len(d_s_sm) and not np.isnan(d_s_sm[t]):
            print(f"    d_s(t={t:2d}) = {d_s_sm[t]:.3f}")
    valid = d_s_sm[30:min(70, len(d_s_sm))]
    valid = valid[~np.isnan(valid)]
    if len(valid) >= 3:
        avg = float(np.mean(valid))
        print(f"    d_s (large-scale avg, t=30--70, smoothed): {avg:.3f}")
        return avg
    valid_raw = d_s[30:min(70, len(d_s))]
    valid_raw = valid_raw[np.isfinite(valid_raw) & ~np.isnan(valid_raw)]
    valid_raw = valid_raw[np.abs(valid_raw) < 20]
    if len(valid_raw) >= 2:
        avg = float(np.mean(valid_raw))
        print(f"    d_s (large-scale avg, t=30--70, trimmed): {avg:.3f}")
        return avg
    return np.nan


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

if __name__ == '__main__':
    np.random.seed(42)
    random.seed(42)

    print("=" * 60)
    print("Spectral Dimension of Rule 110 Causal Graph")
    print("P36 — Emergent Gravity from Rule 110")
    print("=" * 60)

    L = 200            # tape length
    T = 200            # timesteps  →  (T+1) × L = 40,200 nodes
    n_walks_per_node = 300
    n_start_nodes = 80
    max_rw_steps = 80

    # IC 1: period-14 ether (primary)
    ether_pattern = [1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0]
    state_ether = np.array([ether_pattern[x % 14] for x in range(L)], dtype=np.int8)

    # IC 2: random (confirmation)
    state_rand = np.random.randint(0, 2, L, dtype=np.int8)

    results = {}

    for ic_label, state in [("ether-IC", state_ether), ("random-IC", state_rand)]:
        print(f"\n{'─' * 55}")
        print(f"IC: {ic_label}  (L={L}, T={T})")
        print(f"{'─' * 55}")

        print("  Evolving Rule 110...")
        spacetime = evolve_rule110(state, T)

        print("  Building undirected causal graph...")
        adj_undir = build_causal_graph(spacetime)
        print(f"    Nodes: {len(adj_undir)}")

        print("  Building directed causal graph (symmetric closure of causal edges)...")
        adj_dir = build_directed_causal_graph(spacetime)

        nodes_list = list(adj_undir.keys())

        for graph_label, adj in [("undirected", adj_undir), ("directed-sym", adj_dir)]:
            print(f"\n  Heat-kernel trace ({graph_label}): "
                  f"{n_start_nodes} start nodes × {n_walks_per_node} walks...")
            K = heat_kernel_trace(adj, nodes_list, max_rw_steps,
                                  n_walks_per_node=n_walks_per_node,
                                  n_start_nodes=n_start_nodes)
            d_s = compute_spectral_dimension(K)
            avg = report_ds(f"{ic_label} / {graph_label}", d_s)
            results[f"{ic_label}/{graph_label}"] = avg

    print("\n" + "=" * 60)
    print("SPECTRAL DIMENSION SUMMARY")
    print("=" * 60)
    print(f"  {'Variant':<38}  d_s (t=30--70)")
    print(f"  {'-' * 38}  {'-' * 13}")
    for key, val in results.items():
        if not np.isnan(val):
            print(f"  {key:<38}  {val:.3f}")
        else:
            print(f"  {key:<38}  N/A")

    print()
    print(f"  Reference: 1D lattice  → d_s ≈ 1.0")
    print(f"  Reference: 2D lattice  → d_s ≈ 2.0")
    print(f"  Reference: CDT (short) → d_s ≈ 1.8")
    print(f"  Reference: CDT (large) → d_s ≈ 4.0")

    ds_primary = results.get("ether-IC/undirected", np.nan)

    print()
    if not np.isnan(ds_primary):
        if ds_primary > 3.5:
            verdict = "CONSISTENT WITH 3+1D spacetime emergence (d_s ≈ 4)"
        elif ds_primary > 2.5:
            verdict = "INTERMEDIATE (d_s ≈ 3): suggestive but not d_s ≈ 4"
        elif ds_primary > 1.5:
            verdict = "INTERMEDIATE (d_s ≈ 2): between 1D and 3+1D"
        else:
            verdict = "LOW-DIMENSIONAL (d_s ≈ 1-2): 1D CA insufficient for 3+1D"
        print(f"  PRIMARY RESULT (ether-IC, undirected): {verdict}")
    print("=" * 60)
