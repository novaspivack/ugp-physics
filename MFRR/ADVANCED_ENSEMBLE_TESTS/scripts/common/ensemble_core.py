"""
Core ensemble dynamics for adjudication cascades

Implements:
- Avalanche/cascade update dynamics
- Glauber dynamics for continuous evolution
- Spectral analysis utilities

Cross-reference:
    Mathematical_Foundations_of_Reflexive_Reality.tex (Section ensemble-CP)
    ADVANCED_ENSEMBLE_TESTS/docs/1_1_ADVANCED_ENSEMBLE_KICKOFF.md
"""

import numpy as np
from scipy.sparse.linalg import eigsh
from collections import deque


def local_cost(bi, psi_i, bias=0.0, kappa=1.0):
    """
    Local dissonance cost for branch bi.
    
    Quadratic well: D_i(bi) = κ (bi - bias)²
    
    Args:
        bi: Branch value (0 or 1)
        psi_i: Coherence field value (not used in simple cost)
        bias: Preferred branch (0 to 1)
        kappa: Well depth
        
    Returns:
        Cost (dimensionless)
    """
    return kappa * (bi - bias)**2


def inter_cost(bi, bj):
    """
    Interaction dissonance cost (Ising-like).
    
    Υ(bi, bj) = -bi × bj
    
    Favors alignment when coupling is positive.
    
    Args:
        bi, bj: Branch values (0 or 1)
        
    Returns:
        Interaction cost
    """
    return -float(bi) * float(bj)


def argmin_branch(i, b, psi, W_row_indices, W_row_data, bias, kappa):
    """
    Find optimal branch for CP i given current ensemble state.
    
    Minimizes: D_i(bi) + Σ_j J_ij Υ(bi, bj)
    
    Args:
        i: CP index
        b: Current branch array
        psi: Coherence field array
        W_row_indices: Neighbor indices for CP i
        W_row_data: Coupling strengths J_ij
        bias: Bias array
        kappa: Kappa array
        
    Returns:
        Optimal branch (0 or 1)
    """
    cost_0 = local_cost(0, psi[i], bias[i], kappa[i])
    cost_1 = local_cost(1, psi[i], bias[i], kappa[i])
    
    # Add neighbor contributions
    for idx, j in enumerate(W_row_indices):
        J_ij = W_row_data[idx]
        if J_ij != 0.0:
            cost_0 += J_ij * inter_cost(0, b[j])
            cost_1 += J_ij * inter_cost(1, b[j])
    
    return 0 if cost_0 <= cost_1 else 1


def avalanche_update(W, b, psi, bias, kappa, max_iter=1000, seed_fraction=0.02, rng=None):
    """
    Event-driven avalanche/cascade update.
    
    Seeds a random fraction of CPs and propagates changes until stable.
    Records cascade size (number of CPs that flipped).
    
    Args:
        W: Coupling matrix (sparse)
        b: Branch state array (modified in-place)
        psi: Coherence field array
        bias: Bias array
        kappa: Kappa array
        max_iter: Maximum propagation steps
        seed_fraction: Fraction of CPs to seed
        rng: Random number generator
        
    Returns:
        Cascade size (int), list of participating CP indices
    """
    if rng is None:
        rng = np.random.default_rng()
    
    N = len(b)
    
    # Precompute neighbor lists
    nbrs_indices = [W[i].indices for i in range(N)]
    nbrs_data = [W[i].data for i in range(N)]
    
    # Seed queue: random subset
    seed_mask = rng.random(N) < seed_fraction
    queue = deque(np.where(seed_mask)[0].tolist())
    visited = set()
    flipped = []
    iterations = 0
    
    while queue and iterations < max_iter:
        iterations += 1
        i = queue.popleft()
        
        if i in visited:
            continue
        visited.add(i)
        
        # Compute optimal branch
        new_bi = argmin_branch(i, b, psi, nbrs_indices[i], nbrs_data[i], bias, kappa)
        
        # If state changes, record and propagate
        if new_bi != b[i]:
            b[i] = new_bi
            flipped.append(i)
            
            # Add unvisited neighbors to queue
            for j in nbrs_indices[i]:
                if j not in visited:
                    queue.append(j)
    
    return len(flipped), flipped


def glauber_step(states, W, h_ext, rng, dt=1.0, temperature=1.0):
    """
    Single Glauber dynamics step for continuous-time evolution.
    
    Flip probability: p_i = 1 / (1 + exp(2 s_i h_i^eff / T))
    
    where s_i ∈ {-1, +1} and h_i^eff = h_ext,i + Σ_j W_ij s_j
    
    Args:
        states: Spin states (±1)
        W: Coupling matrix
        h_ext: External field
        rng: Random generator
        dt: Time step
        temperature: Temperature (units of coupling)
        
    Returns:
        Updated states
    """
    N = len(states)
    h_eff = h_ext + W.dot(states)
    
    # Flip probabilities
    if temperature > 0:
        flip_probs = 1.0 / (1.0 + np.exp(2 * states * h_eff / temperature))
    else:
        # Zero temperature: deterministic
        flip_probs = (states * h_eff < 0).astype(float)
    
    # Apply flips
    flips = rng.random(N) < (flip_probs * dt)
    new_states = states.copy()
    new_states[flips] *= -1
    
    return new_states


