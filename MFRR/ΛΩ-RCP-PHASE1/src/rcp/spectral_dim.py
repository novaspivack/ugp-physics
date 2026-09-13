import numpy as np
import networkx as nx

def random_walk_return_probability(G, t, rng, n_samples=10000):
    N = G.number_of_nodes()
    if N == 0:
        return 0.0
    
    nodes = list(G.nodes())
    if len(nodes) == 0:
        return 0.0
    
    returns = 0
    for _ in range(n_samples):
        start_node = nodes[rng.integers(0, len(nodes))]
        current = start_node
        
        for _ in range(max(1, int(t))):
            nbrs = list(G.neighbors(current))
            if len(nbrs) == 0:
                break
            current = nbrs[rng.integers(0, len(nbrs))]
        
        if current == start_node:
            returns += 1
    
    return float(returns) / float(n_samples)

def spectral_dimension(G, t_grid, seed):
    rng = np.random.default_rng(seed)
    P0 = []
    
    for t in t_grid:
        p = random_walk_return_probability(G, max(1, int(round(t))), rng, n_samples=5000)
        P0.append(max(p, 1e-12))
    
    x = np.log(np.maximum(t_grid, 1e-9))
    y = np.log(P0)
    
    valid_idx = np.isfinite(y) & np.isfinite(x)
    if np.sum(valid_idx) < 2:
        return 4.0
    
    slope = np.polyfit(x[valid_idx], y[valid_idx], 1)[0]
    ds = -2.0 * slope
    
    ds = np.clip(ds, 1.0, 10.0)
    return float(ds)

