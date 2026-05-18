import numpy as np
import networkx as nx
import math

def build_lattice4d(n):
    G = nx.grid_graph(dim=[n, n, n, n], periodic=True)
    G = nx.convert_node_labels_to_integers(G, ordering='sorted')
    for u, v in G.edges():
        G[u][v]['w'] = 1.0
    return G

def build_lattice4d_smallworld(n, p, rng):
    G = build_lattice4d(n)
    E = list(G.edges())
    m = int(p * len(E))
    nodes = list(G.nodes())
    for _ in range(m):
        if len(E) == 0:
            break
        idx = rng.integers(0, len(E))
        u, v = E[idx]
        G.remove_edge(u, v)
        E.pop(idx)
        a = nodes[rng.integers(0, len(nodes))]
        b = nodes[rng.integers(0, len(nodes))]
        if a != b and not G.has_edge(a, b):
            G.add_edge(a, b, w=1.0)
    return G

def build_mutual_knn4d(seed, N, k):
    rng = np.random.default_rng(seed)
    X = rng.random((N, 4))
    
    D = np.sum((X[:, None, :] - X[None, :, :]) ** 2, axis=2)
    
    idx = np.argpartition(D, kth=k+1, axis=1)[:, 1:k+1]
    
    G = nx.Graph()
    G.add_nodes_from(range(N))
    
    nbrs = [set(idx[i]) for i in range(N)]
    
    for i in range(N):
        for j in nbrs[i]:
            if i in nbrs[j]:
                G.add_edge(i, j, w=1.0)
    
    return G

def build_kpkvb(seed, N, avg_k, T):
    rng = np.random.default_rng(seed)
    
    R = 2.0 * np.log(N)
    
    r = R * rng.random(N)
    theta = 2.0 * np.pi * rng.random(N)
    
    G = nx.Graph()
    G.add_nodes_from(range(N))
    
    beta = 1.0 / T
    r_conn = R - (2.0 / beta) * np.log(N / (avg_k + 1e-9))
    r_conn = max(1.0, r_conn)
    
    edges_added = 0
    target_edges = int(N * avg_k / 2.0)
    
    pairs = [(i, j) for i in range(N) for j in range(i + 1, min(i + int(N * 0.1), N))]
    rng.shuffle(pairs)
    
    for i, j in pairs:
        if edges_added >= target_edges:
            break
            
        dr = abs(r[i] - r[j])
        dtheta = abs(theta[i] - theta[j])
        dtheta = min(dtheta, 2.0 * np.pi - dtheta)
        
        arg = np.cosh(dr) - np.cos(dtheta) * np.sinh(r[i]) * np.sinh(r[j])
        if arg < 1.0:
            arg = 1.0
        d_hyp = np.arccosh(arg)
        
        p_conn = 1.0 / (1.0 + np.exp(beta * (d_hyp - r_conn)))
        
        if rng.random() < p_conn:
            G.add_edge(i, j, w=1.0)
            edges_added += 1
    
    return G

def build_hierarchical_graph(seed, N, depth=4):
    rng = np.random.default_rng(seed)
    G = nx.Graph()
    
    nodes_per_level = max(2, int(N ** (1.0 / depth)))
    node_id = 0
    level_nodes = []
    
    for level in range(depth):
        current_level = []
        n_nodes = min(nodes_per_level ** (level + 1), N - node_id)
        
        for _ in range(n_nodes):
            if node_id >= N:
                break
            current_level.append(node_id)
            G.add_node(node_id)
            node_id += 1
        
        if len(current_level) > 1:
            for i in range(len(current_level)):
                for j in range(i + 1, min(i + 6, len(current_level))):
                    if rng.random() < 0.8:
                        G.add_edge(current_level[i], current_level[j])
        
        if level > 0 and len(level_nodes[level - 1]) > 0:
            for node in current_level:
                n_parents = min(3, len(level_nodes[level - 1]))
                parents = rng.choice(level_nodes[level - 1], 
                                   size=n_parents, 
                                   replace=False)
                for parent in parents:
                    G.add_edge(node, parent)
        
        level_nodes.append(current_level)
    
    n_cross_links = max(1, int(N * 0.15))
    all_nodes = list(G.nodes())
    for _ in range(n_cross_links):
        if len(all_nodes) >= 2:
            i, j = rng.choice(all_nodes, size=2, replace=False)
            G.add_edge(i, j)
    
    return G

