
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PT normal-step integrator in invariant space k.

Implements the universal source (MFRR sec. 9.4):
  dk/d(ln mu) = beta(k) + J_PT(k; Epsi),
  J_PT = -2 * rho_PT(mu) * lambda(Epsi) * (n·k) * n,
  with n = grad(k_M - k_gen2 - 1/4 k_L2).
Default n = (-1/4, -1, 1, 0, ..., 0) in coordinate order (k_L2, k_gen2, k_M, ...).

Diagnostics:
  - final n·k
  - J_PT · tau for any supplied in-plane tangent tau (should be ~ 0).

References:
  - MFRR sec. 9.1-9.4 (Quarter-Lock preservation; PT-induced RG source).
"""
import math
from typing import Callable, Sequence, Tuple, Optional
import json

def ql_normal(dim:int) -> list:
    n = [0.0]*dim
    n[0] = -0.25  # d/d k_L2
    n[1] = -1.0   # d/d k_gen2
    n[2] = +1.0   # d/d k_M
    return n

def dot(a:Sequence[float], b:Sequence[float]) -> float:
    return sum(x*y for x,y in zip(a,b))

def add(a, b, scale=1.0):
    return [ai + scale*bi for ai,bi in zip(a,b)]

def norm(a:Sequence[float]) -> float:
    return math.sqrt(dot(a,a))

def default_beta(k:Sequence[float]) -> list:
    return [0.0]*len(k)

def default_rhoPT(mu:float) -> float:
    return 1.0

def default_lambda(Epsi:float) -> float:
    return 0.1*Epsi

def step(k:list, dlnmu:float, mu:float, Epsi:float,
         beta_fn:Callable[[Sequence[float]],Sequence[float]] = default_beta,
         rhoPT_fn:Callable[[float],float] = default_rhoPT,
         lambda_fn:Callable[[float],float] = default_lambda) -> list:
    dim = len(k)
    n = ql_normal(dim)
    nk = dot(n, k)
    J = [-2.0 * rhoPT_fn(mu) * lambda_fn(Epsi) * nk * nj for nj in n]
    dk = add(beta_fn(k), J, scale=1.0)
    return add(k, dk, scale=dlnmu)

def integrate(k0:list, s_max:float=5.0, ds:float=1e-2, 
              mu0:float=1.0, Epsi:float=1.0,
              beta_fn:Callable[[Sequence[float]],Sequence[float]] = default_beta,
              rhoPT_fn:Callable[[float],float] = default_rhoPT,
              lambda_fn:Callable[[float],float] = default_lambda,
              tangent_in_plane: Optional[Sequence[float]] = None) -> Tuple[list, list]:
    k = list(k0)
    traj = [list(k)]
    times = [0.0]
    dim = len(k)
    n = ql_normal(dim)
    if tangent_in_plane is not None:
        t = list(tangent_in_plane)
        tproj = add(t, n, scale= -dot(n,t)/dot(n,n))
        tangent_in_plane = tproj

    s = 0.0
    while s < s_max:
        mu = mu0*math.exp(s)
        k = step(k, ds, mu, Epsi, beta_fn, rhoPT_fn, lambda_fn)
        s += ds
        traj.append(list(k))
        times.append(s)
    nk_final = dot(n,k)
    print(f"[diag] final n·k = {nk_final:+.12e}")
    if tangent_in_plane is not None:
        nk = dot(n,k)
        J = [-2.0 * rhoPT_fn(mu0*math.exp(s_max)) * lambda_fn(Epsi) * nk * nj for nj in n]
        ortho = dot(J, tangent_in_plane)
        print(f"[diag] J_PT · tangent_in_plane = {ortho:+.12e}")
    return traj, times

def demo():
    k0 = [7/512, -0.8090169, -0.78, 0.02, math.pi/2, 0.125, -1.5, 1.3333333]
    print("[start] n·k = ", dot(ql_normal(len(k0)), k0))
    traj, times = integrate(k0, s_max=2.0, ds=1e-3, Epsi=0.5, tangent_in_plane=[1,4,1,0,0,0,0,0])
    print("[done] steps: ", len(times))
    out = {"times": times, "traj": traj}
    with open("pt_traj.json", "w") as f:
        json.dump(out, f, indent=2)
    print("[write] pt_traj.json written.")

if __name__ == "__main__":
    demo()
