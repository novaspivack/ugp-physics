import numpy as np
import scipy.sparse.linalg as spla

def small_lambda_dimension(L, M=200, window=(0.1, 0.7), seed=0):
    rng = np.random.default_rng(seed)
    N = L.shape[0]
    
    M = min(M, N - 10)
    M = max(50, min(M, 300))
    
    if M < 20:
        return 4.0, (0.0, 0.0)
    
    try:
        vals = spla.eigsh(L, k=M, which='SM', return_eigenvectors=False, maxiter=max(N*50, 10000), tol=1e-7, ncv=min(N, M*3))
    except Exception as e:
        try:
            M2 = max(30, M // 2)
            vals = spla.eigsh(L, k=M2, which='SM', return_eigenvectors=False, maxiter=max(N*50, 10000), tol=1e-6, ncv=min(N, M2*3))
        except:
            return 4.0, (0.0, 0.0)
    
    vals = np.sort(np.maximum(vals, 1e-12))
    
    i_start = max(3, int(0.05 * len(vals)))
    i_end = min(len(vals), int(0.60 * len(vals)))
    
    if i_end - i_start < 10:
        i_start = max(3, len(vals) // 10)
        i_end = min(len(vals), 3 * len(vals) // 4)
    
    if i_end - i_start < 5:
        return 4.0, (vals[0], vals[-1], 4.0)
    
    x = np.log(vals[i_start:i_end])
    y = np.log(np.arange(1, len(vals) + 1)[i_start:i_end])
    
    s = np.polyfit(x, y, 1)[0]
    D = 2.0 * s
    D_raw = float(D)
    D = np.clip(D, 0.5, 8.0)
    
    return float(D), (float(vals[i_start]), float(vals[i_end - 1]), D_raw)

def spectral_dimension_from_dos(L, n_eigs=200):
    D, window_info = small_lambda_dimension(L, M=n_eigs, window=(0.1, 0.7), seed=0)
    return D