def build_fractal_graph(seed, N, branching=3):
    rng = np.random.default_rng(seed)
    G = nx.Graph()
    
    node_id = 0
    G.add_node(node_id)
    frontier = [node_id]
    node_id += 1
    
    while node_id < N and len(frontier) > 0:
        new_frontier = []
        for parent in frontier:
            n_children = min(branching + rng.integers(-1, 2), N - node_id)
            for _ in range(n_children):
                if node_id >= N:
                    break
                G.add_node(node_id)
                G.add_edge(parent, node_id)
                new_frontier.append(node_id)
                node_id += 1
        frontier = new_frontier
    
    all_nodes = list(G.nodes())
    n_shortcuts = max(1, int(N * 0.20))
    for _ in range(n_shortcuts):
        if len(all_nodes) >= 2:
            i, j = rng.choice(all_nodes, size=2, replace=False)
            if not G.has_edge(i, j):
                G.add_edge(i, j)
    
    return G

def build_srrg_graph(seed, N, params=None):
    rng = np.random.default_rng(seed)
    
    if N <= 1000:
        return build_fractal_graph(seed, N, branching=3)
    else:
        depth = max(3, int(math.log(N, 10)))
        return build_hierarchical_graph(seed, N, depth=depth)

def fisher_metric_proxy(G):
    deg = np.array([G.degree(n) for n in G.nodes()], dtype=float)
    v = np.maximum(deg, 1.0)
    return v

def scalar_curvature_proxy(I):
    inv = 1.0 / I
    R = inv - np.mean(inv)
    return R

def ollivier_ricci_curvature_simple(G, sample_edges=200):
    edges = list(G.edges())
    if len(edges) == 0:
        return np.array([0.0])
    
    n_sample = min(sample_edges, len(edges))
    rng = np.random.default_rng(42)
    sampled = rng.choice(len(edges), size=n_sample, replace=False) if len(edges) > n_sample else range(len(edges))
    
    curvatures = []
    for idx in sampled:
        u, v = edges[idx]
        
        nbrs_u = set(G.neighbors(u)) | {u}
        nbrs_v = set(G.neighbors(v)) | {v}
        
        overlap = len(nbrs_u & nbrs_v)
        union = len(nbrs_u | nbrs_v)
        
        if union > 0:
            kappa = 1.0 - float(overlap) / float(union)
        else:
            kappa = 0.0
        
        curvatures.append(kappa)
    
    return np.array(curvatures) if len(curvatures) > 0 else np.array([0.0])

def omega_complexity(R, I):
    return float(np.sum(np.abs(R) * np.sqrt(I)))

def omega_intensive(R, I):
    return float(np.mean(np.abs(R)))

def forman_ricci_curvature_simple(G, sample_edges=200):
    edges = list(G.edges())
    if len(edges) == 0:
        return np.array([0.0])
    
    n_sample = min(sample_edges, len(edges))
    rng = np.random.default_rng(42)
    sampled = rng.choice(len(edges), size=n_sample, replace=False) if len(edges) > n_sample else range(len(edges))
    
    curvatures = []
    for idx in sampled:
        u, v = edges[idx]
        
        deg_u = G.degree(u)
        deg_v = G.degree(v)
        
        nbrs_u = set(G.neighbors(u))
        nbrs_v = set(G.neighbors(v))
        
        triangles_uv = len(nbrs_u & nbrs_v)
        
        kappa = 4.0 - deg_u - deg_v + 3.0 * triangles_uv
        
        curvatures.append(kappa)
    
    return np.array(curvatures) if len(curvatures) > 0 else np.array([0.0])

def omega_intensive_ricci(G, sample_edges=200, signed=False):
    kappas = ollivier_ricci_curvature_simple(G, sample_edges)
    if signed:
        return float(np.mean(kappas))
    else:
        return float(np.mean(np.abs(kappas)))

def omega_intensive_forman(G, sample_edges=200, signed=False):
    kappas = forman_ricci_curvature_simple(G, sample_edges)
    if signed:
        return float(np.mean(kappas))
    else:
        return float(np.mean(np.abs(kappas)))

def omega_rel(current_omega_int, ref_omega_int):
    if ref_omega_int < 1e-10:
        return 1.0
    return current_omega_int / ref_omega_int

