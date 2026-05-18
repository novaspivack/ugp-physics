import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from math import exp

def normalized_laplacian(G):
    N = G.number_of_nodes()
    idx = {n: i for i, n in enumerate(G.nodes())}
    rows, cols, data = [], [], []
    deg = np.zeros(N)
    
    for u, v, attr in G.edges(data=True):
        i, j = idx[u], idx[v]
        w = attr.get('w', 1.0)
        rows.append(i)
        cols.append(j)
        data.append(w)
        rows.append(j)
        cols.append(i)
        data.append(w)
        deg[i] += w
        deg[j] += w
    
    A = sp.coo_matrix((data, (rows, cols)), shape=(N, N)).tocsr()
    d = np.power(deg, -0.5, where=deg > 0, out=np.ones(N))
    Dnh = sp.diags(d)
    I = sp.eye(N, format='csr')
    L = I - Dnh @ A @ Dnh
    
    return L

def hutchpp_heattrace(L, t, probes=32, kpm_order=64, rng=None):
    if rng is None:
        rng = np.random.default_rng(0)
    
    N = L.shape[0]
    
    a, b = 0.0, 2.0
    Ls = (2 * L - (b + a) * sp.eye(N, format='csr')) / (b - a)
    
    tr = 0.0
    
    for _ in range(probes):
        v = rng.standard_normal(N)
        v /= np.linalg.norm(v) + 1e-12
        
        T0 = v.copy()
        T1 = Ls @ v
        
        c0 = cheb_coeff_exp(t, 0)
        tr += c0 * np.dot(v, T0)
        
        if kpm_order >= 1:
            c1 = cheb_coeff_exp(t, 1)
            tr += c1 * np.dot(v, T1)
        
        Tm2, Tm1 = T0, T1
        
        for m in range(2, kpm_order + 1):
            Tm = 2 * (Ls @ Tm1) - Tm2
            cm = cheb_coeff_exp(t, m)
            tr += cm * np.dot(v, Tm)
            Tm2, Tm1 = Tm1, Tm
    
    return float(N * tr / probes)

def cheb_coeff_exp(t, m):
    from scipy.special import iv
    a, b = 0.0, 2.0
    shift = (a + b) / 2.0
    scale = (b - a) / 2.0
    alpha = -t * scale
    
    if m == 0:
        coeff = iv(0, alpha)
    else:
        coeff = 2.0 * iv(m, alpha)
    
    phase_factor = exp(-t * shift)
    
    return float(coeff * phase_factor)

