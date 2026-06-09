"""
Graph topology generators for ensemble testing

Implements:
- Erdős-Rényi (random)
- Watts-Strogatz (small-world)
- Barabási-Albert (scale-free)

Cross-reference:
    ADVANCED_ENSEMBLE_TESTS/docs/1_1_ADVANCED_ENSEMBLE_KICKOFF.md
    Mathematical_Foundations_of_Reflexive_Reality.tex (Section ensemble-CP)
"""

import numpy as np
from scipy.sparse import csr_matrix


def build_erdos_renyi(N, p, rng):
    """
    Build Erdős-Rényi random graph.
    
    Args:
        N: Number of nodes
        p: Edge probability (0 < p < 1)
        rng: NumPy random generator
        
    Returns:
        Sparse adjacency matrix (CSR format)
    """
    mask = rng.random((N, N)) < p
    A = np.triu(mask, k=1).astype(float)
    A = A + A.T  # Symmetrize
    return csr_matrix(A)


def build_watts_strogatz(N, k, p_rewire, rng):
    """
    Build Watts-Strogatz small-world graph.
    
    Args:
        N: Number of nodes
        k: Mean degree (must be even)
        p_rewire: Rewiring probability (0 < p < 1)
        rng: NumPy random generator
        
    Returns:
        Sparse adjacency matrix (CSR format)
    """
    if k % 2 != 0:
        k = k + 1  # Make even
    
    # Start with ring lattice
    A = np.zeros((N, N), dtype=float)
    for i in range(N):
        for j in range(1, k // 2 + 1):
            A[i, (i + j) % N] = 1
            A[i, (i - j) % N] = 1
    
    # Rewire edges with probability p
    for i in range(N):
        neighbors = [j for j in range(N) if A[i, j] > 0 and j > i]
        for j in neighbors:
            if rng.random() < p_rewire:
                # Remove edge (i, j)
                A[i, j] = 0
                A[j, i] = 0
                
                # Add edge to random node (avoid self-loops and duplicates)
                candidates = [k for k in range(N) if k != i and A[i, k] == 0]
                if len(candidates) > 0:
                    new_target = rng.choice(candidates)
                    A[i, new_target] = 1
                    A[new_target, i] = 1
    
    return csr_matrix(A)


def build_barabasi_albert(N, m, rng):
    """
    Build Barabási-Albert scale-free graph via preferential attachment.
    
    Args:
        N: Total number of nodes
        m: Number of edges to attach from each new node
        rng: NumPy random generator
        
    Returns:
        Sparse adjacency matrix (CSR format)
    """
    A = np.zeros((N, N), dtype=float)
    
    # Start with small complete graph
    m0 = max(m, 2)
    for i in range(m0):
        for j in range(i + 1, m0):
            A[i, j] = 1
            A[j, i] = 1
    
    # Add remaining nodes with preferential attachment
    for new_node in range(m0, N):
        degrees = A.sum(axis=1)
        total_degree = degrees.sum()
        
        if total_degree == 0:
            # Fallback: random attachment
            targets = rng.choice(new_node, size=min(m, new_node), replace=False)
        else:
            # Preferential attachment based on degree
            probs = degrees[:new_node] / total_degree
            targets = rng.choice(new_node, size=min(m, new_node), replace=False, p=probs)
        
        for target in targets:
            A[new_node, target] = 1
            A[target, new_node] = 1
    
    return csr_matrix(A)


def init_coupling_matrix(A, J, rng):
    """
    Initialize weighted coupling matrix from adjacency matrix.
    
    Weights are drawn from Gaussian with variance scaled by inverse degree
    to maintain consistent total coupling strength.
    
    Args:
        A: Adjacency matrix (sparse or dense)
        J: Base coupling strength
        rng: NumPy random generator
        
    Returns:
        Weighted coupling matrix W (CSR format)
    """
    N = A.shape[0]
    
    # Compute degrees (with floor at 1 to avoid division by zero)
    if hasattr(A, 'toarray'):
        degrees = np.array(A.sum(axis=1)).flatten()
    else:
        degrees = A.sum(axis=1)
    degrees = np.maximum(degrees, 1.0)
    
    # Copy structure
    W = A.copy()
    if hasattr(W, 'tocsr'):
        W = W.tocsr()
    else:
        W = csr_matrix(W)
    
    # Assign weights (symmetric)
    rows, cols = W.nonzero()
    for i, j in zip(rows, cols):
        if i < j:  # Upper triangle only
            # Weight variance ~ 1/sqrt(degree)
            weight = rng.normal(0.0, J / np.sqrt(degrees[i]))
            W[i, j] = weight
            W[j, i] = weight
    
    return W.tocsr()


def match_edge_density(N, target_density, graph_type='erdos', **kwargs):
    """
    Helper to compute parameters that match a target edge density.
    
    Args:
        N: Number of nodes
        target_density: Target average degree / N
        graph_type: 'erdos', 'watts_strogatz', or 'barabasi_albert'
        **kwargs: Additional graph-specific parameters
        
    Returns:
        dict with appropriate parameters
    """
    target_avg_degree = target_density * N
    
    if graph_type == 'erdos':
        # E[edges] = p * N(N-1)/2
        # E[degree] = p * (N-1)
        p = target_avg_degree / (N - 1)
        return {'N': N, 'p': min(p, 1.0)}
    
    elif graph_type == 'watts_strogatz':
        # Ring lattice with k neighbors
        k = int(2 * round(target_avg_degree / 2))  # Make even
        p_rewire = kwargs.get('p_rewire', 0.3)
        return {'N': N, 'k': k, 'p_rewire': p_rewire}
    
    elif graph_type == 'barabasi_albert':
        # Each node adds m edges
        m = max(int(round(target_avg_degree / 2)), 1)
        return {'N': N, 'm': m}
    
    else:
        raise ValueError(f"Unknown graph type: {graph_type}")


def compute_graph_properties(A):
    """
    Compute basic graph properties.
    
    Args:
        A: Adjacency matrix
        
    Returns:
        dict with: avg_degree, clustering_coeff, num_edges
    """
    if hasattr(A, 'toarray'):
        A_dense = A.toarray()
    else:
        A_dense = A
    
    N = A_dense.shape[0]
    
    # Average degree
    degrees = A_dense.sum(axis=1)
    avg_degree = float(np.mean(degrees))
    
    # Number of edges
    num_edges = int(np.sum(A_dense) / 2)
    
    # Clustering coefficient (global)
    total_triplets = 0
    closed_triplets = 0
    
    for i in range(N):
        neighbors = np.where(A_dense[i] > 0)[0]
        k = len(neighbors)
        if k < 2:
            continue
        
        total_triplets += k * (k - 1) // 2
        
        for idx1 in range(len(neighbors)):
            for idx2 in range(idx1 + 1, len(neighbors)):
                if A_dense[neighbors[idx1], neighbors[idx2]] > 0:
                    closed_triplets += 1
    
    clustering = closed_triplets / total_triplets if total_triplets > 0 else 0.0
    
    return {
        'avg_degree': avg_degree,
        'clustering_coeff': float(clustering),
        'num_edges': num_edges
    }