def compute_spectral_norm(W, k=1):
    """
    Compute spectral norm ||W||₂ = largest eigenvalue.
    
    Args:
        W: Matrix (sparse or dense)
        k: Number of eigenvalues to compute
        
    Returns:
        Spectral norm (float)
    """
    try:
        if W.shape[0] < k + 1:
            k = max(W.shape[0] - 1, 1)
        vals = eigsh(W, k=k, which='LM', return_eigenvectors=False, maxiter=1000)
        return float(np.max(np.abs(vals)))
    except Exception as e:
        # Fallback for small or problematic matrices
        try:
            W_dense = W.toarray() if hasattr(W, 'toarray') else W
            vals = np.linalg.eigvalsh(W_dense)
            return float(np.max(np.abs(vals)))
        except:
            return 0.0


def compute_eigenspectrum(W, k=None, sigma=None):
    """
    Compute eigenvalues of coupling matrix.
    
    Args:
        W: Coupling matrix (sparse or dense)
        k: Number of eigenvalues (None for all if small)
        sigma: Target value for shift-invert mode
        
    Returns:
        Array of eigenvalues (sorted by magnitude, descending)
    """
    N = W.shape[0]
    
    if k is None:
        k = min(N - 1, 50)  # Default to top 50
    
    try:
        if N < 100 or k >= N - 1:
            # Small matrix: compute all eigenvalues
            W_dense = W.toarray() if hasattr(W, 'toarray') else W
            vals = np.linalg.eigvalsh(W_dense)
        else:
            # Large matrix: compute top k
            vals = eigsh(W, k=k, which='LM', return_eigenvectors=False, maxiter=2000)
        
        # Sort by absolute value, descending
        vals = vals[np.argsort(-np.abs(vals))]
        return vals
    
    except Exception as e:
        print(f"Warning: eigenspectrum computation failed: {e}")
        return np.array([])


def measure_synchronization(states):
    """
    Measure synchronization order parameter.
    
    For states ∈ {-1, +1}: M = |⟨s⟩|
    For states ∈ {0, 1}: M = |2⟨b⟩ - 1|
    
    Args:
        states: State array or trajectory (NxT or just N)
        
    Returns:
        Synchronization measure (0 to 1)
    """
    if states.ndim == 1:
        mean_state = np.mean(states)
    else:
        # Time series: average over time first
        mean_state = np.mean(np.mean(states, axis=1))
    
    # If states in {0,1}, convert to {-1,+1} scale
    if np.min(states) >= 0 and np.max(states) <= 1:
        return np.abs(2 * mean_state - 1)
    else:
        return np.abs(mean_state)


def estimate_critical_point(J_values, mean_sizes):
    """
    Estimate critical coupling J_c from cascade size vs coupling data.
    
    Finds largest jump in mean cascade size (susceptibility peak).
    
    Args:
        J_values: Array of coupling strengths
        mean_sizes: Corresponding mean cascade sizes
        
    Returns:
        dict with J_c estimate and uncertainty
    """
    if len(J_values) < 2:
        return {'J_c': np.nan, 'uncertainty': np.nan}
    
    # Compute finite differences
    dS_dJ = np.diff(mean_sizes) / np.diff(J_values)
    
    # Find maximum susceptibility
    max_idx = np.argmax(dS_dJ)
    J_c = (J_values[max_idx] + J_values[max_idx + 1]) / 2
    
    # Uncertainty: width of peak region (above 70% of max)
    threshold = 0.7 * np.max(dS_dJ)
    peak_region = dS_dJ > threshold
    J_width = np.sum(peak_region) * np.mean(np.diff(J_values)) if np.any(peak_region) else 0.0
    
    return {
        'J_c': float(J_c),
        'uncertainty': float(J_width),
        'max_susceptibility': float(np.max(dS_dJ))
    }


def compute_cascade_distribution(cascade_sizes, bins='auto'):
    """
    Compute cascade size distribution and estimate power-law exponent.
    
    Args:
        cascade_sizes: Array of cascade sizes
        bins: Binning strategy for histogram
        
    Returns:
        dict with histogram, power-law fit
    """
    if len(cascade_sizes) == 0:
        return {'sizes': [], 'counts': [], 'exponent': np.nan}
    
    sizes = np.array(cascade_sizes)
    unique_sizes, counts = np.unique(sizes, return_counts=True)
    
    # Fit power law to tail (CCDF)
    if len(unique_sizes) > 3:
        ccdf = 1.0 - np.cumsum(counts) / len(sizes)
        
        # Fit range: mesoscopic (avoid small-size cutoff and large-size noise)
        fit_mask = (unique_sizes >= 5) & (unique_sizes <= np.percentile(unique_sizes, 85))
        
        if np.sum(fit_mask) >= 3:
            log_s = np.log(unique_sizes[fit_mask])
            log_ccdf = np.log(np.maximum(ccdf[fit_mask], 1e-10))
            
            # Linear fit: log(CCDF) ≈ -κ log(s) + const
            kappa = -np.polyfit(log_s, log_ccdf, 1)[0]
        else:
            kappa = np.nan
    else:
        kappa = np.nan
    
    return {
        'sizes': unique_sizes.tolist(),
        'counts': counts.tolist(),
        'exponent': float(kappa) if not np.isnan(kappa) else None
    }

